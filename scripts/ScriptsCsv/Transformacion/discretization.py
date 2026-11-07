"""Discretizacion con KBinsDiscretizer y etiquetas de negocio."""

from dataclasses import dataclass
from typing import Dict, List, Sequence

import numpy as np
import pandas as pd
from sklearn.preprocessing import KBinsDiscretizer


@dataclass
class DiscretizerReport:
    column: str
    edges: List[float]
    counts: Dict[str, int]
    strategy: str
    n_bins: int


def fit_discretizers(df: pd.DataFrame, columns: Sequence[str], n_bins: int = 5,
                     strategy: str = "quantile", encode: str = "ordinal") -> Dict[str, KBinsDiscretizer]:
    """Ajusta un KBinsDiscretizer por columna."""
    discretizers = {}
    for col in columns:
        if col not in df.columns:
            raise KeyError(f"La columna {col} no existe")
        estimator = KBinsDiscretizer(n_bins=n_bins, encode=encode, strategy=strategy)
        estimator.fit(df[[col]].to_numpy(dtype=float))
        discretizers[col] = estimator
    return discretizers


def transform_discretizers(discretizers: Dict[str, KBinsDiscretizer],
                          df: pd.DataFrame, labels: Dict[str, Sequence[str]] = None) -> pd.DataFrame:
    """Devuelve bins numericos y, si se pasan, columnas etiquetadas."""
    labels = labels or {}
    out = pd.DataFrame(index=df.index)
    for col, estimator in discretizers.items():
        values = estimator.transform(df[[col]].to_numpy(dtype=float))
        bin_number = values.ravel().astype(int)
        out[f"{col}_bin"] = bin_number
        if col in labels:
            names = list(labels[col])
            out[f"{col}_bin_label"] = pd.Categorical.from_codes(
                np.where(bin_number < 0, -1, bin_number), categories=range(len(names))
            ).astype(object)
            # Sustituir codigos por etiquetas legibles de forma segura.
            mapping = {i: names[i] for i in range(len(names))}
            out[f"{col}_bin_label"] = pd.Series(bin_number, index=df.index).map(mapping)
    return out


def report_edges(discretizers: Dict[str, KBinsDiscretizer], df: pd.DataFrame,
                 labels: Dict[str, Sequence[str]] = None) -> pd.DataFrame:
    """Reporta bordes, conteos y etiquetas por bin."""
    labels = labels or {}
    rows = []
    for col, estimator in discretizers.items():
        edges = list(estimator.bin_edges_[0])
        transformed = estimator.transform(df[[col]].to_numpy(dtype=float)).ravel().astype(int)
        for bin_id in sorted(set(transformed.tolist())):
            count = int((transformed == bin_id).sum())
            label = labels.get(col, [f"bin_{i}" for i in range(estimator.n_bins)])[bin_id]
            left = edges[bin_id] if bin_id < len(edges) - 1 else edges[-1]
            right = edges[bin_id + 1] if bin_id + 1 < len(edges) else edges[-1]
            rows.append(
                {
                    "column": col,
                    "bin": bin_id,
                    "label": label,
                    "left_edge": float(left),
                    "right_edge": float(right),
                    "count": count,
                }
            )
    return pd.DataFrame(rows)
