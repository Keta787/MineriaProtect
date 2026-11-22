# Guía Maestra de Estudio y Sustentación — Métodos Numéricos en JobPath (`MineriaProtect`)

**Programa:** Ingeniería de Sistemas · UNIMINUTO (Ibagué)  
**Asignatura:** Métodos Numéricos (*Regresión Lineal por Mínimos Cuadrados* + *Interpolación Polinomial de Lagrange*)  
**Proyecto:** **JobPath (`MineriaProtect`)** — *JobHop v2 (`1,993,291` filas crudas → `1,738,738` empleos clasificados) + Catálogo Europeo ESCO v1.2.1 / ISCO-08 (`3,039` oficios; `126,051` relaciones)*  
**Versión verificada:** **V2 (`5.0 / 5.0` en los 8 casos y en las 8 presentaciones HTML · `19/19` tests OK · `19/19` SHA-256 64-hex intactos · `0` violaciones `MR-07/MR-08`)**

> [!TIP]
> **Cómo usar esta guía:** Léela en orden antes de la exposición. Si solo tienes 15 minutos, estudia la **Sección 1 (Apertura)**, los bloques **a) Resumen en 30 s** y **g) Preguntas difíciles** de cada caso, y la **Sección 4 (Acordeón de 1 página)**.

---

## Tabla de Contenido

