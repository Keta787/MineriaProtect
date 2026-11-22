# Evaluación Integral de Métodos Numéricos Aplicados al Proyecto JobPath

**Programa:** Ingeniería de Sistemas · UNIMINUTO (Ibagué)  
**Asignatura:** Métodos Numéricos (Docente referente de temáticas HTML: Prof. Juan Carlos González Sánchez)  
**Fuentes normativas:** `regresion_lineal_minimos_cuadrados (1).html` e `interpolacion_lagrange (1).html`  
**Proyecto aplicado:** **JobPath (`MineriaProtect`)** — *JobHop v2 (1,993,291 filas crudas; 1,871,014 procesadas; 1,738,738 clasificadas `saber_skills == 'ok'`) + ESCO v1.2.1 / ISCO-08 (3,039 oficios; 126,051 relaciones)*  
**Entregable evaluado:** `metodos_numericos_entregable` (Núcleo de 8 casos + `00_general/`)  
**Versión de auditoría:** **V2 Post-Corrección (Re-evaluación completa verificada)** — *19/19 tests OK · 19/19 SHA-256 (64 hex) intactos · 0 violaciones bilingües EN+ES · 0 enlaces rotos*  
**Escala de calificación:** 100 puntos (8 casos × 10 pts + Sección integradora 20 pts) → Nota `0.0` a `5.0` ($\text{Nota} = \text{Puntos} / 20$).

---

## Tabla de Contenido

- [1. Matriz de Trazabilidad: Temáticas HTML ↔ Proyecto JobPath ↔ Casos 01–08](#1-matriz-de-trazabilidad-temáticas-html--proyecto-jobpath--casos-0108)
- [2. Evaluación por Casos](#2-evaluación-por-casos)
  - [Caso 01 — IDEA-RL-01: Progresión por Paso de Carrera (MCO)](#caso-01--idea-rl-01-progresión-por-paso-de-carrera-mco)
  - [Caso 02 — IDEA-RL-02: Ontología ESCO y Transferibilidad (MCO y Rechazos de R²)](#caso-02--idea-rl-02-ontología-esco-y-transferibilidad-mco-y-rechazos-de-r)
  - [Caso 03 — IDEA-RL-04: Deriva Anual de Cohortes y Falla por Extrapolación](#caso-03--idea-rl-04-deriva-anual-de-cohortes-y-falla-por-extrapolación)
  - [Caso 04 — IDEA-RL-05: Sensibilidad a Outliers e Invarianza Afín de Escala](#caso-04--idea-rl-05-sensibilidad-a-outliers-e-invarianza-afín-de-escala)
  - [Caso 05 — IDEA-LG-01: Curva de Supervivencia Laboral S(q) y Fenómeno de Runge](#caso-05--idea-lg-01-curva-de-supervivencia-laboral-sq-y-fenómeno-de-runge)
  - [Caso 06 — IDEA-LG-02: Varianza Acumulada de PCA — Lagrange Directo e Inverso](#caso-06--idea-lg-02-varianza-acumulada-de-pca--lagrange-directo-e-inverso)
  - [Caso 07 — IDEA-HYB-01: Laboratorio Comparativo "¿Interpolar o Ajustar?"](#caso-07--idea-hyb-01-laboratorio-comparativo-interpolar-o-ajustar)
  - [Caso 08 — IDEA-HYB-02: Pack de Verificación en GeoGebra y Auditoría SHA-256](#caso-08--idea-hyb-02-pack-de-verificación-en-geogebra-y-auditoría-sha-256)
- [3. Evaluación Integradora Transversal (Proyecto Completo)](#3-evaluación-integradora-transversal-proyecto-completo)
- [4. Rúbrica Global de Evaluación (Escala 0.0 – 5.0)](#4-rúbrica-global-de-evaluación-escala-00--50)
- [5. Dictamen de Re-Evaluación Post-Corrección (Antes vs. Después — 100/100 · Nota 5.0/5.0)](#5-dictamen-de-re-evaluación-post-corrección-antes-vs-después--100100--nota-5050)

---

## 1. Matriz de Trazabilidad: Temáticas HTML ↔ Proyecto JobPath ↔ Casos 01–08

| Caso | ID | HTML Base | Temáticas del HTML evaluadas | Aplicación en el proyecto JobPath | Insumos CSV / GGB clave |
|---|---|---|---|---|---|
| **Caso 01** | `IDEA-RL-01` | Regresión Lineal (MCO) | Tabla de sumas, $a_1, a_0$, error típico $(\sum x)^2 \neq \sum x^2$, centroide $(\bar{x},\bar{y})$, $S_t, S_r, R^2, r, S_{y/x}$, extrapolación, GeoGebra `FitLine`. | Sintetiza 1,738,738 experiencias ordenadas por paso de carrera ($k=1..10$) y audita cohorte $\ge 10$ y extrapolación ($k=11,12,15$). | [rl01_summation_and_residuals_skills.csv](../01_IDEA_RL_01_Pasos_Carrera_MCO/tables/rl01_summation_and_residuals_skills.csv), [rl01_ols_summary.csv](../01_IDEA_RL_01_Pasos_Carrera_MCO/tables/rl01_ols_summary.csv), [rl01_extrapolation_audit.csv](../01_IDEA_RL_01_Pasos_Carrera_MCO/tables/rl01_extrapolation_audit.csv), [ggb_rl01_career_steps_skills.txt](../01_IDEA_RL_01_Pasos_Carrera_MCO/geogebra/ggb_rl01_career_steps_skills.txt) |
| **Caso 02** | `IDEA-RL-02` | Regresión Lineal (MCO) | Interpretación de $R^2$ bajo (modelo lineal pobre), $S_{y/x}$, interpretación de $a_1$ y $a_0$, verificación `FitLine`/`RSquare`. | Audita la ontología ESCO v1.2.1 (3,039 oficios), transferibilidad intersectorial por 10 grupos ISCO-08 y ortogonalidad de `greenShare`. | [rl02_esco_catalog_ols.csv](../02_IDEA_RL_02_Catalogo_ESCO_MCO/tables/rl02_esco_catalog_ols.csv), [rl02_isco_major_group_slopes.csv](../02_IDEA_RL_02_Catalogo_ESCO_MCO/tables/rl02_isco_major_group_slopes.csv), [ggb_rl02_isco10_transferability.txt](../02_IDEA_RL_02_Catalogo_ESCO_MCO/geogebra/ggb_rl02_isco10_transferability.txt) |
| **Caso 03** | `IDEA-RL-04` | Regresión Lineal (MCO) | Riesgo de extrapolación fuera del rango, invalidez física, estabilidad de ecuaciones normales, sensibilidad a datos extremos. | Evalúa deriva anual (2000–2019 vs. cola censurada 2020–2023), centrado $t=\text{año}-2000$, paridad `01_raw` y predicción negativa en 2027. | [rl04_annual_macro_series.csv](../03_IDEA_RL_04_Deriva_Anual_Extrapolacion/tables/rl04_annual_macro_series.csv), [rl04_ols_regime_comparison.csv](../03_IDEA_RL_04_Deriva_Anual_Extrapolacion/tables/rl04_ols_regime_comparison.csv), [rl04_extrapolation_failure_audit.csv](../03_IDEA_RL_04_Deriva_Anual_Extrapolacion/tables/rl04_extrapolation_failure_audit.csv), [ggb_rl04_annual_duration_extrapolation.txt](../03_IDEA_RL_04_Deriva_Anual_Extrapolacion/geogebra/ggb_rl04_annual_duration_extrapolation.txt) |
| **Caso 04** | `IDEA-RL-05` | Regresión Lineal (MCO) | Sensibilidad de $\sum e_i^2$ a residuos grandes (outliers), efecto sobre $S_t, S_r, R^2, S_{y/x}$, propiedades algebraicas de MCO ante escalado lineal. | Valida decisiones del pipeline `2.0`/`3.0`: winsorización IQR (Versión B) vs. Versión A y borrado de filas, e invarianza bajo `RobustScaler` en `04_transformed`. | [rl05_four_way_outlier_comparison.csv](../04_IDEA_RL_05_Outliers_E_Invarianza_Escala/tables/rl05_four_way_outlier_comparison.csv), [rl05_affine_scale_invariance.csv](../04_IDEA_RL_05_Outliers_E_Invarianza_Escala/tables/rl05_affine_scale_invariance.csv) |
| **Caso 05** | `IDEA-LG-01` | Interpolación de Lagrange | Teorema de unicidad, bases $L_i(x)$, Kronecker, $\sum L_i=1$, extrapolación riesgosa, **Fenómeno de Runge**, Chebyshev y polinomios por tramos, GeoGebra `Polynomial(P)`. | Reconstruye la supervivencia laboral $S(q)$ (`1,643,772` empleos cerrados) desde 4 hitos y mide el fenómeno de Runge de grado 3 a 16. | [lg01_survival_curve_S_q.csv](../05_IDEA_LG_01_Supervivencia_Y_Runge/tables/lg01_survival_curve_S_q.csv), [lg01_milestone_P3_weights_and_eval.csv](../05_IDEA_LG_01_Supervivencia_Y_Runge/tables/lg01_milestone_P3_weights_and_eval.csv), [lg01_runge_phenomenon_benchmark.csv](../05_IDEA_LG_01_Supervivencia_Y_Runge/tables/lg01_runge_phenomenon_benchmark.csv), [ggb_lg01_survival_p3_milestones.txt](../05_IDEA_LG_01_Supervivencia_Y_Runge/geogebra/ggb_lg01_survival_p3_milestones.txt) |
| **Caso 06** | `IDEA-LG-02` | Interpolación de Lagrange | Construcción directa $P_n(x)$, condición de nodos estrictamente distintos ($x_i \neq x_j$), $\sum L_i=1$, interpolación inversa, GeoGebra `Polynomial(P)`. | Dimensiona el número efectivo de componentes principales $\hat{k}(V^*)$ del PCA 50k (Versiones A y B) y prueba la guarda ante la meseta de rango 9. | [lg02_pca_50k_reference.csv](../06_IDEA_LG_02_PCA_Lagrange_Inversa/tables/lg02_pca_50k_reference.csv), [lg02_pca_forward_P3_eval.csv](../06_IDEA_LG_02_PCA_Lagrange_Inversa/tables/lg02_pca_forward_P3_eval.csv), [lg02_pca_inverse_effective_dim.csv](../06_IDEA_LG_02_PCA_Lagrange_Inversa/tables/lg02_pca_inverse_effective_dim.csv), [ggb_lg02_pca_forward_p3.txt](../06_IDEA_LG_02_PCA_Lagrange_Inversa/geogebra/ggb_lg02_pca_forward_p3.txt) |
| **Caso 07** | `IDEA-HYB-01` | Ambos HTML (MCO + Lagrange) | Diapositiva 2 de ambos HTML: *¿Interpolar o ajustar?*, ruido vs. tabla exacta, Runge vs. Chebyshev vs. por tramos, extrapolación. | Enfrenta 4 métodos sobre 4 curvas reales de JobPath bajo LOOCV interior y extrapolación a +2 pasos para construir una rúbrica de selección. | [hyb01_loocv_and_extrapolation_matrix.csv](../07_IDEA_HYB_01_Laboratorio_Interpolar_vs_Ajustar/tables/hyb01_loocv_and_extrapolation_matrix.csv), [hyb01_method_selection_rubric.csv](../07_IDEA_HYB_01_Laboratorio_Interpolar_vs_Ajustar/tables/hyb01_method_selection_rubric.csv) |
| **Caso 08** | `IDEA-HYB-02` | Ambos HTML (Diapositivas 14–15) | Reto Python (`regresion_lineal` vs. `numpy.polyfit`, `lagrange` vs. `scipy.interpolate.lagrange`) y verificación en GeoGebra Classic. | Consolida 5 scripts GeoGebra, verificación triple de 39 modelos MCO y Lagrange, integridad SHA-256 completa (64 hex, 19 insumos), auditoría bilingüe y 19 tests automatizados. | [verification_log.md](./verification_log.md), [sha256_input_integrity.csv](./sha256_input_integrity.csv), [geogebra_verification_index.md](../08_IDEA_HYB_02_Pack_Verificacion_GeoGebra/geogebra/geogebra_verification_index.md) |

---

## 2. Evaluación por Casos

---

### Caso 01 — `IDEA-RL-01`: Progresión por Paso de Carrera (MCO)

#### 1. Ficha Teórico-Aplicada (HTML + Proyecto)
- **Temáticas HTML evaluadas:** Criterio $\min \sum e_i^2$, construcción de tabla de sumas ($n, \sum x_i, \sum y_i, \sum x_i^2, \sum x_i y_i$), fórmulas cerradas de $a_1$ y $a_0$, error típico $(\sum x_i)^2 \neq \sum x_i^2$, propiedad del centroide $(\bar{x}, \bar{y})$, suma nula de residuos, calidad del ajuste ($S_t, S_r, R^2, r, S_{y/x}$), extrapolación y verificación en GeoGebra (`FitLine`, `RSquare`).
- **Rol en JobPath:** Resume el perfil ocupacional a lo largo de la secuencia de empleos ($k = 1..10$) sobre 1,738,738 experiencias clasificadas (`Versión A`), contrastando el universo completo frente a la cohorte longitudinal de personas con $\ge 10$ empleos y auditando predicciones fuera de soporte ($k = 11, 12, 15$).
- **Fuentes verificadas:** [rl01_career_step_profile.csv](../01_IDEA_RL_01_Pasos_Carrera_MCO/tables/rl01_career_step_profile.csv), [rl01_summation_and_residuals_skills.csv](../01_IDEA_RL_01_Pasos_Carrera_MCO/tables/rl01_summation_and_residuals_skills.csv), [rl01_ols_summary.csv](../01_IDEA_RL_01_Pasos_Carrera_MCO/tables/rl01_ols_summary.csv), [rl01_extrapolation_audit.csv](../01_IDEA_RL_01_Pasos_Carrera_MCO/tables/rl01_extrapolation_audit.csv), [ggb_rl01_career_steps_skills.txt](../01_IDEA_RL_01_Pasos_Carrera_MCO/geogebra/ggb_rl01_career_steps_skills.txt).

#### 2. Preguntas Conceptuales (2 puntos)
- **P1.1 (1 pt — Selección múltiple):** En el ajuste `mean_skills ~ job_order (1..10)`, la suma algebraica de los 10 residuos resulta $\sum_{i=1}^{10} e_i = -3.55 \times 10^{-15} \approx 0$. Según el HTML de regresión lineal, ¿por qué esto demuestra que minimizar $\sum e_i$ no sirve como criterio para elegir la mejor recta?
  - a) Porque al sumar cero significa que $R^2 = 1$ para cualquier recta que pase por el origen.
  - b) Porque los residuos positivos (como $e_9 = +0.0535$) y negativos (como $e_8 = -0.1054$) se cancelan entre sí; cualquier recta que pase por el centroide $(\bar{x}, \bar{y}) = (5.5, 23.7534)$ cumple $\sum e_i = 0$ sin importar cuán mala sea su pendiente.
  - c) Porque las fórmulas normales solo convergen cuando todos los residuos son positivos.
  - d) Porque en datos laborales solo se admite minimizar $\sum |e_i|$.
- **P1.2 (1 pt — Verdadero/Falso justificado):** *«Como en `IDEA-RL-01` el modelo `mean_skills ~ job_order (1..10)` obtiene $a_1 = +0.2250$ y $R^2 = 0.9955$, podemos concluir que cambiar de empleo causa que cada trabajador aprenda aproximadamente 0.225 nuevas habilidades técnicas por contrato.»* Indique si es Verdadero o Falso y justifique con dos razones (una estadística/metodológica y otra propia de la semántica de JobPath/ESCO).

#### 3. Ejercicio Procedimental (3 puntos — Datos reales de `rl01_summation_and_residuals_skills.csv`)
Con las 10 medias por paso de carrera ($k = 1..10$) de habilidades esenciales requeridas por el oficio (`mean_skills`), se obtienen exactamente las siguientes sumatorias:

| $i$ | $x_i$ (`job_order`) | $y_i$ (`mean_skills`) | $x_i^2$ | $x_i y_i$ | $e_i^2$ | $(y_i - \bar{y})^2$ |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 22.6939 | 1 | 22.6939 | 0.002223 | 1.122570 |
| 2 | 2 | 22.9780 | 4 | 45.9560 | 0.000144 | 0.601234 |
| 3 | 3 | 23.2077 | 9 | 69.6231 | 0.000280 | 0.297774 |
| 4 | 4 | 23.4354 | 16 | 93.7416 | 0.000379 | 0.101113 |
| 5 | 5 | 23.6797 | 25 | 118.3983 | 0.001503 | 0.005434 |
| 6 | 6 | 23.8848 | 36 | 143.3086 | 0.000357 | 0.017261 |
| 7 | 7 | 24.0849 | 49 | 168.5940 | 0.000036 | 0.109876 |
| 8 | 8 | 24.2104 | 64 | 193.6835 | 0.011103 | 0.208901 |
| 9 | 9 | 24.5942 | 81 | 221.3482 | 0.002859 | 0.707053 |
| 10 | 10 | 24.7649 | 100 | 247.6490 | 0.000001 | 1.023160 |
| **$\Sigma$** | **55.0** | **237.533848** | **385.0** | **1324.996288** | **0.018884** | **4.194377** |

Calcule paso a paso (conservando 4 decimales en los resultados):
1. La pendiente $a_1$ y el intercepto $a_0$ (verificando que no confunde $(\sum x_i)^2$ con $\sum x_i^2$).
2. El coeficiente de determinación $R^2$, la correlación $r$ y el error estándar de la estimación $S_{y/x}$.
3. La comprobación de que la recta pasa exactamente por el centroide $(\bar{x}, \bar{y})$.
4. La extrapolación en $k = 12$ y su error absoluto frente al valor observado real (`25.192637`, con `n_rows = 10,159`).

#### 4. Pregunta de Análisis Crítico y Criterio Ingenieril (3 puntos)
Compare en `rl01_ols_summary.csv` y `rl01_extrapolation_audit.csv` los siguientes hallazgos reales del entregable:
- En `mean_green ~ k`, el universo completo ($k=1..10$) arroja $a_1 = -0.0002187$ ($R^2 = 0.7877$), pero en la cohorte longitudinal ($\ge 10$ empleos) la pendiente se invierte a $a_1 = +0.0001830$ ($R^2 = 0.7310$).
- En `reincide_rate ~ k`, el $R^2$ cae de `0.9625` ($a_1 = +0.0213$) en el universo completo a `0.4475` ($a_1 = +0.0072$) en la cohorte $\ge 10$.
- En `mean_dur_q ~ k` (calculada estrictamente sobre **empleos cerrados `~es_vigente`, regla `MR-09`**), el ajuste en $k=1..10$ tiene $R^2 = 0.9233$ ($a_0 = 13.2330$, $a_1 = -0.8565$, $S_{y/x} = 0.7928$), pero al extrapolar a $k = 15$ predice `0.3852` trimestres frente al observado cerrado `4.2601` (error absoluto `3.8749` trimestres).
- Además, `rl01_ols_summary.csv` incluye la verificación de **Mínimos Cuadrados Ponderados (WLS)** por tamaño de celda $n_k$: en `mean_skills`, la pendiente ponderada es `wls_a1 = +0.2287` (diferencia relativa de apenas **`1.67 %`** respecto a MCO).

**Explique:** (a) qué fenómeno estadístico produce la inversión de signo en `mean_green` y la caída en `reincide_rate`, (b) qué demuestra la auditoría **WLS** cuando `k=1` agrupa `352,093` registros y `k=10` solo `25,321` (13.9× menos), y (c) por qué filtrar `~es_vigente` (`MR-09`) en `mean_dur_q` mejora el ajuste interno ($R^2: 0.9050 \to 0.9233$) pero sigue fallando al extrapolar en $k=15$.

#### 5. Verificación en GeoGebra / Python (2 puntos)
Usando los comandos exactos de [ggb_rl01_career_steps_skills.txt](../01_IDEA_RL_01_Pasos_Carrera_MCO/geogebra/ggb_rl01_career_steps_skills.txt):
1. Escriba la secuencia completa de comandos en GeoGebra Classic (en inglés o español) para graficar la lista `P`, obtener la recta `f`, la correlación `r`, el `R2`, el `Centroid` y el punto extrapolado `Q_pred` en $k=12$.
2. Indique qué debe arrojar `np.polyfit(x, y, 1)` en Python al compararlo con la implementación propia y qué magnitud de discrepancia se obtuvo en `rl01_ols_summary.csv`.

#### 6. Solucionario Detallado y Criterios de Calificación (10 puntos)
- **P1.1:** **Opción b)** (1 pt). Por la primera ecuación normal $\frac{\partial S_r}{\partial a_0} = -2\sum e_i = 0$, toda recta que pasa por $(\bar{x}, \bar{y})$ satisface $\sum e_i = 0$; por ello los errores positivos y negativos se compensan y se requiere minimizar $S_r = \sum e_i^2$.
- **P1.2:** **Falso** (1 pt: 0.5 juicio + 0.5 doble argumento). (1) La regresión MCO describe una **asociación lineal descriptiva** sobre medias agregadas, no causalidad (puede haber sesgo de supervivencia/selección de quienes acumulan más empleos). (2) En JobPath, `mean_skills` mide las **competencias esenciales requeridas por el oficio ESCO asignado**, no un inventario verificado de habilidades individuales aprendidas por la persona.
- **Ejercicio procedimental (3 pts):**
  1. *(1.0 pt)* Con $n = 10$, $\sum x_i = 55$, $(\sum x_i)^2 = 3025$ y $\sum x_i^2 = 385$:
     $$a_1 = \frac{10(1324.996288) - (55)(237.533848)}{10(385) - 55^2} = \frac{13249.96288 - 13064.36166}{3850 - 3025} = \frac{185.601221}{825} = 0.224971 \approx \mathbf{0.2250}$$
     $$\bar{x} = \frac{55}{10} = 5.5, \qquad \bar{y} = \frac{237.533848}{10} = 23.7534$$
     $$a_0 = 23.753385 - (0.224971)(5.5) = 23.753385 - 1.237341 = \mathbf{22.5160}$$
  2. *(1.0 pt)* Calidad del ajuste:
     $$R^2 = \frac{S_t - S_r}{S_t} = \frac{4.194377 - 0.018884}{4.194377} = \mathbf{0.9955}, \qquad r = +\sqrt{0.995498} = \mathbf{0.9977}$$
     $$S_{y/x} = \sqrt{\frac{S_r}{n - 2}} = \sqrt{\frac{0.018884}{8}} = \sqrt{0.002361} = \mathbf{0.0486\ \text{habilidades}}$$
  3. *(0.5 pt)* Centroide: $\hat{y}(5.5) = 22.516043 + 0.224971(5.5) = 23.753385 = \bar{y}$ (`centroid_err = 0.0`).
  4. *(0.5 pt)* Extrapolación en $k = 12$: $\hat{y}(12) = 22.516043 + 0.224971(12) = \mathbf{25.2157}$; error absoluto $= |25.215697 - 25.192637| = \mathbf{0.0231}$.
- **Análisis crítico (3 pts — 1 pt por literal):**
  - (a) **Paradoja de Simpson / sesgo de composición longitudinal:** al avanzar $k$ en el universo completo salen las personas de carreras cortas y sobreviven solo perfiles de alta rotación (efecto composición). En `reincide_rate`, además, el target `veces_ese_oficio > 1` mira toda la carrera completa, introduciendo un sesgo mecánico de longitud de trayectoria que se atenúa al fijar la cohorte $\ge 10$.
  - (b) **Robustez frente a heterocedasticidad (WLS vs. MCO):** dar el mismo peso a $k=1$ (`352,093` filas) que a $k=10$ (`25,321` filas) ignora la distinta varianza de las medias; la comprobación WLS añadida a `rl01_ols_summary.csv` demuestra que la tendencia de `mean_skills` es altamente robusta (`wls_a1 = +0.2287`, diferencia relativa de solo **`1.67 %`**), mientras en `mean_dur_q` y `mean_green` las diferencias ponderadas (`21.7 %` y `29.4 %`) advierten sobre mayor curvatura inicial y efecto composición.
  - (c) **Consistencia de censura (`MR-09`) y curvatura convexa:** al aplicar el filtro estricto `~es_vigente` (`n_closed_rows`, igual que en `IDEA-LG-01`), se elimina el sesgo de empleos activos imputados a `2026-Q1`, elevando $R^2$ de `0.9050` a **`0.9233`** y reduciendo $S_{y/x}$ de `0.8421` a **`0.7928`**. Sin embargo, como la duración cerrada decae de forma **convexa** (cae rápido al inicio y se estabiliza en torno a `4.26–5.24` trimestres en $k=11..15$), extrapolar una recta lineal sigue subestimando fuertemente (`0.3852` vs. `4.2601`, error `3.8749`).
- **Verificación GeoGebra / Python (2 pts — 1 pt c/u):**
  1. Comandos: `P = {(1, 22.693871), ..., (10, 24.764899)}`, `f = FitLine(P)` (`AjusteLineal(P)`), `r = CorrelationCoefficient(P)`, `R2 = RSquare(P, f)`, `Centroid = (5.5, 23.753385)`, `Q_pred = (12, f(12))` → espera `25.215697`.
  2. `np.polyfit(x, y, 1)` devuelve `[a1, a0] = [0.22497118, 22.51604337]` (orden descendente de potencias). En `rl01_ols_summary.csv`, la diferencia absoluta máxima es `3.5527e-15` (prácticamente precisión de máquina `float64`).

---

### Caso 02 — `IDEA-RL-02`: Ontología ESCO y Transferibilidad (MCO y Rechazos de $R^2$)

#### 1. Ficha Teórico-Aplicada (HTML + Proyecto)
- **Temáticas HTML evaluadas:** Evaluación honesta de calidad de ajuste (qué significa un $R^2$ bajo — Pregunta conceptual 1 del HTML de regresión), interpretación de pendiente $a_1$ e intercepto $a_0$, dispersión residual $S_{y/x}$, uso de `FitLine` y `RSquare` en GeoGebra.
- **Rol en JobPath:** Caracteriza la estructura interna del catálogo ESCO v1.2.1 (`3,039` oficios limpios y `126,051` relaciones) que enriquece a JobHop, estratificando la transferibilidad intersectorial en los 10 grandes grupos ISCO-08 y probando la independencia lineal de `greenShare`.
- **Fuentes verificadas:** [rl02_esco_catalog_ols.csv](../02_IDEA_RL_02_Catalogo_ESCO_MCO/tables/rl02_esco_catalog_ols.csv), [rl02_isco_major_group_slopes.csv](../02_IDEA_RL_02_Catalogo_ESCO_MCO/tables/rl02_isco_major_group_slopes.csv), [ggb_rl02_isco10_transferability.txt](../02_IDEA_RL_02_Catalogo_ESCO_MCO/geogebra/ggb_rl02_isco10_transferability.txt).

#### 2. Preguntas Conceptuales (2 puntos)
- **P2.1 (1 pt — Selección múltiple):** Al ajustar `ESCO greenShare ~ n_essential` sobre los `3,039` oficios de ESCO se obtiene $R^2 = 0.000045$ ($4.47 \times 10^{-5}$) y $a_1 = -5.21 \times 10^{-5}$. Con base en el HTML de regresión lineal, ¿cuál es la interpretación correcta?
  - a) El `0.0045 %` de los oficios verdes cae exactamente sobre la recta.
  - b) El número de habilidades esenciales explica prácticamente el `0 %` de la variación del índice `greenShare`; el modelo lineal debe rechazarse por ausencia de relación lineal (ortogonalidad).
  - c) La pendiente vale `0.000045` y por tanto hay correlación positiva débil.
  - d) El algoritmo MCO falló numéricamente y debe reemplazarse por interpolación de Lagrange de grado 3,038.
- **P2.2 (1 pt — Selección múltiple):** En la estratificación de `n_cross_sector ~ n_total_rel` por grandes grupos ISCO-08 (`rl02_isco_major_group_slopes.csv`), **ISCO-1 Managers** presenta $a_1 = 0.7403$ ($R^2 = 0.7541$) frente a **ISCO-9 Elementary occupations** con $a_1 = 0.3131$ ($R^2 = 0.3618$). ¿Qué significa geométrica y operativamente esa diferencia de pendientes?
  - a) Que por cada 10 habilidades adicionales vinculadas a un oficio en ESCO, los cargos directivos (ISCO-1) añaden en promedio ~7.4 habilidades transferibles entre sectores, mientras que las ocupaciones elementales (ISCO-9) añaden solo ~3.1.
  - b) Que ISCO-1 tiene 74 % más oficios registrados que ISCO-9.
  - c) Que los interceptos $a_0$ deben ser iguales a cero en ambos grupos para poder comparar pendientes.
  - d) Que la recta de ISCO-9 explica el 74 % de la varianza de ISCO-1.

