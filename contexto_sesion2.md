# Contexto · Minería de Datos · Sesión 2: Fuentes y Tipos de Datos

## Datos generales

- **Curso:** Minería de Datos · UNIMINUTO Ibagué · Ingeniería de Sistemas · 2026-2 · Unidad 1
- **Docente:** Esteban Ernesto Morales Castro
- **Duración:** 2 horas (120 minutos)
- **Resultado de aprendizaje (Unidad 1):** "Aplica técnicas de preprocesamiento y exploración de datos para preparar conjuntos de datos con fines analíticos." Antes de preprocesar hay que saber *traer* los datos sin corromperlos: ese es el oficio de hoy.
- **Tema:** Del CSV a la API: dónde viven los datos y cómo cargarlos bien con pandas.
- **Archivos de la sesión:**
  - `presentacion.html` (24 slides, material del docente)
  - `codigo/carga_fuentes.py` (genera y carga datos desde CSV, JSON y SQLite)
  - `datasets/ventas_tienda.csv` (12 ventas, formato CSV)
  - `datasets/ventas_tienda.json` (mismos datos, formato JSON)
  - `datasets/ventas_tienda.db` (mismos datos, base SQLite)
  - `datasets/lectura.ipynb` (cuaderno de la sesión con las comparaciones ejecutadas)

## Objetivos de aprendizaje

1. **Explicar** el espectro estructurado – semiestructurado – no estructurado, ubicando ejemplos reales colombianos en cada extremo.
2. **Comparar** los formatos CSV, JSON, XML, Excel y SQL, y justificar la elección del adecuado según el contexto.
3. **Describir** qué es un API REST y leer la estructura de su respuesta JSON.
4. **Cargar** un mismo conjunto de datos desde tres formatos distintos con pandas, interpretando los tipos que infiere.

## Agenda · 120 minutos

| Hora | Bloque |
|---|---|
| 00:00 – 00:10 | Bienvenida, repaso relámpago de KDD/CRISP-DM y objetivos |
| 00:10 – 00:30 | Teoría I: espectro de datos, formatos y tipos que infiere pandas |
| 00:30 – 00:40 | Teoría II: trampas del CSV colombiano y API REST con JSON |
| 00:40 – 00:45 | Pausa activa: ¿dónde está su próximo dataset? |
| 00:45 – 01:05 | Demos guiadas: carga desde CSV, JSON y SQLite |
| 01:05 – 01:40 | Ejercicio en clase: el mismo dato en tres formatos (equipos) |
| 01:40 – 01:50 | Quiz tipo prueba escrita corta (simulacro del instrumento) |
| 01:50 – 02:00 | Socialización, trabajo independiente y cierre |

## Conexión con la sesión 1

- En KDD, la etapa 1 es **Selección**: decidir qué fuentes alimentarán el proceso. Hoy se ejecuta de verdad.
- En CRISP-DM se avanza dentro de la fase **Entendimiento de los datos**: ya se hizo un `head()` al dataset crudo; ahora se aprende a traerlo desde cualquier fuente.
- El dataset TelecomUNO llegó como CSV. ¿Y si la "verdad" de la empresa vive en un JSON de la app o en la base de datos? Hay que saber leer las tres.

| Sesión 1 | Hoy | Próxima |
|---|---|---|
| Mapa KDD y CRISP-DM; primer contacto con telecom_clientes_raw.csv | Fuentes, formatos, APIs y cuatro cargas reales con pandas | Limpieza: reparar los nulos y duplicados que hoy detectamos |

## Conceptos teóricos clave

### El espectro de los datos

| Tipo | Característica | Ejemplos |
|---|---|---|
| **Estructurados** | Filas y columnas fijas, esquema rígido | Tabla SQL de ventas, CSV de clientes, nómina |
| **Semiestructurados** | Sin esquema rígido, organizados con etiquetas internas | JSON de una API, XML de la facturación DIAN, logs |
| **No estructurados** | Sin organización previa: texto, imágenes, audio, video | Reseñas de Rappi, radiografías, llamadas de call center |

