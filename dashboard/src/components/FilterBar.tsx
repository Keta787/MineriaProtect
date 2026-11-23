"use client";

import React, { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import {
  SlidersHorizontal,
  RotateCcw,
  Sparkles,
  UserSearch,
  Loader2,
  Share2,
  Check,
} from "lucide-react";
import type { ExplorerFilters } from "@/lib/db";
import { ISCO_MAJOR_LABELS_ES } from "@/lib/isco-labels";

interface FilterBarProps {
  filters: ExplorerFilters;
  popularOccupations: Array<{ occupation_code: string; occupation_label: string }>;
  selectedOccupationLabel: string | null;
}

const DEMO_SCENARIOS = [
  {
    id: "sc1",
    label: "1. Servicios y Ventas + Secundaria (2010–2019)",
    description: "ISCO 5 · Educación Secundaria · 2010–2019",
    query: "/?isco=5&edu=Secondary+school&yFrom=2010&yTo=2019",
  },
  {
    id: "sc2",
    label: "2. Profesionales Científicos + Maestría (Cerrados)",
    description: "ISCO 2 · Maestría · Solo empleos cerrados",
    query: "/?isco=2&edu=Master&active=false",
  },
  {
    id: "sc3",
    label: "3. Carreras Largas (9+) en Test + Skills Altas (> 28)",
    description: "Partición Test · 9+ empleos · > 28 competencias",
    query: "/?split=test&nJobs=9_mas_empleos&skills=high",
  },
];

export function FilterBar({
  filters,
  popularOccupations,
  selectedOccupationLabel,
}: FilterBarProps) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [resumeIdInput, setResumeIdInput] = useState("");
  const [copiedUrl, setCopiedUrl] = useState(false);

  const [formState, setFormState] = useState({
    isco: filters.isco ?? "",
    occ: filters.occ ?? "",
    edu: filters.edu ?? "",
    yFrom: filters.yFrom !== undefined ? String(filters.yFrom) : "",
    yTo: filters.yTo !== undefined ? String(filters.yTo) : "",
    split: filters.split ?? "",
    active: filters.active ?? "",
    rep: filters.rep ?? "",
    nJobs: filters.nJobs ?? "",
    skills: filters.skills ?? "",
    ward25k: Boolean(filters.ward25k),
  });

  // Sync local form state when URL filters change via preset clicks
  React.useEffect(() => {
    setFormState({
      isco: filters.isco ?? "",
      occ: filters.occ ?? "",
      edu: filters.edu ?? "",
      yFrom: filters.yFrom !== undefined ? String(filters.yFrom) : "",
      yTo: filters.yTo !== undefined ? String(filters.yTo) : "",
      split: filters.split ?? "",
      active: filters.active ?? "",
      rep: filters.rep ?? "",
      nJobs: filters.nJobs ?? "",
      skills: filters.skills ?? "",
      ward25k: Boolean(filters.ward25k),
    });
  }, [filters]);

  function applyFilters(next = formState) {
    const params = new URLSearchParams();
    if (next.isco) params.set("isco", next.isco);
    if (next.occ) params.set("occ", next.occ);
    if (next.edu) params.set("edu", next.edu);
    if (next.yFrom) params.set("yFrom", next.yFrom);
    if (next.yTo) params.set("yTo", next.yTo);
    if (next.split) params.set("split", next.split);
    if (next.active) params.set("active", next.active);
    if (next.rep) params.set("rep", next.rep);
    if (next.nJobs) params.set("nJobs", next.nJobs);
    if (next.skills) params.set("skills", next.skills);
    if (next.ward25k) params.set("ward25k", "1");

    const qs = params.toString();
    startTransition(() => {
      router.push(qs ? `/?${qs}` : "/");
    });
  }

  function handleReset() {
    startTransition(() => {
      router.push("/");
    });
  }

  function handleScenarioClick(query: string) {
    startTransition(() => {
      router.push(query);
    });
  }

  function handlePersonLookup(e: React.FormEvent) {
    e.preventDefault();
    const id = Number(resumeIdInput.trim());
    if (Number.isInteger(id) && id > 0) {
      startTransition(() => {
        router.push(`/explorador?id=${id}`);
      });
    }
  }

  function handleCopyShareUrl() {
    if (typeof window !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(window.location.href).catch(() => {});
      setCopiedUrl(true);
      setTimeout(() => setCopiedUrl(false), 2000);
    }
  }

  // Ensure selected occupation from URL is always present in dropdown
  const occupationOptions = React.useMemo(() => {
    const exists = popularOccupations.some(
      (o) => o.occupation_code === formState.occ
    );
    if (formState.occ && !exists) {
      return [
        {
          occupation_code: formState.occ,
          occupation_label: selectedOccupationLabel ?? `Ocupación ${formState.occ}`,
        },
        ...popularOccupations,
      ];
    }
    return popularOccupations;
  }, [popularOccupations, formState.occ, selectedOccupationLabel]);

  return (
    <section
      aria-label="Barra de filtros interactivos"
      className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
    >
      {/* Top Row: Guided Demo Scenarios ("Prueba esto") + Copy URL */}
      <div className="mb-4 flex flex-col justify-between gap-3 border-b border-slate-100 pb-4 lg:flex-row lg:items-center">
        <div className="space-y-1.5">
          <div className="flex items-center gap-1.5 text-xs font-extrabold uppercase tracking-wider text-blue-700">
            <Sparkles className="h-4 w-4 text-amber-500" />
            <span>Prueba esto · 3 consultas guiadas de ejemplo (1 clic)</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {DEMO_SCENARIOS.map((sc) => (
              <button
                key={sc.id}
                type="button"
                disabled={isPending}
                onClick={() => handleScenarioClick(sc.query)}
                title={sc.description}
                className="rounded-lg border border-blue-200 bg-blue-50/70 px-3 py-1.5 text-left text-xs font-bold text-blue-900 transition-colors hover:bg-blue-100 disabled:opacity-60 sm:text-sm"
              >
                {sc.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={handleCopyShareUrl}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            {copiedUrl ? (
              <>
                <Check className="h-3.5 w-3.5 text-emerald-600" />
                <span>Enlace copiado</span>
              </>
            ) : (
              <>
                <Share2 className="h-3.5 w-3.5" />
                <span>Copiar enlace de esta vista</span>
              </>
            )}
          </button>
          <button
            type="button"
            onClick={handleReset}
            disabled={isPending}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-xs font-bold text-slate-800 hover:bg-slate-100 disabled:opacity-60"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Limpiar filtros</span>
          </button>
        </div>
      </div>

      {/* Main Filter Grid (Big, legible labels for projection) */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          applyFilters();
        }}
        className="space-y-4"
      >
        <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-5">
          {/* 1. Gran Grupo ISCO */}
          <div>
            <label
              htmlFor="f-isco"
              className="block text-xs font-bold text-slate-800 sm:text-sm"
            >
              Grupo ocupacional (ISCO)
            </label>
            <select
              id="f-isco"
              value={formState.isco}
              onChange={(e) =>
                setFormState((s) => ({ ...s, isco: e.target.value }))
              }
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-200"
            >
              <option value="">Todos los grupos</option>
              {Object.entries(ISCO_MAJOR_LABELS_ES).map(([k, v]) => (
                <option key={k} value={k}>
                  {v.title}
                </option>
              ))}
            </select>
          </div>

          {/* 2. Ocupación ESCO por nombre */}
          <div>
            <label
              htmlFor="f-occ"
              className="block text-xs font-bold text-slate-800 sm:text-sm"
            >
              Ocupación específica (ESCO)
            </label>
            <select
              id="f-occ"
              value={formState.occ}
              onChange={(e) =>
                setFormState((s) => ({ ...s, occ: e.target.value }))
              }
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-200"
            >
              <option value="">Todas las ocupaciones</option>
              {occupationOptions.map((o) => (
                <option
                  key={o.occupation_code}
                  value={o.occupation_code}
                  title={`Código ESCO: ${o.occupation_code}`}
                >
                  {o.occupation_label}
                </option>
              ))}
            </select>
          </div>

          {/* 3. Nivel educativo */}
          <div>
            <label
              htmlFor="f-edu"
              className="block text-xs font-bold text-slate-800 sm:text-sm"
            >
              Nivel educativo
            </label>
            <select
              id="f-edu"
              value={formState.edu}
              onChange={(e) =>
                setFormState((s) => ({ ...s, edu: e.target.value }))
              }
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-200"
            >
              <option value="">Todos los niveles</option>
              <option value="Secondary school">Educación Secundaria</option>
              <option value="Bachelor">Pregrado (Bachelor)</option>
              <option value="Master">Maestría (Master)</option>
              <option value="PhD">Doctorado (PhD)</option>
              <option value="No reportado">No reportado</option>
            </select>
          </div>

          {/* 4. Período (Año inicio desde / hasta) */}
          <div>
            <label className="block text-xs font-bold text-slate-800 sm:text-sm">
              Año de inicio (desde – hasta)
            </label>
            <div className="mt-1 flex items-center gap-2">
              <input
                type="number"
                min={1950}
                max={2026}
                placeholder="Ej. 2000"
                aria-label="Año inicio desde"
                value={formState.yFrom}
                onChange={(e) =>
                  setFormState((s) => ({ ...s, yFrom: e.target.value }))
                }
                className="w-1/2 rounded-lg border border-slate-300 bg-white px-2.5 py-2 text-sm text-slate-900 focus:border-blue-600 focus:outline-none"
              />
              <span className="text-slate-400">–</span>
              <input
                type="number"
                min={1950}
                max={2026}
                placeholder="Ej. 2019"
                aria-label="Año inicio hasta"
                value={formState.yTo}
                onChange={(e) =>
                  setFormState((s) => ({ ...s, yTo: e.target.value }))
                }
                className="w-1/2 rounded-lg border border-slate-300 bg-white px-2.5 py-2 text-sm text-slate-900 focus:border-blue-600 focus:outline-none"
              />
            </div>
          </div>

          {/* 5. Partición Train / Test */}
          <div>
            <label
              htmlFor="f-split"
              className="block text-xs font-bold text-slate-800 sm:text-sm"
            >
              Partición de datos
            </label>
            <select
              id="f-split"
              value={formState.split}
              onChange={(e) =>
                setFormState((s) => ({ ...s, split: e.target.value }))
              }
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-600 focus:outline-none"
            >
              <option value="">Todo el censo (Train + Test)</option>
              <option value="train">Train (80 %)</option>
              <option value="test">Test (20 %)</option>
            </select>
          </div>

          {/* 6. Empleo vigente */}
          <div>
            <label
              htmlFor="f-active"
              className="block text-xs font-bold text-slate-800 sm:text-sm"
            >
              Estado del empleo
            </label>
            <select
              id="f-active"
              value={formState.active}
              onChange={(e) =>
                setFormState((s) => ({ ...s, active: e.target.value }))
              }
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-600 focus:outline-none"
            >
              <option value="">Todos (cerrados y vigentes)</option>
              <option value="false">Solo empleos cerrados</option>
              <option value="true">Solo empleos vigentes (2026-Q1)</option>
            </select>
          </div>

          {/* 7. Repite ocupación (reincide) */}
          <div>
            <label
              htmlFor="f-rep"
              className="block text-xs font-bold text-slate-800 sm:text-sm"
            >
              ¿Repite ocupación?
            </label>
            <select
              id="f-rep"
              value={formState.rep}
              onChange={(e) =>
                setFormState((s) => ({ ...s, rep: e.target.value }))
              }
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-600 focus:outline-none"
            >
              <option value="">Todos</option>
              <option value="1">Sí repite este oficio</option>
              <option value="0">No repite este oficio</option>
            </select>
          </div>

          {/* 8. Longitud de trayectoria */}
          <div>
            <label
              htmlFor="f-njobs"
              className="block text-xs font-bold text-slate-800 sm:text-sm"
            >
              Longitud de trayectoria
            </label>
            <select
              id="f-njobs"
              value={formState.nJobs}
              onChange={(e) =>
                setFormState((s) => ({ ...s, nJobs: e.target.value }))
              }
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-600 focus:outline-none"
            >
              <option value="">Cualquier longitud</option>
              <option value="1_empleo">1 empleo</option>
              <option value="2_3_empleos">2 a 3 empleos</option>
              <option value="4_5_empleos">4 a 5 empleos</option>
              <option value="6_8_empleos">6 a 8 empleos</option>
              <option value="9_mas_empleos">9 o más empleos</option>
            </select>
          </div>

          {/* 9. Competencias esenciales de la ocupación */}
          <div>
            <label
              htmlFor="f-skills"
              className="block text-xs font-bold text-slate-800 sm:text-sm"
            >
              Competencias del oficio
            </label>
            <select
              id="f-skills"
              value={formState.skills}
              onChange={(e) =>
                setFormState((s) => ({ ...s, skills: e.target.value }))
              }
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-600 focus:outline-none"
            >
              <option value="">Cualquier nivel</option>
              <option value="low">Bajo (&lt; 15 competencias)</option>
              <option value="mid">Medio (15 a 28 competencias)</option>
              <option value="high">Alto (&gt; 28 competencias)</option>
            </select>
          </div>

          {/* 10. Botón Aplicar */}
          <div className="flex flex-col justify-end">
            <button
              type="submit"
              disabled={isPending}
              className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-blue-700 px-4 py-2.5 text-sm font-extrabold text-white shadow-sm transition-colors hover:bg-blue-800 disabled:opacity-60"
            >
              {isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Consultando Neon...</span>
                </>
              ) : (
                <>
                  <SlidersHorizontal className="h-4 w-4" />
                  <span>Aplicar filtros</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Bottom row: Explicit Ward 25k sample checkbox + direct resume_id lookup */}
        <div className="flex flex-col justify-between gap-3 border-t border-slate-100 pt-3 sm:flex-row sm:items-center">
          <label className="inline-flex cursor-pointer items-center gap-2.5 rounded-lg border border-amber-200 bg-amber-50/70 px-3 py-1.5 text-xs font-semibold text-amber-950">
            <input
              type="checkbox"
              checked={formState.ward25k}
              onChange={(e) =>
                setFormState((s) => ({ ...s, ward25k: e.target.checked }))
              }
              className="h-4 w-4 rounded border-amber-400 text-blue-700 focus:ring-blue-500"
            />
            <span>
              Solo personas de la muestra Ward (subconjunto estratificado de Train; no cubre todo el censo)
            </span>
          </label>

          <div className="flex items-center gap-2">
            <UserSearch className="h-4 w-4 text-slate-500 shrink-0" />
            <input
              type="number"
              min={1}
              placeholder="Ir a persona por resume_id (ej. 47)"
              value={resumeIdInput}
              onChange={(e) => setResumeIdInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  handlePersonLookup(e);
                }
              }}
              className="w-56 rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 font-mono text-xs text-slate-900 focus:border-blue-600 focus:outline-none"
            />
            <button
              type="button"
              onClick={handlePersonLookup}
              className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-bold text-white hover:bg-slate-800"
            >
              Ver trayectoria
            </button>
          </div>
        </div>
      </form>
    </section>
  );
}
