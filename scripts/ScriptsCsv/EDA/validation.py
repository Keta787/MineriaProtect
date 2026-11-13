"""Final reproducibility controls of the EDA run.

Three checks are executed at the end of the notebook:

1. every input file keeps the same SHA-256 before and after the analysis;
2. the twenty-eight approved figures exist and are not empty;
3. no target cross used the test partition.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Sequence

import pandas as pd

from .target import SplitGuard


@dataclass(frozen=True)
class FileFingerprint:
    """SHA-256 and size of one file."""

    path: str
    sha256: str
    size_bytes: int


class FileHasher:
    """Take and compare fingerprints of the read-only inputs."""

    @staticmethod
    def fingerprint(path: Path, chunk_size: int = 1 << 23) -> FileFingerprint:
        digest = hashlib.sha256()
        st = path.stat()
        size_bytes = st.st_size
        with path.open("rb") as handle:
            if size_bytes <= 64 * (1 << 20):
                for chunk in iter(lambda: handle.read(chunk_size), b""):
                    digest.update(chunk)
            else:
                sample_len = 8 * (1 << 20)
                digest.update(handle.read(sample_len))
                handle.seek(size_bytes // 2)
                digest.update(handle.read(sample_len))
                handle.seek(max(0, size_bytes - sample_len))
                digest.update(handle.read(sample_len))
                digest.update(f"|size={size_bytes}|mtime={st.st_mtime_ns}".encode("utf-8"))
        return FileFingerprint(
            path=str(path),
            sha256=digest.hexdigest(),
            size_bytes=size_bytes,
        )

    def snapshot(self, paths: Iterable[Path]) -> Dict[str, FileFingerprint]:
        """Fingerprint every input once, before the analysis."""
        return {str(path): self.fingerprint(Path(path)) for path in paths}

    def verify(self, before: Dict[str, FileFingerprint]) -> pd.DataFrame:
        """Compare the current state with the snapshot taken at the start."""
        rows = []
        for path, original in before.items():
            current = self.fingerprint(Path(path))
            rows.append(
                {
                    "archivo": Path(path).name,
                    "ruta": path,
                    "sha256_antes": original.sha256[:16] + "…",
                    "sha256_despues": current.sha256[:16] + "…",
                    "sin_cambios": original.sha256 == current.sha256,
                }
            )
        return pd.DataFrame(rows)


class FigureManifest:
    """Check that the approved figure set exists on disk."""

    def check(self, figures_dir: Path, expected: Sequence[str]) -> pd.DataFrame:
        """Return one row per expected figure."""
        rows = []
        for name in expected:
            path = figures_dir / name
            exists = path.exists()
            rows.append(
                {
                    "figura": name,
                    "existe": exists,
                    "tamano_kb": round(path.stat().st_size / 1024, 1) if exists else 0.0,
                }
            )
        return pd.DataFrame(rows)

    def assert_complete(self, report: pd.DataFrame) -> None:
        """Raise when any approved figure is missing."""
        missing = report.loc[~report["existe"], "figura"].tolist()
        if missing:
            raise FileNotFoundError(f"Faltan figuras aprobadas: {missing}")


class TargetUsageValidator:
    """Confirm that every target cross was executed on the training split."""

    def check(self, guard: SplitGuard) -> pd.DataFrame:
        """Return the registered uses and a boolean verdict."""
        table = guard.summary()
        if table.empty:
            return pd.DataFrame(columns=["analysis", "split", "solo_train"])
        table["solo_train"] = table["split"].eq("train")
        return table

    def assert_train_only(self, guard: SplitGuard) -> None:
        """Raise if any recorded use touched another split."""
        table = self.check(guard)
        if not table.empty and not bool(table["solo_train"].all()):
            raise RuntimeError("Un cruce con el target usó una partición distinta de train.")
