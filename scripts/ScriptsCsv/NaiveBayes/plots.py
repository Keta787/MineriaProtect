"""Spanish-labeled figure generation for Notebook 7.1 (Naive Bayes), strictly without emojis."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import (
    MODEL_LABELS_ES,
    MODEL_NB_B,
    MODEL_NB_G,
    MODEL_NB_G_STAR,
    MODEL_NB_H,
    MODEL_ORDER,
    NaiveBayesConfig,
)
from .evaluation import ModelCurveBundle, NaiveBayesEvaluationBundle
from .occupation_analysis import OccupationAnalysisBundle
from .outlier_diagnostics import OutlierDiagnosticsBundle
from .patterns import GeneralPatternsBundle, WaterfallProfileDecomposition
from .version_comparison import VersionComparisonBundle


MODEL_COLORS: Dict[str, str] = {
    MODEL_NB_G: "#1f77b4",
    MODEL_NB_B: "#ff7f0e",
    MODEL_NB_H: "#2ca02c",
}


class NaiveBayesPlotter:
    """Render and persist all Notebook 7.1 figures in Spanish without decorative symbols."""

    def __init__(self, config: NaiveBayesConfig) -> None:
        self.config = config
        self.config.figures_dir.mkdir(parents=True, exist_ok=True)

    def _save(self, fig: plt.Figure, filename: str) -> Path:
        out_path = self.config.figures_dir / filename
        fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return out_path

    def plot_dense_correlations(self, corr_df: pd.DataFrame) -> Path:
        """NB01: Heatmap of Pearson correlations across the 14 dense features in Train (Version A)."""
        fig, ax = plt.subplots(figsize=(10.5, 8.2))
        mat = corr_df.to_numpy(dtype=float)
        cols = list(corr_df.columns)
        im = ax.imshow(mat, cmap="coolwarm", vmin=-1.0, vmax=1.0, aspect="auto")

        ax.set_xticks(np.arange(len(cols)))
        ax.set_yticks(np.arange(len(cols)))
        ax.set_xticklabels(cols, rotation=45, ha="right", fontsize=8.5)
        ax.set_yticklabels(cols, fontsize=8.5)

        for i in range(len(cols)):
            for j in range(len(cols)):
                val = mat[i, j]
                if abs(val) >= 0.25 or i == j:
                    color = "white" if abs(val) > 0.60 else "black"
                    ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=7.5, color=color)

        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label("Coeficiente de correlación de Pearson (Train · Versión A)", fontsize=9.0)
        ax.set_title(
            "NB01 · Matriz de correlación de las 14 variables densas legítimas y riesgo de doble conteo (Train A)",
            fontsize=11.0,
            pad=12,
        )
        return self._save(fig, "nb01_correlaciones_bloque_denso.png")

    def plot_gaussian_outlier_diagnostics(self, diag_bundle: OutlierDiagnosticsBundle) -> Path:
        """NB02: Histograms by class with fitted Gaussian curves and Tukey fences overlaid."""
        curves = diag_bundle.histogram_curves
        n_plots = len(curves)
        n_cols = 3
        n_rows = int(np.ceil(n_plots / float(n_cols)))
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(14.5, 4.2 * n_rows))
        axes_flat = np.atleast_1d(axes).ravel()

        for idx, cdata in enumerate(curves):
            ax = axes_flat[idx]
            width = (cdata.bin_centers[1] - cdata.bin_centers[0]) if len(cdata.bin_centers) > 1 else 0.1
            ax.bar(
                cdata.bin_centers,
                cdata.hist_density_c0,
                width=width,
                alpha=0.35,
                color="#1f77b4",
                label="Empírico y=0 (No reincide)",
            )
            ax.bar(
                cdata.bin_centers,
                cdata.hist_density_c1,
                width=width,
                alpha=0.35,
                color="#d62728",
                label="Empírico y=1 (Reincide)",
            )
            ax.plot(
                cdata.x_grid,
                cdata.gauss_pdf_c0,
                color="#0b4f8a",
                linewidth=1.8,
                label=f"Gaussiana y=0 (media={cdata.theta_c0:.2f}, DE={cdata.std_c0:.2f})",
            )
            ax.plot(
                cdata.x_grid,
                cdata.gauss_pdf_c1,
                color="#8c1515",
                linewidth=1.8,
                label=f"Gaussiana y=1 (media={cdata.theta_c1:.2f}, DE={cdata.std_c1:.2f})",
            )
            ax.axvline(cdata.tukey_low, color="#333333", linestyle="--", linewidth=1.0)
            ax.axvline(
                cdata.tukey_high,
                color="#333333",
                linestyle="--",
                linewidth=1.0,
                label=f"Vallas Tukey ({cdata.pct_outside_tukey:.1f}% fuera)",
            )
            ax.set_title(f"{cdata.feature_rob}\n({cdata.label_es})", fontsize=9.5)
            ax.set_xlabel("Valor escalado robusto en Train", fontsize=8.5)
            ax.set_ylabel("Densidad", fontsize=8.5)
            ax.legend(loc="upper right", fontsize=7.0)
            ax.grid(alpha=0.25)

        for idx in range(n_plots, len(axes_flat)):
            axes_flat[idx].axis("off")

        fig.suptitle(
            "NB02 · Diagnóstico del supuesto Gaussiano por clase y vallas de Tukey en Train (Versión A)",
            fontsize=12.0,
            y=1.02,
        )
        return self._save(fig, "nb02_diagnostico_gaussiano_outliers.png")

    def plot_tuning_validation_curves(self, attempts_df: pd.DataFrame) -> Path:
        """NB03: Grouped-CV validation curves over var_smoothing and alpha for NB-G, NB-B, and NB-H."""
        fig, (ax_g, ax_b, ax_h) = plt.subplots(1, 3, figsize=(15.5, 4.6))

        # Panel 1: NB-G and NB-G* over extended var_smoothing
        sub_g = attempts_df.loc[
            (attempts_df["modelo_id"] == MODEL_NB_G) & (attempts_df["prior_mode"] == "empirical")
        ].sort_values("var_smoothing")
        ax_g.plot(
            np.log10(sub_g["var_smoothing"].to_numpy(dtype=float)),
            sub_g["pr_auc_cv_media"].to_numpy(dtype=float),
            marker="o",
            color=MODEL_COLORS[MODEL_NB_G],
            linewidth=2.0,
            label="NB-G PR-AUC (14 cols)",
        )
        sub_gs = attempts_df.loc[
            (attempts_df["modelo_id"] == MODEL_NB_G_STAR) & (attempts_df["prior_mode"] == "empirical")
        ].sort_values("var_smoothing")
        if not sub_gs.empty:
            ax_g.plot(
                np.log10(sub_gs["var_smoothing"].to_numpy(dtype=float)),
                sub_gs["pr_auc_cv_media"].to_numpy(dtype=float),
                marker="^",
                linestyle=":",
                color="#17becf",
                linewidth=1.8,
                label="NB-G* PR-AUC (sin <1 %)",
            )
        ax_g.plot(
            np.log10(sub_g["var_smoothing"].to_numpy(dtype=float)),
            sub_g["roc_auc_cv_media"].to_numpy(dtype=float),
            marker="s",
            linestyle="--",
            color="#555555",
            linewidth=1.5,
            label="NB-G ROC-AUC (CV 5-fold)",
        )
        ax_g.set_xlabel("log10(var_smoothing)")
        ax_g.set_ylabel("Puntaje medio en CV agrupado")
        ax_g.set_title("NB-G y NB-G* · Curva de validación (rejilla extendida)")
        ax_g.legend(loc="best", fontsize=7.5)
        ax_g.grid(alpha=0.25)

        # Panel 2: NB-B over alpha
        sub_b = attempts_df.loc[
            (attempts_df["modelo_id"] == MODEL_NB_B) & (attempts_df["prior_mode"] == "empirical")
        ].sort_values("alpha")
        ax_b.plot(
            sub_b["alpha"].to_numpy(dtype=float),
            sub_b["pr_auc_cv_media"].to_numpy(dtype=float),
            marker="o",
            color=MODEL_COLORS[MODEL_NB_B],
            linewidth=2.0,
            label="PR-AUC (CV 5-fold)",
        )
        ax_b.plot(
            sub_b["alpha"].to_numpy(dtype=float),
            sub_b["roc_auc_cv_media"].to_numpy(dtype=float),
            marker="s",
            linestyle="--",
            color="#555555",
            linewidth=1.5,
            label="ROC-AUC (CV 5-fold)",
        )
        ax_b.set_xscale("log")
        ax_b.set_xlabel("Suavizado de Laplace (alpha, escala log)")
        ax_b.set_ylabel("Puntaje medio en CV agrupado")
        ax_b.set_title("NB-B · Curva de validación (alpha)")
        ax_b.legend(loc="best", fontsize=8.0)
        ax_b.grid(alpha=0.25)

        # Panel 3: NB-H PR-AUC across alpha for selected var_smoothing levels
        sub_h = attempts_df.loc[
            (attempts_df["modelo_id"] == MODEL_NB_H) & (attempts_df["prior_mode"] == "empirical")
        ]
        vs_levels = sorted(sub_h["var_smoothing"].unique())
        selected_vs = [vs_levels[0], vs_levels[len(vs_levels) // 2], vs_levels[-2], vs_levels[-1]]
        for vs_val in sorted(set(selected_vs)):
            s_vs = sub_h.loc[sub_h["var_smoothing"] == vs_val].sort_values("alpha")
            ax_h.plot(
                s_vs["alpha"].to_numpy(dtype=float),
                s_vs["pr_auc_cv_media"].to_numpy(dtype=float),
                marker="o",
                linewidth=1.7,
                label=f"var_smoothing={vs_val:.0e}",
            )
        ax_h.set_xscale("log")
        ax_h.set_xlabel("Suavizado de Laplace (alpha, escala log)")
        ax_h.set_ylabel("PR-AUC medio en CV agrupado")
        ax_h.set_title("NB-H · Interacción (alpha x var_smoothing)")
        ax_h.legend(loc="best", fontsize=8.0)
        ax_h.grid(alpha=0.25)

        fig.suptitle(
            "NB03 · Búsqueda honesta de hiperparámetros en StratifiedGroupKFold (5 pliegues por resume_id · Train A)",
            fontsize=11.5,
            y=1.03,
        )
        return self._save(fig, "nb03_curvas_validacion_tuning_cv.png")

    def plot_oof_threshold_selection(self, eval_bundle: NaiveBayesEvaluationBundle) -> Path:
        """NB04: Out-of-fold threshold curves (F1, Precision, Recall vs tau) on Train."""
        fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.5), sharey=True)
        for idx, model_id in enumerate(MODEL_ORDER):
            ax = axes[idx]
            art = eval_bundle.tuned_models[model_id]
            cdf = eval_bundle.oof_threshold_curves[model_id]
            tau_star = art.oof_threshold_tau

            ax.plot(
                cdf["umbral_tau"],
                cdf["f1_clase_1"],
                color=MODEL_COLORS[model_id],
                linewidth=2.2,
                label="F1 clase 1 (OOF)",
            )
            ax.plot(
                cdf["umbral_tau"],
                cdf["precision_clase_1"],
                color="#555555",
                linestyle="--",
                linewidth=1.4,
                label="Precisión clase 1",
            )
            ax.plot(
                cdf["umbral_tau"],
                cdf["recall_clase_1"],
                color="#8c564b",
                linestyle=":",
                linewidth=1.5,
                label="Recall clase 1",
            )
            ax.axvline(0.50, color="gray", linestyle="--", linewidth=1.1, label="Umbral 0.50")
            ax.axvline(
                tau_star,
                color="#d62728",
                linestyle="-",
                linewidth=1.5,
                label=f"Óptimo OOF tau*={tau_star:.3f}",
            )
            ax.set_title(f"{model_id} (tau* = {tau_star:.3f})", fontsize=10.0)
            ax.set_xlabel("Umbral de decisión (tau)")
            if idx == 0:
                ax.set_ylabel("Valor de la métrica en OOF Train")
            ax.set_xlim(0.0, 1.0)
            ax.set_ylim(0.0, 1.02)
            ax.legend(loc="lower center", fontsize=7.5)
            ax.grid(alpha=0.25)

        fig.suptitle(
            "NB04 · Selección honesta del umbral de decisión (tau*) sobre predicciones Out-Of-Fold en Train (Versión A)",
            fontsize=11.5,
            y=1.03,
        )
        return self._save(fig, "nb04_umbral_oof_f1.png")

    def plot_pr_and_roc_test_curves(self, eval_bundle: NaiveBayesEvaluationBundle) -> Path:
        """NB05: Precision-Recall and ROC curves on Test (Version A) with References 1, 2, and 3."""
        fig, (ax_pr, ax_roc) = plt.subplots(1, 2, figsize=(13.5, 5.2))

        for model_id in MODEL_ORDER:
            cb = eval_bundle.model_curves[model_id]
            ax_pr.plot(
                cb.recall_curve,
                cb.precision_curve,
                color=MODEL_COLORS[model_id],
                linewidth=2.0,
                label=f"{model_id} (PR-AUC = {cb.pr_auc:.4f})",
            )
            ax_roc.plot(
                cb.fpr_curve,
                cb.tpr_curve,
                color=MODEL_COLORS[model_id],
                linewidth=2.0,
                label=f"{model_id} (ROC-AUC = {cb.roc_auc:.4f})",
            )

        # Reference lines
        ax_pr.axhline(
            0.2997,
            color="#7f7f7f",
            linestyle="--",
            linewidth=1.2,
            label="Ref 1/2 · Azar / Prevalencia Test (0.2997)",
        )
        ax_pr.scatter(
            [0.6147],
            [0.4691],
            color="#9467bd",
            s=65,
            zorder=5,
            label="Ref 3 · Techo 6.0 Logística OHE (F1=0.5321, PR-AUC=0.5109)",
        )
        ax_pr.set_xlabel("Exhaustividad (Recall · clase positiva)")
        ax_pr.set_ylabel("Precisión (Precision · clase positiva)")
        ax_pr.set_title("Curva Precision-Recall en Test (347,720 filas)")
        ax_pr.set_xlim(0.0, 1.0)
        ax_pr.set_ylim(0.0, 1.02)
        ax_pr.legend(loc="upper right", fontsize=8.0)
        ax_pr.grid(alpha=0.25)

        ax_roc.plot(
            [0.0, 1.0],
            [0.0, 1.0],
            color="#7f7f7f",
            linestyle="--",
            linewidth=1.2,
            label="Ref 1/2 · Azar (ROC-AUC = 0.5000)",
        )
        ax_roc.axhline(
            0.7133,
            color="#9467bd",
            linestyle=":",
            linewidth=1.3,
            label="Ref 3 · Techo ROC-AUC 6.0 (0.7133)",
        )
        ax_roc.set_xlabel("Tasa de Falsos Positivos (FPR)")
        ax_roc.set_ylabel("Tasa de Verdaderos Positivos (TPR / Recall)")
        ax_roc.set_title("Curva ROC en Test (347,720 filas)")
        ax_roc.set_xlim(0.0, 1.0)
        ax_roc.set_ylim(0.0, 1.02)
        ax_roc.legend(loc="lower right", fontsize=8.0)
        ax_roc.grid(alpha=0.25)

        fig.suptitle(
            "NB05 · Evaluación final en Test (Versión A · 70,419 personas) frente a las Tres Referencias del Proyecto",
            fontsize=11.5,
            y=1.02,
        )
        return self._save(fig, "nb05_curvas_pr_roc_test.png")

    def plot_calibration_and_histograms(self, eval_bundle: NaiveBayesEvaluationBundle) -> Path:
        """NB06: Reliability diagram and predicted probability distribution by class on Test."""
        fig, axes = plt.subplots(1, 4, figsize=(17.0, 4.3))
        ax_cal = axes[0]
        ax_cal.plot([0.0, 1.0], [0.0, 1.0], color="black", linestyle="--", linewidth=1.1, label="Calibración perfecta")

        for idx, model_id in enumerate(MODEL_ORDER):
            cb = eval_bundle.model_curves[model_id]
            ax_cal.plot(
                cb.calib_prob_pred,
                cb.calib_prob_true,
                marker="o",
                color=MODEL_COLORS[model_id],
                linewidth=1.8,
                label=f"{model_id} (Brier={cb.brier:.3f}, ECE={cb.ece:.3f})",
            )

            ax_h = axes[idx + 1]
            width = cb.hist_bins[1] - cb.hist_bins[0]
            ax_h.bar(
                cb.hist_bins,
                cb.hist_density_c0,
                width=width,
                alpha=0.45,
                color="#1f77b4",
                label="Clase real 0 (No reincide)",
            )
            ax_h.bar(
                cb.hist_bins,
                cb.hist_density_c1,
                width=width,
                alpha=0.45,
                color="#d62728",
                label="Clase real 1 (Reincide)",
            )
            ax_h.set_title(f"Distribución de P(y=1|x) · {model_id}", fontsize=9.5)
            ax_h.set_xlabel("Probabilidad predicha P(y=1|x)")
            ax_h.set_ylabel("Densidad")
            ax_h.legend(loc="upper right", fontsize=7.5)
            ax_h.grid(alpha=0.25)

        ax_cal.set_title("Curva de confiabilidad (Test A)", fontsize=9.5)
        ax_cal.set_xlabel("Probabilidad media predicha")
        ax_cal.set_ylabel("Fracción empírica de positivos")
        ax_cal.set_xlim(0.0, 1.0)
        ax_cal.set_ylim(0.0, 1.02)
        ax_cal.legend(loc="upper left", fontsize=7.5)
        ax_cal.grid(alpha=0.25)

        fig.suptitle(
            "NB06 · Calibración probabilística vs. poder de ordenamiento (Ranking) en Test (Versión A)",
            fontsize=11.5,
            y=1.03,
        )
        return self._save(fig, "nb06_calibracion_y_distribucion_prob.png")

    def plot_o1_and_o2_isco_overview(self, occ_bundle: OccupationAnalysisBundle) -> Path:
        """NB07: O1 observed/predicted reincidence rates with 95% CI and O2 PR-AUC by ISCO major group."""
        o1 = occ_bundle.o1_rates_table.sort_values("tasa_observada_train_pct", ascending=True)
        o2 = occ_bundle.o2_performance_by_isco_table

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.0, 5.6), sharey=True)
        y_pos = np.arange(len(o1))
        labels = o1["gran_grupo_isco"].tolist()
        major_order = o1["isco_major"].tolist()

        obs_tr = o1["tasa_observada_train_pct"].to_numpy(dtype=float)
        obs_te = o1["tasa_confirmada_test_pct"].to_numpy(dtype=float)
        pred_tr = o1["prob_media_oof_nb_h_train_pct"].to_numpy(dtype=float)
        err_low = obs_tr - o1["ic95_inf_train_pct"].to_numpy(dtype=float)
        err_high = o1["ic95_sup_train_pct"].to_numpy(dtype=float) - obs_tr

        ax1.barh(
            y_pos - 0.18,
            obs_tr,
            xerr=[err_low, err_high],
            height=0.34,
            color="#1f77b4",
            alpha=0.88,
            label="Observada Train (con IC 95% Wilson)",
        )
        ax1.barh(
            y_pos + 0.18,
            obs_te,
            height=0.34,
            color="#2ca02c",
            alpha=0.82,
            label="Confirmada Test",
        )
        ax1.scatter(
            pred_tr,
            y_pos - 0.18,
            color="#d62728",
            zorder=5,
            s=40,
            label="Media predicha NB-H (OOF Train)",
        )
        ax1.axvline(30.01, color="gray", linestyle="--", linewidth=1.1, label="Media global Train (30.01%)")
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(labels, fontsize=8.5)
        ax1.set_xlabel("Tasa de reincidencia (%)")
        ax1.set_title("O1 · Tasa de reincidencia por gran grupo ISCO (Train vs. Test)")
        ax1.legend(loc="lower right", fontsize=8.0)
        ax1.grid(axis="x", alpha=0.25)

        width = 0.25
        for idx, model_id in enumerate(MODEL_ORDER):
            sub_m = (
                o2.loc[o2["modelo_id"] == model_id]
                .set_index("isco_major")
                .reindex(major_order)
            )
            vals = sub_m["pr_auc_test"].to_numpy(dtype=float)
            ax2.barh(
                y_pos + (idx - 1) * width,
                vals,
                height=width,
                color=MODEL_COLORS[model_id],
                alpha=0.88,
                label=f"{model_id} (PR-AUC Test)",
            )
        ax2.axvline(0.2997, color="gray", linestyle="--", linewidth=1.1, label="Prevalencia global Test (0.2997)")
        ax2.set_xlabel("PR-AUC fuera de muestra en Test")
        ax2.set_title("O2 · Desempeño discriminante (PR-AUC en Test) por gran grupo ISCO")
        ax2.legend(loc="lower right", fontsize=8.0)
        ax2.grid(axis="x", alpha=0.25)

        fig.suptitle(
            "NB07 · Análisis Ocupacional O1 y O2: Tasas observadas y desempeño por Gran Grupo ISCO-08 (Versión A)",
            fontsize=11.5,
            y=1.02,
        )
        return self._save(fig, "nb07_o1_o2_reincidencia_y_desempeno_isco.png")

    def plot_o3_isco_heatmap(self, occ_bundle: OccupationAnalysisBundle) -> Path:
        """NB08: O3 group-by-variable heatmap of mean log-odds contribution differences."""
        hdf = occ_bundle.o3_log_odds_heatmap_df
        row_labels = hdf["gran_grupo_isco"].tolist()
        feature_cols = [
            c
            for c in hdf.columns
            if c not in ("isco_major", "gran_grupo_isco", "soporte_train")
        ]
        mat = hdf[feature_cols].to_numpy(dtype=float)

        fig, ax = plt.subplots(figsize=(13.0, 6.2))
        vmax = max(0.35, float(np.max(np.abs(mat))))
        im = ax.imshow(mat, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")

        ax.set_yticks(np.arange(len(row_labels)))
        ax.set_yticklabels(row_labels, fontsize=8.5)
        ax.set_xticks(np.arange(len(feature_cols)))
        ax.set_xticklabels(feature_cols, rotation=38, ha="right", fontsize=8.5)

        for i in range(len(row_labels)):
            for j in range(len(feature_cols)):
                val = mat[i, j]
                color = "white" if abs(val) > 0.55 * vmax else "black"
                ax.text(j, i, f"{val:+.2f}", ha="center", va="center", fontsize=7.5, color=color)

        cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.03)
        cbar.set_label("Diferencia media de contribución al log-odds (Reincide=1 menos Reincide=0)", fontsize=8.5)
        ax.set_title(
            "NB08 · Análisis O3: ¿Qué distingue a quienes reinciden dentro de cada gran grupo ISCO? (Cambio en log-odds · Train A)",
            fontsize=11.0,
            pad=12,
        )
        return self._save(fig, "nb08_o3_heatmap_contribuciones_isco.png")

    def plot_o6_persistence_scatter(self, occ_bundle: OccupationAnalysisBundle) -> Path:
        """NB09: O6 scatter plot of ISCO major group transition persistence vs. mean predicted probability."""
        df = occ_bundle.o6_transitions_persistence_table
        corr = occ_bundle.o6_correlations_summary

        fig, ax = plt.subplots(figsize=(9.5, 5.8))
        x = df["persistencia_mismo_gran_grupo_1d_train_pct"].to_numpy(dtype=float)
        y = df["prob_media_predicha_nb_h_train_pct"].to_numpy(dtype=float)
        sizes = np.clip(df["n_transiciones_origen_train"].to_numpy(dtype=float) / 600.0, 45.0, 380.0)

        ax.scatter(x, y, s=sizes, color="#1f77b4", alpha=0.80, edgecolors="black", linewidth=1.0)
        for _, r in df.iterrows():
            ax.annotate(
                str(r["gran_grupo_isco"]),
                (
                    float(r["persistencia_mismo_gran_grupo_1d_train_pct"]),
                    float(r["prob_media_predicha_nb_h_train_pct"]),
                ),
                textcoords="offset points",
                xytext=(6, 4),
                fontsize=8.0,
            )

        if len(x) >= 2:
            coef = np.polyfit(x, y, 1)
            x_line = np.linspace(float(x.min()) - 1.5, float(x.max()) + 1.5, 50)
            ax.plot(
                x_line,
                coef[0] * x_line + coef[1],
                color="#d62728",
                linestyle="--",
                linewidth=1.4,
                label=(
                    f"Ajuste lineal (n=10 grupos): r={corr['pearson_r_persistencia_1d_vs_prob']:.3f}, "
                    f"rho={corr['spearman_rho_persistencia_1d_vs_prob']:.3f}"
                ),
            )

        ax.set_xlabel("Persistencia en el mismo gran grupo ISCO en el siguiente empleo clasificado (%)")
        ax.set_ylabel("Probabilidad media predicha de reincidencia por NB-H (%)")
        ax.set_title(
            "NB09 · Análisis O6: Persistencia de transición inter-empleo vs. probabilidad predicha por gran grupo ISCO (Train A)",
            fontsize=10.5,
        )
        ax.legend(loc="best", fontsize=8.5)
        ax.grid(alpha=0.25)
        return self._save(fig, "nb09_o6_persistencia_vs_probabilidad_isco.png")

    def plot_p1_llr_curves(self, pat_bundle: GeneralPatternsBundle) -> Path:
        """NB10: P1 log-likelihood ratio curves across original-unit ranges."""
        curves = pat_bundle.p1_llr_curves
        cols = [
            c
            for c in (
                "job_order_rob",
                "dur_q_rob",
                "start_ord_rob",
                "end_ord_rob",
                "n_skills_essential_rob",
                "univ_ord_mm",
            )
            if c in curves
        ]
        fig, axes = plt.subplots(2, 3, figsize=(14.5, 7.8))
        axes_flat = axes.ravel()

        for idx, col in enumerate(cols):
            ax = axes_flat[idx]
            cdf = curves[col]
            x_orig = cdf["valor_original"].to_numpy(dtype=float)
            llr = cdf["log_likelihood_ratio"].to_numpy(dtype=float)

            ax.plot(x_orig, llr, color="#1f77b4", linewidth=2.0)
            ax.axhline(0.0, color="black", linestyle="--", linewidth=1.0)
            ax.fill_between(
                x_orig,
                0.0,
                llr,
                where=(llr >= 0.0),
                color="#2ca02c",
                alpha=0.25,
                label="Empuja a reincide=1 (LLR > 0)",
            )
            ax.fill_between(
                x_orig,
                0.0,
                llr,
                where=(llr < 0.0),
                color="#d62728",
                alpha=0.25,
                label="Empuja a no reincide=0 (LLR < 0)",
            )
            ax.set_title(f"{col}", fontsize=9.5)
            ax.set_xlabel("Valor en unidades originales (P2 a P98)")
            ax.set_ylabel("Log-Likelihood Ratio log P(x|1)/P(x|0)")
            ax.legend(loc="best", fontsize=7.2)
            ax.grid(alpha=0.25)

        for idx in range(len(cols), len(axes_flat)):
            axes_flat[idx].axis("off")

        fig.suptitle(
            "NB10 · Análisis P1: Evidencia univariada (Log-Likelihood Ratio) en unidades originales (Train A)",
            fontsize=11.5,
            y=1.02,
        )
        return self._save(fig, "nb10_p1_evidencia_log_likelihood_ratio.png")

    def plot_p2_waterfalls(self, waterfalls: List[WaterfallProfileDecomposition]) -> Path:
        """NB11: P2 6-panel waterfall chart of additive log-odds decomposition per profile."""
        fig, axes = plt.subplots(2, 3, figsize=(16.5, 9.2))
        axes_flat = axes.ravel()

        for idx, wf in enumerate(waterfalls[:6]):
            ax = axes_flat[idx]
            df_w = wf.contributions_df
            steps = df_w["paso"].tolist()
            contribs = df_w["contribucion_log_odds"].to_numpy(dtype=float)
            cum_lo = df_w["log_odds_acumulado"].to_numpy(dtype=float)
            prev_lo = np.r_[0.0, cum_lo[:-1]]

            y_pos = np.arange(len(steps))
            colors = [
                "#7f7f7f" if i == 0 else ("#2ca02c" if v >= 0 else "#d62728")
                for i, v in enumerate(contribs)
            ]

            for i in range(len(steps)):
                start_x = 0.0 if i == 0 else prev_lo[i]
                ax.barh(
                    y_pos[i],
                    contribs[i],
                    left=start_x,
                    color=colors[i],
                    alpha=0.88,
                    height=0.62,
                )
                ax.text(
                    cum_lo[i] + (0.04 if contribs[i] >= 0 else -0.04),
                    y_pos[i],
                    f"{contribs[i]:+.2f}",
                    va="center",
                    ha="left" if contribs[i] >= 0 else "right",
                    fontsize=7.5,
                )

            ax.axvline(0.0, color="black", linestyle=":", linewidth=0.9)
            ax.axvline(
                wf.final_log_odds,
                color="#1f77b4",
                linestyle="--",
                linewidth=1.3,
                label=f"Log-odds final={wf.final_log_odds:+.2f} (P={100.0 * wf.predicted_proba:.1f}%)",
            )
            ax.set_yticks(y_pos)
            ax.set_yticklabels(steps if idx % 3 == 0 else [f"P.{i}" for i in range(len(steps))], fontsize=8.0)
            ax.invert_yaxis()
            ax.set_xlabel("Log-odds acumulado")
            ax.set_title(
                f"{wf.profile_title_es[:48]}\n(P(reincide=1) = {100.0 * wf.predicted_proba:.1f}% · y_real={wf.summary_original_units['y_real']})",
                fontsize=8.8,
            )
            ax.legend(loc="lower right", fontsize=7.2)
            ax.grid(axis="x", alpha=0.25)

        fig.suptitle(
            "NB11 · Análisis P2: Descomposición aditiva del log-odds (Waterfall) para 6 perfiles prototípicos de Train A",
            fontsize=11.5,
            y=1.02,
        )
        return self._save(fig, "nb11_p2_waterfall_perfiles.png")

    def plot_p3_risk_deciles(self, pat_bundle: GeneralPatternsBundle) -> Path:
        """NB12: P3 risk deciles observed rate, lift, and cumulative gain curve."""
        df_d = pat_bundle.p3_deciles_table.sort_values("decil_orden", ascending=True)
        df_gain = pat_bundle.p3_deciles_table.sort_values("decil_orden", ascending=False)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 4.8))
        x = np.arange(len(df_d))
        labels = [f"D{int(d):02d}" for d in df_d["decil_orden"]]

        ax1.bar(
            x - 0.18,
            df_d["tasa_observada_train_pct"],
            width=0.35,
            color="#1f77b4",
            label="Tasa observada Train (%)",
        )
        ax1.bar(
            x + 0.18,
            df_d["tasa_confirmada_test_pct"],
            width=0.35,
            color="#2ca02c",
            label="Tasa confirmada Test (%)",
        )
        ax1.plot(
            x,
            df_d["prob_media_train_pct"],
            color="#d62728",
            marker="o",
            linewidth=1.8,
            label="Probabilidad media predicha NB-H (%)",
        )
        ax1.axhline(30.01, color="gray", linestyle="--", linewidth=1.0, label="Prevalencia media (30.01%)")
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels)
        ax1.set_xlabel("Decil de probabilidad predicha (D01 menor riesgo a D10 mayor riesgo)")
        ax1.set_ylabel("Porcentaje (%)")
        ax1.set_title("P3 · Tasa observada vs. probabilidad predicha por decil")
        ax1.legend(loc="upper left", fontsize=8.0)
        ax1.grid(axis="y", alpha=0.25)

        pop_pct = np.r_[0.0, df_gain["pct_poblacion_acumulada"].to_numpy(dtype=float)]
        gain_tr = np.r_[0.0, df_gain["ganancia_acumulada_positivos_train_pct"].to_numpy(dtype=float)]
        gain_te = np.r_[0.0, df_gain["ganancia_acumulada_positivos_test_pct"].to_numpy(dtype=float)]

        ax2.plot(pop_pct, gain_tr, marker="o", color="#1f77b4", linewidth=2.0, label="Ganancia acumulada Train (OOF)")
        ax2.plot(pop_pct, gain_te, marker="s", linestyle="--", color="#2ca02c", linewidth=1.8, label="Ganancia acumulada Test")
        ax2.plot([0.0, 100.0], [0.0, 100.0], color="gray", linestyle=":", linewidth=1.2, label="Selección al azar (Lift = 1.0)")
        ax2.set_xlabel("Porcentaje acumulado de experiencias ordenadas de mayor a menor riesgo (%)")
        ax2.set_ylabel("Porcentaje acumulado de reincidencias capturadas (%)")
        ax2.set_title("P3 · Curva de ganancia acumulada (Cumulative Gain · D10 a D01)")
        ax2.legend(loc="lower right", fontsize=8.0)
        ax2.grid(alpha=0.25)

        fig.suptitle(
            "NB12 · Análisis P3: Estratificación por deciles de riesgo, Lift y Ganancia Acumulada (NB-H · Versión A)",
            fontsize=11.5,
            y=1.02,
        )
        return self._save(fig, "nb12_p3_deciles_lift_gain.png")

    def plot_p4_and_p5_career_and_education(self, pat_bundle: GeneralPatternsBundle) -> Path:
        """NB13: P4 career order & start year and P5 education level observed vs. predicted rates."""
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16.0, 4.6))

        # Panel 1: job_order
        jdf = pat_bundle.p4_job_order_table
        xj = np.arange(len(jdf))
        ax1.plot(xj, jdf["tasa_observada_train_pct"], marker="o", color="black", linewidth=2.2, label="Observada Train")
        ax1.plot(xj, jdf["prob_media_NB_G_train_pct"], marker="^", linestyle="--", color=MODEL_COLORS[MODEL_NB_G], label="Predicha NB-G")
        ax1.plot(xj, jdf["prob_media_NB_B_train_pct"], marker="v", linestyle=":", color=MODEL_COLORS[MODEL_NB_B], label="Predicha NB-B")
        ax1.plot(xj, jdf["prob_media_NB_H_train_pct"], marker="s", color=MODEL_COLORS[MODEL_NB_H], linewidth=1.8, label="Predicha NB-H")
        ax1.set_xticks(xj)
        ax1.set_xticklabels(jdf["tramo_job_order"], rotation=25, ha="right", fontsize=8.5)
        ax1.set_ylabel("Tasa de reincidencia (%)")
        ax1.set_title("P4a · Por posición en la carrera (job_order)")
        ax1.legend(loc="best", fontsize=7.5)
        ax1.grid(alpha=0.25)

        # Panel 2: start_year
        ydf = pat_bundle.p4_start_year_table
        xy = np.arange(len(ydf))
        ax2.plot(xy, ydf["tasa_observada_train_pct"], marker="o", color="black", linewidth=2.2, label="Observada Train")
        ax2.plot(xy, ydf["prob_media_NB_G_train_pct"], marker="^", linestyle="--", color=MODEL_COLORS[MODEL_NB_G], label="Predicha NB-G")
        ax2.plot(xy, ydf["prob_media_NB_B_train_pct"], marker="v", linestyle=":", color=MODEL_COLORS[MODEL_NB_B], label="Predicha NB-B")
        ax2.plot(xy, ydf["prob_media_NB_H_train_pct"], marker="s", color=MODEL_COLORS[MODEL_NB_H], linewidth=1.8, label="Predicha NB-H")
        ax2.set_xticks(xy)
        ax2.set_xticklabels(ydf["periodo_anio_inicio"], rotation=25, ha="right", fontsize=8.5)
        ax2.set_ylabel("Tasa de reincidencia (%)")
        ax2.set_title("P4b · Por periodo de inicio (start_year)")
        ax2.legend(loc="best", fontsize=7.5)
        ax2.grid(alpha=0.25)

        # Panel 3: university_level (P5)
        edf = pat_bundle.p5_education_table
        xe = np.arange(len(edf))
        ax3.bar(xe - 0.18, edf["tasa_observada_train_pct"], width=0.35, color="#1f77b4", label="Observada Train (%)")
        ax3.bar(xe + 0.18, edf["prob_media_oof_nb_h_train_pct"], width=0.35, color="#2ca02c", label="Predicha NB-H OOF (%)")
        ax3.set_xticks(xe)
        ax3.set_xticklabels(edf["university_level"], rotation=20, ha="right", fontsize=8.5)
        ax3.set_ylabel("Tasa de reincidencia (%)")
        ax3.set_title("P5 · Por nivel educativo (con 'No reportado')")
        ax3.legend(loc="best", fontsize=7.5)
        ax3.grid(axis="y", alpha=0.25)

        fig.suptitle(
            "NB13 · Análisis P4 y P5: Seguimiento de patrones por posición en la carrera, periodo y nivel educativo (Versión A)",
            fontsize=11.5,
            y=1.03,
        )
        return self._save(fig, "nb13_p4_p5_carrera_periodo_educacion.png")

    def plot_p7_and_p8_ablation_and_independence(self, pat_bundle: GeneralPatternsBundle) -> Path:
        """NB14: P7 behavior-block CV ablation and P8 correlated-pair independence audit."""
        p7 = pat_bundle.p7_block_ablation_cv_table.iloc[1:].copy()
        p8 = pat_bundle.p8_independence_audit_cv_table.iloc[1:].copy()

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.0, 5.2))

        y7 = np.arange(len(p7))
        vals7 = p7["cambio_pr_auc_vs_completo"].to_numpy(dtype=float)
        colors7 = ["#d62728" if v < 0 else "#2ca02c" for v in vals7]
        ax1.barh(y7, vals7, color=colors7, alpha=0.88)
        ax1.axvline(0.0, color="black", linewidth=1.0)
        ax1.set_yticks(y7)
        ax1.set_yticklabels(p7["experimento_ablacion"], fontsize=8.5)
        ax1.invert_yaxis()
        ax1.set_xlabel("Cambio en PR-AUC medio en CV 5-fold al retirar el bloque")
        ax1.set_title("P7 · Ablación por bloques de comportamiento (NB-H · Train CV)")
        ax1.grid(axis="x", alpha=0.25)

        y8 = np.arange(len(p8))
        w = 0.36
        ax2.barh(
            y8 - w / 2,
            p8["NB_H_delta_pr_auc"].to_numpy(dtype=float),
            height=w,
            color="#2ca02c",
            label="Cambio en PR-AUC (NB-H)",
        )
        ax2.barh(
            y8 + w / 2,
            p8["NB_G_delta_pr_auc"].to_numpy(dtype=float),
            height=w,
            color="#1f77b4",
            label="Cambio en PR-AUC (NB-G)",
        )
        ax2.axvline(0.0, color="black", linewidth=1.0)
        ax2.set_yticks(y8)
        ax2.set_yticklabels([s.split("->")[0].strip() for s in p8["experimento_independencia"]], fontsize=8.0)
        ax2.invert_yaxis()
        ax2.set_xlabel("Cambio en PR-AUC medio en CV 5-fold al retirar variable correlacionada")
        ax2.set_title("P8 · Auditoría de independencia condicional en pares correlacionados")
        ax2.legend(loc="best", fontsize=8.0)
        ax2.grid(axis="x", alpha=0.25)

        fig.suptitle(
            "NB14 · Análisis P7 y P8: Contribución por bloques de comportamiento y efecto del doble conteo en CV (Train A)",
            fontsize=11.5,
            y=1.02,
        )
        return self._save(fig, "nb14_p7_p8_ablacion_bloques_e_independencia.png")

    def plot_final_and_version_ab_comparison(
        self,
        eval_bundle: NaiveBayesEvaluationBundle,
        vcomp_bundle: VersionComparisonBundle,
    ) -> Path:
        """NB15: Final comparison on A vs References/Trees and Version A vs Version B sensitivity."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.5, 5.4))

        comp_a = eval_bundle.final_comparison_table_a
        # Filter key benchmark rows for clear bar chart
        keep_mask = (
            comp_a["modelo"].str.startswith("Ref")
            | comp_a["modelo"].str.contains("Recall")
            | comp_a["modelo"].str.contains("OOF")
        )
        sub_a = comp_a.loc[keep_mask].copy()
        y_pos = np.arange(len(sub_a))
        w = 0.36
        ax1.barh(
            y_pos - w / 2,
            sub_a["test_roc_auc"].to_numpy(dtype=float),
            height=w,
            color="#1f77b4",
            label="ROC-AUC Test (Techo 6.0 = 0.7133)",
        )
        ax1.barh(
            y_pos + w / 2,
            sub_a["test_f1_clase_1"].to_numpy(dtype=float),
            height=w,
            color="#ff7f0e",
            label="F1 Clase 1 Test (Ref 2 = 0.4612)",
        )
        ax1.axvline(0.4612, color="#d62728", linestyle="--", linewidth=1.1, label="Ref 2 F1 trivial (0.4612)")
        ax1.axvline(0.7133, color="#9467bd", linestyle=":", linewidth=1.2, label="Ref 3 ROC-AUC techo (0.7133)")
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(sub_a["modelo"], fontsize=8.2)
        ax1.invert_yaxis()
        ax1.set_xlabel("Puntaje en Test (Versión A · 347,720 filas)")
        ax1.set_title("Comparación en A: Naive Bayes vs. Referencias y Árboles (7.0)")
        ax1.legend(loc="lower right", fontsize=7.8)
        ax1.grid(axis="x", alpha=0.25)

        # Panel 2: Version A vs Version B (no refit & fixed-hyperparam refit)
        vdf = vcomp_bundle.comparison_table
        x_m = np.arange(len(MODEL_ORDER))
        schemes = [
            ("Versión A · CON outliers (Referencia)", "#1f77b4"),
            ("Versión B · SIN outliers (Sin reajuste)", "#ff7f0e"),
            ("Versión B · SIN outliers (Hiperparámetros fijos de A)", "#2ca02c"),
        ]
        width_b = 0.25
        for idx, (s_label, col) in enumerate(schemes):
            sub_v = vdf.loc[vdf["version_evaluada"] == s_label].set_index("modelo_id").reindex(MODEL_ORDER)
            vals_pr = sub_v["pr_auc_test"].to_numpy(dtype=float)
            bars = ax2.bar(
                x_m + (idx - 1) * width_b,
                vals_pr,
                width=width_b,
                color=col,
                alpha=0.88,
                label=s_label,
            )
            for b in bars:
                h = b.get_height()
                ax2.text(
                    b.get_x() + b.get_width() / 2.0,
                    h + 0.008,
                    f"{h:.4f}",
                    ha="center",
                    va="bottom",
                    fontsize=7.5,
                )

        ax2.set_xticks(x_m)
        ax2.set_xticklabels(list(MODEL_ORDER), fontsize=9.5)
        ax2.set_ylim(0.0, 0.62)
        ax2.set_ylabel("PR-AUC en Test (347,720 filas)")
        ax2.set_title("Sensibilidad a outliers: Versión A (con outliers) vs. Versión B (sin outliers)")
        ax2.legend(loc="upper left", fontsize=8.0)
        ax2.grid(axis="y", alpha=0.25)

        fig.suptitle(
            "NB15 · Comparación General en A y Sensibilidad a Outliers en Versión B (Paso 11 y Paso 12)",
            fontsize=11.5,
            y=1.02,
        )
        return self._save(fig, "nb15_comparacion_modelos_y_versiones_ab.png")

    def plot_e3_regularization_by_variant(
        self,
        vcomp_bundle: VersionComparisonBundle,
    ) -> Path:
        """NB16: E3 regularization (var_smoothing) x variant (A, A winsorized E2, B) on NB-H grouped CV."""
        piv = vcomp_bundle.e3_pivot_summary_table.sort_values("var_smoothing")
        x_log = np.log10(piv["var_smoothing"].to_numpy(dtype=float))

        fig, (ax_pr, ax_roc) = plt.subplots(1, 2, figsize=(14.5, 4.9))
        series_pr = [
            ("pr_auc_cv_A", "Versión A · original (con outliers)", "#1f77b4", "o", "-"),
            ("pr_auc_cv_A_wins_E2", "Versión A winsorizada (7 continuas · E2)", "#d62728", "s", "--"),
            ("pr_auc_cv_B", "Versión B · sin outliers (IQR 4 cols)", "#2ca02c", "^", ":"),
        ]
        series_roc = [
            ("roc_auc_cv_A", "Versión A · original (con outliers)", "#1f77b4", "o", "-"),
            ("roc_auc_cv_A_wins_E2", "Versión A winsorizada (7 continuas · E2)", "#d62728", "s", "--"),
            ("roc_auc_cv_B", "Versión B · sin outliers (IQR 4 cols)", "#2ca02c", "^", ":"),
        ]

        for col, lbl, clr, mk, ls in series_pr:
            if col in piv.columns and piv[col].notna().any():
                ax_pr.plot(
                    x_log,
                    piv[col].to_numpy(dtype=float),
                    color=clr,
                    marker=mk,
                    linestyle=ls,
                    linewidth=1.9,
                    label=lbl,
                )
        ax_pr.axvline(0.0, color="#555555", linestyle="-.", linewidth=1.1, label="Óptimo NB-H (var_smoothing=1.0)")
        ax_pr.set_xlabel("log10(var_smoothing)")
        ax_pr.set_ylabel("PR-AUC medio en StratifiedGroupKFold (5 pliegues)")
        ax_pr.set_title("E3 · PR-AUC de NB-H según regularización y variante")
        ax_pr.legend(loc="best", fontsize=8.0)
        ax_pr.grid(alpha=0.25)

        for col, lbl, clr, mk, ls in series_roc:
            if col in piv.columns and piv[col].notna().any():
                ax_roc.plot(
                    x_log,
                    piv[col].to_numpy(dtype=float),
                    color=clr,
                    marker=mk,
                    linestyle=ls,
                    linewidth=1.9,
                    label=lbl,
                )
        ax_roc.axvline(0.0, color="#555555", linestyle="-.", linewidth=1.1, label="Óptimo NB-H (var_smoothing=1.0)")
        ax_roc.set_xlabel("log10(var_smoothing)")
        ax_roc.set_ylabel("ROC-AUC medio en StratifiedGroupKFold (5 pliegues)")
        ax_roc.set_title("E3 · ROC-AUC de NB-H según regularización y variante")
        ax_roc.legend(loc="best", fontsize=8.0)
        ax_roc.grid(alpha=0.25)

        fig.suptitle(
            "NB16 · Experimento E3: Interacción entre var_smoothing y tratamiento de colas (A vs. A winsorizada vs. B · CV Train)",
            fontsize=11.3,
            y=1.03,
        )
        return self._save(fig, "nb16_e3_regularizacion_vs_outliers.png")
