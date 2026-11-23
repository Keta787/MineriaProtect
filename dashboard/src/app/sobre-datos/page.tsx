import React from "react";
import Link from "next/link";
import { getAboutDataLive } from "@/lib/db";
import { Database, ShieldCheck, Scale, ArrowLeft } from "lucide-react";

export const dynamic = "force-dynamic";

/**
 * Panel breve "Sobre estos datos".
 * Todos los números provienen en vivo de Neon (`agg_inclusion_exclusion_funnel` y `esco_occupations_catalog`).
 * Deliberadamente NO contiene hallazgos del proyecto, resultados de modelos ni métodos numéricos.
 */
export default async function SobreDatosPage() {
  const data = await getAboutDataLive();

  const excludedRows = data.funnel.filter((r) =>
    r.status_in_neon.includes("EXCLUDED")
  );
  const rawRow = data.funnel.find((r) => r.stage_code === "raw_jobhop_v2");
  const cleanRow = data.funnel.find(
    (r) => r.stage_code === "clean_master_dataset"
  );

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <Link
          href="/"
          className="inline-flex items-center gap-1 text-xs font-bold text-blue-700 hover:underline"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Volver al Explorador de Datos
        </Link>

        <h1 className="mt-2 text-2xl font-extrabold text-slate-900">
          Sobre estos datos
        </h1>
        <p className="mt-1 max-w-3xl text-sm text-slate-600">
          Resumen breve y verificable de la cobertura de datos consultados en vivo por este explorador interactivo (sin conclusiones ni resultados de modelos; esos resultados pertenecen a la presentación).
        </p>

        {/* Live Coverage Counters */}
        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-xl border border-blue-200 bg-blue-50/40 p-4">
            <div className="text-xs font-bold uppercase text-blue-800">
              Incluido en Neon (Censo)
            </div>
            <div className="mt-1 text-2xl font-extrabold text-slate-900">
              {data.totalPersonsCount.toLocaleString("es-CO")} personas
            </div>
            <div className="text-xs text-slate-600">
              {data.totalExperiencesCount.toLocaleString("es-CO")} experiencias con oficio ESCO
            </div>
          </div>

          <div className="rounded-xl border border-emerald-200 bg-emerald-50/40 p-4">
            <div className="text-xs font-bold uppercase text-emerald-800">
              Partición Train / Test
            </div>
            <div className="mt-1 text-xl font-extrabold text-slate-900">
              {data.trainPersonsCount.toLocaleString("es-CO")} /{" "}
              {data.testPersonsCount.toLocaleString("es-CO")}
            </div>
            <div className="text-xs text-slate-600">
              División por persona completa (0 personas compartidas)
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <div className="text-xs font-bold uppercase text-slate-600">
              Catálogo ESCO Activo
            </div>
            <div className="mt-1 text-2xl font-extrabold text-slate-900">
              {data.escoCatalogCount.toLocaleString("es-CO")} oficios
            </div>
            <div className="text-xs text-slate-600">
              Enlazados por llave foránea verificada
            </div>
          </div>

          <div className="rounded-xl border border-amber-200 bg-amber-50/40 p-4">
            <div className="text-xs font-bold uppercase text-amber-900">
              Submuestra Ward (Filtro opcional)
            </div>
            <div className="mt-1 text-2xl font-extrabold text-slate-900">
              {data.wardDirectPersonsCount.toLocaleString("es-CO")} personas
            </div>
            <div className="text-xs text-slate-600">
              Solo un subconjunto de Train (no cubre todo el censo)
            </div>
          </div>
        </div>
      </section>

      {/* What is Included vs Excluded */}
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2 text-base font-bold text-slate-900">
          <Database className="h-5 w-5 text-blue-700" />
          <h2>Qué está incluido y qué se excluyó</h2>
        </div>

        <p className="mt-2 text-sm text-slate-700">
          Partiendo de{" "}
          <strong>
            {rawRow ? rawRow.experiences_count.toLocaleString("es-CO") : "—"} filas crudas
          </strong>{" "}
          ({rawRow ? rawRow.persons_count.toLocaleString("es-CO") : "—"} personas) y tras la limpieza básica (
          <strong>
            {cleanRow ? cleanRow.experiences_count.toLocaleString("es-CO") : "—"} filas limpias
          </strong>
          ), el explorador carga únicamente las experiencias que cuentan con una ocupación hoja válida en ESCO v1.2.1:
        </p>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-xs sm:text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-bold uppercase text-slate-600">
              <tr>
                <th className="px-3 py-2">Bloque excluido</th>
                <th className="px-3 py-2 text-right">Experiencias</th>
                <th className="px-3 py-2 text-right">Personas</th>
                <th className="px-3 py-2">Motivo</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {excludedRows.map((row) => (
                <tr key={row.stage_code}>
                  <td className="px-3 py-2 font-semibold text-slate-900">
                    {row.stage_label_es}
                  </td>
                  <td className="px-3 py-2 text-right font-mono">
                    {row.experiences_count.toLocaleString("es-CO")}
                  </td>
                  <td className="px-3 py-2 text-right font-mono">
                    {row.persons_count.toLocaleString("es-CO")}
                  </td>
                  <td className="px-3 py-2 text-slate-700">{row.reason_es}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Sources, resume_id note, and License status */}
      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2 text-base font-bold text-slate-900">
            <ShieldCheck className="h-5 w-5 text-emerald-700" />
            <h2>Identificadores <code>resume_id</code> y privacidad</h2>
          </div>
          <p className="mt-2 text-sm leading-relaxed text-slate-700">
            Los identificadores numéricos <code>resume_id</code> se conservan tal como vienen en el dataset público pseudonimizado{" "}
            <strong>JobHop v2</strong> (<code>aida-ugent/JobHop</code>, VDAB y Ghent University). No contienen nombres, correos, empresas ni datos personales identificables (PII).
          </p>
          <p className="mt-2 text-sm leading-relaxed text-slate-700">
            Todas las consultas se ejecutan exclusivamente en servidor mediante un rol PostgreSQL de{" "}
            <strong>solo lectura</strong>, con paginación estricta (25 filas por página) y sin endpoints de descarga masiva.
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2 text-base font-bold text-slate-900">
            <Scale className="h-5 w-5 text-blue-700" />
            <h2>Fuentes públicas y estatus de licencias</h2>
          </div>
          <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-slate-700">
            <li>
              <strong>JobHop v2 (VDAB / Ghent University):</strong> publicado públicamente bajo licencia{" "}
              <strong>CC BY 4.0</strong> (pendiente de confirmación final del equipo antes de abrir el despliegue a público general).
            </li>
            <li>
              <strong>Taxonomía ESCO v1.2.1 (Comisión Europea):</strong> reutilización bajo Decisión{" "}
              <code>2011/833/EU</code> (compatible con <strong>CC BY 4.0</strong>). Las competencias pertenecen al catálogo de la ocupación, no a la persona.
            </li>
            <li>
              <strong>Estado del despliegue:</strong> mantenido deliberadamente en modo{" "}
              <strong>Preview (no público)</strong> en Vercel.
            </li>
          </ul>
        </div>
      </section>
    </div>
  );
}
