import React from "react";
import Link from "next/link";
import { getOverviewData } from "@/lib/db";
import { ChartCard } from "@/components/ChartCard";
import {
  DataJourneyFunnelChart,
  TrajectorySegmentsChart,
  PcaVarianceChart,
  TopTransitionsChart,
} from "@/components/OverviewCharts";
import {
  ArrowRight,
  Users,
  Briefcase,
  Layers,
  ShieldCheck,
  Repeat,
  Compass,
  Award,
} from "lucide-react";

export const dynamic = "force-dynamic";

const TOP_10_HEADLINE_FACTS = [
  {
    rank: 1,
    factIds: "F-017 · F-023 · F-024",
    title:
      "El 45.30 % de los trabajadores repite al menos una vez un mismo oficio en su carrera (30.00 % de las experiencias son reincidentes)",
    meaning:
      "Casi uno de cada tres empleos ejercidos consiste en volver a desempeñar exactamente la misma ocupación ESCO con un nuevo contrato o empleador.",
    limit:
      "El target reincide = (veces_ese_oficio > 1) mide recurrencia acumulada en el CV completo, no sólo una predicción prospectiva desde el primer empleo.",
  },
  {
    rank: 2,
    factIds: "F-042 · F-043 · F-044",
    title:
      "El mercado laboral se divide naturalmente en k* = 4 arquetipos no supervisados (confirmados por Ward y K-Means++ con ARI = 0.6502)",
    meaning:
      "Las trayectorias se separan solas en 4 perfiles: Operativos de Inserción Temprana (43.90 %), Profesionales de Conocimiento (27.99 %), Carreras Largas/Pluriempleo (16.44 %) y Educación No Reportada MNAR (11.66 %).",
    limit:
      "El índice de Silueta es moderado (0.1948 en personas) porque las trayectorias forman un continuo denso, y Ward directo exige submuestreo (n = 25,000) por la barrera física de 495.88 GB de RAM.",
  },
  {
    rank: 3,
    factIds: "F-030 · F-037 · F-038 · F-040",
    title:
      "La ocupación específica ESCO (2,967 dummies) domina la predicción: KNN-W lidera (ROC-AUC = 0.7245), pero Logística y NB-H logran ~98 % de su precisión 100,000x más rápido",
    meaning:
      "Saber exactamente qué oficio ESCO ejerce una persona aporta 10 veces más poder predictivo sobre si repetirá que su educación o la duración aislada del puesto.",
    limit:
      "La inferencia exacta por fuerza bruta de KNN-W en Test tardó 29,146.8 s (~8.1 horas) frente a 0.283 s del HybridNaiveBayes (NB-H).",
  },
  {
    rank: 4,
    factIds: "F-027 · F-038",
    title:
      "Brecha sectorial de 26.4 puntos porcentuales en reincidencia: de 33.87 % en Servicios y Ventas (ISCO 5) a 7.61 % en Ocupaciones Militares (ISCO 0)",
    meaning:
      "La rotación horizontal repetitiva es propia de empleos operativos, comerciales y cortos (2–5 trim: 33.61 %), mientras que posgrados y directivos cambian de código ocupacional al moverse.",
    limit:
      "El gran grupo ISCO a 1 dígito o la educación por sí solos no bastan para clasificar personas individuales (Árbol 1 AUC = 0.5459; Árbol 2 AUC = 0.5208).",
  },
  {
    rank: 5,
    factIds: "F-032 · F-035",
    title:
      "Las competencias ESCO actúan como 'huella digital' del oficio (circularidad N:1): el Árbol 3 alcanza ROC-AUC = 0.6157 y Lift = 1.766x",
    meaning:
      "Un árbol poco profundo sobre conteos de competencias identifica indirectamente oficios masivos de alta rotación (como 3343.1 · administrative assistant, 86.2 % de la Hoja 16).",
    limit:
      "Las competencias no se midieron individualmente en cada persona; provienen del catálogo estándar ESCO v1.2.1 asignado a cada occupation_code.",
  },
  {
    rank: 6,
    factIds: "F-014 · F-032 · F-044",
    title:
      "El recorte IQR independiente (Versión B) rompe la suma E = C + K en 6.53 % de las filas, pero mejora la geometría euclidiana del clustering",
    meaning:
      "Conservar ambas versiones demostró que los modelos supervisados deben usar la Versión A (suma exacta E = C + K) y el clustering cuadrático se beneficia de la Versión B.",
    limit:
      "La regla IQR no se aplicó a dur_q porque truncar en 29.5 trimestres amputaría carreras estables reales (> 7 años) y sesgaría la media de 12.54 a 9.56 trimestres.",
  },
  {
    rank: 7,
    factIds: "F-010 · F-043 · F-044",
    title:
      "La omisión del nivel educativo (11.56 % de experiencias, 42,884 personas) es informativa (MNAR) y descubre un clúster propio (~11.66 %)",
    meaning:
      "Codificar una bandera binaria ortogonal (educacion_no_reportada = 1) en lugar de borrar filas o imputar 'educación cero' revela un segmento operativo estable.",
    limit:
      "En el cuaderno inicial 3.0 se codificó temporalmente como univ_ord = 0 antes de corregirse a bandera ortogonal + mediana en 7.0, 8.0 y 8.1.",
  },
  {
    rank: 8,
    factIds: "F-021 · F-023 · F-024 · F-049",
    title:
      "El 59.47 % de las transiciones tienen solapamiento temporal (gap <= 0 trimestres) y el 53.67 % de los empleos duran 2 o 5 trimestres",
    meaning:
      "La mediana real de duración es de 5.0 trimestres (frente a una media de 12.54 inflada por cola larga) con frecuente coexistencia de contratos en el mismo trimestre.",
    limit:
      "Los picos periódicos en 2, 5, 9, 13 y 17 trimestres reflejan el redondeo a años enteros (annual heaping) cuando las personas redactan su CV.",
  },
  {
    rank: 9,
    factIds: "F-020 · F-026 · F-028 · F-029",
    title:
      "Baja dimensión intrínseca: 3 a 4 componentes principales explican > 80 % de la varianza numérica y la auditoría eliminó 100 % de fuga",
    meaning:
      "El espacio continuo se resume en época/duración, volumen de competencias ESCO y orden del empleo; retirar veces_ese_oficio_rob/bin evitó una fuga trivial de PR-AUC = 1.0000.",
    limit:
      "PCA se utiliza como diagnóstico sobre las 11 variables continuas y no para comprimir las 2,967 dummies ocupacionales.",
  },
  {
    rank: 10,
    factIds: "F-048 · F-049",
    title:
      "Métodos Numéricos (MCO vs. Lagrange): extrapolar la duración lineal predice -4.96 trimestres en 2027 y Chebyshev-Lobatto reduce el error de Runge en 19.4x",
    meaning:
      "Demuestra con 1.64M de empleos cerrados por qué jamás debe extrapolarse una tendencia truncada por censura y cómo los nodos de Chebyshev eliminan oscilaciones espurias.",
    limit:
      "La caída lineal de duración 2000–2019 (-0.7926 trim/año) es un efecto mecánico de truncamiento por ventana de observación, no precarización laboral real.",
  },
];

