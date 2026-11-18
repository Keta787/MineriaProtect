"""Chart renderer for the twenty-eight approved EDA figures.

Every chart is a small, independent method (open/closed principle): adding a
new figure means adding a method, not editing the existing ones.  All titles,
axis labels, legends and annotations are in Spanish; the code and the file
names stay in English.  Figures are written to
``reports/eda_jobpath/figures`` with the exact names of the manifest.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure

from .config import EDAConfig, UNIVERSITY_ORDER, VERSION_LABELS

# Okabe-Ito palette: distinguishable for the most common colour-vision types.
PALETTE: Sequence[str] = (
    "#0072B2",
    "#E69F00",
    "#009E73",
    "#CC79A7",
    "#56B4E9",
    "#D55E00",
    "#F0E442",
    "#000000",
)
SOURCE_NOTE = "Fuente: JobPath · experiencias laborales (datos seudonimizados)."
SOURCE_A = "Datos: empleos_unificado_limpio.csv · versión A (con outliers)."
SOURCE_B = (
    "Datos: empleos_limpio_con_competencias_sin_outliers.csv · "
    "versión B (sin outliers, IQR)."
)
SOURCE_AB = "Datos: CSV A (con outliers) y CSV B (sin outliers, IQR)."
SOURCE_PCA = (
    "Datos: salidas de 4.0_PCA.ipynb (10 k) y 4.1_PCA_completo.ipynb (50 k)."
)
SOURCE_TARGET_A = (
    "Datos: CSV A (con outliers) + y_train de A (data/04_transformed)."
)
SOURCE_TARGET_AB = (
    "Datos: y_train/y_test de data/04_transformed · versiones A y B."
)
SOURCE_LEAK = "Datos: X_train y y_train de A (data/04_transformed)."

#: Exact input of every approved figure.  Keeping the mapping in one place means
#: a new chart only has to be added here, not in the renderer methods.
FIGURE_SOURCES: Dict[str, str] = {
    "g01_duracion_empleo_hist.png": SOURCE_A,
    "g02_top_ocupaciones.png": SOURCE_A,
    "g03_duracion_por_isco.png": SOURCE_A,
    "g04_nivel_educativo.png": SOURCE_A,
    "g05_competencias_esenciales_hist.png": SOURCE_A,
    "g06_competencias_por_isco.png": SOURCE_A,
    "g07_experiencias_por_anio.png": SOURCE_A,
    "g08_nulos_por_columna.png": SOURCE_A,
    "g09_outliers_iqr_ab.png": SOURCE_AB,
    "g10_cobertura_esco_por_anio.png": SOURCE_A,
    "g11_empleos_por_persona.png": SOURCE_A,
    "g12_duracion_trayectoria.png": SOURCE_A,
    "g13_retornos_por_persona.png": SOURCE_A,
    "g14_forma_trayectoria.png": SOURCE_A,
    "g15_hexbin_empleos_oficios.png": SOURCE_A,
    "g16_transiciones_frecuentes.png": SOURCE_A,
    "g17_correlacion_pearson.png": SOURCE_A,
    "g19_pearson_vs_spearman.png": SOURCE_A,
    "g20_transiciones_ocupacion.png": SOURCE_A,
    "g21_transiciones_isco.png": SOURCE_A,
    "g22_autolazo_por_ocupacion.png": SOURCE_A,
    "g23_pca_estabilidad.png": SOURCE_PCA,
    "g25_comparacion_ab.png": SOURCE_AB,
    "g26_balance_target.png": SOURCE_TARGET_AB,
    "g27_target_por_isco.png": SOURCE_TARGET_A,
    "g28_target_por_duracion.png": SOURCE_TARGET_A,
    "g29_target_por_nivel.png": SOURCE_TARGET_A,
    "g30_fuga_target.png": SOURCE_LEAK,
}


class ChartRenderer:
    """Create and persist the approved figures."""

    def __init__(self, config: EDAConfig, save: bool = True) -> None:
        self._config = config
        self._save = save
        self._apply_style()

    # ------------------------------------------------------------------
    # Infrastructure
    # ------------------------------------------------------------------
    def _apply_style(self) -> None:
        sns.set_theme(style="whitegrid", context="notebook")
        plt.rcParams.update(
            {
                "figure.dpi": 110,
                "savefig.dpi": self._config.dpi,
                "axes.titlesize": 12,
                "axes.titleweight": "bold",
                "axes.labelsize": 10,
                "legend.fontsize": 9,
                "xtick.labelsize": 8,
                "ytick.labelsize": 8,
                "figure.autolayout": False,
            }
        )

    def _finish(self, fig: Figure, filename: str) -> Figure:
        source = FIGURE_SOURCES.get(filename, SOURCE_NOTE)
        fig.text(0.01, 0.005, source, fontsize=6.5, color="#555555")
        fig.tight_layout(rect=(0, 0.025, 1, 1))
        if self._save:
            self._config.figures_dir.mkdir(parents=True, exist_ok=True)
            fig.savefig(self._config.figures_dir / filename, bbox_inches="tight")
        return fig

    @staticmethod
    def _short(text: str, width: int = 38) -> str:
        text = str(text)
        return text if len(text) <= width else text[: width - 1] + "…"

    # ------------------------------------------------------------------
    # Experience level
    # ------------------------------------------------------------------
    def g01_duration_hist(self, frame: pd.DataFrame, clip: int = 60) -> Figure:
        """G01 · Distribution of job duration in quarters."""
        data = frame["dur_q"].dropna()
        clipped = data.clip(upper=clip)
        fig, ax = plt.subplots(figsize=(9, 4.5))
        bins = np.arange(1, clip + 2) - 0.5
        ax.hist(clipped, bins=bins, color=PALETTE[0], edgecolor="white", linewidth=0.3)
        ax.axvline(float(data.median()), color=PALETTE[5], linestyle="--", linewidth=1.5,
                   label=f"Mediana = {data.median():.0f} trimestres")
        ax.set_title("Duración de un empleo (trimestres)")
        ax.set_xlabel(f"Trimestres (valores > {clip} agrupados en el último bin)")
        ax.set_ylabel("Experiencias")
        ax.legend(loc="upper right")
        ax.annotate(
            f"n = {len(data):,}".replace(",", "."),
            xy=(0.02, 0.95), xycoords="axes fraction", fontsize=8, color="#333333",
        )
        return self._finish(fig, "g01_duracion_empleo_hist.png")

    def g02_top_occupations(self, table: pd.DataFrame) -> Figure:
        """G02 · Top 15 occupations plus an explicit ``Otras`` bucket."""
        data = table.iloc[::-1]
        fig, ax = plt.subplots(figsize=(9, 6))
        colors = [PALETTE[1] if c == "Otras" else PALETTE[0] for c in data["categoria"]]
        ax.barh([self._short(c, 45) for c in data["categoria"]], data["frecuencia"], color=colors)
        for y, (value, pct) in enumerate(zip(data["frecuencia"], data["pct"])):
            ax.text(value, y, f"  {pct:.1f}%", va="center", fontsize=7, color="#333333")
        ax.set_title("Ocupaciones con más experiencias registradas")
        ax.set_xlabel("Experiencias")
        ax.set_ylabel("Ocupación")
        return self._finish(fig, "g02_top_ocupaciones.png")

    def g03_duration_by_isco(self, frame: pd.DataFrame, top_n: int = 10, clip: int = 60) -> Figure:
        """G03 · Job duration by ISCO group, ordered by median."""
        data = frame.loc[frame["isco_group_label"].notna(), ["isco_group_label", "dur_q"]].dropna()
        top = data["isco_group_label"].value_counts().head(top_n).index
        data = data.loc[data["isco_group_label"].isin(top)].copy()
        data["dur_q"] = data["dur_q"].clip(upper=clip)
        medians = data.groupby("isco_group_label")["dur_q"].median().sort_values()
        order = medians.index.tolist()
        groups = [data.loc[data["isco_group_label"].eq(group), "dur_q"].to_numpy() for group in order]
        fig, ax = plt.subplots(figsize=(10, 6))
        boxes = ax.boxplot(
            groups,
            vert=False,
            patch_artist=True,
            showfliers=False,
            tick_labels=[self._short(group, 42) for group in order],
            medianprops={"color": PALETTE[5], "linewidth": 1.5},
            whiskerprops={"color": "#555555"},
            capprops={"color": "#555555"},
        )
        for patch in boxes["boxes"]:
            patch.set_facecolor(PALETTE[4])
            patch.set_alpha(0.85)
        ax.set_xlim(0, clip * 1.22)
        for position, group in enumerate(order, start=1):
            n = int(data["isco_group_label"].eq(group).sum())
            ax.text(clip * 1.02, position, f"n = {n:,}".replace(",", "."),
                    va="center", fontsize=7, color="#333333")
        ax.set_title("Duración del empleo por grupo ISCO (top 10)")
        ax.set_xlabel(f"Trimestres (recorte visual en {clip}; sin valores atípicos dibujados)")
        ax.set_ylabel("Grupo ISCO")
        return self._finish(fig, "g03_duracion_por_isco.png")

    def g04_education_levels(self, table: pd.DataFrame, order: Sequence[str] = UNIVERSITY_ORDER) -> Figure:
        """G04 · Experience count by education level, in ordinal order."""
        data = table.set_index("categoria").reindex([o for o in order if o in set(table["categoria"])])
        data = data.reset_index()
        fig, ax = plt.subplots(figsize=(8, 4.2))
        bars = ax.bar(data["categoria"], data["frecuencia"], color=PALETTE[2])
        for bar, pct in zip(bars, data["pct"]):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"{pct:.1f}%", ha="center", va="bottom", fontsize=8)
        ax.set_title("Nivel educativo declarado")
        ax.set_xlabel("Nivel educativo")
        ax.set_ylabel("Experiencias")
        ax.tick_params(axis="x", rotation=15)
        return self._finish(fig, "g04_nivel_educativo.png")

    def g05_skills_hist(self, frame: pd.DataFrame) -> Figure:
        """G05 · Distribution of essential skills per occupation."""
        data = frame["n_skills_essential"].dropna()
        upper = float(data.quantile(0.99))
        fig, ax = plt.subplots(figsize=(9, 4.5))
        ax.hist(data.clip(upper=upper), bins=40, color=PALETTE[3], edgecolor="white", linewidth=0.3)
        ax.axvline(float(data.median()), color=PALETTE[5], linestyle="--", linewidth=1.5,
                   label=f"Mediana = {data.median():.0f}")
        ax.set_title("Competencias esenciales que exige un oficio")
        ax.set_xlabel(f"N competencias esenciales (recorte visual en p99 = {upper:.0f})")
        ax.set_ylabel("Experiencias")
        ax.legend(loc="upper right")
        return self._finish(fig, "g05_competencias_esenciales_hist.png")

    def g06_skills_by_isco(self, frame: pd.DataFrame, top_n: int = 10) -> Figure:
        """G06 · Mean skill profile of the most frequent ISCO groups."""
        columns = ["n_skills_essential", "n_skills_competence", "n_skills_knowledge"]
        data = frame.loc[frame["isco_group_label"].notna()]
        top = data["isco_group_label"].value_counts().head(top_n).index
        data = data.loc[data["isco_group_label"].isin(top)]
        table = data.groupby("isco_group_label")[columns].mean().round(1)
        table = table.sort_values("n_skills_essential", ascending=False)
        fig, ax = plt.subplots(figsize=(8.5, 6))
        sns.heatmap(table, annot=True, fmt=".1f", cmap="YlGnBu", linewidths=0.5,
                    cbar_kws={"label": "Media de competencias"}, ax=ax,
                    annot_kws={"size": 8})
        ax.set_title("Perfil medio de competencias por grupo ISCO (top 10)")
        ax.set_xlabel("Tipo de competencia")
        ax.set_ylabel("Grupo ISCO")
        ax.set_xticklabels(["Esenciales", "Competencia", "Conocimiento"], rotation=0)
        ax.set_yticklabels([self._short(label, 38) for label in table.index], rotation=0)
        return self._finish(fig, "g06_competencias_por_isco.png")

    def g07_experiences_by_year(self, frame: pd.DataFrame) -> Figure:
        """G07 · Temporal coverage: experiences started per year."""
        counts = frame["start_year"].dropna().astype(int).value_counts().sort_index()
        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.bar(counts.index.astype(str), counts.values, color=PALETTE[4])
        step = max(1, len(counts) // 20)
        ax.set_xticks(range(0, len(counts), step))
        ax.set_xticklabels([str(y) for y in counts.index[::step]], rotation=45, ha="right")
        ax.set_title("Experiencias iniciadas por año")
        ax.set_xlabel("Año de inicio")
        ax.set_ylabel("Experiencias")
        return self._finish(fig, "g07_experiencias_por_anio.png")

    # ------------------------------------------------------------------
    # Quality and A/B comparison
    # ------------------------------------------------------------------
    def g08_nulls_heatmap(self, profile: pd.DataFrame) -> Figure:
        """G08 · Percentage of nulls per column, as a one-row heatmap."""
        data = profile.sort_values("null_pct", ascending=False)
        matrix = data["null_pct"].to_numpy().reshape(1, -1)
        fig, ax = plt.subplots(figsize=(12, 2.8))
        image = ax.imshow(matrix, aspect="auto", cmap="OrRd", vmin=0, vmax=max(10.0, float(matrix.max())))
        ax.set_xticks(range(len(data)))
        ax.set_xticklabels([self._short(c, 22) for c in data["column"]], rotation=90)
        ax.set_yticks([0])
        ax.set_yticklabels(["% nulos"])
        for index, value in enumerate(data["null_pct"]):
            if value > 0:
                ax.text(index, 0, f"{value:.1f}", ha="center", va="center", fontsize=6,
                        color="black" if value < matrix.max() * 0.6 else "white")
        ax.set_title("Porcentaje de nulos por columna")
        fig.colorbar(image, ax=ax, fraction=0.02, pad=0.01, label="% nulos")
        return self._finish(fig, "g08_nulos_por_columna.png")

    def g09_outliers_ab(self, outliers_a: pd.DataFrame, outliers_b: pd.DataFrame) -> Figure:
        """G09 · Share of IQR outliers per variable in A and B."""
        merged = outliers_a[["variable", "pct_atipicas"]].merge(
            outliers_b[["variable", "pct_atipicas"]], on="variable", suffixes=("_a", "_b")
        ).sort_values("pct_atipicas_a")
        y = np.arange(len(merged))
        fig, ax = plt.subplots(figsize=(9, 4.8))
        ax.barh(y - 0.2, merged["pct_atipicas_a"], height=0.4, color=PALETTE[5],
                label="A · con outliers")
        ax.barh(y + 0.2, merged["pct_atipicas_b"], height=0.4, color=PALETTE[0],
                label="B · sin outliers")
        ax.set_yticks(y)
        ax.set_yticklabels(merged["variable"])
        ax.set_title("Porcentaje de valores atípicos por variable (regla IQR 1,5)")
        ax.set_xlabel("% de filas fuera de los bigotes")
        ax.legend(loc="lower right")
        return self._finish(fig, "g09_outliers_iqr_ab.png")

    def g10_esco_coverage_by_year(
        self,
        frame: pd.DataFrame,
        min_year: int = 2000,
        max_year: int = 2020,
    ) -> Figure:
        """G10 · ESCO matching coverage by start year."""
        data = frame.loc[frame["start_year"].between(min_year, max_year)]
        table = pd.crosstab(data["start_year"], data["emparejado"], normalize="index").mul(100)
        table = table.reindex(columns=["ok", "rescatado", "unknown"], fill_value=0.0)
        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.stackplot(
            table.index,
            table["ok"],
            table["rescatado"],
            table["unknown"],
            labels=["Emparejado OK", "Rescatado desde código", "Sin emparejar"],
            colors=[PALETTE[2], PALETTE[1], PALETTE[5]],
            alpha=0.9,
        )
        ax.set_xlim(min_year, max_year)
        ax.set_ylim(0, 100)
        ax.set_title("Cobertura del emparejamiento ESCO por año de inicio")
        ax.set_xlabel("Año de inicio del empleo")
        ax.set_ylabel("% de experiencias")
        ax.legend(loc="lower left", ncol=3, fontsize=8)
        return self._finish(fig, "g10_cobertura_esco_por_anio.png")

    def g25_ab_comparison(self, comparison: pd.DataFrame, whatif: Dict[str, float]) -> Figure:
        """G25 · Dumbbell A vs B plus the hypothetical ``dur_q`` clipping."""
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={"width_ratios": [1.5, 1]})
        ax = axes[0]
        data = comparison.sort_values("mediana_a")
        y = np.arange(len(data))
        ax.hlines(y, data["mediana_a"], data["mediana_b"], color="#999999", linewidth=2)
        ax.scatter(data["mediana_a"], y, color=PALETTE[5], label="A · con outliers", zorder=3)
        ax.scatter(data["mediana_b"], y, color=PALETTE[0], label="B · sin outliers", zorder=3)
        ax.set_yticks(y)
        ax.set_yticklabels(data["variable"])
        ax.set_title("Mediana por versión")
        ax.set_xlabel("Mediana")
        ax.legend(loc="lower right")

        ax = axes[1]
        labels = ["Mediana", "Media", "Máximo"]
        before = [whatif["median_before"], whatif["mean_before"], whatif["max_before"]]
        after = [whatif["median_after"], whatif["mean_after"], whatif["max_after"]]
        x = np.arange(len(labels))
        ax.bar(x - 0.2, before, width=0.4, color=PALETTE[4], label="Antes")
        ax.bar(x + 0.2, after, width=0.4, color=PALETTE[6], label="Después (hipotético)")
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_yscale("log")
        ax.set_title("dur_q: recorte IQR hipotético")
        ax.set_ylabel("Trimestres (escala log)")
        ax.legend(loc="upper left")
        ax.annotate(
            f"Se recortarían {whatif['rows_clipped']:,} filas ({whatif['pct_clipped']:.2f}%)".replace(",", "."),
            xy=(0.02, 0.98), xycoords="axes fraction", va="top", fontsize=8,
        )
        return self._finish(fig, "g25_comparacion_ab.png")

    # ------------------------------------------------------------------
    # Person level
    # ------------------------------------------------------------------
    def g11_jobs_per_person(self, person: pd.DataFrame) -> Figure:
        """G11 · Number of jobs per person."""
        counts = person["n_jobs"].value_counts().sort_index()
        fig, ax = plt.subplots(figsize=(9, 4.5))
        ax.bar(counts.index.astype(str), counts.values, color=PALETTE[0])
        ax.set_title("Empleos por persona")
        ax.set_xlabel("N empleos")
        ax.set_ylabel("Personas")
        ax.annotate(
            f"Media = {person['n_jobs'].mean():.2f} · Mediana = {person['n_jobs'].median():.0f}",
            xy=(0.02, 0.95), xycoords="axes fraction", va="top", fontsize=9,
        )
        return self._finish(fig, "g11_empleos_por_persona.png")

    def g13_returns_per_person(self, table: pd.DataFrame) -> Figure:
        """G13 · People by number of returns to a previous occupation."""
        fig, ax = plt.subplots(figsize=(7.5, 4.2))
        bars = ax.bar(table["retornos"], table["personas"], color=PALETTE[2])
        for bar, pct in zip(bars, table["pct"]):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"{pct:.1f}%", ha="center", va="bottom", fontsize=9)
        ax.set_title("Personas según número de retornos a un oficio previo")
        ax.set_xlabel("Retornos")
        ax.set_ylabel("Personas")
        return self._finish(fig, "g13_retornos_por_persona.png")

    def g12_career_span(self, person: pd.DataFrame, quantile: float = 0.99) -> Figure:
        """G12 · Total trajectory length per person, clipped for readability."""
        data = person["span_q"].dropna()
        upper = float(data.quantile(quantile))
        clipped = data.clip(upper=upper)
        fig, ax = plt.subplots(figsize=(9, 4.5))
        ax.hist(clipped, bins=40, color=PALETTE[4], edgecolor="white", linewidth=0.3)
        ax.axvline(float(data.median()), color=PALETTE[5], linestyle="--", linewidth=1.5,
                   label=f"Mediana = {data.median():.0f} trimestres")
        ax.set_title("Duración total de la trayectoria por persona")
        ax.set_xlabel(
            f"Trimestres entre el primer inicio y el último fin "
            f"(recorte visual en p{int(quantile * 100)} = {upper:.0f})"
        )
        ax.set_ylabel("Personas")
        ax.legend(loc="upper right")
        ax.annotate(
            f"n = {len(data):,}".replace(",", "."),
            xy=(0.02, 0.95), xycoords="axes fraction", va="top", fontsize=8, color="#333333",
        )
        return self._finish(fig, "g12_duracion_trayectoria.png")

    def g14_trajectory_shape(self, segment: pd.DataFrame, thresholds: Dict[str, float]) -> Figure:
        """G14 · Distribution of self-loop and exploration shares with their Q75."""
        data = segment.loc[segment["n_jobs"] >= 2]
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
        ax = axes[0]
        ax.hist(data["self_loop_share"], bins=30, color=PALETTE[0],
                edgecolor="white", linewidth=0.3)
        ax.axvline(thresholds["self_loop_q75"], color=PALETTE[5], linestyle="--",
                   linewidth=1.5, label=f"Q75 = {thresholds['self_loop_q75']:.3f}")
        ax.set_title("Proporción de autolazos por persona")
        ax.set_xlabel("Autolazos / transiciones")
        ax.set_ylabel("Personas")
        ax.legend(loc="upper right")

        ax = axes[1]
        ax.hist(data["exploration_ratio"], bins=30, color=PALETTE[2],
                edgecolor="white", linewidth=0.3)
        ax.axvline(thresholds["exploration_q75"], color=PALETTE[5], linestyle="--",
                   linewidth=1.5, label=f"Q75 = {thresholds['exploration_q75']:.3f}")
        ax.set_title("Proporción de oficios distintos por empleo")
        ax.set_xlabel("Oficios distintos / empleos")
        ax.set_ylabel("Personas")
        ax.legend(loc="upper left")
        fig.suptitle("Forma de la trayectoria: dos medidas del segmento derivado", fontsize=12,
                     fontweight="bold")
        return self._finish(fig, "g14_forma_trayectoria.png")

    def g15_hexbin_jobs_occupations(self, sample: pd.DataFrame) -> Figure:
        """G15 · Density of jobs vs distinct occupations per person."""
        fig, ax = plt.subplots(figsize=(8, 5.5))
        image = ax.hexbin(sample["n_jobs"], sample["n_occ"], gridsize=30, cmap="viridis",
                          mincnt=1, bins="log")
        limit = max(float(sample["n_jobs"].max()), float(sample["n_occ"].max()))
        ax.plot([1, limit], [1, limit], color=PALETTE[5], linestyle="--", linewidth=1,
                label="n_occ = n_jobs (sin autolazos)")
        ax.set_title("Volumen de empleos frente a oficios distintos")
        ax.set_xlabel("N empleos por persona")
        ax.set_ylabel("N oficios distintos")
        ax.legend(loc="upper left")
        fig.colorbar(image, ax=ax, label="Personas (escala log)")
        return self._finish(fig, "g15_hexbin_empleos_oficios.png")

    # ------------------------------------------------------------------
    # Bivariate and transitions
    # ------------------------------------------------------------------
    def g17_correlation(self, matrix: pd.DataFrame) -> Figure:
        """G17 · Pearson correlation heatmap."""
        fig, ax = plt.subplots(figsize=(9.5, 8))
        sns.heatmap(matrix, annot=True, fmt=".2f", cmap="RdBu_r", center=0, vmin=-1, vmax=1,
                    square=True, linewidths=0.5, cbar_kws={"label": "Pearson r"}, ax=ax,
                    annot_kws={"size": 7})
        ax.set_title("Correlación de Pearson entre variables numéricas")
        ax.set_xlabel("")
        ax.set_ylabel("")
        return self._finish(fig, "g17_correlacion_pearson.png")

    def g19_pearson_vs_spearman(self, pearson: pd.DataFrame, spearman: pd.DataFrame) -> Figure:
        """G19 · Linear correlation against rank correlation for every pair."""
        names = list(pearson.columns)
        rows = []
        for index, first in enumerate(names):
            for second in names[index + 1:]:
                rows.append(
                    {
                        "variable_a": first,
                        "variable_b": second,
                        "pearson": float(pearson.loc[first, second]),
                        "spearman": float(spearman.loc[first, second]),
                    }
                )
        data = pd.DataFrame(rows).dropna()
        data["gap"] = (data["spearman"] - data["pearson"]).abs()
        fig, ax = plt.subplots(figsize=(6.8, 6))
        ax.scatter(data["pearson"], data["spearman"], color=PALETTE[0], alpha=0.75, s=32)
        ax.plot([-1, 1], [-1, 1], color="#999999", linestyle="--", linewidth=1,
                label="r = ρ (misma correlación)")
        ax.set_xlim(-1.05, 1.05)
        ax.set_ylim(-1.05, 1.05)
        ax.set_title("Correlación lineal frente a correlación de rangos")
        ax.set_xlabel("Pearson r")
        ax.set_ylabel("Spearman ρ")
        ax.legend(loc="upper left")
        if not data.empty:
            top = data.nlargest(1, "gap").iloc[0]
            ax.annotate(
                f"{self._short(top['variable_a'], 22)} / {self._short(top['variable_b'], 22)}\n"
                f"r = {top['pearson']:.2f} · ρ = {top['spearman']:.2f}",
                xy=(top["pearson"], top["spearman"]),
                xytext=(0.05, 0.05),
                textcoords="axes fraction",
                fontsize=7,
                arrowprops={"arrowstyle": "->", "color": "#555555", "lw": 0.8},
            )
        return self._finish(fig, "g19_pearson_vs_spearman.png")

    def g20_occupation_transitions(self, matrix: pd.DataFrame) -> Figure:
        """G20 · Fine-grained occupation -> occupation transitions."""
        fig, ax = plt.subplots(figsize=(11, 9))
        data = np.log1p(matrix.to_numpy())
        image = ax.imshow(data, aspect="auto", cmap="magma")
        ax.set_xticks(range(matrix.shape[1]))
        ax.set_xticklabels([self._short(c, 26) for c in matrix.columns], rotation=90)
        ax.set_yticks(range(matrix.shape[0]))
        ax.set_yticklabels([self._short(c, 30) for c in matrix.index])
        ax.set_title("Transiciones entre las ocupaciones más activas (top 20)")
        ax.set_xlabel("Ocupación de destino")
        ax.set_ylabel("Ocupación de origen")
        fig.colorbar(image, ax=ax, fraction=0.03, pad=0.02, label="log(1 + transiciones)")
        return self._finish(fig, "g20_transiciones_ocupacion.png")

    def g21_isco_transitions(self, matrix: pd.DataFrame) -> Figure:
        """G21 · Aggregated ISCO -> ISCO transitions."""
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(matrix, annot=True, fmt="d", cmap="Blues", linewidths=0.4,
                    cbar_kws={"label": "Transiciones"}, ax=ax, annot_kws={"size": 7})
        ax.set_xticklabels([self._short(c, 24) for c in matrix.columns], rotation=45, ha="right")
        ax.set_yticklabels([self._short(c, 26) for c in matrix.index], rotation=0)
        ax.set_title("Transiciones entre grupos ISCO")
        ax.set_xlabel("Grupo ISCO de destino")
        ax.set_ylabel("Grupo ISCO de origen")
        return self._finish(fig, "g21_transiciones_isco.png")

    def g16_top_moves(self, moves: pd.DataFrame) -> Figure:
        """G16 · Most frequent origin -> destination pairs, without self-loops."""
        data = moves.sort_values("transiciones", ascending=True)
        labels = [
            f"{self._short(source, 26)} → {self._short(dest, 26)}"
            for source, dest in zip(data["source_label"], data["dest_label"])
        ]
        fig, ax = plt.subplots(figsize=(10, 7))
        ax.barh(labels, data["transiciones"], color=PALETTE[3])
        for position, (value, pct) in enumerate(zip(data["transiciones"], data["pct_del_total"])):
            ax.text(value, position, f"  {value:,} ({pct:.1f}%)".replace(",", "."),
                    va="center", fontsize=7, color="#333333")
        ax.set_xlim(0, float(data["transiciones"].max()) * 1.35)
        ax.set_title("Transiciones más frecuentes entre oficios (sin autolazos)")
        ax.set_xlabel("Número de transiciones")
        ax.set_ylabel("Oficio de origen → oficio de destino")
        return self._finish(fig, "g16_transiciones_frecuentes.png")

    def g22_selfloop_by_occupation(self, rates: pd.DataFrame) -> Figure:
        """G22 · Self-loop and same-ISCO rates by origin occupation."""
        data = rates.sort_values("transiciones", ascending=True)
        y = np.arange(len(data))
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.barh(y - 0.2, data["autolazo_pct"], height=0.4, color=PALETTE[5],
                label="Autolazo (mismo oficio)")
        ax.barh(y + 0.2, data["mismo_isco_pct"], height=0.4, color=PALETTE[0],
                label="Mismo grupo ISCO (incluye autolazo)")
        ax.set_yticks(y)
        ax.set_yticklabels([self._short(label, 40) for label in data["source_label"]])
        ax.set_xlim(0, 100)
        ax.set_title("Autolazo y permanencia de área según ocupación de origen")
        ax.set_xlabel("% de transiciones desde esa ocupación")
        ax.set_ylabel("Ocupación de origen")
        ax.legend(loc="lower right")
        return self._finish(fig, "g22_autolazo_por_ocupacion.png")

    # ------------------------------------------------------------------
    # PCA evidence
    # ------------------------------------------------------------------
    def g23_pca_stability(self, variance: pd.DataFrame, components: pd.DataFrame) -> Figure:
        """G23 · Cumulative variance of the 10 k and 50 k PCA runs."""
        fig, ax = plt.subplots(figsize=(9, 5))
        styles = {
            ("10k", "con"): (PALETTE[5], "-", "o"),
            ("50k", "con"): (PALETTE[1], "--", "s"),
            ("10k", "sin"): (PALETTE[0], "-", "^"),
            ("50k", "sin"): (PALETTE[4], "--", "D"),
        }
        n80_map = {
            (row.source, row.version): int(row.n80) for row in components.itertuples()
        }
        for (source, version), (color, linestyle, marker) in styles.items():
            subset = variance.loc[
                (variance["source"] == source) & (variance["version"] == version)
            ].sort_values("component")
            if subset.empty:
                continue
            n80 = n80_map.get((source, version))
            suffix = f" · 80% con {n80} comp." if n80 is not None else ""
            label = f"{source} · {'A con outliers' if version == 'con' else 'B sin outliers'}{suffix}"
            ax.plot(range(1, len(subset) + 1), subset["cumulative_variance"] * 100,
                    color=color, linestyle=linestyle, marker=marker, markersize=4, label=label)
        ax.axhline(80, color="#777777", linestyle=":", linewidth=1, label="80 % de varianza")
        ax.set_title("Varianza acumulada del PCA: 10 k frente a 50 k")
        ax.set_xlabel("Componente principal")
        ax.set_ylabel("% de varianza acumulada")
        ax.set_ylim(30, 102)
        ax.legend(loc="lower right", fontsize=8)
        return self._finish(fig, "g23_pca_estabilidad.png")

    # ------------------------------------------------------------------
    # Target (train only)
    # ------------------------------------------------------------------
    def g26_target_balance(self, balance: pd.DataFrame) -> Figure:
        """G26 · Target prevalence in train and test for A and B."""
        balance = balance.copy()
        balance["serie"] = balance["version"] + " · " + balance["split"]
        fig, ax = plt.subplots(figsize=(8.5, 4.3))
        bars = ax.bar(balance["serie"], balance["tasa_pct"], color=PALETTE[: len(balance)])
        for bar, row in zip(bars, balance.itertuples()):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"{row.tasa_pct:.2f}%\nn={row.n:,}".replace(",", "."),
                    ha="center", va="bottom", fontsize=8)
        ax.set_title("Balance del target por versión y partición")
        ax.set_xlabel("Versión · partición")
        ax.set_ylabel("% de experiencias con reincidencia")
        ax.set_ylim(0, max(45, balance["tasa_pct"].max() * 1.25))
        ax.tick_params(axis="x", rotation=10)
        return self._finish(fig, "g26_balance_target.png")

    def g27_target_by_isco(self, table: pd.DataFrame) -> Figure:
        """G27 · Target rate by ISCO group (train, top 15 by volume)."""
        data = table.sort_values("tasa_pct")
        y = np.arange(len(data))
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.barh(y, data["tasa_pct"], color=PALETTE[0],
                xerr=[data["tasa_pct"] - data["ic95_inf_pct"],
                      data["ic95_sup_pct"] - data["tasa_pct"]],
                error_kw={"elinewidth": 1, "capsize": 2, "ecolor": "#333333"})
        ax.set_yticks(y)
        ax.set_yticklabels([self._short(c, 42) for c in data.iloc[:, 0]])
        overall = float((data["positivos"].sum() / data["n"].sum()) * 100)
        ax.axvline(overall, color=PALETTE[5], linestyle="--", linewidth=1.2,
                   label=f"Tasa global del top = {overall:.1f}%")
        for index, row in enumerate(data.itertuples()):
            ax.text(row.tasa_pct + 0.4, index, f"{row.tasa_pct:.1f}% · n={row.n:,}".replace(",", "."),
                    va="center", fontsize=7)
        ax.set_title("Tasa de reincidencia por grupo ISCO (solo train)")
        ax.set_xlabel("% de experiencias con reincidencia")
        ax.set_ylabel("Grupo ISCO")
        ax.legend(loc="lower right")
        return self._finish(fig, "g27_target_por_isco.png")

    def g28_target_by_duration(self, table: pd.DataFrame) -> Figure:
        """G28 · Target rate by duration interval (train)."""
        fig, ax = plt.subplots(figsize=(8.5, 4.5))
        bars = ax.bar(table["tramo"].astype(str), table["tasa_pct"], color=PALETTE[2],
                      yerr=[table["tasa_pct"] - table["ic95_inf_pct"],
                            table["ic95_sup_pct"] - table["tasa_pct"]],
                      error_kw={"elinewidth": 1, "capsize": 3, "ecolor": "#333333"})
        for bar, row in zip(bars, table.itertuples()):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"{row.tasa_pct:.1f}%\nn={row.n:,}".replace(",", "."),
                    ha="center", va="bottom", fontsize=8)
        ax.set_title("Tasa de reincidencia por tramo de duración (solo train)")
        ax.set_xlabel("Trimestres de duración del empleo")
        ax.set_ylabel("% de experiencias con reincidencia")
        ax.set_ylim(0, max(50, table["tasa_pct"].max() * 1.3))
        return self._finish(fig, "g28_target_por_duracion.png")

    def g29_target_by_education(self, table: pd.DataFrame) -> Figure:
        """G29 · Target rate by education level (train)."""
        fig, ax = plt.subplots(figsize=(8.5, 4.5))
        bars = ax.bar(table.iloc[:, 0].astype(str), table["tasa_pct"], color=PALETTE[3],
                      yerr=[table["tasa_pct"] - table["ic95_inf_pct"],
                            table["ic95_sup_pct"] - table["tasa_pct"]],
                      error_kw={"elinewidth": 1, "capsize": 3, "ecolor": "#333333"})
        for bar, row in zip(bars, table.itertuples()):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"{row.tasa_pct:.1f}%\nn={row.n:,}".replace(",", "."),
                    ha="center", va="bottom", fontsize=8)
        ax.set_title("Tasa de reincidencia por nivel educativo (solo train)")
        ax.set_xlabel("Nivel educativo declarado")
        ax.set_ylabel("% de experiencias con reincidencia")
        ax.set_ylim(0, max(50, table["tasa_pct"].max() * 1.3))
        ax.tick_params(axis="x", rotation=15)
        return self._finish(fig, "g29_target_por_nivel.png")

    def g30_leakage(self, audit: pd.DataFrame, contingency: pd.DataFrame) -> Figure:
        """G30 · Target leakage panel: match rates and target by repetition."""
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), gridspec_kw={"width_ratios": [1, 1.2]})
        ax = axes[0]
        data = audit.copy()
        colors = [PALETTE[5] if value >= 99.99 else PALETTE[1] for value in data["value"]]
        bars = ax.bar(data["variable"], data["value"], color=colors)
        for bar, value in zip(bars, data["value"]):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"{value:.2f}%", ha="center", va="bottom", fontsize=8)
        ax.set_ylim(0, 110)
        ax.set_title("Coincidencia con el target")
        ax.set_xlabel("Variable de X")
        ax.set_ylabel("% de filas que reproducen el target")
        ax.tick_params(axis="x", rotation=15)

        ax = axes[1]
        bars = ax.bar(contingency["veces_mostrada"].astype(str), contingency["tasa_pct"],
                      color=PALETTE[0])
        for bar, row in zip(bars, contingency.itertuples()):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"{row.tasa_pct:.1f}%", ha="center", va="bottom", fontsize=8)
        ax.set_title("Tasa de target según veces en el oficio")
        ax.set_xlabel("Veces que la persona tuvo ese oficio (recortado a 5)")
        ax.set_ylabel("% con reincidencia")
        ax.set_ylim(0, 110)
        return self._finish(fig, "g30_fuga_target.png")
