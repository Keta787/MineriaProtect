"""Feature block assembly, leakage/independence audits, and original-unit alignment for Naive Bayes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from scipy import sparse

from scripts.ScriptsCsv.Modelado.dataset_builder import (
    ModelingDatasetBuilder,
    PreparedPartition,
    VersionModelingData,
)
from scripts.ScriptsCsv.Transformacion.split import (
    TransformArtifacts,
    group_train_test_split,
)

from .config import (
    ALL_DENSE_CLEAN_FEATURES,
    BINARY_DENSE_FEATURES,
    CONTINUOUS_ROB_FEATURES,
    DENSE_FEATURE_METADATA_ES,
    GAUSSIAN_HYBRID_FEATURES,
    ISCO_MAJOR_LABELS_ES,
    LEAKAGE_FEATURES_IN_X,
    NaiveBayesConfig,
    ORDINAL_FEATURES,
    PROHIBITED_CONCEPTUAL_COLUMNS,
    VERSION_CON,
)


@dataclass(frozen=True)
class NaiveBayesPartitionBlocks:
    """Model-specific feature matrices and aligned target/group vectors for one split."""

    split_name: str
    dense_clean_df: pd.DataFrame
    X_nb_g: np.ndarray
    X_nb_b: sparse.csr_matrix
    X_nb_h: sparse.csr_matrix
    nb_g_feature_names: Tuple[str, ...]
    nb_b_feature_names: Tuple[str, ...]
    nb_h_feature_names: Tuple[str, ...]
    continuous_idx: Tuple[int, ...]
    binary_idx: Tuple[int, ...]
    y: np.ndarray
    groups: np.ndarray
    nb_g_star_dropped_features: Tuple[str, ...] = ()


@dataclass(frozen=True)
class NaiveBayesVersionBundle:
    """Complete Version A or B bundle with model blocks, audit tables, and original-unit DataFrames."""

    version: str
    modeling_data: VersionModelingData
    train_blocks: NaiveBayesPartitionBlocks
    test_blocks: NaiveBayesPartitionBlocks
    orig_train: pd.DataFrame | None
    orig_test: pd.DataFrame | None
    feature_block_audit_table: pd.DataFrame
    near_constant_audit_table: pd.DataFrame
    dense_correlation_matrix: pd.DataFrame
    correlated_pairs_table: pd.DataFrame
    alignment_checks: Dict[str, object]


class NaiveBayesFeatureBuilder:
    """Build leakage-free Naive Bayes blocks and aligned original-unit frames."""

    def __init__(self, config: NaiveBayesConfig) -> None:
        self.config = config
        self._base_builder = ModelingDatasetBuilder(config.to_modeling_config())

    @staticmethod
    def _enrich_original_units_df(df_split: pd.DataFrame, y_arr: np.ndarray) -> pd.DataFrame:
        """Prepare clean descriptive columns in original units (quarters, years, counts, ISCO)."""
        orig = pd.DataFrame(index=df_split.index)
        orig["resume_id"] = df_split["resume_id"].astype(str)
        orig["reincide"] = (pd.to_numeric(df_split["veces_ese_oficio"], errors="coerce") > 1).astype(
            np.int8
        )
        if not np.array_equal(orig["reincide"].to_numpy(dtype=np.int8), y_arr.astype(np.int8)):
            raise AssertionError(
                "Row-by-row target mismatch between derived 'reincide' and reference y vector."
            )

        orig["occupation_code"] = df_split["occupation_code"].astype(str).str.strip()
        orig["occupation_label"] = (
            df_split["occupation_label"].fillna("Sin etiqueta").astype(str).str.strip()
            if "occupation_label" in df_split.columns
            else orig["occupation_code"]
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
            if "isco_group_label" in df_split.columns
            else isco_clean
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

        for skill_col in (
            "n_skills_essential",
            "n_skills_competence",
            "n_skills_knowledge",
            "n_skills_sin_tipo",
        ):
            orig[skill_col] = pd.to_numeric(df_split[skill_col], errors="coerce").astype(np.float32)

        for bin_col in ("es_vigente", "tiene_skills", "tiene_knowledge", "tiene_sin_tipo"):
            orig[bin_col] = pd.to_numeric(df_split[bin_col], errors="coerce").fillna(0).astype(
                np.int8
            )

        return orig.reset_index(drop=True)

    @staticmethod
    def build_partition_blocks(
        partition: PreparedPartition,
        split_name: str,
        nb_g_star_dropped_features: Tuple[str, ...] = (),
    ) -> NaiveBayesPartitionBlocks:
        """Assemble NB-G, NB-B, and NB-H feature matrices from a PreparedPartition."""
        dense_df = partition.dense_clean
        actual_cols = tuple(dense_df.columns)
        if actual_cols != ALL_DENSE_CLEAN_FEATURES:
            missing = set(ALL_DENSE_CLEAN_FEATURES) - set(actual_cols)
            if missing:
                raise KeyError(f"Missing expected dense_clean columns: {missing}")
            dense_df = dense_df[list(ALL_DENSE_CLEAN_FEATURES)].copy()

        # Verify no prohibited or leakage columns exist in dense_clean or OHE names
        all_names_set = set(dense_df.columns) | set(partition.ohe_feature_names)
        for prohibited in PROHIBITED_CONCEPTUAL_COLUMNS:
            if prohibited in all_names_set:
                raise AssertionError(f"Prohibited leakage column '{prohibited}' found in X!")
        if "resume_id" in all_names_set:
            raise AssertionError("Person identifier 'resume_id' must never enter X!")

        # 1. NB-G: 14 columns of dense_clean as float32 dense array
        X_nb_g = np.ascontiguousarray(dense_df.to_numpy(dtype=np.float32, copy=True))
        nb_g_names = tuple(dense_df.columns)

        # 2. NB-B: 4 dense binary columns + 2,967 sparse occupation dummies
        bin_dense_np = dense_df[list(BINARY_DENSE_FEATURES)].to_numpy(dtype=np.float32, copy=True)
        if not np.isin(bin_dense_np, [0.0, 1.0]).all():
            raise AssertionError("Dense binary features for BernoulliNB must be strictly 0 or 1.")

        ohe_csr = partition.ohe_sparse.astype(np.float32)
        if ohe_csr.nnz > 0 and not np.isin(ohe_csr.data, [0.0, 1.0]).all():
            raise AssertionError("OHE sparse matrix for BernoulliNB must contain only 0/1 entries.")

        bin_dense_csr = sparse.csr_matrix(bin_dense_np)
        X_nb_b = sparse.hstack([bin_dense_csr, ohe_csr], format="csr")
        nb_b_names = tuple(BINARY_DENSE_FEATURES) + tuple(partition.ohe_feature_names)

        # 3. NB-H: 10 Gaussian columns (7 continuous + univ_ord_mm + 2 bins) + 2,971 binary columns
        gauss_10_np = dense_df[list(GAUSSIAN_HYBRID_FEATURES)].to_numpy(dtype=np.float32, copy=True)
        gauss_10_csr = sparse.csr_matrix(gauss_10_np)
        X_nb_h = sparse.hstack([gauss_10_csr, X_nb_b], format="csr")
        nb_h_names = tuple(GAUSSIAN_HYBRID_FEATURES) + nb_b_names

        n_gauss = len(GAUSSIAN_HYBRID_FEATURES)
        n_bin = len(nb_b_names)
        continuous_idx = tuple(range(n_gauss))
        binary_idx = tuple(range(n_gauss, n_gauss + n_bin))

        return NaiveBayesPartitionBlocks(
            split_name=split_name,
            dense_clean_df=dense_df,
            X_nb_g=X_nb_g,
            X_nb_b=X_nb_b,
            X_nb_h=X_nb_h,
            nb_g_feature_names=nb_g_names,
            nb_b_feature_names=nb_b_names,
            nb_h_feature_names=nb_h_names,
            continuous_idx=continuous_idx,
            binary_idx=binary_idx,
            y=partition.y.astype(np.int8, copy=False),
            groups=partition.groups,
            nb_g_star_dropped_features=nb_g_star_dropped_features,
        )

    @staticmethod
    def audit_near_constant_columns(
        dense_train_df: pd.DataFrame,
        minority_threshold_pct: float = 1.0,
    ) -> Tuple[pd.DataFrame, Tuple[str, ...]]:
        """Audit dense columns for near-constant distribution (< 1% minority share on train).

        Binary or ordinal columns below ``minority_threshold_pct`` are flagged for exclusion
        in the NB-G* ablation variant (Sections 5 and 6).
        """
        n_rows = int(len(dense_train_df))
        bin_or_ord = set(BINARY_DENSE_FEATURES) | set(ORDINAL_FEATURES)
        rows: List[Dict[str, object]] = []
        dropped_for_nb_g_star: List[str] = []

        for col in ALL_DENSE_CLEAN_FEATURES:
            s = dense_train_df[col]
            vc = s.value_counts(dropna=False)
            n_uniq = int(len(vc))
            mode_val = float(vc.index[0])
            mode_cnt = int(vc.iloc[0])
            minority_cnt = n_rows - mode_cnt
            mode_pct = 100.0 * float(mode_cnt) / float(max(n_rows, 1))
            minority_pct = 100.0 * float(minority_cnt) / float(max(n_rows, 1))
            is_bin_ord = col in bin_or_ord
            is_near_const = minority_pct < minority_threshold_pct
            drop_star = is_bin_ord and is_near_const
            if drop_star:
                dropped_for_nb_g_star.append(col)

            if drop_star:
                note = "Excluida en NB-G* (binaria/ordinal con minoría < 1 %)"
            elif is_near_const:
                note = "Conteo continuo discreto con minoría < 1 % (conservada en NB-G*; documentada)"
            else:
                note = "Conservada (minoría >= 1 %)"

            rows.append(
                {
                    "variable": col,
                    "naturaleza": DENSE_FEATURE_METADATA_ES[col]["tipo"],
                    "es_binaria_u_ordinal": bool(is_bin_ord),
                    "valores_unicos_train": n_uniq,
                    "valor_modal_train": round(mode_val, 4),
                    "pct_modal_train": round(mode_pct, 4),
                    "soporte_minoria_train": int(minority_cnt),
                    "pct_minoria_train": round(minority_pct, 4),
                    "casi_constante_lt_1pct": bool(is_near_const),
                    "excluida_en_NB_G_star": bool(drop_star),
                    "observacion": note,
                }
            )

        audit_df = (
            pd.DataFrame(rows)
            .sort_values(["excluida_en_NB_G_star", "pct_minoria_train"], ascending=[False, True])
            .reset_index(drop=True)
        )
        return audit_df, tuple(dropped_for_nb_g_star)

    @staticmethod
    def build_feature_block_audit_table(
        train_blocks: NaiveBayesPartitionBlocks,
        base_audit_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Build the Spanish feature audit table showing column, type, and Naive Bayes block membership."""
        corr_map = dict(
            zip(base_audit_df["variable"], base_audit_df["corr_train_con_target"])
        )
        rows: List[Dict[str, object]] = []
        for col in ALL_DENSE_CLEAN_FEATURES:
            meta = DENSE_FEATURE_METADATA_ES[col]
            in_g = "Sí (Gaussiana)"
            in_b = "Sí (Bernoulli)" if col in BINARY_DENSE_FEATURES else "No"
            in_h = (
                "Submodelo Gaussiano (10 cols)"
                if col in GAUSSIAN_HYBRID_FEATURES
                else "Submodelo Bernoulli (2,971 cols)"
            )
            rows.append(
                {
                    "variable": col,
                    "naturaleza": meta["tipo"],
                    "bloque_comportamiento": meta["bloque_comportamiento"],
                    "unidad_original": meta["unidad_original"],
                    "corr_train_target": round(float(corr_map.get(col, 0.0)), 4),
                    "entra_en_NB_G": in_g,
                    "entra_en_NB_B": in_b,
                    "entra_en_NB_H": in_h,
                    "descripcion": meta["descripcion"],
                }
            )

        n_ohe = len(train_blocks.nb_b_feature_names) - len(BINARY_DENSE_FEATURES)
        rows.append(
            {
                "variable": f"occupation_code_* ({n_ohe:,} dummies OHE)",
                "naturaleza": "Binaria dispersa (0/1 CSR)",
                "bloque_comportamiento": "Ocupación",
                "unidad_original": "Código de ocupación ESCO (occupation_code)",
                "corr_train_target": np.nan,
                "entra_en_NB_G": "No (exigiría ~16.6 GB en denso)",
                "entra_en_NB_B": f"Sí (Bernoulli, {n_ohe:,} cols)",
                "entra_en_NB_H": f"Submodelo Bernoulli ({n_ohe:,} cols)",
                "descripcion": "Indicadores binarios de oficio ajustados en train sin fuga del target.",
            }
        )
        return pd.DataFrame(rows)

    @staticmethod
    def compute_dense_correlations(
        dense_train_df: pd.DataFrame,
        threshold: float = 0.25,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Compute Pearson and Spearman correlations on dense_clean and list pairs violating independence."""
        # Identify non-constant columns to avoid NaN division warnings on zero-variance features
        stds = dense_train_df.std(axis=0)
        pearson_df = dense_train_df.corr(method="pearson").fillna(0.0)
        spearman_df = dense_train_df.corr(method="spearman").fillna(0.0)

        cols = list(dense_train_df.columns)
        pair_rows: List[Dict[str, object]] = []
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                c1, c2 = cols[i], cols[j]
                if stds[c1] == 0.0 or stds[c2] == 0.0:
                    continue
                r_p = float(pearson_df.loc[c1, c2])
                r_s = float(spearman_df.loc[c1, c2])
                max_abs = max(abs(r_p), abs(r_s))
                if max_abs >= threshold:
                    if max_abs >= 0.70:
                        risk = "Alto (doble conteo fuerte de señal compartida)"
                    elif max_abs >= 0.45:
                        risk = "Moderado-Alto (dependencia estructural entre variables)"
                    else:
                        risk = "Moderado (asociación parcial en la trayectoria)"
                    pair_rows.append(
                        {
                            "variable_a": c1,
                            "variable_b": c2,
                            "bloque_a": DENSE_FEATURE_METADATA_ES[c1]["bloque_comportamiento"],
                            "bloque_b": DENSE_FEATURE_METADATA_ES[c2]["bloque_comportamiento"],
                            "r_pearson_train": round(r_p, 4),
                            "rho_spearman_train": round(r_s, 4),
                            "max_abs_corr": round(max_abs, 4),
                            "riesgo_violacion_independencia": risk,
                        }
                    )

        pairs_df = (
            pd.DataFrame(pair_rows)
            .sort_values("max_abs_corr", ascending=False)
            .reset_index(drop=True)
        )
        return pearson_df.round(4), pairs_df

    def build_version_bundle(
        self,
        version: str = VERSION_CON,
        include_original_units: bool = True,
    ) -> NaiveBayesVersionBundle:
        """Load one dataset version in a single CSV pass, building model blocks and aligned original units."""
        usecols = [
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
        derived_df = self._base_builder._derive_features(raw_df)
        del raw_df

        classified = derived_df.loc[derived_df["n_skills_essential"].notna()].reset_index(drop=True)
        del derived_df

        train_df, test_df = group_train_test_split(
            classified,
            group_col="resume_id",
            test_size=self.config.test_size,
            random_state=self.config.random_state,
        )
        del classified

        y_train = pd.read_csv(self.config.y_path(version, "train")).iloc[:, 0]
        y_test = pd.read_csv(self.config.y_path(version, "test")).iloc[:, 0]
        artifacts: TransformArtifacts = joblib.load(self.config.transformers_path(version))

        train_part = self._base_builder._build_partition(train_df, y_train, artifacts)
        test_part = self._base_builder._build_partition(test_df, y_test, artifacts)

        # Verify against exported X_train.csv header and first 100 rows
        x_sample = pd.read_csv(self.config.x_path(version, "train"), nrows=100)
        dense_diff = float(
            np.abs(
                x_sample[list(train_part.dense_all.columns)].to_numpy(dtype=float)
                - train_part.dense_all.iloc[:100].to_numpy(dtype=float)
            ).max()
        )
        shared_persons = len(set(train_part.groups).intersection(set(test_part.groups)))
        if shared_persons != 0:
            raise AssertionError(f"Overlapping persons detected between train and test: {shared_persons}")

        remaining_leakage = [
            c for c in train_part.dense_clean.columns if c in LEAKAGE_FEATURES_IN_X
        ]
        if remaining_leakage:
            raise AssertionError(f"Leakage columns still present: {remaining_leakage}")

        orig_train: pd.DataFrame | None = None
        orig_test: pd.DataFrame | None = None
        if include_original_units:
            orig_train = self._enrich_original_units_df(train_df, train_part.y)
            orig_test = self._enrich_original_units_df(test_df, test_part.y)
            # Mandatory row-by-row alignment asserts required by Section 6
            assert np.array_equal(orig_train["reincide"].to_numpy(dtype=np.int8), train_part.y), (
                "Row-by-row y_train alignment failed between original-units DataFrame and PreparedPartition."
            )
            assert np.array_equal(orig_train["resume_id"].to_numpy(dtype=str), train_part.groups), (
                "Row-by-row groups_train alignment failed between original-units DataFrame and PreparedPartition."
            )
            assert np.array_equal(orig_test["reincide"].to_numpy(dtype=np.int8), test_part.y), (
                "Row-by-row y_test alignment failed between original-units DataFrame and PreparedPartition."
            )
            assert np.array_equal(orig_test["resume_id"].to_numpy(dtype=str), test_part.groups), (
                "Row-by-row groups_test alignment failed between original-units DataFrame and PreparedPartition."
            )

        del train_df, test_df

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
            col_np = train_part.dense_all[col].to_numpy(dtype=np.float64)
            if np.std(col_np) == 0.0:
                corr = 0.0
            else:
                corr = float(np.corrcoef(col_np, train_part.y)[0, 1])
            if col in LEAKAGE_FEATURES_IN_X:
                status = "EXCLUIDA (Fuga directa 100 %)"
                reason = "Reproduce exactamente la definición reincide = (veces_ese_oficio > 1)."
            elif col in self.config.collinear_drop_features:
                status = "EXCLUIDA (Colinealidad alta)"
                reason = (
                    "Redundante con start_ord_rob (r = 1.000)."
                    if col == "start_year_rob"
                    else "Redundante con n_skills_essential_rob (r = 0.952)."
                )
            else:
                status = "CONSERVADA (Feature legítima)"
                reason = "Variable predictora válida sin circularidad directa con el target."
            audit_rows.append(
                {
                    "variable": col,
                    "corr_train_con_target": round(corr, 4),
                    "estado_fase4": status,
                    "justificacion": reason,
                }
            )
        base_audit_df = pd.DataFrame(audit_rows)

        modeling_data = VersionModelingData(
            version=version,
            train=train_part,
            test=test_part,
            verification=verification,
            feature_audit_table=base_audit_df,
        )

        near_const_df, nb_g_star_dropped = self.audit_near_constant_columns(
            train_part.dense_clean, minority_threshold_pct=1.0
        )
        train_blocks = self.build_partition_blocks(
            train_part,
            split_name="train",
            nb_g_star_dropped_features=nb_g_star_dropped,
        )
        test_blocks = self.build_partition_blocks(
            test_part,
            split_name="test",
            nb_g_star_dropped_features=nb_g_star_dropped,
        )
        block_audit_df = self.build_feature_block_audit_table(train_blocks, base_audit_df)
        corr_matrix_df, corr_pairs_df = self.compute_dense_correlations(train_blocks.dense_clean_df)

        alignment_checks = {
            "version": version,
            "train_rows": int(len(train_blocks.y)),
            "test_rows": int(len(test_blocks.y)),
            "train_persons": int(verification["personas_train"]),
            "test_persons": int(verification["personas_test"]),
            "overlapping_persons": int(shared_persons),
            "leakage_columns_in_x": 0,
            "nb_g_shape_train": train_blocks.X_nb_g.shape,
            "nb_g_star_n_cols": int(train_blocks.X_nb_g.shape[1] - len(nb_g_star_dropped)),
            "nb_g_star_dropped": ", ".join(nb_g_star_dropped),
            "nb_b_shape_train": train_blocks.X_nb_b.shape,
            "nb_h_shape_train": train_blocks.X_nb_h.shape,
            "orig_units_aligned_train": bool(orig_train is not None and len(orig_train) == len(train_blocks.y)),
            "orig_units_aligned_test": bool(orig_test is not None and len(orig_test) == len(test_blocks.y)),
        }

        return NaiveBayesVersionBundle(
            version=version,
            modeling_data=modeling_data,
            train_blocks=train_blocks,
            test_blocks=test_blocks,
            orig_train=orig_train,
            orig_test=orig_test,
            feature_block_audit_table=block_audit_df,
            near_constant_audit_table=near_const_df,
            dense_correlation_matrix=corr_matrix_df,
            correlated_pairs_table=corr_pairs_df,
            alignment_checks=alignment_checks,
        )
