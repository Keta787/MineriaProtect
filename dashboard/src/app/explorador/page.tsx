import React from "react";
import Link from "next/link";
import {
  searchTrajectoriesBounded,
  getPersonTimelineById,
} from "@/lib/db";
import { ChartCard } from "@/components/ChartCard";
import {
  PersonTimelineDurationChart,
  PersonSkillsEvolutionChart,
} from "@/components/PersonTimelineChart";
import {
  ISCO_MAJOR_LABELS_ES,
  KMEANS_CLUSTER_PROFILES_ES,
  WARD_CLUSTER_PROFILES_ES,
  TRAJECTORY_SEGMENT_ES,
  formatEducationEs,
  formatIscoMajor,
  formatEscoOccupationWithCode,
} from "@/lib/isco-labels";
import {
  UserSearch,
  Sparkles,
  Calendar,
  Briefcase,
  GraduationCap,
  Repeat,
  AlertCircle,
  CheckCircle2,
  Layers,
} from "lucide-react";

export const dynamic = "force-dynamic";

const ARCHETYPE_PRESETS = [
  {
    id: 17,
    badge: "K-Means C0 · Test",
    title: "Operativo / Servicios (Reincidente)",
    desc: "resume_id = 17 (Partición Test, Clúster 0)",
    tone: "blue",
  },
  {
    id: 217,
    badge: "K-Means C1 · MNAR Test",
    title: "Educación No Reportada (MNAR = 1)",
    desc: "resume_id = 217 (Partición Test, Clúster 1)",
    tone: "amber",
  },
  {
    id: 10,
    badge: "K-Means C2 · Test",
    title: "Profesional Intensivo en Conocimiento",
    desc: "resume_id = 10 (Partición Test, Clúster 2)",
    tone: "emerald",
  },
  {
    id: 36,
    badge: "K-Means C3 · Test",
    title: "Carrera Larga y Pluriempleo",
    desc: "resume_id = 36 (Partición Test, Clúster 3)",
    tone: "purple",
  },
  {
    id: 65,
    badge: "Ward 25k Directo · C0",
    title: "Muestra Ward 25k · Operativo (C0)",
    desc: "resume_id = 65 (in_ward_25k_sample = TRUE)",
    tone: "blue",
  },
  {
    id: 665,
    badge: "Ward 25k Directo · C1",
    title: "Muestra Ward 25k · MNAR Estable (C1)",
    desc: "resume_id = 665 (in_ward_25k_sample = TRUE)",
    tone: "amber",
  },
  {
    id: 160,
    badge: "Ward 25k Directo · C2",
    title: "Muestra Ward 25k · Conocimiento (C2)",
    desc: "resume_id = 160 (in_ward_25k_sample = TRUE)",
    tone: "emerald",
  },
  {
    id: 377,
    badge: "Ward 25k Directo · C3",
    title: "Muestra Ward 25k · Alta Amplitud (C3)",
    desc: "resume_id = 377 (in_ward_25k_sample = TRUE)",
    tone: "purple",
  },
];

interface PageProps {
  searchParams: Promise<{
    id?: string;
    q_id?: string;
    split?: string;
    km?: string;
    isco?: string;
    edu?: string;
    ward25k?: string;
    ward_c?: string;
  }>;
}