**Analogía:** biblioteca perfecta con fichas catalogadas (estructurado), estanterías con índice por tema (semiestructurado) y bodega de libros sueltos (no estructurado).

**Dato clave:** cerca del 80% del dato nuevo que generan las empresas es no estructurado; la minería clásica empieza en el estructurado, y el curso tocará texto en la sesión 14.

### ¿Dónde viven los datos de una empresa colombiana?

1. **Bases transaccionales:** Oracle, SQL Server, PostgreSQL. Cada venta o consignación pasa por aquí en tiempo real.
2. **Archivos planos:** CSV y Excel que exporta contabilidad, un proveedor o el ministerio. Ubicuos, frágiles y llenos de sorpresas.
3. **APIs de terceros:** pasarelas de pago Wompi/PayU, clima del IDEAM, portal datos.gov.co. Devuelven JSON bajo demanda.
4. **Ríos nuevos:** logs de la app, sensores IoT, redes sociales, WhatsApp Business. Alto volumen, poco orden, gran valor futuro.

**Idea central:** casi nunca falta información; lo que falta es una sola vista integrada y confiable.

### Formatos frente a frente

| Formato | Qué es | Fortaleza | Cuándo evitarlo |
|---|---|---|---|
| **CSV** | Texto plano separado por comas | Simple, universal, liviano | Datos jerárquicos o anidados |
| **JSON** | Pares clave-valor jerárquicos | Estándar de APIs web; legible | Miles de millones de filas (pesa mucho) |
| **XML** | Etiquetas anidadas estilo HTML | Maduro; usado en DIAN y sistemas SOAP | Verboso y pesado frente a JSON |
| **Excel** | Hojas de cálculo con formato | La gerencia lo entiende y lo edita | Celdas combinadas y fórmulas rompen la carga automática |
| **SQL** | Base de datos en servidor | Volumen, integridad, acceso concurrente | Requiere conexión, permisos y credenciales |

**Regla práctica del curso:** prototipar en CSV, intercambiar con servicios en JSON, operar en serio sobre una base SQL.

### Tipos que pandas infiere al cargar

| Tipo pandas | Ejemplo en TelecomUNO | Detalle importante |
|---|---|---|
| `int64` | antiguedad_meses, num_quejas | Enteros; si hay UN solo nulo se degrada a float |
| `float64` | edad, facturacion_mensual | Números con decimales y portadores involuntarios de nulos (`NaN`) |
| `object` | ciudad, tipo_plan, fuga | Texto o mezcla. Si una columna numérica cae aquí, hay basura adentro |
| `datetime64` | fecha_contrato | Solo si se pide: `parse_dates=["fecha_contrato"]` |
| `bool / category` | pago_automatico | Optimizaciones opcionales que ahorran memoria |

**Ojo con el diagnóstico silencioso:** que pandas cargue sin errores NO significa que cargue bien. Los dtypes inferidos son el primer examen de salud: revíselos siempre después de cargar.

### Las trampas clásicas del CSV colombiano

- **Error 1 · Separador punto y coma** (DANE, ministerios): `pd.read_csv(ruta, sep=";")`.
- **Error 2 · Encoding roto** ("BogotÃ¡" = Windows-1252): `encoding="latin-1"` o `"cp1252"`.
- **Error 3 · Coma decimal** ("125,50" vuelve la columna object): `decimal=","`.
- **Error 4 · Encabezados desplazados** (títulos institucionales arriba): `skiprows=n` y `header=0`.

```python
# Carga defensiva para datos públicos colombianos
df = pd.read_csv(ruta, sep=";", encoding="latin-1",
                 decimal=",", skiprows=3)
print(df.dtypes)   # ¿algún número quedó como texto?
```

### API REST: el mesero de los datos

