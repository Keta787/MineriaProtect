# Diseño de integración de datos — Minería de Protección (trayectorias laborales)

> **Etapa:** diseño de integración (previa a la implementación del cruce).
> **Entrada exclusiva:** `data/limpio/`. **No** se ejecutó ningún JOIN definitivo, **no** se creó `cruzar_datos.py`, **no** se generaron las tablas finales integradas y **no** se modificó ningún dataset.
> **Regla clave:** 1 fila de JobHop = 1 experiencia laboral. Ninguna relación 1:N puede convertirse en filas adicionales de empleo.

---

## 0. Confirmación de entradas

### Archivos encontrados en `data/limpio/` (20)

| # | Archivo | Filas | Cols |
|---|---|---|---|
| 1 | `JobHop_v2_train_limpio.parquet` | 1.506.445 | 5 |
| 2 | `ESCO/occupations_en_limpio.csv` | 3.039 | 15 |
| 3 | `ESCO/ISCOGroups_en_limpio.csv` | 619 | 7 |
| 4 | `ESCO/occupationSkillRelations_en_limpio.csv` | 126.051 | 6 |
| 5 | `ESCO/skills_en_limpio.csv` | 13.939 | 13 |
| 6 | `ESCO/greenShareOcc_en_limpio.csv` | 3.590 | 5 |
| 7 | `ESCO/skillSkillRelations_en_limpio.csv` | 5.818 | 5 |
| 8 | `ESCO/broaderRelationsOccPillar_en_limpio.csv` | 3.648 | 6 |
| 9 | `ESCO/broaderRelationsSkillPillar_en_limpio.csv` | 20.819 | 6 |
| 10 | `ESCO/skillGroups_en_limpio.csv` | 640 | 11 |
| 11 | `ESCO/skillsHierarchy_en_limpio.csv` | 640 | 14 |
| 12 | `ESCO/digitalSkillsCollection_en_limpio.csv` | 1.284 | 10 |
| 13 | `ESCO/greenSkillsCollection_en_limpio.csv` | 629 | 10 |
| 14 | `ESCO/languageSkillsCollection_en_limpio.csv` | 359 | 10 |
| 15 | `ESCO/transversalSkillsCollection_en_limpio.csv` | 95 | 10 |
| 16 | `ESCO/researchSkillsCollection_en_limpio.csv` | 40 | 10 |
| 17 | `ESCO/digCompSkillsCollection_en_limpio.csv` | 25 | 10 |
| 18 | `ESCO/researchOccupationsCollection_en_limpio.csv` | 122 | 8 |
| 19 | `ESCO/conceptSchemes_en_limpio.csv` | 20 | 7 |
| 20 | `ESCO/dictionary_en_limpio.csv` | 160 | 4 |

### Archivos que se usarán como entrada en esta etapa

| Entradas | Archivos | Rol |
|---|---|---|
| **Centrales** | JobHop, occupations, ISCOGroups, occupationSkillRelations, skills | Constituyen el núcleo del diseño |
| **Enriquecimiento** | greenShareOcc (+ opcionales: colecciones temáticas de skills) | Aportan indicadores de caracterización |
| **Referencia** | dictionary, conceptSchemes | Solo documentación de columnas; no participan en JOINS |

### Archivos de uso limitado o no, y por qué

| Archivo | Decisión | Justificación observada |
|---|---|---|
| `skillSkillRelations` | No (fase posterior) | Red N:M entre skills (5.818 aristas, 95% `optional`). Solo útil para análisis de red, no para la integración principal |
| `broaderRelationsSkillPillar`, `skillGroups`, `skillsHierarchy` | No | Taxonomía ISCED-F de grupos de skills, pero **no existe en `data/limpio/` el borde skill→grupo** (no se puede clasificar cada skill en un área con los archivos disponibles) |
| `broaderRelationsOccPillar` | No ahora | La jerarquía ISCO-08 se deriva por **prefijo del código** (más simple y verificable); la pillar queda como alternativa/validación, no como entrada |
| Colecciones de skills (6) | Opcional | Son subconjuntos 100% contenidos en `skills`; añaden *flags* temáticos (digital/green/transversal) pero no cambian la relación central |
| `researchOccupationsCollection` | No | Solo 122 ocupaciones de I+D, subconjunto de `occupations`; no aporta al objetivo general |
| `conceptSchemes`, `dictionary` | No (solo lectura) | Metadatos; no relacionables con trayectorias |

**Nota:** todos los archivos están en `data/limpio/`. `data/original/` no fue tocado ni leído como insumo; la limpieza previa se da por hecha (`JobHop_v2_train_limpio.parquet` se usa tal cual, sin re-limpiar).

---

## 1. Inventario detallado

> Tipos: en los CSV limpios todas las columnas son **texto (`str`)**; el indicador numérico `greenShare` también se guarda como texto. En el parquet, `resume_id` es `int64` y el resto texto.

