# MineríaProyect

Análisis de minería de trayectorias laborales sobre el dataset **JobHop v2** (`aida-ugent/JobHop`, Hugging Face), que contiene trayectorias profesionales reconstruidas a partir de hojas de vida (resúmenes curriculares) no estructuradas.

> **Nota sobre el origen:** los datos principales de JobHop provienen de **Flandes, Bélgica** (conjunto internacional), no de Colombia. El país no es el objetivo del proyecto: el objetivo son las **trayectorias laborales**.

## Objetivo

Analizar qué ocurre con la trayectoria laboral de una persona después de terminar su formación: si sus primeros empleos están relacionados con lo que estudió, si cambia de área y qué patrones de transición laboral aparecen.

**Pregunta de investigación (versión sencilla):**

> ¿Qué patrones aparecen en la trayectoria laboral de las personas después de terminar su formación, especialmente en relación con si sus empleos corresponden o no con lo que estudiaron?

**Pregunta de investigación (versión técnica):**

> ¿Qué patrones de transición ocupacional pueden identificarse en trayectorias laborales posteriores a la formación académica?

Preguntas que guían el análisis:

- ¿Qué ocupaciones suelen venir después de otras?
- ¿Qué trabajos son los primeros empleos más comunes?
- ¿Qué trayectorias se repiten con mayor frecuencia?
- ¿Cuántos cambios de ocupación son habituales?
- ¿Existen caminos profesionales muy frecuentes o poco comunes?

> No se asume de antemano que trabajar en el área estudiada produce una mejor trayectoria. Esa sería una hipótesis; el objetivo es descubrir y evaluar los patrones presentes en los datos.

## Fuentes de datos

```
JobHop v2 (fuente principal — trayectorias)
   ↓
códigos ocupacionales (matched_code)
   ↓
ESCO (fuente de enriquecimiento — significado de la ocupación)
   ↓
minería de trayectorias
```

### 1. JobHop v2 — fuente principal (trayectorias)

Dataset original de trayectorias laborales. Columnas:

| Columna | Descripción |
|---|---|
| `resume_id` | Identificador de la persona/currículum |
| `matched_code` | Código de ocupación (taxonomía ESCO) |
| `start_date` | Trimestre de inicio (ej. `Q1 2000`) |
| `end_date` | Trimestre de fin (ej. `Q4 2007` o `Present`) |
| `university_level` | Nivel de formación (ej. `Master`, `Bachelor`) |

Una misma `resume_id` puede tener varias filas: cada una es una experiencia laboral distinta de la misma persona. Encadenadas en orden forman la trayectoria profesional.

### 2. ESCO — fuente de enriquecimiento (significado de la ocupación)

