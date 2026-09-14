# Contexto · Minería de Datos · Sesión 1: Introducción a la Minería de Datos

## Datos generales

- **Curso:** Minería de Datos · UNIMINUTO Ibagué · Ingeniería de Sistemas · 2026-2 · Unidad 1
- **Docente:** Esteban Ernesto Morales Castro
- **Duración:** 2 horas (120 minutos)
- **Resultado de aprendizaje (Unidad 1):** "Aplica técnicas de preprocesamiento y exploración de datos para preparar conjuntos de datos con fines analíticos." Hoy damos el primer paso: entender el mapa completo antes de caminarlo.
- **Tema:** Conceptos, proceso KDD y metodología CRISP-DM.
- **Archivos de la sesión:**
  - `presentacion.html` (24 slides, material del docente)
  - `codigo/exploracion_inicial.py` (exploración inicial del dataset del proyecto)
  - (Referencia externa) `datasets_base/telecom_clientes_raw.csv` → dataset crudo del proyecto integrador

## Objetivos de aprendizaje

1. **Explicar** qué es la minería de datos y diferenciarla de estadística descriptiva, inteligencia de negocios y aprendizaje automático.
2. **Describir** el proceso KDD (Knowledge Discovery in Databases) etapa por etapa, reconociendo el papel de cada una.
3. **Identificar** las seis fases de la metodología CRISP-DM y su carácter iterativo.
4. **Explorar** un primer dataset real con pandas y formular el problema de negocio del proyecto integrador del semestre.

## Agenda · 120 minutos

| Hora | Bloque |
|---|---|
| 00:00 – 00:10 | Bienvenida, acuerdos del curso y presentación del proyecto integrador |
| 00:10 – 00:30 | Teoría I: qué es (y qué no es) la minería de datos · pirámide dato-información-conocimiento (DIKW) |
| 00:30 – 00:55 | Teoría II: proceso KDD y metodología CRISP-DM · tipos de tareas de minería |
| 00:55 – 01:05 | Pausa activa y casos reales colombianos |
| 01:05 – 01:25 | Demo guiada: primer vistazo al dataset TelecomUNO con pandas |
| 01:25 – 02:05 | Ejercicio en clase: exploración inicial y definición del problema de negocio (equipos) |
| 02:05 – 02:15 | Socialización, evaluación de la sesión y trabajo independiente para la próxima semana |

## Punto de partida (conexión con asignaturas previas)

- En **Diseño de Algoritmos** y programación se aprende a *construir* software; aquí se aprende a hacer que los datos *cuenten una historia útil*.
- En **Bases de Datos** se almacena y consulta; la minería responde preguntas que ni el mejor SELECT imagina: *"¿qué clientes se irán el mes próximo?"*.
- La minería de datos es el puente entre almacenar información y predecir/decidir con ella.

La asignatura hereda de tres pilares:
- **Estadística** → base matemática: muestreo, distribuciones, inferencia.
- **Inteligencia Artificial** → algoritmos que aprenden patrones: clasificadores, clustering.
- **Bases de Datos** → escala y acceso: millones de registros consultables eficientemente.

## Conceptos teóricos clave

### ¿Qué es la minería de datos?

> "Proceso de descubrir patrones válidos, novedosos, potencialmente útiles y comprensibles a partir de grandes volúmenes de datos." — Fayyad, Piatetsky-Shapiro & Smyth (1996)

| SÍ es | NO es |
|---|---|
| Descubrir patrones ocultos no evidentes | Reportes o tableros de lo que YA pasó (eso es BI) |
| Predecir comportamientos futuros | Consultas SQL tradicionales de agregados |
| Segmentar, asociar, detectar anomalías | "Buscar" manualmente en Excel hasta encontrar algo |
| Apoyar decisiones de negocio medibles | Mágica: basura entra, basura sale |

**Analogía:** el BI es como el espejo retrovisor (mira atrás); la minería de datos es el parabrisas con radar (anticipa lo que viene).

### Escalera DIKW (dato → decisión)

