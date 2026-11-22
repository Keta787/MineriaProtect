"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  ShieldCheck,
  UserSearch,
  BrainCircuit,
  Sigma,
  BookOpenCheck,
  Database,
} from "lucide-react";

const NAV_ITEMS = [
  {
    href: "/",
    label: "1. Resumen y Viaje de Datos",
    shortLabel: "1. Resumen",
    icon: BarChart3,
  },
  {
    href: "/transparencia",
    label: "2. Transparencia y Muestreo",
    shortLabel: "2. Transparencia",
    icon: ShieldCheck,
    highlight: true,
  },
  {
    href: "/explorador",
    label: "3. Explorador de Trayectorias",
    shortLabel: "3. Explorador",
    icon: UserSearch,
  },
  {
    href: "/modelos",
    label: "4. Modelos y Clustering",
    shortLabel: "4. Modelos (6–8)",
    icon: BrainCircuit,
  },
  {
    href: "/metodos-numericos",
    label: "5. Métodos Numéricos",
    shortLabel: "5. MCO vs. Lagrange",
    icon: Sigma,
  },
  {
    href: "/metodologia",
    label: "6. Metodología y Límites",
    shortLabel: "6. Metodología",
    icon: BookOpenCheck,
  },
];

export function Navbar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/95 backdrop-blur">
      {/* Persistent Top Academic & Governance Banner */}
      <div className="bg-slate-900 px-4 py-2 text-xs text-slate-100">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2 font-medium">
            <span className="inline-flex items-center gap-1 rounded-full bg-blue-500/20 px-2.5 py-0.5 text-[11px] font-semibold text-blue-200 ring-1 ring-inset ring-blue-400/40">
              <Database className="h-3 w-3" />
              Datos Académicos Verificados
            </span>
            <span>
              <strong>JobPath (UNIMINUTO Ibagué)</strong> · Censo Clasificado{" "}
              <code className="rounded bg-slate-800 px-1.5 py-0.5 text-amber-300">
                352,093 personas
              </code>{" "}
              /{" "}
              <code className="rounded bg-slate-800 px-1.5 py-0.5 text-amber-300">
                1,738,738 empleos
              </code>{" "}
              (JobHop v2 + ESCO v1.2.1 · CC BY 4.0)
            </span>
          </div>
          <div className="flex items-center gap-3 text-[11px] text-slate-300">
            <span className="inline-flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              Neon PostgreSQL 18 (Rol: <code>jobpath_readonly</code> · Server-Only)
            </span>
            <span className="hidden sm:inline text-slate-400">|</span>
            <span className="hidden sm:inline">
              Semilla global: <code>SEED = 42</code> · 0 personas compartidas Train/Test
            </span>
          </div>
        </div>
      </div>

      {/* Main Navigation Bar */}
      <div className="mx-auto max-w-7xl px-4">
        <div className="flex flex-col gap-2 py-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center justify-between">
            <Link href="/" className="group flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-700 font-bold text-white shadow-sm group-hover:bg-blue-800">
                JP
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-base font-bold tracking-tight text-slate-900">
                    JobPath Observatory
                  </span>
                  <span className="rounded bg-blue-50 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-blue-700 ring-1 ring-blue-200">
                    Fase 3
                  </span>
                </div>
                <p className="text-xs text-slate-500">
                  Minería de Trayectorias Laborales y Métodos Numéricos
                </p>
              </div>
            </Link>
          </div>

          <nav
            aria-label="Navegación principal del dashboard"
            className="flex flex-wrap items-center gap-1.5"
          >
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive =
                item.href === "/"
                  ? pathname === "/"
                  : pathname?.startsWith(item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                    isActive
                      ? "bg-blue-700 text-white shadow-sm ring-1 ring-blue-700"
                      : item.highlight
                      ? "bg-amber-50 text-amber-900 ring-1 ring-amber-300 hover:bg-amber-100"
                      : "text-slate-700 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                >
                  <Icon className="h-3.5 w-3.5 shrink-0" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
}
