"""Codificacion de variables nominales y ordinales, sin LabelEncoder en nominales."""

from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder


def derive_skill_presence(df: pd.DataFrame, skill_list_cols: List[str],
                        output_flags: List[str]) -> pd.DataFrame:
    """Convierte listas de skills en banderas de presencia 0/1."""
    if len(skill_list_cols) != len(output_flags):
        raise ValueError("skill_list_cols y output_flags deben tener la misma longitud")
    result = df.copy()
    for source, flag in zip(skill_list_cols, output_flags):
        if source not in result.columns:
            raise KeyError(f"La columna {source} no existe")
        result[flag] = result[source].fillna("").astype(str).str.strip().ne("").astype(np.uint8)
    return result


def ordinal_from_mapping(df: pd.DataFrame, source_col: str, mapping: Dict[str, int],
                        target_col: str, unknown_value: Optional[int] = None) -> pd.DataFrame:
    """Mapea una jerarquia genuina y valida valores no reconocidos."""
    result = df.copy()
    if source_col not in result.columns:
        raise KeyError(f"La columna {source_col} no existe")
    mapped = result[source_col].map(mapping)
    unknowns = result[source_col].notna() & mapped.isna()
    if unknowns.any() and unknown_value is None:
        values = sorted(result.loc[unknowns, source_col].astype(str).unique().tolist())
        raise ValueError(f"Valores no reconocidos en {source_col}: {values}")
    if unknown_value is not None:
        mapped = mapped.fillna(unknown_value)
    result[target_col] = mapped
    if result[target_col].isna().any():
        raise ValueError(f"La columna {target_col} contiene NaN despues del mapeo")
    return result


def fit_onehot(train: pd.DataFrame, columns: List[str], drop_first: bool = True,
               handle_unknown: str = "ignore") -> OneHotEncoder:
    """Ajusta OneHotEncoder en train. Use drop_first por multicolinealidad."""
    if not columns:
        raise ValueError("Se requiere al menos una columna para OneHotEncoder")
    encoder = OneHotEncoder(
        drop="first" if drop_first else None,
        handle_unknown=handle_unknown,
        sparse_output=False,
        dtype=int,
    )
    encoder.fit(train[columns].astype(str))
    return encoder


def transform_onehot(encoder: OneHotEncoder, df: pd.DataFrame,
                     columns: List[str]) -> pd.DataFrame:
    """Transforma con un encoder ajustado y devuelve DataFrame con nombres."""
    values = encoder.transform(df[columns].astype(str))
    output = pd.DataFrame(values, columns=encoder.get_feature_names_out(columns), index=df.index)
    return output.astype(np.uint8 if values.dtype != float else values.dtype)


def reduce_high_cardinality(series: pd.Series, strategy: str = "all",
                           top_n: int = 50, min_frequency: float = 0.01,
                           prefix_length: int = 4) -> pd.Series:
    """Alternativas para columnas de alta cardinalidad (ESCO)."""
    if strategy == "all":
        return series.astype(str)
    values = series.astype(str)
    if strategy == "top_n":
        keep = set(values.value_counts().head(top_n).index)
        return values.where(values.isin(keep), "other")
    if strategy == "frequency_threshold":
        frequencies = values.value_counts(normalize=True)
        keep = set(frequencies[frequencies >= min_frequency].index)
        return values.where(values.isin(keep), "other")
    if strategy == "prefix":
        return values.str.slice(0, prefix_length)
    raise ValueError(f"Estrategia de alta cardinalidad no soportada: {strategy}")
