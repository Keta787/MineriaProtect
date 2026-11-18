"""
Validation module for the cleaned dataset.

Validates: same row count as before winsorizing, nulls == 0, all values within IQR bounds.
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np

from .config import PipelineConfig, DEFAULT_CONFIG


class DataValidator:
    """Validates the cleaned dataset."""
    
    def __init__(self, config: PipelineConfig = DEFAULT_CONFIG):
        self.config = config
    
    def validate_final(self, df_final: pd.DataFrame, df_before_winsor: pd.DataFrame = None,
                      winsor_bounds: Dict = None) -> Dict[str, Any]:
        """
        Validate final cleaned dataset.
        
        Args:
            df_final: Final dataframe (winsorized)
            df_before_winsor: Dataframe before winsorization
            winsor_bounds: Bounds used in winsorization
            
        Returns:
            Validation results
        """
        print("=" * 80)
        print("FINAL VALIDATION")
        print("=" * 80)
        
        results = {
            'passed': True,
            'checks': {}
        }
        
        # Check 1: Row count
        if df_before_winsor is not None:
            rows_before = len(df_before_winsor)
            rows_final = len(df_final)
            rows_match = rows_before == rows_final
            results['checks']['row_count'] = {
                'passed': rows_match,
                'before': rows_before,
                'after': rows_final,
                'message': f'Rows preserved: {rows_before} == {rows_final}' if rows_match else f'ROW COUNT MISMATCH: {rows_before} != {rows_final}'
            }
            print(f"\n[CHECK 1 - ROW COUNT] {'PASSED' if rows_match else 'FAILED'}: {rows_before} -> {rows_final}")
            if not rows_match:
                results['passed'] = False
        else:
            results['checks']['row_count'] = {'passed': None, 'message': 'Not compared (no before_winsor provided)'}
            print(f"\n[CHECK 1 - ROW COUNT] SKIPPED (no reference)")
        
        # Check 2: Nulls
        null_count_total = df_final.isna().sum().sum()
        nulls_zero = null_count_total == 0
        results['checks']['nulls'] = {
            'passed': nulls_zero,
            'count': int(null_count_total),
            'message': 'No nulls' if nulls_zero else f'{null_count_total} nulls remaining'
        }
        print(f"[CHECK 2 - NULLS] {'PASSED' if nulls_zero else 'FAILED'}: {null_count_total} nulls")
        if not nulls_zero:
            results['passed'] = False
            # Show columns with nulls
            null_cols = df_final.isna().sum()
            null_cols = null_cols[null_cols > 0]
            print(f"  Columns with nulls: {null_cols.to_dict()}")
        
        # Check 3: Values within IQR bounds for winsorized columns
        if winsor_bounds:
            all_within_bounds = True
            bounds_check = {}
            for col, bounds in winsor_bounds.items():
                if col not in df_final.columns:
                    continue
                lower = bounds['lower_bound']
                upper = bounds['upper_bound']
                series = df_final[col]
                below = (series < lower).sum()
                above = (series > upper).sum()
                within = below == 0 and above == 0
                bounds_check[col] = {
                    'passed': within,
                    'below_bound': int(below),
                    'above_bound': int(above),
                    'bounds': [lower, upper]
                }
                if not within:
                    all_within_bounds = False
                    print(f"[CHECK 3 - BOUNDS {col}] FAILED: below={below}, above={above}")
                else:
                    print(f"[CHECK 3 - BOUNDS {col}] PASSED: all within [{lower:.4f}, {upper:.4f}]")
            results['checks']['bounds'] = bounds_check
            if not all_within_bounds:
                results['passed'] = False
        else:
            results['checks']['bounds'] = {'passed': None, 'message': 'No winsorization bounds to check'}
            print(f"[CHECK 3 - BOUNDS] SKIPPED (no bounds info)")
        
        # Check 4: Basic sanity
        print(f"\n[CHECK 4 - SANITY]")
        print(f"  Shape: {df_final.shape}")
        print(f"  Duplicates (exact): {df_final.duplicated().sum()}")
        results['checks']['sanity'] = {
            'shape': df_final.shape,
            'exact_duplicates': int(df_final.duplicated().sum())
        }
        
        print("\n" + "=" * 80)
        if results['passed']:
            print("VALIDATION: ALL CHECKS PASSED")
        else:
            print("VALIDATION: SOME CHECKS FAILED - REVIEW ABOVE")
        print("=" * 80)
        
        return results
    
    def generate_summary(self, df_original: pd.DataFrame, df_final: pd.DataFrame) -> pd.DataFrame:
        """
        Generate before/after summary.
        
        Args:
            df_original: Original dataframe
            df_final: Final dataframe
            
        Returns:
            Summary DataFrame
        """
        print("=" * 80)
        print("BEFORE/AFTER SUMMARY")
        print("=" * 80)
        
        summary = {
            'Metric': [
                'Rows',
                'Columns',
                'Nulls (total)',
                'Exact duplicates',
                'Numeric columns',
                'Categorical columns'
            ],
            'Before': [
                len(df_original),
                len(df_original.columns),
                int(df_original.isna().sum().sum()),
                int(df_original.duplicated().sum()),
                len(df_original.select_dtypes(include=[np.number]).columns),
                len(df_original.select_dtypes(include=['object']).columns)
            ],
            'After': [
                len(df_final),
                len(df_final.columns),
                int(df_final.isna().sum().sum()),
                int(df_final.duplicated().sum()),
                len(df_final.select_dtypes(include=[np.number]).columns),
                len(df_final.select_dtypes(include=['object']).columns)
            ]
        }
        
        summary_df = pd.DataFrame(summary)
        print(summary_df.to_string(index=False))
        print("=" * 80)
        
        return summary_df
