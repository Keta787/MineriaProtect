# Guía Fácil para Todos — Caso 03 (`IDEA-RL-04`): El peligro de predecir el futuro a ciegas (Deriva anual y extrapolación 2000–2027)

> **Método utilizado:** Regresión Lineal (MCO) con centrado de variable y auditoría de extrapolación  
> **Nivel de lectura:** Para todo público  
> **Presentación visual interactiva:** Abre [`presentacion_IDEA_RL_04.html`](./presentacion_IDEA_RL_04.html) en cualquier navegador.

---

## 1. Resumen en 30 segundos

Analizamos cómo evolucionaron los empleos iniciados año tras año durante dos décadas (**2000 a 2019**) y demostramos **dos trampas reales** que arruinan un modelo lineal si no se tiene cuidado:
1. **Mezclar años incompletos al final (2020–2023):** Como casi nadie había registrado empleos tan recientes cuando se capturó la base de datos (apenas 59, 3, 3 y 1 registros), incluir esos 4 años **voltea al revés la tendencia** y desploma el ajuste de **74.8 % a 8.3 %**.
2. **Extrapolar sin freno hacia el futuro:** Calculando la duración estrictamente sobre **empleos cerrados (`~es_vigente`, regla MR-09)** —eliminando así el rebote artificial de 2019— el ajuste en 2000–2019 sube a **`R² = 97.29 %`**; pero si estiramos esa recta hasta el año **2027**, el modelo predice **`-4.96` trimestres** (y ya es negativo desde 2021: `-0.20`)... ¡un empleo que dura tiempo **negativo**, algo físicamente imposible!

---

## 2. ¿Cuál era el problema? (Explicado fácil)

Cuando miramos datos a lo largo del tiempo (del año 2000 al 2023), es muy tentador meter todos los años en la calculadora, sacar una recta y proyectarla hacia el futuro (*"¿cómo serán los empleos en 2027?"*).

Pero los datos reales escondían un problema invisible llamado **censura a la derecha**: la recolección de hojas de vida se cerró alrededor de 2019–2020. Por eso:
- Entre 2000 y 2019 hay decenas de miles de empleos por año (hasta **133,578** en 2012).
- Pero en 2020 solo hay **59**, en 2021 hay **3**, en 2022 hay **3** y en 2023 solo **1**.

Además, quien empezó un trabajo en 2018 simplemente *no ha tenido tiempo calendario* para durar 10 años en él, haciendo que la duración promedio parezca caer en línea recta.

---

## 3. Analogía de la vida real: medir la temperatura de un café

Imagina que mides la temperatura de una taza de café caliente cada minuto durante 10 minutos: baja unos 4 grados por minuto (de 80 °C a 40 °C). Eso sigue una línea recta bastante buena.

- **¿Qué pasa si extrapolas esa recta sin pensar a los 30 minutos?** La fórmula diría que tu café estará a **-40 °C (¡congelado como en el Polo Norte!)**, cuando en realidad el café jamás bajará de la temperatura ambiente de la habitación.
- Exactamente lo mismo le ocurre a nuestra recta de duración laboral en empleos cerrados (`~es_vigente`): entre 2000 y 2019 baja a razón de **`-0.7926` trimestres por año** (`R² = 97.29 %`), así que si la estiras ciegamente hasta **2027**, atraviesa el cero y predice **`-4.96` trimestres**.

---

## 4. La solución explicada paso a paso

### Paso 1: Separar la ventana confiable (2000–2019) de la cola incompleta (2020–2023)
Comparamos dos rectas sobre exactamente las mismas variables:
- **Ventana limpia (2000–2019, 20 años):** Muestra la tendencia real con miles de datos cada año.
- **Serie contaminada (2000–2023, 24 años):** Incluye los 4 años casi vacíos del final.

El impacto de esos 4 puntos extremos fue dramático en la complejidad de habilidades (`mean_skills`):

