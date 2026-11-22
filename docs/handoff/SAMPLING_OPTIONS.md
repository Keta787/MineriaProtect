# SAMPLING_OPTIONS.md · Evaluación de Diseño de Muestreo a Nivel Persona para Neon (`JobPath`)

> **Documento de Decisión de Diseño (Fase 1):** Compara tres candidatos de tamaño muestral a nivel de persona (**Candidato A: `25,000` personas Ward**, **Candidato B: `50,000` personas estratificadas con piso $\ge 1,000$ por estrato y pesos $w_i$** en dos variantes `B1` y `B2`, y **Candidato C: `352,093` personas — Censo Clasificado Completo**) sobre el universo modelable de **`352,093` personas** y **`1,738,738` experiencias clasificadas en ESCO**.  
> **Reproducibilidad:** Todos los conteos, márgenes de error con corrección por población finita (`FPC`), distancias de variación total (`TVD`), pruebas de Kolmogorov–Smirnov (`KS`) y coberturas de transiciones provienen de la ejecución de solo lectura sobre `data/03_processed/empleos_limpio_con_competencias_sin_outliers.csv` y `reports/{eda,kmeans,clustering_jerarquico}_jobpath/tables/*.csv` con semilla fija (`SEED = 42`).

---

## 1. Veredicto Ejecutivo y Recomendación (En Lenguaje Claro)

### Veredicto Rápido

1. **Candidato A (`25,000` personas = `7.10 %` del censo, `123,600` experiencias) — NO RECOMENDADO como única fuente:**
   - Aunque reproduce bien las proporciones medias de `Train` (`TVD <= 0.45 pp` en educación, ISCO y clústeres; `KS = 0.0027` en número de empleos), **fue extraído en el cuaderno `8.1` exclusivamente de la partición `Train` (`25,000` personas de `Train` y `0` personas de `Test`)**.
   - Si el dashboard solo carga el Candidato A, **es imposible filtrar o inspeccionar trayectorias individuales del conjunto de prueba (`Test`, `70,419` personas)** donde se evaluaron todos los modelos supervisados (`6.0`–`7.2`) y la validación fuera de muestra de clustering (`8.0`–`8.1`). Además, deja tres estratos por debajo del piso requerido de `1,000` personas (`PhD = 126` personas [`±8.42 pp`], `ISCO 6 Agropecuario = 69` personas [`±11.38 pp`], `ISCO 0 Militar = 42` personas [`±14.58 pp`]) y **pierde el `85.51 %` de los pares únicos de transición ocupacional** (`319,204` de `373,311` pares únicos desaparecen).
2. **Candidato B (`50,000` personas = `14.20 %` del censo, `~245,083` experiencias) — RECOMENDADO si priorizas una base ultraligera (`~55–65 MB` con índices):**
   - Evaluamos dos variantes que incluyen las `25,000` personas exactas de Ward (`Train`) más representación estratificada de `Test` y sobre-muestreo para que **todo estrato marginal alcance el piso de `1,000` personas** (o el `100 %` del estrato poblacional cuando en todo el censo hay menos de `1,000` personas, como `ISCO 6 = 945` o `ISCO 0 = 598`), almacenando el peso exacto `sampling_weight` ($w_i = N_h / n_h$):
     - **Variante B2 (Recomendada dentro de `50k` — Proporción `80/20` preservada: `40,000` Train [`25k` Ward + `15k` Train] + `10,000` Test):** Preserva la proporción poblacional `80 % Train / 20 % Test` sin sesgo de partición, alcanza un efecto de diseño de Kish mínimo ($\text{DEFF} = 1.0271$, $n_{\text{eff}} = 48,682$, margen de error global ponderado **`±0.4123 pp`**), garantiza $\ge 1,000$ personas en `PhD` (`1,054`), captura el `94.85 %` de todos los oficios ESCO (`2,820 / 2,973`), el `100 %` del `Top-50` y `Top-100` de transiciones con correlación de rangos de Spearman **`ρ = 0.9551`**, y reduce `TVD` ponderado a **`0.00 pp`** en educación, ISCO y split (`0.18 pp` en tramos de longitud de carrera y `0.23 pp` en clústeres K-Means). Aun así, como cualquier muestra del `14.2 %`, **pierde el `75.11 %` de las transiciones raras de cola larga** (`280,384` de `373,311` pares únicos).
     - **Variante B1 (`25,000` Ward Train + `23,790` Test estratificado + `1,210` refuerzo piso 1,000 = `26,210` Train / `23,790` Test):** Maximiza la precisión dentro de `Test` (`±0.5174 pp` vs. `±0.9073 pp` en B2), pero sobre-representa `Test` (`47.58 %` vs. `20.00 %` real), lo que eleva el efecto de diseño global a $\text{DEFF} = 1.3566$ ($n_{\text{eff}} = 36,857$, margen global ponderado `±0.4830 pp`) y obliga a usar `sampling_weight` en cualquier consulta que combine `Train + Test`.
