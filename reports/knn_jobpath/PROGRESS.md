# Progreso de Implementación · `7.2_knn.ipynb` (JobPath)

## Estado General: COMPLETADO (ETAPAS 1 A 8 VERIFICADAS Y AUDITADAS)

### Resumen por etapa
- **Etapa 1 · Módulos base (`COMPLETADA`):** `config.py`, `feature_blocks.py`, `models.py`, `self_tests.py` (paquete SOLID en `scripts/ScriptsCsv/KNN/`, `14` archivos en inglés con type hints y docstrings, `8/8` pruebas unitarias aprobadas).
- **Etapa 2 · Piloto, tuning y curvas de aprendizaje (`COMPLETADA`):** `pilot_benchmark.py`, `evaluation.py`. Piloto por persona (`kd_tree` en `KNN-D`, `brute` en `KNN-G`/`KNN-W`, `n_jobs=8`, RSS estable). Ajuste honesto en `StratifiedGroupKFold(5)` al `10 %` (`228` intentos, `0` personas solapadas). Curva de aprendizaje `10 % / 25 % / 50 %` con protocolo unificado de pliegue único fijo disjunto para `KNN-W` y bootstrap pareado por persona (`06f`), preservando ajuste principal y umbral $\tau^*$ en `5-fold CV` completo.
- **Etapa 3 · Módulos de análisis y predicción reanudable (`COMPLETADA`):** `geometry.py`, `version_comparison.py` (5 regímenes incluyendo winsorización Tukey en `6` continuas, entrenamiento exclusivo sin outliers y Versión B + verificación full-test `KNN-D`), `chunked_predictor.py`, `neighbors_explainer.py`, `patterns.py` (`K1`–`K6`), `plots.py` (`knn01`–`knn13`), `pipeline.py`.
- **Etapa 4 · Decisión Paso 9 y checkpoints 100 % Test (`COMPLETADA`):** aprobado por el usuario evaluar el `100 %` de `test` (`347,720` filas, `70,419` personas) en las tres variantes (`KNN-D`, `KNN-G` `kd_tree`, `KNN-W` `brute` CSR) mediante `70/70` checkpoints atómicos en disco (`reports/knn_jobpath/cache/`, verificación bit-a-bit `diff = 0.000e+00`).
- **Etapa 5 · Construcción del cuaderno (`COMPLETADA`):** `notebooks/refactor/7.2_knn.ipynb` (`48` celdas: ficha, Secciones `1`–`15` con estructura `¿Qué hace? / ¿Por qué existe? / ¿Qué recibe y qué entrega? / Papel en el proyecto` + `Lectura`, Sección `16` y Sección `17`).
- **Etapa 6 · Ejecución completa `Run All` (`COMPLETADA`):** ejecutado sin errores con `nbclient` (`29.78 min`), exportando `48` tablas CSV y `13` figuras PNG.
- **Etapa 7 · Redacción analítica y reejecución de verificación (`COMPLETADA`):** redactadas las `15` celdas de `Lectura`, síntesis de `7` patrones de negocio (`5` ocupacionales ISCO), Sección `16` (respuesta explícita a la pregunta guía) y Sección `17` (guía en lenguaje sencillo). Reejecución completa `Run All` de verificación completada en `16.50 min` (`990.2 s`, `exit code 0`, ejecuciones `1..15`, cero errores) y tiempos en vivo sincronizados con los CSV finales.
- **Etapa 8 · Auditorías finales (`COMPLETADA · TODAS LIMPIAS`):**
  - Auditoría de números entre backticks: `1,534` auditados, `0` sin trazabilidad.
  - Emojis o símbolos decorativos: `0` (tanto en `.ipynb` como en los `14` `.py` y las `13` figuras).
  - Celdas de código duplicadas: `0`.
  - Celdas pesadas (`> 45` líneas o `def`/`class` en el cuaderno): `0`.
  - Pruebas unitarias (`run_all_knn_unit_tests`): `True` (`8/8`).
  - Integridad SHA-256 de insumos: `13/13` archivos fuente intactos (`sin_cambios = True`).
  - Idioma: código en inglés; markdown, salidas legibles, tablas y figuras en español.

### Resultados oficiales verificados en `100 %` Test (Versión A · `347,720` filas / `70,419` personas)
- **`KNN-W` (`k=101`, `uniform`, `euclidean`, `w=8`, $\tau^*=0.28$):** `PR-AUC = 0.5247 [0.5193, 0.5288]`, `ROC-AUC = 0.7245 [0.7220, 0.7271]`, `F1 = 0.5471 [0.5441, 0.5499]`, `Brier = 0.1817`, `ECE = 0.0091`, tiempo de predicción acumulado `29,146.83 s`.
- **`KNN-G` (`k=101`, `uniform`, `manhattan`, `w_g=8`, `kd_tree`, $\tau^*=0.27$):** `PR-AUC = 0.4928 [0.4880, 0.4971]`, `ROC-AUC = 0.6919 [0.6897, 0.6945]`, `F1 = 0.5186`, `Brier = 0.1887`, tiempo `1,104.71 s`.
- **`KNN-D` (`k=101`, `uniform`, `manhattan`, `kd_tree`, $\tau^*=0.27$):** `PR-AUC = 0.4652 [0.4609, 0.4693]`, `ROC-AUC = 0.6677 [0.6651, 0.6705]`, `F1 = 0.5010`, `Brier = 0.1936`, tiempo `71.59 s`.
- **Diferencias pareadas (IC 95 % por bootstrap de personas):** `KNN-W` supera a `Logística Regularizada (6.0)` (`+0.0137 [+0.0119, +0.0157]`), a `NB-H (7.1)` (`+0.0285 [+0.0267, +0.0309]`), a `NB-B (7.1)` (`+0.0417`) y a `KNN-G` (`+0.0318`); `KNN-D` pierde frente a `HistGradientBoosting (6.0)` (`-0.0298 [-0.0313, -0.0282]`).
- **Entrenamiento exclusivo sin outliers (`KNN-D`):** degrada el desempeño tanto en CV (`-0.01269 [-0.01630, -0.00848]` en `manhattan`; `-0.01734` en `euclidean`) como en `test` completo (`0.4652 -> 0.4496`, `-0.01561 [-0.01780, -0.01350]`).

---

## Revisión Posterior (`F1` a `F10` · Sección 14A y nueva Sección 17)

- **Etapa R0 (`COMPLETADA`):** respaldo verificado por SHA-256 en `reports/knn_jobpath/backup/7.2_knn_pre_revision.ipynb`; auditoría previa confirmada (`OneHotEncoder(drop="first")` omite `0110.1` con `47` filas cero en `train` y `20` en `test`; `veces_ese_oficio` calculado sobre todo el historial con `transform("size")`; `manifest.json` de `KNN-W` contiene los `70` tiempos individuales).
- **Etapa R1 (`COMPLETADA`):** creado módulo SOLID `scripts/ScriptsCsv/KNN/revision_checks.py`, añadido `plot_knn_w_block_times` (`knn14`) en `plots.py`, extendida la auditoría numérica en `pipeline.py` (formato inglés y español + detección de `<<`) y aprobadas las `10/10` pruebas unitarias (`run_all_knn_unit_tests`, incluyendo equivalencia `0.0` de `ExactOccupationPrefilterKNN` bajo `drop="first"` e interpolación *tie-aware*).
- **Etapa R2 (`EN CURSO`):** ejecutando únicamente las `5` celdas nuevas de la Sección 14A en cuaderno temporal aislado (`run_section_14a.ipynb`) usando exclusivamente cachés en disco (sin recalcular `KNN-W` ni `KNN-G` completos).
