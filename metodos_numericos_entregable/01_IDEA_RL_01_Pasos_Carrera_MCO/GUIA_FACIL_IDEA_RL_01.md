# Guía Fácil para Todos — Caso 01 (`IDEA-RL-01`): ¿Cómo cambia tu perfil laboral conforme avanzas de trabajo en trabajo?

> **Método utilizado:** Regresión Lineal por Mínimos Cuadrados Ordinarios (MCO)  
> **Nivel de lectura:** Para todo público (no necesitas saber matemáticas avanzadas)  
> **Presentación visual interactiva:** Abre [`presentacion_IDEA_RL_01.html`](./presentacion_IDEA_RL_01.html) en cualquier navegador.

---

## 1. Resumen en 30 segundos

Analizamos **1,738,738 experiencias laborales reales** para responder una pregunta muy simple: *cuando una persona pasa de su primer empleo al segundo, tercero y así hasta el décimo, ¿los puestos que ocupa exigen más habilidades, duran más o menos tiempo, o repiten el mismo oficio?*  
Usando **Regresión Lineal (una recta que resume la tendencia promedio)**, descubrimos una tendencia casi perfecta (**99.55 % de ajuste**): con cada nuevo empleo, el puesto exige en promedio **+0.225 habilidades esenciales adicionales** (validado también por mínimos cuadrados ponderados WLS: **+0.229**, diferencia de apenas `1.67 %`), la probabilidad de repetir oficio sube **+2.13 puntos porcentuales**, y la duración promedio de **empleos cerrados (`~es_vigente`, regla MR-09)** baja **-0.86 trimestres** por paso (`R² = 92.33 %`).

---

## 2. ¿Cuál era el problema? (Explicado fácil)

Imagina que tienes un archivo gigantesco con casi **dos millones de empleos** de más de 355,000 personas. Si miras esos datos fila por fila, es imposible ver un patrón: algunas personas cambian de trabajo cada 6 meses, otras duran 10 años, unas tienen oficios muy complejos y otras muy sencillos.

El reto era **resumir todo ese mar de datos en reglas claras y medibles** que respondan:
1. ¿A medida que alguien suma empleos (paso 1, paso 2, ..., paso 10), entra a cargos que piden más competencias?
2. ¿Se vuelve más probable que repita un oficio similar al que ya tuvo?
3. ¿Qué pasa si intentamos usar esa misma recta para predecir qué ocurrirá en el empleo número 12 o 15 (fuera del rango usado para calcular la recta)?

---

## 3. Analogía de la vida real: la regla transparente sobre puntos en una hoja

Imagina que anotas en un cuaderno la estatura promedio de niños desde los 1 hasta los 10 años y dibujas un punto por cada edad. Los puntos casi forman una línea recta, pero no están alineados con perfección milimétrica porque cada niño crece un poquito distinto.

- **¿Qué hace la Regresión Lineal por Mínimos Cuadrados (MCO)?** Coloca una **regla transparente** sobre esos puntos de forma que la suma de las distancias al cuadrado (los "errores" o saltitos verticales de cada punto hasta la regla) sea **lo más pequeña posible**.
- Así, en vez de memorizar diez números sueltos, obtienes una **receta de dos números**: dónde empiezas (*intercepto* `a₀`) y cuánto subes o bajas en cada escalón (*pendiente* `a₁`).

---

## 4. La solución explicada paso a paso

### Paso 1: Ordenar la historia laboral de cada persona
Tomamos las experiencias válidas de cada hoja de vida y las pusimos en orden cronológico: *Empleo 1, Empleo 2, Empleo 3... hasta el Empleo 10*.

### Paso 2: Calcular el promedio de cada escalón
Para cada escalón (del 1 al 10), promediamos cuatro cosas:
- **Complejidad del oficio (`mean_skills`):** cuántas habilidades esenciales pide ese cargo en el catálogo europeo ESCO.
- **Reincidencia (`reincide_rate`):** qué porcentaje de personas vuelve a un oficio que ya había tenido.
- **Duración (`mean_dur_q`):** cuántos trimestres (bloques de 3 meses) dura en promedio ese empleo.
- **Empleo verde (`mean_green`):** qué porcentaje del oficio corresponde a tareas ambientales o sostenibles.

### Paso 3: Trazar la mejor recta (MCO)
Con las ecuaciones cerradas de mínimos cuadrados obtuvimos para las **habilidades esenciales del puesto**:

> **Habilidades estimadas = 22.5160 + 0.2250 × (Número de empleo)**

¿Qué significa esto en español cotidiano?
- El punto de partida teórico (paso 0) es **22.52 habilidades**.
- Por cada empleo adicional que avanza una persona (del 1 al 2, del 2 al 3...), el cargo promedio que ocupa requiere **+0.225 habilidades esenciales más**.
- La recta pasa exactamente por el **centro de equilibrio (centroide)**: en el paso **5.5**, el promedio es **23.75 habilidades**.

### Paso 4: Leer la tabla de resultados en lenguaje humano

