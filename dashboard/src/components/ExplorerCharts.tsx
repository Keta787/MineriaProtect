"use client";

import React from "react";
import {
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type {
  DurationBinPoint,
  TopOccupationPoint,
  StartsPerYearPoint,
  IscoTransitionPoint,
} from "@/lib/db";
import { ISCO_MAJOR_LABELS_ES, ESCO_LABEL_GLOSS_ES } from "@/lib/isco-labels";

function EmptyChartNotice() {
  return (
    <div className="flex h-64 items-center justify-center rounded-lg border border-dashed border-slate-300 bg-slate-50 text-sm font-medium text-slate-500">
      Ningún resultado con estos filtros.
    </div>
  );
}

export function DurationDistributionChart({
  data,
}: {
  data: DurationBinPoint[];
}) {
  if (!data || data.length === 0) return <EmptyChartNotice />;

  const chartData = data.map((d) => ({
    tramo: d.bucket,
    Experiencias: Number(d.count),
  }));

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={{ top: 10, right: 16, left: 10, bottom: 8 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="tramo"
            tick={{ fontSize: 12, fill: "#0f172a", fontWeight: 600 }}
          />
          <YAxis
            tickFormatter={(v) =>
              Number(v) >= 1000
                ? `${(Number(v) / 1000).toFixed(0)}k`
                : String(v)
            }
            tick={{ fontSize: 12, fill: "#334155" }}
          />
          <Tooltip
            formatter={(val: unknown) => [
              `${Number(val).toLocaleString("es-CO")} experiencias`,
              "Cantidad",
            ]}
            contentStyle={{
              fontSize: "13px",
              borderRadius: "8px",
              borderColor: "#cbd5e1",
            }}
          />
          <Bar
            dataKey="Experiencias"
            fill="#1d4ed8"
            radius={[6, 6, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function TopOccupationsChart({
  data,
}: {
  data: TopOccupationPoint[];
}) {
  if (!data || data.length === 0) return <EmptyChartNotice />;

  const chartData = data.map((d) => {
    const gloss = ESCO_LABEL_GLOSS_ES[d.occupation_label.toLowerCase()];
    const displayName = gloss ? `${gloss}` : d.occupation_label;
    return {
      nombre:
        displayName.length > 34
          ? `${displayName.slice(0, 32)}…`
          : displayName,
      nombreCompleto: gloss
        ? `${gloss} (${d.occupation_label})`
        : d.occupation_label,
      codigo: d.occupation_code,
      Experiencias: Number(d.count),
    };
  });

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 6, right: 20, left: 10, bottom: 6 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            type="number"
            tickFormatter={(v) =>
              Number(v) >= 1000
                ? `${(Number(v) / 1000).toFixed(0)}k`
                : String(v)
            }
            tick={{ fontSize: 12, fill: "#334155" }}
          />
          <YAxis
            type="category"
            dataKey="nombre"
            width={185}
            tick={{ fontSize: 11, fill: "#0f172a", fontWeight: 600 }}
          />
          <Tooltip
            formatter={(
              val: unknown,
              _name: string,
              item: { payload?: { nombreCompleto?: string; codigo?: string } }
            ) => [
              `${Number(val).toLocaleString("es-CO")} experiencias — ${
                item?.payload?.nombreCompleto ?? ""
              } (ESCO ${item?.payload?.codigo ?? ""})`,
              "Ocupación",
            ]}
            contentStyle={{
              fontSize: "12px",
              borderRadius: "8px",
              borderColor: "#cbd5e1",
            }}
          />
          <Bar
            dataKey="Experiencias"
            fill="#059669"
            radius={[0, 6, 6, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function StartsPerYearChart({
  data,
}: {
  data: StartsPerYearPoint[];
}) {
  if (!data || data.length === 0) return <EmptyChartNotice />;

  const chartData = data.map((d) => ({
    anio: d.start_year,
    Inicios: Number(d.count),
  }));

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={chartData}
          margin={{ top: 10, right: 16, left: 10, bottom: 8 }}
        >
          <defs>
            <linearGradient id="startsFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#0284c7" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#0284c7" stopOpacity={0.04} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="anio"
            tick={{ fontSize: 12, fill: "#0f172a", fontWeight: 600 }}
          />
          <YAxis
            tickFormatter={(v) =>
              Number(v) >= 1000
                ? `${(Number(v) / 1000).toFixed(0)}k`
                : String(v)
            }
            tick={{ fontSize: 12, fill: "#334155" }}
          />
          <Tooltip
            formatter={(val: unknown) => [
              `${Number(val).toLocaleString("es-CO")} inicios`,
              "Empleos iniciados",
            ]}
            labelFormatter={(yr) => `Año de inicio: ${yr}`}
            contentStyle={{
              fontSize: "13px",
              borderRadius: "8px",
              borderColor: "#cbd5e1",
            }}
          />
          <Area
            type="monotone"
            dataKey="Inicios"
            stroke="#0284c7"
            strokeWidth={2.5}
            fill="url(#startsFill)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function IscoTransitionsChart({
  data,
}: {
  data: IscoTransitionPoint[];
}) {
  if (!data || data.length === 0) return <EmptyChartNotice />;

  const shortName = (d: string) => {
    const m = ISCO_MAJOR_LABELS_ES[d.trim()];
    if (!m) return `Grupo ${d}`;
    return m.title.length > 20 ? `${m.title.slice(0, 18)}…` : m.title;
  };
  const fullName = (d: string) =>
    ISCO_MAJOR_LABELS_ES[d.trim()]?.title ?? `Grupo ${d}`;

  const chartData = data.map((t) => ({
    par: `${shortName(t.from_isco)} → ${shortName(t.to_isco)}`,
    detalle: `${fullName(t.from_isco)} (ISCO ${t.from_isco}) → ${fullName(
      t.to_isco
    )} (ISCO ${t.to_isco})`,
    mismoGrupo: t.from_isco === t.to_isco,
    Transiciones: Number(t.count),
  }));

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 6, right: 20, left: 10, bottom: 6 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            type="number"
            tickFormatter={(v) =>
              Number(v) >= 1000
                ? `${(Number(v) / 1000).toFixed(0)}k`
                : String(v)
            }
            tick={{ fontSize: 12, fill: "#334155" }}
          />
          <YAxis
            type="category"
            dataKey="par"
            width={220}
            tick={{ fontSize: 11, fill: "#0f172a", fontWeight: 600 }}
          />
          <Tooltip
            formatter={(
              val: unknown,
              _name: string,
              item: { payload?: { detalle?: string; mismoGrupo?: boolean } }
            ) => [
              `${Number(val).toLocaleString("es-CO")} transiciones — ${
                item?.payload?.detalle ?? ""
              }`,
              item?.payload?.mismoGrupo
                ? "Mismo grupo ISCO"
                : "Cambio de grupo ISCO",
            ]}
            contentStyle={{
              fontSize: "12px",
              borderRadius: "8px",
              borderColor: "#cbd5e1",
            }}
          />
          <Bar dataKey="Transiciones" radius={[0, 6, 6, 0]}>
            {chartData.map((entry, idx) => (
              <Cell
                key={`tr-${idx}`}
                fill={entry.mismoGrupo ? "#7c3aed" : "#d97706"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
