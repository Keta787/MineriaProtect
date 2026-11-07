# Árboles de decisión para estudiar la reincidencia laboral

## Objetivo y alcance

El objetivo es estudiar si una experiencia laboral corresponde a una **reincidencia en el mismo oficio** o a la primera vez que la persona lo ejerce:

```python
y = (df["veces_ese_oficio"] >= 2).astype(int)
# 0 = primera vez en ese oficio
# 1 = reincide en ese oficio
```

La unidad de análisis es una experiencia laboral (`resume_id` + oficio). La variable `veces_ese_oficio` se usa únicamente para construir `y`; no se incluye como predictor, porque hacerlo produciría fuga directa de información.

El estudio compara tres árboles interpretables:

1. **ISCO:** gran grupo ocupacional.
2. **Nivel educativo:** nivel ordinal y bandera de no reporte.
3. **Competencias ESCO:** número de competencias de tipo *skill/competence* exigidas por el oficio.

Los árboles se utilizan para dos propósitos distintos:

- **Segmentación descriptiva:** identificar ramas con distinta proporción de reincidencia.
- **Priorización predictiva:** ordenar casos mediante `predict_proba()` y aplicar un umbral de decisión validado.

El modelo no demuestra causalidad. Una rama con mayor tasa de reincidencia representa una asociación observada en los datos.

## 1. Datos y preparación

### 1.1 Dataset

El flujo corregido usa:

```text
data/03_processed/empleos_con_competencias_limpio.csv
```

El dataset se regeneró desde las fuentes del proyecto. Contiene 376.567 experiencias y 348.263 filas con competencias ESCO clasificadas; las experiencias sin ocupación clasificada conservan los contadores de competencias vacíos.

### 1.2 Variables predictoras

| Árbol | Variables | Tratamiento |
|---|---|---|
| ISCO | `isco_mayor` | Codificación one-hot; los valores faltantes se representan como `isco_mayor_No reportado`. |
| Nivel educativo | `nivel_ordinal`, `nivel_no_reportado` | `Secondary=1`, `Bachelor=2`, `Master=3`, `PhD=4`; los no reportados conservan una bandera propia y el valor ordinal faltante se imputa con la mediana de train. |
| Competencias ESCO | `n_skills_competence`, `skills_no_reportadas` | El conteo se imputa con la mediana de train y se conserva un indicador de ausencia. |

`n_skills_competence` describe las competencias que ESCO exige al cargo; no mide las competencias que la persona realmente domina. Esta diferencia es esencial para no sobreinterpretar el resultado.

### 1.3 Control de fuga y partición

La etiqueta se deriva de la repetición del oficio por `resume_id` y `occupation_code`. Por ello, una división aleatoria por fila podría colocar experiencias de la misma persona en train y test. El flujo corregido usa:

```text
GroupShuffleSplit por resume_id
```

La partición resultante es:

| Conjunto | Filas |
|---|---:|
| Train | 211.966 |
| Validación | 70.659 |
| Test | 93.942 |

Las imputaciones se aprenden únicamente en train. El conjunto de validación sirve para elegir el umbral; el test se reserva para la evaluación final.

## 2. Configuración de los árboles corregidos

Los tres modelos usan la misma configuración estructural:

```python
DecisionTreeClassifier(
    max_depth=3,
    min_samples_leaf=100,
    class_weight="balanced",
    criterion="gini",
    random_state=42,
)
```

### Explicación de los parámetros

- **`max_depth=3`:** limita la complejidad y mantiene las reglas legibles.
- **`min_samples_leaf=100`:** evita hojas demasiado pequeñas y reglas inestables.
- **`class_weight="balanced"`:** asigna mayor costo a errores sobre la clase 1, cuya prevalencia es menor.
- **`criterion="gini"`:** selecciona divisiones que reducen la impureza ponderada. Gini favorece nodos donde una clase queda relativamente concentrada, pero no garantiza que la clase 1 sea mayoritaria.
- **Umbral separado del árbol:** el árbol estima probabilidades; la decisión final no se fija automáticamente en 0,50. El umbral se elige sobre validación maximizando F1 de la clase 1.

