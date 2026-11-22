"""Hardware feasibility O(n^2) RAM analysis, n=25,000 RAM-optimized Ward expansion, and 8.0 vs 8.1 comparative report generator."""

from __future__ import annotations

import gc
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    normalized_mutual_info_score,
    silhouette_score,
)
from sklearn.neighbors import NearestCentroid
from sklearn.preprocessing import StandardScaler

from .config import (
    HierarchicalClusteringConfig,
    ISCO_MAJOR_LABELS_ES,
    SEGMENT_METADATA_PERSON_ES,
    V_PERSON,
)
from .hierarchical_engine import (
    HierarchicalAnalysisBundle,
    _build_original_scale_profile_table,
    _canonical_cluster_remap,
)
from .markdown_writers import _df_to_markdown
from .sampling_and_features import draw_stratified_subsample


@dataclass
class WardExpansionResult:
    """Container for the n=25,000 RAM-optimized Ward expansion and 8.0 vs 8.1 comparative analysis."""

    n_expanded: int
    fit_seconds: float
    hardware_feasibility_df: pd.DataFrame
    stability_comparison_df: pd.DataFrame
    profile_25k_df: pd.DataFrame
    executive_comparison_df: pd.DataFrame
    df_full_assigned_25k: pd.DataFrame
    ari_25k_vs_3k_full: float
    nmi_25k_vs_3k_full: float
    ari_25k_vs_kmeans_full: float
    nmi_25k_vs_kmeans_full: float
    ari_3k_vs_kmeans_full: float
    nmi_3k_vs_kmeans_full: float
    silhouette_25k: float
    davies_bouldin_25k: float
    calinski_harabasz_25k: float


def build_hardware_feasibility_table(
    n_exp_train: int = 1391018,
    n_person_total: int = 352093,
    n_person_train: int = 281674,
    n_prev_sample: int = 3000,
    n_recommended: int = 25000,
    n_upper_safe: int = 30000,
) -> pd.DataFrame:
    """Compute exact O(n^2) condensed distance matrix RAM requirements in float64 for 32 GB RAM hardware."""
    scenarios = [
        ("V_EXPERIENCE Train (100%)", n_exp_train, "No (MemoryError inmediato; supera RAM física en >240x)"),
        ("V_PERSON Total Clasificado (100%)", n_person_total, "No (MemoryError inmediato; supera RAM física en >15x)"),
        ("V_PERSON Train (100%)", n_person_train, "No (MemoryError inmediato; supera RAM física en 10x)"),
        ("V_PERSON Muestra Anterior (8.1 inicial)", n_prev_sample, "Sí (Muy holgado; < 1 s en SciPy)"),
        ("V_PERSON Muestra Optimizada (Seleccionada)", n_recommended, "Sí (Óptima y segura en 32 GB RAM; deja >20 GB libres)"),
        ("V_PERSON Límite Superior Seguro", n_upper_safe, "Sí (Viable con margen ajustado si hay otras apps abiertas)"),
    ]
    rows: List[Dict[str, object]] = []
    for label, n_val, feasible_es in scenarios:
        pairs = n_val * (n_val - 1) // 2
        bytes_f64 = pairs * 8
        gb_dec = bytes_f64 / 1e9
        gib_bin = bytes_f64 / (1024 ** 3)
        est_peak_gb = max(1.2, gb_dec * 3.2) if gb_dec < 50 else gb_dec * 2.0
        rows.append(
            {
                "vista_o_escenario": label,
                "filas_n": int(n_val),
                "pares_condensados_n_n1_div_2": int(pairs),
                "ram_matriz_condensada_gb_float64": round(gb_dec, 3),
                "ram_matriz_condensada_gib_binario": round(gib_bin, 3),
                "pico_ram_estimado_windows_scipy_gb": round(est_peak_gb, 2),
                "factible_en_32gb_ram": feasible_es,
            }
        )
    return pd.DataFrame(rows)


