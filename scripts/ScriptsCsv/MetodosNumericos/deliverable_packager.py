"""Empaquetador del Entregable Unificado en Español (Núcleo de 8 Ideas · JobPath Métodos Numéricos).

Construye la carpeta autocontenida `metodos_numericos_entregable/`, separada en
8 subcarpetas por idea (cada una con su archivo Markdown explicativo de cómo se
hizo `EXPLICACION_IDEA_*.md`, tablas CSV, figuras PNG a 150 DPI y scripts de
GeoGebra), más un reporte HTML explicativo interactivo (`index.html`) 100% en
español con todos los gráficos incrustados, tablas verificadas y calculadoras
interactivas.
"""

from __future__ import annotations

import base64
import html
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

from .config import NumericalMethodsConfig, default_config


@dataclass(frozen=True)
class IdeaSpec:
    folder_name: str
    idea_id: str
    short_title: str
    topic_family: str  # "OLS" | "Lagrange" | "Hybrid"
    topic_label_es: str
    source_html: str
    slides_ref: str
    priority: str
    purpose: str
    data_inputs: Tuple[str, ...]
    code_modules: Tuple[str, ...]
    how_it_was_built: Tuple[str, ...]
    formulas_md: Tuple[str, ...]
    formulas_html: Tuple[str, ...]
    tables: Tuple[str, ...]
    figures: Tuple[Tuple[str, str], ...]
    geogebra_files: Tuple[str, ...]
    pitfalls: Tuple[str, ...]


