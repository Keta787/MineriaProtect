# DATA_DICTIONARY.md · Diccionario de Datos para la Muestra en Neon y el Dashboard en Vercel (`JobPath`)

> **Propósito:** Definir con precisión verificada todas las columnas —a nivel persona, experiencia laboral, transición y resumen de modelos— que alimentarán la muestra en **Neon PostgreSQL (plan gratuito: límite `< 1 GB` por proyecto)**, el **Dashboard interactivo en Vercel** y la **presentación en Reveal.js ($\le 10$ diapositivas)**.  
> **Idioma de interfaz de usuario:** Todas las etiquetas de cara al usuario final (dashboard y diapositivas) están especificadas en **español**, mientras que los identificadores de columnas y tablas se mantienen en **inglés / snake_case** según las reglas del proyecto.

---

## 1. Identificador de Persona y Estado de Anonimización (`resume_id` → `person_uid`)

| Atributo | Valor Verificado en el Repositorio | Fuente (Archivo + Celda/Línea) |
|---|---|---|
| **Columna original en CSV** | `resume_id` | `data/01_raw/JobHop_v2_*.csv` L1; `data/03_processed/empleos_unificado_limpio.csv` L1 |
| **Tipo de dato y rango observado** | Entero no negativo (`int64` / serializado como `str`), rango `[0, 444,480]`, media `222,207.3`, mediana `222,338.0` | `notebooks/refactor/2.0_preprocesamiento_jobpath.ipynb` Cell 7 (Output 3) |
| **Cardinalidad (personas únicas)** | - Crudo unificado (`02_interim`): `355,315` personas<br/>- Limpio completo (`03_processed`, Versiones A y B): **`355,308` personas**<br/>- Universo modelable con oficio ESCO clasificado: **`352,093` personas** (`281,674` en `train` + `70,419` en `test`; `0` solapadas)<br/>- Excluidas sin ningún oficio ESCO clasificado: **`3,215` personas** (`excluded_no_classified_job`) | `notebooks/refactor/2.0_preprocesamiento_jobpath.ipynb` Cell 5; `notebooks/refactor/5.0_EDA_jobpath.ipynb` Cell 53 (Outputs 0 y 2) |
| **Relación estructural** | `1:N` con las experiencias laborales (`1` persona tiene entre `1` y `20` empleos registrados; media `5.266`, mediana `5.000`; el `93.84 %` tiene $\ge 2$ empleos) | `notebooks/refactor/2.0_preprocesamiento_jobpath.ipynb` Cell 9 (Output 2); `notebooks/refactor/5.0_EDA_jobpath.ipynb` Cell 23 (Output 0) |
| **¿Está anonimizado en la fuente?** | **Seudonimizado (Pseudonymous), NO fuertemente anonimizado:** `aida-ugent/JobHop` eliminó los identificadores directos (no existen nombres, correos, teléfonos, documentos de identidad ni nombres de empresas en `01_raw`), asignando un entero secuencial `resume_id`. Sin embargo, la secuencia longitudinal de cuasi-identificadores `(start_date, end_date, occupation_code, university_level)` en Flandes (Bélgica) podría permitir **re-identificación indirecta por enlace** si un tercero cruza una trayectoria completa con perfiles públicos de CV/LinkedIn, y exponer `resume_id` en bruto permitiría re-vincular directamente con el dataset público de Hugging Face. | `README.md` L61, L78; `notebooks/refactor/2.0_preprocesamiento_jobpath.ipynb` Cell 9; `notebooks/refactor/5.0_EDA_jobpath.ipynb` Cell 1 |
| **Regla obligatoria para Neon y Vercel** | 1) **Reemplazar/hashear `resume_id` antes de subir a Neon:** generar `person_uid` mediante HMAC-SHA256 truncado con sal secreta (`person_uid = SUBSTR(ENCODE(HMAC(resume_id::text, SECRET_SALT, 'sha256'), 'hex'), 1, 12)`) o un ID secuencial de muestra (`person_id = 1..N`), sin exponer `resume_id` en la base de datos pública ni en la API de Vercel.<br/>2) **Nunca entra como feature en `X`:** `resume_id` / `person_uid` se utiliza exclusivamente como llave primaria de la tabla de personas y llave foránea de agrupación de trayectorias. | Regla de Gobernanza del Proyecto + `docs/RefactorDocs/train_test_split_por_persona.md` L22 |

---

## 2. Tabla Principal a Nivel Persona para Neon (`person_trajectories_sample`)

