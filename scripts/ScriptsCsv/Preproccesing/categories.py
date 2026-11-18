"""
Categorical inconsistency handling module.

Normalizes categories: strip, lowercase, accents, whitespace.
Only applies changes after confirmation if inconsistencies found.
"""

from typing import Dict, Any, List, Tuple
import pandas as pd

from .config import PipelineConfig, DEFAULT_CONFIG
from .utils import strip_accents, normalize_whitespace


class CategoryCleaner:
    """Handles categorical normalization."""
    
    def __init__(self, config: PipelineConfig = DEFAULT_CONFIG):
        self.config = config
        self.decision_log = []
    
    def analyze_categories(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze categorical columns for inconsistencies.
        Reports findings but doesn't change anything.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Analysis report
        """
        print("=" * 80)
        print("CATEGORICAL ANALYSIS")
        print("=" * 80)
        print("[NOTE] CSV is supposedly already normalized. Checking for inconsistencies...")
        
        cat_cols = df.select_dtypes(include=['object']).columns.tolist()
        findings = []
        
        for col in cat_cols:
            series = df[col]
            unique_vals = series.dropna().unique()
            unique_count = len(unique_vals)
            
            # Check for issues
            issues = []
            
            # Check for leading/trailing spaces
            has_spaces = any(isinstance(v, str) and (v != v.strip()) for v in unique_vals)
            if has_spaces:
                issues.append('leading/trailing_spaces')
            
            # Check for mixed case
            str_vals = [v for v in unique_vals if isinstance(v, str)]
            if str_vals:
                lower_vals = [v.lower() for v in str_vals]
                if len(set(lower_vals)) < len(str_vals):
                    issues.append('mixed_case')
            
            # Check for accents
            has_accents = any(isinstance(v, str) and strip_accents(v) != v for v in str_vals)
            if has_accents:
                issues.append('accents')
            
            # Check for multiple spaces
            has_multi_space = any(isinstance(v, str) and '  ' in v for v in str_vals)
            if has_multi_space:
                issues.append('multiple_spaces')
            
            if issues:
                findings.append({
                    'column': col,
                    'unique_count': unique_count,
                    'issues': issues,
                    'sample_values': list(unique_vals[:10])
                })
                print(f"\n[INCONSISTENCY FOUND - {col}]")
                print(f"  Unique values: {unique_count}")
                print(f"  Issues: {issues}")
                print(f"  Sample: {list(unique_vals[:10])}")
            else:
                print(f"\n[OK - {col}] {unique_count} unique values, no obvious inconsistencies")
        
        if not findings:
            print(f"\n[ALL CLEAR] No categorical inconsistencies detected")
        else:
            print(f"\n[SUMMARY] {len(findings)} columns with potential inconsistencies")
            print("[ACTION] Will ask for confirmation before applying normalization")
        
        print("=" * 80)
        
        return {
            'findings': findings,
            'cat_columns': cat_cols,
            'needs_normalization': len(findings) > 0
        }
    
    def normalize_categories(self, df: pd.DataFrame, columns: List[str] = None,
                            approved: bool = False, apply_case: str = 'lower',
                            remove_accents: bool = True) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Normalize categorical columns.
        Only applies if approved.
        
        Args:
            df: DataFrame
            columns: Columns to normalize (None = all object columns)
            approved: User approval required
            apply_case: 'lower', 'upper', 'title', or None
            remove_accents: Remove accents
            
        Returns:
            Tuple of (cleaned_df, report)
        """
        if not approved:
            print("[SKIPPED] Category normalization not approved")
            return df.copy(), {'applied': False}
        
        df_clean = df.copy()
        
        if columns is None:
            columns = df_clean.select_dtypes(include=['object']).columns.tolist()
            # Exclude date/quarter columns
            columns = [c for c in columns if c not in self.config.date_quarter_cols]
        
        print("=" * 80)
        print("NORMALIZING CATEGORIES")
        print("=" * 80)
        
        report = {'applied': True, 'columns': [], 'changes': {}}
        
        for col in columns:
            if col not in df_clean.columns:
                continue
            
            series = df_clean[col]
            if series.dtype != 'object':
                continue
            
            original_unique = series.dropna().nunique()
            changes_made = []
            
            # Apply normalization
            def normalize_val(x):
                if pd.isna(x):
                    return x
                if not isinstance(x, str):
                    return x
                val = x
                val = normalize_whitespace(val)
                if remove_accents:
                    val = strip_accents(val)
                if apply_case == 'lower':
                    val = val.lower()
                elif apply_case == 'upper':
                    val = val.upper()
                elif apply_case == 'title':
                    val = val.title()
                return val
            
            df_clean[col] = series.apply(normalize_val)
            
            new_unique = df_clean[col].dropna().nunique()
            
            if new_unique < original_unique:
                changes_made.append(f'unique reduced: {original_unique} -> {new_unique}')
            if changes_made or True:  # Log all normalized
                changes_made.append('strip, whitespace, accents, case normalization')
            
            report['columns'].append(col)
            report['changes'][col] = changes_made
            
            print(f"[NORMALIZED] {col}: {', '.join(changes_made)}")
            
            self.decision_log.append({
                'column': col,
                'issue': 'categorical_inconsistency',
                'method': f'normalize(strip, accents, whitespace, case={apply_case})',
                'justification': 'Normalized categorical values for consistency',
                'values_affected': int(len(series) - series.isna().sum())
            })
        
        print("=" * 80)
        return df_clean, report
    
    def get_decision_log(self) -> pd.DataFrame:
        """Get decision log as DataFrame."""
        return pd.DataFrame(self.decision_log)
