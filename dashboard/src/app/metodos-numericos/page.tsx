import React from "react";
import { getNumericalMethodsData } from "@/lib/db";
import { ChartCard } from "@/components/ChartCard";
import {
  Rl04DurationExtrapolationChart,
  Rl04SkillsCensoredCollapseChart,
  Lg01SurvivalAndP3Chart,
  Lg01RungeVsChebyshevChart,
} from "@/components/NumericalMethodsCharts";
import {
  Sigma,
  AlertOctagon,
  CheckCircle2,
  Presentation,
} from "lucide-react";

export const dynamic = "force-dynamic";

export default async function MetodosNumericosPage() {
  const {
    rl04Annual,
    rl04OlsRegimes,
    rl04Extrapolation,
    lg01Survival,
    lg01P3Milestones,
    lg01Runge,
  } = await getNumericalMethodsData();

  const durExtrap = rl04Extrapolation.filter((r) => r.y_var === "mean_dur_q");

  return (
    <div className="space-y-8">
      {/* Header aligned with the 2 dedicated Reveal.js slides */}
      <section className="rounded-2xl border border-slate-200 bg-gradient-to-r from-slate-900 via-blue-950 to-purple-950 p-6 text-white shadow-md">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-400 px-3 py-1 text-xs font-bold text-slate-950">
            <Sigma className="h-3.5 w-3.5" />
            Vista 5 · Métodos Numéricos Aplicados a Duración Laboral (Sólo Hechos VERIFIED)
          </span>
          <span className="inline-flex items-center gap-1.5 rounded bg-white/10 px-2.5 py-1 font-mono text-xs text-blue-200 ring-1 ring-white/20">
            <Presentation className="h-3.5 w-3.5" />
            Alineación 1 a 1 con las 2 Diapositivas Dedicadas (PLAN_ADDENDUM.md)
          </span>
        </div>

        <h1 className="mt-3 text-2xl font-extrabold tracking-tight sm:text-3xl">
          Regresión Lineal por Mínimos Cuadrados (MCO) vs. Interpolación Polinómica de Lagrange sobre 1,643,772 Empleos Cerrados
        </h1>
        <p className="mt-2 max-w-4xl text-xs leading-relaxed text-slate-300 sm:text-sm">
          Ambos experimentos se calcularon exclusivamente sobre los{" "}
          <strong className="text-white">
            1,643,772 empleos cerrados clasificados (<code>~es_vigente</code>)
          </strong>{" "}
          para evitar sesgar las duraciones con los 94,966 contratos aún activos en <code>2026-Q1</code>. Su lección central es compartida:{" "}
          <strong className="text-amber-300">
            dentro del soporte empírico válido los modelos aproximan con alta fidelidad, pero extrapolar fuera del soporte o usar nodos equiespaciados de grado alto produce predicciones físicamente imposibles (duraciones y probabilidades negativas).
          </strong>
        </p>
      </section>

      {/* PANEL 1 (SLIDE MN-1 MIRROR): OLS REGRESSION IDEA-RL-04 */}
      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-2">
          <div>
            <span className="font-mono text-xs font-bold uppercase text-blue-700">
              Espejo de Diapositiva MN-1 · Caso 1 (IDEA-RL-04 · F-048 VERIFIED)
            </span>
            <h2 className="text-xl font-bold text-slate-900">
              1. Regresión por Mínimos Cuadrados Ordinarios (MCO): Ventana Válida (2000–2019), Censura y Fallo de Extrapolación
            </h2>
          </div>
          <span className="rounded-lg bg-blue-50 px-3 py-1 font-mono text-xs font-bold text-blue-800 ring-1 ring-blue-200">
            Condicionamiento Vandermonde: t - 2000 mejora la precisión en 4,672x
          </span>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <ChartCard
            factId="F-048 · IDEA-RL-04 (Duración Media)"
            sourceLabel="Tablas Neon: agg_nm_rl04_annual_macro y agg_nm_rl04_extrapolation_audit"
            badgeText="R² = 0.9729 en 2000–2019"
            badgeTone="blue"
            headline="En la ventana válida 2000–2019, la duración media de empleos cerrados cae a -0.7926 trimestres/año (R² = 0.9729), pero extrapolar esa recta predice -0.20 trimestres en 2021 y -4.96 trimestres en 2027"
            whatAmISeeing="Evolución anual de la duración media de empleos cerrados (azul) frente a la recta MCO ajustada en 2000–2019 (rojo punteado, y = 16.4417 - 0.7926·(t - 2000)) y su extrapolación hacia 2020–2027 por debajo de la frontera física dur_q = 0."
            primaryLimit="La pendiente negativa (-0.7926 trim/año) es un artefacto mecánico de truncamiento por ventana de observación (un empleo iniciado en 2018 y cerrado antes de 2026 sólo pudo durar pocos trimestres), no precarización real."
          >
            <Rl04DurationExtrapolationChart
              annual={rl04Annual}
              extrapolation={rl04Extrapolation}
            />
          </ChartCard>

          <ChartCard
            factId="F-048 · IDEA-RL-04 (Colapso por Cola Censurada)"
            sourceLabel="Tabla Neon: agg_nm_rl04_ols_regimes (n = 20 vs. n = 24)"
            badgeText="R² cae de 0.7475 a 0.0826"
            badgeTone="amber"
            headline="Incluir las 4 cohortes truncadas 2020–2023 (donde n_starts cae a 59, 3, 3 y 1) invierte la pendiente de competencias ESCO (+0.0967 → -0.1011) y desploma el R² de 0.7475 a 0.0826"
            whatAmISeeing="Promedio anual de competencias esenciales ESCO por cohorte de inicio (negro) comparado contra la recta MCO en soporte válido 2000–2019 (esmeralda, R² = 0.7475) y la recta contaminada por los 4 puntos ruidosos de 2020–2023 (ámbar punteado, R² = 0.0826)."
            primaryLimit="MCO sin ponderar asigna el mismo brazo de palanca en Σ(x - x̄)² a un año con 133,578 empleos (2012) que a un año con 1 solo empleo (2023), demostrando la sensibilidad cuadrática a puntos frontera con bajo soporte."
          >
            <Rl04SkillsCensoredCollapseChart annual={rl04Annual} />
          </ChartCard>
        </div>

        {/* OLS Regimes & Conditioning Table */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <span className="font-mono text-xs font-bold text-blue-700">
              F-048 · Tabla Neon: agg_nm_rl04_ols_regimes (Estabilidad Numérica y Centrado t - 2000)
            </span>
            <h3 className="mt-1 text-base font-bold text-slate-900">
              Parámetros Exactos de los Regímenes MCO y Efecto del Centrado Temporal (t = año - 2000)
            </h3>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-slate-200 bg-slate-50 text-[10px] font-bold uppercase text-slate-600">
                  <tr>
                    <th className="px-2 py-2">Modelo / Régimen</th>
                    <th className="px-2 py-2 text-right">n</th>
                    <th className="px-2 py-2 text-right">Intercepto a₀</th>
                    <th className="px-2 py-2 text-right">Pendiente a₁</th>
                    <th className="px-2 py-2 text-right">R²</th>
                    <th className="px-2 py-2 text-right">Error vs. polyfit</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {rl04OlsRegimes
                    .filter(
                      (r) =>
                        r.y_var === "mean_dur_q" || r.y_var === "mean_skills"
                    )
                    .map((r) => (
                      <tr key={r.name} className="hover:bg-slate-50">
                        <td className="px-2 py-2 font-semibold text-slate-900">
                          {r.name}
                        </td>
                        <td className="px-2 py-2 text-right font-mono">{r.n}</td>
                        <td className="px-2 py-2 text-right font-mono">
                          {Number(r.a0).toFixed(4)}
                        </td>
                        <td className="px-2 py-2 text-right font-mono">
                          {Number(r.a1).toFixed(4)}
                        </td>
                        <td className="px-2 py-2 text-right font-mono font-bold text-blue-800">
                          {Number(r.r2).toFixed(4)}
                        </td>
                        <td className="px-2 py-2 text-right font-mono text-[11px] text-emerald-800">
                          {Number(r.polyfit_max_abs_diff).toExponential(2)}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-xs text-slate-600">
              <strong>Por qué centrar el tiempo (<code>t = start_year - 2000</code>):</strong>{" "}
              Con años crudos (<code>2000..2019</code>), $\sum x_i^2 = 80,762,470$ y el número de condición de la matriz de diseño es <code>201,009.2</code>. Al trasladar el origen al año 2000 (<code>0..19</code>), $\sum t_i^2 = 2,470$, el intercepto $a_0 = 16.4417$ adquiere interpretación directa en el año base, y la discrepancia en punto flotante frente a <code>np.polyfit</code> se reduce{" "}
              <strong>4,672 veces</strong> (de $1.66 \times 10^{-11}$ a $3.55 \times 10^{-15}$).
            </p>
          </div>

          <div className="rounded-xl border border-rose-200 bg-white p-5 shadow-sm">
            <span className="font-mono text-xs font-bold text-rose-700">
              F-048 · Tabla Neon: agg_nm_rl04_extrapolation_audit (Auditoría de Fallo Físico)
            </span>
            <h3 className="mt-1 text-base font-bold text-slate-900">
              Auditoría Año por Año de Extrapolación de Duración Media (2020–2027)
            </h3>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-slate-200 bg-rose-50/60 text-[10px] font-bold uppercase text-rose-950">
                  <tr>
                    <th className="px-2.5 py-2">Año Extrapolado</th>
                    <th className="px-2.5 py-2 text-right">Predicción MCO (trim)</th>
                    <th className="px-2.5 py-2 text-right">Observado (Cerrados)</th>
                    <th className="px-2.5 py-2 text-right">Soporte n_starts</th>
                    <th className="px-2.5 py-2">Validez Física (dur_q &ge; 1)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {durExtrap.map((r) => (
                    <tr
                      key={r.year}
                      className={
                        r.physically_invalid ? "bg-rose-50/50" : "hover:bg-slate-50"
                      }
                    >
                      <td className="px-2.5 py-2 font-mono font-bold text-slate-900">
                        {r.year}
                      </td>
                      <td
                        className={`px-2.5 py-2 text-right font-mono font-bold ${
                          r.physically_invalid ? "text-rose-700" : "text-slate-800"
                        }`}
                      >
                        {Number(r.y_pred_from_2000_2019).toFixed(4)} trim
                      </td>
                      <td className="px-2.5 py-2 text-right font-mono">
                        {r.y_observed !== null
                          ? `${Number(r.y_observed).toFixed(2)} trim`
                          : "Sin datos (futuro)"}
                      </td>
                      <td className="px-2.5 py-2 text-right font-mono">
                        {r.observed_n_starts}
                      </td>
                      <td className="px-2.5 py-2">
                        {r.physically_invalid ? (
                          <span className="inline-flex items-center gap-1 rounded bg-rose-200 px-2 py-0.5 font-mono text-[10px] font-bold text-rose-950">
                            <AlertOctagon className="h-3 w-3" />
                            IMPOSIBLE (&lt; 0 trim)
                          </span>
                        ) : (
                          <span className="rounded bg-amber-100 px-2 py-0.5 font-mono text-[10px] font-semibold text-amber-900">
                            Fuera de soporte (&lt; 1 trim)
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      {/* PANEL 2 (SLIDE MN-2 MIRROR): LAGRANGE INTERPOLATION IDEA-LG-01 */}
      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-2">
          <div>
            <span className="font-mono text-xs font-bold uppercase text-purple-800">
              Espejo de Diapositiva MN-2 · Caso 2 (IDEA-LG-01 · F-049 VERIFIED)
            </span>
            <h2 className="text-xl font-bold text-slate-900">
              2. Interpolación de Lagrange sobre la Curva de Supervivencia S(q): Polinomio Cúbico P₃(q) y Fenómeno de Runge vs. Chebyshev
            </h2>
          </div>
          <span className="rounded-lg bg-emerald-50 px-3 py-1 font-mono text-xs font-bold text-emerald-900 ring-1 ring-emerald-200">
            Chebyshev-Lobatto (15 nodos): Reduce error máximo en 19.4x (0 violaciones)
          </span>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <ChartCard
            factId="F-049 · IDEA-LG-01 (Hitos Cúbicos P₃)"
            sourceLabel="Tablas Neon: agg_nm_lg01_survival_curve y agg_nm_lg01_p3_milestones"
            badgeText="1,643,772 Empleos Cerrados"
            badgeTone="purple"
            headline="Anclado en q ∈ {4, 8, 20, 40} trimestres, el polinomio cúbico P₃(q) estima q = 12 con error de 4.55 pp, pero sufre rebote no monótono en q = 28 (20.58 % vs. 8.04 %) y explota a -59.84 % al extrapolar en q = 48"
            whatAmISeeing="Curva empírica exacta de supervivencia laboral S(q) = P(dur_q ≥ q) con sus escalones cada 4 trimestres por redondeo anual (azul) frente al polinomio cúbico global de Lagrange P₃(q) (púrpura punteado)."
            primaryLimit="Un polinomio cúbico global no garantiza monotonía decreciente entre nodos distantes (entre q = 20 y q = 40 sube artificialmente) y diverge como O(q³) apenas sale del último nodo ancla (q > 40)."
          >
            <Lg01SurvivalAndP3Chart
              survival={lg01Survival}
              milestones={lg01P3Milestones}
            />
          </ChartCard>

          <ChartCard
            factId="F-049 · IDEA-LG-01 (Runge vs. Chebyshev)"
            sourceLabel="Tabla Neon: agg_nm_lg01_runge_benchmark (Grados 3 a 16)"
            badgeText="Reducción de Error 19.4x"
            badgeTone="emerald"
            headline="Al subir a grado 16, Lagrange global con nodos equiespaciados explota por el Fenómeno de Runge (E∞ = 2.5262, mínimo -248.27 %), mientras que los nodos de Chebyshev-Lobatto acotan el error a 0.1301 con 0 violaciones de [0, 1]"
            whatAmISeeing="Error absoluto máximo E∞ en todo el dominio q ∈ [1, 40] para grados 3, 5, 8, 12 y 16 comparando nodos equiespaciados (rojo), nodos enteros de Chebyshev-Lobatto (esmeralda) e interpolación cuadrática local por tramos P₂ (azul)."
            primaryLimit="Incluso con nodos de Chebyshev-Lobatto, el error no baja de ~0.13 porque la curva empírica S(q) tiene saltos discretos reales cada 4 trimestres (annual heaping en q = 2, 5, 9, 13) donde la derivada continua no existe."
          >
            <Lg01RungeVsChebyshevChart runge={lg01Runge} />
          </ChartCard>
        </div>

        {/* Tables: P3 Milestone Basis Weights & Runge Benchmark */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <span className="font-mono text-xs font-bold text-purple-800">
              F-049 · Tabla Neon: agg_nm_lg01_p3_milestones (Partición de la Unidad Σ Lᵢ(q) = 1)
            </span>
            <h3 className="mt-1 text-base font-bold text-slate-900">
              Evaluación Exacta de Pesos Base de Lagrange L₀(q)..L₃(q) y Predicción P₃(q)
            </h3>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-slate-200 bg-slate-50 text-[10px] font-bold uppercase text-slate-600">
                  <tr>
                    <th className="px-2 py-2">q (Años)</th>
                    <th className="px-2 py-2">Régimen</th>
                    <th className="px-2 py-2 text-right">Σ Lᵢ(q)</th>
                    <th className="px-2 py-2 text-right">P₃(q) Predicho</th>
                    <th className="px-2 py-2 text-right">S(q) Empírico</th>
                    <th className="px-2 py-2 text-right">|Error|</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {lg01P3Milestones.map((r) => (
                    <tr
                      key={r.quarter_q}
                      className={
                        Number(r.p3_pred) < 0
                          ? "bg-rose-50/60"
                          : "hover:bg-slate-50"
                      }
                    >
                      <td className="px-2 py-2 font-mono font-bold text-slate-900">
                        q = {r.quarter_q} ({r.years}a)
                      </td>
                      <td className="px-2 py-2">
                        {r.is_extrapolation ? (
                          <span className="rounded bg-rose-100 px-1.5 py-0.5 font-mono text-[10px] font-bold text-rose-900">
                            Extrapolación
                          </span>
                        ) : (
                          <span className="rounded bg-emerald-100 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-emerald-900">
                            Interpolación
                          </span>
                        )}
                      </td>
                      <td className="px-2 py-2 text-right font-mono">
                        {Number(r.sum_li).toFixed(4)}
                      </td>
                      <td
                        className={`px-2 py-2 text-right font-mono font-bold ${
                          Number(r.p3_pred) < 0
                            ? "text-rose-700"
                            : "text-purple-900"
                        }`}
                      >
                        {(Number(r.p3_pred) * 100).toFixed(2)}%
                      </td>
                      <td className="px-2 py-2 text-right font-mono">
                        {(Number(r.true_s_q) * 100).toFixed(2)}%
                      </td>
                      <td className="px-2 py-2 text-right font-mono font-semibold">
                        {(Number(r.abs_err) * 100).toFixed(2)} pp
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <span className="font-mono text-xs font-bold text-emerald-800">
              F-049 · Tabla Neon: agg_nm_lg01_runge_benchmark (Auditoría de Violaciones de Probabilidad)
            </span>
            <h3 className="mt-1 text-base font-bold text-slate-900">
              Benchmark de Grado Alto: Equiespaciado vs. Chebyshev-Lobatto vs. Tramos Locales P₂
            </h3>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-slate-200 bg-slate-50 text-[10px] font-bold uppercase text-slate-600">
                  <tr>
                    <th className="px-2 py-2">Grado (Nodos)</th>
                    <th className="px-2 py-2">Estrategia de Nodos</th>
                    <th className="px-2 py-2 text-right">Error Máx E∞</th>
                    <th className="px-2 py-2 text-right">RMSE</th>
                    <th className="px-2 py-2 text-right">Mín Predicho</th>
                    <th className="px-2 py-2 text-right">Violaciones [0,1]</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {lg01Runge
                    .filter((r) => [8, 12, 16].includes(Number(r.degree)))
                    .map((r) => (
                      <tr
                        key={`${r.degree}-${r.node_strategy}`}
                        className={
                          Number(r.n_prob_bound_violations) > 0
                            ? "bg-rose-50/50"
                            : "hover:bg-slate-50"
                        }
                      >
                        <td className="px-2 py-1.5 font-mono font-bold">
                          g={r.degree} (n={r.n_nodes})
                        </td>
                        <td className="px-2 py-1.5 font-medium text-slate-900">
                          {r.node_strategy}
                        </td>
                        <td className="px-2 py-1.5 text-right font-mono font-bold">
                          {Number(r.max_abs_err).toFixed(4)}
                        </td>
                        <td className="px-2 py-1.5 text-right font-mono">
                          {Number(r.rmse).toFixed(4)}
                        </td>
                        <td
                          className={`px-2 py-1.5 text-right font-mono ${
                            Number(r.min_pred) < 0
                              ? "font-bold text-rose-700"
                              : ""
                          }`}
                        >
                          {(Number(r.min_pred) * 100).toFixed(2)}%
                        </td>
                        <td className="px-2 py-1.5 text-right font-mono font-bold">
                          {Number(r.n_prob_bound_violations) > 0 ? (
                            <span className="text-rose-700">
                              {r.n_prob_bound_violations} viol.
                            </span>
                          ) : (
                            <span className="text-emerald-700">0</span>
                          )}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