Esta tabla consolida en **una fila por persona** las métricas longitudinales del EDA (`5.0_EDA_jobpath.ipynb`), las `9` variables sin fuga de la vista primaria de clustering `V_PERSON` (`8.0_kmeans_clustering.ipynb` y `8.1_clustering_jerarquico.ipynb`), la partición oficial (`split_map_resume_id.csv`) y las asignaciones de clúster (`08_asignacion_clusters_personas_352093.csv` y `08_asignacion_clusters_personas_proyectada_352093.csv`).

> **Nota de presupuesto en Neon:** Incluso almacenando las **`352,093` personas clasificadas completas** (o una muestra estratificada de `25,000`–`50,000` personas), esta tabla de `22` columnas compactas ocupa **`~28 MB`** para las `352,093` personas (o **`~2–4 MB`** para `25,000`–`50,000` personas), es decir, menos del **`3 %`** del límite de `1 GB` del plan gratuito de Neon.

| Columna (Identificador en Inglés) | Tipo SQL Sugerido | Unidad / Rango Verificado | Origen Exacto en el Repositorio | Significado y Etiqueta en Español para el Dashboard |
|---|---|---|---|---|
| `person_uid` | ` TEXT PRIMARY KEY` | Hash hex de 12 caracteres (derivado de `resume_id` con sal) | Derivado de `resume_id` (`split_map_resume_id.csv`, `08_asignacion_clusters_personas_352093.csv`) | **ID Anonimizado de Persona** (reemplaza a `resume_id` por gobernanza de privacidad). |
| `split` | `TEXT` (`'train'` \| `'test'`) | `'train'` (`281,674` = `80.00 %`) · `'test'` (`70,419` = `20.00 %`) | `reports/eda_jobpath/tables/split_map_resume_id.csv` (`GroupShuffleSplit`, `seed=42`) | **Partición de Validación** (`Entrenamiento 80 %` / `Prueba 20 %`). |
| `n_jobs` | `SMALLINT` | Entero `[1, 20]` (media `5.266`, mediana `5.0`, Q1 `3`, Q3 `7`) | `5.0_EDA_jobpath.ipynb` Cell 23; `8.0_kmeans_clustering.ipynb` (`V_PERSON` col 1) | **Número de Empleos en la Trayectoria** (`Empleos registrados`). |
| `n_occ` | `SMALLINT` | Entero `[1, 20]` (media `4.025`, mediana `4.0`, Q1 `2`, Q3 `5`) | `5.0_EDA_jobpath.ipynb` Cell 23 (`scripts/ScriptsCsv/EDA/person_level.py`) | **Oficios ESCO Distintos Ejercidos** *(excluido de `X` en clustering para evitar circularidad con repetición; útil como indicador descriptivo en el dashboard)*. |
| `span_q` | `SMALLINT` | Trimestres `[2, 277]` (media `55.279`, mediana `44.0`, Q1 `24`, Q3 `78`) | `5.0_EDA_jobpath.ipynb` Cell 23; `8.0_kmeans_clustering.ipynb` (`V_PERSON` col 2) | **Amplitud Total de la Carrera (trimestres)** desde el inicio del primer empleo hasta el fin del último (`1 trimestre = 3 meses`). |
| `dur_total` | `SMALLINT` | Trimestres `[2, 2268]` (media `66.018`, mediana `46.0`, Q1 `23`, Q3 `88`) | `5.0_EDA_jobpath.ipynb` Cell 23 (`person_level.py`) | **Duración Acumulada de Contratos (trimestres)** (suma de `dur_q` de todos los empleos de la persona). |
| `dur_mean` | `REAL` | Trimestres `[2.0, 217.0]` (media `14.350`, mediana `9.0`, Q1 `5.0`, Q3 `17.333`) | `5.0_EDA_jobpath.ipynb` Cell 23; `8.0_kmeans_clustering.ipynb` (`V_PERSON` col 3) | **Duración Media por Empleo (trimestres)** (indicador central de permanencia laboral). |
| `overlap_ratio` | `REAL` | Ratio `[0.0, 13.345]` (media `1.176`, mediana `1.018`, Q1 `0.898`, Q3 `1.235`) | `5.0_EDA_jobpath.ipynb` Cell 23; `8.0_kmeans_clustering.ipynb` (`V_PERSON` col 4) | **Índice de Solapamiento Contractual (`dur_total / span_q`)** (`> 1.0` indica pluriempleo o contratos solapados en el mismo trimestre). |
| `mean_skills_competence` | `REAL` | Conteo medio `[0.0, 39.5]` en Versión B / `[0.0, 69.0]` en A | `8.0_kmeans_clustering.ipynb` (`V_PERSON` col 5, `scripts/ScriptsCsv/KMeans/feature_builder.py`) | **Promedio de Competencias Prácticas ESCO (*Saber Hacer*)** exigidas por los oficios de su trayectoria. |
| `mean_skills_knowledge` | `REAL` | Conteo medio `[0.0, 13.5]` en Versión B / `[0.0, 45.0]` en A | `8.0_kmeans_clustering.ipynb` (`V_PERSON` col 6) | **Promedio de Conocimientos Teóricos ESCO (*Saber*)** exigidos por los oficios de su trayectoria. |
| `mean_skills_essential` | `REAL` | Conteo medio `[3.0, 47.5]` en Versión B / `[3.0, 99.0]` en A | `8.0_kmeans_clustering.ipynb` Cell 10 (reportado en escala real; no entra en distancia euclidiana por $E = C + K$) | **Promedio de Competencias Esenciales Totales ESCO** del perfil de la persona. |
| `mean_prop_competence` | `REAL` | Proporción `[0.0, 1.0]` (centroides entre `0.75` en profesionales y `0.87` en operativos) | `8.0_kmeans_clustering.ipynb` (`V_PERSON` col 7) | **Proporción de Exigencia Práctica vs. Teórica (`competence / essential`)**. |
| `education_level_reported` | `TEXT` | `'Secondary school'` \| `'Bachelor'` \| `'Master'` \| `'PhD'` \| `'No reportado'` | `data/03_processed/empleos_unificado_limpio.csv` (`university_level`) | **Nivel Educativo Declarado** (`Secundaria`, `Pregrado / Bachelor`, `Maestría / Master`, `Doctorado / PhD`, `No reportado`). |
| `nivel_academico_ord_imputado` | `REAL` | Ordinal `[1.0, 4.0]` (`1=Secondary`, `2=Bachelor`, `3=Master`, `4=PhD`; imputado con mediana Train `2.0` cuando MNAR=1) | `8.0_kmeans_clustering.ipynb` (`V_PERSON` col 8) | **Nivel Académico Ordinal (`1..4`)** utilizado en K-Means y Ward sin relleno espurio con `0`. |
| `educacion_no_reportada` | `SMALLINT` | Binario `0` \| `1` (`1` en `42,884` personas = `11.56 %` según primera experiencia) | `7.0_arbol_decision.ipynb` Cell 6; `8.0_kmeans_clustering.ipynb` (`V_PERSON` col 9) | **Bandera de Educación No Reportada (MNAR)** (`1 = No reportado`, `0 = Reportado`). |
| `isco_major_modal_posthoc` | `SMALLINT` | Dígito ISCO-08 `0..9` (`10` grandes grupos ocupacionales) | `reports/kmeans_jobpath/tables/08_asignacion_clusters_personas_352093.csv` | **Gran Grupo Ocupacional ISCO-08 Modal** de la trayectoria de la persona (`0` Militares a `9` Ocupaciones elementales). |
| `n_returns` | `SMALLINT` | Entero `[0, 18]` (`0` en `54.70 %`, `1` en `23.91 %`, `2+` en `21.38 %`) | `5.0_EDA_jobpath.ipynb` Cell 23 | **Número de Retornos a Oficios Previos** *(descriptor longitudinal; equivale a `any_repeated_posthoc` cuando $\ge 1$)*. |
| `self_loop_share` | `REAL` | Proporción `[0.0, 1.0]` (media `0.111`, Q75 `0.167`) | `5.0_EDA_jobpath.ipynb` Cell 23, Cell 68 | **Proporción de Autolazos ($A \to A$)** (cambio de contrato manteniendo exactamente el mismo oficio ESCO). |
| `exploration_ratio` | `REAL` | Proporción `(0.0, 1.0]` (`n_occ / n_jobs`, media `0.799`, mediana `0.833`, Q75 `1.000`) | `5.0_EDA_jobpath.ipynb` Cell 23, Cell 68 | **Índice de Exploración Ocupacional (`oficios distintos / empleos totales`)**. |
| `eda_trajectory_segment` | `TEXT` | `'exploradora'` (`36.58 %`) \| `'mixta'` (`34.29 %`) \| `'permanente'` (`23.39 %`) \| `'sin transición'` (`5.74 %`) | `5.0_EDA_jobpath.ipynb` Cell 68 (`scripts/ScriptsCsv/EDA/person_level.py`) | **Tipología Descriptiva de Trayectoria (EDA `5.0`)** basada en umbrales Q75. |
| `any_repeated_posthoc` | `SMALLINT` | Binario `0` \| `1` (`1` si la persona repitió al menos un oficio en su carrera, `~45.3 %`) | `reports/kmeans_jobpath/tables/08_asignacion_clusters_personas_352093.csv` | **Indicador Post-Hoc de Reincidencia en la Carrera (`0/1`)** (evaluado *post-hoc* en clustering y equivalente a nivel persona de `reincide`). |
| `cluster_kmeans_k4` | `SMALLINT` | Clúster `0`, `1`, `2`, `3` (`0`: `43.90 %`, `1`: `11.66 %`, `2`: `27.99 %`, `3`: `16.44 %`) | `reports/kmeans_jobpath/tables/08_asignacion_clusters_personas_352093.csv` (`8.0`) | **Segmento Operativo K-Means++ ($k^*=4$):**<br/>`0`: Inserción Temprana y Trayectorias Cortas en Oficios Operativos<br/>`1`: Trabajadores con Educación No Reportada (MNAR) y Perfil Operativo Estable<br/>`2`: Profesionales Intensivos en Conocimiento y Alta Exigencia ESCO<br/>`3`: Trayectorias Consolidadas de Alta Rotación o Larga Permanencia |
| `cluster_ward_k4` | `SMALLINT` | Clúster `0`, `1`, `2`, `3` (proyectado por `NearestCentroid` desde Ward $n=3,000$ y $n=25,000$) | `reports/clustering_jerarquico_jobpath/tables/08_asignacion_clusters_personas_proyectada_352093.csv` (`8.1`) | **Segmento Jerárquico Aglomerativo Ward ($k^*=4$)** para contraste metodológico `8.0` vs. `8.1`. |