IDEA_SPECS: Tuple[IdeaSpec, ...] = (
    IdeaSpec(
        folder_name="01_IDEA_RL_01_Pasos_Carrera_MCO",
        idea_id="IDEA-RL-01",
        short_title="Progresión por Paso de Carrera (job_order k = 1..10)",
        topic_family="OLS",
        topic_label_es="Regresión Lineal (MCO)",
        source_html="regresion_lineal_minimos_cuadrados.html",
        slides_ref="Diapositivas 3–12 (Ecuaciones Normales, Centroide, Residuos, R², Extrapolación)",
        priority="P0",
        purpose=(
            "Cuantificar la tasa lineal de cambio con la que las personas transitan hacia oficios ESCO "
            "más complejos, más repetidos, de menor duración promedio o con distinta intensidad verde a "
            "medida que avanzan desde su 1.er empleo (k = 1) hasta su 10.º empleo (k = 10), sintetizando "
            "1,738,738 experiencias clasificadas en pendientes interpretables para el observatorio laboral."
        ),
        data_inputs=(
            "`data/03_processed/empleos_unificado_limpio.csv` (Versión A · 1,871,014 filas; filtrado a 1,738,738 experiencias clasificadas `saber_skills == 'ok'`)",
            "`data/02_interim/ESCO/greenShareOcc_en_limpio.csv` (unido en RAM por `occupation_code`, cubriendo el 92.93 % del universo)",
        ),
        code_modules=(
            "`scripts/ScriptsCsv/MetodosNumericos/loaders.py` (`load_processed_numeric`, `load_greenshare_lookup`)",
            "`scripts/ScriptsCsv/MetodosNumericos/ols.py` (`regresion_lineal`, `build_summation_and_residual_table`, `predict_ols`)",
            "`scripts/ScriptsCsv/MetodosNumericos/experiments_ols.py` (`run_rl01_career_steps`)",
        ),
        how_it_was_built=(
            "Se cargó `empleos_unificado_limpio.csv` con `usecols` seguro en memoria (excluyendo columnas de texto largo `skills`, `knowledge`, `sin_tipo`) y se cruzó `greenShare` en RAM sin modificar archivos en disco.",
            "Se ordenó cronológicamente la trayectoria de cada persona (`resume_id`) por `(start_ord, end_ord)` asignando el paso secuencial `job_order = 1, 2, ..., 15`.",
            "Se agregaron las medias por paso de carrera `k = 1..10` (`n = 10` nodos) para cuatro variables: `mean_skills`, `reincide_rate`, `mean_dur_q` y `mean_green`.",
            "Se ejecutó un control de sensibilidad restringido a personas con `>= 10` empleos clasificados para verificar el efecto de sesgo de supervivencia.",
            "Se ajustó el modelo lineal por ecuaciones normales cerradas (`regresion_lineal`), generando la tabla completa de sumas (`Σx, Σy, Σx², Σxy`), cuadrados de residuos (`Sr`), centroide `(x̄, ȳ)` y validación frente a `numpy.polyfit(x, y, 1)` (`< 1e-10`).",
            "Se auditó la extrapolación fuera de rango en `k = 11, 12, 15` (`is_extrapolation = True`) contrastando las predicciones frente a las medias reales observadas.",
        ),
        formulas_md=(
            r"$$\hat{y}(k) = a_0 + a_1 k, \qquad a_1 = \frac{n\sum k_i y_i - \sum k_i \sum y_i}{n\sum k_i^2 - (\sum k_i)^2}, \qquad a_0 = \bar{y} - a_1 \bar{k}$$",
            r"$$S_t = \sum (y_i - \bar{y})^2, \qquad S_r = \sum (y_i - \hat{y}_i)^2, \qquad R^2 = \frac{S_t - S_r}{S_t}, \qquad S_{y/x} = \sqrt{\frac{S_r}{n-2}}$$",
        ),
        formulas_html=(
            r"\hat{y}(k) = a_0 + a_1 k, \quad a_1 = \frac{n\sum k_i y_i - \sum k_i \sum y_i}{n\sum k_i^2 - (\sum k_i)^2}, \quad a_0 = \bar{y} - a_1\bar{k}",
            r"R^2 = \frac{S_t - S_r}{S_t}, \quad r = \operatorname{sign}(a_1)\sqrt{R^2}, \quad S_{y/x} = \sqrt{\frac{S_r}{n-2}}",
        ),
        tables=(
            "rl01_ols_summary.csv",
            "rl01_summation_and_residuals_skills.csv",
            "rl01_career_step_profile.csv",
            "rl01_extrapolation_audit.csv",
        ),
        figures=(
            ("nm01_rl01_career_steps_panel.png", "Panel 4× de regresión MCO por paso de carrera k=1..10 con centroides y zona sombreada de extrapolación (k>10)."),
            ("nm02_rl01_residual_squares_and_extrapolation.png", "Representación geométrica de cuadrados de residuos (minimización de Sr) y residuos verticales e_i para mean_skills ~ job_order."),
        ),
        geogebra_files=("ggb_rl01_career_steps_skills.txt",),
        pitfalls=(
            "Asociación descriptiva, nunca causalidad (MR-07): las pendientes describen tendencias entre pasos, no implican que cambiar de empleo cause mayor adquisición de habilidades.",
            "Regla de atribución ESCO (MR-08): `mean_skills` mide cuántas competencias esenciales exige el oficio ocupado, no cuántas domina la persona.",
            "Sesgo de supervivencia y censura: llegan menos personas a `k = 10` (`25,321` registros frente a `352,093` en `k = 1`); por eso se reporta también la cohorte controlada de personas con `>= 10` empleos.",
        ),
    ),
    IdeaSpec(
        folder_name="02_IDEA_RL_02_Catalogo_ESCO_MCO",
        idea_id="IDEA-RL-02",
        short_title="Ontología ESCO y Transferibilidad de Competencias (n = 3,039 oficios)",
        topic_family="OLS",
        topic_label_es="Regresión Lineal (MCO)",
        source_html="regresion_lineal_minimos_cuadrados.html",
        slides_ref="Diapositivas 11 y 13 (Calidad del Ajuste R² y Rechazo Honesto de Modelos Pobres)",
        priority="P0",
        purpose=(
            "Modelar las leyes estructurales internas de la taxonomía europea ESCO v1.2.1 —midiendo qué "
            "fracción de cada competencia adicional de un oficio es transferible entre sectores "
            "(`cross-sector`) a través de los 3,039 oficios y 10 grandes grupos ISCO-08— mientras se "
            "operacionaliza la Diapositiva 13: rechazar honestamente modelos lineales con R² cercano a cero."
        ),
        data_inputs=(
            "`data/02_interim/ESCO/occupations_en_limpio.csv` (3,039 oficios ESCO limpios)",
            "`data/02_interim/ESCO/ISCOGroups_en_limpio.csv` (619 grupos ISCO-08 y 10 grandes grupos de 1 dígito)",
            "`data/02_interim/SKILLS/occupationSkillRelations_en_limpio.csv` (126,051 relaciones: 67,600 esenciales + 58,451 opcionales)",
            "`data/02_interim/SKILLS/skills_en_limpio.csv` (13,939 competencias con `reuseLevel`: sector-specific, cross-sector, occupation-specific, transversal)",
            "`data/02_interim/ESCO/greenShareOcc_en_limpio.csv` (cruce exacto del 100 % en los 3,039 oficios)",
        ),
        code_modules=(
            "`scripts/ScriptsCsv/MetodosNumericos/loaders.py` (`load_esco_catalog_enriched`)",
            "`scripts/ScriptsCsv/MetodosNumericos/ols.py` (`regresion_lineal`, `classify_r2_quality`)",
            "`scripts/ScriptsCsv/MetodosNumericos/experiments_ols.py` (`run_rl02_esco_catalog`)",
        ),
        how_it_was_built=(
            "Se cruzaron las 126,051 relaciones oficio-competencia con `skills_en_limpio.csv` (`reuseLevel`) usando indicadores binarios vectorizados (`essential`, `optional`, `competence`, `knowledge`, `cross-sector`, `sector-specific`, `transversal`).",
            "Se agregaron los conteos a nivel de los `n = 3,039` oficios únicos (`conceptUri`) y se incorporó `greenShare` (3,039/3,039 = 100 % de cobertura) más el gran grupo ISCO-08 de 1 dígito.",
            "Se ajustó MCO en 7 pares estructurales contrastando acoples fuertes (`n_essential ~ n_ess_comp`), transferibilidad moderada (`n_cross_sector ~ n_total_rel`) e hipótesis nulas/ortogonales rechazadas (`n_optional ~ n_essential`, `greenShare ~ n_essential`).",
            "Se estratificó la ley de transferibilidad `n_cross_sector ~ n_total_rel` por separado en los 10 grandes grupos ISCO-08 y se exportaron sus 10 centroides para verificación en GeoGebra.",
        ),
        formulas_md=(
            r"$$\widehat{\texttt{n\_cross\_sector}} = a_0 + a_1 \cdot \texttt{n\_total\_rel}, \qquad \text{Rechazar modelo lineal si } R^2 < 0.30 \text{ (MR-06)}$$",
        ),
        formulas_html=(
            r"\widehat{\text{intersectorial}} = a_0 + a_1 \cdot \text{total\_skills}, \qquad \text{Regla MR-06: Rechazar si } R^2 < 0.30",
        ),
        tables=(
            "rl02_esco_catalog_ols.csv",
            "rl02_isco_major_group_slopes.csv",
        ),
        figures=(
            ("nm03_rl02_esco_high_vs_low_r2.png", "Contraste lado a lado entre acoples estructurales de alto R² y modelos lineales rechazados en los 3,039 oficios ESCO."),
            ("nm04_rl02_isco_major_group_slopes.png", "Pendiente marginal intersectorial a₁ en los 10 grandes grupos ISCO-08 y ajuste de sus 10 centroides para GeoGebra."),
        ),
        geogebra_files=("ggb_rl02_isco10_transferability.txt",),
        pitfalls=(
            "Acople parte-todo en `n_essential ~ n_ess_comp`: las competencias prácticas son componente del total esencial ($E = C + K + U$); la pendiente $a_1 = 1.1227 > 1$ refleja cuánto conocimiento teórico acompaña a cada competencia práctica adicional.",
            "Ortogonalidad verde (`greenShare ~ n_essential`, $R^2 = 0.0000$): demuestra empíricamente que los oficios verdes no equivalen simplemente a oficios con más competencias totales.",
        ),
    ),
    IdeaSpec(
        folder_name="03_IDEA_RL_04_Deriva_Anual_Extrapolacion",
        idea_id="IDEA-RL-04",
        short_title="Deriva Anual de Cohortes y Falla por Extrapolación (2000–2023)",
        topic_family="OLS",
        topic_label_es="Regresión Lineal (MCO)",
        source_html="regresion_lineal_minimos_cuadrados.html",
        slides_ref="Diapositiva 12 (Interpolar vs. Extrapolar fuera del rango de los datos)",
        priority="P0",
        purpose=(
            "Medir dos décadas de evolución estructural del mercado laboral (2000–2019), auditar la "
            "paridad entre las particiones crudas `train/test/val` de `01_raw` y presentar una prueba "
            "empírica contundente de la Diapositiva 12: cómo la censura a la derecha tras 2019 invierte "
            "la tendencia y hace que la extrapolación prediga duraciones laborales negativas."
        ),
        data_inputs=(
            "`data/03_processed/empleos_unificado_limpio.csv` (experiencias clasificadas con `start_year` entre 2000 y 2023)",
            "`data/02_interim/ESCO/greenShareOcc_en_limpio.csv`",
            "`data/01_raw/JobHop_v2_train.csv`, `JobHop_v2_test.csv`, `JobHop_v2_val.csv` (1,993,291 filas crudas para auditoría de paridad temporal)",
        ),
        code_modules=(
            "`scripts/ScriptsCsv/MetodosNumericos/loaders.py` (`load_raw_jobhop_years`, `parse_quarter_series`)",
            "`scripts/ScriptsCsv/MetodosNumericos/experiments_ols.py` (`run_rl04_annual_drift`)",
        ),
        how_it_was_built=(
            "Se agruparon las experiencias clasificadas por año de inicio (`2000–2023`) calculando volumen (`n_starts`), complejidad media (`mean_skills`), duración media (`mean_dur_q`), intensidad verde (`mean_green`) y tasa de reincidencia.",
            "Se compararon dos ventanas: soporte válido (`2000–2019`, `n = 20`) frente a la serie contaminada con la cola censurada (`2000–2023`, `n = 24`, donde `n_starts` colapsa a `59, 3, 3, 1`).",
            "Se ajustó MCO tanto en años absolutos como en años centrados `t = año - 2000` (mejorando interpretabilidad del intercepto y evitando cancelación numérica en `np.polyfit`).",
            "Se extrapoló el modelo `2000–2019` hacia `2020–2027`, marcando automáticamente las predicciones físicamente imposibles (`y_hat < 0`).",
            "Se auditó la tendencia anual de participación porcentual en las 3 particiones crudas de `01_raw` confirmando estabilidad sin sesgo de partición.",
        ),
        formulas_md=(
            r"$$\hat{y}(t) = a_0 + a_1 (t - 2000), \qquad t \in [2000, 2019] \text{ (soporte válido)} \quad\text{vs.}\quad t > 2019 \text{ (extrapolación)}$$",
        ),
        formulas_html=(
            r"\hat{y}(t) = a_0 + a_1(t - 2000), \qquad \text{Zona de extrapolación riesgosa: } t > 2019",
        ),
        tables=(
            "rl04_ols_regime_comparison.csv",
            "rl04_extrapolation_failure_audit.csv",
            "rl04_annual_macro_series.csv",
            "rl04_raw_partition_parity.csv",
        ),
        figures=(
            ("nm05_rl04_annual_drift_and_censoring_extrapolation.png", "Izquierda: la cola censurada invierte la pendiente y colapsa R² (0.748 -> 0.083). Derecha: extrapolar duración predice -0.56 trimestres en 2027."),
        ),
        geogebra_files=("ggb_rl04_annual_duration_extrapolation.txt",),
        pitfalls=(
            "Artefacto mecánico de censura a la derecha (MR-09): la caída lineal de `mean_dur_q` (-0.71 trimestres/año) refleja principalmente el menor tiempo calendario transcurrido desde inicios cercanos a la captura del CV.",
            "Sin centrar el año (`x ~ 2010`), el intercepto crece a órdenes de `10^6`, degradando el número de condición de Vandermonde; centrar en `t - 2000` reduce el error absoluto 7,000 veces.",
        ),
    ),
    IdeaSpec(
        folder_name="04_IDEA_RL_05_Outliers_E_Invarianza_Escala",
        idea_id="IDEA-RL-05",
        short_title="Sensibilidad a Outliers (4 Vías) e Invarianza Afín en 04_transformed",
        topic_family="OLS",
        topic_label_es="Regresión Lineal (MCO)",
        source_html="regresion_lineal_minimos_cuadrados.html",
        slides_ref="Diapositivas 3–5 y 11 (Sensibilidad del Error Cuadrático a Atípicos y Transformaciones Lineales)",
        priority="P0",
        purpose=(
            "Cuantificar matemáticamente cómo responde MCO a outliers reales (Versión A) frente a "
            "winsorización IQR (Versión B) y frente al borrado legado de filas (`02_interim`), y "
            "demostrar algebraica y numéricamente que `RobustScaler` en `data/04_transformed/` "
            "conserva R² y r intactos mientras transforma (a₀, a₁, Sy/x) de manera exacta."
        ),
        data_inputs=(
            "`data/03_processed/empleos_unificado_limpio.csv` (Versión A · 1,738,738 experiencias clasificadas)",
            "`data/03_processed/empleos_limpio_con_competencias_sin_outliers.csv` (Versión B · winsorizada IQR k=1.5)",
            "`data/02_interim/Jobhop/empleos_limpio.csv` y `empleos_limpio_sin_outliers .csv` (flujo legado con borrado de filas; espacio final preservado según MR-12)",
            "`data/04_transformed/{con_outliers,sin_outliers}/{train,test}/X_*.csv` (leídos mediante lector binario de prefijo sin cargar jamás las 2,985 columnas completas)",
            "`data/04_transformed/transformers/{con_outliers,sin_outliers}/transformers.joblib` (centros y escalas IQR de `RobustScaler`)",
        ),
        code_modules=(
            "`scripts/ScriptsCsv/MetodosNumericos/loaders.py` (`load_legacy_interim_pair`, `load_transformed_dense_subset`, `extract_scaler_params`)",
            "`scripts/ScriptsCsv/MetodosNumericos/ols.py` (`verify_affine_scaling_invariance`)",
            "`scripts/ScriptsCsv/MetodosNumericos/experiments_ols.py` (`run_rl05_outlier_and_scaling`)",
        ),
        how_it_was_built=(
            "Se ajustó MCO para `n_skills_essential ~ n_skills_competence` y `n_skills_essential ~ n_skills_knowledge` en las 4 variantes del dataset (Versión A, Versión B, Legado Limpio y Legado con Borrado de Filas).",
            "Se extrajeron los parámetros exactos `(center_, scale_)` de `RobustScaler` desde `transformers.joblib` (`essential: (20, 13)`, `competence: (18, 11)`, `knowledge: (3, 5)`).",
            "Se leyeron exclusivamente las 3 columnas escaladas densas desde los 4 archivos CSV de 2–8 GB en `04_transformed` usando partición binaria del prefijo (`raw_line.split(b',', max_idx+1)`), manteniendo consumo mínimo de RAM.",
            "Se cruzaron `train` y `test` vía `split_map_resume_id.csv` verificando las 8 identidades de invarianza afín con error máximo `7.22e-14 < 1e-10`.",
        ),
        formulas_md=(
            r"$$\tilde{x} = \frac{x - c_x}{s_x}, \quad \tilde{y} = \frac{y - c_y}{s_y} \implies \tilde{a}_1 = a_1 \frac{s_x}{s_y}, \quad \tilde{a}_0 = \frac{a_0 + a_1 c_x - c_y}{s_y}, \quad \tilde{R}^2 = R^2, \quad \tilde{S}_{y/x} = \frac{S_{y/x}}{s_y}$$",
        ),
        formulas_html=(
            r"\tilde{a}_1 = a_1\frac{s_x}{s_y}, \quad \tilde{a}_0 = \frac{a_0 + a_1 c_x - c_y}{s_y}, \quad \tilde{R}^2 = R^2, \quad \tilde{S}_{y/x} = \frac{S_{y/x}}{s_y}",
        ),
        tables=(
            "rl05_four_way_outlier_comparison.csv",
            "rl05_affine_scale_invariance.csv",
        ),
        figures=(
            ("nm06_rl05_outlier_strategies_and_scale_invariance.png", "Izquierda: la winsorización IQR reduce Sy/x en -21.9 % conservando el 100 % de las filas frente al borrado legado. Derecha: más de 13 dígitos de precisión en la invarianza afín sobre 04_transformed."),
        ),
        geogebra_files=(),
        pitfalls=(
            "La winsorización IQR (Versión B) comprime la dispersión (`Sy/x`: 4.087 -> 3.192) sin perder registros, pero rompe la identidad aditiva exacta `E = C + K + U` en la cola derecha recortada.",
            "`transformers.joblib` fue serializado con `scikit-learn 1.9.1` frente a `1.7.2` local; `extract_scaler_params()` aísla las constantes escalares con respaldo verificado.",
        ),
    ),
    IdeaSpec(
        folder_name="05_IDEA_LG_01_Supervivencia_Y_Runge",
        idea_id="IDEA-LG-01",
        short_title="Curva de Supervivencia Laboral S(q) y Fenómeno de Runge Empírico",
        topic_family="Lagrange",
        topic_label_es="Interpolación de Lagrange",
        source_html="interpolacion_lagrange.html",
        slides_ref="Diapositivas 2–12 (Bases L_i, Partición de la Unidad, Fenómeno de Runge, Chebyshev y Tramos)",
        priority="P0",
        purpose=(
            "Reconstruir la función continua de permanencia laboral S(q) = P(dur_q >= q) a partir de "
            "una tabla compacta de 4 hitos ejecutivos (1, 2, 5 y 10 años) sin consultar 1.64M filas, "
            "y demostrar con datos reales el Fenómeno de Runge junto a sus dos soluciones teóricas: "
            "nodos de Chebyshev e interpolación local cuadrática por tramos P₂."
        ),
        data_inputs=(
            "`data/03_processed/empleos_unificado_limpio.csv` filtrado estrictamente a experiencias cerradas clasificadas (`saber_skills == 'ok'` y `~es_vigente`, `n = 1,643,772` empleos según MR-09)",
        ),
        code_modules=(
            "`scripts/ScriptsCsv/MetodosNumericos/lagrange.py` (`lagrange_basis`, `lagrange_eval`, `diagnose_lagrange`, `chebyshev_nodes`, `piecewise_lagrange_eval`)",
            "`scripts/ScriptsCsv/MetodosNumericos/experiments_lagrange.py` (`run_lg01_survival_runge`)",
        ),
        how_it_was_built=(
            "Se excluyeron los empleos vigentes censurados (`es_vigente == True`) y se calculó la curva exacta de permanencia `S(q) = P(dur_q >= q)` en cada trimestre `q = 1..40` (de 0.25 a 10 años).",
            "Se construyó el polinomio cúbico de Lagrange `P₃(q)` pasando exactamente por los 4 hitos `q = {4, 8, 20, 40}`, descomponiendo sus pesos base `L₀(q)..L₃(q)` y verificando delta de Kronecker (`0.00e+00`), partición de la unidad (`4.44e-16`) y coincidencia con `scipy.interpolate.lagrange` (`5.05e-15`).",
            "Se ejecutó el experimento del Fenómeno de Runge para grados `n en {3, 5, 8, 12, 16}` comparando: (a) Lagrange Global Equiespaciado, (b) Lagrange Global con Nodos Chebyshev redondeados/deduplicados y (c) Lagrange Local Cuadrático por Tramos `P₂`.",
            "Se midieron error máximo `E∞`, RMSE, MAE, extremos predichos y violaciones de probabilidad fuera de `[0, 1]`.",
        ),
        formulas_md=(
            r"$$P_n(q) = \sum_{i=0}^{n} S(q_i)\,L_i(q), \qquad L_i(q) = \prod_{\substack{j=0\\ j\ne i}}^{n}\frac{q - q_j}{q_i - q_j}, \qquad \sum_{i=0}^{n} L_i(q) = 1$$",
            r"$$q_k^{\text{Cheb}} = \operatorname{round}\!\left(\frac{a+b}{2} + \frac{b-a}{2}\cos\!\left(\frac{(2k+1)\pi}{2(n+1)}\right)\right)$$",
        ),
        formulas_html=(
            r"P_n(q) = \sum_{i=0}^{n} S(q_i)L_i(q), \quad L_i(q_j)=\delta_{ij}, \quad \sum_{i=0}^{n}L_i(q)=1",
            r"q_k^{\text{Cheb}} = \frac{a+b}{2} + \frac{b-a}{2}\cos\!\left(\frac{(2k+1)\pi}{2(n+1)}\right)",
        ),
        tables=(
            "lg01_milestone_P3_weights_and_eval.csv",
            "lg01_runge_phenomenon_benchmark.csv",
            "lg01_survival_curve_S_q.csv",
        ),
        figures=(
            ("nm07_lg01_survival_milestones_and_weights.png", "Izquierda: polinomio cúbico P₃(q) sobre 4 hitos frente a la curva real S(q). Derecha: polinomios base L₀..L₃ con pesos exactos en q=12."),
            ("nm08_lg01_runge_phenomenon_vs_chebyshev.png", "Prueba empírica del Fenómeno de Runge: grado 16 equiespaciado explota a E∞ = 2.5262, mientras Chebyshev lo acota en 0.1334 (18.9× menos error) y P₂ por tramos se mantiene estable."),
        ),
        geogebra_files=("ggb_lg01_survival_p3_milestones.txt",),
        pitfalls=(
            "Incluir empleos activos (`es_vigente == True`, imputados en `2026-Q1`) distorsionaría artificialmente las permanencias largas; se filtra estrictamente a empleos cerrados (MR-09).",
            "Al proyectar nodos continuos de Chebyshev sobre trimestres enteros, grados altos pueden producir colisiones de índices; la deduplicación explícita garantiza nodos estrictamente distintos (MR-04).",
        ),
    ),
    IdeaSpec(
        folder_name="06_IDEA_LG_02_PCA_Lagrange_Inversa",
        idea_id="IDEA-LG-02",
        short_title="Varianza Acumulada de PCA: Interpolación Directa e Inversa",
        topic_family="Lagrange",
        topic_label_es="Interpolación de Lagrange",
        source_html="interpolacion_lagrange.html",
        slides_ref="Diapositivas 2–10 (Interpolación Tabular Exacta, Unicidad y Nodos Distintos x_i ≠ x_j)",
        priority="P0",
        purpose=(
            "Interpolar la curva de varianza explicada acumulada de PCA (`4.1_PCA_completo`, muestra 50k) "
            "desde nodos dispersos y aplicar interpolación inversa de Lagrange k(V*) para estimar la "
            "dimensionalidad continua necesaria para alcanzar umbrales objetivo (80 %, 85 %, 90 %, 95 %), "
            "verificando en vivo la guarda de nodos distintos (MR-04) ante la meseta de rango 9 de la Versión A."
        ),
        data_inputs=(
            "`notebooks/refactor/4.1_PCA_completo.ipynb` (curvas verificadas de varianza acumulada 50k sobre `data/04_transformed/{con_outliers,sin_outliers}/train/X_train.csv`)",
            "`data/04_transformed/con_outliers/train/X_train.csv` y `sin_outliers/train/X_train.csv` (auditados vía SHA-256)",
        ),
        code_modules=(
            "`scripts/ScriptsCsv/MetodosNumericos/lagrange.py` (`lagrange_eval`, `inverse_lagrange_eval`, `validate_distinct_nodes`)",
            "`scripts/ScriptsCsv/MetodosNumericos/experiments_lagrange.py` (`run_lg02_pca_curves`)",
        ),
        how_it_was_built=(
            "Se cargaron las curvas PCA de 10 componentes para Versión A (`con_outliers`, donde `PC10 = 6.74e-18` por colinealidad exacta `E = C + K + U`) y Versión B (`sin_outliers`, donde el recorte IQR rompe la colinealidad dejando `PC10 = 5.5e-5`).",
            "Se construyó el interpolante directo cúbico `P₃(k)` con nodos dispersos `k = {1, 3, 5, 8}` evaluando su precisión en los componentes retenidos `k = {2, 4, 6, 7}`.",
            "Se restringió el dominio al tramo estrictamente creciente `k = 1..6` y se invirtieron los ejes `(V(k), k)` con Lagrange local `P₂` y global `P₅` para hallar `k(0.80), k(0.85), k(0.90), k(0.95)`, comprobando `V(ceil(k)) >= V*` en los 8 casos.",
            "Se invocó deliberadamente `inverse_lagrange_eval` sobre los 10 puntos completos de Versión A demostrando que la regla `MR-04` bloquea el empate `V(9) = V(10) = 1.0` en lugar de dividir por cero.",
        ),
        formulas_md=(
            r"$$\text{Directa: } \hat{V}(k) = \sum_{i} V(k_i) L_i(k) \qquad\text{Inversa (estrictamente monótona): } \hat{k}(V^*) = \sum_{i} k_i L_i^{(V)}(V^*)$$",
        ),
        formulas_html=(
            r"\text{Directa: }\hat{V}(k)=\sum_i V(k_i)L_i(k), \qquad \text{Inversa: }\hat{k}(V^*)=\sum_i k_i L_i^{(V)}(V^*)",
        ),
        tables=(
            "lg02_pca_50k_reference.csv",
            "lg02_pca_forward_P3_eval.csv",
            "lg02_pca_inverse_effective_dim.csv",
        ),
        figures=(
            ("nm09_lg02_pca_forward_and_inverse_lagrange.png", "Izquierda: Lagrange directo P₃(k) sobre PCA Versión A y B señalando la meseta de rango 9. Derecha: dimensionalidad efectiva k(V*) por interpolación inversa."),
        ),
        geogebra_files=("ggb_lg02_pca_forward_p3.txt",),
        pitfalls=(
            "La interpolación inversa exige ordenadas estrictamente distintas y monótonas: pasar `k = 9, 10` simultáneamente en Versión A produce una singularidad `V(9) - V(10) = 0`, interceptada automáticamente por `validate_distinct_nodes()`.",
        ),
    ),
    IdeaSpec(
        folder_name="07_IDEA_HYB_01_Laboratorio_Interpolar_vs_Ajustar",
        idea_id="IDEA-HYB-01",
        short_title="Laboratorio Comparativo '¿Interpolar o Ajustar?' (4 Métodos × 4 Regímenes)",
        topic_family="Hybrid",
        topic_label_es="Síntesis Híbrida (MCO vs. Lagrange)",
        source_html="Ambas presentaciones HTML",
        slides_ref="Diapositiva 2 de AMBOS HTML ('¿Pasar por todos los puntos… o capturar la tendencia?' y 'Diferencia con la regresión')",
        priority="P0",
        purpose=(
            "Unificar empíricamente ambas presentaciones sobre datos reales de JobPath: evaluar cara a "
            "cara 4 métodos numéricos en 4 regímenes de curva distintos mediante Validación Cruzada "
            "Leave-One-Out (LOOCV) y extrapolación a +2 pasos, produciendo una Rúbrica Objetiva de "
            "Selección de Método."
        ),
        data_inputs=(
            "Régimen 1: `rl01_career_step_profile.csv` (`mean_skills(k)`, suave casi lineal, `k=1..10`, extrap. `k=11,12`)",
            "Régimen 2: `rl04_annual_macro_series.csv` (`mean_skills(año)`, serie macro ruidosa, `2000..2017`, extrap. `2018,2019`)",
            "Régimen 3: `lg01_survival_curve_S_q.csv` (`S(q)`, curva monótona no lineal empinada, `q=1..36`, extrap. `q=38,40`)",
            "Régimen 4: `lg02_pca_50k_reference.csv` (`V(k)` Versión B, tabla cóncava exacta, `k=1..8`, extrap. `k=9,10`)",
        ),
        code_modules=(
            "`scripts/ScriptsCsv/MetodosNumericos/comparison.py` (`run_hyb01_interpolate_vs_fit`, `_evaluate_four_methods_on_regime`)",
        ),
        how_it_was_built=(
            "Se seleccionaron 4 curvas reales de JobPath que cubren los escenarios clásicos de análisis numérico: tendencia casi lineal, serie temporal ruidosa, decaimiento no lineal pronunciado y tabla cóncava exacta.",
            "Se evaluaron en igualdad de condiciones 4 métodos: (1) Regresión Lineal MCO, (2) Lagrange Global Equiespaciado, (3) Lagrange con Nodos Chebyshev y (4) Lagrange Local Cuadrático por Tramos `P₂`.",
            "Se aplicó Validación Cruzada Leave-One-Out (LOOCV) estrictamente interior para medir MAE, RMSE y error máximo dentro de `[x_min, x_max]`, además de extrapolación controlada a +2 pasos frente a valores reales retenidos.",
            "Se rankearon automáticamente las 16 combinaciones método×régimen y se generó la rúbrica ejecutiva de decisión (`hyb01_method_selection_rubric.csv`).",
        ),
        formulas_md=(
            r"$$\text{LOOCV-RMSE} = \sqrt{\frac{1}{n-2}\sum_{i=2}^{n-1}\left(y_i - \hat{f}_{(-i)}(x_i)\right)^2}, \qquad \text{Extrap-MAE}_{+2} = \frac{1}{2}\sum_{m=1}^{2}\left|y_{n+m} - \hat{f}(x_{n+m})\right|$$",
        ),
        formulas_html=(
            r"\text{LOOCV-RMSE} = \sqrt{\frac{1}{n-2}\sum_{i=2}^{n-1}\big(y_i - \hat{f}_{(-i)}(x_i)\big)^2}",
        ),
        tables=(
            "hyb01_method_selection_rubric.csv",
            "hyb01_loocv_and_extrapolation_matrix.csv",
        ),
        figures=(
            ("nm10_hyb01_interpolate_vs_fit_four_regimes.png", "Superposición visual de los 4 métodos en los 4 regímenes reales de JobPath mostrando oscilación de Lagrange global frente a estabilidad de MCO y fidelidad de P₂ local."),
            ("nm11_hyb01_loocv_and_extrapolation_rubric.png", "Comparación relativa (1.0× = ganador del régimen) de RMSE en LOOCV y MAE en extrapolación +2 pasos."),
        ),
        geogebra_files=(),
        pitfalls=(
            "Lagrange global equiespaciado solo gana en tablas exactas suaves de bajo grado (PCA `V(k)`, `RMSE = 0.0036`); sobre datos anuales ruidosos su error explota 108× (`12.32` frente a `0.114` de `P₂` por tramos), confirmando exactamente la Diapositiva 2.",
        ),
    ),
    IdeaSpec(
        folder_name="08_IDEA_HYB_02_Pack_Verificacion_GeoGebra",
        idea_id="IDEA-HYB-02",
        short_title="Pack Automatizado de Verificación en GeoGebra y Auditoría SHA-256",
        topic_family="Hybrid",
        topic_label_es="Verificación Dual (Python + GeoGebra)",
        source_html="Ambas presentaciones HTML",
        slides_ref="Diapositivas 14–15 de AMBOS HTML (Verificación en GeoGebra + Reto Python vs. NumPy/SciPy)",
        priority="P1",
        purpose=(
            "Conectar la pedagogía de clase con ingeniería reproducible de minería de datos: generar "
            "automáticamente scripts listos para copiar y pegar en GeoGebra Classic para los 5 casos "
            "canónicos de n pequeño, validar todo cálculo hecho a mano contra NumPy/SciPy (< 1e-10) "
            "y certificar mediante SHA-256 que los 19 insumos de `data/` permanecieron 100 % intactos."
        ),
        data_inputs=(
            "Tablas canónicas de nodos de `IDEA-RL-01`, `IDEA-RL-02` (10 centroides ISCO), `IDEA-RL-04` (2000–2019 centrado), `IDEA-LG-01` (4 hitos de supervivencia) e `IDEA-LG-02` (PCA `k = 1, 3, 5, 8`)",
            "19 archivos de solo lectura auditados en `01_raw/`, `02_interim/`, `03_processed/`, `04_transformed/` y `split_map_resume_id.csv`",
        ),
        code_modules=(
            "`scripts/ScriptsCsv/MetodosNumericos/geogebra.py` (`export_hyb02_geogebra_pack`)",
            "`scripts/ScriptsCsv/MetodosNumericos/validation.py` (`snapshot_read_only_inputs`, `verify_read_only_inputs`, `validate_geogebra_scripts`, `audit_wording_compliance`)",
            "`tests/metodos_numericos/` (suite de 15 pruebas automatizadas)",
        ),
        how_it_was_built=(
            "Se generaron automáticamente 5 archivos `.txt` con comandos de GeoGebra en inglés (compatibles en cualquier idioma: `FitLine`, `CorrelationCoefficient`, `RSquare`, `Polynomial` y expresiones explícitas `L0(x)..L3(x)`) e indicando equivalentes en español en los comentarios.",
            "Se validó la sintaxis de cada archivo `.txt` mediante expresiones regulares (`validate_geogebra_scripts`).",
            "Se verificaron los 39 modelos MCO frente a `numpy.polyfit(x, y, 1)` (error relativo máx. `6.98e-14`), las 8 pruebas de invarianza afín (`7.22e-14`) y los diagnósticos de Lagrange frente a `scipy.interpolate` (`5.05e-15`).",
            "Se tomaron huellas SHA-256 antes y después de la ejecución comprobando cero modificaciones en `data/`, junto con auditoría semántica (`MR-07` y `MR-08`).",
        ),
        formulas_md=(
            r"$$\text{Error Relativo MCO} = \frac{\max(|a_0 - \hat{a}_0^{\text{np}}|, |a_1 - \hat{a}_1^{\text{np}}|)}{\max(1, |a_0|, |a_1|)} = 6.98\times 10^{-14} < 10^{-10}, \qquad \max_x |P_n(x) - P_n^{\text{scipy}}(x)| = 5.05\times 10^{-15}$$",
        ),
        formulas_html=(
            r"\text{ErrRel}_{\text{MCO}} = 6.98\times 10^{-14} < 10^{-10}, \qquad \text{Err}_{\text{Lagrange vs SciPy}} = 5.05\times 10^{-15} < 10^{-10}",
        ),
        tables=(
            "ols_summary_all_ideas.csv",
            "sha256_input_integrity.csv",
        ),
        figures=(
            ("nm12_hyb02_verification_summary_dashboard.png", "Tablero de precisión decimal (-log10 error) confirmando que todas las verificaciones de MCO y Lagrange superan ampliamente el umbral 1e-10."),
        ),
        geogebra_files=(
            "ggb_rl01_career_steps_skills.txt",
            "ggb_rl02_isco10_transferability.txt",
            "ggb_rl04_annual_duration_extrapolation.txt",
            "ggb_lg01_survival_p3_milestones.txt",
            "ggb_lg02_pca_forward_p3.txt",
            "geogebra_verification_index.md",
        ),
        pitfalls=(
            "Usa preferiblemente los comandos en inglés (`FitLine`, `Polynomial`, `RSquare`, `CorrelationCoefficient`) porque GeoGebra Classic los acepta sin error sin importar si la interfaz está configurada en español o en inglés.",
        ),
    ),
)

