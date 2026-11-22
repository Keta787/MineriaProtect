import React from "react";
import { getModelsAndClusteringData } from "@/lib/db";
import { ChartCard } from "@/components/ChartCard";
import {
  SupervisedBenchmarkChart,
  NaiveBayesIscoTrainVsTestChart,
  KnnPurityGeometryChart,
  ClusteringTrainVsTestComparisonChart,
} from "@/components/ModelsCharts";
import {
  BrainCircuit,
  AlertTriangle,
  CheckCircle2,
  Layers,
  Gauge,
} from "lucide-react";

export const dynamic = "force-dynamic";

const TRAIN_CV_VS_TEST_SUPERVISED_SUMMARY = [
  {
    family: "6.0 · Modelado Base (Techo Lineal)",
    model: "Regresión Logística Regularizada OHE (2,981 cols · Versión A)",
    trainMetric: "CV 5-Fold PR-AUC = 0.5113 ± 0.0029 · ROC-AUC = 0.7132 · F1 = 0.5340",
    testMetric: "Test PR-AUC = 0.5109 · ROC-AUC = 0.7133 · F1 = 0.5321 · Acc = 0.6760",
    fitPredictTime: "Fit: ~4.2 s · Predict Test: < 0.15 s",
    plainReading:
      "Cero sobreajuste entre Train CV y Test (diferencia de 0.0001 en ROC-AUC). Demuestra que las 2,967 dummies de oficio ESCO aportan una señal lineal estable.",
  },
  {
    family: "6.0 · Boosting Denso (Sin Dummies ESCO)",
    model: "HistGradientBoosting (14 cols densas · balanced)",
    trainMetric: "CV 5-Fold PR-AUC = 0.4954 · ROC-AUC = 0.6938 · F1 = 0.5155",
    testMetric: "Test PR-AUC = 0.4951 · ROC-AUC = 0.6936 · F1 = 0.5151",
    fitPredictTime: "Fit: ~18.5 s · Predict Test: ~0.45 s",
    plainReading:
      "Aun con árboles no lineales sobre las 14 variables continuas, perder el código exacto de oficio ESCO reduce el ROC-AUC en -2.0 puntos frente a la Logística OHE.",
  },
  {
    family: "7.0 · Árboles de Decisión CART",
    model: "Árbol 1 (ISCO 1D) / Árbol 2 (Educación) / Árbol 3 (Skills ESCO, prof=4)",
    trainMetric: "Árbol 3 Train Acc = 0.6113 (bal) / 0.7048 (None) · CV ROC-AUC = 0.6183",
    testMetric: "Árbol 3 Test Acc = 0.6107 (bal) · ROC-AUC = 0.6157 · Hoja 16 Lift = 1.766x",
    fitPredictTime: "Fit: < 1.0 s · Predict Test: < 0.05 s",
    plainReading:
      "ISCO 1D (AUC 0.5459) y Educación (AUC 0.5208) no separan individuos por sí solos. Las competencias ESCO sí alcanzan Lift = 1.766x porque actúan como huella digital del oficio (circularidad N:1).",
  },
  {
    family: "7.1 · Naive Bayes Híbrido",
    model: "HybridNaiveBayes NB-H (Gaussiano denso + Bernoulli 2,967 oficios, τ*=0.265)",
    trainMetric: "OOF Train PR-AUC = 0.4981 · ROC-AUC = 0.7061 · F1 = 0.5342",
    testMetric: "Test PR-AUC = 0.4962 · ROC-AUC = 0.7058 · F1 = 0.5337 · Brier = 0.1871",
    fitPredictTime: "Fit: 1.42 s · Predict Test (347,720 filas): 0.283 s",
    plainReading:
      "Alcanza el 98.9 % del ROC-AUC de la Logística y el 97.4 % de KNN-W en menos de 0.3 segundos, con la mejor calibración probabilística rápida (Brier = 0.1871).",
  },
  {
    family: "7.2 · K-Vecinos Más Cercanos Ponderado",
    model: "KNN-W (k = 101, distancia coseno/euclidiana con peso ocupacional w = 8.0)",
    trainMetric: "OOF Validación PR-AUC = 0.5239 · ROC-AUC = 0.7241 · F1 = 0.5468",
    testMetric: "Test PR-AUC = 0.5247 · ROC-AUC = 0.7245 · F1 = 0.5471 · Brier = 0.1817",
    fitPredictTime: "Inferencia fuerza bruta en Test: 29,146.83 s (~8.10 horas)",
    plainReading:
      "Mejor clasificador absoluto del proyecto al combinar cercanía en el oficio ESCO con similitud en trayectoria y duración, pero su costo O(N·M) exige indexación aproximada en producción.",
  },
];

