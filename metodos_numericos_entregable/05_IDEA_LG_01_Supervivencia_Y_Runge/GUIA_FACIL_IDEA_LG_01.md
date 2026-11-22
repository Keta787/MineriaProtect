# Guía Fácil para Todos — Caso 05 (`IDEA-LG-01`): ¿Cuánto dura un trabajo y por qué usar demasiados puntos puede arruinar una curva? (Lagrange y Fenómeno de Runge)

> **Método utilizado:** Interpolación Polinomial de Lagrange, Nodos de Chebyshev y Lagrange Local por Tramos (`P₂`)  
> **Nivel de lectura:** Para todo público  
> **Presentación visual interactiva:** Abre [`presentacion_IDEA_LG_01.html`](./presentacion_IDEA_LG_01.html) en cualquier navegador.

---

## 1. Resumen en 30 segundos

Tomamos **1,643,772 empleos finalizados reales** para medir qué porcentaje de personas sigue en el mismo trabajo al cabo de 1, 2, 5 y 10 años (**curva de supervivencia laboral** `S(q)`).  
Con la **Interpolación de Lagrange** demostramos dos cosas sorprendentes:
1. Con solo **4 puntos clave** (1, 2, 5 y 10 años), podemos construir una curva suave que estima la permanencia en cualquier año intermedio sin tener que consultar 1.64 millones de filas.
2. **Más puntos NO siempre es mejor:** Si usamos **17 puntos espaciados por igual** (polinomio de grado 16), la curva se vuelve loca en los bordes (**Fenómeno de Runge**) y predice probabilidades absurdas de **`-248 %`** (error de `2.53`). Pero al elegir inteligentemente los puntos con **nodos de Chebyshev-Lobatto** (que anclan siempre los extremos `q=1` y `q=40`), el error cae **19.4 veces** (a **`0.1301`**) y se logran **0 violaciones `[0 %, 100 %]` en todos los grados (3, 5, 8, 12 y 16)**.

---

## 2. ¿Cuál era el problema? (Explicado fácil)

En informes ejecutivos de talento humano no te entregan una tabla gigante con los 40 trimestres uno por uno; normalmente solo tienes **4 hitos resumidos**:
- Al cumplir **1 año** (`q = 4` trimestres): sigue en el cargo el **66.1 %** de las personas.
- Al cumplir **2 años** (`q = 8` trimestres): sigue el **37.1 %**.
- Al cumplir **5 años** (`q = 20` trimestres): sigue el **13.6 %**.
- Al cumplir **10 años** (`q = 40` trimestres): sigue el **4.3 %**.

El problema tiene dos preguntas:
1. Si alguien pregunta *"¿y qué porcentaje sigue a los 3 años (`q = 12`)?"*, ¿cómo lo calculamos usando solo esos 4 hitos?
2. Si alguien dice *"bueno, para que quede perfecto metamos 17 puntos en un solo polinomio gigante de grado 16"*, ¿de verdad queda mejor o la curva explota?

---

## 3. Analogía de la vida real: una varilla flexible clavada en una pared

Imagina que tienes una varilla elástica de plástico y la obligas a pasar por **4 clavos** en una pared. La varilla dibuja una curva bonita y tranquila entre los 4 clavos.

Ahora imagina que pones **17 clavos** uno tras otro a la misma distancia en una curva que cae muy empinada al principio y luego se aplana. Para poder tocar cada uno de los 17 clavos sin romperse, **la varilla empieza a hacer ondas gigantescas y latigazos violentos cerca de los extremos**.  
- Eso es exactamente el **Fenómeno de Runge** en matemáticas.
- ¿Cómo se arregla? Hay dos soluciones brillantes:
  1. **Nodos de Chebyshev:** poner los clavos más apretados cerca de los extremos para "amarrar" los latigazos.
  2. **Interpolación local por tramos (`P₂`):** en lugar de usar una sola varilla larguísima, usar varios trocitos cortos de varilla de a 3 puntos cada uno.

---

## 4. La solución explicada paso a paso

### Paso 1: Filtrar solo empleos cerrados (regla de oro)
Excluimos los empleos aún vigentes (donde la persona no ha renunciado todavía), quedándonos con **1,643,772 empleos cerrados** para obtener la curva exacta `S(q)` desde `q = 1` (3 meses) hasta `q = 40` (10 años).

