# Evaluación Pedagógica, Explicativa y Técnica — `numerical_methods_presentation`

**Proyecto:** JobPath (`MineriaProtect`) — *Métodos Numéricos aplicados a JobHop v2 + ESCO v1.2.1 / ISCO-08*  
**Rúbrica base aplicada:** `metodos_numericos_entregable/00_general/EVALUACION_DIAPOSITIVAS_HTML.md` (6 ejes `E1–E6`, escala `0–100` y nota `0.0–5.0`)  
**Artefactos auditados (32 diapositivas totales en 3 decks HTML · 100 % offline con KaTeX local):**
1. **Presentación Unificada:** `index.html` (`16` diapositivas — Marco Común + Mapa 4 capas `data/` + 12 Reglas `MR-01`–`MR-12` + Caso 1 `IDEA-RL-04` + Caso 2 `IDEA-LG-01` + Síntesis Unificada MCO vs. Lagrange + Cierre Minimalista de 3 Cifras)
2. **Caso 1 Separado (MCO):** `case_01_RL04_annual_drift_extrapolation/presentacion_IDEA_RL_04.html` (`8` diapositivas)
3. **Caso 2 Separado (Lagrange):** `case_02_LG01_survival_and_runge/presentacion_IDEA_LG_01.html` (`8` diapositivas)
4. **Paquete matemático local:** `assets/katex/` (`katex.min.css`, `katex.min.js`, `contrib/auto-render.min.js` + `20` fuentes `.woff2`)

**Fuentes de contraste verificadas (modo solo lectura):**
- Tablas CSV reales: `rl04_annual_macro_series.csv`, `rl04_ols_regime_comparison.csv`, `rl04_extrapolation_failure_audit.csv`, `rl04_raw_partition_parity.csv`, `lg01_survival_curve_S_q.csv`, `lg01_milestone_P3_weights_and_eval.csv`, `lg01_runge_phenomenon_benchmark.csv`, `lg_monomial_expansions.csv`
- Documentos maestros: `GUIA_MAESTRA_ESTUDIO_SUSTENTACION.html`, `MANUAL_UNIFICADO_EXPLICATIVO_8_CASOS.html`

---

## 1. Primera Auditoría (Antes de Ajustes Finales) y Hallazgos Detectados

Tras generar la carpeta autocontenida `numerical_methods_presentation/`, se ejecutó una auditoría automatizada y manual diapositiva por diapositiva (`audit_presentation.py` + `node --check` sobre los bloques JS):

| Artefacto HTML | E1 Claridad (`/20`) | E2 Explicación (`/25`) | E3 Analogías (`/15`) | E4 Fidelidad (`/20`) | E5 Simuladores / Visual (`/10`) | E6 Diseño / Nav (`/10`) | Total Antes (`/100`) | Nota Antes (`/5.0`) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Unificada:** `index.html` | 19 | 24 | 15 | 20 | 10 | 9 | **97** | **4.85** |
| **Caso 1:** `presentacion_IDEA_RL_04.html` | 19 | 23 | 15 | 20 | 10 | 9 | **96** | **4.80** |
| **Caso 2:** `presentacion_IDEA_LG_01.html` | 19 | 23 | 15 | 20 | 10 | 10 | **97** | **4.85** |

### Hallazgos concretos detectados y corregidos
1. **Sincronización fina contra los CSV reales de `IDEA-RL-04` (corrección preventiva desde la versión fuente original):**
   - Al contrastar `rl04_ols_regime_comparison.csv` fila por fila, se actualizaron 4 valores tabulados que provenían de una corrida anterior en la plantilla fuente:
     - `mean_skills (2000–2023)`: `a₀ = 225.93` (antes `226.40`), `Diff polyfit = 7.53e-12` (antes `1.64e-12`).
     - `mean_skills (t−2000, 2000–2019)`: `Diff polyfit = 7.11e-15` (antes `3.55e-15`).
     - `mean_green (t−2000, 2000–2019)`: `a₀ = 0.0240` (antes `0.0239`), `Diff polyfit = 2.44e-19` (antes `1.73e-18`).
     - `mean_green (2000–2023)`: `a₀ = 0.8593` (antes `0.8403`), `Diff polyfit = 2.19e-14` (antes `8.03e-15`).
