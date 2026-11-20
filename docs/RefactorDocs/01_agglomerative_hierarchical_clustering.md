# Session 9 · Technical Implementation Guide 01: Agglomerative Hierarchical Clustering (`MineriaProtect` · JobPath)

> **Course / Subject:** Data Mining · Unit 2 (CRISP-DM Phase 4 & Phase 5 · KDD Data Mining & Interpretation)
> **Project / Repository:** `MineriaProtect` (JobPath — Labor Observatory of Educational Training & Occupational Trajectories)
> **Target Deliverables:** `notebooks/refactor/8.1_clustering_jerarquico.ipynb`, modular package `scripts/ScriptsCsv/ClusteringJerarquico/`, figures in `reports/clustering_jerarquico_jobpath/figures/`, tables in `reports/clustering_jerarquico_jobpath/tables/`, and append-only audit logs `notebooks/refactor/Bitacora_Clustering_Jerarquico.md` & `notebooks/refactor/Comparacion_A_vs_B_Clustering_Jerarquico.md`
> **Purpose of this document:** Serve as a complete, self-contained technical specification for an AI agent or software developer to implement, evaluate, profile, and document **Agglomerative Hierarchical Clustering** in the `MineriaProtect` repository without ambiguity.
> **Language Convention:** All Python code, module names, functions, and variable identifiers MUST be written in **English**. All final plot titles, axis labels, legends, exported table column headers, and narrative interpretations MUST be generated in **Spanish** (matching `5.0_EDA_jobpath.ipynb`, `6.0_modelado_fase4_jobpath.ipynb`, and `7.0_arbol_decision.ipynb`; an optional `PLOT_LANG = "es"` / `"en"` toggle is provided in Section 6).

---

## 1. Context and Session Objective

Previous Phase 4 notebooks in `MineriaProtect` addressed **supervised classification** (`6.0_modelado_fase4_jobpath.ipynb`, `7.0_arbol_decision.ipynb`, `7.1_naive_bayes.ipynb`, `7.2_knn.ipynb`), where the models learned to predict the binary target `reincide = (veces_ese_oficio > 1)` (`30.01%` positive class in Train, `29.97%` in Test).

In this unit, **there is no target column during training**: the objective returns directly to the foundational unsupervised charter declared in `notebooks/refactor/1.0_comprension_negocio.md` — **discovering hidden natural structure (taxonomies of career trajectories and occupational skill-demand profiles)** in the JobHop + ESCO dataset.

Two complementary clustering families are implemented across our two guides:

| Technique | Core Idea | Role in `MineriaProtect` |
|---|---|---|
| **Agglomerative Hierarchical Clustering (This Guide: `01`)** | Starts with each observation as its own singleton cluster and iteratively merges the two most similar groups bottom-up, producing a nested tree (**dendrogram**) that can be cut at any height. | Structural exploration, linkage tournament (`ward` vs. `complete`, `average`, `single`), visual and quantitative justification of the optimal cut $k^*$, and validation of K-Means partition count. |
| **K-Means Clustering (Companion Guide: `02`)** | Flat partitioning into $k$ spherical groups around iteratively updated centroids (`k-means++`). | Full-scale operational segmentation across all `352,093` classified persons and `1,738,738` classified job experiences. |

The true deliverable of clustering **is not a numeric cluster ID (`0, 1, 2...`)**: it is the **actionable segment name**, the **robot portrait (`retrato robot`)** in original real-world units, and the **concrete educational/employability intervention** associated with each group.

### Learning and Implementation Objectives

1. Differentiate supervised classification from unsupervised structure discovery in JobPath, enforcing a strict **zero-target-leakage policy** (`reincide` and `veces_ese_oficio` never enter feature matrix `X`).
2. Design and execute a **memory-safe 3-tier sampling protocol** that respects the $O(n^2)$ memory bound of pairwise distance matrices while guaranteeing statistical representativeness across `352,093` persons and `1,738,738` experiences.
3. Benchmark four linkage criteria (**prioritizing `ward`**, alongside `complete`, `average`, and `single`) using **Cophenetic Correlation**, **Silhouette Score**, **Davies-Bouldin Index**, and **Calinski-Harabasz Index**, plot publication-grade **dendrograms**, and establish the optimal horizontal cut $k^*$.
4. Profile every resulting cluster in **original unscaled units** (`groupby().mean()` and `.median()`), evaluate post-hoc external alignment against `reincide`, ISCO major groups, and educational level, contrast **Version B (`sin_outliers`)** vs. **Version A (`con_outliers`)**, and assign actionable Spanish segment names and policy actions.

---

## 2. Supervised vs. Unsupervised in JobPath (Zero Target Leakage Policy)

| Dimension | Supervised Phase (`6.0`, `7.0`, `7.1`, `7.2`) | Unsupervised Phase (`8.0` K-Means, `8.1` Hierarchical) |
|---|---|---|
| **Input Data** | Feature matrix `X` **and** binary target vector `y` (`reincide`) | Feature matrix `X` **only** (zero response column during fit) |
| **Primary Goal** | Predict whether a person repeats an occupation (`reincide = 1`) | Discover natural archetypes of career trajectories and occupational skill demands |
| **Evaluation Metrics** | ROC-AUC, PR-AUC, F1 (class 1), Recall, Accuracy, Leaf Lift | Cophenetic correlation, Silhouette Score ($s \in [-1, 1]$), Davies-Bouldin Index (lower is better), Calinski-Harabasz Index, and business interpretability |
| **Primary Risk** | Overfitting & target leakage (`veces_ese_oficio` in `X`) | Scale domination by unscaled features, memory explosion ($O(n^2)$), or narrating noise clusters that lack business meaning |

**Bridge between Unsupervised and Supervised:** The cluster assignment discovered here (`cluster_jerarquico`) can subsequently be used to enrich `X` as a structural latent feature or to audit whether natural career/skill archetypes exhibit distinct post-hoc occupational repetition rates (`tasa_reincide_pct`).

### Why Clustering Matters in the JobPath Labor Observatory

- **Career Trajectory Segmentation (Person Level · `352,093` classified persons):** Identifies distinct worker mobility archetypes (e.g., *Long-Tenure Specialists*, *High-Rotation Generalists*, *Technical Skill-Intensive Climbers*, *Early-Career Explorers*).
- **Occupational Skill-Demand Taxonomy (Experience Level · `1,738,738` classified rows):** Groups work experiences by ESCO competency complexity (`n_skills_competence`, `n_skills_knowledge`, `prop_competence_essential`), job duration (`dur_q`), and academic qualification.
- **Anomaly & Boundary Detection:** Isolated branches merging at very high dendrogram distances reveal atypical career paths or extreme multi-job overlapping trajectories (`overlap_ratio >> 1`).
- **Curriculum & Policy Design:** Enables universities and public employment observatories to tailor retraining modules per segment rather than treating all graduates as a homogeneous average.

### Two Rules of Professional Judgment

1. **Before clustering, ask:** *"What concrete decision in the Labor Observatory or university curriculum will change if we find these groups?"* If no stakeholder can act on the segments, the clustering is decorative.
2. **Hierarchical clustering always produces a tree**, even on uniform random noise. Human domain judgment — backed by cophenetic correlation, silhouette separation, stability across seeds, and real-unit profile deltas — decides whether a cut represents genuine structure.

---

## 3. Algorithm Fundamentals & Architecture in `MineriaProtect`

### 3.1 How Agglomerative Hierarchical Clustering Works Step by Step

Unlike K-Means, which requires fixing $k$ before running, the bottom-up agglomerative algorithm proceeds as follows:

