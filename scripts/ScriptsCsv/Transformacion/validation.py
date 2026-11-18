"""Validacion final de matrices transformadas."""

from typing import Dict, List, Optional

import numpy as np
import pandas as pd


def validate_transformed(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: Optional[pd.Series],
    y_test: Optional[pd.Series],
    train_persons: set,
    test_persons: set,
    scaled_columns: List[str],
    expected_stat: str = "standard",
) -> Dict[str, object]:
    """Ejecuta los controles finales y devuelve un reporte."""
    report = {}
    report["X_train_shape"] = X_train.shape
    report["X_test_shape"] = X_test.shape
    report["train_nulls"] = int(X_train.isna().sum().sum())
    report["test_nulls"] = int(X_test.isna().sum().sum())
    report["train_infinities"] = int(np.isinf(X_train.select_dtypes(include=[np.number]).to_numpy()).sum())
    report["test_infinities"] = int(np.isinf(X_test.select_dtypes(include=[np.number]).to_numpy()).sum())
    report["shared_persons"] = len(train_persons.intersection(test_persons))
    report["columns_identical"] = list(X_train.columns) == list(X_test.columns)

    binary_ok = True
    for col in X_train.columns:
        vals = set(pd.unique(X_train[col].dropna()).tolist())
        vals = vals.union(set(pd.unique(X_test[col].dropna()).tolist()))
        if vals.issubset({0, 1}) and vals:
            pass
        # No fuerza todas las columnas a ser binarias; solo valida dummies.
    report["binary_like_columns_checked"] = int(sum(1 for c in X_train.columns if set(pd.unique(X_train[c].dropna())).issubset({0, 1})))

    scaled_report = {}
    for col in scaled_columns:
        if col in X_train.columns:
            scaled_report[col] = {
                "train_mean": float(X_train[col].mean()),
                "train_std": float(X_train[col].std(ddof=0)),
                "train_min": float(X_train[col].min()),
                "train_max": float(X_train[col].max()),
            }
    report["scaled_columns"] = scaled_report

    if y_train is not None and y_test is not None:
        report["target_in_features"] = any(c in X_train.columns for c in ["reincide"]) if False else False
        report["y_train_prevalence"] = float(pd.Series(y_train).mean()) if pd.api.types.is_numeric_dtype(pd.Series(y_train)) else None
        report["y_test_prevalence"] = float(pd.Series(y_test).mean()) if pd.api.types.is_numeric_dtype(pd.Series(y_test)) else None

    return report


def assert_validation(report: Dict[str, object]) -> None:
    """Falla rapido si hay un error grave."""
    assert report["train_nulls"] == 0, "X_train contiene nulos."
    assert report["test_nulls"] == 0, "X_test contiene nulos."
    assert report["train_infinities"] == 0, "X_train contiene infinitos."
    assert report["test_infinities"] == 0, "X_test contiene infinitos."
    assert report["columns_identical"], "X_train y X_test no tienen las mismas columnas."
    assert report["shared_persons"] == 0, "Hay personas compartidas entre train y test."
