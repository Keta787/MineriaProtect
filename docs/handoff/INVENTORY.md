# INVENTORY.md · Inventario Técnico, Gobernanza y Auditoría de Reproducibilidad (`JobPath`)

> **Proyecto:** `JobPath` (`MineriaProtect`) — Estudio de trayectorias laborales sobre **JobHop v2** enriquecido con **ESCO v1.2.1** (UNIMINUTO Ibagué, Colombia)  
> **Fase de Handoff:** Fase 1 · Auditoría de Ciencia de Datos y Analítica de Reproducibilidad  
> **Fecha de auditoría:** `2026-11-22`  
> **Repositorio remoto:** `https://github.com/Keta787/MineriaProtect`  
> **Clon local principal (código y cuadernos a `HEAD`):** `c:\Users\User\Documents\JobPath\MineriaProtect` (commit `00e8a6b`, `2026-11-22 13:55:14 -0500`)  
> **Clon local secundario (almacén físico de `data/`):** `c:\Users\User\Documents\JobPath\Version 2\MineriaProtect` (commit `263c869`, `2026-11-20 08:22:09 -0500`)

---

## 1. Estado de Sincronización de las Dos Copias Locales del Repositorio

Durante la inspección del directorio de trabajo `c:\Users\User\Documents\JobPath` se identificaron dos clones locales del mismo repositorio Git:

| Propiedad | Clon Principal (`c:\Users\User\Documents\JobPath\MineriaProtect`) | Clon Secundario (`c:\Users\User\Documents\JobPath\Version 2\MineriaProtect`) |
|---|---|---|
| **Commit `HEAD`** | `00e8a6b` (`2026-11-22 13:55:14 -0500` · `main`) | `263c869` (`2026-11-20 08:22:09 -0500` · `Naive_KNN`) |
| **Cuadernos en `notebooks/refactor/`** | **12 documentos completos** (`1.0` a `8.1`, más guías y bitácoras de árboles y clustering) | **10 documentos** (`1.0` a `7.2`; **faltan** `8.0_kmeans_clustering.ipynb` y `8.1_clustering_jerarquico.ipynb`) |
| **Paquetes en `scripts/ScriptsCsv/`** | **9 paquetes SOLID** (`Preproccesing`, `Transformacion`, `EDA`, `Modelado`, `ArbolDecision`, `NaiveBayes`, `KNN`, `KMeans`, `ClusteringJerarquico`) | **7 paquetes** (faltan `KMeans` y `ClusteringJerarquico`) |
| **Reportes en `reports/`** | **7 carpetas** (`eda_jobpath`, `modelado_jobpath`, `arbol_decision_jobpath`, `naive_bayes_jobpath`, `knn_jobpath`, `kmeans_jobpath`, `clustering_jerarquico_jobpath`) | **5 carpetas** (faltan `kmeans_jobpath` y `clustering_jerarquico_jobpath`) |
| **Carpeta `data/` (en `.gitignore`)** | **Ausente** (`data/` no existe en este clon recién descargado) | **Presente y completa (`25,910,401,168 bytes` = `24.13 GiB` / `25.91 GB`)** |
| **Idénticos en cuadernos `2.0` a `7.2`** | **Sí (`100 %` byte-idénticos)** entre ambos clones (`2.0`, `3.0`, `4.0`, `4.1`, `5.0`, `6.0`, `7.0`, `7.1`, `7.2`) | **Sí (`100 %` byte-idénticos)** |

---

## 2. Inventario de Cuadernos y Documentos en `notebooks/refactor/` (Propósito, Entradas, Salidas y Estado de Ejecución)

### 2.1 Auditoría de Salidas Guardadas (Regla #6 — Cero Re-ejecución Requerida)

Se auditaron programáticamente los 11 cuadernos `.ipynb` mediante inspección del árbol JSON (`cells`, `cell_type`, `execution_count`, `outputs`). **Todos los 11 cuadernos tienen el `100 %` de sus celdas ejecutadas y sus salidas guardadas** (la única celda de código con `outputs=[]` en todo el repositorio es la celda 2 de `3.0_transformacion.ipynb`, `exec_count=2`, la cual solo asigna diccionarios de configuración en memoria sin `print` ni `display`). **No se requiere re-ejecutar ningún cuaderno.**

