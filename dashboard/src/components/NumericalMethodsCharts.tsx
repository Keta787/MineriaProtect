"use client";

import React, { useState } from "react";
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
  BarChart,
} from "recharts";
import type {
  NmRl04AnnualRow,
  NmRl04ExtrapolationRow,
  NmLg01SurvivalRow,
  NmLg01P3MilestoneRow,
  NmLg01RungeRow,
} from "@/lib/db";

const A0_CENTERED_DUR = 16.44171259037386;
const A1_DUR = -0.7926006555639094;

const A0_CENTERED_SKILLS_VALID = 22.367212541630604;
const A1_SKILLS_VALID = 0.0967314308666689;

const A0_SKILLS_CENSORED = 225.93362299752488;
const A1_SKILLS_CENSORED = -0.1010795763432845;

export function Rl04DurationExtrapolationChart({
  annual,
  extrapolation,
}: {
  annual: NmRl04AnnualRow[];
  extrapolation: NmRl04ExtrapolationRow[];
}) {
  const [showExtrapolatedTail, setShowExtrapolatedTail] = useState(true);

  const durExtrap = extrapolation.filter((r) => r.y_var === "mean_dur_q");

  const historicalPoints = annual.map((r) => {
    const yr = Number(r.start_year);
    const t = yr - 2000;
    const olsPred = Number((A0_CENTERED_DUR + A1_DUR * t).toFixed(4));
    return {
      year: yr,
      "Duración Observada Cerrados (trim)": Number(
        Number(r.mean_dur_q).toFixed(3)
      ),
      "Duración Incl. Vigentes (trim)": Number(
        Number(r.mean_dur_q_incl_active).toFixed(3)
      ),
      "Recta MCO Soporte Válido (2000–2019)": olsPred,
      n_closed: Number(r.n_closed_starts),
      zona: yr <= 2019 ? "Soporte Válido (2000–2019)" : "Cola Censurada (2020–2023)",
    };
  });

  const futurePoints = [2024, 2025, 2026, 2027].map((yr) => {
    const extRow = durExtrap.find((e) => Number(e.year) === yr);
    const t = yr - 2000;
    const pred = extRow
      ? Number(Number(extRow.y_pred_from_2000_2019).toFixed(4))
      : Number((A0_CENTERED_DUR + A1_DUR * t).toFixed(4));
    return {
      year: yr,
      "Duración Observada Cerrados (trim)": null,
      "Duración Incl. Vigentes (trim)": null,
      "Recta MCO Soporte Válido (2000–2019)": pred,
      n_closed: 0,
      zona: "Extrapolación Fuera de Soporte (Imposible < 0)",
    };
  });

  const chartData = showExtrapolatedTail
    ? [...historicalPoints, ...futurePoints]
    : historicalPoints.filter((p) => p.year <= 2019);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-slate-50 px-3 py-2 text-xs">
        <span className="font-semibold text-slate-700">
          Modo interactivo Caso 1 (IDEA-RL-04):
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setShowExtrapolatedTail(true)}
            className={`rounded-md px-3 py-1 font-semibold transition-colors ${
              showExtrapolatedTail
                ? "bg-blue-700 text-white"
                : "bg-white text-slate-700 ring-1 ring-slate-300"
            }`}
          >
            Mostrar Extrapolación 2020–2027 (Fallo &lt; 0)
          </button>
          <button
            type="button"
            onClick={() => setShowExtrapolatedTail(false)}
            className={`rounded-md px-3 py-1 font-semibold transition-colors ${
              !showExtrapolatedTail
                ? "bg-blue-700 text-white"
                : "bg-white text-slate-700 ring-1 ring-slate-300"
            }`}
          >
            Sólo Soporte Válido 2000–2019 (R² = 0.9729)
          </button>
        </div>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={chartData}
            margin={{ top: 12, right: 20, left: 10, bottom: 10 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="year" tick={{ fontSize: 11, fill: "#0f172a" }} />
            <YAxis
              domain={showExtrapolatedTail ? [-6, 22] : [0, 22]}
              unit="q"
              tick={{ fontSize: 11, fill: "#334155" }}
            />
            <Tooltip
              contentStyle={{
                fontSize: "12px",
                borderRadius: "8px",
                borderColor: "#cbd5e1",
              }}
            />
            <Legend wrapperStyle={{ fontSize: "11px" }} />
            <ReferenceLine
              y={0}
              stroke="#dc2626"
              strokeWidth={2}
              label={{
                value: "Frontera física dur_q = 0 trimestres",
                fill: "#dc2626",
                fontSize: 10,
                position: "insideBottomLeft",
              }}
            />
            <ReferenceLine
              x={2019}
              stroke="#64748b"
              strokeDasharray="4 4"
              label={{
                value: "Fin soporte válido (2019)",
                fill: "#475569",
                fontSize: 10,
                position: "top",
              }}
            />
            <Line
              type="monotone"
              dataKey="Duración Observada Cerrados (trim)"
              stroke="#1d4ed8"
              strokeWidth={3}
              dot={{ r: 3.5 }}
              connectNulls={false}
            />
            <Line
              type="monotone"
              dataKey="Recta MCO Soporte Válido (2000–2019)"
              stroke="#dc2626"
              strokeWidth={2.5}
              strokeDasharray="6 4"
              dot={{ r: 2.5 }}
            />
            <Line
              type="monotone"
              dataKey="Duración Incl. Vigentes (trim)"
              stroke="#059669"
              strokeWidth={1.8}
              dot={false}
              connectNulls={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function Rl04SkillsCensoredCollapseChart({
  annual,
}: {
  annual: NmRl04AnnualRow[];
}) {
  const data = annual.map((r) => {
    const yr = Number(r.start_year);
    const t = yr - 2000;
    return {
      year: yr,
      "Skills Esenciales Observadas": Number(Number(r.mean_skills).toFixed(2)),
      "MCO Soporte Válido 2000–2019 (R² = 0.7475)":
        yr <= 2019
          ? Number((A0_CENTERED_SKILLS_VALID + A1_SKILLS_VALID * t).toFixed(2))
          : null,
      "MCO Contaminado 2000–2023 (R² = 0.0826)": Number(
        (A0_SKILLS_CENSORED + A1_SKILLS_CENSORED * yr).toFixed(2)
      ),
      n_starts: Number(r.n_starts),
    };
  });

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={data}
          margin={{ top: 12, right: 20, left: 10, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="year" tick={{ fontSize: 11, fill: "#0f172a" }} />
          <YAxis
            domain={[13, 26]}
            tick={{ fontSize: 11, fill: "#334155" }}
          />
          <Tooltip
            contentStyle={{
              fontSize: "12px",
              borderRadius: "8px",
              borderColor: "#cbd5e1",
            }}
          />
          <Legend wrapperStyle={{ fontSize: "11px" }} />
          <ReferenceLine
            x={2019}
            stroke="#64748b"
            strokeDasharray="4 4"
          />
          <Line
            type="monotone"
            dataKey="Skills Esenciales Observadas"
            stroke="#0f172a"
            strokeWidth={2.5}
            dot={{ r: 3.5 }}
          />
          <Line
            type="monotone"
            dataKey="MCO Soporte Válido 2000–2019 (R² = 0.7475)"
            stroke="#059669"
            strokeWidth={3}
            dot={false}
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="MCO Contaminado 2000–2023 (R² = 0.0826)"
            stroke="#d97706"
            strokeWidth={2.5}
            strokeDasharray="5 5"
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Evaluates cubic Lagrange polynomial P3(q) anchored at q in {4, 8, 20, 40}
 * with exact empirical survival values S(4)=0.660880, S(8)=0.370539, S(20)=0.135783, S(40)=0.042983.
 */
function evalCubicLagrangeP3(q: number): number {
  const nodes = [4, 8, 20, 40];
  const values = [
    0.6608799760550733,
    0.3705386148443945,
    0.1357834298187339,
    0.0429828467695033,
  ];
  let sum = 0;
  for (let i = 0; i < 4; i++) {
    let li = 1;
    for (let j = 0; j < 4; j++) {
      if (i !== j) {
        li *= (q - nodes[j]) / (nodes[i] - nodes[j]);
      }
    }
    sum += values[i] * li;
  }
  return sum;
}

export function Lg01SurvivalAndP3Chart({
  survival,
  milestones,
}: {
  survival: NmLg01SurvivalRow[];
  milestones: NmLg01P3MilestoneRow[];
}) {
  const [includeExtrapolationQ48, setIncludeExtrapolationQ48] = useState(true);

  const baseData = survival.map((s) => {
    const q = Number(s.quarter_q);
    const p3 = evalCubicLagrangeP3(q);
    return {
      quarter_q: q,
      "Supervivencia Empírica Exacta S(q) (%)": Number(
        (Number(s.survival_prob_s_q) * 100).toFixed(2)
      ),
      "Polinomio Cúbico Lagrange P₃(q) (%)": Number((p3 * 100).toFixed(2)),
      esNodoAncla: [4, 8, 20, 40].includes(q),
    };
  });

  const q48Row = milestones.find((m) => Number(m.quarter_q) === 48);
  const extrapData = [44, 48].map((q) => {
    const p3 = evalCubicLagrangeP3(q);
    const trueS =
      q === 48 && q48Row ? Number(q48Row.true_s_q) * 100 : null;
    return {
      quarter_q: q,
      "Supervivencia Empírica Exacta S(q) (%)":
        trueS !== null ? Number(trueS.toFixed(2)) : null,
      "Polinomio Cúbico Lagrange P₃(q) (%)": Number((p3 * 100).toFixed(2)),
      esNodoAncla: false,
    };
  });

  const chartData = includeExtrapolationQ48
    ? [...baseData, ...extrapData]
    : baseData;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-slate-50 px-3 py-2 text-xs">
        <span className="font-semibold text-slate-700">
          Modo interactivo Caso 2 (IDEA-LG-01 · Hitos q &isin; &#123;4, 8, 20, 40&#125;):
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setIncludeExtrapolationQ48(true)}
            className={`rounded-md px-3 py-1 font-semibold transition-colors ${
              includeExtrapolationQ48
                ? "bg-purple-700 text-white"
                : "bg-white text-slate-700 ring-1 ring-slate-300"
            }`}
          >
            Incluir Extrapolación q = 48 (-59.84%)
          </button>
          <button
            type="button"
            onClick={() => setIncludeExtrapolationQ48(false)}
            className={`rounded-md px-3 py-1 font-semibold transition-colors ${
              !includeExtrapolationQ48
                ? "bg-purple-700 text-white"
                : "bg-white text-slate-700 ring-1 ring-slate-300"
            }`}
          >
            Sólo Dominio Interno q = 1..40
          </button>
        </div>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={chartData}
            margin={{ top: 12, right: 20, left: 10, bottom: 10 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey="quarter_q"
              tickFormatter={(v) => `${v}q`}
              tick={{ fontSize: 11, fill: "#0f172a" }}
            />
            <YAxis
              unit="%"
              domain={includeExtrapolationQ48 ? [-65, 105] : [0, 105]}
              tick={{ fontSize: 11, fill: "#334155" }}
            />
            <Tooltip
              formatter={(v: unknown) => [`${v}%`, ""]}
              labelFormatter={(l) => `Trimestre q = ${l} (${(Number(l) / 4).toFixed(2)} años)`}
              contentStyle={{
                fontSize: "12px",
                borderRadius: "8px",
                borderColor: "#cbd5e1",
              }}
            />
            <Legend wrapperStyle={{ fontSize: "11px" }} />
            <ReferenceLine
              y={0}
              stroke="#dc2626"
              strokeWidth={2}
              label={{
                value: "Límite físico S(q) = 0%",
                fill: "#dc2626",
                fontSize: 10,
                position: "insideBottomLeft",
              }}
            />
            <ReferenceLine
              x={40}
              stroke="#64748b"
              strokeDasharray="4 4"
            />
            <Line
              type="monotone"
              dataKey="Supervivencia Empírica Exacta S(q) (%)"
              stroke="#1d4ed8"
              strokeWidth={3}
              dot={{ r: 2.5 }}
            />
            <Line
              type="monotone"
              dataKey="Polinomio Cúbico Lagrange P₃(q) (%)"
              stroke="#7c3aed"
              strokeWidth={2.5}
              strokeDasharray="6 4"
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function Lg01RungeVsChebyshevChart({
  runge,
}: {
  runge: NmLg01RungeRow[];
}) {
  const degrees = [3, 5, 8, 12, 16];
  const data = degrees.map((deg) => {
    const eq = runge.find(
      (r) =>
        Number(r.degree) === deg && r.node_strategy.includes("Equispaced")
    );
    const ch = runge.find(
      (r) =>
        Number(r.degree) === deg && r.node_strategy.includes("Chebyshev")
    );
    const p2 = runge.find(
      (r) =>
        Number(r.degree) === deg && r.node_strategy.includes("Piecewise")
    );
    return {
      grado: `Grado ${deg}`,
      "Lagrange Global Equiespaciado (E∞)": Number(
        Number(eq?.max_abs_err ?? 0).toFixed(4)
      ),
      "Lagrange Chebyshev-Lobatto (E∞)": Number(
        Number(ch?.max_abs_err ?? 0).toFixed(4)
      ),
      "Lagrange Local por Tramos P₂ (E∞)": Number(
        Number(p2?.max_abs_err ?? 0).toFixed(4)
      ),
    };
  });

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 12, right: 20, left: 10, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="grado"
            tick={{ fontSize: 11, fill: "#0f172a", fontWeight: 600 }}
          />
          <YAxis tick={{ fontSize: 11, fill: "#334155" }} />
          <Tooltip
            contentStyle={{
              fontSize: "12px",
              borderRadius: "8px",
              borderColor: "#cbd5e1",
            }}
          />
          <Legend wrapperStyle={{ fontSize: "11px" }} />
          <Bar
            dataKey="Lagrange Global Equiespaciado (E∞)"
            fill="#dc2626"
            radius={[3, 3, 0, 0]}
          />
          <Bar
            dataKey="Lagrange Chebyshev-Lobatto (E∞)"
            fill="#059669"
            radius={[3, 3, 0, 0]}
          />
          <Bar
            dataKey="Lagrange Local por Tramos P₂ (E∞)"
            fill="#1d4ed8"
            radius={[3, 3, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
