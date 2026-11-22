import React from "react";
import { getTransparencyData } from "@/lib/db";
import { ChartCard } from "@/components/ChartCard";
import {
  ExclusionBreakdownChart,
  IscoStrataComparisonChart,
  EducationStrataComparisonChart,
} from "@/components/TransparencyCharts";
import { ISCO_MAJOR_LABELS_ES, formatEducationEs } from "@/lib/isco-labels";
import {
  ShieldCheck,
  Database,
  CheckCircle2,
  AlertOctagon,
  Lock,
  Cpu,
} from "lucide-react";

export const dynamic = "force-dynamic";

export default async function TransparenciaPage() {
  const { funnel, iscoStrata, eduStrata, kmStrata } =
    await getTransparencyData();

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <section className="rounded-2xl border border-amber-300 bg-gradient-to-r from-amber-50 via-white to-blue-50 p-6 shadow-sm">
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500 px-3 py-1 text-xs font-bold text-slate-950">
            <ShieldCheck className="h-3.5 w-3.5" />
            VISTA MÁS IMPORTANTE · Transparencia de Inclusión/Exclusión y Muestreo
          </span>
          <span className="rounded bg-slate-900 px-2.5 py-0.5 font-mono text-xs font-semibold text-amber-300">
            Candidato C Aprobado · SEED = 42 · Unidad = Persona
          </span>
        </div>

        <h1 className="mt-3 text-2xl font-extrabold text-slate-900 sm:text-3xl">
          ¿Por qué los datos de este dashboard son confiables, qué quedó incluido en el censo de Neon y dónde aplica el submuestreo?
        </h1>

        {/* Slide-ready verbatim paragraph from SAMPLING_REPORT.md */}
        <blockquote className="mt-4 rounded-xl border-l-4 border-blue-700 bg-white p-4 text-xs leading-relaxed text-slate-700 shadow-sm sm:text-sm">
          <strong className="block text-slate-900 mb-1">
            Síntesis de Transparencia (Alineada con la Presentación Reveal.js y SAMPLING_REPORT.md):
          </strong>
          En lugar de depender de una submuestra con error de estimación, nuestra base de datos en la nube (Neon PostgreSQL) aloja el{" "}
          <strong className="text-blue-800">
            100 % del universo modelable clasificado (352,093 personas y 1,738,738 experiencias laborales en 268.60 MiB, con error muestral ±0.0000 pp y 0 % de pérdida en las 373,311 rutas únicas de transición ocupacional)
          </strong>
          . Del dataset limpio total (1,871,014 experiencias en 355,308 personas), se excluyeron de forma transparente{" "}
          <strong className="text-amber-900">
            132,276 experiencias (7.07 %: 128,981 sin oficio identificado y 3,295 sin oficio hoja en ESCO; 3,215 personas exclusivas = 0.90 %)
          </strong>{" "}
          para no inventar competencias inexistentes con ceros falsos. Toda la población incluida preserva la partición estricta por persona{" "}
          <strong className="text-emerald-800">
            80 % Train (281,674 personas) / 20 % Test (70,419 personas) con 0 personas compartidas
          </strong>
          ; asimismo, mientras <strong>K-Means++ (8.0)</strong> segmenta directamente a las 352,093 personas, el enlace jerárquico directo de{" "}
          <strong className="text-purple-800">Ward (8.1)</strong> se identifica explícitamente sólo sobre su{" "}
          <strong className="text-purple-800">
            muestra estratificada de 25,000 personas de Train (7.10 %, cluster_ward_25k_direct)
          </strong>
          , dado que calcular la matriz completa de distancias{" "}
          <code className="rounded bg-slate-100 px-1 py-0.5">O(n²)</code> exigiría{" "}
          <strong>495.88 GB de memoria RAM</strong>.
        </blockquote>
      </section>

      {/* 4 Verification Pillars */}
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-bold text-blue-700">
            <Database className="h-4 w-4" />
            <span>1. Cobertura Censal (Candidato C)</span>
          </div>
          <div className="mt-1.5 text-xl font-extrabold text-slate-900">
            100.00 % (±0.00 pp)
          </div>
          <p className="mt-1 text-xs text-slate-600">
            Aloja las 352,093 personas clasificadas completas (<code>sampling_weight = 1.0</code>). Distancia de Variación Total <code>TVD = 0.0000 pp</code> y <code>D_KS = 0.0000</code>.
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-bold text-emerald-700">
            <Lock className="h-4 w-4" />
            <span>2. Cero Fuga Train / Test (F-017)</span>
          </div>
          <div className="mt-1.5 text-xl font-extrabold text-slate-900">
            0 Personas Compartidas
          </div>
          <p className="mt-1 text-xs text-slate-600">
            <code>GroupShuffleSplit(80/20, seed=42)</code> por <code>resume_id</code>: 281,674 personas en Train (1,391,018 empleos) y 70,419 en Test (347,720 empleos).
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-bold text-purple-700">
            <Cpu className="h-4 w-4" />
            <span>3. Alcance Honesto de Ward (8.1)</span>
          </div>
          <div className="mt-1.5 text-xl font-extrabold text-slate-900">
            25,000 Directas (7.10%)
          </div>
          <p className="mt-1 text-xs text-slate-600">
            <code>cluster_ward_25k_direct</code> es no nulo sólo en las 25,000 personas de la muestra Ward (<code>2.50 GB RAM</code>) y <code>NULL</code> en las 327,093 restantes.
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-bold text-amber-800">
            <CheckCircle2 className="h-4 w-4" />
            <span>4. Huella Física y Latencia en Neon</span>
          </div>
          <div className="mt-1.5 text-xl font-extrabold text-slate-900">
            268.60 MiB (27.02%)
          </div>
          <p className="mt-1 text-xs text-slate-600">
            21 tablas + 6 índices B-tree muy por debajo del tope de 600 MiB y del límite gratuito de 1 GiB. Consultas agregadas en <code>&lt; 0.05 ms</code> motor.
          </p>
        </div>
      </section>

      {/* Charts: Exclusion Breakdown & Stratum Comparisons */}
      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ChartCard
          factId="F-004 · F-012 · F-015"
          sourceLabel="Tabla Neon: agg_inclusion_exclusion_funnel"
          badgeText="Auditoría de Exclusión"
          badgeTone="amber"
          headline="De las 1,871,014 experiencias limpias, sólo se excluyeron 132,276 (7.07 %) por carecer de oficio hoja ESCO (128,981 'unknown' + 3,295 'rescatado')"
          whatAmISeeing="Volumen exacto de experiencias laborales removidas en limpieza física (gris), excluidas por falta de código ocupacional hoja ESCO (ámbar) e incluidas en el censo clasificado de Neon (esmeralda)."
          primaryLimit="Las 3,215 personas cuyas experiencias eran exclusivamente 'unknown' o 'rescatado' (0.90 % de las personas limpias) no pueden evaluarse en modelos dependientes de competencias ESCO."
        >
          <ExclusionBreakdownChart funnel={funnel} />
        </ChartCard>

        <ChartCard
          factId="F-044 · SAMPLING_REPORT §4"
          sourceLabel="Consulta en vivo sobre person_trajectories (352,093 vs. 25,000)"
          badgeText="Estratificación ISCO 0..9"
          badgeTone="purple"
          headline="La submuestra estratificada Ward de 25,000 personas replica la distribución de los 10 Grandes Grupos ISCO del censo con desviación máxima de 0.08 pp"
          whatAmISeeing="Comparación barra a barra del porcentaje de personas en cada Gran Grupo ISCO-08 (incluyendo ISCO 0 Militar con cero inicial preservado) entre el Censo Completo (azul) y la submuestra Ward 25k (púrpura)."
          primaryLimit="La submuestra Ward de 25,000 personas se extrajo exclusivamente de la partición Train (80 %) para evitar cualquier contaminación con Test durante el descubrimiento jerárquico."
        >
          <IscoStrataComparisonChart strata={iscoStrata} />
        </ChartCard>
      </section>

      {/* Education Strata Chart + Candidatos A vs B2 vs C Table */}
      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ChartCard
          factId="F-010 · SAMPLING_REPORT §4"
          sourceLabel="Consulta en vivo sobre person_trajectories (Nivel Educativo)"
          badgeText="5 Niveles Educativos"
          badgeTone="emerald"
          headline="En nivel educativo y bandera MNAR ('No reportado' = 12.18 %), la submuestra Ward 25k diverge en máximo 0.27 pp frente al censo y el Censo C tiene 0.00 pp de error"
          whatAmISeeing="Distribución porcentual de las personas según su nivel académico reportado en el primer empleo clasificado (Secondary school, Bachelor, Master, No reportado y PhD) en el Censo Completo frente a la submuestra Ward."
          primaryLimit="En la submuestra de 25,000 personas el estrato minoritario PhD contiene 126 personas (margen ±8.4 pp), mientras que al cargar el Censo C completo en Neon tenemos las 1,819 personas con PhD (±0.00 pp)."
        >
          <EducationStrataComparisonChart strata={eduStrata} />
        </ChartCard>

        {/* Detailed Comparison of Candidate A vs Candidate B2 vs Candidate C */}
        <div className="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div>
            <div className="mb-2 flex items-center justify-between">
              <span className="rounded bg-blue-50 px-2.5 py-0.5 font-mono text-xs font-bold text-blue-800">
                Decisión de Diseño Fase 1 · SAMPLING_OPTIONS.md
              </span>
              <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-bold text-emerald-900">
                Candidato C Seleccionado
              </span>
            </div>
            <h3 className="text-base font-bold text-slate-900">
              Comparativa de Opciones de Muestreo Evaluadas en la Fase 1 (A vs. B2 vs. C)
            </h3>
            <p className="mt-1 text-xs text-slate-600">
              Por qué se eligió cargar el <strong>Censo Clasificado Completo (Candidato C)</strong> tras verificar que su huella con índices (<code>268.60 MiB</code>) quedaba muy por debajo del umbral Go/No-Go de <code>600 MiB</code>.
            </p>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-bold uppercase text-slate-600">
                  <tr>
                    <th className="px-2.5 py-2">Criterio Técnico</th>
                    <th className="px-2.5 py-2">Candidato A (Ward 25k)</th>
                    <th className="px-2.5 py-2">Candidato B2 (50k Estrat.)</th>
                    <th className="bg-emerald-50 px-2.5 py-2 text-emerald-950">
                      Candidato C (Censo Neon)
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  <tr>
                    <td className="px-2.5 py-2 font-semibold">Personas / Empleos</td>
                    <td className="px-2.5 py-2 font-mono">25,000 / 123,600 (7.1%)</td>
                    <td className="px-2.5 py-2 font-mono">50,000 / ~247,264 (14.2%)</td>
                    <td className="bg-emerald-50/50 px-2.5 py-2 font-mono font-bold text-emerald-900">
                      352,093 / 1,738,738 (100%)
                    </td>
                  </tr>
                  <tr>
                    <td className="px-2.5 py-2 font-semibold">Partición Train / Test</td>
                    <td className="px-2.5 py-2 text-rose-700 font-semibold">
                      100% Train / 0% Test
                    </td>
                    <td className="px-2.5 py-2">40,000 Train / 10,000 Test</td>
                    <td className="bg-emerald-50/50 px-2.5 py-2 font-bold text-emerald-900">
                      281,674 Train / 70,419 Test
                    </td>
                  </tr>
                  <tr>
                    <td className="px-2.5 py-2 font-semibold">Margen Error Global (95%)</td>
                    <td className="px-2.5 py-2 font-mono">&plusmn;0.5974 pp</td>
                    <td className="px-2.5 py-2 font-mono">&plusmn;0.4059 pp (pond.)</td>
                    <td className="bg-emerald-50/50 px-2.5 py-2 font-mono font-bold text-emerald-900">
                      &plusmn;0.0000 pp (Censo exacto)
                    </td>
                  </tr>
                  <tr>
                    <td className="px-2.5 py-2 font-semibold">Piso Mínimo por Estrato</td>
                    <td className="px-2.5 py-2 font-mono text-rose-700">
                      n_min = 42 (ISCO 0), 126 (PhD)
                    </td>
                    <td className="px-2.5 py-2 font-mono">
                      Piso &ge; 1,000 (o 100% estrato)
                    </td>
                    <td className="bg-emerald-50/50 px-2.5 py-2 font-mono font-bold text-emerald-900">
                      100% de cada estrato (598..142k)
                    </td>
                  </tr>
                  <tr>
                    <td className="px-2.5 py-2 font-semibold">Rutas de Transición (373k)</td>
                    <td className="px-2.5 py-2">Pierde ~84% de cola larga</td>
                    <td className="px-2.5 py-2">Pierde ~71% de cola larga</td>
                    <td className="bg-emerald-50/50 px-2.5 py-2 font-bold text-emerald-900">
                      100% preservadas (0% pérdida)
                    </td>
                  </tr>
                  <tr>
                    <td className="px-2.5 py-2 font-semibold">Tamaño Físico en Neon</td>
                    <td className="px-2.5 py-2 font-mono">~24 MiB</td>
                    <td className="px-2.5 py-2 font-mono">~48 MiB</td>
                    <td className="bg-emerald-50/50 px-2.5 py-2 font-mono font-bold text-emerald-900">
                      268.60 MiB (27.02% de 1 GiB)
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="mt-4 rounded-lg bg-slate-50 p-3 text-xs text-slate-700 ring-1 ring-slate-200">
            <strong>Dónde NO es confiable usar sólo la muestra Ward 25k:</strong>{" "}
            La submuestra de 25,000 personas tiene <code>0</code> individuos en la partición <code>Test</code> y sólo <code>42</code> personas en <code>ISCO 0 (Militares)</code>. Por ello, en este dashboard la muestra de 25,000 se utiliza <strong>exclusivamente</strong> para las etiquetas directas del dendrograma jerárquico de Ward (<code>8.1</code>), mientras que todas las métricas en Test y exploraciones generales usan el censo completo de 352,093 personas.
          </div>
        </div>
      </section>

      {/* Full Stratum-by-Stratum Verification Table */}
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4">
          <span className="font-mono text-xs font-bold text-blue-700">
            Tabla de Verificación en Vivo · person_trajectories (Neon PostgreSQL 18)
          </span>
          <h2 className="text-base font-bold text-slate-900">
            Auditoría Estrato por Estrato: Censo Completo en Neon (N = 352,093) vs. Submuestra Directa Ward (n = 25,000)
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-bold uppercase text-slate-600">
              <tr>
                <th className="px-3 py-2.5">Dimensión / Estrato</th>
                <th className="px-3 py-2.5 text-right">Personas Censo (N)</th>
                <th className="px-3 py-2.5 text-right">% Censo Neon</th>
                <th className="px-3 py-2.5 text-right">Personas Ward 25k (n)</th>
                <th className="px-3 py-2.5 text-right">% Muestra Ward</th>
                <th className="px-3 py-2.5 text-right">Diferencia (pp)</th>
                <th className="px-3 py-2.5 text-right">Error Muestral Censo C</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {iscoStrata.map((row) => {
                const meta = ISCO_MAJOR_LABELS_ES[String(row.stratum_key).trim()];
                return (
                  <tr key={`isco-${row.stratum_key}`} className="hover:bg-slate-50">
                    <td className="px-3 py-2 font-medium text-slate-900">
                      Gran Grupo {meta ? `${meta.title} (${meta.code})` : row.stratum_key}
                    </td>
                    <td className="px-3 py-2 text-right font-mono">
                      {Number(row.census_total).toLocaleString("es-CO")}
                    </td>
                    <td className="px-3 py-2 text-right font-mono font-semibold text-blue-800">
                      {Number(row.census_pct).toFixed(2)}%
                    </td>
                    <td className="px-3 py-2 text-right font-mono">
                      {Number(row.ward_25k_count).toLocaleString("es-CO")}
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-purple-800">
                      {Number(row.ward_25k_pct).toFixed(2)}%
                    </td>
                    <td className="px-3 py-2 text-right font-mono">
                      {Number(row.diff_pp) >= 0 ? `+${Number(row.diff_pp).toFixed(2)}` : Number(row.diff_pp).toFixed(2)} pp
                    </td>
                    <td className="px-3 py-2 text-right font-mono font-bold text-emerald-700">
                      &plusmn;0.0000 pp
                    </td>
                  </tr>
                );
              })}
              {eduStrata.map((row) => (
                <tr key={`edu-${row.stratum_key}`} className="bg-slate-50/40 hover:bg-slate-50">
                  <td className="px-3 py-2 font-medium text-slate-900">
                    Educación: {formatEducationEs(row.stratum_key)}
                  </td>
                  <td className="px-3 py-2 text-right font-mono">
                    {Number(row.census_total).toLocaleString("es-CO")}
                  </td>
                  <td className="px-3 py-2 text-right font-mono font-semibold text-blue-800">
                    {Number(row.census_pct).toFixed(2)}%
                  </td>
                  <td className="px-3 py-2 text-right font-mono">
                    {Number(row.ward_25k_count).toLocaleString("es-CO")}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-purple-800">
                    {Number(row.ward_25k_pct).toFixed(2)}%
                  </td>
                  <td className="px-3 py-2 text-right font-mono">
                    {Number(row.diff_pp) >= 0 ? `+${Number(row.diff_pp).toFixed(2)}` : Number(row.diff_pp).toFixed(2)} pp
                  </td>
                  <td className="px-3 py-2 text-right font-mono font-bold text-emerald-700">
                    &plusmn;0.0000 pp
                  </td>
                </tr>
              ))}
              {kmStrata.map((row) => (
                <tr key={`km-${row.stratum_key}`} className="hover:bg-slate-50">
                  <td className="px-3 py-2 font-medium text-slate-900">
                    Segmento No Supervisado: {row.stratum_key}
                  </td>
                  <td className="px-3 py-2 text-right font-mono">
                    {Number(row.census_total).toLocaleString("es-CO")}
                  </td>
                  <td className="px-3 py-2 text-right font-mono font-semibold text-blue-800">
                    {Number(row.census_pct).toFixed(2)}%
                  </td>
                  <td className="px-3 py-2 text-right font-mono">
                    {Number(row.ward_25k_count).toLocaleString("es-CO")}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-purple-800">
                    {Number(row.ward_25k_pct).toFixed(2)}%
                  </td>
                  <td className="px-3 py-2 text-right font-mono">
                    {Number(row.diff_pp) >= 0 ? `+${Number(row.diff_pp).toFixed(2)}` : Number(row.diff_pp).toFixed(2)} pp
                  </td>
                  <td className="px-3 py-2 text-right font-mono font-bold text-emerald-700">
                    &plusmn;0.0000 pp
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Complete 10-Stage Inclusion/Exclusion Funnel Table */}
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <span className="font-mono text-xs font-bold text-blue-700">
              Tabla Neon: agg_inclusion_exclusion_funnel (10 Etapas Auditadas)
            </span>
            <h2 className="text-base font-bold text-slate-900">
              Registro Completo del Embudo de Inclusión, Exclusión, Partición 80/20 y Bandera Ward 25k
            </h2>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-bold uppercase text-slate-600">
              <tr>
                <th className="px-3 py-2.5">#</th>
                <th className="px-3 py-2.5">Etapa del Embudo</th>
                <th className="px-3 py-2.5">Estado en Neon</th>
                <th className="px-3 py-2.5 text-right">Experiencias</th>
                <th className="px-3 py-2.5 text-right">Personas</th>
                <th className="px-3 py-2.5 text-right">% Exp. Limpias</th>
                <th className="px-3 py-2.5 text-right">% Pers. Limpias</th>
                <th className="px-3 py-2.5">Razón Técnica y Metodológica</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {funnel.map((row) => {
                const isExcluded = row.status_in_neon.includes("EXCLUDED");
                const isCensus = row.status_in_neon === "INCLUDED_CENSUS";
                return (
                  <tr
                    key={row.stage_order}
                    className={
                      isCensus
                        ? "bg-blue-50/70 font-semibold"
                        : isExcluded
                        ? "bg-amber-50/40"
                        : "hover:bg-slate-50"
                    }
                  >
                    <td className="px-3 py-2.5 font-mono">{row.stage_order}</td>
                    <td className="px-3 py-2.5 text-slate-900">
                      {row.stage_label_es}
                    </td>
                    <td className="px-3 py-2.5">
                      <span
                        className={`inline-flex items-center gap-1 rounded px-2 py-0.5 font-mono text-[10px] font-bold ${
                          isCensus
                            ? "bg-blue-700 text-white"
                            : isExcluded
                            ? "bg-amber-200 text-amber-950"
                            : "bg-slate-200 text-slate-800"
                        }`}
                      >
                        {isExcluded && <AlertOctagon className="h-3 w-3" />}
                        {row.status_in_neon}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-right font-mono">
                      {Number(row.experiences_count).toLocaleString("es-CO")}
                    </td>
                    <td className="px-3 py-2.5 text-right font-mono">
                      {Number(row.persons_count).toLocaleString("es-CO")}
                    </td>
                    <td className="px-3 py-2.5 text-right font-mono">
                      {Number(row.pct_clean_experiences).toFixed(2)}%
                    </td>
                    <td className="px-3 py-2.5 text-right font-mono">
                      {Number(row.pct_clean_persons).toFixed(2)}%
                    </td>
                    <td className="px-3 py-2.5 text-slate-700">
                      {row.reason_es}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
