# JobPath

JobPath es el proyecto de preparación de datos para IA y minería de patrones comportamentales que estudia las **trayectorias laborales** reconstruidas por **JobHop v2** y las enriquece con la taxonomía **ESCO v1.2.1** para descubrir patrones de transición ocupacional, permanencia, reincidencia y continuidad de competencias después de la formación académica. El proyecto sigue las metodologías **KDD** y **CRISP-DM**: sobre el **dato crudo** de JobHop (particiones CSV train/test/val) se integran las fuentes (ESCO) y se ejecutan la unión (**test + val**) y la limpieza en **CSV**, dejando el dataset listo para construir las secuencias por persona (`Sₚ`) y aplicar la minería de secuencias.

> **Estado del proyecto (TL;DR):** ✅ Selección, Preprocesamiento **y Transformación a features HECHOS y verificados** (integrado enriquecido `empleos_con_competencias.csv` **376.567 × 20**; limpio  `empleos_con_competencias_limpio.csv` **376.567 × 23** y variante sin cola larga **341.090 × 23**; codificación ordinal/one-hot, escalado robusto/minmax, perfiles de skills y auditoría PCA en `src/transformacion/` (evidencia en `notebooks/4.x`), **incluidas las competencias ESCO**) · ⏳ **Pendiente:** construcción de secuencias por persona (`Sₚ`), Minería y Evaluación.
>
> ℹ️ La `X` que sale de `4.0`/`4.1` combina **7 variables base**: `start_ord`, `end_ord`, `dur_q` y `n_skills_essential` / `veces_ese_oficio` con `RobustScaler`, `univ_ord` con `MinMaxScaler`, y el binario `reincide` sin escalar. También incorpora las variables one-hot y los indicadores `tiene_skills`, `tiene_knowledge` y `tiene_sin_tipo`. Como el 7,5 % de las filas no tiene oficio clasificado y `sklearn` no admite `NaN` en un escalador, **esas filas salen de la `X`** (376.567 → 348.263 y 341.090 → 314.904) y la pérdida se declara en el cuaderno. Ver `docs/SKILLS.md` §10.

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
| Censura `Present` | Empleo vigente al capturar el CV; se marca con bandera, no se inventa su fin |
| Integrado (cruce) | `empleos` = unión test + val de JobHop enriquecida con ESCO (1 fila = 1 experiencia; unión N:1) |
| `es_unknown_ocupacion` / `es_rescatado` / `es_vigente` | Banderas del limpio: ocupación sin mapeo / mapeada por prefijo / empleo vigente (censura) |

## Fuentes de datos

| Fuente | Rol | Alcance |
|---|---|---|
| **JobHop v2** (`aida-ugent/JobHop`, Hugging Face) | Fuente principal: trayectorias laborales reconstruidas de hojas de vida no estructuradas | Flandes, Bélgica. 3 particiones CSV (`train`/`test`/`val`): columnas clave `resume_id`, `matched_code`, `start_date`, `end_date`, `university_level`. El integrado usa **test + val** |
| **ESCO v1.2.1** (Comisión Europea) | Fuente de enriquecimiento: da **significado** a cada `matched_code` | `ESCO/occupations_en.csv` (código → nombre + grupo ISCO-08), `ESCO/ISCOGroups_en.csv` (jerarquía del área ocupacional), `SKILLS/occupationSkillRelations_en.csv` (competencias esenciales por oficio), `SKILLS/skills_en.csv` (ficha de cada competencia). `greenShareOcc_en.csv` se descartó: no responde a la pregunta de investigación. **Ojo:** queda una copia limpia en `data/02_interim/ESCO/greenShareOcc_en_limpio.csv` de cuando sí se procesó, pero su crudo ya no está en `data/01_raw/`, de modo que no se puede regenerar y nada la consume. Es un resto, no una entrada del pipeline |

Fuentes públicas declaradas (sesión 2: ≥2 fuentes, ≥1 API o base pública): JobHop v2 se aloja en **Hugging Face** (descarga oficial del dato crudo) y ESCO es la base oficial de la **Unión Europea** con **API REST documentada** (`https://data.europa.eu/esco/api`). El cuaderno `2.0` §5b demuestra la consulta en vivo sobre un `conceptUri` real del dataset, con fallback informativo si la red de evaluación no alcanza el dominio.

ESCO no aporta trayectorias: interpreta las ocupaciones para posibilitar el análisis de transiciones. Sobre el integrado test+val, `matched_code` cruza **directamente** con `occupations.code` en 2.855 de los 2.873 códigos distintos, o sea el **99,4 % de los _códigos_**; sobre filas eso deja **348.263 experiencias emparejadas `ok`, el 92,5 % de las 376.567**. Los dos porcentajes son ciertos y no se pueden intercambiar: el 99,4 % mide cuántos oficios de ESCO quedaron cubiertos y el 92,5 % cuánto pesa esa cobertura en la `X`.

Las 28.304 filas sin cobertura se reparten en dos estados que se suelen confundir:

