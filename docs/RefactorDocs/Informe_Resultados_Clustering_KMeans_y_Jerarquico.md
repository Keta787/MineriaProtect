# Informe Consolidado de Especificaciones, Resultados y Explicación Causal · Clustering K-Means (`8.0`) y Jerárquico Aglomerativo (`8.1`)

> **Proyecto:** `MineriaProtect` (JobPath — Observatorio Laboral de Formaciones Educativas y Trayectorias Ocupacionales)  
> **Unidad / Fase:** Unidad 2 · Sesión 9 (CRISP-DM Fase 4 y Fase 5 · Descubrimiento de Estructura No Supervisada)  
> **Corridas vigentes verificadas:**  
> - **Clustering Jerárquico Aglomerativo (`8.1_clustering_jerarquico.ipynb`):** `RUN-20261119-180235` (`2026-11-19 18:02:35` · `[CURRENT]`)  
> - **Clustering K-Means (`8.0_kmeans_clustering.ipynb`):** `RUN-20261119-181140` (`2026-11-19 18:11:40` · `[CURRENT]`)  
> **Guías técnicas base:** `01_agglomerative_hierarchical_clustering.md` y `02_kmeans_clustering.md`

---

## 1. Especificaciones Técnicas de Cómo Quedó la Implementación

### 1.1 Arquitectura de Archivos, Cuadernos y Artefactos Generados

| Componente | Clustering Jerárquico Aglomerativo (`01`) | Clustering K-Means (`02`) |
|---|---|---|
| **Cuaderno ejecutado (`.ipynb`)** | `notebooks/refactor/8.1_clustering_jerarquico.ipynb` | `notebooks/refactor/8.0_kmeans_clustering.ipynb` |
| **Paquete modular (`scripts/ScriptsCsv/`)** | `scripts/ScriptsCsv/ClusteringJerarquico/` (`config.py`, `sampling_and_features.py`, `hierarchical_engine.py`, `profiling_and_plots.py`, `markdown_writers.py`) | `scripts/ScriptsCsv/KMeans/` (`config.py`, `feature_builder.py`, `kmeans_engine.py`, `pca_and_plots.py`, `markdown_writers.py`) |
| **Bitácora técnica append-only** | `notebooks/refactor/Bitacora_Clustering_Jerarquico.md` | `notebooks/refactor/Bitacora_KMeans.md` |
| **Reporte de sensibilidad A vs. B** | `notebooks/refactor/Comparacion_A_vs_B_Clustering_Jerarquico.md` | `notebooks/refactor/Comparacion_A_vs_B_KMeans.md` |
| **Carpeta de figuras (`.png`, 300 DPI)** | `reports/clustering_jerarquico_jobpath/figures/` (7 figuras) | `reports/kmeans_jobpath/figures/` (7 figuras) |
| **Carpeta de tablas (`.csv`)** | `reports/clustering_jerarquico_jobpath/tables/` (9 tablas CSV) | `reports/kmeans_jobpath/tables/` (9 tablas CSV) |

### 1.2 Universo de Datos, Higiene Anti-Fuga y Variables Utilizadas

1. **Insumos verificados por huella `SHA-256` (intactos antes y después de correr)**:
   - **Versión B · SIN outliers IQR (Primaria):** `data/03_processed/empleos_limpio_con_competencias_sin_outliers.csv` (`SHA-256: c8ea36b51dea8803...`).
   - **Versión A · CON outliers (Sensibilidad):** `data/03_processed/empleos_unificado_limpio.csv` (`SHA-256: 68cd34c624e8d23e...`).
   - **Mapa oficial de partición por persona (`resume_id`):** `reports/eda_jobpath/tables/split_map_resume_id.csv` (`SHA-256: 67dd3e3d68e1ff5e...`, `seed = 42`, `0` personas compartidas entre Train y Test).