export default async function ModelosPage() {
  const {
    supervisedBenchmark,
    decisionTrees,
    naiveBayesIsco,
    knnPurity,
    clusteringExec,
    kmeansProfiles,
    ward25kProfiles,
  } = await getModelsAndClusteringData();

  const dtVersionA = decisionTrees.filter((r) =>
    r.version_datos.includes("Versión A")
  );
  const kmPersons = kmeansProfiles.filter((r) =>
    r.vista.toLowerCase().includes("personas")
  );

  return (
    <div className="space-y-8">
      {/* Header */}
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-blue-800 ring-1 ring-blue-200">
            <BrainCircuit className="h-3.5 w-3.5" />
            Vista 4 · Modelos Supervisados (6.0–7.2) y Clustering No Supervisado (8.0–8.1)
          </span>
          <span className="font-mono text-xs font-semibold text-emerald-800">
            Métricas Train (281,674 pers.) y Test (70,419 pers.) reportadas por separado
          </span>
        </div>
        <h1 className="mt-2 text-2xl font-extrabold text-slate-900">
          ¿Qué tan bien podemos predecir la reincidencia ocupacional y cuáles son los 4 arquetipos reales del mercado laboral?
        </h1>
        <p className="mt-1 text-xs leading-relaxed text-slate-600 sm:text-sm">
          Todos los modelos supervisados se entrenaron exclusivamente sobre la partición{" "}
          <strong>Train (1,391,018 experiencias / 281,674 personas)</strong> usando validación cruzada agrupada por persona (<code>StratifiedGroupKFold</code>, 0 fuga de identidad) y se evaluaron una sola vez sobre la partición retenida{" "}
          <strong>Test (347,720 experiencias / 70,419 personas)</strong>.
        </p>
      </section>

      {/* Train vs Test Executive Comparison Table (Supervised 6.0 - 7.2) */}
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div>
            <span className="font-mono text-xs font-bold text-blue-700">
              F-029 · F-030 · F-033 a F-041 · Separación Explícita Train (CV) vs. Test
            </span>
            <h2 className="text-base font-bold text-slate-900">
              Síntesis Comparativa de las 4 Familias Supervisadas (Train CV vs. Test Retenido)
            </h2>
          </div>
          <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-900 ring-1 ring-emerald-200">
            0 columnas con fuga (veces_ese_oficio excluida de X)
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-bold uppercase text-slate-600">
              <tr>
                <th className="px-3 py-2.5">Cuaderno / Familia</th>
                <th className="px-3 py-2.5">Modelo Ganador</th>
                <th className="bg-blue-50/70 px-3 py-2.5 text-blue-950">
                  Métricas en Train (Validación Cruzada / OOF)
                </th>
                <th className="bg-emerald-50/70 px-3 py-2.5 text-emerald-950">
                  Métricas en Test (347,720 empleos / 70,419 pers.)
                </th>
                <th className="px-3 py-2.5">Costo Computacional</th>
                <th className="px-3 py-2.5">Lectura en Lenguaje Sencillo</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {TRAIN_CV_VS_TEST_SUPERVISED_SUMMARY.map((row) => (
                <tr key={row.family} className="hover:bg-slate-50">
                  <td className="px-3 py-2.5 font-bold text-slate-900">
                    {row.family}
                  </td>
                  <td className="px-3 py-2.5 font-medium text-slate-800">
                    {row.model}
                  </td>
                  <td className="bg-blue-50/30 px-3 py-2.5 font-mono text-[11px] text-blue-950">
                    {row.trainMetric}
                  </td>
                  <td className="bg-emerald-50/30 px-3 py-2.5 font-mono text-[11px] font-semibold text-emerald-950">
                    {row.testMetric}
                  </td>
                  <td className="px-3 py-2.5 font-mono text-[11px] text-slate-600">
                    {row.fitPredictTime}
                  </td>
                  <td className="px-3 py-2.5 text-slate-700">
                    {row.plainReading}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Supervised Charts Grid */}
      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ChartCard
          factId="F-030 · F-037 · F-040"
          sourceLabel="Tabla Neon: agg_supervised_models_benchmark (Cuadernos 6.0 a 7.2)"
          badgeText="Benchmark Unificado Test"
          badgeTone="blue"
          headline="KNN-W ponderado por oficio alcanza el mayor poder discriminante en Test (ROC-AUC = 0.7245, PR-AUC = 0.5247, F1 = 0.5471), seguido por Logística OHE (0.7133) y HybridNaiveBayes (0.7058)"
          whatAmISeeing="Comparación en el conjunto Test (347,720 experiencias) de las tres métricas principales (ROC-AUC en azul, F1 de la clase reincidente en esmeralda y PR-AUC en ámbar) para los modelos de los cuadernos 6.0, 7.0, 7.1 y 7.2."
          primaryLimit="El techo predictivo (~0.725 ROC-AUC) está acotado porque el CV público no incluye salario, satisfacción laboral, ubicación geográfica de la empresa ni motivo de término del contrato."
        >
          <SupervisedBenchmarkChart rows={supervisedBenchmark} />
        </ChartCard>

        <ChartCard
          factId="F-027 · F-038"
          sourceLabel="Cuaderno 7.1 · Tabla Neon: agg_naive_bayes_isco_rates"
          badgeText="Train vs. Test por Sector ISCO"
          badgeTone="emerald"
          headline="La tasa de reincidencia varía en 26.26 puntos porcentuales entre sectores ISCO (33.87 % en Servicios/Ventas vs. 7.61 % en Militares), con paridad casi exacta entre Train, Test y la predicción NB-H"
          whatAmISeeing="Tasa real de reincidencia observada en Train (azul claro) frente a la tasa confirmada en Test (esmeralda) y la probabilidad media estimada por el modelo HybridNaiveBayes NB-H en Test (púrpura) para cada Gran Grupo ISCO."
          primaryLimit="Aunque las tasas medias por sector ISCO están perfectamente calibradas, dentro de cada gran grupo coexisten cientos de oficios con dinámicas distintas, por lo que el modelo necesita las 2,967 dummies ESCO para clasificar individuos."
        >
          <NaiveBayesIscoTrainVsTestChart rows={naiveBayesIsco} />
        </ChartCard>

        <ChartCard
          factId="F-039 · F-040"
          sourceLabel="Cuaderno 7.2 · Tabla Neon: agg_knn_neighbor_purity"
          badgeText="Geometría KNN (k = 51)"
          badgeTone="purple"
          headline="Al elevar el peso del bloque ocupacional ESCO de w = 0 (KNN-D) a w = 4.0 (KNN-W), la pureza de vecinos del mismo oficio sube de 10.64 % a 76.23 % y la pureza de clase llega a 61.50 %"
          whatAmISeeing="Evolución del porcentaje de los k = 51 vecinos más cercanos que comparten exactamente la misma ocupación ESCO (azul), el mismo gran grupo ISCO (esmeralda) y el mismo valor del target reincide (ámbar) al aumentar el peso w."
          primaryLimit="En alta dimensión (2,978 columnas), sin ponderar el bloque ocupacional (w = 0 o w = 0.25), la distancia euclidiana es dominada por las variables continuas y mezcla vecinos de oficios inconexos."
        >
          <KnnPurityGeometryChart rows={knnPurity} />
        </ChartCard>

        {/* Decision Trees 7.0 Train vs Test Table Card */}
        <div className="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div>
            <div className="mb-2 flex items-center justify-between">
              <span className="rounded bg-slate-100 px-2 py-0.5 font-mono text-[11px] font-semibold text-slate-800">
                F-033 · F-034 · F-035 · Tabla Neon: agg_decision_trees_comparison
              </span>
              <span className="rounded-full bg-amber-50 px-2.5 py-0.5 text-[11px] font-semibold text-amber-900 ring-1 ring-amber-300">
                Cuaderno 7.0 · CART
              </span>
            </div>
            <h3 className="text-base font-bold text-slate-900">
              Diagnóstico de los 3 Árboles de Decisión (7.0 · Versión A): Exactitud Train vs. Test y Lift de Hojas
            </h3>
            <p className="mt-1 text-xs text-slate-600">
              Prueba de hipótesis por bloques: ¿Basta el grupo ISCO (Árbol 1), el nivel educativo (Árbol 2) o el perfil de competencias ESCO (Árbol 3) para separar a quienes reinciden?
            </p>

            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-slate-200 bg-slate-50 text-[10px] font-bold uppercase text-slate-600">
                  <tr>
                    <th className="px-2 py-2">Modelo CART (Versión A)</th>
                    <th className="bg-blue-50 px-2 py-2 text-right">Train Acc</th>
                    <th className="bg-emerald-50 px-2 py-2 text-right">Test Acc</th>
                    <th className="px-2 py-2 text-right">Test F1</th>
                    <th className="px-2 py-2 text-right">Test AUC</th>
                    <th className="px-2 py-2 text-right">Máx Lift</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {dtVersionA.map((r) => (
                    <tr key={r.modelo_corto} className="hover:bg-slate-50">
                      <td className="px-2 py-1.5 font-medium text-slate-900">
                        {r.modelo_corto}
                      </td>
                      <td className="bg-blue-50/40 px-2 py-1.5 text-right font-mono">
                        {r.train_accuracy !== null
                          ? `${(Number(r.train_accuracy) * 100).toFixed(2)}%`
                          : "—"}
                      </td>
                      <td className="bg-emerald-50/40 px-2 py-1.5 text-right font-mono font-semibold">
                        {(Number(r.test_accuracy) * 100).toFixed(2)}%
                      </td>
                      <td className="px-2 py-1.5 text-right font-mono">
                        {Number(r.test_f1_clase_1).toFixed(4)}
                      </td>
                      <td className="px-2 py-1.5 text-right font-mono font-bold text-blue-800">
                        {Number(r.test_roc_auc).toFixed(4)}
                      </td>
                      <td className="px-2 py-1.5 text-right font-mono">
                        {r.max_lift_hoja_soporte_05pct
                          ? `${Number(r.max_lift_hoja_soporte_05pct).toFixed(3)}x`
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="mt-3 rounded-lg bg-amber-50/80 p-2.5 text-xs text-amber-950 ring-1 ring-amber-200">
            <strong>Hallazgo de circularidad parcial N:1 (F-035):</strong> El Árbol 3 (Competencias ESCO) es el único que supera el criterio <code>Lift &ge; 1.50x</code> (<code>1.766x</code> en su Hoja 16, tasa Test <code>52.94%</code>), pero el <code>86.2%</code> de esa hoja pertenece a un único oficio (<code>3343.1 · administrative assistant</code>). Al validar agrupando por código de ocupación (<code>GroupKFold</code> por <code>occupation_code</code>), su ROC-AUC cae de <code>0.6183</code> a <code>0.5422</code>.
          </div>
        </div>
      </section>

      {/* UNSUPERVISED CLUSTERING SECTION (8.0 K-MEANS FULL CENSUS VS 8.1 WARD 25K SAMPLE) */}
      <section className="space-y-4">
        <div className="rounded-2xl border-2 border-purple-300 bg-purple-50/50 p-5">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-purple-800 px-3 py-0.5 text-xs font-bold text-white">
              Regla de Transparencia de Alcance · Clustering 8.0 vs. 8.1
            </span>
            <span className="font-mono text-xs font-bold text-purple-950">
              K-Means++ (8.0) = 352,093 personas (100% Censo) | Ward Directo (8.1) = 25,000 personas de Train (7.10%)
            </span>
          </div>
          <p className="mt-2 text-xs leading-relaxed text-slate-800 sm:text-sm">
            <strong>Advertencia metodológica obligatoria:</strong> Los resultados de{" "}
            <strong>K-Means++ (Cuaderno 8.0)</strong> cubren la totalidad del censo clasificado (ajustado en las 281,674 personas de <code>Train</code> y evaluado en las 70,419 personas de <code>Test</code>). En cambio, el clustering jerárquico aglomerativo de{" "}
            <strong>Ward (Cuaderno 8.1)</strong> sólo pudo ajustarse directamente sobre una{" "}
            <strong>muestra estratificada de n = 25,000 personas de Train (7.10 % del censo, 2.50 GB RAM)</strong> porque la matriz de distancias condensada para N = 352,093 personas exige{" "}
            <strong>495.88 GB de RAM</strong> (<code className="rounded bg-white px-1">O(N²)</code>). Nunca deben interpretarse las etiquetas directas de Ward como un ajuste directo sobre todo el censo.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <ChartCard
            factId="F-042 · F-043 · F-044"
            sourceLabel="Tablas Neon: agg_kmeans_full_profiles y agg_ward_25k_profiles"
            badgeText="Train vs. Test (k* = 4)"
            badgeTone="purple"
            headline="Las proporciones de los 4 clústeres de K-Means son idénticas entre Train (281,674 personas) y Test (70,419 personas) con desviación menor a 0.21 pp, y concuerdan con Ward 25k (ARI = 0.6502)"
            whatAmISeeing="Comparación del tamaño porcentual de cada uno de los 4 arquetipos laborales en K-Means Train (azul), K-Means Test (esmeralda) y la muestra directa de descubrimiento Ward de 25,000 personas (púrpura)."
            primaryLimit="En Ward n = 25,000, el Clúster 2 absorbe un 47.70 % de la muestra (frente a 27.95 % en K-Means Train) porque el enlace jerárquico aglomerativo forma una frontera no esférica más amplia para perfiles técnico-profesionales."
          >
            <ClusteringTrainVsTestComparisonChart
              kmeansProfiles={kmeansProfiles}
              ward25kProfiles={ward25kProfiles}
            />
          </ChartCard>

          {/* Executive Side-by-Side Matrix (8.0 vs 8.1) */}
          <div className="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div>
              <span className="font-mono text-xs font-bold text-purple-800">
                F-044 · Tabla Neon: agg_clustering_executive_comparison
              </span>
              <h3 className="mt-1 text-base font-bold text-slate-900">
                Matriz Ejecutiva Cara a Cara: K-Means 8.0 (352k) vs. Ward 8.1 (Muestras 3k y 25k)
              </h3>
              <div className="mt-3 space-y-3">
                {clusteringExec.map((row) => (
                  <div
                    key={row.cluster}
                    className="rounded-lg border border-slate-200 bg-slate-50/70 p-3 text-xs"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="font-bold text-slate-900">
                        {row.cluster} · {row.perfil_comportamental}
                      </span>
                      <span className="font-mono text-[11px] font-semibold text-blue-800">
                        K-Means: {row.kmeans_8_0_tamano_y_reincide}
                      </span>
                    </div>
                    <div className="mt-1 flex flex-wrap gap-3 font-mono text-[11px] text-purple-900">
                      <span>Ward 25k (Proy.): {row.ward_8_1_n25000_tamano_y_reincide}</span>
                      <span>|</span>
                      <span>Ward 3k: {row.ward_8_1_n3000_tamano_y_reincide}</span>
                    </div>
                    <p className="mt-1.5 text-[11px] leading-relaxed text-slate-700">
                      {row.patron_reaccion_y_explicacion_es}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Detailed K-Means 8.0 Train vs Test Profiles Table & Ward 25k Direct Sample Table */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <span className="font-mono text-xs font-bold text-blue-700">
            F-042 · F-043 · Tabla Neon: agg_kmeans_full_profiles (Personas N = 352,093 · Train vs. Test Separados)
          </span>
          <h3 className="mt-1 text-base font-bold text-slate-900">
            Retrato Robot de K-Means++ (8.0) en el Censo Completo: Métricas Separadas en Train (281,674) y Test (70,419)
          </h3>

          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-bold uppercase text-slate-600">
                <tr>
                  <th className="px-2.5 py-2">Clúster y Arquetipo</th>
                  <th className="bg-blue-50 px-2.5 py-2 text-right">Personas Train (%)</th>
                  <th className="bg-emerald-50 px-2.5 py-2 text-right">Personas Test (%)</th>
                  <th className="px-2.5 py-2 text-right">Empleos (Tr / Te)</th>
                  <th className="px-2.5 py-2 text-right">Amplitud Trim (Tr / Te)</th>
                  <th className="px-2.5 py-2 text-right">Conocimientos K (Tr / Te)</th>
                  <th className="bg-blue-50 px-2.5 py-2 text-right">Reincidencia Train</th>
                  <th className="bg-emerald-50 px-2.5 py-2 text-right">Reincidencia Test</th>
                  <th className="px-2.5 py-2">Acción Recomendada Observatorio</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {kmPersons.map((r) => (
                  <tr key={r.cluster} className="hover:bg-slate-50">
                    <td className="px-2.5 py-2.5 font-semibold text-slate-900">
                      C{r.cluster} · {r.nombre_segmento_es}
                      <div className="font-normal text-[11px] text-slate-500">
                        ISCO modal: {r.gran_grupo_isco_dominante_posthoc}
                      </div>
                    </td>
                    <td className="bg-blue-50/30 px-2.5 py-2.5 text-right font-mono">
                      {Number(r.n_train).toLocaleString("es-CO")} ({r.pct_train}%)
                    </td>
                    <td className="bg-emerald-50/30 px-2.5 py-2.5 text-right font-mono font-semibold">
                      {Number(r.n_test).toLocaleString("es-CO")} ({r.pct_test}%)
                    </td>
                    <td className="px-2.5 py-2.5 text-right font-mono">
                      {r.n_jobs_media_train} / {r.n_jobs_media_test}
                    </td>
                    <td className="px-2.5 py-2.5 text-right font-mono">
                      {r.span_q_media_train} / {r.span_q_media_test}q
                    </td>
                    <td className="px-2.5 py-2.5 text-right font-mono">
                      {r.mean_skills_knowledge_media_train} /{" "}
                      {r.mean_skills_knowledge_media_test}
                    </td>
                    <td className="bg-blue-50/30 px-2.5 py-2.5 text-right font-mono">
                      {r.tasa_reincide_train_posthoc_pct}% ({r.lift_reincide_train_posthoc}x)
                    </td>
                    <td className="bg-emerald-50/30 px-2.5 py-2.5 text-right font-mono font-bold text-emerald-900">
                      {r.tasa_reincide_test_posthoc_pct}% ({r.lift_reincide_test_posthoc}x)
                    </td>
                    <td className="px-2.5 py-2.5 text-[11px] text-slate-700">
                      {r.accion_observatorio_recomendada_es}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Ward 25k Direct Discovery Sample Table */}
        <div className="rounded-xl border border-purple-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <span className="font-mono text-xs font-bold text-purple-800">
                F-044 · Tabla Neon: agg_ward_25k_profiles (Muestra Directa de Descubrimiento n = 25,000 Personas de Train)
              </span>
              <h3 className="mt-1 text-base font-bold text-slate-900">
                Perfiles del Clustering Jerárquico de Ward (8.1): Muestra Directa (n = 25,000 Train) vs. Proyección por Centroide
              </h3>
            </div>
            <span className="rounded bg-purple-100 px-2.5 py-1 font-mono text-xs font-bold text-purple-900">
              Ajuste directo exclusivo en n = 25,000 (in_ward_25k_sample = TRUE)
            </span>
          </div>

          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-200 bg-purple-50/60 text-[11px] font-bold uppercase text-purple-950">
                <tr>
                  <th className="px-2.5 py-2">Clúster Ward (8.1)</th>
                  <th className="bg-purple-100/70 px-2.5 py-2 text-right">
                    Muestra Directa Train (n = 25,000)
                  </th>
                  <th className="px-2.5 py-2 text-right">
                    Proyección NearestCentroid Test (70,419)
                  </th>
                  <th className="px-2.5 py-2 text-right">Empleos (Muestra)</th>
                  <th className="px-2.5 py-2 text-right">Amplitud (Muestra)</th>
                  <th className="px-2.5 py-2 text-right">Dur. Media (Muestra)</th>
                  <th className="bg-purple-100/70 px-2.5 py-2 text-right">
                    Reincidencia Muestra 25k
                  </th>
                  <th className="px-2.5 py-2 text-right">
                    Reincidencia Test Proyectado
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {ward25kProfiles.map((r) => (
                  <tr key={r.cluster} className="hover:bg-purple-50/20">
                    <td className="px-2.5 py-2.5 font-semibold text-slate-900">
                      Ward C{r.cluster} · {r.nombre_segmento_es}
                      <div className="font-normal text-[11px] text-slate-500">
                        ISCO dominante: {r.gran_grupo_isco_dominante_posthoc}
                      </div>
                    </td>
                    <td className="bg-purple-50/50 px-2.5 py-2.5 text-right font-mono font-bold text-purple-950">
                      {Number(r.n_muestra_descubrimiento).toLocaleString("es-CO")} (
                      {r.pct_muestra_descubrimiento}%)
                    </td>
                    <td className="px-2.5 py-2.5 text-right font-mono text-slate-700">
                      {Number(r.n_test_proyectado).toLocaleString("es-CO")} (
                      {r.pct_test_proyectado}%)
                    </td>
                    <td className="px-2.5 py-2.5 text-right font-mono">
                      {r.n_jobs_media_muestra}
                    </td>
                    <td className="px-2.5 py-2.5 text-right font-mono">
                      {r.span_q_media_muestra} trim
                    </td>
                    <td className="px-2.5 py-2.5 text-right font-mono">
                      {r.dur_mean_media_muestra} trim
                    </td>
                    <td className="bg-purple-50/50 px-2.5 py-2.5 text-right font-mono font-semibold text-purple-950">
                      {r.tasa_reincide_muestra_posthoc_pct}% (
                      {r.lift_reincide_muestra_posthoc}x)
                    </td>
                    <td className="px-2.5 py-2.5 text-right font-mono text-emerald-900">
                      {r.tasa_reincide_test_posthoc_pct}% (
                      {r.lift_reincide_test_posthoc}x)
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  );
}
