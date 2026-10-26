# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas>=2.2.0",
#   "numpy>=1.26.0",
# ]
# ///
"""Estadísticas de apoyo para el EDA de columnas objetivo (JobPath).

Calcula los números que se citan en el notebook `EDA_Columnas_Objetivo.ipynb`.
No genera figuras: solo resúmenes verificables. Se ejecuta con `uv run`.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------- rutas
cwd = Path.cwd()
root = cwd
for _ in range(10):
    if (root / "data").exists():
        break
    root = root.parent
else:
    raise SystemExit("No se encontró la carpeta data/")

SESSION = root / "analysis" / "2026-10-25T16-00-00-eda-columnas-objetivo"
DATA = root / "data" / "03_processed" / "empleos_limpio_con_competencias .csv"

COLS = [
    "resume_id", "start_date", "end_date", "university_level",
    "isco_group", "isco_group_label", "occupation_label",
    "n_skills_essential", "n_skills_competence", "n_skills_knowledge",
    "n_skills_sin_tipo", "veces_ese_oficio", "saber_skills",
    "es_vigente", "es_unknown_ocupacion", "es_rescatado",
    "skills", "knowledge",
]
CANON = ["No reportado", "Secondary school", "Bachelor", "Master", "PhD"]
MAJOR = {
    "1": "1 · Gerentes y directivos",
    "2": "2 · Profesionales y científicos",
    "3": "3 · Técnicos y profesionales asociados",
    "4": "4 · Personal de apoyo administrativo",
    "5": "5 · Servicios y vendedores",
    "6": "6 · Agricultura y pesca",
    "7": "7 · Oficiales y artesanos",
    "8": "8 · Operadores de máquinas",
    "9": "9 · Ocupaciones elementales",
    "0": "0 · Fuerzas armadas",
}


def mil(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def pct(a, b) -> float:
    return round(100 * a / b, 2) if b else float("nan")


def cramers_v(tab: pd.DataFrame) -> float:
    obs = tab.to_numpy(dtype=float)
    n = obs.sum()
    if n == 0:
        return float("nan")
    esperado = np.outer(obs.sum(axis=1), obs.sum(axis=0)) / n
    chi2 = ((obs - esperado) ** 2 / esperado).sum()
    return float(np.sqrt(chi2 / (n * (min(obs.shape) - 1))))


def main() -> None:
    df = pd.read_csv(
        DATA, dtype=str, encoding="utf-8", keep_default_na=False,
        na_values=[""], usecols=COLS,
    )
    res: dict[str, object] = {"archivo": DATA.name, "filas": int(len(df)), "columnas": int(df.shape[1])}
    print(f"Archivo: {DATA.name}")
    print(f"Filas: {mil(len(df))} | columnas leídas: {df.shape[1]}")

    # ------------------------------------------------------------ preparación
    df["Period_Time"] = (
        df["start_date"].astype(str).str.strip()
        + " - "
        + df["end_date"].astype(str).str.strip()
    )
    df["University_Level_norm"] = df["university_level"].astype(str).str.strip()
    df.loc[df["University_Level_norm"].isin(["", "nan", "None", "NaN"]), "University_Level_norm"] = "No reportado"
    df["Isco_group_unif"] = df["isco_group_label"].astype(str).str.strip()
    df.loc[df["Isco_group_unif"].isin(["", "nan", "None", "NaN"]), "Isco_group_unif"] = "SIN_GRUPO"

    for origen, destino in [
        ("n_skills_competence", "n_skills_competence_num"),
        ("n_skills_knowledge", "n_skills_knowledge_num"),
        ("n_skills_essential", "n_skills_essential_num"),
        ("n_skills_sin_tipo", "n_skills_sin_tipo_num"),
        ("veces_ese_oficio", "veces_ese_oficio_num"),
    ]:
        df[destino] = pd.to_numeric(df[origen], errors="coerce")

    ini = df["start_date"].str.extract(r"Q([1-4])\s+(\d{4})")
    df["start_q"] = pd.to_numeric(ini[0], errors="coerce")
    df["start_year"] = pd.to_numeric(ini[1], errors="coerce")
    df["start_ord"] = df["start_year"] * 4 + df["start_q"]

    fin = df["end_date"].str.extract(r"Q([1-4])\s+(\d{4})")
    df["end_q"] = pd.to_numeric(fin[0], errors="coerce")
    df["end_year"] = pd.to_numeric(fin[1], errors="coerce")
    df["end_ord"] = df["end_year"] * 4 + df["end_q"]
    df["es_vigente_bool"] = df["end_date"].astype(str).str.strip().eq("Present")
    df["dur_trim"] = (df["end_ord"] - df["start_ord"] + 1).where(~df["es_vigente_bool"])

    df["major_code"] = df["isco_group"].astype(str).str.strip().str[0]
    df["ISCO_major"] = df["major_code"].map(MAJOR).fillna("SIN_GRUPO")

    # ------------------------------------------------------------ 1. resume_id
    exp = df["resume_id"].value_counts()
    res["personas"] = int(exp.size)
    res["exp_por_persona"] = {
        "media": round(float(exp.mean()), 2),
        "mediana": float(exp.median()),
        "p90": float(exp.quantile(0.90)),
        "p99": float(exp.quantile(0.99)),
        "max": int(exp.max()),
        "una_sola": int((exp == 1).sum()),
        "una_sola_pct": pct(int((exp == 1).sum()), int(exp.size)),
        "top10_pct_de_filas": pct(int(exp.head(10).sum()), int(len(df))),
        "top1pct_personas_pct_filas": pct(
            int(exp.head(max(1, int(exp.size * 0.01))).sum()), int(len(df))
        ),
    }
    res["top10_personas"] = {str(k): int(v) for k, v in exp.head(10).items()}
    res["experiencias_por_persona_vc"] = {
        str(k): int(v) for k, v in exp.value_counts().sort_index().head(15).items()
    }

    # ------------------------------------------------------------ 2. Period_Time
    res["periodo"] = {
        "start_year_min": int(df["start_year"].min()),
        "start_year_max": int(df["start_year"].max()),
        "end_year_min": int(df["end_year"].min()),
        "end_year_max": int(df["end_year"].max()),
        "n_present": int(df["es_vigente_bool"].sum()),
        "pct_present": pct(int(df["es_vigente_bool"].sum()), len(df)),
        "n_duracion_observada": int(df["dur_trim"].notna().sum()),
        "dur_mediana_trim": float(df["dur_trim"].median()),
        "dur_media_trim": round(float(df["dur_trim"].mean()), 2),
        "dur_q1": float(df["dur_trim"].quantile(0.25)),
        "dur_q3": float(df["dur_trim"].quantile(0.75)),
        "dur_max_trim": int(df["dur_trim"].max()),
        "dur_mediana_anios": round(float(df["dur_trim"].median()) / 4, 2),
        "pct_dur_1trim": pct(int((df["dur_trim"] == 1).sum()), int(df["dur_trim"].notna().sum())),
        "pct_dur_le_4trim": pct(int((df["dur_trim"] <= 4).sum()), int(df["dur_trim"].notna().sum())),
        "pct_anios_antes_2000": pct(int((df["start_year"] < 2000).sum()), int(df["start_year"].notna().sum())),
        "pct_anios_2010_mas": pct(int((df["start_year"] >= 2010).sum()), int(df["start_year"].notna().sum())),
        "anio_inicio_top": {str(k): int(v) for k, v in df["start_year"].value_counts().head(8).items()},
        "top_period_time": {str(k): int(v) for k, v in df["Period_Time"].value_counts().head(10).items()},
    }

    # ------------------------------------------------------------ 3. University_Level
    vc_univ = df["University_Level_norm"].value_counts().reindex(CANON, fill_value=0)
    res["university_level"] = {
        k: {"n": int(v), "pct": pct(int(v), len(df))} for k, v in vc_univ.items()
    }
    res["university_level"]["_sin_normalizar_na"] = int(df["university_level"].isna().sum())

    # ------------------------------------------------------------ 4. ISCO
    isco_vc = df.loc[df["Isco_group_unif"] != "SIN_GRUPO", "Isco_group_unif"].value_counts()
    res["isco"] = {
        "grupos_unicos": int(isco_vc.size),
        "sin_grupo": int((df["Isco_group_unif"] == "SIN_GRUPO").sum()),
        "top5_pct": pct(int(isco_vc.head(5).sum()), int(len(df))),
        "top10_pct": pct(int(isco_vc.head(10).sum()), int(len(df))),
        "top20_pct": pct(int(isco_vc.head(20).sum()), int(len(df))),
        "top50_pct": pct(int(isco_vc.head(50).sum()), int(len(df))),
        "top15": {str(k): int(v) for k, v in isco_vc.head(15).items()},
        "mayores": {str(k): {"n": int(v), "pct": pct(int(v), len(df))}
                     for k, v in df["ISCO_major"].value_counts().items()},
    }

    # ------------------------------------------------------------ 5. skills
    skills = {}
    for col in ["n_skills_competence_num", "n_skills_knowledge_num", "n_skills_essential_num", "n_skills_sin_tipo_num", "veces_ese_oficio_num"]:
        s = df[col]
        skills[col] = {
            "n_validos": int(s.notna().sum()),
            "n_na": int(s.isna().sum()),
            "media": round(float(s.mean()), 2),
            "mediana": float(s.median()),
            "std": round(float(s.std()), 2),
            "min": float(s.min()),
            "p25": float(s.quantile(0.25)),
            "p75": float(s.quantile(0.75)),
            "p95": float(s.quantile(0.95)),
            "max": float(s.max()),
            "pct_cero": pct(int((s == 0).sum()), int(s.notna().sum())),
        }
    res["skills"] = skills
    res["correlaciones"] = {
        k: {kk: round(float(vv), 3) for kk, vv in v.items()}
        for k, v in df[["n_skills_competence_num", "n_skills_knowledge_num", "n_skills_essential_num", "n_skills_sin_tipo_num"]].corr().items()
    }

    res["skills_por_nivel"] = {}
    for nivel in CANON:
        sub = df[df["University_Level_norm"] == nivel]
        res["skills_por_nivel"][nivel] = {
            "n": int(len(sub)),
            "competence_mediana": float(sub["n_skills_competence_num"].median()),
            "knowledge_mediana": float(sub["n_skills_knowledge_num"].median()),
            "essential_mediana": float(sub["n_skills_essential_num"].median()),
        }

    sub_major = df[df["ISCO_major"] != "SIN_GRUPO"]
    res["skills_por_major"] = {
        str(k): {
            "n": int(len(g)),
            "competence_mediana": float(g["n_skills_competence_num"].median()),
            "knowledge_mediana": float(g["n_skills_knowledge_num"].median()),
            "essential_mediana": float(g["n_skills_essential_num"].median()),
        }
        for k, g in sub_major.groupby("ISCO_major")
    }

    # ------------------------------------------------------------ 6. cruces
    top12 = isco_vc.head(12).index
    ct = pd.crosstab(
        df.loc[df["Isco_group_unif"].isin(top12), "Isco_group_unif"],
        df.loc[df["Isco_group_unif"].isin(top12), "University_Level_norm"],
    ).reindex(columns=CANON, fill_value=0)
    pct12 = ct.div(ct.sum(axis=1), axis=0) * 100
    res["cruce_top12"] = {
        str(idx): {c: round(float(pct12.loc[idx, c]), 2) for c in CANON}
        for idx in pct12.index
    }
    res["cruce_top12_n"] = {str(k): int(v) for k, v in ct.sum(axis=1).items()}

    ct_major = pd.crosstab(df["ISCO_major"], df["University_Level_norm"])
    res["cramers_v_nivel_major"] = round(cramers_v(ct_major), 4)
    res["cramers_v_nivel_isco"] = round(cramers_v(pd.crosstab(df["Isco_group_unif"], df["University_Level_norm"])), 4)

    df["decada"] = (df["start_year"] // 10 * 10).astype("Int64")
    dec = df.loc[df["decada"].between(1970, 2020)]
    ct_dec = pd.crosstab(dec["decada"], dec["University_Level_norm"]).reindex(columns=CANON, fill_value=0)
    res["nivel_por_decada"] = {
        str(k): {c: round(float(v), 2) for c, v in row.items()}
        for k, row in (ct_dec.div(ct_dec.sum(axis=1), axis=0) * 100).iterrows()
    }
    res["nivel_por_decada_n"] = {str(k): int(v) for k, v in ct_dec.sum(axis=1).items()}

    res["cruce_nivel_isco_major_pct"] = {
        str(k): {c: round(float(v), 2) for c, v in row.items()}
        for k, row in (ct_major.div(ct_major.sum(axis=1), axis=0) * 100).iterrows()
    }

    # ------------------------------------------------------------ 7. calidad
    res["calidad"] = {
        "saber_skills": {str(k): int(v) for k, v in df["saber_skills"].value_counts(dropna=False).items()},
        "nulos": {
            col: {"n": int(df[col].isna().sum()), "pct": pct(int(df[col].isna().sum()), len(df))}
            for col in ["resume_id", "start_date", "end_date", "university_level",
                        "isco_group", "isco_group_label", "n_skills_competence",
                        "n_skills_knowledge", "n_skills_essential"]
        },
        "es_vigente": {str(k): int(v) for k, v in df["es_vigente"].value_counts(dropna=False).items()},
        "es_unknown": {str(k): int(v) for k, v in df["es_unknown_ocupacion"].value_counts(dropna=False).items()},
        "es_rescatado": {str(k): int(v) for k, v in df["es_rescatado"].value_counts(dropna=False).items()},
        "filas_duplicadas_exactas": int(df.duplicated().sum()),
    }

    # ------------------------------------------------------------ 8. ocupaciones
    oc = df.loc[df["occupation_label"].notna(), "occupation_label"].value_counts()
    res["ocupaciones"] = {
        "unicas": int(oc.size),
        "top10_pct": pct(int(oc.head(10).sum()), int(len(df))),
        "top10": {str(k): int(v) for k, v in oc.head(10).items()},
        "pct_una_sola_experiencia_por_ocupacion": pct(int((oc == 1).sum()), int(oc.size)),
    }

    SESSION.mkdir(parents=True, exist_ok=True)
    salida = SESSION / "resumen_columnas_objetivo.json"
    salida.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nResumen guardado en: {salida}")
    print(json.dumps(res, ensure_ascii=False, indent=2)[:12000])


if __name__ == "__main__":
    main()