| Estado | Filas | Qué es | De dónde sale el código |
|---|---|---|---|
| `unknown` | 25.805 | sin coincidencia en ESCO | ninguno: `occupation_code` queda vacío y se levanta la bandera `es_unknown_ocupacion` |
| `rescatado` | 2.499 | llegó con `matched_code` pero sin código utilizable | **se rescata en la fase 4, no aquí**: `transformacion.fusionar_rescatado` recorta el prefijo ISCO de 4 dígitos y recupera 3 códigos |

Por eso las filas sin `occupation_code` (**28.304**) son más que las `es_unknown_ocupacion` (**25.805**): la diferencia son exactamente las 2.499 rescatadas, que en el CSV limpio todavía no tienen código. Quien solo lea el segundo número se queda 2.499 filas sin explicar.

### Competencias ESCO: qué significa y qué no

Las 6 columnas de competencias responden "**cuántas competencias esenciales exige el oficio que esta persona ejercía**", no "cuántas sabe". ESCO describe requisitos de un cargo; el dato de skills de un individuo no existe en ninguna fuente y se **atribuye por el puesto que ocupaba**. Toda lectura debe mantener esa distinción: *"este cargo exige N competencias"*, nunca *"esta persona sabe N cosas"`.

| Columna | Significado |
|---|---|
| `saber_skills` | `ok` (92,5 %) con oficio clasificado · `no_clasificado` (7,5 %) sin oficio. En `no_clasificado` los contadores quedan **vacíos, nunca 0**: un 0 afirmaría que el cargo no exige ninguna competencia, lo cual es falso |
| `n_skills_essential` | Total de competencias `essential` del oficio (mediana 20, máximo 99) |
| `n_skills_competence` / `n_skills_knowledge` | El total separado en *saber hacer* / *saber* |
| `n_skills_sin_tipo` | Bucket de las 39 relaciones que la fuente entrega sin `skillType`; existe para que los tres anteriores sumen el total |
| `veces_ese_oficio` | Cuántas experiencias tiene esta persona en **este** oficio. Resuelve la reincidencia: quien repite el mismo cargo 19 veces tiene 19 filas con `veces_ese_oficio = 19`, y sus competencias no se repiten |

Solo se usan las relaciones `essential` (67.600 de 126.051): las `optional` son habilidades de nivelación, no el piso del cargo, y sumarlas volvería el conteo interpretable.

**Dónde viven los nombres.** La fuente normalizada de perfiles es `data/03_processed/competencias_por_oficio.csv`, una tabla con **una fila por oficio**: 3.039 filas, 5 columnas y 11.378 habilidades distintas agrupadas en `skills`, `knowledge` y `sin_tipo`. `unificar_competencias_empleos.py` copia esas tres listas a `empleos_con_competencias.csv` mediante una unión N:1 por `occupation_code`; así, las etapas actuales pueden leer el perfil directamente sin modificar los CSV originales ni multiplicar filas.

Esa columna es la **regla de guardado, no la de lectura**: para mostrar el perfil de un cargo se agrupa por `occupation_code` y sale una línea con todas sus competencias. Es lo que hace `indicadores.perfil_persona()`, que arma la trayectoria completa de una persona (educación, cargos, periodos y las competencias que exigía cada contrato). `indicadores.salto_competencias()` mide el solapamiento entre las competencias de dos contratos consecutivos.

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
| `competencias_por_oficio.csv` | — | **3.039 × 5** | Tabla agrupada de competencias ESCO: 1 fila = 1 oficio, con `skills`, `knowledge` y `sin_tipo` separados por `|` (`generar_competencias.py`) |
| `empleos_con_competencias.csv` (integrado enriquecido) | 376.567 × 20 | **376.567 × 20** | Unión N:1 por `occupation_code`; conserva las listas de competencias |
| `empleos_con_competencias_limpio.csv` (integrado enriquecido) | 376.567 × 20 | **376.567 × 23** |  Pipeline en 7 fases: 0 filas con fechas futuras en test+val (MCAR) + 3 banderas `es_*` + perfiles de competencias |
| `empleos_con_competencias_limpio_sin_outliers.csv` | 376.567 × 23 | 341.090 × 23 | Variante enriquecida sin cola larga (`dur_Q ≥ 25`, IQR de Tukey): **−35.477 filas (−9,4 %)**. En personas el efecto es bastante menor: de 71.061 personas con cola larga, **69.182** conservan al menos una experiencia y solo **1.879** desaparecen por completo (−2,6 %) |

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
│       ├── competencias_por_oficio.csv  # 3.039 × 5 (1 fila = 1 oficio)
│       ├── empleos_con_competencias.csv        # 376.567 × 20 (entrada enriquecida)
│       ├── empleos_con_competencias_limpio.csv # 376.567 × 23 (limpio final)
│       └── empleos_con_competencias_limpio_sin_outliers.csv # 341.090 × 23
├── logs/                           # bitácoras de ejecución (solo en disco, no versionadas)
├── notebooks/                      # COMPRENSION/EXPLORACION — unidad por fase
│   ├── 1.0_comprension_negocio.md         # acta de constitución analítica (sesión 1)
│   ├── 2.0_EDA_y_seleccion.ipynb          # fuentes, carga defensiva, EDA, API ESCO (sesión 2)
│   ├── 3.0_preprocesamiento.ipynb         # pipeline de limpieza en 7 fases + validación (sesión 3)
│   ├── 4.0_transformacion.ipynb           # codificación ordinal/one-hot + escalado + PCA (sesión 4, con cola)
│   ├── 4.1_transformacion_sin_outliers.ipynb  # ídem sobre la variante sin cola larga
│   └── ENTREGAMINERIA.pdf                 # informe de entrega (marco KDD–CRISP-DM)
└── src/                            # CODIGO REUTILIZABLE
    ├── src.md                      # guía técnica de scripts, módulos y notebooks
    ├── filtro/                     # TRANSFORMACION (insumos) — análisis reutilizable
    │   ├── filtros.py              # selecciones: nivel, grupo ISCO, ocupación, periodo, vigencia
    │   └── indicadores.py          # duración, IQR, transiciones, brechas, crosstabs, banderas,
    │                               #   perfil de competencias por persona, salto de competencias
    ├── limpieza/                   # PREPROCESAMIENTO/PREPARACION
    │   ├── limpiar_datos.py        # data/01_raw/ → data/02_interim/ (limpieza de fuentes)
    │   ├── integrar_empleos.py      # unión test+val + ESCO → data/03_processed/empleos.csv
    │   ├── generar_competencias.py # ESCO → competencias_por_oficio.csv (tabla normalizada)
    │   ├── limpiar_empleos.py      # flujo histórico del integrado de 17 columnas
    │   ├── unificar_competencias_empleos.py # unión N:1 de perfiles ESCO
    │   ├── limpiar_empleos_con_competencias.py # valida y limpia el dataset enriquecido
    │   ├── dividir_competencias_por_outliers.py # limpio enriquecido → variante IQR
    │   └── dividir_por_outliers.py # flujo histórico de comparación
    └── transformacion/             # TRANSFORMACION (sesión 4) — la X
        ├── transformacion.py       # features, codificación, escalado, ensamble de X_final
        └── diagnostico.py          # Tukey, aporte a la distancia, PCA, comprobaciones del cruce
```