2. **Embudo exacto de filas y personas (`Uso de datos`)**:
   - **Universo bruto en CSV:** `1,871,014` experiencias laborales y `355,308` personas únicas.
   - **Excluidas en RAM por carecer de código ESCO (`es_ocupacion_clasificada == 0`):** `132,276` filas (`7.07%`: `128,981` con `emparejado == 'unknown'` y `3,295` con `'rescatado'` sin padre ESCO; `3,215` personas exclusivas).
   - **Universo clasificado modelado (`es_ocupacion_clasificada == 1`):** **`1,738,738` experiencias laborales** y **`352,093` personas únicas**:
     - **Partición `Train` (80% por persona):** `1,391,018` experiencias y `281,674` personas.
     - **Partición `Test` (20% por persona):** `347,720` experiencias y `70,419` personas.
3. **Dos vistas analíticas complementarias (100% libres de fuga del target)**:
   - **Vista Primaria · Personas / Trayectorias (`V_PERSON`, 9 variables sobre `352,093` personas):**
     `n_jobs`, `span_q`, `dur_mean`, `overlap_ratio`, `mean_skills_competence`, `mean_skills_knowledge`, `mean_prop_competence`, `nivel_academico_ord_imputado`, `educacion_no_reportada`.
   - **Vista Secundaria · Experiencias / Perfiles de Exigencia ESCO (`V_EXPERIENCE`, 7 variables sobre `1,738,738` experiencias):**
     `dur_q`, `job_order`, `n_skills_competence`, `n_skills_knowledge`, `prop_competence_essential`, `nivel_academico_ord_imputado`, `educacion_no_reportada`.
4. **Tres decisiones de ingeniería de variables que explican la limpieza del modelo**:
   - **Cero Fuga (`Zero Target Leakage`):** Se excluyeron de `X` todas las columnas que definen o restatean la etiqueta supervisada (`reincide`, `veces_ese_oficio`, `n_returns`, `n_self_loops`, `n_occ`, `exploration_ratio = n_occ / n_jobs`). La variable `reincide` (`any_repeated_posthoc` a nivel persona) se reservó **exclusivamente para evaluación externa *post-hoc*** después de formar los clústeres.
   - **Eliminación de la colinealidad aditiva exacta ($E = C + K$):** Como `n_skills_essential = n_skills_competence + n_skills_knowledge` se cumple exactamente en el `99.10%` de las filas clasificadas (`n_skills_sin_tipo == 0`), incluir los tres conteos en `X` habría duplicado el peso del volumen total de competencias en la distancia euclidiana. Por eso `X` incluye `competence`, `knowledge` y la proporción `prop_competence_essential`, mientras que `n_skills_essential` se reporta en las tablas de perfiles en escala real.
   - **Tratamiento MNAR de educación sin relleno espurio con `0`:** Los `200,934` registros con `university_level == 'No reportado'` (`160,664` en Train y `40,270` en Test; `42,884` personas según su primera experiencia) no son "educación cero". Se codificaron mediante la bandera binaria ortogonal `educacion_no_reportada` ($0/1$) más el ordinal `1..4` imputado con la mediana de Train (`2.0 = Bachelor`).

---

## 2. Qué Resultados Se Obtuvieron en el Clustering Jerárquico Aglomerativo (`8.1` · `RUN-20261119-180235`)

### 2.1 Torneo de Métodos de Linkage (`n = 3,000` personas estandarizadas de Train, `k = 4`)

