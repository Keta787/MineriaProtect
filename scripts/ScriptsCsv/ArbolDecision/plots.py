"""Plotting utilities for Decision Tree visualization, evaluation panels, and A vs B comparison."""

from __future__ import annotations

from pathlib import Path
import textwrap
from typing import Dict, Optional, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier, plot_tree

from .config import (
    ASPIRATIONAL_TARGET_SCORE,
    BLOCK_METADATA_ES,
    MAX_TREE_DEPTH,
    VERSION_A,
    VERSION_B,
    VERSION_LABELS_ES,
)


plt.rcParams["figure.dpi"] = 120
plt.rcParams["savefig.dpi"] = 160
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Segoe UI"]
plt.rcParams["axes.unicode_minus"] = False


def _wrap_verbatim(text: str, width: int = 58) -> str:
    """Wrap a verbatim Spanish question across lines without altering a single word or character."""
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False))


def plot_decision_tree_legible(
    clf: DecisionTreeClassifier,
    feature_names: Sequence[str],
    tree_label_es: str,
    question_es: str,
    version_label_es: str,
    subtitle_es: str,
    output_path: Optional[Path] = None,
) -> plt.Figure:
    """Plot a DecisionTreeClassifier (max_depth <= 4) with verbatim question and version label."""
    if clf.get_depth() > MAX_TREE_DEPTH:
        raise ValueError(f"Cannot plot a tree deeper than {MAX_TREE_DEPTH}!")

    n_leaves = clf.get_n_leaves()
    fig_width = 24 if n_leaves <= 10 else 28
    fig_height = 11.5 if clf.get_depth() <= 3 else 13.5

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    plot_tree(
        clf,
        feature_names=list(feature_names),
        class_names=["No reincide (0)", "Reincide (1)"],
        filled=True,
        rounded=True,
        proportion=True,
        precision=2,
        fontsize=9 if n_leaves > 10 else 10,
        max_depth=MAX_TREE_DEPTH,
        ax=ax,
    )
    fig.suptitle(
        f"{tree_label_es} · {version_label_es}\n{question_es}",
        fontsize=14,
        fontweight="bold",
        y=0.985,
    )
    ax.set_title(
        f"{subtitle_es}\nNota de lectura: en conteos enteros un corte <= k.5 equivale a '<= k' (rama izquierda) "
        f"y '> k.5' equivale a 'k+1 o más' (rama derecha).",
        fontsize=10.5,
        pad=10,
        color="#333333",
    )
    fig.tight_layout(rect=[0.0, 0.0, 1.0, 0.93])

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, bbox_inches="tight")

    return fig


def plot_depth_and_confusion_panel(
    depth_df: pd.DataFrame,
    cm_test_none: np.ndarray,
    cm_test_balanced: np.ndarray,
    tree_label_es: str,
    question_es: str,
    version_label_es: str,
    output_path: Optional[Path] = None,
) -> plt.Figure:
    """Plot Test confusion matrices (None & balanced) and depth evolution (2, 3, 4) with version label."""
    fig, axes = plt.subplots(1, 3, figsize=(18.5, 5.4))

    for idx, (cm, pt_title) in enumerate(
        (
            (cm_test_none, "Punto Exactitud (class_weight=None)"),
            (cm_test_balanced, "Punto Recall (class_weight='balanced')"),
        )
    ):
        ax_cm = axes[idx]
        im = ax_cm.imshow(cm, cmap="Blues")
        ax_cm.set_xticks([0, 1])
        ax_cm.set_yticks([0, 1])
        ax_cm.set_xticklabels(["Pred: 0 (No repite)", "Pred: 1 (Repite)"])
        ax_cm.set_yticklabels(["Real: 0 (No repite)", "Real: 1 (Repite)"])
        ax_cm.set_title(
            f"Matriz de Confusión Test · {version_label_es}\n{pt_title}",
            fontsize=10.5,
            fontweight="bold",
        )
        total_test = cm.sum()
        for i in range(2):
            for j in range(2):
                val = int(cm[i, j])
                pct = 100.0 * val / max(total_test, 1)
                text_color = "white" if val > (cm.max() * 0.55) else "#111111"
                ax_cm.text(
                    j,
                    i,
                    f"{val:,}\n({pct:.1f}%)",
                    ha="center",
                    va="center",
                    fontsize=10,
                    fontweight="bold",
                    color=text_color,
                )
        fig.colorbar(im, ax=ax_cm, fraction=0.046, pad=0.04)

    # Panel 3: Depth table (2, 3, 4)
    ax_d = axes[2]
    sub_none = depth_df.loc[depth_df["punto_operacion"].str.contains("None")].sort_values("max_depth")
    sub_bal = depth_df.loc[depth_df["punto_operacion"].str.contains("balanced")].sort_values("max_depth")

    depths = sub_bal["max_depth"].to_numpy()
    ax_d.plot(
        depths,
        sub_none["test_acc"],
        marker="o",
        linewidth=2.2,
        label="Exactitud Test (class_weight=None)",
        color="#1f77b4",
    )
    ax_d.plot(
        depths,
        sub_bal["test_acc"],
        marker="s",
        linewidth=2.0,
        linestyle="--",
        label="Exactitud Test (class_weight='balanced')",
        color="#ff7f0e",
    )
    ax_d.plot(
        depths,
        sub_bal["test_f1_clase_1"],
        marker="^",
        linewidth=2.2,
        label="F1 Clase 1 Test (class_weight='balanced')",
        color="#2ca02c",
    )
    ax_d.plot(
        depths,
        sub_bal["test_roc_auc"],
        marker="D",
        linewidth=2.0,
        linestyle=":",
        label="ROC-AUC Test (class_weight='balanced')",
        color="#9467bd",
    )

    for _, row in sub_bal.iterrows():
        d_val = int(row["max_depth"])
        n_lv = int(row["n_leaves"])
        t_auc = float(row["test_roc_auc"])
        ax_d.annotate(
            f"{n_lv} hojas",
            xy=(d_val, t_auc),
            xytext=(0, 7),
            textcoords="offset points",
            ha="center",
            fontsize=8.5,
            color="#333333",
        )

    ax_d.set_xticks([2, 3, 4])
    ax_d.set_xticklabels(["Profundidad 2", "Profundidad 3", "Profundidad 4"])
    ax_d.set_ylabel("Valor de métrica en Test (proporción)", fontsize=10)
    ax_d.set_xlabel("Límite de profundidad (max_depth)", fontsize=10)
    ax_d.set_title(
        f"Profundidades 2, 3 y 4 · {version_label_es}",
        fontsize=10.5,
        fontweight="bold",
    )
    ax_d.set_ylim(0.25, 0.80)
    ax_d.grid(True, linestyle=":", alpha=0.6)
    ax_d.legend(loc="best", fontsize=8.5)

    fig.suptitle(
        f"{tree_label_es} · {version_label_es}\n{question_es}",
        fontsize=12.5,
        fontweight="bold",
        y=1.03,
    )
    fig.tight_layout()
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, bbox_inches="tight")

    return fig


