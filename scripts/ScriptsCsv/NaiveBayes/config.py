"""Configuration, feature taxonomy, and constants for Notebook 7.1 (Naive Bayes)."""

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

GUIDING_QUESTION_ES: str = (
    "¿Qué patrones de reincidencia ocupacional captura un modelo probabilístico ingenuo, "
    "cómo cambian según el grupo ocupacional, y qué tan bien los captura aun con outliers?"
)

MODEL_NB_G: str = "NB-G"
MODEL_NB_G_STAR: str = "NB-G*"
MODEL_NB_B: str = "NB-B"
MODEL_NB_H: str = "NB-H"

MODEL_ORDER: Tuple[str, ...] = (MODEL_NB_G, MODEL_NB_B, MODEL_NB_H)

MODEL_LABELS_ES: Dict[str, str] = {
    MODEL_NB_G: "NB-G · GaussianNB (14 cols densas)",
    MODEL_NB_G_STAR: "NB-G* · GaussianNB sin binarias/ordinales casi constantes (< 1 %)",
    MODEL_NB_B: "NB-B · BernoulliNB (4 binarias + 2,967 dummies)",
    MODEL_NB_H: "NB-H · HybridNaiveBayes (10 num/ord + 2,971 binarias)",
}

CONTINUOUS_ROB_FEATURES: Tuple[str, ...] = (
    "start_ord_rob",
    "end_ord_rob",
    "dur_q_rob",
    "n_skills_essential_rob",
    "n_skills_knowledge_rob",
    "n_skills_sin_tipo_rob",
    "job_order_rob",
)

ORDINAL_MINMAX_FEATURES: Tuple[str, ...] = ("univ_ord_mm",)

ORDINAL_BIN_FEATURES: Tuple[str, ...] = (
    "dur_q_bin",
    "n_skills_essential_bin",
)

ORDINAL_FEATURES: Tuple[str, ...] = ORDINAL_MINMAX_FEATURES + ORDINAL_BIN_FEATURES

GAUSSIAN_HYBRID_FEATURES: Tuple[str, ...] = CONTINUOUS_ROB_FEATURES + ORDINAL_FEATURES

BINARY_DENSE_FEATURES: Tuple[str, ...] = (
    "es_vigente",
    "tiene_skills",
    "tiene_knowledge",
    "tiene_sin_tipo",
)

ALL_DENSE_CLEAN_FEATURES: Tuple[str, ...] = (
    "start_ord_rob",
    "end_ord_rob",
    "dur_q_rob",
    "n_skills_essential_rob",
    "n_skills_knowledge_rob",
    "n_skills_sin_tipo_rob",
    "job_order_rob",
    "univ_ord_mm",
    "es_vigente",
    "dur_q_bin",
    "n_skills_essential_bin",
    "tiene_skills",
    "tiene_knowledge",
    "tiene_sin_tipo",
)

CONTINUOUS_TO_ORIGINAL_COL: Dict[str, str] = {
    "start_ord_rob": "start_ord",
    "end_ord_rob": "end_ord",
    "dur_q_rob": "dur_q",
    "n_skills_essential_rob": "n_skills_essential",
    "n_skills_knowledge_rob": "n_skills_knowledge",
    "n_skills_sin_tipo_rob": "n_skills_sin_tipo",
    "job_order_rob": "job_order",
}

ORIGINAL_COL_LABELS_ES: Dict[str, str] = {
    "start_ord": "Trimestre de inicio (ordinal)",
    "end_ord": "Trimestre de fin (ordinal)",
    "start_year": "Año de inicio",
    "dur_q": "Duración del empleo (trimestres)",
    "n_skills_essential": "Competencias esenciales ESCO (conteo)",
    "n_skills_competence": "Competencias prácticas ESCO (conteo)",
    "n_skills_knowledge": "Conocimientos teóricos ESCO (conteo)",
    "n_skills_sin_tipo": "Competencias sin tipo ESCO (conteo)",
    "job_order": "Orden del empleo en la carrera",
    "previous_jobs": "Empleos previos acumulados",
    "es_vigente": "Empleo vigente (0/1)",
    "tiene_skills": "Reporta competencias prácticas (0/1)",
    "tiene_knowledge": "Reporta conocimientos (0/1)",
    "tiene_sin_tipo": "Reporta competencias sin tipo (0/1)",
    "university_level": "Nivel educativo",
    "isco_major": "Gran grupo ISCO (1 dígito)",
}

