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
import type { PersonExperienceJoinedRow } from "@/lib/db";

export function PersonTimelineDurationChart({
  experiences,
}: {
  experiences: PersonExperienceJoinedRow[];
}) {
  const data = experiences.map((e) => ({
    empleo: `#${e.job_order} (${e.start_year}Q${e.start_quarter})`,
    "Duración (Trimestres)": Number(e.dur_q),
    oficio: `${e.occupation_label} (ESCO ${e.occupation_code})`,
    reincide: Number(e.reincide) === 1,
    vigente: Boolean(e.es_vigente),
  }));

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 10, right: 20, left: 10, bottom: 25 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="empleo"
            angle={-15}
            textAnchor="end"
            height={45}
            tick={{ fontSize: 11, fill: "#0f172a" }}
            interval={0}
          />
          <YAxis
            label={{
              value: "Trimestres (dur_q)",
              angle: -90,
              position: "insideLeft",
              style: { fontSize: 11, fill: "#334155" },
            }}
            tick={{ fontSize: 11, fill: "#334155" }}
          />
          <Tooltip
            formatter={(value: unknown, _name: string, props: { payload?: { oficio?: string; reincide?: boolean } }) => [
              `${value} trimestres — ${props?.payload?.oficio ?? ""} (${
                props?.payload?.reincide ? "Reincidente: Sí" : "Oficio único"
              })`,
              "Duración",
            ]}
            contentStyle={{
              fontSize: "12px",
              borderRadius: "8px",
              borderColor: "#cbd5e1",
            }}
          />
          <Bar
            dataKey="Duración (Trimestres)"
            name="Duración en trimestres (Ámbar = Reincidente / Azul = Oficio único)"
            radius={[4, 4, 0, 0]}
          >
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
  experiences: PersonExperienceJoinedRow[];
}) {
  const data = experiences.map((e) => ({
    empleo: `#${e.job_order} (${e.occupation_code})`,
    "Habilidades Prácticas (C)": Number(e.n_skills_competence_a),
    "Conocimientos Teóricos (K)": Number(e.n_skills_knowledge_a),
    TotalEsenciales: Number(e.n_skills_essential_a),
    oficio: e.occupation_label,
  }));

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 10, right: 20, left: 10, bottom: 25 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="empleo"
            angle={-15}
            textAnchor="end"
            height={45}
            tick={{ fontSize: 11, fill: "#0f172a" }}
            interval={0}
          />
          <YAxis tick={{ fontSize: 11, fill: "#334155" }} />
          <Tooltip
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
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
