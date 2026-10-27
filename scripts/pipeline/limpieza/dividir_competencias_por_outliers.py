"""Genera la variante enriquecida sin outliers de duración.

La lógica reproduce el criterio histórico de `dividir_por_outliers.py`, pero
opera sobre `empleos_con_competencias_limpio.csv` y conserva las columnas de
competencias.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

import pandas as pd


BASE = Path(__file__).resolve().parents[3]
PROCESADOS = BASE / "data" / "03_processed"
ENTRADA = PROCESADOS / "empleos_con_competencias_limpio.csv"
SALIDA = PROCESADOS / "empleos_con_competencias_limpio_sin_outliers.csv"
LOG = BASE / "logs" / "bitacora_outliers_empleos_competencias.csv"


def _ordinal(serie: pd.Series) -> pd.Series:
    partes = serie.str.extract(r"^Q([1-4])\s+(\d{4})$")
    anio = pd.to_numeric(partes[1], errors="coerce")
    trimestre = pd.to_numeric(partes[0], errors="coerce")
    return anio * 4 + trimestre


def main() -> None:
    if not ENTRADA.exists():
        raise FileNotFoundError(
            f"No existe {ENTRADA}. Ejecuta primero "
            "limpiar_empleos_con_competencias.py."
        )

    df = pd.read_csv(
        ENTRADA,
        dtype=str,
        encoding="utf-8",
        keep_default_na=False,
        na_values=[""],
    )
    duracion = _ordinal(df["end_date"]) - _ordinal(df["start_date"]) + 1
    q1, q3 = duracion.quantile([0.25, 0.75])
    iqr = q3 - q1
    inferior = q1 - 1.5 * iqr
    superior = q3 + 1.5 * iqr
    outlier = (duracion < inferior) | (duracion > superior)

    sin = df.loc[~outlier].reset_index(drop=True)
    if sin.empty:
        raise AssertionError("La variante enriquecida sin outliers quedó vacía.")
    if len(sin) != len(df) - int(outlier.sum()):
        raise AssertionError("La cantidad de filas sin outliers no es consistente.")
    if list(sin.columns) != list(df.columns):
        raise AssertionError("La variante sin outliers alteró el esquema enriquecido.")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    sin.to_csv(SALIDA, index=False, encoding="utf-8")

    LOG.parent.mkdir(parents=True, exist_ok=True)
    fila = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "script": Path(__file__).name,
        "entrada": str(ENTRADA),
        "salida": str(SALIDA),
        "filas_entrada": len(df),
        "filas_salida": len(sin),
        "outliers": int(outlier.sum()),
        "personas_outliers": int(df.loc[outlier, "resume_id"].nunique()),
        "q1": float(q1),
        "q3": float(q3),
        "iqr": float(iqr),
        "limite_superior": float(superior),
        "estado": "OK",
    }
    nuevo = not LOG.exists()
    with LOG.open("a", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(fila))
        if nuevo:
            escritor.writeheader()
        escritor.writerow(fila)

    print(
        f"Outliers enriquecidos: {int(outlier.sum()):,}; "
        f"salida: {len(sin):,} filas, {sin.shape[1]} columnas."
    )


if __name__ == "__main__":
    main()
