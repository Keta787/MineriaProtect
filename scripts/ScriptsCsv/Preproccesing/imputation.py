"""
Imputation module with strategy pattern.

Implements interchangeable imputers following OCP/LSP.
Only applies after explicit confirmation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
import pandas as pd
import numpy as np

from .config import PipelineConfig, DEFAULT_CONFIG


class ImputerInterface(ABC):
    """Interface for imputers (LSP compliant)."""
    
    @abstractmethod
    def fit_transform(self, df: pd.DataFrame, column: str, **kwargs) -> pd.DataFrame:
        """Fit and transform the dataframe."""
        pass
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Get imputer information."""
        pass


class MedianImputer(ImputerInterface):
    """Median imputation for numeric columns."""
    
    def __init__(self):
        self.median_value = None
        self.values_affected = 0
    
    def fit_transform(self, df: pd.DataFrame, column: str, **kwargs) -> pd.DataFrame:
        df_clean = df.copy()
        null_mask = df_clean[column].isna()
        self.values_affected = null_mask.sum()
        
        if self.values_affected > 0:
            self.median_value = df_clean[column].median()
            df_clean[column] = df_clean[column].fillna(self.median_value)
            print(f"[IMPUTE] {column} filled with median = {self.median_value}")
        
        return df_clean
    
    def get_info(self) -> Dict[str, Any]:
        return {
            'method': 'median',
            'value': self.median_value,
            'values_affected': int(self.values_affected)
        }


class MeanImputer(ImputerInterface):
    """Mean imputation for numeric columns."""
    
    def __init__(self):
        self.mean_value = None
        self.values_affected = 0
    
    def fit_transform(self, df: pd.DataFrame, column: str, **kwargs) -> pd.DataFrame:
        df_clean = df.copy()
        null_mask = df_clean[column].isna()
        self.values_affected = null_mask.sum()
        
        if self.values_affected > 0:
            self.mean_value = df_clean[column].mean()
            df_clean[column] = df_clean[column].fillna(self.mean_value)
            print(f"[IMPUTE] {column} filled with mean = {self.mean_value}")
        
        return df_clean
    
    def get_info(self) -> Dict[str, Any]:
        return {
            'method': 'mean',
            'value': self.mean_value,
            'values_affected': int(self.values_affected)
        }


class ModeImputer(ImputerInterface):
    """Mode imputation for categorical/numeric columns."""
    
    def __init__(self):
        self.mode_value = None
        self.values_affected = 0
    
    def fit_transform(self, df: pd.DataFrame, column: str, **kwargs) -> pd.DataFrame:
        df_clean = df.copy()
        null_mask = df_clean[column].isna()
        self.values_affected = null_mask.sum()
        
        if self.values_affected > 0:
            mode_series = df_clean[column].mode()
            if len(mode_series) > 0:
                self.mode_value = mode_series[0]
                df_clean[column] = df_clean[column].fillna(self.mode_value)
                print(f"[IMPUTE] {column} filled with mode = {self.mode_value}")
            else:
                print(f"[WARNING] No mode found for {column}")
        
        return df_clean
    
    def get_info(self) -> Dict[str, Any]:
        return {
            'method': 'mode',
            'value': self.mode_value,
            'values_affected': int(self.values_affected)
        }


