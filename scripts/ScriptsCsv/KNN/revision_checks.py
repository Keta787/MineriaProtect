"""Post-review verification analyses (Section 14A: F1, F2, F3, F5, F6, F7, F8) using disk caches."""

from __future__ import annotations

from dataclasses import dataclass
import gc
import hashlib
import json
from pathlib import Path
import time
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import sparse, stats
from scipy.spatial.distance import cdist
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold

from scripts.ScriptsCsv.NaiveBayes.evaluation import (
    _weighted_pr_roc_from_presorted,
    compute_classification_metrics,
    compute_equal_alert_rate_cutoff,
    paired_bootstrap_person_diffs,
)
from scripts.ScriptsCsv.NaiveBayes.occupation_analysis import wilson_ci_95

from .chunked_predictor import ChunkedKNNPredictor
from .config import (
    ISCO_MAJOR_LABELS_ES,
    KNNConfig,
    MODEL_KNN_D,
    MODEL_KNN_G,
    MODEL_KNN_W,
    MODEL_ORDER,
    VERSION_CON,
)
from .evaluation import KNNEvaluator, PersonSubsampler
from .feature_blocks import (
    AuditedStandardBinaryScaler,
    KNNFeatureBuilder,
    KNNPartitionBlocks,
    KNNVersionBundle,
)
from .models import KNNModelSpec, build_knn_classifier
from .version_comparison import VersionSensitivityAnalyzer


def tie_aware_equal_alert_weights(
    probs: np.ndarray,
    target_alert_rate: float,
) -> Tuple[np.ndarray, float, float, float, float]:
    """Compute deterministic fractional alert weights matching target_alert_rate exactly across ties.

    For scores strictly above cutoff c, weight = 1; below c, weight = 0; on the tie stratum p == c,
    weight = lambda in (0, 1] such that mean(weights) == target_alert_rate (exact expectation under
    uniform random tie breaking).

    Returns:
        (alert_weights, cutoff, raw_discrete_alert_rate, tie_matched_alert_rate, boundary_lambda)
    """
    p_arr = np.asarray(probs, dtype=np.float64).ravel()
    n = len(p_arr)
    if n == 0:
        return np.zeros(0, dtype=np.float64), 0.5, 0.0, 0.0, 0.0

    k_target = float(target_alert_rate) * float(n)
    k_int = int(round(k_target))
    if k_int <= 0:
        return np.zeros(n, dtype=np.float64), float(np.max(p_arr)) + 1e-12, 0.0, 0.0, 0.0
    if k_int >= n:
        return np.ones(n, dtype=np.float64), float(np.min(p_arr)), 1.0, 1.0, 1.0

    cutoff = float(np.partition(p_arr, n - k_int)[n - k_int])
    above = p_arr > cutoff
    at_cut = p_arr == cutoff
    n_above = int(above.sum())
    n_at = int(at_cut.sum())
    raw_rate = float(n_above + n_at) / float(n)

    lam = (k_target - float(n_above)) / float(max(n_at, 1))
    lam = float(np.clip(lam, 0.0, 1.0))

    weights = np.zeros(n, dtype=np.float64)
    weights[above] = 1.0
    weights[at_cut] = lam
    matched_rate = float(weights.mean())
    return weights, cutoff, raw_rate, matched_rate, lam


def paired_bootstrap_person_multi_alpha(
    y_true: np.ndarray,
    prob_a: np.ndarray,
    prob_b: np.ndarray,
    groups: np.ndarray,
    n_resamples: int = 1000,
    bonferroni_m: int = 10,
    random_state: int = 42,
) -> Dict[str, object]:
    """Paired person-level bootstrap returning both 95% and Bonferroni-adjusted (1 - 0.05/m) CIs."""
    y_arr = np.asarray(y_true, dtype=np.int8).ravel()
    pa = np.asarray(prob_a, dtype=np.float64).ravel()
    pb = np.asarray(prob_b, dtype=np.float64).ravel()
    if not (len(y_arr) == len(pa) == len(pb)):
        raise ValueError("y_true, prob_a, and prob_b must share the same length.")

    _, person_inv = np.unique(np.asarray(groups, dtype=str), return_inverse=True)
    n_persons = int(person_inv.max()) + 1

    ord_a = np.argsort(-pa, kind="mergesort")
    pa_s = pa[ord_a]
    ya_s = y_arr[ord_a].astype(np.float64)
    pers_a_s = person_inv[ord_a]
    ties_a = np.flatnonzero(np.r_[True, pa_s[1:] != pa_s[:-1]])

    ord_b = np.argsort(-pb, kind="mergesort")
    pb_s = pb[ord_b]
    yb_s = y_arr[ord_b].astype(np.float64)
    pers_b_s = person_inv[ord_b]
    ties_b = np.flatnonzero(np.r_[True, pb_s[1:] != pb_s[:-1]])

    rng = np.random.default_rng(random_state)
    d_pr = np.zeros(n_resamples, dtype=np.float64)
    d_roc = np.zeros(n_resamples, dtype=np.float64)

    for b in range(n_resamples):
        drawn = rng.integers(0, n_persons, size=n_persons)
        pw = np.bincount(drawn, minlength=n_persons).astype(np.float64)
        pr_a, roc_a = _weighted_pr_roc_from_presorted(pw, pers_a_s, ya_s, ties_a)
        pr_b, roc_b = _weighted_pr_roc_from_presorted(pw, pers_b_s, yb_s, ties_b)
        d_pr[b] = pr_a - pr_b
        d_roc[b] = roc_a - roc_b

    pr_obs = float(average_precision_score(y_arr, pa) - average_precision_score(y_arr, pb))
    roc_obs = float(roc_auc_score(y_arr, pa) - roc_auc_score(y_arr, pb))

    alpha_bonf = 0.05 / float(max(bonferroni_m, 1))
    lo_b_q = 100.0 * (alpha_bonf / 2.0)
    hi_b_q = 100.0 * (1.0 - alpha_bonf / 2.0)

    pr_95 = tuple(float(v) for v in np.percentile(d_pr, [2.5, 97.5]))
    pr_bonf = tuple(float(v) for v in np.percentile(d_pr, [lo_b_q, hi_b_q]))
    roc_95 = tuple(float(v) for v in np.percentile(d_roc, [2.5, 97.5]))
    roc_bonf = tuple(float(v) for v in np.percentile(d_roc, [lo_b_q, hi_b_q]))

    return {
        "delta_pr_auc": pr_obs,
        "pr_95_low": pr_95[0],
        "pr_95_high": pr_95[1],
        "pr_95_excluye_cero": bool(pr_95[0] > 0.0 or pr_95[1] < 0.0),
        "pr_bonf_low": pr_bonf[0],
        "pr_bonf_high": pr_bonf[1],
        "pr_bonf_excluye_cero": bool(pr_bonf[0] > 0.0 or pr_bonf[1] < 0.0),
        "delta_roc_auc": roc_obs,
        "roc_95_low": roc_95[0],
        "roc_95_high": roc_95[1],
        "roc_95_excluye_cero": bool(roc_95[0] > 0.0 or roc_95[1] < 0.0),
        "roc_bonf_low": roc_bonf[0],
        "roc_bonf_high": roc_bonf[1],
        "roc_bonf_excluye_cero": bool(roc_bonf[0] > 0.0 or roc_bonf[1] < 0.0),
        "nivel_bonferroni_pct": round(100.0 * (1.0 - alpha_bonf), 2),
    }


def paired_bootstrap_practical_counts(
    y_true: np.ndarray,
    weights_a: np.ndarray,
    weights_b: np.ndarray,
    prob_a: np.ndarray,
    prob_b: np.ndarray,
    groups: np.ndarray,
    n_resamples: int = 1000,
    random_state: int = 42,
) -> Dict[str, float]:
    """Paired person-level bootstrap for extra TP per 1,000 alerts, tie-matched F1 diff, and relative PR-AUC gain."""
    y_arr = np.asarray(y_true, dtype=np.float64).ravel()
    wa = np.asarray(weights_a, dtype=np.float64).ravel()
    wb = np.asarray(weights_b, dtype=np.float64).ravel()
    pa = np.asarray(prob_a, dtype=np.float64).ravel()
    pb = np.asarray(prob_b, dtype=np.float64).ravel()

    _, person_inv = np.unique(np.asarray(groups, dtype=str), return_inverse=True)
    n_persons = int(person_inv.max()) + 1

    # Per-person pre-aggregation for instant vectorized bootstrap
    p_pos = np.bincount(person_inv, weights=y_arr, minlength=n_persons)
    p_a_al = np.bincount(person_inv, weights=wa, minlength=n_persons)
    p_a_tp = np.bincount(person_inv, weights=wa * y_arr, minlength=n_persons)
    p_b_al = np.bincount(person_inv, weights=wb, minlength=n_persons)
    p_b_tp = np.bincount(person_inv, weights=wb * y_arr, minlength=n_persons)

    ord_a = np.argsort(-pa, kind="mergesort")
    pa_s = pa[ord_a]
    ya_s = y_arr[ord_a]
    pers_a_s = person_inv[ord_a]
    ties_a = np.flatnonzero(np.r_[True, pa_s[1:] != pa_s[:-1]])

    ord_b = np.argsort(-pb, kind="mergesort")
    pb_s = pb[ord_b]
    yb_s = y_arr[ord_b]
    pers_b_s = person_inv[ord_b]
    ties_b = np.flatnonzero(np.r_[True, pb_s[1:] != pb_s[:-1]])

    rng = np.random.default_rng(random_state)
    d_tp1k = np.zeros(n_resamples, dtype=np.float64)
    d_f1 = np.zeros(n_resamples, dtype=np.float64)
    rel_pr = np.zeros(n_resamples, dtype=np.float64)

    for b in range(n_resamples):
        drawn = rng.integers(0, n_persons, size=n_persons)
        pw = np.bincount(drawn, minlength=n_persons).astype(np.float64)

        tot_pos = float(pw @ p_pos)
        a_al = float(pw @ p_a_al)
        a_tp = float(pw @ p_a_tp)
        b_al = float(pw @ p_b_al)
        b_tp = float(pw @ p_b_tp)

        tp1k_a = 1000.0 * a_tp / max(a_al, 1e-12)
        tp1k_b = 1000.0 * b_tp / max(b_al, 1e-12)
        d_tp1k[b] = tp1k_a - tp1k_b

        f1_a = (2.0 * a_tp / (a_al + tot_pos)) if (a_al + tot_pos) > 0 else 0.0
        f1_b = (2.0 * b_tp / (b_al + tot_pos)) if (b_al + tot_pos) > 0 else 0.0
        d_f1[b] = f1_a - f1_b

        pr_a, _ = _weighted_pr_roc_from_presorted(pw, pers_a_s, ya_s, ties_a)
        pr_b, _ = _weighted_pr_roc_from_presorted(pw, pers_b_s, yb_s, ties_b)
        rel_pr[b] = 100.0 * (pr_a - pr_b) / max(pr_b, 1e-12)

    tot_pos_obs = float(y_arr.sum())
    a_al_obs, a_tp_obs = float(wa.sum()), float((wa * y_arr).sum())
    b_al_obs, b_tp_obs = float(wb.sum()), float((wb * y_arr).sum())
    tp1k_a_obs = 1000.0 * a_tp_obs / max(a_al_obs, 1e-12)
    tp1k_b_obs = 1000.0 * b_tp_obs / max(b_al_obs, 1e-12)
    f1_a_obs = 2.0 * a_tp_obs / (a_al_obs + tot_pos_obs)
    f1_b_obs = 2.0 * b_tp_obs / (b_al_obs + tot_pos_obs)
    pr_a_obs = float(average_precision_score(y_arr, pa))
    pr_b_obs = float(average_precision_score(y_arr, pb))

    return {
        "tp_por_1000_alertas_A": tp1k_a_obs,
        "tp_por_1000_alertas_B": tp1k_b_obs,
        "delta_tp_por_1000_alertas": tp1k_a_obs - tp1k_b_obs,
        "delta_tp_1k_ci_low": float(np.percentile(d_tp1k, 2.5)),
        "delta_tp_1k_ci_high": float(np.percentile(d_tp1k, 97.5)),
        "delta_tp_total_test": a_tp_obs - b_tp_obs,
        "f1_exacto_A": f1_a_obs,
        "f1_exacto_B": f1_b_obs,
        "delta_f1_exacto": f1_a_obs - f1_b_obs,
        "delta_f1_ci_low": float(np.percentile(d_f1, 2.5)),
        "delta_f1_ci_high": float(np.percentile(d_f1, 97.5)),
        "ganancia_relativa_pr_auc_pct": 100.0 * (pr_a_obs - pr_b_obs) / max(pr_b_obs, 1e-12),
        "ganancia_rel_pr_ci_low": float(np.percentile(rel_pr, 2.5)),
        "ganancia_rel_pr_ci_high": float(np.percentile(rel_pr, 97.5)),
    }


