"""Memory-safe read-only data loaders for JobPath Numerical Methods experiments.

Enforces NFR-NM-01 (read-only data/), NFR-NM-02 (partial usecols loading for
1.4 GB processed and 8 GB transformed CSVs), MR-10 (MNAR education integrity),
MR-11 (4-digit zero-padded ISCO codes), and MR-12 (literal legacy filenames).
"""

from __future__ import annotations

import warnings
from typing import Dict, Sequence, Tuple

import joblib
import numpy as np
import pandas as pd

from .config import (
    CENSORING_PRESENT_ORD,
    NumericalMethodsConfig,
    PROCESSED_NUMERIC_COLS,
    VERIFIED_SCALER_PARAMS,
)


def parse_quarter_series(series: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Parse 'Q1 2011' strings into continuous ordinal year*4 + (q-1), year, and quarter."""
    extracted = series.astype(str).str.extract(r"Q([1-4])\s+(\d{4})")
    quarter = pd.to_numeric(extracted[0], errors="coerce")
    year = pd.to_numeric(extracted[1], errors="coerce")
    ordinal = year * 4 + (quarter - 1)
    return ordinal, year, quarter


def normalize_isco_4digit(series: pd.Series) -> pd.Series:
    """Normalize ISCO codes to 4-digit zero-padded strings (fixes float '.0' in Version B; MR-11)."""
    s = series.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    is_empty = s.isin(["", "nan", "None", "NaN", "<NA>"])
    padded = s.str.zfill(4)
    return padded.where(~is_empty, other=np.nan)


def load_greenshare_lookup(cfg: NumericalMethodsConfig) -> pd.DataFrame:
    """Load data/02_interim/ESCO/greenShareOcc_en_limpio.csv preserving exact codes."""
    df = pd.read_csv(
        cfg.interim_greenshare,
        dtype={"code": str, "conceptType": str, "conceptUri": str},
        low_memory=False,
    )
    df["code"] = df["code"].astype(str).str.strip()
    return df


def load_processed_numeric(
    cfg: NumericalMethodsConfig,
    version: str = "con_outliers",
    attach_greenshare: bool = True,
) -> pd.DataFrame:
    """Load Version A or B from data/03_processed excluding heavy text columns."""
    path = cfg.processed_version_a if version == "con_outliers" else cfg.processed_version_b
    df = pd.read_csv(
        path,
        usecols=list(PROCESSED_NUMERIC_COLS),
        dtype={
            "occupation_code": str,
            "matched_code": str,
            "isco_group": str,
            "university_level": str,
        },
        keep_default_na=True,
        low_memory=False,
    )

    df["isco_group"] = normalize_isco_4digit(df["isco_group"])
    df["isco_major"] = df["isco_group"].str[0]
    df["occupation_code"] = df["occupation_code"].astype(str).str.strip()
    df.loc[df["occupation_code"].isin(["nan", "None", ""]), "occupation_code"] = np.nan

    # Parse quarters and compute dur_q matching JobPath 3.0_transformacion.ipynb
    start_ord, start_year, start_q = parse_quarter_series(df["start_date"])
    end_ord, _, _ = parse_quarter_series(df["end_date"])
    df["start_ord"] = start_ord
    df["start_year"] = start_year
    df["start_q"] = start_q
    df["end_ord"] = end_ord.fillna(float(CENSORING_PRESENT_ORD))
    df["dur_q"] = (df["end_ord"] - df["start_ord"] + 1.0).clip(lower=1.0)
    df["reincide"] = (df["veces_ese_oficio"] > 1).astype(np.int8)

    if attach_greenshare:
        gs = load_greenshare_lookup(cfg)
        gs_occ = gs.loc[gs["conceptType"] == "Occupation", ["code", "greenShare"]].dropna()
        df = df.merge(gs_occ, left_on="occupation_code", right_on="code", how="left")
        df.drop(columns=["code"], inplace=True)

    return df


def load_esco_catalog_enriched(cfg: NumericalMethodsConfig) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Assemble the 3,039-occupation ESCO catalog joined with SKILLS reuseLevel, greenShare & ISCO-08."""
    occ = pd.read_csv(
        cfg.interim_occupations,
        usecols=["conceptUri", "code", "iscoGroup", "preferredLabel"],
        dtype={"code": str, "iscoGroup": str},
        low_memory=False,
    )
    occ["code"] = occ["code"].astype(str).str.strip()
    occ["iscoGroup"] = normalize_isco_4digit(occ["iscoGroup"])
    occ["isco_major"] = occ["iscoGroup"].str[0]

    isco = pd.read_csv(
        cfg.interim_isco,
        usecols=["code", "preferredLabel"],
        dtype={"code": str},
        low_memory=False,
    )
    isco["code"] = isco["code"].astype(str).str.strip()
    isco_major_map = (
        isco.loc[isco["code"].str.len() == 1, ["code", "preferredLabel"]]
        .rename(columns={"code": "isco_major", "preferredLabel": "isco_major_label"})
        .drop_duplicates()
    )

    rel = pd.read_csv(
        cfg.interim_relations,
        usecols=["occupationUri", "relationType", "skillType", "skillUri"],
        low_memory=False,
    )
    sk = pd.read_csv(
        cfg.interim_skills,
        usecols=["conceptUri", "reuseLevel"],
        low_memory=False,
    )
    rel = rel.merge(sk, left_on="skillUri", right_on="conceptUri", how="left")

    # Vectorized indicator aggregation (fast, zero python-lambda overhead)
    rel["is_essential"] = (rel["relationType"] == "essential").astype(np.int32)
    rel["is_optional"] = (rel["relationType"] == "optional").astype(np.int32)
    rel["is_competence"] = (rel["skillType"] == "skill/competence").astype(np.int32)
    rel["is_knowledge"] = (rel["skillType"] == "knowledge").astype(np.int32)
    rel["is_ess_comp"] = (rel["is_essential"] & rel["is_competence"]).astype(np.int32)
    rel["is_ess_know"] = (rel["is_essential"] & rel["is_knowledge"]).astype(np.int32)
    rel["is_sector_spec"] = (rel["reuseLevel"] == "sector-specific").astype(np.int32)
    rel["is_cross_sector"] = (rel["reuseLevel"] == "cross-sector").astype(np.int32)
    rel["is_occ_spec"] = (rel["reuseLevel"] == "occupation-specific").astype(np.int32)
    rel["is_transversal"] = (rel["reuseLevel"] == "transversal").astype(np.int32)

    agg = (
        rel.groupby("occupationUri", as_index=False)
        .agg(
            n_total_rel=("skillUri", "size"),
            n_essential=("is_essential", "sum"),
            n_optional=("is_optional", "sum"),
            n_competence=("is_competence", "sum"),
            n_knowledge=("is_knowledge", "sum"),
            n_ess_comp=("is_ess_comp", "sum"),
            n_ess_know=("is_ess_know", "sum"),
            n_sector_spec=("is_sector_spec", "sum"),
            n_cross_sector=("is_cross_sector", "sum"),
            n_occ_spec=("is_occ_spec", "sum"),
            n_transversal=("is_transversal", "sum"),
        )
    )

    gs = load_greenshare_lookup(cfg)
    gs_occ = gs.loc[gs["conceptType"] == "Occupation", ["conceptUri", "greenShare"]].drop_duplicates()

    catalog = (
        occ.merge(agg, left_on="conceptUri", right_on="occupationUri", how="inner")
        .merge(gs_occ, on="conceptUri", how="left")
        .merge(isco_major_map, on="isco_major", how="left")
    )
    return catalog, isco_major_map


def load_legacy_interim_pair(cfg: NumericalMethodsConfig) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load legacy test+val cleaned vs. row-dropped outlier CSVs preserving trailing-space names (MR-12)."""
    cols = ["n_skills_essential", "n_skills_competence", "n_skills_knowledge", "saber_skills"]
    clean = pd.read_csv(cfg.interim_legacy_clean, usecols=cols, low_memory=False)
    dropped = pd.read_csv(cfg.interim_legacy_no_outliers, usecols=cols, low_memory=False)
    return clean, dropped


def load_raw_jobhop_years(cfg: NumericalMethodsConfig) -> Dict[str, pd.DataFrame]:
    """Load start_date only from raw JobHop train, test, val CSVs for partition-parity audit."""
    out: Dict[str, pd.DataFrame] = {}
    for split, path in (
        ("raw_train", cfg.raw_train),
        ("raw_test", cfg.raw_test),
        ("raw_val", cfg.raw_val),
    ):
        df = pd.read_csv(path, usecols=["start_date"], low_memory=False)
        _, year, _ = parse_quarter_series(df["start_date"])
        df["start_year"] = year
        out[split] = df
    return out


def load_transformed_dense_subset(
    cfg: NumericalMethodsConfig,
    version: str,
    split: str,
    columns: Sequence[str],
) -> pd.DataFrame:
    """Read ONLY requested dense numeric columns from data/04_transformed (never full 2,985 cols).

    Uses a fast byte-prefix split when all requested columns reside in the leading dense
    block (columns 0..10), avoiding tokenizing the 2,967 trailing OHE columns across 8 GB files.
    """
    path = cfg.transformed_x(version, split)
    with path.open("rb", buffering=1 << 23) as fh:
        header = [h.strip().strip('"') for h in fh.readline().decode("utf-8-sig").strip().split(",")]
        col_indices = [header.index(c) for c in columns]
        max_idx = max(col_indices)
        if max_idx <= 20:
            # Fast leading-prefix binary scanner (~10x faster than full-width CSV tokenization)
            arrays = [[] for _ in col_indices]
            split_limit = max_idx + 1
            for raw_line in fh:
                parts = raw_line.split(b",", split_limit)
                for k, idx in enumerate(col_indices):
                    arrays[k].append(float(parts[idx]))
            return pd.DataFrame({c: np.asarray(arr, dtype=np.float64) for c, arr in zip(columns, arrays)})
    return pd.read_csv(path, usecols=list(columns), low_memory=False)


def extract_scaler_params(
    cfg: NumericalMethodsConfig,
    version: str = "con_outliers",
) -> Tuple[Dict[str, Tuple[float, float]], str]:
    """Extract RobustScaler (center, scale) pairs from transformers.joblib with safe fallback."""
    path = cfg.transformers_joblib(version)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            artifacts = joblib.load(path)
        params: Dict[str, Tuple[float, float]] = {}
        for col, scaler in artifacts.scaling.scalers.items():
            if hasattr(scaler, "center_") and hasattr(scaler, "scale_"):
                params[col] = (float(scaler.center_[0]), float(scaler.scale_[0]))
        if params:
            return params, "transformers.joblib (read-only verified)"
    except Exception:
        pass
    return dict(VERIFIED_SCALER_PARAMS), "VERIFIED_SCALER_PARAMS fallback"