1. **DATO:** "Cliente TEL-0007, 34 años, plan Básico, 5 quejas." (sin contexto, solo existe).
2. **INFORMACIÓN:** "El 62% de quienes presentan más de 3 quejas tienen plan Básico." (datos organizados y comparados).
3. **CONOCIMIENTO:** "Las quejas repetidas sin respuesta anticipan la fuga del cliente." (patrones explicables).
4. **DECISIÓN:** "Priorizar llamadas de retención a clientes con 3+ quejas." (acción con valor económico).

La minería de datos habita el tramo **información → conocimiento**; el ser humano cierra el ciclo con la decisión.

### KDD: Knowledge Discovery in Databases (6 etapas)

1. **Selección:** elegir los datos relevantes al problema desde las fuentes (BD, APIs, CSV).
2. **Preprocesamiento:** limpiar nulos, duplicados, ruido, inconsistencias. La etapa que más tiempo consume (60–80%).
3. **Transformación:** normalizar, discretizar, reducir dimensiones para que los algoritmos rindan.
4. **Minería de datos:** aplicar el algoritmo (árbol de decisión, K-means, Apriori...). Es solo 1 de las 6 etapas.
5. **Interpretación / Evaluación:** ¿los patrones son útiles y comprensibles? ¿Generalizan o fue suerte?
6. **Conocimiento:** comunicarlo y usarlo en la decisión de negocio. Si nadie actúa, no valió la pena.

### CRISP-DM: el ciclo que se usa todo el semestre

1. **Entendimiento del negocio:** qué problema resolver y cómo se medirá el éxito.
2. **Entendimiento de los datos:** recolectar, describir, explorar (EDA) y verificar calidad.
3. **Preparación de los datos:** limpieza + transformación + selección de variables. Itera constantemente.
4. **Modelado:** elegir y entrenar técnicas (clasificación, clustering, asociación).
5. **Evaluación:** métricas + revisión frente al objetivo de negocio.
6. **Despliegue:** entregar el modelo/reporte a quien decide. Monitorear en producción.

**No es lineal:** la evaluación suele devolvernos a preparación o incluso a entender mejor el negocio. Es un ciclo.

### KDD vs CRISP-DM vs SEMMA

| Aspecto | KDD (Fayyad, 1996) | CRISP-DM (1999) | SEMMA (SAS) |
|---|---|---|---|
| Origen | Académico | Consorcio industrial (SPSS, Daimler) | Fabricante SAS |
| Etapas | Selección → preproc. → transformación → minería → interpretación | Negocio → datos → preparación → modelado → evaluación → despliegue | Sample, Explore, Modify, Model, Assess |
| Fortaleza | Claridad conceptual | Inicia en el NEGOCIO, es iterativa, la más usada (~85% de proyectos) | Simple, ligada a herramienta |
| Debilidad | Omite el negocio y el despliegue | Exige disciplina documental | Parcial, sesgada a SAS |

**Este curso sigue CRISP-DM:** cada sesión y cada corte del proyecto corresponde a fases concretas del ciclo.

### Tareas de minería (qué preguntas responde)

| Tarea | Pregunta ejemplo | Tipo |
|---|---|---|
| Clasificación | "¿Este cliente se fuga: Sí/No?" | Categorías conocidas de antemano |
| Regresión | "¿Cuánto pagará este cliente el próximo mes?" | Predice valores numéricos |
| Clustering | "¿Qué perfiles naturales de clientes existen?" | Grupos SIN etiquetas previas |
| Reglas de asociación | "¿Qué productos se compran juntos?" | Si-compra-X entonces-compra-Y |
| Detección de anomalías | "¿Esta transacción es fraudulenta?" | Lo raro vale oro |
| Minería de texto / series | "¿Qué sienten los clientes en sus reseñas? ¿Cómo evolucionará el consumo?" | Texto y temporales |

El proyecto integrador tocará: clasificación (sesiones 7-8), clustering (9), asociación (10), series/anomalías (13) y texto (14).

## Análisis del código (codigo/exploracion_inicial.py)

Script que ejecuta la exploración inicial del dataset del proyecto. Líneas clave y qué hacen:

