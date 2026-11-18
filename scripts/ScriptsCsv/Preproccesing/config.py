"""
Configuración para el pipeline de preprocesamiento.

Centraliza rutas, constantes, semillas aleatorias y el factor IQR.
Se utilizan rutas relativas al proyecto.
"""

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class PipelineConfig:
    """Configuración inmutable para el pipeline de preprocesamiento."""
    
    # Semilla para reproducibilidad
    seed: int = 42
    
    # Factor IQR (regla de Tukey)
    iqr_factor: float = 1.5
    
    # Ruta de entrada (relativa a MineriaProtect/)
    input_csv_rel: str = "data/03_processed/empleos_limpio_con_competencias.csv"
    
    # Rutas de salida
    output_dir_rel: str = "data/03_processed"
    output_filename: str = "empleos_limpio_con_competencias_sin_outliers.csv"
    
    # Columna clave para identificación
    unique_key: str = "Resume_id"
    
    # Columnas de fecha/trimestre - NUNCA winsorizar
    date_quarter_cols: tuple = ("start_date", "end_date")
    
    # Columnas que NUNCA deben ser sometidas a winsorización
    exclude_from_winsorization: tuple = (
        # IDs y códigos
        "Resume_id", "resume_id",
        "id", "ID", "Id",
        # Códigos ESCO/ocupación
        "occupation_code", "isco_code", "esco_code", "matched_code",
        # Códigos postales
        "postal_code", "zip_code", "cp",
        # Año/fecha
        "year", "anio", "año",
        "start_date", "end_date",
        "start_quarter", "end_quarter",
        # Geográficos
        "latitude", "longitude", "lat", "lon",
        # Timestamps
        "timestamp", "date", "datetime",
    )
    
    @property
    def is_notebook_env(self) -> bool:
        """Verifica si se ejecuta en entorno notebook."""
        try:
            from IPython import get_ipython
            return get_ipython() is not None
        except Exception:
            return False


# Configuración por defecto
DEFAULT_CONFIG = PipelineConfig()


def get_project_root() -> Path:
    """
    Obtiene la raíz del proyecto MineriaProtect.
    Busca marcadores comunes como 'scripts', 'data', 'notebooks'.
    """
    cwd = Path.cwd()
    
    if cwd.name == "MineriaProtect":
        return cwd
    if (cwd / "MineriaProtect").exists():
        return cwd / "MineriaProtect"
    
    for parent in [cwd] + list(cwd.parents):
        if parent.name == "MineriaProtect":
            return parent
        if (parent / "scripts" / "ScriptsCsv").exists():
            if parent.name == "MineriaProtect":
                return parent
    
    return cwd


def get_input_path(config: PipelineConfig = DEFAULT_CONFIG) -> Path:
    """Obtiene ruta absoluta del CSV de entrada."""
    root = get_project_root()
    return root / config.input_csv_rel


def get_output_dir(config: PipelineConfig = DEFAULT_CONFIG) -> Path:
    """Obtiene ruta absoluta del directorio de salida."""
    root = get_project_root()
    return root / config.output_dir_rel


def get_output_path(config: PipelineConfig = DEFAULT_CONFIG) -> Path:
    """Obtiene ruta absoluta del archivo de salida."""
    return get_output_dir(config) / config.output_filename