---

## 3. Tabla a Nivel Experiencia Laboral para la Muestra de Personas en Neon (`person_experiences_sample`)

Para las personas incluidas en la muestra de Neon (por ejemplo, una muestra estratificada de `10,000` a `25,000` personas $\approx 52,000$ a `130,000` experiencias laborales, ocupando **`~8–20 MB`**), esta tabla almacena la secuencia cronológica de empleos $S_p = [(t_1, \text{oficio}_1), (t_2, \text{oficio}_2), \dots]$ sin cargar las pesadas listas textuales `skills | knowledge | sin_tipo` ni las `2,967` columnas one-hot de `04_transformed`.

| Columna en CSV / Neon | Tipo SQL Sugerido | ¿Presente en `03_processed`? | Rango / Valores Verificados | Rol en el Dashboard y Reglas de Uso |
|---|---|---|---|---|
| `person_uid` | `TEXT` (FK) | Sí (como `resume_id`) | Hash hex de 12 caracteres | Agrupa y enlaza cada experiencia laboral con su persona en `person_trajectories_sample`. |
| `job_order` | `SMALLINT` | Derivada (`3.0` / `5.0`) | Entero `1..20` (`1` = primer empleo registrado) | **Orden Cronológico del Empleo** dentro de la trayectoria de la persona (`add_job_order`). |
| `start_date` | `TEXT` | Sí | `226` trimestres únicos en formato `'Q<1-4> <YYYY>'` (ej. `'Q3 1996'`) | **Trimestre de Inicio del Empleo**. |
| `end_date` | `TEXT` | Sí | `226` valores únicos (`'Q<1-4> <YYYY>'` o `'Present'`) | **Trimestre de Fin del Empleo** (`'Present'` indica empleo activo al capturar el CV). |
| `start_year` | `SMALLINT` | Derivada (`3.0` / `5.0`) | Año calendario `<= 2026` | **Año de Inicio del Empleo** (para filtros temporales y series históricas en el dashboard). |
| `dur_q` | `SMALLINT` | Derivada (`3.0` / `5.0`) | Trimestres `[2, 277]` en total / `[2, 225]` en clasificados (mediana `5.0`, media `12.537`) | **Duración del Empleo en Trimestres** (`end_ord - start_ord + 1`, con `'Present'` censurado en `2026-Q1`). |
| `es_vigente` | `BOOLEAN` / `SMALLINT` | Sí | `1` (`True`) en `95,136` filas (`5.08 %`); `0` (`False`) en el resto | **Bandera de Empleo Vigente (`Present`)** (censura a la derecha). |
| `university_level` | `TEXT` | Sí | `5` categorías: `'Secondary school'`, `'Bachelor'`, `'Master'`, `'PhD'`, `'No reportado'` | **Nivel Educativo Declarado** en el currículum. |
| `occupation_code` | `TEXT` | Sí | `2,973` códigos ESCO hoja distintos (`132,276` nulos = `7.07 %` en no clasificados) | **Código de Ocupación ESCO v1.2.1** (ej. `'3343.1'`, `'2353.1'`). |
| `occupation_label` | `TEXT` | Sí | `2,973` etiquetas en inglés del catálogo oficial ESCO (ej. `'administrative assistant'`) | **Nombre Oficial de la Ocupación ESCO**. |
| `isco_group` | `TEXT` | Sí | `426` grupos unitarios ISCO-08 de 4 dígitos (con `zfill(4)`, ej. `'0310'`, `'3343'`; `128,981` nulos) | **Código de Grupo Unitario ISCO-08 (4 dígitos)**. |
| `isco_group_label` | `TEXT` | Sí | `426` nombres de grupos ISCO-08 (ej. `'Administrative and executive secretaries'`) | **Nombre del Grupo Unitario ISCO-08**. |
| `isco_major_1d` | `SMALLINT` | Derivada (`7.0` / `7.1` / `8.0`) | Dígito `0..9` (`primer dígito de isco_group.zfill(4)`) | **Gran Grupo Ocupacional ISCO-08 (1 dígito)** con etiqueta oficial en español (`ISCO_MAJOR_LABELS_ES`). |
| `emparejado` | `TEXT` | Sí | `'ok'` (`1,738,738` = `92.93 %`) · `'unknown'` (`128,981` = `6.89 %`) · `'rescatado'` (`3,295` = `0.18 %`) | **Estado de Emparejamiento con ESCO**. |
| `n_skills_essential` | `REAL` | Sí | `[3.0, 99.0]` en Versión A · `[3.0, 47.5]` en Versión B (mediana `20.0`, Q1 `15.0`, Q3 `28.0`; `NaN` en no clasificados) | **Total de Competencias Esenciales ESCO Exigidas por el Oficio** *(requisito del cargo en ESCO, no habilidad medida del individuo)*. |
| `n_skills_competence` | `REAL` | Sí | `[0.0, 69.0]` en Versión A · `[0.0, 39.5]` en Versión B (mediana `18.0`, Q1 `12.0`, Q3 `23.0`) | **Competencias Prácticas ESCO (*Saber Hacer*) Exigidas por el Oficio**. |
| `n_skills_knowledge` | `REAL` | Sí | `[0.0, 45.0]` en Versión A · `[0.0, 13.5]` en Versión B (mediana `3.0`, Q1 `1.0`, Q3 `6.0`) | **Conocimientos Teóricos ESCO (*Saber*) Exigidos por el Oficio**. |
| `n_skills_sin_tipo` | `SMALLINT` | Sí | `[0, 2]` (`0` en el `99.10 %` de clasificadas; `> 0` en `15,610` filas = `0.90 %`) | **Competencias Esenciales sin Tipo Declarado en ESCO** (completa la identidad $E = C + K + \text{sin\_tipo}$). |
| `diff_competence_knowledge` | `REAL` | Derivada (`7.0`) | `n_skills_competence - n_skills_knowledge` (umbral raíz del Árbol 3 CART: `<= 16.50` vs. `> 16.50`) | **Diferencia entre Competencias Prácticas y Conocimientos Teóricos ($C - K$)** (variable raíz del Árbol 3 de `7.0`). |
| `prop_competence_essential` | `REAL` | Derivada (`7.0` / `8.0`) | `n_skills_competence / n_skills_essential` en `[0.0, 1.0]` | **Proporción de Competencias Prácticas sobre el Total Esencial ($C / E$)**. |
| `reincide` (`is_repeated_occupation`) | `SMALLINT` | Derivada (`3.0` / `5.0`) | Binario `0` \| `1` (`1` en `30.01 %` de Train y `29.97 %` de Test; `1` si `veces_ese_oficio > 1`) | **Variable Objetivo Supervisada (`Reincide en el Oficio`)**: vale `1` si la persona ejerce ese mismo oficio ESCO más de una vez en su trayectoria. |

