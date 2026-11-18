"""
Input/Output operations for the preprocessing pipeline.

Handles safe loading and saving. Never overwrites original CSV.
"""

import os
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd

from .config import PipelineConfig, DEFAULT_CONFIG, get_input_path, get_output_path, get_output_dir


class DataIO:
    """Handles safe data loading and saving."""
    
    def __init__(self, config: PipelineConfig = DEFAULT_CONFIG):
        self.config = config
    
    def load_csv(self, path: Optional[Path] = None) -> pd.DataFrame:
        """
        Load CSV safely and return a copy.
        Never modifies the original file.
        
        Args:
            path: Optional custom path, uses config if None
            
        Returns:
            DataFrame copy
        """
        if path is None:
            path = get_input_path(self.config)
        
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Input CSV not found: {path}")
        
        print(f"[IO] Loading: {path}")
        print(f"[IO] File size: {path.stat().st_size / (1024**2):.2f} MB")
        
        # Load with defensive parameters
        df = pd.read_csv(
            path,
            encoding='utf-8',
            low_memory=False
        )
        
        print(f"[IO] Loaded shape: {df.shape}")
        # Return a copy to work in memory
        return df.copy()
    
    def save_csv(self, df: pd.DataFrame, path: Optional[Path] = None, 
                check_exists: bool = True) -> Tuple[bool, Path]:
        """
        Save CSV to disk. Only for final cleaned output.
        
        Args:
            df: DataFrame to save
            path: Optional custom path
            check_exists: Check if file exists and ask/warn
            
        Returns:
            Tuple of (success, path)
        """
        if path is None:
            path = get_output_path(self.config)
        
        path = Path(path)
        output_dir = path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if exists
        if check_exists and path.exists():
            print(f"[IO] WARNING: Output file already exists: {path}")
            print("[IO] Stopping to avoid overwrite. Please confirm or remove the file.")
            return False, path
        
        print(f"[IO] Saving to: {path}")
        df.to_csv(path, index=False, encoding='utf-8')
        print(f"[IO] Saved shape: {df.shape}")
        print(f"[IO] File size: {path.stat().st_size / (1024**2):.2f} MB")
        
        return True, path
    
    def ensure_output_dir(self):
        """Ensure output directory exists."""
        get_output_dir(self.config).mkdir(parents=True, exist_ok=True)


# Convenience functions
def load_input_csv(config: PipelineConfig = DEFAULT_CONFIG) -> pd.DataFrame:
    """Load input CSV as copy."""
    return DataIO(config).load_csv()


def save_cleaned_csv(df: pd.DataFrame, config: PipelineConfig = DEFAULT_CONFIG,
                     check_exists: bool = True) -> Tuple[bool, Path]:
    """Save cleaned CSV."""
    return DataIO(config).save_csv(df, check_exists=check_exists)
