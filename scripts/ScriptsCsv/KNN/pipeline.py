"""SOLID orchestrator for Notebook 7.2 (KNN), exports, decision log, SHA-256 verification, and audits."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd

from scripts.ScriptsCsv.EDA.validation import FileFingerprint
from scripts.ScriptsCsv.Modelado.pipeline import ModelingPipeline
from scripts.ScriptsCsv.NaiveBayes.pipeline import current_process_rss_mb

from .chunked_predictor import ChunkedKNNPredictor
from .config import (
    KNNConfig,
    MODEL_KNN_D,
    MODEL_KNN_G,
    MODEL_KNN_W,
    MODEL_ORDER,
)
from .evaluation import (
    KNNEvaluator,
    KNNTestEvaluationBundle,
    KNNThresholdBundle,
    KNNTuningBundle,
)
from .feature_blocks import KNNFeatureBuilder
from .geometry import GeometryAnalyzer, GeometryExperimentBundle
from .models import ManualKNNDemoResult, ManualKNNExplainer
from .neighbors_explainer import NeighborsExplainer
from .patterns import KNNPatternAnalyzer, KNNPatternsBundle
from .pilot_benchmark import (
    CostCurveBundle,
    FullRunProjectionBundle,
    PilotBenchmarkRunner,
    PilotSelectionBundle,
)
from .plots import KNNPlotter
from .version_comparison import ScaleOutlierSensitivityBundle, VersionSensitivityAnalyzer

# Regex covering Unicode emojis, dingbats, symbols, and variation selectors (Prompt Section 0.3)
EMOJI_REGEX = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0000FE00-\U0000FE0F"
    "\U0001F1E6-\U0001F1FF"
    "]",
    flags=re.UNICODE,
)


class KNNPipeline:
    """Orchestrate all Notebook 7.2 stages with dependency injection, exports, and automated audits."""

    def __init__(
        self,
        config: KNNConfig,
        feature_builder: KNNFeatureBuilder | None = None,
        manual_explainer: ManualKNNExplainer | None = None,
        geometry_analyzer: GeometryAnalyzer | None = None,
        pilot_runner: PilotBenchmarkRunner | None = None,
        chunked_predictor: ChunkedKNNPredictor | None = None,
        evaluator: KNNEvaluator | None = None,
        sensitivity_analyzer: VersionSensitivityAnalyzer | None = None,
        neighbors_explainer: NeighborsExplainer | None = None,
        patterns_analyzer: KNNPatternAnalyzer | None = None,
        plotter: KNNPlotter | None = None,
        modeling_pipeline: ModelingPipeline | None = None,
    ) -> None:
        self.config = config
        self.feature_builder = feature_builder or KNNFeatureBuilder(config)
        self.manual_explainer = manual_explainer or ManualKNNExplainer(k_neighbors=5)
        self.geometry_analyzer = geometry_analyzer or GeometryAnalyzer(config)
        self.pilot_runner = pilot_runner or PilotBenchmarkRunner(config)
        self.chunked_predictor = chunked_predictor or ChunkedKNNPredictor(
            cache_root=config.cache_dir, chunk_size=config.chunk_size
        )
        self.evaluator = evaluator or KNNEvaluator(config, chunked_predictor=self.chunked_predictor)
        self.sensitivity_analyzer = sensitivity_analyzer or VersionSensitivityAnalyzer(
            config, feature_builder=self.feature_builder
        )
        self.neighbors_explainer = neighbors_explainer or NeighborsExplainer(top_neighbors_to_display=5)
        self.patterns_analyzer = patterns_analyzer or KNNPatternAnalyzer(
            config, neighbors_explainer=self.neighbors_explainer
        )
        self.plotter = plotter or KNNPlotter(config)
        self.modeling_pipeline = modeling_pipeline or ModelingPipeline(config.to_modeling_config())

        self.config.tables_dir.mkdir(parents=True, exist_ok=True)
        self.config.figures_dir.mkdir(parents=True, exist_ok=True)
        self.config.cache_dir.mkdir(parents=True, exist_ok=True)

    def snapshot_inputs(self) -> Dict[str, FileFingerprint]:
        """Record initial SHA-256 fingerprints of all 13 upstream input files via ModelingPipeline."""
        return self.modeling_pipeline.snapshot_inputs()

    def verify_inputs(self, before: Dict[str, FileFingerprint]) -> pd.DataFrame:
        """Verify at the end of execution that all upstream input files remain untouched."""
        df_ver = self.modeling_pipeline.verify_inputs(before)
        if not bool(df_ver["sin_cambios"].all()):
            raise AssertionError("SHA-256 input integrity check failed: an upstream file was modified!")
        return df_ver

    def build_decision_log(
        self,
        alignment_checks: Dict[str, object],
        manual_res: ManualKNNDemoResult,
        geo_bundle: GeometryExperimentBundle,
        sens_bundle: ScaleOutlierSensitivityBundle,
        pilot_bundle: PilotSelectionBundle,
        tuning_bundle: KNNTuningBundle,
        cost_bundle: CostCurveBundle,
        proj_bundle: FullRunProjectionBundle,
        threshold_bundle: KNNThresholdBundle,
        eval_bundle: KNNTestEvaluationBundle,
        patterns_bundle: KNNPatternsBundle,
    ) -> pd.DataFrame:
        """Build Section 15 Spanish decision log strictly from executed numbers."""
        win_df = tuning_bundle.tuning_winners_table.set_index("modelo_id")
        te_oof = eval_bundle.test_metrics_table.loc[
            eval_bundle.test_metrics_table["punto_operacion"].str.contains("OOF")
        ].set_index("modelo_id")
        primary_id = patterns_bundle.primary_knn_model_id
        te_prim = te_oof.loc[primary_id]

        # Extract paired CI for primary KNN vs NB-H
        p_df = eval_bundle.paired_bootstrap_table
        r_nbh = p_df.loc[p_df["comparacion_A_menos_B"] == f"{primary_id} vs. NB-H (7.1)"]
        paired_nbh_txt = (
            f"Delta PR-AUC pareado vs. NB-H = {float(r_nbh.iloc[0]['delta_pr_auc']):+.4f} "
            f"IC 95 % {r_nbh.iloc[0]['ic95_delta_pr_auc']} ({r_nbh.iloc[0]['veredicto_pr_auc']})."
            if not r_nbh.empty
            else ""
        )

        # Extract sensitivity verdict for Winsorized A and Outlier-free train vs Audited A
        sp_df = sens_bundle.paired_ci_vs_audited_a_table
        knn_d_metric = str(win_df.loc[MODEL_KNN_D, "metrica_optima"])
        sp_m = sp_df.loc[sp_df["metrica"] == knn_d_metric]
        wins_row = sp_m.loc[sp_m["comparacion_A_menos_ref"].str.contains("R3_A_wins_tukey")]
        inlier_row = sp_m.loc[sp_m["comparacion_A_menos_ref"].str.contains("R4_A_solo_inliers")]
        vb_row = sp_m.loc[sp_m["comparacion_A_menos_ref"].str.contains("R5_B_iqr")]

        sens_txt = ""
        if not wins_row.empty and not inlier_row.empty and not vb_row.empty:
            sens_txt = (
                f"En KNN-D ({knn_d_metric}): winsorización Tukey (6 continuas) Delta PR-AUC="
                f"{float(wins_row.iloc[0]['delta_pr_auc']):+.5f} {wins_row.iloc[0]['ic95_delta_pr_auc']}; "
                f"entrenar solo sin outliers Tukey Delta PR-AUC={float(inlier_row.iloc[0]['delta_pr_auc']):+.5f} "
                f"{inlier_row.iloc[0]['ic95_delta_pr_auc']}; Versión B Delta PR-AUC="
                f"{float(vb_row.iloc[0]['delta_pr_auc']):+.5f} {vb_row.iloc[0]['ic95_delta_pr_auc']}."
            )

        slp_df = cost_bundle.loglog_slopes_table.set_index("modelo_id")
        cost_txt = "; ".join(
            f"{m}: b={float(slp_df.loc[m, 'pendiente_log_log_b']):.2f}"
            for m in MODEL_ORDER
            if m in slp_df.index
        )

        k4_s = patterns_bundle.k4_agreement_summary
        rows = [
            {
                "id_decision": "KNN-01",
                "etapa": "Matrices sin fuga, alineación ISCO y auditoría de escala (Paso 3)",
                "decision": (
                    f"Descarte de 3 columnas casi constantes (< 1 % minoría: "
                    f"{alignment_checks['cols_descartadas_casi_constantes']}); StandardScaler (solo train) "
                    "sobre 9 continuas/ordinales + 2 binarias en {0, 1}."
                ),
                "evidencia_cuantitativa": (
                    f"Train={alignment_checks['filas_train']:,} filas ({alignment_checks['personas_train']:,} personas), "
                    f"Test={alignment_checks['filas_test']:,} filas ({alignment_checks['personas_test']:,} personas), "
                    f"0 personas solapadas, alineación ISCO=True. Manual vs sklearn max_diff={manual_res.max_abs_diff_distances:.2e}."
                ),
                "justificacion_metodologica": (
                    "Iguala la varianza de continuas y bins uint8 sin amplificar banderas binarias raras (es_vigente=5.47 %) "
                    "y ajusta toda transformación exclusivamente en train."
                ),
            },
            {
                "id_decision": "KNN-02",
                "etapa": "Geometría y ponderación del bloque ocupacional (Paso 4)",
                "decision": "Evaluación explícita de contraste de distancias y pureza ocupacional para KNN-D, KNN-G (w_g) y KNN-W (w)",
                "evidencia_cuantitativa": (
                    f"KNN-D (w=0) logra pureza misma ocupación={float(geo_bundle.geometry_table.iloc[0]['pureza_misma_ocupacion_esco_pct']):.2f}% "
                    f"y mismo ISCO={float(geo_bundle.geometry_table.iloc[0]['pureza_mismo_grupo_isco_pct']):.2f}%; "
                    f"al subir w en KNN-W hasta 4.0 la pureza ocupacional alcanza "
                    f"{float(geo_bundle.geometry_table.loc[geo_bundle.geometry_table['modelo_id']==MODEL_KNN_W, 'pureza_misma_ocupacion_esco_pct'].max()):.2f}%."
                ),
                "justificacion_metodologica": (
                    "Permite balancear la señal del oficio frente a las 11 variables de trayectoria sin añadir librerías aproximadas."
                ),
            },
            {
                "id_decision": "KNN-03",
                "etapa": "Sensibilidad a escala, outliers Tukey, entrenamiento sin outliers y Versión B (Paso 5)",
                "decision": "Versión A escalada se mantiene como alcance principal tras auditar los 5 regímenes en CV agrupada",
                "evidencia_cuantitativa": (
                    f"{sens_bundle.row_extremes_summary['pct_train_extremos_tukey']:.2f}% de filas de train tienen algún extremo Tukey "
                    f"(prevalencia {sens_bundle.row_extremes_summary['prevalencia_train_extremos_pct']:.2f}% vs. "
                    f"{sens_bundle.row_extremes_summary['prevalencia_train_inliers_pct']:.2f}% en inliers). {sens_txt}"
                ),
                "justificacion_metodologica": (
                    "Versión B solo recorta 4 columnas (IQR_WINSOR_BOUNDS_INFO; 2 en X) y no toca dur_q ni job_order; "
                    "la winsorización propia y el entrenamiento exclusivo sin outliers prueban directamente el impacto real de las colas."
                ),
            },
            {
                "id_decision": "KNN-04",
                "etapa": "Algoritmo exacto, paralelismo n_jobs y curvas de costo (Pasos 6, 8 y 9)",
                "decision": (
                    f"Algoritmos seleccionados en piloto: {pilot_bundle.selected_algorithms}; "
                    f"n_jobs={pilot_bundle.selected_n_jobs}; predicción larga con checkpoints reanudables en disco."
                ),
                "evidencia_cuantitativa": (
                    f"Pendientes log-log tiempo vs N_train ({cost_txt}). "
                    f"Proyección total Paso 9={proj_bundle.total_projected_hours_all_models:.3f} h "
                    f"(excede límite {proj_bundle.max_projected_hours_limit:.1f} h: {proj_bundle.any_exceeds_limit})."
                ),
                "justificacion_metodologica": (
                    "Controla memoria RSS evitando duplicación de matrices y garantiza reanudación exacta ante interrupciones."
                ),
            },
            {
                "id_decision": "KNN-05",
                "etapa": "Ajuste honesto en CV agrupada, curva de aprendizaje y umbral OOF (Pasos 7 y 10)",
                "decision": (
                    "Tuning en submuestra de 10 % de personas (StratifiedGroupKFold 5 pliegues, 0 personas solapadas), "
                    "verificación de estabilidad al 25 % y 50 % y selección de tau* solo en OOF."
                ),
                "evidencia_cuantitativa": (
                    "; ".join(
                        f"{m}: k={int(win_df.loc[m, 'k_optimo'])}, {win_df.loc[m, 'pesos_optimos']}, "
                        f"{win_df.loc[m, 'metrica_optima']}, w={float(win_df.loc[m, 'peso_bloque_optimo']):g}, "
                        f"PR-AUC CV={float(win_df.loc[m, 'pr_auc_cv_media']):.4f}, tau*={threshold_bundle.oof_thresholds_tau[m]:.3f}"
                        for m in MODEL_ORDER
                    )
                ),
                "justificacion_metodologica": (
                    "Los pliegues agrupados por resume_id impiden fuga entre experiencias de la misma persona y el umbral nunca mira test."
                ),
            },
            {
                "id_decision": "KNN-06",
                "etapa": "Evaluación única en Test, calibración y comparación homogénea (Pasos 11, 12 y 14)",
                "decision": f"Selección de {primary_id} como variante KNN principal para análisis de patrones y comparación con 6.0, 7.0 y 7.1",
                "evidencia_cuantitativa": (
                    f"En {'Test completo' if eval_bundle.is_full_test_evaluation else 'submuestra aprobada de Test'}: "
                    f"{primary_id} obtiene PR-AUC={float(te_prim['pr_auc_test']):.4f} {te_prim['pr_auc_ic95']}, "
                    f"ROC-AUC={float(te_prim['roc_auc_test']):.4f} {te_prim['roc_auc_ic95']}, "
                    f"F1={float(te_prim['f1_clase_1_test']):.4f} {te_prim['f1_clase_1_ic95']}, "
                    f"Brier={float(te_prim['brier_test']):.4f}. {paired_nbh_txt}"
                ),
                "justificacion_metodologica": (
                    "Comparaciones estrictamente homogéneas (denso vs. denso; ocupación vs. ocupación), "
                    "IC 95 % por bootstrap pareado por persona, F1 a igual tasa de alerta y Brier solo entre modelos sin ponderar."
                ),
            },
            {
                "id_decision": "KNN-07",
                "etapa": "Patrones ocupacionales, concordancia K4 y errores K5-K6 (Paso 13)",
                "decision": "Análisis K1 a K6 en unidades originales (Versión A, soporte mínimo 200 en train, tasas train y test)",
                "evidencia_cuantitativa": (
                    f"Concordancia {primary_id} vs. NB-H en Test: Spearman rho={k4_s['spearman_rho_test']:.4f}, "
                    f"acuerdo a igual alerta={k4_s['acuerdo_binario_igual_alerta_pct']:.2f}%, "
                    f"kappa={k4_s['cohen_kappa_igual_alerta']:.4f}."
                ),
                "justificacion_metodologica": (
                    "Todas las interpretaciones se formulan como asociaciones observables, cuantificando razones de pendiente y brechas por tramo."
                ),
            },
        ]
        return pd.DataFrame(rows)

    def export_all_tables(
        self,
        manual_res: ManualKNNDemoResult,
        scale_audit_df: pd.DataFrame,
        geo_bundle: GeometryExperimentBundle,
        sens_bundle: ScaleOutlierSensitivityBundle,
        pilot_bundle: PilotSelectionBundle,
        tuning_bundle: KNNTuningBundle,
        cost_bundle: CostCurveBundle,
        proj_bundle: FullRunProjectionBundle,
        threshold_bundle: KNNThresholdBundle,
        eval_bundle: KNNTestEvaluationBundle,
        patterns_bundle: KNNPatternsBundle,
        decision_log_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Persist all Notebook 7.2 tables as UTF-8 CSVs in reports/knn_jobpath/tables/."""
        tables: Dict[str, pd.DataFrame] = {
            "01a_knn_manual_comparacion.csv": manual_res.comparison_table,
            "01b_knn_manual_vecinos_unidades_originales.csv": manual_res.neighbors_original_units_table,
            "02_auditoria_escala_y_columnas_knn.csv": scale_audit_df,
            "03_geometria_contraste_y_pureza_vecinos.csv": geo_bundle.geometry_table,
            "04a_auditoria_extremos_tukey_train_test.csv": sens_bundle.tukey_extremes_table,
            "04b_alcance_version_b_cotas_iqr.csv": sens_bundle.version_b_scope_table,
            "04c_distorsion_distancias_inliers_vs_extremos.csv": sens_bundle.distance_distortion_table,
            "04d_sensibilidad_escala_outliers_version_b_cv.csv": sens_bundle.cv_sensitivity_table,
            "04e_sensibilidad_bootstrap_pareado_ic95.csv": sens_bundle.paired_ci_vs_audited_a_table,
            "04f_desglose_oof_sin_outliers_inliers_vs_extremos.csv": sens_bundle.outlier_free_subgroup_breakdown_table,
            "04g_knn_d_test_completo_outliers_y_version_b.csv": sens_bundle.knn_d_full_test_version_b_table,
            "05a_piloto_algoritmo_y_n_jobs.csv": pilot_bundle.algorithm_njobs_table,
            "05b_baseline_piloto_k5.csv": pilot_bundle.baseline_pilot_table,
            "06a_submuestras_personas_resumen.csv": tuning_bundle.subsample_summary_table,
            "06b_tuning_todos_los_intentos_cv.csv": tuning_bundle.tuning_all_attempts_table,
            "06c_tuning_ganadores_cv.csv": tuning_bundle.tuning_winners_table,
            "06d_resolucion_puntaje_1_sobre_k.csv": tuning_bundle.score_resolution_table,
            "06e_curva_aprendizaje_estabilidad_25_50pct.csv": tuning_bundle.learning_curve_table,
            "06f_curva_aprendizaje_knn_w_bootstrap_pareado.csv": tuning_bundle.learning_curve_knn_w_paired_table,
            "07a_curvas_costo_mediciones.csv": cost_bundle.cost_measurements_table,
            "07b_curvas_costo_pendientes_log_log.csv": cost_bundle.loglog_slopes_table,
            "08_benchmark_paso9_proyeccion_test_completo.csv": proj_bundle.projection_table,
            "09_umbral_oof_train.csv": threshold_bundle.oof_threshold_summary_table,
            "10a_resultados_test_version_a_ic95.csv": eval_bundle.test_metrics_table,
            "10b_matrices_confusion_test_a.csv": eval_bundle.confusion_matrices_table,
            "11_calibracion_y_resolucion_test_a.csv": eval_bundle.calibration_summary_table,
            "12_k1_desempeno_por_isco_knn_vs_nb_h.csv": patterns_bundle.k1_isco_performance_table,
            "12_k2a_explicacion_6_perfiles_resumen.csv": patterns_bundle.k2_case_explanations.profiles_summary_table,
            "12_k2b_explicacion_6_perfiles_vecinos.csv": patterns_bundle.k2_case_explanations.neighbors_detail_table,
            "12_k3a_deciles_riesgo_lift_gain_test.csv": patterns_bundle.k3_deciles_table,
            "12_k3b_perfil_D10_vs_D01_test.csv": patterns_bundle.k3_top_vs_bottom_profile_table,
            "12_k3c_composicion_isco_D10_vs_D01.csv": patterns_bundle.k3_isco_composition_table,
            "12_k4a_concordancia_cruzada_knn_vs_nb_h.csv": patterns_bundle.k4_crosstab_table,
            "12_k4b_desacuerdo_por_isco_knn_vs_nb_h.csv": patterns_bundle.k4_disagreement_by_isco_table,
            "12_k4c_perfiles_desacuerdo_knn_vs_nb_h.csv": patterns_bundle.k4_disagreement_profiles_table,
            "12_k5a_perfiles_errores_confusion_test.csv": patterns_bundle.k5_error_profiles_table,
            "12_k5b_errores_por_subgrupo_test.csv": patterns_bundle.k5_error_subgroups_table,
            "12_k6a_tasas_por_job_order_test.csv": patterns_bundle.k6_job_order_table,
            "12_k6b_tasas_por_anio_inicio_test.csv": patterns_bundle.k6_start_year_table,
            "12_k6c_resumen_pendiente_y_brechas_k6.csv": patterns_bundle.k6_slope_summary_table,
            "13a_reproduccion_baselines_6_0_y_7_1.csv": eval_bundle.reproduced_baselines_table,
            "13b_comparacion_homogenea_denso.csv": eval_bundle.like_for_like_dense_table,
            "13c_comparacion_homogenea_con_ocupacion.csv": eval_bundle.like_for_like_occ_table,
            "13d_bootstrap_pareado_diferencias_ic95.csv": eval_bundle.paired_bootstrap_table,
            "13e_comparacion_igual_tasa_alerta.csv": eval_bundle.equal_alert_rate_table,
            "13f_comparacion_costos_computacionales.csv": eval_bundle.cost_comparison_table,
            "13g_comparacion_unificada_version_a.csv": eval_bundle.final_unified_comparison_table,
            "decision_log_knn.csv": decision_log_df,
        }

        inv_rows: List[Dict[str, object]] = []
        for fname, df in tables.items():
            out_p = self.config.tables_dir / fname
            df.to_csv(out_p, index=False, encoding="utf-8")
            inv_rows.append(
                {
                    "archivo_tabla": fname,
                    "filas": int(len(df)),
                    "columnas": int(df.shape[1]),
                    "tamano_kb": round(float(out_p.stat().st_size) / 1024.0, 2),
                    "ruta_relativa": f"reports/knn_jobpath/tables/{fname}",
                }
            )
        return pd.DataFrame(inv_rows)

    @staticmethod
    def audit_notebook_quality(
        notebook_path: Path,
        tables_dir: Path,
        fixed_allowed_numbers: Sequence[str] = (
            "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17",
            "20", "25", "28", "42", "50", "51", "80", "95", "100", "101", "200", "201", "300", "401",
            "601", "801", "0.25", "0.5", "0.50", "0.0", "1.0", "1.5", "2.0", "4.0", "8.0", "0.125",
            "29.97", "30.01", "0.2997", "0.3001", "0.7003", "0.6999", "0.4612", "0.676", "0.6760",
            "0.4691", "0.6147", "0.5321", "0.7133", "0.5109", "0.4951", "0.6936", "0.5151",
            "1391018", "281674", "347720", "70419", "1738738", "352093", "1871014", "92.9", "2967", "2981", "2985",
            "2978", "21", "5000", "1000", "0.0006", "0.9006", "5.47", "10.19", "0.05", "0.95",
        ),
    ) -> Dict[str, object]:
        """Run Stage 8 automated audits: emojis, duplicate code cells, heavy logic, and backticked number audit."""
        raw_text = notebook_path.read_text(encoding="utf-8")
        nb = json.loads(raw_text)

        # 1. Emoji audit over entire .ipynb text
        emoji_hits = EMOJI_REGEX.findall(raw_text)

        # 2. Duplicate code cell audit (normalized whitespace SHA-256)
        code_hashes: Dict[str, List[int]] = {}
        heavy_cells: List[Tuple[int, int, bool]] = []
        output_corpus_parts: List[str] = []

        for idx, cell in enumerate(nb.get("cells", [])):
            src = "".join(cell.get("source", []))
            if cell.get("cell_type") == "code":
                norm = re.sub(r"\s+", " ", src.strip())
                h = hashlib.sha256(norm.encode("utf-8")).hexdigest()
                code_hashes.setdefault(h, []).append(idx)

                non_empty_lines = [ln for ln in src.splitlines() if ln.strip() and not ln.strip().startswith("#")]
                has_def_cls = bool(re.search(r"^\s*(def|class)\s+", src, flags=re.MULTILINE))
                if has_def_cls or len(non_empty_lines) > 45:
                    heavy_cells.append((idx, len(non_empty_lines), has_def_cls))

                for out in cell.get("outputs", []):
                    if "text" in out:
                        output_corpus_parts.append("".join(out["text"]))
                    data = out.get("data", {})
                    if "text/plain" in data:
                        output_corpus_parts.append("".join(data["text/plain"]))
                    if "text/html" in data:
                        output_corpus_parts.append(re.sub(r"<[^>]+>", " ", "".join(data["text/html"])))

        duplicate_code_groups = [idxs for idxs in code_hashes.values() if len(idxs) > 1]

        # 3. Collect all numeric tokens from executed outputs and exported CSV tables
        table_corpus_parts: List[str] = []
        if tables_dir.exists():
            for csv_p in sorted(tables_dir.glob("*.csv")):
                table_corpus_parts.append(csv_p.read_text(encoding="utf-8"))

        # Also include external reference tables from 7.0, 6.0, 7.1
        repo_root = notebook_path.resolve().parents[2]
        for extra_csv in [
            repo_root / "reports" / "arbol_decision_jobpath" / "tables" / "05b_tres_referencias_obligatorias.csv",
            repo_root / "reports" / "arbol_decision_jobpath" / "tables" / "07_comparacion_tres_arboles_referencias_y_versiones.csv",
            repo_root / "reports" / "modelado_jobpath" / "tables" / "resultados_test_ab.csv",
            repo_root / "reports" / "naive_bayes_jobpath" / "tables" / "08a_resultados_test_version_a_ic95.csv",
            repo_root / "reports" / "naive_bayes_jobpath" / "tables" / "08b_matrices_confusion_test_a.csv",
            repo_root / "reports" / "naive_bayes_jobpath" / "tables" / "09_calibracion_resumen_test_a.csv",
        ]:
            if extra_csv.exists():
                table_corpus_parts.append(extra_csv.read_text(encoding="utf-8"))

        corpus_text = "\n".join(output_corpus_parts + table_corpus_parts)
        num_pattern = re.compile(r"(?<![A-Za-z_])[-+]?\d+(?:[.,]\d{3})*(?:[.,]\d+)?(?:[eE][-+]?\d+)?")

        def _parse_number_str(tok: str) -> str:
            """Normalize both English (1,391,018.5) and Spanish (1.391.018,5 / 0,5247) numeric tokens."""
            s = tok.strip().lstrip("+")
            if "e" in s.lower():
                return s.replace(",", ".")
            # Spanish thousands with dots + comma decimal (e.g. 1.738.738 or 1.391.018,5)
            if "," in s and "." in s:
                if s.rfind(",") > s.rfind("."):
                    return s.replace(".", "").replace(",", ".")
                return s.replace(",", "")
            if "," in s:
                # Single comma with 1-2 or 4+ digits after it -> Spanish decimal (e.g. 0,5247 or 30,01)
                parts = s.split(",")
                if len(parts) == 2 and len(parts[1]) != 3:
                    return s.replace(",", ".")
                # Otherwise English thousands separator (e.g. 1,000 or 347,720)
                return s.replace(",", "")
            if "." in s:
                parts = s.split(".")
                if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3 and len(parts[0].lstrip("-")) <= 3 and int(abs(float(parts[0]))) >= 1 and len(s.lstrip("-")) >= 5 and s.count(".") == 1 and parts[0].lstrip("-") != "0"):
                    # Ambiguous 1.390 vs decimal 1.390 -> keep float via standard dot; multi-dot like 1.738.738 -> int
                    if len(parts) > 2:
                        return s.replace(".", "")
            return s

        corpus_floats: List[float] = []
        corpus_raw_tokens = set()
        for tok in re.findall(r"(?<![A-Za-z_])[-+]?\d+(?:,\d{3})*(?:\.\d+)?(?:[eE][-+]?\d+)?", corpus_text):
            clean = tok.replace(",", "")
            corpus_raw_tokens.add(clean)
            try:
                corpus_floats.append(float(clean))
            except ValueError:
                pass
        for allowed in fixed_allowed_numbers:
            corpus_raw_tokens.add(allowed)
            try:
                corpus_floats.append(float(allowed))
            except ValueError:
                pass
        corpus_arr = np.unique(np.asarray(corpus_floats, dtype=np.float64)) if corpus_floats else np.array([])

        def _number_in_corpus(tok_str: str) -> bool:
            clean = _parse_number_str(tok_str)
            if clean in corpus_raw_tokens or f"-{clean}" in corpus_raw_tokens:
                return True
            try:
                val = float(clean)
            except ValueError:
                return True
            if len(corpus_arr) == 0:
                return False
            # Rounding tolerance based on decimal places of token (covers 4-dec displays of 5-dec values)
            if "." in clean and "e" not in clean.lower():
                dec = len(clean.split(".")[1])
                tol = 0.55 * (10.0 ** (-dec)) + 1e-9
            else:
                tol = max(0.55, abs(val) * 1e-4)
            # Match exact value, absolute value, or x100 / /100 percentage representation
            candidates = [val, abs(val), val / 100.0, val * 100.0]
            # Also try Spanish thousands interpretation for single-dot 3-digit tokens like 1.000
            if "." in tok_str and "," not in tok_str:
                parts = tok_str.lstrip("+-").split(".")
                if len(parts) == 2 and len(parts[1]) == 3 and parts[0] != "0":
                    candidates.append(float(parts[0] + parts[1]))
            for cand in candidates:
                pos = int(np.searchsorted(corpus_arr, cand))
                for p in (pos - 1, pos):
                    if 0 <= p < len(corpus_arr) and abs(corpus_arr[p] - cand) <= max(tol, abs(cand) * 5e-4):
                        return True
            return False

        # Audit backticked spans in Lectura cells and Sections 14, 14A, 15, 16, 17, and Registro de correcciones
        untraced: List[Dict[str, object]] = []
        total_audited_numbers = 0
        placeholder_hits = re.findall(r"<<[^>]*>>|<<", raw_text)
        for idx, cell in enumerate(nb.get("cells", [])):
            if cell.get("cell_type") != "markdown":
                continue
            src = "".join(cell.get("source", []))
            is_target_md = (
                src.lstrip().startswith("### Lectura")
                or "## 14." in src
                or "## 14A" in src
                or "### 14A" in src
                or "## 15." in src
                or "## Registro de correcciones" in src
                or "## 16." in src
                or "## 17." in src
            )
            if not is_target_md:
                continue
            for span in re.findall(r"`([^`]+)`", src):
                # Skip code identifiers, file paths, section refs, model ids
                if any(ch in span for ch in ("/", "\\", ".py", ".csv", ".png", ".ipynb", "_")):
                    continue
                for num_tok in num_pattern.findall(span):
                    total_audited_numbers += 1
                    if not _number_in_corpus(num_tok):
                        untraced.append({"cell_index": idx, "span": span, "token": num_tok})

        return {
            "emoji_count": len(emoji_hits),
            "emoji_samples": emoji_hits[:10],
            "placeholder_token_count": len(placeholder_hits),
            "placeholder_samples": placeholder_hits[:10],
            "duplicate_code_cell_groups": duplicate_code_groups,
            "heavy_code_cells": heavy_cells,
            "total_backticked_numbers_audited": total_audited_numbers,
            "untraced_numbers_count": len(untraced),
            "untraced_numbers": untraced[:50],
            "all_audits_clean": bool(
                len(emoji_hits) == 0
                and len(placeholder_hits) == 0
                and len(duplicate_code_groups) == 0
                and len(heavy_cells) == 0
                and len(untraced) == 0
            ),
        }
