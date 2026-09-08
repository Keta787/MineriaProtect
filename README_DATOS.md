# Datos del proyecto MineriaProtect

Auditoría de datos realizada sobre el estado actual del repositorio (solo lectura).
Toda conclusión está respaldada por inspección de archivos, código, notebooks o verificación
empírica sobre los datos. Cuando algo no pudo comprobarse se marca como `NO VERIFICADO`.

---

## 1. Objetivo del procesamiento de datos

El proyecto estudia **trayectorias laborales** con minería de secuencias/transiciones ocupacionales.
Para eso los datos deben pasar de "secuencias de códigos sin sentido" a "secuencias de ocupaciones
interpretables".

Flujo objetivo del procesamiento de datos:

```text
JobHop v2 (trayectorias, códigos de ocupación)
   ↓ limpieza
JobHop limpio (matched_code)
   ↓ cruce  matched_code → occupations.code
códigos ocupacionales interpretados (nombre, grupo ISCO)
   ↓ cruce  isco_group → ISCOGroups.code
área ocupacional (etiqueta jerárquica ISCO-08)
   ↓
dataset integrado (1 fila = 1 experiencia laboral enriquecida)
   ↓
construcción de trayectorias por persona
   ↓
minería de secuencias / transiciones
```

El objetivo del procesamiento no es "tener muchas tablas", sino producir **un dataset de empleos
enriquecido** (T1 `empleos`) que conserve la unidad de análisis original: **1 fila de JobHop =
1 experiencia laboral**.

---

## 2. Fuentes de datos

| Dataset | Archivo | Tipo | Uso |
|---|---|---|---|
| **JobHop v2** | `data/original/JobHop_v2_train.parquet` | Fuente original | Fuente principal de trayectorias laborales |
| **ESCO v1.2.1** | `data/original/ESCO/*.csv` (19 archivos) | Fuente original de enriquecimiento | Da significado a los códigos de ocupación (nombre, ISCO, skills) |
| **OLE Colombia** | *No existe archivo en el repositorio* | Contexto (opcional) | Solo contexto colombiano; no participa en ningún cruce |

> **OLE**: el repositorio **no contiene ningún CSV de OLE**. Solo aparece mencionado como contexto
> en `README.md`. No tiene clave de integración individual con JobHop (ver sección 8).

---

## 3. Estructura de los datos

```text
MineriaProtect/
├── data/
│   ├── original/                  # Fuentes descargadas (NUNCA se modifican; solo lectura)
│   │   ├── JobHop_v2_train.parquet
│   │   └── ESCO/                  # 19 CSV de la taxonomía ESCO v1.2.1
│   ├── limpio/                    # Derivados de la limpieza (verificados, no se re-limpiar)
│   │   ├── JobHop_v2_train_limpio.parquet    # 1.506.445 filas × 5 columnas
│   │   └── ESCO/                  # 19 CSV *_limpio.csv
│   └── procesado/                 # VACÍA — destino previsto para el dataset integrado
├── script/
│   ├── limpiar_datos.py           # Único script: limpieza original → limpio
│   ├── Lectura.ipynb              # Reproduce limpiar_datos.py (celda a celda)
│   └── tablas.ipynb               # Visual: solo lee data/limpio/
├── README.md                      # Documentación del proyecto
├── AUDITORIA_LIMPIEZA.md          # Auditoría de la etapa de limpieza
├── DISEÑO_INTEGRACION.md          # Diseño conceptual de la integración (sin implementar)
├── CIERRE_DISEÑO.md               # Especificación implementable de la integración T1/T2/T3
└── README_DATOS.md                # Este documento (auditoría de datos)
```

**Estado verificable de `data/procesado/`:** la carpeta existe en disco pero está **vacía** y
**no está versionada** en git. No contiene ningún archivo de datos.

---

## 4. Clasificación de archivos

### A. Fuentes originales (no se modifican)

