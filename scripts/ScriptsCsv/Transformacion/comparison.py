"""Comparison utilities for Version A (with outliers) vs Version B (without outliers) and scaling impact."""

import numpy as np
import pandas as pd


def _column_diff_mask(s_a: pd.Series, s_b: pd.Series) -> pd.Series:
    """Return a boolean Series marking rows where s_a and s_b materially differ."""
    both_na = s_a.isna() & s_b.isna()
    if pd.api.types.is_numeric_dtype(s_a) and pd.api.types.is_numeric_dtype(s_b):
        diff = ~np.isclose(
            s_a.to_numpy(dtype=float, na_value=np.nan),
            s_b.to_numpy(dtype=float, na_value=np.nan),
            rtol=1e-9,
            atol=1e-9,
            equal_nan=True,
        )
        return pd.Series(diff, index=s_a.index) & ~both_na

    num_a = pd.to_numeric(s_a, errors="coerce")
    num_b = pd.to_numeric(s_b, errors="coerce")
    if num_a.notna().any() or num_b.notna().any():
        both_num = num_a.notna() & num_b.notna()
        if both_num.sum() == (s_a.notna() | s_b.notna()).sum():
            diff = ~np.isclose(
                num_a.to_numpy(dtype=float, na_value=np.nan),
                num_b.to_numpy(dtype=float, na_value=np.nan),
                rtol=1e-9,
                atol=1e-9,
                equal_nan=True,
            )
            return pd.Series(diff, index=s_a.index) & ~both_na

    str_a = s_a.fillna("").astype(str).str.strip()
    str_b = s_b.fillna("").astype(str).str.strip()
    return (str_a != str_b) & ~both_na


def normalized_equal(df_a: pd.DataFrame, df_b: pd.DataFrame) -> pd.Series:
    """Boolean mask of rows that differ materially between df_a and df_b."""
    if list(df_a.columns) != list(df_b.columns) or len(df_a) != len(df_b):
        return pd.Series([True] * max(len(df_a), len(df_b)))
    mismatch = pd.Series(False, index=df_a.index)
    for col in df_a.columns:
        mismatch = mismatch | _column_diff_mask(df_a[col], df_b[col])
    return mismatch


def material_difference_summary(
    df_a: pd.DataFrame, df_b: pd.DataFrame, label_a: str, label_b: str
) -> pd.DataFrame:
    """Summarize row and column differences between Version A and Version B."""
    mismatch = pd.Series(False, index=df_a.index)
    cols_diff = 0
    for col in df_a.columns:
        col_mask = _column_diff_mask(df_a[col], df_b[col])
        if col_mask.any():
            cols_diff += 1
            mismatch = mismatch | col_mask

    rows = [
        {"metric": "rows", label_a: len(df_a), label_b: len(df_b)},
        {"metric": "columns", label_a: df_a.shape[1], label_b: df_b.shape[1]},
        {
            "metric": "materially_different_rows",
            label_a: int(mismatch.sum()),
            label_b: int(mismatch.sum()),
        },
        {
            "metric": "columns_with_differences",
            label_a: int(cols_diff),
            label_b: int(cols_diff),
        },
    ]
    return pd.DataFrame(rows)


def pair_distance_analysis(
    raw_df: pd.DataFrame,
    scaled_df: pd.DataFrame,
    n_rows: int = 400,
    n_pairs: int = 500,
    random_state: int = 42,
) -> pd.DataFrame:
    """Compare pairwise Euclidean distances before and after feature scaling."""
    rng = np.random.default_rng(random_state)
    sample_idx = rng.choice(
        len(raw_df), size=min(n_rows, len(raw_df)), replace=False
    )
    raw = raw_df.iloc[sample_idx].to_numpy(dtype=float)
    scaled = scaled_df.iloc[sample_idx].to_numpy(dtype=float)
    pairs = []
    while len(pairs) < n_pairs:
        i, j = rng.integers(0, len(sample_idx), size=2)
        if i != j:
            pairs.append((i, j))
    pairs = pairs[:n_pairs]
    raw_dist = np.array([np.linalg.norm(raw[i] - raw[j]) for i, j in pairs])
    scaled_dist = np.array(
        [np.linalg.norm(scaled[i] - scaled[j]) for i, j in pairs]
    )
    return pd.DataFrame(
        {
            "pair_index": range(len(pairs)),
            "distance_raw": raw_dist,
            "distance_scaled": scaled_dist,
        }
    )
