# Qué pregunta responde cada árbol · Sesión 7

**Minería de Datos · UNIMINUTO Ibagué · 2026-2**

> **Documento de sustentación.** Responde, árbol por árbol: **bajo qué pregunta de decisión va**, **qué variables usa**, **cómo parte el árbol** (`export_text`), **qué pasa en cada profundidad** y **qué se esperaba contra qué salió**.
>
> **Evidencia ejecutable:** `notebooks/6.0_arbol_decision.ipynb` (11 celdas de código, 0 errores).
> **Reglas de negocio:** `reports/arbol_reincidencia/reglas/reglas_negocio.md`.
> **Estudio completo:** `docs/ARBOL_REINCIDENCIA_ESTUDIO.md`.
> Este documento no repite el estudio: ordena **la pregunta → el árbol → la profundidad → el resultado esperado**.

---

## 1 · La pregunta de decisión de todo el ejercicio

> **¿El perfil de un oficio separa a las personas que lo repiten de las que lo ejercen por primera vez?**

Se responde con **tres árboles**, no con uno. Cada árbol cambia **solo `X`**; `y`, el split y la profundidad son idénticos. Así la única diferencia entre los tres es *qué se sabe del oficio*:

| Árbol | La pregunta que encarna | `X` | Qué representa |
|---|---|---|---|
| **1 · ISCO** | ¿**Qué** es el oficio? | 9 dummies del gran grupo ISCO | La clasificación ocupacional oficial |
| **2 · Nivel educativo** | ¿**Quién** ejerce el oficio? | `nivel_ordinal` + `nivel_no_reportado` | El capital académico de quien lo ejerce |
| **3 · Competencias** | ¿Qué **exige** el oficio? | `n_skills_essential`, `n_skills_competence`, `n_skills_knowledge` | El catálogo ESCO del oficio |

**La `y` es la misma en los tres:** `1 = reincide` (`veces_ese_oficio >= 2`), `0 = primera vez`.

| Elemento común | Valor |
|---|---|
| Filas | **348.263** (se excluyen 28.304 sin oficio estandarizado) |
| Tasa base | **30,51%** |
| Split | 75% train (261.197) / 25% test (87.066), `stratify=y`, `random_state=42` |
| Profundidad del árbol entregado | `max_depth=3` |
| Baseline | `DummyClassifier(strategy="most_frequent")` = 0,6949 |

**Regla de oro del ejercicio:** el árbol solo puede partir por lo que se le entrega. Si el bloque no contiene la señal, ninguna profundidad la inventa. Eso es justamente lo que se pone a prueba.

---

## 2 · Las profundidades: qué se compara y por qué

La consigna pide **dos árboles** (`max_depth=3` y `max_depth=None`). Aquí se reportan **seis**, porque la tabla de profundidades es la que demuestra *dónde* está el techo del dato:

| `max_depth` | Papel en el ejercicio |
|---|---|
| **3** | **El árbol entregado.** 8 hojas, legible en una diapositiva |
| **None** | **El techo.** Sin límite, para ver si el dato da para más |
| 2 | Piso: ¿basta con dos preguntas? |
| 4 | Un nivel más: ¿aparece señal nueva? |
| 5 | Punto medio |
| 8 | Casi sin límite, pero aún con topes |

**Qué se mira en cada fila:** `train_acc`, `test_acc`, `n_hojas` y **`brecha_train_test`**. La brecha es la firma del sobreajuste: si train sube y test baja, el árbol empezó a memorizar.

> **Los conteos son enteros.** Un umbral `18.5` en el `export_text` significa **"19 o más"**.

---

## 3 · Árbol 1 · ISCO

### 3.1 La pregunta

> **¿Saber en qué gran grupo ocupacional está el oficio alcanza para anticipar si se repite?**

Es la pregunta más "oficial": usa la clasificación ISCO que ya trae el dataset, sin construir nada nuevo. Si el fenómeno fuera del grupo ocupacional, este árbol debería encontrarlo.

### 3.2 El árbol (`reglas/isco_export.txt`)

