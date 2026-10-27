# Journal - EDA columnas objetivo (JobPath)
Fecha inicio: 2026-10-25T16:00:00
Skill: scientific-eda
Dataset: data/03_processed/empleos_con_competencias_limpio_sin_outliers.csv (341090 x 23)

## [CONTEXT] 2026-10-25T16:00:00
- Leído README.md: Proyecto JobPath, KDD/CRISP-DM, JobHop v2 + ESCO v1.2.1, fase actual centrada en preparación/transformación. Pendiente construcción de S_p y minería.
- Leído docs/INFORME_EDA.md: EDA previo enriquecido con competencias ESCO, variante sin cola larga (341090 filas). Reglas de honestidad visual.
- Leído docs/EDA.md: Guía para cruce nivel educativo x grupo ocupacional (apilado 100%, mostrar n, tratar NaN como No reportado, un solo idioma, paleta en escala de grises).
- No se pudo leer notebooks/ENTREGAMINERIA.pdf directamente (el modelo no soporta PDF). Se infiere contexto desde README/docs.

## [DATASET] 2026-10-25T16:00:05
- Archivo utilizado: data/03_processed/empleos_con_competencias_limpio_sin_outliers.csv
- Verificado con head: resume_id,start_date,end_date,university_level,...
- Grano: 1 fila = 1 experiencia laboral. resume_id agrupa trayectoria.

## [MAPPING] 2026-10-25T16:00:10
Columnas objetivo solicitadas -> reales:
- Resume_id -> resume_id
- Period_Time -> crear desde start_date - end_date (conservar 'Present' si end_date=='Present')
- University_Level -> university_level (NaN/vacío -> 'No reportado', orden canónico: No reportado, Secondary school, Bachelor, Master, PhD). Traducción solo visual.
- Isco_group -> unificar isco_group_label (prioritario, legible) con isco_group (código). Revisar duplicidad.
- Skill_competence -> n_skills_competence (requerimiento del oficio según ESCO, NO competencia de la persona)
- Skill_Knowledge -> n_skills_knowledge (requerimiento del oficio según ESCO)
- ISCO_group -> mismo que Isco_group (unificar)

Apoyo: n_skills_essential, saber_skills, veces_ese_oficio, skills/knowledge/sin_tipo, es_vigente, es_unknown_ocupacion, es_rescatado.

## [DECISION] 2026-10-25T16:00:15
Se usará isco_group_label como base principal para "Isco_group" por legibilidad; se verificará si isco_group (código) es redundante/idéntico. Se documentará hallazgo.

## [SHAPE] 2026-10-25T16:05:00
Script: analysis/2026-10-25T16-00-00-eda-columnas-objetivo/scripts/inspeccion_columnas_objetivo.py (uv run)
- shape (subconjunto): 341090 x 11
- university_level ANTES normalizar: Secondary school 132489, Bachelor 118999, Master 50273, NaN 37868, PhD 1461
- saber_skills: ok 314904, no_clasificado 26186
- isco_group únicos: 424, isco_group_label únicos: 424 (duplicados/idénticos en cardinalidad). Se confirma unificación posible; usar isco_group_label.
- nulos en skills/competence/knowledge en filas no_clasificado (esperado). 
- Top 10 isco_group_label coincide con docs/INFORME_EDA.md

## [PREP] 2026-10-25T16:10:00
Script: analysis/2026-10-25T16-00-00-eda-columnas-objetivo/scripts/generar_figuras_columnas_objetivo.py (uv run)
- Creado Period_Time = start_date + ' - ' + end_date
- Normalizado University_Level_norm a 'No reportado' para NaN/vacío
- Creado Isco_group_unif = isco_group_label
- Guardado CSV preparado: analysis/2026-10-25T16-00-00-eda-columnas-objetivo/empleos_preparado_columnas_objetivo.csv
- Figuras .webp guardadas en plots/: 01_univariado_university_level.webp, 02_univariado_isco_top15.webp, 03_univariado_skill_competence_hist.webp, 04_univariado_skill_knowledge_hist.webp, 05_univariado_period_time_top20.webp, 06_univariado_resume_id.webp, 07_bivariado_university_x_isco_stacked100.webp, 08_multivariado_correlacion_competencias.webp