DENSE_FEATURE_METADATA_ES: Dict[str, Dict[str, str]] = {
    "start_ord_rob": {
        "tipo": "Continua (RobustScaler)",
        "unidad_original": "Trimestre calendario (start_ord)",
        "bloque_comportamiento": "Temporal",
        "descripcion": "Fecha de inicio del empleo expresada en trimestres y escalada con mediana/IQR de train.",
    },
    "end_ord_rob": {
        "tipo": "Continua (RobustScaler)",
        "unidad_original": "Trimestre calendario (end_ord)",
        "bloque_comportamiento": "Temporal",
        "descripcion": "Fecha de término del empleo (censurada en 2026-Q1 si sigue vigente), escalada en train.",
    },
    "dur_q_rob": {
        "tipo": "Continua (RobustScaler)",
        "unidad_original": "Trimestres de duración (dur_q)",
        "bloque_comportamiento": "Duración y carrera",
        "descripcion": "Duración del episodio laboral en trimestres con escalado robusto.",
    },
    "n_skills_essential_rob": {
        "tipo": "Continua (RobustScaler)",
        "unidad_original": "Conteo de competencias (n_skills_essential)",
        "bloque_comportamiento": "Competencias",
        "descripcion": "Total de competencias esenciales asociadas al oficio en el catálogo ESCO.",
    },
    "n_skills_knowledge_rob": {
        "tipo": "Continua (RobustScaler)",
        "unidad_original": "Conteo de conocimientos (n_skills_knowledge)",
        "bloque_comportamiento": "Competencias",
        "descripcion": "Total de conocimientos teóricos exigidos por el oficio en el catálogo ESCO.",
    },
    "n_skills_sin_tipo_rob": {
        "tipo": "Continua (RobustScaler)",
        "unidad_original": "Conteo sin tipo (n_skills_sin_tipo)",
        "bloque_comportamiento": "Competencias",
        "descripcion": "Competencias ESCO sin clasificación (casi constante en 0: ~0.90 % distinto de 0 en train).",
    },
    "job_order_rob": {
        "tipo": "Continua (RobustScaler)",
        "unidad_original": "Posición del empleo (job_order)",
        "bloque_comportamiento": "Duración y carrera",
        "descripcion": "Número de orden cronológico del empleo dentro del currículum de la persona.",
    },
    "univ_ord_mm": {
        "tipo": "Ordinal (MinMaxScaler 0..1)",
        "unidad_original": "Nivel educativo codificado (0..4)",
        "bloque_comportamiento": "Educación",
        "descripcion": "Codificación ordinal de university_level escalada entre 0 y 1 en el pipeline 3.0.",
    },
    "es_vigente": {
        "tipo": "Binaria (0/1)",
        "unidad_original": "Indicador 0/1",
        "bloque_comportamiento": "Duración y carrera",
        "descripcion": "Vale 1 cuando el empleo sigue activo al corte del registro ('Present').",
    },
    "dur_q_bin": {
        "tipo": "Ordinal discreta (bins uint8)",
        "unidad_original": "Tramo cuantil de dur_q (0..4)",
        "bloque_comportamiento": "Duración y carrera",
        "descripcion": "Discretización por cuantiles de la duración ajustada en train.",
    },
    "n_skills_essential_bin": {
        "tipo": "Ordinal discreta (bins uint8)",
        "unidad_original": "Tramo cuantil de n_skills_essential (0..4)",
        "bloque_comportamiento": "Competencias",
        "descripcion": "Discretización por cuantiles del número de competencias esenciales.",
    },
    "tiene_skills": {
        "tipo": "Binaria (0/1)",
        "unidad_original": "Indicador 0/1",
        "bloque_comportamiento": "Competencias",
        "descripcion": "Indica si el oficio registra al menos una competencia práctica en ESCO.",
    },
    "tiene_knowledge": {
        "tipo": "Binaria (0/1)",
        "unidad_original": "Indicador 0/1",
        "bloque_comportamiento": "Competencias",
        "descripcion": "Indica si el oficio registra al menos un conocimiento teórico en ESCO.",
    },
    "tiene_sin_tipo": {
        "tipo": "Binaria (0/1)",
        "unidad_original": "Indicador 0/1",
        "bloque_comportamiento": "Competencias",
        "descripcion": "Indica presencia de competencias sin tipo (casi constante en 0: ~0.90 % en 1 en train).",
    },
}

DEFAULT_VAR_SMOOTHING_GRID: Tuple[float, ...] = (
    1e-12,
    1e-9,
    1e-6,
    1e-4,
    1e-2,
    1e-1,
    0.5,
    1.0,
    2.0,
    5.0,
)

DEFAULT_NB_G_VAR_SMOOTHING_GRID: Tuple[float, ...] = (
    1e-12,
    1e-9,
    1e-6,
    1e-4,
    1e-2,
    1e-1,
    0.5,
    1.0,
    2.0,
    5.0,
    10.0,
    25.0,
    50.0,
    100.0,
    500.0,
)

DEFAULT_ALPHA_GRID: Tuple[float, ...] = (
    0.01,
    0.1,
    0.5,
    1.0,
    2.0,
    5.0,
)

PRIOR_MODES: Tuple[str, ...] = ("empirical", "balanced")

