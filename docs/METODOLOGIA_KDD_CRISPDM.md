# MineríaProtect: Marco Metodológico Integrado KDD–CRISP-DM para la Minería de Trayectorias Laborales

> **Documento rector metodológico del proyecto MineríaProtect** · Minería de Datos ·
> Especialización en Ingeniería de Sistemas · UNIMINUTO Ibagué · 2026-2 · Unidad 1.
> Elaborado como contextualización formal del proyecto dentro de las metodologías
> **KDD** (Knowledge Discovery in Databases) y **CRISP-DM** (Cross-Industry Standard
> Process for Data Mining), con mapeo del estado actual y plan de acción para las
> fases restantes.

---

## 1. Propósito y alcance

Este documento tiene dos objetivos complementarios:

1. **Contextualizar formalmente** a MineríaProtect —análisis de trayectorias
   laborales sobre el dataset **JobHop v2** enriquecido con la taxonomía **ESCO
   v1.2.1**— dentro de las fases de las metodologías **KDD** y **CRISP-DM**,
   evidenciando qué fases están **completadas**, cuáles tienen **avance parcial**
   y cuáles están **pendientes**.
2. **Estructurar un plan de acción** detallado para las fases faltantes
   (Transformación, Modelado/Minería de Secuencias, Evaluación y
   Despliegue/Conocimiento), orientado al nivel **"Excepcional"** de la rúbrica
   del curso (recuadro A9 y D1 del estándar interno).

> **Restricciones de fidelidad (verdades inmutables del proyecto):**
> - Los datos principales de JobHop provienen de **Flandes, Bélgica**, no de
>   Colombia. El país no es el objetivo del proyecto: el objetivo son las
>   **trayectorias laborales**.
> - Las banderas `es_unknown_ocupacion`, `es_rescatado` y `es_vigente` **ya
>   reemplazaron a la imputación tradicional** como estrategia central de manejo
>   de ausencia. No se imputa ni se elimina información estructural.
> - El formato final es **exclusivamente CSV** para el integrado y su limpio
>   (`data/cruce/empleos.csv` y `data/cruce/empleos_limpio.csv`), según decisión
>   documentada del equipo. Los parquet del cruce fueron eliminados; su historial
>   queda en git.

Este es un **documento rector en texto** (Markdown): no contiene scripts ni
código ejecutable. Las decisiones, cifras y convenciones citadas provienen
únicamente de los cuatro documentos base del proyecto (ver §8, Referencias).

---

## 2. Síntesis del estado del proyecto (línea base verificada)

### 2.1 Objetivo y pregunta de investigación

El proyecto analiza **qué ocurre con la trayectoria laboral de una persona
después de terminar su formación**: si sus primeros empleos están relacionados con
lo que estudió, si cambia de área y qué patrones de transición laboral aparecen.

- **Pregunta de investigación (sencilla):** ¿Qué patrones aparecen en la
  trayectoria laboral de las personas después de terminar su formación,
  especialmente en relación con si sus empleos corresponden o no con lo que
  estudiaron?
- **Pregunta de investigación (técnica):** ¿Qué patrones de transición
  ocupacional pueden identificarse en trayectorias laborales posteriores a la
  formación académica?

No se asume de antemano que trabajar en el área estudiada produzca una mejor
trayectoria. Esa sería una hipótesis; el objetivo es **descubrir y evaluar los
patrones presentes en los datos**.

### 2.2 Fuentes de datos y sus roles

| Fuente | Archivo en uso | Rol | Estado |
|---|---|---|---|
| **JobHop v2** (`aida-ugent/JobHop`) | `data/original/JobHop_v2_train.parquet` | Fuente principal: trayectorias (quién, cuándo, ocupación por código, nivel educativo) | ✅ Seleccionada |
| **ESCO v1.2.1** — occupations | `occupations_en.csv` | Traduce `matched_code → nombre de ocupación + grupo ISCO-08` | ✅ Seleccionada |
| **ESCO v1.2.1** — ISCOGroups | `ISCOGroups_en.csv` | Etiqueta y jerarquía del área ocupacional (`code` 4 dígitos → `label` + nivel) | ✅ Seleccionada |