**Analogía del restaurante:** usted (aplicación) pide al mesero (API) un plato del menú (endpoint documentado) con una nota escrita (petición HTTP). La cocina (servidor) prepara y devuelve el plato servido (respuesta JSON). Nunca entra a la cocina.

Anatomía de una petición:
- **Método:** GET consultar · POST crear · PUT actualizar · DELETE borrar.
- **Endpoint:** `https://api.datos.gov.co/v1/datasets?tema=salud`.
- **Llave (API key):** identifica quién pregunta y limita abusos.

Códigos de estado:
- **200:** éxito, viene la respuesta.
- **404:** el endpoint o el recurso no existe.
- **401/403:** falta o sobra permiso.
- **429:** hizo demasiadas peticiones: espere.

**Ventaja frente a "pedir el CSV por WhatsApp":** datos frescos, acceso controlado, trazable y sin copias obsoletas circulando.

### Lectura de una respuesta JSON de API

```json
{
  "meta": { "total_registros": 2, "fuente": "SIVIGILA (ilustrativo)" },
  "records": [
    { "municipio": "Ibagué",  "evento": "Dengue", "casos": 145, "semana": 33 },
    { "municipio": "Espinal", "evento": "Dengue", "casos": 38,  "semana": 33 }
  ]
}
```
- **Llaves `{ }`:** objetos con pares clave-valor.
- **Corchetes `[ ]`:** listas ordenadas (aquí, los registros).
- Todo texto entre comillas dobles; números y booleanos sin comillas.
- Para tabularlo: `pd.DataFrame(datos["records"])` o `pd.json_normalize(...)` si está anidado.
- Este patrón (meta + records) es idéntico en Socrata (datos.gov.co), Twitter/X API, APIs de bancos...

> Si sabe leer UN JSON bien estructurado, sabe leer prácticamente cualquier API moderna.

## Análisis del código (codigo/carga_fuentes.py)

Genera el mismo conjunto de ventas en tres formatos (si no existen) y los carga:

```python
CARPETA_DATOS = Path(__file__).resolve().parents[1] / "datasets"   # sesion2/datasets
RUTA_CSV  = CARPETA_DATOS / "ventas_tienda.csv"
RUTA_JSON = CARPETA_DATOS / "ventas_tienda.json"
RUTA_DB   = CARPETA_DATOS / "ventas_tienda.db"
RUTA_TELECOM = RUTA_BASE / "telecom_clientes_raw.csv"

VENTAS = [  # 12 ventas deterministas de una tienda ibaguereña
    {"id_venta": 1, "fecha": "2026-08-01", "producto": "Arroz Gallo 500 g",
     "categoria": "Abarrotes", "precio_cop": 3200, "unidades": 4, "sede": "Ibagué"},
    # ... ventas 2 a 12 ...
]

def crear_datasets_propios():
    df = pd.DataFrame(VENTAS)
    df.to_csv(RUTA_CSV, index=False)                     # formato CSV
    json.dump(VENTAS, f, ensure_ascii=False, indent=2)   # formato JSON (conserva tildes)
    df.to_sql("ventas", conexion, if_exists="replace")   # formato SQLite

def demo_csv_telecom():
    df = pd.read_csv(RUTA_TELECOM)                       # (2460, 12)
    # nulos: edad 123, facturacion 148, pago 170 · duplicados: 60

def demo_json():
    df = pd.read_json(RUTA_JSON)                         # (12, 7)

def demo_sqlite():
    consulta = "SELECT fecha, producto, precio_cop, unidades FROM ventas WHERE sede = ?"
    df = pd.read_sql(consulta, conexion, params=("Ibagué",))   # consulta parametrizada
    # Agregación hecha en SQL:
    #   SELECT categoria, SUM(precio_cop*unidades) AS ingresos_cop
    #   FROM ventas GROUP BY categoria ORDER BY ingresos_cop DESC

def comparar_formatos():
    df_csv, df_json, df_db = ...   # los tres -> mismos dtypes
```