### 1.1 JobHop_v2_train_limpio.parquet — 1.506.445 × 5

| Columna | Tipo | Nulos | Únicos | Ejemplo |
|---|---|---|---|---|
| resume_id | int64 | 0 | 284.247 | 0 |
| matched_code | str | 0 | 2.983 | 3512.1 |
| start_date | str | 0 | 227 | Q1 2000 |
| end_date | str | 0 | 227 | Q1 2002 |
| university_level | str | 0 | 5 | Master |

Registros representativos:

```
resume_id  matched_code  start_date  end_date  university_level
       0        3512.1     Q1 2000    Q1 2002             Master
       0        3512.2     Q1 2002    Q1 2004             Master
       0        4222.1     Q1 2004    Q4 2007             Master
```

**Descripción:** cada fila = una experiencia laboral. Las fechas son **trimestres** (Q1..Q4 + año). Hay 284.247 personas; media 5,3 y máximo 20 empleos por persona. `university_level`: Secondary school 590.624 / Bachelor 515.463 / Master 219.884 / None 174.036 / PhD 6.438.

### 1.2 occupations_en_limpio.csv — 3.039 × 15

| Columna | Tipo | Nulos | Únicos | Ejemplo |
|---|---|---|---|---|
| conceptType | str | 0 | 1 | Occupation |
| conceptUri | str | 0 | 3.039 | …/esco/occupation/00030d0… |
| iscoGroup | str | 0 | 426 | 2654 |
| preferredLabel | str | 0 | 3.039 | technical director |
| altLabels | str | 0 | 3.039 | director of technical arts… |
| hiddenLabels | str | 3.031 | 8 | sexual health consultant… |
| status | str | 0 | 1 | released |
| modifiedDate | str | 0 | 2.898 | 2024-01-25T11:28:50Z |
| regulatedProfessionNote | str | 0 | 2 | …/regulated-professions/unregulated |
| scopeNote | str | 2.730 | 274 | Excludes people performing… |
| definition | str | 3.031 | 8 | Excludes choreologist. |
| inScheme | str | 0 | 2 | …/concept-scheme/member-occupations,… |
| description | str | 0 | 3.039 | Technical directors realise… |
| code | str | 0 | 3.039 | 2654.1.7 |
| naceCode | str | 0 | 1.121 | …/nace2.1/9031 |

**Descripción:** catálogo de ocupaciones ESCO. `code` es el código ocupacional (ej. `2654.1.7` = grupo `2654` + subclasificación). **Todos** los `iscoGroup` son códigos ISCO de 4 dígitos (grupo/unidad). `naceCode` es una **URI** a NACE (no un nombre de sector).

### 1.3 ISCOGroups_en_limpio.csv — 619 × 7

| Columna | Tipo | Únicos | Ejemplo |
|---|---|---|---|
| conceptType | str | 1 | ISCOGroup |
| conceptUri | str | 619 | …/esco/isco/C0 |
| code | str | 619 | 0 |
| preferredLabel | str | 582 | Armed forces occupations |
| status | str | 1 | released |
| inScheme | str | 1 | … |
| description | str | 619 | Armed forces occupations include… |

**Descripción:** clasificación ISCO-08 completa (códigos de 1, 2, 3 y 4 dígitos: gran grupo `0`, sub‑grupo `01`, grupo menor `011`, grupo de base/unidad `0110`). La jerarquía se lee por **prefijo del código** (sin duplicados).

### 1.4 occupationSkillRelations_en_limpio.csv — 126.051 × 6

| Columna | Tipo | Nulos | Únicos | Ejemplo |
|---|---|---|---|---|
| occupationUri | str | 0 | 3.039 | …/esco/occupation/00030d0… |
| occupationLabel | str | 0 | 3.039 | technical director |
| relationType | str | 0 | 2 | essential |
| skillType | str | 59 | 2 | knowledge |
| skillUri | str | 0 | 13.475 | …/esco/skill/fed5b267… |
| skillLabel | str | 0 | 13.475 | theatre techniques |

**Descripción:** tabla **puente 1 ocupación → N skills** (media 41,5 skills/ocupación; min 7, máx 178). 3.039/3.039 ocupaciones tienen al menos una relación. `relationType`: essential 67.600 / optional 58.451. `skillType`: skill/competence 91.608 / knowledge 34.384 / 59 NaN.

### 1.5 skills_en_limpio.csv — 13.939 × 13

