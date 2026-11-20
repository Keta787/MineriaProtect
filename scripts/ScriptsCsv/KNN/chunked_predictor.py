"""Resumable disk-checkpointed chunked predictor for expensive exact KNN inference."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import time
from typing import Dict, List

import numpy as np
from scipy import sparse
from sklearn.neighbors import KNeighborsClassifier

from scripts.ScriptsCsv.NaiveBayes.pipeline import current_process_rss_mb


@dataclass(frozen=True)
class ChunkedPredictResult:
    """Output of a resumable chunked KNN probability prediction run."""

    run_tag: str
    cache_dir: Path
    proba_pos: np.ndarray
    n_queries: int
    n_chunks: int
    chunks_loaded_from_cache: int
    chunks_computed_now: int
    elapsed_compute_s: float
    total_recorded_compute_s: float
    peak_rss_mb: float
    used_full_cache: bool


class ChunkedKNNPredictor:
    """Predict class-1 probabilities in chunks, checkpointing each chunk to disk with automatic resume."""

    def __init__(
        self,
        cache_root: Path,
        chunk_size: int = 5000,
    ) -> None:
        self.cache_root = Path(cache_root)
        self.chunk_size = int(chunk_size)
        if self.chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}.")
        self.cache_root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def compute_signature(metadata: Dict[str, object]) -> str:
        """Compute deterministic SHA-256 signature for cache validation."""
        payload = json.dumps(metadata, sort_keys=True, ensure_ascii=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def _chunk_path(self, run_dir: Path, chunk_idx: int) -> Path:
        return run_dir / f"chunk_{chunk_idx:05d}.npy"

    def _manifest_path(self, run_dir: Path) -> Path:
        return run_dir / "manifest.json"

    def predict_proba_resumable(
        self,
        fitted_knn: KNeighborsClassifier | None,
        X_query: np.ndarray | sparse.spmatrix,
        run_tag: str,
        metadata: Dict[str, object],
        force_recompute: bool = False,
        verbose: bool = True,
    ) -> ChunkedPredictResult:
        """Run chunked predict_proba with per-chunk disk checkpoints and automatic resume.

        If all chunks already exist on disk and match the metadata signature (and force_recompute=False),
        returns the assembled probability vector without needing to call fitted_knn.
        """
        n_queries = int(X_query.shape[0])
        n_chunks = int(np.ceil(float(n_queries) / float(self.chunk_size)))
        sig_payload = {
            **metadata,
            "n_queries": n_queries,
            "n_features": int(X_query.shape[1]),
            "chunk_size": self.chunk_size,
        }
        sig = self.compute_signature(sig_payload)
        run_dir = self.cache_root / f"{run_tag}_{sig}"
        run_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = self._manifest_path(run_dir)

        if force_recompute:
            for existing in run_dir.glob("chunk_*.npy"):
                existing.unlink()
            if manifest_path.exists():
                manifest_path.unlink()

        manifest: Dict[str, object]
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("signature") != sig:
                raise RuntimeError(
                    f"Cache signature mismatch in {run_dir}: expected {sig}, found {manifest.get('signature')}"
                )
        else:
            manifest = {
                "run_tag": run_tag,
                "signature": sig,
                "metadata": sig_payload,
                "n_queries": n_queries,
                "n_chunks": n_chunks,
                "chunk_times_s": {},
                "completed": False,
            }
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
            )

        chunk_times: Dict[str, float] = dict(manifest.get("chunk_times_s", {}))  # type: ignore[arg-type]
        proba_chunks: List[np.ndarray] = []
        loaded_count = 0
        computed_count = 0
        t_compute_total = 0.0
        peak_rss = current_process_rss_mb()

        for c_idx in range(n_chunks):
            start = c_idx * self.chunk_size
            end = min(start + self.chunk_size, n_queries)
            expected_len = end - start
            c_path = self._chunk_path(run_dir, c_idx)

            if c_path.exists():
                arr = np.load(c_path)
                if arr.shape == (expected_len,) and np.isfinite(arr).all():
                    proba_chunks.append(arr.astype(np.float64, copy=False))
                    loaded_count += 1
                    continue

            if fitted_knn is None:
                raise RuntimeError(
                    f"Chunk {c_idx}/{n_chunks} missing in {run_dir} and fitted_knn is None."
                )

            X_slice = X_query[start:end]
            t0 = time.perf_counter()
            probs = np.asarray(fitted_knn.predict_proba(X_slice)[:, 1], dtype=np.float64)
            dt = time.perf_counter() - t0
            t_compute_total += dt
            computed_count += 1

            if probs.shape != (expected_len,) or not np.isfinite(probs).all():
                raise RuntimeError(f"Invalid probabilities produced on chunk {c_idx}.")

            # Atomic write via temporary file to avoid corrupted chunks on interruption
            tmp_path = c_path.with_suffix(".tmp.npy")
            np.save(tmp_path, probs)
            tmp_path.replace(c_path)

            chunk_times[str(c_idx)] = round(float(dt), 4)
            manifest["chunk_times_s"] = chunk_times
            manifest["completed"] = (c_idx + 1 == n_chunks) and (loaded_count + computed_count == n_chunks)
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
            )

            rss_now = current_process_rss_mb()
            if rss_now > peak_rss:
                peak_rss = rss_now

            proba_chunks.append(probs)
            if verbose and (computed_count == 1 or computed_count % 5 == 0 or c_idx + 1 == n_chunks):
                done_rows = end
                avg_dt = t_compute_total / float(computed_count)
                rem_chunks = n_chunks - (c_idx + 1)
                eta_min = (rem_chunks * avg_dt) / 60.0
                print(
                    f"[{run_tag}] Bloque {c_idx + 1}/{n_chunks} ({done_rows:,}/{n_queries:,} filas) | "
                    f"bloque={dt:.2f}s | ETA~{eta_min:.1f} min | RSS={rss_now:.0f} MB",
                    flush=True,
                )

        proba_full = np.concatenate(proba_chunks, axis=0)
        if proba_full.shape != (n_queries,):
            raise AssertionError(f"Expected length {n_queries}, assembled {proba_full.shape}.")
        if np.any(proba_full < -1e-12) or np.any(proba_full > 1.0 + 1e-12):
            raise AssertionError("Assembled probabilities fall outside [0, 1].")
        proba_full = np.clip(proba_full, 0.0, 1.0)

        manifest["completed"] = True
        recorded_peak = float(manifest.get("peak_rss_mb", 0.0))
        eff_peak = max(float(peak_rss), recorded_peak)
        manifest["peak_rss_mb"] = round(eff_peak, 2)
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        total_recorded_s = float(sum(float(v) for v in chunk_times.values()))
        return ChunkedPredictResult(
            run_tag=run_tag,
            cache_dir=run_dir,
            proba_pos=proba_full,
            n_queries=n_queries,
            n_chunks=n_chunks,
            chunks_loaded_from_cache=loaded_count,
            chunks_computed_now=computed_count,
            elapsed_compute_s=round(t_compute_total, 4),
            total_recorded_compute_s=round(total_recorded_s, 4),
            peak_rss_mb=round(eff_peak, 2),
            used_full_cache=(computed_count == 0 and loaded_count == n_chunks),
        )
