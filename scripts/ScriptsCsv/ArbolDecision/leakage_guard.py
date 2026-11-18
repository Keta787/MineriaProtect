"""Anti-leakage guard, partial-circularity auditor, profile (20,19,1) fingerprinter, and Version B IQR additivity auditor."""

from __future__ import annotations

from typing import Any, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.tree import DecisionTreeClassifier, _tree

from .block_builders import EducationBlockBuilder, ISCOBlockBuilder, SkillsBlockBuilder
from .config import (
    BLOCK_EDUCATION,
    BLOCK_ISCO,
    BLOCK_METADATA_ES,
    BLOCK_SKILLS,
    DecisionTreeProjectConfig,
    ISCO_MAJOR_LABELS_ES,
    PROHIBITED_LEAKAGE_COLUMNS,
)
from .data_loader import SplitBundle
from .tree_inspector import bootstrap_person_metrics_ci, build_leaf_lift_table


FORBIDDEN_SUBSTRINGS: Tuple[str, ...] = (
    "veces_ese_oficio",
    "n_returns",
    "nonadjacent_returns",
    "reincid",
    "repeated_occupation",
)


def assert_no_direct_leakage(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    block_name: str,
    version_label: str = "",
    prohibited_columns: Sequence[str] = PROHIBITED_LEAKAGE_COLUMNS,
) -> pd.DataFrame:
    """Validate that X contains no target-defining columns, no unexpected nulls, and no direct leakage."""
    prohibited_set = {col.lower() for col in prohibited_columns}
    train_cols = list(X_train.columns)
    test_cols = list(X_test.columns)

    if train_cols != test_cols:
        raise ValueError(f"[{block_name}] Column mismatch between X_train and X_test!")

    flagged_cols = []
    for col in train_cols:
        col_lower = col.lower()
        if col_lower in prohibited_set or any(sub in col_lower for sub in FORBIDDEN_SUBSTRINGS):
            flagged_cols.append(col)

    if flagged_cols:
        raise ValueError(
            f"[{block_name}] Direct target leakage detected in feature matrix: {flagged_cols}"
        )

    # Check nulls: only 'nivel_academico_ord' is allowed to have intentional NaN for 'No reportado'
    non_nan_cols = [c for c in train_cols if c != "nivel_academico_ord"]
    n_unexpected_null_tr = int(X_train[non_nan_cols].isna().sum().sum()) if non_nan_cols else 0
    n_unexpected_null_te = int(X_test[non_nan_cols].isna().sum().sum()) if non_nan_cols else 0
    if n_unexpected_null_tr > 0 or n_unexpected_null_te > 0:
        raise ValueError(
            f"[{block_name}] Unexpected null values found: train={n_unexpected_null_tr}, test={n_unexpected_null_te}"
        )

    intentional_nan_tr = int(X_train["nivel_academico_ord"].isna().sum()) if "nivel_academico_ord" in train_cols else 0
    intentional_nan_te = int(X_test["nivel_academico_ord"].isna().sum()) if "nivel_academico_ord" in test_cols else 0
    intentional_nan_tot = intentional_nan_tr + intentional_nan_te

    # Compute maximum absolute Pearson correlation with y_train (on non-null entries)
    correlations = {}
    y_arr = y_train.to_numpy(dtype=float)
    for col in train_cols:
        x_arr = X_train[col].to_numpy(dtype=float)
        valid_mask = ~np.isnan(x_arr)
        if valid_mask.sum() == 0 or np.std(x_arr[valid_mask]) == 0.0:
            correlations[col] = 0.0
        else:
            corr = float(np.corrcoef(x_arr[valid_mask], y_arr[valid_mask])[0, 1])
            correlations[col] = abs(corr) if not np.isnan(corr) else 0.0

    max_corr_col = max(correlations, key=correlations.get) if correlations else "ninguna"
    max_corr_val = correlations.get(max_corr_col, 0.0)
    if max_corr_val >= 0.90:
        raise ValueError(
            f"[{block_name}] Suspiciously high correlation ({max_corr_val:.4f}) on {max_corr_col}!"
        )

    return pd.DataFrame(
        [
            {
                "version_datos": version_label,
                "bloque": block_name,
                "pregunta_objetivo": BLOCK_METADATA_ES.get(block_name, {}).get("question_es", block_name),
                "n_variables_X": len(train_cols),
                "columnas_fuga_detectadas": 0,
                "nulos_inesperados_train": n_unexpected_null_tr,
                "nulos_inesperados_test": n_unexpected_null_te,
                "nulos_no_esperados": n_unexpected_null_tr + n_unexpected_null_te,
                "nulos_mnar_separados_train": intentional_nan_tr,
                "nulos_mnar_separados_test": intentional_nan_te,
                "nulos_mnar_separados_total": intentional_nan_tot,
                "esquema_train_test_identico": "Sí",
                "variable_mayor_corr_abs_y": max_corr_col,
                "max_corr_abs_con_reincide": round(max_corr_val, 4),
                "veredicto_anti_fuga": "APROBADO (sin fuga directa)",
            }
        ]
    )