class GroupImputer(ImputerInterface):
    """Group-based imputation."""
    
    def __init__(self):
        self.group_column = None
        self.values_affected = 0
    
    def fit_transform(self, df: pd.DataFrame, column: str, group_by: str = None, 
                      agg_func: str = 'median', **kwargs) -> pd.DataFrame:
        df_clean = df.copy()
        null_mask = df_clean[column].isna()
        self.values_affected = null_mask.sum()
        self.group_column = group_by
        
        if self.values_affected > 0 and group_by and group_by in df_clean.columns:
            if agg_func == 'median':
                group_values = df_clean.groupby(group_by)[column].transform('median')
            elif agg_func == 'mean':
                group_values = df_clean.groupby(group_by)[column].transform('mean')
            elif agg_func == 'mode':
                group_values = df_clean.groupby(group_by)[column].transform(
                    lambda x: x.mode()[0] if len(x.mode()) > 0 else x
                )
            else:
                group_values = df_clean.groupby(group_by)[column].transform('median')
            
            df_clean[column] = df_clean[column].fillna(group_values)
            # Fill remaining with overall median
            if df_clean[column].isna().sum() > 0:
                overall = df_clean[column].median() if df_clean[column].dtype in [np.number] else df_clean[column].mode()[0]
                df_clean[column] = df_clean[column].fillna(overall)
            
            print(f"[IMPUTE] {column} filled by group {group_by} with {agg_func}")
        elif self.values_affected > 0:
            print(f"[WARNING] Group imputation requested but no group_by specified, using median")
            median_imp = MedianImputer()
            df_clean = median_imp.fit_transform(df_clean, column)
            self.values_affected = median_imp.values_affected
        
        return df_clean
    
    def get_info(self) -> Dict[str, Any]:
        return {
            'method': 'group',
            'group_by': self.group_column,
            'values_affected': int(self.values_affected)
        }


class FlagImputer(ImputerInterface):
    """Create indicator column for MNAR - NO IMPUTATION."""
    
    def __init__(self):
        self.values_affected = 0
    
    def fit_transform(self, df: pd.DataFrame, column: str, **kwargs) -> pd.DataFrame:
        df_clean = df.copy()
        null_mask = df_clean[column].isna()
        self.values_affected = null_mask.sum()
        
        if self.values_affected > 0:
            indicator_col = f"{column}_missing_mnar"
            df_clean[indicator_col] = null_mask.astype(int)
            print(f"[FLAG-MNAR] Created indicator {indicator_col}, NOT imputing {column}")
            print(f"[WARNING] MNAR detected - missing values remain for {column}")
        
        return df_clean
    
    def get_info(self) -> Dict[str, Any]:
        return {
            'method': 'flag_mnar',
            'values_affected': int(self.values_affected),
            'imputed': False
        }


class ImputationManager:
    """Manages imputation with strategy pattern."""
    
    def __init__(self, config: PipelineConfig = DEFAULT_CONFIG):
        self.config = config
        self.decision_log = []
        self.imputers = {
            'median': MedianImputer(),
            'mean': MeanImputer(),
            'mode': ModeImputer(),
            'group': GroupImputer(),
            'flag_mnar': FlagImputer()
        }
    
    def impute(self, df: pd.DataFrame, column: str, method: str, 
               approved: bool = False, **kwargs) -> pd.DataFrame:
        """
        Impute missing values with specified method.
        Requires approval.
        
        Args:
            df: DataFrame
            column: Column to impute
            method: Imputation method
            approved: User approval
            **kwargs: Additional arguments
            
        Returns:
            DataFrame
        """
        if not approved:
            print(f"[SKIPPED] Imputation of {column} not approved")
            return df.copy()
        
        if column not in df.columns:
            print(f"[ERROR] Column {column} not found")
            return df.copy()
        
        null_count = df[column].isna().sum()
        if null_count == 0:
            print(f"[SKIPPED] {column} has no missing values")
            return df.copy()
        
        if method not in self.imputers:
            print(f"[ERROR] Unknown method {method}")
            return df.copy()
        
        imputer = self.imputers[method]
        df_clean = imputer.fit_transform(df, column, **kwargs)
        info = imputer.get_info()
        
        self.decision_log.append({
            'column': column,
            'issue': 'missing_values',
            'method': method,
            'justification': kwargs.get('justification', f'Imputed with {method}'),
            'values_affected': info['values_affected']
        })
        
        return df_clean
    
    def get_decision_log(self) -> pd.DataFrame:
        """Get decision log as DataFrame."""
        return pd.DataFrame(self.decision_log)