@dataclass(frozen=True)
class CacheIntegrityBundle:
    """Outputs of Stage 0 / Section 14A.0 cache verification across KNN-D, KNN-G, and KNN-W."""

    integrity_table: pd.DataFrame
    assembled_proba_by_model: Dict[str, np.ndarray]
    manifests_by_model: Dict[str, Dict[str, object]]
    all_valid: bool


class CacheIntegrityVerifier:
    """Verify full-test disk caches without recomputing predictions."""

    def __init__(self, config: KNNConfig) -> None:
        self.config = config

    def _find_fulltest_cache_dir(self, model_id: str) -> Path:
        prefix = f"{model_id.lower().replace('-', '_')}_fulltest_"
        matches = sorted(p for p in self.config.cache_dir.glob(f"{prefix}*") if p.is_dir())
        if len(matches) != 1:
            raise FileNotFoundError(
                f"Expected exactly 1 fulltest cache directory for {model_id} with prefix '{prefix}', "
                f"found {len(matches)}: {[m.name for m in matches]}"
            )
        return matches[0]

    def verify_all_fulltest_caches(
        self,
        y_test: np.ndarray,
    ) -> CacheIntegrityBundle:
        """Verify 70 chunks per model, zero gaps/duplicates/NaNs, checksums, and exact match to table 10a."""
        ref_10a_path = self.config.tables_dir / "10a_resultados_test_version_a_ic95.csv"
        if not ref_10a_path.exists():
            raise FileNotFoundError(f"Missing reference table 10a: {ref_10a_path}")
        ref_10a = pd.read_csv(ref_10a_path, encoding="utf-8")

        n_test = int(len(y_test))
        rows: List[Dict[str, object]] = []
        probas_out: Dict[str, np.ndarray] = {}
        manifests_out: Dict[str, Dict[str, object]] = {}
        all_ok = True

        for model_id in MODEL_ORDER:
            cdir = self._find_fulltest_cache_dir(model_id)
            manifest = json.loads((cdir / "manifest.json").read_text(encoding="utf-8"))
            manifests_out[model_id] = manifest

            n_chunks = int(manifest["n_chunks"])
            chunk_size = int(manifest["metadata"]["chunk_size"])
            expected_n = int(manifest["n_queries"])
            if expected_n != n_test:
                raise AssertionError(f"{model_id}: manifest n_queries={expected_n} != y_test={n_test}")

            parts: List[np.ndarray] = []
            covered_rows = 0
            has_nan_inf = False
            out_of_bounds = False
            chunk_hasher = hashlib.sha256()

            for c_idx in range(n_chunks):
                c_path = cdir / f"chunk_{c_idx:05d}.npy"
                if not c_path.exists():
                    raise FileNotFoundError(f"Missing chunk file: {c_path}")
                arr = np.load(c_path)
                start = c_idx * chunk_size
                end = min(start + chunk_size, n_test)
                exp_len = end - start
                if arr.shape != (exp_len,):
                    raise AssertionError(
                        f"{model_id} chunk {c_idx}: shape {arr.shape} != expected ({exp_len},)"
                    )
                if not np.isfinite(arr).all():
                    has_nan_inf = True
                if np.any(arr < -1e-12) or np.any(arr > 1.0 + 1e-12):
                    out_of_bounds = True
                arr_f64 = np.clip(arr.astype(np.float64, copy=False), 0.0, 1.0)
                chunk_hasher.update(arr_f64.tobytes())
                parts.append(arr_f64)
                covered_rows += exp_len

            assembled = np.concatenate(parts, axis=0)
            if len(assembled) != n_test or covered_rows != n_test:
                raise AssertionError(f"{model_id}: covered {covered_rows} != {n_test}")

            probas_out[model_id] = assembled

            # Compare against exported table 10a (Umbral OOF óptimo row)
            r10 = ref_10a.loc[
                (ref_10a["modelo_id"] == model_id)
                & ref_10a["punto_operacion"].astype(str).str.contains("OOF")
            ].iloc[0]
            tau_ref = float(r10["umbral_tau"])
            m = compute_classification_metrics(y_test, assembled, threshold=tau_ref)

            diff_pr = abs(m["pr_auc"] - float(r10["pr_auc_test"]))
            diff_roc = abs(m["roc_auc"] - float(r10["roc_auc_test"]))
            diff_f1 = abs(m["f1_pos"] - float(r10["f1_clase_1_test"]))
            diff_brier = abs(m["brier"] - float(r10["brier_test"]))
            max_diff = max(diff_pr, diff_roc, diff_f1, diff_brier)

            ok = bool(
                manifest.get("completed") is True
                and not has_nan_inf
                and not out_of_bounds
                and covered_rows == n_test
                and max_diff <= 1e-4
            )
            if not ok:
                all_ok = False

            rows.append(
                {
                    "modelo_id": model_id,
                    "directorio_cache": cdir.name,
                    "bloques_verificados": n_chunks,
                    "filas_cubiertas": covered_rows,
                    "sin_nan_ni_duplicados": bool(not has_nan_inf and not out_of_bounds and covered_rows == n_test),
                    "sha256_vector_16": chunk_hasher.hexdigest()[:16],
                    "pr_auc_cache": round(m["pr_auc"], 4),
                    "pr_auc_tabla_10a": float(r10["pr_auc_test"]),
                    "roc_auc_cache": round(m["roc_auc"], 4),
                    "f1_tau_cache": round(m["f1_pos"], 4),
                    "brier_cache": round(m["brier"], 4),
                    "max_diff_vs_10a": round(max_diff, 6),
                    "reproduce_10a_exacto": ok,
                }
            )

        if not all_ok:
            raise AssertionError("Cache integrity verification failed for at least one model!")

        return CacheIntegrityBundle(
            integrity_table=pd.DataFrame(rows),
            assembled_proba_by_model=probas_out,
            manifests_by_model=manifests_out,
            all_valid=all_ok,
        )


@dataclass(frozen=True)
class PrefilterPredictionResult:
    """Measured outputs of ExactOccupationPrefilterKNN on a query batch."""

    proba_certified_fallback: np.ndarray
    proba_same_occ_fallback_lt_k: np.ndarray
    certified_sqrt2w_mask: np.ndarray
    certified_same_only_w_mask: np.ndarray
    fallback_lt_k_mask: np.ndarray
    fallback_zero_ohe_mask: np.ndarray
    fallback_bound_exceeded_mask: np.ndarray
    index_build_s: float
    local_search_s: float
    fallback_base_s: float
    fallback_exact_s: float
    total_prefilter_s: float