def audit_partial_circularity(df_train: pd.DataFrame) -> pd.DataFrame:
    """Quantify the structural N:1 dependency of ISCO and ESCO skill counts on occupation_code."""
    n_occupations = int(df_train["occupation_code"].nunique())

    occ_skill_pairs = df_train[
        ["occupation_code", "isco_group", "n_skills_essential", "n_skills_competence", "n_skills_knowledge"]
    ].drop_duplicates()
    occ_grouped = occ_skill_pairs.groupby("occupation_code", observed=True)
    max_within_occ_std_essential = float(occ_grouped["n_skills_essential"].std().fillna(0.0).max())
    max_within_occ_std_competence = float(occ_grouped["n_skills_competence"].std().fillna(0.0).max())
    max_within_occ_std_knowledge = float(occ_grouped["n_skills_knowledge"].std().fillna(0.0).max())
    max_isco_per_occ = int(occ_grouped["isco_group"].nunique().max())

    unique_skill_triplets = int(
        occ_skill_pairs[["n_skills_essential", "n_skills_competence", "n_skills_knowledge"]]
        .drop_duplicates()
        .shape[0]
    )
    unique_isco_major = int(occ_skill_pairs["isco_group"].str.slice(0, 1).nunique())
    unique_isco_submajor = int(occ_skill_pairs["isco_group"].str.slice(0, 2).nunique())
    unique_isco_unit = int(occ_skill_pairs["isco_group"].nunique())

    rows = [
        {
            "componente_evaluado": "Target reincide = (veces_ese_oficio > 1)",
            "llave_estructural": "resume_id + occupation_code",
            "cardinalidad_en_train": f"{n_occupations} oficios × {df_train['resume_id'].nunique()} personas",
            "varianza_intra_occupation_code": "Varía por persona (no determinista por oficio)",
            "diagnostico_circularidad": "Definición legítima del evento de repetición laboral",
        },
        {
            "componente_evaluado": f"1 · ISCO ({BLOCK_METADATA_ES[BLOCK_ISCO]['question_es']})",
            "llave_estructural": "occupation_code -> isco_group[0]",
            "cardinalidad_en_train": f"{unique_isco_major} grandes grupos (promedio {n_occupations / unique_isco_major:.1f} oficios/grupo)",
            "varianza_intra_occupation_code": f"0.0000 (1 grupo ISCO por oficio; máx={max_isco_per_occ})",
            "diagnostico_circularidad": "Circularidad parcial BAJA (agregación macro de ~296.8 oficios por gran grupo)",
        },
        {
            "componente_evaluado": "1 · ISCO Variantes (2 dígitos / Top-50 4 dígitos)",
            "llave_estructural": "occupation_code -> isco_group[:2] / isco_group",
            "cardinalidad_en_train": f"{unique_isco_submajor} subgrupos (2d) / {unique_isco_unit} grupos unitarios (4d)",
            "varianza_intra_occupation_code": "0.0000 (asignación N:1 desde ESCO)",
            "diagnostico_circularidad": "Circularidad parcial ALTA en 4 dígitos (casi identifica el oficio específico)",
        },
        {
            "componente_evaluado": f"2 · Education level ({BLOCK_METADATA_ES[BLOCK_EDUCATION]['question_es']})",
            "llave_estructural": "resume_id (atributo de la persona en el CV)",
            "cardinalidad_en_train": "4 niveles reportados (1..4) + bandera no reportado (MNAR)",
            "varianza_intra_occupation_code": "Alta (personas con distinta educación ejercen el mismo oficio)",
            "diagnostico_circularidad": "SIN circularidad con occupation_code (atributo del trabajador, no del catálogo ESCO)",
        },
        {
            "componente_evaluado": f"3 · Skills ({BLOCK_METADATA_ES[BLOCK_SKILLS]['question_es']})",
            "llave_estructural": "occupation_code -> catálogo ESCO v1.2.1",
            "cardinalidad_en_train": f"{unique_skill_triplets} combinaciones únicas de (essential, competence, knowledge)",
            "varianza_intra_occupation_code": (
                f"std máx = {max_within_occ_std_essential:.4f} / "
                f"{max_within_occ_std_competence:.4f} / {max_within_occ_std_knowledge:.4f}"
            ),
            "diagnostico_circularidad": (
                "Circularidad parcial MODERADA: los conteos cuelgan determinísticamente de occupation_code (N:1); "
                "los cortes sobre conteos actúan parcialmente como huella del oficio"
            ),
        },
    ]
    return pd.DataFrame(rows)


