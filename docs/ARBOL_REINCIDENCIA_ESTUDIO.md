# Árbol de decisión para reincidencia por oficio

**Minería de Datos · UNIMINUTO Ibagué · Sesión 7 · 2026-2**

> **Entregable ejecutable:** `notebooks/6.0_arbol_decision.ipynb` (12 celdas, corre completo).
> **Reglas de negocio:** `reports/arbol_reincidencia/reglas/reglas_negocio.md`.
> Este documento es el sustento conceptual y metodológico; el cuaderno es la evidencia.

---

## 1. La pregunta y la idea detrás

### 1.1 La pregunta

> **¿El perfil de competencias que exige un oficio separa a las personas que repiten ese oficio de las que lo ejercen por primera vez?**

### 1.2 La idea de la pregunta

El dataset no dice si alguien "renunció" ni si "fue despedido". Lo que sí dice es cuántas veces la misma persona (`resume_id`) ha ejercido el mismo oficio (`occupation_code`). Ese contador, `veces_ese_oficio`, permite construir una pregunta que sí es observable:

- `veces_ese_oficio == 1` → es la **primera vez** que esta persona ejerce ese oficio.
- `veces_ese_oficio >= 2` → **volvió** a ese oficio. A eso se le llama aquí **reincidencia**.

La intuición de fondo: si un oficio se repite mucho, no es un accidente individual — es una **característica del oficio**. Y si es del oficio, debería poder describirse con las variables que describen el oficio. Las competencias ESCO son exactamente eso: el catálogo de lo que un oficio exige.

Por eso la pregunta no es *"¿quién va a repetir?"* sino *"¿qué tipo de oficio se repite?"*. Es una pregunta descriptiva, no predictiva, y el árbol es el instrumento adecuado porque su salida es **legible**: un conjunto de condiciones en lenguaje natural.

### 1.3 Unidad de análisis y etiqueta

| Elemento | Definición |
|---|---|
| Unidad | Un registro de empleo (una experiencia laboral) |
| `y` | `1 = reincide` (`veces_ese_oficio >= 2`) · `0 = primera vez` |
| Filas para modelar | **348.263** |
| Tasa base | **30,51%** |

### 1.4 Por qué se excluyen 28.304 filas

`veces_ese_oficio` es nulo en **28.304 filas**. No es un dato faltante cualquiera: son exactamente las filas con `saber_skills == 'no_clasificado'`, es decir, ocupaciones que **no se pudieron estandarizar contra ESCO**. En esas filas no hay oficio, así que la pregunta *"¿repitió este oficio?"* no tiene respuesta.

Etiquetarlas como `0` (primera vez) inventaría el dato y sesgaría el modelo hacia la clase mayoritaria: la tasa base bajaría de 30,51% a 28,22% sin ninguna razón sustantiva. **Se excluyen y se documenta.**

### 1.5 Lo que esta pregunta no es

- **No es causal.** Que un oficio con más competencias se repita más no significa que las competencias sean la causa.
- **No es individual.** Las competencias son una propiedad del oficio: todos los meseros comparten el mismo `n_skills_essential`. El modelo describe oficios, no personas.
- **No sustituye la pregunta del proyecto** (transiciones y permanencias por persona). Es un lente descriptivo complementario.

---

## 2. Los predictores: tres formas de describir un oficio

Un árbol solo puede partir por lo que se le entrega. Se probaron **tres bloques de `X`**, con la misma `y`, el mismo split y la misma profundidad, para que la única diferencia fuera el predictor:

| Bloque | Pregunta que encarna | Variables |
|---|---|---|
| **ISCO** | ¿**Qué** es el oficio? | 9 dummies del gran grupo ocupacional |
| **Nivel educativo** | ¿**Quién** lo ejerce? | `nivel_ordinal` (1 Secundaria … 4 PhD) + bandera de "no reportado" |
| **Competencias** | ¿Qué **exige** el oficio? | `n_skills_essential`, `n_skills_competence`, `n_skills_knowledge` |

**Por qué solo conteos y no las listas de texto.** Las columnas `skills` y `knowledge` son texto separado por `|`. Usarlas exigiría un one-hot de miles de columnas: ilegible e inviable para un árbol de 3 niveles. Los conteos resumen lo mismo en tres números.

**Variable prohibida: `veces_ese_oficio`.** Es la que construye `y`. Si entra en `X`, el árbol copia la respuesta (fuga de información).

**Aviso de redundancia.** `n_skills_essential ≈ n_skills_competence + n_skills_knowledge` y `corr(essential, competence) = 0,95`. No son tres variables independientes: son el total y dos pedazos del total. Eso explica que el árbol pregunte varias veces por umbrales parecidos.

---

## 3. Flujo aplicado (los 8 pasos de la sesión)

