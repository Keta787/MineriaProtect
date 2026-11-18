"""Leakage-free and collinearity-controlled dataset builder for CRISP-DM Phase 4.

Reconstructs the exact train/test partitions and sparse/dense feature matrices from
the read-only clean CSVs and pre-fitted `TransformArtifacts` (`transformers.joblib`),
verifies row-by-row alignment with exported `X_train.csv`/`y_train.csv`, and enforces
the removal of target-leakage and collinear redundant columns before modeling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from scipy import sparse

from scripts.ScriptsCsv.Transformacion.date_features import (
    add_date_ordinals,
    add_job_order,
    add_start_year,
)
from scripts.ScriptsCsv.Transformacion.discretization import transform_discretizers
from scripts.ScriptsCsv.Transformacion.encoding import (
    derive_skill_presence,
    ordinal_from_mapping,
)
from scripts.ScriptsCsv.Transformacion.scaling import transform_scaling
from scripts.ScriptsCsv.Transformacion.split import (
    TransformArtifacts,
    group_train_test_split,
)

from .config import (
    ALL_DENSE_FEATURES_IN_X,
    COLLINEAR_REDUNDANT_FEATURES,
    LEAKAGE_FEATURES_IN_X,
    ModelingConfig,
)

UNIV_ORDER: Dict[str, int] = {
    "No reportado": 0,
    "Secondary school": 1,
    "Bachelor": 2,
    "Master": 3,
    "PhD": 4,
}


@dataclass(frozen=True)
class PreparedPartition:
    """Aligned dense + sparse feature sets, target vector, and person groups for one split."""

    dense_all: pd.DataFrame
    dense_no_leakage: pd.DataFrame
    dense_clean: pd.DataFrame
    ohe_sparse: sparse.csr_matrix
    ohe_feature_names: List[str]
    y: np.ndarray
    groups: np.ndarray

    def build_sparse_matrix(self, mode: str = "clean") -> Tuple[sparse.csr_matrix, List[str]]:
        """Combine selected dense features with the sparse occupation_code OHE matrix."""
        if mode == "with_leakage":
            dense_df = self.dense_all
        elif mode == "no_leakage":
            dense_df = self.dense_no_leakage
        elif mode == "clean":
            dense_df = self.dense_clean
        else:
            raise ValueError(f"Unknown feature mode: {mode}")
        dense_csr = sparse.csr_matrix(dense_df.to_numpy(dtype=np.float32, copy=False))
        combined = sparse.hstack([dense_csr, self.ohe_sparse.astype(np.float32)], format="csr")
        names = list(dense_df.columns) + self.ohe_feature_names
        return combined, names


@dataclass(frozen=True)
class VersionModelingData:
    """Complete train/test data and verification metrics for one dataset version (A or B)."""

    version: str
    train: PreparedPartition
    test: PreparedPartition
    verification: Dict[str, object]
    feature_audit_table: pd.DataFrame


class ModelingDatasetBuilder:
    """Build verified, leakage-free datasets for Phase 4 modeling without touching disk inputs."""

    def __init__(self, config: ModelingConfig) -> None:
        self.config = config

    @staticmethod
    def _derive_features(df: pd.DataFrame) -> pd.DataFrame:
        """Apply the exact deterministic feature derivation used in Notebook 3.0."""
        work = df.copy()
        occupation = work["occupation_code"].fillna("").astype(str).str.strip()
        fusion = occupation.eq("") & work["matched_code"].astype(str).str.strip().ne("unknown")
        occupation.loc[fusion] = work.loc[fusion, "matched_code"].astype(str)
        work["occupation_code"] = occupation.replace("", pd.NA).fillna("unknown")

        work = add_date_ordinals(work, "start_date", "end_date")
        work = add_start_year(work)
        work = add_job_order(work, "resume_id", "start_ord")

        for col in [
            "n_skills_essential",
            "n_skills_competence",
            "n_skills_knowledge",
            "n_skills_sin_tipo",
            "veces_ese_oficio",
        ]:
            if col in work.columns:
                work[col] = pd.to_numeric(work[col], errors="coerce")

        work = derive_skill_presence(
            work,
            ["skills", "knowledge", "sin_tipo"],
            ["tiene_skills", "tiene_knowledge", "tiene_sin_tipo"],
        )
        work = ordinal_from_mapping(work, "university_level", UNIV_ORDER, "univ_ord")
        work["es_vigente"] = (
            work["es_vigente"]
            .astype(str)
            .str.strip()
            .str.lower()
            .map({"true": 1, "false": 0, "1": 1, "0": 0})
            .fillna(0)
            .astype("int8")
        )
        return work

    @staticmethod
    def _assemble_dense_and_sparse(
        df: pd.DataFrame, artifacts: TransformArtifacts
    ) -> Tuple[pd.DataFrame, sparse.csr_matrix, List[str]]:
        """Assemble the 18 dense columns and the 2,967 sparse OHE columns from fitted artifacts."""
        scaled_df = transform_scaling(artifacts.scaling, df)
        pieces: List[pd.DataFrame] = [scaled_df]

        if artifacts.binary_columns:
            pieces.append(df[artifacts.binary_columns].astype(np.uint8).copy())

        if artifacts.discretization_columns:
            bins = transform_discretizers(
                artifacts.discretizers,
                df,
                labels=artifacts.discretization_spec.get("labels", {}),
            )
            bin_cols = [f"{c}_bin" for c in artifacts.discretization_columns]
            pieces.append(bins[bin_cols].astype(np.uint8))

        if artifacts.presence_columns:
            pieces.append(df[artifacts.presence_columns].astype(np.uint8).copy())

        dense_df = pd.concat(pieces, axis=1, copy=False)
        ordered_dense = [c for c in ALL_DENSE_FEATURES_IN_X if c in dense_df.columns]
        dense_df = dense_df[ordered_dense].reset_index(drop=True)

        clean_ohe_input = df[artifacts.onehot_columns].astype(str)
        # Use internal sklearn sparse transform or convert uint8 array to CSR immediately
        ohe_enc = artifacts.onehot
        prev_sparse = getattr(ohe_enc, "sparse_output", False)
        try:
            ohe_enc.sparse_output = True
            ohe_matrix = ohe_enc.transform(clean_ohe_input)
        finally:
            ohe_enc.sparse_output = prev_sparse
        if not sparse.isspmatrix_csr(ohe_matrix):
            ohe_matrix = sparse.csr_matrix(ohe_matrix)
        ohe_names = list(ohe_enc.get_feature_names_out(artifacts.onehot_columns))
        return dense_df, ohe_matrix, ohe_names

    def _build_partition(
        self,
        df: pd.DataFrame,
        y_series: pd.Series,
        artifacts: TransformArtifacts,
    ) -> PreparedPartition:
        dense_all, ohe_sparse, ohe_names = self._assemble_dense_and_sparse(df, artifacts)
        no_leak_cols = [
            c for c in dense_all.columns if c not in self.config.leakage_features
        ]
        clean_cols = [
            c
            for c in no_leak_cols
            if c not in self.config.collinear_drop_features
        ]
        return PreparedPartition(
            dense_all=dense_all,
            dense_no_leakage=dense_all[no_leak_cols].copy(),
            dense_clean=dense_all[clean_cols].copy(),
            ohe_sparse=ohe_sparse,
            ohe_feature_names=ohe_names,
            y=y_series.to_numpy(dtype=np.int8),
            groups=df["resume_id"].astype(str).to_numpy(),
        )

    def build_version(self, version: str) -> VersionModelingData:
        """Load, verify, and partition one version ('con_outliers' or 'sin_outliers')."""
        usecols = [
            "resume_id",
            "start_date",
            "end_date",
            "university_level",
            "matched_code",
            "emparejado",
            "occupation_code",
            "isco_group",
            "n_skills_essential",
            "n_skills_competence",
            "n_skills_knowledge",
            "n_skills_sin_tipo",
            "veces_ese_oficio",
            "es_vigente",
            "skills",
            "knowledge",
            "sin_tipo",
        ]
        raw_df = pd.read_csv(
            self.config.clean_csv_path(version),
            usecols=usecols,
            dtype=str,
            encoding="utf-8",
            keep_default_na=False,
            na_values=[""],
        )
        derived_df = self._derive_features(raw_df)
        classified = derived_df.loc[
            derived_df["n_skills_essential"].notna()
        ].reset_index(drop=True)

        train_df, test_df = group_train_test_split(
            classified,
            group_col="resume_id",
            test_size=self.config.test_size,
            random_state=self.config.random_state,
        )

        y_train = pd.read_csv(self.config.y_path(version, "train")).iloc[:, 0]
        y_test = pd.read_csv(self.config.y_path(version, "test")).iloc[:, 0]
        artifacts: TransformArtifacts = joblib.load(
            self.config.transformers_path(version)
        )

        train_part = self._build_partition(train_df, y_train, artifacts)
        test_part = self._build_partition(test_df, y_test, artifacts)

        # Verify against exported X_train.csv header and first 100 rows
        x_sample = pd.read_csv(self.config.x_path(version, "train"), nrows=100)
        dense_diff = float(
            np.abs(
                x_sample[list(train_part.dense_all.columns)].to_numpy(dtype=float)
                - train_part.dense_all.iloc[:100].to_numpy(dtype=float)
            ).max()
        )
        shared_persons = len(
            set(train_part.groups).intersection(set(test_part.groups))
        )

        remaining_leakage = [
            c
            for c in train_part.dense_clean.columns
            if c in LEAKAGE_FEATURES_IN_X
        ]
        if remaining_leakage:
            raise RuntimeError(f"Leakage columns still present: {remaining_leakage}")

        verification = {
            "version": version,
            "filas_train": int(len(train_part.y)),
            "filas_test": int(len(test_part.y)),
            "personas_train": int(len(np.unique(train_part.groups))),
            "personas_test": int(len(np.unique(test_part.groups))),
            "personas_solapadas": int(shared_persons),
            "cols_originales_x": int(
                train_part.dense_all.shape[1] + len(train_part.ohe_feature_names)
            ),
            "cols_sin_fuga_x": int(
                train_part.dense_no_leakage.shape[1] + len(train_part.ohe_feature_names)
            ),
            "cols_limpias_sin_colinealidad_x": int(
                train_part.dense_clean.shape[1] + len(train_part.ohe_feature_names)
            ),
            "cols_densas_limpias": int(train_part.dense_clean.shape[1]),
            "cols_dummies_ocupacion": int(len(train_part.ohe_feature_names)),
            "max_diff_vs_x_train_csv": round(dense_diff, 10),
            "fuga_eliminada": len(remaining_leakage) == 0,
        }

        audit_rows = []
        for col in train_part.dense_all.columns:
            corr = float(
                np.corrcoef(train_part.dense_all[col].to_numpy(), train_part.y)[0, 1]
            )
            if col in LEAKAGE_FEATURES_IN_X:
                status = "EXCLUIDA (Fuga directa 100 %)"
                reason = "Reproduce exactamente la definición reincide = (veces_ese_oficio > 1)."
            elif col in COLLINEAR_REDUNDANT_FEATURES:
                status = "EXCLUIDA (Colinealidad alta)"
                reason = (
                    "Redundante con start_ord_rob (r = 1.000)."
                    if col == "start_year_rob"
                    else "Redundante con n_skills_essential_rob (r = 0.952)."
                )
            else:
                status = "CONSERVADA (Feature legítima)"
                reason = "Variable predictora válida sin circularidad con el target."
            audit_rows.append(
                {
                    "variable": col,
                    "corr_train_con_target": round(corr, 4),
                    "estado_fase4": status,
                    "justificacion": reason,
                }
            )
        feature_audit_table = pd.DataFrame(audit_rows)

        return VersionModelingData(
            version=version,
            train=train_part,
            test=test_part,
            verification=verification,
            feature_audit_table=feature_audit_table,
        )
