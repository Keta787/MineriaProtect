# Revisión crítica y reestructuración formal de los árboles de decisión

**Contexto de evaluación:** Sesión 7, proyecto de reincidencia laboral sobre JobPath/ESCO.  
**Variable objetivo:** `y = 1` si existe reincidencia laboral y `y = 0` si es primera vez.  
**Tamaño y prevalencia reportados:** 348.263 registros; tasa base de la clase 1 = 30,51%.  
**Experimento revisado:** tres árboles con `max_depth=3`, usando como predictores ISCO, nivel educativo y competencias ESCO.

> **Delimitación de evidencia.** Esta revisión usa exclusivamente las métricas y reglas consignadas en el informe base de la Sesión 7: accuracy baseline = 0,6949, accuracy del Árbol 3 = 0,7015, ausencia de hojas positivas en los árboles 1 y 2, y hojas 11 y 14 con reincidencia superior al 50% en el Árbol 3. No se sustituyen esas cifras por las de otros experimentos del repositorio con distinta prevalencia o profundidad.

## 1. Resumen Ejecutivo del Diagnóstico

Los tres árboles no están respondiendo exactamente la pregunta de negocio que los motivó. La pregunta solicita identificar qué perfiles o condiciones se asocian con la reincidencia, mientras que `DecisionTreeClassifier.predict()` convierte cada hoja en una decisión binaria mediante la clase mayoritaria. Por tanto, una rama puede presentar una tasa de reincidencia claramente superior a la tasa base y, aun así, ser etiquetada como clase 0 si su probabilidad estimada no supera 0,50. Esto explica que los árboles 1 (ISCO) y 2 (nivel educativo) tengan accuracy igual al baseline y F1 de la clase 1 igual a cero, sin que ello demuestre que sus variables carezcan de asociación.

El Árbol 3 sí produce separación operativa: alcanza accuracy 0,7015 y contiene dos hojas, 11 y 14, con reincidencia superior al 50%. Sin embargo, esa mejora no basta para atribuir capacidad causal ni para validar el modelo como predictor individual. La relación entre `occupation_code`, la definición de la variable objetivo y las competencias ESCO puede introducir fuga de información o, como mínimo, una proximidad semántica y de construcción que infla la señal. La corrección debe separar tres objetivos: descripción/segmentación de riesgo, predicción con un umbral de decisión explícito y evaluación de utilidad fuera de muestra.

## 2. Evaluación Crítica por Árbol

### 2.1 Árbol 1 (ISCO): fallas estructurales y por qué colapsa

**Planteamiento frente a formulación formal.** La intención de negocio es comparar la reincidencia entre grandes grupos ocupacionales. La formulación correcta para un árbol no es “¿qué grupo causa reincidencia?”, sino “¿qué partición binaria de la codificación ISCO reduce más la impureza de la variable `y`?”. CART selecciona, en cada nodo, el umbral que maximiza la reducción ponderada de Gini —o la entropía, si se configura `criterion="entropy"`—. Con ISCO tratado como variables indicadoras, los cortes `isco_grupo <= 0,5` y `> 0,5` son técnicamente adecuados: significan ausencia/presencia de un grupo, no una escala ordinal.

El problema es de objetivo y de lectura, no necesariamente de cálculo. La búsqueda de un split se guía por pureza y por el criterio de parada, pero la etiqueta de una hoja se obtiene por `argmax` de las probabilidades de clase. Si todas las hojas quedan por debajo de 0,50 para la clase 1, el árbol puede encontrar diferencias de tasa y seguir prediciendo 0 en todas ellas. En consecuencia:

- accuracy = 0,6949 puede coincidir con el clasificador mayoritario;
- recall, precision y F1 de la clase 1 pueden ser 0;
- las hojas no son inútiles para segmentación, pero sí insuficientes como clasificador binario con umbral 0,50;
- un lift reportado —hasta 1,14 en ISCO— es evidencia de concentración relativa, no evidencia de que una hoja deba etiquetarse automáticamente como “reincide”.

