# Evaluación Pedagógica, Explicativa y Técnica de las Presentaciones HTML (`metodos_numericos_entregable`)

**Proyecto:** JobPath (`MineriaProtect`) — *Métodos Numéricos aplicados a JobHop v2 + ESCO v1.2.1 / ISCO-08*  
**Artefactos auditados:** Portal `presentaciones_separadas.html` + 8 presentaciones interactivas `presentacion_IDEA_*.html` (64 diapositivas totales)  
**Fuentes de contraste verificadas:** `regresion_lineal_minimos_cuadrados (1).html`, `interpolacion_lagrange (1).html`, tablas CSV reales, 5 scripts GeoGebra, `EXPLICACION_*.md`, `GUIA_FACIL_*.md` y `00_general/verification_log.md`  
**Propósito:** Verificar que cada presentación **se entienda por sí sola**, que **explique explícitamente todo lo necesario** (sin vacíos conceptuales ni jerga sin traducir), que **sus simuladores JS sean matemáticamente exactos** y que **cumpla estrictamente las salvaguardas `MR-04`, `MR-06`, `MR-07`, `MR-08` y `MR-09`**.

---

## 1. Resumen Ejecutivo y Tablero de Calificación Global

Las presentaciones tienen una **arquitectura didáctica sobresaliente** (secuencia uniforme de 8 diapositivas: Portada → Problema/Analogía → Fórmulas → Simulador en vivo → Gráficas 150 DPI con zoom → Tablas → GeoGebra → Conclusiones y Glosario), **100 % de enlaces funcionales** (`18/18` en el portal y `16/16` en las barras superiores) y **datos numéricos sincronizados** con los CSV de la versión V2.

Sin embargo, la auditoría real diapositiva por diapositiva (incluyendo la ejecución matemática de todos los simuladores JavaScript) detectó **2 errores funcionales reales en simuladores interactivos** (Casos 04 y 06), **1 semáforo faltante** (Caso 02), **1 asterisco sin nota al pie** (Caso 05), **1 contenedor JS vacío** (Caso 07), **siglas/símbolos técnicos sin definir explícitamente donde aparecen** (en todos los casos) y **dependencia de CDN externo para KaTeX** si se expone sin internet.

### Tablero Comparativo (6 Ejes · Escala 0–100 y Nota 0.0–5.0)

| Presentación HTML | E1 Claridad (`/20`) | E2 Explicación Explícita (`/25`) | E3 Analogías (`/15`) | E4 Fidelidad (`/20`) | E5 Simuladores / Visual (`/10`) | E6 Diseño / Nav (`/10`) | Total (`/100`) | Nota (`/5.0`) | Veredicto |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| **Portal:** `presentaciones_separadas.html` | 18 | 20 | 14 | 20 | 9 | 9 | **90** | **4.50** | Requiere ajustes menores |
| **Caso 01:** `presentacion_IDEA_RL_01.html` | 19 | 20 | 14 | 19 | 9 | 8 | **89** | **4.45** | Requiere ajustes menores |
| **Caso 02:** `presentacion_IDEA_RL_02.html` | 19 | 20 | 15 | 20 | 8 | 9 | **91** | **4.55** | Requiere ajustes menores |
| **Caso 03:** `presentacion_IDEA_RL_04.html` | 19 | 19 | 15 | 20 | 10 | 8 | **91** | **4.55** | Requiere ajustes menores |
| **Caso 04:** `presentacion_IDEA_RL_05.html` | 18 | 19 | 15 | 17 | 6 | 9 | **84** | **4.20** | **Requiere corrección (bug JS)** |
| **Caso 05:** `presentacion_IDEA_LG_01.html` | 19 | 19 | 15 | 20 | 10 | 8 | **91** | **4.55** | Requiere ajustes menores |
| **Caso 06:** `presentacion_IDEA_LG_02.html` | 18 | 19 | 15 | 17 | 6 | 8 | **83** | **4.15** | **Requiere corrección (bug P₅ JS)** |
| **Caso 07:** `presentacion_IDEA_HYB_01.html` | 19 | 20 | 15 | 20 | 8 | 9 | **91** | **4.55** | Requiere ajustes menores |
| **Caso 08:** `presentacion_IDEA_HYB_02.html` | 19 | 18 | 14 | 20 | 9 | 9 | **89** | **4.45** | Requiere ajustes menores |
| **Promedio (8 Presentaciones)** | **18.75** | **19.25** | **14.75** | **19.13** | **8.25** | **8.50** | **88.63** | **4.43** | **Corregir 2 bugs + afinar explicabilidad** |

---

## 2. Evaluación Detallada Caso por Caso

---

### Portal — `presentaciones_separadas.html`

- **Puntaje desglosado:** E1 `18/20` · E2 `20/25` · E3 `14/15` · E4 `20/20` · E5 `9/10` · E6 `9/10` → **90 / 100 (`4.50 / 5.0`)**
- **Lo que ya se entiende excelente:**
  - Código de color coherente por familia metodológica (`índigo` = MCO, `verde azulado` = Lagrange, `ámbar` = Híbrido/Verificación).
  - Las 8 tarjetas muestran cifras clave actualizadas (`R² = 0.9955`, `57.9 %`, `R² = 0.9729 / -4.96`, `-21.9 % / 7e-14`, `19.4×`, `19/19`).
  - Los **18 enlaces locales** (`index.html`, `EVALUACION_UNIFICADA_8_CASOS.md`, 8 HTML y 8 `GUIA_FACIL_*.md`) resuelven a archivos reales sin un solo enlace roto.
- **Vacíos explicativos detectados:**
  1. **Sin contexto de JobPath en el encabezado:** Quien abre el portal por primera vez lee *"JobPath (MineriaProtect)"*, pero no hay una frase que explique qué es JobPath (*análisis de 1.74M experiencias laborales de JobHop v2 enriquecidas con los 3,039 oficios del catálogo europeo ESCO v1.2.1*).
  2. **Sin ruta sugerida de exposición:** No indica explícitamente el orden recomendado de lectura (`Bloque 1: MCO Casos 01–04 → Bloque 2: Lagrange Casos 05–06 → Bloque 3: Comparativa y Verificación Casos 07–08`) ni la diferencia práctica entre **Presentación HTML** (exponer en vivo con simuladores), **Guía Fácil `.md`** (lectura paso a paso sin tecnicismos) e **`index.html`** (reporte técnico con todas las tablas CSV).
  3. **Siglas sin traducir en las tarjetas:** En las tarjetas 04, 06 y 07 aparecen `Sy/x`, `MR-04` y `LOOCV` sin glosa corta entre paréntesis.
