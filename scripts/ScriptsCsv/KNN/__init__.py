"""Modular SOLID package for Notebook 7.2 (K-Nearest Neighbors - JobPath)."""

from __future__ import annotations

from scripts.ScriptsCsv.NaiveBayes.pipeline import current_process_rss_mb

from .chunked_predictor import ChunkedKNNPredictor, ChunkedPredictResult
from .config import (
    ALL_DENSE_CLEAN_FEATURES,
    GUIDING_QUESTION_ES,
    ISCO_MAJOR_DUMMY_COLS,
    ISCO_MAJOR_LABELS_ES,
    KNNConfig,
    MODEL_KNN_D,
    MODEL_KNN_G,
    MODEL_KNN_W,
    MODEL_LABELS_ES,
    MODEL_ORDER,
    VERSION_CON,
    VERSION_SIN,
    resolve_project_root,
)
from .evaluation import (
    KNNEvaluator,
    KNNTestEvaluationBundle,
    KNNThresholdBundle,
    KNNTuningBundle,
    PersonSubsampler,
    proba_from_kneighbors,
)
from .feature_blocks import (
    AuditedStandardBinaryScaler,
    DenseScaleStrategy,
    KNNFeatureBuilder,
    KNNPartitionBlocks,
    KNNVersionBundle,
    RawDensePassthroughScaler,
    TukeyWinsorizedStandardScaler,
)
from .geometry import GeometryAnalyzer, GeometryExperimentBundle
from .models import (
    KNNModelSpec,
    ManualKNNDemoResult,
    ManualKNNExplainer,
    VERIFIED_KNN_INIT_PARAMS,
    build_knn_classifier,
    build_knn_d,
    build_knn_g,
    build_knn_w,
)
from .neighbors_explainer import CaseExplanationBundle, NeighborsExplainer
from .patterns import KNNPatternAnalyzer, KNNPatternsBundle
from .pilot_benchmark import (
    CostCurveBundle,
    FullRunProjectionBundle,
    PilotBenchmarkRunner,
    PilotSelectionBundle,
)
from .pipeline import KNNPipeline
from .plots import KNNPlotter
from .revision_checks import (
    CacheIntegrityBundle,
    CacheIntegrityVerifier,
    ExactOccupationPrefilterKNN,
    F1PurityPrefilterBundle,
    F3SizeControlBundle,
    F5CostRangeBundle,
    PrefilterPredictionResult,
    RevisionAnalysisRunner,
    paired_bootstrap_person_multi_alpha,
    paired_bootstrap_practical_counts,
    tie_aware_equal_alert_weights,
)
from .self_tests import run_all_knn_unit_tests, run_stage1_self_tests, run_stage2_self_tests
from .version_comparison import ScaleOutlierSensitivityBundle, VersionSensitivityAnalyzer

__all__ = [
    "ALL_DENSE_CLEAN_FEATURES",
    "AuditedStandardBinaryScaler",
    "CacheIntegrityBundle",
    "CacheIntegrityVerifier",
    "CaseExplanationBundle",
    "ChunkedKNNPredictor",
    "ChunkedPredictResult",
    "CostCurveBundle",
    "DenseScaleStrategy",
    "ExactOccupationPrefilterKNN",
    "F1PurityPrefilterBundle",
    "F3SizeControlBundle",
    "F5CostRangeBundle",
    "FullRunProjectionBundle",
    "GUIDING_QUESTION_ES",
    "GeometryAnalyzer",
    "GeometryExperimentBundle",
    "ISCO_MAJOR_DUMMY_COLS",
    "ISCO_MAJOR_LABELS_ES",
    "KNNConfig",
    "KNNEvaluator",
    "KNNFeatureBuilder",
    "KNNModelSpec",
    "KNNPartitionBlocks",
    "KNNPatternAnalyzer",
    "KNNPatternsBundle",
    "KNNPipeline",
    "KNNPlotter",
    "KNNTestEvaluationBundle",
    "KNNThresholdBundle",
    "KNNTuningBundle",
    "KNNVersionBundle",
    "MODEL_KNN_D",
    "MODEL_KNN_G",
    "MODEL_KNN_W",
    "MODEL_LABELS_ES",
    "MODEL_ORDER",
    "ManualKNNDemoResult",
    "ManualKNNExplainer",
    "NeighborsExplainer",
    "PersonSubsampler",
    "PilotBenchmarkRunner",
    "PilotSelectionBundle",
    "PrefilterPredictionResult",
    "RawDensePassthroughScaler",
    "RevisionAnalysisRunner",
    "ScaleOutlierSensitivityBundle",
    "TukeyWinsorizedStandardScaler",
    "VERIFIED_KNN_INIT_PARAMS",
    "VERSION_CON",
    "VERSION_SIN",
    "VersionSensitivityAnalyzer",
    "build_knn_classifier",
    "build_knn_d",
    "build_knn_g",
    "build_knn_w",
    "current_process_rss_mb",
    "paired_bootstrap_person_multi_alpha",
    "paired_bootstrap_practical_counts",
    "proba_from_kneighbors",
    "resolve_project_root",
    "run_all_knn_unit_tests",
    "run_stage1_self_tests",
    "run_stage2_self_tests",
    "tie_aware_equal_alert_weights",
]