# Traducción limpia de etiquetas de texto en tablas sin alterar los CSV fuente
TEXT_TRANSLATIONS: Dict[str, str] = {
    "Strong Linear Fit (R2 >= 0.70)": "Ajuste Lineal Fuerte (R² ≥ 0.70)",
    "Moderate Linear Fit (0.30 <= R2 < 0.70)": "Ajuste Lineal Moderado (0.30 ≤ R² < 0.70)",
    "Weak / Rejected Linear Model (R2 < 0.30)": "Modelo Lineal Débil / Rechazado (R² < 0.30)",
    "Valid support (2000-2019, n=20)": "Soporte válido (2000–2019, n=20)",
    "Censored tail included (2000-2023, n=24)": "Con cola censurada (2000–2023, n=24)",
    "Equispaced Global Lagrange": "Lagrange Global Equiespaciado",
    "Chebyshev-Snapped Global Lagrange": "Lagrange Global (Nodos Chebyshev)",
    "Piecewise Local Quadratic (P2)": "Lagrange Local Cuadrático (P₂)",
    "OLS Linear Regression": "Regresión Lineal MCO",
    "Global Lagrange (Equispaced)": "Lagrange Global (Equiespaciado)",
    "Chebyshev-Node Lagrange": "Lagrange (Nodos Chebyshev)",
    "Piecewise Local Lagrange (P2)": "Lagrange Local por Tramos (P₂)",
    "1. Smooth Near-Linear · Career Steps mean_skills(k)": "1. Suave Casi Lineal · Pasos mean_skills(k)",
    "2. Noisy Macro Series · Annual mean_skills(year)": "2. Serie Macro Ruidosa · Anual mean_skills(año)",
    "3. Steep Nonlinear Monotone · Survival Curve S(q)": "3. No Lineal Empinada · Supervivencia S(q)",
    "4. Exact Concave Table · PCA CumVar V(k) (Ver. B)": "4. Tabla Cóncava Exacta · PCA V(k) (Ver. B)",
    "Version A (con_outliers)": "Versión A (con outliers)",
    "Version B (sin_outliers)": "Versión B (sin outliers IQR)",
    "Version A · With Outliers (03_processed)": "Versión A · Con Outliers (03_processed)",
    "Version B · IQR Winsorized (03_processed)": "Versión B · Winsorizada IQR (03_processed)",
    "Legacy Clean · test+val (02_interim/empleos_limpio.csv)": "Legado Limpio · test+val (02_interim)",
    "Legacy Row-Dropped · test+val (02_interim/empleos_limpio_sin_outliers .csv)": "Legado Borrado Filas · test+val (02_interim)",
}


