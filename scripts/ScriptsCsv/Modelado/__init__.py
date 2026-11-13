"""SOLID modeling and evaluation package for CRISP-DM Phase 4 (JobPath)."""

from .config import (
    ALL_DENSE_FEATURES_IN_X,
    COLLINEAR_REDUNDANT_FEATURES,
    LEAKAGE_FEATURES_IN_X,
    ModelingConfig,
    VERSION_CON,
    VERSION_LABELS,
    VERSION_SIN,
    resolve_project_root,
)
from .dataset_builder import (
    ModelingDatasetBuilder,
    PreparedPartition,
    VersionModelingData,
)
from .evaluation import CurveData, EvaluationBundle, PersonGroupedEvaluator
from .pipeline import ModelingPipeline, ModelingPipelineResult
from .plots import ModelingPlotter

__all__ = [
    "ALL_DENSE_FEATURES_IN_X",
    "COLLINEAR_REDUNDANT_FEATURES",
    "LEAKAGE_FEATURES_IN_X",
    "ModelingConfig",
    "VERSION_CON",
    "VERSION_LABELS",
    "VERSION_SIN",
    "resolve_project_root",
    "ModelingDatasetBuilder",
    "PreparedPartition",
    "VersionModelingData",
    "CurveData",
    "EvaluationBundle",
    "PersonGroupedEvaluator",
    "ModelingPipeline",
    "ModelingPipelineResult",
    "ModelingPlotter",
]