```text
|--- isco_5 <= 0.50
|   |--- isco_3 <= 0.50
|   |   |--- isco_9 <= 0.50
|   |   |   |--- class: 0
|   |   |--- isco_9 >  0.50
|   |   |   |--- class: 0
|   |--- isco_3 >  0.50
|   |   |--- class: 0
|--- isco_5 >  0.50
|   |--- class: 0
```

### 3.3 Las 4 primeras preguntas

| # | Pregunta | Izq (NO) | Tasa izq | Der (SÍ) | Tasa der | Lift der |
|---|---|---|---|---|---|---|
| 1 | ¿Grupo ISCO 5? (servicios y ventas) | 203.927 | 29,28% | 57.270 | **34,89%** | 1,144 |
| 2 | ¿Grupo ISCO 3? (técnicos) | 153.922 | 27,91% | 50.005 | **33,49%** | 1,098 |
| 3 | ¿Grupo ISCO 9? (ocupaciones elementales) | 118.250 | 26,30% | 35.672 | **33,25%** | 1,090 |
| 4 | ¿Grupo ISCO 2? (profesionales) | 71.915 | 23,40% | 46.335 | **30,80%** | 1,010 |

**Importancias:** `isco_5` 0,361 · `isco_9` 0,339 · `isco_3` 0,301. Los demás grupos no aportan.

### 3.4 Profundidades

| `max_depth` | train_acc | test_acc | hojas | brecha |
|---|---|---|---|---|
| 2 | 0,6949 | 0,6949 | 3 | 0,0000 |
| **3** | **0,6949** | **0,6949** | **4** | 0,0000 |
| 4 | 0,6949 | 0,6949 | 5 | 0,0000 |
| 5 | 0,6949 | 0,6949 | 6 | 0,0000 |
| 8 | 0,6949 | 0,6949 | 9 | 0,0000 |
| None | 0,6949 | 0,6949 | 9 | 0,0000 |

### 3.5 Qué se esperaba vs qué salió

| | Esperado | Obtenido |
|---|---|---|
| Accuracy | Que superara al baseline | **0,6949 = baseline**, no lo supera |
| Hojas | Varias ramas | 4 hojas |
| Hojas "reincide" | Alguna | **0** |
| Tasa máxima | > 50% | 34,89% (lift 1,14) |
| Conclusión | El grupo ocupacional explica la reincidencia | **Segmenta, no predice** |

**Lectura:** el árbol sí encuentra señal real — los grupos **5, 3, 9 y 2** elevan la tasa en ese orden — pero **ninguna hoja cruza el 50%**. Consecuencia: predice lo mismo que decir "primera vez" y **no permite escribir una regla accionable**. Saber que alguien es mesero no alcanza para decir que va a repetir.

---

## 4 · Árbol 2 · Nivel educativo

### 4.1 La pregunta

> **¿El nivel académico de quien ejerce el oficio separa a los que repiten de los que no?**

Es la pregunta del lado de la persona. Si la reincidencia fuera un asunto de formación, este árbol debería mostrarlo.

### 4.2 El árbol (`reglas/nivel_export.txt`)

```text
|--- nivel_ordinal <= 2.50
|   |--- nivel_ordinal <= 1.50
|   |   |--- class: 0
|   |--- nivel_ordinal >  1.50
|   |   |--- nivel_no_reportado <= 0.50
|   |   |   |--- class: 0
|   |   |--- nivel_no_reportado >  0.50
|   |   |   |--- class: 0
|--- nivel_ordinal >  2.50
|   |--- nivel_ordinal <= 3.50
|   |   |--- class: 0
|   |--- nivel_ordinal >  3.50
|   |   |--- class: 0
```

`nivel_ordinal`: 1 = Secundaria, 2 = Bachelor, 3 = Master, 4 = PhD. "No reportado" es `NaN` + bandera, **no** un cero.

### 4.3 Las 4 primeras preguntas

| # | Pregunta | Izq | Tasa izq | Der | Tasa der |
|---|---|---|---|---|---|
| 1 | ¿Nivel hasta Bachelor? | 222.217 | 31,45% | 38.980 | **25,13%** |
| 2 | ¿Nivel hasta Secundaria? | 103.169 | 31,81% | 119.048 | 31,14% |
| 3 | ¿Nivel no reportado? | 89.304 | 31,17% | 29.744 | 31,05% |
| 4 | ¿Nivel hasta Master? | 37.884 | 25,18% | 1.096 | 23,36% |

