# Session 9 · Technical Implementation Guide 02: K-Means Clustering (`MineriaProtect` · JobPath)

> **Course / Subject:** Data Mining · Unit 2 (CRISP-DM Phase 4 & Phase 5 · KDD Data Mining & Interpretation)
> **Project / Repository:** `MineriaProtect` (JobPath — Labor Observatory of Educational Training & Occupational Trajectories)
> **Target Deliverables:** `notebooks/refactor/8.0_kmeans_clustering.ipynb`, modular package `scripts/ScriptsCsv/KMeans/`, figures in `reports/kmeans_jobpath/figures/`, tables in `reports/kmeans_jobpath/tables/`, and append-only audit logs `notebooks/refactor/Bitacora_KMeans.md` & `notebooks/refactor/Comparacion_A_vs_B_KMeans.md`
> **Purpose of this document:** Serve as a complete, self-contained technical specification for an AI agent or software developer to implement, evaluate, visualize, profile, and document **K-Means Clustering** in the `MineriaProtect` repository without ambiguity.
> **Language Convention:** All Python code, module names, functions, and variable identifiers MUST be written in **English**. All final plot titles, axis labels, legends, exported table column headers, and narrative interpretations MUST be generated in **Spanish** (matching `5.0_EDA_jobpath.ipynb`, `6.0_modelado_fase4_jobpath.ipynb`, and `7.0_arbol_decision.ipynb`; an optional `PLOT_LANG = "es"` / `"en"` toggle is provided in Section 5).

---

## 1. Context and Session Objective

Previous Phase 4 notebooks in `MineriaProtect` addressed **supervised classification** (`6.0_modelado_fase4_jobpath.ipynb`, `7.0_arbol_decision.ipynb`, `7.1_naive_bayes.ipynb`, `7.2_knn.ipynb`), where a target column (`reincide = (veces_ese_oficio > 1)`) guided learning.

In Session 9, **no target column enters training**: the goal is **unsupervised structure discovery** — partitioning the JobHop + ESCO labor trajectories into natural, cohesive, and actionable segments as envisioned in the Phase 1 business charter (`notebooks/refactor/1.0_comprension_negocio.md`).

| Technique | Core Idea | Role in `MineriaProtect` |
|---|---|---|
| **K-Means Clustering (This Guide: `02`)** | Flat partitioning into $k$ groups via centroids initialized with `k-means++` and updated iteratively to minimize Within-Cluster Sum of Squares (**Inertia**). | Full-scale operational segmentation across all `352,093` classified persons and `1,738,738` classified job experiences, with original-scale centroid extraction and 2D PCA visualization. |
| **Agglomerative Hierarchical Clustering (Companion Guide: `01`)** | Bottom-up tree fusion (**dendrogram**) on a stratified discovery sample ($n = 3,000$) and visual micro-sample ($n = 60$). | Structural taxonomy discovery, linkage benchmarking (`ward`), and independent tree-cut validation of the $k^*$ used in K-Means. |

The deliverable of K-Means **is not a cluster number (`0, 1, 2...`)**: it is the **commercial/institutional segment name**, the **robot portrait (`retrato robot`)** in real original units, and the **concrete Labor Observatory / curriculum intervention** associated with each segment.

### Learning and Implementation Objectives

1. Differentiate supervised classification from unsupervised clustering in JobPath, enforcing a strict **zero-target-leakage policy** (`reincide` and `veces_ese_oficio` are excluded from `X` and used exclusively for post-hoc cluster profiling).
2. Trace K-Means step by step (centroid seeding via `k-means++`, Voronoi assignment, centroid update, convergence) and determine the optimal $k^*$ ($k \in \{2, 3, 4, 5, 6, 7, 8\}$) by combining the **Elbow Method (Inertia)**, **Silhouette Score**, **Davies-Bouldin Index**, ** hierarchical dendrogram concordance**, and **business viability**.
3. Execute a full-population segmentation with `KMeans(n_init=10, random_state=42)` + `StandardScaler`, extract **interpretable centroids in original scale** (via both `scaler.inverse_transform(km.cluster_centers_)` and `df.groupby("cluster")[V].mean()`), and visualize the clusters in a **2D PCA projection**.
4. Contrast **Version B (`sin_outliers`)** vs. **Version A (`con_outliers`)** across 5 random seeds, name each segment in Spanish (`perfil + comportamiento`), and prescribe a differentiated Labor Observatory action per segment.

---

## 2. Supervised vs. Unsupervised in JobPath (Zero Target Leakage Policy)

| Aspect | Supervised Phase (`6.0`, `7.0`, `7.1`, `7.2`) | Unsupervised Phase (`8.0` K-Means, `8.1` Hierarchical) |
|---|---|---|
| **Input Data** | `X` and `y` (`reincide = (veces_ese_oficio > 1)`) | **Only `X`** (zero response column during clustering) |
| **Goal** | Predict the binary label of unseen persons/experiences | Discover hidden structure: career archetypes, skill-demand profiles, anomalies |
| **Typical Metrics** | ROC-AUC, PR-AUC, F1, Precision, Recall, Accuracy | Inertia (WCSS), Silhouette Score, Davies-Bouldin Index, and business utility |
| **Primary Risk** | Overfitting & target leakage | Scale domination, outlier distortion of centroids, or narrating meaningless groups |

**Synergy between Supervised and Unsupervised:** Clustering can enrich `X` with a categorical `"segmento"` feature for downstream models, and the supervised target `reincide` (`30.01%` base rate in Train, `29.97%` in Test) serves as an **external post-hoc validation signal** to check whether natural behavioral clusters also differ in occupational repetition.