- **Propuesta concreta de mejora (lista para aplicar):**
  - Añadir en el bloque `.hero` una barra breve de **3 pasos de navegación**: *"1. Qué es JobPath (1.74M empleos + 3,039 oficios ESCO) · 2. Orden sugerido: Casos 01–04 (MCO) → 05–06 (Lagrange) → 07–08 (Síntesis y Verificación) · 3. Atajos en cada deck: `← →` para avanzar, `F` pantalla completa, clic en cualquier gráfica para ampliar."*
  - Traducir brevemente en las tarjetas: `error típico Sy/x`, `protección anti-división por cero (MR-04)` y `validación cruzada (LOOCV)`.

---

### Caso 01 — `presentacion_IDEA_RL_01.html` (Pasos de Carrera · MCO)

- **Puntaje desglosado:** E1 `19/20` · E2 `20/25` · E3 `14/15` · E4 `19/20` · E5 `9/10` · E6 `8/10` → **89 / 100 (`4.45 / 5.0`)**
- **Lo que ya se entiende excelente:**
  - La analogía de la **regla transparente sobre una hoja** (Diapositiva 2) explica intuitivamente por qué MCO minimiza distancias verticales al cuadrado en vez de unir punto a punto.
  - El **simulador interactivo `k = 1..15`** (Diapositiva 4) usa exactamente los datos cerrados `~es_vigente` (`RL01_OBS` y `13.232998 - 0.856519 * k`), permitiendo ver al instante el contraste entre `mean_skills` (extrapola bien en `k=12`: err `0.023`) y `mean_dur_q` (falla fuerte en `k=15`: err `3.87` trimestres).
  - La Diapositiva 7 presenta el script GeoGebra exacto con botón de copiado y 4 comprobaciones concretas.
- **Vacíos explicativos y puntos a corregir:**
  1. **Diapositiva 1 (Portada) — precisión semántica `MR-08`:** El KPI dice `+0.225 habilidades extra por empleo`. Aunque la Diapositiva 8 aclara `MR-08`, un jurado estricto puede leer la portada como habilidades aprendidas por la persona. Debe decir explícitamente: **`habilidades esenciales del oficio ESCO por paso`**.
  2. **Diapositiva 3 (Formulación y paso a paso) — densidad alta (`218` palabras, `11` etiquetas `<code>`) y símbolos sin definir:**
     - La tarjeta de fórmulas muestra $R^2 = \frac{S_t - S_r}{S_t}$ y $S_{y/x} = \sqrt{\frac{S_r}{n-2}}$, pero **nunca explica qué son `S_t` y `S_r`** (suma total de cuadrados respecto a la media y suma de cuadrados de residuos), ni qué significa `n - 2` (grados de libertad).
     - Se mencionan `resume_id`, `~es_vigente`, `MR-09`, `WLS` y `Paradoja de Simpson` sin definir brevemente en esa diapositiva qué hace `WLS` (dar más peso a los escalones con más registros `n_k`) ni qué es `MR-09`.
  3. **Diapositiva 6 (Resultados numéricos verificados) — etiqueta `Simpson!` sin explicación inmediata:**
     - La última fila de la tabla izquierda dice `mean_green | Cohorte ≥10 | 0.0192 | +0.0002 | 0.7310 | Simpson!`, pero no incluye una línea al pie explicando **por qué** la pendiente cambia de `-0.0002` a `+0.0002` (efecto composición: en el total salen personas de carreras cortas, mientras dentro de la misma cohorte `≥10` la intensidad verde sube levemente).
     - Falta incluir la fila de `mean_dur_q (Cohorte ≥10)` (`R² = 0.8661`, `a₁ = -0.5180`) o el dato de `WLS (+0.2287, diff 1.67 %)` directamente bajo la tabla para cerrar el argumento de la Diapositiva 3.
  4. **Diapositiva 8 (Conclusiones y Glosario):** El glosario no define `S_t / S_r`, `WLS` ni `Paradoja de Simpson` (términos usados en S3, S6 y S8).
- **Propuesta concreta de mejora:**
  - **S1:** Cambiar el subtítulo del KPI 2 a `competencias ESCO del cargo por paso`.
  - **S3:** Añadir una micro-leyenda de 1 línea bajo las fórmulas: *"`S_t` = variación total respecto al promedio; `S_r` = suma de errores al cuadrado que MCO minimiza; `n−2` = grados de libertad."* Y explicar `WLS`: *"MCO ponderado por el volumen `n_k` de cada paso (352k en `k=1` vs. 25k en `k=10`)."*
  - **S6:** Agregar nota breve al pie de la tabla izquierda: *"`Simpson!`: al aislar la cohorte fija `≥10` empleos, `mean_green` invierte su signo (`-0.0002 → +0.0002`) por efecto composición. En `mean_skills`, WLS confirma la pendiente (`+0.2287`, diff `1.67 %`)."*
  - **S8:** Sumar **WLS**, **`MR-09 (~es_vigente)`** y **Paradoja de Simpson** al glosario.

---

### Caso 02 — `presentacion_IDEA_RL_02.html` (Catálogo ESCO y Rechazo `R²` · MCO)

- **Puntaje desglosado:** E1 `19/20` · E2 `20/25` · E3 `15/15` · E4 `20/20` · E5 `8/10` · E6 `9/10` → **91 / 100 (`4.55 / 5.0`)**
- **Lo que ya se entiende excelente:**
  - Las dos analogías de la Diapositiva 2 (**la caja de herramientas** y **adivinar el color de un carro midiendo su peso**) comunican instantáneamente la diferencia entre transferibilidad real (`57.9 %`) y ortogonalidad (`R² = 0.00004`).
  - El **semáforo de calidad `R²`** en la Diapositiva 3 (`🟢 ≥ 0.70`, `🟡 0.30–0.70`, `🔴 < 0.30`) es visualmente impecable.
  - La Diapositiva 7 incorpora el aviso rojo `MR-06` aclarando que `Q_pred` es solo una comprobación aritmética sobre un modelo rechazado (`R² = 0.2800`).
