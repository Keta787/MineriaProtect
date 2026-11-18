"""Feature builders for the three Decision Tree blocks following SOLID (SRP, OCP, DIP)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List

import numpy as np
import pandas as pd

from .config import (
    EDUCATION_REPORTED_ORDINAL_MAP,
    ISCO_MAJOR_LABELS_ES,
)


class BlockFeatureBuilder(ABC):
    """Abstract base interface for building block-specific feature matrices (fit on train only)."""

    def __init__(self, block_id: str, variant_name: str) -> None:
        self.block_id = block_id
        self.variant_name = variant_name
        self._is_fitted: bool = False

    @abstractmethod
    def fit(self, df_train: pd.DataFrame) -> "BlockFeatureBuilder":
        """Learn any required categories or parameters strictly from the training dataframe."""

    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform a dataframe into the block feature matrix X without modifying the input."""

    def fit_transform(self, df_train: pd.DataFrame) -> pd.DataFrame:
        """Fit on train and return the transformed training feature matrix."""
        return self.fit(df_train).transform(df_train)

    @abstractmethod
    def feature_descriptions(self) -> Dict[str, str]:
        """Return a mapping of feature name to its one-line justification in Spanish."""

    def _check_fitted(self) -> None:
        if not self._is_fitted:
            raise RuntimeError(f"{self.__class__.__name__} must be fitted on train before transform().")


class ISCOBlockBuilder(BlockFeatureBuilder):
    """Feature builder for Tree 1 (ISCO occupation hierarchy dummies)."""

    def __init__(self, granularity: str = "major_1d", top_k_unit: int = 50) -> None:
        super().__init__(block_id="tree_1_isco", variant_name=granularity)
        if granularity not in ("major_1d", "submajor_2d", "top50_unit_4d"):
            raise ValueError(f"Unsupported ISCO granularity: {granularity}")
        self.granularity = granularity
        self.top_k_unit = top_k_unit
        self.learned_categories_: List[str] = []
        self.unit_label_map_: Dict[str, str] = {}

    def fit(self, df_train: pd.DataFrame) -> "ISCOBlockBuilder":
        isco_str = (
            df_train["isco_group"]
            .astype(str)
            .str.strip()
            .str.replace(r"\.0$", "", regex=True)
            .str.zfill(4)
        )
        if self.granularity == "major_1d":
            self.learned_categories_ = [str(d) for d in range(10)]
        elif self.granularity == "submajor_2d":
            submajors = sorted(isco_str.str.slice(0, 2).dropna().unique().tolist())
            self.learned_categories_ = submajors
        elif self.granularity == "top50_unit_4d":
            top_units = (
                isco_str.value_counts(dropna=True)
                .head(self.top_k_unit)
                .index.astype(str)
                .tolist()
            )
            self.learned_categories_ = top_units
            label_df = (
                df_train[["isco_group", "isco_group_label"]]
                .drop_duplicates(subset=["isco_group"])
                .dropna(subset=["isco_group"])
            )
            self.unit_label_map_ = dict(
                zip(
                    label_df["isco_group"]
                    .astype(str)
                    .str.strip()
                    .str.replace(r"\.0$", "", regex=True)
                    .str.zfill(4),
                    label_df["isco_group_label"].astype(str),
                )
            )
        self._is_fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        self._check_fitted()
        isco_str = (
            df["isco_group"]
            .astype(str)
            .str.strip()
            .str.replace(r"\.0$", "", regex=True)
            .str.zfill(4)
        )
        out = pd.DataFrame(index=df.index)

        if self.granularity == "major_1d":
            major_digit = isco_str.str.slice(0, 1)
            for digit in self.learned_categories_:
                col_name = f"isco_major_{digit}"
                out[col_name] = (major_digit == digit).astype("int8")
        elif self.granularity == "submajor_2d":
            submajor = isco_str.str.slice(0, 2)
            for code in self.learned_categories_:
                out[f"isco_sub2_{code}"] = (submajor == code).astype("int8")
        elif self.granularity == "top50_unit_4d":
            top_set = set(self.learned_categories_)
            for code in self.learned_categories_:
                out[f"isco_unit4_{code}"] = (isco_str == code).astype("int8")
            out["isco_unit4_otros"] = (~isco_str.isin(top_set)).astype("int8")

        return out

    def feature_descriptions(self) -> Dict[str, str]:
        self._check_fitted()
        if self.granularity == "major_1d":
            return {
                f"isco_major_{d}": (
                    f"Indicador binario (0/1) del Gran Grupo ISCO-08 {ISCO_MAJOR_LABELS_ES.get(d, d)}"
                )
                for d in self.learned_categories_
            }
        if self.granularity == "submajor_2d":
            return {
                f"isco_sub2_{c}": f"Indicador binario (0/1) del Subgrupo Principal ISCO-08 a 2 dígitos ({c})"
                for c in self.learned_categories_
            }
        desc = {
            f"isco_unit4_{c}": (
                f"Indicador binario (0/1) del Grupo Unitario ISCO-08 {c} "
                f"({self.unit_label_map_.get(c, 'grupo unitario')})"
            )
            for c in self.learned_categories_
        }
        desc["isco_unit4_otros"] = (
            "Indicador binario (0/1) para grupos unitarios ISCO-08 fuera del Top-50 de train"
        )
        return desc


