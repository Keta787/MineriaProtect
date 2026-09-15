# Contexto · Minería de Datos · Sesión 3 · Proyecto MineríaProtect

> Adaptación del material de la sesión 3 (que usa el caso TelecomUNO) a los datos y al
> pipeline del proyecto **MineríaProtect**. Donde un concepto o paso del curso no aplica
> a este proyecto, se marca explícitamente con **No aplica por: <razón>**.

## Datos generales

- **Curso:** Minería de Datos · UNIMINUTO Ibagué · Ingeniería de Sistemas · 2026-2 · Unidad 1
- **Docente:** Esteban Ernesto Morales Castro
- **Resultado de aprendizaje (Unidad 1):** "Aplica técnicas de preprocesamiento y exploración de datos para preparar conjuntos de datos con fines analíticos."
- **Tema:** Nulos, duplicados y outliers: convertir datos sucios en información confiable.
- **Proyecto:** MineríaProtect — análisis de trayectorias laborales (JobHop v2 + taxonomía ESCO).
- **Archivos del proyecto usados en esta sesión:**
  - `src/limpieza/limpiar_empleos.py` (pipeline de limpieza del integrado en 7 fases)
  - `notebooks/Diagnostico_Limpieza_Empleos.ipynb` (reproduce el pipeline con evidencia impresa)
  - `data/cruce/empleos.csv` → integrado crudo (entrada)
  - `data/cruce/empleos_limpio.csv` → integrado limpio (salida canónica)

## Archivos fuente (punto de partida de la limpieza)

- `data/cruce/empleos.csv` → integrado de entrada (1.506.445 filas × 11 columnas,
  284.247 personas). Trae problemas: 115.169 nulos de ocupación, 174.036 literales
  `'None'`, 76.180 literales `'Present'`, 11 fechas futuras y 141.591 duraciones fuera
  del IQR. **No tiene** duplicados exactos ni por llave natural.
- `data/cruce/empleos_limpio.csv` → archivo canónico de la limpieza
  (1.506.434 filas × 14 columnas). Es la meta/referencia contra la que validan los asserts.

> Diferencia con el caso del curso: TelecomUNO limpiaba un archivo sin procesar
> (`telecom_clientes_raw.csv` con 441 nulos y 60 duplicados); en MineríaProtect la
> limpieza es del **integrado** que ya había pasado por una limpieza previa de fuentes
> (JobHop + ESCO) y por el cruce. Por eso los duplicados ya son 0 y el énfasis está en
> nulos técnicos vs literales, censura y outliers.

## Diagnóstico real del integrado (fase 1 del pipeline)

```
Filas: 1.506.445 | Columnas: 11 | Personas (resume_id únicos): 284.247
Nulos técnicos:
  occupation_code     115.169
Literales de ausencia (no son NaN pandas):
  university_level   'None'    174.036
  end_date           'Present'  76.180
Duplicados exactos: 0 | Llave natural (resume_id+matched_code+start_date+end_date): 0
Llaves cortas: 74.357 (resume_id+start_date+end_date) | 9.601 (resume_id+start_date+matched_code)
Fechas "futuras" (año > 2026): 11 filas únicas  (1 inicio, 11 fines; la fila Q1 2027→Q1 2028 cuenta en ambos)
IQR de duración (trimestres): Q1=2, Q3=11, límite superior=24,5 | fuera: 141.591 filas / 97.954 personas
Duración máxima: 160 trimestres (40 años)
```

## Problemas clave del proyecto

1. **Nulos técnicos de ocupación** (115.169, MAR): el cargo de la hoja de vida no pudo
   asociarse a un código ESCO. Tratamiento: **2 banderas** (`es_unknown_ocupacion` 104.993 +
   `es_rescatado` 10.176), sin eliminar filas. Afecta a **64.508 personas** (2.490 con todo
   su historial `'unknown'`), verificado por assert del pipeline.
2. **Literal `'None'` en nivel educativo** (174.036, MNAR): el CV no reporta estudios.
   Tratamiento: recategorizar a `'No reportado'` (categoría propia, **sin imputar**).
   Quedan 174.035 en el limpio (una de las 11 filas futuras tenía este literal).
3. **Literal `'Present'` en fecha de fin** (76.180, censura): el empleo seguía vigente
   cuando se construyó el CV. Tratamiento: bandera `es_vigente` (no se inventa fecha de fin).