| Archivo | Filas | Columnas | Uso |
|---|---|---|---|
| `data/original/JobHop_v2_train.parquet` | 1.594.827 | 5 | Trayectorias brutas |
| `data/original/ESCO/occupations_en.csv` | 3.043 | 15 | Catálogo de ocupaciones ESCO |
| `data/original/ESCO/ISCOGroups_en.csv` | 619 | 8 | Clasificación ISCO-08 |
| `data/original/ESCO/occupationSkillRelations_en.csv` | 126.051 | 6 | Puente ocupación–skill |
| `data/original/ESCO/skills_en.csv` | 13.960 | 13 | Catálogo de skills |
| `data/original/ESCO/greenShareOcc_en.csv` | 3.590 | 5 | Índice "verde" por grupo ISCO |
| `data/original/ESCO/skillSkillRelations_en.csv` | 5.818 | 5 | Red skill–skill |
| `data/original/ESCO/broaderRelationsOccPillar_en.csv` | 3.648 | 6 | Jerarquía ISCO (pillar) |
| `data/original/ESCO/broaderRelationsSkillPillar_en.csv` | 20.819 | 6 | Jerarquía de skill groups |
| `data/original/ESCO/skillGroups_en.csv` | 640 | 11 | Grupos de skills (ISCED-F) |
| `data/original/ESCO/skillsHierarchy_en.csv` | 640 | 14 | Árbol de skill groups |
| `data/original/ESCO/digitalSkillsCollection_en.csv` | 1.284 | 10 | Colección skills digitales |
| `data/original/ESCO/greenSkillsCollection_en.csv` | 629 | 10 | Colección skills verdes |
| `data/original/ESCO/languageSkillsCollection_en.csv` | 359 | 10 | Colección skills de idiomas |
| `data/original/ESCO/transversalSkillsCollection_en.csv` | 95 | 10 | Colección skills transversales |
| `data/original/ESCO/researchSkillsCollection_en.csv` | 40 | 10 | Colección skills de I+D |
| `data/original/ESCO/digCompSkillsCollection_en.csv` | 25 | 10 | Marco DigComp |
| `data/original/ESCO/researchOccupationsCollection_en.csv` | 122 | 8 | Ocupaciones de I+D |
| `data/original/ESCO/conceptSchemes_en.csv` | 20 | 7 | Metadatos de esquemas |
| `data/original/ESCO/dictionary_en.csv` | 160 | 4 | Glosario oficial de columnas ESCO |

### B. Datasets limpios (derivados de las fuentes, verificados)

| Archivo | Filas | Columnas |
|---|---|---|
| `data/limpio/JobHop_v2_train_limpio.parquet` | 1.506.445 | 5 |
| `data/limpio/ESCO/occupations_en_limpio.csv` | 3.039 | 15 |
| `data/limpio/ESCO/ISCOGroups_en_limpio.csv` | 619 | 7 |
| `data/limpio/ESCO/occupationSkillRelations_en_limpio.csv` | 126.051 | 6 |
| `data/limpio/ESCO/skills_en_limpio.csv` | 13.939 | 13 |
| `data/limpio/ESCO/greenShareOcc_en_limpio.csv` | 3.590 | 5 |
| `data/limpio/ESCO/skillSkillRelations_en_limpio.csv` | 5.818 | 5 |
| `data/limpio/ESCO/broaderRelationsOccPillar_en_limpio.csv` | 3.648 | 6 |
| `data/limpio/ESCO/broaderRelationsSkillPillar_en_limpio.csv` | 20.819 | 6 |
| `data/limpio/ESCO/skillGroups_en_limpio.csv` | 640 | 11 |
| `data/limpio/ESCO/skillsHierarchy_en_limpio.csv` | 640 | 14 |
| `data/limpio/ESCO/digitalSkillsCollection_en_limpio.csv` | 1.284 | 10 |
| `data/limpio/ESCO/greenSkillsCollection_en_limpio.csv` | 629 | 10 |
| `data/limpio/ESCO/languageSkillsCollection_en_limpio.csv` | 359 | 10 |
| `data/limpio/ESCO/transversalSkillsCollection_en_limpio.csv` | 95 | 10 |
| `data/limpio/ESCO/researchSkillsCollection_en_limpio.csv` | 40 | 10 |
| `data/limpio/ESCO/digCompSkillsCollection_en_limpio.csv` | 25 | 10 |
| `data/limpio/ESCO/researchOccupationsCollection_en_limpio.csv` | 122 | 8 |
| `data/limpio/ESCO/conceptSchemes_en_limpio.csv` | 20 | 7 |
| `data/limpio/ESCO/dictionary_en_limpio.csv` | 160 | 4 |

Las versiones limpias se generan con `script/limpiar_datos.py` (y se reproducen en
`script/Lectura.ipynb`). Las cifras anteriores (filas/columnas) fueron verificadas empíricamente
en esta auditoría y coinciden con la documentación.

### C. Datasets de enriquecimiento