### Two Rules of Professional Judgment

- **Before running K-Means, ask:** *"What concrete decision in the Labor Observatory or university curriculum will change if we find these groups?"* If no stakeholder will act differently across segments, the analysis is decoration.
- **K-Means always returns $k$ groups**, even on uniform noise. Human domain judgment — backed by silhouette cohesion, centroid separation in original units, and out-of-sample stability — decides whether the segments are real and actionable.

---

## 3. K-Means Algorithm & Project Architecture in `MineriaProtect`

### 3.1 Step-by-Step Algorithm Mechanics

1. **Seed Centroids (`init="k-means++"`):** Place $k$ initial centroids $\{\mu_1^{(0)}, \dots, \mu_k^{(0)}\}$ in standardized feature space using **k-means++**, which spreads initial seeds with probability proportional to squared distance $D(x)^2$ from already chosen centers.
2. **Assign Observations:** Assign each standardized observation $x_i$ to its closest centroid under Euclidean distance:
   $$c_i^{(t)} = \arg\min_{j \in \{1,\dots,k\}} \|x_i - \mu_j^{(t)}\|_2^2$$
3. **Recalculate Centroids:** Move each centroid $\mu_j^{(t+1)}$ to the arithmetic mean of all points currently assigned to cluster $j$:
   $$\mu_j^{(t+1)} = \frac{1}{|C_j^{(t)}|} \sum_{x_i \in C_j^{(t)}} x_i$$
4. **Iterate Until Convergence:** Repeat assignment and centroid recalculation until assignments stop changing (or centroid shift falls below `tol = 1e-4`, up to `max_iter = 300`).

### 3.2 Core Mathematical Concepts

- **Inertia (Within-Cluster Sum of Squares · WCSS):**
  $$\text{Inertia}(k) = \sum_{j=1}^{k} \sum_{x_i \in C_j} \|x_i - \mu_j\|_2^2$$
  This is the exact objective function minimized by K-Means. Lower inertia means tighter, more compact clusters.
- **Sensitivity to Initialization (`n_init=10` & `random_state=42`):** Because K-Means is a local coordinate-descent algorithm, different initial seeds can converge to different local optima. Setting `n_init=10` and `random_state=42` runs 10 independent `k-means++` initializations and retains the solution with the lowest inertia.
- **Mandatory Standardization (`StandardScaler`):** Because Euclidean distance sums squared differences across coordinates, any feature measured in large numbers (e.g., career span in quarters `span_q` or skill count `n_skills_competence`) would overwhelm proportions (`prop_competence_essential` $\in [0, 1]$). Applying `StandardScaler` before `KMeans` is non-negotiable.

### 3.3 Exact Repository Paths (`MineriaProtect`)

All code MUST resolve paths dynamically from the repository root `MineriaProtect/`:

#### Input Paths (Read-Only · Verify Integrity via SHA-256 Before and After Execution)

| Input Identifier | Relative Path from `MineriaProtect/` | Scope & Rows | Role in K-Means |
|---|---|---|---|
| `CLEAN_VERSION_B` **(Primary)** | `data/03_processed/empleos_limpio_con_competencias_sin_outliers.csv` | `1,871,014` rows × `23` cols (`1,738,738` ESCO-classified rows; `352,093` unique classified persons). IQR-winsorized continuous variables (`47.5`, `39.5`, `13.5`). | **Primary dataset** for K-Means (prevents extreme tail outliers from pulling arithmetic centroids $\mu_j$). |
| `CLEAN_VERSION_A` **(Sensitivity)** | `data/03_processed/empleos_unificado_limpio.csv` | `1,871,014` rows × `23` cols (`1,738,738` ESCO-classified rows; `352,093` unique classified persons). Unclipped raw tails. | **Sensitivity benchmark** to quantify centroid drift and cluster reassignment when raw outliers are kept (`Comparacion_A_vs_B_KMeans.md`). |
| `SPLIT_MAP_PATH` | `reports/eda_jobpath/tables/split_map_resume_id.csv` | Official person-grouped split (`281,674` Train persons / `1,391,018` rows; `70,419` Test persons / `347,720` rows; `random_state=42`). | Fits `StandardScaler` and `KMeans` on `Train` (`80%`), then predicts and validates cluster stability on held-out `Test` (`20%`) and full population. |

#### Output Paths (Code, Figures, Tables, and Audit Logs)