1. **Singleton Initialization:** Start with $n$ clusters, where each observation $i \in \{1, \dots, n\}$ is its own cluster $C_i = \{x_i\}$.
2. **Pairwise Distance Matrix ($n \times n$ or condensed $\binom{n}{2}$):** Compute the Euclidean distance $d(x_i, x_j) = \|x_i - x_j\|_2$ between all pairs of **standardized** observations.
3. **Iterative Bottom-Up Fusion:** At each step $t \in \{1, \dots, n-1\}$, find the pair of active clusters $(A, B)$ with the smallest inter-cluster dissimilarity $D(A, B)$, merge them into $A \cup B$, and record the merge height $h_t = D(A, B)$ and cluster size in the $(n-1) \times 4$ linkage matrix `Z`.
4. **Update Dissimilarities (Lance-Williams Recurrence):** Recompute the dissimilarity between the newly formed cluster $A \cup B$ and all remaining clusters according to the chosen **linkage criterion**.
5. **Root Termination:** Continue until all $n$ observations are united into a single root cluster at step $n-1$.

### 3.2 Linkage Criteria Tournament (Prioritizing `ward`)

The linkage method defines how inter-cluster distance $D(A, B)$ is measured. The implementation MUST benchmark all four standard methods on the standardized discovery sample, **prioritizing `ward`**:

| Linkage Method | Mathematical Criterion $D(A, B)$ | Geometric Behavior | Priority & Expected Behavior in JobPath |
|---|---|---|---|
| **`ward` (Primary)** | Minimizes the increase in total within-cluster error sum of squares ($\Delta \text{ESS} = \frac{|A||B|}{|A|+|B|} \|\mu_A - \mu_B\|_2^2$). Requires Euclidean distance. | Produces balanced, compact, spherical-to-ellipsoidal clusters; directly analogous to K-Means objective. | **Priority #1 (Default).** Best suited for continuous standardized behavioral and ESCO skill-count features. |
| **`complete`** | Maximum distance between any point in $A$ and any point in $B$: $\max_{a \in A, b \in B} \|a - b\|_2$. | Produces tight, compact clusters of roughly equal diameter; sensitive to outliers. | **Priority #2 (Benchmark).** Useful to check whether extreme trajectories split into small peripheral branches. |
| **`average` (UPGMA)** | Average distance across all pairs between $A$ and $B$: $\frac{1}{|A||B|} \sum_{a \in A}\sum_{b \in B} \|a - b\|_2$. | Compromise between single and complete linkage; preserves pairwise distance geometry well (often high cophenetic correlation). | **Priority #3 (Benchmark).** Good diagnostic for cophenetic fidelity (`cophenet`). |
| **`single`** | Minimum distance between any point in $A$ and any point in $B$: $\min_{a \in A, b \in B} \|a - b\|_2$. | Prone to the **chaining effect** (merges observations one-by-one into one giant cluster plus tiny singletons). | **Priority #4 (Diagnostic contrast).** Document chaining pathology on dense job-trajectory data. |

### 3.3 How to Read the Dendrogram and Define the Optimal Cut

- **Vertical Axis (Fusion Height / Ward Distance):** Represents the dissimilarity $D(A, B)$ at which two subtrees merge. Low merges indicate highly homogeneous observations; high merges indicate forced unions of structurally distinct macro-groups.
- **Horizontal Cut Line (`corte óptimo`):** Drawing a horizontal line at height $h^*$ cuts the tree into $k^*$ branches (the number of vertical lines intersected by the horizontal cut). This allows inspecting $k = 2, 3, 4, 5, 6\dots$ **without retraining the linkage matrix `Z`**.
- **Largest Vertical Jump Rule (Acceleration of Fusion Distances):** Inspect the last 15 merge heights $Z[-15:, 2]$ and their consecutive differences $\Delta h_m = Z[m, 2] - Z[m-1, 2]$. A large jump between merge $n-k^*$ and $n-k^*+1$ indicates that the $k^*$ macro-clusters are well separated and resisting fusion.
- **Multi-Criteria Cut Decision:** The optimal cut $k^*$ is selected by triangulating:
  1. **Largest vertical jump** in the `ward` dendrogram ($Z[-15:, 2]$),
  2. **Peak Silhouette Score** ($s(k)$) and **Local Minimum of Davies-Bouldin Index** ($\text{DBI}(k)$) across $k \in \{2, 3, 4, 5, 6, 7, 8\}$,
  3. **Business actionability** (typically $k^* \in \{3, 4, 5\}$ interpretable segments for the Labor Observatory).

### 3.4 Exact Repository Paths (`MineriaProtect`)

All scripts and notebooks MUST resolve paths relative to the repository root `MineriaProtect/` (never hard-coding user-specific absolute paths):

#### Input Paths (Read-Only · Verify Integrity via SHA-256 Before and After Execution)

| Input Identifier | Relative Path from `MineriaProtect/` | Description & Scope | Role in This Guide |
|---|---|---|---|
| `CLEAN_VERSION_B` **(Primary)** | `data/03_processed/empleos_limpio_con_competencias_sin_outliers.csv` | `1,871,014` rows × `23` cols (`1,738,738` ESCO-classified rows; `352,093` unique classified persons). IQR-winsorized continuous variables (`n_skills_essential <= 47.5`, `n_skills_competence <= 39.5`, `n_skills_knowledge <= 13.5`). | **Primary dataset** for Hierarchical Clustering (prevents extreme outliers from dominating Euclidean distances and Ward merges). |
| `CLEAN_VERSION_A` **(Sensitivity)** | `data/03_processed/empleos_unificado_limpio.csv` | `1,871,014` rows × `23` cols (`1,738,738` ESCO-classified rows; `352,093` unique classified persons). Raw unclipped tails. | **Sensitivity benchmark** to evaluate how raw outliers alter dendrogram cut heights, linkage stability, and cluster assignments (`Comparacion_A_vs_B_Clustering_Jerarquico.md`). |
| `SPLIT_MAP_PATH` | `reports/eda_jobpath/tables/split_map_resume_id.csv` | Official person-grouped split (`281,674` Train persons / `1,391,018` rows; `70,419` Test persons / `347,720` rows; `random_state=42`; `0` shared persons). | Ensures `StandardScaler` and primary cluster discovery are fitted on `Train` (`80%`) and validated out-of-sample on `Test` (`20%`). |

#### Output Paths (Code, Figures, Tables, and Audit Logs)

