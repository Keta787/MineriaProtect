# Contexto · Minería de Datos · Sesión 3: Limpieza de Datos

## Datos generales

- **Curso:** Minería de Datos · UNIMINUTO Ibagué · Ingeniería de Sistemas · 2026-2 · Unidad 1
- **Docente:** Esteban Ernesto Morales Castro
- **Duración:** 2 horas (120 minutos)
- **Resultado de aprendizaje (Unidad 1):** "Aplica técnicas de preprocesamiento y exploración de datos para preparar conjuntos de datos con fines analíticos."
- **Tema:** Nulos, duplicados y outliers: convertir datos sucios en información confiable.
- **Archivos de la sesión:**
  - `presentacion.html` (24 slides, material del docente)
  - `codigo/limpieza_telecom.py` (pipeline completo de limpieza)
  - `datasets/telecom_limpio_propio.csv` (salida del pipeline del docente)

## Archivos fuente (datasets_base, fuera de esta carpeta)

- `telecom_clientes_raw.csv` → dataset crudo (2.460 filas) con problemas: 441 nulos, 60 duplicados, 16 escrituras de ciudad, 11 escrituras de plan, edades 0–220, facturación negativa, GB hasta 616.
- `telecom_clientes_limpio.csv` → archivo canónico limpio (2.400 filas, 0 nulos). Es la meta/referencia de validación.

## Diagnóstico real del dataset crudo

```
edad                   123
facturacion_mensual    148
pago_automatico        170
Duplicados: 60
         edad  facturacion_mensual  gb_datos
count  2337.0               2312.0    2460.0
mean     49.0             106064.6      12.8
min       0.0              -6459.0       0.0
max     220.0             227829.0     616.4
```

Problemas clave:
1. **Nulos:** 441 en 3 columnas (edad, facturacion_mensual, pago_automatico).
2. **Duplicados exactos:** 60 registros repetidos.
3. **Inconsistencias categóricas:** 16 escrituras para 5 ciudades reales; 11 escrituras para 3 planes (Basico/Estandar/Premium).
4. **Valores imposibles:** edades 0–220 (rango humano plausible 18–90), facturación negativa, minutos negativos, GB de hasta 616 (error de unidad, megabytes).

## Conceptos teóricos clave

### Valores faltantes: MCAR / MAR / MNAR
- **MCAR** (Missing Completely At Random): la ausencia no depende de nada medible. Imputar es seguro. Ej.: el escáner falló una tarde.
- **MAR** (Missing At Random): la ausencia se explica por OTRA variable observada. Imputar condicionando por grupos (edad, ciudad). Ej.: los jóvenes no reportan ingresos.
- **MNAR** (Missing Not At Random): la ausencia depende del valor mismo que no vemos. Imputar distorsiona; mejor marcar bandera y consultar al negocio. Ej.: quienes más facturan lo ocultan.
- Discusión del curso: ¿los 170 nulos de `pago_automatico` son MCAR (falló migración) o MNAR (clientes sin domiciliación no responden la encuesta)? El origen decide el método.

### Estrategias de imputación
| Método | Cuándo | Riesgo principal |
|---|---|---|
| Eliminar filas (dropna) | Faltan <5% y patrón MCAR | Perder segmentos pequeños |
| Media | Numérica simétrica, sin outliers | Sensible a extremos (220 años) |
| **Mediana** | Numérica asimétrica o con outliers | Aplana variabilidad si abusa |
| Moda | Categóricas (pago_automatico, plan) | Infla la categoría mayoritaria |
| Constante / bandera | La ausencia significa algo | Categorías artificiales |
| KNN / regresión | Series largas correlacionadas | Complejidad y fuga de información |

Regla de oro: toda imputación debe quedar **documentada** (columna, método y por qué).

### Duplicados
- Origen: doble clic en formularios, integraciones que reintentan, fusiones de respaldos mal hechas.
- Efecto: conteos inflados, medias sesgadas, el modelo cree que un cliente importa el doble.
- `drop_duplicates()` quita filas idénticas en TODO. Si comparten `id_cliente` pero difieren en campos, usar `drop_duplicates(subset=["id_cliente"], keep="first"/"last")`.

