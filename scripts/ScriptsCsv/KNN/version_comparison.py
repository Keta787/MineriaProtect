"""Section 5: Deep scale, distance-distortion, Tukey winsorization, outlier-free training, and Version B sensitivity."""

from __future__ import annotations

from dataclasses import dataclass
import gc
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from scripts.ScriptsCsv.NaiveBayes.evaluation import (
    compute_classification_metrics,
    paired_bootstrap_person_diffs,
    select_oof_threshold_from_proba,
)

from .config import (
    ALL_DENSE_CLEAN_FEATURES,
    COLLINEAR_REDUNDANT_FEATURES,
    CONTINUOUS_ROB_FEATURES,
    CONTINUOUS_TO_ORIGINAL_COL,
    IQR_WINSOR_BOUNDS_INFO,
    KNNConfig,
    LEAKAGE_FEATURES_IN_X,
    MODEL_KNN_D,
    ORIGINAL_COL_LABELS_ES,
    VERSION_SIN,
)
from .feature_blocks import (
    AuditedStandardBinaryScaler,
    KNNFeatureBuilder,
    KNNPartitionBlocks,
    RawDensePassthroughScaler,
    TukeyWinsorizedStandardScaler,
)
from .models import KNNModelSpec, build_knn_classifier


@dataclass(frozen=True)
class ScaleOutlierSensitivityBundle:
    """All measured tables for Section 5 (scale, extreme values, outlier-free KNN, and Version B)."""

    tukey_extremes_table: pd.DataFrame
    version_b_scope_table: pd.DataFrame
    row_extremes_summary: Dict[str, object]
    distance_distortion_table: pd.DataFrame
    cv_sensitivity_table: pd.DataFrame
    paired_ci_vs_audited_a_table: pd.DataFrame
    outlier_free_subgroup_breakdown_table: pd.DataFrame
    version_b_target_identity: Dict[str, object]
    knn_d_full_test_version_b_table: pd.DataFrame


def build_knn_version_b_scope_table(active_dense_features: Tuple[str, ...]) -> pd.DataFrame:
    """Dynamically describe exactly which columns Version B clips (from IQR_WINSOR_BOUNDS_INFO)."""
    active_set = set(active_dense_features)
    rows: List[Dict[str, object]] = []

    for col_orig, (low_b, high_b) in IQR_WINSOR_BOUNDS_INFO.items():
        col_rob = f"{col_orig}_rob"
        if col_orig == "veces_ese_oficio" or col_rob in LEAKAGE_FEATURES_IN_X:
            enters = "No (excluida por fuga directa 100 %)"
            changes = "No afecta a X en 7.2"
        elif col_rob in COLLINEAR_REDUNDANT_FEATURES or col_orig == "n_skills_competence":
            enters = "No (excluida por colinealidad r = 0.952 con n_skills_essential)"
            changes = "No afecta a X en 7.2"
        elif col_rob in active_set:
            enters = f"Sí (entra como {col_rob})"
            changes = "Sí cambia en X (una de las 2 únicas continuas recortadas en B)"
        else:
            enters = f"No (descartada en auditoría de escala: {col_rob})"
            changes = "No afecta a X en 7.2"

        rows.append(
            {
                "variable_original": col_orig,
                "descripcion_es": ORIGINAL_COL_LABELS_ES.get(col_orig, col_orig),
                "recortada_en_version_B": "Sí (winsorizada con IQR de train)",
                "cota_inf_B": round(float(low_b), 2),
                "cota_sup_B": round(float(high_b), 2),
                "entra_en_X_7_2": enters,
                "efecto_real_en_X_B_vs_A": changes,
            }
        )

    for col_rob in CONTINUOUS_ROB_FEATURES:
        col_orig = CONTINUOUS_TO_ORIGINAL_COL[col_rob]
        if col_orig in IQR_WINSOR_BOUNDS_INFO:
            continue
        in_x = col_rob in active_set
        rows.append(
            {
                "variable_original": col_orig,
                "descripcion_es": ORIGINAL_COL_LABELS_ES.get(col_orig, col_orig),
                "recortada_en_version_B": "No (idéntica en Versión A y Versión B)",
                "cota_inf_B": np.nan,
                "cota_sup_B": np.nan,
                "entra_en_X_7_2": f"Sí (entra como {col_rob})" if in_x else f"No (descartada < 1 %: {col_rob})",
                "efecto_real_en_X_B_vs_A": (
                    "Idéntica entre A y B (colas NO probadas por A vs. B; se prueban con winsorización propia)"
                    if in_x
                    else "Descartada por casi constante"
                ),
            }
        )
    return pd.DataFrame(rows)


