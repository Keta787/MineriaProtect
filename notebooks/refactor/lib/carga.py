"""Lectura e inventario del dataset.

Responsabilidad unica (SOLID-S): convertir un CSV en un DataFrame tipado
y describir su estructura. No limpia, no imputa y no escribe archivos.

Regla del proyecto: el CSV crudo es intocable. Este modulo solo lee.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .columnas import COLUMNAS
from .config import Fuente


def leer(fuente: Fuente, columnas: list[str] | None = None) -> pd.DataFrame:
    """Lee una fuente como texto, sin inferir tipos ni convertir vacios en cero.

    Se lee como `str` a proposito: los codigos ESCO tienen ceros a la izquierda
    y los contadores se convierten despues, de forma explicita.
    """
    if not fuente.ruta.exists():
        raise FileNotFoundError(
            f"No existe {fuente.ruta}. Verifique data/03_processed/."
        )
    return pd.read_csv(
        fuente.ruta,
        dtype=str,
        encoding="utf-8",
        keep_default_na=False,
        na_values=[""],
        usecols=columnas,
    )


def contar_filas(fuente: Fuente) -> int:
    """Cuenta filas de datos sin cargar el archivo completo en memoria."""
    if not fuente.ruta.exists():
        raise FileNotFoundError(f"No existe {fuente.ruta}")
    lineas = 0
    with open(fuente.ruta, "rb") as fh:
        while True:
            bloque = fh.read(1 << 24)
            if not bloque:
                break
            lineas += bloque.count(b"\n")
    return max(lineas - 1, 0)  # descuenta el encabezado


def inventario(df: pd.DataFrame) -> pd.DataFrame:
    """Describe cada columna: rol, dtype, vacios y valores distintos."""
    filas = []
    for col in COLUMNAS:
        if col.nombre not in df.columns:
            continue
        serie = df[col.nombre]
        filas.append(
            {
                "columna": col.nombre,
                "rol": col.rol,
                "dtype": str(serie.dtype),
                "vacios": int(serie.isna().sum()),
                "distintos": int(serie.nunique(dropna=True)),
                "entra_a_x": col.entra_a_x,
                "descripcion": col.descripcion,
            }
        )
    return pd.DataFrame(filas)


def conteo_valores(df: pd.DataFrame, columna: str, limite: int = 10) -> pd.Series:
    """Frecuencias de una columna, con los vacios incluidos y ordenadas."""
    return (
        df[columna]
        .value_counts(dropna=False)
        .head(limite)
        .rename("filas")
        .to_frame()
    )
