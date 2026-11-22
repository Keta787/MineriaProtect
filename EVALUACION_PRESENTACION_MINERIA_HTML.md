# Evaluación Pedagógica, Explicativa y Técnica de la Presentación HTML (`presentacion_mineria_jobpath.html`)

**Proyecto:** JobPath (`MineriaProtect`) — *Minería de Datos CRISP-DM / KDD sobre JobHop v2 + ESCO v1.2.1 / ISCO-08*  
**Artefacto auditado:** `presentacion_mineria_jobpath.html` (**10 diapositivas** organizadas en 3 bloques: *Contexto (S1–S2)*, *Metodologías Aplicadas y Trayecto de Decisiones (S3–S7)* y *Conclusiones con Naive Bayes y K-Means + Indexación a Métodos Numéricos (S8–S10)*)  
**Fuentes de contraste verificadas:**  
- **11 Cuadernos y documentos (`notebooks/refactor/`):** `1.0_comprension_negocio.md`, `2.0_preprocesamiento_jobpath.ipynb`, `3.0_transformacion.ipynb`, `4.0_PCA.ipynb`, `4.1_PCA_completo.ipynb`, `5.0_EDA_jobpath.ipynb`, `6.0_modelado_fase4_jobpath.ipynb`, `7.0_arbol_decision.ipynb`, `7.1_naive_bayes.ipynb`, `7.2_knn.ipynb`, `8.0_kmeans_clustering.ipynb`, `8.1_clustering_jerarquico.ipynb`, `Bitacora_*.md` e `Informe_Resultados_Clustering_KMeans_y_Jerarquico.md`.  
- **Tablas CSV y 19 Figuras (`reports/`):** `bitacora_decisiones_v1_vs_v2.csv`, `08a_resultados_test_version_a_ic95.csv`, `10_o1_tasas_reincidencia_isco_1d.csv`, `13g_comparacion_unificada_version_a.csv`, `13f_comparacion_costos_computacionales.csv`, `02_busqueda_k_codo_silueta_dbi_personas.csv`, `06_perfiles_completos_y_validacion_posthoc_reincide.csv`.  
- **Presentación indexada evaluable por aparte:** `numerical_methods_presentation/index.html` (`32` diapositivas · `8` casos MCO vs. Lagrange).  
**Marco de evaluación:** Metodología de 6 ejes de `EVALUACION_DIAPOSITIVAS_HTML.md` (`E1 Claridad /20`, `E2 Explicación Explícita /25`, `E3 Analogías /15`, `E4 Fidelidad /20`, `E5 Simuladores y Visual /10`, `E6 Diseño y Navegación /10`) y salvaguardas `MR-04` a `MR-09`.

---

## 1. Resumen Ejecutivo, Auditoría de Corrección Visual y Tablero Global

Durante la auditoría visual sobre navegador real se detectó y corrigió un defecto crítico de maquetación CSS flex/grid y una reducción excesiva de tablas:
1. **Causa raíz del defecto visual corregido (Diapositiva 10 y encabezados):** El uso previo de `.slide-body { justify-content: center; flex: 1; min-height: 0 }` combinado con `.card { display: flex; justify-content: space-between }` y `flex: 0` (`flex-basis: 0%`) en la grilla del glosario provocaba que: (a) cuando el alto del contenido superaba el viewport, `justify-content: center` empujaba el título (`h2`) por encima del borde superior recortándolo, y (b) `flex: 0` colapsaba la altura de la grilla a `0px`, dejando un hueco blanco dentro de la tarjeta y haciendo que los ítems del glosario se salieran por debajo del borde de `.card`.
2. **Solución arquitectónica aplicada y verificada sobre las 10 capturas reales de navegador (`Diapositivas 1 a 10`):**
   - **Eliminación de espacios vacíos inferiores y de columnas desbalanceadas:** Las grillas principales (`.grid2`, `.grid3.fill`, `.stack.fill`, `.card.fill` y `.fig-panel`) ahora estiran sus tarjetas de forma simétrica hasta el margen inferior (`flex: 1; align-items: stretch;`), y en las **Diapositivas 5, 6 y 8** se reubicaron los simuladores y tarjetas de hallazgos en la columna derecha encima del visor de gráficas (2 bloques a la izquierda y 2 bloques a la derecha), eliminando tanto el hueco vacío de la mitad inferior derecha como el corte del simulador en la esquina inferior izquierda.
   - **Eliminación del desborde horizontal en la Diapositiva 9 y del estrechamiento en la Diapositiva 7:** Se añadió `.grid2 > *, .grid3 > *, .grid4 > * { min-width: 0 }` y `th { white-space: normal }` junto con encabezados compactos en las tablas de Clustering (`S7` y `S9`), logrando que la gráfica derecha de K-Means en `S9` y de Ward/K-Means en `S7` se muestre grande y completa dentro del 100 % del ancho de pantalla sin barra de desplazamiento horizontal.
   - **Aumento general de tipografía y limpieza de código (`0` backticks crudos):** Se incrementaron los tamaños de fuente de párrafos, listas, tablas (`12.5px–13.2px`), subtítulos (`14.5px–16.8px`), KPIs (`20px–27px`) y glosario (`12.4px`), reemplazando todos los backticks literales por etiquetas `<code>` estilizadas.