#### 3. Ejercicio Procedimental (3 puntos — Datos reales de `rl02_isco_major_group_slopes.csv` y `rl02_esco_catalog_ols.csv`)
Para verificar en GeoGebra la relación entre habilidades totales promedio ($x$: `mean_total_rel`) y habilidades transferibles intersectoriales promedio ($y$: `mean_cross_sector`), el entregable resume los 10 grandes grupos ISCO-08 en los siguientes 10 centroides:

| Grupo ISCO-08 | $x_i$ (`mean_total_rel`) | $y_i$ (`mean_cross_sector`) |
|---|---:|---:|
| 0 · Armed forces | 35.6667 | 25.6190 |
| 1 · Managers | 40.8229 | 25.2171 |
| 2 · Professionals | 53.1763 | 30.8952 |
| 3 · Technicians | 38.4737 | 21.5619 |
| 4 · Clerical support | 29.2809 | 16.2135 |
| 5 · Service & sales | 35.2843 | 15.8824 |
| 6 · Agriculture & forestry | 46.5909 | 12.2955 |
| 7 · Craft & trades | 37.7234 | 21.2005 |
| 8 · Plant & machine op. | 31.4380 | 16.7406 |
| 9 · Elementary | 31.2763 | 13.2763 |

Sumatorias exactas de `rl02_esco_catalog_ols.csv` ($n = 10$):  
$\sum x_i = 379.733303$, $\sum y_i = 198.902019$, $\sum x_i^2 = 14909.232664$, $\sum x_i y_i = 7764.918525$, $S_t = 327.741214$, $S_r = 235.970430$.

Calcule paso a paso:
1. Pendiente $a_1$, intercepto $a_0$ y ecuación $\hat{y} = a_0 + a_1 x$.
2. Calidad del ajuste ($R^2$, $r$, $S_{y/x}$) y clasificación según los umbrales del proyecto (Fuerte $\ge 0.70$, Moderado $[0.30, 0.70)$, Rechazado $< 0.30$).
3. La predicción $\hat{y}(45)$ y diga si corresponde a interpolación o extrapolación respecto al rango $[x_{\min}, x_{\max}]$.

#### 4. Pregunta de Análisis Crítico y Criterio Ingenieril (3 puntos)
Analice críticamente dos puntos delicados de `IDEA-RL-02`:
1. Los dos únicos modelos "Fuertes" sobre el catálogo completo (`n=3,039`) son `n_essential ~ n_ess_comp` ($R^2 = 0.8643$) y `n_total_rel ~ n_competence` ($R^2 = 0.7319$), donde la variable $x$ es **parte algebraica** de $y$ (por ejemplo, `n_essential = n_ess_comp + n_ess_know + ...`). ¿Por qué un ingeniero de datos debe advertir este **acople parte-todo** antes de reportar esos $R^2$ como hallazgos predictivos independientes?
2. En [ggb_rl02_isco10_transferability.txt](../02_IDEA_RL_02_Catalogo_ESCO_MCO/geogebra/ggb_rl02_isco10_transferability.txt) se incluye el punto `Q_pred = (45, f(45))` = `22.9327` acompañado explícitamente de la advertencia `# WARNING (MR-06): R2 = 0.2800 < 0.30 -> REJECTED`, dado que el grupo `ISCO-6` (`x = 46.59, y = 12.30`) se desvía más de `11` habilidades de la recta. ¿Por qué sirve `Q_pred` como verificación aritmética de la fórmula, pero **no** como estimación operativa válida en JobPath?

