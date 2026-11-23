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
import type { PersonExperienceTimelineRow } from "@/lib/db";
import { ESCO_LABEL_GLOSS_ES } from "@/lib/isco-labels";

export function PersonTimelineDurationChart({
  experiences,
}: {
  experiences: PersonExperienceTimelineRow[];
}) {
  const data = experiences.map((e) => {
    const gloss = ESCO_LABEL_GLOSS_ES[e.occupation_label.toLowerCase()];
    return {
      empleo: `#${e.job_order} (${e.start_year}Q${e.start_quarter})`,
      "Duración (Trimestres)": Number(e.dur_q),
      oficio: gloss
        ? `${gloss} (${e.occupation_label})`
        : e.occupation_label,
      codigo: e.occupation_code,
      reincide: Number(e.reincide) === 1,
    };
  });

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 10, right: 20, left: 10, bottom: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="empleo"
            angle={-15}
            textAnchor="end"
            height={45}
            tick={{ fontSize: 11, fill: "#0f172a", fontWeight: 600 }}
            interval={0}
          />
          <YAxis tick={{ fontSize: 12, fill: "#334155" }} />
          <Tooltip
            formatter={(
              value: unknown,
              _name: string,
              props: {
                payload?: { oficio?: string; codigo?: string; reincide?: boolean };
              }
            ) => [
              `${value} trimestres — ${props?.payload?.oficio ?? ""} (ESCO ${
                props?.payload?.codigo ?? ""
              }) · ${props?.payload?.reincide ? "Repite ocupación" : "Única vez"}`,
              "Duración",
            ]}
            contentStyle={{
              fontSize: "12px",
              borderRadius: "8px",
              borderColor: "#cbd5e1",
            }}
          />
          <Bar dataKey="Duración (Trimestres)" radius={[6, 6, 0, 0]}>
            {data.map((entry, idx) => (
              <Cell
                key={`dur-${idx}`}
                fill={entry.reincide ? "#d97706" : "#1d4ed8"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function PersonSkillsEvolutionChart({
  experiences,
}: {
  experiences: PersonExperienceTimelineRow[];
}) {
  const data = experiences.map((e) => {
    const gloss = ESCO_LABEL_GLOSS_ES[e.occupation_label.toLowerCase()];
    return {
      empleo: `#${e.job_order}`,
      oficio: gloss ?? e.occupation_label,
      codigo: e.occupation_code,
      "Habilidades Prácticas (C)": Number(e.n_skills_competence_a),
      "Conocimientos Teóricos (K)": Number(e.n_skills_knowledge_a),
    };
  });

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 10, right: 20, left: 10, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="empleo"
            tick={{ fontSize: 12, fill: "#0f172a", fontWeight: 600 }}
          />
          <YAxis tick={{ fontSize: 12, fill: "#334155" }} />
          <Tooltip
            labelFormatter={(label, payload) => {
              const p = payload?.[0]?.payload as
                | { oficio?: string; codigo?: string }
                | undefined;
              return `${label} — ${p?.oficio ?? ""} (ESCO ${p?.codigo ?? ""})`;
            }}
            contentStyle={{
              fontSize: "12px",
              borderRadius: "8px",
              borderColor: "#cbd5e1",
            }}
          />
          <Legend wrapperStyle={{ fontSize: "12px" }} />
          <Bar
            dataKey="Habilidades Prácticas (C)"
            stackId="a"
            fill="#0284c7"
          />
          <Bar
            dataKey="Conocimientos Teóricos (K)"
            stackId="a"
            fill="#059669"
            radius={[6, 6, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
