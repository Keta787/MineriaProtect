# Progreso de Implementación · `7.1_naive_bayes.ipynb`

## Estado General: REVISIÓN METODOLÓGICA `F1`–`F7` EN PROGRESO (Etapas 0–2 completadas; Etapa 3 en ejecución)

### Versión inicial (COMPLETADA)
- Paquete `scripts/ScriptsCsv/NaiveBayes/`, cuaderno `notebooks/refactor/7.1_naive_bayes.ipynb` (`58` celdas), `37` tablas CSV, `15` figuras PNG y Sección 15 completados y verificados (`13/13` huellas SHA-256 intactas).

### Revisión metodológica y editorial (`F1`–`F7`)
- **Paso 0 · Respaldo (COMPLETADO):** copia íntegra del cuaderno original en `reports/naive_bayes_jobpath/backup/7.1_naive_bayes_original.ipynb` (`SHA-256: 817f410f0096aefc...`).
- **Etapa 1 · Paquete `NaiveBayes/` y pruebas (COMPLETADA):**
  - `config.py`: importación dinámica de `IQR_WINSOR_BOUNDS_INFO`, rejilla extendida de `var_smoothing` para `NB-G`/`NB-G*` (`1e-12` a `500.0`), `MODEL_NB_G_STAR`, corrección de metadatos de `n_skills_sin_tipo_rob` y `tiene_sin_tipo`.
  - `feature_blocks.py`: auditoría de columnas casi constantes (`< 1 %` minoría en `train`: `tiene_skills` `0.0006 %` y `tiene_sin_tipo` `0.9006 %` excluidas en `NB-G*`; `n_skills_sin_tipo_rob` documentada con `0.9006 %`).
  - `outlier_diagnostics.py` y `version_comparison.py`: tabla dinámica de alcance de Versión B (`IQR_WINSOR_BOUNDS_INFO`), razón de desviación estándar, proporciones `< 0.05` y `> 0.95` de `NB-G` sin ajustar, etiqueta `"Sin ajustar"`, experimentos ajustados **E1**, **E2** (winsorización Tukey en RAM de las 7 continuas con re-selección OOF e IC 95 % pareado) y **E3** (`var_smoothing` x {A, A winsorizada, B} en `StratifiedGroupKFold(5)`).
  - `evaluation.py`: `NB-G*` en Secciones 5 y 6 únicamente, reproducción exacta de `6.0` (`Logística Regularizada`: `PR-AUC 0.5109`, `diff 4.7e-5`; `HistGradientBoosting`: `PR-AUC 0.4951`, `diff 2.4e-5`, ambos `<< 5e-4`), bootstrap pareado por persona (`300` remuestreos, semilla `42`), métricas a igual tasa de alerta que `NB-H`, tablas homogéneas (*like-for-like*) y Brier restringido a modelos sin ponderación de clases.
  - `occupation_analysis.py` y `patterns.py`: brecha `test - train` y alerta `> 5 pp` en `O1`, `O5a`, `O5b`, `P1b`, `P5`; `O6` con brecha absoluta pred vs. obs, Spearman `rho` y fracción condicional `4d | mismo 1d`; `P1` con máximo `|LLR|` y participación de bloques en log-odds sobre `test`; `P3` con perfiles `D01`/`D10` en `train` y `test`; `P4` con razón de pendiente y brecha por tramo.
  - `plots.py`, `pipeline.py`, `self_tests.py`: figura `NB16` (E3), exportación de todas las tablas nuevas, pruebas unitarias (`run_hybrid_naive_bayes_self_tests` + `run_revision_self_tests`: `100 %` aprobadas).
- **Etapa 2 · Ediciones del cuaderno (COMPLETADA):** `59` celdas (`18` celdas de código únicas, `0` duplicados, `0` emojis, tildes corregidas en todos los `print`, inserción de celda **Registro de correcciones** antes de Sección 14).
- **Etapa 3 · Ejecución completa (EN CURSO):** corrida íntegra con `nbclient` (timeout `3600 s`) con medición de RSS pico.
- **Próximos pasos:** Etapa 4 (reescritura estricta de todas las celdas «Lectura», Registro de correcciones, Sección 14 y Sección 15 con cifras reales ejecutadas + segunda corrida de verificación) y Etapa 5 (auditoría automática de números entre backticks, controles finales y resumen en español).
