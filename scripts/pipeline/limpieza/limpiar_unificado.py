"""
limpiar_unificado.py
====================
Aplica el pipeline formal de limpieza (9 principios de Data Cleaning & Data
Hygiene) sobre `data/02_interim/Unificacion/empleos_unificado_completo.csv`
(1.993.291 filas x 23 columnas) y exporta el dataset limpio en:

    data/03_processed/Limpio/empleos_unificado_limpio.csv
    data/03_processed/Limpio/bitacora_limpieza_unificado.csv

Etapas ejecutadas en orden:
    1. Eliminacion de filas vacias en fechas (sin start_date ni end_date: 72.726).
    2. Validacion contra reglas de dominio (fechas futuras > 2026: 11).
    3. Estandarizacion de censura (end_date vacio con start_date valido ->
       'Present', sincronizando es_vigente = True en 97.641 filas).
    4. Eliminacion de duplicados exactos (37.553 filas repetidas).
    5. Colapso de variantes del mismo empleo (R7): misma persona, mismo
       start_date y mismo matched_code con distinto end_date -> se conserva el
       fin mas tardio ('Present' tiene prioridad maxima; -11.987 filas).
    6. Imputacion jerarquica por dominio ESCO (R8): de las 12.588 filas en
       estado 'rescatado', las 9.293 cuyo codigo tiene oficio padre en ESCO
       reciben occupation_code, occupation_label y el perfil completo de
       competencias del oficio padre, pasando a emparejado='ok' y
       saber_skills='ok'.
    7. Estandarizacion de categorias y recuentos: university_level 'None'/vacio
       -> 'No reportado' (215.600 filas), limpieza de espacios extremos y
       recalculo de veces_ese_oficio sobre la trayectoria limpia.
    8. Auditoria de outliers IQR en duracion trimestral (conservando la cola
       larga de estabilidad laboral) y validacion de contratos (Data Hygiene).

Como ejecutar (desde la raiz del repositorio):
    python scripts/pipeline/limpieza/limpiar_unificado.py
"""

from __future__ import annotations

import csv
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

# Importar utilidades y constantes canonicas de la unificacion
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unificar_raw_completo import (  # noqa: E402
    COLUMNAS,
    CONTADORES,
    LISTAS,
    OCCUPATIONS,
    RAIZ,
    SABER_NO_CLASIFICADO,
    SABER_OK,
    SEPARADOR,
    SKILL_RELATIONS,
    SKILLS,
    _cargar,
    _ordinal_trimestre,
    construir_perfil_competencias,
)

ENTRADA = RAIZ / "data" / "02_interim" / "Unificacion" / "empleos_unificado_completo.csv"
SALIDA_DIR = RAIZ / "data" / "03_processed" / "Limpio"
SALIDA = SALIDA_DIR / "empleos_unificado_limpio.csv"
BITACORA = SALIDA_DIR / "bitacora_limpieza_unificado.csv"

ANIO_CORTE = 2026
PATRON_TRIMESTRE = r"^Q([1-4])\s+(\d{4})$"
CLAVE_CRUDA = ["resume_id", "start_date", "end_date", "university_level", "matched_code"]
CLAVE_VARIANTE = ["resume_id", "start_date", "matched_code"]

EXPECTED = {
    "filas_entrada": 1_993_291,
    "personas_entrada": 355_315,
    "sin_fechas_eliminadas": 72_726,
    "fechas_futuras_eliminadas": 11,
    "vigentes_present": 97_641,
    "duplicados_exactos_eliminados": 37_553,
    "variantes_colapsadas": 11_987,
    "rescatados_por_padre": 9_293,
    "rescatados_restantes": 3_295,
    "none_recategorizados": 215_600,
    "filas_salida": 1_871_014,
    "personas_salida": 355_308,
    "filas_ok_salida": 1_747_826,
}