export default async function OverviewPage() {
  const { funnel, cleaning, segments, topTransitions, pca } =
    await getOverviewData();

  return (
    <div className="space-y-8">
      {/* HERO: The Project in One Screen */}
      <section className="rounded-2xl border border-slate-200 bg-gradient-to-br from-slate-900 via-slate-900 to-blue-950 p-6 text-white shadow-lg sm:p-8">
        <div className="flex flex-col justify-between gap-6 lg:flex-row lg:items-center">
          <div className="max-w-3xl space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full bg-blue-500/20 px-3 py-1 text-xs font-semibold text-blue-200 ring-1 ring-blue-400/30">
              <span>Resumen Ejecutivo en Una Pantalla · UNIMINUTO Ibagué</span>
            </div>
            <h1 className="text-2xl font-extrabold tracking-tight sm:text-3xl">
              JobPath: ¿Cómo evolucionan las trayectorias laborales y qué predice que una persona vuelva a ejercer el mismo oficio?
            </h1>
            <p className="text-sm leading-relaxed text-slate-300">
              Estudio integral de minería de datos (CRISP-DM) y métodos numéricos sobre el censo clasificado de{" "}
              <strong className="text-white">352,093 trabajadores</strong> y{" "}
              <strong className="text-white">1,738,738 experiencias laborales</strong> del dataset público{" "}
              <strong className="text-amber-300">JobHop v2</strong> enriquecido con las{" "}
              <strong className="text-amber-300">2,973 ocupaciones y competencias ESCO v1.2.1</strong>.
              Consultado en tiempo real desde <strong>Neon PostgreSQL 18</strong> en modo estricto de solo lectura.
            </p>
            <div className="flex flex-wrap gap-3 pt-2">
              <Link
                href="/transparencia"
                className="inline-flex items-center gap-2 rounded-lg bg-amber-400 px-4 py-2 text-xs font-bold text-slate-950 shadow hover:bg-amber-300"
              >
                <ShieldCheck className="h-4 w-4" />
                Ver Transparencia Censal y Muestreo Ward (Vista Clave)
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
              <Link
                href="/explorador"
                className="inline-flex items-center gap-2 rounded-lg bg-white/10 px-4 py-2 text-xs font-semibold text-white ring-1 ring-white/25 hover:bg-white/20"
              >
                Explorar Trayectorias Reales por Persona
              </Link>
              <Link
                href="/metodos-numericos"
                className="inline-flex items-center gap-2 rounded-lg bg-white/10 px-4 py-2 text-xs font-semibold text-white ring-1 ring-white/25 hover:bg-white/20"
              >
                Simulador MCO vs. Lagrange
              </Link>
            </div>
          </div>

          {/* 4 Headline KPI Cards */}
          <div className="grid grid-cols-2 gap-3 sm:w-96 shrink-0">
            <div className="rounded-xl bg-white/10 p-3.5 ring-1 ring-white/15">
              <div className="flex items-center gap-1.5 text-xs text-blue-200">
                <Users className="h-4 w-4" />
                <span>Censo en Neon</span>
              </div>
              <div className="mt-1 text-xl font-extrabold text-white">
                352,093
              </div>
              <div className="text-[11px] text-slate-300">
                Personas (99.10% de limpias · ±0.00 pp error)
              </div>
            </div>

            <div className="rounded-xl bg-white/10 p-3.5 ring-1 ring-white/15">
              <div className="flex items-center gap-1.5 text-xs text-emerald-200">
                <Briefcase className="h-4 w-4" />
                <span>Experiencias ESCO</span>
              </div>
              <div className="mt-1 text-xl font-extrabold text-white">
                1,738,738
              </div>
              <div className="text-[11px] text-slate-300">
                92.93% de limpias · 1,643,772 cerradas
              </div>
            </div>

            <div className="rounded-xl bg-white/10 p-3.5 ring-1 ring-white/15">
              <div className="flex items-center gap-1.5 text-xs text-amber-200">
                <Repeat className="h-4 w-4" />
                <span>Reincidencia Ocup.</span>
              </div>
              <div className="mt-1 text-xl font-extrabold text-amber-300">
                45.30 %
              </div>
              <div className="text-[11px] text-slate-300">
                Personas con &ge;1 retorno (30.00% empleos)
              </div>
            </div>

            <div className="rounded-xl bg-white/10 p-3.5 ring-1 ring-white/15">
              <div className="flex items-center gap-1.5 text-xs text-purple-200">
                <Layers className="h-4 w-4" />
                <span>Mejor Modelo / K*</span>
              </div>
              <div className="mt-1 text-xl font-extrabold text-white">
                0.7245 AUC
              </div>
              <div className="text-[11px] text-slate-300">
                KNN-W en Test · k* = 4 arquetipos
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* TOP 10 HEADLINE RESULTS FROM FACTS.MD */}
      <section className="space-y-4">
        <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-end">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-blue-700">
              RESULTS FOCUS · Libro Mayor Verificado (FACTS.md v1.1)
            </span>
            <h2 className="text-xl font-bold text-slate-900">
              Los 10 Hallazgos Principales Verificados del Proyecto
            </h2>
          </div>
          <p className="text-xs text-slate-500">
            Cada tarjeta presenta el hallazgo cuantitativo, qué significa en lenguaje llano y su límite metodológico.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {TOP_10_HEADLINE_FACTS.map((item) => (
            <article
              key={item.rank}
              className="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
            >
              <div>
                <div className="mb-2 flex items-center justify-between gap-2">
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-700 px-2.5 py-0.5 text-xs font-bold text-white">
                    <Award className="h-3.5 w-3.5" />
                    Hallazgo #{item.rank}
                  </span>
                  <span className="rounded bg-slate-100 px-2 py-0.5 font-mono text-[11px] font-semibold text-slate-700">
                    {item.factIds}
                  </span>
                </div>
                <h3 className="text-sm font-bold leading-snug text-slate-900">
                  {item.title}
                </h3>
                <p className="mt-2 text-xs leading-relaxed text-slate-700">
                  <strong className="text-slate-900">¿Qué significa? </strong>
                  {item.meaning}
                </p>
              </div>
              <div className="mt-3 border-t border-slate-100 pt-2 text-[11px] leading-relaxed text-amber-900">
                <strong>Límite principal: </strong>
                {item.limit}
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* THE DATA JOURNEY (RAW -> CLEAN -> FEATURES -> MODELS) */}
      <section className="space-y-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-blue-700">
            El Viaje de los Datos (Raw &rarr; Clean &rarr; Features &rarr; Models)
          </span>
          <h2 className="text-xl font-bold text-slate-900">
            Trazabilidad Cuantitativa del Pipeline CRISP-DM en Neon
          </h2>
        </div>

        {/* 4-Step Visual Pipeline Banner */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="text-xs font-bold uppercase text-slate-500">
              Etapa 1 · Datos Crudos (01_raw)
            </div>
            <div className="mt-1 text-lg font-extrabold text-slate-900">
              1,993,291 filas
            </div>
            <div className="text-xs font-medium text-slate-600">
              355,315 personas · JobHop v2 + ESCO v1.2.1
            </div>
            <p className="mt-2 text-[11px] text-slate-500">
              Unión de particiones <code>train + test + val</code> de Hugging Face y cruce con 3,043 ocupaciones y 126,051 relaciones de competencias ESCO.
            </p>
          </div>

          <div className="rounded-xl border border-blue-200 bg-blue-50/40 p-4 shadow-sm">
            <div className="text-xs font-bold uppercase text-blue-700">
              Etapa 2 · Limpieza (2.0 · 03_processed)
            </div>
            <div className="mt-1 text-lg font-extrabold text-slate-900">
              1,871,014 filas
            </div>
            <div className="text-xs font-medium text-slate-600">
              355,308 personas (-6.13% filas depuradas)
            </div>
            <p className="mt-2 text-[11px] text-slate-600">
              Elimina 72,726 sin fechas, 11 años &gt; 2026, 37,553 duplicados exactos y 11,987 cierres parciales. Rescata 9,293 filas por oficio padre ESCO.
            </p>
          </div>

          <div className="rounded-xl border border-emerald-200 bg-emerald-50/40 p-4 shadow-sm">
            <div className="text-xs font-bold uppercase text-emerald-800">
              Etapa 3 · Transformación y PCA (3.0–4.1)
            </div>
            <div className="mt-1 text-lg font-extrabold text-slate-900">
              1,738,738 &times; 2,985 cols
            </div>
            <div className="text-xs font-medium text-slate-600">
              352,093 personas (Split 80/20 · 0 compartidas)
            </div>
            <p className="mt-2 text-[11px] text-slate-600">
              Filtra 132,276 filas sin oficio hoja ESCO. Construye 18 variables densas + 2,967 dummies ESCO; 3–4 componentes PCA explican &gt;80% de varianza.
            </p>
          </div>

          <div className="rounded-xl border border-purple-200 bg-purple-50/40 p-4 shadow-sm">
            <div className="text-xs font-bold uppercase text-purple-800">
              Etapa 4 · Modelos y Métodos (6.0–8.1 + MN)
            </div>
            <div className="mt-1 text-lg font-extrabold text-slate-900">
              15 Clasificadores + K*=4
            </div>
            <div className="text-xs font-medium text-slate-600">
              Censo en Neon (268.6 MiB) + MCO y Lagrange
            </div>
            <p className="mt-2 text-[11px] text-slate-600">
              Ablación de fuga en 6.0, CART 7.0, Naive Bayes 7.1, KNN 7.2, K-Means 8.0 (352k), Ward 8.1 (25k) y auditoría numérica RL-04 / LG-01.
            </p>
          </div>
        </div>

        {/* Charts Grid for View 1 */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <ChartCard
            factId="F-001 · F-011 · F-015 · F-017"
            sourceLabel="Tabla Neon: agg_inclusion_exclusion_funnel"
            badgeText="Censo 100% en Neon"
            badgeTone="blue"
            headline="El 99.10 % de las personas limpias (352,093 de 355,308) y el 92.93 % de las experiencias (1,738,738 de 1,871,014) entran al censo clasificado en Neon"
            whatAmISeeing="Comparación del volumen de experiencias laborales (barras de colores, eje izquierdo) y personas únicas (barras verde azulado, eje derecho) a través de las etapas del proyecto hasta la partición Train/Test y la submuestra Ward."
            primaryLimit="Las 132,276 experiencias excluidas del censo modelable carecen de código hoja en ESCO v1.2.1, por lo que incluirlas habría obligado a inventar competencias falsas igualadas a cero."
          >
            <DataJourneyFunnelChart funnel={funnel} />
          </ChartCard>

          <ChartCard
            factId="F-023 · F-024 · F-025"
            sourceLabel="Cuaderno 5.0 · Tabla Neon: agg_eda_distributions_and_segments"
            badgeText="352,093 Personas"
            badgeTone="emerald"
            headline="El 46.77 % de las personas clasificadas sigue una trayectoria exploradora pura, mientras que el 42.98 % consolida permanencia con retornos al mismo oficio"
            whatAmISeeing="Distribución porcentual de las 352,093 personas del censo clasificado según la tipología conductual de su carrera (exploradora sin retornos, permanente con alta repetición, sin transición con 1 empleo y mixta)."
            primaryLimit="La tipología resume toda la historia observada de la persona hasta el corte del CV (2026-Q1), por lo que trabajadores jóvenes con pocos empleos tienen menor ventana temporal para registrar retornos."
          >
            <TrajectorySegmentsChart segments={segments} />
          </ChartCard>

          <ChartCard
            factId="F-019 · F-020 · F-026"
            sourceLabel="Cuadernos 4.0 y 4.1 · Tabla Neon: agg_pca_variance_and_loadings"
            badgeText="Diagnóstico PCA (50k)"
            badgeTone="purple"
            headline="Solo 3 componentes principales en la Versión B (80.58 %) y 4 en la Versión A (87.76 %) capturan más del 80 % de la varianza de las 11 variables continuas"
            whatAmISeeing="Curvas de varianza explicada acumulada e individual de los primeros 5 componentes principales (PC1 a PC5) sobre la muestra de 50,000 experiencias en las Versiones A (con outliers) y B (winsorizada por IQR)."
            primaryLimit="El PCA diagnostica colinealidad en el bloque numérico denso (r = 1.000 entre start_ord y start_year; r = 0.952 entre essential y competence), pero no reemplaza a las 2,967 dummies ocupacionales."
          >
            <PcaVarianceChart pca={pca} />
          </ChartCard>

          <ChartCard
            factId="F-024 · F-031"
            sourceLabel="Cuaderno 5.0 · Tabla Neon: agg_top_occupation_transitions"
            badgeText="1,386,645 Transiciones"
            badgeTone="amber"
            headline="Las 11 transiciones consecutivas más frecuentes de todo el mercado laboral son autolazos (A → A), lideradas por Asistente Administrativo (16,350 transiciones)"
            whatAmISeeing="Ranking de las 10 transiciones ocupacionales consecutivas con mayor número de ocurrencias entre las 1,386,645 transiciones del censo clasificado, mostrando nombre del oficio y código ESCO."
            primaryLimit="El predominio de autolazos en el top nominal refleja tanto estabilidad en oficios masivos (administración, ventas, almacén) como cambios de contrato dentro de la misma profesión."
          >
            <TopTransitionsChart transitions={topTransitions} />
          </ChartCard>
        </div>
      </section>

      {/* BITÁCORA OFICIAL DE LIMPIEZA (8 ETAPAS DE 2.0) */}
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <div>
            <span className="font-mono text-xs font-bold text-blue-700">
              F-004 a F-014 · Tabla Neon: agg_cleaning_and_iqr_audit
            </span>
            <h2 className="text-base font-bold text-slate-900">
              Bitácora Oficial de las 8 Etapas de Limpieza y Auditoría IQR (Cuaderno 2.0)
            </h2>
          </div>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
            1,993,291 crudas &rarr; 1,871,014 limpias (-122,277 filas = -6.134%)
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-bold uppercase text-slate-600">
              <tr>
                <th className="px-3 py-2.5">Etapa</th>
                <th className="px-3 py-2.5">Columnas Auditadas</th>
                <th className="px-3 py-2.5 text-right">Filas Entrada</th>
                <th className="px-3 py-2.5 text-right">Afectadas</th>
                <th className="px-3 py-2.5 text-right">Eliminadas</th>
                <th className="px-3 py-2.5 text-right">Filas Salida</th>
                <th className="px-3 py-2.5">Acción y Justificación Metodológica</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {cleaning.map((row) => (
                <tr key={row.etapa} className="hover:bg-slate-50/80">
                  <td className="px-3 py-2.5 font-mono font-semibold text-slate-900">
                    {row.etapa}
                  </td>
                  <td className="px-3 py-2.5 font-mono text-[11px] text-slate-600">
                    {row.columna}
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono">
                    {Number(row.filas_antes).toLocaleString("es-CO")}
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono text-blue-700">
                    {Number(row.filas_afectadas).toLocaleString("es-CO")}
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono font-semibold text-rose-700">
                    {Number(row.filas_eliminadas) > 0
                      ? `-${Number(row.filas_eliminadas).toLocaleString("es-CO")}`
                      : "0"}
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono font-semibold text-emerald-800">
                    {Number(row.filas_despues).toLocaleString("es-CO")}
                  </td>
                  <td className="px-3 py-2.5 text-slate-700">
                    <strong className="text-slate-900">{row.accion}: </strong>
                    {row.justificacion}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
