"""Column profiling and inherited data-quality audit for the EDA.

Two responsibilities live here on purpose: describing every column (types,
nulls, cardinality, shape) and summarising the quality that notebooks 2.0 and
3.0 left behind.  Both answer the same CRISP-DM task: *describe* and *verify
data quality* before exploring.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Sequence

import numpy as np
import pandas as pd

from .config import (
    COLUMN_RELEVANCE,
    PERSON_COL,
    TARGET_RELATED,
    TEXT_COLUMNS,
)
from .loader import TextColumnStats

_IDENTIFIER = {"resume_id", "matched_code"}
_DATE = {"start_date", "end_date"}
_ORDINAL = {"university_level", "isco_level"}
_BINARY = {"saber_skills", "es_unknown_ocupacion", "es_rescatado", "es_vigente"}
_COUNT = {
    "n_skills_essential",
    "n_skills_competence",
    "n_skills_knowledge",
    "n_skills_sin_tipo",
    "veces_ese_oficio",
    "start_year",
    "job_order",
}
_CONTINUOUS = {"dur_q", "start_ord", "end_ord"}


@dataclass(frozen=True)
class ColumnProfile:
    """One row of the column profile table."""

    column: str
    dtype: str
    semantic_type: str
    nulls: int
    null_pct: float
    n_unique: int
    zero_pct: float
    skew: float
    kurtosis: float
    minimum: float
    maximum: float
    median: float
    target_related: str
    relevant: bool
    reason: str


class ColumnProfiler:
    """Describe every column without assuming its meaning."""

    def semantic_type(self, column: str, series: pd.Series) -> str:
        """Classify a column into an interpretable family."""
        if column in TEXT_COLUMNS:
            return "text"
        if column in _IDENTIFIER:
            return "identifier"
        if column in _DATE:
            return "date"
        if column in _ORDINAL:
            return "ordinal"
        if column in _BINARY:
            return "binary"
        if column in _COUNT:
            return "count"
        if column in _CONTINUOUS:
            return "continuous"
        if pd.api.types.is_bool_dtype(series):
            return "binary"
        if pd.api.types.is_numeric_dtype(series):
            return "continuous"
        if series.nunique(dropna=True) <= 2:
            return "binary"
        return "nominal"

    def profile(
        self,
        frame: pd.DataFrame,
        text_stats: Sequence[TextColumnStats] | None = None,
    ) -> pd.DataFrame:
        """Build the full column profile for one version."""
        rows: List[ColumnProfile] = []
        for column in frame.columns:
            series = frame[column]
            semantic = self.semantic_type(column, series)
            nulls = int(series.isna().sum())
            numeric = pd.api.types.is_numeric_dtype(series) and semantic not in {"identifier"}
            relevant, reason = COLUMN_RELEVANCE.get(column, (False, ""))
            rows.append(
                ColumnProfile(
                    column=column,
                    dtype=str(series.dtype),
                    semantic_type=semantic,
                    nulls=nulls,
                    null_pct=round(nulls / len(frame) * 100, 2) if len(frame) else 0.0,
                    n_unique=int(series.nunique(dropna=True)),
                    zero_pct=round(float((series == 0).mean() * 100), 2) if numeric else float("nan"),
                    skew=round(float(series.skew()), 3) if numeric else float("nan"),
                    kurtosis=round(float(series.kurtosis()), 3) if numeric else float("nan"),
                    minimum=float(series.min()) if numeric and series.notna().any() else float("nan"),
                    maximum=float(series.max()) if numeric and series.notna().any() else float("nan"),
                    median=float(series.median()) if numeric and series.notna().any() else float("nan"),
                    target_related=TARGET_RELATED.get(column, ""),
                    relevant=relevant,
                    reason=reason,
                )
            )
        for stat in (text_stats if text_stats is not None else ()):
            relevant, reason = COLUMN_RELEVANCE.get(stat.column, (False, ""))
            rows.append(
                ColumnProfile(
                    column=stat.column,
                    dtype="string",
                    semantic_type="text",
                    nulls=stat.nulls,
                    null_pct=stat.null_pct,
                    n_unique=stat.n_unique,
                    zero_pct=float("nan"),
                    skew=float("nan"),
                    kurtosis=float("nan"),
                    minimum=float("nan"),
                    maximum=float("nan"),
                    median=float("nan"),
                    target_related=TARGET_RELATED.get(stat.column, ""),
                    relevant=relevant,
                    reason=reason,
                )
            )
        return pd.DataFrame([row.__dict__ for row in rows])

    def compare_versions(self, profile_a: pd.DataFrame, profile_b: pd.DataFrame) -> pd.DataFrame:
        """Columns whose profile changed between version A and B."""
        columns = ["column", "null_pct", "n_unique", "skew", "kurtosis", "minimum", "maximum", "median"]
        merged = profile_a[columns].merge(
            profile_b[columns], on="column", suffixes=("_a", "_b"), how="inner"
        )
        changed = (
            (merged["null_pct_a"] != merged["null_pct_b"])
            | (merged["n_unique_a"] != merged["n_unique_b"])
            | (~np.isclose(merged["skew_a"].astype(float), merged["skew_b"].astype(float), equal_nan=True))
            | (~np.isclose(merged["kurtosis_a"].astype(float), merged["kurtosis_b"].astype(float), equal_nan=True))
            | (~np.isclose(merged["minimum_a"].astype(float), merged["minimum_b"].astype(float), equal_nan=True))
            | (~np.isclose(merged["maximum_a"].astype(float), merged["maximum_b"].astype(float), equal_nan=True))
            | (~np.isclose(merged["median_a"].astype(float), merged["median_b"].astype(float), equal_nan=True))
        )
        return merged.loc[changed].reset_index(drop=True)


class DataQualityAuditor:
    """Summarise the quality inherited from notebooks 2.0 and 3.0."""

    def summary(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Return a long table with the quality checks of one clean version."""
        person_period = frame.duplicated(subset=[PERSON_COL, "start_date", "end_date"]).sum()
        present = frame["end_date"].astype(str).str.strip().eq("Present")
        metrics: List[Dict[str, object]] = [
            {
                "metric": "Filas (experiencias)",
                "value": int(len(frame)),
                "comment": "El preprocesamiento no eliminó filas.",
            },
            {
                "metric": "Columnas",
                "value": int(frame.shape[1]),
                "comment": "Incluye las columnas derivadas de fecha.",
            },
            {
                "metric": "Personas (resume_id)",
                "value": int(frame[PERSON_COL].nunique()),
                "comment": "Clave de agrupación, no feature.",
            },
            {
                "metric": "Nulos totales",
                "value": int(frame.isna().sum().sum()),
                "comment": "La validación de 2.0 falló en este control.",
            },
            {
                "metric": "Filas con oficio sin clasificar",
                "value": int(frame["occupation_code"].isna().sum()),
                "comment": "Quedan fuera del universo de modelado.",
            },
            {
                "metric": "% oficio sin clasificar",
                "value": round(frame["occupation_code"].isna().mean() * 100, 2),
                "comment": "Nulo estructural, no aleatorio.",
            },
            {
                "metric": "Duplicados exactos",
                "value": int(frame.duplicated().sum()),
                "comment": "2.0 los eliminó; el archivo actual no tiene.",
            },
            {
                "metric": "Filas repetidas por persona y periodo",
                "value": int(person_period),
                "comment": "Mismo resume_id + start_date + end_date; posible pluriempleo.",
            },
            {
                "metric": "% repetidas por persona y periodo",
                "value": round(person_period / len(frame) * 100, 2),
                "comment": "Puede inflar transiciones y retornos.",
            },
            {
                "metric": "Empleos vigentes ('Present')",
                "value": int(present.sum()),
                "comment": "Censura a la derecha.",
            },
            {
                "metric": "% empleos vigentes",
                "value": round(present.mean() * 100, 2),
                "comment": "Se tratan como fin en 2026-T1.",
            },
            {
                "metric": "Duración mínima (trimestres)",
                "value": float(frame["dur_q"].min()),
                "comment": "No existe duración de 1 trimestre.",
            },
            {
                "metric": "Duración máxima (trimestres)",
                "value": float(frame["dur_q"].max()),
                "comment": "Cola larga real; no se winsoriza en B.",
            },
            {
                "metric": "Personas en el universo modelable",
                "value": int(frame.loc[frame["n_skills_essential"].notna(), PERSON_COL].nunique()),
                "comment": "Personas con al menos un oficio clasificado.",
            },
        ]
        return pd.DataFrame(metrics)

    def winsorization_effect(
        self, frame_a: pd.DataFrame, frame_b: pd.DataFrame, columns: Iterable[str]
    ) -> pd.DataFrame:
        """Rows changed by the IQR winsorization of version B."""
        rows = []
        for column in columns:
            changed = int((frame_a[column].fillna(-1) != frame_b[column].fillna(-1)).sum())
            rows.append(
                {
                    "column": column,
                    "rows_changed": changed,
                    "pct_changed": round(changed / len(frame_a) * 100, 2),
                    "max_a": float(frame_a[column].max()),
                    "max_b": float(frame_b[column].max()),
                    "median_a": float(frame_a[column].median()),
                    "median_b": float(frame_b[column].median()),
                }
            )
        return pd.DataFrame(rows)
