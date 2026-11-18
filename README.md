# JobPath

JobPath es el proyecto de preparación de datos para IA y minería de patrones comportamentales que estudia las **trayectorias laborales** reconstruidas por **JobHop v2** y las enriquece con la taxonomía **ESCO v1.2.1** para descubrir patrones de transición ocupacional, permanencia, reincidencia y continuidad de competencias después de la formación académica. El proyecto sigue las metodologías **KDD** y **CRISP-DM**: sobre el **dato crudo** de JobHop (particiones CSV `train + test + val`) se integran las fuentes (ESCO) y se ejecutan la unificación y limpieza en **CSV**, dejando el dataset listo para el modelado y la minería de secuencias por persona (`Sₚ`).

> **Estado del proyecto (TL;DR · Pipeline Unificado v2 en `notebooks/refactor/`):** ✅ Selección, Preprocesamiento (`2.0`), Transformación y Partición por Persona (`3.0`), Diagnóstico PCA (`4.0`/`4.1`) y EDA Formal (`5.0`) **HECHOS y verificados sobre el universo completo**:
> - **Versión A (`con_outliers`):** `data/03_processed/empleos_unificado_limpio.csv` (**1.871.014 filas × 23 columnas**, **355.308 personas**).
> - **Versión B (`sin_outliers`, winsorización IQR):** `data/03_processed/empleos_limpio_con_competencias_sin_outliers.csv` (**1.871.014 filas × 23 columnas**, **355.308 personas**; 193.596 filas recortadas en las 4 columnas de competencias/repetición).
> - **Universo modelable (con oficio ESCO clasificado):** **1.738.738 experiencias (92,93 %)** y **352.093 personas (99,10 %)** (132.276 filas sin oficio clasificado = 7,07 % excluidas del escalado).
> - **Partición por persona (`GroupShuffleSplit`, 80/20, `seed=42`) en `data/04_transformed/`:** `X_train` (**1.391.018 × 2.985**, 281.674 personas), `X_test` (**347.720 × 2.985**, 70.419 personas), `y_train` (`reincide` = **30,01 %** positivos) y `y_test` (**29,97 %** positivos), con `shared_persons = 0`.
> - **EDA y auditoría (`5.0_EDA_jobpath.ipynb`):** 28 figuras regeneradas en `reports/eda_jobpath/figures/` y mapa `reports/eda_jobpath/tables/split_map_resume_id.csv`.
> - ⏳ **Pendiente:** Fase 4 CRISP-DM (Modelado / Minería de secuencias excluyendo de `X` las columnas con fuga directa del target: `veces_ese_oficio_rob` y `veces_ese_oficio_bin`).

## Contenidos

