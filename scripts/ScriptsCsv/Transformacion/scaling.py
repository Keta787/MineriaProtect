"""Escalado por columna con ajuste solo en train."""

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler


SUFFIX = {"robust": "rob", "standard": "std", "minmax": "mm"}


@dataclass
class FittedScaling:
    plan: Dict[str, str]
    scalers: Dict[str, object]
    columns: List[str]


def make_scaler(name: str):
    name = name.lower()
    if name in {"robust", "rob"}:
        return RobustScaler()
    if name in {"standard", "std"}:
        return StandardScaler()
    if name in {"minmax", "mm"}:
        return MinMaxScaler()
    raise ValueError(f"Escalador no soportado: {name}")


def _canonical(name: str) -> str:
    name = name.lower()
    if name in {"robust", "rob"}:
        return "robust"
    if name in {"standard", "std"}:
        return "standard"
    if name in {"minmax", "mm"}:
        return "minmax"
    return name


def fit_scaling(df: pd.DataFrame, plan: Dict[str, str]) -> FittedScaling:
    """Ajusta un escalador por columna sobre el train."""
    scalers = {}
    for col, scaler_name in plan.items():
        if col not in df.columns:
            raise KeyError(f"La columna {col} no existe en el DataFrame")
        scaler = make_scaler(scaler_name)
        values = df[[col]].to_numpy(dtype=float)
        scaler.fit(values)
        scalers[col] = scaler
    return FittedScaling(plan={k: _canonical(v) for k, v in plan.items()}, scalers=scalers, columns=list(plan.keys()))


def transform_scaling(fitted: FittedScaling, df: pd.DataFrame) -> pd.DataFrame:
    """Transforma con los escaladores previamente ajustados."""
    out = pd.DataFrame(index=df.index)
    for col in fitted.columns:
        scaler = fitted.scalers[col]
        name = fitted.plan[col]
        suffix = SUFFIX[name]
        out[f"{col}_{suffix}"] = scaler.transform(df[[col]].to_numpy(dtype=float)).ravel()
    return out


def fit_transform_full(df: pd.DataFrame, plan: Dict[str, str]) -> Tuple[FittedScaling, pd.DataFrame]:
    """Ajusta y transforma el mismo DataFrame (uso diagnostico o matriz de trabajo)."""
    fitted = fit_scaling(df, plan)
    transformed = transform_scaling(fitted, df)
    return fitted, transformed


def scaled_column_name(column: str, scaler_name: str) -> str:
    return f"{column}_{SUFFIX[_canonical(scaler_name)]}"