**Importancias:** `nivel_ordinal` 0,9998 · `nivel_no_reportado` 0,0002.

> **Nota técnica:** `nivel_ordinal` tiene nulos y sklearn los envía por la **rama izquierda**. Por eso la pregunta 1 agrupa "hasta Bachelor" **incluyendo** los no reportados, y el árbol los separa en el nivel 3. La tabla se calculó con `decision_path`, no repitiendo `<=`, para no falsear los tamaños.

### 4.4 Profundidades

| `max_depth` | train_acc | test_acc | hojas | brecha |
|---|---|---|---|---|
| 2 | 0,6949 | 0,6949 | 4 | 0,0000 |
| **3** | **0,6949** | **0,6949** | **5** | 0,0000 |
| 4 | 0,6949 | 0,6949 | 5 | 0,0000 |
| 5 | 0,6949 | 0,6949 | 5 | 0,0000 |
| 8 | 0,6949 | 0,6949 | 5 | 0,0000 |
| None | 0,6949 | 0,6949 | 5 | 0,0000 |

### 4.5 Qué se esperaba vs qué salió

| | Esperado | Obtenido |
|---|---|---|
| Accuracy | Que superara al baseline | **0,6949 = baseline** |
| Hojas | Varias | 5 hojas, y **se agota en depth 3** (4→None dan lo mismo) |
| Hojas "reincide" | Alguna | **0** |
| Tasa máxima | > 50% | 31,81% (lift 1,04) |
| Conclusión | El nivel académico explica la reincidencia | **Casi no separa** |

**Lectura:** todas las ramas quedan entre **23% y 32%**, pegadas a la base de 30,5%. La única señal es débil y va en dirección interesante: **a más estudios, menos repetición** (Master/PhD 25,1% vs Secundaria 31,8%), pero no alcanza para cambiar la predicción. Igual que ISCO: **sirve para segmentar, no para escribir reglas**.

---

## 5 · Árbol 3 · Competencias (el entregado)

### 5.1 La pregunta

> **¿Lo que el oficio *exige* —su perfil de competencias ESCO— separa mejor que el grupo ocupacional y que el nivel académico?**

Es la pregunta del lado del oficio, pero desde su contenido y no desde su etiqueta. Aquí el árbol no pregunta "¿es mesero?", pregunta "¿cuántas competencias de saber hacer exige?".

### 5.2 El árbol (`reglas/skills_export.txt`)

```text
|--- n_skills_competence <= 18.50
|   |--- n_skills_essential <= 10.50
|   |   |--- n_skills_essential <= 9.50
|   |   |   |--- class: 0
|   |   |--- n_skills_essential >  9.50
|   |   |   |--- class: 0
|   |--- n_skills_essential >  10.50
|   |   |--- n_skills_competence <= 13.50
|   |   |   |--- class: 0
|   |   |--- n_skills_competence >  13.50
|   |   |   |--- class: 0
|--- n_skills_competence >  18.50
|   |--- n_skills_essential <= 20.50
|   |   |--- n_skills_knowledge <= 0.50
|   |   |   |--- class: 0
|   |   |--- n_skills_knowledge >  0.50
|   |   |   |--- class: 1
|   |--- n_skills_essential >  20.50
|   |   |--- n_skills_knowledge <= 25.50
|   |   |   |--- class: 0
|   |   |--- n_skills_knowledge >  25.50
|   |   |   |--- class: 1
```

### 5.3 Las 4 primeras preguntas

| # | Pregunta | Izq | Tasa izq | Der | Tasa der | Lift der |
|---|---|---|---|---|---|---|
| 1 | ¿`competence` ≤ 18,5? | 136.501 | 24,77% | 124.696 | **36,79%** | 1,206 |
| 2 | ¿`essential` ≤ 10,5? | 29.811 | 28,90% | 106.690 | 23,62% | 0,774 |
| 3 | ¿`essential` ≤ 9,5? | 13.103 | 21,60% | 16.708 | **34,63%** | 1,135 |
| 4 | ¿`competence` ≤ 13,5? | 54.260 | 20,83% | 52.430 | 26,50% | 0,869 |

