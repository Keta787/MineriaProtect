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
  Cell,
  Legend,
  LineChart,
  Line,
} from "recharts";
import type {
  FunnelRow,
  EdaSegmentRow,
  TopTransitionRow,
  PcaVarianceRow,
} from "@/lib/db";
import { TRAJECTORY_SEGMENT_ES } from "@/lib/isco-labels";

interface OverviewChartsProps {
  funnel: FunnelRow[];
  segments: EdaSegmentRow[];
  topTransitions: TopTransitionRow[];
  pca: PcaVarianceRow[];
}

export function DataJourneyFunnelChart({ funnel }: { funnel: FunnelRow[] }) {
  const mainStages = funnel.filter((r) =>
    [1, 3, 6, 7, 8, 9].includes(Number(r.stage_order))
  );

  const chartData = mainStages.map((s) => ({
    name:
      s.stage_order === 1
        ? "1. Crudo JobHop v2"
        : s.stage_order === 3
        ? "2. Limpio (2.0)"
        : s.stage_order === 6
        ? "3. Censo ESCO (Neon)"
        : s.stage_order === 7
        ? "4a. Train (80%)"
        : s.stage_order === 8
        ? "4b. Test (20%)"
        : "5. Muestra Ward 25k",
    Experiencias: Number(s.experiences_count),
    Personas: Number(s.persons_count),
    status: s.status_in_neon,
    reason: s.reason_es,
  }));

  const colors: Record<string, string> = {
    UPSTREAM_RAW: "#64748b",
    CLEAN_REFERENCE: "#0284c7",
    INCLUDED_CENSUS: "#1d4ed8",
    INCLUDED_TRAIN: "#059669",
    INCLUDED_TEST: "#d97706",
    WARD_DIRECT_ONLY: "#7c3aed",
  };

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={{ top: 12, right: 20, left: 15, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 11, fill: "#334155" }}
            interval={0}
          />
          <YAxis
            yAxisId="left"
            tickFormatter={(v) => `${(Number(v) / 1e6).toFixed(1)}M`}
            tick={{ fontSize: 11, fill: "#1e293b" }}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            tickFormatter={(v) => `${(Number(v) / 1e3).toFixed(0)}k`}
            tick={{ fontSize: 11, fill: "#059669" }}
          />
          <Tooltip
            formatter={(value: unknown, name: string) => [
              Number(value).toLocaleString("es-CO"),
              name,
            ]}
            contentStyle={{
              fontSize: "12px",
              borderRadius: "8px",
              borderColor: "#cbd5e1",
            }}
          />
          <Legend wrapperStyle={{ fontSize: "12px" }} />
          <Bar
            yAxisId="left"
            dataKey="Experiencias"
            name="Experiencias laborales (Eje Izq.)"
            radius={[4, 4, 0, 0]}
          >
            {chartData.map((entry, idx) => (
              <Cell
                key={`cell-exp-${idx}`}
                fill={colors[entry.status] ?? "#1d4ed8"}
              />
            ))}
          </Bar>
          <Bar
            yAxisId="right"
            dataKey="Personas"
            name="Personas únicas (Eje Der.)"
            fill="#0f766e"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function TrajectorySegmentsChart({
  segments,
}: {
  segments: EdaSegmentRow[];
}) {
  const data = segments.map((s) => {
    const meta = TRAJECTORY_SEGMENT_ES[s.trajectory_segment_5_0] ?? {
      label: s.trajectory_segment_5_0,
    };
    return {
      segmento: meta.label,
      Personas: Number(s.persons_count),
      Porcentaje: Number(Number(s.pct_persons).toFixed(2)),
      EmpleosMedios: Number(Number(s.mean_n_jobs).toFixed(2)),
      RetornosMedios: Number(Number(s.mean_n_returns).toFixed(2)),
    };
  });

  const barColors = ["#0284c7", "#059669", "#64748b", "#7c3aed"];

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 8, right: 24, left: 30, bottom: 8 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            type="number"
            unit="%"
            domain={[0, 52]}
            tick={{ fontSize: 11, fill: "#334155" }}
          />
          <YAxis
            type="category"
            dataKey="segmento"
            width={150}
            tick={{ fontSize: 11, fill: "#0f172a", fontWeight: 600 }}
          />
          <Tooltip
            formatter={(value: unknown, name: string) => {
              if (name.includes("%")) return [`${value}%`, name];
              return [Number(value).toLocaleString("es-CO"), name];
            }}
            contentStyle={{
              fontSize: "12px",
              borderRadius: "8px",
              borderColor: "#cbd5e1",
            }}
          />
          <Bar
            dataKey="Porcentaje"
            name="% de personas en el censo"
            radius={[0, 4, 4, 0]}
          >
            {data.map((_, idx) => (
              <Cell
                key={`seg-${idx}`}
                fill={barColors[idx % barColors.length]}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function PcaVarianceChart({ pca }: { pca: PcaVarianceRow[] }) {
  const pca50A = pca.filter(
    (r) =>
      r.notebook.includes("50k") && r.version.toLowerCase().includes("version a")
  );
  const pca50B = pca.filter(
    (r) =>
      r.notebook.includes("50k") && r.version.toLowerCase().includes("version b")
  );

  const merged = ["PC1", "PC2", "PC3", "PC4", "PC5"].map((pc) => {
    const rowA = pca50A.find((r) => r.pc === pc);
    const rowB = pca50B.find((r) => r.pc === pc);
    return {
      pc,
      "Acumulada Versión A (con outliers)": Number(
        (rowA?.cum_var_pct ?? 0).toFixed(2)
      ),
      "Acumulada Versión B (sin outliers)": Number(
        (rowB?.cum_var_pct ?? 0).toFixed(2)
      ),
      "Individual Versión B": Number((rowB?.var_exp_pct ?? 0).toFixed(2)),
    };
  });

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={merged}
          margin={{ top: 12, right: 20, left: 10, bottom: 8 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="pc" tick={{ fontSize: 12, fill: "#0f172a" }} />
          <YAxis
            unit="%"
            domain={[0, 100]}
            tick={{ fontSize: 11, fill: "#334155" }}
          />
          <Tooltip
            formatter={(value: unknown) => [`${value}%`, ""]}
            contentStyle={{
              fontSize: "12px",
              borderRadius: "8px",
              borderColor: "#cbd5e1",
            }}
          />
          <Legend wrapperStyle={{ fontSize: "12px" }} />
          <Line
            type="monotone"
            dataKey="Acumulada Versión B (sin outliers)"
            stroke="#059669"
            strokeWidth={3}
            dot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="Acumulada Versión A (con outliers)"
            stroke="#1d4ed8"
            strokeWidth={2.5}
            strokeDasharray="5 5"
            dot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="Individual Versión B"
            stroke="#d97706"
            strokeWidth={2}
            dot={{ r: 3 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function TopTransitionsChart({
  transitions,
}: {
  transitions: TopTransitionRow[];
}) {
  const top10 = transitions.slice(0, 10).map((t) => ({
    label: `${t.rank_order}. ${t.from_occupation_label} (${t.from_occupation_code}) → ${t.to_occupation_code}`,
    Transiciones: Number(t.transition_count),
    Porcentaje: Number(t.pct_of_all_transitions),
    esAutolazo: t.is_self_loop,
  }));

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={top10}
          layout="vertical"
          margin={{ top: 8, right: 20, left: 15, bottom: 8 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis type="number" tick={{ fontSize: 11, fill: "#334155" }} />
          <YAxis
            type="category"
            dataKey="label"
            width={230}
            tick={{ fontSize: 10, fill: "#0f172a" }}
          />
          <Tooltip
            formatter={(value: unknown) => [
              `${Number(value).toLocaleString("es-CO")} transiciones`,
              "Frecuencia",
            ]}
            contentStyle={{
              fontSize: "12px",
              borderRadius: "8px",
              borderColor: "#cbd5e1",
            }}
          />
          <Bar
            dataKey="Transiciones"
            name="Transiciones consecutivas observadas"
            fill="#1d4ed8"
            radius={[0, 4, 4, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