| # | Archivo en `notebooks/refactor/` | Fase CRISP-DM / KDD | Celdas Totales / Código / Con Salida | Módulos Python Importados | Entradas Principales | Salidas Producidas | Estado de Salidas |
|---|---|---|---|---|---|---|---|
| **1.0** | `1.0_comprension_negocio.md` (`7,014 bytes`) | CRISP-DM Fase 1 (Business Understanding) · KDD Selección | Documento Markdown (`77` líneas) | N/A (documento estático) | Contexto académico UNIMINUTO, descripción de JobHop v2, ESCO v1.2.1 y OLE (descartada) | Acta de constitución analítica del proyecto (preguntas de negocio y técnica, alcance exploratorio) | `VERIFIED` (Markdown) |
| **2.0** | `2.0_preprocesamiento_jobpath.ipynb` (`542,578 bytes`) | CRISP-DM Fase 3 (Data Preparation · Clean) · KDD Preprocesamiento | `38` totales / `19` código / `19` con `outputs` (`exec_count` `1..19`) | `scripts.ScriptsCsv.Preproccesing` (`config`, `utils`, `io`, `diagnosis`, `duplicates`, `categories`, `missing`, `imputation`, `outliers_iqr`, `funnel`, `validation`, `pipeline`) | `data/03_processed/empleos_unificado_limpio.csv` (**Versión A**, `1,871,014 × 23`, `355,308` personas) | `data/03_processed/empleos_limpio_con_competencias_sin_outliers.csv` (**Versión B**, `1,871,014 × 23`, winsorizada por IQR `k=1.5` en 4 columnas; `193,596` filas recortadas, `0` filas eliminadas) + tablas y boxplots en celda | `VERIFIED` (`19/19` celdas con salida) |
| **3.0** | `3.0_transformacion.ipynb` (`131,000 bytes`) | CRISP-DM Fase 3 (Select / Construct / Format Data) · KDD Transformación | `31` totales / `16` código / `15` con `outputs` (`exec_count` `1..16`; celda 2 es solo asignación de constantes) | `scripts.ScriptsCsv.Transformacion` (`config`, `column_profile`, `comparison`, `date_features`, `decision_log`, `discretization`, `encoding`, `export`, `scaler_recommendation`, `scaling`, `split`, `validation`) | `data/03_processed/empleos_unificado_limpio.csv` (A) y `empleos_limpio_con_competencias_sin_outliers.csv` (B) (`1,871,014 × 23` cada uno) | Filtra a universo con oficio ESCO (`1,738,738` filas, `352,093` personas), aplica `GroupShuffleSplit(80/20, seed=42)` por `resume_id` y exporta `data/04_transformed/{con_outliers,sin_outliers}/{train,test}/{X,y}_*.csv` (`X_train: 1,391,018 × 2,985`, `X_test: 347,720 × 2,985`) + `transformers.joblib` | `VERIFIED` (`15/15` celdas con salida visible; `16/16` ejecutadas) |
| **4.0** | `4.0_PCA.ipynb` (`79,051 bytes`) | CRISP-DM Fase 3 · Diagnóstico espectral PCA (muestra `10,000` filas) | `6` totales / `4` código / `4` con `outputs` (`exec_count` `1..4`) | `scripts.ScriptsCsv.Transformacion.pca_diagnostic` (`run_pca`, `components_for_threshold`, `top_loadings`), `scaling`, `date_features`, `encoding` | Versiones A y B de `data/03_processed/` filtradas al universo clasificado (`1,738,738` filas), submuestra `n = 10,000` (`seed=42`) sobre `11` variables escaladas | Tablas de varianza explicada (`PC1..PC10`), número de componentes para `80 %` (`4` en A, `3` en B) y `90 %` (`5` en A y B), *loadings* principales y gráfico de varianza acumulada en el cuaderno (leído por `5.0_EDA`) | `VERIFIED` (`4/4` celdas con salida) |
| **4.1** | `4.1_PCA_completo.ipynb` (`80,245 bytes`) | CRISP-DM Fase 3 · Diagnóstico de estabilidad PCA (muestra `50,000` filas) | `6` totales / `4` código / `4` con `outputs` (`exec_count` `1..4`) | `scripts.ScriptsCsv.Transformacion.pca_diagnostic`, `scaling`, `date_features`, `encoding` | Versiones A y B de `data/03_processed/` filtradas al universo clasificado (`1,738,738` filas), submuestra `n = 50,000` (`seed=42`) sobre `11` variables escaladas | Tablas de varianza explicada (`PC1..PC10`), componentes para `80 %` (`4` en A, `3` en B) y `90 %` (`5` en A y B), *loadings* principales y gráfico de estabilidad (leído por `5.0_EDA`) | `VERIFIED` (`4/4` celdas con salida) |
| **5.0** | `5.0_EDA_jobpath.ipynb` (`2,199,666 bytes`) | CRISP-DM Fase 2 (Data Understanding · iteración formal) · KDD Exploración | `76` totales / `24` código / `24` con `outputs` (`exec_count` `1..24`) | `scripts.ScriptsCsv.EDA` (`config`, `loader`, `profiling`, `descriptive`, `person_level`, `transitions`, `bivariate`, `pca_evidence`, `target`, `leakage`, `split_map`, `plots`, `validation`, `decision_log`, `pipeline`) | `data/03_processed/` (A y B), `data/04_transformed/` (`y_train`, `y_test`, cabecera + 2 cols de fuga de `X_train`, hashes SHA-256 de los 10 artefactos), `4.0_PCA.ipynb` y `4.1_PCA_completo.ipynb` | `28` figuras PNG (`g01` a `g30`, sin `g18` ni `g24` que es tabla en cuaderno) en `reports/eda_jobpath/figures/`, mapa oficial `reports/eda_jobpath/tables/split_map_resume_id.csv` (`355,308` personas) y `bitacora_decisiones_v1_vs_v2.csv` | `VERIFIED` (`24/24` celdas con salida) |
| **6.0** | `6.0_modelado_fase4_jobpath.ipynb` (`599,049 bytes`) | CRISP-DM Fase 4 y 5 (Modeling & Evaluation · Baselines y Techo sin fuga) | `19` totales / `6` código / `6` con `outputs` (`exec_count` `1..6`) | `scripts.ScriptsCsv.Modelado` (`config`, `dataset_builder`, `evaluation`, `plots`, `pipeline`) | `data/03_processed/` (A y B), `data/04_transformed/` (`y_*.csv`, `transformers.joblib`, verificación contra `X_train.csv`), `reports/eda_jobpath/tables/split_map_resume_id.csv` | `4` figuras PNG (`m01`–`m04`) en `reports/modelado_jobpath/figures/` y `5` tablas CSV en `reports/modelado_jobpath/tables/` (`ablacion_fuga_colinealidad_cv.csv`, `resultados_cv_por_persona.csv`, `resultados_test_ab.csv`, `importancia_variables_sin_fuga.csv`, `bitacora_fase4_modelado.csv`) | `VERIFIED` (`6/6` celdas con salida) |
| **7.0** | `7.0_arbol_decision.ipynb` (`5,575,921 bytes`) | CRISP-DM Fase 4 y 5 · Modelado interpretable con 3 Árboles de Decisión CART (`max_depth=4`) | `29` totales / `14` código / `14` con `outputs` (`exec_count` `1..14`, corrida `RUN-20261117-225052`) | `scripts.ScriptsCsv.ArbolDecision` (`config`, `data_loader`, `block_builders`, `leakage_guard`, `tuning`, `tree_inspector`, `sensitivity`, `plots`, `markdown_writers`, `pipeline`) y `src.ScriptCsv.ArbolDecision` | `data/03_processed/` (A y B), `reports/eda_jobpath/tables/split_map_resume_id.csv`, `data/04_transformed/con_outliers/{train,test}/y_*.csv`, `reports/modelado_jobpath/tables/resultados_test_ab.csv` | `16` figuras PNG en `reports/arbol_decision_jobpath/figures/`, `13` archivos de reglas en `reports/arbol_decision_jobpath/rules/`, `77` tablas CSV en `reports/arbol_decision_jobpath/tables/`, más `Bitacora_Arbol_Decision.md` y `Comparacion_A_vs_B_Arbol_Decision.md` | `VERIFIED` (`14/14` celdas con salida) |
| **7.1** | `7.1_naive_bayes.ipynb` (`4,284,413 bytes`) | CRISP-DM Fase 4 y 5 · Modelado Probabilístico con Naive Bayes (`NB-G`, `NB-B`, `NB-H` Híbrido) y Patrones ISCO | `59` totales / `18` código / `18` con `outputs` (`exec_count` `1..18`) | `scripts.ScriptsCsv.NaiveBayes` (`config`, `feature_blocks`, `models`, `bayes_by_counting`, `outlier_diagnostics`, `evaluation`, `occupation_analysis`, `patterns`, `version_comparison`, `plots`, `pipeline`, `self_tests`) | `data/03_processed/` (A y B), `data/04_transformed/`, `split_map_resume_id.csv`, tablas de referencia de `6.0` y `7.0` | `16` figuras PNG (`nb01`–`nb16`) en `reports/naive_bayes_jobpath/figures/` y `37` tablas CSV en `reports/naive_bayes_jobpath/tables/` (incluyendo `decision_log_naive_bayes.csv`) | `VERIFIED` (`18/18` celdas con salida) |
| **7.2** | `7.2_knn.ipynb` (`3,401,551 bytes`) | CRISP-DM Fase 4 y 5 · K-Nearest Neighbors (`KNN-D`, `KNN-G`, `KNN-W`), Geometría, Escala, Outliers y Costo Computacional | `48` totales / `15` código / `15` con `outputs` (`exec_count` `1..15`) | `scripts.ScriptsCsv.KNN` (`config`, `feature_blocks`, `models`, `geometry`, `version_comparison`, `pilot_benchmark`, `chunked_predictor`, `evaluation`, `neighbors_explainer`, `patterns`, `plots`, `pipeline`, `self_tests`, `revision_checks`) | `data/03_processed/` (A y B), `data/04_transformed/`, `split_map_resume_id.csv`, tablas de referencia de `6.0`, `7.0` y `7.1` | `13` figuras PNG (`knn01`–`knn13`) en `reports/knn_jobpath/figures/`, `48` tablas CSV en `reports/knn_jobpath/tables/` (incluyendo `decision_log_knn.csv`) y `70` bloques de caché HDF/NPZ por modelo en `reports/knn_jobpath/cache/` | `VERIFIED` (`15/15` celdas con salida) |
| **8.0** | `8.0_kmeans_clustering.ipynb` (`1,813,563 bytes`) | CRISP-DM Fase 4 y 5 · Segmentación No Supervisada K-Means++ (`k*=4`) sobre Personas (`V_PERSON`) y Experiencias (`V_EXPERIENCE`) | `12` totales / `6` código / `6` con `outputs` (`exec_count` `1..6`, corrida `RUN-20261119-181140`) | `scripts.ScriptsCsv.KMeans` (`config`, `feature_builder`, `kmeans_engine`, `pca_and_plots`, `markdown_writers`) | `data/03_processed/` (**Versión B** como primaria y **Versión A** como sensibilidad), `reports/eda_jobpath/tables/split_map_resume_id.csv` | `7` figuras PNG en `reports/kmeans_jobpath/figures/`, `9` tablas CSV en `reports/kmeans_jobpath/tables/` (incluyendo `08_asignacion_clusters_personas_352093.csv`), más `Bitacora_KMeans.md` y `Comparacion_A_vs_B_KMeans.md` | `VERIFIED` (`6/6` celdas con salida) |
| **8.1** | `8.1_clustering_jerarquico.ipynb` (`2,487,322 bytes`) | CRISP-DM Fase 4 y 5 · Clustering Jerárquico Aglomerativo (`ward`, `k*=4`, muestreo en 3 niveles $n=60$, $n=3,000$ y expansión RAM $n=25,000$) | `14` totales / `7` código / `7` con `outputs` (`exec_count` `1..7`, corrida `RUN-20261120-073736`) | `scripts.ScriptsCsv.ClusteringJerarquico` (`config`, `sampling_and_features`, `hierarchical_engine`, `profiling_and_plots`, `markdown_writers`, `ram_expansion_and_comparison`) | `data/03_processed/` (**Versión B** como primaria y **Versión A** como sensibilidad), `reports/eda_jobpath/tables/split_map_resume_id.csv`, asignaciones de `8.0` | `8` figuras PNG en `reports/clustering_jerarquico_jobpath/figures/`, `13` tablas CSV en `reports/clustering_jerarquico_jobpath/tables/` (incluyendo `08_asignacion_clusters_personas_proyectada_352093.csv`), más `Bitacora_Clustering_Jerarquico.md`, `Comparacion_A_vs_B_Clustering_Jerarquico.md` y `Analisis_Comparativo_8_0_vs_8_1_Clustering.md` | `VERIFIED` (`7/7` celdas con salida) |

