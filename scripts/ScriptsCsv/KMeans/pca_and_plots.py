"""Publication-grade visualizations (Spanish titles/labels, 300 DPI) and CSV table exports for K-Means Clustering."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.decomposition import PCA

from .config import KMeansClusteringConfig
from .kmeans_engine import KMeansAnalysisBundle


CLUSTER_PALETTE: List[str] = ["#1F77B4", "#2CA02C", "#FF7F0E", "#D62728", "#9467BD", "#8C564B"]


def _plot_elbow_and_silhouette_panel(
    k_df: pd.DataFrame,
    k_opt: int,
    view_title_es: str,
    fig_path: Path,
) -> None:
    """Render a dual-panel Elbow (Inertia WCSS) and Silhouette Score figure in Spanish."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.8, 5.2), dpi=300)

    ax1.plot(k_df["k"], k_df["inercia_wcss"], marker="o", linewidth=2.3, color="#1F77B4")
    ax1.axvline(x=k_opt, color="#D62728", linestyle="--", linewidth=2.0, label=f"k óptimo seleccionado = {k_opt}")
    ax1.set_title(f"Método del Codo (Inercia WCSS) · {view_title_es}", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Número de clústeres (k)", fontsize=11)
    ax1.set_ylabel("Inercia intra-clúster (WCSS · datos estandarizados)", fontsize=11)
    ax1.legend(loc="upper right", frameon=True)

    ax2.plot(k_df["k"], k_df["silhouette_score"], marker="s", linewidth=2.3, color="#2CA02C")
    ax2.axvline(x=k_opt, color="#D62728", linestyle="--", linewidth=2.0, label=f"k óptimo seleccionado = {k_opt}")
    ax2.set_title(f"Coeficiente de Silueta Promedio vs. k · {view_title_es}", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Número de clústeres (k)", fontsize=11)
    ax2.set_ylabel("Coeficiente de Silueta promedio s(k)", fontsize=11)
    for idx, row in k_df.iterrows():
        ax2.text(row["k"], row["silhouette_score"] + 0.004, f"{row['silhouette_score']:.3f}", ha="center", fontsize=8.8)
    ax2.legend(loc="upper right", frameon=True)

    fig.suptitle(
        f"Determinación del Número Óptimo de Clústeres (k = 2..8) · K-Means++ (n_init = 10, seed = 42) · {view_title_es}",
        fontsize=13,
        fontweight="bold",
        y=1.02,
    )
    fig.tight_layout()
    fig.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _plot_pca_2d_with_centroids(
    bundle: KMeansAnalysisBundle,
    view_title_es: str,
    fig_path: Path,
    seed: int,
) -> None:
    """Project standardized observations and K-Means centroids onto 2D PCA space with Spanish labels."""
    pca = PCA(n_components=2, random_state=seed)
    X_pca = pca.fit_transform(bundle.X_train_scaled_sample)
    centroids_pca = pca.transform(bundle.km_model.cluster_centers_)
    v1 = pca.explained_variance_ratio_[0] * 100.0
    v2 = pca.explained_variance_ratio_[1] * 100.0

    labels = bundle.labels_train_sample
    names_map = dict(zip(bundle.profile_df["cluster"], bundle.profile_df["nombre_segmento_es"]))

    fig, ax = plt.subplots(figsize=(11.8, 6.8), dpi=300)
    for cid in sorted(np.unique(labels)):
        mask = labels == cid
        color = CLUSTER_PALETTE[int(cid) % len(CLUSTER_PALETTE)]
        seg_name = names_map.get(int(cid), f"Segmento {cid}")
        ax.scatter(
            X_pca[mask, 0],
            X_pca[mask, 1],
            s=14,
            alpha=0.45,
            color=color,
            label=f"Clúster {cid}: {seg_name}",
        )
        ax.scatter(
            centroids_pca[int(cid), 0],
            centroids_pca[int(cid), 1],
            s=300,
            marker="*",
            color=color,
            edgecolor="black",
            linewidth=1.6,
            zorder=10,
        )

    ax.set_title(
        f"Proyección PCA 2D de Clústeres K-Means y Centroides (*) · {view_title_es}\n"
        f"Varianza Total Explicada por PC1 + PC2 = {v1 + v2:.1f}%",
        fontsize=12.5,
        fontweight="bold",
    )
    ax.set_xlabel(f"Componente Principal 1 ({v1:.1f}% de varianza explicada)", fontsize=11)
    ax.set_ylabel(f"Componente Principal 2 ({v2:.1f}% de varianza explicada)", fontsize=11)
    ax.legend(loc="best", frameon=True, fontsize=9.2)
    fig.tight_layout()
    fig.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def generate_all_kmeans_figures(
    person_bundle: KMeansAnalysisBundle,
    exp_bundle: KMeansAnalysisBundle,
    per_seed_df: pd.DataFrame,
    ab_summary_df: pd.DataFrame,
    config: KMeansClusteringConfig,
) -> List[Path]:
    """Generate all 7 required 300-DPI PNG figures for K-Means Clustering."""
    sns.set_theme(style="whitegrid")
    fig_dir = config.figures_dir
    saved: List[Path] = []

    # 1. Figure 01: Elbow & Silhouette (Person View)
    p1 = fig_dir / "01_metodo_codo_y_silueta_kmeans_personas.png"
    _plot_elbow_and_silhouette_panel(
        k_df=person_bundle.k_search_df,
        k_opt=person_bundle.k_opt,
        view_title_es="Vista Primaria · Personas / Trayectorias (281,674 Train)",
        fig_path=p1,
    )
    saved.append(p1)

    # 2. Figure 02: Elbow & Silhouette (Experience View)
    p2 = fig_dir / "02_metodo_codo_y_silueta_kmeans_experiencias.png"
    _plot_elbow_and_silhouette_panel(
        k_df=exp_bundle.k_search_df,
        k_opt=exp_bundle.k_opt,
        view_title_es="Vista Secundaria · Experiencias Laborales (1,391,018 Train)",
        fig_path=p2,
    )
    saved.append(p2)

    # 3. Figure 03: PCA 2D Clusters & Centroids (Person View)
    p3 = fig_dir / "03_proyeccion_pca_2d_clusters_y_centroides_personas.png"
    _plot_pca_2d_with_centroids(
        bundle=person_bundle,
        view_title_es="Vista Primaria · Personas / Trayectorias (k = 4)",
        fig_path=p3,
        seed=config.random_state,
    )
    saved.append(p3)

    # 4. Figure 04: PCA 2D Clusters & Centroids (Experience View)
    p4 = fig_dir / "04_proyeccion_pca_2d_clusters_y_centroides_experiencias.png"
    _plot_pca_2d_with_centroids(
        bundle=exp_bundle,
        view_title_es="Vista Secundaria · Experiencias / Perfiles ESCO (k = 4)",
        fig_path=p4,
        seed=config.random_state,
    )
    saved.append(p4)

    # 5. Figure 05: Silhouette Diagram by Cluster for k_opt = 4 (Person View)
    p5 = fig_dir / "05_diagrama_silueta_por_cluster_k_optimo.png"
    fig, ax = plt.subplots(figsize=(11.5, 6.2), dpi=300)
    y_lower = 10
    labels_s = person_bundle.labels_train_sample
    sil_s = person_bundle.silhouette_vals_sample
    mean_sil = float(np.mean(sil_s))

    for cid in sorted(np.unique(labels_s)):
        c_sil_vals = np.sort(sil_s[labels_s == cid])
        size_c = c_sil_vals.shape[0]
        y_upper = y_lower + size_c
        color = CLUSTER_PALETTE[int(cid) % len(CLUSTER_PALETTE)]
        ax.fill_betweenx(
            np.arange(y_lower, y_upper),
            0,
            c_sil_vals,
            facecolor=color,
            edgecolor=color,
            alpha=0.8,
            label=f"Clúster {cid} (n muestra = {size_c}, media s = {np.mean(c_sil_vals):.3f})",
        )
        ax.text(-0.05, y_lower + 0.5 * size_c, f"C{cid}", fontsize=10.5, fontweight="bold")
        y_lower = y_upper + 15

    ax.axvline(x=mean_sil, color="#D62728", linestyle="--", linewidth=2.0, label=f"Silueta global media = {mean_sil:.4f}")
    ax.set_title(
        f"Perfil de Coeficientes de Silueta por Clúster (K-Means · k = {person_bundle.k_opt} · Muestra Train n = {len(labels_s)})",
        fontsize=12.5,
        fontweight="bold",
    )
    ax.set_xlabel("Coeficiente de Silueta individual s(i)", fontsize=11)
    ax.set_ylabel("Observaciones agrupadas y ordenadas por clúster", fontsize=11)
    ax.set_yticks([])
    ax.set_xlim(-0.2, 0.85)
    ax.legend(loc="upper right", frameon=True, fontsize=9.5)
    fig.tight_layout()
    fig.savefig(p5, dpi=300, bbox_inches="tight")
    plt.close(fig)
    saved.append(p5)

    # 6. Figure 06: Original-scale Centroids & Post-Hoc reincide Rate
    p6 = fig_dir / "06_centroides_escala_original_y_tasa_reincide.png"
    prof_p = person_bundle.profile_df
    fig, axes = plt.subplots(1, 3, figsize=(14.8, 5.0), dpi=300)
    c_labels = [f"Clúster {c}" for c in prof_p["cluster"]]
    c_colors = [CLUSTER_PALETTE[int(c) % len(CLUSTER_PALETTE)] for c in prof_p["cluster"]]

    axes[0].bar(c_labels, prof_p["span_q_media_train"], color=c_colors, edgecolor="black")
    axes[0].set_title("Centroide en Escala Real: Amplitud de Carrera (span_q)", fontsize=11, fontweight="bold")
    axes[0].set_ylabel("Trimestres de trayectoria (span_q)", fontsize=10)
    for idx, val in enumerate(prof_p["span_q_media_train"]):
        axes[0].text(idx, val + 1.0, f"{val:.1f} q", ha="center", fontsize=9.5, fontweight="bold")

    axes[1].bar(c_labels, prof_p["mean_skills_knowledge_media_train"], color=c_colors, edgecolor="black")
    axes[1].set_title("Centroide en Escala Real: Conocimientos ESCO", fontsize=11, fontweight="bold")
    axes[1].set_ylabel("Conteo medio de conocimientos ESCO", fontsize=10)
    for idx, val in enumerate(prof_p["mean_skills_knowledge_media_train"]):
        axes[1].text(idx, val + 0.15, f"{val:.2f}", ha="center", fontsize=9.5, fontweight="bold")

    axes[2].bar(c_labels, prof_p["tasa_reincide_test_posthoc_pct"], color=c_colors, edgecolor="black")
    base_te_pct = float(
        person_bundle.df_full_assigned.loc[
            person_bundle.df_full_assigned["split"] == "test", "any_repeated_posthoc"
        ].mean()
        * 100.0
    )
    axes[2].axhline(
        y=base_te_pct,
        color="#D62728",
        linestyle="--",
        linewidth=1.8,
        label=f"Tasa base Test ({base_te_pct:.2f}%)",
    )
    axes[2].set_title("Validación Post-Hoc en Test: % que Repiten Oficio", fontsize=11, fontweight="bold")
    axes[2].set_ylabel("Tasa post-hoc de repetición en Test (%)", fontsize=10)
    for idx, val in enumerate(prof_p["tasa_reincide_test_posthoc_pct"]):
        lift_v = prof_p["lift_reincide_test_posthoc"].iloc[idx]
        axes[2].text(idx, val + 1.3, f"{val:.1f}%\n({lift_v:.2f}x)", ha="center", fontsize=9, fontweight="bold")
    axes[2].set_ylim(0, min(105.0, float(prof_p["tasa_reincide_test_posthoc_pct"].max()) + 18.0))
    axes[2].legend(loc="upper left", fontsize=9)

    fig.suptitle(
        "Centroides K-Means en Escala Original (inverse_transform = groupby.mean) y Tasa Post-Hoc de Repetición en Test",
        fontsize=12.8,
        fontweight="bold",
        y=1.03,
    )
    fig.tight_layout()
    fig.savefig(p6, dpi=300, bbox_inches="tight")
    plt.close(fig)
    saved.append(p6)

    # 7. Figure 07: Sensitivity Version B (SIN outliers) vs Version A (CON outliers) across 5 seeds
    p7 = fig_dir / "07_sensibilidad_version_b_vs_version_a_centroides.png"
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.0), dpi=300)
    x_pos = np.arange(len(per_seed_df))
    width = 0.36
    seed_labels = [f"Semilla {s}" for s in per_seed_df["semilla"]]

    ax1.bar(x_pos - width / 2, per_seed_df["silhouette_version_b"], width=width, color="#2CA02C", edgecolor="black", label="Versión B · SIN outliers (Primaria)")
    ax1.bar(x_pos + width / 2, per_seed_df["silhouette_version_a"], width=width, color="#1F77B4", edgecolor="black", label="Versión A · CON outliers (Sensibilidad)")
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(seed_labels)
    ax1.set_title("Coeficiente de Silueta K-Means en 5 Semillas (B vs. A)", fontsize=11.5, fontweight="bold")
    ax1.set_ylabel("Silhouette Score s(k=4)", fontsize=10.5)
    ax1.legend(loc="lower right", fontsize=9)

    ax2.bar(x_pos - width / 2, per_seed_df["davies_bouldin_version_b"], width=width, color="#2CA02C", edgecolor="black", label="Versión B · SIN outliers (Primaria)")
    ax2.bar(x_pos + width / 2, per_seed_df["davies_bouldin_version_a"], width=width, color="#FF7F0E", edgecolor="black", label="Versión A · CON outliers (Sensibilidad)")
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(seed_labels)
    ax2.set_title("Índice de Davies-Bouldin K-Means en 5 Semillas (B vs. A)", fontsize=11.5, fontweight="bold")
    ax2.set_ylabel("Davies-Bouldin Index (menor es mejor)", fontsize=10.5)
    ax2.legend(loc="lower right", fontsize=9)

    fig.suptitle(
        "Sensibilidad de K-Means a Outliers: Versión B (SIN outliers) vs. Versión A (CON outliers) en 5 Semillas",
        fontsize=12.8,
        fontweight="bold",
        y=1.02,
    )
    fig.tight_layout()
    fig.savefig(p7, dpi=300, bbox_inches="tight")
    plt.close(fig)
    saved.append(p7)

    return saved


