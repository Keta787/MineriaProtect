"""Leakage and circularity audit.

The target ``reincide`` is defined as ``veces_ese_oficio > 1``.  That column is
also present in the transformed matrix, so a model trained on ``X`` would see
the answer.  This module quantifies the overlap, checks the person-level
restatement through ``n_returns`` and lists every X column that must be
excluded before phase 4.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

import numpy as np
import pandas as pd

from .config import PERSON_COL, TARGET_DISPLAY


@dataclass(frozen=True)
class LeakageCheck:
    """One audited relation between a variable and the target."""

    variable: str
    check: str
    value: float
    verdict: str
    detail: str


class LeakageAuditor:
    """Audit direct, indirect and column-name leakage."""

    _NAME_PATTERNS = ("reincide", "is_repeated", "target", "veces_ese_oficio", "n_returns")

    def audit_experience(self, train: pd.DataFrame) -> pd.DataFrame:
        """Direct checks at experience level."""
        target = train[TARGET_DISPLAY].astype(int)
        checks: List[LeakageCheck] = []

        clean_derived = train["veces_ese_oficio"].gt(1).astype(int)
        checks.append(
            LeakageCheck(
                variable="veces_ese_oficio",
                check="veces_ese_oficio > 1 == target",
                value=round(float(clean_derived.eq(target).mean() * 100), 4),
                verdict="FUGA DIRECTA",
                detail="La columna original define el target fila a fila.",
            )
        )
        return pd.DataFrame([check.__dict__ for check in checks])

    def audit_x(
        self,
        train: pd.DataFrame,
        x_leak: pd.DataFrame,
        target: pd.Series,
    ) -> pd.DataFrame:
        """Checks on the leakage columns that survived into the X matrix."""
        target = target.astype(int).reset_index(drop=True)
        checks: List[LeakageCheck] = []

        if "veces_ese_oficio_bin" in x_leak.columns:
            derived = x_leak["veces_ese_oficio_bin"].gt(0).astype(int)
            checks.append(
                LeakageCheck(
                    variable="veces_ese_oficio_bin",
                    check="bin > 0 == target",
                    value=round(float(derived.eq(target).mean() * 100), 4),
                    verdict="FUGA DIRECTA",
                    detail="La versión discretizada conserva la definición del target.",
                )
            )
        if "veces_ese_oficio_rob" in x_leak.columns:
            derived = x_leak["veces_ese_oficio_rob"].gt(0).astype(int)
            checks.append(
                LeakageCheck(
                    variable="veces_ese_oficio_rob",
                    check="rob > 0 == target",
                    value=round(float(derived.eq(target).mean() * 100), 4),
                    verdict="FUGA DIRECTA",
                    detail="La versión robusta escalada también conserva el signo.",
                )
            )
        if "veces_ese_oficio_rob" in x_leak.columns:
            correlation = float(
                np.corrcoef(
                    x_leak["veces_ese_oficio_rob"].to_numpy(dtype=float),
                    target.to_numpy(dtype=float),
                )[0, 1]
            )
            checks.append(
                LeakageCheck(
                    variable="veces_ese_oficio_rob",
                    check="correlación con el target",
                    value=round(correlation, 4),
                    verdict="FUGA DIRECTA",
                    detail="Correlación alta esperada por construcción.",
                )
            )
        return pd.DataFrame([check.__dict__ for check in checks])

    def audit_person(self, person: pd.DataFrame) -> pd.DataFrame:
        """Person-level equivalence between ``n_returns`` and any repetition."""
        repeated = person["any_repeated"].astype(int)
        has_return = person["n_returns"].ge(1).astype(int)
        equivalence = float(repeated.eq(has_return).mean() * 100)
        return pd.DataFrame(
            [
                {
                    "variable": "n_returns",
                    "check": "(n_returns >= 1) == any_repeated",
                    "value": round(equivalence, 4),
                    "verdict": "CIRCULARIDAD",
                    "detail": (
                        "A nivel persona, tener al menos un retorno equivale a tener "
                        "al menos un empleo repetido; no es una variable independiente."
                    ),
                }
            ]
        )

    def x_leak_columns(self, x_header: Sequence[str]) -> List[str]:
        """Columns of X whose name reveals target information."""
        return [column for column in x_header if any(p in column for p in self._NAME_PATTERNS)]

    def contamination_table(self, train: pd.DataFrame, max_value: int = 5) -> pd.DataFrame:
        """Target rate by number of times the person had that occupation."""
        data = train.copy()
        data["veces_mostrada"] = data["veces_ese_oficio"].clip(upper=max_value).astype(int)
        table = (
            data.groupby("veces_mostrada", sort=True)[TARGET_DISPLAY]
            .agg(n="size", positivos="sum")
            .reset_index()
        )
        table["tasa_pct"] = (table["positivos"] / table["n"] * 100).round(2)
        return table

    def verdict_summary(self, *tables: pd.DataFrame) -> pd.DataFrame:
        """Concatenate every leakage table into one audit report."""
        frames = [table for table in tables if table is not None and not table.empty]
        if not frames:
            return pd.DataFrame(columns=["variable", "check", "value", "verdict", "detail"])
        return pd.concat(frames, ignore_index=True)