**Falla estructural principal.** Si la pregunta de negocio es “¿qué grupos tienen mayor propensión?”, el producto correcto es una tabla de tasas, intervalos de incertidumbre, tamaño de hoja y lift por grupo o segmento. Si la pregunta es “¿a quién activar para una intervención?”, el árbol debe optimizar una métrica sensible a la clase 1 y evaluar un umbral distinto de la clase mayoritaria. Un árbol optimizado y evaluado solo con accuracy responde a la pregunta “¿qué tan bien reproduce la clase más frecuente?”, que es una pregunta distinta.

### 2.2 Árbol 2 (Nivel Educativo): impacto de codificación ordinal y manejo de NaNs

**El umbral `nivel_ordinal <= 2,5` no es neutral.** Si `nivel_ordinal` codifica niveles educativos ordenados, el corte es legible como una separación entre niveles bajos y altos según la convención de codificación. Pero CART interpreta los valores numéricos como una escala ordenada: presupone que los niveles se pueden ordenar y que los cortes contiguos son comparables. No presupone causalidad ni una distancia sustantiva igual entre categorías. Si la codificación no representa un orden académico válido, el umbral es un artefacto de codificación. Incluso si el orden es válido, el árbol solo está probando una división acumulada; no está demostrando que el nivel 3 sea intrínsecamente el punto de quiebre.

La alternativa formal para una variable categórica nominal es one-hot encoding, o bien una comparación explícita de tasas por categoría. Para una variable ordinal, conviene contrastar dos especificaciones: (a) ordinal numérica, para probar una tendencia acumulada; y (b) indicadores por nivel, para no imponer una forma monotónica. La estabilidad del split debe comprobarse en validación cruzada y no solo en un único `train_test_split`.

**NaNs e imputación.** Un valor faltante no es automáticamente “nivel bajo”. Si los nulos fueron imputados con 0, con la categoría mínima o con una categoría “no reportado” que queda a la izquierda del corte, la regla `<= 2,5` mezcla dos fenómenos: nivel educativo y ausencia de información. En implementaciones donde los faltantes se enrutan por una rama fija, la misma advertencia aplica: la rama izquierda puede estar capturando el patrón de reporte, no una condición educativa. Por eso se debe:

1. conservar un indicador `nivel_no_reportado`;
2. documentar la regla de imputación y el sentido de cada rama;
3. comprobar la tasa de reincidencia de los faltantes por separado;
4. evitar presentar `nivel_ordinal <= 2,5` como regla sustantiva sin esa descomposición.

El lift de hasta 1,04 en Nivel Educativo es débil pero no equivale a ausencia de variación. El colapso a cero hojas positivas indica que la señal queda por debajo del umbral de decisión adoptado, no que la variable no tenga ninguna utilidad descriptiva.

### 2.3 Árbol 3 (Competencias): potencia predictiva frente a riesgo de leakage

El Árbol 3 es el único que supera el baseline reportado: accuracy = 0,7015 frente a 0,6949, y genera las hojas 11 y 14 con una proporción de reincidencia superior al 50%. La regla `n_skills_competence <= 18,5` es un corte técnicamente válido para un conteo: el algoritmo está separando valores enteros `<=18` de valores `>=19`. No obstante, 18,5 es un punto medio elegido por CART para maximizar reducción de impureza; no es por sí mismo un umbral de negocio ni una discontinuidad natural del fenómeno. Deben revisarse tamaño de hoja, estabilidad, intervalo de la tasa y replicación en validación.

La potencia aparente tiene un riesgo especial. Si `y` se construyó a partir de repeticiones del mismo `occupation_code`, y las competencias ESCO se asignan precisamente desde ese código ocupacional, entonces las competencias pueden funcionar como una representación indirecta del identificador que participa en la construcción del objetivo. Aunque `veces_ese_oficio` no aparezca literalmente en `X`, puede existir fuga semántica o de construcción: el modelo aprende la identidad ocupacional o una codificación casi determinista de ella, en lugar de una señal disponible antes de la predicción.

La prueba necesaria es una auditoría de procedencia:

- verificar si `occupation_code` o cualquier derivación suya interviene en la creación de `y`;
- medir cuántos valores de competencias son deterministas o casi deterministas por ocupación;
- entrenar una versión sin variables derivadas de ocupación y otra con agrupación independiente;
- separar por persona (`resume_id`) cuando varias filas pertenecen al mismo individuo;
- comparar contra un modelo que use solo información disponible en el momento real de decisión.

