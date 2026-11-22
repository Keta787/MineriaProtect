# Guía Fácil para Todos — Caso 06 (`IDEA-LG-02`): ¿Cuántas variables resumidas (PCA) necesitas para conservar el 90 % de la información? (Lagrange Directa e Inversa)

> **Método utilizado:** Interpolación de Lagrange Directa `V(k)` e Interpolación Inversa `k(V*)`  
> **Nivel de lectura:** Para todo público  
> **Presentación visual interactiva:** Abre [`presentacion_IDEA_LG_02.html`](./presentacion_IDEA_LG_02.html) en cualquier navegador.

---

## 1. Resumen en 30 segundos

En minería de datos se usa una técnica llamada **PCA** para resumir muchas columnas numéricas en unas pocas "super-columnas" (componentes `k = 1, 2, ..., 10`). Normalmente uno sabe cuánta información guarda cada componente, pero la pregunta real del equipo suele ser al revés: *"Si quiero conservar exactamente el **80 %, 85 %, 90 % o 95 %** de la información, ¿cuántos componentes debo elegir?"*  
Usando **Interpolación de Lagrange Directa e Inversa**, respondimos ambos sentidos con errores mínimos (`0.0002` en `k = 4`) y demostramos en vivo por qué el algoritmo bloquea automáticamente una trampa matemática oculta: cuando dos componentes tienen exactamente el mismo `100 %` acumulado (`V(9) = V(10) = 1.0`), invertir la tabla causaría una **división por cero**.

---

## 2. ¿Cuál era el problema? (Explicado fácil)

Imagina que estás empacando una maleta con 10 compartimentos ordenados por importancia (eso es la varianza acumulada de PCA):
- Con 1 componente guardas el **32.9 %** de la información (Versión A) o **39.7 %** (Versión B).
- Con 3 componentes guardas el **76.6 %** (Versión A) o **80.6 %** (Versión B).
- Con 5 componentes guardas el **94.1 %** (Versión A) o **95.4 %** (Versión B).
- Con 9 y 10 componentes en la Versión A ya tienes el **100.0 %** exacto en ambos (porque una columna era suma exacta de otras, así que el 10.º componente no aporta nada nuevo).

Teníamos tres retos concretos:
1. **Sentido directo:** Si solo conociéramos 4 filas de la tabla (`k = 1, 3, 5, 8`), ¿qué tan bien reconstruye Lagrange las filas faltantes (`k = 2, 4, 6, 7`)?
2. **Sentido inverso:** Dar la vuelta a los ejes para preguntar: *"Quiero **90 %** de varianza → ¿cuál es el número exacto `k`?"*
3. **Protección contra división por cero (`MR-04`):** Comprobar qué sucede si intentamos invertir toda la tabla incluyendo `k = 9` y `k = 10` cuando ambos valen `1.0`.

---

## 3. Analogía de la vida real: el medidor de batería al revés

Piensa en cargar la batería de tu celular:
- **Pregunta directa:** *"Llevo **40 minutos** cargando, ¿en qué porcentaje de batería voy?"* → Conoces el tiempo (`k`) y buscas el porcentaje (`V`).
- **Pregunta inversa (Lagrange inversa):** *"Necesito salir con exactamente **90 % de batería**, ¿cuántos minutos debo cargarlo?"* → Ahora el porcentaje (`V*`) entra como dato y el tiempo (`k`) es la respuesta.

¿Y cuál es la trampa del `100 %`? Una vez la batería llega al **100 %** a los 90 minutos, a los 100 minutos sigue en **100 %**. Si le preguntas al teléfono *"¿en qué minuto exacto llegué al 100 %?"*, hay dos respuestas distintas para el mismo `100 %` (90 y 100 min). En la fórmula de Lagrange eso produce un denominador `100 % - 100 % = 0`, y dividir por cero rompe cualquier cálculo. Por eso solo se invierte en el tramo donde la carga **siempre está subiendo** (`k = 1..6`).

---

## 4. La solución explicada paso a paso