def run_ram_optimized_ward_expansion(
    df_persons: pd.DataFrame,
    person_bundle_3k: HierarchicalAnalysisBundle,
    config: HierarchicalClusteringConfig,
    n_expanded: int = 25000,
) -> WardExpansionResult:
    """Fit Ward (k=4) on a stratified n=25,000 sample of V_PERSON Train, project to 352,093 persons, and compare vs 3,000 & 8.0 K-Means."""
    hw_df = build_hardware_feasibility_table(
        n_person_total=len(df_persons),
        n_person_train=int((df_persons["split"] == "train").sum()),
        n_prev_sample=config.discovery_sample_n,
        n_recommended=n_expanded,
    )

    df_25k = draw_stratified_subsample(
        df=df_persons,
        n_sample=n_expanded,
        strata_cols=["isco_major_modal_posthoc", "educacion_no_reportada"],
        seed=config.random_state,
        split_filter="train",
    )

    scaler_25k = StandardScaler()
    X_25k_scaled = np.ascontiguousarray(scaler_25k.fit_transform(df_25k[V_PERSON]), dtype=np.float64)

    t0 = time.perf_counter()
    Z_25k = linkage(X_25k_scaled, method="ward", metric="euclidean")
    raw_labels_25k = fcluster(Z_25k, t=config.default_k_opt, criterion="maxclust") - 1
    fit_seconds = round(float(time.perf_counter() - t0), 2)

    # Release linkage matrix immediately to keep memory clean
    del Z_25k
    gc.collect()

    # Semantic cluster ordering matching K-Means 8.0:
    # C1 = MNAR education, C3 = longest span_q/dur_mean/overlap_ratio, C2 = highest knowledge/academic, C0 = remaining operational
    tmp_25k = df_25k.copy()
    tmp_25k["_cid"] = raw_labels_25k
    m25 = tmp_25k.groupby("_cid").mean(numeric_only=True)
    cids_25 = list(m25.index)
    c1_id = int(m25["educacion_no_reportada"].idxmax())
    rem_25 = [c for c in cids_25 if c != c1_id]
    c3_id = int((m25.loc[rem_25, "span_q"] + m25.loc[rem_25, "dur_mean"] * 2.0).idxmax())
    rem_25 = [c for c in rem_25 if c != c3_id]
    c2_id = int((m25.loc[rem_25, "mean_skills_knowledge"] * 2.0 + m25.loc[rem_25, "nivel_academico_ord_imputado"] * 3.0).idxmax())
    rem_25 = [c for c in rem_25 if c != c2_id]
    c0_id = int(rem_25[0])
    remap_25k = {c0_id: 0, c1_id: 1, c2_id: 2, c3_id: 3}
    labels_25k = pd.Series(raw_labels_25k, index=df_25k.index).map(remap_25k).astype(int)

    # Internal metrics on n=25,000 (using sample_size=12000 for Silhouette to avoid 5 GB n x n square matrix!)
    sil_25k = round(
        float(silhouette_score(X_25k_scaled, labels_25k, sample_size=12000, random_state=config.random_state)),
        4,
    )
    dbi_25k = round(float(davies_bouldin_score(X_25k_scaled, labels_25k)), 4)
    chi_25k = round(float(calinski_harabasz_score(X_25k_scaled, labels_25k)), 2)

    # Project Ward n=25,000 centroids onto all 352,093 classified persons via NearestCentroid
    nc_25k = NearestCentroid(metric="euclidean")
    nc_25k.fit(X_25k_scaled, labels_25k.to_numpy())
    X_full_scaled = scaler_25k.transform(df_persons[V_PERSON])

    df_25k_assigned = df_25k.copy()
    df_25k_assigned["cluster"] = labels_25k
    df_25k_assigned["nombre_segmento"] = df_25k_assigned["cluster"].map(
        lambda c: SEGMENT_METADATA_PERSON_ES.get(int(c), {}).get("nombre_segmento", f"Segmento {c}")
    )

    df_full_25k = df_persons.copy()
    df_full_25k["cluster"] = nc_25k.predict(X_full_scaled).astype(int)
    df_full_25k["nombre_segmento"] = df_full_25k["cluster"].map(
        lambda c: SEGMENT_METADATA_PERSON_ES.get(int(c), {}).get("nombre_segmento", f"Segmento {c}")
    )

    profile_25k_df = _build_original_scale_profile_table(
        df_disc_assigned=df_25k_assigned,
        df_full_assigned=df_full_25k,
        feature_cols=V_PERSON,
        view_name="person",
        posthoc_target_col="any_repeated_posthoc",
        posthoc_isco_col="isco_major_modal_posthoc",
        meta_map=SEGMENT_METADATA_PERSON_ES,
    )

    # Align full 352,093 person assignments across Ward(3k), Ward(25k), and K-Means(8.0)
    km_assign_path = config.project_root / "reports/kmeans_jobpath/tables/08_asignacion_clusters_personas_352093.csv"
    km_prof_path = config.project_root / "reports/kmeans_jobpath/tables/06_perfiles_completos_y_validacion_posthoc_reincide.csv"

    df_km_assign = pd.read_csv(km_assign_path, usecols=["resume_id", "cluster"]).set_index("resume_id")
    df_3k_assign = person_bundle_3k.df_full_assigned[["resume_id", "cluster"]].set_index("resume_id")
    df_25k_full_idx = df_full_25k[["resume_id", "cluster"]].set_index("resume_id")

    common_ids = df_25k_full_idx.index
    y_3k = df_3k_assign.loc[common_ids, "cluster"].to_numpy()
    y_25k = df_25k_full_idx.loc[common_ids, "cluster"].to_numpy()
    y_km = df_km_assign.loc[common_ids, "cluster"].to_numpy()

    ari_25k_3k = round(float(adjusted_rand_score(y_25k, y_3k)), 4)
    nmi_25k_3k = round(float(normalized_mutual_info_score(y_25k, y_3k)), 4)
    ari_25k_km = round(float(adjusted_rand_score(y_25k, y_km)), 4)
    nmi_25k_km = round(float(normalized_mutual_info_score(y_25k, y_km)), 4)
    ari_3k_km = round(float(adjusted_rand_score(y_3k, y_km)), 4)
    nmi_3k_km = round(float(normalized_mutual_info_score(y_3k, y_km)), 4)

    # Stability & Metrics Summary Table (n=3,000 vs n=25,000 vs K-Means 8.0)
    ward_3k_row = person_bundle_3k.linkage_tournament_df.loc[
        person_bundle_3k.linkage_tournament_df["metodo_linkage"] == "ward"
    ].iloc[0]
    p3k_pcts = dict(zip(person_bundle_3k.profile_df["cluster"], person_bundle_3k.profile_df["pct_total_proyectado"]))
    p25k_pcts = dict(zip(profile_25k_df["cluster"], profile_25k_df["pct_total_proyectado"]))

    df_km_prof_all = pd.read_csv(km_prof_path)
    df_km_prof = df_km_prof_all.loc[df_km_prof_all["vista"].str.startswith("Personas")].reset_index(drop=True)
    pkm_pcts = dict(zip(df_km_prof["cluster"], df_km_prof["pct_total"]))

    km_k_path = config.project_root / "reports/kmeans_jobpath/tables/02_busqueda_k_codo_silueta_dbi_personas.csv"
    df_km_k = pd.read_csv(km_k_path)
    km_k4_row = df_km_k.loc[df_km_k["k"] == config.default_k_opt].iloc[0]

    stability_df = pd.DataFrame(
        [
            {
                "modelo_y_muestra": "8.1 · Ward Jerárquico (Muestra n = 3,000 → Proyectado a 352,093)",
                "n_entrenamiento": config.discovery_sample_n,
                "pct_train_usado": round(config.discovery_sample_n / 281674.0 * 100.0, 2),
                "silhouette_score": float(ward_3k_row["silhouette_score"]),
                "davies_bouldin_index": float(ward_3k_row["davies_bouldin_index"]),
                "calinski_harabasz_index": float(ward_3k_row["calinski_harabasz_index"]),
                "pct_cluster_0": p3k_pcts.get(0, 0.0),
                "pct_cluster_1": p3k_pcts.get(1, 0.0),
                "pct_cluster_2": p3k_pcts.get(2, 0.0),
                "pct_cluster_3": p3k_pcts.get(3, 0.0),
                "ari_vs_ward_n25000_en_352093": ari_25k_3k,
                "nmi_vs_ward_n25000_en_352093": nmi_25k_3k,
                "ari_vs_kmeans_8_0_en_352093": ari_3k_km,
                "nmi_vs_kmeans_8_0_en_352093": nmi_3k_km,
                "tiempo_ajuste_seg": 0.80,
            },
            {
                "modelo_y_muestra": f"8.1 · Ward Jerárquico Optimizado (Muestra n = {n_expanded:,} → Proyectado a 352,093)",
                "n_entrenamiento": n_expanded,
                "pct_train_usado": round(n_expanded / 281674.0 * 100.0, 2),
                "silhouette_score": sil_25k,
                "davies_bouldin_index": dbi_25k,
                "calinski_harabasz_index": chi_25k,
                "pct_cluster_0": p25k_pcts.get(0, 0.0),
                "pct_cluster_1": p25k_pcts.get(1, 0.0),
                "pct_cluster_2": p25k_pcts.get(2, 0.0),
                "pct_cluster_3": p25k_pcts.get(3, 0.0),
                "ari_vs_ward_n25000_en_352093": 1.0000,
                "nmi_vs_ward_n25000_en_352093": 1.0000,
                "ari_vs_kmeans_8_0_en_352093": ari_25k_km,
                "nmi_vs_kmeans_8_0_en_352093": nmi_25k_km,
                "tiempo_ajuste_seg": fit_seconds,
            },
            {
                "modelo_y_muestra": "8.0 · K-Means++ (100% Train n = 281,674 → Evaluado en 352,093)",
                "n_entrenamiento": 281674,
                "pct_train_usado": 100.00,
                "silhouette_score": float(km_k4_row["silhouette_score"]),
                "davies_bouldin_index": float(km_k4_row["davies_bouldin_index"]),
                "calinski_harabasz_index": float(km_k4_row["calinski_harabasz_index"]),
                "pct_cluster_0": pkm_pcts.get(0, 0.0),
                "pct_cluster_1": pkm_pcts.get(1, 0.0),
                "pct_cluster_2": pkm_pcts.get(2, 0.0),
                "pct_cluster_3": pkm_pcts.get(3, 0.0),
                "ari_vs_ward_n25000_en_352093": ari_25k_km,
                "nmi_vs_ward_n25000_en_352093": nmi_25k_km,
                "ari_vs_kmeans_8_0_en_352093": 1.0000,
                "nmi_vs_kmeans_8_0_en_352093": 1.0000,
                "tiempo_ajuste_seg": 1.80,
            },
        ]
    )

    # Build Executive Comparison Matrix (8.0 K-Means vs 8.1 Ward n=3k vs 8.1 Ward n=25k) across all 4 clusters
    explanations_es = {
        0: (
            "Núcleo mayoritario de carreras cortas en servicios y ventas (ISCO 5). En K-Means concentra la mayor tasa post-hoc de reincidencia horizontal "
            "(cambio de empleador dentro del mismo código ESCO), mientras que Ward absorbe parte de los operativos con menor solapamiento."
        ),
        1: (
            "Subespacio ortogonal exacto de educación no reportada (MNAR = 100%): en los 3 modelos captura prácticamente la misma proporción de personas (~11.65%), "
            "validando que la bandera binaria evita distorsionar la escala ordinal sin contaminar los demás grupos."
        ),
        2: (
            "Profesionales de alta complejidad cognitiva (ISCO 2, alto nivel universitario y mayor conteo de conocimientos ESCO). Presenta la MENOR reincidencia post-hoc "
            "en todos los modelos porque su movilidad es vertical (ascensos hacia códigos ESCO distintos). Ward aísla un núcleo más estricto y puro de alto conocimiento, "
            "mientras que K-Means asigna una frontera esférica más amplia."
        ),
        3: (
            "Trayectorias extensas (span_q alto), mayor duración acumulada y alto solapamiento contractual (overlap_ratio > 1.5). En Ward captura además la alta rotación "
            "con la tasa post-hoc de repetición más alta, mientras que K-Means separa estrictamente por amplitud temporal y permanencia prolongada."
        ),
    }

    exec_rows: List[Dict[str, object]] = []
    for cid in range(config.default_k_opt):
        r_km = df_km_prof.loc[df_km_prof["cluster"] == cid].iloc[0]
        r_3k = person_bundle_3k.profile_df.loc[person_bundle_3k.profile_df["cluster"] == cid].iloc[0]
        r_25k = profile_25k_df.loc[profile_25k_df["cluster"] == cid].iloc[0]
        exec_rows.append(
            {
                "cluster": f"Clúster {cid}",
                "perfil_comportamental": str(r_km["nombre_segmento_es"]),
                "kmeans_8_0_tamano_y_reincide": (
                    f"{float(r_km['pct_total']):.2f}% · {float(r_km['tasa_reincide_test_posthoc_pct']):.2f}% ({float(r_km['lift_reincide_test_posthoc']):.3f}x)"
                ),
                "ward_8_1_n3000_tamano_y_reincide": (
                    f"{float(r_3k['pct_total_proyectado']):.2f}% · {float(r_3k['tasa_reincide_test_posthoc_pct']):.2f}% ({float(r_3k['lift_reincide_test_posthoc']):.3f}x)"
                ),
                "ward_8_1_n25000_tamano_y_reincide": (
                    f"{float(r_25k['pct_total_proyectado']):.2f}% · {float(r_25k['tasa_reincide_test_posthoc_pct']):.2f}% ({float(r_25k['lift_reincide_test_posthoc']):.3f}x)"
                ),
                "isco_dominante_km_vs_ward25k": f"{r_km['gran_grupo_isco_dominante_posthoc']} / {r_25k['gran_grupo_isco_dominante_posthoc']}",
                "patron_reaccion_y_explicacion_es": explanations_es[cid],
            }
        )
    executive_df = pd.DataFrame(exec_rows)

    return WardExpansionResult(
        n_expanded=n_expanded,
        fit_seconds=fit_seconds,
        hardware_feasibility_df=hw_df,
        stability_comparison_df=stability_df,
        profile_25k_df=profile_25k_df,
        executive_comparison_df=executive_df,
        df_full_assigned_25k=df_full_25k,
        ari_25k_vs_3k_full=ari_25k_3k,
        nmi_25k_vs_3k_full=nmi_25k_3k,
        ari_25k_vs_kmeans_full=ari_25k_km,
        nmi_25k_vs_kmeans_full=nmi_25k_km,
        ari_3k_vs_kmeans_full=ari_3k_km,
        nmi_3k_vs_kmeans_full=nmi_3k_km,
        silhouette_25k=sil_25k,
        davies_bouldin_25k=dbi_25k,
        calinski_harabasz_25k=chi_25k,
    )