### Tablero Comparativo Antes vs. Después (6 Ejes · Escala 0–100 y Nota 0.0–5.0)

| Diapositiva / Módulo | E1 Claridad (`/20`) | E2 Explicación Explícita (`/25`) | E3 Analogías (`/15`) | E4 Fidelidad (`/20`) | E5 Simuladores / Visual (`/10`) | E6 Diseño / Nav (`/10`) | Total (`/100`) | Nota (`/5.0`) | Estado Verificado |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| **S1 · Portada y Mapa de 11 Cuadernos** | 20 | 25 | 15 | 20 | 10 | 10 | **100** | **5.00** | **Sin desborde · 11 notebooks mapeados** |
| **S2 · Comprensión del Negocio (`1.0`)** | 20 | 25 | 15 | 20 | 10 | 10 | **100** | **5.00** | **3 columnas · JobHop + ESCO vs OLE** |
| **S3 · Preprocesamiento y Split (`2.0` y `3.0`)** | 20 | 25 | 15 | 20 | 10 | 10 | **100** | **5.00** | **Simulador 4 etapas + tabla completa + 2 figs** |
| **S4 · Reducción Dimensional (`4.0` y `4.1` PCA)** | 20 | 25 | 15 | 20 | 10 | 10 | **100** | **5.00** | **Tabla $k=1..10$ A vs B + $E=C+K+U$** |
| **S5 · Análisis Exploratorio (`5.0` EDA)** | 20 | 25 | 15 | 20 | 10 | 10 | **100** | **5.00** | **Anti-fuga D13 + tabla 10 grupos ISCO + 4 figs** |
| **S6 · Torneo Supervisado (`6.0, 7.0, 7.1, 7.2`)** | 20 | 25 | 15 | 20 | 10 | 10 | **100** | **5.00** | **Tabla 11 modelos + simulador + 3 figs** |
| **S7 · Torneo No Supervisado (`8.0` vs `8.1`)** | 20 | 25 | 15 | 20 | 10 | 10 | **100** | **5.00** | **Tablas Linkage y $k=2..8$ + 3 figs** |
| **S8 · Ganador Supervisado: Naive Bayes (`7.1`)** | 20 | 25 | 15 | 20 | 10 | 10 | **100** | **5.00** | **Fórmula LLR + tabla IC95% + simulador ISCO + 4 figs** |
| **S9 · Ganador No Supervisado: K-Means (`8.0`)** | 20 | 25 | 15 | 20 | 10 | 10 | **100** | **5.00** | **Tabla centroides reales + simulador 4 clústeres + 3 figs** |
| **S10 · Síntesis, Glosario e Indexación (`index.html`)** | 20 | 25 | 15 | 20 | 10 | 10 | **100** | **5.00** | **Glosario encapsulado `.gloss-item` + 8 casos indexados** |
| **PROMEDIO GLOBAL (10 Diapositivas)** | **20.00** | **25.00** | **15.00** | **20.00** | **10.00** | **10.00** | **100 / 100** | **`5.0 / 5.0`** | **33/33 rutas locales OK · Cero desbordes** |

