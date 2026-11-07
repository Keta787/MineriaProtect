"""Split por persona y ensamblado sin fuga de datos."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from .discretization import fit_discretizers, transform_discretizers
from .encoding import fit_onehot, transform_onehot
from .scaling import FittedScaling, fit_scaling, transform_scaling


@dataclass
class TransformArtifacts:
    scaling: FittedScaling
    onehot_columns: List[str]
    onehot: Optional[object]
    discretizers: Dict[str, object]
    discretization_columns: List[str]
    discretization_spec: Dict[str, object]
    binary_columns: List[str]
    presence_columns: List[str]
    feature_order: List[str] = field(default_factory=list)


def group_train_test_split(df: pd.DataFrame, group_col: str = "resume_id",
                          test_size: float = 0.2, random_state: int = 42
                          ) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Divide por persona para evitar fuga entre train y test."""
    if group_col not in df.columns:
        raise KeyError(f"Falta la columna de persona: {group_col}")
    groups = df[group_col].astype(str)
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, test_idx = next(splitter.split(df, groups=groups))
    train = df.iloc[train_idx].copy().reset_index(drop=True)
    test = df.iloc[test_idx].copy().reset_index(drop=True)
    return train, test


def fit_artifacts(train_df: pd.DataFrame, scaling_plan: Dict[str, str],
                 onehot_cols: List[str], discretization_spec: Dict[str, object],
                 binary_cols: List[str], presence_cols: List[str],
                 drop_first: bool = True) -> TransformArtifacts:
    """Ajusta escaladores, encoders y discretizadores solo en train."""
    fitted_scaling = fit_scaling(train_df, scaling_plan)
    onehot_cols = [c for c in onehot_cols if c in train_df.columns]
    onehot = fit_onehot(train_df, onehot_cols, drop_first=drop_first) if onehot_cols else None
    disc_cols = discretization_spec.get("columns", [])
    disc_cols = [c for c in disc_cols if c in train_df.columns]
    discretizers = fit_discretizers(
        train_df,
        disc_cols,
        n_bins=discretization_spec.get("n_bins", 5),
        strategy=discretization_spec.get("strategy", "quantile"),
    )
    return TransformArtifacts(
        scaling=fitted_scaling,
        onehot_columns=onehot_cols,
        onehot=onehot,
        discretizers=discretizers,
        discretization_columns=disc_cols,
        discretization_spec=discretization_spec,
        binary_columns=[c for c in binary_cols if c in train_df.columns],
        presence_columns=[c for c in presence_cols if c in train_df.columns],
    )


def assemble_matrix(df: pd.DataFrame, artifacts: TransformArtifacts) -> pd.DataFrame:
    """Transforma un DataFrame con artefactos ya ajustados y ensambla X."""
    pieces = [transform_scaling(artifacts.scaling, df)]
    if artifacts.onehot_columns and artifacts.onehot is not None:
        pieces.append(transform_onehot(artifacts.onehot, df, artifacts.onehot_columns))
    if artifacts.binary_columns:
        pieces.append(df[artifacts.binary_columns].astype(int).copy())
    if artifacts.discretization_columns:
        disc_report_cols = artifacts.discretization_spec.get("columns", [])
        bins = transform_discretizers(
            artifacts.discretizers,
            df,
            labels=artifacts.discretization_spec.get("labels", {}),
        )
        bin_cols = [f"{c}_bin" for c in artifacts.discretization_columns]
        pieces.append(bins[bin_cols])
    if artifacts.presence_columns:
        pieces.append(df[artifacts.presence_columns].astype(int).copy())
    result = pd.concat(pieces, axis=1)
    result = result.loc[:, ~result.columns.duplicated()]
    artifacts.feature_order = list(result.columns)
    return result


def fit_transform_train_test(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    scaling_plan: Dict[str, str],
    onehot_cols: List[str],
    discretization_spec: Dict[str, object],
    binary_cols: List[str],
    presence_cols: List[str],
    drop_first: bool = True,
) -> Tuple[pd.DataFrame, pd.DataFrame, TransformArtifacts]:
    """Ajusta solo en train y transforma ambos conjuntos."""
    artifacts = fit_artifacts(
        train_df,
        scaling_plan=scaling_plan,
        onehot_cols=onehot_cols,
        discretization_spec=discretization_spec,
        binary_cols=binary_cols,
        presence_cols=presence_cols,
        drop_first=drop_first,
    )
    X_train = assemble_matrix(train_df, artifacts)
    X_test = assemble_matrix(test_df, artifacts)
    # Alinear columnas de test a las de train (one-hot puede variar).
    X_test = X_test.reindex(columns=X_train.columns, fill_value=0)
    return X_train, X_test, artifacts
