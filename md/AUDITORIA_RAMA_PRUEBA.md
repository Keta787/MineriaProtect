# AUDITORIA_RAMA_PRUEBA — Todo lo importante de la rama hasta hoy

Documento único de la rama `prueba` del proyecto **MineríaProtect**. Reúne lo esencial de:
reorganización, fuentes, unión/integración validada, diagnóstico de calidad, guía de limpieza,
explicación técnica, auditorías históricas y decisiones pendientes. Es la base para la compañera/IA
que continúe la fase de limpieza y para el entregable del parcial de Minería de Datos.

> Los documentos viven en `README.md` (raíz, puerta de entrada) y en `md/` (este documento,
> `BUENAS_PRACTICAS_CODIGO.md` y `contexto_sesion3.md`). Los históricos fueron descartados
> (git conserva el historial).

---

## 1. RESUMEN DE LA RAMA

| Área | Hecho verificado | Estado |
|---|---|---|
| Reorganización | Estructura actual: `data/{original, limpia, cruce}`, `libros/`, `md/`, `script/` | ✅ Commit `3698044` (historial preservado con `git mv`); reestructuración posterior revisada en §14 |
| Integración | `empleos` = 1 fila por experiencia enriquecida; N:1, nunca multiplica | ✅ 1.506.445 filas · 284.247 personas · 11 columnas |
| Validación de integración | V1–V7 + comparación contra referencia | ✅ "mismos registros exactos: True" |
| Limpieza de `empleos` (bloque 4) | Pipeline ejecutado, cifras reconciliadas contra los datos | ✅ `empleos_limpio.parquet` generado y verificado (solo parquet) §13 |
| Pendiente principal | `script/limpieza/limpiar_empleos.py` → `empleos_limpio` | ✅ Ejecutado; los pendientes de minería quedan en §12 |

---

## 2. OBJETIVO Y PREGUNTA DE INVESTIGACIÓN

Analizar **trayectorias laborales**: qué ocupaciones tiene cada persona, en qué orden y si cambia de
área, relacionado con su nivel educativo, usando minería de secuencias sobre **JobHop v2**.

- Pregunta sencilla: *¿qué patrones aparecen en la trayectoria laboral después de la formación,
  especialmente si los empleos corresponden con lo estudiado?*
- Pregunta técnica: *¿qué patrones de transición ocupacional pueden identificarse en trayectorias
  posteriores a la formación?*

Cada persona se representa como una secuencia ordenada por trimestre:
`Sₚ = [(t₁, ocupación, área), (t₂, ocupación, área), …]` y sobre `{Sₚ}` se aplicarán minería de
secuencias/transiciones. Para eso se necesita darle **significado** a cada `matched_code` (nombre de
ocupación + área ISCO-08), que es el papel de la unión.

---

## 3. ESTRUCTURA ACTUAL DEL PROYECTO

```text
MineriaProtect/
├── data/                           # datos (original/ y limpia/ en disco; cruce/ versionado, solo parquet)
│   ├── original/                   # fuentes: JobHop_v2_train.parquet + ESCO ISCOGroups/occupations
│   ├── limpia/                     # fuentes de verdad: JobHop + ESCO occupations e ISCOGroups (_limpio)
│   └── cruce/                      # empleos.parquet + empleos_limpio.parquet (sin CSV intermedios)
├── libros/                         # cuadernos: Lectura, Diagnostico_Limpieza_Empleos, presentacion (análisis, §15)
├── md/                             # documentación de la rama: AUDITORIA, BUENAS_PRACTICAS_CODIGO, contexto
├── script/
│   ├── filtro/                     # análisis reutilizable de presentacion.ipynb (§15)
│   │   ├── filtros.py              # selección por nivel/grupo ISCO/ocupación/periodo/vigencia
│   │   └── indicadores.py          # dur_Q (inclusiva), IQR, transiciones, brechas, crosstabs, banderas
│   ├── limpieza/
│   │   ├── limpiar_datos.py        # data/original/ → data/limpia/ (limpia fuentes ESCO; JobHop se omite)
│   │   └── limpiar_empleos.py      # pipeline bloque 4 → data/cruce/empleos_limpio.parquet
│   └── requirements/
│       └── requirements.txt        # pandas>=2, pyarrow>=14
```