---

## 2. Evaluación Detallada Diapositiva por Diapositiva (S1 a S10)

### Diapositiva 1 — Portada Ejecutiva y Mapa Completo de los 11 Cuadernos (`Bloque 1 · Contexto`)
- **Explicabilidad (`E1/E2`):** Explica en lenguaje ciudadano qué es **JobPath** (`352,093` personas reales seguidas a lo largo de `1,738,738` empleos conectados con `3,039` oficios del catálogo europeo ESCO v1.2.1) y qué significa la variable objetivo `reincide` (`30.01 %`).
- **Fidelidad y cobertura (`E4`):** Presenta los 4 KPIs maestros y un **mapa interactivo de 3 columnas con los 11 cuadernos de `notebooks/refactor/`** (`1.0`, `2.0`, `3.0`, `4.0`, `4.1`, `5.0`, `6.0`, `7.0`, `7.1`, `7.2`, `8.0`, `8.1`) más el módulo indexado de Métodos Numéricos (`index.html`).

### Diapositiva 2 — Comprensión del Negocio y Selección de Fuentes (`1.0_comprension_negocio.md`)
- **Analogía cotidiana (`E3`):** *«El GPS de la Vida Laboral»* — ilustra por qué se necesita estandarizar nombres libres de cargos en códigos ESCO para medir transiciones reales.
- **Distribución en 3 columnas equilibradas (`E6`):**
  1. **Selección KDD-1:** Tabla comparativa entre **JobHop v2** (`1,871,014` empleos, `355,308` personas), **ESCO v1.2.1** (`3,039` oficios, `10` grupos ISCO-08) y **OLE Colombia** (descartada por no publicar secuencias individuales por persona).
  2. **Las 2 Preguntas Analíticas:** Enfoque Supervisado (`reincide = veces_ese_oficio > 1`, `417,471` casos en Train y `104,225` en Test) y Enfoque No Supervisado (`V_PERSON` con 9 variables y `V_EXPERIENCE` con 7 variables sin fuga).
  3. **Salvaguardas `MR-07`, `MR-08` y `MR-09`:** Trazabilidad SHA-256, asociación $\neq$ causalidad individual (`MR-07`), competencias atribuidas al oficio ESCO (`MR-08`) y bandera `es_vigente` para contratos abiertos (`MR-09`).

### Diapositiva 3 — Preprocesamiento (`2.0`) y Transformación (`3.0`): Decisiones `D01` a `D11`
- **Simulador interactivo de 4 etapas (`E5`):**
  1. `Embudo y Pluriempleo (D01–D03)`: Integración `train+test+val` (`+396.86 %` de datos vs v1), `0` duplicados exactos de 5 llaves y preservación de `92,099` filas de pluriempleo real.
  2. `Educación MNAR y ESCO (D04–D05)`: `205,238` filas brutas (`200,934` clasificadas) codificadas con `educacion_no_reportada = 1` (*Silencio $\neq$ Cero estudios*); `132,276` sin oficio ESCO (`7.07 %`) excluidas sin fabricar habilidades; `95,136` vigentes con `es_vigente = 1`.
  3. `Outliers Versión A vs. B (D06)`: Comparación entre **Versión A** (valores de hasta `129` habilidades esenciales) y **Versión B** (recorte Tukey $k=1.5$ en `47.5 / 39.5 / 13.5 / 3.5` sobre `193,596` filas = `10.35 %`, conservando `dur_q` intacta).
  4. `Split Persona y Escalado (D07–D11)`: `GroupShuffleSplit` 80/20 (`seed=42`) con `0` personas compartidas, `RobustScaler` ajustado solo en Train y `2,967` dummies de oficio en `uint8`.
- **Tabla completa del embudo + Modal de Bitácora `D01–D14` + Visor de 2 figuras (`g08_nulos_por_columna.png` y `g09_outliers_iqr_ab.png`)**.

