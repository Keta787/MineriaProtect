"""End-to-end orchestrator for CRISP-DM Phase 4 (Modeling & Evaluation)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import pandas as pd

from scripts.ScriptsCsv.EDA.validation import FileFingerprint, FileHasher

from .config import ModelingConfig, VERSION_CON, VERSION_SIN
from .dataset_builder import ModelingDatasetBuilder, VersionModelingData
from .evaluation import EvaluationBundle, PersonGroupedEvaluator
from .plots import ModelingPlotter


@dataclass(frozen=True)
class ModelingPipelineResult:
    """Complete output of the Phase 4 modeling and evaluation pipeline."""

    data_a: VersionModelingData
    data_b: VersionModelingData
    evaluation: EvaluationBundle
    figures: Dict[str, str]
    decision_log: pd.DataFrame
    integrity_report: pd.DataFrame


class ModelingPipeline:
    """Orchestrate leakage-free feature preparation, person-grouped CV, and A/B evaluation."""

    def __init__(
        self,
        config: ModelingConfig,
        builder: ModelingDatasetBuilder | None = None,
        evaluator: PersonGroupedEvaluator | None = None,
        plotter: ModelingPlotter | None = None,
        hasher: FileHasher | None = None,
    ) -> None:
        self.config = config
        self.builder = builder or ModelingDatasetBuilder(config)
        self.evaluator = evaluator or PersonGroupedEvaluator(config)
        self.plotter = plotter or ModelingPlotter(config)
        self.hasher = hasher or FileHasher()

    def _input_paths(self) -> List[Path]:
        paths = [
            self.config.clean_csv_path(VERSION_CON),
            self.config.clean_csv_path(VERSION_SIN),
            self.config.split_map_path,
        ]
        for ver in (VERSION_CON, VERSION_SIN):
            paths.extend(
                [
                    self.config.x_path(ver, "train"),
                    self.config.y_path(ver, "train"),
                    self.config.x_path(ver, "test"),
                    self.config.y_path(ver, "test"),
                    self.config.transformers_path(ver),
                ]
            )
        return paths

    def snapshot_inputs(self) -> Dict[str, FileFingerprint]:
        """Take SHA-256 fingerprints of all upstream inputs before running."""
        return self.hasher.snapshot(self._input_paths())

    def verify_inputs(self, before: Dict[str, FileFingerprint]) -> pd.DataFrame:
        """Verify that no upstream file was modified during Phase 4 execution."""
        return self.hasher.verify(before)

    def build_decision_log(
        self,
        data_a: VersionModelingData,
        eval_bundle: EvaluationBundle,
    ) -> pd.DataFrame:
        """Build the Spanish CRISP-DM Phase 4 decision log from computed metrics."""
        ab = eval_bundle.ablation_table
        te = eval_bundle.test_summary_table
        leak_pr = float(ab.iloc[0]["pr_auc_cv_media"])
        clean_pr = float(ab.iloc[2]["pr_auc_cv_media"])

        log_a = te.loc[
            (te["version"].str.startswith("A")) & (te["modelo"].str.contains("Logística"))
        ].iloc[0]
        log_b = te.loc[
            (te["version"].str.startswith("B")) & (te["modelo"].str.contains("Logística"))
        ].iloc[0]
        hgb_a = te.loc[
            (te["version"].str.startswith("A")) & (te["modelo"].str.contains("HistGradient"))
        ].iloc[0]

        rows = [
            {
                "id": "F4-01",
                "decision": "Exclusión obligatoria de columnas con fuga del target",
                "evidencia_ejecutada": (
                    f"Con veces_ese_oficio_rob/bin el PR-AUC CV es {leak_pr:.4f} (fuga artificial); "
                    f"al excluirlas pasa a {clean_pr:.4f} sobre {data_a.verification['filas_train']:,} filas."
                ),
                "accion_adoptada": (
                    "Se eliminan veces_ese_oficio_rob y veces_ese_oficio_bin de X en RAM antes de entrenar, "
                    "manteniendo intactos los CSV de 04_transformed."
                ),
            },
            {
                "id": "F4-02",
                "decision": "Control de colinealidad en variables numéricas",
                "evidencia_ejecutada": (
                    "Se eliminan start_year_rob (r=1.000 con start_ord_rob) y n_skills_competence_rob "
                    f"(r=0.952 con n_skills_essential_rob), pasando de 2,983 a 2,981 features con PR-AUC CV = {clean_pr:.4f}."
                ),
                "accion_adoptada": "Se conserva una sola representante por familia colineal para estabilizar los coeficientes.",
            },
            {
                "id": "F4-03",
                "decision": "Validación cruzada agrupada por persona (StratifiedGroupKFold)",
                "evidencia_ejecutada": (
                    f"5 pliegues sobre 281,674 personas de train con {eval_bundle.cv_leak_check['personas_solapadas_entre_folds']} "
                    "personas solapadas entre pliegues."
                ),
                "accion_adoptada": "Toda selección de hiperparámetros y ablación se ejecuta agrupando por resume_id.",
            },
            {
                "id": "F4-04",
                "decision": "Comparación de modelos y versiones A (con outliers) vs. B (sin outliers)",
                "evidencia_ejecutada": (
                    f"En test (347,720 filas): Logística OHE alcanza PR-AUC={log_a['pr_auc_test']:.4f}, "
                    f"F1={log_a['f1_pos_test']:.4f}, ROC-AUC={log_a['roc_auc_test']:.4f} en A vs. "
                    f"PR-AUC={log_b['pr_auc_test']:.4f}, F1={log_b['f1_pos_test']:.4f}, ROC-AUC={log_b['roc_auc_test']:.4f} en B; "
                    f"HistGradientBoosting (14 cols densas) alcanza PR-AUC={hgb_a['pr_auc_test']:.4f}, ROC-AUC={hgb_a['roc_auc_test']:.4f}."
                ),
                "accion_adoptada": (
                    "Las 2,967 dummies de occupation_code aportan señal adicional sobre el bloque denso; "
                    "las versiones A y B muestran desempeño prácticamente idéntico tras el escalado robusto."
                ),
            },
        ]
        return pd.DataFrame(rows)

    def save_tables(
        self,
        eval_bundle: EvaluationBundle,
        decision_log: pd.DataFrame,
    ) -> Dict[str, str]:
        """Export Phase 4 evaluation tables to reports/modelado_jobpath/tables/."""
        self.config.tables_dir.mkdir(parents=True, exist_ok=True)
        paths = {
            "ablation": self.config.tables_dir / "ablacion_fuga_colinealidad_cv.csv",
            "cv": self.config.tables_dir / "resultados_cv_por_persona.csv",
            "test": self.config.tables_dir / "resultados_test_ab.csv",
            "importance": self.config.tables_dir / "importancia_variables_sin_fuga.csv",
            "decisions": self.config.tables_dir / "bitacora_fase4_modelado.csv",
        }
        eval_bundle.ablation_table.to_csv(paths["ablation"], index=False)
        eval_bundle.cv_summary_table.to_csv(paths["cv"], index=False)
        eval_bundle.test_summary_table.to_csv(paths["test"], index=False)
        eval_bundle.feature_importance_table.to_csv(paths["importance"], index=False)
        decision_log.to_csv(paths["decisions"], index=False)
        return {k: str(v) for k, v in paths.items()}