class ExactOccupationPrefilterKNN:
    """Exact same-occupation prefiltered KNN-W predictor aware of OneHotEncoder(drop='first').

    For Euclidean KNN-W with weight w on OHE dummies and drop='first':
      - Rows with OHE row sum == 1 (non-baseline occupations seen in train) sit at OHE distance:
          * 0 from same-occupation train rows,
          * w from zero-OHE baseline train rows ('0110.1', 47 rows in JobPath),
          * sqrt(2)*w from every other non-baseline train row.
      - Checking same-occupation train rows PLUS the small zero-OHE baseline pool (47 rows,
        adding w^2 to squared distance) mathematically guarantees exact top-k equivalence to
        full 1.39M search whenever d_k < sqrt(2)*w.
      - Any query with OHE row sum == 0, fewer than k same-occupation train rows, or
        d_k >= sqrt(2)*w falls back to exact full CSR KNeighborsClassifier search.
    """

    def __init__(
        self,
        n_neighbors: int = 101,
        block_weight: float = 8.0,
        n_jobs: int = 8,
    ) -> None:
        self.n_neighbors = int(n_neighbors)
        self.block_weight = float(block_weight)
        self.n_jobs = int(n_jobs)
        self._occ_to_X: Dict[str, np.ndarray] = {}
        self._occ_to_y: Dict[str, np.ndarray] = {}
        self._occ_counts: Dict[str, int] = {}
        self._zero_X: np.ndarray = np.empty((0, 0), dtype=np.float32)
        self._zero_y: np.ndarray = np.empty(0, dtype=np.int8)
        self._full_knn = None
        self.index_build_s_: float = 0.0

    def fit(
        self,
        train_blocks: KNNPartitionBlocks,
        orig_train: pd.DataFrame,
    ) -> "ExactOccupationPrefilterKNN":
        """Build inverted index by occupation_code on dense_scaled plus fallback full CSR KNN."""
        t0 = time.perf_counter()
        X_dense = np.ascontiguousarray(train_blocks.X_dense_scaled, dtype=np.float32)
        y_tr = np.asarray(train_blocks.y, dtype=np.int8)
        occ_tr = orig_train["occupation_code"].to_numpy(dtype=str)
        ohe_sum_tr = np.asarray(train_blocks.ohe_sparse.sum(axis=1)).ravel()

        zero_idx = np.flatnonzero(ohe_sum_tr == 0.0)
        self._zero_X = np.ascontiguousarray(X_dense[zero_idx], dtype=np.float32)
        self._zero_y = y_tr[zero_idx].copy()

        # Group non-zero-OHE rows by occupation_code once via argsort
        nz_idx = np.flatnonzero(ohe_sum_tr > 0.0)
        nz_occ = occ_tr[nz_idx]
        order = np.argsort(nz_occ, kind="mergesort")
        sorted_occ = nz_occ[order]
        sorted_rows = nz_idx[order]
        unique_occ, start_pos, counts = np.unique(
            sorted_occ, return_index=True, return_counts=True
        )

        self._occ_to_X = {}
        self._occ_to_y = {}
        self._occ_counts = {}
        for occ, st, cnt in zip(unique_occ.tolist(), start_pos.tolist(), counts.tolist()):
            r_idx = sorted_rows[st : st + cnt]
            self._occ_to_X[occ] = np.ascontiguousarray(X_dense[r_idx], dtype=np.float32)
            self._occ_to_y[occ] = y_tr[r_idx].copy()
            self._occ_counts[occ] = int(cnt)

        # Fallback exact CSR estimator (instant fit in brute mode)
        X_w_tr = train_blocks.build_knn_w_matrix(w=self.block_weight)
        est = build_knn_classifier(
            KNNModelSpec(
                model_id=MODEL_KNN_W,
                n_neighbors=self.n_neighbors,
                weights="uniform",
                metric="euclidean",
                algorithm="brute",
                block_weight=self.block_weight,
                n_jobs=self.n_jobs,
            )
        )
        est.fit(X_w_tr, y_tr)
        self._full_knn = est
        self.index_build_s_ = time.perf_counter() - t0
        return self

    def predict_with_diagnostics(
        self,
        test_blocks: KNNPartitionBlocks,
        orig_test: pd.DataFrame,
        query_idx: np.ndarray,
    ) -> PrefilterPredictionResult:
        """Predict on query_idx via exact prefilter + fallback, returning full bound and timing diagnostics."""
        if self._full_knn is None:
            raise RuntimeError("ExactOccupationPrefilterKNN must be fitted before predict_with_diagnostics().")

        q_idx = np.asarray(query_idx, dtype=np.int64)
        n_q = len(q_idx)
        k = self.n_neighbors
        w = self.block_weight
        w_sq = float(w * w)
        bound_sqrt2w_sq = float(2.0 * w * w)  # (sqrt(2)*w)^2
        bound_w_sq = w_sq                     # w^2 (strict same-occ-only bound ignoring drop='first')

        X_q_dense = np.ascontiguousarray(test_blocks.X_dense_scaled[q_idx], dtype=np.float32)
        occ_q = orig_test["occupation_code"].to_numpy(dtype=str)[q_idx]
        ohe_sum_q = np.asarray(test_blocks.ohe_sparse[q_idx].sum(axis=1)).ravel()

        proba_cert = np.full(n_q, np.nan, dtype=np.float64)
        proba_same_only = np.full(n_q, np.nan, dtype=np.float64)

        cert_sqrt2w = np.zeros(n_q, dtype=bool)
        cert_same_w = np.zeros(n_q, dtype=bool)
        fb_zero = ohe_sum_q == 0.0
        fb_lt_k = np.zeros(n_q, dtype=bool)
        fb_bound = np.zeros(n_q, dtype=bool)

        t_local0 = time.perf_counter()

        # Group non-zero-OHE queries by occupation for fast batched dense matrix distances
        occ_to_qpos: Dict[str, List[int]] = {}
        for i in range(n_q):
            if fb_zero[i]:
                continue
            occ = str(occ_q[i])
            if self._occ_counts.get(occ, 0) < k:
                fb_lt_k[i] = True
                continue
            occ_to_qpos.setdefault(occ, []).append(i)

        has_zero_pool = len(self._zero_y) > 0
        for occ, pos_list in occ_to_qpos.items():
            pos_arr = np.asarray(pos_list, dtype=np.int64)
            Xq_sub = X_q_dense[pos_arr]
            Xtr_occ = self._occ_to_X[occ]
            ytr_occ = self._occ_to_y[occ]

            # Exact squared Euclidean distances within same occupation
            d2_same = cdist(Xq_sub, Xtr_occ, metric="sqeuclidean")

            # Same-occ-only top-k
            if d2_same.shape[1] == k:
                part_same = np.arange(k)[np.newaxis, :]
                dk2_same = np.max(d2_same, axis=1)
                p_same = np.full(len(pos_arr), float(np.mean(ytr_occ)), dtype=np.float64)
            else:
                part_same = np.argpartition(d2_same, kth=k - 1, axis=1)[:, :k]
                row_ar = np.arange(len(pos_arr))[:, np.newaxis]
                top_d2_same = d2_same[row_ar, part_same]
                dk2_same = np.max(top_d2_same, axis=1)
                p_same = np.mean(ytr_occ[part_same], axis=1)

            proba_same_only[pos_arr] = p_same
            cert_same_w[pos_arr] = dk2_same < (bound_w_sq - 1e-6)

            # Combined same-occ + zero-OHE baseline pool (47 rows) with exact +w^2 offset
            if has_zero_pool:
                d2_zero = cdist(Xq_sub, self._zero_X, metric="sqeuclidean") + w_sq
                d2_comb = np.hstack([d2_same, d2_zero])
                y_comb = np.concatenate([ytr_occ, self._zero_y])
            else:
                d2_comb = d2_same
                y_comb = ytr_occ

            part_comb = np.argpartition(d2_comb, kth=k - 1, axis=1)[:, :k]
            row_ar = np.arange(len(pos_arr))[:, np.newaxis]
            top_d2_comb = d2_comb[row_ar, part_comb]
            dk2_comb = np.max(top_d2_comb, axis=1)
            p_comb = np.mean(y_comb[part_comb], axis=1)

            ok_bound = dk2_comb < (bound_sqrt2w_sq - 1e-5)
            cert_sqrt2w[pos_arr] = ok_bound
            fb_bound[pos_arr] = ~ok_bound
            proba_cert[pos_arr[ok_bound]] = p_comb[ok_bound]

        local_s = time.perf_counter() - t_local0

        # Batched exact CSR fallback: time (<k / zero-OHE) separately from (bound-exceeded) for fair mode timings
        fb_base_positions = np.flatnonzero(fb_zero | fb_lt_k)
        fb_bound_positions = np.flatnonzero(fb_bound & ~(fb_zero | fb_lt_k))

        t_fb_base0 = time.perf_counter()
        if len(fb_base_positions) > 0:
            X_fb_base = test_blocks.build_knn_w_matrix(w=w, row_idx=q_idx[fb_base_positions])
            p_fb_base = self._full_knn.predict_proba(X_fb_base)[:, 1]
            proba_cert[fb_base_positions] = p_fb_base
            proba_same_only[fb_base_positions] = p_fb_base
        fallback_base_s = time.perf_counter() - t_fb_base0

        t_fb_bnd0 = time.perf_counter()
        if len(fb_bound_positions) > 0:
            X_fb_bnd = test_blocks.build_knn_w_matrix(w=w, row_idx=q_idx[fb_bound_positions])
            p_fb_bnd = self._full_knn.predict_proba(X_fb_bnd)[:, 1]
            proba_cert[fb_bound_positions] = p_fb_bnd
        fallback_bound_s = time.perf_counter() - t_fb_bnd0
        fallback_s = fallback_base_s + fallback_bound_s

        if np.isnan(proba_cert).any() or np.isnan(proba_same_only).any():
            raise AssertionError("NaN detected in ExactOccupationPrefilterKNN predictions!")

        return PrefilterPredictionResult(
            proba_certified_fallback=proba_cert,
            proba_same_occ_fallback_lt_k=proba_same_only,
            certified_sqrt2w_mask=cert_sqrt2w,
            certified_same_only_w_mask=cert_same_w,
            fallback_lt_k_mask=fb_lt_k,
            fallback_zero_ohe_mask=fb_zero,
            fallback_bound_exceeded_mask=fb_bound,
            index_build_s=self.index_build_s_,
            local_search_s=local_s,
            fallback_base_s=fallback_base_s,
            fallback_exact_s=fallback_s,
            total_prefilter_s=local_s + fallback_s,
        )


@dataclass(frozen=True)
class F1PurityPrefilterBundle:
    """Outputs of Section 14A.1 (F1: OHE audit, purity at w=8 by tier & ISCO, K2 tiers, prefilter benchmark)."""

    ohe_geometry_audit_table: pd.DataFrame
    purity_by_support_tier_table: pd.DataFrame
    purity_by_isco_table: pd.DataFrame
    k2_support_audit_table: pd.DataFrame
    prefilter_comparison_table: pd.DataFrame
    summary_dict: Dict[str, object]


@dataclass(frozen=True)
class F3SizeControlBundle:
    """Outputs of Section 14A.3 (F3: R4c_random_rows 5-seed control on KNN-D full test)."""

    per_seed_table: pd.DataFrame
    decomposition_summary_table: pd.DataFrame
    summary_dict: Dict[str, object]


@dataclass(frozen=True)
class F5CostRangeBundle:
    """Outputs of Section 14A.4 (F5: per-block KNN-W times and cost range slowdown table)."""

    block_times_table: pd.DataFrame
    cost_range_table: pd.DataFrame
    summary_dict: Dict[str, object]


