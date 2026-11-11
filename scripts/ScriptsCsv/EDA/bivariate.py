"""Bivariate exploration and collinearity control.

The module computes Pearson and Spearman matrices, lists the pairs above a
configurable threshold, and prepares a deterministic sample for the hexbin
chart.  The pair table is the guard that prevents reading redundant variables
as independent evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class HighPair:
    """One pair of variables whose absolute correlation is high."""

    variable_a: str
    variable_b: str
    pearson: float
    spearman: float
    strength: str


class CorrelationAnalyzer:
    """Pearson and Spearman diagnostics with an explicit redundancy list."""

    def matrix(self, frame: pd.DataFrame, columns: Sequence[str], method: str = "pearson") -> pd.DataFrame:
        """Correlation matrix over the requested numeric columns."""
        data = frame.loc[:, [c for c in columns if c in frame.columns]].apply(
            pd.to_numeric, errors="coerce"
        )
        return data.corr(method=method)

    def high_pairs(
        self,
        frame: pd.DataFrame,
        columns: Sequence[str],
        threshold: float = 0.7,
    ) -> pd.DataFrame:
        """Pairs with ``|Pearson| >= threshold`` or ``|Spearman| >= threshold``."""
        pearson = self.matrix(frame, columns, "pearson")
        spearman = self.matrix(frame, columns, "spearman")
        rows = []
        names = list(pearson.columns)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                r = pearson.loc[a, b]
                rho = spearman.loc[a, b]
                if pd.isna(r) or pd.isna(rho):
                    continue
                if abs(r) >= threshold or abs(rho) >= threshold:
                    strongest = max(abs(r), abs(rho))
                    rows.append(
                        HighPair(
                            variable_a=a,
                            variable_b=b,
                            pearson=round(float(r), 3),
                            spearman=round(float(rho), 3),
                            strength="muy alta" if strongest >= 0.9 else "alta",
                        )
                    )
        table = pd.DataFrame([row.__dict__ for row in rows])
        if table.empty:
            return table
        table["_order"] = table[["pearson", "spearman"]].abs().max(axis=1)
        return table.sort_values("_order", ascending=False).drop(columns="_order").reset_index(drop=True)

    def scatter_sample(
        self,
        person: pd.DataFrame,
        x: str,
        y: str,
        n: int = 20_000,
        seed: int = 42,
    ) -> pd.DataFrame:
        """Deterministic sample for the hexbin chart."""
        data = person.loc[:, [x, y]].dropna()
        if len(data) <= n:
            return data
        return data.sample(n=n, random_state=seed).reset_index(drop=True)

    def spearman_matrix(self, frame: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
        """Spearman matrix, useful because several variables are skewed."""
        return self.matrix(frame, columns, "spearman")