| Deliverable Type | Exact Relative Path from `MineriaProtect/` | Contents |
|---|---|---|
| **Main Executed Notebook** | `notebooks/refactor/8.1_clustering_jerarquico.ipynb` | Narrative in Spanish, code in English, inline tables, embedded figures, and final honesty guard cell. |
| **Modular Python Package** | `scripts/ScriptsCsv/ClusteringJerarquico/__init__.py`<br>`scripts/ScriptsCsv/ClusteringJerarquico/config.py`<br>`scripts/ScriptsCsv/ClusteringJerarquico/sampling_and_features.py`<br>`scripts/ScriptsCsv/ClusteringJerarquico/hierarchical_engine.py`<br>`scripts/ScriptsCsv/ClusteringJerarquico/profiling_and_plots.py`<br>`scripts/ScriptsCsv/ClusteringJerarquico/markdown_writers.py` | Clean modular implementation imported by Cell 1 of `8.1_clustering_jerarquico.ipynb`. |
| **Exported Figures (`.png`, 300 DPI)** | `reports/clustering_jerarquico_jobpath/figures/01_dendrograma_micro_muestra_n60_ward.png`<br>`reports/clustering_jerarquico_jobpath/figures/02_dendrograma_truncado_n3000_corte_optimo.png`<br>`reports/clustering_jerarquico_jobpath/figures/03_comparacion_metodos_linkage_metricas.png`<br>`reports/clustering_jerarquico_jobpath/figures/04_curvas_silueta_y_davies_bouldin_k2_a_k8.png`<br>`reports/clustering_jerarquico_jobpath/figures/05_proyeccion_pca_2d_clusters_jerarquicos.png`<br>`reports/clustering_jerarquico_jobpath/figures/06_perfiles_clusters_escala_original_y_reincide.png`<br>`reports/clustering_jerarquico_jobpath/figures/07_sensibilidad_version_b_vs_version_a_5_semillas.png` | All charts with **Spanish titles, axis labels, subtitles, and legends**. |
| **Exported CSV Tables (`.csv`)** | `reports/clustering_jerarquico_jobpath/tables/01_uso_de_datos_y_estrategia_muestreo.csv`<br>`reports/clustering_jerarquico_jobpath/tables/02_torneo_metodos_linkage_cophenet_silueta_dbi.csv`<br>`reports/clustering_jerarquico_jobpath/tables/03_evaluacion_cortes_k2_a_k8_saltos_y_metricas.csv`<br>`reports/clustering_jerarquico_jobpath/tables/04_estabilidad_5_semillas_muestreo_jerarquico.csv`<br>`reports/clustering_jerarquico_jobpath/tables/05_perfiles_clusters_personas_escala_original.csv`<br>`reports/clustering_jerarquico_jobpath/tables/06_perfiles_clusters_experiencias_escala_original.csv`<br>`reports/clustering_jerarquico_jobpath/tables/07_asignacion_clusters_muestra_descubrimiento.csv`<br>`reports/clustering_jerarquico_jobpath/tables/08_asignacion_clusters_personas_completo_nearest_centroid.csv`<br>`reports/clustering_jerarquico_jobpath/tables/09_comparacion_sensibilidad_version_b_vs_version_a.csv` | Machine-readable tables backing every number in the notebook and `.md` logs. |
| **Append-Only Markdown Logs** | `notebooks/refactor/Bitacora_Clustering_Jerarquico.md`<br>`notebooks/refactor/Comparacion_A_vs_B_Clustering_Jerarquico.md` | Dated run logs with unique `run_id` (`[CURRENT]` vs. `[SUPERSEDED]`) and narrative verifier check. |

---

## 4. Feature Selection, Missing/Categorical Handling, and Mandatory Scaling

### 4.1 Filtering the Modelling Universe (`es_ocupacion_clasificada == 1`)

Before constructing features, apply the project's Phase 3/Phase 4 filter in RAM:
- Keep rows where `occupation_code.notna()` (`1,738,738` classified job experiences across `352,093` unique `resume_id` persons: `1,391,018` rows / `281,674` persons in Train and `347,720` rows / `70,419` persons in Test).
- Exclude in RAM the `132,276` unclassified rows (`7.07%` of `1,871,014`, comprising `128,981` `emparejado == 'unknown'` and `3,295` `rescatado` without an ESCO parent code) because they lack valid ESCO competency counts (`n_skills_*`). Document this count in `01_uso_de_datos_y_estrategia_muestreo.csv`.

### 4.2 Dual Analytical Views: Person-Trajectory View (Primary) & Experience-Profile View (Secondary)

Because `MineriaProtect` studies both **worker career trajectories** (`1.0_comprension_negocio.md`) and **occupational skill profiles** (`7.0_arbol_decision.ipynb`), the hierarchical clustering pipeline MUST support two clean behavioral feature matrices `V_PERSON` (Primary) and `V_EXPERIENCE` (Secondary):

#### View 1 (Primary): Person-Trajectory Behavioral Matrix (`V_PERSON` · 1 Row per `resume_id`, $N_{\text{Train}} = 281,674$, $N_{\text{Total}} = 352,093$)

Derived by collapsing each person's classified experiences chronologically (following `scripts/ScriptsCsv/EDA/person_level.py`, **excluding** target-equivalent loop counts from `X`):

| Feature Name in `V_PERSON` | Source / Formula | Scale & Domain | Behavioral Meaning |
|---|---|---|---|
| `n_jobs` | Count of job experiences per `resume_id` | Integer $\ge 1$ | Career job volume / mobility frequency |
| `span_q` | $\max(\text{end\_ord}) - \min(\text{start\_ord}) + 1$ (clipped $\ge 1$) | Quarters ($\ge 1$) | Total observed career span in quarters |
| `dur_mean` | Mean of `dur_q` across the person's jobs | Quarters ($\ge 1.0$) | Average permanence (stability) per job spell |
| `overlap_ratio` | $\text{dur\_total} / \text{span\_q}$ | Continuous $\ge 0$ | Concurrency / multi-job overlapping intensity |
| `mean_skills_competence` | Mean of `n_skills_competence` across person's classified jobs | Count ($[0, 39.5]$ in Version B) | Average practical competency demand of the career |
| `mean_skills_knowledge` | Mean of `n_skills_knowledge` across person's classified jobs | Count ($[0, 13.5]$ in Version B) | Average theoretical/technical knowledge demand |
| `mean_prop_competence` | Mean of $\frac{\text{n\_skills\_competence}}{\max(\text{n\_skills\_essential}, 1)}$ | Proportion $\in [0, 1]$ | Practical vs. theoretical orientation of the person's occupations |
| `nivel_academico_ord_imputado` | Ordinal education (`1`=Secondary, `2`=Bachelor, `3`=Master, `4`=Doctorate; median-imputed `2.0` **only** when paired with `educacion_no_reportada`) | Ordinal $\{1, 2, 3, 4\}$ | Formal academic qualification level |
| `educacion_no_reportada` | `1` if `university_level == 'No reportado'`, else `0` | Binary $\{0, 1\}$ | Preserves MNAR non-reporting signal (`11.56%` of rows) without artificial `0` ordinal distortion |

#### View 2 (Secondary): Job-Experience / Occupational-Profile Matrix (`V_EXPERIENCE` · 1 Row per Experience, $N_{\text{Train}} = 1,391,018$, $N_{\text{Total}} = 1,738,738$)

| Feature Name in `V_EXPERIENCE` | Source / Formula | Scale & Domain | Behavioral Meaning |
|---|---|---|---|
| `dur_q` | $\text{end\_ord} - \text{start\_ord} + 1$ (`Present` right-censored at `2026-Q1`) | Quarters ($\ge 1.0$) | Duration of the specific job experience |
| `job_order` | `groupby("resume_id").cumcount() + 1` sorted by `start_ord` | Integer $\ge 1$ | Career stage (entry job vs. late-career job) |
| `n_skills_competence` | ESCO essential practical competencies count | Count ($[0, 39.5]$ in B) | Volume of practical skills demanded by the occupation |
| `n_skills_knowledge` | ESCO essential specialized knowledge count | Count ($[0, 13.5]$ in B) | Volume of specialized knowledge demanded by the occupation |
| `prop_competence_essential` | $\text{n\_skills\_competence} / \max(\text{n\_skills\_essential}, 1)$ | Proportion $\in [0, 1]$ | Skill mix balance (competence share) |
| `nivel_academico_ord_imputado` | Ordinal `1..4` (median-imputed `2.0` paired with MNAR flag) | Ordinal $\{1, 2, 3, 4\}$ | Academic level of the worker holding the job |
| `educacion_no_reportada` | Binary indicator (`1` if `'No reportado'`, `0` otherwise) | Binary $\{0, 1\}$ | Explicit MNAR indicator |

### 4.3 Variables Strictly Excluded from `X` (Anti-Leakage & Anti-Collinearity Rules)

