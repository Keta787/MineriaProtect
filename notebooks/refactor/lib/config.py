"""Rutas y fuentes del proyecto JobPath.

Responsabilidad unica (SOLID-S): resolver rutas y declarar las fuentes.
No lee archivos, no transforma datos y no imprime nada.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def _raiz_proyecto() -> Path:
    """Sube desde este archivo hasta encontrar la carpeta `data/`."""
    p = Path(__file__).resolve()
    while p != p.parent:
        if (p / "data").is_dir():
            return p
        p = p.parent
    raise FileNotFoundError("No se encontro la carpeta data/ del proyecto")


RAIZ = _raiz_proyecto()
PROCESADOS = RAIZ / "data" / "03_processed"


@dataclass(frozen=True)
class Fuente:
    """Una version del dataset, con su ruta y su criterio."""

    nombre: str
    ruta: Path
    criterio: str


CON_OUTLIERS = Fuente(
    nombre="con_outliers",
    ruta=PROCESADOS / "empleos_limpio_con_competencias.csv",
    criterio="Conserva todas las filas; la cola larga de duracion sigue dentro.",
)

SIN_OUTLIERS = Fuente(
    nombre="sin_outliers",
    ruta=PROCESADOS / "empleos_con_competencias_limpio_sin_outliers.csv",
    criterio="Excluye las filas con duracion fuera del limite de Tukey (IQR 1.5).",
)

FUENTES = {CON_OUTLIERS.nombre: CON_OUTLIERS, SIN_OUTLIERS.nombre: SIN_OUTLIERS}