La diferencia train-test reportada de 0,0000/0,0005 no prueba que no exista leakage. Solo indica que, bajo esa partición aleatoria y esa métrica, el comportamiento global es muy parecido. Con duplicados, filas de la misma persona o representaciones ocupacionales compartidas entre train y test, ambas particiones pueden contener la misma señal. La ausencia de una brecha de accuracy puede ser consecuencia de una señal estable —o de una fuga estable—, no una validación de causalidad ni de generalización temporal.

## 3. Diagnóstico de la Brecha: ¿por qué la pregunta dice X y el árbol responde Y?

| Pregunta de negocio | Formulación que se ejecutó | Respuesta efectiva del árbol | Brecha |
|---|---|---|---|
| ¿Qué grupos ISCO tienen mayor reincidencia? | Clasificar cada hoja por la clase mayoritaria con `predict()` | “¿Qué hojas superan 50% de probabilidad estimada?” | Se pierde el ranking de tasas y lift cuando ninguna hoja cruza 0,50. |
| ¿Influye el nivel educativo? | Cortar una variable numérica codificada y posiblemente imputada | “¿Qué lado del umbral produce menor impureza?” | Se confunde nivel con codificación, orden impuesto y patrón de faltantes. |
| ¿Las competencias permiten identificar reincidencia? | Usar conteos/atributos ESCO derivados del entorno ocupacional | “¿Qué combinación separa mejor la etiqueta en esta partición?” | La señal puede ser predictiva, pero también indirecta o filtrada desde `occupation_code`. |
| ¿El modelo mejora sobre el baseline? | Comparar accuracy | Igualar o superar la clase mayoritaria | Accuracy no mide la utilidad para detectar la clase 1 ni el costo de falsos negativos. |

Con tasa base de clase 1 igual a `p = 0,3051`, el clasificador por defecto de un árbol predice 1 solo si `\hat p >= 0,50`. Esa regla de 0,50 no se deriva de la prevalencia; es la regla de menor error cuando los costos de falso positivo y falso negativo son iguales y las probabilidades están calibradas. Por eso no debe afirmarse que “30,51% implica automáticamente usar umbral 0,3051”.

Sí existe una justificación matemática para usar un umbral menor cuando se desea compensar el desbalance. Con pesos de clase `w_0` y `w_1`, la decisión ponderada predice 1 cuando:

`w_1 p(x) >= w_0 (1 - p(x))`

lo que equivale a:

`p(x) >= w_0 / (w_0 + w_1)`.

Para `class_weight="balanced"` y dos clases, `w_0` es proporcional a `1/0,6949` y `w_1` a `1/0,3051`; el umbral algebraico resultante es aproximadamente `0,3051`. Esto explica la conexión con la tasa base, pero no convierte ese valor en óptimo de negocio. El umbral final debe seleccionarse en validación, usando precision-recall, recall mínimo, costo esperado o beneficio de la intervención.

## 4. Plan de Acción y Reconfiguración Recomendada

### 4.1 Separar explícitamente los objetivos

Mantener dos productos analíticos:

1. **Segmentación explicativa:** tasas de reincidencia, lift, tamaño de hoja e intervalos por grupo/hoja. No usar la etiqueta mayoritaria de la hoja como única interpretación.
2. **Predicción operativa:** probabilidades fuera de muestra, umbral elegido con criterio de negocio y métricas para la clase 1: recall, precision, F1, PR-AUC, matriz de confusión y calibración.

### 4.2 Configuración del árbol

- Mantener `max_depth=3` solo si la estabilidad y la interpretabilidad lo justifican; seleccionar la profundidad mediante validación cruzada estratificada, no por igualdad accidental de accuracy.
- Probar `criterion="gini"` y `criterion="entropy"` como análisis de sensibilidad, sin presentar una elección como superior sin evidencia.
- Usar `class_weight="balanced"` como línea base para el objetivo predictivo y comparar con pesos definidos por costos de negocio.
- Controlar `min_samples_leaf` y `min_samples_split` para evitar reglas basadas en hojas pequeñas; reportar el tamaño mínimo observado.
- Evaluar `predict_proba()` y no solo `predict()`. Seleccionar el umbral en un conjunto de validación separado; reservar el test final para una sola evaluación.
- Reportar intervalos de confianza o bootstrap para las tasas de hojas 11 y 14.