| Deliverable Type | Exact Relative Path from `MineriaProtect/` | Contents |
|---|---|---|
| **Main Executed Notebook** | `notebooks/refactor/8.0_kmeans_clustering.ipynb` | Narrative in Spanish, code in English, inline tables, embedded figures, and final honesty guard cell. |
| **Modular Python Package** | `scripts/ScriptsCsv/KMeans/__init__.py`<br>`scripts/ScriptsCsv/KMeans/config.py`<br>`scripts/ScriptsCsv/KMeans/feature_builder.py`<br>`scripts/ScriptsCsv/KMeans/kmeans_engine.py`<br>`scripts/ScriptsCsv/KMeans/pca_and_plots.py`<br>`scripts/ScriptsCsv/KMeans/markdown_writers.py` | Clean modular package imported by Cell 1 of `8.0_kmeans_clustering.ipynb`. |
| **Exported Figures (`.png`, 300 DPI)** | `reports/kmeans_jobpath/figures/01_metodo_codo_y_silueta_kmeans_personas.png`<br>`reports/kmeans_jobpath/figures/02_metodo_codo_y_silueta_kmeans_experiencias.png`<br>`reports/kmeans_jobpath/figures/03_proyeccion_pca_2d_clusters_y_centroides_personas.png`<br>`reports/kmeans_jobpath/figures/04_proyeccion_pca_2d_clusters_y_centroides_experiencias.png`<br>`reports/kmeans_jobpath/figures/05_diagrama_silueta_por_cluster_k_optimo.png`<br>`reports/kmeans_jobpath/figures/06_centroides_escala_original_y_tasa_reincide.png`<br>`reports/kmeans_jobpath/figures/07_sensibilidad_version_b_vs_version_a_centroides.png` | All charts generated with **Spanish titles, axis labels, subtitles, and legends**. |
| **Exported CSV Tables (`.csv`)** | `reports/kmeans_jobpath/tables/01_uso_de_datos_kmeans.csv`<br>`reports/kmeans_jobpath/tables/02_busqueda_k_codo_silueta_dbi_personas.csv`<br>`reports/kmeans_jobpath/tables/03_busqueda_k_codo_silueta_dbi_experiencias.csv`<br>`reports/kmeans_jobpath/tables/04_centroides_personas_escala_original_y_estandarizada.csv`<br>`reports/kmeans_jobpath/tables/05_centroides_experiencias_escala_original_y_estandarizada.csv`<br>`reports/kmeans_jobpath/tables/06_perfiles_completos_y_validacion_posthoc_reincide.csv`<br>`reports/kmeans_jobpath/tables/07_estabilidad_train_vs_test_y_5_semillas.csv`<br>`reports/kmeans_jobpath/tables/08_asignacion_clusters_personas_352093.csv`<br>`reports/kmeans_jobpath/tables/09_comparacion_sensibilidad_version_b_vs_version_a.csv` | Machine-readable CSVs backing every figure and narrative statement. |
| **Append-Only Markdown Logs** | `notebooks/refactor/Bitacora_KMeans.md`<br>`notebooks/refactor/Comparacion_A_vs_B_KMeans.md` | Dated run logs with unique `run_id` (`[CURRENT]` vs. `[SUPERSEDED]`) and automated narrative number verification. |

---

## 4. Choosing Optimal $k$ and Preparing the Behavioral Features

### 4.1 Feature Selection, Missing/Categorical Treatment, and Anti-Leakage Rules

1. **Filter Classified Universe (`occupation_code.notna()`):** Retain the `1,738,738` ESCO-classified job experiences (`352,093` unique `resume_id` persons) and exclude in RAM the `132,276` unclassified rows (`7.07%`) that lack ESCO competency profiles.
2. **Two Complementary Behavioral Matrices (`V_PERSON` Primary & `V_EXPERIENCE` Secondary):**
   - **`V_PERSON` (`352,093` classified persons; `281,674` in Train / `70,419` in Test):**
     `["n_jobs", "span_q", "dur_mean", "overlap_ratio", "mean_skills_competence", "mean_skills_knowledge", "mean_prop_competence", "nivel_academico_ord_imputado", "educacion_no_reportada"]`
   - **`V_EXPERIENCE` (`1,738,738` classified rows; `1,391,018` in Train / `347,720` in Test):**
     `["dur_q", "job_order", "n_skills_competence", "n_skills_knowledge", "prop_competence_essential", "nivel_academico_ord_imputado", "educacion_no_reportada"]`
3. **Strict Anti-Leakage Exclusion (`reincide` Never Enters `X`):**
   - Exclude `reincide`, `veces_ese_oficio`, `veces_ese_oficio_rob`, `veces_ese_oficio_bin`, `n_returns`, `n_self_loops`, `self_loop_share`, `n_occ`, and `exploration_ratio`. Use `reincide` / `any_repeated_posthoc` **only after clustering** to profile each cluster's repetition rate and Lift.
4. **Elimination of $E = C + K$ Additive Redundancy:**
   - Because `n_skills_essential = n_skills_competence + n_skills_knowledge` in `99.10%` of classified rows (`n_skills_sin_tipo == 0`), omit `n_skills_essential` from the clustering matrix `X` so total skill count is not double-weighted in Euclidean distance, while reporting `n_skills_essential` in the post-hoc original-scale profile table.
5. **MNAR Education Treatment (`university_level == 'No reportado'`):**
   - Never fill `'No reportado'` (`160,664` rows in Train, `40,270` in Test, `200,934` total) with `0`. Keep the binary indicator `educacion_no_reportada` ($0/1$) alongside `nivel_academico_ord_imputado` (where `1..4` represents Secondary through Doctorate, and missing values receive the Train median `2.0 = Bachelor`).

### 4.2 Negotiating Optimal $k$ ($k \in \{2, 3, 4, 5, 6, 7, 8\}$)

The value of $k$ **is a methodological and business decision, not a mechanical formula**. It is negotiated across three criteria:

#### 4.2.1 Elbow Method (Inertia & Relative Marginal Drop)
- Inertia ($\text{WCSS}_k$) **always decreases monotonically** as $k$ increases.
- Plot $\text{Inertia}(k)$ vs. $k$ and compute the relative percentage reduction:
  $$\Delta_{\%}\text{Inertia}(k) = \frac{\text{Inertia}(k-1) - \text{Inertia}(k)}{\text{Inertia}(k-1)} \times 100$$
- Identify the **elbow (`codo`)**: the value of $k$ where the curve transitions from steep marginal gain to a flat plateau. Never decide with the elbow alone.

