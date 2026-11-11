"""Descriptive statistics and IQR diagnostics at experience level.

The module answers two CRISP-DM *data understanding* questions: how each
numeric variable is distributed, and how much of it is extreme.  It also
implements the hypothetical ``dur_q`` winsorization diagnostic requested for
this iteration; the diagnostic never writes a new dataset.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from .config import COLLINEAR_FAMILIES


@dataclass(frozen=True)
class WhatIfResult:
    """Outcome of clipping one column with IQR bounds, in memory only."""

    column: str
    lower: float
    upper: float
    rows_clipped: int
    pct_clipped: float
    median_before: float
    median_after: float
    mean_before: float
    mean_after: float
    max_before: float
    max_after: float


class ExperienceDescriber:
    """Summarise numeric and categorical variables of the clean experience table."""

    def numeric_summary(self, frame: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
        """Mean, median, mode, dispersion and shape for each numeric column."""
        rows = []
        for column in columns:
            series = pd.to_numeric(frame[column], errors="coerce").dropna()
            if series.empty:
                continue
            q1, q3 = series.quantile([0.25, 0.75])
            mode = series.mode()
            rows.append(
                {
                    "variable": column,
                    "n": int(series.size),
                    "media": round(float(series.mean()), 3),
                    "mediana": round(float(series.median()), 3),
                    "moda": round(float(mode.iloc[0]), 3) if not mode.empty else float("nan"),
                    "desv_est": round(float(series.std()), 3),
                    "min": round(float(series.min()), 3),
                    "q1": round(float(q1), 3),
                    "q3": round(float(q3), 3),
                    "iqr": round(float(q3 - q1), 3),
                    "max": round(float(series.max()), 3),
                    "asimetria": round(float(series.skew()), 3),
                    "curtosis": round(float(series.kurtosis()), 3),
                }
            )
        return pd.DataFrame(rows)

    def iqr_outliers(
        self,
        frame: pd.DataFrame,
        columns: Sequence[str],
        factor: float = 1.5,
    ) -> pd.DataFrame:
        """Count rows outside ``[Q1 - factor*IQR, Q3 + factor*IQR]``."""
        rows = []
        for column in columns:
            series = pd.to_numeric(frame[column], errors="coerce")
            valid = series.dropna()
            if valid.empty:
                continue
            q1, q3 = valid.quantile([0.25, 0.75])
            iqr = q3 - q1
            lower, upper = q1 - factor * iqr, q3 + factor * iqr
            outside = ((series < lower) | (series > upper)) & series.notna()
            rows.append(
                {
                    "variable": column,
                    "limite_inferior": round(float(lower), 3),
                    "limite_superior": round(float(upper), 3),
                    "filas_atipicas": int(outside.sum()),
                    "pct_atipicas": round(float(outside.mean() * 100), 2),
                    "max_observado": round(float(valid.max()), 3),
                }
            )
        return pd.DataFrame(rows)

    def compare_versions(
        self,
        frame_a: pd.DataFrame,
        frame_b: pd.DataFrame,
        columns: Sequence[str],
    ) -> pd.DataFrame:
        """Median, maximum and dispersion of A against the winsorized B."""
        rows = []
        for column in columns:
            a = pd.to_numeric(frame_a[column], errors="coerce")
            b = pd.to_numeric(frame_b[column], errors="coerce")
            rows.append(
                {
                    "variable": column,
                    "mediana_a": round(float(a.median()), 3),
                    "mediana_b": round(float(b.median()), 3),
                    "media_a": round(float(a.mean()), 3),
                    "media_b": round(float(b.mean()), 3),
                    "max_a": round(float(a.max()), 3),
                    "max_b": round(float(b.max()), 3),
                    "desv_a": round(float(a.std()), 3),
                    "desv_b": round(float(b.std()), 3),
                }
            )
        return pd.DataFrame(rows)

    def dur_q_what_if(
        self,
        frame: pd.DataFrame,
        column: str = "dur_q",
        factor: float = 1.5,
    ) -> WhatIfResult:
        """Clip ``dur_q`` with IQR bounds in memory and report the effect.

        Version B does **not** winsorize duration, so this is a diagnostic of
        what would happen if it did.  Nothing is persisted.
        """
        series = pd.to_numeric(frame[column], errors="coerce")
        valid = series.dropna()
        q1, q3 = valid.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower, upper = q1 - factor * iqr, q3 + factor * iqr
        clipped = series.clip(lower=lower, upper=upper)
        rows_clipped = int((series < lower).sum() + (series > upper).sum())
        return WhatIfResult(
            column=column,
            lower=round(float(lower), 3),
            upper=round(float(upper), 3),
            rows_clipped=rows_clipped,
            pct_clipped=round(rows_clipped / len(series) * 100, 2),
            median_before=round(float(series.median()), 3),
            median_after=round(float(clipped.median()), 3),
            mean_before=round(float(series.mean()), 3),
            mean_after=round(float(clipped.mean()), 3),
            max_before=round(float(series.max()), 3),
            max_after=round(float(clipped.max()), 3),
        )

    def top_categories(
        self,
        frame: pd.DataFrame,
        column: str,
        top_n: int = 15,
        other_label: str = "Otras",
    ) -> pd.DataFrame:
        """Frequency table with an explicit ``Otras`` bucket."""
        counts = frame[column].fillna("Sin dato").value_counts()
        head = counts.head(top_n)
        tail = counts.iloc[top_n:].sum()
        table = head.rename_axis("categoria").reset_index(name="frecuencia")
        table["pct"] = (table["frecuencia"] / len(frame) * 100).round(2)
        if tail:
            table = pd.concat(
                [
                    table,
                    pd.DataFrame(
                        [{"categoria": other_label, "frecuencia": int(tail),
                          "pct": round(tail / len(frame) * 100, 2)}]
                    ),
                ],
                ignore_index=True,
            )
        return table

    def duration_spikes(self, frame: pd.DataFrame, column: str = "dur_q") -> pd.DataFrame:
        """Most frequent duration values, to expose rounding in the source."""
        counts = frame[column].value_counts().sort_index()
        table = counts.rename_axis("trimestres").reset_index(name="frecuencia")
        table["pct"] = (table["frecuencia"] / len(frame) * 100).round(2)
        return table.sort_values("frecuencia", ascending=False).head(10)

    def collinearity_families(self) -> pd.DataFrame:
        """Declared redundant families, for the profile table."""
        rows = []
        for family, members in COLLINEAR_FAMILIES.items():
            rows.append({"familia": family, "variables": ", ".join(members)})
        return pd.DataFrame(rows)