> **Naturaleza del cruce (verificado):** `matched_code` cruza **directamente** con
> `occupations.code`: 2.966 de 2.983 códigos únicos (99,4 %), cubriendo ≈92 % de
> las filas. Los 17 restantes incluyen `unknown` y códigos mapeables al menos a
> nivel de grupo ISCO-08 (primeros 4 dígitos, rescatados por prefijo).

### 2.3 Cifras ancla del proyecto

| Métrica | Valor verificado | Fuente |
|---|---|---|
| Integrado crudo (`empleos.csv`) | **1.506.445 × 11**, 284.247 personas | Auditoría §6 |
| Integrado limpio (`empleos_limpio.csv`) | **1.506.434 × 14** (11 + 3 banderas) | Auditoría §13 |
| Cruce N:1 (nunca multiplica filas) | 1.506.445 filas; PK única (0 duplicados) | Auditoría §5 |
| Duplicados exactos / por PK | **0** / **0** | Auditoría §6 |
| Duración trimestral **inclusiva** (`end − start + 1`) | mediana **5**, Q1 2, Q3 11, máx 160 | Auditoría §8 |
| IQR (Tukey) de duración | IQR 9, límite superior 24,5; 141.591 filas fuera (todas por arriba) — **conservadas** | Auditoría §8 |
| Banderas | `es_unknown_ocupacion` 104.993 · `es_rescatado` 10.176 · `es_vigente` 76.180 | Auditoría §13 |
| `university_level` sin `'None'` | Re-categorizado a `'No reportado'` (**174.035**) | Auditoría §13 |

---

## 3. Marco metodológico integrado: KDD ↔ CRISP-DM

### 3.1 Tabla comparativa de fases aplicadas a MineríaProtect

| Fase CRISP-DM | Fase KDD | Estado en MineríaProtect | Entregable clave del proyecto |
|---|---|---|---|
| **1. Comprensión del negocio** | **1. Selección** | 🟢 **Hecho** | Objetivo, pregunta de investigación y fuentes seleccionadas (JobHop v2 + ESCO v1.2.1) |
| **2. Comprensión de los datos** | **2. Preprocesamiento** (diagnóstico) | 🟢 **Hecho** | Diagnóstico de calidad, validación de integración V1–V7, clasificación MCAR/MAR/MNAR, IQR/Tukey y censura |
| **3. Preparación de los datos** | **2. Preprocesamiento** (tratamiento) + **3. Transformación** | 🟡 **Parcial** | Pipeline de limpieza en 7 fases con asserts → `empleos_limpio.csv` (14 columnas). **Pendiente:** construcción formal de secuencias por persona |
| **4. Modelado** | **4. Minería** | 🔴 **Pendiente** | Selección y aplicación de la técnica de minería de secuencias/transiciones |
| **5. Evaluación** | **5. Interpretación y evaluación** | 🔴 **Pendiente** | Validación de patrones contra criterios de frecuencia, consistencia, interpretabilidad y utilidad |
| **6. Despliegue** | **6. Conocimiento** | 🔴 **Pendiente** | Caracterización de los patrones de transición ocupacional e informe final |

> **Nota de lectura:** las metodologías no son unívocas en la práctica. CRISP-DM
> es un proceso cíclico con retroalimentación entre fases; KDD es un proceso
> escalonado. En MineríaProtect la preparación de datos (CRISP-DM) absorbe tanto
> el **preprocesamiento** (limpieza, hecho) como la **transformación** (conversión
> de experiencias en secuencias, en planificación). Por eso la fase 3 aparece como
> **Parcial** y no como finalizada en su totalidad.

### 3.2 Convenciones de lectura

- 🟢 **Hecho** = fase completada, verificada y documentada con cifras.
- 🟡 **Parcial** = la fase tiene entregables cumplidos, pero conserva trabajo
  formal pendiente.
- 🔴 **Pendiente** = fase planificada, sin ejecutar.
- Cada fase reporta **Estado actual** e **Hitos entregables** (criterio de
  documentación del curso: *qué hace y por qué existe*).

---

## 4. Fases completadas (estado actual: Hecho)

### 4.1 Comprensión del negocio (CRISP-DM) ↔ Selección (KDD)

**Estado actual: 🟢 HECHO**

La selección de datos KDD y la comprensión del negocio CRISP-DM quedaron
consolidadas en el README:

- **Objetivo de minería:** identificar patrones de transición ocupacional en
  trayectorias posteriores a la formación académica.
- **Criterios de éxito:** patrones **frecuentes, consistentes, interpretables y
  útiles** para responder la pregunta de investigación (no una métrica de
  clasificación; el proyecto no tiene columna objetivo).
- **Selección de fuentes:** JobHop v2 como fuente de trayectorias y ESCO v1.2.1
  como fuente de enriquecimiento (significado de la ocupación). La adición de
  ESCO no es "tener dos bases de datos"; es dar **significado** a cada
  `matched_code` para hacer posible el análisis de transiciones.
- **Descarte justificado del enriquecimiento:** los archivos de la taxonomía ESCO
  distintos de `occupations` e `ISCOGroups` (skills, greenShare, colecciones,
  taxonomía ISCED-F, NACE) fueron descartados del repo; sin borde utilizable, red
  para fase posterior o exigencia de información externa.

**Hitos entregables:**
- README con objetivo, pregunta de investigación (sencilla y técnica), árbol del
  proyecto, reglas de oro (originales intocables, salida única CSV, idempotencia).
- Decisiones de negocio documentadas (§14 README y §12 auditoría).
- Tabla de fuentes con roles y estado (ver §2.2).

---

### 4.2 Comprensión de los datos (CRISP-DM)

**Estado actual: 🟢 HECHO**

La comprensión de datos se realizó sobre el **integrado** (después del cruce con
ESCO), con validación exhaustiva contra la fuente:

- **Validación de integración V1–V7:** `T1 1.506.445` · `ok 1.391.276` ·
  `rescatado 10.176` · `unknown 104.993` · `descartado 0` · `isco_group` nulo solo
  en `unknown` · duplicados PK 0. Comparación contra referencia:
  *"mismos registros exactos: True"*.
- **Diagnóstico de calidad** (cifras verificadas): nulos técnicos de ocupación
  **115.169** (7,64 %), literal `'None'` en educación **174.036** (11,55 %),
  literal `'Present'` en `end_date` **76.180** (5,06 %), **11** filas con fechas
  futuras (>2026), duración inclusiva máxima **160 trimestres** (carrera real de
  ~40 años).
- **Clasificación de ausencia** (teoría aplicada al proyecto):
  - **MCAR:** las 11 fechas futuras (error de captura aislado y sin relación con
    otras variables).
  - **MAR (semántico):** NaN de ocupación explicado 100 % por `emparejado`
    — la ausencia depende del texto del cargo, no del valor faltante.
  - **MNAR:** `university_level='None'` (quien no reporta estudios); la ausencia
    depende del valor mismo.
  - **Censura (no es MCAR):** `'Present'` en `end_date` es **censura por la
    derecha** — el empleo seguía vigente al capturar el CV, un dato deliberadamente
    incompleto, no una pérdida aleatoria.
- **Outliers:** no existe "edad 220 / 600 GB"; el integrado no tiene columna
  numérica analítica (`isco_level` es constante). Los únicos puntuales reales son
  las **11 fechas futuras** → eliminar por dominio. La **cola larga** de duración
  (IQR: Q1 2, Q3 11, límite 24,5 → 141.591 filas / 97.954 personas por arriba) se
  conserva: **estabilidad = señal**.

**Hitos entregables:**
- Auditoría con diagnóstico de calidad, traslapes (429.958 filas / 154.131
  personas) y categorías canónicas (3/5/426/2.966, 0 colisiones).
- Bloque técnico para exponer con un caso real verificado (persona 198574,
  Master, 16 empleos, 5 áreas ISCO, 8 cambios de área).
- Comparativa TelecomUNO vs `empleos` (mismo pipeline, decisiones opuestas).

---

### 4.3 Preparación de los datos (CRISP-DM) ↔ Preprocesamiento (KDD)

**Estado actual: 🟢 HECHO (preprocesamiento) — 🟡 Parcial (transformación pendiente)**

La limpieza se ejecutó en dos niveles y ambos quedaron verificados:

**Nivel 1 — Limpieza de fuentes (`limpiar_datos.py`):** columnas 100 % nulas
eliminadas, textos normalizados (`strip`), duplicados por llave resueltos
(`occupations_en`: −4 filas por `code`), códigos leídos como texto para conservar
ceros a la izquierda (`0110` ≠ `110`), validación antes/después por archivo e
**idempotencia byte a byte** verificada. `JobHop_v2_train.parquet` queda excluido
del proceso automático (derivado previo).

