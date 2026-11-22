# Guía Fácil para Todos — Caso 04 (`IDEA-RL-05`): ¿Qué pasa con la recta cuando hay datos extremos (outliers) o cuando cambias las unidades?

> **Método utilizado:** Regresión Lineal (MCO), análisis de sensibilidad a atípicos (4 vías) y teorema de invarianza afín  
> **Nivel de lectura:** Para todo público  
> **Presentación visual interactiva:** Abre [`presentacion_IDEA_RL_05.html`](./presentacion_IDEA_RL_05.html) en cualquier navegador.

---

## 1. Resumen en 30 segundos

En ciencia de datos siempre surgen dos dudas prácticas antes de entrenar un modelo: *(1) ¿Qué hago con los datos exageradamente altos o bajos (outliers): los dejo, los recorto o borro esas filas?* y *(2) Si cambio la escala de los números (por ejemplo, escalándolos con `RobustScaler`), ¿daño la calidad de la regresión?*  
Sobre **1,738,738 empleos reales** probamos **4 estrategias** y demostramos dos resultados clave:
1. **Recortar extremos suavemente (winsorización IQR)** reduce el error típico de la recta en **-21.9 %** (`Sy/x` baja de `4.09` a `3.19`) **sin borrar ni una sola persona** de la base de datos.
2. **Cambiar de escala no altera la calidad real:** El ajuste `R²` permanece **100 % idéntico hasta 13 cifras decimales** (error máximo de `7.22 × 10⁻¹⁴`), y la pendiente y el intercepto se transforman con una fórmula algebraica exacta.

---

## 2. ¿Cuál era el problema? (Explicado fácil)

El método de Mínimos Cuadrados eleva cada error al **cuadrado** (`e²`). Eso tiene una consecuencia muy importante: si un dato está 10 veces más lejos de lo normal, su peso en el cálculo es **100 veces mayor** (`10² = 100`), jalando la recta hacia él como un imán.

En nuestro proyecto existían **cuatro versiones distintas de los datos** y además una capa escalada gigante (`04_transformed`, con archivos de 2 a 8 GB):
- **Versión A:** Todos los datos originales con sus valores extremos reales.
- **Versión B:** Todos los registros conservados, pero "topando" los valores extremos con el método IQR (winsorización).
- **Flujo legado limpio** y **flujo legado con borrado de filas** (que eliminaba **33,359** registros).

Necesitábamos medir exactamente cuánto cambia la recta entre esas 4 opciones y probar matemáticamente si escalar las variables con `RobustScaler` altera la relación entre ellas.

---

## 3. Analogía de la vida real: cambiar de pesos a dólares y pesar personas con un gigante en la sala

1. **Sobre los valores extremos (outliers):** Imagina calcular el sueldo promedio en un salón de 30 estudiantes... y entra un multimillonario. Si **borras** al multimillonario pierdes un registro real; si lo **dejas tal cual**, el promedio se dispara y no representa a nadie; si aplicas **winsorización**, mantienes a los 31 asistentes pero "topas" su cifra al límite superior razonable para que no distorsione el error típico.
2. **Sobre la invarianza de escala:** Medir la estatura y el peso de 1,000 personas en **centímetros y kilos** frente a medirlos en **pulgadas y libras** cambia los números de la pendiente y el intercepto, pero **NO cambia qué tan relacionadas están la estatura y el peso**. Su `R²` sigue siendo exactamente el mismo.

---

## 4. La solución explicada paso a paso

### Parte A: Comparación de las 4 estrategias frente a datos atípicos (en dos pares de variables)
Ajustamos la recta que predice el total de habilidades esenciales (`n_skills_essential`) primero a partir de **competencias prácticas** (`n_skills_competence`) y luego a partir de **conocimientos teóricos** (`n_skills_knowledge`):

