# IDEA-HYB-02 — Pack Automatizado de Verificación en GeoGebra y Auditoría SHA-256

> **Temática:** Verificación Dual (Python + GeoGebra) · **Prioridad:** P1 · **Presentación base:** `Ambas presentaciones HTML` (Diapositivas 14–15 de AMBOS HTML (Verificación en GeoGebra + Reto Python vs. NumPy/SciPy))

---

## 1. Propósito y Finalidad Analítica

Conectar la pedagogía de clase con ingeniería reproducible de minería de datos: generar automáticamente scripts listos para copiar y pegar en GeoGebra Classic para los 5 casos canónicos de n pequeño, validar todo cálculo hecho a mano contra NumPy/SciPy (< 1e-10), certificar con huellas SHA-256 completas de 64 caracteres que los 19 insumos de `data/` permanecieron 100 % intactos y ejecutar una auditoría semántica bilingüe (EN + ES) sobre el entregable.

## 2. Archivos de `data/` Utilizados (Solo Lectura)

- Tablas canónicas de nodos de `IDEA-RL-01`, `IDEA-RL-02` (10 centroides ISCO), `IDEA-RL-04` (2000–2019 centrado sobre empleos cerrados), `IDEA-LG-01` (4 hitos de supervivencia) e `IDEA-LG-02` (PCA en vivo `k = 1, 3, 5, 8`)
- 19 archivos de solo lectura auditados en `01_raw/`, `02_interim/`, `03_processed/`, `04_transformed/` y `split_map_resume_id.csv` (13 con SHA-256 completo + 6 archivos de 1.4–8.4 GB con SHA-256 muestreado 24 MiB + metadatos, siempre en digest íntegro de 64 caracteres hex)

## 3. Formulación Matemática Aplicada

$$\text{Error Relativo MCO} = \frac{\max(|a_0 - \hat{a}_0^{\text{np}}|, |a_1 - \hat{a}_1^{\text{np}}|)}{\max(1, |a_0|, |a_1|)} = 2.29\times 10^{-12} < 10^{-10}, \qquad \max_x |P_n(x) - P_n^{\text{scipy}}(x)| = 5.05\times 10^{-15}$$

## 4. Cómo se Hizo (Metodología Paso a Paso)

1. Se generaron automáticamente 5 archivos `.txt` con comandos de GeoGebra en inglés (compatibles en cualquier idioma: `FitLine`, `CorrelationCoefficient`, `RSquare`, `Polynomial` y expresiones explícitas `L0(x)..L3(x)`), incorporando la forma monomial expandida en `LG-01`/`LG-02` y la advertencia `MR-06` en `RL-02`.
2. Se validó la sintaxis de cada archivo `.txt` mediante expresiones regulares (`validate_geogebra_scripts`) y se exportó el índice consolidado `geogebra_verification_index.md`.
3. Se verificaron los 39 modelos MCO frente a `numpy.polyfit(x, y, 1)` (error relativo máx. `2.29e-12 < 1e-10`), las 8 pruebas de invarianza afín (`7.22e-14`) y los diagnósticos de Lagrange frente a `scipy.interpolate` (`5.05e-15`).
4. Se registraron huellas SHA-256 íntegras de 64 caracteres hexadecimales (junto con `size_bytes` y `hash_mode`) antes y después de la ejecución, comprobando `19/19` archivos intactos.
5. Se ejecutó la auditoría semántica bilingüe (`MR-07/MR-08` en inglés y español) sobre notebooks, bitácoras y todos los Markdown del entregable (`0` violaciones), validada por la suite automatizada en `tests/metodos_numericos/` (`test_presentation_server_load_fixture`, `test_presentation_practice_loc_fixture`, `test_low_r2_verdict_and_guards`, `test_affine_scaling_invariance`, `test_presentation_cpu_temperature_fixture`, `test_presentation_practice_fixture`, `test_distinct_node_and_monotonic_inverse_guards`, `test_chebyshev_and_piecewise_quadratic`, `test_ols_polyfit_equivalence_and_rejections`, `test_rl04_extrapolation_failure_and_raw_parity`, `test_rl05_outlier_audit_and_affine_invariance`, `test_lg01_runge_explosion_and_chebyshev_mitigation`, `test_lg02_pca_forward_inverse_and_plateau`, `test_hyb01_four_by_four_rubric`, `test_hyb02_geogebra_figures_sha256_and_wording` y verificaciones extendidas de entregable).

