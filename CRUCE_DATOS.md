# Cruce de datos: JobHop v2 + ESCO

> **Etapa:** implementación del cruce/enriquecimiento (paso 1 de "Estado actual y siguientes pasos" del README).
> **Script:** `script/cruzar_datos.py`
> **Entrada:** `data/limpio/` (6 tablas relevantes).
> **Salida:** `data/procesada/empleos.csv` (1 archivo, 1 fila = 1 experiencia laboral enriquecida).

---

## 1. Por qué este cruce

El proyecto analiza las **trayectorias laborales** de las personas representadas en JobHop v2. Pero JobHop solo trae un código ocupacional (`matched_code`) sin significado: es una llave opaca tipo `3512.1`, `1324.4` o `3118.3.12`.

ESCO aporta el **significado** de esas ocupaciones: su nombre legible, su grupo ISCO-08 (el "área ocupacional") y la etiqueta oficial de ese grupo. Sin ESCO, un analista nunca sabría que `3512.1` significa "ICT help desk agent" ni que pertenece al área "Information and communications technology user support technicians".

**Objetivo del producto:** un solo CSV donde cada empleo de JobHop quede **enriquecido** con la ocupación y su área, listo para las fases posteriores de minería (secuencias, transiciones, clustering).

## 2. Archivos relevantes usados

| # | Archivo (data/limpio/) | Filas | Rol en el cruce |
|---|---|---|---|
| 1 | `JobHop_v2_train_limpio.parquet` | 1.506.445 | **Tabla central** — 1 fila = 1 experiencia laboral |
| 2 | `ESCO/occupations_en_limpio.csv` | 3.039 | **Catálogo de ocupaciones** — da nombre y grupo ISCO |
| 3 | `ESCO/ISCOGroups_en_limpio.csv` | 619 | **Clasificación ISCO-08** — da la etiqueta del área ocupacional |
| 4 | `ESCO/occupationSkillRelations_en_limpio.csv` | 126.051 | Puente ocupación→skill (disponible para fases posteriores) |
| 5 | `ESCO/skills_en_limpio.csv` | 13.939 | Catálogo de skills (disponible para fases posteriores) |
| 6 | `ESCO/greenShareOcc_en_limpio.csv` | 3.590 | Indicador verde por grupo ISCO (disponible para fases posteriores) |

Los archivos 4–6 **no multiplican filas** en el producto final: se cargan para quedar disponibles, pero el cruce principal se hace solo con los archivos 1–3 (relaciones N:1 que preservan la unidad de análisis).

> **Archivos ESCO descartados (13):** `skillSkillRelations`, `broaderRelationsOccPillar`, `broaderRelationsSkillPillar`, `skillGroups`, `skillsHierarchy`, 6 colecciones temáticas, `researchOccupationsCollection`, `conceptSchemes`, `dictionary`. Justificación completa en `DISEÑO_INTEGRACION.md` §2 (redundantes con prefijos ISCO, sin borde utilizable, dominio específico o metadatos).

## 3. Cómo se hizo el cruce (paso a paso)

### Paso 0 — Lectura como texto

Todos los CSV se leen con `dtype=str` para conservar ceros a la izquierda en códigos (ej. `0110` no se convierte en `110`). JobHop se lee del parquet limpio.

### Paso 1 — Clasificación `emparejado`

Para cada fila de JobHop se decide cómo se conecta con ESCO, por precedencia estricta:

| Regla | Condición | Categoría |
|---|---|---|
| 1 | `matched_code == 'unknown'` | `unknown` |
| 2 | `matched_code ∈ occupations.code` | `ok` |
| 3 | `matched_code[:4] ∈ ISCOGroups.code` (prefijo de 4 dígitos) | `rescatado` |
| 4 | cualquier otro caso | `descartado` (0 filas) |

**Resultado real:**