4. **Duplicados**: 0 exactos y 0 por llave natural; las 74.357/9.601 coincidencias por
   llaves cortas se **conservan** (se interpretan como pluriempleo o transiciones el mismo día).
5. **Fechas futuras** (11 filas, MCAR de dominio): error de captura posterior a 2026.
   Tratamiento: **eliminar** (es la única eliminación de filas de todo el pipeline).
6. **Outliers de duración** (141.591 filas / 97.954 personas arriba de 24,5 trimestres):
   **no winsorizar** (decisión de negocio documentada: cola larga = estabilidad real).

## Conceptos teóricos clave aplicados al proyecto

### Valores faltantes: MCAR / MAR / MNAR
- **MCAR:** la ausencia no depende de nada medible. Ej. del curso: el escáner falló una
  tarde. En **MineríaProtect no aplica** un escáner; el caso MCAR más claro son las
  **11 fechas futuras** (error de captura sin relación con otras variables).
- **MAR:** la ausencia se explica por otra variable observada. **Ocupación no emparejada**:
  depende de si el texto original del cargo pudo asociarse a ESCO, no del valor faltante.
- **MNAR:** la ausencia depende del valor mismo. **`'None'` educativo**: la falta de
  reporte está ligada al contenido de la hoja de vida (quienes no reportan estudios),
  así que no conviene imputar; se documenta como categoría `'No reportado'`.
- Discusión del curso adaptada: ¿los 76.180 `'Present'` son MCAR? **No**: son **censura
  por la derecha** (el empleo seguía activo al capturar el CV), un dato deliberadamente
  incompleto, no una pérdida aleatoria. Por eso se marca con bandera y no se elimina ni
  se imputa.

### Estrategias de imputación — aplicadas al proyecto
| Método | Cuándo (curso) | En MineríaProtect |
|---|---|---|
| Eliminar filas (dropna) | Faltan <5 % y patrón MCAR | Aplica solo a las **11 fechas futuras** (MCAR de dominio, <0,001 %). No aplica al resto: eliminar las 115.169 no emparejadas o los 76.180 vigentes destruiría personas completas. |
| Media | Numérica simétrica, sin outliers | **No aplica por:** el proyecto no imputa; son literales/nulos categóricos y de censura, no una numérica simétrica. |
| Mediana | Numérica asimétrica o con outliers | **No aplica por:** no hay columna numérica faltante que rellenar (la duración se deriva y los vigentes quedan como censura NaN). |
| Moda | Categóricas | **No aplica por:** el curso la usó para `pago_automatico`; el proyecto no tiene esa variable y decidió no inflar categorías: `'None'` pasa a categoría explícita. |
| Constante / bandera | La ausencia significa algo | **Es la estrategia del proyecto:** banderas `es_unknown_ocupacion`, `es_rescatado`, `es_vigente` + categoría `'No reportado'`. |
| KNN / regresión | Series correlacionadas | **No aplica por:** no hay series largas correlacionadas ni necesidad de complejidad; se documenta la ausencia en lugar de predecirla. |

Regla de oro (heredada y cumplida): toda decisión queda **documentada** en la bitácora del
pipeline — por fila: `columna, problema, cantidad, metodo, razon, impacto` (función `_anotar`).

### Duplicados
- Origen general: doble clic, reintentos de integración, fusión de respaldos.
- En **MineríaProtect**: **0** duplicados exactos y **0** por llave natural
  (`resume_id+matched_code+start_date+end_date`) — el integrado ya venía único desde la
  limpieza de fuentes y el cruce. No hay nada que eliminar; solo se **verifica y documenta**.
- Las llaves cortas (74.357 con `resume_id+start_date+end_date`; 9.601 con
  `resume_id+start_date+matched_code`) **no** son duplicados: se conservan y se interpretan
  como pluriempleo o transiciones el mismo día (inferencia, no hecho confirmado).
- **Diferencia con TelecomUNO:** ahí se eliminaron 60 repetidos (`drop_duplicates`);
  aquí la regla equivalente no encontró ninguno, así que el paso produce 0 cambios.

### Outliers: tratar vs conservar (decisión de NEGOCIO, no solo estadística)
- **Error de digitación** (curso: edad 220) → corregir o eliminar. **En MineríaProtect**:
  las **11 fechas futuras** >2026 son el equivalente (error de captura/transcripción) → eliminar.
