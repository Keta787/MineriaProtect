"""Figuras reutilizables.

Responsabilidad unica (SOLID-S): dibujar. No calcula limites ni decide
tratamientos: los recibe ya calculados.

Regla del proyecto: cuando hay outliers, la figura los muestra o los recorta,
pero el DataFrame nunca se modifica.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def histograma(
    serie: pd.Series,
    titulo: str,
    xlabel: str,
    bins: int = 40,
    limites: dict[str, float] | None = None,
    ruta: Path | None = None,
) -> plt.Figure:
    """Histograma con limites de referencia opcionales."""
    datos = pd.to_numeric(serie, errors="coerce").dropna()
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.hist(datos, bins=bins, color="#3b6ea5", edgecolor="white", linewidth=0.4)

    if limites:
        for clave, color in (("inferior", "#c0392b"), ("superior", "#c0392b")):
            if clave in limites:
                ax.axvline(
                    limites[clave],
                    color=color,
                    linestyle="--",
                    linewidth=1.2,
                    label=f"limite {clave}: {limites[clave]:.1f}",
                )
        ax.legend(frameon=False)

    ax.set_title(titulo, loc="left", fontsize=11, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Frecuencia (filas)")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()

    if ruta is not None:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(ruta, dpi=150, bbox_inches="tight")
    return fig


def barras(
    serie: pd.Series,
    titulo: str,
    xlabel: str,
    ylabel: str = "Filas",
    horizontal: bool = True,
    ruta: Path | None = None,
) -> plt.Figure:
    """Barras ordenadas por frecuencia, con etiquetas de valor."""
    datos = serie.dropna()
    fig, ax = plt.subplots(figsize=(9, 4.5))
    if horizontal:
        datos.sort_values().plot.barh(ax=ax, color="#3b6ea5")
        ax.set_xlabel(ylabel)
        ax.set_ylabel(xlabel)
        for i, valor in enumerate(datos.sort_values().values):
            ax.text(valor, i, f" {valor:,}", va="center", fontsize=8)
    else:
        datos.sort_values(ascending=False).plot.bar(ax=ax, color="#3b6ea5")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
    ax.set_title(titulo, loc="left", fontsize=11, fontweight="bold")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()

    if ruta is not None:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(ruta, dpi=150, bbox_inches="tight")
    return fig
