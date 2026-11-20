"""Spanish-labeled figure generation (knn01 to knn13) for Notebook 7.2 (KNN), strictly without emojis."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import (
    KNNConfig,
    MODEL_KNN_D,
    MODEL_KNN_G,
    MODEL_KNN_W,
    MODEL_LABELS_ES,
    MODEL_ORDER,
)
from .evaluation import (
    KNNTestEvaluationBundle,
    KNNThresholdBundle,
    KNNTuningBundle,
)
from .geometry import GeometryExperimentBundle
from .patterns import KNNPatternsBundle
from .pilot_benchmark import CostCurveBundle
from .version_comparison import ScaleOutlierSensitivityBundle

MODEL_COLORS: Dict[str, str] = {
    MODEL_KNN_D: "#1f77b4",
    MODEL_KNN_G: "#ff7f0e",
    MODEL_KNN_W: "#2ca02c",
    "NB-H": "#9467bd",
    "NB-B": "#8c564b",
    "LOGIT_6_0": "#d62728",
    "HGB_6_0": "#17becf",
}


class KNNPlotter:
    """Render and save all Notebook 7.2 figures in Spanish without emojis or decorative symbols."""

    def __init__(self, config: KNNConfig) -> None:
        self.config = config
        self.config.figures_dir.mkdir(parents=True, exist_ok=True)

    def _save(self, fig: plt.Figure, filename: str) -> Path:
        out_path = self.config.figures_dir / filename
        fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return out_path

    def plot_scale_audit(self, scale_audit_df: pd.DataFrame) -> Path:
        """KNN01: Standard deviation before vs after train-only audited scaling across dense_clean."""
        df = scale_audit_df.copy()
        y_pos = np.arange(len(df))
        fig, ax = plt.subplots(figsize=(11.5, 6.4))

        std_before = df["std_antes_train"].to_numpy(dtype=float)
        std_after = df["std_despues_train"].fillna(0.0).to_numpy(dtype=float)

        h = 0.38
        ax.barh(y_pos + h / 2, std_before, height=h, color="#7f7f7f", alpha=0.80, label="DE antes del escalado (dense_clean)")
        bar_colors = [
            "#d62728" if pd.isna(v) else ("#ff7f0e" if "Binaria" in str(d) else "#1f77b4")
            for v, d in zip(df["std_despues_train"], df["decision_escala_knn"])
        ]
        ax.barh(y_pos - h / 2, std_after, height=h, color=bar_colors, alpha=0.90, label="DE después (azul=estandarizada, naranja=binaria 0/1, 0=descartada)")

        ax.set_yticks(y_pos)
        ax.set_yticklabels(df["columna"].tolist(), fontsize=9.0)
        ax.invert_yaxis()
        ax.axvline(1.0, color="#1f77b4", linestyle="--", linewidth=1.1, alpha=0.7)
        ax.set_xlabel("Desviación estándar en Train (Versión A)", fontsize=10.0)
        ax.set_title("KNN01 · Auditoría de escala en las 14 columnas de dense_clean (antes vs. después, solo Train)", fontsize=11.5, pad=10)
        ax.legend(loc="lower right", fontsize=8.5)
        ax.grid(axis="x", alpha=0.25)
        return self._save(fig, "knn01_auditoria_escala_dense.png")

    def plot_geometry_and_purity(self, geo_bundle: GeometryExperimentBundle) -> Path:
        """KNN02: Distance contrast and neighbor purity vs block weights across KNN-D, KNN-G, KNN-W."""
        df = geo_bundle.geometry_table
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 5.2))

        d_row = df.loc[df["modelo_id"] == MODEL_KNN_D].iloc[0]
        g_df = df.loc[df["modelo_id"] == MODEL_KNN_G].sort_values("peso_bloque_w")
        w_df = df.loc[df["modelo_id"] == MODEL_KNN_W].sort_values("peso_bloque_w")

        # Panel 1: Distance contrast CV = std(d) / mean(d)
        ax1.axhline(float(d_row["contraste_cv_std_sobre_media"]), color=MODEL_COLORS[MODEL_KNN_D], linestyle="--", linewidth=1.6, label=f"KNN-D (w=0): CV={d_row['contraste_cv_std_sobre_media']:.3f}")
        ax1.plot(g_df["peso_bloque_w"], g_df["contraste_cv_std_sobre_media"], marker="o", color=MODEL_COLORS[MODEL_KNN_G], linewidth=2.0, label="KNN-G (21 cols · proxy ISCO)")
        ax1.plot(w_df["peso_bloque_w"], w_df["contraste_cv_std_sobre_media"], marker="s", color=MODEL_COLORS[MODEL_KNN_W], linewidth=2.0, label="KNN-W (2,978 cols · OHE ESCO)")
        ax1.set_xscale("log", base=2)
        ax1.set_xlabel("Peso del bloque ocupacional (w_g o w, escala log2)", fontsize=9.5)
        ax1.set_ylabel("Contraste de distancias CV = DE(d) / Media(d)", fontsize=9.5)
        ax1.set_title("Concentración de distancias según dimensionalidad y peso", fontsize=10.5)
        ax1.legend(fontsize=8.5)
        ax1.grid(alpha=0.25)

        # Panel 2: Neighbor purity (% same occupation & % same ISCO major)
        ax2.axhline(float(d_row["pureza_misma_ocupacion_esco_pct"]), color=MODEL_COLORS[MODEL_KNN_D], linestyle=":", linewidth=1.4, label=f"KNN-D misma ocupación ({d_row['pureza_misma_ocupacion_esco_pct']:.1f}%)")
        ax2.axhline(float(d_row["pureza_mismo_grupo_isco_pct"]), color=MODEL_COLORS[MODEL_KNN_D], linestyle="--", linewidth=1.4, label=f"KNN-D mismo ISCO ({d_row['pureza_mismo_grupo_isco_pct']:.1f}%)")
        ax2.plot(g_df["peso_bloque_w"], g_df["pureza_mismo_grupo_isco_pct"], marker="o", linestyle="--", color=MODEL_COLORS[MODEL_KNN_G], linewidth=2.0, label="KNN-G · mismo gran grupo ISCO (%)")
        ax2.plot(g_df["peso_bloque_w"], g_df["pureza_misma_ocupacion_esco_pct"], marker="o", linestyle="-", color="#c45100", linewidth=1.6, label="KNN-G · misma ocupación ESCO (%)")
        ax2.plot(w_df["peso_bloque_w"], w_df["pureza_mismo_grupo_isco_pct"], marker="s", linestyle="--", color="#5cb85c", linewidth=1.8, label="KNN-W · mismo gran grupo ISCO (%)")
        ax2.plot(w_df["peso_bloque_w"], w_df["pureza_misma_ocupacion_esco_pct"], marker="s", linestyle="-", color=MODEL_COLORS[MODEL_KNN_W], linewidth=2.2, label="KNN-W · misma ocupación ESCO (%)")
        ax2.set_xscale("log", base=2)
        ax2.set_xlabel("Peso del bloque ocupacional (w_g o w, escala log2)", fontsize=9.5)
        ax2.set_ylabel("Pureza promedio en los k vecinos (%)", fontsize=9.5)
        ax2.set_title("Pureza ocupacional de los vecinos cercanos", fontsize=10.5)
        ax2.legend(fontsize=7.8, loc="center right")
        ax2.grid(alpha=0.25)

        fig.suptitle("KNN02 · Geometría, concentración de distancias y pureza de vecinos (Train · muestra fija)", fontsize=12.0, y=1.02)
        return self._save(fig, "knn02_geometria_contraste_y_pureza.png")

    def plot_scale_and_outlier_sensitivity(self, sens_bundle: ScaleOutlierSensitivityBundle) -> Path:
        """KNN03: Tukey extreme shares per continuous feature and 5-fold CV comparison across data regimes."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.0, 5.5))

        tk = sens_bundle.tukey_extremes_table
        tk_cont = tk.loc[tk["continua_activa_knn"]].sort_values("pct_fuera_tukey_train", ascending=True)
        y1 = np.arange(len(tk_cont))
        ax1.barh(y1, tk_cont["pct_fuera_tukey_train"].to_numpy(dtype=float), color="#d95f02", alpha=0.85)
        for i, (_, r) in enumerate(tk_cont.iterrows()):
            ax1.text(
                float(r["pct_fuera_tukey_train"]) + 0.25,
                i,
                f"{r['pct_fuera_tukey_train']:.2f}% (inflación DE: {r['factor_inflacion_std_por_extremos']:.2f}x)",
                va="center",
                fontsize=8.2,
            )
        ax1.set_yticks(y1)
        ax1.set_yticklabels(tk_cont["columna"].tolist(), fontsize=9.0)
        ax1.set_xlim(0, float(tk_cont["pct_fuera_tukey_train"].max()) * 1.45 + 1.0)
        ax1.set_xlabel("Filas fuera de vallas de Tukey en Train (%)", fontsize=9.5)
        ax1.set_title("Extremos de Tukey e inflación de DE en continuas activas", fontsize=10.5)
        ax1.grid(axis="x", alpha=0.25)

        cv_df = sens_bundle.cv_sensitivity_table
        short_names = {
            "R1_A_crudo": "A crudo\n(sin reescalar)",
            "R2_A_escalado": "A escalado\n(referencia)",
            "R3_A_wins_tukey": "A winsorizada\n(Tukey 6 cols)",
            "R4_A_solo_inliers": "A solo inliers\n(sin outliers)",
            "R5_B_iqr": "Versión B\n(IQR 4 cols)",
        }
        reg_order = ["R1_A_crudo", "R2_A_escalado", "R3_A_wins_tukey", "R4_A_solo_inliers", "R5_B_iqr"]
        x2 = np.arange(len(reg_order))
        w_bar = 0.36
        for offset, metric_name, color in [
            (-w_bar / 2, "euclidean", "#1f77b4"),
            (w_bar / 2, "manhattan", "#2ca02c"),
        ]:
            sub_m = cv_df.loc[cv_df["metrica"] == metric_name].set_index("regimen_id")
            vals = [float(sub_m.loc[r, "pr_auc_cv_media"]) for r in reg_order if r in sub_m.index]
            stds = [float(sub_m.loc[r, "pr_auc_cv_std"]) for r in reg_order if r in sub_m.index]
            ax2.bar(x2 + offset, vals, width=w_bar, yerr=stds, capsize=3, color=color, alpha=0.88, label=f"Métrica {metric_name}")

        ax2.set_xticks(x2)
        ax2.set_xticklabels([short_names[r] for r in reg_order], fontsize=8.3)
        all_v = cv_df["pr_auc_cv_media"].to_numpy(dtype=float)
        ax2.set_ylim(max(0.0, float(all_v.min()) - 0.025), float(all_v.max()) + 0.020)
        ax2.set_ylabel("PR-AUC medio en CV agrupada (5 pliegues)", fontsize=9.5)
        ax2.set_title("Sensibilidad de KNN-D a escala, winsorización, exclusión y Versión B", fontsize=10.5)
        ax2.legend(fontsize=8.5)
        ax2.grid(axis="y", alpha=0.25)

        fig.suptitle("KNN03 · Diagnóstico de valores extremos (Tukey) y sensibilidad en CV agrupada (submuestra 10 %)", fontsize=12.0, y=1.02)
        return self._save(fig, "knn03_sensibilidad_escala_y_outliers.png")

    def plot_tuning_validation_curves(self, tuning_bundle: KNNTuningBundle) -> Path:
        """KNN04: Validation curves for k, block weights w_g/w, and 1/k score resolution."""
        att = tuning_bundle.tuning_all_attempts_table
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16.5, 4.9))

        # Panel 1: PR-AUC vs k for winning (metric, block_weight) of each variant
        for mid in MODEL_ORDER:
            sp = tuning_bundle.winner_specs[mid]
            for wt, ls in [("uniform", "--"), ("distance", "-")]:
                sub = att.loc[
                    (att["modelo_id"] == mid)
                    & (att["metrica"] == sp.metric)
                    & (np.isclose(att["peso_bloque"], sp.block_weight))
                    & (att["pesos"] == wt)
                ].sort_values("k_vecinos")
                if sub.empty:
                    continue
                ax1.plot(
                    sub["k_vecinos"],
                    sub["pr_auc_cv_media"],
                    marker="o",
                    linestyle=ls,
                    color=MODEL_COLORS[mid],
                    linewidth=1.8 if wt == "distance" else 1.2,
                    alpha=0.95 if wt == "distance" else 0.65,
                    label=f"{mid} ({wt})",
                )
        ax1.set_xscale("log")
        ax1.set_xlabel("Número de vecinos k (escala log)", fontsize=9.0)
        ax1.set_ylabel("PR-AUC medio en CV (5 pliegues)", fontsize=9.0)
        ax1.set_title("Curva de validación por k y ponderación", fontsize=10.0)
        ax1.legend(fontsize=7.3, ncol=2)
        ax1.grid(alpha=0.25)

        # Panel 2: PR-AUC vs block weight (best k/weights per block weight) for KNN-G and KNN-W
        for mid in (MODEL_KNN_G, MODEL_KNN_W):
            sp = tuning_bundle.winner_specs[mid]
            sub_bw = (
                att.loc[(att["modelo_id"] == mid) & (att["metrica"] == sp.metric)]
                .groupby("peso_bloque", as_index=False)["pr_auc_cv_media"]
                .max()
                .sort_values("peso_bloque")
            )
            ax2.plot(
                sub_bw["peso_bloque"],
                sub_bw["pr_auc_cv_media"],
                marker="s",
                color=MODEL_COLORS[mid],
                linewidth=2.0,
                label=f"{mid} ({sp.metric})",
            )
        best_d_pr = float(tuning_bundle.tuning_winners_table.loc[tuning_bundle.tuning_winners_table["modelo_id"] == MODEL_KNN_D, "pr_auc_cv_media"].iloc[0])
        ax2.axhline(best_d_pr, color=MODEL_COLORS[MODEL_KNN_D], linestyle="--", linewidth=1.4, label=f"KNN-D (w=0): {best_d_pr:.4f}")
        ax2.set_xscale("log", base=2)
        ax2.set_xlabel("Peso del bloque ocupacional (w_g / w)", fontsize=9.0)
        ax2.set_ylabel("Mejor PR-AUC CV por peso", fontsize=9.0)
        ax2.set_title("Sensibilidad al peso del bloque ocupacional", fontsize=10.0)
        ax2.legend(fontsize=8.2)
        ax2.grid(alpha=0.25)

        # Panel 3: Score resolution (unique OOF scores vs k for uniform vs distance)
        sr = tuning_bundle.score_resolution_table
        ref_mid = MODEL_KNN_W if (sr["modelo_id"] == MODEL_KNN_W).any() else MODEL_KNN_D
        for wt, color, marker in [("uniform", "#d62728", "o"), ("distance", "#1f77b4", "^")]:
            sub_r = sr.loc[(sr["modelo_id"] == ref_mid) & (sr["pesos"] == wt)].sort_values("k_vecinos")
            if not sub_r.empty:
                ax3.plot(sub_r["k_vecinos"], sub_r["puntajes_unicos_oof"], marker=marker, color=color, linewidth=2.0, label=f"{ref_mid} ({wt})")
        ax3.set_xscale("log")
        ax3.set_yscale("log")
        ax3.set_xlabel("Número de vecinos k (escala log)", fontsize=9.0)
        ax3.set_ylabel("Puntajes distintos en OOF (escala log)", fontsize=9.0)
        ax3.set_title("Resolución del puntaje (1/k en uniforme vs. distancia)", fontsize=10.0)
        ax3.legend(fontsize=8.2)
        ax3.grid(alpha=0.25)

        fig.suptitle("KNN04 · Ajuste honesto en CV agrupada por persona (10 % de personas de Train)", fontsize=12.0, y=1.02)
        return self._save(fig, "knn04_curvas_validacion_k_y_pesos.png")

    def plot_learning_curves(self, tuning_bundle: KNNTuningBundle) -> Path:
        """KNN05: Learning curve stability of top-3 configs across 10%, 25%, 50% of train persons."""
        lc = tuning_bundle.learning_curve_table
        fig, axes = plt.subplots(1, 3, figsize=(16.0, 4.7), sharey=False)
        rank_colors = {1: "#1f77b4", 2: "#ff7f0e", 3: "#2ca02c"}

        for ax, mid in zip(axes, MODEL_ORDER):
            sub_m = lc.loc[lc["modelo_id"] == mid]
            for rnk in sorted(sub_m["rango_en_10pct"].unique()):
                sr = sub_m.loc[sub_m["rango_en_10pct"] == rnk].sort_values("fraccion_personas_pct")
                lbl = f"Top {rnk}: {sr['config_etiqueta'].iloc[0]}"
                xs = sr["fraccion_personas_pct"].to_numpy(dtype=float)
                ys = sr["pr_auc_cv_media"].to_numpy(dtype=float)
                if mid == MODEL_KNN_W and "pr_auc_ic95_inf" in sr.columns and sr["pr_auc_ic95_inf"].notna().all():
                    yerr_lo = np.maximum(0.0, ys - sr["pr_auc_ic95_inf"].to_numpy(dtype=float))
                    yerr_hi = np.maximum(0.0, sr["pr_auc_ic95_sup"].to_numpy(dtype=float) - ys)
                    ax.errorbar(
                        xs,
                        ys,
                        yerr=[yerr_lo, yerr_hi],
                        marker="o",
                        capsize=3,
                        linewidth=1.9,
                        color=rank_colors.get(int(rnk), "#333333"),
                        label=lbl,
                    )
                else:
                    ax.plot(
                        xs,
                        ys,
                        marker="o",
                        linewidth=2.0,
                        color=rank_colors.get(int(rnk), "#333333"),
                        label=lbl,
                    )
            ax.set_title(
                f"{mid} · Estabilidad del top 3"
                + (" (pliegue único + IC 95 %)" if mid == MODEL_KNN_W else " (5-fold CV)"),
                fontsize=9.8,
            )
            ax.set_xlabel("Porcentaje de personas de Train (%)", fontsize=9.0)
            ax.set_ylabel("PR-AUC en validación agrupada", fontsize=9.0)
            ax.legend(fontsize=7.1, loc="lower right")
            ax.grid(alpha=0.25)

        fig.suptitle("KNN05 · Curvas de aprendizaje y estabilidad de hiperparámetros (10 %, 25 % y 50 % de personas)", fontsize=12.0, y=1.02)
        return self._save(fig, "knn05_curva_aprendizaje_estabilidad.png")

    def plot_cost_curves(self, cost_bundle: CostCurveBundle) -> Path:
        """KNN06: Log-log predict time vs n_train with slopes and peak RSS memory."""
        df = cost_bundle.cost_measurements_table
        slp = cost_bundle.loglog_slopes_table.set_index("modelo_id")
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.2, 5.0))

        for mid in MODEL_ORDER:
            sub = df.loc[df["modelo_id"] == mid].sort_values("n_train")
            if sub.empty:
                continue
            b_val = float(slp.loc[mid, "pendiente_log_log_b"]) if mid in slp.index else np.nan
            algo = str(sub["algoritmo"].iloc[0])
            ax1.plot(
                sub["n_train"],
                sub["s_por_1000_filas"],
                marker="o",
                linewidth=2.2,
                color=MODEL_COLORS[mid],
                label=f"{mid} ({algo}, pendiente b={b_val:.2f})",
            )
            ax2.plot(
                sub["n_train"],
                sub["rss_proceso_mb"],
                marker="s",
                linewidth=2.0,
                color=MODEL_COLORS[mid],
                label=f"{mid} (matriz={sub['memoria_matriz_train_mb'].iloc[-1]:.1f} MB)",
            )

        ax1.set_xscale("log")
        ax1.set_yscale("log")
        ax1.set_xlabel("Tamaño del conjunto de entrenamiento N_train (escala log)", fontsize=9.5)
        ax1.set_ylabel("Tiempo de predicción (segundos / 1,000 filas, log)", fontsize=9.5)
        ax1.set_title("Escalado empírico del tiempo de predicción (log-log)", fontsize=10.5)
        ax1.legend(fontsize=8.2)
        ax1.grid(True, which="both", alpha=0.25)

        ax2.set_xlabel("Tamaño del conjunto de entrenamiento N_train", fontsize=9.5)
        ax2.set_ylabel("Memoria residente RSS del proceso (MB)", fontsize=9.5)
        ax2.set_title("Memoria RSS del proceso según N_train", fontsize=10.5)
        ax2.legend(fontsize=8.2)
        ax2.grid(alpha=0.25)

        fig.suptitle("KNN06 · Curvas de costo computacional de KNN (tiempo de consulta y memoria RSS)", fontsize=12.0, y=1.02)
        return self._save(fig, "knn06_curvas_costo_computacional.png")

    def plot_threshold_and_pr_roc(
        self,
        threshold_bundle: KNNThresholdBundle,
        eval_bundle: KNNTestEvaluationBundle,
        y_eval_test: np.ndarray | None = None,
    ) -> Path:
        """KNN07: OOF threshold F1 curve + Test PR and ROC curves against project references."""
        from sklearn.metrics import average_precision_score, precision_recall_curve, roc_auc_score, roc_curve

        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16.5, 4.9))

        for mid, c_df in threshold_bundle.oof_threshold_curves.items():
            tau = threshold_bundle.oof_thresholds_tau[mid]
            ax1.plot(c_df["umbral_tau"], c_df["f1_clase_1"], color=MODEL_COLORS[mid], linewidth=2.0, label=f"{mid} (tau*={tau:.3f})")
            ax1.axvline(tau, color=MODEL_COLORS[mid], linestyle=":", alpha=0.7)
        ax1.axhline(0.4612, color="#666666", linestyle="--", linewidth=1.1, label="Ref 2 todo-positivo (F1=0.4612)")
        ax1.set_xlabel("Umbral de decisión tau (OOF Train)", fontsize=9.0)
        ax1.set_ylabel("F1 de la clase 1 (reincide=1)", fontsize=9.0)
        ax1.set_title("Selección de umbral en OOF (sin tocar Test)", fontsize=10.0)
        ax1.legend(fontsize=7.8)
        ax1.grid(alpha=0.25)

        for mid, cb in eval_bundle.model_curves.items():
            ax2.plot(cb.recall_curve, cb.precision_curve, color=MODEL_COLORS[mid], linewidth=2.0, label=f"{mid} (PR-AUC={cb.pr_auc:.4f})")
            ax3.plot(cb.fpr_curve, cb.tpr_curve, color=MODEL_COLORS[mid], linewidth=2.0, label=f"{mid} (ROC-AUC={cb.roc_auc:.4f})")

        if y_eval_test is not None:
            for base_k, base_lbl, ls in [
                ("NB-H", "NB-H (7.1)", "--"),
                ("LOGIT_6_0", "Logística (6.0)", ":"),
            ]:
                if base_k in eval_bundle.baseline_test_proba:
                    pb = eval_bundle.baseline_test_proba[base_k]
                    pr_b = float(average_precision_score(y_eval_test, pb))
                    roc_b = float(roc_auc_score(y_eval_test, pb))
                    pc, rc, _ = precision_recall_curve(y_eval_test, pb)
                    fc, tc, _ = roc_curve(y_eval_test, pb)
                    sp_p = max(1, len(pc) // 450)
                    sp_r = max(1, len(fc) // 450)
                    ax2.plot(rc[::sp_p], pc[::sp_p], linestyle=ls, color=MODEL_COLORS[base_k], linewidth=1.6, label=f"{base_lbl} ({pr_b:.4f})")
                    ax3.plot(fc[::sp_r], tc[::sp_r], linestyle=ls, color=MODEL_COLORS[base_k], linewidth=1.6, label=f"{base_lbl} ({roc_b:.4f})")

        ax2.axhline(0.2997, color="#666666", linestyle="--", linewidth=1.0, label="Azar / prevalencia Test (0.2997)")
        ax2.set_xlabel("Recall (sensibilidad clase 1)", fontsize=9.0)
        ax2.set_ylabel("Precisión clase 1", fontsize=9.0)
        ax2.set_title("Curvas Precisión-Recall en Test (Versión A)", fontsize=10.0)
        ax2.legend(fontsize=7.6)
        ax2.grid(alpha=0.25)

        ax3.plot([0, 1], [0, 1], color="#666666", linestyle="--", linewidth=1.0, label="Azar (AUC=0.5000)")
        ax3.set_xlabel("Tasa de falsos positivos (FPR)", fontsize=9.0)
        ax3.set_ylabel("Tasa de verdaderos positivos (TPR)", fontsize=9.0)
        ax3.set_title("Curvas ROC en Test (Versión A)", fontsize=10.0)
        ax3.legend(fontsize=7.6)
        ax3.grid(alpha=0.25)

        fig.suptitle("KNN07 · Umbral OOF y evaluación discriminante (PR y ROC) en Test", fontsize=12.0, y=1.02)
        return self._save(fig, "knn07_umbral_oof_y_curvas_pr_roc_test.png")

    def plot_calibration_and_histograms(
        self,
        eval_bundle: KNNTestEvaluationBundle,
        primary_model_id: str,
        y_eval_test: np.ndarray | None = None,
    ) -> Path:
        """KNN08: Reliability diagram for unweighted KNN models (+ NB-H) + score histogram by class."""
        from sklearn.calibration import calibration_curve
        from sklearn.metrics import brier_score_loss

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.2, 5.0))

        ax1.plot([0, 1], [0, 1], color="#444444", linestyle="--", linewidth=1.2, label="Calibración perfecta")
        for mid, cb in eval_bundle.model_curves.items():
            ax1.plot(
                cb.calib_prob_pred,
                cb.calib_prob_true,
                marker="o",
                linewidth=2.0,
                color=MODEL_COLORS[mid],
                label=f"{mid} (Brier={cb.brier:.4f}, ECE={cb.ece:.4f})",
            )
        if y_eval_test is not None and "NB-H" in eval_bundle.baseline_test_proba:
            p_nbh = eval_bundle.baseline_test_proba["NB-H"]
            pt_n, pp_n = calibration_curve(y_eval_test, p_nbh, n_bins=10, strategy="uniform")
            br_n = float(brier_score_loss(y_eval_test, p_nbh))
            ax1.plot(pp_n, pt_n, marker="^", linestyle="--", linewidth=1.6, color=MODEL_COLORS["NB-H"], label=f"NB-H sin ponderar (Brier={br_n:.4f})")
        ax1.set_xlabel("Probabilidad media predicha por decil/bin", fontsize=9.5)
        ax1.set_ylabel("Frecuencia observada de reincidencia", fontsize=9.5)
        ax1.set_title("Diagrama de confiabilidad (modelos sin ponderar)", fontsize=10.5)
        ax1.legend(fontsize=8.2)
        ax1.grid(alpha=0.25)

        cb_p = eval_bundle.model_curves[primary_model_id]
        width = (cb_p.hist_bins[1] - cb_p.hist_bins[0]) if len(cb_p.hist_bins) > 1 else 0.025
        ax2.bar(cb_p.hist_bins, cb_p.hist_density_c0, width=width, alpha=0.45, color="#1f77b4", label="Clase 0 (No reincide)")
        ax2.bar(cb_p.hist_bins, cb_p.hist_density_c1, width=width, alpha=0.45, color="#d62728", label="Clase 1 (Reincide)")
        ax2.set_xlabel(f"Puntaje predicho por {primary_model_id} en Test", fontsize=9.5)
        ax2.set_ylabel("Densidad", fontsize=9.5)
        ax2.set_title(f"Distribución de puntajes por clase ({primary_model_id})", fontsize=10.5)
        ax2.legend(fontsize=8.5)
        ax2.grid(alpha=0.25)

        fig.suptitle("KNN08 · Calibración probabilística y distribución de puntajes en Test (Versión A)", fontsize=12.0, y=1.02)
        return self._save(fig, "knn08_calibracion_y_resolucion_puntajes.png")

    def plot_k1_isco_comparison(self, patterns_bundle: KNNPatternsBundle) -> Path:
        """KNN09: K1 observed rates (train vs test) and PR-AUC by ISCO major group (KNN vs NB-H)."""
        df = patterns_bundle.k1_isco_performance_table.sort_values("tasa_obs_test_pct", ascending=True)
        y_pos = np.arange(len(df))
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.5, 5.8), sharey=True)

        h = 0.36
        ax1.barh(y_pos + h / 2, df["tasa_obs_train_pct"], height=h, color="#7f7f7f", alpha=0.80, label="Tasa observada Train (%)")
        ax1.barh(y_pos - h / 2, df["tasa_obs_test_pct"], height=h, color="#1f77b4", alpha=0.90, label="Tasa observada Test (%)")
        ax1.axvline(29.97, color="#d62728", linestyle="--", linewidth=1.1, label="Media global Test (29.97 %)")
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(df["gran_grupo_isco"].tolist(), fontsize=8.8)
        ax1.set_xlabel("Tasa observada de reincidencia (%)", fontsize=9.5)
        ax1.set_title("Reincidencia observada Train vs. Test por gran grupo ISCO", fontsize=10.5)
        ax1.legend(fontsize=8.2, loc="lower right")
        ax1.grid(axis="x", alpha=0.25)

        ax2.barh(y_pos + h / 2, df["knn_pr_auc_test"], height=h, color=MODEL_COLORS[patterns_bundle.primary_knn_model_id], alpha=0.90, label=f"{patterns_bundle.primary_knn_model_id} (PR-AUC Test)")
        ax2.barh(y_pos - h / 2, df["nb_h_pr_auc_test"], height=h, color=MODEL_COLORS["NB-H"], alpha=0.85, label="NB-H (PR-AUC Test)")
        for i, (_, r) in enumerate(df.iterrows()):
            mx = max(float(r["knn_pr_auc_test"]), float(r["nb_h_pr_auc_test"]))
            ax2.text(mx + 0.008, i, f"Delta={float(r['delta_pr_auc_knn_menos_nbh']):+.3f}", va="center", fontsize=8.0)
        ax2.set_xlim(0.0, float(max(df["knn_pr_auc_test"].max(), df["nb_h_pr_auc_test"].max())) + 0.14)
        ax2.set_xlabel("PR-AUC en Test", fontsize=9.5)
        ax2.set_title(f"K1 · PR-AUC por grupo ISCO: {patterns_bundle.primary_knn_model_id} vs. NB-H", fontsize=10.5)
        ax2.legend(fontsize=8.2, loc="lower right")
        ax2.grid(axis="x", alpha=0.25)

        fig.suptitle("KNN09 · K1 · Reincidencia y desempeño predictivo por gran grupo ocupacional ISCO-08", fontsize=12.0, y=1.02)
        return self._save(fig, "knn09_k1_desempeno_por_grupo_isco.png")

    def plot_k3_deciles_and_isco(self, patterns_bundle: KNNPatternsBundle) -> Path:
        """KNN10: K3 risk deciles lift/gain (KNN vs NB-H) and ISCO composition in D10 vs D01."""
        dec = patterns_bundle.k3_deciles_table.sort_values("decil_orden", ascending=False)
        isco_c = patterns_bundle.k3_isco_composition_table.sort_values("diff_D10_menos_D01_KNN_pp", ascending=True)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.5, 5.4))
        x = np.arange(len(dec))
        w = 0.38
        ax1.bar(x - w / 2, dec["tasa_obs_knn_test_pct"], width=w, color=MODEL_COLORS[patterns_bundle.primary_knn_model_id], alpha=0.90, label=f"{patterns_bundle.primary_knn_model_id} (Test)")
        ax1.bar(x + w / 2, dec["tasa_obs_nb_h_test_pct"], width=w, color=MODEL_COLORS["NB-H"], alpha=0.80, label="NB-H (Test)")
        ax1.axhline(29.97, color="#555555", linestyle="--", linewidth=1.1, label="Prevalencia Test (29.97 %)")
        ax1.set_xticks(x)
        ax1.set_xticklabels([f"D{int(d):02d}" for d in dec["decil_orden"]], fontsize=8.8)
        ax1.set_xlabel("Decil de riesgo (D10 mayor riesgo -> D01 menor riesgo)", fontsize=9.2)
        ax1.set_ylabel("Tasa observada de reincidencia en Test (%)", fontsize=9.2)
        ax1.set_title("K3 · Concentración del riesgo por decil (KNN vs. NB-H)", fontsize=10.5)
        ax1.legend(fontsize=8.2)
        ax1.grid(axis="y", alpha=0.25)

        y2 = np.arange(len(isco_c))
        colors_d = ["#2ca02c" if v > 0 else "#d62728" for v in isco_c["diff_D10_menos_D01_KNN_pp"]]
        ax2.barh(y2, isco_c["diff_D10_menos_D01_KNN_pp"], color=colors_d, alpha=0.85)
        ax2.axvline(0.0, color="#333333", linewidth=1.0)
        ax2.set_yticks(y2)
        ax2.set_yticklabels(isco_c["gran_grupo_isco"].tolist(), fontsize=8.5)
        ax2.set_xlabel("Diferencia de participación D10 menos D01 (puntos porcentuales)", fontsize=9.2)
        ax2.set_title(f"Composición ocupacional en extremos ({patterns_bundle.primary_knn_model_id})", fontsize=10.5)
        ax2.grid(axis="x", alpha=0.25)

        fig.suptitle("KNN10 · K3 · Deciles de riesgo y composición por gran grupo ISCO (Test)", fontsize=12.0, y=1.02)
        return self._save(fig, "knn10_k3_deciles_riesgo_y_composicion_isco.png")

    def plot_k4_agreement(
        self,
        patterns_bundle: KNNPatternsBundle,
        knn_prob: np.ndarray,
        nb_h_prob: np.ndarray,
    ) -> Path:
        """KNN11: K4 hexbin of KNN vs NB-H scores on test and disagreement share by ISCO group."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.0, 5.4))

        hb = ax1.hexbin(nb_h_prob, knn_prob, gridsize=35, cmap="Blues", mincnt=1, bins="log")
        fig.colorbar(hb, ax=ax1, label="log10(conteo de filas Test)")
        ax1.plot([0, 1], [0, 1], color="#d62728", linestyle="--", linewidth=1.2)
        rho = patterns_bundle.k4_agreement_summary["spearman_rho_test"]
        kap = patterns_bundle.k4_agreement_summary["cohen_kappa_igual_alerta"]
        ax1.set_xlabel("Probabilidad predicha por NB-H (Test)", fontsize=9.5)
        ax1.set_ylabel(f"Probabilidad predicha por {patterns_bundle.primary_knn_model_id} (Test)", fontsize=9.5)
        ax1.set_title(f"Dispersión de puntajes (Spearman rho={rho:.4f}, kappa={kap:.4f})", fontsize=10.2)
        ax1.grid(alpha=0.2)

        dis = patterns_bundle.k4_disagreement_by_isco_table.sort_values("desacuerdo_total_pct", ascending=True)
        y2 = np.arange(len(dis))
        ax2.barh(y2, dis["solo_knn_alerta_pct"], color=MODEL_COLORS[patterns_bundle.primary_knn_model_id], alpha=0.88, label=f"Solo {patterns_bundle.primary_knn_model_id} alerta (%)")
        ax2.barh(y2, dis["solo_nb_h_alerta_pct"], left=dis["solo_knn_alerta_pct"], color=MODEL_COLORS["NB-H"], alpha=0.85, label="Solo NB-H alerta (%)")
        ax2.set_yticks(y2)
        ax2.set_yticklabels(dis["gran_grupo_isco"].tolist(), fontsize=8.5)
        ax2.set_xlabel("Porcentaje de desacuerdo a igual tasa de alerta (%)", fontsize=9.5)
        ax2.set_title("Desacuerdo KNN vs. NB-H por gran grupo ISCO", fontsize=10.2)
        ax2.legend(fontsize=8.2, loc="lower right")
        ax2.grid(axis="x", alpha=0.25)

        fig.suptitle("KNN11 · K4 · Concordancia y desacuerdo entre KNN y NB-H en Test", fontsize=12.0, y=1.02)
        return self._save(fig, "knn11_k4_concordancia_knn_vs_nb_h.png")

    def plot_k6_career_and_period(self, patterns_bundle: KNNPatternsBundle) -> Path:
        """KNN12: K6 observed vs predicted rate by job_order and start_year bands."""
        jb = patterns_bundle.k6_job_order_table
        yr = patterns_bundle.k6_start_year_table
        slp = patterns_bundle.k6_slope_summary_table
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.0, 5.0))

        mid = patterns_bundle.primary_knn_model_id
        for ax, df_d, x_col, title_str, slp_idx in [
            (ax1, jb, "tramo_job_order", "Posición en la carrera (job_order)", 0),
            (ax2, yr, "periodo_anio_inicio", "Período calendario (start_year)", 1),
        ]:
            x = np.arange(len(df_d))
            ax.plot(x, df_d["tasa_obs_test_pct"], marker="o", linewidth=2.4, color="#222222", label="Tasa observada Test (%)")
            ax.plot(x, df_d["prob_media_knn_test_pct"], marker="s", linewidth=2.0, color=MODEL_COLORS[mid], label=f"Predicha {mid} (razón pend.={slp.iloc[slp_idx]['razon_pendiente_knn_sobre_obs']:.2f})")
            ax.plot(x, df_d["prob_media_nb_h_test_pct"], marker="^", linestyle="--", linewidth=1.8, color=MODEL_COLORS["NB-H"], label=f"Predicha NB-H (razón pend.={slp.iloc[slp_idx]['razon_pendiente_nb_h_sobre_obs']:.2f})")
            ax.set_xticks(x)
            ax.set_xticklabels(df_d[x_col].tolist(), rotation=20, ha="right", fontsize=8.5)
            ax.set_ylabel("Tasa / probabilidad media en Test (%)", fontsize=9.5)
            ax.set_title(title_str, fontsize=10.5)
            ax.legend(fontsize=8.0)
            ax.grid(alpha=0.25)

        fig.suptitle("KNN12 · K6 · Tasa observada frente a predicha por orden del empleo y año de inicio (Test)", fontsize=12.0, y=1.02)
        return self._save(fig, "knn12_k6_posicion_carrera_y_periodo.png")

    def plot_final_frontier(self, eval_bundle: KNNTestEvaluationBundle) -> Path:
        """KNN13: Final like-for-like PR-AUC comparison and performance vs inference-cost frontier."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.2, 5.2))

        # Panel 1: Like-for-like PR-AUC bars grouped into Dense-only vs With-occupation
        d_df = eval_bundle.like_for_like_dense_table.copy()
        d_df["grupo"] = "Solo denso"
        o_df = eval_bundle.like_for_like_occ_table.copy()
        o_df["grupo"] = "Con ocupación"
        comb = pd.concat([d_df, o_df], ignore_index=True)

        y_pos = np.arange(len(comb))
        colors = ["#1f77b4" if g == "Solo denso" else "#2ca02c" for g in comb["grupo"]]
        ax1.barh(y_pos, comb["pr_auc_test"].to_numpy(dtype=float), color=colors, alpha=0.88)
        for i, (_, r) in enumerate(comb.iterrows()):
            ax1.text(float(r["pr_auc_test"]) + 0.004, i, f"{float(r['pr_auc_test']):.4f}", va="center", fontsize=8.3)
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(comb["modelo"].tolist(), fontsize=8.4)
        ax1.invert_yaxis()
        ax1.axvline(0.2997, color="#777777", linestyle="--", linewidth=1.1, label="Azar Test (0.2997)")
        ax1.set_xlim(0.25, float(comb["pr_auc_test"].max()) + 0.06)
        ax1.set_xlabel("PR-AUC en Test (Versión A)", fontsize=9.5)
        ax1.set_title("Comparación homogénea (azul=solo denso, verde=con ocupación)", fontsize=10.2)
        ax1.grid(axis="x", alpha=0.25)

        # Panel 2: Performance (PR-AUC) vs log10 inference cost (s per 1,000 rows)
        cost_df = eval_bundle.cost_comparison_table.copy()
        pr_lookup: Dict[str, float] = {}
        for _, r in eval_bundle.equal_alert_rate_table.iterrows():
            pr_lookup[str(r["modelo"])] = float(r["pr_auc_test"])

        for _, r in cost_df.iterrows():
            m_lbl = str(r["modelo"])
            pr_v = np.nan
            for k, v in pr_lookup.items():
                if k in m_lbl:
                    pr_v = v
                    break
            if np.isnan(pr_v):
                continue
            cost_1k = max(float(r["tiempo_predict_por_1000_filas_s"]), 1e-5)
            fam = str(r["familia"])
            c = "#d62728" if "KNN" in fam else ("#9467bd" if "Naive" in fam else "#1f77b4")
            mk = "D" if "KNN" in fam else ("o" if "Naive" in fam else "s")
            ax2.scatter(cost_1k, pr_v, s=95, color=c, marker=mk, zorder=4)
            short = m_lbl.split(" · ")[0]
            ax2.annotate(short, (cost_1k, pr_v), xytext=(6, 4), textcoords="offset points", fontsize=8.2)

        ax2.set_xscale("log")
        ax2.set_xlabel("Costo de predicción (segundos por 1,000 filas, escala log)", fontsize=9.5)
        ax2.set_ylabel("PR-AUC en Test (Versión A)", fontsize=9.5)
        ax2.set_title("Frontera desempeño vs. costo de inferencia", fontsize=10.2)
        ax2.grid(True, which="both", alpha=0.25)

        fig.suptitle("KNN13 · Comparación final homogénea y frontera desempeño-costo (JobPath)", fontsize=12.0, y=1.02)
        return self._save(fig, "knn13_frontera_desempeno_vs_costo.png")

    def plot_knn_w_block_times(
        self,
        block_times_df: pd.DataFrame,
        unthrottled_bench_5k_s: float,
    ) -> Path:
        """KNN14: Per-block execution time across the 70 KNN-W cached blocks showing thermal throttling."""
        fig, ax = plt.subplots(figsize=(13.5, 4.8))
        x = block_times_df["bloque_idx"].to_numpy(dtype=int)
        y = block_times_df["tiempo_bloque_s"].to_numpy(dtype=float)
        seq_mask = x <= 56
        par_mask = x >= 57

        ax.bar(x[seq_mask], y[seq_mask], color="#1f77b4", alpha=0.85, label="Bloques 0–56 (ejecución secuencial)")
        ax.bar(x[par_mask], y[par_mask], color="#ff7f0e", alpha=0.85, label="Bloques 57–69 (paralelo multi-proceso)")

        med_s = float(np.median(y))
        ax.axhline(unthrottled_bench_5k_s, color="#2ca02c", linestyle="--", linewidth=1.8, label=f"Benchmark sin estrangulación ({unthrottled_bench_5k_s:.1f} s / 5k)")
        ax.axhline(med_s, color="#d62728", linestyle=":", linewidth=1.8, label=f"Mediana observada por bloque ({med_s:.1f} s)")

        max_i = int(np.argmax(y))
        ax.annotate(
            f"Pico térmico\nbloque {x[max_i]}: {y[max_i]:.0f} s",
            xy=(x[max_i], y[max_i]),
            xytext=(max(x[max_i] - 12, 2), y[max_i] * 0.86),
            arrowprops={"arrowstyle": "->", "color": "#333333", "lw": 1.1},
            fontsize=8.5,
        )

        ax.set_xlabel("Índice del bloque de 5,000 filas de test (bloque 69 = 2,720 filas)", fontsize=9.5)
        ax.set_ylabel("Tiempo registrado por bloque (segundos)", fontsize=9.5)
        ax.set_title("KNN14 · Tiempo por bloque en los 70 bloques de KNN-W (patrón de estrangulación térmica)", fontsize=11.5, pad=10)
        ax.legend(loc="upper left", fontsize=8.5)
        ax.grid(axis="y", alpha=0.25)
        return self._save(fig, "knn14_tiempos_por_bloque_knn_w.png")