- **Error de unidad** (curso: 600 GB que en realidad son megabytes) → convertir, no borrar.
  **No aplica por:** el integrado no tiene columnas con unidades físicas (duración en
  trimestres y fechas ya normalizadas).
- **Valor real extremo** (curso: empresa VIP factura 380.000) → conservar. **En
  MineríaProtect**: las carreras de hasta **40 años** son estabilidad real → conservar
  (bitácora: "Carreras de ~40 años son estabilidad real; borrar segmenta personas completas").
- **Censura `'Present'`**: no es outlier; es un dato activo sin fin conocido → bandera, nunca inventar fin.

### Regla IQR (Tukey) aplicada a la duración en trimestres
```
Q1 = 2      Q3 = 11
IQR = 11 - 2 = 9
Límite sup = 11 + 1.5*9 = 24,5   (límite inf = 2 - 13,5 = -11,5, irrelevante; todo cae arriba)
141.591 filas / 97.954 personas fuera → NO winsorizar (decisión de negocio documentada)
máximo observado: 160 trimestres (40 años)
```
**Diferencia con TelecomUNO:** en el curso `gb_datos` se winsorizó con `clip()` (28 clientes
fuera); en MineríaProtect la cola larga **es la señal** (estabilidad laboral), así que se
conserva. El IQR se calcula sobre el **original, sin imputar** (los vigentes quedan excluidos
de la duración como censura NaN).

### Z-score
```
z = (dur - media) / std     media ≈ 9,94   std ≈ 14,02
|z| > 3  →  33.841 filas (solo comparación; el pipeline lo reporta, no lo usa como criterio)
```
En TelecomUNO el z-score destapó la edad de 220 (z = 9,1); aquí el criterio oficial es IQR.

### Comparación IQR vs Z-score
| Criterio | IQR | Z-score |
|---|---|---|
| Se apoya en | Cuartiles | Media y desviación |
| Resistencia a outliers | Alta (robusto) | Baja |
| Requiere normalidad | No | Aproximadamente sí |
| Úsese con | Asimétricas, colas largas | Simétricas controladas |

Regla del curso (**cumplida**): **IQR por defecto** (los datos laborales tienen cola larga).

## Pipeline del proyecto (`src/limpieza/limpiar_empleos.py`)

Orden del pipeline: **diagnóstico → duplicados → categorías → faltantes → outliers →
validación → exportar**. Cada fase escribe su entrada en la bitácora y cierra con **asserts**
contra las cifras verificadas.

- **fase1_diagnostico:** dimensión (1.506.445×11), personas (284.247), tipos de dato, nulos
  técnicos y literales (115.169 / 174.036 / 76.180). No toca nada.
- **fase2_duplicados:** verifica exactos = 0 y llave natural = 0 (PK =
  `resume_id+matched_code+start_date+end_date`); cuenta llaves cortas (74.357 / 9.601) y las
  conserva. Asserts: 0 duplicados exactos, 0 por PK, y claves cortas **iguales a la
  auditoría** (74.357 y 9.601).
- **fase3_categorias:** re-verifica la cardinalidad de las columnas canónicas contra los
  valores esperados (a partir de `self.original`) y luego re-categoriza el caso B (MNAR):
  `'None'` → `'No reportado'`. Asserts: queda **0** `'None'` y el conteo de `'No reportado'`
  iguala al de `'None'` original (174.036). Tras fase5 (una de las 11 filas futuras tenía
  este literal) quedan **174.035** en el limpio.
- **fase4_faltantes:** genera las banderas desde las columnas originales (`emparejado ==
  'unknown'/'rescatado'`, `end_date == 'Present'`): `es_unknown_ocupacion` (104.993),
  `es_rescatado` (10.176) y `es_vigente` (76.180). Asserts: todo NaN de `occupation_code`
  está explicado por alguna bandera, `es_unknown + es_rescatado == 115.169`, y las personas
  `'unknown'` son **64.508**. El dataset pasa a **14 columnas**.
- **fase5_outliers:** IQR sobre `dur_Q` del original (Q1=2, Q3=11, límite 24,5 →
  141.591 filas / 97.954 personas, todas por arriba; **no winsorizar**) y **elimina las 11
  fechas futuras**. Asserts: 141.591 y exactamente 11 eliminadas.
