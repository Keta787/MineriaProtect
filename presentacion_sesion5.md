# Sesión 5 · Análisis Exploratorio de Datos · Minería de Datos

## Diapositiva 1

**Pie de diapositiva:** Minería de Datos · UNIMINUTO Ibagué · 2026-2

Ingeniería de Sistemas · Espacio académico teórico-práctico

# Minería de Datos

**Sesión 5 · Análisis Exploratorio de Datos (EDA)**

Estadística descriptiva y visualización: escuchar a los datos antes de modelarlos


Navegue con las flechas del teclado · `F` pantalla completa · `Ctrl`+`P` exportar a PDF

## Diapositiva 2

**Pie de diapositiva:** Minería de Datos · Sesión 5 · EDA

Para empezar

## Cuatro datasets idénticos... hasta que los grafica

> El cuarteto de Anscombe (1973): cuatro conjuntos con la MISMA media de x (9,0), la MISMA media de y (7,5), la MISMA correlación (0,816) y la MISMA recta de regresión. Sus gráficos son radicalmente distintos.

### x̄ = 9,0 · ȳ = 7,5

y varianzas idénticas en los cuatro conjuntos. Cualquier tabla resumen juraría que son el mismo dataset.

### r = 0,816

la correlación exacta se repite en los cuatro... aunque uno es lineal, otro curvo, otro lo define un único outlier.

### 1 gráfico basta

para distinguirlos en dos segundos. Los resúmenes numéricos describen; los gráficos REVELAN.

Pregunta disparadora: ¿qué decisión errónea tomaría su jefe si usted le entrega solo el describe() y él no ve el gráfico?

## Diapositiva 3

**Pie de diapositiva:** Minería de Datos · Sesión 5 · EDA

Objetivos de aprendizaje

## Al finalizar esta sesión podrá...

1. **Calcular e interpretar** medidas de tendencia central, dispersión y forma, eligiendo la apropiada según la distribución.
2. **Construir** histogramas, boxplots, barras, dispersión, mapas de calor y matrices de dispersión con matplotlib, leyendo patrones y outliers.
3. **Interpretar** el coeficiente de Pearson y **distinguir** correlación de causalidad con ejemplos.
4. **Redactar** hallazgos accionables en la estructura estándar del informe EDA que exige el curso.

### Resultado de aprendizaje relacionado (Unidad 1)

"Aplica técnicas de preprocesamiento y exploración de datos para preparar conjuntos de datos con fines analíticos." El EDA es la exploración formal que cierra la preparación.

## Diapositiva 4

**Pie de diapositiva:** Minería de Datos · Sesión 5 · EDA

Agenda · 120 minutos

## Ruta de la sesión

Bienvenida, repaso de transformaciones y gancho: cuarteto de Anscombe

Teoría I: tendencia central, dispersión, forma y correlación

Teoría II: galería de gráficos y buenas prácticas de visualización

Pausa activa + caso real: cuando el EDA detectó fraude y sesgo

Demo guiada: eda_inmuebles.py con las 6 figuras

Ejercicio en clase: informe EDA de TelecomUNO (equipos)

Socialización de hallazgos

Instrumento informe de laboratorio, trabajo independiente y cierre

## Diapositiva 5

**Pie de diapositiva:** Minería de Datos · Sesión 5 · EDA

Conexión con la sesión 4

## Matrices listas... ¿pero conocemos los datos?

- Sesiones 2–4: cargamos, limpiamos y transformamos TelecomUNO. Sabemos que ESTÁ bien; aún no sabemos QUÉ dice.
- El EDA es la fase **Entendimiento de los datos** de CRISP-DM en estado puro y cierra el material del Avance 1.
- Hoy trabajamos con DOS datasets: telecom_clientes_limpio.csv y un nuevo vecino ibaguereño.

| Dataset | Tamaño | Variable estrella | Rol hoy |
| --- | --- | --- | --- |
| telecom_clientes_limpio.csv | 2400 × 12 | fuga (Si/No) | Ejercicio en clase: informe EDA |
| inmuebles_arriendo_ibague.csv | 800 × 8 | arriendo_cop | Demo guiada: galería completa de figuras |

El dataset de inmuebles se generó con semilla 42 (`python3 generador_inmuebles.py`): reproducible al 100%, con nulos y outliers inyectados a propósito para practicar.

## Diapositiva 6

**Pie de diapositiva:** Minería de Datos · Sesión 5 · EDA

Conceptos

## ¿Qué es el análisis exploratorio?

