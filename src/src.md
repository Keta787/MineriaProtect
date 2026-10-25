# Guía técnica de `src`

Este documento explica qué realiza cada script de `src/`, qué archivos utiliza,
qué produce y cómo se relaciona con los notebooks. La carpeta `src/` contiene
la lógica reutilizable del proyecto; los notebooks presentan la explicación,
las decisiones metodológicas y la evidencia de ejecución.

## 1. Principio de organización

El código está separado por responsabilidad:

```text
src/
├── limpieza/        Preparación, integración y validación de CSV
├── filtro/          Filtros e indicadores reutilizables para análisis
└── transformacion/ Conversión del dataset enriquecido a una matriz numérica X
```

El flujo canónico vigente es:

```text
data/01_raw/
    │
    └── limpiar_datos.py
            ↓
data/02_interim/
    │
    └── integrar_empleos.py
            ↓
data/03_processed/empleos.csv
    │
    ├── generar_competencias.py
    │       ↓
    │   competencias_por_oficio.csv
    │
    └── unificar_competencias_empleos.py
            ↓
        empleos_con_competencias.csv
            │
            └── limpiar_empleos_con_competencias.py
                    ↓
                empleos_con_competencias_limpio.csv
                    │
                    └── dividir_competencias_por_outliers.py
                            ↓
                        empleos_con_competencias_limpio_sin_outliers.csv
                            │
                            ├── notebooks/4.0_transformacion.ipynb
                            └── notebooks/4.1_transformacion_sin_outliers.ipynb
```

Los archivos originales no se editan. Cada script lee una entrada y escribe un
derivado nuevo, conservando el grano del dataset: **una fila representa una
experiencia laboral**.

## 2. Relación entre notebooks y código

| Notebook | Propósito | Código principal relacionado |
|---|---|---|
| `notebooks/1.0_comprension_negocio.md` | Acta, objetivo, preguntas, alcance y fuentes | Define el problema que implementan los scripts |
| `notebooks/2.0_EDA_y_seleccion.ipynb` | Selección de fuentes, carga defensiva, EDA, calidad y consulta de ESCO | `limpiar_datos.py`, `integrar_empleos.py`, `generar_competencias.py` |
| `notebooks/3.0_preprocesamiento.ipynb` | Limpieza, banderas, validaciones y comparación de outliers | `limpiar_empleos.py`, `limpiar_empleos_con_competencias.py`, `dividir_competencias_por_outliers.py` |
| `notebooks/4.0_transformacion.ipynb` | Transformación numérica conservando la cola larga | `transformacion/transformacion.py`, `transformacion/diagnostico.py` |
| `notebooks/4.1_transformacion_sin_outliers.ipynb` | La misma transformación sobre la variante sin outliers | `transformacion/transformacion.py`, `transformacion/diagnostico.py` |

Los notebooks son la **narrativa y evidencia**. La lógica que debe poder
reutilizarse está en `src/`. Por eso los notebooks 4.0 y 4.1 importan el mismo
módulo de transformación y cambian solamente la versión del CSV.

## 3. Módulo `src/limpieza/`

### `limpiar_datos.py`

**Responsabilidad:** limpiar las fuentes originales antes de integrarlas.

- Lee las particiones `train`, `test` y `val` de JobHop v2.
- Lee los archivos de ESCO y SKILLS.
- Conserva códigos como texto para no perder ceros iniciales.
- Elimina duplicados y columnas completamente nulas según las reglas definidas.
- Genera las versiones limpias en `data/02_interim/`.
- Registra los cambios en `logs/`.

**Entrada:** `data/01_raw/`.

**Salida:** `data/02_interim/`.

**Notebook relacionado:** `2.0_EDA_y_seleccion.ipynb`.

### `integrar_empleos.py`

**Responsabilidad:** construir el integrado base de experiencias laborales.

- Une las particiones limpias `test` y `val`.
- Excluye `train` del integrado de estudio.
- Cruza `matched_code` con ocupaciones ESCO.
- Clasifica cada experiencia como `ok`, `rescatado` o `unknown`.
- Añade ocupación, grupo ISCO y contadores de competencias.
- Conserva una fila por experiencia.

**Entrada:** fuentes limpias de `data/02_interim/`.

**Salida:** `data/03_processed/empleos.csv`.

**Notebook relacionado:** `2.0_EDA_y_seleccion.ipynb`.

### `generar_competencias.py`

**Responsabilidad:** construir el perfil normalizado de competencias por
ocupación.

- Filtra las relaciones ESCO `essential`.
- Resuelve el vínculo entre `occupationUri` y `occupation_code`.
- Agrupa los nombres en `skills`, `knowledge` y `sin_tipo`.
- Conserva una fila por `occupation_code`.
- Contrasta los cuatro contadores contra el dataset disponible:
  `empleos.csv` o `empleos_con_competencias.csv`.

