"""Defensive column profiling for the Select Data stage (CRISP-DM Phase 3)."""

import numpy as np
import pandas as pd


IDENTIFIER_COLUMNS = {"resume_id", "matched_code"}
DATE_COLUMNS = {"start_date", "end_date"}
TEXT_COLUMNS = {"skills", "knowledge", "sin_tipo"}
NOMINAL_COLUMNS = {
    "university_level",
    "emparejado",
    "occupation_code",
    "occupation_label",
    "isco_group",
    "isco_group_label",
    "saber_skills",
    "es_unknown_ocupacion",
    "es_rescatado",
    "es_vigente",
}
ORDINAL_COLUMNS = {"university_level", "univ_ord"}
BINARY_COLUMNS = {
    "es_unknown_ocupacion",
    "es_rescatado",
    "es_vigente",
    "reincide",
    "tiene_skills",
    "tiene_knowledge",
    "tiene_sin_tipo",
}
COUNT_COLUMNS = {
    "n_skills_essential",
    "n_skills_competence",
    "n_skills_knowledge",
    "n_skills_sin_tipo",
    "veces_ese_oficio",
}


def classify_column(name: str, series: pd.Series) -> str:
    """Classify a column into an interpretable structural category."""
    if name in IDENTIFIER_COLUMNS or name.endswith("_id"):
        return "identifier"
    if name in DATE_COLUMNS:
        return "date"
    if name in COUNT_COLUMNS:
        return "count"
    if name in BINARY_COLUMNS:
        return "binary"
    if name in TEXT_COLUMNS:
        return "text"
    if name in ORDINAL_COLUMNS:
        return "ordinal"
    if series.dtype == bool:
        return "binary"
    if name in NOMINAL_COLUMNS:
        return "nominal"
    numeric = (
        series
        if pd.api.types.is_numeric_dtype(series)
        else pd.to_numeric(series, errors="coerce")
    )
    if numeric.notna().mean() >= 0.8:
        unique = numeric.dropna().unique()
        if len(unique) <= 2:
            return "binary"
        if len(unique) <= 12 and (numeric.dropna() % 1 == 0).all():
            return "ordinal"
        return "continuous numeric"
    return "nominal"


