# Auditoría y cierre del diseño de integración — Especificación implementable

> **Propósito:** especificación final que una IA/desarrollador pueda implementar **sin tomar decisiones metodológicas por su cuenta**.
> Complementa a `DISEÑO_INTEGRACION.md` (diseño conceptual). Este documento **cierra ambigüedades**, define reglas formales y establece verificaciones obligatorias.
> **Entrada exclusiva:** `data/limpio/`. **No** toca `data/original/`, no re-limpiar `JobHop_v2_train_limpio.parquet`, no genera tablas "finales" aquí (es contrato de implementación).

---

## 1. Definiciones formales

### 1.1 `reuseLevel` (skills)
- **Definición oficial** (diccionario ESCO limpio): "Reuseability level of a skill" (propiedad `http://data.europa.eu/esco/model#skillReuseLevel`).
- **Dominio observado** (13.934 de 13.939 con valor):
  | Valor | Significado operativo | n skills |
  |---|---|---|
  | `transversal` | Reutilizable en sectores y ocupaciones muy diversos | 452 |
  | `cross-sector` | Reutilizable entre sectores | 3.783 |
  | `sector-specific` | Reutilizable dentro de un sector | 6.655 |
  | `occupation-specific` | Casi exclusiva de la ocupación / ámbito reducido | 3.044 |
  | NaN | Sin clasificación | 5 |
- **Regla de uso:** es **indicador agregado** de ocupación; la lectura "más transversal = empleo más genérico" es **inferencia metodológica documentada**, no un hecho del dato.

### 1.2 `university_level` (JobHop)
- **Significado:** nivel educativo **más alto declarado en el CV** de la persona. **No** indica campo/formación concreta.
- **Dominio (exhaustivo, 0 nulos):** `Secondary school` (590.624), `Bachelor` (515.463), `Master` (219.884), `None` (174.036), `PhD` (6.438).
- **Regla de uso:** constante para toda la trayectoria de la persona (suposición a documentar). `None` = fila sin nivel declarado (categoría válida, no nulo).

### 1.3 `matched_code` y `emparejado`
Variable derivada `emparejado` (categoría, exhaustiva) definida por precedencia estricta:
1. si `matched_code == 'unknown'` → `emparejado = 'unknown'`.
2. si `matched_code ∈ occupations.code` → `emparejado = 'ok'`.
3. si `matched_code[:4] ∈ ISCOGroups.code` (códigos de 4 dígitos) → `emparejado = 'rescatado'`.
4. en cualquier otro caso → `emparejado = 'descartado'` (no debe existir; ver §4 validaciones).

### 1.4 Regla de rescate por prefijo ISCO (validada)
- **Hecho de validación:** en las 1.391.276 filas con match directo, `matched_code[:4] == occupations.iscoGroup` en el **100%** (0 inconsistencias). La regla de rescate es exactamente equivalente al mapeo real.
- **Regla:** si `emparejado == 'rescatado'`, `isco_group = matched_code[:4]`.
- **Resultados esperados (afirmación de test):**
  - `unknown`: **104.993** filas (de 115.169 sin match).
  - `rescatado`: **10.176** filas (16 códigos con prefijo ISCO válido).
  - `descartado`: 0 filas. Residuo sin match tras el rescate = 0 (además de `unknown`).

### 1.5 Orden temporal y traslapes
- **Conversión trimestre→entero:** `Q{n} yyyy` → `yyyy*4 + n`. Ej.: `Q3 2008` → 8035*. (Parseo bidireccional: token sin `Q` = año; token con `Q` = trimestre.)
- **Orden canónico (futuras secuencias):** `sort(resume_id, start_q, end_q, matched_code)` asc. Llave `(resume_id, matched_code, start_date, end_date)` es única (0 duplicados) → determinismo garantizado.
- **Política de traslapes (decisión tomada en esta auditoría):**
  - Los traslapes **no se eliminan, fusionan ni deduplican** en la integración: 1 fila = 1 experiencia real.
  - Un empleo que empieza antes de que termine otro = **empleo concurrente** (no una transición secuencial).
  - "Primer empleo" = mínimo `start_q`; desempate por máximo `end_q`, luego `matched_code`. 
  - Magnitudes medidas (se usan como afirmaciones de test): 291.014 filas (19,32%) empiezan antes del fin del empleo inmediatamente anterior; 349.758 (23,22%) antes del máximo fin ya visto; 142.300 personas (≈50%) con ≥1 traslape; 60.228 periodos idénticos duplicados (134.585 filas en grupos con misma `(resume_id, start_date, end_date)`).

---