Reglas de oro: originales intocables · derivados regenerables (pipelines **deterministas**) · rutas relativas (la raíz se resuelve buscando `data/` hacia arriba) · salida del cruce única en **CSV** · toda decisión de negocio documentada en bitácora (`logs/`).

## Cómo orientarse en el repositorio

El proyecto se puede leer en tres capas:

1. **Datos:** `data/01_raw/` contiene las fuentes originales; `data/02_interim/`
   contiene esas fuentes limpias; `data/03_processed/` contiene los productos
   integrados y enriquecidos que se usan en la fase actual.
2. **Evidencia:** `notebooks/` explica y demuestra cada fase. Los notebooks no
   son la fuente principal de la lógica: muestran decisiones, resultados y
   validaciones reproducibles.
3. **Código:** `src/` contiene la lógica reutilizable. `src/limpieza/` prepara
   los CSV, `src/filtro/` contiene filtros e indicadores para el análisis de
   trayectorias y competencias, y `src/transformacion/` convierte los datos
   enriquecidos en una matriz numérica `X`.

### Flujo canónico vigente

La ruta que debe seguir un usuario nuevo es:

```text
01_raw
  ↓ limpiar_datos.py
02_interim
  ↓ integrar_empleos.py + generar_competencias.py
empleos.csv + competencias_por_oficio.csv
  ↓ unificar_competencias_empleos.py
empleos_con_competencias.csv
  ↓ limpiar_empleos_con_competencias.py
empleos_con_competencias_limpio.csv
  ├─ conservar cola larga → 4.0_transformacion.ipynb
  └─ dividir_competencias_por_outliers.py
       → empleos_con_competencias_limpio_sin_outliers.csv
       → 4.1_transformacion_sin_outliers.ipynb
```

`empleos.csv`, `empleos_limpio.csv` y `dividir_por_outliers.py` pertenecen al
flujo histórico de limpieza sin las listas de competencias. Se conservan como
referencia y trazabilidad, pero el flujo canónico actual para preparar la `X`
es el que usa `empleos_con_competencias*.csv`.
El archivo auxiliar `empleos_limpio_con_competencias.csv`, que puede producir
el script de unificación por compatibilidad con el trabajo anterior, tampoco
es una entrada del flujo canónico actual; la salida oficial se regenera desde
`empleos_con_competencias.csv`.

### Qué representa cada salida

| Salida | Propósito en la fase actual |
|---|---|
| `empleos.csv` | Integrado histórico de JobHop test + val con atributos ESCO y contadores |
| `competencias_por_oficio.csv` | Perfil normalizado de competencias, una fila por oficio |
| `empleos_con_competencias.csv` | Entrada canónica enriquecida; conserva listas `skills`, `knowledge` y `sin_tipo` |
| `empleos_con_competencias_limpio.csv` | Dataset enriquecido validado, con banderas de calidad y vigencia |
| `empleos_con_competencias_limpio_sin_outliers.csv` | Misma estructura, excluyendo la cola larga según IQR de duración |
| `X` de 4.0/4.1 | Representación numérica de trabajo para IA; se construye en memoria y no inicia todavía minería |