#### 5. Verificación en GeoGebra / Python (2 puntos)
1. Escriba los comandos de GeoGebra Classic de [ggb_rl02_isco10_transferability.txt](../02_IDEA_RL_02_Catalogo_ESCO_MCO/geogebra/ggb_rl02_isco10_transferability.txt) para verificar la recta, el centroide y $R^2$ de los 10 centroides ISCO.
2. Explique cómo comprobaría en GeoGebra (Hoja de cálculo → *Análisis de regresión de dos variables*, diapositiva 14 del HTML) cuál de los 10 grupos ISCO genera el mayor residuo negativo $e_i$.

#### 6. Solucionario Detallado y Criterios de Calificación (10 puntos)
- **P2.1:** **Opción b)** (1 pt). $R^2 = 4.47 \times 10^{-5}$ indica que la recta explica `0.0045 %` de la varianza de `greenShare`; la transición verde es ortogonal al volumen total de habilidades esenciales.
- **P2.2:** **Opción a)** (1 pt). $a_1$ representa la tasa de cambio media $\Delta \hat{y} / \Delta x$ en unidades de $y$ por unidad de $x$.
- **Ejercicio procedimental (3 pts):**
  1. *(1.25 pts)*
     $$a_1 = \frac{10(7764.918525) - (379.733303)(198.902019)}{10(14909.232664) - (379.733303)^2} = \frac{77649.185246 - 75529.720843}{149092.326636 - 144197.381698} = \frac{2119.464403}{4894.944938} = \mathbf{0.4330}$$
     $$\bar{x} = 37.973330, \qquad \bar{y} = 19.890202$$
     $$a_0 = 19.890202 - (0.432990)(37.973330) = 19.890202 - 16.442089 = \mathbf{3.4481}$$
     $$\hat{y} = 3.4481 + 0.4330\,x$$
  2. *(1.0 pt)*
     $$R^2 = \frac{327.741214 - 235.970430}{327.741214} = \mathbf{0.2800}, \qquad r = +\sqrt{0.280010} = \mathbf{0.5292}$$
     $$S_{y/x} = \sqrt{\frac{235.970430}{10 - 2}} = \sqrt{29.496304} = \mathbf{5.4310\ \text{habilidades}}$$
     Clasificación: **Débil / Modelo lineal rechazado** ($R^2 = 0.2800 < 0.30$).
  3. *(0.75 pt)* $\hat{y}(45) = 3.448113 + 0.432990(45) = \mathbf{22.9327}$. Como $x \in [29.2809, 53.1763]$, evaluar en $x = 45$ es **interpolación** (está dentro del rango observado), aunque estadísticamente poco confiable por el $R^2$ rechazado.
- **Análisis crítico (3 pts — 1.5 pts c/u):**
  1. Cuando $x$ es un subconjunto aditivo de $y$ ($y = x + z$), existe covarianza matemática inducida ($\text{Cov}(x, x+z) = \text{Var}(x) + \text{Cov}(x,z)$) que infla $R^2$ por construcción taxonómica. Reportarlo sin aclarar el acople confundiría una identidad contable de ESCO con capacidad predictiva genuina.
  2. `Q_pred = (45, 22.9327)` valida que la recta en GeoGebra coincide con Python (`polyfit_max_abs_diff = 1.066e-14`), pero con $R^2 = 0.2800$ y $S_{y/x} = 5.43$ habilidades (y un atípico estructural como Agricultura ISCO-6 con `y = 12.30` vs. $\hat{y}(46.59) = 23.62$, residuo $e_6 \approx -11.33$), el modelo lineal no captura la heterogeneidad sectorial y no debe usarse para proyectar transferibilidad.
- **Verificación GeoGebra / Python (2 pts — 1 pt c/u):**
  1. `P = {(35.666667, 25.619048), ..., (31.276316, 13.276316)}`, `f = FitLine(P)`, `r = CorrelationCoefficient(P)`, `R2 = RSquare(P, f)`, `Centroid = (37.973330, 19.890202)`, `Q_pred = (45, f(45))`.
  2. En *Vista → Hoja de cálculo*, ingresar `mean_total_rel` en columna A y `mean_cross_sector` en columna B → *Análisis de regresión de dos variables* → Modelo *Lineal* → activar la **gráfica de residuos** (*Residual Plot*), donde el punto de ISCO-6 (`x = 46.59`) destaca con el mayor residuo negativo ($e \approx -11.33$).

---

### Caso 03 — `IDEA-RL-04`: Deriva Anual de Cohortes y Falla por Extrapolación

#### 1. Ficha Teórico-Aplicada (HTML + Proyecto)
- **Temáticas HTML evaluadas:** Diferencia crítica entre interpolar y extrapolar (diapositiva 12 del HTML de MCO), pérdida de validez física fuera del rango observado, sensibilidad de mínimos cuadrados a puntos extremos de cola, y estabilidad numérica de las ecuaciones normales.
- **Rol en JobPath:** Audita la evolución anual de contrataciones (`2000–2019` con `1,509,997` empleos frente a la cola censurada `2020–2023` con apenas `59, 3, 3, 1` registros), verifica paridad de particiones crudas `01_raw` (`train/test/val`) y demuestra el colapso físico de la extrapolación lineal de duración hacia 2027.
- **Fuentes verificadas:** [rl04_annual_macro_series.csv](../03_IDEA_RL_04_Deriva_Anual_Extrapolacion/tables/rl04_annual_macro_series.csv), [rl04_ols_regime_comparison.csv](../03_IDEA_RL_04_Deriva_Anual_Extrapolacion/tables/rl04_ols_regime_comparison.csv), [rl04_extrapolation_failure_audit.csv](../03_IDEA_RL_04_Deriva_Anual_Extrapolacion/tables/rl04_extrapolation_failure_audit.csv), [rl04_raw_partition_parity.csv](../03_IDEA_RL_04_Deriva_Anual_Extrapolacion/tables/rl04_raw_partition_parity.csv), [ggb_rl04_annual_duration_extrapolation.txt](../03_IDEA_RL_04_Deriva_Anual_Extrapolacion/geogebra/ggb_rl04_annual_duration_extrapolation.txt).

#### 2. Preguntas Conceptuales (2 puntos)
- **P3.1 (1 pt — Selección múltiple):** En `mean_skills ~ start_year`, al incluir únicamente 4 puntos adicionales de cola (`2020–2023`, con `59, 3, 3, 1` inicios), el modelo pasa de $a_1 = +0.0967, R^2 = 0.7475$ (`2000–2019`) a $a_1 = -0.1011, R^2 = 0.0826$ (`2000–2023`). ¿Por qué unos pocos puntos en los extremos de $x$ destruyen tan drásticamente una recta MCO?
  - a) Porque las ecuaciones normales siempre rechazan muestras con $n > 20$.
  - b) Porque MCO penaliza los residuos **al cuadrado** ($e_i^2$) y los puntos extremos en el eje $x$ ejercen alto apalancamiento (*leverage*), rotando la pendiente para reducir sus enormes cuadrados residuales ($S_r$ salta de `2.10` a `130.42`).
  - c) Porque al pasar de `2019` a `2023` el signo de $\sum x_i$ se vuelve negativo.
  - d) Porque `start_year` no admite el cálculo del intercepto $a_0$.
- **P3.2 (1 pt — Verdadero/Falso justificado):** *«Centrar la variable temporal como $t = \text{año} - 2000$ cambia la pendiente $a_1$ y el coeficiente $R^2$ del ajuste de `mean_dur_q`, pero vuelve más fácil interpretar el intercepto $a_0$.»* Responda Verdadero o Falso y justifique.

#### 3. Ejercicio Procedimental (3 puntos — Datos reales de `rl04_ols_regime_comparison.csv` y `rl04_extrapolation_failure_audit.csv`)
Para la serie anual de duración media laboral en **empleos estrictamente cerrados (`~es_vigente`, regla `MR-09`)** `mean_dur_q` en el soporte válido `2000–2019` ($n = 20$), usando la variable centrada $t = \text{año} - 2000 \in \{0, 1, \dots, 19\}$, las sumatorias exactas son:
- $\sum t_i = 190.0$, $\sum y_i = 178.240127$, $\sum t_i^2 = 2470.0$, $\sum t_i y_i = 1166.201773$, $S_t = 429.411865$, $S_r = 11.648359$.

Calcule paso a paso:
1. Pendiente $a_1$ e intercepto centrado $a_0$ (y derive el intercepto sin centrar $a_{0,\text{año}}$ que aparecería al usar `start_year = 2000..2019`).
2. Calidad del ajuste: $R^2$, $r$ (con su signo correcto) y $S_{y/x}$.
3. Extrapole la duración media para los años **2020** ($t=20$), **2021** ($t=21$) y **2027** ($t=27$), calcule el año exacto en que la recta cruza cero ($\hat{y} = 0$) y explique por qué los resultados desde 2021 en adelante son físicamente inválidos.

#### 4. Pregunta de Análisis Crítico y Criterio Ingenieril (3 puntos)
Observe los siguientes tres datos reales de los CSV del Caso 03:
1. En `rl04_ols_regime_comparison.csv`, la discrepancia numérica máxima vs. `numpy.polyfit` para `n_starts (2000–2019)` baja de `4.470e-08` (usando `start_year`, donde $|a_0| = 5{,}386{,}114.16$) a `2.183e-11` al centrar $t = \text{año} - 2000$ (reducción > 2,000×), y en `mean_dur_q` baja de `1.660e-11` a `3.553e-15` (**4,672×**).
2. En `rl04_annual_macro_series.csv`, comparar la columna `mean_dur_q` (estrictamente cerrados `~es_vigente`) frente a la columna de auditoría `mean_dur_q_incl_active` muestra que **sin filtrar vigentes**, 2019 daba un rebote artificial (`6.6052 → 8.3124`), mientras que **con el filtro `MR-09` (`~es_vigente`)** decrece limpiamente de `3.1420` (2018) a `2.2712` (2019), elevando $R^2$ de `0.9288` a `0.9729`.
3. En `rl04_raw_partition_parity.csv`, las tres particiones crudas `raw_train` (`1,594,827`), `raw_test` (`198,877`) y `raw_val` (`199,587`) muestran pendientes de participación porcentual casi idénticas (`+0.1855`, `+0.1808`, `+0.1848 %/año`).

**Responda:** (a) ¿por qué ocurre la pérdida de precisión numérica sin centrar (cancelación catastrófica en $n\sum x^2 - (\sum x)^2$)?, (b) ¿por qué la regla `MR-09` (`~es_vigente`) eliminó el salto anómalo de 2019 pero no impide que `mean_dur_q` siga cayendo mecánicamente (`-0.7926` trimestres/año) hacia valores negativos al extrapolar?, y (c) ¿qué valida la paridad en `01_raw` para todo el proyecto JobPath?

#### 5. Verificación en GeoGebra / Python (2 puntos)
1. Transcriba los comandos clave de [ggb_rl04_annual_duration_extrapolation.txt](../03_IDEA_RL_04_Deriva_Anual_Extrapolacion/geogebra/ggb_rl04_annual_duration_extrapolation.txt) y explique qué evidencia visual inmediata entrega `Q_pred = (27, f(27))` en el plano cartesiano de GeoGebra.
2. En `rl04_ols_regime_comparison.csv`, los dos modelos `mean_dur_q (2000–2019)` y `mean_dur_q (t-2000, 2000–2019)` producen `polyfit_max_abs_diff = 1.6598e-11` vs. `3.5527e-15`. ¿Qué buena práctica de programación numérica en Python se desprende de esta comparación?

#### 6. Solucionario Detallado y Criterios de Calificación (10 puntos)
- **P3.1:** **Opción b)** (1 pt). Los 4 años censurados están en el borde superior del dominio y caen hasta `mean_skills = 14.0` (`n=1` en 2023); al elevar sus residuos al cuadrado y tener alto apalancamiento, dominan $S_r$ y revierten la pendiente.
- **P3.2:** **Falso** (1 pt). Una traslación $t = x - 2000$ **no altera** ni la pendiente $a_1$ (`-0.7926`), ni $R^2$ (`0.9729`), ni $S_{y/x}$ (`0.8044`); únicamente traslada el intercepto de un valor sin sentido operativo en el año 0 d. C. (`1601.64` trimestres) al nivel base en el año 2000 (`16.4417` trimestres) y mejora el condicionamiento numérico en **4,672×**.
- **Ejercicio procedimental (3 pts):**
  1. *(1.0 pt)*
     $$a_1 = \frac{20(1166.201773) - (190)(178.240127)}{20(2470) - 190^2} = \frac{23324.035460 - 33865.624130}{49400 - 36100} = \frac{-10541.588670}{13300} = \mathbf{-0.7926\ \text{trim./año}}$$
     $$\bar{t} = \frac{190}{20} = 9.5, \qquad \bar{y} = \frac{178.240127}{20} = 8.9120$$
     $$a_0 = 8.912006 - (-0.792601)(9.5) = 8.912006 + 7.529707 = \mathbf{16.4417\ \text{trimestres}}$$
     Intercepto sin centrar: $a_{0,\text{año}} = a_0 - 2000\,a_1 = 16.441713 - 2000(-0.792601) = \mathbf{1601.6430}$.
  2. *(1.0 pt)*
     $$R^2 = \frac{429.411865 - 11.648359}{429.411865} = \mathbf{0.9729}, \qquad r = -\sqrt{0.972874} = \mathbf{-0.9863}$$
     (Signo negativo porque $a_1 < 0$).
     $$S_{y/x} = \sqrt{\frac{11.648359}{20 - 2}} = \sqrt{0.647131} = \mathbf{0.8044\ \text{trimestres}}$$
  3. *(1.0 pt)* Extrapolación:
     - 2020 ($t=20$): $\hat{y}(20) = 16.441713 - 0.792601(20) = \mathbf{+0.5897\ \text{trimestres}}$.
     - 2021 ($t=21$): $\hat{y}(21) = 16.441713 - 0.792601(21) = \mathbf{-0.2029\ \text{trimestres}}$ (`physically_invalid = True` ya desde 2021).
     - 2027 ($t=27$): $\hat{y}(27) = 16.441713 - 0.792601(27) = \mathbf{-4.9585\ \text{trimestres}}$ (`physically_invalid = True`, una duración laboral no puede ser negativa).
     - Cruce por cero: $t_0 = \frac{16.441713}{0.792601} \approx 20.74 \implies \text{año } \mathbf{2020.74}$.
- **Análisis crítico (3 pts — 1 pt c/u):**
  - (a) Con `start_year` $\approx 2009.5$, tanto $n\sum x_i^2 \approx 1.6152 \times 10^9$ como $(\sum x_i)^2 \approx 1.6152 \times 10^9$ coinciden en sus primeros 5 dígitos significativos; al restarlos se produce **cancelación catastrófica** (y el intercepto $|a_0|$ se amplifica en millones). Centrar en $t = \text{año} - 2000$ reduce la magnitud de $\sum t^2$ y evita pérdida de precisión.
  - (b) Al excluir `es_vigente == True` (`MR-09`, coherente con `RL-01` y `LG-01`), se elimina el sesgo de empleos vigentes imputados a `2026-Q1` que inflaban artificialmente 2019 (`6.61 → 8.31`). No obstante, incluso entre empleos cerrados persiste la **censura derecha calendario**: un empleo iniciado en 2019 y ya cerrado antes del corte del dataset no pudo haber durado 10 años, generando una caída lineal mecánica (`-0.7926`/año) que impide extrapolar al futuro.
  - (c) Las pendientes casi idénticas en `raw_train`, `raw_test` y `raw_val` confirman que las particiones crudas de JobHop v2 son estadísticamente homogéneas en el tiempo y sin deriva de muestreo antes de la unificación del pipeline.
- **Verificación GeoGebra / Python (2 pts — 1 pt c/u):**
  1. `P = {(0, 18.344970), ..., (19, 2.271181)}`, `f = FitLine(P)`, `r = CorrelationCoefficient(P)`, `R2 = RSquare(P, f)`, `Centroid = (9.5, 8.912006)`, `Q_pred = (27, f(27))`. Visualmente, `Q_pred = (27, -4.9585)` cae **profundamente por debajo del eje horizontal $y=0$** (cruzando cero desde `t = 20.74`), demostrando gráficamente la invalidez física de extrapolar linealmente.
  2. Siempre centrar covariables con gran desplazamiento respecto a cero (o usar desviaciones centradas $dx = x - \bar{x}$, $dy = y - \bar{y}$ como hace `ols.py`) para ganar >3.6 órdenes de magnitud (`4,672×`) en estabilidad de punto flotante.