**Nivel 2 — Limpieza del integrado (`limpiar_empleos.py`):** pipeline formal en 7
fases — **diagnóstico → duplicados → categorías/banderas → faltantes → outliers →
validación → exportar** — con `assert` por fase (nivel "Excepcional": funciones
reutilizables + pruebas automáticas) y bitácora `_anotar` por fila
(`columna, problema, cantidad, metodo, razon, impacto`).

Resultado verificable de `empleos_limpio.csv` (14 columnas):
- **−11 filas** (1.506.445 → 1.506.434): única eliminación del pipeline, por
  fechas futuras (MCAR de dominio, < 1 %).
- **Banderas en lugar de imputación** (estrategia central):
  - `es_unknown_ocupacion` **104.993** (MAR estructural) y `es_rescatado`
    **10.176** → conservar; eliminar habría borrado 64.508 personas (2.490 con
    todo su historial sin clasificar).
  - `es_vigente` **76.180** (censura): no se inventa fecha de fin.
  - Re-categorización de `'None'` → **`'No reportado'`** (MNAR, 174.035 en el
    limpio); imputar la moda habría fabricado educación.
- **Duplicados:** 0 exactos, 0 por llave natural; las 74.357 / 9.601 claves cortas
  se **conservan** (pluriempleo legítimo) con `keep='first'`.
- **Outliers:** cola larga conservada (sin `clip`); la duración se calcula con
  convención **inclusiva** (`end − start + 1`), consistente con la auditoría.
- **Validación final:** 6/6 umbrales en 0 — duplicados, duplicados PK, nulos sin
  bandera, nulos de ocupación sin bandera, fechas futuras y `start > end`.
- **Formato de salida:** exclusivamente **CSV** (decisión del equipo; los parquet
  del cruce eliminados, historial en git).

**Hitos entregables:**
- `src/limpieza/limpiar_empleos.py` (clase `LimpiadorEmpleos`, 7 fases,
  asserts por fase, docstrings en español bajo A9).
- `notebooks/Diagnostico_Limpieza_Empleos.ipynb` reproduciendo el pipeline con
  evidencia impresa (15/67 celdas, 0 errores).
- `data/cruce/empleos_limpio.csv` regenerable y verificado (0 celdas diferentes
  contra el parquet previo tras migración CSV).
- `requirements.txt` (pandas≥2, pyarrow≥14).

---

### 4.4 Avance paralelo: exploración analítica (pre-transformación)

**Estado actual: 🟡 PARCIAL (contexto, no reemplaza la transformación formal)**

`notebooks/presentacion.ipynb` con `src/filtro/` ya esboza la **visión analítica
prevista** para la fase de minería, calculada en vivo sobre el limpio:

- **Transiciones consecutivas** entre grupos ISCO por persona (con dedupe de
  repeticiones exactas) → **18,3 %** de transiciones conservan el grupo ISCO.
- **Brechas sin empleo** (proxy de desempleo, previa fusión de periodos solapados):
  **60,1 %** de personas con al menos una brecha; mediana **3** trimestres, máx
  **151**.
- **Traslapes** (mismo método del diagnóstico): **82 %** de personas con ≥1
  traslape (pluriempleo o dato impreciso).
- **Relaciones** nivel educativo ↔ grupo ISCO, ISCO ↔ duración, y 4 preguntas de
  mini investigación (concentración por nivel, duración por nivel, linealidad de
  trayectoria, desempleo proxy), cerrando con formato
  **DATO / INTERPRETACIÓN / LIMITACIÓN**.

> **Advertencia de trazabilidad:** estos indicadores son **exploración**, no
> transformación formal. La construcción del dataset de secuencias por persona
> (`Sₚ`) y su codificación son trabajo pendiente de la fase 5.1; la exploración
> sirve como línea base para elegir la técnica de minería.

---

## 5. Fases pendientes — plan de acción

### 5.1 Transformación (KDD) ↔ Preparación de los datos (CRISP-DM, hacia modelado)

**Estado actual: 🔴 PENDIENTE** (con insumos parciales: filtros e indicadores de
`src/filtro/`)

