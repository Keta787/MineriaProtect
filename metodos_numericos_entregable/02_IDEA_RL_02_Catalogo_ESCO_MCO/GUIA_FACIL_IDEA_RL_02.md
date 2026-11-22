# Guía Fácil para Todos — Caso 02 (`IDEA-RL-02`): ¿Cuántas habilidades de un oficio te sirven en otros sectores? (y cuándo decir "esta recta NO sirve")

> **Método utilizado:** Regresión Lineal (MCO) y criterio honesto de rechazo de modelos débiles  
> **Nivel de lectura:** Para todo público  
> **Presentación visual interactiva:** Abre [`presentacion_IDEA_RL_02.html`](./presentacion_IDEA_RL_02.html) en cualquier navegador.

---

## 1. Resumen en 30 segundos

Estudiamos el catálogo oficial europeo de oficios **ESCO v1.2.1**, que contiene **3,039 ocupaciones** y **126,051 vínculos con habilidades**. Con Regresión Lineal (MCO) comprobamos dos cosas igual de valiosas:
1. **Cuándo sí existe una regla clara:** Por cada habilidad nueva que tiene un oficio, en promedio **58 % (`a₁ = 0.5786`) es transferible a otros sectores** (llegando hasta **74 %** en gerentes).
2. **Cuándo hay que ser honestos y rechazar la recta:** Intentar predecir si un oficio es "verde" (ambiental) o cuántas habilidades opcionales tiene a partir de sus habilidades esenciales da un ajuste de prácticamente **0 % (`R² ≈ 0.0000`)**. En métodos numéricos, **saber rechazar un mal modelo es tan importante como encontrar uno bueno**.

---

## 2. ¿Cuál era el problema? (Explicado fácil)

Las personas suelen hacer dos suposiciones sobre el mundo laboral sin comprobarlas con datos:
- *"Si un trabajo exige muchas habilidades, seguramente casi todas sirven solo para esa industria cerrada."*
- *"Los empleos ecológicos o verdes seguro son simplemente los empleos que piden más habilidades en total."*

Necesitábamos usar los 3,039 oficios reales del catálogo ESCO para **poner a prueba qué relaciones sí siguen una línea recta útil y cuáles NO tienen ninguna relación lineal**, evitando caer en la trampa de presentar una recta engañosa solo porque el computador siempre puede dibujar una.

---

## 3. Analogía de la vida real: la caja de herramientas de un técnico

Piensa en las herramientas que lleva un electricista, un carpintero o un chef en su maletín:
- Algunas herramientas sirven en **casi cualquier oficio** (un destornillador, una libreta, trabajo en equipo): esas son las **habilidades transferibles entre sectores (`cross-sector`)**.
- Otras solo sirven en un nicho muy específico (un equipo de soldadura submarina).

Lo que hicimos con MCO fue revisar **3,039 maletines distintos** y preguntar: *"Si un maletín es más grande (tiene más herramientas en total), ¿cuántas de las herramientas extra sirven en otros trabajos?"*  
La respuesta promedio fue **casi 6 de cada 10 herramientas (`0.58`)**.  
En cambio, preguntar *"¿Si el maletín es más grande significa que el trabajo es ecológico?"* es como preguntar si las personas más altas tienen carros más verdes: **una cosa no tiene nada que ver con la otra (`R² = 0.00004`)**.

---

## 4. La solución explicada paso a paso

### Paso 1: Contar las "piezas" de cada uno de los 3,039 oficios
Para cada ocupación del catálogo ESCO contamos cuántas relaciones tiene de cada tipo: habilidades esenciales, opcionales, prácticas, conocimientos teóricos, habilidades transferibles entre sectores (`cross-sector`), específicas de un sector y porcentaje de tareas verdes (`greenShare`).

### Paso 2: Evaluar 7 parejas de variables con la regla del semáforo de `R²`
Aplicamos un criterio objetivo para juzgar cada recta:
- 🟢 **Ajuste Fuerte (`R² ≥ 0.70`):** La recta explica muy bien la relación.
- 🟡 **Ajuste Moderado (`0.30 ≤ R² < 0.70`):** Hay tendencia real, pero con bastante variación alrededor de la recta.
- 🔴 **Modelo Rechazado (`R² < 0.30`):** La recta **no sirve** para predecir; los puntos son una nube dispersa sin dirección lineal.

