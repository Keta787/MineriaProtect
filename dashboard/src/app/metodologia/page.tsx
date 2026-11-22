import React from "react";
import {
  BookOpenCheck,
  ShieldAlert,
  Scale,
  GitBranch,
  FileWarning,
  Lock,
  CheckCircle2,
} from "lucide-react";

const ARCHITECTURAL_DECISIONS = [
  {
    id: "DEC-01",
    phase: "1.0–2.0 · Enriquecimiento ESCO",
    decision:
      "Asignar competencias esenciales (prácticas y conocimientos) desde la taxonomía oficial ESCO v1.2.1 mediante el código de ocupación emparejado (occupation_code).",
    status: "VERIFIED",
    note:
      "Permite cuantificar exigencias cognitivas y prácticas en 1,738,738 empleos, con varianza intra-ocupación igual a cero por construcción.",
  },
  {
    id: "DEC-02",
    phase: "2.0 · Limpieza de Duplicados Parciales",
    decision:
      "Colapsar 11,987 fragmentos con igual (resume_id, start_date, matched_code) conservando el end_date más tardío, pero preservar 92,099 filas con igual fecha y distinto oficio (pluriempleo).",
    status: "INFERRED - confirm with team",
    note:
      "Se mantiene explícitamente la etiqueta INFERRED - confirm with team sobre la motivación de negocio de conservar el cierre más tardío.",
  },
  {
    id: "DEC-05",
    phase: "7.0–8.1 · Educación No Reportada (MNAR)",
    decision:
      "Reemplazar la codificación temprana univ_ord = 0 de 3.0 por una bandera binaria ortogonal educacion_no_reportada (0/1) más nivel_academico_ord_imputado (1..4 con mediana de Train = 2.0).",
    status: "VERIFIED",
    note:
      "Evita tratar la omisión del título universitario (11.56 % de filas) como 'educación inferior a secundaria' y descubre limpiamente el Clúster 1.",
  },
  {
    id: "DEC-06",
    phase: "2.0–8.1 · Dualidad Versión A vs. Versión B",
    decision:
      "Conservar la Versión A (con_outliers, identidad exacta E = C + K) para modelos supervisados y la Versión B (winsorizada por IQR k=1.5 en competencias, sin tocar dur_q) para clustering euclidiano.",
    status: "VERIFIED",
    note:
      "Evita que valores extremos (+6σ) distorsionen los centroides de K-Means/Ward sin romper la aditividad en árboles ni amputar carreras largas reales.",
  },
  {
    id: "DEC-07",
    phase: "3.0 · Partición GroupShuffleSplit 80/20",
    decision:
      "Particionar por persona completa (resume_id, seed = 42, 80 % Train = 281,674 personas / 20 % Test = 70,419 personas) tras filtrar las 132,276 filas sin oficio hoja ESCO.",
    status: "INFERRED - confirm with team",
    note:
      "La motivación del orden del filtro se mantiene como INFERRED - confirm with team, mientras que la disyunción exacta (0 personas compartidas entre Train y Test) está probada en código como hecho F-050 VERIFIED.",
  },
  {
    id: "DEC-09",
    phase: "1.0 vs. 6.0–7.2 · Evolución del Objetivo",
    decision:
      "Transición desde la formulación descriptiva inicial hacia la predicción supervisada del target binario reincide = (veces_ese_oficio > 1) combinada con segmentación k* = 4.",
    status: "INFERRED - confirm with team",
    note:
      "Se registra que docs/1.0_comprension_negocio.md quedó desactualizado respecto a los modelos supervisados 6.0–7.2 (no se edita ese archivo fuente histórico).",
  },
  {
    id: "DEC-14",
    phase: "8.1 · Submuestreo Estratificado Ward 25k",
    decision:
      "Ejecutar el enlace jerárquico directo de Ward sobre una muestra estratificada de n = 25,000 personas de Train (2.50 GB RAM) y marcar cluster_ward_25k_direct = NULL en las 327,093 personas restantes.",
    status: "VERIFIED",
    note:
      "La matriz condensada O(N²) para N = 352,093 personas requiere 495.88 GB de RAM en float64. El dashboard jamás presenta Ward directo como censo completo.",
  },
];

