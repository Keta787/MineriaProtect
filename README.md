# MineríaProtect

Análisis de minería de trayectorias laborales sobre el dataset **JobHop v2** (`aida-ugent/JobHop`, Hugging Face), que contiene trayectorias profesionales reconstruidas a partir de hojas de vida (resúmenes curriculares) no estructuradas.

> **Nota sobre el origen:** los datos principales de JobHop provienen de **Flandes, Bélgica** (conjunto internacional), no de Colombia. El país no es el objetivo del proyecto: el objetivo son las **trayectorias laborales**. El Observatorio Laboral para la Educación (OLE) colombiano puede quedar como contexto o fuente complementaria, no como parte obligatoria.

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

El proyecto se apoya en tres fuentes con roles distintos:

```text
JobHop v2 (fuente principal — trayectorias)
   ↓
códigos ocupacionales (matched_code)
   ↓
ESCO (fuente de enriquecimiento — significado de la ocupación)
   ↓
minería de trayectorias

OLE (fuente contextual, opcional) → contexto colombiano
```

### 1. JobHop v2 — fuente principal (trayectorias)

Dataset original de trayectorias laborales. Columnas:

| Columna | Descripción |
| ------- | ----------- |
| `resume_id` | Identificador de la persona/currículum |
| `matched_code` | Código de ocupación (taxonomía ESCO) |
| `start_date` | Trimestre de inicio (ej. `Q1 2000`) |
| `end_date` | Trimestre de fin (ej. `Q4 2007` o `Present`) |
| `university_level` | Nivel de formación (ej. `Master`, `Bachelor`) |

Una misma `resume_id` puede tener varias filas: cada una es una experiencia laboral distinta de la misma persona. Encadenadas en orden forman la trayectoria profesional.

### 2. ESCO — fuente de enriquecimiento (significado de la ocupación)

- Fuente oficial (descarga): https://esco.ec.europa.eu/es/use-esco/download
- **Versión incorporada:** ESCO v1.2.1 (clasificación en inglés), archivos CSV en `data/original/ESCO/`.
- **Por qué se agrega:** JobHop trae códigos de ocupación (`matched_code`), pero se necesita información interpretable sobre esas ocupaciones. ESCO relaciona los códigos con nombre, descripción, clasificación ocupacional, grupos ocupacionales, relación con ISCO y competencias.
- No se agrega "por tener dos bases de datos", sino para **enriquecer las experiencias laborales de JobHop y hacer posible un análisis más significativo de las transiciones**.

> **Estado del cruce (verificado):** `matched_code` cruza **directamente** con `occupations.code`: 2.966 de 2.983 códigos únicos (99,4%), que cubren ≈92% de las filas. Los 17 restantes incluyen `unknown` y códigos mapeables al menos a nivel de grupo ISCO-08 (primeros 4 dígitos).

> **Sobre las URIs de ESCO:** los identificadores tipo `http://data.europa.eu/esco/...` son *identificadores* (Linked Data), no el contenido. El análisis no necesita resolverlos: los CSV ya traen los atributos (`preferredLabel`, `description`, `altLabels`, etc.) y las relaciones se cruzan por esos identificadores.

### 3. OLE Colombia — fuente contextual (opcional)

El **Observatorio Laboral para la Educación (OLE)** del Ministerio de Educación: https://ole.mineducacion.gov.co/

Proporciona información agregada del contexto colombiano (graduados, programas académicos, vinculación laboral, ingresos, seguimiento de cohortes e indicadores laborales). Solo se considera como **contexto o fuente complementaria**; no es obligatorio ni se usa para reconstruir trayectorias individuales (limitaciones de granularidad y protección de datos). **No se puede unir a JobHop a nivel individual.**

## Estructura del proyecto

```text
MineriaProtect/
├── data/
│   ├── original/                  # Fuentes (NUNCA se modifican)
│   │   ├── JobHop_v2_train.parquet
│   │   └── ESCO/                  # occupations_en.csv + ISCOGroups_en.csv (los 2 en uso)
│   ├── limpia/                    # Versiones limpias de fuentes (derivados, se sobrescriben)
│   │   ├── JobHop_v2_train_limpio.parquet
│   │   └── ESCO/                  # *_limpio.csv de los 2 ESCO en uso
│   └── cruce/                     # integrado: empleos.parquet + empleos_limpio.parquet
├── libros/                        # cuadernos (sesión 1-3)
│   ├── Lectura.ipynb              # limpieza de fuentes (reproduce limpiar_datos.py)
│   ├── Diagnostico_Limpieza_Empleos.ipynb   # limpieza del integrado (bloque 4)
│   └── presentacion.ipynb         # en construcción
├── md/                            # documentación
│   ├── AUDITORIA_RAMA_PRUEBA.md   # auditoría y trazabilidad por rama
│   ├── BUENAS_PRACTICAS_CODIGO.md # estándar de código del proyecto
│   └── contexto_sesion3.md        # contexto académico sesión 3
├── script/
│   ├── filtro/                    # (futuro) filtros y visualización de trayectorias
│   ├── limpieza/
│   │   ├── limpiar_datos.py       # limpieza de fuentes (ESCO + JobHop limpio)
│   │   └── limpiar_empleos.py     # limpieza formal del integrado (bloque 4)
│   └── requirements/
│       └── requirements.txt       # dependencias (pandas, pyarrow)
└── .gitignore
```