---

## 3. Inventario de Archivos de Datos en `data/` (Tamaños Exactos sin Cargar 20+ GB en Memoria)

Los archivos físicos de `data/` se encuentran en `c:\Users\User\Documents\JobPath\Version 2\MineriaProtect\data\` y suman **`25,910,401,168 bytes` (`24.13 GiB` / `25.91 GB`)**. Los conteos de columnas se verificaron leyendo únicamente la primera línea de cabecera de cada archivo CSV.

### 3.1 `data/01_raw/` — Fuentes Originales Inmutables (`124,897,596 bytes` = `119.11 MB`)

| Ruta Relativa | Tamaño (Bytes) | Tamaño (MB) | Filas Verificadas | Columnas | Cabecera / Esquema | Fuente de Verificación |
|---|---:|---:|---:|---:|---|---|
| `data/01_raw/JobHop_v2_train.csv` | `66,773,042` | `63.68 MB` | `1,594,827` | `5` | `resume_id,matched_code,start_date,end_date,university_level` | `unificar_raw_completo.py` L16 + conteo streaming CSV |
| `data/01_raw/JobHop_v2_test.csv` | `8,337,633` | `7.95 MB` | `198,877` | `5` | `resume_id,matched_code,start_date,end_date,university_level` | `README.md` L108 + conteo streaming CSV |
| `data/01_raw/JobHop_v2_val.csv` | `8,353,320` | `7.97 MB` | `199,587` | `5` | `resume_id,matched_code,start_date,end_date,university_level` | `README.md` L108 + conteo streaming CSV |
| `data/01_raw/ESCO/ISCOGroups_en.csv` | `975,006` | `0.93 MB` | `619` | `8` | `conceptType,conceptUri,code,preferredLabel,status,altLabels,inScheme,description` | Conteo streaming CSV |
| `data/01_raw/ESCO/occupations_en.csv` | `3,079,863` | `2.94 MB` | `3,043` | `15` | `conceptType,conceptUri,iscoGroup,preferredLabel,altLabels,hiddenLabels,status,modifiedDate,regulatedProfessionNote,scopeNote,definition,inScheme,description,code,localizedLabel` | Conteo streaming CSV |
| `data/01_raw/SKILLS/occupationSkillRelations_en.csv` | `27,986,628` | `26.69 MB` | `126,051` | `6` | `occupationUri,occupationLabel,relationType,skillType,skillUri,skillLabel` | Conteo streaming CSV |
| `data/01_raw/SKILLS/skills_en.csv` | `9,392,104` | `8.96 MB` | `13,960` | `13` | `conceptType,conceptUri,skillType,reuseLevel,preferredLabel,altLabels,hiddenLabels,status,modifiedDate,scopeNote,definition,inScheme,description` | Conteo streaming CSV |

### 3.2 `data/02_interim/` — Unificación Cruda e Intermedios Históricos (`1,788,577,193 bytes` = `1,705.72 MB`)

| Ruta Relativa | Tamaño (Bytes) | Tamaño (MB) | Filas Verificadas | Columnas | Rol en el Pipeline |
|---|---:|---:|---:|---:|---|
| `data/02_interim/Unificacion/empleos_unificado_completo.csv` | `1,505,545,254` | `1,435.80 MB` | `1,993,291` | `23` | **Vigente (Pipeline v2):** salida de `unificar_raw_completo.py` (unión cruda `train + test + val` con ESCO y SKILLS sin eliminar filas; `355,315` personas). |
| `data/02_interim/ESCO/greenShareOcc_en_limpio.csv` | `452,319` | `0.43 MB` | `3,590` | `5` | Auxiliar histórico (`limpiar_datos.py`). |
| `data/02_interim/ESCO/ISCOGroups_en_limpio.csv` | `974,377` | `0.93 MB` | `619` | `7` | Auxiliar histórico (`limpiar_datos.py`). |
| `data/02_interim/ESCO/occupations_en_limpio.csv` | `3,075,709` | `2.93 MB` | `3,039` | `15` | Auxiliar histórico (`limpiar_datos.py`). |
| `data/02_interim/SKILLS/occupationSkillRelations_en_limpio.csv` | `27,986,628` | `26.69 MB` | `126,051` | `6` | Auxiliar histórico (`limpiar_datos.py`). |
| `data/02_interim/SKILLS/skills_en_limpio.csv` | `9,373,339` | `8.94 MB` | `13,939` | `13` | Auxiliar histórico (`limpiar_datos.py`). |
| `data/02_interim/Jobhop/competencias_por_oficio.csv` | `2,035,340` | `1.94 MB` | `3,039` | `5` | Auxiliar histórico (`generar_competencias.py`). |
| `data/02_interim/Jobhop/JobHop_v2_train_limpio.csv` | `63,674,647` | `60.72 MB` | `1,506,445` | `5` | Auxiliar histórico (`limpiar_datos.py`). |
| `data/02_interim/Jobhop/JobHop_v2_test_limpio.csv` | `7,957,599` | `7.59 MB` | `188,061` | `5` | Auxiliar histórico (`limpiar_datos.py`). |
| `data/02_interim/Jobhop/JobHop_v2_val_limpio.csv` | `7,967,064` | `7.60 MB` | `188,506` | `5` | Auxiliar histórico (`limpiar_datos.py`). |
| `data/02_interim/Jobhop/empleos .csv` | `50,179,219` | `47.85 MB` | `376,567` | `17` | Histórico v1 (`test + val` integrado por `integrar_empleos.py`). |
| `data/02_interim/Jobhop/empleos_limpio.csv` | `57,423,894` | `54.76 MB` | `376,567` | `20` | Histórico v1 (`test + val` limpio por `limpiar_empleos.py`). |
| `data/02_interim/Jobhop/empleos_limpio_sin_outliers .csv` | `51,931,804` | `49.53 MB` | `341,090` | `20` | Histórico v1 (`test + val` con recorte de filas en `limpiar_empleos.py`). |

### 3.3 `data/03_processed/` — Datasets Maestros Limpios (`2,878,618,732 bytes` = `2,745.26 MB`)

| Ruta Relativa | Tamaño (Bytes) | Tamaño (MB) | Filas Verificadas | Personas Únicas | Columnas | Descripción y Huella SHA-256 |
|---|---:|---:|---:|---:|---:|---|
| `data/03_processed/empleos_unificado_limpio.csv` | `1,427,132,984` | `1,361.02 MB` | `1,871,014` | `355,308` | `23` | **Versión A (`con_outliers`):** salida maestra de `limpiar_unificado.py` y entrada de `2.0` a `8.1`. SHA-256 en `5.0`/`6.0`: `ae0cbc6ebd86bcf3...` (en `7.0`/`8.0`/`8.1`: `68cd34c624e8d23e...`). |
| `data/03_processed/empleos_limpio_con_competencias_sin_outliers.csv` | `1,451,482,826` | `1,384.24 MB` | `1,871,014` | `355,308` | `23` | **Versión B (`sin_outliers`, IQR `k=1.5`):** salida de `2.0_preprocesamiento_jobpath.ipynb` (`193,596` filas recortadas en 4 columnas de conteo). SHA-256 en `5.0`/`6.0`: `de8515e31565ca0b...` (en `7.0`/`8.0`/`8.1`: `c8ea36b51dea8803...`). |
| `data/03_processed/Limpio/bitacora_limpieza_unificado.csv` | `2,922` | `0.003 MB` | `8` | N/A | `10` | Bitácora de las 8 etapas de `limpiar_unificado.py` (`1,993,291 → 1,871,014` filas). |

### 3.4 `data/04_transformed/` — Matrices `X/y` y Transformadores Ajustados en `Train` (`21,118,307,647 bytes` = `20,140.00 MB` / `19.67 GiB`)

| Ruta Relativa | Tamaño (Bytes) | Tamaño (MB) | Filas Verificadas | Personas Únicas | Columnas | Huella SHA-256 (Celdas 74 de `5.0` y 18 de `6.0`) |
|---|---:|---:|---:|---:|---:|---|
| `data/04_transformed/con_outliers/train/X_train.csv` | `8,442,944,675` | `8,051.82 MB` | `1,391,018` | `281,674` | `2,985` | `84326e5737831b79...` |
| `data/04_transformed/con_outliers/train/y_train.csv` | `4,173,064` | `3.98 MB` | `1,391,018` | `281,674` | `1` (`reincide`) | `07d22441c00832e8...` |
| `data/04_transformed/con_outliers/test/X_test.csv` | `2,110,560,074` | `2,012.79 MB` | `347,720` | `70,419` | `2,985` | `785a51c74e626e9f...` |
| `data/04_transformed/con_outliers/test/y_test.csv` | `1,043,170` | `0.99 MB` | `347,720` | `70,419` | `1` (`reincide`) | `38f822d6ac471ec8...` |
| `data/04_transformed/sin_outliers/train/X_train.csv` | `8,443,453,087` | `8,052.30 MB` | `1,391,018` | `281,674` | `2,985` | `5bca3c92a9043c9b...` |
| `data/04_transformed/sin_outliers/train/y_train.csv` | `4,173,064` | `3.98 MB` | `1,391,018` | `281,674` | `1` (`reincide`) | `07d22441c00832e8...` (idéntico a Versión A) |
| `data/04_transformed/sin_outliers/test/X_test.csv` | `2,110,688,241` | `2,012.91 MB` | `347,720` | `70,419` | `2,985` | `318396b60d08afdd...` |
| `data/04_transformed/sin_outliers/test/y_test.csv` | `1,043,170` | `0.99 MB` | `347,720` | `70,419` | `1` (`reincide`) | `38f822d6ac471ec8...` (idéntico a Versión A) |
| `data/04_transformed/transformers/con_outliers/transformers.joblib` | `114,551` | `0.11 MB` | N/A | N/A | N/A | `b64f676458f3ef33...` |
| `data/04_transformed/transformers/sin_outliers/transformers.joblib` | `114,551` | `0.11 MB` | N/A | N/A | N/A | `d9c37b4c4b7364a8...` |

---

## 4. Inventario de Código Modular (`scripts/`, `src/`) y Reportes (`reports/`)

### 4.1 Scripts de Integración y Limpieza (`scripts/pipeline/limpieza/`)
- **Flujo unificado vigente (`v2`, `train + test + val`):**
  - `unificar_raw_completo.py` (`344` líneas): concatena las 3 particiones de JobHop v2 y las cruza `N:1` con ESCO v1.2.1 y SKILLS sin eliminar filas (`1,993,291 × 23`).
  - `limpiar_unificado.py` (`562` líneas): ejecuta las 8 etapas de Data Cleaning & Data Hygiene y exporta `empleos_unificado_limpio.csv` (`1,871,014 × 23`) y `bitacora_limpieza_unificado.csv`.
- **Flujo histórico (`v1`, solo `test + val`, conservado por trazabilidad):**
  - `limpiar_datos.py`, `integrar_empleos.py`, `limpiar_empleos.py`, `generar_competencias.py`, `unificar_competencias_empleos.py`.

### 4.2 Paquetes SOLID en `scripts/ScriptsCsv/` y `src/ScriptCsv/`
1. `scripts/ScriptsCsv/Preproccesing/` (`12` módulos `.py`): `config.py`, `utils.py`, `io.py`, `diagnosis.py`, `duplicates.py`, `categories.py`, `missing.py`, `imputation.py`, `outliers_iqr.py`, `funnel.py`, `validation.py`, `pipeline.py`.
2. `scripts/ScriptsCsv/Transformacion/` (`14` módulos `.py`): `config.py`, `column_profile.py`, `comparison.py`, `date_features.py`, `decision_log.py`, `discretization.py`, `encoding.py`, `export.py`, `pca_diagnostic.py`, `scaler_recommendation.py`, `scaling.py`, `split.py`, `validation.py`.
3. `scripts/ScriptsCsv/EDA/` (`16` módulos `.py`): `config.py`, `loader.py`, `profiling.py`, `descriptive.py`, `person_level.py`, `transitions.py`, `bivariate.py`, `pca_evidence.py`, `target.py`, `leakage.py`, `split_map.py`, `plots.py`, `validation.py`, `decision_log.py`, `pipeline.py`.
4. `scripts/ScriptsCsv/Modelado/` (`6` módulos `.py`): `config.py`, `dataset_builder.py`, `evaluation.py`, `plots.py`, `pipeline.py`.
5. `scripts/ScriptsCsv/ArbolDecision/` (`11` módulos `.py`) y `src/ScriptCsv/ArbolDecision/__init__.py` (re-exportador de compatibilidad): `config.py`, `data_loader.py`, `block_builders.py`, `leakage_guard.py`, `tuning.py`, `tree_inspector.py`, `sensitivity.py`, `plots.py`, `markdown_writers.py`, `pipeline.py`.
6. `scripts/ScriptsCsv/NaiveBayes/` (`13` módulos `.py`): `config.py`, `feature_blocks.py`, `models.py`, `bayes_by_counting.py`, `outlier_diagnostics.py`, `evaluation.py`, `occupation_analysis.py`, `patterns.py`, `version_comparison.py`, `plots.py`, `pipeline.py`, `self_tests.py`.
7. `scripts/ScriptsCsv/KNN/` (`15` módulos `.py`): `config.py`, `feature_blocks.py`, `models.py`, `geometry.py`, `version_comparison.py`, `pilot_benchmark.py`, `chunked_predictor.py`, `evaluation.py`, `neighbors_explainer.py`, `patterns.py`, `plots.py`, `pipeline.py`, `self_tests.py`, `revision_checks.py`.
8. `scripts/ScriptsCsv/KMeans/` (`6` módulos `.py`): `config.py`, `feature_builder.py`, `kmeans_engine.py`, `pca_and_plots.py`, `markdown_writers.py`.
9. `scripts/ScriptsCsv/ClusteringJerarquico/` (`7` módulos `.py`): `config.py`, `sampling_and_features.py`, `hierarchical_engine.py`, `profiling_and_plots.py`, `markdown_writers.py`, `ram_expansion_and_comparison.py`.

### 4.3 Artefactos Exportados en `reports/`
| Carpeta en `reports/` | Cuaderno Productor | Figuras PNG | Tablas CSV / Otros Artefactos |
|---|---|---:|---|
| `reports/eda_jobpath/` | `5.0_EDA_jobpath.ipynb` | `28` PNG (`g01`–`g30`, sin `g18` ni `g24`) | `2` CSV (`split_map_resume_id.csv` con `355,308` filas; `bitacora_decisiones_v1_vs_v2.csv` con `14` decisiones `D01`–`D14`) |
| `reports/modelado_jobpath/` | `6.0_modelado_fase4_jobpath.ipynb` | `4` PNG (`m01`–`m04`) | `5` CSV (`ablacion_fuga_colinealidad_cv.csv`, `resultados_cv_por_persona.csv`, `resultados_test_ab.csv`, `importancia_variables_sin_fuga.csv`, `bitacora_fase4_modelado.csv`) |
| `reports/arbol_decision_jobpath/` | `7.0_arbol_decision.ipynb` | `16` PNG vigentes (+ `9` en `archive/corrida_previa_v1`) | `77` CSV vigentes (+ `33` en `archive/`) + `13` archivos `.txt`/`.md` de reglas en `rules/` |
| `reports/naive_bayes_jobpath/` | `7.1_naive_bayes.ipynb` | `16` PNG (`nb01`–`nb16`) | `37` CSV (`01` a `12b` + `decision_log_naive_bayes.csv`) + `PROGRESS.md` |
| `reports/knn_jobpath/` | `7.2_knn.ipynb` | `13` PNG (`knn01`–`knn13`) | `48` CSV (`01a` a `13g` + `decision_log_knn.csv`) + caché de `70` bloques por modelo en `cache/` + `PROGRESS.md` |
| `reports/kmeans_jobpath/` | `8.0_kmeans_clustering.ipynb` | `7` PNG (`01`–`07`) | `9` CSV (`01` a `09`, incluyendo `08_asignacion_clusters_personas_352093.csv`) |
| `reports/clustering_jerarquico_jobpath/` | `8.1_clustering_jerarquico.ipynb` | `8` PNG (`01`–`08`) | `13` CSV (`01` a `13`, incluyendo `08_asignacion_clusters_personas_proyectada_352093.csv`) |

> **Nota adicional de inventario:** En la raíz del repositorio existe también la carpeta `numerical_methods_presentation/` (agregada en los commits `e9988b6` y `00e8a6b` del `2026-11-22`), correspondiente a una presentación unificada de Métodos Numéricos (MCO y Lagrange sobre 2 casos del dataset JobPath). No forma parte de la secuencia canónica de los 12 cuadernos de Minería de Datos, pero queda inventariada por completitud.

---

## 5. Contradicciones entre `README.md` / `1.0_comprension_negocio.md` y los Cuadernos (Regla #7)

Siguiendo la regla de veracidad (*"Do not trust the README over the notebooks (it may be outdated). Report any contradiction you find"*), se documentan las **7 contradicciones verificadas**:

1. **Estado del proyecto desactualizado en `README.md` (Fase 4 declarada "Pendiente" cuando `6.0` a `8.1` ya están ejecutados):**
   - **En `README.md` (líneas 11, 132–150, 177–184) y `docs/RefactorDocs/guia_ejecucion_notebooks_refactor.md` (líneas 24–45):** Se afirma que la Fase 4 CRISP-DM está *"⏳ Pendiente: Fase 4 CRISP-DM (Modelado / Minería de secuencias excluyendo de X las columnas con fuga directa del target)"* y el árbol de archivos solo llega hasta `5.0_EDA_jobpath.ipynb`.
   - **En los cuadernos ejecutados:** Existen **6 cuadernos adicionales totalmente ejecutados** (`6.0_modelado_fase4_jobpath.ipynb`, `7.0_arbol_decision.ipynb`, `7.1_naive_bayes.ipynb`, `7.2_knn.ipynb`, `8.0_kmeans_clustering.ipynb`, `8.1_clustering_jerarquico.ipynb`) con salidas verificadas en `reports/`.
2. **Contradicción de alcance entre `1.0_comprension_negocio.md` ("solo no supervisado, sin modelos predictivos") y `6.0`–`7.2` (clasificación supervisada de `reincide`):**
   - **En `notebooks/refactor/1.0_comprension_negocio.md` (líneas 18, 27, 35):** Se declara: *"Tarea de minería: Descubrimiento (no supervisada). No existe una columna objetivo que se quiera predecir; se busca estructura. Quedan descartadas tareas supervisadas (clasificación, regresión, predicción)"* y *"Fuera de alcance: construcción de modelos predictivos, producción en la nube"*.
   - **En `3.0` (celdas 3 y 9), `6.0`, `7.0`, `7.1` y `7.2`:** Se define el target binario supervisado `reincide = (veces_ese_oficio > 1)` y se entrenan clasificadores supervisados (Regresión Logística, HistGradientBoosting, CART, Naive Bayes y KNN). El propio cuaderno `7.0_arbol_decision.ipynb` (Decisión `DT-02` en `Bitacora_Arbol_Decision.md` L163) deja constancia: *"Recordatorio explícito: actualizar 1.0_comprension_negocio.md"*.
3. **Discrepancia en el conteo de `'No reportado'` en `university_level` (`205,238` vs. `215,600` en total limpio vs. `200,934` en universo clasificado):**
   - **En `README.md` (línea 189) y `reports/eda_jobpath/tables/bitacora_decisiones_v1_vs_v2.csv` (`D04`):** Se afirma que `'None'` en educación se normaliza a `'No reportado'` en **`205,238` filas (`10.97 %`)**.
   - **En `scripts/pipeline/limpieza/limpiar_unificado.py` (línea 89), `data/03_processed/Limpio/bitacora_limpieza_unificado.csv` (línea 8) y `3.0_transformacion.ipynb` (celda 6, `zero_pct = 11.523163 %` para `univ_ord` sobre `1,871,014` filas):** El conteo real en el dataset limpio completo (`1,871,014` filas) es **`215,600` filas (`11.523 %`)**. Y dentro del universo clasificado con oficio ESCO (`1,738,738` filas), los cuadernos `7.0` (celda 6), `8.0` (celda 4) y `8.1` (celda 4) verifican exactamente **`200,934` filas (`11.556 %`**: `160,664` en `Train` + `40,270` en `Test`). El número `205,238` del `README.md` no coincide con ninguna de las dos poblaciones del CSV final.
4. **Discrepancia en `dur_q` (duración en trimestres: `max=160, Q3=11` vs. `max=277, Q3=13` vs. `right_edge=225`):**
   - **En `data/03_processed/Limpio/bitacora_limpieza_unificado.csv` (línea 9):** Reporta `Q1=2.0, Q3=11.0, umbral Tukey=24.5 trim, max=160 trim`. Causa verificada en `limpiar_unificado.py` (líneas 432–434): allí `_extraer_anio_trimestre(df["end_date"])` devuelve `NaN` para los `95,136` empleos con `end_date == 'Present'`, por lo que `dur_q.dropna()` excluyó todos los empleos vigentes.
   - **En `README.md` (línea 188) y `5.0_EDA_jobpath.ipynb` (celda 17):** Al usar `add_date_ordinals` (`scripts/ScriptsCsv/Transformacion/date_features.py` L32–44), `'Present'` se censura a la derecha en `2026-Q1` (`ordinal = 8105`), dando sobre las `1,871,014` filas `Q1=2.0, mediana=5.0, Q3=13.0, IQR=11.0, umbral Tukey=29.5, max=277.0` trimestres.
   - **En `3.0_transformacion.ipynb` (celda 17 y 18):** Dentro del subconjunto con oficio ESCO clasificado (`1,738,738` filas), el máximo de `dur_q` (borde derecho del tercer bin de `KBinsDiscretizer`) es **`225.0` trimestres** (la experiencia de `277.0` trimestres pertenece a las `132,276` filas sin oficio ESCO clasificado).
5. **Discrepancia en `EXPECTED["filas_ok_salida"]` dentro de `limpiar_unificado.py`:**
   - **En `scripts/pipeline/limpieza/limpiar_unificado.py` (línea 92):** El diccionario `EXPECTED` declara `"filas_ok_salida": 1_747_826` (llave que nunca se evalúa en `validar_data_hygiene`).
   - **En todos los cuadernos (`2.0` celda 7, `3.0` celda 12, `5.0` celda 8, `7.0` celda 4, `8.0` celda 4, `8.1` celda 4):** El número real de filas con `saber_skills == 'ok'` (`occupation_code` no nulo) en `empleos_unificado_limpio.csv` es **`1,738,738` (`92.93 %`)**.
6. **Diferencia en el conteo de personas con educación no reportada en `8.1_clustering_jerarquico.ipynb` (`42,884` vs. `44,568` en la misma fila de tabla):**
   - **En `8.1_clustering_jerarquico.ipynb` (celda 4, fila 8 de la tabla `Uso de datos`) y `Bitacora_Clustering_Jerarquico.md` (línea 39):** La columna `personas_unicas` dice `42884` (personas cuya **primera experiencia** tiene educación no reportada, consistente con `8.0_kmeans_clustering.ipynb` celda 4), pero el texto de `detalle_y_justificacion` de esa misma fila dice `44,568 personas` (personas con **al menos una experiencia** sin educación reportada).
7. **Referencia huérfana a `METODOLOGIA_KDD_CRISPDM.md` en `1.0_comprension_negocio.md` y huellas SHA-256 de CSV entre máquinas:**
   - `1.0_comprension_negocio.md` (línea 77) cita `METODOLOGIA_KDD_CRISPDM.md`, archivo eliminado del repositorio en el commit `43f079a` (`2026-09-14`).
   - Los cuadernos `5.0` y `6.0` (ejecutados en `C:\Users\User\Documents\JobPath\MineriaProtect`) reportan para `empleos_unificado_limpio.csv` y `empleos_limpio_con_competencias_sin_outliers.csv` los hashes `ae0cbc6ebd86bcf3...` y `de8515e31565ca0b...`, mientras que `7.0`, `8.0` y `8.1` (ejecutados en `C:\Users\monoc\Desktop\mineria\MineriaProtect`) reportan `68cd34c624e8d23e...` y `c8ea36b51dea8803...` (variación de saltos de línea `CRLF`/`LF` al escribir CSV en distintas máquinas; el contenido tabular y los hashes de `y_train.csv` `07d22441c00832e8...`, `y_test.csv` `38f822d6ac471ec8...` y `split_map_resume_id.csv` `67dd3e3d68e1ff5e...` son `100 %` idénticos).

---

## 6. Gobernanza de Datos: Licencias (JobHop v2 / ESCO v1.2.1) y Riesgos de Privacidad / Re-identificación

### 6.1 Términos de Licencia de las Fuentes
1. **ESCO v1.2.1 (European Skills, Competences, Qualifications and Occupations — Comisión Europea):**
   - Publicado por la Comisión Europea bajo la política de reutilización de documentos de la Comisión (**Decision 2011/833/EU**, licencia abierta equivalente a **CC BY 4.0**).
   - **Obligación para el dashboard en Vercel y las diapositivas en Reveal.js:** Incluir atribución visible a la Comisión Europea (`"Fuente taxonómica: ESCO v1.2.1 — Comisión Europea"`) y aclarar que los perfiles de competencias corresponden a **requisitos estandarizados del oficio en ESCO**, no a certificaciones individuales del trabajador (`README.md` L92–95).
2. **JobHop v2 (`aida-ugent/JobHop`, Ghent University / VDAB, Flandes, Bélgica):**
   - Dataset académico publicado en Hugging Face (`https://huggingface.co/datasets/aida-ugent/JobHop`) derivado de currículums anonimizados/estructurados en Flandes.
   - **Estado en el repositorio local:** El repositorio `MineriaProtect` no incluye un archivo `LICENSE` propio ni copia del texto legal de `aida-ugent/JobHop` (**`NOT VERIFIED` localmente en disco**; debe citarse el dataset académico original de la Universidad de Gante en el dashboard y en la presentación, y utilizarse estrictamente con fines académicos/demostrativos sin redistribuir el volcado crudo completo).

