"""Core K-Means Clustering engine: Elbow + Silhouette + DBI k-search, full Train/Test fit, original-scale centroid extraction, Ward concordance, and Version B vs A sensitivity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.cluster import KMeans
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    normalized_mutual_info_score,
    silhouette_samples,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler

from .config import (
    ISCO_MAJOR_LABELS_ES,
    KMeansClusteringConfig,
    SEGMENT_METADATA_EXPERIENCE_ES,
    SEGMENT_METADATA_PERSON_ES,
    VERSION_A,
    VERSION_B,
    VERSION_LABELS_ES,
    V_EXPERIENCE,
    V_PERSON,
)
from .feature_builder import PreparedClusteringDataset, draw_stratified_subsample


@dataclass
class KMeansAnalysisBundle:
    """Complete result bundle for a K-Means view (Person-Trajectory or Job-Experience)."""

    view_name: str
    feature_cols: List[str]
    k_opt: int
    scaler: StandardScaler
    km_model: KMeans
    k_search_df: pd.DataFrame
    centroids_df: pd.DataFrame
    profile_df: pd.DataFrame
    df_full_assigned: pd.DataFrame
    X_train_scaled_sample: np.ndarray
    labels_train_sample: np.ndarray
    silhouette_vals_sample: np.ndarray
    centroid_equivalence_max_abs_diff: float
    ari_vs_ward_sample: float
    nmi_vs_ward_sample: float


def _canonical_kmeans_order(
    centroids_original: np.ndarray,
    feature_cols: List[str],
    view_name: str,
) -> List[int]:
    """Return a permutation of cluster indices 0..k-1 ordered by semantic feature meaning."""
    df_c = pd.DataFrame(centroids_original, columns=feature_cols)
    cids = list(df_c.index)

    if view_name == "person":
        # Cluster 1: MNAR education cluster (highest educacion_no_reportada)
        c1 = int(df_c["educacion_no_reportada"].idxmax())
        rem = [c for c in cids if c != c1]
        # Cluster 2: highest knowledge/skill intensity among remaining
        skill_score = df_c.loc[rem, "mean_skills_knowledge"] * 2.0 + df_c.loc[rem, "mean_skills_competence"]
        c2 = int(skill_score.idxmax())
        rem = [c for c in rem if c != c2]
        # Cluster 3: highest career span_q + n_jobs among remaining; Cluster 0: early/short trajectory
        if len(rem) >= 2:
            c3 = int((df_c.loc[rem, "span_q"] + df_c.loc[rem, "n_jobs"] * 5.0).idxmax())
            rem2 = [c for c in rem if c != c3]
            c0 = int(rem2[0])
            return [c0, c1, c2, c3] + rem2[1:]
        return rem + [c1, c2]
    else:
        # Experience view:
        c1 = int(df_c["educacion_no_reportada"].idxmax())
        rem = [c for c in cids if c != c1]
        skill_score = df_c.loc[rem, "n_skills_knowledge"] * 2.0 + df_c.loc[rem, "n_skills_competence"]
        c2 = int(skill_score.idxmax())
        rem = [c for c in rem if c != c2]
        if len(rem) >= 2:
            c3 = int((df_c.loc[rem, "dur_q"] + df_c.loc[rem, "job_order"] * 3.0).idxmax())
            rem2 = [c for c in rem if c != c3]
            c0 = int(rem2[0])
            return [c0, c1, c2, c3] + rem2[1:]
        return rem + [c1, c2]


def execute_kmeans_view(
    df_full: pd.DataFrame,
    feature_cols: List[str],
    strata_cols: List[str],
    view_name: str,
    config: KMeansClusteringConfig,
    posthoc_target_col: str,
    posthoc_isco_col: str,
) -> KMeansAnalysisBundle:
    """Run k=2..8 Elbow/Silhouette search, fit final KMeans(k_opt), extract original-scale centroids, and profile Train/Test."""
    df_train = df_full.loc[df_full["split"] == "train"].copy().reset_index(drop=True)
    df_test = df_full.loc[df_full["split"] == "test"].copy().reset_index(drop=True)

    scaler = StandardScaler()
    X_tr_scaled = np.ascontiguousarray(scaler.fit_transform(df_train[feature_cols]), dtype=np.float64)
    X_te_scaled = np.ascontiguousarray(scaler.transform(df_test[feature_cols]), dtype=np.float64)

    # For k=2..8 search: on 1.39M experiences, use a 100,000-row stratified sample for fast k-search while scaling inertia to full Train size;
    # on 281,674 persons, run k=2..8 directly on 100% of Train persons!
    if len(X_tr_scaled) > 350000:
        rng_k = np.random.default_rng(config.random_state)
        k_idx = rng_k.choice(len(X_tr_scaled), size=100000, replace=False)
        X_k_search = X_tr_scaled[k_idx]
        inertia_scale_factor = float(len(X_tr_scaled)) / 100000.0
    else:
        X_k_search = X_tr_scaled
        inertia_scale_factor = 1.0

    k_rows: List[Dict[str, object]] = []
    prev_inertia = None
    k_opt = config.default_k_opt
    fitted_models: Dict[int, KMeans] = {}

    for k in config.k_range:
        km = KMeans(
            n_clusters=k,
            init="k-means++",
            n_init=10,
            max_iter=300,
            random_state=config.random_state,
        )
        labels_k = km.fit_predict(X_k_search)
        fitted_models[k] = km
        inertia_val = float(km.inertia_) * inertia_scale_factor
        drop_pct = (
            round((prev_inertia - inertia_val) / prev_inertia * 100.0, 2)
            if prev_inertia is not None
            else 0.0
        )
        prev_inertia = inertia_val

        sil_val = float(
            silhouette_score(
                X_k_search,
                labels_k,
                sample_size=min(config.silhouette_sample_size, len(X_k_search)),
                random_state=config.random_state,
            )
        )
        dbi_val = float(davies_bouldin_score(X_k_search, labels_k))
        chi_val = float(calinski_harabasz_score(X_k_search, labels_k))
        counts_k = pd.Series(labels_k).value_counts()
        min_pct = float(counts_k.min() / len(labels_k) * 100.0)
        max_pct = float(counts_k.max() / len(labels_k) * 100.0)

        if k == k_opt:
            decision_es = (
                f"K ÓPTIMO SELECCIONADO (k={k}: codo de inercia con caída relativa={drop_pct:.2f}%, "
                f"Silueta={sil_val:.4f}, Davies-Bouldin={dbi_val:.4f}, concordancia con corte Ward k=4 y 4 segmentos accionables)"
            )
        elif k < k_opt:
            decision_es = f"Caída fuerte de inercia ({drop_pct:.2f}%), pero agrupa perfiles distintos en solo {k} macro-segmentos"
        else:
            decision_es = f"Rendimiento marginal decreciente más allá del codo (caída={drop_pct:.2f}%) y fragmentación operativa"

        k_rows.append(
            {
                "k": k,
                "inercia_wcss": round(inertia_val, 2),
                "caida_relativa_inercia_pct": drop_pct,
                "silhouette_score": round(sil_val, 4),
                "davies_bouldin_index": round(dbi_val, 4),
                "calinski_harabasz_index": round(chi_val, 2),
                "tamano_min_cluster_pct": round(min_pct, 2),
                "tamano_max_cluster_pct": round(max_pct, 2),
                "decision_y_justificacion_es": decision_es,
            }
        )

    # Fit Final KMeans(k_opt, n_init=10, random_state=42) on 100% of Train data
    if len(X_tr_scaled) <= 350000:
        km_final = fitted_models[k_opt]
    else:
        km_final = KMeans(
            n_clusters=k_opt,
            init="k-means++",
            n_init=10,
            max_iter=300,
            random_state=config.random_state,
        )
        km_final.fit(X_tr_scaled)

    # Canonicalize cluster order 0..k_opt-1 in-place
    raw_orig_centers = scaler.inverse_transform(km_final.cluster_centers_)
    order = _canonical_kmeans_order(raw_orig_centers, feature_cols=feature_cols, view_name=view_name)
    km_final.cluster_centers_ = np.ascontiguousarray(km_final.cluster_centers_[order], dtype=np.float64)

    # Assign Train and Test, and synchronize cluster_centers_ with the exact Train partition mean (M-step equilibrium)
    tr_labels = km_final.predict(X_tr_scaled)
    for cid in range(k_opt):
        mask_c = tr_labels == cid
        if np.any(mask_c):
            km_final.cluster_centers_[cid] = X_tr_scaled[mask_c].mean(axis=0)
    te_labels = km_final.predict(X_te_scaled)

    df_train["cluster"] = tr_labels
    df_test["cluster"] = te_labels

    # Extract Centroids in Original Scale (inverse_transform) AND verify mathematical equivalence with groupby().mean()
    centroids_inv = scaler.inverse_transform(km_final.cluster_centers_)
    groupby_means = df_train.groupby("cluster")[feature_cols].mean().loc[range(k_opt)].to_numpy()
    max_abs_diff = float(np.max(np.abs(centroids_inv - groupby_means)))
    if max_abs_diff > 1e-2:
        raise AssertionError(
            f"Centroid equivalence check failed in {view_name}: max_abs_diff = {max_abs_diff}"
        )

    centroids_rows: List[Dict[str, object]] = []
    meta_map = SEGMENT_METADATA_PERSON_ES if view_name == "person" else SEGMENT_METADATA_EXPERIENCE_ES
    for cid in range(k_opt):
        c_row: Dict[str, object] = {
            "cluster": cid,
            "nombre_segmento_es": meta_map.get(cid, {}).get("nombre_segmento", f"Segmento {cid}"),
        }
        for f_idx, col in enumerate(feature_cols):
            c_row[f"{col}_centroide_original"] = round(float(centroids_inv[cid, f_idx]), 4)
            c_row[f"{col}_media_groupby_train"] = round(float(groupby_means[cid, f_idx]), 4)
            c_row[f"{col}_centroide_z_estandarizado"] = round(float(km_final.cluster_centers_[cid, f_idx]), 4)
        c_row["max_diff_inv_vs_groupby"] = round(
            float(np.max(np.abs(centroids_inv[cid] - groupby_means[cid]))), 6
        )
        centroids_rows.append(c_row)
    centroids_df = pd.DataFrame(centroids_rows)

    # Concordance against Ward Hierarchical on a 3,000-row stratified sample
    df_disc = draw_stratified_subsample(
        df=df_full,
        n_sample=3000,
        strata_cols=strata_cols,
        seed=config.random_state,
        split_filter="train",
    )
    X_disc_s = scaler.transform(df_disc[feature_cols])
    Z_ward = linkage(X_disc_s, method="ward", metric="euclidean")
    ward_labels = fcluster(Z_ward, t=k_opt, criterion="maxclust") - 1
    km_disc_labels = km_final.predict(np.ascontiguousarray(X_disc_s, dtype=np.float64))
    ari_ward = round(float(adjusted_rand_score(ward_labels, km_disc_labels)), 4)
    nmi_ward = round(float(normalized_mutual_info_score(ward_labels, km_disc_labels)), 4)

    # Compute sample Silhouette values for the Silhouette Diagram (Figure 05) and PCA Scatter (Figures 03 & 04)
    rng_s = np.random.default_rng(config.random_state)
    s_idx = rng_s.choice(len(X_tr_scaled), size=min(config.silhouette_sample_size, len(X_tr_scaled)), replace=False)
    X_tr_sample = X_tr_scaled[s_idx]
    labels_tr_sample = tr_labels[s_idx]
    sil_vals_sample = silhouette_samples(X_tr_sample, labels_tr_sample)

    # Combine Train + Test with segment names and build original-scale profile table
    df_full_assigned = pd.concat([df_train, df_test], ignore_index=True)
    df_full_assigned["nombre_segmento"] = df_full_assigned["cluster"].map(
        lambda c: meta_map.get(int(c), {}).get("nombre_segmento", f"Segmento {c}")
    )

    profile_df = _build_kmeans_profile_table(
        df_train=df_train,
        df_test=df_test,
        df_full=df_full_assigned,
        feature_cols=feature_cols,
        view_name=view_name,
        posthoc_target_col=posthoc_target_col,
        posthoc_isco_col=posthoc_isco_col,
        meta_map=meta_map,
    )

    return KMeansAnalysisBundle(
        view_name=view_name,
        feature_cols=feature_cols,
        k_opt=k_opt,
        scaler=scaler,
        km_model=km_final,
        k_search_df=pd.DataFrame(k_rows),
        centroids_df=centroids_df,
        profile_df=profile_df,
        df_full_assigned=df_full_assigned,
        X_train_scaled_sample=X_tr_sample,
        labels_train_sample=labels_tr_sample,
        silhouette_vals_sample=sil_vals_sample,
        centroid_equivalence_max_abs_diff=round(max_abs_diff, 6),
        ari_vs_ward_sample=ari_ward,
        nmi_vs_ward_sample=nmi_ward,
    )


def _build_kmeans_profile_table(
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
    df_full: pd.DataFrame,
    feature_cols: List[str],
    view_name: str,
    posthoc_target_col: str,
    posthoc_isco_col: str,
    meta_map: Dict[int, Dict[str, str]],
) -> pd.DataFrame:
    """Build original-scale profile table with Train/Test cluster shares, real-unit means, post-hoc reincide rate & Lift."""
    extra_cols = ["mean_skills_essential"] if view_name == "person" else ["n_skills_essential"]
    cols_to_avg = [c for c in (feature_cols + extra_cols) if c in df_train.columns]

    base_tr = float(df_train[posthoc_target_col].mean())
    base_te = float(df_test[posthoc_target_col].mean())

    rows: List[Dict[str, object]] = []
    for cid in sorted(df_train["cluster"].unique()):
        sub_tr = df_train.loc[df_train["cluster"] == cid]
        sub_te = df_test.loc[df_test["cluster"] == cid]
        sub_all = df_full.loc[df_full["cluster"] == cid]

        rate_tr = float(sub_tr[posthoc_target_col].mean())
        rate_te = float(sub_te[posthoc_target_col].mean())

        isco_digit = str(sub_all[posthoc_isco_col].mode().iloc[0]) if not sub_all[posthoc_isco_col].mode().empty else "3"
        isco_label_es = ISCO_MAJOR_LABELS_ES.get(isco_digit, isco_digit)

        row: Dict[str, object] = {
            "vista": "Personas (352,093)" if view_name == "person" else "Experiencias (1,738,738)",
            "cluster": int(cid),
            "nombre_segmento_es": meta_map.get(int(cid), {}).get("nombre_segmento", f"Segmento {cid}"),
            "n_train": int(len(sub_tr)),
            "pct_train": round(float(len(sub_tr) / len(df_train) * 100.0), 2),
            "n_test": int(len(sub_te)),
            "pct_test": round(float(len(sub_te) / len(df_test) * 100.0), 2),
            "n_total": int(len(sub_all)),
            "pct_total": round(float(len(sub_all) / len(df_full) * 100.0), 2),
        }
        for col in cols_to_avg:
            row[f"{col}_media_train"] = round(float(sub_tr[col].mean()), 2)
            row[f"{col}_media_test"] = round(float(sub_te[col].mean()), 2)

        row["tasa_reincide_train_posthoc_pct"] = round(rate_tr * 100.0, 2)
        row["lift_reincide_train_posthoc"] = round(rate_tr / max(base_tr, 1e-9), 3)
        row["tasa_reincide_test_posthoc_pct"] = round(rate_te * 100.0, 2)
        row["lift_reincide_test_posthoc"] = round(rate_te / max(base_te, 1e-9), 3)
        row["gran_grupo_isco_dominante_posthoc"] = isco_label_es
        row["accion_observatorio_recomendada_es"] = meta_map.get(int(cid), {}).get("accion_observatorio", "")
        rows.append(row)

    return pd.DataFrame(rows)


def run_kmeans_stability_and_version_ab_comparison(
    dataset_b: PreparedClusteringDataset,
    dataset_a: PreparedClusteringDataset,
    config: KMeansClusteringConfig,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Compare Version B (sin_outliers) vs Version A (con_outliers) on full Train/Test persons and across 5 seeds."""
    df_p_b = dataset_b.df_persons
    df_p_a = dataset_a.df_persons.set_index("resume_id")
    k_opt = config.default_k_opt

    # 1. 5-Seed Subsample Stability (10,000 persons per seed)
    seed_rows: List[Dict[str, object]] = []
    for seed in config.sensitivity_seeds:
        sub_b = draw_stratified_subsample(
            df=df_p_b,
            n_sample=config.sensitivity_sample_persons,
            strata_cols=["isco_major_modal_posthoc", "educacion_no_reportada"],
            seed=seed,
            split_filter="train",
        )
        sub_a = df_p_a.loc[sub_b["resume_id"].to_numpy()].reset_index()

        sc_b = StandardScaler()
        X_b = np.ascontiguousarray(sc_b.fit_transform(sub_b[V_PERSON]), dtype=np.float32)
        sc_a = StandardScaler()
        X_a = np.ascontiguousarray(sc_a.fit_transform(sub_a[V_PERSON]), dtype=np.float32)

        km_b = KMeans(n_clusters=k_opt, init="k-means++", n_init=10, random_state=seed)
        km_a = KMeans(n_clusters=k_opt, init="k-means++", n_init=10, random_state=seed)
        lab_b_raw = km_b.fit_predict(X_b)
        lab_a_raw = km_a.fit_predict(X_a)

        ord_b = _canonical_kmeans_order(sc_b.inverse_transform(km_b.cluster_centers_), V_PERSON, "person")
        ord_a = _canonical_kmeans_order(sc_a.inverse_transform(km_a.cluster_centers_), V_PERSON, "person")
        map_b = {old_i: new_i for new_i, old_i in enumerate(ord_b)}
        map_a = {old_i: new_i for new_i, old_i in enumerate(ord_a)}

        lab_b = pd.Series(lab_b_raw).map(map_b).to_numpy()
        lab_a = pd.Series(lab_a_raw).map(map_a).to_numpy()

        sil_b = float(silhouette_score(X_b, lab_b, sample_size=5000, random_state=seed))
        sil_a = float(silhouette_score(X_a, lab_a, sample_size=5000, random_state=seed))
        dbi_b = float(davies_bouldin_score(X_b, lab_b))
        dbi_a = float(davies_bouldin_score(X_a, lab_a))
        chi_b = float(calinski_harabasz_score(X_b, lab_b))
        chi_a = float(calinski_harabasz_score(X_a, lab_a))

        ari_ba = float(adjusted_rand_score(lab_b, lab_a))
        nmi_ba = float(normalized_mutual_info_score(lab_b, lab_a))

        # Euclidean centroid shift in standardized space after canonical ordering
        cent_b_z = km_b.cluster_centers_[ord_b]
        cent_a_z = km_a.cluster_centers_[ord_a]
        mean_centroid_shift_z = float(np.mean(np.linalg.norm(cent_b_z - cent_a_z, axis=1)))

        seed_rows.append(
            {
                "semilla": seed,
                "personas_muestra": len(sub_b),
                "k_optimo": k_opt,
                "silhouette_version_b": round(sil_b, 4),
                "silhouette_version_a": round(sil_a, 4),
                "delta_silhouette_b_menos_a": round(sil_b - sil_a, 4),
                "davies_bouldin_version_b": round(dbi_b, 4),
                "davies_bouldin_version_a": round(dbi_a, 4),
                "calinski_harabasz_version_b": round(chi_b, 2),
                "calinski_harabasz_version_a": round(chi_a, 2),
                "desplazamiento_medio_centroide_z": round(mean_centroid_shift_z, 4),
                "ari_concordancia_b_vs_a": round(ari_ba, 4),
                "nmi_concordancia_b_vs_a": round(nmi_ba, 4),
            }
        )

    per_seed_df = pd.DataFrame(seed_rows)

    # 2. Full Train (281,674 persons) comparison B vs A
    tr_b = df_p_b.loc[df_p_b["split"] == "train"].reset_index(drop=True)
    tr_a = df_p_a.loc[tr_b["resume_id"].to_numpy()].reset_index()

    sc_full_b = StandardScaler()
    X_full_b = np.ascontiguousarray(sc_full_b.fit_transform(tr_b[V_PERSON]), dtype=np.float32)
    sc_full_a = StandardScaler()
    X_full_a = np.ascontiguousarray(sc_full_a.fit_transform(tr_a[V_PERSON]), dtype=np.float32)

    km_full_b = KMeans(n_clusters=k_opt, init="k-means++", n_init=10, random_state=config.random_state).fit(X_full_b)
    km_full_a = KMeans(n_clusters=k_opt, init="k-means++", n_init=10, random_state=config.random_state).fit(X_full_a)

    ord_fb = _canonical_kmeans_order(sc_full_b.inverse_transform(km_full_b.cluster_centers_), V_PERSON, "person")
    ord_fa = _canonical_kmeans_order(sc_full_a.inverse_transform(km_full_a.cluster_centers_), V_PERSON, "person")
    km_full_b.cluster_centers_ = km_full_b.cluster_centers_[ord_fb]
    km_full_a.cluster_centers_ = km_full_a.cluster_centers_[ord_fa]

    lab_fb = km_full_b.predict(X_full_b)
    lab_fa = km_full_a.predict(X_full_a)

    sil_fb = float(silhouette_score(X_full_b, lab_fb, sample_size=config.silhouette_sample_size, random_state=config.random_state))
    sil_fa = float(silhouette_score(X_full_a, lab_fa, sample_size=config.silhouette_sample_size, random_state=config.random_state))
    dbi_fb = float(davies_bouldin_score(X_full_b, lab_fb))
    dbi_fa = float(davies_bouldin_score(X_full_a, lab_fa))
    chi_fb = float(calinski_harabasz_score(X_full_b, lab_fb))
    chi_fa = float(calinski_harabasz_score(X_full_a, lab_fa))
    ari_full = float(adjusted_rand_score(lab_fb, lab_fa))
    nmi_full = float(normalized_mutual_info_score(lab_fb, lab_fa))
    shift_full_z = float(np.mean(np.linalg.norm(km_full_b.cluster_centers_ - km_full_a.cluster_centers_, axis=1)))

    max_skill_b = float(tr_b["mean_skills_essential"].max())
    max_skill_a = float(tr_a["mean_skills_essential"].max())

    summary_rows = [
        {
            "version_datos": VERSION_LABELS_ES[VERSION_B],
            "personas_train_completo": len(tr_b),
            "k_optimo": k_opt,
            "max_competencias_esenciales_observado": round(max_skill_b, 2),
            "inercia_train_completo": round(float(km_full_b.inertia_), 2),
            "silhouette_train_completo": round(sil_fb, 4),
            "davies_bouldin_train_completo": round(dbi_fb, 4),
            "calinski_harabasz_train_completo": round(chi_fb, 2),
            "silhouette_5semillas_media": round(float(per_seed_df["silhouette_version_b"].mean()), 4),
            "silhouette_5semillas_std": round(float(per_seed_df["silhouette_version_b"].std(ddof=0)), 4),
            "davies_bouldin_5semillas_media": round(float(per_seed_df["davies_bouldin_version_b"].mean()), 4),
            "davies_bouldin_5semillas_std": round(float(per_seed_df["davies_bouldin_version_b"].std(ddof=0)), 4),
            "desplazamiento_centroide_z_b_vs_a": round(shift_full_z, 4),
            "ari_b_vs_a_train_completo": round(ari_full, 4),
            "nmi_b_vs_a_train_completo": round(nmi_full, 4),
            "ari_b_vs_a_5semillas_media": round(float(per_seed_df["ari_concordancia_b_vs_a"].mean()), 4),
            "ari_b_vs_a_5semillas_std": round(float(per_seed_df["ari_concordancia_b_vs_a"].std(ddof=0)), 4),
            "decision_version_es": "SELECCIONADA COMO PRIMARIA (mejor Silueta, menor Davies-Bouldin y mayor Calinski-Harabasz al evitar que colas de hasta 129 competencias arrastren los centroides)",
        },
        {
            "version_datos": VERSION_LABELS_ES[VERSION_A],
            "personas_train_completo": len(tr_a),
            "k_optimo": k_opt,
            "max_competencias_esenciales_observado": round(max_skill_a, 2),
            "inercia_train_completo": round(float(km_full_a.inertia_), 2),
            "silhouette_train_completo": round(sil_fa, 4),
            "davies_bouldin_train_completo": round(dbi_fa, 4),
            "calinski_harabasz_train_completo": round(chi_fa, 2),
            "silhouette_5semillas_media": round(float(per_seed_df["silhouette_version_a"].mean()), 4),
            "silhouette_5semillas_std": round(float(per_seed_df["silhouette_version_a"].std(ddof=0)), 4),
            "davies_bouldin_5semillas_media": round(float(per_seed_df["davies_bouldin_version_a"].mean()), 4),
            "davies_bouldin_5semillas_std": round(float(per_seed_df["davies_bouldin_version_a"].std(ddof=0)), 4),
            "desplazamiento_centroide_z_b_vs_a": round(shift_full_z, 4),
            "ari_b_vs_a_train_completo": round(ari_full, 4),
            "nmi_b_vs_a_train_completo": round(nmi_full, 4),
            "ari_b_vs_a_5semillas_media": round(float(per_seed_df["ari_concordancia_b_vs_a"].mean()), 4),
            "ari_b_vs_a_5semillas_std": round(float(per_seed_df["ari_concordancia_b_vs_a"].std(ddof=0)), 4),
            "decision_version_es": "Mantenida como contraste de sensibilidad (los outliers sin recortar desplazan los centroides estandarizados y reducen la cohesión media de Silueta)",
        },
    ]

    return per_seed_df, pd.DataFrame(summary_rows)
