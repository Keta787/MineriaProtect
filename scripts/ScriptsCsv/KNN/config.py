"""Configuration, hyperparameter grids, metadata, and paths for Notebook 7.2 (KNN)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Tuple

from scripts.ScriptsCsv.ArbolDecision.config import (
    IQR_WINSOR_BOUNDS_INFO,
    ISCO_MAJOR_LABELS_ES,
)
from scripts.ScriptsCsv.Modelado.config import (
    ALL_DENSE_FEATURES_IN_X,
    CLEAN_CSV_BY_VERSION,
    COLLINEAR_REDUNDANT_FEATURES,
    LEAKAGE_FEATURES_IN_X,
    ModelingConfig,
    PROHIBITED_CONCEPTUAL_COLUMNS,
    VERSION_CON,
    VERSION_LABELS,
    VERSION_SIN,
    resolve_project_root,
)
from scripts.ScriptsCsv.NaiveBayes.config import (
    ALL_DENSE_CLEAN_FEATURES,
    BINARY_DENSE_FEATURES,
    CONTINUOUS_ROB_FEATURES,
    CONTINUOUS_TO_ORIGINAL_COL,
    DENSE_FEATURE_METADATA_ES,
    EDUCATION_ORDER_ES,
    ORDINAL_BIN_FEATURES,
    ORDINAL_FEATURES,
    ORDINAL_MINMAX_FEATURES,
    ORIGINAL_COL_LABELS_ES,
)

GUIDING_QUESTION_ES: str = (
    "¿Qué tan bien anticipa la reincidencia ocupacional un modelo basado en vecinos, "
    "cómo cambia según el grupo ocupacional, y qué costo computacional y qué sensibilidad "
    "a la escala y a los valores extremos implica frente a los árboles y a Naive Bayes?"
)

MODEL_KNN_D: str = "KNN-D"
MODEL_KNN_G: str = "KNN-G"
MODEL_KNN_W: str = "KNN-W"

MODEL_ORDER: Tuple[str, ...] = (MODEL_KNN_D, MODEL_KNN_G, MODEL_KNN_W)

MODEL_LABELS_ES: Dict[str, str] = {
    MODEL_KNN_D: "KNN-D · Bloque denso auditado (11 cols)",
    MODEL_KNN_G: "KNN-G · Denso + 10 grupos ISCO ponderados (21 cols)",
    MODEL_KNN_W: "KNN-W · Denso + 2,967 ocupaciones ESCO ponderadas (2,978 cols)",
}

# Active columns after train-only near-constant audit (< 1% minority dropped)
DEFAULT_NEAR_CONSTANT_THRESHOLD_PCT: float = 1.0

DEFAULT_K_GRID: Tuple[int, ...] = (5, 15, 51, 101, 201, 401)
EXTENDED_K_UPPER_VALUES: Tuple[int, ...] = (601, 801)
DEFAULT_WEIGHTS_GRID: Tuple[str, ...] = ("uniform", "distance")
DEFAULT_DENSE_METRICS_GRID: Tuple[str, ...] = ("euclidean", "manhattan")
DEFAULT_SPARSE_METRICS_GRID: Tuple[str, ...] = ("euclidean",)
DEFAULT_BLOCK_WEIGHT_GRID: Tuple[float, ...] = (0.25, 0.5, 1.0, 2.0, 4.0)
EXTENDED_BLOCK_WEIGHT_LOWER: Tuple[float, ...] = (0.125,)
EXTENDED_BLOCK_WEIGHT_UPPER: Tuple[float, ...] = (8.0,)

ISCO_MAJOR_DIGITS: Tuple[str, ...] = tuple(str(d) for d in range(10))
ISCO_MAJOR_DUMMY_COLS: Tuple[str, ...] = tuple(f"isco_major_{d}" for d in ISCO_MAJOR_DIGITS)


@dataclass(frozen=True)
class KNNConfig:
    """Immutable configuration for Notebook 7.2 (KNN) and its modular package."""

    project_root: Path
    random_state: int = 42
    cv_folds: int = 5
    test_size: float = 0.20
    bootstrap_resamples: int = 300
    min_subgroup_support: int = 200
    near_constant_threshold_pct: float = DEFAULT_NEAR_CONSTANT_THRESHOLD_PCT
    tuning_person_fraction: float = 0.10
    learning_curve_fractions: Tuple[float, ...] = (0.10, 0.25, 0.50)
    pilot_train_persons: int = 10000
    pilot_val_persons: int = 2500
    geometry_ref_rows: int = 50000
    geometry_query_rows: int = 2000
    geometry_k: int = 51
    benchmark_n_queries: int = 5000
    max_projected_hours: float = 4.0
    chunk_size: int = 5000
    n_jobs: int = 4
    k_grid: Tuple[int, ...] = field(default=DEFAULT_K_GRID)
    weights_grid: Tuple[str, ...] = field(default=DEFAULT_WEIGHTS_GRID)
    dense_metrics_grid: Tuple[str, ...] = field(default=DEFAULT_DENSE_METRICS_GRID)
    sparse_metrics_grid: Tuple[str, ...] = field(default=DEFAULT_SPARSE_METRICS_GRID)
    block_weight_grid: Tuple[float, ...] = field(default=DEFAULT_BLOCK_WEIGHT_GRID)
    leakage_features: Tuple[str, ...] = field(default=LEAKAGE_FEATURES_IN_X)
    collinear_drop_features: Tuple[str, ...] = field(default=COLLINEAR_REDUNDANT_FEATURES)

    def to_modeling_config(self) -> ModelingConfig:
        """Convert to the base Phase 4 ModelingConfig expected by ModelingDatasetBuilder."""
        return ModelingConfig(
            project_root=self.project_root,
            random_state=self.random_state,
            cv_folds=self.cv_folds,
            test_size=self.test_size,
            leakage_features=self.leakage_features,
            collinear_drop_features=self.collinear_drop_features,
        )

    @property
    def processed_dir(self) -> Path:
        """Directory containing read-only clean CSV datasets."""
        return self.project_root / "data" / "03_processed"

    @property
    def transformed_dir(self) -> Path:
        """Directory containing read-only transformed matrices and joblib artifacts."""
        return self.project_root / "data" / "04_transformed"

    @property
    def split_map_path(self) -> Path:
        """Path to the person-level train/test split map."""
        return self.project_root / "reports" / "eda_jobpath" / "tables" / "split_map_resume_id.csv"

    @property
    def reports_dir(self) -> Path:
        """Root output directory for Notebook 7.2 artifacts."""
        return self.project_root / "reports" / "knn_jobpath"

    @property
    def figures_dir(self) -> Path:
        """Directory for exported PNG figures."""
        return self.reports_dir / "figures"

    @property
    def tables_dir(self) -> Path:
        """Directory for exported CSV tables."""
        return self.reports_dir / "tables"

    @property
    def cache_dir(self) -> Path:
        """Directory for resumable chunked-prediction disk checkpoints."""
        return self.reports_dir / "cache"

    @property
    def progress_md_path(self) -> Path:
        """Path to the stage-by-stage progress log."""
        return self.reports_dir / "PROGRESS.md"

    @property
    def references_csv_path(self) -> Path:
        """Path to mandatory References 1-3 table from Notebook 7.0."""
        return (
            self.project_root
            / "reports"
            / "arbol_decision_jobpath"
            / "tables"
            / "05b_tres_referencias_obligatorias.csv"
        )

    @property
    def trees_comparison_csv_path(self) -> Path:
        """Path to Decision Trees comparison table from Notebook 7.0."""
        return (
            self.project_root
            / "reports"
            / "arbol_decision_jobpath"
            / "tables"
            / "07_comparacion_tres_arboles_referencias_y_versiones.csv"
        )

    @property
    def phase4_test_csv_path(self) -> Path:
        """Path to Notebook 6.0 test comparison table."""
        return (
            self.project_root
            / "reports"
            / "modelado_jobpath"
            / "tables"
            / "resultados_test_ab.csv"
        )

    @property
    def nb_tables_dir(self) -> Path:
        """Directory containing exported Naive Bayes (7.1) reference tables."""
        return self.project_root / "reports" / "naive_bayes_jobpath" / "tables"

    @property
    def nb_winners_csv_path(self) -> Path:
        """Path to Naive Bayes (7.1) tuned CV winners table."""
        return self.nb_tables_dir / "06b_tuning_ganadores_cv.csv"

    @property
    def nb_test_metrics_csv_path(self) -> Path:
        """Path to Naive Bayes (7.1) Version A test metrics table."""
        return self.nb_tables_dir / "08a_resultados_test_version_a_ic95.csv"

    @property
    def nb_confusion_csv_path(self) -> Path:
        """Path to Naive Bayes (7.1) confusion matrices table."""
        return self.nb_tables_dir / "08b_matrices_confusion_test_a.csv"

    @property
    def nb_calibration_csv_path(self) -> Path:
        """Path to Naive Bayes (7.1) calibration summary table."""
        return self.nb_tables_dir / "09_calibracion_resumen_test_a.csv"

    @property
    def nb_o1_csv_path(self) -> Path:
        """Path to Naive Bayes (7.1) ISCO major group reincidence rates table."""
        return self.nb_tables_dir / "10_o1_tasas_reincidencia_isco_1d.csv"

    @property
    def nb_o2_csv_path(self) -> Path:
        """Path to Naive Bayes (7.1) per-ISCO model performance table."""
        return self.nb_tables_dir / "10_o2_desempeno_modelos_por_isco_1d.csv"

    @property
    def nb_p2_csv_path(self) -> Path:
        """Path to Naive Bayes (7.1) P2 prototype profiles table."""
        return self.nb_tables_dir / "10_p2_descomposicion_aditiva_perfiles.csv"

    @property
    def nb_p3a_csv_path(self) -> Path:
        """Path to Naive Bayes (7.1) P3a risk deciles table."""
        return self.nb_tables_dir / "10_p3a_deciles_riesgo_lift_gain.csv"

    def clean_csv_path(self, version: str = VERSION_CON) -> Path:
        """Return path to the clean unscaled CSV for the specified version."""
        return self.processed_dir / CLEAN_CSV_BY_VERSION[version]


__all__ = [
    "ALL_DENSE_CLEAN_FEATURES",
    "ALL_DENSE_FEATURES_IN_X",
    "BINARY_DENSE_FEATURES",
    "CLEAN_CSV_BY_VERSION",
    "COLLINEAR_REDUNDANT_FEATURES",
    "CONTINUOUS_ROB_FEATURES",
    "CONTINUOUS_TO_ORIGINAL_COL",
    "DEFAULT_BLOCK_WEIGHT_GRID",
    "DEFAULT_DENSE_METRICS_GRID",
    "DEFAULT_K_GRID",
    "DEFAULT_NEAR_CONSTANT_THRESHOLD_PCT",
    "DEFAULT_SPARSE_METRICS_GRID",
    "DEFAULT_WEIGHTS_GRID",
    "DENSE_FEATURE_METADATA_ES",
    "EDUCATION_ORDER_ES",
    "EXTENDED_BLOCK_WEIGHT_LOWER",
    "EXTENDED_BLOCK_WEIGHT_UPPER",
    "EXTENDED_K_UPPER_VALUES",
    "GUIDING_QUESTION_ES",
    "IQR_WINSOR_BOUNDS_INFO",
    "ISCO_MAJOR_DIGITS",
    "ISCO_MAJOR_DUMMY_COLS",
    "ISCO_MAJOR_LABELS_ES",
    "KNNConfig",
    "LEAKAGE_FEATURES_IN_X",
    "MODEL_KNN_D",
    "MODEL_KNN_G",
    "MODEL_KNN_W",
    "MODEL_LABELS_ES",
    "MODEL_ORDER",
    "ORDINAL_BIN_FEATURES",
    "ORDINAL_FEATURES",
    "ORDINAL_MINMAX_FEATURES",
    "ORIGINAL_COL_LABELS_ES",
    "PROHIBITED_CONCEPTUAL_COLUMNS",
    "VERSION_CON",
    "VERSION_LABELS",
    "VERSION_SIN",
    "resolve_project_root",
]
