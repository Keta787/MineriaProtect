# Guía Fácil para Todos — Caso 07 (`IDEA-HYB-01`): El gran duelo "¿Interpolar o Ajustar?" (4 métodos probados en 4 tipos de datos reales)

> **Método utilizado:** Competencia controlada entre Regresión Lineal (MCO) y 3 variantes de Lagrange mediante Validación Cruzada (`LOOCV`) y Extrapolación  
> **Nivel de lectura:** Para todo público  
> **Presentación visual interactiva:** Abre [`presentacion_IDEA_HYB_01.html`](./presentacion_IDEA_HYB_01.html) en cualquier navegador.

---

## 1. Resumen en 30 segundos

Ambas clases de Métodos Numéricos comienzan con la misma gran pregunta: **¿cuándo debo trazar una recta de tendencia (Regresión MCO) y cuándo debo construir una curva que pase exacto por los puntos (Interpolación de Lagrange)?**  
En lugar de quedarnos en teoría, montamos un **torneo justo con 4 métodos numéricos compitiendo sobre 4 curvas reales muy distintas** de JobPath (16 duelos en total). El resultado produce una **rúbrica práctica de decisión** clara: *ningún método gana en todo*, y usar Lagrange global sobre datos ruidosos hace explotar el error **108 veces** (`12.32` frente a `0.11`).

---

## 2. ¿Cuál era el problema? (Explicado fácil)

Un error muy común al aprender métodos numéricos es enamorarse de una sola fórmula y aplicarla a todo:
- Si usas una **recta (MCO)** en una curva muy doblada, la recta corta de largo y se equivoca.
- Si usas un **polinomio global de Lagrange** en datos con ruido, la curva serpentea violentamente y se vuelve inútil para predecir.

Necesitábamos un experimento limpio donde los 4 métodos compitieran con las **mismas reglas** tanto **dentro del rango conocido** como **dos pasos hacia el futuro**.

---

## 3. Analogía de la vida real: elegir el zapato correcto para cada terreno

Imagina 4 competencias deportivas distintas: *pista de atletismo recta, camino destapado con piedras, montaña empinada y pista de patinaje lisa*.
- Si llevas patines a un camino con piedras, te caes de inmediato.
- Si llevas botas de montaña a la pista de patinaje, llegas último.

Lo mismo pasa con nuestros **4 métodos**:
1. **Regresión Lineal (MCO):** el rey de las carreteras rectas o con ruido suave.
2. **Lagrange Global Equiespaciado:** el campeón absoluto en pistas lisas y exactas de pocos puntos (como PCA), pero se estrella violentamente en caminos ruidosos.
3. **Lagrange con Nodos de Chebyshev:** excelente todo-terreno para curvas muy empinadas dentro del rango.
4. **Lagrange Local por Tramos (`P₂`):** el más confiable y equilibrado cuando hay ruido o cuando toca asomarse ligeramente fuera del rango.

---

## 4. La solución explicada paso a paso

### Paso 1: Elegir 4 tipos de curvas reales ("los 4 terrenos")
1. **Terreno 1 — Casi lineal y suave:** Habilidades por paso de carrera `mean_skills(k)` (`R² = 0.9955`).
2. **Terreno 2 — Serie macro curva en arco con fluctuación:** Habilidades por año `2000–2017` (`R² = 0.8995`, sube hasta 2015–2016 y desciende en 2017–2019).
3. **Terreno 3 — Curva no lineal empinada:** Supervivencia laboral `S(q)` (`R² = 0.6935`).
4. **Terreno 4 — Tabla matemática exacta y cóncava:** Varianza acumulada PCA `V(k)` (`R² = 0.7964`).

### Paso 2: Cómo calificamos a los 4 métodos sin hacer trampa
Usamos dos exámenes estrictos:
- **Examen 1 (`LOOCV` — Dentro del rango):** Escondemos **un punto interior a la vez**, entrenamos el método sin ver ese punto y medimos qué tan cerca acertó (`RMSE`: mientras más bajo, mejor).
- **Examen 2 (`Extrap +2` — Fuera del rango):** Escondemos los **últimos 2 puntos reales** y vemos qué tanto se equivoca cada método al intentar predecirlos (`MAE`: mientras más bajo, mejor). *(Nota de diseño: en curvas largas `n > 14`, Lagrange Global se acota explícitamente a 13 nodos = grado 12 para medir Runge sin desbordamiento de grado 35, y Chebyshev usa nodos Chebyshev-Lobatto anclados en extremos).*

### Paso 3: La Tabla de Ganadores (Rúbrica práctica)

| Tipo de curva real | 🏆 Ganador dentro del rango (`LOOCV`) | 🏆 Ganador extrapolando +2 pasos | ❌ Peor método en el rango |
| :--- | :--- | :--- | :--- |
| **1. Suave casi lineal** *(Pasos carrera)* | **Regresión Lineal MCO** (`0.0558`) | **Regresión Lineal MCO** (`0.0745`) | Lagrange Global (`0.2937` · y `71.28` al extrapolar!) |
| **2. Serie macro curva** *(Años 2000–2017)* | **Lagrange Local `P₂`** (`0.1139`) | **Lagrange Local `P₂`** (`0.1711`) | Lagrange Global (`12.3239` — **108.2× peor**; `386.4` al extrapolar!) |
| **3. No lineal empinada** *(Supervivencia)* | **Lagrange Local `P₂`** (`0.0524`) | **Lagrange Local `P₂`** (`0.0060`) | Lagrange Global (`0.3777` · `38.89` al extrapolar!) |
| **4. Tabla cóncava exacta** *(PCA)* | **Lagrange Global** (`0.0036`) | **Lagrange Local `P₂`** (`0.0068`) | Regresión Lineal MCO (`0.0765`) |

---

## 5. ¿Por qué se eligió esta solución y no otra?

Porque convierte una discusión teórica en una **guía de bolsillo infalible** respaldada por datos reales:
- ¿Tus datos siguen una tendencia recta y/o tienen ruido? → **Usa MCO** (o `P₂` local si hay ondulaciones suaves).
- ¿Tus datos forman una curva exacta y limpia de pocos puntos (como una tabla matemática o PCA)? → **Usa Lagrange Global**.
- ¿Tu curva es muy empinada y tiene muchos puntos? → **Nunca uses Lagrange Global equiespaciado; usa Chebyshev o `P₂` por tramos**.

---

## 6. Cuidados importantes a tener en cuenta

- Mira lo catastrófico que es extrapolar con Lagrange Global equiespaciado: en la serie anual se equivocó por **386.36 habilidades** (cuando el valor real ronda 23), ¡un error totalmente fuera de escala!

---

## 7. Glosario fácil

- **Validación cruzada Leave-One-Out (`LOOCV`):** Examen justo donde quitas un punto de la tabla, ajustas el modelo con el resto y verificas cuánto se equivoca al adivinar el punto que escondiste; repites eso con cada punto interior.
- **RMSE (Error Cuadrático Medio):** Promedio del tamaño de los errores que castiga más fuerte los errores grandes. Mientras más cercano a `0`, mejor el método.
- **MAE (Error Absoluto Medio):** Promedio simple de cuánto se equivocó el modelo en unidades originales, sin importar si se pasó por arriba o por abajo.
- **Rúbrica de selección:** Regla clara de decisión para saber qué método matemático elegir según cómo se vean tus datos.