| Columna | Tipo | Nulos | Únicos | Ejemplo |
|---|---|---|---|---|
| conceptType | str | 0 | 1 | KnowledgeSkillCompetence |
| conceptUri | str | 0 | 13.939 | …/esco/skill/0005c15… |
| skillType | str | 5 | 2 | skill/competence |
| reuseLevel | str | 5 | 4 | sector-specific |
| preferredLabel | str | 0 | 13.939 | manage musical staff |
| altLabels | str | 18 | 13.918 | manage music staff… |
| hiddenLabels | str | 13.786 | 153 | active participation… |
| status / modifiedDate | str | 0 | 1 / 2.648 | released |
| scopeNote / definition | str | 13.704 / 13.937 | 224 / 2 | … |
| inScheme | str | 0 | 15 | … |
| description | str | 0 | 13.935 | Assign and manage staff… |

**Descripción:** catálogo de skills/conocimientos. `reuseLevel` (distribución): transversal 452, cross-sector 3.783, sector-specific 6.655, occupation-specific 3.044 (+5 NaN). Es **el indicador de especialización** de un empleo.

### 1.6 greenShareOcc_en_limpio.csv — 3.590 × 5

| Columna | Tipo | Únicos | Ejemplo |
|---|---|---|---|
| conceptType | str | 3 ('ISCO level 3', 'ISCO level 4', 'Occupation') | ISCO level 4 |
| conceptUri | str | 3.590 | …/esco/isco/C011 |
| code | str | 3.590 | 0110 |
| preferredLabel | str | 3.566 | Commissioned armed forces officers |
| greenShare | str | 725 | 0.005753968… |

**Descripción:** proporción "verde" por grupo ISCO/ocupación (rango 0–0,72). A nivel **4 dígitos hay 426 códigos = el conjunto exacto de `occupations.iscoGroup`** (cobertura 426/426, 100%).

### 1.7 Resto de tablas (estructura + ejemplos)

- **skillSkillRelations 5.818×5**: originalSkillUri(3.759 únicos), originalSkillType, relationType(optional 5.629 / essential 189), relatedSkillType, relatedSkillUri(1.953). Ej: `…/skill/0006473… | skill/competence | optional | knowledge | …/skill/d4a0744…`.
- **broaderRelationsOccPillar 3.648×6**: conceptUri(isco/C01), conceptLabel, broaderUri(isco/C0), broaderLabel — aristas padre→grupo de la jerarquía ISCO. Ej: *Commissioned armed forces officers* → *Armed forces occupations*.
- **broaderRelationsSkillPillar 20.819×6**: conceptUri(isced-f/00), broaderUri(skill/…) — jerarquía de skill groups.
- **skillGroups 640×11**: conceptUri(isced-f/00), code('00','000'), preferredLabel('generic programmes…'), description… — grupos de skills.
- **skillsHierarchy 640×14**: Level 0 URI/term/code ('L'), Level 1 ('L1'), Level 2 ('S6.13'), Level 3 ('S6.13.2'), descripción — árbol de skill groups.
- **Colecciones**: digital 1.284 / green 629 / language 359 / transversal 95 / research 40 / digComp 25 — columnas: conceptUri, preferredLabel, status, skillType, reuseLevel, altLabels, description, broaderConceptUri, broaderConceptPT. Todas 100% subconjuntos de `skills.conceptUri`.
- **researchOccupationsCollection 122×8**: ocupaciones de I+D (biomedical engineer, criminologist…).
- **conceptSchemes 20×7**: Digital, Research occupations… (metadatos).
- **dictionary 160×4**: filename, data header, property, description — **glosario de columnas del paquete ESCO** (documentación oficial).

---

## 2. Función de cada tabla

| Archivo | Función | Papel |
|---|---|---|
| JobHop | **Trayectoria laboral** | Tabla central; 1 fila = 1 empleo; unidad de análisis del proyecto |
| occupations | **Catálogo de ocupaciones** | Diccionario code→concepto; une a JobHop y da grupo ISCO |
| ISCOGroups | **Clasificación ISCO-08** | Da el "área ocupacional" y su jerarquía (prefijos) |
| occupationSkillRelations | **Relación ocupación–skill** | Puente 1:N que conecta empleos con skills |
| skills | **Catálogo de skills** | Perfil de competencias requeridas; `reuseLevel` = especialización |
| greenShareOcc | **Indicador auxiliar** | Proporción verde por grupo ISCO |
| skillSkillRelations | Relaciones auxiliares (red) | Fase posterior (análisis de red de skills) |
| broaderRelations*Pillar | Jerarquías auxiliares | Alternativa de árbol; redundante con prefijos ISCO |
| skillGroups / skillsHierarchy | Taxonomía de grupos de skills | Sin borde skill→grupo en limpio → no utilizable ahora |
| Colecciones (6) | Colecciones temáticas | Flags opcionales (digital/green/transversal) sobre skills |
| researchOccupations | Colección temática | Dominio I+D; fuera del objetivo general |
| conceptSchemes / dictionary | Metadatos | Documentación, no insumo de joins |

Regla aplicada: **no se asume utilidad por poder técnicamente relacionar**; cada tabla se clasifica por su papel frente a las preguntas de investigación.

---