| Pregunta que hicimos | Cambio por cada empleo nuevo (`a₁`) | Qué tan buena es la recta (`R²`) | Traducción en palabras simples |
| :--- | :---: | :---: | :--- |
| **¿El oficio exige más habilidades?** | **+0.225 habilidades** | **99.55 %** (Excelente) | Los puntos siguen casi una línea recta perfecta hacia arriba. |
| **¿Se repite más el mismo oficio?** | **+2.13 % por paso** | **96.25 %** (Excelente) | Con el tiempo la gente se especializa y vuelve a roles similares. |
| **¿Cuánto dura cada empleo cerrado (`~es_vigente`)?** | **-0.86 trimestres** (~2.6 meses menos) | **92.33 %** (Excelente) | Al excluir empleos aún abiertos (`MR-09`), los empleos avanzados muestran una baja limpia y sostenida en duración. |
| **¿Aumentan los empleos verdes?** | **-0.02 % por paso** | **78.77 %** (Bueno) | El cambio global es diminuto —¡y ojo: al controlar por cohorte `≥ 10` empleos el signo se invierte a `+0.018 %` (Paradoja de Simpson)! |

### Paso 5: Probar la recta fuera de su zona segura (Extrapolación)
Entrenamos la recta solo con los empleos **1 al 10**, y luego probamos qué tan bien adivina los empleos **11, 12 y 15**:
- En **habilidades del oficio**, la predicción fue sorprendentemente buena: para el empleo 12 la recta predijo **25.22** y el dato real fue **25.19** (un error mínimo de apenas **0.023**).
- En cambio, en **duración de empleos cerrados**, la recta falló fuerte: para el empleo 15 predijo **0.39 trimestres**, cuando el valor real era **4.26 trimestres** (error de **3.87 trimestres**). **Lección clave:** *extrapolar fuera del rango siempre conlleva peligro si el comportamiento deja de ser recto.*

---

## 5. ¿Por qué se eligió esta solución y no otra?

- **¿Por qué Regresión Lineal y no conectar punto por punto (Interpolación)?** Porque aquí tenemos datos reales con pequeñas variaciones aleatorias ("ruido"). Si forzáramos una curva a pasar exacto por cada punto, solo copiaríamos pequeñas sacudidas del azar en lugar de capturar la tendencia real de subida (+0.225 habilidades por paso).
- **Verificación doble:** Comparamos nuestras cuentas manuales con `numpy.polyfit` y con **GeoGebra Classic**, y la diferencia fue de **3.55 × 10⁻¹⁵** (quince ceros después del punto decimal: ¡exactitud total!).

---

## 6. Cuidados importantes para no malinterpretar los resultados

1. **Tendencia no significa causa:** Que las personas en su 8.º empleo ocupen puestos más complejos no significa que *cambiar de trabajo mágicamente te haga saber más*; también puede ocurrir que quienes ascienden cambian de rol más seguido.
2. **Mide lo que pide el oficio, no a la persona:** El número `mean_skills` viene del catálogo ESCO del cargo ocupado, no de un examen aplicado al trabajador.
3. **Paradoja de Simpson y sesgo de supervivencia:** En el empleo 1 hay **352,093** personas, mientras que al empleo 10 llegan **25,321** (13.9× menos). Al repetir el cálculo **solo** con la cohorte fija de personas que tienen `≥ 10` empleos:
   - La subida de habilidades se mantiene muy fuerte (**R² = 95.29 %**, `a₁ = +0.203`).
   - En cambio, en **`mean_green`** ocurre la **Paradoja de Simpson** (la pendiente se invierte de `-0.000219` en el universo a **`+0.000183`** dentro de la cohorte fija) y en **`reincide_rate`** el ajuste cae de `96.25 %` a **`44.75 %`** (`a₁`: `+2.13 %` → `+0.72 %`), evidenciando el sesgo mecánico de calcular reincidencia sobre toda la trayectoria.
4. **Control por pesos (WLS) y censura (`MR-09`):** Verificamos con Mínimos Cuadrados Ponderados (dando más peso a pasos con más registros) que la pendiente de `mean_skills` apenas varía `1.67 %` (`+0.2287` vs. `+0.2250`), y calculamos `mean_dur_q` exclusivamente sobre empleos cerrados (`~es_vigente`) para mantener consistencia total con `IDEA-LG-01` e `IDEA-RL-04`.

---

## 7. Glosario fácil (para entender cada término sin miedo)

- **Regresión Lineal (MCO):** Método matemático que encuentra la línea recta que mejor resume la tendencia de una nube de puntos, haciendo lo más pequeña posible la suma de los errores al cuadrado.
- **Pendiente (`a₁`):** Cuánto sube (si es positiva) o baja (si es negativa) la recta cada vez que avanzas 1 paso en el eje horizontal.
- **Intercepto (`a₀`):** El valor teórico donde la recta corta el eje vertical cuando el paso vale 0.
- **Residuo (`eᵢ`):** La pequeña diferencia vertical entre el valor real observado y el valor que predijo nuestra recta.
- **Coeficiente de determinación (`R²`):** Una "nota" de 0 % a 100 % (o de 0 a 1) que dice qué tan bien explica nuestra recta el comportamiento real de los datos. Un `R² = 0.9955` equivale a un 99.55 % de ajuste.
- **Centroide (`x̄, ȳ`):** El punto promedio exacto por donde **siempre** pasa la recta de mínimos cuadrados.
- **Extrapolación:** Usar la recta para predecir valores **fuera** del rango con el que fue construida (por ejemplo, predecir el empleo 15 con una recta hecha del 1 al 10).