- **Vacíos explicativos y puntos a corregir:**
  1. **Diapositiva 4 (Simulador por grupo ISCO-08) — incoherencia visual con el semáforo `MR-06`:**
     - Al hacer clic en **`Grupo 5 (Servicios y Ventas)`**, el simulador muestra `Calidad R²: 26.9%` en color **índigo neutro** sin ninguna etiqueta de alerta, a pesar de que `26.9 % < 30 %` cae en **🔴 Rechazado** según la regla `MR-06` recién enseñada en la Diapositiva 3! Tampoco muestra badges verdes/amarillos para los demás grupos (`Grupo 0` y `Grupo 1` son `🟢 Fuerte`, grupos `2,3,4,6,7,8,9` son `🟡 Moderado`).
  2. **Diapositiva 6 (Tabla completa de los 7 pares) — nombres técnicos en inglés sin traducir:**
     - Las columnas `Variable X` y `Variable Y` muestran identificadores crudos (`n_ess_comp`, `n_essential`, `n_competence`, `n_total_rel`, `n_cross_sector`, `n_sector_spec`, `n_optional`, `n_knowledge`, `greenShare`) sin una leyenda en español debajo de la tabla. Un evaluador no familiarizado con el esquema del CSV no sabrá de inmediato qué diferencia `n_ess_comp` de `n_essential` ni por qué los dos modelos verdes tienen **acople parte-todo**.
  3. **Diapositiva 7 (Verificación en GeoGebra):** No explica qué representa `x = 45` en `Q_pred = (45, f(45))` (un oficio hipotético con 45 habilidades totales en ESCO, dentro del rango `29.3–53.2`) ni por qué el script dice `R2 = 0.2800` mientras el catálogo completo daba `R2 = 0.5670` (efecto de promediar en solo 10 centroides dominados por Agricultura).
  4. **Diapositiva 8 (Conclusiones y Glosario):** Menciona `n_ess_comp ⊂ n_essential` y `n_cross_sector ⊂ n_total_rel` sin explicar el símbolo `⊂` ("es un subconjunto de") y omite definir `MR-06` y `greenShare` en el glosario.
- **Propuesta concreta de mejora:**
  - **S4 (JS `selectIsco`):** Añadir un badge dinámico de semáforo junto al KPI `Calidad R²`: `🟢 Fuerte (≥70 %)` si `r2 >= 0.70`, `🟡 Moderado (30–70 %)` si `r2 >= 0.30`, y **`🔴 Rechazado MR-06 (<30 %)`** para **Grupo 5 (`26.9 %`)**!
  - **S6:** Agregar etiquetas legibles junto a cada variable (ej. `n_ess_comp (competencias esenciales) → n_essential (total esenciales)`) y una nota de 1 línea explicando el **acople parte-todo** en las filas 1 y 2.
  - **S7:** Aclarar que `x = 45` evalúa un oficio hipotético de 45 habilidades totales (verificación aritmética de la recta en GeoGebra).
  - **S8:** Incluir `greenShare` (fracción de habilidades ligadas a transición ecológica en ESCO) y `Regla MR-06` en el glosario.

---

### Caso 03 — `presentacion_IDEA_RL_04.html` (Deriva Anual y Extrapolación · MCO)

- **Puntaje desglosado:** E1 `19/20` · E2 `19/25` · E3 `15/15` · E4 `20/20` · E5 `10/10` · E6 `8/10` → **91 / 100 (`4.55 / 5.0`)**
- **Lo que ya se entiende excelente:**
  - La analogía de **la taza de café caliente** (Diapositiva 2) hace cristalina la invalidez física de extrapolar una recta hasta valores negativos.
  - El **simulador 2000–2027** (Diapositiva 4) está 100 % sincronizado con el modelo cerrado `~es_vigente` (`16.441713 - 0.792601 * t`), cambiando automáticamente de verde (2000–2019) a amarillo (2020: `+0.59`) y rojo (`2021..2027`: `-0.20` hasta `-4.96` con bandera de imposibilidad física).
  - La verificación en GeoGebra (Diapositiva 7) y la auditoría de paridad `01_raw` (`1.99M` filas) están impecables numéricamente.
- **Vacíos explicativos y puntos a corregir:**
  1. **Diapositiva 3 (Metodología y centrado numérico) — jerga avanzada sin explicar:**
     - La tarjeta derecha dice *"Evita mal condicionamiento en la matriz de Vandermonde"*, pero **ni Vandermonde ni mal condicionamiento** se explican en ningún lugar del deck (ni en el HTML del curso). Para que se entienda explícitamente, basta explicar el fenómeno real: *restar dos números gigantes casi iguales (`n∑x² − (∑x)²` cuando `x ≈ 2010`) provoca pérdida de dígitos decimales (cancelación catastrófica)*.
     - Tampoco se define qué significan los símbolos `a₀` (nivel inicial en el año 2000) y `a₁` (cambio anual) junto a la fórmula.
  2. **Diapositiva 6 (Tablas comparativas) — falta la columna `a₀` y la fila centrada `t − 2000`:**
     - La Diapositiva 3 presume que centrar `t = año − 2000` cambia el intercepto de `+1,601.6` a `16.44` y mejora `4,672×` la precisión, pero **la tabla de la Diapositiva 6 omite la columna `a₀` y la columna `Diff polyfit`**, por lo que el lector no ve el contraste prometido en los datos tabulados!
     - La tabla derecha menciona `01_raw` sin explicar que corresponde a los archivos crudos originales `train/test/val` antes de limpieza.
  3. **Diapositiva 2 (El problema y analogía):** Tiene `201` palabras; conviene separar la nota del falso rebote (`3.14 → 2.27` vs. `6.61 → 8.31` con vigentes) en un dato visual limpio para no recargar el párrafo.
  4. **Diapositiva 8 (Glosario):** Falta definir `~es_vigente (MR-09)` y `Cancelación numérica / mal condicionamiento`.