#### 4.2.2 Silhouette Coefficient ($s \in [-1, +1]$) & Complementary Internal Metrics
For each observation $i$, Silhouette compares:
- $a(i)$ = **cohesion** (mean distance from $i$ to all other points in its own cluster),
- $b(i)$ = **separation** (mean distance from $i$ to all points in the nearest neighboring cluster).

$$s(i) = \frac{b(i) - a(i)}{\max(a(i), b(i))} \in [-1, +1]$$

| Value of $s$ | Interpretation |
|---|---|
| Close to **+1** | Well-clustered: tight within its own group and far from neighboring groups |
| Around **0.15 – 0.35** | **Normal in real socioeconomic/labor trajectory data** with continuous overlapping distributions; focus on actionability and profile separation |
| Near **0** | Boundary observation lying between two adjacent centroids |
| **Negative (< 0)** | Potentially misassigned observation |

- **Computational Note for Large $N$:** Computing exact pairwise Silhouette on $N = 1,391,018$ or $N = 281,674$ rows scales as $O(N^2)$. Therefore, pass `sample_size=20000, random_state=42` to `silhouette_score(X_scaled, labels, sample_size=20000, random_state=42)`, and complement it with **full-dataset** `davies_bouldin_score(X_scaled, labels)` (lower is better) and `calinski_harabasz_score(X_scaled, labels)` (higher is better), which run in $O(N \cdot k)$ linear time!

#### 4.2.3 Business Viability & Dendrogram Concordance
- Cross-check whether the candidate $k^*$ matches the optimal horizontal cut of the Ward dendrogram from `01_agglomerative_hierarchical_clustering.md` ($k^* \in \{3, 4, 5\}$) and corresponds to a realistic number of differentiated institutional programs in the Labor Observatory.

---

## 5. Step-by-Step Implementation Workflow (Scikit-Learn Pipeline)

All code MUST use `pandas`, `numpy`, `scikit-learn` (`StandardScaler`, `KMeans`, `PCA`, `silhouette_score`, `silhouette_samples`, `davies_bouldin_score`, `calinski_harabasz_score`, `adjusted_rand_score`), `scipy`, `matplotlib`, and `seaborn`, with `RANDOM_STATE = 42`.

### 5.1 Step 1: Configuration, Defensive Load, and Feature Scaling

```python
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    normalized_mutual_info_score,
    silhouette_samples,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler

RANDOM_STATE: int = 42
SENSITIVITY_SEEDS: Tuple[int, ...] = (42, 100, 2026, 7, 999)
K_RANGE: range = range(2, 9)
SILHOUETTE_SAMPLE_SIZE: int = 20000
PCA_PLOT_SAMPLE_SIZE: int = 15000
PLOT_LANG: str = "es"  # "es" for Spanish titles/labels (project default) or "en" for English


def resolve_project_root() -> Path:
    """Locate the MineriaProtect repository root dynamically."""
    cwd = Path.cwd()
    for candidate in [cwd] + list(cwd.parents):
        if candidate.name == "MineriaProtect":
            return candidate
        if (candidate / "MineriaProtect").is_dir():
            return candidate / "MineriaProtect"
    raise FileNotFoundError("Could not locate MineriaProtect root directory.")


PROJECT_ROOT = resolve_project_root()
PATH_VERSION_B = PROJECT_ROOT / "data/03_processed/empleos_limpio_con_competencias_sin_outliers.csv"
PATH_VERSION_A = PROJECT_ROOT / "data/03_processed/empleos_unificado_limpio.csv"
PATH_SPLIT_MAP = PROJECT_ROOT / "reports/eda_jobpath/tables/split_map_resume_id.csv"

OUT_DIR = PROJECT_ROOT / "reports/kmeans_jobpath"
FIG_DIR = OUT_DIR / "figures"
TAB_DIR = OUT_DIR / "tables"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TAB_DIR.mkdir(parents=True, exist_ok=True)
```

### 5.2 Step 2: Searching for Optimal $k$ (Elbow Inertia + Silhouette + Davies-Bouldin)

