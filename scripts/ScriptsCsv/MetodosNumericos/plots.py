"""Suite de 12 figuras en español a 150 DPI (nm01..nm12) para el núcleo de 8 ideas de Métodos Numéricos."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd

from .comparison import HYB01Bundle, run_hyb01_interpolate_vs_fit
from .config import NumericalMethodsConfig, PALETTE, default_config
from .experiments_lagrange import LG01Bundle, LG02Bundle, run_lg02_pca_curves
from .experiments_ols import RL01Bundle, RL02Bundle, RL04Bundle, RL05Bundle, run_rl02_esco_catalog
from .lagrange import chebyshev_nodes, diagnose_lagrange, lagrange_basis, lagrange_eval, piecewise_lagrange_eval
from .ols import OLSResult, regresion_lineal


def _verdict_es(verdict: str) -> str:
    if "Strong" in verdict:
        return "Ajuste Lineal Fuerte (R² ≥ 0.70)"
    if "Moderate" in verdict:
        return "Ajuste Lineal Moderado (0.30 ≤ R² < 0.70)"
    if "Rejected" in verdict:
        return "Modelo Lineal Débil / Rechazado (R² < 0.30)"
    return verdict


def _style_ax(ax: plt.Axes, title: str, xlabel: str, ylabel: str) -> None:
    ax.set_title(title, fontsize=10.8, fontweight="bold", color=PALETTE["ink"], pad=8)
    ax.set_xlabel(xlabel, fontsize=9.3, color=PALETTE["ink"])
    ax.set_ylabel(ylabel, fontsize=9.3, color=PALETTE["ink"])
    ax.grid(True, color=PALETTE["grid"], linestyle="-", linewidth=0.8, alpha=0.9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(colors=PALETTE["muted"], labelsize=8.5)


def _save(fig: plt.Figure, path: Path, dpi: int) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def generate_all_figures(
    cfg: NumericalMethodsConfig,
    rl01: RL01Bundle,
    rl02: RL02Bundle,
    rl04: RL04Bundle,
    rl05: RL05Bundle,
    lg01: LG01Bundle,
    lg02: LG02Bundle,
    hyb01: HYB01Bundle,
) -> Dict[str, Path]:
    """Renderiza y exporta las 12 figuras aprobadas (nm01..nm12) completamente en español."""
    out: Dict[str, Path] = {}
    fdir = cfg.figures_dir
    dpi = cfg.dpi

    # --- nm01: IDEA-RL-01 Panel 4x OLS por paso de carrera ---
    fig, axes = plt.subplots(2, 2, figsize=(12.6, 8.6))
    s10 = rl01.step_profile.loc[rl01.step_profile["job_order"] <= 10]
    s_ex = rl01.step_profile.loc[rl01.step_profile["job_order"] > 10]
    panels = [
        ("mean_skills", "Competencias Esenciales Exigidas (Media)", "Competencias esenciales (conteo)"),
        ("reincide_rate", "Tasa de Reincidencia en el Oficio", "P(veces_ese_oficio > 1)"),
        ("mean_dur_q", "Duración Promedio del Empleo (Trimestres)", "Trimestres"),
        ("mean_green", "Intensidad Verde Media ESCO (greenShare)", "greenShare (0–1)"),
    ]
    for ax, (col, ttl, ylab) in zip(axes.flat, panels):
        m = rl01.models[col]
        x_line = np.linspace(1.0, 15.0, 120)
        ax.axvspan(1.0, 10.0, color=PALETTE["teal"], alpha=0.06, label="Rango de ajuste (k=1..10)")
        ax.axvspan(10.0, 15.5, color=PALETTE["rose"], alpha=0.05, label="Zona de extrapolación (k>10)")
        ax.plot(x_line, m.a0 + m.a1 * x_line, color=PALETTE["teal"], lw=2.3, label=f"MCO: ŷ={m.a0:.4f}{m.a1:+.4f}k")
        ax.scatter(s10["job_order"], s10[col], color=PALETTE["indigo"], s=48, zorder=4, label="Observado (k=1..10)")
        ax.scatter(s_ex["job_order"], s_ex[col], color=PALETTE["rose"], marker="x", s=55, zorder=4, label="Observado (k=11..15)")
        ax.scatter([m.x_mean], [m.y_mean], color=PALETTE["amber"], marker="D", s=75, zorder=5, label=f"Centroide ({m.x_mean:.1f}, {m.y_mean:.3f})")
        ax.text(
            0.03, 0.94, f"R² = {m.r2:.4f} | r = {m.r:+.4f} | Sy/x = {m.s_yx:.4f}",
            transform=ax.transAxes, fontsize=8.4, fontweight="bold", va="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor=PALETTE["grid"]),
        )
        _style_ax(ax, ttl, "Paso de trayectoria laboral (job_order k)", ylab)
        ax.legend(fontsize=7.3, loc="lower right", framealpha=0.92)
    fig.suptitle("IDEA-RL-01 · Regresión Lineal por Mínimos Cuadrados por Paso de Carrera (k = 1..10)", fontsize=13, fontweight="bold", color=PALETTE["ink"], y=1.01)
    out["nm01"] = _save(fig, fdir / "nm01_rl01_career_steps_panel.png", dpi)

    # --- nm02: IDEA-RL-01 Cuadrados de residuos (Diapositiva 4) y gráfico de residuos ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.6, 4.9))
    m_sk = rl01.models["mean_skills"]
    xs_10 = s10["job_order"].to_numpy(dtype=float)
    ys_10 = s10["mean_skills"].to_numpy(dtype=float)
    yh_10 = m_sk.a0 + m_sk.a1 * xs_10
    res_10 = ys_10 - yh_10
    ax1.plot(xs_10, yh_10, color=PALETTE["teal"], lw=2.5, label=f"MCO: ŷ = {m_sk.a0:.4f} + {m_sk.a1:.4f}k")
    for x0, y0, yh0 in zip(xs_10, ys_10, yh_10):
        ax1.plot([x0, x0], [y0, yh0], color=PALETTE["rose"], ls="--", lw=1.6)
        side = abs(y0 - yh0)
        rect = patches.Rectangle((x0, min(y0, yh0)), side * 1.8, side, facecolor=PALETTE["rose"], alpha=0.22, edgecolor=PALETTE["rose"], lw=0.8)
        ax1.add_patch(rect)
    ax1.scatter(xs_10, ys_10, color=PALETTE["indigo"], s=55, zorder=4, label="Media observada (mean_skills)")
    ax1.scatter([m_sk.x_mean], [m_sk.y_mean], color=PALETTE["amber"], marker="D", s=85, zorder=5, label=f"Centroide ({m_sk.x_mean:.1f}, {m_sk.y_mean:.3f})")
    _style_ax(ax1, f"Minimización de Sr = Σeᵢ² = {m_sk.s_r:.5f} (R² = {m_sk.r2:.4f})", "Paso de carrera k", "Competencias esenciales promedio exigidas")
    ax1.legend(fontsize=8.2)

    colors_r = [PALETTE["teal"] if e >= 0 else PALETTE["rose"] for e in res_10]
    ax2.axhline(0.0, color=PALETTE["ink"], lw=1.2)
    ax2.bar(xs_10, res_10, color=colors_r, alpha=0.85, width=0.55)
    ax2.axhline(m_sk.s_yx, color=PALETTE["amber"], ls=":", lw=1.4, label=f"+Sy/x = +{m_sk.s_yx:.4f}")
    ax2.axhline(-m_sk.s_yx, color=PALETTE["amber"], ls=":", lw=1.4, label=f"-Sy/x = -{m_sk.s_yx:.4f}")
    _style_ax(ax2, f"Residuos verticales eᵢ = yᵢ - ŷᵢ (Σeᵢ = {m_sk.residual_sum:.2e})", "Paso de carrera k", "Residuo vertical eᵢ (competencias)")
    ax2.legend(fontsize=8.5)
    out["nm02"] = _save(fig, fdir / "nm02_rl01_residual_squares_and_extrapolation.png", dpi)

    # --- nm03: IDEA-RL-02 Alto R² vs. Bajo R² Rechazado (Catálogo ESCO 3,039) ---
    fig, axes = plt.subplots(2, 2, figsize=(12.6, 8.6))
    cat = rl02.catalog_df
    cat_panels = [
        ("n_ess_comp", "n_essential", "Ajuste Estructural Fuerte · Esenciales vs. Competencias Prácticas", PALETTE["teal"]),
        ("n_total_rel", "n_cross_sector", "Transferibilidad Moderada · Intersectoriales vs. Total de Skills", PALETTE["indigo"]),
        ("n_essential", "n_optional", "RECHAZADO (Diap. 13) · Opcionales vs. Esenciales", PALETTE["rose"]),
        ("n_essential", "greenShare", "RECHAZADO / Ortogonal · greenShare ESCO vs. Esenciales", PALETTE["rose"]),
    ]
    for ax, (xc, yc, ttl, col_line) in zip(axes.flat, cat_panels):
        m = rl02.models[f"{yc}~{xc}"]
        ax.scatter(cat[xc], cat[yc], s=10, alpha=0.28, color=PALETTE["indigo"], edgecolors="none")
        xg = np.linspace(m.x_min, m.x_max, 100)
        ax.plot(xg, m.a0 + m.a1 * xg, color=col_line, lw=2.4, label=f"ŷ = {m.a0:.3f} {m.a1:+.4f}x")
        ax.text(
            0.03, 0.94, f"n = {m.n:,} | R² = {m.r2:.4f} | r = {m.r:+.4f}\n{_verdict_es(m.quality_verdict)}",
            transform=ax.transAxes, fontsize=8.1, fontweight="bold", va="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor=col_line),
        )
        _style_ax(ax, ttl, xc, yc)
        ax.legend(fontsize=8, loc="lower right")
    fig.suptitle("IDEA-RL-02 · Ontología ESCO v1.2.1: Acoples de Alto R² frente a Modelos Lineales Rechazados", fontsize=12.5, fontweight="bold", color=PALETTE["ink"], y=1.01)
    out["nm03"] = _save(fig, fdir / "nm03_rl02_esco_high_vs_low_r2.png", dpi)

    # --- nm04: IDEA-RL-02 Pendientes por Gran Grupo ISCO-08 ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.0, 5.1))
    isc = rl02.isco_major_summary.sort_values("a1_cross_sector_slope", ascending=True)
    y_pos = np.arange(len(isc))
    short_lbl = [f"ISCO {r['isco_major']} · {r['isco_major_label'][:26]}" for _, r in isc.iterrows()]
    ax1.barh(y_pos, isc["a1_cross_sector_slope"], color=PALETTE["teal"], alpha=0.88)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(short_lbl, fontsize=8.2)
    for idx_b, val in enumerate(isc["a1_cross_sector_slope"]):
        ax1.text(val + 0.01, idx_b, f"{val:.3f}", va="center", fontsize=8, color=PALETTE["ink"])
    _style_ax(ax1, "Pendiente Marginal Intersectorial (a₁) por Gran Grupo ISCO", "Pendiente a₁ (skills intersectoriales por cada skill adicional)", "")

    mc = rl02.models["isco10_centroids"]
    ax2.scatter(isc["mean_total_rel"], isc["mean_cross_sector"], color=PALETTE["indigo"], s=65, zorder=4)
    xg = np.linspace(mc.x_min - 2, mc.x_max + 2, 100)
    ax2.plot(xg, mc.a0 + mc.a1 * xg, color=PALETTE["teal"], lw=2.3, label=f"MCO: ŷ={mc.a0:.2f}+{mc.a1:.3f}x (R²={mc.r2:.3f})")
    for _, r in isc.iterrows():
        ax2.annotate(f"G{r['isco_major']}", (r["mean_total_rel"], r["mean_cross_sector"]), xytext=(4, 4), textcoords="offset points", fontsize=8, fontweight="bold")
    _style_ax(ax2, "10 Centroides de Grandes Grupos ISCO (Set de GeoGebra)", "Media total de skills vinculados", "Media de skills intersectoriales")
    ax2.legend(fontsize=8.2)
    out["nm04"] = _save(fig, fdir / "nm04_rl02_isco_major_group_slopes.png", dpi)

    # --- nm05: IDEA-RL-04 Deriva Anual y Falla de Extrapolación ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.0, 5.1))
    ann = rl04.annual_series
    ann_v = ann.loc[ann["start_year"] <= 2019]
    ann_c = ann.loc[ann["start_year"] >= 2020]

    ms_v = rl04.models["mean_skills_2000_2019"]
    ms_f = rl04.models["mean_skills_2000_2023"]
    xg = np.linspace(2000, 2024, 120)
    ax1.axvspan(2000, 2019.4, color=PALETTE["teal"], alpha=0.06)
    ax1.axvspan(2019.4, 2024.5, color=PALETTE["rose"], alpha=0.08, label="Cola censurada dispersa (n=59..1)")
    ax1.scatter(ann_v["start_year"], ann_v["mean_skills"], color=PALETTE["indigo"], s=45, label="Años válidos 2000–2019")
    ax1.scatter(ann_c["start_year"], ann_c["mean_skills"], color=PALETTE["rose"], marker="X", s=70, label="Cola escasa 2020–2023")
    ax1.plot(xg, ms_v.a0 + ms_v.a1 * xg, color=PALETTE["teal"], lw=2.4, label=f"MCO 2000–2019 (a₁={ms_v.a1:+.4f}, R²={ms_v.r2:.3f})")
    ax1.plot(xg, ms_f.a0 + ms_f.a1 * xg, color=PALETTE["rose"], ls="--", lw=2.0, label=f"MCO 2000–2023 (a₁={ms_f.a1:+.4f}, R²={ms_f.r2:.3f})")
    _style_ax(ax1, "Distorsión por Censura: Invierte Pendiente y Colapsa R² (0.748 → 0.083)", "Año de inicio del empleo", "Media de competencias esenciales exigidas")
    ax1.legend(fontsize=7.5, loc="lower left")

    md_v = rl04.models["mean_dur_q_2000_2019"]
    xg2 = np.linspace(2000, 2028, 120)
    ax2.axvspan(2000, 2019.4, color=PALETTE["teal"], alpha=0.06)
    ax2.axvspan(2019.4, 2028.5, color=PALETTE["rose"], alpha=0.08, label="Zona de riesgo por extrapolación")
    ax2.axhline(0.0, color=PALETTE["ink"], lw=1.2, ls=":")
    ax2.scatter(ann_v["start_year"], ann_v["mean_dur_q"], color=PALETTE["indigo"], s=45, label="Observado 2000–2019")
    ax2.plot(xg2, md_v.a0 + md_v.a1 * xg2, color=PALETTE["teal"], lw=2.4, label=f"MCO 2000–2019 (R²={md_v.r2:.3f})")
    y27 = md_v.a0 + md_v.a1 * 2027.0
    ax2.scatter([2027], [y27], color=PALETTE["rose"], s=85, zorder=5, label=f"Extrapolado 2027 = {y27:.2f} trim. (< 0!)")
    _style_ax(ax2, "Falla de Extrapolación (Diap. 12): Duración Negativa tras 2026", "Año de inicio del empleo", "Duración media observada (trimestres)")
    ax2.legend(fontsize=7.7, loc="upper right")
    out["nm05"] = _save(fig, fdir / "nm05_rl04_annual_drift_and_censoring_extrapolation.png", dpi)

    # --- nm06: IDEA-RL-05 Auditoría de Outliers (4 vías) e Invarianza de Escala ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.0, 5.1))
    oc = rl05.outlier_comparison.loc[rl05.outlier_comparison["x_var"] == "n_skills_competence"].reset_index(drop=True)
    labels_short = ["Versión A\nCon Outliers\n(1.74M)", "Versión B\nWinsor. IQR\n(1.74M)", "Legado\nLimpio\n(348k)", "Legado\nBorrado Filas\n(315k)"]
    x_idx = np.arange(len(oc))
    bars = ax1.bar(x_idx, oc["s_yx"], color=[PALETTE["indigo"], PALETTE["teal"], PALETTE["slate"], PALETTE["rose"]], width=0.55)
    for b, (_, r) in zip(bars, oc.iterrows()):
        ax1.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.08, f"Sy/x={r['s_yx']:.3f}\na₁={r['a1']:.4f}\nR²={r['r2']:.4f}", ha="center", va="bottom", fontsize=7.8)
    ax1.set_xticks(x_idx)
    ax1.set_xticklabels(labels_short, fontsize=8.3)
    ax1.set_ylim(0, max(oc["s_yx"]) * 1.28)
    _style_ax(ax1, "Impacto del Tratamiento de Outliers en Sy/x y Pendiente", "Estrategia de tratamiento de datos", "Error estándar de estimación Sy/x (skills)")

    inv = rl05.scale_invariance_table
    inv_labels = [f"{r['version'][:3]}/{r['split']}\n{r['x_var'].split('_')[-1]}" for _, r in inv.iterrows()]
    err_vals = np.maximum(inv["max_invariance_err"].to_numpy(dtype=float), 1e-16)
    ax2.bar(np.arange(len(inv)), -np.log10(err_vals), color=PALETTE["teal"], alpha=0.88, width=0.6)
    ax2.axhline(10.0, color=PALETTE["rose"], ls="--", lw=1.6, label="Umbral de tolerancia (1e-10 → 10 dígitos)")
    ax2.set_xticks(np.arange(len(inv)))
    ax2.set_xticklabels(inv_labels, fontsize=7.5, rotation=25)
    _style_ax(ax2, "Precisión de Invarianza Afín en 04_transformed (-log10 error máx.)", "Versión / Partición / Predictor", "Dígitos decimales exactos (-log10 error)")
    ax2.legend(fontsize=8)
    out["nm06"] = _save(fig, fdir / "nm06_rl05_outlier_strategies_and_scale_invariance.png", dpi)

    # --- nm07: IDEA-LG-01 Supervivencia Laboral P3(q) y Polinomios Base L0..L3 ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.0, 5.1))
    sc = lg01.survival_curve
    mn = lg01.milestone_nodes
    qs_grid = np.linspace(1.0, 46.0, 200)
    p3_grid, _, _ = lagrange_eval(mn["quarter_q"].values, mn["S_q"].values, qs_grid)
    ev12 = lg01.milestone_eval_table.loc[lg01.milestone_eval_table["quarter_q"] == 12].iloc[0]

    ax1.axvspan(4, 40, color=PALETTE["teal"], alpha=0.06, label="Dominio de interpolación [4, 40]")
    ax1.plot(sc["quarter_q"], sc["survival_prob_S_q"], color=PALETTE["slate"], lw=2.0, ls="--", label="Curva real S(q) (1.64M empleos cerrados)")
    ax1.plot(qs_grid, p3_grid, color=PALETTE["teal"], lw=2.5, label="Lagrange cúbico P₃(q)")
    ax1.scatter(mn["quarter_q"], mn["S_q"], color=PALETTE["indigo"], s=65, zorder=5, label="4 nodos hito (1, 2, 5 y 10 años)")
    ax1.scatter([12], [ev12["P3_pred"]], color=PALETTE["amber"], marker="D", s=85, zorder=6, label=f"P₃(12) = {ev12['P3_pred']:.4f} (real {ev12['true_S_q']:.4f})")
    ax1.set_ylim(-0.05, 1.08)
    _style_ax(ax1, "IDEA-LG-01 · Curva de Supervivencia Laboral por Lagrange P₃(q)", "Antigüedad q (trimestres)", "Probabilidad de permanencia S(q) = P(dur_q ≥ q)")
    ax1.legend(fontsize=7.7)

    q_b = np.linspace(4.0, 40.0, 200)
    b_cols = [PALETTE["indigo"], PALETTE["rose"], PALETTE["amber"], PALETTE["teal"]]
    w12 = [ev12["L0_q4"], ev12["L1_q8"], ev12["L2_q20"], ev12["L3_q40"]]
    for i, (col_b, wi) in enumerate(zip(b_cols, w12)):
        ax2.plot(q_b, lagrange_basis(mn["quarter_q"].values, i, q_b), color=col_b, lw=2.0, label=f"L{i}(q) · peso en q=12: {wi:+.4f}")
    ax2.axvline(12.0, color=PALETTE["ink"], ls=":", lw=1.4, label=f"q = 12 (ΣLᵢ = {ev12['sum_Li']:.6f})")
    ax2.axhline(0.0, color=PALETTE["muted"], lw=0.9)
    ax2.axhline(1.0, color=PALETTE["muted"], lw=0.9, ls="--")
    _style_ax(ax2, "Polinomios Base L₀..L₃ ('Encendidos' en 1 en su nodo, 0 en los demás)", "Trimestre q", "Peso base Lᵢ(q)")
    ax2.legend(fontsize=7.7, loc="upper right")
    out["nm07"] = _save(fig, fdir / "nm07_lg01_survival_milestones_and_weights.png", dpi)

    # --- nm08: IDEA-LG-01 Fenómeno de Runge Empírico vs. Chebyshev y P2 por tramos ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.0, 5.1))
    rb = lg01.runge_benchmark
    strat_map = [
        ("Equispaced Global Lagrange", "Lagrange Global Equiespaciado", PALETTE["rose"], "o"),
        ("Chebyshev-Snapped Global Lagrange", "Lagrange Global con Nodos Chebyshev", PALETTE["teal"], "s"),
        ("Piecewise Local Quadratic (P2)", "Lagrange Local Cuadrático por Tramos (P₂)", PALETTE["amber"], "^"),
    ]
    for strat_key, strat_lbl, col_s, mk in strat_map:
        sub = rb.loc[rb["node_strategy"] == strat_key]
        ax1.plot(sub["degree"], sub["max_abs_err"], marker=mk, lw=2.3, color=col_s, label=strat_lbl)
    ax1.set_yscale("log")
    _style_ax(ax1, "Fenómeno de Runge en Supervivencia S(q): Error Máx. vs. Grado", "Grado del polinomio n", "Error absoluto máximo E∞ (escala log)")
    ax1.legend(fontsize=8.0)

    qs = lg01.runge_curves["qs"]
    ax2.axhline(0.0, color=PALETTE["muted"], lw=0.9, ls=":")
    ax2.axhline(1.0, color=PALETTE["muted"], lw=0.9, ls=":")
    ax2.plot(qs, lg01.runge_curves["true"], color=PALETTE["ink"], lw=2.6, label="Curva real S(q)")
    ax2.plot(qs, lg01.runge_curves["eq_deg16"], color=PALETTE["rose"], lw=1.8, ls="--", label="Equiespaciado grado 16 (¡EXPLOSIÓN RUNGE!)")
    ax2.plot(qs, lg01.runge_curves["cheb_deg16"], color=PALETTE["teal"], lw=2.0, label="Chebyshev grado 16 (18.9× menos error)")
    ax2.plot(qs, lg01.runge_curves["pw2_deg16"], color=PALETTE["amber"], lw=2.0, ls="-.", label="Local por tramos P₂")
    ax2.set_ylim(-0.6, 1.4)
    _style_ax(ax2, "Prueba Visual Grado 16: Oscilación en Extremos vs. Mitigaciones", "Antigüedad q (trimestres)", "Probabilidad estimada de permanencia")
    ax2.legend(fontsize=7.6, loc="upper right")
    out["nm08"] = _save(fig, fdir / "nm08_lg01_runge_phenomenon_vs_chebyshev.png", dpi)

    # --- nm09: IDEA-LG-02 PCA Directa e Inversa ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.0, 5.1))
    pt = lg02.pca_table
    kf = np.linspace(1.0, 8.0, 150)
    anc_k = np.array([1.0, 3.0, 5.0, 8.0])
    p3_a, _, _ = lagrange_eval(anc_k, pt.loc[pt["k_components"].isin([1, 3, 5, 8]), "cum_var_version_a"].values, kf)
    p3_b, _, _ = lagrange_eval(anc_k, pt.loc[pt["k_components"].isin([1, 3, 5, 8]), "cum_var_version_b"].values, kf)
    ax1.plot(kf, p3_a, color=PALETTE["indigo"], lw=2.2, label="Lagrange P₃ (Ver. A · con outliers)")
    ax1.scatter(pt["k_components"], pt["cum_var_version_a"], color=PALETTE["indigo"], s=42, alpha=0.85, label="PCA exacto (Ver. A)")
    ax1.plot(kf, p3_b, color=PALETTE["teal"], lw=2.2, ls="--", label="Lagrange P₃ (Ver. B · sin outliers)")
    ax1.scatter(pt["k_components"], pt["cum_var_version_b"], color=PALETTE["teal"], marker="s", s=38, alpha=0.85, label="PCA exacto (Ver. B)")
    ax1.annotate("Meseta V(9)=V(10)=1.0\n(bloqueada en inversa)", xy=(9.5, 1.0), xytext=(5.9, 0.84),
                 arrowprops=dict(arrowstyle="->", color=PALETTE["rose"]), fontsize=8, fontweight="bold", color=PALETTE["rose"])
    _style_ax(ax1, "Lagrange Directo P₃ sobre Varianza Acumulada PCA (50k)", "Número de componentes principales (k)", "Varianza acumulada explicada V(k)")
    ax1.legend(fontsize=7.6, loc="lower right")

    inv = lg02.inverse_eval
    va_inv = inv.loc[inv["version"].str.contains("Version A")]
    vb_inv = inv.loc[inv["version"].str.contains("Version B")]
    x_pos = np.arange(len(va_inv))
    w = 0.35
    ax2.bar(x_pos - w / 2, va_inv["k_est_local_P2"], width=w, color=PALETTE["indigo"], label="Versión A · k(V*) vía Inversa P₂")
    ax2.bar(x_pos + w / 2, vb_inv["k_est_local_P2"], width=w, color=PALETTE["teal"], label="Versión B · k(V*) vía Inversa P₂")
    for idx_i, (a_v, b_v) in enumerate(zip(va_inv["k_est_local_P2"], vb_inv["k_est_local_P2"])):
        ax2.text(idx_i - w / 2, a_v + 0.08, f"{a_v:.2f}", ha="center", fontsize=8)
        ax2.text(idx_i + w / 2, b_v + 0.08, f"{b_v:.2f}", ha="center", fontsize=8)
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels([f"{int(v*100)}%" for v in va_inv["target_variance_V"]], fontsize=9)
    _style_ax(ax2, "Interpolación Inversa de Lagrange: Dimensionalidad Efectiva k(V*)", "Umbral objetivo de varianza acumulada V*", "Componentes interpolados k(V*)")
    ax2.legend(fontsize=8.2)
    out["nm09"] = _save(fig, fdir / "nm09_lg02_pca_forward_and_inverse_lagrange.png", dpi)

    # --- nm10: IDEA-HYB-01 Superposición Visual de los 4 Regímenes ---
    reg_titles_es = [
        "1. Suave Casi Lineal · Pasos de Carrera mean_skills(k)",
        "2. Serie Macro Ruidosa · Anual mean_skills(año)",
        "3. No Lineal Monótona Empinada · Supervivencia S(q)",
        "4. Tabla Cóncava Exacta · Varianza PCA V(k) (Ver. B)",
    ]
    fig, axes = plt.subplots(2, 2, figsize=(13.0, 8.8))
    for ax, ttl_es, (_, c) in zip(axes.flat, reg_titles_es, hyb01.regime_curves.items()):
        ax.axvspan(c["xs"][0], c["xs"][-1], color=PALETTE["teal"], alpha=0.05)
        ax.axvspan(c["xs"][-1], c["x_extrap"][-1], color=PALETTE["rose"], alpha=0.07)
        y_lo, y_hi = float(np.min(c["ys"])), float(np.max(c["ys"]))
        pad = max(0.25 * (y_hi - y_lo), 0.05)
        ax.plot(c["x_fine"], c["ols"], color=PALETTE["indigo"], lw=2.1, label="Regresión Lineal MCO")
        ax.plot(c["x_fine"], np.clip(c["global_lagrange"], y_lo - 2 * pad, y_hi + 2 * pad), color=PALETTE["rose"], ls="--", lw=1.6, label="Lagrange Global (Equiespaciado)")
        ax.plot(c["x_fine"], np.clip(c["chebyshev_lagrange"], y_lo - 2 * pad, y_hi + 2 * pad), color=PALETTE["teal"], ls="-.", lw=1.8, label="Lagrange con Nodos Chebyshev")
        ax.plot(c["x_fine"], np.clip(c["piecewise_p2"], y_lo - 2 * pad, y_hi + 2 * pad), color=PALETTE["amber"], lw=2.0, label="Lagrange Local por Tramos P₂")
        ax.scatter(c["xs"], c["ys"], color=PALETTE["ink"], s=28, zorder=5, label="Nodos de entrenamiento")
        ax.scatter(c["x_extrap"], c["y_extrap_true"], color=PALETTE["rose"], marker="X", s=60, zorder=6, label="Extrapolación +2 real")
        ax.set_ylim(y_lo - pad, y_hi + pad)
        _style_ax(ax, ttl_es, "x", "y")
        ax.legend(fontsize=7.0, loc="best", framealpha=0.9)
    fig.suptitle("IDEA-HYB-01 · '¿Interpolar o Ajustar?' (Diapositiva 2 de Ambos HTML) en 4 Regímenes Reales de JobPath", fontsize=12.6, fontweight="bold", color=PALETTE["ink"], y=1.01)
    out["nm10"] = _save(fig, fdir / "nm10_hyb01_interpolate_vs_fit_four_regimes.png", dpi)

    # --- nm11: IDEA-HYB-01 Barras Relativas de LOOCV y Extrapolación ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.2))
    bm = hyb01.benchmark_matrix.copy()
    methods = ["OLS Linear Regression", "Global Lagrange (Equispaced)", "Chebyshev-Node Lagrange", "Piecewise Local Lagrange (P2)"]
    methods_es = ["Regresión Lineal MCO", "Lagrange Global (Equiesp.)", "Lagrange Chebyshev", "Lagrange Local P₂"]
    reg_order = list(hyb01.regime_curves.keys())
    reg_short = ["R1: Pasos\nCarrera", "R2: Skills\nAnuales", "R3: Superv.\nS(q)", "R4: PCA\nV(k)"]

    piv_loocv = bm.pivot(index="regime_name", columns="method", values="loocv_rmse").loc[reg_order, methods]
    piv_loocv_rel = piv_loocv.div(piv_loocv.min(axis=1), axis=0)
    piv_ext = bm.pivot(index="regime_name", columns="method", values="extrap_2step_mae").loc[reg_order, methods]
    piv_ext_rel = piv_ext.div(piv_ext.min(axis=1), axis=0)

    x_g = np.arange(len(reg_short))
    bw = 0.19
    m_cols = [PALETTE["indigo"], PALETTE["rose"], PALETTE["teal"], PALETTE["amber"]]
    for j, (meth, meth_es, col_m) in enumerate(zip(methods, methods_es, m_cols)):
        ax1.bar(x_g + (j - 1.5) * bw, np.minimum(piv_loocv_rel[meth].values, 100.0), width=bw, color=col_m, label=meth_es)
        ax2.bar(x_g + (j - 1.5) * bw, np.minimum(piv_ext_rel[meth].values, 100.0), width=bw, color=col_m, label=meth_es)
    ax1.set_yscale("log")
    ax2.set_yscale("log")
    ax1.axhline(1.0, color=PALETTE["ink"], lw=1.0, ls=":")
    ax2.axhline(1.0, color=PALETTE["ink"], lw=1.0, ls=":")
    ax1.set_xticks(x_g); ax1.set_xticklabels(reg_short, fontsize=8.5)
    ax2.set_xticks(x_g); ax2.set_xticklabels(reg_short, fontsize=8.5)
    _style_ax(ax1, "Error Relativo LOOCV en Rango (1.0× = Mejor Método; tope 100×)", "Régimen de curva JobPath", "RMSE relativo frente al ganador (log)")
    _style_ax(ax2, "Error Relativo Extrapolación +2 Pasos (1.0× = Mejor Método)", "Régimen de curva JobPath", "MAE relativo de extrapolación (log)")
    ax1.legend(fontsize=7.3, loc="upper left")
    out["nm11"] = _save(fig, fdir / "nm11_hyb01_loocv_and_extrapolation_rubric.png", dpi)

    # --- nm12: IDEA-HYB-02 Tablero de Precisión Numérica ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.0, 4.9))
    ols_checks = {
        "RL-01\nskills~k": rl01.models["mean_skills"].polyfit_max_abs_diff,
        "RL-01\nreincide~k": rl01.models["reincide_rate"].polyfit_max_abs_diff,
        "RL-02\nESCO ess~comp": rl02.models["n_essential~n_ess_comp"].polyfit_max_abs_diff,
        "RL-02\nISCO-10": rl02.models["isco10_centroids"].polyfit_max_abs_diff,
        "RL-04\n2000-19 dur": rl04.models["mean_dur_q_2000_2019"].polyfit_max_abs_diff,
        "RL-05\nInvar. Escala": float(rl05.scale_invariance_table["max_invariance_err"].max()),
    }
    ax1.bar(list(ols_checks.keys()), [-np.log10(max(v, 1e-16)) for v in ols_checks.values()], color=PALETTE["indigo"], width=0.55)
    ax1.axhline(10.0, color=PALETTE["rose"], ls="--", lw=1.5, label="Tolerancia 1e-10 (10 dígitos)")
    ax1.tick_params(axis="x", labelsize=8)
    _style_ax(ax1, "Verificación MCO: Precisión vs. numpy.polyfit (-log10 error)", "Experimento", "Dígitos decimales coincidentes")
    ax1.legend(fontsize=8)

    lg_checks = {
        "LG-01 P3\nKronecker": lg01.milestone_diagnostics.kronecker_max_err,
        "LG-01 P3\nΣLᵢ = 1": lg01.milestone_diagnostics.unity_sum_max_err,
        "LG-01 P3\nvs SciPy": lg01.milestone_diagnostics.scipy_max_abs_diff,
        "LG-02 Ver A\nvs SciPy": lg02.diagnostics["forward_Version A (con_outliers)"].scipy_max_abs_diff,
        "LG-02 Ver B\nvs SciPy": lg02.diagnostics["forward_Version B (sin_outliers)"].scipy_max_abs_diff,
        "LG-02 Inv A\nvs SciPy": lg02.diagnostics["inverse_Version A (con_outliers)"].scipy_max_abs_diff,
    }
    ax2.bar(list(lg_checks.keys()), [-np.log10(max(v, 1e-16)) for v in lg_checks.values()], color=PALETTE["teal"], width=0.55)
    ax2.axhline(10.0, color=PALETTE["rose"], ls="--", lw=1.5, label="Tolerancia 1e-10 (10 dígitos)")
    ax2.tick_params(axis="x", labelsize=8)
    _style_ax(ax2, "Verificación Lagrange: Invariantes y SciPy (-log10 error)", "Control numérico", "Dígitos decimales coincidentes")
    ax2.legend(fontsize=8)
    out["nm12"] = _save(fig, fdir / "nm12_hyb02_verification_summary_dashboard.png", dpi)

    return out


def regenerate_figures_from_tables(cfg: NumericalMethodsConfig | None = None) -> Dict[str, Path]:
    """Reconstruye las 12 figuras en español en ~3s usando las tablas verificadas en disco."""
    cfg = cfg or default_config()
    tdir = cfg.tables_dir

    # Reconstruct lightweight bundles from saved tables (zero 22GB re-scan!)
    step_all = pd.read_csv(tdir / "rl01_career_step_profile.csv")
    s10 = step_all.loc[step_all["job_order"] <= 10]
    rl01_models = {
        col: regresion_lineal(s10["job_order"].values, s10[col].values, name=col)
        for col in ("mean_skills", "reincide_rate", "mean_dur_q", "mean_green")
    }
    rl01 = RL01Bundle(
        step_profile=step_all,
        step_profile_ge10=s10,
        ols_summary=pd.read_csv(tdir / "rl01_ols_summary.csv"),
        summation_skills=pd.read_csv(tdir / "rl01_summation_and_residuals_skills.csv"),
        extrapolation_audit=pd.read_csv(tdir / "rl01_extrapolation_audit.csv"),
        models=rl01_models,
    )

    rl02 = run_rl02_esco_catalog(cfg)  # ~0.3s over 3,039 occupations

    ann = pd.read_csv(tdir / "rl04_annual_macro_series.csv")
    ann_v = ann.loc[ann["start_year"] <= 2019]
    rl04_models = {
        "mean_skills_2000_2019": regresion_lineal(ann_v["start_year"].values, ann_v["mean_skills"].values),
        "mean_skills_2000_2023": regresion_lineal(ann["start_year"].values, ann["mean_skills"].values),
        "mean_dur_q_2000_2019": regresion_lineal(ann_v["start_year"].values, ann_v["mean_dur_q"].values),
    }
    rl04 = RL04Bundle(
        annual_series=ann,
        ols_regime_comparison=pd.read_csv(tdir / "rl04_ols_regime_comparison.csv"),
        extrapolation_audit=pd.read_csv(tdir / "rl04_extrapolation_failure_audit.csv"),
        raw_partition_parity=pd.read_csv(tdir / "rl04_raw_partition_parity.csv"),
        models=rl04_models,
    )

    rl05 = RL05Bundle(
        outlier_comparison=pd.read_csv(tdir / "rl05_four_way_outlier_comparison.csv"),
        scale_invariance_table=pd.read_csv(tdir / "rl05_affine_scale_invariance.csv"),
        scaler_source="cached",
    )

    surv_df = pd.read_csv(tdir / "lg01_survival_curve_S_q.csv")
    qs = surv_df["quarter_q"].to_numpy(dtype=float)
    surv = surv_df["survival_prob_S_q"].to_numpy(dtype=float)
    m_qs = np.array([4.0, 8.0, 20.0, 40.0])
    m_ys = np.array([surv[int(q) - 1] for q in m_qs])
    eq16_idx = np.unique(np.round(np.linspace(0, 39, 17)).astype(int))
    ch16_x = chebyshev_nodes(1.0, 40.0, degree=16, snap_int=True)
    ch16_y = np.array([surv[int(x) - 1] for x in ch16_x])
    lg01 = LG01Bundle(
        survival_curve=surv_df,
        milestone_nodes=pd.DataFrame({"node_i": [0, 1, 2, 3], "quarter_q": m_qs.astype(int), "years": m_qs / 4.0, "S_q": m_ys}),
        milestone_eval_table=pd.read_csv(tdir / "lg01_milestone_P3_weights_and_eval.csv"),
        milestone_diagnostics=diagnose_lagrange(m_qs, m_ys, name="P3"),
        runge_benchmark=pd.read_csv(tdir / "lg01_runge_phenomenon_benchmark.csv"),
        runge_curves={
            "qs": qs,
            "true": surv,
            "eq_deg16": lagrange_eval(qs[eq16_idx], surv[eq16_idx], qs)[0],
            "cheb_deg16": lagrange_eval(ch16_x, ch16_y, qs)[0],
            "pw2_deg16": piecewise_lagrange_eval(qs[eq16_idx], surv[eq16_idx], qs, degree=2),
        },
    )

    lg02 = run_lg02_pca_curves(cfg)
    hyb01 = run_hyb01_interpolate_vs_fit(rl01, rl04, lg01, lg02)
    return generate_all_figures(cfg, rl01, rl02, rl04, rl05, lg01, lg02, hyb01)


if __name__ == "__main__":
    figs = regenerate_figures_from_tables()
    print(f"Regeneradas {len(figs)} figuras en español en {list(figs.values())[0].parent}")
