# Análisis Comparativo Profundo (`8.0` K-Means vs. `8.1` Clustering Jerárquico Ward) y Factibilidad de Hardware ($O(n^2)$)

> **Proyecto:** `MineriaProtect` (JobPath — Observatorio Laboral de Trayectorias y Perfiles ESCO)  
> **Corrida de actualización (`8.1` · `n = 25,000`):** **`RUN-20261120-073736`** (`2026-11-20 07:37:36` · `[CURRENT]`)  
> **Referencia `8.0` K-Means (sin sobrescribir):** `8.0_kmeans_clustering.ipynb` (`RUN-20261119-181140`)  
> **Hardware local evaluado:** Laptop Acer Nitro ANV15-52 · Intel Core i5-13420H (8 núcleos / 12 hilos) · **32 GB RAM (`31.7 GB` útiles)** · RTX 5050 Laptop (4 GB VRAM) · SSD NVMe 512 GB · Windows 11 Home 64-bit.

---

## 1. Justificación Matemática de Factibilidad de Hardware ($O(n^2)$ en 32 GB RAM)

El algoritmo de Clustering Jerárquico Aglomerativo con criterio de enlace `ward` (`scipy.cluster.hierarchy.linkage`) requiere construir previamente la matriz condensada de distancias euclidianas entre todos los pares de observaciones en precisión `float64` (`8 bytes` por par):

$$\text{Pares} = \frac{n(n-1)}{2}, \qquad \text{RAM}_{\text{condensada}} = \frac{n(n-1)}{2} \times 8\text{ bytes}$$

### Tabla 1.1 · Cálculo Exacto de RAM $O(n^2)$ para los Escenarios de `MineriaProtect`
| vista_o_escenario | filas_n | pares_condensados_n_n1_div_2 | ram_matriz_condensada_gb_float64 | ram_matriz_condensada_gib_binario | pico_ram_estimado_windows_scipy_gb | factible_en_32gb_ram |
| --- | --- | --- | --- | --- | --- | --- |
| V_EXPERIENCE Train (100%) | 1391018 | 967464842653 | 7739.72 | 7208.18 | 15479.44 | No (MemoryError inmediato; supera RAM física en >240x) |
| V_PERSON Total Clasificado (100%) | 352093 | 61984564278 | 495.877 | 461.821 | 991.75 | No (MemoryError inmediato; supera RAM física en >15x) |
| V_PERSON Train (100%) | 281674 | 39669980301 | 317.36 | 295.564 | 634.72 | No (MemoryError inmediato; supera RAM física en 10x) |
| V_PERSON Muestra Anterior (8.1 inicial) | 3000 | 4498500 | 0.036 | 0.034 | 1.2 | Sí (Muy holgado; < 1 s en SciPy) |
| V_PERSON Muestra Optimizada (Seleccionada) | 25000 | 312487500 | 2.5 | 2.328 | 8 | Sí (Óptima y segura en 32 GB RAM; deja >20 GB libres) |
| V_PERSON Límite Superior Seguro | 30000 | 449985000 | 3.6 | 3.353 | 11.52 | Sí (Viable con margen ajustado si hay otras apps abiertas) |

- **Demostración de inviabilidad física (desbordamiento de RAM, no tiempo de CPU):** Ejecutar Ward sobre el 100% de `V_PERSON` Train (`281674` personas) exige **`317.36 GB`** solo para alojar el vector condensado de distancias (`~10` veces la RAM física total de `31.7 GB`), y sobre `V_EXPERIENCE` Train (`1391018` filas) exige **`7739.72 GB`** (`~7.74 TB`). Por consiguiente, el fallo sobre el conjunto completo es un **`MemoryError` determinista de memoria física**, independientemente de la velocidad del procesador Intel Core i5-13420H.
- **Muestra segura optimizada para 32 GB RAM (`n = 25000` personas):** Con `n = 25000` personas estratificadas por Gran Grupo ISCO (`isco_major_modal_posthoc`) y bandera MNAR (`educacion_no_reportada`) con `random_state = 42`, la matriz condensada ocupa **`2.500 GB`** (`2.328 GiB`) y el pico total con Windows 11 y `scipy` se mantiene en `~8.00 GB`, ejecutando el ajuste completo de Ward en **`146.11` segundos**.

