"""Configuration, verified read-only data paths, and visual constants for JobPath Numerical Methods."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple


SEED: int = 42
NUMERICAL_TOL: float = 1e-10
DISTINCT_NODE_TOL: float = 1e-12
CENSORING_PRESENT_ORD: int = 2026 * 4  # 2026-Q1 per JobPath README.md

# Palette inspired by the course Numerical Methods HTML decks (colorblind-safe, high contrast)
PALETTE: Dict[str, str] = {
    "ink": "#1b2340",
    "muted": "#5b6482",
    "grid": "#e3e6f0",
    "indigo": "#4f46e5",
    "teal": "#0d9488",
    "amber": "#d97706",
    "rose": "#e11d48",
    "slate": "#64748b",
}

# Exact verified columns for memory-safe partial loading of large CSVs
PROCESSED_NUMERIC_COLS: Tuple[str, ...] = (
    "resume_id",
    "start_date",
    "end_date",
    "university_level",
    "matched_code",
    "emparejado",
    "occupation_code",
    "occupation_label",
    "isco_group",
    "isco_group_label",
    "isco_level",
    "n_skills_essential",
    "n_skills_competence",
    "n_skills_knowledge",
    "n_skills_sin_tipo",
    "veces_ese_oficio",
    "saber_skills",
    "es_unknown_ocupacion",
    "es_rescatado",
    "es_vigente",
)

TRANSFORMED_DENSE_COLS: Tuple[str, ...] = (
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

PCA_NUMERIC_COLS: Tuple[str, ...] = (
    "start_ord_rob",
    "end_ord_rob",
    "dur_q_rob",
    "n_skills_essential_rob",
    "n_skills_competence_rob",
    "n_skills_knowledge_rob",
    "n_skills_sin_tipo_rob",
    "start_year_rob",
    "job_order_rob",
    "univ_ord_mm",
)

# Verified RobustScaler/MinMaxScaler parameters from data/04_transformed/transformers/*/transformers.joblib
VERIFIED_SCALER_PARAMS: Dict[str, Tuple[float, float]] = {
    "start_ord": (8043.0, 36.0),
    "end_ord": (8052.0, 32.0),
    "dur_q": (5.0, 11.0),
    "n_skills_essential": (20.0, 13.0),
    "n_skills_competence": (18.0, 11.0),
    "n_skills_knowledge": (3.0, 5.0),
    "n_skills_sin_tipo": (0.0, 1.0),
    "veces_ese_oficio": (1.0, 1.0),
    "start_year": (2010.0, 9.0),
    "job_order": (3.0, 3.0),
}

# Verified 50k PCA cumulative variance curves from notebooks/refactor/4.1_PCA_completo.ipynb
VERIFIED_PCA_50K: Dict[str, Tuple[float, ...]] = {
    "con_outliers": (
        0.3291052,
        0.5536032,
        0.7658773,
        0.8776043,
        0.9406563,
        0.9943101,
        0.9988704,
        0.9999543,
        1.0000000,
        1.0000000,
    ),
    "sin_outliers": (
        0.396820,
        0.658927,
        0.805850,
        0.890892,
        0.953598,
        0.992809,
        0.998265,
        0.999568,
        0.999945,
        1.000000,
    ),
}

# Approved 12-figure manifest for the 8-idea core implementation
APPROVED_FIGURES: Tuple[str, ...] = (
    "nm01_rl01_career_steps_panel.png",
    "nm02_rl01_residual_squares_and_extrapolation.png",
    "nm03_rl02_esco_high_vs_low_r2.png",
    "nm04_rl02_isco_major_group_slopes.png",
    "nm05_rl04_annual_drift_and_censoring_extrapolation.png",
    "nm06_rl05_outlier_strategies_and_scale_invariance.png",
    "nm07_lg01_survival_milestones_and_weights.png",
    "nm08_lg01_runge_phenomenon_vs_chebyshev.png",
    "nm09_lg02_pca_forward_and_inverse_lagrange.png",
    "nm10_hyb01_interpolate_vs_fit_four_regimes.png",
    "nm11_hyb01_loocv_and_extrapolation_rubric.png",
    "nm12_hyb02_verification_summary_dashboard.png",
)


def resolve_project_root(start: Path | None = None) -> Path:
    """Locate the MineriaProtect repository root containing data/ and notebooks/."""
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "data").is_dir() and (candidate / "notebooks").is_dir():
            return candidate
        if (candidate / "MineriaProtect" / "data").is_dir():
            return candidate / "MineriaProtect"
    raise FileNotFoundError("Could not locate MineriaProtect root containing data/ and notebooks/.")


@dataclass(frozen=True)
class NumericalMethodsConfig:
    """Immutable path and parameter configuration for Numerical Methods modules."""

    root: Path
    seed: int = SEED
    dpi: int = 150

    @property
    def data_dir(self) -> Path:
        return self.root / "data"

    # 01_raw
    @property
    def raw_train(self) -> Path:
        return self.data_dir / "01_raw" / "JobHop_v2_train.csv"

    @property
    def raw_test(self) -> Path:
        return self.data_dir / "01_raw" / "JobHop_v2_test.csv"

    @property
    def raw_val(self) -> Path:
        return self.data_dir / "01_raw" / "JobHop_v2_val.csv"

    @property
    def raw_isco(self) -> Path:
        return self.data_dir / "01_raw" / "ESCO" / "ISCOGroups_en.csv"

    @property
    def raw_occupations(self) -> Path:
        return self.data_dir / "01_raw" / "ESCO" / "occupations_en.csv"

    @property
    def raw_relations(self) -> Path:
        return self.data_dir / "01_raw" / "SKILLS" / "occupationSkillRelations_en.csv"

    @property
    def raw_skills(self) -> Path:
        return self.data_dir / "01_raw" / "SKILLS" / "skills_en.csv"

    # 02_interim
    @property
    def interim_greenshare(self) -> Path:
        return self.data_dir / "02_interim" / "ESCO" / "greenShareOcc_en_limpio.csv"

    @property
    def interim_isco(self) -> Path:
        return self.data_dir / "02_interim" / "ESCO" / "ISCOGroups_en_limpio.csv"

    @property
    def interim_occupations(self) -> Path:
        return self.data_dir / "02_interim" / "ESCO" / "occupations_en_limpio.csv"

    @property
    def interim_relations(self) -> Path:
        return self.data_dir / "02_interim" / "SKILLS" / "occupationSkillRelations_en_limpio.csv"

    @property
    def interim_skills(self) -> Path:
        return self.data_dir / "02_interim" / "SKILLS" / "skills_en_limpio.csv"

    @property
    def interim_legacy_clean(self) -> Path:
        return self.data_dir / "02_interim" / "Jobhop" / "empleos_limpio.csv"

    @property
    def interim_legacy_no_outliers(self) -> Path:
        # Literal trailing space before .csv preserved per MR-12 (read-only data/)
        return self.data_dir / "02_interim" / "Jobhop" / "empleos_limpio_sin_outliers .csv"

    # 03_processed
    @property
    def processed_version_a(self) -> Path:
        return self.data_dir / "03_processed" / "empleos_unificado_limpio.csv"

    @property
    def processed_version_b(self) -> Path:
        return self.data_dir / "03_processed" / "empleos_limpio_con_competencias_sin_outliers.csv"

    # 04_transformed
    def transformed_x(self, version: str, split: str) -> Path:
        return self.data_dir / "04_transformed" / version / split / f"X_{split}.csv"

    def transformed_y(self, version: str, split: str) -> Path:
        return self.data_dir / "04_transformed" / version / split / f"y_{split}.csv"

    def transformers_joblib(self, version: str) -> Path:
        return self.data_dir / "04_transformed" / "transformers" / version / "transformers.joblib"

    # Upstream reference artifacts (read-only)
    @property
    def split_map_path(self) -> Path:
        return self.root / "reports" / "eda_jobpath" / "tables" / "split_map_resume_id.csv"

    @property
    def pca_50k_notebook(self) -> Path:
        return self.root / "notebooks" / "refactor" / "4.1_PCA_completo.ipynb"

    # Output directories (all new files live here)
    @property
    def reports_dir(self) -> Path:
        return self.root / "reports" / "metodos_numericos_jobpath"

    @property
    def tables_dir(self) -> Path:
        return self.reports_dir / "tables"

    @property
    def figures_dir(self) -> Path:
        return self.reports_dir / "figures"

    @property
    def geogebra_dir(self) -> Path:
        return self.reports_dir / "geogebra"

    @property
    def verification_log_path(self) -> Path:
        return self.reports_dir / "verification_log.md"

    def audit_input_paths(self) -> Tuple[Path, ...]:
        """All read-only input files consumed by the 8-idea core suite."""
        return (
            self.raw_train,
            self.raw_test,
            self.raw_val,
            self.interim_greenshare,
            self.interim_isco,
            self.interim_occupations,
            self.interim_relations,
            self.interim_skills,
            self.interim_legacy_clean,
            self.interim_legacy_no_outliers,
            self.processed_version_a,
            self.processed_version_b,
            self.transformed_x("con_outliers", "train"),
            self.transformed_x("con_outliers", "test"),
            self.transformed_x("sin_outliers", "train"),
            self.transformed_x("sin_outliers", "test"),
            self.transformers_joblib("con_outliers"),
            self.transformers_joblib("sin_outliers"),
            self.split_map_path,
        )


def default_config(start: Path | None = None) -> NumericalMethodsConfig:
    """Create the default immutable configuration anchored at MineriaProtect root."""
    return NumericalMethodsConfig(root=resolve_project_root(start))