## [NOTEBOOK] 2026-10-25T16:15:00
Creado notebooks/EDA_Columnas_Objetivo.ipynb con estructura completa:
- Portada, índice, contexto/metodología, carga/preparación
- Análisis univariado por cada columna objetivo con markdown antes/después (qué muestra, patrón, para qué ayuda, hallazgos)
- Análisis bivariado con cruce University_Level x Isco_group apilado 100% siguiendo reglas de docs/EDA.md + análisis Skill_competence/Skill_Knowledge x Isco_group
- Multivariado/correlación competencias
- Calidad de datos
- Hallazgos, conclusiones, recomendaciones
- Reproducibilidad
Figuras mostradas desde analysis/.../plots/*.webp y guardadas allí también.

## [DONE] 2026-10-25T16:15:30
EDA enfocado a columnas objetivo completado según requerimientos. Listo para revisión.

## [CHANGE] 2026-10-25T18:40:00
Migración visual solicitada: se reemplazan matplotlib/seaborn por **pandas + Plotly** y se
amplía el cuaderno de 8 a **26 figuras**. Se conserva la estructura de secciones 1–9 y el
markdown antes/después de cada figura (qué muestra, qué patrón evidencia, para qué ayuda,
hallazgo).
- Dataset actualizado al archivo con competencias: `data/03_processed/empleos_limpio_con_competencias .csv`
  (376.567 × 23; el journal anterior describía 341.090 filas sin outliers).
- Nuevo constructor: `scripts/construir_notebook_plotly.py` (genera las 95 celdas del cuaderno).
- Nuevo verificador: `scripts/verificar_salidas.py` (comprueba 26 figuras, cero errores y que
  conteos, medianas y n embebidos coincidan con el dataset).
- Dependencias añadidas a `requirements.txt`: `plotly>=6.0`, `kaleido>=1.0`.

## [DECISION] 2026-10-25T18:42:00
Para que el cuaderno sea versionable se evita embeber los 376.567 puntos crudos en cada figura:
- Histogramas de duración, competencias y conocimientos: conteos exactos con `np.unique` y
  `go.Bar` (sin pérdida de información, sin muestreo).
- Comparación por gran grupo ISCO: diagramas de caja con cuartiles y bigotes de 1,5 × IQR
  calculados con **todas** las filas del grupo (se descarta el violín, que exigía embeber los
  puntos). Se elimina el grupo vacío "Sin grupo" (sin competencias ESCO).
- Resultado: el .ipynb pasa de 132 MB a ~7 MB, con 26 figuras interactivas y 26 WebP.
- Etiquetas de oficios traducidas al español (se completó `OFICIO_ES`); porcentajes de los
  títulos con coma decimal.

## [OUTPUT] 2026-10-25T18:50:00
`notebooks/EDA_Columnas_Objetivo.ipynb` ejecutado con nbconvert (29 celdas de código, 66 de
markdown):
- 26 figuras Plotly inline, **0 errores**, sin advertencias de kaleido.
- 26 HTML interactivos + 26 WebP en `plots/figuras_plotly/` (plotly.min.js una sola vez).
- Verificación automática OK: suma de barras = cobertura real; medianas y n por gran grupo
  coinciden con `pandas` sobre el CSV.

## [FINDINGS] 2026-10-25T18:52:00
- Personas: 71.061; 5,3 experiencias/persona (mediana 5, máximo 20); 6,15 % con una sola.
- Period_Time: 6.229 combinaciones; top 20 = 23,4 %; pico 2012; duración mediana 5 trimestres;
  5,03 % vigentes (censurados).
- Educación: Secundaria 39,28 %, Pregrado 34,39 %, Maestría 14,53 %, No reportado 11,37 %,
  Doctorado 0,44 %.
- Ocupaciones: 424 grupos ISCO; top 5 = 22,56 %, top 10 = 31,24 %, top 50 = 56,92 %.
- Competencias: mediana 18 (máx. 69); conocimientos: mediana 3 (máx. 45; 10,25 % ceros).
  Las competencias apenas cambian entre niveles educativos (medianas 17–20), mientras los
  conocimientos suben de 2 (Secundaria) a 6 (Doctorado): dimensión clave para el modelado.
- Asociaciones débiles: V de Cramér nivel × gran grupo = 0,274; nivel × ISCO = 0,216.

## [DONE] 2026-10-25T18:55:00
Cuaderno Plotly listo para revisión; pendiente únicamente la aprobación del usuario.