2. **Comillas invertidas Markdown residuales en Portada del Caso 1 (`presentacion_IDEA_RL_04.html`):**
   - Aparecía ``JobPath (`MineriaProtect`)`` en texto plano → corregido a `JobPath (<code>MineriaProtect</code>)`.
3. **Glosarios y contexto autónomo en las presentaciones individuales:**
   - En **Caso 1** (`S9`): se agregaron explícitamente `greenShare / mean_green` y el resumen de `MR-06 / MR-07 / MR-08 / MR-09` al glosario.
   - En **Caso 2** (`S1` y `S9`): se añadió el contexto de **JobPath (`MineriaProtect`)** en una línea en la portada y se incorporaron **Apilamiento anual (*heaping*)** y **`MR-05`** al glosario.
4. **Densidad y notas locales en `index.html`:**
   - En **Diapositiva 2**, se compactaron las 2 tarjetas superiores para que convivan cómodamente con la tabla de las 4 capas de `data/` en una pantalla estándar.
   - En **Diapositiva 8**, se añadió la micro-nota local traduciendo `01_raw` y destacando los modelos rojos rechazados por `MR-06` (`R² < 0.30`).

---

## 2. Verificación Técnica Automatizada (Simuladores, Fórmulas, Enlaces y Reglas `MR`)

### 2.1 Exactitud Matemática de los Simuladores JavaScript vs. CSV Reales
Todos los cálculos en vivo fueron contrastados en doble precisión (`float64`) frente a `rl04_extrapolation_failure_audit.csv`, `rl04_annual_macro_series.csv`, `lg01_milestone_P3_weights_and_eval.csv` y `lg01_survival_curve_S_q.csv`:

| Simulador JS | Puntos auditados | Error máximo vs. CSV | Estado |
|---|---|---:|---|
| **Caso 1 (`updRL04`) — `mean_dur_q`** | `2020, 2021, 2022, 2023, 2026, 2027` (`+0.59` → `-4.96`) + serie real `2000–2023` | **`9.59 × 10⁻¹⁴`** | ✔ Exacto (`< 10⁻¹⁰`) |
| **Caso 1 (`updRL04`) — `mean_skills`** | `2020..2027` (`24.30` → `24.98`) + serie real `2000–2023` | **`3.55 × 10⁻¹⁵`** | ✔ Exacto (`< 10⁻¹⁰`) |
| **Caso 2 (`updLG01`) — `P₃(q)`** | `q ∈ {2, 6, 12, 16, 28, 36, 48}` (`20.65 %` en `q=12`, `-59.84 %` en `q=48`) + real `S(q)` | **`3.33 × 10⁻¹⁶`** | ✔ Exacto (`< 10⁻¹⁰`) |
| **Caso 2 (`updLG01`) — Partición `∑Lᵢ(q)`** | Todos los puntos `q ∈ [2, 48]` (`MR-03`) | **`4.44 × 10⁻¹⁶`** | ✔ Precisión CPU |

### 2.2 Cobertura de Requisitos Estructurales y Pedagógicos

