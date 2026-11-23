# MODEL_SELECTION.md · Marco de Decisión Basado en Evidencia para Modelos Supervisados (`6.0`–`7.2`) y Clustering (`8.0`–`8.1`) (`JobPath` · Fase 4 · Paso 1)

> **Propósito y Regla de Rigor:** Este documento establece primero los criterios en lenguaje sencillo, los pesos (`35 % / 25 % / 20 % / 10 % / 10 %`), los requisitos mínimos eliminatorios (*pass/fail*) y las rúbricas explícitas de 1 a 5 ancladas a puntos de corte numéricos **antes** de calcular cualquier puntaje, de modo que las reglas de evaluación no puedan parecer elegidas a posteriori para favorecer a un candidato. Toda cifra proviene de hechos verificados en [FACTS.md](file:///c:/Users/User/Documents/JobPath/MineriaProtect/docs/handoff/FACTS.md) (`F-001` a `F-050`) y de las tablas oficiales exportadas en `reports/`. Cuando un dato de tiempo, memoria o métrica no fue registrado en los cuadernos, se declara explícitamente como **`No calculado`** o **`NOT VERIFIED`** y jamás se estima ni se penaliza como cero.

---

## 1. Criterios en Lenguaje Sencillo, Pesos, Requisitos Mínimos y Rúbricas Pre-Definidas (Sección C — Definida Antes de Puntuar)

### 1.1 Los 5 Criterios de Evaluación y sus Pesos Aprobados

Se aplican por separado a la pregunta supervisada (`¿qué modelo elegimos para detectar quién repite oficio?`) y a la pregunta no supervisada (`¿qué método elegimos para agrupar trayectorias laborales?`):

| # | Criterio en Lenguaje Sencillo | Peso Base | Peso Renormalizado (Excluyendo Criterio 5 cuando no hay evidencia comparable) | Naturaleza de la Evidencia |
|---:|---|---:|---:|---|
| **`C1`** | **¿Qué tan seguido acierta en personas nuevas y qué tan bien detecta a quienes sí repiten (supervisado) / qué tan bien separados y con sentido quedan los grupos (clustering)?** | **`35 %`** | **`38.89 %`** (`35 / 90`) | **Datos medidos en `TEST`** (`ROC-AUC`, `Recall Clase 1`, `F1 Clase 1`, `Accuracy` vs. baseline trivial; en clustering: `Silhouette`, `Davies-Bouldin`, `Calinski-Harabasz` y perfiles nombrables). |
| **`C2`** | **¿Es práctico a nuestra escala (`~1.74 millones` de experiencias y `352,093` personas en memoria RAM y tiempo)?** | **`25 %`** | **`27.78 %`** (`25 / 90`) | **Datos medidos de tiempo y RAM** registrados en los cuadernos (`13f_comparacion_costos_computacionales.csv`, `8.0` y `8.1`). |
| **`C3`** | **¿Podemos explicar en una sola oración por qué tomó una decisión o formó un grupo?** | **`20 %`** | **`22.22 %`** (`20 / 90`) | **`Team judgment` (Juicio del equipo)** anclado a la estructura matemática del método (reglas de árbol, suma de probabilidades por oficio, distancia a 101 vecinos, centroide en unidades reales). |
| **`C4`** | **¿Se ajusta a lo que hace el proyecto (describir patrones observables sin afirmar causalidad)?** | **`10 %`** | **`11.11 %`** (`10 / 90`) | **`Team judgment` (Juicio del equipo)** sobre compatibilidad descriptiva. Si todos los candidatos cumplen por igual, **se declara empate explícito** sin inventar diferencias. |
| **`C5`** | **¿Es estable (da resultados similares si los datos o el tratamiento de valores extremos cambian ligeramente)?** | **`10 %`** | **Excluido (`0 %`) en el puntaje renormalizado** | **Evidencia de sensibilidad (`Versión A vs. Versión B` / semillas)** registrada en cada cuaderno. Cuando el protocolo de estabilidad no es homogéneo entre todos los candidatos, se marca **`"sin evidencia comparable"`**, no se penaliza, y se reporta el resultado **con y sin `C5`**. |

---

### 1.2 Paso 1 Eliminatorio: Requisitos Mínimos Obligatorios (`PASS / FAIL`)

Un candidato que falle cualquiera de estos tres requisitos queda **`DESCARTADO`** con su razón explícita y **no puede ganar acumulando puntos en otros criterios**:

1. **Cero columnas con fuga del objetivo (`PASS / FAIL`):** Debe excluir `veces_ese_oficio`, `veces_ese_oficio_rob`, `veces_ese_oficio_bin` y `n_returns` de la matriz de entrada $X$ (`F-028`, `F-029`).
2. **Superar al baseline trivial (`"siempre responde que NO repite"`) en la detección de personas que sí repiten en `TEST` (`PASS / FAIL`, solo supervisados):** En `Test` (`347,720` experiencias, `70,419` personas), el `29.97 %` de las experiencias son positivas (`reincide = 1`) y el `70.03 %` negativas (`F-017`). Un modelo que siempre dice *"no repite"* parece acertar el **`70.03 %`** de las veces, pero detecta al **`0.00 %`** de quienes sí repiten (`Recall = 0.0000`, `F1 = 0.0000`, `ROC-AUC = 0.5000`, `F-030`). Para aprobar, el modelo en su punto de operación debe detectar una fracción sustancial de repetidores (**`Test Recall Clase 1 >= 0.5000`**, es decir $\ge 50$ de cada $100$ que sí repiten) y superar en `Test ROC-AUC` (`> 0.5500`) al azar.
3. **Ejecutable a la escala completa del proyecto (`PASS / FAIL`):**
   - En **supervisados**, debe poder entrenarse sobre `Train` (`1,391,018` filas) y evaluar el `100 %` de `Test` (`347,720` filas) sin desbordar los `32 GB` de RAM física.
   - En **clustering**, debe poder asignar directamente a las **`352,093` personas del censo clasificado** (y `1,738,738` experiencias) sin desbordar los `32 GB` de RAM física ni depender de una aproximación externa sobre el `92.90 %` de la población (`F-041`).

---

### 1.3 Paso 2: Rúbricas Explícitas de Puntuación (`1` a `5`) Ancladas a Puntos de Corte

#### Rúbrica para Modelos Supervisados
- **Criterio 1 (`C1`, `35 %`) — Acierto y detección de quienes sí repiten en `TEST`:**  
  *Regla de equidad por métricas faltantes:* Como en `7.0` no se calcularon `PR-AUC` ni `Brier`, **`C1` se califica usando únicamente las métricas calculadas para TODOS los candidatos en `TEST`**: `Test ROC-AUC`, `Test F1 Clase 1` y `Test Recall Clase 1` (detección de repetidores):
  - **`5 puntos`:** `Test ROC-AUC >= 0.7200`, `Test F1 >= 0.5400` y detecta $\ge 70$ de cada $100$ repetidores (`Recall >= 0.7000`).
  - **`4 puntos`:** `Test ROC-AUC` entre `0.7000` y `0.7199`, `Test F1 >= 0.5300` y detecta $\ge 70$ de cada $100$ repetidores (`Recall >= 0.7000`) [o `Recall >= 0.6100` con `Precision >= 0.4600`].
  - **`3 puntos`:** `Test ROC-AUC` entre `0.6500` y `0.6999`, `Test F1 >= 0.5000` y `Recall >= 0.6000`.
  - **`2 puntos`:** `Test ROC-AUC` entre `0.6000` y `0.6499`, `Test F1 >= 0.4500` y `Recall >= 0.5000`.
  - **`1 punto`:** `Test ROC-AUC < 0.6000` o `Test F1 < 0.4500`.
- **Criterio 2 (`C2`, `25 %`) — Practicidad a escala (`1.39M` Train / `347.7k` Test en tiempo y RAM registrados):**
  - **`5 puntos`:** Entrenamiento (`fit`) + predicción completa en `Test` (`347,720` filas) en **`< 5 segundos` totales** y matriz de entrenamiento en RAM **`< 150 MB`**.
  - **`4 puntos`:** Entrenamiento + predicción en `Test` entre **`5 y 30 segundos`** y RAM `< 500 MB`.
  - **`3 puntos`:** Entrenamiento + predicción en `Test` entre **`30 segundos y 5 minutos`** (`300 s`).
  - **`2 puntos`:** Entrenamiento + predicción en `Test` entre **`5 minutos y 1 hora`** (`3,600 s`).
  - **`1 punto`:** Predicción en `Test` **`> 1 hora`** (inviable para consulta interactiva o re-entrenamiento ágil sin indexación aproximada).
  - *Nota:* Si los tiempos o la RAM en el dataset completo no fueron registrados en el cuaderno (`NOT VERIFIED`), no se inventan.
- **Criterio 3 (`C3`, `20 %`, `Team judgment`) — Explicabilidad en una sola oración para no expertos:**
  - **`5 puntos`:** Regla lógica directa de hasta 4 pasos (`"si A y B, entonces..."`) leíble en un diagrama sin álgebra.
  - **`4 puntos`:** Suma transparente de probabilidades o pesos por cada oficio y característica (`"cada oficio tiene una tasa base y cada característica suma o resta puntos a favor de repetir"`).
  - **`3 puntos`:** Analogía intuitiva de vecindario (`"busca los 101 casos más parecidos"`), pero sin ecuación global ni regla explícita por variable en `2,978` dimensiones.
  - **`2 puntos`:** Ensamble de múltiples árboles (`Boosting`) donde la decisión final combina decenas de particiones sucesivas.
- **Criterio 4 (`C4`, `10 %`, `Team judgment`) — Ajuste al propósito descriptivo del proyecto (sin reclamos causales):**
  - **`5 puntos`:** Describe asociaciones y patrones empíricos observables en el historial laboral sin requerir supuestos causales. *(Empate previsto si todos los modelos se interpretan descriptivamente).*
- **Criterio 5 (`C5`, `10 %`) — Estabilidad ante variaciones de datos (`Versión A vs. B`):**
  - Se muestra primero como **`"sin evidencia comparable"`** (porque `7.0` y `7.1` midieron $|\Delta\text{ROC-AUC}|$ y $|\Delta\text{F1}|$ en el `100 %` de `Test`, mientras que `7.2` midió sensibilidad a `Versión B` y outliers solo sobre `KNN-D` en validación cruzada al `10 %`, no sobre `KNN-W` en `Test`).
  - Para la comparación **con `C5` incluido** (usando la mejor medición disponible en cada cuaderno): **`5 puntos`** si la variación $|\Delta\text{AUC}|$ o $|\Delta\text{PR-AUC}|$ entre Versión A y Versión B es `< 0.0030`; **`4 puntos`** entre `0.0030` y `0.0060`; **`3 puntos`** `> 0.0060`.

#### Rúbrica para Métodos de Clustering
- **Criterio 1 (`C1`, `35 %`) —Separación geométrica y grupos con nombres de perfil laboral con sentido:**
  - **`5 puntos`:** `Silhouette >= 0.2500`, `Davies-Bouldin < 1.50` y los $k^*$ grupos tienen perfiles claros y accionables.
  - **`4 puntos`:** `Silhouette` entre `0.1800` y `0.2499`, `Davies-Bouldin < 1.70`, `Calinski-Harabasz > 20,000` (sobre población completa) y los 4 grupos reciben nombres de perfil laboral claros y verificados post-hoc.
  - **`3 puntos`:** `Silhouette` entre `0.1100` y `0.1799` o `Davies-Bouldin` entre `1.70` y `2.00`, con 4 grupos interpretables pero frontera geométrica más difusa al escalar muestra.
- **Criterio 2 (`C2`, `25 %`) — Practicidad a escala (`352,093` personas y `1,738,738` experiencias en `32 GB` RAM):**
  - **`5 puntos`:** Escala linealmente $O(N\cdot k\cdot d)$, ajusta sobre el `100 %` de `Train` (`281,674` personas y `1,391,018` experiencias) en **`< 5 segundos`** y sin matriz $O(n^2)$ (matriz `V_PERSON` Train `float64` = `20.28 MB`; `25.35 MB` censo total).
  - **`2 puntos`:** Complejidad $O(n^2)$ que desborda la RAM en el censo completo (`317.36 GB` en `Train` / `495.88 GB` en `Total` / `7,739.72 GB` en `Experiencias`), pero puede ejecutarse sobre una submuestra estratificada de `n = 25,000` personas (`2.50 GB` matriz condensada, `~8.0 GB` pico Windows, `146.11 s`) y proyectarse por centroide.
- **Criterio 3 (`C3`, `20 %`, `Team judgment`) — Explicabilidad en una oración:**
  - **`5 puntos`:** Cada grupo se define por su *"retrato robot"* promedio en unidades originales (empleos, trimestres, competencias) y un árbol jerárquico (dendrograma) muestra visualmente por qué se cortó en $k^* = 4$.
  - **`4 puntos`:** Cada grupo se define exactamente por su *"retrato robot"* promedio en unidades originales (`diferencia 0.000000` entre centroide desescalado y media del grupo), aunque requiere elegir $k$ mediante curva de inercia/índices.
- **Criterio 4 (`C4`, `10 %`, `Team judgment`) — Ajuste al propósito descriptivo:**
  - **`5 puntos`:** Ambos métodos resumen tipologías descriptivas sin usar variables del target (`0` fuga) y sin afirmar causalidad (**empate `5 vs. 5`**).
- **Criterio 5 (`C5`, `10 %`) — Estabilidad:**
  - Mostrado como **`"sin evidencia comparable"`** en la tabla renormalizada (porque `8.0` evaluó `Versión B vs. A` sobre las `281,674` personas completas [`ARI = 0.8633`] y 5 semillas [`ARI = 0.8557`], mientras que `8.1` evaluó cambio de tamaño muestral de `n = 3,000` a `n = 25,000` [`ARI = 0.3582`]). En la tabla **con `C5` incluido**: **`5 puntos`** para `ARI >= 0.85` (`8.0`) y **`3 puntos`** para `ARI = 0.3582` al cambiar tamaño muestral (`8.1`).

---

## 2. Modelos Supervisados: Auditoría de Homogeneidad, Baseline Trivial y Comparación en `TEST` (Sección A)

### 2.1 ¿Qué es el Cuaderno `6.0_modelado_fase4_jobpath.ipynb`?

El cuaderno **`6.0` cumple un doble rol documentado (`DEC-10`, `F-029`, `F-030`)**:
1. **Infraestructura y protocolo experimental compartido para toda la Fase 4:** Ejecuta la ablación 5-fold CV agrupada por `resume_id` (`StratifiedGroupKFold(n_splits=5)`) que demuestra empíricamente la fuga del `100 %` si se incluyen `veces_ese_oficio_rob/bin` (`PR-AUC CV = 1.0000`), y fija el contrato sin fuga ni colinealidad extrema para los cuadernos `7.0`, `7.1` y `7.2`.
2. **Dos modelos de referencia obligatorios (`Techo Lineal` y `Boosting Denso`):**
   - **`Ref 3 · Regresión Logística Regularizada OHE` (`SGDClassifier(loss='log_loss', penalty='l2', class_weight='balanced')` sobre `2,981` columnas):** Establece el **techo lineal multivariado de referencia** (`Test ROC-AUC = 0.7133`, `PR-AUC = 0.5109`, `F1 = 0.5321`) contra el cual se miden `7.0`, `7.1` y `7.2`.
   - **`HistGradientBoostingClassifier` (`14` columnas densas, sin las `2,967` dummies de oficio):** Cuantifica cuánto rinde un ensamble no lineal cuando se le priva del código exacto de ocupación ESCO (`Test ROC-AUC = 0.6936`, `PR-AUC = 0.4951`, `F1 = 0.5151`).

---

### 2.2 Auditoría de Paridad (*Like-for-Like*): Target, Partición por Persona y Conjuntos de Variables ($X$)

- **Mismo Target (`reincide`) confirmado al `100 %` (`F-017`):** Todos los modelos (`6.0`, `7.0`, `7.1`, `7.2`) predicen exactamente la misma variable binaria `reincide = (veces_ese_oficio > 1)` (`417,471` positivos en `Train` = **`30.0119 %`**; `104,225` positivos en `Test` = **`29.9738 %`**).
- **Misma Partición `Train / Test` agrupada por persona confirmada al `100 %` (`F-017`, `F-046`):** Todos los modelos usan el mapa oficial `split_map_resume_id.csv` generado por `GroupShuffleSplit(80/20, seed=42)` sobre `resume_id`: **`281,674` personas (`1,391,018` experiencias) en `Train`** y **`70,419` personas (`347,720` experiencias) en `Test`**, con **`0` personas compartidas (`|Train ∩ Test| = 0`)**.
- **Exclusión de las columnas de fuga confirmada al `100 %` (`F-028`, `F-029`):** Tal como exige `README.md`, todos los modelos finales de `6.0`, `7.0`, `7.1` y `7.2` excluyeron `veces_ese_oficio_rob` y `veces_ese_oficio_bin` (así como `veces_ese_oficio` y `n_returns`).
- **ALERTA DE NO HOMOGENEIDAD EN VARIABLES (`Comparación no homogénea en variables` para `7.0`):**
  - La matriz exportada `X_train.csv` / `X_test.csv` en `3.0_transformacion.ipynb` (`F-016`) tiene **`2,985` columnas totales**, compuestas por **`2,967` dummies de ocupación ESCO (`occupation_code_*`)** más **`18` columnas densas** (`2,985 - 2,967 = 18`).
  - Sin embargo, **los árboles de decisión de `7.0` NO se entrenaron sobre las `2,981` columnas sin fuga ni sobre las `16` columnas densas limpias de `04_transformed`**. En su lugar, `7.0` construyó desde `03_processed` **tres árboles independientes por bloques temáticos de baja dimensión (`10`, `2` y `7` variables; `19` variables en total entre los tres bloques) SIN incluir las `2,967` dummies de `occupation_code` (`DEC-11`, `F-033` a `F-035`)**.
  - Por consiguiente, **la comparación entre `7.0` (que vio `2` a `10` variables sin el código de oficio ESCO) y `6.0 / 7.1 / 7.2` (que vieron `2,978` a `2,981` variables incluyendo las `2,967` dummies de oficio) NO es homogénea (*not like-for-like*) en información de entrada**.

#### Tabla 2.1 · Inventario Exacto de Variables ($X$) por Modelo Supervisado (`F-016`, `F-029`, `F-033`–`F-040`)

| Cuaderno y Modelo | Nº Exacto de Variables en $X$ | ¿Incluye las `2,967` Dummies `occupation_code_*`? | ¿Excluye Fuga (`veces_ese_oficio_rob/bin`)? | Composición Exacta de las Variables Utilizadas | ¿Comparación Homogénea (*Like-for-Like*) con `NB-H` y `KNN-W`? |
|---|---:|---|---|---|---|
| **Matriz `X` bruta (`3.0` `04_transformed`)** | `2,985` | Sí (`2,967`) | **No** (contiene las 2 cols de fuga para auditoría de `5.0`) | `18` densas (`10` `RobustScaler` + `1` `MinMaxScaler` + `3` bins + `4` binarias `0/1`) + `2,967` dummies `occupation_code_*` (`2,985 - 2,967 = 18`). | No (prohibida para modelar sin filtrar las 2 cols de fuga). |
| **`6.0` · Logística Regularizada OHE (`Ref 3`)** | **`2,981`** | **Sí (`2,967`)** | **Sí (`0` fuga)** | `14` densas limpias (las `18` menos `2` de fuga y menos `2` colineales: `start_year_rob` [$r=1.000$] y `n_skills_competence_rob` [$r=0.952$]) + `2,967` dummies ESCO. | **Sí (100 % idéntica a `NB-H`)**. |
| **`6.0` · HistGradientBoosting** | **`14`** | **No (`0`)** | **Sí (`0` fuga)** | Solo las `14` variables densas limpias de `04_transformed`. | Solo homogénea contra modelos densos (`NB-G`, `KNN-D`). |
| **`7.0` · Árbol 1 · ISCO (`tree_1_isco`)** | **`10`** | **No (`0`)** | **Sí (`0` fuga)** | `10` dummies binarias de Gran Grupo ISCO a 1 dígito (`isco_major_0` a `isco_major_9`). | **NO (`Comparación no homogénea en variables`)**. |
| **`7.0` · Árbol 2 · Educación (`tree_2_education`)** | **`2`** | **No (`0`)** | **Sí (`0` fuga)** | `nivel_academico_ord` (`1..4`, `NaN` para no reportado) + bandera `educacion_no_reportada` (`0/1`). | **NO (`Comparación no homogénea en variables`)**. |
| **`7.0` · Árbol 3 · Competencias ESCO (`tree_3_skills`)** | **`7`** | **No (`0`)** | **Sí (`0` fuga)** | `3` conteos (`n_skills_essential`, `n_skills_competence`, `n_skills_knowledge`) + `4` razones/diferencias (`prop_competence_essential`, `prop_knowledge_essential`, `ratio_competence_knowledge`, `diff_competence_knowledge`). | **NO (`Comparación no homogénea en variables`)**. |
| **`7.1` · `NB-G` (`GaussianNB`)** | **`14`** | **No (`0`)** | **Sí (`0` fuga)** | Las `14` variables densas limpias de `04_transformed`. | Solo homogénea en bloque denso. |
| **`7.1` · `NB-B` (`BernoulliNB`)** | **`2,971`** | **Sí (`2,967`)** | **Sí (`0` fuga)** | `4` binarias densas (`es_vigente`, `tiene_skills`, `tiene_knowledge`, `tiene_sin_tipo`) + `2,967` dummies ESCO. | Casi homogénea (omite las `10` continuas/ordinales). |
| **`7.1` · `NB-H` (`HybridNaiveBayes` · ELEGIDO)** | **`2,981`** | **Sí (`2,967`)** | **Sí (`0` fuga)** | `10` continuas/ordinales en submodelo Gaussiano + `2,971` binarias CSR en submodelo Bernoulli (incluye las `2,967` dummies ESCO). | **Sí (100 % idéntica a `6.0 Logística` y `99.9 %` a `KNN-W`)**. |
| **`7.2` · `KNN-D` (`kd_tree`)** | **`11`** | **No (`0`)** | **Sí (`0` fuga)** | Las `14` densas limpias menos `3` casi constantes (`< 1 %` minoría: `tiene_skills`, `tiene_sin_tipo`, `n_skills_sin_tipo_rob`), re-escaladas con `StandardScaler` en `Train`. | Solo homogénea en bloque denso. |
| **`7.2` · `KNN-G` (`kd_tree`, $w_g=8.0$)** | **`21`** | **No (`0`)** | **Sí (`0` fuga)** | `11` densas auditadas + `10` dummies de Gran Grupo ISCO ponderadas con $w_g = 8.0$. | Intermedia (usa ISCO 1D, no oficio ESCO). |
| **`7.2` · `KNN-W` (`brute`, $w=8.0$)** | **`2,978`** | **Sí (`2,967`)** | **Sí (`0` fuga)** | `11` densas auditadas + `2,967` dummies de ocupación ESCO ponderadas con $w = 8.0$. | **Sí (misma señal ocupacional + trayectoria que `NB-H` y `6.0`)**. |

---

### 2.3 Comparación Estricta en `TEST` (`347,720` Experiencias, `70,419` Personas) frente al Baseline Trivial

- **Por qué el baseline trivial (`"siempre dice que NO repite"`) es engañoso (`F-017`, `F-030`):** Como en `Test` hay `243,495` experiencias donde la persona no repite (`70.0262 %`) y `104,225` donde sí repite (`29.9738 %`), un modelo perezoso que responde siempre `"no repite"` logra **`70.03 %` de exactitud global (`Accuracy = 0.7003`)**, pero **detecta a `0` de las `104,225` experiencias reincidentes (`Recall = 0.00 %`, `F1 = 0.0000`, `ROC-AUC = 0.5000`)**.
- **Nota sobre `Train` (solo para auditar sobreajuste):** Ninguno de los modelos seleccionados en `6.0`–`7.2` presenta sobreajuste entre `Train` y `Test`:
  - En `6.0 Logística OHE`: `ROC-AUC Train CV = 0.7132` vs. `Test = 0.7133`; `F1 Train CV = 0.5340` vs. `Test = 0.5321` (`F-029`, `F-030`).
  - En `7.0 Árbol 3 (Skills, max_depth=4, balanced)`: `Train Acc = 0.6113` vs. `Test Acc = 0.6107`; `CV ROC-AUC = 0.6183` vs. `Test ROC-AUC = 0.6157` (`F-035`, la poda `max_depth <= 4` y `min_samples_leaf = 2,500` evitó el sobreajuste de árboles profundos).
  - En `7.1 NB-H`: `PR-AUC Train CV = 0.4994` vs. `Test = 0.4962` (`F-037`).
  - En `7.2 KNN-W`: `PR-AUC Train CV (10% muestra) = 0.5008` vs. `Test (100% Train) = 0.5247` (`F-039`, `F-040`, mejora al disponer de `10x` más vecinos de referencia en el `100 %` de `Train`).

#### Tabla 2.2 · Resultados Verificados en `TEST` (`Versión A`, `347,720` filas / `70,419` personas) y Tiempos/RAM Registrados (`F-030` a `F-040`)

| Familia / Modelo | Vars ($X$) | ¿Incluye `2,967` Oficios ESCO? | `Test ROC-AUC` (Calculado en Todos) | `Test F1 Clase 1` (Calculado en Todos) | `Test Recall Clase 1` (De cada 100 que sí repiten, detecta...) | `Test Precision Clase 1` (Calculado en Todos) | `Test Accuracy` vs. Baseline `70.03 %` | `Test PR-AUC` *(No usar para rankear a `7.0`)* | `Test Brier` *(Menor es mejor; no usar para rankear a `7.0`)* | Tiempo `fit` Registrado | Tiempo `predict` en `Test` (`347.7k` filas) | Memoria Matriz `Train` (`MB`) / RSS Pico (`MB`) |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Ref 1 · Baseline Trivial (`"Siempre dice NO repite"`)** | `0` | No | `0.5000` | `0.0000` | **`0.0 de 100` (`0.00 %`)** | `0.00 %` | `70.03 %` *(engañoso)* | `0.2997` | `0.2099` (`6.0`) | `0.000 s` | `0.000 s` | `0 MB` / `NOT VERIFIED` |
| **Ref 2 · Trivial Todo-Positivo (`"Siempre dice SÍ repite"`)** | `0` | No | `0.5000` | `0.4612` | `100.0 de 100` (`100.00 %`) | `29.97 %` | `29.97 %` | `0.2997` | `No calculado` | `0.000 s` | `0.000 s` | `0 MB` / `NOT VERIFIED` |
| **Ref 3 · `6.0` Logística Regularizada OHE (Techo Lineal)** | `2,981` | **Sí** | `0.7133` | `0.5321` (`0.5384` a igual alerta) | **`61.5 de 100` (`61.47 %`)** (`73.4 %` a igual alerta) | `46.91 %` | `67.60 %` | `0.5109` | `No calculado` (ponderado) | `4.005 s` | **`0.010 s`** | `118.19 MB` / `NOT VERIFIED` |
| **`6.0` · HistGradientBoosting (Solo denso)** | `14` | No | `0.6936` | `0.5151` | **`61.1 de 100` (`61.09 %`)** | `44.53 %` | `64.26 %` (`BalAcc`) | `0.4951` | `No calculado` (ponderado) | `8.585 s` | `0.407 s` | `74.29 MB` / `NOT VERIFIED` |
| **`7.0` · Árbol 1 · ISCO (`class_weight=None`)** | `10` | **No** | `0.5459` | `0.0000` | **`0.0 de 100` (`0.00 %`)** | `0.00 %` | `70.03 %` | `No calculado en 7.0` | `No calculado en 7.0` | `NOT VERIFIED` *(16.1 ms en 5k)* | `NOT VERIFIED` | `NOT VERIFIED` |
| **`7.0` · Árbol 1 · ISCO (`balanced`)** | `10` | **No** | `0.5459` | `0.4620` | **`79.6 de 100` (`79.61 %`)** | `32.54 %` | `44.43 %` | `No calculado en 7.0` | `No calculado en 7.0` | `NOT VERIFIED` *(16.1 ms en 5k)* | `NOT VERIFIED` | `NOT VERIFIED` |
| **`7.0` · Árbol 2 · Educación (`balanced`)** | `2` | **No** | `0.5208` | `0.4564` | **`87.4 de 100` (`87.38 %`)** | `30.88 %` | `37.60 %` | `No calculado en 7.0` | `No calculado en 7.0` | `NOT VERIFIED` *(16.5 ms en 5k)* | `NOT VERIFIED` | `NOT VERIFIED` |
| **`7.0` · Árbol 3 · Competencias ESCO (`None`)** | `7` | **No** | `0.6145` | `0.1769` | **`10.6 de 100` (`10.60 %`)** | `53.63 %` | `70.46 %` | `No calculado en 7.0` | `No calculado en 7.0` | `NOT VERIFIED` *(35.5 ms en 5k)* | `NOT VERIFIED` | `NOT VERIFIED` |
| **`7.0` · Árbol 3 · Competencias ESCO (`balanced` · Ganador `7.0`)** | `7` | **No** | **`0.6157`** | **`0.4550`** | **`54.2 de 100` (`54.21 %`)** | `39.20 %` | `61.07 %` | **`No calculado en 7.0`** | **`No calculado en 7.0`** | `NOT VERIFIED` *(35.5 ms en 5k)* | `NOT VERIFIED` | `NOT VERIFIED` |
| **`7.1` · `NB-G` (`GaussianNB`, `14` cols, $\tau^*=0.295$)** | `14` | No | `0.5921` | `0.4687` | `85.5 de 100` (`85.51 %`) | `32.28 %` | `41.90 %` | `0.3778` | `0.2086` | `0.219 s` | `0.073 s` | `74.29 MB` / `NOT VERIFIED` |
| **`7.1` · `NB-B` (`BernoulliNB`, `2,971` cols, $\tau^*=0.270$)** | `2,971` | **Sí** | `0.7024` | `0.5323` | `72.9 de 100` (`72.85 %`) | `41.93 %` | `61.62 %` | `0.4829` | `0.1877` | `0.091 s` (`0.100 s`) | `0.054 s` (`0.060 s`) | `36.74 MB` / `NOT VERIFIED` |
| **`7.1` · `NB-H` (`HybridNaiveBayes`, $\tau^*=0.265$ · ELEGIDO POR EL EQUIPO)** | **`2,981`** | **Sí** | **`0.7058`** | **`0.5337`** | **`72.8 de 100` (`72.79 %`)** | **`42.14 %`** | **`61.88 %`** | **`0.4962`** | **`0.1871`** | **`0.560 s`** (`0.634 s`) | **`0.241 s`** (`0.283 s`) | **`118.19 MB` / `1,539.3 MB`** (`7.1` Celda 15) |
| **`7.2` · `KNN-D` (`11` cols densas, $k=101$, $\tau^*=0.270$)** | `11` | No | `0.6677` | `0.5010` | `71.2 de 100` (`71.24 %`) | `38.63 %` | `57.46 %` | `0.4652` | `0.1936` | `5.216 s` | `71.590 s` | `58.37 MB` / `1,807.8 MB` |
| **`7.2` · `KNN-G` (`21` cols con ISCO 1D, $w_g=8$, $\tau^*=0.270$)** | `21` | No | `0.6919` | `0.5186` | `71.2 de 100` (`71.18 %`) | `40.79 %` | `60.39 %` | `0.4928` | `0.1887` | `8.815 s` | `1,104.710 s` (`18.4 min`) | `111.43 MB` / `2,051.3 MB` |
| **`7.2` · `KNN-W` (`2,978` cols con ESCO, $w=8$, $\tau^*=0.280$ · Ganador `7.2`)** | **`2,978`** | **Sí** | **`0.7245`** | **`0.5471`** | **`70.8 de 100` (`70.77 %`)** (`76.0 %` a igual alerta) | **`44.59 %`** | **`64.87 %`** | **`0.5247`** | **`0.1817`** | **`0.076 s`** | **`29,146.830 s` (`~8.10 h`)** | **`121.54 MB` / `1,931.7 MB`** |

---

### 2.4 Regla de Interpretación sobre el Desempeño de `7.0` y Estimación Analítica de Re-Ejecución (Sin Ejecutar)

1. **Interpretación justa del resultado de `7.0` (Regla de desventaja informativa):**
   - Aunque el **Árbol 3 (`7.0`, Competencias ESCO, `balanced`)** obtuvo un `Test ROC-AUC = 0.6157` y `Test F1 = 0.4550` inferiores a los de **`NB-H` (`0.7058` / `0.5337`)** y **`KNN-W` (`0.7245` / `0.5471`)**, **esa diferencia NO puede atribuirse únicamente al algoritmo de Árbol de Decisión**, porque el Árbol 3 vio solo **`7` variables** (y el Árbol 1 solo `10`), mientras que `NB-H` y `KNN-W` recibieron las **`2,967` dummies del código exacto de ocupación ESCO** más las variables de duración y orden del empleo (`2,981` y `2,978` variables).
   - De hecho, en la ablación `P7` de `7.1` (`F-038`), cuando a `NB-H` se le quitan las `2,967` dummies de ocupación ESCO, su `PR-AUC` cae en `-0.1246` (de `0.4981` a `0.3735`), y `NB-G` sin dummies de oficio obtiene `Test ROC-AUC = 0.5921` (`F-037`), que es **inferior** al `0.6157` logrado por el Árbol 3 con solo `7` variables de competencias. Asimismo, como `7.0` no calculó `PR-AUC` ni `Brier`, jamás se afirma que el árbol esté mal calibrado.
2. **Estimación analítica (SIN ejecutar código) del tiempo y memoria necesarios para re-ejecutar `7.0` con las mismas `2,981` variables y calcular `PR-AUC` + `Brier`:**
   - *Cálculo basado estrictamente en las dimensiones verificadas de `X_train` (`1,391,018 × 2,981`) y `X_test` (`347,720 × 2,981`) en formato disperso CSR (`118.19 MB` en `Train`, `F-036`):*
   - **Memoria RAM requerida:**
     - Si se pasa como **matriz dispersa `scipy.sparse.csr_matrix`** (soportada nativamente por `BestSparseSplitter` en `sklearn.tree.DecisionTreeClassifier`): **`~0.6 GB a 1.2 GB` de RAM RSS pico** (cabe holgadamente en los `32 GB` del equipo).
     - *(Advertencia: si se convirtiera `1,391,018 × 2,981` a matriz densa `float64`, exigiría $1,391,018 \times 2,981 \times 8\text{ bytes} =$ **`33.18 GB` (`30.90 GiB`)**, provocando `MemoryError` en `32 GB` de RAM).*
   - **Tiempo de cómputo estimado:**
     - Ajuste de un árbol CART podado (`max_depth = 4..8`, `min_samples_leaf = 2,500`) sobre la matriz CSR `1,391,018 × 2,981`: **`~12 a 25 segundos`** por árbol.
     - Búsqueda `5-fold StratifiedGroupKFold` sobre una rejilla corta de 5 configuraciones (25 ajustes) + re-entrenamiento final + `predict_proba` en `Test` (`347,720` filas) + cálculo de `PR-AUC`, `Brier` y `300` réplicas bootstrap por persona: **`~5 a 9 minutos` en total**.
   - *Estado:* No se ha re-ejecutado `7.0` conforme a tu instrucción, dado que el equipo ya eligió **Naive Bayes (`7.1`)** y la ventaja entre los dos candidatos con `2,967` oficios (`NB-H` vs. `KNN-W`) está completamente medida con las mismas variables.

---

## 3. Clustering: Auditoría de Homogeneidad, Métricas de Calidad y Nombres de Perfil (`8.0` vs. `8.1` — Sección B)

### 3.1 ¿Corrieron K-Means (`8.0`) y Clustering Jerárquico Ward (`8.1`) sobre los Mismos Datos?

- **Mismas variables (`V_PERSON`, `9` columnas sin fuga en `Versión B` primaria, `F-041`):** Ambos métodos utilizaron exactamente las mismas `9` variables a nivel persona estandarizadas con `StandardScaler` ajustado en `Train`: `n_jobs`, `span_q`, `dur_mean`, `overlap_ratio`, `mean_skills_competence`, `mean_skills_knowledge`, `mean_prop_competence`, `nivel_academico_ord_imputado` y `educacion_no_reportada`, omitiendo `n_skills_essential` por colinealidad exacta $E = C + K$ y con **`0` variables derivadas del target `reincide`**.
- **ALERTA DE NO HOMOGENEIDAD EN POBLACIÓN DE AJUSTE (`Comparación no homogénea en tamaño muestral`, `F-041`, `F-047`):**
  - **K-Means++ (`8.0`)** se ajustó sobre el **`100 %` de las personas de `Train` (`281,674` personas)** y asignó directamente a las **`352,093` personas del censo clasificado** (además de una segunda vista sobre las **`1,738,738` experiencias**, `F-043`).
  - **Clustering Jerárquico de Ward (`8.1`)** **NO** pudo ejecutarse sobre las `281,674` personas de `Train` ni sobre las `352,093` personas totales porque la matriz condensada de distancias pares $\frac{n(n-1)}{2}\times 8\text{ bytes}$ exige **`317.36 GB` de RAM en `Train`** (`39,669,980,301` pares) y **`495.88 GB` de RAM en el censo total** (`61,984,564,278` pares), lo que produce un `MemoryError` físico determinista en una máquina de `32 GB` de RAM (`F-041`).
  - Por ello, `8.1` ajustó el dendrograma directo de Ward sobre una **submuestra estratificada de `n = 25,000` personas de `Train` (`8.88 %` de `Train` / `7.10 %` del censo total, `2.50 GB` de matriz condensada, pico `~8.0 GB` RAM, `146.11 s`)** (además de una muestra piloto inicial de `n = 3,000` personas = `1.07 %` de `Train`, `36 MB`, `0.80 s`), y para el `92.90 %` restante del censo (`327,093` personas) tuvo que aproximar la asignación mediante un clasificador externo de centroide más cercano (`NearestCentroid`, `F-044`).
  - **Qué implica esta no-homogeneidad:** Las métricas geométricas internas (`Silhouette`, `Davies-Bouldin`, `Calinski-Harabasz`) de K-Means (`N = 281,674`) y de Ward directo (`n = 25,000` o proyectado a `352,093`) no se calculan sobre el mismo conjunto de ajuste directo; Ward evalúa un árbol jerárquico exacto sobre el `7.10 %` del censo, mientras que K-Means optimiza fronteras esféricas directamente sobre el `100 %` de `Train`.

---

### 3.2 Cómo se Eligió $k^* = 4$, Métricas Calculadas, Tamaños y Nombres de Perfil Laboral (`F-042`, `F-043`, `F-044`)

1. **Cómo se eligió $k^* = 4$ de forma convergente:**
   - En **`8.1` (Ward, torneo de linkage en `n = 3,000`):** Primero se descartaron `single`, `average` y `complete` porque sufrían encadenamiento severo (*chaining*: concentraban el `99.87 %`, `97.50 %` y `90.03 %` de las personas en un solo macro-clúster, `F-042`). En el dendrograma de `ward` (clúster máximo balanceado = `55.00 %`), el salto vertical de fusión se mantiene alto hasta **$k^* = 4$ ($\Delta h = 10.060$)** y **se desploma un `-85.8 %` al pasar a $k = 5$ ($\Delta h = 1.431$)**, demostrando 4 macro-ramas naturales (`F-042`).
   - En **`8.0` (K-Means++, `k = 2..8` sobre `281,674` personas de `Train`):** En $k^* = 4$, el índice **Calinski-Harabasz alcanza su máximo (`46,780.83`)**, la inercia WCSS cae un `11.93 %` respecto a $k = 3$ (`1,692,018.00`), `Silhouette = 0.1948` (antes de caer a `0.1751` en $k = 5$) y en la vista de experiencias (`1,391,018` filas) `Silhouette` alcanza su **máximo global en $k^* = 4$ (`0.2465`)** (`F-043`).
   - **Concordancia entre ambos métodos en las `352,093` personas (`F-044`):** Al ampliar la muestra de Ward de `n = 3,000` a `n = 25,000`, la concordancia con K-Means++ sube de `ARI = 0.4708` (`NMI = 0.5462`) a **`ARI = 0.6502` (`NMI = 0.7296`)**.

#### Tabla 3.1 · Comparación de Calidad, Escala y Tamaños de Grupo: K-Means++ (`8.0`) vs. Jerárquico Ward (`8.1`) (`F-041`–`F-044`)

| Criterio / Métrica | **`8.0` · K-Means++ (`init='k-means++', n_init=10` · ELEGIDO POR EL EQUIPO)** | **`8.1` · Clustering Jerárquico de Ward (Muestra Optimizada `n = 25,000` / Piloto `n = 3,000`)** |
|---|---|---|
| **Población de ajuste directo** | **`100 %` de `Train` (`281,674` personas)** y evaluación directa en `Test` (`70,419` personas) = **`352,093` personas** (más `1,738,738` experiencias en `V_EXPERIENCE`). | **Solo `25,000` personas de `Train` (`8.88 %` de Train / `7.10 %` del censo)** para ajuste directo (`3,000` en piloto). Las `327,093` personas restantes (`92.90 %`, incluido todo `Test`) requieren proyección externa `NearestCentroid`. |
| **Memoria RAM de matriz y Tiempo de ajuste (`fit`)** | No requiere matriz $O(n^2)$: su matriz `V_PERSON` Train (`281,674 × 9 × 8 B`) pesa **`20.28 MB`** (`25.35 MB` censo total; RSS de proceso `NOT VERIFIED` en `8.0`); ajuste completo en **`1.80 segundos`** (`F-041`, Tabla 2.1 de `Analisis_Comparativo_8_0_vs_8_1_Clustering.md`). | En censo completo: **`495.88 GB` RAM (`317.36 GB` en Train) → `MemoryError`**. En `n = 25,000`: **`2.50 GB` matriz condensada (`~8.0 GB` pico RAM)** y **`146.11 segundos`** (`0.036 GB` y `0.80 s` en `n = 3,000`). |
| **Métricas internas de separación ($k^* = 4$)** | **Personas (`281,674` Train):** `Silhouette = 0.1948`, **`Davies-Bouldin = 1.6298`**, **`Calinski-Harabasz = 46,780.83`**.<br/>**Experiencias (`1,391,018` Train):** **`Silhouette = 0.2465`**, `Davies-Bouldin = 1.4488`, `Calinski-Harabasz = 20,887.65`. | **En `n = 25,000` (proyectado a `352,093`):** `Silhouette = 0.1167` (`0.2367` interno en muestra), `Davies-Bouldin = 1.9295`, `Calinski-Harabasz = 3,134.50`.<br/>**En `n = 3,000`:** `Silhouette = 0.1827`, `Davies-Bouldin = 1.9489`, `Calinski-Harabasz = 370.72`, `cophenet = 0.4463`. |
| **Clúster 0: *Inserción Temprana y Trayectorias Cortas en Oficios Operativos* (ISCO 5 · Servicios y ventas)** | **`154,577` personas (`43.90 %`**: `43.94 %` Train / `43.73 %` Test) · `4.82` empleos, amplitud `38.71` trim, duración media `8.75` trim, `2.51` conocimientos ESCO · Reincidencia post-hoc Test: **`47.78 %` (`Lift = 1.046x`)**. | **Directo en `n = 25,000`:** **`6,818` personas (`27.27 %`)** (`119,736` = `34.01 %` proyectado al censo; `52.13 %` en `n = 3,000`) · `3.96` empleos, duración media `10.36` trim · Reincidencia Test proyectada: `44.04 %` (`Lift = 0.964x`). |
| **Clúster 1: *Trabajadores con Educación No Reportada (MNAR) y Perfil Operativo Estable* (ISCO 5)** | **`41,062` personas (`11.66 %`**: `11.65 %` Train / `11.70 %` Test) · **`100 %` sin educación reportada (`MNAR = 1.00`)**, `4.72` empleos, duración media `14.12` trim · Reincidencia post-hoc Test: **`45.00 %` (`Lift = 0.985x`)**. | **Directo en `n = 25,000`:** **`2,966` personas (`11.86 %`)** (`41,607` = `11.82 %` proyectado; `11.65 %` en `n = 3,000`) · **`100 %` sin educación reportada (`MNAR = 1.00`)**, duración media `14.70` trim · Reincidencia Test proyectada: `44.96 %`. |
| **Clúster 2: *Profesionales Intensivos en Conocimiento y Alta Exigencia ESCO* (ISCO 2 · Científicos e intelectuales)** | **`98,553` personas (`27.99 %`**: `27.95 %` Train / `28.14 %` Test) · Nivel académico `2.33` (Pregrado/Maestría), **`5.98` conocimientos teóricos ESCO** (`25.37` esenciales) · Reincidencia post-hoc Test: **`42.75 %` (`Lift = 0.936x`, la más baja por movilidad vertical)**. | **Directo en `n = 25,000`:** **`11,924` personas (`47.70 %`)** (`136,804` = `38.85 %` proyectado; en `n = 3,000` aislaba un núcleo de `9.47 %` con `7.69` conocimientos y reincidencia `34.34 %`) · Reincidencia Test proyectada en 25k: `47.96 %`. |
| **Clúster 3: *Trayectorias Consolidadas de Larga Permanencia y Pluriempleo* (ISCO 3 · Técnicos)** | **`57,901` personas (`16.44 %`**: `16.45 %` Train / `16.43 %` Test) · **`5.44` empleos**, amplitud **`112.14` trimestres (`~28 años`)**, duración media **`37.47` trim**, solapamiento **`1.61x`** · Reincidencia post-hoc Test: **`45.55 %` (`Lift = 0.997x`)**. | **Directo en `n = 25,000`:** **`3,292` personas (`13.17 %`)** (`53,946` = `15.32 %` proyectado; `26.75 %` en `n = 3,000`) · Amplitud **`109.66` trim**, duración media **`37.96` trim**, solapamiento **`1.64x`** · Reincidencia Test proyectada: `43.99 %`. |
| **¿Cada grupo recibe un nombre de perfil laboral claro y accionable?** | **Sí (`4 de 4` grupos con nombre, centroide exacto en unidades originales `diff = 0.000000` y programa recomendado del Observatorio Laboral).** | **Sí (`4 de 4` grupos con nombre; en `n = 25,000` converge con K-Means en Clústeres 1 y 3, aunque ensancha la frontera del Clúster 2 al `47.70 %` de la muestra).** |

---

## 4. Aplicación de las Reglas de Puntuación, Renormalización y Análisis de Sensibilidad (Sección D)

### 4.1 Evaluación en 2 Pasos para Modelos Supervisados (`7.0` Árbol 3 vs. `7.1` Naive Bayes `NB-H` vs. `7.2` `KNN-W`)

#### Paso 1 · Requisitos Mínimos Eliminatorios (`PASS / FAIL`)
1. **`7.0` · Árboles 1 y 2 (`ISCO 1D` y `Educación`) y configuraciones `class_weight=None`:**
   - En `class_weight=None`, los Árboles 1 y 2 predicen `0` positivos (`Test Recall = 0.00 %`, `F1 = 0.0000`) y el Árbol 3 apenas detecta al `10.60 %` de los repetidores (`Recall = 0.1060 < 0.5000`). En `balanced`, los Árboles 1 (`ROC-AUC = 0.5459 < 0.5500`, `Lift = 1.086x < 1.50x`) y 2 (`ROC-AUC = 0.5208 < 0.5500`, `F1 = 0.4564` inferior al trivial todo-1 `0.4612`) no separan clases según el criterio del propio cuaderno `7.0` (`F-033`, `F-034`) → **`DESCARTADOS en Paso 1`**.
2. **Los 3 candidatos principales de cada familia que SÍ pasan los Requisitos Mínimos (`PASS`):**
   - **`7.0` · Árbol 3 · Competencias ESCO (`class_weight='balanced'`, Versión A):** `0` fuga (`PASS`), detecta `54.21 %` de repetidores en `Test` con `ROC-AUC = 0.6157` y `Hoja 16 Lift = 1.766x >= 1.50x` (`PASS`), corre a escala (`PASS`). *(Nota: sujeto a advertencia de `Comparación no homogénea en variables` por usar solo `7` columnas sin las `2,967` dummies de oficio, y `Tiempo/RAM en 1.39M filas = NOT VERIFIED`).*
   - **`7.1` · `HybridNaiveBayes` (`NB-H`, $\tau^* = 0.265$, Versión A):** `0` fuga (`PASS`), detecta **`72.79 %`** de repetidores en `Test` (`ROC-AUC = 0.7058`, `F1 = 0.5337`) (`PASS`), corre en `0.801 s` totales y `118.19 MB` (`PASS`).
   - **`7.2` · `KNN-W` ($k = 101, w = 8.0$, $\tau^* = 0.280$, Versión A):** `0` fuga (`PASS`), detecta **`70.77 %`** de repetidores en `Test` (`ROC-AUC = 0.7245`, `F1 = 0.5471`) (`PASS`), evalúa el `100 %` de `Test` por bloques en `1,931.7 MB` RSS (`PASS`, aunque con `29,146.83 s` de tiempo).
   - *(Referencia compartida `6.0` Logística Regularizada OHE: pasa los 3 requisitos con `ROC-AUC = 0.7133`, `F1 = 0.5321`, `Recall = 61.47 %` [`73.42 %` a igual tasa de alerta], `fit + predict = 4.015 s`; se incluye en la tabla como línea base/techo lineal de `6.0`).*

#### Paso 2 · Puntuación Ponderada (`1` a `5`) según las Rúbricas de la Sección 1.3

> **Nota sobre criterios sin evidencia comparable entre los 3 candidatos (`C5` Estabilidad, y `C2` Practicidad para `7.0`):**
> - En **`C5` (Estabilidad `10 %`)**, `7.0` y `7.1` midieron `Versión A vs. Versión B` sobre el `100 %` de `Test` (`|\Delta\text{AUC}| = 0.0046` en Árbol 3 [`0.0000` en B2] y `|\Delta\text{AUC}| = 0.0009` en `NB-H`), mientras que `7.2` midió `Versión A vs. B` solo sobre `KNN-D` en `5-fold CV` al `10 %` de personas (`\Delta\text{PR-AUC} = -0.00277`), no sobre `KNN-W` en `Test`. Por tanto, `C5` se marca como **`"sin evidencia comparable"`** y se excluye en el puntaje principal renormalizado (`C1..C4` suman `90 %` → renormalizados a `38.89 % / 27.78 % / 22.22 % / 11.11 %`), mostrando también el puntaje con `C5` incluido.
> - En **`C2` (Practicidad `25 %`)**, `13f_comparacion_costos_computacionales.csv` registró tiempos y memoria exactos en el dataset completo para `NB-H` (`0.560 s + 0.241 s = 0.801 s`, `118.19 MB` → **`5 / 5`**) y `KNN-W` (`0.076 s + 29,146.83 s = 8.10 h`, `121.54 MB / 1,931.7 MB RSS` → **`1 / 5`**), pero **no registró el tiempo en `Test` completo ni la RAM de `7.0`** (`fit_time_ms_media = 35.47 ms` se registró en la submuestra de 5 semillas de `5,000` personas, Tabla `10`). Por ello, para `7.0` mostramos su puntaje tanto excluyendo `C2` (renormalizando `C1, C3, C4`) como asignando `5 / 5` por su ajuste instantáneo en submuestra (`35.5 ms` en `7` variables). En ambos casos el orden de los candidatos no cambia.

| Candidato Supervisado | `C1` Acierto y Detección en `TEST` (`35 %` / renorm `38.89 %`) *[Datos]* | `C2` Practicidad a Escala `1.74M` (`25 %` / renorm `27.78 %`) *[Datos]* | `C3` Explicabilidad en 1 Oración (`20 %` / renorm `22.22 %`) *[`Team judgment`]* | `C4` Ajuste Descriptivo sin Causalidad (`10 %` / renorm `11.11 %`) *[`Team judgment`]* | `C5` Estabilidad `A vs. B` (`10 %`) *[Comparabilidad parcial]* | **Puntaje Total SIN `C5` (Renormalizado sobre `90 %`)** | **Puntaje Total CON `C5` (Pesos Base `100 %`)** | Estado Final |
|---|---|---|---|---|---|---|---|---|
| **`7.1` · `HybridNaiveBayes` (`NB-H`, `2,981` vars)** | **`4 / 5`**<br/>(`ROC-AUC = 0.7058`, `F1 = 0.5337`, detecta **`72.8 / 100`** que repiten) | **`5 / 5`**<br/>(`fit = 0.560 s`, `predict Test = 0.241 s`, total **`0.801 s`**, matriz `118.19 MB` / RSS `1,539.3 MB`) | **`4 / 5`**<br/>(Suma transparente de log-probabilidades por oficio ESCO y trayectoria) | **`5 / 5`**<br/>(Empate: describe tasas y propensiones observables) | *Sin evidencia comparable en los 3*<br/>*(Si se puntúa: **`5 / 5`**, $|\Delta\text{AUC}| = 0.0009$ en Test)* | **`4.39 / 5.00`** | **`4.45 / 5.00`** | **GANADOR Y ELEGIDO POR EL EQUIPO** |
| **`7.2` · `KNN-W` ($k=101, w=8$, `2,978` vars)** | **`5 / 5`**<br/>(**Mejor en cifras:** `ROC-AUC = 0.7245`, `F1 = 0.5471`, detecta **`70.8 / 100`** [`76.0 / 100` a igual alerta]) | **`1 / 5`**<br/>(`fit = 0.076 s`, pero `predict Test = 29,146.83 s` = **`8.10 horas`**, RSS `1,931.7 MB`) | **`3 / 5`**<br/>(Votación de 101 vecinos en `2,978` dims; sin peso explícito por variable) | **`5 / 5`**<br/>(Empate: similitud empírica entre historiales) | *Sin evidencia comparable en Test para `KNN-W`*<br/>*(Si se puntúa con `KNN-D` CV: **`5 / 5`**, $|\Delta| = 0.0028$)* | **`3.44 / 5.00`** | **`3.60 / 5.00`** | **Mejor en precisión pura (`C1`), descartado para operación por `8.10 h` en `C2`** |
| **`7.0` · Árbol 3 · Competencias ESCO (`balanced`, `7` vars)** *(Comparación no homogénea en variables)* | **`2 / 5`**<br/>(`ROC-AUC = 0.6157`, `F1 = 0.4550`, detecta **`54.2 / 100`**; *vio solo `7` vars sin las `2,967` dummies de oficio*) | *`NOT VERIFIED` en 1.39M (`35.5 ms` en 5k)*<br/>*(Si se excluye `C2`: renorm sobre `65 %`; si se asigna `5 / 5` por 7 vars)* | **`5 / 5`**<br/>(Árbol visual de profundidad 4 y `13` hojas con reglas `"si... entonces..."`) | **`5 / 5`**<br/>(Empate: perfila exigencias del catálogo ESCO) | *Sin evidencia comparable en los 3*<br/>*(Si se puntúa: **`4 / 5`**, $|\Delta\text{AUC}| = 0.0046$, `0.0000` en B2)* | **`3.38 / 5.00`** *(excl. `C2` y `C5`)*<br/>`3.83 / 5.00` *(con `C2=5`)* | **`3.48 / 5.00`** *(excl. `C2`)*<br/>`3.85 / 5.00` *(con `C2=5`)* | **No concluyente como método aislado por desventaja de variables (`7` vs. `2,981`)** |
| *(Ref 3 · `6.0` Logística Regularizada OHE, `2,981` vars)* | *`4 / 5`*<br/>*(`ROC-AUC = 0.7133`, `F1 = 0.5321`, `Recall = 61.5 %` [`73.4 %` igual alerta])* | *`5 / 5`*<br/>*(`fit = 4.005 s`, `predict = 0.010 s`, `118.19 MB`)* | *`4 / 5`*<br/>*(Suma lineal de `2,981` coeficientes log-odds)* | *`5 / 5`*<br/>*(Empate)* | *No medida en `6.0` para todos los criterios (`|\Delta\text{AUC}| = 0.0001` en Test)* | *`4.39 / 5.00` (Techo lineal de referencia)* | *`4.45 / 5.00`* | *Línea base multivariada / Techo de referencia de `6.0`* |

---

### 4.2 Evaluación en 2 Pasos para Métodos de Clustering (`8.0` K-Means++ vs. `8.1` Jerárquico Ward)

#### Paso 1 · Requisitos Mínimos Eliminatorios (`PASS / FAIL`)
1. **`8.1` · Enlaces Jerárquicos `single`, `average` y `complete` (`n = 3,000`):** Pasan anti-fuga (`0` columnas de target), pero fallan en formar grupos útiles por encadenamiento severo (*chaining*: un solo clúster absorbe el `99.87 %`, `97.50 %` y `90.03 %` de las personas, `F-042`) → **`DESCARTADOS en Paso 1`**.
2. **`8.1` · Clustering Jerárquico de Ward Directo sobre el Censo Completo (`352,093` personas / `281,674` Train):** Pasa anti-fuga, pero **falla el requisito de escalabilidad en la población completa** (`317.36 GB` de RAM en `Train` y `495.88 GB` en `Total` para la matriz condensada $O(n^2)$ frente a `32 GB` disponibles → `MemoryError` físico determinista, `F-041`). Solo puede ejecutarse directamente sobre la **submuestra estratificada de `n = 25,000` personas de `Train` (`7.10 %` del censo)**. Evaluamos a continuación `8.0` K-Means++ (`100 %` del censo) frente a `8.1` Ward Optimizado (`n = 25,000` + proyección `NearestCentroid`) dejando explícito que **la comparación no es *like-for-like* en tamaño muestral**.

#### Paso 2 · Puntuación Ponderada (`1` a `5`) para Clustering

| Candidato de Clustering | `C1` Separación y Nombres de Perfil (`35 %` / renorm `38.89 %`) *[Datos]* | `C2` Practicidad a Escala `352k` Personas (`25 %` / renorm `27.78 %`) *[Datos]* | `C3` Explicabilidad en 1 Oración (`20 %` / renorm `22.22 %`) *[`Team judgment`]* | `C4` Ajuste Descriptivo sin Causalidad (`10 %` / renorm `11.11 %`) *[`Team judgment`]* | `C5` Estabilidad (`10 %`) *[Comparabilidad parcial]* | **Puntaje Total SIN `C5` (Renormalizado sobre `90 %`)** | **Puntaje Total CON `C5` (Pesos Base `100 %`)** | Estado Final |
|---|---|---|---|---|---|---|---|---|
| **`8.0` · K-Means++ (`k* = 4`, `352,093` personas y `1,738,738` experiencias)** | **`4 / 5`**<br/>(`Silhouette = 0.1948` en Personas y **`0.2465`** en Experiencias; `DBI = 1.6298`; `CHI = 46,780.83`; 4 perfiles nombrados con paridad Train/Test `< 0.21 pp`) | **`5 / 5`**<br/>(Ajusta sobre el **`100 %` de Train** en **`1.80 s`**, matriz Train **`20.28 MB`** sin pares [RSS `NOT VERIFIED` en `8.0`]; asigna directamente a las `352,093` personas) | **`4 / 5`**<br/>(Cada grupo es el retrato promedio exacto `diff = 0.000000` en unidades reales) | **`5 / 5`**<br/>(Empate: tipología descriptiva con `0` variables del target) | *Sin evidencia idéntica*<br/>*(Si se puntúa: **`5 / 5`**, `ARI = 0.8633` B vs. A en Train completo; `ARI = 0.8557` en 5 semillas)* | **`4.39 / 5.00`** | **`4.45 / 5.00`** | **GANADOR Y ELEGIDO POR EL EQUIPO (`DEC-14`)** |
| **`8.1` · Jerárquico Ward (`k* = 4`, muestra directa `n = 25,000` de Train)** *(Comparación no homogénea en población)* | **`3 / 5`**<br/>(Proyectado a `352k`: `Silhouette = 0.1167`, `DBI = 1.9295`, `CHI = 3,134.50`; confirma $k^* = 4$ y converge con K-Means `ARI = 0.6502`, pero ensancha el Clúster 2 al `47.70 %` de la muestra) | **`2 / 5`**<br/>(Inviable en las `352,093` personas por **`495.88 GB` RAM**; directo solo en `25,000` personas = `7.10 %` del censo en `146.11 s` y `2.50 GB` matriz) | **`5 / 5`**<br/>(El dendrograma muestra visualmente el árbol de fusiones y la caída del `-85.8 %` en el salto vertical después de $k^* = 4$) | **`5 / 5`**<br/>(Empate: taxonomía jerárquica descriptiva sin target) | *Sin evidencia idéntica*<br/>*(Si se puntúa por cambio muestral `3k → 25k`: **`3 / 5`**, `ARI = 0.3582`, `NMI = 0.5035`)* | **`3.33 / 5.00`** | **`3.30 / 5.00`** | **Rol complementario: valida $k^* = 4$ en submuestra (`DEC-14`)** |

---

### 4.3 Análisis de Sensibilidad de los Pesos (¿Cambia el Ganador si Cambiamos las Prioridades?)

Evaluamos cuatro esquemas de pesos (tanto sobre los 4 criterios comparables `C1..C4` como sobre los 5 criterios `C1..C5`):
1. **Esquema Base Aprobado (`C1 = 35 %, C2 = 25 %, C3 = 20 %, C4 = 10 %, C5 = 10 %`):**
2. **Pesos Iguales (`25 %` cada uno en `C1..C4` / `20 %` cada uno en `C1..C5`):**
3. **Prioridad Extrema a Acierto y Detección (`C1 = 50 %`, resto reescalado proporcionalmente: `C2 = 19.23 %, C3 = 15.38 %, C4 = 7.69 %, C5 = 7.69 %`):**
4. **Baja Importancia a Practicidad (`C2 = 10 %`, resto reescalado proporcionalmente: `C1 = 42.0 %, C3 = 24.0 %, C4 = 12.0 %, C5 = 12.0 %`):**

| Esquema de Pesos Evaluado | Supervisado: **`7.1` Naive Bayes (`NB-H`)** | Supervisado: **`7.2` `KNN-W`** | Supervisado: **`7.0` Árbol 3 (`Skills`)** *(con `C2=5` / sin `C2`)* | ¿Quién Gana en Supervisados? | Clustering: **`8.0` K-Means++** | Clustering: **`8.1` Ward (`25k`)** | ¿Quién Gana en Clustering? |
|---|---:|---:|---:|---|---:|---:|---|
| **1. Pesos Base (`35 / 25 / 20 / 10 / 10`) — Sin `C5` (renorm)** | **`4.39`** | `3.44` | `3.83` / `3.38` | **`NB-H (7.1)` por `+0.95` pts sobre `KNN-W`** | **`4.39`** | `3.33` | **`K-Means++ (8.0)` por `+1.06` pts** |
| **1b. Pesos Base (`35 / 25 / 20 / 10 / 10`) — Con `C5`** | **`4.45`** | `3.60` | `3.85` / `3.48` | **`NB-H (7.1)` por `+0.85` pts sobre `KNN-W`** | **`4.45`** | `3.30` | **`K-Means++ (8.0)` por `+1.15` pts** |
| **2. Pesos Iguales (`25 %` c/u sin `C5` / `20 %` c/u con `C5`)** | **`4.50` / `4.60`** | `3.50` / `3.80` | `4.25` / `4.20` | **`NB-H (7.1)` gana en ambos** | **`4.50` / `4.60`** | `3.75` / `3.60` | **`K-Means++ (8.0)` gana en ambos** |
| **3. Acierto y Detección al `50 %` (`C1 = 50 %`) — Sin `C5` / Con `C5`** | **`4.32` / `4.38`** | `3.79` / `3.92` | `3.42` / `3.50` | **`NB-H (7.1)` sigue ganando (`+0.46` a `+0.53` pts)** | **`4.32` / `4.38`** | `3.27` / `3.23` | **`K-Means++ (8.0)` sigue ganando** |
| **4. Practicidad baja (`C2 = 10 %`, `C1 = 42 %`) — Sin `C5` / Con `C5`** | **`4.23` / `4.34`** | `3.95` / `4.08` | `3.55` / `3.62` | **`NB-H (7.1)` sigue ganando (`+0.26` a `+0.28` pts)** | **`4.23` / `4.34`** | `3.45` / `3.38` | **`K-Means++ (8.0)` sigue ganando** |
| **5. Caso límite: ¿Cuándo se invierte el ganador hacia `KNN-W`?** | `4.00` (si `C1=100%`) | **`5.00` (si `C1=100%`)** | `2.00` | **Solo si `C1 >= 72 %` y Practicidad `C2 <= 5 %` (ignorando las `8.10 horas` de cómputo)** | **`4.00` (si `C1=100%`)** | `3.00` (si `C1=100%`) | **Nunca se invierte (`K-Means++` domina o empata en `C1`, `C2`, `C4`, `C5`)** |

- **Conclusión de sensibilidad (para informar al usuario y poner en las *speaker notes*):**
  - En **Clustering**, **`K-Means++ (8.0)` es `100 %` robusto e invariante** bajo cualquier combinación razonable de pesos: gana en los 4 escenarios porque supera a Ward tanto en separación global (`Silhouette = 0.1948 / 0.2465` vs. `0.1167`) como en practicidad a escala completa (`1.80 s` en `352,093` personas vs. `MemoryError` de `495.88 GB` RAM).
  - En **Supervisados**, **`HybridNaiveBayes (NB-H, 7.1)` es estable y gana en los 4 escenarios evaluados** (pesos base, pesos iguales, `C1 = 50 %` y `C2 = 10 %`). El ganador **solo se invertiría a favor de `KNN-W (7.2)`** si el equipo asignara **`>= 72 %` del peso total exclusivamente a la precisión numérica (`C1`) y `<= 5 %` a la practicidad (`C2`)**, es decir, si no importara esperar **`8.10 horas`** para clasificar `Test`. Esto se declara explícitamente en la Diapositiva 8 y en sus notas del orador.

---

## 5. Analogías Cotidianas y Debilidades Principales Verificadas contra Nuestros Datos para los 5 Métodos (Sección E)

| # | Método Evaluado | Analogía Cotidiana en Una Sola Oración (Sin Engañar) | Debilidad Principal en Palabras Sencillas y **Verificación Directa en Nuestros Datos (`FACTS.md`)** |
|---:|---|---|---|
| `1` | **Árbol de Decisión CART (`7.0`)** | Es como un cuestionario médico de hasta 4 preguntas de *"sí o no"* que divide a los trabajadores en grupos según su sector, estudios o competencias exigidas por el cargo. | **Debilidad verificada en nuestros datos:** Un árbol corto con pocas variables generales (`7` de competencias o `10` de grupo ISCO, sin las `2,967` ocupaciones específicas) no tiene suficiente detalle para distinguir entre miles de oficios distintos (`Test ROC-AUC = 0.5459` en ISCO y `0.5208` en Educación, `F-033`, `F-034`), y cuando usa los conteos de competencias ESCO (`Árbol 3`, `ROC-AUC = 0.6157`) en realidad actúa como una *"huella digital"* de oficios masivos: el **`86.2 %`** de su mejor hoja (`Hoja 16`, `Lift = 1.766x`) corresponde a un solo oficio (`3343.1 · administrative assistant`), por lo que al validar agrupando por código de ocupación su `ROC-AUC` cae de `0.6183` a **`0.5422`** (`F-035`). |
| `2` | **Naive Bayes Híbrido (`NB-H`, `7.1` · ELEGIDO)** | Es como un analista de seguros que parte de qué tan frecuente es repetir en cada oficio específico y luego suma o resta puntos según la duración del empleo, la etapa de la carrera y el nivel educativo. | **Debilidad verificada en nuestros datos:** Supone que las pistas son independientes entre sí, cuando en nuestros datos **sí existen variables fuertemente relacionadas** (en `F-026`, `n_skills_essential` y `n_skills_competence` tienen correlación `Pearson r = 0.952`, y las variables continuas `dur_q_rob` / `n_skills_essential_rob` coexisten con sus tramos discretizados `dur_q_bin` / `n_skills_essential_bin`). **Efecto medido en `7.1`:** ese doble conteo descalibra las probabilidades brutas y resta un poco de precisión: en la ablación `P7` (`F-038`), quitar las `7` columnas redundantes de competencias ESCO de `NB-H` **sube** el `PR-AUC CV` en **`+0.0040`** (de `0.4981` a `0.5022`), y para corregir el sesgo del umbral hubo que calibrar $\tau^* = 0.2650$ en validación cruzada OOF (`F-037`). |
| `3` | **K-Vecinos Más Cercanos Ponderado (`KNN-W`, `7.2`)** | Es como predecir si alguien volverá a un oficio buscando en el archivo histórico los `101` empleos más parecidos en exactamente la misma ocupación y viendo cuántos de ellos se repitieron. | **Debilidad verificada en nuestros datos:** No aprende una fórmula compacta, sino que en cada predicción debe comparar contra los `1,391,018` empleos de `Train` en `2,978` dimensiones (`fuerza bruta`, porque los árboles `kd_tree` colapsan con `2,967` dummies). En nuestros datos (`F-040`), clasificar las `347,720` filas de `Test` tardó **`29,146.83 segundos` (`~8.10 horas`, `83.82 s` por cada `1,000` filas)**, frente a **`0.241 segundos`** de `NB-H` (`~120,000` veces más lento). Además, si no se multiplica por $w = 8.0$ el peso del oficio (`KNN-D`), el `89.36 %` de los vecinos encontrados pertenecen a oficios distintos (`pureza = 10.64 %`, `F-039`). |
| `4` | **K-Means++ (`8.0` · ELEGIDO)** | Es como colocar `4` puntos de encuentro (centroides) en el mapa de trayectorias laborales y asignar a cada una de las `352,093` personas al perfil promedio que le queda más cerca. | **Debilidad verificada en nuestros datos:** Como traza fronteras esféricas minimizando distancias al cuadrado hacia el promedio, es sensible a valores extremos y no dibuja bordes vacíos cuando los datos forman un continuo: en nuestros datos (`F-043`, `F-044`), las trayectorias laborales son un continuo denso, por lo que la separación global es moderada (`Silhouette = 0.1948` en Personas y `0.2465` en Experiencias) y los outliers de hasta `99` competencias en la Versión A desplazaban los centroides en `0.1105` desviaciones estándar (razón por la cual requirió usar la **Versión B winsorizada por IQR**, que redujo la inercia WCSS de `1,714,084` a `1,692,018`, `F-044`). |
| `5` | **Clustering Jerárquico de Ward (`8.1`)** | Es como construir un árbol genealógico de abajo hacia arriba, uniendo paso a paso las trayectorias más parecidas hasta descubrir cuántas grandes ramas naturales existen en el mercado laboral. | **Debilidad verificada en nuestros datos:** Exige calcular y guardar en memoria la distancia entre **todos los pares posibles de personas** ($\frac{n(n-1)}{2}$ pares en `float64`). En nuestros datos (`F-041`), para las `352,093` personas del censo eso requiere `61,984,564,278` pares = **`495.88 GB` de RAM** (`317.36 GB` para las `281,674` de `Train` y `7,739.72 GB` para las `1,391,018` experiencias), haciendo físicamente imposible correrlo sobre el censo completo en `32 GB` de RAM y obligando a ejecutarlo solo sobre una submuestra de `25,000` personas (`7.10 %` del censo, `2.50 GB` RAM, `146.11 s`). |

---

## 6. Justificación Final con Evidencia de las Dos Elecciones del Equipo: 3 Razones Verificadas, Qué Sacrificamos y Dónde Ganaron los Otros (Sección F)

### 6.1 Elección Supervisada Confirmada por el Equipo: **`HybridNaiveBayes` (`NB-H`, Cuaderno `7.1`)**

> **Distinción explícita ("mejor en los números" vs. "elegido por el equipo"):**  
> En las métricas puras de `Test`, **`KNN-W` (`7.2`) obtuvo el puntaje numérico más alto** (`Test ROC-AUC = 0.7245`, `PR-AUC = 0.5247`, `F1 = 0.5471`, `Brier = 0.1817`). Sin embargo, **el equipo eligió `HybridNaiveBayes` (`NB-H`, `7.1`)** porque captura casi toda esa capacidad discriminante y detecta a más repetidores en su umbral operativo, siendo **`~120,000` veces más rápido en inferencia** y directamente interpretable por probabilidades por oficio.

#### Exactamente 3 Razones Específicas Atadas a Hechos `VERIFIED` (`FACTS.md`)
1. **Detecta a `72.8` de cada `100` experiencias reincidentes en personas nuevas (`Test`), superando ampliamente al baseline trivial (`0` de `100`) y alcanzando el `97.4 %` del `ROC-AUC` del mejor modelo (`KNN-W`) [`F-030`, `F-037`, `F-040`]:**  
   En las `347,720` experiencias de `Test` (`70,419` personas nunca vistas en `Train`), `NB-H` en su umbral OOF $\tau^* = 0.2650$ logra **`Test Recall = 0.7279` (`75,861` repetidores detectados de `104,225`)**, **`Test F1 = 0.5337` `[0.5304, 0.5366]`**, **`Test ROC-AUC = 0.7058` `[0.7033, 0.7083]`** (`96.48 %` del techo logístico `0.7133` y `97.42 %` del `0.7245` de `KNN-W`) y **`Test Brier = 0.1871` `[0.1862, 0.1881]`**.
2. **Clasifica las `347,720` experiencias de `Test` en `0.241 segundos` (`0.283 s` en `7.1`) y entrena sobre `1,391,018` filas en `0.560 segundos` con `118.19 MB` de matriz Train y `1,539.3 MB` de RSS de proceso (`1.54 GB` en `7.1` Celda 15) [`F-036`, `F-037`, `F-040`]:**  
   Gracias a combinar `10` columnas continuas en denso con `2,971` columnas binarias en formato disperso CSR (en lugar de los `~16.6 GB` que exigiría `GaussianNB` denso), `NB-H` ocupa una memoria comparable a `KNN-W` (`121.54 MB` matriz / `1,931.7 MB` RSS), pero es **`120,941` veces más rápido en inferencia que `KNN-W`** (`0.241 s` vs. `29,146.83 s` = `8.10 horas`), permitiendo re-entrenar y evaluar todo el censo en menos de `1 segundo`.
3. **Aprovecha la señal dominante del proyecto —las `2,967` ocupaciones específicas ESCO (`+0.1246` de `PR-AUC`)— con total estabilidad frente a outliers (`|\Delta\text{ROC-AUC}| = 0.0009` entre Versión A y B) [`F-038`]:**  
   La ablación `P7` en `7.1` demostró que el código de ocupación ESCO aporta **`+0.1246` de `PR-AUC`** (frente a `+0.0114` de duración/carrera), y el suavizado `var_smoothing = 1.0` hace que `NB-H` sea prácticamente invariante entre la Versión A (`con_outliers`) y la Versión B (`sin_outliers`: `Test ROC-AUC` cambia de `0.7058` a `0.7067` y `F1` de `0.5337` a `0.5332`).

#### Qué Sacrificamos al Elegir `NB-H` (*What We Gave Up*)
- **Sacrificamos `+1.87` puntos porcentuales de `ROC-AUC` (`0.7058` vs. `0.7245`), `+2.85` puntos de `PR-AUC` (`0.4962` vs. `0.5247`), `+1.34` puntos de `F1` (`0.5337` vs. `0.5471`) y `0.0054` de calibración `Brier` (`0.1871` vs. `0.1817`)** frente a `KNN-W` (`7.2`, diferencia estadísticamente significativa por bootstrap de personas, `F-040`), porque `NB-H` no captura interacciones locales no lineales entre el oficio específico y la duración exacta de cada vecino.
- **Sacrificamos también `+0.75` puntos de `ROC-AUC` (`0.7058` vs. `0.7133`) y `+1.47` puntos de `PR-AUC` (`0.4962` vs. `0.5109`)** frente al techo lineal de `6.0` (`Regresión Logística Regularizada OHE`), debido al supuesto de independencia condicional de Naive Bayes entre variables colineales del bloque denso (`F-026`, `F-038`).

#### Dónde Fueron Mejores las Otras Opciones (*Where the Other Options Were Better*)
- **Dónde ganó `KNN-W` (`7.2`):** Ganó en **todas las métricas de precisión y calibración en `Test`** (`ROC-AUC = 0.7245`, `PR-AUC = 0.5247`, `F1 = 0.5471`, `Precision = 44.59 %`, `Brier = 0.1817`, y a igual tasa de alerta que `NB-H` alcanza `Recall = 76.02 %` y `F1 = 0.5451`, `F-040`), porque comparar contra los `101` vecinos reales del mismo oficio pondera simultáneamente ocupación y duración sin suponer independencia.
- **Dónde ganó el Árbol de Decisión CART (`7.0`, Árbol 3 · Competencias ESCO):** Ganó en **simplicidad visual y aislamiento de reglas puras de alta concentración (`Lift`)**: con solo **`7` variables** y profundidad `4` (`13` hojas, sin usar las `2,967` dummies de oficio), entregó reglas de 4 pasos legibles por cualquier persona y aisló la `Hoja 16` (`E=20, C=19, K=1`) con **`52.94 %` de reincidencia en `Test` (`Lift = 1.766x`**, `F-035`), además de lograr en su modo `None` una exactitud global de **`70.46 %`** que supera estrictamente al baseline de `70.03 %`.
- **Dónde ganó la Regresión Logística Regularizada OHE (`6.0`):** Superó a `NB-H` en discriminación lineal (`ROC-AUC = 0.7133` vs. `0.7058` y `PR-AUC = 0.5109` vs. `0.4962`, `F-030`) porque optimiza conjuntamente los `2,981` pesos con penalización $L_2$ en lugar de estimar cada variable como condicionalmente independiente.

---

### 6.2 Elección de Clustering Confirmada por el Equipo: **`K-Means++` (Cuaderno `8.0`, apoyado por `Ward` `8.1` para validar $k^* = 4$)**

> **Distinción explícita:**  
> El equipo eligió **`K-Means++` (`8.0`)** como método principal de segmentación porque es el **único que escala al `100 %` del censo clasificado (`352,093` personas y `1,738,738` experiencias)** y obtuvo además los **mejores indicadores geométricos internos (`Silhouette`, `Davies-Bouldin` y `Calinski-Harabasz`)**, utilizando el dendrograma de **`Ward` (`8.1`, en submuestra estratificada `n = 25,000`)** como prueba estructural independiente de que el número correcto de grupos es $k^* = 4$ (`DEC-14`).

#### Exactamente 3 Razones Específicas Atadas a Hechos `VERIFIED` (`FACTS.md`)
1. **Segmenta directamente al `100 %` del censo clasificado (`352,093` personas y `1,738,738` experiencias) en `1.80 segundos`, mientras que Ward directo en el censo completo es físicamente imposible (`495.88 GB` de RAM) [`F-041`, `F-043`]:**  
   K-Means++ (`init='k-means++', n_init=10, seed=42`) ajusta sobre las `281,674` personas de `Train` en **`1.80 s`** sin matriz de distancias por pares y asigna sin aproximaciones externas a las `70,419` personas de `Test` (paridad de tamaños entre `Train` y `Test` con diferencia máxima de **`0.21 puntos porcentuales`**: Clúster 0 `43.94 % vs. 43.73 %`, Clúster 1 `11.65 % vs. 11.70 %`, Clúster 2 `27.95 % vs. 28.14 %`, Clúster 3 `16.45 % vs. 16.43 %`, `F-043`).
2. **Alcanza la mejor cohesión y separación geométrica en $k^* = 4$ (`Silhouette = 0.1948` en Personas y `0.2465` en Experiencias; `Davies-Bouldin = 1.6298`; `Calinski-Harabasz = 46,780.83`) y alta estabilidad (`ARI = 0.8633`) [`F-043`, `F-044`]:**  
   Sobre las `352,093` personas, K-Means++ supera a la proyección de Ward `n = 25,000` en `Silhouette` (`0.1948` vs. `0.1167`), `Davies-Bouldin` (`1.6298` vs. `1.9295`, menor es mejor) y `Calinski-Harabasz` (`46,780.83` vs. `3,134.50`), manteniendo una estabilidad de **`ARI = 0.8633`** entre Versión B y Versión A (`0.8557 ± 0.0109` en 5 semillas, `F-044`).
3. **Sus `4` centroides coinciden con exactitud matemática (`diferencia = 0.000000`) con los promedios reales en unidades originales y convergen con Ward `n = 25,000` (`ARI = 0.6502`, `NMI = 0.7296`) en 4 perfiles laborales accionables [`F-043`, `F-044`]:**  
   Los 4 grupos tienen interpretación directa para el Observatorio Laboral y validan post-hoc diferencias reales en reincidencia en `Test` sin haber usado el target: **Clúster 0 · Operativos de Inserción Temprana (`43.90 %`, mayor reincidencia `47.78 %`, `Lift = 1.046x`)**, **Clúster 1 · Educación No Reportada MNAR (`11.66 %`, `100 %` sin título reportado, `dur_mean = 14.12` trim)**, **Clúster 2 · Profesionales Intensivos en Conocimiento (`27.99 %`, `5.98` conocimientos ESCO, menor reincidencia `42.75 %`, `Lift = 0.936x` por movilidad vertical)** y **Clúster 3 · Carreras Largas y Pluriempleo (`16.44 %`, amplitud `112.14` trim = `28 años`, solapamiento `1.61x`)**.

#### Qué Sacrificamos al Elegir `K-Means++` (*What We Gave Up*)
- **Sacrificamos la jerarquía visual de árbol (dendrograma) y la capacidad de descubrir $k^* = 4$ sin fijar $k$ de antemano:** K-Means++ obliga a especificar el número de grupos $k$ como hiperparámetro y no muestra qué subgrupos se fusionan al pasar de $k = 4$ a $k = 3$ o $k = 2$.
- **Sacrificamos fronteras no esféricas y el aislamiento de nichos hiper-puros pequeños:** Como K-Means++ reparte el espacio en celdas de Voronoi esféricas alrededor de los centroides, su Clúster 2 abarca al `27.99 %` del censo con una tasa post-hoc de reincidencia en `Test` de `42.75 %` (`Lift = 0.936x`), menos extrema que el nicho ultra-especializado que aislaba Ward en muestra pequeña (`F-044`).

#### Dónde Fue Mejor el Clustering Jerárquico de Ward (`8.1`) (*Where the Other Option Was Better*)
- **Dónde ganó Ward (`8.1`):**
  1. **Demostración visual y matemática de por qué existen $k^* = 4$ grupos naturales (`F-042`):** El dendrograma de Ward probó que el salto vertical de distancia de fusión cae un **`-85.8 %`** después de $k^* = 4$ (`de 10.060 a 1.431`), una prueba estructural de árbol que K-Means por sí solo no ofrece.
  2. **Mayor contraste post-hoc de reincidencia en el núcleo puro de descubrimiento (`n = 3,000`, `F-044`):** En la muestra inicial de `n = 3,000`, la fusión aglomerativa de Ward aisló un **Clúster 2 ultra-puro de alta especialización cognitiva** (`9.47 %` de personas con `7.69` conocimientos ESCO medios) cuya reincidencia en `Test` bajó hasta **`34.34 %` (`Lift = 0.752x`)**, y un **Clúster 3 de alta rotación** cuya reincidencia subió a **`54.17 %` (`Lift = 1.186x`)**, logrando una brecha post-hoc de **`19.83 puntos porcentuales`** entre clústeres (frente a `5.03 pp` entre `42.75 %` y `47.78 %` en K-Means `8.0`).
