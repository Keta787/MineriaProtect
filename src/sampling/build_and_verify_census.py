"""Reproducible Phase 1 script to build, load, and verify Candidate C (Full Classified Census) in Neon PostgreSQL 18.

Enforces all Phase 1 design requirements:
1. Reads DATA_DIR from .env.local in strictly read-only mode (no NTFS junctions, no modifications to data/).
2. Preserves resume_id as-is (unhashed) and keeps complete person trajectories (352,093 persons / 1,738,738 experiences).
3. Keeps split ('train'/'test') with verified 0 shared persons, K-Means 8.0 labels, and sets cluster_ward_25k_direct
   ONLY for the 25,000 persons in the Ward sample (in_ward_25k_sample = TRUE) and NULL for the remaining 327,093 persons.
4. Loads the normalized ESCO catalog (2,973 occupations) and 12 pre-aggregated summary tables (agg_*) for headline figures.
5. Measures exact physical storage with pg_total_relation_size (including indexes) and real query latencies (cold start +
   warm server execution via EXPLAIN (ANALYZE, BUFFERS) + client RTT), enforcing the Go/No-Go gate (< 600 MB) without
   automatic fallback.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import psycopg
from dotenv import load_dotenv
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestCentroid
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.ScriptsCsv.ClusteringJerarquico.config import V_EXPERIENCE, V_PERSON, VERSION_B
from scripts.ScriptsCsv.ClusteringJerarquico.sampling_and_features import (
    draw_stratified_subsample,
    load_and_prepare_clustering_dataset,
)
from scripts.ScriptsCsv.Transformacion.date_features import add_date_ordinals, add_job_order

SEED = 42
GO_NO_GO_MAX_BYTES = 600 * 1024 * 1024  # 600 MiB hard Go/No-Go cap


def _copy_df_to_postgres(conn: psycopg.Connection, df: pd.DataFrame, table_name: str, columns: List[str]) -> None:
    """Fast bulk load of a DataFrame into PostgreSQL via COPY FROM STDIN WITH CSV."""
    buf = io.StringIO()
    df[columns].to_csv(buf, index=False, header=False, na_rep="\\N")
    buf.seek(0)
    cols_sql = ", ".join(columns)
    copy_sql = f"COPY {table_name} ({cols_sql}) FROM STDIN WITH (FORMAT CSV, NULL '\\N')"
    with conn.cursor() as cur:
        with cur.copy(copy_sql) as copy:
            while chunk := buf.read(1024 * 1024):
                copy.write(chunk)
    conn.commit()


def _njobs_bin(n: int) -> str:
    if n == 1:
        return "1_empleo"
    if n <= 3:
        return "2_3_empleos"
    if n <= 5:
        return "4_5_empleos"
    if n <= 8:
        return "6_8_empleos"
    return "9_mas_empleos"


def build_datasets(data_dir: Path) -> Dict[str, pd.DataFrame]:
    """Build normalized Candidate C tables and 12 aggregate tables from read-only CSVs."""
    t0 = time.perf_counter()
    clean_a_path = data_dir / "03_processed" / "empleos_unificado_limpio.csv"
    clean_b_path = data_dir / "03_processed" / "empleos_limpio_con_competencias_sin_outliers.csv"
    split_map_path = PROJECT_ROOT / "reports" / "eda_jobpath" / "tables" / "split_map_resume_id.csv"

    if not clean_a_path.exists() or not clean_b_path.exists():
        raise FileNotFoundError(f"Missing processed CSV files under DATA_DIR={data_dir}")

    print("[1/5] Loading Version B via official clustering dataset loader (read-only)...")
    ds_b = load_and_prepare_clustering_dataset(
        csv_path=clean_b_path,
        split_map_path=split_map_path,
        version_code=VERSION_B,
    )
    df_exp = ds_b.df_experiences.copy()
    df_per = ds_b.df_persons.copy()

    # Verify zero overlap between Train and Test
    tr_ids = set(df_per.loc[df_per["split"] == "train", "resume_id"])
    te_ids = set(df_per.loc[df_per["split"] == "test", "resume_id"])
    assert len(tr_ids & te_ids) == 0, "Train and Test share persons!"
    assert len(df_per) == 352093, f"Expected 352,093 persons, got {len(df_per)}"
    assert len(df_exp) == 1738738, f"Expected 1,738,738 experiences, got {len(df_exp)}"

    print("[2/5] Reading Version A exact integer skill counts & building ESCO catalog (2,973 occupations)...")
    df_a_raw = pd.read_csv(
        clean_a_path,
        usecols=[
            "resume_id",
            "start_date",
            "end_date",
            "es_vigente",
            "occupation_code",
            "occupation_label",
            "isco_group",
            "isco_group_label",
            "n_skills_essential",
            "n_skills_competence",
            "n_skills_knowledge",
            "n_skills_sin_tipo",
        ],
        low_memory=False,
    )
    df_a_cls = df_a_raw.loc[df_a_raw["occupation_code"].notna()].copy()
    del df_a_raw
    assert len(df_a_cls) == len(df_exp), "Version A and Version B classified row counts differ!"

    # Build ESCO occupations catalog (2,973 unique occupations)
    cat_df = (
        df_a_cls.drop_duplicates("occupation_code")[
            [
                "occupation_code",
                "occupation_label",
                "isco_group",
                "isco_group_label",
                "n_skills_essential",
                "n_skills_competence",
                "n_skills_knowledge",
                "n_skills_sin_tipo",
            ]
        ]
        .copy()
        .sort_values("occupation_code")
        .reset_index(drop=True)
    )
    cat_df["occupation_code"] = cat_df["occupation_code"].astype(str).str.strip()
    cat_df["occupation_label"] = cat_df["occupation_label"].fillna("Sin etiqueta").astype(str).str.strip()
    cat_df["isco_group_code"] = cat_df["isco_group"].astype(int).astype(str).str.zfill(4)
    cat_df["isco_group_label"] = cat_df["isco_group_label"].fillna("Sin grupo ISCO").astype(str).str.strip()
    cat_df["isco_major_1d_zfill"] = cat_df["isco_group_code"].str[0]
    cat_df["n_skills_essential_ref"] = cat_df["n_skills_essential"].round().astype(int)
    cat_df["n_skills_competence_ref"] = cat_df["n_skills_competence"].round().astype(int)
    cat_df["n_skills_knowledge_ref"] = cat_df["n_skills_knowledge"].round().astype(int)
    cat_df["n_skills_sin_tipo_ref"] = cat_df["n_skills_sin_tipo"].fillna(0).round().astype(int)
    esco_catalog = cat_df[
        [
            "occupation_code",
            "occupation_label",
            "isco_group_code",
            "isco_group_label",
            "isco_major_1d_zfill",
            "n_skills_essential_ref",
            "n_skills_competence_ref",
            "n_skills_knowledge_ref",
            "n_skills_sin_tipo_ref",
        ]
    ].copy()
    assert len(esco_catalog) == 2973, f"Expected 2,973 ESCO occupations, got {len(esco_catalog)}"

    print("[3/5] Computing Ward n=25,000 direct vs projected labels & K-Means experience labels...")
    # Load official K-Means 8.0 and Ward 3k projected person assignments
    km_per_path = PROJECT_ROOT / "reports" / "kmeans_jobpath" / "tables" / "08_asignacion_clusters_personas_352093.csv"
    w3k_per_path = (
        PROJECT_ROOT
        / "reports"
        / "clustering_jerarquico_jobpath"
        / "tables"
        / "08_asignacion_clusters_personas_completo_nearest_centroid.csv"
    )
    df_km_full = pd.read_csv(km_per_path)
    df_km_per = df_km_full[["resume_id", "cluster"]].rename(
        columns={"cluster": "cluster_kmeans_8_0"}
    )
    df_w3k_per = pd.read_csv(w3k_per_path, usecols=["resume_id", "cluster"]).rename(
        columns={"cluster": "cluster_ward_3k_projected"}
    )

    # Exact Ward n=25,000 stratified Train sample (seed=42) on the official 8.0/8.1 V_PERSON table
    df_25k = draw_stratified_subsample(
        df=df_km_full,
        n_sample=25000,
        strata_cols=["isco_major_modal_posthoc", "educacion_no_reportada"],
        seed=SEED,
        split_filter="train",
    )
    scaler_25k = StandardScaler()
    X_25k_scaled = np.ascontiguousarray(scaler_25k.fit_transform(df_25k[V_PERSON]), dtype=np.float64)
    Z_25k = linkage(X_25k_scaled, method="ward", metric="euclidean")
    raw_labels_25k = fcluster(Z_25k, t=4, criterion="maxclust") - 1
    del Z_25k

    tmp_25k = df_25k.copy()
    tmp_25k["_cid"] = raw_labels_25k
    m25 = tmp_25k.groupby("_cid").mean(numeric_only=True)
    cids_25 = list(m25.index)
    c1_id = int(m25["educacion_no_reportada"].idxmax())
    rem_25 = [c for c in cids_25 if c != c1_id]
    c3_id = int((m25.loc[rem_25, "span_q"] + m25.loc[rem_25, "dur_mean"] * 2.0).idxmax())
    rem_25 = [c for c in rem_25 if c != c3_id]
    c2_id = int(
        (m25.loc[rem_25, "mean_skills_knowledge"] * 2.0 + m25.loc[rem_25, "nivel_academico_ord_imputado"] * 3.0).idxmax()
    )
    rem_25 = [c for c in rem_25 if c != c2_id]
    c0_id = int(rem_25[0])
    remap_25k = {c0_id: 0, c1_id: 1, c2_id: 2, c3_id: 3}
    labels_25k = pd.Series(raw_labels_25k, index=df_25k.index).map(remap_25k).astype(int)

    nc_25k = NearestCentroid(metric="euclidean")
    nc_25k.fit(X_25k_scaled, labels_25k.to_numpy())
    X_full_scaled = scaler_25k.transform(df_km_full[V_PERSON])
    proj_25k = nc_25k.predict(X_full_scaled).astype(int)

    ward_direct_map = dict(zip(df_25k["resume_id"].to_numpy(), labels_25k.to_numpy()))
    ward_25k_set = set(df_25k["resume_id"].to_numpy())
    assert len(ward_25k_set) == 25000

    # Verify 4 clusters on the 25,000 Ward sample and all 352,093 projected persons
    vc_dir = pd.Series(list(ward_direct_map.values())).value_counts().to_dict()
    vc_proj = pd.Series(proj_25k).value_counts().to_dict()
    print(f"Ward 25k direct cluster counts: {vc_dir} | Projected 352k counts: {vc_proj}")
    assert sum(vc_dir.values()) == 25000 and set(vc_dir.keys()) == {0, 1, 2, 3}
    assert sum(vc_proj.values()) == 352093 and set(vc_proj.keys()) == {0, 1, 2, 3}

    # Compute experience-level K-Means 8.0 labels matching 06_perfiles_completos_y_validacion_posthoc_reincide.csv
    exp_tr_mask = (df_exp["split"] == "train").to_numpy()
    scaler_exp = StandardScaler()
    X_exp_tr = scaler_exp.fit_transform(df_exp.loc[exp_tr_mask, V_EXPERIENCE])
    X_exp_all = scaler_exp.transform(df_exp[V_EXPERIENCE])
    km_exp = KMeans(n_clusters=4, init="k-means++", n_init=10, random_state=SEED)
    km_exp.fit(X_exp_tr)
    raw_exp_labels = km_exp.predict(X_exp_all)

    tmp_e = df_exp.loc[exp_tr_mask, V_EXPERIENCE].copy()
    tmp_e["_cid"] = raw_exp_labels[exp_tr_mask]
    me = tmp_e.groupby("_cid").mean(numeric_only=True)
    ecids = list(me.index)
    ec1 = int(me["educacion_no_reportada"].idxmax())
    erem = [c for c in ecids if c != ec1]
    ec3 = int(me.loc[erem, "dur_q"].idxmax())
    erem = [c for c in erem if c != ec3]
    ec2 = int((me.loc[erem, "n_skills_knowledge"] * 2.0 + me.loc[erem, "nivel_academico_ord_imputado"] * 2.0).idxmax())
    erem = [c for c in erem if c != ec2]
    ec0 = int(erem[0])
    eremap = {ec0: 0, ec1: 1, ec2: 2, ec3: 3}
    exp_km_labels = pd.Series(raw_exp_labels, index=df_exp.index).map(eremap).astype(int)
    vc_exp_km = exp_km_labels.value_counts().to_dict()
    print(f"Experience KMeans cluster counts: {vc_exp_km}")
    assert sum(vc_exp_km.values()) == 1738738 and set(vc_exp_km.keys()) == {0, 1, 2, 3}

    print("[4/5] Assembling person_trajectories (352,093) and person_experiences (1,738,738)...")
    # Derive corrected 1-digit ISCO with leading zero and transition metrics per person
    df_exp["occupation_code"] = df_exp["occupation_code"].astype(str).str.strip()
    df_exp["isco_major_1d_zfill"] = df_exp["isco_group"].astype(int).astype(str).str.zfill(4).str[0]
    df_exp["start_year"] = ((df_exp["start_ord"] - 1) // 4).round().astype(int)
    df_exp["start_quarter"] = (((df_exp["start_ord"] - 1) % 4) + 1).round().astype(int)
    df_exp["end_year"] = ((df_exp["end_ord"] - 1) // 4).round().astype(int)
    df_exp["end_quarter"] = (((df_exp["end_ord"] - 1) % 4) + 1).round().astype(int)
    df_exp["es_vigente"] = df_a_cls["es_vigente"].astype(bool).to_numpy()
    df_exp["n_skills_essential_a"] = df_a_cls["n_skills_essential"].round().astype(int).to_numpy()
    df_exp["n_skills_competence_a"] = df_a_cls["n_skills_competence"].round().astype(int).to_numpy()
    df_exp["n_skills_knowledge_a"] = df_a_cls["n_skills_knowledge"].round().astype(int).to_numpy()
    df_exp["n_skills_essential_b"] = df_exp["n_skills_essential"].round(4)
    df_exp["n_skills_competence_b"] = df_exp["n_skills_competence"].round(4)
    df_exp["n_skills_knowledge_b"] = df_exp["n_skills_knowledge"].round(4)
    df_exp["dur_q_int"] = df_exp["dur_q"].round().astype(int)
    df_exp["job_order_int"] = df_exp["job_order"].round().astype(int)
    df_exp["cluster_exp_kmeans_8_0"] = exp_km_labels.to_numpy()

    # Modal isco_major_1d_zfill per person
    isco_z_counts = (
        df_exp.groupby(["resume_id", "isco_major_1d_zfill"], sort=False)
        .size()
        .reset_index(name="_cnt")
        .sort_values(["resume_id", "_cnt", "isco_major_1d_zfill"], ascending=[True, False, True])
        .drop_duplicates("resume_id")
        .set_index("resume_id")["isco_major_1d_zfill"]
    )
    first_edu = (
        df_exp.sort_values(["resume_id", "job_order_int"])
        .drop_duplicates("resume_id")[["resume_id", "university_level"]]
        .copy()
    )
    first_edu["university_level"] = first_edu["university_level"].fillna("No reportado").astype(str).str.strip()

    # Compute 5.0 typological trajectory segment per person (exploradora, mixta, permanente, sin_transicion)
    df_exp_sorted = df_exp.sort_values(["resume_id", "job_order_int"]).copy()
    df_exp_sorted["prev_resume_id"] = df_exp_sorted["resume_id"].shift(1)
    df_exp_sorted["prev_occ"] = df_exp_sorted["occupation_code"].shift(1)
    df_exp_sorted["is_self_loop"] = (
        (df_exp_sorted["resume_id"] == df_exp_sorted["prev_resume_id"])
        & (df_exp_sorted["occupation_code"] == df_exp_sorted["prev_occ"])
    ).astype(int)
    sl_per_person = df_exp_sorted.groupby("resume_id", sort=False)["is_self_loop"].sum()

    df_per = df_per.merge(df_km_per, on="resume_id", how="left")
    df_per = df_per.merge(df_w3k_per, on="resume_id", how="left")
    df_per = df_per.merge(first_edu, on="resume_id", how="left")
    df_per["isco_major_1d_zfill"] = df_per["resume_id"].map(isco_z_counts).fillna("3")
    df_per["in_ward_25k_sample"] = df_per["resume_id"].isin(ward_25k_set)
    # CRITICAL REQUIREMENT: cluster_ward_25k_direct is ONLY populated for the 25,000 Ward sample persons, NULL otherwise
    df_per["cluster_ward_25k_direct"] = df_per["resume_id"].map(ward_direct_map).astype("Int64")
    df_per["cluster_ward_25k_projected"] = proj_25k
    df_per["sampling_weight"] = 1.0
    df_per["n_jobs_bin"] = df_per["n_jobs"].map(_njobs_bin)
    df_per["n_returns_posthoc"] = (df_per["n_jobs"] - df_per["n_occ_posthoc"]).clip(lower=0).astype(int)
    n_trans_p = (df_per["n_jobs"] - 1).clip(lower=1)
    sl_cnt = df_per["resume_id"].map(sl_per_person).fillna(0).to_numpy()
    sl_share = np.where(df_per["n_jobs"] > 1, sl_cnt / n_trans_p, 0.0)
    nonadj_ret = (df_per["n_returns_posthoc"].to_numpy() - sl_cnt).clip(min=0)
    nonadj_share = np.where(df_per["n_jobs"] > 1, nonadj_ret / n_trans_p, 0.0)

    seg_5_0 = np.full(len(df_per), "mixta", dtype=object)
    seg_5_0[df_per["n_jobs"].to_numpy() == 1] = "sin_transicion"
    is_perm = (df_per["n_jobs"].to_numpy() > 1) & ((sl_share >= 0.166666) | (nonadj_share >= 0.125))
    is_expl = (df_per["n_jobs"].to_numpy() > 1) & (~is_perm) & (df_per["exploration_ratio_posthoc"].to_numpy() >= 1.0)
    seg_5_0[is_perm] = "permanente"
    seg_5_0[is_expl] = "exploradora"
    df_per["trajectory_segment_5_0"] = seg_5_0

    person_trajectories = df_per[
        [
            "resume_id",
            "split",
            "sampling_weight",
            "in_ward_25k_sample",
            "cluster_ward_25k_direct",
            "cluster_ward_25k_projected",
            "cluster_ward_3k_projected",
            "cluster_kmeans_8_0",
            "university_level",
            "nivel_academico_ord_imputado",
            "educacion_no_reportada",
            "isco_major_modal_posthoc",
            "isco_major_1d_zfill",
            "n_jobs",
            "n_jobs_bin",
            "span_q",
            "dur_total",
            "dur_mean",
            "overlap_ratio",
            "mean_skills_essential",
            "mean_skills_competence",
            "mean_skills_knowledge",
            "mean_prop_competence",
            "n_occ_posthoc",
            "n_returns_posthoc",
            "any_repeated_posthoc",
            "tasa_reincide_persona_posthoc",
            "trajectory_segment_5_0",
        ]
    ].copy()
    person_trajectories["educacion_no_reportada"] = person_trajectories["educacion_no_reportada"].round().astype(int)

    person_experiences = (
        df_exp[
            [
                "resume_id",
                "job_order_int",
                "split",
                "start_year",
                "start_quarter",
                "end_year",
                "end_quarter",
                "dur_q_int",
                "es_vigente",
                "occupation_code",
                "isco_major_1d_zfill",
                "n_skills_essential_a",
                "n_skills_competence_a",
                "n_skills_knowledge_a",
                "n_skills_essential_b",
                "n_skills_competence_b",
                "n_skills_knowledge_b",
                "reincide",
                "cluster_exp_kmeans_8_0",
            ]
        ]
        .rename(columns={"job_order_int": "job_order", "dur_q_int": "dur_q"})
        .sort_values(["resume_id", "job_order"])
        .reset_index(drop=True)
    )

    print("[5/5] Building the 12 pre-aggregated census tables (agg_*)...")
    # 1. agg_inclusion_exclusion_funnel
    agg_funnel = pd.DataFrame(
        [
            {
                "stage_order": 1,
                "stage_code": "raw_jobhop_v2",
                "stage_label_es": "1. Universo crudo JobHop v2 (train + test + val)",
                "status_in_neon": "UPSTREAM_RAW",
                "experiences_count": 1993291,
                "persons_count": 355315,
                "pct_clean_experiences": 106.5353,
                "pct_clean_persons": 100.0020,
                "reason_es": "Unión íntegra de las 3 particiones crudas de Hugging Face (0 personas solapadas).",
            },
            {
                "stage_order": 2,
                "stage_code": "removed_in_cleaning_stages_1_to_5",
                "stage_label_es": "2. Removidos en limpieza física (sin fechas, año > 2026, duplicados y variantes de cierre)",
                "status_in_neon": "EXCLUDED_CLEANING",
                "experiences_count": 122277,
                "persons_count": 7,
                "pct_clean_experiences": 6.5353,
                "pct_clean_persons": 0.0020,
                "reason_es": "72,726 sin fechas + 11 con año > 2026 + 37,553 duplicados exactos + 11,987 variantes parciales de cierre.",
            },
            {
                "stage_order": 3,
                "stage_code": "clean_master_dataset",
                "stage_label_es": "3. Dataset maestro limpio (03_processed Versiones A y B)",
                "status_in_neon": "CLEAN_REFERENCE",
                "experiences_count": 1871014,
                "persons_count": 355308,
                "pct_clean_experiences": 100.0000,
                "pct_clean_persons": 100.0000,
                "reason_es": "Base limpia tras deduplicación, rescate jerárquico de 9,293 filas y winsorización IQR sin borrar filas.",
            },
            {
                "stage_order": 4,
                "stage_code": "excluded_esco_unknown",
                "stage_label_es": "4a. Excluidos del censo modelable: ocupación no identificada (emparejado = 'unknown')",
                "status_in_neon": "EXCLUDED_NO_ESCO",
                "experiences_count": 128981,
                "persons_count": 3132,
                "pct_clean_experiences": 6.8936,
                "pct_clean_persons": 0.8815,
                "reason_es": "Sin código ESCO ni grupo ISCO; imposible asignar competencias sin inventar ceros espurios (Decisión D05/D07).",
            },
            {
                "stage_order": 5,
                "stage_code": "excluded_esco_rescatado_no_leaf",
                "stage_label_es": "4b. Excluidos del censo modelable: solo grupo ISCO de 4 dígitos sin oficio hoja ESCO ('rescatado')",
                "status_in_neon": "EXCLUDED_NO_ESCO",
                "experiences_count": 3295,
                "persons_count": 83,
                "pct_clean_experiences": 0.1761,
                "pct_clean_persons": 0.0234,
                "reason_es": "Tienen grupo ISCO pero carecen de oficio hoja en occupations_en.csv y de perfil de competencias.",
            },
            {
                "stage_order": 6,
                "stage_code": "included_classified_census_total",
                "stage_label_es": "5. CENSO CLASIFICADO INCLUIDO EN NEON (Candidato C · 100 % del universo modelable)",
                "status_in_neon": "INCLUDED_CENSUS",
                "experiences_count": 1738738,
                "persons_count": 352093,
                "pct_clean_experiences": 92.9302,
                "pct_clean_persons": 99.0952,
                "reason_es": "Universo completo con oficio ESCO válido (±0.0000 pp error muestral, 100 % de transiciones preservadas).",
            },
            {
                "stage_order": 7,
                "stage_code": "census_split_train",
                "stage_label_es": "6a. Partición Train en Neon (80.00 % de personas clasificadas · GroupShuffleSplit seed=42)",
                "status_in_neon": "INCLUDED_TRAIN",
                "experiences_count": 1391018,
                "persons_count": 281674,
                "pct_clean_experiences": 74.3457,
                "pct_clean_persons": 79.2760,
                "reason_es": "Ajuste de escaladores, OHE, clasificadores (6.0–7.2) y centroides K-Means (8.0). 0 personas compartidas con Test.",
            },
            {
                "stage_order": 8,
                "stage_code": "census_split_test",
                "stage_label_es": "6b. Partición Test en Neon (20.00 % de personas clasificadas · Retenida out-of-sample)",
                "status_in_neon": "INCLUDED_TEST",
                "experiences_count": 347720,
                "persons_count": 70419,
                "pct_clean_experiences": 18.5846,
                "pct_clean_persons": 19.8191,
                "reason_es": "Evaluación final sin fuga de todos los modelos supervisados y validación post-hoc de clústeres.",
            },
            {
                "stage_order": 9,
                "stage_code": "ward_25k_direct_subsample",
                "stage_label_es": "7a. Submuestra directa Ward Jerárquico (in_ward_25k_sample = TRUE · cluster_ward_25k_direct IS NOT NULL)",
                "status_in_neon": "WARD_DIRECT_ONLY",
                "experiences_count": int(len(df_exp.loc[df_exp["resume_id"].isin(ward_25k_set)])),
                "persons_count": 25000,
                "pct_clean_experiences": round(len(df_exp.loc[df_exp["resume_id"].isin(ward_25k_set)]) / 1871014 * 100, 4),
                "pct_clean_persons": round(25000 / 355308 * 100, 4),
                "reason_es": "Muestra estratificada de Train (7.10 % del censo) donde se ajustó directamente el dendrograma Ward (2.50 GB RAM).",
            },
            {
                "stage_order": 10,
                "stage_code": "outside_ward_25k_subsample",
                "stage_label_es": "7b. Personas fuera de la muestra directa Ward (in_ward_25k_sample = FALSE · cluster_ward_25k_direct IS NULL)",
                "status_in_neon": "WARD_NULL_DIRECT",
                "experiences_count": int(1738738 - len(df_exp.loc[df_exp["resume_id"].isin(ward_25k_set)])),
                "persons_count": 327093,
                "pct_clean_experiences": round(
                    (1738738 - len(df_exp.loc[df_exp["resume_id"].isin(ward_25k_set)])) / 1871014 * 100, 4
                ),
                "pct_clean_persons": round(327093 / 355308 * 100, 4),
                "reason_es": "327,093 personas (92.90 % del censo) donde Ward no se ajustó directamente por límite O(n^2) de 495.9 GB RAM.",
            },
        ]
    )

    # 2. agg_cleaning_and_iqr_audit
    agg_clean = pd.read_csv(data_dir / "03_processed" / "Limpio" / "bitacora_limpieza_unificado.csv")

    # 3. agg_pca_variance_and_loadings
    agg_pca = pd.DataFrame(
        [
            {"notebook": "4.0_PCA (10k)", "version": "Version A (con_outliers)", "pc": "PC1", "var_exp_pct": 32.9837, "cum_var_pct": 32.9837, "k_for_80pct": 4, "k_for_90pct": 5},
            {"notebook": "4.0_PCA (10k)", "version": "Version A (con_outliers)", "pc": "PC2", "var_exp_pct": 22.8199, "cum_var_pct": 55.8037, "k_for_80pct": 4, "k_for_90pct": 5},
            {"notebook": "4.0_PCA (10k)", "version": "Version A (con_outliers)", "pc": "PC3", "var_exp_pct": 21.4099, "cum_var_pct": 77.2136, "k_for_80pct": 4, "k_for_90pct": 5},
            {"notebook": "4.0_PCA (10k)", "version": "Version A (con_outliers)", "pc": "PC4", "var_exp_pct": 10.6173, "cum_var_pct": 87.8309, "k_for_80pct": 4, "k_for_90pct": 5},
            {"notebook": "4.0_PCA (10k)", "version": "Version A (con_outliers)", "pc": "PC5", "var_exp_pct": 6.2208, "cum_var_pct": 94.0517, "k_for_80pct": 4, "k_for_90pct": 5},
            {"notebook": "4.1_PCA_completo (50k)", "version": "Version A (con_outliers)", "pc": "PC1", "var_exp_pct": 32.9105, "cum_var_pct": 32.9105, "k_for_80pct": 4, "k_for_90pct": 5},
            {"notebook": "4.1_PCA_completo (50k)", "version": "Version A (con_outliers)", "pc": "PC2", "var_exp_pct": 22.4498, "cum_var_pct": 55.3603, "k_for_80pct": 4, "k_for_90pct": 5},
            {"notebook": "4.1_PCA_completo (50k)", "version": "Version A (con_outliers)", "pc": "PC3", "var_exp_pct": 21.2274, "cum_var_pct": 76.5877, "k_for_80pct": 4, "k_for_90pct": 5},
            {"notebook": "4.1_PCA_completo (50k)", "version": "Version A (con_outliers)", "pc": "PC4", "var_exp_pct": 11.1727, "cum_var_pct": 87.7604, "k_for_80pct": 4, "k_for_90pct": 5},
            {"notebook": "4.1_PCA_completo (50k)", "version": "Version A (con_outliers)", "pc": "PC5", "var_exp_pct": 6.3052, "cum_var_pct": 94.0656, "k_for_80pct": 4, "k_for_90pct": 5},
            {"notebook": "4.1_PCA_completo (50k)", "version": "Version B (sin_outliers)", "pc": "PC1", "var_exp_pct": 39.6820, "cum_var_pct": 39.6820, "k_for_80pct": 3, "k_for_90pct": 5},
            {"notebook": "4.1_PCA_completo (50k)", "version": "Version B (sin_outliers)", "pc": "PC2", "var_exp_pct": 26.2107, "cum_var_pct": 65.8927, "k_for_80pct": 3, "k_for_90pct": 5},
            {"notebook": "4.1_PCA_completo (50k)", "version": "Version B (sin_outliers)", "pc": "PC3", "var_exp_pct": 14.6922, "cum_var_pct": 80.5850, "k_for_80pct": 3, "k_for_90pct": 5},
            {"notebook": "4.1_PCA_completo (50k)", "version": "Version B (sin_outliers)", "pc": "PC4", "var_exp_pct": 8.5042, "cum_var_pct": 89.0892, "k_for_80pct": 3, "k_for_90pct": 5},
            {"notebook": "4.1_PCA_completo (50k)", "version": "Version B (sin_outliers)", "pc": "PC5", "var_exp_pct": 6.2706, "cum_var_pct": 95.3598, "k_for_80pct": 3, "k_for_90pct": 5},
        ]
    )

    # 4. agg_eda_distributions_and_segments
    seg_summary = (
        person_trajectories.groupby("trajectory_segment_5_0", as_index=False)
        .agg(
            persons_count=("resume_id", "size"),
            mean_n_jobs=("n_jobs", "mean"),
            mean_n_occ=("n_occ_posthoc", "mean"),
            mean_n_returns=("n_returns_posthoc", "mean"),
            mean_span_q=("span_q", "mean"),
            any_repeated_rate_pct=("any_repeated_posthoc", lambda s: float(s.mean() * 100.0)),
        )
        .sort_values("persons_count", ascending=False)
    )
    seg_summary["pct_persons"] = (seg_summary["persons_count"] / len(person_trajectories) * 100.0).round(4)

    # 5. agg_top_occupation_transitions (Top 100 consecutive transitions across 1,386,645 transitions)
    df_exp_sorted["next_resume_id"] = df_exp_sorted["resume_id"].shift(-1)
    df_exp_sorted["next_occ_code"] = df_exp_sorted["occupation_code"].shift(-1)
    trans_df = df_exp_sorted.loc[df_exp_sorted["resume_id"] == df_exp_sorted["next_resume_id"]].copy()
    occ_label_map = dict(zip(esco_catalog["occupation_code"], esco_catalog["occupation_label"]))
    top_trans = (
        trans_df.groupby(["occupation_code", "next_occ_code"], as_index=False)
        .size()
        .rename(columns={"occupation_code": "from_occupation_code", "next_occ_code": "to_occupation_code", "size": "transition_count"})
        .sort_values("transition_count", ascending=False)
        .head(100)
        .reset_index(drop=True)
    )
    top_trans["rank_order"] = np.arange(1, len(top_trans) + 1)
    top_trans["from_occupation_label"] = top_trans["from_occupation_code"].map(occ_label_map)
    top_trans["to_occupation_label"] = top_trans["to_occupation_code"].map(occ_label_map)
    top_trans["is_self_loop"] = top_trans["from_occupation_code"] == top_trans["to_occupation_code"]
    top_trans["pct_of_all_transitions"] = (top_trans["transition_count"] / len(trans_df) * 100.0).round(4)

    # 6–12. Load official report CSVs for supervised models, clustering, and numerical methods
    agg_sup = pd.read_csv(PROJECT_ROOT / "reports" / "knn_jobpath" / "tables" / "13g_comparacion_unificada_version_a.csv")
    agg_dt = pd.read_csv(
        PROJECT_ROOT / "reports" / "arbol_decision_jobpath" / "tables" / "07_comparacion_tres_arboles_referencias_y_versiones.csv"
    )
    agg_nb_isco = pd.read_csv(
        PROJECT_ROOT / "reports" / "naive_bayes_jobpath" / "tables" / "10_o1_tasas_reincidencia_isco_1d.csv"
    )
    agg_knn_geom = pd.read_csv(
        PROJECT_ROOT / "reports" / "knn_jobpath" / "tables" / "03_geometria_contraste_y_pureza_vecinos.csv"
    )
    agg_clus_exec = pd.read_csv(
        PROJECT_ROOT
        / "reports"
        / "clustering_jerarquico_jobpath"
        / "tables"
        / "13_matriz_ejecutiva_comparativa_8_0_vs_8_1.csv"
    )
    agg_nm_rl04 = pd.read_csv(
        PROJECT_ROOT
        / "numerical_methods_presentation"
        / "case_01_RL04_annual_drift_extrapolation"
        / "tables"
        / "rl04_annual_macro_series.csv"
    )
    agg_nm_rl04_ols = pd.read_csv(
        PROJECT_ROOT
        / "numerical_methods_presentation"
        / "case_01_RL04_annual_drift_extrapolation"
        / "tables"
        / "rl04_ols_regime_comparison.csv"
    )
    agg_nm_rl04_ext = pd.read_csv(
        PROJECT_ROOT
        / "numerical_methods_presentation"
        / "case_01_RL04_annual_drift_extrapolation"
        / "tables"
        / "rl04_extrapolation_failure_audit.csv"
    )
    agg_nm_lg01 = pd.read_csv(
        PROJECT_ROOT
        / "numerical_methods_presentation"
        / "case_02_LG01_survival_and_runge"
        / "tables"
        / "lg01_survival_curve_S_q.csv"
    )
    agg_nm_lg01_p3 = pd.read_csv(
        PROJECT_ROOT
        / "numerical_methods_presentation"
        / "case_02_LG01_survival_and_runge"
        / "tables"
        / "lg01_milestone_P3_weights_and_eval.csv"
    )
    agg_nm_lg01_runge = pd.read_csv(
        PROJECT_ROOT
        / "numerical_methods_presentation"
        / "case_02_LG01_survival_and_runge"
        / "tables"
        / "lg01_runge_phenomenon_benchmark.csv"
    )
    agg_km_prof = pd.read_csv(
        PROJECT_ROOT
        / "reports"
        / "kmeans_jobpath"
        / "tables"
        / "06_perfiles_completos_y_validacion_posthoc_reincide.csv"
    )
    agg_w25k_prof = pd.read_csv(
        PROJECT_ROOT
        / "reports"
        / "clustering_jerarquico_jobpath"
        / "tables"
        / "12_perfiles_ward_n25000_escala_original.csv"
    )

    print(f"Datasets built in {time.perf_counter() - t0:.2f} s.")
    return {
        "esco_occupations_catalog": esco_catalog,
        "person_trajectories": person_trajectories,
        "person_experiences": person_experiences,
        "agg_inclusion_exclusion_funnel": agg_funnel,
        "agg_cleaning_and_iqr_audit": agg_clean,
        "agg_pca_variance_and_loadings": agg_pca,
        "agg_eda_distributions_and_segments": seg_summary,
        "agg_top_occupation_transitions": top_trans,
        "agg_supervised_models_benchmark": agg_sup,
        "agg_decision_trees_comparison": agg_dt,
        "agg_naive_bayes_isco_rates": agg_nb_isco,
        "agg_knn_neighbor_purity": agg_knn_geom,
        "agg_clustering_executive_comparison": agg_clus_exec,
        "agg_kmeans_full_profiles": agg_km_prof,
        "agg_ward_25k_profiles": agg_w25k_prof,
        "agg_nm_rl04_annual_macro": agg_nm_rl04,
        "agg_nm_rl04_ols_regimes": agg_nm_rl04_ols,
        "agg_nm_rl04_extrapolation_audit": agg_nm_rl04_ext,
        "agg_nm_lg01_survival_curve": agg_nm_lg01,
        "agg_nm_lg01_p3_milestones": agg_nm_lg01_p3,
        "agg_nm_lg01_runge_benchmark": agg_nm_lg01_runge,
    }


def _sanitize_col(c: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_]", "_", str(c).strip().lower())
    s = re.sub(r"_+", "_", s).strip("_")
    if not s or s[0].isdigit():
        s = "col_" + s
    return s


def create_and_load_generic_agg_table(conn: psycopg.Connection, table_name: str, df: pd.DataFrame) -> None:
    """Create and load a compact aggregate table from a DataFrame."""
    df_clean = df.copy()
    df_clean.columns = [_sanitize_col(c) for c in df_clean.columns]
    col_defs = []
    for c in df_clean.columns:
        dt = df_clean[c].dtype
        if pd.api.types.is_bool_dtype(dt):
            col_defs.append(f"{c} BOOLEAN")
        elif pd.api.types.is_integer_dtype(dt):
            col_defs.append(f"{c} BIGINT")
        elif pd.api.types.is_float_dtype(dt):
            col_defs.append(f"{c} DOUBLE PRECISION")
        else:
            col_defs.append(f"{c} TEXT")
    ddl = f"DROP TABLE IF EXISTS {table_name} CASCADE; CREATE TABLE {table_name} ({', '.join(col_defs)});"
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()
    _copy_df_to_postgres(conn, df_clean, table_name, list(df_clean.columns))


def _load_phase2_extra_agg_tables() -> Dict[str, pd.DataFrame]:
    """Load the 6 small numerical-methods and clustering profile aggregate CSVs directly (< 0.1 s)."""
    return {
        "agg_kmeans_full_profiles": pd.read_csv(
            PROJECT_ROOT / "reports" / "kmeans_jobpath" / "tables" / "06_perfiles_completos_y_validacion_posthoc_reincide.csv"
        ),
        "agg_ward_25k_profiles": pd.read_csv(
            PROJECT_ROOT
            / "reports"
            / "clustering_jerarquico_jobpath"
            / "tables"
            / "12_perfiles_ward_n25000_escala_original.csv"
        ),
        "agg_nm_rl04_ols_regimes": pd.read_csv(
            PROJECT_ROOT
            / "numerical_methods_presentation"
            / "case_01_RL04_annual_drift_extrapolation"
            / "tables"
            / "rl04_ols_regime_comparison.csv"
        ),
        "agg_nm_rl04_extrapolation_audit": pd.read_csv(
            PROJECT_ROOT
            / "numerical_methods_presentation"
            / "case_01_RL04_annual_drift_extrapolation"
            / "tables"
            / "rl04_extrapolation_failure_audit.csv"
        ),
        "agg_nm_lg01_p3_milestones": pd.read_csv(
            PROJECT_ROOT
            / "numerical_methods_presentation"
            / "case_02_LG01_survival_and_runge"
            / "tables"
            / "lg01_milestone_P3_weights_and_eval.csv"
        ),
        "agg_nm_lg01_runge_benchmark": pd.read_csv(
            PROJECT_ROOT
            / "numerical_methods_presentation"
            / "case_02_LG01_survival_and_runge"
            / "tables"
            / "lg01_runge_phenomenon_benchmark.csv"
        ),
    }


EXPECTED_TABLE_ROWS: Dict[str, int] = {
    "person_experiences": 1738738,
    "person_trajectories": 352093,
    "esco_occupations_catalog": 2973,
    "agg_top_occupation_transitions": 100,
    "agg_nm_lg01_survival_curve": 40,
    "agg_nm_rl04_annual_macro": 24,
    "agg_nm_rl04_extrapolation_audit": 18,
    "agg_pca_variance_and_loadings": 15,
    "agg_supervised_models_benchmark": 15,
    "agg_decision_trees_comparison": 15,
    "agg_nm_rl04_ols_regimes": 15,
    "agg_nm_lg01_runge_benchmark": 15,
    "agg_knn_neighbor_purity": 11,
    "agg_inclusion_exclusion_funnel": 10,
    "agg_naive_bayes_isco_rates": 10,
    "agg_cleaning_and_iqr_audit": 8,
    "agg_kmeans_full_profiles": 8,
    "agg_nm_lg01_p3_milestones": 7,
    "agg_eda_distributions_and_segments": 4,
    "agg_clustering_executive_comparison": 4,
    "agg_ward_25k_profiles": 4,
}


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env.local")
    data_dir_str = os.environ.get("DATA_DIR")
    db_url = os.environ.get("DATABASE_URL_DIRECT") or os.environ.get("DATABASE_URL")
    ro_url = os.environ.get("DATABASE_URL_READONLY_DIRECT") or os.environ.get("DATABASE_URL_READONLY")
    if not data_dir_str or not db_url:
        raise RuntimeError("Missing DATA_DIR or DATABASE_URL in .env.local")

    verify_only = "--verify-only" in sys.argv
    finalize_phase2 = "--finalize-phase2" in sys.argv
    load_seconds = 104.89
    cold_connect_ms = 1616.69

    if finalize_phase2:
        extra_aggs = _load_phase2_extra_agg_tables()
        with psycopg.connect(db_url) as conn:
            for tname, tdf in extra_aggs.items():
                print(f"Loading Phase 2 aggregate table {tname} ({len(tdf)} rows)...")
                create_and_load_generic_agg_table(conn, tname, tdf)
            with conn.cursor() as cur:
                print("Ensuring explicit FOREIGN KEY constraints and read-only privileges for jobpath_readonly...")
                cur.execute(
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_constraint WHERE conname = 'fk_pe_person'
                        ) THEN
                            ALTER TABLE person_experiences
                                ADD CONSTRAINT fk_pe_person
                                FOREIGN KEY (resume_id) REFERENCES person_trajectories (resume_id);
                        END IF;
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_constraint WHERE conname = 'fk_pe_occupation'
                        ) THEN
                            ALTER TABLE person_experiences
                                ADD CONSTRAINT fk_pe_occupation
                                FOREIGN KEY (occupation_code) REFERENCES esco_occupations_catalog (occupation_code);
                        END IF;
                    END $$;

                    GRANT CONNECT ON DATABASE neondb TO jobpath_readonly;
                    GRANT USAGE ON SCHEMA public TO jobpath_readonly;
                    GRANT SELECT ON ALL TABLES IN SCHEMA public TO jobpath_readonly;
                    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO jobpath_readonly;
                    REVOKE CREATE ON SCHEMA public FROM jobpath_readonly;
                    """
                )
            conn.commit()
    elif not verify_only:
        data_dir = Path(data_dir_str)
        tables = build_datasets(data_dir)

        # Measure initial connection latency (potentially cold start if compute was suspended)
        t_conn0 = time.perf_counter()
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
        cold_connect_ms = round((time.perf_counter() - t_conn0) * 1000.0, 2)
        print(f"Initial Neon connection + SELECT 1 latency: {cold_connect_ms} ms")

        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                print("Creating core normalized tables (esco_occupations_catalog, person_trajectories, person_experiences)...")
                cur.execute(
                    """
                    DROP TABLE IF EXISTS person_experiences CASCADE;
                    DROP TABLE IF EXISTS person_trajectories CASCADE;
                    DROP TABLE IF EXISTS esco_occupations_catalog CASCADE;

                    CREATE TABLE esco_occupations_catalog (
                        occupation_code VARCHAR(16) PRIMARY KEY,
                        occupation_label VARCHAR(160) NOT NULL,
                        isco_group_code CHAR(4) NOT NULL,
                        isco_group_label VARCHAR(160) NOT NULL,
                        isco_major_1d_zfill CHAR(1) NOT NULL,
                        n_skills_essential_ref SMALLINT NOT NULL,
                        n_skills_competence_ref SMALLINT NOT NULL,
                        n_skills_knowledge_ref SMALLINT NOT NULL,
                        n_skills_sin_tipo_ref SMALLINT NOT NULL
                    );

                    CREATE TABLE person_trajectories (
                        resume_id INTEGER PRIMARY KEY,
                        split VARCHAR(5) NOT NULL,
                        sampling_weight REAL NOT NULL DEFAULT 1.0,
                        in_ward_25k_sample BOOLEAN NOT NULL,
                        cluster_ward_25k_direct SMALLINT NULL,
                        cluster_ward_25k_projected SMALLINT NOT NULL,
                        cluster_ward_3k_projected SMALLINT NOT NULL,
                        cluster_kmeans_8_0 SMALLINT NOT NULL,
                        university_level VARCHAR(20) NOT NULL,
                        nivel_academico_ord_imputado REAL NOT NULL,
                        educacion_no_reportada SMALLINT NOT NULL,
                        isco_major_modal_posthoc CHAR(1) NOT NULL,
                        isco_major_1d_zfill CHAR(1) NOT NULL,
                        n_jobs SMALLINT NOT NULL,
                        n_jobs_bin VARCHAR(16) NOT NULL,
                        span_q REAL NOT NULL,
                        dur_total REAL NOT NULL,
                        dur_mean REAL NOT NULL,
                        overlap_ratio REAL NOT NULL,
                        mean_skills_essential REAL NOT NULL,
                        mean_skills_competence REAL NOT NULL,
                        mean_skills_knowledge REAL NOT NULL,
                        mean_prop_competence REAL NOT NULL,
                        n_occ_posthoc SMALLINT NOT NULL,
                        n_returns_posthoc SMALLINT NOT NULL,
                        any_repeated_posthoc SMALLINT NOT NULL,
                        tasa_reincide_persona_posthoc REAL NOT NULL,
                        trajectory_segment_5_0 VARCHAR(16) NOT NULL
                    );

                    CREATE TABLE person_experiences (
                        resume_id INTEGER NOT NULL,
                        job_order SMALLINT NOT NULL,
                        split VARCHAR(5) NOT NULL,
                        start_year SMALLINT NOT NULL,
                        start_quarter SMALLINT NOT NULL,
                        end_year SMALLINT NOT NULL,
                        end_quarter SMALLINT NOT NULL,
                        dur_q SMALLINT NOT NULL,
                        es_vigente BOOLEAN NOT NULL,
                        occupation_code VARCHAR(16) NOT NULL,
                        isco_major_1d_zfill CHAR(1) NOT NULL,
                        n_skills_essential_a SMALLINT NOT NULL,
                        n_skills_competence_a SMALLINT NOT NULL,
                        n_skills_knowledge_a SMALLINT NOT NULL,
                        n_skills_essential_b REAL NOT NULL,
                        n_skills_competence_b REAL NOT NULL,
                        n_skills_knowledge_b REAL NOT NULL,
                        reincide SMALLINT NOT NULL,
                        cluster_exp_kmeans_8_0 SMALLINT NOT NULL,
                        PRIMARY KEY (resume_id, job_order)
                    );
                    """
                )
            conn.commit()

            t_load0 = time.perf_counter()
            print("Bulk loading esco_occupations_catalog (2,973 rows)...")
            _copy_df_to_postgres(
                conn,
                tables["esco_occupations_catalog"],
                "esco_occupations_catalog",
                list(tables["esco_occupations_catalog"].columns),
            )

            print("Bulk loading person_trajectories (352,093 rows)...")
            _copy_df_to_postgres(
                conn,
                tables["person_trajectories"],
                "person_trajectories",
                list(tables["person_trajectories"].columns),
            )

            print("Bulk loading person_experiences (1,738,738 rows)...")
            _copy_df_to_postgres(
                conn,
                tables["person_experiences"],
                "person_experiences",
                list(tables["person_experiences"].columns),
            )

            for tname, tdf in tables.items():
                if tname.startswith("agg_"):
                    print(f"Loading aggregate table {tname} ({len(tdf)} rows)...")
                    create_and_load_generic_agg_table(conn, tname, tdf)

            print("Creating secondary B-tree indexes for dashboard filter queries...")
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE INDEX idx_pt_split_km_isco_edu
                        ON person_trajectories (split, cluster_kmeans_8_0, isco_major_1d_zfill, university_level);
                    CREATE INDEX idx_pt_ward25k
                        ON person_trajectories (in_ward_25k_sample, cluster_ward_25k_direct)
                        WHERE in_ward_25k_sample = TRUE;
                    CREATE INDEX idx_pe_occ_split
                        ON person_experiences (occupation_code, split);
                    """
                )
            conn.commit()
            load_seconds = round(time.perf_counter() - t_load0, 2)
            print(f"All tables and indexes loaded in {load_seconds} s.")

    # Run VACUUM ANALYZE in autocommit mode so pg_total_relation_size and query plans are 100% accurate
    with psycopg.connect(db_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            if not verify_only or finalize_phase2:
                print("Running VACUUM ANALYZE...")
                cur.execute("VACUUM ANALYZE;")

            # Measure exact storage sizes
            cur.execute(
                """
                SELECT
                    c.relname AS table_name,
                    s.n_live_tup AS row_count,
                    pg_table_size(c.oid) AS table_bytes,
                    pg_indexes_size(c.oid) AS index_bytes,
                    pg_total_relation_size(c.oid) AS total_bytes,
                    pg_size_pretty(pg_total_relation_size(c.oid)) AS total_pretty
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                LEFT JOIN pg_stat_user_tables s ON s.relid = c.oid
                WHERE n.nspname = 'public' AND c.relkind = 'r'
                ORDER BY pg_total_relation_size(c.oid) DESC;
                """
            )
            size_rows = cur.fetchall()
            cur.execute("SELECT pg_database_size(current_database()), pg_size_pretty(pg_database_size(current_database()));")
            db_bytes, db_pretty = cur.fetchone()

            # Inventory all indexes in public schema
            cur.execute(
                """
                SELECT tablename, indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname;
                """
            )
            index_rows = [
                {"table_name": str(r[0]), "index_name": str(r[1]), "index_def": str(r[2])}
                for r in cur.fetchall()
            ]

            # Inventory foreign key constraints and check referential integrity
            cur.execute(
                """
                SELECT conname, convalidated
                FROM pg_constraint
                WHERE contype = 'f'
                ORDER BY conname;
                """
            )
            fk_rows = [{"constraint_name": str(r[0]), "validated": bool(r[1])} for r in cur.fetchall()]

            cur.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM person_experiences e LEFT JOIN person_trajectories p ON p.resume_id = e.resume_id WHERE p.resume_id IS NULL) AS orphan_persons,
                    (SELECT COUNT(*) FROM person_experiences e LEFT JOIN esco_occupations_catalog c ON c.occupation_code = e.occupation_code WHERE c.occupation_code IS NULL) AS orphan_occupations;
                """
            )
            orphan_p, orphan_occ = cur.fetchone()

            # Verify Ward 25k NULL constraint and Train/Test zero overlap inside Postgres
            cur.execute(
                """
                SELECT
                    COUNT(*) AS total_persons,
                    COUNT(*) FILTER (WHERE split = 'train') AS train_persons,
                    COUNT(*) FILTER (WHERE split = 'test') AS test_persons,
                    COUNT(*) FILTER (WHERE in_ward_25k_sample = TRUE) AS ward_sample_true,
                    COUNT(*) FILTER (WHERE cluster_ward_25k_direct IS NOT NULL) AS ward_direct_non_null,
                    COUNT(*) FILTER (WHERE in_ward_25k_sample = FALSE AND cluster_ward_25k_direct IS NOT NULL) AS invalid_ward_outside_sample
                FROM person_trajectories;
                """
            )
            pt_audit = cur.fetchone()

            cur.execute("SELECT COUNT(*) FROM person_experiences;")
            pe_count = cur.fetchone()[0]

            # Benchmark real dashboard queries (server execution time from EXPLAIN ANALYZE + client RTT)
            queries = [
                (
                    "Q1_headline_inclusion_exclusion_funnel",
                    "SELECT * FROM agg_inclusion_exclusion_funnel ORDER BY stage_order;",
                ),
                (
                    "Q2_headline_supervised_models_benchmark",
                    "SELECT * FROM agg_supervised_models_benchmark;",
                ),
                (
                    "Q3_headline_clustering_executive",
                    "SELECT * FROM agg_clustering_executive_comparison;",
                ),
                (
                    "Q4_headline_numerical_methods_rl04_lg01",
                    "SELECT * FROM agg_nm_rl04_annual_macro ORDER BY start_year;",
                ),
                (
                    "Q5_explorer_filtered_trajectories_limit50",
                    """
                    SELECT resume_id, split, cluster_kmeans_8_0, cluster_ward_25k_direct, university_level,
                           isco_major_1d_zfill, n_jobs, span_q, dur_mean, tasa_reincide_persona_posthoc
                    FROM person_trajectories
                    WHERE split = 'test' AND cluster_kmeans_8_0 = 0 AND isco_major_1d_zfill = '5'
                    ORDER BY resume_id
                    LIMIT 50;
                    """,
                ),
                (
                    "Q6_explorer_single_person_timeline_join_esco",
                    """
                    SELECT e.resume_id, e.job_order, e.start_year, e.start_quarter, e.end_year, e.end_quarter,
                           e.dur_q, e.es_vigente, e.occupation_code, c.occupation_label, c.isco_group_label,
                           e.n_skills_essential_a, e.n_skills_competence_a, e.n_skills_knowledge_a, e.reincide
                    FROM person_experiences e
                    JOIN esco_occupations_catalog c ON c.occupation_code = e.occupation_code
                    WHERE e.resume_id = 47
                    ORDER BY e.job_order;
                    """,
                ),
                (
                    "Q7_explorer_ward_25k_only_filter_limit50",
                    """
                    SELECT resume_id, cluster_ward_25k_direct, cluster_kmeans_8_0, n_jobs, span_q, dur_mean
                    FROM person_trajectories
                    WHERE in_ward_25k_sample = TRUE AND cluster_ward_25k_direct = 2
                    LIMIT 50;
                    """,
                ),
            ]

            latency_results = []
            for qname, qsql in queries:
                cur.execute(qsql)
                cur.fetchall()
                t_q0 = time.perf_counter()
                cur.execute(qsql)
                rows_ret = cur.fetchall()
                rtt_ms = round((time.perf_counter() - t_q0) * 1000.0, 2)
                cur.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {qsql}")
                plan_json = cur.fetchone()[0][0]
                exec_ms = round(float(plan_json.get("Execution Time", 0.0)), 3)
                plan_ms = round(float(plan_json.get("Planning Time", 0.0)), 3)
                node_type = plan_json.get("Plan", {}).get("Node Type", "Unknown")
                latency_results.append(
                    {
                        "query_name": qname,
                        "rows_returned": len(rows_ret),
                        "server_execution_ms": exec_ms,
                        "server_planning_ms": plan_ms,
                        "client_rtt_ms": rtt_ms,
                        "top_plan_node": node_type,
                    }
                )

    # Verify read-only role jobpath_readonly (connect with DATABASE_URL_READONLY)
    ro_audit: Dict[str, Any] = {}
    if ro_url:
        print("Verifying least-privilege read-only role (jobpath_readonly)...")
        with psycopg.connect(ro_url, autocommit=True) as ro_conn:
            with ro_conn.cursor() as rcur:
                rcur.execute(
                    """
                    SELECT
                        current_user,
                        r.rolsuper,
                        pg_has_role(current_user, 'neon_superuser', 'MEMBER') AS is_neon_superuser,
                        has_schema_privilege(current_user, 'public', 'CREATE') AS can_create_in_public,
                        has_schema_privilege(current_user, 'public', 'USAGE') AS can_usage_public
                    FROM pg_roles r
                    WHERE r.rolname = current_user;
                    """
                )
                cu, is_sup, is_nsup, can_cr, can_us = rcur.fetchone()
                ro_audit["current_user"] = str(cu)
                ro_audit["rolsuper"] = bool(is_sup)
                ro_audit["is_neon_superuser"] = bool(is_nsup)
                ro_audit["can_create_in_public"] = bool(can_cr)
                ro_audit["can_usage_public"] = bool(can_us)

                # Verify exact row counts across all 21 tables as jobpath_readonly
                row_parity: Dict[str, Dict[str, Any]] = {}
                all_counts_match = True
                for tname, exp_cnt in EXPECTED_TABLE_ROWS.items():
                    rcur.execute(f"SELECT COUNT(*) FROM {tname};")
                    act_cnt = int(rcur.fetchone()[0])
                    matched = act_cnt == exp_cnt
                    if not matched:
                        all_counts_match = False
                    row_parity[tname] = {"expected": exp_cnt, "actual": act_cnt, "pass": matched}
                ro_audit["all_21_tables_readable_and_exact_row_parity"] = all_counts_match
                ro_audit["table_row_parity"] = row_parity

                # Negative write tests (all must raise InsufficientPrivilege)
                neg_tests = [
                    ("deny_insert", "INSERT INTO agg_inclusion_exclusion_funnel (stage_order) VALUES (999);"),
                    ("deny_update", "UPDATE person_trajectories SET n_jobs = 0 WHERE resume_id = 1;"),
                    ("deny_delete", "DELETE FROM person_experiences WHERE resume_id = 1 AND job_order = 1;"),
                    ("deny_create_table", "CREATE TABLE public.unauthorized_test (id INT);"),
                    ("deny_drop_table", "DROP TABLE agg_inclusion_exclusion_funnel;"),
                ]
                neg_results = {}
                for tlabel, tsql in neg_tests:
                    try:
                        rcur.execute(tsql)
                        neg_results[tlabel] = {"blocked": False, "error": "UNEXPECTED_SUCCESS"}
                    except psycopg.errors.InsufficientPrivilege as exc:
                        neg_results[tlabel] = {"blocked": True, "error": type(exc).__name__}
                ro_audit["negative_write_tests"] = neg_results
                ro_audit["all_writes_blocked"] = all(v["blocked"] for v in neg_results.values())

    total_tables_bytes = sum(int(r[4]) for r in size_rows)
    total_tables_mib = round(total_tables_bytes / (1024 * 1024), 2)
    db_mib = round(int(db_bytes) / (1024 * 1024), 2)
    go_storage = total_tables_bytes < GO_NO_GO_MAX_BYTES and int(db_bytes) < GO_NO_GO_MAX_BYTES
    max_agg_exec_ms = max(r["server_execution_ms"] for r in latency_results if r["query_name"].startswith("Q1") or r["query_name"].startswith("Q2") or r["query_name"].startswith("Q3") or r["query_name"].startswith("Q4"))
    max_exp_exec_ms = max(r["server_execution_ms"] for r in latency_results if r["query_name"].startswith("Q5") or r["query_name"].startswith("Q6") or r["query_name"].startswith("Q7"))
    go_latency = (cold_connect_ms <= 2500.0) and (max_agg_exec_ms <= 15.0) and (max_exp_exec_ms <= 25.0)

    report_payload: Dict[str, Any] = {
        "candidate": "C (Full Classified Census: 352,093 persons / 1,738,738 experiences)",
        "go_no_go_verdict": "GO" if (go_storage and go_latency) else "NO-GO",
        "go_storage_under_600mb": go_storage,
        "go_latency_passed": go_latency,
        "load_seconds": load_seconds,
        "cold_connect_ms": cold_connect_ms,
        "total_user_tables_count": len(size_rows),
        "total_indexes_count": len(index_rows),
        "total_user_tables_bytes": total_tables_bytes,
        "total_user_tables_mib": total_tables_mib,
        "pg_database_size_bytes": int(db_bytes),
        "pg_database_size_mib": db_mib,
        "pg_database_size_pretty": db_pretty,
        "pct_of_1gib_limit": round(db_mib / 1024.0 * 100.0, 2),
        "referential_integrity": {
            "foreign_keys": fk_rows,
            "orphan_person_experiences_to_persons": int(orphan_p),
            "orphan_person_experiences_to_esco_catalog": int(orphan_occ),
            "pass": (int(orphan_p) == 0 and int(orphan_occ) == 0 and len(fk_rows) == 2),
        },
        "person_trajectories_audit": {
            "total_persons": int(pt_audit[0]),
            "train_persons": int(pt_audit[1]),
            "test_persons": int(pt_audit[2]),
            "ward_sample_true": int(pt_audit[3]),
            "ward_direct_non_null": int(pt_audit[4]),
            "invalid_ward_outside_sample": int(pt_audit[5]),
        },
        "person_experiences_count": int(pe_count),
        "readonly_role_audit": ro_audit,
        "indexes": index_rows,
        "table_sizes": [
            {
                "table_name": str(r[0]),
                "row_count": int(r[1] or 0),
                "table_bytes": int(r[2]),
                "index_bytes": int(r[3]),
                "total_bytes": int(r[4]),
                "total_mib": round(int(r[4]) / (1024 * 1024), 3),
                "total_pretty": str(r[5]),
            }
            for r in size_rows
        ],
        "query_latencies": latency_results,
    }

    out_json = Path(
        r"C:\Users\User\.gemini\antigravity\brain\c1534532-02c0-49ac-ad0f-8540f7d0b357\scratch\neon_census_verification.json"
    )
    out_json.write_text(json.dumps(report_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Verification JSON written to {out_json}")
    print(f"GO/NO-GO VERDICT: {report_payload['go_no_go_verdict']} | Total tables+indexes: {total_tables_mib} MiB | DB size: {db_mib} MiB")


if __name__ == "__main__":
    main()
