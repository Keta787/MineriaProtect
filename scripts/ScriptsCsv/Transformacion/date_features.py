"""Derivacion de features temporales sin escalar fechas crudas."""

import re
import pandas as pd


TRIMESTRE = re.compile(r"^Q([1-4])\s+(\d{4})$")


def quarter_to_ordinal(value: str) -> float:
    match = TRIMESTRE.match(str(value).strip())
    if not match:
        return float("nan")
    quarter = int(match.group(1))
    year = int(match.group(2))
    return year * 4 + quarter


def add_date_ordinals(df: pd.DataFrame, start_col: str, end_col: str,
                      censorship_value: str = "Present",
                      censorship_quarter: int = 2026 * 4 + 1) -> pd.DataFrame:
    """Anade start_ord, end_ord y dur_q; 'Present' se trata como censura."""
    result = df.copy()
    start_ord = result[start_col].map(quarter_to_ordinal)
    end_ord = result[end_col].map(quarter_to_ordinal)
    end_ord = end_ord.mask(result[end_col].astype(str).str.strip().eq(censorship_value), censorship_quarter)
    result["start_ord"] = start_ord
    result["end_ord"] = end_ord
    result["dur_q"] = end_ord - start_ord + 1
    return result


def add_start_year(df: pd.DataFrame, source_col: str = "start_date") -> pd.DataFrame:
    result = df.copy()
    ordinals = result[source_col].map(quarter_to_ordinal)
    result["start_year"] = (ordinals // 4).astype("Int64")
    return result


def add_job_order(df: pd.DataFrame, person_col: str, time_col: str = "start_ord") -> pd.DataFrame:
    """Orden de cada empleo dentro de la trayectoria de la persona."""
    result = df.copy()
    result["_job_order_key1"] = result[person_col]
    result["_job_order_key2"] = pd.to_numeric(result[time_col], errors="coerce")
    result = result.sort_values(["_job_order_key1", "_job_order_key2"], kind="mergesort")
    result["job_order"] = result.groupby(person_col).cumcount() + 1
    result = result.sort_index()
    return result.drop(columns=["_job_order_key1", "_job_order_key2"])
