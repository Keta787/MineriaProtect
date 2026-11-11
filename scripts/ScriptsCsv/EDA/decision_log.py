"""Decision log of the EDA iteration.

Each record has the shape requested by the rubric: finding, evidence, figure,
action and the CRISP-DM task it belongs to.  The notebook fills the log with
values produced by executed cells, so no number is typed by hand.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import List

import pandas as pd


@dataclass(frozen=True)
class EDADecision:
    """One finding with its evidence, figure and recommended action."""

    hallazgo: str
    evidencia: str
    figura: str
    accion: str
    tarea_crispdm: str


class DecisionLog:
    """Append-only log of findings and decisions."""

    def __init__(self) -> None:
        self._records: List[EDADecision] = []

    def add(
        self,
        hallazgo: str,
        evidencia: str,
        figura: str,
        accion: str,
        tarea_crispdm: str = "Data Understanding",
    ) -> None:
        """Append one decision."""
        self._records.append(
            EDADecision(
                hallazgo=hallazgo,
                evidencia=evidencia,
                figura=figura,
                accion=accion,
                tarea_crispdm=tarea_crispdm,
            )
        )

    def to_frame(self) -> pd.DataFrame:
        """Return the log as a DataFrame, in insertion order."""
        if not self._records:
            return pd.DataFrame(
                columns=["hallazgo", "evidencia", "figura", "accion", "tarea_crispdm"]
            )
        return pd.DataFrame([asdict(record) for record in self._records])

    def __len__(self) -> int:
        return len(self._records)
