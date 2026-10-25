"""Banderas de competencias y conocimientos.

Responsabilidad unica (SOLID-S): traducir el estado del emparejamiento ESCO
y la presencia de listas a banderas legibles, con sus validaciones.

Por que dos banderas y no una:
- `estado_competencias` responde si el oficio exige ACCIONES.
- `estado_conocimientos` responde si el oficio exige TEMAS.
Ambas comparten el valor `sin_clasificar` (no hay oficio), pero los otros
valores son hechos distintos y no deben sumarse.

Fuente de verdad: `saber_skills`. Nunca el vacio de la lista.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

SIN_CLASIFICAR = "sin_clasificar"


def a_bool(serie: pd.Series) -> pd.Series:
    """Convierte 'True'/'False' (texto) a booleano real."""
    return serie.astype("string").str.lower().eq("true")


def sin_oficio(df: pd.DataFrame) -> pd.Series:
    """True cuando no se pudo emparejar el oficio con ESCO."""
    return df["saber_skills"].ne("ok")


def estado_competencias(df: pd.DataFrame) -> pd.Series:
    """sin_clasificar / sin_competencias / con_competencias."""
    return pd.Series(
        np.select(
            [sin_oficio(df), df["skills"].isna()],
            [SIN_CLASIFICAR, "sin_competencias"],
            default="con_competencias",
        ),
        index=df.index,
        name="estado_competencias",
    )


def estado_conocimientos(df: pd.DataFrame) -> pd.Series:
    """sin_clasificar / sin_conocimientos / con_conocimientos."""
    return pd.Series(
        np.select(
            [sin_oficio(df), df["knowledge"].isna()],
            [SIN_CLASIFICAR, "sin_conocimientos"],
            default="con_conocimientos",
        ),
        index=df.index,
        name="estado_conocimientos",
    )


def agregar_banderas(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve una copia con las dos banderas y el periodo legible."""
    salida = df.copy()
    salida["estado_competencias"] = estado_competencias(df)
    salida["estado_conocimientos"] = estado_conocimientos(df)
    return salida


def resumen_banderas(df: pd.DataFrame) -> pd.DataFrame:
    """Conteo y porcentaje de cada valor, por bandera."""
    filas = []
    for columna in ("estado_competencias", "estado_conocimientos"):
        conteo = df[columna].value_counts()
        for valor, n in conteo.items():
            filas.append(
                {
                    "bandera": columna,
                    "valor": valor,
                    "filas": int(n),
                    "porcentaje": round(100 * n / len(df), 2),
                }
            )
    return pd.DataFrame(filas)


def cruce_banderas(df: pd.DataFrame) -> pd.DataFrame:
    """Tabla cruzada: prueba visible de que las banderas no son lo mismo."""
    return pd.crosstab(
        df["estado_competencias"],
        df["estado_conocimientos"],
        margins=True,
        margins_name="total",
    )


def auditar_falso_positivo(df: pd.DataFrame) -> dict[str, int]:
    """Compara la regla correcta con la ingenua (lista vacia).

    Devuelve los conteos que alimentan la seccion de riesgos del cuaderno.
    """
    lista_vacia = df["skills"].isna() | df["knowledge"].isna()
    verdad = sin_oficio(df)
    return {
        "verdaderos_sin_clasificar": int(verdad.sum()),
        "ingenuos_sin_clasificar": int(lista_vacia.sum()),
        "falsos_positivos": int((lista_vacia & ~verdad).sum()),
        "sin_conocimientos_reales": int(
            (df["estado_conocimientos"].eq("sin_conocimientos")).sum()
        ),
        "sin_competencias_reales": int(
            (df["estado_competencias"].eq("sin_competencias")).sum()
        ),
    }


def validar(df: pd.DataFrame) -> None:
    """Invariantes de las banderas. Si algo se construyo mal, falla aqui."""
    if "estado_competencias" not in df or "estado_conocimientos" not in df:
        raise ValueError("Primero llame a agregar_banderas().")

    verdad = sin_oficio(df)

    # 1. Las dos banderas coinciden exactamente en 'sin_clasificar'.
    sin_comp = df["estado_competencias"].eq(SIN_CLASIFICAR).to_numpy()
    sin_conoc = df["estado_conocimientos"].eq(SIN_CLASIFICAR).to_numpy()
    if not (sin_comp == sin_conoc).all():
        raise AssertionError("Las banderas discrepan en 'sin_clasificar'.")

    # 2. 'sin_clasificar' es lo mismo que saber_skills.
    if not (sin_comp == verdad.to_numpy()).all():
        raise AssertionError("La bandera no coincide con saber_skills.")

    # 3. es_unknown_ocupacion es un SUBCONJUNTO: marca 'unknown', no 'rescatado'.
    #    Nunca debe contradecir a saber_skills, pero puede quedarse corto.
    desconocido = a_bool(df["es_unknown_ocupacion"]).to_numpy()
    if (desconocido & ~verdad.to_numpy()).any():
        raise AssertionError("es_unknown_ocupacion marca como desconocido un oficio clasificado.")
    if (desconocido & ~sin_comp).any():
        raise AssertionError("es_unknown_ocupacion no coincide con la bandera.")

    # 4. Ningun oficio sin clasificar puede tener listas.
    if df.loc[verdad, ["skills", "knowledge"]].notna().any().any():
        raise AssertionError("Hay filas sin oficio con listas no vacias.")

    # 5. Ningun oficio clasificado puede caer en 'sin_clasificar'.
    if (df.loc[~verdad, "estado_competencias"].eq(SIN_CLASIFICAR)).any():
        raise AssertionError("Hay oficios clasificados marcados como sin clasificar.")

    # 6. Coherencia entre valor y lista.
    if df["estado_competencias"].eq("sin_competencias").sum() != int(
        (df["skills"].isna() & ~verdad).sum()
    ):
        raise AssertionError("Conteo inconsistente en estado_competencias.")
    if df["estado_conocimientos"].eq("sin_conocimientos").sum() != int(
        (df["knowledge"].isna() & ~verdad).sum()
    ):
        raise AssertionError("Conteo inconsistente en estado_conocimientos.")


def validar_contadores(df: pd.DataFrame) -> pd.DataFrame:
    """Comprueba que cada contador sea el largo de su lista (filas con oficio)."""
    con_oficio = ~sin_oficio(df)
    muestra = df.loc[con_oficio]
    comprobaciones = {
        "skills vs n_skills_competence": (
            muestra["skills"].fillna("").apply(lambda s: len(s.split("|")) if s else 0)
            == pd.to_numeric(muestra["n_skills_competence"], errors="coerce")
        ),
        "knowledge vs n_skills_knowledge": (
            muestra["knowledge"].fillna("").apply(lambda s: len(s.split("|")) if s else 0)
            == pd.to_numeric(muestra["n_skills_knowledge"], errors="coerce")
        ),
        "sin_tipo vs n_skills_sin_tipo": (
            muestra["sin_tipo"].fillna("").apply(lambda s: len(s.split("|")) if s else 0)
            == pd.to_numeric(muestra["n_skills_sin_tipo"], errors="coerce")
        ),
    }
    return pd.DataFrame(
        {
            "comprobacion": list(comprobaciones),
            "coinciden": [int(v.sum()) for v in comprobaciones.values()],
            "total": [int(len(muestra))] * len(comprobaciones),
            "resultado": ["OK" if v.all() else "FALLA" for v in comprobaciones.values()],
        }
    )
