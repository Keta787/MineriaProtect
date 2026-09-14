"""
dividir_por_outliers.py
=======================
Divide el integrado limpio `empleos_limpio.csv` en dos versiones comparables:

    - `empleos_limpio.csv`         (con outliers): conserva todas las filas
      (salida del pipeline de limpieza; este script no la toca).
    - `empleos_limpio_sin_outliers.csv` (sin outliers): quita las filas con
      duracion fuera del IQR de Tukey (cola larga).

Criterio (misma fase 5 de `limpiar_empleos.py`):
    duracion trimestral inclusiva  dur_Q = ordinal(end) - ordinal(start) + 1;
    limites IQR(Tukey) sobre dur_Q: Q1=2, Q3=11, IQR=9 -> limite superior 24.5;
    son outliers las filas con dur_Q >= 25 (todas por la cola larga).

Uso de las dos versiones: cruzar descriptivos con/sin cola larga para validar el
impacto de esos atipicos antes de elegir la tecnica de mineria de trayectorias.

Como ejecutar:
    python src/limpieza/dividir_por_outliers.py

Requisitos:
    pandas (el CSV se lee como texto: dtype=str + keep_default_na=False para no
    perder ceros a la izquierda en los codigos).
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def _raiz_proyecto() -> Path:
    """Raiz del repo: busca hacia arriba la carpeta `data/` desde este archivo."""
    p = Path(__file__).resolve().parent
    while not (p / "data").exists() and p != p.parent:
        p = p.parent
    return p


RAIZ = _raiz_proyecto()
ORIGEN = RAIZ / "data" / "03_processed" / "empleos_limpio.csv"
SALIDA_SIN = RAIZ / "data" / "03_processed" / "empleos_limpio_sin_outliers.csv"
LOGS_DIR = RAIZ / "logs"
BITACORA = LOGS_DIR / "bitacora_dividir_outliers.csv"

# Canon de la fase 5 de limpiar_empleos.py (verificado): limites IQR sobre dur_Q.
CANONICOS_IQ = {"q1": 2.0, "q3": 11.0, "i_qr": 9.0, "inferior": -11.5, "superior": 24.5}


def _ordinal_trimestre(serie: pd.Series) -> pd.Series:
    """'Q<n> <aaaa>' -> anio*4 + trimestre; 'Present'/no-parseable -> NaN."""
    partes = serie.str.extract(r"^Q([1-4])\s+(\d{4})$")
    anio = pd.to_numeric(partes[1], errors="coerce")
    trimestre = pd.to_numeric(partes[0], errors="coerce")
    return anio * 4 + trimestre


def main() -> None:
    if not ORIGEN.exists():
        raise FileNotFoundError(
            f"No existe el limpio de empleos: {ORIGEN}\n"
            "Ejecuta primero src/limpieza/limpiar_empleos.py."
        )

    print("=" * 78)
    print("DIVISION POR OUTLIERS DE DURACION (empleos_limpio + sin_outliers)")
    print("=" * 78)

    df = pd.read_csv(
        ORIGEN, dtype=str, encoding="utf-8", keep_default_na=False, na_values=[""]
    )
    print(f"Origen:  {ORIGEN}")
    print(f"Filas:   {len(df):,} | Columnas: {df.shape[1]} | Personas: {df['resume_id'].nunique():,}")

    dur = _ordinal_trimestre(df["end_date"]) - _ordinal_trimestre(df["start_date"]) + 1
    q1, q3 = dur.quantile([0.25, 0.75])
    limits = {"q1": float(q1), "q3": float(q3), "i_qr": float(q3 - q1),
              "inferior": float(q1 - 1.5 * (q3 - q1)), "superior": float(q3 + 1.5 * (q3 - q1))}

    for clave, can in CANONICOS_IQ.items():
        assert abs(limits[clave] - can) < 1e-9, (
            f"IQR no canonico en {clave}: {limits[clave]} != {can}"
        )

    es_outlier = (dur < limits["inferior"]) | (dur > limits["superior"])
    print(f"IQR (Tukey) sobre dur_Q: Q1={q1:.2f} Q3={q3:.2f} IQR={q3 - q1:.2f} "
          f"| limites [{limits['inferior']:.2f}, {limits['superior']:.2f}]")
    print(f"Outliers (dur_Q >= 25, cola larga): {int(es_outlier.sum()):,} filas "
          f"/ {df.loc[es_outlier, 'resume_id'].nunique():,} personas")

    sin = df.loc[~es_outlier].reset_index(drop=True)
    con = df.copy()
    print("=" * 78)
    print("RESULTADO DE LA DIVISION")
    print("=" * 78)
    print(f"  Con outliers    : {len(con):,} filas / {con['resume_id'].nunique():,} personas  -> empleos_limpio.csv")
    print(f"  Sin outliers    : {len(sin):,} filas / {sin['resume_id'].nunique():,} personas  -> empleos_limpio_sin_outliers.csv")
    print(f"  Consistencia    : {len(df):,} - {int(es_outlier.sum()):,} outliers = {len(df) - int(es_outlier.sum()):,} (sin outliers)")

    n_out = int(es_outlier.sum())
    assert len(sin) == len(df) - n_out, "Sin outliers no es el total menos los outliers"
    assert len(con) == len(df), "La version con outliers debe conservar todas las filas"
    assert sin.shape[1] == con.shape[1] == 14, "Cambió la estructura de columnas"
    assert not sin.empty, "La version sin outliers quedó vacía"

    SALIDA_SIN.parent.mkdir(parents=True, exist_ok=True)
    sin.to_csv(SALIDA_SIN, index=False, encoding="utf-8")
    print(f"Escrito: {SALIDA_SIN} ({SALIDA_SIN.stat().st_size / 1e6:.1f} MB)")
    print("El original data/03_processed/empleos_limpio.csv NO fue modificado.")

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    nuevo = not BITACORA.exists()
    with BITACORA.open("a", newline="", encoding="utf-8") as fh:
        import csv
        fila = {
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "script": Path(__file__).name,
            "filas_con_outliers": len(con),
            "filas_sin_outliers": len(sin),
            "outliers_filas": int(es_outlier.sum()),
            "outliers_personas": int(df.loc[es_outlier, "resume_id"].nunique()),
            "limite_superior": limits["superior"],
            "estado": "OK",
        }
        writer = csv.DictWriter(fh, fieldnames=list(fila))
        if nuevo:
            writer.writeheader()
        writer.writerow(fila)
    print(f"Bitacora de ejecucion persistida: {BITACORA}")

    print("\nDivision completada sin errores.")


if __name__ == "__main__":
    main()