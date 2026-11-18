"""Configuration and constants for CRISP-DM Phase 4 (Modeling & Evaluation)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Tuple


VERSION_CON: str = "con_outliers"
VERSION_SIN: str = "sin_outliers"

VERSION_LABELS: Dict[str, str] = {
    VERSION_CON: "A · con outliers",
    VERSION_SIN: "B · sin outliers (IQR)",
}

CLEAN_CSV_BY_VERSION: Dict[str, str] = {
    VERSION_CON: "empleos_unificado_limpio.csv",
    VERSION_SIN: "empleos_limpio_con_competencias_sin_outliers.csv",
}

LEAKAGE_FEATURES_IN_X: Tuple[str, ...] = (
    "veces_ese_oficio_rob",
    "veces_ese_oficio_bin",
)

PROHIBITED_CONCEPTUAL_COLUMNS: Tuple[str, ...] = (
    "veces_ese_oficio",
    "veces_ese_oficio_rob",
    "veces_ese_oficio_bin",
    "n_returns",
    "n_nonadjacent_returns",
    "reincide",
    "is_repeated_occupation",
)

COLLINEAR_REDUNDANT_FEATURES: Tuple[str, ...] = (
    "start_year_rob",
    "n_skills_competence_rob",
)

ALL_DENSE_FEATURES_IN_X: Tuple[str, ...] = (
    "start_ord_rob",
    "end_ord_rob",
    "dur_q_rob",
    "n_skills_essential_rob",
    "n_skills_competence_rob",
    "n_skills_knowledge_rob",
    "n_skills_sin_tipo_rob",
    "veces_ese_oficio_rob",
    "start_year_rob",
    "job_order_rob",
    "univ_ord_mm",
    "es_vigente",
    "dur_q_bin",
    "n_skills_essential_bin",
    "veces_ese_oficio_bin",
    "tiene_skills",
    "tiene_knowledge",
    "tiene_sin_tipo",
)


def resolve_project_root(start: Path | None = None) -> Path:
    """Walk up from start until finding the repository root containing data/ and notebooks/."""
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "data").is_dir() and (candidate / "notebooks").is_dir():
            return candidate
    raise FileNotFoundError("Could not locate project root containing data/ and notebooks/.")


@dataclass(frozen=True)
class ModelingConfig:
    """Immutable configuration for Phase 4 modeling and evaluation."""

    project_root: Path
    random_state: int = 42
    cv_folds: int = 5
    test_size: float = 0.20
    leakage_features: Tuple[str, ...] = field(default=LEAKAGE_FEATURES_IN_X)
    collinear_drop_features: Tuple[str, ...] = field(default=COLLINEAR_REDUNDANT_FEATURES)

    @property
    def processed_dir(self) -> Path:
        return self.project_root / "data" / "03_processed"

    @property
    def transformed_dir(self) -> Path:
        return self.project_root / "data" / "04_transformed"

    @property
    def split_map_path(self) -> Path:
        return self.project_root / "reports" / "eda_jobpath" / "tables" / "split_map_resume_id.csv"

    @property
    def reports_dir(self) -> Path:
        return self.project_root / "reports" / "modelado_jobpath"

    @property
    def figures_dir(self) -> Path:
        return self.reports_dir / "figures"

    @property
    def tables_dir(self) -> Path:
        return self.reports_dir / "tables"

    def clean_csv_path(self, version: str) -> Path:
        return self.processed_dir / CLEAN_CSV_BY_VERSION[version]

    def x_path(self, version: str, split: str) -> Path:
        return self.transformed_dir / version / split / f"X_{split}.csv"

    def y_path(self, version: str, split: str) -> Path:
        return self.transformed_dir / version / split / f"y_{split}.csv"

    def transformers_path(self, version: str) -> Path:
        return self.transformed_dir / "transformers" / version / "transformers.joblib"

