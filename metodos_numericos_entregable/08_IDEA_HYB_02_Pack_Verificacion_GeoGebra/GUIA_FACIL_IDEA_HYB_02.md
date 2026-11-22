# Guía Fácil para Todos — Caso 08 (`IDEA-HYB-02`): ¿Cómo demostramos que todas las cuentas son 100 % exactas y que nadie alteró los datos? (GeoGebra + Python + SHA-256)

> **Método utilizado:** Verificación cruzada en 3 vías (fórmulas propias, NumPy/SciPy y GeoGebra Classic) + auditoría criptográfica SHA-256  
> **Nivel de lectura:** Para todo público  
> **Presentación visual interactiva:** Abre [`presentacion_IDEA_HYB_02.html`](./presentacion_IDEA_HYB_02.html) en cualquier navegador.

---

## 1. Resumen en 30 segundos

Cuando alguien te entrega un estudio con casi dos millones de datos, siempre surge la pregunta más sana de todas: ***"¿Cómo sé que tus fórmulas en Python no tienen un error de código y que no modificaste por accidente los archivos originales?"***  
Este octavo caso es el **sello de calidad y auditoría** de todo el proyecto. Comprobamos nuestros 39 modelos MCO y todos los polinomios de Lagrange contra **NumPy/SciPy** (coincidiendo hasta **12–15 cifras decimales**, muy por debajo de `10⁻¹⁰`), generamos **5 scripts listos para copiar y pegar en GeoGebra Classic**, ejecutamos una **auditoría semántica bilingüe (EN + ES)** sobre todo el entregable (`0` violaciones), pasamos **19 de 19 pruebas automatizadas** y sellamos criptográficamente con **huellas SHA-256 completas de 64 caracteres** que los **19 archivos originales de `data/` permanecieron 100 % intactos**.

---

## 2. ¿Cuál era el problema? (Explicado fácil)

En proyectos grandes de programación y matemáticas pasan tres riesgos silenciosos:
1. Un pequeño error de signos o paréntesis en una fórmula escrita a mano pasa desapercibido y contamina todas las conclusiones.
2. El profesor o cualquier evaluador quiere comprobar visualmente los números en **GeoGebra Classic** sin tener que teclear manualmente 20 puntos decimales.
3. Un script podría sobrescribir o dañar accidentalmente los archivos de datos originales (`data/`).

Necesitábamos un **paquete automático de verificación** que cualquiera pueda auditar en segundos.

---

## 3. Analogía de la vida real: el doble conteo de un banco y el sello de seguridad de un sobre

Piensa en cómo un banco audita una bóveda de dinero:
1. **Doble verificación independiente (Python propio vs. NumPy/SciPy vs. GeoGebra):** Primero cuentas el dinero a mano con la fórmula clásica; luego lo pasas por una máquina contadora certificada (`NumPy/SciPy`); y finalmente dejas el recibo listo para que un auditor externo lo verifique en su propia calculadora (**GeoGebra Classic**). Si los tres coinciden hasta el último centavo (aquí hasta la **billonésima parte**), el cálculo es irrefutable.
2. **Huella digital SHA-256:** Es como tomarle la huella dactilar a cada uno de los **19 archivos originales** antes de empezar y volverla a tomar al terminar. Si cambiara siquiera **una sola coma o un solo espacio** en un archivo de 8 gigabytes, la huella SHA-256 cambiaría por completo. Aquí **19 de 19 huellas coincidieron exactamente**.

---

## 4. La solución explicada paso a paso

### Paso 1: Verificar las fórmulas escritas a mano frente a librerías científicas
En los 39 modelos de Regresión Lineal y en todos los polinomios de Lagrange, la meta era que la diferencia fuera menor a `1 × 10⁻¹⁰` (diez ceros después del punto). Logramos algo mucho mejor:

| Prueba de precisión ejecutada | Error máximo medido | Precisión decimal lograda | Estado |
| :--- | :---: | :---: | :---: |
| **39 modelos MCO propios vs. `numpy.polyfit`** | `2.29 × 10⁻¹²` | **~11.6 dígitos exactos** | ✅ Superado por 43× |
| **8 pruebas de Invarianza Afín (`RobustScaler`)** | `7.22 × 10⁻¹⁴` | **~13.1 dígitos exactos** | ✅ Superado por 1,380× |
| **Lagrange propio vs. `scipy.interpolate.lagrange`** | `5.05 × 10⁻¹⁵` | **~14.3 dígitos exactos** | ✅ Casi límite de la CPU |
| **Propiedad Partición de la Unidad (`Σ Lᵢ = 1`)** | `4.44 × 10⁻¹⁶` | **~15.4 dígitos exactos** | ✅ Precisión de máquina |
| **Propiedad Delta de Kronecker (`Lᵢ(xⱼ)`)** | `0.00` | **Exacto absoluto** | ✅ Perfecto |

### Paso 2: Pack de 5 scripts listos para GeoGebra Classic
Generamos y validamos automáticamente 5 guiones listos para pegar en [geogebra.org/classic](https://www.geogebra.org/classic):
1. `ggb_rl01_career_steps_skills.txt` → Recta MCO de pasos de carrera (`k = 1..10`) y predicción en `k = 12`.
2. `ggb_rl02_isco10_transferability.txt` → 10 centroides de grupos ISCO-08 y su recta de transferibilidad (con aviso explícito `MR-06`: `R² = 0.28 < 0.30`, `Q_pred` solo verificación aritmética).
3. `ggb_rl04_annual_duration_extrapolation.txt` → Recta de duración en empleos cerrados (`~es_vigente`) 2000–2019 (`R² = 0.9729`) y extrapolación imposible en 2027 (`-4.96` trimestres).
4. `ggb_lg01_survival_p3_milestones.txt` → Los 4 polinomios base `L₀..L₃`, forma monomial expandida y `P₃(12)` de supervivencia laboral.
5. `ggb_lg02_pca_forward_p3.txt` → Polinomio cúbico `P₃(4)` y forma monomial expandida de varianza acumulada de PCA (recomputado en vivo).

### Paso 3: Auditoría de integridad SHA-256 (64 hex), lenguaje bilingüe y 19 pruebas automatizadas
- Se comprobó que los **19 archivos** distribuidos en las 4 capas de `data/` (`01_raw`, `02_interim`, `03_processed`, `04_transformed`) conservaron exactamente el mismo **digest SHA-256 íntegro de 64 caracteres hexadecimales** (13 con hash completo byte a byte `full_sha256` + 6 archivos masivos de 1.4–8.4 GB con `sampled_24MiB_plus_meta_sha256`, transparencia explícita en `hash_mode`).
- La auditoría semántica bilingüe (inglés y español, `MR-07/MR-08`) escaneó notebooks, bitácoras y todos los Markdown del entregable con **0 violaciones**.
- Las **19 pruebas unitarias e integrales** (`tests/metodos_numericos`) pasaron **19/19 en verde**.

---

## 5. ¿Por qué se eligió esta solución y no otra?

Porque combina lo mejor de dos mundos: **transparencia pedagógica** (cualquiera puede copiar 5 líneas en GeoGebra y comprobar el gráfico en vivo) y **rigor profesional de ingeniería** (pruebas automatizadas y sellos SHA-256 reproducibles con un solo comando).

---

## 6. Cuidados importantes a tener en cuenta

- Los comandos de GeoGebra se exportaron en **inglés** (`FitLine`, `Polynomial`, `RSquare`, `CorrelationCoefficient`) porque GeoGebra Classic los acepta sin error sin importar si tu navegador está en español o en inglés (y dentro de cada archivo incluimos además su equivalente en español como comentario).

---

## 7. Glosario fácil

- **GeoGebra Classic:** Calculadora gráfica gratuita en línea que permite ver puntos, rectas y polinomios en vivo pegando comandos de texto.
- **NumPy / SciPy:** Bibliotecas matemáticas estándar de Python usadas mundialmente en ciencia e ingeniería para validar cálculos numéricos.
- **Precisión `10⁻¹⁴` o `10⁻¹⁵`:** Un error tan pequeño (`0.00000000000001`) que equivale a medir la distancia de la Tierra a la Luna con un error del tamaño de un cabello.
- **Huella criptográfica SHA-256:** Un código único de 64 caracteres que identifica exactamente el contenido de un archivo; sirve para probar matemáticamente que un archivo no fue alterado.
- **Suite de pruebas automatizadas:** Conjunto de verificaciones que el computador ejecuta automáticamente para confirmar que todas las fórmulas, casos límite y protecciones siguen funcionando bien.