> [!CAUTION]
> **Columnas de `03_processed` y `04_transformed` que NO deben cargarse en Neon ni usarse como predictores:**
> 1. **`veces_ese_oficio`, `veces_ese_oficio_rob`, `veces_ese_oficio_bin`:** Fuga directa del `100.00 %` del target `reincide` (`reincide = veces_ese_oficio > 1`). Solo se documentan en la sección de auditoría de fuga.
> 2. **`skills`, `knowledge`, `sin_tipo` (listas separadas por `|` en `03_processed`):** Ocupan `> 1.1 GB` de texto repetido por fila (hasta `2,588` caracteres por celda). Si el dashboard necesita mostrar los nombres de las competencias de un oficio, debe consultar una tabla catálogo `esco_occupation_catalog` de **`2,973` filas (`~1.94 MB`, `data/02_interim/Jobhop/competencias_por_oficio.csv`)** indexada por `occupation_code` (normalización `3NF`), ahorrando **`> 99.8 %`** de almacenamiento.
> 3. **`occupation_code_*` (`2,967` columnas dummy OHE en `data/04_transformed/X_*.csv`):** Ocupan `19.67 GiB` en CSV texto. En PostgreSQL la ocupación se representa con la columna indexada `occupation_code` (`TEXT`).

---

## 4. Tablas Pre-Agregadas Oficiales (`reports/*/tables/*.csv`) para Carga Directa en Neon