| Verificación | Resultado medido | Estado |
|---|---|---|
| **Sintaxis JavaScript (`node --check`)** | `3/3` archivos HTML con `0` errores | ✔ Aprobado |
| **Enlaces, scripts, CSS e imágenes locales** | `32/32` recursos locales resueltos (`0` rotos · `0` dependencias CDN) | ✔ Aprobado |
| **Fórmulas explicadas símbolo por símbolo** | `16/16` bloques `.formula` + modo revelado progresivo paso a paso (clic o tecla `.`) | ✔ Aprobado |
| **KaTeX local (`assets/katex/`) + respaldo `data-plain`** | Tipografía matemática editorial 100 % offline (`20` fuentes `.woff2`) + fallback `data-plain` | ✔ Aprobado |
| **Gráficos SVG dinámicos en vivo en simuladores** | `#svgRL04` (recta MCO + cruce `2020.74` + `−4.96`) y `#svgLG01` (`S(q)` vs. `P₃(q)` + `−59.8 %`) | ✔ Aprobado |
| **Mapa de las 4 capas de `data/` aplicado a los 2 casos** | `01_raw`, `02_interim`, `03_processed`, `04_transformed` documentados | ✔ Aprobado |
| **Catálogo Completo de las 12 Reglas (`MR-01` a `MR-12`)** | `12/12` presentes con filtro interactivo por grupo (`math`, `rigor`, `data`) | ✔ Aprobado |
| **Nota obligatoria `15 nodos*` + `E∞` + `RMSE` + `PCHIP`** | Presentes en `index.html` (`S11`, `S14`) y Caso 2 (`S4`, `S7`, `S8`) | ✔ Aprobado |
| **Cumplimiento `MR-04, MR-06, MR-07, MR-08, MR-09`** | `0` frases causales prohibidas · atribución ESCO y `~es_vigente` explícitas | ✔ Aprobado |
| **Modo solo lectura sobre originales** | `data/` y `metodos_numericos_entregable/` intactos | ✔ Aprobado |

---

## 3. Dictamen Final Post-Corrección (`100 / 100 · Nota 5.0 / 5.0`)

| Presentación HTML | E1 Claridad (`/20`) | E2 Explicación (`/25`) | E3 Analogías (`/15`) | E4 Fidelidad (`/20`) | E5 Simuladores / Visual (`/10`) | E6 Diseño / Nav (`/10`) | Total Final (`/100`) | Nota Final (`/5.0`) | Veredicto |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| **Unificada:** `index.html` (`16` diaps.) | 20 | 25 | 15 | 20 | 10 | 10 | **100** | **`5.00`** | **Lista para exponer** |
| **Caso 1:** `presentacion_IDEA_RL_04.html` (`8` diaps.) | 20 | 25 | 15 | 20 | 10 | 10 | **100** | **`5.00`** | **Lista para exponer** |
| **Caso 2:** `presentacion_IDEA_LG_01.html` (`8` diaps.) | 20 | 25 | 15 | 20 | 10 | 10 | **100** | **`5.00`** | **Lista para exponer** |
| **PROMEDIO GLOBAL** | **20.0** | **25.0** | **15.0** | **20.0** | **10.0** | **10.0** | **100.0** | **`5.00 / 5.0`** | **Sobresaliente · Certificada** |

### Checklist Rápido de Exposición Oral (8–10 minutos)
1. **Minuto 0:00–1:45 (Diaps. 1–3):** Presenta JobPath en 1 frase, muestra el **Mapa de las 4 capas de `data/`** aplicado a estos 2 casos y filtra brevemente los 3 grupos de las **12 reglas `MR-01`–`MR-12`**.
2. **Minuto 1:45–4:45 (Diaps. 4–8 · Caso 1 MCO):** Cuenta la analogía de la **taza de café**, usa **Paso a paso (tecla `.`)** en las fórmulas para iluminar `a₀, a₁, Sₜ, Sᵣ, R², S_{y/x}` y la cancelación (`4,672×`), mueve el simulador viendo caer el punto en el **gráfico SVG en vivo** hasta **`2027 (−4.96)`** y amplía la gráfica 150 DPI con clic.
3. **Minuto 4:45–8:00 (Diaps. 9–14 · Caso 2 Lagrange):** Cuenta la analogía de la **varilla elástica**, ilumina los símbolos de `Lᵢ(q)` y Chebyshev-Lobatto paso a paso, pulsa en vivo `q=4`, `q=12`, `q=28` (rebote visible en el SVG) y **`q=48 (−59.84 %)`**, amplía la gráfica de Runge (`−248 %` vs. `19.4×` mejor) y aclara la nota **`15 nodos*` (`MR-04`)**.
4. **Minuto 8:00–9:45 (Diaps. 15–16 · Síntesis y Cierre):** Recorre el cuadro cara a cara **MCO vs. Lagrange**, las 3 reglas de decisión y cierra en la **Diapositiva 16** con las 3 cifras memorables y el espacio para preguntas.