### 6.2 Riesgo de Privacidad y Re-identificación de `resume_id`
- **Qué contiene `01_raw` y `03_processed`:** No existen identificadores personales directos (no hay nombres, apellidos, correos electrónicos, teléfonos, direcciones, nombres de empresas empleadoras ni números de documento). Cada persona está representada por `resume_id` (entero en el rango `[0, 444,480]`, con `355,308` valores únicos en `03_processed` y `352,093` en el universo clasificado).
- **Por qué `resume_id` es seudónimo pero NO inmune a re-identificación indirecta:**
  - Una trayectoria laboral longitudinal de `5` a `20` empleos con fechas trimestrales exactas (`start_date`, `end_date`), códigos finos de ocupación ESCO (`2,973` oficios distintos) y nivel educativo (`university_level`, incluyendo grupos pequeños como `PhD` con `5,974` filas en Train y `1,556` en Test) actúa como una combinación de **cuasi-identificadores de alta unicidad**. Si un tercero cruza una secuencia trimestral completa con perfiles públicos de LinkedIn en Flandes, podría re-identificar a un individuo.
  - Además, conservar el entero original `resume_id` permitiría cruzar directamente cualquier registro expuesto en el dashboard con el dataset público `aida-ugent/JobHop`.
- **Reglas obligatorias de gobernanza para la Fase 2 (Neon) y Fase 3 (Vercel):**
  1. **Hash o clave sustituta para personas:** Antes de cargar la muestra de personas en Neon, reemplazar `resume_id` por un identificador opaco derivado con sal secreta (`person_uid = SUBSTR(ENCODE(HMAC(resume_id::text, SECRET_SALT, 'sha256'), 'hex'), 1, 12)`) o un entero secuencial de muestra (`sample_person_id = 1..N`) sin publicar la tabla de correspondencia con `resume_id`.
  2. **Priorizar agregados y perfiles de clúster/transición en vistas públicas:** Si el dashboard muestra ejemplos de trayectorias individuales, limitar la resolución o mostrar ejemplos sintéticos/agregados o con `person_uid` hasheado, respetando la regla aplicada en `2.0_preprocesamiento_jobpath.ipynb` (celda 8: *"sin exponer trayectorias individuales"*).

