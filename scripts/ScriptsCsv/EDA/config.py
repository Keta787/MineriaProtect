"""Configuration, paths and shared constants for the JobPath EDA.

This module centralises every path and every list of columns used by the
notebook, so the rest of the package never hard-codes a file name.  It is the
only place that knows where the project lives on disk.

CRISP-DM phase: 2 (Data Understanding), executed as a valid iteration after the
data preparation of notebooks 2.0 and 3.0.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping, Tuple

VERSION_WITH_OUTLIERS: str = "con_outliers"
VERSION_WITHOUT_OUTLIERS: str = "sin_outliers"
VERSIONS: Tuple[str, ...] = (VERSION_WITH_OUTLIERS, VERSION_WITHOUT_OUTLIERS)

VERSION_LABELS: Mapping[str, str] = {
    VERSION_WITH_OUTLIERS: "A · con outliers",
    VERSION_WITHOUT_OUTLIERS: "B · sin outliers (IQR)",
}

CLEAN_FILES: Mapping[str, str] = {
    VERSION_WITH_OUTLIERS: "empleos_limpio_con_competencias.csv",
    VERSION_WITHOUT_OUTLIERS: "empleos_limpio_con_competencias_sin_outliers.csv",
}

PERSON_COL: str = "resume_id"
TARGET_COL: str = "reincide"
TARGET_DISPLAY: str = "is_repeated_occupation"

#: Columns that take part in the definition of the target, directly or through
#: a person-level restatement.  They are never crossed with the target.
TARGET_RELATED: Mapping[str, str] = {
    "veces_ese_oficio": "Definición directa: reincide = veces_ese_oficio > 1.",
    "n_returns": "Equivalente a nivel persona: n_returns >= 1 <=> max(reincide) = 1.",
    "n_nonadjacent_returns": "Retornos no adyacentes; relacionados con la repetición.",
}

#: Families of variables that are redundant by construction.  They are
#: reported together but never interpreted as independent evidence.
COLLINEAR_FAMILIES: Mapping[str, Tuple[str, ...]] = {
    "duración": ("dur_q", "dur_total", "span_q", "start_ord", "end_ord"),
    "competencias": (
        "n_skills_essential",
        "n_skills_competence",
        "n_skills_knowledge",
        "n_skills_sin_tipo",
    ),
    "tamaño de la trayectoria": ("n_jobs", "n_occ"),
}

#: Numeric columns explored at experience level (clean CSV, unscaled).
EXPERIENCE_NUMERIC: Tuple[str, ...] = (
    "dur_q",
    "n_skills_essential",
    "n_skills_competence",
    "n_skills_knowledge",
    "n_skills_sin_tipo",
    "veces_ese_oficio",
)

#: Numeric columns explored at person level (aggregated by resume_id).
PERSON_NUMERIC: Tuple[str, ...] = (
    "n_jobs",
    "n_occ",
    "span_q",
    "dur_total",
    "dur_mean",
    "n_returns",
    "overlap_ratio",
    "self_loop_share",
    "exploration_ratio",
)

#: Numeric columns used in the Pearson / Spearman matrix (experience level).
CORRELATION_NUMERIC: Tuple[str, ...] = (
    "dur_q",
    "start_ord",
    "end_ord",
    "start_year",
    "job_order",
    "n_skills_essential",
    "n_skills_competence",
    "n_skills_knowledge",
    "n_skills_sin_tipo",
    "veces_ese_oficio",
)

#: Categorical columns explored in the univariate section.
CATEGORICAL_COLUMNS: Tuple[str, ...] = (
    "university_level",
    "isco_group_label",
    "occupation_label",
    "emparejado",
    "es_vigente",
)

#: Logical order of the education levels.  It is ordinal, so it is plotted in
#: this order instead of frequency order.
UNIVERSITY_ORDER: Tuple[str, ...] = (
    "Secondary school",
    "Bachelor",
    "Master",
    "PhD",
    "No reportado",
)

#: Short reason that explains why each column matters for JobPath.
COLUMN_RELEVANCE: Mapping[str, Tuple[bool, str]] = {
    "resume_id": (False, "Clave de agrupación por persona; no es una feature."),
    "start_date": (True, "Origen de la duración y del orden temporal."),
    "end_date": (True, "Fin del empleo; 'Present' se trata como censura."),
    "university_level": (True, "Único proxy disponible del nivel de formación."),
    "matched_code": (False, "Código de ocupación emparejado; no es campo de estudio."),
    "emparejado": (True, "Calidad del emparejamiento con ESCO."),
    "occupation_code": (True, "Unidad de análisis de la transición."),
    "occupation_label": (True, "Etiqueta legible del oficio."),
    "isco_group": (True, "Agregación ISCO de la ocupación."),
    "isco_group_label": (True, "Etiqueta legible del grupo ISCO."),
    "isco_level": (False, "Nivel jerárquico ISCO; IQR = 0."),
    "n_skills_essential": (True, "Complejidad del oficio (competencias esenciales)."),
    "n_skills_competence": (True, "Competencias de tipo 'competence'."),
    "n_skills_knowledge": (True, "Competencias de tipo 'knowledge'."),
    "n_skills_sin_tipo": (False, "Competencias sin tipo; mayoría cero."),
    "veces_ese_oficio": (True, "Define el target; se marca como circular."),
    "saber_skills": (True, "Cobertura de competencias del oficio."),
    "es_unknown_ocupacion": (True, "Bandera de oficio desconocido."),
    "es_rescatado": (True, "Bandera de oficio rescatado desde matched_code."),
    "es_vigente": (True, "Empleo actual; explica la censura a la derecha."),
    "skills": (False, "Lista ESCO cruda; ya resumida por n_skills_*."),
    "knowledge": (False, "Lista ESCO cruda; ya resumida por n_skills_*."),
    "sin_tipo": (False, "Lista ESCO cruda; ya resumida por n_skills_*."),
}

TEXT_COLUMNS: Tuple[str, ...] = ("skills", "knowledge", "sin_tipo")


@dataclass(frozen=True)
class EDAConfig:
    """Immutable configuration shared by every EDA component."""

    root: Path
    processed_dir: Path
    transformed_dir: Path
    figures_dir: Path
    tables_dir: Path
    seed: int = 42
    top_n: int = 15
    test_size: float = 0.2
    min_group_n: int = 200
    scatter_sample: int = 20_000
    dpi: int = 150

    @property
    def clean_paths(self) -> Dict[str, Path]:
        """Absolute path of the clean CSV for each version."""
        return {version: self.processed_dir / CLEAN_FILES[version] for version in VERSIONS}

    @property
    def split_map_path(self) -> Path:
        """Where the resume_id -> train/test map is written."""
        return self.tables_dir / "split_map_resume_id.csv"

    @property
    def pca_notebooks(self) -> Dict[str, Path]:
        """Saved PCA diagnostics reused as evidence (no refitting)."""
        return {
            "10k": self.root / "notebooks" / "refactor" / "4.0_PCA.ipynb",
            "50k": self.root / "notebooks" / "refactor" / "4.1_PCA_completo.ipynb",
        }

    @property
    def input_paths(self) -> Tuple[Path, ...]:
        """Every input that must remain byte-identical after the EDA run."""
        paths = list(self.clean_paths.values())
        for version in VERSIONS:
            for split in ("train", "test"):
                base = self.transformed_dir / version / split
                paths.append(base / f"X_{split}.csv")
                paths.append(base / f"y_{split}.csv")
            paths.append(self.transformed_dir / "transformers" / version / "transformers.joblib")
        paths.extend(self.pca_notebooks.values())
        return tuple(paths)

    @property
    def figure_files(self) -> Tuple[str, ...]:
        """Approved figure manifest, in report order."""
        return (
            "g01_duracion_empleo_hist.png",
            "g02_top_ocupaciones.png",
            "g03_duracion_por_isco.png",
            "g04_nivel_educativo.png",
            "g05_competencias_esenciales_hist.png",
            "g06_competencias_por_isco.png",
            "g07_experiencias_por_anio.png",
            "g08_nulos_por_columna.png",
            "g09_outliers_iqr_ab.png",
            "g10_cobertura_esco_por_anio.png",
            "g11_empleos_por_persona.png",
            "g12_duracion_trayectoria.png",
            "g13_retornos_por_persona.png",
            "g14_forma_trayectoria.png",
            "g15_hexbin_empleos_oficios.png",
            "g16_transiciones_frecuentes.png",
            "g17_correlacion_pearson.png",
            "g19_pearson_vs_spearman.png",
            "g20_transiciones_ocupacion.png",
            "g21_transiciones_isco.png",
            "g22_autolazo_por_ocupacion.png",
            "g23_pca_estabilidad.png",
            "g25_comparacion_ab.png",
            "g26_balance_target.png",
            "g27_target_por_isco.png",
            "g28_target_por_duracion.png",
            "g29_target_por_nivel.png",
            "g30_fuga_target.png",
        )


def project_root(start: Path | None = None) -> Path:
    """Walk upwards until the directory that contains ``data`` and ``notebooks``."""
    current = Path(start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "data").is_dir() and (candidate / "notebooks").is_dir():
            return candidate
    return current


def default_config(start: Path | None = None) -> EDAConfig:
    """Build the standard configuration for the JobPath EDA."""
    root = project_root(start)
    return EDAConfig(
        root=root,
        processed_dir=root / "data" / "03_processed",
        transformed_dir=root / "data" / "04_transformed",
        figures_dir=root / "reports" / "eda_jobpath" / "figures",
        tables_dir=root / "reports" / "eda_jobpath" / "tables",
    )