| Paso | Acción |
|---|---|
| 1 | Cargar el CSV y **excluir** las filas sin oficio estandarizado |
| 2 | Crear `y = (veces_ese_oficio >= 2)` |
| 3 | Construir `X` (bloque elegido) |
| 4 | `train_test_split(test_size=0.25, random_state=42, stratify=y)` **antes** del `fit` |
| 5 | Comparar `max_depth ∈ [2, 3, 4, 5, 8, None]` con train, test, hojas y brecha |
| 6 | Entrenar el árbol final con `max_depth=3` |
| 7 | `plot_tree(...)` y `export_text(...)` |
| 8 | Escribir **2 reglas de negocio** a partir de las hojas |

---

## 4. Resultados

### 4.1 Comparación de bloques

Mismo split, `max_depth=3`:

| Bloque | accuracy test | f1 clase 1 | recall clase 1 | hojas | hojas "reincide" | tasa máxima | lift |
|---|---|---|---|---|---|---|---|
| baseline (`most_frequent`) | 0,6949 | 0,000 | 0,000 | 1 | 0 | — | — |
| ISCO | 0,6949 | 0,000 | 0,000 | 4 | **0** | 34,89% | 1,14 |
| nivel educativo | 0,6949 | 0,000 | 0,000 | 5 | **0** | 31,81% | 1,04 |
| **competencias** | **0,7015** | **0,196** | **0,119** | 8 | **2** | **63,10%** | **2,07** |

**Lectura:** solo el bloque de competencias produce hojas con mayoría de "reincide". Los otros dos **segmentan** (mueven la tasa) pero **no alcanzan a predecir**, porque ninguna de sus hojas supera el 50%.

### 4.2 Profundidades: no hay sobreajuste

| max_depth | isco train | isco test | nivel train | nivel test | skills train | skills test | skills hojas |
|---|---|---|---|---|---|---|---|
| 2 | 0,6949 | 0,6949 | 0,6949 | 0,6949 | 0,6949 | 0,6949 | 4 |
| **3** | 0,6949 | 0,6949 | 0,6949 | 0,6949 | **0,7010** | **0,7015** | **8** |
| 4 | 0,6949 | 0,6949 | 0,6949 | 0,6949 | 0,7013 | 0,7018 | 15 |
| 5 | 0,6949 | 0,6949 | 0,6949 | 0,6949 | 0,7015 | 0,7021 | 27 |
| 8 | 0,6949 | 0,6949 | 0,6949 | 0,6949 | 0,7045 | 0,7050 | 112 |
| None | 0,6949 | 0,6949 | 0,6949 | 0,6949 | 0,7068 | 0,7068 | 554 |

- **La brecha train–test es cero** (o negativa en milésimas). No hay sobreajuste en ningún bloque ni en ninguna profundidad.
- El techo está en el dato, no en el modelo: de `depth=3` a `None` se ganan **+0,5 pp** y se pierden 546 hojas de legibilidad.
- ISCO y nivel educativo se agotan solos: a partir de `depth=3` el accuracy no se mueve, porque no queda información nueva que partir.

### 4.3 Árbol ISCO

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

**Las 4 primeras preguntas** (train, base 30,51%):

| # | Pregunta | Izq (NO) | Tasa izq | Der (SÍ) | Tasa der | Lift der |
|---|---|---|---|---|---|---|
| 1 | ¿Grupo ISCO 5? | 203.927 | 29,28% | 57.270 | **34,89%** | 1,144 |
| 2 | ¿Grupo ISCO 3? | 153.922 | 27,91% | 50.005 | **33,49%** | 1,098 |
| 3 | ¿Grupo ISCO 9? | 118.250 | 26,30% | 35.672 | **33,25%** | 1,090 |
| 4 | ¿Grupo ISCO 2? | 71.915 | 23,40% | 46.335 | **30,80%** | 1,010 |

Los grupos **5, 3, 9 y 2** elevan la tasa respecto al global, y en ese orden aparecen los splits. Importancias: `isco_5` 0,361 · `isco_9` 0,339 · `isco_3` 0,301.

**Pero las 4 hojas terminan en clase 0.** El árbol encontró señal real (lift 1,14) y aun así no logra que ninguna rama cruce el 50%. Consecuencia: predice exactamente lo mismo que el baseline y **no permite escribir una regla accionable**. Este es el hallazgo metodológico: *saber que alguien es mesero no alcanza para decir que va a repetir*.

### 4.4 Árbol de nivel educativo

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

| # | Pregunta | Izq | Tasa izq | Der | Tasa der |
|---|---|---|---|---|---|
| 1 | ¿Nivel hasta Bachelor? | 222.217 | 31,45% | 38.980 | **25,13%** |
| 2 | ¿Nivel hasta Secundaria? | 103.169 | 31,81% | 119.048 | 31,14% |
| 3 | ¿Nivel no reportado? | 89.304 | 31,17% | 29.744 | 31,05% |
| 4 | ¿Nivel hasta Master? | 37.884 | 25,18% | 1.096 | 23,36% |

**El nivel educativo casi no separa.** Todas las ramas quedan entre 23% y 32%, es decir, pegadas a la base. La única señal es débil y en dirección interesante: **a mayor nivel educativo, menor repetición** (Master/PhD 25,1% vs Secundaria 31,8%), pero la diferencia no alcanza para cambiar la predicción. **Ninguna de sus 5 hojas predice "reincide".**