---

## 7. Inventario de Herramientas MCP Disponibles en el Entorno (Regla de Trabajo #1)

En cumplimiento de la regla *"Before using Neon or Vercel MCP tools, list the tools you actually have available"*, se documentan los servidores y herramientas MCP disponibles en la sesión (ninguna ha sido invocada en esta Fase 1 de solo lectura):

- **Servidor MCP `Neon` (`115` herramientas lazy disponibles):**
  - *Exploración y proyectos:* `list_organizations`, `list_projects`, `count_projects`, `describe_project`, `create_project`, `update_project`, `delete_project`, `recover_project`, `list_project_permissions`, `list_project_members`, `list_regions`, `list_operations`, `get_operation`, `get_project_consumption`.
  - *Ramas y cómputo:* `list_branches`, `get_branch`, `describe_branch`, `create_branch`, `update_branch`, `delete_branch`, `get_default_branch`, `set_default_branch`, `reset_from_parent`, `compare_database_schema`, `finalize_branch_restore`, `get_branch_consumption`, `list_postgres_endpoints`, `list_branch_computes`, `get_postgres_endpoint`, `create_postgres_endpoint`, `update_postgres_endpoint`, `delete_postgres_endpoint`, `start_postgres_endpoint`, `suspend_postgres_endpoint`, `restart_postgres_endpoint`.
  - *SQL, esquema y migraciones:* `run_sql`, `run_sql_transaction`, `describe_table_schema`, `get_database_tables`, `prepare_database_migration`, `complete_database_migration`, `explain_sql_statement`, `prepare_query_tuning`, `complete_query_tuning`, `list_slow_queries`, `inspect_database`, `get_connection_string`, `list_postgres_roles`, `get_postgres_role`, `create_postgres_role`, `delete_postgres_role`, `reset_postgres_role_password`, `list_postgres_databases`, `get_postgres_database`, `create_postgres_database`, `update_postgres_database`, `delete_postgres_database`.
  - *Snapshots, Auth, Data API, Storage y Docs:* `list_snapshots`, `get_snapshot_schedule`, `set_snapshot_schedule`, `create_snapshot`, `update_snapshot`, `delete_snapshot`, `restore_snapshot`, `get_auth`, `provision_neon_auth`, `disable_auth`, `get_data_api`, `provision_neon_data_api`, `get_storage`, `list_storage_buckets`, `search`, `fetch`, `search_docs`, `get_doc`.