Para que el dashboard en Vercel y las 10 diapositivas de Reveal.js muestren instantáneamente todas las métricas verificadas del proyecto sin recalcular sobre `1.87M` filas en tiempo de consulta, se deben cargar en Neon las siguientes tablas resumen verificadas (que en conjunto pesan **`< 2 MB`**):

| Tabla Sugerida en Neon | Archivo CSV Fuente en `reports/` | Filas | Qué Alimenta en el Dashboard y en Reveal.js |
|---|---|---:|---|
| `isco_major_catalog` | `scripts/ScriptsCsv/NaiveBayes/config.py` + `reports/naive_bayes_jobpath/tables/10_o1_tasas_reincidencia_isco_1d.csv` | `10` | Catálogo de los 10 Grandes Grupos ISCO-08 (`0..9`) en español con soporte, tasa observada de reincidencia (`7.43 %` a `33.84 %`), IC 95 % de Wilson y probabilidad media `NB-H`. |
| `cleaning_funnel_log` | `data/03_processed/Limpio/bitacora_limpieza_unificado.csv` + `reports/arbol_decision_jobpath/tables/01_resumen_ocupaciones_no_estandarizadas.csv` | `13` | Embudo completo de datos desde `1,993,291` filas crudas → `1,871,014` limpias (`355,308` personas) → `1,738,738` clasificadas (`352,093` personas) → `1,391,018` Train / `347,720` Test. |
| `eda_transitions_top` | Salidas de `5.0_EDA_jobpath.ipynb` Cell 29 (`top_moves`, `transition_rates`, `return_stats`) | `38` | Resumen de las `1,386,645` transiciones (`11.95 %` autolazos, `10.31 %` retornos no adyacentes, `16.95 %` mismo ISCO) y top 20 pares de transición oficio $\to$ oficio. |
| `supervised_models_benchmark` | `reports/knn_jobpath/tables/13g_comparacion_unificada_version_a.csv` + `reports/knn_jobpath/tables/13f_comparacion_costos_computacionales.csv` + `reports/modelado_jobpath/tables/resultados_test_ab.csv` | `16` | Tabla maestra comparativa de todos los modelos supervisados (`Ref 1 Baseline`, `Ref 2 Todo-1`, `Ref 3 Logística 6.0`, `HistGB 6.0`, `Árboles 1–3 de 7.0`, `NB-G/B/H de 7.1`, `KNN-D/G/W de 7.2`) con `PR-AUC`, `ROC-AUC`, `F1`, `Recall`, `Precision`, `Accuracy`, `Brier` y tiempos de inferencia. |
| `supervised_performance_by_isco` | `reports/knn_jobpath/tables/12_k1_desempeno_por_isco_knn_vs_nb_h.csv` + `reports/naive_bayes_jobpath/tables/10_o2_desempeno_modelos_por_isco_1d.csv` | `30` | Desempeño desglosado por cada uno de los 10 grandes grupos ISCO-08 (`KNN-W` vs. `NB-H` vs. `NB-B` vs. `NB-G`). |
| `decision_tree_rules` | `reports/arbol_decision_jobpath/tables/06_reglas_negocio_consolidadas.csv` + `07_comparacion_tres_arboles_referencias_y_versiones.csv` | `28` | Reglas de negocio interpretables con soporte $\ge 0.5 \%$, `Lift` e IC 95 % de Wilson de los 3 árboles CART (`7.0`). |
| `clustering_k_search` | `reports/kmeans_jobpath/tables/02_busqueda_k_codo_silueta_dbi_personas.csv` + `reports/clustering_jerarquico_jobpath/tables/02_torneo_metodos_linkage.csv` + `03_evaluacion_cortes_k2_a_k8_ward.csv` | `18` | Curvas del Método del Codo, Silueta, Davies-Bouldin, Calinski-Harabasz, saltos verticales del dendrograma Ward (`10.060` en $k=4 \to 1.431$ en $k=5$) y torneo de linkages (`ward` vs. `complete`/`average`/`single`). |
| `clustering_profiles_summary` | `reports/kmeans_jobpath/tables/06_perfiles_completos_y_validacion_posthoc.csv` + `reports/clustering_jerarquico_jobpath/tables/12_perfiles_ward_n25000_escala_original.csv` + `13_matriz_ejecutiva_comparativa_8_0_vs_8_1.csv` | `16` | Retrato Robot en unidades reales originales (`n_jobs`, `span_q`, `dur_mean`, `overlap_ratio`, `competence`, `knowledge`, `essential`, `educacion_no_reportada`), tasas *post-hoc* de repetición (`reincide`), grupo ISCO dominante y acción recomendada del Observatorio Laboral para cada uno de los 4 clústeres. |
| `esco_occupation_catalog` | `data/02_interim/Jobhop/competencias_por_oficio.csv` + conteos por oficio en `03_processed` | `2,973` | Catálogo normalizado (`3NF`) de los `2,973` oficios ESCO clasificados con su etiqueta, grupo ISCO y conteos/listas de competencias (`~1.94 MB`). |