> Nota técnica: `nivel_ordinal` tiene nulos ("no reportado"), y sklearn los envía por una rama del árbol. Por eso la primera pregunta agrupa "hasta Bachelor" **incluyendo** los no reportados; el árbol los separa en el tercer nivel. La tabla se calculó con `decision_path`, no repitiendo la comparación `<=`, para no falsear los tamaños.

### 4.5 Árbol de competencias (el elegido)

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

**Importancias:** `n_skills_competence` 0,550 · `n_skills_essential` 0,236 · `n_skills_knowledge` 0,214.

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

Solo **2 de 8 hojas** predicen "reincide". Ahí está el fenómeno concentrado.

---

## 5. Las 2 reglas de negocio

**Regla 1 · Oficios de perfil práctico con algo de teoría**
`competence > 18,5` ∧ `essential <= 20,5` ∧ `knowledge > 0,5`
→ 14.424 registros · **53,3%** reincide · **+22,8 pp** · lift **1,75**

**Regla 2 · Oficios altamente especializados**
`competence > 18,5` ∧ `essential > 20,5` ∧ `knowledge > 25,5`
→ 2.520 registros · **63,1%** reincide · **+32,6 pp** · lift **2,07**

Redacción completa, acciones y advertencias: `reports/arbol_reincidencia/reglas/reglas_negocio.md`.

---

## 6. Por qué `max_depth=3`

1. **No hay sobreajuste que impida bajarla**: train ≈ test en todas las profundidades, así que la profundidad no se elige por accuracy.
2. **Legibilidad**: 8 hojas caben en una diapositiva; 554 no.
3. **Rendimiento**: de 3 a `None` se ganan +0,5 pp. No compensa.
4. **Coherencia con la consigna**, que pide `3` y `None`. `None` se reporta igual, como techo del dato.

---

## 7. Limitaciones

1. **No es causal.** Asociación, no causa.
2. **Clasifica oficios, no personas.**
3. **Circularidad parcial:** las competencias se pegan al `occupation_code` y la etiqueta se construye repitiendo ese mismo `occupation_code`. El árbol describe el oficio desde otro ángulo; no descubre un factor nuevo.
4. **Accuracy engañosa:** con 30,5% de positivos, 69,5% se logra sin identificar a nadie. Por eso se reportan tasa, delta y lift por hoja.
5. **Confusor probable:** los oficios con más competencias en ESCO suelen ser oficios amplios y comunes, con alta rotación por tamaño, no por competencias.
6. **El árbol no es un buen clasificador:** detecta solo 11,9% de los reincidentes (`recall`). Su valor es **descriptivo y de priorización**.

---

## 8. Conclusión

- El **nivel educativo** y el **gran grupo ISCO** mueven la tasa de reincidencia pero **no producen ninguna regla accionable**: todas sus hojas quedan por debajo del 50%.
- El **perfil de competencias del oficio** sí: **70,1% de accuracy** (vs 69,5% del baseline) y **2 hojas con mayoría de "reincide"**.
- Las 2 reglas concentran el hallazgo: oficios de perfil **práctico con algo de teoría** (53,3%) y oficios **altamente especializados** (63,1%) repiten muy por encima del **30,5%** general.
- **El límite no es el modelo, es el dato.** Eso se demuestra con la tabla de profundidades, no se afirma.

---

## 9. Archivos y cómo se reproduce

```
reports/arbol_reincidencia/
├── figuras/
│   ├── arbol_isco.png          árbol ISCO (depth 3)
│   ├── arbol_nivel.png         árbol de nivel educativo (depth 3)
│   └── arbol_skills.png        árbol de competencias (depth 3)
├── tablas/
│   ├── comparacion_bloques.csv     los 3 bloques vs baseline
│   ├── {isco,nivel,skills}_metricas.csv
│   ├── {isco,nivel,skills}_profundidades.csv
│   ├── {isco,nivel,skills}_importancias.csv
│   ├── {isco,nivel,skills}_preguntas.csv   las 4 primeras preguntas con lift
│   └── skills_hojas.csv            las 8 hojas con n, tasa, delta y lift
└── reglas/
    ├── reglas_negocio.md       LAS 2 REGLAS redactadas
    ├── isco_export.txt         export_text
    ├── nivel_export.txt
    └── skills_export.txt
```

```powershell
# 1. Los tres bloques
python scripts/arbol_reincidencia/train_arbol_bloques.py --bloque todos

# 2. El cuaderno entregable (árbol final + 2 reglas + hojas)
jupyter nbconvert --to notebook --execute --inplace notebooks/6.0_arbol_decision.ipynb
```

| Archivo | Rol |
|---|---|
| `notebooks/6.0_arbol_decision.ipynb` | **entregable de la Sesión 7** |
| `scripts/arbol_reincidencia/train_arbol_bloques.py` | genera los 3 bloques y la comparación |
| `reports/arbol_reincidencia/reglas/reglas_negocio.md` | las 2 reglas |
