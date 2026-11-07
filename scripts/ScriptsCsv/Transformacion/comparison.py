"""Comparacion de matrices A/B y efecto del escalado."""

import numpy as np
import pandas as pd


def normalize_cell(value) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "null", "<na>"}:
        return ""
    try:
        number = float(text)
        if number.is_integer():
            return str(int(number))
        return repr(number)
    except ValueError:
        return text


def normalized_equal(df_a: pd.DataFrame, df_b: pd.DataFrame) -> pd.Series:
    """Mascarra de filas que difieren despues de normalizar vacios y numeros."""
    if list(df_a.columns) != list(df_b.columns) or len(df_a) != len(df_b):
        return pd.Series([True] * max(len(df_a), len(df_b)))
    mismatch = pd.Series(False, index=df_a.index)
    for col in df_a.columns:
        a = df_a[col].map(normalize_cell)
        b = df_b[col].map(normalize_cell)
        mismatch = mismatch | (a != b)
    return mismatch


def material_difference_summary(df_a: pd.DataFrame, df_b: pd.DataFrame,
                              label_a: str, label_b: str) -> pd.DataFrame:
    mismatch = normalized_equal(df_a, df_b)
    rows = [
        {"metric": "rows", label_a: len(df_a), label_b: len(df_b)},
        {"metric": "columns", label_a: df_a.shape[1], label_b: df_b.shape[1]},
        {"metric": "materially_different_rows", label_a: int(mismatch.sum()), label_b: int(mismatch.sum())},
        {"metric": "columns_with_differences", label_a: int((df_a.astype(str) != df_b.astype(str)).any().sum()), label_b: ""},
    ]
    return pd.DataFrame(rows)


def pair_distance_analysis(raw_df: pd.DataFrame, scaled_df: pd.DataFrame,
                          n_rows: int = 400, n_pairs: int = 500,
                          random_state: int = 42) -> pd.DataFrame:
    """Compara distancias euclidianas entre pares antes y despues de escalar."""
    rng = np.random.default_rng(random_state)
    sample_idx = rng.choice(len(raw_df), size=min(n_rows, len(raw_df)), replace=False)
    raw = raw_df.iloc[sample_idx].to_numpy(dtype=float)
    scaled = scaled_df.iloc[sample_idx].to_numpy(dtype=float)
    pairs = []
    while len(pairs) < n_pairs:
        i, j = rng.integers(0, len(sample_idx), size=2)
        if i != j:
            pairs.append((i, j))
    pairs = pairs[:n_pairs]
    raw_dist = np.array([np.linalg.norm(raw[i] - raw[j]) for i, j in pairs])
    scaled_dist = np.array([np.linalg.norm(scaled[i] - scaled[j]) for i, j in pairs])
    return pd.DataFrame(
        {
            "pair_index": range(len(pairs)),
            "distance_raw": raw_dist,
            "distance_scaled": scaled_dist,
        }
    )
