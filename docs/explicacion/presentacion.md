# Sesión 5 · Análisis Exploratorio de Datos (EDA)

*Minería de Datos · UNIMINUTO Ibagué · 2026-2*

## 1. Cuatro datasets idénticos... hasta que los grafica

## 2. Objetivos de aprendizaje

- Calcular e interpretar medidas de tendencia central, dispersión y forma, eligiendo la apropiada según la distribución.
- Construir histogramas, boxplots, barras, dispersión, mapas de calor y matrices de dispersión con matplotlib, leyendo patrones y outliers.
- Interpretar el coeficiente de Pearson y distinguir correlación de causalidad con ejemplos.
- Redactar hallazgos accionables en la estructura estándar del informe EDA que exige el curso.

## 3. Ruta de la sesión (Agenda)

## 4. Conexión con sesiones anteriores ¿pero conocemos los datos?

- Sesiones 2–4: cargamos, limpiamos y transformamos TelecomUNO. Sabemos que ESTÁ bien; aún no sabemos QUÉ dice.
- El EDA es la fase Entendimiento de los datos de CRISP-DM en estado puro y cierra el material del Avance 1.
- Hoy trabajamos con DOS datasets: telecom_clientes_limpio.csv y un nuevo vecino ibaguereño.

## 5. ¿Qué es el Análisis Exploratorio de Datos (EDA)?

## 6. Medidas descriptivas, tres preguntas

## 7. Correlación de Pearson: fuerza y dirección

- Ventas de helado ↑ con ahogamientos ↑... porque AMBOS suben en verano (variable confusora)
- Más bomberos en el incendio ↔ más daños: la gravedad causa ambos
- En nuestros datos: área↔arriendo r=0,62 (causal plausible); antigüedad↔arriendo r=−0,20 (débil, requiere contexto)

## 8. Dataset: inmuebles_arriendo_ibague.csv

- Barrios incluidos: Multicentro, Cádiz, Picaleña, Ciudad Jardín, La Pola, Santa Helena, Alfonso López, Venecia, Jordán y Calambío, con tarifas por m² distintas.
- Problemas inyectados: 10 nulos en arriendo, 8 en baños, 6 en antigüedad; 6 mansiones ×3,2 y 4 precios imposibles de $90.000.
- Semilla 42: cada estudiante regenera EXACTAMENTE el mismo archivo.
- Ruta: sesion5/datasets/ . Generador: generador_inmuebles.py .

## 9. Histograma: la forma de la distribución

- Agrupa los valores en intervalos (bins) y cuenta cuántos caen en cada uno: la "silueta" de la variable.
- Lectura aquí: masa principal entre ~150 y ~300 mil COP, con cola derecha larga: los outliers estiran el gráfico.
- Línea roja (media 249 mil) queda a la derecha de la verde (mediana 238 mil): firma de asimetría positiva.
- Tip: pocos bins ocultan picos; demasiados inventan ruido. 30 es buen punto de partida.

## 10. Boxplot: anatomía de cinco números + outliers

- Caja: el IQR, el 50% central de los datos (Q1=189 mil a Q3=291 mil). Línea: mediana.
- Bigotes: hasta 1,5×IQR desde los cuartiles. Todo punto fuera del bigote se dibuja como círculo: outlier visual.
- Lectura aquí: límite superior 444 mil y 19 puntos detectados por IQR: mansiones y errores conviven en esa nube.
- Súper poder: comparar grupos lado a lado (boxplot de arriendo POR BARRIO en su tarea).

## 11. Barras: contar categorías sin engaños

- Equivalente al countplot de seaborn: df["barrio"].value_counts().barh() .
- Lectura: Multicentro (112) y Cádiz (104) concentran oferta; Calambío (40) es nicho. Amoblado: minoría (~29%).
- Orden SIEMPRE por frecuencia o por valor, jamás alfabético "porque sí": el orden ya es información.
- Para precio por barrio, mejor la MEDIANA: Calambío media 162 vs mediana 165 mil (los outliers distorsionan la media).

## 12. Dispersión + recta de tendencia

- Cada punto es un inmueble: área (x) contra arriendo (y). La recta roja ajusta por mínimos cuadrados (equivalente al regplot de seaborn).
- Lectura: r = 0,62 fuerte positivo; pendiente ≈ 3 mil COP adicionales por cada m² construido.
- Salta a la vista el cúmulo de puntos arriba-derecha (mansiones) y la franja inferior ($90.000): el describe() los escondía entre promedios; el gráfico los exhibe.
- Eso es EDA en estado puro: hipótesis visibles ANTES de cualquier modelo.

