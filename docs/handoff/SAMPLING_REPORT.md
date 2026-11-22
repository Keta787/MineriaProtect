# SAMPLING_REPORT.md · Reporte Final de Diseño Censal, Inclusión/Exclusión y Verificación Go/No-Go en Neon (`JobPath` · Fase 1)

---

## 1. Veredicto Ejecutivo y Cifras Clave (`RESULTS FOCUS`)

- **Veredicto de la Puerta Go / No-Go en Neon (`steep-poetry-63912763`, PostgreSQL 18):** **`GO (APROBADO)`**
- **Candidato Construido y Verificado:** **Candidato C — Censo Clasificado Completo (`352,093` personas / `1,738,738` experiencias + Catálogo ESCO normalizado de `2,973` oficios + `12` tablas agregadas `agg_*`)**, reproducible mediante un solo script (`src/sampling/build_and_verify_census.py`, semilla fija `SEED = 42`, leyendo `DATA_DIR` desde `.env.local` en modo solo lectura).
- **Cobertura sobre la Población:**
  - **Sobre el universo modelable con oficio ESCO clasificado (`352,093` personas / `1,738,738` experiencias):** **`100.0000 %` de las personas** y **`100.0000 %` de las experiencias** (`sampling_weight = 1.0` uniforme).
  - **Sobre el dataset maestro limpio completo (`355,308` personas / `1,871,014` experiencias en `03_processed`):** **`99.0952 %` de las personas** y **`92.9302 %` de las experiencias** (las restantes `132,276` experiencias = `7.0698 %` y `3,215` personas exclusivas = `0.9048 %` carecen de oficio hoja en ESCO y se documentan explícitamente en la tabla `agg_inclusion_exclusion_funnel`).