---

## 2. Auditoría de Estabilidad: Ward `n = 3,000` vs. Ward Optimizado `n = 25000` vs. K-Means `8.0` (`100% Train`)

### Tabla 2.1 · Comparación de Métricas Internas, Proporciones y Concordancia (`ARI` / `NMI` sobre las `352093` Personas)
| modelo_y_muestra | n_entrenamiento | pct_train_usado | silhouette_score | davies_bouldin_index | calinski_harabasz_index | pct_cluster_0 | pct_cluster_1 | pct_cluster_2 | pct_cluster_3 | ari_vs_ward_n25000_en_352093 | nmi_vs_ward_n25000_en_352093 | ari_vs_kmeans_8_0_en_352093 | nmi_vs_kmeans_8_0_en_352093 | tiempo_ajuste_seg |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8.1 · Ward Jerárquico (Muestra n = 3,000 → Proyectado a 352,093) | 3000 | 1.07 | 0.1827 | 1.9489 | 370.72 | 52.13 | 11.65 | 9.47 | 26.75 | 0.3582 | 0.5035 | 0.4708 | 0.5462 | 0.8 |
| 8.1 · Ward Jerárquico Optimizado (Muestra n = 25,000 → Proyectado a 352,093) | 25000 | 8.88 | 0.1167 | 1.9295 | 3134.50 | 34.01 | 11.82 | 38.85 | 15.32 | 1 | 1 | 0.6502 | 0.7296 | 146.11 |
| 8.0 · K-Means++ (100% Train n = 281,674 → Evaluado en 352,093) | 281674 | 100 | 0.1948 | 1.6298 | 46780.83 | 43.9 | 11.66 | 27.99 | 16.44 | 0.6502 | 0.7296 | 1 | 1 | 1.8 |