## 3. Variables importantes

| Archivo | Variable | Tipo | Función | Importancia | Justificación |
|---|---|---|---|---|---|
| JobHop | resume_id | int64 (id) | Persona/identidad de trayectoria | Esencial | Necesaria para reconstruir la secuencia de empleos de cada persona |
| JobHop | matched_code | str (código) | Ocupación codificada | Esencial | Es la llave a `occupations.code`: conexión con ESCO |
| JobHop | start_date | str (trimestre) | Inicio del empleo | Esencial | Orden temporal, primer empleo, duración |
| JobHop | end_date | str (trimestre) | Fin del empleo | Esencial | Duración; final de empleo para la transición |
| JobHop | university_level | str (categórica) | Nivel educativo | Esencial | Única variable socio‑demográfica; base de "congruencia de nivel" |
| occupations | code | str (código) | Llave ocupacional | Esencial | Match directo con `matched_code` (99,4% de códigos) |
| occupations | conceptUri | str (URI) | Llave interna ESCO | Esencial | Une con `occupationSkillRelations.occupationUri` |
| occupations | iscoGroup | str (código 4 díg.) | Grupo ISCO-08 | Esencial | Define el área ocupacional y el nivel de jerarquía |
| occupations | preferredLabel | str (texto) | Nombre de la ocupación | Esencial | Lectura e interpretación de resultados |
| occupations | altLabels | str (texto) | Sinónimos | Potencial | Validación/lectura; no interviene en joins |
| occupations | naceCode | str (URI) | Sector NACE | No prioritaria | Es una URI; extraer el sector exige mapeo NACE (información externa, prohibida en esta etapa) |
| occupations | hiddenLabels / definition / status / inScheme / modifiedDate | str | Etiquetas ocultas / constantes | No prioritarias | Casi nulas o casi constantes; sin poder discriminativo |
| occupations | scopeNote / description | str | Notas | Potencial | Solo lectura humana (90% de scopeNote nulo) |
| ISCOGroups | code | str (código) | Grupo ISCO (1–4 díg.) | Esencial | Llave con `occupations.iscoGroup`; **prefijo = nivel jerárquico** |
| ISCOGroups | preferredLabel | str (texto) | Nombre del grupo/área | Esencial | Etiqueta el área ocupacional (gran grupo, sub‑grupo…) |
| ISCOGroups | description | str | Definición oficial | Potencial | Contexto cualitativo |
| relations | occupationUri | str (URI) | Ocupación | Esencial | Llave a occupations.conceptUri (100% de cobertura) |
| relations | skillUri | str (URI) | Skill | Esencial | Llave a skills.conceptUri (100% de las 13.475 referenciadas) |
| relations | relationType | str (essential/optional) | Peso de la skill | Esencial | Distingue habilidades obligatorias vs opcionales |
| relations | skillType | str | Competencia vs conocimiento | Esencial | Caracteriza el tipo de exigencia (59 NaN, 0,05%) |
| relations | occupationLabel / skillLabel | str (texto) | Denominalizaciones | Potencial | Conveniencia de lectura; redundantes (fuentes: occupations/skills) |
| skills | conceptUri | str (URI) | Llave | Esencial | Une con relation.skillUri |
| skills | preferredLabel | str | Nombre del skill | Esencial | Interpretación |
| skills | reuseLevel | str | Transversalidad | Esencial | **Proxy de especialización del empleo** (transversal=sencillo, occupation‑specific=especializado) |
| skills | skillType | str | Competencia vs conocimiento | Esencial | Complementa el perfil de exigencia |
| skills | scopeNote / definition | str | Notas | Potencial | Lectura (mayormente nulas) |
| skills | hiddenLabels / status / modifiedDate | str | Constantes/nulas | No prioritarias | Sin poder discriminativo |
| greenShareOcc | code | str (4 díg.) | Grupo ISCO | Potencial | Llave con occupations.iscoGroup (426/426) |
| greenShareOcc | greenShare | str (→float) | Proporción verde | Potencial | Índice de "verdor" del área; caracteriza ocupaciones destino |
| Colecciones | conceptUri | str (URI) | Skill etiquetado | Potencial | Flags temáticos opcionales (digital/green/transversal) |
| skillSkillRelations | todas | str (URI) | Relaciones skill–skill | No prioritarias | Red para una fase posterior de análisis de network |

---

## 4. Preguntas del proyecto → variables

