"""Temporal feature derivation without scaling raw quarter strings."""

import re
import pandas as pd


QUARTER_PATTERN = re.compile(r"^Q([1-4])\s+(\d{4})$")


def quarter_to_ordinal(value: str) -> float:
    """Convert a 'Q<1-4> <YYYY>' string into a linear quarter ordinal (year * 4 + quarter)."""
    match = QUARTER_PATTERN.match(str(value).strip())
    if not match:
        return float("nan")
    quarter = int(match.group(1))
    year = int(match.group(2))
    return float(year * 4 + quarter)


def _map_quarter_series(series: pd.Series) -> pd.Series:
    """Fast unique-value mapping from quarter string Series to ordinal float Series."""
    uniques = series.dropna().unique()
    lookup = {val: quarter_to_ordinal(val) for val in uniques}
    return series.map(lookup).astype(float)


def add_date_ordinals(
    df: pd.DataFrame,
    start_col: str,
    end_col: str,
    censorship_value: str = "Present",
    censorship_quarter: int = 2026 * 4 + 1,
) -> pd.DataFrame:
    """Add `start_ord`, `end_ord`, and `dur_q`; 'Present' is right-censored at 2026-Q1."""
    result = df.copy()
    start_ord = _map_quarter_series(result[start_col])
    end_ord = _map_quarter_series(result[end_col])
    is_present = (
        result[end_col].astype(str).str.strip().eq(censorship_value)
    )
    end_ord = end_ord.mask(is_present, float(censorship_quarter))
    result["start_ord"] = start_ord
    result["end_ord"] = end_ord
    result["dur_q"] = end_ord - start_ord + 1.0
    return result


def add_start_year(
    df: pd.DataFrame, source_col: str = "start_date"
) -> pd.DataFrame:
    """Add integer `start_year` derived from `start_ord` or `source_col`."""
    result = df.copy()
    if "start_ord" in result.columns:
        ordinals = result["start_ord"]
    else:
        ordinals = _map_quarter_series(result[source_col])
    result["start_year"] = ((ordinals - 1) // 4).astype("Int64")
    return result


def add_job_order(
    df: pd.DataFrame, person_col: str, time_col: str = "start_ord"
) -> pd.DataFrame:
    """Compute chronological 1-based `job_order` within each person's trajectory."""
    result = df.copy()
    result["_job_order_key1"] = result[person_col]
    result["_job_order_key2"] = pd.to_numeric(result[time_col], errors="coerce")
    result = result.sort_values(
        ["_job_order_key1", "_job_order_key2"], kind="mergesort"
    )
    result["job_order"] = result.groupby(person_col).cumcount() + 1
    result = result.sort_index()
    return result.drop(columns=["_job_order_key1", "_job_order_key2"])