### Paso 1: Interpolación directa (`P₃`) desde solo 4 nodos (sobre PCA 50k recomputado en vivo)
Recomputamos el PCA 50k directamente desde `data/03_processed` en precisión completa `float64` (sin constantes fijas copiadas a mano). Usando solo `k = {1, 3, 5, 8}` construimos el polinomio cúbico de Lagrange —cuya **forma monomial expandida** en Versión A es `P₃(k) = 0.002746·k³ - 0.057466·k² + 0.412549·k - 0.028723`— y lo probamos en los componentes ocultos `k = 2, 4, 6, 7`:
- En `k = 4` (Versión A), el valor real era **`0.8776`** y Lagrange predijo **`0.8778`** — ¡un error de apenas **0.00017 (menos de dos diezmilésimas)**!
- En todos los puntos evaluados, el error fue menor a `0.035` y los pesos base sumaron exactamente `1.0000`.

### Paso 2: Interpolación inversa `k(V*)` en el tramo estrictamente creciente (`k = 1..6`)
Intercambiamos los ejes `(x = Varianza acumulada V, y = Componentes k)` y calculamos cuántos componentes continuos se requieren para llegar a cada meta, redondeando hacia arriba (`ceil`) para elegir un número entero real de componentes:

| Meta de información (`V*`) | Versión A (Con outliers): `k` estimado → Recomendado | Varianza real lograda (A) | Versión B (Sin outliers IQR): `k` estimado → Recomendado | Varianza real lograda (B) |
| :---: | :---: | :---: | :---: | :---: |
| **80 %** (`0.80`) | `3.20` → **4 comp.** | `87.76 %` ✅ | `2.94` → **3 comp.** | `80.58 %` ✅ |
| **85 %** (`0.85`) | `3.66` → **4 comp.** | `87.76 %` ✅ | `3.47` → **4 comp.** | `89.09 %` ✅ |
| **90 %** (`0.90`) | `4.33` → **5 comp.** | `94.07 %` ✅ | `4.10` → **5 comp.** | `95.36 %` ✅ |
| **95 %** (`0.95`) | `5.16` → **6 comp.** | `99.43 %` ✅ | `4.92` → **5 comp.** | `95.36 %` ✅ |

**Hallazgo práctico:** Al limpiar outliers con IQR (Versión B), la información se compacta más rápido: necesitas **1 componente menos** para alcanzar tanto el **80 %** (3 en lugar de 4) como el **95 %** (5 en lugar de 6).

### Paso 3: Prueba de la barrera de seguridad (`MR-04`)
Probamos a propósito meter los 10 puntos de la Versión A en `inverse_lagrange_eval`. Como `V(9) = 1.0` y `V(10) = 1.0`, la función `validate_distinct_nodes()` detectó el empate inmediatamente y detuvo el cálculo con un error controlado en lugar de devolver números falsos (`NaN` o infinito).

---

## 5. ¿Por qué se eligió esta solución y no otra?

Porque la tabla de varianza acumulada de PCA es **exacta, libre de ruido aleatorio y suavemente cóncava**. Ese es precisamente el escenario soñado para la **Interpolación de Lagrange**: no queremos suavizar ruido (como en MCO), sino respetar exactamente los valores de la tabla de PCA y poder consultarla al derecho y al revés.

---

## 6. Cuidados importantes a tener en cuenta

- **Condición obligatoria para invertir:** Una tabla solo se puede interpolar al revés en una zona **estrictamente creciente (o estrictamente decreciente)** sin mesetas planas ni valores repetidos.

---

## 7. Glosario fácil

- **PCA (Análisis de Componentes Principales):** Técnica que comprime muchas variables originales en unos pocos "componentes" que conservan la mayor parte de la información.
- **Varianza explicada acumulada `V(k)`:** Porcentaje total de información original que logras conservar al quedarte con los primeros `k` componentes.
- **Interpolación inversa:** Darle la vuelta a la tabla (usar `y` como entrada y `x` como salida) para averiguar qué valor de entrada te da una meta deseada.
- **Colinealidad exacta / Meseta de rango 9:** Cuando una de tus 10 columnas se puede calcular exactamente sumando otras; entonces el 10.º componente no aporta nada (`0 %`) y la curva llega al `100 %` en el componente 9.
- **Guarda de nodos distintos (`MR-04`):** Verificación obligatoria antes de aplicar Lagrange que asegura que ningún par de puntos tenga la misma coordenada `x`, evitando divisiones por cero.