### Outliers: tratar vs conservar (decisión de NEGOCIO, no solo estadística)
- **Error de digitación** (edad 220) → corregir o eliminar.
- **Error de unidad** (600 GB cuando todos usan ~11 = megabytes) → convertir unidades, no borrar.
- **Valor real extremo** (empresa con 400 líneas factura 380.000) → conservar (fraude o VIP).
- En detección de fraude, el outlier ES la señal; en un promedio de consumo, es contaminación.

### Regla IQR (Tukey) aplicada a gb_datos
```
Q1 = 6.07   Q3 = 12.31
IQR = 12.31 - 6.07 = 6.24
Límite inf = 6.07 - 1.5*6.24 = -3.29
Límite sup = 12.31 + 1.5*6.24 = 21.67
28 clientes fuera (todos por arriba) → winsorizar (clip), no eliminar
```

### Z-score
```
z = (x - media) / std
z(220 años) = (220 - 49.0) / 18.8 = 9.1   # |z| > 3 es sospechoso
```

### Comparación IQR vs Z-score
| Criterio | IQR | Z-score |
|---|---|---|
| Se apoya en | Cuartiles | Media y desviación |
| Resistencia a outliers | Alta (robusto) | Baja |
| Requiere normalidad | No | Aproximadamente sí |
| Úsese con | Asimétricas, colas largas | Simétricas controladas |

Regla del curso: **IQR por defecto** (los datasets comerciales casi siempre tienen colas largas).

## Pipeline completo del docente (codigo/limpieza_telecom.py)

Orden del pipeline (importante): **duplicados → categorías → nulos → outliers → validación**.

- **PASO 0 · Diagnóstico:** `isna().sum()`, `duplicated().sum()`, `describe()` → filas=2460, nulos=441, duplicados=60.
- **PASO 1 · Duplicados:** `df.drop_duplicates().reset_index(drop=True)` → 2.400 filas, nulos=432.
- **PASO 2 · Categorías uniformes:** `str.strip().str.lower()` → `sin_tildes()` (normalizar NFKD a ASCII) → `replace(MAPA_CIUDAD)` para ciudad; `str.capitalize()` para plan. Resultado: 5 ciudades, 3 planes, 0 desconocidas.
- **PASO 3 · Faltantes:** medianas para `edad` (49.0) y `facturacion_mensual` (105701.0); moda ("No") para `pago_automatico`. Resultado: 0 nulos. (Se usa mediana y no media porque convive con edades de 220; `mode()[0]` por si hay empates; `fillna` no modifica en sitio → hay que reasignar a la columna.)
- **PASO 4 · Outliers:** IQR en `gb_datos` → límites [-3.30, 21.67], 28 valores fuera → `clip()` (winsorizar). Correcciones de imposibles: edades fuera de [18,90] → mediana; facturación negativa → mediana; minutos negativos → 0.
- **PASO 5 · Validación contra canónico:**
  ```
  Nuestro pipeline : filas=2400  nulos=0
  Archivo canónico : filas=2400  nulos=0
  ¿Coinciden filas y nulos? True
  media_edad         48.9 vs 49.0
  media_facturacion  106045 vs 105876
  ```

### Código de imputación
```python
for col in ["edad", "facturacion_mensual"]:
    mediana = df[col].median()
    df[col] = df[col].fillna(mediana)

moda_pago = df["pago_automatico"].mode()[0]
df["pago_automatico"] = df["pago_automatico"].fillna(moda_pago)
```

### Código de categorías
```python
import unicodedata
def sin_tildes(texto):
    return unicodedata.normalize("NFKD", texto).encode("ascii","ignore").decode()

MAPA = {"ibague": "Ibagué", "cali": "Cali", "bogota": "Bogotá",
        "medellin": "Medellín", "espinal": "Espinal"}

df["ciudad"] = (df["ciudad"].str.strip().str.lower()
                .apply(sin_tildes).replace(MAPA))
df["tipo_plan"] = (df["tipo_plan"].str.strip().str.lower()
                   .apply(sin_tildes).str.capitalize())
```

### Código de outliers (pista para el ejercicio)
```python
mascara = (df["edad"] < 18) | (df["edad"] > 90)
df.loc[mascara, "edad"] = df["edad"].median()   # evita SettingWithCopyWarning
df["gb_datos"] = df["gb_datos"].clip(lim_inf, lim_sup)
```

## Esquema del dataset limpio (telecom_limpio_propio.csv)