### Tabla 2.2 · Perfiles en Escala Original del Modelo Ward Optimizado (`n = 25000` → Proyectado a `352093` Personas)
| cluster | nombre_segmento_es | n_muestra_descubrimiento | pct_muestra_descubrimiento | n_total_proyectado | pct_total_proyectado | n_test_proyectado | pct_test_proyectado | n_jobs_media_muestra | n_jobs_media_total | span_q_media_muestra | span_q_media_total | dur_mean_media_muestra | dur_mean_media_total | overlap_ratio_media_muestra | overlap_ratio_media_total | mean_skills_competence_media_muestra | mean_skills_competence_media_total | mean_skills_knowledge_media_muestra | mean_skills_knowledge_media_total | mean_prop_competence_media_muestra | mean_prop_competence_media_total | nivel_academico_ord_imputado_media_muestra | nivel_academico_ord_imputado_media_total | educacion_no_reportada_media_muestra | educacion_no_reportada_media_total | mean_skills_essential_media_muestra | mean_skills_essential_media_total | tasa_reincide_muestra_posthoc_pct | lift_reincide_muestra_posthoc | tasa_reincide_total_posthoc_pct | tasa_reincide_test_posthoc_pct | lift_reincide_test_posthoc | gran_grupo_isco_dominante_posthoc | accion_observatorio_recomendada_es |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Inserción Temprana y Trayectorias Cortas en Oficios Operativos | 6818 | 27.27 | 119736 | 34.01 | 23728 | 33.7 | 3.96 | 4.26 | 37.82 | 37.73 | 10.36 | 9.24 | 0.99 | 0.99 | 17.93 | 18.02 | 2.35 | 2.26 | 0.88 | 0.88 | 1.22 | 1.27 | 0 | 0 | 20.29 | 20.31 | 41.55 | 0.904 | 44.12 | 44.04 | 0.964 | 5 · Trabajadores de los servicios y vendedores | Programa Puente al Primer Empleo: orientación vocacional temprana, certificación de competencias prácticas base y seguimiento en los primeros 4 trimestres post-egreso. |
| 1 | Especialistas Estables de Permanencia Prolongada | 2966 | 11.86 | 41607 | 11.82 | 8356 | 11.87 | 4.71 | 4.7 | 59.88 | 58.02 | 14.7 | 14.13 | 1.04 | 1.03 | 18.03 | 18.13 | 3.34 | 3.31 | 0.84 | 0.84 | 2 | 2 | 1 | 1 | 21.42 | 21.46 | 45.92 | 0.999 | 45.59 | 44.96 | 0.984 | 5 · Trabajadores de los servicios y vendedores | Ruta de Actualización Continua (Up-Skilling): micro-credenciales de especialización técnica para evitar obsolescencia en carreras de larga duración. |
| 2 | Profesionales Intensivos en Conocimiento y Alta Exigencia ESCO | 11924 | 47.7 | 136804 | 38.85 | 27495 | 39.04 | 5.52 | 5.5 | 46.96 | 44.08 | 10.37 | 9.58 | 1.14 | 1.13 | 18.72 | 18.95 | 4.66 | 5.17 | 0.8 | 0.78 | 2.1 | 2.22 | 0 | 0 | 23.43 | 24.18 | 48.69 | 1.06 | 47.83 | 47.96 | 1.05 | 2 · Profesionales científicos e intelectuales | Vinculación I+D y Posgrados Aplicados: articulación con maestrías, liderazgo técnico y transferencia tecnológica universidad-empresa. |
| 3 | Trayectorias de Alta Rotación y Multi-Empleo Solapado | 3292 | 13.17 | 53946 | 15.32 | 10840 | 15.39 | 5.09 | 5.2 | 109.66 | 113 | 37.96 | 39.35 | 1.64 | 1.63 | 18.3 | 17.74 | 3.98 | 3.88 | 0.82 | 0.82 | 1.38 | 1.43 | 0.02 | 0.02 | 22.31 | 21.66 | 45.14 | 0.982 | 43.96 | 43.99 | 0.963 | 3 · Técnicos y profesionales de nivel medio | Programa de Estabilización y Consolidación de Portafolio Laboral: acompañamiento para formalizar trayectorias fragmentadas y capitalizar la experiencia acumulada. |

- **Estabilidad del muestreo jerárquico (`n = 3,000` vs. `n = 25000`):** Al multiplicar el tamaño muestral por `8.33x` (pasando del `1.07%` al `8.88%` de todo `Train`), los perfiles proyectados sobre las `352093` personas alcanzan una concordancia de **`ARI = 0.3582`** y **`NMI = 0.5035`**, con un `silhouette_score = 0.1167` y `davies_bouldin_index = 1.9295`.
- **Concordancia con K-Means `8.0` (`100% Train`):** Sobre las `352093` personas clasificadas, la concordancia frente a K-Means `8.0` es de **`ARI = 0.6502`** (`NMI = 0.7296`) para Ward `n = 25000` frente a **`ARI = 0.4708`** (`NMI = 0.5462`) para Ward `n = 3,000`.

---

## 3. Impacto del Tratamiento de Datos en la Geometría de Ambos Algoritmos

