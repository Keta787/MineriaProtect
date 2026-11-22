import React from "react";
import { Eye, AlertTriangle, CheckCircle2 } from "lucide-react";

export interface ChartCardProps {
  /** Identificador de hecho en FACTS.md (ej. "F-004 · F-017") */
  factId: string;
  /** Categoría o cuaderno fuente (ej. "Cuaderno 5.0 · EDA Poblacional") */
  sourceLabel: string;
  /** RESULTS FOCUS 1: Titular cuantitativo que declara el hallazgo verificado */
  headline: string;
  /** RESULTS FOCUS 2: Una oración en lenguaje sencillo: ¿Qué estoy viendo? */
  whatAmISeeing: string;
  /** RESULTS FOCUS 3: Una oración honesta: Límite principal */
  primaryLimit: string;
  /** Contenido visual (gráfico Recharts o tabla comparativa) */
  children: React.ReactNode;
  /** Nota adicional o badge opcional */
  badgeText?: string;
  badgeTone?: "blue" | "emerald" | "amber" | "purple";
}

const BADGE_STYLES = {
  blue: "bg-blue-50 text-blue-800 ring-blue-200",
  emerald: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  amber: "bg-amber-50 text-amber-900 ring-amber-300",
  purple: "bg-purple-50 text-purple-800 ring-purple-200",
};

/**
 * Componente estandarizado RESULTS FOCUS.
 * Garantiza que cada visualización del dashboard tenga:
 * 1) Titular del hallazgo cuantitativo verificado,
 * 2) "¿Qué estoy viendo?" en una oración clara para no expertos,
 * 3) "Límite principal" en una oración metodológica honesta.
 */
export function ChartCard({
  factId,
  sourceLabel,
  headline,
  whatAmISeeing,
  primaryLimit,
  children,
  badgeText,
  badgeTone = "blue",
}: ChartCardProps) {
  return (
    <section className="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md">
      <div>
        {/* Meta header */}
        <div className="mb-2.5 flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-0.5 font-mono text-[11px] font-semibold text-slate-800">
              <CheckCircle2 className="h-3 w-3 text-emerald-600" />
              {factId}
            </span>
            <span className="text-xs font-medium text-slate-500">
              {sourceLabel}
            </span>
          </div>
          {badgeText && (
            <span
              className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold ring-1 ring-inset ${BADGE_STYLES[badgeTone]}`}
            >
              {badgeText}
            </span>
          )}
        </div>

        {/* RESULTS FOCUS Headline */}
        <h3 className="text-base font-bold leading-snug text-slate-900 sm:text-lg">
          {headline}
        </h3>

        {/* ¿Qué estoy viendo? */}
        <div className="mt-2.5 flex items-start gap-2 rounded-lg bg-slate-50 p-2.5 text-xs leading-relaxed text-slate-700 ring-1 ring-inset ring-slate-200/80">
          <Eye className="mt-0.5 h-4 w-4 shrink-0 text-blue-600" />
          <div>
            <strong className="font-semibold text-slate-900">
              ¿Qué estoy viendo?{" "}
            </strong>
            <span>{whatAmISeeing}</span>
          </div>
        </div>
      </div>

      {/* Chart / Visual Content */}
      <div className="my-4 w-full">{children}</div>

      {/* Límite principal */}
      <div className="mt-auto flex items-start gap-2 rounded-lg bg-amber-50/70 p-2.5 text-xs leading-relaxed text-amber-950 ring-1 ring-inset ring-amber-200/90">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
        <div>
          <strong className="font-semibold text-amber-900">
            Límite principal:{" "}
          </strong>
          <span>{primaryLimit}</span>
        </div>
      </div>
    </section>
  );
}
