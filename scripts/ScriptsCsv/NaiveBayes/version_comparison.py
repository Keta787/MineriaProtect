"""Version A (con_outliers) vs. Version B (sin_outliers) sensitivity comparison for Naive Bayes."""

from __future__ import annotations

from dataclasses import dataclass
import gc
from typing import Dict, List

import numpy as np
import pandas as pd

from .config import (
    GAUSSIAN_HYBRID_FEATURES,
    MODEL_LABELS_ES,
    MODEL_NB_B,
    MODEL_NB_G,
    MODEL_NB_H,
    MODEL_ORDER,
    NaiveBayesConfig,
    VERSION_SIN,
)
from .evaluation import (
    TunedModelArtifact,
    bootstrap_person_metrics,
    compute_classification_metrics,
)
from .feature_blocks import NaiveBayesFeatureBuilder
from .models import HybridNaiveBayes, build_bernoulli_nb, build_gaussian_nb
from .outlier_diagnostics import build_version_b_bounds_table, evaluate_nb_h_vs_grid_cv


@dataclass(frozen=True)
class VersionComparisonBundle:
    """Outputs of Section 12 (Version A vs. Version B outlier sensitivity comparison + E3)."""

    version_b_bounds_table: pd.DataFrame
    comparison_table: pd.DataFrame
    differences_summary_table: pd.DataFrame
    e3_regularization_by_variant_table: pd.DataFrame
    e3_pivot_summary_table: pd.DataFrame
    target_identity_verified: Dict[str, object]