La fase actual termina cuando ambas variantes enriquecidas están validadas y
la transformación produce una `X` numérica sin nulos ni columnas de texto.
Todavía no se crea `Sₚ`, no se selecciona una técnica de minería y no se
interpretan patrones: esas decisiones permanecen deliberadamente fuera del
alcance de este corte.

## Metodología (KDD / CRISP-DM)

| # | Fase KDD | Fase CRISP-DM | Estado | Entregable |
|---|---|---|---|---|
| 1 | **Selección** | Comprensión del negocio | ✅ **HECHO** | Acta `1.0`; objetivo, preguntas y fuentes (JobHop v2 + ESCO v1.2.1) |
| 2 | **Preprocesamiento** | Comprensión y preparación de datos | ✅ **HECHO** | Fuentes limpias (`02_interim`); integrado validado; `empleos_con_competencias.csv` (20 columnas), derivado limpio con 23 columnas y variante sin cola larga; **transformación a features** (ordinal/one-hot/escalado/PCA) en `4.0` y `4.1` — competencias ESCO incorporadas a la `X` en la sección 2.5 (`docs/SKILLS.md` §10) |
| 3 | **Transformación** | Preparación (hacia modelado) | ✅ **HECHO** (features listas) | Codificación y escalado en `src/transformacion/`, ejecutados y evidenciados por `notebooks/4.x`, **competencias ESCO incluidas** (sección 2.5); resta la construcción de secuencias por persona (`Sₚ`); insumos listos en `src/filtro/` |
| 4 | **Minería** | Modelado | ⏳ **PENDIENTE** | Técnica de minería de secuencias/transiciones a seleccionar |
| 5 | **Interpretación y evaluación** | Evaluación | ⏳ **PENDIENTE** | Patrones juzgados: frecuentes, consistentes, interpretables, útiles |
| 6 | **Conocimiento** | Despliegue | ⏳ **PENDIENTE** | Caracterización de patrones e informe final |

El marco rector completo (mapeo KDD ↔ CRISP-DM por corte, criterios de éxito, cifras de auditoría) está en `METODOLOGIA_KDD_CRISPDM.md` (solo en disco, por decisión acordada). La alineación por entregable y las referencias cruzadas entre unidad, fase y sesión están en la sección §6 del acta `1.0`.

## Lo que se hizo en el código

**`src/limpieza/limpiar_datos.py`** — limpieza de fuentes: `data/01_raw/` → `data/02_interim/`.
Limpia las 3 particiones CSV de JobHop (`train`/`test`/`val`: elimina filas sin `start_date` y duplicados, ordena por persona/trimestre) y los cuatro CSV de ESCO en `ESCO/` + `SKILLS/` (duplicados por `code`/`conceptUri`, columnas 100 % nulas). Función `validar(...)` audita cada archivo; bitácora de cambios por ejecución.

**`src/limpieza/integrar_empleos.py`** - integración: une las particiones limpias **test + val** de JobHop (train excluido), cruza `matched_code` con ESCO (`emparejado`: `ok` / `rescatado` / `unknown`), agrega los contadores de competencias ESCO y crea `data/03_processed/empleos.csv` (376.567 × 17, 71.061 personas).

**`src/limpieza/generar_competencias.py`** — construye `competencias_por_oficio.csv`, una tabla agrupada (**una fila por oficio**, 3.039 × 5). Las competencias se distribuyen en `skills`, `knowledge` y `sin_tipo`, con nombres separados por `|`. Esta tabla es la fuente normalizada; después `unificar_competencias_empleos.py` copia las listas a la entrada canónica enriquecida mediante una unión N:1, sin modificar los CSV originales ni multiplicar el grano del dataset. Resuelve el salto `code` → `occupationUri` (UUID) del puente ESCO y valida contra los contadores del integrado disponible (`empleos.csv` o, si aún no se regeneró, `empleos_con_competencias.csv`) antes de escribir.

**`src/limpieza/unificar_competencias_empleos.py`** — crea la entrada enriquecida independiente `empleos_con_competencias.csv` mediante una unión `left` por `occupation_code`. Conserva intactos los archivos originales, sus filas y sus nombres de columnas; solo agrega `skills`, `knowledge` y `sin_tipo`. Las filas sin oficio clasificado permanecen sin competencias. La limpieza posterior y las banderas `es_*` se regeneran con `limpiar_empleos_con_competencias.py`.

**`src/limpieza/limpiar_empleos.py`** — clase `LimpiadorEmpleos` con **7 fases** (`fase1_diagnostico` … `fase7_exportar`) sobre el integrado histórico `empleos.csv` (CSV). Cada fase termina en un `assert` contra `EXPECTED` (umbrales de aceptación, criterio "funciones reutilizables + pruebas automáticas" de la rúbrica de la sesión 3). Para el flujo vigente enriquecido se utiliza `limpiar_empleos_con_competencias.py`:
1. Diagnóstico (nada se toca) → 2. Duplicados (0 exactos; claves cortas = pluriempleo, se conservan) → 3. Categorías y caso MNAR (`'None'` y celdas vacías → `'No reportado'`) → 4. Faltantes por bandera (MAR + censura, sin imputar) → 5. Outliers IQR de Tukey + 0 fechas futuras en test+val (MCAR) → 6. Validación 6/6 → 7. Exportar CSV + bitácora.