| Categoría | Filas | % |
|---|---|---|
| `ok` | 1.391.276 | 92,3% |
| `rescatado` | 10.176 | 0,7% |
| `unknown` | 104.993 | 7,0% |
| `descartado` | 0 | 0,0% |

### Paso 2 — Cruce N:1 JobHop → occupations (R1)

Se une por `matched_code = occupations.code` para traer:
- `occupation_code` (el código matcheado)
- `occupation_conceptUri` (URI ESCO)
- `occupation_label` (nombre legible de la ocupación)
- `isco_group_from_occ` (grupo ISCO-08 de 4 dígitos)

Este merge es **N:1** (a lo sumo 1 ocupación por empleo): no multiplica las 1.506.445 filas.

### Paso 3 — Rescate por prefijo ISCO (R6)

Los 16 códigos que no matchean directo pero cuyo **prefijo de 4 dígitos es un grupo ISCO válido** recuperan su área ocupacional:

- si `emparejado == 'rescatado'` → `isco_group = matched_code[:4]`

Esto recupera **10.176 empleos** que de otro modo se perderían a nivel de ocupación. Solo `unknown` queda sin `isco_group`.

### Paso 4 — Cruce N:1 con ISCOGroups (R2)

Se une por `isco_group = ISCOGroups.code` para traer:
- `isco_group_label` (nombre oficial del área, ej. "Draughtspersons")
- `isco_level` (nivel jerárquico = longitud del código; aquí siempre 4 = unidad ISCO)

### Paso 5 — Validaciones (afirmaciones V1–V7, V13)

| # | Afirmación | Valor obtenido |
|---|---|---|
| V1 | len tras cada merge | 1.506.445 ✓ |
| V2 | filas `ok` | 1.391.276 ✓ |
| V3 | filas `rescatado` | 10.176 ✓ |
| V4 | filas `unknown` | 104.993 ✓ |
| V5 | filas `descartado` | 0 ✓ |
| V6 | `isco_group` nulo solo en `unknown` | ✓ |
| V7 | duplicados de PK `(resume_id, matched_code, start_date, end_date)` | 0 ✓ |
| V13 | para todo `ok`: `matched_code[:4] == isco_group` | 100% ✓ |

### Paso 6 — Ordenamiento y guardado

Se ordena por `(resume_id, start_date, matched_code)` para que cada persona tenga sus empleos en orden temporal. Se guarda en `data/procesada/empleos.csv` (UTF-8).

## 4. Producto final: `data/procesada/empleos.csv`

**1.506.445 filas × 11 columnas** (156,8 MB).

| Columna | Origen | Descripción | Nulos |
|---|---|---|---|
| `resume_id` | JobHop | Identificador de la persona | 0 |
| `start_date` | JobHop | Trimestre de inicio (ej. `Q1 2000`) | 0 |
| `end_date` | JobHop | Trimestre de fin (ej. `Q4 2007` o `Present`) | 0 |
| `university_level` | JobHop | Nivel educativo (`Secondary school`/`Bachelor`/`Master`/`PhD`/`None`) | 0 |
| `matched_code` | JobHop | Código ocupacional original (sin interpretar) | 0 |
| `emparejado` | **derivado** | `ok` / `rescatado` / `unknown` | 0 |
| `occupation_code` | ESCO occupations | Código de ocupación (igual a `matched_code` cuando `ok`) | 115.169 (7,6%) |
| `occupation_label` | ESCO occupations | Nombre legible de la ocupación (ej. "ICT help desk agent") | 115.169 (7,6%) |
| `isco_group` | ESCO occupations + rescate | Grupo ISCO-08 de 4 dígitos (ej. `3512`) | 104.993 (7,0%) |
| `isco_group_label` | ESCO ISCOGroups | Área ocupacional oficial (ej. "Draughtspersons") | 104.993 (7,0%) |
| `isco_level` | ESCO ISCOGroups | Nivel jerárquico (siempre 4 en esta tabla) | 104.993 (7,0%) |

**Ejemplo real (persona 0):**

