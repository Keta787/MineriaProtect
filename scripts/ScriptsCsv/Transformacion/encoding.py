"""Nominal and ordinal encoding utilities (no LabelEncoder on nominal features)."""

from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder


def derive_skill_presence(
    df: pd.DataFrame, skill_list_cols: List[str], output_flags: List[str]
) -> pd.DataFrame:
    """Convert raw skill list columns into 0/1 uint8 presence flags."""
    if len(skill_list_cols) != len(output_flags):
        raise ValueError("skill_list_cols and output_flags must have the same length")
    result = df.copy()
    for source, flag in zip(skill_list_cols, output_flags):
        if source not in result.columns:
            raise KeyError(f"Column {source} does not exist")
        result[flag] = (
            result[source]
            .fillna("")
            .astype(str)
            .str.strip()
            .ne("")
            .astype(np.uint8)
        )
    return result


def ordinal_from_mapping(
    df: pd.DataFrame,
    source_col: str,
    mapping: Dict[str, int],
    target_col: str,
    unknown_value: Optional[int] = None,
) -> pd.DataFrame:
    """Map a genuine ordinal hierarchy and validate unrecognized values."""
    result = df.copy()
    if source_col not in result.columns:
        raise KeyError(f"Column {source_col} does not exist")
    mapped = result[source_col].map(mapping)
    unknowns = result[source_col].notna() & mapped.isna()
    if unknowns.any() and unknown_value is None:
        values = sorted(
            result.loc[unknowns, source_col].astype(str).unique().tolist()
        )
        raise ValueError(f"Unrecognized values in {source_col}: {values}")
    if unknown_value is not None:
        mapped = mapped.fillna(unknown_value)
    result[target_col] = mapped
    if result[target_col].isna().any():
        raise ValueError(f"Column {target_col} contains NaN after mapping")
    return result


def fit_onehot(
    train: pd.DataFrame,
    columns: List[str],
    drop_first: bool = True,
    handle_unknown: str = "ignore",
) -> OneHotEncoder:
    """Fit OneHotEncoder on train only using compact uint8 storage."""
    if not columns:
        raise ValueError("At least one column is required for OneHotEncoder")
    encoder = OneHotEncoder(
        drop="first" if drop_first else None,
        handle_unknown=handle_unknown,
        sparse_output=False,
        dtype=np.uint8,
    )
    encoder.fit(train[columns].astype(str))
    return encoder


def transform_onehot(
    encoder: OneHotEncoder, df: pd.DataFrame, columns: List[str]
) -> pd.DataFrame:
    """Transform DataFrame with a fitted OneHotEncoder returning uint8 columns."""
    values = encoder.transform(df[columns].astype(str))
    return pd.DataFrame(
        values,
        columns=encoder.get_feature_names_out(columns),
        index=df.index,
         copy=False,
    )


def reduce_high_cardinality(
    series: pd.Series,
    strategy: str = "all",
    top_n: int = 50,
    min_frequency: float = 0.01,
    prefix_length: int = 4,
) -> pd.Series:
    """High-cardinality reduction strategies for ESCO occupation codes."""
    if strategy == "all":
        return series.astype(str)
    values = series.astype(str)
    if strategy == "top_n":
        keep = set(values.value_counts().head(top_n).index)
        return values.where(values.isin(keep), "other")
    if strategy == "frequency_threshold":
        frequencies = values.value_counts(normalize=True)
        keep = set(frequencies[frequencies >= min_frequency].index)
        return values.where(values.isin(keep), "other")
    if strategy == "prefix":
        return values.str.slice(0, prefix_length)
    raise ValueError(f"Unsupported high-cardinality strategy: {strategy}")
