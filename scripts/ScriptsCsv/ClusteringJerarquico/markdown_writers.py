"""Append-only Markdown writers and strict narrative number verifier for Agglomerative Hierarchical Clustering."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Set

import pandas as pd

from .config import HierarchicalClusteringConfig
from .hierarchical_engine import HierarchicalAnalysisBundle


def _df_to_markdown(df: pd.DataFrame) -> str:
    """Render a DataFrame as a GitHub-flavored Markdown table without external dependencies."""
    cols = [str(c) for c in df.columns]
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    body_lines = []
    for _, row in df.iterrows():
        vals = []
        for v in row:
            if isinstance(v, float):
                if v.is_integer():
                    vals.append(f"{int(v)}")
                else:
                    vals.append(f"{v:.4f}".rstrip("0").rstrip(".") if abs(v) < 1000 else f"{v:.2f}")
            else:
                vals.append(str(v))
        body_lines.append("| " + " | ".join(vals) + " |")
    return "\n".join([header, sep] + body_lines)


def _mark_previous_runs_superseded(existing_text: str, new_run_id: str, new_timestamp: str) -> str:
    """Mark any previous [CURRENT] section in an existing append-only .md file as [SUPERSEDED]."""
    updated = existing_text.replace("· [CURRENT]", "· [SUPERSEDED]")
    updated = updated.replace("estado: **`CURRENT`**", "estado: **`SUPERSEDED`**")
    updated = re.sub(
        r"- \*\*Corrida vigente confirmada en ambos archivos \(`\.md`\)\*\*:.*",
        f"- **Corrida vigente confirmada en ambos archivos (`.md`)**: **`{new_run_id}`** (`{new_timestamp}` · estado: **`CURRENT`**).",
        updated,
    )
    return updated


def append_bitacora_jerarquico_md(
    config: HierarchicalClusteringConfig,
    run_id: str,
    run_timestamp: str,
    hash_df: pd.DataFrame,
    leakage_df: pd.DataFrame,
    data_usage_df: pd.DataFrame,
    person_bundle: HierarchicalAnalysisBundle,
    exp_bundle: HierarchicalAnalysisBundle,
    per_seed_df: pd.DataFrame,
    ab_summary_df: pd.DataFrame,
) -> Path:
    """Write or append the dated run section to Bitacora_Clustering_Jerarquico.md."""
    md_path = config.bitacora_md_path
    lt_df = person_bundle.linkage_tournament_df
    ward_row = lt_df.loc[lt_df["metodo_linkage"] == "ward"].iloc[0]
    single_row = lt_df.loc[lt_df["metodo_linkage"] == "single"].iloc[0]
    cuts_df = person_bundle.cuts_evaluation_df
    cut_row = cuts_df.loc[cuts_df["k_clusters"] == person_bundle.k_opt].iloc[0]

    b_sum = ab_summary_df.iloc[0]
    a_sum = ab_summary_df.iloc[1]

    ref_summary_df = pd.DataFrame(
        [
            {
                "run_id": run_id,
                "timestamp": run_timestamp,
                "k_optimo": person_bundle.k_opt,
                "altura_corte_ward_personas": person_bundle.optimal_cut_height,
                "salto_vertical_k_optimo": float(cut_row["salto_vertical_fusion"]),
                "cophenet_ward_personas": float(ward_row["correlacion_cofenetica"]),
                "silhouette_ward_personas": float(ward_row["silhouette_score"]),
                "davies_bouldin_ward_personas": float(ward_row["davies_bouldin_index"]),
                "pct_max_cluster_single_chaining": float(single_row["pct_cluster_mas_grande"]),
                "ari_ward_vs_kmeans_muestra": person_bundle.ari_vs_kmeans,
                "nmi_ward_vs_kmeans_muestra": person_bundle.nmi_vs_kmeans,
                "silhouette_5semillas_b_media": float(b_sum["silhouette_media"]),
                "silhouette_5semillas_b_std": float(b_sum["silhouette_std"]),
                "silhouette_5semillas_a_media": float(a_sum["silhouette_media"]),
                "ari_b_vs_a_5semillas_media": float(b_sum["ari_b_vs_a_media"]),
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

### 2. Tabla de Uso de Datos y Estrategia de Muestreo Jerárquico en 3 Niveles ($O(n^2)$)
{_df_to_markdown(data_usage_df)}

### 3. Torneo de Métodos de Linkage (`ward`, `complete`, `average`, `single`) en Muestra de Descubrimiento (`n = {config.discovery_sample_n}`)
{_df_to_markdown(lt_df)}

- **Lectura del torneo de linkage**: En la muestra estratificada de `{config.discovery_sample_n}` personas de Train (`k = {person_bundle.k_opt}`), el método `ward` obtiene una correlación cofenética de `{float(ward_row['correlacion_cofenetica']):.4f}`, un `silhouette_score` de `{float(ward_row['silhouette_score']):.4f}` y un `davies_bouldin_index` de `{float(ward_row['davies_bouldin_index']):.4f}`, manteniendo el clúster más grande en `{float(ward_row['pct_cluster_mas_grande']):.2f}%` de la muestra. En contraste, `single` sufre de encadenamiento severo (`{float(single_row['pct_cluster_mas_grande']):.2f}%` concentrado en un solo clúster). Se selecciona **`ward`** por equilibrar cohesión intra-clúster y tamaños operativos.

### 4. Evaluación del Corte Horizontal Óptimo del Dendrograma Ward (`k = 2..8`)
{_df_to_markdown(cuts_df)}

- **Justificación del corte óptimo `k = {person_bundle.k_opt}`**: En `k = {person_bundle.k_opt}`, la altura de corte horizontal recomendada es `{person_bundle.optimal_cut_height:.3f}` (entre las fusiones `{float(cut_row['altura_fusion_inferior_ward']):.3f}` y `{float(cut_row['altura_fusion_superior_ward']):.3f}`, con salto vertical `{float(cut_row['salto_vertical_fusion']):.3f}`), alcanzando `silhouette_score = {float(cut_row['silhouette_score']):.4f}`, `davies_bouldin_index = {float(cut_row['davies_bouldin_index']):.4f}` y concordancia frente a K-Means de `ARI = {person_bundle.ari_vs_kmeans:.4f}` (`NMI = {person_bundle.nmi_vs_kmeans:.4f}`).

### 5. Perfiles de los Clústeres en Escala Original (`Retrato Robot`) y Validación Post-Hoc con `reincide`

#### 5.1 Vista Primaria · Trayectorias por Persona (`352093` Personas Clasificadas)
{_df_to_markdown(person_bundle.profile_df)}

#### 5.2 Vista Secundaria · Experiencias Laborales / Perfiles de Exigencia ESCO (`1738738` Experiencias Clasificadas)
{_df_to_markdown(exp_bundle.profile_df)}
"""

    if md_path.exists():
        prev = _mark_previous_runs_superseded(md_path.read_text(encoding="utf-8"), run_id, run_timestamp)
        md_path.write_text(prev + "\n" + section.strip() + "\n", encoding="utf-8")
    else:
        header = f"""# Bitácora de Clustering Jerárquico Aglomerativo · `8.1_clustering_jerarquico.ipynb`

> **Proyecto:** `MineriaProtect` (JobPath — Observatorio Laboral de Trayectorias y Perfiles ESCO)
> **Guía técnica implementada:** `01_agglomerative_hierarchical_clustering.md`

Este archivo es **append-only**: conserva todas las corridas previas marcadas como **`[SUPERSEDED]`** y registra la corrida vigente como **`[CURRENT]`**.
- **Corrida vigente confirmada en ambos archivos (`.md`)**: **`{run_id}`** (`{run_timestamp}` · estado: **`CURRENT`**).
"""
        md_path.write_text(header + "\n" + section.strip() + "\n", encoding="utf-8")

    return md_path