**Importancias:** `competence` **0,550** · `essential` **0,236** · `knowledge` **0,214**.

**Las 8 hojas:**

| Hoja | Registros (train) | Reincide | vs base | Lift | Predice |
|---|---|---|---|---|---|
| 14 | 2.520 | **63,1%** | +32,6 pp | 2,07 | Reincide |
| 11 | 14.424 | **53,3%** | +22,8 pp | 1,75 | Reincide |
| 4 | 16.708 | 34,6% | +4,1 pp | 1,14 | Primera vez |
| 13 | 100.846 | 34,0% | +3,5 pp | 1,12 | Primera vez |
| 10 | 6.906 | 32,9% | +2,4 pp | 1,08 | Primera vez |
| 7 | 52.430 | 26,5% | −4,0 pp | 0,87 | Primera vez |
| 3 | 13.103 | 21,6% | −8,9 pp | 0,71 | Primera vez |
| 6 | 54.260 | 20,8% | −9,7 pp | 0,69 | Primera vez |

### 5.4 Profundidades

| `max_depth` | train_acc | test_acc | hojas | brecha |
|---|---|---|---|---|
| 2 | 0,6949 | 0,6949 | 4 | 0,0000 |
| **3** | **0,7010** | **0,7015** | **8** | −0,0004 |
| 4 | 0,7013 | 0,7018 | 15 | −0,0005 |
| 5 | 0,7015 | 0,7021 | 27 | −0,0006 |
| 8 | 0,7045 | 0,7050 | 112 | −0,0005 |
| None | 0,7068 | 0,7068 | 554 | +0,0001 |

### 5.5 Qué se esperaba vs qué salió

| | Esperado | Obtenido |
|---|---|---|
| Accuracy | Superar el 0,6949 | **0,7015** (+0,66 pp) |
| Hojas | Varias | 8 hojas |
| Hojas "reincide" | Alguna | **2** (hojas 14 y 11) |
| Tasa máxima | > 50% | **63,1%** (lift 2,07) |
| Conclusión | El perfil de competencias separa | **Sí, y permite 2 reglas** |

**Lectura:** solo **2 de 8 hojas** predicen "reincide", y ahí está el hallazgo: el fenómeno **no está repartido**, está concentrado en dos tipos de perfil. Esa concentración es la que hace posible escribir reglas.

---

## 6 · El contraste que cierra el ejercicio

Mismo split, misma `max_depth=3`, misma `y`:

| Bloque | accuracy test | f1 clase 1 | hojas | hojas "reincide" | tasa máx | lift |
|---|---|---|---|---|---|---|
| baseline | 0,6949 | 0,000 | 1 | 0 | — | — |
| ISCO | 0,6949 | 0,000 | 4 | **0** | 34,89% | 1,14 |
| nivel educativo | 0,6949 | 0,000 | 5 | **0** | 31,81% | 1,04 |
| **competencias** | **0,7015** | **0,196** | 8 | **2** | **63,10%** | **2,07** |

**Lo que esto permite afirmar:** el **perfil de competencias del oficio** separa mejor que el gran grupo ISCO y que el nivel académico.
**Lo que NO permite afirmar:** que las competencias *causen* la reincidencia. Es una asociación descriptiva, no causal.

---

## 7 · Lo que se esperaba según la diapositiva vs lo que salió en el proyecto

Esto es lo que hay que decir en voz alta, porque es la única parte donde el proyecto **no se parece** a la demo.

| | Demo TelecomUNO (diapositivas 11 y 13) | Proyecto |
|---|---|---|
| Baseline | ~83,0% | 69,49% |
| `depth=3` train / test | 0,834 / 0,828 | 0,7010 / **0,7015** |
| `None` train / test | **1,000 / 0,727** | **0,7068 / 0,7068** |
| Brecha máxima train–test | **+27,3 pp** | **≈ 0,0 pp** |
| Ganancia vs baseline en test | **negativa** (−10 pp) | +0,66 pp |

