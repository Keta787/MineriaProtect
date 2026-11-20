"""First-principles Ordinary Least Squares (OLS) linear regression engine.

Implements the exact closed-form normal-equation estimators, summation tables,
residual diagnostics (St, Sr, R^2, r, Sy/x), extrapolation tagging, numpy.polyfit
cross-verification, and affine-scaling invariance verification taught in
`regresion_lineal_minimos_cuadrados.html`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Sequence

import numpy as np
import pandas as pd

from .config import NUMERICAL_TOL


@dataclass(frozen=True)
class OLSResult:
    """Complete closed-form Ordinary Least Squares diagnostic bundle."""

    name: str
    n: int
    sum_x: float
    sum_y: float
    sum_xx: float
    sum_xy: float
    x_mean: float
    y_mean: float
    x_min: float
    x_max: float
    a0: float
    a1: float
    s_t: float
    s_r: float
    r2: float
    r: float
    s_yx: float
    quality_verdict: str
    centroid_err: float
    residual_sum: float
    polyfit_max_abs_diff: float

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def classify_r2_quality(r2: float) -> str:
    """Honest quality verdict honoring MR-06 and Presentation 1 Slide 13."""
    if not np.isfinite(r2):
        return "Undefined (constant y)"
    if r2 >= 0.70:
        return "Strong Linear Fit (R2 >= 0.70)"
    if r2 >= 0.30:
        return "Moderate Linear Fit (0.30 <= R2 < 0.70)"
    return "Weak / Rejected Linear Model (R2 < 0.30)"


def regresion_lineal(
    x: Sequence[float] | np.ndarray,
    y: Sequence[float] | np.ndarray,
    name: str = "",
) -> OLSResult:
    """Fit y_hat = a0 + a1 * x using closed-form least-squares normal equations.

    Computes exact textbook sums (n, sum_x, sum_y, sum_xx, sum_xy) while using
    centered deviations for numerical stability against catastrophic cancellation
    when x has large magnitude (e.g., calendar years ~2010), and verifies both
    against `numpy.polyfit(x, y, 1)`.
    """
    x_arr = np.asarray(x, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)

    if x_arr.ndim != 1 or y_arr.ndim != 1 or x_arr.shape != y_arr.shape:
        raise ValueError("Inputs x and y must be 1D sequences of equal length.")
    if not (np.all(np.isfinite(x_arr)) and np.all(np.isfinite(y_arr))):
        raise ValueError("Inputs x and y must contain only finite numeric values (no NaN/Inf).")

    n = int(x_arr.size)
    if n < 2:
        raise ValueError(f"At least 2 observations are required for OLS (received n={n}).")

    # Textbook sums from Presentation 1 Slide 7
    sum_x = float(np.sum(x_arr))
    sum_y = float(np.sum(y_arr))
    sum_xx = float(np.sum(x_arr * x_arr))
    sum_xy = float(np.sum(x_arr * y_arr))
    x_mean = sum_x / n
    y_mean = sum_y / n

    # Centered normal equations (algebraically identical to (n*sum_xy - sum_x*sum_y)/(n*sum_xx - sum_x^2),
    # immune to floating-point cancellation for large x such as year=2000..2023)
    dx = x_arr - x_mean
    dy = y_arr - y_mean
    s_xx = float(np.dot(dx, dx))
    if s_xx <= 0.0:
        raise ValueError("Zero variance in x: cannot fit OLS slope when all x_i are identical.")

    s_xy = float(np.dot(dx, dy))
    a1 = s_xy / s_xx
    a0 = y_mean - a1 * x_mean

    y_hat = a0 + a1 * x_arr
    residuals = y_arr - y_hat
    s_t = float(np.dot(dy, dy))
    s_r = float(np.dot(residuals, residuals))

    if s_t > 0.0:
        r2 = float(np.clip((s_t - s_r) / s_t, 0.0, 1.0))
        r = float(np.sign(a1) * np.sqrt(r2)) if a1 != 0.0 else 0.0
    else:
        r2 = float("nan")
        r = float("nan")

    s_yx = float(np.sqrt(s_r / (n - 2))) if n > 2 else float("nan")

    # Verify invariants (MR-01) and cross-check with numpy.polyfit(x, y, 1)
    centroid_err = float(abs((a0 + a1 * x_mean) - y_mean))
    residual_sum = float(np.sum(residuals))

    poly_a1, poly_a0 = np.polyfit(x_arr, y_arr, 1)
    polyfit_max_abs_diff = float(max(abs(a0 - float(poly_a0)), abs(a1 - float(poly_a1))))

    return OLSResult(
        name=name,
        n=n,
        sum_x=sum_x,
        sum_y=sum_y,
        sum_xx=sum_xx,
        sum_xy=sum_xy,
        x_mean=x_mean,
        y_mean=y_mean,
        x_min=float(np.min(x_arr)),
        x_max=float(np.max(x_arr)),
        a0=float(a0),
        a1=float(a1),
        s_t=s_t,
        s_r=s_r,
        r2=r2,
        r=r,
        s_yx=s_yx,
        quality_verdict=classify_r2_quality(r2),
        centroid_err=centroid_err,
        residual_sum=residual_sum,
        polyfit_max_abs_diff=polyfit_max_abs_diff,
    )


def predict_ols(
    model: OLSResult,
    x_eval: Sequence[float] | np.ndarray,
) -> pd.DataFrame:
    """Evaluate fitted OLS model at x_eval with explicit extrapolation tagging (MR-05)."""
    xq = np.asarray(x_eval, dtype=np.float64)
    y_hat = model.a0 + model.a1 * xq
    is_extrap = (xq < model.x_min) | (xq > model.x_max)
    return pd.DataFrame(
        {
            "x": xq,
            "y_hat": y_hat,
            "is_extrapolation": is_extrap,
            "domain_status": np.where(is_extrap, "Extrapolation (outside range)", "In-range prediction"),
        }
    )


def build_summation_and_residual_table(
    x: Sequence[float] | np.ndarray,
    y: Sequence[float] | np.ndarray,
    model: OLSResult,
) -> pd.DataFrame:
    """Build step-by-step summation & residual table matching Presentation 1 Slides 7 & 11."""
    x_arr = np.asarray(x, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)
    y_hat = model.a0 + model.a1 * x_arr
    err = y_arr - y_hat
    df = pd.DataFrame(
        {
            "i": np.arange(1, len(x_arr) + 1),
            "x_i": x_arr,
            "y_i": y_arr,
            "x_i_sq": x_arr * x_arr,
            "x_i_y_i": x_arr * y_arr,
            "y_hat_i": y_hat,
            "e_i": err,
            "e_i_sq": err * err,
            "y_minus_ybar_sq": (y_arr - model.y_mean) ** 2,
        }
    )
    return df


def verify_affine_scaling_invariance(
    raw_model: OLSResult,
    scaled_model: OLSResult,
    center_x: float,
    scale_x: float,
    center_y: float,
    scale_y: float,
) -> Dict[str, float | bool]:
    """Algebraically and numerically verify OLS affine invariance under RobustScaler/MinMaxScaler."""
    a1_theory = raw_model.a1 * (scale_x / scale_y)
    a0_theory = (raw_model.a0 + raw_model.a1 * center_x - center_y) / scale_y
    syx_theory = raw_model.s_yx / scale_y

    err_a1 = abs(scaled_model.a1 - a1_theory)
    err_a0 = abs(scaled_model.a0 - a0_theory)
    err_r2 = abs(scaled_model.r2 - raw_model.r2)
    err_r = abs(scaled_model.r - raw_model.r)
    err_syx = abs(scaled_model.s_yx - syx_theory)
    max_err = max(err_a1, err_a0, err_r2, err_r, err_syx)

    return {
        "a0_scaled_obs": scaled_model.a0,
        "a0_scaled_theory": a0_theory,
        "a1_scaled_obs": scaled_model.a1,
        "a1_scaled_theory": a1_theory,
        "r2_raw": raw_model.r2,
        "r2_scaled_obs": scaled_model.r2,
        "s_yx_scaled_obs": scaled_model.s_yx,
        "s_yx_scaled_theory": syx_theory,
        "max_invariance_err": max_err,
        "passes_tol": bool(max_err < NUMERICAL_TOL),
    }