class EducationBlockBuilder(BlockFeatureBuilder):
    """Feature builder for Tree 2 (Ordinal education level + separate 'not reported' flag, never filling nulls with 0)."""

    def __init__(self, encoding_mode: str = "ordinal_nan_plus_flag") -> None:
        super().__init__(block_id="tree_2_education", variant_name=encoding_mode)
        if encoding_mode not in (
            "ordinal_nan_plus_flag",
            "ordinal_neg1_plus_flag",
            "ordinal_nan_plus_flag_and_cycles",
        ):
            raise ValueError(f"Unsupported education encoding_mode: {encoding_mode}")
        self.encoding_mode = encoding_mode

    def fit(self, df_train: pd.DataFrame) -> "EducationBlockBuilder":
        allowed = set(EDUCATION_REPORTED_ORDINAL_MAP.keys()) | {"No reportado"}
        unknown_cats = set(df_train["university_level"].dropna().astype(str).unique()) - allowed
        if unknown_cats:
            raise ValueError(f"Unexpected university_level categories in train: {unknown_cats}")
        self._is_fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        self._check_fitted()
        univ = df["university_level"].fillna("No reportado").astype(str)
        out = pd.DataFrame(index=df.index)

        # Map reported levels to 1..4; leave 'No reportado' as NaN (NEVER fill with 0!)
        ord_series = univ.map(EDUCATION_REPORTED_ORDINAL_MAP).astype("float32")
        not_reported_flag = (univ == "No reportado").astype("float32")

        if self.encoding_mode == "ordinal_nan_plus_flag":
            out["nivel_academico_ord"] = ord_series
            out["educacion_no_reportada"] = not_reported_flag
        elif self.encoding_mode == "ordinal_neg1_plus_flag":
            out["nivel_academico_ord"] = ord_series.fillna(-1.0).astype("float32")
            out["educacion_no_reportada"] = not_reported_flag
        elif self.encoding_mode == "ordinal_nan_plus_flag_and_cycles":
            out["nivel_academico_ord"] = ord_series
            out["educacion_no_reportada"] = not_reported_flag
            out["es_posgrado"] = univ.isin(["Master", "PhD"]).astype("float32")

        return out

    def feature_descriptions(self) -> Dict[str, str]:
        if self.encoding_mode == "ordinal_nan_plus_flag":
            return {
                "nivel_academico_ord": (
                    "Nivel educativo ordinal solo para reportados (1=Secondary school, 2=Bachelor, "
                    "3=Master, 4=PhD; 'No reportado' queda como NaN sin rellenar con 0)"
                ),
                "educacion_no_reportada": (
                    "Bandera binaria separada (0/1) de ausencia informativa (MNAR: 1 si 'No reportado')"
                ),
            }
        if self.encoding_mode == "ordinal_neg1_plus_flag":
            return {
                "nivel_academico_ord": (
                    "Nivel educativo ordinal (1..4 para niveles reportados; -1 para 'No reportado', nunca 0)"
                ),
                "educacion_no_reportada": (
                    "Bandera binaria separada (0/1) de ausencia informativa (MNAR: 1 si 'No reportado')"
                ),
            }
        return {
            "nivel_academico_ord": (
                "Nivel educativo ordinal (1..4 para niveles reportados; NaN para 'No reportado', nunca 0)"
            ),
            "educacion_no_reportada": "Bandera binaria separada (0/1) de ausencia informativa (MNAR)",
            "es_posgrado": "Indicador binario (0/1) de ciclo de posgrado (Master o PhD)",
        }