---

## [v1.1 — Addendum: Política Definitiva de `resume_id` sin Hash, Columnas de Estrato/Clúster ya Existentes en Disco, `sampling_weight` y Tablas de Métodos Numéricos]

> **Nota de Versionado (`v1.1`):** Esta sección actualiza y complementa de forma aditiva el diccionario de datos de `v1.0` conforme a las decisiones del usuario.

### 5. Política Definitiva sobre el Identificador de Persona (`resume_id` sin Hash)

- **Identificador canónico en Neon y en el Dashboard:** Se mantiene **`resume_id` (`INTEGER PRIMARY KEY`)** exactamente con sus valores enteros originales (`0..355,314`) procedentes del dataset público **JobHop v2**. **No se crea `person_uid` ni se aplica hashing (`SHA-256` descartado).**
- **Aviso obligatorio en la página `Metodología y Gobernanza` del Dashboard:**
  > *"Los identificadores `resume_id` corresponden a los códigos secuenciales públicos del conjunto de datos anonimizado JobHop v2 (VDAB / Ghent University, distribuido bajo licencia CC BY 4.0) enriquecido con la taxonomía europea ESCO v1.2.1 (Comisión Europea, CC BY 4.0). No contienen nombres, documentos nacionales de identidad ni datos de contacto personal."*

