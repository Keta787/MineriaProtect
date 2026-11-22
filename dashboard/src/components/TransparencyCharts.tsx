"use client";

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Cell,
} from "recharts";
import type { FunnelRow, StratumComparisonRow } from "@/lib/db";
import { ISCO_MAJOR_LABELS_ES } from "@/lib/isco-labels";

export function ExclusionBreakdownChart({ funnel }: { funnel: FunnelRow[] }) {
  const excludedAndIncluded = funnel
    .filter((r) => [2, 4, 5, 6].includes(Number(r.stage_order)))
    .map((r) => ({
      etapa:
        r.stage_order === 2
          ? "Excluido Limpieza (122,277)"
          : r.stage_order === 4
          ? "Excluido 'unknown' sin ESCO (128,981)"
          : r.stage_order === 5
          ? "Excluido 'rescatado' sin hoja (3,295)"
          : "Incluido Censo Neon (1,738,738)",
      Experiencias: Number(r.experiences_count),
      PorcentajeLimpio: Number(Number(r.pct_clean_experiences).toFixed(2)),
      color:
        r.stage_order === 6
          ? "#059669"
          : r.stage_order === 2
          ? "#64748b"
          : "#d97706",
    }));

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={excludedAndIncluded}
          layout="vertical"
          margin={{ top: 10, right: 24, left: 25, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            type="number"
            tickFormatter={(v) => `${(Number(v) / 1e3).toFixed(0)}k`}
            tick={{ fontSize: 11, fill: "#334155" }}
          />
          <YAxis
            type="category"
            dataKey="etapa"
            width={215}
            tick={{ fontSize: 11, fill: "#0f172a", fontWeight: 600 }}
          />
          <Tooltip
            formatter={(value: unknown) => [
              `${Number(value).toLocaleString("es-CO")} experiencias`,
              "Volumen",
            ]}
            contentStyle={{
              fontSize: "12px",
              borderRadius: "8px",
              borderColor: "#cbd5e1",
            }}
          />
          <Bar dataKey="Experiencias" radius={[0, 4, 4, 0]}>
            {excludedAndIncluded.map((entry, idx) => (
              <Cell key={`exc-${idx}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function IscoStrataComparisonChart({
  strata,
}: {
  strata: StratumComparisonRow[];
}) {
  const data = strata.map((s) => {
    const meta = ISCO_MAJOR_LABELS_ES[String(s.stratum_key).trim()];
    return {
      grupo: meta ? meta.short : `ISCO ${s.stratum_key}`,
      "Censo Completo (N = 352,093)": Number(s.census_pct),
      "Muestra Ward 25k (n = 25,000)": Number(s.ward_25k_pct),
      diff_pp: Number(s.diff_pp),
    };
  });

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 12, right: 20, left: 10, bottom: 35 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="grupo"
            angle={-20}
            textAnchor="end"
            height={55}
            tick={{ fontSize: 10, fill: "#0f172a" }}
            interval={0}
          />
          <YAxis
            unit="%"
            tick={{ fontSize: 11, fill: "#334155" }}
            domain={[0, 28]}
          />
          <Tooltip
            formatter={(value: unknown, name: string) => [`${value}%`, name]}
            contentStyle={{
              fontSize: "12px",
              borderRadius: "8px",
              borderColor: "#cbd5e1",
            }}
          />
          <Legend wrapperStyle={{ fontSize: "12px" }} />
          <Bar
            dataKey="Censo Completo (N = 352,093)"
            fill="#1d4ed8"
            radius={[3, 3, 0, 0]}
          />
          <Bar
            dataKey="Muestra Ward 25k (n = 25,000)"
            fill="#7c3aed"
            radius={[3, 3, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function EducationStrataComparisonChart({
  strata,
}: {
  strata: StratumComparisonRow[];
}) {
  const data = strata.map((s) => ({
    nivel: s.stratum_key,
    "Censo Completo (352,093)": Number(s.census_pct),
    "Muestra Ward 25k (25,000)": Number(s.ward_25k_pct),
  }));

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 12, right: 20, left: 10, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="nivel"
            tick={{ fontSize: 11, fill: "#0f172a" }}
            interval={0}
          />
          <YAxis
            unit="%"
            tick={{ fontSize: 11, fill: "#334155" }}
            domain={[0, 45]}
          />
          <Tooltip
            formatter={(value: unknown, name: string) => [`${value}%`, name]}
            contentStyle={{
              fontSize: "12px",
              borderRadius: "8px",
              borderColor: "#cbd5e1",
            }}
          />
          <Legend wrapperStyle={{ fontSize: "12px" }} />
          <Bar
            dataKey="Censo Completo (352,093)"
            fill="#059669"
            radius={[3, 3, 0, 0]}
          />
          <Bar
            dataKey="Muestra Ward 25k (25,000)"
            fill="#d97706"
            radius={[3, 3, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