| Ventana analizada | Pendiente anual (`a₁`) | Ajuste (`R²`) | Qué ocurrió |
| :--- | :---: | :---: | :--- |
| **Soporte válido (2000–2019)** | **+0.0967 skills/año** (Sube) | **74.75 %** (Fuerte) | Los oficios se vuelven gradualmente más exigentes en habilidades. |
| **Con cola censurada (2000–2023)** | **-0.1011 skills/año** (¡Baja!) | **8.26 %** (Destruido) | Solo 4 años con 1 a 59 registros voltearon el signo de la pendiente y arruinaron el modelo. |

### Paso 2: Centrar los años (`t = año - 2000`) para estabilidad numérica
Si usas `x = 2000, 2001, ..., 2019`, la fórmula intenta calcular el valor en el **año 0 (hace dos mil años)**, arrojando interceptos absurdos como `-171.10` o `+1,601.64` y aumentando los errores de redondeo del computador.  
Al cambiar la variable a **`t = año - 2000`** (`t = 0` es el año 2000 y `t = 19` es 2019):
- La pendiente sigue siendo idéntica (`-0.7926` trimestres/año) y `R² = 97.29 %` (`Sy/x = 0.8044`).
- El intercepto ahora tiene sentido real: **`16.44` trimestres** en el año 2000.
- El error numérico frente a `numpy.polyfit` se reduce **más de 4,600 veces** en duración (`1.66e-11 → 3.55e-15`) y **más de 2,000 veces** en `n_starts`.

### Paso 3: Auditar la extrapolación (2020–2027)
Usando la recta limpia sobre empleos cerrados `Duración(t) = 16.4417 - 0.7926 × t`:
- En `t = 20` (año 2020): predice `+0.59` trimestres.
- En `t = 21` (año 2021): ya cruza cero y predice **`-0.20` trimestres** (físicamente imposible).
- En `t = 27` (año **2027**): predice **`-4.9585` trimestres** → **Bandera roja automática: predicción físicamente inválida (`y < 0`)**.

### Paso 4: Verificar que los archivos crudos (`train`, `test`, `val`) no estén sesgados
Revisamos los **1,993,291 registros originales** en las tres particiones crudas (`train`, `test`, `val`) y comprobamos que las tres tienen exactamente la misma tendencia temporal (`+0.181 %` a `+0.186 %` por año), probando que el fenómeno viene del calendario real y no de un error al dividir los datos.

---

## 5. ¿Por qué se eligió esta solución y no otra?

Porque demuestra con números reales **dos lecciones fundamentales de Métodos Numéricos**:
1. **No basta con ajustar una recta:** primero hay que inspeccionar el soporte válido de los datos y centrar el eje horizontal cuando los valores son grandes (como años 2000+).
2. **La extrapolación lineal tiene límites físicos:** nunca debes confiar en una predicción fuera del rango sin validar si la realidad permite seguir bajando o subiendo en línea recta.

---

## 6. Cuidados importantes a tener en cuenta

- **Efecto calendario y filtro `~es_vigente` (`MR-09`):** Excluir empleos vigentes (imputados a `2026-Q1`) elimina el salto anómalo que antes inflaba 2019 a `8.31` trimestres (frente a `2.27` real en cerrados). Aun así, la caída de `-0.79` trimestres/año refleja principalmente el menor horizonte de tiempo calendario disponible para empleos iniciados cerca del cierre del dataset.

---

## 7. Glosario fácil

- **Deriva temporal (drift):** Cambio gradual que sufren los datos a medida que pasan los años.
- **Censura a la derecha:** Cuando los registros más recientes están incompletos o "cortados" porque todavía no ha pasado suficiente tiempo al momento de tomar la foto de los datos.
- **Centrado de variable (`t = año - 2000`):** Mover el punto cero de la gráfica hacia el inicio de tus datos para que los números sean más fáciles de interpretar y el computador calcule con mucha mayor precisión.
- **Extrapolación físicamente inválida:** Cuando una fórmula matemática produce una respuesta imposible en el mundo real (como edades, distancias o duraciones de empleo negativas).