> "El mayor valor de una imagen es cuando nos obliga a notar lo que nunca esperábamos ver." — John Tukey, padre del EDA (1977)

### Univariado

Una variable a la vez: distribución, rangos, valores típicos.
Ej.: ¿cómo se distribuye arriendo_cop?

### Bivariado

Pares de variables: relaciones y diferencias.
Ej.: ¿el área explica el arriendo? ¿el plan afecta la fuga?

### Multivariado

El conjunto completo: correlaciones cruzadas, estructuras ocultas.
Ej.: heatmap general, matriz de dispersión, PCA.

**Analogía:** antes de comprar un carro usado, usted hace su EDA: mira el exterior (univariado), enciende y escucha (bivariado) y lo lleva al mecánico que revisa todo en conjunto (multivariado).

## Diapositiva 7

**Pie de diapositiva:** Minería de Datos · Sesión 5 · EDA

Estadística descriptiva

## Tres familias de medidas, tres preguntas

| Familia | Medidas | Pregunta que responde |
| --- | --- | --- |
| **Tendencia central** | Media, mediana, moda | ¿Dónde está el centro típico? |
| **Dispersión** | Rango, IQR, desviación estándar | ¿Qué tan extendidos están los datos? |
| **Forma** | Asimetría (skew), curtosis | ¿Es simétrica? ¿Tiene colas pesadas? |

### Nuestros arriendos: media ≠ mediana

Media = 249 mil COP, mediana = 238 mil, asimetría = +2,56 (cola derecha). Las mansiones outliers jalan la media hacia arriba. Regla práctica: con cola larga, reporte mediana.

### Curtosis en una línea

La curtosis mide qué tan pesadas son las colas. Arriendo_cop: curtosis 18,5 (¡altísima!): eventos raros pero muy alejados, como los precios imposibles que inyectamos.

## Diapositiva 8

**Pie de diapositiva:** Minería de Datos · Sesión 5 · EDA

Bivariado

## Correlación de Pearson: fuerza y dirección

| |r| aproximado | Lectura práctica |
| --- | --- |
| 0 – 0,1 | Sin relación lineal |
| 0,1 – 0,3 | Débil |
| 0,3 – 0,5 | Moderada |
| 0,5 – 0,7 | Fuerte |
| > 0,7 | Muy fuerte |

El signo indica dirección (+ suben juntos, − uno sube cuando el otro baja). Guía práctica, no dogma: depende del dominio.

### Correlación NO es causalidad

- Ventas de helado ↑ con ahogamientos ↑... porque AMBOS suben en verano (variable confusora)
- Más bomberos en el incendio ↔ más daños: la gravedad causa ambos
- En nuestros datos: área↔arriendo r=0,62 (causal plausible); antigüedad↔arriendo r=−0,20 (débil, requiere contexto)

```
r_area = df["area_m2"].corr(df["arriendo_cop"])
print(r_area)   # -> 0.621 : fuerte y positiva
```

## Diapositiva 9

**Pie de diapositiva:** Minería de Datos · Sesión 5 · Nuevo dataset

Nuevo laboratorio

## Anatomía: inmuebles_arriendo_ibague.csv

| Columna | Contenido |
| --- | --- |
| id_inmueble | INM-0001 ... INM-0800 |
| barrio | 10 barrios reales de Ibagué |
| habitaciones / banos | 1–4 / 1–3 |
| area_m2 | 30 – 148 m² |
| antiguedad_anos | 0 – 50 |
| amoblado | Si / No |
| arriendo_cop | precio mensual (objetivo) |

- **Barrios incluidos:** Multicentro, Cádiz, Picaleña, Ciudad Jardín, La Pola, Santa Helena, Alfonso López, Venecia, Jordán y Calambío, con tarifas por m² distintas.
- **Problemas inyectados:** 10 nulos en arriendo, 8 en baños, 6 en antigüedad; 6 mansiones ×3,2 y 4 precios imposibles de $90.000.
- **Semilla 42:** cada estudiante regenera EXACTAMENTE el mismo archivo.
- Ruta: `sesion5/datasets/`. Generador: `generador_inmuebles.py`.

## Diapositiva 10

**Pie de diapositiva:** Minería de Datos · Sesión 5 · Galería de gráficos

Galería · 1 de 4

## Histograma: la forma de la distribución

![Histograma del arriendo](datasets/fig_hist_arriendo.png)