- `ESCO/occupations_en_limpio.csv` → añade nombre, descripción y grupo ISCO a cada código.
- `ESCO/ISCOGroups_en_limpio.csv` → añade la etiqueta del área ocupacional.
- `ESCO/occupationSkillRelations_en_limpio.csv` + `ESCO/skills_en_limpio.csv` → perfil de
  skills por ocupación (**agregado**, no expandido).
- `ESCO/greenShareOcc_en_limpio.csv` → indicador verde por grupo ISCO (opcional).

### D. Datasets intermedios

- No existe ningún archivo intermedio materializado. Los documentos
  `DISEÑO_INTEGRACION.md` y `CIERRE_DISEÑO.md` **diseñan** las tablas T1/T2/T3, pero
  **no se ha generado el script `cruzar_datos.py` ni los archivos de salida**.

### E. Dataset final

- Definido por diseño como **T1 `empleos`** → `data/procesado/empleos.parquet` (ver sección 10).
  **No existe todavía.**

### F. No utilizados para el flujo principal (ver sección 9)

- `skillSkillRelations`, `broaderRelations*Pillar`, `skillGroups`, `skillsHierarchy`,
  6 colecciones de skills, `researchOccupationsCollection`, `conceptSchemes`, `dictionary`.

---

## 5. Procedencia y función de las 11 columnas "funcionales"

El conjunto reportado por el compañero coincide exactamente con las columnas de la tabla
**T1 `empleos`** definida en `CIERRE_DISEÑO.md` §3. Verificado: **ningún archivo del
repositorio contiene hoy estas columnas**; son el resultado *diseñado* del cruce, no datos
existentes.

| Columna | Origen | Fuente (archivo) | Transformación / regla |
|---|---|---|---|
| `resume_id` | Original | `JobHop_v2_train_limpio.parquet` | Copia directa |
| `start_date` | Original | JobHop limpio | Copia directa |
| `end_date` | Original | JobHop limpio | Copia directa |
| `university_level` | Original | JobHop limpio | Copia directa |
| `matched_code` | Original | JobHop limpio | Copia directa |
| `emparejado` | Derivada (integración) | — | Clasificación con precedencia: `'unknown'` si `matched_code=='unknown'`; `'ok'` si está en `occupations.code`; `'rescatado'` si `matched_code[:4]` es código ISCO-08 de 4 dígitos; si no, `'descartado'` (verificado: 0 filas) |
| `occupation_code` | Derivada | `occupations_en_limpio.code` | `= matched_code` cuando `emparejado=='ok'`; NaN en otro caso |
| `occupation_label` | Derivada (JOIN) | `occupations_en_limpio.preferredLabel` | JOIN N:1 `occupation_code → code` |
| `isco_group` | Derivada | `occupations_en_limpio.iscoGroup` o `ISCOGroups_en_limpio.code` | `'ok'` → `occupations.iscoGroup`; `'rescatado'` → `matched_code[:4]`; `'unknown'` → NaN |
| `isco_group_label` | Derivada (JOIN) | `ISCOGroups_en_limpio.preferredLabel` | JOIN N:1 `isco_group → code` |
| `isco_level` | Derivada | — | `= len(isco_group)` (verificado: siempre 4 en T1) |

### Preguntas del paso 3 respondidas

1. **¿En qué archivos aparecen originalmente?** `resume_id`, `start_date`, `end_date`,
   `university_level`, `matched_code` existen en JobHop limpio. El resto no aparece en
   ningún archivo.
2. **¿Qué columnas son creadas por transformación?** `emparejado`, `occupation_code`,
   `isco_group`, `isco_level` (derivadas fila a fila) y `occupation_label`, `isco_group_label`
   (resultado de join).
3. **¿Qué columnas provienen de JobHop?** Las 5 originales.
4. **¿Qué columnas provienen de ESCO?** `occupation_label` (occupations), `isco_group`
   (occupations o prefijo), `isco_group_label` (ISCOGroups).
5. **¿Qué columnas son resultado de la integración?** `emparejado`, `occupation_code`,
   `isco_group`, `isco_level` (derivadas) y las dos etiquetas (joins).
6. **¿Cuáles son necesarias para las trayectorias?** Todas las 5 originales son necesarias.
   De las derivadas, para **minería de transiciones** las esenciales son `emparejado`
   (control de calidad), `occupation_code`/`occupation_label` (identidad de la ocupación) y
   `isco_group` (área ocupacional). `isco_group_label`/`isco_level` son de lectura/agregación.