### Paso 2: Entender cómo funciona Lagrange con los 4 hitos (`P₃`)
Lagrange construye **4 "interruptores" matemáticos (`L₀, L₁, L₂, L₃`)**, uno para cada hito:
- Cada interruptor vale **1** en su propio hito y **0** en los otros tres (propiedad *delta de Kronecker*).
- En cualquier trimestre intermedio `q`, los cuatro interruptores reparten el peso y **siempre suman exactamente 1** (*partición de la unidad*, verificado hasta `4.44 × 10⁻¹⁶`).
- Su **forma monomial expandida exacta** es: `P₃(q) = -7.9099e-5·q³ + 0.005845·q² - 0.133867·q + 1.107889` (exportada en `lg_monomial_expansions.csv`).
- Al evaluar en **3 años (`q = 12`)**, la fórmula predice **`20.65 %`** (frente al dato real de `25.19 %`, un error de `4.55` puntos porcentuales usando solo 4 números).
- En cambio, si **extrapolamos** fuera del rango hasta los **12 años (`q = 48`)**, el polinomio predice **`-59.84 %`** (una probabilidad negativa imposible).

### Paso 3: El experimento del Fenómeno de Runge (grados 3, 5, 8, 12 y 16)
Probamos qué ocurre cuando subimos el número de puntos de 4 hasta 17 usando las tres estrategias:

| Estrategia en grado 16 | Error máximo (`E∞`) | Predicción mínima | ¿Rompe el rango `[0, 1]` en algún grado 3–16? | Resultado |
| :--- | :---: | :---: | :---: | :--- |
| **Lagrange Global Equiespaciado** | **`2.5262`** (¡252 %!) | **`-2.4827`** (-248 %) | ❌ Sí (`1` violación en g=12 y `2` en g=16) | **Explosión de Runge** en los bordes. |
| **Lagrange con Nodos Chebyshev-Lobatto** | **`0.1301`** | `0.0430` (+4.3 %) | ✅ **No (0 violaciones en TODOS los grados)** | **19.4 veces menos error**; extremos anclados en `1` y `40`. |
| **Lagrange Local por Tramos (`P₂`)** | **`0.1843`** (`0.1196` en g=12) | `0.0430` (+4.3 %) | ✅ **No (0 violaciones en TODOS los grados)** | Muy estable y simple de calcular localmente. |

---

## 5. ¿Por qué se eligió esta solución y no otra?

Porque la curva de permanencia laboral cae muy rápido al inicio (del 100 % al 37 % en solo 2 años) y luego se vuelve casi horizontal. Una recta simple (MCO) no puede doblarse para seguir esa "L" (`R² = 0.69`), mientras que Lagrange con **nodos de Chebyshev** o **por tramos `P₂`** se adapta a la curvatura real sin volverse inestable.

---

## 6. Cuidados importantes a tener en cuenta

- **Nunca extrapolar un polinomio de Lagrange:** Fuera del rango de los nodos (`q < 4` o `q > 40`), el polinomio se dispara rápidamente hacia valores imposibles (como `-59.8 %` en `q = 48`).
- **No-monotonicidad del polinomio cúbico `P₃(q)`:** Aunque la supervivencia real siempre baja, un polinomio cúbico no tiene restricción de monotonía: `P₃` baja a `13.84 %` en `q = 16` y luego rebota hacia arriba a **`20.58 %`** en `q = 28` (cuando el valor real es `8.04 %`).
- **Escalones anuales (*annual heaping*) cada 4 trimestres:** Porque las personas suelen redondear fechas por año completo en sus hojas de vida, la curva real cae a escalones (`q = 3, 6, 10, 14, 18...`), lo que explica por qué incluso Chebyshev-Lobatto y `P₂` mantienen un piso mínimo de error de `0.12–0.18`.
- **Nodos repetidos al redondear (`MR-04`):** Como los trimestres son enteros (`1..40`), al proyectar nodos Chebyshev-Lobatto en grado 16 se deduplican automáticamente a `15` nodos estrictamente distintos para evitar divisiones por cero.

---

## 7. Glosario fácil

- **Curva de supervivencia laboral `S(q)`:** Gráfico que muestra qué fracción de los empleos dura al menos `q` trimestres.
- **Interpolación de Lagrange:** Fórmula que construye el único polinomio que pasa **exactamente** por todos los puntos de una tabla conocida, sin necesidad de resolver sistemas de ecuaciones.
- **Polinomios base `Lᵢ(x)`:** Los "pesos" o interruptores de cada punto conocido; valen 1 en su punto, 0 en los demás, y siempre suman 1.
- **Fenómeno de Runge:** Oscilación gigante y destructiva cerca de los extremos cuando se usa un polinomio de grado muy alto sobre puntos igualmente espaciados.
- **Nodos de Chebyshev:** Posiciones especiales calculadas con cosenos que concentran más puntos hacia los bordes del intervalo para domesticar y eliminar el Fenómeno de Runge.
- **Interpolación local por tramos (`P₂`):** En lugar de un solo polinomio enorme para toda la tabla, se usan parábolas pequeñas de 3 puntos cercanos alrededor del valor que quieres consultar.
