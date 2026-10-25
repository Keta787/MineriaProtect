"""Calidad de datos: vacios, duplicados y outliers.

Responsabilidad unica (SOLID-S): medir y describir problemas de calidad.
No imputa, no elimina filas y no escribe archivos.

Regla del curso (sesion 3): un outlier se detecta con estadistica y se decide
con negocio. Aqui solo se mide y se marca; ocultarlo es tarea de la figura.
"""

from __future__ import annotations

import pandas as pd


def resumen_vacios(df: pd.DataFrame) -> pd.DataFrame:
    """Columnas con al menos un vacio, ordenadas de mayor a menor."""
    vacios = df.isna().sum()
    tabla = pd.DataFrame(
        {
            "vacios": vacios,
            "porcentaje": (100 * vacios / len(df)).round(2),
        }
    )
    return tabla[vacios.gt(0)].sort_values("vacios", ascending=False)


def resumen_duplicados(df: pd.DataFrame) -> dict[str, int]:
    """Duplicados exactos y duplicados por llave de negocio."""
    return {
        "filas": int(len(df)),
        "duplicados_exactos": int(df.duplicated().sum()),
        "resume_id_distintos": int(df["resume_id"].nunique()),
        "experiencias_por_persona_max": int(
            df["resume_id"].value_counts().max()
        ),
    }


def limites_iqr(serie: pd.Series, factor: float = 1.5) -> dict[str, float]:
    """Limites de Tukey para una serie numerica."""
    limpia = pd.to_numeric(serie, errors="coerce").dropna()
    q1 = float(limpia.quantile(0.25))
    q3 = float(limpia.quantile(0.75))
    iqr = q3 - q1
    return {
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "inferior": q1 - factor * iqr,
        "superior": q3 + factor * iqr,
    }


def marcar_outliers(
    serie: pd.Series, factor: float = 1.5
) -> pd.Series:
    """True donde el valor cae fuera de los limites de Tukey.

    Los NA no se marcan: no son outliers, son ausencia.
    """
    valores = pd.to_numeric(serie, errors="coerce")
    lim = limites_iqr(valores, factor)
    fuera = (valores < lim["inferior"]) | (valores > lim["superior"])
    return fuera.fillna(False)


def resumen_outliers(
    df: pd.DataFrame, columnas: list[str], factor: float = 1.5
) -> pd.DataFrame:
    """Cuantos outliers tiene cada columna y donde estan sus limites."""
    filas = []
    for columna in columnas:
        lim = limites_iqr(df[columna], factor)
        marca = marcar_outliers(df[columna], factor)
        filas.append(
            {
                "columna": columna,
                "q1": round(lim["q1"], 2),
                "q3": round(lim["q3"], 2),
                "iqr": round(lim["iqr"], 2),
                "limite_inferior": round(lim["inferior"], 2),
                "limite_superior": round(lim["superior"], 2),
                "outliers": int(marca.sum()),
                "porcentaje": round(100 * marca.mean(), 2),
            }
        )
    return pd.DataFrame(filas)


def ocultar(serie: pd.Series, factor: float = 1.5) -> pd.Series:
    """Recorta (winsoriza) solo para graficar. No modifica el DataFrame."""
    valores = pd.to_numeric(serie, errors="coerce").astype(float)
    lim = limites_iqr(valores, factor)
    return valores.clip(float(lim["inferior"]), float(lim["superior"]))


def impacto_outliers(
    df: pd.DataFrame, columna: str, factor: float = 1.5
) -> pd.DataFrame:
    """Compara media y mediana con y sin outliers, sin borrar nada."""
    valores = pd.to_numeric(df[columna], errors="coerce")
    marca = marcar_outliers(df[columna], factor)
    return pd.DataFrame(
        {
            "grupo": ["con outliers", "sin outliers", "total"],
            "filas": [int(marca.sum()), int((~marca).sum()), int(valores.notna().sum())],
            "media": [
                round(float(valores[marca].mean()), 2),
                round(float(valores[~marca].mean()), 2),
                round(float(valores.mean()), 2),
            ],
            "mediana": [
                round(float(valores[marca].median()), 2),
                round(float(valores[~marca].median()), 2),
                round(float(valores.median()), 2),
            ],
        }
    )
