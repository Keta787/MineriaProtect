"""
cruzar_datos.py
===============
Integra las fuentes limpias (JobHop + ESCO) en el dataset unificado `empleos`.

Flujo (R1 + R6 + R2 del diseno):
    JobHop_v2_train_limpio.parquet
        |  matched_code --(R1)--> occupations_en_limpio.code
        |  matched_code[:4] --(R6)--> ISCOGroups.enrier limpio (rescate por prefijo ISCO)
        |  isco_group --(R2)--> ISCOGroups_en_limpio.code
        v
    empleos  (1 fila = 1 experiencia laboral enriquecida)

Regla de cardinalidad: los merges son N:1. El numero de filas NO cambia
(== len(JobHop limpio) == 1.506.445).

Clasificacion `emparejado` (precedencia estricta):
    1. matched_code == 'unknown'      -> 'unknown'
    2. matched_code in occupations.code -> 'ok'
    3. matched_code[:4] in ISCOGroups.code (4 digitos) -> 'rescatado'
    4. cualquier otro caso            -> 'descartado' (debe ser 0)

Validaciones obligatorias (contrato CIERRE_DISENO.md V1-V7) + comparacion
contra la referencia `cruce/salida/empleos_ref.csv` si existe.

Salida:
    cruce/salida/empleos.csv
    cruce/salida/empleos.parquet

Uso:
    python script/cruzar_datos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

RAIZ = Path(__file__).resolve().parent.parent
LIM = RAIZ / "dataset"
OUT = RAIZ / "cruce" / "salida"
JH = LIM / "JobHop_v2_train_limpio.parquet"
OCC = LIM / "ESCO" / "occupations_en_limpio.csv"
ISCO = LIM / "ESCO" / "ISCOGroups_en_limpio.csv"
REF = OUT / "empleos_ref.csv"  # referencia local (no versionada) para validar el cruce


def carga_csv(p: Path) -> pd.DataFrame:
    return pd.read_csv(p, dtype=str, encoding="utf-8", na_filter=False)


def clasificar(matched: pd.Series, cods_occ: set, isco4: set) -> pd.Series:
    """Aplica la precedencia de 'emparejado'."""
    out = pd.Series("descartado", index=matched.index, dtype="object")
    out[matched == "unknown"] = "unknown"
    m = matched.isin(cods_occ)
    out[m] = "ok"
    out[(~m) & (matched != "unknown") & (matched.str[:4].isin(isco4))] = "rescatado"
    return out


def main() -> None:
    # 1. Carga de entradas
    jh = pd.read_parquet(JH)
    occ = carga_csv(OCC)
    isco = carga_csv(ISCO)

    for c in ("code", "iscoGroup"):
        occ[c] = occ[c].str.strip()
    isco["code"] = isco["code"].str.strip()
    isco4 = set(isco.loc[isco["code"].str.len() == 4, "code"])

    jh["matched_code"] = jh["matched_code"].astype(str).str.strip()
    cods_occ = set(occ["code"])

    print(f"JobHop limpio: {len(jh)} filas")
    print(f"occupations limpio: {len(occ)} filas | {occ['code'].nunique()} codigos")
    print(f"ISCOGroups limpio: {len(isco)} filas")

    # 2. clasificacion emparejado (regla 1.3 del contrato)
    emp = pd.DataFrame(index=jh.index)
    emp["emparejado"] = clasificar(jh["matched_code"], cods_occ, isco4)
    print("\nemparejado (counts):")
    print(emp["emparejado"].value_counts().to_string())

    # 3. R1: occupation_code = matched_code solo donde 'ok'
    emp["occupation_code"] = jh["matched_code"].where(emp["emparejado"] == "ok", pd.NA)

    # 4. merge dejo las columnas base
    base = jh.copy()
    base["emparejado"] = emp["emparejado"]
    base["occupation_code"] = emp["occupation_code"]

    cols_left = ["resume_id", "start_date", "end_date", "university_level",
                 "matched_code", "emparejado", "occupation_code"]
    base = base[cols_left].copy()

    # R1 merge con occupations (N:1)
    base = base.merge(
        occ[["code", "preferredLabel", "iscoGroup"]],
        left_on="occupation_code", right_on="code", how="left",
    ).drop(columns="code")
    base = base.rename(columns={"preferredLabel": "occupation_label",
                                "iscoGroup": "isco_group"})

    # R6 rescate: donde emparejado == 'rescatado', isco_group = matched_code[:4]
    m_resc = base["emparejado"] == "rescatado"
    base.loc[m_resc, "isco_group"] = base.loc[m_resc, "matched_code"].str[:4]

    # R2 merge con ISCOGroups (N:1) para etiqueta y nivel
    base = base.merge(
        isco[["code", "preferredLabel"]],
        left_on="isco_group", right_on="code", how="left",
    ).drop(columns="code")
    base = base.rename(columns={"preferredLabel": "isco_group_label"})
    base["isco_level"] = base["isco_group"].fillna("").str.len().replace(0, pd.NA)

    # 5. orden canonico por persona y fecha (igual que el parquet limpio)
    def qk(v):
        v = str(v)
        if v.lower() == "present":
            return (9999, 4)
        try:
            q, a = v.split()
            return (int(a), int(q[1]))
        except Exception:
            return (0, 0)

    k = base["start_date"].map(qk)
    base["_k"] = k
    base = base.sort_values(["resume_id", "_k"]).drop(columns="_k").reset_index(drop=True)

    cols_final = ["resume_id", "start_date", "end_date", "university_level",
                  "matched_code", "emparejado", "occupation_code", "occupation_label",
                  "isco_group", "isco_group_label", "isco_level"]
    base = base[cols_final]

    # 6. validaciones V1-V7
    print("\n=== VALIDACIONES ===")
    v = {}
    v["V1 len==1506445"] = len(base) == 1_506_445
    v["V2 ok==1391276"] = int((base["emparejado"] == "ok").sum()) == 1_391_276
    v["V3 rescatado==10176"] = int((base["emparejado"] == "rescatado").sum()) == 10_176
    v["V4 unknown==104993"] = int((base["emparejado"] == "unknown").sum()) == 104_993
    v["V5 descartado==0"] = int((base["emparejado"] == "descartado").sum()) == 0
    v["V6 isco nulo solo unknown"] = int(base.loc[base["emparejado"] != "unknown", "isco_group"].isna().sum()) == 0
    v["V7 PK duplicados==0"] = int(base.duplicated(subset=["resume_id", "matched_code", "start_date", "end_date"]).sum()) == 0
    v["V13 prefix ok==100%"] = bool((base.loc[base["emparejado"] == "ok", "matched_code"].str[:4].reset_index(drop=True)
                                    == base.loc[base["emparejado"] == "ok", "isco_group"].reset_index(drop=True)).all())
    for nombre, ok in v.items():
        print(f"  {nombre}: {'OK' if ok else 'FALLO'}")

    if not all(v.values()):
        print("\nERROR: fallaron validaciones -> no se guarda.")
        sys.exit(1)

    # 7. comparacion contra la referencia empleos.csv
    if REF.exists():
        ref = pd.read_csv(REF, dtype=str, encoding="utf-8", na_filter=False)
        gen = base.copy().astype(str).fillna("")
        ref = ref.astype(str)
        # alinear el orden de columnas
        ref = ref[cols_final]
        gen = gen[cols_final]

        def to_tuples(df):
            return set(map(tuple, df.sort_values(cols_final).values.tolist()))

        t_gen, t_ref = to_tuples(gen), to_tuples(ref)
        iguales = t_gen == t_ref
        print("\n=== COMPARACION CONTRA REFERENCIA cruce/salida/empleos_ref.csv ===")
        print("  mismos registros exactos:", iguales)
        if not iguales:
            print("  solo en generado:", len(t_gen - t_ref))
            print("  solo en referencia:", len(t_ref - t_gen))
    else:
        print("\n(referencia no existe, se omite comparacion)")

    # 8. guardar (siempre mismo tamano)
    OUT.mkdir(parents=True, exist_ok=True)
    base.to_csv(OUT / "empleos.csv", index=False, encoding="utf-8")
    base.to_parquet(OUT / "empleos.parquet", index=False)
    print(f"\nGuardado en {OUT}: empleos.csv ({len(base)} filas) y empleos.parquet")


if __name__ == "__main__":
    main()