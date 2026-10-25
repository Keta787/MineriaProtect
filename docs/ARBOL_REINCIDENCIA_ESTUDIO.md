# Árbol de Decisión para predecir reincidencia por oficio

**Objetivo:** Entrenar un árbol de decisión para predecir si una persona **reincide** en el mismo oficio (`veces_ese_oficio >= 2`) o si lo ejerce por **primera vez** (`veces_ese_oficio == 1`), siguiendo el flujo de la Sesión 7 (caso TelecomUNO) adaptado a nuestro dataset.

**Dataset:** `data/03_processed/empleos_limpio_con_competencias .csv`  
**Unidad de análisis:** Registros de empleos (cada fila representa una experiencia laboral con su `occupation_code`)

---

## 1. ¿Por qué estas decisiones?

### 1.1 Variable objetivo `y`
Se calculó usando `veces_ese_oficio`, columna ya calculada por `(resume_id, occupation_code)`.

```python
y = (df['veces_ese_oficio'] >= 2).astype(int)
# 0 = Primera vez que esta persona ejerce este oficio concreto
# 1 = Ya ha ejercido este mismo oficio anteriormente (reincide)
```

Usar `>= 2` es más intuitivo para el negocio: **1 = sí reincide**.

### 1.2 Variables predictoras `X`
Tras análisis, se optó por el enfoque más minimalista e interpretable:

| Variable | Acción | Justificación |
|---|---|---|
| `isco_mayor` | **Usar** (con `get_dummies`) | Variable clave. Diferentes grandes grupos ISCO presentan tasas distintas de reincidencia. Responde directamente a la pregunta orientadora. |
| `veces_ese_oficio` | **DESCARTAR** | **Fuga de información.** Se usa para crear `y`. Si se incluye en `X`, el árbol aprendería a "copiar" la respuesta en lugar de aprender patrones reales. |
| `dur_Q` | **DESCARTAR** | Duración de esa experiencia en particular, no indica cuántas veces se ha repetido. |
| `nivel_ordinal` / `nivel_no_reportado` | **DESCARTAR (por ahora)** | Podrían aportar, pero para este objetivo se prioriza interpretabilidad con `isco_mayor`. |
| `n_skills_essential` | **DESCARTAR** | Conteo de competencias, no explica la reincidencia por oficio. |
| `estado_competencias` | **DESCARTAR** | Más descriptivo que predictivo para este objetivo. |

```python
df['isco_mayor'] = categorias.isco_mayor(df)
X = pd.get_dummies(df[['isco_mayor']], columns=['isco_mayor'])
```

---

## 2. Flujo aplicado (Sesión 7)

Siguiendo el mismo procedimiento que con TelecomUNO:

| Paso | Acción | Notas |
|---|---|---|
| 1 | **Cargar datos** | `empleos_limpio_con_competencias .csv` desde `data/03_processed/` |
| 2 | **Crear `y`** | `(veces_ese_oficio >= 2).astype(int)` |
| 3 | **Crear `X`** | Solo `isco_mayor` con `pd.get_dummies`. **Sin `veces_ese_oficio`.** |
| 4 | **Separar train/test** | `train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)`. Se mantiene proporción de clases (estratificado). |
| 5 | **Comparar profundidades** | `[2,3,4,5,8,None]` comparando `train_acc` vs `test_acc` y `n_leaves`. Justificar elección. |
| 6 | **Entrenar con `max_depth=4`** | `DecisionTreeClassifier(max_depth=4, random_state=42).fit(X_train, y_train)` |
| 7 | **Graficar y extraer reglas** | `plot_tree(...)` → `arbol_fuga_completo.png`, `export_text(...)` → `arbol_fuga_export_completo.txt` |
| 8 | **Analizar 4 primeras preguntas** | Tomar en orden exacto del árbol. Calcular clientes, tasa de reincidencia, lift y acción de retención. |

---

## 3. Resultados