### 4.3 Remuestreo y métricas

El remuestreo debe hacerse dentro de cada partición de entrenamiento para no contaminar validación/test. Comparar:

- pesos de clase;
- submuestreo de la clase 0;
- sobremuestreo de la clase 1, solo dentro de train;
- conjunto original con ajuste de umbral.

La métrica primaria no debe ser accuracy. Para detección de reincidentes, usar recall y precision de la clase 1, F1 o PR-AUC según el costo de intervención. Accuracy debe conservarse como referencia, no como criterio único de selección.

### 4.4 Ingeniería y auditoría de variables

- ISCO: conservar indicadores por grupo para análisis descriptivo; explorar agrupaciones justificadas por dominio y validar su estabilidad.
- Nivel educativo: comparar ordinal numérica, one-hot y categoría explícita de no reportado.
- Competencias: distinguir conteos disponibles antes de la decisión de los derivados del mismo `occupation_code` usado para construir `y`.
- Auditoría de leakage: rehacer el experimento con partición por persona, y si el uso real lo exige, con separación temporal.
- Si se pretende predecir la primera reincidencia antes de que ocurra, excluir toda variable calculada con información posterior al evento o con el historial completo de la misma persona.

## 5. Reglas de Negocio Corregidas y Reescritas

Las siguientes reglas son formulaciones válidas de negocio, siempre que se presenten como asociaciones predictivas y no como causalidad:

1. **ISCO — regla de segmentación:** “Los grupos ISCO deben ordenarse por tasa observada de reincidencia y lift respecto de 30,51%. El árbol puede proponer particiones, pero la regla de intervención solo se activa si el segmento supera el umbral de utilidad definido y cuenta con tamaño y estabilidad suficientes.”
2. **ISCO — regla predictiva:** “Para un nuevo registro, clasificar como candidato a intervención cuando la probabilidad estimada por el árbol supere el umbral validado para el costo de falsos negativos; no exigir que la hoja supere 50% si el objetivo es priorización.”
3. **Nivel educativo:** “Interpretar una división como diferencia entre niveles codificados únicamente después de verificar que la codificación es ordinal, que los faltantes tienen categoría propia y que la tasa no está explicada por el patrón de no reporte.”
4. **Competencias ESCO:** “Un perfil con el patrón de competencias asociado a las hojas 11 o 14 puede priorizarse porque esas hojas superan 50% de reincidencia en el informe base, pero la regla queda condicionada a superar una prueba de leakage y a replicarse en una partición por persona o temporal.”
5. **Regla de comunicación:** “El árbol identifica segmentos con distinta propensión; no demuestra que ISCO, educación o competencias causen reincidencia.”
6. **Regla de monitoreo:** “Toda regla desplegada debe vigilar prevalencia, precision, recall, lift, tamaño de hoja y deriva de datos. Si cambia la tasa base, el umbral de decisión y la interpretación de accuracy deben recalibrarse.”

En síntesis, la reestructuración no consiste en forzar que los árboles 1 y 2 produzcan hojas de clase 1. Consiste en alinear la salida con la pregunta: usar tasas y lift para explicar segmentos, probabilidades y umbrales validados para decidir, y una auditoría independiente para asegurar que la señal del Árbol 3 no sea una consecuencia de la forma en que se construyeron `occupation_code`, las competencias y la variable objetivo.

## 6. Implementación reproducible de la corrección

La configuración corregida quedó implementada en:

```text
scripts/arbol_reincidencia/generar_arboles_corregidos.py
```

Se ejecuta desde la raíz del repositorio con:

```text
python scripts\arbol_reincidencia\generar_arboles_corregidos.py
```

El script usa `GroupShuffleSplit` por `resume_id`, `max_depth=3`, `min_samples_leaf=100`, `class_weight="balanced"`, imputación aprendida solo en entrenamiento y selección del umbral mediante F1 en validación. Genera nuevas reglas, métricas, auditoría de procedencia y tres PNG en:

```text
reports/arbol_reincidencia_corregido/
```

Los artefactos históricos de `reports/arbol_reincidencia/figuras/` no se reemplazan. Las métricas nuevas no deben compararse directamente con las cifras de la Sesión 7: la partición por persona y el umbral validado responden a un protocolo metodológico distinto y más estricto.