- **fase6_validacion:** tabla de umbrales con 6 criterios verificados en **0** — duplicados
  exactos, duplicados por PK, nulos restantes sin bandera, nulos de ocupación sin bandera,
  fechas futuras y `start > end` — más el assert de que se eliminaron **exactamente 11
  filas** (1.506.445 → 1.506.434).
- **fase7_exportar:** assert de que el **original no cambió** (1.506.445 filas) y graba
  `data/cruce/empleos_limpio.csv` con las 14 columnas finales.

Reproducido con evidencia impresa en `notebooks/Diagnostico_Limpieza_Empleos.ipynb`.
Orden idéntico al del curso (duplicados y categorías antes que outliers) salvo que aquí no
hay paso de **imputación** (reemplazado por **construcción de banderas**).

## Código de categorías (fase 3 del proyecto)

```python
# Caso B (MNAR): el literal 'None' pasa a categoria propia 'No reportado'.
# No se imputa moda: fabricaria educacion para 174.036 filas.
n_none = int(self.df["university_level"].eq("None").sum())
self.df["university_level"] = self.df["university_level"].replace({"None": "No reportado"})
assert int(self.df["university_level"].eq("None").sum()) == 0, "Queda 'None' sin re-categorizar"
assert int(self.df["university_level"].eq("No reportado").sum()) == n_none
self._anotar("university_level", "Literal 'None' (MNAR)", n_none,
             "Re-categorizar a 'No reportado'",
             "Imputar la moda fabricaria educacion para esa fila.",
             "Categoria propia, sin None restante.")
```

> El curso normalizaba ciudades y planes (strip/lower/sin_tildes/mapeo). **No aplica por:**
> el integrado no tiene variables categóricas con escrituras inconsistentes (los códigos ESCO
> e ISCO ya vienen normalizados de las fuentes); la única categoría sucia era el literal
> `'None'`.

## Código de outliers (fase 5 del proyecto)

```python
dur = self._duracion_trimestres().dropna()   # 'Present' (sin fin) -> NaN: censura excluida
limites = self._limites_iqr(dur)             # Q1=2, Q3=11, IQR=9, sup=24,5
fuera = (dur < limites["inferior"]) | (dur > limites["superior"])   # 141.591 filas / 97.954 personas

def _es_futura():
    f_ini = self._extraer_anio("start_date")
    f_fin = self._extraer_anio("end_date")
    return (f_ini > ANIO_CORTE) | (f_fin > ANIO_CORTE)   # ANIO_CORTE = 2026

futura = _es_futura()
self.df = self.df.loc[~futura].reset_index(drop=True)    # 11 filas únicas (única eliminación)
```

## Esquema del dataset limpio (empleos_limpio.csv)

14 columnas: `resume_id` (int64); `start_date`, `end_date`, `university_level`,
`matched_code`, `emparejado`, `occupation_code`, `occupation_label`, `isco_group`,
`isco_group_label` (str); `isco_level` (float64); `es_unknown_ocupacion`, `es_rescatado`,
`es_vigente` (bool).

> En el CSV todo se guarda como **texto** (los códigos conservan ceros a la izquierda, p. ej.
> ISCO `0110`). Al cargar, el cuaderno/script restauran los tipos reales: `resume_id`
> (entero), `isco_level` (float) y las banderas `es_*` (booleano); la celda vacía es el único
> `NaN` (`keep_default_na=False`).

Muestra (3 filas reales):
```
resume_id  start_date  end_date  university_level  occupation_label          isco_group  isco_group_label
0          Q3 1996     Q1 2000   Master            language school teacher   2353        Other language teachers
1          Q1 1994     Q4 1996   Bachelor          infantry soldier          0310        Armed forces occupations, other ranks
2          Q1 2005     Q1 2014   Bachelor          accountant                2411        Accountants
```

> **No aplica la "columna objetivo `fuga`":** TelecomUNO preparaba un modelo de clasificación
> de fuga; MineríaProtect es análisis de trayectorias (transiciones, duración, brechas), no
> de clasificación, así que no hay variable objetivo en esta etapa.

## Validación final (vista del pipeline)

