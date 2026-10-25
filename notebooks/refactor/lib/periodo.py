"""Fechas trimestrales: Period_Time, ordinales y duracion.

Responsabilidad unica (SOLID-S): todo lo que tenga que ver con
`start_date` y `end_date`. Ninguna otra funcion del paquete los interpreta.

Decisiones documentadas:
- Un trimestre se escribe "Qn AAAA" (n = 1..4).
- `end_date` puede ser "Present" cuando la experiencia sigue vigente.
- `duracion_observada` es NaN para "Present": no se inventa un fin.
- `duracion_a_corte` usa el ultimo trimestre observado como referencia.
"""

from __future__ import annotations

import pandas as pd

PATRON = r"^Q([1-4])\s+(\d{4})$"
VIGENTE = "Present"


def es_trimestre(serie: pd.Series) -> pd.Series:
    """True donde la cadena cumple el formato trimestral."""
    return serie.astype("string").str.match(PATRON).fillna(False)


def ordinal(serie: pd.Series) -> pd.Series:
    """Convierte 'Q3 2012' en un entero comparable (anio * 4 + trimestre).

    Devuelve NA donde no hay trimestre valido ("Present", vacios, texto).
    """
    partes = serie.astype("string").str.extract(PATRON)
    trimestre = pd.to_numeric(partes[0], errors="coerce")
    anio = pd.to_numeric(partes[1], errors="coerce")
    return (anio * 4 + trimestre).astype("Int64")


def crear_period_time(df: pd.DataFrame) -> pd.Series:
    """Une inicio y fin en una etiqueta legible: 'Q1 2011 - Q3 2012'."""
    inicio = df["start_date"].fillna("?")
    fin = df["end_date"].fillna("?")
    return inicio.str.strip() + " - " + fin.str.strip()


def duracion_observada(df: pd.DataFrame) -> pd.Series:
    """Trimestres inclusivos entre inicio y fin. NA si la experiencia es vigente."""
    inicio = ordinal(df["start_date"])
    fin = ordinal(df["end_date"])
    return (fin - inicio + 1).astype("Int64")


def trimestre_de_corte(df: pd.DataFrame) -> int:
    """Ultimo trimestre con fecha de fin real en el dataset."""
    fin = ordinal(df["end_date"]).dropna()
    if fin.empty:
        raise ValueError("No hay trimestres de fin validos para calcular el corte.")
    return int(fin.max())


def duracion_a_corte(df: pd.DataFrame, corte: int | None = None) -> pd.Series:
    """Duracion inclusiva; para 'Present' usa el trimestre de corte."""
    if corte is None:
        corte = trimestre_de_corte(df)
    inicio = ordinal(df["start_date"])
    fin = ordinal(df["end_date"]).fillna(corte)
    return (fin - inicio + 1).astype("Int64")


def resumen_duracion(df: pd.DataFrame) -> dict[str, float]:
    """Cinco numeros de la duracion observada, sin imputar las vigentes."""
    d = duracion_observada(df).dropna()
    return {
        "n_con_fin": int(d.size),
        "n_vigentes": int(df["end_date"].eq(VIGENTE).sum()),
        "min": float(d.min()),
        "q1": float(d.quantile(0.25)),
        "mediana": float(d.median()),
        "q3": float(d.quantile(0.75)),
        "max": float(d.max()),
    }


def validar(df: pd.DataFrame) -> None:
    """Rompe la ejecucion si las fechas no cumplen las reglas del proyecto."""
    if df["start_date"].isna().any():
        raise ValueError("Hay start_date vacios: no se puede construir el periodo.")
    if not es_trimestre(df["start_date"]).all():
        raise ValueError("Hay start_date con formato distinto de 'Qn AAAA'.")

    fin = df["end_date"]
    if not (fin.eq(VIGENTE) | es_trimestre(fin)).all():
        raise ValueError("end_date solo admite 'Qn AAAA' o 'Present'.")

    inicio = ordinal(df["start_date"])
    fin_ord = ordinal(df["end_date"])
    comparables = fin_ord.notna()
    if (fin_ord[comparables] < inicio[comparables]).any():
        raise ValueError("Hay experiencias que terminan antes de empezar.")

    dur = duracion_observada(df).dropna()
    if (dur < 1).any():
        raise ValueError("Hay duraciones menores a un trimestre.")
