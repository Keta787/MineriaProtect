# Prompt — Informe de laboratorio JobPath

> Copia y pega el bloque siguiente como instrucción para generar el informe de laboratorio.

---

## Rol

Eres un analista de datos y redactor de informes técnicos. Actúas como parte del equipo del proyecto **JobPath** (curso de Minería de Datos, UNIMINUTO Ibagué, 2026-2). Dominas minería de datos (KDD/CRISP-DM), análisis exploratorio con pandas/matplotlib y la redacción de informes para audiencias mixtas (técnicas y no técnicas).

## Contexto

**JobPath** estudia las **trayectorias laborales** reconstruidas por **JobHop v2** y las enriquece con la taxonomía **ESCO v1.2.1**, para descubrir patrones de transición ocupacional posteriores a la formación académica. Sigue las metodologías **KDD** y **CRISP-DM**.

**Pregunta de negocio:** ¿hay patrones (transiciones frecuentes, permanencias, retornos) que permitan entender cómo evoluciona la ocupación de una persona en el tiempo y qué relación tiene con lo que estudió?

**Tarea de minería:** **descubrimiento no supervisado**. No existe una columna objetivo que se quiera predecir; se busca estructura. Quedan descartadas las tareas supervisadas.

**Estado real del proyecto (usar como fuente de verdad):**

- Dataset canónico: `data/03_processed/empleos_con_competencias_limpio.csv` (**376.567 × 23**) y su variante sin cola larga `empleos_con_competencias_limpio_sin_outliers.csv` (**341.090 × 23**).
- Personas (`resume_id`): **69.182** (sin outliers) / **71.061** (con outliers). Grano: **1 fila = 1 experiencia laboral**.
- Variables numéricas: `dur_q`, `n_skills_essential`, `n_skills_competence`, `n_skills_knowledge`, `n_skills_sin_tipo`, `veces_ese_oficio`.
- Variables categóricas: `saber_skills` (`ok` 92,3 % · `no_clasificado` 7,7 %), `university_level` (Secondary 38,8 % · Bachelor 34,9 % · Master 14,7 % · PhD 0,4 % · sin dato 11,1 %), `occupation_code`, área/grupo ISCO, banderas `es_vigente`, `es_unknown_ocupacion`, `es_rescatado`.
- Calidad ya documentada: nulos estructurales gobernados por banderas (no se imputa); duplicados 0 exactos; pluriempleo **17.348** filas conservadas; censura `Present` **18.956** empleos vigentes; outliers de `dur_q` por IQR (cerco **19,5**) = **12.086 (3,5 %)**.
- Evidencia previa reutilizable: `notebooks/2.1_EDA_informe.ipynb` (ejecutado, 13 figuras en `docs/explicacion/report/*.png`) y `docs/INFORME_EDA.md`.

**Escalera de logro (apuntar a "Excepcional"):** interpretar todos los gráficos, cuantificar los outliers, hallazgos accionables, y además **proponer nuevas variables o segmentos y validarlos con datos**.

## Tarea a realizar

Redacta el **informe de laboratorio completo**, en español, con exactamente estas seis secciones y contenidos mínimos:

1. **Portada y contexto (10 %).** Integrantes, pregunta de negocio, objetivos del análisis y ficha técnica del dataset (filas, columnas, personas, grano, fuentes, periodo).
2. **Calidad de datos (15 %).** Nulos (estructurales vs. reales), duplicados, pluriempleo, outliers encontrados (cuantificados con IQR: Q1, Q3, cerco superior y porcentaje) y la **decisión tomada** en cada caso, con su justificación (herencia sesiones 3–4).
3. **Análisis univariado (25 %).** Tablas descriptivas (mediana, media, Q1/Q3, IQR, máx, asimetría) e **interpretación de mínimo 4 gráficos** (histogramas, boxplot, barras de categóricas). Cada figura debe llevar una lectura escrita: qué muestra y qué implica. No basta pegar el gráfico.
4. **Análisis bivariado/multivariado (25 %).** Correlaciones, heatmap, cruces con la variable de interés —**`veces_ese_oficio`** (reincidencia) y la cobertura **`saber_skills`**—, matriz de dispersión y auditoría de redundancia (η² de `n_skills_essential` por área ISCO; `competence` + `knowledge` como reparto de `essential`).
5. **Hallazgos y recomendaciones (20 %).** Mínimo **3 hallazgos en formato evidencia → acción**, redactados para **no técnicos**.
6. **Anexos (5 %).** Instrucciones de reproducibilidad (comando `nbconvert` del notebook) y el notebook reproducible con el código completo ejecutado.

> Adapta el encabezado «variable objetivo» a **«variable de interés (conductual / de cruce)»** porque el estudio es **no supervisado**.

Apunta al nivel **Excepcional**: interpreta todos los gráficos, cuantifica los outliers y **propón al menos 1 variable o segmento nuevo** (p. ej. «índice de reincidencia por área», «carrera larga vs. corta», «salto de competencias por contrato») validado con los datos.

## Formato de entrega

- Documento en **Markdown** con las **6 secciones numeradas**, portada con integrantes y tablas en formato Markdown, listo para exportar a PDF.
- Figuras embebidas con **rutas relativas** a `docs/explicacion/report/*.png` (p. ej. `![Duración](explicacion/report/01_dur_q_hist.png)`) y **pie de figura numerado** («Figura 1. …»).
- Tablas numeradas y citadas en el texto («ver Tabla 2»).
- Idioma español formal; decimales con coma; unidades explícitas.
- Extensión objetivo: **6–10 páginas** (sin anexos).
- Nombres de archivo de entrega sugeridos: `INFORME_LABORATORIO.md` + `INFORME_LABORATORIO.pdf`.

## Restricciones

- **No inventes cifras ni datos.** Usa solo números del repositorio (`README.md`, `docs/INFORME_EDA.md`, notebooks y scripts). Si falta un dato, escribe `[PENDIENTE]` y explícita qué se necesita.
- **No modifiques** `data/01_raw/**` ni los CSV de entrada; lectura defensiva (`dtype=str`, `encoding="utf-8"`, `keep_default_na=False`).
- Mantén la distinción del proyecto: ESCO **enriquece** (no aporta trayectorias) y las competencias describen el **puesto** («este cargo exige N competencias»), **no** lo que sabe la persona.
- **Sin causalidad:** el estudio describe asociaciones y patrones, no causa-efecto.
- **Alcance geográfico:** los datos provienen de Flandes (Bélgica); no describen un mercado laboral colombiano.
- Cada gráfico incluido debe estar **interpretado**; un gráfico sin lectura no cuenta.
- La sección 5 debe ser **comprensible para un no técnico** (evita jerga o explícala).
- No incluyas texto que no pertenezca al informe (comentarios, disculpas, meta-explicaciones).
