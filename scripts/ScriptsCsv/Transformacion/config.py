"""Configuration and relative paths for the transformation pipeline (CRISP-DM Phase 3)."""

from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class TransformConfig:
    """Immutable configuration for the transformation stage."""

    data_dir: str = "data"
    processed_dir: str = "03_processed"
    transformed_root: str = "data/04_transformed"
    random_seed: int = 42
    person_col: str = "resume_id"


VERSION_CON: str = "con_outliers"
VERSION_SIN: str = "sin_outliers"
CSV_BY_VERSION = {
    VERSION_CON: "empleos_unificado_limpio.csv",
    VERSION_SIN: "empleos_limpio_con_competencias_sin_outliers.csv",
}


def project_root() -> Path:
    """Resolve the root directory of the MineriaProtect project."""
    cwd = Path.cwd()
    if cwd.name == "MineriaProtect":
        return cwd
    for p in [cwd] + list(cwd.parents):
        if p.name == "MineriaProtect":
            return p
    return cwd


def processed_path(version: str) -> Path:
    """Return the absolute path to the processed input CSV for the given version."""
    if version not in CSV_BY_VERSION:
        raise ValueError(f"Unknown version: {version}")
    return project_root() / "data" / "03_processed" / CSV_BY_VERSION[version]


def transformed_dir(version: str) -> Path:
    """Return the output directory for a transformed version."""
    return project_root() / "data" / "04_transformed" / version


def transformers_dir() -> Path:
    """Return the directory where fitted joblib transformers are stored."""
    return project_root() / "data" / "04_transformed" / "transformers"