Desversionados (conservados en disco/historial): `data/original/` — solo los originales de los 3
datasets conservados (`JobHop_v2_train.parquet`, `ESCO/occupations_en.csv`, `ESCO/ISCOGroups_en.csv`)
— y `data/cruce/*.csv` (los CSV intermedios del cruce fueron **eliminados**; el bloque 4 solo
exporta parquet). `data/limpio/`, `docs/historicos/` y los ESCO descartados fueron **borrados**
de disco. El parquet del integrado (`empleos.parquet`) se regenera desde el historial git si se requiere.

Reproducción:
```text
python script/limpieza/limpiar_datos.py     # fuente: data/original/ → data/limpia/ (limpieza de fuentes; JobHop ya limpio, se omite)
python script/limpieza/limpiar_empleos.py   # integrado → data/cruce/empleos_limpio.parquet (bloque 4, §13)
# integración: empleos ya existe versionado en data/cruce/empleos.parquet (validado V1–V7).
# cruzar_datos.py fue ELIMINADO del repo por decisión (para eso existe empleos); se recupera del historial git si hace falta regenerar.
```

---

## 4. FUENTES Y SUS ROLES

| Fuente | Archivo | Rol |
|---|---|---|
| **JobHop v2** | `JobHop_v2_train_limpio.parquet` | Base: quién, cuándo, qué ocupación (código), nivel educativo |
| **ESCO occupations** | `occupations_en_limpio.csv` | Traduce `code → nombre ocupación + grupo ISCO-08` |
| **ESCO ISCOGroups** | `ISCOGroups_en_limpio.csv` | Etiqueta y jerarquía del área ocupacional (`code 4d → label + nivel`) |
| ESCO skills / greenShare / colecciones | *(borrados del repo)* | Enriquecimientos descartados: se mantienen solo occupations + ISCOGroups |
| OLE Colombia | *(inexistente en repo)* | **Descartado**: contexto colombiano sin clave de unión individual con JobHop |

JobHop proviene de Flandes, Bélgica (aida-ugent/JobHop, Hugging Face). El país no es el objetivo.

---

## 5. UNIÓN / INTEGRACIÓN (validada)

### 5.1 Cruces implementados
| Cruce | Llave | Tipo | Cobertura verificada |
|---|---|---|---|
| R1 JobHop → occupations | `matched_code = code` | N:1 | 2.966/2.983 códigos; 1.391.276 filas (92,35 %) |
| R6 Rescate por prefijo | `matched_code[:4] = ISCOGroups.code` | N:1 | 16 códigos → 10.176 filas (0,68 %); prefijo coincide 100 % con el grupo real |
| R2 occupations → ISCOGroups | `isco_group = code` | N:1 | 426/426 grupos (100 %) |

Ver R8–R10 (skill–skill red, taxonomía ISCED-F, NACE) **descartadas**: sin borde utilizable,
red para fase posterior, o exigiría información externa. R3/R4/R5/R7 (skills/greenShare/colecciones)
**solo agregadas** (1 fila por ocupación), nunca expandiendo `empleos`.

### 5.2 `emparejado` (clasificación exhaustiva, precedencia estricta)
1. `matched_code == 'unknown'` → `unknown`
2. `matched_code ∈ occupations.code` → `ok`
3. `matched_code[:4] ∈ ISCOGroups.code (4d)` → `rescatado`
4. resto → `descartado` (debe ser 0)

Resultado: `ok 1.391.276 (92,35 %) · unknown 104.993 (6,97 %) · rescatado 10.176 (0,68 %) · descartado 0`.

### 5.3 Las 11 columnas de `empleos`
`resume_id · start_date · end_date · university_level · matched_code · emparejado ·
occupation_code · occupation_label · isco_group · isco_group_label · isco_level (constante 4)`.
PK `(resume_id, matched_code, start_date, end_date)` única (0 duplicados). Cardinalidad: **1 fila =
1 experiencia**; cada merge N:1 mantiene `len == 1.506.445`.

### 5.4 Validaciones V1–V7 (integración)
`T1 1.506.445` · `ok 1.391.276` · `rescatado 10.176` · `unknown 104.993` · `descartado 0` ·
`isco_group nulo solo en unknown (104.993)` · `duplicados PK 0`. (V8–V15: agregados de skills,
coberturas y anti-fuga, en el `CIERRE_DISEÑO.md` histórico, ahora descartado; sus pendientes
formales D1–D4 viven en §12.)

