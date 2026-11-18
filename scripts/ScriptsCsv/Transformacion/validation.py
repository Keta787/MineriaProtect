"""Final validation of transformed train/test feature matrices."""

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
    """Run final integrity checks on X_train, X_test, y_train, and y_test."""
    report: Dict[str, object] = {}
    report["X_train_shape"] = X_train.shape
    report["X_test_shape"] = X_test.shape
    report["train_nulls"] = int(X_train.isna().sum().sum())
    report["test_nulls"] = int(X_test.isna().sum().sum())

    float_cols_tr = X_train.select_dtypes(include=["floating"]).columns
    float_cols_te = X_test.select_dtypes(include=["floating"]).columns
    report["train_infinities"] = int(
        sum(int(np.isinf(X_train[c].to_numpy()).sum()) for c in float_cols_tr)
    )
    report["test_infinities"] = int(
        sum(int(np.isinf(X_test[c].to_numpy()).sum()) for c in float_cols_te)
    )
    report["shared_persons"] = len(train_persons.intersection(test_persons))
    report["columns_identical"] = list(X_train.columns) == list(X_test.columns)

    binary_count = 0
    for col in X_train.columns:
        s = X_train[col]
        if s.dtype == np.uint8 or s.dtype == np.int8 or s.dtype == bool:
            cmin, cmax = int(s.min()), int(s.max())
            if cmin >= 0 and cmax <= 1:
                binary_count += 1
        else:
            vals = set(pd.unique(s.dropna()).tolist())
            if vals and vals.issubset({0, 1, 0.0, 1.0}):
                binary_count += 1
    report["binary_like_columns_checked"] = int(binary_count)

    scaled_report = {}
    for col in scaled_columns:
        target_col = col
        if target_col not in X_train.columns:
            for suffix in ("_rob", "_mm", "_std"):
                candidate = f"{col}{suffix}"
                if candidate in X_train.columns:
                    target_col = candidate
                    break
        if target_col in X_train.columns:
            s_tr = X_train[target_col]
            scaled_report[target_col] = {
                "train_mean": round(float(s_tr.mean()), 4),
                "train_std": round(float(s_tr.std(ddof=0)), 4),
                "train_median": round(float(s_tr.median()), 4),
                "train_min": round(float(s_tr.min()), 4),
                "train_max": round(float(s_tr.max()), 4),
            }
    report["scaled_columns"] = scaled_report

    if y_train is not None and y_test is not None:
        report["target_in_features"] = any(
            c in X_train.columns for c in ["reincide"]
        )
        report["y_train_prevalence"] = (
            float(pd.Series(y_train).mean())
            if pd.api.types.is_numeric_dtype(pd.Series(y_train))
            else None
        )
        report["y_test_prevalence"] = (
            float(pd.Series(y_test).mean())
            if pd.api.types.is_numeric_dtype(pd.Series(y_test))
            else None
        )

    return report


def assert_validation(report: Dict[str, object]) -> None:
    """Fail fast if any mandatory invariant is violated."""
    assert report["train_nulls"] == 0, "X_train contains nulls."
    assert report["test_nulls"] == 0, "X_test contains nulls."
    assert report["train_infinities"] == 0, "X_train contains infinities."
    assert report["test_infinities"] == 0, "X_test contains infinities."
    assert report["columns_identical"], "X_train and X_test do not have identical columns."
    assert report["shared_persons"] == 0, "Persons overlap between train and test."
    assert not report.get("target_in_features", False), "Target column found inside X."
