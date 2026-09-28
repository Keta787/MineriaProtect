# JobPath

JobPath es el proyecto de minería de datos que estudia las **trayectorias laborales** reconstruidas por **JobHop v2** y las enriquece con la taxonomía **ESCO v1.2.1** para descubrir patrones de transición ocupacional después de la formación académica. El proyecto sigue las metodologías **KDD** y **CRISP-DM**: sobre el **dato crudo** de JobHop (particiones CSV train/test/val) se integran las fuentes (ESCO) y se ejecutan la unión (**test + val**) y la limpieza en **CSV**, dejando el dataset listo para construir las secuencias por persona (`Sₚ`) y aplicar la minería de secuencias.

> **Estado del proyecto (TL;DR):** ✅ Selección, Preprocesamiento **y Transformación a features HECHOS y verificados** (integrado `empleos.csv` **376.567 × 17**; limpio `empleos_limpio.csv` **376.567 × 20** y variante sin cola larga **341.090 × 20**; codificación ordinal/one-hot, escalado robusto/minmax y auditoría PCA en `notebooks/4.x`, **incluidas las competencias ESCO**) · ⏳ **Pendiente:** construcción de secuencias por persona (`Sₚ`), Minería y Evaluación.
>
> ℹ️ La `X` que sale de `4.0`/`4.1` usa **7 variables**: `start_ord`, `end_ord`, `dur_q` y `n_skills_essential` / `veces_ese_oficio` con `RobustScaler`, `univ_ord` con `MinMaxScaler`, y el binario `reincide` sin escalar. Como el 7,5 % de las filas no tiene oficio clasificado y `sklearn` no admite `NaN` en un escalador, **esas filas salen de la `X`** (376.567 → 348.263 y 341.090 → 314.904) y la pérdida se declara en el cuaderno. Ver `docs/SKILLS.md` §10.

## Contenidos

