"""Read-only loading of the JobPath datasets used by the EDA.

The loader never writes to an input file.  It keeps one enriched copy per
version in memory and hands out ``.copy()`` objects so a caller cannot mutate
the cache by accident.  Date ordinals and job order are derived with the same
helpers used by notebook 3.0, so the EDA sees exactly the same timeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence

import joblib
import pandas as pd

from scripts.ScriptsCsv.Transformacion.date_features import (
    add_date_ordinals,
    add_job_order,
    add_start_year,
)

from .config import EDAConfig, PERSON_COL, TEXT_COLUMNS, VERSIONS


@dataclass(frozen=True)
class TextColumnStats:
    """Lightweight profile of the raw ESCO list columns."""

    column: str
    nulls: int
    null_pct: float
    n_unique: int
    max_length: int


class JobPathLoader:
    """Load the clean CSVs and the exported train/test artefacts."""

    def __init__(self, config: EDAConfig) -> None:
        self._config = config
        self._cache: Dict[str, pd.DataFrame] = {}
        self._header: Dict[str, List[str]] = {}

    # ------------------------------------------------------------------
    # Clean datasets
    # ------------------------------------------------------------------
    def header(self, version: str) -> List[str]:
        """Column names of a clean CSV, without loading the rows."""
        if version not in self._header:
            path = self._config.clean_paths[version]
            self._header[version] = pd.read_csv(path, nrows=0).columns.tolist()
        return list(self._header[version])

    def load_clean(self, version: str, include_text: bool = False) -> pd.DataFrame:
        """Load one clean version with derived temporal features.

        Parameters
        ----------
        version:
            ``con_outliers`` (A) or ``sin_outliers`` (B).
        include_text:
            When ``True`` the three raw ESCO list columns are kept.  They are
            excluded by default because they are long strings and no approved
            chart uses them.
        """
        if version not in VERSIONS:
            raise ValueError(f"Versión desconocida: {version!r}")
        key = f"{version}|{'text' if include_text else 'lean'}"
        if key not in self._cache:
            path = self._config.clean_paths[version]
            usecols = None
            if not include_text:
                usecols = [c for c in self.header(version) if c not in TEXT_COLUMNS]
            frame = pd.read_csv(path, usecols=usecols, encoding="utf-8", low_memory=False)
            frame = add_date_ordinals(frame, "start_date", "end_date")
            frame = add_start_year(frame)
            frame = add_job_order(frame, PERSON_COL, "start_ord")
            self._cache[key] = frame
        return self._cache[key].copy()

    def text_column_stats(self, version: str) -> List[TextColumnStats]:
        """Nulls, cardinality and max length of the raw ESCO lists.

        The columns are read one at a time to keep the peak memory low.
        """
        path = self._config.clean_paths[version]
        stats: List[TextColumnStats] = []
        for column in TEXT_COLUMNS:
            series = pd.read_csv(path, usecols=[column], dtype="string")[column]
            nulls = int(series.isna().sum())
            stats.append(
                TextColumnStats(
                    column=column,
                    nulls=nulls,
                    null_pct=round(nulls / len(series) * 100, 2) if len(series) else 0.0,
                    n_unique=int(series.nunique(dropna=True)),
                    max_length=int(series.str.len().max()) if series.notna().any() else 0,
                )
            )
            del series
        return stats

    # ------------------------------------------------------------------
    # Exported train/test artefacts
    # ------------------------------------------------------------------
    def load_y(self, version: str, split: str) -> pd.DataFrame:
        """Load ``y_train`` / ``y_test`` exactly as exported by notebook 3.0."""
        path = self._config.transformed_dir / version / split / f"y_{split}.csv"
        return pd.read_csv(path)

    def load_x_header(self, version: str, split: str) -> List[str]:
        """Column names of an ``X`` matrix without loading its values."""
        path = self._config.transformed_dir / version / split / f"X_{split}.csv"
        return pd.read_csv(path, nrows=0).columns.tolist()

    def load_x_subset(self, version: str, split: str, columns: Sequence[str]) -> pd.DataFrame:
        """Load only the requested columns of an ``X`` matrix."""
        path = self._config.transformed_dir / version / split / f"X_{split}.csv"
        available = set(self.load_x_header(version, split))
        missing = [c for c in columns if c not in available]
        if missing:
            raise KeyError(f"Columnas ausentes en {path.name}: {missing}")
        return pd.read_csv(path, usecols=list(columns))

    def load_transformers(self, version: str):
        """Load the fitted transformers (read-only, never modified)."""
        path = self._config.transformed_dir / "transformers" / version / "transformers.joblib"
        return joblib.load(path)

    def load_split_map(self) -> pd.DataFrame | None:
        """Load the persisted resume_id -> split map when it already exists."""
        path = self._config.split_map_path
        if not path.exists():
            return None
        return pd.read_csv(path)

    # ------------------------------------------------------------------
    # Small helpers
    # ------------------------------------------------------------------
    def file_size_mb(self, path: Path) -> float:
        """Human-friendly size of a file."""
        return round(path.stat().st_size / (1024 * 1024), 2)