### 5.5 CSV usados / no usados (resumen)
- **Sí (archivos actuales del repo):** JobHop, occupations, ISCOGroups (los 3 datasets gestionados).
- **Histórico del cruce (archivos ya borrados del repo):** occupationSkillRelations, skills,
  greenShareOcc, skillSkillRelations, broaderRelations*Pillar, skillGroups/skillsHierarchy,
  colecciones temáticas, researchOccupationsCollection, conceptSchemes/dictionary, NACE. OLE: sin clave.
- Los enriquecimientos experimentados fueron **agregados** (1 fila/ocupación); el integrado final
  `empleos` conserva 11 columnas (sin columnas de skills/greenShare), ver §5.3.

---

## 6. DIAGNÓSTICO DE CALIDAD DEL INTEGRADO (cifras verificadas)

| Columna | NaN reales | % | Literales que parecen nulos |
|---|---|---|---|
| `occupation_code/label` | 115.169 | 7,64 % | `'unknown'` 104.993 (ausente desde la fuente) |
| `isco_group/label/level` | 104.993 | 6,97 % | `'None'` 174.036 (nivel literal) |
| `resto` | 0 | 0 % | `'Present'` 76.180 (empleo vigente) |

- Tipos: todo `str` salvo `resume_id` (int) e `isco_level` (float, **constante 4**) → **no hay
  columna numérica analítica** en el integrado.
- Duplicados: **0** exactos; **0** por `(resume_id, start, end, code)`; ⚠️ claves cortas crean
  falsos positivos: `(resume_id, start, code)` → **9.601**; `(resume_id, start, end)` → **74.357**
  (pluriempleo real).
- Fechas: 1955–2029; **0 `start>end`**; duración máx **160 trimestres** (convención inclusiva
  `end−start+1`; Q1=2 · Q3=11 · sup=24,5); **11 filas con fechas futuras** (>2026: 1 inicio +
  11 fin; la fila `Q1 2027→Q1 2028` pertenece a ambos conjuntos) → error de captura.
- Categorías canónicas: `emparejado` 3 (ok 1.391.276 · unknown 104.993 · rescatado 10.176);
  `university_level` 5 (Secondary 590.624 · Bachelor 515.463 · Master 219.884 · None 174.036 ·
  PhD 6.438); `occupation_label` 2.966 · `isco_group_label` 426. **0 colisiones** tras
  `strip/lower/sin_tildes` → ya normalizadas.
- **Traslapes**: 429.958 filas (28,54 %) · 154.131 personas (54,22 %) → regla de negocio
  ("transición"), no borrado automático.

---

## 7. LIMPIEZA DE `empleos` — GUÍA (bloque 1-3 del parcial)

### 7.1 Regla central y orden canónico
`DIAGNÓSTICO → DUPLICADOS → CATEGORÍAS → FALTANTES → OUTLIERS → VALIDACIÓN → EXPORTAR`.
Todo cambio: diagnóstico → clasificación → justificación → tratamiento → validación → documentación.
IQR **sobre el original**, nunca sobre imputados; no imputar antes de deduplicar.

### 7.2 MCAR / MAR / MNAR en `empleos`
| Tipo | Ejemplo real en `empleos` | Decisión |
|---|---|---|
| MCAR | 11 filas con fechas futuras (apariciones aisladas) | Corregir/eliminar (0,0007 %) |
| MAR (semántico) | NaN de ocupación explicado 100 % por `emparejado` | NO imputar → **bandera** (`unknown`/`rescatado`) |
| MNAR | `university_level='None'` (quien no reporta nivel) | NO imputar moda → **re-categorizar** |

### 7.3 Métodos: cuál se usa y por qué los demás NO
| Método | ¿Aplica? | Por qué |
|---|---|---|
| Eliminar filas | **No** | <5 % + MCAR obligatorios; bloque es 6,97 % estructural; borra 64.508 personas (2.490 con todo su historial) |
| Media/mediana | **No** | No existe columna numérica a imputar; "la mediana para una fecha no existe" |
| Moda | **Prohibido** | Inflaría `Secondary school` (590.624) y fabricaría educación |
| KNN/regresión | **No** | Sin correlaciones que expliquen ocupación/fecha; fuga de información |
| **Constante / bandera** | **Estrategia central** | La ausencia significa algo: `unknown`→flag, `'None'`→categoría, `'Present'`→vigente |