Reglas de oro del proyecto:

- **Los archivos originales nunca se modifican**: solo se leen.
- **No se vuelve a limpiar una versión limpia/derivada.** `JobHop_v2_train.parquet` ya generó su limpio en un proceso anterior, por eso queda **excluido** del proceso automático.
- El proceso de limpieza es **idempotente**: re-ejecutarlo sobrescribe los archivos de salida con contenido equivalente (no genera duplicados).
- **Salida única en parquet.** El integrado y su limpio solo existen en formato Parquet (ver **Decisiones**).
- Cada decisión de negocio del pipeline vive en un único punto de configuración o está documentada en la bitácora impresa por el propio script.

## Datasets

### JobHop v2 (`aida-ugent/JobHop`)

| Archivo | Descripción |
| ------- | ----------- |
| `data/original/JobHop_v2_train.parquet` | Dataset original (1.594.827 filas) |
| `data/limpia/JobHop_v2_train_limpio.parquet` | Dataset limpio (1.506.445 filas) — derivado previo, no se re-limpió |

Limpieza aplicada en el proceso anterior (derivado previo; verificado en `libros/Lectura.ipynb`, no re-ejecutada): `end_date` nulo → `Present`; filas sin `start_date` eliminadas; duplicados exactos eliminados; orden por persona y trimestre real (`Q1 2000` → clave `(2000, 1)`).

### Taxonomía ESCO v1.2.1 (2 CSV en uso)

| Archivo | Originales | Limpias | Operación clave |
| ------- | ---------- | ------- | --------------- |
| `occupations_en.csv` | 3.043 | 3.039 | −4 filas por `code` duplicado (idénticas salvo `modifiedDate`) |
| `ISCOGroups_en.csv` | 619 | 619 | columna `altLabels` 100% nula eliminada (8 → 7 columnas) |

Solo se conservan los archivos que usa la integración (`occupations` e `ISCOGroups`). El resto de la taxonomía ESCO (skills, relaciones skill-ocupación, greenShare, colecciones, etc.) fue **descartado** del repo en el recorte a 3 datasets; su historial queda en git.

### Integrado de empleos (cruce con ESCO)

| Archivo | Descripción |
| ------- | ----------- |
| `data/cruce/empleos.parquet` | Integrado original (1.506.445 × 11; inmutable) |
| `data/cruce/empleos_limpio.parquet` | Integrado limpio (1.506.434 × 14) — salida del bloque 4 |

Limpieza formal aplicada (`script/limpieza/limpiar_empleos.py`): diagnóstico con asserts por fase, banderas `es_unknown_ocupacion`, `es_rescatado` y `es_vigente`, re-categorización de `'None'` → `'No reportado'`, eliminación de 11 filas con fechas futuras, duración trimestral **inclusiva** y validación contra criterios explícitos. Ver `md/AUDITORIA_RAMA_PRUEBA.md` §13.

## Proceso de limpieza

### Fuentes (`script/limpieza/limpiar_datos.py`)

Reglas generales (reproducidas en `libros/Lectura.ipynb`):

1. Los CSV se leen **como texto** (`dtype=str`) para no perder ceros a la izquierda en los códigos (p. ej. código ISCO `0110` ≠ `110`).
2. Se eliminan las **columnas 100% nulas** (columna sin información no sirve para cruzar).
3. Se normalizan textos: `strip()` (quita espacios que romperían comparaciones en cruces).
4. Se eliminan **duplicados exactos de fila completa** (en la práctica 0; regla defensiva).
5. **Duplicados por llave** (datos de dos publicaciones de ESCO fusionadas):
   - `occupations_en`: −4 filas por `code` (idénticas salvo `modifiedDate`; se conserva la primera).
6. `ISCOGroups_en`: `altLabels` está 100% nula → se elimina (de 8 a 7 columnas).
7. Cada archivo pasa por **validación antes/después**: filas, columnas, nulos críticos, duplicados y las transformaciones aplicadas.

`JobHop_v2_train.parquet` está **excluido** del proceso automático: ya tiene su versión limpia (derivado previo).

Idempotencia verificada: ejecutar el proceso dos veces produce **archivos byte a byte idénticos**.

### Integrado (`script/limpieza/limpiar_empleos.py`)

Pipeline formal del curso en 7 fases: **diagnóstico → duplicados → categorías/banderas → faltantes → outliers → limpieza → validación**. Cada fase emite la bitácora (qué cambió, cuántos, con qué criterio) y cierra con asserts que comparan contra las cantidades verificadas de la fuente. Reproducido en `libros/Diagnostico_Limpieza_Empleos.ipynb`.

## Cómo ejecutar