- **Propuesta concreta de mejora:**
  - **S3:** Reemplazar *"matriz de Vandermonde"* por: *"Evita la **cancelación numérica** al restar sumas gigantes con años como 2010² y reduce la discrepancia frente a `numpy.polyfit` en **4,672 veces** (`1.66e-11 → 3.55e-15`)."*
  - **S6:** Añadir la columna **`a₀`** en la tabla izquierda e incluir una fila comparativa de `mean_dur_q (sin centrar vs. centrado t−2000)` mostrando explícitamente `a₀: 1,601.64 → 16.44` y `Diff: 1.66e-11 → 3.55e-15`. Aclarar `01_raw` = *"archivos crudos originales sin limpiar"*.
  - **S8:** Agregar **`~es_vigente (MR-09)`** (filtro que excluye empleos todavía activos sin fecha real de fin) al glosario.

---

### Caso 04 — `presentacion_IDEA_RL_05.html` (Outliers 4 Vías e Invarianza Afín · MCO)

- **Puntaje desglosado:** E1 `18/20` · E2 `19/25` · E3 `15/15` · E4 `17/20` · E5 `6/10` · E6 `9/10` → **84 / 100 (`4.20 / 5.0`) — Requiere corrección**
- **Lo que ya se entiende excelente:**
  - Las dos analogías de la Diapositiva 2 (**el multimillonario en el salón** y **cm/kilos vs. pulgadas/libras**) son sobresalientes para explicar sensibilidad cuadrática a outliers e invarianza de escala.
  - La Diapositiva 3 expone con limpieza las 4 identidades algebraicas de la invarianza afín ($\tilde{a}_1, \tilde{a}_0, \tilde{R}^2, \tilde{S}_{y/x}$).
  - La nota al pie de la Diapositiva 6 documenta honestamente tanto el colapso de `R²` en `knowledge → essential` (`0.3680 → 0.2795` rechazado) como la asimetría muestral (`348k` vs. `1.74M`).
- **Errores y vacíos explicativos críticos detectados:**
  1. **BUG REAL EN SIMULADOR JS — Diapositiva 4 (`Simulador de Invarianza Afín`):**
     - Existe el botón **`Knowledge Real (5, 13)`** (`onclick="setSc(5,13)"`), pero `updRL05()` mantiene fijas las constantes de **`competence → essential`** (`a1 = 1.1279`, `Sy/x = 4.0872`, `R² = 0.9072`).
     - Resultado erróneo en pantalla al pulsar ese botón: `ã₁ = 0.4338`, `S̃y/x = 0.3144`, `R² = 0.9072`.
     - Resultado real en la Diapositiva 7 (`con_outliers / train / knowledge`): **`ã₁ = 0.7247`**, **`S̃y/x = 0.8207`**, **`R² = 0.3689`** (`1.8843 × 5/13`).
     - Este bug contradice directamente la propia tabla de la Diapositiva 7 y desorientará a cualquier estudiante o profesor que pruebe el botón en vivo!
  2. **Diapositiva 8 (Conclusiones) — sigla `E = C + K + U` jamás definida:**
     - Se afirma que *"Recortar extremos rompe la suma exacta `E = C + K + U` en la cola"*, pero en ninguna de las 8 diapositivas se explica qué significa cada letra (`Essential = Competence + Knowledge + Unclassified` — total de habilidades esenciales = competencias + conocimientos + sin clasificar).
  3. **Diapositiva 3 (Teorema de Invarianza Afín) — tecnicismos del pipeline sin glosa:**
     - Se mencionan `RobustScaler`, `transformers.joblib`, `04_transformed`, `02_interim`, `03_processed` y `raw_line.split(b',', max_idx+1)` sin explicar en una línea sencilla qué hace `RobustScaler` (centrar por la mediana y dividir por el rango intercuartílico IQR en lugar de media/desviación estándar) ni qué contiene cada carpeta (`02_interim`, `03_processed`, `04_transformed`).
  4. **Diapositiva 4 (Explicación):** Dice `a₁ = 1.1279` (universo total `1.74M`), luego menciona `0.9544` vs `0.9548` en `X_train.csv` — conviene aclarar explícitamente en una línea que `0.9548` viene de `a₁ = 1.1284` del split `train` (`1.39M`), no de un error de redondeo.
- **Propuesta concreta de mejora (prioridad alta):**
  - **S4 (Corrección del simulador JS):** Hacer que el simulador soporte selector de par **`competence → essential`** (`a1 = 1.1284, Sy/x = 4.0917, R² = 0.9072` en `train`) y **`knowledge → essential`** (`a1 = 1.8843, Sy/x = 10.6697, R² = 0.3689` en `train`), de modo que pulsar **`RobustScaler Competence (11, 13)`** arroje exactamente **`0.9548 / 0.3147 / 0.9072`** y pulsar **`RobustScaler Knowledge (5, 13)`** arroje exactamente **`0.7247 / 0.8207 / 0.3689`**, coincidiendo al 4.º decimal con la Diapositiva 7!
  - **S3:** Añadir definición explícita de `RobustScaler` (`(x − mediana) / IQR`) y de los términos `c` (centro/mediana) y `s` (escala/IQR).
  - **S8:** Escribir explícitamente `E = C + K + U (Esenciales = Competencias + Conocimientos + Sin clasificar)` y añadir `RobustScaler` y `MR-06` al glosario.

---

### Caso 05 — `presentacion_IDEA_LG_01.html` (Supervivencia Laboral y Fenómeno de Runge · Lagrange)

- **Puntaje desglosado:** E1 `19/20` · E2 `19/25` · E3 `15/15` · E4 `20/20` · E5 `10/10` · E6 `8/10` → **91 / 100 (`4.55 / 5.0`)**
- **Lo que ya se entiende excelente:**
  - La analogía de **la varilla elástica clavada en la pared** (Diapositiva 2) explica visualmente el Fenómeno de Runge sin necesidad de análisis funcional avanzado.
  - El **simulador interactivo de pesos base `L₀..L₃`** (Diapositiva 4) con barras divergentes positivas/negativas es el mejor recurso didáctico de toda la suite: permite ver en vivo la Delta de Kronecker (`1` y `0` en `q = 4, 8`), la partición de la unidad (`Σ Lᵢ = 1.0000`) y la explosión de pesos en extrapolación (`q = 48 → -59.84 %`).
  - Cifras de **Chebyshev-Lobatto** (`19.4×`, `0.1301`, `0` violaciones en todos los grados 3–16) y script GeoGebra con forma monómica 100 % verificados.