| Método de Linkage | Correlación Cofenética (`cophenet`) | Silhouette Score ($k=4$) | Davies-Bouldin Index ($k=4$) | Calinski-Harabasz Index | Tamaño Mín. Clúster ($n$) | Tamaño Máx. Clúster ($n$) | % en Clúster Más Grande | Diagnóstico y Decisión |
|---|---|---|---|---|---|---|---|---|
| **`ward` (Seleccionado)** | **`0.4463`** | **`0.1827`** | **`1.9489`** | **`370.72`** | **`160`** (`5.33%`) | **`1,650`** | **`55.00%`** | **SELECCIONADO:** minimiza varianza intra-clúster ($\Delta\text{ESS}$) y produce 4 grupos balanceados y accionables. |
| `complete` | `0.5623` | `0.2249` | `1.3672` | `210.72` | `38` (`1.27%`) | `2,701` | `90.03%` | Descartado por encadenamiento: 1 mega-clúster absorbe el `90.03%` de las personas. |
| `average` | `0.7348` | `0.4431` | `0.8927` | `121.36` | `2` (`0.07%`) | `2,925` | `97.50%` | Descartado por encadenamiento severo: 1 mega-clúster absorbe el `97.50%` y deja hojas de 2 personas. |
| `single` | `0.5010` | `0.5048` | `0.4334` | `10.53` | `1` (`0.03%`) | `2,996` | `99.87%` | Descartado por patología extrema de *chaining*: `2,996` de `3,000` personas caen en un solo grupo (`99.87%`). |

### 2.2 Determinación del Corte Horizontal Óptimo del Dendrograma Ward (`k = 2..8`)

| Número de Clústeres ($k$) | Altura Fusión Superior Ward | Altura Fusión Inferior Ward | Salto Vertical de Fusión ($\Delta h$) | Altura de Corte Recomendada | Silhouette Score | Davies-Bouldin Index | Calinski-Harabasz Index | % Clúster Mínimo | % Clúster Máximo |
|---|---|---|---|---|---|---|---|---|---|
| `2` | `76.439` | `71.141` | `5.297` | `73.790` | `0.2204` | `1.5182` | `363.74` | `11.37%` | `88.63%` |
| `3` | `71.141` | `60.951` | `10.190` | `66.046` | `0.1803` | `2.2490` | `379.14` | `11.37%` | `55.00%` |
| **`4` (Corte Óptimo)** | **`60.951`** | **`50.891`** | **`10.060`** | **`55.921`** | **`0.1827`** | **`1.9489`** | **`370.72`** | **`5.33%`** | **`55.00%`** |
| `5` | `50.891` | `49.460` | **`1.431`** | `50.176` | `0.1812` | `1.8463` | `350.22` | `5.33%` | `55.00%` |
| `6` | `49.460` | `48.624` | `0.837` | `49.042` | `0.1462` | `1.8035` | `342.69` | `5.33%` | `44.60%` |
| `7` | `48.624` | `44.783` | `3.840` | `46.703` | `0.1521` | `1.6632` | `343.46` | `4.67%` | `44.60%` |
| `8` | `44.783` | `36.872` | `7.912` | `40.827` | `0.1200` | `1.6812` | `342.58` | `4.67%` | `27.00%` |

- **Hallazgo estructural del dendrograma:** Entre $k=3$ y $k=4$ el salto vertical de fusión de Ward es muy pronunciado (`10.190` y `10.060`), mientras que al intentar dividir en $k=5$ el salto colapsa a **`1.431`** (una caída del `85.8%` en la ganancia de separación jerárquica). Esto demuestra matemáticamente que el árbol contiene **4 macro-ramas naturales** cortando a la altura `55.921`.

### 2.3 Perfiles Jerárquicos en Escala Original (`Retrato Robot`) proyectados a las `352,093` Personas