---

### Caso 04 — `IDEA-RL-05`: Sensibilidad a Outliers e Invarianza Afín de Escala

#### 1. Ficha Teórico-Aplicada (HTML + Proyecto)
- **Temáticas HTML evaluadas:** Sensibilidad de $S_r = \sum e_i^2$, $S_t$, $R^2$ y $S_{y/x}$ ante observaciones extremas, y comportamiento exacto de las fórmulas cerradas de MCO bajo transformaciones lineales (afines) de $x$ y $y$.
- **Rol en JobPath:** Audita cuantitativamente dos decisiones centrales de ingeniería de datos del proyecto: (1) comparar en `1,738,738` registros la winsorización IQR (`Versión B`) frente a conservar outliers (`Versión A`) y frente al borrado legado de filas (`02_interim`), y (2) verificar la integridad matemática del escalado `RobustScaler` en `04_transformed/{train,test}` (matrices de hasta 8 GB).
- **Fuentes verificadas:** [rl05_four_way_outlier_comparison.csv](../04_IDEA_RL_05_Outliers_E_Invarianza_Escala/tables/rl05_four_way_outlier_comparison.csv), [rl05_affine_scale_invariance.csv](../04_IDEA_RL_05_Outliers_E_Invarianza_Escala/tables/rl05_affine_scale_invariance.csv).

#### 2. Preguntas Conceptuales (2 puntos)
- **P4.1 (1 pt — Selección múltiple):** Si aplicamos un escalado afín tipo `RobustScaler`, $\tilde{x} = (x - c_x)/s_x$ y $\tilde{y} = (y - c_y)/s_y$ (con $s_x, s_y > 0$), ¿qué ocurre con el coeficiente de determinación $R^2$ y el error estándar $S_{y/x}$ de una regresión lineal MCO?
  - a) Ambos permanecen exactamente invariantes ($\tilde{R}^2 = R^2$ y $\tilde{S}_{y/x} = S_{y/x}$).
  - b) $R^2$ permanece **exactamente invariante** ($\tilde{R}^2 = R^2$), mientras que $S_{y/x}$ se escala inversamente con $s_y$ ($\tilde{S}_{y/x} = S_{y/x} / s_y$).
  - c) $R^2$ se divide por $s_x s_y$ y $S_{y/x}$ se multiplica por $c_y$.
  - d) Ambos cambian arbitrariamente porque `RobustScaler` no usa la media ni la desviación estándar.
- **P4.2 (1 pt — Verdadero/Falso justificado):** *«Winsorizar (recortar a los límites IQR $k=1.5$) en `Versión B` siempre mejora simultáneamente $S_{y/x}$ y $R^2$ en cualquier par de variables del dataset JobPath.»* Responda Verdadero o Falso usando evidencia numérica real de `rl05_four_way_outlier_comparison.csv`.

#### 3. Ejercicio Procedimental (3 puntos — Datos reales de `rl05_affine_scale_invariance.csv`)
En la partición `con_outliers / train` (`n = 1,391,018` registros), el ajuste MCO en escala original para `n_skills_essential ~ n_skills_competence` entrega:
- $a_{0,\text{raw}} = 1.530874$, $a_{1,\text{raw}} = 1.128372$, $R^2_{\text{raw}} = 0.907188$, $S_{y/x,\text{raw}} = 4.091719$.

El transformador `RobustScaler` del pipeline `04_transformed` usa los parámetros exactos:
- Para $x$ (`n_skills_competence`): centro $c_x = 18.0$, escala $s_x = 11.0$.
- Para $y$ (`n_skills_essential`): centro $c_y = 20.0$, escala $s_y = 13.0$.

Demuestre y calcule paso a paso:
1. A partir de $\tilde{x} = \frac{x - c_x}{s_x}$ y $\tilde{y} = \frac{y - c_y}{s_y}$, deduzca las fórmulas teóricas para $\tilde{a}_1$ y $\tilde{a}_0$.
2. Calcule los valores teóricos exactos de $\tilde{a}_1$, $\tilde{a}_0$, $\tilde{R}^2$ y $\tilde{S}_{y/x}$ (4 decimales).
3. Compare sus resultados con los observados directamente sobre `X_train.csv` en `rl05_affine_scale_invariance.csv` (`a0_scaled_obs = 0.141659`, `a1_scaled_obs = 0.954776`, `r2_scaled_obs = 0.907188`, `s_yx_scaled_obs = 0.314748`, `max_invariance_err = 4.818e-14`) e indique si pasa el umbral `< 1e-10`.

#### 4. Pregunta de Análisis Crítico y Criterio Ingenieril (3 puntos)
Examine la tabla completa de `rl05_four_way_outlier_comparison.csv`:

| Variante | $n$ | Par `competence → essential` ($a_1$ / $R^2$ / $S_{y/x}$) | Par `knowledge → essential` ($a_1$ / $R^2$ / $S_{y/x}$) |
|---|---:|---|---|
| **Ver. A** (`03_processed`, con outliers) | 1,738,738 | `1.1279` / `0.9072` / `4.0872` | `1.8827` / `0.3680` (Mod.) / `10.6664` |
| **Ver. B** (`03_processed`, IQR $k=1.5$) | 1,738,738 | `1.0868` / `0.8983` / `3.1915` | `1.6728` / `0.2795` (Rech.) / `8.4934` |
| **Legado limpio** (`02_interim`, `test+val`) | 348,263 | `1.1336` / `0.9046` / `4.1147` | `1.8806` / `0.3793` (Mod.) / `10.4969` |
| **Legado borrado** (`02_interim`, sin outliers) | 314,904 | `1.1351` / `0.9062` / `4.1105` | `1.9006` / `0.3828` (Mod.) / `10.5421` |

**Analice críticamente:** (a) ¿por qué en `knowledge → essential` la winsorización IQR **reduce $S_{y/x}$ un 20.4 %** (`10.67 → 8.49`) pero al mismo tiempo hace **caer $R^2$ por debajo del umbral de rechazo** (`0.3680 → 0.2795`)?, (b) ¿por qué la comparación de 4 vías tiene un factor de confusión muestral entre las versiones `03_processed` y las legadas `02_interim`?, y (c) ¿qué ventaja operativa tuvo la winsorización frente al borrado legado de filas (`33,359` filas perdidas, `9.58 %`)?

#### 5. Verificación en GeoGebra / Python (2 puntos)
1. Explique por qué `IDEA-RL-05` es uno de los casos **sin script `.txt` de GeoGebra** (`n = 1,738,738`) y cómo debería auditarse en Python en lugar de pegar puntos manualmente en GeoGebra.
2. Escriba un bloque breve en Python (`numpy`) que verifique simultáneamente la equivalencia con `np.polyfit(x, y, 1)` y la prueba de invarianza afín con tolerancia `< 1e-10`.

#### 6. Solucionario Detallado y Criterios de Calificación (10 puntos)
- **P4.1:** **Opción b)** (1 pt). $R^2 = 1 - S_r/S_t$ es adimensional porque tanto $S_r$ como $S_t$ se dividen por $s_y^2$, cancelándose; en cambio $S_{y/x} = \sqrt{S_r/(n-2)}$ tiene unidades de $y$, por lo que se divide por $s_y$.
- **P4.2:** **Falso** (1 pt). En `rl05_four_way_outlier_comparison.csv`, la winsorización reduce $S_{y/x}$ en ambos pares (`4.0872 → 3.1915`, -21.9 %; y `10.6664 → 8.4934`, -20.4 %), pero **reduce $R^2$ en ambos** (`0.9072 → 0.8983` y especialmente `0.3680 → 0.2795`, haciendo que `knowledge → essential` pase de Moderado a Rechazado).
- **Ejercicio procedimental (3 pts):**
  1. *(1.0 pt)* Sustituyendo $x = c_x + s_x \tilde{x}$ y $y = c_y + s_y \tilde{y}$ en $\hat{y} = a_0 + a_1 x$:
     $$c_y + s_y \hat{\tilde{y}} = a_0 + a_1(c_x + s_x \tilde{x}) \implies \hat{\tilde{y}} = \underbrace{\frac{a_0 + a_1 c_x - c_y}{s_y}}_{\tilde{a}_0} + \underbrace{\left(a_1 \frac{s_x}{s_y}\right)}_{\tilde{a}_1}\tilde{x}$$
  2. *(1.5 pts)* Cálculos exactos:
     $$\tilde{a}_1 = 1.1283715 \times \frac{11}{13} = \mathbf{0.9548}$$
     $$\tilde{a}_0 = \frac{1.5308745 + (1.1283715)(18) - 20}{13} = \frac{1.5308745 + 20.3106878 - 20}{13} = \frac{1.8415623}{13} = \mathbf{0.1417}$$
     $$\tilde{R}^2 = R^2_{\text{raw}} = \mathbf{0.9072}, \qquad \tilde{S}_{y/x} = \frac{4.0917191}{13} = \mathbf{0.3147}$$
  3. *(0.5 pt)* Coincidencia completa con los observados en `X_train.csv` (`max_invariance_err = 4.818e-14 < 1e-10`; y el máximo global de las 8 pruebas es `7.216e-14 < 1e-10`), confirmando que no existe corrupción ni fuga en `04_transformed`.
- **Análisis crítico (3 pts — 1 pt c/u):**
  - (a) La winsorización recorta `n_skills_knowledge` desde `x_max = 45.0` hasta `13.5` (y `essential` en su cola superior). Eso comprime $S_t$ casi a la mitad (`312.99M → 174.09M`, -44.4 %) mientras $S_r$ cae solo -36.6 % (`197.82M → 125.43M`), por lo que la fracción explicada $1 - S_r/S_t$ disminuye aunque el error absoluto típico $S_{y/x}$ mejore.
  - (b) Las variantes legadas (`02_interim`) contienen solo `test+val` (`348k`/`315k` filas) mientras `Versión A` y `Versión B` cubren el universo completo `train+test+val` (`1.74M` filas); por tanto, las pequeñas diferencias entre `Ver. A` y `Legado limpio` mezclan efecto de partición con efecto de limpieza.
  - (c) La winsorización preserva el 100 % de los registros (`1,738,738`) sin amputar perfiles profesionales especializados de alta cualificación (que el borrado legado eliminó en un `9.58 %`), evitando sesgo de truncamiento en las trayectorias.
- **Verificación GeoGebra / Python (2 pts — 1 pt c/u):**
  1. GeoGebra Classic en navegador no escala interactivamente a 1.74 millones de puntos; por ello la verificación se ejecuta vía código en Python sobre lectura eficiente de columnas (`loaders.py`) y pruebas automatizadas (`test_affine_scaling_invariance`, `test_rl05_outlier_audit_and_affine_invariance`).
  2. Snippet mínimo válido: calcular `(a1_np, a0_np) = np.polyfit(x, y, 1)`, escalar `xs = (x - cx)/sx`, `ys = (y - cy)/sy`, ajustar `(a1s, a0s) = np.polyfit(xs, ys, 1)`, y comprobar `assert max(abs(a1s - a1*sx/sy), abs(a0s - (a0 + a1*cx - cy)/sy)) < 1e-10`.

---

### Caso 05 — `IDEA-LG-01`: Curva de Supervivencia Laboral $S(q)$ y Fenómeno de Runge

#### 1. Ficha Teórico-Aplicada (HTML + Proyecto)
- **Temáticas HTML evaluadas:** Teorema de existencia y unicidad ($n+1$ nodos $\implies$ grado $\le n$), polinomios base $L_i(x)$, delta de Kronecker ($L_i(x_i)=1$, $L_i(x_j)=0$), partición de la unidad ($\sum L_i(x)=1$), error típico del denominador, peligro de extrapolación, **Fenómeno de Runge** con nodos equiespaciados, mitigación con **nodos de Chebyshev** y **polinomios de grado bajo por tramos**, y verificación `Polynomial(P)` en GeoGebra.
- **Rol en JobPath:** Reconstruye la probabilidad empírica de permanencia laboral $S(q) = P(\text{dur\_q} \ge q)$ sobre `1,643,772` empleos **estrictamente cerrados** (`~es_vigente`) a partir de 4 hitos ejecutivos ($q = 4, 8, 20, 40$ trimestres) y demuestra el Fenómeno de Runge directamente sobre datos reales del mercado laboral (grados 3 a 16).
- **Fuentes verificadas:** [lg01_survival_curve_S_q.csv](../05_IDEA_LG_01_Supervivencia_Y_Runge/tables/lg01_survival_curve_S_q.csv), [lg01_milestone_P3_weights_and_eval.csv](../05_IDEA_LG_01_Supervivencia_Y_Runge/tables/lg01_milestone_P3_weights_and_eval.csv), [lg01_runge_phenomenon_benchmark.csv](../05_IDEA_LG_01_Supervivencia_Y_Runge/tables/lg01_runge_phenomenon_benchmark.csv), [ggb_lg01_survival_p3_milestones.txt](../05_IDEA_LG_01_Supervivencia_Y_Runge/geogebra/ggb_lg01_survival_p3_milestones.txt).

#### 2. Preguntas Conceptuales (2 puntos)
- **P5.1 (1 pt — Selección múltiple):** Para interpolar la curva de supervivencia $S(q)$ con los 4 hitos $q \in \{4, 8, 20, 40\}$, ¿qué grado máximo tiene $P(q)$ y cuánto vale exactamente $L_1(20)$?
  - a) Grado 4; $L_1(20) = 1$.
  - b) Grado $\le 3$; $L_1(20) = 0$, porque toda base $L_i$ vale 1 en su propio nodo ($q_1 = 8$) y se anula en los demás nodos ($q_0=4, q_2=20, q_3=40$).
  - c) Grado $\le 3$; $L_1(20) = S(20) = 0.1358$.
  - d) Grado exactamente 2; $L_1(20) = -1$.
- **P5.2 (1 pt — Selección múltiple):** En `lg01_runge_phenomenon_benchmark.csv`, al subir el grado del interpolador global con nodos equiespaciados de `grado 5` a `grado 16` (17 nodos), el error máximo $E_\infty$ se dispara de `0.1301` a `2.5262` (produciendo `min_pred = -2.4827`). Según el HTML de Lagrange, ¿qué fenómeno ocurre y cuáles son las dos mitigaciones recomendadas?
  - a) Cancelación de residuos; se corrige sumando los errores absolutos.
  - b) Fenómeno de Runge (oscilación severa cerca de los extremos al aumentar el grado con nodos equiespaciados); se mitiga usando **nodos de Chebyshev** (agrupados hacia los extremos) o **interpolación de grado bajo por tramos** (splines / Lagrange local $P_2$).
  - c) Violación del teorema de unicidad; se corrige repitiendo el nodo $q=1$ dos veces.
  - d) Overfitting lineal; se corrige reemplazando `Polynomial(P)` por `FitLine(P)`.

#### 3. Ejercicio Procedimental (3 puntos — Datos reales de `lg01_milestone_P3_weights_and_eval.csv`)
Con los 4 hitos exactos de supervivencia laboral (`1,643,772` empleos cerrados):

| $i$ | $q_i$ (trimestres) | Años | $y_i = S(q_i)$ |
|---:|---:|---:|---:|
| 0 | 4 | 1.0 | 0.660880 |
| 1 | 8 | 2.0 | 0.370539 |
| 2 | 20 | 5.0 | 0.135783 |
| 3 | 40 | 10.0 | 0.042983 |

Calcule paso a paso:
1. Los denominadores exactos de $L_0(q), L_1(q), L_2(q)$ y $L_3(q)$ (aplicando la verificación del HTML: el denominador es el numerador evaluado en $q_i$).
2. Los pesos $L_0(12), L_1(12), L_2(12), L_3(12)$ para estimar la supervivencia a los **3 años** ($q = 12$) y verifique la propiedad de partición de la unidad $\sum_{i=0}^{3} L_i(12) = 1$.
3. El valor interpolado $P_3(12)$ y su error absoluto frente a la supervivencia empírica real $S(12) = 0.251949$.
4. Comente el resultado de extrapolar este mismo polinomio a **12 años** ($q = 48$): en la tabla CSV, $L(48) = [-3.8889, +6.4167, -3.6667, +2.1389]$ y $P_3(48) = -0.5984$ (vs. $S(48) = 0.0292$). ¿Qué revela el crecimiento de magnitud de los pesos $L_i(48)$?