### 3.1 Distribución de la variable objetivo
```text
y
0    0.717846 (Primera vez)
1    0.282154 (Reincide)
Name: proportion, dtype: float64
```

**Tasa global (train):** ~28.21% reincide. La clase mayoritaria es **"Primera vez" (0)** con ~71.78%.

### 3.2 Comparación con baseline (clasificador mayoritario)
Siguiendo la lógica de TelecomUNO: **¿Supera el árbol predecir "siempre no fuga/reincide"?**

```python
from sklearn.dummy import DummyClassifier
dummy = DummyClassifier(strategy='most_frequent')
```

**Resultados:**

- **Baseline (most_frequent):** Accuracy = 0.717841  
  Matriz de confusión: `[[67579, 0],[26563, 0]]`  
  `classification_report`: Precision/Recall/F1 para clase 1 = 0.00 (no identifica ningún reincidente)

- **Árbol `max_depth=4`:** Accuracy = 0.717841  
  Matriz de confusión idéntica: `[[67579, 0],[26563, 0]]`  
  `classification_report`: Precision/Recall/F1 para clase 1 = 0.00

**Conclusión:** Con solo `isco_mayor`, el árbol **NO supera** al baseline en accuracy global. Tampoco identifica reincidentes individualmente, porque **ninguna hoja alcanza mayoría para clase 1**.

### 3.3 Comparación de profundidades

| max_depth | train_acc | test_acc | n_leaves |
|---|---|---|---|
| 2 | 0.717847 | 0.717841 | 3 |
| 3 | 0.717847 | 0.717841 | 4 |
| 4 | 0.717847 | 0.717841 | 5 |
| 5 | 0.717847 | 0.717841 | 6 |
| 8 | 0.717847 | 0.717841 | 9 |
| None | 0.717847 | 0.717841 | 10 |

**Justificación para elegir `max_depth=4`:**

- **Sin overfitting detectable:** `train_acc == test_acc` en todas las profundidades. La métrica global no mejora al aumentar profundidad.
- **Legibilidad para negocio:** Un árbol con `max_depth=4` tiene techo teórico 16 hojas (aquí 5). Es fácil de leer, discutir y traducir a reglas accionables.
- **Equilibrio interpretabilidad vs complejidad:** Suficiente para ver los **primeros splits** (los que realmente separan) sin generar un árbol ilegible.
- **Coincide con la práctica de la sesión:** Tal como se hizo con TelecomUNO, se elige la profundidad más legible que permita extraer las reglas claras.

### 3.4 Importancia de variables (`feature_importances_`)

```csv
feature,importance
isco_mayor_2,0.346564  (Professionals)
isco_mayor_9,0.244169  (Elementary occupations)
isco_mayor_5,0.233170  (Service and sales workers)
isco_mayor_3,0.176097  (Technicians and associate professionals)
isco_mayor_1,0.000000
isco_mayor_4,0.000000
isco_mayor_6,0.000000
isco_mayor_7,0.000000
isco_mayor_8,0.000000
```

Los pesos confirman lo que vemos en el árbol: **los splits importantes caen en grupos 2, 3, 5 y 9**. Estos son justamente los primeros 4 que aparecen en `export_text`.

### 3.5 Árbol generado (`max_depth=4`)

**Archivo:** `arbol_fuga_completo.png`  
**Reglas:** `arbol_fuga_export_completo.txt`

```text
|--- isco_mayor_5 <= 0.50
|   |--- isco_mayor_3 <= 0.50
|   |   |--- isco_mayor_9 <= 0.50
|   |   |   |--- isco_mayor_2 <= 0.50
|   |   |   |   |--- class: 0
|   |   |   |--- isco_mayor_2 >  0.50
|   |   |   |   |--- class: 0
|   |   |--- isco_mayor_9 >  0.50
|   |   |   |--- class: 0
|   |--- isco_mayor_3 >  0.50
|   |   |--- class: 0
|--- isco_mayor_5 >  0.50
|   |--- class: 0
```

