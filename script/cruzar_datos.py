"""
cruzar_datos.py — Cruce de JobHop v2 con ESCO (6 tablas relevantes)

Genera: data/procesada/empleos.csv  (T1 — 1 fila = 1 experiencia laboral enriquecida)

Entradas (data/limpio/):
  - JobHop_v2_train_limpio.parquet  (JH)
  - ESCO/occupations_en_limpio.csv  (OCC)
  - ESCO/ISCOGroups_en_limpio.csv   (ISCO)
  - ESCO/occupationSkillRelations_en_limpio.csv (REL)
  - ESCO/skills_en_limpio.csv       (SK)
  - ESCO/greenShareOcc_en_limpio.csv (GS)

Sigue la especificación de CIERRE_DISEÑO.md (secciones 1-8).
"""

import pandas as pd
import sys
from pathlib import Path

# ── Rutas ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
LIMPIO = ROOT / "data" / "limpio"
PROCESADA = ROOT / "data" / "procesada"
PROCESADA.mkdir(exist_ok=True)

print("=" * 60)
print("CRUCE JobHop v2 + ESCO — Generación de empleos.csv")
print("=" * 60)

# ── 1. Cargar tablas ──────────────────────────────────────────────────
print("\n[1/8] Cargando tablas...")

JH = pd.read_parquet(LIMPIO / "JobHop_v2_train_limpio.parquet")
OCC = pd.read_csv(LIMPIO / "ESCO" / "occupations_en_limpio.csv", dtype=str)
ISCO = pd.read_csv(LIMPIO / "ESCO" / "ISCOGroups_en_limpio.csv", dtype=str)
REL = pd.read_csv(LIMPIO / "ESCO" / "occupationSkillRelations_en_limpio.csv", dtype=str)
SK = pd.read_csv(LIMPIO / "ESCO" / "skills_en_limpio.csv", dtype=str)
GS = pd.read_csv(LIMPIO / "ESCO" / "greenShareOcc_en_limpio.csv", dtype=str)

print(f"  JobHop:  {len(JH):>10,} filas x {len(JH.columns)} cols")
print(f"  OCC:     {len(OCC):>10,} filas x {len(OCC.columns)} cols")
print(f"  ISCO:    {len(ISCO):>10,} filas x {len(ISCO.columns)} cols")
print(f"  REL:     {len(REL):>10,} filas x {len(REL.columns)} cols")
print(f"  SK:      {len(SK):>10,} filas x {len(SK.columns)} cols")
print(f"  GS:      {len(GS):>10,} filas x {len(GS.columns)} cols")

# Asegurar matched_code como string
JH["matched_code"] = JH["matched_code"].astype(str)
len_jh_original = len(JH)

# ── 2. Clasificar emparejado (§1.3 del CIERRE) ────────────────────────
print("\n[2/8] Clasificando emparejado...")

# Preparar conjuntos de lookup
codes_occ = set(OCC["code"].dropna().unique())
codes_isco = set(ISCO["code"].dropna().unique())

def clasificar_emparejado(code):
    if code == "unknown":
        return "unknown"
    if code in codes_occ:
        return "ok"
    prefix4 = code[:4]
    if len(code) >= 4 and prefix4 in codes_isco:
        return "rescatado"
    return "descartado"

JH["emparejado"] = JH["matched_code"].apply(clasificar_emparejado)

# Conteos de clasificación
conteos = JH["emparejado"].value_counts()
for cat in ["ok", "rescatado", "unknown", "descartado"]:
    n = conteos.get(cat, 0)
    print(f"  {cat:>12}: {n:>10,}")

# ── 3. Merge N:1 JobHop → Occupations (R1) ───────────────────────────
print("\n[3/8] Cruzando con occupations (R1)...")

occ_key = OCC[["code", "conceptUri", "preferredLabel", "iscoGroup"]].copy()
occ_key = occ_key.rename(columns={
    "code": "occupation_code",
    "conceptUri": "occupation_conceptUri",
    "preferredLabel": "occupation_label",
    "iscoGroup": "isco_group_from_occ",
})

# Merge: matched_code → occupation_code
JH = JH.merge(occ_key, left_on="matched_code", right_on="occupation_code", how="left")
assert len(JH) == len_jh_original, f"V1 FAIL: {len(JH)} != {len_jh_original}"
print(f"  Filas tras merge: {len(JH):,} (esperado: {len_jh_original:,}) OK")

# ── 4. Rescate por prefijo ISCO (§1.4) ───────────────────────────────
print("\n[4/8] Aplicando rescate por prefijo ISCO...")

# Para filas rescatadas: isco_group = matched_code[:4]
rescatado_mask = JH["emparejado"] == "rescatado"
JH.loc[rescatado_mask, "isco_group"] = JH.loc[rescatado_mask, "matched_code"].str[:4]

# Para filas ok: isco_group = de occupations
ok_mask = JH["emparejado"] == "ok"
JH.loc[ok_mask, "isco_group"] = JH.loc[ok_mask, "isco_group_from_occ"]

# Para unknown: isco_group = NaN
unknown_mask = JH["emparejado"] == "unknown"
JH.loc[unknown_mask, "isco_group"] = pd.NA

n_rescatado = rescatado_mask.sum()
n_ok = ok_mask.sum()
n_unknown = unknown_mask.sum()
n_descartado = (JH["emparejado"] == "descartado").sum()
print(f"  ok:       {n_ok:>10,}")
print(f"  rescatado:{n_rescatado:>10,}")
print(f"  unknown:  {n_unknown:>10,}")
print(f"  descartado:{n_descartado:>9,}")