def export_all_kmeans_tables(
    data_usage_df: pd.DataFrame,
    person_bundle: KMeansAnalysisBundle,
    exp_bundle: KMeansAnalysisBundle,
    per_seed_df: pd.DataFrame,
    ab_summary_df: pd.DataFrame,
    config: KMeansClusteringConfig,
) -> Dict[str, Path]:
    """Export all 9 required CSV tables to reports/kmeans_jobpath/tables/."""
    tab_dir = config.tables_dir
    exported: Dict[str, Path] = {}

    p01 = tab_dir / "01_uso_de_datos_kmeans.csv"
    data_usage_df.to_csv(p01, index=False)
    exported["01_uso_de_datos"] = p01

    p02 = tab_dir / "02_busqueda_k_codo_silueta_dbi_personas.csv"
    person_bundle.k_search_df.to_csv(p02, index=False)
    exported["02_busqueda_k_personas"] = p02

    p03 = tab_dir / "03_busqueda_k_codo_silueta_dbi_experiencias.csv"
    exp_bundle.k_search_df.to_csv(p03, index=False)
    exported["03_busqueda_k_experiencias"] = p03

    p04 = tab_dir / "04_centroides_personas_escala_original_y_estandarizada.csv"
    person_bundle.centroids_df.to_csv(p04, index=False)
    exported["04_centroides_personas"] = p04

    p05 = tab_dir / "05_centroides_experiencias_escala_original_y_estandarizada.csv"
    exp_bundle.centroids_df.to_csv(p05, index=False)
    exported["05_centroides_experiencias"] = p05

    p06 = tab_dir / "06_perfiles_completos_y_validacion_posthoc_reincide.csv"
    combined_profiles = pd.concat([person_bundle.profile_df, exp_bundle.profile_df], ignore_index=True)
    combined_profiles.to_csv(p06, index=False)
    exported["06_perfiles_completos"] = p06

    p07 = tab_dir / "07_estabilidad_train_vs_test_y_5_semillas.csv"
    per_seed_df.to_csv(p07, index=False)
    exported["07_estabilidad_5_semillas"] = p07

    p08 = tab_dir / "08_asignacion_clusters_personas_352093.csv"
    cols_p = ["resume_id", "split", "cluster", "nombre_segmento"] + person_bundle.feature_cols + [
        "any_repeated_posthoc",
        "tasa_reincide_persona_posthoc",
        "isco_major_modal_posthoc",
    ]
    person_bundle.df_full_assigned[cols_p].to_csv(p08, index=False)
    exported["08_asignacion_personas"] = p08

    p09 = tab_dir / "09_comparacion_sensibilidad_version_b_vs_version_a.csv"
    ab_summary_df.to_csv(p09, index=False)
    exported["09_comparacion_b_vs_a"] = p09

    return exported
