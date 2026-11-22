"""Head-to-head 'Interpolate vs. Fit' comparative laboratory (IDEA-HYB-01).

Directly operationalizes Slide 2 of both HTML presentations across 4 real JobPath
curve regimes and 4 candidate methods under Leave-One-Out Cross-Validation (LOOCV)
and +2-step controlled extrapolation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from .experiments_lagrange import LG01Bundle, LG02Bundle
from .experiments_ols import RL01Bundle, RL04Bundle
from .lagrange import chebyshev_nodes, lagrange_eval, piecewise_lagrange_eval
from .ols import regresion_lineal


@dataclass(frozen=True)
class HYB01Bundle:
    benchmark_matrix: pd.DataFrame
    regime_curves: Dict[str, Dict[str, np.ndarray]]
    decision_rubric: pd.DataFrame


def _evaluate_four_methods_on_regime(
    regime_name: str,
    xs: np.ndarray,
    ys: np.ndarray,
    x_extrap: np.ndarray,
    y_extrap_true: np.ndarray,
) -> Tuple[List[Dict[str, object]], Dict[str, np.ndarray]]:
    """Run LOOCV + 2-step extrapolation for OLS, Global Lagrange, Chebyshev Lagrange, and Piecewise P2."""
    n = len(xs)
    # Interior indices for LOOCV (keep endpoints so LOOCV tests pure interpolation inside [x_min, x_max])
    interior = list(range(1, n - 1))

    # Full-fit curves for plotting on a fine grid
    x_fine = np.linspace(float(xs[0]), float(x_extrap[-1]), 200)
    ols_full = regresion_lineal(xs, ys, name=regime_name)
    y_fine_ols = ols_full.a0 + ols_full.a1 * x_fine

    # Global Lagrange on up to 12 equispaced anchors (for n=40 survival, pick 13 equispaced anchors = deg 12)
    if n > 14:
        g_idx = np.unique(np.round(np.linspace(0, n - 1, 13)).astype(int))
    else:
        g_idx = np.arange(n)
    y_fine_glob, _, _ = lagrange_eval(xs[g_idx], ys[g_idx], x_fine)

    # Chebyshev-Lobatto subset (degree = min(8, n-1); anchored at endpoints)
    ch_deg = min(8, n - 1)
    ch_cont = chebyshev_nodes(float(xs[0]), float(xs[-1]), degree=ch_deg, snap_int=False, kind="lobatto")
    ch_idx = np.unique(np.array([int(np.argmin(np.abs(xs - c))) for c in ch_cont]))
    y_fine_cheb, _, _ = lagrange_eval(xs[ch_idx], ys[ch_idx], x_fine)

    # Piecewise Local Quadratic P2
    y_fine_pw2 = piecewise_lagrange_eval(xs, ys, x_fine, degree=2)

    curves = {
        "xs": xs,
        "ys": ys,
        "x_extrap": x_extrap,
        "y_extrap_true": y_extrap_true,
        "x_fine": x_fine,
        "ols": y_fine_ols,
        "global_lagrange": y_fine_glob,
        "chebyshev_lagrange": y_fine_cheb,
        "piecewise_p2": y_fine_pw2,
    }

    # LOOCV error collectors
    errs: Dict[str, List[float]] = {
        "OLS Linear Regression": [],
        "Global Lagrange (Equispaced)": [],
        "Chebyshev-Node Lagrange": [],
        "Piecewise Local Lagrange (P2)": [],
    }

    for i in interior:
        mask = np.ones(n, dtype=bool)
        mask[i] = False
        x_tr, y_tr = xs[mask], ys[mask]
        xq, yq = float(xs[i]), float(ys[i])

        # 1. OLS
        m_ols = regresion_lineal(x_tr, y_tr)
        errs["OLS Linear Regression"].append(abs(yq - (m_ols.a0 + m_ols.a1 * xq)))

        # 2. Global Equispaced Lagrange (cap at 13 nodes on long curves to measure Runge clearly)
        if len(x_tr) > 14:
            idx_sub = np.unique(np.round(np.linspace(0, len(x_tr) - 1, 13)).astype(int))
            yh_g, _, _ = lagrange_eval(x_tr[idx_sub], y_tr[idx_sub], [xq])
        else:
            yh_g, _, _ = lagrange_eval(x_tr, y_tr, [xq])
        errs["Global Lagrange (Equispaced)"].append(abs(yq - float(yh_g[0])))

        # 3. Chebyshev-Lobatto Lagrange (exclude point i naturally via x_tr)
        ch_pts = chebyshev_nodes(float(x_tr[0]), float(x_tr[-1]), degree=min(8, len(x_tr) - 1), snap_int=False, kind="lobatto")
        ch_tr_idx = np.unique(np.array([int(np.argmin(np.abs(x_tr - c))) for c in ch_pts]))
        yh_c, _, _ = lagrange_eval(x_tr[ch_tr_idx], y_tr[ch_tr_idx], [xq])
        errs["Chebyshev-Node Lagrange"].append(abs(yq - float(yh_c[0])))

        # 4. Piecewise Local P2
        yh_p = piecewise_lagrange_eval(x_tr, y_tr, [xq], degree=2)
        errs["Piecewise Local Lagrange (P2)"].append(abs(yq - float(yh_p[0])))

    # Controlled +2-step Extrapolation MAE (evaluating full models on x_extrap)
    extrap_preds = {
        "OLS Linear Regression": ols_full.a0 + ols_full.a1 * x_extrap,
        "Global Lagrange (Equispaced)": lagrange_eval(xs[g_idx], ys[g_idx], x_extrap)[0],
        "Chebyshev-Node Lagrange": lagrange_eval(xs[ch_idx], ys[ch_idx], x_extrap)[0],
        "Piecewise Local Lagrange (P2)": piecewise_lagrange_eval(xs, ys, x_extrap, degree=2),
    }

    rows: List[Dict[str, object]] = []
    for method, e_list in errs.items():
        e_arr = np.asarray(e_list, dtype=np.float64)
        ext_mae = float(np.mean(np.abs(y_extrap_true - extrap_preds[method])))
        rows.append(
            {
                "regime_name": regime_name,
                "n_train_nodes": n,
                "ols_r2": ols_full.r2,
                "method": method,
                "loocv_mae": float(np.mean(e_arr)),
                "loocv_rmse": float(np.sqrt(np.mean(e_arr**2))),
                "loocv_max_err": float(np.max(e_arr)),
                "extrap_2step_mae": ext_mae,
            }
        )

    # Rank methods by LOOCV RMSE within this regime
    rows.sort(key=lambda r: float(r["loocv_rmse"]))
    for rank, r in enumerate(rows, start=1):
        r["loocv_rank"] = rank

    # Also rank by extrapolation MAE
    ext_order = sorted(range(len(rows)), key=lambda idx: float(rows[idx]["extrap_2step_mae"]))
    for rank, idx in enumerate(ext_order, start=1):
        rows[idx]["extrap_rank"] = rank

    return rows, curves


def run_hyb01_interpolate_vs_fit(
    rl01: RL01Bundle,
    rl04: RL04Bundle,
    lg01: LG01Bundle,
    lg02: LG02Bundle,
) -> HYB01Bundle:
    """Execute the 4-method x 4-regime empirical comparison and build the Selection Rubric."""
    # Regime 1: Smooth near-linear career-step progression (k=1..10, extrap k=11, 12)
    r1_tr = rl01.step_profile.loc[rl01.step_profile["job_order"] <= 10]
    r1_ex = rl01.step_profile.loc[rl01.step_profile["job_order"].isin([11, 12])]

    # Regime 2: Noisy macro annual trend (2000..2017, extrap 2018, 2019 — inside valid support before 2020 collapse!)
    r2_tr = rl04.annual_series.loc[(rl04.annual_series["start_year"] >= 2000) & (rl04.annual_series["start_year"] <= 2017)]
    r2_ex = rl04.annual_series.loc[rl04.annual_series["start_year"].isin([2018, 2019])]

    # Regime 3: Steep nonlinear monotone survival curve S(q) (q=1..36, extrap q=38, 40)
    r3_tr = lg01.survival_curve.loc[lg01.survival_curve["quarter_q"] <= 36]
    r3_ex = lg01.survival_curve.loc[lg01.survival_curve["quarter_q"].isin([38, 40])]

    # Regime 4: Exact concave PCA cumulative variance curve (Version B k=1..8, extrap k=9, 10)
    r4_tr = lg02.pca_table.loc[lg02.pca_table["k_components"] <= 8]
    r4_ex = lg02.pca_table.loc[lg02.pca_table["k_components"].isin([9, 10])]

    regimes = [
        (
            "1. Smooth Near-Linear · Career Steps mean_skills(k)",
            r1_tr["job_order"].to_numpy(dtype=np.float64),
            r1_tr["mean_skills"].to_numpy(dtype=np.float64),
            r1_ex["job_order"].to_numpy(dtype=np.float64),
            r1_ex["mean_skills"].to_numpy(dtype=np.float64),
        ),
        (
            "2. Curved Macro Series · Annual mean_skills(year)",
            r2_tr["start_year"].to_numpy(dtype=np.float64),
            r2_tr["mean_skills"].to_numpy(dtype=np.float64),
            r2_ex["start_year"].to_numpy(dtype=np.float64),
            r2_ex["mean_skills"].to_numpy(dtype=np.float64),
        ),
        (
            "3. Steep Nonlinear Monotone · Survival Curve S(q)",
            r3_tr["quarter_q"].to_numpy(dtype=np.float64),
            r3_tr["survival_prob_S_q"].to_numpy(dtype=np.float64),
            r3_ex["quarter_q"].to_numpy(dtype=np.float64),
            r3_ex["survival_prob_S_q"].to_numpy(dtype=np.float64),
        ),
        (
            "4. Exact Concave Table · PCA CumVar V(k) (Ver. B)",
            r4_tr["k_components"].to_numpy(dtype=np.float64),
            r4_tr["cum_var_version_b"].to_numpy(dtype=np.float64),
            r4_ex["k_components"].to_numpy(dtype=np.float64),
            r4_ex["cum_var_version_b"].to_numpy(dtype=np.float64),
        ),
    ]

    all_rows: List[Dict[str, object]] = []
    curves_map: Dict[str, Dict[str, np.ndarray]] = {}
    rubric_rows: List[Dict[str, object]] = []

    for name, xs, ys, x_ex, y_ex in regimes:
        rows, curves = _evaluate_four_methods_on_regime(name, xs, ys, x_ex, y_ex)
        all_rows.extend(rows)
        curves_map[name] = curves

        best_loocv = next(r for r in rows if r["loocv_rank"] == 1)
        best_extrap = next(r for r in rows if r["extrap_rank"] == 1)
        worst_loocv = max(rows, key=lambda r: float(r["loocv_rmse"]))
        rubric_rows.append(
            {
                "regime_name": name,
                "ols_r2": best_loocv["ols_r2"],
                "best_in_range_method": best_loocv["method"],
                "best_loocv_rmse": best_loocv["loocv_rmse"],
                "best_extrapolation_method": best_extrap["method"],
                "best_extrap_mae": best_extrap["extrap_2step_mae"],
                "worst_in_range_method": worst_loocv["method"],
                "worst_loocv_rmse": worst_loocv["loocv_rmse"],
            }
        )

    return HYB01Bundle(
        benchmark_matrix=pd.DataFrame(all_rows),
        regime_curves=curves_map,
        decision_rubric=pd.DataFrame(rubric_rows),
    )
