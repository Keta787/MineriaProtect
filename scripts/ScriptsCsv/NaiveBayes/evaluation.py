"""Person-grouped CV, hyperparameter tuning, OOF threshold, bootstrap CIs, and calibration."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.special import logsumexp
from sklearn.calibration import calibration_curve
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.naive_bayes import BernoulliNB, GaussianNB

from scripts.ScriptsCsv.Modelado.dataset_builder import VersionModelingData

from .config import (
    MODEL_LABELS_ES,
    MODEL_NB_B,
    MODEL_NB_G,
    MODEL_NB_G_STAR,
    MODEL_NB_H,
    MODEL_ORDER,
    NaiveBayesConfig,
    PRIOR_MODE_LABELS_ES,
)
from .feature_blocks import NaiveBayesPartitionBlocks
from .models import HybridNaiveBayes, build_bernoulli_nb, build_gaussian_nb, resolve_priors


@dataclass(frozen=True)
class ModelCurveBundle:
    """PR, ROC, and calibration curves on Test for one Naive Bayes variant."""

    model_id: str
    model_label_es: str
    pr_auc: float
    roc_auc: float
    brier: float
    ece: float
    precision_curve: np.ndarray
    recall_curve: np.ndarray
    fpr_curve: np.ndarray
    tpr_curve: np.ndarray
    calib_prob_pred: np.ndarray
    calib_prob_true: np.ndarray
    calib_bin_counts: np.ndarray
    hist_bins: np.ndarray
    hist_density_c0: np.ndarray
    hist_density_c1: np.ndarray


@dataclass(frozen=True)
class TunedModelArtifact:
    """Best hyperparameters, OOF probabilities, OOF threshold, and fitted estimator on full Train."""

    model_id: str
    model_label_es: str
    best_params: Dict[str, object]
    best_cv_pr_auc: float
    best_cv_roc_auc: float
    oof_proba_train: np.ndarray
    oof_threshold_tau: float
    threshold_comparison_df: pd.DataFrame
    threshold_curve_df: pd.DataFrame
    fitted_estimator: object
    fit_time_s: float
    predict_time_test_s: float
    input_memory_mb: float
    test_proba: np.ndarray


@dataclass(frozen=True)
class NaiveBayesEvaluationBundle:
    """All evaluation tables, tuned models, test metrics, curves, and comparisons on Version A."""

    references_table: pd.DataFrame
    trees_reference_table: pd.DataFrame
    baseline_cv_table: pd.DataFrame
    tuning_all_attempts_table: pd.DataFrame
    tuning_winners_table: pd.DataFrame
    oof_threshold_summary_table: pd.DataFrame
    oof_threshold_curves: Dict[str, pd.DataFrame]
    test_metrics_table: pd.DataFrame
    confusion_matrices_table: pd.DataFrame
    calibration_summary_table: pd.DataFrame
    final_comparison_table_a: pd.DataFrame
    phase4_reproduction_table: pd.DataFrame
    like_for_like_dense_table: pd.DataFrame
    like_for_like_occ_table: pd.DataFrame
    paired_bootstrap_comparisons_table: pd.DataFrame
    equal_alert_rate_table: pd.DataFrame
    grid_sizes: Dict[str, object]
    tuned_models: Dict[str, TunedModelArtifact]
    model_curves: Dict[str, ModelCurveBundle]
    cv_person_overlap_count: int
    bootstrap_elapsed_s: float


def compute_classification_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.5,
) -> Dict[str, float]:
    """Compute standard imbalance-aware classification metrics at a given decision threshold."""
    y_pred = (y_prob >= threshold).astype(np.int8)
    return {
        "pr_auc": float(average_precision_score(y_true, y_prob)),
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
        "f1_pos": float(f1_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "recall_pos": float(recall_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "precision_pos": float(precision_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "balanced_acc": float(balanced_accuracy_score(y_true, y_pred)),
        "brier": float(brier_score_loss(y_true, y_prob)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
    }


def compute_matrix_memory_mb(X: sparse.spmatrix | np.ndarray) -> float:
    """Return memory footprint in megabytes (MB) of a dense or CSR matrix."""
    if sparse.issparse(X):
        csr = X.tocsr()
        total_bytes = csr.data.nbytes + csr.indices.nbytes + csr.indptr.nbytes
    else:
        total_bytes = np.asarray(X).nbytes
    return float(total_bytes) / (1024.0 * 1024.0)


def bootstrap_person_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    groups: np.ndarray,
    threshold: float = 0.5,
    n_resamples: int = 300,
    random_state: int = 42,
) -> Dict[str, Tuple[float, float]]:
    """Compute 95% confidence intervals by resampling persons (resume_id) with replacement.

    Pre-sorts predictions once and uses exact person-multiplicity weights so 300 resamples
    over 347,720 rows complete in < 1 second while matching sample-weighted sklearn metrics.
    """
    y_arr = np.asarray(y_true, dtype=np.int8).ravel()
    p_arr = np.asarray(y_prob, dtype=np.float64).ravel()
    y_pred = (p_arr >= threshold).astype(np.int8)

    _, person_inv = np.unique(np.asarray(groups, dtype=str), return_inverse=True)
    n_persons = int(person_inv.max()) + 1

    # Pre-aggregate confusion counts and squared error per person for threshold metrics & Brier
    p_tp = np.bincount(person_inv, weights=((y_arr == 1) & (y_pred == 1)).astype(np.float64), minlength=n_persons)
    p_fp = np.bincount(person_inv, weights=((y_arr == 0) & (y_pred == 1)).astype(np.float64), minlength=n_persons)
    p_fn = np.bincount(person_inv, weights=((y_arr == 1) & (y_pred == 0)).astype(np.float64), minlength=n_persons)
    p_tn = np.bincount(person_inv, weights=((y_arr == 0) & (y_pred == 0)).astype(np.float64), minlength=n_persons)
    p_sq_err = np.bincount(person_inv, weights=(y_arr.astype(np.float64) - p_arr) ** 2, minlength=n_persons)

    # Pre-sort by descending probability once for exact weighted ROC-AUC and PR-AUC
    desc_order = np.argsort(-p_arr, kind="mergesort")
    p_sorted = p_arr[desc_order]
    y_sorted = y_arr[desc_order].astype(np.float64)
    person_sorted = person_inv[desc_order]

    # Identify unique probability tie boundaries in descending order
    tie_starts = np.flatnonzero(np.r_[True, p_sorted[1:] != p_sorted[:-1]])

    rng = np.random.default_rng(random_state)
    samples: Dict[str, np.ndarray] = {
        k: np.zeros(n_resamples, dtype=np.float64)
        for k in ("pr_auc", "roc_auc", "f1_pos", "recall_pos", "precision_pos", "balanced_acc", "brier", "accuracy")
    }

    for b in range(n_resamples):
        drawn_persons = rng.integers(0, n_persons, size=n_persons)
        p_weights = np.bincount(drawn_persons, minlength=n_persons).astype(np.float64)

        tp = float(p_weights @ p_tp)
        fp = float(p_weights @ p_fp)
        fn = float(p_weights @ p_fn)
        tn = float(p_weights @ p_tn)
        tot = tp + fp + fn + tn
        sq_sum = float(p_weights @ p_sq_err)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        tnr = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        f1 = (2.0 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

        samples["precision_pos"][b] = prec
        samples["recall_pos"][b] = rec
        samples["f1_pos"][b] = f1
        samples["balanced_acc"][b] = 0.5 * (rec + tnr)
        samples["accuracy"][b] = (tp + tn) / tot if tot > 0 else 0.0
        samples["brier"][b] = sq_sum / tot if tot > 0 else 0.0

        row_w = p_weights[person_sorted]
        w_y1 = row_w * y_sorted
        w_y0 = row_w - w_y1

        agg_y1 = np.add.reduceat(w_y1, tie_starts)
        agg_y0 = np.add.reduceat(w_y0, tie_starts)
        tot_y1 = float(agg_y1.sum())
        tot_y0 = float(agg_y0.sum())

        if tot_y1 > 0.0 and tot_y0 > 0.0:
            cum_y1 = np.cumsum(agg_y1)
            cum_y0 = np.cumsum(agg_y0)
            # ROC-AUC trapezoidal rule from top score to bottom score
            prev_y0 = cum_y0 - agg_y0
            u_stat = float(np.sum(agg_y1 * (tot_y0 - prev_y0 - 0.5 * agg_y0)))
            samples["roc_auc"][b] = u_stat / (tot_y1 * tot_y0)

            # Average Precision: sum_k (Delta Recall_k) * Precision_k
            denom = cum_y1 + cum_y0
            prec_at_k = np.divide(cum_y1, denom, out=np.zeros_like(cum_y1), where=denom > 0)
            samples["pr_auc"][b] = float(np.sum((agg_y1 / tot_y1) * prec_at_k))
        else:
            samples["roc_auc"][b] = 0.5
            samples["pr_auc"][b] = 0.0

    ci_out: Dict[str, Tuple[float, float]] = {}
    for metric_name, arr in samples.items():
        low, high = np.percentile(arr, [2.5, 97.5])
        ci_out[metric_name] = (float(low), float(high))
    return ci_out


def select_oof_threshold_from_proba(
    y_train: np.ndarray,
    oof_proba: np.ndarray,
) -> Tuple[float, pd.DataFrame]:
    """Sweep thresholds on train OOF predictions to maximize class-1 F1 without touching test."""
    y_arr = np.asarray(y_train, dtype=np.int8).ravel()
    p_arr = np.asarray(oof_proba, dtype=np.float64).ravel()

    order = np.argsort(-p_arr, kind="mergesort")
    p_sorted = p_arr[order]
    y_sorted = y_arr[order]
    cum_tp = np.cumsum(y_sorted == 1, dtype=np.int64)
    cum_fp = np.cumsum(y_sorted == 0, dtype=np.int64)
    total_pos = int(cum_tp[-1])
    total_neg = int(cum_fp[-1])
    n_total = len(y_arr)

    thresholds = np.round(np.linspace(0.02, 0.98, 193), 4)
    neg_p_sorted = -p_sorted
    counts_pred_pos = np.searchsorted(neg_p_sorted, -thresholds, side="right")

    curve_rows: List[Dict[str, float]] = []
    best_tau = 0.50
    best_f1 = -1.0

    for tau, k_pred in zip(thresholds, counts_pred_pos):
        if k_pred == 0:
            tp, fp = 0, 0
        else:
            tp = int(cum_tp[k_pred - 1])
            fp = int(cum_fp[k_pred - 1])
        tn = total_neg - fp

        prec = tp / float(tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / float(total_pos) if total_pos > 0 else 0.0
        tnr = tn / float(total_neg) if total_neg > 0 else 0.0
        f1 = (2.0 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        bal_acc = 0.5 * (rec + tnr)
        acc = (tp + tn) / float(n_total)

        if f1 > best_f1:
            best_f1 = f1
            best_tau = float(tau)

        curve_rows.append(
            {
                "umbral_tau": float(tau),
                "f1_clase_1": f1,
                "precision_clase_1": prec,
                "recall_clase_1": rec,
                "balanced_acc": bal_acc,
                "accuracy": acc,
            }
        )

    return best_tau, pd.DataFrame(curve_rows)


def compute_equal_alert_rate_cutoff(
    probs: np.ndarray,
    target_alert_rate: float,
) -> Tuple[float, float]:
    """Compute deterministic quantile threshold matching a target positive alert rate without test tuning."""
    p_arr = np.asarray(probs, dtype=np.float64).ravel()
    n = len(p_arr)
    if n == 0:
        return 0.5, 0.0
    k_target = int(round(float(target_alert_rate) * float(n)))
    if k_target <= 0:
        return float(np.max(p_arr)) + 1e-12, 0.0
    if k_target >= n:
        return float(np.min(p_arr)), 1.0
    cutoff = float(np.partition(p_arr, n - k_target)[n - k_target])
    actual_rate = float(np.mean(p_arr >= cutoff))
    return cutoff, actual_rate


def _weighted_pr_roc_from_presorted(
    p_weights: np.ndarray,
    person_sorted: np.ndarray,
    y_sorted: np.ndarray,
    tie_starts: np.ndarray,
) -> Tuple[float, float]:
    """Compute exact person-weighted PR-AUC and ROC-AUC from a pre-sorted prediction array."""
    row_w = p_weights[person_sorted]
    w_y1 = row_w * y_sorted
    w_y0 = row_w - w_y1

    agg_y1 = np.add.reduceat(w_y1, tie_starts)
    agg_y0 = np.add.reduceat(w_y0, tie_starts)
    tot_y1 = float(agg_y1.sum())
    tot_y0 = float(agg_y0.sum())

    if tot_y1 > 0.0 and tot_y0 > 0.0:
        cum_y1 = np.cumsum(agg_y1)
        cum_y0 = np.cumsum(agg_y0)
        prev_y0 = cum_y0 - agg_y0
        u_stat = float(np.sum(agg_y1 * (tot_y0 - prev_y0 - 0.5 * agg_y0)))
        roc_val = u_stat / (tot_y1 * tot_y0)

        denom = cum_y1 + cum_y0
        prec_at_k = np.divide(cum_y1, denom, out=np.zeros_like(cum_y1), where=denom > 0)
        pr_val = float(np.sum((agg_y1 / tot_y1) * prec_at_k))
        return pr_val, roc_val
    return 0.0, 0.5


def paired_bootstrap_person_diffs(
    y_true: np.ndarray,
    prob_a: np.ndarray,
    prob_b: np.ndarray,
    groups: np.ndarray,
    threshold_a: float | None = None,
    threshold_b: float | None = None,
    n_resamples: int = 300,
    random_state: int = 42,
) -> Dict[str, object]:
    """Compute paired person-level bootstrap 95% CIs for (model A minus model B).

    Uses identical person draws across models A and B within every resample.
    """
    y_arr = np.asarray(y_true, dtype=np.int8).ravel()
    pa = np.asarray(prob_a, dtype=np.float64).ravel()
    pb = np.asarray(prob_b, dtype=np.float64).ravel()
    if not (len(y_arr) == len(pa) == len(pb)):
        raise ValueError("y_true, prob_a, and prob_b must share the same length.")

    _, person_inv = np.unique(np.asarray(groups, dtype=str), return_inverse=True)
    n_persons = int(person_inv.max()) + 1

    # Pre-sort both models once
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

    eval_f1 = threshold_a is not None and threshold_b is not None
    if eval_f1:
        pred_a = (pa >= float(threshold_a)).astype(np.int8)
        pred_b = (pb >= float(threshold_b)).astype(np.int8)
        a_tp = np.bincount(person_inv, weights=((y_arr == 1) & (pred_a == 1)).astype(np.float64), minlength=n_persons)
        a_fp = np.bincount(person_inv, weights=((y_arr == 0) & (pred_a == 1)).astype(np.float64), minlength=n_persons)
        a_fn = np.bincount(person_inv, weights=((y_arr == 1) & (pred_a == 0)).astype(np.float64), minlength=n_persons)
        b_tp = np.bincount(person_inv, weights=((y_arr == 1) & (pred_b == 1)).astype(np.float64), minlength=n_persons)
        b_fp = np.bincount(person_inv, weights=((y_arr == 0) & (pred_b == 1)).astype(np.float64), minlength=n_persons)
        b_fn = np.bincount(person_inv, weights=((y_arr == 1) & (pred_b == 0)).astype(np.float64), minlength=n_persons)

    rng = np.random.default_rng(random_state)
    d_pr = np.zeros(n_resamples, dtype=np.float64)
    d_roc = np.zeros(n_resamples, dtype=np.float64)
    d_f1 = np.zeros(n_resamples, dtype=np.float64) if eval_f1 else None

    for b in range(n_resamples):
        drawn = rng.integers(0, n_persons, size=n_persons)
        p_w = np.bincount(drawn, minlength=n_persons).astype(np.float64)

        pr_a, roc_a = _weighted_pr_roc_from_presorted(p_w, pers_a_s, ya_s, ties_a)
        pr_b, roc_b = _weighted_pr_roc_from_presorted(p_w, pers_b_s, yb_s, ties_b)
        d_pr[b] = pr_a - pr_b
        d_roc[b] = roc_a - roc_b

        if eval_f1 and d_f1 is not None:
            tp_a = float(p_w @ a_tp)
            fp_a = float(p_w @ a_fp)
            fn_a = float(p_w @ a_fn)
            f1_a = (2.0 * tp_a / (2.0 * tp_a + fp_a + fn_a)) if (2.0 * tp_a + fp_a + fn_a) > 0 else 0.0

            tp_b = float(p_w @ b_tp)
            fp_b = float(p_w @ b_fp)
            fn_b = float(p_w @ b_fn)
            f1_b = (2.0 * tp_b / (2.0 * tp_b + fp_b + fn_b)) if (2.0 * tp_b + fp_b + fn_b) > 0 else 0.0
            d_f1[b] = f1_a - f1_b

    obs_pr = float(average_precision_score(y_arr, pa) - average_precision_score(y_arr, pb))
    obs_roc = float(roc_auc_score(y_arr, pa) - roc_auc_score(y_arr, pb))
    pr_lo, pr_hi = (float(v) for v in np.percentile(d_pr, [2.5, 97.5]))
    roc_lo, roc_hi = (float(v) for v in np.percentile(d_roc, [2.5, 97.5]))

    def _verdict(lo: float, hi: float) -> str:
        if lo > 0.0:
            return "A supera a B (IC 95 % excluye 0)"
        if hi < 0.0:
            return "B supera a A (IC 95 % excluye 0)"
        return "No hay diferencia distinguible (IC 95 % incluye 0)"

    out: Dict[str, object] = {
        "delta_pr_auc": obs_pr,
        "delta_pr_auc_ci_low": pr_lo,
        "delta_pr_auc_ci_high": pr_hi,
        "pr_auc_excluye_cero": bool(pr_lo > 0.0 or pr_hi < 0.0),
        "veredicto_pr_auc": _verdict(pr_lo, pr_hi),
        "delta_roc_auc": obs_roc,
        "delta_roc_auc_ci_low": roc_lo,
        "delta_roc_auc_ci_high": roc_hi,
        "roc_auc_excluye_cero": bool(roc_lo > 0.0 or roc_hi < 0.0),
        "veredicto_roc_auc": _verdict(roc_lo, roc_hi),
    }

    if eval_f1 and d_f1 is not None:
        obs_f1 = float(
            f1_score(y_arr, (pa >= float(threshold_a)).astype(np.int8), pos_label=1, zero_division=0)
            - f1_score(y_arr, (pb >= float(threshold_b)).astype(np.int8), pos_label=1, zero_division=0)
        )
        f1_lo, f1_hi = (float(v) for v in np.percentile(d_f1, [2.5, 97.5]))
        out.update(
            {
                "delta_f1": obs_f1,
                "delta_f1_ci_low": f1_lo,
                "delta_f1_ci_high": f1_hi,
                "f1_excluye_cero": bool(f1_lo > 0.0 or f1_hi < 0.0),
                "veredicto_f1": _verdict(f1_lo, f1_hi),
            }
        )
    return out


class NaiveBayesEvaluator:
    """Run grouped-CV baseline, honest hyperparameter tuning, OOF thresholding, and test evaluation."""

    def __init__(self, config: NaiveBayesConfig) -> None:
        self.config = config

    def load_project_references(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load References 1, 2, 3 and Version A decision tree benchmarks from existing repo CSVs."""
        if not self.config.references_csv_path.exists():
            raise FileNotFoundError(f"Missing references CSV: {self.config.references_csv_path}")
        if not self.config.trees_comparison_csv_path.exists():
            raise FileNotFoundError(f"Missing trees CSV: {self.config.trees_comparison_csv_path}")

        refs_df = pd.read_csv(self.config.references_csv_path, encoding="utf-8")
        trees_df = pd.read_csv(self.config.trees_comparison_csv_path, encoding="utf-8")

        # Enrich Reference 3 with PR-AUC and Brier from 6.0 resultados_test_ab.csv if available
        if self.config.phase4_test_csv_path.exists():
            p4_df = pd.read_csv(self.config.phase4_test_csv_path, encoding="utf-8")
            log_a = p4_df.loc[
                p4_df["version"].astype(str).str.startswith("A")
                & p4_df["modelo"].astype(str).str.contains("Logística")
            ]
            if not log_a.empty:
                pr_auc_ref3 = float(log_a.iloc[0]["pr_auc_test"])
                brier_ref3 = float(log_a.iloc[0]["brier_test"])
                refs_df["test_pr_auc"] = [0.2997, 0.2997, pr_auc_ref3]
                refs_df["test_brier"] = [0.2997, 0.7003, brier_ref3]

        trees_a_df = trees_df.loc[
            trees_df["version_datos"].astype(str).str.contains("CON outliers")
        ].reset_index(drop=True)
        return refs_df, trees_a_df

    def _build_folds(
        self,
        X: sparse.spmatrix | np.ndarray,
        y: np.ndarray,
        groups: np.ndarray,
    ) -> Tuple[List[Tuple[np.ndarray, np.ndarray]], int]:
        """Create 5 StratifiedGroupKFold splits on train and verify zero person overlap."""
        sgkf = StratifiedGroupKFold(
            n_splits=self.config.cv_folds,
            shuffle=True,
            random_state=self.config.random_state,
        )
        folds: List[Tuple[np.ndarray, np.ndarray]] = []
        overlap_count = 0
        for tr_idx, va_idx in sgkf.split(X, y, groups):
            overlap_count += len(set(groups[tr_idx]).intersection(set(groups[va_idx])))
            folds.append((tr_idx, va_idx))
        if overlap_count != 0:
            raise AssertionError(f"Person overlap across CV folds detected: {overlap_count}")
        return folds, overlap_count

    @staticmethod
    def _nb_g_star_matrix(blocks: NaiveBayesPartitionBlocks) -> np.ndarray:
        """Return NB-G feature matrix excluding near-constant binary/ordinal columns (< 1% minority)."""
        drop_set = set(blocks.nb_g_star_dropped_features)
        keep_idx = [
            i for i, col in enumerate(blocks.nb_g_feature_names) if col not in drop_set
        ]
        return np.ascontiguousarray(blocks.X_nb_g[:, keep_idx], dtype=np.float32)

    def run_baseline_cv(
        self,
        train_blocks: NaiveBayesPartitionBlocks,
        folds: List[Tuple[np.ndarray, np.ndarray]],
    ) -> pd.DataFrame:
        """Evaluate NB-G, NB-G*, NB-B, and NB-H with default hyperparameters in 5-fold grouped CV."""
        y_tr = train_blocks.y
        X_nb_g_star = self._nb_g_star_matrix(train_blocks)
        dropped_desc = ", ".join(train_blocks.nb_g_star_dropped_features) or "ninguna"
        specs = [
            (
                MODEL_NB_G,
                MODEL_LABELS_ES[MODEL_NB_G],
                "var_smoothing=1e-9, priors=empírico",
                train_blocks.X_nb_g,
                lambda: build_gaussian_nb(var_smoothing=1e-9, priors=None),
            ),
            (
                MODEL_NB_G_STAR,
                f"{MODEL_NB_G_STAR} · GaussianNB ({X_nb_g_star.shape[1]} cols; sin {dropped_desc})",
                "var_smoothing=1e-9, priors=empírico",
                X_nb_g_star,
                lambda: build_gaussian_nb(var_smoothing=1e-9, priors=None),
            ),
            (
                MODEL_NB_B,
                MODEL_LABELS_ES[MODEL_NB_B],
                "alpha=1.0, binarize=0.0, priors=empírico",
                train_blocks.X_nb_b,
                lambda: build_bernoulli_nb(alpha=1.0, priors=None),
            ),
            (
                MODEL_NB_H,
                MODEL_LABELS_ES[MODEL_NB_H],
                "var_smoothing=1e-9, alpha=1.0, priors=empírico",
                train_blocks.X_nb_h,
                lambda: HybridNaiveBayes(
                    continuous_idx=train_blocks.continuous_idx,
                    binary_idx=train_blocks.binary_idx,
                    var_smoothing=1e-9,
                    alpha=1.0,
                    priors=None,
                ),
            ),
        ]

        rows: List[Dict[str, object]] = []
        for model_id, model_label, param_desc, X_mat, factory in specs:
            fold_metrics = []
            fit_times = []
            pred_times = []
            for tr_idx, va_idx in folds:
                est = factory()
                t0 = time.perf_counter()
                est.fit(X_mat[tr_idx], y_tr[tr_idx])
                fit_times.append(time.perf_counter() - t0)

                t1 = time.perf_counter()
                prob_va = est.predict_proba(X_mat[va_idx])[:, 1]
                pred_times.append(time.perf_counter() - t1)

                fold_metrics.append(compute_classification_metrics(y_tr[va_idx], prob_va, threshold=0.5))

            df_f = pd.DataFrame(fold_metrics)
            rows.append(
                {
                    "modelo_id": model_id,
                    "modelo": model_label,
                    "hiperparametros_base": param_desc,
                    "n_columnas": int(X_mat.shape[1]),
                    "memoria_matriz_train_mb": round(compute_matrix_memory_mb(X_mat), 2),
                    "pr_auc_cv_media": round(float(df_f["pr_auc"].mean()), 4),
                    "pr_auc_cv_std": round(float(df_f["pr_auc"].std()), 4),
                    "roc_auc_cv_media": round(float(df_f["roc_auc"].mean()), 4),
                    "roc_auc_cv_std": round(float(df_f["roc_auc"].std()), 4),
                    "f1_clase_1_cv_media": round(float(df_f["f1_pos"].mean()), 4),
                    "recall_clase_1_cv_media": round(float(df_f["recall_pos"].mean()), 4),
                    "precision_clase_1_cv_media": round(float(df_f["precision_pos"].mean()), 4),
                    "balanced_acc_cv_media": round(float(df_f["balanced_acc"].mean()), 4),
                    "brier_cv_media": round(float(df_f["brier"].mean()), 4),
                    "accuracy_cv_media": round(float(df_f["accuracy"].mean()), 4),
                    "tiempo_fit_fold_s": round(float(np.mean(fit_times)), 4),
                    "tiempo_predict_fold_s": round(float(np.mean(pred_times)), 4),
                }
            )

        return pd.DataFrame(rows)

    def run_honest_tuning_and_oof(
        self,
        train_blocks: NaiveBayesPartitionBlocks,
        test_blocks: NaiveBayesPartitionBlocks,
        folds: List[Tuple[np.ndarray, np.ndarray]],
    ) -> Tuple[
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        Dict[str, pd.DataFrame],
        Dict[str, TunedModelArtifact],
        Dict[str, object],
    ]:
        """Tune NB-G, NB-G* (Sec. 6 only), NB-B, and NB-H in 5-fold grouped CV on train by PR-AUC."""
        y_tr = train_blocks.y
        n_tr = len(y_tr)
        vs_grid_h = list(self.config.var_smoothing_grid)
        vs_grid_g = list(self.config.nb_g_var_smoothing_grid)
        alpha_grid = list(self.config.alpha_grid)
        prior_modes = list(self.config.prior_modes)

        # 1. Precompute fold log-posteriors on NB-G (14 cols), NB-G* (clean dense), NB-H Gaussian slice (10 cols), and NB-B
        X_g14 = train_blocks.X_nb_g
        X_g_star = self._nb_g_star_matrix(train_blocks)
        X_g10 = np.ascontiguousarray(
            train_blocks.dense_clean_df.iloc[:, list(train_blocks.continuous_idx)].to_numpy(dtype=np.float32)
        )
        X_b2971 = train_blocks.X_nb_b

        oof_lp_nbg: Dict[Tuple[float, str], np.ndarray] = {
            (vs, pm): np.zeros((n_tr, 2), dtype=np.float64)
            for vs in vs_grid_g
            for pm in prior_modes
        }
        oof_lp_nbg_star: Dict[Tuple[float, str], np.ndarray] = {
            (vs, pm): np.zeros((n_tr, 2), dtype=np.float64)
            for vs in vs_grid_g
            for pm in prior_modes
        }
        oof_lp_g10: Dict[Tuple[float, str], np.ndarray] = {
            (vs, pm): np.zeros((n_tr, 2), dtype=np.float64)
            for vs in vs_grid_h
            for pm in prior_modes
        }
        oof_lp_nbb: Dict[Tuple[float, str], np.ndarray] = {
            (a, pm): np.zeros((n_tr, 2), dtype=np.float64)
            for a in alpha_grid
            for pm in prior_modes
        }
        fold_log_priors: Dict[Tuple[int, str], np.ndarray] = {}

        for fold_idx, (tr_idx, va_idx) in enumerate(folds):
            y_fold_tr = y_tr[tr_idx]
            _, counts = np.unique(y_fold_tr, return_counts=True)
            emp_priors = counts.astype(np.float64) / float(len(y_fold_tr))
            bal_priors = np.array([0.5, 0.5], dtype=np.float64)
            fold_log_priors[(fold_idx, "empirical")] = np.log(emp_priors)
            fold_log_priors[(fold_idx, "balanced")] = np.log(bal_priors)

            for vs in vs_grid_g:
                for pm in prior_modes:
                    p_seq = resolve_priors(pm)
                    gnb14 = GaussianNB(var_smoothing=float(vs), priors=p_seq)
                    gnb14.fit(X_g14[tr_idx], y_fold_tr)
                    oof_lp_nbg[(vs, pm)][va_idx] = gnb14.predict_log_proba(X_g14[va_idx])

                    gnbs = GaussianNB(var_smoothing=float(vs), priors=p_seq)
                    gnbs.fit(X_g_star[tr_idx], y_fold_tr)
                    oof_lp_nbg_star[(vs, pm)][va_idx] = gnbs.predict_log_proba(X_g_star[va_idx])

            for vs in vs_grid_h:
                for pm in prior_modes:
                    p_seq = resolve_priors(pm)
                    gnb10 = GaussianNB(var_smoothing=float(vs), priors=p_seq)
                    gnb10.fit(X_g10[tr_idx], y_fold_tr)
                    oof_lp_g10[(vs, pm)][va_idx] = gnb10.predict_log_proba(X_g10[va_idx])

            for a in alpha_grid:
                for pm in prior_modes:
                    p_seq = resolve_priors(pm)
                    bnb = BernoulliNB(alpha=float(a), binarize=0.0, force_alpha=True, class_prior=p_seq)
                    bnb.fit(X_b2971[tr_idx], y_fold_tr)
                    oof_lp_nbb[(a, pm)][va_idx] = bnb.predict_log_proba(X_b2971[va_idx])

        all_attempts_rows: List[Dict[str, object]] = []
        oof_probs_by_candidate: Dict[Tuple[str, int], np.ndarray] = {}
        params_by_candidate: Dict[Tuple[str, int], Dict[str, object]] = {}

        def _evaluate_oof_across_folds(oof_prob: np.ndarray) -> Dict[str, float]:
            f_scores = [
                compute_classification_metrics(y_tr[va_idx], oof_prob[va_idx], threshold=0.5)
                for _, va_idx in folds
            ]
            df_s = pd.DataFrame(f_scores)
            return {
                "pr_auc_mean": float(df_s["pr_auc"].mean()),
                "pr_auc_std": float(df_s["pr_auc"].std()),
                "roc_auc_mean": float(df_s["roc_auc"].mean()),
                "roc_auc_std": float(df_s["roc_auc"].std()),
                "f1_mean": float(df_s["f1_pos"].mean()),
                "recall_mean": float(df_s["recall_pos"].mean()),
                "precision_mean": float(df_s["precision_pos"].mean()),
                "balanced_acc_mean": float(df_s["balanced_acc"].mean()),
                "brier_mean": float(df_s["brier"].mean()),
                "accuracy_mean": float(df_s["accuracy"].mean()),
            }

        # Evaluate NB-G grid (extended)
        cand_id = 0
        for vs in vs_grid_g:
            for pm in prior_modes:
                cand_id += 1
                prob_vec = np.exp(oof_lp_nbg[(vs, pm)][:, 1])
                stats_m = _evaluate_oof_across_folds(prob_vec)
                oof_probs_by_candidate[(MODEL_NB_G, cand_id)] = prob_vec
                params_by_candidate[(MODEL_NB_G, cand_id)] = {
                    "var_smoothing": float(vs),
                    "alpha": np.nan,
                    "prior_mode": pm,
                }
                all_attempts_rows.append(
                    {
                        "modelo_id": MODEL_NB_G,
                        "intento_id": f"NBG-{cand_id:02d}",
                        "intento_num": cand_id,
                        "var_smoothing": float(vs),
                        "alpha": np.nan,
                        "prior_mode": pm,
                        "prior_etiqueta": PRIOR_MODE_LABELS_ES[pm],
                        "pr_auc_cv_media": round(stats_m["pr_auc_mean"], 5),
                        "pr_auc_cv_std": round(stats_m["pr_auc_std"], 5),
                        "roc_auc_cv_media": round(stats_m["roc_auc_mean"], 5),
                        "roc_auc_cv_std": round(stats_m["roc_auc_std"], 5),
                        "f1_cv_050": round(stats_m["f1_mean"], 4),
                        "recall_cv_050": round(stats_m["recall_mean"], 4),
                        "precision_cv_050": round(stats_m["precision_mean"], 4),
                        "balanced_acc_cv_050": round(stats_m["balanced_acc_mean"], 4),
                        "brier_cv": round(stats_m["brier_mean"], 4),
                        "accuracy_cv_050": round(stats_m["accuracy_mean"], 4),
                    }
                )

        # Evaluate NB-G* grid (Sections 5 & 6 only; excluding binary/ordinal columns with minority < 1%)
        cand_id = 0
        for vs in vs_grid_g:
            for pm in prior_modes:
                cand_id += 1
                prob_vec = np.exp(oof_lp_nbg_star[(vs, pm)][:, 1])
                stats_m = _evaluate_oof_across_folds(prob_vec)
                oof_probs_by_candidate[(MODEL_NB_G_STAR, cand_id)] = prob_vec
                params_by_candidate[(MODEL_NB_G_STAR, cand_id)] = {
                    "var_smoothing": float(vs),
                    "alpha": np.nan,
                    "prior_mode": pm,
                }
                all_attempts_rows.append(
                    {
                        "modelo_id": MODEL_NB_G_STAR,
                        "intento_id": f"NBGS-{cand_id:02d}",
                        "intento_num": cand_id,
                        "var_smoothing": float(vs),
                        "alpha": np.nan,
                        "prior_mode": pm,
                        "prior_etiqueta": PRIOR_MODE_LABELS_ES[pm],
                        "pr_auc_cv_media": round(stats_m["pr_auc_mean"], 5),
                        "pr_auc_cv_std": round(stats_m["pr_auc_std"], 5),
                        "roc_auc_cv_media": round(stats_m["roc_auc_mean"], 5),
                        "roc_auc_cv_std": round(stats_m["roc_auc_std"], 5),
                        "f1_cv_050": round(stats_m["f1_mean"], 4),
                        "recall_cv_050": round(stats_m["recall_mean"], 4),
                        "precision_cv_050": round(stats_m["precision_mean"], 4),
                        "balanced_acc_cv_050": round(stats_m["balanced_acc_mean"], 4),
                        "brier_cv": round(stats_m["brier_mean"], 4),
                        "accuracy_cv_050": round(stats_m["accuracy_mean"], 4),
                    }
                )

        # Evaluate NB-B grid
        cand_id = 0
        for a in alpha_grid:
            for pm in prior_modes:
                cand_id += 1
                prob_vec = np.exp(oof_lp_nbb[(a, pm)][:, 1])
                stats_m = _evaluate_oof_across_folds(prob_vec)
                oof_probs_by_candidate[(MODEL_NB_B, cand_id)] = prob_vec
                params_by_candidate[(MODEL_NB_B, cand_id)] = {
                    "var_smoothing": np.nan,
                    "alpha": float(a),
                    "prior_mode": pm,
                }
                all_attempts_rows.append(
                    {
                        "modelo_id": MODEL_NB_B,
                        "intento_id": f"NBB-{cand_id:02d}",
                        "intento_num": cand_id,
                        "var_smoothing": np.nan,
                        "alpha": float(a),
                        "prior_mode": pm,
                        "prior_etiqueta": PRIOR_MODE_LABELS_ES[pm],
                        "pr_auc_cv_media": round(stats_m["pr_auc_mean"], 5),
                        "pr_auc_cv_std": round(stats_m["pr_auc_std"], 5),
                        "roc_auc_cv_media": round(stats_m["roc_auc_mean"], 5),
                        "roc_auc_cv_std": round(stats_m["roc_auc_std"], 5),
                        "f1_cv_050": round(stats_m["f1_mean"], 4),
                        "recall_cv_050": round(stats_m["recall_mean"], 4),
                        "precision_cv_050": round(stats_m["precision_mean"], 4),
                        "balanced_acc_cv_050": round(stats_m["balanced_acc_mean"], 4),
                        "brier_cv": round(stats_m["brier_mean"], 4),
                        "accuracy_cv_050": round(stats_m["accuracy_mean"], 4),
                    }
                )

        # Evaluate NB-H grid (all combinations of var_smoothing x alpha x prior_mode)
        cand_id = 0
        for vs in vs_grid_h:
            for a in alpha_grid:
                for pm in prior_modes:
                    cand_id += 1
                    lp_g = oof_lp_g10[(vs, pm)]
                    lp_b = oof_lp_nbb[(a, pm)]
                    prob_vec = np.zeros(n_tr, dtype=np.float64)
                    for fold_idx, (_, va_idx) in enumerate(folds):
                        log_pi = fold_log_priors[(fold_idx, pm)]
                        unnorm = lp_g[va_idx] + lp_b[va_idx] - log_pi[np.newaxis, :]
                        normed = unnorm - logsumexp(unnorm, axis=1, keepdims=True)
                        prob_vec[va_idx] = np.exp(normed[:, 1])

                    stats_m = _evaluate_oof_across_folds(prob_vec)
                    oof_probs_by_candidate[(MODEL_NB_H, cand_id)] = prob_vec
                    params_by_candidate[(MODEL_NB_H, cand_id)] = {
                        "var_smoothing": float(vs),
                        "alpha": float(a),
                        "prior_mode": pm,
                    }
                    all_attempts_rows.append(
                        {
                            "modelo_id": MODEL_NB_H,
                            "intento_id": f"NBH-{cand_id:02d}",
                            "intento_num": cand_id,
                            "var_smoothing": float(vs),
                            "alpha": float(a),
                            "prior_mode": pm,
                            "prior_etiqueta": PRIOR_MODE_LABELS_ES[pm],
                            "pr_auc_cv_media": round(stats_m["pr_auc_mean"], 5),
                            "pr_auc_cv_std": round(stats_m["pr_auc_std"], 5),
                            "roc_auc_cv_media": round(stats_m["roc_auc_mean"], 5),
                            "roc_auc_cv_std": round(stats_m["roc_auc_std"], 5),
                            "f1_cv_050": round(stats_m["f1_mean"], 4),
                            "recall_cv_050": round(stats_m["recall_mean"], 4),
                            "precision_cv_050": round(stats_m["precision_mean"], 4),
                            "balanced_acc_cv_050": round(stats_m["balanced_acc_mean"], 4),
                            "brier_cv": round(stats_m["brier_mean"], 4),
                            "accuracy_cv_050": round(stats_m["accuracy_mean"], 4),
                        }
                    )

        all_attempts_df = pd.DataFrame(all_attempts_rows)
        all_attempts_df["es_ganador"] = False

        winners_rows: List[Dict[str, object]] = []
        oof_summary_rows: List[Dict[str, object]] = []
        oof_curves: Dict[str, pd.DataFrame] = {}
        tuned_models: Dict[str, TunedModelArtifact] = {}

        # Include NB-G* in Section 6 winners table only (not in Steps 7-12)
        for model_id in (MODEL_NB_G, MODEL_NB_G_STAR, MODEL_NB_B, MODEL_NB_H):
            sub = all_attempts_df.loc[all_attempts_df["modelo_id"] == model_id].copy()
            sub_sorted = sub.sort_values(
                by=["pr_auc_cv_media", "roc_auc_cv_media", "brier_cv"],
                ascending=[False, False, True],
            )
            winner_row = sub_sorted.iloc[0]
            win_num = int(winner_row["intento_num"])
            all_attempts_df.loc[
                (all_attempts_df["modelo_id"] == model_id)
                & (all_attempts_df["intento_num"] == win_num),
                "es_ganador",
            ] = True

            best_params = params_by_candidate[(model_id, win_num)]
            oof_prob = oof_probs_by_candidate[(model_id, win_num)]

            if model_id == MODEL_NB_G_STAR:
                tau_star_s, _ = select_oof_threshold_from_proba(y_tr, oof_prob)
                f1_star_s = compute_classification_metrics(y_tr, oof_prob, threshold=tau_star_s)["f1_pos"]
                dropped_desc = ", ".join(train_blocks.nb_g_star_dropped_features) or "ninguna"
                winners_rows.append(
                    {
                        "modelo_id": model_id,
                        "modelo": f"{MODEL_NB_G_STAR} · GaussianNB ({X_g_star.shape[1]} cols; sin {dropped_desc})",
                        "intento_ganador": str(winner_row["intento_id"]),
                        "var_smoothing_optimo": best_params["var_smoothing"],
                        "alpha_optimo": best_params["alpha"],
                        "prior_optimo": PRIOR_MODE_LABELS_ES[str(best_params["prior_mode"])],
                        "pr_auc_cv_media": float(winner_row["pr_auc_cv_media"]),
                        "pr_auc_cv_std": float(winner_row["pr_auc_cv_std"]),
                        "roc_auc_cv_media": float(winner_row["roc_auc_cv_media"]),
                        "f1_cv_umbral_050": float(winner_row["f1_cv_050"]),
                        "umbral_oof_optimo_tau": round(tau_star_s, 4),
                        "f1_oof_en_tau_optimo": round(f1_star_s, 4),
                        "brier_cv": float(winner_row["brier_cv"]),
                    }
                )
                continue

            # Step 7: OOF threshold selection maximizing class-1 F1 on train
            tau_star, thr_comp_df, thr_curve_df = self._select_oof_threshold(
                model_id=model_id,
                y_train=y_tr,
                oof_proba=oof_prob,
            )
            oof_curves[model_id] = thr_curve_df
            for _, r in thr_comp_df.iterrows():
                oof_summary_rows.append(r.to_dict())

            # Fit final selected model once on full train and predict once on test
            if model_id == MODEL_NB_G:
                est = build_gaussian_nb(
                    var_smoothing=float(best_params["var_smoothing"]),
                    priors=str(best_params["prior_mode"]),
                )
                X_tr_m = train_blocks.X_nb_g
                X_te_m = test_blocks.X_nb_g
            elif model_id == MODEL_NB_B:
                est = build_bernoulli_nb(
                    alpha=float(best_params["alpha"]),
                    priors=str(best_params["prior_mode"]),
                )
                X_tr_m = train_blocks.X_nb_b
                X_te_m = test_blocks.X_nb_b
            else:
                est = HybridNaiveBayes(
                    continuous_idx=train_blocks.continuous_idx,
                    binary_idx=train_blocks.binary_idx,
                    var_smoothing=float(best_params["var_smoothing"]),
                    alpha=float(best_params["alpha"]),
                    priors=str(best_params["prior_mode"]),
                )
                X_tr_m = train_blocks.X_nb_h
                X_te_m = test_blocks.X_nb_h

            t0 = time.perf_counter()
            est.fit(X_tr_m, y_tr)
            fit_time_s = time.perf_counter() - t0

            t1 = time.perf_counter()
            test_proba = est.predict_proba(X_te_m)[:, 1]
            pred_time_s = time.perf_counter() - t1

            mem_mb = compute_matrix_memory_mb(X_tr_m)

            winners_rows.append(
                {
                    "modelo_id": model_id,
                    "modelo": MODEL_LABELS_ES[model_id],
                    "intento_ganador": str(winner_row["intento_id"]),
                    "var_smoothing_optimo": best_params["var_smoothing"],
                    "alpha_optimo": best_params["alpha"],
                    "prior_optimo": PRIOR_MODE_LABELS_ES[str(best_params["prior_mode"])],
                    "pr_auc_cv_media": float(winner_row["pr_auc_cv_media"]),
                    "pr_auc_cv_std": float(winner_row["pr_auc_cv_std"]),
                    "roc_auc_cv_media": float(winner_row["roc_auc_cv_media"]),
                    "f1_cv_umbral_050": float(winner_row["f1_cv_050"]),
                    "umbral_oof_optimo_tau": round(tau_star, 4),
                    "f1_oof_en_tau_optimo": float(
                        thr_comp_df.loc[
                            thr_comp_df["esquema_umbral"].str.contains("OOF"), "f1_clase_1_oof_train"
                        ].iloc[0]
                    ),
                    "brier_cv": float(winner_row["brier_cv"]),
                }
            )

            tuned_models[model_id] = TunedModelArtifact(
                model_id=model_id,
                model_label_es=MODEL_LABELS_ES[model_id],
                best_params=best_params,
                best_cv_pr_auc=float(winner_row["pr_auc_cv_media"]),
                best_cv_roc_auc=float(winner_row["roc_auc_cv_media"]),
                oof_proba_train=oof_prob,
                oof_threshold_tau=tau_star,
                threshold_comparison_df=thr_comp_df,
                threshold_curve_df=thr_curve_df,
                fitted_estimator=est,
                fit_time_s=fit_time_s,
                predict_time_test_s=pred_time_s,
                input_memory_mb=mem_mb,
                test_proba=test_proba,
            )

        winners_df = pd.DataFrame(winners_rows)
        w_idx = winners_df.set_index("modelo_id")
        nb_g_vs_opt = float(w_idx.loc[MODEL_NB_G, "var_smoothing_optimo"])
        nb_g_is_interior = (nb_g_vs_opt > min(vs_grid_g)) and (nb_g_vs_opt < max(vs_grid_g))
        grid_sizes: Dict[str, object] = {
            "n_var_smoothing_nb_g": int(len(vs_grid_g)),
            "n_var_smoothing_nb_h": int(len(vs_grid_h)),
            "n_alpha": int(len(alpha_grid)),
            "n_priors": int(len(prior_modes)),
            "intentos_NB_G": int((all_attempts_df["modelo_id"] == MODEL_NB_G).sum()),
            "intentos_NB_G_star": int((all_attempts_df["modelo_id"] == MODEL_NB_G_STAR).sum()),
            "intentos_NB_B": int((all_attempts_df["modelo_id"] == MODEL_NB_B).sum()),
            "intentos_NB_H": int((all_attempts_df["modelo_id"] == MODEL_NB_H).sum()),
            "intentos_totales": int(len(all_attempts_df)),
            "nb_g_var_smoothing_optimo": nb_g_vs_opt,
            "nb_g_grid_max": float(max(vs_grid_g)),
            "nb_g_optimo_interior": bool(nb_g_is_interior),
            "nb_g_star_delta_pr_auc_cv": round(
                float(w_idx.loc[MODEL_NB_G_STAR, "pr_auc_cv_media"])
                - float(w_idx.loc[MODEL_NB_G, "pr_auc_cv_media"]),
                5,
            ),
            "nb_g_star_delta_roc_auc_cv": round(
                float(w_idx.loc[MODEL_NB_G_STAR, "roc_auc_cv_media"])
                - float(w_idx.loc[MODEL_NB_G, "roc_auc_cv_media"]),
                5,
            ),
        }

        return (
            all_attempts_df,
            winners_df,
            pd.DataFrame(oof_summary_rows),
            oof_curves,
            tuned_models,
            grid_sizes,
        )

    @staticmethod
    def _select_oof_threshold(
        model_id: str,
        y_train: np.ndarray,
        oof_proba: np.ndarray,
    ) -> Tuple[float, pd.DataFrame, pd.DataFrame]:
        """Sweep thresholds on train OOF predictions to maximize class-1 F1 without touching test."""
        y_arr = np.asarray(y_train, dtype=np.int8).ravel()
        p_arr = np.asarray(oof_proba, dtype=np.float64).ravel()
        best_tau, curve_df = select_oof_threshold_from_proba(y_arr, p_arr)

        m_050 = compute_classification_metrics(y_arr, p_arr, threshold=0.50)
        m_tau = compute_classification_metrics(y_arr, p_arr, threshold=best_tau)

        comp_df = pd.DataFrame(
            [
                {
                    "modelo_id": model_id,
                    "modelo": MODEL_LABELS_ES[model_id],
                    "esquema_umbral": "Umbral estándar (0.5000)",
                    "umbral_tau": 0.5000,
                    "f1_clase_1_oof_train": round(m_050["f1_pos"], 4),
                    "recall_clase_1_oof_train": round(m_050["recall_pos"], 4),
                    "precision_clase_1_oof_train": round(m_050["precision_pos"], 4),
                    "balanced_acc_oof_train": round(m_050["balanced_acc"], 4),
                    "accuracy_oof_train": round(m_050["accuracy"], 4),
                    "delta_f1_vs_050": 0.0000,
                },
                {
                    "modelo_id": model_id,
                    "modelo": MODEL_LABELS_ES[model_id],
                    "esquema_umbral": f"Umbral óptimo OOF (tau* = {best_tau:.4f})",
                    "umbral_tau": round(best_tau, 4),
                    "f1_clase_1_oof_train": round(m_tau["f1_pos"], 4),
                    "recall_clase_1_oof_train": round(m_tau["recall_pos"], 4),
                    "precision_clase_1_oof_train": round(m_tau["precision_pos"], 4),
                    "balanced_acc_oof_train": round(m_tau["balanced_acc"], 4),
                    "accuracy_oof_train": round(m_tau["accuracy"], 4),
                    "delta_f1_vs_050": round(m_tau["f1_pos"] - m_050["f1_pos"], 4),
                },
            ]
        )
        return best_tau, comp_df, curve_df

    def evaluate_on_test_and_calibrate(
        self,
        test_blocks: NaiveBayesPartitionBlocks,
        tuned_models: Dict[str, TunedModelArtifact],
        references_df: pd.DataFrame,
        trees_a_df: pd.DataFrame,
    ) -> Tuple[
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        Dict[str, ModelCurveBundle],
        float,
    ]:
        """Evaluate tuned models once on Version A test set with 300 person-bootstrap CIs and calibration."""
        y_te = test_blocks.y
        groups_te = test_blocks.groups
        n_te = len(y_te)

        test_rows: List[Dict[str, object]] = []
        cm_rows: List[Dict[str, object]] = []
        calib_rows: List[Dict[str, object]] = []
        curves_by_model: Dict[str, ModelCurveBundle] = {}

        t_boot_start = time.perf_counter()

        for model_id in MODEL_ORDER:
            art = tuned_models[model_id]
            prob_te = art.test_proba
            tau_star = art.oof_threshold_tau

            for point_label, thr in [
                ("Umbral OOF óptimo (tau*)", tau_star),
                ("Umbral por defecto (0.50)", 0.50),
            ]:
                m = compute_classification_metrics(y_te, prob_te, threshold=thr)
                ci = bootstrap_person_metrics(
                    y_true=y_te,
                    y_prob=prob_te,
                    groups=groups_te,
                    threshold=thr,
                    n_resamples=self.config.bootstrap_resamples,
                    random_state=self.config.random_state,
                )
                pred_te = (prob_te >= thr).astype(np.int8)
                tn, fp, fn, tp = confusion_matrix(y_te, pred_te, labels=[0, 1]).ravel()

                test_rows.append(
                    {
                        "modelo_id": model_id,
                        "modelo": art.model_label_es,
                        "punto_operacion": point_label,
                        "umbral_tau": round(thr, 4),
                        "pr_auc_test": round(m["pr_auc"], 4),
                        "pr_auc_ic95": f"[{ci['pr_auc'][0]:.4f}, {ci['pr_auc'][1]:.4f}]",
                        "roc_auc_test": round(m["roc_auc"], 4),
                        "roc_auc_ic95": f"[{ci['roc_auc'][0]:.4f}, {ci['roc_auc'][1]:.4f}]",
                        "f1_clase_1_test": round(m["f1_pos"], 4),
                        "f1_clase_1_ic95": f"[{ci['f1_pos'][0]:.4f}, {ci['f1_pos'][1]:.4f}]",
                        "recall_clase_1_test": round(m["recall_pos"], 4),
                        "recall_clase_1_ic95": f"[{ci['recall_pos'][0]:.4f}, {ci['recall_pos'][1]:.4f}]",
                        "precision_clase_1_test": round(m["precision_pos"], 4),
                        "precision_clase_1_ic95": f"[{ci['precision_pos'][0]:.4f}, {ci['precision_pos'][1]:.4f}]",
                        "balanced_acc_test": round(m["balanced_acc"], 4),
                        "balanced_acc_ic95": f"[{ci['balanced_acc'][0]:.4f}, {ci['balanced_acc'][1]:.4f}]",
                        "brier_test": round(m["brier"], 4),
                        "brier_ic95": f"[{ci['brier'][0]:.4f}, {ci['brier'][1]:.4f}]",
                        "accuracy_test": round(m["accuracy"], 4),
                        "accuracy_ic95": f"[{ci['accuracy'][0]:.4f}, {ci['accuracy'][1]:.4f}]",
                        "tiempo_fit_train_s": round(art.fit_time_s, 3),
                        "tiempo_predict_test_s": round(art.predict_time_test_s, 3),
                        "memoria_matriz_train_mb": round(art.input_memory_mb, 2),
                    }
                )

                cm_rows.append(
                    {
                        "modelo_id": model_id,
                        "punto_operacion": point_label,
                        "umbral_tau": round(thr, 4),
                        "TN_verdaderos_negativos": int(tn),
                        "FP_falsos_positivos": int(fp),
                        "FN_falsos_negativos": int(fn),
                        "TP_verdaderos_positivos": int(tp),
                        "pct_predichos_positivos": round(100.0 * float(tp + fp) / float(n_te), 2),
                    }
                )

            # Calibration & curves for this model
            prob_true, prob_pred = calibration_curve(y_te, prob_te, n_bins=10, strategy="uniform")
            bin_edges = np.linspace(0.0, 1.0, 11)
            bin_idx = np.clip(np.digitize(prob_te, bin_edges) - 1, 0, 9)
            bin_counts = np.bincount(bin_idx, minlength=10)
            non_empty = bin_counts > 0
            ece = float(
                np.sum(
                    (bin_counts[non_empty] / float(n_te))
                    * np.abs(prob_true - prob_pred)
                )
            )
            pct_extreme_probs = float(
                100.0 * np.mean((prob_te < 0.05) | (prob_te > 0.95))
            )

            calib_rows.append(
                {
                    "modelo_id": model_id,
                    "modelo": art.model_label_es,
                    "brier_test": round(float(brier_score_loss(y_te, prob_te)), 4),
                    "ece_error_calibracion_esperado": round(ece, 4),
                    "prob_media_predicha_test": round(float(prob_te.mean()), 4),
                    "prevalencia_real_test": round(float(y_te.mean()), 4),
                    "prob_mediana_clase_0": round(float(np.median(prob_te[y_te == 0])), 4),
                    "prob_mediana_clase_1": round(float(np.median(prob_te[y_te == 1])), 4),
                    "pct_probabilidades_extremas_<005_o_>095": round(pct_extreme_probs, 2),
                    "roc_auc_ranking_test": round(float(roc_auc_score(y_te, prob_te)), 4),
                    "pr_auc_ranking_test": round(float(average_precision_score(y_te, prob_te)), 4),
                }
            )

            prec_c, rec_c, _ = precision_recall_curve(y_te, prob_te)
            fpr_c, tpr_c, _ = roc_curve(y_te, prob_te)
            pr_step = max(1, len(prec_c) // 450)
            roc_step = max(1, len(fpr_c) // 450)

            hist_edges = np.linspace(0.0, 1.0, 41)
            h_c0, _ = np.histogram(prob_te[y_te == 0], bins=hist_edges, density=True)
            h_c1, _ = np.histogram(prob_te[y_te == 1], bins=hist_edges, density=True)

            curves_by_model[model_id] = ModelCurveBundle(
                model_id=model_id,
                model_label_es=art.model_label_es,
                pr_auc=float(average_precision_score(y_te, prob_te)),
                roc_auc=float(roc_auc_score(y_te, prob_te)),
                brier=float(brier_score_loss(y_te, prob_te)),
                ece=ece,
                precision_curve=prec_c[::pr_step],
                recall_curve=rec_c[::pr_step],
                fpr_curve=fpr_c[::roc_step],
                tpr_curve=tpr_c[::roc_step],
                calib_prob_pred=prob_pred,
                calib_prob_true=prob_true,
                calib_bin_counts=bin_counts,
                hist_bins=0.5 * (hist_edges[:-1] + hist_edges[1:]),
                hist_density_c0=h_c0,
                hist_density_c1=h_c1,
            )

        bootstrap_elapsed_s = time.perf_counter() - t_boot_start
        test_metrics_df = pd.DataFrame(test_rows)
        cm_df = pd.DataFrame(cm_rows)
        calib_df = pd.DataFrame(calib_rows)

        final_comp_a_df = self._build_final_comparison_table_a(
            test_metrics_df=test_metrics_df,
            references_df=references_df,
            trees_a_df=trees_a_df,
        )

        return (
            test_metrics_df,
            cm_df,
            calib_df,
            final_comp_a_df,
            curves_by_model,
            bootstrap_elapsed_s,
        )

    def fit_and_verify_phase4_baselines(
        self,
        modeling_data: VersionModelingData,
        tolerance: float = 5e-4,
    ) -> Tuple[pd.DataFrame, Dict[str, np.ndarray], Dict[str, float], bool]:
        """Re-fit Phase 4 (6.0) Logistic Regression and HistGradientBoosting on Version A and verify against CSV."""
        X_tr_csr, _ = modeling_data.train.build_sparse_matrix(mode="clean")
        X_te_csr, _ = modeling_data.test.build_sparse_matrix(mode="clean")
        X_tr_dense = modeling_data.train.dense_clean.to_numpy(dtype=np.float32)
        X_te_dense = modeling_data.test.dense_clean.to_numpy(dtype=np.float32)
        y_tr = modeling_data.train.y
        y_te = modeling_data.test.y

        logit_est = SGDClassifier(
            loss="log_loss",
            penalty="l2",
            alpha=1e-4,
            class_weight="balanced",
            max_iter=50,
            tol=1e-3,
            random_state=self.config.random_state,
        )
        t0 = time.perf_counter()
        logit_est.fit(X_tr_csr, y_tr)
        fit_logit_s = time.perf_counter() - t0
        prob_logit = logit_est.predict_proba(X_te_csr)[:, 1]

        hgb_est = HistGradientBoostingClassifier(
            max_iter=120,
            learning_rate=0.08,
            max_leaf_nodes=31,
            min_samples_leaf=100,
            class_weight="balanced",
            random_state=self.config.random_state,
        )
        t1 = time.perf_counter()
        hgb_est.fit(X_tr_dense, y_tr)
        fit_hgb_s = time.perf_counter() - t1
        prob_hgb = hgb_est.predict_proba(X_te_dense)[:, 1]

        p4_df = pd.read_csv(self.config.phase4_test_csv_path, encoding="utf-8")
        p4_a = p4_df.loc[p4_df["version"].astype(str).str.startswith("A")].copy()

        specs = [
            (
                "Logística Regularizada (6.0 · OHE 2,981 cols)",
                "Logística",
                2981,
                prob_logit,
                fit_logit_s,
            ),
            (
                "HistGradientBoosting (6.0 · 14 cols densas)",
                "HistGradientBoosting",
                14,
                prob_hgb,
                fit_hgb_s,
            ),
        ]

        ver_rows: List[Dict[str, object]] = []
        all_match = True
        for label, key_substr, n_cols, probs, fit_s in specs:
            m = compute_classification_metrics(y_te, probs, threshold=0.50)
            ref_sub = p4_a.loc[p4_a["modelo"].astype(str).str.contains(key_substr)]
            ref_pr = float(ref_sub.iloc[0]["pr_auc_test"]) if not ref_sub.empty else np.nan
            ref_roc = float(ref_sub.iloc[0]["roc_auc_test"]) if not ref_sub.empty else np.nan
            ref_f1 = float(ref_sub.iloc[0]["f1_pos_test"]) if not ref_sub.empty else np.nan
            diff_pr = abs(m["pr_auc"] - ref_pr) if not np.isnan(ref_pr) else np.nan
            diff_roc = abs(m["roc_auc"] - ref_roc) if not np.isnan(ref_roc) else np.nan
            ok = bool((diff_pr <= tolerance) and (diff_roc <= tolerance))
            if not ok:
                all_match = False

            ver_rows.append(
                {
                    "modelo_6_0": label,
                    "n_variables_X": n_cols,
                    "ponderacion_clases": "class_weight='balanced'",
                    "pr_auc_csv_6_0": round(ref_pr, 4),
                    "pr_auc_reproducido": round(m["pr_auc"], 4),
                    "diff_abs_pr_auc": round(diff_pr, 6),
                    "roc_auc_csv_6_0": round(ref_roc, 4),
                    "roc_auc_reproducido": round(m["roc_auc"], 4),
                    "diff_abs_roc_auc": round(diff_roc, 6),
                    "f1_050_csv_6_0": round(ref_f1, 4),
                    "f1_050_reproducido": round(m["f1_pos"], 4),
                    "tiempo_fit_s": round(fit_s, 3),
                    "coincide_tolerancia_5e4": ok,
                }
            )

        repro_probas = {
            "LOGIT_6_0": prob_logit,
            "HGB_6_0": prob_hgb,
        }
        fit_times = {
            "LOGIT_6_0": fit_logit_s,
            "HGB_6_0": fit_hgb_s,
        }
        return pd.DataFrame(ver_rows), repro_probas, fit_times, all_match

    def build_like_for_like_and_paired_tables(
        self,
        test_blocks: NaiveBayesPartitionBlocks,
        tuned_models: Dict[str, TunedModelArtifact],
        test_metrics_df: pd.DataFrame,
        repro_probas: Dict[str, np.ndarray],
        repro_fit_times: Dict[str, float],
        repro_ok: bool,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Build Section 11 like-for-like tables, paired person-bootstrap CIs, and equal-alert-rate F1 table."""
        y_te = test_blocks.y
        groups_te = test_blocks.groups

        prob_g = tuned_models[MODEL_NB_G].test_proba
        prob_b = tuned_models[MODEL_NB_B].test_proba
        prob_h = tuned_models[MODEL_NB_H].test_proba
        tau_h = tuned_models[MODEL_NB_H].oof_threshold_tau
        target_alert_rate = float(np.mean(prob_h >= tau_h))

        prob_logit = repro_probas.get("LOGIT_6_0")
        prob_hgb = repro_probas.get("HGB_6_0")

        # 1. Equal-alert-rate table (all models evaluated at NB-H's fixed alert rate on test, no test tuning)
        eq_specs: List[Tuple[str, str, int, str, np.ndarray, float | None]] = [
            (
                "NB-G",
                "Solo bloque denso (14 cols)",
                14,
                "Sin ponderar (empírico)",
                prob_g,
                None,
            ),
            (
                "NB-B",
                "Con ocupación OHE (2,971 cols)",
                2971,
                "Sin ponderar (empírico)",
                prob_b,
                None,
            ),
            (
                "NB-H",
                "Con ocupación OHE (2,981 cols)",
                2981,
                "Sin ponderar (empírico)",
                prob_h,
                tau_h,
            ),
        ]
        if prob_logit is not None:
            eq_specs.append(
                (
                    "Logística Regularizada (6.0)",
                    "Con ocupación OHE (2,981 cols)",
                    2981,
                    "Balanceada (class_weight='balanced')",
                    prob_logit,
                    None,
                )
            )
        if prob_hgb is not None:
            eq_specs.append(
                (
                    "HistGradientBoosting (6.0)",
                    "Solo bloque denso (14 cols)",
                    14,
                    "Balanceada (class_weight='balanced')",
                    prob_hgb,
                    None,
                )
            )

        eq_cutoffs: Dict[str, float] = {}
        eq_rows: List[Dict[str, object]] = []
        for m_name, space_lbl, n_vars, weight_lbl, p_vec, fixed_tau in eq_specs:
            if fixed_tau is not None:
                cutoff = float(fixed_tau)
                eff_rate = float(np.mean(p_vec >= cutoff))
            else:
                cutoff, eff_rate = compute_equal_alert_rate_cutoff(p_vec, target_alert_rate)
            eq_cutoffs[m_name] = cutoff
            m_eq = compute_classification_metrics(y_te, p_vec, threshold=cutoff)
            eq_rows.append(
                {
                    "modelo": m_name,
                    "espacio_variables": space_lbl,
                    "n_variables_X": n_vars,
                    "ponderacion_clases": weight_lbl,
                    "tasa_alerta_objetivo_pct": round(100.0 * target_alert_rate, 2),
                    "tasa_alerta_efectiva_pct": round(100.0 * eff_rate, 2),
                    "umbral_corte_equivalente": round(cutoff, 4),
                    "pr_auc_test": round(m_eq["pr_auc"], 4),
                    "roc_auc_test": round(m_eq["roc_auc"], 4),
                    "f1_igual_alerta_test": round(m_eq["f1_pos"], 4),
                    "recall_igual_alerta_test": round(m_eq["recall_pos"], 4),
                    "precision_igual_alerta_test": round(m_eq["precision_pos"], 4),
                    "balanced_acc_igual_alerta_test": round(m_eq["balanced_acc"], 4),
                    "brier_solo_sin_ponderar": round(m_eq["brier"], 4)
                    if weight_lbl.startswith("Sin ponderar")
                    else np.nan,
                }
            )
        eq_df = pd.DataFrame(eq_rows)

        # 2. Like-for-like tables (Dense-only 14 cols & With-occupation 2,971-2,981 cols)
        def _row_from_test_metrics(mid: str) -> pd.Series:
            return test_metrics_df.loc[
                (test_metrics_df["modelo_id"] == mid)
                & (test_metrics_df["punto_operacion"].str.contains("OOF"))
            ].iloc[0]

        dense_rows: List[Dict[str, object]] = []
        r_g = _row_from_test_metrics(MODEL_NB_G)
        eq_g = eq_df.loc[eq_df["modelo"] == "NB-G"].iloc[0]
        dense_rows.append(
            {
                "modelo": "NB-G · GaussianNB (7.1)",
                "n_variables_X": 14,
                "ponderacion_clases": "Sin ponderar (empírico)",
                "pr_auc_test": float(r_g["pr_auc_test"]),
                "pr_auc_ic95": str(r_g["pr_auc_ic95"]),
                "roc_auc_test": float(r_g["roc_auc_test"]),
                "roc_auc_ic95": str(r_g["roc_auc_ic95"]),
                "f1_umbral_propio": float(r_g["f1_clase_1_test"]),
                "f1_igual_alerta_NB_H": float(eq_g["f1_igual_alerta_test"]),
                "precision_igual_alerta": float(eq_g["precision_igual_alerta_test"]),
                "recall_igual_alerta": float(eq_g["recall_igual_alerta_test"]),
                "brier_comparable_sin_ponderar": float(r_g["brier_test"]),
                "tiempo_fit_s": float(r_g["tiempo_fit_train_s"]),
            }
        )
        if prob_hgb is not None:
            m_hgb = compute_classification_metrics(y_te, prob_hgb, threshold=0.50)
            ci_hgb = bootstrap_person_metrics(
                y_te, prob_hgb, groups_te, threshold=0.50,
                n_resamples=self.config.bootstrap_resamples,
                random_state=self.config.random_state,
            )
            eq_hgb = eq_df.loc[eq_df["modelo"] == "HistGradientBoosting (6.0)"].iloc[0]
            dense_rows.append(
                {
                    "modelo": "HistGradientBoosting (6.0)",
                    "n_variables_X": 14,
                    "ponderacion_clases": "Balanceada (class_weight='balanced')",
                    "pr_auc_test": round(m_hgb["pr_auc"], 4),
                    "pr_auc_ic95": f"[{ci_hgb['pr_auc'][0]:.4f}, {ci_hgb['pr_auc'][1]:.4f}]",
                    "roc_auc_test": round(m_hgb["roc_auc"], 4),
                    "roc_auc_ic95": f"[{ci_hgb['roc_auc'][0]:.4f}, {ci_hgb['roc_auc'][1]:.4f}]",
                    "f1_umbral_propio": round(m_hgb["f1_pos"], 4),
                    "f1_igual_alerta_NB_H": float(eq_hgb["f1_igual_alerta_test"]),
                    "precision_igual_alerta": float(eq_hgb["precision_igual_alerta_test"]),
                    "recall_igual_alerta": float(eq_hgb["recall_igual_alerta_test"]),
                    "brier_comparable_sin_ponderar": np.nan,
                    "tiempo_fit_s": round(float(repro_fit_times.get("HGB_6_0", np.nan)), 3),
                }
            )
        like_dense_df = pd.DataFrame(dense_rows)

        occ_rows: List[Dict[str, object]] = []
        for mid, n_v, lbl in [
            (MODEL_NB_B, 2971, "NB-B · BernoulliNB (7.1)"),
            (MODEL_NB_H, 2981, "NB-H · HybridNaiveBayes (7.1)"),
        ]:
            rm = _row_from_test_metrics(mid)
            eq_m = eq_df.loc[eq_df["modelo"] == mid].iloc[0]
            occ_rows.append(
                {
                    "modelo": lbl,
                    "n_variables_X": n_v,
                    "ponderacion_clases": "Sin ponderar (empírico)",
                    "pr_auc_test": float(rm["pr_auc_test"]),
                    "pr_auc_ic95": str(rm["pr_auc_ic95"]),
                    "roc_auc_test": float(rm["roc_auc_test"]),
                    "roc_auc_ic95": str(rm["roc_auc_ic95"]),
                    "f1_umbral_propio": float(rm["f1_clase_1_test"]),
                    "f1_igual_alerta_NB_H": float(eq_m["f1_igual_alerta_test"]),
                    "precision_igual_alerta": float(eq_m["precision_igual_alerta_test"]),
                    "recall_igual_alerta": float(eq_m["recall_igual_alerta_test"]),
                    "brier_comparable_sin_ponderar": float(rm["brier_test"]),
                    "tiempo_fit_s": float(rm["tiempo_fit_train_s"]),
                }
            )
        if prob_logit is not None:
            m_log = compute_classification_metrics(y_te, prob_logit, threshold=0.50)
            ci_log = bootstrap_person_metrics(
                y_te, prob_logit, groups_te, threshold=0.50,
                n_resamples=self.config.bootstrap_resamples,
                random_state=self.config.random_state,
            )
            eq_log = eq_df.loc[eq_df["modelo"] == "Logística Regularizada (6.0)"].iloc[0]
            occ_rows.append(
                {
                    "modelo": "Logística Regularizada (6.0)",
                    "n_variables_X": 2981,
                    "ponderacion_clases": "Balanceada (class_weight='balanced')",
                    "pr_auc_test": round(m_log["pr_auc"], 4),
                    "pr_auc_ic95": f"[{ci_log['pr_auc'][0]:.4f}, {ci_log['pr_auc'][1]:.4f}]",
                    "roc_auc_test": round(m_log["roc_auc"], 4),
                    "roc_auc_ic95": f"[{ci_log['roc_auc'][0]:.4f}, {ci_log['roc_auc'][1]:.4f}]",
                    "f1_umbral_propio": round(m_log["f1_pos"], 4),
                    "f1_igual_alerta_NB_H": float(eq_log["f1_igual_alerta_test"]),
                    "precision_igual_alerta": float(eq_log["precision_igual_alerta_test"]),
                    "recall_igual_alerta": float(eq_log["recall_igual_alerta_test"]),
                    "brier_comparable_sin_ponderar": np.nan,
                    "tiempo_fit_s": round(float(repro_fit_times.get("LOGIT_6_0", np.nan)), 3),
                }
            )
        like_occ_df = pd.DataFrame(occ_rows)

        # 3. Paired person-level bootstrap comparisons (same resampled persons, 300 resamples, seed 42)
        paired_specs: List[Tuple[str, str, str, np.ndarray, np.ndarray, float, float]] = [
            (
                "NB-H vs. NB-B",
                "Homogénea (aporte del bloque Gaussiano sobre Bernoulli)",
                "2,981 vs. 2,971 cols",
                prob_h,
                prob_b,
                eq_cutoffs["NB-H"],
                eq_cutoffs["NB-B"],
            ),
        ]
        if repro_ok and prob_logit is not None:
            paired_specs.insert(
                0,
                (
                    "NB-H vs. Logística Regularizada (6.0)",
                    "Homogénea (mismo espacio con ocupación OHE)",
                    "2,981 vs. 2,981 cols",
                    prob_h,
                    prob_logit,
                    eq_cutoffs["NB-H"],
                    eq_cutoffs["Logística Regularizada (6.0)"],
                ),
            )
        if repro_ok and prob_hgb is not None:
            paired_specs.append(
                (
                    "NB-G vs. HistGradientBoosting (6.0)",
                    "Homogénea (mismo espacio solo denso)",
                    "14 vs. 14 cols",
                    prob_g,
                    prob_hgb,
                    eq_cutoffs["NB-G"],
                    eq_cutoffs["HistGradientBoosting (6.0)"],
                )
            )
            paired_specs.append(
                (
                    "NB-H vs. HistGradientBoosting (6.0) [auditoría]",
                    "NO homogénea (distinto espacio de variables; solo auditoría F2)",
                    "2,981 vs. 14 cols",
                    prob_h,
                    prob_hgb,
                    eq_cutoffs["NB-H"],
                    eq_cutoffs["HistGradientBoosting (6.0)"],
                )
            )

        paired_rows: List[Dict[str, object]] = []
        for comp_name, comp_type, vars_desc, pa, pb, ta, tb in paired_specs:
            res = paired_bootstrap_person_diffs(
                y_true=y_te,
                prob_a=pa,
                prob_b=pb,
                groups=groups_te,
                threshold_a=ta,
                threshold_b=tb,
                n_resamples=self.config.bootstrap_resamples,
                random_state=self.config.random_state,
            )
            paired_rows.append(
                {
                    "comparacion_A_menos_B": comp_name,
                    "tipo_comparacion": comp_type,
                    "variables_comparadas": vars_desc,
                    "delta_pr_auc": round(float(res["delta_pr_auc"]), 4),
                    "ic95_delta_pr_auc": f"[{float(res['delta_pr_auc_ci_low']):+.4f}, {float(res['delta_pr_auc_ci_high']):+.4f}]",
                    "pr_auc_excluye_cero": bool(res["pr_auc_excluye_cero"]),
                    "veredicto_pr_auc": str(res["veredicto_pr_auc"]),
                    "delta_roc_auc": round(float(res["delta_roc_auc"]), 4),
                    "ic95_delta_roc_auc": f"[{float(res['delta_roc_auc_ci_low']):+.4f}, {float(res['delta_roc_auc_ci_high']):+.4f}]",
                    "roc_auc_excluye_cero": bool(res["roc_auc_excluye_cero"]),
                    "veredicto_roc_auc": str(res["veredicto_roc_auc"]),
                    "delta_f1_igual_alerta": round(float(res["delta_f1"]), 4),
                    "ic95_delta_f1_igual_alerta": f"[{float(res['delta_f1_ci_low']):+.4f}, {float(res['delta_f1_ci_high']):+.4f}]",
                    "f1_excluye_cero": bool(res["f1_excluye_cero"]),
                    "veredicto_f1_igual_alerta": str(res["veredicto_f1"]),
                }
            )
        paired_df = pd.DataFrame(paired_rows)
        return like_dense_df, like_occ_df, paired_df, eq_df

    @staticmethod
    def _build_final_comparison_table_a(
        test_metrics_df: pd.DataFrame,
        references_df: pd.DataFrame,
        trees_a_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Build Section 11 unified comparison table, keeping Brier strictly for unweighted models."""
        f1_ref2 = 0.4612
        auc_ceiling_ref3 = 0.7133

        rows: List[Dict[str, object]] = []

        pr_map_ref = {}
        brier_map_ref = {}
        if "test_pr_auc" in references_df.columns:
            for _, r in references_df.iterrows():
                pr_map_ref[str(r["referencia_id"])[:5]] = float(r["test_pr_auc"])
                brier_map_ref[str(r["referencia_id"])[:5]] = float(r["test_brier"])

        for _, trow in trees_a_df.iterrows():
            m_short = str(trow["modelo_corto"])
            f1_val = float(trow["test_f1_clase_1"])
            auc_val = float(trow["test_roc_auc"])
            gain_ratio_pct = 100.0 * (auc_val - 0.50) / (auc_ceiling_ref3 - 0.50)
            ref_key = m_short[:5] if m_short.startswith("Ref") else ""
            is_weighted = ("Ref 3" in m_short) or ("balanced" in str(trow["punto_operacion"]))
            weight_lbl = (
                "Balanceada (class_weight='balanced')"
                if is_weighted
                else "Sin ponderar (empírico)"
            )
            brier_unweighted = (
                round(brier_map_ref[ref_key], 4)
                if (ref_key in brier_map_ref and not is_weighted)
                else np.nan
            )
            rows.append(
                {
                    "familia": "Referencia" if m_short.startswith("Ref") else "Árbol de Decisión (7.0)",
                    "modelo": m_short,
                    "ponderacion_clases": weight_lbl,
                    "punto_operacion": str(trow["punto_operacion"]),
                    "n_variables_X": int(trow["n_variables_X"]),
                    "test_pr_auc": round(pr_map_ref.get(ref_key, np.nan), 4)
                    if ref_key in pr_map_ref
                    else np.nan,
                    "test_roc_auc": round(auc_val, 4),
                    "test_f1_clase_1": round(f1_val, 4),
                    "delta_f1_vs_ref2_04612": round(f1_val - f1_ref2, 4),
                    "fraccion_ganancia_roc_sobre_azar_vs_ref3_pct": round(gain_ratio_pct, 2),
                    "test_recall_clase_1": round(float(trow["test_recall_clase_1"]), 4),
                    "test_precision_clase_1": round(float(trow["test_precision_clase_1"]), 4),
                    "test_accuracy": round(float(trow["test_accuracy"]), 4),
                    "test_brier_sin_ponderar": brier_unweighted,
                    "tiempo_fit_s": np.nan,
                    "memoria_mb": np.nan,
                }
            )

        for _, nb_row in test_metrics_df.iterrows():
            f1_val = float(nb_row["f1_clase_1_test"])
            auc_val = float(nb_row["roc_auc_test"])
            gain_ratio_pct = 100.0 * (auc_val - 0.50) / (auc_ceiling_ref3 - 0.50)
            n_vars = (
                14
                if nb_row["modelo_id"] == MODEL_NB_G
                else (2971 if nb_row["modelo_id"] == MODEL_NB_B else 2981)
            )
            rows.append(
                {
                    "familia": "Naive Bayes (7.1)",
                    "modelo": f"{nb_row['modelo_id']} ({nb_row['punto_operacion']})",
                    "ponderacion_clases": "Sin ponderar (empírico)",
                    "punto_operacion": f"tau = {nb_row['umbral_tau']:.4f}",
                    "n_variables_X": n_vars,
                    "test_pr_auc": float(nb_row["pr_auc_test"]),
                    "test_roc_auc": round(auc_val, 4),
                    "test_f1_clase_1": round(f1_val, 4),
                    "delta_f1_vs_ref2_04612": round(f1_val - f1_ref2, 4),
                    "fraccion_ganancia_roc_sobre_azar_vs_ref3_pct": round(gain_ratio_pct, 2),
                    "test_recall_clase_1": float(nb_row["recall_clase_1_test"]),
                    "test_precision_clase_1": float(nb_row["precision_clase_1_test"]),
                    "test_accuracy": float(nb_row["accuracy_test"]),
                    "test_brier_sin_ponderar": float(nb_row["brier_test"]),
                    "tiempo_fit_s": float(nb_row["tiempo_fit_train_s"]),
                    "memoria_mb": float(nb_row["memoria_matriz_train_mb"]),
                }
            )

        return pd.DataFrame(rows)

    def run_full_evaluation(
        self,
        train_blocks: NaiveBayesPartitionBlocks,
        test_blocks: NaiveBayesPartitionBlocks,
        modeling_data: VersionModelingData | None = None,
    ) -> NaiveBayesEvaluationBundle:
        """Orchestrate Steps 3, 5, 6, 7, 8, 9, and 11 on Version A (including fair 6.0 comparisons)."""
        refs_df, trees_a_df = self.load_project_references()
        folds, overlap_count = self._build_folds(
            train_blocks.X_nb_h, train_blocks.y, train_blocks.groups
        )
        baseline_cv_df = self.run_baseline_cv(train_blocks, folds)
        (
            tuning_all_df,
            tuning_winners_df,
            oof_summary_df,
            oof_curves,
            tuned_models,
            grid_sizes,
        ) = self.run_honest_tuning_and_oof(train_blocks, test_blocks, folds)

        (
            test_metrics_df,
            cm_df,
            calib_df,
            final_comp_a_df,
            model_curves,
            boot_s,
        ) = self.evaluate_on_test_and_calibrate(
            test_blocks=test_blocks,
            tuned_models=tuned_models,
            references_df=refs_df,
            trees_a_df=trees_a_df,
        )

        if modeling_data is not None:
            p4_ver_df, repro_probas, repro_fit_times, repro_ok = self.fit_and_verify_phase4_baselines(
                modeling_data=modeling_data,
                tolerance=5e-4,
            )
        else:
            p4_ver_df = pd.DataFrame()
            repro_probas = {}
            repro_fit_times = {}
            repro_ok = False

        like_dense_df, like_occ_df, paired_df, eq_alert_df = self.build_like_for_like_and_paired_tables(
            test_blocks=test_blocks,
            tuned_models=tuned_models,
            test_metrics_df=test_metrics_df,
            repro_probas=repro_probas,
            repro_fit_times=repro_fit_times,
            repro_ok=repro_ok,
        )

        return NaiveBayesEvaluationBundle(
            references_table=refs_df,
            trees_reference_table=trees_a_df,
            baseline_cv_table=baseline_cv_df,
            tuning_all_attempts_table=tuning_all_df,
            tuning_winners_table=tuning_winners_df,
            oof_threshold_summary_table=oof_summary_df,
            oof_threshold_curves=oof_curves,
            test_metrics_table=test_metrics_df,
            confusion_matrices_table=cm_df,
            calibration_summary_table=calib_df,
            final_comparison_table_a=final_comp_a_df,
            phase4_reproduction_table=p4_ver_df,
            like_for_like_dense_table=like_dense_df,
            like_for_like_occ_table=like_occ_df,
            paired_bootstrap_comparisons_table=paired_df,
            equal_alert_rate_table=eq_alert_df,
            grid_sizes=grid_sizes,
            tuned_models=tuned_models,
            model_curves=model_curves,
            cv_person_overlap_count=overlap_count,
            bootstrap_elapsed_s=boot_s,
        )