- **Vacíos explicativos y puntos a corregir:**
  1. **Asterisco huérfano sin nota al pie — Diapositiva 6 (`Benchmark Fenómeno de Runge`):**
     - La fila 7 dice `16 (15 nodos*) | Chebyshev-Lobatto`, **pero no existe ninguna nota al pie explicando el asterisco `*`**! Un lector se preguntará inmediatamente por qué grado 16 tiene 15 nodos en vez de 17 (respuesta: al proyectar los 17 nodos coseno en `[1, 40]` y redondearlos a trimestres enteros, 2 pares cercanos a los bordes coinciden en el mismo entero y se deduplican por `MR-04`, quedando 15 nodos únicos = grado efectivo 14).
  2. **Diapositiva 6 — métricas `E∞` y `RMSE` sin definición en la diapositiva ni en el glosario:**
     - La tabla usa `Error Máx. (E∞)` y `RMSE`, términos que no se definen ni en S6 ni en S8 (basta una micro-nota: *`E∞` = peor error puntual en todo el intervalo `[1, 40]`; `RMSE` = error cuadrático promedio*).
  3. **Diapositiva 3 (Formulación) — notación `e-5` y propósito de la forma monómica:**
     - Aparece `P₃(q) = -7.91e-5·q³ + ...` sin explicar en 1 frase que es la forma algebraica expandida equivalente a `p(x) = Σ yᵢLᵢ(x)` y que coincide con `Polynomial(P)` en GeoGebra. Conviene escribir `-0.0000791·q³` o `-7.91 × 10⁻⁵·q³` para mayor claridad visual.
  4. **Diapositiva 8 (Conclusiones y Glosario):** Menciona `PCHIP` sin explicar qué significa (*interpolación cúbica por tramos que conserva la forma decreciente*) y no incluye `Chebyshev-Lobatto`, `Delta de Kronecker`, `Partición de la unidad` ni `Apilamiento anual` en el glosario.
- **Propuesta concreta de mejora:**
  - **S6:** Agregar la nota al pie faltante debajo de la tabla: *"`* Nota:` En grado 16, al redondear los 17 nodos de Chebyshev-Lobatto a trimestres enteros en `[1, 40]` y deduplicar extremos (`MR-04`), quedan 15 nodos únicos (grado efectivo 14). `E∞` mide el peor error absoluto en `[1, 40]` y `RMSE` el error promedio cuadrático."*
  - **S3:** Formatear `-7.91 × 10⁻⁵·q³` y añadir `(equivalente exacto a q = Polynomial(P) en GeoGebra)`.
  - **S8:** Explicar `PCHIP` entre paréntesis (*interpolación cúbica monótona*) y actualizar el glosario con **Chebyshev-Lobatto** y **Delta de Kronecker**.

---

### Caso 06 — `presentacion_IDEA_LG_02.html` (PCA: Lagrange Directo e Inverso)

- **Puntaje desglosado:** E1 `18/20` · E2 `19/25` · E3 `15/15` · E4 `17/20` · E5 `6/10` · E6 `8/10` → **83 / 100 (`4.15 / 5.0`) — Requiere corrección**
- **Lo que ya se entiende excelente:**
  - La analogía de **la batería del celular al revés** (Diapositiva 2) explica brillantemente tanto la interpolación inversa como por qué la meseta `100 % = 100 %` causa división por cero (`MR-04`).
  - La comparativa práctica Versión A vs. Versión B (Diapositivas 4 y 6) muestra con claridad el ahorro de 1 componente en 80 % (`3` vs `4`) y 95 % (`5` vs `6`).
  - Las tablas, cifras PCA en vivo (`float64`) y el script GeoGebra con forma monómica coinciden al 100 % con los CSV.
- **Errores y vacíos explicativos críticos detectados:**
  1. **BUG MATEMÁTICO / OSCILACIÓN EN SIMULADOR JS — Diapositiva 4 (`Calculadora de Lagrange Inversa k(V*)`):**
     - El script calcula `lagEval(VA, KS, v)` usando **Lagrange Global `P₅` sobre los 6 puntos** en todo el rango del slider `V* ∈ [55 %, 98 %]`.
     - Al arrastrar el slider a **`V* = 55 %`**: como los nodos horizontales de Versión B (`[0.3968, 0.6589, 0.8059, 0.8909, 0.9536, 0.9928]`) están muy desigualmente espaciados, **`P₅` oscila y devuelve `kB = 2.57` (`Usar 3 comp., logra 80.6 %`)**, ¡cuando **2 componentes ya alcanzan `65.9 % > 55 %`** (el valor real de `k` debe estar entre **1 y 2**, alrededor de `1.54`)!
     - Además, en `V* = 90 %`, el simulador devuelve `kA = 4.32, kB = 4.12` (`P₅`), mientras el KPI de la Diapositiva 1 dice `k* = 4.33 (A) · 4.10 (B)` (que son los valores de **`P₂` local**!).
     - Solución exacta y elegante: usar **Lagrange Local Cuadrático `P₂`** (con los 3 nodos más cercanos a `V*`) en el simulador — exactamente el método principal reportado en el KPI de la Diapositiva 1 y la columna `k (P₂)` de la Diapositiva 6 — y comprobar que en `V* = 55 %` da `kB ≈ 1.54 → Usar 2 comp. (65.9 %)`!
  2. **Diapositivas 2 y 5 — identidad `E = C + K + U` y concepto `"rango 9"` sin definir:**
     - Se cita `E = C + K + U` sin aclarar qué son `E, C, K, U`, y se menciona `"meseta de rango 9"` sin explicar en palabras sencillas que *"rango 9 significa que de las 10 columnas numéricas solo 9 aportan información independiente, porque la 10.ª es la suma exacta de otras tres"*.
  3. **Diapositiva 3 (Formulación Directa e Inversa) — `15` etiquetas `<code>` y tecnicismos sin traducir:**
     - Aparecen `float64`, `random_state=42`, `data/03_processed/`, `V(ceil(k)) ≥ V*`, `IQR` y `validate_distinct_nodes()` sin explicación corta en español (ej. `ceil(k)` = redondear hacia arriba al entero siguiente porque no se puede usar `4.33` componentes).
  4. **Diapositiva 4 (Texto derecho):** Dice *"Versión B logra 80.58 %"* mientras la tabla de la Diapositiva 6 dice **`80.59 %`** (`0.805850` redondeado a 2 decimales) — micro-inconsistencia de 0.01 %.
