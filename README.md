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

> No se asume de antemano que trabajar en el área estudiada produce una mejor trayectoria.
> Esa sería una hipótesis; el objetivo es descubrir y evaluar los patrones presentes en los datos.

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
- **Versión incorporada:** ESCO v1.2.1 (clasificación en inglés, archivos CSV en
  `ESCO dataset - v1.2.1 - classification - en - csv/`).
- **Por qué se agrega:** JobHop trae códigos de ocupación (`matched_code`), pero se necesita
  información interpretable sobre esas ocupaciones. ESCO relaciona los códigos con nombre,
  descripción, clasificación ocupacional, grupos ocupacionales, relación con ISCO y
  competencias.
- No se agrega "por tener dos bases de datos", sino para **enriquecer las experiencias
  laborales de JobHop y hacer posible un análisis más significativo de las transiciones**.

> **Estado del cruce:** la base ESCO ya está descargada e incorporada al repositorio, pero el
> **cruce/enriquecimiento de ESCO con JobHop todavía está pendiente**. Antes de implementarlo
> hay que verificar que la versión de ESCO usada sea compatible con la versión que emplea
> JobHop v2.

### 3. OLE Colombia — fuente contextual (opcional)

El **Observatorio Laboral para la Educación (OLE)** del Ministerio de Educación:
https://ole.mineducacion.gov.co/

Proporciona información agregada del contexto colombiano (graduados, programas académicos,
vinculación laboral, ingresos, seguimiento de cohortes e indicadores laborales). Solo se
considera como **contexto o fuente complementaria**; no es obligatorio ni se usa para
reconstruir trayectorias individuales (limitaciones de granularidad y protección de datos).
**No se puede unir a JobHop a nivel individual.**

## Dataset (JobHop v2)

| Archivo | Descripción |
| ------- | ----------- |
| `JobHop_v2_train.parquet` | Dataset original (1.594.827 filas) |
| `JobHop_v2_train_limpio.parquet` | Dataset limpio (1.506.445 filas): sin nulos en `start_date`, fecha de fin rellenada con "Present" y sin duplicados |

## Metodología: KDD

1. **Selección** — JobHop v2 y ESCO.
2. **Preprocesamiento** — nulos, duplicados, fechas, códigos desconocidos, inconsistencias.
3. **Transformación** — encadenar las experiencias de cada `resume_id` en una secuencia
   temporal de ocupaciones; luego enriquecer con ESCO.
4. **Minería** — técnicas candidatas: minería de secuencias, análisis de transiciones,
   clustering de trayectorias y detección de trayectorias atípicas.
5. **Interpretación y evaluación** — ¿son los patrones frecuentes, consistentes, interpretables
   y útiles para responder la pregunta de investigación?
6. **Conocimiento** — caracterización de los principales patrones de transición ocupacional.

> La técnica definitiva se seleccionará después de explorar la estructura final de los datos.

## Notebooks

| Notebook | Contenido |
| -------- | --------- |
| `Lectura..ipynb` | Lectura del dataset original, limpieza de datos y guardado de la versión limpia |

## Limitaciones

- **JobHop no representa Colombia** (los datos provienen de Flandes, Bélgica).
- **Sin causalidad:** se buscan asociaciones y patrones, no demostrar que una característica
  causa una trayectoria.
- **ESCO no es un dataset de trayectorias:** solo enriquece/interpreta las ocupaciones.
- **OLE no es una unión individual** con JobHop.
- **La técnica de minería aún no está definida definitivamente.**

## Estado actual y siguientes pasos

**Estado actual:** JobHop v2 ya fue seleccionado, leído y limpiado (`Lectura..ipynb`).
La base de ESCO v1.2.1 ya fue descargada e incorporada al repositorio, pero su cruce con
JobHop aún está pendiente. El proyecto se encuentra en la fase de preparación y diseño.

**Siguientes pasos planificados:**
1. Verificar la compatibilidad de la versión de ESCO con la usada por JobHop v2.
2. Implementar el cruce/enriquecimiento de las ocupaciones con ESCO.
3. Aplicar el preprocesamiento y transformar las experiencias en secuencias temporales.
4. Explorar la estructura de las trayectorias y seleccionar la técnica de minería.
5. Evaluar, interpretar y documentar los patrones encontrados.

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