def plot_feature_importances_three_trees(
    importances_by_block: Dict[str, pd.DataFrame],
    version_label_es: str,
    output_path: Optional[Path] = None,
) -> plt.Figure:
    """Plot horizontal bar charts of feature_importances_ for each of the three trees."""
    fig, axes = plt.subplots(1, 3, figsize=(19, 5.8))

    colors = ["#2b5c8f", "#388e3c", "#d95f02"]
    for idx, (block_id, df_imp) in enumerate(importances_by_block.items()):
        ax = axes[idx]
        meta = BLOCK_METADATA_ES[block_id]
        top_df = df_imp.head(10).iloc[::-1]

        bars = ax.barh(
            top_df["variable"],
            top_df["importancia_pct"],
            color=colors[idx % len(colors)],
            alpha=0.88,
            edgecolor="#222222",
        )
        for bar in bars:
            width = bar.get_width()
            ax.text(
                width + 1.0,
                bar.get_y() + bar.get_height() / 2.0,
                f"{width:.1f}%",
                va="center",
                ha="left",
                fontsize=9,
            )

        ax.set_xlim(0, 114)
        ax.set_xlabel("Importancia relativa en el árbol (%)", fontsize=10)
        wrapped_q = _wrap_verbatim(meta["question_es"], width=48)
        ax.set_title(
            f"{meta['tree_label']} · {version_label_es}\n{wrapped_q}",
            fontsize=10,
            fontweight="bold",
        )
        ax.grid(axis="x", linestyle=":", alpha=0.6)

    fig.suptitle(
        f"Importancia de Variables por Árbol · {version_label_es} (Lo que este árbol miró · NO implica causalidad)",
        fontsize=13,
        fontweight="bold",
        y=1.03,
    )
    fig.tight_layout()

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, bbox_inches="tight")

    return fig