```python
def search_optimal_k_kmeans(
    df_train: pd.DataFrame,
    feature_cols: List[str],
    k_range: range = K_RANGE,
    sil_sample_size: int = SILHOUETTE_SAMPLE_SIZE,
    seed: int = RANDOM_STATE,
) -> Tuple[pd.DataFrame, StandardScaler, np.ndarray]:
    """Evaluate KMeans across k=2..8 on standardized Train data, recording Inertia, Silhouette, DBI, and CHI."""
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(df_train[feature_cols])

    rows = []
    prev_inertia = None
    for k in k_range:
        km = KMeans(n_clusters=k, init="k-means++", n_init=10, max_iter=300, random_state=seed)
        labels = km.fit_predict(X_train_scaled)
        inertia = float(km.inertia_)
        drop_pct = (
            round((prev_inertia - inertia) / prev_inertia * 100.0, 2)
            if prev_inertia is not None
            else 0.0
        )
        prev_inertia = inertia

        sil = float(
            silhouette_score(
                X_train_scaled,
                labels,
                sample_size=min(sil_sample_size, len(X_train_scaled)),
                random_state=seed,
            )
        )
        dbi = float(davies_bouldin_score(X_train_scaled, labels))
        chi = float(calinski_harabasz_score(X_train_scaled, labels))
        counts = pd.Series(labels).value_counts()

        rows.append(
            {
                "k": k,
                "inercia_wcss": round(inertia, 2),
                "caida_relativa_inercia_pct": drop_pct,
                "silhouette_score": round(sil, 4),
                "davies_bouldin_index": round(dbi, 4),
                "calinski_harabasz_index": round(chi, 2),
                "tamano_min_cluster": int(counts.min()),
                "tamano_max_cluster": int(counts.max()),
                "pct_cluster_mas_grande": round(float(counts.max() / len(labels) * 100.0), 2),
            }
        )

    return pd.DataFrame(rows), scaler, X_train_scaled


def plot_elbow_and_silhouette_es(
    k_table: pd.DataFrame,
    k_opt: int,
    fig_path: Path,
    view_label_es: str = "Personas · Trayectorias",
    lang: str = PLOT_LANG,
) -> None:
    """Plot dual-panel Elbow (Inertia) and Silhouette Score curve with Spanish (or English) titles and labels."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.2), dpi=300)

    # Panel 1: Elbow Method (Inertia)
    ax1.plot(k_table["k"], k_table["inercia_wcss"], marker="o", linewidth=2.2, color="#1F77B4")
    ax1.axvline(x=k_opt, color="#D62728", linestyle="--", linewidth=1.8, label=f"k elegido = {k_opt}")
    if lang == "es":
        ax1.set_title(f"Método del Codo (Inercia WCSS) · {view_label_es}", fontsize=12, fontweight="bold")
        ax1.set_xlabel("Número de clústeres (k)", fontsize=11)
        ax1.set_ylabel("Inercia intra-clúster (WCSS · datos escalados)", fontsize=11)
    else:
        ax1.set_title(f"Elbow Method (WCSS Inertia) · {view_label_es}", fontsize=12, fontweight="bold")
        ax1.set_xlabel("Number of clusters (k)", fontsize=11)
        ax1.set_ylabel("Within-Cluster Sum of Squares (WCSS · scaled data)", fontsize=11)
    ax1.grid(True, linestyle="--", alpha=0.4)
    ax1.legend(loc="upper right")

    # Panel 2: Silhouette Score
    ax2.plot(k_table["k"], k_table["silhouette_score"], marker="s", linewidth=2.2, color="#2CA02C")
    ax2.axvline(x=k_opt, color="#D62728", linestyle="--", linewidth=1.8, label=f"k elegido = {k_opt}")
    if lang == "es":
        ax2.set_title(f"Coeficiente de Silueta Promedio vs. k · {view_label_es}", fontsize=12, fontweight="bold")
        ax2.set_xlabel("Número de clústeres (k)", fontsize=11)
        ax2.set_ylabel("Coeficiente de Silueta promedio s(k)", fontsize=11)
    else:
        ax2.set_title(f"Mean Silhouette Coefficient vs. k · {view_label_es}", fontsize=12, fontweight="bold")
        ax2.set_xlabel("Number of clusters (k)", fontsize=11)
        ax2.set_ylabel("Mean Silhouette Coefficient s(k)", fontsize=11)
    ax2.grid(True, linestyle="--", alpha=0.4)
    ax2.legend(loc="upper right")

    fig.tight_layout()
    fig.savefig(fig_path, dpi=300)
    plt.close(fig)
```

### 5.3 Step 3: Fitting the Final K-Means Model and Extracting Original-Scale Centroids

A critical requirement of Session 9 is **never interpreting standardized centroids (`km.cluster_centers_`) as real-world units**. A standardized value of `+0.73` means `0.73` standard deviations above the mean, not `0.73` jobs or `0.73` quarters.

The implementation MUST extract **both** standardized centroids (for z-score heatmaps) and **original-scale centroids** (via `scaler.inverse_transform(km.cluster_centers_)` and `df.groupby("cluster")[V].mean()`, which are mathematically identical on the training partition):

```python
def fit_final_kmeans_and_extract_centroids(
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
    feature_cols: List[str],
    k_opt: int,
    posthoc_target_col: str = "any_repeated_posthoc",
    seed: int = RANDOM_STATE,
) -> Tuple[KMeans, StandardScaler, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Fit final KMeans on Train, assign Train and Test, and extract centroids in original and standardized scales."""
    scaler = StandardScaler()
    X_tr_scaled = scaler.fit_transform(df_train[feature_cols])
    X_te_scaled = scaler.transform(df_test[feature_cols])

    km_raw = KMeans(n_clusters=k_opt, init="k-means++", n_init=10, max_iter=300, random_state=seed)
    tr_labels_raw = km_raw.fit_predict(X_tr_scaled)

    # Order cluster IDs 0..k_opt-1 deterministically by ascending mean of primary feature (e.g., n_jobs or dur_q)
    order = np.argsort(scaler.inverse_transform(km_raw.cluster_centers_)[:, 0])
    remap = {int(old_idx): int(new_idx) for new_idx, old_idx in enumerate(order)}

    # Reorder cluster_centers_ in-place so km.predict() and km.cluster_centers_ use the canonical 0..k_opt-1 order
    km_raw.cluster_centers_ = km_raw.cluster_centers_[order]

    df_tr_out = df_train.copy()
    df_te_out = df_test.copy()
    df_tr_out["cluster"] = pd.Series(tr_labels_raw, index=df_train.index).map(remap)
    df_te_out["cluster"] = km_raw.predict(X_te_scaled)

    # 1. Centroids via inverse_transform (original units) vs standardized z-scores
    centroids_orig = pd.DataFrame(
        scaler.inverse_transform(km_raw.cluster_centers_),
        columns=[f"{c}_centroide_original" for c in feature_cols],
    ).round(3)
    centroids_z = pd.DataFrame(
        km_raw.cluster_centers_,
        columns=[f"{c}_z_estandarizado" for c in feature_cols],
    ).round(3)
    centroids_table = pd.concat([pd.Series(range(k_opt), name="cluster"), centroids_orig, centroids_z], axis=1)

    # 2. Full profile table on original unscaled data (groupby().mean() + post-hoc target rate & Lift)
    profile_tr = df_tr_out.groupby("cluster")[feature_cols].mean().round(2)
    profile_tr["n_train"] = df_tr_out["cluster"].value_counts().sort_index()
    profile_tr["pct_train"] = (profile_tr["n_train"] / len(df_tr_out) * 100.0).round(2)
    profile_tr["n_test"] = df_te_out["cluster"].value_counts().sort_index()
    profile_tr["pct_test"] = (profile_tr["n_test"] / len(df_te_out) * 100.0).round(2)

    base_tr = float(df_tr_out[posthoc_target_col].mean())
    base_te = float(df_te_out[posthoc_target_col].mean())
    rate_tr = df_tr_out.groupby("cluster")[posthoc_target_col].mean()
    rate_te = df_te_out.groupby("cluster")[posthoc_target_col].mean()

    profile_tr["tasa_reincide_train_posthoc_pct"] = (rate_tr * 100.0).round(2)
    profile_tr["tasa_reincide_test_posthoc_pct"] = (rate_te * 100.0).round(2)
    profile_tr["lift_reincide_test_posthoc"] = (rate_te / max(base_te, 1e-9)).round(3)

    return km_raw, scaler, centroids_table, profile_tr.reset_index(), pd.concat([df_tr_out, df_te_out], ignore_index=True)
```