**Módulos de Python que lo implementan:**

- `scripts/ScriptsCsv/MetodosNumericos/geogebra.py` (`export_hyb02_geogebra_pack`)
- `scripts/ScriptsCsv/MetodosNumericos/validation.py` (`snapshot_read_only_inputs`, `verify_read_only_inputs`, `validate_geogebra_scripts`, `audit_wording_compliance`)
- `tests/metodos_numericos/` (`test_ols_engine.py`, `test_lagrange_engine.py`, `test_pipeline_integration.py` — suite completa automatizada)

## 5. Resultados Empíricos Verificados

### Tabla: `ols_summary_all_ideas.csv`

| idea_id | x_var | y_var | n | a0 | a1 | r2 | s_yx | quality_verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IDEA-RL-01 | job_order (1..10) | mean_skills | 10 | 22.5160 | 0.2250 | 0.9955 | 0.0486 | Ajuste Lineal Fuerte (R² ≥ 0.70) |
| IDEA-RL-01 (cohort >=10) | job_order (1..10) | mean_skills | 10 | 22.9122 | 0.2026 | 0.9529 | 0.1446 | Ajuste Lineal Fuerte (R² ≥ 0.70) |
| IDEA-RL-01 | job_order (1..10) | reincide_rate | 10 | 0.2206 | 0.0213 | 0.9625 | 0.0135 | Ajuste Lineal Fuerte (R² ≥ 0.70) |
| IDEA-RL-01 (cohort >=10) | job_order (1..10) | reincide_rate | 10 | 0.3806 | 0.0072 | 0.4475 | 0.0258 | Ajuste Lineal Moderado (0.30 ≤ R² < 0.70) |
| IDEA-RL-01 | job_order (1..10) | mean_dur_q | 10 | 13.2330 | -0.8565 | 0.9233 | 0.7928 | Ajuste Lineal Fuerte (R² ≥ 0.70) |
| IDEA-RL-01 (cohort >=10) | job_order (1..10) | mean_dur_q | 10 | 10.2132 | -0.5180 | 0.8661 | 0.6540 | Ajuste Lineal Fuerte (R² ≥ 0.70) |
| IDEA-RL-01 | job_order (1..10) | mean_green | 10 | 0.0236 | -0.0002 | 0.7877 | 0.0004 | Ajuste Lineal Fuerte (R² ≥ 0.70) |
| IDEA-RL-01 (cohort >=10) | job_order (1..10) | mean_green | 10 | 0.0192 | 0.0002 | 0.7310 | 0.0004 | Ajuste Lineal Fuerte (R² ≥ 0.70) |
| IDEA-RL-02 | n_ess_comp | n_essential | 3,039 | 3.3465 | 1.1227 | 0.8643 | 4.4184 | Ajuste Lineal Fuerte (R² ≥ 0.70) |
| IDEA-RL-02 | n_competence | n_total_rel | 3,039 | 4.8359 | 1.2156 | 0.7319 | 10.4702 | Ajuste Lineal Fuerte (R² ≥ 0.70) |
| IDEA-RL-02 | n_total_rel | n_cross_sector | 3,039 | -0.7983 | 0.5786 | 0.5670 | 10.2229 | Ajuste Lineal Moderado (0.30 ≤ R² < 0.70) |
| IDEA-RL-02 | n_sector_spec | n_total_rel | 3,039 | 24.5534 | 0.9925 | 0.4069 | 15.5728 | Ajuste Lineal Moderado (0.30 ≤ R² < 0.70) |
| IDEA-RL-02 | n_essential | n_optional | 3,039 | 15.9592 | 0.1472 | 0.0140 | 14.8176 | Modelo Lineal Débil / Rechazado (R² < 0.30) |
| IDEA-RL-02 | n_essential | greenShare | 3,039 | 0.0435 | -5.206e-05 | 4.474e-05 | 0.0933 | Modelo Lineal Débil / Rechazado (R² < 0.30) |
| IDEA-RL-02 | n_knowledge | greenShare | 3,039 | 0.0360 | 0.0006 | 0.0043 | 0.0931 | Modelo Lineal Débil / Rechazado (R² < 0.30) |
| IDEA-RL-02 (ISCO-10 centroids) | mean_total_rel | mean_cross_sector | 10 | 3.4481 | 0.4330 | 0.2800 | 5.4310 | Modelo Lineal Débil / Rechazado (R² < 0.30) |
| IDEA-RL-04 | start_year | mean_skills | 20 | -171.0956 | 0.0967 | 0.7475 | 0.3417 | Ajuste Lineal Fuerte (R² ≥ 0.70) |
| IDEA-RL-04 | start_year | mean_skills | 24 | 225.9336 | -0.1011 | 0.0826 | 2.4348 | Modelo Lineal Débil / Rechazado (R² < 0.30) |
| IDEA-RL-04 | start_year - 2000 | mean_skills | 20 | 22.3672 | 0.0967 | 0.7475 | 0.3417 | Ajuste Lineal Fuerte (R² ≥ 0.70) |
| IDEA-RL-04 | start_year | mean_dur_q | 20 | 1,601.64 | -0.7926 | 0.9729 | 0.8044 | Ajuste Lineal Fuerte (R² ≥ 0.70) |