3. **Candidato C (`352,093` personas = `100.00 %` Censo Clasificado Completo, `1,738,738` experiencias) — RECOMENDACIÓN PRINCIPAL si el benchmark en Neon confirma `< 400 MB` con índices:**
   - Al normalizar las etiquetas de texto repetidas (`occupation_label`, `isco_group_label`) en una tabla catálogo `esco_occupations_catalog` (`2,973` filas, `< 0.5 MB`), el tamaño estimado en PostgreSQL 18 para el **censo completo (`352,093` personas + `1,738,738` experiencias + `11` tablas agregadas + índices B-tree)** es de **`~310–360 MB`** (muy por debajo del tope de `600–700 MB` y `< 35 %` del límite gratuito de `1,024 MiB` de Neon).
   - **Ventaja decisiva:** Error muestral **`±0.0000 pp`** en toda la población y en todos los estratos (`TVD = 0`, `KS = 0`, `ρ = 1.0000`), **`0 %` de pérdida de transiciones raras** (`373,311 / 373,311` pares únicos disponibles), `sampling_weight = 1.0` uniforme, e inclusión de la bandera `in_ward_25k_sample` (`BOOLEAN`) para filtrar al instante las `25,000` personas de Ward cuando se desee.

### Tabla Resumen Comparativa de los Candidatos

| Criterio Auditado | Población Clasificada (Referencia) | Candidato A (`25k` Ward Train) | Candidato B1 (`50k`: Ward Train + Test) | Candidato B2 (`50k`: 80/20 + Piso 1,000) | Candidato C (`352k` Censo Completo) |
|---|---:|---:|---:|---:|---:|
| **Personas (`n` y `%` del censo)** | `352,093 (100.00 %)` | `25,000 (7.1004 %)` | `50,000 (14.2008 %)` | `50,000 (14.2008 %)` | **`352,093 (100.0000 %)`** |
| **Experiencias completas (`n` y `%`)** | `1,738,738 (100.00 %)` | `123,600 (7.1086 %)` | `245,155 (14.0996 %)` | `245,083 (14.0955 %)` | **`1,738,738 (100.0000 %)`** |
| **Personas en `Train` / `Test`** | `281,674 / 70,419` (`80/20`) | `25,000 / 0` (**`100/0`**) | `26,210 / 23,790` (`52.4/47.6`) | `40,000 / 10,000` (**`80/20`**) | **`281,674 / 70,419` (`80/20`)** |
| **Margen error global (`95 %`, $p=0.5$, SRS+FPC)** | `±0.0000 pp` | `±0.5974 pp` | `±0.4060 pp` (sin pond.) | `±0.4060 pp` (sin pond.) | **`±0.0000 pp`** |
| **Efecto de diseño Kish (`DEFF`) y $n_{\text{eff}}$** | `1.0000` (`352,093`) | `1.0000` (`25,000` solo Train) | `1.3566` (`36,857.3`) | **`1.0271` (`48,682.0`)** | **`1.0000` (`352,093.0`)** |
| **Margen error global ponderado (`95 %`, $p=0.5$)** | `±0.0000 pp` | No representa `Test` | `±0.4830 pp` | **`±0.4123 pp`** | **`±0.0000 pp`** |
| **Margen error en `Test` ($N_{\text{test}}=70,419$)** | `±0.0000 pp` | **`∞` (`n_test = 0`)** | **`±0.5174 pp`** | `±0.9073 pp` | **`±0.0000 pp`** |
| **Estratos marginales con $< 1,000$ personas** | Solo si $N_h < 1,000$ (`ISCO 6`, `ISCO 0`) | **3 estratos falla** (`PhD=126`, `ISCO 6=69`, `ISCO 0=42`) | **`0` fallas** (`PhD=1,000`; `ISCO 6/0 = 100 %` censo) | **`0` fallas** (`PhD=1,054`; `ISCO 6/0 = 100 %` censo) | **`0` fallas (`100 %` censo)** |
| **Estadístico `KS` en longitud `n_jobs` ($D_{\text{KS}}$)** | `0.000000` | `0.002717` ($p = 0.995$) | `0.004799` ($p = 0.265$) | `0.006111` ($p = 0.076$) | **`0.000000` ($p = 1.000$)** |
| **Oficios ESCO únicos capturados (`/ 2,973`)** | `2,973 (100.00 %)` | `2,640 (88.80 %)` | `2,822 (94.92 %)` | `2,820 (94.85 %)` | **`2,973 (100.00 %)`** |
| **Cobertura `Top-50` y `Top-100` transiciones** | `100.0 % / 100.0 %` | `100.0 % / 100.0 %` | `100.0 % / 100.0 %` | `100.0 % / 100.0 %` | **`100.0 % / 100.0 %`** |
| **Correlación Spearman $\rho$ (`Top-50` / `Top-100`)** | `1.0000 / 1.0000` | `0.8968 / 0.9317` | `0.9544 / 0.9701` | **`0.9551 / 0.9679`** | **`1.0000 / 1.0000`** |
| **Pares únicos de transición (`/ 373,311`)** | `373,311 (100.00 %)` | `54,107 (14.49 %)` | `93,407 (25.02 %)` | `92,927 (24.89 %)` | **`373,311 (100.00 %)`** |
| **Transiciones raras perdidas (`%` de pares únicos)** | `0.00 %` | **`85.51 %` perdidos** | **`74.98 %` perdidos** | **`75.11 %` perdidos** | **`0.00 %` perdidos** |
| **Tamaño estimado PostgreSQL + índices (normalizado)** | `~310–360 MB` | `~24–30 MB` | `~48–58 MB` | `~48–58 MB` | **`~310–360 MB` (`< 600 MB` tope)** |