**`src/limpieza/dividir_competencias_por_outliers.py`** — genera la variante enriquecida **sin cola larga** (`empleos_con_competencias_limpio_sin_outliers.csv`) con la misma convención IQR de la fase 5 (`dur_Q ≥ 25`), para comparar el impacto de la cola larga antes de elegir la técnica de minería. `dividir_por_outliers.py` se conserva como flujo histórico del integrado sin skills.

**`src/filtro/filtros.py` y `src/filtro/indicadores.py`** — biblioteca reutilizable de análisis: filtros (nivel educativo, grupo ISCO, ocupación, periodo, vigentes) e indicadores (duración trimestral inclusiva, distribución, medianas por grupo/nivel, crosstabs, transiciones consecutivas, proporción que conserva el grupo, primera→segunda ocupación, brechas entre empleos, personas solapadas, resumen de banderas). Sobre la tabla de competencias añaden `cargar_competencias()`, `perfil_persona()` (trayectoria de una persona con las competencias que exigía cada contrato) y `salto_competencias()` (índice de Jaccard entre contratos consecutivos). En este corte se documentan como insumos reutilizables; no se usan todavía para construir `Sₚ`.

**`src/transformacion/transformacion.py` y `src/transformacion/diagnostico.py`** — la fase de **transformación** (sesión 4) como código, no como cuaderno. `transformacion.py` arma la `X` en orden: carga la versión enriquecida pedida, fusiona el código recuperado de las filas rescatadas, deriva los ordinales (trimestre, duración, nivel educativo), recorta el universo sin dato de competencias midiendo el costo, toma la submuestra, codifica (one-hot + presencia de perfiles ESCO + las banderas que aportan) y escala por grupos. `diagnostico.py` produce las medidas que **justifican** esas decisiones: Tukey, el aporte de cada columna a la distancia euclidea, el PCA y las comprobaciones del cruce con ESCO. Ninguna de las dos imprime: devuelven los datos y los cuadernos los formatean, porque el texto que las justifica es parte del entregable. Con la semilla documentada, el módulo y los notebooks 4.0/4.1 producen `X` de 2.328 y 2.329 columnas respectivamente; esas dimensiones tienen una comprobación explícita en `FORMAS_X`.

**`notebooks/`** — reproducen y exhiben cada fase con evidencia impresa y outputs persistidos: `1.0` (acta/diseño), `2.0` (selección de fuentes + carga defensiva + EDA + diagnóstico de calidad + API ESCO), `3.0` (pipeline de limpieza ejecutado en vivo, validación 6/6, bitácora, división con/sin cola larga). De la **sesión 4 (transformación)**, `4.0_transformacion.ipynb` (sobre `empleos_con_competencias_limpio.csv`, con cola larga) y `4.1_transformacion_sin_outliers.ipynb` (sobre la variante sin cola larga) comparten un pipeline parametrizado por `VERSION` (una celda de configuración elige el CSV). El cálculo no vive en los cuadernos sino en `src/transformacion/`: los dos importan el mismo módulo y sus 18 celdas de código difieren **en una sola línea**, la del `VERSION`. Los cuadernos quedan como narrativa y evidencia;