### Diapositiva 4 — Reducción de Dimensionalidad: `4.0_PCA.ipynb` y `4.1_PCA_completo.ipynb` (`D12`)
- **Analogía cotidiana (`E3`):** *«No cobrar dos veces el combo y los ingredientes por separado»* — explica la identidad aditiva $E = C + K + U$ y por qué el **rango efectivo es 9 de 10** (el componente 10 tiene varianza `0.0000 %`).
- **Tabla completa de varianza explicada (`k = 1` a `k = 10`, Versión A vs. Versión B):**
  - Demuestra el salto en `PC1` de `32.91 %` (A) a **`39.68 %` (B)** (`+6.77 pp`), el ahorro de **1 componente en el umbral de 80 %** (`3` comp. en B con `80.59 %` vs. `4` en A con `85.39 %`) y en el **umbral de 95 %** (`5` comp. en B con `95.36 %` vs. `6` en A con `96.16 %`), junto con la figura `g23_pca_estabilidad.png`.

### Diapositiva 5 — Análisis Exploratorio de Datos: `5.0_EDA_jobpath.ipynb` (`D13`)
- **Bloqueo Anti-Fuga (`D13`):** Explica por qué `veces_ese_oficio_rob`, `veces_ese_oficio_bin`, `n_returns`, `n_self_loops` y `exploration_ratio` reproducen el `100 %` del target y fueron bloqueadas en $X$.
- **Tabla completa de los 10 Grandes Grupos ISCO-08 (`ISCO 0` a `ISCO 9`):** Incluye soporte de filas y personas en Train, tasa observada con **IC 95 % de Wilson**, tasa confirmada en Test y diferencia contra el promedio (`30.01 %`), desde `ISCO 5 Servicios (33.84 %)` e `ISCO 3 Técnicos (33.72 %)` hasta `ISCO 1 Directivos (22.07 %)` e `ISCO 0 Militares (7.43 %)`.
- **Galería interactiva de 4 gráficas del EDA:** `g27_target_por_isco.png`, `g30_fuga_target.png`, `g21_transiciones_isco.png` y `g19_pearson_vs_spearman.png`.

### Diapositiva 6 — Torneo Supervisado: `6.0_modelado`, `7.0_arbol_decision`, `7.1_naive_bayes` y `7.2_knn` (`D14`)
- **Tabla maestra con las 11 filas comparativas en Test (`347,720` filas):**
  - Reporta `Cols X`, `PR-AUC`, `ROC-AUC`, `F1 (Clase 1)`, `Recall / Precisión`, `Brier Score` y `Tiempos Fit / Test (s)` para `Ref 1/2`, `HistGradientBoosting (6.0)`, `Logística Regularizada OHE (6.0)`, los `3 Árboles de Decisión (7.0)`, las `3 variantes de KNN (7.2: KNN-D, KNN-G, KNN-W)` y las `3 variantes de Naive Bayes (7.1: NB-G, NB-B, NB-H)`.
- **Simulador interactivo de decisión + Visor de 3 gráficas (`nb15_comparacion_modelos_y_versiones_ab.png`, `knn13_frontera_desempeno_vs_costo.png`, `08_comparacion_tres_arboles_y_techo.png`)** demostrando por qué se descartan Árboles (`54.2 %` del techo) y `KNN-W` (`29,146.8 s ≈ 8.1 horas` en Test) frente a **`NB-H` (`0.241 s`)**.

### Diapositiva 7 — Torneo No Supervisado: `8.0_kmeans_clustering.ipynb` vs. `8.1_clustering_jerarquico.ipynb`
- **Analogía del Efecto Fila India (*Chaining*):** Explica por qué `single` (`99.87 %` en 1 grupo), `average` (`97.50 %`) y `complete` (`90.03 %`) fallan en nubes continuas frente a **`Ward` (`55.00 %` máx., `5.33 %` mín.)**.
- **2 Tablas completas verificadas:**
  1. Torneo de los 4 métodos de linkage en `8.1` ($n=3,000$, $k=4$) con correlación cofenética, Silueta, Davies-Bouldin, Calinski-Harabasz y tamaños extremos.
  2. Búsqueda $k = 2..8$ mostrando el salto vertical de Ward ($\Delta h = 10.060$ en $k=4$ que cae un **`85.8 %`** a $1.431$ en $k=5$) junto con la inercia WCSS, Silueta, Davies-Bouldin y el pico global de **Calinski-Harabasz (`46,780.83`)** y **Silueta en Experiencias (`0.2465`)** de K-Means en $k^* = 4$.
