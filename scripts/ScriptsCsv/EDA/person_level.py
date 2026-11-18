"""Person-level aggregation of the JobPath trajectories.

The clean table has one row per experience.  This module collapses it to one
row per ``resume_id`` and derives the trajectory measures used by the charter:
how many jobs a person had, how many different occupations, how much of the
career is a loop, and how many times the person returns to a previous
occupation.

``resume_id`` is used only as an aggregation key; no row of the output can be
traced back to an identified person.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from .config import PERSON_COL


@dataclass(frozen=True)
class SegmentThresholds:
    """Quantile thresholds used by the derived trajectory segment."""

    self_loop_q75: float
    exploration_q75: float
    nonadjacent_q75: float
    n_persons: int


class PersonLevelAggregator:
    """Build one row per person with volume, duration and loop measures."""

    def _first_non_null(self, series: pd.Series):
        valid = series.dropna()
        return valid.iloc[0] if not valid.empty else np.nan

    def aggregate(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Return one row per person.

        ``n_jobs``, ``span_q`` and ``dur_total`` use every experience.  The
        occupation measures use only experiences with a classified occupation,
        because a transition needs an origin and a destination.
        """
        base = frame.groupby(PERSON_COL, sort=True).agg(
            n_jobs=(PERSON_COL, "size"),
            min_start=("start_ord", "min"),
            max_end=("end_ord", "max"),
            dur_total=("dur_q", "sum"),
            dur_mean=("dur_q", "mean"),
            university_level=("university_level", self._first_non_null),
        )
        base["span_q"] = (base["max_end"] - base["min_start"] + 1).clip(lower=1)
        base["overlap_ratio"] = base["dur_total"] / base["span_q"]
        base = base.drop(columns=["min_start", "max_end"])

        classified = frame.loc[frame["occupation_code"].notna()].copy()
        classified = classified.sort_values(
            [PERSON_COL, "start_ord", "job_order"], kind="mergesort"
        )
        classified["_prev_occ"] = classified.groupby(PERSON_COL)["occupation_code"].shift()
        classified["_seen_before"] = (
            classified.groupby([PERSON_COL, "occupation_code"]).cumcount() > 0
        )
        classified["_is_transition"] = classified.groupby(PERSON_COL).cumcount() > 0
        classified["_self_loop"] = (
            classified["_is_transition"]
            & classified["occupation_code"].eq(classified["_prev_occ"])
        )
        classified["_nonadjacent_return"] = (
            classified["_seen_before"]
            & classified["occupation_code"].ne(classified["_prev_occ"])
        )

        occ = classified.groupby(PERSON_COL, sort=True).agg(
            n_classified=(PERSON_COL, "size"),
            n_occ=("occupation_code", "nunique"),
            n_returns=("_seen_before", "sum"),
            n_nonadjacent_returns=("_nonadjacent_return", "sum"),
            n_self_loops=("_self_loop", "sum"),
            n_transitions=("_is_transition", "sum"),
            max_veces=("veces_ese_oficio", "max"),
        )
        occ["self_loop_share"] = np.where(
            occ["n_transitions"] > 0, occ["n_self_loops"] / occ["n_transitions"], 0.0
        )
        occ["nonadjacent_return_share"] = np.where(
            occ["n_transitions"] > 0,
            occ["n_nonadjacent_returns"] / occ["n_transitions"],
            0.0,
        )
        occ["any_repeated"] = occ["max_veces"].gt(1)

        isco_mode = (
            classified.dropna(subset=["isco_group_label"])
            .groupby([PERSON_COL, "isco_group_label"], sort=False)
            .size()
            .reset_index(name="n")
            .sort_values([PERSON_COL, "n"], ascending=[True, False])
            .drop_duplicates(PERSON_COL)
            .set_index(PERSON_COL)["isco_group_label"]
        )

        person = base.join(occ, how="left").join(isco_mode.rename("isco_main"), how="left")
        person["n_occ"] = person["n_occ"].fillna(0).astype(int)
        person["n_classified"] = person["n_classified"].fillna(0).astype(int)
        for column in ("n_returns", "n_nonadjacent_returns", "n_self_loops", "n_transitions"):
            person[column] = person[column].fillna(0).astype(int)
        person["self_loop_share"] = person["self_loop_share"].fillna(0.0)
        person["nonadjacent_return_share"] = person["nonadjacent_return_share"].fillna(0.0)
        person["any_repeated"] = person["any_repeated"].fillna(False).astype(bool)
        person["exploration_ratio"] = person["n_occ"] / person["n_jobs"]
        person["has_classified_job"] = person["n_classified"] > 0
        return person.reset_index()

    def summary(self, person: pd.DataFrame) -> pd.DataFrame:
        """Compact description of the person-level variables."""
        columns = (
            "n_jobs",
            "n_occ",
            "span_q",
            "dur_total",
            "dur_mean",
            "n_returns",
            "overlap_ratio",
            "self_loop_share",
            "exploration_ratio",
        )
        rows = []
        for column in columns:
            series = pd.to_numeric(person[column], errors="coerce").dropna()
            q1, q3 = series.quantile([0.25, 0.75])
            rows.append(
                {
                    "variable": column,
                    "media": round(float(series.mean()), 3),
                    "mediana": round(float(series.median()), 3),
                    "q1": round(float(q1), 3),
                    "q3": round(float(q3), 3),
                    "max": round(float(series.max()), 3),
                }
            )
        return pd.DataFrame(rows)

    def job_distribution(self, person: pd.DataFrame) -> pd.DataFrame:
        """How many people have each number of jobs, plus cumulative share."""
        counts = person["n_jobs"].value_counts().sort_index()
        table = counts.rename_axis("n_jobs").reset_index(name="personas")
        table["pct"] = (table["personas"] / len(person) * 100).round(2)
        table["pct_acumulado"] = table["pct"].cumsum().round(2)
        return table

    def returns_distribution(self, person: pd.DataFrame) -> pd.DataFrame:
        """Group the number of returns into 0, 1, 2 or more."""
        bucket = pd.cut(
            person["n_returns"],
            bins=[-1, 0, 1, np.inf],
            labels=["0 retornos", "1 retorno", "2 o más retornos"],
        )
        table = bucket.value_counts().sort_index().rename_axis("retornos").reset_index(name="personas")
        table["pct"] = (table["personas"] / len(person) * 100).round(2)
        return table

    def segment_thresholds(self, person: pd.DataFrame) -> SegmentThresholds:
        """Q75 thresholds of the three loop measures, computed from the data."""
        eligible = person.loc[person["n_jobs"] >= 2]
        return SegmentThresholds(
            self_loop_q75=round(float(eligible["self_loop_share"].quantile(0.75)), 4),
            exploration_q75=round(float(eligible["exploration_ratio"].quantile(0.75)), 4),
            nonadjacent_q75=round(float(eligible["nonadjacent_return_share"].quantile(0.75)), 4),
            n_persons=int(len(eligible)),
        )

    def assign_segment(self, person: pd.DataFrame, thresholds: SegmentThresholds) -> pd.DataFrame:
        """Assign one of four trajectory types using the Q75 thresholds.

        The labels describe the shape of the trajectory.  They are **not**
        compared with the target: ``n_returns`` is a person-level restatement
        of the target, so such a comparison would be circular.
        """
        result = person.copy()
        conditions = [
            result["n_jobs"] < 2,
            result["self_loop_share"] >= thresholds.self_loop_q75,
            result["exploration_ratio"] >= thresholds.exploration_q75,
        ]
        result["segmento"] = np.select(
            conditions,
            ["sin transición", "permanente", "exploradora"],
            default="mixta",
        )
        return result

    def segment_summary(self, person: pd.DataFrame) -> pd.DataFrame:
        """Counts and profile of the derived segment, without the target."""
        table = (
            person.groupby("segmento", sort=False)
            .agg(
                personas=("resume_id", "size"),
                empleos_medios=("n_jobs", "mean"),
                oficios_medios=("n_occ", "mean"),
                retornos_medios=("n_returns", "mean"),
                autolazo_medio=("self_loop_share", "mean"),
            )
            .reset_index()
        )
        table["pct"] = (table["personas"] / len(person) * 100).round(2)
        for column in ("empleos_medios", "oficios_medios", "retornos_medios", "autolazo_medio"):
            table[column] = table[column].round(3)
        order = {"permanente": 0, "exploradora": 1, "mixta": 2, "sin transición": 3}
        return table.sort_values("segmento", key=lambda s: s.map(order)).reset_index(drop=True)
