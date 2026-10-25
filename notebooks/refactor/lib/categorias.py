"""Categorias: mapeos honestos y grupos ISCO.

Responsabilidad unica (SOLID-S): convertir categorias de texto a su forma
analitica, sin inventar jerarquias.

Decisiones:
- `university_level` es ordinal REAL para sus cuatro niveles academicos
  (Secondary < Bachelor < Master < PhD). "No reportado" NO es el nivel cero:
  es ausencia, y se marca aparte. Ponerlo en 0 afirmaria que esas personas
  tienen menos educacion que bachiller, y el dato no dice eso.
- `isco_group` viene con cuatro digitos; el gran grupo ISCO es el primero.
"""

from __future__ import annotations

import pandas as pd

NO_REPORTADO = "No reportado"

ORDEN_UNIVERSIDAD = {
    "Secondary school": 1,
    "Bachelor": 2,
    "Master": 3,
    "PhD": 4,
}

NIVELES_VALIDOS = set(ORDEN_UNIVERSIDAD) | {NO_REPORTADO}


def nivel_ordinal(df: pd.DataFrame) -> pd.Series:
    """Nivel academico 1-4. NA para 'No reportado' (no es un cero)."""
    return df["university_level"].map(ORDEN_UNIVERSIDAD).astype("Int64")


def nivel_no_reportado(df: pd.DataFrame) -> pd.Series:
    """Bandera de ausencia del nivel academico (42.807 filas en con_outliers)."""
    return df["university_level"].eq(NO_REPORTADO)


def isco_mayor(df: pd.DataFrame) -> pd.Series:
    """Gran grupo ISCO (primer digito de isco_group): '0'..'9'."""
    grupo = df["isco_group"].astype("string")
    return grupo.str.slice(0, 1).where(grupo.notna())


def resumen_categorias(df: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    """Conteo y porcentaje de cada categoria, con los vacios incluidos."""
    filas = []
    for columna in columnas:
        conteo = df[columna].value_counts(dropna=False)
        for valor, n in conteo.items():
            filas.append(
                {
                    "columna": columna,
                    "valor": "(vacio)" if pd.isna(valor) else valor,
                    "filas": int(n),
                    "porcentaje": round(100 * n / len(df), 2),
                }
            )
    return pd.DataFrame(filas)


def validar(df: pd.DataFrame) -> None:
    """Rompe la ejecucion si aparecen categorias fuera del catalogo."""
    fuera = set(df["university_level"].dropna().unique()) - NIVELES_VALIDOS
    if fuera:
        raise ValueError(f"Niveles academicos no previstos: {fuera}")

    grupo = df["isco_group"].dropna().astype(str)
    if not grupo.str.fullmatch(r"\d{4}").all():
        raise ValueError("isco_group debe tener cuatro digitos cuando existe.")

    if "isco_mayor" in df:
        valores = set(df["isco_mayor"].dropna().unique())
        if not valores <= {str(i) for i in range(10)}:
            raise ValueError(f"Gran grupo ISCO fuera de rango: {valores}")

    if "nivel_ordinal" in df:
        valores = set(df["nivel_ordinal"].dropna().astype(int).unique())
        if not valores <= set(ORDEN_UNIVERSIDAD.values()):
            raise ValueError(f"nivel_ordinal fuera de rango: {valores}")