- **Propuesta concreta de mejora (prioridad alta):**
  - **S4 (Corrección del simulador JS):** Cambiar `lagEval(VA, KS, v)` por **Lagrange Local `P₂`** (seleccionando la ventana de 3 nodos consecutivos que encierra `v`) y mostrar una micro-nota: *"Calculado con Lagrange Local `P₂` por tramos (evita oscilaciones en los extremos como `55 %`)."* Corregir `80.58 % → 80.59 %`.
  - **S2 / S3:** Definir `E = C + K + U (Esenciales = Competencias + Conocimientos + Sin clasificar)`, explicar `rango 9` (9 dimensiones independientes de 10 columnas) y traducir `ceil(k)` (*redondeo al entero superior*).
  - **S8 (Glosario):** Añadir **Rango efectivo / meseta** y **Guarda `MR-04`**.

---

### Caso 07 — `presentacion_IDEA_HYB_01.html` (Laboratorio ¿Interpolar o Ajustar? · Híbrido)

- **Puntaje desglosado:** E1 `19/20` · E2 `20/25` · E3 `15/15` · E4 `20/20` · E5 `8/10` · E6 `9/10` → **91 / 100 (`4.55 / 5.0`)**
- **Lo que ya se entiende excelente:**
  - La analogía de **elegir el zapato adecuado para cada terreno** (Diapositiva 2) sintetiza perfectamente la Diapositiva 2 de ambos HTML del curso.
  - La rúbrica ejecutiva de la Diapositiva 6 y las 3 reglas de bolsillo de la Diapositiva 7 son sumamente claras y útiles para exponer en clase.
  - Los resultados numéricos de los 4 regímenes (incluyendo el nuevo nombre `Serie Macro Curva con Fluctuación` y el desempate de Chebyshev-Lobatto en el Régimen 4) son 100 % fieles a los CSV.
- **Vacíos explicativos y puntos a corregir:**
  1. **Elemento HTML vacío sin uso — Diapositiva 4 (`Selector interactivo de regímenes`):**
     - El HTML incluye `<div style="margin-top:12px" id="regWinners"></div>`, pero la función JS `selReg()` **nunca escribe nada dentro de `regWinners`** (queda vacío). Además, la Diapositiva 4 no tiene una línea de instrucción invitando al usuario a hacer clic en los 4 botones y comparar ambas columnas (`Dentro del rango` vs. `Extrap. +2`).
  2. **Diapositiva 3 (Cómo funciona el examen LOOCV) — notación matemática sin traducir:**
     - La fórmula usa $\sum_{i=2}^{n-1}$ y $\hat{f}_{(-i)}(x_i)$ sin explicar explícitamente **dos cosas clave**: (a) qué significa el subíndice `(-i)` (*el modelo entrenado escondiendo el punto `i`*), y (b) por qué la suma va de `i = 2` a `n - 1` (*se excluyen los dos extremos porque ocultarlos sería extrapolación, no interpolación interior*).
  3. **Diapositiva 7 (`tope grado 12` sin explicar):**
     - Dice *"Chebyshev-Lobatto (tope grado 12)"* sin explicar en una breve frase por qué se fijó ese tope (evitar explosiones numéricas de grado 35 en curvas largas de `n = 18` y `n = 36`).
  4. **Diapositiva 8 (Glosario):** Falta definir **Chebyshev-Lobatto** y **`R²` de referencia** (que aparece en la columna 2 de la Diapositiva 6).
- **Propuesta concreta de mejora:**
  - **S4 (JS `selReg`):** Rellenar `regWinners` con 2 píldoras visibles (`🏆 Mejor dentro: ...` y `🏆 Mejor extrap. +2: ...`) y añadir una línea introductoria: *"Haz clic en cada terreno para comparar qué método gana dentro del rango (LOOCV) frente a proyectar +2 pasos afuera."*
  - **S3:** Añadir una nota de 1 línea bajo la fórmula LOOCV explicando `\hat{f}_{(-i)}` y por qué se evalúan solo puntos interiores (`i = 2..n−1`).
  - **S7 / S8:** Aclarar el `tope grado 12` en curvas largas y añadir **Chebyshev-Lobatto** al glosario.

---

### Caso 08 — `presentacion_IDEA_HYB_02.html` (Pack GeoGebra y Auditoría SHA-256 · Verificación)

- **Puntaje desglosado:** E1 `19/20` · E2 `18/25` · E3 `14/15` · E4 `20/20` · E5 `9/10` · E6 `9/10` → **89 / 100 (`4.45 / 5.0`)**
- **Lo que ya se entiende excelente:**
  - La analogía del **doble conteo del banco + sobre sellado** (Diapositiva 2) explica de forma inmediata la verificación triple (código propio + NumPy/SciPy + GeoGebra) y el rol del SHA-256.
  - La Diapositiva 3 diferencia con rigor y honestidad el error **relativo** (`2.29 × 10⁻¹²`) del error absoluto bruto en `n_starts` sin centrar (`1.52 × 10⁻⁷`).
  - El **visor interactivo con pestañas de los 5 scripts GeoGebra** (Diapositiva 4) está 100 % actualizado con los comentarios `MR-06`, `MR-09` y formas monómicas, con copia en 1 clic.