- **Mayor Desviación por Estrato frente al Universo Modelable:** **`0.0000 puntos porcentuales (`±0.0000 pp`)** en todos los estratos (`university_level`, `isco_major_1d_zfill`, `isco_major_modal_posthoc`, `n_jobs_bin`, `cluster_kmeans_8_0`, `cluster_ward_3k_projected`, `cluster_ward_25k_projected`, `split` y `educacion_no_reportada`).
  - Distancia de Variación Total (`TVD`): **`0.0000 pp`** en todas las dimensiones.
  - Estadístico de Kolmogorov–Smirnov en longitud de trayectoria (`n_jobs`): **`D_KS = 0.000000`** ($p = 1.0000$).
  - Cobertura de transiciones ocupacionales (`1,386,645` transiciones en `373,311` pares únicos y `2,973` oficios ESCO): **`100.00 %` en `Top-50`, `Top-100` y cola larga (`0 %` de patrones raros perdidos; correlación de rangos de Spearman $\rho = 1.0000$)**.
- **Huella Física Real Medida en Neon (`pg_total_relation_size` incluyendo índices B-tree tras `VACUUM ANALYZE`):**
  - **Suma de las 15 tablas de usuario + todos los índices:** **`281,477,120 bytes` (`268.44 MiB` / `281.48 MB`)** — **`55.26 %` por debajo del tope Go/No-Go de `600 MiB`**.
  - **Tamaño total de la base `pg_database_size('neondb')` (incluyendo catálogos del sistema):** **`289,701,888 bytes` (`276.28 MiB` / `289.70 MB`)** — apenas el **`26.98 %` del límite gratuito de `1,024 MiB` (`1 GiB`) de Neon**.
- **Latencias Reales Medidas en Neon (`aws-us-east-1`):**
  - **Arranque en frío (*Cold Start* conexión TLS + `SELECT 1`):** **`1,616.69 ms`** (objetivo `<= 2,500 ms`: **APROBADO**).
  - **Consultas titulares sobre las 12 tablas pre-agregadas (`Q1`–`Q4`):** **`0.028 ms` a `0.049 ms`** de ejecución en el motor PostgreSQL (`73.50 ms` a `83.13 ms` RTT cliente-servidor; objetivo `<= 15 ms` motor / `<= 120 ms` RTT: **APROBADO**).
  - **Consultas interactivas indexadas del explorador de trayectorias (`Q5`–`Q7`, `LIMIT 50` y `JOIN` con catálogo ESCO):** **`0.064 ms` a `0.433 ms`** de ejecución en el motor PostgreSQL vía *Index Scan* B-tree (`74.42 ms` a `80.09 ms` RTT; objetivo `<= 25 ms` motor / `<= 150 ms` RTT: **APROBADO**).

---

## 2. Párrafo Listo para Diapositiva (Reveal.js) y Vista de Transparencia de Inclusión/Exclusión del Dashboard

> **Transparencia de Datos: Censo Clasificado, Criterios de Exclusión y Límites de Muestreo**  
> En lugar de depender de una submuestra con error de estimación, nuestra base de datos en la nube (Neon PostgreSQL) aloja el **`100 %` del universo modelable clasificado (`352,093` personas y `1,738,738` experiencias laborales en `268.4 MiB`, con error muestral `±0.00 pp` y `0 %` de pérdida en las `373,311` rutas únicas de transición ocupacional)**. Del dataset limpio total (`1,871,014` experiencias en `355,308` personas), se excluyeron de forma transparente **`132,276` experiencias (`7.07 %`: `128,981` sin oficio identificado y `3,295` sin oficio hoja en ESCO; `3,215` personas exclusivas = `0.90 %`)** para no inventar competencias inexistentes con ceros falsos. Toda la población incluida preserva la partición estricta por persona **`80 % Train` (`281,674` personas) / `20 % Test` (`70,419` personas) con `0` personas compartidas**, garantizando que las métricas del dashboard jamás mezclen entrenamiento y prueba; asimismo, mientras **K-Means++ (`8.0`)** segmenta directamente a las `352,093` personas, el enlace jerárquico directo de **Ward (`8.1`)** se identifica explícitamente sólo sobre su **muestra estratificada de `25,000` personas de `Train` (`7.10 %`, `cluster_ward_25k_direct`)**, dado que calcular la matriz completa de distancias $O(n^2)$ exigiría `495.9 GB` de memoria RAM.

---

## 3. Embudo Exacto de Inclusión/Exclusión y Auditoría de Partición y Clústeres en PostgreSQL

### 3.1 Tabla `agg_inclusion_exclusion_funnel` (Cargada y Verificada en Neon)

| Orden | Código de Etapa | Descripción en Español | Estado en Neon | Experiencias | Personas | `%` Exp. Limpias | `%` Personas Limpias | Justificación Técnica y de Negocio |
|---:|---|---|---|---:|---:|---:|---:|---|
| `1` | `raw_jobhop_v2` | 1. Universo crudo JobHop v2 (`train + test + val`) | `UPSTREAM_RAW` | `1,993,291` | `355,315` | `106.5353 %` | `100.0020 %` | Unión íntegra de las 3 particiones crudas de Hugging Face (`0` personas solapadas). |
| `2` | `removed_in_cleaning_stages_1_to_5` | 2. Removidos en limpieza física (sin fechas, año `> 2026`, duplicados y variantes de cierre) | `EXCLUDED_CLEANING` | `122,277` | `7` | `6.5353 %` | `0.0020 %` | `72,726` sin fechas + `11` con año `> 2026` + `37,553` duplicados exactos + `11,987` variantes parciales de cierre (`limpiar_unificado.py`). |
| `3` | `clean_master_dataset` | 3. Dataset maestro limpio (`03_processed` Versiones A y B) | `CLEAN_REFERENCE` | `1,871,014` | `355,308` | `100.0000 %` | `100.0000 %` | Base limpia tras deduplicación, rescate jerárquico de `9,293` filas y winsorización IQR sin borrar filas (`2.0`). |
| `4` | `excluded_esco_unknown` | 4a. Excluidos del censo modelable: ocupación no identificada (`emparejado = 'unknown'`) | `EXCLUDED_NO_ESCO` | `128,981` | `3,132` | `6.8936 %` | `0.8815 %` | Sin código ESCO ni grupo ISCO; imposible asignar competencias sin inventar ceros espurios (Decisiones `D05`/`D07`). |
| `5` | `excluded_esco_rescatado_no_leaf` | 4b. Excluidos del censo modelable: solo grupo ISCO de 4 dígitos sin oficio hoja ESCO (`'rescatado'`) | `EXCLUDED_NO_ESCO` | `3,295` | `83` | `0.1761 %` | `0.0234 %` | Tienen grupo ISCO pero carecen de oficio hoja en `occupations_en.csv` y de perfil de competencias. |
| `6` | `included_classified_census_total` | **5. CENSO CLASIFICADO INCLUIDO EN NEON (Candidato C · `100 %` del universo modelable)** | **`INCLUDED_CENSUS`** | **`1,738,738`** | **`352,093`** | **`92.9302 %`** | **`99.0952 %`** | Universo completo con oficio ESCO válido (`±0.0000 pp` error muestral, `100 %` de transiciones preservadas). |
| `7` | `census_split_train` | 6a. Partición `Train` en Neon (`80.00 %` de personas clasificadas · `GroupShuffleSplit seed=42`) | `INCLUDED_TRAIN` | `1,391,018` | `281,674` | `74.3457 %` | `79.2760 %` | Ajuste de escaladores, OHE, clasificadores (`6.0`–`7.2`) y centroides K-Means (`8.0`). `0` personas compartidas con `Test`. |
| `8` | `census_split_test` | 6b. Partición `Test` en Neon (`20.00 %` de personas clasificadas · Retenida *out-of-sample*) | `INCLUDED_TEST` | `347,720` | `70,419` | `18.5846 %` | `19.8191 %` | Evaluación final sin fuga de todos los modelos supervisados y validación post-hoc de clústeres. |
| `9` | `ward_25k_direct_subsample` | 7a. Submuestra directa Ward Jerárquico (`in_ward_25k_sample = TRUE` · `cluster_ward_25k_direct IS NOT NULL`) | `WARD_DIRECT_ONLY` | `123,600` | `25,000` | `6.6060 %` | `7.0361 %` | Muestra estratificada de `Train` (`7.1004 %` del censo) donde se ajustó directamente el dendrograma Ward (`2.50 GB` RAM). |
| `10` | `outside_ward_25k_subsample` | 7b. Personas fuera de la muestra directa Ward (`in_ward_25k_sample = FALSE` · `cluster_ward_25k_direct IS NULL`) | `WARD_NULL_DIRECT` | `1,615,138` | `327,093` | `86.3242 %` | `92.0590 %` | `327,093` personas (`92.8996 %` del censo) donde Ward no se ajustó directamente por límite $O(n^2)$ de `495.9 GB` RAM. |

### 3.2 Verificación SQL en Neon de la Restricción de Clústeres Ward (`25k`) y Partición `Train`/`Test`

Resultado exacto devuelto por PostgreSQL 18 en `steep-poetry-63912763`:

- `total_persons = 352,093`
- `train_persons = 281,674` (`79.9999 %`)
- `test_persons = 70,419` (`20.0001 %`)
- `ward_sample_true (WHERE in_ward_25k_sample = TRUE) = 25,000` (`6,818` en Clúster 0; `2,966` en Clúster 1; `11,924` en Clúster 2; `3,292` en Clúster 3 — coincidencia exacta `100 %` con `12_perfiles_ward_n25000_escala_original.csv`)
- `ward_direct_non_null (WHERE cluster_ward_25k_direct IS NOT NULL) = 25,000`
- **`invalid_ward_outside_sample (WHERE in_ward_25k_sample = FALSE AND cluster_ward_25k_direct IS NOT NULL) = 0`**

---

## 4. Representatividad por Estrato del Censo Cargado (Candidato C) frente a las Alternativas Muestrales (A y B)

| Variable de Estrato | Categorías | Población Clasificada ($N = 352,093$) | Candidato A (`25,000` Ward Train) · Máx $|\Delta|$ / `TVD` | Candidato B2 (`50,000` 80/20 + Piso 1,000) · `TVD` sin pond. / **Ponderado** | **Candidato C Cargado en Neon (`352,093` Personas)** · Mín $n_h$ / Máx $|\Delta|$ / **`TVD`** |
|---|---|---:|---|---|---|
| `university_level` | `5` (`Secondary school`, `Bachelor`, `Master`, `No reportado`, `PhD`) | `142,802 / 113,455 / 51,133 / 42,884 / 1,819` | `n_min = 126` (`PhD`) · Máx `0.2650 pp` · `TVD = 0.2650 pp` | `n_min = 1,054` · `TVD = 1.5914 pp` → **`0.0000 pp`** | `n_min = 1,819` (`PhD`) · Máx **`0.0000 pp`** · **`TVD = 0.0000 pp`** |
| `isco_major_1d_zfill` | `10` (`0` Militar a `9` Elementales, cero inicial preservado) | `598` (`ISCO 0`) a `84,916` (`ISCO 5`) | `n_min = 42` (`ISCO 0`), `69` (`ISCO 6`) · `TVD = 0.08 pp` | `n_min = 598` (`100 %` `ISCO 0`), `945` (`ISCO 6`) → **`0.0000 pp`** | `n_min = 598` (`100 %` `ISCO 0`) · Máx **`0.0000 pp`** · **`TVD = 0.0000 pp`** |
| `isco_major_modal_posthoc` | `9` (`1` a `9`, columna original `8.0`/`8.1`) | `945` (`ISCO 6`) a `75,913` (`ISCO 5`) | `n_min = 69` (`ISCO 6`) · Máx `0.0407 pp` · `TVD = 0.0799 pp` | `n_min = 945` (`100 %` `ISCO 6`) · `TVD = 2.1789 pp` → **`0.0000 pp`** | `n_min = 945` (`ISCO 6`) · Máx **`0.0000 pp`** · **`TVD = 0.0000 pp`** |
| `n_jobs_bin` | `5` (`1`, `2–3`, `4–5`, `6–8`, `9+` empleos) | `26,481 / 97,949 / 101,849 / 86,827 / 38,987` | `n_min = 1,893` · Máx `0.3358 pp` · `TVD = 0.3867 pp` | `n_min = 3,867` · `TVD = 0.6059 pp` → **`0.1764 pp`** | `n_min = 26,481` (`1_empleo`) · Máx **`0.0000 pp`** · **`TVD = 0.0000 pp`** |
| `cluster_kmeans_8_0` | `4` (`C0`, `C1 MNAR`, `C2`, `C3`) | `154,577 / 41,062 / 98,553 / 57,901` | `n_min = 2,906` · Máx `0.4494 pp` · `TVD = 0.4494 pp` | `n_min = 5,759` · `TVD = 1.7294 pp` → **`0.2312 pp`** | `n_min = 41,062` (`C1`) · Máx **`0.0000 pp`** · **`TVD = 0.0000 pp`** |
| `cluster_ward_3k_projected` | `4` (`C0`, `C1`, `C2`, `C3`) | `183,538 / 41,006 / 33,350 / 94,199` | `n_min = 2,396` · Máx `0.1121 pp` · `TVD = 0.1121 pp` | `n_min = 5,384` · `TVD = 1.2961 pp` → **`0.1810 pp`** | `n_min = 33,350` (`C2`) · Máx **`0.0000 pp`** · **`TVD = 0.0000 pp`** |
| `split` | `2` (`train` 80 %, `test` 20 %) | `281,674 / 70,419` | **`n_min = 0` (`test`) · Máx `20.0001 pp` · `TVD = 20.0001 pp`** | `n_min = 10,000` (`test`) · `TVD = 0.0001 pp` → **`0.0000 pp`** | `n_min = 70,419` (`test`) · Máx **`0.0000 pp`** · **`TVD = 0.0000 pp`** |

---

## 5. Mediciones Físicas Exactas en Neon (`pg_total_relation_size` y Latencia de Consultas)

### 5.1 Tamaño Físico Exacto por Tabla e Índices (`VACUUM ANALYZE` ejecutado en `steep-poetry-63912763`)

| Tabla en Neon (`schema public`) | Filas Exactas (`n_live_tup`) | `pg_table_size` (Bytes) | `pg_indexes_size` (Bytes) | `pg_total_relation_size` (Bytes) | Tamaño Total (`MiB`) | `pg_size_pretty` |
|---|---:|---:|---:|---:|---:|---:|
| **`person_experiences`** | `1,738,738` | `148,537,344` | `51,724,288` | **`200,261,632`** | **`190.984 MiB`** | `191 MB` |
| **`person_trajectories`** | `352,093` | `56,401,920` | `23,748,608` | **`80,150,528`** | **`76.438 MiB`** | `76 MB` |
| **`esco_occupations_catalog`** | `2,973` | `385,024` | `98,304` | **`483,328`** | **`0.461 MiB`** | `472 kB` |
| `agg_top_occupation_transitions` | `100` | `57,344` | `0` | `57,344` | `0.055 MiB` | `56 kB` |
| `agg_inclusion_exclusion_funnel` | `10` | `49,152` | `0` | `49,152` | `0.047 MiB` | `48 kB` |
| `agg_cleaning_and_iqr_audit` | `8` | `49,152` | `0` | `49,152` | `0.047 MiB` | `48 kB` |
| `agg_pca_variance_and_loadings` | `15` | `49,152` | `0` | `49,152` | `0.047 MiB` | `48 kB` |
| `agg_eda_distributions_and_segments` | `4` | `49,152` | `0` | `49,152` | `0.047 MiB` | `48 kB` |
| `agg_supervised_models_benchmark` | `15` | `49,152` | `0` | `49,152` | `0.047 MiB` | `48 kB` |
| `agg_decision_trees_comparison` | `15` | `49,152` | `0` | `49,152` | `0.047 MiB` | `48 kB` |
| `agg_naive_bayes_isco_rates` | `10` | `49,152` | `0` | `49,152` | `0.047 MiB` | `48 kB` |
| `agg_knn_neighbor_purity` | `11` | `49,152` | `0` | `49,152` | `0.047 MiB` | `48 kB` |
| `agg_clustering_executive_comparison` | `4` | `49,152` | `0` | `49,152` | `0.047 MiB` | `48 kB` |
| `agg_nm_rl04_annual_macro` | `24` | `40,960` | `0` | `40,960` | `0.039 MiB` | `40 kB` |
| `agg_nm_lg01_survival_curve` | `40` | `40,960` | `0` | `40,960` | `0.039 MiB` | `40 kB` |
| **TOTAL `15` TABLAS DE USUARIO + ÍNDICES** | **`2,094,060`** | **`205,905,920`** | **`75,571,200`** | **`281,477,120`** | **`268.440 MiB`** | **`268 MB`** |
| **TOTAL BASE DE DATOS (`pg_database_size('neondb')`)** | — | — | — | **`289,701,888`** | **`276.280 MiB`** | **`276 MB` (`26.98 %` de `1 GiB`)** |

### 5.2 Latencias Medidas de las Consultas Reales del Dashboard (`EXPLAIN (ANALYZE, BUFFERS)` y RTT Cliente)

- **Arranque en frío (*Cold Start* conexión inicial + `SELECT 1`):** **`1,616.69 ms`** (`<= 2,500 ms` objetivo: **GO**).
- **Tiempo total de carga masiva (`COPY` + creación de índices B-tree):** **`104.89 segundos`**.

| Consulta Real del Dashboard | Filas Devueltas | Nodo Superior del Plan (`EXPLAIN`) | Tiempo de Planificación en Motor (`ms`) | **Tiempo de Ejecución en Motor Postgres (`ms`)** | Latencia RTT Cliente → `aws-us-east-1` (`ms`) | Veredicto vs. Umbral Go/No-Go |
|---|---:|---|---:|---:|---:|---|
| **`Q1_headline_inclusion_exclusion_funnel`** (`SELECT * FROM agg_inclusion_exclusion_funnel ORDER BY stage_order`) | `10` | `Sort` | `0.047 ms` | **`0.043 ms`** | `75.11 ms` | **GO** (`<= 15 ms` motor / `<= 120 ms` RTT) |
| **`Q2_headline_supervised_models_benchmark`** (`SELECT * FROM agg_supervised_models_benchmark`) | `15` | `Seq Scan` (`1` pág.) | `0.027 ms` | **`0.028 ms`** | `73.50 ms` | **GO** (`<= 15 ms` motor / `<= 120 ms` RTT) |
| **`Q3_headline_clustering_executive`** (`SELECT * FROM agg_clustering_executive_comparison`) | `4` | `Seq Scan` (`1` pág.) | `0.034 ms` | **`0.034 ms`** | `74.70 ms` | **GO** (`<= 15 ms` motor / `<= 120 ms` RTT) |
| **`Q4_headline_numerical_methods_rl04_lg01`** (`SELECT * FROM agg_nm_rl04_annual_macro ORDER BY start_year`) | `24` | `Sort` | `0.050 ms` | **`0.049 ms`** | `83.13 ms` | **GO** (`<= 15 ms` motor / `<= 120 ms` RTT) |
| **`Q5_explorer_filtered_trajectories_limit50`** (`WHERE split='test' AND cluster_kmeans_8_0=0 AND isco_major_1d_zfill='5' ORDER BY resume_id LIMIT 50`) | `50` | `Limit` sobre `Index Scan` | `0.102 ms` | **`0.433 ms`** | `76.86 ms` | **GO** (`<= 25 ms` motor / `<= 150 ms` RTT) |
| **`Q6_explorer_single_person_timeline_join_esco`** (`person_experiences JOIN esco_occupations_catalog WHERE resume_id=47 ORDER BY job_order`) | `7` | `Nested Loop` (`Index Scan` PK) | `0.271 ms` | **`0.064 ms`** | `74.42 ms` | **GO** (`<= 25 ms` motor / `<= 150 ms` RTT) |
| **`Q7_explorer_ward_25k_only_filter_limit50`** (`WHERE in_ward_25k_sample=TRUE AND cluster_ward_25k_direct=2 LIMIT 50`) | `50` | `Limit` (`Index Scan` `idx_pt_ward25k`) | `0.087 ms` | **`0.119 ms`** | `80.09 ms` | **GO** (`<= 25 ms` motor / `<= 150 ms` RTT) |
