"""Perfilado defensivo de columnas para la seccion Select data."""

from typing import Dict, List
import numpy as np
import pandas as pd


IDENTIFIER_COLUMNS = {"resume_id", "matched_code"}
DATE_COLUMNS = {"start_date", "end_date"}
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
ORDINAL_COLUMNS = {"university_level"}
BINARY_COLUMNS = {"es_unknown_ocupacion", "es_rescatado", "es_vigente", "reincide"}
COUNT_COLUMNS = {
    "n_skills_essential",
    "n_skills_competence",
    "n_skills_knowledge",
    "n_skills_sin_tipo",
    "veces_ese_oficio",
}


def classify_column(name: str, series: pd.Series) -> str:
    """Clasifica una columna en una categoria interpretable."""
    if name in IDENTIFIER_COLUMNS or name.endswith("_id"):
        return "identifier"
    if name in DATE_COLUMNS:
        return "date"
    if name in COUNT_COLUMNS:
        return "count"
    if name in BINARY_COLUMNS:
        return "binary"
    if name in {"skills", "knowledge", "sin_tipo"}:
        return "text"
    if series.dtype == bool:
        return "binary"
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().mean() >= 0.8 and name not in NOMINAL_COLUMNS:
        unique = numeric.dropna().unique()
        if len(unique) <= 2:
            return "binary"
        if len(unique) <= 12 and (numeric.dropna() % 1 == 0).all():
            return "ordinal"
        return "continuous numeric"
    return "nominal"


def _relevance_reason(name: str) -> tuple[bool, str]:
    reasons = {
        "resume_id": (False, "Identificador de persona: indispensable para el split por persona, pero no es una feature."),
        "start_date": (True, "Fecha de inicio del empleo: se deriva a ordinal para secuencias y duracion."),
        "end_date": (True, "Fecha de fin o censura Present: define duracion y vigencia."),
        "university_level": (True, "Nivel educativo: jerarquia real, sirve como ordinal."),
        "matched_code": (False, "Codigo JobHop: se interpreta mediante ESCO; occupation_code es la version util."),
        "emparejado": (True, "Estado del cruce ESCO: resume la calidad del emparejado."),
        "occupation_code": (True, "Oficio ESCO: eje central de transiciones, alta cardinalidad controlada."),
        "occupation_label": (False, "Etiqueta del oficio: redundante con el codigo; no aporta al calculo numerico."),
        "isco_group": (True, "Area ocupacional: apoya el analisis de cambio de area."),
        "isco_group_label": (False, "Etiqueta del area: redundante para X; sirve para interpretacion."),
        "isco_level": (False, "Nivel ISCO constante en esta fuente; no aporta variacion."),
        "n_skills_essential": (True, "Demanda de competencias del oficio: contador continuo de ESCO."),
        "n_skills_competence": (True, "Competencias tipo saber-hacer del oficio."),
        "n_skills_knowledge": (True, "Competencias tipo saber del oficio."),
        "n_skills_sin_tipo": (True, "Bucket de relaciones ESCO sin type; completa el total."),
        "veces_ese_oficio": (True, "Reincidencia cuantitativa del mismo oficio."),
        "saber_skills": (False, "Ya queda resumida por saber_skills ok/no_clasificado; se deriva presencia de perfiles."),
        "es_unknown_ocupacion": (True, "Bandera de ausencia de oficio; relevante para trazabilidad."),
        "es_rescatado": (True, "Bandera de codigo recuperado por prefijo."),
        "es_vigente": (True, "Bandera de censura; representa empleos vigentes."),
        "skills": (True, "Lista de competencias; se resume como presencia y puede auditar perfiles."),
        "knowledge": (True, "Lista de conocimientos; se resume como presencia."),
        "sin_tipo": (True, "Lista sin tipo declarado; se resume como presencia."),
        "reincide": (True, "Y auxiliar elegida: indica si la persona repitio el oficio."),
    }
    if name in reasons:
        return reasons[name]
    return (False, "Columna no perfilada manualmente; revisar fuera del flujo principal.")


def profile_columns(df: pd.DataFrame, version: str) -> pd.DataFrame:
    """Devuelve la tabla de perfil para todas las columnas."""
    rows = []
    for col in df.columns:
        series = df[col]
        non_null = series.dropna()
        numeric = pd.to_numeric(series, errors="coerce")
        # Porcentaje de ceros considerando solo valores parseables.
        zero_pct = float((numeric == 0).mean() * 100) if numeric.notna().any() else np.nan
        skew = float(numeric.skew()) if numeric.notna().sum() > 2 else np.nan
        kurt = float(numeric.kurt()) if numeric.notna().sum() > 2 else np.nan
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