| Clúster Jerárquico (Ward, $k=4$) | Nombre Accionable del Segmento | Tamaño Proyectado ($n$ y $\%$) | Empleos Medios (`n_jobs`) | Amplitud Carrera (`span_q` trim.) | Duración Media (`dur_mean` trim.) | Solapamiento (`overlap_ratio`) | Competencias Prácticas / Conocimientos / Esenciales ESCO | Educación No Reportada (`MNAR`) | Tasa Post-Hoc Repetición en Test (`%` y `Lift`) | Gran Grupo ISCO Dominante |
|---|---|---|---|---|---|---|---|---|---|---|
| **Clúster 0** | **Inserción Temprana y Trayectorias Cortas en Oficios Operativos** | `183,538` (`52.13%`) | `4.42` | `32.64` | `8.00` | `1.01` | `18.76` / `3.16` / `21.96` | `0.00` (`0%`) | `43.53%` (`0.953x`) | `5 · Servicios y vendedores` |
| **Clúster 1** | **Especialistas Estables de Permanencia Prolongada (con MNAR educativo)** | `41,006` (`11.65%`) | `4.71` | `59.40` | `15.04` | `1.04` | `18.23` / `3.15` / `21.40` | `1.00` (`100%`) | `45.11%` (`0.988x`) | `5 · Servicios y vendedores` |
| **Clúster 2** | **Profesionales Intensivos en Conocimiento y Alta Exigencia ESCO** | `33,350` (`9.47%`) | `3.69` | `45.97` | `14.69` | `1.04` | `16.13` / **`7.69`** / **`23.99`** | `0.04` (`4%`) | **`34.34%` (`0.752x`)** | `2 · Profesionales científicos e intelectuales` |
| **Clúster 3** | **Trayectorias de Alta Rotación y Multi-Empleo Solapado** | `94,199` (`26.75%`) | **`6.49`** | **`96.59`** | **`27.10`** | **`1.51`** | `18.40` / `3.81` / `22.23` | `0.01` (`1%`) | **`54.17%` (`1.186x`)** | `3 · Técnicos y profesionales de nivel medio` |

---

## 3. Qué Resultados Se Obtuvieron en el Clustering K-Means (`8.0` · `RUN-20261119-181140`)

### 3.1 Búsqueda del $k$ Óptimo (`k = 2..8` · Método del Codo + Silueta + Davies-Bouldin + Calinski-Harabasz)

#### Vista Primaria · Personas (`281,674` personas en Train) y Vista Secundaria · Experiencias (`1,391,018` filas en Train)

| $k$ | Inercia WCSS (Personas) | Caída Relativa Inercia (Personas) | Silhouette Score (Personas) | Davies-Bouldin (Personas) | Calinski-Harabasz (Personas) | Silhouette Score (Experiencias) | Davies-Bouldin (Experiencias) | Decisión Metodológica |
|---|---|---|---|---|---|---|---|---|
| `2` | `2,185,781.34` | `0.00%` | `0.1660` | `2.2810` | `45,011.74` | `0.1951` | `1.9733` | Demasiado grueso (2 macro-bloques) |
| `3` | `1,921,139.73` | `12.11%` | `0.1958` | `1.8498` | `45,006.23` | `0.2342` | `1.6059` | Fusiona trayectorias largas con operativas |
| **`4` ($k^*$)** | **`1,692,018.00`** | **`11.93%`** | **`0.1948`** | **`1.6298`** | **`46,780.83` (Máx)** | **`0.2465` (Máx)** | **`1.4488`** | **SELECCIONADO:** Codo de inercia + máximo Calinski-Harabasz en Personas + máxima Silueta en Experiencias + concordancia con Ward ($k^*=4$) |
| `5` | `1,547,830.99` | `8.52%` | `0.1751` | `1.6292` | `44,913.59` | `0.2373` | `1.3699` | Caída de Silueta y caída de ganancia marginal (`8.52%`) |
| `6` | `1,428,115.55` | `7.73%` | `0.1821` | `1.4943` | `43,665.04` | `0.2165` | `1.3929` | Sobre-fragmentación (`clúster mín = 2.92%`) |
| `7` | `1,322,114.13` | `7.42%` | `0.1856` | `1.4638` | `43,068.59` | `0.2229` | `1.2686` | Sobre-fragmentación (`clúster mín = 2.86%`) |
| `8` | `1,244,354.29` | `5.88%` | `0.1736` | `1.4372` | `41,737.18` | `0.2177` | `1.2384` | Sobre-fragmentación (`clúster mín = 2.80%`) |

### 3.2 Verificación de Equivalencia Matemática Exacta de Centroides en Escala Original