El umbral de 0,50 es apropiado únicamente bajo una función de costos simétrica y probabilidades calibradas. No se debe imponer solo por costumbre.

## 3. Reglas y explicación por árbol

### 3.1 Árbol ISCO

**PNG:** `reports/arbol_reincidencia_corregido/figuras/arbol_isco.png`
**Reglas:** `reports/arbol_reincidencia_corregido/reglas/arbol_isco.txt`

Reglas exportadas:

```text
|--- isco_mayor_No reportado <= 0.50
|   |--- isco_mayor_5 <= 0.50
|   |   |--- isco_mayor_4 <= 0.50
|   |   |   |--- class: 1
|   |   |--- isco_mayor_4 >  0.50
|   |   |   |--- class: 0
|   |--- isco_mayor_5 >  0.50
|   |   |--- class: 1
|--- isco_mayor_No reportado > 0.50
|   |--- class: 0
```

La raíz separa primero los registros sin gran grupo ISCO reportado. Dentro de los registros clasificados, aparecen los grupos 5 y 4. Los umbrales `<= 0,50` y `> 0,50` son cortes de variables binarias one-hot: significan ausencia o presencia del grupo, no una escala ordinal.

El modelo seleccionó el umbral **0,43** en validación. En test obtuvo:

- accuracy: **0,3916**;
- precision de clase 1: **0,3093**;
- recall de clase 1: **0,9429**;
- F1 de clase 1: **0,4657**;
- PR-AUC: **0,3191**.

La caída de accuracy no es un error de ejecución: es el costo de priorizar la detección de reincidentes. El modelo captura casi todos los positivos, pero genera muchos falsos positivos. Por ello, esta configuración sirve para **tamizaje amplio**, no para una intervención costosa sin una segunda etapa de validación.

### 3.2 Árbol de nivel educativo

**PNG:** `reports/arbol_reincidencia_corregido/figuras/arbol_nivel_educativo.png`
**Reglas:** `reports/arbol_reincidencia_corregido/reglas/arbol_nivel_educativo.txt`

Reglas exportadas:

```text
|--- nivel_ordinal <= 2.50
|   |--- nivel_ordinal <= 1.50
|   |   |--- class: 1
|   |--- nivel_ordinal >  1.50
|   |   |--- nivel_no_reportado <= 0.50
|   |   |   |--- class: 1
|   |   |--- nivel_no_reportado >  0.50
|   |   |   |--- class: 1
|--- nivel_ordinal >  2.50
|   |--- nivel_ordinal <= 3.50
|   |   |--- class: 0
|   |--- nivel_ordinal >  3.50
|   |   |--- class: 0
```

El corte `nivel_ordinal <= 2,50` separa los niveles codificados 1 y 2 de los niveles 3 y 4. El valor 2,50 es un punto medio entre categorías enteras generado por CART; no significa que exista una frontera natural en el nivel 2,5 ni demuestra una relación causal.

La bandera `nivel_no_reportado` evita confundir la ausencia de información con el nivel educativo mínimo. En este árbol, la bandera aparece en una rama profunda, pero ambas hojas se etiquetan igual; por tanto, con esta configuración no aporta una diferenciación final importante.

El umbral validado fue **0,10**. En test obtuvo:

- accuracy: **0,2813**;
- precision de clase 1: **0,2813**;
- recall de clase 1: **1,0000**;
- F1 de clase 1: **0,4391**;
- PR-AUC: **0,2927**.

El resultado indica que el modelo es muy agresivo al priorizar la clase 1. El nivel educativo puede servir como variable de segmentación, pero por sí solo no ofrece una separación suficientemente precisa para decidir intervenciones individuales.

