"""
Enriquece los datasets de empleos con las competencias agrupadas por oficio.

Cada archivo de empleos se procesa de forma independiente. Los originales no
se modifican: se escriben copias nuevas con las columnas `skills`,
`knowledge` y `sin_tipo`, unidas por `occupation_code`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def _raiz_proyecto() -> Path:
    p = Path(__file__).resolve().parent
    while not (p / "data").exists() and p != p.parent:
        p = p.parent
    return p


RAIZ = _raiz_proyecto()
PROC = RAIZ / "data" / "03_processed"
COMPETENCIAS = PROC / "competencias_por_oficio.csv"

FUENTES = (
    (
        (PROC / "empleos.csv", PROC / "empleos .csv"),
        PROC / "empleos_con_competencias.csv",
    ),
    (
        (PROC / "empleos_limpio.csv",),
        PROC / "empleos_limpio_con_competencias.csv",
    ),
)

COLUMNAS_COMPETENCIAS = ["skills", "knowledge", "sin_tipo"]
CLAVE = "occupation_code"


def _cargar(ruta: Path) -> pd.DataFrame:
    return pd.read_csv(
        ruta,
        dtype=str,
        encoding="utf-8",
        keep_default_na=False,
        na_values=[""],
    )


def _enriquecer(
    empleos: pd.DataFrame, competencias: pd.DataFrame, origen: Path
) -> pd.DataFrame:
    if CLAVE not in empleos.columns:
        raise AssertionError(f"{origen.name} no contiene la llave {CLAVE!r}")
    if CLAVE not in competencias.columns:
        raise AssertionError(f"La tabla de competencias no contiene {CLAVE!r}")

    faltantes = [c for c in COLUMNAS_COMPETENCIAS if c not in competencias.columns]
    if faltantes:
        raise AssertionError(f"Faltan columnas de competencias: {faltantes}")

    repetidas = competencias[CLAVE].duplicated().sum()
    assert repetidas == 0, (
        f"La tabla de competencias tiene {repetidas:,} códigos repetidos; "
        "la unión dejaría de ser N:1"
    )
    existentes = set(empleos.columns)
    conflicto = sorted(existentes.intersection(COLUMNAS_COMPETENCIAS))
    assert not conflicto, (
        f"{origen.name} ya contiene columnas que no se deben sobrescribir: {conflicto}"
    )

    # La clave se conserva una sola vez porque solo se seleccionan las columnas
    # nuevas del lado derecho.
    derecha = competencias[[CLAVE, *COLUMNAS_COMPETENCIAS]]
    resultado = empleos.merge(
        derecha,
        on=CLAVE,
        how="left",
        sort=False,
        validate="many_to_one",
        indicator=True,
    )
    assert len(resultado) == len(empleos), (
        f"La unión alteró el número de filas de {origen.name}: "
        f"{len(empleos):,} -> {len(resultado):,}"
    )

    # No se asignan competencias a filas sin código. En pandas, el código vacío
    # no debe coincidir por accidente con otro valor vacío.
    sin_codigo = empleos[CLAVE].isna() | empleos[CLAVE].eq("")
    if sin_codigo.any():
        assert resultado.loc[sin_codigo, "_merge"].eq("left_only").all(), (
            f"Filas sin {CLAVE} recibieron competencias en {origen.name}"
        )
        assert resultado.loc[sin_codigo, COLUMNAS_COMPETENCIAS].isna().all().all(), (
            f"Filas sin {CLAVE} no quedaron vacías en {origen.name}"
        )

    resultado = resultado.drop(columns="_merge")
    assert list(resultado.columns) == [*empleos.columns, *COLUMNAS_COMPETENCIAS]
    return resultado


def main() -> None:
    if not COMPETENCIAS.exists():
        raise FileNotFoundError(f"No existe {COMPETENCIAS}")

    competencias = _cargar(COMPETENCIAS)
    assert competencias[CLAVE].is_unique, (
        "competencias_por_oficio.csv debe tener un solo registro por occupation_code"
    )
    print(f"Competencias: {len(competencias):,} oficios")

    for candidatos, salida in FUENTES:
        origen = next((ruta for ruta in candidatos if ruta.exists()), None)
        if origen is None:
            raise FileNotFoundError(
                "No existe ninguna fuente candidata: "
                + ", ".join(str(ruta) for ruta in candidatos)
            )
        empleos = _cargar(origen)
        enriquecido = _enriquecer(empleos, competencias, origen)
        salida.parent.mkdir(parents=True, exist_ok=True)
        enriquecido.to_csv(salida, index=False, encoding="utf-8")
        coincidencias = int(
            enriquecido[COLUMNAS_COMPETENCIAS].notna().any(axis=1).sum()
        )
        print(
            f"{origen.name}: {len(empleos):,} filas -> {salida.name}; "
            f"filas con competencias: {coincidencias:,}"
        )

    print("Los archivos originales no fueron modificados.")


if __name__ == "__main__":
    main()