Uno de los requisitos centrales de la Sesión 9 fue extraer los centroides en **escala original real** mediante `scaler.inverse_transform(km.cluster_centers_)` y demostrar que coinciden con `df_train.groupby("cluster")[V].mean()`:
- **Diferencia máxima absoluta en Vista Personas (`281,674` filas Train × 9 variables):** **`0.000000`** (`< 10^{-12}`).
- **Diferencia máxima absoluta en Vista Experiencias (`1,391,018` filas Train × 7 variables):** **`0.000001`**.

### 3.3 Perfiles K-Means en Escala Original (`Retrato Robot`) en `Train` (80%) y `Test` (20%)

#### A. Vista Primaria · Personas (`352,093` Personas Clasificadas: `281,674` Train / `70,419` Test)

| Clúster K-Means ($k=4$) | Nombre del Segmento | % Train / % Test ($n$ Total) | Centroide `n_jobs` (empleos) | Centroide `span_q` (trimestres) | Centroide `dur_mean` (trimestres) | Centroide `overlap_ratio` | Centroide `competence` / `knowledge` / `essential` | Centroide `nivel_academico` / `MNAR` | Tasa Post-Hoc Repetición en Test (`%` y `Lift`) | Gran Grupo ISCO Dominante |
|---|---|---|---|---|---|---|---|---|---|---|
| **Clúster 0** | **Inserción Temprana y Trayectorias Cortas en Oficios Operativos** | `43.94%` / `43.73%` (`154,577`) | `4.82` | `38.71` | `8.75` | `1.03` | `18.08` / `2.51` / `20.63` | `1.42` / `0.00` | **`47.78%` (`1.046x`)** | `5 · Servicios y vendedores` |
| **Clúster 1** | **Trabajadores con Educación No Reportada (MNAR) y Perfil Operativo Estable** | `11.65%` / `11.70%` (`41,062`) | `4.72` | `58.35` | `14.12` | `1.03` | `18.12` / `3.22` / `21.37` | `2.00` / **`1.00`** | `45.00%` (`0.985x`) | `5 · Servicios y vendedores` |
| **Clúster 2** | **Profesionales Intensivos en Conocimiento y Alta Exigencia ESCO** | `27.95%` / `28.14%` (`98,553`) | `4.92` | `42.54` | `10.44` | `1.12` | **`19.34` / `5.98` / `25.37`** | **`2.33`** / `0.00` | **`42.75%` (`0.936x`)** | `2 · Profesionales científicos e intelectuales` |
| **Clúster 3** | **Trayectorias Consolidadas de Alta Rotación o Larga Permanencia** | `16.45%` / `16.43%` (`57,901`) | **`5.44`** | **`112.14`** | **`37.47`** | **`1.61`** | `17.58` / `3.71` / `21.33` | `1.45` / `0.02` | `45.55%` (`0.997x`) | `3 · Técnicos y profesionales de nivel medio` |

#### B. Vista Secundaria · Experiencias Laborales (`1,738,738` Experiencias: `1,391,018` Train / `347,720` Test)