const METHODOLOGICAL_LIMITATIONS = [
  {
    num: 1,
    title: "Atribución de competencias por catálogo ESCO (Circularidad parcial N:1)",
    detail:
      "Las competencias esenciales, prácticas y conocimientos no fueron evaluadas mediante exámenes individuales a cada trabajador, sino imputadas desde el catálogo oficial ESCO v1.2.1 según el occupation_code. Por ello, la varianza intra-oficio es cero y los árboles de competencias (Árbol 3, ROC-AUC = 0.6157) actúan en parte como identificadores indirectos de oficios masivos (al agrupar CV por occupation_code, el AUC baja a 0.5422).",
  },
  {
    num: 2,
    title: "Censura por la derecha en 2026-Q1 y truncamiento de cohortes recientes",
    detail:
      "El 5.46 % de las experiencias clasificadas (94,966 empleos) seguía activo al corte del dataset (end_date = 'Present' → 2026-Q1). En los análisis de duración por año de inicio (IDEA-RL-04), los empleos cerrados iniciados cerca del corte sólo pudieron tener duraciones cortas, lo que explica la caída mecánica de mean_dur_q entre 2000 y 2019 (-0.7926 trim/año).",
  },
  {
    num: 3,
    title: "Redondeo anual en el reporte de fechas (Annual Heaping en 2, 5, 9, 13 trimestres)",
    detail:
      "El 53.67 % de las experiencias dura exactamente 2 trimestres (30.06 %) o 5 trimestres (23.61 %), con escalones periódicos cada 4 trimestres (múltiplos de 4k + 1). Esto ocurre porque muchos candidatos reportan sólo años calendario enteros en sus currículums, generando discontinuidades reales en la curva de supervivencia S(q).",
  },
  {
    num: 4,
    title: "Techo predictivo moderado en clasificación supervisada (ROC-AUC = 0.7245, F1 = 0.5471)",
    detail:
      "Incluso el mejor modelo del proyecto (KNN-W con 2,978 variables) alcanza un ROC-AUC de 0.7245 en Test porque la decisión humana de repetir o cambiar de oficio depende también de factores no observables en un CV público (salario ofrecido, clima organizacional, ubicación geográfica, motivos familiares o despidos).",
  },
  {
    num: 5,
    title: "Barrera física O(N²) en Clustering Jerárquico de Ward (495.88 GB RAM)",
    detail:
      "Mientras K-Means++ (8.0) escala linealmente O(N·k·d) y segmenta directamente a las 352,093 personas del censo, el algoritmo aglomerativo de Ward (8.1) sólo tiene etiquetas directas en la muestra estratificada de 25,000 personas de Train (7.10 % del censo).",
  },
  {
    num: 6,
    title: "Prohibición de extrapolación fuera del soporte empírico (MCO y Lagrange)",
    detail:
      "Tanto la regresión lineal MCO (que predice -4.96 trimestres en 2027) como el polinomio cúbico de Lagrange P₃(q) (que predice -59.84 % de supervivencia en q = 48) demuestran matemáticamente que ningún modelo polinómico debe usarse fuera del intervalo de datos observados.",
  },
];

