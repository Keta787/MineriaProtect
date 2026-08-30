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

## Dataset

| Archivo | Descripción |
| ------- | ----------- |
| `JobHop_v2_train.parquet` | Dataset original (1.594.827 filas) |
| `JobHop_v2_train_limpio.parquet` | Dataset limpio (1.506.445 filas): sin nulos en `start_date`, fecha de fin rellenada con "Present" y sin duplicados |

**Columnas:**

- `resume_id`: identificador de la persona/currículum
- `matched_code`: código de ocupación (taxonomía ESCO)
- `start_date`: trimestre de inicio (ej. `Q1 2000`)
- `end_date`: trimestre de fin (ej. `Q4 2007` o `Present`)
- `university_level`: nivel de formación (ej. `Master`, `Bachelor`)

Una misma `resume_id` puede tener varias filas: cada una es una experiencia laboral distinta de la misma persona. Encadenadas en orden forman la trayectoria profesional.

## Notebooks

| Notebook | Contenido |
| -------- | --------- |
| `Lectura..ipynb` | Lectura del dataset original, limpieza de datos y guardado de la versión limpia |

## Referencias

- Artículo: *JobHop v2: A Large-Scale Career Trajectory Dataset from Unstructured Resumes* — https://arxiv.org/abs/2607.11715
- Repositorio del código fuente (STEP): https://github.com/aida-ugent/Step
- Dataset: https://huggingface.co/datasets/aida-ugent/JobHop

## Requisitos

- Python 3
- `pandas`
- `pyarrow`