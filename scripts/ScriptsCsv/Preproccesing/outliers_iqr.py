"""
IQR-based outlier detection and winsorization module.

STRICT RULES:
- ONLY IQR method (Q1 - 1.5*IQR, Q3 + 1.5*IQR), NO z-score
- WINSORIZATION with clip(), NEVER row deletion
- Compute bounds BEFORE imputation
- df_winsor = df.copy(), keep pre and post for comparison
- Many exclusions, ask for confirmation before applying
"""

from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

from .config import PipelineConfig, DEFAULT_CONFIG
from .utils import get_numeric_columns, is_binary_series, is_one_hot_or_dummy


class IQROutlierHandler:
    """Handles IQR-based winsorization."""
    
    def __init__(self, config: PipelineConfig = DEFAULT_CONFIG):
        self.config = config
        self.bounds_info = {}
        self.decision_log = []
    
    def identify_winsorization_candidates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Identify columns that CAN be winsorized (with reasoning).
        Apply all exclusions, ask for confirmation.
        
        Args:
            df: DataFrame
            
        Returns:
            Candidates report
        """
        print("=" * 80)
        print("IQR WINSORIZATION - CANDIDATE IDENTIFICATION")
        print("=" * 80)
        print(f"[FACTOR] IQR factor = {self.config.iqr_factor}")
        print("[METHOD] Winsorization with clip() - NO row deletion")
        print("[TIMING] Bounds will be computed BEFORE imputation")
        
        numeric_cols = get_numeric_columns(df)
        candidates = []
        excluded = []
        
        print(f"\n[NUMERIC COLUMNS FOUND] {len(numeric_cols)}")
        
        for col in numeric_cols:
            series = df[col]
            reasons_exclude = []
            
            # Exclude by name
            if col in self.config.exclude_from_winsorization:
                reasons_exclude.append(f'In exclude list')
            
            # Exclude date/quarter columns
            if col in self.config.date_quarter_cols:
                reasons_exclude.append('Date/quarter column - never winsorize')
            
            # Exclude binary/flags
            if is_binary_series(series):
                reasons_exclude.append('Binary/flag column')
            
            # Exclude one-hot/dummy
            if is_one_hot_or_dummy(df, col):
                reasons_exclude.append('One-hot/dummy column')
            
            # Exclude if IQR == 0
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            if iqr == 0 or pd.isna(iqr):
                reasons_exclude.append(f'IQR == 0 (would collapse variable)')
            
            # Exclude if mostly zeros/ones pattern
            if series.dropna().nunique() <= 2:
                if not reasons_exclude:
                    reasons_exclude.append('Low cardinality (<=2)')
            
            if reasons_exclude:
                excluded.append({
                    'column': col,
                    'reasons': reasons_exclude,
                    'iqr': float(iqr) if not pd.isna(iqr) else None
                })
            else:
                # Calculate preliminary bounds
                lower_bound = q1 - self.config.iqr_factor * iqr
                upper_bound = q3 + self.config.iqr_factor * iqr
                
                outliers_lower = (series < lower_bound).sum()
                outliers_upper = (series > upper_bound).sum()
                outliers_total = outliers_lower + outliers_upper
                
                candidates.append({
                    'column': col,
                    'q1': float(q1),
                    'q3': float(q3),
                    'iqr': float(iqr),
                    'lower_bound': float(lower_bound),
                    'upper_bound': float(upper_bound),
                    'outliers_lower': int(outliers_lower),
                    'outliers_upper': int(outliers_upper),
                    'outliers_total': int(outliers_total),
                    'outliers_percent': float(outliers_total / len(series.dropna()) * 100) if len(series.dropna()) > 0 else 0
                })
        
        print(f"\n[EXCLUDED] {len(excluded)} columns (will NOT be winsorized)")
        for ex in excluded:
            print(f"  - {ex['column']}: {', '.join(ex['reasons'])}")
        
        print(f"\n[CANDIDATES FOR WINSORIZATION] {len(candidates)} columns")
        if candidates:
            candidates_df = pd.DataFrame(candidates)
            print(candidates_df.to_string())
        
        print("\n" + "=" * 80)
        print("[ACTION REQUIRED] Review candidates and CONFIRM the final list")
        print("[NOTE] Bounds computed on current data (before imputation)")
        print("=" * 80)
        
        return {
            'candidates': candidates,
            'excluded': excluded,
            'candidates_df': pd.DataFrame(candidates) if candidates else pd.DataFrame(),
            'excluded_df': pd.DataFrame(excluded) if excluded else pd.DataFrame()
        }
    
    def winsorize(self, df: pd.DataFrame, columns_to_winsorize: List[str],
                  approved: bool = False) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Apply winsorization using IQR method.
        ONLY if approved. Computes bounds BEFORE imputation as per rules.
        
        Args:
            df: DataFrame (pre-imputation state for bounds calculation)
            columns_to_winsorize: Approved columns
            approved: User approval required
            
        Returns:
            Tuple of (df_winsor, report)
        """
        if not approved:
            print("[SKIPPED] Winsorization not approved")
            print("[NOTE] Must approve final list of columns before applying")
            return df.copy(), {'applied': False}
        
        if not columns_to_winsorize:
            print("[SKIPPED] No columns to winsorize")
            return df.copy(), {'applied': False}
        
        print("=" * 80)
        print("APPLYING IQR WINSORIZATION")
        print("=" * 80)
        print("[METHOD] clip(lower_bound, upper_bound) - winsorization")
        print("[BOUNDS] Computed BEFORE imputation")
        
        df_winsor = df.copy()
        report = {
            'applied': True,
            'columns': [],
            'details': {}
        }
        
        for col in columns_to_winsorize:
            if col not in df_winsor.columns:
                print(f"[WARNING] {col} not found, skipping")
                continue
            
            series = df_winsor[col]
            
            # Double-check exclusions
            if col in self.config.date_quarter_cols:
                print(f"[SKIPPED] {col} - date/quarter column (never winsorize)")
                continue
            if col in self.config.exclude_from_winsorization:
                print(f"[SKIPPED] {col} - in exclude list")
                continue
            if is_binary_series(series):
                print(f"[SKIPPED] {col} - binary/flag")
                continue
            if is_one_hot_or_dummy(df_winsor, col):
                print(f"[SKIPPED] {col} - one-hot/dummy")
                continue
            
            # Compute bounds BEFORE imputation (on current data)
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            
            if iqr == 0 or pd.isna(iqr):
                print(f"[SKIPPED] {col} - IQR == 0")
                continue
            
            lower_bound = q1 - self.config.iqr_factor * iqr
            upper_bound = q3 + self.config.iqr_factor * iqr
            
            # Count before
            outliers_lower_before = (series < lower_bound).sum()
            outliers_upper_before = (series > upper_bound).sum()
            clipped_lower = outliers_lower_before
            clipped_upper = outliers_upper_before
            
            # Apply winsorization with clip
            df_winsor[col] = series.clip(lower=lower_bound, upper=upper_bound)
            
            self.bounds_info[col] = {
                'q1': float(q1),
                'q3': float(q3),
                'iqr': float(iqr),
                'lower_bound': float(lower_bound),
                'upper_bound': float(upper_bound),
                'clipped_lower': int(clipped_lower),
                'clipped_upper': int(clipped_upper),
                'total_clipped': int(clipped_lower + clipped_upper)
            }
            
            report['columns'].append(col)
            report['details'][col] = self.bounds_info[col]
            
            print(f"\n[WINSORIZED] {col}")
            print(f"  Bounds: [{lower_bound:.4f}, {upper_bound:.4f}]")
            print(f"  Clipped: lower={clipped_lower}, upper={clipped_upper} (total={clipped_lower+clipped_upper})")
            
            self.decision_log.append({
                'column': col,
                'issue': 'outliers',
                'method': f'IQR_winsorization_clip(factor={self.config.iqr_factor})',
                'justification': f'Outliers clipped to IQR bounds [Q1-1.5*IQR, Q3+1.5*IQR] computed before imputation',
                'values_affected': int(clipped_lower + clipped_upper)
            })
        
        print("\n" + "=" * 80)
        print("WINSORIZATION COMPLETE")
        print("=" * 80)
        
        return df_winsor, report
    
    def compare_before_after(self, df_before: pd.DataFrame, df_after: pd.DataFrame, 
                            columns: List[str]) -> pd.DataFrame:
        """
        Compare before and after winsorization.
        
        Args:
            df_before: Pre-winsorization dataframe
            df_after: Post-winsorization dataframe
            columns: Columns to compare
            
        Returns:
            Comparison DataFrame
        """
        print("=" * 80)
        print("BEFORE/AFTER WINSORIZATION COMPARISON")
        print("=" * 80)
        
        comparison = []
        for col in columns:
            if col not in df_before.columns or col not in df_after.columns:
                continue
            
            desc_before = df_before[col].describe()
            desc_after = df_after[col].describe()
            
            comparison.append({
                'column': col,
                'min_before': desc_before['min'],
                'min_after': desc_after['min'],
                'max_before': desc_before['max'],
                'max_after': desc_after['max'],
                'mean_before': desc_before['mean'],
                'mean_after': desc_after['mean'],
                'std_before': desc_before['std'],
                'std_after': desc_after['std'],
                'bounds': self.bounds_info.get(col, {})
            })
        
        comp_df = pd.DataFrame(comparison)
        print(comp_df.to_string())
        print("=" * 80)
        
        return comp_df
    
    def get_decision_log(self) -> pd.DataFrame:
        """Get decision log as DataFrame."""
        return pd.DataFrame(self.decision_log)
