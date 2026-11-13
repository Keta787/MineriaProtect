"""
Configuration module for the JobPath preprocessing pipeline.

Centralizes relative paths, constants, random seeds, IQR factor, funnel threshold,
and column exclusion lists.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelineConfig:
    """Immutable configuration for the preprocessing pipeline."""

    # Random seed for reproducibility
    seed: int = 42

    # Tukey IQR multiplier
    iqr_factor: float = 1.5

    # Alert threshold (%) for row or person loss in any single funnel step
    funnel_alert_threshold_pct: float = 5.0

    # Input path (relative to MineriaProtect/) - read-only
    input_csv_rel: str = "data/03_processed/empleos_unificado_limpio.csv"

    # Output path for the IQR-winsorized dataset (Version B: without outliers)
    output_dir_rel: str = "data/03_processed"
    output_filename: str = "empleos_limpio_con_competencias_sin_outliers.csv"

    # Grouping key for persons (1:N trajectories; never display individual rows)
    unique_key: str = "resume_id"

    # Composite primary key for experience-level deduplication
    composite_key: tuple = (
        "resume_id",
        "start_date",
        "end_date",
        "university_level",
        "matched_code",
    )

    # Quarter/date columns - NEVER winsorize
    date_quarter_cols: tuple = ("start_date", "end_date")

    # Columns that must NEVER undergo IQR winsorization
    exclude_from_winsorization: tuple = (
        # IDs and codes
        "Resume_id",
        "resume_id",
        "id",
        "ID",
        "Id",
        # ESCO / ISCO occupation codes
        "occupation_code",
        "isco_code",
        "esco_code",
        "matched_code",
        "isco_group",
        # Postal codes
        "postal_code",
        "zip_code",
        "cp",
        # Years / dates
        "year",
        "anio",
        "año",
        "start_date",
        "end_date",
        "start_quarter",
        "end_quarter",
        # Geographic coordinates
        "latitude",
        "longitude",
        "lat",
        "lon",
        # Timestamps
        "timestamp",
        "date",
        "datetime",
    )

    @property
    def is_notebook_env(self) -> bool:
        """Return True when running inside an IPython/Jupyter kernel."""
        try:
            from IPython import get_ipython

            return get_ipython() is not None
        except Exception:
            return False


DEFAULT_CONFIG = PipelineConfig()


def get_project_root() -> Path:
    """Resolve the root directory of the MineriaProtect project."""
    cwd = Path.cwd()

    if cwd.name == "MineriaProtect":
        return cwd
    if (cwd / "MineriaProtect").exists():
        return cwd / "MineriaProtect"

    for parent in [cwd] + list(cwd.parents):
        if parent.name == "MineriaProtect":
            return parent
        if (parent / "scripts" / "ScriptsCsv").exists():
            if parent.name == "MineriaProtect":
                return parent

    return cwd


def get_input_path(config: PipelineConfig = DEFAULT_CONFIG) -> Path:
    """Return the absolute path to the input CSV."""
    root = get_project_root()
    return root / config.input_csv_rel


def get_output_dir(config: PipelineConfig = DEFAULT_CONFIG) -> Path:
    """Return the absolute path to the processed output directory."""
    root = get_project_root()
    return root / config.output_dir_rel


def get_output_path(config: PipelineConfig = DEFAULT_CONFIG) -> Path:
    """Return the absolute path to the winsorized output CSV."""
    return get_output_dir(config) / config.output_filename