## 2. Datos de entrada autorizados (solo `data/limpio/`)

| Alias | Archivo | Uso |
|---|---|---|
| `JH` | `JobHop_v2_train_limpio.parquet` | Tabla central (nunca re-limpiar) |
| `OCC` | `ESCO/occupations_en_limpio.csv` | Catálogo ocupaciones |
| `ISCO` | `ESCO/ISCOGroups_en_limpio.csv` | Clasificación ISCO-08 |
| `REL` | `ESCO/occupationSkillRelations_en_limpio.csv` | Puente ocupación–skill |
| `SK` | `ESCO/skills_en_limpio.csv` | Catálogo de skills |
| `GS` | `ESCO/greenShareOcc_en_limpio.csv` | Indicador verde (nivel 4 dígitos) |

Metadatos (no JOIN): `dictionary_en_limpio.csv`, `conceptSchemes_en_limpio.csv`.

---

## 3. Especificación de tablas finales

### T1 `empleos` — 1 fila = 1 experiencia laboral (sin multiplicación)

| Columna | Tipo | Origen | Fuente | Regla |
|---|---|---|---|---|
| resume_id | int64 | **original** | JH | copia directa |
| start_date | str | **original** | JH | copia directa |
| end_date | str | **original** | JH | copia directa |
| university_level | str | **original** | JH | copia directa |
| matched_code | str | **original** | JH | copia directa |
| emparejado | categorical | **derivada** | §1.3 | 'ok' / 'rescatado' / 'unknown' |
| occupation_code | str | **derivada** | §1.3 | = matched_code si 'ok'; NaN si no |
| occupation_label | str | **derivada** | OCC.preferredLabel | JOIN N:1 `occupation_code → OCC.code` |
| isco_group | str | **derivada** | §1.4 | 'ok'→OCC.iscoGroup; 'rescatado'→matched_code[:4]; 'unknown'→NaN |
| isco_group_label | str | **derivada** | ISCO.preferredLabel | JOIN N:1 `isco_group → ISCO.code` |
| isco_level | int | **derivada** | ISCO | = len(isco_group) (verificado: siempre 4 en T1) |

- **Llave primaria:** `(resume_id, matched_code, start_date, end_date)` — unicidad verificada (0 duplicados).
- **Llaves foráneas:** `occupation_code → OCC.code`; `isco_group → ISCO.code`.
- **Restricción cardinalidad:** T1 se construye mediante merges N:1 únicamente. **Asegurar `len(T1) == 1.506.445` después de cada merge.**

### T2 `ocupaciones` — 1 fila = 1 ocupación ESCO (catálogo + perfil)

| Columna | Tipo | Origen | Fuente | Regla |
|---|---|---|---|---|
| occupation_code | str | **original** | OCC.code | PK/FK → T1 |
| conceptUri | str | **original** | OCC.conceptUri | FK → REL.occupationUri |
| preferredLabel | str | **original** | OCC.preferredLabel | |
| iscoGroup | str | **original** | OCC.iscoGroup | todos de 4 dígitos (426 únicos) |
| isco_group_label | str | **derivada** | ISCO.preferredLabel | JOIN N:1 |
| greenShare | float | **agregado/derivado** | GS.greenShare | JOIN `iscoGroup = GS.code` (nivel 4); coerción str→float; fallo de parse → NaN (verificado: 426/426 cubiertos, rango 0–0,72) |
| n_empleos | int | **indicador agregado** | T1 | conteo de filas T1 con `occupation_code` = esta ocupación (puede ser 0; solo filas 'ok') |
| n_skills | int | **indicador agregado** | REL | count por `occupationUri` |
| n_essential | int | **indicador agregado** | REL | count `relationType=='essential'` |
| n_optional | int | **indicador agregado** | REL | count `relationType=='optional'` |
| n_knowledge | int | **indicador agregado** | REL | count `skillType=='knowledge'` |
| n_skill_competence | int | **indicador agregado** | REL | count `skillType=='skill/competence'` |
| n_skilltype_unclassified | int | **indicador agregado** | REL | count `skillType` NaN |
| n_transversal | int | **indicador agregado** | REL⋈SK | count `skills.reuseLevel=='transversal'` |
| n_cross_sector | int | **indicador agregado** | REL⋈SK | count `reuseLevel=='cross-sector'` |
| n_sector_specific | int | **indicador agregado** | REL⋈SK | count `reuseLevel=='sector-specific'` |
| n_occupation_specific | int | **indicador agregado** | REL⋈SK | count `reuseLevel=='occupation-specific'` |
| n_reuse_unclassified | int | **indicador agregado** | REL⋈SK | count `reuseLevel` NaN |
| p_essential | float | **indicador agregado** | T2 | `n_essential / n_skills` (n_skills≥7 verificado → sin división por 0) |
| p_knowledge | float | **indicador agregado** | T2 | `n_knowledge / n_skills` |
| p_transversal | float | **indicador agregado** | T2 | `n_transversal / n_skills` |

