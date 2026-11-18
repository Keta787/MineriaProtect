"""
Duplicate detection and handling module.

Implements the exact order specified:
1. Exact duplicates across all columns (keep='first')
2. Duplicates by unique key (Resume_id) - show side by side, ask before removing
"""

from typing import Dict, Any, Tuple
import pandas as pd

from .config import PipelineConfig, DEFAULT_CONFIG


class DuplicateHandler:
    """Handles duplicate detection and removal."""
    
    def __init__(self, config: PipelineConfig = DEFAULT_CONFIG):
        self.config = config
        self.decision_log = []
    
    def remove_exact_duplicates(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Step 1: Remove exact duplicates across all columns (keep='first').
        
        Args:
            df: Input DataFrame
            
        Returns:
            Tuple of (cleaned_df, report)
        """
        print("=" * 80)
        print("STEP 1: EXACT DUPLICATES ACROSS ALL COLUMNS")
        print("=" * 80)
        
        initial_shape = df.shape
        exact_dups_mask = df.duplicated(keep='first')
        exact_dups_count = exact_dups_mask.sum()
        
        print(f"\n[BEFORE] Shape: {initial_shape}")
        print(f"[EXACT DUPLICATES FOUND] {exact_dups_count} rows")
        
        if exact_dups_count > 0:
            print(f"[ACTION] Removing with keep='first'")
            df_clean = df.drop_duplicates(keep='first').reset_index(drop=True)
            print(f"[AFTER] Shape: {df_clean.shape}")
            print(f"[REMOVED] {exact_dups_count} rows")
            
            self.decision_log.append({
                'column': 'ALL_COLUMNS',
                'issue': 'exact_duplicates',
                'method': "drop_duplicates(keep='first')",
                'justification': 'Exact duplicates across all columns removed as per pipeline order',
                'values_affected': int(exact_dups_count)
            })
        else:
            print(f"[ACTION] None to remove")
            df_clean = df.copy()
            self.decision_log.append({
                'column': 'ALL_COLUMNS',
                'issue': 'exact_duplicates',
                'method': 'none',
                'justification': 'No exact duplicates found',
                'values_affected': 0
            })
        
        report = {
            'initial_shape': initial_shape,
            'exact_duplicates_count': int(exact_dups_count),
            'final_shape': df_clean.shape,
            'removed': int(exact_dups_count)
        }
        
        print("=" * 80)
        return df_clean, report
    
    def find_key_duplicates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Step 2: Find duplicates by unique key (Resume_id).
        DO NOT remove automatically - show side by side and ask for confirmation.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary with duplicates info
        """
        print("=" * 80)
        print(f"STEP 2: DUPLICATES BY UNIQUE KEY [{self.config.unique_key}]")
        print("=" * 80)
        
        key_col = self.config.unique_key
        
        if key_col not in df.columns:
            print(f"[ERROR] Key column '{key_col}' not found in dataframe")
            print(f"[AVAILABLE COLUMNS] {list(df.columns)}")
            return {'found': False, 'error': f'Column {key_col} not found'}
        
        # Find duplicates
        key_dups_mask = df.duplicated(subset=[key_col], keep=False)
        key_dups_count_total = key_dups_mask.sum()
        key_dups_groups = df[key_dups_mask][key_col].nunique()
        
        print(f"\n[KEY] {key_col}")
        print(f"[ROWS WITH DUPLICATE KEYS] {key_dups_count_total}")
        print(f"[NUMBER OF DUPLICATE GROUPS] {key_dups_groups}")
        
        report = {
            'found': key_dups_groups > 0,
            'key_column': key_col,
            'rows_affected': int(key_dups_count_total),
            'groups': int(key_dups_groups),
            'duplicate_df': None,
            'groups_detail': []
        }
        
        if key_dups_groups > 0:
            print(f"\n[WARNING] Duplicates found by key - DO NOT REMOVE AUTOMATICALLY")
            print(f"[ACTION REQUIRED] Review groups below and confirm before removal")
            
            # Get duplicate groups
            dup_df = df[key_dups_mask].copy()
            dup_df = dup_df.sort_values(by=[key_col])
            report['duplicate_df'] = dup_df
            
            # Analyze groups
            for key_val, group in dup_df.groupby(key_col):
                # Check if all columns same or different
                is_identical = group.drop(columns=[key_col]).duplicated().sum() == len(group) - 1
                diff_cols = []
                if not is_identical:
                    # Find columns with differences
                    for col in group.columns:
                        if col == key_col:
                            continue
                        if group[col].nunique(dropna=False) > 1:
                            diff_cols.append(col)
                
                report['groups_detail'].append({
                    'key_value': key_val,
                    'group_size': len(group),
                    'is_identical': is_identical,
                    'differing_columns': diff_cols
                })
                
                print(f"\n{'='*60}")
                print(f"GROUP: {key_col} = {key_val} ({len(group)} rows)")
                print(f"Identical across all columns: {is_identical}")
                if diff_cols:
                    print(f"Differing columns: {diff_cols}")
                print(f"{'='*60}")
                # Show the group
                print(group.to_string())
        else:
            print(f"\n[OK] No duplicates found by key {key_col}")
            self.decision_log.append({
                'column': key_col,
                'issue': 'key_duplicates',
                'method': 'none',
                'justification': f'No duplicates found by unique key {key_col}',
                'values_affected': 0
            })
        
        print("=" * 80)
        return report
    
    def remove_key_duplicates(self, df: pd.DataFrame, approved: bool = False, 
                               keep: str = 'first') -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Step 2b: Remove duplicates by key ONLY if approved.
        
        Args:
            df: Input DataFrame
            approved: Must be True from user confirmation
            keep: 'first' or 'last'
            
        Returns:
            Tuple of (cleaned_df, report)
        """
        key_col = self.config.unique_key
        
        if not approved:
            print("[SKIPPED] Key duplicates removal not approved")
            return df.copy(), {'removed': 0, 'approved': False}
        
        if key_col not in df.columns:
            return df.copy(), {'removed': 0, 'error': 'Key not found'}
        
        initial_shape = df.shape
        key_dups_mask = df.duplicated(subset=[key_col], keep=keep)
        key_dups_count = key_dups_mask.sum()
        
        print(f"[REMOVING] Duplicates by {key_col} with keep='{keep}'")
        df_clean = df.drop_duplicates(subset=[key_col], keep=keep).reset_index(drop=True)
        print(f"[REMOVED] {key_dups_count} rows. New shape: {df_clean.shape}")
        
        self.decision_log.append({
            'column': key_col,
            'issue': 'key_duplicates',
            'method': f"drop_duplicates(subset=['{key_col}'], keep='{keep}')",
            'justification': f'Removed duplicates by unique key {key_col} with user approval',
            'values_affected': int(key_dups_count)
        })
        
        return df_clean, {'removed': int(key_dups_count), 'approved': True, 'keep': keep}
    
    def get_decision_log(self) -> pd.DataFrame:
        """Get decision log as DataFrame."""
        return pd.DataFrame(self.decision_log)
