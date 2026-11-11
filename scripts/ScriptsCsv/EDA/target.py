"""Target analysis restricted to the training partition.

Every cross of a variable with the target goes through :class:`SplitGuard`.
The guard records each use and refuses any split other than ``train``.  This is
the executable version of the rule "the test set is not used for exploration".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

import numpy as np
import pandas as pd

from .config import TARGET_DISPLAY


class SplitGuardError(RuntimeError):
    """Raised when an analysis tries to use the test partition."""


class SplitGuard:
    """Allow target crosses only on the training partition."""

    def __init__(self) -> None:
        self._uses: List[Dict[str, object]] = []

    def check(self, split: str, analysis: str) -> None:
        """Register one use and reject anything that is not ``train``."""
        if split != "train":
            raise SplitGuardError(
                f"El análisis '{analysis}' intentó usar el split '{split}'. "
                "Los cruces con el target solo se permiten en train."
            )
        self._uses.append({"analysis": analysis, "split": split})

    @property
    def uses(self) -> List[Dict[str, object]]:
        """Recorded uses, in order."""
        return list(self._uses)

    def summary(self) -> pd.DataFrame:
        """Table with every target cross performed."""
        if not self._uses:
            return pd.DataFrame(columns=["analysis", "split"])
        return pd.DataFrame(self._uses)


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """95 % Wilson interval for a proportion, robust for small groups."""
    if total == 0:
        return (float("nan"), float("nan"))
    p = successes / total
    denominator = 1 + z**2 / total
    centre = (p + z**2 / (2 * total)) / denominator
    margin = z * np.sqrt(p * (1 - p) / total + z**2 / (4 * total**2)) / denominator
    return (max(0.0, centre - margin), min(1.0, centre + margin))


class TargetAnalyzer:
    """Balance and group rates of the target, always on train."""

    def __init__(self, guard: SplitGuard) -> None:
        self._guard = guard

    def balance(
        self,
        parts: Dict[str, tuple[pd.DataFrame, pd.DataFrame]],
        version_labels: Dict[str, str],
    ) -> pd.DataFrame:
        """Positive/negative counts and prevalence in train and test.

        ``parts`` maps each version key (A/B) to its ``(train, test)`` pair.
        Test is read **only** to describe the split; it is never crossed with
        any feature.  The guard is applied to the train rows that feed rates.
        """
        self._guard.check("train", "balance del target")
        rows = []
        for version, (train, test) in parts.items():
            label = version_labels.get(version, version)
            for split_name, frame in (("train", train), ("test", test)):
                series = frame[TARGET_DISPLAY]
                positives = int(series.sum())
                rows.append(
                    {
                        "version": label,
                        "split": split_name,
                        "n": int(len(series)),
                        "positivos": positives,
                        "negativos": int(len(series) - positives),
                        "tasa_pct": round(float(series.mean() * 100), 2),
                    }
                )
        return pd.DataFrame(rows)

    def overall_rate(self, train: pd.DataFrame, analysis: str = "tasa global") -> Dict[str, object]:
        """Overall prevalence with a Wilson interval."""
        self._guard.check("train", analysis)
        series = train[TARGET_DISPLAY]
        positives = int(series.sum())
        low, high = wilson_interval(positives, len(series))
        return {
            "n": int(len(series)),
            "positivos": positives,
            "tasa_pct": round(float(series.mean() * 100), 2),
            "ic95_inf_pct": round(float(low) * 100, 2),
            "ic95_sup_pct": round(float(high) * 100, 2),
        }

    def rate_by(
        self,
        train: pd.DataFrame,
        group_col: str,
        analysis: str,
        min_n: int = 200,
        order: Sequence[str] | None = None,
        top_n: int | None = None,
    ) -> pd.DataFrame:
        """Target rate per category, with n, positives and Wilson interval."""
        self._guard.check("train", analysis)
        data = train.dropna(subset=[group_col]).copy()
        table = (
            data.groupby(group_col, sort=False)[TARGET_DISPLAY]
            .agg(n="size", positivos="sum")
            .reset_index()
        )
        table["tasa_pct"] = (table["positivos"] / table["n"] * 100).round(2)
        intervals = [
            wilson_interval(int(row.positivos), int(row.n))
            for row in table.itertuples()
        ]
        table["ic95_inf_pct"] = [round(low * 100, 2) for low, _ in intervals]
        table["ic95_sup_pct"] = [round(high * 100, 2) for _, high in intervals]
        table["grupo_pequeno"] = table["n"] < min_n
        if order is not None:
            table["_order"] = table[group_col].map({value: i for i, value in enumerate(order)})
            table = table.sort_values("_order", na_position="last").drop(columns="_order")
        elif top_n is not None:
            table = table.sort_values("n", ascending=False).head(top_n)
        else:
            table = table.sort_values("tasa_pct", ascending=False)
        return table.reset_index(drop=True)

    def quantile_bins(
        self,
        train: pd.DataFrame,
        column: str,
        n_bins: int = 4,
    ) -> tuple[list[float], list[str]]:
        """Data-driven bin edges and labels for a numeric variable."""
        self._guard.check("train", f"cortes de {column}")
        series = pd.to_numeric(train[column], errors="coerce").dropna()
        edges = np.unique(series.quantile(np.linspace(0, 1, n_bins + 1)).to_numpy())
        edges = [float(edge) for edge in edges]
        if len(edges) < 2:
            return edges, []
        labels = []
        for index in range(len(edges) - 1):
            labels.append(f"{edges[index]:.0f}–{edges[index + 1]:.0f}")
        return edges, labels

    def rate_by_bins(
        self,
        train: pd.DataFrame,
        column: str,
        edges: Sequence[float],
        labels: Sequence[str],
        analysis: str,
    ) -> pd.DataFrame:
        """Target rate per interval of a numeric variable."""
        self._guard.check("train", analysis)
        data = train.copy()
        data["_bin"] = pd.cut(
            pd.to_numeric(data[column], errors="coerce"),
            bins=list(edges),
            labels=list(labels),
            include_lowest=True,
        )
        table = (
            data.dropna(subset=["_bin"])
            .groupby("_bin", observed=True)[TARGET_DISPLAY]
            .agg(n="size", positivos="sum")
            .reset_index()
        )
        table["tasa_pct"] = (table["positivos"] / table["n"] * 100).round(2)
        intervals = [wilson_interval(int(row.positivos), int(row.n)) for row in table.itertuples()]
        table["ic95_inf_pct"] = [round(low * 100, 2) for low, _ in intervals]
        table["ic95_sup_pct"] = [round(high * 100, 2) for _, high in intervals]
        table = table.rename(columns={"_bin": "tramo"})
        return table.reset_index(drop=True)