## Demos guiadas (diapositivas 13-16)

### Demo 1 · CSV del proyecto
```python
df = pd.read_csv(RUTA_TELECOM)
print("Dimensiones:", df.shape)
print("Duplicados:", df.duplicated().sum())
```
Salida real:
```
Dimensiones: (2460, 12)
edad                   123
facturacion_mensual    148
pago_automatico        170
Duplicados: 60
```
Una sola línea trajo 2.460 filas: `pd.read_csv` es la puerta de entrada del 90% de los proyectos.

### Demo 2 · JSON propio de ventas
```python
with open(RUTA_JSON, "w", encoding="utf-8") as f:
    json.dump(VENTAS, f, ensure_ascii=False, indent=2)
df = pd.read_json(RUTA_JSON)
```
Salida:
```
Dimensiones: (12, 7)
 id_venta      fecha          producto  precio_cop  unidades
        1 2026-08-01 Arroz Gallo 500 g        3200         4
        2 2026-08-01 Aceite girasol 1 L        9800         2
        3 2026-08-02 Café Tolima 500 g       18500         3
```
Cada elemento de la lista JSON se volvió una **fila**; cada clave, una **columna**. `ensure_ascii=False` preserva las tildes de "Café Tolima".

### Demo 3 · SQLite
```python
conexion = sqlite3.connect(RUTA_DB)
consulta = """SELECT fecha, producto, precio_cop, unidades
              FROM ventas WHERE sede = ?"""
df = pd.read_sql(consulta, conexion, params=("Ibagué",))
```
Salida:
```
Ventas de la sede Ibagué: (7, 4)
  categoria  ingresos_cop
      Cafés        139500
  Abarrotes        103900
    Bebidas         67400
Endulzantes         48200
```
- `params=(...,)` evita inyección SQL: nunca concatenar strings del usuario.
- **Regla de oro: filtrar y agregar en SQL**, refinar en pandas. Traer solo lo necesario.
- SQLite vive en un archivo; PostgreSQL/Oracle cambian la conexión, no la lógica.

### Demo 4 · El mismo dato en tres formatos
```python
df_csv = pd.read_csv(RUTA_CSV)
df_json = pd.DataFrame(json.load(f))       # fecha llega como object
df_db = pd.read_sql("SELECT * FROM ventas", conexion)
```
Resultado: **los tres formatos producen los mismos dtypes**. `fecha` llega como *object* en los tres: las fechas requieren conversión explícita con `pd.to_datetime`. El formato transporta, pero **no corrige** la semántica.

## Esquema del dataset de ventas (ventas_tienda.csv / .json / .db)

12 filas × 7 columnas, tres formatos equivalentes:

| id_venta | fecha | producto | categoria | precio_cop | unidades | sede |
|---|---|---|---|---|---|---|
| 1 | 2026-08-01 | Arroz Gallo 500 g | Abarrotes | 3200 | 4 | Ibagué |
| 2 | 2026-08-01 | Aceite girasol 1 L | Abarrotes | 9800 | 2 | Ibagué |
| 3 | 2026-08-02 | Café Tolima 500 g | Cafés | 18500 | 3 | Espinal |
| ... | ... | ... | ... | ... | ... | ... |
| 12 | 2026-08-11 | Gaseosa 1.5 L | Bebidas | 6500 | 6 | Espinal |

Categorías: Abarrotes, Cafés, Endulzantes, Bebidas · Sedes: Ibagué (7), Espinal (3), Girardot (2).

Ingresos totales por categoría (SQL/groupby): Cafés 139.500 > Abarrotes 103.900 > Bebidas 67.400 > Endulzantes 48.200.

## Notebook de la sesión (datasets/lectura.ipynb)

