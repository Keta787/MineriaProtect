# Scripts y módulos del proyecto

Esta carpeta contiene los puntos de entrada que preparan los archivos del
proyecto (`pipeline/limpieza/`) y los paquetes modulares que alimentan los
cuadernos de `notebooks/refactor/` (`ScriptsCsv/`).

## Pipeline de datos

Los pasos de limpieza e integración iniciales están en
[`pipeline/limpieza/`](./pipeline/limpieza/):

```text
scripts/pipeline/limpieza/
├── limpiar_datos.py
├── integrar_empleos.py
├── limpiar_empleos.py
├── generar_competencias.py
├── unificar_competencias_empleos.py
├── unificar_raw_completo.py
└── limpiar_unificado.py
```

- **Flujo unificado vigente para `notebooks/refactor/` (train + test + val):**
  - `unificar_raw_completo.py` une **todos** los CSV de `data/01_raw/` (JobHop
    train + test + val, ESCO occupations/ISCOGroups y SKILLS relations/skills)
    por el código ESCO, sin eliminar filas, en
    `data/02_interim/Unificacion/empleos_unificado_completo.csv`
    (1.993.291 filas × 23 columnas, ~1,5 GB).
  - `limpiar_unificado.py` aplica el pipeline de limpieza y Data Hygiene sobre el
    dataset unificado completo y genera la entrada maestra de los cuadernos
    refactorizados: `data/03_processed/empleos_unificado_limpio.csv`
    (1.871.014 filas × 23 columnas, 355.308 personas, **Versión A · con outliers**).
  - A partir de ese archivo, `notebooks/refactor/2.0_preprocesamiento_jobpath.ipynb`
    genera `data/03_processed/empleos_limpio_con_competencias_sin_outliers.csv`
    (1.871.014 filas × 23 columnas, **Versión B · sin outliers IQR**), y
    `notebooks/refactor/3.0_transformacion.ipynb` exporta las particiones por
    persona (`X_train` de 1.391.018 × 2.985 y `X_test` de 347.720 × 2.985) en
    `data/04_transformed/`.
- **Flujo histórico anterior (solo test + val):**
  `limpiar_datos.py` → `integrar_empleos.py` → `limpiar_empleos.py` +
  `generar_competencias.py` → `unificar_competencias_empleos.py` generaban
  `data/03_processed/empleos_limpio_con_competencias.csv` (376.567 filas,
  71.061 personas).

Se ejecutan desde la raíz del repositorio. Por ejemplo:

```powershell
python scripts/pipeline/limpieza/unificar_raw_completo.py
python scripts/pipeline/limpieza/limpiar_unificado.py
```

## Módulos de `notebooks/refactor/` (`ScriptsCsv/`)

- [`ScriptsCsv/Preproccesing/`](./ScriptsCsv/Preproccesing/): preprocesamiento y
  tratamiento IQR usado por `notebooks/refactor/2.0_preprocesamiento_jobpath.ipynb`.
- [`ScriptsCsv/Transformacion/`](./ScriptsCsv/Transformacion/): codificación,
  escalado, split por persona y diagnóstico PCA usados por
  `notebooks/refactor/3.0_transformacion.ipynb`, `4.0_PCA.ipynb` y
  `4.1_PCA_completo.ipynb`.
- [`ScriptsCsv/EDA/`](./ScriptsCsv/EDA/): pipeline de análisis exploratorio y
  generación de figuras usado por `notebooks/refactor/5.0_EDA_jobpath.ipynb`.
- [`ScriptsCsv/Modelado/`](./ScriptsCsv/Modelado/): preparación de matrices sin
  fuga ni colinealidad redundante, validación cruzada agrupada por persona
  (`StratifiedGroupKFold`) y evaluación comparativa A vs. B usados por
  `notebooks/refactor/6.0_modelado_fase4_jobpath.ipynb`.