- **PK:** `occupation_code` (o `conceptUri`). **Filas:** 3.039 (catálogo completo, incluso ocupaciones con `n_empleos=0`).
- **Criterio anti-fuga:** T2 se calcula **exclusivamente** con `REL`, `SK`, `GS`, `ISCO` y `T1` (solo `n_empleos`). **Ninguna variable de persona (T1) alimenta los perfil-skills.** El agregado sobre `REL`/`SK` se computa sin filtrar por personas ni fechas.

### T3 `grupos_isco` — 1 fila = 1 código ISCO-08 (dimensión)

| Columna | Tipo | Origen | Fuente | Regla |
|---|---|---|---|---|
| code | str | **original** | ISCO.code | PK (619 filas) |
| conceptUri | str | **original** | ISCO.conceptUri | |
| preferredLabel | str | **original** | ISCO.preferredLabel | |
| nivel | int | **derivada** | ISCO.code | = len(code): 1=gran grupo, 2=sub‑grupo, 3=grupo menor, 4=unidad |
| description | str | **original** | ISCO.description | opcional (lectura) |

- **Relación con T1/T2:** `isco_group → T3.code`. Niveles superiores (1/2/3) se obtienen por **prefijo** del `isco_group` de 4 dígitos (p. ej. `2654` → `2` → subgrupo `26` → menor `265`), siempre presentes en T3.

### Tablas puente que NO se replican
`REL` (puente ocupación–skill) y las colecciones temáticas permanecen como están en `data/limpio/`. Solo si se aprueba el enriquecimiento opcional de §5 se agregan flags temáticos.

---

## 4. Agregaciones de skills (formales)

- **Granularidad:** `groupby(REL.occupationUri)` para conteos; join `REL.skillUri → SK.conceptUri` (100% de las 13.475 referenciadas presentes) para `reuseLevel`.
- **Totales globales esperados** (afirmaciones de test obligatorias):
  - Σ n_skills sobre las 3.039 ocupaciones = **126.051**; rango por ocupación **7–178**.
  - Σ n_essential = 67.600; Σ n_optional = 58.451.
  - Σ n_knowledge = 34.384; Σ n_skill_competence = 91.608; Σ n_skilltype_unclassified = 59.
  - Σ reuse (transversal/cross/sector/occupation/unclassified) = distribución de `SK.reuseLevel` referenciada (máx: transversal 452, cross 3.783, sector 6.655, occupation-specific 3.044; NaN 5). **Nota:** los totales de `reuseLevel` referenciado pueden ser ≤ catálogo si algún skill del catálogo no es referenciado por ninguna relación.
- **Enriquecimiento opcional (requiere aprobación):** flags temáticos `es_digital`, `es_green`, `es_transversal` (boolean por skill) desde las colecciones `digitalSkillsCollection`, `greenSkillsCollection`, `transversalSkillsCollection` (todas 100% ⊆ SK) y sus agregados `n_digital`, `n_green`, `n_transversal_coleccion` en T2.

---

## 5. Control de fuga y duplicación (auditoría)

- Fuga de información: prohibido computar agregados de T2 sobre subconjuntos de T1. `n_empleos` es la **única** conexión con T1 y es un conteo, no un perfil.
- Multiplicación: los merges hacia T1 son N:1 (como máximo 1 ocupación por empleo; a lo sumo 1 fila de OCC/ISCO por fila de JH). **Asegurar tamaño invariante** tras cada paso.
- Duplicación: llave primaria de T1 única (0 duplicados) y `conceptUri` único en T2 (3.039). Sin riesgo salvo bug → cubierto por las afirmaciones de §6.

---

## 6. Validaciones obligatorias de la implementación