Código de banderas:
```python
df["es_unknown_ocupacion"] = df["emparejado"].eq("unknown")
df["es_rescatado"]         = df["emparejado"].eq("rescatado")
df["es_vigente"]           = df["end_date"].eq("Present")
```

### 7.4 Casos A/B/C
- **A — ocupación/área (NaN estructurales):** bandera (el flag ya la provee). Conservar → salva
  64.508 personas; **2.490** con historial completo `unknown` (la cifra 4.987 prevista no se reproduce;
  ver §13).
- **B — `'None'` en educación:** re-categorizar como categoría propia.
- **C — `'Present'` (76.180):** flag `vigente`; censura a la derecha solo si se requiere.

### 7.5 Normalización de categorías
**No aplica como limpieza** (0 colisiones verificadas en 2.966/426 labels). Se conserva solo como
**re-verificación defensiva** (`assert colisiones == 0`) y para enriquecimientos futuros (CV/ESCO).

### 7.6 Fechas y coherencia temporal
Formato `Q<n> <aaaa>` → ordinal `4*año+trimestre`; `start<=end` (0 violaciones); `'Present'` = vigente;
11 filas con fechas futuras → eliminar; 75.227 inicios ≤1990 → definir ventana temporal (decisión de negocio).

### 7.7 Umbrales de aceptación (regla del negocio)
Duplicados 0 · nulos restantes 0 (tras banderas) · categorías desconocidas 0 · fechas futuras 0 ·
`start>end` 0 · impacto 1.506.445 filas / 284.247 personas.

### 7.8 Bitácora prevista vs real (la real la imprime el pipeline; ver §13)
| Columna | Problema | Cantidad | % | Diagnóstico | Método | Por qué | Impacto |
|---|---|---|---|---|---|---|---|
| `occupation_code/label` | NaN | 115.169 | 7,64 % | MAR estructural | Bandera | "Sin emparejar" ≠ no dato | 64.508 personas |
| `isco_group/label/level` | NaN | 104.993 | 6,97 % | Ídem | Bandera | Ídem | Ídem |
| `university_level` | `'None'` | 174.036 | 11,55 % | MNAR | Re-categorizar | Moda inflaría mayoría | Sin inventar |
| `end_date` | `'Present'` | 76.180 | 5,06 % | Censura | Flag vigente | Fin inventado falsea duración | 5,06 % |
| `end_date/start_date` | futuras | 11 | 0 % | Error dominio | Eliminar | Imposible vs 2026 | 11 filas |
| `start>end` | — | 0 | 0 % | — | — | No existe | — |

---

## 8. OUTLIERS EN `empleos` (bloque 3)

### 8.1 ¿Dónde está el "edad 220 / 600 GB"?
**No existe**: sin columna numérica analítica (códigos texto, `isco_level` constante). Los únicos
puntuales reales = **11 filas con fechas futuras** → eliminar por dominio.

### 8.2 IQR (regla de Tukey) sobre la única numérica real: `dur_Q`
```
PASO 1 Ordenar 1.430.265 valores con fecha
PASO 2 Q1 = 2.00 · Q3 = 11.00
PASO 3 IQR = 9.00
PASO 4 inferior = -11.50 (irrelevante) · superior = 24.50 (≈6 años)
PASO 5 fuera: 141.591 filas / 97.954 personas (todas por arriba, ≥25 trim)
PASO 6 CONSERVAR (estabilidad = señal); winsorizar clip(-11.5, 24.5) SOLO si dur_Q entra al modelo
```
Patrón central: mediana **5** · P90 **24** · P95 **36** · P99 **73** · máx **160** (carrera real de
40 años, p. ej. *commissioning technician* Q1 1975–Q4 2014). Cola larga verificada → **IQR es la
regla correcta para el curso** ("comerciales casi siempre tienen colas largas").

### 8.3 z-score: NO como criterio
|z|>3 marca **33.841** vs IQR **141.591** → dos respuestas = ambigüedad. Media (9,9) y std (14,0)
arrastradas por la cola → perdona lo que IQR marca. Texto para el informe: *"el z-score confirma la
cola larga como señal; la decisión se toma con IQR (regla del curso)."*

### 8.4 Tratar vs conservar (lo concreto)
- **CONSERVAR:** cola larga `dur_Q` (141.591/97.954); segmento `unknown` (104.993, bandera);
  429.958 traslapadas (pluriempleo). "Eliminar borra un segmento completo."