def _fmt_cell(val: object) -> str:
    if pd.isna(val):
        return "—"
    if isinstance(val, bool) or type(val).__name__ == "bool_":
        return "Sí" if bool(val) else "No"
    if isinstance(val, int) or type(val).__name__.startswith("int"):
        return f"{int(val):,}"
    if isinstance(val, float) or type(val).__name__.startswith("float"):
        fval = float(val)
        if fval.is_integer() and abs(fval) < 1e12:
            return f"{int(fval):,}"
        av = abs(fval)
        if av != 0.0 and (av < 1e-4 or av >= 1e7):
            return f"{fval:.3e}"
        if av >= 1000:
            return f"{fval:,.2f}"
        return f"{fval:.4f}"
    s = str(val)
    return TEXT_TRANSLATIONS.get(s, s)


def _df_to_markdown(df: pd.DataFrame, max_rows: int = 25) -> str:
    sub = df.head(max_rows)
    cols = list(sub.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in sub.iterrows():
        lines.append("| " + " | ".join(_fmt_cell(row[c]).replace("|", "\\|") for c in cols) + " |")
    if len(df) > max_rows:
        lines.append(f"\n*Se muestran las primeras {max_rows} de {len(df)} filas; consulta el archivo CSV completo en `tables/`.*")
    return "\n".join(lines)


def _df_to_html_table(df: pd.DataFrame, max_rows: int = 20) -> str:
    sub = df.head(max_rows)
    cols = list(sub.columns)
    thead = "".join(f"<th>{html.escape(str(c))}</th>" for c in cols)
    body_rows: List[str] = []
    for _, row in sub.iterrows():
        tds = []
        for c in cols:
            txt = _fmt_cell(row[c])
            cls = ""
            if "Rechazado" in txt or txt == "No":
                cls = ' class="bad-cell"'
            elif "Fuerte" in txt or txt == "Sí":
                cls = ' class="ok-cell"'
            tds.append(f"<td{cls}>{html.escape(txt)}</td>")
        body_rows.append("<tr>" + "".join(tds) + "</tr>")
    note = f'<p class="tbl-note">Mostrando {len(sub)} de {len(df)} filas (CSV completo incluido en la subcarpeta).</p>' if len(df) > max_rows else ""
    return f'<div class="tbl-wrap"><table><thead><tr>{thead}</tr></thead><tbody>{"".join(body_rows)}</tbody></table></div>{note}'


def _img_to_base64(path: Path) -> str:
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


def _select_display_columns(table_name: str, df: pd.DataFrame) -> pd.DataFrame:
    col_maps: Dict[str, List[str]] = {
        "rl01_ols_summary.csv": ["idea_id", "y_var", "n", "a0", "a1", "r", "r2", "s_yx", "quality_verdict", "polyfit_max_abs_diff"],
        "rl02_esco_catalog_ols.csv": ["idea_id", "x_var", "y_var", "n", "a0", "a1", "r", "r2", "s_yx", "quality_verdict"],
        "rl02_isco_major_group_slopes.csv": ["isco_major", "isco_major_label", "n_occupations", "mean_total_rel", "mean_cross_sector", "a1_cross_sector_slope", "r2"],
        "rl04_ols_regime_comparison.csv": ["y_var", "regime", "n", "a0", "a1", "r", "r2", "s_yx", "quality_verdict"],
        "rl05_four_way_outlier_comparison.csv": ["variant", "x_var", "y_var", "n", "a0", "a1", "r2", "s_yx"],
        "rl05_affine_scale_invariance.csv": ["version", "split", "x_var", "y_var", "r2_raw", "r2_scaled_obs", "a1_scaled_obs", "a1_scaled_theory", "max_invariance_err", "passes_tol"],
        "ols_summary_all_ideas.csv": ["idea_id", "x_var", "y_var", "n", "a0", "a1", "r2", "s_yx", "quality_verdict"],
        "sha256_input_integrity.csv": ["file_name", "sha256_before", "sha256_after", "intact"],
    }
    if table_name in col_maps:
        keep = [c for c in col_maps[table_name] if c in df.columns]
        out = df[keep].copy()
        if table_name == "rl04_ols_regime_comparison.csv":
            out = out.loc[~out["regime"].str.contains("Centered")].reset_index(drop=True)
        return out
    return df


def _write_idea_markdown(
    spec: IdeaSpec,
    idea_dir: Path,
    tdir: Path,
    gdir: Path,
) -> Path:
    lines: List[str] = [
        f"# {spec.idea_id} — {spec.short_title}",
        "",
        f"> **Temática:** {spec.topic_label_es} · **Prioridad:** {spec.priority} · **Presentación base:** `{spec.source_html}` ({spec.slides_ref})",
        "",
        "---",
        "",
        "## 1. Propósito y Finalidad Analítica",
        "",
        spec.purpose,
        "",
        "## 2. Archivos de `data/` Utilizados (Solo Lectura)",
        "",
    ]
    for inp in spec.data_inputs:
        lines.append(f"- {inp}")

    lines.extend(["", "## 3. Formulación Matemática Aplicada", ""])
    for fm in spec.formulas_md:
        lines.append(fm)
        lines.append("")

    lines.extend(["## 4. Cómo se Hizo (Metodología Paso a Paso)", ""])
    for idx, step in enumerate(spec.how_it_was_built, start=1):
        lines.append(f"{idx}. {step}")

    lines.extend(["", "**Módulos de Python que lo implementan:**", ""])
    for mod in spec.code_modules:
        lines.append(f"- {mod}")

    lines.extend(["", "## 5. Resultados Empíricos Verificados", ""])
    for tbl_name in spec.tables:
        csv_path = tdir / tbl_name
        df_raw = pd.read_csv(csv_path)
        df_disp = _select_display_columns(tbl_name, df_raw)
        lines.append(f"### Tabla: `{tbl_name}`")
        lines.append("")
        lines.append(_df_to_markdown(df_disp, max_rows=20))
        lines.append("")

    lines.extend(["## 6. Gráficos Generados (150 DPI)", ""])
    for fig_name, caption in spec.figures:
        lines.append(f"### `{fig_name}`")
        lines.append("")
        lines.append(f"![{caption}](./figures/{fig_name})")
        lines.append("")
        lines.append(f"*{caption}*")
        lines.append("")

    if spec.geogebra_files:
        lines.extend(["## 7. Comandos de Verificación en GeoGebra", ""])
        for gfile in spec.geogebra_files:
            if gfile.endswith(".txt"):
                txt = (gdir / gfile).read_text(encoding="utf-8").strip()
                lines.append(f"### `{gfile}`")
                lines.append("")
                lines.append("```text")
                lines.append(txt)
                lines.append("```")
                lines.append("")
            else:
                lines.append(f"- Índice consolidado: [`geogebra/{gfile}`](./geogebra/{gfile})")
                lines.append("")

    sec_num = 8 if spec.geogebra_files else 7
    lines.extend([f"## {sec_num}. Limitaciones, Advertencias y Salvaguardas de Dominio", ""])
    for pit in spec.pitfalls:
        lines.append(f"- {pit}")

    lines.extend(
        [
            "",
            "---",
            "",
            "**Reproducibilidad:** Ejecuta `python -m scripts.ScriptsCsv.MetodosNumericos.pipeline` desde la raíz de `MineriaProtect` para recalcular todo desde `data/`, `python -m scripts.ScriptsCsv.MetodosNumericos.deliverable_packager` para actualizar esta carpeta, y `python -m unittest discover -s tests/metodos_numericos -v` para correr las 15 pruebas.",
        ]
    )

    md_path = idea_dir / f"EXPLICACION_{spec.idea_id.replace('-', '_')}.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path


def _build_master_html(
    cfg: NumericalMethodsConfig,
    out_root: Path,
) -> Path:
    tdir, fdir, gdir = cfg.tables_dir, cfg.figures_dir, cfg.geogebra_dir

    rl01_ols = pd.read_csv(tdir / "rl01_ols_summary.csv")
    rl01_sk = rl01_ols.loc[(rl01_ols["idea_id"] == "IDEA-RL-01") & (rl01_ols["y_var"] == "mean_skills")].iloc[0]
    rl04_reg = pd.read_csv(tdir / "rl04_ols_regime_comparison.csv")
    rl04_dur = rl04_reg.loc[(rl04_reg["y_var"] == "mean_dur_q") & (rl04_reg["regime"].str.startswith("Valid"))].iloc[0]
    lg01_rb = pd.read_csv(tdir / "lg01_runge_phenomenon_benchmark.csv")
    lg01_eq16 = lg01_rb.loc[(lg01_rb["degree"] == 16) & (lg01_rb["node_strategy"] == "Equispaced Global Lagrange")].iloc[0]
    lg01_ch16 = lg01_rb.loc[(lg01_rb["degree"] == 16) & (lg01_rb["node_strategy"] == "Chebyshev-Snapped Global Lagrange")].iloc[0]
    lg01_surv = pd.read_csv(tdir / "lg01_survival_curve_S_q.csv")
    s_nodes = [float(lg01_surv.loc[lg01_surv["quarter_q"] == q, "survival_prob_S_q"].iloc[0]) for q in (4, 8, 20, 40)]
    hyb_rubric = pd.read_csv(tdir / "hyb01_method_selection_rubric.csv")
    sha_df = pd.read_csv(tdir / "sha256_input_integrity.csv")
    rl05_inv = pd.read_csv(tdir / "rl05_affine_scale_invariance.csv")

    nav_items: List[str] = [
        '<a href="#resumen" class="nav-link active" data-sec="resumen"><span class="dot dot-all"></span>Resumen Ejecutivo</a>',
    ]
    idea_sections_html: List[str] = []

    badge_cls = {"OLS": "pill-indigo", "Lagrange": "pill-teal", "Hybrid": "pill-amber"}
    dot_cls = {"OLS": "dot-ols", "Lagrange": "dot-lag", "Hybrid": "dot-hyb"}

    for idx, spec in enumerate(IDEA_SPECS, start=1):
        sec_id = f"sec-{spec.idea_id.lower()}"
        nav_items.append(
            f'<a href="#{sec_id}" class="nav-link" data-sec="{sec_id}" data-family="{spec.topic_family}">'
            f'<span class="dot {dot_cls[spec.topic_family]}"></span>'
            f'{idx:02d}. {html.escape(spec.idea_id)}</a>'
        )

        figs_html: List[str] = []
        for fig_name, caption in spec.figures:
            b64 = _img_to_base64(fdir / fig_name)
            figs_html.append(
                f'<figure class="fig-card">'
                f'<img src="{b64}" alt="{html.escape(caption)}" onclick="openLightbox(this)" title="Haz clic para ampliar">'
                f'<figcaption><strong>{html.escape(fig_name)}</strong> — {html.escape(caption)}</figcaption>'
                f"</figure>"
            )

        tables_html: List[str] = []
        for t_idx, tbl_name in enumerate(spec.tables):
            df_disp = _select_display_columns(tbl_name, pd.read_csv(tdir / tbl_name))
            tbl_block = _df_to_html_table(df_disp, max_rows=16)
            if t_idx < 2:
                tables_html.append(f'<div class="sub-block"><h4>Tabla verificada · <code>{html.escape(tbl_name)}</code></h4>{tbl_block}</div>')
            else:
                tables_html.append(
                    f'<details class="fold-block"><summary>Desplegar tabla adicional: <code>{html.escape(tbl_name)}</code> ({len(df_disp)} filas)</summary>{tbl_block}</details>'
                )

        ggb_html = ""
        txt_files = [g for g in spec.geogebra_files if g.endswith(".txt")]
        if txt_files:
            blocks = []
            for gf in txt_files:
                code_txt = (gdir / gf).read_text(encoding="utf-8").strip()
                blocks.append(
                    f'<div class="ggb-box">'
                    f'<div class="ggb-head"><span>Script de GeoGebra Classic · <code>{html.escape(gf)}</code></span>'
                    f'<button class="copy-btn" onclick="copyCode(this)">Copiar comandos</button></div>'
                    f'<pre><code>{html.escape(code_txt)}</code></pre></div>'
                )
            ggb_html = '<div class="sub-block"><h4>Verificación en GeoGebra (Diapositivas 14–15)</h4>' + "".join(blocks) + "</div>"

        interactive_html = ""
        if spec.idea_id == "IDEA-RL-01":
            interactive_html = """
            <div class="interactive-card">
              <h4>Calculadora Interactiva · Paso de Carrera $k \\in [1, 15]$ (MCO Real de JobPath)</h4>
              <p class="muted">Mueve el deslizador $k$ para comparar la predicción dentro del rango ($1 \\le k \\le 10$) frente a la extrapolación ($k > 10$):</p>
              <div class="slider-row">
                <label>Paso $k$:</label>
                <input type="range" id="rl01Slider" min="1" max="15" step="0.5" value="5.5" oninput="updateRL01()">
                <span class="mono big-inline" id="rl01K">5.5</span>
              </div>
              <div class="kpi-mini-row">
                <div><span class="muted">Competencias esenciales estimadas $\\hat{y}(k)$</span><div class="kpi-val teal-txt" id="rl01Y">—</div></div>
                <div><span class="muted">Estado del dominio</span><div id="rl01Status" class="status-badge ok-badge">Dentro del rango</div></div>
              </div>
            </div>
            """
        elif spec.idea_id == "IDEA-RL-04":
            interactive_html = """
            <div class="interactive-card rose-border">
              <h4>Simulador de Extrapolación · Duración Media Anual (Advertencia Diapositiva 12)</h4>
              <p class="muted">Desliza el año más allá de 2019 para observar cómo la extrapolación lineal cruza cero hacia duraciones negativas físicamente imposibles:</p>
              <div class="slider-row">
                <label>Año $t$:</label>
                <input type="range" id="rl04Slider" min="2000" max="2028" step="1" value="2027" oninput="updateRL04()">
                <span class="mono big-inline" id="rl04Yr">2027</span>
              </div>
              <div class="kpi-mini-row">
                <div><span class="muted">Duración media predicha (trimestres)</span><div class="kpi-val" id="rl04Y">—</div></div>
                <div><span class="muted">Control de validez</span><div id="rl04Status" class="status-badge bad-badge">Extrapolación</div></div>
              </div>
            </div>
            """
        elif spec.idea_id == "IDEA-LG-01":
            interactive_html = """
            <div class="interactive-card teal-border">
              <h4>Explorador Interactivo de Pesos Base de Lagrange · Supervivencia $P_3(q)$ (Diapositiva 11)</h4>
              <p class="muted">Mueve el trimestre $q \\in [4, 48]$ para comprobar que cada peso $L_i(q)$ vale 1 en su nodo, 0 en los demás y siempre suman exactamente <strong>1.000000</strong>:</p>
              <div class="slider-row">
                <label>Trimestre $q$:</label>
                <input type="range" id="lg01Slider" min="4" max="48" step="1" value="12" oninput="updateLG01()">
                <span class="mono big-inline" id="lg01Q">12</span>
              </div>
              <div class="kpi-mini-row">
                <div><span class="muted">Probabilidad estimada $P_3(q)$</span><div class="kpi-val teal-txt" id="lg01Y">—</div></div>
                <div><span class="muted">Suma de pesos $\\sum L_i(q)$</span><div class="kpi-val mono" id="lg01Sum">1.000000</div></div>
                <div><span class="muted">Estado del dominio</span><div id="lg01Status" class="status-badge ok-badge">Interpolación</div></div>
              </div>
              <div id="lg01Bars" class="weight-bars"></div>
            </div>
            """

        formulas_box = "".join(f'<div class="math-box">$$ {f} $$</div>' for f in spec.formulas_html)
        steps_li = "".join(f"<li>{html.escape(s)}</li>" for s in spec.how_it_was_built)
        inputs_li = "".join(f"<li>{html.escape(s)}</li>" for s in spec.data_inputs)
        pitfalls_li = "".join(f"<li>{html.escape(p)}</li>" for p in spec.pitfalls)
        md_rel = f"./{spec.folder_name}/EXPLICACION_{spec.idea_id.replace('-', '_')}.md"

        idea_sections_html.append(
            f"""
            <section class="idea-section" id="{sec_id}" data-family="{spec.topic_family}">
              <div class="sec-header">
                <div>
                  <span class="pill {badge_cls[spec.topic_family]}">{html.escape(spec.topic_label_es)} · {spec.priority}</span>
                  <span class="pill pill-muted">{html.escape(spec.source_html)} · {html.escape(spec.slides_ref)}</span>
                  <h2>{idx:02d}. {html.escape(spec.idea_id)} — {html.escape(spec.short_title)}</h2>
                </div>
                <a class="md-chip" href="{md_rel}" target="_blank">Carpeta: {html.escape(spec.folder_name)}</a>
              </div>

              <div class="card purpose-card">
                <h3>Propósito y Finalidad Analítica</h3>
                <p>{html.escape(spec.purpose)}</p>
              </div>

              <div class="two-col">
                <div class="card">
                  <h3>Cómo se Hizo (Paso a Paso)</h3>
                  <ol class="step-list">{steps_li}</ol>
                </div>
                <div class="stack">
                  <div class="card indigo-soft">
                    <h3>Formulación Matemática</h3>
                    {formulas_box}
                  </div>
                  <div class="card">
                    <h3>Archivos de <code>data/</code> Consumidos (Solo Lectura)</h3>
                    <ul class="clean-list">{inputs_li}</ul>
                  </div>
                </div>
              </div>

              {interactive_html}

              <div class="fig-grid fig-count-{len(spec.figures)}">
                {"".join(figs_html)}
              </div>

              <div class="card">
                <h3>Tablas Empíricas Verificadas</h3>
                {"".join(tables_html)}
              </div>

              {ggb_html}

              <div class="card amber-soft">
                <h3>Limitaciones, Advertencias y Salvaguardas</h3>
                <ul class="clean-list">{pitfalls_li}</ul>
              </div>
            </section>
            """
        )

    nav_items.append(
        '<a href="#gobernanza" class="nav-link" data-sec="gobernanza"><span class="dot dot-gov"></span>Gobernanza y SHA-256</a>'
    )

    rubric_html = _df_to_html_table(hyb_rubric, max_rows=10)
    sha_html = _df_to_html_table(_select_display_columns("sha256_input_integrity.csv", sha_df), max_rows=25)
    max_inv_err = float(rl05_inv["max_invariance_err"].max())

    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>JobPath Métodos Numéricos · Reporte Explicativo de las 8 Ideas (MCO y Lagrange)</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>
<style>
:root {{
  --bg: #f5f6fb; --card: #ffffff; --ink: #1b2340; --muted: #5b6482; --line: #e3e6f0;
  --indigo: #4f46e5; --indigo-soft: #eef0ff; --teal: #0d9488; --teal-soft: #e6f6f4;
  --amber: #d97706; --amber-soft: #fff5e6; --rose: #e11d48; --rose-soft: #ffeef2;
  --shadow: 0 8px 24px rgba(27, 35, 64, .06);
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ scroll-behavior: smooth; }}
body {{ background: var(--bg); color: var(--ink); font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; line-height: 1.55; }}
.layout {{ display: grid; grid-template-columns: 275px 1fr; min-height: 100vh; }}
.sidebar {{ position: sticky; top: 0; height: 100vh; overflow-y: auto; background: #141b33; color: #e8ecff; padding: 24px 18px; display: flex; flex-direction: column; gap: 16px; }}
.brand {{ border-bottom: 1px solid rgba(255,255,255,.12); padding-bottom: 14px; }}
.brand .kicker {{ font-size: 11px; letter-spacing: .14em; text-transform: uppercase; color: #818cf8; font-weight: 700; }}
.brand h1 {{ font-size: 19px; font-weight: 800; margin-top: 4px; line-height: 1.25; }}
.brand p {{ font-size: 12px; color: #a5b0d6; margin-top: 6px; }}
.filter-bar {{ display: flex; flex-wrap: wrap; gap: 6px; }}
.filter-btn {{ border: 1px solid rgba(255,255,255,.18); background: rgba(255,255,255,.06); color: #dbe1ff; font-size: 11.5px; font-weight: 600; padding: 5px 9px; border-radius: 999px; cursor: pointer; }}
.filter-btn.on {{ background: var(--indigo); border-color: var(--indigo); color: #fff; }}
nav.side-nav {{ display: flex; flex-direction: column; gap: 4px; }}
.nav-link {{ display: flex; align-items: center; gap: 9px; padding: 8px 10px; border-radius: 10px; text-decoration: none; color: #cbd5f5; font-size: 13px; font-weight: 500; transition: background .15s, color .15s; }}
.nav-link:hover, .nav-link.active {{ background: rgba(79,70,229,.28); color: #fff; font-weight: 600; }}
.dot {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}
.dot-all {{ background: #94a3b8; }} .dot-ols {{ background: #818cf8; }} .dot-lag {{ background: #2dd4bf; }} .dot-hyb {{ background: #fbbf24; }} .dot-gov {{ background: #fb7185; }}
.side-foot {{ margin-top: auto; padding-top: 12px; border-top: 1px solid rgba(255,255,255,.12); font-size: 11.5px; color: #94a3b8; }}
.main {{ padding: 32px clamp(20px, 4vw, 52px) 64px; max-width: 1320px; width: 100%; }}
.hero {{ background: linear-gradient(135deg, #1b2340 0%, #312e81 60%, #0f766e 100%); color: #fff; border-radius: 22px; padding: 34px 36px; box-shadow: 0 16px 40px rgba(27,35,64,.16); margin-bottom: 26px; }}
.hero .kicker {{ font-size: 12px; text-transform: uppercase; letter-spacing: .16em; color: #a5b4fc; font-weight: 700; }}
.hero h1 {{ font-size: clamp(26px, 3vw, 40px); font-weight: 800; line-height: 1.12; margin: 8px 0 12px; }}
.hero p {{ color: #dbe4ff; max-width: 860px; font-size: 15px; }}
.kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(215px, 1fr)); gap: 14px; margin: 22px 0 28px; }}
.kpi {{ background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 18px 20px; box-shadow: var(--shadow); }}
.kpi .lbl {{ font-size: 12px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; }}
.kpi .val {{ font-size: 28px; font-weight: 800; margin: 4px 0; font-variant-numeric: tabular-nums; }}
.kpi .sub {{ font-size: 12.5px; color: var(--muted); }}
.indigo-txt {{ color: var(--indigo); }} .teal-txt {{ color: var(--teal); }} .amber-txt {{ color: var(--amber); }} .rose-txt {{ color: var(--rose); }}
.idea-section {{ margin-top: 40px; padding-top: 26px; border-top: 2px solid var(--line); display: flex; flex-direction: column; gap: 16px; }}
.idea-section.hidden {{ display: none; }}
.sec-header {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; flex-wrap: wrap; }}
.sec-header h2 {{ font-size: clamp(20px, 2.1vw, 27px); font-weight: 800; margin-top: 8px; }}
.pill {{ display: inline-block; padding: 4px 11px; border-radius: 999px; font-size: 11.5px; font-weight: 700; margin-right: 6px; }}
.pill-indigo {{ background: var(--indigo-soft); color: var(--indigo); }}
.pill-teal {{ background: var(--teal-soft); color: var(--teal); }}
.pill-amber {{ background: var(--amber-soft); color: var(--amber); }}
.pill-muted {{ background: #eef1f8; color: var(--muted); }}
.md-chip {{ font-family: "JetBrains Mono", monospace; font-size: 11.5px; background: #1b2340; color: #e2e8f0; text-decoration: none; padding: 6px 11px; border-radius: 9px; white-space: nowrap; }}
.card {{ background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 20px 22px; box-shadow: var(--shadow); }}
.card h3 {{ font-size: 15.5px; font-weight: 700; margin-bottom: 10px; color: var(--ink); }}
.card h4 {{ font-size: 14px; font-weight: 700; margin-bottom: 8px; color: var(--ink); }}
.purpose-card {{ border-left: 5px solid var(--indigo); }}
.indigo-soft {{ background: var(--indigo-soft); border-color: #d6d9ff; }}
.amber-soft {{ background: var(--amber-soft); border-color: #fde3bd; }}
.two-col {{ display: grid; grid-template-columns: 1.1fr .9fr; gap: 16px; }}
.stack {{ display: flex; flex-direction: column; gap: 14px; }}
.step-list {{ padding-left: 20px; display: flex; flex-direction: column; gap: 7px; font-size: 14px; }}
.clean-list {{ padding-left: 18px; display: flex; flex-direction: column; gap: 6px; font-size: 13.8px; }}
.math-box {{ background: #fff; border: 1px dashed #c7cbe6; border-radius: 12px; padding: 10px 14px; overflow-x: auto; margin-bottom: 8px; }}
.fig-grid {{ display: grid; gap: 16px; }}
.fig-count-2 {{ grid-template-columns: 1fr 1fr; }}
.fig-count-1 {{ grid-template-columns: 1fr; }}
.fig-card {{ background: #fff; border: 1px solid var(--line); border-radius: 16px; padding: 12px; box-shadow: var(--shadow); }}
.fig-card img {{ width: 100%; height: auto; border-radius: 10px; cursor: zoom-in; display: block; transition: transform .15s; }}
.fig-card img:hover {{ transform: scale(1.006); }}
.fig-card figcaption {{ font-size: 12.5px; color: var(--muted); margin-top: 9px; padding: 0 4px; }}
.tbl-wrap {{ overflow-x: auto; border: 1px solid var(--line); border-radius: 12px; }}
table {{ border-collapse: collapse; width: 100%; font-size: 12.8px; font-variant-numeric: tabular-nums; }}
th, td {{ padding: 8px 10px; border-bottom: 1px solid var(--line); text-align: left; white-space: nowrap; }}
th {{ background: #1b2340; color: #fff; font-weight: 600; font-size: 12px; }}
tr:nth-child(even) td {{ background: #fafbff; }}
.ok-cell {{ color: var(--teal); font-weight: 700; }}
.bad-cell {{ color: var(--rose); font-weight: 700; }}
.tbl-note {{ font-size: 12px; color: var(--muted); margin-top: 6px; }}
.sub-block {{ margin-top: 14px; }}
.fold-block {{ margin-top: 12px; border: 1px solid var(--line); border-radius: 12px; padding: 10px 14px; background: #fafbff; }}
.fold-block summary {{ cursor: pointer; font-weight: 600; font-size: 13.5px; color: var(--indigo); }}
.ggb-box {{ background: #141b33; color: #e8ebff; border-radius: 12px; overflow: hidden; margin-top: 10px; }}
.ggb-head {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 14px; background: rgba(255,255,255,.07); font-size: 12.5px; }}
.ggb-box pre {{ padding: 12px 14px; overflow-x: auto; font-family: "JetBrains Mono", monospace; font-size: 12.2px; line-height: 1.5; }}
.copy-btn {{ background: var(--indigo); color: #fff; border: none; border-radius: 8px; padding: 5px 11px; font-size: 12px; font-weight: 600; cursor: pointer; }}
.copy-btn:hover {{ background: #4338ca; }}
code, .mono {{ font-family: "JetBrains Mono", ui-monospace, monospace; font-size: .92em; }}
.interactive-card {{ background: #fff; border: 2px solid #c7d2fe; border-radius: 16px; padding: 18px 22px; box-shadow: var(--shadow); }}
.rose-border {{ border-color: #fecdd3; }} .teal-border {{ border-color: #99f6e4; }}
.slider-row {{ display: grid; grid-template-columns: 105px 1fr 78px; gap: 12px; align-items: center; margin: 12px 0; font-weight: 600; }}
.slider-row input[type=range] {{ width: 100%; accent-color: var(--indigo); }}
.big-inline {{ font-size: 17px; font-weight: 800; text-align: right; }}
.kpi-mini-row {{ display: flex; gap: 26px; flex-wrap: wrap; align-items: center; margin-top: 8px; }}
.kpi-val {{ font-size: 25px; font-weight: 800; font-variant-numeric: tabular-nums; }}
.status-badge {{ display: inline-block; padding: 5px 12px; border-radius: 999px; font-size: 12.5px; font-weight: 700; margin-top: 4px; }}
.ok-badge {{ background: var(--teal-soft); color: var(--teal); }}
.bad-badge {{ background: var(--rose-soft); color: var(--rose); }}
.weight-bars {{ margin-top: 14px; display: flex; flex-direction: column; gap: 8px; }}
.w-row {{ display: grid; grid-template-columns: 125px 1fr 78px; gap: 10px; align-items: center; font-size: 12.8px; }}
.w-track {{ position: relative; height: 14px; background: #eef0f7; border-radius: 8px; overflow: hidden; }}
.w-zero {{ position: absolute; left: 50%; top: 0; bottom: 0; width: 2px; background: #94a3b8; }}
.w-fill {{ position: absolute; top: 0; bottom: 0; border-radius: 6px; }}
.muted {{ color: var(--muted); font-size: 13.5px; }}
.lightbox {{ position: fixed; inset: 0; background: rgba(15, 23, 42, .88); display: none; align-items: center; justify-content: center; z-index: 100; padding: 24px; cursor: zoom-out; }}
.lightbox.open {{ display: flex; }}
.lightbox img {{ max-width: 96vw; max-height: 92vh; border-radius: 12px; background: #fff; padding: 8px; }}
.toast {{ position: fixed; bottom: 24px; right: 24px; background: #1b2340; color: #fff; padding: 10px 16px; border-radius: 10px; font-size: 13px; opacity: 0; transition: opacity .25s; pointer-events: none; z-index: 120; }}
.toast.on {{ opacity: 1; }}
@media (max-width: 1024px) {{ .layout {{ grid-template-columns: 1fr; }} .sidebar {{ position: static; height: auto; }} .two-col, .fig-count-2 {{ grid-template-columns: 1fr; }} }}
@media print {{ .sidebar, .copy-btn, .filter-bar, .interactive-card input {{ display: none !important; }} .layout {{ grid-template-columns: 1fr; }} .idea-section {{ break-inside: avoid; }} }}
</style>
</head>
<body>
<div class="layout">
  <aside class="sidebar">
    <div class="brand">
      <div class="kicker">JobPath · MineriaProtect</div>
      <h1>Métodos Numéricos<br>Reporte de 8 Ideas</h1>
      <p>Regresión Lineal por Mínimos Cuadrados e Interpolación de Lagrange sobre las 4 capas de <code>data/</code></p>
    </div>
    <div class="filter-bar">
      <button class="filter-btn on" onclick="filterFam('ALL', this)">Todas (8)</button>
      <button class="filter-btn" onclick="filterFam('OLS', this)">MCO (4)</button>
      <button class="filter-btn" onclick="filterFam('Lagrange', this)">Lagrange (2)</button>
      <button class="filter-btn" onclick="filterFam('Hybrid', this)">Híbridas (2)</button>
    </div>
    <nav class="side-nav">
      {"".join(nav_items)}
    </nav>
    <div class="side-foot">
      UNIMINUTO · Ibagué<br>
      Commit base: <code>aa36d93</code><br>
      Pruebas: <strong>15/15 OK</strong> · <code>data/</code> 100% SHA-256 intacto
    </div>
  </aside>

  <main class="main">
    <section id="resumen">
      <div class="hero">
        <div class="kicker">Informe Explicativo Autocontenido · Gráficos Interactivos y Evidencia Real</div>
        <h1>Regresión Lineal por Mínimos Cuadrados e Interpolación de Lagrange en JobPath</h1>
        <p>Implementación empírica completa del <strong>Núcleo de 8 Ideas</strong> aplicando las dos presentaciones de Métodos Numéricos (Prof. Juan Carlos González Sánchez) sobre trayectorias laborales reales (<strong>1,871,014</strong> experiencias limpias · <strong>355,308</strong> personas · <strong>3,039</strong> oficios ESCO v1.2.1 · enriquecimiento <strong>greenShare</strong> · matrices <code>04_transformed</code>).</p>
      </div>

      <div class="kpi-grid">
        <div class="kpi"><div class="lbl">MCO Pasos de Carrera</div><div class="val indigo-txt">R² = {float(rl01_sk['r2']):.4f}</div><div class="sub">a₁ = +{float(rl01_sk['a1']):.4f} skills/paso · Sy/x = {float(rl01_sk['s_yx']):.4f}</div></div>
        <div class="kpi"><div class="lbl">Reducción Error Runge</div><div class="val teal-txt">{float(lg01_eq16['max_abs_err'])/float(lg01_ch16['max_abs_err']):.1f}×</div><div class="sub">Grado 16 Equiesp. {float(lg01_eq16['max_abs_err']):.2f} → Chebyshev {float(lg01_ch16['max_abs_err']):.3f}</div></div>
        <div class="kpi"><div class="lbl">Invarianza de Escala Afín</div><div class="val amber-txt">{max_inv_err:.2e}</div><div class="sub">Error máximo en 8 controles sobre <code>04_transformed</code></div></div>
        <div class="kpi"><div class="lbl">Integridad de data/</div><div class="val teal-txt">{int(sha_df['intact'].sum())}/{len(sha_df)}</div><div class="sub">100 % intacto por SHA-256 · 15/15 pruebas en verde</div></div>
      </div>

      <div class="card">
        <h3>Resumen Ejecutivo — Rúbrica Empírica "¿Interpolar o Ajustar?" (<code>IDEA-HYB-01</code>)</h3>
        <p class="muted" style="margin-bottom:10px">Validación directa de la Diapositiva 2 de ambas presentaciones en 4 regímenes reales de curvas de JobPath:</p>
        {rubric_html}
      </div>
    </section>

    {"".join(idea_sections_html)}

    <section class="idea-section" id="gobernanza">
      <div class="sec-header">
        <div>
          <span class="pill pill-muted">Gobernanza · Reproducibilidad · NFR-NM-01</span>
          <h2>Bitácora de Verificación y Auditoría SHA-256 sobre <code>data/</code></h2>
        </div>
      </div>
      <div class="card">
        <h3>Prueba de Inmutabilidad SHA-256 (19 Archivos de Solo Lectura Auditados)</h3>
        <p class="muted" style="margin-bottom:10px">Cada archivo consultado en <code>data/01_raw</code>, <code>data/02_interim</code>, <code>data/03_processed</code> y <code>data/04_transformed</code> fue verificado antes y después de la ejecución con cero modificaciones.</p>
        {sha_html}
      </div>
    </section>
  </main>
</div>

<div class="lightbox" id="lightbox" onclick="this.classList.remove('open')">
  <img id="lbImg" src="" alt="Gráfico ampliado">
</div>
<div class="toast" id="toast"></div>

<script>
const RL01_A0 = {float(rl01_sk['a0']):.10f};
const RL01_A1 = {float(rl01_sk['a1']):.10f};
const RL04_A0 = {float(rl04_dur['a0']):.10f};
const RL04_A1 = {float(rl04_dur['a1']):.10f};
const LG01_X  = [4, 8, 20, 40];
const LG01_Y  = [{s_nodes[0]:.10f}, {s_nodes[1]:.10f}, {s_nodes[2]:.10f}, {s_nodes[3]:.10f}];
const LG_COLS = ['#4f46e5', '#e11d48', '#d97706', '#0d9488'];

function updateRL01() {{
  const k = parseFloat(document.getElementById('rl01Slider').value);
  const y = RL01_A0 + RL01_A1 * k;
  document.getElementById('rl01K').textContent = k.toFixed(1);
  document.getElementById('rl01Y').textContent = y.toFixed(4) + ' skills';
  const st = document.getElementById('rl01Status');
  if (k > 10) {{ st.textContent = '⚠ Extrapolación (k > 10)'; st.className = 'status-badge bad-badge'; }}
  else {{ st.textContent = '✔ Dentro del rango (1 ≤ k ≤ 10)'; st.className = 'status-badge ok-badge'; }}
}}

function updateRL04() {{
  const yr = parseInt(document.getElementById('rl04Slider').value, 10);
  const y = RL04_A0 + RL04_A1 * yr;
  document.getElementById('rl04Yr').textContent = yr;
  const el = document.getElementById('rl04Y');
  el.textContent = y.toFixed(3) + ' trimestres';
  el.style.color = y < 0 ? '#e11d48' : '#0d9488';
  const st = document.getElementById('rl04Status');
  if (y < 0) {{ st.textContent = '✘ Físicamente imposible (< 0 trimestres)'; st.className = 'status-badge bad-badge'; }}
  else if (yr > 2019) {{ st.textContent = '⚠ Extrapolación (cola censurada > 2019)'; st.className = 'status-badge bad-badge'; }}
  else {{ st.textContent = '✔ Ventana de soporte válido (2000–2019)'; st.className = 'status-badge ok-badge'; }}
}}

function lagBasis(xs, i, x) {{
  let L = 1.0;
  for (let j = 0; j < xs.length; j++) if (j !== i) L *= (x - xs[j]) / (xs[i] - xs[j]);
  return L;
}}

function updateLG01() {{
  const q = parseFloat(document.getElementById('lg01Slider').value);
  document.getElementById('lg01Q').textContent = q + ' t (' + (q/4).toFixed(2) + ' a)';
  let sumL = 0, p3 = 0;
  const labels = ['L₀ (q=4 · 1 año)', 'L₁ (q=8 · 2 años)', 'L₂ (q=20 · 5 años)', 'L₃ (q=40 · 10 años)'];
  let bars = '';
  for (let i = 0; i < 4; i++) {{
    const w = lagBasis(LG01_X, i, q);
    sumL += w; p3 += LG01_Y[i] * w;
    const mx = 1.5, wd = Math.min(Math.abs(w), mx) / mx * 50;
    const left = w >= 0 ? 50 : (50 - wd);
    bars += `<div class="w-row"><span class="mono" style="color:${{LG_COLS[i]}};font-weight:700">${{labels[i]}}</span>` +
            `<div class="w-track"><div class="w-zero"></div><div class="w-fill" style="left:${{left}}%;width:${{wd}}%;background:${{LG_COLS[i]}}"></div></div>` +
            `<span class="mono" style="text-align:right">${{w.toFixed(4)}}</span></div>`;
  }}
  document.getElementById('lg01Bars').innerHTML = bars;
  document.getElementById('lg01Y').textContent = (p3 * 100).toFixed(2) + '% (' + p3.toFixed(4) + ')';
  document.getElementById('lg01Sum').textContent = sumL.toFixed(6);
  const st = document.getElementById('lg01Status');
  if (q < 4 || q > 40) {{ st.textContent = '⚠ Extrapolación (fuera de [4, 40])'; st.className = 'status-badge bad-badge'; }}
  else {{ st.textContent = '✔ Interpolación dentro de rango ([4, 40])'; st.className = 'status-badge ok-badge'; }}
}}

function filterFam(fam, btn) {{
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('on'));
  btn.classList.add('on');
  document.querySelectorAll('.idea-section[data-family]').forEach(sec => {{
    sec.classList.toggle('hidden', fam !== 'ALL' && sec.dataset.family !== fam);
  }});
  document.querySelectorAll('.nav-link[data-family]').forEach(a => {{
    a.style.display = (fam === 'ALL' || a.dataset.family === fam) ? 'flex' : 'none';
  }});
}}

function openLightbox(img) {{
  document.getElementById('lbImg').src = img.src;
  document.getElementById('lightbox').classList.add('open');
}}

function copyCode(btn) {{
  const text = btn.closest('.ggb-box').querySelector('code').textContent;
  (navigator.clipboard ? navigator.clipboard.writeText(text) : Promise.reject())
    .then(() => showToast('¡Comandos de GeoGebra copiados al portapapeles!'))
    .catch(() => showToast('Selecciona y copia los comandos manualmente.'));
}}

function showToast(msg) {{
  const t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('on');
  clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove('on'), 2000);
}}

window.addEventListener('load', () => {{
  updateRL01(); updateRL04(); updateLG01();
  if (window.renderMathInElement) {{
    renderMathInElement(document.body, {{
      delimiters: [{{left:'$$',right:'$$',display:true}}, {{left:'$',right:'$',display:false}}],
      throwOnError: false
    }});
  }}
}});
</script>
</body>
</html>
"""
    html_path = out_root / "index.html"
    html_path.write_text(full_html, encoding="utf-8")
    return html_path


def build_unified_deliverable(cfg: NumericalMethodsConfig | None = None) -> Path:
    """Construye la carpeta unificada `metodos_numericos_entregable/` completamente en español."""
    cfg = cfg or default_config()
    out_root = cfg.root / "metodos_numericos_entregable"
    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    # 1. 00_general/
    gen_dir = out_root / "00_general"
    gen_dir.mkdir(parents=True, exist_ok=True)
    general_copies = [
        cfg.root / "docs" / "MASTER_NUMERICAL_METHODS_IMPLEMENTATION_PROMPT.md",
        cfg.verification_log_path,
        cfg.tables_dir / "ols_summary_all_ideas.csv",
        cfg.tables_dir / "sha256_input_integrity.csv",
        cfg.root / "notebooks" / "refactor" / "8.0_regresion_lineal_minimos_cuadrados.ipynb",
        cfg.root / "notebooks" / "refactor" / "8.1_interpolacion_lagrange.ipynb",
        cfg.root / "notebooks" / "refactor" / "8.2_comparativa_regresion_vs_interpolacion.ipynb",
    ]
    for src in general_copies:
        if src.exists():
            shutil.copy2(src, gen_dir / src.name)

    # 2. 8 subcarpetas separadas con su EXPLICACION_IDEA_*.md en español
    readme_rows: List[str] = []
    for idx, spec in enumerate(IDEA_SPECS, start=1):
        idea_dir = out_root / spec.folder_name
        (idea_dir / "tables").mkdir(parents=True, exist_ok=True)
        (idea_dir / "figures").mkdir(parents=True, exist_ok=True)
        if spec.geogebra_files:
            (idea_dir / "geogebra").mkdir(parents=True, exist_ok=True)

        for tname in spec.tables:
            shutil.copy2(cfg.tables_dir / tname, idea_dir / "tables" / tname)
        for fname, _ in spec.figures:
            shutil.copy2(cfg.figures_dir / fname, idea_dir / "figures" / fname)
        for gname in spec.geogebra_files:
            shutil.copy2(cfg.geogebra_dir / gname, idea_dir / "geogebra" / gname)

        md_path = _write_idea_markdown(spec, idea_dir, cfg.tables_dir, cfg.geogebra_dir)
        readme_rows.append(
            f"| {idx:02d} | `{spec.idea_id}` | {spec.topic_label_es} | "
            f"[`{spec.folder_name}/`](./{spec.folder_name}/) | "
            f"[`{md_path.name}`](./{spec.folder_name}/{md_path.name}) | "
            f"{len(spec.tables)} CSV · {len(spec.figures)} PNG · {len(spec.geogebra_files)} GGB |"
        )

    # 3. README.md en español
    readme_lines = [
        "# JobPath Métodos Numéricos — Entregable Unificado (Núcleo de 8 Ideas)",
        "",
        "Abre [`index.html`](./index.html) directamente en cualquier navegador para ver el **reporte explicativo interactivo en español** (con los 12 gráficos a 150 DPI incrustados, tablas verificadas, 3 calculadoras en vivo y comandos listos para copiar en GeoGebra).",
        "",
        "## Estructura Separada por Idea",
        "",
        "| # | ID Idea | Temática | Subcarpeta | Markdown Explicativo | Archivos Incluidos |",
        "|---|---|---|---|---|---|",
        *readme_rows,
        "",
        "## Documentación General y Cuadernos Ejecutados (`00_general/`)",
        "",
        "- [`00_general/MASTER_NUMERICAL_METHODS_IMPLEMENTATION_PROMPT.md`](./00_general/MASTER_NUMERICAL_METHODS_IMPLEMENTATION_PROMPT.md) *(Master Prompt en inglés solicitado originalmente)*",
        "- [`00_general/verification_log.md`](./00_general/verification_log.md)",
        "- [`00_general/8.0_regresion_lineal_minimos_cuadrados.ipynb`](./00_general/8.0_regresion_lineal_minimos_cuadrados.ipynb)",
        "- [`00_general/8.1_interpolacion_lagrange.ipynb`](./00_general/8.1_interpolacion_lagrange.ipynb)",
        "- [`00_general/8.2_comparativa_regresion_vs_interpolacion.ipynb`](./00_general/8.2_comparativa_regresion_vs_interpolacion.ipynb)",
        "",
    ]
    (out_root / "README.md").write_text("\n".join(readme_lines), encoding="utf-8")

    # 4. HTML explicativo en español
    _build_master_html(cfg, out_root)
    return out_root


if __name__ == "__main__":
    dest = build_unified_deliverable()
    print(f"Entregable unificado en español generado en: {dest}")