**Observación clave:** **Todas las hojas son clase 0 (Primera vez).** Esto es esperado por la teoría: el algoritmo busca minimizar impureza (Gini). Aunque algunas ramas suben la tasa de reincidencia, **ninguna supera el 50%**, por lo que la clase mayoritaria sigue siendo 0 y el árbol predice "primera vez" en todo el conjunto.

---

## 4. Las 4 primeras preguntas (análisis detallado)

Tomadas **exactamente en el orden** que aparecen en `export_text`. Se calculan sobre el set **train** estratificado.

| # | Pregunta | Regla del árbol | Rama | Clientes (train) | Tasa de reincidencia | Lift (rama / global 28.21%) | Ganancia de información (intuición) | Acción de retención |
|---|---|---|---|---|---|---|---|---|
| **1** | ¿Pertenece al grupo ISCO 5 (Service and sales workers)? | `isco_mayor_5 <= 0.50` | **Izq (NO):** No es grupo 5 → 225099 / **Der (SÍ):** Sí es grupo 5 → 57326 | 225099 / 57326 | Izq: **26.5%** / Der: **34.8%** | Der / global = **1.234** (+23.4%) | **Primera pregunta (raíz).** Es la que mejor separa. Al pasar a grupo 5 sube la tasa ~6.6 pp sobre la población sin grupo 5. | **Alta prioridad.** Enfocar retención en *Service and sales workers*. Analizar por suboficio dentro de grupo 5 (motivos de repetición/abandono) y crear acciones específicas. |
| **2** | ¿Pertenece al grupo ISCO 3 (Technicians and associate professionals)? *(sigue rama NO grupo 5)* | `isco_mayor_3 <= 0.50` | **Izq (NO):** No es grupo 3 → / **Der (SÍ):** Sí es grupo 3 → (dentro de no-grupo-5) | 173814 / 51285 (sobre 225099 sin grupo 5) | Izq: **24.8%** / Der: **32.5%** | Der / global = **1.152** (+15.2%) | Dentro de los que **NO** son grupo 5, pertenecer a grupo 3 eleva notablemente la propensión. | **Segunda prioridad.** Considerar seguimiento a técnicos/profesionales de apoyo que ya han estado antes o que muestran patrones de reincidencia. |
| **3** | ¿Pertenece al grupo ISCO 9 (Elementary occupations)? *(sigue NO5, NO3)* | `isco_mayor_9 <= 0.50` | **Izq (NO):** No es grupo 9 → / **Der (SÍ):** Sí es grupo 9 → | 138131 / 35683 (sobre subpoblación NO5,NO3) | Izq: **22.6%** / Der: **33.3%** | Der / global = **1.181** (+18.1%) | También genera buena separación dentro de esa subpoblación. Tasa elevada pese a ser ocupaciones elementales. | **Tercera prioridad.** Vigilar reincidencia en ocupaciones elementales. Puede deberse a rotación cíclica o a que son empleos más accesibles para volver a ejercer. |
| **4** | ¿Pertenece al grupo ISCO 2 (Professionals)? *(sigue NO5, NO3, NO9)* | `isco_mayor_2 <= 0.50` | **Izq (NO):** Ninguno de 5,3,9,2 → / **Der (SÍ):** Sí es grupo 2 → | 91428 / 46703 (sobre subpoblación NO5,NO3,NO9) | Izq: **18.4%** / Der: **30.7%** | Der / global = **1.088** (+8.8%) | Menor ganancia relativa a las anteriores, pero sigue elevando la tasa respecto a la rama "ninguno de estos". | **Cuarta prioridad.** Grupo 2 (Profesionales) tiene propensión moderada-alta. El segmento con **menor** propensión son quienes **NO** pertenecen a 2,3,5,9 (principalmente grupos 1,4,6,7,8) con ~18.4%. |

---

## 5. Interpretación desde la teoría (Sesión 7)