| Pregunta | ¿Puede responderse? | Variables necesarias | Archivo | Cruce/transformación | Limitaciones |
|---|---|---|---|---|---|
| ¿Cuál fue el primer empleo? | Sí (aproximado) | resume_id, matched_code, start_date | JobHop + occupations (label) | `matched_code→code` (N:1); orden por `start_date` | Siempre hay fechas de inicio; con traslapes el "primero" requiere regla de desempate |
| ¿Qué ocupaciones aparecen después? | Sí | resume_id, matched_code, start_date, end_date | JobHop + occupations | Mismo cruce + orden temporal | No hay motivo del cambio (¿voluntario/despido?) |
| ¿Cuántos empleos por persona? | Sí | resume_id | JobHop | conteo por persona | Directo (0–20 empleos) |
| ¿Cuánto tiempo en una ocupación? | Sí (aproximado) | resume_id, matched_code, start_date, end_date | JobHop | duración entre trimestres | Granularidad trimestral; traslapes entre empleos |
| ¿Qué ocupaciones suceden a otras? | Sí | resume_id, matched_code, start_date | JobHop + occupations | construir secuencias; emparejar (ocup_anterior, ocup_actual) | Requiere definir regla de secuencia ante traslapes y empleos simultáneos |
| ¿Transiciones más frecuentes? | Sí | ídem | derivada de secuencias | minería de transiciones (fase posterior) | Depende de la regla de orden elegida |
| ¿La persona permanece en la misma área? | Sí | iscoGroup | occupations + ISCOGroups | `iscoGroup→code` (N:1); comparar grupo entre empleos | "Área" = grupo ISCO (4 díg.) o nivel superior derivado por prefijo |
| ¿Cuándo se produce un cambio de área? | Sí (aproximado) | iscoGroup, start_date/end_date | occupations + ISCOGroups + JobHop | timestamp del cambio de grupo | Cambio de área de 4 dígitos ≠ cambio de gran grupo (1 dígito) |
| ¿Relación university_level ↔ ocupaciones? | Sí, **parcial** | university_level, iscoGroup, ocupación | JobHop + occupations | distribución de nivel por ocupación/grupo | Solo nivel, **no campo de estudio** (ver Limitaciones) |
| ¿Diferencias de trayectoria por nivel educativo? | Sí, **parcial** | resume_id, university_level, matched_code | JobHop + occupations | resúmenes por university_level | No hay cohorte temporal ni causa de transición |
| ¿Qué grupo ISCO corresponde a cada ocupación? | Sí | iscoGroup → code | occupations + ISCOGroups | N:1 direto, 426/426 (100%) | Sin limitación (0 nulos) |
| ¿Características de las ocupaciones destino? | Sí | relationType, skillType, reuseLevel, greenShare | relations + skills (+ greenShare) | agregado por ocupación (N:1 hasta el empleo) | El perfil es de la ocupación, no de la persona |
| ¿Qué skills exige cada ocupación? | Sí | occupationUri, skillUri | relations + skills | `occupationUri→conceptUri`, `skillUri→conceptUri` (100%) | Ninguna a nivel ocupación |

---

## 5. Mapa de relaciones (verificado con datos)

| Relación | Tabla A → columna | Tabla B → columna | Tipo | Cobertura real | Riesgo de multiplicación |
|---|---|---|---|---|---|
| R1 | JobHop → `matched_code` | occupations → `code` | **N:1** | 2.966/2.983 códigos (99,4%); **92,35% de filas** (1.391.276/1.506.445) | Ninguno (1 ocupación/empleo) |
| R2 | occupations → `iscoGroup` | ISCOGroups → `code` | **N:1** | 426/426 grupos (100%); 0 sin | Ninguno |
| R3 | occupations → `conceptUri` | relations → `occupationUri` | **1:N** | 3.039/3.039 ocupaciones (100%); media 41,5 skills | **ALTO si se expande en filas de empleo** (→ Control de cardinalidad) |
| R4 | relations → `skillUri` | skills → `conceptUri` | **N:1** | 13.475/13.475 skills (100%); 0 sin | Ninguno (la N ya está en R3) |
| R5 | occupations → `iscoGroup` | greenShareOcc → `code` (4 díg.) | **N:1** | 426/426 (100%); greenShare 0–0,72 | Ninguno |
| R6 | **Rescate**: JobHop `matched_code[:4]` → ISCOGroups `code` | **N:1** | 16 códigos sin match con prefijo ISCO válido → **10.176 filas recuperables** | Ninguno |
| R7 | Colecciones → `conceptUri` | skills → `conceptUri` | **N:1** (subconjunto) | 100% de cada colección ⊆ skills | Ninguno (flag por skill) |
| R8 | skills → `conceptUri` | `skillSkillRelations` (original→related) | **N:M** | red 5.818 aristas; 3.759 orig / 1.953 dest | Alto solo si se explota la red (no en esta fase) |
| R9 | skills → grupos | skillGroups/skillsHierarchy | — | **Sin borde skill→grupo disponible** en `data/limpio/` | No aplica |
| R10 | occupations → `naceCode` | NACE (externa) | N:1 | URI sin mapeo interno | Rechazada por regla de "no info externa" |