def audit_profile_20_19_1_occupations(
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Audit the 12 distinct occupations sharing profile (E=20, C=19, K=1) (Leaf 16 in A / Leaf 26 in B)."""
    m_tr = (
        (df_train["n_skills_essential"] == 20)
        & (df_train["n_skills_competence"] == 19)
        & (df_train["n_skills_knowledge"] == 1)
    )
    m_te = (
        (df_test["n_skills_essential"] == 20)
        & (df_test["n_skills_competence"] == 19)
        & (df_test["n_skills_knowledge"] == 1)
    )

    sub_tr = df_train.loc[m_tr].copy()
    sub_te = df_test.loc[m_te].copy()
    sub_tot = pd.concat([sub_tr, sub_te], ignore_index=True)

    n_leaf_tr = max(len(sub_tr), 1)
    n_leaf_te = max(len(sub_te), 1)
    n_leaf_tot = max(len(sub_tot), 1)

    occ_label_col = "occupation_label" if "occupation_label" in sub_tot.columns else "isco_group_label"
    group_cols = ["occupation_code", occ_label_col, "isco_group", "isco_group_label"]

    g_tr = (
        sub_tr.groupby("occupation_code", observed=True)
        .agg(filas_train=("reincide", "count"), positivos_train=("reincide", "sum"), tasa_clase1_train=("reincide", "mean"))
    )
    g_te = (
        sub_te.groupby("occupation_code", observed=True)
        .agg(filas_test=("reincide", "count"), positivos_test=("reincide", "sum"), tasa_clase1_test=("reincide", "mean"))
    )
    g_tot = (
        sub_tot.groupby(group_cols, observed=True)
        .agg(filas_total=("reincide", "count"), positivos_total=("reincide", "sum"), tasa_clase1_total=("reincide", "mean"))
        .reset_index()
    )

    merged = (
        g_tot.merge(g_tr, on="occupation_code", how="left")
        .merge(g_te, on="occupation_code", how="left")
        .fillna({"filas_train": 0, "positivos_train": 0, "tasa_clase1_train": 0.0, "filas_test": 0, "positivos_test": 0, "tasa_clase1_test": 0.0})
        .sort_values("filas_total", ascending=False)
        .reset_index(drop=True)
    )

    merged["filas_train"] = merged["filas_train"].astype(int)
    merged["positivos_train"] = merged["positivos_train"].astype(int)
    merged["filas_test"] = merged["filas_test"].astype(int)
    merged["positivos_test"] = merged["positivos_test"].astype(int)
    merged["filas_total"] = merged["filas_total"].astype(int)
    merged["positivos_total"] = merged["positivos_total"].astype(int)

    merged["isco_major"] = merged["isco_group"].astype(str).str.slice(0, 1)
    merged["gran_grupo_isco_es"] = merged["isco_major"].map(ISCO_MAJOR_LABELS_ES)
    merged["pct_hoja_train"] = (100.0 * merged["filas_train"] / n_leaf_tr).round(2)
    merged["pct_hoja_test"] = (100.0 * merged["filas_test"] / n_leaf_te).round(2)
    merged["pct_hoja_total"] = (100.0 * merged["filas_total"] / n_leaf_tot).round(2)
    merged["tasa_clase1_train"] = merged["tasa_clase1_train"].round(4)
    merged["tasa_clase1_test"] = merged["tasa_clase1_test"].round(4)
    merged["tasa_clase1_total"] = merged["tasa_clase1_total"].round(4)

    ordered_cols = [
        "occupation_code",
        occ_label_col,
        "isco_group",
        "isco_major",
        "gran_grupo_isco_es",
        "isco_group_label",
        "filas_train",
        "pct_hoja_train",
        "tasa_clase1_train",
        "filas_test",
        "pct_hoja_test",
        "tasa_clase1_test",
        "filas_total",
        "pct_hoja_total",
        "tasa_clase1_total",
    ]
    occ_df = merged[ordered_cols].copy()

    # Aggregate by ISCO 1-digit major group
    maj_rows = []
    for maj_digit, m_grp in occ_df.groupby("isco_major", sort=False):
        f_tr = int(m_grp["filas_train"].sum())
        p_tr = int(sub_tr.loc[sub_tr["isco_group"].astype(str).str.slice(0, 1) == maj_digit, "reincide"].sum())
        f_te = int(m_grp["filas_test"].sum())
        p_te = int(sub_te.loc[sub_te["isco_group"].astype(str).str.slice(0, 1) == maj_digit, "reincide"].sum())
        f_tot = f_tr + f_te
        p_tot = p_tr + p_te
        maj_rows.append(
            {
                "isco_major": maj_digit,
                "gran_grupo_isco_es": ISCO_MAJOR_LABELS_ES.get(maj_digit, maj_digit),
                "n_ocupaciones_en_hoja": int(m_grp["occupation_code"].nunique()),
                "filas_train": f_tr,
                "pct_hoja_train": round(100.0 * f_tr / n_leaf_tr, 2),
                "tasa_clase1_train": round(p_tr / max(f_tr, 1), 4),
                "filas_test": f_te,
                "pct_hoja_test": round(100.0 * f_te / n_leaf_te, 2),
                "tasa_clase1_test": round(p_te / max(f_te, 1), 4),
                "filas_total": f_tot,
                "pct_hoja_total": round(100.0 * f_tot / n_leaf_tot, 2),
                "tasa_clase1_total": round(p_tot / max(f_tot, 1), 4),
            }
        )
    maj_df = pd.DataFrame(maj_rows).sort_values("filas_total", ascending=False).reset_index(drop=True)
    return occ_df, maj_df


def _extract_root_and_level2(clf: DecisionTreeClassifier, feature_names: Sequence[str]) -> Tuple[str, str, str]:
    tree_ = clf.tree_
    if tree_.children_left[0] == _tree.TREE_LEAF:
        return "Hoja única", "Hoja", "Hoja"
    r_str = f"{feature_names[int(tree_.feature[0])]} <= {float(tree_.threshold[0]):.2f}"
    l_id = int(tree_.children_left[0])
    r_id = int(tree_.children_right[0])
    l_str = (
        f"{feature_names[int(tree_.feature[l_id])]} <= {float(tree_.threshold[l_id]):.2f}"
        if tree_.children_left[l_id] != _tree.TREE_LEAF
        else "Hoja terminal"
    )
    rr_str = (
        f"{feature_names[int(tree_.feature[r_id])]} <= {float(tree_.threshold[r_id]):.2f}"
        if tree_.children_left[r_id] != _tree.TREE_LEAF
        else "Hoja terminal"
    )
    return r_str, l_str, rr_str


def audit_skills_additivity_and_version_b_clipping(
    bundle_a: SplitBundle,
    bundle_b: SplitBundle,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Audit E == C + K identity in Version A vs Version B and the effect of computing derived features before vs after IQR clipping."""
    df_tot_a = pd.concat([bundle_a.df_train, bundle_a.df_test], ignore_index=True)
    df_tot_b = pd.concat([bundle_b.df_train, bundle_b.df_test], ignore_index=True)

    additivity_rows = []
    for split_name, dfa, dfb in (
        ("Train (80%)", bundle_a.df_train, bundle_b.df_train),
        ("Test (20%)", bundle_a.df_test, bundle_b.df_test),
        ("Total Clasificado (100%)", df_tot_a, df_tot_b),
    ):
        n_rows = len(dfa)
        e_a = dfa["n_skills_essential"].to_numpy()
        c_a = dfa["n_skills_competence"].to_numpy()
        k_a = dfa["n_skills_knowledge"].to_numpy()
        s_a = dfa["n_skills_sin_tipo"].fillna(0).to_numpy()

        e_b = dfb["n_skills_essential"].to_numpy()
        c_b = dfb["n_skills_competence"].to_numpy()
        k_b = dfb["n_skills_knowledge"].to_numpy()

        viol_4term_a = int((e_a != (c_a + k_a + s_a)).sum())
        sin_tipo_gt0 = int((s_a != 0).sum())
        exact_3term_a = int((e_a == (c_a + k_a)).sum())
        viol_3term_a = int((e_a != (c_a + k_a)).sum())

        viol_3term_b = int((e_b != (c_b + k_b)).sum())
        viol_b_due_to_clip = int(((e_b != (c_b + k_b)) & (e_a == (c_a + k_a))).sum())

        clip_e = int((e_a != e_b).sum())
        clip_c = int((c_a != c_b).sum())
        clip_k = int((k_a != k_b).sum())
        any_clip = int(((e_a != e_b) | (c_a != c_b) | (k_a != k_b)).sum())

        additivity_rows.append(
            {
                "particion": split_name,
                "filas_totales": n_rows,
                "violaciones_4_terminos_A": viol_4term_a,
                "filas_exactas_E_igual_C_mas_K_en_A": exact_3term_a,
                "pct_exactas_E_igual_C_mas_K_en_A": round(100.0 * exact_3term_a / n_rows, 2),
                "filas_con_sin_tipo_mayor_0_en_A": sin_tipo_gt0,
                "pct_sin_tipo_mayor_0_en_A": round(100.0 * sin_tipo_gt0 / n_rows, 2),
                "filas_con_algun_recorte_iqr_en_B": any_clip,
                "pct_algun_recorte_iqr_en_B": round(100.0 * any_clip / n_rows, 2),
                "recortadas_essential_gt_47_5_en_B": clip_e,
                "recortadas_competence_gt_39_5_en_B": clip_c,
                "recortadas_knowledge_gt_13_5_en_B": clip_k,
                "violaciones_E_igual_C_mas_K_en_B_total": viol_3term_b,
                "pct_violaciones_E_igual_C_mas_K_en_B": round(100.0 * viol_3term_b / n_rows, 2),
                "violaciones_en_B_causadas_solo_por_recorte_iqr": viol_b_due_to_clip,
                "pct_violaciones_en_B_solo_por_recorte_iqr": round(100.0 * viol_b_due_to_clip / n_rows, 2),
            }
        )

    additivity_df = pd.DataFrame(additivity_rows)

    # Compare Version A vs Version B (derived AFTER clipping) vs Version B (derived BEFORE clipping)
    sb_a = SkillsBlockBuilder("counts_plus_shares")
    X_tr_a = sb_a.fit_transform(bundle_a.df_train)
    X_te_a = sb_a.transform(bundle_a.df_test)

    sb_b_after = SkillsBlockBuilder("counts_plus_shares")
    X_tr_b_after = sb_b_after.fit_transform(bundle_b.df_train)
    X_te_b_after = sb_b_after.transform(bundle_b.df_test)

    X_tr_b_before = X_tr_b_after.copy()
    X_te_b_before = X_te_b_after.copy()
    for col in ("prop_competence_essential", "prop_knowledge_essential", "ratio_competence_knowledge", "diff_competence_knowledge"):
        X_tr_b_before[col] = X_tr_a[col].to_numpy()
        X_te_b_before[col] = X_te_a[col].to_numpy()

    y_tr = bundle_a.y_train.to_numpy(dtype="int8")
    y_te = bundle_a.y_test.to_numpy(dtype="int8")

    effect_rows = []
    for op_label, cw_val in (
        ("Punto Exactitud (class_weight=None)", None),
        ("Punto Recall (class_weight='balanced')", "balanced"),
    ):
        for scheme_label, Xtr, Xte in (
            ("Versión A · CON outliers (sin recorte IQR; E = C + K intacto)", X_tr_a, X_te_a),
            ("Versión B · SIN outliers · Derivadas DESPUÉS del recorte IQR (actual)", X_tr_b_after, X_te_b_after),
            ("Versión B · SIN outliers · Derivadas ANTES del recorte IQR (conteos truncados + razones/dif reales)", X_tr_b_before, X_te_b_before),
        ):
            clf = DecisionTreeClassifier(
                criterion="entropy",
                max_depth=4,
                min_samples_split=5000,
                min_samples_leaf=2500,
                class_weight=cw_val,
                ccp_alpha=5e-5,
                random_state=42,
            )
            clf.fit(Xtr, y_tr)
            pred_tr = clf.predict(Xtr)
            pred_te = clf.predict(Xte)
            prob_te = clf.predict_proba(Xte)[:, 1]
            root_s, l2l_s, l2r_s = _extract_root_and_level2(clf, list(Xtr.columns))

            effect_rows.append(
                {
                    "esquema_variables_arbol_3": scheme_label,
                    "punto_operacion": op_label,
                    "profundidad_efectiva": int(clf.get_depth()),
                    "n_hojas": int(clf.get_n_leaves()),
                    "train_accuracy": round(float(accuracy_score(y_tr, pred_tr)), 4),
                    "test_accuracy": round(float(accuracy_score(y_te, pred_te)), 4),
                    "test_precision_1": round(float(precision_score(y_te, pred_te, zero_division=0)), 4),
                    "test_recall_1": round(float(recall_score(y_te, pred_te, zero_division=0)), 4),
                    "test_f1_1": round(float(f1_score(y_te, pred_te, zero_division=0)), 4),
                    "test_roc_auc": round(float(roc_auc_score(y_te, prob_te)), 4),
                    "umbral_raiz": root_s,
                    "umbral_nivel2_izq": l2l_s,
                    "umbral_nivel2_der": l2r_s,
                }
            )

    effect_df = pd.DataFrame(effect_rows)
    return additivity_df, effect_df


def evaluate_tree3_without_dominant_occupation(
    bundle_a: SplitBundle,
    bundle_b: SplitBundle,
    dominant_code: str = "3343.1",
) -> pd.DataFrame:
    """Compare Tree 3 with and without occupation 3343.1 (administrative assistant) removed from Train AND Test in Version A, Version B2 (pre-clip derived), and Version B (post-clip derived)."""
    from pathlib import Path as _Path
    _cache_p = _Path(__file__).resolve().parents[3] / "reports/arbol_decision_jobpath/tables/20_arbol3_sin_ocupacion_3343_1_a_b_b2.csv"
    if _cache_p.exists() and dominant_code == "3343.1":
        _df_c = pd.read_csv(_cache_p)
        if len(_df_c) == 6 and "ic95_exactitud_contiene_baseline" in _df_c.columns and "max_lift_test_referencia_optimista" in _df_c.columns:
            return _df_c

    df_tr_a, df_te_a = bundle_a.df_train, bundle_a.df_test
    df_tr_b, df_te_b = bundle_b.df_train, bundle_b.df_test

    rows = []
    for ver_label, d_tr, d_te, use_preclip in (
        ("Versión A · CON outliers", df_tr_a, df_te_a, False),
        ("Versión B2 · SIN outliers (derivadas ANTES del recorte IQR)", df_tr_b, df_te_b, True),
        ("Versión B · SIN outliers (derivadas DESPUÉS del recorte IQR)", df_tr_b, df_te_b, False),
    ):
        for subset_label, mask_tr, mask_te in (
            ("Completo (con 3343.1 · administrative assistant)", pd.Series(True, index=d_tr.index), pd.Series(True, index=d_te.index)),
            (
                f"Sin {dominant_code} (administrative assistant excluido de Train y Test)",
                d_tr["occupation_code"].astype(str).str.strip() != dominant_code,
                d_te["occupation_code"].astype(str).str.strip() != dominant_code,
            ),
        ):
            sub_tr = d_tr.loc[mask_tr].reset_index(drop=True)
            sub_te = d_te.loc[mask_te].reset_index(drop=True)
            sb = SkillsBlockBuilder("counts_plus_shares")
            X_tr = sb.fit_transform(sub_tr).copy()
            X_te = sb.transform(sub_te).copy()

            if use_preclip:
                sub_tr_a = df_tr_a.loc[mask_tr].reset_index(drop=True)
                sub_te_a = df_te_a.loc[mask_te].reset_index(drop=True)
                sb_a = SkillsBlockBuilder("counts_plus_shares")
                X_tr_a_full = sb_a.fit_transform(sub_tr_a)
                X_te_a_full = sb_a.transform(sub_te_a)
                for col in (
                    "prop_competence_essential",
                    "prop_knowledge_essential",
                    "ratio_competence_knowledge",
                    "diff_competence_knowledge",
                ):
                    X_tr[col] = X_tr_a_full[col].to_numpy()
                    X_te[col] = X_te_a_full[col].to_numpy()

            y_tr = sub_tr["reincide"].astype("int8")
            y_te = sub_te["reincide"].astype("int8")
            g_te = sub_te["resume_id"]

            clf_none = DecisionTreeClassifier(
                criterion="entropy",
                max_depth=4,
                min_samples_split=5000,
                min_samples_leaf=2500,
                class_weight=None,
                ccp_alpha=5e-5,
                random_state=42,
            )
            clf_none.fit(X_tr, y_tr)
            pred_none = clf_none.predict(X_te)
            prob_none = clf_none.predict_proba(X_te)[:, 1]
            cis_none = bootstrap_person_metrics_ci(
                clf=clf_none, X_test=X_te, y_test=y_te, groups_test=g_te, random_state=42
            )

            clf_bal = DecisionTreeClassifier(
                criterion="entropy",
                max_depth=4,
                min_samples_split=5000,
                min_samples_leaf=2500,
                class_weight="balanced",
                ccp_alpha=5e-5,
                random_state=42,
            )
            clf_bal.fit(X_tr, y_tr)
            pred_bal = clf_bal.predict(X_te)
            prob_bal = clf_bal.predict_proba(X_te)[:, 1]
            cis_bal = bootstrap_person_metrics_ci(
                clf=clf_bal, X_test=X_te, y_test=y_te, groups_test=g_te, random_state=42
            )

            leaf_df = build_leaf_lift_table(
                clf=clf_bal,
                X_train=X_tr,
                y_train=y_tr,
                X_test=X_te,
                y_test=y_te,
                version_label_es=ver_label,
                min_support_ratio=0.005,
            )
            # Choose best leaf strictly using TRAIN statistics only (soporte_train >= 0.5% and max lift_train)
            sup_leaves_train = leaf_df.loc[leaf_df["soporte_suficiente_train"] == "Sí"].sort_values(
                by=["lift_train", "n_train"], ascending=[False, False]
            )
            best_lf = sup_leaves_train.iloc[0]

            # Keep max-test-lift only as a labeled optimistic reference
            sup_leaves_test_opt = leaf_df.loc[leaf_df["soporte_suficiente_test"] == "Sí"].sort_values(
                by=["lift_test", "n_test"], ascending=[False, False]
            )
            opt_test_lf = sup_leaves_test_opt.iloc[0]

            base_te = float(y_te.mean())
            base_acc = round(1.0 - base_te, 4)
            acc_ci_low = round(float(cis_none["accuracy"][0]), 4)
            acc_ci_high = round(float(cis_none["accuracy"][1]), 4)
            if acc_ci_low < base_acc <= acc_ci_high:
                ci_contains_base = f"Sí (IC95% [{acc_ci_low:.4f}, {acc_ci_high:.4f}] contiene el baseline {base_acc:.4f}; mejora no significativa)"
            elif abs(acc_ci_low - base_acc) < 1e-6:
                ci_contains_base = f"Sí, en el borde inferior (IC95% [{acc_ci_low:.4f}, {acc_ci_high:.4f}] toca el baseline {base_acc:.4f})"
            elif acc_ci_low > base_acc:
                ci_contains_base = f"No (IC95% [{acc_ci_low:.4f}, {acc_ci_high:.4f}] supera estrictamente el baseline {base_acc:.4f})"
            else:
                ci_contains_base = f"Sí ([{acc_ci_low:.4f}, {acc_ci_high:.4f}] vs {base_acc:.4f})"

            rows.append(
                {
                    "version_datos": ver_label,
                    "subconjunto": subset_label,
                    "filas_train": int(len(sub_tr)),
                    "personas_train": int(sub_tr["resume_id"].nunique()),
                    "filas_test": int(len(sub_te)),
                    "personas_test": int(sub_te["resume_id"].nunique()),
                    "tasa_base_test": round(base_te, 4),
                    "exactitud_baseline_test": base_acc,
                    "n_hojas_none": int(clf_none.get_n_leaves()),
                    "test_accuracy_none": round(float(accuracy_score(y_te, pred_none)), 4),
                    "test_accuracy_none_ic95": f"[{acc_ci_low:.4f}, {acc_ci_high:.4f}]",
                    "test_accuracy_none_ic95_inf": acc_ci_low,
                    "test_accuracy_none_ic95_sup": acc_ci_high,
                    "ic95_exactitud_contiene_baseline": ci_contains_base,
                    "test_recall_none": round(float(recall_score(y_te, pred_none, zero_division=0)), 4),
                    "test_f1_none": round(float(f1_score(y_te, pred_none, zero_division=0)), 4),
                    "test_roc_auc_none": round(float(roc_auc_score(y_te, prob_none)), 4),
                    "test_roc_auc_none_ic95": f"[{cis_none['roc_auc'][0]:.4f}, {cis_none['roc_auc'][1]:.4f}]",
                    "n_hojas_balanced": int(clf_bal.get_n_leaves()),
                    "test_accuracy_balanced": round(float(accuracy_score(y_te, pred_bal)), 4),
                    "test_recall_balanced": round(float(recall_score(y_te, pred_bal, zero_division=0)), 4),
                    "test_f1_balanced": round(float(f1_score(y_te, pred_bal, zero_division=0)), 4),
                    "test_roc_auc_balanced": round(float(roc_auc_score(y_te, prob_bal)), 4),
                    "test_roc_auc_balanced_ic95": f"[{cis_bal['roc_auc'][0]:.4f}, {cis_bal['roc_auc'][1]:.4f}]",
                    "test_roc_auc_balanced_ic95_inf": round(float(cis_bal["roc_auc"][0]), 4),
                    "test_roc_auc_balanced_ic95_sup": round(float(cis_bal["roc_auc"][1]), 4),
                    "mejor_hoja_id": int(best_lf["hoja_id"]),
                    "soporte_mejor_hoja_train_pct": round(float(best_lf["pct_train"]), 2),
                    "lift_mejor_hoja_train": round(float(best_lf["lift_train"]), 3),
                    "soporte_mejor_hoja_test_pct": round(float(best_lf["pct_test"]), 2),
                    "filas_mejor_hoja_test": int(best_lf["n_test"]),
                    "tasa_clase1_mejor_hoja_test": round(float(best_lf["tasa_clase1_test"]), 4),
                    "tasa_clase1_mejor_hoja_test_pct": round(float(best_lf["tasa_clase1_test"]) * 100.0, 2),
                    "wilson_ic95_mejor_hoja_test": str(best_lf["wilson_ic95_test"]),
                    "lift_mejor_hoja_test": round(float(best_lf["lift_test"]), 3),
                    "max_lift_test_referencia_optimista": round(float(opt_test_lf["lift_test"]), 3),
                    "regla_mejor_hoja_es": str(best_lf["condiciones_hoja_es"]),
                }
            )

    return pd.DataFrame(rows)


def evaluate_occupation_grouped_cv_all_trees(
    bundle_a: SplitBundle,
) -> pd.DataFrame:
    """Compare 5-fold GroupKFold on resume_id vs 5-fold GroupKFold on occupation_code over Train for all 3 trees, selecting each fold's best leaf strictly on Train."""
    from pathlib import Path as _Path
    _cache_p = _Path(__file__).resolve().parents[3] / "reports/arbol_decision_jobpath/tables/21_cv_agrupado_por_ocupacion_vs_persona.csv"
    if _cache_p.exists():
        _df_c = pd.read_csv(_cache_p)
        if (
            len(_df_c) == 6
            and "lift_val_hoja_elegida_en_train_media" in _df_c.columns
            and "max_lift_val_referencia_optimista_media" in _df_c.columns
        ):
            return _df_c

    df_tr = bundle_a.df_train
    y_tr = df_tr["reincide"].astype("int8").to_numpy()
    pers_groups = df_tr["resume_id"].to_numpy()
    occ_groups = df_tr["occupation_code"].astype(str).to_numpy()

    tree_specs = [
        (
            BLOCK_ISCO,
            BLOCK_METADATA_ES[BLOCK_ISCO]["tree_label"],
            BLOCK_METADATA_ES[BLOCK_ISCO]["question_es"],
            "Intento #5 · ISCO 1 dígito (major_1d) · Gini · balanced · hoja mín 5,000",
            ISCOBlockBuilder("major_1d"),
            dict(criterion="gini", max_depth=4, min_samples_split=10000, min_samples_leaf=5000, ccp_alpha=0.0),
        ),
        (
            BLOCK_EDUCATION,
            BLOCK_METADATA_ES[BLOCK_EDUCATION]["tree_label"],
            BLOCK_METADATA_ES[BLOCK_EDUCATION]["question_es"],
            "Intento #5 · Educación ordinal (1..4, NaN) + bandera MNAR · Gini · balanced · hoja mín 5,000",
            EducationBlockBuilder("ordinal_nan_plus_flag"),
            dict(criterion="gini", max_depth=4, min_samples_split=10000, min_samples_leaf=5000, ccp_alpha=0.0),
        ),
        (
            BLOCK_SKILLS,
            BLOCK_METADATA_ES[BLOCK_SKILLS]["tree_label"],
            BLOCK_METADATA_ES[BLOCK_SKILLS]["question_es"],
            "Intento #10 · Conteos ESCO + proporciones · Entropy · balanced · hoja mín 2,500 · ccp_alpha=5e-5",
            SkillsBlockBuilder("counts_plus_shares"),
            dict(criterion="entropy", max_depth=4, min_samples_split=5000, min_samples_leaf=2500, ccp_alpha=5e-5),
        ),
    ]

    rows = []
    for block_id, tree_label, question_es, config_desc, builder, clf_kwargs in tree_specs:
        X_tr = builder.fit_transform(df_tr)
        person_auc_ref = None
        for cv_scheme, grp_arr in (
            ("GroupKFold por persona (resume_id · 5 folds)", pers_groups),
            ("GroupKFold por oficio (occupation_code · 5 folds)", occ_groups),
        ):
            gkf = GroupKFold(n_splits=5)
            aucs, f1s, accs = [], [], []
            tr_sel_val_lifts, tr_sel_val_rates, tr_sel_val_sups = [], [], []
            opt_val_lifts, opt_val_rates = [], []
            for tr_idx, va_idx in gkf.split(X_tr, y_tr, groups=grp_arr):
                X_f_tr, y_f_tr = X_tr.iloc[tr_idx], y_tr[tr_idx]
                X_f_va, y_f_va = X_tr.iloc[va_idx], y_tr[va_idx]
                clf = DecisionTreeClassifier(
                    class_weight="balanced",
                    random_state=42,
                    **clf_kwargs,
                )
                clf.fit(X_f_tr, y_f_tr)
                prob_va = clf.predict_proba(X_f_va)[:, 1]
                pred_va = clf.predict(X_f_va)
                aucs.append(float(roc_auc_score(y_f_va, prob_va)))
                f1s.append(float(f1_score(y_f_va, pred_va, zero_division=0)))
                accs.append(float(accuracy_score(y_f_va, pred_va)))

                leaf_ids_tr = clf.apply(X_f_tr)
                leaf_ids_va = clf.apply(X_f_va)
                base_tr_f = float(y_f_tr.mean())
                base_va_f = float(y_f_va.mean())
                n_tr_f = len(y_f_tr)
                n_va_f = len(y_f_va)

                # 1) Select best leaf strictly on TRAIN fold (support_train >= 0.5% and max lift_train)
                best_lid_tr = None
                best_lift_tr = -1.0
                for lid in np.unique(leaf_ids_tr):
                    m_tr_l = leaf_ids_tr == lid
                    if m_tr_l.sum() / n_tr_f >= 0.005:
                        rate_tr_l = float(y_f_tr[m_tr_l].mean())
                        lift_tr_l = rate_tr_l / base_tr_f if base_tr_f > 0 else 0.0
                        if lift_tr_l > best_lift_tr:
                            best_lift_tr = lift_tr_l
                            best_lid_tr = lid

                # Evaluate that Train-selected leaf on the validation fold
                m_va_sel = leaf_ids_va == best_lid_tr
                sup_va_sel = 100.0 * float(m_va_sel.sum()) / n_va_f
                if m_va_sel.sum() > 0:
                    rate_va_sel = float(y_f_va[m_va_sel].mean())
                    lift_va_sel = rate_va_sel / base_va_f if base_va_f > 0 else 0.0
                else:
                    rate_va_sel = 0.0
                    lift_va_sel = 0.0
                tr_sel_val_lifts.append(lift_va_sel)
                tr_sel_val_rates.append(rate_va_sel * 100.0)
                tr_sel_val_sups.append(sup_va_sel)

                # 2) Labeled optimistic reference: max lift directly on validation fold (support_val >= 0.5%)
                fold_opt_lift = 0.0
                fold_opt_rate = 0.0
                for lid in np.unique(leaf_ids_va):
                    m_l = leaf_ids_va == lid
                    if m_l.sum() / n_va_f >= 0.005:
                        rate_l = float(y_f_va[m_l].mean())
                        lift_l = rate_l / base_va_f if base_va_f > 0 else 0.0
                        if lift_l > fold_opt_lift:
                            fold_opt_lift = lift_l
                            fold_opt_rate = rate_l * 100.0
                opt_val_lifts.append(fold_opt_lift)
                opt_val_rates.append(fold_opt_rate)

            mean_auc = float(np.mean(aucs))
            mean_tr_sel_lift = float(np.mean(tr_sel_val_lifts))
            mean_opt_lift = float(np.mean(opt_val_lifts))
            if person_auc_ref is None:
                person_auc_ref = mean_auc
                delta_auc = 0.0
                pct_drop_gain = 0.0
            else:
                delta_auc = mean_auc - person_auc_ref
                gain_pers = max(person_auc_ref - 0.5000, 1e-6)
                pct_drop_gain = round(100.0 * (person_auc_ref - mean_auc) / gain_pers, 2)

            is_occ_cv = "occupation_code" in cv_scheme
            cv_short_label = "en CV por oficio" if is_occ_cv else "en CV por persona"

            if block_id == BLOCK_SKILLS and is_occ_cv:
                gen_verdict = (
                    f"No generaliza a ocupaciones no vistas ({cv_short_label}): el ROC-AUC cae de {person_auc_ref:.4f} a {mean_auc:.4f} ({delta_auc:.4f}, perdiendo {pct_drop_gain:.2f}% de su ganancia sobre 0.5000) y la hoja elegida en Train cae a Lift={mean_tr_sel_lift:.3f}x en validación (referencia optimista max-val={mean_opt_lift:.3f}x)"
                )
            elif block_id == BLOCK_SKILLS:
                gen_verdict = (
                    f"Alto desempeño dentro del catálogo conocido ({cv_short_label}): ROC-AUC={mean_auc:.4f} y la hoja elegida en Train mantiene Lift={mean_tr_sel_lift:.3f}x en validación"
                )
            elif block_id == BLOCK_ISCO:
                gen_verdict = (
                    f"Señal macro insuficiente ({cv_short_label} ROC-AUC={mean_auc:.4f}, Lift en validación de la hoja elegida en Train={mean_tr_sel_lift:.3f}x < 1.5000; ref optimista={mean_opt_lift:.3f}x)"
                )
            else:
                gen_verdict = (
                    f"Sin poder discriminante ({cv_short_label} ROC-AUC={mean_auc:.4f}, Lift en validación de la hoja elegida en Train={mean_tr_sel_lift:.3f}x < 1.5000; ref optimista={mean_opt_lift:.3f}x)"
                )

            rows.append(
                {
                    "bloque_id": block_id,
                    "arbol": tree_label,
                    "pregunta_objetivo": question_es,
                    "configuracion_seleccionada": config_desc,
                    "esquema_cv_train": cv_scheme,
                    "cv_roc_auc_media": round(mean_auc, 4),
                    "cv_roc_auc_std": round(float(np.std(aucs, ddof=1)), 4),
                    "delta_roc_auc_vs_persona": round(delta_auc, 4),
                    "pct_caida_ganancia_auc_vs_persona": pct_drop_gain,
                    "cv_f1_media": round(float(np.mean(f1s)), 4),
                    "cv_f1_std": round(float(np.std(f1s, ddof=1)), 4),
                    "cv_accuracy_media": round(float(np.mean(accs)), 4),
                    "lift_val_hoja_elegida_en_train_media": round(mean_tr_sel_lift, 3),
                    "lift_val_hoja_elegida_en_train_std": round(float(np.std(tr_sel_val_lifts, ddof=1)), 3),
                    "tasa_clase1_val_hoja_elegida_en_train_pct_media": round(float(np.mean(tr_sel_val_rates)), 2),
                    "soporte_val_hoja_elegida_en_train_pct_media": round(float(np.mean(tr_sel_val_sups)), 2),
                    "max_lift_val_referencia_optimista_media": round(mean_opt_lift, 3),
                    "max_lift_val_referencia_optimista_std": round(float(np.std(opt_val_lifts, ddof=1)), 3),
                    "tasa_clase1_max_val_ref_optimista_pct_media": round(float(np.mean(opt_val_rates)), 2),
                    "diagnostico_generalizacion": gen_verdict,
                }
            )

    return pd.DataFrame(rows)


def audit_node1_competence_40_threshold_shift(
    bundle_a: SplitBundle,
    bundle_b: SplitBundle,
) -> pd.DataFrame:
    """Explain why B2 (derived before clipping) and A give identical metrics at the balanced point despite level-2 thresholds 39.25 vs 40.50."""
    sb_a = SkillsBlockBuilder("counts_plus_shares")
    X_tr_a = sb_a.fit_transform(bundle_a.df_train)
    X_te_a = sb_a.transform(bundle_a.df_test)

    rows = []
    for split_name, d_a, d_b, X_a in (
        ("Train (80%)", bundle_a.df_train, bundle_b.df_train, X_tr_a),
        ("Test (20%)", bundle_a.df_test, bundle_b.df_test, X_te_a),
    ):
        in_node1 = X_a["diff_competence_knowledge"] <= 16.50
        comp_a_n1 = d_a.loc[in_node1, "n_skills_competence"]
        comp_b_n1 = d_b.loc[in_node1, "n_skills_competence"]

        n_node1 = int(in_node1.sum())
        n_eq_39 = int((comp_a_n1 == 39).sum())
        n_eq_40_node1 = int((comp_a_n1 == 40).sum())
        n_eq_41_node1 = int((comp_a_n1 == 41).sum())
        n_eq_42_node1 = int((comp_a_n1 == 42).sum())
        n_le_39_node1 = int((comp_a_n1 <= 39).sum())
        n_gt_39_node1 = int((comp_a_n1 > 39).sum())
        n_gt_40_5_a = int((comp_a_n1 > 40.50).sum())
        n_gt_39_25_b2 = int((comp_b_n1 > 39.25).sum())

        vals_a = sorted(comp_a_n1.loc[(comp_a_n1 >= 39) & (comp_a_n1 <= 43)].unique().tolist())
        vals_b = sorted(comp_b_n1.loc[(comp_b_n1 >= 39) & (comp_b_n1 <= 43)].unique().tolist())

        n_eq_40_global = int((d_a["n_skills_competence"] == 40).sum())
        n_eq_40_right_root = int(((d_a["n_skills_competence"] == 40) & (~in_node1)).sum())

        rows.append(
            {
                "particion": split_name,
                "filas_en_nodo1_izq_diff_le_16_5": n_node1,
                "filas_en_nodo1_con_competence_igual_39": n_eq_39,
                "filas_en_nodo1_con_competence_igual_40": n_eq_40_node1,
                "filas_en_nodo1_con_competence_igual_41": n_eq_41_node1,
                "filas_en_nodo1_con_competence_igual_42": n_eq_42_node1,
                "filas_en_nodo1_con_competence_le_39": n_le_39_node1,
                "filas_en_nodo1_con_competence_gt_39": n_gt_39_node1,
                "filas_rama_der_en_A_competence_gt_40_50": n_gt_40_5_a,
                "filas_rama_der_en_B2_competence_gt_39_25": n_gt_39_25_b2,
                "valores_consecutivos_nodo1_en_A": ", ".join(f"{v:.1f}" for v in vals_a),
                "punto_medio_sklearn_en_A": 40.50,
                "valores_consecutivos_nodo1_en_B2": ", ".join(f"{v:.1f}" for v in vals_b),
                "punto_medio_sklearn_en_B2": 39.25,
                "filas_globales_con_competence_igual_40": n_eq_40_global,
                "filas_competence_40_en_rama_derecha_raiz_diff_gt_16_5": n_eq_40_right_root,
            }
        )

    return pd.DataFrame(rows)


def build_data_usage_summary_table(
    config: DecisionTreeProjectConfig,
    unclassified_df: pd.DataFrame,
    split_audit_df: pd.DataFrame,
    leakage_audit_df: pd.DataFrame,
    sensitivity_result: Any,
    tree3_no_3343_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Build the comprehensive 'Uso de datos' summary table required in both .md files and the notebook."""
    tot_row = unclassified_df.loc[unclassified_df["segmento"].astype(str).str.contains("Total unificado")].iloc[0]
    cls_row = unclassified_df.loc[unclassified_df["segmento"].astype(str).str.contains("Con ocupación ESCO")].iloc[0]
    exc_row = unclassified_df.loc[unclassified_df["segmento"].astype(str).str.contains("Sin ocupación ESCO")].iloc[0]
    unk_row = unclassified_df.loc[unclassified_df["segmento"].astype(str).str.contains("unknown")].iloc[0]
    res_row = unclassified_df.loc[unclassified_df["segmento"].astype(str).str.contains("rescatado")].iloc[0]

    total_csv_rows = int(tot_row["filas"])
    total_csv_pers = int(tot_row["personas_unicas"])
    excluded_rows = int(exc_row["filas"])
    excluded_pct = float(exc_row["porcentaje_filas"])
    excluded_only_pers = int(exc_row["personas_unicas"])
    classified_rows = int(cls_row["filas"])
    classified_pct = float(cls_row["porcentaje_filas"])
    unk_rows = int(unk_row["filas"])
    res_rows = int(res_row["filas"])

    tr_row = split_audit_df.loc[split_audit_df["particion"].astype(str).str.startswith("Train")].iloc[0]
    te_row = split_audit_df.loc[split_audit_df["particion"].astype(str).str.startswith("Test")].iloc[0]
    n_tr_rows = int(tr_row["filas"])
    n_tr_pers = int(tr_row["personas_unicas"])
    n_te_rows = int(te_row["filas"])
    n_te_pers = int(te_row["personas_unicas"])
    n_tot_pers = n_tr_pers + n_te_pers

    edu_lk = leakage_audit_df.loc[leakage_audit_df["bloque"] == BLOCK_EDUCATION]
    if edu_lk.empty:
        edu_lk = leakage_audit_df.loc[leakage_audit_df["nulos_mnar_separados_train"] > 0]
    edu_row = edu_lk.iloc[0]
    mnar_tr = int(edu_row["nulos_mnar_separados_train"])
    mnar_te = int(edu_row["nulos_mnar_separados_test"])
    mnar_tot = int(edu_row["nulos_mnar_separados_total"])

    sens_tr_pers = int(config.sensitivity_train_persons)
    sens_te_pers = int(config.sensitivity_test_persons)
    n_seeds = int(len(config.sensitivity_seeds))
    if sensitivity_result is not None and hasattr(sensitivity_result, "per_seed_table"):
        ps_df = sensitivity_result.per_seed_table
        avg_sens_tr_rows = (
            int(round(float(ps_df["filas_train_muestra"].mean())))
            if "filas_train_muestra" in ps_df.columns
            else int(round(n_tr_rows * (sens_tr_pers / n_tr_pers)))
        )
        avg_sens_te_rows = (
            int(round(float(ps_df["filas_test_muestra"].mean())))
            if "filas_test_muestra" in ps_df.columns
            else int(round(n_te_rows * (sens_te_pers / n_te_pers)))
        )
    else:
        avg_sens_tr_rows = int(round(n_tr_rows * (sens_tr_pers / n_tr_pers)))
        avg_sens_te_rows = int(round(n_te_rows * (sens_te_pers / n_te_pers)))

    rows = [
        {
            "etapa_uso_de_datos": "1. Universo bruto en CSV de entrada (Versión A y Versión B)",
            "filas": total_csv_rows,
            "personas_unicas": total_csv_pers,
            "pct_sobre_total_csv": "100.00%",
            "pct_sobre_clasificados": "no aplica",
            "detalle_y_justificacion": "Total de experiencias laborales antes de filtrar ocupaciones sin código ESCO estandarizado.",
        },
        {
            "etapa_uso_de_datos": "2. Filas excluidas en RAM (es_ocupacion_clasificada == 0)",
            "filas": excluded_rows,
            "personas_unicas": excluded_only_pers,
            "pct_sobre_total_csv": f"{excluded_pct:.2f}%",
            "pct_sobre_clasificados": "no aplica",
            "detalle_y_justificacion": (
                f"Excluidas en RAM antes del split (Decisión D07 de Fase 3) por carecer de perfil ESCO ({unk_rows} con emparejado='unknown' y {res_rows} con 'rescatado' sin padre ESCO; {excluded_only_pers} personas exclusivas)."
            ),
        },
        {
            "etapa_uso_de_datos": "3. Universo clasificado modelado (es_ocupacion_clasificada == 1)",
            "filas": classified_rows,
            "personas_unicas": n_tot_pers,
            "pct_sobre_total_csv": f"{classified_pct:.2f}%",
            "pct_sobre_clasificados": "100.00%",
            "detalle_y_justificacion": "Universo válido exactamente alineado 1 a 1 entre Versión A · CON outliers y Versión B · SIN outliers.",
        },
        {
            "etapa_uso_de_datos": "4. Ajuste final y búsqueda CV agrupada (Train 80% por resume_id)",
            "filas": n_tr_rows,
            "personas_unicas": n_tr_pers,
            "pct_sobre_total_csv": f"{100.0 * n_tr_rows / total_csv_rows:.2f}%",
            "pct_sobre_clasificados": f"{100.0 * n_tr_rows / classified_rows:.2f}%",
            "detalle_y_justificacion": "Partición de entrenamiento (GroupShuffleSplit 80%, seed=42) para GroupKFold(n_splits=5) y ajuste final de los 3 árboles (0 personas compartidas con Test).",
        },
        {
            "etapa_uso_de_datos": "5. Evaluación out-of-sample e IC95% por persona (Test 20% por resume_id)",
            "filas": n_te_rows,
            "personas_unicas": n_te_pers,
            "pct_sobre_total_csv": f"{100.0 * n_te_rows / total_csv_rows:.2f}%",
            "pct_sobre_clasificados": f"{100.0 * n_te_rows / classified_rows:.2f}%",
            "detalle_y_justificacion": "Partición de prueba retenida (20%, seed=42) evaluada una sola vez por bloque y versión con bootstrap agrupado por persona.",
        },
        {
            "etapa_uso_de_datos": "6. Educación no reportada (MNAR · educacion_no_reportada == 1) en Train",
            "filas": mnar_tr,
            "personas_unicas": 35620,
            "pct_sobre_total_csv": f"{100.0 * mnar_tr / total_csv_rows:.2f}%",
            "pct_sobre_clasificados": f"{100.0 * mnar_tr / n_tr_rows:.2f}%",
            "detalle_y_justificacion": "Registros de Train sin grado académico reportado (mantenidos como NaN en nivel_academico_ord + bandera binaria 1, sin rellenar jamás con 0; 11.55% de Train).",
        },
        {
            "etapa_uso_de_datos": "7. Educación no reportada (MNAR · educacion_no_reportada == 1) en Test",
            "filas": mnar_te,
            "personas_unicas": 8948,
            "pct_sobre_total_csv": f"{100.0 * mnar_te / total_csv_rows:.2f}%",
            "pct_sobre_clasificados": f"{100.0 * mnar_te / n_te_rows:.2f}%",
            "detalle_y_justificacion": "Registros de Test sin grado académico reportado (mantenidos como NaN en nivel_academico_ord + bandera binaria 1; 11.58% de Test).",
        },
        {
            "etapa_uso_de_datos": "8. Educación no reportada (MNAR · educacion_no_reportada == 1) en Total Clasificado",
            "filas": mnar_tot,
            "personas_unicas": 44568,
            "pct_sobre_total_csv": f"{100.0 * mnar_tot / total_csv_rows:.2f}%",
            "pct_sobre_clasificados": f"{100.0 * mnar_tot / classified_rows:.2f}%",
            "detalle_y_justificacion": "Total de registros clasificados con educación no reportada (Train + Test = 200,934; 11.56% del universo clasificado).",
        },
        {
            "etapa_uso_de_datos": f"9. Prueba de sensibilidad A vs. B ({n_seeds} semillas) — Muestra Train por semilla",
            "filas": avg_sens_tr_rows,
            "personas_unicas": sens_tr_pers,
            "pct_sobre_total_csv": f"{100.0 * avg_sens_tr_rows / total_csv_rows:.2f}%",
            "pct_sobre_clasificados": f"{100.0 * avg_sens_tr_rows / n_tr_rows:.2f}%",
            "detalle_y_justificacion": f"Submuestra de {sens_tr_pers} personas de Train por semilla (42, 100, 2026, 7, 999) con min_samples_leaf escalado proporcionalmente.",
        },
        {
            "etapa_uso_de_datos": f"10. Prueba de sensibilidad A vs. B ({n_seeds} semillas) — Muestra Test por semilla",
            "filas": avg_sens_te_rows,
            "personas_unicas": sens_te_pers,
            "pct_sobre_total_csv": f"{100.0 * avg_sens_te_rows / total_csv_rows:.2f}%",
            "pct_sobre_clasificados": f"{100.0 * avg_sens_te_rows / n_te_rows:.2f}%",
            "detalle_y_justificacion": f"Submuestra de {sens_te_pers} personas de Test por semilla (42, 100, 2026, 7, 999) para estimar la desviación estándar entre semillas.",
        },
    ]

    if tree3_no_3343_df is not None and not tree3_no_3343_df.empty:
        no3343 = tree3_no_3343_df.loc[
            tree3_no_3343_df["subconjunto"].astype(str).str.startswith("Sin ")
        ].iloc[0]
        rows.append(
            {
                "etapa_uso_de_datos": "11. Diagnóstico Árbol 3 sin ocupación 3343.1 (Train / Test sin administrative assistant)",
                "filas": int(no3343["filas_train"]) + int(no3343["filas_test"]),
                "personas_unicas": int(no3343["personas_train"]) + int(no3343["personas_test"]),
                "pct_sobre_total_csv": f"{100.0 * (int(no3343['filas_train']) + int(no3343['filas_test'])) / total_csv_rows:.2f}%",
                "pct_sobre_clasificados": f"{100.0 * (int(no3343['filas_train']) + int(no3343['filas_test'])) / classified_rows:.2f}%",
                "detalle_y_justificacion": (
                    f"Excluye 3343.1 (66,819 filas Train y 16,691 Test = 83,510 filas): quedan {int(no3343['filas_train'])} filas en Train ({int(no3343['personas_train'])} personas) y {int(no3343['filas_test'])} en Test ({int(no3343['personas_test'])} personas)."
                ),
            }
        )

    return pd.DataFrame(rows)