| Verificación | TelecomUNO (curso) | MineríaProtect (proyecto) |
|---|---|---|
| Contra qué | `telecom_clientes_limpio.csv` canónico (2.400 filas, 0 nulos) | Cifras verificadas de la auditoría, vía **asserts** (1.506.434×14, 11 futuras, 141.591, 174.035 `'No reportado'`) |
| Nulos faltantes | 0 | No se imputan; ausencias convertidas en **banderas/categoría** |
| Duplicados | 60 eliminados | 0 ya; llaves cortas conservadas |
| Outliers | `gb_datos` winsorizado (clip) | Duración **no winsorizada** (cola larga = estabilidad) |

## Ejercicio del curso adaptado a MineríaProtect (lo que ya verifica el pipeline)

1. Diagnosticar con `isna().sum()`, `duplicated().sum()` y conteo de literales; listar los
   6 problemas con cifras (hecho: fase1).
2. Verificar duplicados (0) y documentar llaves cortas 74.357/9.601 como pluriempleo.
3. Recategorizar `'None'` → `'No reportado'` y justificar MNAR.
4. Crear banderas MAR (ocupación) y censura (`es_vigente`) sin imputar.
5. IQR sobre la duración original (Q1=2, Q3=11, 141.591/97.954) y eliminar las 11 futuras.
6. Validar con la tabla de 6 umbrales (todas en 0) + assert de **exactamente 11 filas
   eliminadas**, y exportar el CSV con las 14 columnas.

### Errores frecuentes a evitar (proyecto)
- Imputar `'Present'` o tratar la censura como un nulo que se rellena (debe quedar como bandera).
- `dropna()` global: borraría 76.180 vigentes y 115.169 no emparejadas sin distinción.
- Calcular el IQR sobre datos ya imputados o sobre el limpio y reportarlo como original.
- Eliminar las filas `es_unknown_ocupacion` "porque no tienen código" (se pierde la persona).
- Confundir nulos técnicos (NaN) con literales (`'None'`, `'Present'`).
- Reportar "12 fechas futuras" en vez de 11 al no contemplar la unión de criterios.
- Sobrescribir `empleos.csv` (el original es intocable).
- Limpiar sin bitácora (qué cambió, cuántos, con qué criterio) ni asserts.

## Rúbrica de código (aplica a todo entregable programado)

- **Funcionalidad 40%:** el pipeline ejecuta sin errores, transforma correctamente y valida
  contra criterios explícitos (filas, nulos, rangos) — aquí: asserts de la fase 6.
- **Justificación técnica 30%:** cada decisión defendida con conceptos (MCAR/MAR/MNAR, IQR,
  censura, contexto de negocio).
- **Documentación 20%:** qué hace cada fase y por qué existe; hallazgos en texto legible
  (bitácora `_anotar`).
- **Reproducibilidad 10%:** rutas relativas, requisitos declarados, cuaderno que reproduce
  el script.

Escalera de logro: Inicio → Progreso → Esperado (pipeline completo validado, justificado y
documentado) → Excepcional (funciones reutilizables + pruebas automáticas). El pipeline de
`limpiar_empleos.py` está en nivel **Excepcional** (funciones reutilizables por fase +
asserts automáticos + bitácora).

## Casos de la vida real (motivación de la sesión)

> Casos externos al dataset; **no aplican como datos del proyecto**, pero son la motivación
> de por qué la limpieza es crítica.

1. **Reino Unido · COVID-19 (2020):** Public Health England truncó ~16.000 casos por el
   límite de ~65.000 filas de Excel. Lección: validar límites y automatizar con código
   reproducible (en MineríaProtect: asserts + CSV, no Excel).
2. **Hospitales EE. UU.:** miles de millones anuales por errores de digitación en reclamos
   médicos.
3. **Banca colombiana:** cargar centavos en un sistema de pesos duplica saldos y dispara
   alertas falsas.
4. **TelecomUNO (caso del curso):** usar la media de edad contaminada (edades 220) para
   campañas llamaría a segmentos inexistentes.

## Trabajo independiente (para sesión 4)

1. **Lectura (2 h):** Han, Kamber & Pei, sección 2.3 (preprocesamiento) + artículo MCAR/MAR/MNAR.
2. **Proyecto (2 h):** revisar que cada decisión de `limpiar_empleos.py` tenga bitácora y
   assert; el integrado limpio ya está listo.
3. **Estado del proyecto:** fuentes limpias e integradas, integrado limpio validado. La
   siguiente etapa oficial es **seleccionar la técnica de minería** (anticipando transformación
   y reducción: escaladores, codificación y PCA en sesión 4).