**Entrada:** fuentes ESCO limpias y un dataset integrado para el contraste.

**Salida:** `data/03_processed/competencias_por_oficio.csv`.

**Notebook relacionado:** `2.0_EDA_y_seleccion.ipynb`.

Esta tabla describe las competencias exigidas por una ocupación. No demuestra
qué competencias posee individualmente una persona.

### `unificar_competencias_empleos.py`

**Responsabilidad:** crear la entrada canónica enriquecida.

- Une los perfiles de `competencias_por_oficio.csv` por `occupation_code`.
- Usa una unión `left` y valida que sea `many_to_one`.
- Conserva las filas del dataset de empleos.
- Añade las columnas `skills`, `knowledge` y `sin_tipo`.
- No modifica el CSV original.

**Entrada:** `empleos.csv` y `competencias_por_oficio.csv`.

**Salida principal:** `empleos_con_competencias.csv`.

También reconoce el archivo histórico `empleos .csv` con espacio si existe y
puede producir `empleos_limpio_con_competencias.csv` como derivado de
compatibilidad. Este último no es la entrada canónica actual.

**Notebook relacionado:** el enriquecimiento se explica en `2.0` y se utiliza
como entrada en `3.0` y `4.x`.

### `limpiar_empleos.py`

**Responsabilidad:** flujo histórico de limpieza del integrado sin listas de
competencias.

Implementa siete fases:

1. Diagnóstico.
2. Duplicados.
3. Normalización de categorías.
4. Tratamiento explícito de faltantes y banderas.
5. Auditoría de duración y fechas.
6. Validación mediante `assert`.
7. Exportación y bitácora.

**Entrada:** `data/03_processed/empleos.csv`.

**Salida histórica:** `data/03_processed/empleos_limpio.csv`.

**Notebook relacionado:** `3.0_preprocesamiento.ipynb`.

Se conserva para trazabilidad y comparación. Para el flujo vigente con ESCO se
utiliza `limpiar_empleos_con_competencias.py`.

### `limpiar_empleos_con_competencias.py`

**Responsabilidad:** limpiar y validar la entrada canónica enriquecida.

- Lee `empleos_con_competencias.csv` como texto.
- Valida el esquema y la llave natural.
- Normaliza `university_level`.
- Genera `es_unknown_ocupacion`, `es_rescatado` y `es_vigente`.
- Comprueba que los contadores de competencias cierren.
- Comprueba que las listas coincidan con sus contadores.
- Conserva vacíos los contadores de experiencias no clasificadas.
- Escribe una bitácora de ejecución.

**Entrada:** `data/03_processed/empleos_con_competencias.csv`.

**Salida:** `data/03_processed/empleos_con_competencias_limpio.csv`.

**Notebook relacionado:** `3.0_preprocesamiento.ipynb`; sus reglas son la base
de la preparación que consumen los notebooks 4.0 y 4.1.

### `dividir_competencias_por_outliers.py`

**Responsabilidad:** generar una segunda variante del dataset enriquecido para
comparar el efecto de la cola larga de duración.

- Lee el dataset enriquecido limpio.
- Calcula duración trimestral inclusiva.
- Aplica la regla de Tukey/IQR.
- Elimina únicamente las filas consideradas outliers.
- Conserva exactamente las mismas columnas y el mismo significado.
- Registra cantidades, límites y personas afectadas.

**Entrada:** `empleos_con_competencias_limpio.csv`.

**Salida:** `empleos_con_competencias_limpio_sin_outliers.csv`.

**Notebook relacionado:** `3.0_preprocesamiento.ipynb` y
`4.1_transformacion_sin_outliers.ipynb`.

### `dividir_por_outliers.py`

**Responsabilidad:** flujo histórico de comparación de outliers sobre
`empleos_limpio.csv`.

No es el script canónico para el dataset enriquecido. Se conserva para
reproducir la fase anterior y comparar las reglas históricas.

## 4. Módulo `src/filtro/`

### `filtros.py`

Contiene filtros reutilizables que reciben un `DataFrame` y devuelven una copia:

- nivel educativo;
- grupo ISCO;
- ocupación;
- periodo;
- experiencias vigentes;
- experiencias sin área ISCO;
- resumen de un segmento.

El módulo no modifica archivos ni imputa valores. Acepta banderas leídas como
texto (`"True"`/`"False"`) o como booleanos.

**Uso esperado:** exploración y análisis sobre
`empleos_con_competencias_limpio.csv`.

**Notebook relacionado:** principalmente `2.0` y `3.0`. Sus funciones también
son insumos para el análisis posterior, pero todavía no construyen `Sₚ`.

### `indicadores.py`

Contiene indicadores calculados sobre un `DataFrame`:

- duración trimestral;
- distribución y límites IQR;
- medianas por grupo ISCO y nivel educativo;
- tablas de frecuencia y cruces;
- transiciones consecutivas;
- brechas entre empleos;
- solapamientos;
- resumen de banderas;
- carga y expansión de competencias ESCO;
- perfil de competencias por persona;
- similitud Jaccard entre contratos consecutivos.

Las funciones `cargar_competencias()` y `cargar_relaciones()` realizan lectura
de archivos. El resto trabaja sobre datos recibidos como argumento.

**Fuentes de competencias:**

- `competencias_por_oficio.csv` es la tabla normalizada preferida.
- `data/02_interim/SKILLS/` se conserva como fuente de contraste.

**Notebook relacionado:** `2.0` y `3.0`. Los indicadores de transiciones y
Jaccard son herramientas disponibles, no una ejecución de minería ya realizada.

## 5. Módulo `src/transformacion/`

### `transformacion.py`

**Responsabilidad:** convertir un dataset limpio enriquecido en una matriz
numérica `X` para preparación de IA.

El módulo realiza, en orden:

1. Carga una de las dos versiones enriquecidas.
2. Recupera códigos de filas `rescatado`.
3. Convierte fechas trimestrales a ordinales.
4. Calcula duración.
5. Convierte educación a escala ordinal.
6. Deriva indicadores de presencia de perfiles ESCO:
   `tiene_skills`, `tiene_knowledge` y `tiene_sin_tipo`.
7. Excluye filas sin datos de competencias, informando el costo.
8. Deriva `reincide`.
9. Codifica variables categóricas.
10. Escala las variables numéricas por grupos.
11. Ensambla y valida la matriz `X`.

**Entradas:**

- `empleos_con_competencias_limpio.csv`;
- `empleos_con_competencias_limpio_sin_outliers.csv`.

**Resultados verificados con la semilla documentada:**

- versión con outliers: `X` de 2.328 columnas;
- versión sin outliers: `X` de 2.329 columnas;
- sin nulos y sin columnas no numéricas.

La `X` se usa como representación numérica de preparación. Este módulo no
entrena modelos y no construye secuencias por persona.

**Notebooks relacionados:** `4.0_transformacion.ipynb` y
`4.1_transformacion_sin_outliers.ipynb`.

### `diagnostico.py`

**Responsabilidad:** producir las auditorías que justifican las decisiones de
transformación.

Incluye:

- comprobaciones del cruce con ESCO;
- revisión de `isco_level`;
- segmentación exploratoria por cuantiles;
- tamaño del bloque one-hot;
- tabla de Tukey;
- comparación de escaladores;
- aporte de variables a la distancia euclídea;
- pareja ilustrativa de experiencias;
- auditoría PCA.

No crea una matriz final distinta ni entrena un modelo. Devuelve tablas y
resultados para que los notebooks los presenten.

**Notebooks relacionados:** `4.0_transformacion.ipynb` y
`4.1_transformacion_sin_outliers.ipynb`.

## 6. Orden recomendado de ejecución

Desde la raíz del proyecto:

```powershell
python -m pip install -r requirements.txt

python src\limpieza\limpiar_datos.py
python src\limpieza\integrar_empleos.py
python src\limpieza\generar_competencias.py
python src\limpieza\unificar_competencias_empleos.py
python src\limpieza\limpiar_empleos_con_competencias.py
python src\limpieza\dividir_competencias_por_outliers.py
```

Después se pueden ejecutar los notebooks:

```powershell
python -m jupyter nbconvert --to notebook --execute --inplace `
    notebooks\4.0_transformacion.ipynb `
    notebooks\4.1_transformacion_sin_outliers.ipynb
```

Los scripts resuelven la raíz del proyecto buscando la carpeta `data/`, por lo
que no dependen de una ruta absoluta específica de una máquina.

## 7. Convenciones de calidad

- Leer códigos con `dtype=str`.
- No modificar archivos de `data/01_raw/`.
- No sobrescribir entradas para producir derivados.
- Mantener una fila por experiencia laboral.
- Usar `assert` para invariantes verificables.
- Registrar ejecuciones y conteos en `logs/`.
- Tratar una celda vacía como ausencia, no como cero.
- No interpretar las competencias ESCO como habilidades aprendidas
  individualmente.
- Mantener listas de competencias fuera de la matriz numérica; usar indicadores
  derivados o representaciones explícitas justificadas.

## 8. Alcance actual

El código de `src/` deja preparada y verificada la información para la fase de
IA:

- fuentes limpias;
- integración JobHop + ESCO;
- perfiles de competencias;
- dataset enriquecido limpio;
- variante con/sin outliers;
- indicadores y diagnósticos;
- matriz numérica `X`.

Todavía no se implementa en esta fase:

- construcción del dataset de secuencias `Sₚ`;
- decisión definitiva sobre `unknown`;
- regla final para pluriempleo;
- selección de algoritmo de minería;
- entrenamiento;
- evaluación o interpretación de patrones.

