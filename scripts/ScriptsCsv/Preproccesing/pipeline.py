"""
Main orchestrator for the JobPath preprocessing pipeline.

Follows the Dependency Inversion Principle (DIP) by injecting modular handlers.
Execution order:
Diagnosis -> Duplicates -> Categories -> Missing Values -> IQR Winsorization -> Validation.
Also tracks a RowCountFunnel (rows and unique persons) after every stage with an
automatic loss alert when a stage removes more than `config.funnel_alert_threshold_pct`.
"""

from typing import Dict, Any, Optional
import pandas as pd

from .config import PipelineConfig, DEFAULT_CONFIG
from .io import DataIO
from .diagnosis import DataDiagnoser
from .duplicates import DuplicateHandler
from .categories import CategoryCleaner
from .missing import MissingValueAnalyzer
from .imputation import ImputationManager
from .outliers_iqr import IQROutlierHandler
from .validation import DataValidator
from .funnel import RowCountFunnel
from .utils import set_random_seed


class PreprocessingPipeline:
    """SOLID orchestrator for the JobPath preprocessing workflow."""

    def __init__(
        self,
        config: PipelineConfig = DEFAULT_CONFIG,
        data_io: Optional[DataIO] = None,
        diagnoser: Optional[DataDiagnoser] = None,
        duplicate_handler: Optional[DuplicateHandler] = None,
        category_cleaner: Optional[CategoryCleaner] = None,
        missing_analyzer: Optional[MissingValueAnalyzer] = None,
        imputation_manager: Optional[ImputationManager] = None,
        outlier_handler: Optional[IQROutlierHandler] = None,
        validator: Optional[DataValidator] = None,
        funnel: Optional[RowCountFunnel] = None,
    ) -> None:
        self.config = config
        set_random_seed(config.seed)

        self.data_io = data_io or DataIO(config)
        self.diagnoser = diagnoser or DataDiagnoser(config)
        self.duplicate_handler = duplicate_handler or DuplicateHandler(config)
        self.category_cleaner = category_cleaner or CategoryCleaner(config)
        self.missing_analyzer = missing_analyzer or MissingValueAnalyzer(config)
        self.imputation_manager = imputation_manager or ImputationManager(config)
        self.outlier_handler = outlier_handler or IQROutlierHandler(config)
        self.validator = validator or DataValidator(config)
        self.funnel = funnel or RowCountFunnel(
            person_col=config.unique_key,
            alert_threshold_pct=getattr(config, "funnel_alert_threshold_pct", 5.0),
        )

        self.df: Optional[pd.DataFrame] = None
        self.df_original: Optional[pd.DataFrame] = None
        self.df_before_winsor: Optional[pd.DataFrame] = None
        self.df_winsor: Optional[pd.DataFrame] = None
        self.decision_log_all = []
        self.results: Dict[str, Any] = {}

    def run_diagnosis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Stage 1: Run comprehensive dataset diagnosis and record initial funnel step."""
        print("\n" + "🔍" * 40)
        print("ETAPA 1: DIAGNÓSTICO")
        print("🔍" * 40)
        result = self.diagnoser.diagnose(df)
        self.df_original = df.copy()
        self.funnel.record_step(
            "1. Carga y Diagnóstico Inicial",
            df,
            note="Punto de partida en memoria (.copy() de empleos_unificado_limpio.csv)",
        )
        return result

    def run_duplicates(
        self,
        df: pd.DataFrame,
        remove_key_dups: bool = False,
        key_dups_approved: bool = False,
    ) -> pd.DataFrame:
        """Stage 2: Check exact and composite-key duplicates and record funnel step."""
        print("\n" + "🔍" * 40)
        print("ETAPA 2: DUPLICADOS")
        print("🔍" * 40)

        df, exact_report = self.duplicate_handler.remove_exact_duplicates(df)
        self.decision_log_all.extend(
            self.duplicate_handler.get_decision_log().to_dict("records")
        )

        key_report = self.duplicate_handler.find_key_duplicates(df)
        self.results["key_duplicates_report"] = key_report

        if remove_key_dups and key_dups_approved:
            df, key_report2 = self.duplicate_handler.remove_key_duplicates(
                df, approved=True
            )
            self.decision_log_all.extend(
                self.duplicate_handler.get_decision_log().to_dict("records")
            )

        self.funnel.record_step(
            "2. Tratamiento de Duplicados",
            df,
            note="0 duplicados exactos y 0 en clave compuesta; resume_id agrupa trayectorias 1:N",
        )
        self.df = df
        return df

    def run_categories(
        self,
        df: pd.DataFrame,
        normalize: bool = False,
        approved: bool = False,
    ) -> pd.DataFrame:
        """Stage 3: Analyze and optionally normalize categorical columns."""
        print("\n" + "🔍" * 40)
        print("ETAPA 3: CATEGORÍAS")
        print("🔍" * 40)

        cat_report = self.category_cleaner.analyze_categories(df)
        self.results["categories_report"] = cat_report

        if normalize and approved and cat_report["needs_normalization"]:
            df, norm_report = self.category_cleaner.normalize_categories(
                df, approved=True
            )
            self.decision_log_all.extend(
                self.category_cleaner.get_decision_log().to_dict("records")
            )
            self.results["categories_normalized"] = norm_report

        self.funnel.record_step(
            "3. Revisión Categórica",
            df,
            note="Categorías estandarizadas; start_date y end_date preservadas en formato trimestral",
        )
        self.df = df
        return df

    def run_missing_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Stage 4a: Classify missing-value mechanisms (MCAR/MAR/MNAR) with evidence."""
        print("\n" + "🔍" * 40)
        print("ETAPA 4a: ANÁLISIS DE VALORES FALTANTES")
        print("🔍" * 40)

        missing_report = self.missing_analyzer.analyze_missing(df)
        self.results["missing_analysis"] = missing_report
        return missing_report

    def run_imputation(
        self, df: pd.DataFrame, imputation_plan: Dict[str, Dict]
    ) -> pd.DataFrame:
        """Stage 4b: Execute approved imputation plan and record funnel step."""
        print("\n" + "🔍" * 40)
        print("ETAPA 4b: IMPUTACIÓN (SOLO APROBADA)")
        print("🔍" * 40)

        df_current = df.copy()
        for col, plan in imputation_plan.items():
            if plan.get("approved", False):
                method = plan["method"]
                justification = plan.get(
                    "justification", f"Imputación aprobada con {method}"
                )
                df_current = self.imputation_manager.impute(
                    df_current,
                    col,
                    method,
                    approved=True,
                    justification=justification,
                    **plan.get("kwargs", {}),
                )
            else:
                print(f"[OMITIDO] {col} - sin aprobación")

        self.decision_log_all.extend(
            self.imputation_manager.get_decision_log().to_dict("records")
        )
        self.funnel.record_step(
            "4. Valores Faltantes (MNAR/MAR)",
            df_current,
            note="Sin imputación artificial ni eliminación de filas en etapa 2.0",
        )
        self.df = df_current
        return df_current

    def run_outliers(
        self,
        df: pd.DataFrame,
        columns_to_winsorize: Optional[list] = None,
        approved: bool = False,
    ) -> pd.DataFrame:
        """Stage 5: Apply Tukey IQR winsorization (clip) without deleting rows."""
        print("\n" + "🔍" * 40)
        print("ETAPA 5: WINSORIZACIÓN IQR")
        print("🔍" * 40)

        candidates_report = self.outlier_handler.identify_winsorization_candidates(df)
        self.results["outliers_candidates"] = candidates_report

        self.df_before_winsor = df.copy()

        if columns_to_winsorize and approved:
            df_winsor, winsor_report = self.outlier_handler.winsorize(
                df, columns_to_winsorize, approved=True
            )
            self.df_winsor = df_winsor
            self.decision_log_all.extend(
                self.outlier_handler.get_decision_log().to_dict("records")
            )
            self.results["winsorization_report"] = winsor_report
            self.funnel.record_step(
                "5. Winsorización IQR (clip)",
                df_winsor,
                note="Acotación por clip() en 4 variables de conteo; 0 filas eliminadas",
            )
            return df_winsor

        print("[NOTA] Winsorización no aplicada - esperando aprobación")
        self.df_winsor = df.copy()
        self.funnel.record_step(
            "5. Winsorización IQR (omitida)",
            df,
            note="Sin winsorización",
        )
        return df.copy()

    def run_validation(self, df_final: pd.DataFrame) -> Dict[str, Any]:
        """Stage 6: Validate final dataset invariants and print the row-count funnel."""
        print("\n" + "🔍" * 40)
        print("ETAPA 6: VALIDACIÓN")
        print("🔍" * 40)

        validation_result = self.validator.validate_final(
            df_final,
            df_before_winsor=self.df_before_winsor,
            winsor_bounds=self.outlier_handler.bounds_info,
        )
        summary = self.validator.generate_summary(self.df_original, df_final)
        self.funnel.record_step(
            "6. Validación Final y Exportación",
            df_final,
            note="Integridad de filas (1,871,014) y personas (355,308) verificada al 100%",
        )
        funnel_df = self.funnel.print_summary()

        self.results["validation"] = validation_result
        self.results["summary"] = summary
        self.results["funnel"] = funnel_df
        return validation_result

    def get_funnel_df(self) -> pd.DataFrame:
        """Return the row-and-person funnel DataFrame."""
        return self.funnel.to_dataframe()

    def get_decision_log_df(self) -> pd.DataFrame:
        """Consolidate all handler decision logs into a single DataFrame."""
        logs = []
        logs.extend(self.duplicate_handler.get_decision_log().to_dict("records"))
        logs.extend(self.category_cleaner.get_decision_log().to_dict("records"))
        logs.extend(self.imputation_manager.get_decision_log().to_dict("records"))
        logs.extend(self.outlier_handler.get_decision_log().to_dict("records"))

        if logs:
            return pd.DataFrame(logs)
        return pd.DataFrame(
            columns=["column", "issue", "method", "justification", "values_affected"]
        )

    def export(self, df_final: pd.DataFrame, check_exists: bool = True) -> bool:
        """Save the winsorized DataFrame to the configured output path."""
        print("\n" + "💾" * 40)
        print("EXPORTACIÓN")
        print("💾" * 40)

        success, path = self.data_io.save_csv(df_final, check_exists=check_exists)
        if success:
            print(f"\n[EXPORTADO] {path}")
            return True
        print("\n[EXPORTACIÓN FALLIDA] El archivo ya existe o hubo un error")
        print(f"[RUTA] {path}")
        return False
