import React from "react";
import Link from "next/link";
import { getPersonTrajectoryLive } from "@/lib/db";
import { ChartCard } from "@/components/ChartCard";
import {
  PersonTimelineDurationChart,
  PersonSkillsEvolutionChart,
} from "@/components/PersonTimelineChart";
import {
  ISCO_MAJOR_LABELS_ES,
  ESCO_LABEL_GLOSS_ES,
  formatEducationEs,
} from "@/lib/isco-labels";
import {
  UserSearch,
  Calendar,
  Briefcase,
  Repeat,
  Info,
  ArrowLeft,
} from "lucide-react";

export const dynamic = "force-dynamic";

interface PageProps {
  searchParams: Promise<{ id?: string }>;
}

const QUICK_SAMPLE_IDS = [47, 17, 10, 36, 160, 217];

export default async function PersonTrajectoryPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const parsedId = params.id ? Number(params.id) : 47;
  const targetId =
    Number.isInteger(parsedId) && parsedId > 0 ? parsedId : 47;

  const { person, experiences, elapsedMs } =
    await getPersonTrajectoryLive(targetId);

  return (
    <div className="space-y-6">
      {/* Header + Search by resume_id */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
          <div>
            <Link
              href="/"
              className="inline-flex items-center gap-1 text-xs font-bold text-blue-700 hover:underline"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Volver al Explorador de Datos
            </Link>
            <h1 className="mt-1.5 text-2xl font-extrabold text-slate-900">
              Línea de tiempo por persona
            </h1>
            <p className="mt-1 text-sm text-slate-600">
              Consulta los empleos, períodos, nivel educativo, grupos ocupacionales y competencias exigidas por cada ocupación ESCO para un <code>resume_id</code> específico (consulta puntual <code>LIMIT 1</code>).
            </p>
          </div>

          <form
            method="GET"
            action="/explorador"
            className="flex flex-wrap items-center gap-2 shrink-0"
          >
            <UserSearch className="h-4 w-4 text-slate-500" />
            <input
              type="number"
              name="id"
              min={1}
              defaultValue={targetId}
              aria-label="Buscar por resume_id"
              placeholder="Ej. 47"
              className="w-36 rounded-lg border border-slate-300 bg-white px-3 py-2 font-mono text-sm text-slate-900 focus:border-blue-600 focus:outline-none"
            />
            <button
              type="submit"
              className="rounded-lg bg-blue-700 px-4 py-2 text-sm font-bold text-white hover:bg-blue-800"
            >
              Buscar ID
            </button>
          </form>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-slate-100 pt-3 text-xs">
          <span className="font-semibold text-slate-600">
            Ejemplos rápidos de ID:
          </span>
          {QUICK_SAMPLE_IDS.map((sid) => (
            <Link
              key={sid}
              href={`/explorador?id=${sid}`}
              className={`rounded-md px-2.5 py-1 font-mono font-bold transition-colors ${
                sid === targetId
                  ? "bg-blue-700 text-white"
                  : "bg-slate-100 text-slate-700 hover:bg-blue-50"
              }`}
            >
              #{sid}
            </Link>
          ))}
          <span className="ml-auto font-mono text-[11px] text-slate-500">
            Consulta en vivo: {elapsedMs} ms
          </span>
        </div>
      </section>

      {!person ? (
        <section className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm font-semibold text-slate-600">
          Ningún resultado para <code>resume_id = {targetId}</code> en el censo clasificado. Prueba otro identificador o selecciona una persona desde la tabla principal.
        </section>
      ) : (
        <>
          {/* Person Summary Strip (Strictly factual live columns, NO model narratives) */}
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-lg bg-slate-900 px-3 py-1 font-mono text-base font-extrabold text-amber-300">
                  resume_id #{person.resume_id}
                </span>
                <span className="rounded-full bg-slate-100 px-3 py-1 font-mono text-xs font-bold uppercase text-slate-800">
                  Partición: {person.split}
                </span>
                {person.in_ward_25k_sample && (
                  <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-950">
                    Incluida en submuestra Ward (Train)
                  </span>
                )}
              </div>
              <div className="text-sm font-semibold text-slate-700">
                Nivel educativo:{" "}
                <span className="text-slate-900">
                  {formatEducationEs(person.university_level).split(" (")[0]}
                </span>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-5">
              <div className="rounded-lg bg-slate-50 p-3">
                <div className="text-xs text-slate-500">Empleos clasificados</div>
                <div className="mt-0.5 text-xl font-extrabold text-slate-900">
                  {person.n_jobs}
                </div>
              </div>
              <div className="rounded-lg bg-slate-50 p-3">
                <div className="text-xs text-slate-500">Ocupaciones distintas</div>
                <div className="mt-0.5 text-xl font-extrabold text-slate-900">
                  {person.n_occ_posthoc}
                </div>
              </div>
              <div className="rounded-lg bg-slate-50 p-3">
                <div className="text-xs text-slate-500">Amplitud de carrera</div>
                <div className="mt-0.5 text-xl font-extrabold text-slate-900">
                  {Number(person.span_q).toFixed(0)} trim
                </div>
              </div>
              <div className="rounded-lg bg-slate-50 p-3">
                <div className="text-xs text-slate-500">Duración media</div>
                <div className="mt-0.5 text-xl font-extrabold text-slate-900">
                  {Number(person.dur_mean).toFixed(1)} trim
                </div>
              </div>
              <div className="rounded-lg bg-slate-50 p-3">
                <div className="text-xs text-slate-500">Retornos a oficio previo</div>
                <div className="mt-0.5 text-xl font-extrabold text-amber-700">
                  {person.n_returns_posthoc}
                </div>
              </div>
            </div>

            {/* Mandatory ESCO Skills Attribution Note */}
            <div className="mt-4 flex items-start gap-2.5 rounded-xl border border-amber-200 bg-amber-50/80 p-3.5 text-xs leading-relaxed text-amber-950 sm:text-sm">
              <Info className="mt-0.5 h-4 w-4 shrink-0 text-amber-700" />
              <p>
                <strong>Nota importante sobre competencias ESCO:</strong> El número de habilidades prácticas y conocimientos teóricos mostrado en cada puesto proviene del catálogo estándar <strong>ESCO v1.2.1</strong> y{" "}
                <strong>describe lo que exige esa ocupación</strong>, no las habilidades individuales que la persona declaró saber.
              </p>
            </div>
          </section>

          {/* 2 Descriptive Reactive Charts for this Person */}
          <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <ChartCard
              title="Duración por puesto en orden cronológico"
              badgeText={`${experiences.length} empleos`}
              badgeTone="blue"
              whatAmISeeing="Duración en trimestres de cada empleo registrado para esta persona; las barras en ámbar señalan empleos en una ocupación que se repite en su historial."
            >
              <PersonTimelineDurationChart experiences={experiences} />
            </ChartCard>

            <ChartCard
              title="Competencias esenciales exigidas por cada ocupación ESCO"
              badgeText="Catálogo ESCO v1.2.1"
              badgeTone="emerald"
              whatAmISeeing="Cantidad de habilidades prácticas (azul) y conocimientos teóricos (verde) que el catálogo ESCO asigna a la ocupación de cada puesto."
            >
              <PersonSkillsEvolutionChart experiences={experiences} />
            </ChartCard>
          </section>

          {/* Chronological Job Cards */}
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-base font-bold text-slate-900 sm:text-lg">
              Secuencia cronológica de experiencias (pasa el cursor sobre la ocupación para ver el código ESCO)
            </h2>
            <div className="mt-4 space-y-3">
              {experiences.map((exp) => {
                const gloss =
                  ESCO_LABEL_GLOSS_ES[exp.occupation_label.toLowerCase()];
                const iscoMeta =
                  ISCO_MAJOR_LABELS_ES[String(exp.isco_major_1d_zfill).trim()];
                const isRepeated = Number(exp.reincide) === 1;

                return (
                  <div
                    key={`${exp.resume_id}-${exp.job_order}`}
                    className={`rounded-xl border p-4 ${
                      isRepeated
                        ? "border-amber-300 bg-amber-50/30"
                        : "border-slate-200 bg-slate-50/40"
                    }`}
                  >
                    <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
                      <div className="space-y-1">
                        <div className="flex flex-wrap items-center gap-2 text-xs">
                          <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-blue-700 font-mono font-bold text-white">
                            {exp.job_order}
                          </span>
                          <span className="font-mono font-bold text-slate-800">
                            <Calendar className="mr-1 inline h-3.5 w-3.5 text-blue-600" />
                            {exp.start_year}-Q{exp.start_quarter} &rarr;{" "}
                            {exp.es_vigente
                              ? "Vigente (2026-Q1)"
                              : `${exp.end_year}-Q${exp.end_quarter}`}
                          </span>
                          <span className="rounded bg-slate-200 px-2 py-0.5 font-mono font-semibold text-slate-800">
                            {exp.dur_q} trim ({(Number(exp.dur_q) / 4).toFixed(2)} años)
                          </span>
                          {isRepeated && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-amber-200 px-2.5 py-0.5 font-bold text-amber-950">
                              <Repeat className="h-3 w-3" />
                              Ocupación repetida
                            </span>
                          )}
                        </div>

                        <div className="pt-1 text-base font-bold text-slate-900">
                          <Briefcase className="mr-1.5 inline h-4 w-4 text-blue-700" />
                          <Link
                            href={`/ocupaciones?code=${encodeURIComponent(
                              exp.occupation_code
                            )}`}
                            title={`Código ESCO: ${exp.occupation_code} · Subgrupo ISCO: ${exp.isco_group_code} · Nombre oficial ESCO: ${exp.occupation_label}`}
                            className="hover:text-blue-700 hover:underline"
                          >
                            {gloss ? gloss : exp.occupation_label}
                          </Link>
                        </div>

                        <div className="text-xs text-slate-600">
                          <strong>Grupo ocupacional:</strong>{" "}
                          <span title={`Código ISCO 1D: ${exp.isco_major_1d_zfill}`}>
                            {iscoMeta?.title ?? `Grupo ${exp.isco_major_1d_zfill}`}
                          </span>{" "}
                          &middot;{" "}
                          <span title={`Código ISCO 4D: ${exp.isco_group_code}`}>
                            {exp.isco_group_label}
                          </span>
                        </div>
                      </div>

                      <div className="rounded-lg bg-white px-3.5 py-2 text-xs shadow-sm ring-1 ring-slate-200">
                        <div className="font-bold text-slate-900">
                          {exp.n_skills_essential_a} competencias esenciales ESCO
                        </div>
                        <div className="mt-0.5 text-slate-600">
                          {exp.n_skills_competence_a} habilidades prácticas +{" "}
                          {exp.n_skills_knowledge_a} conocimientos teóricos
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