```bash
python -m pip install -r script/requirements/requirements.txt

python script/limpieza/limpiar_datos.py     # fuentes → data/limpia/
python script/limpieza/limpiar_empleos.py   # integrado → data/cruce/empleos_limpio.parquet
```

Los scripts resuelven la raíz del proyecto buscando hacia arriba la carpeta `data/`, así que se pueden ejecutar desde cualquier directorio dentro del repo.

## Notebooks (`libros/`)

| Notebook | Contenido |
| -------- | --------- |
| `libros/Lectura.ipynb` | Limpieza de fuentes: inspección → limpieza → validación de cada archivo. Reproduce `limpiar_datos.py`. |
| `libros/Diagnostico_Limpieza_Empleos.ipynb` | Diagnóstico y limpieza formal del integrado (bloque 4). Reproduce `limpiar_empleos.py` con evidencia impresa. |
| `libros/presentacion.ipynb` | En construcción (filtros/visualización de trayectorias; pendiente). |

## Decisiones documentadas

- **Salida única en parquet** en el bloque 4: el integrado y su limpio solo se almacenan como `.parquet` (`pandas` + `pyarrow`); no se generan CSV intermedios en `data/cruce/` (los CSV están excluidos del repo vía `.gitignore`).
- **Prints como entregable:** en estos scripts/notebooks, la bitácora impresa (diagnóstico, decisiones, validación) es parte de la documentación del curso; los prints son intencionales, no residuos de depuración (ver excepción C2 en `md/BUENAS_PRACTICAS_CODIGO.md`).
- **Duración trimestral inclusiva:** una experiencia del mismo trimestre de inicio/fin dura 1 trimestre (`end − start + 1`), consistente con las estadísticas reportadas en la auditoría.
- **Claves cortas con `keep='first'`:** las filas extra de combinaciones repetidas se cuentan conservando la primera ocurrencia (74.357 / 9.601); no se eliminan por ser pluriempleo legítimo.
- **11 filas futuras:** se elimina 1 fila con inicio posterior a 2026 y 11 filas con fin posterior a 2026 (MCAR, < 1 %); una de ellas se cuenta en ambos criterios.
- Convenciones aplicadas al estándar del proyecto: ver `md/BUENAS_PRACTICAS_CODIGO.md`.

## Metodología: KDD

1. **Selección** — JobHop v2 y ESCO.
2. **Preprocesamiento** — nulos, duplicados, fechas, códigos desconocidos, inconsistencias.
3. **Transformación** — encadenar las experiencias de cada `resume_id` en una secuencia temporal de ocupaciones; luego enriquecer con ESCO.
4. **Minería** — técnicas candidatas: minería de secuencias, análisis de transiciones, clustering de trayectorias y detección de trayectorias atípicas.
5. **Interpretación y evaluación** — ¿son los patrones frecuentes, consistentes, interpretables y útiles para responder la pregunta de investigación?
6. **Conocimiento** — caracterización de los principales patrones de transición ocupacional.

> La técnica definitiva se seleccionará después de explorar la estructura final de los datos.

## Limitaciones

- **JobHop no representa Colombia** (los datos provienen de Flandes, Bélgica).
- **Sin causalidad:** se buscan asociaciones y patrones, no demostrar que una característica causa una trayectoria.
- **ESCO no es un dataset de trayectorias:** solo enriquece/interpreta las ocupaciones.
- **OLE no es una unión individual** con JobHop.
- **La técnica de minería aún no está definida definitivamente.**
- Los códigos de ESCO ajenos a la versión 1.2.1 y el valor `unknown` de `matched_code` requieren manejo explícito en el cruce (resuelto con banderas en el bloque 4).

## Estado actual y siguientes pasos

**Estado actual:** fuentes seleccionadas (JobHop v2 + ESCO v1.2.1), los 3 datasets documentados y limpios, integración aplicada y versionada en `data/cruce/empleos.parquet` (99,4% de códigos cruzan directo; 1.506.445 filas / 284.247 personas) **y limpieza formal del integrado completada** en `data/cruce/empleos_limpio.parquet` (1.506.434 × 14, todas las validaciones en verde). Pendiente: la selección de la técnica de minería.

**Siguientes pasos planificados:**
1. Convertir las experiencias en secuencias temporales por persona (`script/filtro/`).
2. Explorar la estructura de las trayectorias y seleccionar la técnica de minería.
3. Evaluar, interpretar y documentar los patrones encontrados.

## Referencias

- Artículo: *JobHop v2: A Large-Scale Career Trajectory Dataset from Unstructured Resumes* — https://arxiv.org/abs/2607.11715
- Repositorio del código fuente (STEP): https://github.com/aida-ugent/Step
- Dataset JobHop v2: https://huggingface.co/datasets/aida-ugent/JobHop
- ESCO (descarga): https://esco.ec.europa.eu/es/use-esco/download
- OLE Colombia: https://ole.mineducacion.gov.co/

## Requisitos

- Python 3
- `pandas>=2` y `pyarrow>=14` (ver `script/requirements/requirements.txt`)