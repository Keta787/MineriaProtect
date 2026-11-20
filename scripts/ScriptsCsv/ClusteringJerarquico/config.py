"""Configuration, paths, feature definitions, and SHA-256 integrity helpers for Agglomerative Hierarchical Clustering."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd


RANDOM_STATE: int = 42
SENSITIVITY_SEEDS: Tuple[int, ...] = (42, 100, 2026, 7, 999)
MICRO_SAMPLE_N: int = 60
DISCOVERY_SAMPLE_N: int = 3000
K_RANGE: Tuple[int, ...] = (2, 3, 4, 5, 6, 7, 8)
DEFAULT_K_OPT: int = 4
PLOT_LANG: str = "es"

VERSION_B: str = "sin_outliers"
VERSION_A: str = "con_outliers"

VERSION_LABELS_ES: Dict[str, str] = {
    VERSION_B: "Versión B · SIN outliers (Primaria)",
    VERSION_A: "Versión A · CON outliers (Sensibilidad)",
}

UNIVERSITY_ORDINAL_MAP: Dict[str, float] = {
    "Secondary school": 1.0,
    "Secondary education": 1.0,
    "Bachelor": 2.0,
    "Bachelor or equivalent": 2.0,
    "Master": 3.0,
    "Master or equivalent": 3.0,
    "PhD": 4.0,
    "Doctor or equivalent": 4.0,
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

V_PERSON: List[str] = [
    "n_jobs",
    "span_q",
    "dur_mean",
    "overlap_ratio",
    "mean_skills_competence",
    "mean_skills_knowledge",
    "mean_prop_competence",
    "nivel_academico_ord_imputado",
    "educacion_no_reportada",
]

V_EXPERIENCE: List[str] = [
    "dur_q",
    "job_order",
    "n_skills_competence",
    "n_skills_knowledge",
    "prop_competence_essential",
    "nivel_academico_ord_imputado",
    "educacion_no_reportada",
]

FORBIDDEN_LEAKAGE_COLS: Tuple[str, ...] = (
    "reincide",
    "is_repeated_occupation",
    "any_repeated",
    "any_repeated_posthoc",
    "tasa_reincide_persona_posthoc",
    "veces_ese_oficio",
    "veces_ese_oficio_rob",
    "veces_ese_oficio_bin",
    "n_returns",
    "n_self_loops",
    "n_nonadjacent_returns",
    "self_loop_share",
    "nonadjacent_return_share",
    "n_occ",
    "n_occ_posthoc",
    "exploration_ratio",
    "exploration_ratio_posthoc",
)

SEGMENT_METADATA_PERSON_ES: Dict[int, Dict[str, str]] = {
    0: {
        "nombre_segmento": "Inserción Temprana y Trayectorias Cortas en Oficios Operativos",
        "foco_demografico_y_conductual": "Baja movilidad acumulada (1 a 2 empleos), horizonte temporal corto y exigencia ESCO moderada con predominio práctico.",
        "accion_observatorio": "Programa Puente al Primer Empleo: orientación vocacional temprana, certificación de competencias prácticas base y seguimiento en los primeros 4 trimestres post-egreso.",
    },
    1: {
        "nombre_segmento": "Especialistas Estables de Permanencia Prolongada",
        "foco_demografico_y_conductual": "Permanencia media alta por empleo, bajo solapamiento contractual y trayectoria consolidada en un mismo campo ocupacional.",
        "accion_observatorio": "Ruta de Actualización Continua (Up-Skilling): micro-credenciales de especialización técnica para evitar obsolescencia en carreras de larga duración.",
    },
    2: {
        "nombre_segmento": "Profesionales Intensivos en Conocimiento y Alta Exigencia ESCO",
        "foco_demografico_y_conductual": "Alto volumen de competencias prácticas y conocimientos especializados ESCO, mayor nivel académico formal y transición hacia cargos técnicos/profesionales.",
        "accion_observatorio": "Vinculación I+D y Posgrados Aplicados: articulación con maestrías, liderazgo técnico y transferencia tecnológica universidad-empresa.",
    },
    3: {
        "nombre_segmento": "Trayectorias de Alta Rotación y Multi-Empleo Solapado",
        "foco_demografico_y_conductual": "Alto número de experiencias laborales a lo largo de una carrera extensa, mayor solapamiento temporal o encadenamiento frecuente de contratos.",
        "accion_observatorio": "Programa de Estabilización y Consolidación de Portafolio Laboral: acompañamiento para formalizar trayectorias fragmentadas y capitalizar la experiencia acumulada.",
    },
}

SEGMENT_METADATA_EXPERIENCE_ES: Dict[int, Dict[str, str]] = {
    0: {
        "nombre_segmento": "Experiencias Iniciales de Corta Duración y Exigencia Básica",
        "foco_demografico_y_conductual": "Primeros escalones de la trayectoria (bajo job_order), duración acotada y perfil de competencias ESCO elemental.",
        "accion_observatorio": "Módulo de Nivelación de Competencias Transversales para reducir la rotación temprana.",
    },
    1: {
        "nombre_segmento": "Puestos Operativos y Administrativos con Educación No Reportada (MNAR)",
        "foco_demografico_y_conductual": "Experiencias donde el trabajador no reporta título universitario formal (educacion_no_reportada = 1) con perfil práctico ESCO.",
        "accion_observatorio": "Certificación por Evaluación de Saberes Previos (reconocimiento de experiencia empírica sin título reportado).",
    },
    2: {
        "nombre_segmento": "Ocupaciones Técnicas y Profesionales de Alta Complejidad ESCO",
        "foco_demografico_y_conductual": "Exigencia elevada tanto en competencias prácticas como en conocimientos teóricos especializados.",
        "accion_observatorio": "Alineación Curricular con Estándares ESCO de Alta Complejidad en programas de pregrado y posgrado.",
    },
    3: {
        "nombre_segmento": "Empleos de Larga Permanencia o Etapa Avanzada de Carrera",
        "foco_demografico_y_conductual": "Experiencias de alta duración trimestral (dur_q elevado) o ubicadas en etapas maduras del historial laboral (job_order alto).",
        "accion_observatorio": "Red de Mentores Egresados y Reconversión Ejecutiva para trayectorias sénior.",
    },
}


def resolve_project_root() -> Path:
    """Resolve the MineriaProtect repository root from any working directory."""
    cwd = Path.cwd()
    for candidate in [cwd] + list(cwd.parents):
        if candidate.name == "MineriaProtect":
            return candidate
        if (candidate / "MineriaProtect").is_dir():
            return candidate / "MineriaProtect"
    raise FileNotFoundError("Could not locate MineriaProtect root directory.")


@dataclass(frozen=True)
class HierarchicalClusteringConfig:
    """Immutable configuration for the Agglomerative Hierarchical Clustering pipeline."""

    project_root: Path
    clean_version_b_path: Path
    clean_version_a_path: Path
    split_map_path: Path
    reports_dir: Path
    figures_dir: Path
    tables_dir: Path
    bitacora_md_path: Path
    comparacion_ab_md_path: Path
    random_state: int = RANDOM_STATE
    sensitivity_seeds: Tuple[int, ...] = SENSITIVITY_SEEDS
    micro_sample_n: int = MICRO_SAMPLE_N
    discovery_sample_n: int = DISCOVERY_SAMPLE_N
    k_range: Tuple[int, ...] = K_RANGE
    default_k_opt: int = DEFAULT_K_OPT
    plot_lang: str = PLOT_LANG

    @classmethod
    def default(cls) -> "HierarchicalClusteringConfig":
        root = resolve_project_root()
        rep_dir = root / "reports" / "clustering_jerarquico_jobpath"
        fig_dir = rep_dir / "figures"
        tab_dir = rep_dir / "tables"
        fig_dir.mkdir(parents=True, exist_ok=True)
        tab_dir.mkdir(parents=True, exist_ok=True)
        return cls(
            project_root=root,
            clean_version_b_path=root / "data" / "03_processed" / "empleos_limpio_con_competencias_sin_outliers.csv",
            clean_version_a_path=root / "data" / "03_processed" / "empleos_unificado_limpio.csv",
            split_map_path=root / "reports" / "eda_jobpath" / "tables" / "split_map_resume_id.csv",
            reports_dir=rep_dir,
            figures_dir=fig_dir,
            tables_dir=tab_dir,
            bitacora_md_path=root / "notebooks" / "refactor" / "Bitacora_Clustering_Jerarquico.md",
            comparacion_ab_md_path=root / "notebooks" / "refactor" / "Comparacion_A_vs_B_Clustering_Jerarquico.md",
        )


def compute_file_sha256(filepath: Path) -> str:
    """Compute SHA-256 hex digest of a file on disk."""
    sha = hashlib.sha256()
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def snapshot_input_hashes(config: HierarchicalClusteringConfig) -> Dict[str, str]:
    """Record initial SHA-256 digests of the three read-only input files."""
    return {
        "clean_version_b": compute_file_sha256(config.clean_version_b_path),
        "clean_version_a": compute_file_sha256(config.clean_version_a_path),
        "split_map": compute_file_sha256(config.split_map_path),
    }


def verify_input_hashes(
    config: HierarchicalClusteringConfig,
    initial_hashes: Dict[str, str],
) -> pd.DataFrame:
    """Verify that read-only input files were not modified during execution."""
    current_hashes = snapshot_input_hashes(config)
    paths_map = {
        "clean_version_b": config.clean_version_b_path.relative_to(config.project_root).as_posix(),
        "clean_version_a": config.clean_version_a_path.relative_to(config.project_root).as_posix(),
        "split_map": config.split_map_path.relative_to(config.project_root).as_posix(),
    }
    rows = []
    for key, init_h in initial_hashes.items():
        curr_h = current_hashes[key]
        intact = init_h == curr_h
        if not intact:
            raise AssertionError(f"SHA-256 mismatch detected for input file {key}!")
        rows.append(
            {
                "archivo_insumo": key,
                "ruta_relativa": paths_map[key],
                "sha256_inicial": init_h[:16] + "...",
                "sha256_final": curr_h[:16] + "...",
                "intacto_en_disco": "Sí" if intact else "No",
            }
        )
    return pd.DataFrame(rows)