**Valores sin correspondencia (R1):** 17 códigos sin match = 115.169 filas (7,65%). De ellas: `unknown` = **104.993 filas (91,2% de las no‑emparejadas, no recuperables)** y 16 códigos con prefijo ISCO-08 válido = **10.176 filas recuperables** a nivel de grupo. Detalle de los 17: `unknown`, `2131.4.12`, `2131.8`, `2131.8.1`, `2131.8.2`, `2131.4.3`, `2424.3`, `2659.2.2`, `3214.2`, `3214.3.1`, `3251.2`, `3311.2.2`, `3412.4.9`, `4229.1`, `5153.1.1`, `7215.4`, `7514.1`.

---

## 6. Cruces adicionales (más allá de los obvios)

| Cruce nuevo | Justificación (ligada al objetivo) | Verificación |
|---|---|---|
| **Rescate por prefijo ISCO** (matched_code 4 primeros dígitos → ISCOGroups) | No perder 10.176 empleos; conservarlos al menos a nivel de área | 16/17 códigos recuperables |
| **Nivel jerárquico ISCO por longitud de código** (1=gran grupo, 2=sub‑grupo, 3=g, 4=unidad) | Respuesta fina a "¿cambia de *área*?" en distintos niveles de agregación | 619 códigos; occupations todos de 4 dígitos |
| **Perfil de skills por ocupación** (agregado R3+R4) | Caracterizar las ocupaciones de destino (objetivo explícito) | 3.039/3.039 cubiertas |
| **Especialización por reuseLevel** (transversal vs occupation‑specific) por ocupación | Distinguir empleos "genéricos" de "especializados" en trayectorias | 4 categorías, 13.934 skills con dato |
| **Indicador verde por grupo ISCO** (R5) | Caracterizar la dirección de las transiciones (hacia áreas verdes o no) | 426/426 grupos |
| **Flags temáticos de skills** (colecciones → R7) | Enriquecer el perfil de skills (digital/green/transversal) | 100% subconjuntos |

Se descartaron por no aportar al objetivo central: la red skill–skill (R8, fase de network), la taxonomía ISCED-F (R9, sin borde utilizable), la colección de ocupaciones de I+D (dominio específico) y el sector NACE (R10, exige información externa).

---

## 7. Evaluación de cada cruce

| Cruce | Llave | Qué aporta | Cardinalidad | Riesgo dup. | Pregunta que responde | Utilidad |
|---|---|---|---|---|---|---|
| JobHop → occupations | matched_code = code | Nombre y grupo ISCO de cada empleo | N:1 | Ninguno | ¿Qué ocupaciones tiene cada trayectoria? | **Alta** |
| occupations → ISCOGroups | iscoGroup = code | Área ocupacional y su jerarquía | N:1 | Ninguno | ¿La persona permanece en el mismo área? | **Alta** |
| occupations → relations → skills (agregado) | conceptUri = occupationUri = skillUri = conceptUri | Perfil de skills y especialización por ocupación | 1:N (→agregación) | **Alto si se expande** | ¿Características de las ocupaciones destino? | **Alta** (solo agregado) |
| Rescate matched_code[:4] → ISCOGroups | prefijo = code | Recupera 10.176 filas a nivel grupo | N:1 | Ninguno | ¿Qué ocupación/grupo tenía el empleo? | **Media** |
| iscoGroup → greenShare | code = code | Índice verde por área | N:1 | Ninguno | ¿Hacia áreas verdes o no? | **Media** |
| Colecciones → skills | conceptUri = conceptUri | Flags temáticos de skills | N:1 (subset) | Ninguno | ¿Qué tipos de skills exige la ocupación? | **Media** |
| skills → skillSkillRelations | conceptUri = originalSkillUri | Red de skills | N:M | Alto (grafo) | ¿Cómo se relacionan los skills entre sí? | **Baja (fase posterior)** |
| occupations → skillGroups | — | Clasificar skills por ISCED-F | Sin borde | No aplica | ¿Área de skill? | **Inutilizable hoy** |
| occupations → naceCode → NACE | URI | Sector económico | N:1 | Incierto | ¿En qué sector se mueve? | **Descartada (info externa)** |

**Criterio aplicado:** un cruce se mantiene solo si responde una pregunta que no puede responderse con una sola tabla. Por eso se descartan los cruces puramente "técnicamente posibles" (R8, R9, R10, colección de I+D).

---

## 8. Control de cardinalidad

**Unidad de análisis a preservar:** 1 fila de JobHop = 1 experiencia laboral.

- **R3 es la única relación problemática**: 1 ocupación → ~41,5 skills (min 7, máx 178). Convertir cada skill en fila de empleo **multiplicaría ~41 veces** las 1,5 M filas → prohibido.
- **Solución (la más adecuada metodológicamente): doble vía**:
  1. **Tabla agregada `ocupacion_skills`** (1 fila por ocupación): conteos y proporciones por `relationType`, `skillType` y `reuseLevel`. Se une al empleo en N:1 → el perfil de skills se convierte en **atributo de la ocupación**, no en filas extra. *Alternativa recomendada*: conserva la unidad de análisis y permite características numéricas.
  2. **Tabla puente `occupationSkillRelations` tal cual** (ya existe en `data/limpio/`): para consultas exploratorias skill‑céntricas, sin tocar las filas de empleo. *Puente en lugar de denormalización*.
