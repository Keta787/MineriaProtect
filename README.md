# README ACTUALIZADO · Cambios aplicados al proyecto

Documento de seguimiento de los cambios aplicados sobre el repositorio (enero de 2026 - sesión 3/curso). Aquí se registra el estado del proyecto: **qué cambió, por qué y cómo quedó la estructura**.

## 1. Causa raíz: rutas del layout antiguo

Todos los scripts y cuadernos apuntaban a las carpetas del **layout viejo**, que ya no existían en disco → se generaban múltiples fallas al ejecutar (`FileNotFoundError` y referencias rotas).

| Layout viejo (README/scripts anteriores) | Layout nuevo (este repositorio) |
|---|---|
| `data/original/` | `data/01_raw/` |
| `data/limpia/` | `data/02_interim/` |
| `data/cruce/` | `data/03_processed/` |
| `script/` | `src/` |
| `libros/` | `notebooks/` |
| `md/` (bitácora/docs) | raíz + `contexto_*.md` |

## 2. Archivos corregidos (rutas y referencias)

- `src/limpieza/limpiar_empleos.py` → origen/destino en `data/03_processed/`.
- `src/limpieza/limpiar_datos.py` → `data/01_raw/` → `data/02_interim/`.
- `src/filtro/filtros.py` y `src/filtro/indicadores.py` → docstrings con rutas nuevas.
- `notebooks/` reorganizado a tres unidades alineadas con las sesiones 1–3: `1.0_comprension_negocio.md`, `2.0_EDA_y_seleccion.ipynb` y `3.0_preprocesamiento.ipynb` (los cuadernos viejos `Lectura.ipynb`, `Diagnostico_Limpieza_Empleos.ipynb` y `presentacion.ipynb` fueron eliminados; sus rutas, `sys.path` y `RUTA` quedaron corregidos y ejecutados en verde).
- `.gitignore` → reglas de tamaño: se versionan `data/01_raw/` y `data/02_interim/` (todos los archivos <50 MB); se descartan los CSV de `data/03_processed/` (156–184 MB, no caben en GitHub) y `logs/`.

## 3. Pipelines re-ejecutados (validación en verde)

### `limpiar_datos.py` — fuentes → `data/02_interim/`

| Archivo | Original | Limpio | Observación |
|---|---|---|---|
| `JobHop_v2_train.parquet` | 1.594.827 | 1.506.445 | −58.312 sin `start_date`; −30.070 duplicados |
| `ESCO/occupations_en.csv` | 3.043 | 3.039 | −4 por `code` duplicado |
| `ESCO/ISCOGroups_en.csv` | 619 | 619 | −1 columna 100% nula |
| `ESCO/occupationSkillRelations_en.csv` | 126.051 | 126.051 | 59 con `skillType` nulo conservados |
| `ESCO/skills_en.csv` | 13.960 | 13.939 | −21 por `conceptUri` duplicado |
| `ESCO/greenShareOcc_en.csv` | 3.590 | 3.590 | `greenShare` → float |

### `limpiar_empleos.py` — integrado → `empleos_limpio.csv`

7 fases ejecutadas sin errores: 1.506.445 → **1.506.434** filas (solo −11 por fechas futuras > 2026); 284.247 personas; tabla de umbrales (6 criterios) ✅; bitácora persistida en `logs/bitacora_limpieza_empleos.csv`.

### `dividir_por_outliers.py` — nuevo script

Divide el limpio según la **cola larga** de duración (mismo criterio de la fase 5: IQR de Tukey sobre `dur_Q`, límite superior 24,5 → outliers = `dur_Q ≥ 25`). Bitácora en `logs/bitacora_dividir_outliers.csv`.

## 4. CSV señalados para los cruces

Solo los CSV de `data/03_processed/` participan en los cruces (formato acordado del proyecto):

| CSV | Rol en el cruce | Filas × Columnas | Personas |
|---|---|---|---|
| `empleos.csv` | Integrado original JobHop + ESCO (**inmutable**) | 1.506.445 × 11 | 284.247 |
| `empleos_limpio.csv` | Limpio **CON** cola larga (outliers incluidos) | 1.506.434 × 14 | 284.247 |
| `empleos_limpio_sin_outliers.csv` | Limpio **SIN** cola larga (`dur_Q` máx. 24) | 1.364.853 × 14 | 277.052 |

Los dos limpios se **cruzan entre sí** para comparar descriptivos (duración, transiciones, crosstabs) y validar el impacto de la cola larga antes de elegir la técnica de minería. `empleos.csv` solo es origen del pipeline.

### Validación cruzada con/sin outliers

| Métrica | Con outliers (`empleos_limpio.csv`) | Sin outliers (`empleos_limpio_sin_outliers.csv`) |
|---|---|---|
| Filas | 1.506.434 | 1.364.853 |
| Personas | 284.247 | 277.052 |
| `dur_Q` min | 2 | 2 |
| `dur_Q` p99,9 | 125 | 24 |
| `dur_Q` máx | 160 | 24 |
| Nulos sin bandera | 0 | 0 |

## 5. Estado de los archivos en disco y en GitHub

- En GitHub se versionan **completos** `data/01_raw/` (parquet + 5 ESCO CSV) y `data/02_interim/` (parquet limpio + 5 ESCO `*_limpio.csv`), además de `src/`, `notebooks/` y este documento.
- `data/03_processed/` NO se versiona su contenido: los 3 CSV pesan 156–184 MB (superan el límite duro de GitHub de 100 MB por archivo y la regla del proyecto de 50 MB). Solo se sube la estructura de la carpeta con un `.gitkeep`.
- En disco: `data/01_raw/` (8,8 MB parquet + 5 ESCO CSV), `data/02_interim/` (parquet limpio + 5 ESCO `*_limpio.csv`), `data/03_processed/` (`empleos.csv` 156,8 MB, `empleos_limpio.csv` 183,8 MB, `empleos_limpio_sin_outliers.csv` 166,2 MB).
- `logs/`: bitácoras de ejecución (solo en disco, no se versionan).

## 6. Siguientes pasos

1. Convertir experiencias en secuencias temporales por persona (`src/filtro/`).
2. Cruzar descriptivos con/sin cola larga y **seleccionar la técnica de minería**.
3. Evaluar, interpretar y documentar los patrones.
4. Actualizar la bitácora del proyecto (`logs/bitacora_*.csv`) con estos cambios.