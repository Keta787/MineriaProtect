# Auditoría de la etapa de limpieza

Estado: verificada contra `script/limpiar_datos.py`, el cuaderno `script/Lectura.ipynb` y los datos reales (`data/original/` y `data/limpio/`), todo en modo solo-lectura.

## Veredicto general

La limpieza está **bien ejecutada y es reproducible dentro de su alcance** (texto, llaves y duplicados). No modifica originales, conserva ceros a la izquierda, y documenta problema → transformación → impacto por archivo. **Falla contra la guía de clase en lo que la guía exige y el proyecto no implementó**: no hay IQR/outliers, no hay clasificación MCAR/MAR/MNAR, el dedupe en JobHop ocurre *después* de imputar nulos, y faltan checks de "valores imposibles". Las cifras documentadas **reconcilian exactamente** con los datos finales (verificado).

## Tabla de estados

| Elemento | Estado | Evidencia encontrada | Problema | Qué debería hacerse |
|---|---|---|---|---|
| 1. Diagnóstico origen | 🟢 | Originales nunca modificados; `dtype=str`, `utf-8-sig`; regla de oro documentada (CEL 1). | Ninguno | Mantener |
| 2. Duplicados | 🟡 | Detección + eliminación; verificado: original 36.249 dup, limpio 0; −4 por `code` (occupations), −21 por `conceptUri` (skills) | En JobHop el dedupe va **después** del fill de nulos (orden inverso al de clase) | Reordenar a: dedupe → categorías → nulos → outliers → validar, o justificar la excepción |
| 3. Categorías | 🟡 | `strip()` general; dominios coherentes (status `released`; `university_level` 5 valores; relationType/skillType binarios) | No hay paso formal de "unificación/variantes" ni dominio esperado chequeado | Añadir checklist de dominios canónicos (aunque hoy dé 0 inconsistencias) |
| 4. Nulos | 🔴 | Detectados y contados por archivo; nulos descriptivos conservados a propósito (occupations scopeNote 2.730 / definition 3.031; skills 13.704 / 13.937 / 13.786; skillType 59; reuseLevel ≥ 5) | No hay % por columna ni justificación formal de por qué esos nulos se aceptan | Documentar % y patrón por columna + regla "nulos aceptables = no-llaves" |
| 5. MCAR/MAR/MNAR | 🔴 | **NO ENCONTRÉ EVIDENCIA DE ESTO** (ni en script ni en cuaderno) | Mecanismo de ausencia no analizado (exigido por clase) | Clasificar end_date (ausencia ≈ MNAR/MAR estructural) y start_date |
| 6. Imputación | 🔴 | Solo 2 tratamientos justificados: end_date 136.497 → `'Present'` (vigente); start_date 58.312 → eliminadas. Reconciliación verificada (todas las start-null son también end-null; 78.185 − 2.005 = 76.180 `'Present'` finales) | Sin fillna(0) ni media (correcto), pero no se justifica por escrito por qué no se imputa nada más ni el riesgo de inflado por moda | Documentar la no-imputación y el riesgo de moda en categóricas |
| 7. Valores imposibles | 🔵 | **NO ENCONTRÉ EVIDENCIA DE ESTO** como regla; chequeo externo: **0** `start>end`, **0** formatos fuera de `Qn AAAA`, **0** duración = 0 | El pipeline no verifica imposibles | Añadir checks de formato trimestral y `start<=end` (hoy devolverían 0) |
| 8. Outliers | 🔴 | **NO ENCONTRÉ EVIDENCIA DE ESTO** | Profesor exige IQR; el proyecto no lo aborda en limpieza | Aplazarlo a la etapa de procesado (numéricas derivadas) o justificar su no-aplicación aquí |
| 9. IQR (detalle) | 🔴 | Sección vacía en código y documentación | Faltan Q1, Q3, IQR, límites, conteo, análisis, estrategia, clip | Ver detalle abajo |
| 10. Winsorización/clip | 🔴 | **NO ENCONTRÉ EVIDENCIA DE ESTO** | No se usa | Solo tras el IQR, sobre numéricas del procesado |
| 11. Pipeline | 🟡 | Trazabilidad cuaderno ↔ script exacta; inspección → limpieza → validación → guardado | Orden de la clase no se cumple al pie de la letra en JobHop (nulos antes que dup) | Reordenar o documentar excepción + asserts |
| 12. Validación final | 🟢 | Antes/después por archivo (filas/cols/nulos críticos/dups) + resumen; números verificados | Meta "2.400 filas / 0 nulos" es del dataset de clase; en ESCO quedan nulos descriptivos (diseño); sin asserts | Definir meta propia "0 nulos en llaves" y añadir asserts |
| 13. Documentación | 🟢 | README + Lectura.ipynb con problema/transformación/impacto por archivo; diccionario de columnas | Faltan las secciones de los puntos 4–10 | Completarlas |