- **Las demás relaciones son N:1 o 1:N con destino de agregación** → sin multiplicación de filas de JobHop.
- **Riesgo residual propio de JobHop** (no de los cruces): pueden existir empleos con fechas traslapadas por persona (empleos simultáneos). Al implementar habrá que verificar unicidad del par `(resume_id, start_date, end_date)` y decidir una regla de desempate para "primer empleo"/secuencias.

---

## 9. Diseño de las tablas finales (propuesta, sin implementar)

### T1. `empleos` (1 fila = 1 experiencia laboral)

| Columna | Fuente | Tipo |
|---|---|---|
| resume_id | JobHop | int64 (PK parcial) |
| start_date, end_date | JobHop | trimestre |
| university_level | JobHop | categórica |
| matched_code (bruto) | JobHop | código |
| occupation_code | occupations.code (por R1) | código |
| occupation_label | occupations.preferredLabel | texto |
| isco_group | occupations.iscoGroup (R1/R2) o prefijo (rescate R6) | 4 dígitos |
| isco_group_label | ISCOGroups.preferredLabel | texto |
| isco_level | ISCOGroups (largo de code) | 1/2/3/4 |
| emparejado | derivada (R1 ok / rescatado / unknown) | categoría |

- **PK**: compuesta `(resume_id, matched_code, start_date, end_date)` **a verificar**; si hay duplicados, añadir índice de fila.
- **FK**: `occupation_code→occupations.code`; `isco_group→ISCOGroups.code`.
- **Respuestas**: todas las preguntas de trayectoria y transición, con la ocupación y su área.

### T2. `ocupaciones` (1 fila = 1 ocupación ESCO; perfil enriquecido)

| Columna | Fuente |
|---|---|
| occupation_code, conceptUri, preferredLabel, iscoGroup | occupations |
| isco_group_label, isco_level | ISCOGroups (R2) |
| n_empleos (frecuencia en JobHop, R1) | derivada |
| n_skills, n_essential, n_optional, n_knowledge, n_skill_competence | relations agregadas (R3) |
| n_transversal, n_cross_sector, n_sector_specific, n_occupation_specific, %x | skills.reuseLevel agregadas (R4) |
| greenShare | greenShareOcc (R5) |
| (opcional) flags digital/green/transversal | colecciones (R7) |

- **PK**: `occupation_code` / `conceptUri`. **FK**: `iscoGroup→ISCOGroups.code`.
- **Respuestas**: características de las ocupaciones y de las de destino; especialización; verdor.

### T3. `grupos_isco` (dimensión; 1 fila = 1 código ISCO-08)

- `code` (1–4 dígitos), `preferredLabel`, `nivel` (por longitud), `code_gran_grupo`.
- **PK**: `code`. **FK**: referenciado por T1 y T2.
- **Respuestas**: agregación y lectura del "área" en 4 niveles.

### Tablas que NO se replicarán en la integración (permanecen en `data/limpio/`)

`occupationSkillRelations` (puente), colecciones (flags opcionales), `skillSkillRelations` (red posterior).

**Por qué se agrega `ocupaciones` en vez de aplanar:** resuelve R3 (41 skills → 1 fila), mantiene la unidad de análisis de JobHop y convierte el perfil de skills en atributo numérico usable en minería.

---

## 10. Limitaciones de los datos

**Lo que podemos medir directamente (hechos en los datos):** ocupación codificada, fechas trimestrales, nivel educativo, grupo ISCO de cada ocupación, perfil y especialización (`reuseLevel`) por ocupación, `essential/optional`, `skillType`, índice verde por área.

**Lo que podemos aproximar (inferencias justificadas):** duración por trimestre; orden de la trayectoria por `start_date`; "primer empleo" (inicio más temprano, con regla de desempate); cambio de área por cambio de grupo ISCO; especialización del empleo vía `reuseLevel`; congruencia de nivel (nivel individual vs distribución típica de la ocupación).

**Lo que NO podemos medir:**
- **Campo de estudio** (`university_level` solo es nivel → **no puede afirmarse que la persona trabaje en lo que estudió**).
- Motivo/causa de la transición (voluntario, despido, reubicación) — no existe en JobHop.
- Salario, empleador, jornada, motivo de simultaneidad/traslape de empleos.
- **Sector económico real** (NACE solo como URI, sin tabla de mapeo en `data/limpio/`).
- Skills demostradas por la persona (JobHop no registra skills individuales); solo skills exigidas por la ocupación.
- `unknown` (104.993 filas, ~7% del total) **no es rescatable** a nivel de ocupación.
- Conexión skill → grupo ISCED-F (no hay borde en los archivos limpios) → **no se puede clasificar skills por área temática interna**.

