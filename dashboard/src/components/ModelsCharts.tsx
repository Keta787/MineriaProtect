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
  LineChart,
  Line,
  Cell,
} from "recharts";
import type {
  SupervisedBenchmarkRow,
  NaiveBayesIscoRow,
  KnnPurityRow,
  KMeansProfileRow,
  Ward25kProfileRow,
} from "@/lib/db";

export function SupervisedBenchmarkChart({
  rows,
}: {
  rows: SupervisedBenchmarkRow[];
}) {
  // Show key representative models across all 4 notebooks (6.0, 7.0, 7.1, 7.2)
  const selected = rows.filter(
    (r) =>
      r.modelo.includes("Ref 2") ||
      r.modelo.includes("Ref 3") ||
      r.modelo.includes("Árbol 1 · ISCO [Recall") ||
      r.modelo.includes("Árbol 2 · Education level [Recall") ||
      r.modelo.includes("Árbol 3 · Skills [Recall") ||
      r.modelo.includes("NB-G") ||
      r.modelo.includes("NB-B") ||
      r.modelo.includes("NB-H") ||
      r.modelo.includes("KNN-D") ||
      r.modelo.includes("KNN-G") ||
      r.modelo.includes("KNN-W")
  );

  const data = selected.map((r) => ({
    modelo: r.modelo
      .replace(" [Recall (balanced)]", " (bal)")
      .replace("Ref 3 · Techo 6.0 (Logística OHE)", "6.0 Logística OHE")
      .replace("Ref 2 · Trivial Todo-Positivo (1)", "Ref Todo-1"),
    "ROC-AUC (Test)": Number(Number(r.test_roc_auc).toFixed(4)),
    "F1 Clase 1 (Test)": Number(Number(r.test_f1_clase_1).toFixed(4)),
    "PR-AUC (Test)": r.test_pr_auc ? Number(Number(r.test_pr_auc).toFixed(4)) : 0,
  }));

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 12, right: 20, left: 10, bottom: 45 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="modelo"
            angle={-25}
            textAnchor="end"
            height={65}
            tick={{ fontSize: 10, fill: "#0f172a" }}
            interval={0}
          />
          <YAxis
            domain={[0, 0.8]}
            tick={{ fontSize: 11, fill: "#334155" }}
          />
          <Tooltip
            contentStyle={{
              fontSize: "12px",
              borderRadius: "8px",
              borderColor: "#cbd5e1",
            }}
          />
          <Legend wrapperStyle={{ fontSize: "12px" }} />
          <Bar
            dataKey="ROC-AUC (Test)"
            fill="#1d4ed8"
            radius={[3, 3, 0, 0]}
          />
          <Bar
            dataKey="F1 Clase 1 (Test)"
            fill="#059669"
            radius={[3, 3, 0, 0]}
          />
          <Bar
            dataKey="PR-AUC (Test)"
            fill="#d97706"
            radius={[3, 3, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function NaiveBayesIscoTrainVsTestChart({
  rows,
}: {
  rows: NaiveBayesIscoRow[];
}) {
  const data = rows.map((r) => ({
    grupo: `${r.isco_major} · ${r.gran_grupo_isco.split("·")[1]?.trim().slice(0, 18) ?? r.isco_major}`,
    "Tasa Observada Train (%)": Number(r.tasa_observada_train_pct),
    "Tasa Confirmada Test (%)": Number(r.tasa_confirmada_test_pct),
    "Predicción NB-H Test (%)": Number(r.prob_media_nb_h_test_pct),
  }));

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 12, right: 20, left: 10, bottom: 45 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="grupo"
            angle={-25}
            textAnchor="end"
            height={65}
            tick={{ fontSize: 10, fill: "#0f172a" }}
            interval={0}
          />
          <YAxis
            unit="%"
            domain={[0, 38]}
            tick={{ fontSize: 11, fill: "#334155" }}
          />
          <Tooltip
            formatter={(v: unknown) => [`${v}%`, ""]}
            contentStyle={{
              fontSize: "12px",
              borderRadius: "8px",
              borderColor: "#cbd5e1",
            }}
          />
          <Legend wrapperStyle={{ fontSize: "12px" }} />
          <Bar
            dataKey="Tasa Observada Train (%)"
            fill="#0284c7"
            radius={[3, 3, 0, 0]}
          />
          <Bar
            dataKey="Tasa Confirmada Test (%)"
            fill="#059669"
            radius={[3, 3, 0, 0]}
          />
          <Bar
            dataKey="Predicción NB-H Test (%)"
            fill="#7c3aed"
            radius={[3, 3, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function KnnPurityGeometryChart({ rows }: { rows: KnnPurityRow[] }) {
  const knnW = rows.filter((r) => r.modelo_id === "KNN-D" || r.modelo_id === "KNN-W");
  const data = knnW.map((r) => ({
    peso: `w = ${r.peso_bloque_w} (${r.modelo_id})`,
    "Mismo Oficio ESCO (%)": Number(r.pureza_misma_ocupacion_esco_pct),
    "Mismo Grupo ISCO (%)": Number(r.pureza_mismo_grupo_isco_pct),
    "Misma Clase Reincide (%)": Number(r.pureza_misma_clase_reincide_pct),
  }));

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={data}
          margin={{ top: 12, right: 20, left: 10, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="peso"
            tick={{ fontSize: 10, fill: "#0f172a" }}
            interval={0}
          />
          <YAxis
            unit="%"
            domain={[0, 100]}
            tick={{ fontSize: 11, fill: "#334155" }}
          />
          <Tooltip
            formatter={(v: unknown) => [`${v}%`, ""]}
            contentStyle={{
              fontSize: "12px",
              borderRadius: "8px",
              borderColor: "#cbd5e1",
            }}
          />
          <Legend wrapperStyle={{ fontSize: "12px" }} />
          <Line
            type="monotone"
            dataKey="Mismo Oficio ESCO (%)"
            stroke="#1d4ed8"
            strokeWidth={3}
            dot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="Mismo Grupo ISCO (%)"
            stroke="#059669"
            strokeWidth={2.5}
            dot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="Misma Clase Reincide (%)"
            stroke="#d97706"
            strokeWidth={2.5}
            strokeDasharray="4 4"
            dot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ClusteringTrainVsTestComparisonChart({
  kmeansProfiles,
  ward25kProfiles,
}: {
  kmeansProfiles: KMeansProfileRow[];
  ward25kProfiles: Ward25kProfileRow[];
}) {
  const kmPersons = kmeansProfiles.filter((r) =>
    r.vista.toLowerCase().includes("personas")
  );

  const data = [0, 1, 2, 3].map((cid) => {
    const km = kmPersons.find((r) => Number(r.cluster) === cid);
    const wd = ward25kProfiles.find((r) => Number(r.cluster) === cid);
    return {
      cluster: `Clúster ${cid}`,
      "K-Means Train (%)": Number(km?.pct_train ?? 0),
      "K-Means Test (%)": Number(km?.pct_test ?? 0),
      "Ward Muestra Directa 25k Train (%)": Number(
        wd?.pct_muestra_descubrimiento ?? 0
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
            dataKey="cluster"
            tick={{ fontSize: 12, fill: "#0f172a", fontWeight: 600 }}
          />
          <YAxis
            unit="%"
            domain={[0, 52]}
            tick={{ fontSize: 11, fill: "#334155" }}
          />
          <Tooltip
            formatter={(v: unknown) => [`${v}%`, ""]}
            contentStyle={{
              fontSize: "12px",
              borderRadius: "8px",
              borderColor: "#cbd5e1",
            }}
          />
          <Legend wrapperStyle={{ fontSize: "12px" }} />
          <Bar
            dataKey="K-Means Train (%)"
            fill="#1d4ed8"
            radius={[3, 3, 0, 0]}
          />
          <Bar
            dataKey="K-Means Test (%)"
            fill="#059669"
            radius={[3, 3, 0, 0]}
          />
          <Bar
            dataKey="Ward Muestra Directa 25k Train (%)"
            fill="#7c3aed"
            radius={[3, 3, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
