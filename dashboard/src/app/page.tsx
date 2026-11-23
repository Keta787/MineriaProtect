import React from "react";
import {
  sanitizeExplorerFilters,
  getExplorerData,
  getPopularOccupationsForFilter,
  type ExplorerFilters,
} from "@/lib/db";
import { FilterBar } from "@/components/FilterBar";
import { ChartCard } from "@/components/ChartCard";
import {
  DurationDistributionChart,
  TopOccupationsChart,
  StartsPerYearChart,
  IscoTransitionsChart,
} from "@/components/ExplorerCharts";
import { ExperiencesTable } from "@/components/ExperiencesTable";
import { ISCO_MAJOR_LABELS_ES, formatEducationEs } from "@/lib/isco-labels";
import { Users, Briefcase, Repeat, Clock, Activity } from "lucide-react";

export const dynamic = "force-dynamic";

function describeActiveSelection(
  filters: ExplorerFilters,
  persons: number,
  experiences: number,
  selectedOccupationLabel: string | null
): string {
  const parts: string[] = [];

  if (filters.isco) {
    const meta = ISCO_MAJOR_LABELS_ES[filters.isco];
    parts.push(`en el grupo "${meta?.title ?? filters.isco}"`);
  }
  if (filters.occ) {
    parts.push(
      `en la ocupación "${selectedOccupationLabel ?? filters.occ}"`
    );
  }
  if (filters.edu) {
    parts.push(
      `con nivel educativo "${formatEducationEs(filters.edu).split(" (")[0]}"`
    );
  }
  if (filters.yFrom !== undefined && filters.yTo !== undefined) {
    parts.push(`iniciadas entre ${filters.yFrom} y ${filters.yTo}`);
  } else if (filters.yFrom !== undefined) {
    parts.push(`iniciadas desde ${filters.yFrom}`);
  } else if (filters.yTo !== undefined) {
    parts.push(`iniciadas hasta ${filters.yTo}`);
  }
  if (filters.split) {
    parts.push(
      `de la partición ${filters.split === "train" ? "Train (80 %)" : "Test (20 %)"}`
    );
  }
  if (filters.active === "true") {
    parts.push("solo empleos vigentes (corte 2026-Q1)");
  } else if (filters.active === "false") {
    parts.push("solo empleos cerrados");
  }
  if (filters.rep === "1") {
    parts.push("donde la persona repite esa ocupación");
  } else if (filters.rep === "0") {
    parts.push("donde la persona no repite esa ocupación");
  }
  if (filters.nJobs) {
    parts.push(
      `en trayectorias de ${filters.nJobs.replace("_mas_", "+ ").replaceAll("_", " ")}`
    );
  }
  if (filters.skills === "low") {
    parts.push("en ocupaciones con menos de 15 competencias esenciales");
  } else if (filters.skills === "mid") {
    parts.push("en ocupaciones con 15 a 28 competencias esenciales");
  } else if (filters.skills === "high") {
    parts.push("en ocupaciones con más de 28 competencias esenciales");
  }
  if (filters.ward25k) {
    parts.push("limitadas a las personas de la muestra estratificada Ward (Train)");
  }

  const base = `Estás viendo ${experiences.toLocaleString(
    "es-CO"
  )} experiencias laborales de ${persons.toLocaleString("es-CO")} personas`;

  if (parts.length === 0) {
    return `${base} correspondientes a todo el censo clasificado en Neon (sin filtros activos).`;
  }
  return `${base} ${parts.join(", ")}.`;
}

interface HomePageProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export default async function ExplorerHomePage({ searchParams }: HomePageProps) {
  const rawParams = await searchParams;
  const filters = sanitizeExplorerFilters(rawParams);

  const [data, popularOccupations] = await Promise.all([
    getExplorerData(filters),
    getPopularOccupationsForFilter(),
  ]);

  const activeSentence = describeActiveSelection(
    filters,
    data.counters.persons,
    data.counters.experiences,
    data.selectedOccupationLabel
  );