- **TRATAR:** 11 filas con fechas futuras (error de dominio; eliminadas en la ejecución real, §13).

---

## 9. RÚBRICA, NIVEL ESPERADO Y COMPARATIVA (parcial)

- **Rúbrica:** funcionalidad 40 % (valida contra criterios explícitos) · justificación técnica 30 %
  (MCAR/MAR/MNAR, IQR, negocio) · documentación 20 % (QUÉ/POR QUÉ + bitácora) · reproducibilidad
  10 % (rutas relativas, requisitos, semillas, sin dependencias locales).
- **Nivel esperado → nuestro `empleos`:** 1.506.445 filas, nulos 0 tras banderas, `emparejado` 3,
  `university_level` 5, ESCO 426, ocupaciones 2.966, dups 0. No usamos `fillna`. Validación explícita
  impresa + bitácora.
- **Objetivo de logro:** "Excepcional" → funciones reutilizables y **pruebas automáticas** (asserts
  por fase).

### Comparativa TelecomUNO vs `empleos` (entregable "Proyecto")
| Problema | TelecomUNO (ejercicio) | `empleos` (nuestro) |
|---|---|---|
| Duplicados | 60 (2,4 %) → eliminar | 0; riesgos con claves cortas (9.601/74.357) |
| Faltantes | 441 MCAR, moda/mediana válidas | Estructurales (flag) + literales `None`/`Present` → banderas |
| Categorías | 16 ciudades "de mil maneras" | Ya normalizadas (0 colisiones) |
| Outliers | gb_datos + edad/facturación/minutos imposibles | Sin numérica analítica; cola larga = señal; 11 filas con fechas futuras |
| Validación | Contra canónico (medias) | Contra integración V1–V7 + bitácora |

Conclusión: **mismo pipeline, decisiones opuestas** (el patrón del ejercicio no se repite; aquí los
problemas son estructurales, semánticos y de dominio).

---

## 10. EXPLICACIÓN TÉCNICA (para exponer, 3 bloques)

**Bloque 1 — Objetivo:** dar significado a los códigos para construir secuencias por persona
(`Sₚ = [(t, ocupación, área)…]`) y aplicar minería de secuencias/transiciones.

**Bloque 2 — Datos:** una misma fila de `empleos` trae quién/cuándo/qué/área/educación (11 columnas,
validada V1–V7; la integración ya está aplicada y versionada, `cruzar_datos.py` se elimina del repo y
se recupera del historial git si se necesita regenerar).

**Bloque 3 — Ejemplo real (persona 198574, Master):** 16 empleos con ocupación identificada, 5 áreas
ISCO recorridas (`Teaching professionals n.e.c. → Teachers' aides → Social work … → Secondary
education teachers → University and higher education teachers`), **8 cambios de área**; el último
salto (Q3 2017) a *University and higher education teachers* (mayor especialización, coherente con
su Master). Muestra traslapes reales (dos empleos iniciados Q1 2016) → calidad controlable.

---

## 11. AUDITORÍA DE LA LIMPIEZA DE FUENTES (deuda heredada)

Estado de `limpiar_datos.py` (fuentes JobHop/ESCO): **bien** (no toca originales, códigos como texto,
validación antes/después, reconciliación exacta) con **deudas vs guía**:
- Orden del pipeline invertido en JobHop (dedupe después de imputar nulos).
- Sin clasificación MCAR/MAR/MNAR sobre las fuentes.
- Sin sección IQR/outliers (aquí aceptable: textual/llaves; el IQR procede en el integrado, hecho en §8).
- Sin checks de "valores imposibles" ni dominios canónicos. Verificado: 0 anomalías externas
  (formatos `Qn AAAA`, `start>end`, duración 0).
(Detalle: la auditoría de fuentes original fue consolidada aquí; el histórico fue descartado.)

---

## 12. ESTADO ACTUAL, DECISIONES PENDIENTES Y PRÓXIMOS PASOS

**Listo:** reorganización (commit `3698044`), integración reproducida y validada, diagnóstico,
estrategia de faltantes, outliers (IQR/Tukey), bitácora, rúbrica, comparativa, guía consolidada,
pipeline de limpieza ejecutado y verificado (bloque 4 → `empleos_limpio`, §13); `script/`
reestructurado (eliminados `cruzar_datos.py` y `tablas.ipynb`; `limpieza/limpiar_datos.py` y
`limpieza/limpiar_empleos.py`; cuadernos en `libros/`, dependencias en `script/requirements/`).

