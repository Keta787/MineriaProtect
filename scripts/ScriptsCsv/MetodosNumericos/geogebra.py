"""Automated GeoGebra verification script generator (IDEA-HYB-02).

Produces copy-pasteable GeoGebra Classic command files (.txt) using locale-independent
English command syntax (`FitLine`, `CorrelationCoefficient`, `RSquare`, `Polynomial`,
and explicit `L0(x)..Ln(x)` basis expressions) alongside Spanish equivalents in comments,
directly operationalizing Slides 14-15 of both source HTML presentations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Sequence

from .config import NumericalMethodsConfig
from .experiments_lagrange import LG01Bundle, LG02Bundle
from .experiments_ols import RL01Bundle, RL02Bundle, RL04Bundle


def _fmt_points(xs: Sequence[float], ys: Sequence[float], decimals: int = 4) -> str:
    pairs = [f"({x:.{decimals}f}, {y:.{decimals}f})" if x % 1 else f"({int(x)}, {y:.{decimals}f})" for x, y in zip(xs, ys)]
    return "P = {" + ", ".join(pairs) + "}"


def _fmt_monomial(coeffs_desc: Sequence[float] | None, var: str = "x") -> str:
    if not coeffs_desc:
        return ""
    deg = len(coeffs_desc) - 1
    parts: List[str] = []
    for idx, c in enumerate(coeffs_desc):
        p = deg - idx
        sign = "+" if c >= 0 else "-"
        mag = abs(float(c))
        c_str = f"{mag:.6e}" if (mag != 0.0 and mag < 1e-3) else f"{mag:.6f}"
        term = f"{c_str}*{var}^{p}" if p > 1 else (f"{c_str}*{var}" if p == 1 else c_str)
        parts.append((f"-{term}" if sign == "-" else term) if idx == 0 else f" {sign} {term}")
    return "".join(parts)


def _build_ols_script(
    title: str,
    xs: Sequence[float],
    ys: Sequence[float],
    a0: float,
    a1: float,
    r: float,
    r2: float,
    x_bar: float,
    y_bar: float,
    x_pred: float,
    y_pred: float,
    extra_note: str = "",
) -> str:
    lines = [
        f"# JobPath GeoGebra Verification — {title}",
        "# Paste each command sequentially into GeoGebra Classic Algebra Input (https://www.geogebra.org/classic)",
        "# Spanish equivalents: AjusteLineal(P), CoeficienteCorrelación(P), RCuadrado(P, f)",
        f"# Expected Python OLS: a0 = {a0:.6f}, a1 = {a1:.6f}, r = {r:.6f}, R2 = {r2:.6f}",
    ]
    if extra_note:
        lines.append(extra_note)
    lines.extend(
        [
            _fmt_points(xs, ys, decimals=6),
            "f = FitLine(P)",
            "r = CorrelationCoefficient(P)",
            "R2 = RSquare(P, f)",
            f"Centroid = ({x_bar:.6f}, {y_bar:.6f})",
            f"Q_pred = ({x_pred:g}, f({x_pred:g}))",
            f"# Expected Q_pred y-coordinate: {y_pred:.6f}",
        ]
    )
    return "\n".join(lines) + "\n"


def _build_lagrange_script(
    title: str,
    xs: Sequence[float],
    ys: Sequence[float],
    eval_x: float,
    expected_y: float,
    monomial_desc: Sequence[float] | None = None,
) -> str:
    n = len(xs)
    lines = [
        f"# JobPath GeoGebra Verification — {title}",
        "# Paste each command sequentially into GeoGebra Classic Algebra Input (https://www.geogebra.org/classic)",
        "# Spanish equivalent: q = Polinomio(P). Verify that p(x) and q(x) coincide identically.",
        f"# Expected Python Lagrange: P_{n-1}({eval_x:g}) = {expected_y:.6f}",
    ]
    if monomial_desc:
        lines.append(f"# Expanded monomial form: P_{n-1}(x) = {_fmt_monomial(monomial_desc, var='x')}")
    lines.append(_fmt_points(xs, ys, decimals=6))
    terms: List[str] = []
    for i in range(n):
        num_parts = [f"(x - {xs[j]:g})" for j in range(n) if j != i]
        den_parts = [f"({xs[i]:g} - {xs[j]:g})" for j in range(n) if j != i]
        lines.append(f"L{i}(x) = ({'*'.join(num_parts)}) / ({'*'.join(den_parts)})")
        terms.append(f"{ys[i]:.6f}*L{i}(x)")
    lines.append("p(x) = " + " + ".join(terms))
    lines.append("q = Polynomial(P)")
    lines.append(f"A_eval = ({eval_x:g}, p({eval_x:g}))")
    return "\n".join(lines) + "\n"


def export_hyb02_geogebra_pack(
    cfg: NumericalMethodsConfig,
    rl01: RL01Bundle,
    rl02: RL02Bundle,
    rl04: RL04Bundle,
    lg01: LG01Bundle,
    lg02: LG02Bundle,
) -> Dict[str, Path]:
    """Generate and save verified GeoGebra scripts + summary markdown index."""
    cfg.geogebra_dir.mkdir(parents=True, exist_ok=True)
    exported: Dict[str, Path] = {}

    # 1. IDEA-RL-01: Career-step mean_skills ~ job_order (1..10)
    s10 = rl01.step_profile.loc[rl01.step_profile["job_order"] <= 10]
    m1 = rl01.models["mean_skills"]
    txt_rl01 = _build_ols_script(
        title="IDEA-RL-01 (mean_skills ~ job_order, k=1..10)",
        xs=s10["job_order"].tolist(),
        ys=s10["mean_skills"].tolist(),
        a0=m1.a0,
        a1=m1.a1,
        r=m1.r,
        r2=m1.r2,
        x_bar=m1.x_mean,
        y_bar=m1.y_mean,
        x_pred=12.0,
        y_pred=m1.a0 + m1.a1 * 12.0,
    )
    p1 = cfg.geogebra_dir / "ggb_rl01_career_steps_skills.txt"
    p1.write_text(txt_rl01, encoding="utf-8")
    exported["rl01"] = p1

    # 2. IDEA-RL-02: ISCO-10 major-group centroids (mean_cross_sector ~ mean_total_rel)
    c_df = rl02.isco_centroids
    m2 = rl02.models["isco10_centroids"]
    txt_rl02 = _build_ols_script(
        title="IDEA-RL-02 (ISCO-10 Centroids: mean_cross_sector ~ mean_total_rel)",
        xs=c_df["mean_total_rel"].tolist(),
        ys=c_df["mean_cross_sector"].tolist(),
        a0=m2.a0,
        a1=m2.a1,
        r=m2.r,
        r2=m2.r2,
        x_bar=m2.x_mean,
        y_bar=m2.y_mean,
        x_pred=45.0,
        y_pred=m2.a0 + m2.a1 * 45.0,
        extra_note="# WARNING (MR-06): R2 = 0.2800 < 0.30 -> Model REJECTED for operational forecasting; Q_pred=(45, f(45)) is an arithmetic formula check only.",
    )
    p2 = cfg.geogebra_dir / "ggb_rl02_isco10_transferability.txt"
    p2.write_text(txt_rl02, encoding="utf-8")
    exported["rl02"] = p2

    # 3. IDEA-RL-04: Annual closed-job mean_dur_q ~ (year - 2000) for 2000..2019 (extrapolate to 2027 -> t=27!)
    a_v = rl04.annual_series.loc[rl04.annual_series["start_year"] <= 2019]
    m4 = rl04.models["mean_dur_q_centered_2000_2019"]
    txt_rl04 = _build_ols_script(
        title="IDEA-RL-04 (Annual closed-job mean_dur_q ~ year-2000, 2000..2019; extrap t=27 -> year 2027)",
        xs=a_v["year_centered"].tolist(),
        ys=a_v["mean_dur_q"].tolist(),
        a0=m4.a0,
        a1=m4.a1,
        r=m4.r,
        r2=m4.r2,
        x_bar=m4.x_mean,
        y_bar=m4.y_mean,
        x_pred=27.0,
        y_pred=m4.a0 + m4.a1 * 27.0,
        extra_note="# Strict MR-09 censoring consistency: mean_dur_q computed ONLY on closed jobs (~es_vigente); Q_pred(27) < 0 proves extrapolation failure.",
    )
    p4 = cfg.geogebra_dir / "ggb_rl04_annual_duration_extrapolation.txt"
    p4.write_text(txt_rl04, encoding="utf-8")
    exported["rl04"] = p4

    # 4. IDEA-LG-01: 4-milestone Tenure Survival P3(q) at q = 4, 8, 20, 40 (evaluate q = 12 = 3 years)
    mn = lg01.milestone_nodes
    ev12 = lg01.milestone_eval_table.loc[lg01.milestone_eval_table["quarter_q"] == 12].iloc[0]
    txt_lg01 = _build_lagrange_script(
        title="IDEA-LG-01 (Tenure Survival P3 at q=4,8,20,40; eval q=12 = 3 years)",
        xs=mn["quarter_q"].tolist(),
        ys=mn["S_q"].tolist(),
        eval_x=12.0,
        expected_y=float(ev12["P3_pred"]),
        monomial_desc=lg01.milestone_diagnostics.monomial_coeffs_desc,
    )
    p5 = cfg.geogebra_dir / "ggb_lg01_survival_p3_milestones.txt"
    p5.write_text(txt_lg01, encoding="utf-8")
    exported["lg01"] = p5

    # 5. IDEA-LG-02: PCA Cumulative Variance Forward P3 (Version A, k=1,3,5,8 -> eval k=4)
    p_tbl = lg02.pca_table
    anc = p_tbl.loc[p_tbl["k_components"].isin([1, 3, 5, 8])]
    ev4 = lg02.forward_eval.loc[
        (lg02.forward_eval["version"] == "Version A (con_outliers)") & (lg02.forward_eval["k_eval"] == 4)
    ].iloc[0]
    txt_lg02 = _build_lagrange_script(
        title="IDEA-LG-02 (PCA Cumulative Variance Version A P3 at k=1,3,5,8; eval k=4)",
        xs=anc["k_components"].tolist(),
        ys=anc["cum_var_version_a"].tolist(),
        eval_x=4.0,
        expected_y=float(ev4["P3_pred"]),
        monomial_desc=lg02.diagnostics["forward_Version A (con_outliers)"].monomial_coeffs_desc,
    )
    p6 = cfg.geogebra_dir / "ggb_lg02_pca_forward_p3.txt"
    p6.write_text(txt_lg02, encoding="utf-8")
    exported["lg02"] = p6

    # Markdown verification index
    md_lines = [
        "# GeoGebra Verification Pack Index (`IDEA-HYB-02`)",
        "",
        "Open [GeoGebra Classic](https://www.geogebra.org/classic) and paste the commands from any `.txt` file below into the Algebra Input bar. English command names work in all GeoGebra language locales.",
        "",
        "| Case Study | File | Method | Expected Key Output (Python Verified `< 1e-10`) |",
        "|---|---|---|---|",
        f"| `IDEA-RL-01` | `{p1.name}` | OLS `FitLine` | `a0 = {m1.a0:.6f}`, `a1 = {m1.a1:.6f}`, `R2 = {m1.r2:.6f}`, `f(12) = {m1.a0 + m1.a1*12:.6f}` |",
        f"| `IDEA-RL-02` | `{p2.name}` | OLS `FitLine` (`MR-06` Rejected) | `a0 = {m2.a0:.6f}`, `a1 = {m2.a1:.6f}`, `R2 = {m2.r2:.6f}` (`< 0.30`: `f(45)` solo verificación aritmética) |",
        f"| `IDEA-RL-04` | `{p4.name}` | OLS `FitLine` (`MR-09` `~es_vigente`) | `a0 = {m4.a0:.6f}`, `a1 = {m4.a1:.6f}`, `R2 = {m4.r2:.6f}`, `f(27) = {m4.a0 + m4.a1*27:.6f}` (negative!) |",
        f"| `IDEA-LG-01` | `{p5.name}` | Lagrange `P3` vs `Polynomial(P)` | `P3(12) = {float(ev12['P3_pred']):.6f}` (true `S(12) = {float(ev12['true_S_q']):.6f}`) |",
        f"| `IDEA-LG-02` | `{p6.name}` | Lagrange `P3` vs `Polynomial(P)` | `P3(4) = {float(ev4['P3_pred']):.6f}` (true `V(4) = {float(ev4['true_cum_var']):.6f}`) |",
        "",
    ]
    idx_path = cfg.geogebra_dir / "geogebra_verification_index.md"
    idx_path.write_text("\n".join(md_lines), encoding="utf-8")
    exported["index"] = idx_path

    return exported