1. [Contexto general del proyecto](#contexto-general-del-proyecto)
2. [Objetivo, finalidad y preguntas de investigación](#objetivo-finalidad-y-preguntas-de-investigación)
3. [Conceptos clave](#conceptos-clave)
4. [Fuentes de datos](#fuentes-de-datos)
5. [Datasets y calidad (antes / después)](#datasets-y-calidad-antes--después)
6. [Estructura del proyecto](#estructura-del-proyecto)
7. [Cómo orientarse en el repositorio](#cómo-orientarse-en-el-repositorio)
8. [Metodología (KDD / CRISP-DM)](#metodología-kdd--crisp-dm)
9. [Lo que se hizo en el código](#lo-que-se-hizo-en-el-código)
10. [Decisiones técnicas clave](#decisiones-técnicas-clave)
11. [Excepciones explícitas del proyecto](#excepciones-explícitas-del-proyecto)
12. [Decisiones de negocio pendientes](#decisiones-de-negocio-pendientes)
13. [Verificación del resultado](#verificación-del-resultado)
14. [Cómo ejecutar (reproducibilidad)](#cómo-ejecutar-reproducibilidad)
15. [Estado actual y siguientes pasos](#estado-actual-y-siguientes-pasos)
16. [Limitaciones](#limitaciones)
17. [Ruta de lectura sugerida](#ruta-de-lectura-sugerida)
18. [Referencias](#referencias)

## Contexto general del proyecto

JobPath es un proyecto académico del curso de **Minería de Datos** (2026-2, Unidad 1) de la Especialización en Ingeniería de Sistemas de **UNIMINUTO (Ibagué)**, formalizado sobre las metodologías **KDD** y **CRISP-DM** (acta de constitución analítica en `notebooks/1.0_comprension_negocio.md`).

**El problema de fondo.** Las hojas de vida contienen historial laboral en lenguaje natural y no estructurado: distintas personas describen cargos de maneras distintas y no existe un significado estandarizado de cada ocupación. **JobHop v2** ya reconstruyó ese historial en un dataset relacional —una fila por experiencia laboral con `resume_id`, fechas y un código de ocupación (`matched_code`)— pero los códigos aún carecen de *significado* interpretable. Para comparar trayectorias y estudiar transiciones se necesita traducir cada código a una ocupación con nombre y área ocupacional: ese es el papel de la taxonomía **ESCO v1.2.1**.

**El problema de interés.** Después de terminar una formación, ¿se queda la persona en el área que estudió? ¿cambia de área y cuántas veces? ¿qué ocupaciones suceden a otras y qué caminos se repiten? Como no se asume causalidad, el proyecto responde en términos **descriptivos y de patrón**, no de causa-efecto.

> Los datos de JobHop provienen de **Flandes, Bélgica**. El país no es el objetivo del proyecto; el objetivo son las **trayectorias laborales** y sus patrones de transición.

## Objetivo, finalidad y preguntas de investigación

**Objetivo:** descubrir y evaluar los patrones de transición ocupacional presentes en las trayectorias laborales posteriores a la formación académica, relacionando cada experiencia con las competencias esenciales que exige la ocupación desempeñada y con la reincidencia de la persona en ese oficio.

**Finalidad de minería (inmediata).** Construir el dataset de **secuencias por persona** (`Sₚ`) y aplicar técnicas de minería de secuencias/transiciones para identificar patrones **frecuentes, consistentes, interpretables y útiles** que respondan las preguntas del proyecto. Cada secuencia puede incorporar la ocupación, el área ISCO, el periodo, el nivel educativo y las competencias esenciales asociadas a cada empleo.

**Finalidad de conocimiento (última).** Caracterizar los principales patrones de transición ocupacional y consolidar un informe reproducible y documentado que sirva de base descriptiva para futuras preguntas sobre la relación formación–empleo e inserción laboral (fase de conocimiento de KDD).

- **Pregunta sencilla:** ¿qué patrones aparecen en la trayectoria laboral de las personas después de su formación, especialmente respecto de si sus empleos corresponden o no con lo que estudiaron y de las competencias que exige cada ocupación?
- **Pregunta técnica:** ¿qué patrones de transición ocupacional y de continuidad o cambio de competencias pueden identificarse en trayectorias laborales posteriores a la formación académica?

El estudio descubre y evalúa patrones presentes en los datos; trabajar (o no) en el área estudiada no se presupone mejor: es una asociación a verificar, no una hipótesis asumida.

## Conceptos clave

| Concepto | Significado |
|---|---|
| `resume_id` | Identificador de persona/currículo; agrupa sus experiencias en una trayectoria |
| Experiencia | Una fila = un empleo (ocupación + periodo), enriquecido con ESCO |
| `matched_code` | Código de ocupación de JobHop v2; se interpreta vía ESCO (`occupations.code`) |
| ESCO / ISCO-08 | Taxonomía europea de ocupaciones; códigos de 4 dígitos = grupo/área ocupacional jerárquica |
| Secuencia `Sₚ` | Representación de una trayectoria: `[(t₁, ocupación, área), (t₂, …), …]` ordenada por trimestre |
| Competencias esenciales | Competencias que ESCO asocia como requisito de una ocupación; se atribuyen analíticamente a cada experiencia laboral clasificada |
| `n_skills_essential` / `n_skills_competence` / `n_skills_knowledge` / `n_skills_sin_tipo` | Contadores de competencias esenciales del oficio, separados por tipo y conservando las relaciones sin tipo declarado |
| `veces_ese_oficio` | Número de experiencias de una persona en el mismo oficio; mide reincidencia sin repetir las competencias como filas |
| `saber_skills` | Estado de disponibilidad del perfil de competencias del oficio: `ok` o `no_clasificado` |
| Censura `Present` | Empleo vigente al capturar el CV (`95.136` filas = `5,08 %`); se marca con bandera, no se inventa su fin |
| Integrado unificado (cruce) | `empleos_unificado_limpio.csv` = unión completa `train + test + val` de JobHop enriquecida con ESCO (`1.871.014` filas = `355.308` personas; unión N:1) |
| `es_unknown_ocupacion` / `es_rescatado` / `es_vigente` | Banderas del limpio: ocupación sin mapeo (`128.981`) / mapeada por prefijo ISCO (`3.295`) / empleo vigente (`95.136`) |

## Fuentes de datos

| Fuente | Rol | Alcance |
|---|---|---|
| **JobHop v2** (`aida-ugent/JobHop`, Hugging Face) | Fuente principal: trayectorias laborales reconstruidas de hojas de vida no estructuradas | Flandes, Bélgica. 3 particiones CSV (`train`/`test`/`val`): columnas clave `resume_id`, `matched_code`, `start_date`, `end_date`, `university_level`. El flujo unificado actual integra **train + test + val** (`1.871.014` experiencias limpias de `355.308` personas) |
| **ESCO v1.2.1** (Comisión Europea) | Fuente de enriquecimiento: da **significado** a cada `matched_code` | `ESCO/occupations_en.csv` (código → nombre + grupo ISCO-08), `ESCO/ISCOGroups_en.csv` (jerarquía del área ocupacional), `SKILLS/occupationSkillRelations_en.csv` (competencias esenciales por oficio), `SKILLS/skills_en.csv` (ficha de cada competencia) |

ESCO no aporta trayectorias: interpreta las ocupaciones para posibilitar el análisis de transiciones. Sobre el universo unificado completo (`1.871.014` filas), `matched_code` cruza **directamente** con `occupations.code` en **2.973 de los 2.991 códigos distintos**, dejando **1.738.738 experiencias emparejadas `ok` (`92,93 %`)** correspondientes a **352.093 personas (`99,10 %`)**.

Las **132.276 filas sin oficio clasificado (`7,07 %`)** se reparten en dos estados:

| Estado | Filas | Qué es | De dónde sale el código |
|---|---|---|---|
| `unknown` | `128.981` (`6,89 %`) | sin coincidencia en ESCO ni en grupo ISCO | ninguno: `occupation_code` e `isco_group` quedan vacíos y se levanta la bandera `es_unknown_ocupacion = 1` |
| `rescatado` | `3.295` (`0,18 %`) | código truncado a 4 dígitos (grupo ISCO) sin ocupación hoja ESCO | conserva `isco_group` e `isco_group_label`, deja `occupation_code` vacío y levanta `es_rescatado = 1` |

Por eso las filas sin `occupation_code` (**132.276**) son exactamente la suma de `es_unknown_ocupacion` (**128.981**) más `es_rescatado` (**3.295**).

### Competencias ESCO: qué significa y qué no

Las 6 columnas de competencias responden "**cuántas competencias esenciales exige el oficio que esta persona ejercía**", no "cuántas sabe". ESCO describe requisitos de un cargo; el dato de skills de un individuo no existe en ninguna fuente y se **atribuye por el puesto que ocupaba**. Toda lectura debe mantener esa distinción: *"este cargo exige N competencias"*, nunca *"esta persona sabe N cosas"*.

| Columna | Significado |
|---|---|
| `saber_skills` | `ok` (`92,93 %`, `1.738.738` filas) con oficio clasificado · `no_clasificado` (`7,07 %`, `132.276` filas) sin oficio. En `no_clasificado` los contadores quedan **vacíos (`NaN`), nunca 0**: un 0 afirmaría que el cargo no exige ninguna competencia, lo cual es falso |
| `n_skills_essential` | Total de competencias `essential` del oficio (mediana `20`, Q1 `15`, Q3 `28`, máximo `99`; límite IQR en B = `47,5`) |
| `n_skills_competence` / `n_skills_knowledge` | El total separado en *saber hacer* (mediana `18`, máx `69`, límite IQR = `39,5`) / *saber* (mediana `3`, máx `45`, límite IQR = `13,5`) |
| `n_skills_sin_tipo` | Bucket de las relaciones que la fuente entrega sin `skillType`; existe para que los tres anteriores sumen el total |
| `veces_ese_oficio` | Cuántas experiencias tiene esta persona en **este** oficio (mediana `1`, Q3 `2`, máx `19`, límite IQR = `3,5`). Define directamente el target supervisado `reincide = (veces_ese_oficio > 1)` |

## Datasets y calidad (antes / después)

| Dataset | Antes (entrada) | Después (salida) | Operación clave |
|---|---|---|---|
| JobHop v2 + ESCO + SKILLS (`unificar_raw_completo.py`) | `train` 1.594.827 · `test` 198.877 · `val` 199.587 (`1.993.291` filas) | `data/02_interim/Unificacion/empleos_unificado_completo.csv` (`1.993.291 × 23`) | Cruce completo de las 3 particiones con ESCO y listas de competencias sin eliminar filas |
| `empleos_unificado_limpio.csv` (**Versión A · Con Outliers**) | `1.993.291 × 23` | **`1.871.014 × 23`** (`355.308` personas) | `limpiar_unificado.py` + validado en `2.0_preprocesamiento_jobpath.ipynb` (`0` duplicados exactos, `0` pérdida en el embudo de 6 fases) |
| `empleos_limpio_con_competencias_sin_outliers.csv` (**Versión B · Sin Outliers IQR**) | `1.871.014 × 23` | **`1.871.014 × 23`** (`355.308` personas) | Winsorización IQR (`k = 1,5`) en `2.0_preprocesamiento_jobpath.ipynb` sobre 4 columnas (`193.596` filas recortadas = `10,35 %`, `0` filas eliminadas) |
| `data/04_transformed/{con_outliers,sin_outliers}/` | `1.738.738` filas clasificadas (`352.093` personas) | `X_train`: **`1.391.018 × 2.985`** (`281.674` pers.) · `X_test`: **`347.720 × 2.985`** (`70.419` pers.) | `3.0_transformacion.ipynb`: `GroupShuffleSplit` 80/20 por `resume_id` (`seed=42`), `RobustScaler`/`MinMaxScaler`/`OneHotEncoder`/`KBinsDiscretizer` ajustados solo en `train` |

## Estructura del proyecto

```text
JobPath/
├── README.md                       # puerta de entrada (este documento)
├── requirements.txt                # dependencias del entorno
├── data/
│   ├── 01_raw/                     # SELECTION — fuentes inmutables, NUNCA se modifican
│   ├── 02_interim/                 # PREPROCESAMIENTO — versiones intermedias y unificación cruda
│   ├── 03_processed/               # PREPROCESAMIENTO — datasets limpios (versiones A y B)
│   │   ├── empleos_unificado_limpio.csv                      # 1.871.014 × 23 (Versión A · con outliers)
│   │   └── empleos_limpio_con_competencias_sin_outliers.csv  # 1.871.014 × 23 (Versión B · winsorizado IQR)
│   └── 04_transformed/             # TRANSFORMACIÓN — matrices X/y y transformadores ajustados en train
│       ├── con_outliers/           # train/ (X_train, y_train) y test/ (X_test, y_test)
│       ├── sin_outliers/           # train/ (X_train, y_train) y test/ (X_test, y_test)
│       └── transformers/           # con_outliers/transformers.joblib y sin_outliers/transformers.joblib
├── docs/
│   └── RefactorDocs/               # guías de ejecución, split por persona e insumos del EDA
├── notebooks/
│   └── refactor/                   # PIPELINE MODULAR EJECUTADO (CRISP-DM + KDD)
│       ├── 1.0_comprension_negocio.md              # acta de constitución analítica
│       ├── 2.0_preprocesamiento_jobpath.ipynb      # limpieza, embudo de filas/personas y winsorización IQR
│       ├── 3.0_transformacion.ipynb                # escalado, codificación, discretización y split por persona
│       ├── 4.0_PCA.ipynb                           # diagnóstico PCA sobre muestra de 10.000 filas
│       ├── 4.1_PCA_completo.ipynb                  # diagnóstico PCA sobre muestra de 50.000 filas
│       └── 5.0_EDA_jobpath.ipynb                   # EDA formal (28 figuras, transiciones, segmentos y auditoría de fuga)
├── reports/
│   └── eda_jobpath/
│       ├── figures/                # 28 figuras PNG (g01 a g30)
│       └── tables/                 # split_map_resume_id.csv y bitácora consolidada
└── scripts/
    ├── README.md                   # documentación de scripts y paquetes modulares
    ├── pipeline/limpieza/          # unificar_raw_completo.py, limpiar_unificado.py y scripts históricos
    └── ScriptsCsv/                 # MÓDULOS SOLID IMPORTADOS POR LOS CUADERNOS
        ├── Preproccesing/          # config, io, duplicates, categories, missing, outliers_iqr, funnel, validation, pipeline
        ├── Transformacion/         # config, comparison, column_profile, date_features, encoding, scaling, discretization, split, validation, export, pca_diagnostic
        └── EDA/                    # config, loader, profiling, descriptive, person_level, transitions, bivariate, pca_evidence, target, leakage, split_map, plots, validation, pipeline
```

## Cómo orientarse en el repositorio

El proyecto se organiza bajo principios **SOLID** en tres capas:

1. **Datos (`data/`):** `01_raw/` contiene las fuentes originales inmutables; `03_processed/` almacena las versiones limpias A (`empleos_unificado_limpio.csv`) y B (`empleos_limpio_con_competencias_sin_outliers.csv`); `04_transformed/` contiene las particiones `train`/`test` por persona y los `.joblib`.
2. **Cuadernos (`notebooks/refactor/`):** Orquestan cada fase importando los paquetes modulares y documentando en español cada decisión, resultado y figura con salidas ejecutadas (`Run All`).
3. **Módulos (`scripts/ScriptsCsv/`):** Contienen toda la lógica pesada en Python con tipado estático, docstrings e inyección de dependencias (`Preproccesing`, `Transformacion`, `EDA`).

### Flujo canónico vigente (`notebooks/refactor/`)

```text
01_raw (JobHop train + test + val, ESCO, SKILLS)
  ↓ unificar_raw_completo.py → limpiar_unificado.py
data/03_processed/empleos_unificado_limpio.csv (Versión A · 1.871.014 × 23 · 355.308 personas)
  ↓ 2.0_preprocesamiento_jobpath.ipynb (Embudo 0 % pérdida + Winsorización IQR k=1,5)
data/03_processed/empleos_limpio_con_competencias_sin_outliers.csv (Versión B · 1.871.014 × 23)
  ↓ 3.0_transformacion.ipynb (Universo clasificado: 1.738.738 filas · 352.093 personas · Split 80/20 por resume_id)
data/04_transformed/{con_outliers,sin_outliers}/{train,test}/{X,y}_*.csv (X_train: 1.391.018 × 2.985 · X_test: 347.720 × 2.985)
  ↓ 4.0_PCA.ipynb (10k) y 4.1_PCA_completo.ipynb (50k)
  ↓ 5.0_EDA_jobpath.ipynb
reports/eda_jobpath/figures/ (28 PNG) + reports/eda_jobpath/tables/split_map_resume_id.csv
```

## Metodología (KDD / CRISP-DM)

| # | Fase KDD | Fase CRISP-DM | Estado | Entregable en `notebooks/refactor/` |
|---|---|---|---|---|
| 1 | **Selección** | Comprensión del negocio | ✅ **HECHO** | `1.0_comprension_negocio.md` |
| 2 | **Preprocesamiento** | Preparación de datos (limpieza) | ✅ **HECHO** | `2.0_preprocesamiento_jobpath.ipynb` (`RowCountFunnel` + versiones A y B) |
| 3 | **Transformación** | Preparación de datos (features y split) | ✅ **HECHO** | `3.0_transformacion.ipynb`, `4.0_PCA.ipynb`, `4.1_PCA_completo.ipynb` |
| 4 | **Exploración y Auditoría** | Comprensión de los datos (iteración formal) | ✅ **HECHO** | `5.0_EDA_jobpath.ipynb` (28 figuras + mapa de split + auditoría de fuga) |
| 5 | **Minería / Modelado** | Modelado (Fase 4) | ⏳ **SIGUIENTE PASO** | Selección de features sin fuga (`X` sin `veces_ese_oficio_*`) y modelado/minería |

## Decisiones técnicas clave

- **Embudo de conteo (`RowCountFunnel`):** Vigila filas y personas (`resume_id`) en cada etapa con alerta automática ante pérdidas `> 5,0 %`, evitando pérdidas silenciosas de datos.
- **Winsorización selectiva IQR (`k = 1,5`):** Se aplica en la Versión B únicamente sobre `n_skills_essential` (`[-4,5, 47,5]`), `n_skills_competence` (`[-4,5, 39,5]`), `n_skills_knowledge` (`[-6,5, 13,5]`) y `veces_ese_oficio` (`[-0,5, 3,5]`). La duración `dur_q` (`Q1=2`, `mediana=5`, `Q3=13`, `IQR=11`, `máx=277`) no se recorta porque representa carreras largas reales.
- **Banderas en lugar de imputación:** Los nulos estructurales de oficio se conservan con banderas (`es_unknown_ocupacion = 128.981`, `es_rescatado = 3.295`) y `'None'` en educación se normaliza a `'No reportado'` (`205.238` filas = `10,97 %`).
- **Censura (`Present`) explícita:** `es_vigente` (`95.136` filas = `5,08 %`) marca empleos en curso al momento de captura del CV (`2026-Q1`).
- **Partición por persona sin fuga (`GroupShuffleSplit`):** `281.674` personas en `train` (`1.391.018` filas) y `70.419` personas en `test` (`347.720` filas), `shared_persons = 0`. Prevalencia de `reincide`: **`30,01 %` en `train`** (`417.471` positivos) y **`29,97 %` en `test`** (`104.225` positivos).
- **Prevención de fuga del target hacia Fase 4:** `reincide` se define como `veces_ese_oficio > 1`. Las columnas `veces_ese_oficio_rob` y `veces_ese_oficio_bin` presentes en `X` reproducen el target al `100 %` y **deben excluirse obligatoriamente de `X` al entrenar modelos en la Fase 4**.

## Limitaciones declaradas

- **Sin causalidad:** Se describen asociaciones y patrones de transición (`1.386.645` transiciones clasificadas en `325.612` personas: `11,95 %` autolazos, `10,31 %` retornos no adyacentes, `16,95 %` dentro del mismo grupo ISCO).
- **"Qué estudió" no está en la fuente:** `university_level`, `isco_group` y el perfil de competencias son proxies parciales del nivel educativo y del sector ocupacional, no de la carrera universitaria.
- **Pluriempleo conservado:** Sobre la llave `(resume_id, start_date, end_date)` existen **`92.099` filas repetidas (`4,92 %`)** que reflejan empleos simultáneos o cambios dentro del mismo trimestre.

## Ruta de lectura sugerida

1. **Este README** — panorama general, arquitectura y cifras verificadas del universo completo.
2. `notebooks/refactor/1.0_comprension_negocio.md` — acta de constitución analítica.
3. `notebooks/refactor/2.0_preprocesamiento_jobpath.ipynb` — limpieza, embudo de filas/personas y winsorización IQR.
4. `notebooks/refactor/3.0_transformacion.ipynb` — codificación, escalado, discretización y partición por persona.
5. `notebooks/refactor/4.0_PCA.ipynb` y `4.1_PCA_completo.ipynb` — estabilidad del diagnóstico PCA (10k vs. 50k).
6. `notebooks/refactor/5.0_EDA_jobpath.ipynb` — EDA formal, 28 figuras en `reports/eda_jobpath/figures/` y auditoría de fuga.
7. `docs/RefactorDocs/guia_ejecucion_notebooks_refactor.md` — guía paso a paso para ejecutar y verificar los cuadernos.

## Referencias

- Dataset JobHop v2: https://huggingface.co/datasets/aida-ugent/JobHop
- Artículo: *JobHop v2: A Large-Scale Career Trajectory Dataset from Unstructured Resumes* (arXiv).
- Taxonomía ESCO v1.2.1 (descarga): https://esco.ec.europa.eu/es/use-esco/download
- API de ESCO: https://data.europa.eu/esco/api