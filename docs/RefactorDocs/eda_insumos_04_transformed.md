# Insumos de `data/04_transformed` usados en el EDA

**Proyecto:** JobPath · EDA fase 2 (Data Understanding)  
**Cuaderno:** `notebooks/refactor/5.0_EDA_jobpath.ipynb`  
**Lógica:** `scripts/ScriptsCsv/EDA/`

## 1. Resumen

El EDA no entrena modelos ni repite la transformación de la fase 3. De
`data/04_transformed` usa:

- los `y_train.csv` / `y_test.csv` de ambas versiones para verificar el split
  y describir el target;
- la cabecera de `X_train.csv` de la versión A y dos columnas concretas para
  auditar la fuga;
- la huella SHA-256 de los `transformers.joblib`, sin cargarlos.

No carga la matriz `X` completa ni el `X_test.csv`.

## 2. Artefactos y uso

| Artefacto | Uso | Motivo |
|---|---|---|
| `con_outliers/train/y_train.csv` | Completo | Verificar el split reconstruido y calcular el target en train |
| `con_outliers/test/y_test.csv` | Completo | Verificar el split y comparar prevalencia train/test |
| `sin_outliers/train/y_train.csv` | Completo | Comprobar que el target es idéntico entre A y B |
| `sin_outliers/test/y_test.csv` | Completo | Igual que el anterior |
| `con_outliers/train/X_train.csv` | Cabecera + `veces_ese_oficio_bin` + `veces_ese_oficio_rob` | Detectar y medir la fuga del target |
| `con_outliers/test/X_test.csv` | No se usa | Evitar decisiones contaminadas por test |
| `sin_outliers/**/X_*.csv` | No se usan | La comparación A/B se hace sobre el CSV limpio |
| `transformers/*/transformers.joblib` | Solo SHA-256 | Verificar que la fase 3 quedó intacta |

## 3. Por qué la versión A es la referencia

- **A (`con_outliers`)** conserva la distribución original, incluidas las colas.
  Es la base de la descripción del universo y del análisis del target.
- **B (`sin_outliers`)** solo se usa para medir el efecto de la winsorización
  (figuras G09 y G25) y para comprobar que el target no cambia.
- El target es idéntico en A y B: los `y_*.csv` tienen el mismo SHA-256.

## 4. Qué es `X`

- Una fila por **experiencia laboral con oficio clasificado**.
- **2.839 columnas** numéricas (2.828 `int64`, 11 `float64`):
  - 2.821 dummies `occupation_code_*` (one-hot del oficio);
  - 18 columnas de duración, competencias, calendario, nivel educativo,
    banderas y bins.
- **No contiene `resume_id`**: la persona no entra como feature.
- Dimensiones: train 278.987 filas; test 69.276 filas.
- A y B comparten las mismas 2.839 columnas y las mismas filas.

Las 18 columnas que no son dummies de oficio son:

`start_ord_rob`, `end_ord_rob`, `dur_q_rob`, `n_skills_essential_rob`,
`n_skills_competence_rob`, `n_skills_knowledge_rob`, `n_skills_sin_tipo_rob`,
`veces_ese_oficio_rob`, `start_year_rob`, `job_order_rob`, `univ_ord_mm`,
`es_vigente`, `dur_q_bin`, `n_skills_essential_bin`, `veces_ese_oficio_bin`,
`tiene_skills`, `tiene_knowledge`, `tiene_sin_tipo`.

## 5. Qué es `Y`

- Una sola columna: `reincide`, binaria 0/1.
- `1` si la persona ya había tenido ese mismo oficio (`veces_ese_oficio > 1`);
  `0` en caso contrario.
- Train: 85.147 positivos de 278.987 (30,52 %).
- Test: 21.103 positivos de 69.276 (30,46 %).
- En el EDA se renombra solo en RAM a `is_repeated_occupation`; los archivos
  no se modifican.

## 6. Alineación y fuga

- La fila *i* de `X` corresponde a la fila *i* de `y`.
- El split se reconstruye desde el CSV limpio con semilla 42 y se verifica
  contra los `y_*.csv`: coincidencia del 100 % y 0 personas solapadas.
- `X` contiene `veces_ese_oficio_rob` y `veces_ese_oficio_bin`, que reproducen
  el target en el 100 % de train. Son fuga y deben excluirse en la fase 4.

## 7. Qué no se usó y por qué

- **`X` completo:** 1.539 MB en train y 382 MB en test; 2.839 columnas. El EDA
  es descriptivo y no necesita la matriz completa.
- **`X_test.csv`:** no se lee para no contaminar decisiones con test.
- **`transformers.joblib`:** no se carga; solo se verifica su huella. Reajustar
  o reutilizar transformadores es responsabilidad de la fase 3.

## 8. Consecuencias para la fase 4

1. Excluir `veces_ese_oficio`, `veces_ese_oficio_bin` y `veces_ese_oficio_rob`
   de `X`.
2. No usar `n_returns` ni `n_nonadjacent_returns` como features.
3. Mantener `resume_id` fuera de `X`; usarlo solo para agrupar.
4. Elegir métricas sensibles al desbalance (PR-AUC, recall, F1 de la clase 1).
5. Documentar si se modela con A o con B y justificar la decisión.

## 9. Dónde se ve en el cuaderno

| Sección del cuaderno | Celda | Uso de `data/04_transformed` |
|---|---|---|
| 2. Carga e inventario | 7 | `y_train` / `y_test` de A y B |
| 9. Split por persona | 52 | `y_train` / `y_test` de A para verificar |
| 10. Target | 55 | `y_train` de A y balance A/B |
| 11. Fuga | 61 | Cabecera y dos columnas de `X_train` de A |
| 14. Validación | 73 | SHA-256 de los 8 archivos X/y y los 2 `.joblib` |
