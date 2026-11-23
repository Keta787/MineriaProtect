import React from "react";
import Link from "next/link";
import type { ExperienceTableRow, ExplorerFilters } from "@/lib/db";
import {
  ISCO_MAJOR_LABELS_ES,
  ESCO_LABEL_GLOSS_ES,
  formatEducationEs,
} from "@/lib/isco-labels";
import { ArrowUpDown, ChevronLeft, ChevronRight, ExternalLink } from "lucide-react";

interface ExperiencesTableProps {
  rows: ExperienceTableRow[];
  filters: ExplorerFilters;
  totalRows: number;
  page: number;
  pageSize: number;
  maxPage: number;
}

function buildUrlWithOverrides(
  filters: ExplorerFilters,
  overrides: Partial<ExplorerFilters>
): string {
  const merged = { ...filters, ...overrides };
  const params = new URLSearchParams();
  if (merged.isco) params.set("isco", merged.isco);
  if (merged.occ) params.set("occ", merged.occ);
  if (merged.edu) params.set("edu", merged.edu);
  if (merged.yFrom !== undefined) params.set("yFrom", String(merged.yFrom));
  if (merged.yTo !== undefined) params.set("yTo", String(merged.yTo));
  if (merged.split) params.set("split", merged.split);
  if (merged.active) params.set("active", merged.active);
  if (merged.rep) params.set("rep", merged.rep);
  if (merged.nJobs) params.set("nJobs", merged.nJobs);
  if (merged.skills) params.set("skills", merged.skills);
  if (merged.ward25k) params.set("ward25k", "1");
  if (merged.sort) params.set("sort", merged.sort);
  if (merged.dir) params.set("dir", merged.dir);
  if (merged.page && merged.page > 1) params.set("page", String(merged.page));
  const qs = params.toString();
  return qs ? `/?${qs}` : "/";
}