class VersionABComparator:
    """Compare Version A and Version B without hyperparameter re-tuning on B."""

    def __init__(self, config: NaiveBayesConfig, feature_builder: NaiveBayesFeatureBuilder | None = None) -> None:
        self.config = config
        self.feature_builder = feature_builder or NaiveBayesFeatureBuilder(config)

    def run_comparison_after_freeing_a(
        self,
        y_train_a: np.ndarray,
        y_test_a: np.ndarray,
        test_metrics_a_df: pd.DataFrame,
        tuned_models_a: Dict[str, TunedModelArtifact],
        e3_partial_a_and_wins_df: pd.DataFrame | None = None,
    ) -> VersionComparisonBundle:
        """Build Version B after A has been freed, verify identical y, and evaluate on B's test set."""
        gc.collect()

        # Build Version B without descriptive original-unit DataFrames (not needed in Step 12)
        bundle_b = self.feature_builder.build_version_bundle(
            version=VERSION_SIN,
            include_original_units=False,
        )
        tr_b = bundle_b.train_blocks
        te_b = bundle_b.test_blocks

        # Mandatory assert: Target in A and B must be 100% identical
        same_y_train = bool(np.array_equal(y_train_a, tr_b.y))
        same_y_test = bool(np.array_equal(y_test_a, te_b.y))
        assert same_y_train and same_y_test, (
            f"Target mismatch between Version A and Version B: train={same_y_train}, test={same_y_test}"
        )

        target_verification = {
            "y_train_identico_A_vs_B": same_y_train,
            "y_test_identico_A_vs_B": same_y_test,
            "filas_train_B": int(len(tr_b.y)),
            "filas_test_B": int(len(te_b.y)),
            "prevalencia_train_B_pct": round(100.0 * float(tr_b.y.mean()), 2),
            "prevalencia_test_B_pct": round(100.0 * float(te_b.y.mean()), 2),
        }

        comp_rows: List[Dict[str, object]] = []
        diff_rows: List[Dict[str, object]] = []

        for model_id in MODEL_ORDER:
            art_a = tuned_models_a[model_id]
            tau_a = art_a.oof_threshold_tau
            best_params = art_a.best_params

            # Extract Version A row at tau*
            row_a = test_metrics_a_df.loc[
                (test_metrics_a_df["modelo_id"] == model_id)
                & (test_metrics_a_df["punto_operacion"].str.contains("OOF"))
            ].iloc[0]

            comp_rows.append(
                {
                    "modelo_id": model_id,
                    "modelo": MODEL_LABELS_ES[model_id],
                    "version_evaluada": "Versión A · CON outliers (Referencia)",
                    "esquema_ajuste": "Entrenado en Train A · Evaluado en Test A",
                    "umbral_fijo_de_A": round(tau_a, 4),
                    "pr_auc_test": float(row_a["pr_auc_test"]),
                    "pr_auc_ic95": str(row_a["pr_auc_ic95"]),
                    "roc_auc_test": float(row_a["roc_auc_test"]),
                    "roc_auc_ic95": str(row_a["roc_auc_ic95"]),
                    "f1_clase_1_test": float(row_a["f1_clase_1_test"]),
                    "f1_clase_1_ic95": str(row_a["f1_clase_1_ic95"]),
                    "recall_clase_1_test": float(row_a["recall_clase_1_test"]),
                    "precision_clase_1_test": float(row_a["precision_clase_1_test"]),
                    "balanced_acc_test": float(row_a["balanced_acc_test"]),
                    "brier_test": float(row_a["brier_test"]),
                    "accuracy_test": float(row_a["accuracy_test"]),
                }
            )

            if model_id == MODEL_NB_G:
                X_tr_b, X_te_b = tr_b.X_nb_g, te_b.X_nb_g
                est_b = build_gaussian_nb(
                    var_smoothing=float(best_params["var_smoothing"]),
                    priors=str(best_params["prior_mode"]),
                )
            elif model_id == MODEL_NB_B:
                X_tr_b, X_te_b = tr_b.X_nb_b, te_b.X_nb_b
                est_b = build_bernoulli_nb(
                    alpha=float(best_params["alpha"]),
                    priors=str(best_params["prior_mode"]),
                )
            else:
                X_tr_b, X_te_b = tr_b.X_nb_h, te_b.X_nb_h
                est_b = HybridNaiveBayes(
                    continuous_idx=tr_b.continuous_idx,
                    binary_idx=tr_b.binary_idx,
                    var_smoothing=float(best_params["var_smoothing"]),
                    alpha=float(best_params["alpha"]),
                    priors=str(best_params["prior_mode"]),
                )

            # 1. Direct evaluation of estimator fitted on A applied to Test B (zero refitting)
            prob_b_direct = art_a.fitted_estimator.predict_proba(X_te_b)[:, 1]  # type: ignore[attr-defined]
            m_b_direct = compute_classification_metrics(te_b.y, prob_b_direct, threshold=tau_a)
            ci_b_direct = bootstrap_person_metrics(
                y_true=te_b.y,
                y_prob=prob_b_direct,
                groups=te_b.groups,
                threshold=tau_a,
                n_resamples=self.config.bootstrap_resamples,
                random_state=self.config.random_state,
            )

            comp_rows.append(
                {
                    "modelo_id": model_id,
                    "modelo": MODEL_LABELS_ES[model_id],
                    "version_evaluada": "Versión B · SIN outliers (Sin reajuste)",
                    "esquema_ajuste": "Parámetros de Train A evaluados directamente en Test B",
                    "umbral_fijo_de_A": round(tau_a, 4),
                    "pr_auc_test": round(m_b_direct["pr_auc"], 4),
                    "pr_auc_ic95": f"[{ci_b_direct['pr_auc'][0]:.4f}, {ci_b_direct['pr_auc'][1]:.4f}]",
                    "roc_auc_test": round(m_b_direct["roc_auc"], 4),
                    "roc_auc_ic95": f"[{ci_b_direct['roc_auc'][0]:.4f}, {ci_b_direct['roc_auc'][1]:.4f}]",
                    "f1_clase_1_test": round(m_b_direct["f1_pos"], 4),
                    "f1_clase_1_ic95": f"[{ci_b_direct['f1_pos'][0]:.4f}, {ci_b_direct['f1_pos'][1]:.4f}]",
                    "recall_clase_1_test": round(m_b_direct["recall_pos"], 4),
                    "precision_clase_1_test": round(m_b_direct["precision_pos"], 4),
                    "balanced_acc_test": round(m_b_direct["balanced_acc"], 4),
                    "brier_test": round(m_b_direct["brier"], 4),
                    "accuracy_test": round(m_b_direct["accuracy"], 4),
                }
            )

            # 2. Estimator fitted on Train B using fixed hyperparameters and threshold chosen on A
            est_b.fit(X_tr_b, tr_b.y)
            prob_b_refit = est_b.predict_proba(X_te_b)[:, 1]
            m_b_refit = compute_classification_metrics(te_b.y, prob_b_refit, threshold=tau_a)
            ci_b_refit = bootstrap_person_metrics(
                y_true=te_b.y,
                y_prob=prob_b_refit,
                groups=te_b.groups,
                threshold=tau_a,
                n_resamples=self.config.bootstrap_resamples,
                random_state=self.config.random_state,
            )

            comp_rows.append(
                {
                    "modelo_id": model_id,
                    "modelo": MODEL_LABELS_ES[model_id],
                    "version_evaluada": "Versión B · SIN outliers (Hiperparámetros fijos de A)",
                    "esquema_ajuste": "Ajustado en Train B (sin re-tuning) · Evaluado en Test B",
                    "umbral_fijo_de_A": round(tau_a, 4),
                    "pr_auc_test": round(m_b_refit["pr_auc"], 4),
                    "pr_auc_ic95": f"[{ci_b_refit['pr_auc'][0]:.4f}, {ci_b_refit['pr_auc'][1]:.4f}]",
                    "roc_auc_test": round(m_b_refit["roc_auc"], 4),
                    "roc_auc_ic95": f"[{ci_b_refit['roc_auc'][0]:.4f}, {ci_b_refit['roc_auc'][1]:.4f}]",
                    "f1_clase_1_test": round(m_b_refit["f1_pos"], 4),
                    "f1_clase_1_ic95": f"[{ci_b_refit['f1_pos'][0]:.4f}, {ci_b_refit['f1_pos'][1]:.4f}]",
                    "recall_clase_1_test": round(m_b_refit["recall_pos"], 4),
                    "precision_clase_1_test": round(m_b_refit["precision_pos"], 4),
                    "balanced_acc_test": round(m_b_refit["balanced_acc"], 4),
                    "brier_test": round(m_b_refit["brier"], 4),
                    "accuracy_test": round(m_b_refit["accuracy"], 4),
                }
            )

            diff_rows.append(
                {
                    "modelo_id": model_id,
                    "comparacion": "Test B (sin reajuste, pesos de A) menos Test A",
                    "delta_pr_auc": round(m_b_direct["pr_auc"] - float(row_a["pr_auc_test"]), 4),
                    "delta_roc_auc": round(m_b_direct["roc_auc"] - float(row_a["roc_auc_test"]), 4),
                    "delta_f1_clase_1": round(m_b_direct["f1_pos"] - float(row_a["f1_clase_1_test"]), 4),
                    "delta_recall_clase_1": round(
                        m_b_direct["recall_pos"] - float(row_a["recall_clase_1_test"]), 4
                    ),
                    "delta_precision_clase_1": round(
                        m_b_direct["precision_pos"] - float(row_a["precision_clase_1_test"]), 4
                    ),
                    "delta_brier": round(m_b_direct["brier"] - float(row_a["brier_test"]), 4),
                    "delta_accuracy": round(m_b_direct["accuracy"] - float(row_a["accuracy_test"]), 4),
                }
            )
            diff_rows.append(
                {
                    "modelo_id": model_id,
                    "comparacion": "Test B (ajustado en Train B con hiperparámetros fijos de A) menos Test A",
                    "delta_pr_auc": round(m_b_refit["pr_auc"] - float(row_a["pr_auc_test"]), 4),
                    "delta_roc_auc": round(m_b_refit["roc_auc"] - float(row_a["roc_auc_test"]), 4),
                    "delta_f1_clase_1": round(m_b_refit["f1_pos"] - float(row_a["f1_clase_1_test"]), 4),
                    "delta_recall_clase_1": round(
                        m_b_refit["recall_pos"] - float(row_a["recall_clase_1_test"]), 4
                    ),
                    "delta_precision_clase_1": round(
                        m_b_refit["precision_pos"] - float(row_a["precision_clase_1_test"]), 4
                    ),
                    "delta_brier": round(m_b_refit["brier"] - float(row_a["brier_test"]), 4),
                    "delta_accuracy": round(m_b_refit["accuracy"] - float(row_a["accuracy_test"]), 4),
                }
            )

        # ---- E3 (Part B): NB-H across Section 6 var_smoothing grid on Version B ----
        nb_h_art = tuned_models_a[MODEL_NB_H]
        alpha_h = float(nb_h_art.best_params["alpha"])
        pm_h = str(nb_h_art.best_params["prior_mode"])
        X_g10_b = np.ascontiguousarray(
            tr_b.dense_clean_df[list(GAUSSIAN_HYBRID_FEATURES)].to_numpy(dtype=np.float32)
        )
        e3_b_df = evaluate_nb_h_vs_grid_cv(
            X_g10=X_g10_b,
            X_b2971=tr_b.X_nb_b,
            y=tr_b.y,
            groups=tr_b.groups,
            var_smoothing_grid=self.config.var_smoothing_grid,
            alpha_opt=alpha_h,
            prior_mode=pm_h,
            variant_label="B · sin outliers (IQR 4 cols)",
            cv_folds=self.config.cv_folds,
            random_state=self.config.random_state,
        )

        if e3_partial_a_and_wins_df is not None and not e3_partial_a_and_wins_df.empty:
            e3_full_df = pd.concat([e3_partial_a_and_wins_df, e3_b_df], ignore_index=True)
        else:
            e3_full_df = e3_b_df.copy()

        # Build pivot table comparing A, A winsorized (E2), and B across var_smoothing
        piv_rows: List[Dict[str, object]] = []
        lbl_a = "A · Original (con outliers)"
        lbl_w = "A winsorizada (7 continuas · E2)"
        lbl_b = "B · sin outliers (IQR 4 cols)"
        for vs_val in sorted(e3_full_df["var_smoothing"].unique()):
            sub_v = e3_full_df.loc[e3_full_df["var_smoothing"] == vs_val].set_index("variante_datos")
            pr_a = float(sub_v.loc[lbl_a, "pr_auc_cv_media"]) if lbl_a in sub_v.index else np.nan
            pr_w = float(sub_v.loc[lbl_w, "pr_auc_cv_media"]) if lbl_w in sub_v.index else np.nan
            pr_b = float(sub_v.loc[lbl_b, "pr_auc_cv_media"]) if lbl_b in sub_v.index else np.nan
            roc_a = float(sub_v.loc[lbl_a, "roc_auc_cv_media"]) if lbl_a in sub_v.index else np.nan
            roc_w = float(sub_v.loc[lbl_w, "roc_auc_cv_media"]) if lbl_w in sub_v.index else np.nan
            roc_b = float(sub_v.loc[lbl_b, "roc_auc_cv_media"]) if lbl_b in sub_v.index else np.nan
            piv_rows.append(
                {
                    "var_smoothing": float(vs_val),
                    "pr_auc_cv_A": round(pr_a, 5) if not np.isnan(pr_a) else np.nan,
                    "pr_auc_cv_A_wins_E2": round(pr_w, 5) if not np.isnan(pr_w) else np.nan,
                    "pr_auc_cv_B": round(pr_b, 5) if not np.isnan(pr_b) else np.nan,
                    "delta_pr_wins_menos_A": round(pr_w - pr_a, 5)
                    if not (np.isnan(pr_w) or np.isnan(pr_a))
                    else np.nan,
                    "delta_pr_B_menos_A": round(pr_b - pr_a, 5)
                    if not (np.isnan(pr_b) or np.isnan(pr_a))
                    else np.nan,
                    "roc_auc_cv_A": round(roc_a, 5) if not np.isnan(roc_a) else np.nan,
                    "roc_auc_cv_A_wins_E2": round(roc_w, 5) if not np.isnan(roc_w) else np.nan,
                    "roc_auc_cv_B": round(roc_b, 5) if not np.isnan(roc_b) else np.nan,
                    "delta_roc_wins_menos_A": round(roc_w - roc_a, 5)
                    if not (np.isnan(roc_w) or np.isnan(roc_a))
                    else np.nan,
                    "delta_roc_B_menos_A": round(roc_b - roc_a, 5)
                    if not (np.isnan(roc_b) or np.isnan(roc_a))
                    else np.nan,
                }
            )
        e3_pivot_df = pd.DataFrame(piv_rows)

        del bundle_b, tr_b, te_b, X_g10_b
        gc.collect()

        return VersionComparisonBundle(
            version_b_bounds_table=build_version_b_bounds_table(),
            comparison_table=pd.DataFrame(comp_rows),
            differences_summary_table=pd.DataFrame(diff_rows),
            e3_regularization_by_variant_table=e3_full_df,
            e3_pivot_summary_table=e3_pivot_df,
            target_identity_verified=target_verification,
        )
