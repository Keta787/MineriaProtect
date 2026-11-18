# Informe EDA — JobPath

**Análisis Exploratorio de Datos (EDA) · CRISP-DM fase 2 · KDD etapa de entendimiento**
**Minería de Datos · UNIMINUTO Ibagué · 2026-2**

- **Dataset:** `data/02_interim/empleos_con_competencias_limpio_sin_outliers.csv` (341.090 × 23)
- **Fuentes:** JobHop v2 (Flandes, Bélgica; unión test + val) enriquecido con ESCO v1.2.1
- **Evidencia reproducible:** `notebooks/2.1_EDA_informe.ipynb` (ejecutado, 13 figuras)
- **Figuras:** `docs/explicacion/report/*.png`

> **Por qué este informe.** El único EDA previo del repositorio (`2.0`) se ejecutó el 2026-09-15, **antes**
> de integrar las seis columnas de competencias ESCO, y su salida no las cubre. Este informe trabaja sobre el
> dataset enriquecido completo.
>
> **Alcance.** Se analiza la variante **sin cola larga** (recorte IQR de Tukey, `dur_q ≥ 25`). No hay
> contraste con el set con cola larga porque esa versión no está en disco: es un límite declarado.

---

## 1. Ficha técnica

| Métrica | Valor |
|---|---|
| Filas | 341.090 |
| Columnas | 23 |
| Personas (`resume_id` únicos) | 69.182 |
| Grano | 1 fila = 1 experiencia laboral |
| Periodos distintos (persona, inicio, fin) | 323.742 |
| Cargos distintos (`occupation_code`) | 2.826 |
| Primer periodo | Q1 1967 |

El dataset tiene **una fila por experiencia** (no por persona ni por oficio): `resume_id` agrupa la
trayectoria. Las seis columnas de competencias describen el **puesto** (lo que exige el oficio), no a la
persona; la única columna conductual es `veces_ese_oficio`.

Diccionario y tipos: ver §0–§1 del notebook `2.1`.

---

## 2. Análisis univariado

| Variable | Mediana | Media | Q1 | Q3 | IQR | Máx | Asimetría |
|---|---:|---:|---:|---:|---:|---:|---:|
| `dur_q` (trimestres) | 5 | 6,27 | 2 | 9 | 7 | 24 | 1,41 |
| `n_skills_essential` | 20 | 23,31 | 15 | 28 | 13 | 99 | 2,24 |
| `n_skills_competence` | 18 | 19,32 | 12 | 23 | 11 | 69 | 1,92 |
| `n_skills_knowledge` | 3 | 3,98 | 1 | 6 | 5 | 45 | 3,84 |
| `n_skills_sin_tipo` | 0 | 0,01 | 0 | 0 | 0 | 2 | 11,53 |
| `veces_ese_oficio` | 1 | 1,59 | 1 | 2 | 1 | 19 | 3,33 |

Todas las numéricas son **asimétricas positivas** (media > mediana): se reporta la **mediana** como medida
de centro. La cola derecha de `dur_q` ya está recortada por diseño (máx 24).

![Distribución de la duración](explicacion/report/01_dur_q_hist.png)

![Distribución de competencias esenciales](explicacion/report/02_n_skills_essential_hist.png)

**Outliers cuantificados (IQR):** en `dur_q`, Q1 = 2, Q3 = 9, IQR = 7, cerco superior = 19,5 →
**12.086 experiencias (3,5 %)** quedan por encima. No son error: son carreras largas dentro de la variante
preservada.

![Boxplot de duración con IQR](explicacion/report/03_dur_q_boxplot.png)

**Categóricas.** `saber_skills` = `ok` 314.904 (92,3 %) / `no_clasificado` 26.186 (7,7 %). Nivel educativo:
**Secondary school 132.489 (38,8 %)**, Bachelor 118.999 (34,9 %), Master 50.273 (14,7 %), PhD 1.461
(0,4 %), sin dato 37.868 (11,1 %).

![Categóricas](explicacion/report/04_categoricas_barras.png)

![Top 15 oficios](explicacion/report/05_top_oficios.png)

---

## 3. Análisis bivariado

**Duración por área ocupacional.** La mediana varía hasta **3×** entre áreas (3 a 9 trimestres): docencia
de secundaria es la más corta (3), gerencia de comercio la más larga (9).

![Duración por área ISCO](explicacion/report/06_dur_q_por_area.png)

**Duración vs. demanda de competencias.** La correlación de Pearson es **r ≈ −0,02**: ambas dimensiones son
casi ortogonales. La duración no anticipa cuántas competencias exige el cargo.

![Dispersión demanda–duración](explicacion/report/07_scatter_essential_duracion.png)

**Reincidencia por área.** La tasa global de reincidencia (`veces_ese_oficio > 1`) es **31,5 %**. Docencia
de primaria (60,9 %), enfermería (60,6 %) y docencia de secundaria (58,7 %) casi duplican el promedio;
comercio y secretariado rondan el 48 %.

![Reincidencia por área](explicacion/report/08_reincidencia_por_area.png)

---

## 4. Análisis multivariado

![Heatmap de correlaciones](explicacion/report/09_heatmap_correlaciones.png)

Lecturas clave de la matriz:

- `start_ord` ↔ `end_ord` = **0,99** (misma línea de tiempo).
- `dur_q` ↔ `start_ord` = **−0,32**: las experiencias recientes duran menos (censura por la derecha).
- `n_skills_essential` ↔ `n_skills_competence` = **0,95**; ↔ `n_skills_knowledge` = **0,62**;
  `competence` ↔ `knowledge` = **0,35**.
- `dur_q` ↔ `n_skills_essential` = **−0,02** (dimensiones independientes).

![Matriz de dispersión](explicacion/report/10_matriz_dispersion.png)

**Auditoría de redundancia.** `n_skills_essential` es **determinista de `occupation_code`** (1 solo valor
por oficio en los 2.826 oficios) con **η² = 0,73** respecto del grupo ISCO: el área explica ~73 % de su
varianza. `competence` + `knowledge` son un **reparto** de `essential`, no variables nuevas. Tras el recorte
de `no_clasificado`, dentro de la matriz `X` las banderas `es_unknown_ocupacion` y `es_rescatado` quedan
**constantes**, y `emparejado` colapsa a una sola categoría (`ok`): ninguna aporta señal y deben excluirse.

---

## 5. Competencias ESCO

**Reparto saber / saber-hacer.** El ratio `competence / essential` tiene mediana **0,85**: domina el *saber
hacer*. En **309.709 de 314.904** registros (98,4 %) el ratio supera 0,5.

![Ratio saber-hacer](explicacion/report/11_ratio_saber_hacer.png)

**Demanda media por área.** Servicios sociales (**58,8**), manipulación de carga (32,1) y docencia de
secundaria (30,4) encabezan; cajeros (10,3) y secretariado (17,8) son los menos exigentes. Media global:
**23,3** competencias.

![Demanda por área](explicacion/report/12_demanda_por_area.png)

**Oficios más exigentes (≥ 200 experiencias):** psicólogo clínico (99), enfermería general (92),
fisioterapeuta (90), educador infantil (73).

**Vocabulario de competencias.** El dataset contiene **6.082.711** pares (experiencia, competencia) con
**8.485** competencias distintas; las **10 más frecuentes cubren solo el 5,6 %**. El vocabulario es de cola
larga y específico de cada puesto, lo que refuerza que la unidad útil de análisis es el **oficio**, no un
«perfil promedio».

---

## 6. Diagnóstico de calidad

![Cobertura de competencias](explicacion/report/13_calidad_ok_vs_noclasi.png)

| Control | Resultado |
|---|---|
| Vacío ⟺ `no_clasificado` | ✅ (contadores vacíos exactamente en las 26.186 filas sin oficio) |
| Contadores en 0 en filas clasificadas | ✅ 0 (el 0 está prohibido; el vacío ≠ 0) |
| `competence + knowledge + sin_tipo = essential` | ✅ cierra en todas las filas clasificadas |
| Censura `Present` | 18.956 empleos vigentes con `es_vigente`, sin inventar fecha de fin |
| Pluriempleo | 341.090 filas vs 323.742 periodos → **17.348 filas de más** (conservadas) |
| Filas fuera de `X` | 26.186 (`no_clasificado`, **7,68 %**) |

No hay nulos «sucios»: los vacíos son estructurales y gobernados por banderas. El pluriempleo no es
duplicado —son cargos simultáneos o transiciones dentro del mismo trimestre— y se conserva.

---

## Hallazgos accionables

**H1. La cobertura ESCO gobierna el universo analizable.** 314.904 experiencias `ok` (92,3 %) frente a
26.186 `no_clasificado` (7,7 %). → La construcción de `Sₚ` debe definir el tratamiento de `unknown`
(deuda **D1**): excluirlas o analizarlas como segmento propio; hoy serían un hueco que rompe la cadena.

**H2. La trayectoria típica es corta y la cola larga ya fue recortada.** Mediana 5 trimestres, Q3 9, máx 24.
→ Las secuencias serán cortas (1–3 empleos dominantes); usar umbrales de soporte bajos y recordar que la
estabilidad extrema queda subrepresentada por diseño.

**H3. La reincidencia es un tercio del dataset.** 31,5 % de las experiencias ocurren en un oficio ya
ejercido por la misma persona. → `Sₚ` debe incorporar la repetición como señal (retorno al oficio), no
deduplicarla; docencia y enfermería reinciden casi el doble del promedio.

**H4. Duración y demanda de competencias son ortogonales.** r ≈ −0,02. → Para caracterizar transiciones se
necesitan **ambas** dimensiones; ninguna resume a la otra. Confirma además por qué el PCA no comprime.

**H5. El «saber hacer» domina y el vocabulario es de cola larga.** Ratio > 0,5 en el 98,4 %; top-10 de
competencias cubre 5,6 % de los pares. → Medir el salto entre contratos con Jaccard sobre listas, no con
conteos; el oficio es la unidad de análisis.

**H6. Hay redundancia estructural que debe declararse antes de modelar.** `n_skills_essential` determinista
de `occupation_code`; `competence`+`knowledge` reparten `essential`; banderas constantes dentro de la `X`.
→ Elegir una sola representación del oficio (número **o** one-hot) y excluir banderas constantes.

---

### Reproducibilidad

```bash
python -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=600 notebooks/2.1_EDA_informe.ipynb
```

Cada cifra de este informe se regenera al reejecutar el cuaderno. La ruta del CSV se resuelve buscando la
carpeta `data/` hacia arriba; no se modifica `data/01_raw/**` ni el CSV de entrada.
