"""Reconstruction and export of the person-level train/test split.

Notebook 3.0 exported ``y_train`` / ``y_test`` but not the person map.  This
module rebuilds the split with the same filter, splitter and seed, verifies
that the rebuilt target matches the exported files row by row, and writes a
new file *outside the inputs*:

``reports/eda_jobpath/tables/split_map_resume_id.csv``

Columns: ``resume_id``, ``split`` and ``n_experiences``.  The file contains a
pseudonymous key, a split label and a count; it does not expose trajectories.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from scripts.ScriptsCsv.Transformacion.split import group_train_test_split

from .config import EDAConfig, PERSON_COL, TARGET_COL, TARGET_DISPLAY


@dataclass(frozen=True)
class SplitMapResult:
    """Everything the EDA needs to work with the verified split."""

    map_frame: pd.DataFrame
    train: pd.DataFrame
    test: pd.DataFrame
    verification: Dict[str, object]


class SplitMapper:
    """Rebuild the split, verify it against the exported target and export the map."""

    def build(
        self,
        frame: pd.DataFrame,
        y_train: pd.DataFrame,
        y_test: pd.DataFrame,
        config: EDAConfig,
    ) -> SplitMapResult:
        """Recreate the exact split used by notebook 3.0 and attach the target."""
        classified = frame.loc[frame["n_skills_essential"].notna()].reset_index(drop=True)
        # Stable row position: lets the B version reuse the exact same rows
        # without depending on the order returned by the splitter.
        classified["_row_position"] = np.arange(len(classified))
        train, test = group_train_test_split(
            classified,
            group_col=PERSON_COL,
            test_size=config.test_size,
            random_state=config.seed,
        )

        y_train_series = y_train.iloc[:, 0].reset_index(drop=True)
        y_test_series = y_test.iloc[:, 0].reset_index(drop=True)
        if len(train) != len(y_train_series) or len(test) != len(y_test_series):
            raise ValueError(
                "El split reconstruido no coincide en tamaño con los archivos exportados: "
                f"train {len(train)} vs {len(y_train_series)}, "
                f"test {len(test)} vs {len(y_test_series)}"
            )

        train = train.copy()
        test = test.copy()
        train[TARGET_COL] = y_train_series.to_numpy()
        test[TARGET_COL] = y_test_series.to_numpy()
        # Rename in RAM only.  Persisting it would require editing
        # src/transformacion/transformacion.py and re-running notebook 3.0.
        train[TARGET_DISPLAY] = train[TARGET_COL]
        test[TARGET_DISPLAY] = test[TARGET_COL]

        derived_train = train["veces_ese_oficio"].gt(1).astype(int)
        derived_test = test["veces_ese_oficio"].gt(1).astype(int)
        overlap = len(set(train[PERSON_COL]).intersection(set(test[PERSON_COL])))

        counts = frame.groupby(PERSON_COL, sort=False).size()
        all_persons = counts.index.to_series().reset_index(drop=True)
        train_ids = set(train[PERSON_COL])
        test_ids = set(test[PERSON_COL])
        labels = np.where(
            all_persons.isin(train_ids),
            "train",
            np.where(all_persons.isin(test_ids), "test", "excluded_no_classified_job"),
        )
        map_frame = pd.DataFrame(
            {
                PERSON_COL: all_persons.to_numpy(),
                "split": labels,
                "n_experiences": all_persons.map(counts).to_numpy(),
            }
        )

        verification = {
            "filas_train": int(len(train)),
            "filas_test": int(len(test)),
            "personas_train": int(train[PERSON_COL].nunique()),
            "personas_test": int(test[PERSON_COL].nunique()),
            "personas_solapadas": int(overlap),
            "target_coincide_train_pct": round(
                float(derived_train.eq(train[TARGET_COL]).mean() * 100), 4
            ),
            "target_coincide_test_pct": round(
                float(derived_test.eq(test[TARGET_COL]).mean() * 100), 4
            ),
            "prevalencia_train_pct": round(float(train[TARGET_COL].mean() * 100), 2),
            "prevalencia_test_pct": round(float(test[TARGET_COL].mean() * 100), 2),
            "personas_sin_oficio_clasificado": int(
                (map_frame["split"] == "excluded_no_classified_job").sum()
            ),
        }
        return SplitMapResult(map_frame=map_frame, train=train, test=test, verification=verification)

    def save(self, result: SplitMapResult, config: EDAConfig) -> str:
        """Persist the map outside the input folders and return its path."""
        config.tables_dir.mkdir(parents=True, exist_ok=True)
        path = config.split_map_path
        result.map_frame.to_csv(path, index=False, encoding="utf-8")
        return str(path)