export default async function ExploradorPage({ searchParams }: PageProps) {
  const params = await searchParams;

  const queryResumeId = params.q_id ? Number(params.q_id) : null;
  const splitFilter = params.split ?? "test";
  const kmFilter =
    params.km !== undefined && params.km !== "all" ? Number(params.km) : 0;
  const iscoFilter = params.isco ?? "all";
  const eduFilter = params.edu ?? "all";
  const onlyWard25k = params.ward25k === "1";
  const wardClusterFilter =
    params.ward_c !== undefined && params.ward_c !== "all"
      ? Number(params.ward_c)
      : null;

  const matchingPersons = await searchTrajectoriesBounded({
    resumeId:
      queryResumeId && Number.isInteger(queryResumeId) && queryResumeId > 0
        ? queryResumeId
        : null,
    split: splitFilter,
    clusterKmeans: kmFilter,
    iscoMajor: iscoFilter,
    universityLevel: eduFilter,
    onlyWard25k,
    clusterWardDirect: wardClusterFilter,
  });

  const selectedId = params.id
    ? Number(params.id)
    : matchingPersons[0]?.resume_id ?? 17;

  const { person, experiences } = await getPersonTimelineById(selectedId);

  const kmProfile = person
    ? KMEANS_CLUSTER_PROFILES_ES[Number(person.cluster_kmeans_8_0)]
    : null;
  const wardDirectProfile =
    person &&
    person.in_ward_25k_sample &&
    person.cluster_ward_25k_direct !== null
      ? WARD_CLUSTER_PROFILES_ES[Number(person.cluster_ward_25k_direct)]
      : null;
  const wardProjectedProfile = person
    ? WARD_CLUSTER_PROFILES_ES[Number(person.cluster_ward_25k_projected)]
    : null;
  const segMeta = person
    ? TRAJECTORY_SEGMENT_ES[person.trajectory_segment_5_0]
    : null;

  return (
    <div className="space-y-8">
      {/* Header */}
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-blue-800 ring-1 ring-blue-200">
            <UserSearch className="h-3.5 w-3.5" />
            Vista 3 · Explorador de Trayectorias por Persona (Consultas Indexadas LIMIT &le; 25)
          </span>
          <span className="font-mono text-xs text-slate-500">
            Gobernanza: Sin endpoints de listado completo ni descarga masiva
          </span>
        </div>
        <h1 className="mt-2 text-2xl font-extrabold text-slate-900">
          Inspección Cronológica de Carreras Reales (Empleos, Educación, Oficios ESCO y Clústeres)
        </h1>
        <p className="mt-1 text-xs leading-relaxed text-slate-600 sm:text-sm">
          Selecciona uno de los <strong>8 arquetipos representativos</strong> con un clic o utiliza el buscador acotado por filtros (partición <code>train</code>/<code>test</code>, clúster K-Means, submuestra Ward 25k, grupo ISCO, nivel educativo o <code>resume_id</code>). Cada oficio muestra primero su nombre legible seguido de su código oficial ESCO e ISCO.
        </p>

        {/* MODE A: 8 Quick Archetype Presets */}
        <div className="mt-4">
          <div className="mb-2 flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-700">
            <Sparkles className="h-3.5 w-3.5 text-amber-600" />
            <span>Modo A · Galería Rápida de 8 Arquetipos Verificados (1 Clic)</span>
          </div>
          <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 lg:grid-cols-4">
            {ARCHETYPE_PRESETS.map((preset) => {
              const isSelected = selectedId === preset.id;
              return (
                <Link
                  key={preset.id}
                  href={`/explorador?id=${preset.id}&q_id=${preset.id}`}
                  className={`flex flex-col justify-between rounded-xl border p-3 text-left transition-all ${
                    isSelected
                      ? "border-blue-700 bg-blue-50/80 ring-2 ring-blue-600/30"
                      : "border-slate-200 bg-slate-50/60 hover:border-blue-300 hover:bg-white"
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between gap-1">
                      <span className="rounded bg-slate-900 px-1.5 py-0.5 font-mono text-[10px] font-bold text-amber-300">
                        {preset.badge}
                      </span>
                      <span className="font-mono text-[11px] font-bold text-blue-700">
                        ID #{preset.id}
                      </span>
                    </div>
                    <div className="mt-1.5 text-xs font-bold text-slate-900">
                      {preset.title}
                    </div>
                  </div>
                  <div className="mt-1 text-[11px] text-slate-500">
                    {preset.desc}
                  </div>
                </Link>
              );
            })}
          </div>
        </div>

        {/* MODE B: Guided Filter Form (GET form, Server-Side rendered) */}
        <form
          method="GET"
          action="/explorador"
          className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4"
        >
          <div className="mb-2.5 flex flex-wrap items-center justify-between gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Modo B · Buscador y Filtro Guiado en Neon (Máximo 25 resultados por consulta)
            </span>
            <Link
              href="/explorador"
              className="text-xs font-semibold text-blue-700 hover:underline"
            >
              Restablecer filtros
            </Link>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-6">
            <div>
              <label className="block text-[11px] font-semibold text-slate-700">
                Buscar por resume_id
              </label>
              <input
                type="number"
                name="q_id"
                min={1}
                placeholder="Ej. 47, 160, 217..."
                defaultValue={queryResumeId ?? ""}
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 font-mono text-xs text-slate-900 focus:border-blue-600 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-700">
                Partición (Split 80/20)
              </label>
              <select
                name="split"
                defaultValue={splitFilter}
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-900"
              >
                <option value="test">Test (20% · 70,419 pers.)</option>
                <option value="train">Train (80% · 281,674 pers.)</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-700">
                Clúster K-Means (8.0 · Censo)
              </label>
              <select
                name="km"
                defaultValue={String(kmFilter)}
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-900"
              >
                <option value="0">C0 · Operativos / Inserción (43.9%)</option>
                <option value="1">C1 · Educación No Reportada MNAR (11.7%)</option>
                <option value="2">C2 · Profesionales Conocimiento (28.0%)</option>
                <option value="3">C3 · Carreras Largas / Pluriempleo (16.4%)</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-700">
                Gran Grupo ISCO (0..9)
              </label>
              <select
                name="isco"
                defaultValue={iscoFilter}
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-900"
              >
                <option value="all">Todos los grupos ISCO</option>
                {Object.entries(ISCO_MAJOR_LABELS_ES).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v.short}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-700">
                Nivel Educativo
              </label>
              <select
                name="edu"
                defaultValue={eduFilter}
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-900"
              >
                <option value="all">Todos los niveles</option>
                <option value="Secondary school">Secundaria (Secondary school)</option>
                <option value="Bachelor">Pregrado (Bachelor)</option>
                <option value="Master">Maestría (Master)</option>
                <option value="PhD">Doctorado (PhD)</option>
                <option value="No reportado">No reportado (MNAR = 1)</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-700">
                Submuestra Ward 25k
              </label>
              <select
                name="ward25k"
                defaultValue={onlyWard25k ? "1" : "0"}
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-900"
              >
                <option value="0">Censo completo (352,093)</option>
                <option value="1">Sólo muestra directa Ward (25,000)</option>
              </select>
            </div>
          </div>

          <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
            <div className="text-[11px] text-slate-500">
              Mostrando <strong>{matchingPersons.length}</strong> perfiles encontrados (selecciona cualquier chip abajo para inspeccionar su línea de tiempo):
            </div>
            <button
              type="submit"
              className="rounded-lg bg-blue-700 px-4 py-1.5 text-xs font-bold text-white shadow-sm hover:bg-blue-800"
            >
              Consultar en Neon
            </button>
          </div>

          {/* Matching Person Chips (up to 25) */}
          {matchingPersons.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5 border-t border-slate-200 pt-3">
              {matchingPersons.map((p) => {
                const active = p.resume_id === selectedId;
                return (
                  <Link
                    key={p.resume_id}
                    href={`/explorador?id=${p.resume_id}&split=${splitFilter}&km=${kmFilter}&isco=${iscoFilter}&edu=${eduFilter}&ward25k=${
                      onlyWard25k ? "1" : "0"
                    }`}
                    className={`inline-flex items-center gap-1 rounded-md px-2.5 py-1 font-mono text-xs transition-colors ${
                      active
                        ? "bg-blue-700 font-bold text-white shadow-sm"
                        : "bg-white text-slate-700 ring-1 ring-slate-300 hover:bg-blue-50"
                    }`}
                  >
                    <span>#{p.resume_id}</span>
                    <span className="text-[10px] opacity-80">
                      ({p.n_jobs} emp · ISCO {p.isco_major_1d_zfill})
                    </span>
                  </Link>
                );
              })}
            </div>
          )}
        </form>
      </section>

      {/* SELECTED PERSON PROFILE & CAREER TIMELINE */}
      {!person ? (
        <section className="rounded-xl border border-amber-300 bg-amber-50 p-6 text-sm text-amber-950">
          No se encontró ninguna persona con <code>resume_id = {selectedId}</code> en el censo clasificado. Prueba con uno de los 8 arquetipos superiores.
        </section>
      ) : (
        <>
          {/* Person Summary Header Card */}
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-start">
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-lg bg-slate-900 px-3 py-1 font-mono text-sm font-extrabold text-amber-300">
                    Persona resume_id #{person.resume_id}
                  </span>
                  <span
                    className={`rounded-full px-3 py-0.5 font-mono text-xs font-bold uppercase ${
                      person.split === "test"
                        ? "bg-amber-100 text-amber-900 ring-1 ring-amber-300"
                        : "bg-emerald-100 text-emerald-900 ring-1 ring-emerald-300"
                    }`}
                  >
                    Partición: {person.split.toUpperCase()}
                  </span>
                  {segMeta && (
                    <span
                      className={`rounded-full border px-3 py-0.5 text-xs font-bold ${segMeta.badgeClass}`}
                    >
                      Tipología 5.0: {segMeta.label}
                    </span>
                  )}
                </div>

                <h2 className="text-lg font-bold text-slate-900">
                  Sector Principal: {formatIscoMajor(person.isco_major_1d_zfill)} ·{" "}
                  {formatEducationEs(person.university_level)}
                </h2>
                <p className="text-xs text-slate-600">
                  Trayectoria completa con{" "}
                  <strong>{person.n_jobs} experiencias clasificadas</strong> en{" "}
                  <strong>{person.n_occ_posthoc} oficios ESCO distintos</strong> (
                  <strong>{person.n_returns_posthoc} retornos acumulados</strong> a un oficio previo; tasa de empleos reincidentes:{" "}
                  <strong>
                    {(Number(person.tasa_reincide_persona_posthoc) * 100).toFixed(1)}%
                  </strong>
                  ).
                </p>
              </div>

              {/* Dual Cluster Comparison Box: K-Means 8.0 (Full Census) vs Ward 8.1 (25k Direct vs Projected) */}
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:w-[540px]">
                {/* K-Means 8.0 Badge */}
                <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-3.5">
                  <div className="flex items-center justify-between text-[11px] font-bold uppercase text-blue-800">
                    <span>Clúster K-Means++ (8.0 · Censo 352k)</span>
                    <CheckCircle2 className="h-3.5 w-3.5 text-blue-700" />
                  </div>
                  <div className="mt-1 text-xs font-bold text-slate-900">
                    {kmProfile?.name ?? `Clúster ${person.cluster_kmeans_8_0}`}
                  </div>
                  <p className="mt-1 text-[11px] text-slate-600">
                    {kmProfile?.summary}
                  </p>
                </div>

                {/* Ward 8.1 Badge (Explicitly differentiating direct 25k sample vs outside sample) */}
                <div
                  className={`rounded-xl border p-3.5 ${
                    person.in_ward_25k_sample
                      ? "border-purple-300 bg-purple-50/60"
                      : "border-amber-300 bg-amber-50/50"
                  }`}
                >
                  <div className="flex items-center justify-between text-[11px] font-bold uppercase">
                    <span
                      className={
                        person.in_ward_25k_sample
                          ? "text-purple-900"
                          : "text-amber-900"
                      }
                    >
                      Clúster Jerárquico Ward (8.1)
                    </span>
                    {person.in_ward_25k_sample ? (
                      <span className="rounded bg-purple-700 px-1.5 py-0.5 font-mono text-[10px] text-white">
                        Muestra Directa 25k
                      </span>
                    ) : (
                      <span className="rounded bg-amber-200 px-1.5 py-0.5 font-mono text-[10px] text-amber-950">
                        Fuera de Muestra 25k (NULL)
                      </span>
                    )}
                  </div>

                  {person.in_ward_25k_sample && wardDirectProfile ? (
                    <>
                      <div className="mt-1 text-xs font-bold text-slate-900">
                        {wardDirectProfile.name} (Directo)
                      </div>
                      <p className="mt-1 text-[11px] text-slate-600">
                        Esta persona pertenece a las 25,000 de Train donde se ejecutó directamente el dendrograma de Ward.
                      </p>
                    </>
                  ) : (
                    <>
                      <div className="mt-1 text-xs font-bold text-slate-900">
                        Directo: <code>NULL</code> · Proyectado NearestCentroid:{" "}
                        <code>Clúster {person.cluster_ward_25k_projected}</code>
                      </div>
                      <p className="mt-1 text-[11px] text-amber-950">
                        No forma parte de las 25,000 personas de la muestra directa Ward; su etiqueta proyectada ({wardProjectedProfile?.name}) es sólo una aproximación geométrica.
                      </p>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* 6 Quantitative Trajectory Metrics */}
            <div className="mt-5 grid grid-cols-2 gap-3 border-t border-slate-100 pt-4 sm:grid-cols-3 lg:grid-cols-6">
              <div className="rounded-lg bg-slate-50 p-2.5">
                <div className="text-[11px] text-slate-500">Empleos / Oficios</div>
                <div className="mt-0.5 font-mono text-sm font-bold text-slate-900">
                  {person.n_jobs} emp / {person.n_occ_posthoc} oficios
                </div>
              </div>
              <div className="rounded-lg bg-slate-50 p-2.5">
                <div className="text-[11px] text-slate-500">Amplitud (span_q)</div>
                <div className="mt-0.5 font-mono text-sm font-bold text-slate-900">
                  {Number(person.span_q).toFixed(0)} trim ({(Number(person.span_q) / 4).toFixed(1)} años)
                </div>
              </div>
              <div className="rounded-lg bg-slate-50 p-2.5">
                <div className="text-[11px] text-slate-500">Duración Media (dur_mean)</div>
                <div className="mt-0.5 font-mono text-sm font-bold text-slate-900">
                  {Number(person.dur_mean).toFixed(1)} trim/empleo
                </div>
              </div>
              <div className="rounded-lg bg-slate-50 p-2.5">
                <div className="text-[11px] text-slate-500">Solapamiento (overlap)</div>
                <div className="mt-0.5 font-mono text-sm font-bold text-slate-900">
                  {Number(person.overlap_ratio).toFixed(2)}x
                </div>
              </div>
              <div className="rounded-lg bg-slate-50 p-2.5">
                <div className="text-[11px] text-slate-500">Skills Medias (E = C + K)</div>
                <div className="mt-0.5 font-mono text-sm font-bold text-slate-900">
                  {Number(person.mean_skills_essential).toFixed(1)} ({Number(person.mean_skills_competence).toFixed(1)}C + {Number(person.mean_skills_knowledge).toFixed(1)}K)
                </div>
              </div>
              <div className="rounded-lg bg-slate-50 p-2.5">
                <div className="text-[11px] text-slate-500">Tasa Reincidencia</div>
                <div className="mt-0.5 font-mono text-sm font-bold text-amber-800">
                  {(Number(person.tasa_reincide_persona_posthoc) * 100).toFixed(1)}% ({person.n_returns_posthoc} ret.)
                </div>
              </div>
            </div>
          </section>

          {/* 2 RESULTS FOCUS Charts for the Selected Person */}
          <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <ChartCard
              factId={`Persona #${person.resume_id} · F-021 · F-023`}
              sourceLabel="JOIN en vivo: person_experiences ⋈ esco_occupations_catalog"
              badgeText={`${experiences.length} Experiencias`}
              badgeTone="blue"
              headline={`La persona #${person.resume_id} registra ${experiences.length} empleos a lo largo de ${Number(person.span_q).toFixed(0)} trimestres, con una duración media de ${Number(person.dur_mean).toFixed(1)} trimestres por puesto`}
              whatAmISeeing="Duración en trimestres (dur_q) de cada experiencia laboral ordenada cronológicamente (#1 a #N); las barras en color ámbar indican empleos en un oficio ESCO donde la persona reincide (reincide = 1)."
              primaryLimit="Las fechas provienen de trimestres calendario reportados en JobHop v2; los empleos con es_vigente = TRUE están censurados por la derecha en 2026-Q1."
            >
              <PersonTimelineDurationChart experiences={experiences} />
            </ChartCard>

            <ChartCard
              factId={`Persona #${person.resume_id} · F-032 · F-035`}
              sourceLabel="Catálogo ESCO v1.2.1 · Versión A (Identidad Exacta E = C + K)"
              badgeText="Perfil de Competencias ESCO"
              badgeTone="emerald"
              headline={`A lo largo de su carrera, los oficios de la persona #${person.resume_id} exigen un promedio de ${Number(person.mean_skills_competence).toFixed(1)} habilidades prácticas (C) y ${Number(person.mean_skills_knowledge).toFixed(1)} conocimientos teóricos (K)`}
              whatAmISeeing="Composición apilada de competencias esenciales ESCO (Habilidades Prácticas en azul + Conocimientos Teóricos en esmeralda = Total Esenciales) exigidas por cada puesto de la trayectoria."
              primaryLimit="Las competencias se asignan desde el catálogo oficial ESCO v1.2.1 según el código de ocupación (occupation_code), por lo que dos empleos con el mismo código ESCO comparten el mismo perfil de competencias."
            >
              <PersonSkillsEvolutionChart experiences={experiences} />
            </ChartCard>
          </section>

          {/* Step-by-Step Career Timeline Cards */}
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-base font-bold text-slate-900">
              Línea de Tiempo Cronológica Puesto por Puesto (Persona #{person.resume_id})
            </h3>
            <p className="mt-0.5 text-xs text-slate-500">
              Cada tarjeta muestra el nombre oficial de la ocupación ESCO, su glosa en español (cuando aplica), el código ESCO, el subgrupo ISCO de 4 dígitos y el Gran Grupo ISCO de 1 dígito.
            </p>

            <div className="mt-5 space-y-4">
              {experiences.map((exp) => {
                const isRepeated = Number(exp.reincide) === 1;
                return (
                  <div
                    key={`${exp.resume_id}-${exp.job_order}`}
                    className={`relative rounded-xl border p-4 transition-shadow hover:shadow-sm ${
                      isRepeated
                        ? "border-amber-300 bg-amber-50/30"
                        : "border-slate-200 bg-slate-50/40"
                    }`}
                  >
                    <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
                      <div className="space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-blue-700 font-mono text-xs font-bold text-white">
                            {exp.job_order}
                          </span>
                          <span className="font-mono text-xs font-bold text-slate-800">
                            <Calendar className="mr-1 inline h-3.5 w-3.5 text-blue-600" />
                            {exp.start_year}-Q{exp.start_quarter} &rarr;{" "}
                            {exp.es_vigente
                              ? `Vigente (Censurado 2026-Q1)`
                              : `${exp.end_year}-Q${exp.end_quarter}`}
                          </span>
                          <span className="rounded bg-slate-200 px-2 py-0.5 font-mono text-xs font-semibold text-slate-800">
                            Duración: {exp.dur_q} trim ({(Number(exp.dur_q) / 4).toFixed(2)} años)
                          </span>
                          {isRepeated ? (
                            <span className="inline-flex items-center gap-1 rounded-full bg-amber-200 px-2.5 py-0.5 text-xs font-bold text-amber-950">
                              <Repeat className="h-3 w-3" />
                              Reincidente en este oficio (reincide = 1)
                            </span>
                          ) : (
                            <span className="rounded-full bg-slate-200 px-2.5 py-0.5 text-xs font-medium text-slate-700">
                              Oficio ejercido 1 sola vez (reincide = 0)
                            </span>
                          )}
                        </div>

                        {/* Occupation Name FIRST, then Code in monospace badge */}
                        <div className="pt-1 text-sm font-bold text-slate-900">
                          <Briefcase className="mr-1.5 inline h-4 w-4 text-blue-700" />
                          {formatEscoOccupationWithCode(
                            exp.occupation_label,
                            exp.occupation_code
                          )}
                        </div>

                        <div className="flex flex-wrap items-center gap-2 pt-1 text-xs text-slate-600">
                          <span>
                            <strong>Gran Grupo:</strong>{" "}
                            {formatIscoMajor(exp.isco_major_1d_zfill)}
                          </span>
                          <span>&middot;</span>
                          <span>
                            <strong>Subgrupo ISCO 4D:</strong>{" "}
                            {exp.isco_group_label}{" "}
                            <code className="rounded bg-slate-200 px-1.5 py-0.5 font-mono text-[11px]">
                              ISCO {exp.isco_group_code}
                            </code>
                          </span>
                        </div>
                      </div>

                      {/* Right side: Skills E = C + K and Experience-level K-Means Cluster */}
                      <div className="flex flex-wrap items-center gap-2 sm:flex-col sm:items-end">
                        <div className="rounded-lg bg-white px-3 py-1.5 font-mono text-xs shadow-sm ring-1 ring-slate-200">
                          <span className="font-bold text-slate-900">
                            E = {exp.n_skills_essential_a}
                          </span>{" "}
                          <span className="text-slate-600">
                            ({exp.n_skills_competence_a} Prácticas +{" "}
                            {exp.n_skills_knowledge_a} Conocimientos)
                          </span>
                        </div>
                        <span className="rounded bg-blue-50 px-2 py-0.5 font-mono text-[11px] font-semibold text-blue-800 ring-1 ring-blue-200">
                          Clúster Experiencia K-Means 8.0: C{exp.cluster_exp_kmeans_8_0}
                        </span>
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