1. **Justificación por categoría** de por qué cada columna es ordinal (jerarquía real: fechas `Qn AAAA`, `university_level`, `isco_level`) o one-hot (sin orden: `emparejado`, `occupation_code`, banderas `es_*`) — con auditoría de redundancias (1:1, prefijos, constantes) que descarta `matched_code`, `occupation_label`, `isco_group*`.
2. **Codificación:** ordinal `año×4+trimestre` + `KBinsDiscretizer` (quantile, demo) para fechas; mapeo manual 0–4 para educación; `get_dummies` (demo) y `OneHotEncoder` sparse (producción) para las nominales; banderas como 0/1 enteros.
3. **Escalado con auditoría de outliers (Tukey):** `RobustScaler` para fechas y `dur_q` (colas reales censuradas), `MinMaxScaler` para educación (rango acotado) y `StandardScaler` mostrado y descartado; **no se escalan dummies ni banderas**; `fit` solo sobre la muestra (sin fuga de datos).
4. **PCA auditado y descartado (sección 4.3):** correlaciones + varianza acumulada muestran que las numéricas son ~3 dimensiones lineales (`dur_q = end − start + 1`) y que las dummies no entran a PCA por diseño; no comprime aquí.
5. **Dos banderas constantes quedan fuera de la `X`:** de las tres banderas del dataset solo entra `es_vigente`. `es_unknown_ocupacion` y `es_rescatado` son `True` exactamente cuando `occupation_code` está vacío, y el recorte del universo se lleva esas filas, así que en la `X` son `False` por construcción: una columna constante colapsa a 0 en la distancia y **engaña la importancia de variables**. No es información perdida —sigue en el dataset y en qué filas quedaron—; es la consecuencia lógica del recorte. `codificar()` lleva un `assert` que avisa si alguna vez dejaran de ser constantes, para que el cambio no pase inadvertido.
6. **Las dos banderas se quedan también en el dataset.** Se evaluó borrarlas de ahí y no compensa: no se pierde nada, porque `es_unknown_ocupacion` es exactamente `emparejado == 'unknown'` y `es_rescatado` exactamente `emparejado == 'rescatado'` (medido en las 376.567 filas), y porque `isco_group` está vacío en las 25.805 filas `unknown` y lleno en las 2.499 `rescatado`, así que la distinción entre «sin oficio y sin área» y «sin oficio exacto pero con área» se sigue viendo sin ellas. Lo que sí costaría es el preprocesamiento entero: el dataset pasa de **20 a 18 columnas** y hay que rehacer los tres CSV y la verificación de `limpiar_empleos.py` L440-442, que usa las dos banderas como instrumento. Coste cero, además: en el dataset no son ruido.
7. **La forma de la `X` está vigilada:** `armar_X()` no devuelve nada sin comprobar cuatro cosas —0 nulos, 0 columnas no numéricas, una dummy por oficio presente en la submuestra, y la forma contra `FORMAS_X` (2.328 en `4.0`, 2.329 en `4.1`)—. `version` es un parámetro obligatorio, sin valor por defecto, para que no se pueda llamar a la función sin comprobar. Las 2.316 columnas de oficios **no son un número fijo del código**: salen de `get_dummies` sobre la submuestra, así que un cambio de codificación las movería y todas las cifras citadas quedarían viejas sin que nada fallara. El mensaje del `assert` obliga a corregir este README y `docs/SKILLS.md` en el mismo commit.

Se ejecutan de principio a fin sin errores (núcleo `python3` 3.14.7) y entregan una **X** numérica finita (0 nulos, 0 columnas no numéricas) lista para minería.

## Decisiones técnicas clave

- **Salida única en CSV para el cruce:** `empleos.csv`, `empleos_con_competencias.csv` y sus dos derivados enriquecidos se mantienen exclusivamente en CSV (`data/03_processed/`), regenerables desde los scripts. Los CSV no se versionan por tamaño y la estructura de la carpeta se conserva en git con `.gitkeep`.
- **Competencias normalizadas y disponibles en el dataset canónico:** `competencias_por_oficio.csv` conserva una fila por oficio como fuente de verdad. Las listas se copian a `empleos_con_competencias.csv` y sus derivados mediante una unión N:1 por `occupation_code`; los CSV originales no se modifican y el grano sigue siendo una fila por experiencia.
- **Una fila por oficio en la fuente normalizada:** cada `occupation_code` aparece una sola vez en `competencias_por_oficio.csv`; en los datasets enriquecidos las listas `skills`, `knowledge` y `sin_tipo` se repiten como atributo del oficio para que cada experiencia sea autosuficiente. `indicadores.cargar_competencias()` permite expandirlas a formato largo cuando una consulta lo necesita.
- **`n_skills_essential` es caché verificada, no un dato independiente:** se conserva (está dentro de la `X` de `4.0`/`4.1` y no cuesta nada) pero es derivable de la tabla de competencias —se comprobó que la reproduce en los 2.855 oficios, con 0 discrepancias—. `generar_competencias.py` lo contrasta en cada corrida: si el puente ESCO se rompiera, el pipeline cortaría con diagnóstico en vez de dejar dos números distintos circulando. La redundancia no se elimina, se vigila.
- **La tabla de competencias es un superconjunto:** describe a ESCO (3.039 oficios, 3.693 competencias), no a JobHop (2.855 oficios). Los 184 oficios que nadie usó están a propósito, para poder ampliar sin volver a la fuente.
- **CSV procesados también en Google Drive:** el integrado (`empleos.csv`), la versión limpia con outliers (`empleos_con_competencias_limpio.csv`) y la versión limpia sin outliers (`empleos_con_competencias_limpio_sin_outliers.csv`) se comparten en: https://drive.google.com/file/d/1NH-ibBT_wsehhnQNOKCpGJDx1UPmG1sC/view
  El enlace incluye también `competencias_por_oficio.csv` (5,02 MiB), que es la fuente normalizada de los nombres. Los CSV enriquecidos contienen copias de las listas para el trabajo fila a fila; la tabla aparte permite auditar y regenerar el enriquecimiento.
- **Banderas en lugar de imputación:** la ausencia es informativa; no se usa `fillna`. Nulos estructurales conservados con banderas: `es_unknown_ocupacion` (25.805), `es_rescatado` (2.499) y re-categorización de `'None'`/celdas vacías → `'No reportado'` (42.807). De las tres, solo `es_vigente` entra en la `X`: las otras dos quedan constantes tras el recorte del universo y se excluyen a propósito (punto 5 de la transformación).
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
| D2 | Empleos simultáneos / pluriempleo (18.749 filas repetidas) | ¿Cómo se concreta la regla de negocio "transición" en secuencias con pluriempleo conservado? |
| D3 | ~~Enriquecimiento temático futuro~~ | **RESUELTO**: las competencias ESCO ya están agregadas al integrado como 6 columnas de contadores (`saber_skills`, `n_skills_essential`, `n_skills_competence`, `n_skills_knowledge`, `n_skills_sin_tipo`, `veces_ese_oficio`). `greenShare` se descartó por no responder a la pregunta de investigación |
| D4 | Técnica de minería y destino de las secuencias | ¿Qué técnica y dónde se persiste `Sₚ` (misma regla: CSV + original intocable)? |