### 3.3 Árbol de competencias ESCO

**PNG:** `reports/arbol_reincidencia_corregido/figuras/arbol_competencias_ESCO.png`
**Reglas:** `reports/arbol_reincidencia_corregido/reglas/arbol_competencias_ESCO.txt`

Reglas exportadas:

```text
|--- skills_no_reportadas <= 0.50
|   |--- n_skills_competence <= 18.50
|   |   |--- n_skills_competence <= 13.50
|   |   |   |--- class: 0
|   |   |--- n_skills_competence >  13.50
|   |   |   |--- class: 0
|   |--- n_skills_competence >  18.50
|   |   |   |--- n_skills_competence <= 19.50
|   |   |   |   |--- class: 1
|   |   |   |--- n_skills_competence >  19.50
|   |   |   |   |--- class: 1
|--- skills_no_reportadas >  0.50
|   |--- class: 0
```

La raíz separa primero los registros sin competencias reportadas. Entre los cargos con competencias, los cortes `13,5` y `18,5` son puntos medios entre conteos enteros. En términos prácticos, `n_skills_competence <= 18,5` equivale a hasta 18 competencias y `>18,5` equivale a 19 o más.

El umbral validado fue **0,10**. En test obtuvo:

- accuracy: **0,3568**;
- precision de clase 1: **0,3043**;
- recall de clase 1: **1,0000**;
- F1 de clase 1: **0,4666**;
- PR-AUC: **0,3558**.

Este árbol ofrece la mayor PR-AUC de los tres modelos corregidos, pero el resultado no debe interpretarse como evidencia de que las competencias de la persona causan reincidencia. Las competencias ESCO se asignan al oficio y `veces_ese_oficio` se calcula usando la repetición del oficio. Existe, por tanto, proximidad estructural entre predictor y objetivo.

La auditoría encontró:

| Indicador | Resultado |
|---|---:|
| Códigos de ocupación clasificados | 2.855 |
| Filas con `occupation_code` | 348.263 |
| Valores distintos de `n_skills_competence` | 68 |
| Ocupaciones con más de un valor de competencias | 0 |

Que cada ocupación tenga un único conteo de competencias confirma que el conteo es una representación determinista del cargo. No es una fuga directa de la etiqueta, pero sí una señal indirecta del `occupation_code` que participa en la definición de reincidencia. Antes de usar este modelo en producción o formular conclusiones causales, debe evaluarse una versión con separación temporal, partición por persona y, si el objetivo lo requiere, predictores que no sean derivados del oficio repetido.

## 4. Comparación de resultados

| Modelo | Umbral | Accuracy test | Precision clase 1 | Recall clase 1 | F1 clase 1 | PR-AUC | Hojas |
|---|---:|---:|---:|---:|---:|---:|---:|
| ISCO | 0,43 | 0,3916 | 0,3093 | 0,9429 | 0,4657 | 0,3191 | 4 |
| Nivel educativo | 0,10 | 0,2813 | 0,2813 | 1,0000 | 0,4391 | 0,2927 | 5 |
| Competencias ESCO | 0,10 | 0,3568 | 0,3043 | 1,0000 | 0,4666 | 0,3558 | 5 |

Estas métricas **no deben compararse directamente** con el experimento histórico de `train_test_split` por fila y umbral 0,50. El protocolo corregido cambia la unidad de separación, el tratamiento del desbalance y el umbral; por tanto, responde a una pregunta predictiva distinta y más estricta.

La lectura correcta es:

- **ISCO:** mejor equilibrio entre recall y precisión dentro de este experimento, pero con muchos falsos positivos.
- **Nivel educativo:** detecta la clase 1 de forma exhaustiva al umbral elegido, pero su precision y PR-AUC son las menores.
- **Competencias ESCO:** presenta la mayor PR-AUC y el F1 más alto por una diferencia pequeña; requiere la auditoría de leakage más cuidadosa.

