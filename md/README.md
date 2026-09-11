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
├── data/                          # todos los datos bajo una sola raíz
│   ├── original/                  # Fuentes (NUNCA se modifican)
│   │   ├── JobHop_v2_train.parquet
│   │   └── ESCO/                  # occupations_en.csv + ISCOGroups_en.csv (los 2 en uso)
│   ├── limpia/                    # Versiones limpias (derivados, se sobrescriben)
│   │   ├── JobHop_v2_train_limpio.parquet   # generado en un proceso anterior (verificado)
│   │   └── ESCO/                  # *_limpio.csv de los 2 ESCO en uso
│   └── cruce/                     # integrado: empleos.parquet (versionado) + *.csv ignorados
├── md/                            # documentación: README.md, AUDITORIA_RAMA_PRUEBA.md, contexto_sesion3.md
├── script/
│   ├── limpiar_datos.py           # Proceso de limpieza (fuente única)
│   └── Lectura.ipynb              # Cuaderno de limpieza (reproduce el script)
└── .gitignore
```

Reglas de oro del proyecto:

- **Los archivos originales nunca se modifican**: solo se leen.
- **No se vuelve a limpiar una versión limpia/derivada.** `JobHop_v2_train.parquet` ya generó su limpio en un proceso anterior, por eso queda **excluido** del proceso automático.
- El proceso de limpieza es **idempotente**: re-ejecutarlo sobrescribe los archivos limpios con contenido idéntico (no genera duplicados).

## Datasets

### JobHop v2 (`aida-ugent/JobHop`)

| Archivo | Descripción |
| ------- | ----------- |
| `data/original/JobHop_v2_train.parquet` | Dataset original (1.594.827 filas) |
| `data/limpia/JobHop_v2_train_limpio.parquet` | Dataset limpio (1.506.445 filas) — derivado previo, no se re-limpió |

Limpieza aplicada en el proceso anterior (derivado previo; verificado en `Lectura.ipynb`, no re-ejecutada): `end_date` nulo → `Present`; filas sin `start_date` eliminadas; duplicados exactos eliminados; orden por persona y trimestre real (`Q1 2000` → clave `(2000, 1)`).

### Taxonomía ESCO v1.2.1 (2 CSV en uso)

| Archivo | Originales | Limpias | Operación clave |
| ------- | ---------- | ------- | --------------- |
| `occupations_en.csv` | 3.043 | 3.039 | −4 filas por `code` duplicado (idénticas salvo `modifiedDate`) |
| `ISCOGroups_en.csv` | 619 | 619 | columna `altLabels` 100% nula eliminada (8 → 7 columnas) |

Solo se conservan los archivos que usa la integración (`occupations` e `ISCOGroups`). El resto de la
taxonomía ESCO (skills, relaciones skill-ocupación, greenShare, colecciones, etc.) fue **descartado**
del repo en el recorte a 3 datasets; su historial queda en git.

## Proceso de limpieza

Reglas generales (aplicadas por `script/limpiar_datos.py` y reproducidas en `script/Lectura.ipynb`):

1. Los CSV se leen **como texto** (`dtype=str`) para no perder ceros a la izquierda en los códigos (p. ej. código ISCO `0110` ≠ `110`).
2. Se eliminan las **columnas 100% nulas** (columna sin información no sirve para cruzar).
3. Se normalizan textos: `strip()` (quita espacios que romperían comparaciones en cruces).
4. Se eliminan **duplicados exactos de fila completa** (en la práctica 0; regla defensiva).
5. **Duplicados por llave** (datos de dos publicaciones de ESCO fusionadas):
   - `occupations_en`: −4 filas por `code` (idénticas salvo `modifiedDate`; se conserva la primera).
6. `ISCOGroups_en`: `altLabels` está 100% nula → se elimina (de 8 a 7 columnas).
7. Cada archivo pasa por **validación antes/después**: filas, columnas, nulos críticos, duplicados y las transformaciones aplicadas.

`JobHop_v2_train.parquet` está **excluido** del proceso automático: ya tiene su versión limpia (derivado previo).

Idempotencia verificada: ejecutar el proceso dos veces produce **archivos byte a byte idénticos** (no se generan duplicados).

## Cómo ejecutar

- Proceso completo en consola:

  ```bash
  python script/limpiar_datos.py
  ```

- Reproducir y **documentar** el mismo proceso:

  `script/Lectura.ipynb` (Kernel → Restart & Run All)

Los cuadernos detectan la raíz del proyecto aunque se abran desde la carpeta `script/`.

## Notebooks

| Notebook | Contenido |
| -------- | --------- |
| `script/Lectura.ipynb` | Limpieza: inspección → limpieza → validación de cada archivo. Reproduce exactamente `limpiar_datos.py` (trazabilidad código → ejecución → datos limpios). |

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
- Los códigos de ESCO ajenos a la versión 1.2.1 y el valor `unknown` de `matched_code` requieren manejo explícito en el cruce.

## Estado actual y siguientes pasos

**Estado actual:** fuentes seleccionadas (JobHop v2 + ESCO v1.2.1), los 3 datasets documentados y limpios, e integración aplicada y versionada en `data/cruce/empleos.parquet` (cruce `matched_code` ↔ `occupations.code`: 99,4% de códigos cruzan directo; 1.506.445 filas / 284.247 personas). Pendiente: la limpieza formal del integrado y la selección de la técnica de minería.

**Siguientes pasos planificados:**
1. Aplicar la limpieza del integrado `empleos` (diagnóstico, banderas, outliers, bitácora).
2. Convertir las experiencias en secuencias temporales por persona.
3. Explorar la estructura de las trayectorias y seleccionar la técnica de minería.
4. Evaluar, interpretar y documentar los patrones encontrados.

## Referencias

- Artículo: *JobHop v2: A Large-Scale Career Trajectory Dataset from Unstructured Resumes* — https://arxiv.org/abs/2607.11715
- Repositorio del código fuente (STEP): https://github.com/aida-ugent/Step
- Dataset JobHop v2: https://huggingface.co/datasets/aida-ugent/JobHop
- ESCO (descarga): https://esco.ec.europa.eu/es/use-esco/download
- OLE Colombia: https://ole.mineducacion.gov.co/

## Requisitos

- Python 3
- `pandas`
- `pyarrow`