**Descripción objetivo.** Convertir las experiencias en **secuencias temporales
por persona** para sobre ellas aplicar minería de secuencias/transiciones. La
representación canónica ya documentada es:

> `Sₚ = [(t₁, ocupación, área), (t₂, ocupación, área), …]`

Donde cada elemento se ordena por el **ordinal continuo del trimestre**
(`Q<n> <aaaa>` → `4·año + n`), atributo clave ya implementado en
`src/filtro/indicadores.py`.

**Plan de acción (numerado):**
1. Construir el dataset de secuencias por `resume_id`: orden estable por
   `(inicio, fin)`, definiendo el manejo de **traslapes** (D2) y de las
   experiencias **vigentes** (`es_vigente`, censura a la derecha) dentro de la
   secuencia.
2. Decidir la **unidad de análisis** de cada paso: ocupación ESCO (`occupation_code`),
   grupo ISCO (`isco_group`) o nivel de agregación jerárquico; documentar la
   elección como decisión de negocio.
3. Definir la **ventana temporal** de análisis (rango de años de inicio) como
   regla de negocio explícita (decisión anticipada nº 5 de la auditoría).
4. Aplicar **codificación** de los elementos alfabéticos (labels/grupos) y
   decidir si entra `dur_Q` al modelo; si entra, **winsorizar `clip(−11,5; 24,5)`**
   solo entonces (IQR sobre el original, nunca sobre imputados). En caso de
   requerirse variables numéricas adicionales: escaladores, codificación y PCA
   (agenda de la sesión 4).
5. Definir el **destino de datos procesados** (deuda formal **D4**: `data/procesada/`)
   manteniendo el formato CSV como estándar y el original intocable.
6. Cerrar con **validación de invariantes** (asserts): número de personas,
   primer/último elemento de secuencia, orden temporal estricto y ausencia de
   pérdida de registros frente a `empleos_limpio.csv`.

**Hitos entregables:**
- Dataset de secuencias por persona (CSV) con bitácora de construcción
  (antes/después) y asserts de línea base.
- Decisión documentada de la unidad de análisis y la ventana temporal.
- Módulo de transformación reutilizable alineado a las reglas B3 (valores de
  negocio en un único punto de configuración) y D5 (rutas relativas).

---

### 5.2 Minería de secuencias (KDD) ↔ Modelado (CRISP-DM)

**Estado actual: 🔴 PENDIENTE**

La técnica definitiva **se seleccionará después de explorar la estructura final
de los datos** (fase de transformación). Se parte de un catálogo de técnicas
**candidatas sin compromiso**, fiel al README:

| Técnica candidata | Tipo de respuesta | Consideración inicial |
|---|---|---|
| **Análisis de transiciones** (matriz/tabla de transición de primer orden) | Patrones directos "qué sigue a qué" | La menos costosa; ya hay indicadores exploratorios (transiciones consecutivas, primera→segunda) |
| **Minería de patrones secuenciales** (p. ej. familias tipo PrefixSpan / GSP) | Subsecuencias frecuentes recurrentes | Requiere umbral de soporte; sensible a la unidad de análisis elegida |
| **Clustering de trayectorias** (agrupación por similitud de secuencia) | Segmentos de trayectorias | Requiere distancia entre secuencias y definición de reposo/representante |
| **Detección de trayectorias atípicas** | Trayectorias poco comunes o anómalas | Complementa; orientada a la pregunta "¿existen caminos muy poco comunes?" |

**Plan de acción (numerado):**
1. Resolver las **deudas formales heredadas de la fase de diseño** antes de
   modelar:
   - **D1** — tratamiento de `unknown` en minería: las filas flagadas
     (`es_unknown_ocupacion`) definen el alcance de la secuencia (¿se excluyen, se
     marcan como paso nulo, o se analizan como segmento propio?).
   - **D2** — empleos simultáneos (**traslapes**, 429.958 filas) y claves cortas
     conservadas (74.357/9.601) en las transiciones: cómo se concreta la regla de
     negocio "transición" en secuencias con pluriempleo.
   - **D3** — enriquecimiento temático futuro (skills, greenShare) si la pregunta
     de investigación lo exige más adelante.