### 5.4 Step 4: Visualizing Clusters & Centroids in a 2D PCA Projection

To inspect cluster separation visually in two dimensions, project both the standardized observations and the $k^*$ standardized centroids `km.cluster_centers_` onto the first two principal components (`PCA(n_components=2, random_state=42)`):

```python
def plot_pca_2d_clusters_and_centroids_es(
    X_scaled: np.ndarray,
    labels: np.ndarray,
    km: KMeans,
    segment_names_es: Dict[int, str],
    fig_path: Path,
    sample_n: int = PCA_PLOT_SAMPLE_SIZE,
    seed: int = RANDOM_STATE,
    lang: str = PLOT_LANG,
) -> None:
    """Project standardized observations and K-Means centroids onto 2D PCA space with Spanish titles/labels."""
    pca = PCA(n_components=2, random_state=seed)
    X_pca_full = pca.fit_transform(X_scaled)
    centroids_pca = pca.transform(km.cluster_centers_)
    var_pc1 = pca.explained_variance_ratio_[0] * 100.0
    var_pc2 = pca.explained_variance_ratio_[1] * 100.0

    # Subsample points for clean scatter rendering while keeping exact full-data centroids
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(X_pca_full), size=min(sample_n, len(X_pca_full)), replace=False)
    X_sub = X_pca_full[idx]
    y_sub = labels[idx]

    fig, ax = plt.subplots(figsize=(11, 7.0), dpi=300)
    palette = sns.color_palette("tab10", n_colors=len( np.unique(labels)))

    for cid in sorted(np.unique(labels)):
        mask = y_sub == cid
        label_str = f"Clúster {cid}: {segment_names_es.get(cid, f'Segmento {cid}')}"
        ax.scatter(X_sub[mask, 0], X_sub[mask, 1], s=14, alpha=0.45, color=palette[cid], label=label_str)
        ax.scatter(
            centroids_pca[cid, 0],
            centroids_pca[cid, 1],
            s=280,
            marker="*",
            color=palette[cid],
            edgecolor="black",
            linewidth=1.5,
            zorder=10,
        )

    if lang == "es":
        ax.set_title(
            f"Proyección PCA 2D de Clústeres K-Means y Centroides (★) · Varianza Explicada = {var_pc1 + var_pc2:.1f}%",
            fontsize=13,
            fontweight="bold",
        )
        ax.set_xlabel(f"Componente Principal 1 ({var_pc1:.1f}% de varianza)", fontsize=11)
        ax.set_ylabel(f"Componente Principal 2 ({var_pc2:.1f}% de varianza)", fontsize=11)
    else:
        ax.set_title(
            f"2D PCA Projection of K-Means Clusters and Centroids (★) · Explained Variance = {var_pc1 + var_pc2:.1f}%",
            fontsize=13,
            fontweight="bold",
        )
        ax.set_xlabel(f"Principal Component 1 ({var_pc1:.1f}% variance)", fontsize=11)
        ax.set_ylabel(f"Principal Component 2 ({var_pc2:.1f}% variance)", fontsize=11)

    ax.legend(loc="best", frameon=True, fontsize=9.5)
    ax.grid(True, linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(fig_path, dpi=300)
    plt.close(fig)
```

---

## 6. Cluster Profiling, Post-Hoc External Validation, and Segment Naming ("Retrato Robot")

### 6.1 Key Rules for Profiling and Post-Hoc Validation

1. **Always Narrate Real Units:** Each cluster becomes a legible row of real-world means (`n_jobs` in jobs, `span_q` and `dur_mean` in quarters, `mean_skills_competence` and `mean_skills_knowledge` in ESCO skill counts, `mean_prop_competence` in $\%$, and `educacion_no_reportada` in $\%$).
2. **Mathematical Equivalence Check:** Verify in code that `scaler.inverse_transform(km.cluster_centers_)` matches `df_train.groupby("cluster")[V].mean().to_numpy()` within `1e-5`.
3. **Post-Hoc Evaluation of `reincide`:** Compare `tasa_reincide_train_posthoc_pct` and `tasa_reincide_test_posthoc_pct` across clusters against the global base rate (`30.01%` in Train / `29.97%` in Test). This demonstrates whether unsupervised behavioral segments naturally stratify occupational repetition without ever having seen the target during training.