7. **¿Columnas redundantes?** `occupation_code` y `matched_code` son idénticas cuando
   `emparejado=='ok'`; ambas se conservan por diseño (bruto vs. validado). `isco_level` es
   constante (4) en T1 → solo aporta si se agregan niveles superiores de ISCO.
8. **¿Alguna no debería estar en el final?** Con el diseño actual ninguna sobra; las
   decisiones de descarte pertenecen a la etapa de minería (e.g. cómo tratar `unknown`).

---

## 6. Uniones reconstruidas

Verificado: **no existe ninguna operación `merge`/`join`/`concat` implementada** en
`limpiar_datos.py`, `Lectura.ipynb` ni `tablas.ipynb`. Las uniones que siguen son las que
define el diseño (`CIERRE_DISEÑO.md`) y cuya **cobertura fue verificada empíricamente** en
esta auditoría.

| # | Izquierdo | Derecho | Clave | Tipo | Aporta | Columnas nuevas | Cobertura verificada |
|---|---|---|---|---|---|---|---|
| R1 | JobHop limpio | `occupations_en_limpio` | `matched_code` = `code` | N:1 (left) | Nombre, grupo ISCO, descripción de la ocupación | `occupation_code`, `occupation_label`, `isco_group` | 1.391.276 filas (92,35%) directas; 16 códigos sin match (→ R6) |
| R2 | `occupations_en_limpio` | `ISCOGroups_en_limpio` | `iscoGroup` = `code` | N:1 (left) | Etiqueta y jerarquía ISCO del área | `isco_group_label`, nivel | 426/426 grupos únicos; 100% de ocupaciones cubiertas |
| R3 | `occupations_en_limpio` | `occupationSkillRelations_en_limpio` | `conceptUri` = `occupationUri` | 1:N → agregación | Perfil de skills por ocupación (sin expandir filas) | columnas `n_*` de T2 `ocupaciones` | 3.039/3.039 ocupaciones; 126.051 relaciones |
| R4 | `occupationSkillRelations_en_limpio` | `skills_en_limpio` | `skillUri` = `conceptUri` | N:1 (left) | Nombre y `reuseLevel` de cada skill | `reuseLevel` agregado | 13.475/13.475 skills presentes (100%) |
| R5 | `occupations_en_limpio` | `greenShareOcc_en_limpio` | `iscoGroup` = `code` (4 díg.) | N:1 (left) | Índice "verde" por área | `greenShare` | 426/426 grupos cubiertos (100%) |
| R6 (rescate) | JobHop (filas sin match) | `ISCOGroups_en_limpio` | `matched_code[:4]` = `code` | N:1 (left) | Recupera la fila a nivel de grupo ISCO | `isco_group`, etiqueta | 10.176 filas (0,68%) recuperadas de 16 códigos |

### Justificación de cada unión

- **R1**: es la unión central. Traduce el código abstracto de JobHop a una ocupación con
  nombre y área. Sin ella el proyecto no puede interpretar las trayectorias.
- **R2**: permite agrupar empleos por **área ocupacional (ISCO-08)** y responder si una
  persona cambia o no de área.
- **R3+R4**: caracterizan la ocupación de destino (competencias exigidas, especialización
  vía `reuseLevel`). Se aplican **agregadas** para no multiplicar filas de empleo (1 ocupación
  tiene 7–178 skills; expandirlas rompería la unidad de análisis).
- **R5**: contextualiza las áreas (transiciones hacia áreas verdes). Opcional.
- **R6**: rescata el 0,68% de filas que no cruzan directo pero sí tienen prefijo ISCO válido
  (ej. `2131.8` → grupo `2131`). Verificado: en las filas con match directo, `matched_code[:4]==iscoGroup`
  en el 100% → la regla de rescate es equivmente al mapeo real.

---

## 7. Verificación del flujo JobHop + ESCO

El flujo conceptual planteado es **correcto en estructura** con una salvedad: las etapas
después de `match` están **diseñadas, no implementadas**.

```text
JobHop v2 ─limpieza→ matched_code ─R1→ occupations (occupation_code, occupation_label, isco_group)
                                                              │
                                        ─R2→ ISCOGroups (isco_group_label, isco_level)
                                                              │
                                        ─R6→ rescate prefijo ISCO (10.176 filas)
                                                              ↓
                                              dataset integrado (NO existe aún)
                                                              ↓
                                              trayectorias laborales ─→ minería de secuencias
```

Corrección al planteamiento original: `occupation_code` no proviene directamente de ESCO,
sino que **es el `matched_code` de JobHop validado** contra `occupations.code`; ESCO aporta la
**etiqueta** (`occupation_label`) y el **grupo** (`isco_group`). `isco_group` en filas
rescatadas proviene del **prefijo** de `matched_code`, no de `occupations`.