### 7.1 El "momento ajá" no ocurre — y está bien

La diapositiva enseña: *mientras `train` sube, `test` baja; esa brecha es la firma del sobreajuste*. En el proyecto **train y test son idénticos en las seis profundidades**. El árbol sin límite no memoriza nada.

**Por qué:** el sobreajuste necesita **capacidad de memorizar**. Este `X` tiene **3 variables enteras** y el train tiene **261.197 filas**. Aunque el árbol crezca a **554 hojas**, cada hoja promedio queda con **~470 registros**: no hay nada que memorizar. La demo tenía **11 variables sobre 1.800 filas**: ahí sí cabía una ramita por cliente.

**Consecuencia metodológica:** la tabla de profundidades aquí **no sirve para "encontrar el punto dulce"** (no hay punto dulce que encontrar). Sirve para dos cosas:

1. **Descartar el sobreajuste como problema** del modelo.
2. **Justificar `max_depth=3` por legibilidad**, no por accuracy: de 3 a `None` se ganan **+0,5 pp** y se pierden **546 hojas**.

### 7.2 Qué se esperaba de cada árbol, en una línea

| Árbol | Expectativa razonable | Resultado |
|---|---|---|
| ISCO | Que el grupo ocupacional moviera la aguja | Mueve la tasa (34,9% máx) pero **no cruza el 50%** |
| Nivel | Que el nivel académico moviera la aguja | Casi no mueve nada (31,8% máx) |
| Competencias | Que el contenido del oficio separara | **Sí: 63,1% en 2 hojas y 0,7015 de accuracy** |

---

## 8 · Las reglas de decisión que quedan

Salen de las **2 hojas que predicen "reincide"**:

| Regla | Condición (del `export_text`) | n | Reincide | vs base | Lift |
|---|---|---|---|---|---|
| **1** | `competence > 18,5` ∧ `essential <= 20,5` ∧ `knowledge > 0,5` | 14.424 | **53,3%** | +22,8 pp | 1,75 |
| **2** | `competence > 18,5` ∧ `essential > 20,5` ∧ `knowledge > 25,5` | 2.520 | **63,1%** | +32,6 pp | 2,07 |

**En una frase:** los oficios de perfil **práctico con algo de teoría** repiten al 53,3%, y los **altamente especializados** al 63,1%, contra un **30,5%** general. Redacción, acciones y advertencias: `reports/arbol_reincidencia/reglas/reglas_negocio.md`.

**Lo que estas reglas NO dicen:** no son causales, no predicen personas (clasifican oficios), hay circularidad parcial (las competencias cuelgan del mismo `occupation_code` que construye `y`) y el accuracy global es engañoso con 30,5% de positivos.

---

## 9 · Cómo se reproduce

```powershell
# Los tres árboles: figuras, tablas, export_text y comparación
python scripts/arbol_reincidencia/train_arbol_bloques.py --bloque todos

# El cuaderno entregable (árbol final, 8 hojas y 2 reglas)
jupyter nbconvert --to notebook --execute --inplace notebooks/6.0_arbol_decision.ipynb
```

| Archivo | Contenido |
|---|---|
| `reports/arbol_reincidencia/reglas/{isco,nivel,skills}_export.txt` | el árbol en texto de cada bloque |
| `reports/arbol_reincidencia/tablas/{isco,nivel,skills}_preguntas.csv` | las 4 primeras preguntas con n, tasa y lift |
| `reports/arbol_reincidencia/tablas/{isco,nivel,skills}_profundidades.csv` | la tabla de profundidades |
| `reports/arbol_reincidencia/tablas/comparacion_bloques.csv` | los 3 bloques frente al baseline |
| `reports/arbol_reincidencia/tablas/skills_hojas.csv` | las 8 hojas del árbol entregado |
| `reports/arbol_reincidencia/figuras/arbol_{isco,nivel,skills}.png` | los árboles dibujados con `plot_tree` |
| `docs/ARBOL_REINCIDENCIA_ESTUDIO.md` | estudio completo con metodología y límites |