| Versión del dataset | Registros (`n`) | Par `competence → essential` (`a₁` / `R²` / `Sy/x`) | Par `knowledge → essential` (`a₁` / `R²` / `Sy/x`) | Conclusión práctica |
| :--- | :---: | :---: | :---: | :--- |
| **Versión A (Con outliers reales)** | 1,738,738 (100 %) | `1.1279` / `90.72 %` / `4.0872` | `1.8827` / `36.80 %` (Mod.) / `10.6664` | Conserva todo el universo, pero los extremos inflan `Sy/x`. |
| **Versión B (Winsorizada IQR)** | 1,738,738 (100 %) | `1.0868` / `89.83 %` / **`3.1915`** | `1.6728` / **`27.95 %` (Rech.)** / **`8.4934`** | Baja `Sy/x` (**-21.9 %** y **-20.4 %**) sin borrar filas, pero en `knowledge` comprime la cola (`45 → 13.5`) y baja `R²` debajo de `30 %`. |
| **Legado limpio (`test+val`)** | 348,263 | `1.1336` / `90.46 %` / `4.1147` | `1.8806` / `37.93 %` (Mod.) / `10.4969` | Cubre solo `test+val` (asimetría muestral frente a `1.74M`). |
| **Legado borrando filas (`test+val`)** | 314,904 (-9.6 %) | `1.1351` / `90.62 %` / `4.1105` | `1.9006` / `38.28 %` (Mod.) / `10.5421` | Borró **33,359** empleos reales y casi no redujo `Sy/x`. |

### Parte B: Demostración de Invarianza Afín sobre `04_transformed`
Cuando `RobustScaler` transforma una variable restando su mediana (`c`) y dividiendo por su rango intercuartílico (`s`), la teoría matemática promete que:
- La nueva calidad del ajuste es **exactamente igual**: `R² nuevo = R² original`.
- La nueva pendiente es exactamente: `a₁ nuevo = a₁ original × (s_x / s_y)`.
- El nuevo error típico es exactamente: `Sy/x nuevo = Sy/x original / s_y`.

**Resultado verificado en los 8 controles (`con/sin outliers × train/test × 2 variables`):**
- En todos los casos `R²` coincidió al **100 %** (`0.9072 = 0.9072`, `0.8984 = 0.8984`, etc.).
- La mayor diferencia entre la fórmula teórica y los números reales leídos de los archivos de varios gigabytes fue **`7.22 × 10⁻¹⁴`** (más de **13 dígitos exactos de precisión**).
- Además, para no colapsar la memoria RAM al leer archivos CSV gigantes de hasta 8 GB con 2,985 columnas, se leyó solo el prefijo binario de las 3 columnas necesarias en cada fila.

---

## 5. ¿Por qué se eligió esta solución y no otra?

- Porque demuestra con evidencia dura que **winsorizar (Versión B) es superior a borrar filas**: conserva el 100 % del universo de personas y baja el error residual en casi una quinta parte.
- Y porque certifica que el preprocesamiento de `04_transformed` (`RobustScaler`) es matemáticamente limpio y no introdujo fugas ni distorsiones ocultas en las correlaciones lineales.

---

## 6. Cuidados importantes a tener en cuenta

- **Efecto secundario y compromiso (*trade-off*) de la winsorización:** Aunque la Versión B baja la dispersión en ambos pares, recortar individualmente el techo de cada columna rompe la suma exacta `Total = Prácticas + Conocimientos + Sin tipo` y, en `knowledge → essential`, recorta `x_max` de `45` a `13.5` reduciendo `R²` por debajo del umbral de rechazo (`36.80 % → 27.95 %`). Por eso el proyecto mantiene **ambas versiones (A y B)** en paralelo.
- **Comparación justa por tamaño muestral:** Las dos variantes legadas (`02_interim`) corresponden solo a `test+val` (`348k`/`315k` filas), mientras las Versiones A y B cubren `1.74M` filas; la tabla de invarianza afín (`test`, `347,720` filas) confirma que el contraste A vs. B se mantiene idéntico a igual tamaño muestral.

---

## 7. Glosario fácil

- **Outlier (valor atípico):** Un dato inusualmente grande o pequeño comparado con el resto del grupo.
- **Winsorización IQR:** Técnica que, en lugar de eliminar un dato extremo, lo reemplaza por el valor máximo (o mínimo) "normal" permitido, manteniendo el registro vivo sin dejar que arruine los promedios.
- **Error estándar de estimación (`Sy/x`):** Mide qué tan lejos, en promedio, caen los puntos reales respecto a la recta. Mientras más pequeño, más pegados están los datos a la línea.
- **Invarianza afín (de escala):** Propiedad matemática que garantiza que sumar constantes o cambiar unidades de medida no cambia la fuerza real (`R²`) de una relación lineal.
- **`RobustScaler`:** Herramienta de preparación de datos que centra los números alrededor de la mediana y los divide por el rango intercuartílico (IQR) para hacerlos menos sensibles a extremos.
