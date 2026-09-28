"""
integrar_empleos.py
===================
Construye el dataset integrado `empleos` a partir de las fuentes ya limpiadas
en `data/02_interim/`:

    JobHop_v2_test_limpio.csv + JobHop_v2_val_limpio.csv  ->  empleos.csv
      (union de las particiones test y val del dato crudo de JobHop v2 en CSV)
    + ESCO occupations_en_limpio.csv  (matched_code -> ocupacion + grupo ISCO)
    + ESCO ISCOGroups_en_limpio.csv   (grupo ISCO-08 -> etiqueta de area)
    + ESCO occupationSkillRelations_en_limpio.csv (oficio -> competencias)

Regla de emparejado (semantica documentada en README y en el acta 1.0):
    - 'ok'       : matched_code == occupations.code (cruce directo por codigo).
    - 'rescatado': no hay cruce directo, pero el prefijo de 4 digitos de
                   matched_code (grupo ISCO-08) si existe en ISCOGroups_en;
                   se conserva unicamente el area ISCO, no una ocupacion.
    - 'unknown'  : sin mapeo directo ni grupo ISCO valido (incluye el literal
                   'unknown'). Se flagga, no se elimina.

Enriquecimiento de competencias (5 columnas, fase de integracion):
    Las competencias NO se agregan como filas: hacerlo multiplicaria el dataset
    por ~21 y dejaria sin llave primaria. Se agregan como CONTADORES por
    experiencia, de modo que el grano canonico sigue siendo 1 fila = 1
    experiencia y todo el pipeline descendente (limpieza, outliers, modelos)
    sigue operando sin cambios.

    Que significa "skill de una persona" (leer antes de usar):
        ESCO describe lo que un CARGO exige, no lo que un INDIVIDUO sabe. El
        dato de skills de una persona no existe en ninguna fuente: se ATRIBUYE
        a partir del oficio que ocupaba. Cualquier lectura debe decir "este cargo
        exige N competencias", nunca "esta persona sabe N cosas".
        `saber_skills` deja explicito el otro caso: cuando no hay oficio
        clasificado las cuentas quedan VACIAS, no en 0. Un 0 afirmaria que el
        cargo no exige ninguna competencia, que es falso; vacio afirma que no
        sabemos cual era el cargo. Son cosas opuestas y no deben mezclarse.

        `veces_ese_oficio` existe para que la reincidencia no se pierda: una
        persona que repite el mismo cargo 19 veces tiene 19 filas (una por
        experiencia, con sus fechas), todas con veces_ese_oficio=19, y sus
        competencias NO se repiten dentro de cada fila. Sin esta columna, el
        conteo de competencias seria ambiguo entre "un cargo duro" y "muchos
        periodos en el mismo cargo".

Salida (unica): `data/03_processed/empleos.csv` (16 columnas), canonica.
`limpiar_empleos.py` la lee y exporta `empleos_limpio.csv` (19 columnas).

Como ejecutar:
    python src/limpieza/integrar_empleos.py

Requisitos:
    pandas (CSV como texto: dtype=str + keep_default_na=False para conservar
    ceros a la izquierda y literales 'None'/'Present'/'unknown').
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


def _raiz_proyecto() -> Path:
    """Raiz del repo: busca hacia arriba la carpeta `data/` desde este archivo."""
    p = Path(__file__).resolve().parent
    while not (p / "data").exists() and p != p.parent:
        p = p.parent
    return p


RAIZ = _raiz_proyecto()
INTERIM = RAIZ / "data" / "02_interim"
PROC = RAIZ / "data" / "03_processed"

# Particiones del dato crudo de JobHop que forman el integrado (decidido por el
# equipo: test + val; la particion train queda fuera de este dataset).
PARTICIONES_JOBHOP = ["JobHop_v2_test_limpio.csv", "JobHop_v2_val_limpio.csv"]

OCCUPATIONS = INTERIM / "ESCO" / "occupations_en_limpio.csv"
ISCO_GROUPS = INTERIM / "ESCO" / "ISCOGroups_en_limpio.csv"
# Puente de competencias. Vive en data/02_interim/SKILLS/ porque se limpio aparte
# del resto de ESCO; `limpiar_datos.py` lo descubre con rglob y conserva la
# subcarpeta, asi que la ruta refleja esa organizacion.
SKILL_RELATIONS = INTERIM / "SKILLS" / "occupationSkillRelations_en_limpio.csv"
SALIDA = PROC / "empleos.csv"

# Solo se usan las competencias 'essential' (el piso minimo del cargo). Las
# 'optional' son telemetria de jerarquia y se descartan por decision de alcance.
RELACION_KEPT = "essential"

# Orden de columnas canonico del integrado (16 columnas).
COLUMNAS = [
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
    # --- Enriquecimiento de competencias (contadores, no filas) ---
    "n_skills_essential",
    "n_skills_competence",
    "n_skills_knowledge",
    "n_skills_sin_tipo",
    "veces_ese_oficio",
    "saber_skills",
]

# Columnas de contadores. Se dejan VACIAS cuando no hay oficio clasificado:
# vacio = "no sabemos el cargo"; 0 = "el cargo no exige nada" (falso).
CONTADORES_SKILL = [
    "n_skills_essential",
    "n_skills_competence",
    "n_skills_knowledge",
    "n_skills_sin_tipo",
]

# Valores admitidos de `saber_skills`.
SABER_OK = "ok"
SABER_NO_CLASIFICADO = "no_clasificado"


def _cargar(ruta: Path) -> pd.DataFrame:
    """Lee un CSV de texto: solo la celda vacia es NaN."""
    return pd.read_csv(ruta, dtype=str, encoding="utf-8", keep_default_na=False,
                       na_values=[""])


def clave_trimestre(valor) -> tuple:
    """'Q1 2000' -> (2000, 1). 'Present'/no parseable -> al final."""
    if pd.isna(valor) or str(valor).strip().lower() == "present":
        return (9999, 4)
    partes = str(valor).strip().split()
    if len(partes) != 2 or not partes[0].startswith("Q"):
        return (0, 0)
    try:
        return (int(partes[1]), int(partes[0][1]))
    except ValueError:
        return (0, 0)


def main() -> None:
    faltantes = [p for p in PARTICIONES_JOBHOP if not (INTERIM / p).exists()]
    if faltantes:
        raise FileNotFoundError(
            "Faltan limpias de JobHop en data/02_interim/: " + ", ".join(faltantes)
            + "\nEjecuta primero: python src/limpieza/limpiar_datos.py"
        )
    if not OCCUPATIONS.exists() or not ISCO_GROUPS.exists():
        raise FileNotFoundError("Faltan las limpias de ESCO en data/02_interim/ESCO/.")
    if not SKILL_RELATIONS.exists():
        raise FileNotFoundError(
            f"Falta el puente de competencias: {SKILL_RELATIONS}\n"
            "Ejecuta primero: python src/limpieza/limpiar_datos.py"
        )

    print("=" * 78)
    print("INTEGRACION DE EMPLEOS (union test + val, cruce con ESCO)")
    print("=" * 78)

    # 1. Union de las particiones limpias de JobHop (test + val).
    partes = [_cargar(INTERIM / p) for p in PARTICIONES_JOBHOP]
    for p, df in zip(PARTICIONES_JOBHOP, partes):
        print(f"  {p}: {len(df):,} filas / {df['resume_id'].nunique():,} personas")
    jh = pd.concat(partes, ignore_index=True)

    n_dup = int(jh.duplicated().sum())
    if n_dup:
        jh = jh.drop_duplicates().reset_index(drop=True)
        print(f"Union: {n_dup:,} filas duplicadas exactas inter-particion eliminadas.")

    # 2. Orden canonico por persona y por trimestre real (misma clave que la
    #    limpieza de JobHop).
    jh["_ini"] = jh["start_date"].map(clave_trimestre)
    jh["_fin"] = jh["end_date"].map(clave_trimestre)
    jh = jh.sort_values(["resume_id", "_ini", "_fin"]).drop(
        columns=["_ini", "_fin"]
    ).reset_index(drop=True)

    print(f"\nUnion test+val limpia: {len(jh):,} filas / {jh['resume_id'].nunique():,} personas")

    # 3. Cruce directo con occupations (matched_code == code).
    occ = _cargar(OCCUPATIONS).drop_duplicates(subset="code")
    m = jh.merge(
        occ[["code", "preferredLabel", "iscoGroup"]].rename(columns={
            "code": "occupation_code",
            "preferredLabel": "occupation_label",
            "iscoGroup": "isco_group",
        }),
        how="left",
        left_on="matched_code",
        right_on="occupation_code",
    )

    # 4. Rescate por prefijo (grupo ISCO-08 de 4 digitos) cuando no hay cruce.
    ig = _cargar(ISCO_GROUPS).drop_duplicates(subset="code")
    prefijo = m["matched_code"].str[:4]
    prefijo_valido = prefijo.isin(set(ig["code"]))

    emparejado = pd.Series("unknown", index=m.index, dtype=str)
    emparejado = emparejado.where(m["occupation_code"].isna(), other="ok")
    emparejado = emparejado.where(
        ~(m["occupation_code"].isna() & prefijo_valido), other="rescatado"
    )
    m["emparejado"] = emparejado

    m["isco_group"] = m["isco_group"].where(
        m["occupation_code"].notna(), other=prefijo.where(prefijo_valido)
    )
    etiqueta_ig = ig.set_index("code")["preferredLabel"]
    m["isco_group_label"] = m["isco_group"].map(etiqueta_ig)
    m["isco_level"] = m["isco_group"].map(lambda c: "4" if pd.notna(c) else "")

    # 4b. Enriquecimiento de competencias: CONTADORES por ocupacion.
    #     El puente de skills usa `occupationUri` (UUID), no `code`, asi que hay
    #     que traducir con occupations antes de poder contar.
    rel = _cargar(SKILL_RELATIONS)
    rel = rel.loc[rel["relationType"].eq(RELACION_KEPT)]
    rel = rel.drop_duplicates(subset=["occupationUri", "skillUri"])
    print(f"\nPares de competencia '{RELACION_KEPT}': {len(rel):,}")

    codigo_uri = occ[["code", "conceptUri"]].drop_duplicates(subset="code")
    par = rel.merge(codigo_uri, left_on="occupationUri", right_on="conceptUri",
                    how="inner")
    # ESCO escribe esta columna en camelCase; se renombra en la frontera.
    par = par.rename(columns={"skillType": "skill_type", "code": "occupation_code"})
    conteo = (
        par.groupby("occupation_code")
        .agg(
            n_skills_essential=("skillUri", "size"),
            n_skills_competence=("skill_type",
                                 lambda s: int(s.eq("skill/competence").sum())),
            n_skills_knowledge=("skill_type",
                                lambda s: int(s.eq("knowledge").sum())),
            # 39 de las 67.600 relaciones 'essential' llegan sin `skillType`
            # (defecto conocido de la fuente, documentado en el README). Sin
            # este bucket la suma competence + knowledge no cerraria contra el
            # total en las experiencias de esos oficios.
            n_skills_sin_tipo=("skill_type",
                               lambda s: int(s.isna().sum())),
        )
    )
    print(f"Ocupaciones con competencias: {len(conteo):,} | "
          f"mediana {conteo['n_skills_essential'].median():.0f} | "
          f"max {conteo['n_skills_essential'].max()}")

    for col in CONTADORES_SKILL:
        m[col] = m["occupation_code"].map(conteo[col])

    # 4c. Reincidencia: cuantas experiencias tiene esta persona en ESTE oficio.
    #     Cuenta sobre el merged, no sobre JobHop, para que la unidad sea la
    #     experiencia clasificada (la misma que aporta cada fila del dataset).
    m["veces_ese_oficio"] = (
        m.groupby(["resume_id", "occupation_code"])["occupation_code"]
        .transform("size")
        .where(m["occupation_code"].notna())
    )

    # 4d. Flag de Sabibilidad. 'rescatado' cae en 'no_clasificado' porque ESCO
    #     solo publica relaciones de competencia a nivel de OCUPACION, no de
    #     grupo ISCO: aunque sepamos el area, no hay con que contar skills.
    m["saber_skills"] = SABER_OK
    m.loc[m["occupation_code"].isna(), "saber_skills"] = SABER_NO_CLASIFICADO

    n_ok = int(m["saber_skills"].eq(SABER_OK).sum())
    print(f"\nsaber_skills: '{SABER_OK}' {n_ok:,} ({100 * n_ok / len(m):.1f} %) | "
          f"'{SABER_NO_CLASIFICADO}' {len(m) - n_ok:,} "
          f"({100 * (len(m) - n_ok) / len(m):.1f} %)")
    print("  (los contadores quedan VACIOS en 'no_clasificado', nunca en 0)")

    # 5. Columnas canonicas y escritura.
    empleos = m[COLUMNAS]
    print(f"\nemparejado:")
    print(empleos["emparejado"].value_counts(dropna=False).rename("filas").to_string())
    print(f"occupation_code NaN: {int(empleos['occupation_code'].isna().sum()):,}")
    print(f"n_skills_essential vacio: "
          f"{int(empleos['n_skills_essential'].isna().sum()):,}")

    PROC.mkdir(parents=True, exist_ok=True)
    empleos.to_csv(SALIDA, index=False, encoding="utf-8")
    print(f"\nEscrito: {SALIDA} ({SALIDA.stat().st_size / 1e6:.1f} MB) | "
          f"{empleos.shape[0]:,} filas x {empleos.shape[1]} columnas")

    # 6. Canon para EXPECTED/CANONICOS de limpiar_empleos.py (auditoria).
    print("\n" + "#" * 78)
    print("CANON PARA limpiar_empleos.py (EXPECTED / CANONICOS)")
    print("#" * 78)
    d = empleos
    anio_ini = pd.to_numeric(d["start_date"].str.extract(r"(\d{4})$", expand=False),
                             errors="coerce")
    anio_fin = pd.to_numeric(d["end_date"].str.extract(r"(\d{4})$", expand=False),
                             errors="coerce")
    futuras = int(((anio_ini > 2026) | (anio_fin > 2026)).sum())
    print(f"filas_original            : {len(d)}")
    print(f"personas_original         : {int(d['resume_id'].nunique())}")
    print(f"none_recategorizados      : {int(d['university_level'].eq('None').sum())}")
    print(f"fechas_futuras            : {futuras}")
    print(f"clave_corta_fin           : {int(d.duplicated(subset=['resume_id','start_date','end_date'], keep='first').sum())}")
    print(f"clave_corta_codigo        : {int(d.duplicated(subset=['resume_id','start_date','matched_code'], keep='first').sum())}")

    def ordinal(serie):
        partes = serie.str.extract(r"^Q([1-4])\s+(\d{4})$")
        a = pd.to_numeric(partes[1], errors="coerce")
        t = pd.to_numeric(partes[0], errors="coerce")
        return a * 4 + t

    dur = ordinal(d["end_date"]) - ordinal(d["start_date"]) + 1
    dur_s = dur.dropna()
    q1, q3 = dur_s.quantile([0.25, 0.75])
    iqr = q3 - q1
    sup = q3 + 1.5 * iqr
    fuera = (dur_s < q1 - 1.5 * iqr) | (dur_s > sup)
    print(f"duracion_iqr_q1           : {float(q1)}")
    print(f"duracion_iqr_q3           : {float(q3)}")
    print(f"duracion_iqr_superior     : {float(sup)}")
    print(f"duracion_maxima           : {int(dur_s.max())}")
    print(f"fuera_iqr_filas           : {int(fuera.sum())}")
    print(f"fuera_iqr_personas        : {int(d.loc[fuera.index[fuera.values], 'resume_id'].nunique())}")
    es_unk = d["emparejado"].eq("unknown")
    print(f"personas_unknown          : {int(d.loc[es_unk, 'resume_id'].nunique())}")
    print(f"personas_historial_unknown: {int(d.groupby('resume_id')['emparejado'].apply(lambda s: s.eq('unknown').all()).sum())}")
    print(f"CANONICOS emparejado      : {int(d['emparejado'].nunique())}")
    print(f"CANONICOS university_level: {int(d['university_level'].nunique(dropna=True))}")
    print(f"CANONICOS isco_group_label: {int(d['isco_group_label'].nunique(dropna=True))}")
    print(f"CANONICOS occupation_label: {int(d['occupation_label'].nunique(dropna=True))}")

    # Canon de las columnas de competencias (para los asserts de
    # limpiar_empleos.py). Se imprime el rango de la mediana para dejar
    # constancia de la dispersion del piso de exigencia por cargo.
    print(f"CANONICOS saber_skills     : {int(d['saber_skills'].nunique())}")
    print(f"CANONICOS n_skills_essential: {int(d['n_skills_essential'].nunique(dropna=True))}")
    print(f"CANONICOS veces_ese_oficio : {int(d['veces_ese_oficio'].nunique(dropna=True))}")
    print(f"mediana_n_skills_essential : {float(d['n_skills_essential'].median()):.0f}")
    print(f"max_veces_ese_oficio       : {int(d['veces_ese_oficio'].max())}")
    print(f"filas_saber_skills_ok      : {int(d['saber_skills'].eq(SABER_OK).sum())}")
    print(f"filas_sin_oficio           : {int(d['occupation_code'].isna().sum())}")


if __name__ == "__main__":
    main()