Columnas: `id_cliente, edad, ciudad, tipo_plan, facturacion_mensual, antiguedad_meses, minutos_llamada, gb_datos, num_quejas, pago_automatico, fecha_contrato, fuga`

Muestra (3 filas):
```
id_cliente,edad,ciudad,tipo_plan,facturacion_mensual,antiguedad_meses,minutos_llamada,gb_datos,num_quejas,pago_automatico,fecha_contrato,fuga
TEL-2038,20.0,Ibagué,Estandar,160086.0,82,410.4,8.67,1,No,2022-12-03,No
TEL-1979,21.0,Ibagué,Premium,78311.0,59,580.5,8.65,1,Si,2020-08-28,No
TEL-0856,71.0,Cali,Basico,144989.0,15,211.1,10.27,2,No,2020-01-23,No
```

Categorías válidas: ciudades = Ibagué, Cali, Bogotá, Medellín, Espinal; planes = Basico, Estandar, Premium; pago_automatico = Si/No; fuga = Si/No (columna objetivo de clasificación, sesiones posteriores).

## Ejercicio en clase (mision)

Producir `telecom_limpio_propio.csv` comparable con el canónico (2.400 filas, 0 nulos) defendiendo cada decisión:
1. (5 min) Diagnosticar con `isna().sum()`, `duplicated().sum()`, `describe()`; listar los 5 problemas con cifras.
2. (10 min) Duplicados y categorías (strip, tildes, mapeo): 2.400 filas, 5 ciudades, 3 planes.
3. (10 min) Imputar nulos columna por columna con comentario del método y su justificación (mediana/moda/bandera).
4. (7 min) IQR a `gb_datos` y corregir edades/facturación/minutos imposibles; reportar cuántos valores se tocaron.
5. (3 min) Validar contra `telecom_clientes_limpio.csv` (filas y nulos) y exportar CSV.

### Errores frecuentes a evitar
- `fillna(0)` "porque sí" (distorsiona medias/modelos).
- `dropna()` global (pierde 400+ registros útiles sin justificar).
- Sobrescribir el CSV original (el original es intocable).
- Calcular IQR sobre datos ya imputados y reportarlo como original.
- `df[fila][col] = x` → SettingWithCopyWarning; usar `df.loc[mascara, col]` y `df.copy()`.
- Imputar antes de quitar duplicados (el orden importa).
- Limpiar sin bitácora (qué cambió, cuántos valores, con qué criterio).

## Rúbrica de código (aplica a todo entregable programado)

- **Funcionalidad 40%:** el pipeline ejecuta sin errores, transforma correctamente y valida contra criterios explícitos (filas, nulos, rangos).
- **Justificación técnica 30%:** cada decisión defendida con conceptos (MCAR/MAR/MNAR, IQR, contexto de negocio).
- **Documentación 20%:** qué hace cada bloque y por qué existe; hallazgos en texto legible.
- **Reproducibilidad 10%:** rutas relativas, semillas fijas, requisitos declarados.

Escalera de logro: Inicio (limpia 1 dimensión con guía) → Progreso (pipeline parcial) → Esperado (pipeline completo validado, justificado y documentado) → Excepcional (funciones reutilizables + pruebas automáticas).

## Casos de la vida real (motivación de la sesión)

1. **Reino Unido · COVID-19 (2020):** Public Health England truncó ~16.000 casos por el límite de ~65.000 filas de Excel (.xls). Lección: validar límites y automatizar con código reproducible.
2. **Hospitales EE. UU.:** miles de millones anuales por errores de digitación en reclamos médicos.
3. **Banca colombiana:** cargar centavos en un sistema de pesos duplica saldos y dispara alertas falsas.
4. **TelecomUNO (caso del curso):** usar la media de edad contaminada (edades 220) para campañas llamaría a segmentos inexistentes.

## Trabajo independiente (para sesión 4)

1. **Lectura (2 h):** Han, Kamber & Pei, sección 2.3 (preprocesamiento) + artículo MCAR/MAR/MNAR.
2. **Práctica (2 h):** completar ejercicio hasta validación verde + informe corto (1 página) de qué imputó, con qué método y por qué.
3. **Proyecto (2 h):** aplicar el mismo pipeline al dataset alternativo del equipo.

**Anticipo sesión 4 · Transformación y Reducción:** escaladores, codificación one-hot, discretización y PCA.