```python
import pandas as pd
from pathlib import Path

RUTA = Path(__file__).resolve().parents[2] / "datasets_base" / "telecom_clientes_raw.csv"

df = pd.read_csv(RUTA)                       # 1. Cargar el CSV crudo
print("Dimensiones (filas, columnas):", df.shape)   # (2460, 12)
print(df.head())                             # 3. Primeras 5 filas
df.info()                                    # 4. Tipos y nulos por columna
print(df.describe().round(1))                # 5. Resumen estadístico de numéricas

# 6. Tasa de fuga global (17%)
print(df["fuga"].value_counts(normalize=True).round(3))

# 7. Fuga por tipo de plan (normaliza texto rudimentariamente)
df["plan_normalizado"] = df["tipo_plan"].str.strip().str.capitalize()
tabla = pd.crosstab(df["plan_normalizado"], df["fuga"], normalize="index")

# 8. Diagnóstico de calidad
print(df.isna().sum()[lambda s: s > 0])      # nulos por columna
print("Filas duplicadas:", int(df.duplicated().sum()))  # 60
print("Edades imposibles:", int((df["edad"] > 100).sum() + (df["edad"] < 10).sum()))
print("Facturación negativa:", int((df["facturacion_mensual"] < 0).sum()))
```

Salidas esperadas (datos reales):
```
Dimensiones: (2460, 12)
edad                   123
facturacion_mensual    148
pago_automatico        170
Duplicados: 60
```

Hallazgos que se descubren "sin escribir casi código":
- `edad` máxima 220 años → outlier imposible.
- Facturación negativa → error de registro.
- 17% de fuga → clases desbalanceadas.
- Plan Básico fuga más que Premium.

## Proyecto integrador TelecomUNO

**Contexto de negocio:** operadora regional ficticia con 2.400 clientes en el Tolima y el eje cafetero; pierde ~17% de sus clientes al año. Recuperar un cliente cuesta 5 veces más que retener uno.

**Pregunta de negocio:** *"¿Qué clientes van a fugarse y qué podemos hacer para retenerlos?"*

| Corte | Peso | Avance | Fases CRISP-DM | Sesiones |
|---|---|---|---|---|
| Avance 1 | 30% | Dataset preprocesado y documentado | Negocio · Datos · Preparación | 1 – 6 |
| Avance 2 | 35% | Modelos aplicados y comparados | Preparación · Modelado | 7 – 11 |
| Final | 35% | Modelo evaluado + recomendaciones + sustentación | Evaluación · Despliegue | 12 – 16 |

**Variable objetivo:** `fuga` (Si/No) → tarea de **clasificación**.

## Esquema del dataset crudo (telecom_clientes_raw.csv)

```
# 2.460 filas x 12 columnas
id_cliente            identificador unico          [texto]
edad                  18 - 80 anos                 [numerica]
ciudad                Ibagué, Cali, Medellín...    [categorica]
tipo_plan             Basico/Estandar/Premium      [categorica]
facturacion_mensual   COP ~20.000 - 250.000        [numerica]
antiguedad_meses      1 - 96                       [numerica]
minutos_llamada       minutos/mes                  [numerica]
gb_datos              gigas/mes                    [numerica]
num_quejas            0 - 12                       [numerica]
pago_automatico       Si/No                        [categorica]
fecha_contrato        AAAA-MM-DD                   [fecha]
fuga                  Si/No  <- VARIABLE OBJETIVO  [categorica]
```

- Contiene problemas **a propósito**: nulos, duplicados, escritura inconsistente, outliers. Se aprenden a dominar en las sesiones 2-5.
- Ubicación: `../../datasets_base/telecom_clientes_raw.csv`
- Regenerable con: `python3 generador_telecom.py`
- ¿Por qué sintético y no Kaggle? Porque se puede regenerar, compartir sin licencias y conocer cada columna; el flujo es idéntico al de datos reales.

## Demo guiada de pandas (diapositivas 17-18)