- **Servidor MCP `vercel-plugin_vercel` (`205` herramientas lazy disponibles):**
  - *Proyectos y despliegues:* `list_projects`, `get_project`, `create_project`, `create_git_project`, `update_project`, `list_deployments`, `get_deployment`, `create_deployment`, `cancel_deployment`, `open_deployments`, `get_git_deployment_context`, `list_deployment_files`, `get_deployment_file_contents`, `list_deployment_events`, `list_deployment_aliases`, `assign_alias`, `list_aliases`, `get_alias`, `request_promote`, `request_rollback`.
  - *Variables de entorno, dominios y rutas:* `get_project_env`, `filter_project_envs`, `create_project_env`, `edit_project_env`, `get_shared_env_var`, `list_project_domains`, `get_project_domain`, `add_project_domain`, `verify_project_domain`, `list_domains`, `get_domain`, `list_project_routes`, `add_route`, `edit_route`, `stage_routes`, `update_route_versions`.
  - *Observabilidad, logs y documentación:* `get_runtime_logs`, `get_runtime_errors`, `get_project_trace`, `create_observability_query`, `get_observability_schema`, `search_vercel_documentation`, `get_access_to_vercel_url`, `web_fetch_vercel_url`, `list_teams`, `get_team`, `get_auth_user`.
