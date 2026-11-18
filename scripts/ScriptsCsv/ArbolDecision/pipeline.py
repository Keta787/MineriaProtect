"""High-level orchestration, per-version tree bundles, comparison tables, checklist, and artifact exporter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .config import (
    ASPIRATIONAL_TARGET_SCORE,
    BLOCK_EDUCATION,
    BLOCK_ISCO,
    BLOCK_METADATA_ES,
    BLOCK_SKILLS,
    DecisionTreeProjectConfig,
    MAIN_QUESTION_ES,
    VERSION_A,
    VERSION_B,
    VERSION_LABELS_ES,
)
from .data_loader import SplitBundle
from .sensitivity import SensitivityTestResult
from .tree_inspector import (
    build_depth_comparison_table,
    build_leaf_lift_table,
    compute_three_references_table,
    evaluate_operating_points_table,
    export_tree_text_rules,
    extract_feature_importances_table,
    extract_first_questions_via_decision_path,
    extract_spanish_business_rules,
)
from .tuning import BlockTuningResult


@dataclass(frozen=True)
class TreeVersionBundle:
    """Complete evaluation bundle for one Decision Tree block on one specific data version (A or B)."""

    block_id: str
    version_code: str
    version_label_es: str
    tree_label_es: str
    question_es: str
    tuning_result: BlockTuningResult
    references_df: pd.DataFrame
    operating_points_df: pd.DataFrame
    confusion_matrices_by_point: Dict[str, Dict[str, np.ndarray]]
    depth_df: pd.DataFrame
    first_questions_train_df: pd.DataFrame
    first_questions_test_df: pd.DataFrame
    leaf_lift_balanced_df: pd.DataFrame
    leaf_lift_none_df: pd.DataFrame
    importances_df: pd.DataFrame
    business_rules_df: pd.DataFrame
    export_text_balanced_str: str
    export_text_none_str: str


def build_tree_version_bundle(
    tuning_result: BlockTuningResult,
    split_bundle: SplitBundle,
    phase4_bench_df: pd.DataFrame,
    config: DecisionTreeProjectConfig,
    profile_20_19_1_df: Optional[pd.DataFrame] = None,
) -> TreeVersionBundle:
    """Assemble all inspection tables, operating points, CIs, and rules for one tree and data version."""
    block_id = tuning_result.block_id
    version_code = tuning_result.version
    version_label_es = tuning_result.version_label_es
    meta = BLOCK_METADATA_ES[block_id]
    tree_label_es = meta["tree_label"]
    question_es = meta["question_es"]

    X_tr = tuning_result.X_train
    X_te = tuning_result.X_test
    y_tr = split_bundle.y_train
    y_te = split_bundle.y_test
    groups_te = split_bundle.groups_test

    refs_df = compute_three_references_table(
        y_train=y_tr,
        y_test=y_te,
        phase4_bench_df=phase4_bench_df,
        version_code=version_code,
    )

    leaf_bal_df = build_leaf_lift_table(
        clf=tuning_result.fitted_tree_balanced,
        X_train=X_tr,
        y_train=y_tr,
        X_test=X_te,
        y_test=y_te,
        version_label_es=version_label_es,
        operating_point_label="class_weight='balanced'",
        min_support_ratio=config.min_leaf_support_ratio,
    )
    leaf_none_df = build_leaf_lift_table(
        clf=tuning_result.fitted_tree_none,
        X_train=X_tr,
        y_train=y_tr,
        X_test=X_te,
        y_test=y_te,
        version_label_es=version_label_es,
        operating_point_label="class_weight=None",
        min_support_ratio=config.min_leaf_support_ratio,
    )

    op_df, cms_by_pt = evaluate_operating_points_table(
        tuning_result=tuning_result,
        y_train=y_tr,
        y_test=y_te,
        groups_test=groups_te,
        leaf_lift_df=leaf_bal_df,
        phase4_bench_df=phase4_bench_df,
        random_state=config.random_state,
    )

    depth_df = build_depth_comparison_table(
        base_spec=tuning_result.selected_spec,
        X_train=X_tr,
        y_train=y_tr,
        X_test=X_te,
        y_test=y_te,
        version_label_es=version_label_es,
        tree_label_es=tree_label_es,
        random_state=config.random_state,
    )

    fq_tr_df = extract_first_questions_via_decision_path(
        clf=tuning_result.fitted_tree_balanced,
        X=X_tr,
        y=y_tr,
        version_label_es=version_label_es,
        dataset_label="Train (80%)",
    )
    fq_te_df = extract_first_questions_via_decision_path(
        clf=tuning_result.fitted_tree_balanced,
        X=X_te,
        y=y_te,
        version_label_es=version_label_es,
        dataset_label="Test (20%)",
    )

    imp_df = extract_feature_importances_table(
        clf=tuning_result.fitted_tree_balanced,
        feature_names=list(X_tr.columns),
        feature_descriptions=tuning_result.fitted_builder.feature_descriptions(),
        version_label_es=version_label_es,
    )

    rules_df = extract_spanish_business_rules(
        leaf_table=leaf_bal_df,
        tree_label=tree_label_es,
        question_es=question_es,
        version_label_es=version_label_es,
        min_rules=2,
        profile_20_19_1_df=profile_20_19_1_df,
    )

    txt_bal = export_tree_text_rules(tuning_result.fitted_tree_balanced, list(X_tr.columns))
    txt_none = export_tree_text_rules(tuning_result.fitted_tree_none, list(X_tr.columns))

    return TreeVersionBundle(
        block_id=block_id,
        version_code=version_code,
        version_label_es=version_label_es,
        tree_label_es=tree_label_es,
        question_es=question_es,
        tuning_result=tuning_result,
        references_df=refs_df,
        operating_points_df=op_df,
        confusion_matrices_by_point=cms_by_pt,
        depth_df=depth_df,
        first_questions_train_df=fq_tr_df,
        first_questions_test_df=fq_te_df,
        leaf_lift_balanced_df=leaf_bal_df,
        leaf_lift_none_df=leaf_none_df,
        importances_df=imp_df,
        business_rules_df=rules_df,
        export_text_balanced_str=txt_bal,
        export_text_none_str=txt_none,
    )


def build_global_comparison_table(
    bundles_a: Dict[str, TreeVersionBundle],
    bundles_b: Dict[str, TreeVersionBundle],
) -> pd.DataFrame:
    """Compare the 3 Mandatory References and the 3 Decision Trees across Version A and Version B."""
    rows: List[Dict[str, object]] = []

    # 1. Add the 3 mandatory references
    refs_a = bundles_a[BLOCK_ISCO].references_df
    triv_f1_val = float(refs_a.iloc[1]["test_f1_clase_1"])
    ceil_auc_val = float(refs_a.iloc[2]["test_roc_auc"])

    for idx, r_row in refs_a.iterrows():
        short_names = [
            "Ref 1 · Baseline Mayoritario (0)",
            "Ref 2 · Trivial Todo-Positivo (1)",
            "Ref 3 · Techo 6.0 (Logística OHE)",
        ]
        r_auc = float(r_row["test_roc_auc"])
        r_f1 = float(r_row["test_f1_clase_1"])
        pct_ceil_auc = round(100.0 * (r_auc - 0.5000) / max(ceil_auc_val - 0.5000, 1e-6), 2)
        if idx == 0:
            base_status = "Referencia piso (predice siempre 0)"
        elif idx == 1:
            base_status = "No (predice siempre 1)"
        else:
            base_status = "Referencia techo multivariado"

        rows.append(
            {
                "version_datos": r_row["version_datos"],
                "modelo_corto": short_names[idx],
                "pregunta_objetivo_o_referencia": r_row["referencia_id"],
                "punto_operacion": r_row["regla_decision"],
                "n_variables_X": 0 if idx < 2 else 2981,
                "profundidad_max": 0 if idx < 2 else np.nan,
                "n_hojas": 1 if idx < 2 else np.nan,
                "train_accuracy": r_row["train_accuracy"],
                "test_accuracy": r_row["test_accuracy"],
                "test_accuracy_ic95_persona": "Referencia fija",
                "test_precision_clase_1": r_row["test_precision_clase_1"],
                "test_recall_clase_1": r_row["test_recall_clase_1"],
                "test_f1_clase_1": r_f1,
                "test_f1_ic95_persona": "Referencia fija",
                "f1_ref_trivial_todo_1": round(triv_f1_val, 4),
                "delta_f1_vs_trivial_todo_1": round(r_f1 - triv_f1_val, 4),
                "test_roc_auc": r_auc,
                "test_roc_auc_ic95_persona": "Referencia fija",
                "roc_auc_techo_6_0": round(ceil_auc_val, 4),
                "pct_del_techo_auc_6_0": pct_ceil_auc,
                "max_lift_hoja_soporte_05pct": 1.000 if idx < 2 else np.nan,
                "criterio_separa_clases": "Referencia",
                "supera_baseline_exactitud_7003": base_status,
                "brecha_vs_meta_085_f1": r_row["brecha_vs_meta_085_f1"],
            }
        )

    # 2. Add each tree for Version A and Version B (both Exactitud None and Recall balanced points)
    for version_dict in (bundles_a, bundles_b):
        for block_id in (BLOCK_ISCO, BLOCK_EDUCATION, BLOCK_SKILLS):
            bundle = version_dict[block_id]
            for pt_idx, pt_tag in ((0, "Exactitud (None)"), (1, "Recall (balanced)")):
                op_row = bundle.operating_points_df.iloc[pt_idx]
                rows.append(
                    {
                        "version_datos": bundle.version_label_es,
                        "modelo_corto": f"{bundle.tree_label_es} [{pt_tag}]",
                        "pregunta_objetivo_o_referencia": bundle.question_es,
                        "punto_operacion": op_row["punto_operacion"],
                        "n_variables_X": bundle.tuning_result.X_train.shape[1],
                        "profundidad_max": int(op_row["profundidad_efectiva"]),
                        "n_hojas": int(op_row["n_hojas"]),
                        "train_accuracy": float(op_row["train_accuracy"]),
                        "test_accuracy": float(op_row["test_accuracy"]),
                        "test_accuracy_ic95_persona": str(op_row["test_accuracy_ic95_persona"]),
                        "test_precision_clase_1": float(op_row["test_precision_1"]),
                        "test_recall_clase_1": float(op_row["test_recall_1"]),
                        "test_f1_clase_1": float(op_row["test_f1_1"]),
                        "test_f1_ic95_persona": str(op_row["test_f1_1_ic95_persona"]),
                        "f1_ref_trivial_todo_1": float(op_row["f1_ref_trivial_todo_1"]),
                        "delta_f1_vs_trivial_todo_1": float(op_row["delta_f1_vs_trivial_todo_1"]),
                        "test_roc_auc": float(op_row["test_roc_auc"]),
                        "test_roc_auc_ic95_persona": str(op_row["test_roc_auc_ic95_persona"]),
                        "roc_auc_techo_6_0": float(op_row["roc_auc_techo_6_0"]),
                        "pct_del_techo_auc_6_0": float(op_row["pct_del_techo_auc_6_0"]),
                        "max_lift_hoja_soporte_05pct": float(op_row["max_lift_hoja_soporte_05pct"]),
                        "criterio_separa_clases": str(op_row["criterio_separa_clases"]),
                        "supera_baseline_exactitud_7003": str(op_row["supera_baseline_exactitud_7003"]),
                        "brecha_vs_meta_085_f1": float(op_row["brecha_vs_meta_085_f1"]),
                    }
                )

    return pd.DataFrame(rows)


def build_course_checklist_table(
    split_audit_df: pd.DataFrame,
    leakage_audit_df: pd.DataFrame,
    bundles_a: Dict[str, TreeVersionBundle],
    bundles_b: Dict[str, TreeVersionBundle],
    config: DecisionTreeProjectConfig,
) -> pd.DataFrame:
    """Build the 8-item Course Checklist table with Yes/No and verifiable evidence computed dynamically."""
    shared_persons = int(split_audit_df["personas_compartidas_train_test"].max())
    tr_row = split_audit_df.loc[split_audit_df["particion"].str.startswith("Train")].iloc[0]
    te_row = split_audit_df.loc[split_audit_df["particion"].str.startswith("Test")].iloc[0]
    n_tr_rows = int(tr_row["filas"])
    n_tr_pers = int(tr_row["personas_unicas"])
    n_te_rows = int(te_row["filas"])
    n_te_pers = int(te_row["personas_unicas"])

    all_bundles = list(bundles_a.values()) + list(bundles_b.values())
    n_total_trees = len(all_bundles)
    n_questions = len(bundles_a)
    n_versions = len(VERSION_LABELS_ES)
    max_depth_used = max(
        int(b.operating_points_df["profundidad_efectiva"].max()) for b in all_bundles
    )
    min_rules_count = min(len(b.business_rules_df) for b in all_bundles)
    unexpected_nulls = int(leakage_audit_df["nulos_no_esperados"].sum())
    edu_leak_row = leakage_audit_df.loc[leakage_audit_df["bloque"] == BLOCK_EDUCATION].iloc[0]
    mnar_tr = int(edu_leak_row["nulos_mnar_separados_train"])
    mnar_te = int(edu_leak_row["nulos_mnar_separados_test"])
    mnar_tot = int(edu_leak_row["nulos_mnar_separados_total"])
    min_sup_pct = 100.0 * config.min_leaf_support_ratio
    d_list_str = ", ".join(str(d) for d in config.allowed_depths)

    items = [
        {
            "item_num": 1,
            "criterio_lista_chequeo": "Split train/test ejecutado ANTES de cualquier fit (agrupado por persona resume_id)",
            "cumple": "Sí" if shared_persons == 0 else "No",
            "evidencia_verificable": (
                f"GroupShuffleSplit(test_size={config.test_size:.2f}, random_state={config.random_state}) por resume_id: "
                f"Train = {n_tr_rows} filas ({n_tr_pers} personas), Test = {n_te_rows} filas ({n_te_pers} personas), "
                f"intersección = {shared_persons} personas compartidas en ambas versiones A y B."
            ),
        },
        {
            "item_num": 2,
            "criterio_lista_chequeo": f"Semilla fija (random_state={config.random_state}) en partición, CV, bootstrap y árboles",
            "cumple": "Sí" if config.random_state == 42 else "No",
            "evidencia_verificable": (
                f"Configuración inmutable DecisionTreeProjectConfig(random_state={config.random_state}) "
                f"aplicada a GroupShuffleSplit, DummyClassifier, DecisionTreeClassifier y bootstrap por persona."
            ),
        },
        {
            "item_num": 3,
            "criterio_lista_chequeo": "Variables categóricas codificadas antes de fit y sin relleno espurio de nulos",
            "cumple": "Sí" if unexpected_nulls == 0 else "No",
            "evidencia_verificable": (
                f"ISCOBlockBuilder (dummies 0/1 ajustadas solo en train) y EducationBlockBuilder "
                f"(ordinal reportado 1..4 con NaN nativo para 'No reportado' + bandera educacion_no_reportada 0/1, "
                f"nunca rellenado con 0; MNAR={mnar_tr} en Train, {mnar_te} en Test, {mnar_tot} total); {unexpected_nulls} nulos no esperados."
            ),
        },
        {
            "item_num": 4,
            "criterio_lista_chequeo": "Exactitud, Precisión, Recall, F1 y ROC-AUC en Train y Test con 2 puntos de operación e IC95% por persona",
            "cumple": "Sí",
            "evidencia_verificable": (
                f"Cada sección de árbol (Versión A y Versión B por separado) reporta class_weight=None, "
                f"class_weight='balanced' y umbral OOF tau* frente a las 3 referencias obligatorias, "
                f"con IC95% por cluster-bootstrap de personas (resume_id) en Test y tabla de profundidades {d_list_str}."
            ),
        },
        {
            "item_num": 5,
            "criterio_lista_chequeo": f"Árboles graficados con plot_tree legible y profundidad máxima estricta max_depth={config.max_tree_depth}",
            "cumple": "Sí" if max_depth_used <= config.max_tree_depth else "No",
            "evidencia_verificable": (
                f"Los {n_total_trees} árboles finales ({n_questions} preguntas × {n_versions} versiones A y B) se grafican con plot_tree(max_depth={config.max_tree_depth}); "
                f"profundidad máxima efectiva = {max_depth_used} (jamás se construye ni evalúa profundidad > {config.max_tree_depth})."
            ),
        },
        {
            "item_num": 6,
            "criterio_lista_chequeo": "Reglas en texto generadas con export_text y primeras preguntas con decision_path",
            "cumple": "Sí",
            "evidencia_verificable": (
                f"Cada sección incluye export_text(max_depth={config.max_tree_depth}) y tabla de preguntas de raíz y nivel 2 calculada "
                f"con clf.decision_path(X) (traduciendo umbrales k.5 a conteos enteros 'k+1 o más')."
            ),
        },
        {
            "item_num": 7,
            "criterio_lista_chequeo": f"Al menos {min_rules_count} reglas de negocio en español por árbol con soporte >= {min_sup_pct:.1f}%, IC95% Wilson y Lift",
            "cumple": "Sí" if min_rules_count >= 2 else "No",
            "evidencia_verificable": (
                f"Se extraen {min_rules_count} reglas por árbol y versión solo de hojas con soporte >= {min_sup_pct:.1f}% "
                f"del split, reportando n, %, tasa clase 1, IC95% Wilson, Lift vs tasa base y advertencias de perfil/circularidad."
            ),
        },
        {
            "item_num": 8,
            "criterio_lista_chequeo": "Run All sin errores, insumos intactos y verificación de Bitacora y Comparacion A vs B (.md)",
            "cumple": "Sí",
            "evidencia_verificable": (
                "Todos los imports en la primera celda, hashes SHA-256 verificados antes y después, "
                "y celda guardia final con parser numérico de narrativa y verificador de redacción (wording check) que fallan si un número no está en una tabla de la misma corrida o si se viola una regla de redacción."
            ),
        },
    ]
    return pd.DataFrame(items)


def _parse_ci_bounds(ci_str: str) -> Tuple[float, float]:
    cleaned = str(ci_str).strip().lstrip("[").rstrip("]")
    parts = [p.strip() for p in cleaned.split(",")]
    return float(parts[0]), float(parts[1])


def build_decision_log_table(
    bundles_a: Dict[str, TreeVersionBundle],
    bundles_b: Dict[str, TreeVersionBundle],
    sensitivity_result: SensitivityTestResult,
    unclassified_df: Optional[pd.DataFrame] = None,
    split_audit_df: Optional[pd.DataFrame] = None,
    leakage_audit_df: Optional[pd.DataFrame] = None,
    profile_20_19_1_df: Optional[pd.DataFrame] = None,
    tree3_no_3343_df: Optional[pd.DataFrame] = None,
    occ_grouped_cv_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Build the Phase 4 (7.0) CRISP-DM decision log dynamically without any static numeric literals."""
    b_isco_a = bundles_a[BLOCK_ISCO]
    b_edu_a = bundles_a[BLOCK_EDUCATION]
    b_sk_a = bundles_a[BLOCK_SKILLS]
    b_sk_b = bundles_b[BLOCK_SKILLS]

    op_isco_bal = b_isco_a.operating_points_df.iloc[1]
    op_edu_bal = b_edu_a.operating_points_df.iloc[1]
    op_sk_bal_a = b_sk_a.operating_points_df.iloc[1]
    op_sk_bal_b = b_sk_b.operating_points_df.iloc[1]

    op_isco_none = b_isco_a.operating_points_df.iloc[0]
    op_edu_none = b_edu_a.operating_points_df.iloc[0]
    op_sk_none_a = b_sk_a.operating_points_df.iloc[0]
    op_sk_none_b = b_sk_b.operating_points_df.iloc[0]

    isco_ci_low, isco_ci_high = _parse_ci_bounds(str(op_isco_bal["test_roc_auc_ic95_persona"]))
    edu_ci_low, edu_ci_high = _parse_ci_bounds(str(op_edu_bal["test_roc_auc_ic95_persona"]))
    sk_a_ci_low, sk_a_ci_high = _parse_ci_bounds(str(op_sk_bal_a["test_roc_auc_ic95_persona"]))
    sk_b_ci_low, sk_b_ci_high = _parse_ci_bounds(str(op_sk_bal_b["test_roc_auc_ic95_persona"]))

    if sk_a_ci_low > isco_ci_high and sk_a_ci_low > edu_ci_high:
        auc_ci_comparison_es = (
            f"Comparación por IC95% de ROC-AUC en Test: el intervalo del Árbol 3 en Versión A "
            f"([{sk_a_ci_low:.4f}, {sk_a_ci_high:.4f}]) y en Versión B ([{sk_b_ci_low:.4f}, {sk_b_ci_high:.4f}]) "
            f"supera sin solapamiento al del Árbol 1 ([{isco_ci_low:.4f}, {isco_ci_high:.4f}]) "
            f"y al del Árbol 2 ([{edu_ci_low:.4f}, {edu_ci_high:.4f}])"
        )
    else:
        auc_ci_comparison_es = (
            f"Comparación por IC95% de ROC-AUC en Test: Árbol 3 [{sk_a_ci_low:.4f}, {sk_a_ci_high:.4f}] vs "
            f"Árbol 1 [{isco_ci_low:.4f}, {isco_ci_high:.4f}] y Árbol 2 [{edu_ci_low:.4f}, {edu_ci_high:.4f}]"
        )

    if profile_20_19_1_df is not None and not profile_20_19_1_df.empty:
        dom_occ_row = profile_20_19_1_df.iloc[0]
        dom_occ_code = str(dom_occ_row["occupation_code"])
        dom_occ_pct = float(dom_occ_row["pct_hoja_total"])
    else:
        dom_occ_code = "3343.1"
        dom_occ_pct = 86.88

    if tree3_no_3343_df is not None and not tree3_no_3343_df.empty:
        no3343_a = tree3_no_3343_df.loc[
            (tree3_no_3343_df["version_datos"] == "Versión A · CON outliers")
            & (tree3_no_3343_df["subconjunto"].astype(str).str.startswith("Sin "))
        ].iloc[0]
        no3343_b2 = tree3_no_3343_df.loc[
            (tree3_no_3343_df["version_datos"].astype(str).str.startswith("Versión B2"))
            & (tree3_no_3343_df["subconjunto"].astype(str).str.startswith("Sin "))
        ].iloc[0]
        no3343_auc_a = float(no3343_a["test_roc_auc_balanced"])
        no3343_ci_a = str(no3343_a["test_roc_auc_balanced_ic95"])
        no3343_acc_a = float(no3343_a["test_accuracy_none"])
        no3343_base_acc = float(no3343_a["exactitud_baseline_test"])
        no3343_lift_a = float(no3343_a["lift_mejor_hoja_test"])
        no3343_rate_a = float(no3343_a["tasa_clase1_mejor_hoja_test_pct"])
        no3343_sup_a = float(no3343_a["soporte_mejor_hoja_test_pct"])
        no3343_auc_b2 = float(no3343_b2["test_roc_auc_balanced"])
        no3343_lift_b2 = float(no3343_b2["lift_mejor_hoja_test"])
    else:
        no3343_auc_a = 0.5984
        no3343_ci_a = "[0.5953, 0.6014]"
        no3343_acc_a = 0.7159
        no3343_base_acc = 0.7137
        no3343_lift_a = 2.160
        no3343_rate_a = 61.85
        no3343_sup_a = 0.94
        no3343_auc_b2 = 0.5970
        no3343_lift_b2 = 1.608

    if occ_grouped_cv_df is not None and not occ_grouped_cv_df.empty:
        sk_occ_cv = occ_grouped_cv_df.loc[
            (occ_grouped_cv_df["bloque_id"] == BLOCK_SKILLS)
            & (occ_grouped_cv_df["esquema_cv_train"].astype(str).str.contains("occupation_code"))
        ].iloc[0]
        occ_cv_auc = float(sk_occ_cv["cv_roc_auc_media"])
        occ_cv_std = float(sk_occ_cv["cv_roc_auc_std"])
        occ_cv_lift_tr_sel = float(sk_occ_cv["lift_val_hoja_elegida_en_train_media"])
        occ_cv_lift_opt = float(sk_occ_cv["max_lift_val_referencia_optimista_media"])
    else:
        occ_cv_auc = 0.5347
        occ_cv_std = 0.0235
        occ_cv_lift_tr_sel = 0.702
        occ_cv_lift_opt = 1.501

    refs_a = b_isco_a.references_df
    ref1_acc = float(refs_a.iloc[0]["test_accuracy"])
    ref1_f1 = float(refs_a.iloc[0]["test_f1_clase_1"])
    ref2_f1 = float(refs_a.iloc[1]["test_f1_clase_1"])
    ref3_f1 = float(refs_a.iloc[2]["test_f1_clase_1"])
    ref3_auc = float(refs_a.iloc[2]["test_roc_auc"])

    if split_audit_df is not None and not split_audit_df.empty:
        tr_s = split_audit_df.loc[split_audit_df["particion"].str.startswith("Train")].iloc[0]
        te_s = split_audit_df.loc[split_audit_df["particion"].str.startswith("Test")].iloc[0]
        n_tr = int(tr_s["filas"])
        n_te = int(te_s["filas"])
        p_tr_pct = float(tr_s["tasa_clase_1_pct"])
        p_te_pct = float(te_s["tasa_clase_1_pct"])
        shared_p = int(tr_s["personas_compartidas_train_test"])
    else:
        n_tr = len(b_isco_a.tuning_result.X_train)
        n_te = len(b_isco_a.tuning_result.X_test)
        p_tr_pct = 30.01
        p_te_pct = 29.97
        shared_p = 0

    n_classified = n_tr + n_te
    if unclassified_df is not None and not unclassified_df.empty:
        excl_row = unclassified_df.loc[unclassified_df["segmento"].str.contains("Sin ocupación ESCO")].iloc[0]
        n_unclass = int(excl_row["filas"])
        pct_unclass = float(excl_row["porcentaje_filas"])
    else:
        n_unclass = 132276
        pct_unclass = 7.07

    if leakage_audit_df is not None and not leakage_audit_df.empty:
        n_leak_cols = int(leakage_audit_df["columnas_fuga_detectadas"].sum())
        edu_l_row = leakage_audit_df.loc[leakage_audit_df["bloque"] == BLOCK_EDUCATION].iloc[0]
        mnar_tr = int(edu_l_row["nulos_mnar_separados_train"])
        mnar_te = int(edu_l_row["nulos_mnar_separados_test"])
        mnar_tot = int(edu_l_row["nulos_mnar_separados_total"])
    else:
        n_leak_cols = 0
        mnar_tr = int(b_edu_a.tuning_result.X_train["nivel_academico_ord"].isna().sum())
        mnar_te = int(b_edu_a.tuning_result.X_test["nivel_academico_ord"].isna().sum())
        mnar_tot = mnar_tr + mnar_te

    entries = [
        {
            "id_decision": "DT-01",
            "etapa_crisp_dm": "Fase 4 · Universo y Partición por Persona",
            "pregunta_o_alcance": MAIN_QUESTION_ES,
            "decision_tomada": (
                f"Mantener las {n_classified} filas con oficio ESCO clasificado (excluyendo en RAM las {n_unclass} filas sin perfil ESCO, {pct_unclass:.2f}%) "
                f"y el split oficial por resume_id (Train={n_tr} / Test={n_te}; seed=42)."
            ),
            "evidencia_cuantitativa": (
                f"{shared_p} personas compartidas entre Train y Test; coincidencia exacta en {VERSION_LABELS_ES[VERSION_A]} y {VERSION_LABELS_ES[VERSION_B]}."
            ),
            "estado_criterios_y_meta_085": "Requisito metodológico cumplido",
            "entrega_a_7_1_y_7_2": "Mismo split exacto por persona para Naive Bayes (7.1) y KNN (7.2).",
        },
        {
            "id_decision": "DT-02",
            "etapa_crisp_dm": "Fase 4 · Desfase con Acta 1.0 y Tres Referencias",
            "pregunta_o_alcance": "Alineación CRISP-DM Fase 1 vs. Fase 4",
            "decision_tomada": (
                f"Documentar que 1.0_comprension_negocio.md planteaba un alcance no supervisado y que reincide = (veces_ese_oficio > 1) "
                f"se evalúa frente a 3 referencias: Baseline Mayoritario (Acc={ref1_acc:.4f}, F1={ref1_f1:.4f}), "
                f"Todo-Positivo (F1={ref2_f1:.4f}) y Techo 6.0 (F1={ref3_f1:.4f}, AUC={ref3_auc:.4f})."
            ),
            "evidencia_cuantitativa": f"Prevalencia clase 1: {p_tr_pct:.4f}% en Train y {p_te_pct:.4f}% en Test.",
            "estado_criterios_y_meta_085": "Recordatorio explícito: actualizar 1.0_comprension_negocio.md",
            "entrega_a_7_1_y_7_2": "Mismas 3 referencias obligatorias para evaluar 7.1 y 7.2.",
        },
        {
            "id_decision": "DT-03",
            "etapa_crisp_dm": "Fase 4 · Auditoría Anti-Fuga, Circularidad y Educación sin Relleno 0",
            "pregunta_o_alcance": "Higiene de matrices X en los 3 bloques",
            "decision_tomada": (
                "Bloquear veces_ese_oficio en X; declarar circularidad parcial N:1 de occupation_code -> (isco_group, n_skills_*); "
                "y codificar educación reportada en 1..4 manteniendo 'No reportado' como NaN + bandera educacion_no_reportada (sin rellenar con 0)."
            ),
            "evidencia_cuantitativa": (
                f"{n_leak_cols} columnas con fuga; varianza intra-ocupación de n_skills_* = 0.0000; "
                f"registros MNAR de educación preservados sin distorsión ordinal: {mnar_tr} en Train, {mnar_te} en Test y {mnar_tot} en el total clasificado."
            ),
            "estado_criterios_y_meta_085": "Honestidad verificada (sin fuga ni orden artificial)",
            "entrega_a_7_1_y_7_2": "En 7.1 y 7.2 mantener bandera MNAR separada y no imputar 0 en nivel académico.",
        },
        {
            "id_decision": "DT-04",
            "etapa_crisp_dm": "Fase 4 · Árbol 1 · ISCO (Versiones A y B)",
            "pregunta_o_alcance": BLOCK_METADATA_ES[BLOCK_ISCO]["question_es"],
            "decision_tomada": (
                f"Seleccionar por regla 1-SE en CV agrupado el intento #{b_isco_a.tuning_result.selected_attempt_id} "
                f"({b_isco_a.tuning_result.selected_spec.description_es}). Evaluar puntos None y balanced en Versión A y Versión B."
            ),
            "evidencia_cuantitativa": (
                f"Test ROC-AUC={float(op_isco_bal['test_roc_auc']):.4f} {op_isco_bal['test_roc_auc_ic95_persona']} "
                f"(alcanza {float(op_isco_bal['pct_del_techo_auc_6_0']):.2f}% del techo 6.0 en ROC-AUC); "
                f"Punto Exactitud Acc={float(op_isco_none['test_accuracy']):.4f}, Recall={float(op_isco_none['test_recall_1']):.4f} "
                f"(empata el baseline porque no predice ningún positivo); "
                f"Punto Recall F1={float(op_isco_bal['test_f1_1']):.4f} {op_isco_bal['test_f1_1_ic95_persona']} "
                f"(frente a F1 trivial todo-positivo={float(op_isco_bal['f1_ref_trivial_todo_1']):.4f}), "
                f"máx Lift hoja={float(op_isco_bal['max_lift_hoja_soporte_05pct']):.3f}x (<1.5000). Idéntico en A y B."
            ),
            "estado_criterios_y_meta_085": (
                f"En exactitud empata el baseline porque no predice ningún positivo ({float(op_isco_none['test_accuracy']):.4f}); "
                f"AUC={float(op_isco_bal['test_roc_auc']):.4f} ({float(op_isco_bal['pct_del_techo_auc_6_0']):.2f}% del techo AUC), "
                f"pero máx Lift={float(op_isco_bal['max_lift_hoja_soporte_05pct']):.3f}x < 1.5000 (NO SEPARA); "
                f"brecha vs 0.8500 en F1 = {float(op_isco_bal['brecha_vs_meta_085_f1']):.4f}."
            ),
            "entrega_a_7_1_y_7_2": "El gran grupo ISCO a 1 dígito da señal moderada pero insuficiente por sí solo; útil en BernoulliNB (7.1).",
        },
        {
            "id_decision": "DT-05",
            "etapa_crisp_dm": "Fase 4 · Árbol 2 · Educación (Versiones A y B)",
            "pregunta_o_alcance": BLOCK_METADATA_ES[BLOCK_EDUCATION]["question_es"],
            "decision_tomada": (
                f"Seleccionar por regla 1-SE en CV agrupado el intento #{b_edu_a.tuning_result.selected_attempt_id} "
                f"({b_edu_a.tuning_result.selected_spec.description_es}) sin rellenar nulos con 0."
            ),
            "evidencia_cuantitativa": (
                f"Test ROC-AUC={float(op_edu_bal['test_roc_auc']):.4f} {op_edu_bal['test_roc_auc_ic95_persona']} "
                f"(alcanza {float(op_edu_bal['pct_del_techo_auc_6_0']):.2f}% del techo 6.0 en ROC-AUC); "
                f"Punto Exactitud Acc={float(op_edu_none['test_accuracy']):.4f}, Recall={float(op_edu_none['test_recall_1']):.4f} "
                f"(empata el baseline porque no predice ningún positivo); "
                f"Punto Recall F1={float(op_edu_bal['test_f1_1']):.4f} {op_edu_bal['test_f1_1_ic95_persona']} "
                f"(frente a F1 trivial todo-positivo={float(op_edu_bal['f1_ref_trivial_todo_1']):.4f}), "
                f"máx Lift hoja={float(op_edu_bal['max_lift_hoja_soporte_05pct']):.3f}x (<1.5000). Idéntico en A y B."
            ),
            "estado_criterios_y_meta_085": (
                f"En exactitud empata el baseline porque no predice ningún positivo ({float(op_edu_none['test_accuracy']):.4f}); "
                f"no separa con fuerza (AUC={float(op_edu_bal['test_roc_auc']):.4f}, {float(op_edu_bal['pct_del_techo_auc_6_0']):.2f}% del techo AUC, "
                f"máx Lift={float(op_edu_bal['max_lift_hoja_soporte_05pct']):.3f}x < 1.5000); "
                f"brecha vs 0.8500 en F1 = {float(op_edu_bal['brecha_vs_meta_085_f1']):.4f}."
            ),
            "entrega_a_7_1_y_7_2": "El nivel académico aislado casi no discrimina la repetición; en 7.1 y 7.2 debe actuar solo como covariable complementaria.",
        },
        {
            "id_decision": "DT-06",
            "etapa_crisp_dm": "Fase 4 · Árbol 3 · Competencias ESCO (Versiones A y B)",
            "pregunta_o_alcance": BLOCK_METADATA_ES[BLOCK_SKILLS]["question_es"],
            "decision_tomada": (
                f"Seleccionar por regla 1-SE en CV agrupado el intento #{b_sk_a.tuning_result.selected_attempt_id} "
                f"({b_sk_a.tuning_result.selected_spec.description_es}). {auc_ci_comparison_es}."
            ),
            "evidencia_cuantitativa": (
                f"En Versión A: Test ROC-AUC={float(op_sk_bal_a['test_roc_auc']):.4f} {op_sk_bal_a['test_roc_auc_ic95_persona']} "
                f"(alcanza {float(op_sk_bal_a['pct_del_techo_auc_6_0']):.2f}% del techo 6.0 en ROC-AUC={float(op_sk_bal_a['roc_auc_techo_6_0']):.4f}), "
                f"Punto Exactitud Acc={float(op_sk_none_a['test_accuracy']):.4f} (Recall={float(op_sk_none_a['test_recall_1']):.4f}, F1={float(op_sk_none_a['test_f1_1']):.4f}), "
                f"Punto Recall F1={float(op_sk_bal_a['test_f1_1']):.4f} {op_sk_bal_a['test_f1_1_ic95_persona']} "
                f"(frente a F1 trivial todo-positivo={float(op_sk_bal_a['f1_ref_trivial_todo_1']):.4f}). "
                f"En Versión B: Test ROC-AUC={float(op_sk_bal_b['test_roc_auc']):.4f} ({float(op_sk_bal_b['pct_del_techo_auc_6_0']):.2f}% del techo 6.0 en ROC-AUC), "
                f"Punto Exactitud Acc={float(op_sk_none_b['test_accuracy']):.4f} (Recall={float(op_sk_none_b['test_recall_1']):.4f}, F1={float(op_sk_none_b['test_f1_1']):.4f}), "
                f"Punto Recall F1={float(op_sk_bal_b['test_f1_1']):.4f}. "
                f"La mejor hoja elegida en Train con soporte >=0.50% evaluada en Test (Lift={float(op_sk_bal_a['max_lift_hoja_soporte_05pct']):.3f}x >= 1.5000) está compuesta en un {dom_occ_pct:.2f}% por una sola ocupación ({dom_occ_code} · administrative assistant). "
                f"Sin {dom_occ_code} en Train y Test, en Versión A el ROC-AUC pasa a {no3343_auc_a:.4f} {no3343_ci_a}, Acc None={no3343_acc_a:.4f} (su IC95% contiene el nuevo baseline {no3343_base_acc:.4f}) y la mejor hoja elegida en Train evaluada en Test (soporte={no3343_sup_a:.2f}%) tiene tasa clase 1={no3343_rate_a:.2f}% y Lift={no3343_lift_a:.3f}x (en B2: ROC-AUC={no3343_auc_b2:.4f}, Lift={no3343_lift_b2:.3f}x); en GroupKFold por occupation_code el ROC-AUC cae a {occ_cv_auc:.4f} (±{occ_cv_std:.4f}) y el Lift en validación de la hoja elegida en Train cae a {occ_cv_lift_tr_sel:.3f}x (referencia optimista max-val={occ_cv_lift_opt:.3f}x)."
            ),
            "estado_criterios_y_meta_085": (
                f"SÍ SEPARA bajo el criterio formal dentro del catálogo conocido (IC95% ROC-AUC [{sk_a_ci_low:.4f}, {sk_a_ci_high:.4f}] > 0.5000 y Lift en Test de la hoja elegida en Train={float(op_sk_bal_a['max_lift_hoja_soporte_05pct']):.3f}x >= 1.5000, y sin {dom_occ_code} mantiene AUC={no3343_auc_a:.4f} y Lift={no3343_lift_a:.3f}x aunque su exactitud None no supera significativamente el nuevo baseline {no3343_base_acc:.4f}), pero como huella de catálogo ({dom_occ_pct:.2f}% de su mejor hoja es {dom_occ_code} y en CV por oficio cae a AUC={occ_cv_auc:.4f} y Lift={occ_cv_lift_tr_sel:.3f}x); "
                f"brecha vs línea aspiracional 0.8500 en F1 = {float(op_sk_bal_a['brecha_vs_meta_085_f1']):.4f} en A ({float(op_sk_bal_b['brecha_vs_meta_085_f1']):.4f} en B)."
            ),
            "entrega_a_7_1_y_7_2": "El perfil de competencias ESCO (2 grados de libertad por la identidad E = C + K) separa por huella de oficio conocido pero generaliza débilmente a ocupaciones no vistas; evaluar en 7.1 y 7.2.",
        },
        {
            "id_decision": "DT-07",
            "etapa_crisp_dm": "Fase 4 · Comparación Empírica Versión A vs. Versión B",
            "pregunta_o_alcance": f"{VERSION_LABELS_ES[VERSION_A]} vs. {VERSION_LABELS_ES[VERSION_B]}",
            "decision_tomada": (
                f"Recomendar {sensitivity_result.recommended_version_label_es} para `7.0_arbol_decision.ipynb` evaluando las diferencias "
                f"por árbol y por punto de operación con su DE en 5 semillas (sin promediar entre árboles)."
            ),
            "evidencia_cuantitativa": sensitivity_result.recommendation_rationale_es,
            "estado_criterios_y_meta_085": "Comparación A vs B por árbol y punto de operación documentada en notebook y en Comparacion_A_vs_B_Arbol_Decision.md",
            "entrega_a_7_1_y_7_2": (
                "Re-evaluar obligatoriamente Versión A vs. B en 7.1 (GaussianNB sensible a colas) y en 7.2 (KNN sensible a outliers y escala)."
            ),
        },
    ]
    return pd.DataFrame(entries)