| # | Afirmación | Valor esperado |
|---|---|---|
| V1 | len(T1) tras cada merge | 1.506.445 |
| V2 | filas con `emparejado=='ok'` | 1.391.276 |
| V3 | filas con `emparejado=='rescatado'` | 10.176 |
| V4 | filas con `emparejado=='unknown'` | 104.993 |
| V5 | filas con `emparejado=='descartado'` | 0 |
| V6 | `isco_group` nulo | solo cuando `emparejado=='unknown'` (104.993) |
| V7 | duplicados de PK(T1) | 0 |
| V8 | ocupaciones en T2 (conceptUri únicos) | 3.039 |
| V9 | Σ n_skills (todas las ocupaciones) | 126.051 |
| V10 | Σ n_essential / n_optional | 67.600 / 58.451 |
| V11 | Σ n_knowledge / n_skill_competence / unclassified | 34.384 / 91.608 / 59 |
| V12 | greenShare: no nulo en 426 grupos (de ocupaciones con grupo presente) | cobertura 426/426 |
| V13 | consistencia prefix: para todo `emparejado=='ok'`, `matched_code[:4]==isco_group` | 100% |
| V14 | ningún merge cambió el número de filas (assert en cada paso) | True |
| V15 | T2 no contiene ninguna columna de persona (resume_id/university_level/fechas) | True |

---

## 7. Clasificación: dato original / derivado / indicador agregado

- **Original:** columnas copiadas sin transformación (todas las de JH; `code`, `conceptUri`, `preferredLabel`, `iscoGroup`, `description`, `greenShare` sin coerción aún, etc.).
- **Derivado:** cálculo determinista fila a fila (emparejado, isco_group, isco_level, occupation_code/label, nivel de ISCO, greenShare→float).
- **Indicador agregado:** resultado de `groupby` (n_*, p_* de T2; n_empleos). Todo derivado/agregado debe ser reproducible con el mismo código y orden determinista (sin dependencia de orden de filas).

---

## 8. Orden de implementación (fijo)

1. Cargar `JH`, `OCC`, `ISCO`, `REL`, `SK`, `GS`.
2. Construir T1:
   a. clasificar `emparejado` (regla §1.3);
   b. merge N:1 a `OCC` (occupation_code, label, iscoGroup);
   c. aplicar rescate §1.4 y asignar `isco_group`;
   d. merge N:1 a `ISCO` (label, nivel);
   e. asserts V1–V7, V13.
3. Construir T3 (directo desde ISCO + nivel).
4. Construir T2:
   a. Perfil de skills (agregación §4) → asserts V8–V11 (V15);
   b. greenShare → V12;
   c. `isco_group_label` desde T3;
   d. `n_empleos` desde T1 (posterior a T1).
5. (Opcional, si se aprueba) flags temáticos de colecciones.
6. Guardar resultados en `data/procesada/` (nueva carpeta) — **no** sobrescribir `data/limpio/`.

---

## 9. Decisiones metodológicas cerradas en esta auditoría

1. `reuseLevel` = nivel de reutilización de la skill (definición oficial); lectura operativa documentada como inferencia.
2. `university_level` = nivel educativo más alto; `None` es categoría válida (no imputar).
3. `unknown` se **mantiene** como categoría propia en T1 (no se elimina); su distribución por nivel educativo es uniforme (≈6–8%), sin sesgo evidente.
4. Rescate por prefijo ISCO **validado 100%**; codifica el último caso de la clasificación.
5. Traslapes: **sin eliminación ni fusión**; empleos concurrentes se conservan; las transiciones se contarán solo entre empleos secuenciales no solapados (regla a aplicar en la fase de minería, no aquí).
6. El agregado de skills solo usa tablas ESCO (no JobHop) → sin fuga.
7. La PK de T1 ya está fijada por unicidad comprobada; las tablas de salida van a `data/procesada/`.

## 10. Decisiones pendientes de aprobación

- [ ] **D1. `unknown` en minería:** ¿incluir los 104.993 empleos como categoría propia o excluirlos de los pares de transición? (Recomendación: mantener en empleos; excluir como par origen/destino en secuencias).
- [ ] **D2. Empleos simultáneos en transiciones:** si A y B coexisten en el mismo periodo, ¿puede B→A contarse como transición? (Recomendación: no; describirlos por separado como "concurrencia").
- [ ] **D3. Enriquecimiento temático opcional** (flags digital/green/transversal de colecciones) en T2.
- [ ] **D4. `data/procesada/`** como destino de salida (se crea carpeta nueva).

## 11. Limitaciones vigentes (resumen)

- Sin campo de estudio → no se puede afirmar congruencia carrera–empleo (solo nivel).
- Sin causa de transición, salario ni sector económico (NACE sin mapeo).
- `unknown` no rescatable a nivel de ocupación (104.993 filas, 6,97%).
- Skills solo del requerimiento ocupacional; no hay skills individuales de la persona.
- No hay borde skill→grupo ISCED-F en `data/limpio/` (taxonomía de skills no utilizada).

---

*Generado como "auditoría y cierre" del diseño de integración. Complementa y corrige cifras de `DISEÑO_INTEGRACION.md` (p. ej. traslapes ahora cuantificados).*