1. **Target & Target-Equivalent Leakage Columns (NEVER include in `X`):**
   - `reincide`, `is_repeated_occupation`, `any_repeated`, `veces_ese_oficio`, `veces_ese_oficio_rob`, `veces_ese_oficio_bin`, `n_returns`, `n_self_loops`, `n_nonadjacent_returns`, `self_loop_share`, `nonadjacent_return_share`, `n_occ`, and `exploration_ratio = n_occ / n_jobs` (since `n_occ < n_jobs` is algebraically equivalent to `any_repeated == True`).
   - *Rule:* These columns are reserved **exclusively for post-hoc external profiling** after the clusters have been formed.
2. **Exact Additive Collinearity ($E = C + K$ Identity):**
   - As proven in `7.0_arbol_decision.ipynb`, `n_skills_essential = n_skills_competence + n_skills_knowledge` holds exactly in `99.10%` of classified rows (`n_skills_sin_tipo == 0`). Including all three counts (`essential`, `competence`, `knowledge`) in Euclidean distance double-weights total skill volume. Therefore, include **`n_skills_competence`**, **`n_skills_knowledge`**, and **`prop_competence_essential`**, omitting `n_skills_essential` from `X` (while reporting `n_skills_essential` in the post-hoc original-scale profile table!).
3. **Identifiers, Raw Strings, and High-Cardinality Codes:**
   - Exclude `resume_id`, `start_date`, `end_date`, `matched_code`, `occupation_code`, `occupation_label`, `isco_group`, `isco_group_label`, `saber_skills`, `skills`, `knowledge`, `sin_tipo`, `es_unknown_ocupacion`, `es_rescatado`.
4. **Missing Value & Categorical Treatment (No Spurious Zero-Filling):**
   - Because `scipy.cluster.hierarchy.linkage` and `sklearn.cluster.AgglomerativeClustering` do not accept `NaN` values, and `university_level == 'No reportado'` (`160,664` rows in Train, `40,270` in Test, `200,934` total) is Missing Not At Random (MNAR), **never encode `'No reportado'` as `0`** (which would place unreported education artificially below primary/secondary school). Instead, include the binary flag `educacion_no_reportada` ($0/1$) alongside `nivel_academico_ord_imputado` (where missing values receive the Train median `2.0 = Bachelor`), so the Euclidean distance separates unreported records via the orthogonal binary flag without distorting the ordinal scale.

### 4.4 Mandatory Standardization (`StandardScaler`)

Euclidean distance is dominated by features with large numerical variance (e.g., `span_q` or `n_skills_competence` vs. `prop_competence_essential` $\in [0, 1]$).
- Fit `scaler = StandardScaler()` **exclusively on the Train partition** (or the discovery sample drawn from Train).
- Transform the features to zero mean ($\mu = 0$) and unit variance ($\sigma = 1$) **before** calling `linkage()` or `AgglomerativeClustering()`.

---

## 5. Memory-Safe Sampling Strategy for Hierarchical Clustering ($O(n^2)$ Bound)

### 5.1 Why Full-Dataset Hierarchical Clustering Cannot Fit in RAM

`scipy.cluster.hierarchy.linkage` requires a condensed pairwise distance vector of length $\binom{n}{2} = \frac{n(n-1)}{2}$ stored in 64-bit floats (`8 bytes` per pair):
- For $N = 1,738,738$ experiences: $\binom{N}{2} = 1.51 \times 10^{12}$ pairs $\times 8\text{ bytes} \approx \mathbf{12.09\text{ TB}}$ of RAM.
- For $N = 352,093$ persons: $\binom{N}{2} = 6.20 \times 10^{10}$ pairs $\times 8\text{ bytes} \approx \mathbf{495.9\text{ GB}}$ of RAM.

Attempting to run `linkage()` on the full dataset will immediately crash with `MemoryError`.

### 5.2 Mandatory 3-Tier Sampling & Out-of-Sample Assignment Protocol

To combine mathematical rigor, visual clarity, and 100% dataset coverage, the implementation MUST execute three complementary tiers with fixed seeds:

| Tier | Sample Size ($n$) | Sampling Method & Seed | Purpose | Memory Footprint $\binom{n}{2} \times 8\text{B}$ |
|---|---|---|---|---|
| **Tier 1 · Visual Micro-Sample** | $n = 60$ persons (and $n = 60$ experiences) | Stratified by ISCO 1-digit major group (`isco_main`) from Train (`random_state=42`) | Generates a clean, readable **leaf-annotated dendrogram** (`01_dendrograma_micro_muestra_n60_ward.png`), following the Session 9 classroom standard ($50\text{–}60$ observations). | `14.2 KB` (instantaneous) |
| **Tier 2 · Primary Discovery Subsample** | $n = 3,000$ persons (and $n = 3,000$ experiences) | Stratified by ISCO 1-digit major group & MNAR education flag from Train (`random_state=42`, matching the `3,000`-person sample size of `7.0_arbol_decision.ipynb`) | Runs the **4-linkage tournament** (`ward`, `complete`, `average`, `single`), computes **Cophenetic Correlation**, evaluates cuts $k \in \{2 \dots 8\}$ (`Silhouette`, `Davies-Bouldin`, `Calinski-Harabasz`), and plots the **truncated dendrogram** (`truncate_mode="lastp", p=30`). | `36.0 MB` (~0.8 seconds) |
| **Tier 3 · 5-Seed Stability & Full-Dataset Nearest-Centroid Assignment** | $5 \times 3,000$ samples (`seeds = [42, 100, 2026, 7, 999]`) $\to$ Full projection onto `352,093` persons & `1,738,738` rows | 5 independent stratified person subsamples + `NearestCentroid` projection in standardized space | Verifies that Silhouette, Davies-Bouldin, and cluster centroids are stable (`mean ± SD` across 5 seeds), and assigns every single person (`352,093`) and experience (`1,738,738`) to its nearest hierarchical cluster centroid in standardized space. | `< 50 MB` peak RAM |

---

## 6. Step-by-Step Implementation Workflow (Scikit-Learn & SciPy Pipeline)

All code MUST use the following expected libraries and fixed seed configuration:
- **Required Libraries:** `pandas`, `numpy`, `scipy` (`scipy.cluster.hierarchy.linkage`, `dendrogram`, `fcluster`, `cophenet`; `scipy.spatial.distance.pdist`), `scikit-learn` (`sklearn.preprocessing.StandardScaler`, `sklearn.cluster.AgglomerativeClustering`, `sklearn.neighbors.NearestCentroid`, `sklearn.metrics.silhouette_score`, `silhouette_samples`, `davies_bouldin_score`, `calinski_harabasz_score`, `adjusted_rand_score`, `normalized_mutual_info_score`, `sklearn.decomposition.PCA`), `matplotlib`, `seaborn`.
- **Reproducibility Contract:** `RANDOM_STATE = 42` and `SENSITIVITY_SEEDS = (42, 100, 2026, 7, 999)`.

### 6.1 Step 1: Configuration, SHA-256 Integrity Check, and Feature Engineering

