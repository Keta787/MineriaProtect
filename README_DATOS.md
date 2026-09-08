# MineríaProtect — Datos y etapa de unión

Documento vigente de la **fase de unión (integración)**. Responde: qué datos tenemos, por qué se
unen esos y no otros, y qué se obtiene. Las cifras fueron verificadas sobre los datos reales.

---

## 1. Estructura del proyecto

```text
MineriaProtect/
├── dataset/                          # SOLO datasets limpios necesarios (fuente de verdad)
│   ├── JobHop_v2_train_limpio.parquet
│   └── ESCO/
│       ├── occupations_en_limpio.csv
│       ├── ISCOGroups_en_limpio.csv
│       ├── occupationSkillRelations_en_limpio.csv   # enriquecimiento: skills por ocupación
│       ├── skills_en_limpio.csv                     # enriquecimiento: nombre/nivel de cada skill
│       └── greenShareOcc_en_limpio.csv              # enriquecimiento: proporción "verde" por grupo ISCO
├── script/                           # Código y notebooks
│   ├── limpiar_datos.py              # data/original/ → dataset/ (limpieza de fuentes)
│   ├── cruzar_datos.py               # dataset/ → cruce/salida/empleos (integración)
│   ├── Lectura.ipynb
│   └── tablas.ipynb
├── cruce/
│   └── salida/                       # empleos: parquet versionado + CSV local (ignorado)
│       ├── empleos.parquet           # entregable integrado (versionado, 16 MB)
│       └── empleos.csv / empleos_ref.csv  # local, no se publican (>100 MB)
├── README.md                         # puerta de entrada del proyecto
└── README_DATOS.md                   # este documento
```

Notas:
- `data/original/`, `data/limpio/` y `data/integrado/` se conservan **en disco y en el historial
  git**, pero **no se versionan** en la rama de trabajo: el repositorio solo publica lo necesario.
- `cruce/salida/empleos` se regenera en cualquier momento → linaje reproducible sin depender de
  archivos de 156 MB.

---

## 2. Objetivo de la unión

El objetivo del proyecto es analizar **trayectorias laborales**. Para eso no basta tener códigos
de ocupación (`matched_code`): es necesario saber **qué ocupación** es cada código y **a qué área
ocupacional (ISCO-08)** pertenece, para poder:

- ordenar los empleos de cada persona en el tiempo;
- identificar la ocupación de cada empleo;
- medir si la persona cambia o no de área ocupacional;
- relacionar trayectorias con nivel educativo.

La unión convierte:

```text
JobHop limpio (employments con códigos)
        │  matched_code
        ▼
code ──› occupations   ──› nombre de la ocupación + grupo ISCO (4 dígitos)
        │  isco_group
        ▼
code ──› ISCOGroups    ──› etiqueta del área + nivel jerárquico
        │
        ▼
   empleos  = dataset integrado (1 fila = 1 experiencia laboral enriquecida)
```

**Regla de cardinalidad:** las uniones son N:1. `empleos` tiene exactamente las mismas filas que
JobHop limpio (1.506.445), nunca se multiplican registros.

---

## 3. Fuentes y sus roles

| Fuente | Archivo | Rol |
|---|---|---|
| **JobHop v2** | `dataset/JobHop_v2_train_limpio.parquet` | Trayectorias: persona, fechas trimestrales, nivel educativo, código de ocupación |
| **ESCO occupations** | `dataset/ESCO/occupations_en_limpio.csv` | Traduce cada código a nombre de ocupación y su grupo ISCO |
| **ESCO ISCOGroups** | `dataset/ESCO/ISCOGroups_en_limpio.csv` | Da la etiqueta y jerarquía del área ocupacional (ISCO-08) |
| ESCO skills (enriquecimiento) | `occupationSkillRelations`, `skills` | Perfil de competencias/especialización por ocupación |
| ESCO greenShare (enriquecimiento) | `greenShareOcc_en_limpio.csv` | Índice "verde" por área ocupacional |
| OLE Colombia | *(no existe archivo)* | **Descartado**: solo contexto colombiano, sin clave de unión con JobHop |

