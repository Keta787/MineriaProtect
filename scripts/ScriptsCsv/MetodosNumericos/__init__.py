"""JobPath Numerical Methods package (Least-Squares Linear Regression & Lagrange Interpolation)."""

from .config import NumericalMethodsConfig, default_config, resolve_project_root
from .lagrange import (
    LagrangeDiagnostics,
    chebyshev_nodes,
    diagnose_lagrange,
    expand_monomial_coefficients,
    inverse_lagrange_eval,
    lagrange_basis,
    lagrange_eval,
    lagrange_weights_matrix,
    piecewise_lagrange_eval,
    validate_distinct_nodes,
)
from .ols import (
    OLSResult,
    build_summation_and_residual_table,
    classify_r2_quality,
    predict_ols,
    regresion_lineal,
    verify_affine_scaling_invariance,
)
from .pipeline import NumericalMethodsPipelineResult, run_all_8_ideas

__all__ = [
    "NumericalMethodsConfig",
    "default_config",
    "resolve_project_root",
    "OLSResult",
    "regresion_lineal",
    "predict_ols",
    "build_summation_and_residual_table",
    "classify_r2_quality",
    "verify_affine_scaling_invariance",
    "LagrangeDiagnostics",
    "validate_distinct_nodes",
    "lagrange_basis",
    "lagrange_weights_matrix",
    "lagrange_eval",
    "expand_monomial_coefficients",
    "diagnose_lagrange",
    "chebyshev_nodes",
    "piecewise_lagrange_eval",
    "inverse_lagrange_eval",
]