## Verificación del resultado

- **Asserts por fase (nivel "Excepcional"):** `limpiar_empleos.py` valida cada fase contra cantidades verificadas de la fuente (`EXPECTED`), con tabla de umbrales 10/10 y bitácora de trazabilidad en `logs/`. Cuatro de esos umbrales son de las competencias: que el contador esté vacío exactamente cuando `saber_skills != 'ok'`, que nunca valga 0, que los tres buckets sumen el total, y que `veces_ese_oficio ≥ 1`.
- **Cuadernos de diagnóstico:** `2.0`, `3.0`, `4.0` y `4.1` se ejecutan de principio a fin sin errores y reproducen los scripts con evidencia impresa (nbclient con núcleo `python3`).
- **Las dos fuentes de las competencias no pueden separarse:** `generar_competencias.py` exige que contar las filas de `competencias_por_oficio.csv` por oficio reproduzca los cuatro contadores (`n_skills_essential`, `n_skills_competence`, `n_skills_knowledge`, `n_skills_sin_tipo`) de `empleos.csv` — **0 discrepancias en los 2.855 oficios**, y 0 pares (oficio, competencia) repetidos. `limpiar_empleos_con_competencias.py` vuelve a validar que las listas copiadas a cada experiencia cierren con sus contadores y que los perfiles no clasificados conserven los contadores vacíos.
- **Sanidad de la matriz final (4.x):** `X_final` sin nulos y sin columnas no numéricas; mediana ≈ 0 en las robust, extremos 0/1 en la minmax; auditoría de outliers y varianza de PCA impresas en vivo.
- **Comparación con/sin cola larga:** `dividir_por_outliers.py` cruza ambas versiones (filas, personas, mediana/máximo de `dur_Q`, vigentes) para cuantificar el impacto antes de elegir la técnica de minería.
- **Idempotencia/regeneración:** los pipelines son deterministas (sin aleatoriedad) y regenerables desde `data/01_raw/`; cada cifra del informe se reproduce con los comandos de la sección siguiente.
- **API pública (sesión 2):** `2.0` §5b intenta la consulta REST de ESCO sobre un `conceptUri` real; en redes sin acceso reporta el fallback con las URLs oficiales (la respuesta JSON viva requiere red que alcance `data.europa.eu/esco/api`).

## Cómo ejecutar (reproducibilidad)

```bash
python -m pip install -r requirements.txt

python src/limpieza/limpiar_datos.py         # fuentes → data/02_interim/
python src/limpieza/integrar_empleos.py      # unión test+val + ESCO + competencias → empleos.csv
python src/limpieza/generar_competencias.py  # ESCO → competencias_por_oficio.csv (+ contraste)
python src/limpieza/unificar_competencias_empleos.py
python src/limpieza/limpiar_empleos_con_competencias.py
python src/limpieza/dividir_competencias_por_outliers.py
```

Los scripts del bloque canónico son **deterministas y se ejecutan en ese orden**:
`integrar_empleos.py` necesita las fuentes limpias; `generar_competencias.py`
construye el perfil normalizado y lo contrasta contra el integrado;
`unificar_competencias_empleos.py` crea una copia enriquecida sin tocar los
originales; `limpiar_empleos_con_competencias.py` añade las banderas y valida
contadores/listas; finalmente `dividir_competencias_por_outliers.py` crea la
segunda variante conservando exactamente el mismo esquema. El flujo histórico
`limpiar_empleos.py` → `dividir_por_outliers.py` no es requisito para generar las
salidas canónicas enriquecidas.

`generar_competencias.py` va **después** de `integrar_empleos.py` porque su
bloque de validación contrasta la tabla contra los contadores del integrado
disponible (`empleos.csv` o `empleos_con_competencias.csv`);
si ese archivo no estuviera, genera la tabla igual y **avisa en pantalla** de que
el contraste se omitió (nunca lo omite en silencio).

Los scripts resuelven la raíz del proyecto buscando hacia arriba la carpeta `data/`, por lo que se ejecutan desde cualquier directorio del repo (rutas relativas). Requiere **Python 3** (referencia: `.python-version` = 3.14.7, documento `requirements.txt`) y las dependencias declaradas (pandas, pyarrow, matplotlib, **scikit-learn** para la transformación `4.x`, nbconvert, ipykernel, jupyter-client).