class SkillsBlockBuilder(BlockFeatureBuilder):
    """Feature builder for Tree 3 (Unscaled ESCO skill counts and block-consistent derived shares)."""

    def __init__(self, feature_set: str = "counts_plus_shares") -> None:
        super().__init__(block_id="tree_3_skills", variant_name=feature_set)
        if feature_set not in ("counts_base", "counts_with_sin_tipo", "counts_plus_shares"):
            raise ValueError(f"Unsupported skills feature_set: {feature_set}")
        self.feature_set = feature_set
        self.sin_tipo_nonzero_in_train_: int = 0

    def fit(self, df_train: pd.DataFrame) -> "SkillsBlockBuilder":
        for col in ("n_skills_essential", "n_skills_competence", "n_skills_knowledge"):
            if col not in df_train.columns:
                raise KeyError(f"Missing required skill column: {col}")
        if "n_skills_sin_tipo" in df_train.columns:
            self.sin_tipo_nonzero_in_train_ = int((df_train["n_skills_sin_tipo"].fillna(0) != 0).sum())
        self._is_fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        self._check_fitted()
        out = pd.DataFrame(index=df.index)
        essential = df["n_skills_essential"].astype("float32")
        competence = df["n_skills_competence"].astype("float32")
        knowledge = df["n_skills_knowledge"].astype("float32")

        out["n_skills_essential"] = essential
        out["n_skills_competence"] = competence
        out["n_skills_knowledge"] = knowledge

        if self.feature_set == "counts_with_sin_tipo":
            sin_tipo = (
                df["n_skills_sin_tipo"].astype("float32")
                if "n_skills_sin_tipo" in df.columns
                else pd.Series(0.0, index=df.index, dtype="float32")
            )
            out["n_skills_sin_tipo"] = sin_tipo

        if self.feature_set == "counts_plus_shares":
            safe_den = np.where(essential > 0, essential, 1.0)
            out["prop_competence_essential"] = np.round(competence / safe_den, 4).astype("float32")
            out["prop_knowledge_essential"] = np.round(knowledge / safe_den, 4).astype("float32")
            out["ratio_competence_knowledge"] = np.round(competence / (knowledge + 1.0), 4).astype("float32")
            out["diff_competence_knowledge"] = (competence - knowledge).astype("float32")

        return out

    def feature_descriptions(self) -> Dict[str, str]:
        desc = {
            "n_skills_essential": (
                "Conteo total (en unidades reales ESCO) de competencias esenciales exigidas por el oficio"
            ),
            "n_skills_competence": (
                "Conteo (en unidades reales ESCO) de competencias prácticas/operativas ('saber hacer') del oficio"
            ),
            "n_skills_knowledge": (
                "Conteo (en unidades reales ESCO) de conocimientos teóricos/disciplinares ('saber') del oficio"
            ),
        }
        if self.feature_set == "counts_with_sin_tipo":
            desc["n_skills_sin_tipo"] = (
                f"Conteo de competencias ESCO sin tipo clasificado "
                f"(registros distintos de 0 en train: {self.sin_tipo_nonzero_in_train_}; varianza cero)"
            )
        if self.feature_set == "counts_plus_shares":
            desc["prop_competence_essential"] = (
                "Proporción de competencias prácticas sobre el total esencial (n_skills_competence / n_skills_essential)"
            )
            desc["prop_knowledge_essential"] = (
                "Proporción de conocimientos teóricos sobre el total esencial (n_skills_knowledge / n_skills_essential)"
            )
            desc["ratio_competence_knowledge"] = (
                "Razón entre competencias prácticas y conocimientos teóricos (n_skills_competence / (n_skills_knowledge + 1))"
            )
            desc["diff_competence_knowledge"] = (
                "Diferencia neta entre competencias prácticas y conocimientos teóricos (n_skills_competence - n_skills_knowledge)"
            )
        return desc