---

## 8. Papel de OLE (contexto vs. dato usado)

- **¿Participa en una unión?** No. No existe ningún archivo OLE en el repositorio.
- **¿Existe clave para unirlo a nivel individual?** No. JobHop es una muestra internacional
  (Flandes, Bélgica) con `resume_id` anónimos; OLE es agregado colombiano. No hay claves
  compartidas (documentado en `README.md`).
- **¿Se usa como contexto?** Sí, únicamente textual en `README.md` como contexto opcional.
- **¿Forma parte del dataset final?** No.
- **Conclusión:** OLE es **contexto/comparación**, nunca insumo de minería. No se debe mezclar
  con los datos que alimentan el análisis de trayectorias.

---

## 9. CSV no utilizados y por qué

| Archivo (limpio) | Estado | Razón |
|---|---|---|
| `skillSkillRelations_en_limpio.csv` | No utilizado actualmente (fase posterior) | Red N:M skill–skill; útil para análisis de red, no para la integración principal |
| `broaderRelationsOccPillar_en_limpio.csv` | Descartado metodológicamente (para joins) | La jerarquía ISCO se deriva por prefijo del código; la pillar es redundante |
| `broaderRelationsSkillPillar_en_limpio.csv` | Descartado (sin borde utilizable) | No existe extremo skill→grupo en `data/limpio/` para clasificar cada skill |
| `skillGroups_en_limpio.csv` | Descartado | Misma razón: sin borde skill→grupo ISCED-F |
| `skillsHierarchy_en_limpio.csv` | Descartado | Misma razón: árbol de grupos, no enlaza con skills |
| `digCompSkillsCollection_en_limpio.csv` | Pendiente de evaluación (colección) | Flags temáticos opcionales de enriquecimiento (D3 sin aprobar) |
| `digitalSkillsCollection_en_limpio.csv` | Pendiente de evaluación | Idem |
| `greenSkillsCollection_en_limpio.csv` | Pendiente de evaluación | Idem |
| `languageSkillsCollection_en_limpio.csv` | Pendiente de evaluación | Idem |
| `transversalSkillsCollection_en_limpio.csv` | Pendiente de evaluación | Idem |
| `researchSkillsCollection_en_limpio.csv` | Pendiente de evaluación | Idem |
| `researchOccupationsCollection_en_limpio.csv` | Descartado | Solo 122 ocupaciones de I+D; subconjunto de `occupations`, fuera del objetivo general |
| `conceptSchemes_en_limpio.csv` | No necesario para el flujo final | Metadatos de esquemas; sin relación con trayectorias |
| `dictionary_en_limpio.csv` | No necesario para el flujo final | Glosario de columnas (documentación), no insumo de joins |

> Distinción aplicada: "no utilizado actualmente" (no importado por scripts, pero podrá
> usarse) ≠ "descartado metodológicamente" (se decidió no usarlo con justificación) ≠
> "no necesario para el flujo final" (función documental) ≠ "pendiente de evaluación"
> (enriquecimiento opcional D3 del diseño).

**Versiones originales (sin sufijo `_limpio`):** todas las del apartado A son fuentes y **no se
tocan**. No son "CSV sobrantes"; son los insumos de donde salen las versiones limpias.

---

## 10. Dataset final para minería

> **El dataset final todavía no está formalmente consolidado.**

- **Candidato actual (por diseño):** tabla **T1 `empleos`** → ruta prevista
  `data/procesado/empleos.parquet` (también se escribe como `empleos.csv` si se prefiere).
- **Origen:** generado por el futuro script `cruzar_datos.py` a partir únicamente de
  `data/limpio/`.
- **Columnas previstas (11):** `resume_id`, `start_date`, `end_date`, `university_level`,
  `matched_code`, `emparejado`, `occupation_code`, `occupation_label`, `isco_group`,
  `isco_group_label`, `isco_level`.
- **Filas previstas:** 1.506.445 (misma cantidad que JobHop limpio; los merges son N:1 y
  no expanden filas) — comprobable con las validaciones V1–V7 de `CIERRE_DISEÑO.md`.
- **Datasets que participan en su construcción:** JobHop limpio, `occupations_en_limpio`,
  `ISCOGroups_en_limpio` (obligatorios); `occupationSkillRelations`, `skills`,
  `greenShareOcc` (solo si se enriquecen las ocupaciones en T2, no expanden T1).