Código de la primera demo:
```python
ruta = Path("../../datasets_base/telecom_clientes_raw.csv")
df = pd.read_csv(ruta)
print("Dimensiones:", df.shape)
print(df.head())
df.info()
```
Salida esperada:
```
Dimensiones: (2460, 12)
   id_cliente  edad   ciudad tipo_plan ...
0   TEL-0001  45.0   Bogotá   Premium
1   TEL-0002  61.0   ibague    basico
2   TEL-0003   NaN     cali   Estandar
...
 2   edad         2338 non-null
 5   facturacion_mensual  2312 non-null
```
Señales inmediatas: `edad` tiene nulos, `ciudad` llega en minúscula... esto alimenta directamente la sesión 3 (limpieza).

Segunda demo (resumen estadístico instantáneo):
```python
print(df.describe().round(1))
print(df["fuga"].value_counts(normalize=True).round(3))
print(pd.crosstab(df["tipo_plan"], df["fuga"], normalize="index").round(2))
```

## Datos abiertos para proyectos alternativos

| Fuente | URL | Ideal para... |
|---|---|---|
| Datos Abiertos Colombia | datos.gov.co | Proyectos con contexto nacional real |
| DANE | dane.gov.co | Pobreza, empleo, demografía |
| IDEAM | ideam.gov.co | Series de tiempo climáticas (sesión 13) |
| Kaggle Datasets | kaggle.com/datasets | Telco Churn, Titanic, retail |
| UCI ML Repository | archive.ics.uci.edu | Datasets clásicos de benchmarking |

Criterios para elegir dataset del equipo: mínimo 500 filas, variable objetivo clara (o pregunta de agrupación), datos comprensibles. Detalle completo en `datasets_base/CATALOGO_FUENTES.md`.

## Caja de herramientas del semestre

- **Python 3 + Jupyter/Colab:** lenguaje principal; Colab en navegador sin instalar nada.
- **pandas + numpy:** carga, limpieza y manipulación de tablas.
- **scikit-learn:** clasificación, clustering, PCA, métricas (estándar industrial).
- **matplotlib + seaborn:** visualización para EDA y comunicación.
- **Weka:** interfaz gráfica clásica (sesión de contraste).
- **Power BI:** comunicar hallazgos a audiencias no técnicas (despliegue).

## Ejemplo de la vida real: KDD dentro de un banco (detección de fraude)

| Etapa KDD | Acción concreta |
|---|---|
| 1 · Selección | 90 días de transacciones + perfil del cliente + geolocalización de datáfonos |
| 2 · Preprocesamiento | Corregir montos con distinta moneda, imputar coordenadas faltantes |
| 3 · Transformación | Variables nuevas: "monto vs promedio histórico", "minutos desde la última compra" |
| 4 · Minería | Modelo de anomalías puntúa cada compra: riesgo 0-100 |
| 5 · Interpretación | Reglas legibles: "compra > 800.000 COP fuera de ciudad habitual en < 30 min = riesgo alto" |
| 6 · Conocimiento → acción | Si riesgo > 85: bloqueo preventivo + notificación al celular en 2 segundos |

Mismo esqueleto que el proyecto TelecomUNO, cambiando fraude por fuga.

## Casos colombianos de minería de datos

- **Banca · Fraude en tarjetas:** cada compra evaluada en milisegundos por el modelo (monto, ubicación, hora, hábito del cliente); cada punto porcentual de detección ahorra miles de millones.
- **Telecom · Fuga de clientes (churn):** operadoras predicen quién cancelará usando quejas, consumo y antigüedad; ofrecen planes personalizados ANTES de perderlos. Ejemplo replicado por el proyecto integrador.
- **Salud · EPS y hospitales públicos:** clustering de pacientes crónicos prioriza visitas; modelos anticipan hospitalizaciones evitables.
- **Gobierno · Deserción escolar (MinEducación):** con datos abiertos de matrícula se identifican municipios y estudiantes en riesgo, dirigiendo subsidios donde más impactan.

## Ejercicio en clase (misión)

