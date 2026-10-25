# Reglas de negocio · Árbol de reincidencia por oficio

**Sesión 7 · Minería de Datos · UNIMINUTO Ibagué**

Este archivo contiene las **2 reglas accionables** que salen del árbol de decisión de competencias. Son las que se piden en el punto 7 de la lista de cotejo ("2 reglas en lenguaje de negocio").

---

## Contexto

| Elemento | Valor |
|---|---|
| Dataset | `data/03_processed/empleos_limpio_con_competencias.csv` |
| Filas usadas | **348.263** (se excluyen 28.304 sin oficio estandarizado) |
| Etiqueta | `1 = reincide` (`veces_ese_oficio >= 2`) · `0 = primera vez` |
| **Tasa base** | **30,51%** de los registros son una repetición |
| Modelo | `DecisionTreeClassifier(max_depth=3, random_state=42)` |
| Predictores | `n_skills_essential`, `n_skills_competence`, `n_skills_knowledge` |
| Split | 75% train (261.197) / 25% test (87.066), estratificado |
| Accuracy test | **0,7015** (baseline `most_frequent`: 0,6949) |

> Los conteos son enteros, así que un umbral de `18.5` significa **"19 o más"**.

---

## Regla 1 · Oficios de perfil práctico con algo de teoría

**Regla del árbol** (`reglas/skills_export.txt`):

```text
n_skills_competence > 18.5
  AND n_skills_essential <= 20.5
    AND n_skills_knowledge > 0.5
```

**En lenguaje de negocio:**

> Los oficios que exigen **más de 18 competencias de tipo *competencia*** (saber hacer), **hasta 20,5 competencias esenciales en total** y **al menos un saber teórico** (`knowledge >= 1`) concentran una reincidencia del **53,3%**.

| Métrica | Valor |
|---|---|
| Registros (train) | **14.424** |
| Tasa de reincidencia | **53,3%** |
| Diferencia vs base | **+22,8 pp** |
| Lift | **1,75×** |

**A quién se le asigna:** al área de **formación y certificación**, para los 14.424 registros de este perfil.

**Qué se le asigna:** un programa de **certificación de saberes previos + ruta de ascenso** dentro del mismo oficio. Si 1 de cada 2 ya volvió, la permanencia es estructural: el esfuerzo rinde más certificando lo que la persona ya sabe que captándola de nuevo.

**Qué NO se le asigna:** una campaña de atracción. Aquí no falta gente; falta reconocer la que ya está.

---

## Regla 2 · Oficios altamente especializados

**Regla del árbol:**

```text
n_skills_competence > 18.5
  AND n_skills_essential > 20.5
    AND n_skills_knowledge > 25.5
```

**En lenguaje de negocio:**

> Los oficios que exigen **más de 18 competencias**, **más de 20,5 competencias esenciales** y **más de 25 saberes teóricos** concentran una reincidencia del **63,1%**.

| Métrica | Valor |
|---|---|
| Registros (train) | **2.520** |
| Tasa de reincidencia | **63,1%** |
| Diferencia vs base | **+32,6 pp** |
| Lift | **2,07×** |

**A quién se le asigna:** a la **mesa técnica educación–trabajo** (SENA, universidades, cajas de compensación), para los 2.520 registros de este perfil.

**Qué se le asigna:** **convenios de formación avanzada** atados al oficio (especializaciones, técnicos de nivel superior, actualización tecnológica), con seguimiento de trayectoria a 12 meses. Si 63 de cada 100 ya repitieron, el cuello de botella está en la **trayectoria**, no en la atracción: la persona ya está en el oficio y vuelve.

**Qué NO se le asigna:** bolsa de empleo ni convocatoria masiva. Es el grupo más pequeño (2.520 de 348.263) y el más extremo: lo que necesita es un instrumento de cualificación, no más candidatos.

---

## Las 8 hojas del árbol (para contexto)

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

Solo **2 de 8 hojas** predicen "reincide". Esa concentración es el hallazgo: el fenómeno no está repartido, está en dos tipos de perfil.

---

## Las 2 reglas no salen de los otros bloques

Se probaron los mismos 3 bloques con el mismo split y la misma profundidad:

| Bloque | accuracy test | hojas | hojas que predicen "reincide" |
|---|---|---|---|
| baseline | 0,6949 | 1 | 0 |
| ISCO (9 grupos) | 0,6949 | 4 | **0** |
| Nivel educativo | 0,6949 | 5 | **0** |
| **Competencias** | **0,7015** | 8 | **2** |

Ni el gran grupo ocupacional ni el nivel académico producen una sola hoja por encima del 50%, así que **no permiten escribir una regla accionable**. Por eso las 2 reglas se construyen sobre competencias.

---

## Lo que estas reglas NO dicen

1. **No son causales.** "Los oficios con más competencias se repiten más" es una asociación, no una causa.
2. **No predicen personas.** Las competencias son una propiedad del oficio, no de la persona: todos los meseros comparten el mismo `n_skills_essential`. El modelo clasifica **oficios**.
3. **Hay circularidad parcial.** Las competencias se pegan al `occupation_code` y la etiqueta se construye repitiendo ese mismo `occupation_code`. El árbol describe el oficio desde otro ángulo; no descubre un factor externo.
4. **El accuracy es engañoso por sí solo.** Con 30,5% de positivos, acertar 69,5% se logra sin identificar a nadie. Por eso cada regla se reporta con tasa, delta y lift.
5. **Posible confusor:** tamaño del oficio. Los oficios con más competencias en ESCO suelen ser oficios amplios y comunes, con alta entrada y salida de personas.

---

## Cómo se regeneran

```powershell
# Los tres bloques (figuras, tablas y export_text)
python scripts/arbol_reincidencia/train_arbol_bloques.py --bloque todos

# El árbol final con el detalle de hojas y las reglas redactadas
jupyter nbconvert --to notebook --execute --inplace notebooks/6.0_arbol_decision.ipynb
```

**Archivos relacionados**

| Archivo | Contenido |
|---|---|
| `reports/arbol_reincidencia/reglas/skills_export.txt` | reglas crudas del `export_text` |
| `reports/arbol_reincidencia/tablas/skills_hojas.csv` | las 8 hojas con n, tasa, delta y lift |
| `reports/arbol_reincidencia/tablas/comparacion_bloques.csv` | los 3 bloques frente al baseline |
| `reports/arbol_reincidencia/figuras/arbol_skills.png` | el árbol dibujado |
| `notebooks/6.0_arbol_decision.ipynb` | el cuaderno entregable (sección 9) |