## 1. Diagnóstico — 🟢

Inspección por archivo (filas, columnas + significado, tipos, nulos, duplicados, TOP/BOTTOM 3). Reconciliación verificada:

- Original JobHop: 1.594.827 filas; nulos `start_date` 58.312, `end_date` 136.497; duplicados fila-completa 36.249.
- Limpio JobHop: 1.506.445 filas (−88.382 = 58.312 drop + 30.070 dup), **0 nulos, 0 duplicados**. ✓ Cuadra con los comentarios del código.

## 2–3. Duplicados y categorías — 🟡

Dedupe exacto-fila en todos; por clave solo en occupations (−4) y skills (−21), con justificación ("artefacto modifiedDate"). Categorías: solo `strip()`; dominios verificados coherentes; `matched_code == 'unknown'` (104.993) es categoría documentada válida.

## 4–6. Nulos, mecanismo de ausencia e imputación — 🔴

- end_date 136.497 → `'Present'` (interpretación "empleo vigente"); start_date 58.312 → filas eliminadas (no ubicable). **No hay** `fillna(0)`, ni media automática, ni moda automática (correcto).
- Quedan nulos descriptivos intencionales (scopeNote / definition / hiddenLabels / skillType) porque la regla solo exige llaves no nulas.
- Falta: % por columna, clasificación MCAR/MAR/MNAR y justificación del tratamiento. `end_date` nulo = "empleo sin fin reportado" → ausencia ligada al valor mismo (MNAR probable) o a características del empleo (MAR); debe formalizarse por escrito.

## 7. Valores imposibles — ⚠️

No hay regla implementada; comprobación externa dio **0** anomalías (formatos, `start>end`, duración 0). Deuda documental, no defecto de datos.

## 8–10. Outliers / IQR (detalle) / winsorización — 🔴

| Paso | Valor en el proyecto |
|---|---|
| Variable analizada | — (no hay numérica de análisis en limpio) |
| Q1 / Q3 / IQR | **NO ENCONTRÉ EVIDENCIA DE ESTO** |
| Límites Q1 − 1,5·IQR y Q3 + 1,5·IQR | **NO ENCONTRÉ EVIDENCIA DE ESTO** |
| Conteo de outliers | **NO ENCONTRÉ EVIDENCIA DE ESTO** |
| Análisis de causa | **NO ENCONTRÉ EVIDENCIA DE ESTO** |
| Estrategia / justificación | **NO ENCONTRÉ EVIDENCIA DE ESTO** |
| Winsorización / clip | **NO ENCONTRÉ EVIDENCIA DE ESTO** |

Contexto: la limpieza trabaja casi solo con llaves/texto; el único numérico (`greenShare`, proporción 0–0,72, 0 NaN) **no admite outliers** (acotado). El IQR procede en la etapa de procesado sobre numéricas derivadas (duración en trimestres, conteos por ocupación); ahí debe aplicarse con Q1/Q3/IQR/límites/conteo/análisis y clip justificado. No deben "inventarse" outliers donde el dato es textual; declararlo en el README.

## 11–13. Pipeline, validación y documentación — 🟢 con deudas

Trazabilidad exacta cuaderno ↔ script; validación antes/después por archivo; documentación por archivo sólida. Deudas: orden de clase no literal (dedupe tras imputación en JobHop), sin asserts, faltan secciones de MCAR/MAR/MNAR, IQR/outliers y dominios canónicos.

## Cierre

- **A — Bien:** no se tocan originales; códigos como texto; fase de validación antes/después; justificación por transformación; reconciliación numérica verificada.
- **B — Mal (vs. guía):** no existe tratamiento IQR/outliers ni clasificación MCAR/MAR/MNAR; el orden dedupe → nulos está invertido en JobHop.
- **C — Falta:** % de nulos por columna, justificación de nulos descriptivos, checks de imposibles, dominios canónicos, asserts de validación.
- **D — Corregir primero:** implementar/documentar IQR en la etapa que corresponda y la clasificación de mecanismos; reordenar duplicados antes de imputar.
- **E — No tocar:** no sobrescribir originales; no eliminar outliers automáticamente; no añadir `fillna(0)`.
- **F — Lista para la siguiente etapa:** el cruce ya diseñado (`DISEÑO_INTEGRACION.md` + `CIERRE_DISEÑO.md`) con rescate ISCO 100% validado y validaciones V1–V15; pendientes de decisión **D1–D4**.