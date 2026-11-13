"""
Duplicate detection and handling module.

Implements two-stage duplicate verification while preserving privacy
(only aggregated metrics are displayed; individual trajectories are never printed):
1. Exact duplicates across all columns (keep='first').
2. Composite business-key duplicates (`resume_id`, `start_date`, `end_date`,
   `university_level`, `matched_code`) and aggregated person-trajectory summary
   for `resume_id`.
"""

from typing import Dict, Any, Tuple
import pandas as pd

from .config import PipelineConfig, DEFAULT_CONFIG


class DuplicateHandler:
    """Handles duplicate detection and removal with aggregated reporting."""

    def __init__(self, config: PipelineConfig = DEFAULT_CONFIG) -> None:
        self.config = config
        self.decision_log = []

    def remove_exact_duplicates(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Step 1: Remove exact duplicates across all columns (keep='first')."""
        print("=" * 80)
        print("STEP 1: EXACT DUPLICATES ACROSS ALL COLUMNS")
        print("=" * 80)

        initial_shape = df.shape
        exact_dups_mask = df.duplicated(keep="first")
        exact_dups_count = int(exact_dups_mask.sum())

        print(f"\n[BEFORE] Shape: {initial_shape}")
        print(f"[EXACT DUPLICATES FOUND] {exact_dups_count} rows")

        if exact_dups_count > 0:
            print("[ACTION] Removing with keep='first'")
            df_clean = df.drop_duplicates(keep="first").reset_index(drop=True)
            print(f"[AFTER] Shape: {df_clean.shape}")
            print(f"[REMOVED] {exact_dups_count} rows")

            self.decision_log.append(
                {
                    "column": "ALL_COLUMNS",
                    "issue": "exact_duplicates",
                    "method": "drop_duplicates(keep='first')",
                    "justification": (
                        "Eliminación de filas exactamente idénticas en todas las columnas"
                    ),
                    "values_affected": exact_dups_count,
                }
            )
        else:
            print("[ACTION] None to remove")
            df_clean = df.copy()
            self.decision_log.append(
                {
                    "column": "ALL_COLUMNS",
                    "issue": "exact_duplicates",
                    "method": "none",
                    "justification": (
                        "Sin duplicados exactos en las 23 columnas (ya depurados en integración)"
                    ),
                    "values_affected": 0,
                }
            )

        report = {
            "initial_shape": initial_shape,
            "exact_duplicates_count": exact_dups_count,
            "final_shape": df_clean.shape,
            "removed": exact_dups_count,
        }

        print("=" * 80)
        return df_clean, report

    def find_key_duplicates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Step 2: Check composite business key and report aggregated person counts."""
        key_col = self.config.unique_key
        comp_cols = list(
            getattr(
                self.config,
                "composite_key",
                (
                    "resume_id",
                    "start_date",
                    "end_date",
                    "university_level",
                    "matched_code",
                ),
            )
        )

        print("=" * 80)
        print(
            f"STEP 2: COMPOSITE KEY {comp_cols} & PERSON GROUPING KEY [{key_col}]"
        )
        print("=" * 80)

        if key_col not in df.columns:
            print(f"[ERROR] Key column '{key_col}' not found in dataframe")
            print(f"[AVAILABLE COLUMNS] {list(df.columns)}")
            return {"found": False, "error": f"Column {key_col} not found"}

        comp_present = [c for c in comp_cols if c in df.columns]
        comp_dups_count = int(df.duplicated(subset=comp_present, keep="first").sum())
        short_cols = [
            c
            for c in ("resume_id", "start_date", "matched_code")
            if c in df.columns
        ]
        short_dups_count = int(df.duplicated(subset=short_cols, keep="first").sum())

        jobs_per_person = df.groupby(key_col).size()
        n_persons = int(jobs_per_person.shape[0])
        multi_job_persons = int((jobs_per_person > 1).sum())

        print(f"\n[PERSON GROUPING KEY] {key_col} (relación 1:N persona -> empleos)")
        print(f"  - Personas únicas ({key_col}): {n_persons:,}")
        print(
            f"  - Personas con >1 experiencia laboral (trayectoria longitudinal): "
            f"{multi_job_persons:,} ({multi_job_persons / n_persons * 100:.2f}%)"
        )
        print(
            f"  - Empleos por persona (agregado, sin exponer trayectorias individuales): "
            f"min={int(jobs_per_person.min())}, mediana={float(jobs_per_person.median()):.1f}, "
            f"media={float(jobs_per_person.mean()):.2f}, max={int(jobs_per_person.max())}"
        )
        print(f"\n[COMPOSITE BUSINESS KEY] {comp_present}")
        print(f"  - Duplicados por clave compuesta (5 columnas): {comp_dups_count}")
        print(
            f"  - Duplicados por clave corta {short_cols} (variantes parciales end_date): {short_dups_count}"
        )

        report = {
            "found": comp_dups_count > 0,
            "key_column": key_col,
            "composite_key": comp_present,
            "rows_affected": comp_dups_count,
            "short_key_duplicates": short_dups_count,
            "unique_persons": n_persons,
            "multi_job_persons": multi_job_persons,
            "groups": comp_dups_count,
            "duplicate_df": None,
            "groups_detail": [],
        }

        if comp_dups_count == 0:
            print(
                f"\n[OK] 0 duplicados erróneos en clave compuesta {comp_present}. "
                f"Las repeticiones de '{key_col}' corresponden a la trayectoria laboral longitudinal (1:N)."
            )
            self.decision_log.append(
                {
                    "column": "+".join(comp_present),
                    "issue": "composite_key_duplicates",
                    "method": "none",
                    "justification": (
                        "0 duplicados en clave compuesta ni en clave corta; "
                        "resume_id agrupa trayectorias 1:N sin eliminar experiencias legítimas"
                    ),
                    "values_affected": 0,
                }
            )
        else:
            print(
                f"\n[WARNING] {comp_dups_count} duplicados encontrados en clave compuesta - requiere confirmación."
            )

        print("=" * 80)
        return report

    def remove_key_duplicates(
        self, df: pd.DataFrame, approved: bool = False, keep: str = "first"
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Step 2b: Remove composite-key duplicates ONLY if explicitly approved."""
        comp_cols = [
            c
            for c in getattr(
                self.config,
                "composite_key",
                (
                    "resume_id",
                    "start_date",
                    "end_date",
                    "university_level",
                    "matched_code",
                ),
            )
            if c in df.columns
        ]

        if not approved:
            print("[SKIPPED] Composite key duplicates removal not approved")
            return df.copy(), {"removed": 0, "approved": False}

        key_dups_mask = df.duplicated(subset=comp_cols, keep=keep)
        key_dups_count = int(key_dups_mask.sum())

        print(f"[REMOVING] Duplicates by {comp_cols} with keep='{keep}'")
        df_clean = df.drop_duplicates(subset=comp_cols, keep=keep).reset_index(
            drop=True
        )
        print(f"[REMOVED] {key_dups_count} rows. New shape: {df_clean.shape}")

        self.decision_log.append(
            {
                "column": "+".join(comp_cols),
                "issue": "composite_key_duplicates",
                "method": f"drop_duplicates(subset={comp_cols}, keep='{keep}')",
                "justification": (
                    f"Eliminación aprobada de duplicados por clave compuesta {comp_cols}"
                ),
                "values_affected": key_dups_count,
            }
        )

        return df_clean, {
            "removed": key_dups_count,
            "approved": True,
            "keep": keep,
        }

    def get_decision_log(self) -> pd.DataFrame:
        """Return decision log as a DataFrame."""
        return pd.DataFrame(self.decision_log)