## 5. Interpretación estadística y de negocio

### 5.1 Por qué ya no se usa únicamente accuracy

La clase 1 es minoritaria. Un modelo puede alcanzar una accuracy aparentemente razonable prediciendo siempre la clase 0, aunque no detecte ningún reincidente. Por eso se reportan precision, recall, F1 y PR-AUC de la clase 1.

El ajuste del umbral cambia explícitamente la política de decisión:

- umbral bajo: aumenta el recall y también los falsos positivos;
- umbral alto: mejora la precision, pero puede perder reincidentes.

El umbral no se debe fijar automáticamente igual a la prevalencia. Con costos simétricos, el umbral teórico es 0,50; con `class_weight="balanced"` aparece una relación algebraica con la prevalencia, pero la selección final debe responder al costo de cada tipo de error. En este flujo se eligió el umbral que maximizó F1 en validación, no en test.

### 5.2 Por qué la brecha train-test pequeña no elimina el riesgo

La separación por `resume_id` reduce la contaminación entre conjuntos, pero una diferencia pequeña entre train y test no prueba ausencia de leakage. Una señal derivada de una ocupación puede ser estable en ambos conjuntos y seguir siendo una representación indirecta del identificador usado para construir `y`.

La validación futura debe incluir:

1. partición temporal si el modelo se usará para nuevos registros;
2. evaluación por persona;
3. comparación con variables no derivadas de la ocupación repetida;
4. análisis de calibración y estabilidad de los umbrales;
5. intervalos de incertidumbre para las tasas de cada hoja.

## 6. Reglas de negocio corregidas

1. **ISCO:** usar el modelo para priorizar registros de alta probabilidad, no para afirmar que un grupo ocupacional causa reincidencia.
2. **Nivel educativo:** interpretar los cortes como asociaciones entre categorías codificadas; mantener “no reportado” separado del nivel académico.
3. **Competencias ESCO:** interpretar `n_skills_competence` como complejidad de competencias exigidas por el cargo, no como habilidades poseídas por la persona.
4. **Intervención:** aplicar el umbral elegido en validación solo si la organización acepta el volumen de falsos positivos resultante.
5. **Monitoreo:** recalcular prevalencia, precision, recall, F1, PR-AUC, tamaño de hojas y deriva de datos después del despliegue.
6. **Causalidad:** ninguna regla debe formularse como “el nivel educativo” o “las competencias” producen reincidencia; el resultado es asociativo y predictivo.

## 7. Archivos generados

### Script reproducible

```text
scripts/arbol_reincidencia/generar_arboles_corregidos.py
```

### PNG

| Archivo | Descripción |
|---|---|
| `reports/arbol_reincidencia_corregido/figuras/arbol_isco.png` | Árbol corregido con ISCO |
| `reports/arbol_reincidencia_corregido/figuras/arbol_nivel_educativo.png` | Árbol corregido con nivel educativo |
| `reports/arbol_reincidencia_corregido/figuras/arbol_competencias_ESCO.png` | Árbol corregido con competencias ESCO |

### Reglas y tablas

| Archivo | Descripción |
|---|---|
| `reports/arbol_reincidencia_corregido/reglas/*.txt` | Reglas `export_text` de cada árbol |
| `reports/arbol_reincidencia_corregido/tablas/metricas_arboles_corregidos.csv` | Métricas finales sobre test |
| `reports/arbol_reincidencia_corregido/tablas/auditoria_leakage_competencias.csv` | Auditoría de procedencia de competencias |
| `reports/arbol_reincidencia_corregido/configuracion.json` | Parámetros y protocolo de entrenamiento |

Los PNG históricos de `reports/arbol_reincidencia/figuras/` no fueron reemplazados. El flujo corregido se conserva en una carpeta separada para que los resultados antiguos y los nuevos puedan auditarse de forma independiente.