- Agrupa los valores en intervalos (bins) y cuenta cuántos caen en cada uno: la "silueta" de la variable.
- **Lectura aquí:** masa principal entre ~150 y ~300 mil COP, con cola derecha larga: los outliers estiran el gráfico.
- Línea roja (media 249 mil) queda a la derecha de la verde (mediana 238 mil): firma de asimetría positiva.
- **Tip:** pocos bins ocultan picos; demasiados inventan ruido. 30 es buen punto de partida.

## Diapositiva 11

**Pie de diapositiva:** Minería de Datos · Sesión 5 · Galería de gráficos

Galería · 2 de 4

## Boxplot: anatomía de cinco números + outliers

![Boxplot del arriendo](datasets/fig_box_arriendo.png)

- **Caja:** el IQR, el 50% central de los datos (Q1=189 mil a Q3=291 mil). **Línea:** mediana.
- **Bigotes:** hasta 1,5×IQR desde los cuartiles. Todo punto fuera del bigote se dibuja como círculo: outlier visual.
- **Lectura aquí:** límite superior 444 mil y 19 puntos detectados por IQR: mansiones y errores conviven en esa nube.
- Súper poder: comparar grupos lado a lado (boxplot de arriendo POR BARRIO en su tarea).

## Diapositiva 12

**Pie de diapositiva:** Minería de Datos · Sesión 5 · Galería de gráficos

Galería · 3 de 4

## Barras: contar categorías sin engaños

![Barras por barrio y amoblado](datasets/fig_barras_barrio.png)

- Equivalente al countplot de seaborn: `df["barrio"].value_counts().barh()`.
- **Lectura:** Multicentro (112) y Cádiz (104) concentran oferta; Calambío (40) es nicho. Amoblado: minoría (~29%).
- Orden SIEMPRE por frecuencia o por valor, jamás alfabético "porque sí": el orden ya es información.
- Para precio por barrio, mejor la MEDIANA: Calambío media 162 vs mediana 165 mil (los outliers distorsionan la media).

## Diapositiva 13

**Pie de diapositiva:** Minería de Datos · Sesión 5 · Galería de gráficos

Galería · 4 de 4

## Dispersión + recta de tendencia

![Área vs arriendo](datasets/fig_scatter_area.png)

- Cada punto es un inmueble: área (x) contra arriendo (y). La recta roja ajusta por mínimos cuadrados (equivalente al regplot de seaborn).
- **Lectura:** r = 0,62 fuerte positivo; pendiente ≈ 3 mil COP adicionales por cada m² construido.
- Salta a la vista el cúmulo de puntos arriba-derecha (mansiones) y la franja inferior ($90.000): el describe() los escondía entre promedios; el gráfico los exhibe.
- Eso es EDA en estado puro: hipótesis visibles ANTES de cualquier modelo.

## Diapositiva 14

**Pie de diapositiva:** Minería de Datos · Sesión 5 · Multivariado

Multivariado

## Heatmap de correlaciones y matriz de dispersión

![Mapa de calor de correlaciones](datasets/fig_heatmap_corr.png)

- **Heatmap:** toda la matriz de Pearson en un vistazo; rojo positivo, azul negativo.
- **Lecturas clave:** habitaciones↔banos 0,75 y habitaciones↔área 0,69 (redundancia potencial); área↔arriendo 0,62; antigüedad↔arriendo −0,20.
- Variables redundantes anticipan problemas de multicolinealidad en modelos lineales (lo retomaremos en regresión).
- **Matriz de dispersión** (`fig_matriz_dispersion.png`): todos los scatter cruzados + histogramas en diagonal; versión matplotlib del pairplot de seaborn (opcional instalarla para estética extra).

## Diapositiva 15

**Pie de diapositiva:** Minería de Datos · Sesión 5 · Buenas prácticas

Buenas prácticas de visualización

## Un gráfico es un argumento

### Siempre

- Ejes etiquetados CON UNIDADES ("miles de COP", "m²")
- Título que declara el hallazgo, no el tipo de gráfico ("El área explica el 38% del arriendo")
- Barras arrancan en cero; anotaciones directas sobre el dato clave
- Paleta consistente y accesible (verificable en escala de grises)

### Nunca

- Pastel 3D: distorsiona áreas y es ilegible (además, pastel solo con < 5 categorías)
- Truncar el eje Y de barras para exagerar diferencias minúsculas
- Doble eje Y disfrazando correlaciones forzadas
- Colormap arcoíris para variables continuas: inventa fronteras falsas

**Regla final:** si su gráfico necesita defensa verbal para no engañar, está mal diseñado. La honestidad visual es parte de la ética del ingeniero de datos.