PRIOR_MODE_LABELS_ES: Dict[str, str] = {
    "empirical": "Empírico (prevalencia train)",
    "balanced": "Balanceado [0.5, 0.5]",
}

EDUCATION_ORDER_ES: Tuple[str, ...] = (
    "No reportado",
    "Secondary school",
    "Bachelor",
    "Master",
    "PhD",
)


@dataclass(frozen=True)
class NaiveBayesConfig:
    """Immutable configuration for Notebook 7.1 (Naive Bayes) and its modules."""

    project_root: Path
    random_state: int = 42
    cv_folds: int = 5
    test_size: float = 0.20
    bootstrap_resamples: int = 300
    min_subgroup_support: int = 200
    var_smoothing_grid: Tuple[float, ...] = field(default=DEFAULT_VAR_SMOOTHING_GRID)
    nb_g_var_smoothing_grid: Tuple[float, ...] = field(default=DEFAULT_NB_G_VAR_SMOOTHING_GRID)
    alpha_grid: Tuple[float, ...] = field(default=DEFAULT_ALPHA_GRID)
    prior_modes: Tuple[str, ...] = field(default=PRIOR_MODES)
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
        return self.project_root / "data" / "03_processed"

    @property
    def transformed_dir(self) -> Path:
        return self.project_root / "data" / "04_transformed"

    @property
    def split_map_path(self) -> Path:
        return self.project_root / "reports" / "eda_jobpath" / "tables" / "split_map_resume_id.csv"

    @property
    def reports_dir(self) -> Path:
        return self.project_root / "reports" / "naive_bayes_jobpath"

    @property
    def figures_dir(self) -> Path:
        return self.reports_dir / "figures"

    @property
    def tables_dir(self) -> Path:
        return self.reports_dir / "tables"

    @property
    def progress_md_path(self) -> Path:
        return self.reports_dir / "PROGRESS.md"

    @property
    def references_csv_path(self) -> Path:
        return (
            self.project_root
            / "reports"
            / "arbol_decision_jobpath"
            / "tables"
            / "05b_tres_referencias_obligatorias.csv"
        )

    @property
    def trees_comparison_csv_path(self) -> Path:
        return (
            self.project_root
            / "reports"
            / "arbol_decision_jobpath"
            / "tables"
            / "07_comparacion_tres_arboles_referencias_y_versiones.csv"
        )

    @property
    def phase4_test_csv_path(self) -> Path:
        return (
            self.project_root
            / "reports"
            / "modelado_jobpath"
            / "tables"
            / "resultados_test_ab.csv"
        )

    def clean_csv_path(self, version: str = VERSION_CON) -> Path:
        return self.processed_dir / CLEAN_CSV_BY_VERSION[version]

    def x_path(self, version: str, split: str) -> Path:
        return self.transformed_dir / version / split / f"X_{split}.csv"

    def y_path(self, version: str, split: str) -> Path:
        return self.transformed_dir / version / split / f"y_{split}.csv"

    def transformers_path(self, version: str) -> Path:
        return self.transformed_dir / "transformers" / version / "transformers.joblib"


__all__ = [
    "ALL_DENSE_CLEAN_FEATURES",
    "ALL_DENSE_FEATURES_IN_X",
    "BINARY_DENSE_FEATURES",
    "CLEAN_CSV_BY_VERSION",
    "COLLINEAR_REDUNDANT_FEATURES",
    "CONTINUOUS_ROB_FEATURES",
    "CONTINUOUS_TO_ORIGINAL_COL",
    "DEFAULT_ALPHA_GRID",
    "DEFAULT_NB_G_VAR_SMOOTHING_GRID",
    "DEFAULT_VAR_SMOOTHING_GRID",
    "DENSE_FEATURE_METADATA_ES",
    "EDUCATION_ORDER_ES",
    "GAUSSIAN_HYBRID_FEATURES",
    "GUIDING_QUESTION_ES",
    "IQR_WINSOR_BOUNDS_INFO",
    "ISCO_MAJOR_LABELS_ES",
    "LEAKAGE_FEATURES_IN_X",
    "MODEL_LABELS_ES",
    "MODEL_NB_B",
    "MODEL_NB_G",
    "MODEL_NB_G_STAR",
    "MODEL_NB_H",
    "MODEL_ORDER",
    "NaiveBayesConfig",
    "ORDINAL_BIN_FEATURES",
    "ORDINAL_FEATURES",
    "ORDINAL_MINMAX_FEATURES",
    "ORIGINAL_COL_LABELS_ES",
    "PRIOR_MODES",
    "PRIOR_MODE_LABELS_ES",
    "PROHIBITED_CONCEPTUAL_COLUMNS",
    "VERSION_CON",
    "VERSION_LABELS",
    "VERSION_SIN",
    "resolve_project_root",
]