- Fuente oficial (descarga): [https://esco.ec.europa.eu/es/use-esco/download](https://esco.ec.europa.eu/es/use-esco/download)
- **Versión incorporada:** ESCO v1.2.1 (clasificación en inglés), archivos CSV en `data/01_raw/ESCO/`.
- **Por qué se agrega:** JobHop trae códigos de ocupación (`matched_code`), pero se necesita información interpretable sobre esas ocupaciones. ESCO relaciona los códigos con nombre, descripción, clasificación ocupacional, grupos ocupacionales, relación con ISCO y competencias.

> **Estado del cruce (verificado):** `matched_code` cruza **directamente** con `occupations.code`: 2.966 de 2.983 códigos únicos (99,4%), que cubren ≈92% de las filas. Los 17 restantes incluyen `unknown` y códigos mapeables al menos a nivel de grupo ISCO-08 (primeros 4 dígitos).

## Estructura del proyecto

```
MineriaProtect/
├── data/
│   ├── 01_raw/                    # Fuentes (NUNCA se modifican; no versionadas)
│   │   ├── JobHop_v2_train.parquet
│   │   └── ESCO/                  # 5 CSV: occupations, ISCOGroups, occupationSkillRelations, skills, greenShareOcc
│   ├── 02_interim/                # Versiones limpias de fuentes (derivados regenerables)
│   │   ├── JobHop_v2_train_limpio.parquet   # parquet (no versionado); se regenera
│   │   └── ESCO/                  # *_limpio.csv (CSV: sí versionados)
│   └── 03_processed/              # integrado + limpios (los CSV de los cruces; NO versionados por tamaño)
│       ├── empleos.csv                     # integrado original JobHop+ESCO (inmutable)
│       ├── empleos_limpio.csv              # limpio formal: incluye cola larga (con outliers)
│       └── empleos_limpio_sin_outliers.csv # limpio sin la cola larga (dur_Q < 25)
├── notebooks/                     # cuadernos (sesión 1-4)
│   ├── Lectura.ipynb              # limpieza de fuentes (reproduce limpiar_datos.py)
│   ├── Diagnostico_Limpieza_Empleos.ipynb  # limpieza del integrado (bloque 4)
│   └── presentacion.ipynb         # análisis y mini investigación (sesión 3)
├── logs/                          # bitácora de ejecución del pipeline (no versionada)
├── src/
│   ├── filtro/                    # análisis reutilizable (presentacion.ipynb)
│   │   ├── filtros.py             # selección por nivel/grupo ISCO/periodo/vigencia
│   │   └── indicadores.py         # duración, transiciones, brechas, crosstabs
│   ├── limpieza/
│   │   ├── limpiar_datos.py       # limpieza de fuentes (ESCO + JobHop desde 01_raw)
│   │   ├── limpiar_empleos.py     # limpieza formal del integrado (bloque 4)
│   │   └── dividir_por_outliers.py# división por cola larga: con/sin outliers
├── .python-version              # entorno validado: Python 3.14.7
├── requirements.txt             # dependencias (pandas, pyarrow, matplotlib)
├── contexto_sesion1.md / contexto_sesion2.md / contexto_sesion3.md  # contexto de cada sesión del curso
└── .gitignore
```

Reglas de oro del proyecto:

- **Los archivos originales nunca se modifican**: solo se leen.
- **No se vuelve a limpiar una versión limpia/derivada.** El pipeline siempre parte de `data/01_raw/`.
- El proceso de limpieza es **idempotente**: re-ejecutarlo sobrescribe las salidas con contenido equivalente (no genera duplicados).
- **Salida única en CSV.** El integrado y sus limpios solo se mantienen en CSV en `data/03_processed/`.
- Cada decisión de negocio del pipeline vive en un único punto de configuración o está documentada en la bitácora (`logs/`).

## Datasets

### JobHop v2 (`aida-ugent/JobHop`)

| Archivo | Descripción |
|---|---|
| `data/01_raw/JobHop_v2_train.parquet` | Dataset original (1.594.827 filas) — **no versionado** |
| `data/02_interim/JobHop_v2_train_limpio.parquet` | Dataset limpio (1.506.445 filas) — **no versionado**; regenerable con `limpiar_datos.py` |

Limpieza aplicada por `limpiar_datos.py` (módulo JobHop): `end_date` nulo → `Present`; filas sin `start_date` eliminadas (58.312); duplicados exactos eliminados (30.070); orden por persona y trimestre real (`Q1 2000` → clave `(2000, 1)`). Resultado: 1.594.827 → 1.506.445 filas.

### Taxonomía ESCO v1.2.1 (5 archivos gestionados)

| Archivo | Originales | Limpias | Operación clave |
|---|---|---|---|
| `occupations_en.csv` | 3.043 | 3.039 | −4 filas por `code` duplicado |
| `ISCOGroups_en.csv` | 619 | 619 | columna `altLabels` 100% nula eliminada (8 → 7 columnas) |
| `occupationSkillRelations_en.csv` | 126.051 | 126.051 | puente ocupación→habilidad; 59 filas con `skillType` nulo conservadas |
| `skills_en.csv` | 13.960 | 13.939 | −21 filas por `conceptUri` duplicado |
| `greenShareOcc_en.csv` | 3.590 | 3.590 | columna `greenShare` convertida a número (float) |

Solo `occupations` e `ISCOGroups` participan en la integración; los otros 3 son **enriquecimientos opcionales**.

## CSV para los cruces (lineage)

Los cruces del proyecto se hacen **exclusivamente** sobre los CSV de `data/03_processed/`. Son los archivos que se usan para las uniones/cruce de datos y su validación cruzada:

| CSV | Rol en el cruce | Filas × Columnas | Personas | Estado |
|---|---|---|---|---|
| `data/03_processed/empleos.csv` | **Integrado original** JobHop + ESCO (inmutable, fuente del bloque 4) | 1.506.445 × 11 | 284.247 | Inmutable |
| `data/03_processed/empleos_limpio.csv` | **Limpio formal CON cola larga** (incluye outliers de duración, `dur_Q` hasta 160) | 1.506.434 × 14 | 284.247 | Derivado, regenerable |
| `data/03_processed/empleos_limpio_sin_outliers.csv` | **Limpio SIN cola larga** (outliers de `dur_Q ≥ 25` eliminados; `dur_Q` máx. 24) | 1.364.853 × 14 | 277.052 | Derivado, regenerable |

```
empleos.csv ──limpiar_empleos.py──▶ empleos_limpio.csv ──dividir_por_outliers.py
                                                  │  (con outliers)
                                                  ▼
                                        empleos_limpio_sin_outliers.csv
                                                  (sin outliers)
```

**Uso en los cruces de validación:** los dos limpios (con/sin outliers) se cruzan entre sí para comparar descriptivos (duración, transiciones, crosstabs) y medir el impacto de la cola larga antes de elegir la técnica de minería. `empleos.csv` nunca se usa como entrada de análisis directo: solo como origen del pipeline.

### Limpieza formal del integrado (bloque 4)

`empleos_limpio.csv` (1.506.434 × 14) surge de `src/limpieza/limpiar_empleos.py` en 7 fases: **diagnóstico → duplicados → categorías/banderas → faltantes → outliers → limpieza → validación**, cada una con asserts contra cifras canónicas (nivel "Excepcional"). Columnas finales: las 11 originales + `es_unknown_ocupacion`, `es_rescatado`, `es_vigente`.

### División por outliers

`empleos_limpio_sin_outliers.csv` surge de `src/limpieza/dividir_por_outliers.py` usando el mismo criterio de la fase 5 (IQR de Tukey sobre `dur_Q`). Como todas las atípicas caen por la cola larga (limite superior 24,5), "sin outliers" elimina las filas con `dur_Q ≥ 25`:

- `empleos_limpio.csv`: 1.506.434 filas | 284.247 personas | `dur_Q` máx. 160
- `empleos_limpio_sin_outliers.csv`: 1.364.853 filas | 277.052 personas | `dur_Q` máx. 24

## Proceso de limpieza

`src/limpieza/limpiar_datos.py` (fuentes → `data/02_interim/`):

1. Los CSV se leen **como texto** (`dtype=str`) para no perder ceros a la izquierda (p. ej. ISCO `0110` ≠ `110`).
2. Se eliminan las **columnas 100% nulas**.
3. Se normalizan textos: `strip()`.
4. Se eliminan **duplicados exactos** (regla defensiva; en la práctica 0).
5. **Duplicados por llave** (datos de dos publicaciones ESCO fusionadas): `occupations` −4 por `code`; `skills` −21 por `conceptUri`.
6. `ISCOGroups`: columna 100% nula eliminada (8 → 7).
7. `greenShareOcc`: `greenShare` a float.
8. `occupationSkillRelations`: 59 filas con `skillType` nulo conservadas.
9. Validación antes/después por archivo (filas, columnas, nulos críticos, duplicados).

Idempotencia verificada: ejecutar dos veces produce archivos byte a byte idénticos.

## Cómo ejecutar

```bash
python -m pip install -r requirements.txt
python src/limpieza/limpiar_datos.py        # fuentes → data/02_interim/
python src/limpieza/limpiar_empleos.py      # integrado → data/03_processed/empleos_limpio.csv
python src/limpieza/dividir_por_outliers.py # → data/03_processed/empleos_limpio_sin_outliers.csv
```

Los scripts resuelven la raíz del proyecto buscando hacia arriba la carpeta `data/`, así que se ejecutan desde cualquier directorio dentro del repo.

## Notebooks (`notebooks/`)

| Notebook | Contenido |
|---|---|
| `Lectura.ipynb` | Limpieza de fuentes: inspección → limpieza → validación. Reproduce `limpiar_datos.py`. |
| `Diagnostico_Limpieza_Empleos.ipynb` | Diagnóstico y limpieza formal del integrado (bloque 4). Reproduce `limpiar_empleos.py`. |
| `presentacion.ipynb` | Análisis y mini investigación sobre `empleos_limpio.csv`: 5 bloques (Conocer → Exploración → Relaciones → Mini investigación → Hallazgos). Importar: *Kernel → Restart & Run All*. |

## Decisiones documentadas

- **Salida única en CSV** en el bloque 4: integrado y limpios solo en CSV en `data/03_processed/`; ningún Parquet se versiona.
- **Prints como entregable:** la bitácora impresa (diagnóstico, decisiones, validación) es parte de la documentación.
- **Duración trimestral inclusiva:** una experiencia del mismo trimestre de inicio/fin dura 1 trimestre (`end − start + 1`).
- **Claves cortas con `keep='first'`:** 74.357 / 9.601 filas extra por combinaciones repetidas; no se eliminan por ser pluriempleo legítimo.
- **11 filas futuras (>2026):** eliminadas (MCAR, error de dominio).
- **Cola larga de duración:** conservada en `empleos_limpio.csv` (estabilidad = señal) y aislada en `empleos_limpio_sin_outliers.csv` para validación cruzada.

## Metodología: KDD

1. **Selección** — JobHop v2 y ESCO.
2. **Preprocesamiento** — nulos, duplicados, fechas, códigos desconocidos (bloque 4).
3. **Transformación** — encadenar experiencias por `resume_id` en una secuencia temporal; enriquecer con ESCO.
4. **Minería** — técnicas candidatas: minería de secuencias, análisis de transiciones, clustering de trayectorias y detección de atípicas.
5. **Interpretación y evaluación** — ¿son los patrones frecuentes, consistentes, interpretables y útiles para responder la pregunta?
6. **Conocimiento** — caracterización de los principales patrones de transición ocupacional.

## Limitaciones

- **JobHop no representa Colombia** (datos de Flandes, Bélgica).
- **Sin causalidad:** se buscan asociaciones y patrones.
- **ESCO no es un dataset de trayectorias:** solo enriquece/interpreta.
- **La técnica de minería aún no está definida definitivamente.**
- Los códigos ajenos a ESCO v1.2.1 y el valor `unknown` necesitan manejo explícito (resuelto con banderas).

## Estado actual y siguientes pasos

**Estado actual:** fuentes limpias (layout `01_raw` → `02_interim`), integrado y limpieza formal completados, **división con/sin outliers generada** para cruces de validación. Rutas de scripts y cuadernos corregidas al layout nuevo (todas las fallas de ejecución resueltas).

**Siguientes pasos planificados:**

1. Convertir las experiencias en secuencias temporales por persona (`src/filtro/`).
2. Cruzar descriptivos con/sin cola larga y seleccionar la técnica de minería.
3. Evaluar, interpretar y documentar los patrones encontrados.

## Referencias

- Artículo: *JobHop v2: A Large-Scale Career Trajectory Dataset from Unstructured Resumes* — [https://arxiv.org/abs/2607.11715](https://arxiv.org/abs/2607.11715)
- Repositorio del código fuente (STEP): [https://github.com/aida-ugent/Step](https://github.com/aida-ugent/Step)
- Dataset JobHop v2: [https://huggingface.co/datasets/aida-ugent/JobHop](https://huggingface.co/datasets/aida-ugent/JobHop)
- ESCO (descarga): [https://esco.ec.europa.eu/es/use-esco/download](https://esco.ec.europa.eu/es/use-esco/download)

## Requisitos

- Python **3.14.7** (ver `.python-version`)
- `pandas>=2`, `pyarrow>=14`, `matplotlib>=3.8` (ver `requirements.txt`)