```
resume_id  start_date  end_date  university_level  matched_code  emparejado  occupation_code  occupation_label                                  isco_group  isco_group_label                                                      isco_level
       0    Q1 2000     Q1 2002   Master            3512.1        ok          3512.1           ICT help desk agent                                  3512       Information and communications technology...                          4
       0    Q1 2002     Q1 2004   Master            3512.2        ok          3512.2           ICT help desk manager                                 3512       Information and communications technology...                          4
       0    Q1 2004     Q4 2007   Master            4222.1        ok          4222.1           customer contact centre information clerk            4222       Contact centre information clerks                                      4
```

**Top 10 áreas ocupacionales más frecuentes:**

| Área (isco_group_label) | Empleos |
|---|---|
| Shop sales assistants | 120.639 |
| Administrative and executive secretaries | 98.466 |
| Freight handlers | 55.717 |
| Secondary education teachers | 35.560 |
| Waiters | 31.272 |
| Social work associate professionals | 30.093 |
| Cleaners and helpers in offices, hotels... | 26.692 |
| Child care workers | 25.930 |
| Cashiers and ticket clerks | 23.863 |
| Kitchen helpers | 23.743 |

## 5. Diseño del cruce (diagrama)

```text
                    data/limpio/
                          │
     ┌────────────────────┼────────────────────────────┐
     │                    │                            │
     │  N:1               │  N:1                       │  N:1 (futuro)
     ▼                    ▼                            ▼
JobHop           occupations         ISCOGroups                occupationSkillRelations
(matched_code)   (code, label,       (code, label)              + skills + greenShare
                  iscoGroup)                  │                 (perfil por ocupación,
     │                    │                  │                  agregado en fase posterior)
     │                    │                  │
     └────matched_code════╪══code═══════════╪──►  empleos.csv
                          │  iscoGroup═══code══►  (isco_group_label)
                          │
                 (rescatado: matched_code[:4])
```

## 6. Qué se puede responder con este CSV

| Pregunta del proyecto | Columnas necesarias | ¿Listo? |
|---|---|---|
| ¿Cuál fue el primer empleo de cada persona? | `resume_id`, `start_date`, `matched_code`, `occupation_label` | **Sí** |
| ¿Qué ocupaciones aparecen después? | + orden temporal | **Sí** |
| ¿Cuántos empleos por persona? | `resume_id` | **Sí** |
| ¿Cambia la persona de área ocupacional? | `isco_group`, `isco_group_label` | **Sí** |
| ¿Qué áreas son las más frecuentes como destino? | `isco_group_label` | **Sí** |
| ¿Hay relación entre nivel educativo y ocupación? | `university_level`, `isco_group` | **Sí** (parcial: solo nivel, no campo de estudio) |

## 7. Limitaciones del producto

- **`unknown` (7,0%):** 104.993 empleos sin ocupación interpretable. Se conservan como categoría propia (`emparejado='unknown'`), no se eliminan.
- **Sin skills en el CSV final:** el perfil de skills (relaciones, reuseLevel, greenShare) requiere agregación por ocupación; se dejó como tabla puente para la fase de minería (evita multiplicar ~41× las filas de empleo).
- **`isco_level` siempre 4:** todos los empleos matcheados caen en unidades ISCO de 4 dígitos; los niveles superiores (gran grupo/sub-grupo) se derivan por prefijo del código.

## 8. Cómo ejecutar

```bash
python script/cruzar_datos.py
```

Idempotente: re-ejecutarlo sobrescribe `data/procesada/empleos.csv` con contenido idéntico.

## 9. Siguientes pasos

1. Enriquecer con **perfil de skills por ocupación** (T2 `ocupaciones`): n_skills, n_essential, n_optional, reuseLevel, greenShare — todo agregado, sin tocar la unidad de análisis.
2. Construir **secuencias temporales por persona** (encadenar empleos en orden por `start_date`).
3. Seleccionar técnica de minería: secuencias, transiciones, clustering de trayectorias.