- **"Preguntas secuenciales":** El árbol hace preguntas binarias en orden. Primero `isco_mayor_5` (mayor ganancia/separación), luego `isco_mayor_3`, luego `isco_mayor_9`, luego `isco_mayor_2`. Esto coincide con `feature_importances_`.
- **Gini/pureza:** El algoritmo elige la pregunta que deja las ramas **más puras** tras dividir. Aunque ninguna rama se vuelve "puramente reincide" (todas <50%), sí logra **segmentar**: pasa de 28.21% global a 34.8% en la mejor rama.
- **Sobreajuste:** Al comparar `[2,3,4,5,8,None]`, **no hay brecha** entre train y test. Elegimos `max_depth=4` por **legibilidad**, no por ganar accuracy.
- **Baseline obligatorio:** Comparar con `most_frequent` es fundamental. Aquí **no hay mejora** en accuracy - el valor está en la **interpretación y segmentación**.
- **Causalidad vs correlación:** Decir "grupo 5 reincide más" **NO** implica causalidad. Solo indica correlación/patrón encontrado por el árbol.

---

## 6. Conclusión práctica

**Hallazgo principal:** Según el árbol, la probabilidad de reincidir **aumenta** cuando la persona pertenece a los grupos ISCO **5, 3, 9 o 2**. Los grupos con **menor propensión** son los que quedan fuera de estos (especialmente en la rama más profunda izquierda con ~18.4% de reincidencia).

**Acción de negocio:** Dado que el objetivo es entender **¿Qué hace que una persona repita el mismo oficio o lo ejerza por primera vez?**, la respuesta basada en este modelo es:

> *"Según nuestro árbol de decisión, los grupos ISCO con mayor propensión a reincidir son **5 (Service and sales workers)**, seguido de **3 (Technicians and associate professionals)**, **9 (Elementary occupations)** y **2 (Professionals)**. Con `max_depth=4` y usando únicamente `isco_mayor`, el modelo segmenta la población pero no discrimina individualmente mejor que predecir 'primera vez' para todos (accuracy ~71.8%, igual al baseline), ya que ninguna hoja supera el 50% de reincidencia. Por consiguiente, **el valor práctico es la segmentación por grupo ISCO para focalizar acciones de análisis/seguimiento**, más que un clasificador para predecir caso a caso."*

**Lecciones aplicadas:**
1. **Evitar fuga de información:** `veces_ese_oficio` solo para crear `y`, nunca en `X`.
2. **Interpretabilidad primero:** Elegimos `max_depth=4` por legibilidad (coherente con sesión 7).
3. **Medir correctamente:** Siempre comparar con baseline + matriz de confusión + `classification_report`.
4. **Explicar con datos:** Usar las **4 primeras preguntas tal cual salen de `export_text`**, con conteos, tasas, lift y justificación.
5. **Entender las limitaciones:** Accuracy global engañoso cuando hay desbalance moderado; lo relevante aquí es **¿qué grupos se diferencian?**

---

## 7. Archivos generados

| Archivo | Descripción |
|---|---|
| `arbol_fuga_comparacion_depth.csv` / `arbol_fuga_comparacion_depth_completo.csv` | Comparación de profundidades (train/test/n_leaves) |
| `arbol_fuga.png` / `arbol_fuga_completo.png` | Visualización del árbol con `plot_tree` |
| `arbol_fuga_export.txt` / `arbol_fuga_export_completo.txt` | Reglas en texto con `export_text` |
| `arbol_fuga_feature_importances.csv` | Importancias de variables |
| `arbol_fuga_metricas.csv` | Comparación baseline vs árbol |
| `arbol_fuga_4preguntas_completo.csv` | Tabla detallada de las 4 primeras preguntas con lift |
| `train_arbol.py`, `completar_arbol.py`, `generar_tabla_4preguntas.py`, `debug_arbol*.py` | Scripts utilizados para reproducir el análisis |
