# DASHBOARD.md · Arquitectura, Decisiones de Visualización, Seguridad y Verificación del Dashboard (`JobPath` · Fase 3)

> **Ubicación de la Aplicación:** [dashboard/](file:///c:/Users/User/Documents/JobPath/MineriaProtect/dashboard) (`Next.js 15 App Router` + `TypeScript` + `Tailwind CSS` + `Recharts` + `@neondatabase/serverless` + `lucide-react`).  
> **Conexión a Base de Datos:** Exclusivamente en servidor (`import "server-only"` en [src/lib/db.ts](file:///c:/Users/User/Documents/JobPath/MineriaProtect/dashboard/src/lib/db.ts)) hacia **Neon PostgreSQL 18** (`steep-poetry-63912763`, rama `production` `br-round-water-bboiqzaf`, base `neondb`) autenticada únicamente con el rol de mínimo privilegio **`jobpath_readonly`** (`DATABASE_URL_READONLY` en `.env.local` ignorado por Git).

---

## 1. Resumen Ejecutivo y Verificación de Controles (`RESULTS FOCUS`)

| # | Control de Verificación (Fase 3) | Criterio Exigido | Resultado Medido | Estado |
|---:|---|---|---|---|
| `1` | **Compilación y Tipado Estático (`next build`)** | `0` errores de TypeScript y `0` errores de compilación en las 6 rutas del App Router | **Compilación exitosa de las 6 vistas (`/`, `/transparencia`, `/explorador`, `/modelos`, `/metodos-numericos`, `/metodologia`)** | **`PASS`** |
| `2` | **Aislamiento Server-Only y Cero Secretos en Cliente** | `import "server-only"` en `src/lib/db.ts`, ninguna variable `NEXT_PUBLIC_*` con credenciales y `0` coincidencias de `postgresql://` o `jobpath_readonly` en `.next/static/` | **`CLIENT_BUNDLE_SECRET_LEAKS_COUNT = 0`** (`100 %` de consultas ejecutadas en Server Components vía HTTP driver `@neondatabase/serverless`) | **`PASS`** |
| `3` | **Rol de Solo Lectura (`jobpath_readonly`)** | El dashboard jamás usa credenciales de propietario (`neondb_owner`) ni de administrador | `dashboard/.env.local` contiene exclusivamente `DATABASE_URL_READONLY` (`rolsuper = FALSE`, `5/5` escrituras bloqueadas con `InsufficientPrivilege`) | **`PASS`** |
| `4` | **Gobernanza contra Descarga Masiva (`LIMIT <= 25`)** | Sin endpoints de listado completo ni descarga *bulk* del censo (`352,093` personas / `1,738,738` experiencias) | Todas las consultas relacionales en `searchTrajectoriesBounded()` y `getPersonTimelineById()` fuerzan **`LIMIT 25`** o **`LIMIT 1`** sobre índices B-tree | **`PASS`** |
| `5` | **Contrato Visual `RESULTS FOCUS` en cada Gráfico** | Todo gráfico debe mostrar: 1) Titular con el hallazgo cuantitativo, 2) *"¿Qué estoy viendo?"* (1 oración), 3) *"Límite principal"* (1 oración) | Implementado mediante el componente tipado obligatorio [ChartCard.tsx](file:///c:/Users/User/Documents/JobPath/MineriaProtect/dashboard/src/components/ChartCard.tsx) en los **14 gráficos interactivos** de las Vistas 1 a 5 | **`PASS`** |
| `6` | **Separación `Train` vs. `Test` y Alcance de Ward (`25k`)** | Reportar métricas de `Train` y `Test` por separado y distinguir K-Means (`352,093` personas) del ajuste directo de Ward (`25,000` personas de `Train`) | Tablas y gráficos comparativos `Train` vs. `Test` en `/modelos`, y distinción explícita `cluster_ward_25k_direct` (`NULL` fuera de las `25,000` personas) en `/transparencia`, `/explorador` y `/modelos` | **`PASS`** |
| `7` | **Alineación de Métodos Numéricos con las 2 Diapositivas** | Usar sólo hechos `VERIFIED` (`F-048`, `F-049`) para MCO (`IDEA-RL-04`) y Lagrange (`IDEA-LG-01`) con la lección sobre límites de extrapolación | Panel 1 espejo de Diapositiva MN-1 (`2000–2019` $R^2=0.9729$, fallo `-4.96` trim en `2027`, centrado `4,672x`) y Panel 2 espejo de Diapositiva MN-2 ($P_3(48) = -59.84\%$, Runge $2.5262 \to 0.1301$ con Chebyshev `19.4x`) | **`PASS`** |
| `8` | **Transparencia de `resume_id`, `DEC-02/07/09` y Licencias** | Declarar el origen público de `resume_id`, licencias `CC BY 4.0`, mantener `INFERRED` en `DEC-02/07/09` y nota sobre `1.0_comprension_negocio.md` | Documentado íntegramente en `/metodologia` ([src/app/metodologia/page.tsx](file:///c:/Users/User/Documents/JobPath/MineriaProtect/dashboard/src/app/metodologia/page.tsx)) y en el pie de página global | **`PASS`** |

---

## 2. Mapa de las 6 Vistas Requeridas y Consultas SQL Asociadas

### Vista 1: Resumen Ejecutivo y Viaje de los Datos (`/`)
- **Archivos:** [src/app/page.tsx](file:///c:/Users/User/Documents/JobPath/MineriaProtect/dashboard/src/app/page.tsx) y [src/components/OverviewCharts.tsx](file:///c:/Users/User/Documents/JobPath/MineriaProtect/dashboard/src/components/OverviewCharts.tsx).
- **Contenido:**
  - *En una pantalla:* Pregunta central del proyecto, 4 KPIs maestros del censo en Neon (`352,093` personas, `1,738,738` experiencias, `45.30 %` personas con $\ge 1$ retorno, `0.7245` ROC-AUC en Test / $k^* = 4$ arquetipos) y tarjetas con **Los 10 Hallazgos Principales Verificados (`FACTS.md` Top 10)**.
  - *El Viaje de los Datos (`Raw -> Clean -> Features -> Models`):*
    1. **Gráfico 1.1 (`agg_inclusion_exclusion_funnel`):** Embudo desde `1,993,291` filas crudas (`355,315` personas) $\to$ `1,871,014` limpias (`355,308` personas) $\to$ `1,738,738` clasificadas en Neon (`352,093` personas, `99.10 %`) $\to$ `Train` (`281,674`) / `Test` (`70,419`) $\to$ Muestra directa Ward (`25,000`).
    2. **Gráfico 1.2 (`agg_eda_distributions_and_segments`):** Los 4 segmentos tipológicos del EDA (`exploradora` `46.77 %`, `permanente` `42.98 %`, `sin_transicion` `7.52 %`, `mixta` `2.73 %`).
    3. **Gráfico 1.3 (`agg_pca_variance_and_loadings`):** Varianza explicada individual y acumulada (`PC1`–`PC5`) en `4.1_PCA_completo (50k)` comparando Versión A (`4` comps $\ge 80 \%$) y Versión B (`3` comps $\ge 80 \%$).
    4. **Gráfico 1.4 (`agg_top_occupation_transitions`):** Top 10 transiciones ocupacionales consecutivas entre las `1,386,645` transiciones del censo.
  - *Tabla de auditoría:* Bitácora oficial de las 8 etapas de limpieza y auditoría IQR (`agg_cleaning_and_iqr_audit`).

### Vista 2: Transparencia de Datos, Inclusión/Exclusión y Muestreo Ward (`/transparencia` — *MÁS IMPORTANTE*)
- **Archivos:** [src/app/transparencia/page.tsx](file:///c:/Users/User/Documents/JobPath/MineriaProtect/dashboard/src/app/transparencia/page.tsx) y [src/components/TransparencyCharts.tsx](file:///c:/Users/User/Documents/JobPath/MineriaProtect/dashboard/src/components/TransparencyCharts.tsx).
- **Contenido:**
  - *Síntesis lista para diapositiva (`SAMPLING_REPORT.md` §2):* Explica por qué Neon aloja el `100 %` del censo clasificado (`Candidato C`, error muestral `±0.0000 pp`), qué quedó fuera y por qué, cómo se garantizó cero fuga entre `Train` y `Test` (`SEED = 42`, `0` personas compartidas, hecho `F-050`), y por qué el ajuste directo de Ward se restringe a `25,000` personas de `Train` (`495.88 GB` RAM para $O(N^2)$).
  - **Gráfico 2.1 (`agg_inclusion_exclusion_funnel`):** Desglose exacto de exclusiones (`122,277` en limpieza física + `128,981` `'unknown'` sin oficio ESCO + `3,295` `'rescatado'` sin oficio hoja ESCO) frente a las `1,738,738` experiencias incluidas.
  - **Gráfico 2.2 (`person_trajectories` agrupado por `isco_major_1d_zfill`):** Comparación barra a barra de los 10 Grandes Grupos ISCO (`0` Militar a `9` Elementales) entre el Censo Completo (`352,093`) y la submuestra Ward (`25,000`), con desviación máxima de `0.08 pp`.
  - **Gráfico 2.3 (`person_trajectories` agrupado por `university_level`):** Comparación de los 5 niveles educativos (incluyendo `'No reportado'` = `12.18 %`).
  - *Tablas comparativas:* Matriz de diseño de la Fase 1 (`Candidato A 25k` vs. `Candidato B2 50k` vs. `Candidato C Censo 352k`) y auditoría estrato por estrato en vivo desde PostgreSQL.

### Vista 3: Explorador de Trayectorias por Persona (`/explorador`)
- **Archivos:** [src/app/explorador/page.tsx](file:///c:/Users/User/Documents/JobPath/MineriaProtect/dashboard/src/app/explorador/page.tsx) y [src/components/PersonTimelineChart.tsx](file:///c:/Users/User/Documents/JobPath/MineriaProtect/dashboard/src/components/PersonTimelineChart.tsx).
- **Contenido:**
  - **Modo A (Galería de 8 Arquetipos Verificados):** Botones de 1 clic para cargar perfiles reales de `Test` en los 4 clústeres de K-Means (`#17`, `#217`, `#10`, `#36`) y de la muestra directa Ward 25k en los 4 clústeres jerárquicos (`#65`, `#665`, `#160`, `#377`).
  - **Modo B (Buscador y Filtro Guiado con `LIMIT <= 25`):** Filtrado combinable por `resume_id`, `split` (`train`/`test`), `cluster_kmeans_8_0` (`0..3`), `isco_major_1d_zfill` (`0..9`), `university_level` y `in_ward_25k_sample` usando exclusivamente los índices B-tree `person_trajectories_pkey`, `idx_pt_split_km_isco_edu` e `idx_pt_ward25k`.
  - **Visualización de la Carrera:**
    - Tarjeta de perfil con diferenciación explícita entre **Clúster K-Means (`8.0`, censo completo)** y **Clúster Ward (`8.1`, mostrando la etiqueta directa si `in_ward_25k_sample = TRUE` o un aviso `NULL · Fuera de Muestra 25k` + proyección `NearestCentroid` si es `FALSE`)**.
    - **Gráfico 3.1:** Duración trimestral `dur_q` puesto por puesto coloreando empleos reincidentes (`reincide = 1`).
    - **Gráfico 3.2:** Evolución apilada de competencias prácticas (`C`) y conocimientos teóricos (`K`) en la Versión A ($E = C + K$).
    - Cronograma detallado con nombres legibles de ocupación ESCO + glosa en español + código ESCO e ISCO en etiquetas monoespaciadas.

### Vista 4: Modelos Supervisados (`6.0`–`7.2`) y Clustering (`8.0`–`8.1`) (`/modelos`)
- **Archivos:** [src/app/modelos/page.tsx](file:///c:/Users/User/Documents/JobPath/MineriaProtect/dashboard/src/app/modelos/page.tsx) y [src/components/ModelsCharts.tsx](file:///c:/Users/User/Documents/JobPath/MineriaProtect/dashboard/src/components/ModelsCharts.tsx).
- **Contenido:**
  - Tabla ejecutiva con **métricas de `Train (Validación Cruzada / OOF)` y `Test (347,720 empleos / 70,419 personas)` reportadas por separado** y lectura en lenguaje sencillo para cada familia (`6.0` Logística OHE e HistGradientBoosting, `7.0` CART Árboles 1–3, `7.1` HybridNaiveBayes `NB-H` y `7.2` `KNN-W`).
  - **Gráfico 4.1 (`agg_supervised_models_benchmark`):** Comparativa unificada de `ROC-AUC`, `F1 Clase 1` y `PR-AUC` en Test.
  - **Gráfico 4.2 (`agg_naive_bayes_isco_rates`):** Tasa observada en `Train` vs. tasa confirmada en `Test` vs. probabilidad predicha por `NB-H` en los 10 Grandes Grupos ISCO.
  - **Gráfico 4.3 (`agg_knn_neighbor_purity`):** Curva de pureza geométrica de los `k = 51` vecinos al variar el peso ocupacional $w \in [0, 4]$.
  - **Gráfico 4.4 y Tablas de Clustering (`agg_kmeans_full_profiles`, `agg_ward_25k_profiles`, `agg_clustering_executive_comparison`):** Comparación `Train` vs. `Test` de los 4 arquetipos de K-Means++ (`352,093` personas) frente a la muestra directa de descubrimiento de Ward (`25,000` personas de `Train`).

### Vista 5: Métodos Numéricos Aplicados a Duración Laboral (`/metodos-numericos`)
- **Archivos:** [src/app/metodos-numericos/page.tsx](file:///c:/Users/User/Documents/JobPath/MineriaProtect/dashboard/src/app/metodos-numericos/page.tsx) y [src/components/NumericalMethodsCharts.tsx](file:///c:/Users/User/Documents/JobPath/MineriaProtect/dashboard/src/components/NumericalMethodsCharts.tsx).
- **Contenido (Alineado 1 a 1 con las 2 diapositivas dedicadas de la Fase 4):**
  - **Panel 1 — Espejo Diapositiva MN-1 (`IDEA-RL-04` MCO sobre empleos cerrados `~es_vigente`):**
    - **Gráfico 5.1 interactivo:** Conmutador entre soporte válido `2000–2019` ($R^2 = 0.9729$, pendiente $-0.7926\text{ trim/año}$) y extrapolación `2020–2027` que cruza por debajo de cero desde `2021` (`-0.2029` trim) hasta **`-4.9585` trimestres en `2027`**.
    - **Gráfico 5.2:** Colapso del ajuste lineal de competencias esenciales al incluir las 4 cohortes censuradas `2020–2023` ($R^2$ cae de `0.7475` a `0.0826`).
    - Tablas de condicionamiento numérico (centrado $t - 2000$ reduce discrepancia frente a `polyfit` en **`4,672x`**) y auditoría año por año.
  - **Panel 2 — Espejo Diapositiva MN-2 (`IDEA-LG-01` Lagrange sobre curva de supervivencia $S(q)$ en `1,643,772` empleos cerrados):**
    - **Gráfico 5.3 interactivo:** Polinomio cúbico $P_3(q)$ anclado en $q \in \{4, 8, 20, 40\}$ mostrando interpolación interna en $q = 12$ (`20.65 %` vs `25.19 %`), rebote no monótono en $q = 28$ (`20.58 %` vs `8.04 %`) y explosión al extrapolar en $q = 48$ (**`-59.84 %`**).
    - **Gráfico 5.4:** Fenómeno de Runge en grados `3, 5, 8, 12, 16` comparando Lagrange Global Equiespaciado ($E_\infty = 2.5262$ en grado 16, mínimo `-248.27 %`), **Chebyshev-Lobatto (`15` nodos enteros deduplicados, $E_\infty = 0.1301$, reducción de error de `19.4x` y `0` violaciones de `[0, 1]`)** y Lagrange Local por Tramos $P_2$.

### Vista 6: Metodología, Gobernanza y Limitaciones (`/metodologia`)
- **Archivo:** [src/app/metodologia/page.tsx](file:///c:/Users/User/Documents/JobPath/MineriaProtect/dashboard/src/app/metodologia/page.tsx).
- **Contenido:**
  - Declaración explícita de que `resume_id` proviene directamente del dataset público pseudonimizado **JobHop v2** (`0` PII).
  - Atribución formal de licencias **CC BY 4.0** para **JobHop v2** (VDAB / Ghent University) y **ESCO v1.2.1** (Comisión Europea, Decisión `2011/833/EU`).
  - Las 6 limitaciones metodológicas principales del proyecto.
  - Tabla de trazabilidad `DEC-01` a `DEC-14` conservando la etiqueta **`INFERRED - confirm with team`** en `DEC-02`, `DEC-07` y `DEC-09`, el hecho verificado `F-050` (`0` personas compartidas entre `Train` y `Test`) y la nota de que `docs/1.0_comprension_negocio.md` quedó desactualizado respecto a los modelos supervisados sin editar dicho archivo histórico.

---

## 3. Verificación en Vivo (HTTP 200 contra Neon) e Instrucciones de Despliegue Preview en Vercel

### 3.1 Resultados de Renderizado Server-Side en Vivo contra Neon (`steep-poetry-63912763`)

Se inició el servidor de producción compilado (`next start -p 3199`) conectado a Neon con `jobpath_readonly` y se verificó la respuesta HTTP y carga de datos reales en las 6 vistas:

| Ruta del Dashboard | Modo Next.js (`next build`) | Estado HTTP | Bytes HTML Renderizados | Tamaño JS Ruta / First Load JS | Tablas Neon Consultadas en Servidor |
|---|---|---:|---:|---:|---|
| `/` (Vista 1 · Resumen y Viaje de Datos) | `ƒ Dynamic (Server)` | **`HTTP 200`** | `138,266 B` | `2.93 kB` / `220 kB` | `agg_inclusion_exclusion_funnel`, `agg_cleaning_and_iqr_audit`, `agg_eda_distributions_and_segments`, `agg_top_occupation_transitions`, `agg_pca_variance_and_loadings` |
| `/transparencia` (Vista 2 · Inclusión/Exclusión y Muestreo Ward) | `ƒ Dynamic (Server)` | **`HTTP 200`** | `129,029 B` | `2.12 kB` / `212 kB` | `agg_inclusion_exclusion_funnel`, `person_trajectories` (agrupado por `isco_major_1d_zfill`, `university_level`, `cluster_kmeans_8_0` vs. `in_ward_25k_sample`) |
| `/explorador?id=17` (Vista 3 · Arquetipo K-Means Test) | `ƒ Dynamic (Server)` | **`HTTP 200`** | `145,872 B` | `1.20 kB` / `214 kB` | `person_trajectories` (`LIMIT 25`), `person_experiences JOIN esco_occupations_catalog` (`LIMIT 25`) |
| `/explorador?id=65` (Vista 3 · Arquetipo Muestra Directa Ward 25k) | `ƒ Dynamic (Server)` | **`HTTP 200`** | `128,803 B` | `1.20 kB` / `214 kB` | `person_trajectories` (`in_ward_25k_sample = TRUE`), `person_experiences JOIN esco_occupations_catalog` |
| `/modelos` (Vista 4 · Supervisados 6.0–7.2 y Clustering 8.0–8.1) | `ƒ Dynamic (Server)` | **`HTTP 200`** | `162,220 B` | `1.91 kB` / `216 kB` | `agg_supervised_models_benchmark`, `agg_decision_trees_comparison`, `agg_naive_bayes_isco_rates`, `agg_knn_neighbor_purity`, `agg_clustering_executive_comparison`, `agg_kmeans_full_profiles`, `agg_ward_25k_profiles` |
| `/metodos-numericos` (Vista 5 · MCO RL-04 vs. Lagrange LG-01) | `ƒ Dynamic (Server)` | **`HTTP 200`** | `133,319 B` | `8.84 kB` / `223 kB` | `agg_nm_rl04_annual_macro`, `agg_nm_rl04_ols_regimes`, `agg_nm_rl04_extrapolation_audit`, `agg_nm_lg01_survival_curve`, `agg_nm_lg01_p3_milestones`, `agg_nm_lg01_runge_benchmark` |
| `/metodologia` (Vista 6 · Metodología, Límites y Licencias CC BY 4.0) | `○ Static (Prerendered)` | **`HTTP 200`** | `63,180 B` | `123 B` / `103 kB` | Contenido estático verificado (`DEC-01`..`DEC-14`, nota `resume_id`, licencias `CC BY 4.0`) |

### 3.2 Despliegue Preview Verificado en Vercel (`sgemd/jobpath-dashboard`)

- **Cuenta / Equipo Vercel:** `johan-lopez-o` / equipo `sgemd` (`team_NdmIzUIHCYNDrCqfi2ChTqmX`).
- **Proyecto Creado y Vinculado:** `jobpath-dashboard` (`prj_843GkYlusadqOJAS52MtKM81nm8d`, framework `nextjs` en [dashboard/vercel.json](file:///c:/Users/User/Documents/JobPath/MineriaProtect/dashboard/vercel.json), sin modificar ningún proyecto previo del equipo).
- **Variable de Entorno Configurada:** `DATABASE_URL_READONLY` (`Encrypted` / `sensitive`, asignada exclusivamente al entorno **`Preview`** con el rol de solo lectura `jobpath_readonly`).
- **URL del Preview Deployment (`READY`, `dpl_ESwYHeVBD3PjVjwKsT4VzHKTHTq2`):**
  - **Preview URL:** `https://jobpath-dashboard-ouqmm8rx3-sgemd.vercel.app`
  - **Panel de Inspección:** `https://vercel.com/sgemd/jobpath-dashboard/ESwYHeVBD3PjVjwKsT4VzHKTHTq2`
- **Gobernanza:** Mantenido estrictamente como **Preview Deployment** (con Vercel Deployment Protection activa, no promovido a producción pública) conforme a la regla de gobernanza del Candidato C.

```powershell
# Re-desplegar cambios futuros en Preview desde dashboard/:
cd c:\Users\User\Documents\JobPath\MineriaProtect\dashboard
vercel deploy . --target preview --yes
```