- **Servidor MCP `GitKraken` (`33` herramientas lazy disponibles):**
  - `git_status`, `git_log_or_diff`, `git_branch`, `git_blame`, `git_graph`, `git_add`, `git_commit`, `git_checkout`, `git_push`, `git_pull`, `git_fetch`, `git_stash`, `git_worktree`, etc.


---

## [v1.1 — Addendum: Comparación de Clones Locales, Subcarpetas de `reports/`, Auditoría de `numerical_methods_presentation/` y Política de Identificadores]

> **Nota de Versionado (`v1.1`):** Esta sección amplía de forma aditiva el inventario de la Fase 1 sin sobrescribir el contenido aprobado en `v1.0` ni mover, enlazar o eliminar archivos en ninguno de los dos clones locales.

### 8. Comparación Auditada de los Dos Clones Locales

| Atributo Verificado | Clon 1 (Canónico): `c:\Users\User\Documents\JobPath\MineriaProtect` | Clon 2 (Respaldo de Datos): `c:\Users\User\Documents\JobPath\Version 2\MineriaProtect` |
|---|---|---|
| **Último Commit (`HEAD`)** | `00e8a6bcda1ae09b10a136d61fc9a115530ad076` | `263c8695657f4cdead59a2add153919b770cd40f` (**6 commits atrás** de Clon 1) |
| **Fecha y Autor del `HEAD`** | `2026-11-22 13:55:14 -0500` · `J3ST <128815315+NostruJ@users.noreply.github.com>` (`"Add files via upload"`) | `2026-11-20 08:22:09 -0500` · `Hollowlightmouse <johanstevenlopezordonez1102@gmail.com>` (`"Models"`) |
| **Commits Presentes Solo en Clon 1** | `9200bbb` (`8.0` y `8.1` clustering), `75e1ed3` (PR `#11`), `26c565e` (PR `#12`), `e9988b6` y `00e8a6b` (`numerical_methods_presentation/`) | Ninguno (es ancestro directo de Clon 1) |
| **Cambios Sin Confirmar (`git status -s`)** | Únicamente `?? docs/handoff/` (`0` archivos rastreados modificados) | Vacío (`0` cambios sin confirmar) |
| **Cuadernos en `notebooks/refactor/`** | Completo (`1.0` + 11 cuadernos `.ipynb` de `2.0` a `8.1`, todos con salidas guardadas) | Incompleto (solo hasta `7.2_knn.ipynb`; carece de `8.0` y `8.1`) |
| **Carpeta Física `data/` (`24.13 GiB`)** | No presente físicamente (ignorada en `.gitignore` L162) | **Presente físicamente (`25,910,401,168 bytes` = `24.13 GiB`)** |

---

### 9. Inventario Detallado de las 7 Subcarpetas de `reports/` (Clon Canónico)

| Subcarpeta en `reports/` | Cuaderno Generador | Contenido Verificado | Archivos Clave con Columnas de Persona / Estrato / Métricas |
|---|---|---|---|
| `reports/eda_jobpath/` | `3.0` y `5.0_EDA_jobpath.ipynb` | `28` figuras PNG (`figures/g01..g30`) + `2` tablas CSV (`tables/`) | `tables/split_map_resume_id.csv` (`355,308` filas: `resume_id, split`); `tables/bitacora_decisiones_v1_vs_v2.csv` (`14` decisiones `D01`–`D14`). |
| `reports/modelado_jobpath/` | `6.0_modelado_fase4_jobpath.ipynb` | `5` figuras PNG + `5` tablas CSV | `tables/ablacion_fuga_colinealidad_cv.csv`; `tables/resultados_test_ab.csv` (Baseline, Logística OHE `ROC-AUC = 0.7133`, HistGB); `tables/top_coeficientes_logistica.csv`; `tables/bitacora_fase4_modelado.csv`. |
| `reports/arbol_decision_jobpath/` | `7.0_arbol_decision.ipynb` | `14` figuras PNG vigentes + `47` tablas CSV vigentes + `13` archivos de reglas en `rules/` (+ carpeta histórica `archive/corrida_previa_v1/`) | `tables/05b_tres_referencias_obligatorias.csv`; `tables/07_comparacion_tres_arboles_referencias_y_versiones.csv`; `tables/16_auditoria_identidad_aditiva_skills_a_vs_b.csv`; `tables/20_arbol3_sin_ocupacion_3343_1_comparacion.csv`; `tables/21_cv_agrupado_por_ocupacion_vs_persona.csv`. |
| `reports/naive_bayes_jobpath/` | `7.1_naive_bayes.ipynb` | `16` figuras PNG (`nb01..nb15`) + `37` tablas CSV | `tables/01_bayes_manual_comparacion.csv`; `tables/08a_resultados_test_version_a_ic95_bootstrap.csv` (`NB-G`, `NB-B`, `NB-H`); `tables/10_o1_tasas_reincidencia_isco_1d.csv`; `tables/10_p7_ablacion_bloques_comportamiento.csv`; `tables/decision_log_naive_bayes.csv`. |
| `reports/knn_jobpath/` | `7.2_knn.ipynb` | `13` figuras PNG (`knn01..knn13`) + `48` tablas CSV + `210` checkpoints `.npz` en `cache/` (`70` bloques $\times$ `3` modelos en `Test`) | `tables/01_auditoria_escala_variables_knn.csv`; `tables/04_pureza_geometrica_vecinos_k51.csv`; `tables/09a_resultados_test_version_a_ic95_bootstrap.csv` (`KNN-D`, `KNN-G`, `KNN-W`); `tables/13g_comparacion_unificada_version_a.csv`; `tables/decision_log_knn.csv`. |
| `reports/kmeans_jobpath/` | `8.0_kmeans_clustering.ipynb` | `7` figuras PNG (`01..07`) + `9` tablas CSV | **`tables/08_asignacion_clusters_personas_352093.csv`** (`59,110,791 bytes`, las `352,093` personas clasificadas con `resume_id, split, cluster, nombre_segmento`, las `9` variables de `V_PERSON`, `any_repeated_posthoc, tasa_reincide_persona_posthoc, isco_major_modal_posthoc`); `tables/04_centroides_personas_escala_original_y_estandarizada.csv`; `tables/06_perfiles_completos_y_validacion_posthoc_reincide.csv`. |
| `reports/clustering_jerarquico_jobpath/` | `8.1_clustering_jerarquico.ipynb` | `8` figuras PNG (`01..08`) + `13` tablas CSV | **`tables/08_asignacion_clusters_personas_completo_nearest_centroid.csv`** (`32,819,142 bytes`, las `352,093` personas proyectadas desde Ward $n=3,000$); `tables/07_asignacion_clusters_muestra_descubrimiento.csv` (`3,000` personas Train); `tables/10_factibilidad_hardware_ram_o_n2.csv`; `tables/11_comparacion_muestra_3000_vs_25000_ward.csv`; `tables/12_perfiles_ward_n25000_escala_original.csv`; `tables/13_matriz_ejecutiva_comparativa_8_0_vs_8_1.csv`. |

