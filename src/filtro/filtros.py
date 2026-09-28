"""Filtros reutilizables para el análisis de los cuadernos del proyecto.

Todo se aplica sobre `data/03_processed/empleos_limpio.csv` (solo lectura).
El CSV se carga con `dtype=str` —regla del proyecto para no perder los ceros a
la izquierda de los códigos ESCO—, lo que deja las banderas `es_*` como texto
'True'/'False'; `_como_bool` las normaliza para que el módulo funcione con y sin
conversión previa en el cuaderno.
Las funciones devuelven copias explícitas para evitar SettingWithCopyWarning.
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


def _como_bool(serie: pd.Series) -> pd.Series:
    """Normaliza una columna de banderas a booleano, sea cual sea su dtype de origen.

    El proyecto lee los CSV con `dtype=str` para no perder los ceros a la
    izquierda de los códigos ESCO ('0110' no puede colisionar con '110'), y eso
    arrastra las banderas `es_*` como los textos 'True'/'False'. Sin esta
    normalización, `int(serie.sum())` concatena las cadenas y revienta con un
    `ValueError` que no dice nada sobre la causa real. Acepta ambos formatos
    para que el módulo sirva con y sin la conversión previa del cuaderno.
    """
    if serie.dtype == bool:
        return serie
    if pd.api.types.is_numeric_dtype(serie):
        return serie.ne(0)
    return serie.astype("string").str.strip().str.lower().isin(("true", "1", "t", "yes"))


def contar_banderas(df: pd.DataFrame, columna: str) -> int:
    """Cuántas filas de `df` tienen esa bandera en True, sea cual sea su dtype.

    Envoltorio público de `_como_bool`, que es privado. Existe porque el error es
    fácil de cometer y **silencioso en un caso**: con la regla `dtype=str` del
    proyecto, `int(df[col].sum())` sobre una bandera concatena las cadenas y
    revienta con un `ValueError` que no señala la causa, mientras que
    `df[col].mean()` sobre la misma columna devuelve `NaN` **sin avisar nada** y
    se propaga como un `nan %` en un texto impreso.

    Toda suma, promedio o proporción sobre una columna `es_*` debe pasar por
    aquí. Devolver `int` y no `Series` porque el conteo es lo que se imprime.
    """
    return int(_como_bool(df[columna]).sum())


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
    return df.loc[_como_bool(df["es_vigente"]).eq(vigentes)].copy()


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
            "vigentes": [int(_como_bool(df["es_vigente"]).sum())],
            "sin_area_isco": [int(df["isco_group"].isna().sum())],
            "sin_ocupacion": [int(df["occupation_label"].isna().sum())],
        }
    )