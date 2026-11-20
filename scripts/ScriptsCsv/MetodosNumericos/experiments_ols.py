"""Least-Squares Linear Regression experiments for the 8-idea core (IDEA-RL-01, RL-02, RL-04, RL-05)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd

from .config import NumericalMethodsConfig
from .loaders import (
    extract_scaler_params,
    load_esco_catalog_enriched,
    load_legacy_interim_pair,
    load_raw_jobhop_years,
    load_transformed_dense_subset,
)
from .ols import (
    OLSResult,
    build_summation_and_residual_table,
    predict_ols,
    regresion_lineal,
    verify_affine_scaling_invariance,
)


@dataclass(frozen=True)
class RL01Bundle:
    step_profile: pd.DataFrame
    step_profile_ge10: pd.DataFrame
    ols_summary: pd.DataFrame
    summation_skills: pd.DataFrame
    extrapolation_audit: pd.DataFrame
    models: Dict[str, OLSResult]


@dataclass(frozen=True)
class RL02Bundle:
    catalog_df: pd.DataFrame
    ols_summary: pd.DataFrame
    isco_major_summary: pd.DataFrame
    isco_centroids: pd.DataFrame
    models: Dict[str, OLSResult]


@dataclass(frozen=True)
class RL04Bundle:
    annual_series: pd.DataFrame
    ols_regime_comparison: pd.DataFrame
    extrapolation_audit: pd.DataFrame
    raw_partition_parity: pd.DataFrame
    models: Dict[str, OLSResult]


@dataclass(frozen=True)
class RL05Bundle:
    outlier_comparison: pd.DataFrame
    scale_invariance_table: pd.DataFrame
    scaler_source: str


def run_rl01_career_steps(df_a: pd.DataFrame) -> RL01Bundle:
    """IDEA-RL-01: Career-step progression OLS (job_order 1..10) + extrapolation & cohort check."""
    clf = df_a.loc[df_a["saber_skills"] == "ok"].copy()
    clf.sort_values(["resume_id", "start_ord", "end_ord"], inplace=True)
    clf["job_order"] = clf.groupby("resume_id").cumcount() + 1

    # Full classified step profile (k = 1..15 so we can compare extrapolation at k=11, 12, 15 against observed!)
    step_all = (
        clf.loc[clf["job_order"] <= 15]
        .groupby("job_order", as_index=False)
        .agg(
            n_rows=("resume_id", "size"),
            mean_skills=("n_skills_essential", "mean"),
            mean_dur_q=("dur_q", "mean"),
            median_dur_q=("dur_q", "median"),
            mean_green=("greenShare", "mean"),
            reincide_rate=("reincide", "mean"),
        )
    )
    step_10 = step_all.loc[step_all["job_order"] <= 10].copy()

    # Cohort-controlled sensitivity check: persons with >= 10 classified jobs (controls survivorship!)
    job_counts = clf.groupby("resume_id")["job_order"].transform("max")
    step_ge10 = (
        clf.loc[(job_counts >= 10) & (clf["job_order"] <= 10)]
        .groupby("job_order", as_index=False)
        .agg(
            n_rows=("resume_id", "size"),
            mean_skills=("n_skills_essential", "mean"),
            mean_dur_q=("dur_q", "mean"),
            mean_green=("greenShare", "mean"),
            reincide_rate=("reincide", "mean"),
        )
    )

    specs = [
        ("mean_skills", "Essential skills required by occupation (mean)"),
        ("reincide_rate", "Occupation recurrence rate P(veces_ese_oficio > 1)"),
        ("mean_dur_q", "Mean tenure duration (quarters)"),
        ("mean_green", "Mean ESCO greenShare intensity"),
    ]
    models: Dict[str, OLSResult] = {}
    rows: List[Dict[str, object]] = []

    for col, label in specs:
        res = regresion_lineal(step_10["job_order"].values, step_10[col].values, name=f"{col} ~ job_order (1..10)")
        models[col] = res
        row = res.to_dict()
        row.update(
            {
                "idea_id": "IDEA-RL-01",
                "dataset_version": "Version A (with outliers)",
                "x_var": "job_order (1..10)",
                "y_var": col,
                "y_label": label,
            }
        )
        rows.append(row)

        # Cohort-controlled sensitivity fit
        res_coh = regresion_lineal(
            step_ge10["job_order"].values,
            step_ge10[col].values,
            name=f"{col} ~ job_order (cohort >=10 jobs)",
        )
        row_coh = res_coh.to_dict()
        row_coh.update(
            {
                "idea_id": "IDEA-RL-01 (cohort >=10)",
                "dataset_version": "Version A (persons with >=10 jobs)",
                "x_var": "job_order (1..10)",
                "y_var": col,
                "y_label": label,
            }
        )
        rows.append(row_coh)

    summation_skills = build_summation_and_residual_table(
        step_10["job_order"].values,
        step_10["mean_skills"].values,
        models["mean_skills"],
    )

    # Controlled extrapolation audit at k = 11, 12, 15 vs. observed corpus means
    extrap_rows: List[Dict[str, object]] = []
    extrap_ks = [11, 12, 15]
    for col, _ in specs:
        pred_df = predict_ols(models[col], extrap_ks)
        for _, pr in pred_df.iterrows():
            k = int(pr["x"])
            obs_row = step_all.loc[step_all["job_order"] == k]
            obs_val = float(obs_row[col].iloc[0]) if not obs_row.empty else float("nan")
            obs_n = int(obs_row["n_rows"].iloc[0]) if not obs_row.empty else 0
            extrap_rows.append(
                {
                    "y_var": col,
                    "job_order_k": k,
                    "is_extrapolation": bool(pr["is_extrapolation"]),
                    "y_pred_ols": float(pr["y_hat"]),
                    "y_observed": obs_val,
                    "abs_error": abs(obs_val - float(pr["y_hat"])),
                    "observed_n_rows": obs_n,
                }
            )

    return RL01Bundle(
        step_profile=step_all,
        step_profile_ge10=step_ge10,
        ols_summary=pd.DataFrame(rows),
        summation_skills=summation_skills,
        extrapolation_audit=pd.DataFrame(extrap_rows),
        models=models,
    )


def run_rl02_esco_catalog(cfg: NumericalMethodsConfig) -> RL02Bundle:
    """IDEA-RL-02: ESCO ontology & skill-transferability OLS ($n=3,039$) + low-R^2 rejection contrast."""
    catalog, _ = load_esco_catalog_enriched(cfg)

    pairs = [
        ("n_ess_comp", "n_essential", "Essential Skills vs. Essential Practical Competences"),
        ("n_competence", "n_total_rel", "Total Linked Skills vs. Practical Competences"),
        ("n_total_rel", "n_cross_sector", "Cross-Sector Transferable Skills vs. Total Linked Skills"),
        ("n_sector_spec", "n_total_rel", "Total Linked Skills vs. Sector-Specific Skills"),
        ("n_essential", "n_optional", "Optional Skills vs. Essential Skills (Low-R2 Rejection Test)"),
        ("n_essential", "greenShare", "ESCO greenShare vs. Essential Skills (Orthogonality Test)"),
        ("n_knowledge", "greenShare", "ESCO greenShare vs. Knowledge Skills (Orthogonality Test)"),
    ]

    models: Dict[str, OLSResult] = {}
    rows: List[Dict[str, object]] = []
    for x_col, y_col, desc in pairs:
        sub = catalog[[x_col, y_col]].dropna()
        key = f"{y_col}~{x_col}"
        res = regresion_lineal(sub[x_col].values, sub[y_col].values, name=desc)
        models[key] = res
        row = res.to_dict()
        row.update(
            {
                "idea_id": "IDEA-RL-02",
                "dataset_version": "ESCO v1.2.1 + SKILLS + greenShare (3,039 occupations)",
                "x_var": x_col,
                "y_var": y_col,
            }
        )
        rows.append(row)

    # Stratification across the 10 ISCO-08 major groups (transferability law: n_cross_sector ~ n_total_rel)
    isco_rows: List[Dict[str, object]] = []
    for major, grp in catalog.groupby("isco_major"):
        if len(grp) < 5:
            continue
        res_m = regresion_lineal(
            grp["n_total_rel"].values,
            grp["n_cross_sector"].values,
            name=f"ISCO-{major} cross_sector ~ total_rel",
        )
        isco_rows.append(
            {
                "isco_major": major,
                "isco_major_label": str(grp["isco_major_label"].iloc[0]),
                "n_occupations": len(grp),
                "mean_essential": float(grp["n_essential"].mean()),
                "mean_total_rel": float(grp["n_total_rel"].mean()),
                "mean_cross_sector": float(grp["n_cross_sector"].mean()),
                "mean_greenshare": float(grp["greenShare"].mean()),
                "a0": res_m.a0,
                "a1_cross_sector_slope": res_m.a1,
                "r2": res_m.r2,
                "s_yx": res_m.s_yx,
                "quality_verdict": res_m.quality_verdict,
            }
        )
    isco_df = pd.DataFrame(isco_rows).sort_values("isco_major").reset_index(drop=True)

    # 10 ISCO major-group centroids (ideal compact n=10 GeoGebra dataset!)
    cent_res = regresion_lineal(
        isco_df["mean_total_rel"].values,
        isco_df["mean_cross_sector"].values,
        name="ISCO-10 Centroids: mean_cross_sector ~ mean_total_rel",
    )
    models["isco10_centroids"] = cent_res
    cent_row = cent_res.to_dict()
    cent_row.update(
        {
            "idea_id": "IDEA-RL-02 (ISCO-10 centroids)",
            "dataset_version": "ISCO-08 10 Major Groups",
            "x_var": "mean_total_rel",
            "y_var": "mean_cross_sector",
        }
    )
    rows.append(cent_row)

    return RL02Bundle(
        catalog_df=catalog,
        ols_summary=pd.DataFrame(rows),
        isco_major_summary=isco_df,
        isco_centroids=isco_df[["isco_major", "isco_major_label", "mean_total_rel", "mean_cross_sector", "mean_greenshare"]],
        models=models,
    )


def run_rl04_annual_drift(cfg: NumericalMethodsConfig, df_a: pd.DataFrame) -> RL04Bundle:
    """IDEA-RL-04: Annual macro-cohort drift (2000-2019 vs. 2000-2023) + extrapolation & raw split audit."""
    clf = df_a.loc[(df_a["saber_skills"] == "ok") & (df_a["start_year"] >= 2000) & (df_a["start_year"] <= 2023)].copy()
    ann = (
        clf.groupby("start_year", as_index=False)
        .agg(
            n_starts=("resume_id", "size"),
            mean_skills=("n_skills_essential", "mean"),
            mean_knowledge=("n_skills_knowledge", "mean"),
            mean_dur_q=("dur_q", "mean"),
            mean_green=("greenShare", "mean"),
            reincide_rate=("reincide", "mean"),
        )
        .sort_values("start_year")
        .reset_index(drop=True)
    )
    ann["year_centered"] = ann["start_year"] - 2000.0

    ann_valid = ann.loc[ann["start_year"] <= 2019].copy()
    targets = ["mean_skills", "mean_dur_q", "mean_green", "reincide_rate", "n_starts"]

    models: Dict[str, OLSResult] = {}
    rows: List[Dict[str, object]] = []
    for y_col in targets:
        r_valid = regresion_lineal(ann_valid["start_year"].values, ann_valid[y_col].values, name=f"{y_col} (2000-2019)")
        r_full = regresion_lineal(ann["start_year"].values, ann[y_col].values, name=f"{y_col} (2000-2023)")
        # Centered version (t - 2000) for clean GeoGebra verification and intercept readability
        r_cent = regresion_lineal(ann_valid["year_centered"].values, ann_valid[y_col].values, name=f"{y_col} (t-2000, 2000-2019)")

        models[f"{y_col}_2000_2019"] = r_valid
        models[f"{y_col}_2000_2023"] = r_full
        models[f"{y_col}_centered_2000_2019"] = r_cent

        for regime, res, x_name in (
            ("Valid support (2000-2019, n=20)", r_valid, "start_year"),
            ("Censored tail included (2000-2023, n=24)", r_full, "start_year"),
            ("Centered valid (t-2000, n=20)", r_cent, "start_year - 2000"),
        ):
            row = res.to_dict()
            row.update(
                {
                    "idea_id": "IDEA-RL-04",
                    "regime": regime,
                    "x_var": x_name,
                    "y_var": y_col,
                }
            )
            rows.append(row)

    # Extrapolation failure audit: forecast 2020..2027 from 2000-2019 model
    extrap_years = [2020, 2021, 2022, 2023, 2026, 2027]
    extrap_rows: List[Dict[str, object]] = []
    for y_col in ("mean_skills", "mean_dur_q", "mean_green"):
        pred = predict_ols(models[f"{y_col}_2000_2019"], extrap_years)
        for _, pr in pred.iterrows():
            yr = int(pr["x"])
            obs_m = ann.loc[ann["start_year"] == yr]
            obs_val = float(obs_m[y_col].iloc[0]) if not obs_m.empty else float("nan")
            obs_n = int(obs_m["n_starts"].iloc[0]) if not obs_m.empty else 0
            y_hat = float(pr["y_hat"])
            extrap_rows.append(
                {
                    "y_var": y_col,
                    "year": yr,
                    "is_extrapolation": True,
                    "y_pred_from_2000_2019": y_hat,
                    "y_observed": obs_val,
                    "observed_n_starts": obs_n,
                    "physically_invalid": bool((y_col in ("mean_dur_q", "mean_green")) and (y_hat < 0.0)),
                }
            )

    # Raw 01_raw partition parity audit (JobHop_v2_train / test / val annual volume share 2000-2019)
    raw_splits = load_raw_jobhop_years(cfg)
    parity_rows: List[Dict[str, object]] = []
    for split_name, rdf in raw_splits.items():
        sub = rdf.loc[(rdf["start_year"] >= 2000) & (rdf["start_year"] <= 2019)]
        vc = sub.groupby("start_year").size().reset_index(name="n_rows")
        vc["share_pct"] = 100.0 * vc["n_rows"] / vc["n_rows"].sum()
        res_p = regresion_lineal(vc["start_year"].values, vc["share_pct"].values, name=f"{split_name} share_pct ~ year")
        parity_rows.append(
            {
                "raw_file": split_name,
                "total_rows_raw": len(rdf),
                "null_start_date_rows": int(rdf["start_year"].isna().sum()),
                "rows_2000_2019": int(len(sub)),
                "share_slope_pct_per_yr": res_p.a1,
                "share_r2": res_p.r2,
                "polyfit_max_abs_diff": res_p.polyfit_max_abs_diff,
            }
        )

    return RL04Bundle(
        annual_series=ann,
        ols_regime_comparison=pd.DataFrame(rows),
        extrapolation_audit=pd.DataFrame(extrap_rows),
        raw_partition_parity=pd.DataFrame(parity_rows),
        models=models,
    )


def run_rl05_outlier_and_scaling(
    cfg: NumericalMethodsConfig,
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
) -> RL05Bundle:
    """IDEA-RL-05: 4-way outlier audit (A vs B vs Legacy) + 04_transformed affine scale-invariance proof."""
    clf_a = df_a.loc[df_a["saber_skills"] == "ok"]
    clf_b = df_b.loc[df_b["saber_skills"] == "ok"]
    leg_clean, leg_drop = load_legacy_interim_pair(cfg)
    leg_clean_ok = leg_clean.loc[leg_clean["saber_skills"] == "ok"].dropna(
        subset=["n_skills_essential", "n_skills_competence", "n_skills_knowledge"]
    )
    leg_drop_ok = leg_drop.loc[leg_drop["saber_skills"] == "ok"].dropna(
        subset=["n_skills_essential", "n_skills_competence", "n_skills_knowledge"]
    )

    variants = [
        ("Version A · With Outliers (03_processed)", clf_a),
        ("Version B · IQR Winsorized (03_processed)", clf_b),
        ("Legacy Clean · test+val (02_interim/empleos_limpio.csv)", leg_clean_ok),
        ("Legacy Row-Dropped · test+val (02_interim/empleos_limpio_sin_outliers .csv)", leg_drop_ok),
    ]

    out_rows: List[Dict[str, object]] = []
    for x_col, y_col in (
        ("n_skills_competence", "n_skills_essential"),
        ("n_skills_knowledge", "n_skills_essential"),
    ):
        for label, dsub in variants:
            res = regresion_lineal(dsub[x_col].values, dsub[y_col].values, name=f"{label} | {y_col}~{x_col}")
            row = res.to_dict()
            row.update({"idea_id": "IDEA-RL-05", "variant": label, "x_var": x_col, "y_var": y_col})
            out_rows.append(row)

    # Affine scale-invariance verification on 04_transformed dense columns (train & test for both A and B)
    split_map = pd.read_csv(cfg.split_map_path)
    split_lookup = dict(zip(split_map["resume_id"], split_map["split"]))
    scaler_params_a, scaler_src = extract_scaler_params(cfg, "con_outliers")
    scaler_params_b, _ = extract_scaler_params(cfg, "sin_outliers")

    inv_rows: List[Dict[str, object]] = []
    for ver, df_raw, sparams in (
        ("con_outliers", clf_a, scaler_params_a),
        ("sin_outliers", clf_b, scaler_params_b),
    ):
        split_col = df_raw["resume_id"].map(split_lookup)
        for split in ("train", "test"):
            raw_sp = df_raw.loc[split_col == split]
            sc_df = load_transformed_dense_subset(
                cfg,
                version=ver,
                split=split,
                columns=("n_skills_competence_rob", "n_skills_essential_rob", "n_skills_knowledge_rob"),
            )
            for raw_x, raw_y, sc_x, sc_y in (
                ("n_skills_competence", "n_skills_essential", "n_skills_competence_rob", "n_skills_essential_rob"),
                ("n_skills_knowledge", "n_skills_essential", "n_skills_knowledge_rob", "n_skills_essential_rob"),
            ):
                m_raw = regresion_lineal(raw_sp[raw_x].values, raw_sp[raw_y].values, name=f"{ver}/{split} raw")
                m_sc = regresion_lineal(sc_df[sc_x].values, sc_df[sc_y].values, name=f"{ver}/{split} scaled")
                cx, sx = sparams[raw_x]
                cy, sy = sparams[raw_y]
                chk = verify_affine_scaling_invariance(m_raw, m_sc, cx, sx, cy, sy)
                inv_rows.append(
                    {
                        "version": ver,
                        "split": split,
                        "x_var": raw_x,
                        "y_var": raw_y,
                        "n_raw": m_raw.n,
                        "n_scaled": m_sc.n,
                        "center_x": cx,
                        "scale_x": sx,
                        "center_y": cy,
                        "scale_y": sy,
                        "a0_raw": m_raw.a0,
                        "a1_raw": m_raw.a1,
                        "s_yx_raw": m_raw.s_yx,
                        **chk,
                    }
                )

    return RL05Bundle(
        outlier_comparison=pd.DataFrame(out_rows),
        scale_invariance_table=pd.DataFrame(inv_rows),
        scaler_source=scaler_src,
    )