# Verificar V6: isco_group nulo solo cuando unknown
isco_nulo = JH["isco_group"].isna()
assert (isco_nulo == unknown_mask).all(), "V6 FAIL: isco_group nulo fuera de 'unknown'"
print("  V6 (isco_group nulo solo en unknown): OK")

# ── 5. Merge N:1 ISCOGroups (R2) ─────────────────────────────────────
print("\n[5/8] Cruzando con ISCOGroups (R2)...")

isco_key = ISCO[["code", "preferredLabel"]].copy()
isco_key = isco_key.rename(columns={
    "preferredLabel": "isco_group_label",
})

# Solo merge para filas que tienen isco_group (no unknown)
mask_con_grupo = JH["isco_group"].notna()
JH_con = JH[mask_con_grupo].copy()
JH_sin = JH[~mask_con_grupo].copy()

JH_con = JH_con.merge(isco_key, left_on="isco_group", right_on="code", how="left")
JH_con = JH_con.drop(columns=["code"])

# Concatenar
JH = pd.concat([JH_con, JH_sin], ignore_index=True)
assert len(JH) == len_jh_original, f"V1 FAIL post-ISCO: {len(JH)} != {len_jh_original}"
print(f"  Filas tras merge: {len(JH):,} OK")

# Derivar isco_level = longitud del código
JH["isco_level"] = JH["isco_group"].apply(lambda x: len(str(x)) if pd.notna(x) else None)
JH["isco_level"] = JH["isco_level"].astype("Int64")

# ── 6. Verificar consistencia de prefijo (V13) ────────────────────────
print("\n[6/8] Verificando consistencia (V13)...")

mask_ok = JH["emparejado"] == "ok"
consistente = (JH.loc[mask_ok, "matched_code"].str[:4] == JH.loc[mask_ok, "isco_group"]).all()
print(f"  V13 (matched_code[:4] == isco_group para 'ok'): {'OK' if consistente else 'FAIL'}")

# ── 7. Seleccionar y ordenar columnas finales de T1 ───────────────────
print("\n[7/8] Construyendo tabla final...")

T1 = JH[[
    "resume_id",
    "start_date",
    "end_date",
    "university_level",
    "matched_code",
    "emparejado",
    "occupation_code",
    "occupation_label",
    "isco_group",
    "isco_group_label",
    "isco_level",
]].copy()

T1 = T1.sort_values(["resume_id", "start_date", "matched_code"]).reset_index(drop=True)

# ── 8. Validaciones finales y guardado ────────────────────────────────
print("\n[8/8] Validaciones finales...")

# V1: tamaño
assert len(T1) == 1_506_445, f"V1 FAIL: {len(T1)} != 1,506,445"
print(f"  V1 (len == 1,506,445): {len(T1):,} OK")

# V2-V5: conteos de emparejado
assert (T1["emparejado"] == "ok").sum() == 1_391_276, "V2 FAIL"
print(f"  V2 (ok == 1,391,276): {(T1['emparejado'] == 'ok').sum():,} OK")

assert (T1["emparejado"] == "rescatado").sum() == 10_176, "V3 FAIL"
print(f"  V3 (rescatado == 10,176): {(T1['emparejado'] == 'rescatado').sum():,} OK")

assert (T1["emparejado"] == "unknown").sum() == 104_993, "V4 FAIL"
print(f"  V4 (unknown == 104,993): {(T1['emparejado'] == 'unknown').sum():,} OK")

assert (T1["emparejado"] == "descartado").sum() == 0, "V5 FAIL"
print(f"  V5 (descartado == 0): {(T1['emparejado'] == 'descartado').sum()} OK")

# V7: unicidad de PK
pk_cols = ["resume_id", "matched_code", "start_date", "end_date"]
n_dup = T1.duplicated(subset=pk_cols).sum()
assert n_dup == 0, f"V7 FAIL: {n_dup} duplicados"
print(f"  V7 (duplicados PK == 0): {n_dup} OK")

# Guardar
salida = PROCESADA / "empleos.csv"
T1.to_csv(salida, index=False, encoding="utf-8")
print(f"\n{'=' * 60}")
print(f"GUARDADO: {salida}")
print(f"  Filas:  {len(T1):>10,}")
print(f"  Columnas: {len(T1.columns):>8}")
print(f"  Tamaño:  {salida.stat().st_size / 1024 / 1024:.1f} MB")
print(f"{'=' * 60}")

# Resumen de la tabla
print("\nMuestra (5 filas):")
print(T1.head().to_string(index=False))

print("\nTipos de datos:")
print(T1.dtypes.to_string())

print("\nValores nulos por columna:")
nulos = T1.isna().sum()
for col in T1.columns:
    n = nulos[col]
    if n > 0:
        print(f"  {col}: {n:,} ({n/len(T1)*100:.1f}%)")

print("\nDistribución university_level:")
print(T1["university_level"].value_counts().to_string())

print("\nDistribución emparejado:")
print(T1["emparejado"].value_counts().to_string())

print("\nTop 10 isco_group_label (más frecuentes):")
top_isco = T1["isco_group_label"].value_counts().head(10)
print(top_isco.to_string())

print("\n¡Cruce completado exitosamente!")