*Se muestran las primeras 20 de 39 filas; consulta el archivo CSV completo en `tables/`.*

### Tabla: `sha256_input_integrity.csv`

| file_name | size_bytes | hash_mode | sha256_before | sha256_after | intact |
| --- | --- | --- | --- | --- | --- |
| JobHop_v2_train.csv | 66,773,042 | SHA-256 completo (64 hex) | 68b7d3686c7580a059a8731d6762f09b466fbf1a64c9e65b8dea34d547470e16 | 68b7d3686c7580a059a8731d6762f09b466fbf1a64c9e65b8dea34d547470e16 | Sí |
| JobHop_v2_test.csv | 8,337,633 | SHA-256 completo (64 hex) | ed28c2671e00c2127271df2f817ea419863a70a4c762364502573dff6d967f97 | ed28c2671e00c2127271df2f817ea419863a70a4c762364502573dff6d967f97 | Sí |
| JobHop_v2_val.csv | 8,353,320 | SHA-256 completo (64 hex) | c31236fb3639b411327237f3197764284e430fb43d289fd3d89093725f173886 | c31236fb3639b411327237f3197764284e430fb43d289fd3d89093725f173886 | Sí |
| greenShareOcc_en_limpio.csv | 452,319 | SHA-256 completo (64 hex) | 3cc4c43291437fc8b90f5774b295002c06818e38d62cea6065d10def86a53234 | 3cc4c43291437fc8b90f5774b295002c06818e38d62cea6065d10def86a53234 | Sí |
| ISCOGroups_en_limpio.csv | 974,377 | SHA-256 completo (64 hex) | a81ef1362babc9249e6fb3889cabc49f6ea028ac07a4c590febc5bd389d550e8 | a81ef1362babc9249e6fb3889cabc49f6ea028ac07a4c590febc5bd389d550e8 | Sí |
| occupations_en_limpio.csv | 3,075,709 | SHA-256 completo (64 hex) | 1a6d59c8ae1aed23ed18714a785fef33d634620c5f4bb50d83ba793b1b4e333b | 1a6d59c8ae1aed23ed18714a785fef33d634620c5f4bb50d83ba793b1b4e333b | Sí |
| occupationSkillRelations_en_limpio.csv | 27,986,628 | SHA-256 completo (64 hex) | e1a46511f0ef4d505f106f1d41f528ef76d289f93e59d4d0cbaac38986102c44 | e1a46511f0ef4d505f106f1d41f528ef76d289f93e59d4d0cbaac38986102c44 | Sí |
| skills_en_limpio.csv | 9,373,339 | SHA-256 completo (64 hex) | 99f0ed64f643a82d5916f19e9da2a87710cc50a45fb414b5e8621ba767109668 | 99f0ed64f643a82d5916f19e9da2a87710cc50a45fb414b5e8621ba767109668 | Sí |
| empleos_limpio.csv | 57,423,894 | SHA-256 completo (64 hex) | 4ee5b956e25e8e7a4c095175bd11dbd3b36ef64ed67829e33335fe9e14cb2c74 | 4ee5b956e25e8e7a4c095175bd11dbd3b36ef64ed67829e33335fe9e14cb2c74 | Sí |
| empleos_limpio_sin_outliers .csv | 51,931,804 | SHA-256 completo (64 hex) | 87d9350e82f27646574b2628e2493773f4af80e2be55e0de500877cd17309dfb | 87d9350e82f27646574b2628e2493773f4af80e2be55e0de500877cd17309dfb | Sí |
| empleos_unificado_limpio.csv | 1,427,132,984 | SHA-256 24 MiB + meta (64 hex) | f51aaadffdff47ab653c7cbcd31b7c1ee252c041e1236dbb9405c5ea2bb02107 | f51aaadffdff47ab653c7cbcd31b7c1ee252c041e1236dbb9405c5ea2bb02107 | Sí |
| empleos_limpio_con_competencias_sin_outliers.csv | 1,451,482,826 | SHA-256 24 MiB + meta (64 hex) | 541d9576f35102498d32eb6543e12e7e231c78873e4cd890b0d3da577f42db13 | 541d9576f35102498d32eb6543e12e7e231c78873e4cd890b0d3da577f42db13 | Sí |
| X_train.csv | 8,442,944,675 | SHA-256 24 MiB + meta (64 hex) | ac2db9a34ed6fa945f07ad84922660317e9488ea230f76b93902f440f85b4467 | ac2db9a34ed6fa945f07ad84922660317e9488ea230f76b93902f440f85b4467 | Sí |
| X_test.csv | 2,110,560,074 | SHA-256 24 MiB + meta (64 hex) | 375baf909c3827142403aef34d8297e3ddba01a25db3039b199b341129540454 | 375baf909c3827142403aef34d8297e3ddba01a25db3039b199b341129540454 | Sí |
| X_train.csv | 8,443,453,087 | SHA-256 24 MiB + meta (64 hex) | 07386ebe978ebd4967e628459de83159b2a306237ad3d415502826af7fc3d43c | 07386ebe978ebd4967e628459de83159b2a306237ad3d415502826af7fc3d43c | Sí |
| X_test.csv | 2,110,688,241 | SHA-256 24 MiB + meta (64 hex) | 2554eb5a56b7fbe27cb216ac17bec72e17e315f35a12f22b57a2d16fda930f99 | 2554eb5a56b7fbe27cb216ac17bec72e17e315f35a12f22b57a2d16fda930f99 | Sí |
| transformers.joblib | 114,551 | SHA-256 completo (64 hex) | b64f676458f3ef330d44f46bda0319b76f360d2723c1bf3701645db3af2f9da8 | b64f676458f3ef330d44f46bda0319b76f360d2723c1bf3701645db3af2f9da8 | Sí |
| transformers.joblib | 114,551 | SHA-256 completo (64 hex) | d9c37b4c4b7364a83a977b475e9824fec7e849539e9121f543ba1fa50ac4ddc2 | d9c37b4c4b7364a83a977b475e9824fec7e849539e9121f543ba1fa50ac4ddc2 | Sí |
| split_map_resume_id.csv | 5,626,057 | SHA-256 completo (64 hex) | 67dd3e3d68e1ff5e4e2f5e6d50f4b41cbb1b1d19cfc5d86d57d3238d94f928dd | 67dd3e3d68e1ff5e4e2f5e6d50f4b41cbb1b1d19cfc5d86d57d3238d94f928dd | Sí |