**Objetivo:** producir el "Acta de constitución analítica" que guiará el proyecto todo el semestre.
1. **(10 min)** Abrir el dataset en Colab (`pd.read_csv`) y registrar: dimensiones, tipos de datos, 3 problemas de calidad detectados.
2. **(10 min)** Calcular la tasa global de fuga y la tasa por `tipo_plan` y por `num_quejas >= 3`. ¿Qué segmento preocupa más?
3. **(10 min)** Redactar la *pregunta de negocio* y el *objetivo analítico* en lenguaje no técnico (máx. 3 líneas cada uno).
4. **(10 min)** Clasificar el proyecto según las tareas de minería (¿clasificación? ¿clustering?) y justificar en 2 líneas.
5. **(5 min)** Subir el cuaderno .ipynb + acta al espacio del curso; un portavoz socializa en 60 segundos.

**Pista técnica para el punto 2:**
```python
df["quejas_altas"] = df["num_quejas"] >= 3
tasa = df.groupby("quejas_altas")["fuga"].apply(lambda s: (s == "Si").mean())
print(tasa.round(2))
```

**Criterios de éxito · nivel esperado:**
- Cuaderno ejecuta sin errores de principio a fin.
- Reporta dimensiones y al menos 3 problemas de calidad correctos.
- Pregunta de negocio clara y medible.

**Errores frecuentes a evitar:**
- Confundir objetivo técnico ("aplicar K-means") con objetivo de negocio ("reducir fuga 10%").
- Reportar la tasa de fuga sin separar por segmentos.
- Copiar código sin comentar qué encontró cada celda.

## Evaluación formativa de la sesión

**Instrumento: Taller de ejercicios.**

| Evidencia | Criterio | Peso |
|---|---|---|
| Cuaderno Colab ejecutado | Exploración básica completa (puntos 1-2) | 50% |
| Acta del proyecto | Pregunta de negocio + objetivo analítico coherentes (punto 3) | 30% |
| Socialización | Comunicación clara en 60 segundos (punto 5) | 20% |

**Escalera de logro:**
- **Inicio:** reconoce las etapas KDD/CRISP-DM y abre el dataset con apoyo.
- **Progreso:** explora el dataset identificando problemas de calidad con guía.
- **Esperado:** documenta exploración + define problema de negocio propio del equipo.
- **Excepcional:** además propone hipótesis de fuga verificables y plan de validación.

## Trabajo independiente (~6 horas) · para sesión 2

1. **Lectura (2 h):** Han, Kamber & Pei, *Data Mining: Concepts and Techniques*, cap. 1 (biblioteca digital UNIMINUTO). Anotar 3 ideas y 2 dudas.
2. **Práctica (2 h):** completar el tutorial "Intro to Pandas" de Kaggle Learn (gratis, certifica). Reproducir la demo de hoy desde cero sin mirar el cuaderno.
3. **Proyecto (2 h):** cada equipo lista 2 datasets candidatos alternativos (uno debe venir de datos.gov.co) con enlace, número de filas y posible variable objetivo.

**Anticipo sesión 2 · Fuentes y Tipos de Datos:** estructurados vs no estructurados, carga desde CSV, bases de datos y APIs. Traer instalado (o listo) Google Colab.

## Errores comunes del minero principiante (tips del docente)

- **Error 1 · Empezar por el modelo:** "primero entreno la red y ya." Sin entender el negocio ni limpiar datos, el modelo aprende basura. Regla: 80% preparación, 20% modelado.
- **Error 2 · Confundir reporte con patrón:** una tabla dinámica dice QUÉ pasó; la minería busca POR QUÉ y QUÉ SIGUE.
- **Error 3 · Creer que más datos = mejores resultados:** 1 millón de filas mal muestreadas pierden contra 5 mil representativas.
- **Error 4 · No versionar nada:** nombrar archivos con fecha y versión (`telecom_v1_2026-08.ipynb`).

## Cierre · qué nos llevamos

- Minería de datos = descubrir patrones útiles, ocultos y accionables; no es reporting.
- KDD describe el proceso completo; CRISP-DM es la versión industrial: negocio → datos → preparación → modelado → evaluación → despliegue.
- Tareas principales: clasificación, regresión, clustering, asociación, anomalías, texto y series.
- Ya cargamos y diagnosticamos el dataset del proyecto: TelecomUNO espera.

**Próxima sesión · Fuentes y Tipos de Datos:** estructurados vs no estructurados, CSV, bases de datos y APIs. Prueba escrita corta de entrada.