1. [Contexto general del proyecto](#contexto-general-del-proyecto)
2. [Objetivo, finalidad y preguntas de investigación](#objetivo-finalidad-y-preguntas-de-investigación)
3. [Conceptos clave](#conceptos-clave)
4. [Fuentes de datos](#fuentes-de-datos)
5. [Datasets y calidad (antes / después)](#datasets-y-calidad-antes--después)
6. [Estructura del proyecto](#estructura-del-proyecto)
7. [Metodología (KDD / CRISP-DM)](#metodología-kdd--crisp-dm)
8. [Lo que se hizo en el código](#lo-que-se-hizo-en-el-código)
9. [Decisiones técnicas clave](#decisiones-técnicas-clave)
10. [Excepciones explícitas del proyecto](#excepciones-explícitas-del-proyecto)
11. [Decisiones de negocio pendientes](#decisiones-de-negocio-pendientes)
12. [Verificación del resultado](#verificación-del-resultado)
13. [Cómo ejecutar (reproducibilidad)](#cómo-ejecutar-reproducibilidad)
14. [Estado actual y siguientes pasos](#estado-actual-y-siguientes-pasos)
15. [Limitaciones](#limitaciones)
16. [Ruta de lectura sugerida](#ruta-de-lectura-sugerida)
17. [Referencias](#referencias)

## Contexto general del proyecto

JobPath es un proyecto académico del curso de **Minería de Datos** (2026-2, Unidad 1) de la Especialización en Ingeniería de Sistemas de **UNIMINUTO (Ibagué)**, formalizado sobre las metodologías **KDD** y **CRISP-DM** (acta de constitución analítica en `notebooks/1.0_comprension_negocio.md`).

**El problema de fondo.** Las hojas de vida contienen historial laboral en lenguaje natural y no estructurado: distintas personas describen cargos de maneras distintas y no existe un significado estandarizado de cada ocupación. **JobHop v2** ya reconstruyó ese historial en un dataset relacional —una fila por experiencia laboral con `resume_id`, fechas y un código de ocupación (`matched_code`)— pero los códigos aún carecen de *significado* interpretable. Para comparar trayectorias y estudiar transiciones se necesita traducir cada código a una ocupación con nombre y área ocupacional: ese es el papel de la taxonomía **ESCO v1.2.1**.

**El problema de interés.** Después de terminar una formación, ¿se queda la persona en el área que estudió? ¿cambia de área y cuántas veces? ¿qué ocupaciones suceden a otras y qué caminos se repiten? Como no se asume causalidad, el proyecto responde en términos **descriptivos y de patrón**, no de causa-efecto.

> Los datos de JobHop provienen de **Flandes, Bélgica**. El país no es el objetivo del proyecto; el objetivo son las **trayectorias laborales** y sus patrones de transición.

## Objetivo, finalidad y preguntas de investigación

**Objetivo:** descubrir y evaluar los patrones de transición ocupacional presentes en las trayectorias laborales posteriores a la formación académica.

**Finalidad de minería (inmediata).** Construir el dataset de **secuencias por persona** (`Sₚ`) y aplicar técnicas de minería de secuencias/transiciones para identificar patrones **frecuentes, consistentes, interpretables y útiles** que respondan las preguntas del proyecto.

**Finalidad de conocimiento (última).** Caracterizar los principales patrones de transición ocupacional y consolidar un informe reproducible y documentado que sirva de base descriptiva para futuras preguntas sobre la relación formación–empleo e inserción laboral (fase de conocimiento de KDD).

- **Pregunta sencilla:** ¿qué patrones aparecen en la trayectoria laboral de las personas después de su formación, especialmente respecto de si sus empleos corresponden o no con lo que estudiaron?
- **Pregunta técnica:** ¿qué patrones de transición ocupacional pueden identificarse en trayectorias laborales posteriores a la formación académica?

El estudio descubre y evalúa patrones presentes en los datos; trabajar (o no) en el área estudiada no se presupone mejor: es una asociación a verificar, no una hipótesis asumida.

## Conceptos clave

| Concepto | Significado |
|---|---|
| `resume_id` | Identificador de persona/currículo; agrupa sus experiencias en una trayectoria |
| Experiencia | Una fila = un empleo (ocupación + periodo), enriquecido con ESCO |
| `matched_code` | Código de ocupación de JobHop v2; se interpreta vía ESCO (`occupations.code`) |
| ESCO / ISCO-08 | Taxonomía europea de ocupaciones; códigos de 4 dígitos = grupo/área ocupacional jerárquica |
| Secuencia `Sₚ` | Representación de una trayectoria: `[(t₁, ocupación, área), (t₂, …), …]` ordenada por trimestre |
| Censura `Present` | Empleo vigente al capturar el CV; se marca con bandera, no se inventa su fin |
| Integrado (cruce) | `empleos` = unión test + val de JobHop enriquecida con ESCO (1 fila = 1 experiencia; unión N:1) |
| `es_unknown_ocupacion` / `es_rescatado` / `es_vigente` | Banderas del limpio: ocupación sin mapeo / mapeada por prefijo / empleo vigente (censura) |

## Fuentes de datos

| Fuente | Rol | Alcance |
|---|---|---|
| **JobHop v2** (`aida-ugent/JobHop`, Hugging Face) | Fuente principal: trayectorias laborales reconstruidas de hojas de vida no estructuradas | Flandes, Bélgica. 3 particiones CSV (`train`/`test`/`val`): columnas clave `resume_id`, `matched_code`, `start_date`, `end_date`, `university_level`. El integrado usa **test + val** |
| **ESCO v1.2.1** (Comisión Europea) | Fuente de enriquecimiento: da **significado** a cada `matched_code` | `ESCO/occupations_en.csv` (código → nombre + grupo ISCO-08), `ESCO/ISCOGroups_en.csv` (jerarquía del área ocupacional), `SKILLS/occupationSkillRelations_en.csv` (competencias esenciales por oficio), `SKILLS/skills_en.csv` (ficha de cada competencia). `greenShareOcc_en.csv` se descartó: no responde a la pregunta de investigación. **Ojo:** queda una copia limpia en `data/02_interim/ESCO/greenShareOcc_en_limpio.csv` de cuando sí se procesó, pero su crudo ya no está en `data/01_raw/`, de modo que no se puede regenerar y nada la consume. Es un resto, no una entrada del pipeline |

Fuentes públicas declaradas (sesión 2: ≥2 fuentes, ≥1 API o base pública): JobHop v2 se aloja en **Hugging Face** (descarga oficial del dato crudo) y ESCO es la base oficial de la **Unión Europea** con **API REST documentada** (`https://data.europa.eu/esco/api`). El cuaderno `2.0` §5b demuestra la consulta en vivo sobre un `conceptUri` real del dataset, con fallback informativo si la red de evaluación no alcanza el dominio.

ESCO no aporta trayectorias: interpreta las ocupaciones para posibilitar el análisis de transiciones. Sobre el integrado test+val, `matched_code` cruza **directamente** con `occupations.code` en 2.855 de 2.873 códigos únicos (93,1 % de las filas, emparejado `ok` 348.263); el resto se rescata por prefijo (grupo ISCO de 4 dígitos, `rescatado` 2.499) o se flagga (`unknown` 25.805).

### Competencias ESCO: qué significa y qué no

Las 6 columnas de competencias responden "**cuántas competencias esenciales exige el oficio que esta persona ejercía**", no "cuántas sabe". ESCO describe requisitos de un cargo; el dato de skills de un individuo no existe en ninguna fuente y se **atribuye por el puesto que ocupaba**. Toda lectura debe mantener esa distinción: *"este cargo exige N competencias"*, nunca *"esta persona sabe N cosas"`.

| Columna | Significado |
|---|---|
| `saber_skills` | `ok` (92,5 %) con oficio clasificado · `no_clasificado` (7,5 %) sin oficio. En `no_clasificado` los contadores quedan **vacíos, nunca 0**: un 0 afirmaría que el cargo no exige ninguna competencia, lo cual es falso |
| `n_skills_essential` | Total de competencias `essential` del oficio (mediana 20, máximo 99) |
| `n_skills_competence` / `n_skills_knowledge` | El total separado en *saber hacer* / *saber* |
| `n_skills_sin_tipo` | Bucket de las 39 relaciones que la fuente entrega sin `skillType`; existe para que los tres anteriores sumen el total |
| `veces_ese_oficio` | Cuántas experiencias tiene esta persona en **este** oficio. Resuelve la reincidencia: quien repite el mismo cargo 19 veces tiene 19 filas con `veces_ese_oficio = 19`, y sus competencias no se repiten |

Solo se usan las relaciones `essential` (67.600 de 126.051): las `optional` son habilidades de nivelación, no el piso del cargo, y sumarlas volvería el conteo interpretable. Los **nombres** de las competencias no viven en el pipeline (solo hay contadores, para no multiplicar las filas ×21); se recuperan con `indicadores.skills_de_ocupacion()` o `indicadores.skills_de_persona()`, que resuelven el salto `code` → `occupationUri` (UUID) del puente ESCO.

> **Referencia completa del tema: [`docs/SKILLS.md`](docs/SKILLS.md).** Incluye las seis columnas
> medidas una por una, por qué son contadores y no filas, qué se puede y qué no se puede sacar de
> ellas (las seis columnas no son seis variables), y las recetas de uso.

## Datasets y calidad (antes / después)

| Dataset | Antes (entrada) | Después (salida) | Operación clave |
|---|---|---|---|
| JobHop v2 (dato crudo, CSV) | test 198.877 · val 199.587 · train 1.594.827 | test 188.061 · val 188.506 · train 1.506.445 | Del dato crudo al CSV: elimina filas sin `start_date` y duplicados; el integrado `empleos` solo toma **test + val** |
| `ESCO/occupations_en.csv` | 3.043 | 3.039 | −4 filas por `code` duplicado |
| `ESCO/ISCOGroups_en.csv` | 619 (8 col.) | 619 (7 col.) | Columna 100 % nula eliminada |
| `SKILLS/occupationSkillRelations_en.csv` | 126.051 | 126.051 | 59 con `skillType` nulo conservados (bandera) |
| `SKILLS/skills_en.csv` | 13.960 | 13.939 | −21 filas por `conceptUri` duplicado |
| `empleos.csv` (integrado, unión test+val) | — | 376.567 × 17 (inmutable) | Integración validada (`integrar_empleos.py`); cruce N:1 por persona + 6 columnas de competencias |
| `empleos_limpio.csv` (integrado) | 376.567 × 17 | **376.567 × 20** | Pipeline en 7 fases: 0 filas con fechas futuras en test+val (MCAR) + 3 banderas `es_*` |
| `empleos_limpio_sin_outliers.csv` | 376.567 × 20 | 341.090 × 20 | Variante sin cola larga (`dur_Q ≥ 25`, IQR de Tukey); −35.477 filas / 24.687 personas |

Validación final del limpio (**6/6**): duplicados · duplicados por llave natural · nulos sin bandera · nulos de ocupación sin bandera · fechas futuras · `start > end`. Lectura siempre como texto (`dtype=str`) para conservar ceros a la izquierda en los códigos ISCO/ESCO.

## Estructura del proyecto

```text
JobPath/
├── README.md                       # puerta de entrada (este documento)
├── .gitignore                      # contextos, metodología y CSV pesados fuera de git
├── requirements.txt                # pandas, pyarrow, matplotlib, nbconvert, ipykernel, jupyter-client
├── data/
│   ├── 01_raw/                     # SELECTION — fuentes inmutables, NUNCA se modifican
│   │   ├── JobHop (dato crudo)   # trayectorias (JobHop v2)
│   │   ├── ESCO/                   # occupations_en, ISCOGroups_en
│   │   └── SKILLS/                 # occupationSkillRelations_en, skills_en
│   ├── 02_interim/                 # PREPROCESAMIENTO — versiones limpias de las fuentes
│   │   ├── JobHop (limpio)         # dato crudo limpio, listo para el cruce en CSV
│   │   ├── ESCO/                   # *_limpio.csv (códigos como texto)
│   │   └── SKILLS/                 # puente de competencias limpio
│   └── 03_processed/               # PREPROCESAMIENTO — integrado, formato exclusivo: CSV
│       ├── empleos.csv             # 376.567 × 17 (unión test+val; inmutable)
│       ├── empleos_limpio.csv      # 376.567 × 20 (limpio final, banderas es_*)
│       └── empleos_limpio_sin_outliers.csv  # 341.090 × 20 (sin cola larga)
├── logs/                           # bitácoras de ejecución (solo en disco, no versionadas)
├── notebooks/                      # COMPRENSION/EXPLORACION — unidad por fase
│   ├── 1.0_comprension_negocio.md         # acta de constitución analítica (sesión 1)
│   ├── 2.0_EDA_y_seleccion.ipynb          # fuentes, carga defensiva, EDA, API ESCO (sesión 2)
│   ├── 3.0_preprocesamiento.ipynb         # pipeline de limpieza en 7 fases + validación (sesión 3)
│   ├── 4.0_transformacion.ipynb           # codificación ordinal/one-hot + escalado + PCA (sesión 4, con cola)
│   ├── 4.1_transformacion_sin_outliers.ipynb  # ídem sobre la variante sin cola larga
│   └── ENTREGAMINERIA.pdf                 # informe de entrega (marco KDD–CRISP-DM)
└── src/                            # CODIGO REUTILIZABLE
    ├── filtro/                     # TRANSFORMACION (insumos) — análisis reutilizable
    │   ├── filtros.py              # selecciones: nivel, grupo ISCO, ocupación, periodo, vigencia
    │   └── indicadores.py          # duración, IQR, transiciones, brechas, crosstabs, banderas
    └── limpieza/                   # PREPROCESAMIENTO/PREPARACION
        ├── limpiar_datos.py        # data/01_raw/ → data/02_interim/ (limpieza de fuentes)
        ├── integrar_empleos.py      # unión test+val + ESCO → data/03_processed/empleos.csv
        ├── limpiar_empleos.py      # data/03_processed/empleos.csv → empleos_limpio.csv (7 fases)
        └── dividir_por_outliers.py # empleos_limpio.csv → empleos_limpio_sin_outliers.csv (IQR)
```

Reglas de oro: originales intocables · derivados regenerables (pipelines **deterministas**) · rutas relativas (la raíz se resuelve buscando `data/` hacia arriba) · salida del cruce única en **CSV** · toda decisión de negocio documentada en bitácora (`logs/`).

## Metodología (KDD / CRISP-DM)

| # | Fase KDD | Fase CRISP-DM | Estado | Entregable |
|---|---|---|---|---|
| 1 | **Selección** | Comprensión del negocio | ✅ **HECHO** | Acta `1.0`; objetivo, preguntas y fuentes (JobHop v2 + ESCO v1.2.1) |
| 2 | **Preprocesamiento** | Comprensión y preparación de datos | ✅ **HECHO** | Fuentes limpias (`02_interim`); integrado validado; `empleos_limpio.csv` (20 columnas, incluye 6 de competencias ESCO) y variante sin cola larga; **transformación a features** (ordinal/one-hot/escalado/PCA) en `4.0` y `4.1` — competencias ESCO incorporadas a la `X` en la sección 2.5 (`docs/SKILLS.md` §10) |
| 3 | **Transformación** | Preparación (hacia modelado) | ✅ **HECHO** (features listas) | Codificación y escalado entregados en `notebooks/4.x`, **competencias ESCO incluidas** (sección 2.5); resta la construcción de secuencias por persona (`Sₚ`); insumos listos en `src/filtro/` |
| 4 | **Minería** | Modelado | ⏳ **PENDIENTE** | Técnica de minería de secuencias/transiciones a seleccionar |
| 5 | **Interpretación y evaluación** | Evaluación | ⏳ **PENDIENTE** | Patrones juzgados: frecuentes, consistentes, interpretables, útiles |
| 6 | **Conocimiento** | Despliegue | ⏳ **PENDIENTE** | Caracterización de patrones e informe final |

El marco rector completo (mapeo KDD ↔ CRISP-DM por corte, criterios de éxito, cifras de auditoría) está en `METODOLOGIA_KDD_CRISPDM.md` (solo en disco, por decisión acordada). La alineación por entregable y las referencias cruzadas entre unidad, fase y sesión están en la sección §6 del acta `1.0`.

## Lo que se hizo en el código

**`src/limpieza/limpiar_datos.py`** — limpieza de fuentes: `data/01_raw/` → `data/02_interim/`.
Limpia las 3 particiones CSV de JobHop (`train`/`test`/`val`: elimina filas sin `start_date` y duplicados, ordena por persona/trimestre) y los cuatro CSV de ESCO en `ESCO/` + `SKILLS/` (duplicados por `code`/`conceptUri`, columnas 100 % nulas). Función `validar(...)` audita cada archivo; bitácora de cambios por ejecución.

**`src/limpieza/integrar_empleos.py`** - integración: une las particiones limpias **test + val** de JobHop (train excluido), cruza `matched_code` con ESCO (`emparejado`: `ok` / `rescatado` / `unknown`), agrega los contadores de competencias ESCO y crea `data/03_processed/empleos.csv` (376.567 × 17, 71.061 personas).

**`src/limpieza/limpiar_empleos.py`** — clase `LimpiadorEmpleos` con **7 fases** (`fase1_diagnostico` … `fase7_exportar`) sobre el integrado `empleos.csv` (CSV). Cada fase termina en un `assert` contra `EXPECTED` (umbrales de aceptación, criterio "funciones reutilizables + pruebas automáticas" de la rúbrica de la sesión 3):
1. Diagnóstico (nada se toca) → 2. Duplicados (0 exactos; claves cortas = pluriempleo, se conservan) → 3. Categorías y caso MNAR (`'None'` y celdas vacías → `'No reportado'`) → 4. Faltantes por bandera (MAR + censura, sin imputar) → 5. Outliers IQR de Tukey + 0 fechas futuras en test+val (MCAR) → 6. Validación 6/6 → 7. Exportar CSV + bitácora.

**`src/limpieza/dividir_por_outliers.py`** — genera la variante **sin cola larga** (`empleos_limpio_sin_outliers.csv`) con la misma convención IQR de la fase 5 (`dur_Q ≥ 25`), para comparar el impacto de la cola larga antes de elegir la técnica de minería.

**`src/filtro/filtros.py` y `src/filtro/indicadores.py`** — biblioteca reutilizable de **transformación**: filtros (nivel educativo, grupo ISCO, ocupación, periodo, vigentes) e indicadores (duración trimestral inclusiva, distribución, medianas por grupo/nivel, crosstabs, transiciones consecutivas, proporción que conserva el grupo, primera→segunda ocupación, brechas entre empleos, personas solapadas, resumen de banderas). Son los insumos de la fase 3 (construcción de `Sₚ`).

**`notebooks/`** — reproducen y exhiben cada fase con evidencia impresa y outputs persistidos: `1.0` (acta/diseño), `2.0` (selección de fuentes + carga defensiva + EDA + diagnóstico de calidad + API ESCO), `3.0` (pipeline de limpieza ejecutado en vivo, validación 6/6, bitácora, división con/sin cola larga). De la **sesión 4 (transformación)**, `4.0_transformacion.ipynb` (sobre `empleos_limpio.csv`, con cola larga) y `4.1_transformacion_sin_outliers.ipynb` (sobre la variante sin cola larga) comparten un pipeline parametrizado por `VERSION` (una celda de configuración elige el CSV):

1. **Justificación por categoría** de por qué cada columna es ordinal (jerarquía real: fechas `Qn AAAA`, `university_level`, `isco_level`) o one-hot (sin orden: `emparejado`, `occupation_code`, banderas `es_*`) — con auditoría de redundancias (1:1, prefijos, constantes) que descarta `matched_code`, `occupation_label`, `isco_group*`.
2. **Codificación:** ordinal `año×4+trimestre` + `KBinsDiscretizer` (quantile, demo) para fechas; mapeo manual 0–4 para educación; `get_dummies` (demo) y `OneHotEncoder` sparse (producción) para las nominales; banderas como 0/1 enteros.
3. **Escalado con auditoría de outliers (Tukey):** `RobustScaler` para fechas y `dur_q` (colas reales censuradas), `MinMaxScaler` para educación (rango acotado) y `StandardScaler` mostrado y descartado; **no se escalan dummies ni banderas**; `fit` solo sobre la muestra (sin fuga de datos).
4. **PCA auditado y descartado (sección 4.3):** correlaciones + varianza acumulada muestran que las numéricas son ~3 dimensiones lineales (`dur_q = end − start + 1`) y que las dummies no entran a PCA por diseño; no comprime aquí.

Se ejecutan de principio a fin sin errores (núcleo `python3` 3.14.7) y entregan una **X** numérica finita (0 nulos, 0 columnas no numéricas) lista para minería.

## Decisiones técnicas clave

- **Salida única en CSV para el cruce:** `empleos.csv`, `empleos_limpio.csv` y `empleos_limpio_sin_outliers.csv` se mantienen exclusivamente en CSV (`data/03_processed/`), regenerables desde los scripts. Los CSV no se versionan por tamaño (41–48 MB) y la estructura de la carpeta se conserva en git con `.gitkeep`.
- **CSV procesados también en Google Drive:** el integrado (`empleos.csv`), la versión limpia con outliers (`empleos_limpio.csv`) y la versión limpia sin outliers (`empleos_limpio_sin_outliers.csv`) se comparten en: https://drive.google.com/file/d/1NH-ibBT_wsehhnQNOKCpGJDx1UPmG1sC/view
- **Banderas en lugar de imputación:** la ausencia es informativa; no se usa `fillna`. Nulos estructurales conservados con banderas: `es_unknown_ocupacion` (25.805), `es_rescatado` (2.499) y re-categorización de `'None'`/celdas vacías → `'No reportado'` (42.807).
- **Censura (`Present`) explícita:** `es_vigente` (18.956) marca empleos vigentes al capturar el CV; no se inventa fecha de fin (censura por la derecha).
- **Duración trimestral inclusiva:** `end − start + 1` (un empleo del mismo trimestre dura 1); Q1=2, mediana 5, Q3=11, IQR=9, máximo 160 (≈40 años).
- **Solo se elimina lo justificado:** 0 filas con fechas futuras en test+val (MCAR de dominio; el pipeline las eliminaría si aparecieran). La cola larga de duración (IQR de Tukey, límite superior **24,5**) se **conserva**: estabilidad de carrera = señal, no contaminación.
- **Lectura defensiva:** `dtype=str`, `encoding="utf-8"`, `keep_default_na=False` + `na_values=[""]` para conservar ceros a la izquierda y literales `'None'`/`'Present'`/`'unknown'` como texto (trampas de la sesión 2).
- **Transformación 4.x:** escalador elegido por los outliers re-auditados (robust para fechas/duración aunque se limpie la cola — la censura `Present`→Q1 2026 recrea extremos; minmax para educación); banderas y dummies sin escalar; PCA descartado tras correlación/varianza. `fit` del escalador solo sobre la muestra de trabajo.

## Excepciones explícitas del proyecto

- **Prints/bitácoras como entregable:** la bitácora impresa por scripts y cuadernos (diagnóstico, decisiones, validación, SHA de trazabilidad) es parte del entregable académico; no son residuos de depuración.
- **Salida única en CSV en el cruce:** decisión de negocio acordada por el equipo (interoperabilidad y revisión manual).
- **Banderas en lugar de imputar:** reemplaza la estrategia tradicional de imputación (MAR/MNAR informativos en este dataset).
- **Notebooks ejecutados con outputs persistidos:** la entrega se presenta con los resultados en el cuaderno (git conserva los outputs); `1.0` es un acta en Markdown por diseño (no ejecutable).

## Decisiones de negocio pendientes

Deudas formales heredadas para la fase de minería:

| # | Decisión | Pregunta a resolver |
|---|---|---|
| D1 | Tratamiento de `unknown` en minería | ¿Se excluyen, se marcan como paso nulo o se analizan como segmento propio las filas con `es_unknown_ocupacion`? |
| D2 | Empleos simultáneos / pluriempleo (18.749 claves cortas) | ¿Cómo se concreta la regla de negocio "transición" en secuencias con pluriempleo conservado? |
| D3 | ~~Enriquecimiento temático futuro~~ | **RESUELTO**: las competencias ESCO ya están agregadas al integrado como 6 columnas de contadores (`saber_skills`, `n_skills_essential`, `n_skills_competence`, `n_skills_knowledge`, `n_skills_sin_tipo`, `veces_ese_oficio`). `greenShare` se descartó por no responder a la pregunta de investigación |
| D4 | Técnica de minería y destino de las secuencias | ¿Qué técnica y dónde se persiste `Sₚ` (misma regla: CSV + original intocable)? |

## Verificación del resultado

- **Asserts por fase (nivel "Excepcional"):** `limpiar_empleos.py` valida cada fase contra cantidades verificadas de la fuente (`EXPECTED`), con tabla de umbrales 10/10 y bitácora de trazabilidad en `logs/`. Cuatro de esos umbrales son de las competencias: que el contador esté vacío exactamente cuando `saber_skills != 'ok'`, que nunca valga 0, que los tres buckets sumen el total, y que `veces_ese_oficio ≥ 1`.
- **Cuadernos de diagnóstico:** `2.0`, `3.0`, `4.0` y `4.1` se ejecutan de principio a fin sin errores y reproducen los scripts con evidencia impresa (nbclient con núcleo `python3`).
- **Sanidad de la matriz final (4.x):** `X_final` sin nulos y sin columnas no numéricas; mediana ≈ 0 en las robust, extremos 0/1 en la minmax; auditoría de outliers y varianza de PCA impresas en vivo.
- **Comparación con/sin cola larga:** `dividir_por_outliers.py` cruza ambas versiones (filas, personas, mediana/máximo de `dur_Q`, vigentes) para cuantificar el impacto antes de elegir la técnica de minería.
- **Idempotencia/regeneración:** los pipelines son deterministas (sin aleatoriedad) y regenerables desde `data/01_raw/`; cada cifra del informe se reproduce con los comandos de la sección siguiente.
- **API pública (sesión 2):** `2.0` §5b intenta la consulta REST de ESCO sobre un `conceptUri` real; en redes sin acceso reporta el fallback con las URLs oficiales (la respuesta JSON viva requiere red que alcance `data.europa.eu/esco/api`).

## Cómo ejecutar (reproducibilidad)

```bash
python -m pip install -r requirements.txt

python src/limpieza/limpiar_datos.py        # fuentes → data/02_interim/
python src/limpieza/integrar_empleos.py     # unión test+val + ESCO + competencias → empleos.csv
python src/limpieza/limpiar_empleos.py      # integrado → data/03_processed/empleos_limpio.csv
python src/limpieza/dividir_por_outliers.py # limpio → empleos_limpio_sin_outliers.csv
```

Los cuatro scripts son **deterministas y se ejecutan en ese orden**: `integrar_empleos.py` necesita el puente de competencias ya limpio, así que `limpiar_datos.py` va primero (además es quien crea las carpetas `ESCO/` y `SKILLS/` en `02_interim/`).

Los scripts resuelven la raíz del proyecto buscando hacia arriba la carpeta `data/`, por lo que se ejecutan desde cualquier directorio del repo (rutas relativas). Requiere **Python 3** (referencia: `.python-version` = 3.14.7, documento `requirements.txt`) y las dependencias declaradas (pandas, pyarrow, matplotlib, **scikit-learn** para la transformación `4.x`, nbconvert, ipykernel, jupyter-client).

**Regeneración de derivados (cierre del ciclo):**
- `data/02_interim/**` y los CSV de `data/03_processed/` se regeneran con los scripts anteriores.
- `data/03_processed/empleos.csv` es el integrado canónico; se regenera con `integrar_empleos.py` (unión test+val + cruce ESCO) o se restaura desde el historial git.
- El repositorio versiona `data/01_raw/` y `data/02_interim/` completos; no versiona los CSV del cruce por tamaño.

## Estado actual y siguientes pasos

**Estado:** la limpieza está **100 % terminada y verificada** en los tres niveles — fuentes (`limpiar_datos.py`), integración (`integrar_empleos.py`) e integrado (`limpiar_empleos.py`). `empleos_limpio.csv` alcanzó **376.567 filas × 20 columnas** (71.061 personas), con validación final 10/10; la variante sin cola larga (341.090 × 20, 69.182 personas) queda lista para comparar. Las 6 columnas de competencias ESCO son **contadores por experiencia** (nunca filas: hacerlo multiplicaría el dataset ×21 y rompería la llave primaria), y los nombres de las competencias se recuperan bajo demanda con `indicadores.cargar_relaciones()`. La **transformación a features** (sesión 4) está terminada **e incluye las competencias ESCO**: `4.0` y `4.1` codifican (ordinal/one-hot), escalan (robust/minmax) y auditan PCA, entregando la **X** numérica lista para modelar. La `X` incorpora `n_skills_essential` y `veces_ese_oficio` con `RobustScaler` más el binario `reincide` sin escalar, y deja fuera de sí misma las 28.304 filas `no_clasificado` porque sus contadores están vacíos y `sklearn` no admite `NaN` (mediciones en `docs/SKILLS.md` §10).304 filas `no_clasificado` (ver `docs/SKILLS.md` §10, con las mediciones). Alineado con las sesiones 1–4: acta (1.0), fuentes/carga defensiva/EDA/API (2.0), pipeline de limpieza con rúbrica de código (3.0) y transformación (4.0/4.1).

**Siguiente paso:** construir el **dataset de secuencias por persona** (`Sₚ`) sobre `empleos_limpio.csv`: orden estable por trimestre, unidad de análisis (ocupación ESCO / grupo ISCO), ventana temporal y manejo de pluriempleo y censura (ver `src/filtro/`). La **X** de los cuadernos 4.x habilita los modelos de sesiones 7–9 (KNN / K-means / árboles). Sobre esas secuencias se seleccionará y aplicará la técnica de minería, se evaluarán los patrones y se consolidará el conocimiento (fases 3–6 de la tabla metodológica).

## Limitaciones

- **Sin causalidad:** se describen asociaciones y patrones; no se demuestra que una característica cause una trayectoria.
- **Alcance geográfico:** los datos provienen de Flandes, Bélgica; los hallazgos no describen un mercado laboral colombiano.
- **ESCO solo enriquece:** no aporta trayectorias; sin ella, `matched_code` no es interpretable.
- **Censura y ausencia sin imputar:** `Present` y `unknown` se conservan con banderas; su rol en la minería está en discusión (D1).
- **Pluriempleo conservado:** las 18.749 claves cortas simultáneas se mantienen; la regla de "transición" se define en la fase de transformación (D2).
- **Técnica de minería por definir:** se fija tras explorar la estructura final de las secuencias.
- **API ESCO dependiente de red:** la demostración en vivo (§5b de `2.0`) requiere acceso a `data.europa.eu/esco/api` desde la máquina que la ejecute.

## Ruta de lectura sugerida

1. **Este README** — panorama, estado, metodología y repro por comandos.
2. `METODOLOGIA_KDD_CRISPDM.md` (solo en disco) — marco rector y plan de acción fase a fase.
3. `notebooks/1.0_comprension_negocio.md` — acta de constitución analítica.
4. `notebooks/2.0_EDA_y_seleccion.ipynb` — fuentes, carga defensiva, EDA y diagnóstico.
5. `notebooks/3.0_preprocesamiento.ipynb` — pipeline de limpieza, validación y bitácora.
6. `notebooks/4.0_transformacion.ipynb` y `4.1_transformacion_sin_outliers.ipynb` — transformación a features (codificación, escalado, PCA) en ambas versiones.
7. **Código:** `src/limpieza/` (pipelines) y `src/filtro/` (análisis reutilizable).

## Referencias

- Dataset JobHop v2: https://huggingface.co/datasets/aida-ugent/JobHop
- Artículo: *JobHop v2: A Large-Scale Career Trajectory Dataset from Unstructured Resumes* (arXiv).
- Taxonomía ESCO v1.2.1 (descarga): https://esco.ec.europa.eu/es/use-esco/download
- API de ESCO (sesión 2): https://data.europa.eu/esco/api