## 6. Gráficos Generados (150 DPI)

### `nm12_hyb02_verification_summary_dashboard.png`

![Tablero de precisión decimal (-log10 error) confirmando que todas las verificaciones de MCO y Lagrange superan ampliamente el umbral 1e-10 (10 dígitos).](./figures/nm12_hyb02_verification_summary_dashboard.png)

*Tablero de precisión decimal (-log10 error) confirmando que todas las verificaciones de MCO y Lagrange superan ampliamente el umbral 1e-10 (10 dígitos).*

## 7. Comandos de Verificación en GeoGebra

### `ggb_rl01_career_steps_skills.txt`

```text
# JobPath GeoGebra Verification — IDEA-RL-01 (mean_skills ~ job_order, k=1..10)
# Paste each command sequentially into GeoGebra Classic Algebra Input (https://www.geogebra.org/classic)
# Spanish equivalents: AjusteLineal(P), CoeficienteCorrelación(P), RCuadrado(P, f)
# Expected Python OLS: a0 = 22.516043, a1 = 0.224971, r = 0.997746, R2 = 0.995498
P = {(1, 22.693871), (2, 22.977992), (3, 23.207698), (4, 23.435402), (5, 23.679668), (6, 23.884766), (7, 24.084861), (8, 24.210442), (9, 24.594249), (10, 24.764899)}
f = FitLine(P)
r = CorrelationCoefficient(P)
R2 = RSquare(P, f)
Centroid = (5.500000, 23.753385)
Q_pred = (12, f(12))
# Expected Q_pred y-coordinate: 25.215697
```