### 6.2 Naming the Segments & Designing Actions

Each segment name MUST combine **demographic/skill profile + career behavior** (never `"Grupo 0"` or `"Cluster 1"`):

```python
SEGMENT_NAMES_ES: Dict[int, str] = {
    0: "Inserción Temprana o Trayectoria Corta en Oficios Operativos",
    1: "Especialistas Estables de Permanencia Prolongada",
    2: "Trayectorias Intensivas en Conocimiento y Alta Exigencia ESCO",
    3: "Rotación Frecuente y Multi-Empleo Solapado",
}
```

For each segment, the report and `Bitacora_KMeans.md` MUST document:
1. **Actionable Spanish Name.**
2. **Robot Portrait (`Retrato Robot`):** Cluster share ($n$ and $\%$ in Train and Test), real-scale centroid values, dominant ISCO 1-digit group, and post-hoc `reincide` rate & Lift.
3. **Differentiated Observatory / University Action:** Specific curriculum, placement, or career-counseling intervention coherent with the segment's profile.

---

## 7. K-Means vs. Agglomerative Hierarchical (Combined Strategy)

| Criterion | K-Means (`02_kmeans_clustering.md`) | Agglomerative Hierarchical (`01_agglomerative_hierarchical_clustering.md`) |
|---|---|---|
| **Data Scale** | Hundreds of thousands to millions of rows (`352,093` persons / `1,738,738` experiences) | Hundreds to a few thousand rows ($n = 60$ visual micro-sample / $n = 3,000$ discovery sample) |
| **Must $k$ Be Fixed Upfront?** | **Yes, mandatory** | **No:** explore the dendrogram tree and cut at the optimal height |
| **Typical Output** | Flat partition into $k$ spherical Voronoi cells + explicit centroids | Nested hierarchy of subgroups (dendrogram) |
| **Stability** | Depends on random seeding (`init="k-means++"`, `n_init=10`, `random_state=42` stabilize it) | **Deterministic** on the same sample |
| **Ideal Use in JobPath** | Massive operational segmentation & centroid reporting | Initial taxonomy exploration & independent validation of $k^*$ |

**Recommended Combined Strategy in `MineriaProtect`:** Use Agglomerative Hierarchical Clustering (`ward` linkage) on the stratified sample ($n = 3,000$) to inspect the dendrogram and confirm how many natural macro-groups exist ($k^*$), and then apply K-Means across the **entire classified population (`352,093` persons and `1,738,738` experiences)** to assign every observation to its definitive operational segment. Report the concordance (`adjusted_rand_score` and `normalized_mutual_info_score`) between both methods on the shared discovery sample.

---

## 8. Limitations of K-Means & Version B (`sin_outliers`) vs. Version A (`con_outliers`) Protocol

Every report and notebook MUST explicitly declare the four structural limitations of K-Means:

1. **Assumes Spherical, Equal-Variance Clusters:** K-Means partitions space via linear Voronoi hyperplanes around Euclidean centroids. If true groups are elongated, skewed, or non-convex, K-Means slices them artificially.
2. **Hypersensitive to Feature Scale:** Without `StandardScaler`, variables with larger numerical variance completely dominate inertia.
3. **Sensitive to Outliers (Why Version B `sin_outliers` Is Primary):** Because centroids are arithmetic means, extreme outliers pull centroids away from the dense core.
   - **Mandatory Version B vs. Version A Sensitivity Experiment (`09_comparacion_sensibilidad_version_b_vs_version_a.csv`):** Fit K-Means with the same $k^*$ and `random_state=42` (plus 5 subsamples `seeds = [42, 100, 2026, 7, 999]`) on **Version B (`empleos_limpio_con_competencias_sin_outliers.csv`)** and **Version A (`empleos_unificado_limpio.csv`)**. Quantify the Euclidean shift in standardized centroids, the change in Silhouette Score and Davies-Bouldin Index, and the cross-version Adjusted Rand Index (`ARI(labels_B, labels_A)`).
4. **$k$ Is a Decision, Not an Automatic Truth:** $k^*$ must be justified transparently by triangulating Elbow Inertia, Silhouette Score, Davies-Bouldin Index, hierarchical dendrogram cut, and business viability.

---

## 9. Quality Criteria & Frequent Mistakes to Avoid

### Signals of a Well-Executed K-Means Segmentation

- `StandardScaler` is fitted on Train **before** `KMeans`, and standardization is verified in code.
- The choice of $k^*$ cites exact figures from the Elbow (Inertia & marginal drop $\%$), Silhouette Score, Davies-Bouldin Index, and the companion Ward dendrogram.
- Centroids are extracted and narrated in **original unscaled units** (`scaler.inverse_transform` / `groupby().mean()`), alongside the post-hoc `reincide` rate and Lift per cluster.
- Segment names describe **profile + career behavior**, paired with a concrete Labor Observatory intervention.

### 7 Frequent Mistakes to Avoid