2. Seleccionar la técnica con un **criterio de decisión documentado** basado en la
   estructura final de los datos (longitud media de secuencias, cardinalidad de la
   unidad de análisis, presencia de censura).
3. Parametrizar la técnica (soporte mínimo, número de clústeres, distancia) como
   **constantes de negocio documentadas** en un único punto de configuración.
4. Implementar el modelado como **módulo reutilizable con asserts de invariantes**,
   respetando la jerarquía A9/bitácora y la regla D5 (sin aleatoriedad no se
   introducen semillas).
5. Comparar al menos dos técnicas candidatas sobre el mismo dataset de secuencias
   y registrar la comparación (patrón de validación cruzada de técnicas, no solo
   de parámetros).

**Hitos entregables:**
- Documento de **decisión técnica** (qué técnica, por qué, qué descartan y con qué
  evidencia).
- Modelo(s) de minería de secuencias ejecutado(s) con bitácora y asserts.
- Tabla comparativa de técnicas candidatas (resultados, costo, interpretabilidad).

---

### 5.3 Interpretación y evaluación (KDD) ↔ Evaluación (CRISP-DM)

**Estado actual: 🔴 PENDIENTE**

**Descripción objetivo.** Juzgar si los patrones encontrados son útiles para
responder la pregunta de investigación. Los criterios ya declarados en el proyecto
son: los patrones deben ser **frecuentes, consistentes, interpretables y útiles**.

**Plan de acción (numerado):**
1. Evaluar **frecuencia y robustez** de cada patrón (soporte, cobertura de
   personas) contra líneas base de `presentacion.ipynb` (18,3 % de transiciones
   conservan grupo; mediana de duración 5 trimestres, etc.).
2. Evaluar **consistencia** entre segmentos (por nivel educativo, por grupo ISCO
   de entrada) y estabilidad ante variaciones de parámetros.
3. Evaluar **interpretabilidad** en lenguaje de negocio: traducir cada patrón a un
   hallazgo "qué pasa, para quién, en qué plazo", usando la taxonomía ESCO como
   diccionario.
4. Contrastar contra la pregunta de investigación: ¿aparecen caminos muy
   frecuentes o poco comunes? ¿cuántos cambios de ocupación son habituales? ¿los
   primeros empleos se relacionan con lo estudiado?
5. Documentar **limitaciones** con formato DATO / INTERPRETACIÓN / LIMITACIÓN,
   declarando explícitamente: sin causalidad, datos de Flandes (no Colombia), y
   censura/`unknown` sin imputar.

**Hitos entregables:**
- Informe de evaluación con criterios explícitos y evidencia numérica.
- Anexo de limitaciones y decisiones revisitadas (¿cambia algo de la limpieza si
  la minería lo exige? — en tal caso, volver a fase de preparación del ciclo
  CRISP-DM).

---

### 5.4 Conocimiento y despliegue (KDD) ↔ Despliegue (CRISP-DM)

**Estado actual: 🔴 PENDIENTE**

**Descripción objetivo.** Consolidar el **conocimiento descubierto**: la
caracterización de los principales patrones de transición ocupacional y los
entregables finales del curso, con reproducibilidad total.

**Plan de acción (numerado):**
1. Caracterizar los **patrones de transición ocupacional** más frecuentes con
   nombre, soporte y descripción (resultado de la interpretación).
2. Documentar el **ciclo completo** en un informe entregable: selección →
   preprocesamiento → transformación → minería → evaluación → conocimiento, con
   las cifras verificadas de cada etapa.
3. Empaquetar la reproducibilidad (regla **D5**): rutas relativas, requisitos
   declarados, comandos de ejecución en README, originales intocables y
   regeneración de derivados por script.
4. Validar la **coherencia del repositorio** contra `BUENAS_PRACTICAS_CODIGO.md`
   (revisión final tipo auditoría de la rama, como la de §14 de la auditoría) y
   unificar el estado de ramas en git.
5. Describir cómo el conocimiento producido **contextualiza futuras preguntas**
   (p. ej. relación formación–empleo), recordando que los hallazgos no implican
   causalidad.

**Hitos entregables:**
- Caracterización final de patrones de transición ocupacional (sección
  "Conocimiento" de KDD).
- Informe metodológico integrado (este marco incorporado) + presentación del
  proyecto.