def _registrar(
    bitacora: list[dict],
    etapa: str,
    principio: str,
    columna: str,
    filas_antes: int,
    filas_afectadas: int,
    filas_despues: int,
    accion: str,
    justificacion: str,
) -> None:
    """Agrega un registro auditable a la bitacora de limpieza."""
    bitacora.append(
        {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "etapa": etapa,
            "principio": principio,
            "columna": columna,
            "filas_antes": filas_antes,
            "filas_afectadas": filas_afectadas,
            "filas_eliminadas": filas_antes - filas_despues,
            "filas_despues": filas_despues,
            "accion": accion,
            "justificacion": justificacion,
        }
    )


def _buscar_padre_esco(codigo: str, codigos_validos: set[str]) -> str | None:
    """Recorta sufijos jerarquicos '.x' hasta hallar un oficio padre en ESCO."""
    if pd.isna(codigo):
        return None
    partes = str(codigo).strip().split(".")
    while len(partes) > 1:
        partes = partes[:-1]
        candidato = ".".join(partes)
        if candidato in codigos_validos:
            return candidato
    return None


def _extraer_anio_trimestre(serie: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Devuelve (anio, ordinal_trimestral) para una serie en formato 'Qn AAAA'."""
    partes = serie.str.strip().str.extract(PATRON_TRIMESTRE)
    anio = pd.to_numeric(partes[1], errors="coerce")
    trim = pd.to_numeric(partes[0], errors="coerce")
    return anio, anio * 4 + trim


def ejecutar_limpieza() -> tuple[pd.DataFrame, list[dict]]:
    """Ejecuta las 8 etapas de limpieza y devuelve (df_limpio, bitacora)."""
    if not ENTRADA.exists():
        raise FileNotFoundError(
            f"No existe el archivo de entrada: {ENTRADA}\n"
            "Ejecuta primero: python scripts/pipeline/limpieza/unificar_raw_completo.py"
        )

    print("=" * 78)
    print("PIPELINE DE LIMPIEZA SOBRE EL DATASET UNIFICADO COMPLETO")
    print("=" * 78)

    df = _cargar(ENTRADA)
    bitacora: list[dict] = []

    assert list(df.columns) == COLUMNAS, "Las columnas de entrada no coinciden con el esquema"
    assert len(df) == EXPECTED["filas_entrada"], (
        f"Filas de entrada inesperadas: {len(df):,} != {EXPECTED['filas_entrada']:,}"
    )
    personas_ini = int(df["resume_id"].nunique())
    assert personas_ini == EXPECTED["personas_entrada"]
    print(f"Entrada: {len(df):,} filas | {personas_ini:,} personas")

    # ------------------------------------------------------------------
    # Etapa 1: Eliminacion de filas vacias en fechas (nulos criticos)
    # ------------------------------------------------------------------
    n_antes = len(df)
    sin_start = df["start_date"].isna()
    sin_end = df["end_date"].isna()
    assert int((sin_start & ~sin_end).sum()) == 0, (
        "Existen filas sin start_date pero con end_date presente"
    )
    n_sin_fechas = int(sin_start.sum())
    assert n_sin_fechas == EXPECTED["sin_fechas_eliminadas"]

    df = df.loc[~sin_start].reset_index(drop=True)
    _registrar(
        bitacora,
        etapa="1_filas_sin_fechas",
        principio="Eliminacion de filas vacias / Manejo de nulos criticos",
        columna="start_date, end_date",
        filas_antes=n_antes,
        filas_afectadas=n_sin_fechas,
        filas_despues=len(df),
        accion="Eliminar filas sin start_date ni end_date",
        justificacion=(
            "Sin fechas no es posible ubicar la experiencia en la secuencia "
            "temporal ni calcular duracion; ademas contaminaban es_vigente."
        ),
    )
    print(f"[1/8] Sin fechas eliminadas      : -{n_sin_fechas:,} -> {len(df):,} filas")

    # ------------------------------------------------------------------
    # Etapa 2: Validacion contra reglas de dominio (fechas futuras / invertidas)
    # ------------------------------------------------------------------
    n_antes = len(df)
    anio_ini, ord_ini = _extraer_anio_trimestre(df["start_date"])
    anio_fin, ord_fin = _extraer_anio_trimestre(df["end_date"])

    invertidas = int((ord_fin.notna() & (ord_fin < ord_ini)).sum())
    assert invertidas == 0, f"Se detectaron {invertidas} filas con end_date < start_date"

    futuras = (anio_ini > ANIO_CORTE) | (anio_fin > ANIO_CORTE)
    n_futuras = int(futuras.sum())
    assert n_futuras == EXPECTED["fechas_futuras_eliminadas"]

    df = df.loc[~futuras].reset_index(drop=True)
    _registrar(
        bitacora,
        etapa="2_fechas_futuras",
        principio="Validacion contra reglas de negocio o dominio",
        columna="start_date, end_date",
        filas_antes=n_antes,
        filas_afectadas=n_futuras,
        filas_despues=len(df),
        accion=f"Eliminar filas con anio > {ANIO_CORTE}",
        justificacion="Fechas posteriores al anio de corte (2027-2029) son errores de captura.",
    )
    print(f"[2/8] Fechas futuras (> {ANIO_CORTE})    : -{n_futuras:,} -> {len(df):,} filas")

    # ------------------------------------------------------------------
    # Etapa 3: Estandarizacion de formatos y nulos por censura ('Present')
    # ------------------------------------------------------------------
    n_antes = len(df)
    mask_vigente = df["end_date"].isna() | df["end_date"].eq("Present")
    n_vigentes = int(mask_vigente.sum())
    assert n_vigentes == EXPECTED["vigentes_present"]

    df.loc[mask_vigente, "end_date"] = "Present"
    df["es_vigente"] = df["end_date"].eq("Present")
    _registrar(
        bitacora,
        etapa="3_estandarizar_present",
        principio="Estandarizacion de formatos y manejo de nulos por censura",
        columna="end_date, es_vigente",
        filas_antes=n_antes,
        filas_afectadas=n_vigentes,
        filas_despues=len(df),
        accion="Imputar end_date vacio como 'Present' y sincronizar es_vigente",
        justificacion=(
            "Representa empleos activos al capturar el CV (censura a la derecha) "
            "y unifica el formato con los modulos de transformacion y EDA."
        ),
    )
    print(f"[3/8] Censura 'Present'          : {n_vigentes:,} empleos vigentes estandarizados")

    # ------------------------------------------------------------------
    # Etapa 4: Eliminacion de duplicados exactos
    # ------------------------------------------------------------------
    n_antes = len(df)
    dup_exactos = df.duplicated(subset=CLAVE_CRUDA, keep="first")
    n_dup_exactos = int(dup_exactos.sum())
    assert n_dup_exactos == EXPECTED["duplicados_exactos_eliminados"]

    df = df.loc[~dup_exactos].reset_index(drop=True)
    _registrar(
        bitacora,
        etapa="4_duplicados_exactos",
        principio="Eliminacion de duplicados",
        columna=",".join(CLAVE_CRUDA),
        filas_antes=n_antes,
        filas_afectadas=n_dup_exactos,
        filas_despues=len(df),
        accion="Eliminar duplicados exactos conservando la primera aparicion",
        justificacion=(
            "Evita inflar veces_ese_oficio y evita falsas transiciones A->A "
            "producidas por repeticiones del extractor de CV."
        ),
    )
    print(f"[4/8] Duplicados exactos         : -{n_dup_exactos:,} -> {len(df):,} filas")

    # ------------------------------------------------------------------
    # Etapa 5: Colapso de variantes del mismo empleo (R7)
    # ------------------------------------------------------------------
    n_antes = len(df)
    df["_rid"] = pd.to_numeric(df["resume_id"], errors="raise")
    df["_ini"] = _ordinal_trimestre(df["start_date"])
    df["_fin"] = _ordinal_trimestre(df["end_date"])

    # Ordenar ascendente por _fin ('Present' = 99994 queda al final) y conservar 'last'
    df = df.sort_values(["_rid", "_ini", "matched_code", "_fin"], kind="stable")
    dup_variantes = df.duplicated(subset=CLAVE_VARIANTE, keep="last")
    n_variantes = int(dup_variantes.sum())
    assert n_variantes == EXPECTED["variantes_colapsadas"]

    df = (
        df.loc[~dup_variantes]
        .sort_values(["_rid", "_ini", "_fin"], kind="stable")
        .drop(columns=["_rid", "_ini", "_fin"])
        .reset_index(drop=True)
    )
    _registrar(
        bitacora,
        etapa="5_colapsar_variantes_fin",
        principio="Eliminacion de duplicados parciales / Consistencia temporal",
        columna="resume_id, start_date, matched_code, end_date",
        filas_antes=n_antes,
        filas_afectadas=n_variantes,
        filas_despues=len(df),
        accion="Colapsar por (resume_id, start_date, matched_code) conservando el end_date mas tardio",
        justificacion=(
            "Un mismo contrato en el mismo oficio y trimestre de inicio no "
            "puede tener multiples cierres; son fragmentos parciales del CV."
        ),
    )
    print(f"[5/8] Variantes colapsadas (R7)  : -{n_variantes:,} -> {len(df):,} filas")

    # ------------------------------------------------------------------
    # Etapa 6: Imputacion jerarquica por oficio padre ESCO en 'rescatado' (R8)
    # ------------------------------------------------------------------
    n_antes = len(df)
    occ = _cargar(OCCUPATIONS).drop_duplicates(subset="code", keep="first")
    rel = _cargar(SKILL_RELATIONS)
    skills = _cargar(SKILLS).drop_duplicates(subset="conceptUri", keep="first")
    perfil = construir_perfil_competencias(occ, rel, skills).set_index("occupation_code")

    codigos_esco = set(occ["code"])
    label_por_codigo = occ.set_index("code")["preferredLabel"]
    isco_por_codigo = occ.set_index("code")["iscoGroup"]

    mask_resc = df["emparejado"].eq("rescatado")
    padres = df.loc[mask_resc, "matched_code"].map(
        lambda c: _buscar_padre_esco(c, codigos_esco)
    )
    idx_con_padre = padres.index[padres.notna()]
    codigos_padre = padres.loc[idx_con_padre]

    n_rescatados_padre = len(idx_con_padre)
    assert n_rescatados_padre == EXPECTED["rescatados_por_padre"]

    df.loc[idx_con_padre, "occupation_code"] = codigos_padre.values
    df.loc[idx_con_padre, "occupation_label"] = codigos_padre.map(label_por_codigo).values
    df.loc[idx_con_padre, "isco_group"] = codigos_padre.map(isco_por_codigo).values
    df.loc[idx_con_padre, "emparejado"] = "ok"
    df.loc[idx_con_padre, "saber_skills"] = SABER_OK

    for col in CONTADORES:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
        df.loc[idx_con_padre, col] = codigos_padre.map(perfil[col]).astype("Int64").values
    for col in LISTAS:
        df.loc[idx_con_padre, col] = codigos_padre.map(perfil[col]).values

    n_resc_restantes = int(df["emparejado"].eq("rescatado").sum())
    assert n_resc_restantes == EXPECTED["rescatados_restantes"]

    _registrar(
        bitacora,
        etapa="6_rescate_oficio_padre_esco",
        principio="Manejo sistematico de nulos con imputacion jerarquica de dominio",
        columna="occupation_code, occupation_label, emparejado, saber_skills, skills",
        filas_antes=n_antes,
        filas_afectadas=n_rescatados_padre,
        filas_despues=len(df),
        accion="Asignar oficio padre ESCO (y su perfil de competencias) a 7 codigos rescatados con padre valido",
        justificacion=(
            "Los subcodigos detallados (ej. 3412.4.9) heredan la definicion y "
            "competencias esenciales de su oficio padre ESCO (3412.4)."
        ),
    )
    print(
        f"[6/8] Rescate oficio padre (R8)  : +{n_rescatados_padre:,} filas pasan a 'ok' "
        f"(quedan {n_resc_restantes:,} rescatado sin padre)"
    )

    # ------------------------------------------------------------------
    # Etapa 7: Normalizacion de categorias, textos y recalculo de indicadores
    # ------------------------------------------------------------------
    n_antes = len(df)
    for col in [
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
        "saber_skills",
    ]:
        df[col] = df[col].str.strip()

    mask_none = df["university_level"].isna() | df["university_level"].eq("None") | df["university_level"].eq("")
    n_none = int(mask_none.sum())
    assert n_none == EXPECTED["none_recategorizados"]
    df.loc[mask_none, "university_level"] = "No reportado"

    # Recalcular veces_ese_oficio sobre la trayectoria limpia y con padres ESCO asignados
    sin_codigo = df["occupation_code"].isna()
    for col in CONTADORES:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    df["veces_ese_oficio"] = (
        df.groupby(["resume_id", "occupation_code"])["occupation_code"]
        .transform("size")
        .where(~sin_codigo)
        .astype("Int64")
    )

    # Sincronizar banderas booleanas
    df["saber_skills"] = SABER_OK
    df.loc[sin_codigo, "saber_skills"] = SABER_NO_CLASIFICADO
    df["es_unknown_ocupacion"] = df["emparejado"].eq("unknown")
    df["es_rescatado"] = df["emparejado"].eq("rescatado")
    df["es_vigente"] = df["end_date"].eq("Present")

    _registrar(
        bitacora,
        etapa="7_normalizar_categorias_y_reincidencia",
        principio="Estandarizacion de formatos y recuentos derivados",
        columna="university_level, veces_ese_oficio, es_*",
        filas_antes=n_antes,
        filas_afectadas=n_none,
        filas_despues=len(df),
        accion="Recategorizar 'None' -> 'No reportado', normalizar espacios y recalcular veces_ese_oficio",
        justificacion=(
            "Evita que pandas interprete 'None' como NaN (faltante MNAR) y "
            "actualiza la reincidencia tras eliminar duplicados y rescatar padres."
        ),
    )
    print(f"[7/8] 'None' -> 'No reportado'   : {n_none:,} filas normalizadas + veces_ese_oficio recalculado")

    # ------------------------------------------------------------------
    # Etapa 8: Auditoria de outliers IQR (sin eliminar cola larga)
    # ------------------------------------------------------------------
    _, ord_ini = _extraer_anio_trimestre(df["start_date"])
    _, ord_fin = _extraer_anio_trimestre(df["end_date"])
    dur_q = (ord_fin - ord_ini + 1).dropna()
    q1, q3 = dur_q.quantile([0.25, 0.75])
    iqr = q3 - q1
    lim_sup = q3 + 1.5 * iqr
    n_outliers_iqr = int((dur_q > lim_sup).sum())

    _registrar(
        bitacora,
        etapa="8_auditoria_outliers_iqr",
        principio="Tratamiento cuidadoso de valores atipicos (outliers)",
        columna="start_date, end_date (duracion trimestral)",
        filas_antes=len(df),
        filas_afectadas=n_outliers_iqr,
        filas_despues=len(df),
        accion=f"Conservar cola larga (Q1={q1:.1f}, Q3={q3:.1f}, umbral Tukey={lim_sup:.1f} trim, max={int(dur_q.max())} trim)",
        justificacion=(
            "Las duraciones > 24.5 trimestres (~6 anios, hasta 40 anios) son "
            "carreras estables reales y no errores de captura."
        ),
    )
    print(
        f"[8/8] Auditoria IQR duracion     : Q1={q1:.1f}, Q3={q3:.1f}, sup={lim_sup:.1f} trim | "
        f"cola larga conservada: {n_outliers_iqr:,} filas"
    )

    return df[COLUMNAS], bitacora


def validar_data_hygiene(df: pd.DataFrame, bitacora: list[dict]) -> None:
    """Asserts de contrato de salida (Data Hygiene)."""
    assert list(df.columns) == COLUMNAS and len(COLUMNAS) == 23
    assert len(df) == EXPECTED["filas_salida"], (
        f"Filas de salida: {len(df):,} != {EXPECTED['filas_salida']:,}"
    )
    assert int(df["resume_id"].nunique()) == EXPECTED["personas_salida"]

    # 1. Sin fechas vacias ni futuras ni invertidas
    assert int(df["start_date"].isna().sum()) == 0
    assert int(df["end_date"].isna().sum()) == 0
    anio_ini, ord_ini = _extraer_anio_trimestre(df["start_date"])
    anio_fin, ord_fin = _extraer_anio_trimestre(df["end_date"])
    assert int(anio_ini.isna().sum()) == 0, "Formato invalido en start_date"
    assert int((df["end_date"].ne("Present") & anio_fin.isna()).sum()) == 0, "Formato invalido en end_date"
    assert int(((anio_ini > ANIO_CORTE) | (anio_fin > ANIO_CORTE)).sum()) == 0
    assert int((ord_fin.notna() & (ord_fin < ord_ini)).sum()) == 0

    # 2. Cero duplicados exactos y cero variantes por (resume_id, start_date, matched_code)
    assert int(df.duplicated(subset=CLAVE_CRUDA).sum()) == 0
    assert int(df.duplicated(subset=CLAVE_VARIANTE).sum()) == 0

    # 3. Categorias limpias
    assert int(df["university_level"].isna().sum()) == 0
    assert int(df["university_level"].eq("None").sum()) == 0
    assert set(df["university_level"].unique()) == {
        "Secondary school",
        "Bachelor",
        "Master",
        "PhD",
        "No reportado",
    }
    assert set(df["emparejado"].unique()) == {"ok", "rescatado", "unknown"}

    # 4. Reconciliacion de banderas y competencias
    assert (df["es_vigente"] == df["end_date"].eq("Present")).all()
    assert int(df["es_vigente"].sum()) > 0

    sin_codigo = df["occupation_code"].isna()
    assert (sin_codigo == (df["es_unknown_ocupacion"] | df["es_rescatado"])).all()

    ok = df["saber_skills"].eq(SABER_OK)
    assert (ok == ~sin_codigo).all()
    assert int(ok.sum()) + int(df["es_unknown_ocupacion"].sum()) + int(df["es_rescatado"].sum()) == len(df)
    print(
        f"Distribucion final: ok={int(ok.sum()):,} ({100 * ok.mean():.2f}%) | "
        f"unknown={int(df['es_unknown_ocupacion'].sum()):,} | "
        f"rescatado={int(df['es_rescatado'].sum()):,} | "
        f"vigentes={int(df['es_vigente'].sum()):,}"
    )

    assert df.loc[ok, CONTADORES + ["veces_ese_oficio"]].notna().all().all()
    suma = (
        df.loc[ok, "n_skills_competence"]
        + df.loc[ok, "n_skills_knowledge"]
        + df.loc[ok, "n_skills_sin_tipo"]
    )
    assert (suma == df.loc[ok, "n_skills_essential"]).all()

    for lista, contador in zip(LISTAS, CONTADORES[1:]):
        largo = df.loc[ok, lista].str.split(SEPARADOR, regex=False).str.len().fillna(0)
        assert (largo == df.loc[ok, contador]).all(), f"Desajuste entre {lista} y {contador}"

    assert df.loc[~ok, CONTADORES + LISTAS + ["veces_ese_oficio"]].isna().all().all()

    # 5. Cuadre contable de la bitacora
    eliminadas_bitacora = sum(item["filas_eliminadas"] for item in bitacora)
    assert EXPECTED["filas_entrada"] - eliminadas_bitacora == len(df)
    print("Validacion Data Hygiene: OK (todos los asserts superados)")


def guardar_salidas(df: pd.DataFrame, bitacora: list[dict], t0: float) -> None:
    """Escribe el CSV limpio y la bitacora de auditoria."""
    SALIDA_DIR.mkdir(parents=True, exist_ok=True)

    with BITACORA.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(bitacora[0].keys()))
        writer.writeheader()
        writer.writerows(bitacora)

    print(f"\nEscribiendo {SALIDA} ...")
    df.to_csv(SALIDA, index=False, encoding="utf-8")
    mb = SALIDA.stat().st_size / 1e6
    print(
        f"Escrito: {SALIDA} ({mb:,.1f} MB) | "
        f"{df.shape[0]:,} filas x {df.shape[1]} columnas | "
        f"{df['resume_id'].nunique():,} personas | {time.time() - t0:.0f} s"
    )
    print(f"Bitacora: {BITACORA}")


def main() -> None:
    t0 = time.time()
    df, bitacora = ejecutar_limpieza()
    validar_data_hygiene(df, bitacora)
    guardar_salidas(df, bitacora, t0)


if __name__ == "__main__":
    main()

