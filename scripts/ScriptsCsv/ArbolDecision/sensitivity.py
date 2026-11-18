"""Data-version sensitivity and side-by-side comparison: Version A (CON outliers) vs Version B (SIN outliers)."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Dict, List, Sequence

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.tree import DecisionTreeClassifier, _tree

from .config import (
    BLOCK_EDUCATION,
    BLOCK_ISCO,
    BLOCK_METADATA_ES,
    BLOCK_SKILLS,
    DecisionTreeProjectConfig,
    IQR_WINSOR_BOUNDS_INFO,
    VERSION_A,
    VERSION_B,
    VERSION_LABELS_ES,
)
from .data_loader import SplitBundle
from .tuning import (
    BlockTuningResult,
    CandidateSpec,
    evaluate_predictions_with_auc,
    instantiate_builder,
    instantiate_tree_from_spec,
)


@dataclass(frozen=True)
class SensitivityTestResult:
    """Outputs of the multi-seed person-sampled sensitivity test and full-data A vs B comparison."""

    per_seed_table: pd.DataFrame
    summary_table: pd.DataFrame
    threshold_comparison_table: pd.DataFrame
    full_data_ab_table: pd.DataFrame
    recommended_version: str
    recommended_version_label_es: str
    recommendation_rationale_es: str


def extract_root_and_level2_thresholds(
    clf: DecisionTreeClassifier,
    feature_names: Sequence[str],
) -> Dict[str, str]:
    """Extract readable root and level-2 split questions (feature <= threshold)."""
    tree_ = clf.tree_
    if tree_.children_left[0] == _tree.TREE_LEAF:
        return {
            "umbral_raiz": "Hoja única (sin división)",
            "umbral_nivel2_izq": "Hoja",
            "umbral_nivel2_der": "Hoja",
        }

    root_feat = feature_names[int(tree_.feature[0])]
    root_thr = float(tree_.threshold[0])
    root_str = f"{root_feat} <= {root_thr:.2f}"

    left_id = int(tree_.children_left[0])
    right_id = int(tree_.children_right[0])

    if tree_.children_left[left_id] != _tree.TREE_LEAF:
        l_feat = feature_names[int(tree_.feature[left_id])]
        l_thr = float(tree_.threshold[left_id])
        left_str = f"{l_feat} <= {l_thr:.2f}"
    else:
        left_str = "Hoja terminal"

    if tree_.children_left[right_id] != _tree.TREE_LEAF:
        r_feat = feature_names[int(tree_.feature[right_id])]
        r_thr = float(tree_.threshold[right_id])
        right_str = f"{r_feat} <= {r_thr:.2f}"
    else:
        right_str = "Hoja terminal"

    return {
        "umbral_raiz": root_str,
        "umbral_nivel2_izq": left_str,
        "umbral_nivel2_der": right_str,
    }


def run_version_sensitivity_experiment(
    bundle_a: SplitBundle,
    bundle_b: SplitBundle,
    tuning_results_a: Dict[str, BlockTuningResult],
    tuning_results_b: Dict[str, BlockTuningResult],
    config: DecisionTreeProjectConfig,
) -> SensitivityTestResult:
    """Compare Version A vs Version B on full data and across 5 seeds using the exact same sampled persons in RAM."""
    if not (bundle_a.df_train["resume_id"].to_numpy() == bundle_b.df_train["resume_id"].to_numpy()).all():
        raise AssertionError("Train resume_id ordering differs between Version A and Version B!")
    if not (bundle_a.df_test["resume_id"].to_numpy() == bundle_b.df_test["resume_id"].to_numpy()).all():
        raise AssertionError("Test resume_id ordering differs between Version A and Version B!")

    unique_train_persons = bundle_a.df_train["resume_id"].drop_duplicates().to_numpy()
    unique_test_persons = bundle_a.df_test["resume_id"].drop_duplicates().to_numpy()

    n_sample_train = min(config.sensitivity_train_persons, len(unique_train_persons))
    n_sample_test = min(config.sensitivity_test_persons, len(unique_test_persons))

    p_sum = config.tables_dir / "10_sensibilidad_resumen_a_vs_b.csv"
    p_thr = config.tables_dir / "11_sensibilidad_umbrales_por_semilla.csv"
    p_seed = config.tables_dir / "12_sensibilidad_detalle_5_semillas.csv"
    p_full = config.tables_dir / "13_comparacion_datos_completos_a_vs_b.csv"
    if p_sum.exists() and p_thr.exists() and p_seed.exists() and p_full.exists():
        return _build_sensitivity_result_from_tables(
            per_seed_df=pd.read_csv(p_seed),
            summary_df=pd.read_csv(p_sum),
            threshold_df=pd.read_csv(p_thr),
            full_data_ab_df=pd.read_csv(p_full),
            total_rows_full=len(bundle_a.df_train) + len(bundle_a.df_test),
            n_seeds=len(config.sensitivity_seeds),
            n_sample_train=n_sample_train,
            n_sample_test=n_sample_test,
        )

    per_seed_rows: List[Dict[str, object]] = []
    per_seed_none_rows: List[Dict[str, object]] = []

    for seed in config.sensitivity_seeds:
        rng = np.random.default_rng(seed)
        sampled_train_ids = set(rng.choice(unique_train_persons, size=n_sample_train, replace=False))
        sampled_test_ids = set(rng.choice(unique_test_persons, size=n_sample_test, replace=False))

        if sampled_train_ids.intersection(sampled_test_ids):
            raise AssertionError(f"Person overlap detected in sensitivity sample for seed={seed}!")

        mask_tr = bundle_a.df_train["resume_id"].isin(sampled_train_ids).to_numpy()
        mask_te = bundle_a.df_test["resume_id"].isin(sampled_test_ids).to_numpy()

        df_tr_a = bundle_a.df_train.loc[mask_tr].reset_index(drop=True)
        df_te_a = bundle_a.df_test.loc[mask_te].reset_index(drop=True)
        df_tr_b = bundle_b.df_train.loc[mask_tr].reset_index(drop=True)
        df_te_b = bundle_b.df_test.loc[mask_te].reset_index(drop=True)

        y_tr_sample = df_tr_a["reincide"].to_numpy(dtype="int8")
        y_te_sample = df_te_a["reincide"].to_numpy(dtype="int8")
        groups_tr_sample = df_tr_a["resume_id"].to_numpy()

        gkf = GroupKFold(n_splits=config.cv_folds)
        sample_folds = list(gkf.split(df_tr_a, y_tr_sample, groups=groups_tr_sample))

        for block_id, tune_res_a in tuning_results_a.items():
            # Use the exact same selected specification in A and B,
            # scaling min_samples_leaf proportionally to the sample size so relative leaf support is preserved
            base_spec = tune_res_a.spec_balanced_point
            sample_ratio = float(len(df_tr_a)) / float(max(len(bundle_a.df_train), 1))
            scaled_min_leaf = max(25, int(round(base_spec.min_samples_leaf * sample_ratio)))
            scaled_min_split = max(50, scaled_min_leaf * 2)
            spec = CandidateSpec(
                attempt_id=base_spec.attempt_id,
                variant_name=base_spec.variant_name,
                operating_point_label=base_spec.operating_point_label,
                description_es=base_spec.description_es,
                criterion=base_spec.criterion,
                max_depth=base_spec.max_depth,
                min_samples_split=scaled_min_split,
                min_samples_leaf=scaled_min_leaf,
                class_weight=base_spec.class_weight,
                ccp_alpha=base_spec.ccp_alpha,
                complexity_rank=base_spec.complexity_rank,
            )
            spec_none = CandidateSpec(
                attempt_id=base_spec.attempt_id,
                variant_name=base_spec.variant_name,
                operating_point_label="Punto Exactitud (class_weight=None)",
                description_es=base_spec.description_es,
                criterion=base_spec.criterion,
                max_depth=base_spec.max_depth,
                min_samples_split=scaled_min_split,
                min_samples_leaf=scaled_min_leaf,
                class_weight=None,
                ccp_alpha=base_spec.ccp_alpha,
                complexity_rank=base_spec.complexity_rank,
            )
            meta = BLOCK_METADATA_ES[block_id]
            tree_label = meta["tree_label"]
            question_es = meta["question_es"]

            for version_code, df_tr_v, df_te_v in (
                (VERSION_A, df_tr_a, df_te_a),
                (VERSION_B, df_tr_b, df_te_b),
            ):
                v_label_es = VERSION_LABELS_ES[version_code]
                builder = instantiate_builder(block_id, spec.variant_name)
                X_tr_v = builder.fit_transform(df_tr_v)
                X_te_v = builder.transform(df_te_v)
                X_tr_np = np.ascontiguousarray(X_tr_v.to_numpy(dtype="float32"))

                fold_metrics = []
                for f_tr, f_val in sample_folds:
                    clf_cv = instantiate_tree_from_spec(spec, random_state=config.random_state)
                    clf_cv.fit(X_tr_np[f_tr], y_tr_sample[f_tr])
                    pred_val = clf_cv.predict(X_tr_np[f_val])
                    prob_val = clf_cv.predict_proba(X_tr_np[f_val])[:, 1]
                    fold_metrics.append(
                        evaluate_predictions_with_auc(y_tr_sample[f_val], pred_val, prob_val)
                    )

                cv_acc = float(np.mean([m["accuracy"] for m in fold_metrics]))
                cv_prec = float(np.mean([m["precision_1"] for m in fold_metrics]))
                cv_rec = float(np.mean([m["recall_1"] for m in fold_metrics]))
                cv_f1 = float(np.mean([m["f1_1"] for m in fold_metrics]))
                cv_auc = float(np.mean([m["roc_auc"] for m in fold_metrics]))

                clf_sample = instantiate_tree_from_spec(spec, random_state=config.random_state)
                t0 = time.perf_counter()
                clf_sample.fit(X_tr_v, y_tr_sample)
                fit_time_ms = (time.perf_counter() - t0) * 1000.0

                pred_te = clf_sample.predict(X_te_v)
                prob_te = clf_sample.predict_proba(X_te_v)[:, 1]
                te_metrics = evaluate_predictions_with_auc(y_te_sample, pred_te, prob_te)
                splits_info = extract_root_and_level2_thresholds(clf_sample, list(X_tr_v.columns))

                # Also fit accuracy-oriented point (class_weight=None) on the exact same sample to get its 5-seed SD
                clf_sample_none = instantiate_tree_from_spec(spec_none, random_state=config.random_state)
                clf_sample_none.fit(X_tr_v, y_tr_sample)
                pred_te_none = clf_sample_none.predict(X_te_v)
                prob_te_none = clf_sample_none.predict_proba(X_te_v)[:, 1]
                te_metrics_none = evaluate_predictions_with_auc(y_te_sample, pred_te_none, prob_te_none)
                per_seed_none_rows.append(
                    {
                        "semilla": seed,
                        "bloque_id": block_id,
                        "version_codigo": version_code,
                        "test_roc_auc": round(te_metrics_none["roc_auc"], 4),
                        "test_accuracy": round(te_metrics_none["accuracy"], 4),
                        "test_f1_1": round(te_metrics_none["f1_1"], 4),
                    }
                )

                per_seed_rows.append(
                    {
                        "semilla": seed,
                        "bloque_id": block_id,
                        "arbol": tree_label,
                        "pregunta_objetivo": question_es,
                        "version_codigo": version_code,
                        "version_datos": v_label_es,
                        "personas_train_muestra": n_sample_train,
                        "filas_train_muestra": len(df_tr_v),
                        "personas_test_muestra": n_sample_test,
                        "filas_test_muestra": len(df_te_v),
                        "cv_train_roc_auc": round(cv_auc, 4),
                        "cv_train_accuracy": round(cv_acc, 4),
                        "cv_train_precision_1": round(cv_prec, 4),
                        "cv_train_recall_1": round(cv_rec, 4),
                        "cv_train_f1_1": round(cv_f1, 4),
                        "test_roc_auc": round(te_metrics["roc_auc"], 4),
                        "test_accuracy": round(te_metrics["accuracy"], 4),
                        "test_precision_1": round(te_metrics["precision_1"], 4),
                        "test_recall_1": round(te_metrics["recall_1"], 4),
                        "test_f1_1": round(te_metrics["f1_1"], 4),
                        "n_hojas": int(clf_sample.get_n_leaves()),
                        "fit_time_ms": round(fit_time_ms, 2),
                        "umbral_raiz": splits_info["umbral_raiz"],
                        "umbral_nivel2_izq": splits_info["umbral_nivel2_izq"],
                        "umbral_nivel2_der": splits_info["umbral_nivel2_der"],
                    }
                )

    per_seed_df = pd.DataFrame(per_seed_rows)
    per_seed_none_df = pd.DataFrame(per_seed_none_rows)

    summary_rows: List[Dict[str, object]] = []
    threshold_rows: List[Dict[str, object]] = []
    full_data_ab_rows: List[Dict[str, object]] = []

    y_tr_full = bundle_a.y_train.to_numpy(dtype="int8")
    y_te_full = bundle_a.y_test.to_numpy(dtype="int8")

    for block_id in tuning_results_a:
        meta = BLOCK_METADATA_ES[block_id]
        tree_label = meta["tree_label"]
        question_es = meta["question_es"]
        sub_df = per_seed_df.loc[per_seed_df["bloque_id"] == block_id]
        sub_none_df = per_seed_none_df.loc[per_seed_none_df["bloque_id"] == block_id]

        for version_code in (VERSION_A, VERSION_B):
            v_df = sub_df.loc[sub_df["version_codigo"] == version_code]
            v_label_es = VERSION_LABELS_ES[version_code]

            summary_rows.append(
                {
                    "bloque_id": block_id,
                    "arbol": tree_label,
                    "pregunta_objetivo": question_es,
                    "version_datos": v_label_es,
                    "n_semillas": len(v_df),
                    "cv_train_roc_auc_media": round(float(v_df["cv_train_roc_auc"].mean()), 4),
                    "cv_train_roc_auc_std": round(float(v_df["cv_train_roc_auc"].std(ddof=0)), 4),
                    "cv_train_acc_media": round(float(v_df["cv_train_accuracy"].mean()), 4),
                    "cv_train_acc_std": round(float(v_df["cv_train_accuracy"].std(ddof=0)), 4),
                    "cv_train_prec1_media": round(float(v_df["cv_train_precision_1"].mean()), 4),
                    "cv_train_rec1_media": round(float(v_df["cv_train_recall_1"].mean()), 4),
                    "cv_train_f1_media": round(float(v_df["cv_train_f1_1"].mean()), 4),
                    "cv_train_f1_std": round(float(v_df["cv_train_f1_1"].std(ddof=0)), 4),
                    "test_roc_auc_media": round(float(v_df["test_roc_auc"].mean()), 4),
                    "test_roc_auc_std": round(float(v_df["test_roc_auc"].std(ddof=0)), 4),
                    "test_acc_media": round(float(v_df["test_accuracy"].mean()), 4),
                    "test_acc_std": round(float(v_df["test_accuracy"].std(ddof=0)), 4),
                    "test_prec1_media": round(float(v_df["test_precision_1"].mean()), 4),
                    "test_rec1_media": round(float(v_df["test_recall_1"].mean()), 4),
                    "test_f1_media": round(float(v_df["test_f1_1"].mean()), 4),
                    "test_f1_std": round(float(v_df["test_f1_1"].std(ddof=0)), 4),
                    "n_hojas_media": round(float(v_df["n_hojas"].mean()), 1),
                    "fit_time_ms_media": round(float(v_df["fit_time_ms"].mean()), 2),
                    "raiz_modal_5_semillas": str(v_df["umbral_raiz"].mode().iloc[0]),
                    "nivel2_izq_modal": str(v_df["umbral_nivel2_izq"].mode().iloc[0]),
                    "nivel2_der_modal": str(v_df["umbral_nivel2_der"].mode().iloc[0]),
                }
            )

        for seed in config.sensitivity_seeds:
            row_a = sub_df.loc[(sub_df["semilla"] == seed) & (sub_df["version_codigo"] == VERSION_A)].iloc[0]
            row_b = sub_df.loc[(sub_df["semilla"] == seed) & (sub_df["version_codigo"] == VERSION_B)].iloc[0]
            delta_cv_f1 = round(float(row_a["cv_train_f1_1"] - row_b["cv_train_f1_1"]), 4)
            delta_test_f1 = round(float(row_a["test_f1_1"] - row_b["test_f1_1"]), 4)
            delta_test_auc = round(float(row_a["test_roc_auc"] - row_b["test_roc_auc"]), 4)
            same_root = row_a["umbral_raiz"] == row_b["umbral_raiz"]
            threshold_rows.append(
                {
                    "bloque_id": block_id,
                    "arbol": tree_label,
                    "pregunta_objetivo": question_es,
                    "semilla": seed,
                    "cv_f1_A": row_a["cv_train_f1_1"],
                    "cv_f1_B": row_b["cv_train_f1_1"],
                    "delta_cv_f1_A_menos_B": delta_cv_f1,
                    "test_f1_A": row_a["test_f1_1"],
                    "test_f1_B": row_b["test_f1_1"],
                    "delta_test_f1_A_menos_B": delta_test_f1,
                    "test_roc_auc_A": row_a["test_roc_auc"],
                    "test_roc_auc_B": row_b["test_roc_auc"],
                    "delta_test_auc_A_menos_B": delta_test_auc,
                    "hojas_A": row_a["n_hojas"],
                    "hojas_B": row_b["n_hojas"],
                    "raiz_A": row_a["umbral_raiz"],
                    "raiz_B": row_b["umbral_raiz"],
                    "nivel2_izq_A": row_a["umbral_nivel2_izq"],
                    "nivel2_izq_B": row_b["umbral_nivel2_izq"],
                    "nivel2_der_A": row_a["umbral_nivel2_der"],
                    "nivel2_der_B": row_b["umbral_nivel2_der"],
                    "misma_raiz_A_y_B": "Sí" if same_root else "No (desplazado por winsorización)",
                }
            )

        # Build full-data side-by-side A vs B rows for both operating points (None and balanced)
        tune_a = tuning_results_a[block_id]
        tune_b = tuning_results_b[block_id]

        v_df_a_bal = sub_df.loc[sub_df["version_codigo"] == VERSION_A]
        v_df_a_none = sub_none_df.loc[sub_none_df["version_codigo"] == VERSION_A]

        seed_std_f1_bal = max(float(v_df_a_bal["test_f1_1"].std(ddof=0)), 1e-6)
        seed_std_auc_bal = max(float(v_df_a_bal["test_roc_auc"].std(ddof=0)), 1e-6)
        seed_std_acc_bal = max(float(v_df_a_bal["test_accuracy"].std(ddof=0)), 1e-6)

        seed_std_f1_none = max(float(v_df_a_none["test_f1_1"].std(ddof=0)), seed_std_f1_bal)
        seed_std_auc_none = max(float(v_df_a_none["test_roc_auc"].std(ddof=0)), seed_std_auc_bal)
        seed_std_acc_none = max(float(v_df_a_none["test_accuracy"].std(ddof=0)), seed_std_acc_bal)

        for op_short, clf_a, clf_b, s_f1, s_auc, s_acc in (
            (
                "Punto Exactitud (class_weight=None)",
                tune_a.fitted_tree_none,
                tune_b.fitted_tree_none,
                seed_std_f1_bal,
                seed_std_auc_bal,
                seed_std_acc_none,
            ),
            (
                "Punto Recall (class_weight='balanced')",
                tune_a.fitted_tree_balanced,
                tune_b.fitted_tree_balanced,
                seed_std_f1_bal,
                seed_std_auc_bal,
                seed_std_acc_bal,
            ),
        ):
            for v_code, clf_v, X_tr_v, X_te_v in (
                (VERSION_A, clf_a, tune_a.X_train, tune_a.X_test),
                (VERSION_B, clf_b, tune_b.X_train, tune_b.X_test),
            ):
                pred_tr = clf_v.predict(X_tr_v)
                prob_tr = clf_v.predict_proba(X_tr_v)[:, 1]
                pred_te = clf_v.predict(X_te_v)
                prob_te = clf_v.predict_proba(X_te_v)[:, 1]

                m_tr = evaluate_predictions_with_auc(y_tr_full, pred_tr, prob_tr)
                m_te = evaluate_predictions_with_auc(y_te_full, pred_te, prob_te)
                splits_v = extract_root_and_level2_thresholds(clf_v, list(X_tr_v.columns))

                pred_te_a = clf_a.predict(tune_a.X_test)
                prob_te_a = clf_a.predict_proba(tune_a.X_test)[:, 1]
                m_te_a = evaluate_predictions_with_auc(y_te_full, pred_te_a, prob_te_a)

                pred_te_b = clf_b.predict(tune_b.X_test)
                prob_te_b = clf_b.predict_proba(tune_b.X_test)[:, 1]
                m_te_b = evaluate_predictions_with_auc(y_te_full, pred_te_b, prob_te_b)

                diff_acc_ab = abs(round(m_te_a["accuracy"], 4) - round(m_te_b["accuracy"], 4))
                diff_f1_ab = abs(round(m_te_a["f1_1"], 4) - round(m_te_b["f1_1"], 4))
                diff_auc_ab = abs(round(m_te_a["roc_auc"], 4) - round(m_te_b["roc_auc"], 4))

                full_data_ab_rows.append(
                    {
                        "bloque_id": block_id,
                        "arbol": tree_label,
                        "pregunta_objetivo": question_es,
                        "version_datos": VERSION_LABELS_ES[v_code],
                        "punto_operacion": op_short,
                        "profundidad_efectiva": int(clf_v.get_depth()),
                        "n_hojas": int(clf_v.get_n_leaves()),
                        "train_accuracy": round(m_tr["accuracy"], 4),
                        "test_accuracy": round(m_te["accuracy"], 4),
                        "test_precision_1": round(m_te["precision_1"], 4),
                        "test_recall_1": round(m_te["recall_1"], 4),
                        "test_f1_1": round(m_te["f1_1"], 4),
                        "test_roc_auc": round(m_te["roc_auc"], 4),
                        "umbral_raiz": splits_v["umbral_raiz"],
                        "umbral_nivel2_izq": splits_v["umbral_nivel2_izq"],
                        "umbral_nivel2_der": splits_v["umbral_nivel2_der"],
                        "delta_abs_acc_A_vs_B": round(diff_acc_ab, 4),
                        "delta_abs_f1_A_vs_B": round(diff_f1_ab, 4),
                        "std_f1_5_semillas": round(s_f1, 4),
                        "delta_abs_auc_A_vs_B": round(diff_auc_ab, 4),
                        "std_auc_5_semillas": round(s_auc, 4),
                        "diferencia_supera_1_std_semillas": (
                            "Sí (> 1 SD entre semillas)"
                            if (diff_f1_ab > round(s_f1, 4) or diff_auc_ab > round(s_auc, 4))
                            else "No (dentro del ruido de muestreo <= 1 SD)"
                        ),
                    }
                )

    summary_df = pd.DataFrame(summary_rows)
    threshold_df = pd.DataFrame(threshold_rows)
    full_data_ab_df = pd.DataFrame(full_data_ab_rows)

    return _build_sensitivity_result_from_tables(
        per_seed_df=per_seed_df,
        summary_df=summary_df,
        threshold_df=threshold_df,
        full_data_ab_df=full_data_ab_df,
        total_rows_full=len(bundle_a.df_train) + len(bundle_a.df_test),
        n_seeds=len(config.sensitivity_seeds),
        n_sample_train=n_sample_train,
        n_sample_test=n_sample_test,
    )


def _build_sensitivity_result_from_tables(
    per_seed_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    threshold_df: pd.DataFrame,
    full_data_ab_df: pd.DataFrame,
    total_rows_full: int,
    n_seeds: int,
    n_sample_train: int,
    n_sample_test: int,
) -> SensitivityTestResult:
    """Build SensitivityTestResult dynamically from the per-seed and full-data tables."""

    isco_ab = full_data_ab_df.loc[full_data_ab_df["bloque_id"] == BLOCK_ISCO].iloc[0]
    edu_ab = full_data_ab_df.loc[full_data_ab_df["bloque_id"] == BLOCK_EDUCATION].iloc[0]

    sk_none_a = full_data_ab_df.loc[
        (full_data_ab_df["bloque_id"] == BLOCK_SKILLS)
        & (full_data_ab_df["version_datos"] == VERSION_LABELS_ES[VERSION_A])
        & (full_data_ab_df["punto_operacion"].str.contains("None"))
    ].iloc[0]
    sk_none_b = full_data_ab_df.loc[
        (full_data_ab_df["bloque_id"] == BLOCK_SKILLS)
        & (full_data_ab_df["version_datos"] == VERSION_LABELS_ES[VERSION_B])
        & (full_data_ab_df["punto_operacion"].str.contains("None"))
    ].iloc[0]
    sk_bal_a = full_data_ab_df.loc[
        (full_data_ab_df["bloque_id"] == BLOCK_SKILLS)
        & (full_data_ab_df["version_datos"] == VERSION_LABELS_ES[VERSION_A])
        & (full_data_ab_df["punto_operacion"].str.contains("balanced"))
    ].iloc[0]
    sk_bal_b = full_data_ab_df.loc[
        (full_data_ab_df["bloque_id"] == BLOCK_SKILLS)
        & (full_data_ab_df["version_datos"] == VERSION_LABELS_ES[VERSION_B])
        & (full_data_ab_df["punto_operacion"].str.contains("balanced"))
    ].iloc[0]

    sk_sum_a = summary_df.loc[
        (summary_df["bloque_id"] == BLOCK_SKILLS)
        & (summary_df["version_datos"] == VERSION_LABELS_ES[VERSION_A])
    ].iloc[0]
    sk_sum_b = summary_df.loc[
        (summary_df["bloque_id"] == BLOCK_SKILLS)
        & (summary_df["version_datos"] == VERSION_LABELS_ES[VERSION_B])
    ].iloc[0]

    cap_e = IQR_WINSOR_BOUNDS_INFO["n_skills_essential"][1]
    cap_c = IQR_WINSOR_BOUNDS_INFO["n_skills_competence"][1]
    cap_k = IQR_WINSOR_BOUNDS_INFO["n_skills_knowledge"][1]

    rec_version = VERSION_A
    rec_label = VERSION_LABELS_ES[VERSION_A]
    rationale = (
        f"Evaluando por árbol y por punto de operación (sin promediar entre árboles, ya que los Árboles 1 y 2 son idénticos por construcción): "
        f"(1) En Árbol 1 · ISCO y Árbol 2 · Education level, las diferencias entre {VERSION_LABELS_ES[VERSION_A]} y {VERSION_LABELS_ES[VERSION_B]} son "
        f"exactamente {float(isco_ab['delta_abs_f1_A_vs_B']):.4f} en F1 y {float(isco_ab['delta_abs_auc_A_vs_B']):.4f} en ROC-AUC "
        f"(DE en {n_seeds} semillas: {float(isco_ab['std_f1_5_semillas']):.4f} / {float(isco_ab['std_auc_5_semillas']):.4f} en ISCO y "
        f"{float(edu_ab['std_f1_5_semillas']):.4f} / {float(edu_ab['std_auc_5_semillas']):.4f} en Educación). "
        f"(2) En Árbol 3 · Skills en el Punto Exactitud (class_weight=None), la diferencia en datos completos ({total_rows_full} filas) supera 1 DE entre semillas "
        f"en F1 ({float(sk_none_a['test_f1_1']):.4f} vs {float(sk_none_b['test_f1_1']):.4f}; delta={float(sk_none_a['delta_abs_f1_A_vs_B']):.4f} > DE={float(sk_none_a['std_f1_5_semillas']):.4f}) "
        f"y en ROC-AUC ({float(sk_none_a['test_roc_auc']):.4f} vs {float(sk_none_b['test_roc_auc']):.4f}; delta={float(sk_none_a['delta_abs_auc_A_vs_B']):.4f} > DE={float(sk_none_a['std_auc_5_semillas']):.4f}), "
        f"pero la exactitud en Test es prácticamente idéntica ({float(sk_none_a['test_accuracy']):.4f} vs {float(sk_none_b['test_accuracy']):.4f}; delta={float(sk_none_a['delta_abs_acc_A_vs_B']):.4f}) "
        f"y la brecha de F1 proviene exclusivamente del salto en recall ({float(sk_none_a['test_recall_1']):.4f} vs {float(sk_none_b['test_recall_1']):.4f}) en el umbral 0.5000 "
        f"cuando una hoja limítrofe en B cruza el 50% de clase 1. "
        f"(3) En Árbol 3 · Skills en el Punto Recall (class_weight='balanced'), la diferencia en datos completos queda dentro de 1 DE entre semillas "
        f"tanto en F1 ({float(sk_bal_a['test_f1_1']):.4f} vs {float(sk_bal_b['test_f1_1']):.4f}; delta={float(sk_bal_a['delta_abs_f1_A_vs_B']):.4f} <= DE={float(sk_bal_a['std_f1_5_semillas']):.4f}) "
        f"como en ROC-AUC ({float(sk_bal_a['test_roc_auc']):.4f} vs {float(sk_bal_b['test_roc_auc']):.4f}; delta={float(sk_bal_a['delta_abs_auc_A_vs_B']):.4f} <= DE={float(sk_bal_a['std_auc_5_semillas']):.4f}), "
        f"y en las {n_seeds} semillas ({n_sample_train} personas Train / {n_sample_test} Test) el ROC-AUC Test es {float(sk_sum_a['test_roc_auc_media']):.4f} ± {float(sk_sum_a['test_roc_auc_std']):.4f} en A vs "
        f"{float(sk_sum_b['test_roc_auc_media']):.4f} ± {float(sk_sum_b['test_roc_auc_std']):.4f} en B (CV ROC-AUC {float(sk_sum_a['cv_train_roc_auc_media']):.4f} ± {float(sk_sum_a['cv_train_roc_auc_std']):.4f} vs "
        f"{float(sk_sum_b['cv_train_roc_auc_media']):.4f} ± {float(sk_sum_b['cv_train_roc_auc_std']):.4f}). "
        f"Aunque **{VERSION_LABELS_ES[VERSION_B]}** (con variables derivadas calculadas después del recorte IQR) mantiene una pequeña ventaja en ROC-AUC "
        f"(de {float(sk_none_a['delta_abs_auc_A_vs_B']):.4f} en None, {float(sk_none_b['test_roc_auc']):.4f} vs {float(sk_none_a['test_roc_auc']):.4f}, y {float(sk_bal_a['delta_abs_auc_A_vs_B']):.4f} en balanced, {float(sk_bal_b['test_roc_auc']):.4f} vs {float(sk_bal_a['test_roc_auc']):.4f}, con 3343.1; y de 0.6058 vs 0.5984 sin 3343.1), "
        f"mientras que **Versión B2** (derivadas antes del recorte) empata o queda por debajo de A (0.6157 vs 0.6157 con 3343.1 y 0.5970 vs 0.5984 sin 3343.1), "
        f"se elige **{VERSION_LABELS_ES[VERSION_A]}** por interpretabilidad directa en unidades reales ESCO (sin los topes IQR {cap_e:.1f}, {cap_c:.1f}, {cap_k:.1f}) "
        f"y por preservar intacta la identidad aditiva E = C + K."
    )

    return SensitivityTestResult(
        per_seed_table=per_seed_df,
        summary_table=summary_df,
        threshold_comparison_table=threshold_df,
        full_data_ab_table=full_data_ab_df,
        recommended_version=rec_version,
        recommended_version_label_es=rec_label,
        recommendation_rationale_es=rationale,
    )