**Pendiente principal (bloque 4):** `script/limpieza/limpiar_empleos.py` (clase `LimpiadorEmpleos`):
cargar `data/cruce/empleos.parquet` → 1 diagnóstico → 2 duplicados → 3 categorías (re-verificar y
re-categorizar `'None'`) → 4 faltantes (banderas A–C) → 5 outliers (11 filas futuras → eliminar;
conservar cola larga) → 6 validación (tabla §7.7 impresa) → 7 exportar `data/cruce/empleos_limpio.parquet`
(solo parquet). Con asserts por fase (nivel "Excepcional") y `requirements.txt`.
**→ ESTADO: ✅ ejecutado y verificado (ver §13).**

**Decisiones de negocio anticipadas (a justificar):**
| # | Bloque | Cantidad | % | Tratamiento propuesto |
|---|---|---|---|---|
| 1 | `emparejado=unknown` | 104.993 | 6,97 % | Bandera (64.508 personas; 2.490 perderían todo) |
| 2 | `university_level='None'` | 174.036 | 11,55 % | Re-categorizar |
| 3 | `end_date='Present'` | 76.180 | 5,06 % | Flag `vigente` / censura |
| 4 | Traslapes | 429.958 | 28,54 % | Definir "transición" |
| 5 | Ventana temporal | 1955–2029 | — | Definir rango (+11 filas futuras) |
| 6 | Categorías canónicas | 3/5/426/2.966 | — | "Desconocidas: 0" sin romper ESCO |

**Diseño de integración histórico:** pendientes formales D1 (`unknown` en minería), D2 (empleos
simultáneos en transiciones), D3 (enriquecimiento temático), D4 (destino `data/procesada/`) —
relevantes en la fase de minería, no en la limpieza.

**Git:** rama `prueba` es la de trabajo (pusheada). `main` quedó con commits antiguos/junk del
compañero y `CRUCE_DATOS.md` desactualizado → **no merge aún**; unificar sobre la estructura de
`prueba`.

---

## 13. EJECUCIÓN DEL BLOQUE 4: `script/limpieza/limpiar_empleos.py` → `empleos_limpio`

Pipeline implementado y ejecutado sobre el original **sin modificarlo**. Clase `LimpiadorEmpleos`,
7 fases con `assert` por fase (nivel "Excepcional"), docstrings en español y comentarios solo del
porqué (A9 del estándar), `script/requirements/requirements.txt` (pandas>=2, pyarrow>=14).
Reproducción: `python script/limpieza/limpiar_empleos.py`.

### 13.1 Qué se le hizo a `empleos` (as-built, en orden)

| Fase | Acción sobre la copia de trabajo | Verificado por assert |
|---|---|---|
| 1 Diagnóstico | Shape/tipos/nulos/dups/rango de fechas sobre el original | 1.506.445 × 11 · 284.247 personas |
| 2 Duplicados | Detección exacta y por PK + claves cortas (`keep='first'`, solo reporte) | dups 0 / PK 0 · 74.357 / 9.601 |
| 3 Categorías | Re-verificación de cardinalidades + **re-categorizar** `'None'` → `'No reportado'` (caso B) | 3/5/426/2.966 · 0 `'None'` restantes |
| 4 Faltantes | Banderas `es_unknown_ocupacion`, `es_rescatado`, `es_vigente` (casos A y C) | 104.993 / 10.176 / 76.180 · 115.169 NaN ↔ 100 % explicados |
| 5 Outliers | IQR/Tukey sobre `dur_Q` inclusiva (conservar cola) + z-score solo comparativo + **eliminar 11 filas futuras** | 141.591/97.954 conservadas · −11 filas |
| 6 Validación | Tabla §7.7 impresa (dups 0 · dups PK 0 · nulos sin bandera 0 · futuras 0 · `start>end` 0) | 6/6 ok |
| 7 Exportar | `data/cruce/empleos_limpio.parquet` (17,4 MB, **solo parquet**), bitácora de trazabilidad impresa, original intacto | shape final 1.506.434 × 14 |

### 13.2 Fallos encontrados durante la ejecución (lo previsto vs lo real)

