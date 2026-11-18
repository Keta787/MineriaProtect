"""
unificar_raw_completo.py
========================
Une TODOS los CSV de `data/01_raw/` en un unico dataset, enlazados por el
codigo ESCO de la ocupacion:

    JobHop_v2_train.csv + JobHop_v2_test.csv + JobHop_v2_val.csv   (concat)
        -- matched_code = code (N:1) -------------> ESCO/occupations_en.csv
        -- prefijo ISCO de 4 digitos (rescate) ---> ESCO/ISCOGroups_en.csv
    occupations.conceptUri = occupationUri -------> SKILLS/occupationSkillRelations_en.csv
    occupationSkillRelations.skillUri = conceptUri -> SKILLS/skills_en.csv

Por que existe
--------------
`integrar_empleos.py` solo unia las particiones test + val (376.567 filas) y
dejaba fuera la particion train (1.594.827 filas). Este script construye la
union COMPLETA (1.993.291 filas) directamente desde el dato crudo.

Reglas
------
- Union pura: NO se elimina ninguna fila (ni sin `start_date` ni duplicados
  exactos). La calidad se expresa con banderas, no borrando.
- Se repiten las reglas de `integrar_empleos.py` (emparejado ok / rescatado /
  unknown, contadores de competencias 'essential', veces_ese_oficio,
  saber_skills), las banderas de la fase 4 de `limpiar_empleos.py`
  (es_unknown_ocupacion, es_rescatado, es_vigente) y las listas de nombres de
  `unificar_competencias_empleos.py` (skills | knowledge | sin_tipo).
- Grano: 1 fila = 1 experiencia laboral. Todas las uniones son N:1 y se
  validan para que nunca multipliquen filas.
- Cuando no hay oficio clasificado, contadores y listas quedan VACIOS (nunca 0):
  vacio = "no sabemos el cargo"; 0 = "el cargo no exige nada" (falso).
- `university_level` y `end_date` se dejan tal cual vienen del crudo. El empleo
  vigente llega con `end_date` vacio y se marca con `es_vigente = True`.
- Los archivos de `data/01_raw/` solo se leen; nunca se modifican.

Salida: `data/02_interim/Unificacion/empleos_unificado_completo.csv` (23 columnas)

Como ejecutar (desde la raiz del repo):
    python scripts/pipeline/limpieza/unificar_raw_completo.py
"""

from __future__ import annotations

import sys
import time
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
RAW = RAIZ / "data" / "01_raw"
SALIDA_DIR = RAIZ / "data" / "02_interim" / "Unificacion"
SALIDA = SALIDA_DIR / "empleos_unificado_completo.csv"

PARTICIONES = ("train", "test", "val")
JOBHOP = [RAW / f"JobHop_v2_{p}.csv" for p in PARTICIONES]
OCCUPATIONS = RAW / "ESCO" / "occupations_en.csv"
ISCO_GROUPS = RAW / "ESCO" / "ISCOGroups_en.csv"
SKILL_RELATIONS = RAW / "SKILLS" / "occupationSkillRelations_en.csv"
SKILLS = RAW / "SKILLS" / "skills_en.csv"

RELACION_KEPT = "essential"
SEPARADOR = "|"
SABER_OK = "ok"
SABER_NO_CLASIFICADO = "no_clasificado"

CONTADORES = [
    "n_skills_essential",
    "n_skills_competence",
    "n_skills_knowledge",
    "n_skills_sin_tipo",
]
LISTAS = ["skills", "knowledge", "sin_tipo"]

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
    "n_skills_essential",
    "n_skills_competence",
    "n_skills_knowledge",
    "n_skills_sin_tipo",
    "veces_ese_oficio",
    "saber_skills",
    "es_unknown_ocupacion",
    "es_rescatado",
    "es_vigente",
    "skills",
    "knowledge",
    "sin_tipo",
]


