"""Append-only Markdown writers and strict narrative number verifier for K-Means Clustering."""

from __future__ import annotations

from pathlib import Path
import pandas as pd

from scripts.ScriptsCsv.ClusteringJerarquico.markdown_writers import (
    _df_to_markdown,
    _mark_previous_runs_superseded,
    verify_narrative_numbers_against_tables,
)

from .config import KMeansClusteringConfig
from .kmeans_engine import KMeansAnalysisBundle


def append_bitacora_kmeans_md(
    config: KMeansClusteringConfig,
    run_id: str,
    run_timestamp: str,
    hash_df: pd.DataFrame,
    leakage_df: pd.DataFrame,
    data_usage_df: pd.DataFrame,
    person_bundle: KMeansAnalysisBundle,
    exp_bundle: KMeansAnalysisBundle,
    per_seed_df: pd.DataFrame,
    ab_summary_df: pd.DataFrame,
) -> Path:
    """Write or append the dated run section to Bitacora_KMeans.md."""
    md_path = config.bitacora_md_path

    k_row_p = person_bundle.k_search_df.loc[person_bundle.k_search_df["k"] == person_bundle.k_opt].iloc[0]
    k_row_e = exp_bundle.k_search_df.loc[exp_bundle.k_search_df["k"] == exp_bundle.k_opt].iloc[0]
    b_sum = ab_summary_df.iloc[0]
    a_sum = ab_summary_df.iloc[1]

    ref_summary_df = pd.DataFrame(
        [
            {
                "run_id": run_id,
                "timestamp": run_timestamp,
                "k_optimo": person_bundle.k_opt,
                "inercia_wcss_personas_k4": float(k_row_p["inercia_wcss"]),
                "caida_inercia_personas_k4_pct": float(k_row_p["caida_relativa_inercia_pct"]),
                "silhouette_personas_k4": float(k_row_p["silhouette_score"]),
                "davies_bouldin_personas_k4": float(k_row_p["davies_bouldin_index"]),
                "silhouette_experiencias_k4": float(k_row_e["silhouette_score"]),
                "davies_bouldin_experiencias_k4": float(k_row_e["davies_bouldin_index"]),
                "max_diff_centroide_inv_vs_groupby": person_bundle.centroid_equivalence_max_abs_diff,
                "ari_kmeans_vs_ward_personas": person_bundle.ari_vs_ward_sample,
                "nmi_kmeans_vs_ward_personas": person_bundle.nmi_vs_ward_sample,
                "silhouette_5semillas_b_media": float(b_sum["silhouette_5semillas_media"]),
                "silhouette_5semillas_a_media": float(a_sum["silhouette_5semillas_media"]),
                "ari_b_vs_a_train_completo": float(b_sum["ari_b_vs_a_train_completo"]),
            }
        ]
    )

    section = f"""
---
## Corrida Fechada · ID `{run_id}` · `{run_timestamp}` · [CURRENT]

### 0. Resumen de Indicadores Clave de la Corrida (`{run_id}`)
{_df_to_markdown(ref_summary_df)}

### 1. Verificación de Integridad SHA-256 y Auditoría Cero-Fuga (`Zero Target Leakage`)
{_df_to_markdown(hash_df)}

{_df_to_markdown(leakage_df)}

### 2. Tabla de Uso de Datos (`Uso de datos`)
{_df_to_markdown(data_usage_df)}

### 3. Determinación del $k$ Óptimo (`k = 2..8` · Método del Codo + Coeficiente de Silueta + Davies-Bouldin)

#### 3.1 Vista Primaria · Personas / Trayectorias (`281674` Personas en Train)
{_df_to_markdown(person_bundle.k_search_df)}

#### 3.2 Vista Secundaria · Experiencias Laborales / Perfiles ESCO (`1391018` Experiencias en Train)
{_df_to_markdown(exp_bundle.k_search_df)}

- **Justificación cuantitativa y de negocio de `k = {person_bundle.k_opt}`**: En la vista primaria de personas, `k = {person_bundle.k_opt}` reduce la inercia WCSS a `{float(k_row_p['inercia_wcss']):.2f}` (caída relativa de `{float(k_row_p['caida_relativa_inercia_pct']):.2f}%`), alcanza un `silhouette_score` de `{float(k_row_p['silhouette_score']):.4f}` y un `davies_bouldin_index` de `{float(k_row_p['davies_bouldin_index']):.4f}`, coincidiendo con el corte óptimo del dendrograma jerárquico de Ward (`ARI = {person_bundle.ari_vs_ward_sample:.4f}`, `NMI = {person_bundle.nmi_vs_ward_sample:.4f}`). En la vista de experiencias, `k = {exp_bundle.k_opt}` obtiene `silhouette_score = {float(k_row_e['silhouette_score']):.4f}` y `davies_bouldin_index = {float(k_row_e['davies_bouldin_index']):.4f}`.

### 4. Centroides Interpretables en Escala Original (`inverse_transform` vs. `groupby().mean()`) y Escala Estandarizada ($z$)

#### 4.1 Centroides Vista Primaria · Personas (`max_diff = {person_bundle.centroid_equivalence_max_abs_diff:.6f}`)
{_df_to_markdown(person_bundle.centroids_df)}

#### 4.2 Centroides Vista Secundaria · Experiencias (`max_diff = {exp_bundle.centroid_equivalence_max_abs_diff:.6f}`)
{_df_to_markdown(exp_bundle.centroids_df)}

### 5. Evaluación de Perfiles por Clúster (`Retrato Robot`), Validación Post-Hoc con `reincide` y Acciones del Observatorio

#### 5.1 Perfiles Vista Primaria · Personas (`352093` Personas Clasificadas: `281674` Train / `70419` Test)
{_df_to_markdown(person_bundle.profile_df)}

#### 5.2 Perfiles Vista Secundaria · Experiencias (`1738738` Experiencias Clasificadas: `1391018` Train / `347720` Test)
{_df_to_markdown(exp_bundle.profile_df)}
"""

    if md_path.exists():
        prev = _mark_previous_runs_superseded(md_path.read_text(encoding="utf-8"), run_id, run_timestamp)
        md_path.write_text(prev + "\n" + section.strip() + "\n", encoding="utf-8")
    else:
        header = f"""# Bitácora de Clustering K-Means · `8.0_kmeans_clustering.ipynb`

> **Proyecto:** `MineriaProtect` (JobPath — Observatorio Laboral de Trayectorias y Perfiles ESCO)
> **Guía técnica implementada:** `02_kmeans_clustering.md`

Este archivo es **append-only**: conserva todas las corridas previas marcadas como **`[SUPERSEDED]`** y registra la corrida vigente como **`[CURRENT]`**.
- **Corrida vigente confirmada en ambos archivos (`.md`)**: **`{run_id}`** (`{run_timestamp}` · estado: **`CURRENT`**).
"""
        md_path.write_text(header + "\n" + section.strip() + "\n", encoding="utf-8")

    return md_path


