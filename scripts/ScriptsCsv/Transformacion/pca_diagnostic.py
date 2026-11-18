"""Diagnostico PCA educativo para variables numericas escaladas."""

from typing import Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA


def run_pca(scaled_df: pd.DataFrame, n_components: int = 10) -> Tuple[pd.DataFrame, pd.DataFrame, PCA]:
    """Ejecuta PCA y devuelve varianza, acumulada y loadings."""
    n_components = min(n_components, scaled_df.shape[0], scaled_df.shape[1])
    model = PCA(n_components=n_components, random_state=42)
    model.fit(scaled_df)
    variance = pd.DataFrame(
        {
            "component": [f"PC{i + 1}" for i in range(n_components)],
            "explained_variance_ratio": model.explained_variance_ratio_,
            "cumulative_variance": np.cumsum(model.explained_variance_ratio_),
        }
    )
    loadings = pd.DataFrame(model.components_.T, index=scaled_df.columns,
                           columns=[f"PC{i + 1}" for i in range(n_components)])
    return variance, loadings, model


def components_for_threshold(variance_df: pd.DataFrame, threshold: float) -> int:
    """Cantidad de componentes para alcanzar un umbral de varianza."""
    mask = variance_df["cumulative_variance"] >= threshold
    if not mask.any():
        return len(variance_df)
    return int(mask.idxmax() + 1)


def top_loadings(loadings: pd.DataFrame, component: str, n: int = 5) -> pd.DataFrame:
    """Variables con mayor peso absoluto en un componente."""
    result = loadings[component].abs().sort_values(ascending=False).head(n).to_frame("abs_loading")
    result["signed_loading"] = loadings.loc[result.index, component]
    return result