def _cargar(ruta: Path) -> pd.DataFrame:
    """Lee un CSV como texto: solo la celda vacia es NaN (conserva 'None'/'Present')."""
    return pd.read_csv(ruta, dtype=str, encoding="utf-8",
                       keep_default_na=False, na_values=[""])


def _ordinal_trimestre(serie: pd.Series) -> pd.Series:
    """'Q1 2000' -> 20001. NaN/'Present' -> 99994 (al final). No parseable -> 0.

    Version vectorizada de `clave_trimestre` de `integrar_empleos.py`.
    """
    partes = serie.str.strip().str.extract(r"^Q([1-4])\s+(\d{4})$")
    ordinal = pd.to_numeric(partes[1], errors="coerce") * 10 + pd.to_numeric(
        partes[0], errors="coerce")
    es_fin = serie.isna() | serie.str.strip().str.lower().eq("present")
    return ordinal.where(~es_fin, 99994).fillna(0).astype("int64")


def cargar_jobhop() -> pd.DataFrame:
    """Concatena las 3 particiones de JobHop sin eliminar filas y las ordena."""
    partes = []
    for ruta in JOBHOP:
        df = _cargar(ruta)
        print(f"  {ruta.name}: {len(df):,} filas / {df['resume_id'].nunique():,} personas")
        partes.append(df)
    total_esperado = sum(len(p) for p in partes)
    jh = pd.concat(partes, ignore_index=True)
    assert len(jh) == total_esperado

    jh["_rid"] = pd.to_numeric(jh["resume_id"], errors="raise")
    jh["_ini"] = _ordinal_trimestre(jh["start_date"])
    jh["_fin"] = _ordinal_trimestre(jh["end_date"])
    jh = (jh.sort_values(["_rid", "_ini", "_fin"], kind="stable")
            .drop(columns=["_rid", "_ini", "_fin"])
            .reset_index(drop=True))
    print(f"Union JobHop: {len(jh):,} filas / {jh['resume_id'].nunique():,} personas "
          f"(sin start_date: {int(jh['start_date'].isna().sum()):,} | "
          f"duplicados exactos: {int(jh.duplicated().sum()):,}; se CONSERVAN)")
    return jh


def cruzar_ocupaciones(jh: pd.DataFrame, occ: pd.DataFrame,
                       ig: pd.DataFrame) -> pd.DataFrame:
    """Cruce directo por codigo ESCO y rescate por prefijo ISCO de 4 digitos."""
    mapa = occ[["code", "preferredLabel", "iscoGroup"]].rename(columns={
        "code": "occupation_code",
        "preferredLabel": "occupation_label",
        "iscoGroup": "isco_group",
    })
    m = jh.merge(mapa, how="left", left_on="matched_code",
                 right_on="occupation_code", validate="many_to_one")
    assert len(m) == len(jh), "El cruce con occupations multiplico filas"

    prefijo = m["matched_code"].str[:4]
    prefijo_valido = prefijo.isin(set(ig["code"]))
    sin_codigo = m["occupation_code"].isna()

    m["emparejado"] = "unknown"
    m.loc[~sin_codigo, "emparejado"] = "ok"
    m.loc[sin_codigo & prefijo_valido, "emparejado"] = "rescatado"

    m["isco_group"] = m["isco_group"].where(~sin_codigo, prefijo.where(prefijo_valido))
    m["isco_group_label"] = m["isco_group"].map(ig.set_index("code")["preferredLabel"])
    m["isco_level"] = pd.Series(pd.NA, index=m.index, dtype="object")
    m.loc[m["isco_group"].notna(), "isco_level"] = "4"
    return m


