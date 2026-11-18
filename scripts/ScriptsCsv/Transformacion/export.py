"""Export utilities for transformed feature matrices and fitted artifacts."""

from pathlib import Path
from typing import Any

import joblib
import pandas as pd

try:
    import pyarrow as pa
    import pyarrow.csv as pacsv

    _HAS_PYARROW = True
except Exception:
    _HAS_PYARROW = False


def ensure_dir(path: Path) -> Path:
    """Create directory (and parents) if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_frame(df: pd.DataFrame, path: Path) -> Path:
    """Write DataFrame to CSV using multi-threaded PyArrow when available."""
    ensure_dir(path.parent)
    if _HAS_PYARROW and len(df) > 10_000 and df.shape[1] > 50:
        write_opts = pacsv.WriteOptions(include_header=True, batch_size=100_000)
        chunk_rows = 200_000
        with open(path, "wb") as sink:
            for start in range(0, len(df), chunk_rows):
                sub = df.iloc[start : start + chunk_rows]
                tbl = pa.Table.from_pandas(sub, preserve_index=False)
                opts = (
                    write_opts
                    if start == 0
                    else pacsv.WriteOptions(
                        include_header=False, batch_size=100_000
                    )
                )
                pacsv.write_csv(tbl, sink, write_options=opts)
    else:
        df.to_csv(path, index=False, encoding="utf-8", chunksize=50_000)
    return path


def save_transformers(artifacts: Any, transformers_path: Path) -> Path:
    """Serialize fitted TransformArtifacts to `transformers.joblib`."""
    ensure_dir(transformers_path)
    joblib.dump(artifacts, transformers_path / "transformers.joblib")
    return transformers_path / "transformers.joblib"
