# AUDITORIA_RAMA_PRUEBA — Todo lo importante de la rama hasta hoy

Documento único de la rama `prueba` del proyecto **MineríaProtect**. Reúne lo esencial de:
reorganización, fuentes, unión/integración validada, diagnóstico de calidad, guía de limpieza,
explicación técnica, auditorías históricas y decisiones pendientes. Es la base para la compañera/IA
que continúe la fase de limpieza y para el entregable del parcial de Minería de Datos.

> Los 3 MD de la rama viven en `md/` (`README.md` como puerta de entrada, este documento y
> `contexto_sesion3.md` material de clase). Los históricos fueron descartados (git conserva el historial).

---

## 1. RESUMEN DE LA RAMA

| Área | Hecho verificado | Estado |
|---|---|---|
| Reorganización | Estructura actual: `data/{original, limpia, cruce}`, `md/`, `script/` | ✅ Commit `3698044` (historial preservado con `git mv`) |
| Integración | `empleos` = 1 fila por experiencia enriquecida; N:1, nunca multiplica | ✅ 1.506.445 filas · 284.247 personas · 11 columnas |
| Validación de integración | V1–V7 + comparación contra referencia | ✅ "mismos registros exactos: True" |
| Limpieza de `empleos` (parcial) | Diagnóstico, faltantes, outliers documentados con cifras | 🟡 Teoría + hallazgos listos; **falta el pipeline (bloque 4)** |
| Pendiente principal | `script/limpiar_empleos.py` → `empleos_limpio` | ⏳ A construir (obligatorio para sesión 4) |

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
├── data/                           # datos (original/ y limpia/ en disco; cruce/ versionado)
│   ├── original/                   # fuentes: JobHop_v2_train.parquet + ESCO ISCOGroups/occupations
│   ├── limpia/                     # fuentes de verdad: JobHop + ESCO occupations e ISCOGroups (_limpio)
│   └── cruce/                      # empleos.parquet (versionado) + *.csv ignorados
├── md/                             # documentación de la rama: README, AUDITORIA, contexto
├── script/
│   ├── limpiar_datos.py           # data/original/ → data/limpia/ (limpia fuentes ESCO; JobHop se omite)
│   └── Lectura.ipynb              # cuaderno de limpieza (reproduce limpiar_datos.py)
```

Desversionados (conservados en disco/historial): `data/original/` — solo los originales de los 3
datasets conservados (`JobHop_v2_train.parquet`, `ESCO/occupations_en.csv`, `ESCO/ISCOGroups_en.csv`)
— y `data/cruce/*.csv`. `data/limpio/`, `docs/historicos/` y los ESCO descartados fueron **borrados**
de disco. El CSV de 156 MB no se publica (límite GitHub 100 MB); el parquet se regenera.

Reproducción:
```text
python script/limpiar_datos.py   # fuente: data/original/ → data/limpia/ (limpieza de fuentes; JobHop ya limpio, se omite)
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
- Fechas: 1955–2029; **0 `start>end`**; duración máx **160 trimestres**; **12 fechas futuras**
  (>2026: 1 inicio + 11 fin) → error de captura.
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
| MCAR | 12 fechas futuras (apariciones aisladas) | Corregir/eliminar (0,0008 %) |
| MAR (semántico) | NaN de ocupación explicado 100 % por `emparejado` | NO imputar → **bandera** (`unknown`/`rescatado`) |
| MNAR | `university_level='None'` (quien no reporta nivel) | NO imputar moda → **re-categorizar** |

### 7.3 Métodos: cuál se usa y por qué los demás NO
| Método | ¿Aplica? | Por qué |
|---|---|---|
| Eliminar filas | **No** | <5 % + MCAR obligatorios; bloque es 6,97 % estructural; borra 64.508 personas (4.987 completas) |
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
  64.508 personas y 4.987 personas con historial completo `unknown`.
- **B — `'None'` en educación:** re-categorizar como categoría propia.
- **C — `'Present'` (76.180):** flag `vigente`; censura a la derecha solo si se requiere.

### 7.5 Normalización de categorías
**No aplica como limpieza** (0 colisiones verificadas en 2.966/426 labels). Se conserva solo como
**re-verificación defensiva** (`assert colisiones == 0`) y para enriquecimientos futuros (CV/ESCO).

### 7.6 Fechas y coherencia temporal
Formato `Q<n> <aaaa>` → ordinal `4*año+trimestre`; `start<=end` (0 violaciones); `'Present'` = vigente;
12 fechas futuras → tratar; 75.227 inicios ≤1990 → definir ventana temporal (decisión de negocio).

### 7.7 Umbrales de aceptación (regla del negocio)
Duplicados 0 · nulos restantes 0 (tras banderas) · categorías desconocidas 0 · fechas futuras 0 ·
`start>end` 0 · impacto 1.506.445 filas / 284.247 personas.

### 7.8 Bitácora prevista (documentable por el pipeline)
| Columna | Problema | Cantidad | % | Diagnóstico | Método | Por qué | Impacto |
|---|---|---|---|---|---|---|---|
| `occupation_code/label` | NaN | 115.169 | 7,64 % | MAR estructural | Bandera | "Sin emparejar" ≠ no dato | 64.508 personas |
| `isco_group/label/level` | NaN | 104.993 | 6,97 % | Ídem | Bandera | Ídem | Ídem |
| `university_level` | `'None'` | 174.036 | 11,55 % | MNAR | Re-categorizar | Moda inflaría mayoría | Sin inventar |
| `end_date` | `'Present'` | 76.180 | 5,06 % | Censura | Flag vigente | Fin inventado falsea duración | 5,06 % |
| `end_date/start_date` | futuras | 12 | 0 % | Error dominio | Corregir/eliminar | Imposible vs 2026 | 12 filas |
| `start>end` | — | 0 | 0 % | — | — | No existe | — |

---

## 8. OUTLIERS EN `empleos` (bloque 3)

### 8.1 ¿Dónde está el "edad 220 / 600 GB"?
**No existe**: sin columna numérica analítica (códigos texto, `isco_level` constante). Los únicos
puntuales reales = **12 fechas futuras** → tratar por dominio.

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
- **TRATAR:** 12 fechas futuras (error documentado). Winsorizar/imputar: condicional o no aplica.

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
| Outliers | gb_datos + edad/facturación/minutos imposibles | Sin numérica analítica; cola larga = señal; 12 fechas futuras |
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
estrategia de faltantes, outliers (IQR/Tukey), bitácora, rúbrica, comparativa, guía consolidada;
`script/` simplificado (eliminados `cruzar_datos.py` y `tablas.ipynb`; quedan `limpiar_datos.py` y
`Lectura.ipynb` como cuaderno de limpieza).

**Pendiente principal (bloque 4):** `script/limpiar_empleos.py` (clase `LimpiadorEmpleos`):
cargar `data/cruce/empleos.parquet` → 1 diagnóstico → 2 duplicados → 3 categorías (re-verificar) →
4 faltantes (banderas A–C) → 5 outliers (12 fechas → tratar; conservar cola larga) → 6 validación
(tabla §7.7 impresa) → 7 exportar `data/cruce/empleos_limpio` (csv + parquet). Con asserts por fase
(nivel "Excepcional") y `requirements.txt`.

**Decisiones de negocio anticipadas (a justificar):**
| # | Bloque | Cantidad | % | Tratamiento propuesto |
|---|---|---|---|---|
| 1 | `emparejado=unknown` | 104.993 | 6,97 % | Bandera (64.508 personas; 4.987 perderían todo) |
| 2 | `university_level='None'` | 174.036 | 11,55 % | Re-categorizar |
| 3 | `end_date='Present'` | 76.180 | 5,06 % | Flag `vigente` / censura |
| 4 | Traslapes | 429.958 | 28,54 % | Definir "transición" |
| 5 | Ventana temporal | 1955–2029 | — | Definir rango (+12 futuras) |
| 6 | Categorías canónicas | 3/5/426/2.966 | — | "Desconocidas: 0" sin romper ESCO |

**Diseño de integración histórico:** pendientes formales D1 (`unknown` en minería), D2 (empleos
simultáneos en transiciones), D3 (enriquecimiento temático), D4 (destino `data/procesada/`) —
relevantes en la fase de minería, no en la limpieza.

**Git:** rama `prueba` es la de trabajo (pusheada). `main` quedó con commits antiguos/junk del
compañero y `CRUCE_DATOS.md` desactualizado → **no merge aún**; unificar sobre la estructura de
`prueba`.

---

*Documento consolidado a partir de: README.md, README_DATOS.md, GUIA_LIMPLEZA_EMPLEOS.md,
EXPLICACION_TECNICA.md, DISEÑO_INTEGRACION.md, CIERRE_DISEÑO.md, AUDITORIA_LIMPLEZA.md.
Cifras verificadas sobre `data/cruce/empleos.parquet`.*