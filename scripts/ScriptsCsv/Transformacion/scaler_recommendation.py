"""Recomendacion de escalador por columna (MinMax/Standard/Robust)."""

import numpy as np
import pandas as pd
from typing import List


def recommend_scalers(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Devuelve evidencia y recomendacion para cada columna numerica."""

    rows = []
    for col in columns:
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if series.empty:
            continue
        q1, q3 = series.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        pct_outside = float(((series < lower) | (series > upper)).mean() * 100)
        # Medida simple de pilas: repeticion del valor mas frecuente.
        top_freq = float(series.value_counts(normalize=True).iloc[0] * 100) if len(series) else 0.0
        skew = float(series.skew())
        kurt = float(series.kurt())

        if abs(skew) <= 0.5 and kurt <= 2.0 and pct_outside <= 2.0:
            scaler = "StandardScaler"
            evidence = "Distribucion cercana a normal y pocos extremos: adecuado como entrada continua para PCA."
        elif pct_outside <= 2.0 and top_freq < 25.0 and iqr > 0:
            scaler = "MinMaxScaler"
            evidence = "Rango acotado y sin colas problematicas; rescala a [0,1] sin inflar outliers."
        elif pct_outside <= 2.0 and iqr > 0 and top_freq >= 25.0:
            scaler = "MinMaxScaler"
            evidence = "Aunque hay valores repetidos, no hay outliers graves; MinMax conserva el rango finito."
        else:
            scaler = "RobustScaler"
            evidence = "Colas o valores extremos reales; la mediana y el IQR son mas estables que media/varianza o min/max."

        rows.append(
            {
                "column": col,
                "skewness": skew,
                "kurtosis": kurt,
                "pct_outside_tukey": pct_outside,
                "top_value_frequency_pct": top_freq,
                "recommended_scaler": scaler,
                "evidence": evidence,
            }
        )
    return pd.DataFrame(rows)