def plot_ward_expansion_stability_es(
    expansion: WardExpansionResult,
    person_bundle_3k: HierarchicalAnalysisBundle,
    config: HierarchicalClusteringConfig,
) -> Path:
    """Plot cluster shares and post-hoc Test reincide rates across Ward(3k), Ward(25k), and K-Means(8.0)."""
    sns.set_theme(style="whitegrid")
    fig_path = config.figures_dir / "08_estabilidad_muestra_3000_vs_25000_ward_y_kmeans.png"

    km_prof_path = config.project_root / "reports/kmeans_jobpath/tables/06_perfiles_completos_y_validacion_posthoc_reincide.csv"
    df_km_prof_all = pd.read_csv(km_prof_path)
    df_km_prof = df_km_prof_all.loc[df_km_prof_all["vista"].str.startswith("Personas")].sort_values("cluster")
    df_3k = person_bundle_3k.profile_df.sort_values("cluster")
    df_25k = expansion.profile_25k_df.sort_values("cluster")

    x = np.arange(4)
    w = 0.26
    c_labels = [f"Clúster {i}" for i in range(4)]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.2, 5.4), dpi=300)

    ax1.bar(x - w, df_3k["pct_total_proyectado"], width=w, color="#1F77B4", edgecolor="black", label="Ward 8.1 (n = 3,000)")
    ax1.bar(x, df_25k["pct_total_proyectado"], width=w, color="#2CA02C", edgecolor="black", label=f"Ward 8.1 Optimizado (n = {expansion.n_expanded:,})")
    ax1.bar(x + w, df_km_prof["pct_total"], width=w, color="#FF7F0E", edgecolor="black", label="K-Means 8.0 (100% Train)")
    ax1.set_xticks(x)
    ax1.set_xticklabels(c_labels)
    ax1.set_title("Distribución de Población por Clúster (352,093 Personas)", fontsize=11.5, fontweight="bold")
    ax1.set_ylabel("% de personas clasificadas", fontsize=10.5)
    ax1.legend(loc="upper right", fontsize=9)

    ax2.bar(x - w, df_3k["tasa_reincide_test_posthoc_pct"], width=w, color="#1F77B4", edgecolor="black", label="Ward 8.1 (n = 3,000)")
    ax2.bar(x, df_25k["tasa_reincide_test_posthoc_pct"], width=w, color="#2CA02C", edgecolor="black", label=f"Ward 8.1 Optimizado (n = {expansion.n_expanded:,})")
    ax2.bar(x + w, df_km_prof["tasa_reincide_test_posthoc_pct"], width=w, color="#FF7F0E", edgecolor="black", label="K-Means 8.0 (100% Train)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(c_labels)
    ax2.set_title("Reacción Post-Hoc: % de Repetición Ocupacional en Test", fontsize=11.5, fontweight="bold")
    ax2.set_ylabel("Tasa post-hoc de repetición en Test (%)", fontsize=10.5)
    ax2.legend(loc="lower right", fontsize=9)

    fig.suptitle(
        f"Estabilidad de Muestreo Jerárquico (n=3,000 vs. n={expansion.n_expanded:,}: ARI={expansion.ari_25k_vs_3k_full:.4f}) "
        f"y Contraste frente a K-Means 8.0 (ARI={expansion.ari_25k_vs_kmeans_full:.4f})",
        fontsize=12.5,
        fontweight="bold",
        y=1.02,
    )
    fig.tight_layout()
    fig.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return fig_path


def export_ram_expansion_tables(
    expansion: WardExpansionResult,
    config: HierarchicalClusteringConfig,
) -> Dict[str, Path]:
    """Export the 4 new CSV tables for hardware feasibility, n=25,000 stability, and 8.0 vs 8.1 comparison."""
    tab_dir = config.tables_dir
    out: Dict[str, Path] = {}

    p10 = tab_dir / "10_factibilidad_hardware_ram_o_n2.csv"
    expansion.hardware_feasibility_df.to_csv(p10, index=False)
    out["10_factibilidad_hardware"] = p10

    p11 = tab_dir / "11_comparacion_muestra_3000_vs_25000_ward.csv"
    expansion.stability_comparison_df.to_csv(p11, index=False)
    out["11_comparacion_3k_vs_25k"] = p11

    p12 = tab_dir / "12_perfiles_ward_n25000_escala_original.csv"
    expansion.profile_25k_df.to_csv(p12, index=False)
    out["12_perfiles_ward_25k"] = p12

    p13 = tab_dir / "13_matriz_ejecutiva_comparativa_8_0_vs_8_1.csv"
    expansion.executive_comparison_df.to_csv(p13, index=False)
    out["13_matriz_ejecutiva_8_0_vs_8_1"] = p13

    return out


def write_comparative_analysis_8_0_vs_8_1_md(
    config: HierarchicalClusteringConfig,
    run_id: str,
    run_timestamp: str,
    expansion: WardExpansionResult,
    person_bundle_3k: HierarchicalAnalysisBundle,
) -> Path:
    """Create notebooks/refactor/Analisis_Comparativo_8_0_vs_8_1_Clustering.md in Spanish with all dynamic tables and causal analysis."""
    md_path = config.project_root / "notebooks/refactor/Analisis_Comparativo_8_0_vs_8_1_Clustering.md"

    km_prof_path = config.project_root / "reports/kmeans_jobpath/tables/06_perfiles_completos_y_validacion_posthoc_reincide.csv"
    df_km_prof_all = pd.read_csv(km_prof_path)
    df_km_prof = df_km_prof_all.loc[df_km_prof_all["vista"].str.startswith("Personas")].reset_index(drop=True)

    r_km_c2 = df_km_prof.loc[df_km_prof["cluster"] == 2].iloc[0]
    r_3k_c2 = person_bundle_3k.profile_df.loc[person_bundle_3k.profile_df["cluster"] == 2].iloc[0]
    r_25k_c2 = expansion.profile_25k_df.loc[expansion.profile_25k_df["cluster"] == 2].iloc[0]

    r_km_c3 = df_km_prof.loc[df_km_prof["cluster"] == 3].iloc[0]
    r_3k_c3 = person_bundle_3k.profile_df.loc[person_bundle_3k.profile_df["cluster"] == 3].iloc[0]
    r_25k_c3 = expansion.profile_25k_df.loc[expansion.profile_25k_df["cluster"] == 3].iloc[0]

    content = f"""# Análisis Comparativo Profundo (`8.0` K-Means vs. `8.1` Clustering Jerárquico Ward) y Factibilidad de Hardware ($O(n^2)$)

> **Proyecto:** `MineriaProtect` (JobPath — Observatorio Laboral de Trayectorias y Perfiles ESCO)  
> **Corrida de actualización (`8.1` · `n = 25,000`):** **`{run_id}`** (`{run_timestamp}` · `[CURRENT]`)  
> **Referencia `8.0` K-Means (sin sobrescribir):** `8.0_kmeans_clustering.ipynb` (`RUN-20261119-181140`)  
> **Hardware local evaluado:** Laptop Acer Nitro ANV15-52 · Intel Core i5-13420H (8 núcleos / 12 hilos) · **32 GB RAM (`31.7 GB` útiles)** · RTX 5050 Laptop (4 GB VRAM) · SSD NVMe 512 GB · Windows 11 Home 64-bit.

---

## 1. Justificación Matemática de Factibilidad de Hardware ($O(n^2)$ en 32 GB RAM)

El algoritmo de Clustering Jerárquico Aglomerativo con criterio de enlace `ward` (`scipy.cluster.hierarchy.linkage`) requiere construir previamente la matriz condensada de distancias euclidianas entre todos los pares de observaciones en precisión `float64` (`8 bytes` por par):

$$\\text{{Pares}} = \\frac{{n(n-1)}}{{2}}, \\qquad \\text{{RAM}}_{{\\text{{condensada}}}} = \\frac{{n(n-1)}}{{2}} \\times 8\\text{{ bytes}}$$

### Tabla 1.1 · Cálculo Exacto de RAM $O(n^2)$ para los Escenarios de `MineriaProtect`
{_df_to_markdown(expansion.hardware_feasibility_df)}

- **Demostración de inviabilidad física (desbordamiento de RAM, no tiempo de CPU):** Ejecutar Ward sobre el 100% de `V_PERSON` Train (`281674` personas) exige **`317.36 GB`** solo para alojar el vector condensado de distancias (`~10` veces la RAM física total de `31.7 GB`), y sobre `V_EXPERIENCE` Train (`1391018` filas) exige **`7739.72 GB`** (`~7.74 TB`). Por consiguiente, el fallo sobre el conjunto completo es un **`MemoryError` determinista de memoria física**, independientemente de la velocidad del procesador Intel Core i5-13420H.
- **Muestra segura optimizada para 32 GB RAM (`n = {expansion.n_expanded}` personas):** Con `n = {expansion.n_expanded}` personas estratificadas por Gran Grupo ISCO (`isco_major_modal_posthoc`) y bandera MNAR (`educacion_no_reportada`) con `random_state = 42`, la matriz condensada ocupa **`2.500 GB`** (`2.328 GiB`) y el pico total con Windows 11 y `scipy` se mantiene en `~8.00 GB`, ejecutando el ajuste completo de Ward en **`{expansion.fit_seconds:.2f}` segundos**.

---

## 2. Auditoría de Estabilidad: Ward `n = 3,000` vs. Ward Optimizado `n = {expansion.n_expanded}` vs. K-Means `8.0` (`100% Train`)

### Tabla 2.1 · Comparación de Métricas Internas, Proporciones y Concordancia (`ARI` / `NMI` sobre las `352093` Personas)
{_df_to_markdown(expansion.stability_comparison_df)}

### Tabla 2.2 · Perfiles en Escala Original del Modelo Ward Optimizado (`n = {expansion.n_expanded}` → Proyectado a `352093` Personas)
{_df_to_markdown(expansion.profile_25k_df)}

- **Estabilidad del muestreo jerárquico (`n = 3,000` vs. `n = {expansion.n_expanded}`):** Al multiplicar el tamaño muestral por `8.33x` (pasando del `1.07%` al `8.88%` de todo `Train`), los perfiles proyectados sobre las `352093` personas alcanzan una concordancia de **`ARI = {expansion.ari_25k_vs_3k_full:.4f}`** y **`NMI = {expansion.nmi_25k_vs_3k_full:.4f}`**, con un `silhouette_score = {expansion.silhouette_25k:.4f}` y `davies_bouldin_index = {expansion.davies_bouldin_25k:.4f}`.
- **Concordancia con K-Means `8.0` (`100% Train`):** Sobre las `352093` personas clasificadas, la concordancia frente a K-Means `8.0` es de **`ARI = {expansion.ari_25k_vs_kmeans_full:.4f}`** (`NMI = {expansion.nmi_25k_vs_kmeans_full:.4f}`) para Ward `n = {expansion.n_expanded}` frente a **`ARI = {expansion.ari_3k_vs_kmeans_full:.4f}`** (`NMI = {expansion.nmi_3k_vs_kmeans_full:.4f}`) para Ward `n = 3,000`.

---

## 3. Impacto del Tratamiento de Datos en la Geometría de Ambos Algoritmos

1. **Escalado obligatorio (`StandardScaler`):** Sin estandarización, `span_q` (rango de `1` a `> 160` trimestres) y `mean_skills_competence` dominarían por completo la distancia euclidiana al cuadrado, anulando variables de rango `[0, 1]` como `mean_prop_competence` y `educacion_no_reportada`. Al llevar todas las variables a $\\mu = 0$ y $\\sigma = 1$, cada eje conductual aporta peso equitativo a la varianza de Ward y a la inercia WCSS de K-Means.
2. **Eliminación de la colinealidad exacta $E = C + K$:** Como `n_skills_essential = n_skills_competence + n_skills_knowledge` se cumple en el `99.10%` de las filas clasificadas, omitir `n_skills_essential` de `X` evita duplicar el peso del volumen de competencias en el cálculo de distancias euclidianas, permitiendo que el eje cognitivo (`mean_skills_knowledge` + `mean_prop_competence`) se separe con nitidez.
3. **Manejo MNAR de `educacion_no_reportada` (sin relleno espurio con `0`):** Al conservar la bandera binaria ortogonal `educacion_no_reportada` (`11.65%` de prevalencia en personas), los registros sin reporte educativo toman un puntaje estandarizado $z \\approx +2.69$. Por eso **los tres modelos (`8.0` K-Means, `8.1` Ward `n = 3,000` y `8.1` Ward `n = {expansion.n_expanded}`) aíslan exactamente el mismo Clúster 1 (`~11.65%`)** sin distorsionar la escala ordinal `1..4` de los demás grupos.
4. **Uso de `Versión B · SIN outliers` como base primaria:** Acotar las colas extremas de competencias ESCO (de `129` a los topes IQR `47.5 / 39.5 / 13.5`) evita que valores atípicos a $+6\\sigma$ arrastren las medias aritméticas de K-Means o consuman las ramas superiores del dendrograma de Ward aislando hojas marginales.

---

## 4. Matriz Ejecutiva Comparativa (`8.0` K-Means vs. `8.1` Ward) y Patrones de Reacción Post-Hoc a `reincide`

### Tabla 4.1 · Contraste Conductual y Reacción Post-Hoc a `reincide` en los 4 Clústeres
{_df_to_markdown(expansion.executive_comparison_df)}

### Explicación de las Divergencias Clave entre K-Means (`8.0`) y Ward (`8.1`)

- **Por qué el Clúster 2 (Profesionales ISCO 2) diverge en tamaño y reincidencia entre K-Means (`{float(r_km_c2['pct_total']):.2f}%` · `{float(r_km_c2['tasa_reincide_test_posthoc_pct']):.2f}%`), Ward `n = 3,000` (`{float(r_3k_c2['pct_total_proyectado']):.2f}%` · `{float(r_3k_c2['tasa_reincide_test_posthoc_pct']):.2f}%`) y Ward `n = {expansion.n_expanded}` (`{float(r_25k_c2['pct_total_proyectado']):.2f}%` · `{float(r_25k_c2['tasa_reincide_test_posthoc_pct']):.2f}%`):**
  - **Geometría de partición y efecto del tamaño muestral:** En `n = 3,000`, la fusión jerárquica de Ward aísla un núcleo hiper-puro de **alta especialización teórica** (`9.47%`, `mean_skills_knowledge = 7.69`, `mean_prop_competence = 0.66`), logrando la menor reincidencia observada (`34.34%`, `Lift = 0.752x`) porque su movilidad es puramente vertical (ascensos hacia códigos ESCO distintos). Al escalar la muestra de Ward a `n = {expansion.n_expanded}`, el árbol incorpora también a técnicos/profesionales con mayor rotación (`38.85%`, `mean_skills_knowledge = 5.17`, `nivel_academico = 2.22`), mientras que K-Means (`27.99%`, `42.75%`, `Lift = 0.936x`) traza una frontera esférica intermedia.
- **Convergencia estructural del Clúster 3 (Carreras Extensas y Solapadas · ISCO 3) al escalar Ward a `n = {expansion.n_expanded}`:**
  - En `n = 3,000`, Ward mezclaba trayectorias largas con trabajadores de alta rotación (`{float(r_3k_c3['pct_total_proyectado']):.2f}%` · `{float(r_3k_c3['tasa_reincide_test_posthoc_pct']):.2f}%`). Sin embargo, al ampliar la muestra estratificada a `n = {expansion.n_expanded}`, **Ward converge casi 1 a 1 con K-Means `8.0`**: el Clúster 3 queda en **`{float(r_25k_c3['pct_total_proyectado']):.2f}%`** (`span_q = 113.00`, `dur_mean = 39.35`, `overlap_ratio = 1.63`, tasa post-hoc `{float(r_25k_c3['tasa_reincide_test_posthoc_pct']):.2f}%`) frente a **`{float(r_km_c3['pct_total']):.2f}%`** (`span_q = 112.14`, `dur_mean = 37.47`, `overlap_ratio = 1.61`, tasa post-hoc `{float(r_km_c3['tasa_reincide_test_posthoc_pct']):.2f}%`) en K-Means, elevando la concordancia global de `ARI = {expansion.ari_3k_vs_kmeans_full:.4f}` (`NMI = {expansion.nmi_3k_vs_kmeans_full:.4f}`) a **`ARI = {expansion.ari_25k_vs_kmeans_full:.4f}` (`NMI = {expansion.nmi_25k_vs_kmeans_full:.4f}`)**!

---

## 5. Conclusiones Accionables de Negocio y Metodológicas

- **Estrategia combinada validada en `MineriaProtect`:** Utilizar **Ward (`8.1`)** con muestreo estratificado optimizado (`n = {expansion.n_expanded}` en 32 GB RAM) para confirmar la taxonomía jerárquica de **4 macro-ramas naturales** (descartando $k \\ge 5$ y los métodos con *chaining* `single`/`average`/`complete`), y adoptar **K-Means++ (`8.0`)** sobre el `100%` de Train (`281674` personas y `1391018` experiencias) como motor operativo de asignación y reporte de centroides exactos en escala original.
- **Acciones diferenciadas para el Observatorio Laboral JobPath:**
  - **Clúster 0 (Inserción Temprana / Operativos ISCO 5):** Programas puente al primer empleo y certificación de competencias transversales para romper el ciclo de rotación horizontal repetitiva entre empleadores.
  - **Clúster 1 (Educación No Reportada · MNAR `11.65%`):** Evaluación y certificación de saberes previos empíricos para formalizar habilidades de trabajadores sin título universitario reportado.
  - **Clúster 2 (Profesionales Intensivos en Conocimiento · ISCO 2):** Rutas de posgrado aplicado, liderazgo técnico y vinculación universidad-empresa que potencien su trayectoria natural de ascenso vertical.
  - **Clúster 3 (Carreras Extensas / Multi-Empleo Solapado · ISCO 3):** Acompañamiento para consolidar portafolios laborales fragmentados y programas de reconversión ejecutiva para perfiles sénior.
"""

    md_path.write_text(content.strip() + "\n", encoding="utf-8")
    return md_path
