"""Gaussian assumption diagnostics and in-RAM outlier sensitivity experiment inside Version A."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import sparse, stats
from scipy.special import logsumexp
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.naive_bayes import BernoulliNB, GaussianNB

from .config import (
    COLLINEAR_REDUNDANT_FEATURES,
    CONTINUOUS_ROB_FEATURES,
    CONTINUOUS_TO_ORIGINAL_COL,
    DENSE_FEATURE_METADATA_ES,
    GAUSSIAN_HYBRID_FEATURES,
    IQR_WINSOR_BOUNDS_INFO,
    LEAKAGE_FEATURES_IN_X,
    MODEL_NB_G,
    MODEL_NB_H,
    NaiveBayesConfig,
    ORIGINAL_COL_LABELS_ES,
)
from .evaluation import (
    TunedModelArtifact,
    bootstrap_person_metrics,
    compute_classification_metrics,
    paired_bootstrap_person_diffs,
    select_oof_threshold_from_proba,
)
from .feature_blocks import NaiveBayesPartitionBlocks
from .models import HybridNaiveBayes, build_gaussian_nb, resolve_priors


@dataclass(frozen=True)
class GaussianFitHistogramData:
    """Histogram bins and fitted Gaussian density curves per class for one continuous feature."""

    feature_rob: str
    feature_orig: str
    label_es: str
    bin_centers: np.ndarray
    hist_density_c0: np.ndarray
    hist_density_c1: np.ndarray
    x_grid: np.ndarray
    gauss_pdf_c0: np.ndarray
    gauss_pdf_c1: np.ndarray
    theta_c0: float
    theta_c1: float
    std_c0: float
    std_c1: float
    tukey_low: float
    tukey_high: float
    pct_outside_tukey: float


@dataclass(frozen=True)
class OutlierDiagnosticsBundle:
    """Complete outputs of Section 4 (Naive Bayes vs. outliers inside Version A)."""

    version_b_bounds_table: pd.DataFrame
    distribution_table: pd.DataFrame
    parameter_shift_table: pd.DataFrame
    sensitivity_experiment_table: pd.DataFrame
    subset_summary: Dict[str, object]
    histogram_curves: List[GaussianFitHistogramData]


@dataclass(frozen=True)
class TunedOutlierExperimentsBundle:
    """Outputs of tuned outlier experiments E1, E2, and E3 (Version A and A-winsorized parts)."""

    e1_tuned_sensitivity_table: pd.DataFrame
    e2_tukey_fences_table: pd.DataFrame
    e2_winsorization_table: pd.DataFrame
    e2_paired_diff_table: pd.DataFrame
    e3_partial_a_and_wins_table: pd.DataFrame


def build_version_b_bounds_table() -> pd.DataFrame:
    """Build Spanish audit table describing exactly which columns Version B clips (from IQR_WINSOR_BOUNDS_INFO)."""
    rows: List[Dict[str, object]] = []
    # 1. Columns explicitly winsorized in Version B (read dynamically from IQR_WINSOR_BOUNDS_INFO)
    for col_orig, (low_b, high_b) in IQR_WINSOR_BOUNDS_INFO.items():
        col_rob = f"{col_orig}_rob"
        if col_orig == "veces_ese_oficio" or col_rob in LEAKAGE_FEATURES_IN_X:
            enters_x = "No (excluida por fuga directa 100 %)"
            changes_x = "No afecta a X en 7.1"
        elif col_rob in COLLINEAR_REDUNDANT_FEATURES or col_orig == "n_skills_competence":
            enters_x = "No (excluida por colinealidad r = 0.952 con n_skills_essential)"
            changes_x = "No afecta a X en 7.1"
        else:
            enters_x = f"Sí (entra como {col_rob})"
            changes_x = "Sí cambia en X (únicas columnas continuas alteradas en B)"

        rows.append(
            {
                "variable_original": col_orig,
                "descripcion_es": ORIGINAL_COL_LABELS_ES.get(col_orig, col_orig),
                "recortada_en_version_B": "Sí (winsorizada con IQR de train)",
                "cota_inf_B": round(float(low_b), 2),
                "cota_sup_B": round(float(high_b), 2),
                "entra_en_X_7_1": enters_x,
                "efecto_real_en_X_B_vs_A": changes_x,
            }
        )

    # 2. Remaining continuous features that enter X and are NOT touched by Version B
    for col_rob in CONTINUOUS_ROB_FEATURES:
        col_orig = CONTINUOUS_TO_ORIGINAL_COL[col_rob]
        if col_orig in IQR_WINSOR_BOUNDS_INFO:
            continue
        rows.append(
            {
                "variable_original": col_orig,
                "descripcion_es": ORIGINAL_COL_LABELS_ES.get(col_orig, col_orig),
                "recortada_en_version_B": "No (idéntica en Versión A y Versión B)",
                "cota_inf_B": np.nan,
                "cota_sup_B": np.nan,
                "entra_en_X_7_1": f"Sí (entra como {col_rob})",
                "efecto_real_en_X_B_vs_A": "Idéntica entre A y B (colas pesadas NO recortadas en B)",
            }
        )
    return pd.DataFrame(rows)


def winsorize_continuous_blocks_in_ram(
    train_blocks: NaiveBayesPartitionBlocks,
    test_blocks: NaiveBayesPartitionBlocks,
) -> Tuple[np.ndarray, np.ndarray, sparse.csr_matrix, sparse.csr_matrix, pd.DataFrame]:
    """Fit Tukey fences on train only for the 7 continuous columns and clip train/test in RAM."""
    X_g_tr = train_blocks.X_nb_g.copy()
    X_g_te = test_blocks.X_nb_g.copy()
    g_name_to_idx = {name: i for i, name in enumerate(train_blocks.nb_g_feature_names)}

    X_h_g10_tr = np.ascontiguousarray(
        train_blocks.dense_clean_df[list(GAUSSIAN_HYBRID_FEATURES)].to_numpy(dtype=np.float32, copy=True)
    )
    X_h_g10_te = np.ascontiguousarray(
        test_blocks.dense_clean_df[list(GAUSSIAN_HYBRID_FEATURES)].to_numpy(dtype=np.float32, copy=True)
    )
    h_name_to_idx = {name: i for i, name in enumerate(GAUSSIAN_HYBRID_FEATURES)}

    fence_rows: List[Dict[str, object]] = []
    for col_rob in CONTINUOUS_ROB_FEATURES:
        idx_g = g_name_to_idx[col_rob]
        idx_h = h_name_to_idx[col_rob]
        arr_tr = X_g_tr[:, idx_g].astype(np.float64)
        arr_te = X_g_te[:, idx_g].astype(np.float64)

        q1, q3 = np.percentile(arr_tr, [25.0, 75.0])
        iqr = q3 - q1
        low_f = float(q1 - 1.5 * iqr)
        high_f = float(q3 + 1.5 * iqr)

        clipped_tr = (arr_tr < low_f) | (arr_tr > high_f)
        clipped_te = (arr_te < low_f) | (arr_te > high_f)

        new_tr = np.clip(arr_tr, low_f, high_f).astype(np.float32)
        new_te = np.clip(arr_te, low_f, high_f).astype(np.float32)

        X_g_tr[:, idx_g] = new_tr
        X_g_te[:, idx_g] = new_te
        X_h_g10_tr[:, idx_h] = new_tr
        X_h_g10_te[:, idx_h] = new_te

        fence_rows.append(
            {
                "variable_rob": col_rob,
                "valla_inf_tukey_train_rob": round(low_f, 4),
                "valla_sup_tukey_train_rob": round(high_f, 4),
                "filas_recortadas_train": int(clipped_tr.sum()),
                "pct_recortado_train": round(100.0 * float(clipped_tr.mean()), 2),
                "filas_recortadas_test": int(clipped_te.sum()),
                "pct_recortado_test": round(100.0 * float(clipped_te.mean()), 2),
            }
        )

    X_h_tr_w = sparse.hstack([sparse.csr_matrix(X_h_g10_tr), train_blocks.X_nb_b], format="csr")
    X_h_te_w = sparse.hstack([sparse.csr_matrix(X_h_g10_te), test_blocks.X_nb_b], format="csr")
    return X_g_tr, X_g_te, X_h_tr_w, X_h_te_w, pd.DataFrame(fence_rows)


def evaluate_nb_h_vs_grid_cv(
    X_g10: np.ndarray,
    X_b2971: sparse.csr_matrix,
    y: np.ndarray,
    groups: np.ndarray,
    var_smoothing_grid: Tuple[float, ...],
    alpha_opt: float,
    prior_mode: str,
    variant_label: str,
    cv_folds: int = 5,
    random_state: int = 42,
) -> pd.DataFrame:
    """Evaluate NB-H across a var_smoothing grid in StratifiedGroupKFold(5) for one data variant (E3)."""
    sgkf = StratifiedGroupKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    folds = list(sgkf.split(X_g10, y, groups))
    n_tr = len(y)
    p_seq = resolve_priors(prior_mode)

    oof_lp_b = np.zeros((n_tr, 2), dtype=np.float64)
    fold_log_priors: Dict[int, np.ndarray] = {}
    for fold_idx, (tr_idx, va_idx) in enumerate(folds):
        y_f = y[tr_idx]
        if prior_mode == "balanced":
            log_pi = np.log(np.array([0.5, 0.5], dtype=np.float64))
        else:
            _, cnts = np.unique(y_f, return_counts=True)
            log_pi = np.log(cnts.astype(np.float64) / float(len(y_f)))
        fold_log_priors[fold_idx] = log_pi

        bnb = BernoulliNB(alpha=float(alpha_opt), binarize=0.0, force_alpha=True, class_prior=p_seq)
        bnb.fit(X_b2971[tr_idx], y_f)
        oof_lp_b[va_idx] = bnb.predict_log_proba(X_b2971[va_idx])

    rows: List[Dict[str, object]] = []
    for vs in var_smoothing_grid:
        pr_folds: List[float] = []
        roc_folds: List[float] = []
        brier_folds: List[float] = []
        for fold_idx, (tr_idx, va_idx) in enumerate(folds):
            gnb = GaussianNB(var_smoothing=float(vs), priors=p_seq)
            gnb.fit(X_g10[tr_idx], y[tr_idx])
            lp_g = gnb.predict_log_proba(X_g10[va_idx])
            log_pi = fold_log_priors[fold_idx]
            unnorm = lp_g + oof_lp_b[va_idx] - log_pi[np.newaxis, :]
            normed = unnorm - logsumexp(unnorm, axis=1, keepdims=True)
            p1 = np.exp(normed[:, 1])
            pr_folds.append(float(average_precision_score(y[va_idx], p1)))
            roc_folds.append(float(roc_auc_score(y[va_idx], p1)))
            brier_folds.append(float(brier_score_loss(y[va_idx], p1)))

        rows.append(
            {
                "variante_datos": variant_label,
                "var_smoothing": float(vs),
                "alpha_fijo": float(alpha_opt),
                "prior_fijo": prior_mode,
                "pr_auc_cv_media": round(float(np.mean(pr_folds)), 5),
                "pr_auc_cv_std": round(float(np.std(pr_folds)), 5),
                "roc_auc_cv_media": round(float(np.mean(roc_folds)), 5),
                "roc_auc_cv_std": round(float(np.std(roc_folds)), 5),
                "brier_cv_media": round(float(np.mean(brier_folds)), 4),
            }
        )
    return pd.DataFrame(rows)


class OutlierDiagnosticsAnalyzer:
    """Measure skewness, kurtosis, Tukey extremes, Gaussian fit quality, and outlier sensitivity in A."""

    def __init__(self, config: NaiveBayesConfig) -> None:
        self.config = config

    @staticmethod
    def _compute_metrics(
        y_true: np.ndarray,
        y_prob: np.ndarray,
        threshold: float = 0.5,
    ) -> Dict[str, float]:
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

    def run_diagnostics(
        self,
        train_blocks: NaiveBayesPartitionBlocks,
        test_blocks: NaiveBayesPartitionBlocks,
        orig_train: pd.DataFrame | None = None,
    ) -> OutlierDiagnosticsBundle:
        """Execute full Gaussian diagnostics and train/test extreme-value sensitivity inside Version A."""
        dense_tr = train_blocks.dense_clean_df
        dense_te = test_blocks.dense_clean_df
        y_tr = train_blocks.y
        y_te = test_blocks.y

        n_tr = len(y_tr)
        n_te = len(y_te)
        any_extreme_train = np.zeros(n_tr, dtype=bool)
        any_extreme_test = np.zeros(n_te, dtype=bool)

        dist_rows: List[Dict[str, object]] = []
        tukey_bounds_rob: Dict[str, Tuple[float, float]] = {}

        for col_rob in CONTINUOUS_ROB_FEATURES:
            col_orig = CONTINUOUS_TO_ORIGINAL_COL[col_rob]
            arr_tr = dense_tr[col_rob].to_numpy(dtype=np.float64)
            arr_te = dense_te[col_rob].to_numpy(dtype=np.float64)

            q1_rob, med_rob, q3_rob = np.percentile(arr_tr, [25.0, 50.0, 75.0])
            iqr_rob = q3_rob - q1_rob
            low_rob = float(q1_rob - 1.5 * iqr_rob)
            high_rob = float(q3_rob + 1.5 * iqr_rob)
            tukey_bounds_rob[col_rob] = (low_rob, high_rob)

            if orig_train is not None and col_orig in orig_train.columns:
                orig_arr = orig_train[col_orig].to_numpy(dtype=np.float64)
                q1_o, med_o, q3_o = np.percentile(orig_arr, [25.0, 50.0, 75.0])
                iqr_o = q3_o - q1_o
                low_orig = float(q1_o - 1.5 * iqr_o)
                high_orig = float(q3_o + 1.5 * iqr_o)
                max_orig = float(np.max(orig_arr))
            else:
                med_o, low_orig, high_orig, max_orig = np.nan, np.nan, np.nan, np.nan

            std_val = float(np.std(arr_tr))
            if std_val < 1e-12:
                skew_val = 0.0
                kurt_val = 0.0
                mask_ext_tr = np.zeros(n_tr, dtype=bool)
                mask_ext_te = np.zeros(n_te, dtype=bool)
            else:
                skew_val = float(stats.skew(arr_tr, bias=False))
                kurt_val = float(stats.kurtosis(arr_tr, fisher=True, bias=False))
                mask_ext_tr = (arr_tr < low_rob) | (arr_tr > high_rob)
                mask_ext_te = (arr_te < low_rob) | (arr_te > high_rob)
                any_extreme_train |= mask_ext_tr
                any_extreme_test |= mask_ext_te

            n_ext_tr = int(mask_ext_tr.sum())
            pct_ext_tr = 100.0 * n_ext_tr / float(n_tr)

            dist_rows.append(
                {
                    "variable_rob": col_rob,
                    "variable_original": col_orig,
                    "descripcion_es": ORIGINAL_COL_LABELS_ES.get(col_orig, col_rob),
                    "mediana_original_train": round(med_o, 2) if not np.isnan(med_o) else np.nan,
                    "max_original_train": round(max_orig, 2) if not np.isnan(max_orig) else np.nan,
                    "valla_inf_tukey_orig": round(low_orig, 2) if not np.isnan(low_orig) else np.nan,
                    "valla_sup_tukey_orig": round(high_orig, 2) if not np.isnan(high_orig) else np.nan,
                    "valla_inf_tukey_rob": round(low_rob, 4),
                    "valla_sup_tukey_rob": round(high_rob, 4),
                    "asimetria_skewness_train": round(skew_val, 4),
                    "curtosis_exceso_train": round(kurt_val, 4),
                    "filas_fuera_tukey_train": n_ext_tr,
                    "pct_fuera_tukey_train": round(pct_ext_tr, 2),
                }
            )

        distribution_table = pd.DataFrame(dist_rows)

        # Fit GaussianNB on full train and on inlier-only train to inspect parameter shifts and curves
        inlier_tr_mask = ~any_extreme_train
        inlier_te_mask = ~any_extreme_test
        extreme_te_mask = any_extreme_test

        gnb_all = build_gaussian_nb(var_smoothing=1e-9)
        gnb_all.fit(train_blocks.X_nb_g, y_tr)

        gnb_inlier = build_gaussian_nb(var_smoothing=1e-9)
        gnb_inlier.fit(train_blocks.X_nb_g[inlier_tr_mask], y_tr[inlier_tr_mask])

        # Build histogram + Gaussian curve overlay data for each non-constant continuous column
        hist_curves: List[GaussianFitHistogramData] = []
        param_shift_rows: List[Dict[str, object]] = []
        nb_g_col_to_idx = {name: i for i, name in enumerate(train_blocks.nb_g_feature_names)}

        mask_tr_c0 = y_tr == 0
        mask_tr_c1 = y_tr == 1

        for col_rob in CONTINUOUS_ROB_FEATURES:
            idx = nb_g_col_to_idx[col_rob]
            col_orig = CONTINUOUS_TO_ORIGINAL_COL[col_rob]
            arr_tr = train_blocks.X_nb_g[:, idx].astype(np.float64)

            t0_all = float(gnb_all.theta_[0, idx])
            t1_all = float(gnb_all.theta_[1, idx])
            s0_all = float(np.sqrt(gnb_all.var_[0, idx]))
            s1_all = float(np.sqrt(gnb_all.var_[1, idx]))

            t0_in = float(gnb_inlier.theta_[0, idx])
            t1_in = float(gnb_inlier.theta_[1, idx])
            s0_in = float(np.sqrt(gnb_inlier.var_[0, idx]))
            s1_in = float(np.sqrt(gnb_inlier.var_[1, idx]))

            param_shift_rows.append(
                {
                    "variable_rob": col_rob,
                    "media_c0_train_completo": round(t0_all, 4),
                    "media_c0_sin_extremos": round(t0_in, 4),
                    "media_c1_train_completo": round(t1_all, 4),
                    "media_c1_sin_extremos": round(t1_in, 4),
                    "std_c0_train_completo": round(s0_all, 4),
                    "std_c0_sin_extremos": round(s0_in, 4),
                    "std_c1_train_completo": round(s1_all, 4),
                    "std_c1_sin_extremos": round(s1_in, 4),
                    "razon_varianza_completo_vs_inliers_c1": round(
                        (s1_all**2) / max(s1_in**2, 1e-12), 2
                    ),
                    "razon_std_completo_vs_inliers_c1": round(
                        s1_all / max(s1_in, 1e-12), 2
                    ),
                }
            )

            if np.std(arr_tr) < 1e-12:
                continue

            # Clip display range to [P0.5, P99.5] so histogram and fitted Gaussian are legible
            p_low, p_high = np.percentile(arr_tr, [0.5, 99.5])
            low_t, high_t = tukey_bounds_rob[col_rob]
            disp_min = min(float(p_low), low_t)
            disp_max = max(float(p_high), high_t)
            if disp_max <= disp_min:
                disp_max = disp_min + 1.0

            bins = np.linspace(disp_min, disp_max, 45)
            centers = 0.5 * (bins[:-1] + bins[1:])
            h0, _ = np.histogram(
                np.clip(arr_tr[mask_tr_c0], disp_min, disp_max), bins=bins, density=True
            )
            h1, _ = np.histogram(
                np.clip(arr_tr[mask_tr_c1], disp_min, disp_max), bins=bins, density=True
            )

            x_grid = np.linspace(disp_min, disp_max, 200)
            pdf_c0 = stats.norm.pdf(x_grid, loc=t0_all, scale=max(s0_all, 1e-6))
            pdf_c1 = stats.norm.pdf(x_grid, loc=t1_all, scale=max(s1_all, 1e-6))

            pct_out = float(
                distribution_table.loc[
                    distribution_table["variable_rob"] == col_rob, "pct_fuera_tukey_train"
                ].iloc[0]
            )
            hist_curves.append(
                GaussianFitHistogramData(
                    feature_rob=col_rob,
                    feature_orig=col_orig,
                    label_es=ORIGINAL_COL_LABELS_ES.get(col_orig, col_rob),
                    bin_centers=centers,
                    hist_density_c0=h0,
                    hist_density_c1=h1,
                    x_grid=x_grid,
                    gauss_pdf_c0=pdf_c0,
                    gauss_pdf_c1=pdf_c1,
                    theta_c0=t0_all,
                    theta_c1=t1_all,
                    std_c0=s0_all,
                    std_c1=s1_all,
                    tukey_low=low_t,
                    tukey_high=high_t,
                    pct_outside_tukey=pct_out,
                )
            )

        parameter_shift_table = pd.DataFrame(param_shift_rows)

        # Also fit HybridNaiveBayes on full train vs inlier-only train
        hnb_all = HybridNaiveBayes(
            continuous_idx=train_blocks.continuous_idx,
            binary_idx=train_blocks.binary_idx,
            var_smoothing=1e-9,
            alpha=1.0,
        )
        hnb_all.fit(train_blocks.X_nb_h, y_tr)

        hnb_inlier = HybridNaiveBayes(
            continuous_idx=train_blocks.continuous_idx,
            binary_idx=train_blocks.binary_idx,
            var_smoothing=1e-9,
            alpha=1.0,
        )
        hnb_inlier.fit(train_blocks.X_nb_h[inlier_tr_mask], y_tr[inlier_tr_mask])

        # Evaluate NB-G and NB-H under both training regimes across the 3 test subsets
        eval_subsets = [
            ("Test completo (A)", np.ones(n_te, dtype=bool)),
            ("Test sin extremos Tukey", inlier_te_mask),
            ("Test con extremos Tukey", extreme_te_mask),
        ]
        model_regimes = [
            (MODEL_NB_G, "a) Entrenado en Train completo", gnb_all, test_blocks.X_nb_g),
            (MODEL_NB_G, "b) Entrenado en Train sin extremos Tukey", gnb_inlier, test_blocks.X_nb_g),
            (MODEL_NB_H, "a) Entrenado en Train completo", hnb_all, test_blocks.X_nb_h),
            (MODEL_NB_H, "b) Entrenado en Train sin extremos Tukey", hnb_inlier, test_blocks.X_nb_h),
        ]

        sens_rows: List[Dict[str, object]] = []
        nb_g_untuned_test_probs: np.ndarray | None = None
        for model_id, train_regime, fitted_est, X_te_full in model_regimes:
            probs_full = fitted_est.predict_proba(X_te_full)[:, 1]
            if model_id == MODEL_NB_G and train_regime.startswith("a)"):
                nb_g_untuned_test_probs = probs_full
            for subset_label, mask_sub in eval_subsets:
                y_sub = y_te[mask_sub]
                p_sub = probs_full[mask_sub]
                m = self._compute_metrics(y_sub, p_sub, threshold=0.5)
                sens_rows.append(
                    {
                        "regimen_hiperparametros": "Sin ajustar (var_smoothing=1e-9, umbral=0.50)",
                        "modelo": model_id,
                        "regimen_entrenamiento": train_regime,
                        "subconjunto_evaluacion_test": subset_label,
                        "n_filas_test": int(mask_sub.sum()),
                        "prevalencia_test_pct": round(float(y_sub.mean() * 100.0), 2),
                        "pr_auc": round(m["pr_auc"], 4),
                        "roc_auc": round(m["roc_auc"], 4),
                        "f1_clase_1": round(m["f1_pos"], 4),
                        "recall_clase_1": round(m["recall_pos"], 4),
                        "precision_clase_1": round(m["precision_pos"], 4),
                        "brier": round(m["brier"], 4),
                        "accuracy": round(m["accuracy"], 4),
                    }
                )

        sensitivity_experiment_table = pd.DataFrame(sens_rows)

        assert nb_g_untuned_test_probs is not None
        pct_nbg_lt_005 = round(100.0 * float(np.mean(nb_g_untuned_test_probs < 0.05)), 2)
        pct_nbg_gt_095 = round(100.0 * float(np.mean(nb_g_untuned_test_probs > 0.95)), 2)
        pct_nbg_ext = round(
            100.0 * float(np.mean((nb_g_untuned_test_probs < 0.05) | (nb_g_untuned_test_probs > 0.95))),
            2,
        )

        subset_summary = {
            "n_train_total": int(n_tr),
            "n_train_inliers": int(inlier_tr_mask.sum()),
            "n_train_extremes": int(any_extreme_train.sum()),
            "pct_train_extremes": round(100.0 * float(any_extreme_train.mean()), 2),
            "prevalencia_train_inliers_pct": round(
                100.0 * float(y_tr[inlier_tr_mask].mean()), 2
            ),
            "prevalencia_train_extremes_pct": round(
                100.0 * float(y_tr[any_extreme_train].mean()), 2
            ),
            "n_test_total": int(n_te),
            "n_test_inliers": int(inlier_te_mask.sum()),
            "n_test_extremes": int(extreme_te_mask.sum()),
            "pct_test_extremes": round(100.0 * float(extreme_te_mask.mean()), 2),
            "prevalencia_test_inliers_pct": round(
                100.0 * float(y_te[inlier_te_mask].mean()), 2
            ),
            "prevalencia_test_extremes_pct": round(
                100.0 * float(y_te[extreme_te_mask].mean()), 2
            ),
            "nb_g_sin_ajustar_pct_prob_lt_005_test": pct_nbg_lt_005,
            "nb_g_sin_ajustar_pct_prob_gt_095_test": pct_nbg_gt_095,
            "nb_g_sin_ajustar_pct_prob_extremos_test": pct_nbg_ext,
        }

        version_b_bounds_df = build_version_b_bounds_table()

        return OutlierDiagnosticsBundle(
            version_b_bounds_table=version_b_bounds_df,
            distribution_table=distribution_table,
            parameter_shift_table=parameter_shift_table,
            sensitivity_experiment_table=sensitivity_experiment_table,
            subset_summary=subset_summary,
            histogram_curves=hist_curves,
        )

    @staticmethod
    def _compute_tukey_extreme_masks(
        train_blocks: NaiveBayesPartitionBlocks,
        test_blocks: NaiveBayesPartitionBlocks,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Compute row-level Tukey extreme masks on train and test using fences fitted on train only."""
        dense_tr = train_blocks.dense_clean_df
        dense_te = test_blocks.dense_clean_df
        any_tr = np.zeros(len(train_blocks.y), dtype=bool)
        any_te = np.zeros(len(test_blocks.y), dtype=bool)
        for col_rob in CONTINUOUS_ROB_FEATURES:
            arr_tr = dense_tr[col_rob].to_numpy(dtype=np.float64)
            if float(np.std(arr_tr)) < 1e-12:
                continue
            arr_te = dense_te[col_rob].to_numpy(dtype=np.float64)
            q1, q3 = np.percentile(arr_tr, [25.0, 75.0])
            iqr = q3 - q1
            low_f = float(q1 - 1.5 * iqr)
            high_f = float(q3 + 1.5 * iqr)
            any_tr |= (arr_tr < low_f) | (arr_tr > high_f)
            any_te |= (arr_te < low_f) | (arr_te > high_f)
        return any_tr, any_te

    def _oof_proba_for_estimator(
        self,
        X: sparse.spmatrix | np.ndarray,
        y: np.ndarray,
        groups: np.ndarray,
        factory: object,
    ) -> np.ndarray:
        """Compute grouped 5-fold OOF positive-class probabilities for an estimator factory."""
        sgkf = StratifiedGroupKFold(
            n_splits=self.config.cv_folds,
            shuffle=True,
            random_state=self.config.random_state,
        )
        oof = np.zeros(len(y), dtype=np.float64)
        for tr_idx, va_idx in sgkf.split(X, y, groups):
            est = factory()  # type: ignore[operator]
            est.fit(X[tr_idx], y[tr_idx])
            oof[va_idx] = est.predict_proba(X[va_idx])[:, 1]
        return oof

    def run_tuned_outlier_experiments(
        self,
        train_blocks: NaiveBayesPartitionBlocks,
        test_blocks: NaiveBayesPartitionBlocks,
        tuned_models: Dict[str, TunedModelArtifact],
    ) -> TunedOutlierExperimentsBundle:
        """Execute E1 (tuned row-exclusion), E2 (in-RAM Tukey winsorization), and E3 (A & A-wins CV grid)."""
        y_tr = train_blocks.y
        y_te = test_blocks.y
        groups_tr = train_blocks.groups
        groups_te = test_blocks.groups

        any_ext_tr, any_ext_te = self._compute_tukey_extreme_masks(train_blocks, test_blocks)
        inlier_tr_mask = ~any_ext_tr
        inlier_te_mask = ~any_ext_te
        eval_subsets = [
            ("Test completo (A)", np.ones(len(y_te), dtype=bool)),
            ("Test sin extremos Tukey", inlier_te_mask),
            ("Test con extremos Tukey", any_ext_te),
        ]

        art_g = tuned_models[MODEL_NB_G]
        art_h = tuned_models[MODEL_NB_H]
        vs_g = float(art_g.best_params["var_smoothing"])
        pm_g = str(art_g.best_params["prior_mode"])
        vs_h = float(art_h.best_params["var_smoothing"])
        alpha_h = float(art_h.best_params["alpha"])
        pm_h = str(art_h.best_params["prior_mode"])

        def _make_nb_g() -> GaussianNB:
            return build_gaussian_nb(var_smoothing=vs_g, priors=pm_g)

        def _make_nb_h() -> HybridNaiveBayes:
            return HybridNaiveBayes(
                continuous_idx=train_blocks.continuous_idx,
                binary_idx=train_blocks.binary_idx,
                var_smoothing=vs_h,
                alpha=alpha_h,
                priors=pm_h,
            )

        # ---- E1: Tuned sensitivity (full train vs train without Tukey-extreme rows) ----
        y_tr_in = y_tr[inlier_tr_mask]
        g_tr_in = groups_tr[inlier_tr_mask]

        oof_g_in = self._oof_proba_for_estimator(
            train_blocks.X_nb_g[inlier_tr_mask], y_tr_in, g_tr_in, _make_nb_g
        )
        tau_g_in, _ = select_oof_threshold_from_proba(y_tr_in, oof_g_in)
        est_g_in = _make_nb_g()
        est_g_in.fit(train_blocks.X_nb_g[inlier_tr_mask], y_tr_in)
        prob_g_in_te = est_g_in.predict_proba(test_blocks.X_nb_g)[:, 1]

        oof_h_in = self._oof_proba_for_estimator(
            train_blocks.X_nb_h[inlier_tr_mask], y_tr_in, g_tr_in, _make_nb_h
        )
        tau_h_in, _ = select_oof_threshold_from_proba(y_tr_in, oof_h_in)
        est_h_in = _make_nb_h()
        est_h_in.fit(train_blocks.X_nb_h[inlier_tr_mask], y_tr_in)
        prob_h_in_te = est_h_in.predict_proba(test_blocks.X_nb_h)[:, 1]

        e1_specs = [
            (
                MODEL_NB_G,
                f"Ajustado (vs={vs_g:g}, prior={pm_g})",
                "a) Entrenado en Train completo",
                art_g.test_proba,
                art_g.oof_threshold_tau,
            ),
            (
                MODEL_NB_G,
                f"Ajustado (vs={vs_g:g}, prior={pm_g})",
                "b) Entrenado en Train sin extremos Tukey",
                prob_g_in_te,
                tau_g_in,
            ),
            (
                MODEL_NB_H,
                f"Ajustado (vs={vs_h:g}, alpha={alpha_h:g}, prior={pm_h})",
                "a) Entrenado en Train completo",
                art_h.test_proba,
                art_h.oof_threshold_tau,
            ),
            (
                MODEL_NB_H,
                f"Ajustado (vs={vs_h:g}, alpha={alpha_h:g}, prior={pm_h})",
                "b) Entrenado en Train sin extremos Tukey",
                prob_h_in_te,
                tau_h_in,
            ),
        ]

        e1_rows: List[Dict[str, object]] = []
        for mid, hp_desc, tr_regime, probs_full, tau_val in e1_specs:
            for sub_lbl, m_sub in eval_subsets:
                y_sub = y_te[m_sub]
                p_sub = probs_full[m_sub]
                m = compute_classification_metrics(y_sub, p_sub, threshold=tau_val)
                e1_rows.append(
                    {
                        "regimen_hiperparametros": hp_desc,
                        "modelo": mid,
                        "regimen_entrenamiento": tr_regime,
                        "umbral_oof_tau": round(float(tau_val), 4),
                        "subconjunto_evaluacion_test": sub_lbl,
                        "n_filas_test": int(m_sub.sum()),
                        "pr_auc": round(m["pr_auc"], 4),
                        "roc_auc": round(m["roc_auc"], 4),
                        "f1_clase_1": round(m["f1_pos"], 4),
                        "recall_clase_1": round(m["recall_pos"], 4),
                        "precision_clase_1": round(m["precision_pos"], 4),
                        "brier": round(m["brier"], 4),
                        "accuracy": round(m["accuracy"], 4),
                    }
                )
        e1_df = pd.DataFrame(e1_rows)

        # ---- E2: In-RAM Tukey winsorization of all 7 continuous columns (train fences only) ----
        X_g_tr_w, X_g_te_w, X_h_tr_w, X_h_te_w, fences_df = winsorize_continuous_blocks_in_ram(
            train_blocks, test_blocks
        )

        oof_g_w = self._oof_proba_for_estimator(X_g_tr_w, y_tr, groups_tr, _make_nb_g)
        tau_g_w, _ = select_oof_threshold_from_proba(y_tr, oof_g_w)
        est_g_w = _make_nb_g()
        est_g_w.fit(X_g_tr_w, y_tr)
        prob_g_w_te = est_g_w.predict_proba(X_g_te_w)[:, 1]

        oof_h_w = self._oof_proba_for_estimator(X_h_tr_w, y_tr, groups_tr, _make_nb_h)
        tau_h_w, _ = select_oof_threshold_from_proba(y_tr, oof_h_w)
        est_h_w = _make_nb_h()
        est_h_w.fit(X_h_tr_w, y_tr)
        prob_h_w_te = est_h_w.predict_proba(X_h_te_w)[:, 1]

        e2_rows: List[Dict[str, object]] = []
        e2_paired_rows: List[Dict[str, object]] = []
        for mid, art_ref, prob_w, tau_w in [
            (MODEL_NB_G, art_g, prob_g_w_te, tau_g_w),
            (MODEL_NB_H, art_h, prob_h_w_te, tau_h_w),
        ]:
            for var_lbl, p_vec, tau_v in [
                ("Versión A · original (sin recortar las 7 continuas)", art_ref.test_proba, art_ref.oof_threshold_tau),
                ("Versión A winsorizada en RAM (7 continuas · E2)", prob_w, tau_w),
            ]:
                m = compute_classification_metrics(y_te, p_vec, threshold=tau_v)
                ci = bootstrap_person_metrics(
                    y_true=y_te,
                    y_prob=p_vec,
                    groups=groups_te,
                    threshold=tau_v,
                    n_resamples=self.config.bootstrap_resamples,
                    random_state=self.config.random_state,
                )
                e2_rows.append(
                    {
                        "modelo_id": mid,
                        "variante_datos": var_lbl,
                        "umbral_oof_tau": round(float(tau_v), 4),
                        "pr_auc_test": round(m["pr_auc"], 4),
                        "pr_auc_ic95": f"[{ci['pr_auc'][0]:.4f}, {ci['pr_auc'][1]:.4f}]",
                        "roc_auc_test": round(m["roc_auc"], 4),
                        "roc_auc_ic95": f"[{ci['roc_auc'][0]:.4f}, {ci['roc_auc'][1]:.4f}]",
                        "f1_clase_1_test": round(m["f1_pos"], 4),
                        "recall_clase_1_test": round(m["recall_pos"], 4),
                        "precision_clase_1_test": round(m["precision_pos"], 4),
                        "brier_test": round(m["brier"], 4),
                        "accuracy_test": round(m["accuracy"], 4),
                    }
                )

            p_res = paired_bootstrap_person_diffs(
                y_true=y_te,
                prob_a=prob_w,
                prob_b=art_ref.test_proba,
                groups=groups_te,
                threshold_a=tau_w,
                threshold_b=art_ref.oof_threshold_tau,
                n_resamples=self.config.bootstrap_resamples,
                random_state=self.config.random_state,
            )
            e2_paired_rows.append(
                {
                    "modelo_id": mid,
                    "comparacion": "A winsorizada (7 continuas · E2) menos A original",
                    "delta_pr_auc": round(float(p_res["delta_pr_auc"]), 4),
                    "ic95_delta_pr_auc": f"[{float(p_res['delta_pr_auc_ci_low']):+.4f}, {float(p_res['delta_pr_auc_ci_high']):+.4f}]",
                    "pr_auc_excluye_cero": bool(p_res["pr_auc_excluye_cero"]),
                    "veredicto_pr_auc": str(p_res["veredicto_pr_auc"]),
                    "delta_roc_auc": round(float(p_res["delta_roc_auc"]), 4),
                    "ic95_delta_roc_auc": f"[{float(p_res['delta_roc_auc_ci_low']):+.4f}, {float(p_res['delta_roc_auc_ci_high']):+.4f}]",
                    "roc_auc_excluye_cero": bool(p_res["roc_auc_excluye_cero"]),
                    "veredicto_roc_auc": str(p_res["veredicto_roc_auc"]),
                    "delta_f1_oof": round(float(p_res["delta_f1"]), 4),
                    "ic95_delta_f1_oof": f"[{float(p_res['delta_f1_ci_low']):+.4f}, {float(p_res['delta_f1_ci_high']):+.4f}]",
                }
            )

        # ---- E3 (Version A and Version A winsorized): NB-H across Section 6 var_smoothing grid ----
        X_g10_a = np.ascontiguousarray(
            train_blocks.dense_clean_df[list(GAUSSIAN_HYBRID_FEATURES)].to_numpy(dtype=np.float32)
        )
        X_g10_w = np.ascontiguousarray(
            X_h_tr_w[:, list(train_blocks.continuous_idx)].toarray(), dtype=np.float32
        )

        e3_a = evaluate_nb_h_vs_grid_cv(
            X_g10=X_g10_a,
            X_b2971=train_blocks.X_nb_b,
            y=y_tr,
            groups=groups_tr,
            var_smoothing_grid=self.config.var_smoothing_grid,
            alpha_opt=alpha_h,
            prior_mode=pm_h,
            variant_label="A · Original (con outliers)",
            cv_folds=self.config.cv_folds,
            random_state=self.config.random_state,
        )
        e3_w = evaluate_nb_h_vs_grid_cv(
            X_g10=X_g10_w,
            X_b2971=train_blocks.X_nb_b,
            y=y_tr,
            groups=groups_tr,
            var_smoothing_grid=self.config.var_smoothing_grid,
            alpha_opt=alpha_h,
            prior_mode=pm_h,
            variant_label="A winsorizada (7 continuas · E2)",
            cv_folds=self.config.cv_folds,
            random_state=self.config.random_state,
        )
        e3_partial_df = pd.concat([e3_a, e3_w], ignore_index=True)

        return TunedOutlierExperimentsBundle(
            e1_tuned_sensitivity_table=e1_df,
            e2_tukey_fences_table=fences_df,
            e2_winsorization_table=pd.DataFrame(e2_rows),
            e2_paired_diff_table=pd.DataFrame(e2_paired_rows),
            e3_partial_a_and_wins_table=e3_partial_df,
        )