---

## 4. Por qué se unen JobHop + ESCO (occupations + ISCOGroups)

Es necesario porque **JobHop solo no responde la pregunta de investigación**: un `matched_code`
es un número sin significado. Verificado sobre los datos:

### Unión R1 — JobHop → occupations (`matched_code = code`)
- **Qué aporta:** el **nombre de la ocupación** y su **grupo ISCO-08** de 4 dígitos.
- **Por qué:** sin ella no se puede saber qué trabajo tenía la persona ni si cambia de área.
- **Cobertura:** 1.391.276 de 1.506.445 filas (92,35 %) cruzan directo.

### Unión R6 — Rescate por prefijo (`matched_code[:4] = código ISCO`)
- **Qué aporta:** recupera filas sin match exacto asignándoles al menos su **área ISCO** por los
  primeros 4 dígitos del código.
- **Por qué:** evita perder 10.176 empleos (0,68 %); su `matched_code[:4]` es idéntico al grupo
  real en el 100 % de los casos verificados.
- **Cobertura:** 10.176 filas de 16 códigos sin match directo.

### Unión R2 — occupations → ISCOGroups (`isco_group = code`)
- **Qué aporta:** la **etiqueta del área** (ej. "Systems analysts") y el **nivel** del grupo.
- **Por qué:** permite agrupar empleos por área ocupacional con nombre legible para el análisis.
- **Cobertura:** 426/426 grupos de 4 dígitos presentes en occupations → 100 %.

### Resultado: `empleos`
- 1.506.445 filas · 11 columnas · 0 duplicados.
- Clasificación `emparejado`: `ok` 92,35 % · `unknown` 6,97 % · `rescatado` 0,68 % · `descartado` 0.
- Las filas `unknown` (104.993) no tienen ocupación identificable → quedan marcadas para la fase
  de limpieza; no se borran aún.

### Columnas que aporta cada unión

| Unión | Columnas que añade | Ejemplo |
|---|---|---|
| R1 (occupations) | `matched_code`, `occupation_code`, `occupation_label`, `isco_group` | "Systems analysts", `2512` |
| R6 (prefijo ISCO) | `isco_group` recuperado cuando no hay match exacto | `5211` aunque no exista ocupación |
| R2 (ISCOGroups) | `isco_group_label`, `isco_level` | "Software and applications developers and analysts", nivel 4 |

Las 11 columnas finales de `empleos`:
`resume_id, start_date, end_date, university_level, matched_code, emparejado,
occupation_code, occupation_label, isco_group, isco_group_label, isco_level`.

---

## 5. CSV que SÍ se usan y por qué

| Archivo (en `dataset/`) | Por qué se usa |
|---|---|
| `JobHop_v2_train_limpio.parquet` | **Base del proyecto**: contiene las trayectorias (quién, cuándo, qué ocupación, nivel educativo) |
| `ESCO/occupations_en_limpio.csv` | **Traducción de códigos**: `code → nombre + iscoGroup`. Necesaria para interpretar cada empleo |
| `ESCO/ISCOGroups_en_limpio.csv` | **Área ocupacional**: `code(4d) → etiqueta + nivel`. Necesaria para medir cambios de área |
| `ESCO/occupationSkillRelations_en_limpio.csv` | Enriquecimiento: skills exigidas por cada ocupación (uso opcional, agregado) |
| `ESCO/skills_en_limpio.csv` | Enriquecimiento: nombre y especialización (`reuseLevel`) de cada skill |
| `ESCO/greenShareOcc_en_limpio.csv` | Enriquecimiento: proporción "verde" por grupo ISCO |

Los enriquecimientos se usan **agregados** (1 fila por ocupación/grupo), nunca expandiendo `empleos`.

---

## 6. CSV que NO se usan y por qué