---

### 10. Inventario y Auditoría de `numerical_methods_presentation/` (Commits `e9988b6` y `00e8a6b`)

Carpeta autocontenida (`45` archivos, `1,259,908 bytes` = `1.20 MiB`) que aplica **Regresión Lineal por Mínimos Cuadrados (MCO)** e **Interpolación Polinomial de Lagrange** a la duración de empleos cerrados (`~es_vigente`) de JobPath:

| Ruta Relativa en `numerical_methods_presentation/` | Tamaño (Bytes) | Rol y Estado de Verificación Independiente |
|---|---:|---|
| `index.html` | `120,581` | Presentación HTML unificada (`16` diapositivas, 100 % offline con KaTeX local y 2 simuladores SVG en vivo para `IDEA-RL-04` e `IDEA-LG-01`). |
| `README.md` | `2,300` | Guía de uso local y atajos de teclado de la presentación de métodos numéricos. |
| `EVALUACION_PRESENTACION_UNIFICADA.md` | `9,226` | **ADVERTENCIA DE AUDITORÍA (`SELF-ASSESSMENT`):** Documento de autoevaluación interna (`100/100 · Nota 5.0/5.0`). **No constituye evidencia independiente**; cada cifra matemática de las diapositivas fue verificada por reproducción directa desde `data/03_processed/empleos_unificado_limpio.csv` (`F-048` y `F-049` en `FACTS.md`). |
| `assets/katex/*` (`23` archivos) | `548,569` | Paquete offline **KaTeX 0.16.11** (`katex.min.css`, `katex.min.js`, `auto-render.min.js` + `20` fuentes `.woff2`). |
| `case_01_RL04_annual_drift_extrapolation/presentacion_IDEA_RL_04.html` | `42,496` | Presentación individual del Caso 1 MCO (`8` diapositivas). |
| `case_01_RL04_annual_drift_extrapolation/EXPLICACION_IDEA_RL_04.md` y `GUIA_FACIL_IDEA_RL_04.md` | `19,751` | Documentación técnica y pedagógica de `IDEA-RL-04`. **Contradicción detectada:** cita los scripts `scripts/ScriptsCsv/MetodosNumericos/{loaders.py,experiments_ols.py,pipeline.py}` y `tests/metodos_numericos/`, que **no existen en el repositorio Git** (`NOT VERIFIED` en el árbol de código). |
| `case_01_RL04_annual_drift_extrapolation/tables/rl04_annual_macro_series.csv` | `3,195` | `24` filas (`start_year` `2000..2023`): volumen `n_starts`, cerrados `n_closed_starts`, `mean_skills`, `mean_dur_q` (`~es_vigente`), `mean_green`, `reincide_rate`. **`VERIFIED` por reproducción directa desde `03_processed`**. |
| `case_01_RL04_annual_drift_extrapolation/tables/rl04_ols_regime_comparison.csv` | `6,563` | `15` modelos MCO (`2000–2019` sin centrar, `2000–2023` con cola censurada, y `t - 2000` centrado en `2000–2019`). **`VERIFIED` con diferencia máxima `$5.73 \times 10^{-8}$`**. |
| `case_01_RL04_annual_drift_extrapolation/tables/rl04_extrapolation_failure_audit.csv` | `1,143` | `18` filas de extrapolación `2020..2027` (`mean_dur_q` predice valores negativos desde `2021` con `-0.2029` hasta `-4.9585` trimestres en `2027`). **`VERIFIED`**. |
| `case_01_RL04_annual_drift_extrapolation/tables/rl04_raw_partition_parity.csv` | `390` | `3` filas auditando la paridad temporal `2000–2019` en `JobHop_v2_{train,test,val}.csv`. **`VERIFIED`**. |
| `case_01_RL04_annual_drift_extrapolation/figures/nm05_rl04_annual_drift_and_censoring_extrapolation.png` y `geogebra/*.txt` | `152,570` | Figura comparativa a 150 DPI y script reproducible para GeoGebra Classic. |
| `case_02_LG01_survival_and_runge/presentacion_IDEA_LG_01.html` | `42,606` | Presentación individual del Caso 2 Lagrange (`8` diapositivas). |
| `case_02_LG01_survival_and_runge/EXPLICACION_IDEA_LG_01.md` y `GUIA_FACIL_IDEA_LG_01.md` | `18,711` | Documentación de `IDEA-LG-01`. Cita `scripts/ScriptsCsv/MetodosNumericos/{lagrange.py,experiments_lagrange.py}` (ausentes del árbol Git). |
| `case_02_LG01_survival_and_runge/tables/lg01_survival_curve_S_q.csv` | `1,461` | `40` filas (`quarter_q` `1..40`) de la curva empírica $S(q) = P(\text{dur\_q} \ge q)$ sobre los `1,643,772` empleos cerrados clasificados (`saber_skills == 'ok' & ~es_vigente`). **`VERIFIED` al `100 %` desde `03_processed`**. |
| `case_02_LG01_survival_and_runge/tables/lg01_milestone_P3_weights_and_eval.csv` y `lg_monomial_expansions.csv` | `1,785` | Evaluación en `7` trimestres (`q ∈ {2, 6, 12, 16, 28, 36, 48}`) y coeficientes monomiales de $P_3(q)$ sobre los hitos `q = {4, 8, 20, 40}`. **`VERIFIED` al `100 %`**. |
| `case_02_LG01_survival_and_runge/tables/lg01_runge_phenomenon_benchmark.csv` | `1,948` | `15` filas (`degree ∈ {3, 5, 8, 12, 16}` $\times$ `3` estrategias: Global Equiespaciado, Chebyshev-Lobatto y Local Cuadrático $P_2$). **`VERIFIED`**. |
| `case_02_LG01_survival_and_runge/figures/*.png` (`2` figuras) y `geogebra/*.txt` | `361,888` | Figuras de $P_3(q)$ y del Fenómeno de Runge a 150 DPI + comandos para GeoGebra Classic. |

---

### 11. Actualización de Gobernanza sobre `resume_id` y Archivos de Handoff (`v1.1`)

1. **Política definitiva sobre `resume_id` (Instrucción del Usuario):** Se conserva `resume_id` tal como viene en el dataset público JobHop v2 (**sin** crear `person_uid` y **sin** aplicar hash). En la página de **Metodología (`Methods`)** del dashboard en Vercel se incluirá de forma visible la declaración de que `resume_id` proviene directamente del dataset público anonimizado **JobHop v2** (`VDAB / Ghent University`, licencia **CC BY 4.0**) enriquecido con **ESCO v1.2.1** (Comisión Europea, licencia **CC BY 4.0**).
2. **Estado de [1.0_comprension_negocio.md](file:///c:/Users/User/Documents/JobPath/MineriaProtect/notebooks/refactor/1.0_comprension_negocio.md):** Se registra formalmente que `1.0_comprension_negocio.md` está desactualizado respecto a la incorporación de los modelos supervisados (`6.0`, `7.0`, `7.1`, `7.2`) y el despliegue web, pero **no se edita** dicho archivo.
3. **Documento adicional producido en `/docs/handoff/`:** [SAMPLING_OPTIONS.md](file:///c:/Users/User/Documents/JobPath/MineriaProtect/docs/handoff/SAMPLING_OPTIONS.md) (evaluación comparativa de los Candidatos A, B y C para Neon).