Celdas principales y conclusiones:
1. **CSV → JSON → read_json:** convierte un CSV a lista de diccionarios y lo relee con pandas. Dimensiones (12, 7).
2. **JSON → SQLite + consulta parametrizada:** crea `ventas_tienda.db`, consulta sede Ibagué (7 filas) y agrega ingresos por categoría en SQL.
3. **Comparación de dtypes CSV/JSON/SQLite:** convergen todos a `datetime64[us]` en `fecha` tras `pd.to_datetime()`. Conclusión: los tres formatos preservan la estructura temporal, permitiendo unificar análisis de series de tiempo.
4. **Ingresos en pandas vs SQL:** `df.groupby("categoria")["ingresos"].sum()` coincide con el `GROUP BY` en SQL.
5. **Recomendación para 50 sedes:** usar **SQLite (o BD relacional escalada)** como fuente de producción: centraliza información de múltiples sucursales, evita desorden/duplicación/corrupción de archivos planos y optimiza consultas con índices.

## Datos abiertos colombianos (proveedor gratuito)

- **Datos Abiertos Colombia · datos.gov.co:** miles de datasets oficiales descargables en CSV o vía API JSON (protocolo Socrata): delitos, SECOP II, matrícula escolar, vacunación.
- **DANE:** microdatos de pobreza, empleo y censos en CSV con separador `;` y encoding especial: practicar aquí las cargas defensivas.
- **IDEAM:** series históricas de lluvia y temperatura por estación (materia prima de la sesión 13).
- **MinEducación:** matrícula y deserción por municipio.

Guía completa en `datasets_base/CATALOGO_FUENTES.md`. Criterios: mínimo 500 filas, variable objetivo clara, datos comprensibles para el equipo.

## Quiz de la sesión (simulacro de prueba escrita corta)

1. **Espectro de datos:** una tabla SQL de nómina (estructurado, esquema fijo), la respuesta JSON de Wompi (semiestructurado, etiquetas flexibles), las grabaciones de un call center (no estructurado).
2. **`edad` con 123 nulos → dtype float64:** la presencia de NaN obliga a pandas a usar flotantes aunque todos los valores válidos sean enteros.
3. **"Datos actualizados cada hora" → API REST:** datos frescos sin copias desactualizadas + control de acceso y trazabilidad.
4. **"BogotÃ¡" y una columna gigante:** `encoding="latin-1"` y `sep=";"`.
5. **`pd.read_sql`:** ejecuta una consulta SQL y devuelve un DataFrame; necesita una conexión activa y, idealmente, parámetros seguros.

## Ejercicio en clase (misión)

**Objetivo:** cargar las ventas de "La Central" desde CSV, JSON y SQLite, comparar los tipos que infiere pandas y recomendar la fuente adecuada para producción.
1. **(5 min)** Ubicar los tres archivos en `sesion2/datasets/` y abrirlos "con los ojos" (editor de texto para CSV/JSON, visor para la BD).
2. **(10 min)** Cargar con `read_csv`, `read_json` y `read_sql`; imprimir `shape` y `dtypes` de cada uno.
3. **(8 min)** Tabla comparativa de tipos por columna. ¿Hubo divergencias? ¿Por qué `fecha` quedó igual en los tres formatos y qué implica?
4. **(7 min)** Ingresos por categoría dos veces: con SQL (GROUP BY) y con pandas (`groupby`). Verificar que coincidan.
5. **(5 min)** Redactar 3 líneas: ¿cuál fuente elegirían si la tienda crece a 50 sedes?, ¿por qué?

**Pista técnica para el punto 3:**
```python
df_csv["fecha"] = pd.to_datetime(df_csv["fecha"])
print(df_csv["fecha"].dtype, df_csv["fecha"].min(), "->", df_csv["fecha"].max())
```

**Criterios de éxito · nivel esperado:**
- Las tres cargas ejecutan sin errores y reportan shape + dtypes.
- Tabla comparativa completa con la explicación del caso "fecha".
- Fechas convertidas con `pd.to_datetime` y verificadas.
- Recomendación final con criterio técnico (volumen, concurrencia, trazabilidad).

