"""
Preprocessing package for the JobPath data cleaning pipeline (CRISP-DM Phase 3).

Provides SOLID modular components for diagnosis, duplicate verification,
categorical normalization, MCAR/MAR/MNAR missing-value analysis, IQR
winsorization, row-count funnel tracking, and final validation.
"""

__version__ = "2.0.0"

__all__ = [
    "config",
    "utils",
    "io",
    "diagnosis",
    "duplicates",
    "categories",
    "missing",
    "imputation",
    "outliers_iqr",
    "validation",
    "funnel",
    "pipeline",
]