**Regeneración de derivados (cierre del ciclo):**
- `data/02_interim/**` y los CSV de `data/03_processed/` se regeneran con los scripts anteriores.
- `data/03_processed/empleos.csv` es el integrado histórico; la entrada canónica para transformación es `empleos_con_competencias.csv`, que se regenera con `unificar_competencias_empleos.py` sin sobrescribir los CSV originales.
- El repositorio versiona `data/01_raw/` y `data/02_interim/` completos; no versiona los CSV del cruce por tamaño.

## Estado actual y siguientes pasos

**Estado:** la limpieza de fuentes y la integración están verificadas. La base canónica enriquecida para las etapas posteriores es `empleos_con_competencias.csv`; sobre ella se valida y genera `empleos_con_competencias_limpio.csv` (376.567 filas × 23 columnas) y su variante `empleos_con_competencias_limpio_sin_outliers.csv` (341.090 × 23). Las columnas `skills`, `knowledge` y `sin_tipo` conservan los nombres de las competencias exigidas por cada oficio, mientras que los contadores (`n_skills_*`) y `veces_ese_oficio` se usan en la representación numérica y comportamental. La transformación en `src/transformacion/` valida la presencia de los perfiles de skills y deriva indicadores binarios reproducibles antes de formar la `X`. La construcción de secuencias por persona (`Sₚ`), la minería y la evaluación siguen pendientes.

### Cumplimiento del propósito de esta fase

- **Preparación para IA:** las dos variantes limpias conservan una fila por experiencia,
  atributos laborales, contadores ESCO, listas de competencias y banderas de calidad.
- **Integridad de las fuentes:** `data/01_raw/` y los CSV de entrada no se
  sobrescriben; cada etapa escribe un derivado identificable en `data/02_interim/`
  o `data/03_processed/`.
- **Uso real de ESCO:** las listas `skills`, `knowledge` y `sin_tipo` se validan
  contra sus contadores; la transformación deriva `tiene_skills`,
  `tiene_knowledge` y `tiene_sin_tipo` antes de construir `X`.
- **Comparación metodológica:** se conservan una versión con la cola larga y otra
  sin outliers para comparar sus efectos, sin elegir todavía una técnica de minería.
- **Límite intencional:** esta fase termina en datasets validados y una
  representación numérica de trabajo. No crea secuencias `Sₚ`, no entrena modelos,
  no extrae patrones y no presenta conclusiones causales.

**Fuera del alcance actual:** la construcción del dataset de secuencias por persona
(`Sₚ`), la selección de técnica de minería, el entrenamiento, la evaluación y la
interpretación se reservan para una fase posterior. `src/filtro/` contiene
funciones reutilizables que servirán como insumo, pero no se presentan aquí como
una etapa ya ejecutada.

## Limitaciones

- **Sin causalidad:** se describen asociaciones y patrones; no se demuestra que una característica cause una trayectoria.
- **Alcance geográfico:** los datos provienen de Flandes, Bélgica; los hallazgos no describen un mercado laboral colombiano.
- **ESCO solo enriquece:** no aporta trayectorias; sin ella, `matched_code` no es interpretable.
- **Censura y ausencia sin imputar:** `Present` y `unknown` se conservan con banderas; su rol en la minería está en discusión (D1).
- **Pluriempleo conservado:** sobre la llave natural `(persona, inicio, fin)` hay **18.749 filas de más** —el mismo periodo repetido, por un cargo simultáneo o por una transición real dentro del mismo trimestre—, que equivalen a **357.818 periodos distintos**. El nombre "clave corta" es engañoso: lo que se cuenta son filas de más dentro de un grupo, no grupos; un grupo no puede estar "corto". Se conservan todas, y la regla de "transición" se define en la fase de transformación (D2).
- **Técnica de minería por definir:** se fija tras explorar la estructura final de las secuencias.
- **API ESCO dependiente de red:** la demostración en vivo (§5b de `2.0`) requiere acceso a `data.europa.eu/esco/api` desde la máquina que la ejecute.

## Ruta de lectura sugerida

1. **Este README** — panorama, estado, metodología y repro por comandos.
2. `METODOLOGIA_KDD_CRISPDM.md` (solo en disco) — marco rector y plan de acción fase a fase.
3. `notebooks/1.0_comprension_negocio.md` — acta de constitución analítica.
4. `notebooks/2.0_EDA_y_seleccion.ipynb` — fuentes, carga defensiva, EDA y diagnóstico.
5. `notebooks/3.0_preprocesamiento.ipynb` — pipeline de limpieza, validación y bitácora.
6. `notebooks/4.0_transformacion.ipynb` y `4.1_transformacion_sin_outliers.ipynb` — transformación a features (codificación, escalado, PCA) en ambas versiones.
7. **Código:** `src/limpieza/` (pipelines), `src/filtro/` (análisis reutilizable) y `src/transformacion/` (la `X` de la sesión 4).

## Referencias

- Dataset JobHop v2: https://huggingface.co/datasets/aida-ugent/JobHop
- Artículo: *JobHop v2: A Large-Scale Career Trajectory Dataset from Unstructured Resumes* (arXiv).
- Taxonomía ESCO v1.2.1 (descarga): https://esco.ec.europa.eu/es/use-esco/download
- API de ESCO (sesión 2): https://data.europa.eu/esco/api