class RevisionAnalysisRunner:
    """Execute all Section 14A post-review checks from disk caches without rerunning heavy full-test KNN."""

    def __init__(self, config: KNNConfig) -> None:
        self.config = config
        self.feature_builder = KNNFeatureBuilder(config)
        self.cache_verifier = CacheIntegrityVerifier(config)
        self.evaluator = KNNEvaluator(config)

    def load_version_a_and_caches(self) -> Tuple[KNNVersionBundle, CacheIntegrityBundle]:
        """Load Version A matrices/original units and verify all full-test cached predictions."""
        bundle_a = self.feature_builder.build_version_bundle(
            version=VERSION_CON, include_original_units=True
        )
        cache_bundle = self.cache_verifier.verify_all_fulltest_caches(bundle_a.test_blocks.y)
        return bundle_a, cache_bundle

    # ------------------------------------------------------------------
    # 14A.1 · F1: Purity at w=8, K2 support audit, and exact prefilter
    # ------------------------------------------------------------------
    def run_f1_purity_and_prefilter(
        self,
        bundle_a: KNNVersionBundle,
        cached_knn_w_proba: np.ndarray,
        n_queries: int = 5000,
        tau_knn_w: float = 0.28,
        k_neighbors: int = 101,
        w: float = 8.0,
    ) -> F1PurityPrefilterBundle:
        """Measure true neighbor purity at final w=8 on the 5,000 Step 9 queries and test exact prefiltering."""
        assert bundle_a.orig_train is not None and bundle_a.orig_test is not None
        tr_blocks = bundle_a.train_blocks
        te_blocks = bundle_a.test_blocks
        orig_tr = bundle_a.orig_train
        orig_te = bundle_a.orig_test

        q_idx = np.arange(min(int(n_queries), len(te_blocks.y)), dtype=np.int64)
        y_q = te_blocks.y[q_idx]
        g_q = te_blocks.groups[q_idx]
        p_cache_q = cached_knn_w_proba[q_idx]

        # 1. Audit OHE row sums & drop='first' baseline effect
        rs_tr = np.asarray(tr_blocks.ohe_sparse.sum(axis=1)).ravel()
        rs_te = np.asarray(te_blocks.ohe_sparse.sum(axis=1)).ravel()
        occ_tr_arr = orig_tr["occupation_code"].to_numpy(dtype=str)
        occ_te_arr = orig_te["occupation_code"].to_numpy(dtype=str)
        isco_tr_arr = orig_tr["isco_major"].to_numpy(dtype=str)
        isco_te_arr = orig_te["isco_major"].to_numpy(dtype=str)

        tr_counts_series = orig_tr["occupation_code"].value_counts()
        tr_counts_map: Dict[str, int] = {str(k): int(v) for k, v in tr_counts_series.items()}

        te_occ_support_full = np.array([tr_counts_map.get(c, 0) for c in occ_te_arr], dtype=np.int64)
        q_occ_support = te_occ_support_full[q_idx]

        zero_tr_occs = sorted(set(occ_tr_arr[rs_tr == 0.0].tolist()))
        te_zero_mask = rs_te == 0.0
        te_unseen_mask = np.array([c not in tr_counts_map for c in occ_te_arr], dtype=bool)

        ohe_audit_df = pd.DataFrame(
            [
                {
                    "particion": "Train completo",
                    "filas_totales": int(len(rs_tr)),
                    "filas_con_1_dummy_activa": int((rs_tr == 1.0).sum()),
                    "pct_con_1_dummy": round(100.0 * float((rs_tr == 1.0).mean()), 4),
                    "filas_con_vector_cero": int((rs_tr == 0.0).sum()),
                    "pct_vector_cero": round(100.0 * float((rs_tr == 0.0).mean()), 4),
                    "detalle_vector_cero": f"Categoría base omitida por drop='first': {zero_tr_occs}",
                },
                {
                    "particion": "Test completo",
                    "filas_totales": int(len(rs_te)),
                    "filas_con_1_dummy_activa": int((rs_te == 1.0).sum()),
                    "pct_con_1_dummy": round(100.0 * float((rs_te == 1.0).mean()), 4),
                    "filas_con_vector_cero": int(te_zero_mask.sum()),
                    "pct_vector_cero": round(100.0 * float(te_zero_mask.mean()), 4),
                    "detalle_vector_cero": (
                        f"{int((te_zero_mask & ~te_unseen_mask).sum())} filas de {zero_tr_occs} + "
                        f"{int(te_unseen_mask.sum())} filas de {int(len(set(occ_te_arr[te_unseen_mask])))} ocupaciones no vistas en train"
                    ),
                },
                {
                    "particion": f"Consultas Paso 9 ({len(q_idx):,} filas)",
                    "filas_totales": int(len(q_idx)),
                    "filas_con_1_dummy_activa": int((rs_te[q_idx] == 1.0).sum()),
                    "pct_con_1_dummy": round(100.0 * float((rs_te[q_idx] == 1.0).mean()), 4),
                    "filas_con_vector_cero": int((rs_te[q_idx] == 0.0).sum()),
                    "pct_vector_cero": round(100.0 * float((rs_te[q_idx] == 0.0).mean()), 4),
                    "detalle_vector_cero": (
                        f"Cota OHE exacta: w={w:g} vs. base omitida; sqrt(2)*w={w * np.sqrt(2.0):.4f} vs. otras ocupaciones"
                    ),
                },
            ]
        )

        # 2. Exact KNN-W (k=101, uniform, euclidean, w=8) returning neighbors on the 5,000 Step 9 queries
        X_w_tr = tr_blocks.build_knn_w_matrix(w=w)
        X_w_q = te_blocks.build_knn_w_matrix(w=w, row_idx=q_idx)
        exact_knn = build_knn_classifier(
            KNNModelSpec(
                model_id=MODEL_KNN_W,
                n_neighbors=k_neighbors,
                weights="uniform",
                metric="euclidean",
                algorithm="brute",
                block_weight=w,
                n_jobs=self.config.n_jobs,
            )
        )
        t_fit_ex = time.perf_counter()
        exact_knn.fit(X_w_tr, tr_blocks.y)
        fit_ex_s = time.perf_counter() - t_fit_ex

        t_q_ex = time.perf_counter()
        nn_dists, nn_idx = exact_knn.kneighbors(X_w_q, n_neighbors=k_neighbors, return_distance=True)
        exact_query_s = time.perf_counter() - t_q_ex
        p_exact_q = np.mean(tr_blocks.y[nn_idx], axis=1)
        exact_vs_cache_diff = float(np.max(np.abs(p_exact_q - p_cache_q)))

        del exact_knn, X_w_tr, X_w_q
        gc.collect()

        occ_q_arr = occ_te_arr[q_idx]
        isco_q_arr = isco_te_arr[q_idx]
        same_occ_per_q = (occ_tr_arr[nn_idx] == occ_q_arr[:, np.newaxis]).mean(axis=1) * 100.0
        same_isco_per_q = (isco_tr_arr[nn_idx] == isco_q_arr[:, np.newaxis]).mean(axis=1) * 100.0
        dk_exact = nn_dists[:, -1]

        # 3. Purity table by training support tier + overall + full-test share comparison
        tier_defs = [
            ("Global (5,000 consultas)", np.ones(len(q_idx), dtype=bool), np.ones(len(occ_te_arr), dtype=bool)),
            ("Soporte en train < 101 filas", q_occ_support < 101, te_occ_support_full < 101),
            (
                "Soporte en train 101 a 1,000 filas",
                (q_occ_support >= 101) & (q_occ_support <= 1000),
                (te_occ_support_full >= 101) & (te_occ_support_full <= 1000),
            ),
            ("Soporte en train > 1,000 filas", q_occ_support > 1000, te_occ_support_full > 1000),
        ]
        tier_rows: List[Dict[str, object]] = []
        for lbl, mq, m_full in tier_defs:
            nq = int(mq.sum())
            tier_rows.append(
                {
                    "tramo_soporte_ocupacion_train": lbl,
                    "filas_test_completo": int(m_full.sum()),
                    "pct_test_completo": round(100.0 * float(m_full.mean()), 2),
                    "consultas_evaluadas": nq,
                    "pct_consultas": round(100.0 * nq / float(len(q_idx)), 2),
                    "pureza_misma_ocupacion_media_pct": round(float(np.mean(same_occ_per_q[mq])), 2) if nq > 0 else np.nan,
                    "pureza_misma_ocupacion_mediana_pct": round(float(np.median(same_occ_per_q[mq])), 2) if nq > 0 else np.nan,
                    "pct_consultas_con_100pct_pureza_esco": round(100.0 * float(np.mean(same_occ_per_q[mq] >= 99.999)), 2) if nq > 0 else np.nan,
                    "pureza_mismo_isco_media_pct": round(float(np.mean(same_isco_per_q[mq])), 2) if nq > 0 else np.nan,
                    "dist_mediana_vecino_101": round(float(np.median(dk_exact[mq])), 4) if nq > 0 else np.nan,
                }
            )
        purity_tier_df = pd.DataFrame(tier_rows)

        # 4. Purity table by ISCO major group
        isco_rows: List[Dict[str, object]] = []
        for digit in sorted(ISCO_MAJOR_LABELS_ES.keys()):
            mq = isco_q_arr == digit
            m_full = isco_te_arr == digit
            nq = int(mq.sum())
            isco_rows.append(
                {
                    "isco_major": digit,
                    "gran_grupo_isco": ISCO_MAJOR_LABELS_ES[digit],
                    "consultas_5000": nq,
                    "pct_test_completo_con_soporte_lt_101": round(
                        100.0 * float((te_occ_support_full[m_full] < 101).mean()), 2
                    )
                    if m_full.any()
                    else np.nan,
                    "pureza_misma_ocupacion_media_pct": round(float(np.mean(same_occ_per_q[mq])), 2) if nq > 0 else np.nan,
                    "pct_consultas_con_100pct_pureza_esco": round(100.0 * float(np.mean(same_occ_per_q[mq] >= 99.999)), 2) if nq > 0 else np.nan,
                    "pureza_mismo_isco_media_pct": round(float(np.mean(same_isco_per_q[mq])), 2) if nq > 0 else np.nan,
                }
            )
        purity_isco_df = pd.DataFrame(isco_rows)

        # 5. K2 6-profile support-tier audit
        k2_path = self.config.tables_dir / "12_k2a_explicacion_6_perfiles_resumen.csv"
        k2_df = pd.read_csv(k2_path, encoding="utf-8")
        occ_ranks = tr_counts_series.rank(ascending=False, method="min")
        n_total_occs_tr = int(len(tr_counts_series))
        k2_rows: List[Dict[str, object]] = []
        for _, r in k2_df.iterrows():
            occ_code = str(r["ocupacion_esco"]).split(" · ")[0].strip()
            sup_tr = tr_counts_map.get(occ_code, 0)
            tier_lbl = (
                "< 101 filas"
                if sup_tr < 101
                else ("101 a 1,000 filas" if sup_tr <= 1000 else "> 1,000 filas")
            )
            rk = int(occ_ranks.get(occ_code, n_total_occs_tr))
            k2_rows.append(
                {
                    "perfil_id": str(r["perfil_id"]),
                    "fila_test_idx": int(r["fila_test_idx"]),
                    "ocupacion_esco": str(r["ocupacion_esco"]),
                    "soporte_ocupacion_en_train": int(sup_tr),
                    "tramo_soporte_train": tier_lbl,
                    "rango_frecuencia_entre_2968": f"{rk} / {n_total_occs_tr}",
                    "pureza_esco_k2_pct": float(r["pureza_misma_ocupacion_pct"]),
                    "criterio_seleccion_k2": "Primera fila de test que cumple los cuantiles del perfil P2 (sesga hacia oficios frecuentes)",
                }
            )
        k2_audit_df = pd.DataFrame(k2_rows)

        # 6. Exact prefilter experiment on the EXACT SAME 5,000 queries
        prefilter = ExactOccupationPrefilterKNN(
            n_neighbors=k_neighbors, block_weight=w, n_jobs=self.config.n_jobs
        )
        prefilter.fit(tr_blocks, orig_tr)
        pf_res = prefilter.predict_with_diagnostics(te_blocks, orig_te, q_idx)

        exact_s_per_1k = exact_query_s / (len(q_idx) / 1000.0)
        pf_s_per_1k = pf_res.total_prefilter_s / (len(q_idx) / 1000.0)
        pf_local_only_s_per_1k = pf_res.local_search_s / (len(q_idx) / 1000.0)

        pf_rows: List[Dict[str, object]] = []
        for mode_lbl, p_pred, pred_s, cert_share, fb_share in [
            (
                "1. Búsqueda exacta completa CSR (referencia Paso 9 · 5,000 consultas)",
                p_exact_q,
                exact_query_s,
                100.0,
                100.0,
            ),
            (
                "2. Prefiltro exacto certificado (misma ocupación + 47 base cero; respaldo si d_k >= sqrt(2)*w o soporte < 101)",
                pf_res.proba_certified_fallback,
                pf_res.total_prefilter_s,
                100.0 * float(pf_res.certified_sqrt2w_mask.mean()),
                100.0 * float((~pf_res.certified_sqrt2w_mask).mean()),
            ),
            (
                "3. Prefiltro solo misma ocupación (respaldo solo si soporte < 101 o vector cero; sin respaldo por cota d_k)",
                pf_res.proba_same_occ_fallback_lt_k,
                pf_res.local_search_s + pf_res.fallback_base_s,
                100.0 * float(pf_res.certified_same_only_w_mask.mean()),
                100.0 * float((pf_res.fallback_lt_k_mask | pf_res.fallback_zero_ohe_mask).mean()),
            ),
        ]:
            rho = float(stats.spearmanr(p_pred, p_cache_q).statistic)
            max_diff = float(np.max(np.abs(p_pred - p_cache_q)))
            mean_diff = float(np.mean(np.abs(p_pred - p_cache_q)))
            agree_tau = 100.0 * float(np.mean((p_pred >= tau_knn_w) == (p_cache_q >= tau_knn_w)))
            paired = paired_bootstrap_person_diffs(
                y_true=y_q,
                prob_a=p_pred,
                prob_b=p_cache_q,
                groups=g_q,
                threshold_a=tau_knn_w,
                threshold_b=tau_knn_w,
                n_resamples=300,
                random_state=self.config.random_state,
            )
            s_1k = pred_s / (len(q_idx) / 1000.0)
            pf_rows.append(
                {
                    "metodo_evaluado": mode_lbl,
                    "consultas_evaluadas": int(len(q_idx)),
                    "pct_certificado_por_cota_exacta": round(cert_share, 2),
                    "pct_enviado_a_respaldo_completo": round(fb_share, 2),
                    "spearman_vs_exacto_cache": round(rho, 6),
                    "max_diff_abs_puntaje": round(max_diff, 6),
                    "media_diff_abs_puntaje": round(mean_diff, 6),
                    "acuerdo_alertas_tau_028_pct": round(agree_tau, 2),
                    "pr_auc_5000": round(float(average_precision_score(y_q, p_pred)), 4),
                    "delta_pr_auc_vs_exacto": round(float(paired["delta_pr_auc"]), 6),
                    "ic95_pareado_delta_pr_auc": f"[{float(paired['delta_pr_auc_ci_low']):+.6f}, {float(paired['delta_pr_auc_ci_high']):+.6f}]",
                    "tiempo_total_5000_s": round(pred_s, 3),
                    "tiempo_por_1000_consultas_s": round(s_1k, 3),
                    "factor_aceleracion_vs_exacto": round(exact_s_per_1k / max(s_1k, 1e-6), 2),
                }
            )

        prefilter_df = pd.DataFrame(pf_rows)
        summary = {
            "n_queries": int(len(q_idx)),
            "exact_vs_cache_max_diff": round(exact_vs_cache_diff, 8),
            "exact_fit_s": round(fit_ex_s, 3),
            "exact_query_5000_s": round(exact_query_s, 3),
            "exact_s_per_1k": round(exact_s_per_1k, 3),
            "prefilter_index_build_s": round(pf_res.index_build_s, 3),
            "prefilter_local_s": round(pf_res.local_search_s, 3),
            "prefilter_fallback_s": round(pf_res.fallback_exact_s, 3),
            "prefilter_total_s": round(pf_res.total_prefilter_s, 3),
            "prefilter_s_per_1k": round(pf_s_per_1k, 3),
            "prefilter_local_only_s_per_1k": round(pf_local_only_s_per_1k, 3),
            "speedup_factor": round(exact_s_per_1k / max(pf_s_per_1k, 1e-6), 2),
            "pct_test_full_occ_lt_101": round(100.0 * float((te_occ_support_full < 101).mean()), 2),
            "n_test_full_occ_lt_101": int((te_occ_support_full < 101).sum()),
            "pct_q5000_certified_sqrt2w": round(100.0 * float(pf_res.certified_sqrt2w_mask.mean()), 2),
            "pct_q5000_certified_same_w": round(100.0 * float(pf_res.certified_same_only_w_mask.mean()), 2),
            "n_q5000_fallback_lt_k": int(pf_res.fallback_lt_k_mask.sum()),
            "n_q5000_fallback_zero_ohe": int(pf_res.fallback_zero_ohe_mask.sum()),
            "n_q5000_fallback_bound_exceeded": int(pf_res.fallback_bound_exceeded_mask.sum()),
            "purity_esco_global_w8_pct": round(float(np.mean(same_occ_per_q)), 2),
            "purity_isco_global_w8_pct": round(float(np.mean(same_isco_per_q)), 2),
        }

        return F1PurityPrefilterBundle(
            ohe_geometry_audit_table=ohe_audit_df,
            purity_by_support_tier_table=purity_tier_df,
            purity_by_isco_table=purity_isco_df,
            k2_support_audit_table=k2_audit_df,
            prefilter_comparison_table=prefilter_df,
            summary_dict=summary,
        )

    # ------------------------------------------------------------------
    # 14A.2 · F2: L1 minus L2 gap table across all regimes (from 04d)
    # ------------------------------------------------------------------
    def build_f2_l1_l2_gap_table(self) -> pd.DataFrame:
        """Build explicit L1 (Manhattan) minus L2 (Euclidean) CV PR-AUC & ROC-AUC gap table from 04d."""
        p04d = self.config.tables_dir / "04d_sensibilidad_escala_outliers_version_b_cv.csv"
        df = pd.read_csv(p04d, encoding="utf-8")

        order_ids = [
            "R1_A_crudo",
            "R2_A_escalado",
            "R3_A_wins_tukey",
            "R5_B_iqr",
            "R4_A_solo_inliers",
        ]
        rows: List[Dict[str, object]] = []
        for reg_id in order_ids:
            sub = df.loc[df["regimen_id"] == reg_id]
            r_l1 = sub.loc[sub["metrica"] == "manhattan"].iloc[0]
            r_l2 = sub.loc[sub["metrica"] == "euclidean"].iloc[0]
            gap_pr = float(r_l1["pr_auc_cv_media"]) - float(r_l2["pr_auc_cv_media"])
            gap_roc = float(r_l1["roc_auc_cv_media"]) - float(r_l2["roc_auc_cv_media"])
            if reg_id in ("R3_A_wins_tukey", "R5_B_iqr"):
                nota = "La brecha NO disminuye al recortar extremos (refuta que los extremos expliquen L1 > L2)"
            elif reg_id == "R4_A_solo_inliers":
                nota = "Al eliminar extremos del train la brecha incluso crece (L2 sufre más en la frontera de extrapolación)"
            elif reg_id == "R2_A_escalado":
                nota = "Referencia principal escalada; brecha casi idéntica a los regímenes winsorizados"
            else:
                nota = "L1 ya supera a L2 incluso sin reescalar"
            rows.append(
                {
                    "regimen_id": reg_id,
                    "regimen_datos": str(r_l1["regimen_datos"]),
                    "pr_auc_manhattan_L1": round(float(r_l1["pr_auc_cv_media"]), 5),
                    "pr_auc_euclidean_L2": round(float(r_l2["pr_auc_cv_media"]), 5),
                    "brecha_L1_menos_L2_pr_auc": round(gap_pr, 5),
                    "roc_auc_manhattan_L1": round(float(r_l1["roc_auc_cv_media"]), 5),
                    "roc_auc_euclidean_L2": round(float(r_l2["roc_auc_cv_media"]), 5),
                    "brecha_L1_menos_L2_roc_auc": round(gap_roc, 5),
                    "lectura_diagnostica": nota,
                }
            )
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # 14A.3 · F3: Random row-removal size control (R4c_random_rows, 5 seeds)
    # ------------------------------------------------------------------
    def run_f3_random_size_control(
        self,
        bundle_a: KNNVersionBundle,
        cached_knn_d_proba: np.ndarray,
        seeds: Sequence[int] = (42, 43, 44, 45, 46),
    ) -> F3SizeControlBundle:
        """Control experiment removing the exact same number of rows as R4 at random across 5 fixed seeds."""
        tr_blocks = bundle_a.train_blocks
        te_blocks = bundle_a.test_blocks
        y_tr = tr_blocks.y
        y_te = te_blocks.y
        g_te = te_blocks.groups

        # Compute exact Tukey extreme mask on full train (same rule as VersionSensitivityAnalyzer)
        _, any_ext_tr, _, _ = VersionSensitivityAnalyzer.compute_tukey_audit(
            dense_train_df=tr_blocks.dense_clean_df,
            dense_test_df=te_blocks.dense_clean_df,
            y_train=y_tr,
            y_test=y_te,
            active_dense_features=tr_blocks.active_dense_features,
        )
        keep_inliers = ~any_ext_tr
        n_keep = int(keep_inliers.sum())
        n_removed = int(any_ext_tr.sum())

        knn_d_spec = KNNModelSpec(
            model_id=MODEL_KNN_D,
            n_neighbors=101,
            weights="uniform",
            metric="manhattan",
            algorithm="kd_tree",
            block_weight=0.0,
            n_jobs=self.config.n_jobs,
        )

        # Recompute R4_A_solo_inliers on full test once (~50 s) to get exact vector for paired CIs vs R4c
        sc_r4 = AuditedStandardBinaryScaler(self.config.near_constant_threshold_pct)
        X_tr_r4 = sc_r4.fit_transform(tr_blocks.dense_clean_df.iloc[keep_inliers])
        X_te_r4 = sc_r4.transform(te_blocks.dense_clean_df)
        est_r4 = build_knn_classifier(knn_d_spec)
        t0_r4 = time.perf_counter()
        est_r4.fit(X_tr_r4, y_tr[keep_inliers])
        p_r4 = est_r4.predict_proba(X_te_r4)[:, 1]
        t_r4 = time.perf_counter() - t0_r4
        del est_r4, X_tr_r4, X_te_r4
        gc.collect()

        m_r2 = compute_classification_metrics(y_te, cached_knn_d_proba, threshold=0.26)
        m_r4 = compute_classification_metrics(y_te, p_r4, threshold=0.25)

        seed_rows: List[Dict[str, object]] = []
        r4c_probas: List[np.ndarray] = []
        r4c_pr_vals: List[float] = []
        r4c_roc_vals: List[float] = []
        r4c_brier_vals: List[float] = []

        for seed in seeds:
            rng = np.random.default_rng(int(seed))
            keep_rand = np.sort(rng.choice(len(y_tr), size=n_keep, replace=False))
            sc_c = AuditedStandardBinaryScaler(self.config.near_constant_threshold_pct)
            X_tr_c = sc_c.fit_transform(tr_blocks.dense_clean_df.iloc[keep_rand])
            X_te_c = sc_c.transform(te_blocks.dense_clean_df)

            est_c = build_knn_classifier(knn_d_spec)
            t0 = time.perf_counter()
            est_c.fit(X_tr_c, y_tr[keep_rand])
            p_c = est_c.predict_proba(X_te_c)[:, 1]
            dt = time.perf_counter() - t0
            del est_c, X_tr_c, X_te_c
            gc.collect()

            m_c = compute_classification_metrics(y_te, p_c, threshold=0.26)
            cmp_vs_r2 = paired_bootstrap_person_diffs(
                y_true=y_te,
                prob_a=p_c,
                prob_b=cached_knn_d_proba,
                groups=g_te,
                n_resamples=self.config.bootstrap_resamples,
                random_state=self.config.random_state,
            )
            cmp_r4_vs_c = paired_bootstrap_person_diffs(
                y_true=y_te,
                prob_a=p_r4,
                prob_b=p_c,
                groups=g_te,
                n_resamples=self.config.bootstrap_resamples,
                random_state=self.config.random_state,
            )

            r4c_probas.append(p_c)
            r4c_pr_vals.append(m_c["pr_auc"])
            r4c_roc_vals.append(m_c["roc_auc"])
            r4c_brier_vals.append(m_c["brier"])

            seed_rows.append(
                {
                    "regimen_id": f"R4c_random_rows (semilla={int(seed)})",
                    "semilla": int(seed),
                    "n_train_efectivo": int(n_keep),
                    "filas_eliminadas": int(n_removed),
                    "pr_auc_test": round(m_c["pr_auc"], 5),
                    "roc_auc_test": round(m_c["roc_auc"], 5),
                    "brier_test": round(m_c["brier"], 4),
                    "delta_pr_vs_R2_escalado": round(float(cmp_vs_r2["delta_pr_auc"]), 5),
                    "ic95_delta_pr_vs_R2": f"[{float(cmp_vs_r2['delta_pr_auc_ci_low']):+.5f}, {float(cmp_vs_r2['delta_pr_auc_ci_high']):+.5f}]",
                    "delta_pr_R4_menos_R4c": round(float(cmp_r4_vs_c["delta_pr_auc"]), 5),
                    "ic95_delta_pr_R4_menos_R4c": f"[{float(cmp_r4_vs_c['delta_pr_auc_ci_low']):+.5f}, {float(cmp_r4_vs_c['delta_pr_auc_ci_high']):+.5f}]",
                    "tiempo_s": round(dt, 2),
                }
            )

        # Pick median-PR-AUC seed for representative single-run paired bootstrap + compute mean across seeds
        med_idx = int(np.argsort(r4c_pr_vals)[len(r4c_pr_vals) // 2])
        p_r4c_med = r4c_probas[med_idx]
        med_seed = int(seeds[med_idx])

        cmp_total = paired_bootstrap_person_diffs(
            y_true=y_te, prob_a=p_r4, prob_b=cached_knn_d_proba, groups=g_te,
            n_resamples=self.config.bootstrap_resamples, random_state=self.config.random_state,
        )
        cmp_size = paired_bootstrap_person_diffs(
            y_true=y_te, prob_a=p_r4c_med, prob_b=cached_knn_d_proba, groups=g_te,
            n_resamples=self.config.bootstrap_resamples, random_state=self.config.random_state,
        )
        cmp_extremes = paired_bootstrap_person_diffs(
            y_true=y_te, prob_a=p_r4, prob_b=p_r4c_med, groups=g_te,
            n_resamples=self.config.bootstrap_resamples, random_state=self.config.random_state,
        )

        mean_r4c_pr = float(np.mean(r4c_pr_vals))
        mean_r4c_roc = float(np.mean(r4c_roc_vals))
        total_loss_pr = m_r4["pr_auc"] - m_r2["pr_auc"]
        size_loss_pr = mean_r4c_pr - m_r2["pr_auc"]
        ext_loss_pr = m_r4["pr_auc"] - mean_r4c_pr

        pct_due_to_size = 100.0 * size_loss_pr / total_loss_pr if abs(total_loss_pr) > 1e-12 else 0.0
        pct_due_to_extremes = 100.0 * ext_loss_pr / total_loss_pr if abs(total_loss_pr) > 1e-12 else 0.0

        decomp_df = pd.DataFrame(
            [
                {
                    "componente": "1. Referencia completa R2_A_escalado (100 % train)",
                    "n_train": int(len(y_tr)),
                    "pr_auc_media_test": round(m_r2["pr_auc"], 5),
                    "rango_pr_auc_5_semillas": "Referencia única",
                    "roc_auc_media_test": round(m_r2["roc_auc"], 5),
                    "delta_pr_auc": 0.0,
                    "ic95_pareado_persona": "Referencia",
                    "pct_de_la_perdida_total_R4": 0.0,
                },
                {
                    "componente": f"2. Control R4c_random_rows (borrado aleatorio de {n_removed:,} filas · media 5 semillas)",
                    "n_train": int(n_keep),
                    "pr_auc_media_test": round(mean_r4c_pr, 5),
                    "rango_pr_auc_5_semillas": f"[{min(r4c_pr_vals):.5f}, {max(r4c_pr_vals):.5f}]",
                    "roc_auc_media_test": round(mean_r4c_roc, 5),
                    "delta_pr_auc": round(size_loss_pr, 5),
                    "ic95_pareado_persona": (
                        f"Semilla mediana ({med_seed}) vs. R2: "
                        f"[{float(cmp_size['delta_pr_auc_ci_low']):+.5f}, {float(cmp_size['delta_pr_auc_ci_high']):+.5f}]"
                    ),
                    "pct_de_la_perdida_total_R4": round(pct_due_to_size, 1),
                },
                {
                    "componente": "3. R4_A_solo_inliers menos R4c_random_rows (efecto puro de eliminar extremos a igual N)",
                    "n_train": int(n_keep),
                    "pr_auc_media_test": round(m_r4["pr_auc"], 5),
                    "rango_pr_auc_5_semillas": "Comparación a igual N=1,042,397",
                    "roc_auc_media_test": round(m_r4["roc_auc"], 5),
                    "delta_pr_auc": round(ext_loss_pr, 5),
                    "ic95_pareado_persona": (
                        f"R4 vs. semilla mediana ({med_seed}): "
                        f"[{float(cmp_extremes['delta_pr_auc_ci_low']):+.5f}, {float(cmp_extremes['delta_pr_auc_ci_high']):+.5f}]"
                    ),
                    "pct_de_la_perdida_total_R4": round(pct_due_to_extremes, 1),
                },
                {
                    "componente": "4. Pérdida total R4_A_solo_inliers menos R2_A_escalado (tamaño + extremos)",
                    "n_train": int(n_keep),
                    "pr_auc_media_test": round(m_r4["pr_auc"], 5),
                    "rango_pr_auc_5_semillas": "Total acumulado",
                    "roc_auc_media_test": round(m_r4["roc_auc"], 5),
                    "delta_pr_auc": round(total_loss_pr, 5),
                    "ic95_pareado_persona": (
                        f"R4 vs. R2: "
                        f"[{float(cmp_total['delta_pr_auc_ci_low']):+.5f}, {float(cmp_total['delta_pr_auc_ci_high']):+.5f}]"
                    ),
                    "pct_de_la_perdida_total_R4": 100.0,
                },
            ]
        )

        summary = {
            "n_train_r2": int(len(y_tr)),
            "n_train_r4_y_r4c": int(n_keep),
            "n_removed": int(n_removed),
            "r2_pr_auc": round(m_r2["pr_auc"], 5),
            "r4c_pr_auc_mean": round(mean_r4c_pr, 5),
            "r4c_pr_auc_min": round(min(r4c_pr_vals), 5),
            "r4c_pr_auc_max": round(max(r4c_pr_vals), 5),
            "r4_pr_auc": round(m_r4["pr_auc"], 5),
            "total_loss_pr": round(total_loss_pr, 5),
            "size_loss_pr": round(size_loss_pr, 5),
            "extremes_loss_pr": round(ext_loss_pr, 5),
            "pct_due_to_size": round(pct_due_to_size, 1),
            "pct_due_to_extremes": round(pct_due_to_extremes, 1),
            "median_seed": med_seed,
            "r4_recompute_s": round(t_r4, 2),
        }

        return F3SizeControlBundle(
            per_seed_table=pd.DataFrame(seed_rows),
            decomposition_summary_table=decomp_df,
            summary_dict=summary,
        )

    # ------------------------------------------------------------------
    # 14A.4 · F5: Cost as a range & per-block throttling times (KNN-W)
    # ------------------------------------------------------------------
    def run_f5_cost_range_and_block_times(
        self,
        knn_w_manifest: Dict[str, object],
    ) -> F5CostRangeBundle:
        """Analyze per-block KNN-W runtimes from manifest.json and compute cost-range slowdown bounds."""
        chunk_times: Dict[str, float] = dict(knn_w_manifest["chunk_times_s"])  # type: ignore[arg-type]
        n_chunks = int(knn_w_manifest["n_chunks"])
        n_queries = int(knn_w_manifest["n_queries"])
        chunk_size = int(knn_w_manifest["metadata"]["chunk_size"])  # type: ignore[index]

        ref_08 = pd.read_csv(
            self.config.tables_dir / "08_benchmark_paso9_proyeccion_test_completo.csv",
            encoding="utf-8",
        )
        ref_13f = pd.read_csv(
            self.config.tables_dir / "13f_comparacion_costos_computacionales.csv",
            encoding="utf-8",
        )

        row_08_w = ref_08.loc[ref_08["modelo_id"] == MODEL_KNN_W].iloc[0]
        bench_5k_s = float(row_08_w["tiempo_predict_benchmark_s"])
        bench_1k_s = float(row_08_w["s_por_1000_filas_test"])
        bench_total_h = float(row_08_w["proyeccion_test_completo_horas"])
        bench_total_s = bench_total_h * 3600.0

        row_13f_w = ref_13f.loc[ref_13f["modelo"].astype(str).str.startswith("KNN-W")].iloc[0]
        real_total_s = float(row_13f_w["tiempo_predict_total_eval_s"])
        real_total_h = real_total_s / 3600.0
        real_1k_s = float(row_13f_w["tiempo_predict_por_1000_filas_s"])

        nb_h_s = float(ref_13f.loc[ref_13f["modelo"].astype(str).str.contains("NB-H"), "tiempo_predict_total_eval_s"].iloc[0])
        logit_s = float(ref_13f.loc[ref_13f["modelo"].astype(str).str.contains("Logística"), "tiempo_predict_total_eval_s"].iloc[0])

        blk_rows: List[Dict[str, object]] = []
        for idx in range(n_chunks):
            dt = float(chunk_times[str(idx)])
            rows_in_blk = min(chunk_size, n_queries - idx * chunk_size)
            s_per_1k = dt / (rows_in_blk / 1000.0)
            phase = "Secuencial (bloques 0–56)" if idx <= 56 else "Paralelo multi-proceso (bloques 57–69)"
            blk_rows.append(
                {
                    "bloque_idx": idx,
                    "filas_bloque": rows_in_blk,
                    "tiempo_bloque_s": round(dt, 2),
                    "s_por_1000_filas": round(s_per_1k, 2),
                    "fase_ejecucion": phase,
                    "ratio_vs_benchmark_sin_estrangulacion": round(s_per_1k / max(bench_1k_s, 1e-6), 2),
                }
            )
        blk_df = pd.DataFrame(blk_rows)

        cost_range_df = pd.DataFrame(
            [
                {
                    "escenario_costo_knn_w": "Cota inferior · Benchmark Paso 9 sin estrangulación térmica (5,000 filas extrapolado)",
                    "tiempo_total_test_s": round(bench_total_s, 1),
                    "tiempo_total_test_horas": round(bench_total_h, 3),
                    "s_por_1000_filas": round(bench_1k_s, 3),
                    "veces_mas_lento_que_NB_H": round(bench_total_s / max(nb_h_s, 1e-6), 0),
                    "ordenes_magnitud_vs_NB_H": round(float(np.log10(bench_total_s / max(nb_h_s, 1e-6))), 2),
                    "veces_mas_lento_que_Logistica_6_0": round(bench_total_s / max(logit_s, 1e-6), 0),
                    "ordenes_magnitud_vs_Logistica": round(float(np.log10(bench_total_s / max(logit_s, 1e-6))), 2),
                },
                {
                    "escenario_costo_knn_w": "Cota superior · Tiempo acumulado real de los 70 bloques (con estrangulación térmica y concurrencia)",
                    "tiempo_total_test_s": round(real_total_s, 2),
                    "tiempo_total_test_horas": round(real_total_h, 3),
                    "s_por_1000_filas": round(real_1k_s, 4),
                    "veces_mas_lento_que_NB_H": round(real_total_s / max(nb_h_s, 1e-6), 0),
                    "ordenes_magnitud_vs_NB_H": round(float(np.log10(real_total_s / max(nb_h_s, 1e-6))), 2),
                    "veces_mas_lento_que_Logistica_6_0": round(real_total_s / max(logit_s, 1e-6), 0),
                    "ordenes_magnitud_vs_Logistica": round(float(np.log10(real_total_s / max(logit_s, 1e-6))), 2),
                },
            ]
        )

        vals = blk_df["tiempo_bloque_s"].to_numpy(dtype=float)
        summary = {
            "n_chunks": n_chunks,
            "bench_5k_s": round(bench_5k_s, 2),
            "bench_total_h": round(bench_total_h, 3),
            "real_total_s": round(real_total_s, 2),
            "real_total_h": round(real_total_h, 3),
            "uncertainty_ratio_real_over_bench": round(real_total_h / max(bench_total_h, 1e-6), 2),
            "chunk_min_s": round(float(np.min(vals)), 2),
            "chunk_median_s": round(float(np.median(vals)), 2),
            "chunk_mean_s": round(float(np.mean(vals)), 2),
            "chunk_max_s": round(float(np.max(vals)), 2),
            "chunk_max_idx": int(np.argmax(vals)),
            "nb_h_total_s": nb_h_s,
            "logit_total_s": logit_s,
            "slowdown_nb_h_low": int(round(bench_total_s / max(nb_h_s, 1e-6))),
            "slowdown_nb_h_high": int(round(real_total_s / max(nb_h_s, 1e-6))),
            "slowdown_logit_low": int(round(bench_total_s / max(logit_s, 1e-6))),
            "slowdown_logit_high": int(round(real_total_s / max(logit_s, 1e-6))),
        }

        return F5CostRangeBundle(
            block_times_table=blk_df,
            cost_range_table=cost_range_df,
            summary_dict=summary,
        )

    # ------------------------------------------------------------------
    # 14A.5 · F6: Practical significance in counts + tie-aware alert match
    # ------------------------------------------------------------------
    def run_f6_practical_significance(
        self,
        bundle_a: KNNVersionBundle,
        cached_knn_w_proba: np.ndarray,
        base_probas: Dict[str, np.ndarray],
        base_taus: Dict[str, float],
        n_resamples: int = 1000,
    ) -> pd.DataFrame:
        """Compute plain TP-per-1,000-alerts gains and tie-aware exact alert-rate F1 comparisons with 95% CIs."""
        y_te = bundle_a.test_blocks.y
        g_te = bundle_a.test_blocks.groups
        p_knnw = cached_knn_w_proba
        p_nbh = base_probas["NB-H"]
        p_log = base_probas["LOGIT_6_0"]

        # Reference alert rate of NB-H (51.78%) and KNN-W own OOF alert rate (47.58%)
        nbh_alert_rate = float(np.mean(p_nbh >= base_taus["NB-H"]))
        knnw_oof_alert_rate = float(np.mean(p_knnw >= 0.28))

        rows: List[Dict[str, object]] = []
        for target_lbl, target_rate in [
            ("Igual tasa de alerta que NB-H (exacta tie-aware)", nbh_alert_rate),
            ("Igual tasa de alerta que KNN-W en tau*=0.28 (exacta tie-aware)", knnw_oof_alert_rate),
        ]:
            w_k, cut_k, raw_r_k, mat_r_k, lam_k = tie_aware_equal_alert_weights(p_knnw, target_rate)
            for comp_lbl, p_ref in [
                ("KNN-W vs. Logística Regularizada (6.0)", p_log),
                ("KNN-W vs. NB-H (7.1)", p_nbh),
            ]:
                w_ref, cut_ref, raw_r_ref, mat_r_ref, _ = tie_aware_equal_alert_weights(p_ref, target_rate)
                res = paired_bootstrap_practical_counts(
                    y_true=y_te,
                    weights_a=w_k,
                    weights_b=w_ref,
                    prob_a=p_knnw,
                    prob_b=p_ref,
                    groups=g_te,
                    n_resamples=n_resamples,
                    random_state=self.config.random_state,
                )
                rows.append(
                    {
                        "punto_comparacion": target_lbl,
                        "comparacion": comp_lbl,
                        "tasa_alerta_objetivo_pct": round(100.0 * target_rate, 2),
                        "tasa_alerta_discreta_bruta_knn_w_pct": round(100.0 * raw_r_k, 2),
                        "tasa_alerta_tie_aware_knn_w_pct": round(100.0 * mat_r_k, 2),
                        "tasa_alerta_tie_aware_ref_pct": round(100.0 * mat_r_ref, 2),
                        "lambda_frontera_knn_w": round(lam_k, 4),
                        "tp_por_1000_alertas_knn_w": round(res["tp_por_1000_alertas_A"], 2),
                        "tp_por_1000_alertas_ref": round(res["tp_por_1000_alertas_B"], 2),
                        "delta_tp_por_1000_alertas": round(res["delta_tp_por_1000_alertas"], 2),
                        "ic95_delta_tp_por_1000_alertas": f"[{res['delta_tp_1k_ci_low']:+.2f}, {res['delta_tp_1k_ci_high']:+.2f}]",
                        "delta_tp_total_test": round(res["delta_tp_total_test"], 1),
                        "f1_tie_aware_knn_w": round(res["f1_exacto_A"], 4),
                        "f1_tie_aware_ref": round(res["f1_exacto_B"], 4),
                        "delta_f1_tie_aware": round(res["delta_f1_exacto"], 4),
                        "ic95_delta_f1_tie_aware": f"[{res['delta_f1_ci_low']:+.4f}, {res['delta_f1_ci_high']:+.4f}]",
                        "ganancia_relativa_pr_auc_pct": round(res["ganancia_relativa_pr_auc_pct"], 2),
                        "ic95_ganancia_relativa_pr_auc_pct": f"[{res['ganancia_rel_pr_ci_low']:+.2f} %, {res['ganancia_rel_pr_ci_high']:+.2f} %]",
                    }
                )
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # 14A.6 · F8: K1 multiple comparisons (1,000 bootstrap + Bonferroni 99.5%)
    # ------------------------------------------------------------------
    def run_f8_k1_bonferroni_1000(
        self,
        bundle_a: KNNVersionBundle,
        cached_knn_w_proba: np.ndarray,
        nb_h_proba: np.ndarray,
        n_resamples: int = 1000,
    ) -> pd.DataFrame:
        """Recompute K1 paired differences with 1,000 person-bootstrap resamples and Bonferroni 99.5% CIs."""
        assert bundle_a.orig_train is not None and bundle_a.orig_test is not None
        orig_tr = bundle_a.orig_train
        orig_te = bundle_a.orig_test
        y_te = bundle_a.test_blocks.y
        g_te = bundle_a.test_blocks.groups

        digits = sorted(ISCO_MAJOR_LABELS_ES.keys())
        m_comp = len(digits)
        rows: List[Dict[str, object]] = []

        for digit in digits:
            m_te = (orig_te["isco_major"] == digit).to_numpy()
            m_tr = (orig_tr["isco_major"] == digit).to_numpy()
            y_g = y_te[m_te]
            pk = cached_knn_w_proba[m_te]
            pn = nb_h_proba[m_te]
            gg = g_te[m_te]

            res = paired_bootstrap_person_multi_alpha(
                y_true=y_g,
                prob_a=pk,
                prob_b=pn,
                groups=gg,
                n_resamples=n_resamples,
                bonferroni_m=m_comp,
                random_state=self.config.random_state,
            )
            pr_k = float(average_precision_score(y_g, pk))
            pr_n = float(average_precision_score(y_g, pn))
            roc_k = float(roc_auc_score(y_g, pk))
            roc_n = float(roc_auc_score(y_g, pn))

            rows.append(
                {
                    "isco_major": digit,
                    "gran_grupo_isco": ISCO_MAJOR_LABELS_ES[digit],
                    "soporte_train": int(m_tr.sum()),
                    "soporte_test": int(m_te.sum()),
                    "tasa_obs_test_pct": round(100.0 * float(y_g.mean()), 2),
                    "knn_w_pr_auc": round(pr_k, 4),
                    "nb_h_pr_auc": round(pr_n, 4),
                    "delta_pr_auc": round(float(res["delta_pr_auc"]), 4),
                    "ic95_sin_ajuste_pr_auc": f"[{float(res['pr_95_low']):+.4f}, {float(res['pr_95_high']):+.4f}]",
                    "distinguible_ic95": bool(res["pr_95_excluye_cero"]),
                    "ic995_bonferroni_pr_auc": f"[{float(res['pr_bonf_low']):+.4f}, {float(res['pr_bonf_high']):+.4f}]",
                    "distinguible_bonferroni_995": bool(res["pr_bonf_excluye_cero"]),
                    "delta_roc_auc": round(roc_k - roc_n, 4),
                    "ic995_bonferroni_roc_auc": f"[{float(res['roc_bonf_low']):+.4f}, {float(res['roc_bonf_high']):+.4f}]",
                    "roc_distinguible_bonferroni_995": bool(res["roc_bonf_excluye_cero"]),
                }
            )

        return pd.DataFrame(rows).sort_values("tasa_obs_test_pct", ascending=False).reset_index(drop=True)

    # ------------------------------------------------------------------
    # 14A.7 · F7: Grid edge check w_g=16 and w=16 (time-boxed to 30 min)
    # ------------------------------------------------------------------
    def run_f7_grid_edge_w16_check(
        self,
        bundle_a: KNNVersionBundle,
        max_minutes: float = 30.0,
    ) -> Tuple[pd.DataFrame, Dict[str, object]]:
        """Evaluate w_g=16 (KNN-G) and w=16 (KNN-W) on 10% 5-fold grouped CV vs cached w=8 with paired CIs."""
        tr_blocks = bundle_a.train_blocks
        subsampler = PersonSubsampler(self.config.random_state)
        nested = subsampler.sample_persons_nested(
            tr_blocks.groups, tr_blocks.y, (self.config.tuning_person_fraction,)
        )
        idx_10, _ = nested[self.config.tuning_person_fraction]
        y_10 = tr_blocks.y[idx_10]
        g_10 = tr_blocks.groups[idx_10]
        folds, overlap = KNNEvaluator._build_grouped_folds(
            y_10, g_10, n_splits=self.config.cv_folds, random_state=self.config.random_state
        )
        assert overlap == 0

        cv_cache_dir = self.config.cache_dir / "tuning_cv"
        t_start = time.perf_counter()

        # Load cached w=8 OOFs (exact same signature as Section 7)
        X_g8 = tr_blocks.build_knn_g_matrix(w_g=8.0, row_idx=idx_10)
        rows_g8, oof_g8_map = KNNEvaluator._evaluate_grid_for_single_space(
            X_sub=X_g8, y_sub=y_10, folds=folds, model_id=MODEL_KNN_G,
            algorithm="brute", metric="manhattan", block_weight=8.0,
            k_values=self.config.k_grid, weights_values=self.config.weights_grid,
            n_jobs=self.config.n_jobs, stage_label="Extensión de borde (peso superior)",
            cache_dir=cv_cache_dir, force_recompute=False, verbose=False,
        )
        oof_g8 = oof_g8_map[(101, "uniform")]
        del X_g8
        gc.collect()

        X_w8 = tr_blocks.build_knn_w_matrix(w=8.0, row_idx=idx_10)
        rows_w8, oof_w8_map = KNNEvaluator._evaluate_grid_for_single_space(
            X_sub=X_w8, y_sub=y_10, folds=folds, model_id=MODEL_KNN_W,
            algorithm="brute", metric="euclidean", block_weight=8.0,
            k_values=self.config.k_grid, weights_values=self.config.weights_grid,
            n_jobs=self.config.n_jobs, stage_label="Extensión de borde (peso superior)",
            cache_dir=cv_cache_dir, force_recompute=False, verbose=False,
        )
        oof_w8 = oof_w8_map[(101, "uniform")]
        del X_w8
        gc.collect()

        # Evaluate ONLY best (k=101, uniform, metric) at w=16 with disk cache and strict time-box
        results_rows: List[Dict[str, object]] = []
        status_info: Dict[str, object] = {"max_minutes_limit": max_minutes, "skipped_any": False}

        for model_id, metric, oof_ref_8, build_fn in [
            (MODEL_KNN_G, "manhattan", oof_g8, lambda: tr_blocks.build_knn_g_matrix(w_g=16.0, row_idx=idx_10)),
            (MODEL_KNN_W, "euclidean", oof_w8, lambda: tr_blocks.build_knn_w_matrix(w=16.0, row_idx=idx_10)),
        ]:
            elapsed_min = (time.perf_counter() - t_start) / 60.0
            if elapsed_min >= max_minutes:
                status_info["skipped_any"] = True
                status_info[f"{model_id}_w16_status"] = "Omitido por límite de tiempo de 30 min"
                continue

            X_16 = build_fn()
            t_m0 = time.perf_counter()
            rows_16, oof_16_map = KNNEvaluator._evaluate_grid_for_single_space(
                X_sub=X_16, y_sub=y_10, folds=folds, model_id=model_id,
                algorithm="brute", metric=metric, block_weight=16.0,
                k_values=(101,), weights_values=("uniform",),
                n_jobs=self.config.n_jobs, stage_label="Verificación de borde revisión (w=16)",
                cache_dir=cv_cache_dir, force_recompute=False, verbose=True,
            )
            dt_m = time.perf_counter() - t_m0
            oof_16 = oof_16_map[(101, "uniform")]
            del X_16
            gc.collect()

            r8 = next(r for r in (rows_g8 if model_id == MODEL_KNN_G else rows_w8) if r["k_vecinos"] == 101 and r["pesos"] == "uniform")
            r16 = rows_16[0]

            paired = paired_bootstrap_person_diffs(
                y_true=y_10,
                prob_a=oof_16,
                prob_b=oof_ref_8,
                groups=g_10,
                n_resamples=self.config.bootstrap_resamples,
                random_state=self.config.random_state,
            )
            results_rows.append(
                {
                    "modelo_id": model_id,
                    "metrica": metric,
                    "k_vecinos": 101,
                    "pesos": "uniform",
                    "pr_auc_cv_w8": float(r8["pr_auc_cv_media"]),
                    "pr_auc_std_w8": float(r8["pr_auc_cv_std"]),
                    "pr_auc_cv_w16": float(r16["pr_auc_cv_media"]),
                    "pr_auc_std_w16": float(r16["pr_auc_cv_std"]),
                    "delta_pr_auc_w16_menos_w8_oof": round(float(paired["delta_pr_auc"]), 5),
                    "ic95_pareado_delta_pr": f"[{float(paired['delta_pr_auc_ci_low']):+.5f}, {float(paired['delta_pr_auc_ci_high']):+.5f}]",
                    "pr_excluye_cero": bool(paired["pr_auc_excluye_cero"]),
                    "veredicto_pr_auc": str(paired["veredicto_pr_auc"]),
                    "roc_auc_cv_w8": float(r8["roc_auc_cv_media"]),
                    "roc_auc_cv_w16": float(r16["roc_auc_cv_media"]),
                    "delta_roc_auc_w16_menos_w8_oof": round(float(paired["delta_roc_auc"]), 5),
                    "ic95_pareado_delta_roc": f"[{float(paired['delta_roc_auc_ci_low']):+.5f}, {float(paired['delta_roc_auc_ci_high']):+.5f}]",
                    "tiempo_5folds_s": round(dt_m, 2),
                }
            )
            status_info[f"{model_id}_w16_status"] = "Completado dentro del límite"
            status_info[f"{model_id}_w16_time_s"] = round(dt_m, 2)

        status_info["total_elapsed_min"] = round((time.perf_counter() - t_start) / 60.0, 2)
        return pd.DataFrame(results_rows), status_info

    # ------------------------------------------------------------------
    # Export all Section 14A tables + decision_log_knn_revision.csv
    # ------------------------------------------------------------------
    def export_revision_tables(
        self,
        cache_bundle: CacheIntegrityBundle,
        f1_bundle: F1PurityPrefilterBundle,
        f2_df: pd.DataFrame,
        f3_bundle: F3SizeControlBundle,
        f5_bundle: F5CostRangeBundle,
        f6_df: pd.DataFrame,
        f8_df: pd.DataFrame,
        f7_df: pd.DataFrame,
        decision_log_rev_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Persist all Section 14A verification CSVs and decision_log_knn_revision.csv in UTF-8."""
        tables: Dict[str, pd.DataFrame] = {
            "14a0_integridad_caches_test_completo.csv": cache_bundle.integrity_table,
            "14a1a_auditoria_ohe_drop_first.csv": f1_bundle.ohe_geometry_audit_table,
            "14a1b_pureza_knn_w_w8_por_soporte.csv": f1_bundle.purity_by_support_tier_table,
            "14a1c_pureza_knn_w_w8_por_isco.csv": f1_bundle.purity_by_isco_table,
            "14a1d_auditoria_soporte_perfiles_k2.csv": f1_bundle.k2_support_audit_table,
            "14a1e_experimento_prefiltro_exacto_5000.csv": f1_bundle.prefilter_comparison_table,
            "14a2_brecha_l1_menos_l2_cv.csv": f2_df,
            "14a3a_control_tamano_aleatorio_5_semillas.csv": f3_bundle.per_seed_table,
            "14a3b_descomposicion_perdida_r4_tamano_vs_extremos.csv": f3_bundle.decomposition_summary_table,
            "14a4a_tiempos_por_bloque_knn_w.csv": f5_bundle.block_times_table,
            "14a4b_rango_costo_y_factores_lentitud.csv": f5_bundle.cost_range_table,
            "14a5_significancia_practica_y_alerta_exacta.csv": f6_df,
            "14a6_k1_bonferroni_1000_bootstrap.csv": f8_df,
            "14a7_prueba_borde_w16_cv.csv": f7_df,
            "decision_log_knn_revision.csv": decision_log_rev_df,
        }
        inv_rows: List[Dict[str, object]] = []
        for fname, df in tables.items():
            out_p = self.config.tables_dir / fname
            df.to_csv(out_p, index=False, encoding="utf-8")
            inv_rows.append(
                {
                    "archivo_tabla": fname,
                    "filas": int(len(df)),
                    "columnas": int(df.shape[1]),
                    "tamano_kb": round(float(out_p.stat().st_size) / 1024.0, 2),
                }
            )
        return pd.DataFrame(inv_rows)

    @staticmethod
    def build_revision_decision_log(
        f1_bundle: F1PurityPrefilterBundle,
        f2_df: pd.DataFrame,
        f3_bundle: F3SizeControlBundle,
        f5_bundle: F5CostRangeBundle,
        f6_df: pd.DataFrame,
        f8_df: pd.DataFrame,
        f7_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Build decision_log_knn_revision.csv summarizing verified evidence for F1–F10."""
        s1 = f1_bundle.summary_dict
        s3 = f3_bundle.summary_dict
        s5 = f5_bundle.summary_dict
        n_bonf = int(f8_df["distinguible_bonferroni_995"].sum())
        n_95 = int(f8_df["distinguible_ic95"].sum())
        f6_log = f6_df.loc[
            f6_df["punto_comparacion"].str.contains("NB-H")
            & f6_df["comparacion"].str.contains("Logística")
        ].iloc[0]
        f6_nbh = f6_df.loc[
            f6_df["punto_comparacion"].str.contains("NB-H")
            & f6_df["comparacion"].str.contains("NB-H")
        ].iloc[0]
        r_l1_sc = float(f2_df.loc[f2_df["regimen_id"] == "R2_A_escalado", "brecha_L1_menos_L2_pr_auc"].iloc[0])
        r_l1_tw = float(f2_df.loc[f2_df["regimen_id"] == "R3_A_wins_tukey", "brecha_L1_menos_L2_pr_auc"].iloc[0])

        w16_txt = "No ejecutado"
        if not f7_df.empty:
            parts = []
            for _, r in f7_df.iterrows():
                parts.append(
                    f"{r['modelo_id']}: w=8 ({r['pr_auc_cv_w8']:.5f}) vs w=16 ({r['pr_auc_cv_w16']:.5f}), "
                    f"delta={r['delta_pr_auc_w16_menos_w8_oof']:+.5f} {r['ic95_pareado_delta_pr']}"
                )
            w16_txt = "; ".join(parts)

        rows = [
            {
                "id_revision": "REV-F1",
                "hallazgo": "Pureza real con w=8 por tramo de soporte, sesgo K2 y prefiltro exacto",
                "decision_adoptada": "Se reemplazan afirmaciones no medidas por pureza medida en 5,000 consultas y benchmark real del prefiltro exacto consciente de drop='first'.",
                "evidencia_cuantitativa": (
                    f"Pureza global w=8: ESCO={s1['purity_esco_global_w8_pct']}%, ISCO={s1['purity_isco_global_w8_pct']}%; "
                    f"filas test con soporte <101={s1['pct_test_full_occ_lt_101']}%. "
                    f"Prefiltro certificado={s1['pct_q5000_certified_sqrt2w']}%, tiempo={s1['prefilter_s_per_1k']} s/1k vs exacto={s1['exact_s_per_1k']} s/1k ({s1['speedup_factor']}x)."
                ),
            },
            {
                "id_revision": "REV-F2",
                "hallazgo": "Brecha L1 (Manhattan) vs L2 (Euclídea) en todos los regímenes",
                "decision_adoptada": "Se retira toda afirmación de que los extremos explican L1 > L2; se declara causa no identificada.",
                "evidencia_cuantitativa": (
                    f"Brecha PR-AUC L1-L2: escalado={r_l1_sc:+.5f}, winsorizado Tukey={r_l1_tw:+.5f} (no se reduce tras winsorizar)."
                ),
            },
            {
                "id_revision": "REV-F3",
                "hallazgo": "Control de tamaño R4c_random_rows (5 semillas) en KNN-D test completo",
                "decision_adoptada": "Se descompone la pérdida total de R4 en efecto tamaño muestral frente a efecto pérdida de extremos reales.",
                "evidencia_cuantitativa": (
                    f"Pérdida total R4-R2={s3['total_loss_pr']:+.5f}: efecto tamaño R4c-R2={s3['size_loss_pr']:+.5f} ({s3['pct_due_to_size']}%), "
                    f"efecto extremos R4-R4c={s3['extremes_loss_pr']:+.5f} ({s3['pct_due_to_extremes']}%)."
                ),
            },
            {
                "id_revision": "REV-F4",
                "hallazgo": "Redacción sobredimensionada ('techo', 'prueba', 'demuestra')",
                "decision_adoptada": "Se sustituye por afirmaciones estrictamente medidas: mejor modelo probado; modelos rápidos con oficio quedan como hipótesis no probada.",
                "evidencia_cuantitativa": "HistGradientBoosting (6.0) usó 14 columnas densas sin ocupación; no se entrenan nuevos modelos.",
            },
            {
                "id_revision": "REV-F5",
                "hallazgo": "Incertidumbre 3x en costo computacional de KNN-W por estrangulación térmica",
                "decision_adoptada": "Se reporta el costo como rango (benchmark sin estrangulación vs. tiempo acumulado real) y se grafica knn14.",
                "evidencia_cuantitativa": (
                    f"Rango KNN-W: {s5['bench_total_h']} h a {s5['real_total_h']} h (factor {s5['uncertainty_ratio_real_over_bench']}x); "
                    f"vs NB-H: {s5['slowdown_nb_h_low']:,}x–{s5['slowdown_nb_h_high']:,}x; vs Logística: {s5['slowdown_logit_low']:,}x–{s5['slowdown_logit_high']:,}x."
                ),
            },
            {
                "id_revision": "REV-F6",
                "hallazgo": "Significancia práctica en conteos y emparejamiento exacto tie-aware de alerta",
                "decision_adoptada": "Se reportan reincidencias adicionales por 1,000 alertas con IC 95% pareado y tasas de alerta reales junto a F1.",
                "evidencia_cuantitativa": (
                    f"A tasa exacta 51.78%: vs Logística {f6_log['delta_tp_por_1000_alertas']:+.2f} {f6_log['ic95_delta_tp_por_1000_alertas']} TP/1k alertas "
                    f"(+{f6_log['ganancia_relativa_pr_auc_pct']}% PR-AUC rel.); vs NB-H {f6_nbh['delta_tp_por_1000_alertas']:+.2f} {f6_nbh['ic95_delta_tp_por_1000_alertas']} TP/1k alertas."
                ),
            },
            {
                "id_revision": "REV-F7",
                "hallazgo": "Borde de rejilla w=8 y verificación acotada w=16 en 5-fold CV (10%)",
                "decision_adoptada": "Se documenta la meseta de w y se mantiene w=8 si w=16 no aporta ganancia práctica clara.",
                "evidencia_cuantitativa": w16_txt,
            },
            {
                "id_revision": "REV-F8",
                "hallazgo": "Comparaciones múltiples en K1 (10 grupos ISCO)",
                "decision_adoptada": "Se recalcula K1 con 1,000 remuestreos bootstrap reportando IC 95% e IC Bonferroni 99.5%.",
                "evidencia_cuantitativa": f"Grupos distinguibles en PR-AUC: {n_95}/10 con IC 95% y {n_bonf}/10 tras ajuste Bonferroni 99.5%.",
            },
            {
                "id_revision": "REV-F9-F10",
                "hallazgo": "Semántica retrospectiva de reincide y reemplazo integral de Sección 17",
                "decision_adoptada": "Se documenta la construcción retrospectiva de veces_ese_oficio en Secciones 1 y 17, y se integra la guía revisada sin tecnicismos.",
                "evidencia_cuantitativa": "integrar_empleos.py / limpiar_unificado.py: groupby(['resume_id','occupation_code']).transform('size') sobre todo el historial; 0 marcadores << pendientes.",
            },
        ]
        return pd.DataFrame(rows)