def append_comparacion_ab_jerarquico_md(
    config: HierarchicalClusteringConfig,
    run_id: str,
    run_timestamp: str,
    data_usage_df: pd.DataFrame,
    per_seed_df: pd.DataFrame,
    ab_summary_df: pd.DataFrame,
    person_bundle: HierarchicalAnalysisBundle,
) -> Path:
    """Write or append the Version B vs Version A comparison to Comparacion_A_vs_B_Clustering_Jerarquico.md."""
    md_path = config.comparacion_ab_md_path
    b_row = ab_summary_df.iloc[0]
    a_row = ab_summary_df.iloc[1]

    section = f"""
---
## Corrida Fechada · ID `{run_id}` · `{run_timestamp}` · [CURRENT]

### 0. Uso de Datos y Estrategia de Muestreo (`{run_id}`)
{_df_to_markdown(data_usage_df)}

### 1. Estabilidad en `{len(config.sensitivity_seeds)}` Semillas Estratificadas (`Versión B · SIN outliers` vs. `Versión A · CON outliers`)
{_df_to_markdown(per_seed_df)}

### 2. Resumen Comparativo `Versión B` vs. `Versión A` (Media y DE en `{len(config.sensitivity_seeds)}` Semillas)
{_df_to_markdown(ab_summary_df)}

### 3. Perfiles Finales en Escala Original (`Versión B · SIN outliers` · `k = {person_bundle.k_opt}`)
{_df_to_markdown(person_bundle.profile_df)}

- **Conclusión y elección de versión para Clustering Jerárquico**: Evaluando en `{int(b_row['n_semillas'])}` semillas independientes (`{int(b_row['personas_por_semilla'])}` personas de Train por semilla, `k = {int(b_row['k_optimo'])}`), **Versión B · SIN outliers (Primaria)** alcanza un `silhouette_media = {float(b_row['silhouette_media']):.4f}` (`± {float(b_row['silhouette_std']):.4f}`), `davies_bouldin_media = {float(b_row['davies_bouldin_media']):.4f}` (`± {float(b_row['davies_bouldin_std']):.4f}`) y `cophenet_media = {float(b_row['cophenet_media']):.4f}`, frente a `silhouette_media = {float(a_row['silhouette_media']):.4f}` (`± {float(a_row['silhouette_std']):.4f}`) y `davies_bouldin_media = {float(a_row['davies_bouldin_media']):.4f}` en **Versión A · CON outliers**, con una concordancia promedio entre ambas versiones de `ARI = {float(b_row['ari_b_vs_a_media']):.4f}` (`± {float(b_row['ari_b_vs_a_std']):.4f}`, `NMI = {float(b_row['nmi_b_vs_a_media']):.4f}`). Se selecciona **Versión B · SIN outliers** como versión primaria porque el criterio de varianza de Ward utiliza distancias euclidianas al cuadrado y la winsorización IQR evita que valores extremos distorsionen las alturas de corte (`{float(b_row['altura_corte_ward_media']):.3f}` en B vs. `{float(a_row['altura_corte_ward_media']):.3f}` en A).
"""

    if md_path.exists():
        prev = _mark_previous_runs_superseded(md_path.read_text(encoding="utf-8"), run_id, run_timestamp)
        md_path.write_text(prev + "\n" + section.strip() + "\n", encoding="utf-8")
    else:
        header = f"""# Comparación Versión B (SIN outliers) vs. Versión A (CON outliers) · Clustering Jerárquico Aglomerativo

> **Proyecto:** `MineriaProtect` (JobPath) · `8.1_clustering_jerarquico.ipynb`

Este archivo es **append-only**: conserva todas las corridas previas marcadas como **`[SUPERSEDED]`** y registra la corrida vigente como **`[CURRENT]`**.
- **Corrida vigente confirmada en ambos archivos (`.md`)**: **`{run_id}`** (`{run_timestamp}` · estado: **`CURRENT`**).
"""
        md_path.write_text(header + "\n" + section.strip() + "\n", encoding="utf-8")

    return md_path