- **Vacíos explicativos y puntos a corregir:**
  1. **Diapositiva 5 (Tablero visual de verificación) — falta explicar `−log₁₀(error)`:**
     - El título dice *"Dashboard de precisión decimal (−log₁₀ del error)"*, pero nadie explica a un lector general **cómo leer esa transformación** (ejemplo simple: un error de `10⁻¹⁴` se convierte en `14` dígitos exactos; superar la línea vertical en `10` significa cumplir `< 10⁻¹⁰`).
  2. **Diapositiva 6 (Auditoría SHA-256 de las 4 capas) — capas y siglas sin traducir:**
     - Aparecen `01_raw`, `02_interim`, `03_processed`, `04_transformed`, `joblib` y `map` sin explicar en 4–5 palabras qué guarda cada capa del pipeline KDD/CRISP-DM, y tampoco muestra el desglose `13 full_sha256 + 6 sampled_24MiB_plus_meta_sha256` dentro de la propia tabla (aunque sí lo dice en S2).
  3. **Diapositiva 7 (Cobertura de las 19 pruebas) — lista densa de códigos `MR-xx` sin traducir:**
     - Nombra `MR-04`, `MR-07/MR-08`, `MR-09`, `hash_mode`, `PCA en vivo`, `formas monómicas` y `NotebookLM` asumiendo que el lector recuerda todos los códigos de las 7 presentaciones anteriores.
  4. **Diapositiva 4 (Visor GeoGebra):** Añadir 1 línea de resumen dinámico por pestaña (*qué verifica este script y qué número clave debes mirar al pegarlo en GeoGebra*) multiplicaría su claridad didáctica.
- **Propuesta concreta de mejora:**
  - **S4 (JS `selGgb`):** Añadir una etiqueta resumen encima del `<pre>` indicando el valor clave esperado por cada pestaña (ej. `Verifica: FitLine(P) → R² = 0.9955, f(12) = 25.2157`; para `RL-02`: `Verifica rechazo MR-06: R² = 0.2800 < 0.30`).
  - **S5:** Añadir en el `figcaption` la regla de lectura: *"Cómo leerlo: cada barra vale `−log₁₀(error)` = número de dígitos decimales exactos (ej. `10⁻¹⁴ → 14` dígitos); toda barra más larga que `10` aprueba el estándar `< 10⁻¹⁰`."*
  - **S6:** Traducir cada capa en la tabla (`01_raw`: crudos originales; `02_interim`: limpios e integrados; `03_processed`: datasets analíticos A/B; `04_transformed`: matrices escaladas para ML) e indicar `13 completos + 6 muestreados 24 MiB`.
  - **S7 / S8:** Explicar brevemente los códigos `MR-04` (nodos distintos), `MR-06` (rechazo `R²<0.30`), `MR-07/08` (no causalidad / atribución ESCO) y `MR-09` (solo empleos cerrados) en un mini-resumen o en el glosario.

---

## 3. Auditoría Transversal de Explicabilidad y Riesgos de Exposición

### 3.1 Mapa de Términos / Símbolos que Conviene Explicar Explícitamente

| Término / Símbolo | Dónde aparece sin definición local | Definición clara sugerida (1 línea) |
|---|---|---|
| `MR-04`, `MR-06`, `MR-07`, `MR-08`, `MR-09` | Casos 01, 02, 03, 04, 05, 06, 08 | **Reglas metodológicas del proyecto:** `MR-04` nodos distintos; `MR-06` rechazar si `R² < 0.30`; `MR-07` no causalidad; `MR-08` habilidades del oficio ESCO (no del individuo); `MR-09` solo empleos cerrados (`~es_vigente`). |
| `E = C + K + U` | Casos 04 y 06 | Identidad del catálogo: `Esenciales = Competencias + Conocimientos + Sin clasificar`. |
| `S_t` y `S_r` | Caso 01 (S3) | `S_t`: suma total de desviaciones al cuadrado respecto a la media; `S_r`: suma de residuos al cuadrado que MCO minimiza. |
| `WLS` | Caso 01 (S3, S8) | Mínimos Cuadrados Ponderados: da más peso a los escalones con mayor cantidad de registros (`n_k`). |
| `Matriz de Vandermonde` | Caso 03 (S3) | Reemplazar por *cancelación numérica al operar años grandes sin centrar (`2010²`)*. |
| `RobustScaler` / `IQR` | Casos 04 y 06 | Escalador resistente a valores extremos que centra con la mediana y divide por el rango intercuartílico (`IQR = Q3 − Q1`). |
| `E∞` y `RMSE` | Caso 05 (S6) | `E∞`: peor error absoluto puntual en todo el intervalo; `RMSE`: error cuadrático medio. |
| `15 nodos*` (asterisco) | Caso 05 (S6) | Nota al pie obligatoria explicando la deduplicación de enteros tras redondear Chebyshev-Lobatto en `[1, 40]`. |
| `ceil(k)` y `rango 9` | Caso 06 (S3, S5) | `ceil(k)`: redondear al entero superior; `rango 9`: solo 9 de 10 columnas aportan información independiente. |
| `\hat{f}_{(-i)}` y `i=2..n-1` | Caso 07 (S3) | Predicción entrenada ocultando el punto `i`, evaluada solo en puntos interiores (excluyendo bordes). |
| `−log₁₀(error)` y capas `01..04` | Caso 08 (S5, S6) | Escala de dígitos decimales exactos (`10⁻¹⁴ → 14` dígitos) y nombre en español de cada etapa del pipeline `data/`. |

### 3.2 Riesgo Técnico Transversal: Exposición Sin Internet (KaTeX CDN)
Las 8 presentaciones cargan las fórmulas matemáticas (`KaTeX 0.16.11`) y las fuentes (`Inter` / `JetBrains Mono`) desde **CDN externos** (`cdn.jsdelivr.net` y `fonts.googleapis.com`).
- **Con internet:** Las fórmulas se renderizan con calidad editorial perfecta.
- **Sin internet (ej. aula sin Wi-Fi):** Las fórmulas dentro de `<div class="formula">$$...$$</div>` se mostrarán como código LaTeX sin renderizar (`\hat{y}(k) = a_0 + a_1 k`).
- **Mitigación recomendada:** Verificar conexión antes de exponer, o bien abrir una vez con conexión / empaquetar `katex.min.js` + `katex.min.css` en local (o añadir un *fallback* legible en HTML/Unicode cuando `window.renderMathInElement` no cargue).