## Diapositiva 16

**Pie de diapositiva:** Minería de Datos · Sesión 5 · Demo guiada

Demo guiada · 00:53 – 01:13

## Las tablas que imprime eda_inmuebles.py

```
# Tendencia, dispersion y forma
print(df["arriendo_cop"].mean())     # 249106
print(df["arriendo_cop"].median())   # 238000
print(df["arriendo_cop"].skew().round(2))    # 2.56
print(df["arriendo_cop"].kurtosis()
                        .round(2))   # 18.54

# Regla IQR sobre el arriendo
q1, q3 = df["arriendo_cop"].quantile([.25,.75])
iqr = q3 - q1
outliers = df[df["arriendo_cop"] > q3 + 1.5*iqr]
print(len(outliers))                 # 19

# Mediana ordena barrios mejor que media
df.groupby("barrio")["arriendo_cop"].median() \
  .sort_values(ascending=False)
```

Salida real (mediana por barrio)

- Gradiente claro norte-caribe→sur: la ubicación vale hasta 117 mil COP mensuales entre extremos.
- El script también cruza TelecomUNO: fuga 23% en plan Basico vs 13% Premium.

## Diapositiva 17

**Pie de diapositiva:** Minería de Datos · Sesión 5 · Ejemplo de la vida real

Ejemplo de la vida real

## Cuando mirar antes de modelar evitó desastres

### Detección de fraude sin modelo

En procesadoras de pago, el boxplot de montos por comercio reveló tiendas "de barrio" con tickets decenas de veces su percentil histórico: eran mulas de lavado. Ningún modelo estaba en producción: el simple boxplot abrió las investigaciones.

### Sesgo detectado a tiempo

En 2018 un gigante tecnológico probó filtrar hojas de vida con IA. El EDA de tasas de aprobación históricas mostró penalización sistemática de CV femeninos (los datos heredaban sesgos del pasado). Cancelaron el proyecto ANTES de producción: mirar primero salvó reputación y millones.

### Calidad de datos clínica

EPS que cruzan edad contra fecha de atención descubren historias clínicas duplicadas y fechas imposibles (pacientes "atendidos" antes de nacer): scatter simples exponen registros que ningún formulario validó.

### TelecomUNO · nuestro caso

El cruce plan×fuga del script muestra Basico fugando 23% vs Premium 13%: si mañana hay presupuesto para UNA sola campaña de retención, el EDA ya dijo dónde invertirla.

## Diapositiva 18

**Pie de diapositiva:** Minería de Datos · Sesión 5 · Ejercicio en clase

Ejercicio en clase · 01:13 – 01:48 · equipos de 3

## Misión: el primer informe EDA de TelecomUNO

**Objetivo:** producir el borrador del informe exploratorio del dataset del proyecto (telecom_clientes_limpio.csv) siguiendo la estructura oficial del instrumento.

1. **(5 min)** Univariado: `describe()` de las numéricas + skew de facturacion_mensual y gb_datos. Identifiquen las 2 asimetrías más marcadas.
2. **(8 min)** Histograma y boxplot de facturacion_mensual; cuantifiquen los outliers con IQR (no solo "se ven raros").
3. **(7 min)** Barras de ciudad y tipo_plan + tabla de tasa de fuga por segmento con `pd.crosstab(normalize="index")`.
4. **(8 min)** Dispersión antiguedad_meses vs facturacion_mensual + heatmap de correlaciones numéricas. ¿Alguna relación sorprendente?
5. **(7 min)** Redacten 3 hallazgos en formato: hallazgo + evidencia (cifra/gráfico) + acción sugerida para el negocio.

## Diapositiva 19

**Pie de diapositiva:** Minería de Datos · Sesión 5 · Ejercicio en clase

Ejercicio en clase · criterios de éxito

## ¿Qué distingue un informe excelente?

### Nivel esperado

- Todo gráfico con título-hallazgo, ejes y unidades completos
- Outliers CUANTIFICADOS con IQR, no solo señalados visualmente
- Mediana usada para reportar variables asimétricas
- Los 3 hallazgos conectan evidencia estadística con acción de negocio

### Errores frecuentes a evitar

- Graficar sin revisar tipos (fechas/categorías como texto)
- Concluir causalidad desde una correlación ("las quejas CAUSAN fuga")
- Describir el gráfico en vez de interpretarlo ("aquí hay barras azules...")
- Pastel con 10 categorías o efecto 3D decorativo

