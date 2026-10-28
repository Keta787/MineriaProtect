"""
Dataset diagnosis module.

Performs full analysis: shape, dtypes, nulls, duplicates, describe, cardinality, odd values, impossible values.
"""

from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

from .config import PipelineConfig, DEFAULT_CONFIG
from .utils import get_numeric_columns, get_categorical_columns


class DataDiagnoser:
    """Performs comprehensive dataset diagnosis."""
    
    def __init__(self, config: PipelineConfig = DEFAULT_CONFIG):
        self.config = config
    
    def diagnose(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Perform full diagnosis of the dataset.
        
        Args:
            df: DataFrame to diagnose
            
        Returns:
            Dictionary with all diagnosis results
        """
        results = {}
        
        print("=" * 80)
        print("DATASET DIAGNOSIS")
        print("=" * 80)
        
        # Basic info
        results['shape'] = df.shape
        print(f"\n[SHAPE] Rows: {df.shape[0]}, Columns: {df.shape[1]}")
        
        # Data types
        results['dtypes'] = df.dtypes
        print(f"\n[DTYPES]")
        print(df.dtypes.value_counts())
        
        # Nulls
        null_counts = df.isna().sum()
        null_percent = (null_counts / len(df) * 100).round(2)
        null_df = pd.DataFrame({
            'null_count': null_counts,
            'null_percent': null_percent
        }).sort_values('null_count', ascending=False)
        null_df = null_df[null_df['null_count'] > 0]
        
        results['nulls'] = null_df
        print(f"\n[NULLS] Columns with nulls: {len(null_df)}")
        if len(null_df) > 0:
            print(null_df.to_string())
        else:
            print("No nulls found.")
        
        # Duplicates
        exact_duplicates = df.duplicated().sum()
        results['exact_duplicates'] = int(exact_duplicates)
        print(f"\n[DUPLICATES - EXACT] {exact_duplicates} rows")
        
        # Duplicates by unique key
        if self.config.unique_key in df.columns:
            key_duplicates = df.duplicated(subset=[self.config.unique_key]).sum()
            results['key_duplicates'] = int(key_duplicates)
            print(f"[DUPLICATES - BY {self.config.unique_key}] {key_duplicates} rows")
        else:
            results['key_duplicates'] = None
            print(f"[DUPLICATES - BY {self.config.unique_key}] Key not found in dataframe")
        
        # Describe numeric
        numeric_cols = get_numeric_columns(df)
        if numeric_cols:
            results['describe_numeric'] = df[numeric_cols].describe()
            print(f"\n[DESCRIBE - NUMERIC] {len(numeric_cols)} columns")
            print(results['describe_numeric'].to_string())
        
        # Categorical cardinality
        cat_cols = get_categorical_columns(df)
        cardinality = []
        for col in cat_cols:
            card = df[col].nunique(dropna=False)
            cardinality.append({
                'column': col,
                'cardinality': card,
                'dtype': str(df[col].dtype)
            })
        results['cardinality'] = pd.DataFrame(cardinality).sort_values('cardinality', ascending=False)
        print(f"\n[CARDINALITY - CATEGORICAL] {len(cat_cols)} columns")
        if len(results['cardinality']) > 0:
            print(results['cardinality'].to_string())
        
        # Odd values check (sample)
        results['odd_values_sample'] = {}
        for col in cat_cols[:10]:  # Check first 10 categorical columns
            unique_vals = df[col].unique()
            results['odd_values_sample'][col] = unique_vals[:20]
            print(f"\n[ODD VALUES SAMPLE - {col}] {len(unique_vals)} unique")
            print(list(unique_vals[:15]))
        
        print("\n" + "=" * 80)
        print("DIAGNOSIS COMPLETE")
        print("=" * 80)
        
        return results
    
    def check_impossible_values(self, df: pd.DataFrame, rules: Dict[str, Dict] = None) -> pd.DataFrame:
        """
        Check for impossible values based on rules or heuristics.
        Always asks before applying corrections.
        
        Args:
            df: DataFrame to check
            rules: Optional dict with rules per column
            
        Returns:
            DataFrame with findings
        """
        findings = []
        numeric_cols = get_numeric_columns(df)
        
        for col in numeric_cols:
            series = df[col].dropna()
            if series.empty:
                continue
            
            # Heuristic checks
            if series.min() < 0:
                neg_count = (df[col] < 0).sum()
                findings.append({
                    'column': col,
                    'issue': 'negative_values',
                    'count': neg_count,
                    'min': series.min(),
                    'max': series.max(),
                    'note': 'Negative values detected'
                })
            
            # Very large values
            q99 = series.quantile(0.99)
            q1 = series.quantile(0.01)
            if series.max() > q99 * 10 and q99 > 0:
                outliers_count = (df[col] > q99 * 10).sum()
                findings.append({
                    'column': col,
                    'issue': 'extreme_high_values',
                    'count': outliers_count,
                    'min': series.min(),
                    'max': series.max(),
                    'q99': q99,
                    'note': 'Values extremely high vs 99th percentile'
                })
        
        findings_df = pd.DataFrame(findings)
        if not findings_df.empty:
            print("\n[POSSIBLE IMPOSSIBLE VALUES]")
            print(findings_df.to_string())
        else:
            print("\n[POSSIBLE IMPOSSIBLE VALUES] No obvious issues found by heuristics")
        
        return findings_df


def diagnose_dataframe(df: pd.DataFrame, config: PipelineConfig = DEFAULT_CONFIG) -> Dict[str, Any]:
    """Convenience function for diagnosis."""
    return DataDiagnoser(config).diagnose(df)