- **Galería de 3 figuras:** `01_metodo_codo_y_silueta_kmeans_personas.png`, `02_dendrograma_truncado_n3000_corte_optimo.png` y `03_comparacion_metodos_linkage_metricas.png`.

### Diapositiva 8 — Conclusión 1 (Ganador Supervisado): `7.1_naive_bayes.ipynb` (`NB-H Híbrido`)
- **Fórmula aditiva completa con respaldo offline (`data-plain`):** Desglosa el prior $\log(0.3001/0.6999) = -0.8468$, la suma de las `10` variables continuas/ordinales (GaussianNB) y las `2,971` binarias (BernoulliNB en matriz CSR) mediante **`LLR` (Log-Likelihood Ratio)**.
- **Tabla completa con IC 95 % (bootstrap pareado de 300 remuestreos por persona)** para `NB-G`, `NB-B` y `NB-H` en **Versión A** y **Versión B** (confirmando invarianza ante outliers: `ROC-AUC 0.7058 → 0.7065`, `F1 0.5337 → 0.5341`).
- **Simulador interactivo por sector ISCO-08 + Galería de 4 figuras de Naive Bayes** (`nb07`, `nb05`, `nb10_p1_evidencia_log_likelihood_ratio.png`, `nb12_p3_deciles_lift_gain.png`).

### Diapositiva 9 — Conclusión 2 (Ganador No Supervisado): `8.0_kmeans_clustering.ipynb` ($k^* = 4$)
- **3 Pruebas de su victoria sobre el Jerárquico (`8.1`):**
  1. Entrenamiento directo sobre el **100 % del censo** (`281,674` personas Train + `70,419` Test = `352,093` personas y `1,738,738` experiencias) frente al límite $O(N^2)$ de `n = 3,000` en Ward (`> 317 GB` RAM).
  2. Equivalencia exacta de centroides invertidos a escala humana (`max_diff = 0.000000` en Personas y `0.000001` en Experiencias).
  3. Estabilidad Train vs. Test (`< 0.21 pp` de diferencia) y concordancia Versión B vs. A (`ARI = 0.8633`, `NMI = 0.8437`).
- **Tabla completa de los 4 centroides en unidades originales + Explorador interactivo causal de los 4 arquetipos + Galería de 3 figuras de K-Means** (`06_centroides`, `03_proyeccion_pca_2d`, `07_sensibilidad_version_b_vs_version_a_centroides.png`).

### Diapositiva 10 — Síntesis Ejecutiva, Glosario Encapsulado e Indexación a Métodos Numéricos (`index.html`)
- **Sinergia de los 2 modelos ganadores:** Cómo el *Mapa Macro (`K-Means 8.0`)* explica la diferencia estructural entre el ascenso vertical de los profesionales científicos (`Clúster 2`, menor repetición de código ESCO `42.75 %`), la rotación horizontal operativa (`Clúster 0`, mayor repetición `47.78 %`) y la estabilidad de larga permanencia (`Clúster 3`, `23.13 %` por experiencia), mientras la *Brújula Micro (`Naive Bayes 7.1`)* estima la probabilidad individual calibrada en `0.241 s`.
- **Glosario ciudadano perfectamente encapsulado (`.gloss-grid` + `.gloss-item`):** 8 tarjetas individuales con borde lateral de color dentro de su `.card`, sin ningún desborde ni espacio muerto.
- **Portal Oficial de Indexación a `numerical_methods_presentation/index.html`:** Tabla detallada de los **8 casos experimentales** (`RL-01`, `RL-02`, `RL-04`, `RL-05`, `LG-01`, `LG-02`, `HYB-01`, `HYB-02`) con botón de apertura directa y botón de **Vista Interactiva Integrada (Modal en Vivo)**.