#### 4. Pregunta de Análisis Crítico y Criterio Ingenieril (3 puntos)
Analice tres hallazgos profundos observables en `lg01_survival_curve_S_q.csv`, `lg01_milestone_P3_weights_and_eval.csv` y `lg01_runge_phenomenon_benchmark.csv`:
1. **No-monotonicidad dentro del intervalo:** Aunque $S(q)$ es matemáticamente decreciente, el polinomio $P_3(q)$ predice `0.1384` en $q=16$ y luego **sube** a `0.2058` en $q=28$ (más de 2.5× el valor real `0.0804`) y `0.1734` en $q=36$ (3.3× el valor real `0.0520`). ¿Por qué un polinomio cúbico exacto en 4 nodos puede violar la monotonicidad de una función de supervivencia?
2. **Escalones anuales (*annual heaping*):** En `lg01_survival_curve_S_q.csv`, $S(1)=S(2)=1.0$ y la curva cae en escalones abruptos cada 4 trimestres ($q=3, 6, 10, 14, 18, 22\dots$). ¿Cómo explica esta falta de suavidad que incluso **Chebyshev-Lobatto** (`0.1301` en grado 16) y **Local $P_2$** (`0.1196` en grado 12; `0.1843` en grado 16) mantengan un piso de error $E_\infty \in [0.12, 0.18]$?
3. **Nodos Chebyshev de 1.ª especie vs. Chebyshev-Lobatto (`cos(kπ/n)`):** ¿Por qué usar nodos de **Chebyshev-Lobatto** (2.ª especie, que anclan exactamente los extremos $q=1$ y $q=40$) en `lg01_runge_phenomenon_benchmark.csv` logra **`0` violaciones de `[0, 1]` en los 5 grados (`3, 5, 8, 12, 16`)**, corrigiendo la anomalía que producían los nodos de 1.ª especie en grados bajos (`deg=3, 5` donde extrapolaban en $q=1$ por encima de `1.11–1.23`)?

#### 5. Verificación en GeoGebra / Python (2 puntos)
1. A partir de [ggb_lg01_survival_p3_milestones.txt](../05_IDEA_LG_01_Supervivencia_Y_Runge/geogebra/ggb_lg01_survival_p3_milestones.txt) y [lg_monomial_expansions.csv](../05_IDEA_LG_01_Supervivencia_Y_Runge/tables/lg_monomial_expansions.csv), explique cómo verifica en GeoGebra que la construcción manual $p(x) = \sum y_i L_i(x)$ es idéntica tanto al comando nativo `q = Polynomial(P)` (`Polinomio(P)`) como a la forma monómica explícita $-7.91\times 10^{-5} q^3 + 0.005845 q^2 - 0.133867 q + 1.107889$, y cómo comprobar visualmente que $L_i(q_j) = \delta_{ij}$.
2. En `verification_log.md`, la comparación `LG-01 P3` vs. `scipy.interpolate.lagrange` reporta `5.052e-15`, Kronecker `0.000e+00` y partición de la unidad `4.441e-16`. ¿Qué representa cada una de estas tres métricas?

#### 6. Solucionario Detallado y Criterios de Calificación (10 puntos)
- **P5.1:** **Opción b)** (1 pt). Con 4 puntos ($n+1=4$) el polinomio único tiene grado $\le 3$, y por la delta de Kronecker $L_1(q_2) = L_1(20) = 0$.
- **P5.2:** **Opción b)** (1 pt). Con grado 16, Chebyshev-Lobatto reduce $E_\infty$ de `2.5262` a **`0.1301`** (reducción de **`19.4×`**) y mantiene **`0` violaciones de `[0, 1]` en TODOS los grados (3 a 16)**.
- **Ejercicio procedimental (3 pts):**
  1. *(0.75 pt)* Denominadores:
     - $D_0 = (4-8)(4-20)(4-40) = (-4)(-16)(-36) = \mathbf{-2304}$
     - $D_1 = (8-4)(8-20)(8-40) = (4)(-12)(-32) = \mathbf{+1536}$
     - $D_2 = (20-4)(20-8)(20-40) = (16)(12)(-20) = \mathbf{-3840}$
     - $D_3 = (40-4)(40-8)(40-20) = (36)(32)(20) = \mathbf{+23040}$
  2. *(1.0 pt)* Evaluación en $q = 12$:
     - $L_0(12) = \frac{(4)(-8)(-28)}{-2304} = -\frac{7}{18} \approx \mathbf{-0.3889}$
     - $L_1(12) = \frac{(8)(-8)(-28)}{1536} = +\frac{7}{6} \approx \mathbf{+1.1667}$
     - $L_2(12) = \frac{(8)(4)(-28)}{-3840} = +\frac{7}{30} \approx \mathbf{+0.2333}$
     - $L_3(12) = \frac{(8)(4)(-8)}{23040} = -\frac{1}{90} \approx \mathbf{-0.0111}$
     - Verificación: $-\frac{7}{18} + \frac{7}{6} + \frac{7}{30} - \frac{1}{90} = \frac{-35 + 105 + 21 - 1}{90} = \frac{90}{90} = \mathbf{1}$ ✔.
  3. *(0.75 pt)* Valor interpolado:
     $$P_3(12) = 0.660880(-0.388889) + 0.370539(1.166667) + 0.135783(0.233333) + 0.042983(-0.011111) = \mathbf{0.2065}$$
     Error absoluto $= |0.206491 - 0.251949| = \mathbf{0.0455}$ (4.55 puntos porcentuales).
  4. *(0.5 pt)* En $q = 48$ (extrapolación), los pesos $L_i$ siguen sumando 1 pero sus magnitudes crecen con signos alternados (`-3.89, +6.42, -3.67, +2.14`), amplificando violentamente la curvatura hasta producir una probabilidad negativa imposible (`-0.5984`, error `0.6276`).
- **Análisis crítico (3 pts — 1 pt c/u):**
  1. Un polinomio de Lagrange no impone restricciones de forma (ni monotonicidad ni acotación en $[0,1]$). La fuerte caída inicial entre $q=4$ y $q=8$ seguida de una cola casi plana hasta $q=40$ obliga a la cúbica ($c_3 = -7.9099\times 10^{-5}, c_2 = +5.8451\times 10^{-3}, c_1 = -0.133867, c_0 = 1.107889$) a "rebotar" al alza entre $q=20$ y $q=40$ para pasar por los 4 nodos.
  2. El redondeo anual en las fechas declaradas en hojas de vida (*annual heaping*) crea discontinuidades tipo escalón cada 4 trimestres. La teoría de aproximación polinomial requiere derivadas acotadas (suavidad); ante saltos bruscos, ni siquiera Chebyshev-Lobatto o $P_2$ eliminan el error local cerca de los escalones.
  3. Los nodos de Chebyshev de 1.ª especie son estrictamente interiores a $[1, 40]$, lo que en grados bajos (`deg=3, 5`) obligaba a **extrapolar** al evaluar en $q=1$ produciendo valores $>1$. Al cambiar a **Chebyshev-Lobatto** ($\cos(k\pi/n)$), los extremos exactos $q=1$ y $q=40$ quedan siempre incluidos como nodos de interpolación en todos los grados, eliminando toda extrapolación de borde y logrando **`0` violaciones de `[0,1]`** en `deg = 3, 5, 8, 12, 16`.
- **Verificación GeoGebra / Python (2 pts — 1 pt c/u):**
  1. Definir `P = {(4, 0.660880), (8, 0.370539), (20, 0.135783), (40, 0.042983)}`, cada `L0(x)..L3(x)`, `p(x)` y `q = Polynomial(P)`: ambas curvas se superponen exactamente en pantalla (por unicidad). Activando/desactivando cada `L_i(x)` en la Vista Algebraica se observa que cruza $y=1$ en su nodo $q_i$ y $y=0$ en los otros tres.
  2. `5.052e-15`: discrepancia máxima entre el motor propio y `scipy.interpolate.lagrange`; `0.000e+00`: cumplimiento exacto de $\max_{i,j}|L_i(q_j)-\delta_{ij}|$; `4.441e-16`: desviación máxima de $\sum L_i(q) = 1$ (equivalente a ~2 veces `eps` de `float64`).

---

### Caso 06 — `IDEA-LG-02`: Varianza Acumulada de PCA — Lagrange Directo e Inverso

#### 1. Ficha Teórico-Aplicada (HTML + Proyecto)
- **Temáticas HTML evaluadas:** Condición indispensable del teorema de unicidad (**nodos $x_i$ estrictamente distintos**), construcción de $P_3(x)$ y bases $L_i(x)$, partición de la unidad $\sum L_i = 1$, ventaja/desventaja de agregar nodos en Lagrange, y verificación en GeoGebra con `Polynomial(P)`.
- **Rol en JobPath:** Resuelve el problema de dimensionamiento efectivo del **PCA sobre la muestra 50k (`4.1_PCA_completo.ipynb`)** tanto en forma directa ($V(k)$ desde 4 nodos dispersos $k=\{1,3,5,8\}$) como en forma **inversa** ($\hat{k}(V^*)$ para metas de varianza del 80 %, 85 %, 90 % y 95 % en Versiones A y B), comprobando la ruptura de rango exacto entre ambas versiones.
- **Fuentes verificadas:** [lg02_pca_50k_reference.csv](../06_IDEA_LG_02_PCA_Lagrange_Inversa/tables/lg02_pca_50k_reference.csv), [lg02_pca_forward_P3_eval.csv](../06_IDEA_LG_02_PCA_Lagrange_Inversa/tables/lg02_pca_forward_P3_eval.csv), [lg02_pca_inverse_effective_dim.csv](../06_IDEA_LG_02_PCA_Lagrange_Inversa/tables/lg02_pca_inverse_effective_dim.csv), [ggb_lg02_pca_forward_p3.txt](../06_IDEA_LG_02_PCA_Lagrange_Inversa/geogebra/ggb_lg02_pca_forward_p3.txt).

#### 2. Preguntas Conceptuales (2 puntos)
- **P6.1 (1 pt — Selección múltiple):** En la interpolación **inversa** de Lagrange $\hat{k}(V^*)$ sobre la Versión A (`con_outliers`), se toman los valores de varianza acumulada $V(k)$ como nodos horizontales y $k$ como ordenadas. ¿Por qué falla matemáticamente intentar construir el polinomio inverso incluyendo los 10 puntos ($k=1..10$), donde $V_A(9) = 1.0$ y $V_A(10) = 1.0$?
  - a) Porque $P_9$ siempre tiene error mayor que 100 %.
  - b) Porque se viola la hipótesis de **nodos estrictamente distintos** del teorema de Lagrange: al ser $V_A(9) = V_A(10) = 1.0$, el denominador $(x_i - x_j) = (1.0 - 1.0) = 0$ produce división por cero (disparando la guarda `MR-04`).
  - c) Porque la interpolación inversa solo funciona cuando $k$ es par.
  - d) Porque los polinomios base $L_i$ solo admiten valores positivos de $x_i > 1$.
- **P6.2 (1 pt — Verdadero/Falso justificado):** *«Si el equipo de JobPath decide agregar el nodo $k=6$ a los 4 nodos originales $k=\{1, 3, 5, 8\}$ usando la fórmula de Lagrange para pasar de $P_3(k)$ a $P_4(k)$, puede reutilizar sin cambios los cuatro polinomios base $L_0, L_1, L_2, L_3$ ya calculados y simplemente sumar un quinto término $y_4 L_4(k)$.»* Responda Verdadero o Falso y justifique según el HTML de Lagrange (diapositivas 5 y 15).

#### 3. Ejercicio Procedimental (3 puntos — Datos reales de `lg02_pca_50k_reference.csv` y `lg02_pca_forward_P3_eval.csv`)
Con los 4 nodos dispersos de varianza acumulada de PCA en **Versión A (`con_outliers`)**:

| $i$ | $k_i$ (componentes) | $V_A(k_i)$ |
|---:|---:|---:|
| 0 | 1 | 0.3291052 |
| 1 | 3 | 0.7658773 |
| 2 | 5 | 0.9406563 |
| 3 | 8 | 0.9999543 |

Calcule paso a paso:
1. Los polinomios base evaluados en $k = 4$: $L_0(4), L_1(4), L_2(4), L_3(4)$ (como fracción exacta y decimal) y compruebe $\sum_{i=0}^{3} L_i(4) = 1$.
2. La varianza acumulada interpolada $P_3(4)$ y su error absoluto frente al valor real del PCA `V_A(4) = 0.8776043`.
3. A partir de `lg02_pca_inverse_effective_dim.csv`, compare las estimaciones inversas para la meta $V^* = 0.95$:
   - Versión A (`con_outliers`): $\hat{k}_{\text{local } P_2} = 5.1643$, $\hat{k}_{\text{global } P_5} = 5.1693 \implies k_{\text{rec}} = \lceil \hat{k} \rceil = 6$ ($V_A(6) = 0.9943$).
   - Versión B (`sin_outliers`): $\hat{k}_{\text{local } P_2} = 4.9227$, $\hat{k}_{\text{global } P_5} = 4.9278 \implies k_{\text{rec}} = \lceil \hat{k} \rceil = 5$ ($V_B(5) = 0.9536$).  
   Explique por qué se aplica la función techo $\lceil \cdot \rceil$ y por qué la Versión B alcanza el 95 % con **un componente menos** que la Versión A.

#### 4. Pregunta de Análisis Crítico y Criterio Ingenieril (3 puntos)
Evalúe críticamente dos aspectos de ingeniería y modelado del Caso 06:
1. **Colinealidad exacta vs. winsorización:** En `lg02_pca_50k_reference.csv` (recalculado en vivo en precisión completa `float64`), la varianza marginal del 10.º componente es `6.74e-18` (cero de máquina `float64`, rango efectivo 9 debido a la identidad exacta $E = C + K + U$) en Versión A (`con_outliers`), mientras que en Versión B (`sin_outliers`) aparece una varianza marginal no nula de `5.534e-05` en `PC10`. ¿Por qué la winsorización IQR independiente por columna rompe esa relación lineal exacta?
2. **Trazabilidad en vivo vs. constantes hardcodeadas:** En la versión corregida V2 de `experiments_lagrange.py`, se eliminó la tabla literal `VERIFIED_PCA_50K` y ahora `run_lg02_pca_curves` recalcula el PCA 50k **en vivo desde `data/03_processed/` en `float64`** (`pca_source = live_50k_from_03_processed_float64`, replicando exactamente `4.1_PCA_completo.ipynb`). ¿Qué riesgo de reproducibilidad eliminó este cambio en el pipeline?

#### 5. Verificación en GeoGebra / Python (2 puntos)
1. Escriba los comandos de [ggb_lg02_pca_forward_p3.txt](../06_IDEA_LG_02_PCA_Lagrange_Inversa/geogebra/ggb_lg02_pca_forward_p3.txt), cite la forma monómica explícita de [lg_monomial_expansions.csv](../06_IDEA_LG_02_PCA_Lagrange_Inversa/tables/lg_monomial_expansions.csv) (`0.002746k³ - 0.057466k² + 0.412549k - 0.028723`) y señale el valor esperado en `A_eval = (4, p(4))`.
2. Explique qué pruebas automatizadas del repositorio (`test_distinct_node_and_monotonic_inverse_guards`, `test_lg02_pca_forward_inverse_and_plateau` y `test_lg_monomial_expansions_and_live_pca_precision`) validan tanto la guarda `MR-04` como la precisión `float64` en vivo.