### `ggb_rl02_isco10_transferability.txt`

```text
# JobPath GeoGebra Verification — IDEA-RL-02 (ISCO-10 Centroids: mean_cross_sector ~ mean_total_rel)
# Paste each command sequentially into GeoGebra Classic Algebra Input (https://www.geogebra.org/classic)
# Spanish equivalents: AjusteLineal(P), CoeficienteCorrelación(P), RCuadrado(P, f)
# Expected Python OLS: a0 = 3.448113, a1 = 0.432990, r = 0.529160, R2 = 0.280010
# WARNING (MR-06): R2 = 0.2800 < 0.30 -> Model REJECTED for operational forecasting; Q_pred=(45, f(45)) is an arithmetic formula check only.
P = {(35.666667, 25.619048), (40.822857, 25.217143), (53.176267, 30.895161), (38.473684, 21.561920), (29.280899, 16.213483), (35.284314, 15.882353), (46.590909, 12.295455), (37.723350, 21.200508), (31.438040, 16.740634), (31.276316, 13.276316)}
f = FitLine(P)
r = CorrelationCoefficient(P)
R2 = RSquare(P, f)
Centroid = (37.973330, 19.890202)
Q_pred = (45, f(45))
# Expected Q_pred y-coordinate: 22.932683
```

### `ggb_rl04_annual_duration_extrapolation.txt`

```text
# JobPath GeoGebra Verification — IDEA-RL-04 (Annual closed-job mean_dur_q ~ year-2000, 2000..2019; extrap t=27 -> year 2027)
# Paste each command sequentially into GeoGebra Classic Algebra Input (https://www.geogebra.org/classic)
# Spanish equivalents: AjusteLineal(P), CoeficienteCorrelación(P), RCuadrado(P, f)
# Expected Python OLS: a0 = 16.441713, a1 = -0.792601, r = -0.986344, R2 = 0.972874
# Strict MR-09 censoring consistency: mean_dur_q computed ONLY on closed jobs (~es_vigente); Q_pred(27) < 0 proves extrapolation failure.
P = {(0, 18.344970), (1, 16.566926), (2, 15.008176), (3, 14.047819), (4, 13.164835), (5, 12.089182), (6, 11.260520), (7, 10.342956), (8, 9.456837), (9, 8.464565), (10, 7.781372), (11, 6.665584), (12, 6.090126), (13, 5.590715), (14, 5.163663), (15, 4.721620), (16, 4.290154), (17, 3.776902), (18, 3.142024), (19, 2.271181)}
f = FitLine(P)
r = CorrelationCoefficient(P)
R2 = RSquare(P, f)
Centroid = (9.500000, 8.912006)
Q_pred = (27, f(27))
# Expected Q_pred y-coordinate: -4.958505
```

### `ggb_lg01_survival_p3_milestones.txt`