  return (
    <div className="space-y-6">
      {/* 1. Always-visible Filter Bar synced with URL + 3 Guided Scenarios */}
      <FilterBar
        filters={filters}
        popularOccupations={popularOccupations}
        selectedOccupationLabel={data.selectedOccupationLabel}
      />

      {/* 2. Plain-language Active Selection Summary + Live Query Latency */}
      <section className="flex flex-col justify-between gap-2 rounded-xl border border-blue-200 bg-blue-50/60 px-5 py-3.5 sm:flex-row sm:items-center">
        <p className="text-sm font-semibold text-slate-900 sm:text-base">
          {activeSentence}
        </p>
        <span className="inline-flex items-center gap-1.5 self-start rounded-full bg-white px-3 py-1 font-mono text-xs font-semibold text-slate-700 ring-1 ring-slate-200 sm:self-center shrink-0">
          <Activity className="h-3.5 w-3.5 text-emerald-600" />
          {data.isUnfilteredDefault
            ? `Vista agregada · ${data.queryElapsedMs} ms`
            : `Consulta en vivo · ${data.queryElapsedMs} ms`}
        </span>
      </section>

      {/* 3. Large Back-of-Room Readable Live Counters */}
      <section
        aria-label="Contadores reactivos de la selección"
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4"
      >
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-slate-500">
            <Users className="h-4 w-4 text-blue-700" />
            <span>Personas</span>
          </div>
          <div className="mt-2 text-3xl font-extrabold tracking-tight text-slate-900">
            {data.counters.persons.toLocaleString("es-CO")}
          </div>
          <div className="mt-1 text-xs text-slate-500">
            Personas únicas en la selección actual
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-slate-500">
            <Briefcase className="h-4 w-4 text-emerald-700" />
            <span>Experiencias</span>
          </div>
          <div className="mt-2 text-3xl font-extrabold tracking-tight text-slate-900">
            {data.counters.experiences.toLocaleString("es-CO")}
          </div>
          <div className="mt-1 text-xs text-slate-500">
            Puestos laborales con oficio ESCO
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-slate-500">
            <Repeat className="h-4 w-4 text-amber-600" />
            <span>% que repite ocupación</span>
          </div>
          <div className="mt-2 text-3xl font-extrabold tracking-tight text-amber-700">
            {data.counters.reincidePct.toFixed(2)} %
          </div>
          <div className="mt-1 text-xs text-slate-500">
            Experiencias en oficios ejercidos &gt; 1 vez
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-slate-500">
            <Clock className="h-4 w-4 text-purple-700" />
            <span>Duración mediana</span>
          </div>
          <div className="mt-2 text-3xl font-extrabold tracking-tight text-slate-900">
            {Number(data.counters.medianDurQ).toFixed(1)} trim
          </div>
          <div className="mt-1 text-xs text-slate-500">
            Equivalente a {(Number(data.counters.medianDurQ) / 4).toFixed(2)} años por puesto
          </div>
        </div>
      </section>

      {/* 4. Four Reactive Descriptive Recharts Visualizations */}
      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ChartCard
          title="Distribución de duración de empleos (en trimestres)"
          badgeText={
            data.isUnfilteredDefault
              ? "Preagregado (empleos cerrados)"
              : "Selección actual"
          }
          badgeTone="blue"
          whatAmISeeing="Cantidad de experiencias laborales agrupadas según cuántos trimestres duró cada puesto (de 1–2 trimestres hasta más de 40 trimestres)."
        >
          <DurationDistributionChart data={data.durationHist} />
        </ChartCard>

        <ChartCard
          title="Top 10 ocupaciones más frecuentes"
          badgeText="Nombres ESCO (código en tooltip)"
          badgeTone="emerald"
          whatAmISeeing="Las diez ocupaciones específicas con más experiencias registradas dentro de los filtros activos; pasa el cursor sobre una barra para ver el código oficial ESCO."
        >
          <TopOccupationsChart data={data.topOccupations} />
        </ChartCard>

        <ChartCard
          title="Inicios de empleo por año calendario"
          badgeText="Serie temporal"
          badgeTone="blue"
          whatAmISeeing="Número de experiencias laborales que comenzaron en cada año calendario dentro de la selección actual."
        >
          <StartsPerYearChart data={data.startsPerYear} />
        </ChartCard>

        <ChartCard
          title="Transiciones más frecuentes entre grupos ocupacionales"
          badgeText={
            data.transitionsCappedTo250k
              ? "Primeras 100k exp. coincidentes"
              : "Pares consecutivos"
          }
          badgeTone={data.transitionsCappedTo250k ? "amber" : "slate"}
          whatAmISeeing={
            data.transitionsCappedTo250k
              ? "Pares consecutivos de Gran Grupo ISCO origen → destino (púrpura = mismo grupo, ámbar = cambio de grupo) calculados sobre las primeras 100,000 experiencias coincidentes para mantener respuesta ágil; añade un filtro adicional para cobertura exacta."
              : "Pares consecutivos de Gran Grupo ISCO origen → destino dentro de la población filtrada (púrpura = permanencia en el mismo grupo, ámbar = cambio entre grupos)."
          }
        >
          <IscoTransitionsChart data={data.transitions} />
        </ChartCard>
      </section>

      {/* 5. Paginated, Sortable Table of Experiences (25 rows/page, NO export) */}
      <ExperiencesTable
        rows={data.tableRows}
        filters={filters}
        totalRows={data.totalRowsForPagination}
        page={data.page}
        pageSize={data.pageSize}
        maxPage={data.maxPage}
      />
    </div>
  );
}