```python
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.cluster.hierarchy import cophenet, dendrogram, fcluster, linkage
from scipy.spatial.distance import pdist
from sklearn.cluster import AgglomerativeClustering
from sklearn.decomposition import PCA
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

# Global reproducibility & language constants
RANDOM_STATE: int = 42
SENSITIVITY_SEEDS: Tuple[int, ...] = (42, 100, 2026, 7, 999)
MICRO_SAMPLE_N: int = 60
DISCOVERY_SAMPLE_N: int = 3000
K_RANGE: range = range(2, 9)
PLOT_LANG: str = "es"  # Set to "es" for Spanish titles/labels (project default) or "en" for English


def resolve_project_root() -> Path:
    """Resolve the MineriaProtect repository root from any working directory."""
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

OUT_DIR = PROJECT_ROOT / "reports/clustering_jerarquico_jobpath"
FIG_DIR = OUT_DIR / "figures"
TAB_DIR = OUT_DIR / "tables"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TAB_DIR.mkdir(parents=True, exist_ok=True)


def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 hex digest of an input file to guarantee read-only integrity."""
    h = hashlib.sha256()
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
```

### 6.2 Step 2: Building the Clean Behavioral Matrices (`V_PERSON` and `V_EXPERIENCE`)

```python
UNIVERSITY_ORDINAL_MAP: Dict[str, float] = {
    "Secondary school": 1.0,
    "Bachelor": 2.0,
    "Master": 3.0,
    "PhD": 4.0,
}

V_PERSON: List[str] = [
    "n_jobs",
    "span_q",
    "dur_mean",
    "overlap_ratio",
    "mean_skills_competence",
    "mean_skills_knowledge",
    "mean_prop_competence",
    "nivel_academico_ord_imputado",
    "educacion_no_reportada",
]

V_EXPERIENCE: List[str] = [
    "dur_q",
    "job_order",
    "n_skills_competence",
    "n_skills_knowledge",
    "prop_competence_essential",
    "nivel_academico_ord_imputado",
    "educacion_no_reportada",
]


def prepare_classified_experiences(csv_path: Path, split_map_path: Path) -> pd.DataFrame:
    """Load clean CSV, filter classified ESCO rows in RAM, and derive non-leaky behavioral features."""
    df = pd.read_csv(csv_path, low_memory=False)
    split_map = pd.read_csv(split_map_path)

    # Filter classified occupations in RAM (1,738,738 rows across 352,093 persons)
    df = df.loc[df["occupation_code"].notna()].copy()
    df = df.merge(split_map[["resume_id", "split"]], on="resume_id", how="inner")

    # Derive quarter ordinals and job duration dur_q (right-censored at 2026-Q1 = 8105)
    from scripts.ScriptsCsv.Transformacion.date_features import add_date_ordinals, add_job_order

    df = add_date_ordinals(df, start_col="start_date", end_col="end_date")
    df["dur_q"] = df["dur_q"].clip(lower=1.0)
    df = add_job_order(df, person_col="resume_id", time_col="start_ord")

    # Competence proportion (avoids E = C + K collinearity while capturing skill balance)
    denom = df["n_skills_essential"].clip(lower=1.0)
    df["prop_competence_essential"] = (df["n_skills_competence"] / denom).clip(0.0, 1.0)

    # MNAR education handling: binary indicator + median-imputed ordinal (NEVER fill with 0)
    df["educacion_no_reportada"] = (
        df["university_level"].isna() | df["university_level"].astype(str).str.strip().eq("No reportado")
    ).astype(float)
    df["nivel_academico_ord"] = df["university_level"].map(UNIVERSITY_ORDINAL_MAP)
    train_edu_median = float(df.loc[df["split"] == "train", "nivel_academico_ord"].median())
    df["nivel_academico_ord_imputado"] = df["nivel_academico_ord"].fillna(train_edu_median)

    # Post-hoc target and ISCO major group (NEVER included in X; used ONLY for post-hoc profiling)
    df["reincide"] = (df["veces_ese_oficio"] > 1).astype(int)
    df["isco_major_1d"] = df["isco_group"].astype(str).str.strip().str[0]
    return df


def aggregate_to_person_level(df_exp: pd.DataFrame) -> pd.DataFrame:
    """Collapse classified experiences to 1 row per resume_id (352,093 persons) without target leakage."""
    grouped = df_exp.groupby("resume_id", sort=True)
    person = grouped.agg(
        split=("split", "first"),
        n_jobs=("resume_id", "size"),
        min_start=("start_ord", "min"),
        max_end=("end_ord", "max"),
        dur_total=("dur_q", "sum"),
        dur_mean=("dur_q", "mean"),
        mean_skills_essential=("n_skills_essential", "mean"),
        mean_skills_competence=("n_skills_competence", "mean"),
        mean_skills_knowledge=("n_skills_knowledge", "mean"),
        mean_prop_competence=("prop_competence_essential", "mean"),
        nivel_academico_ord_imputado=("nivel_academico_ord_imputado", "first"),
        educacion_no_reportada=("educacion_no_reportada", "first"),
        # Post-hoc validation columns ONLY (excluded from V_PERSON)
        n_occ_posthoc=("occupation_code", "nunique"),
        max_veces_posthoc=("veces_ese_oficio", "max"),
        tasa_reincide_persona_posthoc=("reincide", "mean"),
        isco_major_modal_posthoc=("isco_major_1d", lambda s: s.mode().iloc[0] if not s.mode().empty else "Unknown"),
    ).reset_index()

    person["span_q"] = (person["max_end"] - person["min_start"] + 1.0).clip(lower=1.0)
    person["overlap_ratio"] = person["dur_total"] / person["span_q"]
    person["any_repeated_posthoc"] = (person["max_veces_posthoc"] > 1).astype(int)
    person["exploration_ratio_posthoc"] = person["n_occ_posthoc"] / person["n_jobs"]
    return person
```

### 6.3 Step 3: Stratified Sampling, Linkage Tournament (`ward` vs. `complete`, `average`, `single`), and Dendrograms

```python
def draw_stratified_sample(
    df: pd.DataFrame,
    n_sample: int,
    strata_cols: List[str],
    seed: int = RANDOM_STATE,
) -> pd.DataFrame:
    """Draw a reproducible stratified subsample from Train without replacement."""
    train_df = df.loc[df["split"] == "train"].copy()
    train_df["_stratum"] = train_df[strata_cols].astype(str).agg("_".join, axis=1)
    rng = np.random.default_rng(seed)

    proportions = train_df["_stratum"].value_counts(normalize=True)
    sampled_indices: List[int] = []
    for stratum, prop in proportions.items():
        sub_idx = train_df.index[train_df["_stratum"] == stratum].to_numpy()
        k_take = max(1, int(round(prop * n_sample)))
        k_take = min(k_take, len(sub_idx))
        chosen = rng.choice(sub_idx, size=k_take, replace=False)
        sampled_indices.extend(chosen.tolist())

    # Adjust to exact n_sample
    if len(sampled_indices) > n_sample:
        sampled_indices = rng.choice(sampled_indices, size=n_sample, replace=False).tolist()
    elif len(sampled_indices) < n_sample:
        remaining = list(set(train_df.index) - set(sampled_indices))
        extra = rng.choice(remaining, size=n_sample - len(sampled_indices), replace=False).tolist()
        sampled_indices.extend(extra)

    return train_df.loc[sorted(sampled_indices)].drop(columns=["_stratum"]).reset_index(drop=True)


def run_linkage_tournament(
    X_scaled: np.ndarray,
    k_eval: int = 4,
) -> Tuple[pd.DataFrame, Dict[str, np.ndarray]]:
    """Benchmark ward, complete, average, and single linkage on the standardized discovery sample."""
    pairwise_dists = pdist(X_scaled, metric="euclidean")
    methods = ("ward", "complete", "average", "single")
    rows = []
    linkage_matrices: Dict[str, np.ndarray] = {}

    for method in methods:
        Z = linkage(X_scaled, method=method, metric="euclidean")
        linkage_matrices[method] = Z
        coph_corr, _ = cophenet(Z, pairwise_dists)

        labels = fcluster(Z, t=k_eval, criterion="maxclust") - 1
        n_unique = len(np.unique(labels))
        cluster_sizes = pd.Series(labels).value_counts().sort_index().to_dict()
        largest_share_pct = float(pd.Series(labels).value_counts(normalize=True).max() * 100.0)

        if n_unique > 1:
            sil = float(silhouette_score(X_scaled, labels))
            dbi = float(davies_bouldin_score(X_scaled, labels))
            chi = float(calinski_harabasz_score(X_scaled, labels))
        else:
            sil, dbi, chi = float("nan"), float("nan"), float("nan")

        rows.append(
            {
                "metodo_linkage": method,
                "correlacion_cofenetica": round(coph_corr, 4),
                "k_referencia": k_eval,
                "silhouette_score": round(sil, 4),
                "davies_bouldin_index": round(dbi, 4),
                "calinski_harabasz_index": round(chi, 2),
                "pct_cluster_mas_grande": round(largest_share_pct, 2),
                "distribucion_tamanos": str(cluster_sizes),
                "diagnostico_es": (
                    "SELECCIONADO (minimiza varianza intra-cluster; grupos balanceados y compactos)"
                    if method == "ward"
                    else (
                        "Efecto encadenamiento (chaining: 1 mega-cluster absorbe >95% de la muestra)"
                        if largest_share_pct > 90.0
                        else "Alternativa válida pero con menor cohesión esférica que Ward"
                    )
                ),
            }
        )
    return pd.DataFrame(rows), linkage_matrices
```