---

### 6. Columnas de Persona, Estrato, Partición y Clúster que YA Existen en Archivos CSV del Repositorio

Antes de construir la base de datos en Neon, las siguientes columnas ya se encuentran calculadas y persistidas en disco dentro de `reports/`:

| Archivo CSV Existente en el Repositorio | Filas | Columnas Disponibles en el Archivo | Uso Directo para Muestreo y Dashboard |
|---|---:|---|---|
| [reports/eda_jobpath/tables/split_map_resume_id.csv](file:///c:/Users/User/Documents/JobPath/MineriaProtect/reports/eda_jobpath/tables/split_map_resume_id.csv) | `355,308` | `resume_id, split` (`'train'` para `281,674` personas clasificadas; `'test'` para `70,419` personas clasificadas; `'unclassified'` para las `3,215` personas sin oficio ESCO) | Mapa oficial de partición `80/20` (`GroupShuffleSplit`, `seed=42`, `shared_persons = 0`). |
| [reports/kmeans_jobpath/tables/08_asignacion_clusters_personas_352093.csv](file:///c:/Users/User/Documents/JobPath/MineriaProtect/reports/kmeans_jobpath/tables/08_asignacion_clusters_personas_352093.csv) | `352,093` | `resume_id, split, cluster, nombre_segmento, n_jobs, span_q, dur_mean, overlap_ratio, mean_skills_competence, mean_skills_knowledge, mean_prop_competence, nivel_academico_ord_imputado, educacion_no_reportada, any_repeated_posthoc, tasa_reincide_persona_posthoc, isco_major_modal_posthoc` | **Tabla maestra a nivel persona ya materializada (`59.11 MB`):** contiene el `100 %` del censo clasificado (`352,093` personas), el `split`, el clúster K-Means (`8.0`), las `9` variables de `V_PERSON` y las variables post-hoc. |
| [reports/clustering_jerarquico_jobpath/tables/08_asignacion_clusters_personas_completo_nearest_centroid.csv](file:///c:/Users/User/Documents/JobPath/MineriaProtect/reports/clustering_jerarquico_jobpath/tables/08_asignacion_clusters_personas_completo_nearest_centroid.csv) | `352,093` | `resume_id, split, cluster, nombre_segmento, n_jobs, span_q, dur_mean, any_repeated_posthoc` | Asignación de clúster jerárquico Ward (`8.1`, modelo $n=3,000$ proyectado por `NearestCentroid` a las `352,093` personas, `32.82 MB`). |
| [reports/clustering_jerarquico_jobpath/tables/07_asignacion_clusters_muestra_descubrimiento.csv](file:///c:/Users/User/Documents/JobPath/MineriaProtect/reports/clustering_jerarquico_jobpath/tables/07_asignacion_clusters_muestra_descubrimiento.csv) | `3,000` | `resume_id, split, cluster, nombre_segmento, n_jobs, span_q, dur_mean, overlap_ratio, mean_skills_competence, mean_skills_knowledge, mean_prop_competence, nivel_academico_ord_imputado, educacion_no_reportada, any_repeated_posthoc, tasa_reincide_persona_posthoc, isco_major_modal_posthoc` | Submuestra de descubrimiento Ward (`n = 3,000` personas de `Train`, `seed = 42`). |

---

### 7. Columnas Adicionales de Diseño de Muestreo y Corrección `ISCO 0` en `person_trajectories_sample`

En la tabla a nivel persona (`person_trajectories_sample`), además de conservar `resume_id` (`INTEGER PRIMARY KEY`) en lugar de `person_uid`, se incorporan estas 3 columnas técnicas:

| Nombre de Columna | Tipo SQL (PostgreSQL) | Definición Exacta y Regla de Uso |
|---|---|---|
| `sampling_weight` | `REAL NOT NULL DEFAULT 1.0` | Peso de muestreo $w_i = \pi_i^{-1} = N_h / n_h$ (inversa de la probabilidad de inclusión de la persona en su estrato $h$). Vale exactamente `1.0` en diseños autoponderados o en el Censo Completo (`Candidato C`). Permite corregir cualquier estimación basada en la muestra cuando hay sobre-muestreo de estratos pequeños, mientras que las cifras titulares del dashboard se leen siempre de las tablas resumen pre-agregadas del censo completo. |
| `isco_major_1d_zfill` | `CHAR(1) NOT NULL` | Gran grupo ISCO-08 modal (`'0'`..`'9'`) calculado con relleno de 4 dígitos (`isco_group.astype(int).astype(str).str.zfill(4).str[0]`, idéntico a `occupation_code.str[0]`), que preserva las **`598` personas con moda en `0 · Ocupaciones militares`** (`4,195` experiencias) que en `isco_major_modal_posthoc` habían quedado plegadas en `'1'`, `'2'` y `'3'` por la lectura en coma flotante (`110.0, 210.0, 310.0`). Se conservan **ambas** columnas (`isco_major_modal_posthoc` para reproducibilidad 1:1 con `8.0`/`8.1` e `isco_major_1d_zfill` para clasificación ISCO-08 exacta). |
| `in_ward_25k_sample` | `BOOLEAN NOT NULL` | `TRUE` si la persona pertenece a la muestra estratificada de `25,000` personas de `Train` usada en la expansión RAM de Ward (`8.1` Celda 10, `seed = 42`). Permite filtrar instantáneamente en el dashboard el subconjunto exacto de Ward `n = 25,000` incluso si se carga una muestra mayor (`50,000` o `352,093`). |

---

### 8. Tablas Resumen Pre-Agregadas Adicionales para las 2 Diapositivas de Métodos Numéricos (`< 20 KB`)

Para respaldar desde Neon tanto el dashboard como las 2 diapositivas dedicadas a Métodos Numéricos (dentro del límite de 12 diapositivas de Reveal.js), se añaden dos tablas pre-agregadas verificadas:

| # | Nombre de Tabla en Neon | Filas | Columnas Principales | Fuente Exacta |
|---|---:|---:|---|---|
| `10` | `agg_nm_rl04_annual_ols` | `24` (serie anual) + `15` (modelos MCO) | `start_year, n_starts, n_closed_starts, mean_skills, mean_dur_q, mean_dur_q_incl_active, mean_green, reincide_rate, y_pred_2000_2019, is_extrapolation, physically_invalid` | `numerical_methods_presentation/case_01_RL04_annual_drift_extrapolation/tables/rl04_*.csv` (verificado contra `03_processed`, `F-048`) |
| `11` | `agg_nm_lg01_survival_runge` | `40` ($S(q)$) + `15` (benchmark Runge) | `quarter_q, years, survival_prob_S_q, P3_pred, L0_q4, L1_q8, L2_q20, L3_q40, degree, node_strategy, max_abs_err, rmse, min_pred, max_pred, n_prob_bound_violations` | `numerical_methods_presentation/case_02_LG01_survival_and_runge/tables/lg01_*.csv` (verificado sobre `1,643,772` empleos cerrados clasificados, `F-049`) |
