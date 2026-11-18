"""Read-only data loader, person-level split verifier, and integrity checker."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from .config import DecisionTreeProjectConfig, VERSION_A, VERSION_B, VERSION_LABELS_ES


REQUIRED_CLEAN_COLUMNS: Tuple[str, ...] = (
    "resume_id",
    "occupation_code",
    "occupation_label",
    "isco_group",
    "isco_group_label",
    "isco_level",
    "emparejado",
    "es_unknown_ocupacion",
    "es_rescatado",
    "university_level",
    "n_skills_essential",
    "n_skills_competence",
    "n_skills_knowledge",
    "n_skills_sin_tipo",
    "veces_ese_oficio",
)


@dataclass(frozen=True)
class SplitBundle:
    """In-memory train/test dataset bundle aligned by person (resume_id)."""

    version: str
    df_train: pd.DataFrame
    df_test: pd.DataFrame
    y_train: pd.Series
    y_test: pd.Series
    groups_train: pd.Series
    groups_test: pd.Series
    unclassified_summary: pd.DataFrame
    split_audit: pd.DataFrame


def compute_file_sha256(file_path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Compute SHA-256 hex digest of a file without modifying it."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def snapshot_input_file_hashes(config: DecisionTreeProjectConfig) -> Dict[str, str]:
    """Record SHA-256 hashes of all critical input files to verify immutability."""
    files_to_track = {
        "clean_version_a": config.clean_csv_path(VERSION_A),
        "clean_version_b": config.clean_csv_path(VERSION_B),
        "split_map": config.split_map_path,
        "y_train_ref_a": config.y_reference_path(VERSION_A, "train"),
        "y_test_ref_a": config.y_reference_path(VERSION_A, "test"),
    }
    return {
        label: compute_file_sha256(path)
        for label, path in files_to_track.items()
        if path.exists()
    }


def verify_input_file_hashes(
    config: DecisionTreeProjectConfig,
    initial_hashes: Dict[str, str],
) -> pd.DataFrame:
    """Verify that no input file was modified during execution."""
    current_hashes = snapshot_input_file_hashes(config)
    rows = []
    for label, before_hash in initial_hashes.items():
        after_hash = current_hashes.get(label, "MISSING")
        intact = before_hash == after_hash
        if not intact:
            raise RuntimeError(f"Input file integrity violation detected for {label}!")
        rows.append(
            {
                "archivo_insumo": label,
                "sha256_inicial": before_hash[:16] + "...",
                "sha256_final": after_hash[:16] + "...",
                "intacto_en_disco": "Sí" if intact else "No",
            }
        )
    return pd.DataFrame(rows)


def load_clean_version_in_ram(
    config: DecisionTreeProjectConfig,
    version: str = VERSION_A,
) -> pd.DataFrame:
    """Load the clean unscaled CSV into a fresh RAM copy without touching disk."""
    csv_path = config.clean_csv_path(version)
    if not csv_path.exists():
        raise FileNotFoundError(f"Clean dataset not found at {csv_path}")

    dtype_map = {
        "resume_id": "string",
        "occupation_code": "string",
        "occupation_label": "string",
        "isco_group": "string",
        "isco_group_label": "string",
        "emparejado": "string",
        "university_level": "string",
    }
    df_raw = pd.read_csv(
        csv_path,
        usecols=list(REQUIRED_CLEAN_COLUMNS),
        dtype=dtype_map,
        low_memory=False,
    )
    df_copy = df_raw.copy(deep=True)
    mask_isco = df_copy["isco_group"].notna()
    df_copy.loc[mask_isco, "isco_group"] = (
        df_copy.loc[mask_isco, "isco_group"]
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(4)
    )
    return df_copy


def summarize_unclassified_occupations(df_full: pd.DataFrame) -> pd.DataFrame:
    """Summarize rows with and without a standardized ESCO skill profile (Decision D07)."""
    total_rows = len(df_full)
    total_persons = int(df_full["resume_id"].nunique())

    mask_classified = df_full["n_skills_essential"].notna()
    n_classified = int(mask_classified.sum())
    n_unclassified = int((~mask_classified).sum())

    n_unknown = int((~mask_classified & (df_full["emparejado"] == "unknown")).sum())
    n_rescued_no_esco = int((~mask_classified & (df_full["emparejado"] == "rescatado")).sum())
    n_other_unclassified = n_unclassified - n_unknown - n_rescued_no_esco

    persons_classified = set(df_full.loc[mask_classified, "resume_id"].unique())
    persons_all = set(df_full["resume_id"].unique())
    persons_excluded_completely = len(persons_all - persons_classified)

    rows = [
        {
            "segmento": "Total unificado limpio (03_processed)",
            "filas": total_rows,
            "porcentaje_filas": 100.0,
            "personas_unicas": total_persons,
            "decision_proyecto": "Universo completo en disco (inmutable)",
        },
        {
            "segmento": "Con ocupación ESCO estandarizada (n_skills_essential no nulo)",
            "filas": n_classified,
            "porcentaje_filas": round(100.0 * n_classified / total_rows, 2),
            "personas_unicas": len(persons_classified),
            "decision_proyecto": "Incluido en modelado (Decisión D07)",
        },
        {
            "segmento": "Sin ocupación ESCO estandarizada (total excluido en RAM)",
            "filas": n_unclassified,
            "porcentaje_filas": round(100.0 * n_unclassified / total_rows, 2),
            "personas_unicas": persons_excluded_completely,
            "decision_proyecto": "Excluido en RAM antes del split (sin perfil ESCO)",
        },
        {
            "segmento": "  └─ Desglose: emparejado == 'unknown'",
            "filas": n_unknown,
            "porcentaje_filas": round(100.0 * n_unknown / total_rows, 2),
            "personas_unicas": np.nan,
            "decision_proyecto": "Texto libre sin correspondencia ESCO",
        },
        {
            "segmento": "  └─ Desglose: emparejado == 'rescatado' sin padre ESCO",
            "filas": n_rescued_no_esco,
            "porcentaje_filas": round(100.0 * n_rescued_no_esco / total_rows, 2),
            "personas_unicas": np.nan,
            "decision_proyecto": "Rescate léxico sin perfil de competencias ESCO",
        },
    ]
    if n_other_unclassified > 0:
        rows.append(
            {
                "segmento": "  └─ Desglose: otros sin competencias esenciales",
                "filas": n_other_unclassified,
                "porcentaje_filas": round(100.0 * n_other_unclassified / total_rows, 2),
                "personas_unicas": np.nan,
                "decision_proyecto": "Ocupación sin competencias esenciales en ESCO",
            }
        )
    return pd.DataFrame(rows)


def build_person_split_bundle(
    config: DecisionTreeProjectConfig,
    version: str = VERSION_A,
    verify_against_disk_reference: bool = True,
) -> SplitBundle:
    """Build the person-grouped train/test split on an in-memory copy of the clean dataset."""
    df_full = load_clean_version_in_ram(config, version=version)
    unclassified_summary = summarize_unclassified_occupations(df_full)

    # Filter modelable universe in RAM (Decision D07)
    df_valid = df_full.loc[df_full["n_skills_essential"].notna()].copy()
    df_valid["reincide"] = (df_valid["veces_ese_oficio"] > 1).astype("int8")

    # Apply the exact project split by resume_id (seed=42, test_size=0.20)
    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=config.test_size,
        random_state=config.random_state,
    )
    train_idx, test_idx = next(splitter.split(df_valid, groups=df_valid["resume_id"]))

    df_train = df_valid.iloc[train_idx].reset_index(drop=True).copy()
    df_test = df_valid.iloc[test_idx].reset_index(drop=True).copy()

    persons_train = set(df_train["resume_id"].unique())
    persons_test = set(df_test["resume_id"].unique())
    shared_persons = len(persons_train.intersection(persons_test))
    if shared_persons != 0:
        raise ValueError(f"Person-level leakage detected: {shared_persons} shared resume_id values!")

    y_train = df_train["reincide"].copy()
    y_test = df_test["reincide"].copy()
    groups_train = df_train["resume_id"].copy()
    groups_test = df_test["reincide"].copy()
    groups_test = df_test["resume_id"].copy()

    # Cross-check against split_map_resume_id.csv and 04_transformed reference targets
    matches_split_map = True
    if verify_against_disk_reference and config.split_map_path.exists():
        split_map_df = pd.read_csv(config.split_map_path, dtype={"resume_id": "string", "split": "string"})
        map_train_ids = set(split_map_df.loc[split_map_df["split"] == "train", "resume_id"])
        map_test_ids = set(split_map_df.loc[split_map_df["split"] == "test", "resume_id"])
        matches_split_map = (persons_train == map_train_ids) and (persons_test == map_test_ids)
        if not matches_split_map:
            raise AssertionError("In-memory split does not match split_map_resume_id.csv!")

    matches_y_ref = True
    y_train_path = config.y_reference_path(version, "train")
    y_test_path = config.y_reference_path(version, "test")
    if verify_against_disk_reference and y_train_path.exists() and y_test_path.exists():
        y_train_disk = pd.read_csv(y_train_path)["reincide"].astype("int8")
        y_test_disk = pd.read_csv(y_test_path)["reincide"].astype("int8")
        matches_y_ref = bool(
            (y_train.to_numpy() == y_train_disk.to_numpy()).all()
            and (y_test.to_numpy() == y_test_disk.to_numpy()).all()
        )
        if not matches_y_ref:
            raise AssertionError("In-memory target vector does not match 04_transformed y reference!")

    split_audit = pd.DataFrame(
        [
            {
                "version": VERSION_LABELS_ES.get(version, version),
                "particion": "Train (80%)",
                "filas": len(df_train),
                "personas_unicas": len(persons_train),
                "positivos_reincide_1": int(y_train.sum()),
                "negativos_reincide_0": int((y_train == 0).sum()),
                "tasa_clase_1_pct": round(float(y_train.mean() * 100.0), 2),
                "personas_compartidas_train_test": shared_persons,
                "coincide_split_map": "Sí" if matches_split_map else "No",
                "coincide_y_04_transformed": "Sí" if matches_y_ref else "No",
            },
            {
                "version": VERSION_LABELS_ES.get(version, version),
                "particion": "Test (20%)",
                "filas": len(df_test),
                "personas_unicas": len(persons_test),
                "positivos_reincide_1": int(y_test.sum()),
                "negativos_reincide_0": int((y_test == 0).sum()),
                "tasa_clase_1_pct": round(float(y_test.mean() * 100.0), 2),
                "personas_compartidas_train_test": shared_persons,
                "coincide_split_map": "Sí" if matches_split_map else "No",
                "coincide_y_04_transformed": "Sí" if matches_y_ref else "No",
            },
        ]
    )

    return SplitBundle(
        version=version,
        df_train=df_train,
        df_test=df_test,
        y_train=y_train,
        y_test=y_test,
        groups_train=groups_train,
        groups_test=groups_test,
        unclassified_summary=unclassified_summary,
        split_audit=split_audit,
    )


def load_phase4_ceiling_benchmarks(config: DecisionTreeProjectConfig) -> pd.DataFrame:
    """Load the Phase 4 full-model benchmark table from notebook 6.0 for ceiling comparison."""
    if not config.phase4_benchmark_path.exists():
        raise FileNotFoundError(f"Phase 4 benchmark table not found at {config.phase4_benchmark_path}")
    df_bench = pd.read_csv(config.phase4_benchmark_path)
    return df_bench.copy()