def _extract_current_run_block(md_text: str) -> str:
    """Extract only the [CURRENT] run section from an append-only Markdown document."""
    pattern = re.compile(r"(## Corrida Fechada · ID `RUN-[^`]+` · `[^`]+` · \[CURRENT\].*)", re.DOTALL)
    match = pattern.search(md_text)
    if not match:
        raise AssertionError("No [CURRENT] run section found in Markdown file!")
    return match.group(1)


def _normalize_number_token(tok: str) -> Set[str]:
    """Generate exact canonical string representations of a numeric token (trailing zeros only, never coarse rounding)."""
    cleaned = tok.replace(",", "").rstrip("%").rstrip("x")
    forms = {cleaned, tok.rstrip("%").rstrip("x")}
    try:
        val = float(cleaned)
        forms.add(f"{val}")
        if val.is_integer():
            forms.add(f"{int(val)}")
        for dec in range(1, 5):
            if abs(round(val, dec) - val) < 1e-9:
                forms.add(f"{val:.{dec}f}")
                forms.add(f"{val:.{dec}f}".rstrip("0").rstrip("."))
    except ValueError:
        pass
    return forms


def verify_narrative_numbers_against_tables(md_text: str, doc_name: str = "markdown") -> Dict[str, object]:
    """Parse every numeric literal in narrative lines of the [CURRENT] block and fail loudly if absent from tables."""
    block = _extract_current_run_block(md_text)
    lines = block.splitlines()

    table_lines = [ln for ln in lines if ln.strip().startswith("|")]
    narrative_lines = [
        ln
        for ln in lines
        if not ln.strip().startswith("|")
        and not ln.strip().startswith("#")
        and not ln.strip().startswith("---")
        and "Corrida Fechada" not in ln
        and "Identificador" not in ln
    ]

    num_regex = re.compile(r"(?<![A-Za-z0-9_.-])\d+(?:,\d{3})*(?:\.\d+)?%?(?![A-Za-z0-9_])")
    allowed_structural = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "10", "30", "60", "100"}

    table_tokens: Set[str] = set(allowed_structural)
    for t_ln in table_lines:
        for match in num_regex.findall(t_ln):
            table_tokens.update(_normalize_number_token(match))

    checked_count = 0
    missing: List[str] = []
    for n_ln in narrative_lines:
        # Remove inline code identifiers like k_opt or section numbers
        cleaned_ln = re.sub(r"`RUN-[^`]+`", "", n_ln)
        cleaned_ln = re.sub(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}", "", cleaned_ln)
        for match in num_regex.findall(cleaned_ln):
            checked_count += 1
            candidate_forms = _normalize_number_token(match)
            if candidate_forms.isdisjoint(table_tokens):
                missing.append(f"{match} (en: '{n_ln.strip()[:90]}')")

    if missing:
        raise AssertionError(
            f"[{doc_name}] Narrative number verification FAILED! Numbers not found in tables of the same run: {missing}"
        )

    return {
        "archivo_md": doc_name,
        "numeros_narrativa_verificados": checked_count,
        "discrepancias_detectadas": len(missing),
        "estado_verificacion": "APROBADO (100% trazable a tablas de la misma corrida)",
    }
