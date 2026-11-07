"""Configuracion y rutas relativas para la transformacion (fase CRISP-DM 3)."""

from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class TransformConfig:
    data_dir: str = "data"
    processed_dir: str = "03_processed"
    transformed_root: str = "data/04_transformed"
    random_seed: int = 42
    person_col: str = "resume_id"


VERSION_CON: str = "con_outliers"
VERSION_SIN: str = "sin_outliers"
CSV_BY_VERSION = {
    VERSION_CON: "empleos_limpio_con_competencias.csv",
    VERSION_SIN: "empleos_limpio_con_competencias_sin_outliers.csv",
}


def project_root() -> Path:
    cwd = Path.cwd()
    if cwd.name == "MineriaProtect":
        return cwd
    for p in [cwd] + list(cwd.parents):
        if p.name == "MineriaProtect":
            return p
    return cwd


def processed_path(version: str) -> Path:
    if version not in CSV_BY_VERSION:
        raise ValueError(f"Version desconocida: {version}")
    return project_root() / "data" / "03_processed" / CSV_BY_VERSION[version]


def transformed_dir(version: str) -> Path:
    return project_root() / "data" / "04_transformed" / version


def transformers_dir() -> Path:
    return project_root() / "data" / "04_transformed" / "transformers"