**Errores frecuentes a evitar:**
- Usar `json.load` y quedarse en una lista sin DataFrame.
- `SELECT *` sin filtro y creer que son "todas" las ventas.
- Guardar sobre el archivo original y dañarlo (trabaje sobre copias).
- Comparar shapes y olvidar los dtypes: el tamaño no garantiza tipos.

## Evaluación de la sesión

**Instrumento del PEA: Prueba escrita corta.**

| Aspecto evaluado | Qué evidencia exige | Peso |
|---|---|---|
| Comprensión conceptual | Diferencias estructurado/semiestructurado/no estructurado y entre formatos | 40% |
| Lectura crítica de JSON / API | Interpretar estructura, claves, listas y códigos de estado | 25% |
| Aplicación práctica | Elegir parámetros correctos de carga (sep, encoding, decimal) | 25% |
| Precisión terminológica | Uso riguroso de vocabulario técnico | 10% |

Modalidad: individual, 15 minutos, sin computador, al cierre del bloque teórico. El quiz de la clase (01:40–01:50) es el simulacro con retroalimentación inmediata.

**Escalera de logro:**
- **Inicio:** reconoce formatos y ejemplos con apoyo de notas.
- **Progreso:** clasifica fuentes correctamente y corrige una carga con guía.
- **Esperado:** compara formatos con criterio y justifica la elección para un caso dado.
- **Excepcional:** propone una estrategia de ingesta multi-fuente para su propio proyecto.

## Trabajo independiente (~6 horas) · para sesión 3

1. **Lectura (2 h):** guía de tipos y formatos del curso + Han, Kamber & Pei, sección 2.1 (tipos de datos y calidad). Anotar 2 dudas para el foro.
2. **Práctica (2 h):** descargar 2 datasets de datos.gov.co y cargarlos exitosamente en Colab. Documentar qué parámetros necesitó (sep, encoding...) y qué dtypes resultaron.
3. **Proyecto (2 h):** el equipo define sus 2 fuentes definitivas (al menos una API o base de datos pública) y documenta formato, tamaño y posible variable objetivo.

**Anticipo sesión 3 · Limpieza de Datos:** nulos (MCAR/MAR/MNAR), duplicados, outliers IQR/z-score y pipeline completo sobre TelecomUNO. Instrumento: rúbrica de código.

## Errores comunes al traer datos (tips del docente)

- **Error 1 · Editar el original:** abrir el CSV maestro en Excel "solo para mirar" y guardarlo: Excel reescribe fechas y borra ceros iniciales. Originales intocables, siempre copias de trabajo.
- **Error 2 · Asumir UTF-8:** gran parte del legado institucional colombiano vive en latin-1. Si ve caracteres raros, no los "corrija a mano": corrija el encoding de lectura.
- **Error 3 · Fechas como texto:** dejar la fecha en *object* y descubrir en la sesión 13 que no puede calcular "meses desde el contrato". Convierta temprano: `pd.to_datetime`.
- **Error 4 · Publicar credenciales:** usuario y contraseña de la base pegados en el cuaderno compartido. Use variables de entorno o archivos de configuración excluidos del repositorio. Cero llaves en GitHub.

## Cierre · qué nos llevamos

- Los datos viven en un espectro: estructurados, semiestructurados y no estructurados; cada formato tiene su nicho.
- CSV, JSON, XML, Excel y SQL se comparan por simplicidad, jerarquía y operación; el CSV colombiano exige cargas defensivas.
- Un API REST es un contrato de consulta; su respuesta JSON se convierte a DataFrame con dos líneas.
- El mismo dato cargado desde tres formatos produce los mismos dtypes: el formato transporta, la semántica la cuidamos nosotros.

**Próxima sesión · Limpieza de Datos:** nulos (MCAR/MAR/MNAR), duplicados, outliers IQR/z-score y pipeline completo sobre TelecomUNO. Instrumento: rúbrica de código.