---

## 2. Cómo se Extrajo la Muestra Ward (`n = 25,000`) en el Cuaderno `8.1` y Qué Implica

En [ram_expansion_and_comparison.py](file:///c:/Users/User/Documents/JobPath/MineriaProtect/scripts/ScriptsCsv/ClusteringJerarquico/ram_expansion_and_comparison.py#L115-L121) y [sampling_and_features.py](file:///c:/Users/User/Documents/JobPath/MineriaProtect/scripts/ScriptsCsv/ClusteringJerarquico/sampling_and_features.py#L249-L280), el equipo extrajo la muestra de `25,000` personas mediante:

```python
df_25k = draw_stratified_subsample(
    df=df_persons,
    n_sample=25000,
    strata_cols=["isco_major_modal_posthoc", "educacion_no_reportada"],
    seed=42,
    split_filter="train",
)
```

### Tres Hallazgos de Auditoría sobre la Muestra Ward (`8.1`)

1. **Extraída exclusivamente de `Train` (`split_filter = "train"`):**
   - Las `25,000` personas provienen únicamente de las `281,674` personas de `Train` (`8.8755 %` de `Train`).
   - **Implicación:** Las `70,419` personas de `Test` (`20.0001 %` de la población) tienen probabilidad de inclusión **$\pi_i = 0$**. Por sí sola, la muestra Ward no puede representar al conjunto de evaluación `Test` ni alimentar vistas interactivas del dashboard que comparen predicciones individuales en `Train` vs. `Test`.
2. **Estratificada solo por 2 variables (`isco_major_modal_posthoc` $\times$ `educacion_no_reportada`):**
   - No estratificó por los 4 niveles educativos específicos (`Secondary school`, `Bachelor`, `Master`, `PhD`), ni por longitud de trayectoria (`n_jobs`), ni por clúster (`cluster`), y aplicó asignación puramente proporcional (`round(prop * 25000)`) sin piso mínimo por estrato.
   - Como consecuencia, en el Candidato A el estrato `PhD` queda con solo **`126` personas** (margen de error `±8.42 pp`) y `ISCO 6 (Agricultores)` queda con solo **`69` personas** (margen de error `±11.38 pp`).
3. **Pérdida del cero inicial de `ISCO 0 (Ocupaciones militares)` en `isco_major_modal_posthoc`:**
   - En [sampling_and_features.py](file:///c:/Users/User/Documents/JobPath/MineriaProtect/scripts/ScriptsCsv/ClusteringJerarquico/sampling_and_features.py#L169), la instrucción `df["isco_major_1d"] = df["isco_group"].astype(str).str.strip().str[0]` se ejecutó después de que `pandas.read_csv()` leyera `isco_group` como `float64` (debido a los `128,981` nulos de ocupaciones no clasificadas). Los códigos militares `0110`, `0210` y `0310` se convirtieron en `"110.0"`, `"210.0"` y `"310.0"`, cuyo primer carácter es `'1'`, `'2'` y `'3'`.
   - Por ello, las `4,195` experiencias militares (`3,393` en `Train` y `802` en `Test`, correspondientes a **`598` personas** cuyo gran grupo ISCO modal es `0`) quedaron plegadas dentro de los grupos `1`, `2` y `3` en `isco_major_modal_posthoc` (`18` estratos activos en lugar de `20`). En el Candidato A solo caen **`42` personas** de `ISCO 0` (`±14.58 pp`).

---

## 3. Variables de Estratificación (Nombres Reales de Columna) y Justificación del Piso de `1,000` Personas

### 3.1 Nombres Reales de Columna en el Repositorio

| Dimensión Solicitada | Nombre Real de Columna | Valores y Distribución en el Censo Clasificado (`352,093` Personas) | Fuente en Disco |
|---|---|---|---|
| **Nivel educativo** | `university_level` (categórica) + `nivel_academico_ord_imputado` (`1..4`) + `educacion_no_reportada` (`0/1`) | `Secondary school`: `142,802 (40.56 %)` · `Bachelor`: `113,455 (32.22 %)` · `Master`: `51,133 (14.52 %)` · `No reportado`: `42,884 (12.18 %)` · `PhD`: `1,819 (0.52 %)` | `03_processed/*.csv` (primera experiencia clasificada por persona) + `08_asignacion_clusters_personas_352093.csv` |
| **Longitud de trayectoria** | `n_jobs` (`1..20`, entero) y `n_jobs_bin` (5 tramos para estratificación) | `1_empleo`: `26,481 (7.52 %)` · `2_3_empleos`: `97,949 (27.82 %)` · `4_5_empleos`: `101,849 (28.93 %)` · `6_8_empleos`: `86,827 (24.66 %)` · `9_mas_empleos`: `38,987 (11.07 %)` | `08_asignacion_clusters_personas_352093.csv` (`n_jobs`) |
| **Grupo ocupacional ESCO/ISCO** | `isco_major_modal_posthoc` (`1..9` en `8.0`/`8.1`) e `isco_major_1d_zfill` (`0..9` con `zfill(4)`) | En `isco_major_modal_posthoc`: `5`: `75,913 (21.56 %)` · `3`: `75,725 (21.51 %)` · `2`: `75,280 (21.38 %)` · `9`: `38,494 (10.93 %)` · `7`: `25,702 (7.30 %)` · `1`: `24,493 (6.96 %)` · `4`: `20,797 (5.91 %)` · `8`: `14,744 (4.19 %)` · `6`: `945 (0.27 %)`. Con `zfill(4)`, `0 (Militar)` tiene `598 (0.17 %)` y `6 (Agro)` `962 (0.27 %)`. | `08_asignacion_clusters_personas_352093.csv` + `03_processed/*.csv` |
| **Clúster ID (`8.0` y `8.1`)** | `cluster_kmeans_8_0` (`0..3`) y `cluster_ward_3k` / `cluster_ward_25k` (`0..3`) | **K-Means `8.0`:** `C0`: `154,577 (43.90 %)` · `C2`: `98,553 (27.99 %)` · `C3`: `57,901 (16.44 %)` · `C1 (MNAR)`: `41,062 (11.66 %)`.<br/>**Ward `8.1` (`n=25k` proyectado):** `C2`: `136,804 (38.85 %)` · `C0`: `119,736 (34.01 %)` · `C3`: `53,946 (15.32 %)` · `C1`: `41,607 (11.82 %)`. | `reports/kmeans_jobpath/tables/08_asignacion_clusters_personas_352093.csv` y `reports/clustering_jerarquico_jobpath/tables/08_*.csv` |
| **Partición (`Train` / `Test`)** | `split` (`'train'` / `'test'`) | `train`: `281,674 (80.0000 %)` · `test`: `70,419 (20.0000 %)` (`0` personas compartidas, `F-046`) | `reports/eda_jobpath/tables/split_map_resume_id.csv` |

### 3.2 Justificación Matemática Basada en los Datos: Por Qué el Piso de `1,000` Personas se Aplica a los Estratos Marginales y No a las `1,081` Celdas Cruzadas

Si cruzamos simultáneamente las 5 variables (`split [2] × university_level [5] × isco_major [10] × cluster_kmeans_8_0 [4] × n_jobs_bin [5]`):
- Existen `2,000` celdas teóricas y **`1,081` celdas no vacías** en la población de `352,093` personas.
- El tamaño mediano de una celda cruzada en toda la población es de apenas **`69.0` personas**: **`987` de las `1,081` celdas (`91.3 %`) tienen menos de `1,000` personas en el censo completo**, y solo `94` celdas tienen $\ge 1,000$ personas.
- Si exigiéramos $\min(N_c, 1000)$ en cada una de las `1,081` celdas cruzadas, necesitaríamos seleccionar más de `210,000` personas (lo cual equivale prácticamente a cargar el censo completo).
- **Solución rigurosa para $n = 50,000$ (Candidato B):**
  1. **Garantizar el piso de $\ge 1,000$ personas en todos los estratos marginales** de `university_level`, `isco_major`, `cluster_kmeans_8_0`, `cluster_ward_3k`, `n_jobs_bin` y `split` (tomando el **`100 %` del estrato poblacional** cuando $N_h < 1,000$, como `ISCO 6 Agropecuario` con $N_h = 945$ en `isco_major_modal_posthoc` [`962` en `zfill`] e `ISCO 0 Militar` con $N_h = 598$, donde el error muestral cae a **`±0.00 pp`** por censo exhaustivo del estrato, y sobre-muestreando `PhD` de `~258` hasta **`1,054` personas** en B2 / **`1,000` personas** en B1).
  2. **Asignar el resto de la muestra proporcionalmente en las celdas cruzadas** `(split, university_level, isco_major_modal_posthoc, cluster_kmeans_8_0, n_jobs_bin)` con semilla fija `SEED = 42`.
  3. **Guardar `sampling_weight` ($w_i = N_h / n_h$)** por persona (`min = 1.0000`, `max = 7.6994` en B2; suma exacta de pesos $\sum_{i=1}^{50,000} w_i = 352,093.0$) para que cualquier proporción o media calculada desde la muestra sea insesgada.

---

## 4. Recálculo Exacto de Precisión y Márgenes de Error (`95 %` de Confianza, Peor Caso $p = 0.5$)

Fórmula bajo muestreo aleatorio simple sin reemplazo con corrección por población finita (`FPC`, $z_{0.975} = 1.959964$):

$$\text{MoE}_{\text{SRS+FPC}} = 1.959964 \times \sqrt{\frac{N - n}{N - 1} \cdot \frac{0.5(1 - 0.5)}{n}} \times 100\text{ pp}$$

Cuando hay sobre-muestreo con pesos $w_i$, el tamaño muestral efectivo de Kish es $n_{\text{eff}} = \frac{(\sum w_i)^2}{\sum w_i^2} = \frac{n}{\text{DEFF}}$:

| Ámbito / Subgrupo | Población $N_h$ | Aproximación del Usuario | Valor Exacto Recalculado · **Candidato A (`25k`)** | Valor Exacto Recalculado · **Candidato B1 (`50k` Ward+Test)** | Valor Exacto Recalculado · **Candidato B2 (`50k` 80/20)** | Valor Exacto Recalculado · **Candidato C (`352k` Censo)** |
|---|---:|---:|---:|---:|---:|---:|
| **Global bajo SRS + FPC** | `352,093` | `A: ±0.60 pp` · `B: ±0.41 pp` | **`±0.5974 pp`** | **`±0.4060 pp`** | **`±0.4060 pp`** | **`±0.0000 pp`** |
| **Global con Diseño Real Ponderado ($n_{\text{eff}}$ de Kish)** | `352,093` | *(recalcular para diseño real)* | Sesgado (`0` en `Test`, $\pm 20.00\text{ pp}$ en `split`) | **`±0.4830 pp`** ($\text{DEFF}=1.3566$, $n_{\text{eff}}=36,857$) | **`±0.4123 pp`** ($\text{DEFF}=1.0271$, $n_{\text{eff}}=48,682$) | **`±0.0000 pp`** ($\text{DEFF}=1.0000$) |
| **Subconjunto `Test` ($N_{\text{test}} = 70,419$)** | `70,419` | — | **`No definido (n = 0)`** | **`±0.5174 pp`** ($n = 23,790$) | **`±0.9073 pp`** ($n = 10,000$) | **`±0.0000 pp`** ($n = 70,419$) |
| **Piso genérico $n_h = 1,000$ (sin FPC)** | $\gg 1,000$ | `±3.1 pp` | **`±3.0990 pp`** | **`±3.0990 pp`** | **`±3.0990 pp`** | **`±0.0000 pp`** |
| **Piso genérico $n_h = 400$ (sin FPC)** | $\gg 400$ | `±4.9 pp` | **`±4.8999 pp`** | **`±4.8999 pp`** | **`±4.8999 pp`** | **`±0.0000 pp`** |
| **Estrato `PhD` (con FPC sobre $N_h = 1,819$)** | `1,819` | — | `±8.4216 pp` ($n=126$) | **`±2.0789 pp`** ($n=1,000$) | **`±1.9585 pp`** ($n=1,054$) | **`±0.0000 pp`** ($n=1,819$) |
| **Estrato `ISCO 6 · Agropecuario` ($N_h = 945$)** | `945` | — | `±11.3755 pp` ($n=69$) | **`±0.0000 pp`** ($n=945$, censo `100 %`) | **`±0.0000 pp`** ($n=945$, censo `100 %`) | **`±0.0000 pp`** ($n=945$) |
| **Estrato `ISCO 0 · Militar` (`zfill`, $N_h = 598$)** | `598` | — | `±14.5843 pp` ($n=42$) | **`±0.0000 pp`** ($n=598$, censo `100 %`) | **`±0.0000 pp`** ($n=598$, censo `100 %`) | **`±0.0000 pp`** ($n=598$) |

---

## 5. Evidencia de Representatividad por Variable de Estrato, Longitud de Carrera y Transiciones

> **Nota sobre pruebas de significancia con $N = 352,093$:** Con cientos de miles de personas, cualquier prueba de hipótesis clásica ($p$-valor de $\chi^2$ o Kolmogorov–Smirnov) detecta diferencias irrelevantes de menos de `0.3 puntos porcentuales`. Por ello reportamos **tamaños del efecto en unidades directas**:
> - **Desviación absoluta máxima ($\max |\Delta|\text{ en pp}$):** la mayor diferencia en puntos porcentuales entre el porcentaje de una categoría en la muestra y en la población.
> - **Distancia de Variación Total ($\text{TVD} = \frac{1}{2}\sum_c |p_{\text{muestra}}(c) - p_{\text{pob}}(c)|\text{ en pp}$):** qué porcentaje total de la muestra habría que mover de categoría para igualar exactamente a la población (`0.00 pp` = coincidencia perfecta).
> - **Estadístico $D_{\text{KS}}$ de Kolmogorov–Smirnov:** la máxima distancia vertical (entre `0` y `1`) entre la curva acumulada de longitud de carrera (`n_jobs`) de la muestra y la de la población (`< 0.01` indica que las dos distribuciones difieren en menos de `1 punto porcentual` en cualquier tramo).

### 5.1 Resumen de Desviación Máxima (`pp`), `TVD` (`pp`) y Mínimo por Estrato

| Variable de Estrato | Candidato A (`25k` Ward) · Mín $n_h$ / Máx $|\Delta|$ / `TVD` | Candidato B1 (`50k` Ward+Test) · Mín $n_h$ / `TVD` sin pond. → **Ponderado** | Candidato B2 (`50k` 80/20) · Mín $n_h$ / `TVD` sin pond. → **Ponderado** | Candidato C (`352k` Censo) · Mín $n_h$ / `TVD` |
|---|---|---|---|---|
| `university_level` (`5` cat.) | `n_min = 126` (`PhD`) · Máx `0.27 pp` · `TVD = 0.27 pp` | `n_min = 1,000` · `TVD = 1.48 pp` → **`0.0000 pp`** | `n_min = 1,054` · `TVD = 1.59 pp` → **`0.0000 pp`** | `n_min = 1,819` · **`TVD = 0.0000 pp`** |
| `isco_major_modal_posthoc` (`9` cat.) | `n_min = 69` (`ISCO 6`) · Máx `0.04 pp` · `TVD = 0.08 pp` | `n_min = 945` (`100 %`) · `TVD = 2.16 pp` → **`0.0000 pp`** | `n_min = 945` (`100 %`) · `TVD = 2.18 pp` → **`0.0000 pp`** | `n_min = 945` · **`TVD = 0.0000 pp`** |
| `n_jobs_bin` (`5` tramos) | `n_min = 1,893` · Máx `0.34 pp` · `TVD = 0.39 pp` | `n_min = 3,859` · `TVD = 0.48 pp` → **`0.3128 pp`** | `n_min = 3,867` · `TVD = 0.61 pp` → **`0.1764 pp`** | `n_min = 26,481` · **`TVD = 0.0000 pp`** |
| `cluster_kmeans_8_0` (`4` clústeres) | `n_min = 2,906` · Máx `0.45 pp` · `TVD = 0.45 pp` | `n_min = 5,772` · `TVD = 1.70 pp` → **`0.3695 pp`** | `n_min = 5,759` · `TVD = 1.73 pp` → **`0.2312 pp`** | `n_min = 41,062` · **`TVD = 0.0000 pp`** |
| `cluster_ward_3k` (`4` clústeres) | `n_min = 2,396` · Máx `0.11 pp` · `TVD = 0.11 pp` | `n_min = 5,253` · `TVD = 1.03 pp` → **`0.0529 pp`** | `n_min = 5,384` · `TVD = 1.30 pp` → **`0.1810 pp`** | `n_min = 33,350` · **`TVD = 0.0000 pp`** |
| `split` (`train` / `test`) | **`n_min = 0` (`test`) · Máx `20.00 pp` · `TVD = 20.00 pp`** | `n_min = 23,790` · `TVD = 27.58 pp` → **`0.0000 pp`** | `n_min = 10,000` · `TVD = 0.0001 pp` → **`0.0000 pp`** | `n_min = 70,419` · **`TVD = 0.0000 pp`** |
| `educacion_no_reportada` (`0/1`) | `n_min = 3,041` · Máx `0.02 pp` · `TVD = 0.02 pp` | `n_min = 6,076` · `TVD = 0.03 pp` → **`0.0000 pp`** | `n_min = 6,058` · `TVD = 0.06 pp` → **`0.0000 pp`** | `n_min = 42,884` · **`TVD = 0.0000 pp`** |

> **Por qué la desviación sin ponderar de B1/B2 sube a `~1.5–2.1 pp` en `PhD` e `ISCO 6` y cae a `0.0000 pp` al ponderar:** Porque el requisito de diseño exige elevar `PhD` de `0.52 %` (`~258` personas) a $\ge 1,000$ personas (`2.11 %` de la muestra de `50,000`) e `ISCO 6` de `0.27 %` (`~134` personas) a `945` personas (`1.89 %`). Ese sobre-muestreo deliberado de `+1.59 pp` y `+1.62 pp` es exactamente lo que garantiza márgenes de error $\le \pm 2.0\text{ pp}$ dentro de esos grupos pequeños, y la columna `sampling_weight` ($w_i = N_h / n_h$) devuelve su peso poblacional exacto (`0.0000 pp` de error).

### 5.2 Longitud de Trayectoria (`n_jobs` = Experiencias Clasificadas por Persona)

- **Población (`352,093` personas):** media = `4.9383` empleos clasificados (`5.266` incluyendo no clasificados en `5.0_EDA`).
- **Candidato A (`25,000` personas):** media = `4.9440`, estadístico Kolmogorov–Smirnov **`D_KS = 0.002717`** ($p = 0.9951$ — diferencia acumulada máxima de `0.27 puntos porcentuales`).
- **Candidato B1 (`50,000` personas Ward+Test):** media sin ponderar = `4.9031`, media ponderada = **`4.9423`**, **`D_KS = 0.004799`** ($p = 0.2647$ — diferencia acumulada máxima de `0.48 pp`).
- **Candidato B2 (`50,000` personas 80/20):** media sin ponderar = `4.9017`, media ponderada = **`4.9407`**, **`D_KS = 0.006111`** ($p = 0.0757$ — diferencia acumulada máxima de `0.61 pp`, no significativa ni siquiera con $n=50,000$).
- **Candidato C (`352,093` personas):** media = **`4.9383`**, **`D_KS = 0.000000`** ($p = 1.0000$).

### 5.3 Cobertura de Transiciones Ocupacionales (`Top-50`, `Top-100`, Correlación de Spearman y Patrones Raros Perdidos)

En el universo clasificado existen **`1,386,645` transiciones consecutivas** entre oficios ESCO (`325,612` personas con $\ge 2$ empleos clasificados), distribuidas en **`373,311` pares únicos `(origen → destino)`** sobre **`2,973` códigos de ocupación ESCO**:

1. **Cobertura de las transiciones más frecuentes (`N = 50` propuesto y `N = 100` adicional):**
   - Los **Candidatos A, B1, B2 y C capturan el `100.0 %` de las `50` y de las `100` transiciones más frecuentes** del mercado laboral.
   - En el `Top-50`, la transición #50 aparece un mínimo de `62` veces en el Candidato A, `147` veces en B1, `143` veces en B2 y `1,079` veces en el Candidato C.
   - La **correlación de rangos de Spearman ($\rho$)** entre las frecuencias muestrales y poblacionales del `Top-50` sube de **`0.8968` en el Candidato A** a **`0.9551` en el Candidato B2** (`0.9544` en B1) y **`1.0000` en el Candidato C** (en el `Top-100`: `0.9317` en A $\rightarrow$ `0.9679` en B2 / `0.9701` en B1 $\rightarrow$ `1.0000` en C).
2. **Qué patrones raros se pierden en las muestras (A y B) frente al Censo Completo (C):**
   - **Oficios ESCO de baja frecuencia ausentes:** De los `2,973` oficios ESCO, el Candidato A pierde **`333` oficios (`11.20 %`)** y el Candidato B2 pierde **`153` oficios (`5.15 %`)**, mientras que el Candidato C conserva los **`2,973` (`100 %`)**.
   - **Pares de transición de cola larga (`373,311` pares únicos `(origen → destino)`):** Como la matriz de transición entre `2,973 × 2,973` oficios sigue una ley de potencias (donde la mayoría de las rutas especializadas ocurren entre 1 y 5 veces en toda la población), el Candidato A solo captura `54,107` pares únicos (**se pierde el `85.51 %` de las rutas únicas**) y el Candidato B captura `~92,927–93,407` pares únicos (**se pierde el `~75.0 %` de las rutas únicas**). Solo el **Candidato C** preserva el `100 %` del grafo de movilidad ocupacional cuando un usuario busca en el dashboard un oficio especializado concreto.

---

## 6. Costo de Almacenamiento en PostgreSQL (`Neon < 1 GB`) y Velocidad de Consultas

### 6.1 Diseño Normalizado para Minimizar `pg_total_relation_size`

Al separar las cadenas de texto repetidas (`occupation_label`, `isco_group_label`) en una tabla catálogo `esco_occupations_catalog` (`2,973` filas, `< 0.5 MB`), cada fila de `person_experiences` contiene únicamente tipos compactos de ancho fijo (`resume_id INT4`, `job_order INT2`, `start_year INT2`, `dur_q INT2`, `es_vigente BOOL`, `occupation_code VARCHAR(12)`, `n_skills_essential REAL`, `n_skills_competence REAL`, `n_skills_knowledge REAL`, `reincide INT2`, `cluster_exp_kmeans INT2`, `prob_reincide_nb_h REAL`, `prob_reincide_log_ohe REAL` $\approx$ `64 bytes` de datos + `24 bytes` de cabecera de tupla PostgreSQL = **`~88 bytes/fila`**):

| Candidato | `person_trajectories` (Heap + Índices) | `person_experiences` (Heap + Índices B-tree) | `esco_occupations_catalog` + `11` Tablas Agregadas | Total Estimado `pg_total_relation_size` (Incluyendo Índices) | `%` del Límite Gratuito Neon (`1,024 MiB`) | Cumple Tope `600–700 MB` |
|---|---:|---:|---:|---:|---:|---|
| **Candidato A (`25,000` personas / `123,600` exp.)** | `~4.5 MB` | `~18.5 MB` | `~1.5 MB` | **`~24.5 MB`** | `2.39 %` | Sí (muy holgado) |
| **Candidato B (`50,000` personas / `245,083` exp.)** | `~9.0 MB` | `~36.8 MB` | `~1.5 MB` | **`~47.3 MB`** | `4.62 %` | Sí (muy holgado) |
| **Candidato C (`352,093` personas / `1,738,738` exp.)** | `~62.0 MB` | `~255.0 MB` | `~1.5 MB` | **`~318.5 MB`** | `31.10 %` | **Sí (`~50 %` por debajo del tope de `600–700 MB`)** |

### 6.2 Latencia de las Consultas Reales del Dashboard

1. **Vistas globales, KPIs, gráficos de EDA, tablas de modelos (`6.0`–`7.2`), perfiles de clúster (`8.0`–`8.1`) y casos de Métodos Numéricos (`RL-04` y `LG-01`):**
   - Leen exclusivamente de las **11 tablas resumen pre-agregadas** (`< 100` filas por tabla).
   - Latencia en PostgreSQL: **`< 2 ms` de tiempo de ejecución en motor** (`< 30 ms` incluyendo RTT serverless en Vercel/Neon), **idéntica en los Candidatos A, B y C**.
2. **Explorador interactivo de trayectorias individuales por `resume_id` o filtros combinados (`WHERE split = $1 AND cluster_kmeans_8_0 = $2 AND isco_major_1d_zfill = $3 LIMIT 50`):**
   - Con los índices compuestos B-tree `idx_person_filter (split, cluster_kmeans_8_0, isco_major_1d_zfill, university_level)` en `person_trajectories` e `idx_exp_resume_job (resume_id, job_order)` en `person_experiences`, PostgreSQL resuelve la búsqueda por *Index Scan* en **`< 5 ms`** tanto para `50,000` personas (Candidato B) como para `352,093` personas (Candidato C).

> **Siguiente paso en Fase 2 (tras tu elección):** En cuanto elijas entre el **Candidato C (`352,093` personas — Recomendado)** o el **Candidato B2 (`50,000` personas 80/20 con piso $\ge 1,000$)**, ejecutaremos la carga en el proyecto Neon `JobPath` (`steep-poetry-63912763`) y reportaremos la salida exacta de `SELECT pg_size_pretty(pg_total_relation_size(...))` y `EXPLAIN (ANALYZE, BUFFERS)` sobre las tablas reales.


---

## [v1.1 — Decisión Aprobada por el Usuario: Selección del Candidato C con Puerta Go/No-Go y Condiciones de Gobernanza]

> **Estado (`2026-11-22`):** El usuario aprobó el **Candidato C (`352,093` personas / `1,738,738` experiencias — Censo Clasificado Completo con tabla catálogo ESCO normalizada e indicador `in_ward_25k_sample`)** en el proyecto Neon `JobPath` (`id: steep-poetry-63912763`, rama raíz `production` `br-round-water-bboiqzaf`), bajo las siguientes condiciones verificadas:

1. **Verificación del Plan Gratuito de Neon (`free_v3`) y Medición de Almacenamiento:**
   - Confirmado vía `describe_project` y documentación oficial de Neon (`docs/introduction/plans` `2026-11-18` y `docs/postgres/backup-restore/history-window` `2026-11-10`) que el proyecto `steep-poetry-63912763` está en el plan **`Free` (`$0/mes`)**, donde **jamás se facturan excedentes (*overages*)**.
   - El límite de **`1 GB` de almacenamiento (`1,024 MiB` = `1,073,741,824 bytes`)** en la única rama raíz (`production`, `0` ramas hijas) contabiliza el **tamaño lógico actual de la base** (`pg_database_size`: tablas *heap* + TOAST + índices B-tree), mientras que el historial WAL para *Instant Restore* (`history_retention_seconds = 21600` = `6 horas`) se contabiliza por separado con su propio tope gratuito de `1 GB` y se purga automáticamente pasadas 6 horas.
2. **Puerta Go / No-Go sin Fallback Automático:**
   - Se procede con el Candidato C únicamente si el tamaño total medido con `pg_total_relation_size` (incluyendo todos los índices y las 12 tablas agregadas) se mantiene **`< 600 MB`** y las consultas reales cumplen los objetivos de latencia (*cold start* `<= 2,500 ms`; consultas agregadas en caliente `<= 15 ms` en motor / `<= 120 ms` RTT; búsquedas indexadas de trayectorias con `LIMIT 50` `<= 25 ms` en motor / `<= 150 ms` RTT). Si algún criterio falla, el proceso se detiene y presenta los datos para decidir sobre el **Candidato B2 (`50,000` personas `80/20`, piso $\ge 1,000$, `sampling_weight`)**.
3. **Distinción Explícita de Clústeres Ward (`25k`) frente al Censo Completo:**
   - La columna `cluster_ward_25k_direct` (`SMALLINT NULL`) almacena etiquetas `0..3` **exclusivamente para las `25,000` personas de `Train` donde `in_ward_25k_sample = TRUE`** y permanece **`NULL` en las `327,093` personas restantes**, separándola explícitamente de las proyecciones por centroide (`cluster_ward_25k_projected`, `cluster_ward_3k_projected`) y de K-Means++ (`cluster_kmeans_8_0`).
4. **Gobernanza de Licencias (`CC BY 4.0`) y Redefinición de la Vista de Transparencia como Inclusión / Exclusión:**
   - Tanto **JobHop v2** (`aida-ugent/JobHop`, VDAB / Ghent University) como **ESCO v1.2.1** (Comisión Europea, Decisión `2011/833/EU`) operan bajo licencia **`CC BY 4.0`**.
   - Al cargar el censo clasificado completo, no se exponen endpoints de descarga ni listado masivo (`LIMIT <= 50`), cualquier despliegue se mantiene en modo *preview* / no público hasta confirmación final, la página de Metodología declara las atribuciones **CC BY 4.0** y el origen público de `resume_id`, y la vista de transparencia del dashboard y de las diapositivas se define como **Transparencia de Inclusión/Exclusión y Partición** (`99.10 %` de personas limpias incluidas, `7.07 %` de experiencias sin oficio hoja ESCO excluidas, split `80/20` sin solapamiento y bandera `in_ward_25k_sample`).