| Cifra prevista (documentada) | Real verificada | Causa | Medida tomada |
|---|---|---|---|
| 12 fechas futuras ("1 inicio + 11 fin") | **11 filas** | La fila `Q1 2027→Q1 2028` pertenece a ambos conjuntos y se contó dos veces al sumar | Fase 5 elimina 11 filas (assert `== 11`) |
| 4.987 personas con historial completo `unknown` | **2.490** | Ninguna definición natural (todas las filas `unknown`, incl. `rescatado`) reproduce 4.987 | Assert descartado; se reporta 2.490 |
| Duración sin convención explícita | **Inclusiva `end−start+1`** | Única definición que reproduce §8.2 (Q1=2, Q3=11, sup 24,5, mediana 5, máx 160) | `_duracion_trimestres` usa `+1` |
| Claves cortas | **`keep='first'` → 74.357 / 9.601** | La cifra documentada cuenta filas extra (`keep=False` daría 134.585/19.073) | Fase 2 alineada a `keep='first'` |
| Caso B solo documentado, no aplicado | 174.036 `'None'` en educación | Faltaba la transformación | Implementada en fase 3 → `'No reportado'` |

### 13.3 Resultado final de `empleos_limpio` (verificado aparte)

- **1.506.434 filas** (original 1.506.445 → **−11** por fechas futuras) · **284.247 personas** ·
  **14 columnas** = 11 del original + `es_unknown_ocupacion` · `es_rescatado` · `es_vigente`.
- 0 duplicados exactos · 0 duplicados PK · 0 nulos de ocupación sin bandera · 0 fechas futuras ·
  0 `start>end` · `university_level` sin `'None'` (`'No reportado'` 174.035 = 174.036 − 1 fila
  futura que era `'None'`).
- Banderas: 104.993 · 10.176 · 76.180 (idénticas al diagnóstico del original).
- El original `data/cruce/empleos.parquet` **no se modifica** (se mantiene versionado en el repo).

### 13.4 Notas para la fase de minería

- La cola larga de `dur_Q` se conserva (0 filas eliminadas por atípicos); si `dur_Q` entra al modelo,
  winsorizar `clip(−11,5; 24,5)` (§8.2).
- `libros/Diagnostico_Limpieza_Empleos.ipynb` reproduce el pipeline: duración **inclusiva** (`+1`),
  `keep='first'` en `contarGruposDuplicados`, **11 filas futuras** y el centinela `SENTINELA_FIN`;
  sus valores coinciden con los de §8.2 y de este documento (alineado en §14).

---

## 14. AUDITORÍA DE REESTRUCTURACIÓN Y MEJORAS (BUENAS_PRACTICAS_CODIGO)

Auditoría del repo contra `md/BUENAS_PRACTICAS_CODIGO.md` realizada al cerrar la reorganización
(responsable: revisión asistida). Las falencias detectadas se **corrigieron** en esta misma ronda.

| Falencias detectadas | Corrección aplicada | Evidencia |
|---|---|---|
| `README.md` desactualizado (estructura vieja: `script/limpiar_datos.py`, `script/Lectura.ipynb`, sin `libros/`, sin `empleos_limpio`) | `README.md` reescrito a la estructura real: tree actualizado, comandos `script/limpieza/…`, notebooks `libros/`, datasets con `empleos_limpio.parquet`, decisiones documentadas | `README.md` (raíz) |
| Rutas obsoletas `script/limpiar_*.py` / `script/Lectura.ipynb` | Actualizadas a `script/limpieza/…` y `libros/…` en §1, §3, §12 y §13 | Este documento |
| `libros/Lectura.ipynb` import roto (`sys.path` apuntaba a `script/` donde ya no vive el código) | CELDA 3 → `sys.path.insert(0, PROYECTO/"script"/"limpieza")`; sintaxis del cuaderno validada (15 celdas, 0 errores) | `libros/Lectura.ipynb` |
| Cuaderno Diagnóstico inconsistente con el pipeline: duración exclusiva, `keep=False`, "12 filas", sentinela literal 99999 | Alineado: duración `+1`, `keep='first'`, "11 filas" (3 celdas md + 1 tabla) y constantes `SENTINELA_FIN`; sintaxis validada (67 celdas, 0 errores) | `libros/Diagnostico_Limpieza_Empleos.ipynb` |
| `requirements.txt` sin versiones y en carpeta no documentada | Pineado `pandas>=2` / `pyarrow>=14` en `script/requirements/`; ruta documentada en README y §13 | `script/requirements/requirements.txt` |
| Estándar: sin regla de reproducibilidad, sin regla de documentación, excepción de prints/camelCase implícita, `asserts` del nivel Excepcional no reconocidos, ruta obsoleta `scripts/limpiar_empleos.py` | Añadidas **D5 Reproducibilidad**, **A9 Documentación**, excepciones explícitas en C2 y A1, nota "Excepcional" en D1, D3 marcada opcional, ruta corregida | `md/BUENAS_PRACTICAS_CODIGO.md` |
| Decisiones "solo parquet" y "prints como entregable" no documentadas formalmente | Documentadas en `README.md` (Decisiones), excepción C2 del estándar y §13.1 | `README.md`, `md/BUENAS_PRACTICAS_CODIGO.md` |

