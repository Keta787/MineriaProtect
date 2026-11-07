"""Exportacion de artefactos transformados."""

from pathlib import Path
from typing import Any, Dict

import joblib
import pandas as pd


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_frame(df: pd.DataFrame, path: Path) -> Path:
    ensure_dir(path.parent)
    df.to_csv(path, index=False, encoding="utf-8")
    return path


def save_transformers(artifacts: Any, transformers_path: Path) -> Path:
    ensure_dir(transformers_path)
    joblib.dump(artifacts, transformers_path / "transformers.joblib")
    return transformers_path / "transformers.joblib"