```text
# JobPath GeoGebra Verification — IDEA-LG-01 (Tenure Survival P3 at q=4,8,20,40; eval q=12 = 3 years)
# Paste each command sequentially into GeoGebra Classic Algebra Input (https://www.geogebra.org/classic)
# Spanish equivalent: q = Polinomio(P). Verify that p(x) and q(x) coincide identically.
# Expected Python Lagrange: P_3(12) = 0.206491
# Expanded monomial form: P_3(x) = -7.909888e-05*x^3 + 0.005845*x^2 - 0.133867*x + 1.107889
P = {(4, 0.660880), (8, 0.370539), (20, 0.135783), (40, 0.042983)}
L0(x) = ((x - 8)*(x - 20)*(x - 40)) / ((4 - 8)*(4 - 20)*(4 - 40))
L1(x) = ((x - 4)*(x - 20)*(x - 40)) / ((8 - 4)*(8 - 20)*(8 - 40))
L2(x) = ((x - 4)*(x - 8)*(x - 40)) / ((20 - 4)*(20 - 8)*(20 - 40))
L3(x) = ((x - 4)*(x - 8)*(x - 20)) / ((40 - 4)*(40 - 8)*(40 - 20))
p(x) = 0.660880*L0(x) + 0.370539*L1(x) + 0.135783*L2(x) + 0.042983*L3(x)
q = Polynomial(P)
A_eval = (12, p(12))
```

### `ggb_lg02_pca_forward_p3.txt`

```text
# JobPath GeoGebra Verification — IDEA-LG-02 (PCA Cumulative Variance Version A P3 at k=1,3,5,8; eval k=4)
# Paste each command sequentially into GeoGebra Classic Algebra Input (https://www.geogebra.org/classic)
# Spanish equivalent: q = Polinomio(P). Verify that p(x) and q(x) coincide identically.
# Expected Python Lagrange: P_3(4) = 0.877777
# Expanded monomial form: P_3(x) = 0.002746*x^3 - 0.057466*x^2 + 0.412549*x - 0.028723
P = {(1, 0.329105), (3, 0.765877), (5, 0.940656), (8, 0.999954)}
L0(x) = ((x - 3)*(x - 5)*(x - 8)) / ((1 - 3)*(1 - 5)*(1 - 8))
L1(x) = ((x - 1)*(x - 5)*(x - 8)) / ((3 - 1)*(3 - 5)*(3 - 8))
L2(x) = ((x - 1)*(x - 3)*(x - 8)) / ((5 - 1)*(5 - 3)*(5 - 8))
L3(x) = ((x - 1)*(x - 3)*(x - 5)) / ((8 - 1)*(8 - 3)*(8 - 5))
p(x) = 0.329105*L0(x) + 0.765877*L1(x) + 0.940656*L2(x) + 0.999954*L3(x)
q = Polynomial(P)
A_eval = (4, p(4))
```

- Índice consolidado: [`geogebra/geogebra_verification_index.md`](./geogebra/geogebra_verification_index.md)

## 8. Limitaciones, Advertencias y Salvaguardas de Dominio

- Usa preferiblemente los comandos en inglés (`FitLine`, `Polynomial`, `RSquare`, `CorrelationCoefficient`) porque GeoGebra Classic los acepta sin error sin importar si la interfaz está configurada en español o en inglés.
- Transparencia del modo de hash: los 13 insumos `<= 64 MiB` se verifican con SHA-256 completo byte a byte (`full_sha256`), mientras los 6 archivos masivos de `1.4–8.4 GB` usan muestreo determinista de 24 MiB (inicio, centro y final) + tamaño y `mtime_ns` (`sampled_24MiB_plus_meta_sha256`), guardando siempre el digest completo de 64 caracteres hexadecimales.
- Diferencia entre alcance del núcleo (8 ideas / 19 insumos auditados) y el catálogo extendido del Prompt Maestro (14 ideas / 33 artefactos): las 6 ideas restantes (`RL-03, RL-06, LG-03..LG-06`) quedan documentadas como extensiones opcionales fuera del núcleo evaluado.

---

**Reproducibilidad:** Ejecuta `python -m scripts.ScriptsCsv.MetodosNumericos.pipeline` desde la raíz de `MineriaProtect` para recalcular todo desde `data/`, `python -m scripts.ScriptsCsv.MetodosNumericos.deliverable_packager` para actualizar esta carpeta, y `python -m unittest discover -s tests/metodos_numericos -v` para correr las 19 pruebas.
