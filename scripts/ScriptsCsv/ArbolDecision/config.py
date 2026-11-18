"""Configuration and immutable constants for CRISP-DM Phase 4 (Decision Trees 7.0 v2)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Tuple


VERSION_A: str = "con_outliers"
VERSION_B: str = "sin_outliers"

VERSION_LABELS_ES: Dict[str, str] = {
    VERSION_A: "Versión A · CON outliers",
    VERSION_B: "Versión B · SIN outliers",
}
VERSION_A_LABEL_ES: str = VERSION_LABELS_ES[VERSION_A]
VERSION_B_LABEL_ES: str = VERSION_LABELS_ES[VERSION_B]

CLEAN_CSV_BY_VERSION: Dict[str, str] = {
    VERSION_A: "empleos_unificado_limpio.csv",
    VERSION_B: "empleos_limpio_con_competencias_sin_outliers.csv",
}

MAIN_QUESTION_ES: str = (
    "¿El perfil de un oficio separa a las personas que lo repiten de las que lo ejercen por primera vez?"
)

BLOCK_ISCO: str = "tree_1_isco"
BLOCK_EDUCATION: str = "tree_2_education"
BLOCK_SKILLS: str = "tree_3_skills"

BLOCK_ORDER: Tuple[str, ...] = (BLOCK_ISCO, BLOCK_EDUCATION, BLOCK_SKILLS)

BLOCK_METADATA_ES: Dict[str, Dict[str, str]] = {
    BLOCK_ISCO: {
        "tree_id": "1 · ISCO",
        "tree_label": "Árbol 1 · ISCO",
        "question_es": "¿Saber en qué gran grupo ocupacional está el oficio alcanza para anticipar si se repite?",
        "heading_es": (
            "Árbol 1 · ISCO: ¿Saber en qué gran grupo ocupacional está el oficio alcanza para anticipar si se repite?"
        ),
        "short_name": "isco",
        "description": (
            "Información ISCO-08 (grandes grupos a 1 dígito como versión principal; "
            "2 dígitos y Top-50 a 4 dígitos solo como variantes registradas en bitácora)"
        ),
    },
    BLOCK_EDUCATION: {
        "tree_id": "2 · Education level",
        "tree_label": "Árbol 2 · Education level",
        "question_es": "¿El nivel académico de quien ejerce el oficio separa a los que repiten de los que no?",
        "heading_es": (
            "Árbol 2 · Education level: ¿El nivel académico de quien ejerce el oficio separa a los que repiten de los que no?"
        ),
        "short_name": "educacion",
        "description": (
            "Nivel educativo ordinal (1..4 solo para reportados, sin rellenar nulos con 0) "
            "+ bandera separada 'educacion_no_reportada' (0/1)"
        ),
    },
    BLOCK_SKILLS: {
        "tree_id": "3 · Skills",
        "tree_label": "Árbol 3 · Skills",
        "question_es": (
            "¿Lo que el oficio exige —su perfil de competencias ESCO— separa mejor que el grupo ocupacional y que el nivel académico?"
        ),
        "heading_es": (
            "Árbol 3 · Skills: ¿Lo que el oficio exige —su perfil de competencias ESCO— separa mejor que el grupo ocupacional y que el nivel académico?"
        ),
        "short_name": "skills",
        "description": (
            "n_skills_essential, n_skills_competence, n_skills_knowledge y variables derivadas "
            "consistentes con el bloque (proporciones, razón y diferencia)"
        ),
    },
}

ISCO_MAJOR_LABELS_ES: Dict[str, str] = {
    "0": "0 · Ocupaciones militares",
    "1": "1 · Directores y gerentes",
    "2": "2 · Profesionales científicos e intelectuales",
    "3": "3 · Técnicos y profesionales de nivel medio",
    "4": "4 · Personal de apoyo administrativo",
    "5": "5 · Trabajadores de los servicios y vendedores",
    "6": "6 · Agricultores y trabajadores agropecuarios",
    "7": "7 · Oficiales, operarios y artesanos",
    "8": "8 · Operadores de instalaciones y máquinas",
    "9": "9 · Ocupaciones elementales",
}

# Strictly map only reported education levels (1..4); never fill 'No reportado' with 0!
EDUCATION_REPORTED_ORDINAL_MAP: Dict[str, float] = {
    "Secondary school": 1.0,
    "Bachelor": 2.0,
    "Master": 3.0,
    "PhD": 4.0,
}
EDUCATION_ORDINAL_MAP: Dict[str, float] = EDUCATION_REPORTED_ORDINAL_MAP

TREE_1_QUESTION_ES: str = BLOCK_METADATA_ES[BLOCK_ISCO]["question_es"]
TREE_2_QUESTION_ES: str = BLOCK_METADATA_ES[BLOCK_EDUCATION]["question_es"]
TREE_3_QUESTION_ES: str = BLOCK_METADATA_ES[BLOCK_SKILLS]["question_es"]

PROHIBITED_LEAKAGE_COLUMNS: Tuple[str, ...] = (
    "veces_ese_oficio",
    "veces_ese_oficio_rob",
    "veces_ese_oficio_bin",
    "n_returns",
    "n_nonadjacent_returns",
    "reincide",
    "is_repeated_occupation",
)

RANDOM_STATE: int = 42
MAX_TREE_DEPTH: int = 4
ALLOWED_DEPTHS: Tuple[int, ...] = (2, 3, 4)
HISTORICAL_REFERENCE_GOAL: float = 0.85
SUCCESS_THRESHOLD: float = HISTORICAL_REFERENCE_GOAL
ASPIRATIONAL_TARGET_SCORE: float = HISTORICAL_REFERENCE_GOAL
MAX_TUNING_ATTEMPTS: int = 10
CV_FOLDS: int = 5

MIN_LEAF_SUPPORT_RATIO: float = 0.005
MIN_LIFT_SEPARATION: float = 1.50
MIN_LEAF_LIFT_FOR_SEPARATION: float = MIN_LIFT_SEPARATION
BOOTSTRAP_PERSON_RESAMPLES: int = 300
BOOTSTRAP_N_RESAMPLES: int = BOOTSTRAP_PERSON_RESAMPLES

SENSITIVITY_TRAIN_PERSONS: int = 3000
SENSITIVITY_TEST_PERSONS: int = 750
SENSITIVITY_SEEDS: Tuple[int, ...] = (42, 100, 2026, 7, 999)

IQR_WINSOR_BOUNDS_INFO: Dict[str, Tuple[float, float]] = {
    "n_skills_essential": (-4.5, 47.5),
    "n_skills_competence": (-4.5, 39.5),
    "n_skills_knowledge": (-6.5, 13.5),
    "veces_ese_oficio": (-0.5, 3.5),
}


def resolve_project_root(start: Path | None = None) -> Path:
    """Locate the repository root containing data/ and notebooks/."""
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "data").is_dir() and (candidate / "notebooks").is_dir():
            return candidate
        if (candidate / "MineriaProtect" / "data").is_dir():
            return candidate / "MineriaProtect"
    raise FileNotFoundError("Could not locate project root containing data/ and notebooks/.")


@dataclass(frozen=True)
class DecisionTreeProjectConfig:
    """Immutable configuration for the 7.0 Decision Tree notebook and modules."""

    project_root: Path
    random_state: int = RANDOM_STATE
    max_depth: int = MAX_TREE_DEPTH
    allowed_depths: Tuple[int, ...] = field(default=ALLOWED_DEPTHS)
    historical_goal: float = HISTORICAL_REFERENCE_GOAL
    max_tuning_attempts: int = MAX_TUNING_ATTEMPTS
    cv_folds: int = CV_FOLDS
    test_size: float = 0.20
    min_leaf_support_ratio: float = MIN_LEAF_SUPPORT_RATIO
    min_lift_separation: float = MIN_LIFT_SEPARATION
    bootstrap_resamples: int = BOOTSTRAP_PERSON_RESAMPLES
    sensitivity_train_persons: int = SENSITIVITY_TRAIN_PERSONS
    sensitivity_test_persons: int = SENSITIVITY_TEST_PERSONS
    sensitivity_seeds: Tuple[int, ...] = field(default=SENSITIVITY_SEEDS)
    prohibited_columns: Tuple[str, ...] = field(default=PROHIBITED_LEAKAGE_COLUMNS)

    @property
    def processed_dir(self) -> Path:
        """Directory containing clean unscaled CSV datasets."""
        return self.project_root / "data" / "03_processed"

    @property
    def transformed_dir(self) -> Path:
        """Directory containing transformed datasets and reference targets."""
        return self.project_root / "data" / "04_transformed"

    @property
    def split_map_path(self) -> Path:
        """Path to the person-level train/test split assignment table."""
        return self.project_root / "reports" / "eda_jobpath" / "tables" / "split_map_resume_id.csv"

    @property
    def phase4_benchmark_path(self) -> Path:
        """Path to the Phase 4 general modeling benchmark results table (notebook 6.0)."""
        return self.project_root / "reports" / "modelado_jobpath" / "tables" / "resultados_test_ab.csv"

    @property
    def notebooks_refactor_dir(self) -> Path:
        """Directory where 7.0_arbol_decision.ipynb and the two .md files reside."""
        return self.project_root / "notebooks" / "refactor"

    @property
    def bitacora_md_path(self) -> Path:
        """Path to File 1: Bitacora_Arbol_Decision.md."""
        return self.notebooks_refactor_dir / "Bitacora_Arbol_Decision.md"

    @property
    def comparacion_ab_md_path(self) -> Path:
        """Path to File 2: Comparacion_A_vs_B_Arbol_Decision.md."""
        return self.notebooks_refactor_dir / "Comparacion_A_vs_B_Arbol_Decision.md"

    @property
    def reports_dir(self) -> Path:
        """Root output directory for notebook 7.0 artifacts."""
        return self.project_root / "reports" / "arbol_decision_jobpath"

    @property
    def figures_dir(self) -> Path:
        """Directory for exported PNG figures."""
        return self.reports_dir / "figures"

    @property
    def rules_dir(self) -> Path:
        """Directory for exported text rules and business rule summaries."""
        return self.reports_dir / "rules"

    @property
    def tables_dir(self) -> Path:
        """Directory for exported CSV metric and analysis tables."""
        return self.reports_dir / "tables"

    def clean_csv_path(self, version: str = VERSION_A) -> Path:
        """Return the path to the clean unscaled CSV for the requested data version."""
        return self.processed_dir / CLEAN_CSV_BY_VERSION[version]

    @property
    def max_tree_depth(self) -> int:
        """Alias for max_depth."""
        return self.max_depth

    @property
    def clean_with_outliers_path(self) -> Path:
        """Path to Version A clean dataset (with outliers)."""
        return self.clean_csv_path(VERSION_A)

    @property
    def clean_without_outliers_path(self) -> Path:
        """Path to Version B clean dataset (IQR-winsorized)."""
        return self.clean_csv_path(VERSION_B)

    @classmethod
    def from_root(cls, project_root: Path | str, random_state: int = RANDOM_STATE) -> "DecisionTreeProjectConfig":
        """Instantiate configuration from a resolved project root path."""
        return cls(project_root=Path(project_root).resolve(), random_state=random_state)

    def y_reference_path(self, version: str, split: str) -> Path:
        """Return the path to the reference target CSV in 04_transformed."""
        return self.transformed_dir / version / split / f"y_{split}.csv"
