"""Scale audit, train-only scalers (OCP/LSP), ISCO join with alignment checks, and KNN feature blocks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.preprocessing import StandardScaler

from scripts.ScriptsCsv.ArbolDecision.block_builders import ISCOBlockBuilder
from scripts.ScriptsCsv.Modelado.dataset_builder import (
    ModelingDatasetBuilder,
    PreparedPartition,
    VersionModelingData,
)
from scripts.ScriptsCsv.Transformacion.date_features import (
    add_date_ordinals,
    add_job_order,
    add_start_year,
)
from scripts.ScriptsCsv.Transformacion.split import group_train_test_split

from .config import (
    ALL_DENSE_CLEAN_FEATURES,
    BINARY_DENSE_FEATURES,
    CONTINUOUS_ROB_FEATURES,
    DENSE_FEATURE_METADATA_ES,
    ISCO_MAJOR_DUMMY_COLS,
    ISCO_MAJOR_LABELS_ES,
    KNNConfig,
    LEAKAGE_FEATURES_IN_X,
    ORDINAL_FEATURES,
    PROHIBITED_CONCEPTUAL_COLUMNS,
    VERSION_CON,
)


class DenseScaleStrategy(ABC):
    """Abstract base interface for train-only dense feature scaling strategies (OCP/LSP)."""

    def __init__(self, strategy_name: str, near_constant_threshold_pct: float = 1.0) -> None:
        self.strategy_name = strategy_name
        self.near_constant_threshold_pct = float(near_constant_threshold_pct)
        self.active_columns_: Tuple[str, ...] = ()
        self.dropped_columns_: Tuple[str, ...] = ()
        self._is_fitted: bool = False

    @abstractmethod
    def fit(self, dense_train_df: pd.DataFrame) -> "DenseScaleStrategy":
        """Fit any column-drop rules, fences, and scalers strictly on training data."""

    @abstractmethod
    def transform(self, dense_df: pd.DataFrame) -> np.ndarray:
        """Transform a dense DataFrame into a contiguous float32 feature array without refitting."""

    def fit_transform(self, dense_train_df: pd.DataFrame) -> np.ndarray:
        """Fit on train and transform train."""
        return self.fit(dense_train_df).transform(dense_train_df)

    @abstractmethod
    def describe_es(self) -> str:
        """Return a concise Spanish description of this scaling strategy."""

    def _check_fitted(self) -> None:
        if not self._is_fitted:
            raise RuntimeError(
                f"{self.__class__.__name__} must be fitted on train before calling transform()."
            )

    def _identify_active_columns(
        self,
        dense_train_df: pd.DataFrame,
    ) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
        """Identify active vs near-constant columns (< threshold minority share) strictly on train."""
        n_rows = max(int(len(dense_train_df)), 1)
        active: List[str] = []
        dropped: List[str] = []
        for col in dense_train_df.columns:
            vc = dense_train_df[col].value_counts(dropna=False)
            mode_cnt = int(vc.iloc[0]) if not vc.empty else 0
            minority_pct = 100.0 * float(n_rows - mode_cnt) / float(n_rows)
            if minority_pct < self.near_constant_threshold_pct:
                dropped.append(str(col))
            else:
                active.append(str(col))
        return tuple(active), tuple(dropped)


class AuditedStandardBinaryScaler(DenseScaleStrategy):
    """Drop near-constant columns, StandardScaler on continuous/ordinal cols, keep binaries in {0, 1}.

    Fitted exclusively on train. Putting continuous and ordinal columns at unit variance (std=1)
    while leaving legitimate binaries in {0, 1} ensures comparable pairwise contributions without
    amplifying rare binary flags (e.g., es_vigente at 5.47% -> 4.4 SD if standardized).
    """

    def __init__(self, near_constant_threshold_pct: float = 1.0) -> None:
        super().__init__(
            strategy_name="audited_standard_plus_binary01",
            near_constant_threshold_pct=near_constant_threshold_pct,
        )
        self.scaled_columns_: Tuple[str, ...] = ()
        self.binary_passthrough_columns_: Tuple[str, ...] = ()
        self.scaler_: StandardScaler | None = None

    def fit(self, dense_train_df: pd.DataFrame) -> "AuditedStandardBinaryScaler":
        active, dropped = self._identify_active_columns(dense_train_df)
        self.active_columns_ = active
        self.dropped_columns_ = dropped

        bin_set = set(BINARY_DENSE_FEATURES)
        self.scaled_columns_ = tuple(c for c in active if c not in bin_set)
        self.binary_passthrough_columns_ = tuple(c for c in active if c in bin_set)

        if self.scaled_columns_:
            scaler = StandardScaler()
            scaler.fit(dense_train_df[list(self.scaled_columns_)].to_numpy(dtype=np.float64))
            self.scaler_ = scaler
        else:
            self.scaler_ = None

        self._is_fitted = True
        return self

    def transform(self, dense_df: pd.DataFrame) -> np.ndarray:
        self._check_fitted()
        n_rows = len(dense_df)
        out = np.empty((n_rows, len(self.active_columns_)), dtype=np.float32)

        scaled_arr: np.ndarray | None = None
        if self.scaled_columns_ and self.scaler_ is not None:
            raw_scaled = dense_df[list(self.scaled_columns_)].to_numpy(dtype=np.float64)
            scaled_arr = self.scaler_.transform(raw_scaled).astype(np.float32, copy=False)

        scaled_pos = {c: i for i, c in enumerate(self.scaled_columns_)}
        for col_idx, col_name in enumerate(self.active_columns_):
            if col_name in scaled_pos and scaled_arr is not None:
                out[:, col_idx] = scaled_arr[:, scaled_pos[col_name]]
            else:
                out[:, col_idx] = dense_df[col_name].to_numpy(dtype=np.float32, copy=False)

        return np.ascontiguousarray(out, dtype=np.float32)

    def describe_es(self) -> str:
        return (
            "Descarta casi constantes (< 1 % minoría en train); aplica StandardScaler (solo train) "
            "a continuas y ordinales, y conserva binarias legítimas en {0, 1}."
        )


class RawDensePassthroughScaler(DenseScaleStrategy):
    """Drop near-constant columns only, preserving the original dense_clean scales untouched."""

    def __init__(self, near_constant_threshold_pct: float = 1.0) -> None:
        super().__init__(
            strategy_name="raw_dense_clean_active",
            near_constant_threshold_pct=near_constant_threshold_pct,
        )

    def fit(self, dense_train_df: pd.DataFrame) -> "RawDensePassthroughScaler":
        active, dropped = self._identify_active_columns(dense_train_df)
        self.active_columns_ = active
        self.dropped_columns_ = dropped
        self._is_fitted = True
        return self

    def transform(self, dense_df: pd.DataFrame) -> np.ndarray:
        self._check_fitted()
        arr = dense_df[list(self.active_columns_)].to_numpy(dtype=np.float32, copy=True)
        return np.ascontiguousarray(arr, dtype=np.float32)

    def describe_es(self) -> str:
        return (
            "Conserva las columnas activas en su escala original de dense_clean "
            "(RobustScaler + MinMax + bins uint8 sin reescalar + binarias 0/1)."
        )


class TukeyWinsorizedStandardScaler(DenseScaleStrategy):
    """Clip continuous columns to train-only Tukey fences (Q1 - 1.5*IQR, Q3 + 1.5*IQR), then apply audited scaling."""

    def __init__(self, near_constant_threshold_pct: float = 1.0) -> None:
        super().__init__(
            strategy_name="tukey_winsorized_audited_standard",
            near_constant_threshold_pct=near_constant_threshold_pct,
        )
        self.fences_: Dict[str, Tuple[float, float]] = {}
        self.inner_scaler_: AuditedStandardBinaryScaler | None = None

    def fit(self, dense_train_df: pd.DataFrame) -> "TukeyWinsorizedStandardScaler":
        active, dropped = self._identify_active_columns(dense_train_df)
        self.active_columns_ = active
        self.dropped_columns_ = dropped

        cont_set = set(CONTINUOUS_ROB_FEATURES)
        work = dense_train_df.copy()
        fences: Dict[str, Tuple[float, float]] = {}
        for col in active:
            if col in cont_set:
                vals = work[col].to_numpy(dtype=np.float64)
                q1, q3 = np.percentile(vals, [25.0, 75.0])
                iqr = float(q3 - q1)
                low_f = float(q1 - 1.5 * iqr)
                high_f = float(q3 + 1.5 * iqr)
                fences[col] = (low_f, high_f)
                work[col] = np.clip(vals, low_f, high_f)

        self.fences_ = fences
        inner = AuditedStandardBinaryScaler(
            near_constant_threshold_pct=self.near_constant_threshold_pct
        )
        inner.fit(work)
        # Ensure identical active column ordering
        self.active_columns_ = inner.active_columns_
        self.dropped_columns_ = inner.dropped_columns_
        self.inner_scaler_ = inner
        self._is_fitted = True
        return self

    def transform(self, dense_df: pd.DataFrame) -> np.ndarray:
        self._check_fitted()
        if self.inner_scaler_ is None:
            raise RuntimeError("Inner scaler not fitted.")
        work = dense_df.copy()
        for col, (low_f, high_f) in self.fences_.items():
            vals = work[col].to_numpy(dtype=np.float64)
            work[col] = np.clip(vals, low_f, high_f)
        return self.inner_scaler_.transform(work)

    def describe_es(self) -> str:
        return (
            "Recorta las columnas continuas activas a las vallas de Tukey ajustadas solo en train "
            "(Q1 - 1.5*IQR, Q3 + 1.5*IQR) y aplica después el escalado auditado."
        )


@dataclass(frozen=True)
class KNNPartitionBlocks:
    """Aligned KNN feature matrices, ISCO dummies, OHE sparse block, target, and person groups."""

    split_name: str
    dense_clean_df: pd.DataFrame
    X_dense_scaled: np.ndarray
    X_dense_raw_active: np.ndarray
    X_isco_major: np.ndarray
    ohe_sparse: sparse.csr_matrix
    active_dense_features: Tuple[str, ...]
    dropped_dense_features: Tuple[str, ...]
    isco_feature_names: Tuple[str, ...]
    ohe_feature_names: Tuple[str, ...]
    y: np.ndarray
    groups: np.ndarray

    def build_knn_d_matrix(self, row_idx: np.ndarray | None = None) -> np.ndarray:
        """Return dense float32 feature matrix for KNN-D (optionally sliced by row_idx)."""
        if row_idx is None:
            return self.X_dense_scaled
        return np.ascontiguousarray(self.X_dense_scaled[row_idx], dtype=np.float32)

    def build_knn_g_matrix(
        self,
        w_g: float = 1.0,
        row_idx: np.ndarray | None = None,
    ) -> np.ndarray:
        """Return dense float32 matrix for KNN-G: [dense_scaled, w_g * isco_major_dummies]."""
        X_d = self.X_dense_scaled if row_idx is None else self.X_dense_scaled[row_idx]
        X_g = self.X_isco_major if row_idx is None else self.X_isco_major[row_idx]
        scaled_isco = (X_g * np.float32(w_g)).astype(np.float32, copy=False)
        return np.ascontiguousarray(np.hstack([X_d, scaled_isco]), dtype=np.float32)

    def build_knn_w_matrix(
        self,
        w: float = 1.0,
        row_idx: np.ndarray | None = None,
    ) -> sparse.csr_matrix:
        """Return sparse CSR float32 matrix for KNN-W: [dense_scaled, w * occupation_ohe]."""
        X_d = self.X_dense_scaled if row_idx is None else self.X_dense_scaled[row_idx]
        X_ohe = self.ohe_sparse if row_idx is None else self.ohe_sparse[row_idx]
        dense_csr = sparse.csr_matrix(np.asarray(X_d, dtype=np.float32))
        if float(w) == 0.0:
            zero_ohe = sparse.csr_matrix(X_ohe.shape, dtype=np.float32)
            return sparse.hstack([dense_csr, zero_ohe], format="csr", dtype=np.float32)
        weighted_ohe = X_ohe.astype(np.float32, copy=True)
        if float(w) != 1.0:
            weighted_ohe.data *= np.float32(w)
        return sparse.hstack([dense_csr, weighted_ohe], format="csr", dtype=np.float32)


@dataclass(frozen=True)
class KNNVersionBundle:
    """Complete Version A or B bundle with verified PreparedPartitions, KNN blocks, audits, and original units."""

    version: str
    modeling_data: VersionModelingData
    train_blocks: KNNPartitionBlocks
    test_blocks: KNNPartitionBlocks
    orig_train: pd.DataFrame | None
    orig_test: pd.DataFrame | None
    scaler: AuditedStandardBinaryScaler
    isco_builder: ISCOBlockBuilder
    scale_audit_table: pd.DataFrame
    alignment_checks: Dict[str, object]


class KNNFeatureBuilder:
    """Build leakage-free KNN matrices, train-only scalers, scale audits, and verified ISCO joins."""

    def __init__(
        self,
        config: KNNConfig,
        scale_strategy: DenseScaleStrategy | None = None,
    ) -> None:
        self.config = config
        self._base_builder = ModelingDatasetBuilder(config.to_modeling_config())
        self._scale_strategy = scale_strategy

    @staticmethod
    def _verify_no_leakage_or_id(
        dense_df: pd.DataFrame,
        ohe_feature_names: Sequence[str],
    ) -> None:
        """Assert zero leakage columns and zero person-identifier columns in feature matrices."""
        all_cols = set(dense_df.columns) | set(ohe_feature_names)
        for col in PROHIBITED_CONCEPTUAL_COLUMNS:
            if col in all_cols:
                raise AssertionError(f"Prohibited leakage column '{col}' detected in X!")
        for col in LEAKAGE_FEATURES_IN_X:
            if col in all_cols:
                raise AssertionError(f"Leakage feature '{col}' detected in X!")
        if "resume_id" in all_cols:
            raise AssertionError("Identifier 'resume_id' must never enter feature matrix X!")

    def _load_original_metadata_splits(
        self,
        version: str,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Rebuild clean original-unit metadata splits (including isco_group) from the clean CSV."""
        usecols = [
            "resume_id",
            "start_date",
            "end_date",
            "university_level",
            "matched_code",
            "occupation_code",
            "occupation_label",
            "isco_group",
            "isco_group_label",
            "n_skills_essential",
            "n_skills_competence",
            "n_skills_knowledge",
            "n_skills_sin_tipo",
            "veces_ese_oficio",
            "es_vigente",
        ]
        raw_df = pd.read_csv(
            self.config.clean_csv_path(version),
            usecols=usecols,
            dtype=str,
            encoding="utf-8",
            keep_default_na=False,
            na_values=[""],
        )
        work = raw_df.copy()
        del raw_df

        occupation = work["occupation_code"].fillna("").astype(str).str.strip()
        fusion = occupation.eq("") & work["matched_code"].astype(str).str.strip().ne("unknown")
        occupation.loc[fusion] = work.loc[fusion, "matched_code"].astype(str)
        work["occupation_code"] = occupation.replace("", pd.NA).fillna("unknown")

        work = add_date_ordinals(work, "start_date", "end_date")
        work = add_start_year(work)
        work = add_job_order(work, "resume_id", "start_ord")

        for col in (
            "n_skills_essential",
            "n_skills_competence",
            "n_skills_knowledge",
            "n_skills_sin_tipo",
            "veces_ese_oficio",
        ):
            work[col] = pd.to_numeric(work[col], errors="coerce")

        work["es_vigente"] = (
            work["es_vigente"]
            .astype(str)
            .str.strip()
            .str.lower()
            .map({"true": 1, "false": 0, "1": 1, "0": 0})
            .fillna(0)
            .astype(np.int8)
        )

        classified = work.loc[work["n_skills_essential"].notna()].reset_index(drop=True)
        del work

        train_df, test_df = group_train_test_split(
            classified,
            group_col="resume_id",
            test_size=self.config.test_size,
            random_state=self.config.random_state,
        )
        del classified

        return self._format_original_df(train_df), self._format_original_df(test_df)

    @staticmethod
    def _format_original_df(df_split: pd.DataFrame) -> pd.DataFrame:
        """Format clean descriptive columns in original units with standardized 4-char ISCO text."""
        orig = pd.DataFrame(index=df_split.index)
        orig["resume_id"] = df_split["resume_id"].astype(str)
        orig["reincide"] = (pd.to_numeric(df_split["veces_ese_oficio"], errors="coerce") > 1).astype(
            np.int8
        )
        orig["occupation_code"] = df_split["occupation_code"].astype(str).str.strip()
        orig["occupation_label"] = (
            df_split["occupation_label"].fillna("Sin etiqueta").astype(str).str.strip()
        )

        isco_clean = (
            df_split["isco_group"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.replace(r"\.0$", "", regex=True)
        )
        isco_clean = isco_clean.where(isco_clean.eq(""), isco_clean.str.zfill(4))
        orig["isco_group"] = isco_clean
        orig["isco_group_label"] = (
            df_split["isco_group_label"].fillna("Sin etiqueta").astype(str).str.strip()
        )
        orig["isco_major"] = isco_clean.str.slice(0, 1)
        orig["isco_major_label_es"] = (
            orig["isco_major"].map(ISCO_MAJOR_LABELS_ES).fillna("Sin grupo ISCO")
        )
        orig["isco_sub2"] = isco_clean.str.slice(0, 2)

        orig["university_level"] = (
            df_split["university_level"]
            .replace("", pd.NA)
            .fillna("No reportado")
            .astype(str)
            .str.strip()
        )
        orig["start_ord"] = pd.to_numeric(df_split["start_ord"], errors="coerce").astype(np.float32)
        orig["end_ord"] = pd.to_numeric(df_split["end_ord"], errors="coerce").astype(np.float32)
        orig["dur_q"] = pd.to_numeric(df_split["dur_q"], errors="coerce").astype(np.float32)
        orig["start_year"] = pd.to_numeric(df_split["start_year"], errors="coerce").astype(
            np.float32
        )
        orig["job_order"] = pd.to_numeric(df_split["job_order"], errors="coerce").astype(np.int32)
        orig["previous_jobs"] = (orig["job_order"] - 1).clip(lower=0).astype(np.int32)

        for col in (
            "n_skills_essential",
            "n_skills_competence",
            "n_skills_knowledge",
            "n_skills_sin_tipo",
        ):
            orig[col] = pd.to_numeric(df_split[col], errors="coerce").astype(np.float32)

        orig["es_vigente"] = df_split["es_vigente"].astype(np.int8)
        return orig.reset_index(drop=True)

    @staticmethod
    def verify_row_alignment(
        orig_df: pd.DataFrame,
        partition: PreparedPartition,
        split_label: str,
    ) -> None:
        """Strict row-by-row alignment check between ISCO/original metadata and PreparedPartition."""
        if len(orig_df) != len(partition.y):
            raise AssertionError(
                f"Row count mismatch on {split_label}: metadata={len(orig_df)} vs partition={len(partition.y)}."
            )
        if not np.array_equal(orig_df["reincide"].to_numpy(dtype=np.int8), partition.y.astype(np.int8)):
            raise AssertionError(
                f"Row-by-row target y mismatch on {split_label} between ISCO metadata and PreparedPartition!"
            )
        if not np.array_equal(
            orig_df["resume_id"].to_numpy(dtype=str),
            np.asarray(partition.groups, dtype=str),
        ):
            raise AssertionError(
                f"Row-by-row person groups mismatch on {split_label} between ISCO metadata and PreparedPartition!"
            )

    @staticmethod
    def build_scale_audit_table(
        dense_train_df: pd.DataFrame,
        X_train_scaled: np.ndarray,
        scaler: AuditedStandardBinaryScaler,
    ) -> pd.DataFrame:
        """Build the Spanish scale-audit table documenting real ranges, std before/after, and decisions."""
        n_rows = max(int(len(dense_train_df)), 1)
        active_pos = {c: i for i, c in enumerate(scaler.active_columns_)}
        scaled_set = set(scaler.scaled_columns_)
        bin_set = set(scaler.binary_passthrough_columns_)

        rows: List[Dict[str, object]] = []
        for col in ALL_DENSE_CLEAN_FEATURES:
            s = dense_train_df[col].to_numpy(dtype=np.float64)
            q01, q25, q50, q75, q99 = np.percentile(s, [1.0, 25.0, 50.0, 75.0, 99.0])
            vc = dense_train_df[col].value_counts(dropna=False)
            min_pct = 100.0 * float(n_rows - int(vc.iloc[0])) / float(n_rows)

            if col in active_pos:
                s_after = X_train_scaled[:, active_pos[col]].astype(np.float64)
                std_after = round(float(np.std(s_after)), 4)
                rng_after = f"[{float(s_after.min()):.2f}, {float(s_after.max()):.2f}]"
                if col in scaled_set:
                    decision = "Conservada · StandardScaler (solo train)"
                    reason = (
                        "Iguala varianza a 1.0 para que ninguna continua ni bin ordinal sin escalar domine la distancia."
                    )
                elif col in bin_set:
                    decision = "Conservada · Binaria 0/1 sin estandarizar"
                    reason = (
                        "Mantiene diferencia binaria en {0, 1} (comparable a 1 DE) evitando inflar banderas raras."
                    )
                else:
                    decision = "Conservada"
                    reason = "Columna activa."
            else:
                std_after = np.nan
                rng_after = "Descartada"
                decision = "Descartada (casi constante < 1 %)"
                reason = (
                    f"Minoría de solo {min_pct:.4f} % en train; aporta ruido o distancia casi nula."
                )

            rows.append(
                {
                    "columna": col,
                    "tipo_original": DENSE_FEATURE_METADATA_ES[col]["tipo"],
                    "dtype_original": str(dense_train_df[col].dtype),
                    "valores_unicos_train": int(len(vc)),
                    "pct_minoria_train": round(min_pct, 4),
                    "min_train": round(float(s.min()), 4),
                    "p01_train": round(float(q01), 4),
                    "mediana_train": round(float(q50), 4),
                    "p99_train": round(float(q99), 4),
                    "max_train": round(float(s.max()), 4),
                    "iqr_train": round(float(q75 - q25), 4),
                    "std_antes_train": round(float(np.std(s)), 4),
                    "std_despues_train": std_after,
                    "rango_despues_train": rng_after,
                    "decision_escala_knn": decision,
                    "justificacion": reason,
                }
            )
        return pd.DataFrame(rows)

    def build_version_bundle(
        self,
        version: str = VERSION_CON,
        include_original_units: bool = True,
    ) -> KNNVersionBundle:
        """Build verified KNN feature matrices and aligned ISCO/original metadata for Version A or B."""
        modeling_data = self._base_builder.build_version(version)
        train_part = modeling_data.train
        test_part = modeling_data.test

        # Order dense_clean deterministically
        dense_tr = train_part.dense_clean[list(ALL_DENSE_CLEAN_FEATURES)].copy()
        dense_te = test_part.dense_clean[list(ALL_DENSE_CLEAN_FEATURES)].copy()

        self._verify_no_leakage_or_id(dense_tr, train_part.ohe_feature_names)
        self._verify_no_leakage_or_id(dense_te, test_part.ohe_feature_names)

        shared_persons = len(set(train_part.groups).intersection(set(test_part.groups)))
        if shared_persons != 0:
            raise AssertionError(
                f"Overlapping persons detected between train and test: {shared_persons}"
            )

        # Load clean metadata splits (for isco_group and original units) and strictly verify alignment
        orig_train_df, orig_test_df = self._load_original_metadata_splits(version)
        self.verify_row_alignment(orig_train_df, train_part, split_label=f"{version}/train")
        self.verify_row_alignment(orig_test_df, test_part, split_label=f"{version}/test")

        # Fit train-only scaler on dense_clean
        scaler = AuditedStandardBinaryScaler(
            near_constant_threshold_pct=self.config.near_constant_threshold_pct
        )
        X_tr_scaled = scaler.fit_transform(dense_tr)
        X_te_scaled = scaler.transform(dense_te)

        raw_passthrough = RawDensePassthroughScaler(
            near_constant_threshold_pct=self.config.near_constant_threshold_pct
        )
        X_tr_raw_active = raw_passthrough.fit_transform(dense_tr)
        X_te_raw_active = raw_passthrough.transform(dense_te)

        # Build 10 ISCO major-group dummies via ArbolDecision.ISCOBlockBuilder (fit on train only)
        isco_builder = ISCOBlockBuilder(granularity="major_1d")
        isco_tr_df = isco_builder.fit_transform(orig_train_df)[list(ISCO_MAJOR_DUMMY_COLS)]
        isco_te_df = isco_builder.transform(orig_test_df)[list(ISCO_MAJOR_DUMMY_COLS)]

        X_tr_isco = np.ascontiguousarray(isco_tr_df.to_numpy(dtype=np.float32, copy=True))
        X_te_isco = np.ascontiguousarray(isco_te_df.to_numpy(dtype=np.float32, copy=True))

        # Verify each row belongs to at most 1 ISCO major group (strictly 1 in JobPath classified universe)
        if not np.all(X_tr_isco.sum(axis=1) == 1.0):
            raise AssertionError("Unexpected ISCO major-group dummy row sum != 1 on train.")
        if not np.all(X_te_isco.sum(axis=1) == 1.0):
            raise AssertionError("Unexpected ISCO major-group dummy row sum != 1 on test.")

        scale_audit_df = self.build_scale_audit_table(dense_tr, X_tr_scaled, scaler)

        train_blocks = KNNPartitionBlocks(
            split_name="train",
            dense_clean_df=dense_tr,
            X_dense_scaled=X_tr_scaled,
            X_dense_raw_active=X_tr_raw_active,
            X_isco_major=X_tr_isco,
            ohe_sparse=train_part.ohe_sparse.astype(np.float32),
            active_dense_features=scaler.active_columns_,
            dropped_dense_features=scaler.dropped_columns_,
            isco_feature_names=ISCO_MAJOR_DUMMY_COLS,
            ohe_feature_names=tuple(train_part.ohe_feature_names),
            y=train_part.y.astype(np.int8, copy=False),
            groups=np.asarray(train_part.groups, dtype=str),
        )
        test_blocks = KNNPartitionBlocks(
            split_name="test",
            dense_clean_df=dense_te,
            X_dense_scaled=X_te_scaled,
            X_dense_raw_active=X_te_raw_active,
            X_isco_major=X_te_isco,
            ohe_sparse=test_part.ohe_sparse.astype(np.float32),
            active_dense_features=scaler.active_columns_,
            dropped_dense_features=scaler.dropped_columns_,
            isco_feature_names=ISCO_MAJOR_DUMMY_COLS,
            ohe_feature_names=tuple(test_part.ohe_feature_names),
            y=test_part.y.astype(np.int8, copy=False),
            groups=np.asarray(test_part.groups, dtype=str),
        )

        alignment_checks = {
            "version": version,
            "filas_train": int(len(train_blocks.y)),
            "filas_test": int(len(test_blocks.y)),
            "personas_train": int(len(np.unique(train_blocks.groups))),
            "personas_test": int(len(np.unique(test_blocks.groups))),
            "personas_solapadas": int(shared_persons),
            "prevalencia_train_pct": round(100.0 * float(train_blocks.y.mean()), 2),
            "prevalencia_test_pct": round(100.0 * float(test_blocks.y.mean()), 2),
            "cols_dense_clean_iniciales": int(dense_tr.shape[1]),
            "cols_densas_activas_knn_d": int(len(scaler.active_columns_)),
            "cols_descartadas_casi_constantes": ", ".join(scaler.dropped_columns_),
            "cols_knn_g": int(len(scaler.active_columns_) + len(ISCO_MAJOR_DUMMY_COLS)),
            "cols_knn_w": int(len(scaler.active_columns_) + len(train_part.ohe_feature_names)),
            "alineacion_isco_y_groups_train": True,
            "alineacion_isco_y_groups_test": True,
            "fuga_eliminada": True,
        }

        return KNNVersionBundle(
            version=version,
            modeling_data=modeling_data,
            train_blocks=train_blocks,
            test_blocks=test_blocks,
            orig_train=orig_train_df if include_original_units else None,
            orig_test=orig_test_df if include_original_units else None,
            scaler=scaler,
            isco_builder=isco_builder,
            scale_audit_table=scale_audit_df,
            alignment_checks=alignment_checks,
        )