| Clúster K-Means ($k=4$) | Nombre del Segmento | % Train / % Test ($n$ Total) | Centroide `dur_q` (trimestres) | Centroide `job_order` | Centroide `competence` / `knowledge` / `essential` | Proporción Práctica (`prop_competence`) | Centroide `nivel_academico` / `MNAR` | Tasa Post-Hoc `reincide` en Test (`%` y `Lift`) | Gran Grupo ISCO Dominante |
|---|---|---|---|---|---|---|---|---|---|
| **Clúster 0** | **Experiencias Iniciales de Corta Duración y Exigencia Práctica** | `49.59%` / `49.51%` (`861,919`) | `7.86` | `3.72` | `17.59` / `1.81` / `19.43` | **`0.90`** | `1.53` / `0.00` | **`31.85%` (`1.063x`)** | `5 · Servicios y vendedores` |
| **Clúster 1** | **Puestos Operativos y de Servicios con Educación No Reportada (MNAR)** | `11.14%` / `11.17%` (`193,789`) | `11.50` | `3.68` | `18.20` / `3.29` / `21.50` | `0.84` | `2.00` / **`1.00`** | `30.86%` (`1.030x`) | `5 · Servicios y vendedores` |
| **Clúster 2** | **Ocupaciones Técnicas y Profesionales de Alta Complejidad ESCO** | `31.91%` / `32.01%` (`555,229`) | `8.76` | **`4.08`** | **`20.21` / `7.05` / `27.33`** | `0.72` | **`2.07`** / `0.00` | `28.32%` (`0.945x`) | `2 · Profesionales científicos e intelectuales` |
| **Clúster 3** | **Empleos de Etapa Avanzada de Carrera o Larga Permanencia** | `7.36%` / `7.32%` (`127,801`) | **`66.30`** | `3.08` | `17.65` / `3.53` / `21.23` | `0.83` | `1.61` / `0.05` | **`23.13%` (`0.772x`)** | `3 · Técnicos y profesionales de nivel medio` |

---

## 4. El Porqué de Estos Resultados: Explicación Causal, Matemática y de Negocio

A continuación se explica **por qué** emergieron exactamente estos números y estructuras al implementar ambos algoritmos sobre `MineriaProtect`:

### 4.1 ¿Por qué `single`, `average` y `complete` colapsaron en un mega-clúster (`90%–99.87%`) mientras que `ward` produjo 4 grupos equilibrados?
- **Causa geométrica (Efecto Encadenamiento o *Chaining*):** En datos reales de trayectorias laborales (`352,093` personas en un espacio continuo de 9 dimensiones), no existen "islas vacías" gigantescas entre trabajadores, sino una nube continua de densidad variable con colas hacia carreras largas (`span_q > 100`) y alto solapamiento (`overlap_ratio > 2`).
  - `single` une grupos por la distancia entre su **par de puntos más cercano** ($\min d(a,b)$), por lo que forma puentes locales a través de la nube densa y absorbe al **`99.87%` (`2,996 / 3,000`)** de las personas en un solo grupo, dejando las otras 3 ramas para 4 outliers extremos.
  - `average` (`97.50%`) y `complete` (`90.03%`) sufren del mismo sesgo porque las distancias euclidianas de unos pocos trabajadores con carreras muy largas o solapadas superan el diámetro del núcleo denso.
  - **`ward`**, en cambio, penaliza el incremento en la suma de cuadrados intra-clúster pondera por el tamaño del grupo ($\Delta \text{ESS} = \frac{|A||B|}{|A|+|B|}\|\mu_A - \mu_B\|_2^2$). A medida que un clúster crece en $|A|$, fusionarlo se vuelve cuadráticamente más costoso, obligando al algoritmo a particionar el núcleo denso en **4 segmentos balanceados** (`52.13%`, `26.75%`, `11.65%`, `9.47%`).

### 4.2 ¿Por qué ambos métodos (el salto vertical del dendrograma Ward y las curvas de K-Means) coinciden exactamente en $k^* = 4$?
- **Causa estructural en los datos (4 dimensiones ortogonales dominantes):** Al estandarizar las variables con `StandardScaler`, la varianza total de las trayectorias laborales se organiza a lo largo de **cuatro ejes reales del mercado laboral**:
  1. **Eje 1 · Núcleo operativo de carrera corta/media con educación reportada** $\to$ **Clúster 0** (`~44%–52%` de las personas).
  2. **Eje 2 · Ortogonalidad de la educación no reportada (`educacion_no_reportada == 1`, `11.56%` del dataset)** $\to$ Como la bandera MNAR vale `1` en el `11.65%` de las personas y `0` en el `88.35%`, al estandarizarse a media `0` y varianza `1`, los registros con `educacion_no_reportada == 1` adquieren un puntaje $z = +2.687$ (a casi 3 desviaciones estándar del resto). Tanto Ward como K-Means descubren de inmediato este subespacio natural como el **Clúster 1 (`11.65%` en ambos algoritmos)**.
  3. **Eje 3 · Complejidad cognitiva y teórica del oficio (`mean_skills_knowledge` y `nivel_academico_ord`)** $\to$ Separa las ocupaciones profesionales e intelectuales (Gran Grupo ISCO `2`, con `5.98` a `7.69` conocimientos especializados y menor proporción puramente manual `prop_competence = 0.66–0.75`) en el **Clúster 2**.
  4. **Eje 4 · Extensión temporal, permanencia y multi-empleo (`span_q`, `dur_mean`, `n_jobs`, `overlap_ratio`)** $\to$ Separa las carreras extensas (`span_q = 96.6–112.1` trimestres, `dur_mean = 27.1–37.5` trimestres, `overlap_ratio = 1.51–1.61`) en el **Clúster 3**.