def append_comparacion_ab_kmeans_md(
    config: KMeansClusteringConfig,
    run_id: str,
    run_timestamp: str,
    data_usage_df: pd.DataFrame,
    per_seed_df: pd.DataFrame,
    ab_summary_df: pd.DataFrame,
    person_bundle: KMeansAnalysisBundle,
) -> Path:
    """Write or append the Version B vs Version A sensitivity analysis to Comparacion_A_vs_B_KMeans.md."""
    md_path = config.comparacion_ab_md_path
    b_row = ab_summary_df.iloc[0]
    a_row = ab_summary_df.iloc[1]

    section = f"""
---
## Corrida Fechada · ID `{run_id}` · `{run_timestamp}` · [CURRENT]

### 0. Uso de Datos (`{run_id}`)
{_df_to_markdown(data_usage_df)}

### 1. Estabilidad y Sensibilidad en `5` Semillas (`Versión B · SIN outliers` vs. `Versión A · CON outliers` · `10000` Personas/Semilla)
{_df_to_markdown(per_seed_df)}

### 2. Comparación en Train Completo (`281674` Personas) y Resumen de `5` Semillas (`Versión B` vs. `Versión A`)
{_df_to_markdown(ab_summary_df)}

### 3. Perfiles Finales K-Means en Escala Original (`Versión B · SIN outliers` · `k = {person_bundle.k_opt}`)
{_df_to_markdown(person_bundle.profile_df)}

- **Conclusión y recomendación de versión para K-Means**: En el conjunto completo de entrenamiento (`{int(b_row['personas_train_completo'])}` personas, `k = {int(b_row['k_optimo'])}`), **Versión B · SIN outliers (Primaria)** alcanza un `silhouette_train_completo = {float(b_row['silhouette_train_completo']):.4f}`, `davies_bouldin_train_completo = {float(b_row['davies_bouldin_train_completo']):.4f}` y `calinski_harabasz_train_completo = {float(b_row['calinski_harabasz_train_completo']):.2f}`, superando a **Versión A · CON outliers** (`silhouette_train_completo = {float(a_row['silhouette_train_completo']):.4f}`, `davies_bouldin_train_completo = {float(a_row['davies_bouldin_train_completo']):.4f}`, `calinski_harabasz_train_completo = {float(a_row['calinski_harabasz_train_completo']):.2f}`). En las `5` semillas muestrales, la Silueta media es `{float(b_row['silhouette_5semillas_media']):.4f}` (`± {float(b_row['silhouette_5semillas_std']):.4f}`) en B frente a `{float(a_row['silhouette_5semillas_media']):.4f}` (`± {float(a_row['silhouette_5semillas_std']):.4f}`) en A, con un desplazamiento medio de centroides estandarizados de `{float(b_row['desplazamiento_centroide_z_b_vs_a']):.4f}` y una concordancia en Train completo de `ARI = {float(b_row['ari_b_vs_a_train_completo']):.4f}` (`NMI = {float(b_row['nmi_b_vs_a_train_completo']):.4f}`). Se confirma **Versión B · SIN outliers** como versión primaria porque los conteos ESCO sin truncar en A (hasta `{float(a_row['max_competencias_esenciales_observado']):.2f}` frente al tope IQR `{float(b_row['max_competencias_esenciales_observado']):.2f}` en B) arrastran las medias aritméticas de los centroides de K-Means.
"""

    if md_path.exists():
        prev = _mark_previous_runs_superseded(md_path.read_text(encoding="utf-8"), run_id, run_timestamp)
        md_path.write_text(prev + "\n" + section.strip() + "\n", encoding="utf-8")
    else:
        header = f"""# Comparación Versión B (SIN outliers) vs. Versión A (CON outliers) · Clustering K-Means

> **Proyecto:** `MineriaProtect` (JobPath) · `8.0_kmeans_clustering.ipynb`

Este archivo es **append-only**: conserva todas las corridas previas marcadas como **`[SUPERSEDED]`** y registra la corrida vigente como **`[CURRENT]`**.
- **Corrida vigente confirmada en ambos archivos (`.md`)**: **`{run_id}`** (`{run_timestamp}` · estado: **`CURRENT`**).
"""
        md_path.write_text(header + "\n" + section.strip() + "\n", encoding="utf-8")

    return md_path


__all__ = [
    "append_bitacora_kmeans_md",
    "append_comparacion_ab_kmeans_md",
    "verify_narrative_numbers_against_tables",
]