- [1. Panorama General y Discurso de Apertura (60 segundos)](#1-panorama-general-y-discurso-de-apertura-60-segundos)
- [2. Guía de Estudio Caso por Caso (Casos 01 al 08)](#2-guía-de-estudio-caso-por-caso-casos-01-al-08)
  - [Caso 01 — `IDEA-RL-01`: Progresión Laboral por Paso de Carrera (MCO)](#caso-01--idea-rl-01-progresión-laboral-por-paso-de-carrera-mco)
  - [Caso 02 — `IDEA-RL-02`: Ontología ESCO, Transferibilidad y Rechazo Honesto (MCO)](#caso-02--idea-rl-02-ontología-esco-transferibilidad-y-rechazo-honesto-mco)
  - [Caso 03 — `IDEA-RL-04`: Deriva Anual (2000–2023) y Falla por Extrapolación (MCO)](#caso-03--idea-rl-04-deriva-anual-20002023-y-falla-por-extrapolación-mco)
  - [Caso 04 — `IDEA-RL-05`: Outliers (4 Vías) e Invarianza Afín en `04_transformed` (MCO)](#caso-04--idea-rl-05-outliers-4-vías-e-invarianza-afín-en-04_transformed-mco)
  - [Caso 05 — `IDEA-LG-01`: Curva de Supervivencia Laboral `S(q)` y Fenómeno de Runge (Lagrange)](#caso-05--idea-lg-01-curva-de-supervivencia-laboral-sq-y-fenómeno-de-runge-lagrange)
  - [Caso 06 — `IDEA-LG-02`: Varianza Acumulada PCA — Lagrange Directo e Inverso](#caso-06--idea-lg-02-varianza-acumulada-pca--lagrange-directo-e-inverso)
  - [Caso 07 — `IDEA-HYB-01`: Laboratorio Comparativo "¿Interpolar o Ajustar?"](#caso-07--idea-hyb-01-laboratorio-comparativo-interpolar-o-ajustar)
  - [Caso 08 — `IDEA-HYB-02`: Pack de Verificación GeoGebra, Precisión y Auditoría SHA-256](#caso-08--idea-hyb-02-pack-de-verificación-geogebra-precisión-y-auditoría-sha-256)
- [3. Glosario Maestro Completo (A–Z)](#3-glosario-maestro-completo-az)
- [4. Acordeón Final de 1 Página, Tiempos y Checklist Previo a Exponer](#4-acordeón-final-de-1-página-tiempos-y-checklist-previo-a-exponer)

---

## 1. Panorama General y Discurso de Apertura (60 segundos)

### Guion listo para abrir la presentación
> *"Nuestro proyecto **JobPath** analiza casi **2 millones de registros laborales reales** del dataset **JobHop v2** (`1,993,291` filas crudas; `1,738,738` experiencias clasificadas con habilidades completas) integrados con el catálogo europeo oficial **ESCO v1.2.1** (`3,039` ocupaciones y `126,051` relaciones ocupación–competencia).*
>
> *En lugar de aplicar métodos numéricos sobre ejemplos de juguete, llevamos las dos grandes técnicas del curso —**Regresión Lineal por Mínimos Cuadrados (MCO)** e **Interpolación Polinomial de Lagrange**— directamente sobre las **4 capas reales de nuestro pipeline KDD/CRISP-DM**, respetando al 100 % el modo solo lectura sobre `data/`.*
>
> *Organizamos el estudio en **8 casos progresivos**: los **Casos 01 al 04** aplican y auditan MCO (tendencias, rechazo honesto por bajo `R²`, fallo físico por extrapolación y sensibilidad a outliers/escalado); los **Casos 05 y 06** aplican Lagrange (curva de supervivencia, Fenómeno de Runge mitigado con Chebyshev-Lobatto e interpolación inversa en PCA); el **Caso 07** enfrenta ambos métodos cara a cara para responder '¿Interpolar o ajustar?'; y el **Caso 08** certifica todo con verificación triple (fórmulas propias desde cero ↔ NumPy/SciPy ↔ 5 scripts de GeoGebra Classic), huellas **SHA-256 completas de 64 caracteres** y **19 pruebas automatizadas en verde**."*

### Mapa rápido de las 4 capas de `data/` (solo lectura)
| Capa | Qué guarda | Volumen / Ejemplos | En qué casos se usa |
|---|---|---|---|
| `01_raw/` | Archivos crudos originales de JobHop v2 sin limpiar (`train`, `test`, `val`). | `1,993,291` filas (`63.7 + 8.0 + 8.0 MiB`). | Caso 03 (`RL-04`), Caso 08 (`HYB-02`). |
| `02_interim/` | Catálogos limpios ESCO/ISCO/SKILLS y tablas legadas (`test+val`). | `3,039` oficios, `126,051` relaciones, `348k` filas legadas. | Casos 01, 02, 04, 08. |
| `03_processed/` | Datasets analíticos completos en **Versión A** (con outliers) y **Versión B** (winsorizada IQR). | `1,871,014` filas (`1,738,738` clasificadas; `~1.4 GB` c/u). | Casos 01, 03, 04, 05, 06, 07, 08. |
| `04_transformed/` | Matrices escaladas con `RobustScaler` listas para Machine Learning (`2,985` columnas). | Archivos CSV de `2 GB` a `8 GB` + `transformers.joblib`. | Caso 04 (`RL-05`), Caso 08 (`HYB-02`). |

### Las 5 Reglas Metodológicas (`MR`) que debes dominar de memoria
| Regla | Nombre corto | Qué garantiza en la sustentación |
|---|---|---|
| **`MR-04`** | **Nodos distintos** | En Lagrange nunca puede haber dos nodos `xᵢ = xⱼ`, porque el denominador `(xᵢ − xⱼ)` se hace cero (división por cero). Se dispara en vivo en PCA `V(9) = V(10) = 1.0`. |
| **`MR-06`** | **Rechazo honesto (`R² < 0.30`)** | Aunque MCO siempre dibuje una recta, si `R² < 0.30` el modelo lineal se **rechaza explícitamente** (no se usa para predecir). |
| **`MR-07`** | **No causalidad** | Las pendientes `a₁` y correlaciones `r` describen **asociaciones históricas** en los datos; nunca prueban que `X` "cause" `Y`. |
| **`MR-08`** | **Atribución ESCO** | Las columnas de competencias miden **cuántas habilidades exige el oficio ESCO asignado al cargo**, nunca cuántas habilidades sabe o posee individualmente una persona. |
| **`MR-09`** | **Censura (`~es_vigente`)** | Todas las métricas de duración (`RL-01`, `RL-04`, `LG-01`) se calculan **solo sobre empleos ya terminados (`~es_vigente`)**, excluyendo empleos aún activos sin fecha real de fin. |

---

## 2. Guía de Estudio Caso por Caso (Casos 01 al 08)

---

### Caso 01 — `IDEA-RL-01`: Progresión Laboral por Paso de Carrera (MCO)

- **Presentación:** `01_IDEA_RL_01_Pasos_Carrera_MCO/presentacion_IDEA_RL_01.html`
- **Tablas clave:** `rl01_career_step_profile.csv`, `rl01_summation_and_residuals_skills.csv`, `rl01_ols_summary.csv`, `rl01_extrapolation_audit.csv`

#### a) Resumen en 30 segundos y analogía
Ordenamos los `1,738,738` empleos clasificados por el número secuencial de empleo de cada hoja de vida (`k = 1, 2, ..., 10`) y ajustamos rectas por Mínimos Cuadrados (MCO) para ver cómo evolucionan las competencias exigidas por el cargo, la reincidencia en el oficio, la duración de empleos cerrados y la intensidad verde.
- **Analogía:** *Colocar una regla transparente sobre los puntos de estatura promedio de niños de 1 a 10 años, buscando que los "saltitos" verticales al cuadrado sean lo más pequeños posible en vez de unir punto a punto el ruido.*

#### b) Problema, datos y reglas aplicadas
- **Capa:** `03_processed` (Versión A, `1,738,738` filas clasificadas) + `02_interim/ESCO/greenShareOcc_en_limpio.csv`.
- **Variable `X`:** `job_order` (`k = 1..10` para entrenamiento; `k = 11, 12, 15` retenidos para probar extrapolación).
- **Variables `Y`:** `mean_skills` (promedio de habilidades esenciales ESCO del oficio), `reincide_rate` (proporción de empleos cuyo oficio se repite en la trayectoria), `mean_dur_q` (duración media en trimestres solo sobre empleos cerrados `~es_vigente`), `mean_green` (intensidad verde promedio ESCO).
- **Reglas activas:** `MR-07`, `MR-08`, `MR-09` (`~es_vigente`) + control de cohorte fija (`≥10` empleos) + verificación ponderada **WLS**.

#### c) Fórmulas explicadas símbolo por símbolo
$$\hat{y}(k) = a_0 + a_1 k, \qquad a_1 = \frac{n\sum k_i y_i - \sum k_i \sum y_i}{n\sum k_i^2 - (\sum k_i)^2}, \qquad a_0 = \bar{y} - a_1 \bar{k}$$
$$R^2 = \frac{S_t - S_r}{S_t}, \qquad S_{y/x} = \sqrt{\frac{S_r}{n - 2}}$$
- `k`: número de paso de carrera (`1` a `10`).
- `a₀`: intercepto (nivel base teórico en `k = 0`; para `mean_skills`, `22.5160`).
- `a₁`: pendiente (cuánto cambia el promedio por cada escalón adicional; `+0.2250` competencias ESCO por paso).
- `Sₜ`: suma total de desviaciones al cuadrado respecto a la media (`4.1944`).
- `Sᵣ`: suma de residuos al cuadrado `Σ(yᵢ − ŷᵢ)²` que MCO minimiza (`0.0189`).
- `R²`: fracción de varianza explicada por la recta (`99.55 %`, casi línea recta perfecta).
- `S_{y/x}`: error típico vertical en las mismas unidades de `Y` (`0.0486` habilidades); `n − 2 = 8` son los grados de libertad porque se estimaron 2 parámetros (`a₀` y `a₁`).
- **Cuidado clásico del curso:** nunca confundir `∑kᵢ² = 385` con `(∑kᵢ)² = 55² = 3,025`.

#### d) Cadena exacta de cómo se sacó cada conclusión
| Pregunta / Hallazgo | Dato de entrada (`CSV`) | Cálculo exacto | Control / Verificación | Conclusión defendible |
|---|---|---|---|---|
| **1. Crecimiento de competencias exigidas** | `rl01_summation_and_residuals_skills.csv` (`n=10`, `∑k=55`, `∑y=237.5338`) | `a₀ = 22.5160`, `a₁ = +0.2250`, `R² = 0.9955`, `Sy/x = 0.0486` | Centroide `(5.5, 23.7534)` exacto (`err = 0.0`); `polyfit` diff `3.55e-15`; **WLS** `a₁ = +0.2287` (**diff solo `1.67 %`**); Cohorte `≥10` mantiene `R² = 0.9529` (`a₁ = +0.2026`). | La complejidad ocupacional ESCO sube casi linealmente con el paso de carrera y es robusta frente al tamaño desigual de cada paso (`352k` vs `25k`). |
| **2. Duración laboral cerrada y fallo al extrapolar** | `rl01_career_step_profile.csv` (`~es_vigente`, `n_closed_rows` de `336,800` a `23,465`) | `a₀ = 13.2330`, `a₁ = -0.8565`, `R² = 0.9233`, `Sy/x = 0.7928` | Extrapolación en `rl01_extrapolation_audit.csv`: en `k = 15` la recta predice `0.3852` trim., pero el dato real cerrado se estabiliza en `4.2601` (error `3.8749` trim.). | Aplicar `MR-09` mejora `R²` (`0.9050 → 0.9233`), pero la caída es **convexa**: nunca extrapoles una recta fuera del rango `k = 1..10`. |
| **3. Paradoja de Simpson en `mean_green`** | `rl01_ols_summary.csv` (Universo vs. Cohorte `≥10`) | Universo: `a₁ = -0.000219` (`R² = 0.7877`). Cohorte `≥10`: **`a₁ = +0.000183`** (`R² = 0.7310`). | Al fijar exactamente las mismas personas (`≥10` empleos), el signo de la pendiente **se invierte**. | La caída aparente global en intensidad verde es un **efecto composición** (salen perfiles de carreras cortas); dentro de la misma cohorte la tendencia es levemente positiva. |
| **4. Sesgo en `reincide_rate`** | `rl01_ols_summary.csv` | Universo: `R² = 0.9625` (`a₁ = +0.0213`). Cohorte `≥10`: `R² = 0.4475` (`a₁ = +0.0072`). | Caída fuerte de pendiente y `R²` al controlar la longitud de carrera. | Parte del aumento en reincidencia es mecánico (personas con más empleos tienen más oportunidades de repetir oficio). |

#### e) Qué mostrar en vivo en la presentación
- **Simulador (Diap. 4):** Mueve el slider a `k = 5` (verde, dentro del rango), luego pulsa **`Extrap. k=12`** (muestra que `mean_skills` apenas falla `0.023`) y **`Extrap. k=15`** (muestra que duración cerrada falla `3.87` trimestres!).
- **Gráficas (Diap. 5):** Haz clic para zoom en la Figura 1 (señala el centroide y la zona sombreada `k > 10`) y Figura 2 (muestra los cuadraditos de residuos `eᵢ²` que suman `Sᵣ = 0.0189`).
- **GeoGebra (Diap. 7):** Señala `FitLine(P)`, `RSquare(P, f) = 0.9955` y `Centroid = (5.5, 23.7534)`.

#### f) Qué SÍ decir vs. Qué NUNCA decir
| ✅ Frase correcta (aprobada) | ❌ Frase prohibida (error grave) |
|---|---|
| *"En promedio, los cargos ocupados en pasos posteriores exigen +0.225 competencias ESCO más por escalón."* | *"Cambiar de trabajo hace que la persona aprenda 0.225 habilidades nuevas cada vez."* (Viola `MR-07` y `MR-08`). |
| *"Confirmamos con WLS que el menor volumen en `k=10` (`25k` vs `352k`) solo cambia la pendiente de `mean_skills` en 1.67 %."* | *"Usamos MCO simple porque todos los pasos tienen el mismo peso estadístico."* |

#### g) Preguntas difíciles del docente y respuestas ganadoras
1. **¿Por qué no hicieron la regresión sobre las 1.74 millones de filas directamente en vez de 10 promedios?**
   - *Respuesta:* Porque aquí buscamos replicar la tabla paso a paso de sumatorias (`n = 10`, verificable a mano y en GeoGebra) para modelar la tendencia media por escalón `k`; para cubrir el riesgo de agregación ecológica y distinto tamaño `n_k` (`352k` vs `25k`), añadimos la auditoría **WLS** (`1.67 %` de diferencia en `mean_skills`) y el control de cohorte `≥10` (que destapó la Paradoja de Simpson en `mean_green`).
2. **¿Por qué la suma de residuos `∑eᵢ = 0` no sirve como criterio para hallar la mejor recta?**
   - *Respuesta:* Porque los errores positivos y negativos se cancelan entre sí: **cualquier recta** que pase por el centroide `(5.5, 23.7534)` tiene `∑eᵢ = 0`, incluso una recta pésima. Por eso MCO minimiza la suma de los **cuadrados** `Sᵣ = ∑eᵢ²`.

---

### Caso 02 — `IDEA-RL-02`: Ontología ESCO, Transferibilidad y Rechazo Honesto (MCO)

- **Presentación:** `02_IDEA_RL_02_Catalogo_ESCO_MCO/presentacion_IDEA_RL_02.html`
- **Tablas clave:** `rl02_esco_catalog_ols.csv`, `rl02_isco_major_group_slopes.csv`

#### a) Resumen en 30 segundos y analogía
Analizamos los `3,039` oficios del catálogo europeo ESCO v1.2.1 (`126,051` relaciones) para medir qué fracción de las habilidades de un oficio es transferible a otros sectores (`57.9 %` en promedio, llegando a `74.0 %` en Gerentes) y demostrar **cuándo la honestidad numérica obliga a rechazar una recta** (`greenShare` tiene `R² = 0.00004`).
- **Analogía:** *Una caja de herramientas: de cada 10 herramientas extra que exige un oficio, casi 6 son universales (`cross-sector`) y 4 son de nicho. En cambio, intentar adivinar si un oficio es ecológico contando cuántas habilidades tiene es como adivinar el color de un carro midiendo su peso (`R² ≈ 0`).*

#### b) Problema, datos y reglas aplicadas
- **Capa:** `02_interim/ESCO/` y `02_interim/SKILLS/` (`3,039` ocupaciones con `100 %` cobertura `greenShare`, agrupadas en los `10` grandes grupos ISCO-08).
- **Reglas activas:** **`MR-06` (semáforo `R²`)**, `MR-07`, `MR-08`.
  - 🟢 **Fuerte:** `R² ≥ 0.70` | 🟡 **Moderado:** `0.30 ≤ R² < 0.70` | 🔴 **Rechazado:** `R² < 0.30`.

#### c) Fórmulas explicadas símbolo por símbolo
$$\widehat{\text{cross\_sector}} = a_0 + a_1 \cdot \text{total\_rel}$$
- `total_rel`: total de relaciones de habilidades de un oficio en ESCO (`competencias + conocimientos`).
- `cross_sector`: habilidades reutilizables entre distintos sectores industriales.
- `a₁ = 0.5786`: tasa marginal de transferibilidad (`+57.9 %` de cada habilidad extra vinculada a un oficio es intersectorial).
- `greenShare`: proporción de habilidades ligadas a la transición ecológica en el oficio ESCO.

#### d) Cadena exacta de cómo se sacó cada conclusión
| Hallazgo | Dato (`CSV`) | Resultado exacto | Control crítico | Conclusión defendible |
|---|---|---|---|---|
| **1. Transferibilidad global** | `rl02_esco_catalog_ols.csv` (`n = 3,039`) | `a₀ = -0.7983`, `a₁ = +0.5786`, `R² = 0.5670` (🟡 Moderado) | `n_cross_sector` es subconjunto de `n_total_rel` (**acople parte-todo**): `a₁` se interpreta como proporción marginal estructural. | Por cada 10 habilidades adicionales en un oficio ESCO, en promedio ~5.8 son transferibles a otros sectores. |
| **2. Contrastes fuertes por composición interna** | `rl02_esco_catalog_ols.csv` (`n = 3,039`) | `n_ess_comp → n_essential`: `R² = 0.8643`; `n_competence → n_total_rel`: `R² = 0.7319` | **Advertencia parte-todo:** como `X` es un sumando de `Y`, la covarianza matemática infla `R²`; describe estructura taxonómica, no predicción externa. | Las competencias (vs. conocimientos) explican la mayor parte del volumen esencial de ESCO. |
| **3. Mitos desmontados (Rechazos `MR-06`)** | `rl02_esco_catalog_ols.csv` (`n = 3,039`) | `essential → optional`: `R² = 0.0140`; `essential → greenShare`: **`R² = 0.000045`**; `knowledge → greenShare`: `R² = 0.0043` | Todos `< 0.30` → **🔴 Rechazados**. | Tener más habilidades esenciales **no** hace a un oficio más "verde" ni le da más habilidades opcionales (ortogonalidad). |
| **4. Brecha por grupo ISCO-08 y rechazo en centroides** | `rl02_isco_major_group_slopes.csv` (`10` grupos) | Campeón: **ISCO-1 Gerentes** (`a₁ = 74.0 %`, `R² = 0.7541`). Mínimos: **ISCO-9 Elementales** (`31.3 %`) y **ISCO-6 Agricultura** (`33.3 %`, aunque tiene el mayor `greenShare = 13.7 %`!). **ISCO-5 Servicios** queda **🔴 Rechazado (`R² = 0.2687`)**. | Al resumir los `3,039` oficios en los `10` centroides ISCO (`ggb_rl02`), **Agricultura (`46.6` totales vs `12.3` transferibles)** desploma `R²` a **`0.2800` (🔴 Rechazado `MR-06`)**. | La transferibilidad depende fuertemente del sector; promediar en 10 centroides oculta la dispersión interna y obliga a rechazar la recta agregada (`Q_pred(45) = 22.93` es solo chequeo aritmético). |

#### e) Qué mostrar en vivo en la presentación
- **Simulador ISCO-08 (Diap. 4):** Haz clic en **Grupo 1** (`🟢 Fuerte 75.4 %, 74.0 % transferible`), luego en **Grupo 6** (`Agricultura: 33.3 % transferible`) y finalmente en **Grupo 5** para mostrar en vivo la alerta roja **`🔴 Semáforo MR-06: RECHAZADO (26.9 %)`**!
- **GeoGebra (Diap. 7):** Resalta la línea `# WARNING (MR-06): R2 = 0.2800 < 0.30 -> REJECTED` dentro del bloque de comandos.

#### f) Qué SÍ decir vs. Qué NUNCA decir
| ✅ Frase correcta | ❌ Frase prohibida |
|---|---|
| *"En los 2 modelos fuertes (`0.86` y `0.73`), `X` es parte de `Y`; por eso los reportamos como tasas estructurales del catálogo ESCO."* | *"Descubrimos un modelo predictivo independiente con `R² = 0.86`."* |
| *"El punto `Q_pred(45) = 22.93` en GeoGebra valida la aritmética de la recta, pero el modelo está rechazado por `MR-06` (`R² = 0.28`)."* | *"Según GeoGebra, un oficio con 45 habilidades tendrá exactamente 22.93 habilidades transferibles."* |

#### g) Preguntas difíciles del docente y respuestas ganadoras
1. **Si `R² = 0.28` en los 10 centroides ISCO está rechazado, ¿por qué incluyeron ese archivo en GeoGebra?**
   - *Respuesta:* Precisamente para cumplir la lección de la Diapositiva 13 del curso: demostrar en vivo que MCO siempre calcula una recta exacta (`FitLine`, error `1.07e-14` vs NumPy), pero que el criterio ingenieril (`MR-06`) nos exige rechazarla al ver `RSquare = 0.2800` y detectar el residuo extremo del grupo 6 (Agricultura, `e₆ ≈ -11.33`).
2. **¿Por qué `greenShare` dio `R² = 0.00004` frente a `n_essential`?**
   - *Respuesta:* Porque un oficio ecológico depende del **tipo temático de tareas** (ej. Agricultura/silvicultura tiene `13.7 %` verde, el más alto), no de la cantidad total de habilidades que exige el cargo.

---

### Caso 03 — `IDEA-RL-04`: Deriva Anual (2000–2023) y Falla por Extrapolación (MCO)

- **Presentación:** `03_IDEA_RL_04_Deriva_Anual_Extrapolacion/presentacion_IDEA_RL_04.html`
- **Tablas clave:** `rl04_annual_macro_series.csv`, `rl04_ols_regime_comparison.csv`, `rl04_extrapolation_failure_audit.csv`, `rl04_raw_partition_parity.csv`

#### a) Resumen en 30 segundos y analogía
Estudiamos 20 años del mercado laboral (`2000–2019`) y demostramos **tres lecciones clave de MCO**: (1) incluir los 4 años censurados al final (`2020–2023`, con solo `59, 3, 3, 1` inicios) invierte el signo de la pendiente y desploma `R²` (`0.75 → 0.08`); (2) centrar el año en `t = año − 2000` hace interpretable `a₀` y mejora `4,672×` la estabilidad numérica; y (3) extrapolar una recta con `R² = 97.29 %` produce **duraciones laborales negativas (`-0.20` desde 2021 hasta `-4.96` en 2027)**.
- **Analogía:** *Tu café caliente baja 4 °C por minuto de 80 °C a 40 °C en 10 minutos; si estiras la recta al minuto 30, predice `-40 °C` (congelado), lo cual es físicamente imposible.*

#### b) Problema, datos y reglas aplicadas
- **Capas:** `03_processed` (serie anual `2000–2023`, `1,509,997` inicios en `2000–2019`) + `01_raw` (`1,993,291` filas crudas para auditar paridad `train/test/val`).
- **Reglas activas:** **`MR-09` (`~es_vigente`)** estricta en `mean_dur_q`, `MR-06`, `MR-07`, `MR-08`.

#### c) Fórmulas explicadas símbolo por símbolo
$$\widehat{\text{dur}}(t) = 16.4417 - 0.7926 \cdot (\text{año} - 2000)$$
- `t = año − 2000`: tiempo centrado (`t = 0` en el año 2000, `t = 19` en 2019, `t = 27` en 2027).
- `a₀ = 16.4417`: duración promedio esperada (en trimestres) para un empleo cerrado iniciado en el año 2000. *(Sin centrar daba `+1,601.64` trimestres en el año 0 d. C., sin sentido físico).*
- `a₁ = -0.7926`: caída promedio por cada año posterior (`-0.79` trimestres/año).
- **Cruce por cero:** `t₀ = 16.4417 / 0.7926 = 20.74` → año **`2020.74`** (por eso desde `2021` ya es negativo!).

#### d) Cadena exacta de cómo se sacó cada conclusión
| Hallazgo | Dato (`CSV`) | Resultado exacto | Control crítico | Conclusión defendible |
|---|---|---|---|---|
| **1. Efecto palanca de la cola censurada** | `rl04_ols_regime_comparison.csv` (`mean_skills`) | `2000–2019 (n=20)`: `a₁ = +0.0967`, `R² = 0.7475`. `2000–2023 (n=24)`: **`a₁ = -0.1011`, `R² = 0.0826`** (Rechazado). | En `2020–2023` solo hay `59, 3, 3, 1` inicios (`mean_skills` cae a `14.0` con `n=1`). Por residuos al cuadrado + alto apalancamiento en el borde, esos 4 puntos voltean la recta. | Nunca ajustes MCO sin revisar primero el soporte muestral por periodo. |
| **2. Filtro `MR-09` elimina rebote falso de 2019** | `rl04_annual_macro_series.csv` (`mean_dur_q` vs. `mean_dur_q_incl_active`) | Con vigentes: 2018 `6.61 →` 2019 `8.31` (rebote artificial, `R² = 0.9288`). Solo cerrados (`~es_vigente`): **2018 `3.14 →` 2019 `2.27` (`R² = 0.9729`)**. | Excluir empleos activos (`es_vigente == True`, imputados a `2026-Q1`) devuelve coherencia total con `RL-01` y `LG-01`. | El rebote de 2019 era un artefacto de censura; filtrando `~es_vigente` el ajuste interno sube a `R² = 97.29 %`. |
| **3. Alto `R²` NO legitima extrapolar** | `rl04_extrapolation_failure_audit.csv` | `2020`: `+0.59` · `2021`: **`-0.20`** · `2026`: `-4.17` · `2027`: **`-4.96` trimestres** (`physically_invalid = True`). | Un empleo iniciado en 2019 y ya cerrado no pudo durar 10 años (censura derecha calendario). | Un `R² = 97.29 %` describe el pasado censurado, pero extrapolar produce valores físicamente imposibles desde 2021. |
| **4. Centrado numérico y paridad `01_raw`** | `rl04_ols_regime_comparison.csv` y `rl04_raw_partition_parity.csv` | Diff vs `polyfit` en `mean_dur_q`: `1.66e-11` (sin centrar) → **`3.55e-15`** (centrado, **`4,672×`** mejor). En `01_raw`: `train/test/val` tienen pendientes casi iguales (`+0.1855 / +0.1808 / +0.1848 %/año`). | Centrar evita cancelación numérica (`2010²`) sin alterar `a₁`, `R²` ni `Sy/x`; `01_raw` prueba ausencia de sesgo de división. | Siempre centrar el eje temporal en MCO; las 3 particiones crudas de JobHop v2 son temporalmente homogéneas. |

#### e) Qué mostrar en vivo en la presentación
- **Simulador (Diap. 4):** Pulsa **`2005 (Válido)`** (verde), **`2019 (Borde)`**, **`2023 (Censurado)`** (ya sale rojo `-1.79`!) y **`2027 (¡Falla!)`** (`-4.96 trimestres · FÍSICAMENTE IMPOSIBLE`).
- **Tabla (Diap. 6):** Señala las dos filas de `mean_dur_q (cerr.)`: `Sin centrar (a₀ = 1,601.64, diff 1.66e-11)` vs. `Centrado (a₀ = 16.4417, diff 3.55e-15)` con exactamente el mismo `a₁` y `R²`.
- **GeoGebra (Diap. 7):** Muestra que `Q_pred = (27, -4.9585)` cae visualmente muy por debajo del eje X.

#### f) Qué SÍ decir vs. Qué NUNCA decir
| ✅ Frase correcta | ❌ Frase prohibida |
|---|---|
| *"La caída de `-0.79` trimestres/año en duración cerrada refleja censura calendario derecha, no necesariamente que los empleos duren cada vez menos en la economía."* | *"Los empleos duran cada año 0.79 trimestres menos y en 2027 durarán menos de cero."* |
| *"Centrar `t = año − 2000` deja intactos `a₁`, `R²` y `Sy/x`, pero hace interpretable `a₀` y gana `4,672×` en precisión."* | *"Centrar `t − 2000` mejora el `R²` del modelo."* (¡Falso! `R²` es invariante a traslaciones). |

#### g) Preguntas difíciles del docente y respuestas ganadoras
1. **Si excluyeron los empleos vigentes (`~es_vigente`), ¿por qué la duración igual cae en línea recta hacia 2019?**
   - *Respuesta:* Porque incluso entre empleos ya cerrados existe **censura derecha calendario**: un empleo iniciado en 2000 tuvo hasta 20 años para cerrarse con duraciones largas, mientras que uno iniciado en 2019 y ya cerrado antes del corte del dataset solo pudo haber durado unos pocos trimestres. Para proyectar duraciones al futuro habría que usar modelos de supervivencia (Kaplan-Meier / Cox), no extrapolación lineal.
2. **¿Por qué sin centrar se pierde precisión frente a `numpy.polyfit`?**
   - *Respuesta:* Porque `n∑x²` y `(∑x)²` con `x ≈ 2010` valen ambos `~1.615 × 10⁹` y coinciden en sus primeros 5 dígitos; al restarlos ocurre **cancelación catastrófica** en punto flotante `float64`.

---

### Caso 04 — `IDEA-RL-05`: Outliers (4 Vías) e Invarianza Afín en `04_transformed` (MCO)

- **Presentación:** `04_IDEA_RL_05_Outliers_E_Invarianza_Escala/presentacion_IDEA_RL_05.html`
- **Tablas clave:** `rl05_four_way_outlier_comparison.csv`, `rl05_affine_scale_invariance.csv`

#### a) Resumen en 30 segundos y analogía
Auditamos dos decisiones de ingeniería de datos sobre `1,738,738` empleos: (1) comparar **4 estrategias frente a outliers** (dejar crudo, winsorizar con IQR, limpio legado y borrar filas) mostrando que winsorizar reduce el error típico `Sy/x` en **`-21.9 %`** sin perder ni un registro (frente a `-9.6 %` de filas borradas en el flujo legado), revelando honestamente su *trade-off* en `knowledge → essential`; y (2) probar matemáticamente con **13+ dígitos de exactitud (`7.22 × 10⁻¹⁴`)** que `RobustScaler` en los archivos gigantes de `04_transformed` (2–8 GB) preserva `R²` intacto.
- **Analogías:** *(1) Un multimillonario en un salón jala el promedio por elevar errores al cuadrado (`e²`); winsorizar le pone un techo sin expulsarlo del salón. (2) Medir personas en centímetros/kilos o en pulgadas/libras cambia la pendiente por cambio de unidades, pero la fuerza real de la relación (`R²`) jamás cambia.*

#### b) Problema, datos y reglas aplicadas
- **Capas:** `03_processed` (Versión A y B, `1,738,738` filas), `02_interim` (legado `test+val`, `348,263` vs `314,904` filas) y `04_transformed` (`X_train.csv` `8.4 GB` y `X_test.csv` `2.1 GB` leídos por prefijo binario sin agotar RAM + `transformers.joblib`).
- **Pares evaluados:** `n_skills_competence → n_skills_essential` y `n_skills_knowledge → n_skills_essential`.
- **Reglas activas:** `MR-06`, `MR-07`, `MR-08`.

#### c) Fórmulas explicadas símbolo por símbolo
$$\tilde{x} = \frac{x - c_x}{s_x}, \quad \tilde{y} = \frac{y - c_y}{s_y} \implies \tilde{a}_1 = a_1 \frac{s_x}{s_y}, \quad \tilde{a}_0 = \frac{a_0 + a_1 c_x - c_y}{s_y}, \quad \tilde{R}^2 = R^2, \quad \tilde{S}_{y/x} = \frac{S_{y/x}}{s_y}$$
- `cₓ, cᵧ`: centros de `RobustScaler` (la **mediana** real en JobPath: `competence = 18`, `knowledge = 3`, `essential = 20`).
- `sₓ, sᵧ`: escalas de `RobustScaler` (el **rango intercuartílico IQR = Q3 − Q1**: `competence = 11`, `knowledge = 5`, `essential = 13`).
- `ã₁, ã₀, R̃², S̃_{y/x}`: parámetros del modelo MCO tras escalar las columnas en `04_transformed`.
- **Por qué `R²` es invariante:** tanto `Sᵣ` como `Sₜ` quedan divididos por `sᵧ²`, que se cancela en `1 − Sᵣ/Sₜ`.

#### d) Cadena exacta de cómo se sacó cada conclusión
| Hallazgo | Dato (`CSV`) | Resultado exacto | Control / Matiz crítico | Conclusión defendible |
|---|---|---|---|---|
| **1. Winsorizar IQR supera a borrar filas** | `rl05_four_way_outlier_comparison.csv` (`competence → essential`) | Ver. A: `Sy/x = 4.0872`, `R² = 0.9072`. **Ver. B (IQR):** `Sy/x = 3.1915` (**`-21.9 %`**), `R² = 0.8983`, **`0` filas perdidas**. Borrado legado: pierde **`33,359` filas (`-9.58 %`)** y `Sy/x` casi no cambia (`4.1147 → 4.1105`). | Se documenta la **asimetría muestral**: `02_interim` legado solo contiene `test+val` (`348k`), mientras `03_processed` cubre todo (`1.74M`). | La winsorización IQR reduce la dispersión residual sin amputar perfiles profesionales de alta especialización. |
| **2. Trade-off honesto en `knowledge → essential`** | `rl05_four_way_outlier_comparison.csv` (`knowledge → essential`) | Ver. A: `Sy/x = 10.6664`, `R² = 0.3680` (🟡 Moderado). Ver. B: `Sy/x = 8.4934` (`-20.4 %`), pero **`R² = 0.2795` (🔴 Rechazado `MR-06`)**. | Al recortar `knowledge` de `45 → 13.5`, `Sₜ` se comprime (`-44.4 %`) más rápido que `Sᵣ` (`-36.6 %`), bajando `R²`, y se rompe la identidad `E = C + K + U` en la cola extrema. | Por eso JobPath conserva **ambas versiones (A y B)** en experimentación CRISP-DM. |
| **3. Certificación `04_transformed` (8/8 OK)** | `rl05_affine_scale_invariance.csv` | `con/sin × train/test × 2 pares` = **8/8 controles PASS**, error máximo global **`7.216 × 10⁻¹⁴ < 10⁻¹⁰`** (`~13.1` dígitos). | Ejemplo `train` Ver. A: `competence` `ã₁ = 0.9548` (`R² = 0.9072`), `knowledge` `ã₁ = 0.7247` (`R² = 0.3689`), exactos a teoría. | El escalado `RobustScaler` en `04_transformed` es algebraicamente transparente y libre de corrupción o fuga. |

#### e) Qué mostrar en vivo en la presentación
- **Simulador (Diap. 4):** Alterna entre **`RobustScaler Comp. (11, 13)`** (`ã₁ = 0.9548`, `S̃y/x = 0.3147`, `R² = 0.9072`) y **`RobustScaler Know. (5, 13)`** (`ã₁ = 0.7247`, `S̃y/x = 0.8207`, `R² = 0.3689`), mueve libremente los sliders y demuestra en vivo que **`R²` no se mueve ni una milésima**, luego contrasta esos números exactos en la tabla de la **Diap. 7**.

#### f) Qué SÍ decir vs. Qué NUNCA decir
| ✅ Frase correcta | ❌ Frase prohibida |
|---|---|
| *"Winsorizar baja `Sy/x` en ambos pares (`-21.9 %` y `-20.4 %`), pero en `knowledge` baja `R²` debajo de `0.30`; por eso mantenemos Versión A y B."* | *"Winsorizar siempre mejora tanto `Sy/x` como `R²` en todas las variables."* |
| *"`E = C + K + U` significa `Esenciales = Competencias + Conocimientos + Sin clasificar`."* | Mencionar `E = C + K + U` sin explicar qué representa cada letra. |

#### g) Preguntas difíciles del docente y respuestas ganadoras
1. **¿Cómo leyeron archivos CSV de 8.4 GB sin colapsar la memoria RAM?**
   - *Respuesta:* En `loaders.py` implementamos un lector binario por prefijo (`raw_line.split(b',', max_idx+1)`) que extrae únicamente las 3 columnas numéricas densas (`essential`, `competence`, `knowledge`) sin cargar las casi `2,985` columnas one-hot dispersas.
2. **¿Por qué no hay script de GeoGebra para el Caso 04 (`RL-05`)?**
   - *Respuesta:* Porque GeoGebra Classic en navegador no está diseñado para `1.74 millones` de puntos; por ello la verificación se hace en Python comparando contra `numpy.polyfit` y contra las fórmulas cerradas de invarianza afín con tolerancia `< 10⁻¹⁰` (validado en `unittest`).

---

### Caso 05 — `IDEA-LG-01`: Curva de Supervivencia Laboral `S(q)` y Fenómeno de Runge (Lagrange)

- **Presentación:** `05_IDEA_LG_01_Supervivencia_Y_Runge/presentacion_IDEA_LG_01.html`
- **Tablas clave:** `lg01_survival_curve_S_q.csv`, `lg01_milestone_P3_weights_and_eval.csv`, `lg01_runge_phenomenon_benchmark.csv`, `lg_monomial_expansions.csv`

#### a) Resumen en 30 segundos y analogía
Construimos la curva empírica de permanencia laboral `S(q)` sobre `1,643,772` empleos **cerrados (`~es_vigente`)**, la reconstruimos con un polinomio cúbico de Lagrange `P₃(q)` desde solo **4 hitos** (`1, 2, 5 y 10 años`), y demostramos en vivo el **Fenómeno de Runge** al subir a grado 16 con nodos equiespaciados (`-248 %` de probabilidad imposible!) frente a la estabilidad de **Chebyshev-Lobatto** (**`19.4×`** menos error y **`0` violaciones `[0,1]` en todos los grados**) y **Lagrange Local `P₂`**.
- **Analogía:** *Una varilla elástica pasa suavemente por 4 clavos. Si clavas 17 clavos a igual distancia en una curva muy empinada, la varilla da latigazos gigantes cerca de los bordes (Fenómeno de Runge). Solución: acercar los clavos hacia los extremos (Chebyshev-Lobatto) o usar trocitos cortos de 3 puntos (`P₂` local).*

#### b) Problema, datos y reglas aplicadas
- **Capa:** `03_processed` (Versión A filtrada estrictamente a `~es_vigente` → `1,643,772` empleos cerrados).
- **4 hitos de `P₃(q)`:** `q = 4` (1 año: `66.09 %`), `q = 8` (2 años: `37.05 %`), `q = 20` (5 años: `13.58 %`), `q = 40` (10 años: `4.30 %`).
- **Reglas activas:** **`MR-09`** (`~es_vigente`) y **`MR-04`** (deduplicación de nodos enteros tras redondear Chebyshev-Lobatto).

#### c) Fórmulas explicadas símbolo por símbolo
$$P_n(q) = \sum_{i=0}^{n} S(q_i)\,L_i(q), \qquad L_i(q) = \prod_{\substack{j=0\\ j\ne i}}^{n} \frac{q - q_j}{q_i - q_j}$$
$$q_k^{\text{Lob}} = \operatorname{round}\!\left(\frac{a+b}{2} + \frac{b-a}{2}\cos\!\left(\frac{k\pi}{n}\right)\right), \quad k = 0 \dots n$$
- `S(q)`: probabilidad empírica de que un empleo cerrado dure al menos `q` trimestres (`q = 4` es 1 año).
- `Lᵢ(q)`: polinomio base (peso con signo) asociado al nodo `qᵢ`. Cumple dos propiedades de oro: **Delta de Kronecker** (`Lᵢ(qᵢ) = 1`, `Lᵢ(qⱼ) = 0` para `j ≠ i`, error `0.0`) y **Partición de la unidad** (`∑Lᵢ(q) = 1` en cualquier `q`, error `4.44 × 10⁻¹⁶`).
- **Forma monómica expandida equivalente** (`lg_monomial_expansions.csv`): `P₃(q) = −7.91×10⁻⁵ q³ + 0.005845 q² − 0.133867 q + 1.107889` (idéntica a `Polynomial(P)` en GeoGebra, diff `5.05 × 10⁻¹⁵` vs SciPy).
- `qₖᴸᵒᵇ`: **nodos de Chebyshev-Lobatto** (`cos(kπ/n)`), que agrupan nodos en los bordes e **incluyen siempre exactamente los extremos `q = 1` y `q = 40`**.

#### d) Cadena exacta de cómo se sacó cada conclusión
| Hallazgo | Dato (`CSV`) | Resultado exacto | Control crítico | Conclusión defendible |
|---|---|---|---|---|
| **1. Interpolación `P₃(12)` vs. extrapolación `P₃(48)`** | `lg01_milestone_P3_weights_and_eval.csv` | En 3 años (`q=12`): pesos `[-0.3889, +1.1667, +0.2333, -0.0111]` (`∑=1.0`), `P₃(12) = 0.2065` vs real `0.2519` (err `0.0455`). En 12 años (`q=48`, extrap.): pesos estallan `[-3.89, +6.42, -3.67, +2.14]`, dando **`P₃(48) = -0.5984` (`-59.8 %`!)**. | Comprobación de unicidad vs `scipy.interpolate.lagrange`: `5.05 × 10⁻¹⁵`. | Dentro de `[4, 40]` los pesos están acotados; fuera del rango los pesos alternantes disparan el polinomio a probabilidades imposibles. |
| **2. Explosión de Runge vs. Chebyshev-Lobatto y `P₂`** | `lg01_runge_phenomenon_benchmark.csv` (grados `3, 5, 8, 12, 16`) | Grado 16 Equiespaciado: **`E∞ = 2.5262`**, `min = -2.4827` (`-248 %`, `2` violaciones). **Chebyshev-Lobatto (15 nodos únicos):** **`E∞ = 0.1301`** (**`19.4×` mejor**), **`0` violaciones en TODOS los grados (`3..16`)**. **Local `P₂` grado 12:** mejor `E∞ = 0.1196` (`0` violaciones). | En grado 16, al redondear 17 nodos coseno a enteros en `[1, 40]`, 2 pares cercanos a los bordes coinciden y se deduplican por `MR-04` → `15 nodos*`. | Aumentar el grado con nodos equiespaciados **destruye** el ajuste; Chebyshev-Lobatto y `P₂` local eliminan la explosión de bordes y las violaciones de `[0, 1]`. |
| **3. No-monotonicidad y apilamiento anual (*heaping*)** | `lg01_milestone_P3_weights_and_eval.csv` y `lg01_survival_curve_S_q.csv` | `P₃(16) = 0.1384 < P₃(28) = 0.2058` (la cúbica "sube" entre 4 y 7 años aunque `S(q)` siempre baja). Además `S(q)` cae en escalones cada 4 trimestres (1, 2, 3 años exactos). | Los polinomios de Lagrange no imponen monotonicidad y los saltos anuales crean un piso de error `~0.12–0.13`. | Para sistemas productivos de supervivencia, preferir **`P₂` local** o **PCHIP** (interpolación cúbica monótona). |

#### e) Qué mostrar en vivo en la presentación
- **Simulador de pesos `L₀..L₃` (Diap. 4):** Haz clic en **`Hito 1a (q=4)`** (verás solo `L₀ = 1.00`, los otros en `0.00` = Kronecker), luego **`Interpolar 3a (q=12)`** (`P₃ = 20.65 %`, `ΣLᵢ = 1.0000`) y finalmente **`Extrap. 12a (q=48)`** (barras disparadas y alerta roja `-59.84 %`!).
- **Gráfica Runge (Diap. 5, Fig. 2):** Haz zoom y muestra la curva equiespaciada cayendo hasta `-2.48` frente a Chebyshev-Lobatto pegado a la curva real.
- **GeoGebra (Diap. 7):** Explica que `p(x)` (manual con `L₀..L₃`) y `q = Polynomial(P)` se superponen píxel por píxel (Teorema de Unicidad).

#### f) Qué SÍ decir vs. Qué NUNCA decir
| ✅ Frase correcta | ❌ Frase prohibida |
|---|---|
| *"Usamos Chebyshev-Lobatto (`cos(kπ/n)`) porque ancla los extremos `q=1` y `q=40`, logrando `0` violaciones de `[0,1]` desde grado 3 hasta grado 16."* | *"Con más nodos equiespaciados siempre mejora la interpolación polinomial."* |
| *"P₃(q) ilustra perfectamente las bases `Lᵢ`, pero oscila hacia arriba en `q=28`; en producción se prefiere `P₂` local o PCHIP."* | *"P₃(q) es monótonamente decreciente en todo `[4, 40]`."* |

#### g) Preguntas difíciles del docente y respuestas ganadoras
1. **¿Por qué cambiaron de Chebyshev de 1.ª especie a Chebyshev-Lobatto (`cos(kπ/n)`)?**
   - *Respuesta:* Porque los nodos de 1.ª especie son estrictamente interiores (`[2..39]` en grados 3 y 5); al evaluar en `q = 1` extrapolaban a la izquierda produciendo probabilidades `> 1` (`1.11` y `1.23`). Chebyshev-Lobatto siempre incluye los extremos exactos `1` y `40`, eliminando toda extrapolación de borde y logrando `0` violaciones en todos los grados.
2. **¿Por qué en grado 16 Chebyshev-Lobatto tiene `15 nodos*` en vez de `17`?**
   - *Respuesta:* Porque la variable `q` son trimestres enteros en `[1, 40]`; al agruparse los nodos de coseno muy pegados cerca de `1` y `40`, al redondear a entero dos nodos caen sobre el mismo trimestre y la guarda `MR-04` los deduplica para impedir división por cero.

---

### Caso 06 — `IDEA-LG-02`: Varianza Acumulada PCA — Lagrange Directo e Inverso

- **Presentación:** `06_IDEA_LG_02_PCA_Lagrange_Inversa/presentacion_IDEA_LG_02.html`
- **Tablas clave:** `lg02_pca_50k_reference.csv`, `lg02_pca_forward_P3_eval.csv`, `lg02_pca_inverse_effective_dim.csv`, `lg_monomial_expansions.csv`

#### a) Resumen en 30 segundos y analogía
Recalculamos **en vivo en `float64`** las curvas de varianza acumulada del PCA (`50,000` filas, replicando `4.1_PCA_completo.ipynb`) y aplicamos Lagrange en dos sentidos: **directo** (predecir `V(4)` desde 4 nodos con solo `0.0002` de error) e **inverso** (darle la vuelta a la tabla para hallar cuántos componentes `k(V*)` requiere una meta de `80–95 %`), demostrando en vivo la **guarda `MR-04`** cuando la colinealidad de Versión A produce `V(9) = V(10) = 1.0`.
- **Analogía:** *La batería del celular al revés: en sentido directo preguntas "llevo 40 min cargando, ¿qué % tengo?"; en sentido inverso preguntas "quiero llegar al 90 %, ¿cuántos minutos necesito?". En `100 %` falla invertir porque al minuto 90 y al minuto 100 ambos valen `100 %`, y restar `100 − 100 = 0` divide por cero.*

#### b) Problema, datos y reglas aplicadas
- **Capa:** `03_processed` (muestra fija `n = 50,000`, `random_state = 42`, Versión A con outliers y Versión B winsorizada IQR — **cero tablas hardcodeadas**).
- **Directo:** entrenamiento `k ∈ {1, 3, 5, 8}`, evaluación oculta `k ∈ {2, 4, 6, 7}`.
- **Inverso:** tramo estrictamente creciente `k = 1..6` para metas `V* ∈ {80 %, 85 %, 90 %, 95 %}`.
- **Regla clave:** **`MR-04`** (`validate_distinct_nodes()` bloquea la meseta `V_A(9) = V_A(10) = 1.0`).

#### c) Fórmulas explicadas símbolo por símbolo
$$\text{Directa: } \hat{V}(k) = \sum_i V(k_i)\,L_i(k), \qquad \text{Inversa (tramo creciente): } \hat{k}(V^*) = \sum_i k_i\,L_i^{(V)}(V^*)$$
- `k`: número de componentes principales (`1` a `10`).
- `V(k)`: varianza acumulada retenida por los primeros `k` componentes (`0` a `1`, es decir `0 %` a `100 %`).
- `V*`: meta deseada de varianza (ej. `0.90 = 90 %`).
- `k_rec = ceil(k̂)`: función techo (redondeo al entero superior) porque no existen "4.33 componentes" y hay que garantizar `V(k_rec) ≥ V*`.
- **Monomios exactos (`lg_monomial_expansions.csv`):**
  - Ver. A: `P₃(k) = 0.002746k³ − 0.057466k² + 0.412549k − 0.028723`
  - Ver. B: `P₃(k) = 0.002993k³ − 0.059596k² + 0.403991k + 0.049433`

#### d) Cadena exacta de cómo se sacó cada conclusión
| Hallazgo | Dato (`CSV`) | Resultado exacto | Control crítico | Conclusión defendible |
|---|---|---|---|---|
| **1. Precisión directa en tabla suave y exacta** | `lg02_pca_forward_P3_eval.csv` | Ver. A en `k = 4`: real `0.877604`, `P₃(4) = 0.877777` (**err `0.000173`** = `0.017 %`). En `k = 2, 6, 7`: errores `0.014–0.035`, `∑Lᵢ = 1.0`. | SciPy diff `5.11 × 10⁻¹⁵` (Ver. A) y `1.55 × 10⁻¹⁵` (Ver. B). | En tablas deterministas suaves y sin ruido, Lagrange directo reconstruye valores intermedios con precisión milimétrica. |
| **2. Inversa `k(V*)`: Versión B ahorra 1 componente** | `lg02_pca_inverse_effective_dim.csv` | Meta `80 %`: Ver. A pide `4` (`3.20`) vs. Ver. B pide **`3`** (`2.94`, logra `80.59 %`). Meta `95 %`: Ver. A pide `6` (`5.16`) vs. Ver. B pide **`5`** (`4.92`, logra `95.36 %`). | `8/8` combinaciones cumplen `meets_target = True`; el simulador usa **Local `P₂`** (evita oscilación `P₅` en extremos como `55 %`). | Limpiar outliers con IQR compacta más varianza en menos dimensiones principales. |
| **3. Rango 9 vs. ruptura de colinealidad y `MR-04`** | `lg02_pca_50k_reference.csv` (en vivo `float64`) | `PC10` Ver. A: **`6.74 × 10⁻¹⁸`** (cero de máquina → `V(9) = V(10) = 1.0`, **rango 9**). `PC10` Ver. B: **`5.534 × 10⁻⁵`** (rango completo 10). | Al intentar invertir los 10 puntos de Ver. A, `MR-04` lanza `ValueError: min gap = 0.000e+00 < 1.0e-12`. | En Ver. A la identidad `E = C + K + U` vuelve redundante la 10.ª dimensión; la winsorización univariada IQR rompe esa igualdad exacta en las colas. |

#### e) Qué mostrar en vivo en la presentación
- **Simulador `k(V*)` (Diap. 4):** Pulsa **`80 %`** (Ver. A = `4` comp. vs Ver. B = `3` comp.), **`90 %`** (`k = 4.33` y `4.10` → `5` comp.) y **`95 %`** (Ver. A = `6` vs Ver. B = `5`), y arrastra a **`55 %`** para mostrar que `Local P₂` se mantiene 100 % monótono (`kB = 1.46 → 2 comp.`).
- **GeoGebra (Diap. 7):** Resalta `A_eval = (4, 0.877777)` y la verificación de unicidad `p(x) = Polynomial(P)`.

#### f) Qué SÍ decir vs. Qué NUNCA decir
| ✅ Frase correcta | ❌ Frase prohibida |
|---|---|
| *"Las curvas PCA de 50k filas se recalculan en vivo en `float64` desde `03_processed`, replicando `4.1_PCA_completo.ipynb`."* | *"Copiamos los números de PCA a mano en el código."* (Eso ya se eliminó en V2). |
| *"Usamos `Lagrange Local P₂` en el simulador para garantizar monotonicidad incluso en `V* = 55 %`."* | *"Podemos invertir los 10 componentes de Versión A a la vez sin filtrar la meseta."* |

#### g) Preguntas difíciles del docente y respuestas ganadoras
1. **Si quisiéramos agregar el nodo `k = 6` al polinomio `P₃(k)` de Lagrange, ¿podemos reutilizar `L₀..L₃` sin recalcularlos?**
   - *Respuesta:* **No.** Esa es la principal desventaja de Lagrange (Diapositiva 5 del curso): al añadir un punto nuevo hay que recalcular todos los `Lᵢ(x)` porque cambia cada producto. Para construir polinomios incrementalmente se usarían **diferencias divididas de Newton**.
2. **¿Por qué en Versión B aparece varianza no nula (`5.53e-5`) en `PC10` si las columnas son las mismas?**
   - *Respuesta:* Porque el recorte IQR se aplica columna por columna; cuando un registro supera el tope superior en `essential` pero no en sus sumandos `competence/knowledge/unclassified`, se rompe la relación lineal exacta `E = C + K + U`, devolviendo rango completo 10.

---

### Caso 07 — `IDEA-HYB-01`: Laboratorio Comparativo "¿Interpolar o Ajustar?"

- **Presentación:** `07_IDEA_HYB_01_Laboratorio_Interpolar_vs_Ajustar/presentacion_IDEA_HYB_01.html`
- **Tablas clave:** `hyb01_loocv_and_extrapolation_matrix.csv`, `hyb01_method_selection_rubric.csv`

#### a) Resumen en 30 segundos y analogía
Enfrentamos los **4 métodos** (`MCO`, `Lagrange Global Equiespaciado`, `Chebyshev-Lobatto` y `Lagrange Local P₂`) sobre **4 terrenos reales de JobPath** mediante dos exámenes objetivos: **LOOCV interior** (dentro del rango) y **Extrapolación +2 pasos** (fuera del rango), demostrando con datos reales la Diapositiva 2 de ambas presentaciones del curso.
- **Analogía:** *Elegir el zapato correcto para cada deporte: los patines vuelan en pista lisa (`Lagrange Global` en PCA exacto), pero te hacen caer al instante en un terreno ondulado (`serie macro anual`, donde el error explota `108×`).*

#### b) Problema, datos y reglas aplicadas
- **4 regímenes reales:**
  1. **Suave casi lineal (`n = 10`, `R² = 0.9955`):** `mean_skills(k)` por paso de carrera.
  2. **Serie macro curva con fluctuación (`n = 18`, `R² = 0.8995`):** `mean_skills(año)` `2000–2017` (forma en arco).
  3. **No lineal empinada (`n = 36`, `R² = 0.6935`):** curva de supervivencia `S(q)` en forma de L.
  4. **Tabla cóncava exacta (`n = 8`, `R² = 0.7964`):** varianza acumulada `PCA V(k)` Versión B.
- **Nota metodológica transparente:** en regímenes largos (`n = 18, 36`), los interpoladores globales se acotan a **grado `≤ 12`** para evitar desbordamiento numérico extremo de grado 35.

#### c) Fórmulas explicadas símbolo por símbolo
$$\text{LOOCV-RMSE} = \sqrt{\frac{1}{n-2}\sum_{i=2}^{n-1}\left(y_i - \hat{f}_{(-i)}(x_i)\right)^2}, \qquad \text{Extrap-MAE}_{+2} = \frac{1}{2}\sum_{m=1}^{2}\left|y_{n+m} - \hat{f}(x_{n+m})\right|$$
- `\hat{f}_{(-i)}(xᵢ)`: predicción del método entrenado **ocultando el punto `i`**.
- **Por qué `i = 2..n−1`:** se evalúan solo puntos **interiores** (se excluyen los 2 extremos para no confundir interpolación con extrapolación).
- **Por qué NO medimos el error sobre los nodos de entrenamiento:** porque todo polinomio de Lagrange tiene error exactamente `0` en sus nodos por definición, lo que ocultaría sus oscilaciones entre nodos!

#### d) Cadena exacta de cómo se sacó cada conclusión (`hyb01_loocv_and_extrapolation_matrix.csv`)
| Régimen | Ganador Dentro (LOOCV RMSE) | Ganador Extrap. (+2 MAE) | Peor Método (y magnitud de fallo) | Por qué ganó ese método |
|---|---|---|---|---|
| **1. Casi lineal (`Pasos`, `n=10`)** | **MCO** (`0.0558`) | **MCO** (`0.0745`) | Lagrange Global (`0.2937` / **`71.28`** = `957×` peor!) | Con `R² = 0.9955` la señal es casi recta pura; MCO evita sobreajustar micro-variaciones. |
| **2. Serie curva (`Anual`, `n=18`)** | **Local `P₂`** (`0.1139`) | **Local `P₂`** (`0.1711`) | Lagrange Global (**`12.32`** = `108×` peor / **`386.36`**!) | La serie sube de `22.27` a un pico `24.27` (`2016`) y luego gira a la baja; una recta MCO deja sesgo de curvatura (`0.2396`), mientras `P₂` sigue el arco suavemente. |
| **3. Empinada (`Superv.`, `n=36`)** | **Local `P₂`** (`0.0524`) | **Local `P₂`** (`0.0060`) | Lagrange Global (`0.3777` / **`38.89`** = `6,495×` peor!) | La forma en L rompe la recta MCO (`0.1301`) y dispara Runge en Global; `P₂` local y Chebyshev-Lobatto (`0.0620`) doman la curvatura. |
| **4. Tabla exacta (`PCA`, `n=8`)** | **Lagrange Global** (**`0.0036`**) | **Local `P₂`** (`0.0068`) | En LOOCV: **MCO** (`0.0765` = `21×` peor). En Extrap: Global (`0.2423`; Lobatto desempata con `0.1741`). | Pocos nodos (`n=8`), función exacta y sin ruido: el escenario soñado de Lagrange Global dentro del rango. |

#### e) Qué mostrar en vivo en la presentación
- **Selector interactivo (Diap. 4):** Recorre en orden los 4 botones (`1 · Casi Lineal → 2 · Serie Curva → 3 · No Lineal → 4 · Tabla Exacta`) señalando cómo cambian automáticamente las **2 píldoras de ganadores (`Dentro` vs `Extrap. +2`)** y el error catastrófico de `Lagrange Global` (`71.28`, `386.36`, `38.89`).
- **Gráficas (Diap. 5):** Amplía la Figura 2 (mapa de calor relativo `1.0×` = ganador) para ver la rúbrica de un vistazo.

#### f) Qué SÍ decir vs. Qué NUNCA decir
| ✅ Frase correcta | ❌ Frase prohibida |
|---|---|
| *"MCO y Lagrange no compiten para eliminarse: MCO gana en tendencias casi lineales, Lagrange Global en tablas exactas cortas (`n ≤ 8`), y `Local P₂` domina curvas suaves no lineales."* | *"Lagrange siempre es mejor que MCO porque pasa por todos los puntos."* |
| *"Renombramos el Régimen 2 a 'Serie Macro Curva con Fluctuación' porque tiene un arco real (`R²=0.90`), lo que explica por qué `P₂` supera a MCO."* | *"MCO perdió en el Régimen 2 porque el algoritmo falló."* |

#### g) Preguntas difíciles del docente y respuestas ganadoras
1. **Si las diapositivas dicen que MCO gana con ruido, ¿por qué en el Régimen 2 (`mean_skills` anual) MCO quedó 3.º detrás de `P₂` y Chebyshev-Lobatto?**
   - *Respuesta:* Porque al inspeccionar los datos reales de `2000–2019`, vimos que `mean_skills` no es ruido puro sobre una línea recta, sino una **curva suave en campana/arco** (crece hasta `2016` y gira a la baja en `2017–2019`). Por eso renombramos ese régimen con honestidad: MCO tiene sesgo de curvatura al forzar una línea recta sobre un arco, mientras `P₂` se adapta localmente.
2. **¿Por qué `Lagrange Local P₂` resultó tan buen comodín en 3 de 4 regímenes?**
   - *Respuesta:* Porque cada predicción usa solo los 3 puntos vecinos más cercanos (grado 2), lo que le permite doblarse en curvas no lineales sin sufrir jamás el Fenómeno de Runge de grados altos.

---

### Caso 08 — `IDEA-HYB-02`: Pack de Verificación GeoGebra, Precisión y Auditoría SHA-256

- **Presentación:** `08_IDEA_HYB_02_Pack_Verificacion_GeoGebra/presentacion_IDEA_HYB_02.html`
- **Archivos clave:** `verification_log.md`, `sha256_input_integrity.csv`, `geogebra_verification_index.md`, `tests/metodos_numericos/`

#### a) Resumen en 30 segundos y analogía
Es el **sello de confianza e ingeniería** de todo el proyecto: demuestra que nuestras fórmulas escritas desde cero coinciden con `NumPy` y `SciPy` entre **11 y 16 dígitos exactos**, entrega **5 scripts listos para pegar en GeoGebra Classic**, certifica con **SHA-256 completo de 64 caracteres** que los `19` insumos de `data/` jamás fueron alterados, aprueba la **auditoría semántica bilingüe (EN+ES)** en `28` archivos (`0` violaciones) y pasa **`19 / 19` pruebas automatizadas**.
- **Analogía:** *El doble conteo del banco + sobre sellado: contamos los billetes a mano (código propio), los pasamos por la contadora certificada (NumPy/SciPy), entregamos recibo a un auditor externo (GeoGebra) y sellamos la bóveda con huella dactilar (SHA-256).*

#### b) Problema, datos y reglas aplicadas
- **Cobertura:** los `39` modelos MCO del proyecto, todos los polinomios de Lagrange (`LG-01`, `LG-02`), las `8` pruebas de invarianza afín, las `12` figuras PNG a `150 DPI`, los `5` scripts GeoGebra + índice, los `19` archivos de entrada (`4` capas) y `28` archivos documentales auditados en inglés y español.

#### c) Fórmulas explicadas símbolo por símbolo
$$D = -\log_{10}(\max(\text{error}, 10^{-16})), \qquad e_{\text{rel}} = \frac{|\text{diff}_{\text{abs}}|}{\max(|a_0|, |a_1|, 1)}$$
- `D`: número de **dígitos decimales exactos** que coinciden con `NumPy`/`SciPy` (ej. error `10⁻¹⁴ → D = 14` dígitos; línea de aprobación en `D = 10` equivale a `< 10⁻¹⁰`). Se usa piso `10⁻¹⁶` porque `log₁₀(0)` no existe (`16` dígitos = precisión máquina `float64`).
- `e_rel`: error relativo que normaliza el tamaño del parámetro (clave cuando un intercepto sin centrar vale `2.18 millones`).

#### d) Cadena exacta de cómo se sacó cada conclusión
| Control auditado | Archivo fuente | Métrica exacta obtenida | Umbral exigido | Veredicto |
|---|---|---|---|---|
| **39 Modelos MCO vs `numpy.polyfit`** | `ols_summary_all_ideas.csv` y `verification_log.md` | Error **relativo** máx: **`2.294 × 10⁻¹²`** (`D = 11.64` dígitos, en `RL-05 Ver. B`). Bruto máx: `1.523e-07` en `n_starts` (`|a₀|=2.18e6`, rel `6.98e-14`). | `< 10⁻¹⁰` (`D ≥ 10`) | ✔ PASS (`43×` bajo umbral) |
| **8 Controles Invarianza Afín** | `rl05_affine_scale_invariance.csv` | **`7.216 × 10⁻¹⁴`** (`D = 13.14` dígitos) | `< 10⁻¹⁰` | ✔ PASS (`1,380×`) |
| **Lagrange `LG-01 P₃` vs `SciPy`** | `lg_monomial_expansions.csv` | SciPy **`5.05 × 10⁻¹⁵`** · Unidad **`4.44 × 10⁻¹⁶`** · Kronecker **`0.0`** | `< 10⁻¹⁰` | ✔ PASS (precisión máquina) |
| **Integridad solo-lectura `data/`** | `sha256_input_integrity.csv` | **`19 / 19` intactos** con digest completo de **64 hex**: `13 full_sha256` (`≤ 64 MiB`: `01_raw` 3, `02_interim` 7, `04/map` 3) + `6 sampled_24MiB_plus_meta_sha256` (`> 64 MiB`: `03_processed` 2, `X_train/X_test` 4). | `100 %` sin mutación | ✔ PASS |
| **Auditoría bilingüe (`MR-07/08`) + Enlaces + Tests** | `test_pipeline_integration.py` y `verification_log.md` | **`28` archivos escaneados (`0` violaciones EN+ES)** · **`0` enlaces rotos** en `fuentes_notebooklm/` y `README.md` · **`19 / 19` tests OK** (`2.39 s`). | `0` fallos | ✔ PASS |

#### e) Qué mostrar en vivo en la presentación
- **Visor de 5 scripts GeoGebra (Diap. 4):** Haz clic en 2 o 3 pestañas (especialmente `RL-02` con alerta `MR-06` y `LG-01` con forma monómica), señala la barra verde/turquesa *"Qué compruebas"* y el botón **`Copiar comandos`**.
- **Dashboard (Diap. 5):** Haz zoom y explica la línea vertical en `10` dígitos (`< 10⁻¹⁰`) y cómo todas las barras la superan holgadamente.
- **Tabla SHA-256 y 3 comandos (Diap. 6):** Muestra el desglose transparente `13 completos + 6 muestreados 24 MiB` y los 3 comandos reproducibles.

#### f) Qué SÍ decir vs. Qué NUNCA decir
| ✅ Frase correcta | ❌ Frase prohibida |
|---|---|
| *"Guardamos los 64 caracteres SHA-256 completos y declaramos `hash_mode`: hash íntegro en los 13 archivos `≤ 64 MiB` y muestreo 24 MiB + tamaño exacto en los 6 archivos masivos de 1.4–8.4 GB."* | *"Calculamos SHA-256 byte por byte sobre los 22 GB en 1 segundo."* (Sería impreciso frente a la auditoría). |
| *"El error relativo máximo de MCO en los 39 modelos es `2.29 × 10⁻¹²` (supera en `43×` el umbral `10⁻¹⁰`)."* | *"El error absoluto en todos los 39 modelos fue `10⁻¹⁴`."* |

#### g) Preguntas difíciles del docente y respuestas ganadoras
1. **¿Por qué empiezan las pruebas unitarias con los ejemplos de las diapositivas de clase (Servidor Web, LOC, Temperatura CPU) antes de probar JobPath?**
   - *Respuesta:* Son nuestros *golden fixtures* (pruebas doradas): al verificar primero que `ols.py` y `lagrange.py` reproducen a 10+ decimales las soluciones hechas a mano en clase (`a₁=28.5714`, `a₁=2.05`, `P₂(65)=66.375`, `P₂(2)=11`), probamos que el motor matemático es correcto antes de escalarlo a `1.74 millones` de filas.
2. **¿Qué pasa si abren las presentaciones HTML en el salón sin conexión a internet?**
   - *Respuesta:* Son 100 % autocontenidas: las 12 imágenes van embebidas en `base64`, todos los simuladores corren en JavaScript local y las 14 fórmulas tienen respaldo offline automático (`data-plain` en Unicode) si el CDN de KaTeX no carga.

---

## 3. Glosario Maestro Completo (A–Z)

| Término / Símbolo | Significado claro (para explicar en voz alta) | Dónde aparece en JobPath |
|---|---|---|
| **`01_raw` → `04_transformed`** | Las 4 etapas del pipeline de datos: crudos (`01`), limpios/ESCO (`02`), datasets analíticos A y B (`03`) y matrices escaladas ML (`04`). | Transversal (Casos 01–08). |
| **`a₀` (Intercepto)** | Valor que predice la recta cuando `X = 0`. Al centrar `t = año − 2000`, se vuelve el valor real en el año 2000. | Casos 01–04. |
| **`a₁` (Pendiente)** | Cuánto sube o baja `Y` en promedio por cada unidad que aumenta `X` (`Δŷ / Δx`). | Casos 01–04. |
| **Acople parte-todo** | Cuando `X` es un subconjunto aditivo de `Y` (ej. `n_ess_comp` forma parte de `n_essential`), lo que eleva `R²` por estructura interna del catálogo. | Caso 02 (`RL-02`). |
| **Apilamiento anual (*heaping*)** | Tendencia en hojas de vida a reportar duraciones exactas de 1, 2 o 3 años, generando escalones cada 4 trimestres en `S(q)`. | Caso 05 (`LG-01`). |
| **Cancelación numérica** | Pérdida de precisión decimal al restar dos números enormes casi iguales (ej. `n∑x² − (∑x)²` con años `2010²`). Se evita centrando `X`. | Caso 03 (`RL-04`). |
| **`ceil(k)` (Función techo)** | Redondear hacia arriba al entero siguiente (ej. `ceil(4.33) = 5` componentes) para no quedarse por debajo de una meta de varianza `V*`. | Caso 06 (`LG-02`). |
| **Censura a la derecha (`~es_vigente`)** | Registros recientes cuyo desenlace final aún no ha ocurrido (empleos todavía activos sin fecha real de fin). | Casos 01, 03, 05 (`MR-09`). |
| **Centrado de variable** | Restar un origen de referencia (`t = año − 2000`) para mejorar estabilidad numérica e interpretabilidad de `a₀` sin cambiar `a₁` ni `R²`. | Caso 03 (`RL-04`). |
| **Centroide `(x̄, ȳ)`** | Punto formado por el promedio de `X` y el promedio de `Y`; toda recta MCO pasa exactamente por él. | Casos 01–04. |
| **Chebyshev-Lobatto** | Distribución de nodos `cos(kπ/n)` más densos en los bordes e incluyendo siempre los extremos `[a, b]`; mitiga el Fenómeno de Runge sin violar `[0, 1]`. | Casos 05 y 07. |
| **Colinealidad / Rango 9** | Cuando una columna es combinación lineal exacta de otras (`E = C + K + U`), solo 9 de 10 columnas son independientes y `PC10 ≈ 0`. | Caso 06 (`LG-02`). |
| **Delta de Kronecker `Lᵢ(xⱼ)=δᵢⱼ`** | Propiedad de las bases de Lagrange: cada peso `Lᵢ` vale `1` en su propio nodo y `0` en todos los demás. | Casos 05 y 06. |
| **`E = C + K + U`** | Identidad de ESCO: `Esenciales = Competencias + Conocimientos + Sin clasificar`. | Casos 04 y 06. |
| **`E∞` (Error máximo)** | Peor error absoluto puntual `max |y − ŷ|` en todo el intervalo evaluado. | Caso 05 (`LG-01`). |
| **ESCO v1.2.1 / ISCO-08** | Clasificación europea oficial de `3,039` oficios y sus competencias (`ESCO`), organizada en `10` grandes grupos profesionales (`ISCO-08`). | Todos los casos (esp. Caso 02). |
| **Extrapolación** | Usar un modelo para predecir **fuera** del rango observado de `X` (zona peligrosa en MCO y explosiva en Lagrange global). | Casos 01, 03, 05, 07. |
| **Fenómeno de Runge** | Oscilaciones gigantes cerca de los extremos al aumentar el grado de un polinomio interpolante con nodos equiespaciados. | Casos 05 y 07. |
| **`float64`** | Estándar IEEE 754 de doble precisión (~15–16 dígitos decimales significativos). | Casos 06 y 08. |
| **Forma monómica** | Escritura expandida del polinomio como `c₃x³ + c₂x² + c₁x + c₀`, algebraicamente idéntica a la forma de Lagrange. | Casos 05 y 06. |
| **`greenShare`** | Fracción de habilidades ligadas a sostenibilidad / transición verde exigidas por cada ocupación ESCO. | Casos 01, 02, 03. |
| **`hash_mode`** | Modo transparente de verificación SHA-256: `full_sha256` (`≤ 64 MiB`) o `sampled_24MiB_plus_meta_sha256` (`> 64 MiB`). | Caso 08 (`HYB-02`). |
| **Interpolación inversa** | Intercambiar ejes para hallar el valor de entrada `k` necesario para alcanzar una salida objetivo `V*` (exige monotonía estricta). | Caso 06 (`LG-02`). |
| **Invarianza afín** | Propiedad algebraica por la cual escalar linealmente `X` e `Y` (`RobustScaler`) no modifica `R²` y escala predeciblemente `a₁`, `a₀` y `Sy/x`. | Caso 04 (`RL-05`). |
| **Lagrange Local `P₂`** | Construir parábolas locales usando solo los 3 nodos más cercanos a cada consulta; evita el Fenómeno de Runge y funciona muy bien en curvas no lineales. | Casos 05, 06, 07. |
| **LOOCV** | *Leave-One-Out Cross-Validation*: ocultar cada punto interior uno a uno, re-ajustar sin verlo y medir el error de predicción. | Caso 07 (`HYB-01`). |
| **`−log₁₀(error)`** | Transformación que convierte errores pequeños en cantidad de dígitos exactos (`10⁻¹⁴ → 14` dígitos; umbral `10⁻¹⁰ → 10`). | Caso 08 (`HYB-02`). |
| **MAE / RMSE** | `MAE` = promedio de errores absolutos; `RMSE` = raíz del promedio de errores al cuadrado (penaliza más los errores grandes). Menor = mejor. | Casos 05 y 07. |
| **MCO (OLS)** | Mínimos Cuadrados Ordinarios: halla la recta única que minimiza la suma de residuos al cuadrado `Sᵣ = ∑eᵢ²`. | Casos 01–04, 07, 08. |
| **`MR-04` a `MR-09`** | Reglas metodológicas del proyecto (nodos distintos, rechazo `R²<0.30`, no causalidad, atribución ESCO, solo empleos cerrados). | Transversal. |
| **Ortogonalidad** | Ausencia total de relación lineal entre dos variables (`R² ≈ 0`, como `greenShare` vs `n_essential`). | Caso 02 (`RL-02`). |
| **Outlier / Winsorización IQR** | Dato extremo; winsorizar recorta valores fuera de `[Q1−1.5·IQR, Q3+1.5·IQR]` al límite en vez de borrar la fila. | Casos 04 y 06. |
| **Paradoja de Simpson** | Tendencia observada en el agregado global que desaparece o **invierte su signo** al analizar subgrupos/cohortes fijas (como `mean_green`). | Caso 01 (`RL-01`). |
| **Partición de la unidad (`∑Lᵢ=1`)** | Propiedad exacta de Lagrange: en cualquier punto `x` (incluso extrapolando), la suma de todos los pesos base vale siempre `1`. | Casos 05 y 06. |
| **PCA** | Análisis de Componentes Principales: transforma variables correlacionadas en componentes ortogonales ordenados por varianza explicada. | Caso 06 (`LG-02`). |
| **PCHIP** | Interpolación cúbica por tramos que preserva la monotonicidad (no crea rebotes falsos hacia arriba en curvas decrecientes). | Caso 05 (`LG-01`). |
| **`R²` y `r`** | `R²` (`0` a `1`): fracción de variación explicada por la recta. `r` (`-1` a `+1`): dirección (`+`/`-`) y fuerza de la relación lineal (`r² = R²`). | Casos 01–04, 07. |
| **Residuo (`eᵢ`)** | Error vertical entre el dato real y la recta: `eᵢ = yᵢ − ŷᵢ`. | Casos 01–04. |
| **`RobustScaler`** | Transformador `(x − mediana) / IQR` resistente a valores atípicos usado en `04_transformed`. | Caso 04 (`RL-05`). |
| **SHA-256 (64 hex)** | Huella digital criptográfica de 256 bits (64 caracteres hexadecimales) que certifica que ningún archivo en `data/` fue modificado. | Caso 08 (`HYB-02`). |
| **`Sₜ`, `Sᵣ` y `Sy/x`** | `Sₜ` = variación total; `Sᵣ` = suma de errores al cuadrado; `Sy/x = √(Sᵣ/(n−2))` = error típico vertical en unidades de `Y`. | Casos 01–04. |
| **Teorema de unicidad** | Dados `n + 1` puntos con `xᵢ` distintos, existe un **único** polinomio de grado `≤ n` que pasa por todos (`p(x) ≡ Polynomial(P)`). | Casos 05 y 06. |
| **WLS** | Mínimos Cuadrados Ponderados: asigna mayor peso a observaciones con mayor tamaño muestral (`n_k`) para comprobar robustez frente a heterocedasticidad. | Caso 01 (`RL-01`). |

---

## 4. Acordeón Final de 1 Página, Tiempos y Checklist Previo a Exponer

### 4.1 Los 8 Casos en Una Sola Vista

| # | Caso | Pregunta clave | Fórmula / Método estrella | Cifra estrella (V2) | Conclusión en 1 frase | Cuidado #1 al hablar |
|---|---|---|---|---|---|---|
| **01** | `RL-01` | ¿Cómo cambian las variables por paso `k=1..10`? | MCO + WLS + cohorte `≥10` | `R² = 0.9955` (`+0.225/paso`), WLS diff `1.67 %` | Competencias ESCO suben casi en recta; `mean_green` exhibe Paradoja de Simpson y duración falla en `k=15`. | `MR-07/08` (oficio ESCO, no causalidad). |
| **02** | `RL-02` | ¿Qué habilidades transfieren y cuándo rechazar MCO? | MCO + Semáforo `MR-06` + ISCO-08 | Transferibilidad `57.9 %` (Gerentes `74.0 %`); `greenShare R² = 0.00004` | Casi 6 de cada 10 habilidades extra transfieren; ser "verde" es ortogonal al número de habilidades. | Avisar acople parte-todo y rechazo `R²=0.28` en `ggb_rl02`. |
| **03** | `RL-04` | ¿Qué pasa al incluir cola censurada y extrapolar a 2027? | MCO centrado `t = año − 2000` + `MR-09` | `R² = 0.9729` cerrados → **`-4.96` trim. en 2027**; centrado **`4,672×`** mejor | 4 años censurados invierten la pendiente (`0.75 → 0.08`) y extrapolar produce duraciones negativas desde 2021. | Alto `R²` interno **no** valida extrapolar. |
| **04** | `RL-05` | ¿Conviene winsorizar y `RobustScaler` daña `R²`? | 4 vías outliers + Invarianza afín | `Sy/x -21.9 %` (`0` filas perdidas); err máx `7.22 × 10⁻¹⁴` | Winsorizar vence a borrar filas (`-9.6 %`) con trade-off en `knowledge`; `04_transformed` preserva `R²` intacto. | Mencionar que `knowledge` baja a `R²=0.2795` (Rechazado). |
| **05** | `LG-01` | ¿Cómo reconstruir `S(q)` sin caer en Runge? | Lagrange `P₃`, Chebyshev-Lobatto, `P₂` | Runge **`19.4×`** menor (`2.53 → 0.1301`), **`0` violaciones** `[0,1]` | Equiespaciado grado 16 explota (`-248 %`); Chebyshev-Lobatto y `P₂` local eliminan Runge y violaciones. | Explicar `15 nodos*` (deduplicación), no-monotonicidad y *heaping*. |
| **06** | `LG-02` | ¿Cuántos componentes PCA pide `80–95 %` de varianza? | Lagrange directo `P₃` + inverso `P₂` + `MR-04` | Err `P₃(4) = 0.0002`; Ver. B ahorra 1 comp. (`5` vs `6` en `95 %`) | En tablas exactas Lagrange brilla; `MR-04` protege contra la meseta de rango 9 (`V(9)=V(10)=1.0`). | Enfatizar PCA en vivo `float64` y `Local P₂` en simulador. |
| **07** | `HYB-01` | ¿Cuándo usar MCO, Global, Chebyshev o Local `P₂`? | Torneo `4 × 4` (LOOCV + Extrap. `+2`) | Global estalla `108×` en anual (`12.32`); gana `0.0036` en PCA | Cada método tiene su terreno: MCO (lineal), Global (tabla exacta corta), `P₂` local (curvas no lineales). | Aclarar que Régimen 2 es curvo en arco (`R²=0.90`). |
| **08** | `HYB-02` | ¿Cómo probamos exactitud y que `data/` no se tocó? | Triple verificación + SHA-256 64-hex + Tests | MCO rel `2.29 × 10⁻¹²`; `19/19` SHA-256; `19/19` tests; `0` viol. EN+ES | Cero cajas negras: 11–16 dígitos exactos vs NumPy/SciPy, 5 scripts GeoGebra y gobernanza reproducible. | Explicar `hash_mode` (`13` completos + `6` muestreados 24 MiB). |

### 4.2 Guion de Tiempos Recomendado
- **Versión rápida (10 minutos):** Apertura (`1 min`) → Bloque MCO `01–04` (`4 min`: énfasis en simulador RL-01, semáforo ISCO-5 RL-02, simulador 2027 RL-04 y selector 2 pares RL-05) → Bloque Lagrange `05–06` (`2.5 min`: simulador `L₀..L₃` + gráfica Runge y simulador PCA `k(V*)`) → Síntesis y Verificación `07–08` (`2.5 min`: selector de regímenes HYB-01 + visor GeoGebra y SHA-256 HYB-02).
- **Versión completa (20–25 minutos):** Apertura (`1.5 min`) + **`2.5 min` por cada caso** siguiendo el ritmo fijo: *Analogía (20 s) → Fórmula clave (25 s) → Simulador en vivo (40 s) → Gráfica con zoom + tabla (40 s) → GeoGebra + salvaguarda (25 s)*.

### 4.3 Checklist Técnico 2 Minutos Antes de Presentar
- [ ] Abrir [`presentaciones_separadas.html`](../presentaciones_separadas.html) en navegador a pantalla completa (`F`).
- [ ] Verificar atajos: `← →` o `Espacio` para pasar diapositiva, `Esc` para cerrar el zoom (`lightbox`) de las gráficas.
- [ ] Probar una vez los 3 simuladores estrella: `RL-04` (`2027 → -4.96`), `RL-05` (`Knowledge 5, 13 → 0.7247 / R² 0.3689`) y `LG-01` (`q=4`, `q=12`, `q=48`).
- [ ] Tener a mano una pestaña abierta de `https://www.geogebra.org/classic` por si el docente pide pegar en vivo uno de los 5 scripts (recomendado: `ggb_lg01_survival_p3_milestones.txt` o `ggb_rl04_annual_duration_extrapolation.txt`).
- [ ] Sin internet en el aula: tranquilidad total — imágenes (`base64`), simuladores JS y las **14 fórmulas (`data-plain`)** funcionan 100 % offline.