def construir_perfil_competencias(occ: pd.DataFrame, rel: pd.DataFrame,
                                  skills: pd.DataFrame) -> pd.DataFrame:
    """Una fila por occupation_code con contadores y listas de competencias 'essential'.

    El nombre sale de `skills_en.preferredLabel` (respaldo: `skillLabel` de la
    relacion); el tipo sale de `skillType` de la relacion, para conservar el
    bucket `sin_tipo` (relaciones que la fuente entrega sin tipo).
    """
    rel = rel.loc[rel["relationType"].eq(RELACION_KEPT)]
    rel = rel.drop_duplicates(subset=["occupationUri", "skillUri"])

    par = rel.merge(occ[["code", "conceptUri"]], left_on="occupationUri",
                    right_on="conceptUri", how="inner", validate="many_to_one")
    par = par.drop(columns="conceptUri").merge(
        skills[["conceptUri", "preferredLabel"]], left_on="skillUri",
        right_on="conceptUri", how="left", validate="many_to_one")
    par["nombre"] = par["preferredLabel"].fillna(par["skillLabel"])
    assert not par["nombre"].str.contains(SEPARADOR, regex=False).any(), (
        f"Una competencia contiene '{SEPARADOR}', el separador reservado")

    par["tipo"] = "sin_tipo"
    par.loc[par["skillType"].eq("skill/competence"), "tipo"] = "skills"
    par.loc[par["skillType"].eq("knowledge"), "tipo"] = "knowledge"
    par = par.sort_values(["code", "tipo", "nombre"], kind="stable")

    listas = (par.groupby(["code", "tipo"])["nombre"]
                 .agg(SEPARADOR.join)
                 .unstack("tipo")
                 .reindex(columns=LISTAS))
    conteos = (par.groupby(["code", "tipo"]).size()
                  .unstack("tipo", fill_value=0)
                  .reindex(columns=LISTAS, fill_value=0))
    perfil = pd.DataFrame({
        "n_skills_essential": conteos.sum(axis=1),
        "n_skills_competence": conteos["skills"],
        "n_skills_knowledge": conteos["knowledge"],
        "n_skills_sin_tipo": conteos["sin_tipo"],
    }).join(listas)
    perfil.index.name = "occupation_code"
    print(f"Pares '{RELACION_KEPT}': {len(par):,} | oficios con competencias: "
          f"{len(perfil):,} | mediana {perfil['n_skills_essential'].median():.0f} | "
          f"max {perfil['n_skills_essential'].max()}")
    return perfil.reset_index()


def enriquecer(m: pd.DataFrame, perfil: pd.DataFrame) -> pd.DataFrame:
    """Une el perfil de competencias (N:1) y calcula reincidencia, saber y banderas."""
    n = len(m)
    m = m.merge(perfil, on="occupation_code", how="left", validate="many_to_one")
    assert len(m) == n, "La union de competencias multiplico filas"

    sin_codigo = m["occupation_code"].isna()
    # Ninguna fila sin codigo puede recibir competencias (NaN no debe emparejar).
    assert m.loc[sin_codigo, CONTADORES + LISTAS].isna().all().all()

    for col in CONTADORES:
        m[col] = m[col].astype("Int64")

    m["veces_ese_oficio"] = (
        m.groupby(["resume_id", "occupation_code"])["occupation_code"]
         .transform("size")
         .where(~sin_codigo)
         .astype("Int64")
    )
    m["saber_skills"] = SABER_OK
    m.loc[sin_codigo, "saber_skills"] = SABER_NO_CLASIFICADO

    m["es_unknown_ocupacion"] = m["emparejado"].eq("unknown")
    m["es_rescatado"] = m["emparejado"].eq("rescatado")
    # En el crudo el empleo vigente llega con `end_date` VACIO (no existe el
    # literal 'Present'; ese relleno lo hacia `limpiar_datos.py`). Se conserva el
    # valor crudo y la censura se expresa con la bandera.
    m["es_vigente"] = m["end_date"].isna() | m["end_date"].eq("Present")
    return m[COLUMNAS]