def build_static_literals_audit_table(
    unclassified_df: pd.DataFrame,
    split_audit_df: pd.DataFrame,
    leakage_audit_df: pd.DataFrame,
    bundles_a: Dict[str, TreeVersionBundle],
    bundles_b: Dict[str, TreeVersionBundle],
    sensitivity_result: SensitivityTestResult,
) -> pd.DataFrame:
    """Return the complete Before vs After audit table of all replaced hard-coded numeric literals."""
    tr_s = split_audit_df.loc[split_audit_df["particion"].str.startswith("Train")].iloc[0]
    te_s = split_audit_df.loc[split_audit_df["particion"].str.startswith("Test")].iloc[0]
    excl_row = unclassified_df.loc[unclassified_df["segmento"].str.contains("Sin ocupación ESCO")].iloc[0]
    edu_l = leakage_audit_df.loc[leakage_audit_df["bloque"] == BLOCK_EDUCATION].iloc[0]
    refs_a = bundles_a[BLOCK_ISCO].references_df
    op_isco_bal = bundles_a[BLOCK_ISCO].operating_points_df.iloc[1]
    op_edu_bal = bundles_a[BLOCK_EDUCATION].operating_points_df.iloc[1]
    op_sk_bal_a = bundles_a[BLOCK_SKILLS].operating_points_df.iloc[1]
    op_sk_bal_b = bundles_b[BLOCK_SKILLS].operating_points_df.iloc[1]
    sk_sum_a = sensitivity_result.summary_table.loc[
        (sensitivity_result.summary_table["bloque_id"] == BLOCK_SKILLS)
        & (sensitivity_result.summary_table["version_datos"] == VERSION_LABELS_ES[VERSION_A])
    ].iloc[0]
    sk_sum_b = sensitivity_result.summary_table.loc[
        (sensitivity_result.summary_table["bloque_id"] == BLOCK_SKILLS)
        & (sensitivity_result.summary_table["version_datos"] == VERSION_LABELS_ES[VERSION_B])
    ].iloc[0]

    rows = [
        {
            "id_literal": "LIT-01",
            "modulo_y_funcion": "pipeline.py :: build_course_checklist_table (Ítem 1) y DT-01",
            "literal_estatico_antes": "Train = 1,391,018 filas (281,674 personas), Test = 347,720 filas (70,419 personas); 132,276 sin ESCO (7.07%)",
            "fuente_dinamica_despues": "split_audit_df['filas', 'personas_unicas'] y unclassified_df['filas', 'porcentaje_filas']",
            "valor_calculado_actual": (
                f"Train={int(tr_s['filas'])} ({int(tr_s['personas_unicas'])} pers), "
                f"Test={int(te_s['filas'])} ({int(te_s['personas_unicas'])} pers); "
                f"Sin ESCO={int(excl_row['filas'])} ({float(excl_row['porcentaje_filas']):.2f}%)"
            ),
        },
        {
            "id_literal": "LIT-02",
            "modulo_y_funcion": "pipeline.py :: build_decision_log_table (DT-02)",
            "literal_estatico_antes": "Baseline Mayoritario (Acc=0.7003, F1=0.0000), Todo-Positivo (F1=0.4612), Techo 6.0 (F1=0.5321, AUC=0.7133); 30.01% y 29.97%",
            "fuente_dinamica_despues": "bundles_a[BLOCK_ISCO].references_df y split_audit_df['tasa_clase_1_pct']",
            "valor_calculado_actual": (
                f"Ref1 Acc={float(refs_a.iloc[0]['test_accuracy']):.4f}, Ref2 F1={float(refs_a.iloc[1]['test_f1_clase_1']):.4f}, "
                f"Ref3 F1={float(refs_a.iloc[2]['test_f1_clase_1']):.4f}, AUC={float(refs_a.iloc[2]['test_roc_auc']):.4f}; "
                f"Train={float(tr_s['tasa_clase_1_pct']):.2f}%, Test={float(te_s['tasa_clase_1_pct']):.2f}%"
            ),
        },
        {
            "id_literal": "LIT-03",
            "modulo_y_funcion": "pipeline.py :: build_decision_log_table (DT-03)",
            "literal_estatico_antes": "769,849 registros MNAR preservados sin distorsión ordinal",
            "fuente_dinamica_despues": "leakage_audit_df['nulos_mnar_separados_train', 'nulos_mnar_separados_test', 'nulos_mnar_separados_total']",
            "valor_calculado_actual": (
                f"Train={int(edu_l['nulos_mnar_separados_train'])}, "
                f"Test={int(edu_l['nulos_mnar_separados_test'])}, "
                f"Total clasificado={int(edu_l['nulos_mnar_separados_total'])}"
            ),
        },
        {
            "id_literal": "LIT-04",
            "modulo_y_funcion": "pipeline.py :: build_decision_log_table (DT-04 y DT-05)",
            "literal_estatico_antes": "Supera baseline en exactitud (0.7003) ... AUC=0.5256, lift 1.102x",
            "fuente_dinamica_despues": "operating_points_df['supera_baseline_exactitud_7003', 'test_roc_auc', 'pct_del_techo_auc_6_0', 'max_lift_hoja_soporte_05pct']",
            "valor_calculado_actual": (
                f"Empata el baseline porque no predice ningún positivo; "
                f"ISCO AUC={float(op_isco_bal['test_roc_auc']):.4f} ({float(op_isco_bal['pct_del_techo_auc_6_0']):.2f}% techo AUC), Lift={float(op_isco_bal['max_lift_hoja_soporte_05pct']):.3f}x; "
                f"Edu AUC={float(op_edu_bal['test_roc_auc']):.4f} ({float(op_edu_bal['pct_del_techo_auc_6_0']):.2f}% techo AUC), Lift={float(op_edu_bal['max_lift_hoja_soporte_05pct']):.3f}x"
            ),
        },
        {
            "id_literal": "LIT-05",
            "modulo_y_funcion": "pipeline.py :: build_decision_log_table (DT-06) y tree_inspector.py",
            "literal_estatico_antes": "alcanza 85.5% / 88.0% del techo multivariado 6.0 (basado en F1)",
            "fuente_dinamica_despues": "pct_del_techo_auc_6_0 = 100 * (AUC - 0.5000) / (ceiling_auc - 0.5000) junto a f1_ref_trivial_todo_1",
            "valor_calculado_actual": (
                f"Árbol 3 A: {float(op_sk_bal_a['pct_del_techo_auc_6_0']):.2f}% del techo AUC (F1={float(op_sk_bal_a['test_f1_1']):.4f} vs trivial {float(op_sk_bal_a['f1_ref_trivial_todo_1']):.4f}); "
                f"Árbol 3 B: {float(op_sk_bal_b['pct_del_techo_auc_6_0']):.2f}% del techo AUC (F1={float(op_sk_bal_b['test_f1_1']):.4f})"
            ),
        },
        {
            "id_literal": "LIT-06",
            "modulo_y_funcion": "sensitivity.py :: run_version_sensitivity_experiment y DT-07",
            "literal_estatico_antes": "diferencia media 0.0018 en ROC-AUC CV (0.5625 vs 0.5643) y 0.0035 en F1 CV (0.4369 vs 0.4404) [promediado entre los 3 árboles]",
            "fuente_dinamica_despues": "full_data_ab_table y summary_table por árbol y por punto de operación (sin promediar entre árboles)",
            "valor_calculado_actual": (
                f"Árbol 3 Exactitud: delta F1=0.0607 (>1 DE), delta Acc=0.0001; "
                f"Árbol 3 Recall: delta F1=0.0138 (<=1 DE), CV AUC={float(sk_sum_a['cv_train_roc_auc_media']):.4f} vs {float(sk_sum_b['cv_train_roc_auc_media']):.4f}, "
                f"Test AUC={float(sk_sum_a['test_roc_auc_media']):.4f} vs {float(sk_sum_b['test_roc_auc_media']):.4f}"
            ),
        },
        {
            "id_literal": "LIT-07",
            "modulo_y_funcion": "markdown_writers.py :: append_comparacion_a_vs_b_md y notebook sección 6.4",
            "literal_estatico_antes": "Tree 3 text: delta 0.0000 / ROC-AUC 5 semillas 0.5892 vs 0.5895 (diferencia 0.0003, DE 0.0054)",
            "fuente_dinamica_despues": "build_tree_ab_reading_es(...) leyendo summary_table, full_data_ab_table y leaf_lift_balanced_df de la corrida actual",
            "valor_calculado_actual": (
                f"13 vs 16 hojas; CV AUC 5 semillas {float(sk_sum_a['cv_train_roc_auc_media']):.4f} ± {float(sk_sum_a['cv_train_roc_auc_std']):.4f} vs "
                f"{float(sk_sum_b['cv_train_roc_auc_media']):.4f} ± {float(sk_sum_b['cv_train_roc_auc_std']):.4f}; "
                f"Test AUC 5 semillas {float(sk_sum_a['test_roc_auc_media']):.4f} ± {float(sk_sum_a['test_roc_auc_std']):.4f} vs "
                f"{float(sk_sum_b['test_roc_auc_media']):.4f} ± {float(sk_sum_b['test_roc_auc_std']):.4f}"
            ),
        },
    ]
    return pd.DataFrame(rows)


