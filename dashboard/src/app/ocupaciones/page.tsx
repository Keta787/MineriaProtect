import React from "react";
import Link from "next/link";
import { searchEscoOccupations } from "@/lib/db";
import { ISCO_MAJOR_LABELS_ES, ESCO_LABEL_GLOSS_ES } from "@/lib/isco-labels";
import {
  BookOpen,
  Search,
  SlidersHorizontal,
  ChevronLeft,
  ChevronRight,
  Info,
} from "lucide-react";

export const dynamic = "force-dynamic";

interface PageProps {
  searchParams: Promise<{
    q?: string;
    isco?: string;
    code?: string;
    page?: string;
  }>;
}

export default async function OcupacionesPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const q = params.q ?? "";
  const isco = params.isco ?? "";
  const code = params.code ?? "";
  const page = params.page ? Number(params.page) : 1;

  const { items, selected, totalMatches, elapsedMs } =
    await searchEscoOccupations({ q, isco, code, page });

  const totalPages = Math.min(40, Math.max(1, Math.ceil(totalMatches / 25)));

  const buildPageHref = (nextPage: number) => {
    const sp = new URLSearchParams();
    if (q) sp.set("q", q);
    if (isco) sp.set("isco", isco);
    if (code) sp.set("code", code);
    if (nextPage > 1) sp.set("page", String(nextPage));
    const qs = sp.toString();
    return qs ? `/ocupaciones?${qs}` : "/ocupaciones";
  };

  return (
    <div className="space-y-6">
      {/* Search Header */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-extrabold text-slate-900">
              <BookOpen className="h-6 w-6 text-blue-700" />
              <span>Buscador de Ocupaciones (Catálogo ESCO v1.2.1)</span>
            </h1>
            <p className="mt-1 text-sm text-slate-600">
              Consulta cualquier ocupación del catálogo ESCO para ver su grupo ocupacional ISCO y las competencias esenciales exigidas por el oficio.
            </p>
          </div>
          <span className="font-mono text-xs text-slate-500">
            {totalMatches.toLocaleString("es-CO")} ocupaciones coincidentes · {elapsedMs} ms
          </span>
        </div>

        <form
          method="GET"
          action="/ocupaciones"
          className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3"
        >
          <div>
            <label className="block text-xs font-bold text-slate-800 sm:text-sm">
              Buscar ocupación o subgrupo
            </label>
            <input
              type="text"
              name="q"
              defaultValue={q}
              placeholder="Ej. nurse, developer, sales, teacher..."
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-600 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-800 sm:text-sm">
              Filtrar por Gran Grupo ISCO
            </label>
            <select
              name="isco"
              defaultValue={isco}
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-600 focus:outline-none"
            >
              <option value="">Todos los grupos</option>
              {Object.entries(ISCO_MAJOR_LABELS_ES).map(([k, v]) => (
                <option key={k} value={k}>
                  {v.title}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end gap-2">
            <button
              type="submit"
              className="inline-flex flex-1 items-center justify-center gap-2 rounded-lg bg-blue-700 px-4 py-2 text-sm font-bold text-white hover:bg-blue-800"
            >
              <Search className="h-4 w-4" />
              Buscar en catálogo
            </button>
            <Link
              href="/ocupaciones"
              className="rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
            >
              Limpiar
            </Link>
          </div>
        </form>
      </section>

      {/* Main Split: Occupation Detail Card + Paginated List */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        {/* Selected Occupation Detail (2 cols) */}
        <section className="rounded-2xl border border-blue-200 bg-white p-5 shadow-sm lg:col-span-2">
          {!selected ? (
            <div className="py-12 text-center text-sm text-slate-500">
              Ningún resultado con estos filtros.
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-bold text-blue-800 ring-1 ring-blue-200">
                  Ficha de ocupación ESCO
                </span>
                <h2 className="mt-2 text-xl font-extrabold text-slate-900">
                  {ESCO_LABEL_GLOSS_ES[selected.occupation_label.toLowerCase()]
                    ? `${ESCO_LABEL_GLOSS_ES[selected.occupation_label.toLowerCase()]} (${selected.occupation_label})`
                    : selected.occupation_label}
                </h2>
                <p className="mt-1 font-mono text-xs text-slate-500">
                  Código ESCO: <strong>{selected.occupation_code}</strong> · Subgrupo ISCO 4D:{" "}
                  <strong>{selected.isco_group_code}</strong>
                </p>
              </div>

              <div className="rounded-xl bg-slate-50 p-3.5 text-xs text-slate-700 ring-1 ring-slate-200/80">
                <div>
                  <strong>Gran Grupo ISCO:</strong>{" "}
                  {ISCO_MAJOR_LABELS_ES[selected.isco_major_1d_zfill]?.title ??
                    selected.isco_major_1d_zfill}
                </div>
                <div className="mt-1">
                  <strong>Subgrupo ISCO:</strong> {selected.isco_group_label}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-xl border border-slate-200 p-3">
                  <div className="text-xs text-slate-500">
                    Experiencias en el censo
                  </div>
                  <div className="mt-0.5 text-2xl font-extrabold text-slate-900">
                    {selected.census_experiences.toLocaleString("es-CO")}
                  </div>
                </div>
                <div className="rounded-xl border border-slate-200 p-3">
                  <div className="text-xs text-slate-500">
                    Personas distintas
                  </div>
                  <div className="mt-0.5 text-2xl font-extrabold text-slate-900">
                    {selected.census_persons.toLocaleString("es-CO")}
                  </div>
                </div>
              </div>

              <div className="rounded-xl border border-emerald-200 bg-emerald-50/40 p-4">
                <div className="text-xs font-bold uppercase tracking-wide text-emerald-900">
                  Competencias esenciales exigidas (ESCO v1.2.1)
                </div>
                <div className="mt-2 grid grid-cols-3 gap-2 text-center">
                  <div className="rounded-lg bg-white p-2 ring-1 ring-emerald-200">
                    <div className="text-[11px] text-slate-500">Total (E)</div>
                    <div className="text-lg font-extrabold text-slate-900">
                      {selected.n_skills_essential_ref}
                    </div>
                  </div>
                  <div className="rounded-lg bg-white p-2 ring-1 ring-emerald-200">
                    <div className="text-[11px] text-slate-500">Prácticas (C)</div>
                    <div className="text-lg font-extrabold text-blue-700">
                      {selected.n_skills_competence_ref}
                    </div>
                  </div>
                  <div className="rounded-lg bg-white p-2 ring-1 ring-emerald-200">
                    <div className="text-[11px] text-slate-500">Teóricas (K)</div>
                    <div className="text-lg font-extrabold text-emerald-700">
                      {selected.n_skills_knowledge_ref}
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-2 rounded-lg bg-amber-50 p-3 text-xs text-amber-950 ring-1 ring-amber-200">
                <Info className="mt-0.5 h-4 w-4 shrink-0 text-amber-700" />
                <span>
                  Estas cifras describen las competencias requeridas por la ocupación en el catálogo estándar ESCO, no las competencias individuales de una persona.
                </span>
              </div>

              <Link
                href={`/?occ=${encodeURIComponent(selected.occupation_code)}`}
                className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-blue-700 px-4 py-2.5 text-sm font-bold text-white shadow-sm hover:bg-blue-800"
              >
                <SlidersHorizontal className="h-4 w-4" />
                Explorar experiencias de esta ocupación
              </Link>
            </div>
          )}
        </section>

        {/* Paginated Catalog Table (3 cols) */}
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm lg:col-span-3">
          <h2 className="text-base font-bold text-slate-900">
            Resultados del catálogo (haz clic en una ocupación para ver su detalle)
          </h2>

          {items.length === 0 ? (
            <div className="mt-4 rounded-lg border border-dashed border-slate-300 bg-slate-50 p-10 text-center text-sm text-slate-500">
              Ningún resultado con estos filtros.
            </div>
          ) : (
            <>
              <div className="mt-3 overflow-x-auto">
                <table className="w-full text-left text-xs sm:text-sm">
                  <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-bold uppercase text-slate-600">
                    <tr>
                      <th className="px-3 py-2">Ocupación (código en hover)</th>
                      <th className="px-3 py-2">Grupo ISCO</th>
                      <th className="px-3 py-2 text-right">Esenciales</th>
                      <th className="px-3 py-2 text-right">Prácticas</th>
                      <th className="px-3 py-2 text-right">Teóricas</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {items.map((item) => {
                      const isCurrent =
                        selected?.occupation_code === item.occupation_code;
                      const gloss =
                        ESCO_LABEL_GLOSS_ES[item.occupation_label.toLowerCase()];
                      const iscoMeta =
                        ISCO_MAJOR_LABELS_ES[item.isco_major_1d_zfill];

                      const sp = new URLSearchParams();
                      if (q) sp.set("q", q);
                      if (isco) sp.set("isco", isco);
                      sp.set("code", item.occupation_code);
                      if (page > 1) sp.set("page", String(page));

                      return (
                        <tr
                          key={item.occupation_code}
                          className={
                            isCurrent
                              ? "bg-blue-50/80 font-semibold"
                              : "hover:bg-slate-50"
                          }
                        >
                          <td className="px-3 py-2">
                            <Link
                              href={`/ocupaciones?${sp.toString()}`}
                              title={`Código ESCO: ${item.occupation_code} · ISCO 4D: ${item.isco_group_code} · ${item.occupation_label}`}
                              className="text-slate-900 hover:text-blue-700 hover:underline"
                            >
                              {gloss ? gloss : item.occupation_label}
                            </Link>
                          </td>
                          <td className="px-3 py-2 text-slate-600">
                            {iscoMeta?.title ?? item.isco_major_1d_zfill}
                          </td>
                          <td className="px-3 py-2 text-right font-mono font-bold">
                            {item.n_skills_essential_ref}
                          </td>
                          <td className="px-3 py-2 text-right font-mono text-blue-700">
                            {item.n_skills_competence_ref}
                          </td>
                          <td className="px-3 py-2 text-right font-mono text-emerald-700">
                            {item.n_skills_knowledge_ref}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3 text-xs">
                <span className="text-slate-600">
                  Página <strong>{page}</strong> de <strong>{totalPages}</strong>
                </span>
                <div className="flex gap-2">
                  {page > 1 && (
                    <Link
                      href={buildPageHref(page - 1)}
                      className="inline-flex items-center gap-1 rounded-lg border border-slate-300 bg-white px-3 py-1.5 font-bold text-slate-800 hover:bg-slate-50"
                    >
                      <ChevronLeft className="h-4 w-4" />
                      Anterior
                    </Link>
                  )}
                  {page < totalPages && (
                    <Link
                      href={buildPageHref(page + 1)}
                      className="inline-flex items-center gap-1 rounded-lg border border-slate-300 bg-white px-3 py-1.5 font-bold text-slate-800 hover:bg-slate-50"
                    >
                      Siguiente
                      <ChevronRight className="h-4 w-4" />
                    </Link>
                  )}
                </div>
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