| Archivo | Estado | Por qué no se usa |
|---|---|---|
| `skillSkillRelations_en_limpio.csv` | Pendiente (fase posterior) | Red N:M skill–skill; útil solo para análisis de red, no para la unión/trayectorias |
| `broaderRelationsOccPillar_en_limpio.csv` | Descartado metodológicamente | La jerarquía ISCO se obtiene por prefijo del código; es redundante |
| `broaderRelationsSkillPillar_en_limpio.csv` | Descartado | Sin borde skill→grupo en los datos; no clasifica skills por área |
| `skillGroups_en_limpio.csv` | Descartado | Igual que el anterior: taxonomía sin clave de unión utilizable |
| `skillsHierarchy_en_limpio.csv` | Descartado | Árbol de grupos de skills; no enlaza con skills concretas |
| `digCompSkillsCollection_en_limpio.csv` | Pendiente de evaluación | Colección temática; solo flags opcionales (no definidos) |
| `digitalSkillsCollection_en_limpio.csv` | Pendiente de evaluación | Idem: enriquecimiento temático opcional |
| `greenSkillsCollection_en_limpio.csv` | Pendiente de evaluación | Idem |
| `languageSkillsCollection_en_limpio.csv` | Pendiente de evaluación | Idem |
| `transversalSkillsCollection_en_limpio.csv` | Pendiente de evaluación | Idem |
| `researchSkillsCollection_en_limpio.csv` | Pendiente de evaluación | Idem |
| `researchOccupationsCollection_en_limpio.csv` | Descartado | Solo 122 ocupaciones de I+D; subconjunto de `occupations`, fuera del objetivo |
| `conceptSchemes_en_limpio.csv` | No necesario | Metadatos de esquemas; sin relación con trayectorias |
| `dictionary_en_limpio.csv` | No necesario | Glosario de columnas (documentación ESCO), no insumo de uniones |
| **Datasets de OLE** | Descartado | No existen en el repo; sin clave de unión individual con JobHop |
| `data/original/*` (fuentes crudas) | Fuentes | Conservadas en disco/historial; la capa de trabajo es solo `dataset/` |

> Tras la decisión del equipo (requisito del profesor), **`empleos` forma parte del abastecimiento**:
> el parquet en `cruce/salida/` es el entregable versionado; el CSV de 156 MB se genera localmente
> y no se publica (límite de GitHub de 100 MB por archivo).

---

## 7. Cómo reproducir todo

```text
# 1) Limpieza de fuentes (requiere data/original/ local)
python script/limpiar_datos.py          → dataset/ (JobHop se omite: ya está limpio)

# 2) Integración (requiere solo dataset/)
python script/cruzar_datos.py           → cruce/salida/empleos.parquet (+.csv local)
```

El cruce valida al ejecutarse: V1–V7 (contrato `CIERRE_DISENO.md`) + comparación exacta contra la
referencia `cruce/salida/empleos_ref.csv`. Resultado esperado: **mismos registros exactos: True**.

### Linaje (quién produce qué)

```text
limpiar_datos.py  →  dataset/ESCO/*_en_limpio.csv      (desde data/original/)
cruzar_datos.py   →  cruce/salida/empleos.parquet      (desde dataset/)
```

---

## 8. Datos faltantes a tratar en la siguiente etapa (limpieza del integrado)

Problemas verificados sobre `empleos` que la fase de limpieza deberá resolver (no se borran ahora):

| Problema | Cantidad | % | Nota |
|---|---|---|---|
| `emparejado = unknown` | 104.993 filas | 6,97 % | Sin ocupación identificable; decidir excluir/mantener |
| `university_level = 'None'` | 174.036 filas | 11,55 % | Categoría literal de JobHop (no nulo real) |
| Empleos simultáneos (fechas traslapadas) | **429.958 filas (28,54 %)** · **154.131 personas (54,22 %) de 284.247** | — | Afecta la definición de "transición" en la minería (verificado) |
| `occupation_label` / `isco_group` nulos | solo en `unknown` | — | Consecuencia directa del código sin match |