### 6.4 Step 4: Evaluating Cuts ($k \in \{2 \dots 8\}$) & Plotting the Dendrograms

```python
def evaluate_dendrogram_cuts(
    Z_ward: np.ndarray,
    X_scaled: np.ndarray,
    k_range: range = K_RANGE,
) -> pd.DataFrame:
    """Evaluate horizontal cuts k=2..8 on Ward linkage using Silhouette, Davies-Bouldin, and merge jumps."""
    n_obs = X_scaled.shape[0]
    rows = []
    for k in k_range:
        labels = fcluster(Z_ward, t=k, criterion="maxclust") - 1
        sil = float(silhouette_score(X_scaled, labels))
        dbi = float(davies_bouldin_score(X_scaled, labels))
        chi = float(calinski_harabasz_score(X_scaled, labels))

        # Height at which k clusters merge into k-1 clusters: row (n_obs - k) of Z
        h_merge_to_k_minus_1 = float(Z_ward[n_obs - k, 2])
        h_prev_merge = float(Z_ward[n_obs - k - 1, 2]) if (n_obs - k - 1) >= 0 else 0.0
        vertical_jump = h_merge_to_k_minus_1 - h_prev_merge
        optimal_cut_height = 0.5 * (h_merge_to_k_minus_1 + h_prev_merge)

        counts = pd.Series(labels).value_counts()
        rows.append(
            {
                "k_clusters": k,
                "altura_fusion_superior": round(h_merge_to_k_minus_1, 3),
                "altura_fusion_anterior": round(h_prev_merge, 3),
                "salto_vertical_distancia": round(vertical_jump, 3),
                "altura_corte_recomendada": round(optimal_cut_height, 3),
                "silhouette_score": round(sil, 4),
                "davies_bouldin_index": round(dbi, 4),
                "calinski_harabasz_index": round(chi, 2),
                "tamano_min_cluster": int(counts.min()),
                "tamano_max_cluster": int(counts.max()),
                "pct_max_cluster": round(float(counts.max() / n_obs * 100.0), 2),
            }
        )
    return pd.DataFrame(rows)


def plot_dendrograms_es(
    Z_micro: np.ndarray,
    Z_discovery: np.ndarray,
    cut_height_discovery: float,
    k_opt: int,
    fig_dir: Path,
    lang: str = PLOT_LANG,
) -> None:
    """Generate micro-sample (n=60) and truncated discovery (n=3000) dendrograms in Spanish (or English)."""
    # 1. Micro-sample full dendrogram (n=60)
    fig, ax = plt.subplots(figsize=(12, 5.5), dpi=300)
    dendrogram(Z_micro, ax=ax, leaf_rotation=90.0, leaf_font_size=8.0, color_threshold=0.7 * np.max(Z_micro[:, 2]))
    if lang == "es":
        ax.set_title("Dendrograma Jerárquico Aglomerativo (Linkage Ward · Micro-Muestra Estratificada n = 60)", fontsize=13, fontweight="bold")
        ax.set_xlabel("Índice de observación en la micro-muestra (personas clasificadas)", fontsize=11)
        ax.set_ylabel("Distancia de fusión de Ward (escala estandarizada)", fontsize=11)
    else:
        ax.set_title("Agglomerative Hierarchical Dendrogram (Ward Linkage · Stratified Micro-Sample n = 60)", fontsize=13, fontweight="bold")
        ax.set_xlabel("Observation index in micro-sample (classified persons)", fontsize=11)
        ax.set_ylabel("Ward fusion distance (standardized scale)", fontsize=11)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig(fig_dir / "01_dendrograma_micro_muestra_n60_ward.png", dpi=300)
    plt.close(fig)

    # 2. Discovery sample truncated dendrogram (n=3,000, lastp=30) with optimal cut line
    fig, ax = plt.subplots(figsize=(12, 6.0), dpi=300)
    dendrogram(
        Z_discovery,
        ax=ax,
        truncate_mode="lastp",
        p=30,
        show_leaf_counts=True,
        leaf_rotation=45.0,
        leaf_font_size=9.0,
        color_threshold=cut_height_discovery,
    )
    ax.axhline(
        y=cut_height_discovery,
        color="#D62728",
        linestyle="--",
        linewidth=2.0,
        label=(
            f"Corte óptimo k = {k_opt} (altura = {cut_height_discovery:.2f})"
            if lang == "es"
            else f"Optimal cut k = {k_opt} (height = {cut_height_discovery:.2f})"
        ),
    )
    if lang == "es":
        ax.set_title(f"Dendrograma Truncado (30 Ramas Superiores · Muestra n = 3,000 · Ward · Corte k = {k_opt})", fontsize=13, fontweight="bold")
        ax.set_xlabel("Tamaño de rama fusionada (entre paréntesis: número de personas)", fontsize=11)
        ax.set_ylabel("Distancia de fusión de Ward (Δ varianza intra-cluster)", fontsize=11)
    else:
        ax.set_title(f"Truncated Dendrogram (Top 30 Branches · Sample n = 3,000 · Ward · Cut k = {k_opt})", fontsize=13, fontweight="bold")
        ax.set_xlabel("Merged branch size (in parentheses: number of persons)", fontsize=11)
        ax.set_ylabel("Ward fusion distance (Δ within-cluster variance)", fontsize=11)
    ax.legend(loc="upper right", frameon=True)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig(fig_dir / "02_dendrograma_truncado_n3000_corte_optimo.png", dpi=300)
    plt.close(fig)
```

---

## 7. Cluster Evaluation, Original-Scale Profiling, and Business Naming ("Retrato Robot")

### 7.1 Full-Dataset Assignment & Original-Scale Profiling (`groupby().mean()`)

Once $k^*$ is selected on the discovery sample (`AgglomerativeClustering(n_clusters=k_opt, metric="euclidean", linkage="ward")`), we:
1. Profile the discovery sample directly (`05_perfiles_clusters_personas_escala_original.csv`), **and**
2. Fit a `NearestCentroid()` classifier on `(X_discovery_scaled, labels_hc)` to assign all `352,093` classified persons (`281,674` Train + `70,419` Test) to their nearest Ward cluster centroid in standardized space, verifying that full-dataset profiles match discovery-sample profiles within sampling noise.

