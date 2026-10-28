"""
Módulo de análisis de valores faltantes.

Clasifica los valores faltantes como MCAR/MAR/MNAR con evidencia.
SIEMPRE solicita confirmación antes de aplicar imputación.
Para MNAR: crea columna indicadora, avisa, NO imputa.
"""

from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

from .config import PipelineConfig, DEFAULT_CONFIG


class MissingValueAnalyzer:
    """Analiza valores faltantes y clasifica como MCAR/MAR/MNAR."""
    
    def __init__(self, config: PipelineConfig = DEFAULT_CONFIG):
        self.config = config
        self.analysis_results = {}
    
    def analyze_missing(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analiza todas las columnas con valores faltantes.
        Proporciona evidencia para clasificación MCAR/MAR/MNAR.
        """
        print("=" * 80)
        print("ANÁLISIS DE VALORES FALTANTES")
        print("=" * 80)
        
        null_counts = df.isna().sum()
        null_cols = null_counts[null_counts > 0].index.tolist()
        
        print(f"\n[COLUMNAS CON NULOS] {len(null_cols)}")
        for col in null_cols:
            count = null_counts[col]
            pct = count / len(df) * 100
            print(f"  - {col}: {count} ({pct:.2f}%)")
        
        results = {
            'columns_with_nulls': null_cols,
            'analysis': {}
        }
        
        for col in null_cols:
            print(f"\n{'='*60}")
            print(f"ANALIZANDO: {col}")
            print(f"{'='*60}")
            
            analysis = self._analyze_single_column(df, col)
            results['analysis'][col] = analysis
            
            print(f"\n[CONTEO NULOS] {analysis['null_count']} ({analysis['null_percent']:.2f}%)")
            print(f"\n[EVIDENCIA]")
            for ev in analysis['evidence']:
                print(f"  - {ev}")
            if 'suggestion' in analysis:
                print(f"\n[SUGERENCIA] {analysis['suggestion']}")
            print(f"[CLASIFICACIÓN] {analysis['classification']}")
            print(f"[JUSTIFICACIÓN] {analysis['justification']}")
            if analysis['classification'] == 'MNAR':
                print(f"\n[ADVERTENCIA - MNAR] Se creará columna indicadora, NO se imputará")
            else:
                print(f"\n[ESTRATEGIA PROPUESTA] {analysis.get('proposed_strategy', 'Revisar con confirmación')}")
            print(f"[REQUIERE CONFIRMACIÓN] SÍ")
        
        print("\n" + "=" * 80)
        print("ANÁLISIS COMPLETO - ESPERANDO CONFIRMACIÓN POR COLUMNA")
        print("=" * 80)
        
        self.analysis_results = results
        return results
    
    def _analyze_single_column(self, df: pd.DataFrame, col: str) -> Dict[str, Any]:
        """Analiza una columna individual con valores faltantes."""
        null_mask = df[col].isna()
        null_count = null_mask.sum()
        null_percent = null_count / len(df) * 100
        
        evidence = []
        classification = 'DESCONOCIDO'
        justification = ''
        proposed_strategy = ''
        
        df_temp = df.copy()
        df_temp[f'_missing_{col}'] = null_mask.astype(int)
        
        numeric_cols = df_temp.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [c for c in numeric_cols if c != col and not c.startswith('_missing_')]
        
        if numeric_cols:
            for num_col in numeric_cols[:5]:
                try:
                    mean_missing = df_temp[null_mask][num_col].mean()
                    mean_not_missing = df_temp[~null_mask][num_col].mean()
                    if not pd.isna(mean_missing) and not pd.isna(mean_not_missing):
                        if abs(mean_missing - mean_not_missing) / (abs(mean_not_missing) + 1e-10) > 0.1:
                            evidence.append(f"Difiere por {num_col}: faltantes={mean_missing:.2f}, no faltantes={mean_not_missing:.2f}")
                except Exception:
                    pass
        
        cat_cols = df_temp.select_dtypes(include=['object']).columns.tolist()
        cat_cols = [c for c in cat_cols if c != col]
        
        if cat_cols:
            for cat_col in cat_cols[:3]:
                try:
                    crosstab = pd.crosstab(df_temp[cat_col], df_temp[f'_missing_{col}'], normalize='index')
                    if crosstab.shape[1] == 2:
                        max_diff = (crosstab[1] - crosstab[0]).abs().max()
                        if max_diff > 0.1:
                            evidence.append(f"La distribución difiere según {cat_col} (dif. máx={max_diff:.2f})")
                except Exception:
                    pass
        
        if len(evidence) == 0:
            classification = 'MCAR'
            justification = 'No se detecta relación con otras variables observadas'
            proposed_strategy = 'Imputación con mediana/moda según tipo (tras confirmación)'
        else:
            classification = 'MAR'
            justification = 'La ausencia parece relacionada con otras variables observadas'
            proposed_strategy = 'Imputación por grupo o condicional (tras confirmación)'
        
        if null_percent > 30:
            evidence.append(f"Porcentaje alto de faltantes ({null_percent:.2f}%) - requiere cuidado")
        
        if classification == 'POSSIBLE_MNAR' or (classification == 'MAR' and null_percent > 40):
            classification = 'MNAR'
            justification = 'Posible relación con el propio valor o alta incertidumbre. Se recomienda NO imputar.'
            proposed_strategy = 'SOLO INDICADOR - no imputar'
        
        return {
            'null_count': int(null_count),
            'null_percent': float(null_percent),
            'evidence': evidence if evidence else ['No se detectan patrones evidentes en análisis rápido'],
            'classification': classification,
            'justification': justification,
            'proposed_strategy': proposed_strategy
        }
    
    def get_confirmation_prompt(self) -> str:
        """Mensaje de confirmación."""
        return """
Para cada columna con nulos se requiere confirmación explícita.
Especifique: (columna, accion, metodo) donde accion puede ser:
- 'impute_median', 'impute_mode', 'impute_mean', 'impute_group', 'impute_constant'
- 'flag_mnar' (crear indicador, sin imputación) - RECOMENDADO para MNAR
- 'drop_rows' (solo si justificado)
- 'skip' (omitir por ahora)

Toda decisión quedará registrada en el log.
"""