def _relevance_reason(name: str) -> tuple[bool, str]:
    reasons = {
        "resume_id": (
            False,
            "Identificador de persona: indispensable para el split por persona, pero no es una feature.",
        ),
        "start_date": (
            True,
            "Fecha de inicio del empleo: se deriva a ordinal para secuencias y duración.",
        ),
        "end_date": (
            True,
            "Fecha de fin o censura Present: define duración y vigencia.",
        ),
        "university_level": (
            True,
            "Nivel educativo: jerarquía real, sirve como ordinal.",
        ),
        "matched_code": (
            False,
            "Código JobHop: se interpreta mediante ESCO; occupation_code es la versión útil.",
        ),
        "emparejado": (
            True,
            "Estado del cruce ESCO: resume la calidad del emparejamiento.",
        ),
        "occupation_code": (
            True,
            "Oficio ESCO: eje central de transiciones, alta cardinalidad controlada.",
        ),
        "occupation_label": (
            False,
            "Etiqueta del oficio: redundante con el código; no aporta al cálculo numérico.",
        ),
        "isco_group": (
            True,
            "Área ocupacional: apoya el análisis de cambio de área.",
        ),
        "isco_group_label": (
            False,
            "Etiqueta del área: redundante para X; sirve para interpretación.",
        ),
        "isco_level": (
            False,
            "Nivel ISCO constante (4.0) en esta fuente; no aporta variación.",
        ),
        "n_skills_essential": (
            True,
            "Demanda de competencias esenciales del oficio: contador continuo de ESCO.",
        ),
        "n_skills_competence": (
            True,
            "Competencias tipo saber-hacer del oficio.",
        ),
        "n_skills_knowledge": (
            True,
            "Competencias tipo saber (conocimientos) del oficio.",
        ),
        "n_skills_sin_tipo": (
            True,
            "Bucket de relaciones ESCO sin tipo; completa el total.",
        ),
        "veces_ese_oficio": (
            True,
            "Reincidencia cuantitativa del mismo oficio en la trayectoria.",
        ),
        "saber_skills": (
            False,
            "Ya queda resumida por saber_skills ok/no_clasificado y banderas de presencia.",
        ),
        "es_unknown_ocupacion": (
            True,
            "Bandera de ausencia de oficio; relevante para trazabilidad.",
        ),
        "es_rescatado": (
            True,
            "Bandera de código recuperado por prefijo jerárquico.",
        ),
        "es_vigente": (
            True,
            "Bandera de censura; representa empleos vigentes (end_date='Present').",
        ),
        "skills": (
            True,
            "Lista de competencias; se resume como bandera tiene_skills.",
        ),
        "knowledge": (
            True,
            "Lista de conocimientos; se resume como bandera tiene_knowledge.",
        ),
        "sin_tipo": (
            True,
            "Lista sin tipo declarado; se resume como bandera tiene_sin_tipo.",
        ),
        "start_ord": (
            True,
            "Trimestre ordinal de inicio (año*4 + trimestre); entra escalado a X.",
        ),
        "end_ord": (
            True,
            "Trimestre ordinal de término o censura (2026-Q1); entra escalado a X.",
        ),
        "dur_q": (
            True,
            "Duración del empleo en trimestres (end_ord - start_ord + 1); entra a X.",
        ),
        "start_year": (
            True,
            "Año de inicio del empleo; entra escalado a X.",
        ),
        "job_order": (
            True,
            "Orden cronológico del empleo dentro de la trayectoria de la persona.",
        ),
        "tiene_skills": (
            True,
            "Bandera binaria 0/1 de presencia de lista de skills ESCO.",
        ),
        "tiene_knowledge": (
            True,
            "Bandera binaria 0/1 de presencia de lista de conocimientos ESCO.",
        ),
        "tiene_sin_tipo": (
            True,
            "Bandera binaria 0/1 de presencia de competencias sin tipo.",
        ),
        "univ_ord": (
            True,
            "Nivel educativo codificado ordinalmente (0..4); se escala con MinMax.",
        ),
        "reincide": (
            True,
            "Y auxiliar elegida: indica si la persona repitió el oficio (veces_ese_oficio > 1).",
        ),
    }
    if name in reasons:
        return reasons[name]
    return (
        False,
        "Columna no perfilada manualmente; revisar fuera del flujo principal.",
    )


def profile_columns(df: pd.DataFrame, version: str) -> pd.DataFrame:
    """Build the complete column profile table for a given dataset version."""
    rows = []
    skip_numeric_parse = (
        DATE_COLUMNS
        | TEXT_COLUMNS
        | {
            "university_level",
            "emparejado",
            "occupation_label",
            "isco_group_label",
            "saber_skills",
        }
    )
    for col in df.columns:
        series = df[col]
        if pd.api.types.is_numeric_dtype(series):
            numeric = series.astype(float)
        elif col in skip_numeric_parse:
            numeric = pd.Series(dtype=float)
        else:
            numeric = pd.to_numeric(series, errors="coerce")

        has_num = len(numeric) > 0 and numeric.notna().any()
        zero_pct = float((numeric == 0).mean() * 100) if has_num else np.nan
        skew = (
            float(numeric.skew())
            if has_num and numeric.notna().sum() > 2
            else np.nan
        )
        kurt = (
            float(numeric.kurt())
            if has_num and numeric.notna().sum() > 2
            else np.nan
        )
        relevant, reason = _relevance_reason(col)
        rows.append(
            {
                "version": version,
                "column": col,
                "dtype": str(series.dtype),
                "n_rows": len(series),
                "n_null": int(series.isna().sum()),
                "null_pct": float(series.isna().mean() * 100),
                "cardinality": int(series.nunique(dropna=True)),
                "zero_pct": zero_pct,
                "skewness": skew,
                "kurtosis": kurt,
                "type_class": classify_column(col, series),
                "relevant": relevant,
                "reason": reason,
            }
        )
    return pd.DataFrame(rows)