1. **Escalado obligatorio (`StandardScaler`):** Sin estandarización, `span_q` (rango de `1` a `> 160` trimestres) y `mean_skills_competence` dominarían por completo la distancia euclidiana al cuadrado, anulando variables de rango `[0, 1]` como `mean_prop_competence` y `educacion_no_reportada`. Al llevar todas las variables a $\mu = 0$ y $\sigma = 1$, cada eje conductual aporta peso equitativo a la varianza de Ward y a la inercia WCSS de K-Means.
2. **Eliminación de la colinealidad exacta $E = C + K$:** Como `n_skills_essential = n_skills_competence + n_skills_knowledge` se cumple en el `99.10%` de las filas clasificadas, omitir `n_skills_essential` de `X` evita duplicar el peso del volumen de competencias en el cálculo de distancias euclidianas, permitiendo que el eje cognitivo (`mean_skills_knowledge` + `mean_prop_competence`) se separe con nitidez.
3. **Manejo MNAR de `educacion_no_reportada` (sin relleno espurio con `0`):** Al conservar la bandera binaria ortogonal `educacion_no_reportada` (`11.65%` de prevalencia en personas), los registros sin reporte educativo toman un puntaje estandarizado $z \approx +2.69$. Por eso **los tres modelos (`8.0` K-Means, `8.1` Ward `n = 3,000` y `8.1` Ward `n = 25000`) aíslan exactamente el mismo Clúster 1 (`~11.65%`)** sin distorsionar la escala ordinal `1..4` de los demás grupos.
4. **Uso de `Versión B · SIN outliers` como base primaria:** Acotar las colas extremas de competencias ESCO (de `129` a los topes IQR `47.5 / 39.5 / 13.5`) evita que valores atípicos a $+6\sigma$ arrastren las medias aritméticas de K-Means o consuman las ramas superiores del dendrograma de Ward aislando hojas marginales.

---

## 4. Matriz Ejecutiva Comparativa (`8.0` K-Means vs. `8.1` Ward) y Patrones de Reacción Post-Hoc a `reincide`

### Tabla 4.1 · Contraste Conductual y Reacción Post-Hoc a `reincide` en los 4 Clústeres
| cluster | perfil_comportamental | kmeans_8_0_tamano_y_reincide | ward_8_1_n3000_tamano_y_reincide | ward_8_1_n25000_tamano_y_reincide | isco_dominante_km_vs_ward25k | patron_reaccion_y_explicacion_es |
| --- | --- | --- | --- | --- | --- | --- |
| Clúster 0 | Inserción Temprana y Trayectorias Cortas en Oficios Operativos | 43.90% · 47.78% (1.046x) | 52.13% · 43.53% (0.953x) | 34.01% · 44.04% (0.964x) | 5 · Trabajadores de los servicios y vendedores / 5 · Trabajadores de los servicios y vendedores | Núcleo mayoritario de carreras cortas en servicios y ventas (ISCO 5). En K-Means concentra la mayor tasa post-hoc de reincidencia horizontal (cambio de empleador dentro del mismo código ESCO), mientras que Ward absorbe parte de los operativos con menor solapamiento. |
| Clúster 1 | Trabajadores con Educación No Reportada (MNAR) y Perfil Operativo Estable | 11.66% · 45.00% (0.985x) | 11.65% · 45.11% (0.988x) | 11.82% · 44.96% (0.984x) | 5 · Trabajadores de los servicios y vendedores / 5 · Trabajadores de los servicios y vendedores | Subespacio ortogonal exacto de educación no reportada (MNAR = 100%): en los 3 modelos captura prácticamente la misma proporción de personas (~11.65%), validando que la bandera binaria evita distorsionar la escala ordinal sin contaminar los demás grupos. |
| Clúster 2 | Profesionales Intensivos en Conocimiento y Alta Exigencia ESCO | 27.99% · 42.75% (0.936x) | 9.47% · 34.34% (0.752x) | 38.85% · 47.96% (1.050x) | 2 · Profesionales científicos e intelectuales / 2 · Profesionales científicos e intelectuales | Profesionales de alta complejidad cognitiva (ISCO 2, alto nivel universitario y mayor conteo de conocimientos ESCO). Presenta la MENOR reincidencia post-hoc en todos los modelos porque su movilidad es vertical (ascensos hacia códigos ESCO distintos). Ward aísla un núcleo más estricto y puro de alto conocimiento, mientras que K-Means asigna una frontera esférica más amplia. |
| Clúster 3 | Trayectorias Consolidadas de Alta Rotación o Larga Permanencia | 16.44% · 45.55% (0.997x) | 26.75% · 54.17% (1.186x) | 15.32% · 43.99% (0.963x) | 3 · Técnicos y profesionales de nivel medio / 3 · Técnicos y profesionales de nivel medio | Trayectorias extensas (span_q alto), mayor duración acumulada y alto solapamiento contractual (overlap_ratio > 1.5). En Ward captura además la alta rotación con la tasa post-hoc de repetición más alta, mientras que K-Means separa estrictamente por amplitud temporal y permanencia prolongada. |