### Paso 3: Qué descubrimos en los datos reales

| Relación probada | Pendiente (`a₁`) | Ajuste (`R²`) | Veredicto honesto | Explicación cotidiana |
| :--- | :---: | :---: | :---: | :--- |
| **Habilidades prácticas → Total esenciales** | `+1.1227` | **86.43 %** | 🟢 Fuerte | Por cada habilidad práctica esencial, el oficio suma en promedio ~0.12 conocimientos teóricos extra. |
| **Habilidades totales → Transferibles (`cross-sector`)** | `+0.5786` | **56.70 %** | 🟡 Moderado | Cerca del **58 %** de cada habilidad extra de un oficio se puede llevar a otros sectores. |
| **Esenciales → Opcionales** | `+0.1472` | **1.40 %** | 🔴 **Rechazado** | Tener muchas habilidades obligatorias NO predice cuántas opcionales tiene el cargo. |
| **Esenciales → Porcentaje Verde (`greenShare`)** | `-0.00005` | **0.004 %** | 🔴 **Rechazado** | Que un trabajo sea "verde" es totalmente independiente de cuántas habilidades pida. |

### Paso 4: Comparar los 10 grandes grupos de ocupaciones (ISCO-08)
Separamos los 3,039 oficios en sus **10 grandes familias** y vimos diferencias fascinantes en qué tanto se transfieren sus habilidades:
- **Los más transferibles:** *Gerentes (`Managers`)* con **74.0 %** (`a₁ = 0.7403`, `R² = 0.754`) y *Fuerzas Armadas* con **71.5 %** (`R² = 0.922`).
- **Los más cerrados o especializados:** *Ocupaciones elementales* (**31.3 %**) y *Agricultura, silvicultura y pesca* (**33.3 %**).

---

## 5. ¿Por qué se eligió esta solución y no otra?

Porque este caso valida una regla de oro de la clase de Métodos Numéricos: **la fórmula de mínimos cuadrados SIEMPRE arroja una recta, incluso cuando los datos son puro desorden.**  
Si un analista mira solo la ecuación y olvida revisar `R²` y el gráfico de dispersión, cometería el error grave de afirmar que encontró una fórmula para predecir empleos verdes. Aquí mostramos en vivo tanto los modelos exitosos como los rechazados.

---

## 6. Cuidados importantes a tener en cuenta

- **Relación parte-todo:** En el par con mayor ajuste (`86.43 %`), las habilidades prácticas son una *parte* del total de habilidades esenciales. Por eso su pendiente mayor a 1 (`1.1227`) se interpreta correctamente como el "acompañamiento" de conocimientos teóricos que suele venir con cada habilidad práctica.
- **Promedios vs. oficios individuales (y advertencia `MR-06` en GeoGebra):** Cuando resumimos los 3,039 oficios en solo 10 promedios (uno por gran grupo ISCO-08) para verificarlo en **GeoGebra**, el `R²` cae a **`0.2800` (< 0.30, modelo rechazado)** porque la agricultura (ISCO-6) tiene muchas habilidades totales (`46.59`) pero muy pocas transferibles (`12.30`, residuo de **`-11.33`**). Por eso el punto `Q_pred = (45, 22.93)` del script de GeoGebra se usa **solo para comprobar aritméticamente la fórmula MCO contra Python**, nunca como pronóstico operativo válido.

---

## 7. Glosario fácil

- **Catálogo ESCO:** Diccionario oficial europeo que lista más de 3,000 profesiones y las habilidades exactas asociadas a cada una.
- **Grupos ISCO-08:** Las 10 grandes categorías internacionales que agrupan todos los trabajos (gerentes, profesionales, técnicos, operarios, agricultura, etc.).
- **Habilidad `cross-sector` (intersectorial):** Habilidad que te sirve aunque cambies completamente de industria (por ejemplo, gestionar presupuestos o analizar datos).
- **Ortogonalidad / Independencia:** Cuando dos variables no tienen relación lineal entre sí (`R² ≈ 0`): conocer una no te ayuda a adivinar la otra.
- **Rechazo honesto de modelo:** Decisión técnica de descartar una recta cuando su `R²` es muy bajo (`< 0.30`), evitando predicciones falsas.