---

## 11. Hechos, inferencias y suposiciones

| Categoría | Afirmación |
|---|---|
| **Hecho** | matched_code → occupations.code empareja 92,35% de filas; occupations.iscoGroup→ISCOGroups 426/426; relations cubren 3.039/3.039 ocupaciones; 13.475 skillUri presentes en skills; reuseLevel transversal=452…; greenShare 426/426; university_level 5 valores |
| **Hecho** | todos los `iscoGroup` son códigos de 4 dígitos; ISCOGroups contiene códigos de 1–4 dígitos (jerarquía por prefijo); relationType essential 67.600 / optional 58.451 |
| **Hecho** | 17 códigos sin match; `unknown` concentra 104.993 de las 115.169 filas no emparejadas; 16 códigos con prefijo ISCO válido (10.176 filas recuperables) |
| **Inferencia** | `start_date` ordena la trayectoria (se asume que refleja la secuencia real; hay traslapes) |
| **Inferencia** | `reuseLevel` mide especialización del empleo (clasificación oficial ESCO) |
| **Inferencia** | empleo con muchas skills transversales = genérico; con occupation‑specific = especializado |
| **Suposición** | `university_level` es constante a lo largo de todo el resume (no está anotado por empleo) |
| **Suposición** | la muestra `train` es representativa de la población de trayectorias |
| **Suposición** | los empleos traslapados son empleos simultáneos (y no error de datos) |

*Ninguna inferencia/suposición se presenta como hecho verificado.*

---

## 12. Estado de la integración

Se ejecutaron **solo lecturas** de `data/limpio/` (inventarios, unicidades, coberturas, cardinalidades y ejemplos). **No** se generó `cruzar_datos.py`, **no** existen tablas finales (T1/T2/T3), **no** se ejecutó JOIN definitivo y **no** se modificó ningún dataset. Este documento es únicamente el diseño que, tras aprobación, se implementará.

---

## 13. Resultado final (A–J)

- **A. Inventario**: 20 datasets en `data/limpio/` (JobHop + 19 ESCO); función identificada en las secciones 0 y 2.
- **B. Variables relevantes**: codificadas en la sección 3 (esenciales/potenciales/no prioritarias).
- **C. Preguntas → variables**: tabla de la sección 4 (13 preguntas operativas, con solapamientos y límites marcados).
- **D. Mapa de relaciones**: sección 5 (R1–R10) con coberturas medidas y valores sin correspondencia detectados.
- **E. Cruces recomendados**: JobHop↔occupations (N:1), occupations↔ISCOGroups (N:1), occupations↔relations↔skills **agregado** (1:N→N:1), rescate por prefijo ISCO, iscoGroup↔greenShare, colecciones opcionales.
- **F. Cruces descartados**: skill↔skill (red, fase posterior), skill→skillGroups/ISCED-F (borde inexistente), NACE/naceCode (información externa), researchOccupationsCollection (dominio I+D), broaderRelations* como entrada (redundante con prefijos).
- **G. Diseño de tablas finales**: `empleos`, `ocupaciones` (perfil agregado), `grupos_isco` (dimensión) — sección 9.
- **H. Control de cardinalidad**: R3 es el único riesgo (×41); se resuelve con tablas **agregada + puente** sin tocar la unidad de análisis; el resto son N:1 sin riesgo.
- **I. Limitaciones**: sección 10 — destacan: sin campo de estudio (no congruencia carrera–empleo), sin causa de transición, ~7% de filas en `unknown`, sin skills de persona.
- **J. Orden recomendado de integración** (para implementar tras aprobación):
  1. Cargar catálogos limpios: `occupations`, `ISCOGroups`, `relations`, `skills`, `greenShareOcc`.
  2. R1: emparejar JobHop → occupations por `code` (dejar `emparejado` = ok/rescatado/unknown).
  3. R6: rescate de los 16 códigos por prefijo `matched_code[:4]` → `isco_group`.
  4. R2: `isco_group` → ISCOGroups (label y nivel por longitud).
  5. R3+R4: construir `ocupaciones` (agregado de skills por ocupación).
  6. R5: añadir `greenShare` por `isco_group`.
  7. R7 (opcional): flags temáticos de colecciones sobre skills y su agregado.
  8. Montaje de `empleos` (T1) uniendo paso a paso en N:1 (nunca expandir skills). El resultado de la minería (`transiciones`) es fase posterior.

**Pregunta clave para decidir antes de implementar:** en T1, ¿cómo tratar las 104.993 filas `unknown` — mantenerlas como categoría propia o excluirlas del análisis de transiciones?