- **Por qué en $k=5$ cae la calidad:** Una vez separados esos 4 ejes reales, un quinto clúster ($k=5$) se ve forzado a cortar arbitrariamente por la mitad el núcleo operativo homogéneo (Clúster 0), haciendo que el salto vertical de Ward se desplome de **`10.060` a `1.431`** y que el Silhouette Score de K-Means caiga de **`0.1948` a `0.1751`** (y en Experiencias de **`0.2465` a `0.2373`**).

### 4.3 ¿Por qué el Coeficiente de Silueta está en el rango `0.18 – 0.25` y qué significa?
- Tal como explica expresamente la guía de la **Sesión 9 (Sección 4.2)**: *"Las siluetas bajas ($\approx 0.1 - 0.3$) son **normales** en datos comerciales y socioeconómicos reales. Lo importante es que los grupos sean **accionables**, no perfectos."*
- **Causa estadística:** En trayectorias laborales humanas (`352,093` personas), variables como la duración del empleo (`dur_q`), el número de empleos (`n_jobs`) y el conteo de competencias ESCO forman un **continuo gradual** (un trabajador con 4 empleos y 35 trimestres está cerca de uno con 5 empleos y 40 trimestres en la frontera entre clústeres). Por eso muchos puntos fronterizos tienen $s(i)$ cercano a `0.05–0.15`, situando el promedio en `0.1948` (Personas) y `0.2465` (Experiencias), mientras que los centroides reales de los 4 grupos están **fuertemente diferenciados** y son 100% estables entre `Train` (`80%`) y `Test` (`20%`) (las proporciones de los 4 clústeres en Train vs. Test difieren en menos de `0.21` puntos porcentuales: `43.94% vs 43.73%`, `11.65% vs 11.70%`, `27.95% vs 28.14%` y `16.45% vs 16.43%`).

### 4.4 ¿Por qué los clústeres presentan diferencias tan claras en la tasa *post-hoc* de repetición de oficio (`reincide`) sin haber usado `reincide` para entrenar?
- **En el Clúster 2 (Profesionales Intensivos en Conocimiento · ISCO 2):** La tasa post-hoc de repetición ocupacional es la **más baja** en ambos métodos (`34.34%`, `Lift = 0.752x` en Ward; `42.75%`, `Lift = 0.936x` en K-Means Personas; `28.32%`, `Lift = 0.945x` en K-Means Experiencias). **¿Por qué?** Porque en carreras científicas, intelectuales y de gestión (con alto nivel universitario `2.33` y alto conocimiento teórico ESCO), la movilidad laboral ocurre por **ascenso vertical entre cargos con distinto código ESCO** (p. ej., de analista junior a especialista, líder de proyecto o gerente), en lugar de repetir cíclicamente el mismo código de oficio.
- **En el Clúster 3 de Ward (`Alta Rotación y Multi-Empleo`, `n_jobs = 6.49`, `overlap_ratio = 1.51`) y en el Clúster 0 de K-Means (`Oficios Operativos y de Servicios`, ISCO 5):** La tasa post-hoc de repetición ocupacional sube hasta **`54.17%` (`Lift = 1.186x`)** en Ward y **`47.78%` (`Lift = 1.046x`)** en K-Means Personas (`31.85%`, `Lift = 1.063x` en Experiencias). **¿Por qué?** Porque en ocupaciones operativas, administrativas y de servicios con contratos cortos o solapados, los trabajadores rotan de empleador pero **permanecen dentro del mismo oficio estandarizado ESCO** (reincidencia horizontal).
- **En el Clúster 3 de Experiencias (`Empleos de Larga Permanencia`, `dur_q = 66.30` trimestres $\approx 16.5$ años):** La tasa de `reincide` por experiencia cae a **`23.13%` (`Lift = 0.772x`)**. **¿Por qué?** Porque quien permanece más de 16 años en un mismo puesto estable tiene pocas transiciones adicionales en su vida laboral y no acumula múltiples contratos repetidos en ese mismo oficio.

