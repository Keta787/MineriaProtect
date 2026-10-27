# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas>=2.2.0",
# ]
# ///

import sys
from pathlib import Path
import pandas as pd

# Encontrar raiz del proyecto buscando data/
cwd = Path.cwd()
root = cwd
for _ in range(10):
    if (root / "data").exists():
        break
    root = root.parent

data_path = root / "data" / "03_processed" / "empleos_con_competencias_limpio_sin_outliers.csv"
print(f"DATA_PATH: {data_path}")
print(f"EXISTS: {data_path.exists()}")
if not data_path.exists():
    sys.exit(1)

# Leer defensivo
df = pd.read_csv(data_path, dtype=str, encoding="utf-8", keep_default_na=False, na_values=[""])

# Columnas objetivo + necesarias
cols = ["resume_id", "start_date", "end_date", "university_level", 
        "isco_group", "isco_group_label", 
        "n_skills_competence", "n_skills_knowledge", "n_skills_essential",
        "saber_skills", "emparejado"]
for c in cols:
    if c not in df.columns:
        print(f"MISSING: {c}")

df_sub = df[cols].copy()
print("\n=== SHAPE ===")
print(df_sub.shape)
print("\n=== DTYPES ===")
print(df_sub.dtypes)
print("\n=== NULOS/NA (count) ===")
print(df_sub.isna().sum())
print("\n=== VALORES VACIOS POR COLUMNA ===")
for c in df_sub.columns:
    if df_sub[c].dtype == object:
        vac = (df_sub[c].astype(str).str.strip() == "").sum()
        print(f"{c}: {vac}")
print("\n=== university_level (ANTES DE NORMALIZAR) ===")
print(df_sub["university_level"].value_counts(dropna=False))
print("\n=== saber_skills ===")
print(df_sub["saber_skills"].value_counts(dropna=False))
print("\n=== isco_group vs isco_group_label (duplicidad) ===")
print("isco_group únicos:", df_sub["isco_group"].nunique())
print("isco_group_label únicos:", df_sub["isco_group_label"].nunique())
print("\n=== TOP 10 isco_group_label ===")
print(df_sub["isco_group_label"].value_counts().head(10))
print("\n=== n_skills_competence/knowledge resumen ===")
print(df_sub[["n_skills_competence","n_skills_knowledge"]].describe())