```python
def fit_final_hierarchical_and_profile(
    df_discovery: pd.DataFrame,
    df_full: pd.DataFrame,
    feature_cols: List[str],
    k_opt: int,
    posthoc_target_col: str = "any_repeated_posthoc",
) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
    """Fit final AgglomerativeClustering(linkage='ward'), project onto full dataset, and profile in original scale."""
    scaler = StandardScaler()
    X_disc_scaled = scaler.fit_transform(df_discovery[feature_cols])

    hc = AgglomerativeClustering(n_clusters=k_opt, metric="euclidean", linkage="ward")
    disc_labels = hc.fit_predict(X_disc_scaled)

    # Order cluster IDs deterministically by ascending mean career job volume (or primary feature)
    df_disc_out = df_discovery.copy()
    df_disc_out["cluster_raw"] = disc_labels
    order_map = (
        df_disc_out.groupby("cluster_raw")[feature_cols[0]]
        .mean()
        .sort_values()
        .index.to_list()
    )
    remap = {old_id: new_id for new_id, old_id in enumerate(order_map)}
    df_disc_out["cluster"] = df_disc_out["cluster_raw"].map(remap)

    # Nearest-centroid out-of-sample projection onto all 352,093 persons
    nc = NearestCentroid(metric="euclidean")
    nc.fit(X_disc_scaled, df_disc_out["cluster"].to_numpy())
    X_full_scaled = scaler.transform(df_full[feature_cols])
    df_full_out = df_full.copy()
    df_full_out["cluster"] = nc.predict(X_full_scaled)

    # Profile in ORIGINAL unscaled units (NEVER report standardized z-scores as raw means)
    profile = df_disc_out.groupby("cluster")[feature_cols].mean().round(2)
    profile["n_muestra"] = df_disc_out["cluster"].value_counts().sort_index()
    profile["pct_muestra"] = (profile["n_muestra"] / len(df_disc_out) * 100.0).round(2)
    profile["n_total_proyectado"] = df_full_out["cluster"].value_counts().sort_index()
    profile["pct_total_proyectado"] = (profile["n_total_proyectado"] / len(df_full_out) * 100.0).round(2)

    # Post-hoc external validation against target (reincide / any_repeated) and ISCO group
    base_rate = float(df_disc_out[posthoc_target_col].mean())
    cluster_rate = df_disc_out.groupby("cluster")[posthoc_target_col].mean()
    profile["tasa_reincide_posthoc_pct"] = (cluster_rate * 100.0).round(2)
    profile["lift_reincide_posthoc"] = (cluster_rate / max(base_rate, 1e-9)).round(3)

    if "isco_major_modal_posthoc" in df_disc_out.columns:
        profile["isco_grupo_dominante_posthoc"] = (
            df_disc_out.groupby("cluster")["isco_major_modal_posthoc"]
            .agg(lambda s: s.mode().iloc[0] if not s.mode().empty else "N/A")
        )

    return profile.reset_index(), df_full_out, X_disc_scaled
```

### 7.2 Mandatory Segment Naming & Business Action Template ("Retrato Robot")

Every cluster MUST be translated into a business-ready card in Spanish (never leaving generic labels like `"Cluster 0"` or `"Grupo 1"`):

| Cluster ID | Actionable Segment Name (Spanish) | Robot Portrait (`Retrato Robot` in Original Units) | Post-Hoc `reincide` Signal (External Validation) | Concrete Labor Observatory / University Action |
|---|---|---|---|---|
| `0` | **Inserción Temprana o Trayectoria Corta en Oficios Operativos** | Low `n_jobs` ($\approx 1\text{–}2$), short career span `span_q`, moderate practical skills, high share of secondary/bachelor education. | Below-average occupational repetition (`Lift < 1.0x`). | **First-Job Employability Bridge:** Early career orientation and core practical skill certification. |
| `1` | **Especialistas Estables de Permanencia Prolongada** | Moderate `n_jobs` ($\approx 3\text{–}4$), high average duration per job (`dur_mean` $\ge 12$ quarters), low overlap (`overlap_ratio` $\approx 1.0$). | Moderate repetition concentrated within the same specialty. | **Continuous Specialization & Up-Skilling:** Micro-credentials to update technical knowledge within their career track. |
| `2` | **Trayectorias Intensivas en Conocimiento y Alta Exigencia ESCO** | High `mean_skills_competence` and `mean_skills_knowledge`, higher academic qualification (`Bachelor`/`Master`), multi-year career span. | Distinct repetition rate driven by specialized professional roles. | **Advanced R&D / Leadership Track:** Postgraduate linkage and specialized industry-academia placement. |
| `3` | **Rotación Frecuente / Multi-Empleo Solapado** | High `n_jobs` ($\ge 7$), high `overlap_ratio` ($> 1.3$) or short `dur_mean`, broad occupational transitions. | High post-hoc repetition rate (`Lift > 1.25x`). | **Career Stabilization & Portfolio Consolidation:** Advisory on formalizing scattered short-term contracts into stable career paths. |

*(Note: Exact numeric thresholds in the robot portrait MUST be populated dynamically from `05_perfiles_clusters_personas_escala_original.csv` and `06_perfiles_clusters_experiencias_escala_original.csv` — zero hardcoded literals in narrative text!)*

---

## 8. Cross-Method Comparison: Agglomerative Hierarchical vs. K-Means

| Criterion | Agglomerative Hierarchical (`01_agglomerative_hierarchical_clustering.md`) | K-Means (`02_kmeans_clustering.md`) |
|---|---|---|
| **Computational Complexity** | $O(n^2)$ space and $O(n^2 \log n)$ to $O(n^3)$ time $\to$ requires stratified sampling ($n = 3,000\text{–}5,000$) + Nearest-Centroid projection | $O(n \cdot k \cdot d \cdot i)$ linear in rows $\to$ runs directly on all `352,093` persons and `1,738,738` experiences |
| **Must $k$ Be Fixed Beforehand?** | **No:** one linkage tree `Z` exposes the entire hierarchy across all $k$ | **Yes:** requires fitting a separate model for each candidate $k$ |
| **Output Structure** | Nested taxonomy (dendrogram) + flat partition after horizontal cut | Flat partition into $k$ Voronoi cells around centroids |
| **Determinism** | **100% deterministic** on a given sample (no random centroid initialization) | Depends on centroid seeding (mitigated via `init="k-means++"`, `n_init=10`, `random_state=42`) |
| **Ideal Role in JobPath** | Discover hierarchical taxonomy, benchmark linkages, and validate optimal $k^*$ | Operational full-population assignment and centroid reporting |

**Mandatory Concordance Check with K-Means:**
On the shared discovery sample ($n = 3,000$, `seed=42`), compute the agreement between `AgglomerativeClustering(n_clusters=k_opt, linkage="ward")` and `KMeans(n_clusters=k_opt, n_init=10, random_state=42)` using:
- **Adjusted Rand Index (`adjusted_rand_score`)**
- **Normalized Mutual Information (`normalized_mutual_info_score`)**

---

## 9. Limitations & Version B (`sin_outliers`) vs. Version A (`con_outliers`) Sensitivity Protocol

