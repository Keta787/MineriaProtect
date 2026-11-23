import React from "react";
import { Eye } from "lucide-react";

export interface ChartCardProps {
  /** Título descriptivo neutral (NO un titular de conclusión o hallazgo) */
  title: string;
  /** Una oración en lenguaje claro: ¿Qué estoy viendo? */
  whatAmISeeing: string;
  /** Etiqueta de contexto opcional (ej. "En vivo · Selección actual") */
  badgeText?: string;
  badgeTone?: "blue" | "emerald" | "amber" | "slate";
  /** Contenido del gráfico Recharts */
  children: React.ReactNode;
}

const BADGE_STYLES = {
  blue: "bg-blue-50 text-blue-800 ring-blue-200",
  emerald: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  amber: "bg-amber-50 text-amber-900 ring-amber-300",
  slate: "bg-slate-100 text-slate-700 ring-slate-200",
};

/**
 * Contenedor descriptivo para gráficos reactivos del Explorador Interactivo de Datos.
 * Muestra siempre un título descriptivo neutro y una oración "¿Qué estoy viendo?".
 */
export function ChartCard({
  title,
  whatAmISeeing,
  badgeText,
  badgeTone = "slate",
  children,
}: ChartCardProps) {
  return (
    <section className="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-base font-bold text-slate-900 sm:text-lg">
            {title}
          </h2>
          {badgeText && (
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset ${BADGE_STYLES[badgeTone]}`}
            >
              {badgeText}
            </span>
          )}
        </div>

        <div className="mt-2 flex items-start gap-2 rounded-lg bg-slate-50 px-3 py-2 text-xs leading-relaxed text-slate-700 ring-1 ring-inset ring-slate-200/80 sm:text-sm">
          <Eye className="mt-0.5 h-4 w-4 shrink-0 text-blue-600" />
          <p>
            <strong className="font-semibold text-slate-900">
              ¿Qué estoy viendo?{" "}
            </strong>
            {whatAmISeeing}
          </p>
        </div>
      </div>

      <div className="mt-4 w-full">{children}</div>
    </section>
  );
}