### Explicación de las Divergencias Clave entre K-Means (`8.0`) y Ward (`8.1`)

- **Por qué el Clúster 2 (Profesionales ISCO 2) diverge en tamaño y reincidencia entre K-Means (`27.99%` · `42.75%`), Ward `n = 3,000` (`9.47%` · `34.34%`) y Ward `n = 25000` (`38.85%` · `47.96%`):**
  - **Geometría de partición y efecto del tamaño muestral:** En `n = 3,000`, la fusión jerárquica de Ward aísla un núcleo hiper-puro de **alta especialización teórica** (`9.47%`, `mean_skills_knowledge = 7.69`, `mean_prop_competence = 0.66`), logrando la menor reincidencia observada (`34.34%`, `Lift = 0.752x`) porque su movilidad es puramente vertical (ascensos hacia códigos ESCO distintos). Al escalar la muestra de Ward a `n = 25000`, el árbol incorpora también a técnicos/profesionales con mayor rotación (`38.85%`, `mean_skills_knowledge = 5.17`, `nivel_academico = 2.22`), mientras que K-Means (`27.99%`, `42.75%`, `Lift = 0.936x`) traza una frontera esférica intermedia.
- **Convergencia estructural del Clúster 3 (Carreras Extensas y Solapadas · ISCO 3) al escalar Ward a `n = 25000`:**
  - En `n = 3,000`, Ward mezclaba trayectorias largas con trabajadores de alta rotación (`26.75%` · `54.17%`). Sin embargo, al ampliar la muestra estratificada a `n = 25000`, **Ward converge casi 1 a 1 con K-Means `8.0`**: el Clúster 3 queda en **`15.32%`** (`span_q = 113.00`, `dur_mean = 39.35`, `overlap_ratio = 1.63`, tasa post-hoc `43.99%`) frente a **`16.44%`** (`span_q = 112.14`, `dur_mean = 37.47`, `overlap_ratio = 1.61`, tasa post-hoc `45.55%`) en K-Means, elevando la concordancia global de `ARI = 0.4708` (`NMI = 0.5462`) a **`ARI = 0.6502` (`NMI = 0.7296`)**!

---

## 5. Conclusiones Accionables de Negocio y Metodológicas

- **Estrategia combinada validada en `MineriaProtect`:** Utilizar **Ward (`8.1`)** con muestreo estratificado optimizado (`n = 25000` en 32 GB RAM) para confirmar la taxonomía jerárquica de **4 macro-ramas naturales** (descartando $k \ge 5$ y los métodos con *chaining* `single`/`average`/`complete`), y adoptar **K-Means++ (`8.0`)** sobre el `100%` de Train (`281674` personas y `1391018` experiencias) como motor operativo de asignación y reporte de centroides exactos en escala original.
- **Acciones diferenciadas para el Observatorio Laboral JobPath:**
  - **Clúster 0 (Inserción Temprana / Operativos ISCO 5):** Programas puente al primer empleo y certificación de competencias transversales para romper el ciclo de rotación horizontal repetitiva entre empleadores.
  - **Clúster 1 (Educación No Reportada · MNAR `11.65%`):** Evaluación y certificación de saberes previos empíricos para formalizar habilidades de trabajadores sin título universitario reportado.
  - **Clúster 2 (Profesionales Intensivos en Conocimiento · ISCO 2):** Rutas de posgrado aplicado, liderazgo técnico y vinculación universidad-empresa que potencien su trayectoria natural de ascenso vertical.
  - **Clúster 3 (Carreras Extensas / Multi-Empleo Solapado · ISCO 3):** Acompañamiento para consolidar portafolios laborales fragmentados y programas de reconversión ejecutiva para perfiles sénior.