1. **Clustering without scaling (`StandardScaler`):** Produces degenerate mega-clusters dominated by high-variance columns.
2. **Including identifiers (`resume_id`, `occupation_code`) or raw date strings (`start_date`, `end_date`) in `X`.**
3. **Including the target (`reincide`, `veces_ese_oficio`, `n_returns`, or `exploration_ratio`) in `X`:** Contaminates unsupervised discovery with supervised leakage. Use them **only after clustering** for post-hoc profiling.
4. **Interpreting standardized centroids (`km.cluster_centers_`) as real-world values:** Always inverse-transform or compute `df.groupby("cluster")[V].mean()` on original unscaled variables before writing narrative interpretations.
5. **Including all three ESCO skill counts (`essential`, `competence`, `knowledge`) simultaneously in `X`:** Double-weights total skill count because $E = C + K$ in `99.10%` of rows.
6. **Filling MNAR education (`'No reportado'`) with `0`:** Introduces a false ordinal rank below secondary education. Use `educacion_no_reportada` ($0/1$) + median-imputed ordinal level.
7. **Choosing an excessively high $k$** under the false belief that "more clusters = better analysis" when silhouette drops and segments become operationally indistinguishable.

---

## 10. End-to-End Business Workflow in the JobPath Labor Observatory

| Stage | Action in `MineriaProtect` |
|---|---|
| **1. Engineer Behavioral Features** | Construct non-leaky trajectory features (`V_PERSON`) and occupational demand features (`V_EXPERIENCE`) from Version B (`sin_outliers`). |
| **2. Segment with K-Means** | Fit `KMeans(init="k-means++", n_init=10, random_state=42)` on scaled Train data; select $k^*$ with Elbow + Silhouette + DBI + Ward dendrogram concordance. |
| **3. Extract Real-Scale Centroids & Profile** | Compute original-scale centroids (`inverse_transform` & `groupby().mean()`), project onto Test (`20%`), and audit post-hoc `reincide` rate and ISCO distribution. |
| **4. Name & Prioritize Segments** | Assign each cluster an actionable Spanish name (`Retrato Robot`) and an institutional owner. |
| **5. Measure & Iterate** | Track employability and retention outcomes **by segment** and periodically recalibrate centroids on new cohorts. |

---

## 11. Evaluation Rubric & Verification Checklist

| Evidence Deliverable | Core Criterion | Weight |
|---|---|---|
| **Inertia / Silhouette / DBI Table ($k = 2\dots 8$)** | Correct calculations on **scaled** data (`StandardScaler`), relative inertia drop $\%$, and reasoned reading of the elbow & silhouette peak | 30% |
| **Original-Scale Centroids & Cluster Profiles** | Mathematical equivalence of `inverse_transform(cluster_centers_)` and `groupby("cluster")[V].mean()` + post-hoc `reincide` rate/Lift + 2D PCA projection | 30% |
| **Actionable Segment Names & Observatory Actions** | Spanish names describing profile + behavior + coherent institutional intervention per segment | 30% |
| **Cross-Check vs. Hierarchical Dendrogram & Version A/B** | Verbal and quantitative contrast (`ARI`, `NMI`) against the Ward dendrogram (`01`) and Version B vs. Version A sensitivity check | 10% |

### Mandatory Automated Honesty Guard Cell (Final Cell of `8.0_kmeans_clustering.ipynb`)

The final cell of the notebook MUST execute and pass four automated assertions:
1. **Input SHA-256 Integrity:** `CLEAN_VERSION_B`, `CLEAN_VERSION_A`, and `SPLIT_MAP_PATH` hashes remain unchanged after execution.
2. **Zero Target Leakage in `X`:** Assert that `set(V_PERSON).isdisjoint({"reincide", "veces_ese_oficio", "n_returns", "n_occ", "exploration_ratio"})`.
3. **Centroid Equivalence Check:** Assert `np.allclose(scaler.inverse_transform(km.cluster_centers_), df_train.groupby("cluster")[V].mean().to_numpy(), atol=1e-4)`.
4. **Narrative Number Verifier:** Parse every number in `Bitacora_KMeans.md` and `Comparacion_A_vs_B_KMeans.md` and assert that it exists in a table of the same `[CURRENT]` run.

---

## 12. Independent Extension Work & Validation

1. **Supervised Enrichment Experiment:** Add the discovered K-Means `cluster` (one-hot encoded) as an additional feature in the Phase 4 classifiers (`7.0_arbol_decision.ipynb`, `7.1_naive_bayes.ipynb`, `7.2_knn.ipynb`) and measure whether `ROC-AUC` or leaf `Lift` improves on `Test`.
2. **Sub-Group Sensitivity:** Re-run K-Means within specific ISCO major groups to compare macro-level vs. intra-sector occupational segments.

---

## 13. Key Takeaways to Remember

- Without labels we still learn: K-Means **discovers latent structure**, and its value is judged by **cohesion (Inertia/Silhouette), separation (Davies-Bouldin/PCA 2D), and business actionability**.
- K-Means iterates **seed (`k-means++`) $\to$ assign $\to$ recalculate** until convergence; it **mandates `StandardScaler`** and chooses $k^*$ by combining **Elbow (Inertia) + Silhouette + Ward Dendrogram + Business Viability**.
- Never narrate standardized z-score centroids as real values: always extract **original-scale centroids** (`scaler.inverse_transform` and `groupby().mean()`).
- The target variable (`reincide`) **never** enters `X` during clustering; it is used strictly afterward for external profiling.

---

## 14. Next Session

**Session 10 · Association Rules (`Apriori` / `FP-Growth`):** Discovering frequent co-occurring occupational transitions and ESCO skill bundles across career trajectories to formulate educational and training recommendations.
