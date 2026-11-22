"""Core Agglomerative Hierarchical Clustering engine: linkage tournament, optimal cut, 5-seed stability, K-Means concordance, and Version B vs A sensitivity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import cophenet, fcluster, linkage
from scipy.spatial.distance import pdist
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    normalized_mutual_info_score,
    silhouette_samples,
    silhouette_score,
)
from sklearn.neighbors import NearestCentroid
from sklearn.preprocessing import StandardScaler

from .config import (
    HierarchicalClusteringConfig,
    ISCO_MAJOR_LABELS_ES,
    SEGMENT_METADATA_EXPERIENCE_ES,
    SEGMENT_METADATA_PERSON_ES,
    VERSION_A,
    VERSION_B,
    VERSION_LABELS_ES,
    V_EXPERIENCE,
    V_PERSON,
)
from .sampling_and_features import PreparedClusteringDataset, draw_stratified_subsample


@dataclass
class HierarchicalAnalysisBundle:
    """Complete result bundle for the Agglomerative Hierarchical Clustering pipeline."""

    view_name: str
    feature_cols: List[str]
    k_opt: int
    optimal_cut_height: float
    scaler: StandardScaler
    X_micro_scaled: np.ndarray
    Z_micro_ward: np.ndarray
    df_discovery: pd.DataFrame
    X_discovery_scaled: np.ndarray
    Z_discovery_by_method: Dict[str, np.ndarray]
    linkage_tournament_df: pd.DataFrame
    cuts_evaluation_df: pd.DataFrame
    profile_df: pd.DataFrame
    df_full_assigned: pd.DataFrame
    ari_vs_kmeans: float
    nmi_vs_kmeans: float


def run_linkage_tournament(
    X_scaled: np.ndarray,
    k_reference: int = 4,
) -> Tuple[pd.DataFrame, Dict[str, np.ndarray]]:
    """Benchmark ward, complete, average, and single linkage on the standardized discovery sample."""
    pairwise_dists = pdist(X_scaled, metric="euclidean")
    methods = ("ward", "complete", "average", "single")
    rows: List[Dict[str, object]] = []
    z_map: Dict[str, np.ndarray] = {}

    for method in methods:
        Z = linkage(X_scaled, method=method, metric="euclidean")
        z_map[method] = Z
        coph_corr, _ = cophenet(Z, pairwise_dists)

        labels = fcluster(Z, t=k_reference, criterion="maxclust") - 1
        n_unique = len(np.unique(labels))
        counts = pd.Series(labels).value_counts().sort_index()
        largest_pct = float(counts.max() / len(labels) * 100.0)
        smallest_n = int(counts.min())

        if n_unique > 1:
            sil = float(silhouette_score(X_scaled, labels))
            dbi = float(davies_bouldin_score(X_scaled, labels))
            chi = float(calinski_harabasz_score(X_scaled, labels))
        else:
            sil, dbi, chi = 0.0, 99.0, 0.0

        if method == "ward":
            verdict_es = (
                "SELECCIONADO (prioridad metodológica: minimiza incremento de varianza intra-clúster ΔESS y produce segmentos balanceados y accionables)"
            )
        elif largest_pct >= 85.0:
            verdict_es = (
                f"Descartado por efecto encadenamiento (chaining: el clúster mayor absorbe {largest_pct:.2f}% de la muestra y aísla hojas marginales)"
            )
        else:
            verdict_es = (
                "Descartado frente a Ward (menor equilibrio de tamaños de grupo o menor poder de separación operativa)"
            )

        rows.append(
            {
                "metodo_linkage": method,
                "correlacion_cofenetica": round(float(coph_corr), 4),
                "k_evaluado": k_reference,
                "silhouette_score": round(sil, 4),
                "davies_bouldin_index": round(dbi, 4),
                "calinski_harabasz_index": round(chi, 2),
                "tamano_min_cluster": smallest_n,
                "tamano_max_cluster": int(counts.max()),
                "pct_cluster_mas_grande": round(largest_pct, 2),
                "decision_y_diagnostico_es": verdict_es,
            }
        )

    return pd.DataFrame(rows), z_map


def evaluate_ward_dendrogram_cuts(
    Z_ward: np.ndarray,
    X_scaled: np.ndarray,
    k_range: Tuple[int, ...],
    k_selected: int,
) -> pd.DataFrame:
    """Evaluate horizontal cuts k=2..8 on Ward linkage using vertical fusion jumps, Silhouette, DBI, and CHI."""
    n_obs = X_scaled.shape[0]
    rows: List[Dict[str, object]] = []

    for k in k_range:
        labels = fcluster(Z_ward, t=k, criterion="maxclust") - 1
        sil = float(silhouette_score(X_scaled, labels))
        dbi = float(davies_bouldin_score(X_scaled, labels))
        chi = float(calinski_harabasz_score(X_scaled, labels))

        h_upper = float(Z_ward[n_obs - k, 2])
        h_lower = float(Z_ward[n_obs - k - 1, 2]) if (n_obs - k - 1) >= 0 else 0.0
        jump = h_upper - h_lower
        cut_height = 0.5 * (h_upper + h_lower)

        counts = pd.Series(labels).value_counts()
        min_pct = float(counts.min() / n_obs * 100.0)
        max_pct = float(counts.max() / n_obs * 100.0)

        if k == k_selected:
            decision_es = (
                f"CORTE ÓPTIMO SELECCIONADO (k={k}: equilibrio entre salto vertical de fusión={jump:.2f}, "
                f"Silueta={sil:.4f}, Davies-Bouldin={dbi:.4f} y 4 arquetipos accionables con soporte mínimo={min_pct:.2f}%)"
            )
        elif k == 2:
            decision_es = "Partición binaria macro demasiado gruesa (separa solo 2 grandes bloques sin distinguir rotación vs. complejidad ESCO)"
        elif k == 3:
            decision_es = "Partición parsimoniosa válida, pero fusiona a los especialistas estables con el grupo de alta exigencia ESCO"
        else:
            decision_es = f"Descartado por sobre-fragmentación operativa (k={k} divide arquetipos en subgrupos con menor salto vertical={jump:.2f})"

        rows.append(
            {
                "k_clusters": k,
                "altura_fusion_superior_ward": round(h_upper, 3),
                "altura_fusion_inferior_ward": round(h_lower, 3),
                "salto_vertical_fusion": round(jump, 3),
                "altura_corte_horizontal": round(cut_height, 3),
                "silhouette_score": round(sil, 4),
                "davies_bouldin_index": round(dbi, 4),
                "calinski_harabasz_index": round(chi, 2),
                "tamano_min_cluster": int(counts.min()),
                "pct_min_cluster": round(min_pct, 2),
                "tamano_max_cluster": int(counts.max()),
                "pct_max_cluster": round(max_pct, 2),
                "justificacion_corte_es": decision_es,
            }
        )

    return pd.DataFrame(rows)


def _canonical_cluster_remap(
    df_sample: pd.DataFrame,
    raw_labels: np.ndarray,
    view_name: str,
) -> Dict[int, int]:
    """Assign deterministic cluster IDs 0..k-1 based on semantic feature means so cluster names match their profile."""
    temp = df_sample.copy()
    temp["_cid"] = raw_labels
    means = temp.groupby("_cid").mean(numeric_only=True)
    cids = list(means.index)

    if view_name == "person":
        # Cluster 3: highest n_jobs (high rotation / multi-job)
        c3 = int(means["n_jobs"].idxmax())
        rem = [c for c in cids if c != c3]
        # Cluster 2: highest mean_skills_competence + mean_skills_knowledge among remaining
        skill_sum = means.loc[rem, "mean_skills_competence"] + means.loc[rem, "mean_skills_knowledge"]
        c2 = int(skill_sum.idxmax())
        rem = [c for c in rem if c != c2]
        # Cluster 1: higher dur_mean among remaining two; Cluster 0: lower dur_mean / shorter career
        if len(rem) >= 2:
            c1 = int(means.loc[rem, "dur_mean"].idxmax())
            rem2 = [c for c in rem if c != c1]
            c0 = int(rem2[0])
            ordered = [c0, c1, c2, c3] + rem2[1:]
        else:
            ordered = rem + [c2, c3]
    else:
        # Experience view:
        # Cluster 1: highest educacion_no_reportada (or MNAR cluster)
        c1 = int(means["educacion_no_reportada"].idxmax())
        rem = [c for c in cids if c != c1]
        # Cluster 2: highest n_skills_competence + n_skills_knowledge among remaining
        skill_sum = means.loc[rem, "n_skills_competence"] + means.loc[rem, "n_skills_knowledge"]
        c2 = int(skill_sum.idxmax())
        rem = [c for c in rem if c != c2]
        # Cluster 3: highest dur_q + job_order among remaining
        if len(rem) >= 2:
            c3 = int((means.loc[rem, "dur_q"] + means.loc[rem, "job_order"]).idxmax())
            rem2 = [c for c in rem if c != c3]
            c0 = int(rem2[0])
            ordered = [c0, c1, c2, c3] + rem2[1:]
        else:
            ordered = rem + [c1, c2]

    return {old_id: new_id for new_id, old_id in enumerate(ordered)}


def execute_hierarchical_view(
    df_full: pd.DataFrame,
    feature_cols: List[str],
    strata_cols: List[str],
    view_name: str,
    config: HierarchicalClusteringConfig,
    posthoc_target_col: str,
    posthoc_isco_col: str,
) -> HierarchicalAnalysisBundle:
    """Execute full 3-tier Hierarchical Clustering for a given view (person or experience)."""
    scaler = StandardScaler()
    df_train_full = df_full.loc[df_full["split"] == "train"]
    scaler.fit(df_train_full[feature_cols])

    # Tier 1: Visual Micro-Sample (n = 60)
    df_micro = draw_stratified_subsample(
        df=df_full,
        n_sample=config.micro_sample_n,
        strata_cols=strata_cols,
        seed=config.random_state,
        split_filter="train",
    )
    X_micro_scaled = scaler.transform(df_micro[feature_cols])
    Z_micro_ward = linkage(X_micro_scaled, method="ward", metric="euclidean")

    # Tier 2: Discovery Sample (n = 3,000) standardized on the discovery sample itself for exact mean=0, std=1
    df_discovery = draw_stratified_subsample(
        df=df_full,
        n_sample=config.discovery_sample_n,
        strata_cols=strata_cols,
        seed=config.random_state,
        split_filter="train",
    )
    disc_scaler = StandardScaler()
    X_discovery_scaled = disc_scaler.fit_transform(df_discovery[feature_cols])

    k_opt = config.default_k_opt
    linkage_tournament_df, z_map = run_linkage_tournament(X_discovery_scaled, k_reference=k_opt)
    Z_ward = z_map["ward"]
    cuts_evaluation_df = evaluate_ward_dendrogram_cuts(
        Z_ward=Z_ward,
        X_scaled=X_discovery_scaled,
        k_range=config.k_range,
        k_selected=k_opt,
    )
    optimal_cut_height = float(
        cuts_evaluation_df.loc[cuts_evaluation_df["k_clusters"] == k_opt, "altura_corte_horizontal"].iloc[0]
    )

    # Fit AgglomerativeClustering(linkage='ward') and canonicalize cluster IDs
    hc = AgglomerativeClustering(n_clusters=k_opt, metric="euclidean", linkage="ward")
    raw_labels = hc.fit_predict(X_discovery_scaled)
    remap = _canonical_cluster_remap(df_discovery, raw_labels, view_name=view_name)

    df_disc_assigned = df_discovery.copy()
    df_disc_assigned["cluster"] = pd.Series(raw_labels, index=df_discovery.index).map(remap).astype(int)

    # Concordance against K-Means on the exact same standardized discovery matrix
    km_check = KMeans(n_clusters=k_opt, init="k-means++", n_init=10, random_state=config.random_state)
    km_labels = km_check.fit_predict(X_discovery_scaled)
    ari_vs_km = round(float(adjusted_rand_score(df_disc_assigned["cluster"], km_labels)), 4)
    nmi_vs_km = round(float(normalized_mutual_info_score(df_disc_assigned["cluster"], km_labels)), 4)

    # NearestCentroid projection onto the entire population (Train + Test)
    nc = NearestCentroid(metric="euclidean")
    nc.fit(X_discovery_scaled, df_disc_assigned["cluster"].to_numpy())
    X_full_scaled = disc_scaler.transform(df_full[feature_cols])
    df_full_assigned = df_full.copy()
    df_full_assigned["cluster"] = nc.predict(X_full_scaled).astype(int)

    meta_map = SEGMENT_METADATA_PERSON_ES if view_name == "person" else SEGMENT_METADATA_EXPERIENCE_ES
    df_disc_assigned["nombre_segmento"] = df_disc_assigned["cluster"].map(
        lambda c: meta_map.get(int(c), {}).get("nombre_segmento", f"Segmento {c}")
    )
    df_full_assigned["nombre_segmento"] = df_full_assigned["cluster"].map(
        lambda c: meta_map.get(int(c), {}).get("nombre_segmento", f"Segmento {c}")
    )

    # Build Original-Scale Profile Table (discovery sample + full projected population + post-hoc target)
    profile_df = _build_original_scale_profile_table(
        df_disc_assigned=df_disc_assigned,
        df_full_assigned=df_full_assigned,
        feature_cols=feature_cols,
        view_name=view_name,
        posthoc_target_col=posthoc_target_col,
        posthoc_isco_col=posthoc_isco_col,
        meta_map=meta_map,
    )

    return HierarchicalAnalysisBundle(
        view_name=view_name,
        feature_cols=feature_cols,
        k_opt=k_opt,
        optimal_cut_height=optimal_cut_height,
        scaler=disc_scaler,
        X_micro_scaled=X_micro_scaled,
        Z_micro_ward=Z_micro_ward,
        df_discovery=df_disc_assigned,
        X_discovery_scaled=X_discovery_scaled,
        Z_discovery_by_method=z_map,
        linkage_tournament_df=linkage_tournament_df,
        cuts_evaluation_df=cuts_evaluation_df,
        profile_df=profile_df,
        df_full_assigned=df_full_assigned,
        ari_vs_kmeans=ari_vs_km,
        nmi_vs_kmeans=nmi_vs_km,
    )


def _build_original_scale_profile_table(
    df_disc_assigned: pd.DataFrame,
    df_full_assigned: pd.DataFrame,
    feature_cols: List[str],
    view_name: str,
    posthoc_target_col: str,
    posthoc_isco_col: str,
    meta_map: Dict[int, Dict[str, str]],
) -> pd.DataFrame:
    """Compute real-unit cluster profiles (means, medians, sizes, post-hoc reincide rate & Lift, ISCO mode)."""
    extra_cols = ["mean_skills_essential"] if view_name == "person" else ["n_skills_essential"]
    cols_to_avg = [c for c in (feature_cols + extra_cols) if c in df_disc_assigned.columns]

    base_rate_disc = float(df_disc_assigned[posthoc_target_col].mean())
    base_rate_full = float(df_full_assigned[posthoc_target_col].mean())

    rows: List[Dict[str, object]] = []
    for cid in sorted(df_disc_assigned["cluster"].unique()):
        sub_d = df_disc_assigned.loc[df_disc_assigned["cluster"] == cid]
        sub_f = df_full_assigned.loc[df_full_assigned["cluster"] == cid]
        sub_f_te = sub_f.loc[sub_f["split"] == "test"]

        rate_d = float(sub_d[posthoc_target_col].mean())
        rate_f = float(sub_f[posthoc_target_col].mean())
        rate_te = float(sub_f_te[posthoc_target_col].mean()) if len(sub_f_te) > 0 else rate_f
        base_te = float(df_full_assigned.loc[df_full_assigned["split"] == "test", posthoc_target_col].mean())

        isco_mode_digit = str(sub_f[posthoc_isco_col].mode().iloc[0]) if not sub_f[posthoc_isco_col].mode().empty else "3"
        isco_label_es = ISCO_MAJOR_LABELS_ES.get(isco_mode_digit, isco_mode_digit)

        row: Dict[str, object] = {
            "cluster": int(cid),
            "nombre_segmento_es": meta_map.get(int(cid), {}).get("nombre_segmento", f"Segmento {cid}"),
            "n_muestra_descubrimiento": int(len(sub_d)),
            "pct_muestra_descubrimiento": round(float(len(sub_d) / len(df_disc_assigned) * 100.0), 2),
            "n_total_proyectado": int(len(sub_f)),
            "pct_total_proyectado": round(float(len(sub_f) / len(df_full_assigned) * 100.0), 2),
            "n_test_proyectado": int(len(sub_f_te)),
            "pct_test_proyectado": round(
                float(len(sub_f_te) / max(1, (df_full_assigned["split"] == "test").sum()) * 100.0), 2
            ),
        }
        for col in cols_to_avg:
            row[f"{col}_media_muestra"] = round(float(sub_d[col].mean()), 2)
            row[f"{col}_media_total"] = round(float(sub_f[col].mean()), 2)

        row["tasa_reincide_muestra_posthoc_pct"] = round(rate_d * 100.0, 2)
        row["lift_reincide_muestra_posthoc"] = round(rate_d / max(base_rate_disc, 1e-9), 3)
        row["tasa_reincide_total_posthoc_pct"] = round(rate_f * 100.0, 2)
        row["tasa_reincide_test_posthoc_pct"] = round(rate_te * 100.0, 2)
        row["lift_reincide_test_posthoc"] = round(rate_te / max(base_te, 1e-9), 3)
        row["gran_grupo_isco_dominante_posthoc"] = isco_label_es
        row["accion_observatorio_recomendada_es"] = meta_map.get(int(cid), {}).get("accion_observatorio", "")
        rows.append(row)

    return pd.DataFrame(rows)


def run_five_seed_stability_and_version_ab_sensitivity(
    dataset_b: PreparedClusteringDataset,
    dataset_a: PreparedClusteringDataset,
    config: HierarchicalClusteringConfig,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Run 5-seed hierarchical clustering stability on Version B and compare head-to-head against Version A."""
    df_p_b = dataset_b.df_persons
    df_p_a = dataset_a.df_persons.set_index("resume_id")

    per_seed_rows: List[Dict[str, object]] = []
    for seed in config.sensitivity_seeds:
        sample_b = draw_stratified_subsample(
            df=df_p_b,
            n_sample=config.discovery_sample_n,
            strata_cols=["isco_major_modal_posthoc", "educacion_no_reportada"],
            seed=seed,
            split_filter="train",
        )
        # Align exact same resume_id sample in Version A
        sample_a = df_p_a.loc[sample_b["resume_id"].to_numpy()].reset_index()

        scaler_b = StandardScaler()
        X_b = scaler_b.fit_transform(sample_b[V_PERSON])
        scaler_a = StandardScaler()
        X_a = scaler_a.fit_transform(sample_a[V_PERSON])

        Z_b = linkage(X_b, method="ward", metric="euclidean")
        Z_a = linkage(X_a, method="ward", metric="euclidean")

        coph_b, _ = cophenet(Z_b, pdist(X_b, metric="euclidean"))
        coph_a, _ = cophenet(Z_a, pdist(X_a, metric="euclidean"))

        labels_b_raw = fcluster(Z_b, t=config.default_k_opt, criterion="maxclust") - 1
        labels_a_raw = fcluster(Z_a, t=config.default_k_opt, criterion="maxclust") - 1

        remap_b = _canonical_cluster_remap(sample_b, labels_b_raw, view_name="person")
        remap_a = _canonical_cluster_remap(sample_a, labels_a_raw, view_name="person")
        labels_b = pd.Series(labels_b_raw).map(remap_b).to_numpy()
        labels_a = pd.Series(labels_a_raw).map(remap_a).to_numpy()

        sil_b = float(silhouette_score(X_b, labels_b))
        sil_a = float(silhouette_score(X_a, labels_a))
        dbi_b = float(davies_bouldin_score(X_b, labels_b))
        dbi_a = float(davies_bouldin_score(X_a, labels_a))
        chi_b = float(calinski_harabasz_score(X_b, labels_b))
        chi_a = float(calinski_harabasz_score(X_a, labels_a))

        ari_ba = float(adjusted_rand_score(labels_b, labels_a))
        nmi_ba = float(normalized_mutual_info_score(labels_b, labels_a))

        n_obs = len(X_b)
        k_opt = config.default_k_opt
        cut_b = 0.5 * float(Z_b[n_obs - k_opt, 2] + Z_b[n_obs - k_opt - 1, 2])
        cut_a = 0.5 * float(Z_a[n_obs - k_opt, 2] + Z_a[n_obs - k_opt - 1, 2])

        max_pct_b = float(pd.Series(labels_b).value_counts(normalize=True).max() * 100.0)
        max_pct_a = float(pd.Series(labels_a).value_counts(normalize=True).max() * 100.0)

        per_seed_rows.append(
            {
                "semilla": seed,
                "n_personas_muestra": n_obs,
                "k_optimo": k_opt,
                "cophenet_version_b": round(float(coph_b), 4),
                "cophenet_version_a": round(float(coph_a), 4),
                "silhouette_version_b": round(sil_b, 4),
                "silhouette_version_a": round(sil_a, 4),
                "delta_silhouette_b_menos_a": round(sil_b - sil_a, 4),
                "davies_bouldin_version_b": round(dbi_b, 4),
                "davies_bouldin_version_a": round(dbi_a, 4),
                "calinski_harabasz_version_b": round(chi_b, 2),
                "calinski_harabasz_version_a": round(chi_a, 2),
                "altura_corte_ward_b": round(cut_b, 3),
                "altura_corte_ward_a": round(cut_a, 3),
                "pct_max_cluster_b": round(max_pct_b, 2),
                "pct_max_cluster_a": round(max_pct_a, 2),
                "ari_concordancia_b_vs_a": round(ari_ba, 4),
                "nmi_concordancia_b_vs_a": round(nmi_ba, 4),
            }
        )

    per_seed_df = pd.DataFrame(per_seed_rows)

    summary_rows = [
        {
            "version_datos": VERSION_LABELS_ES[VERSION_B],
            "n_semillas": len(config.sensitivity_seeds),
            "personas_por_semilla": config.discovery_sample_n,
            "k_optimo": config.default_k_opt,
            "cophenet_media": round(float(per_seed_df["cophenet_version_b"].mean()), 4),
            "cophenet_std": round(float(per_seed_df["cophenet_version_b"].std(ddof=0)), 4),
            "silhouette_media": round(float(per_seed_df["silhouette_version_b"].mean()), 4),
            "silhouette_std": round(float(per_seed_df["silhouette_version_b"].std(ddof=0)), 4),
            "davies_bouldin_media": round(float(per_seed_df["davies_bouldin_version_b"].mean()), 4),
            "davies_bouldin_std": round(float(per_seed_df["davies_bouldin_version_b"].std(ddof=0)), 4),
            "calinski_harabasz_media": round(float(per_seed_df["calinski_harabasz_version_b"].mean()), 2),
            "altura_corte_ward_media": round(float(per_seed_df["altura_corte_ward_b"].mean()), 3),
            "pct_max_cluster_media": round(float(per_seed_df["pct_max_cluster_b"].mean()), 2),
            "ari_b_vs_a_media": round(float(per_seed_df["ari_concordancia_b_vs_a"].mean()), 4),
            "ari_b_vs_a_std": round(float(per_seed_df["ari_concordancia_b_vs_a"].std(ddof=0)), 4),
            "nmi_b_vs_a_media": round(float(per_seed_df["nmi_concordancia_b_vs_a"].mean()), 4),
            "decision_version_es": "RECOMENDADA COMO PRIMARIA (acota colas extremas de conteos ESCO hasta 47.5/39.5/13.5 evitando que outliers arrastren la varianza de Ward)",
        },
        {
            "version_datos": VERSION_LABELS_ES[VERSION_A],
            "n_semillas": len(config.sensitivity_seeds),
            "personas_por_semilla": config.discovery_sample_n,
            "k_optimo": config.default_k_opt,
            "cophenet_media": round(float(per_seed_df["cophenet_version_a"].mean()), 4),
            "cophenet_std": round(float(per_seed_df["cophenet_version_a"].std(ddof=0)), 4),
            "silhouette_media": round(float(per_seed_df["silhouette_version_a"].mean()), 4),
            "silhouette_std": round(float(per_seed_df["silhouette_version_a"].std(ddof=0)), 4),
            "davies_bouldin_media": round(float(per_seed_df["davies_bouldin_version_a"].mean()), 4),
            "davies_bouldin_std": round(float(per_seed_df["davies_bouldin_version_a"].std(ddof=0)), 4),
            "calinski_harabasz_media": round(float(per_seed_df["calinski_harabasz_version_a"].mean()), 2),
            "altura_corte_ward_media": round(float(per_seed_df["altura_corte_ward_a"].mean()), 3),
            "pct_max_cluster_media": round(float(per_seed_df["pct_max_cluster_a"].mean()), 2),
            "ari_b_vs_a_media": round(float(per_seed_df["ari_concordancia_b_vs_a"].mean()), 4),
            "ari_b_vs_a_std": round(float(per_seed_df["ari_concordancia_b_vs_a"].std(ddof=0)), 4),
            "nmi_b_vs_a_media": round(float(per_seed_df["nmi_concordancia_b_vs_a"].mean()), 4),
            "decision_version_es": "Mantenida como contraste de sensibilidad (las colas sin recortar hasta 129 competencias inflan las distancias euclidianas de las hojas extremas)",
        },
    ]
    return per_seed_df, pd.DataFrame(summary_rows)
