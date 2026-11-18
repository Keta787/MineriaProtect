"""Bitacora de decisiones de transformacion."""

from dataclasses import dataclass, asdict
from typing import List

import pandas as pd


@dataclass
class Decision:
    column: str
    decision: str
    method: str
    justification: str
    phase_task: str


class DecisionLog:
    def __init__(self):
        self.records: List[Decision] = []

    def add(self, column: str, decision: str, method: str, justification: str, phase_task: str):
        self.records.append(Decision(column, decision, method, justification, phase_task))

    def to_frame(self) -> pd.DataFrame:
        if not self.records:
            return pd.DataFrame(columns=["column", "decision", "method", "justification", "phase_task"])
        return pd.DataFrame([asdict(r) for r in self.records])