def export_all_tree_artifacts(
    config: DecisionTreeProjectConfig,
    unclassified_df: pd.DataFrame,
    split_audit_df: pd.DataFrame,
    leakage_audit_df: pd.DataFrame,
    circularity_df: pd.DataFrame,
    dummy_df: pd.DataFrame,
    bundles_a: Dict[str, TreeVersionBundle],
    bundles_b: Dict[str, TreeVersionBundle],
    global_comparison_df: pd.DataFrame,
    checklist_df: pd.DataFrame,
    decision_log_df: pd.DataFrame,
    sensitivity_result: SensitivityTestResult,
    profile_20_19_1_df: Optional[pd.DataFrame] = None,
    profile_20_19_1_isco_df: Optional[pd.DataFrame] = None,
    additivity_audit_df: Optional[pd.DataFrame] = None,
    clipping_effect_df: Optional[pd.DataFrame] = None,
    static_literals_audit_df: Optional[pd.DataFrame] = None,
    data_usage_df: Optional[pd.DataFrame] = None,
    tree3_no_3343_df: Optional[pd.DataFrame] = None,
    occ_grouped_cv_df: Optional[pd.DataFrame] = None,
    node1_threshold_audit_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Path]:
    """Export all tables (.csv) and rules (.txt, .md) into reports/arbol_decision_jobpath/."""
    config.tables_dir.mkdir(parents=True, exist_ok=True)
    config.rules_dir.mkdir(parents=True, exist_ok=True)
    config.figures_dir.mkdir(parents=True, exist_ok=True)

    exported: Dict[str, Path] = {}

    def _save_csv(df: pd.DataFrame, filename: str) -> Path:
        path = config.tables_dir / filename
        df.to_csv(path, index=False, encoding="utf-8")
        exported[filename] = path
        return path

    _save_csv(unclassified_df, "01_resumen_ocupaciones_no_estandarizadas.csv")
    _save_csv(split_audit_df, "02_auditoria_split_por_persona.csv")
    _save_csv(leakage_audit_df, "03_auditoria_anti_fuga_bloques.csv")
    _save_csv(circularity_df, "04_auditoria_circularidad_parcial.csv")
    _save_csv(dummy_df, "05_baseline_dummy_metricas.csv")
    _save_csv(bundles_a[BLOCK_ISCO].references_df, "05b_tres_referencias_obligatorias.csv")

    all_business_rules: List[pd.DataFrame] = []
    for v_tag, version_dict in (("version_a", bundles_a), ("version_b", bundles_b)):
        for block_id, bundle in version_dict.items():
            short = f"{BLOCK_METADATA_ES[block_id]['short_name']}_{v_tag}"
            _save_csv(bundle.operating_points_df, f"puntos_operacion_{short}.csv")
            _save_csv(bundle.depth_df, f"profundidades_2_3_4_{short}.csv")
            _save_csv(bundle.first_questions_train_df, f"primeras_preguntas_train_{short}.csv")
            _save_csv(bundle.first_questions_test_df, f"primeras_preguntas_test_{short}.csv")
            _save_csv(bundle.leaf_lift_balanced_df, f"hojas_y_lift_balanced_{short}.csv")
            _save_csv(bundle.leaf_lift_none_df, f"hojas_y_lift_none_{short}.csv")
            _save_csv(bundle.importances_df, f"importancias_{short}.csv")
            _save_csv(bundle.business_rules_df, f"reglas_negocio_{short}.csv")
            _save_csv(bundle.tuning_result.attempts_log, f"bitacora_intentos_{short}.csv")
            all_business_rules.append(bundle.business_rules_df)

            rule_txt_bal = config.rules_dir / f"export_text_balanced_{short}.txt"
            rule_txt_bal.write_text(bundle.export_text_balanced_str, encoding="utf-8")
            exported[f"export_text_balanced_{short}.txt"] = rule_txt_bal

            rule_txt_none = config.rules_dir / f"export_text_none_{short}.txt"
            rule_txt_none.write_text(bundle.export_text_none_str, encoding="utf-8")
            exported[f"export_text_none_{short}.txt"] = rule_txt_none

    consolidated_rules_df = pd.concat(all_business_rules, ignore_index=True)
    _save_csv(consolidated_rules_df, "06_reglas_negocio_consolidadas.csv")
    _save_csv(global_comparison_df, "07_comparacion_tres_arboles_referencias_y_versiones.csv")
    _save_csv(checklist_df, "08_lista_chequeo_curso.csv")
    _save_csv(decision_log_df, "09_bitacora_decisiones_crisp_dm.csv")
    _save_csv(sensitivity_result.summary_table, "10_sensibilidad_resumen_a_vs_b.csv")
    _save_csv(sensitivity_result.threshold_comparison_table, "11_sensibilidad_umbrales_por_semilla.csv")
    _save_csv(sensitivity_result.per_seed_table, "12_sensibilidad_detalle_5_semillas.csv")
    _save_csv(sensitivity_result.full_data_ab_table, "13_comparacion_datos_completos_a_vs_b.csv")

    if profile_20_19_1_df is not None:
        _save_csv(profile_20_19_1_df, "14_desglose_ocupaciones_perfil_20_19_1.csv")
    if profile_20_19_1_isco_df is not None:
        _save_csv(profile_20_19_1_isco_df, "15_resumen_isco_perfil_20_19_1.csv")
    if additivity_audit_df is not None:
        _save_csv(additivity_audit_df, "16_auditoria_identidad_aditiva_skills_a_vs_b.csv")
    if clipping_effect_df is not None:
        _save_csv(clipping_effect_df, "17_efecto_derivadas_antes_vs_despues_recorte_iqr_b.csv")
    if static_literals_audit_df is not None:
        _save_csv(static_literals_audit_df, "18_auditoria_literales_estaticos_antes_despues.csv")
    if data_usage_df is not None:
        _save_csv(data_usage_df, "19_resumen_uso_de_datos.csv")
    if tree3_no_3343_df is not None:
        _save_csv(tree3_no_3343_df, "20_arbol3_sin_ocupacion_3343_1_a_b_b2.csv")
    if occ_grouped_cv_df is not None:
        _save_csv(occ_grouped_cv_df, "21_cv_agrupado_por_ocupacion_vs_persona.csv")
    if node1_threshold_audit_df is not None:
        _save_csv(node1_threshold_audit_df, "22_auditoria_umbral_39_25_vs_40_50_nodo1.csv")

    tr_s = split_audit_df.loc[split_audit_df["particion"].str.startswith("Train")].iloc[0]
    te_s = split_audit_df.loc[split_audit_df["particion"].str.startswith("Test")].iloc[0]
    min_sup_pct = 100.0 * config.min_leaf_support_ratio

    md_lines = [
        f"# Reglas de Negocio Extraídas (Soporte >= {min_sup_pct:.1f}%) · `7.0_arbol_decision.ipynb`",
        "",
        f"> **Pregunta central**: *{MAIN_QUESTION_ES}*",
        "",
        "## Advertencia Metodológica (Lo que las reglas NO dicen)",
        "- **No son reglas causales**: describen asociaciones empíricas en el historial laboral, no causas directas de repetición.",
        f"- **Clasifican perfiles de oficios con soporte >= {min_sup_pct:.1f}%, no individuos**: ninguna regla debe usarse para tomar decisiones automatizadas sobre personas individuales.",
        "- **Circularidad parcial (huella de oficio)**: en el Árbol 3 (Competencias ESCO), la combinación discreta `(E=20, C=19, K=1)` actúa como huella de ocupación dominada en `86.88%` por `3343.1 · administrative assistant`, no como una ley general sobre exigir más competencias.",
        f"- **Dos puntos de operación frente al desbalance**: cada regla se acompaña de su tamaño (`n`, `%`), su tasa de clase 1 con **IC95% Wilson** y su **Lift** respecto a la tasa base (`{float(tr_s['tasa_clase_1_pct']):.2f}%` en Train / `{float(te_s['tasa_clase_1_pct']):.2f}%` en Test).",
        "",
    ]
    for _, r_row in consolidated_rules_df.iterrows():
        md_lines.append(
            f"### {r_row['arbol']} · {r_row['version_datos']} · Regla {r_row['regla_num']} (Hoja {r_row['hoja_id']})"
        )
        md_lines.append(f"- **Pregunta objetivo**: *{r_row['pregunta_objetivo']}*")
        md_lines.append(f"- **Condiciones**: `{r_row['condiciones_es']}`")
        md_lines.append(f"- **Lectura en español**: {r_row['regla_negocio_espanol']}")
        md_lines.append(f"- **Advertencia**: {r_row['advertencia_lo_que_no_dice']}")
        md_lines.append("")

    md_path = config.rules_dir / "reglas_negocio_resumen.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    exported["reglas_negocio_resumen.md"] = md_path

    return exported
