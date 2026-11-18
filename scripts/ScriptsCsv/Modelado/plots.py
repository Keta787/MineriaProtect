"""Spanish-labeled figure generation for CRISP-DM Phase 4 (Modeling & Evaluation)."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import ModelingConfig
from .evaluation import CurveData, EvaluationBundle


class ModelingPlotter:
    """Render and persist Phase 4 diagnostic and evaluation figures in Spanish."""

    def __init__(self, config: ModelingConfig) -> None:
        self.config = config
        self.config.figures_dir.mkdir(parents=True, exist_ok=True)

    def _save_fig(self, fig: plt.Figure, filename: str) -> Path:
        out_path = self.config.figures_dir / filename
        fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return out_path

    def plot_ablation(self, ablation_df: pd.DataFrame) -> Path:
        """M01: Bar chart comparing CV metrics with leakage vs without leakage vs clean."""
        fig, ax = plt.subplots(figsize=(9.5, 4.8))
        labels = ablation_df["esquema_features"].tolist()
        metrics = [
            ("pr_auc_cv_media", "PR-AUC (media CV 5-fold)", "#1f77b4"),
            ("f1_pos_cv_media", "F1 clase positiva (reincide=1)", "#ff7f0e"),
            ("roc_auc_cv_media", "ROC-AUC (media CV 5-fold)", "#2ca02c"),
        ]
        x = np.arange(len(labels))
        width = 0.25

        for idx, (col, label, color) in enumerate(metrics):
            vals = ablation_df[col].to_numpy(dtype=float)
            bars = ax.bar(x + (idx - 1) * width, vals, width=width, label=label, color=color, alpha=0.9)
            for bar in bars:
                h = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    h + 0.015,
                    f"{h:.3f}",
                    ha="center",
                    va="bottom",
                    fontsize=8.5,
                )

        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=9.5)
        ax.set_ylim(0.0, 1.14)
        ax.axhline(0.3001, color="#d62728", linestyle="--", linewidth=1.1, label="Prevalencia base en train (0.3001)")
        ax.set_ylabel("Puntaje en validación cruzada por persona")
        ax.set_title("M01 · Ablación de fuga del target y control de colinealidad (Train · 5-Fold por resume_id)")
        ax.legend(loc="upper right", fontsize=8.5)
        ax.grid(axis="y", alpha=0.25)
        return self._save_fig(fig, "m01_ablacion_fuga_y_colinealidad.png")

    def plot_pr_and_roc_curves(self, curves: List[CurveData]) -> Path:
        """M02: Precision-Recall and ROC curves on the test partition (347,720 rows)."""
        fig, (ax_pr, ax_roc) = plt.subplots(1, 2, figsize=(12.5, 5.0))
        palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd"]

        for idx, c in enumerate(curves):
            color = palette[idx % len(palette)]
            short_v = "A (con outliers)" if c.version_label.startswith("A") else "B (sin outliers)"
            short_m = "Logística OHE" if "Logística" in c.model_name else "HistGradientBoosting"
            ax_pr.plot(
                c.recall,
                c.precision,
                label=f"{short_v} · {short_m} (PR-AUC={c.pr_auc:.3f})",
                color=color,
                linewidth=1.8,
            )
            ax_roc.plot(
                c.fpr,
                c.tpr,
                label=f"{short_v} · {short_m} (ROC-AUC={c.roc_auc:.3f})",
                color=color,
                linewidth=1.8,
            )

        ax_pr.axhline(0.2997, color="gray", linestyle="--", linewidth=1.1, label="Azar en test (0.2997)")
        ax_pr.set_xlabel("Exhaustividad (Recall · clase positiva)")
        ax_pr.set_ylabel("Precisión (Precision · clase positiva)")
        ax_pr.set_title("Curva Precision-Recall en Test (347,720 filas)")
        ax_pr.set_xlim(0.0, 1.0)
        ax_pr.set_ylim(0.0, 1.02)
        ax_pr.legend(loc="upper right", fontsize=8.0)
        ax_pr.grid(alpha=0.25)

        ax_roc.plot([0, 1], [0, 1], color="gray", linestyle="--", linewidth=1.1, label="Azar (ROC-AUC=0.500)")
        ax_roc.set_xlabel("Tasa de Falsos Positivos (FPR)")
        ax_roc.set_ylabel("Tasa de Verdaderos Positivos (TPR / Recall)")
        ax_roc.set_title("Curva ROC en Test (347,720 filas)")
        ax_roc.set_xlim(0.0, 1.0)
        ax_roc.set_ylim(0.0, 1.02)
        ax_roc.legend(loc="lower right", fontsize=8.0)
        ax_roc.grid(alpha=0.25)

        fig.suptitle("M02 · Desempeño fuera de muestra en Test por persona (70,419 personas · Sin fuga)", fontsize=11.5, y=1.02)
        return self._save_fig(fig, "m02_curvas_pr_y_roc_test.png")

    def plot_version_comparison(self, test_df: pd.DataFrame) -> Path:
        """M03: Grouped comparison between Version A (with outliers) and Version B (without outliers)."""
        non_dummy = test_df.loc[test_df["modelo"] != "Baseline (Prior)"].copy()
        fig, ax = plt.subplots(figsize=(10.0, 4.8))
        labels = [
            f"{row['version'].split('·')[0].strip()} · {'Logística OHE' if 'Logística' in row['modelo'] else 'HistGradBoost'}"
            for _, row in non_dummy.iterrows()
        ]
        x = np.arange(len(labels))
        width = 0.20
        metric_specs = [
            ("pr_auc_test", "PR-AUC Test", "#1f77b4"),
            ("f1_pos_test", "F1 Positiva Test", "#ff7f0e"),
            ("recall_pos_test", "Recall Positiva Test", "#2ca02c"),
            ("roc_auc_test", "ROC-AUC Test", "#9467bd"),
        ]
        for idx, (col, mlabel, color) in enumerate(metric_specs):
            vals = non_dummy[col].to_numpy(dtype=float)
            bars = ax.bar(x + (idx - 1.5) * width, vals, width=width, label=mlabel, color=color, alpha=0.9)
            for bar in bars:
                h = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    h + 0.01,
                    f"{h:.3f}",
                    ha="center",
                    va="bottom",
                    fontsize=8.0,
                )

        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=9.0)
        ax.set_ylim(0.0, 0.90)
        ax.set_ylabel("Valor de la métrica en Test")
        ax.set_title("M03 · Comparación Versión A (con outliers) vs. Versión B (sin outliers IQR) en Test")
        ax.legend(loc="upper right", fontsize=8.5, ncol=2)
        ax.grid(axis="y", alpha=0.25)
        return self._save_fig(fig, "m03_comparacion_modelos_ab.png")

    def plot_feature_importance(self, imp_df: pd.DataFrame) -> Path:
        """M04: Horizontal bar chart of signed logistic coefficients for the 14 legitimate dense features."""
        sub_a = imp_df.loc[imp_df["version"].str.startswith("A")].sort_values("coef_logistico", ascending=True)
        fig, ax = plt.subplots(figsize=(9.0, 5.2))
        vals = sub_a["coef_logistico"].to_numpy(dtype=float)
        names = sub_a["variable"].tolist()
        colors = ["#2ca02c" if v >= 0 else "#d62728" for v in vals]

        y_pos = np.arange(len(names))
        ax.barh(y_pos, vals, color=colors, alpha=0.88)
        ax.axvline(0.0, color="black", linewidth=0.9)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(names, fontsize=9.0)
        ax.set_xlabel("Coeficiente logístico regularizado (escala estandarizada · sin fuga)")
        ax.set_title("M04 · Peso y dirección de las 14 variables densas legítimas sobre reincide (Versión A)")
        ax.grid(axis="x", alpha=0.25)
        return self._save_fig(fig, "m04_importancia_variables_sin_fuga.png")

    def render_all(self, bundle: EvaluationBundle) -> Dict[str, str]:
        """Generate all four Phase 4 figures and return their paths."""
        return {
            "M01": str(self.plot_ablation(bundle.ablation_table)),
            "M02": str(self.plot_pr_and_roc_curves(bundle.curves)),
            "M03": str(self.plot_version_comparison(bundle.test_summary_table)),
            "M04": str(self.plot_feature_importance(bundle.feature_importance_table)),
        }