Estado del repo tras la ronda: scripts y cuadernos con sintaxis válida, cifras de todos los
artefactos coincidentes (§8.2, §13, notebooks acreditan Q1=2/Q3=11/máx 160, 74.357/9.601, −11 filas).
La reorganización de esta ronda quedó commitada en `dce93d5` (rama `prueba`, origin).
El libro de análisis se agrega después en §15.

---

## 15. LIBRO DE ANÁLISIS: `libros/presentacion.ipynb` Y `script/filtro/`

Entregable de análisis/mini investigación sobre `data/cruce/empleos_limpio.parquet` (solo
lectura; `dur_Q` se **recalcula** con la fórmula inclusiva, no se agrega al parquet). La rúbrica
de la sesión 3 tiene prioridad sobre el estándar del repo; el libro cumple Funcionalidad
(exec de las 30 celdas de código pasa sin errores), Justificación técnica (IQR de Tukey sobre
datos observados, gaps = proxy de desempleo, censura `Present` y `unknown` sin imputar),
Documentación (bloque 5 con DATO/INTERPRETACIÓN/LIMITACIÓN, todo calculado en vivo) y
Reproducibilidad (rutas relativas, sin aleatoriedad → sin semillas). Nivel Excepcional:
funciones reutilizables + asserts de línea base contra §8.2/§13.

| Artefacto | Descripción |
|---|---|
| `script/filtro/filtros.py` | Selecciones vectorizadas (nivel, grupo ISCO, ocupación, periodo, vigencia, sin-área) que devuelven copias; asserts de invariantes y reporte de excluidos. |
| `script/filtro/indicadores.py` | `dur_Q` inclusiva, `distribucion_duracion`, duración por grupo/nivel, `top_valores`, `crosstab_nivel_grupo`, transiciones consecutivas y primera→segunda (dedupe de 74.357 repetidas exactas), brechas sin empleo (running `cummax+shift`, proxy de desempleo) y traslapes (mismo método que el diagnóstico). |
| `libros/presentacion.ipynb` | 44 celdas (14 md + 30 code); 5 bloques: Conocer (línea base + asserts), Exploración por preguntas, Relaciones (nivel↔ISCO, ISCO↔duración, transiciones, brechas, traslapes), Mini investigación (4 preguntas: concentración por nivel, duración por nivel, linealidad, desempleo proxy) y Hallazgos con formato DATO/INTERPRETACIÓN/LIMITACIÓN. |

Cifras verificadas en la ejecución (30/30 celdas OK): línea base 1.506.434×14 · 284.247 personas ·
flags 104.993/10.176/76.180 · `No reportado` 174.035 · inicios Q1 1955–Q4 2020 · duración mediana
5 trimestres (IQR 2–11) · 18,3 % de transiciones conservan grupo ISCO · 60,1 % de personas con al
menos una brecha (mediana 3 trimestres, máx 151) · 82 % de personas con ≥1 traslape (pluriempleo o
dato impreciso; método igual al del diagnóstico). La reestructuración de la ronda §14 quedó
commitada en `dce93d5` (rama `prueba`, origin).

---

*Documento consolidado a partir de: README.md, README_DATOS.md, GUIA_LIMPLEZA_EMPLEOS.md,
EXPLICACION_TECNICA.md, DISEÑO_INTEGRACION.md, CIERRE_DISEÑO.md, AUDITORIA_LIMPLEZA.md.
Cifras verificadas sobre `data/cruce/empleos.parquet` y `data/cruce/empleos_limpio.parquet`.*