export default function MetodologiaPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-blue-800 ring-1 ring-blue-200">
            <BookOpenCheck className="h-3.5 w-3.5" />
            Vista 6 · Metodología CRISP-DM, Limitaciones, Identificadores y Licencias Abiertas
          </span>
          <span className="font-mono text-xs text-slate-500">
            Auditoría Fases 0 a 3 · UNIMINUTO Ibagué
          </span>
        </div>
        <h1 className="mt-2 text-2xl font-extrabold text-slate-900">
          Gobernanza de Datos, Decisiones Metodológicas y Límites de Interpretación
        </h1>
        <p className="mt-1 text-xs leading-relaxed text-slate-600 sm:text-sm">
          Esta página documenta con transparencia las reglas metodológicas del estudio, el origen público de los identificadores{" "}
          <code>resume_id</code>, el estatus de las licencias abiertas <strong>CC BY 4.0</strong>, las decisiones con etiqueta{" "}
          <code>INFERRED - confirm with team</code> y los límites técnicos que todo jurado o visitante debe conocer al interpretar los resultados.
        </p>
      </section>

      {/* GOVERNANCE: RESUME_ID PROVENANCE & CC BY 4.0 LICENSES */}
      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-emerald-300 bg-emerald-50/40 p-5 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-bold uppercase text-emerald-900">
            <Scale className="h-4 w-4" />
            <span>Origen de resume_id y Privacidad (PII = 0)</span>
          </div>
          <h2 className="mt-1.5 text-base font-bold text-slate-900">
            Nota Obligatoria sobre el Identificador <code>resume_id</code>
          </h2>
          <p className="mt-2 text-xs leading-relaxed text-slate-700">
            Los identificadores numéricos <code>resume_id</code> (ej. <code>1, 10, 17, 47, 217</code>) que aparecen en la base de datos Neon y en el Explorador de Trayectorias{" "}
            <strong>
              provienen directamente y sin alteración del dataset público académico JobHop v2
            </strong>{" "}
            (publicado en Hugging Face bajo <code>aida-ugent/JobHop</code> por investigadores de{" "}
            <strong>VDAB y Ghent University, Bélgica</strong>).
          </p>
          <ul className="mt-3 list-disc space-y-1.5 pl-5 text-xs text-slate-700">
            <li>
              <strong>Sin datos personales (PII):</strong> El dataset original fue completamente anonimizado y pseudonimizado en origen antes de su liberación pública; no contiene nombres, documentos de identidad, empresas, correos ni ubicaciones exactas.
            </li>
            <li>
              <strong>Trazabilidad reproducible:</strong> Conservar el entero <code>resume_id</code> original calculado en Python permite verificar fila por fila la paridad del 100 % contra los archivos CSV de los cuadernos <code>2.0</code> a <code>8.1</code>.
            </li>
          </ul>
        </div>

        <div className="rounded-xl border border-blue-300 bg-blue-50/40 p-5 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-bold uppercase text-blue-900">
            <Lock className="h-4 w-4" />
            <span>Licencias Abiertas (CC BY 4.0) y Protección contra Descarga Masiva</span>
          </div>
          <h2 className="mt-1.5 text-base font-bold text-slate-900">
            Estatus Legal de JobHop v2 y ESCO v1.2.1
          </h2>
          <div className="mt-2 space-y-2 text-xs leading-relaxed text-slate-700">
            <p>
              <strong>1. JobHop v2 Dataset (VDAB / Ghent University — AI &amp; Data Lab):</strong>{" "}
              Distribuido públicamente para investigación bajo licencia{" "}
              <strong className="text-blue-900">
                Creative Commons Attribution 4.0 International (CC BY 4.0)
              </strong>
              . Exige atribución explícita a los autores originales del repositorio <code>aida-ugent/JobHop</code>.
            </p>
            <p>
              <strong>2. Taxonomía Europea ESCO v1.2.1 (Comisión Europea):</strong>{" "}
              Publicada bajo la Decisión de Reutilización de la Comisión Europea{" "}
              <code>2011/833/EU</code> compatible con{" "}
              <strong className="text-blue-900">CC BY 4.0</strong>. Exige indicar que las ocupaciones y relaciones de competencias provienen del catálogo oficial ESCO v1.2.1.
            </p>
            <p>
              <strong>3. Medidas de Gobernanza en este Dashboard (Candidato C):</strong>{" "}
              Dado que Neon aloja el censo clasificado completo (<code>352,093</code> personas / <code>1,738,738</code> experiencias), la aplicación se mantiene como{" "}
              <strong>despliegue Preview académico</strong>, se conecta exclusivamente en servidor mediante el rol de solo lectura{" "}
              <code>jobpath_readonly</code> y{" "}
              <strong>
                prohíbe cualquier endpoint de listado masivo o descarga bulk (todas las consultas individuales imponen <code>LIMIT &le; 25</code>)
              </strong>
              .
            </p>
          </div>
        </div>
      </section>

      {/* 6 CORE LIMITATIONS */}
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4 flex items-center gap-2">
          <ShieldAlert className="h-5 w-5 text-amber-600" />
          <div>
            <span className="font-mono text-xs font-bold text-amber-800">
              RESULTS FOCUS · Honestidad Científica
            </span>
            <h2 className="text-base font-bold text-slate-900">
              Las 6 Limitaciones Metodológicas Principales del Estudio
            </h2>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {METHODOLOGICAL_LIMITATIONS.map((lim) => (
            <div
              key={lim.num}
              className="rounded-xl border border-slate-200 bg-slate-50/70 p-4"
            >
              <div className="flex items-center gap-2">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-amber-500 font-mono text-xs font-bold text-slate-950">
                  {lim.num}
                </span>
                <h3 className="text-xs font-bold text-slate-900 sm:text-sm">
                  {lim.title}
                </h3>
              </div>
              <p className="mt-2 text-xs leading-relaxed text-slate-700">
                {lim.detail}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ARCHITECTURAL & METHODOLOGICAL DECISIONS (DEC-01 .. DEC-14 WITH INFERRED LABELS PRESERVED) */}
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <GitBranch className="h-5 w-5 text-blue-700" />
            <div>
              <span className="font-mono text-xs font-bold text-blue-700">
                Libro de Decisiones · docs/handoff/DECISIONS.md
              </span>
              <h2 className="text-base font-bold text-slate-900">
                Trazabilidad de Decisiones Clave y Etiquetas <code>INFERRED - confirm with team</code>
              </h2>
            </div>
          </div>
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-3 py-1 font-mono text-[11px] font-bold text-amber-950">
            <FileWarning className="h-3.5 w-3.5" />
            Nota DEC-09: 1.0_comprension_negocio.md desactualizado frente a modelos supervisados (conservado sin editar)
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-bold uppercase text-slate-600">
              <tr>
                <th className="px-3 py-2.5">ID</th>
                <th className="px-3 py-2.5">Fase / Cuaderno</th>
                <th className="px-3 py-2.5">Decisión Adoptada</th>
                <th className="px-3 py-2.5">Estatus de Confirmación</th>
                <th className="px-3 py-2.5">Implicación y Verificación en Código</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {ARCHITECTURAL_DECISIONS.map((d) => {
                const isInferred = d.status.includes("INFERRED");
                return (
                  <tr
                    key={d.id}
                    className={
                      isInferred ? "bg-amber-50/40" : "hover:bg-slate-50"
                    }
                  >
                    <td className="px-3 py-2.5 font-mono font-bold text-slate-900">
                      {d.id}
                    </td>
                    <td className="px-3 py-2.5 font-medium text-slate-700">
                      {d.phase}
                    </td>
                    <td className="px-3 py-2.5 text-slate-900">{d.decision}</td>
                    <td className="px-3 py-2.5">
                      <span
                        className={`inline-flex items-center gap-1 rounded px-2 py-0.5 font-mono text-[10px] font-bold ${
                          isInferred
                            ? "bg-amber-200 text-amber-950"
                            : "bg-emerald-100 text-emerald-900"
                        }`}
                      >
                        {!isInferred && <CheckCircle2 className="h-3 w-3" />}
                        {d.status}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-slate-700">{d.note}</td>
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
