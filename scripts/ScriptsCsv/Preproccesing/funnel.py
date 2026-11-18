"""
Row-count and person-count funnel tracker with automatic loss alerts.

Follows the Single Responsibility Principle (SRP): tracks rows and unique
persons (`resume_id`) across pipeline stages and triggers an alert whenever a
stage removes more than the configured threshold percentage.
"""

from dataclasses import dataclass
from typing import List, Optional
import pandas as pd


@dataclass(frozen=True)
class FunnelRecord:
    """Immutable snapshot of rows and persons after a single pipeline step."""

    step: str
    rows_before: int
    rows_after: int
    rows_lost: int
    rows_lost_pct: float
    persons_before: int
    persons_after: int
    persons_lost: int
    persons_lost_pct: float
    cumulative_rows_lost_pct: float
    cumulative_persons_lost_pct: float
    alert_triggered: bool
    note: str


class RowCountFunnel:
    """Tracks row and person counts across pipeline stages and emits loss alerts."""

    def __init__(
        self,
        person_col: str = "resume_id",
        alert_threshold_pct: float = 5.0,
    ) -> None:
        self.person_col = person_col
        self.alert_threshold_pct = float(alert_threshold_pct)
        self._records: List[FunnelRecord] = []
        self._initial_rows: Optional[int] = None
        self._initial_persons: Optional[int] = None
        self._prev_rows: Optional[int] = None
        self._prev_persons: Optional[int] = None

    def _count_persons(self, df: pd.DataFrame) -> int:
        if self.person_col in df.columns:
            return int(df[self.person_col].nunique(dropna=True))
        return 0

    def record_step(
        self,
        step_name: str,
        df: pd.DataFrame,
        note: str = "",
    ) -> FunnelRecord:
        """Record row and person counts after `step_name` and check the alert threshold."""
        rows_now = int(len(df))
        persons_now = self._count_persons(df)

        if self._initial_rows is None:
            self._initial_rows = rows_now
            self._initial_persons = persons_now
            rows_before = rows_now
            persons_before = persons_now
        else:
            rows_before = int(self._prev_rows if self._prev_rows is not None else rows_now)
            persons_before = int(self._prev_persons if self._prev_persons is not None else persons_now)

        rows_lost = rows_before - rows_now
        rows_lost_pct = (rows_lost / rows_before * 100.0) if rows_before > 0 else 0.0

        persons_lost = persons_before - persons_now
        persons_lost_pct = (persons_lost / persons_before * 100.0) if persons_before > 0 else 0.0

        cum_rows_pct = (
            (self._initial_rows - rows_now) / self._initial_rows * 100.0
            if self._initial_rows and self._initial_rows > 0
            else 0.0
        )
        cum_persons_pct = (
            (self._initial_persons - persons_now) / self._initial_persons * 100.0
            if self._initial_persons and self._initial_persons > 0
            else 0.0
        )

        alert = (rows_lost_pct > self.alert_threshold_pct) or (
            persons_lost_pct > self.alert_threshold_pct
        )

        record = FunnelRecord(
            step=step_name,
            rows_before=rows_before,
            rows_after=rows_now,
            rows_lost=rows_lost,
            rows_lost_pct=round(rows_lost_pct, 4),
            persons_before=persons_before,
            persons_after=persons_now,
            persons_lost=persons_lost,
            persons_lost_pct=round(persons_lost_pct, 4),
            cumulative_rows_lost_pct=round(cum_rows_pct, 4),
            cumulative_persons_lost_pct=round(cum_persons_pct, 4),
            alert_triggered=alert,
            note=note,
        )
        self._records.append(record)
        self._prev_rows = rows_now
        self._prev_persons = persons_now

        if alert:
            print(
                f"[ALERTA EMBUDO > {self.alert_threshold_pct:.1f}%] Etapa '{step_name}': "
                f"filas perdidas = {rows_lost} ({rows_lost_pct:.2f}%), "
                f"personas perdidas = {persons_lost} ({persons_lost_pct:.2f}%). {note}"
            )
        return record

    def to_dataframe(self) -> pd.DataFrame:
        """Return the funnel history as a Spanish-labeled DataFrame for notebook reporting."""
        if not self._records:
            return pd.DataFrame(
                columns=[
                    "etapa",
                    "filas_antes",
                    "filas_despues",
                    "filas_perdidas",
                    "pct_filas_perdidas",
                    "personas_antes",
                    "personas_despues",
                    "personas_perdidas",
                    "pct_personas_perdidas",
                    "alerta_umbral_5pct",
                    "nota",
                ]
            )
        return pd.DataFrame(
            [
                {
                    "etapa": r.step,
                    "filas_antes": r.rows_before,
                    "filas_despues": r.rows_after,
                    "filas_perdidas": r.rows_lost,
                    "pct_filas_perdidas": r.rows_lost_pct,
                    "personas_antes": r.persons_before,
                    "personas_despues": r.persons_after,
                    "personas_perdidas": r.persons_lost,
                    "pct_personas_perdidas": r.persons_lost_pct,
                    "alerta_umbral_5pct": "ALERTA (>5%)" if r.alert_triggered else "OK (<=5%)",
                    "nota": r.note,
                }
                for r in self._records
            ]
        )

    def print_summary(self) -> pd.DataFrame:
        """Print and return the complete row-and-person funnel table."""
        df_funnel = self.to_dataframe()
        print("=" * 80)
        print(
            f"EMBUDO DE FILAS Y PERSONAS (Umbral de alerta = {self.alert_threshold_pct:.1f}%)"
        )
        print("=" * 80)
        if not df_funnel.empty:
            print(df_funnel.to_string(index=False))
        else:
            print("Sin etapas registradas en el embudo.")
        print("=" * 80)
        return df_funnel