- **Datasets que NO participan:** el resto de ESCO (ver sección 9) y OLE.
- **Por qué es el adecuado:** conserva la unidad de análisis (1 fila = 1 empleo), incluye la
  identidad de la ocupación y su área ISCO-08 (base para minería de transiciones), y deja
  trazada la calidad del emparejamiento (`emparejado`).

**Qué falta para consolidarlo:**
1. Implementar `script/cruzar_datos.py` según el orden fijo de `CIERRE_DISEÑO.md` §8.
2. Ejecutar las validaciones V1–V15 y confirmar `len(T1) == 1.506.445`.
3. Definir pendientes D1–D4 (tratamiento de `unknown` en secuencias, empleos simultáneos,
   flags temáticos, ruta de salida).

---

## 11. Datos descartados y por qué

| Dato descartado | Tipo de descarte | Razón |
|---|---|---|
| 58.312 filas de JobHop sin `start_date` | Eliminadas en limpieza | No se puede ubicar el empleo en la trayectoria |
| 36.249 filas duplicadas de JobHop | Eliminadas en limpieza | Fila completa idéntica = misma experiencia repetida |
| `matched_code == 'unknown'` (**104.993 filas, 6,97%**) | Clasificado aparte, no descartado aún | Sin ocupación identificable; no es rescatable; decisión D1 pendiente |
| 16 códigos sin match directo | Recuperados parcialmente (prefijo ISCO, 10.176 filas) | No descartados: se conservan a nivel de área |
| Columnas 100% nulas (p. ej. `ISCOGroups.altLabels`) | Eliminadas en limpieza | Sin información |
| Duplicados por clave en ESCO (−4 occupations, −21 skills) | Eliminados en limpieza | Idénticos salvo `modifiedDate` |
| `skillSkillRelations`, `broaderRelations*`, `skillGroups`, `skillsHierarchy`, colecciones, `researchOccupations`, `conceptSchemes`, `dictionary` | No usados en la integración | Ver sección 9 |

---

## 12. Veredicto sobre el conjunto de columnas reportado por el compañero

- El conjunto de 11 columnas **es correcto como diseño** y corresponde íntegramente a la
  tabla T1 `empleos`.
- **NO VERIFICADO:** que "actualmente parece funcionar correctamente". No existe ningún
  archivo generado con esas columnas (`data/procesado/` está vacío) ni código que ejecute el
  cruce. Lo que sí está verificado es la **viabilidad** del cruce (coberturas R1, R2, R6,
  R3–R5 reproducidas al 100% en esta auditoría).
- Conclusión operativa: esas columnas **son las que deben producirse** en la siguiente etapa,
  no datos ya disponibles.

---

## 13. Evidencias y método de la auditoría

| Afirmación | Evidencia |
|---|---|
| `data/procesado/` vacío | Listado de directorio y `git ls-files` (la carpeta no aparece versionada) |
| No hay merges/joins implementados | búsqueda `merge\|join\|concat` en `.py` e `.ipynb` (0 resultados) |
| Cifras de cobertura R1/R2/R6/R3-R5 | Script de verificación ejecutado en esta auditoría sobre `data/limpio/` |
| Columnas de cada archivo limpio | `pd.read_csv(..., dtype=str)` / `read_parquet` sobre cada archivo |
| Clasificación A–F | Inspección de `limpiar_datos.py`, `Lectura.ipynb`, `tablas.ipynb` y documentos de diseño |
| OLE sin archivos | Búsqueda de archivos CSV (`glob`) y menciones en markdown (solo referencias textuales) |

---

## 14. Datasets limpios recomendados para las siguientes etapas

| Prioridad | Dataset | Rol |
|---|---|---|
| Obligatorio | `data/limpio/JobHop_v2_train_limpio.parquet` | Base de trayectorias |
| Obligatorio | `data/limpio/ESCO/occupations_en_limpio.csv` | Traducción código → ocupación + grupo ISCO |
| Obligatorio | `data/limpio/ESCO/ISCOGroups_en_limpio.csv` | Etiquetas de áreas ISCO-08 |
| Enriquecimiento | `data/limpio/ESCO/occupationSkillRelations_en_limpio.csv` y `skills_en_limpio.csv` | Perfil de skills por ocupación (agregado) |
| Enriquecimiento (opcional) | `data/limpio/ESCO/greenShareOcc_en_limpio.csv` | Indicador verde por área |
| Resto | — | Ver sección 9 (no requeridos para el flujo principal) |