#### 6. Solucionario Detallado y Criterios de Calificación (10 puntos)
- **P6.1:** **Opción b)** (1 pt). Sin nodos $x_i$ estrictamente distintos el polinomio de Lagrange no está definido (división por cero en $x_i - x_j$). La solución correcta es restringir la inversión al tramo estrictamente creciente $k = 1..6$.
- **P6.2:** **Falso** (1 pt). Como señala explícitamente la diapositiva 5 del HTML de Lagrange, la principal **desventaja** del método de Lagrange es que al agregar un punto nuevo hay que **recalcular todos los $L_i(x)$** (porque cada producto añade un nuevo factor $(x - x_4)/(x_i - x_4)$). Para agregar puntos incrementalmente se usan **diferencias divididas de Newton** (diapositiva 15).
- **Ejercicio procedimental (3 pts):**
  1. *(1.25 pts)* Denominadores: $D_0 = (-2)(-4)(-7) = -56$; $D_1 = (2)(-2)(-5) = 20$; $D_2 = (4)(2)(-3) = -24$; $D_3 = (7)(5)(3) = 105$.  
     Evaluando en $k = 4$:
     - $L_0(4) = \frac{(1)(-1)(-4)}{-56} = -\frac{1}{14} \approx \mathbf{-0.0714}$
     - $L_1(4) = \frac{(3)(-1)(-4)}{20} = +\frac{3}{5} = \mathbf{+0.6000}$
     - $L_2(4) = \frac{(3)(1)(-4)}{-24} = +\frac{1}{2} = \mathbf{+0.5000}$
     - $L_3(4) = \frac{(3)(1)(-1)}{105} = -\frac{1}{35} \approx \mathbf{-0.0286}$
     - Suma: $-\frac{1}{14} + \frac{3}{5} + \frac{1}{2} - \frac{1}{35} = \frac{-5 + 42 + 35 - 2}{70} = \frac{70}{70} = \mathbf{1}$ ✔.
  2. *(1.0 pt)*
     $$P_3(4) = 0.3291052\left(-\frac{1}{14}\right) + 0.7658773(0.6) + 0.9406563(0.5) + 0.9999543\left(-\frac{1}{35}\right)$$
     $$P_3(4) = -0.023508 + 0.459526 + 0.470328 - 0.028570 = \mathbf{0.8778}\ \text{(exacto: } 0.877777\text{)}$$
     Error absoluto $= |0.877777 - 0.877604| = \mathbf{0.000173}$ (apenas `0.017 %`).
  3. *(0.75 pt)* Como el número de componentes principales debe ser entero y garantizar **al menos** el umbral $V^*$, se toma el entero superior $\lceil \hat{k} \rceil$ (en 8/8 pruebas `meets_target = True`). La Versión B requiere 5 componentes en vez de 6 porque recortar outliers concentra la varianza en las primeras dimensiones (`V_B(5) = 0.9536 > 0.95`, mientras `V_A(5) = 0.9407 < 0.95`).
- **Análisis crítico (3 pts — 1.5 pts c/u):**
  1. El recorte IQR se aplica **univariadamente** a cada columna; cuando un registro supera el tope superior en una variable pero no en los sumandos restantes, se rompe la suma exacta $E = C + K + U$, devolviendo rango completo (10) con una varianza residual diminuta en `PC10` (`5.534e-05`), frente al cero numérico de Versión A (`6.74e-18`).
  2. Recalcular el PCA 50k en vivo desde `03_processed` con semilla fija (`random_state=42`) garantiza trazabilidad de extremo a extremo (si los datos procesados cambiaran, `LG-02` reflejaría automáticamente el cambio) y elimina la pérdida de precisión por redondeo a 6–7 decimales de tablas hardcodeadas.
- **Verificación GeoGebra / Python (2 pts — 1 pt c/u):**
  1. `P = {(1, 0.329105), (3, 0.765877), (5, 0.940656), (8, 0.999954)}`, `L0(x)..L3(x)`, `p(x)`, `q = Polynomial(P)`, `A_eval = (4, p(4))` → espera `0.877777` (idéntico a evaluar el monomio $0.002746(64) - 0.057466(16) + 0.412549(4) - 0.028723$).
  2. Al pasar la serie completa de Versión A (`V_A(9) = V_A(10) = 1.0`) a `inverse_lagrange_eval`, la guarda `MR-04` lanza exactamente `ValueError: Interpolation nodes x_i must be strictly distinct (min gap = 0.000e+00 < 1.0e-12)`, y `test_lg_monomial_expansions_and_live_pca_precision` verifica en `lg02_pca_50k_reference.csv` que `marginal_var_version_a[10] < 1e-12` y `marginal_var_version_b[10] > 1e-5`.

---

### Caso 07 — `IDEA-HYB-01`: Laboratorio Comparativo "¿Interpolar o Ajustar?"

#### 1. Ficha Teórico-Aplicada (HTML + Proyecto)
- **Temáticas HTML evaluadas:** Diapositiva 2 de ambos HTML (*¿Pasar por todos los puntos… o capturar la tendencia?*), datos con ruido vs. tabla exacta, contraste directo entre MCO, Lagrange global equiespaciado, nodos de Chebyshev y polinomios de grado bajo por tramos, y comportamiento en interpolación interior vs. extrapolación.
- **Rol en JobPath:** Sintetiza los 6 casos previos enfrentando los **4 métodos** sobre **4 regímenes reales de JobPath** bajo validación cruzada *Leave-One-Out* interior (**LOOCV**) y extrapolación controlada a +2 pasos, produciendo una rúbrica empírica de selección de método.
- **Fuentes verificadas:** [hyb01_loocv_and_extrapolation_matrix.csv](../07_IDEA_HYB_01_Laboratorio_Interpolar_vs_Ajustar/tables/hyb01_loocv_and_extrapolation_matrix.csv), [hyb01_method_selection_rubric.csv](../07_IDEA_HYB_01_Laboratorio_Interpolar_vs_Ajustar/tables/hyb01_method_selection_rubric.csv).

#### 2. Preguntas Conceptuales (2 puntos)
- **P7.1 (1 pt — Selección múltiple):** ¿Por qué en `IDEA-HYB-01` el error dentro del rango se mide mediante **LOOCV interior** (dejando fuera un punto interior a la vez y prediciéndolo con el resto) en lugar de evaluar el error sobre los mismos nodos de entrenamiento?
  - a) Porque MCO siempre tiene error cero en los nodos de entrenamiento.
  - b) Porque todo polinomio de Lagrange pasa **exactamente** por los nodos de entrenamiento ($e_i = 0$ por definición), lo cual ocultaría sus oscilaciones entre nodos; LOOCV interior mide la capacidad real de estimación en puntos intermedios no vistos.
  - c) Porque LOOCV elimina automáticamente el Fenómeno de Runge.
  - d) Porque `scipy` no permite evaluar polinomios en los nodos originales.
- **P7.2 (1 pt — Selección múltiple):** Según `hyb01_method_selection_rubric.csv`, ¿en cuál de los 4 regímenes de JobPath gana **Lagrange Global Equiespaciado** en LOOCV interior y por qué?
  - a) En la curva de supervivencia $S(q)$ (`n=36`), porque tiene más nodos.
  - b) En la tabla cóncava exacta `PCA V(k)` Versión B (`n=8`, LOOCV RMSE = `0.0036`), porque tiene pocos nodos, es una función matemática suave y exacta sin ruido de muestreo, y en cambio MCO comete alto sesgo de curvatura (`RMSE = 0.0765`).
  - c) En la serie anual `mean_skills(year)` (`n=18`), porque su error es `12.3239`.
  - d) Nunca gana en ningún régimen.

#### 3. Ejercicio Procedimental (3 puntos — Datos reales de `hyb01_loocv_and_extrapolation_matrix.csv`)
Con base en los resultados exactos del torneo 4×4 (con nodos **Chebyshev-Lobatto**):

| Régimen (`n_train`, `ols_r2`) | Método | LOOCV RMSE | Extrap. +2 pasos MAE | Rank LOOCV | Rank Extrap. |
|---|---|---:|---:|---:|---:|
| **1. Pasos carrera** `mean_skills(k)` (`n=10`, `0.9955`) | MCO | 0.0558 | 0.0745 | 1 | 1 |
| | Local $P_2$ | 0.0888 | 0.4341 | 2 | 2 |
| | Chebyshev-Lobatto | 0.0985 | 1.9159 | 3 | 3 |
| | Lagrange Global | 0.2937 | 71.2822 | 4 | 4 |
| **2. Serie curva anual** `mean_skills(year)` (`n=18`, `0.8995`) | Local $P_2$ | 0.1139 | 0.1711 | 1 | 1 |
| | Chebyshev-Lobatto | 0.1250 | 0.7216 | 2 | 2 |
| | MCO | 0.2396 | 0.9285 | 3 | 3 |
| | Lagrange Global | 12.3239 | 386.3603 | 4 | 4 |
| **3. Supervivencia** $S(q)$ (`n=36`, `0.6935`) | Local $P_2$ | 0.0524 | 0.0060 | 1 | 1 |
| | Chebyshev-Lobatto | 0.0620 | 0.6673 | 2 | 3 |
| | MCO | 0.1301 | 0.2032 | 3 | 2 |
| | Lagrange Global | 0.3777 | 38.8875 | 4 | 4 |
| **4. PCA Ver. B** $V(k)$ (`n=8`, `0.7964`) | Lagrange Global | 0.0036 | 0.2423 | 1 | 4 |
| | Local $P_2$ | 0.0108 | 0.0068 | 2 | 1 |
| | Chebyshev-Lobatto | 0.0111 | 0.1741 | 3 | 2 |
| | MCO | 0.0765 | 0.2264 | 4 | 3 |

Calcule y responda:
1. El factor de degradación (cociente `peor / mejor`) en LOOCV RMSE para los Regímenes 1, 2 y 4.
2. El factor de explosión en extrapolación a +2 pasos de **Lagrange Global** frente al mejor método en el Régimen 1 (`71.2822 / 0.0745`) y en el Régimen 3 (`38.8875 / 0.0060`).
3. A partir de la tabla, formule una **regla de decisión de 3 ramas** (cuándo usar MCO, cuándo Lagrange Global y cuándo Lagrange Local $P_2$ / Chebyshev-Lobatto).

#### 4. Pregunta de Análisis Crítico y Criterio Ingenieril (3 puntos)
Examine tres aspectos metodológicos clave de `comparison.py` (`IDEA-HYB-01`):
1. **¿Por qué el Régimen 2 se renombró de "Serie Macro Ruidosa" a "Serie Macro Curva con Fluctuación" (`2. Curved Macro Series`)?** En `mean_skills(2000..2017)` ($R^2 = 0.8995$), MCO queda **3.º** tanto en LOOCV (`0.2396`) como en extrapolación (`0.9285`), detrás de Local $P_2$ (`0.1139` / `0.1711`) y Chebyshev-Lobatto (`0.1250` / `0.7216`). Observe `rl04_annual_macro_series.csv`: ¿qué forma geométrica real tiene la serie `2000–2019` que explica este resultado?
2. **Desempate en el Régimen 4 con Chebyshev-Lobatto:** Al sustituir Chebyshev de 1.ª especie por **Chebyshev-Lobatto**, en el Régimen 4 (`n=8`) la extrapolación +2 pasos de Chebyshev-Lobatto pasó a `0.1741` (Rank #2) frente a `0.2423` de Lagrange Global (Rank #4), y en el Régimen 1 bajó de `19.55` a `1.92`. ¿Por qué el cambio de malla eliminó el empate que existía con 1.ª especie?
3. **Tope de grado 12 documentado:** En los Regímenes 2 (`n=18`) y 3 (`n=36`), `comparison.py` acota el grado máximo de Lagrange Global y Chebyshev-Lobatto a `degree <= 12` (`13` nodos) en lugar de usar grado 35, ahora documentado explícitamente en el entregable. ¿Por qué es necesario transparentar este límite para interpretar justamente el benchmark?

#### 5. Verificación en GeoGebra / Python (2 puntos)
1. Explique cómo replicaría conceptualmente en GeoGebra la comparación visual de la diapositiva 2 (*Solo datos* → *Interpolar con `Polynomial(P)`* → *Ajustar con `FitLine(P)`*) sobre los 10 puntos de `IDEA-RL-01` para demostrar la explosión en $k=12$ (`71.28` vs `0.023`).
2. Indique qué prueba de integración (`tests/metodos_numericos/test_pipeline_integration.py`) verifica automáticamente la matriz 4×4 de `IDEA-HYB-01`.

#### 6. Solucionario Detallado y Criterios de Calificación (10 puntos)
- **P7.1:** **Opción b)** (1 pt). En los nodos de entrenamiento el error de Lagrange es idénticamente 0; evaluar con LOOCV interior revela las oscilaciones entre nodos y permite comparar justamente con MCO.
- **P7.2:** **Opción b)** (1 pt). La curva PCA tiene pocos puntos (`n=8`), es determinista, suave y fuertemente cóncava, por lo que una recta MCO sufre severo subajuste (`0.0765`) mientras Lagrange Global logra `0.0036`.
- **Ejercicio procedimental (3 pts — 1 pt c/u):**
  1. Factores de degradación en LOOCV RMSE:
     - Régimen 1: $0.293668 / 0.055822 = \mathbf{5.26\times}$ (Lagrange Global vs. MCO).
     - Régimen 2: $12.323899 / 0.113939 = \mathbf{108.16\times}$ (Lagrange Global vs. Local $P_2$).
     - Régimen 4: $0.076464 / 0.003644 = \mathbf{20.98\times}$ (MCO vs. Lagrange Global).
  2. Factores de explosión en extrapolación (+2 pasos):
     - Régimen 1: $71.282153 / 0.074520 = \mathbf{956.55\times}$ peor que MCO.
     - Régimen 3: $38.887515 / 0.005988 = \mathbf{6494.5\times}$ peor que Local $P_2$.
  3. Regla de decisión (3 ramas): (i) **MCO** cuando la tendencia es lineal o casi lineal ($R^2$ alto y sin curvatura sistemática) o cuando se requiere extrapolación conservadora de tendencia; (ii) **Lagrange Global** solo en tablas exactas, suaves y de **pocos nodos** ($n \le 8$) estrictamente dentro del rango; (iii) **Lagrange Local $P_2$ / Chebyshev-Lobatto** cuando la curva es no lineal o tiene muchos nodos ($n > 10$), destacando **Local $P_2$** como ganador absoluto en Regímenes 2 y 3 (LOOCV y +2) y en extrapolación del Régimen 4 (`0.0068`).
- **Análisis crítico (3 pts — 1 pt c/u):**
  1. Al recortar `2000–2017`, `mean_skills(año)` no es ruido puro sobre una recta sino una **curva suave en arco/campana** (crece de `22.27` en 2000 hasta un pico de `24.27` en 2015–2016 y luego desciende en 2017–2019 a `24.07 → 23.79 → 23.32`). Una recta MCO deja sesgo de curvatura y sigue subiendo en 2018–2019, mientras $P_2$ captura el giro suavemente.
  2. Con Chebyshev de 1.ª especie redondeado a enteros sobre `{1..8}`, los 8 nodos colapsaban exactamente al conjunto completo `{1..8}` (produciendo el mismo polinomio de grado 7 que Global). Con **Chebyshev-Lobatto**, la compresión en los extremos agrupa nodos repetidos que al deduplicarse producen un subconjunto de menor grado bien condicionado (sin empate: `0.1741` vs `0.2423`, y en Régimen 1 reduce el error de extrapolación de `19.55` a `1.92`).
  3. Truncar el grado global a `<= 12` (`13` nodos) evita un desbordamiento aún mayor en `n=36` (grado 35), pero cambia la definición de "Global" respecto a usar todos los nodos disponibles; declararlo explícitamente garantiza rigor metodológico.
- **Verificación GeoGebra / Python (2 pts — 1 pt c/u):**
  1. Con `P = {(1, 22.693871), ..., (10, 24.764899)}`, ejecutar `f = FitLine(P)` y `g = Polynomial(P)` (polinomio de grado 9). Entre $x=1$ y $x=10$ ambas curvas parecen cercanas, pero al evaluar `f(12)` vs. `g(12)` se observa visualmente cómo `g` diverge explosivamente fuera del soporte mientras `f` mantiene la tendencia.
  2. La prueba `test_hyb01_four_by_four_rubric` dentro de `tests/metodos_numericos/test_pipeline_integration.py`.

---

### Caso 08 — `IDEA-HYB-02`: Pack de Verificación en GeoGebra y Auditoría SHA-256

