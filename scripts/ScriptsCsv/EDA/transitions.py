"""Occupational transitions between consecutive jobs.

A transition exists when a person has at least two classified jobs.  The
module builds the origin -> destination table, counts self-loops (same
occupation) and same-ISCO moves, and prepares the two heatmaps of the report:
fine-grained occupations and aggregated ISCO groups.

The transition table is used descriptively only.  It is never crossed with the
target, because a return to a previous occupation is mechanically related to
the definition of the target.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from .config import PERSON_COL


@dataclass(frozen=True)
class TransitionSummary:
    """Headline numbers of the transition universe."""

    n_transitions: int
    n_persons: int
    self_loop_pct: float
    same_isco_pct: float
    median_gap_q: float
    overlap_pct: float


class TransitionAnalyzer:
    """Build and summarise consecutive occupational moves."""

    def build(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Return one row per consecutive pair of classified jobs."""
        classified = frame.loc[frame["occupation_code"].notna()].copy()
        classified = classified.sort_values(
            [PERSON_COL, "start_ord", "job_order"], kind="mergesort"
        )
        grouped = classified.groupby(PERSON_COL, sort=False)
        classified["source_occ"] = grouped["occupation_code"].shift()
        classified["source_label"] = grouped["occupation_label"].shift()
        classified["source_isco"] = grouped["isco_group"].shift()
        classified["source_isco_label"] = grouped["isco_group_label"].shift()
        classified["source_end_ord"] = grouped["end_ord"].shift()
        classified["is_transition"] = grouped.cumcount() > 0
        classified["_seen_before"] = (
            classified.groupby([PERSON_COL, "occupation_code"]).cumcount() > 0
        )

        transitions = classified.loc[classified["is_transition"]].copy()
        transitions = transitions.rename(
            columns={
                "occupation_code": "dest_occ",
                "occupation_label": "dest_label",
                "isco_group": "dest_isco",
                "isco_group_label": "dest_isco_label",
            }
        )
        transitions["is_self_loop"] = transitions["source_occ"].eq(transitions["dest_occ"])
        transitions["same_isco"] = transitions["source_isco"].eq(transitions["dest_isco"])
        transitions["nonadjacent_return"] = (
            transitions["_seen_before"] & ~transitions["is_self_loop"]
        )
        transitions["gap_q"] = transitions["start_ord"] - transitions["source_end_ord"]
        transitions["overlap"] = transitions["gap_q"] < 1
        return transitions.reset_index(drop=True)

    def summary(self, transitions: pd.DataFrame) -> TransitionSummary:
        """Aggregate the transition table into headline indicators."""
        return TransitionSummary(
            n_transitions=int(len(transitions)),
            n_persons=int(transitions[PERSON_COL].nunique()),
            self_loop_pct=round(float(transitions["is_self_loop"].mean() * 100), 2),
            same_isco_pct=round(float(transitions["same_isco"].mean() * 100), 2),
            median_gap_q=round(float(transitions["gap_q"].median()), 2),
            overlap_pct=round(float(transitions["overlap"].mean() * 100), 2),
        )

    def top_moves(
        self,
        transitions: pd.DataFrame,
        top_n: int = 20,
        exclude_self_loops: bool = True,
    ) -> pd.DataFrame:
        """Most frequent origin -> destination pairs with readable labels."""
        data = transitions.loc[~transitions["is_self_loop"]] if exclude_self_loops else transitions
        moves = (
            data.groupby(["source_label", "dest_label"], sort=False)
            .size()
            .reset_index(name="transiciones")
            .sort_values("transiciones", ascending=False)
            .head(top_n)
            .reset_index(drop=True)
        )
        moves["pct_del_total"] = (moves["transiciones"] / len(transitions) * 100).round(2)
        return moves

    def _top_nodes(self, transitions: pd.DataFrame, top_n: int) -> List[str]:
        outgoing = transitions["source_label"].value_counts()
        incoming = transitions["dest_label"].value_counts()
        totals = outgoing.add(incoming, fill_value=0).sort_values(ascending=False)
        return totals.head(top_n).index.tolist()

    def occupation_matrix(self, transitions: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
        """Square count matrix of the ``top_n`` most active occupations."""
        nodes = self._top_nodes(transitions, top_n)
        subset = transitions.loc[
            transitions["source_label"].isin(nodes) & transitions["dest_label"].isin(nodes)
        ]
        matrix = pd.crosstab(subset["source_label"], subset["dest_label"])
        return matrix.reindex(index=nodes, columns=nodes, fill_value=0)

    def isco_matrix(self, transitions: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
        """Square count matrix of the most active ISCO groups."""
        outgoing = transitions["source_isco_label"].value_counts()
        incoming = transitions["dest_isco_label"].value_counts()
        totals = outgoing.add(incoming, fill_value=0).sort_values(ascending=False)
        nodes = totals.head(top_n).index.tolist()
        subset = transitions.loc[
            transitions["source_isco_label"].isin(nodes)
            & transitions["dest_isco_label"].isin(nodes)
        ]
        matrix = pd.crosstab(subset["source_isco_label"], subset["dest_isco_label"])
        return matrix.reindex(index=nodes, columns=nodes, fill_value=0)

    def transition_rates(self, transitions: pd.DataFrame) -> pd.DataFrame:
        """Self-loop and same-ISCO rates per origin occupation (top 15)."""
        top = transitions["source_label"].value_counts().head(15).index
        data = transitions.loc[transitions["source_label"].isin(top)]
        table = (
            data.groupby("source_label", sort=False)
            .agg(
                transiciones=("is_self_loop", "size"),
                autolazo_pct=("is_self_loop", lambda s: round(float(s.mean() * 100), 2)),
                mismo_isco_pct=("same_isco", lambda s: round(float(s.mean() * 100), 2)),
            )
            .reset_index()
            .sort_values("transiciones", ascending=False)
        )
        return table

    def return_stats(self, transitions: pd.DataFrame) -> pd.DataFrame:
        """Return counts by type of move, without the target."""
        rows = [
            {"tipo": "Autolazo (mismo oficio consecutivo)",
             "transiciones": int(transitions["is_self_loop"].sum())},
            {"tipo": "Retorno no adyacente",
             "transiciones": int(transitions["nonadjacent_return"].sum())},
            {"tipo": "Cambio a otro oficio (sin retorno)",
             "transiciones": int((~transitions["is_self_loop"]
                                  & ~transitions["nonadjacent_return"]).sum())},
        ]
        table = pd.DataFrame(rows)
        table["pct"] = (table["transiciones"] / len(transitions) * 100).round(2)
        return table
