"""Publication-grade visualizations (Spanish titles/labels, 300 DPI) and CSV table exports for Agglomerative Hierarchical Clustering."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.cluster.hierarchy import dendrogram
from sklearn.decomposition import PCA

from .config import HierarchicalClusteringConfig
from .hierarchical_engine import HierarchicalAnalysisBundle


CLUSTER_PALETTE: List[str] = ["#1F77B4", "#2CA02C", "#FF7F0E", "#D62728", "#9467BD", "#8C564B"]


def generate_all_hierarchical_figures(
    person_bundle: HierarchicalAnalysisBundle,
    exp_bundle: HierarchicalAnalysisBundle,
    per_seed_df: pd.DataFrame,
    ab_summary_df: pd.DataFrame,
    config: HierarchicalClusteringConfig,
) -> List[Path]:
    """Generate all 7 required 300-DPI PNG figures with Spanish (or English) titles and labels."""
    sns.set_theme(style="whitegrid")
    saved_paths: List[Path] = []
    fig_dir = config.figures_dir
    lang = config.plot_lang

    # 1. Figure 01: Full leaf-level dendrogram on stratified micro-sample (n = 60)
    p1 = fig_dir / "01_dendrograma_micro_muestra_n60_ward.png"
    fig, ax = plt.subplots(figsize=(13, 5.8), dpi=300)
    cut_micro = 0.65 * float(np.max(person_bundle.Z_micro_ward[:, 2]))
    dendrogram(
        person_bundle.Z_micro_ward,
        ax=ax,
        leaf_rotation=90.0,
        leaf_font_size=8.5,
        color_threshold=cut_micro,
    )
    ax.axhline(y=cut_micro, color="#D62728", linestyle="--", linewidth=1.8, label=f"Umbral visual de corte ({cut_micro:.2f})")
    if lang == "es":
        ax.set_title(
            "Dendrograma Jerárquico Aglomerativo · Linkage Ward (Micro-Muestra Estratificada n = 60 Personas)",
            fontsize=13,
            fontweight="bold",
        )
        ax.set_xlabel("Observaciones individuales de la micro-muestra (personas con oficio clasificado ESCO)", fontsize=11)
        ax.set_ylabel("Distancia de fusión de Ward (escala estandarizada StandardScaler)", fontsize=11)
    else:
        ax.set_title("Agglomerative Hierarchical Dendrogram · Ward Linkage (Stratified Micro-Sample n = 60)", fontsize=13, fontweight="bold")
        ax.set_xlabel("Individual observations in micro-sample (classified persons)", fontsize=11)
        ax.set_ylabel("Ward fusion distance (standardized scale)", fontsize=11)
    ax.legend(loc="upper right", frameon=True)
    fig.tight_layout()
    fig.savefig(p1, dpi=300)
    plt.close(fig)
    saved_paths.append(p1)

    # 2. Figure 02: Truncated discovery dendrogram (n = 3,000, lastp = 30) with optimal cut k*
    p2 = fig_dir / "02_dendrograma_truncado_n3000_corte_optimo.png"
    fig, ax = plt.subplots(figsize=(13, 6.2), dpi=300)
    Z_disc_ward = person_bundle.Z_discovery_by_method["ward"]
    cut_h = person_bundle.optimal_cut_height
    k_opt = person_bundle.k_opt
    dendrogram(
        Z_disc_ward,
        ax=ax,
        truncate_mode="lastp",
        p=30,
        show_leaf_counts=True,
        leaf_rotation=45.0,
        leaf_font_size=9.0,
        color_threshold=cut_h,
    )
    ax.axhline(
        y=cut_h,
        color="#D62728",
        linestyle="--",
        linewidth=2.2,
        label=f"Corte horizontal óptimo: k = {k_opt} clústeres (altura Ward = {cut_h:.2f})",
    )
    if lang == "es":
        ax.set_title(
            f"Dendrograma Truncado (30 Ramas Superiores · Muestra de Descubrimiento n = 3,000 Personas · Corte Óptimo k = {k_opt})",
            fontsize=13,
            fontweight="bold",
        )
        ax.set_xlabel("Ramas terminales truncadas (entre paréntesis: número de personas agrupadas en la rama)", fontsize=11)
        ax.set_ylabel("Distancia de fusión de Ward (incremento de varianza intra-clúster ΔESS)", fontsize=11)
    else:
        ax.set_title(f"Truncated Dendrogram (Top 30 Branches · Discovery Sample n = 3,000 · Optimal Cut k = {k_opt})", fontsize=13, fontweight="bold")
        ax.set_xlabel("Truncated terminal branches (in parentheses: number of grouped persons)", fontsize=11)
        ax.set_ylabel("Ward fusion distance (Δ within-cluster variance)", fontsize=11)
    ax.legend(loc="upper right", frameon=True, fontsize=10.5)
    fig.tight_layout()
    fig.savefig(p2, dpi=300)
    plt.close(fig)
    saved_paths.append(p2)

    # 3. Figure 03: Linkage methods comparison (ward, complete, average, single)
    p3 = fig_dir / "03_comparacion_metodos_linkage_metricas.png"
    lt_df = person_bundle.linkage_tournament_df
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8), dpi=300)
    colors_lt = ["#2CA02C" if m == "ward" else "#7F7F7F" for m in lt_df["metodo_linkage"]]

    axes[0].bar(lt_df["metodo_linkage"], lt_df["correlacion_cofenetica"], color=colors_lt, edgecolor="black")
    axes[0].set_title("Correlación Cofenética (cophenet)", fontsize=11.5, fontweight="bold")
    axes[0].set_xlabel("Método de linkage", fontsize=10.5)
    axes[0].set_ylabel("Correlación cofenética", fontsize=10.5)
    for idx, val in enumerate(lt_df["correlacion_cofenetica"]):
        axes[0].text(idx, val + 0.01, f"{val:.4f}", ha="center", fontsize=9.5, fontweight="bold")
    axes[0].set_ylim(0, 1.05)

    axes[1].bar(lt_df["metodo_linkage"], lt_df["silhouette_score"], color=colors_lt, edgecolor="black")
    axes[1].set_title(f"Coeficiente de Silueta (k = {k_opt})", fontsize=11.5, fontweight="bold")
    axes[1].set_xlabel("Método de linkage", fontsize=10.5)
    axes[1].set_ylabel("Silhouette Score", fontsize=10.5)
    for idx, val in enumerate(lt_df["silhouette_score"]):
        axes[1].text(idx, val + 0.01, f"{val:.4f}", ha="center", fontsize=9.5, fontweight="bold")
    axes[1].set_ylim(0, max(0.85, float(lt_df["silhouette_score"].max()) + 0.12))

    axes[2].bar(lt_df["metodo_linkage"], lt_df["pct_cluster_mas_grande"], color=colors_lt, edgecolor="black")
    axes[2].axhline(y=90.0, color="#D62728", linestyle="--", linewidth=1.5, label="Alerta de encadenamiento (>90%)")
    axes[2].set_title("% en el Clúster Más Grande (Balance)", fontsize=11.5, fontweight="bold")
    axes[2].set_xlabel("Método de linkage", fontsize=10.5)
    axes[2].set_ylabel("% de observaciones en el clúster mayor", fontsize=10.5)
    for idx, val in enumerate(lt_df["pct_cluster_mas_grande"]):
        axes[2].text(idx, val + 1.5, f"{val:.1f}%", ha="center", fontsize=9.5, fontweight="bold")
    axes[2].set_ylim(0, 112)
    axes[2].legend(loc="upper left", fontsize=8.5)

    fig.suptitle(
        "Torneo de Criterios de Linkage en Muestra Estandarizada (n = 3,000 Personas · Ward Seleccionado por Equilibrio y Varianza)",
        fontsize=13,
        fontweight="bold",
        y=1.02,
    )
    fig.tight_layout()
    fig.savefig(p3, dpi=300, bbox_inches="tight")
    plt.close(fig)
    saved_paths.append(p3)

    # 4. Figure 04: Silhouette, Davies-Bouldin, and Vertical Merge Jumps across k = 2..8
    p4 = fig_dir / "04_curvas_silueta_y_davies_bouldin_k2_a_k8.png"
    cuts_df = person_bundle.cuts_evaluation_df
    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.8), dpi=300)

    axes[0].plot(cuts_df["k_clusters"], cuts_df["salto_vertical_fusion"], marker="o", linewidth=2.2, color="#1F77B4")
    axes[0].axvline(x=k_opt, color="#D62728", linestyle="--", linewidth=1.8, label=f"Corte elegido k = {k_opt}")
    axes[0].set_title("Salto Vertical de Fusión Ward (Δ Altura)", fontsize=11.5, fontweight="bold")
    axes[0].set_xlabel("Número de clústeres (k)", fontsize=10.5)
    axes[0].set_ylabel("Salto de distancia Ward al fusionar k → k-1", fontsize=10.5)
    axes[0].legend(loc="upper right")

    axes[1].plot(cuts_df["k_clusters"], cuts_df["silhouette_score"], marker="s", linewidth=2.2, color="#2CA02C")
    axes[1].axvline(x=k_opt, color="#D62728", linestyle="--", linewidth=1.8, label=f"Corte elegido k = {k_opt}")
    axes[1].set_title("Coeficiente de Silueta Promedio vs. k", fontsize=11.5, fontweight="bold")
    axes[1].set_xlabel("Número de clústeres (k)", fontsize=10.5)
    axes[1].set_ylabel("Silhouette Score s(k) (mayor es mejor)", fontsize=10.5)
    axes[1].legend(loc="upper right")

    axes[2].plot(cuts_df["k_clusters"], cuts_df["davies_bouldin_index"], marker="^", linewidth=2.2, color="#FF7F0E")
    axes[2].axvline(x=k_opt, color="#D62728", linestyle="--", linewidth=1.8, label=f"Corte elegido k = {k_opt}")
    axes[2].set_title("Índice de Davies-Bouldin vs. k", fontsize=11.5, fontweight="bold")
    axes[2].set_xlabel("Número de clústeres (k)", fontsize=10.5)
    axes[2].set_ylabel("Davies-Bouldin Index (menor es mejor)", fontsize=10.5)
    axes[2].legend(loc="upper right")

    fig.suptitle(
        "Evaluación Cuantitativa del Corte Horizontal del Dendrograma Ward (k = 2..8 · Vista Personas n = 3,000)",
        fontsize=13,
        fontweight="bold",
        y=1.02,
    )
    fig.tight_layout()
    fig.savefig(p4, dpi=300, bbox_inches="tight")
    plt.close(fig)
    saved_paths.append(p4)

    # 5. Figure 05: 2D PCA Projection of Hierarchical Clusters (Person View & Experience View)
    p5 = fig_dir / "05_proyeccion_pca_2d_clusters_jerarquicos.png"
    fig, (ax_p, ax_e) = plt.subplots(1, 2, figsize=(14.5, 6.2), dpi=300)

    for ax, bundle, subtitle_es in (
        (ax_p, person_bundle, "Vista Primaria · Trayectorias por Persona (n = 3,000)"),
        (ax_e, exp_bundle, "Vista Secundaria · Experiencias Laborales (n = 3,000)"),
    ):
        pca = PCA(n_components=2, random_state=config.random_state)
        coords = pca.fit_transform(bundle.X_discovery_scaled)
        v1 = pca.explained_variance_ratio_[0] * 100.0
        v2 = pca.explained_variance_ratio_[1] * 100.0
        labels = bundle.df_discovery["cluster"].to_numpy()
        names_map = dict(zip(bundle.profile_df["cluster"], bundle.profile_df["nombre_segmento_es"]))

        for cid in sorted(np.unique(labels)):
            mask = labels == cid
            color = CLUSTER_PALETTE[int(cid) % len(CLUSTER_PALETTE)]
            short_name = names_map.get(int(cid), f"Clúster {cid}")
            ax.scatter(
                coords[mask, 0],
                coords[mask, 1],
                s=18,
                alpha=0.55,
                color=color,
                label=f"C{cid}: {short_name[:42]}...",
            )
            centroid_xy = coords[mask].mean(axis=0)
            ax.scatter(
                centroid_xy[0],
                centroid_xy[1],
                s=260,
                marker="*",
                color=color,
                edgecolor="black",
                linewidth=1.5,
                zorder=10,
            )

        ax.set_title(f"{subtitle_es}\nVarianza explicada PC1+PC2 = {v1 + v2:.1f}%", fontsize=11.5, fontweight="bold")
        ax.set_xlabel(f"Componente Principal 1 ({v1:.1f}% varianza)", fontsize=10.5)
        ax.set_ylabel(f"Componente Principal 2 ({v2:.1f}% varianza)", fontsize=10.5)
        ax.legend(loc="best", frameon=True, fontsize=8.5)

    fig.suptitle(
        "Proyección PCA 2D de los Clústeres Jerárquicos Aglomerativos (Linkage Ward · k = 4 · Centroides *)",
        fontsize=13,
        fontweight="bold",
        y=1.02,
    )
    fig.tight_layout()
    fig.savefig(p5, dpi=300, bbox_inches="tight")
    plt.close(fig)
    saved_paths.append(p5)

    # 6. Figure 06: Original-scale cluster profiles & post-hoc reincide rate
    p6 = fig_dir / "06_perfiles_clusters_escala_original_y_reincide.png"
    prof_p = person_bundle.profile_df
    fig, axes = plt.subplots(1, 3, figsize=(14.8, 5.0), dpi=300)
    c_labels = [f"Clúster {c}" for c in prof_p["cluster"]]
    c_colors = [CLUSTER_PALETTE[int(c) % len(CLUSTER_PALETTE)] for c in prof_p["cluster"]]

    axes[0].bar(c_labels, prof_p["n_jobs_media_total"], color=c_colors, edgecolor="black")
    axes[0].set_title("Promedio de Empleos por Persona (Escala Real)", fontsize=11, fontweight="bold")
    axes[0].set_ylabel("Número medio de empleos (n_jobs)", fontsize=10)
    for idx, val in enumerate(prof_p["n_jobs_media_total"]):
        axes[0].text(idx, val + 0.12, f"{val:.2f}", ha="center", fontsize=9.5, fontweight="bold")

    axes[1].bar(c_labels, prof_p["mean_skills_essential_media_total"], color=c_colors, edgecolor="black")
    axes[1].set_title("Competencias ESCO Esenciales Medias (Escala Real)", fontsize=11, fontweight="bold")
    axes[1].set_ylabel("Conteo medio de competencias esenciales", fontsize=10)
    for idx, val in enumerate(prof_p["mean_skills_essential_media_total"]):
        axes[1].text(idx, val + 0.4, f"{val:.2f}", ha="center", fontsize=9.5, fontweight="bold")

    axes[2].bar(c_labels, prof_p["tasa_reincide_test_posthoc_pct"], color=c_colors, edgecolor="black")
    base_te_pct = float(
        (person_bundle.df_full_assigned.loc[person_bundle.df_full_assigned["split"] == "test", "any_repeated_posthoc"].mean())
        * 100.0
    )
    axes[2].axhline(
        y=base_te_pct,
        color="#D62728",
        linestyle="--",
        linewidth=1.8,
        label=f"Tasa base Test ({base_te_pct:.2f}%)",
    )
    axes[2].set_title("Validación Post-Hoc: % Personas que Repiten Oficio (Test)", fontsize=11, fontweight="bold")
    axes[2].set_ylabel("Tasa post-hoc de repetición ocupacional (%)", fontsize=10)
    for idx, val in enumerate(prof_p["tasa_reincide_test_posthoc_pct"]):
        lift_v = prof_p["lift_reincide_test_posthoc"].iloc[idx]
        axes[2].text(idx, val + 1.2, f"{val:.1f}%\n({lift_v:.2f}x)", ha="center", fontsize=9, fontweight="bold")
    axes[2].set_ylim(0, min(105.0, float(prof_p["tasa_reincide_test_posthoc_pct"].max()) + 18.0))
    axes[2].legend(loc="upper right", fontsize=9)

    fig.suptitle(
        "Retrato Robot en Escala Original y Tasa Post-Hoc de Repetición Ocupacional por Clúster Jerárquico (352,093 Personas)",
        fontsize=12.8,
        fontweight="bold",
        y=1.03,
    )
    fig.tight_layout()
    fig.savefig(p6, dpi=300, bbox_inches="tight")
    plt.close(fig)
    saved_paths.append(p6)

    # 7. Figure 07: 5-Seed Stability & Version B vs Version A Sensitivity
    p7 = fig_dir / "07_sensibilidad_version_b_vs_version_a_5_semillas.png"
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.0), dpi=300)
    x_pos = np.arange(len(per_seed_df))
    width = 0.36
    seed_labels = [f"Semilla {s}" for s in per_seed_df["semilla"]]

    ax1.bar(x_pos - width / 2, per_seed_df["silhouette_version_b"], width=width, color="#2CA02C", edgecolor="black", label="Versión B · SIN outliers (Primaria)")
    ax1.bar(x_pos + width / 2, per_seed_df["silhouette_version_a"], width=width, color="#1F77B4", edgecolor="black", label="Versión A · CON outliers (Sensibilidad)")
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(seed_labels)
    ax1.set_title("Estabilidad del Coeficiente de Silueta en 5 Semillas (k = 4)", fontsize=11.5, fontweight="bold")
    ax1.set_ylabel("Silhouette Score", fontsize=10.5)
    ax1.legend(loc="lower right", fontsize=9)

    ax2.bar(x_pos - width / 2, per_seed_df["davies_bouldin_version_b"], width=width, color="#2CA02C", edgecolor="black", label="Versión B · SIN outliers (Primaria)")
    ax2.bar(x_pos + width / 2, per_seed_df["davies_bouldin_version_a"], width=width, color="#FF7F0E", edgecolor="black", label="Versión A · CON outliers (Sensibilidad)")
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(seed_labels)
    ax2.set_title("Estabilidad del Índice Davies-Bouldin en 5 Semillas (k = 4)", fontsize=11.5, fontweight="bold")
    ax2.set_ylabel("Davies-Bouldin Index (menor es mejor)", fontsize=10.5)
    ax2.legend(loc="lower right", fontsize=9)

    fig.suptitle(
        "Sensibilidad Versión B (SIN outliers) vs. Versión A (CON outliers) en 5 Semillas Estratificadas (n = 3,000 Personas/Semilla)",
        fontsize=12.8,
        fontweight="bold",
        y=1.02,
    )
    fig.tight_layout()
    fig.savefig(p7, dpi=300, bbox_inches="tight")
    plt.close(fig)
    saved_paths.append(p7)

    return saved_paths


def export_all_hierarchical_tables(
    data_usage_df: pd.DataFrame,
    person_bundle: HierarchicalAnalysisBundle,
    exp_bundle: HierarchicalAnalysisBundle,
    per_seed_df: pd.DataFrame,
    ab_summary_df: pd.DataFrame,
    config: HierarchicalClusteringConfig,
) -> Dict[str, Path]:
    """Export all 9 required CSV tables to reports/clustering_jerarquico_jobpath/tables/."""
    tab_dir = config.tables_dir
    exported: Dict[str, Path] = {}

    p01 = tab_dir / "01_uso_de_datos_y_estrategia_muestreo.csv"
    data_usage_df.to_csv(p01, index=False)
    exported["01_uso_de_datos"] = p01

    p02 = tab_dir / "02_torneo_metodos_linkage_cophenet_silueta_dbi.csv"
    person_bundle.linkage_tournament_df.to_csv(p02, index=False)
    exported["02_torneo_linkage"] = p02

    p03 = tab_dir / "03_evaluacion_cortes_k2_a_k8_saltos_y_metricas.csv"
    person_bundle.cuts_evaluation_df.to_csv(p03, index=False)
    exported["03_evaluacion_cortes"] = p03

    p04 = tab_dir / "04_estabilidad_5_semillas_muestreo_jerarquico.csv"
    per_seed_df.to_csv(p04, index=False)
    exported["04_estabilidad_5_semillas"] = p04

    p05 = tab_dir / "05_perfiles_clusters_personas_escala_original.csv"
    person_bundle.profile_df.to_csv(p05, index=False)
    exported["05_perfiles_personas"] = p05

    p06 = tab_dir / "06_perfiles_clusters_experiencias_escala_original.csv"
    exp_bundle.profile_df.to_csv(p06, index=False)
    exported["06_perfiles_experiencias"] = p06

    p07 = tab_dir / "07_asignacion_clusters_muestra_descubrimiento.csv"
    cols_disc = ["resume_id", "split", "cluster", "nombre_segmento"] + person_bundle.feature_cols + [
        "any_repeated_posthoc",
        "tasa_reincide_persona_posthoc",
        "isco_major_modal_posthoc",
    ]
    person_bundle.df_discovery[cols_disc].to_csv(p07, index=False)
    exported["07_asignacion_muestra"] = p07

    p08 = tab_dir / "08_asignacion_clusters_personas_completo_nearest_centroid.csv"
    cols_full = ["resume_id", "split", "cluster", "nombre_segmento", "n_jobs", "span_q", "dur_mean", "any_repeated_posthoc"]
    person_bundle.df_full_assigned[cols_full].to_csv(p08, index=False)
    exported["08_asignacion_completa"] = p08

    p09 = tab_dir / "09_comparacion_sensibilidad_version_b_vs_version_a.csv"
    ab_summary_df.to_csv(p09, index=False)
    exported["09_comparacion_b_vs_a"] = p09

    return exported
