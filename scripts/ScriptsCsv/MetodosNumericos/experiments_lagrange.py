"""Lagrange Polynomial Interpolation experiments for the 8-idea core (IDEA-LG-01, IDEA-LG-02)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from .config import NumericalMethodsConfig, VERIFIED_PCA_50K
from .lagrange import (
    LagrangeDiagnostics,
    chebyshev_nodes,
    diagnose_lagrange,
    inverse_lagrange_eval,
    lagrange_eval,
    piecewise_lagrange_eval,
)


@dataclass(frozen=True)
class LG01Bundle:
    survival_curve: pd.DataFrame
    milestone_nodes: pd.DataFrame
    milestone_eval_table: pd.DataFrame
    milestone_diagnostics: LagrangeDiagnostics
    runge_benchmark: pd.DataFrame
    runge_curves: Dict[str, np.ndarray]


@dataclass(frozen=True)
class LG02Bundle:
    pca_table: pd.DataFrame
    forward_eval: pd.DataFrame
    inverse_eval: pd.DataFrame
    diagnostics: Dict[str, LagrangeDiagnostics]
    plateau_guard_triggered: bool
    plateau_guard_message: str


def run_lg01_survival_runge(df_a: pd.DataFrame) -> LG01Bundle:
    """IDEA-LG-01: Closed-job tenure survival S(q) reconstruction + Runge phenomenon & Chebyshev remedies."""
    # Strictly closed classified experiences (~es_vigente, MR-09)
    closed = df_a.loc[(df_a["saber_skills"] == "ok") & (~df_a["es_vigente"]), "dur_q"].to_numpy(dtype=np.float64)
    qs = np.arange(1, 41, dtype=np.float64)
    surv = np.array([(closed >= q).mean() for q in qs], dtype=np.float64)

    surv_df = pd.DataFrame(
        {
            "quarter_q": qs.astype(int),
            "years": qs / 4.0,
            "survival_prob_S_q": surv,
            "n_closed_jobs": len(closed),
        }
    )

    # 1. Executive 4-milestone cubic Lagrange P3(q) at 1 yr, 2 yr, 5 yr, 10 yr (q = 4, 8, 20, 40)
    m_qs = np.array([4.0, 8.0, 20.0, 40.0])
    m_ys = np.array([surv[int(q) - 1] for q in m_qs])
    m_diag = diagnose_lagrange(m_qs, m_ys, name="Tenure Survival P3 (q=4,8,20,40)")

    # Evaluate at intermediate milestones (1.5 yr=6, 3 yr=12, 7 yr=28) + extrapolation (12 yr=48)
    eval_qs = np.array([2.0, 6.0, 12.0, 16.0, 28.0, 36.0, 48.0])
    y_hat, w_mat, is_extrap = lagrange_eval(m_qs, m_ys, eval_qs)
    eval_rows: List[Dict[str, object]] = []
    for idx, q in enumerate(eval_qs):
        q_int = int(q)
        true_val = float((closed >= q_int).mean())
        eval_rows.append(
            {
                "quarter_q": q_int,
                "years": q / 4.0,
                "is_extrapolation": bool(is_extrap[idx]),
                "L0_q4": float(w_mat[idx, 0]),
                "L1_q8": float(w_mat[idx, 1]),
                "L2_q20": float(w_mat[idx, 2]),
                "L3_q40": float(w_mat[idx, 3]),
                "sum_Li": float(np.sum(w_mat[idx])),
                "P3_pred": float(y_hat[idx]),
                "true_S_q": true_val,
                "abs_err": abs(true_val - float(y_hat[idx])),
            }
        )

    milestone_nodes = pd.DataFrame(
        {"node_i": [0, 1, 2, 3], "quarter_q": m_qs.astype(int), "years": m_qs / 4.0, "S_q": m_ys}
    )

    # 2. Runge's Phenomenon Benchmark across degrees n in {3, 5, 8, 12, 16}
    bench_rows: List[Dict[str, object]] = []
    runge_curves: Dict[str, np.ndarray] = {"qs": qs, "true": surv}

    for deg in (3, 5, 8, 12, 16):
        # Strategy A: Equispaced nodes on [1, 40]
        eq_idx = np.unique(np.round(np.linspace(0, 39, deg + 1)).astype(int))
        eq_x, eq_y = qs[eq_idx], surv[eq_idx]
        p_eq, _, _ = lagrange_eval(eq_x, eq_y, qs)
        err_eq = np.abs(surv - p_eq)
        bench_rows.append(
            {
                "degree": deg,
                "n_nodes": int(len(eq_x)),
                "node_strategy": "Equispaced Global Lagrange",
                "max_abs_err": float(np.max(err_eq)),
                "rmse": float(np.sqrt(np.mean(err_eq**2))),
                "mae": float(np.mean(err_eq)),
                "min_pred": float(np.min(p_eq)),
                "max_pred": float(np.max(p_eq)),
                "n_prob_bound_violations": int(np.sum((p_eq < 0.0) | (p_eq > 1.0))),
            }
        )
        runge_curves[f"eq_deg{deg}"] = p_eq

        # Strategy B: Chebyshev-snapped nodes on [1, 40]
        ch_x = chebyshev_nodes(1.0, 40.0, degree=deg, snap_int=True)
        ch_y = np.array([surv[int(x) - 1] for x in ch_x])
        p_ch, _, _ = lagrange_eval(ch_x, ch_y, qs)
        err_ch = np.abs(surv - p_ch)
        bench_rows.append(
            {
                "degree": deg,
                "n_nodes": int(len(ch_x)),
                "node_strategy": "Chebyshev-Snapped Global Lagrange",
                "max_abs_err": float(np.max(err_ch)),
                "rmse": float(np.sqrt(np.mean(err_ch**2))),
                "mae": float(np.mean(err_ch)),
                "min_pred": float(np.min(p_ch)),
                "max_pred": float(np.max(p_ch)),
                "n_prob_bound_violations": int(np.sum((p_ch < 0.0) | (p_ch > 1.0))),
            }
        )
        runge_curves[f"cheb_deg{deg}"] = p_ch

        # Strategy C: Piecewise Local Quadratic P2 over the same equispaced anchors
        p_pw = piecewise_lagrange_eval(eq_x, eq_y, qs, degree=2)
        err_pw = np.abs(surv - p_pw)
        bench_rows.append(
            {
                "degree": deg,
                "n_nodes": int(len(eq_x)),
                "node_strategy": "Piecewise Local Quadratic (P2)",
                "max_abs_err": float(np.max(err_pw)),
                "rmse": float(np.sqrt(np.mean(err_pw**2))),
                "mae": float(np.mean(err_pw)),
                "min_pred": float(np.min(p_pw)),
                "max_pred": float(np.max(p_pw)),
                "n_prob_bound_violations": int(np.sum((p_pw < 0.0) | (p_pw > 1.0))),
            }
        )
        runge_curves[f"pw2_deg{deg}"] = p_pw

    return LG01Bundle(
        survival_curve=surv_df,
        milestone_nodes=milestone_nodes,
        milestone_eval_table=pd.DataFrame(eval_rows),
        milestone_diagnostics=m_diag,
        runge_benchmark=pd.DataFrame(bench_rows),
        runge_curves=runge_curves,
    )


def run_lg02_pca_curves(cfg: NumericalMethodsConfig) -> LG02Bundle:
    """IDEA-LG-02: Forward & monotonic inverse Lagrange interpolation on 50k PCA cumulative variance."""
    ks = np.arange(1, 11, dtype=np.float64)
    va = np.array(VERIFIED_PCA_50K["con_outliers"], dtype=np.float64)
    vb = np.array(VERIFIED_PCA_50K["sin_outliers"], dtype=np.float64)

    pca_df = pd.DataFrame(
        {
            "k_components": ks.astype(int),
            "cum_var_version_a": va,
            "cum_var_version_b": vb,
            "marginal_var_version_a": np.diff(np.insert(va, 0, 0.0)),
            "marginal_var_version_b": np.diff(np.insert(vb, 0, 0.0)),
        }
    )

    # 1. Forward interpolation from sparse anchors k = {1, 3, 5, 8} -> predict held-out k = {2, 4, 6, 7}
    anchor_k = np.array([1.0, 3.0, 5.0, 8.0])
    held_k = np.array([2.0, 4.0, 6.0, 7.0])
    forward_rows: List[Dict[str, object]] = []
    diags: Dict[str, LagrangeDiagnostics] = {}

    for ver_label, v_arr in (("Version A (con_outliers)", va), ("Version B (sin_outliers)", vb)):
        anc_y = np.array([v_arr[int(k) - 1] for k in anchor_k])
        diags[f"forward_{ver_label}"] = diagnose_lagrange(anchor_k, anc_y, name=f"PCA Forward P3 · {ver_label}")
        y_pred, w_mat, _ = lagrange_eval(anchor_k, anc_y, held_k)
        for idx, k in enumerate(held_k):
            true_v = float(v_arr[int(k) - 1])
            forward_rows.append(
                {
                    "version": ver_label,
                    "k_eval": int(k),
                    "true_cum_var": true_v,
                    "P3_pred": float(y_pred[idx]),
                    "abs_err": abs(true_v - float(y_pred[idx])),
                    "sum_Li": float(np.sum(w_mat[idx])),
                }
            )

    # 2. Inverse Lagrange interpolation on strictly monotonic prefix k = 1..6 for V* in {0.80, 0.85, 0.90, 0.95}
    targets = np.array([0.80, 0.85, 0.90, 0.95])
    inv_rows: List[Dict[str, object]] = []
    mono_k = np.arange(1, 7, dtype=np.float64)

    for ver_label, v_arr in (("Version A (con_outliers)", va), ("Version B (sin_outliers)", vb)):
        mono_v = v_arr[:6]
        k_hat_local, is_ext = inverse_lagrange_eval(mono_k, mono_v, targets, local_degree=2)
        k_hat_global, _ = inverse_lagrange_eval(mono_k, mono_v, targets, local_degree=None)
        diags[f"inverse_{ver_label}"] = diagnose_lagrange(mono_v, mono_k, name=f"PCA Inverse P5 · {ver_label}")
        for idx, v_star in enumerate(targets):
            k_ceil = int(np.ceil(k_hat_local[idx]))
            k_ceil = min(max(k_ceil, 1), 10)
            actual_at_ceil = float(v_arr[k_ceil - 1])
            inv_rows.append(
                {
                    "version": ver_label,
                    "target_variance_V": float(v_star),
                    "k_est_local_P2": float(k_hat_local[idx]),
                    "k_est_global_P5": float(k_hat_global[idx]),
                    "k_ceil_recommended": k_ceil,
                    "actual_cum_var_at_ceil": actual_at_ceil,
                    "meets_target": bool(actual_at_ceil >= v_star),
                    "is_extrapolation": bool(is_ext[idx]),
                }
            )

    # 3. Verify MR-04 distinct-node guard on Version A plateau V(9) == V(10) == 1.0
    plateau_triggered = False
    plateau_msg = ""
    try:
        inverse_lagrange_eval(ks, va, [0.90])
    except ValueError as exc:
        plateau_triggered = True
        plateau_msg = str(exc)

    return LG02Bundle(
        pca_table=pca_df,
        forward_eval=pd.DataFrame(forward_rows),
        inverse_eval=pd.DataFrame(inv_rows),
        diagnostics=diags,
        plateau_guard_triggered=plateau_triggered,
        plateau_guard_message=plateau_msg,
    )