def validar(df: pd.DataFrame, filas_esperadas: int, personas_esperadas: int) -> None:
    """Asserts de integridad del dataset unificado."""
    assert list(df.columns) == COLUMNAS and len(COLUMNAS) == 23
    assert len(df) == filas_esperadas, f"{len(df):,} != {filas_esperadas:,}"
    assert df["resume_id"].nunique() == personas_esperadas

    sin_codigo = df["occupation_code"].isna()
    assert (sin_codigo == (df["es_unknown_ocupacion"] | df["es_rescatado"])).all(), (
        "occupation_code vacio no reconciliado con las banderas")

    ok = df["saber_skills"].eq(SABER_OK)
    assert (ok == ~sin_codigo).all()
    # Oficios ESCO sin ninguna relacion 'essential' quedarian con contador vacio.
    sin_perfil = ok & df["n_skills_essential"].isna()
    if sin_perfil.any():
        print(f"AVISO: {int(sin_perfil.sum()):,} filas 'ok' cuyo oficio no tiene "
              f"competencias '{RELACION_KEPT}' en ESCO")
    con = ok & df["n_skills_essential"].notna()
    suma = (df.loc[con, "n_skills_competence"] + df.loc[con, "n_skills_knowledge"]
            + df.loc[con, "n_skills_sin_tipo"])
    assert (suma == df.loc[con, "n_skills_essential"]).all(), "Contadores no suman el total"

    for lista, contador in zip(LISTAS, CONTADORES[1:]):
        largo = df[lista].str.split(SEPARADOR, regex=False).str.len().fillna(0)
        assert (largo[con] == df.loc[con, contador]).all(), (
            f"La lista {lista} no coincide con {contador}")

    no_clas = ~ok
    assert df.loc[no_clas, CONTADORES + LISTAS + ["veces_ese_oficio"]].isna().all().all(), (
        "Filas no_clasificado con contadores/listas no vacios")
    print("Validacion: OK (todos los asserts pasaron)")


def resumen(df: pd.DataFrame) -> None:
    """Imprime las distribuciones clave del dataset unificado."""
    print("\nemparejado:")
    print(df["emparejado"].value_counts(dropna=False).to_string())
    print("\nsaber_skills:")
    print(df["saber_skills"].value_counts(dropna=False).to_string())
    print(f"\nes_vigente: {int(df['es_vigente'].sum()):,} | "
          f"occupation_code vacio: {int(df['occupation_code'].isna().sum()):,}")


def main() -> None:
    """Orquesta carga, cruces, validacion y escritura."""
    t0 = time.time()
    faltantes = [p for p in [*JOBHOP, OCCUPATIONS, ISCO_GROUPS, SKILL_RELATIONS, SKILLS]
                 if not p.exists()]
    if faltantes:
        raise FileNotFoundError("Faltan crudos: " + ", ".join(map(str, faltantes)))

    print("=" * 78)
    print("UNIFICACION COMPLETA DE data/01_raw (train + test + val + ESCO + SKILLS)")
    print("=" * 78)

    jh = cargar_jobhop()
    filas, personas = len(jh), jh["resume_id"].nunique()

    occ = _cargar(OCCUPATIONS)
    n_dup = int(occ["code"].duplicated().sum())
    occ = occ.drop_duplicates(subset="code", keep="first")
    print(f"occupations: {len(occ):,} oficios ({n_dup} code duplicados descartados)")
    ig = _cargar(ISCO_GROUPS).drop_duplicates(subset="code", keep="first")
    rel = _cargar(SKILL_RELATIONS)
    skills = _cargar(SKILLS).drop_duplicates(subset="conceptUri", keep="first")

    m = cruzar_ocupaciones(jh, occ, ig)
    perfil = construir_perfil_competencias(occ, rel, skills)
    df = enriquecer(m, perfil)

    validar(df, filas, personas)
    resumen(df)

    SALIDA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nEscribiendo {SALIDA} ...")
    df.to_csv(SALIDA, index=False, encoding="utf-8")
    print(f"Escrito: {SALIDA.stat().st_size / 1e6:,.1f} MB | "
          f"{df.shape[0]:,} filas x {df.shape[1]} columnas | {time.time() - t0:.0f} s")
    print("Los archivos de data/01_raw no fueron modificados.")


if __name__ == "__main__":
    main()