- Repositorio verificado y reproducible en un entorno limpio.

---

## 6. Conclusiones y siguientes pasos

**Conclusión de estado.** MineríaProtect ha completado de forma verificada las
fases de **selección**, **preprocesamiento** y **comprensión de los datos** de
ambas metodologías: fuentes elegidas y justificadas, integración validada (V1–V7),
integrado limpio (`empleos_limpio.csv`, 1.506.434 × 14) con banderas en lugar de
imputación, y una base analítica exploratoria de transiciones, brechas y
traslapes. Las fases que restan son las de **mayor valor analítico**: transformar
las experiencias en secuencias, aplicar la minería de secuencias, evaluar los
patrones y consolidar el conocimiento.

**Ruta priorizada de impacto (siguientes pasos):**

1. **Transformación formal** de experiencias a secuencias por persona (`Sₚ`),
   resolviendo primero las deudas **D1** (`unknown`), **D2** (traslapes/empleos
   simultáneos) y **D4** (destino `data/procesada/`, formato CSV).
2. **Selección de la técnica de minería** con criterio documentado y comparación
   de candidatas sobre la estructura final de los datos.
3. **Minería de secuencias/transiciones** e **interpretación** de patrones contra
   la pregunta de investigación (frecuencia, consistencia, interpretabilidad,
   utilidad).
4. **Evaluación y conocimiento final**: caracterización de patrones de transición
   ocupacional e informe reproducible (regla D5).

> **Recordatorio metodológico del curso:** la técnica definitiva se seleccionará
> después de explorar la estructura final de los datos. Hasta entonces, el
> catálogo de candidatas (§5.2) se mantiene abierto y sin compromiso.

---

## 7. Cumplimiento del estándar de documentación (sección A9)

Este documento rector se redactó alineado implícitamente con la sección **A9
(Documentación)** de `docs/BUENAS_PRACTICAS_CODIGO.md`:

| Regla A9 | Cómo se cumple aquí |
|---|---|
| Explicar **qué** hace cada fase y **por qué** existe | Todas las fases (§4 y §5) incluyen un descriptor de propósito y decisiones justificadas. |
| Registrar **antes/después** y criterio aplicado | Las cifras ancla (§2.3) y los resultados de limpieza (§4.3) citan cantidades verificadas de la fuente (1.506.445 → 1.506.434). |
| Trazabilidad de decisiones (bitácora) | Se referencia la bitácora `_anotar` del pipeline y las tablas de decisión de la auditoría como fuente de verdad. |
| Excepciones explícitas y no obvias | Se marcan las excepciones de proyecto: prints como entregable, banderas en vez de imputación, duración inclusiva, CSV como formato único. |
| Sin inventar requisitos ni resultados (regla E1) | Todo número y decisión proviene de los cuatro documentos base; no se generan resultados que no existan en ellos. |

> **Fidelidad absoluta:** ninguna fase, dato o decisión de este documento
> contradice los documentos base. Los datos son de **Flandes (Bélgica)**, las
> banderas `es_unknown_ocupacion`, `es_rescatado` y `es_vigente` **ya reemplazaron
> a la imputación tradicional**, y el formato final es **exclusivamente CSV**.

---

## 8. Referencias

1. `README.md` — objetivo central, pregunta de investigación, justificación de
   fuentes y árbol del proyecto.
2. `docs/AUDITORIA_RAMA_PRUEBA.md` — estado as-built, validación de integración
   (V1–V7), cifras del diagnóstico y del pipeline de limpieza (`empleos_limpio`),
   decisiones pendientes D1–D4 y migración a CSV.
3. `docs/BUENAS_PRACTICAS_CODIGO.md` — estándar de calidad, estructura, nomenclatura
   y reproducibilidad (con sección A9 de documentación).
4. `docs/contexto_sesion3_mineriaprotect.md` — teoría aplicada (MCAR/MAR/MNAR, IQR,
   censura) y decisiones de limpieza justificadas.

Fuentes externas del proyecto: JobHop v2 (`aida-ugent/JobHop`, Hugging Face) ·
artículo *JobHop v2: A Large-Scale Career Trajectory Dataset from Unstructured
Resumes* (arXiv) · taxonomía **ESCO v1.2.1** (descarga oficial de la Comisión
Europea).