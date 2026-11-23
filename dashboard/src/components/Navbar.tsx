"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  SlidersHorizontal,
  UserSearch,
  BookOpen,
  Info,
  Database,
} from "lucide-react";

const NAV_ITEMS = [
  {
    href: "/",
    label: "Explorador de Datos",
    icon: SlidersHorizontal,
  },
  {
    href: "/explorador",
    label: "Trayectoria por Persona",
    icon: UserSearch,
  },
  {
    href: "/ocupaciones",
    label: "Catálogo de Ocupaciones ESCO",
    icon: BookOpen,
  },
  {
    href: "/sobre-datos",
    label: "Sobre estos datos",
    icon: Info,
  },
];

export function Navbar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/95 backdrop-blur">
      {/* Visible Banner: "Demo interactivo de datos" */}
      <div className="bg-slate-900 px-4 py-2 text-xs text-slate-100">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2.5 font-medium">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide text-emerald-300 ring-1 ring-inset ring-emerald-400/40">
              <Database className="h-3.5 w-3.5" />
              Demo interactivo de datos
            </span>
            <span className="text-slate-200">
              <strong>JobPath Explorer</strong> · Consulta en vivo sobre el censo clasificado{" "}
              <span className="text-amber-300">JobHop v2 + ESCO v1.2.1</span>
            </span>
          </div>
          <div className="flex items-center gap-2 text-[11px] text-slate-300">
            <span className="inline-flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              Neon PostgreSQL (Solo lectura · Paginado, sin exportación masiva)
            </span>
          </div>
        </div>
      </div>

      {/* Main Navigation */}
      <div className="mx-auto max-w-7xl px-4">
        <div className="flex flex-col gap-2 py-3 md:flex-row md:items-center md:justify-between">
          <Link href="/" className="group flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-700 font-bold text-white shadow-sm group-hover:bg-blue-800">
              JP
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-base font-extrabold tracking-tight text-slate-900">
                  JobPath Explorer
                </span>
                <span className="rounded bg-blue-50 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-blue-700 ring-1 ring-blue-200">
                  Preview
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Herramienta interactiva de consulta de trayectorias laborales
              </p>
            </div>
          </Link>

          <nav
            aria-label="Navegación del explorador"
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
                  className={`inline-flex items-center gap-1.5 rounded-lg px-3.5 py-2 text-xs font-bold transition-all sm:text-sm ${
                    isActive
                      ? "bg-blue-700 text-white shadow-sm"
                      : "text-slate-700 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                >
                  <Icon className="h-4 w-4 shrink-0" />
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