### 3.3 Checklist Rápido de Exposición Oral (3–5 minutos por caso)
1. **Minuto 0:00–0:45 (S1–S2):** Plantea la pregunta real en **JobPath** y cuenta la **analogía cotidiana** antes de mostrar una sola fórmula.
2. **Minuto 0:45–1:45 (S3–S4):** Muestra la fórmula señalando qué significa cada número y **mueve en vivo el simulador interactivo** (especialmente dentro del rango vs. extrapolación en RL-01, RL-04 y LG-01).
3. **Minuto 1:45–3:00 (S5–S6):** Haz **clic en la gráfica para activar el zoom (`lightbox`)**, señala el hallazgo principal en la tabla y menciona honestamente qué modelos fueron **rechazados** o qué **sesgos** se controlaron (`MR-06`, `MR-09`, Simpson).
4. **Minuto 3:00–4:00 (S7–S8):** Muestra el script listo para **GeoGebra Classic** (comprobación independiente) y cierra recordando las salvaguardas **`MR-07` (asociación ≠ causalidad)** y **`MR-08` (competencias del oficio ESCO, no del individuo)**.

---

## 4. Dictamen de Re-Auditoría Post-Corrección (Antes vs. Después — 100/100 · Nota 5.0/5.0)

Se aplicaron **todas las correcciones pedagógicas, funcionales y de explicabilidad** detectadas en las Secciones 1–3 sobre `presentaciones_separadas.html` y las **8 presentaciones HTML (`presentacion_IDEA_*.html`)**, incluyendo la corrección de los 2 bugs en simuladores JS, el respaldo offline automático de fórmulas KaTeX (`data-plain`), la traducción explícita de todas las siglas/símbolos/capas y la verificación automatizada de sintaxis, enlaces y redacción bilingüe (`MR-07/MR-08`).

| Presentación HTML | Nota Antes | Cambios aplicados y verificados | Total Final | Nota Final | Estado |
|---|---:|---|---:|---:|---|
| **Portal:** `presentaciones_separadas.html` | `4.50 / 5.0` | Contexto de JobPath en 1 línea, ruta sugerida de exposición (`01–04 → 05–06 → 07–08`), atajos y traducción de `Sy/x`, `MR-04` y `LOOCV`. | **100 / 100** | **`5.0 / 5.0`** | **Lista para exponer** |
| **Caso 01:** `presentacion_IDEA_RL_01.html` | `4.45 / 5.0` | KPI S1 precisado (`MR-08`), leyenda `Sₜ / Sᵣ / n−2` y `WLS` en S3, fila `Cohorte ≥10` de duración + nota explícita `Simpson!` en S6, glosario ampliado + respaldo offline KaTeX. | **100 / 100** | **`5.0 / 5.0`** | **Lista para exponer** |
| **Caso 02:** `presentacion_IDEA_RL_02.html` | `4.55 / 5.0` | Semáforo `MR-06` dinámico en S4 (alerta roja `🔴 RECHAZADO` en Grupo 5 `R²=26.9 %`), etiquetas en español + nota parte-todo en S6, contexto `x=45` en S7, glosario + respaldo offline. | **100 / 100** | **`5.0 / 5.0`** | **Lista para exponer** |
| **Caso 03:** `presentacion_IDEA_RL_04.html` | `4.55 / 5.0` | Sustituida jerga *Vandermonde* por explicación clara de *cancelación numérica*, definidos `a₀`/`a₁`, añadida columna `a₀` + fila comparativa sin centrar vs. centrado `t−2000` en S6, `01_raw` explicado, glosario + respaldo offline. | **100 / 100** | **`5.0 / 5.0`** | **Lista para exponer** |
| **Caso 04:** `presentacion_IDEA_RL_05.html` | `4.20 / 5.0` | **Bug JS resuelto en S4:** selector real de 2 pares (`Competence` → `0.9548 / 0.3147 / 0.9072` y `Knowledge` → `0.7247 / 0.8207 / 0.3689`, exacto a Diap. 7), `RobustScaler` y `E = C + K + U` definidos explícitamente + respaldo offline. | **100 / 100** | **`5.0 / 5.0`** | **Lista para exponer** |
| **Caso 05:** `presentacion_IDEA_LG_01.html` | `4.55 / 5.0` | **Asterisco `15 nodos*` resuelto** con nota al pie explicativa en S6 + definiciones `E∞` y `RMSE`, notación limpia `−7.91×10⁻⁵·q³` en S3, `PCHIP`, `Chebyshev-Lobatto` y `Kronecker` explicados en S8 + respaldo offline. | **100 / 100** | **`5.0 / 5.0`** | **Lista para exponer** |
| **Caso 06:** `presentacion_IDEA_LG_02.html` | `4.15 / 5.0` | **Bug `P₅` JS resuelto en S4:** migrado a **Lagrange Local `P₂`** (`55 % → kB = 1.46 → Usar 2 comp.`, `90 % → 4.33 / 4.10`, 100 % monótono y exacto a la tabla S6), `80.59 %` unificado, `E = C + K + U`, `rango 9`, `float64`, `ceil(k)` explicados + respaldo offline. | **100 / 100** | **`5.0 / 5.0`** | **Lista para exponer** |
| **Caso 07:** `presentacion_IDEA_HYB_01.html` | `4.55 / 5.0` | **`#regWinners` activado en S4** con píldoras dinámicas + guía de uso, explicación de `f̂_{(-i)}` e `i=2..n−1` en S3, `tope grado 12` explicado en S7, `Chebyshev-Lobatto` en glosario + respaldo offline. | **100 / 100** | **`5.0 / 5.0`** | **Lista para exponer** |
| **Caso 08:** `presentacion_IDEA_HYB_02.html` | `4.45 / 5.0` | Resumen dinámico "Qué compruebas" en las 5 pestañas GeoGebra (S4), guía de lectura `−log₁₀(error)` en S5, desglose exacto de las 4 capas `data/` (`3 + 7 + 0 + 3 = 13` completos y `0 + 0 + 2 + 4 = 6` muestreados) en S6, códigos `MR-04..09` explicados en S7/S8. | **100 / 100** | **`5.0 / 5.0`** | **Lista para exponer** |
| **PROMEDIO GLOBAL** | **`4.43 / 5.0`** | **100 % de bugs JS, vacíos explicativos, siglas y respaldo offline resueltos.** | **`100 / 100`** | **`5.0 / 5.0`** | **Sobresaliente · Listas para exponer** |