class VersionSensitivityAnalyzer:
    """Evaluate KNN-D sensitivity to feature scaling, extreme values (Tukey), outlier-free training, and Version B."""

    def __init__(self, config: KNNConfig, feature_builder: KNNFeatureBuilder | None = None) -> None:
        self.config = config
        self.feature_builder = feature_builder or KNNFeatureBuilder(config)

    @staticmethod
    def compute_tukey_audit(
        dense_train_df: pd.DataFrame,
        dense_test_df: pd.DataFrame,
        y_train: np.ndarray,
        y_test: np.ndarray,
        active_dense_features: Tuple[str, ...],
    ) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray, Dict[str, object]]:
        """Compute train-only Tukey fences, outlier shares, variance inflation, and row-level extreme masks."""
        active_cont = [c for c in CONTINUOUS_ROB_FEATURES if c in set(active_dense_features)]
        n_tr = len(dense_train_df)
        n_te = len(dense_test_df)
        any_ext_tr = np.zeros(n_tr, dtype=bool)
        any_ext_te = np.zeros(n_te, dtype=bool)

        rows: List[Dict[str, object]] = []
        for col in ALL_DENSE_CLEAN_FEATURES:
            arr_tr = dense_train_df[col].to_numpy(dtype=np.float64)
            arr_te = dense_test_df[col].to_numpy(dtype=np.float64)
            q1, med, q3 = np.percentile(arr_tr, [25.0, 50.0, 75.0])
            iqr = float(q3 - q1)
            low_f = float(q1 - 1.5 * iqr)
            high_f = float(q3 + 1.5 * iqr)

            is_cont_active = col in active_cont
            if is_cont_active and iqr > 0.0:
                m_tr = (arr_tr < low_f) | (arr_tr > high_f)
                m_te = (arr_te < low_f) | (arr_te > high_f)
                any_ext_tr |= m_tr
                any_ext_te |= m_te
                std_all = float(np.std(arr_tr))
                std_in = float(np.std(arr_tr[~m_tr])) if np.any(~m_tr) else std_all
                infl_ratio = std_all / max(std_in, 1e-12)
            else:
                m_tr = np.zeros(n_tr, dtype=bool)
                m_te = np.zeros(n_te, dtype=bool)
                std_all = float(np.std(arr_tr))
                std_in = std_all
                infl_ratio = 1.0

            rows.append(
                {
                    "columna": col,
                    "continua_activa_knn": bool(is_cont_active),
                    "valla_inf_tukey_train": round(low_f, 4),
                    "valla_sup_tukey_train": round(high_f, 4),
                    "min_train": round(float(arr_tr.min()), 4),
                    "max_train": round(float(arr_tr.max()), 4),
                    "filas_fuera_tukey_train": int(m_tr.sum()),
                    "pct_fuera_tukey_train": round(100.0 * float(m_tr.mean()), 2),
                    "pct_fuera_tukey_test": round(100.0 * float(m_te.mean()), 2),
                    "std_total_train": round(std_all, 4),
                    "std_sin_extremos_train": round(std_in, 4),
                    "factor_inflacion_std_por_extremos": round(infl_ratio, 3),
                }
            )

        summary = {
            "n_train_total": int(n_tr),
            "n_train_inliers": int((~any_ext_tr).sum()),
            "n_train_extremos_tukey": int(any_ext_tr.sum()),
            "pct_train_extremos_tukey": round(100.0 * float(any_ext_tr.mean()), 2),
            "prevalencia_train_inliers_pct": round(100.0 * float(y_train[~any_ext_tr].mean()), 2),
            "prevalencia_train_extremos_pct": round(100.0 * float(y_train[any_ext_tr].mean()), 2),
            "n_test_extremos_tukey": int(any_ext_te.sum()),
            "pct_test_extremos_tukey": round(100.0 * float(any_ext_te.mean()), 2),
            "prevalencia_test_inliers_pct": round(100.0 * float(y_test[~any_ext_te].mean()), 2),
            "prevalencia_test_extremos_pct": round(100.0 * float(y_test[any_ext_te].mean()), 2),
        }
        return pd.DataFrame(rows), any_ext_tr, any_ext_te, summary

    @staticmethod
    def _measure_distance_distortion(
        dense_sub_a: pd.DataFrame,
        dense_sub_b: pd.DataFrame,
        ext_mask_sub: np.ndarray,
        tr_local: np.ndarray,
        va_local: np.ndarray,
        k_eval: int,
        n_jobs: int,
    ) -> pd.DataFrame:
        """Quantify how scaling and outliers change k-th neighbor distances (inliers vs extremes) & neighbor overlap."""
        # Cap query sample to 8,000 rows from fold 0 validation for fast exact diagnostic
        va_diag = va_local[: min(8000, len(va_local))]
        ext_va = ext_mask_sub[va_diag]
        in_va = ~ext_va

        df_tr_a = dense_sub_a.iloc[tr_local]
        df_va_a = dense_sub_a.iloc[va_diag]
        df_tr_b = dense_sub_b.iloc[tr_local]
        df_va_b = dense_sub_b.iloc[va_diag]

        scalers = {
            "1. A crudo (sin reescalar)": (RawDensePassthroughScaler(1.0), df_tr_a, df_va_a),
            "2. A escalado auditado (Standard + bin 0/1)": (AuditedStandardBinaryScaler(1.0), df_tr_a, df_va_a),
            "3. A winsorizado Tukey (6 continuas · train)": (TukeyWinsorizedStandardScaler(1.0), df_tr_a, df_va_a),
            "4. Versión B (IQR 4 cols) + escalado auditado": (AuditedStandardBinaryScaler(1.0), df_tr_b, df_va_b),
        }

        rows: List[Dict[str, object]] = []
        ref_nn_idx_by_metric: Dict[str, np.ndarray] = {}

        for metric_name in ("euclidean", "manhattan"):
            # Compute reference neighborhoods (Audited Scaled A) first for overlap comparison
            sc_ref = AuditedStandardBinaryScaler(1.0)
            X_tr_ref = sc_ref.fit_transform(df_tr_a)
            X_va_ref = sc_ref.transform(df_va_a)
            knn_ref = build_knn_classifier(
                KNNModelSpec(MODEL_KNN_D, n_neighbors=k_eval, metric=metric_name, algorithm="kd_tree", n_jobs=n_jobs)
            )
            knn_ref.fit(X_tr_ref, np.zeros(len(X_tr_ref), dtype=np.int8))
            _, idx_ref = knn_ref.kneighbors(X_va_ref, n_neighbors=k_eval, return_distance=True)
            ref_nn_idx_by_metric[metric_name] = idx_ref

            for lbl, (sc, d_tr, d_va) in scalers.items():
                X_tr = sc.fit_transform(d_tr)
                X_va = sc.transform(d_va)
                est = build_knn_classifier(
                    KNNModelSpec(MODEL_KNN_D, n_neighbors=k_eval, metric=metric_name, algorithm="kd_tree", n_jobs=n_jobs)
                )
                est.fit(X_tr, np.zeros(len(X_tr), dtype=np.int8))
                dists, idxs = est.kneighbors(X_va, n_neighbors=k_eval, return_distance=True)
                dk = dists[:, -1]

                dk_in = float(np.median(dk[in_va])) if np.any(in_va) else np.nan
                dk_ext = float(np.median(dk[ext_va])) if np.any(ext_va) else np.nan
                ratio_ext_in = dk_ext / max(dk_in, 1e-12)

                # Jaccard/share of top-k neighbors shared with Audited Scaled A
                overlaps = [
                    len(set(idxs[i].tolist()).intersection(idx_ref[i].tolist())) / float(k_eval)
                    for i in range(len(va_diag))
                ]
                mean_overlap_pct = 100.0 * float(np.mean(overlaps))
                ext_overlap_pct = (
                    100.0 * float(np.mean([overlaps[i] for i in range(len(va_diag)) if ext_va[i]]))
                    if np.any(ext_va)
                    else np.nan
                )

                rows.append(
                    {
                        "metrica": metric_name,
                        "tratamiento_datos": lbl,
                        "k_vecinos": int(k_eval),
                        "dist_mediana_dk_inliers": round(dk_in, 4),
                        "dist_mediana_dk_extremos_tukey": round(dk_ext, 4),
                        "razon_distancia_extremos_sobre_inliers": round(ratio_ext_in, 3),
                        "solapamiento_vecinos_vs_A_escalado_total_pct": round(mean_overlap_pct, 2),
                        "solapamiento_vecinos_en_extremos_pct": round(ext_overlap_pct, 2),
                    }
                )
        return pd.DataFrame(rows)

    def run_sensitivity_study(
        self,
        train_blocks_a: KNNPartitionBlocks,
        test_blocks_a: KNNPartitionBlocks,
        tuning_row_idx: np.ndarray,
        knn_d_spec: KNNModelSpec,
    ) -> ScaleOutlierSensitivityBundle:
        """Execute full Section 5 scale, Tukey winsorization, outlier-free KNN, and Version B CV study."""
        # 1. Tukey audit on full train/test Version A
        tukey_df, any_ext_tr_full, _, row_ext_summary = self.compute_tukey_audit(
            dense_train_df=train_blocks_a.dense_clean_df,
            dense_test_df=test_blocks_a.dense_clean_df,
            y_train=train_blocks_a.y,
            y_test=test_blocks_a.y,
            active_dense_features=train_blocks_a.active_dense_features,
        )
        vb_scope_df = build_knn_version_b_scope_table(train_blocks_a.active_dense_features)

        # 2. Load Version B (without original units) to verify target identity and extract dense_clean_df
        bundle_b = self.feature_builder.build_version_bundle(
            version=VERSION_SIN,
            include_original_units=False,
        )
        same_y_tr = bool(np.array_equal(train_blocks_a.y, bundle_b.train_blocks.y))
        same_y_te = bool(np.array_equal(test_blocks_a.y, bundle_b.test_blocks.y))
        if not (same_y_tr and same_y_te):
            raise AssertionError("Target vector y mismatch between Version A and Version B!")
        vb_identity = {
            "y_train_identico_A_vs_B": same_y_tr,
            "y_test_identico_A_vs_B": same_y_te,
            "filas_submuestra_cv": int(len(tuning_row_idx)),
            "personas_submuestra_cv": int(len(np.unique(train_blocks_a.groups[tuning_row_idx]))),
        }

        dense_sub_a = train_blocks_a.dense_clean_df.iloc[tuning_row_idx].reset_index(drop=True)
        dense_sub_b = bundle_b.train_blocks.dense_clean_df.iloc[tuning_row_idx].reset_index(drop=True)
        dense_tr_b_full = bundle_b.train_blocks.dense_clean_df.copy()
        dense_te_b_full = bundle_b.test_blocks.dense_clean_df.copy()
        y_sub = train_blocks_a.y[tuning_row_idx]
        g_sub = train_blocks_a.groups[tuning_row_idx]
        ext_mask_sub = any_ext_tr_full[tuning_row_idx]
        del bundle_b
        gc.collect()

        # Build identical 5 grouped folds on the 10% person tuning subsample
        sgkf = StratifiedGroupKFold(
            n_splits=self.config.cv_folds,
            shuffle=True,
            random_state=self.config.random_state,
        )
        folds = list(sgkf.split(np.zeros((len(y_sub), 1), dtype=np.int8), y_sub, g_sub))

        # 3. Distance distortion diagnostic (Euclidean vs Manhattan on Fold 0)
        dist_distort_df = self._measure_distance_distortion(
            dense_sub_a=dense_sub_a,
            dense_sub_b=dense_sub_b,
            ext_mask_sub=ext_mask_sub,
            tr_local=folds[0][0],
            va_local=folds[0][1],
            k_eval=knn_d_spec.n_neighbors,
            n_jobs=knn_d_spec.n_jobs,
        )

        # 4. Run 5-fold grouped CV for ALL 5 regimes under chosen KNN-D config (plus Euclidean check if winner is Manhattan)
        metrics_to_test = [knn_d_spec.metric]
        other_m = "euclidean" if knn_d_spec.metric == "manhattan" else "manhattan"
        metrics_to_test.append(other_m)

        regimes: List[Tuple[str, str, str, bool]] = [
            ("R1_A_crudo", "1. Versión A cruda (sin reescalar, con outliers)", "A_raw", False),
            ("R2_A_escalado", "2. Versión A escalada auditada (referencia 7.2)", "A_scaled", False),
            ("R3_A_wins_tukey", "3. Versión A winsorizada Tukey (6 continuas en train) + escalada", "A_wins", False),
            ("R4_A_solo_inliers", "4. Versión A entrenada EXCLUSIVAMENTE sin filas con outliers Tukey", "A_inliers_only", True),
            ("R5_B_iqr", "5. Versión B (sin_outliers IQR en 4 cols) + escalada auditada", "B_scaled", False),
        ]

        cv_rows: List[Dict[str, object]] = []
        oof_store: Dict[Tuple[str, str], np.ndarray] = {}
        tau_store: Dict[Tuple[str, str], float] = {}
        breakdown_rows: List[Dict[str, object]] = []

        for metric_name in metrics_to_test:
            role_lbl = "Métrica ganadora KNN-D" if metric_name == knn_d_spec.metric else "Contraste L1/L2"
            for reg_id, reg_label, mode, drop_outliers_in_train in regimes:
                oof_p = np.zeros(len(y_sub), dtype=np.float64)
                fold_pr, fold_roc, fold_brier = [], [], []

                for tr_idx, va_idx in folds:
                    if mode == "B_scaled":
                        df_tr_f = dense_sub_b.iloc[tr_idx]
                        df_va_f = dense_sub_b.iloc[va_idx]
                        scaler = AuditedStandardBinaryScaler(self.config.near_constant_threshold_pct)
                        X_tr_f = scaler.fit_transform(df_tr_f)
                        X_va_f = scaler.transform(df_va_f)
                        y_tr_f = y_sub[tr_idx]
                    elif mode == "A_raw":
                        scaler = RawDensePassthroughScaler(self.config.near_constant_threshold_pct)
                        X_tr_f = scaler.fit_transform(dense_sub_a.iloc[tr_idx])
                        X_va_f = scaler.transform(dense_sub_a.iloc[va_idx])
                        y_tr_f = y_sub[tr_idx]
                    elif mode == "A_wins":
                        scaler = TukeyWinsorizedStandardScaler(self.config.near_constant_threshold_pct)
                        X_tr_f = scaler.fit_transform(dense_sub_a.iloc[tr_idx])
                        X_va_f = scaler.transform(dense_sub_a.iloc[va_idx])
                        y_tr_f = y_sub[tr_idx]
                    elif mode == "A_inliers_only":
                        # Fit train-only Tukey fences inside this fold, exclude extreme rows from train ONLY
                        df_tr_all = dense_sub_a.iloc[tr_idx]
                        active_cont = [c for c in CONTINUOUS_ROB_FEATURES if c in set(train_blocks_a.active_dense_features)]
                        fold_ext = np.zeros(len(tr_idx), dtype=bool)
                        for col in active_cont:
                            vals = df_tr_all[col].to_numpy(dtype=np.float64)
                            q1, q3 = np.percentile(vals, [25.0, 75.0])
                            iqr = float(q3 - q1)
                            if iqr > 0.0:
                                fold_ext |= (vals < q1 - 1.5 * iqr) | (vals > q3 + 1.5 * iqr)
                        keep_in = ~fold_ext
                        scaler = AuditedStandardBinaryScaler(self.config.near_constant_threshold_pct)
                        X_tr_f = scaler.fit_transform(df_tr_all.iloc[keep_in])
                        X_va_f = scaler.transform(dense_sub_a.iloc[va_idx])
                        y_tr_f = y_sub[tr_idx][keep_in]
                    else:
                        scaler = AuditedStandardBinaryScaler(self.config.near_constant_threshold_pct)
                        X_tr_f = scaler.fit_transform(dense_sub_a.iloc[tr_idx])
                        X_va_f = scaler.transform(dense_sub_a.iloc[va_idx])
                        y_tr_f = y_sub[tr_idx]

                    est = build_knn_classifier(
                        KNNModelSpec(
                            model_id=MODEL_KNN_D,
                            n_neighbors=knn_d_spec.n_neighbors,
                            weights=knn_d_spec.weights,
                            metric=metric_name,
                            algorithm=knn_d_spec.algorithm,
                            n_jobs=knn_d_spec.n_jobs,
                        )
                    )
                    est.fit(X_tr_f, y_tr_f)
                    p_va = est.predict_proba(X_va_f)[:, 1]
                    oof_p[va_idx] = p_va
                    m_f = compute_classification_metrics(y_sub[va_idx], p_va, threshold=0.50)
                    fold_pr.append(m_f["pr_auc"])
                    fold_roc.append(m_f["roc_auc"])
                    fold_brier.append(m_f["brier"])

                tau_oof, _ = select_oof_threshold_from_proba(y_sub, oof_p)
                m_all = compute_classification_metrics(y_sub, oof_p, threshold=tau_oof)
                oof_store[(metric_name, reg_id)] = oof_p
                tau_store[(metric_name, reg_id)] = tau_oof

                cv_rows.append(
                    {
                        "rol_metrica": role_lbl,
                        "metrica": metric_name,
                        "regimen_id": reg_id,
                        "regimen_datos": reg_label,
                        "k_vecinos": int(knn_d_spec.n_neighbors),
                        "pesos": knn_d_spec.weights,
                        "umbral_oof_tau": round(tau_oof, 4),
                        "pr_auc_cv_media": round(float(np.mean(fold_pr)), 5),
                        "pr_auc_cv_std": round(float(np.std(fold_pr)), 5),
                        "roc_auc_cv_media": round(float(np.mean(fold_roc)), 5),
                        "roc_auc_cv_std": round(float(np.std(fold_roc)), 5),
                        "f1_oof_tau": round(m_all["f1_pos"], 4),
                        "brier_cv": round(float(np.mean(fold_brier)), 4),
                    }
                )

                # Subgroup breakdown on OOF (Complete vs Inliers vs Tukey Extremes) for winner metric
                if metric_name == knn_d_spec.metric:
                    for sub_lbl, mask_s in [
                        ("Validación OOF completa", np.ones(len(y_sub), dtype=bool)),
                        ("Solo inliers (dentro vallas Tukey)", ~ext_mask_sub),
                        ("Solo extremos Tukey (fuera vallas)", ext_mask_sub),
                    ]:
                        ms = compute_classification_metrics(y_sub[mask_s], oof_p[mask_s], threshold=tau_oof)
                        breakdown_rows.append(
                            {
                                "regimen_id": reg_id,
                                "regimen_datos": reg_label,
                                "subconjunto_oof": sub_lbl,
                                "n_filas_oof": int(mask_s.sum()),
                                "prevalencia_pct": round(100.0 * float(y_sub[mask_s].mean()), 2),
                                "pr_auc_oof": round(ms["pr_auc"], 4),
                                "roc_auc_oof": round(ms["roc_auc"], 4),
                                "f1_oof": round(ms["f1_pos"], 4),
                                "brier_oof": round(ms["brier"], 4),
                            }
                        )

        # 5. Paired person-level bootstrap CIs comparing each regime vs R2 (Audited Scaled A)
        paired_rows: List[Dict[str, object]] = []
        for metric_name in metrics_to_test:
            p_ref = oof_store[(metric_name, "R2_A_escalado")]
            t_ref = tau_store[(metric_name, "R2_A_escalado")]
            for reg_id, reg_label, _, _ in regimes:
                if reg_id == "R2_A_escalado":
                    continue
                res = paired_bootstrap_person_diffs(
                    y_true=y_sub,
                    prob_a=oof_store[(metric_name, reg_id)],
                    prob_b=p_ref,
                    groups=g_sub,
                    threshold_a=tau_store[(metric_name, reg_id)],
                    threshold_b=t_ref,
                    n_resamples=self.config.bootstrap_resamples,
                    random_state=self.config.random_state,
                )
                paired_rows.append(
                    {
                        "metrica": metric_name,
                        "comparacion_A_menos_ref": f"{reg_id} menos R2_A_escalado",
                        "regimen_evaluado": reg_label,
                        "delta_pr_auc": round(float(res["delta_pr_auc"]), 5),
                        "ic95_delta_pr_auc": f"[{float(res['delta_pr_auc_ci_low']):+.5f}, {float(res['delta_pr_auc_ci_high']):+.5f}]",
                        "pr_auc_excluye_cero": bool(res["pr_auc_excluye_cero"]),
                        "veredicto_pr_auc": str(res["veredicto_pr_auc"]),
                        "delta_roc_auc": round(float(res["delta_roc_auc"]), 5),
                        "ic95_delta_roc_auc": f"[{float(res['delta_roc_auc_ci_low']):+.5f}, {float(res['delta_roc_auc_ci_high']):+.5f}]",
                        "veredicto_roc_auc": str(res["veredicto_roc_auc"]),
                        "delta_f1": round(float(res["delta_f1"]), 4),
                        "ic95_delta_f1": f"[{float(res['delta_f1_ci_low']):+.4f}, {float(res['delta_f1_ci_high']):+.4f}]",
                    }
                )

        # 6. Full-test verification for KNN-D (only ~2 min per regime!) across A scaled, A Tukey-winsorized,
        #    A outlier-free train, and Version B (using OOF thresholds from Step 5d; zero test tuning!)
        full_test_rows: List[Dict[str, object]] = []
        y_tr_full = train_blocks_a.y
        y_te_full = test_blocks_a.y
        g_te_full = test_blocks_a.groups
        prob_a_ref_full: np.ndarray | None = None
        tau_a_ref = tau_store[(knn_d_spec.metric, "R2_A_escalado")]

        full_regimes = [
            ("R2_A_escalado", "Versión A escalada auditada (referencia)", "A_scaled"),
            ("R3_A_wins_tukey", "Versión A winsorizada Tukey (6 continuas en train)", "A_wins"),
            ("R4_A_solo_inliers", "Versión A entrenada EXCLUSIVAMENTE sin outliers Tukey", "A_inliers_only"),
            ("R5_B_iqr", "Versión B (sin_outliers IQR en 4 cols) + escalada", "B_scaled"),
        ]
        for reg_id, reg_lbl, mode in full_regimes:
            tau_r = tau_store[(knn_d_spec.metric, reg_id)]
            if mode == "A_scaled":
                X_tr_r = train_blocks_a.X_dense_scaled
                X_te_r = test_blocks_a.X_dense_scaled
                y_tr_r = y_tr_full
            elif mode == "A_wins":
                sc_w = TukeyWinsorizedStandardScaler(self.config.near_constant_threshold_pct)
                X_tr_r = sc_w.fit_transform(train_blocks_a.dense_clean_df)
                X_te_r = sc_w.transform(test_blocks_a.dense_clean_df)
                y_tr_r = y_tr_full
            elif mode == "A_inliers_only":
                keep_in = ~any_ext_tr_full
                sc_i = AuditedStandardBinaryScaler(self.config.near_constant_threshold_pct)
                X_tr_r = sc_i.fit_transform(train_blocks_a.dense_clean_df.iloc[keep_in])
                X_te_r = sc_i.transform(test_blocks_a.dense_clean_df)
                y_tr_r = y_tr_full[keep_in]
            else:
                sc_b = AuditedStandardBinaryScaler(self.config.near_constant_threshold_pct)
                X_tr_r = sc_b.fit_transform(dense_tr_b_full)
                X_te_r = sc_b.transform(dense_te_b_full)
                y_tr_r = y_tr_full

            est_ft = build_knn_classifier(knn_d_spec)
            est_ft.fit(X_tr_r, y_tr_r)
            p_te_r = est_ft.predict_proba(X_te_r)[:, 1]
            m_ft = compute_classification_metrics(y_te_full, p_te_r, threshold=tau_r)

            if prob_a_ref_full is None:
                prob_a_ref_full = p_te_r
                d_pr_str, ci_pr_str, verd_str = 0.0, "Referencia", "Referencia"
            else:
                pr_cmp = paired_bootstrap_person_diffs(
                    y_true=y_te_full,
                    prob_a=p_te_r,
                    prob_b=prob_a_ref_full,
                    groups=g_te_full,
                    threshold_a=tau_r,
                    threshold_b=tau_a_ref,
                    n_resamples=self.config.bootstrap_resamples,
                    random_state=self.config.random_state,
                )
                d_pr_str = round(float(pr_cmp["delta_pr_auc"]), 5)
                ci_pr_str = f"[{float(pr_cmp['delta_pr_auc_ci_low']):+.5f}, {float(pr_cmp['delta_pr_auc_ci_high']):+.5f}]"
                verd_str = str(pr_cmp["veredicto_pr_auc"])

            full_test_rows.append(
                {
                    "modelo_id": MODEL_KNN_D,
                    "muestra": "Test completo (347,720 filas)",
                    "regimen_id": reg_id,
                    "regimen_datos": reg_lbl,
                    "n_train_efectivo": int(len(y_tr_r)),
                    "umbral_oof_tau": round(float(tau_r), 4),
                    "pr_auc_test": round(m_ft["pr_auc"], 4),
                    "delta_pr_auc_vs_A_escalado": d_pr_str,
                    "ic95_pareado_delta_pr": ci_pr_str,
                    "veredicto_pareado": verd_str,
                    "roc_auc_test": round(m_ft["roc_auc"], 4),
                    "f1_test_tau_oof": round(m_ft["f1_pos"], 4),
                    "brier_test": round(m_ft["brier"], 4),
                }
            )
            del est_ft
            gc.collect()

        del dense_tr_b_full, dense_te_b_full
        gc.collect()

        return ScaleOutlierSensitivityBundle(
            tukey_extremes_table=tukey_df,
            version_b_scope_table=vb_scope_df,
            row_extremes_summary=row_ext_summary,
            distance_distortion_table=dist_distort_df,
            cv_sensitivity_table=pd.DataFrame(cv_rows),
            paired_ci_vs_audited_a_table=pd.DataFrame(paired_rows),
            outlier_free_subgroup_breakdown_table=pd.DataFrame(breakdown_rows),
            version_b_target_identity=vb_identity,
            knn_d_full_test_version_b_table=pd.DataFrame(full_test_rows),
        )