1. **Sensitivity to Outliers and Scale:** Even under `ward` linkage, extreme unclipped values in `n_skills_essential` (up to `129` in Version A vs. `47.5` IQR cap in Version B) or `dur_q` inflate Euclidean distances and force the dendrogram to spend top-level splits isolating tiny outlier branches.
2. **Irrevocable Greedy Merges:** Once two observations or clusters merge at a lower step of the hierarchy, they can never be separated at a higher step.
3. **Spherical Bias of Ward Linkage:** Like K-Means, Ward's criterion favors compact globular clusters and can split elongated manifolds.
4. **Mandatory Version B vs. Version A Sensitivity Experiment (`09_comparacion_sensibilidad_version_b_vs_version_a.csv`):**
   - Run the exact same 5-seed stratified sampling protocol (`seeds = [42, 100, 2026, 7, 999]`, $n = 3,000$ persons per seed) on **Version B (`empleos_limpio_con_competencias_sin_outliers.csv`)** and **Version A (`empleos_unificado_limpio.csv`)** using identical `resume_id` draws per seed.
   - Report `mean ± SD` across the 5 seeds for Cophenetic Correlation, Silhouette Score, Davies-Bouldin Index, largest cluster share ($\%$), and cross-version Adjusted Rand Index (`ARI(labels_B, labels_A)`).
   - Justify choosing **Version B (`sin_outliers`)** as primary for distance-based clustering when raw outliers in Version A degrade cluster balance or silhouette cohesion.

---

## 10. Quality Criteria & Frequent Mistakes to Avoid

### Signals of a Well-Executed Hierarchical Segmentation

- `StandardScaler` is fitted **before** computing `pdist` / `linkage`, and this is explicitly verified (`mean ≈ 0`, `std ≈ 1`).
- Both a readable leaf-level micro-dendrogram ($n = 60$) and a quantitative truncated discovery dendrogram ($n = 3,000$, `p = 30`) are plotted with the optimal horizontal cut clearly marked.
- The choice of `ward` linkage and optimal cut $k^*$ is justified quantitatively using Cophenetic Correlation, Silhouette Score, Davies-Bouldin Index, and vertical merge jumps.
- Profile tables report **real unscaled units** alongside post-hoc `reincide` rates and Lift, and every number in the narrative is generated dynamically from the result DataFrames.

### 7 Frequent Mistakes to Avoid in `MineriaProtect`

1. **Running `linkage()` on all `1,738,738` rows or `352,093` persons:** Will immediately crash with `MemoryError`. Always use the 3-tier stratified sampling + Nearest-Centroid projection protocol.
2. **Clustering without `StandardScaler`:** Variables with larger numeric range (`span_q`, `n_skills_competence`) will completely dictate the dendrogram merges.
3. **Leaking `reincide`, `veces_ese_oficio`, `n_returns`, or `exploration_ratio` into `X`:** Turns unsupervised clustering into a circular tautology. Keep them strictly post-hoc.
4. **Including all three ESCO skill counts (`essential`, `competence`, `knowledge`) simultaneously in `X`:** Violates independence because $E = C + K$ in `99.10%` of rows, double-weighting skill volume in Euclidean distance.
5. **Filling `university_level == 'No reportado'` with `0`:** Creates a false ordinal rank below secondary education. Always use `educacion_no_reportada` ($0/1$) + median-imputed ordinal level.
6. **Narrating standardized z-scores as real values:** Never say *"this cluster has -0.45 jobs"*; always compute `df.groupby("cluster")[V].mean()` on original unscaled variables.
7. **Using `single` linkage for operational segmentation:** Produces a single giant chained cluster plus 1-person outlier branches.

---

## 11. End-to-End Business Workflow in the JobPath Labor Observatory

| Stage | Action in `MineriaProtect` |
|---|---|
| **1. Build Behavioral Features** | Aggregate non-leaky career trajectory features (`n_jobs`, `span_q`, `dur_mean`, `overlap_ratio`, ESCO skill mix, MNAR education) on Version B (`sin_outliers`). |
| **2. Explore Hierarchy & Cut** | Run linkage tournament (`ward` priority), inspect dendrogram vertical jumps, and select $k^*$ with Silhouette + Davies-Bouldin + operational capacity. |
| **3. Project & Profile** | Assign full population via standardized `NearestCentroid`, compute real-unit means/medians, and audit post-hoc `reincide` Lift and ISCO mix. |
| **4. Name & Assign Ownership** | Give each cluster a descriptive Spanish name (`Retrato Robot`) and assign an institutional owner (Career Services, Curriculum Committee, Alumni Observatory). |
| **5. Validate & Cross-Check** | Compare $k^*$ and cluster assignments against full-scale K-Means (`02_kmeans_clustering.md`) via Adjusted Rand Index (`ARI`). |

---

## 12. Evaluation Rubric & Verification Checklist

| Evidence Deliverable | Core Criterion | Weight |
|---|---|---|
| **Linkage Tournament & Cut Table ($k = 2\dots 8$)** | Correct calculations on **scaled** data (`ward`, `complete`, `average`, `single`), Cophenetic Correlation, Silhouette, Davies-Bouldin, and vertical jump reading | 30% |
| **Dendrograms ($n = 60$ micro & $n = 3,000$ truncated)** | Executed with horizontal cut line, Spanish titles/labels, and verbally contrasted against the chosen $k^*$ and K-Means | 20% |
| **Cluster Profiles in Original Scale + Post-Hoc `reincide`** | Correct `groupby().mean()` on original units + post-hoc `reincide` rate/Lift + Version B vs. Version A 5-seed stability | 25% |
| **Actionable Segment Names & Observatory Campaigns** | Descriptive Spanish names (profile + behavior) + concrete institutional intervention per cluster | 25% |

### Mandatory Automated Honesty Guard Cell (Final Cell of `8.1_clustering_jerarquico.ipynb`)

Before completing execution, the final cell of the notebook MUST assert:
1. **Input SHA-256 Integrity:** `CLEAN_VERSION_B`, `CLEAN_VERSION_A`, and `SPLIT_MAP_PATH` hashes are identical before and after execution.
2. **Zero Target Leakage in `X`:** Neither `reincide` nor `veces_ese_oficio*` nor `n_returns*` is present in `V_PERSON` or `V_EXPERIENCE`.
3. **Standardization Check:** `np.allclose(X_disc_scaled.mean(axis=0), 0, atol=1e-6)` and `np.allclose(X_disc_scaled.std(axis=0), 1, atol=1e-6)`.
4. **Narrative Number Verifier:** Every number cited in `Bitacora_Clustering_Jerarquico.md` and `Comparacion_A_vs_B_Clustering_Jerarquico.md` appears in a table of the same `[CURRENT]` run.

---

## 13. Key Takeaways to Remember

- Agglomerative Hierarchical Clustering builds a **bottom-up taxonomy** without requiring $k$ upfront; cutting the **Ward dendrogram** provides visual and mathematical evidence for how many natural segments exist.
- Because pairwise distance matrices scale as $O(n^2)$, large bases (`352,093` persons / `1,738,738` experiences) require a **stratified discovery sample ($n = 3,000$) + 5-seed stability check + Nearest-Centroid full projection**, paired with a **$n = 60$ micro-sample** for leaf-level visual inspection.
- Always standardize (`StandardScaler`) before computing Euclidean distances, use **Version B (`sin_outliers`)** as primary to prevent extreme outliers from distorting Ward variance merges, and keep `reincide` strictly post-hoc.
- The deliverable is **Name + Original-Scale Robot Portrait + Concrete Observatory Action**.

---

## 14. Connection to Next Steps

- **Companion Guide (`02_kmeans_clustering.md`):** Uses the $k^*$ validated by the Ward dendrogram cut to execute a full-scale flat K-Means segmentation across all `352,093` classified persons and `1,738,738` experiences, extracting original-scale centroids and 2D PCA cluster projections.
- **Session 10 (Association Rules · Apriori):** Discovers frequent co-occurring occupational and skill transition baskets across career sequences.
