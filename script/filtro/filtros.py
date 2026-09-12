"""Filtros reutilizables para el libro de análisis (libros/presentacion.ipynb).

Todo se aplica sobre `data/cruce/empleos_limpio.parquet` (solo lectura):
las funciones devuelven copias explícitas para evitar SettingWithCopyWarning.
Ningún filtro imputa valores: las filas sin clasificar se excluyen siempre
reportando su cantidad.

Autor: Grupo de análisis · Sesión 3 · Minería de Datos.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

TRIMESTRE_VALIDO = re.compile(r"^Q([1-4])\s+(\d{4})$")
NIVELES_EDUCATIVOS = {"Secondary school", "Bachelor", "Master", "PhD", "No reportado"}


def _anio_trimestre(serie: pd.Series) -> pd.Series:
    """Año de un trimestre en formato 'Q1 1955' (devuelve NaN si el formato no aplica)."""
    return serie.str.extract(TRIMESTRE_VALIDO, expand=False)[1].astype("float64")


def filtrar_por_nivel_educativo(df: pd.DataFrame, nivel: str) -> pd.DataFrame:
    """Experiencias de personas con un nivel educativo dado.

    El nivel debe estar en el conjunto canónico del dataset,
    incluido 'No reportado', que no se imputa.
    """
    assert nivel in NIVELES_EDUCATIVOS, f"Nivel no contemplado: {nivel!r}"
    return df.loc[df["university_level"].eq(nivel)].copy()


def filtrar_por_grupo_isco(df: pd.DataFrame, grupo: str) -> pd.DataFrame:
    """Experiencias de un grupo ISCO (por etiqueta, p. ej. 'Software and applications developers and analysts')."""
    return df.loc[df["isco_group_label"].eq(grupo)].copy()


def filtrar_sin_area_isco(df: pd.DataFrame) -> pd.DataFrame:
    """Experiencias cuya ocupación no tiene grupo ISCO asignado (unknown)."""
    return df.loc[df["isco_group"].isna()].copy()


def filtrar_por_ocupacion(df: pd.DataFrame, ocupacion: str) -> pd.DataFrame:
    """Experiencias con una etiqueta de ocupación exacta."""
    return df.loc[df["occupation_label"].eq(ocupacion)].copy()


def filtrar_por_periodo(
    df: pd.DataFrame, anio_inicio: int | None = None, anio_fin: int | None = None
) -> pd.DataFrame:
    """Experiencias que inician dentro del rango de años (inclusivo).

    Si un extremo es None no se aplica esa cota. El filtro usa el año
    de `start_date` (inicio), no toca el final.
    """
    anio = _anio_trimestre(df["start_date"])
    mascara = np.ones(len(df), dtype=bool)
    if anio_inicio is not None:
        mascara &= anio >= anio_inicio
    if anio_fin is not None:
        mascara &= anio <= anio_fin
    return df.loc[mascara].copy()


def filtrar_vigentes(df: pd.DataFrame, vigentes: bool = True) -> pd.DataFrame:
    """Experiencias vigentes (es_vigente True) o finalizadas (vigentes=False)."""
    return df.loc[df["es_vigente"].eq(vigentes)].copy()


def resumen(df: pd.DataFrame, segmento: str) -> pd.DataFrame:
    """Bitácora de un segmento: filas, personas, vigentes y sin clasificar.

    Reporta explícitamente lo que se deja fuera de cada selección
    (sin_area / sin_ocupacion) para que ningún descarte quede oculto.
    """
    return pd.DataFrame(
        {
            "segmento": [segmento],
            "filas": [len(df)],
            "personas": [df["resume_id"].nunique()],
            "vigentes": [int(df["es_vigente"].sum())],
            "sin_area_isco": [int(df["isco_group"].isna().sum())],
            "sin_ocupacion": [int(df["occupation_label"].isna().sum())],
        }
    )