### 4.5 ¿Por qué la `Versión B` (`sin_outliers`) supera a la `Versión A` (`con_outliers`) en K-Means y Ward, manteniendo una alta concordancia (`ARI = 0.8633`)?
- En `Versión A`, existen ocupaciones con hasta **`129` competencias esenciales** (`mean_skills_essential` por persona de hasta **`99.00`**), mientras que en `Versión B` la winsorización IQR de Fase 2 acota los topes en **`47.5`** (`essential`), **`39.5`** (`competence`) y **`13.5`** (`knowledge`).
- Como K-Means y Ward minimizan **distancias euclidianas al cuadrado**, un valor extremo a $+6\sigma$ aporta $36$ veces más a la suma de cuadrados que un punto a $+1\sigma$.
- Al usar **`Versión B · SIN outliers`**, la inercia total de K-Means baja de `1,714,083.62` a **`1,692,018.38`**, el índice de Davies-Bouldin mejora de `1.6424` a **`1.6298`**, y el índice de Calinski-Harabasz sube de `44,970.04` a **`46,780.87`**, evitando un desplazamiento espurio de `0.1105` desviaciones estándar en los centroides, al tiempo que el **`ARI = 0.8633` (`NMI = 0.8437`)** en las `281,674` personas de Train confirma que la estructura de los 4 arquetipos es robusta y no un artefacto del recorte IQR.

---

## 5. Síntesis Comparativa Final: Cómo se Complementan Ambos Modelos en el Informe del Proyecto

| Dimensión | Clustering Jerárquico Aglomerativo (`8.1` · Ward) | Clustering K-Means (`8.0` · K-Means++) |
|---|---|---|
| **Muestra de ajuste directo** | Micro-muestra visual `n = 60` + Muestra de descubrimiento `n = 3,000` (proyectada vía `NearestCentroid` a `352,093` personas y `1,738,738` experiencias) | **Población completa de Train (`281,674` personas y `1,391,018` experiencias)** + validación en Test (`70,419` personas y `347,720` experiencias) |
| **Evidencia para elegir $k^*$** | Salto vertical del dendrograma Ward (`10.060` en $k=4 \to 1.431$ en $k=5$) + descarte visual/cuantitativo de `single`, `average` y `complete` | Codo de inercia (`-11.93%` en $k=4$), pico global de Calinski-Harabasz en Personas (`46,780.83`) y pico global de Silueta en Experiencias (`0.2465`) |
| **Concordancia mutua ($k^* = 4$)** | `ARI = 0.4164` / `NMI = 0.5014` (desde la muestra de Ward) | `ARI = 0.3117` / `NMI = 0.4560` (desde los centroides globales de K-Means) |
| **Aporte único al informe** | Demuestra la **taxonomía jerárquica** (cómo se funden las ramas y por qué no deben elegirse $k \ge 5$ ni otros linkages que encadenan). | Entrega la **segmentación operativa definitiva** sobre el 100% de la base con centroides exactos en escala real (`max_diff = 0.000000`). |
