"""Indicadores reutilizables para el libro de análisis (libros/presentacion.ipynb).

Derivados calculados en vivo a partir de `data/cruce/empleos_limpio.parquet`:

- Duración de cada experiencia en trimestres (fórmula inclusiva; `Present` → NaN).
- Distribuciones (IQR de Tukey) y concentración por ocupación / grupo ISCO.
- Transiciones consecutivas entre grupos ISCO por persona.
- Brechas sin empleo registrado (proxy de desempleo), previa fusión de
  periodos solapados para no confundir pluriempleo con desempleo.

Práctica: las funciones son puras (sin I/O) para que el libro decida qué
muestra y cómo lo interpreta.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

SENTINELA_FIN = 99_999  # fin ordinal de 'Present': última experiencia censurada
TRIMESTRE_VALIDO = re.compile(r"^Q([1-4])\s+(\d{4})$")


def _ordinal_trimestre(serie: pd.Series) -> pd.Series:
    """Ordinal continuo de un trimestre 'Q4 2010' -> 2010*4 + 4 = 8044."""
    partes = serie.str.extract(TRIMESTRE_VALIDO, expand=False)
    anio = partes[1].astype("float64")
    trim = partes[0].astype("float64")
    return (anio * 4 + trim).astype("float64")


def _ordenar_empleos(
    df: pd.DataFrame, columnas: list[str]
) -> "tuple[pd.DataFrame, pd.Series, pd.Series]":
    """Ordena experiencias de cada persona por (inicio, fin) y devuelve ordin.

    `Present` recibe el sentinel SENTINELA_FIN y su duración será NaN.
    """
    trabajo = df[["resume_id", "start_date", "end_date", *columnas]].copy()
    ini = _ordinal_trimestre(trabajo["start_date"])
    fin = _ordinal_trimestre(trabajo["end_date"])
    cod = trabajo["end_date"].ne("Present")
    trabajo = trabajo.assign(
        _ini=ini,
        _fin=fin.where(cod, SENTINELA_FIN),
    ).sort_values(["resume_id", "_ini", "_fin"], kind="stable")
    return trabajo, trabajo["_ini"], trabajo["_fin"]


def duracion_trimestres(df: pd.DataFrame) -> pd.Series:
    """Duración inclusiva de cada experiencia (ordinal_fin - ordinal_ini + 1).

    `Present` no tiene fin observado: se devuelve NaN (censura), nunca 0.
    """
    trabajo, ini, fin = _ordenar_empleos(df, [])
    observada = trabajo["end_date"].notna() & trabajo["end_date"].ne("Present")
    return (fin - ini + 1).where(observada)


def distribucion_duracion(df: pd.DataFrame) -> pd.DataFrame:
    """Resumen de duración (finalizadas): mediana, IQR de Tukey y outliers.

    Se calcula sobre duraciones observadas; no se imputa ni se gana.
    Un periodo finalizado puede durar 1 trimestre como mínimo.
    """
    dur = duracion_trimestres(df).dropna()
    q1, q3 = dur.quantile([0.25, 0.75])
    iqr = q3 - q1
    lim_inf, lim_sup = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    fuera = dur[(dur < lim_inf) | (dur > lim_sup)]
    return pd.DataFrame(
        {
            "n_finalizadas": [int(dur.size)],
            "mediana": [float(dur.median())],
            "media": [round(float(dur.mean()), 2)],
            "q1": [float(q1)],
            "q3": [float(q3)],
            "iqr": [float(iqr)],
            "min": [float(dur.min())],
            "max": [float(dur.max())],
            "fuera_de_iqr_n": [int(fuera.size)],
            "fuera_de_iqr_%": [round(100 * fuera.size / dur.size, 2)],
        }
    )


def duracion_mediana_por_grupo(df: pd.DataFrame, top: int = 15) -> pd.DataFrame:
    """Mediana de duración por grupo ISCO (grupos más frecuentes)."""
    grupo = df[["isco_group_label", "start_date", "end_date", "resume_id"]].copy()
    grupo = grupo.dropna(subset=["isco_group_label"])
    grupo = grupo.assign(dur=duracion_trimestres(grupo)).dropna(subset=["dur"])
    resumen = (
        grupo.groupby("isco_group_label")["dur"]
        .agg(mediana="median", n_empleos="size")
        .sort_values("n_empleos", ascending=False)
        .head(top)
    )
    return resumen.round(2)


def duracion_mediana_por_nivel(df: pd.DataFrame) -> pd.DataFrame:
    """Mediana de duración por nivel educativo."""
    sub = df[["university_level", "start_date", "end_date", "resume_id"]].copy()
    sub = sub.assign(dur=duracion_trimestres(sub)).dropna(subset=["dur"])
    return (
        sub.groupby("university_level")["dur"]
        .agg(mediana="median", n_empleos="size")
        .round(2)
    )


def top_valores(serie: pd.Series, n: int = 10) -> pd.DataFrame:
    """Top n de una columna categórica (% sobre el total con etiqueta)."""
    vc = serie.dropna().value_counts().head(n).rename("n")
    total = int(serie.notna().sum())
    out = vc.to_frame()
    out["%_de_con_etiqueta"] = (out["n"] / total * 100).round(2)
    return out


def crosstab_nivel_grupo(df: pd.DataFrame, top: int = 30) -> pd.DataFrame:
    """% de filas por fila-nivel: frecuencia relativa de grupos ISCO por nivel."""
    top_grupos = df["isco_group_label"].dropna().value_counts().head(top).index
    sub = df[df["isco_group_label"].isin(top_grupos)]
    cruce = pd.crosstab(sub["university_level"], sub["isco_group_label"])
    return (cruce.div(cruce.sum(axis=1), axis=0) * 100).round(2)


def _repetidas_exactas(df: pd.DataFrame) -> pd.DataFrame:
    """Quita filas repetidas (resume_id, start, end) para transiciones/solape.

    El pipeline ya marcó estas 74.357 repeticiones; mantenerlas inflaría
    los indicadores de transición y pluriempleo con ruido.
    """
    return df.drop_duplicates(subset=["resume_id", "start_date", "end_date"], keep="first")


def transiciones_consecutivas(df: pd.DataFrame, columna: str = "isco_group_label") -> pd.DataFrame:
    """Pares consecutivos (desde -> hacia) por persona, ordenados por fecha.

    Solo cuenta parejas con ambas etiquetas conocidas; la primera experiencia
    de una persona no tiene 'desde' anterior y la última no tiene 'hacia'.
    """
    trabajo, _, _ = _ordenar_empleos(_repetidas_exactas(df), [columna])
    desde = trabajo[columna]
    hacia = trabajo.groupby("resume_id")[columna].shift(-1)
    parejas = trabajo.loc[desde.notna() & hacia.notna(), ["resume_id"]].copy()
    parejas["desde"] = desde[parejas.index]
    parejas["hacia"] = hacia[parejas.index]
    return (
        parejas.groupby(["desde", "hacia"], dropna=False)
        .size()
        .rename("n")
        .reset_index()
        .sort_values("n", ascending=False)
    )


def proporcion_mismo_grupo(df: pd.DataFrame) -> float:
    """% de transiciones consecutivas que conservan el grupo ISCO."""
    trans = transiciones_consecutivas(df)
    total = int(trans["n"].sum())
    if total == 0:
        return 0.0
    mismo = int(trans.loc[trans["desde"].eq(trans["hacia"]), "n"].sum())
    return 100 * mismo / total


def primera_a_segunda(df: pd.DataFrame, columna: str = "isco_group_label") -> pd.DataFrame:
    """De la primera a la segunda experiencia de cada persona."""
    trabajo, _, _ = _ordenar_empleos(_repetidas_exactas(df), [columna])
    orden = trabajo.groupby("resume_id").cumcount()
    primera = trabajo.loc[orden.eq(0), ["resume_id", columna]].copy()
    segunda = trabajo.loc[orden.eq(1), ["resume_id", columna]].copy()
    parejas = primera.merge(
        segunda, on="resume_id", suffixes=("_primera", "_segunda")
    ).dropna(subset=[f"{columna}_primera", f"{columna}_segunda"])
    return (
        parejas.groupby([f"{columna}_primera", f"{columna}_segunda"], dropna=False)
        .size()
        .rename("n")
        .reset_index()
        .sort_values("n", ascending=False)
    )


def brechas_entre_empleos(df: pd.DataFrame) -> "tuple[pd.DataFrame, dict[str, float | int]]":
    """Períodos sin empleo registrado por persona (proxy de desempleo).

    Se ordena por (inicio, fin) y se usa el máximo de fines previos para
    fusionar periodos solapados: si el siguiente inicio cae dentro (o
    pegado al) empleo previo, la brecha es <= 0 y se cuenta como 0.

    Brecha positiva = trimestres sin empleo registrado entre experiencias.
    `Present` censura el final: su fila no produce brecha (asume continuidad
    hasta el corte; la limitación se declara en el libro).
    """
    trabajo, ini, _ = _ordenar_empleos(df, [])
    fin_max_previo = (
        trabajo.groupby("resume_id")["_fin"].cummax().groupby(trabajo["resume_id"]).shift(1)
    )
    brecha = (ini - fin_max_previo - 1).where(fin_max_previo.notna(), 0.0)
    trabajo = trabajo.assign(
        brecha=brecha.clip(lower=0.0),
        con_brecha=brecha > 0,
    )
    positivo = trabajo.loc[trabajo["con_brecha"], "brecha"]
    resumen: dict[str, float | int] = {
        "personas": int(trabajo["resume_id"].nunique()),
        "personas_con_brecha": int(trabajo.groupby("resume_id")["con_brecha"].any().sum()),
        "brechas": int(trabajo["con_brecha"].sum()),
        "mediana_trimestres": float(positivo.median()) if len(positivo) else np.nan,
        "max_trimestres": float(positivo.max()) if len(positivo) else np.nan,
    }
    columnas_salida = ["resume_id", "start_date", "end_date", "brecha", "con_brecha"]
    return trabajo[columnas_salida], resumen


def brechas_por_nivel(df: pd.DataFrame) -> pd.DataFrame:
    """Personas con brecha (n y %) y mediana de su mayor brecha por nivel."""
    brechas, _ = brechas_entre_empleos(df)
    mayor = (
        brechas.loc[brechas["con_brecha"], ["resume_id", "brecha"]]
        .groupby("resume_id")["brecha"]
        .max()
        .rename("max_brecha")
    ).reset_index()
    nivel = df[["resume_id", "university_level"]].drop_duplicates()
    mayor = mayor.merge(nivel, on="resume_id", how="left")
    base = nivel.groupby("university_level")["resume_id"].count().rename("personas_nivel")
    resumen = (
        mayor.groupby("university_level")
        .agg(personas_con_brecha=("resume_id", "nunique"), mediana_brecha=("max_brecha", "median"))
        .join(base)
    )
    resumen["%_con_brecha"] = (resumen["personas_con_brecha"] / resumen["personas_nivel"] * 100).round(2)
    return resumen.round(2)


def resumen_personas_solapadas(df: pd.DataFrame) -> pd.DataFrame:
    """Traslapes entre experiencias consecutivas de la misma persona.

    Usa el mismo método del diagnóstico (`contarFilasSolapadas`): comparar
    cada inicio con el **fin de la fila anterior** de la persona (tras ordenar
    por inicio/fin). Es una medición conservadora de pluriempleo / datos
    imprecisos; brechas no se ve afectada por ellos.
    """
    trabajo, ini, _ = _ordenar_empleos(df, [])
    fin_anterior = trabajo.groupby("resume_id")["_fin"].shift(1)
    traslapada = ini <= fin_anterior
    filas = int(traslapada.sum())
    personas = int(trabajo.loc[traslapada, "resume_id"].nunique())
    return pd.DataFrame(
        {
            "metrica": ["filas_traslapadas", "personas_traslapadas", "personas_total", "%_personas"],
            "valor": [
                filas,
                personas,
                int(df["resume_id"].nunique()),
                round(100 * personas / df["resume_id"].nunique(), 2),
            ],
        }
    )


def resumen_banderas(df: pd.DataFrame) -> pd.DataFrame:
    """Conteo de las banderas de clasificación del pipeline."""
    return pd.DataFrame(
        {
            "flag": ["es_unknown_ocupacion", "es_rescatado", "es_vigente"],
            "n": [
                int(df["es_unknown_ocupacion"].sum()),
                int(df["es_rescatado"].sum()),
                int(df["es_vigente"].sum()),
            ],
            "%_del_total": [
                round(100 * df["es_unknown_ocupacion"].mean(), 2),
                round(100 * df["es_rescatado"].mean(), 2),
                round(100 * df["es_vigente"].mean(), 2),
            ],
        }
    )