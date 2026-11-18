"""
Utility functions for data preprocessing.

Shared helpers for accent removal, safe operations, etc.
"""

import unicodedata
import re
from typing import Any, List, Set
import numpy as np
import pandas as pd


def strip_accents(text: str) -> str:
    """
    Remove accents and diacritics from text.
    
    Args:
        text: Input string
        
    Returns:
        String without accents
    """
    if not isinstance(text, str):
        return text
    try:
        # Normalize and remove combining characters
        normalized = unicodedata.normalize('NFKD', text)
        return ''.join(c for c in normalized if not unicodedata.combining(c))
    except Exception:
        return text


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text (strip and collapse multiple spaces).
    
    Args:
        text: Input string
        
    Returns:
        Normalized string
    """
    if not isinstance(text, str):
        return text
    # Replace multiple whitespace with single space and strip
    return re.sub(r'\s+', ' ', text).strip()


def is_binary_series(series: pd.Series) -> bool:
    """
    Check if a series contains only binary values (0/1, True/False, '0'/'1').
    
    Args:
        series: Pandas series to check
        
    Returns:
        True if series is binary
    """
    if series.empty:
        return False
    
    # Drop NaN for checking
    unique_vals = series.dropna().unique()
    if len(unique_vals) == 0:
        return True  # All NaN, treat carefully
    
    # Check for common binary representations
    binary_sets = [
        {0, 1},
        {True, False},
        {'0', '1'},
        {'true', 'false'},
        {'True', 'False'},
        {'yes', 'no'},
        {'Yes', 'No'},
        {'Y', 'N'},
    ]
    
    unique_set = set(unique_vals)
    for bs in binary_sets:
        if unique_set.issubset(bs) and len(unique_set) <= 2:
            return True
    
    # Check numeric binary
    try:
        numeric_vals = pd.to_numeric(unique_vals, errors='coerce')
        if not pd.isna(numeric_vals).any():
            unique_numeric = set(numeric_vals)
            if unique_numeric.issubset({0, 1}):
                return True
    except Exception:
        pass
    
    return False


def is_likely_id_or_code(series: pd.Series, col_name: str = "") -> bool:
    """
    Detect if a column is likely an ID, code, or identifier.
    
    Args:
        series: Pandas series to check
        col_name: Column name for pattern matching
        
    Returns:
        True if likely ID/code
    """
    col_lower = col_name.lower()
    
    # Check column name patterns
    id_patterns = ['id', 'code', 'key', 'numero', 'número', 'ref']
    if any(pattern in col_lower for pattern in id_patterns):
        # But be careful - some might be categorical
        pass
    
    # Check if it's mostly unique
    if len(series) > 0:
        unique_ratio = series.nunique(dropna=False) / len(series)
        # If almost all unique and not binary, likely ID
        if unique_ratio > 0.95 and not is_binary_series(series):
            return True
    
    return False


def is_one_hot_or_dummy(df: pd.DataFrame, col_name: str) -> bool:
    """
    Check if column appears to be one-hot/dummy encoded.
    
    Args:
        df: DataFrame
        col_name: Column name
        
    Returns:
        True if likely one-hot/dummy
    """
    series = df[col_name]
    
    # Must be binary
    if not is_binary_series(series):
        return False
    
    # Check naming patterns
    col_lower = col_name.lower()
    dummy_patterns = ['_', 'dummy', 'oh_', 'onehot']
    if any(pattern in col_lower for pattern in dummy_patterns):
        return True
    
    # Check if there are multiple columns with similar prefix
    # This is a heuristic
    if '_' in col_name:
        prefix = col_name.rsplit('_', 1)[0]
        similar_cols = [c for c in df.columns if c.startswith(prefix + '_')]
        if len(similar_cols) >= 2:
            return True
    
    return False


def get_numeric_columns(df: pd.DataFrame) -> List[str]:
    """
    Get list of numeric columns.
    
    Args:
        df: DataFrame
        
    Returns:
        List of numeric column names
    """
    return df.select_dtypes(include=[np.number]).columns.tolist()


def get_categorical_columns(df: pd.DataFrame) -> List[str]:
    """
    Get list of categorical/object columns.
    
    Args:
        df: DataFrame
        
    Returns:
        List of categorical column names
    """
    return df.select_dtypes(include=['object', 'category']).columns.tolist()


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format value as percentage string."""
    return f"{value * 100:.{decimals}f}%"


def set_random_seed(seed: int = 42):
    """Set random seeds for reproducibility."""
    np.random.seed(seed)
    try:
        import random
        random.seed(seed)
    except Exception:
        pass
