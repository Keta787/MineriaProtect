# Instrumento de evaluación · PEA — Informe de laboratorio

> **Qué es este documento.** Es la **rúbrica de evaluación** del informe de laboratorio de la
> unidad (PEA) transcrita como fuente de verdad del proyecto, más una **tabla de trazabilidad**
> que indica, sección por sección, dónde queda la evidencia en este repositorio.
>
> **Nada de este documento es invención:** los pesos y la escalera de logro son el instrumento
> tal cual; las columnas de evidencia apuntan a archivos reales (`notebooks/`, `docs/`, `data/`).

**Proyecto:** JobPath · **Asignatura:** Minería de Datos (2026-2, Unidad 1) ·
**Programa:** Especialización en Ingeniería de Sistemas · **UNIMINUTO Ibagué** ·
**Docente:** Esteban Ernesto Morales Castro.

---

## 1. Estructura exigida del informe de laboratorio

| # | Sección | Contenido mínimo | Peso |
|---|---|---|---:|
| 1 | **Portada y contexto** | Integrantes, pregunta de negocio del proyecto, objetivos del análisis | **10 %** |
| 2 | **Calidad de datos** | Nulos, duplicados, outliers encontrados y decisiones tomadas (herencia sesiones 3-4) | **15 %** |
| 3 | **Análisis univariado** | Tablas descriptivas + **mínimo 4 gráficos interpretados** (no solo pegados) | **25 %** |
| 4 | **Análisis bivariado/multivariado** | Correlaciones, cruces con la variable objetivo, heatmap | **25 %** |
| 5 | **Hallazgos y recomendaciones** | Mínimo **3 hallazgos formato evidencia-acción**, redactados para no técnicos | **20 %** |
| 6 | **Anexos** | **Notebook reproducible** con el código completo ejecutado | **5 %** |
| | | **Total** | **100 %** |

### Regla de lectura de la rúbrica

- **Los gráficos no son decorativos.** La sección 3 exige *interpretados*: cada figura necesita
  una lectura escrita (qué se ve, cuánto, por qué importa), no solo la imagen pegada.
- **La sección 4 pide explícitamente un heatmap** y cruces con la variable objetivo.
  ⚠️ Este proyecto es **no supervisado** (no hay columna objetivo que predecir; ver
  `notebooks/1.0_comprension_negocio.md` §2). Por eso el cruce se hace contra las **variables
  clave** del proyecto (`university_level` y `isco_group_label`), y el heatmap se resuelve con la
  **matriz de correlaciones de Pearson** de las variables numéricas.
- **Los hallazgos deben ser evidencia-acción** (no observaciones sueltas) y escritos para alguien
  que no programa.

---

## 2. Escalera de logro

| Nivel | Criterio |
|---|---|
| **Inicio** | Presenta tablas y gráficos básicos con apoyo de la plantilla. |
| **Progreso** | Interpreta la mayoría de gráficos y cuantifica algunos outliers. |
| **Esperado** | Informe completo, interpretaciones correctas y hallazgos accionables. |
| **Excepcional** | Además, propone **nuevas variables o segmentos** y **valida sus hipótesis con datos**. |

---

## 3. Tabla de trazabilidad (dónde está la evidencia aquí)

| § | Exigencia de la rúbrica | Evidencia en este repositorio |
|---|---|---|
| **1** | Integrantes, pregunta de negocio, objetivos | Portada del `Informe_...docx` · `notebooks/1.0_comprension_negocio.md` §1-§3 (acta: pregunta de negocio, pregunta técnica, objetivo, criterios de éxito) · `README.md` §Objetivo |
| **2** | Nulos, duplicados, outliers y decisiones | `notebooks/2.1_EDA_informe.ipynb` **§6** (imprime nulos por columna, regla *vacío ≠ 0*, censura `Present`, pluriempleo) · `notebooks/3.0_preprocesamiento.ipynb` (pipeline de 7 fases, validación 6/6) · `src/limpieza/limpiar_empleos_con_competencias.py` · `README.md` §Datasets y calidad |
| **3** | Tablas descriptivas + ≥4 gráficos interpretados | `notebooks/2.1_EDA_informe.ipynb` **§2**: tabla de medidas (media, mediana, moda, sd, Q1/Q3, IQR, asimetría, curtosis) + figuras **01–05** y **13** |
| **4** | Correlaciones, cruces, heatmap | `notebooks/2.1_EDA_informe.ipynb` **§3-§5**: figuras **06–12** (correlaciones, dispersión, reincidencia, demanda) y **heatmap** de correlaciones (fig. **09**) · `docs/img/eda_nivel_por_oficio.png` (cruce *oficio × nivel educativo*) |
| **5** | ≥3 hallazgos evidencia-acción para no técnicos | `notebooks/2.1_EDA_informe.ipynb` **§7 «Hallazgos accionables»** (H1…) · §5 del informe Word |
| **6** | Notebook reproducible ejecutado | `notebooks/2.1_EDA_informe.ipynb` (34 celdas, 13 figuras, salidas persistidas) · `docs/EDA.md` §6 (código que genera la figura final) · `README.md` §Cómo ejecutar |

---

## 4. Reglas de visualización exigidas a las figuras (control de calidad)

Lista "Buenas prácticas de visualización" usada como checklist antes de publicar
(evidencia completa en `docs/EDA.md` §13):

| | Regla |
|---|---|
| **Siempre** | Ejes etiquetados **con unidades** · **título que declara el hallazgo** (no el tipo de gráfico) · barras **desde cero** + anotaciones directas sobre el dato clave · **paleta consistente y accesible (verificable en escala de grises)** |
| **Nunca** | Pastel 3D · truncar el eje Y de barras · doble eje Y · colormap arcoíris para variables continuas |
| **Regla final** | Si el gráfico necesita defensa verbal para no engañar, está mal diseñado. |

> *Criterio ético.* La honestidad visual es parte de la ética del ingeniero de datos: un gráfico
> de este proyecto **describe patrones, no toma decisiones de contratación** (fuera de alcance
> declarado en `notebooks/1.0_comprension_negocio.md` §3).

---

## 5. Dataset que sostiene el informe

| Dato | Valor verificado |
|---|---|
| Archivo | `data/03_processed/empleos_con_competencias_limpio_sin_outliers.csv` |
| Filas × columnas | **341.090 × 23** |
| Personas (`resume_id`) | **69.182** |
| Grano | **1 fila = 1 empleo** (experiencia), no 1 persona |
| Cobertura ESCO | 314.904 `ok` (92,3 %) · 26.186 `no_clasificado` (7,7 %) |
| Fuente / mercado | JobHop v2 + ESCO v1.2.1 · **Flandes, Bélgica** (método, no cifras aplicables a Colombia) |
| Periodo de los empleos | inicio 1967–2021 · fin 1970–2024 (vigentes censurados en Q1 2026) |

---

*Documento de control del entregable Word `Informe_Laboratorio_JobPath.docx` (mismo directorio).*
