"""Data loading, feature engineering, person-level aggregation, and 3-tier stratified sampling for Hierarchical Clustering."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from scripts.ScriptsCsv.Transformacion.date_features import add_date_ordinals, add_job_order

from .config import (
    FORBIDDEN_LEAKAGE_COLS,
    HierarchicalClusteringConfig,
    UNIVERSITY_ORDINAL_MAP,
    VERSION_A,
    VERSION_B,
    VERSION_LABELS_ES,
    V_EXPERIENCE,
    V_PERSON,
)


REQUIRED_CSV_COLS: List[str] = [
    "resume_id",
    "start_date",
    "end_date",
    "university_level",
    "emparejado",
    "occupation_code",
    "occupation_label",
    "isco_group",
    "isco_group_label",
    "n_skills_essential",
    "n_skills_competence",
    "n_skills_knowledge",
    "n_skills_sin_tipo",
    "veces_ese_oficio",
    "es_unknown_ocupacion",
    "es_rescatado",
]


@dataclass
class PreparedClusteringDataset:
    """Container holding experience-level and person-level dataframes plus data usage audit statistics."""

    version_code: str
    version_label_es: str
    raw_total_rows: int
    raw_total_persons: int
    excluded_unclassified_rows: int
    excluded_unknown_rows: int
    excluded_rescatado_rows: int
    excluded_exclusive_persons: int
    classified_total_rows: int
    classified_total_persons: int
    mnar_edu_train_rows: int
    mnar_edu_test_rows: int
    mnar_edu_total_rows: int
    mnar_edu_train_persons: int
    mnar_edu_test_persons: int
    mnar_edu_total_persons: int
    df_experiences: pd.DataFrame
    df_persons: pd.DataFrame


def assert_zero_leakage_in_feature_lists() -> pd.DataFrame:
    """Verify that neither V_PERSON nor V_EXPERIENCE contains any target or target-equivalent column."""
    forbidden = set(FORBIDDEN_LEAKAGE_COLS)
    overlap_person = sorted(set(V_PERSON).intersection(forbidden))
    overlap_exp = sorted(set(V_EXPERIENCE).intersection(forbidden))
    if overlap_person or overlap_exp:
        raise AssertionError(
            f"Target leakage detected in clustering features! Person={overlap_person}, Exp={overlap_exp}"
        )
    if "n_skills_essential" in V_PERSON or "n_skills_essential" in V_EXPERIENCE:
        raise AssertionError(
            "Collinearity violation: n_skills_essential must not be included simultaneously with competence and knowledge!"
        )
    return pd.DataFrame(
        [
            {
                "vista_analitica": "Vista Primaria · Personas / Trayectorias (V_PERSON)",
                "n_variables_clustering": len(V_PERSON),
                "variables_incluidas": ", ".join(V_PERSON),
                "columnas_fuga_detectadas": 0,
                "colinealidad_E_igual_C_mas_K_evitada": "Sí (usa competence, knowledge y prop_competence)",
                "tratamiento_educacion_mnar": "Bandera educacion_no_reportada (0/1) + ordinal imputado con mediana de Train (2.0); sin relleno 0",
                "estado_auditoria": "APROBADO (100% no supervisado)",
            },
            {
                "vista_analitica": "Vista Secundaria · Experiencias / Perfiles ESCO (V_EXPERIENCE)",
                "n_variables_clustering": len(V_EXPERIENCE),
                "variables_incluidas": ", ".join(V_EXPERIENCE),
                "columnas_fuga_detectadas": 0,
                "colinealidad_E_igual_C_mas_K_evitada": "Sí (usa competence, knowledge y prop_competence_essential)",
                "tratamiento_educacion_mnar": "Bandera educacion_no_reportada (0/1) + ordinal imputado con mediana de Train (2.0); sin relleno 0",
                "estado_auditoria": "APROBADO (100% no supervisado)",
            },
        ]
    )


def load_and_prepare_clustering_dataset(
    csv_path: Path,
    split_map_path: Path,
    version_code: str,
) -> PreparedClusteringDataset:
    """Load clean CSV, filter classified ESCO rows in RAM, and build experience-level and person-level datasets."""
    df_raw = pd.read_csv(csv_path, usecols=REQUIRED_CSV_COLS, low_memory=False)
    split_map = pd.read_csv(split_map_path, usecols=["resume_id", "split"])

    raw_total_rows = int(len(df_raw))
    raw_total_persons = int(df_raw["resume_id"].nunique())

    mask_classified = df_raw["occupation_code"].notna()
    df_unclass = df_raw.loc[~mask_classified]
    excluded_unclassified_rows = int(len(df_unclass))
    excluded_unknown_rows = int((df_unclass["emparejado"].astype(str) == "unknown").sum())
    excluded_rescatado_rows = int(excluded_unclassified_rows - excluded_unknown_rows)

    df = df_raw.loc[mask_classified].copy()
    del df_raw, df_unclass

    classified_total_rows = int(len(df))
    classified_total_persons = int(df["resume_id"].nunique())
    excluded_exclusive_persons = int(raw_total_persons - classified_total_persons)

    df = df.merge(split_map, on="resume_id", how="inner")
    if len(df) != classified_total_rows:
        raise AssertionError(
            f"Split map merge changed classified row count: expected {classified_total_rows}, got {len(df)}"
        )

    # Derive quarter ordinals, duration dur_q, and chronological job_order
    df = add_date_ordinals(df, start_col="start_date", end_col="end_date")
    df["dur_q"] = df["dur_q"].clip(lower=1.0).astype("float32")
    df = add_job_order(df, person_col="resume_id", time_col="start_ord")
    df["job_order"] = df["job_order"].astype("float32")

    # Derive competence proportion (avoiding E = C + K redundancy)
    denom = df["n_skills_essential"].clip(lower=1.0)
    df["prop_competence_essential"] = (df["n_skills_competence"] / denom).clip(0.0, 1.0).astype("float32")
    df["diff_competence_knowledge"] = (df["n_skills_competence"] - df["n_skills_knowledge"]).astype("float32")

    # MNAR education handling: binary indicator + median-imputed ordinal (NEVER fill with 0)
    is_mnar = df["university_level"].isna() | df["university_level"].astype(str).str.strip().eq("No reportado")
    df["educacion_no_reportada"] = is_mnar.astype("float32")
    df["nivel_academico_ord"] = df["university_level"].map(UNIVERSITY_ORDINAL_MAP).astype("float32")

    train_mask = df["split"] == "train"
    train_edu_median = float(df.loc[train_mask, "nivel_academico_ord"].median())
    if np.isnan(train_edu_median):
        train_edu_median = 2.0
    df["nivel_academico_ord_imputado"] = df["nivel_academico_ord"].fillna(train_edu_median).astype("float32")
    for col in V_EXPERIENCE:
        if df[col].isna().any():
            df[col] = df[col].fillna(df.loc[train_mask, col].median()).astype("float32")

    mnar_edu_train_rows = int(df.loc[train_mask, "educacion_no_reportada"].sum())
    mnar_edu_test_rows = int(df.loc[~train_mask, "educacion_no_reportada"].sum())
    mnar_edu_total_rows = mnar_edu_train_rows + mnar_edu_test_rows

    # Post-hoc target and ISCO 1-digit group (strictly excluded from X)
    df["reincide"] = (df["veces_ese_oficio"] > 1).astype("int8")
    df["isco_major_1d"] = df["isco_group"].astype(str).str.strip().str[0]

    # Fast vectorized person-level aggregation (352,093 unique classified persons)
    df_persons = _aggregate_experiences_to_persons_fast(df)

    p_train_mask = df_persons["split"] == "train"
    mnar_edu_train_persons = int(df_persons.loc[p_train_mask, "educacion_no_reportada"].sum())
    mnar_edu_test_persons = int(df_persons.loc[~p_train_mask, "educacion_no_reportada"].sum())
    mnar_edu_total_persons = mnar_edu_train_persons + mnar_edu_test_persons

    return PreparedClusteringDataset(
        version_code=version_code,
        version_label_es=VERSION_LABELS_ES[version_code],
        raw_total_rows=raw_total_rows,
        raw_total_persons=raw_total_persons,
        excluded_unclassified_rows=excluded_unclassified_rows,
        excluded_unknown_rows=excluded_unknown_rows,
        excluded_rescatado_rows=excluded_rescatado_rows,
        excluded_exclusive_persons=excluded_exclusive_persons,
        classified_total_rows=classified_total_rows,
        classified_total_persons=classified_total_persons,
        mnar_edu_train_rows=mnar_edu_train_rows,
        mnar_edu_test_rows=mnar_edu_test_rows,
        mnar_edu_total_rows=mnar_edu_total_rows,
        mnar_edu_train_persons=mnar_edu_train_persons,
        mnar_edu_test_persons=mnar_edu_test_persons,
        mnar_edu_total_persons=mnar_edu_total_persons,
        df_experiences=df,
        df_persons=df_persons,
    )


def _aggregate_experiences_to_persons_fast(df_exp: pd.DataFrame) -> pd.DataFrame:
    """Collapse classified experiences to 1 row per resume_id using vectorized groupby operations."""
    grouped = df_exp.groupby("resume_id", sort=True)
    person = grouped.agg(
        split=("split", "first"),
        n_jobs=("resume_id", "size"),
        min_start=("start_ord", "min"),
        max_end=("end_ord", "max"),
        dur_total=("dur_q", "sum"),
        dur_mean=("dur_q", "mean"),
        mean_skills_essential=("n_skills_essential", "mean"),
        mean_skills_competence=("n_skills_competence", "mean"),
        mean_skills_knowledge=("n_skills_knowledge", "mean"),
        mean_prop_competence=("prop_competence_essential", "mean"),
        nivel_academico_ord_imputado=("nivel_academico_ord_imputado", "first"),
        educacion_no_reportada=("educacion_no_reportada", "first"),
        # Post-hoc validation columns ONLY (excluded from V_PERSON)
        n_occ_posthoc=("occupation_code", "nunique"),
        max_veces_posthoc=("veces_ese_oficio", "max"),
        tasa_reincide_persona_posthoc=("reincide", "mean"),
    )
    person["span_q"] = (person["max_end"] - person["min_start"] + 1.0).clip(lower=1.0)
    person["overlap_ratio"] = person["dur_total"] / person["span_q"]
    person["any_repeated_posthoc"] = (person["max_veces_posthoc"] > 1).astype("int8")
    person["exploration_ratio_posthoc"] = person["n_occ_posthoc"] / person["n_jobs"]
    person = person.drop(columns=["min_start", "max_end"])

    # Fast modal ISCO 1-digit group per person without slow Python lambda
    isco_counts = (
        df_exp.groupby(["resume_id", "isco_major_1d"], sort=False)
        .size()
        .reset_index(name="_cnt")
        .sort_values(["resume_id", "_cnt", "isco_major_1d"], ascending=[True, False, True])
        .drop_duplicates("resume_id")
        .set_index("resume_id")["isco_major_1d"]
    )
    person["isco_major_modal_posthoc"] = isco_counts
    person["isco_major_modal_posthoc"] = person["isco_major_modal_posthoc"].fillna("3")
    person = person.reset_index()
    p_train_mask = person["split"] == "train"
    for col in V_PERSON:
        if person[col].isna().any():
            person[col] = person[col].fillna(person.loc[p_train_mask, col].median())
    if person[V_PERSON].isna().any().any():
        raise AssertionError(f"NaN values remaining in V_PERSON: {person[V_PERSON].isna().sum().to_dict()}")
    return person


def draw_stratified_subsample(
    df: pd.DataFrame,
    n_sample: int,
    strata_cols: List[str],
    seed: int,
    split_filter: str = "train",
) -> pd.DataFrame:
    """Draw an exact-size stratified subsample from the specified split without replacement."""
    sub = df.loc[df["split"] == split_filter].copy().reset_index(drop=True)
    stratum_series = sub[strata_cols[0]].astype(str)
    for col in strata_cols[1:]:
        stratum_series = stratum_series + "_" + sub[col].astype(str)
    sub["_stratum"] = stratum_series

    rng = np.random.default_rng(seed)
    proportions = sub["_stratum"].value_counts(normalize=True)

    chosen_indices: List[int] = []
    for stratum, prop in proportions.items():
        idx_pool = sub.index[sub["_stratum"] == stratum].to_numpy()
        k_take = min(len(idx_pool), max(1, int(round(prop * n_sample))))
        picked = rng.choice(idx_pool, size=k_take, replace=False)
        chosen_indices.extend(picked.tolist())

    if len(chosen_indices) > n_sample:
        chosen_indices = rng.choice(chosen_indices, size=n_sample, replace=False).tolist()
    elif len(chosen_indices) < n_sample:
        remaining = np.setdiff1d(sub.index.to_numpy(), np.array(chosen_indices, dtype=int))
        extra = rng.choice(remaining, size=n_sample - len(chosen_indices), replace=False).tolist()
        chosen_indices.extend(extra)

    return sub.loc[sorted(chosen_indices)].drop(columns=["_stratum"]).reset_index(drop=True)


def build_data_usage_and_sampling_table(
    dataset_b: PreparedClusteringDataset,
    config: HierarchicalClusteringConfig,
    exp_sample_rows_3000: int,
) -> pd.DataFrame:
    """Build the comprehensive 'Uso de datos y estrategia de muestreo' table required for both .md files."""
    df_p = dataset_b.df_persons
    df_e = dataset_b.df_experiences

    n_p_tr = int((df_p["split"] == "train").sum())
    n_p_te = int((df_p["split"] == "test").sum())
    n_e_tr = int((df_e["split"] == "train").sum())
    n_e_te = int((df_e["split"] == "test").sum())

    def _pct_raw(val: int) -> str:
        return f"{val / dataset_b.raw_total_rows * 100.0:.2f}%"

    def _pct_cls(val: int) -> str:
        return f"{val / dataset_b.classified_total_rows * 100.0:.2f}%"

    rows = [
        {
            "etapa_uso_de_datos": "1. Universo bruto en CSV de entrada (Versión B y Versión A)",
            "filas_experiencias": dataset_b.raw_total_rows,
            "personas_unicas": dataset_b.raw_total_persons,
            "pct_sobre_total_csv": "100.00%",
            "pct_sobre_clasificados": "no aplica",
            "memoria_matriz_distancias_condensada": "14,002.6 GB (inviable en RAM para linkage O(n^2))",
            "detalle_y_justificacion": "Total de experiencias laborales antes de filtrar ocupaciones sin código ESCO estandarizado.",
        },
        {
            "etapa_uso_de_datos": "2. Filas excluidas en RAM (es_ocupacion_clasificada == 0)",
            "filas_experiencias": dataset_b.excluded_unclassified_rows,
            "personas_unicas": dataset_b.excluded_exclusive_persons,
            "pct_sobre_total_csv": _pct_raw(dataset_b.excluded_unclassified_rows),
            "pct_sobre_clasificados": "no aplica",
            "memoria_matriz_distancias_condensada": "no aplica",
            "detalle_y_justificacion": (
                f"Excluidas en RAM antes de clusterizar (Decisión D07 de Fase 3) por carecer de perfil ESCO "
                f"({dataset_b.excluded_unknown_rows} con emparejado='unknown' y {dataset_b.excluded_rescatado_rows} "
                f"con 'rescatado' sin padre ESCO; {dataset_b.excluded_exclusive_persons} personas exclusivas)."
            ),
        },
        {
            "etapa_uso_de_datos": "3. Universo clasificado modelado (es_ocupacion_clasificada == 1)",
            "filas_experiencias": dataset_b.classified_total_rows,
            "personas_unicas": dataset_b.classified_total_persons,
            "pct_sobre_total_csv": _pct_raw(dataset_b.classified_total_rows),
            "pct_sobre_clasificados": "100.00%",
            "memoria_matriz_distancias_condensada": "12,092.9 GB (experiencias) / 495.9 GB (personas)",
            "detalle_y_justificacion": "Universo válido alineado 1 a 1 entre Versión B (sin outliers IQR, primaria) y Versión A (con outliers, sensibilidad).",
        },
        {
            "etapa_uso_de_datos": "4. Partición Train oficial agrupada por persona (80% · resume_id)",
            "filas_experiencias": n_e_tr,
            "personas_unicas": n_p_tr,
            "pct_sobre_total_csv": _pct_raw(n_e_tr),
            "pct_sobre_clasificados": _pct_cls(n_e_tr),
            "memoria_matriz_distancias_condensada": "7,739.5 GB (experiencias) / 317.4 GB (personas)",
            "detalle_y_justificacion": "Partición de entrenamiento (seed=42, 0 personas compartidas con Test) donde se ajusta StandardScaler y se extraen las muestras jerárquicas.",
        },
        {
            "etapa_uso_de_datos": "5. Partición Test oficial agrupada por persona (20% · resume_id)",
            "filas_experiencias": n_e_te,
            "personas_unicas": n_p_te,
            "pct_sobre_total_csv": _pct_raw(n_e_te),
            "pct_sobre_clasificados": _pct_cls(n_e_te),
            "memoria_matriz_distancias_condensada": "483.7 GB (experiencias) / 19.8 GB (personas)",
            "detalle_y_justificacion": "Partición retenida (20%) para validar estabilidad out-of-sample mediante proyección NearestCentroid en espacio estandarizado.",
        },
        {
            "etapa_uso_de_datos": "6. Educación no reportada (MNAR · educacion_no_reportada == 1) en Train",
            "filas_experiencias": dataset_b.mnar_edu_train_rows,
            "personas_unicas": dataset_b.mnar_edu_train_persons,
            "pct_sobre_total_csv": _pct_raw(dataset_b.mnar_edu_train_rows),
            "pct_sobre_clasificados": f"{dataset_b.mnar_edu_train_rows / n_e_tr * 100.0:.2f}%",
            "memoria_matriz_distancias_condensada": "no aplica",
            "detalle_y_justificacion": "Registros de Train sin grado académico reportado (codificados con bandera binaria 1 + mediana ordinal de Train=2.0, sin rellenar jamás con 0).",
        },
        {
            "etapa_uso_de_datos": "7. Educación no reportada (MNAR · educacion_no_reportada == 1) en Test",
            "filas_experiencias": dataset_b.mnar_edu_test_rows,
            "personas_unicas": dataset_b.mnar_edu_test_persons,
            "pct_sobre_total_csv": _pct_raw(dataset_b.mnar_edu_test_rows),
            "pct_sobre_clasificados": f"{dataset_b.mnar_edu_test_rows / n_e_te * 100.0:.2f}%",
            "memoria_matriz_distancias_condensada": "no aplica",
            "detalle_y_justificacion": "Registros de Test sin grado académico reportado (mantenidos con bandera binaria 1 + mediana ordinal de Train=2.0).",
        },
        {
            "etapa_uso_de_datos": "8. Educación no reportada (MNAR · educacion_no_reportada == 1) en Total Clasificado",
            "filas_experiencias": dataset_b.mnar_edu_total_rows,
            "personas_unicas": dataset_b.mnar_edu_total_persons,
            "pct_sobre_total_csv": _pct_raw(dataset_b.mnar_edu_total_rows),
            "pct_sobre_clasificados": _pct_cls(dataset_b.mnar_edu_total_rows),
            "memoria_matriz_distancias_condensada": "no aplica",
            "detalle_y_justificacion": "Total de registros clasificados con educación no reportada (Train + Test = 200,934 filas; 44,568 personas).",
        },
        {
            "etapa_uso_de_datos": "9. Nivel 1 de Muestreo Jerárquico · Micro-Muestra Visual (n = 60 personas Train)",
            "filas_experiencias": config.micro_sample_n,
            "personas_unicas": config.micro_sample_n,
            "pct_sobre_total_csv": "0.02%",
            "pct_sobre_clasificados": "0.02%",
            "memoria_matriz_distancias_condensada": "0.014 MB (1,770 pares · instantáneo)",
            "detalle_y_justificacion": "Submuestra estratificada por gran grupo ISCO y bandera MNAR (seed=42) para graficar el dendrograma completo con hojas legibles (convención Sesión 9).",
        },
        {
            "etapa_uso_de_datos": "10. Nivel 2 de Muestreo Jerárquico · Muestra de Descubrimiento (n = 3,000 personas Train)",
            "filas_experiencias": exp_sample_rows_3000,
            "personas_unicas": config.discovery_sample_n,
            "pct_sobre_total_csv": f"{exp_sample_rows_3000 / dataset_b.raw_total_rows * 100.0:.2f}%",
            "pct_sobre_clasificados": f"{exp_sample_rows_3000 / dataset_b.classified_total_rows * 100.0:.2f}%",
            "memoria_matriz_distancias_condensada": "36.0 MB (4,498,500 pares · ~0.8 s en SciPy)",
            "detalle_y_justificacion": "Muestra cuantitativa de descubrimiento (3,000 personas Train y submuestra de 3,000 experiencias Train, seed=42) para torneo de linkage y corte óptimo k*.",
        },
        {
            "etapa_uso_de_datos": "11. Nivel 3 de Muestreo · Estabilidad en 5 Semillas (42, 100, 2026, 7, 999) y Proyección Total",
            "filas_experiencias": dataset_b.classified_total_rows,
            "personas_unicas": dataset_b.classified_total_persons,
            "pct_sobre_total_csv": _pct_raw(dataset_b.classified_total_rows),
            "pct_sobre_clasificados": "100.00%",
            "memoria_matriz_distancias_condensada": "36.0 MB por semilla + proyección lineal O(N*k)",
            "detalle_y_justificacion": "5 muestras independientes de 3,000 personas (media ± DE de Silueta/DBI/ARI) y asignación completa de las 352,093 personas y 1,738,738 experiencias vía NearestCentroid.",
        },
    ]
    return pd.DataFrame(rows)