export function ExperiencesTable({
  rows,
  filters,
  totalRows,
  page,
  pageSize,
  maxPage,
}: ExperiencesTableProps) {
  const nextDirFor = (col: string): "asc" | "desc" =>
    filters.sort === col && filters.dir === "desc" ? "asc" : "desc";

  const startRow = totalRows === 0 ? 0 : (page - 1) * pageSize + 1;
  const endRow = Math.min(page * pageSize, totalRows);

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-base font-bold text-slate-900 sm:text-lg">
            Tabla de experiencias coincidentes (paginada, 25 filas por página)
          </h2>
          <p className="text-xs text-slate-600">
            Haz clic en un <code>resume_id</code> para abrir la línea de tiempo completa de esa persona o pasa el cursor sobre una ocupación para ver su código ESCO/ISCO. Sin descarga masiva.
          </p>
        </div>
        <div className="rounded-lg bg-slate-100 px-3 py-1.5 font-mono text-xs font-semibold text-slate-700">
          Mostrando {startRow.toLocaleString("es-CO")}–{endRow.toLocaleString("es-CO")} de{" "}
          {totalRows.toLocaleString("es-CO")} (límite: máx. {maxPage} págs.)
        </div>
      </div>

      {rows.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-10 text-center text-sm font-semibold text-slate-600">
          Ningún resultado con estos filtros. Prueba ampliar el rango de años o quitar un filtro.
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-bold uppercase text-slate-600">
                <tr>
                  <th className="px-3 py-2.5">Persona (ID)</th>
                  <th className="px-3 py-2.5">
                    <Link
                      href={buildUrlWithOverrides(filters, {
                        sort: "job_order",
                        dir: nextDirFor("job_order"),
                        page: 1,
                      })}
                      className="inline-flex items-center gap-1 hover:text-blue-700"
                    >
                      Orden
                      <ArrowUpDown className="h-3 w-3" />
                    </Link>
                  </th>
                  <th className="px-3 py-2.5">Ocupación (código al pasar el cursor)</th>
                  <th className="px-3 py-2.5">Grupo ISCO</th>
                  <th className="px-3 py-2.5">Educación</th>
                  <th className="px-3 py-2.5">
                    <Link
                      href={buildUrlWithOverrides(filters, {
                        sort: "start_year",
                        dir: nextDirFor("start_year"),
                        page: 1,
                      })}
                      className="inline-flex items-center gap-1 hover:text-blue-700"
                    >
                      Período
                      <ArrowUpDown className="h-3 w-3" />
                    </Link>
                  </th>
                  <th className="px-3 py-2.5 text-right">
                    <Link
                      href={buildUrlWithOverrides(filters, {
                        sort: "dur_q",
                        dir: nextDirFor("dur_q"),
                        page: 1,
                      })}
                      className="inline-flex items-center gap-1 hover:text-blue-700"
                    >
                      Duración
                      <ArrowUpDown className="h-3 w-3" />
                    </Link>
                  </th>
                  <th className="px-3 py-2.5 text-right">
                    <Link
                      href={buildUrlWithOverrides(filters, {
                        sort: "skills",
                        dir: nextDirFor("skills"),
                        page: 1,
                      })}
                      className="inline-flex items-center gap-1 hover:text-blue-700"
                    >
                      Skills ESCO
                      <ArrowUpDown className="h-3 w-3" />
                    </Link>
                  </th>
                  <th className="px-3 py-2.5 text-center">¿Repite?</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {rows.map((r) => {
                  const gloss =
                    ESCO_LABEL_GLOSS_ES[r.occupation_label.toLowerCase()];
                  const iscoMeta =
                    ISCO_MAJOR_LABELS_ES[String(r.isco_major_1d_zfill).trim()];
                  return (
                    <tr
                      key={`${r.resume_id}-${r.job_order}`}
                      className="hover:bg-blue-50/40"
                    >
                      <td className="px-3 py-2.5 font-mono">
                        <Link
                          href={`/explorador?id=${r.resume_id}`}
                          className="inline-flex items-center gap-1 font-bold text-blue-700 hover:underline"
                          title="Abrir línea de tiempo completa de esta persona"
                        >
                          #{r.resume_id}
                          <ExternalLink className="h-3 w-3" />
                        </Link>
                      </td>
                      <td className="px-3 py-2.5 font-mono text-slate-600">
                        {r.job_order} / {r.n_jobs}
                      </td>
                      <td className="px-3 py-2.5">
                        <Link
                          href={`/ocupaciones?code=${encodeURIComponent(
                            r.occupation_code
                          )}`}
                          title={`Código ESCO: ${r.occupation_code} · Subgrupo ISCO: ${r.isco_group_code} · Nombre oficial ESCO: ${r.occupation_label}`}
                          className="font-semibold text-slate-900 hover:text-blue-700 hover:underline"
                        >
                          {gloss ? gloss : r.occupation_label}
                        </Link>
                      </td>
                      <td
                        className="px-3 py-2.5 text-slate-700"
                        title={`Código ISCO 1D: ${r.isco_major_1d_zfill}`}
                      >
                        {iscoMeta?.title ?? `Grupo ${r.isco_major_1d_zfill}`}
                      </td>
                      <td className="px-3 py-2.5 text-slate-700">
                        {formatEducationEs(r.university_level).split(" (")[0]}
                      </td>
                      <td className="px-3 py-2.5 font-mono text-xs text-slate-700">
                        {r.start_year}Q{r.start_quarter} &rarr;{" "}
                        {r.es_vigente ? (
                          <span className="rounded bg-emerald-100 px-1.5 py-0.5 font-bold text-emerald-900">
                            Vigente
                          </span>
                        ) : (
                          `${r.end_year}Q${r.end_quarter}`
                        )}
                      </td>
                      <td className="px-3 py-2.5 text-right font-mono font-semibold text-slate-900">
                        {r.dur_q} trim
                      </td>
                      <td className="px-3 py-2.5 text-right font-mono text-slate-700">
                        {r.n_skills_essential_a}
                      </td>
                      <td className="px-3 py-2.5 text-center">
                        {Number(r.reincide) === 1 ? (
                          <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-bold text-amber-900">
                            Sí
                          </span>
                        ) : (
                          <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
                            No
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Server-side Pagination Controls */}
          <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 pt-3 text-xs">
            <span className="text-slate-600">
              Página <strong>{page}</strong> de <strong>{maxPage}</strong>
            </span>
            <div className="flex items-center gap-2">
              {page > 1 ? (
                <Link
                  href={buildUrlWithOverrides(filters, { page: page - 1 })}
                  className="inline-flex items-center gap-1 rounded-lg border border-slate-300 bg-white px-3 py-1.5 font-bold text-slate-800 hover:bg-slate-50"
                >
                  <ChevronLeft className="h-4 w-4" />
                  Anterior
                </Link>
              ) : (
                <span className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 font-semibold text-slate-400">
                  <ChevronLeft className="h-4 w-4" />
                  Anterior
                </span>
              )}

              {page < maxPage ? (
                <Link
                  href={buildUrlWithOverrides(filters, { page: page + 1 })}
                  className="inline-flex items-center gap-1 rounded-lg border border-slate-300 bg-white px-3 py-1.5 font-bold text-slate-800 hover:bg-slate-50"
                >
                  Siguiente
                  <ChevronRight className="h-4 w-4" />
                </Link>
              ) : (
                <span className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 font-semibold text-slate-400">
                  Siguiente
                  <ChevronRight className="h-4 w-4" />
                </span>
              )}
            </div>
          </div>
        </>
      )}
    </section>
  );
}