def plot_trees_vs_baseline_and_ceiling(
    comparison_df: pd.DataFrame,
    output_path: Optional[Path] = None,
) -> plt.Figure:
    """Plot grouped bars comparing the 3 References and the 3 Decision Trees (Versions A & B)."""
    fig, ax = plt.subplots(figsize=(15.5, 6.6))

    labels = [
        f"{row['modelo_corto']}\n[{row['version_datos']}]"
        for _, row in comparison_df.iterrows()
    ]
    x = np.arange(len(labels))
    width = 0.20

    m_acc = comparison_df["test_accuracy"].to_numpy(dtype=float)
    m_rec = comparison_df["test_recall_clase_1"].to_numpy(dtype=float)
    m_f1 = comparison_df["test_f1_clase_1"].to_numpy(dtype=float)
    m_auc = comparison_df["test_roc_auc"].to_numpy(dtype=float)

    ax.bar(x - 1.5 * width, m_acc, width, label="Exactitud Test (Accuracy)", color="#4e79a7")
    ax.bar(x - 0.5 * width, m_rec, width, label="Sensibilidad / Recall Clase 1", color="#e15759")
    bars_f1 = ax.bar(x + 0.5 * width, m_f1, width, label="F1-Score Clase 1", color="#59a14f")
    bars_auc = ax.bar(x + 1.5 * width, m_auc, width, label="ROC-AUC Test", color="#9467bd")

    for bar in bars_f1:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            h + 0.012,
            f"{h:.3f}",
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold",
            color="#1b5e20",
        )
    for bar in bars_auc:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            h + 0.012,
            f"{h:.3f}",
            ha="center",
            va="bottom",
            fontsize=8,
            color="#4a148c",
        )

    ax.axhline(
        ASPIRATIONAL_TARGET_SCORE,
        color="#b71c1c",
        linestyle="--",
        linewidth=1.8,
        label="Línea de referencia aspiracional (0.85)",
    )
    ax.axhline(
        0.7003,
        color="#1f77b4",
        linestyle=":",
        linewidth=1.5,
        label="Ref 1 · Baseline Exactitud Mayoritaria (0.7003)",
    )
    ax.axhline(
        0.4612,
        color="#d95f02",
        linestyle="-.",
        linewidth=1.4,
        label="Ref 2 · F1 Trivial Todo-Positivo 2p/(1+p) (0.4612)",
    )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=18, ha="right", fontsize=8.8)
    ax.set_ylim(0.0, 0.98)
    ax.set_ylabel("Valor de métrica en Test (proporción)", fontsize=11)
    ax.set_title(
        "¿El perfil de un oficio separa a las personas que lo repiten de las que lo ejercen por primera vez?\n"
        "Comparación en Test: 3 Referencias (Baseline, Todo-1, Techo 6.0) vs. 3 Árboles (Versión A · CON outliers y Versión B · SIN outliers)",
        fontsize=11.5,
        fontweight="bold",
    )
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", ncol=2, fontsize=8.8)

    fig.tight_layout()
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, bbox_inches="tight")

    return fig


def plot_sensitivity_version_a_vs_b(
    per_seed_df: pd.DataFrame,
    output_path: Optional[Path] = None,
) -> plt.Figure:
    """Plot grouped CV ROC-AUC and Test F1 across the 5 seeds comparing Version A vs Version B."""
    fig, axes = plt.subplots(1, 3, figsize=(18.5, 5.6), sharey=True)
    blocks = per_seed_df["bloque_id"].unique().tolist()

    label_a = VERSION_LABELS_ES[VERSION_A]
    label_b = VERSION_LABELS_ES[VERSION_B]

    for idx, block_id in enumerate(blocks):
        ax = axes[idx]
        meta = BLOCK_METADATA_ES[block_id]
        sub = per_seed_df.loc[per_seed_df["bloque_id"] == block_id]
        sub_a = sub.loc[sub["version_codigo"] == VERSION_A].sort_values("semilla")
        sub_b = sub.loc[sub["version_codigo"] == VERSION_B].sort_values("semilla")

        seeds_labels = [f"Semilla {s}" for s in sub_a["semilla"].tolist()]
        x = np.arange(len(seeds_labels))
        width = 0.34

        ax.bar(
            x - width / 2,
            sub_a["cv_train_f1_1"],
            width,
            label=f"{label_a} (F1 CV Train)",
            color="#1f77b4",
            alpha=0.9,
        )
        ax.bar(
            x + width / 2,
            sub_b["cv_train_f1_1"],
            width,
            label=f"{label_b} (F1 CV Train)",
            color="#ff7f0e",
            alpha=0.9,
        )
        ax.plot(
            x - width / 2,
            sub_a["test_roc_auc"],
            marker="o",
            linestyle="none",
            color="#0b3c68",
            label=f"ROC-AUC Test ({label_a})",
        )
        ax.plot(
            x + width / 2,
            sub_b["test_roc_auc"],
            marker="D",
            linestyle="none",
            color="#993d00",
            label=f"ROC-AUC Test ({label_b})",
        )

        ax.set_xticks(x)
        ax.set_xticklabels(seeds_labels, rotation=20, fontsize=9.5)
        ax.set_ylim(0.0, 0.72)
        wrapped_q = _wrap_verbatim(meta["question_es"], width=46)
        ax.set_title(f"{meta['tree_label']}\n{wrapped_q}", fontsize=10, fontweight="bold")
        ax.grid(axis="y", linestyle=":", alpha=0.6)
        if idx == 0:
            ax.set_ylabel("Valor de métrica (F1 Clase 1 / ROC-AUC)", fontsize=10.5)
            ax.legend(loc="lower right", fontsize=8.3)

    fig.suptitle(
        f"Sensibilidad en 5 Semillas (3,000 personas Train / 750 Test): {label_a} vs. {label_b}",
        fontsize=12.8,
        fontweight="bold",
        y=1.03,
    )
    fig.tight_layout()

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, bbox_inches="tight")

    return fig