#### 1. Ficha Teórico-Aplicada (HTML + Proyecto)
- **Temáticas HTML evaluadas:** Verificación cruzada obligatoria de las diapositivas 14 y 15 de ambos HTML: implementación propia en Python comparada con `numpy.polyfit(x, y, 1)` y `scipy.interpolate.lagrange`, más validación interactiva en GeoGebra Classic (`FitLine`, `CorrelationCoefficient`, `RSquare`, `Polynomial`).
- **Rol en JobPath:** Cierra el entregable garantizando **reproducibilidad, trazabilidad y no-mutación de solo lectura** sobre los 19 insumos de `data/` (de hasta 8 GB) mediante **SHA-256 íntegro de 64 caracteres hexadecimales** (con `hash_mode` transparente), 5 scripts GeoGebra verificados + índice, 12 figuras a 150 DPI, **auditoría semántica bilingüe (EN+ES)** y **19 pruebas automatizadas (`unittest`)**.
- **Fuentes verificadas:** [verification_log.md](./verification_log.md), [sha256_input_integrity.csv](./sha256_input_integrity.csv), [geogebra_verification_index.md](../08_IDEA_HYB_02_Pack_Verificacion_GeoGebra/geogebra/geogebra_verification_index.md).

#### 2. Preguntas Conceptuales (2 puntos)
- **P8.1 (1 pt — Selección múltiple):** ¿Por qué la suite `tests/metodos_numericos/` comienza verificando exactamente los 4 ejercicios pedagógicos de los HTML del docente (`test_presentation_server_load_fixture`, `test_presentation_practice_loc_fixture`, `test_presentation_cpu_temperature_fixture`, `test_presentation_practice_fixture`) antes de correr los casos de JobPath?
  - a) Porque GeoGebra exige cargar el ejemplo del servidor web antes de cualquier otro dataset.
  - b) Para establecer pruebas unitarias de referencia (*golden fixtures*) con soluciones analíticas conocidas a mano, garantizando que los motores `ols.py` y `lagrange.py` reproducen fielmente la teoría de clase antes de escalar a 1.74 millones de registros.
  - c) Porque `numpy.polyfit` solo funciona si primero se ejecuta con $n \le 6$.
  - d) Para acelerar el cálculo de los hashes SHA-256.
- **P8.2 (1 pt — Verdadero/Falso justificado):** *«En `verification_log.md`, haber obtenido un error absoluto bruto de `1.523e-07` en `n_starts` sin centrar significa que el motor MCO reprobó la tolerancia de precisión `< 1e-10`.»* Responda Verdadero o Falso y justifique cuantitativamente.

#### 3. Ejercicio Procedimental (3 puntos — Datos reales de `verification_log.md` y `ols_summary_all_ideas.csv`)
En el tablero de verificación (`nm12_hyb02_verification_summary_dashboard.png`), el proyecto mide la precisión en **dígitos significativos concordantes** mediante la fórmula:
$$D = -\log_{10}(\max(\text{error}, 10^{-16}))$$
con línea de aprobación mínima en $\text{tol} = 10^{-10}$ ($D \ge 10.0$ dígitos).

Con los valores exactos de `verification_log.md`, `ols_summary_all_ideas.csv` y `rl04_ols_regime_comparison.csv`:
1. Calcule el **error relativo** tanto de `n_starts (2000–2023)` (`abs_diff = 1.522712e-07`, $|a_0| = 2{,}182{,}899.4867$) como del máximo relativo global en `RL-05 Ver. B knowledge~essential` (`abs_diff = 3.668355e-11`, $|a_0| = 15.993238$). Verifique que reproduce `6.976e-14` y `2.294e-12` (`verification_log.md`).
2. Calcule los dígitos de precisión $D$ para las siguientes cuatro comprobaciones del tablero e indique si superan el umbral $D \ge 10.0$:
   - Max error relativo MCO (39 modelos): `2.294e-12`
   - Max error de invarianza afín (`04_transformed`): `7.216e-14`
   - `LG-01 P3` vs. SciPy: `5.052e-15`
   - `LG-02` Lagrange inverso Ver. A vs. SciPy (PCA en vivo `float64`): `1.290e-11`
3. Explique por qué `LG-01 P3 Kronecker` (`error = 0.0`) se grafica en $D = 16.0$ dígitos en lugar de $+\infty$.

#### 4. Pregunta de Análisis Crítico y Criterio Ingenieril (3 puntos)
Como auditor de calidad del entregable `metodos_numericos_entregable`, evalúe cómo la actualización V2 resolvió tres controles críticos de gobernanza en `IDEA-HYB-02`:
1. **Hashes SHA-256 completos (64 hex) y transparencia de `hash_mode`:** En [sha256_input_integrity.csv](./sha256_input_integrity.csv), las columnas `sha256_before` y `sha256_after` ahora guardan el **digest completo de 64 caracteres hexadecimales** y declaran explícitamente `hash_mode` (`13 full_sha256` para archivos $\le 64$ MiB y `6 sampled_24MiB_plus_meta_sha256` para archivos masivos de hasta 8 GB). ¿Por qué es esencial guardar los 64 caracteres íntegros y documentar el modo de muestreo?
2. **Auditoría semántica bilingüe (`MR-07/MR-08` EN+ES):** La función `audit_wording_compliance` en `validation.py` fue ampliada a expresiones regulares bilingües (español e inglés) con filtro de contexto de salvaguarda y ahora audita **todos los notebooks, reportes `EXPLICACION_*.md`, `GUIA_FACIL_*.md` y presentaciones HTML** (0 violaciones). ¿Qué riesgo de verificación se eliminó frente a la auditoría anterior solo en inglés?
3. **Integridad documental y enlaces automatizados:** `deliverable_packager.py` ahora preserva archivos complementarios sin borrar `out_root`, genera un `README.md` completo, corrige el conteo `"5 .txt + 1 índice .md"` (en lugar de `"6 GGB"`), reconstruye `fuentes_notebooklm/` reescribiendo enlaces relativos (`0` enlaces rotos validados en `unittest`) y empaqueta `metodos_numericos_entregable.zip`. ¿Qué buenas prácticas de gestión de configuración garantiza esto?

#### 5. Verificación en GeoGebra / Python (2 puntos)
1. A partir de [geogebra_verification_index.md](../08_IDEA_HYB_02_Pack_Verificacion_GeoGebra/geogebra/geogebra_verification_index.md), resuma en una tabla los **5 scripts GeoGebra** con su caso, comando principal (`FitLine` o `Polynomial`) y valor clave esperado para aprobar la verificación manual en clase.
2. Indique el comando de consola para ejecutar la suite completa de **19 pruebas** en `tests/metodos_numericos/` y explique qué garantiza la división en 3 archivos (`test_ols_engine.py`, `test_lagrange_engine.py`, `test_pipeline_integration.py`).

#### 6. Solucionario Detallado y Criterios de Calificación (10 puntos)
- **P8.1:** **Opción b)** (1 pt). Validar primero los ejercicios resueltos a mano de los HTML (`a1=28.5714, a0=91.667`; `a1=2.05, a0=0.70`; `P2(65)=66.375`; práctica Lagrange) prueba la corrección del motor antes de confiar en resultados sobre millones de registros.
- **P8.2:** **Falso** (1 pt). Cuando el parámetro tiene magnitud $|a_0| \approx 2.18 \times 10^6$, la precisión de punto flotante `float64` (~15–16 dígitos decimales) impone un error absoluto mínimo del orden de `1e-14 * 2.18e6 ~ 2e-8`. Al normalizar por $|a_0|$, el **error relativo** es `6.976e-14` (y el máximo relativo global en todos los 39 modelos es `2.294e-12`), más de un orden de magnitud por debajo de `1e-10`.
- **Ejercicio procedimental (3 pts — 1 pt c/u):**
  1. Errores relativos:
     $$e_{\text{rel, n\_starts}} = \frac{1.522712 \times 10^{-7}}{2{,}182{,}899.4867} = \mathbf{6.976 \times 10^{-14}} < 10^{-10}\ \checkmark$$
     $$e_{\text{rel, max 39}} = \frac{3.668355 \times 10^{-11}}{15.993238} = \mathbf{2.294 \times 10^{-12}} < 10^{-10}\ \checkmark$$
  2. Dígitos de precisión $D = -\log_{10}(\text{error})$:
     - MCO 39 modelos (`2.294e-12`): $D = 12 - \log_{10}(2.294) \approx \mathbf{11.64}$ dígitos (PASS).
     - Invarianza afín (`7.216e-14`): $D = 14 - \log_{10}(7.216) \approx \mathbf{13.14}$ dígitos (PASS).
     - `LG-01 P3` vs. SciPy (`5.052e-15`): $D = 15 - \log_{10}(5.052) \approx \mathbf{14.30}$ dígitos (PASS).
     - `LG-02` Inv A vs. SciPy (`1.290e-11`): $D = 11 - \log_{10}(1.290) \approx \mathbf{10.89}$ dígitos (PASS).
  3. Porque $\log_{10}(0)$ no está definido ($-\log_{10}(0) = +\infty$); se aplica un piso numérico $\max(\text{error}, 10^{-16})$ que corresponde al límite de precisión de máquina (`float64`, ~16 dígitos).
- **Análisis crítico (3 pts — 1 pt c/u):**
  1. Almacenar los 64 caracteres completos (256 bits) permite a cualquier auditor externo verificar los 13 archivos `full_sha256` con `sha256sum` o `Get-FileHash`, y declarar `sampled_24MiB_plus_meta_sha256` para los 6 archivos masivos (>64 MiB) evita falsas afirmaciones sobre el algoritmo de hashing usado.
  2. Elimina el sesgo de falsa conformidad: cualquier afirmación causal o atribución errónea de competencias ESCO en español dentro de reportes, guías fáciles o diapositivas HTML es detectada automáticamente en la suite de pruebas (`test_deliverable_completeness_bilingual_wording_and_links`).
  3. Elimina la deriva documental (*documentation drift*) entre el empaquetador, el `README.md`, `index.html`, `fuentes_notebooklm/` y el archivo `.zip`, garantizando que todos los enlaces relativos resuelven a archivos reales en disco.
- **Verificación GeoGebra / Python (2 pts — 1 pt c/u):**
  1. Tabla esperada de los 5 scripts:
     - `ggb_rl01_career_steps_skills.txt` (`IDEA-RL-01`, `FitLine`): `a0=22.516043, a1=0.224971, R2=0.995498, f(12)=25.215697`.
     - `ggb_rl02_isco10_transferability.txt` (`IDEA-RL-02`, `FitLine`): `a0=3.448113, a1=0.432990, R2=0.280010 (RECHAZADO MR-06), f(45)=22.932683` (solo chequeo aritmético).
     - `ggb_rl04_annual_duration_extrapolation.txt` (`IDEA-RL-04`, `FitLine`, empleos cerrados `~es_vigente`): `a0=16.441713, a1=-0.792601, R2=0.972874, f(27)=-4.958505`.
     - `ggb_lg01_survival_p3_milestones.txt` (`IDEA-LG-01`, `Polynomial(P)`): `P3(12)=0.206491` (+ forma monómica comentada).
     - `ggb_lg02_pca_forward_p3.txt` (`IDEA-LG-02`, `Polynomial(P)`): `P3(4)=0.877777` (+ forma monómica comentada).
  2. Comando: `python -m unittest discover -s tests/metodos_numericos -v`. Separa pruebas **unitarias** de motores matemáticos (`4` MCO + `5` Lagrange, incluyendo Chebyshev-Lobatto y guardas) de pruebas de **integración y gobernanza** de extremo a extremo (`10` tests sobre los artefactos reales, `MR-09`, PCA en vivo, monomios, SHA-256 64-hex, redacción bilingüe y enlaces).

---

## 3. Evaluación Integradora Transversal (Proyecto Completo — 20 puntos)

### Integradora 1 (10 puntos): Coherencia metodológica de extremo a extremo en el pipeline JobPath
Un comité evaluador revisa el proyecto **JobPath** completo y plantea la siguiente situación integrada:
> *«Queremos estimar dos cantidades nuevas: (A) la permanencia promedio esperada de un empleo en el año **2028**, y (B) la probabilidad de supervivencia laboral exacta a **3.5 años ($q = 14$)** usando los datos cerrados `~es_vigente` del dataset.»*

Con base en los dos HTML y la evidencia consolidada de los Casos `01`, `03`, `05` y `07`:
1. **(4 pts)** Para **(A)**, justifique con cifras exactas de `IDEA-RL-04` por qué ni MCO ni Lagrange global deben usarse para predecir `2028` (incluya el valor que arrojaría la recta centrada en $t = 28$ y explique el doble problema: extrapolación fuera de `2000–2019` + contaminación por `es_vigente`).
2. **(4 pts)** Para **(B)**, compare qué ocurriría al estimar $S(14)$ con: (i) MCO global sobre $q=1..36$, (ii) Lagrange global equiespaciado de grado 16, y (iii) Lagrange local cuadrático $P_2$ / Chebyshev (cite los rangos de error observados en `IDEA-LG-01` e `IDEA-HYB-01`).
3. **(2 pts)** Señale una mejora estructural de ingeniería que debería aplicarse simultáneamente a `IDEA-RL-01`, `IDEA-RL-04` e `IDEA-LG-02` para elevar la consistencia interna del entregable.

#### Solucionario Integradora 1 (10 puntos)
1. *(4 pts)* Con el modelo centrado de `IDEA-RL-04` sobre empleos estrictamente cerrados (`~es_vigente`, $\hat{y}(t) = 16.441713 - 0.792601\,t$), en 2028 ($t=28$) se obtiene $\hat{y}(28) = 16.441713 - 0.792601(28) = \mathbf{-5.7511}$ trimestres (físicamente imposible, aún más severo que `-4.9585` en 2027 y negativo ya desde 2021 con `-0.2029`). Un polinomio de Lagrange global empeoraría exponencialmente la divergencia (como mostró `HYB-01` con errores de hasta `386.36`). Aunque el filtro `~es_vigente` eliminó la contaminación de activos en 2019 (`2.27` vs. `8.31` con vigentes), persiste la censura calendario derecha; por ello se requiere modelado de supervivencia (Kaplan-Meier / Cox) y no extrapolación lineal ni polinomial.
2. *(4 pts)* En $q=14$ (interior a $[1, 40]$, donde el valor empírico real en `lg01_survival_curve_S_q.csv` es $S(14) = 0.1893$): (i) **MCO global** tiene alto sesgo estructural por la curvatura convexa ($R^2 = 0.6935$, LOOCV RMSE `0.1301`, error máximo `0.4681`); (ii) **Lagrange global equiespaciado grado 16** sufre el Fenómeno de Runge ($E_\infty = 2.5262$, RMSE `0.5120`, predicciones negativas); (iii) **Lagrange Local $P_2$** (LOOCV RMSE `0.0524`, extrapolación `+2` `0.0060`) o **Chebyshev-Lobatto** (LOOCV RMSE `0.0620`, `0` violaciones de `[0,1]` en todos los grados) son las opciones recomendables, advirtiendo siempre el salto por *annual heaping* entre $q=13$ (`0.2472`) y $q=14$ (`0.1893`).
3. *(2 pts)* En la revisión V2 del entregable, las tres mejoras estructurales quedaron **implementadas y verificadas en pruebas automatizadas**: filtro uniforme `~es_vigente` (`MR-09`) en `RL-01`, `RL-04` y `LG-01`; recálculo PCA 50k en vivo en `float64` para `LG-02` (cero constantes hardcodeadas); y verificación SHA-256 íntegra de 64 caracteres hexadecimales con `hash_mode` explícito.

---

