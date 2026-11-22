"""SOLID orchestrator for Notebook 7.1 (Naive Bayes), table exports, decision log, and SHA-256 verification."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import psutil

from scripts.ScriptsCsv.EDA.validation import FileFingerprint
from scripts.ScriptsCsv.Modelado.pipeline import ModelingPipeline

from .bayes_by_counting import ManualBayesCounter, ManualBayesResult
from .config import MODEL_NB_B, MODEL_NB_G, MODEL_NB_H, NaiveBayesConfig, VERSION_CON
from .evaluation import NaiveBayesEvaluationBundle, NaiveBayesEvaluator
from .feature_blocks import NaiveBayesFeatureBuilder, NaiveBayesVersionBundle
from .occupation_analysis import OccupationAnalysisBundle, OccupationPatternAnalyzer
from .outlier_diagnostics import (
    OutlierDiagnosticsAnalyzer,
    OutlierDiagnosticsBundle,
    TunedOutlierExperimentsBundle,
)
from .patterns import GeneralPatternAnalyzer, GeneralPatternsBundle
from .plots import NaiveBayesPlotter
from .version_comparison import VersionABComparator, VersionComparisonBundle


def current_process_rss_mb() -> float:
    """Return current resident set size (RSS) memory of the Python process in MB."""
    proc = psutil.Process(os.getpid())
    return round(float(proc.memory_info().rss) / (1024.0 * 1024.0), 2)


class NaiveBayesPipeline:
    """Orchestrate all stages of Notebook 7.1 with dependency injection."""

    def __init__(
        self,
        config: NaiveBayesConfig,
        feature_builder: NaiveBayesFeatureBuilder | None = None,
        manual_counter: ManualBayesCounter | None = None,
        outlier_analyzer: OutlierDiagnosticsAnalyzer | None = None,
        evaluator: NaiveBayesEvaluator | None = None,
        occupation_analyzer: OccupationPatternAnalyzer | None = None,
        patterns_analyzer: GeneralPatternAnalyzer | None = None,
        version_comparator: VersionABComparator | None = None,
        plotter: NaiveBayesPlotter | None = None,
        modeling_pipeline: ModelingPipeline | None = None,
    ) -> None:
        self.config = config
        self.feature_builder = feature_builder or NaiveBayesFeatureBuilder(config)
        self.manual_counter = manual_counter or ManualBayesCounter()
        self.outlier_analyzer = outlier_analyzer or OutlierDiagnosticsAnalyzer(config)
        self.evaluator = evaluator or NaiveBayesEvaluator(config)
        self.occupation_analyzer = occupation_analyzer or OccupationPatternAnalyzer(config)
        self.patterns_analyzer = patterns_analyzer or GeneralPatternAnalyzer(config)
        self.version_comparator = version_comparator or VersionABComparator(
            config, self.feature_builder
        )
        self.plotter = plotter or NaiveBayesPlotter(config)
        self.modeling_pipeline = modeling_pipeline or ModelingPipeline(
            config.to_modeling_config()
        )
        self.config.tables_dir.mkdir(parents=True, exist_ok=True)
        self.config.figures_dir.mkdir(parents=True, exist_ok=True)

    def snapshot_inputs(self) -> Dict[str, FileFingerprint]:
        """Record initial SHA-256 fingerprints of all upstream input files via ModelingPipeline."""
        return self.modeling_pipeline.snapshot_inputs()

    def verify_inputs(self, before: Dict[str, FileFingerprint]) -> pd.DataFrame:
        """Verify at the end of execution that all upstream input files remain untouched."""
        df_ver = self.modeling_pipeline.verify_inputs(before)
        if not bool(df_ver["sin_cambios"].all()):
            raise AssertionError("SHA-256 input integrity check failed: an upstream file was modified!")
        return df_ver

    def build_decision_log(
        self,
        bundle_a_checks: Dict[str, object],
        manual_res: ManualBayesResult,
        outlier_bundle: OutlierDiagnosticsBundle,
        eval_bundle: NaiveBayesEvaluationBundle,
        occ_bundle: OccupationAnalysisBundle,
        pat_bundle: GeneralPatternsBundle,
        vcomp_bundle: VersionComparisonBundle,
        tuned_outlier_bundle: TunedOutlierExperimentsBundle | None = None,
    ) -> pd.DataFrame:
        """Build the traceable Spanish decision log from real executed metrics."""
        win_df = eval_bundle.tuning_winners_table.set_index("modelo_id")
        te_df = eval_bundle.test_metrics_table

        def _get_test_row(mid: str) -> pd.Series:
            return te_df.loc[
                (te_df["modelo_id"] == mid) & (te_df["punto_operacion"].str.contains("OOF"))
            ].iloc[0]

        te_g = _get_test_row(MODEL_NB_G)
        te_b = _get_test_row(MODEL_NB_B)
        te_h = _get_test_row(MODEL_NB_H)

        o1_top = occ_bundle.o1_rates_table.iloc[0]
        o1_bot = occ_bundle.o1_rates_table.iloc[-1]
        p7_df = pat_bundle.p7_block_ablation_cv_table
        p8_df = pat_bundle.p8_independence_audit_cv_table
        diff_b = vcomp_bundle.differences_summary_table

        # Extract paired CI summaries if available
        paired_df = eval_bundle.paired_bootstrap_comparisons_table
        paired_h_b_txt = ""
        paired_h_log_txt = ""
        if not paired_df.empty:
            r_hb = paired_df.loc[paired_df["comparacion_A_menos_B"] == "NB-H vs. NB-B"]
            if not r_hb.empty:
                paired_h_b_txt = (
                    f" Delta PR-AUC pareado NB-H vs. NB-B={float(r_hb.iloc[0]['delta_pr_auc']):+.4f} "
                    f"IC 95 % {r_hb.iloc[0]['ic95_delta_pr_auc']}."
                )
            r_hl = paired_df.loc[paired_df["comparacion_A_menos_B"].str.contains("Logística")]
            if not r_hl.empty:
                paired_h_log_txt = (
                    f" Frente a Logística 6.0 (2,981 cols): Delta PR-AUC={float(r_hl.iloc[0]['delta_pr_auc']):+.4f} "
                    f"IC 95 % {r_hl.iloc[0]['ic95_delta_pr_auc']}, "
                    f"Delta ROC-AUC={float(r_hl.iloc[0]['delta_roc_auc']):+.4f} "
                    f"IC 95 % {r_hl.iloc[0]['ic95_delta_roc_auc']}."
                )

        e2_txt = ""
        if tuned_outlier_bundle is not None and not tuned_outlier_bundle.e2_paired_diff_table.empty:
            r_e2h = tuned_outlier_bundle.e2_paired_diff_table.loc[
                tuned_outlier_bundle.e2_paired_diff_table["modelo_id"] == MODEL_NB_H
            ]
            if not r_e2h.empty:
                e2_txt = (
                    f" En E2 (winsorización Tukey de las 7 continuas en RAM), NB-H cambia en "
                    f"Delta PR-AUC={float(r_e2h.iloc[0]['delta_pr_auc']):+.4f} "
                    f"IC 95 % {r_e2h.iloc[0]['ic95_delta_pr_auc']}."
                )

        rows = [
            {
                "id_decision": "NB-01",
                "etapa": "Alcance y partición de datos",
                "decision": "Desarrollo principal sobre Versión A (con_outliers) y partición agrupada por resume_id",
                "evidencia_cuantitativa": (
                    f"Train={bundle_a_checks['train_rows']:,} filas ({bundle_a_checks['train_persons']:,} personas), "
                    f"Test={bundle_a_checks['test_rows']:,} filas ({bundle_a_checks['test_persons']:,} personas), "
                    f"{bundle_a_checks['overlapping_persons']} personas solapadas y 0 columnas con fuga."
                ),
                "justificacion_metodologica": (
                    "La Versión A preserva todas las observaciones sin recortes previos; la sensibilidad a colas "
                    "se evalúa de forma controlada en el Paso 12 mediante E1 (exclusión ajustada), E2 (winsorización "
                    "de las 7 continuas en RAM), E3 (var_smoothing x variante) y la Versión B (recorte IQR en 4 columnas)."
                ),
            },
            {
                "id_decision": "NB-02",
                "etapa": "Restricciones de scikit-learn y arquitectura de modelos",
                "decision": "Descarte de MultinomialNB/CategoricalNB y diseño de tres variantes (NB-G, NB-B y HybridNaiveBayes NB-H)",
                "evidencia_cuantitativa": (
                    f"La matriz densa completa exigiría ~16.6 GB; NB-H materializa en denso solo las 10 cols continuas/ordinales "
                    f"({te_h['memoria_matriz_train_mb']:.2f} MB totales con CSR). Diferencia manual vs BernoulliNB = {manual_res.max_abs_diff_vs_sklearn:.2e}."
                ),
                "justificacion_metodologica": (
                    "GaussianNB no acepta matrices dispersas y BernoulliNB exige entradas estrictamente binarias (0/1); "
                    "NB-H suma log-verosimilitudes de ambos bloques restando una vez log(pi_c)."
                ),
            },
            {
                "id_decision": "NB-03",
                "etapa": "Tratamiento de variables ordinales en NB-H y auditoría casi constantes",
                "decision": "Inclusión de univ_ord_mm, dur_q_bin y n_skills_essential_bin en el submodelo Gaussiano (10 cols) y prueba NB-G* en Pasos 5–6",
                "evidencia_cuantitativa": (
                    f"En la auditoría P8, retirar los dos bins duplicados (dur_q_bin y n_skills_essential_bin) cambia el PR-AUC CV "
                    f"de NB-H en {float(p8_df.iloc[8]['NB_H_delta_pr_auc']):+.4f} y de NB-G en {float(p8_df.iloc[8]['NB_G_delta_pr_auc']):+.4f}. "
                    f"En Paso 6, NB-G* (sin columnas binarias/ordinales < 1 %) cambia PR-AUC CV en {float(eval_bundle.grid_sizes['nb_g_star_delta_pr_auc_cv']):+.5f}."
                ),
                "justificacion_metodologica": (
                    "Se documenta como supuesto débil tratar ordinales discretas como gaussianas y se audita el efecto "
                    "tanto del doble conteo como de las columnas binarias casi constantes."
                ),
            },
            {
                "id_decision": "NB-04",
                "etapa": "Diagnóstico de outliers dentro de Versión A (Paso 4 y Paso 12 E1–E3)",
                "decision": "Separación entre sensibilidad sin ajustar (confundida por var_smoothing=1e-9) y experimentos ajustados E1, E2 y E3",
                "evidencia_cuantitativa": (
                    f"{outlier_bundle.subset_summary['pct_train_extremes']:.2f}% de las filas de train tienen algún extremo Tukey "
                    f"(prevalencia {outlier_bundle.subset_summary['prevalencia_train_extremes_pct']:.2f}% vs "
                    f"{outlier_bundle.subset_summary['prevalencia_train_inliers_pct']:.2f}% en inliers). "
                    f"En NB-G sin ajustar en test: {outlier_bundle.subset_summary['nb_g_sin_ajustar_pct_prob_gt_095_test']:.2f}% > 0.95 y "
                    f"{outlier_bundle.subset_summary['nb_g_sin_ajustar_pct_prob_lt_005_test']:.2f}% < 0.05."
                ),
                "justificacion_metodologica": (
                    "El experimento de Paso 4 con var_smoothing=1e-9 mezcla el efecto de colas con la degeneración de NB-G; "
                    "por eso las conclusiones sobre outliers se sustentan en E1, E2 y E3 tras el ajuste de hiperparámetros."
                ),
            },
            {
                "id_decision": "NB-05",
                "etapa": "Ajuste honesto de hiperparámetros y umbral OOF (Pasos 6 y 7)",
                "decision": "Selección por PR-AUC medio en StratifiedGroupKFold (5 folds) y umbral tau* que maximiza F1 en OOF train",
                "evidencia_cuantitativa": (
                    f"Ganadores CV: NB-G (vs={win_df.loc[MODEL_NB_G, 'var_smoothing_optimo']:g}, PR-AUC={win_df.loc[MODEL_NB_G, 'pr_auc_cv_media']:.4f}, tau*={win_df.loc[MODEL_NB_G, 'umbral_oof_optimo_tau']:.3f}), "
                    f"NB-B (alpha={win_df.loc[MODEL_NB_B, 'alpha_optimo']}, PR-AUC={win_df.loc[MODEL_NB_B, 'pr_auc_cv_media']:.4f}, tau*={win_df.loc[MODEL_NB_B, 'umbral_oof_optimo_tau']:.3f}), "
                    f"NB-H (vs={win_df.loc[MODEL_NB_H, 'var_smoothing_optimo']:g}, alpha={win_df.loc[MODEL_NB_H, 'alpha_optimo']}, PR-AUC={win_df.loc[MODEL_NB_H, 'pr_auc_cv_media']:.4f}, tau*={win_df.loc[MODEL_NB_H, 'umbral_oof_optimo_tau']:.3f})."
                ),
                "justificacion_metodologica": (
                    "El umbral de decisión jamás se elige mirando test; usar predicciones OOF corrige el sesgo del umbral "
                    "fijo 0.50 bajo desbalanceo 30/70."
                ),
            },
            {
                "id_decision": "NB-06",
                "etapa": "Evaluación única en Test A y comparaciones homogéneas con 6.0 (Pasos 8, 9 y 11)",
                "decision": "Adopción de NB-H como variante principal de Naive Bayes con comparaciones homogéneas, IC 95 % pareados e igual tasa de alerta",
                "evidencia_cuantitativa": (
                    f"En Test A: NB-H logra PR-AUC={te_h['pr_auc_test']:.4f} {te_h['pr_auc_ic95']}, "
                    f"ROC-AUC={te_h['roc_auc_test']:.4f} {te_h['roc_auc_ic95']} y F1={te_h['f1_clase_1_test']:.4f} {te_h['f1_clase_1_ic95']}."
                    f"{paired_h_b_txt}{paired_h_log_txt}"
                ),
                "justificacion_metodologica": (
                    "Solo se comparan modelos sobre el mismo espacio de variables (denso vs. denso; ocupación vs. ocupación), "
                    "se evita comparar Brier contra modelos con class_weight='balanced' y se aplica criterio estricto de IC 95 % pareado."
                ),
            },
            {
                "id_decision": "NB-07",
                "etapa": "Patrones por grupo ocupacional y ablación de bloques (Paso 10)",
                "decision": "Caracterización en unidades originales con soporte >= 200, tasas train/test en todos los subgrupos y advertencia de huella N:1",
                "evidencia_cuantitativa": (
                    f"Rango ISCO en train: desde {o1_top['gran_grupo_isco']} ({o1_top['tasa_observada_train_pct']:.2f}%) "
                    f"hasta {o1_bot['gran_grupo_isco']} ({o1_bot['tasa_observada_train_pct']:.2f}%). "
                    f"En P7, retirar Duración y carrera reduce PR-AUC CV en {float(p7_df.iloc[2]['cambio_pr_auc_vs_completo']):+.4f} "
                    f"y retirar Ocupación OHE lo cambia en {float(p7_df.iloc[5]['cambio_pr_auc_vs_completo']):+.4f}."
                ),
                "justificacion_metodologica": (
                    "Las diferencias entre grupos ocupacionales y oficios describen asociaciones sujetas a regresión a la media "
                    "en soportes pequeños, nunca relaciones causales."
                ),
            },
            {
                "id_decision": "NB-08",
                "etapa": "Sensibilidad a outliers E1–E3 y Versión B (Paso 12)",
                "decision": "Evaluación controlada de E1, E2, E3 y Versión B (que solo recorta 4 columnas según IQR_WINSOR_BOUNDS_INFO, 2 de ellas en X)",
                "evidencia_cuantitativa": (
                    f"Versión B menos Versión A (Train B con hiperparámetros fijos de A): "
                    f"Delta PR-AUC NB-G={float(diff_b.loc[(diff_b['modelo_id']==MODEL_NB_G) & diff_b['comparacion'].str.contains('Train B'), 'delta_pr_auc'].iloc[0]):+.4f}, "
                    f"NB-B={float(diff_b.loc[(diff_b['modelo_id']==MODEL_NB_B) & diff_b['comparacion'].str.contains('Train B'), 'delta_pr_auc'].iloc[0]):+.4f}, "
                    f"NB-H={float(diff_b.loc[(diff_b['modelo_id']==MODEL_NB_H) & diff_b['comparacion'].str.contains('Train B'), 'delta_pr_auc'].iloc[0]):+.4f}.{e2_txt}"
                ),
                "justificacion_metodologica": (
                    "La Versión B no recorta dur_q ni job_order; E2 y E3 prueban directamente el recorte de las 7 continuas "
                    "y la interacción entre var_smoothing y el tratamiento de colas."
                ),
            },
        ]
        return pd.DataFrame(rows)

    def export_all_tables(
        self,
        bundle_a_audit_df: pd.DataFrame,
        corr_pairs_df: pd.DataFrame,
        manual_res: ManualBayesResult,
        outlier_bundle: OutlierDiagnosticsBundle,
        eval_bundle: NaiveBayesEvaluationBundle,
        occ_bundle: OccupationAnalysisBundle,
        pat_bundle: GeneralPatternsBundle,
        vcomp_bundle: VersionComparisonBundle,
        decision_log_df: pd.DataFrame,
        near_constant_audit_df: pd.DataFrame | None = None,
        tuned_outlier_bundle: TunedOutlierExperimentsBundle | None = None,
    ) -> pd.DataFrame:
        """Persist all CSV tables in reports/naive_bayes_jobpath/tables/ with UTF-8 encoding."""
        tables_to_save: Dict[str, pd.DataFrame] = {
            "01_bayes_manual_comparacion.csv": manual_res.comparison_table,
            "02_auditoria_variables_y_bloques_nb.csv": bundle_a_audit_df,
            "03_pares_correlacionados_bloque_denso.csv": corr_pairs_df,
            "04a_diagnostico_distribucion_tukey_train_a.csv": outlier_bundle.distribution_table,
            "04b_experimento_sensibilidad_outliers_en_a.csv": outlier_bundle.sensitivity_experiment_table,
            "04c_alcance_version_b_cotas_iqr.csv": outlier_bundle.version_b_bounds_table,
            "04d_desplazamiento_parametros_gaussianos_a.csv": outlier_bundle.parameter_shift_table,
            "05_baseline_cv_por_persona.csv": eval_bundle.baseline_cv_table,
            "06a_tuning_todos_los_intentos_cv.csv": eval_bundle.tuning_all_attempts_table,
            "06b_tuning_ganadores_cv.csv": eval_bundle.tuning_winners_table,
            "07_umbral_oof_train.csv": eval_bundle.oof_threshold_summary_table,
            "08a_resultados_test_version_a_ic95.csv": eval_bundle.test_metrics_table,
            "08b_matrices_confusion_test_a.csv": eval_bundle.confusion_matrices_table,
            "09_calibracion_resumen_test_a.csv": eval_bundle.calibration_summary_table,
            "10_o1_tasas_reincidencia_isco_1d.csv": occ_bundle.o1_rates_table,
            "10_o2_desempeno_modelos_por_isco_1d.csv": occ_bundle.o2_performance_by_isco_table,
            "10_o3a_heatmap_contribuciones_log_odds_isco.csv": occ_bundle.o3_log_odds_heatmap_df,
            "10_o3b_diferencias_unidades_originales_isco.csv": occ_bundle.o3_original_units_diff_table,
            "10_o4_perfil_unidades_originales_por_isco.csv": occ_bundle.o4_profile_by_group_table,
            "10_o5a_subgrupos_isco_2d_extremos.csv": occ_bundle.o5_subgroups_2d_table,
            "10_o5b_ocupaciones_esco_4d_extremos.csv": occ_bundle.o5_occupations_4d_table,
            "10_o6_persistencia_transiciones_vs_prob_isco.csv": occ_bundle.o6_transitions_persistence_table,
            "10_p1a_evidencia_llr_variables_continuas.csv": pat_bundle.p1_continuous_evidence_table,
            "10_p1b_evidencia_llr_variables_binarias.csv": pat_bundle.p1_binary_evidence_table,
            "10_p1c_participacion_bloques_log_odds_test.csv": pat_bundle.p1_block_log_odds_share_test_table,
            "10_p2_descomposicion_aditiva_perfiles.csv": pat_bundle.p2_profiles_summary_table,
            "10_p3a_deciles_riesgo_lift_gain.csv": pat_bundle.p3_deciles_table,
            "10_p3b_perfil_decil_superior_vs_inferior.csv": pat_bundle.p3_top_vs_bottom_profile_table,
            "10_p3c_composicion_isco_deciles_extremos.csv": pat_bundle.p3_isco_composition_deciles_table,
            "10_p4a_tasas_por_orden_empleo.csv": pat_bundle.p4_job_order_table,
            "10_p4b_tasas_por_anio_inicio.csv": pat_bundle.p4_start_year_table,
            "10_p4c_resumen_pendiente_job_order.csv": pat_bundle.p4_job_order_slope_summary_table,
            "10_p5_desempeno_por_nivel_educativo.csv": pat_bundle.p5_education_table,
            "10_p6a_perfiles_errores_confusion.csv": pat_bundle.p6_error_profiles_table,
            "10_p6b_errores_por_subgrupo.csv": pat_bundle.p6_error_subgroups_table,
            "10_p7_ablacion_bloques_comportamiento_cv.csv": pat_bundle.p7_block_ablation_cv_table,
            "10_p8_auditoria_independencia_pares_cv.csv": pat_bundle.p8_independence_audit_cv_table,
            "11_comparacion_final_version_a_referencias_y_arboles.csv": eval_bundle.final_comparison_table_a,
            "11a_reproduccion_baselines_6_0.csv": eval_bundle.phase4_reproduction_table,
            "11b_comparacion_homogenea_denso_14cols.csv": eval_bundle.like_for_like_dense_table,
            "11c_comparacion_homogenea_con_ocupacion.csv": eval_bundle.like_for_like_occ_table,
            "11d_bootstrap_pareado_diferencias_ic95.csv": eval_bundle.paired_bootstrap_comparisons_table,
            "11e_comparacion_igual_tasa_alerta.csv": eval_bundle.equal_alert_rate_table,
            "12a_comparacion_sensibilidad_version_a_vs_b.csv": vcomp_bundle.comparison_table,
            "12b_diferencias_absolutas_b_menos_a.csv": vcomp_bundle.differences_summary_table,
            "12g_e3_regularizacion_por_variante_cv.csv": vcomp_bundle.e3_pivot_summary_table,
            "decision_log_naive_bayes.csv": decision_log_df,
        }
        if near_constant_audit_df is not None:
            tables_to_save["02b_auditoria_casi_constantes.csv"] = near_constant_audit_df
        if tuned_outlier_bundle is not None:
            tables_to_save["12c_e1_sensibilidad_ajustada_en_a.csv"] = (
                tuned_outlier_bundle.e1_tuned_sensitivity_table
            )
            tables_to_save["12d_e2_vallas_tukey_train_7_continuas.csv"] = (
                tuned_outlier_bundle.e2_tukey_fences_table
            )
            tables_to_save["12e_e2_winsorizacion_tukey_7_continuas.csv"] = (
                tuned_outlier_bundle.e2_winsorization_table
            )
            tables_to_save["12f_e2_bootstrap_pareado_wins_vs_a.csv"] = (
                tuned_outlier_bundle.e2_paired_diff_table
            )

        inventory_rows: List[Dict[str, object]] = []
        for fname, df in tables_to_save.items():
            out_path = self.config.tables_dir / fname
            df.to_csv(out_path, index=False, encoding="utf-8")
            size_kb = round(float(out_path.stat().st_size) / 1024.0, 2)
            inventory_rows.append(
                {
                    "archivo_tabla": fname,
                    "filas": int(len(df)),
                    "columnas": int(df.shape[1]),
                    "tamano_kb": size_kb,
                    "ruta_relativa": f"reports/naive_bayes_jobpath/tables/{fname}",
                }
            )
        return pd.DataFrame(inventory_rows)