## 13. Heatmap de correlaciones y matriz de dispersión

- Heatmap: toda la matriz de Pearson en un vistazo; rojo positivo, azul negativo.
- Lecturas clave: habitaciones↔banos 0,75 y habitaciones↔área 0,69 (redundancia potencial); área↔arriendo 0,62; antigüedad↔arriendo −0,20.
- Variables redundantes anticipan problemas de multicolinealidad en modelos lineales (lo retomaremos en regresión).
- Matriz de dispersión ( fig_matriz_dispersion.png ): todos los scatter cruzados + histogramas en diagonal; versión matplotlib del pairplot de seaborn (opcional instalarla para estética extra).

## Un gráfico es un argumento

- Ejes etiquetados CON UNIDADES ("miles de COP", "m²")
- Título que declara el hallazgo, no el tipo de gráfico ("El área explica el 38% del arriendo")
- Barras arrancan en cero; anotaciones directas sobre el dato clave
- Paleta consistente y accesible (verificable en escala de grises)
- Pastel 3D: distorsiona áreas y es ilegible (además, pastel solo con &lt; 5 categorías)
- Truncar el eje Y de barras para exagerar diferencias minúsculas
- Doble eje Y disfrazando correlaciones forzadas
- Colormap arcoíris para variables continuas: inventa fronteras falsas

## 15. Las tablas que imprime eda_inmuebles.py

- Gradiente claro norte-caribe→sur: la ubicación vale hasta 117 mil COP mensuales entre extremos.
- El script también cruza TelecomUNO: fuga 23% en plan Basico vs 13% Premium.

## 16. Cuando mirar antes de modelar evitó desastres

## 17. Ejercicio en clase: informe EDA de TelecomUNO

- (5 min) Univariado: describe() de las numéricas + skew de facturacion_mensual y gb_datos. Identifiquen las 2 asimetrías más marcadas.
- (8 min) Histograma y boxplot de facturacion_mensual; cuantifiquen los outliers con IQR (no solo "se ven raros").
- (7 min) Barras de ciudad y tipo_plan + tabla de tasa de fuga por segmento con pd.crosstab(normalize="index") .
- (8 min) Dispersión antiguedad_meses vs facturacion_mensual + heatmap de correlaciones numéricas. ¿Alguna relación sorprendente?
- (7 min) Redacten 3 hallazgos en formato: hallazgo + evidencia (cifra/gráfico) + acción sugerida para el negocio.

## 18. Criterios de éxito del informe?

- Todo gráfico con título-hallazgo, ejes y unidades completos
- Outliers CUANTIFICADOS con IQR, no solo señalados visualmente
- Mediana usada para reportar variables asimétricas
- Los 3 hallazgos conectan evidencia estadística con acción de negocio
- Graficar sin revisar tipos (fechas/categorías como texto)
- Concluir causalidad desde una correlación ("las quejas CAUSAN fuga")
- Describir el gráfico en vez de interpretarlo ("aquí hay barras azules...")
- Pastel con 10 categorías o efecto 3D decorativo

## 19. Informe de laboratorio

- Inicio: presenta tablas y gráficos básicos con apoyo de la plantilla.
- Progreso: interpreta la mayoría de gráficos y cuantifica algunos outliers.
- Esperado: informe completo, interpretaciones correctas y hallazgos accionables.
- Excepcional: además, propone nuevas variables o segmentos y valida sus hipótesis con datos.

## 20. Trabajo independiente

- Lectura (2 h): plantilla de análisis exploratorio del curso + Han, Kamber &amp; Pei, sección 2.2 (resúmenes descriptivos). Revise la galería de matplotlib y guarde 2 ejemplos útiles.
- Práctica (2 h): extienda eda_inmuebles.py : agregue boxplot de arriendo por barrio y un gráfico propio suyo (con título-hallazgo). Guarde ambas figuras.
- Proyecto (2 h): complete el borrador COMPLETO del informe EDA de su dataset con la estructura de 6 secciones exigida.

## 21. Errores comunes

## 22. Cierre

- EDA = escuchar los datos antes de modelar: univariado, bivariado y multivariado.
- Tendencia central, dispersión y forma responden preguntas distintas; con asimetría, la mediana manda.
- Pearson mide asociación lineal; correlación jamás prueba causalidad.
- La galería mínima: histograma, boxplot, barras, dispersión, heatmap y matriz de dispersión, todos generados con matplotlib puro.
- Con este cierre, el material técnico del Avance 1 está completo.