### Integradora 2 (10 puntos): Decisiones de preprocesamiento y lectura ética/técnica de modelos lineales
El equipo de minería de datos debe decidir si entrenar sus modelos de clasificación de reincidencia (`reincide`) usando `04_transformed/con_outliers` (**Versión A**) o `04_transformed/sin_outliers` (**Versión B**). Usando los resultados exactos de `IDEA-RL-02`, `IDEA-RL-05`, `IDEA-LG-02` e `IDEA-HYB-02`:
1. **(4 pts)** Integre en un argumento cuantitativo los pros y contras observados al elegir **Versión B (IQR)** frente a **Versión A**: mencione (i) reducción de $S_{y/x}$ en `RL-05`, (ii) degradación de $R^2$ bajo `0.30` en `knowledge → essential`, (iii) reducción de 6 a 5 componentes principales para 95 % de varianza en `LG-02`, y (iv) ruptura de la colinealidad exacta en `PC10`.
2. **(3 pts)** Demuestre cómo `IDEA-RL-05` e `IDEA-HYB-02` prueban que el paso por `RobustScaler` no corrompió la información lineal de las variables en `04_transformed/` (cite la tolerancia y el error máximo real).
3. **(3 pts)** Redacte dos reglas estrictas de comunicación de resultados (derivadas de `RL-01`, `RL-02` y `HYB-02`) que un ingeniero debe cumplir al presentar estos hallazgos ante un público no técnico.

#### Solucionario Integradora 2 (10 puntos)
1. *(4 pts — 1 pt por evidencia)* **Pros de Versión B:** reduce $S_{y/x}$ un `21.9 %` en `competence → essential` (`4.09 → 3.19`) y un `20.4 %` en `knowledge → essential` (`10.67 → 8.49`) sin perder ni una de las `1,738,738` filas; además compacta la varianza PCA logrando `95.36 %` en solo **5** componentes (vs. **6** en Versión A). **Contras de Versión B:** al truncar la cola superior de `knowledge` (`45 → 13.5`), el $R^2$ de `knowledge → essential` cae de `0.3680` a `0.2795` (por debajo del umbral de rechazo `0.30`) y se rompe la identidad contable exacta $E = C + K + U$ (apareciendo varianza no nula `5.5e-05` en `PC10`). Por ello la decisión correcta en CRISP-DM es mantener ambas versiones en experimentación comparativa.
2. *(3 pts)* En las 8 combinaciones (`con/sin × train/test × 2 pares`) de `rl05_affine_scale_invariance.csv`, los coeficientes MCO en escala `RobustScaler` coinciden con las fórmulas afines teóricas hasta un error máximo de **`7.216e-14 < 1e-10`** (`~13.14` dígitos), con $R^2$ idéntico y 19/19 insumos intactos según `sha256_input_integrity.csv`.
3. *(3 pts — 1.5 pts c/u)* (1) **No causalidad (`MR-07`):** las pendientes $a_1$ y correlaciones $r$ describen tendencias estadísticas en datos históricos observacionales (no efectos causales de cambiar de empleo ni de tomar cursos). (2) **Atribución taxonómica ESCO (`MR-08`):** las variables de competencias representan requisitos normativos asociados al código ocupacional ESCO asignado al puesto, no habilidades evaluadas individualmente en cada trabajador.

---

## 4. Rúbrica Global de Evaluación (Escala 0.0 – 5.0)

| Criterio de Evaluación | Peso | Insuficiente (`0.0 – 2.9`) | Básico (`3.0 – 3.7`) | Satisfactorio (`3.8 – 4.4`) | Sobresaliente (`4.5 – 5.0`) |
|---|---:|---|---|---|---|
| **1. Dominio conceptual de los HTML** (MCO, Lagrange, unicidad, Runge, extrapolación) | **20 %** | Confunde interpolar con ajustar, malinterpreta $R^2$ o desconoce Kronecker / Runge. | Define los conceptos básicos de ambos HTML, pero falla al justificar el criterio $\sum e_i^2$, $\sum L_i=1$ o las mitigaciones de Runge. | Explica correctamente las bases teóricas de MCO y Lagrange y distingue adecuadamente interpolación de extrapolación. | Articula con total rigor todos los fundamentos, propiedades, ventajas/desventajas y errores típicos de ambos HTML en contextos reales. |
| **2. Rigor procedimental y exactitud numérica** (sumas, $a_0, a_1, R^2, S_{y/x}$, $L_i, P_n$, invarianza afín) | **25 %** | Comete errores graves de fórmula (ej. $(\sum x)^2$ vs. $\sum x^2$, signos en denominadores de $L_i$) o cálculos incompletos. | Plantea las fórmulas correctas, pero presenta errores de redondeo/cálculo u omite verificaciones (centroide, $\sum L_i=1$). | Calcula correctamente coeficientes, métricas y evaluaciones con precisión adecuada y verifica la mayoría de invariantes. | Todos los desarrollos son exactos a $\ge 4$ decimales, verifican centroide, $\sum L_i=1$, deducción afín y coinciden con los CSV reales. |
| **3. Aplicación e interpretación en el proyecto JobPath** (KDD/CRISP-DM, ESCO, no causalidad) | **25 %** | Trata los números como ejercicios aislados, confunde el dominio o hace afirmaciones causales impropias. | Interpreta los resultados en el contexto laboral, pero con imprecisiones sobre el alcance de ESCO o del pipeline `01_raw → 04_transformed`. | Relaciona acertadamente los resultados numéricos con decisiones de JobPath respetando lenguaje descriptivo y atribución ESCO. | Conecta de forma integral cada caso con todo el ciclo KDD/CRISP-DM de JobPath, justificando decisiones de preprocesamiento y modelado con rigor semántico impecable. |
| **4. Análisis crítico de limitaciones y trampas metodológicas** (Simpson, censura, acople, Runge/heaping, guarda `MR-04`) | **15 %** | Acepta todos los $R^2$ altos o extrapolaciones sin cuestionar sesgos ni validez física. | Identifica fallas evidentes (ej. valores negativos en 2027 o en $q=48$), pero omite sesgos más profundos. | Reconoce rechazos honestos ($R^2<0.30$), censura temporal, acople parte-todo y efecto de Runge en los datos reales. | Detecta y argumenta con profundidad incluso las sutilezas críticas del entregable (inversión de signo por cohorte, `es_vigente`, *annual heaping*, extremos de Chebyshev, hardcodeo en `LG-02` y colapso en `HYB-01`). |
| **5. Verificación computacional y reproducibilidad** (GeoGebra, Python `polyfit`/`scipy`, tests y SHA-256) | **15 %** | No presenta comandos válidos ni sabe contrastar soluciones manuales con software. | Replica comandos básicos de GeoGebra o Python, pero sin interpretar tolerancias ni pruebas automatizadas. | Verifica correctamente con comandos de GeoGebra y funciones de NumPy/SciPy, comprendiendo tolerancia `< 1e-10` y pruebas unitarias. | Domina la verificación triple (fórmula propia ↔ NumPy/SciPy ↔ GeoGebra), diferencia error absoluto vs. relativo, audita SHA-256/tests y propone mejoras concretas de ingeniería reproducible. |

**Tabla rápida de conversión de puntaje (100 puntos → Escala UNIMINUTO 0.0 – 5.0):**
- `90 – 100 pts` → `4.5 – 5.0` (**Sobresaliente**)
- `76 – 89 pts` → `3.8 – 4.4` (**Satisfactorio**)
- `60 – 75 pts` → `3.0 – 3.7` (**Básico / Aprobado**)
- `0 – 59 pts` → `0.0 – 2.9` (**Insuficiente**)

---

## 5. Dictamen de Re-Evaluación Post-Corrección (Antes vs. Después — 100/100 · Nota 5.0/5.0)

Tras aplicar las correcciones de ingeniería numérica, rigor metodológico, verificación automatizada y sincronización documental sobre todos los scripts (`scripts/ScriptsCsv/MetodosNumericos/`), tablas CSV, 12 figuras (150 DPI), 5 scripts GeoGebra + índice, 3 notebooks (`8.0–8.2` re-ejecutados), 8 `EXPLICACION_*.md`, 8 `GUIA_FACIL_*.md`, 8 presentaciones HTML interactivas, `index.html`, `presentaciones_separadas.html`, `README.md`, `fuentes_notebooklm/` y `metodos_numericos_entregable.zip`, se realizó una **re-auditoría independiente completa** caso por caso bajo la rúbrica de la Sección 4.

### 5.1 Tablero Comparativo Antes (V1) → Después (V2)

| Caso | ID | Nota Antes (V1) | Hallazgos detectados en V1 y resueltos en V2 | Evidencia verificada Post-Corrección (V2) | Puntaje V2 | Nota V2 |
|---|---|---:|---|---|---:|---:|
| **Caso 01** | `IDEA-RL-01` | `4.4 / 5.0` (`8.8/10`) | `mean_dur_q` incluía `es_vigente`; faltaba prueba WLS por tamaño de celda $n_k$; Paradoja de Simpson en `mean_green` y sesgo de `reincide_rate` sub-documentados. | Filtro estricto `~es_vigente` (`MR-09`, $R^2: 0.9050 \to 0.9233$, $S_{y/x}: 0.8421 \to 0.7928$); WLS integrado (`wls_a1=+0.2287`, diff `1.67 %` en `mean_skills`); Simpson (`-0.00022 → +0.00018`) y cohorte documentados en tablas, gráficas, MD y HTML. | **10.0 / 10** | **5.0 / 5.0** |
| **Caso 02** | `IDEA-RL-02` | `4.5 / 5.0` (`9.0/10`) | Acople parte-todo (`n_ess_comp ⊂ n_essential`, `n_cross_sector ⊂ n_total_rel`) no advertido; `Q_pred=(45, f(45))` en `ggb_rl02` carecía de aviso `MR-06` de modelo rechazado ($R^2=0.2800$). | Acople parte-todo explicitado como tasa marginal estructural; `ggb_rl02_isco10_transferability.txt`, `geogebra_verification_index.md`, `EXPLICACION`, `GUIA_FACIL` y HTML llevan advertencia explícita `WARNING (MR-06): REJECTED` verificada por `unittest`. | **10.0 / 10** | **5.0 / 5.0** |
| **Caso 03** | `IDEA-RL-04` | `4.2 / 5.0` (`8.4/10`) | `mean_dur_q` sin filtro `~es_vigente` creaba rebote artificial en 2019 (`6.61 → 8.31`); filas centradas `t-2000` filtradas de `EXPLICACION`/`index.html`; años formateados con comas (`2,000`, `2,027`). | Filtro `~es_vigente` aplicado (`2018: 3.14 → 2019: 2.27`, $R^2=0.9729$, $a_0=16.4417$, $a_1=-0.7926$, cruce por cero en `2020.74`, `pred(2027)=-4.9585`, mejora `4,672×` al centrar); las 15 filas (incluyendo centradas) visibles sin comas en años. | **10.0 / 10** | **5.0 / 5.0** |
| **Caso 04** | `IDEA-RL-05` | `4.6 / 5.0` (`9.2/10`) | Narrativa centrada solo en `competence → essential`, omitiendo el trade-off de `knowledge → essential` ($R^2: 0.3680 \to 0.2795$ rechazado) y la asimetría muestral (`02_interim` `test+val` 348k vs. `03_processed` 1.74M). | Ambos pares y el trade-off `MR-06` de `knowledge → essential` + asimetría muestral documentados con transparencia total en `EXPLICACION`, `GUIA_FACIL`, presentación HTML e `index.html`; `8/8` pruebas de invarianza afín `< 7.22e-14`. | **10.0 / 10** | **5.0 / 5.0** |
| **Caso 05** | `IDEA-LG-01` | `4.4 / 5.0` (`8.8/10`) | Chebyshev 1.ª especie extrapolaba en $q=1$ en `deg=3, 5` (`max_pred=1.11–1.23`, violando `[0,1]`); faltaba forma monómica expandida de $P_3(q)$; no-monotonicidad y *annual heaping* no destacados. | Actualizado a **Chebyshev-Lobatto** ($\cos(k\pi/n)$): **`0` violaciones `[0,1]` en TODOS los grados (3..16)** y reducción de Runge **`19.4×`** (`2.5262 → 0.1301`); forma monómica exportada en `lg_monomial_expansions.csv` y `ggb_lg01`; no-monotonicidad y *heaping* explicados. | **10.0 / 10** | **5.0 / 5.0** |
| **Caso 06** | `IDEA-LG-02` | `4.3 / 5.0` (`8.6/10`) | Curvas PCA 50k hardcodeadas (`VERIFIED_PCA_50K`) con redondeo asimétrico (6 vs. 7 decimales); faltaba forma monómica explícita de $P_3(k)$. | Constantes hardcodeadas eliminadas: **PCA 50k recalculado en vivo en `float64`** directamente desde `03_processed` (`live_50k_from_03_processed_float64`, `PC10_A = 6.74e-18`, `PC10_B = 5.534e-05`); monomios A y B exportados y verificados en `unittest` y `ggb_lg02`. | **10.0 / 10** | **5.0 / 5.0** |
| **Caso 07** | `IDEA-HYB-01` | `4.4 / 5.0` (`8.8/10`) | Régimen 2 rotulado "Ruidosa" pese a $R^2=0.90$ en arco; empate en Régimen 4 (`0.2423`) entre Chebyshev y Global; tope `degree<=12` no documentado. | Régimen 2 renombrado `"2. Curved Macro Series · Annual mean_skills(year)"` (`Serie Macro Curva con Fluctuación`); Chebyshev-Lobatto desempata Régimen 4 (`0.1741` vs `0.2423`) y mejora Régimen 1 (`19.55 → 1.92`); `P2` local domina R2 y R3; tope `deg<=12` explicitado. | **10.0 / 10** | **5.0 / 5.0** |
| **Caso 08** | `IDEA-HYB-02` | `4.1 / 5.0` (`8.2/10`) | Hashes SHA-256 truncados a 16 hex; auditoría `MR-07/08` solo inglés y en 1 archivo; `6 GGB` erróneo; `README.md` incompleto; enlaces relativos rotos en `fuentes_notebooklm/`; riesgo `shutil.rmtree` en packager; max rel MCO subestimado (`6.98e-14` vs real `2.29e-12`). | **SHA-256 completo de 64 hex** + `hash_mode` (`13 full` + `6 sampled`); **auditoría bilingüe EN+ES** sobre 28 archivos (`0` violaciones); max rel MCO exacto `2.294e-12 < 1e-10`; `5 .txt + 1 índice .md`; `README.md` completo; **`0` enlaces rotos**; `shutil.rmtree` eliminado; **19/19 tests OK**. | **10.0 / 10** | **5.0 / 5.0** |
| **Transversal** | **Integradora (20 pts)** | `4.3 / 5.0` (`17.2/20`) | Inconsistencia `MR-09` entre casos, desfase entre notebooks/presentaciones/ZIP y empaquetador destructivo. | Consistencia total `MR-09` (`RL-01`, `RL-04`, `LG-01`), notebooks `8.0–8.2` re-ejecutados sin errores, 8 HTML con 12 PNGs frescos en base64, `0` cifras obsoletas y `.zip` sincronizado. | **20.0 / 20** | **5.0 / 5.0** |
| **TOTAL** | **Suite Completa** | **`4.37 / 5.0`** (`87.4 / 100`) | **100 % de hallazgos técnicos, metodológicos, numéricos y documentales corregidos.** | **`19/19` tests PASS · `19/19` SHA-256 (64 hex) intactos · `12/12` PNGs 150 DPI · `5/5` GeoGebra OK · `0` violaciones bilingües · `0` enlaces rotos.** | **`100.0 / 100`** | **`5.0 / 5.0` (Sobresaliente)** |

### 5.2 Evidencia de Verificación Automatizada Final
- **Pruebas unitarias e integración (`python -m unittest discover -s tests/metodos_numericos -v`):** **`19 / 19 OK`** (`test_ols_engine.py`: 4, `test_lagrange_engine.py`: 5, `test_pipeline_integration.py`: 10).
- **Notebooks reproducibles (`8.0`, `8.1`, `8.2` ejecutados con `nbconvert --execute --inplace`):** **`3 / 3` ejecutados sin errores** con todas las aserciones en verde.
- **Integridad de solo lectura (`data/`):** **`19 / 19` archivos intactos** con digests SHA-256 completos de 64 caracteres hexadecimales (`13 full_sha256` + `6 sampled_24MiB_plus_meta_sha256`).
- **Cumplimiento semántico bilingüe (`MR-07` no causalidad + `MR-08` atribución ESCO, EN+ES):** **`0` violaciones** en todos los reportes, guías fáciles, presentaciones HTML, índices y notebooks.
- **Integridad de enlaces relativos (`fuentes_notebooklm/` y `README.md`):** **`0` enlaces rotos**.