### Pista técnica para el punto 3

```
tasa = telecom.groupby("tipo_plan")["fuga"] \
              .apply(lambda s: (s == "Si").mean())
print(tasa.sort_values(ascending=False).round(2))
```

## Diapositiva 20

**Pie de diapositiva:** Minería de Datos · Sesión 5 · Evaluación

Evaluación · instrumento del PEA

## Informe de laboratorio: estructura exigida

| Sección | Contenido mínimo | Peso |
| --- | --- | --- |
| 1 · Portada y contexto | Integrantes, pregunta de negocio del proyecto, objetivos del análisis | 10% |
| 2 · Calidad de datos | Nulos, duplicados, outliers encontrados y decisiones tomadas (herencia sesiones 3-4) | 15% |
| 3 · Análisis univariado | Tablas descriptivas + mínimo 4 gráficos interpretados (no solo pegados) | 25% |
| 4 · Análisis bivariado/multivariado | Correlaciones, cruces con la variable objetivo, heatmap | 25% |
| 5 · Hallazgos y recomendaciones | Mínimo 3 hallazgos formato evidencia-acción, redactados para no técnicos | 20% |
| 6 · Anexos | Notebook reproducible con el código completo ejecutado | 5% |

### Escalera de logro

- **Inicio:** presenta tablas y gráficos básicos con apoyo de la plantilla.
- **Progreso:** interpreta la mayoría de gráficos y cuantifica algunos outliers.
- **Esperado:** informe completo, interpretaciones correctas y hallazgos accionables.
- **Excepcional:** además, propone nuevas variables o segmentos y valida sus hipótesis con datos.

## Diapositiva 21

**Pie de diapositiva:** Minería de Datos · Sesión 5 · Trabajo independiente

Trabajo independiente · ~6 horas esta semana

## Tarea para la sesión 6

1. **Lectura (2 h):** plantilla de análisis exploratorio del curso + Han, Kamber & Pei, sección 2.2 (resúmenes descriptivos). Revise la galería de matplotlib y guarde 2 ejemplos útiles.
2. **Práctica (2 h):** extienda `eda_inmuebles.py`: agregue boxplot de arriendo por barrio y un gráfico propio suyo (con título-hallazgo). Guarde ambas figuras.
3. **Proyecto (2 h):** complete el borrador COMPLETO del informe EDA de su dataset con la estructura de 6 secciones exigida.

### Anticipo sesión 6

Consolidamos el Avance 1: limpieza + transformación + EDA integrados en el documento entregable del primer corte (30% de la nota). Traiga su borrador avanzado para revisión entre pares.

## Diapositiva 22

**Pie de diapositiva:** Minería de Datos · Sesión 5 · Tips

Tips del docente

## Errores comunes del explorador principiante

### Error 1 · Confiarse del describe()

El cuarteto de Anscombe existe por una razón: cuatro datasets, un mismo describe. Numérico y gráfico son complementarios; ninguno sustituye al otro.

### Error 2 · Media en colas largas

Reportar "el arriendo promedio es 249 mil" cuando la mediana es 238 mil infla expectativas. Con skew alto, la mediana es la voz honesta del centro.

### Error 3 · Saltar de r a causalidad

r=0,62 entre área y arriendo es sugerente, no probatorio. La causalidad se argumenta con diseño (experimentos, control de confusoras), no con un coeficiente.

### Error 4 · Gráficos mudos

Un gráfico sin ejes ni unidades obliga al lector a adivinar. Si su audiencia tiene que preguntar "¿qué estoy viendo?", el gráfico falló.

## Diapositiva 23

**Pie de diapositiva:** Minería de Datos · Sesión 5 · Cierre

Cierre · 01:54 – 02:00

## Lo que nos llevamos hoy

- EDA = escuchar los datos antes de modelar: univariado, bivariado y multivariado.
- Tendencia central, dispersión y forma responden preguntas distintas; con asimetría, la mediana manda.
- Pearson mide asociación lineal; correlación jamás prueba causalidad.
- La galería mínima: histograma, boxplot, barras, dispersión, heatmap y matriz de dispersión, todos generados con matplotlib puro.
- Con este cierre, el material técnico del Avance 1 está completo.

### Próxima sesión

**Sesión 6 · Consolidación del Avance 1:** integramos limpieza, transformación y EDA en el entregable documental del primer corte (30%).

### Contacto

Esteban Ernesto Morales Castro
Aula virtual UNIMINUTO · foro de la semana para dudas
Atención: horario publicado en el aula virtual

