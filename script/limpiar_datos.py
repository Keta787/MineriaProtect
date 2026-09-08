"""
limpiar_datos.py
================
Inspeccion y limpieza de los datasets del proyecto de Mineria de Datos
(JobHop + taxonomia ESCO).

Flujo:
    DATOS ORIGINALES (data/original/)
        -> INSPECCION (filas, columnas, tipos, nulos, duplicados, muestras TOP/BOTTOM)
        -> LIMPIEZA (reglas especificas por archivo, documentadas)
        -> VALIDACION (resumen antes/despues)
        -> DATOS LIMPIOS (data/limpio/)

Reglas generales:
    - NUNCA se modifican los archivos originales: solo se leen.
    - Los archivos limpios llevan sufijo "_limpio" y conservan el nombre base.
    - Las llaves / codigos se leen como TEXTO para no perder ceros a la izquierda
      (p. ej. el codigo ISCO '0110' no debe colisionar con '110').
    - Las tablas de relaciones 1:N (ocupacion <-> habilidad) conservan todas sus
      filas: NO se eliminan filas solo porque un codigo se repita muchas veces.

Como ejecutar:
    python script/limpiar_datos.py

Requisitos:
    pandas, pyarrow
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

# Consola: forzar UTF-8 para poder imprimir caracteres especiales de los datos
# (En Windows la consola usa cp1252 y falla con caracteres como el U+200B).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

# Renderizado de tablas: en Jupyter muestra tablas HTML; en consola imprime texto.
try:
    from IPython.display import display as _display
except Exception:  # consola sin IPython instalado
    def _display(obj, *args, **kwargs):
        print(obj.to_string() if hasattr(obj, "to_string") else obj)

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
ORIGEN = RAIZ / "data" / "original"
DESTINO = RAIZ / "dataset"

# Extensiones que se procesan automaticamente
EXT_CSV = ".csv"
EXT_PARQUET = ".parquet"

# Archivos que NO se vuelven a limpiar (ya tienen su version limpia en dataset/).
# JobHop_v2_train.parquet ya genero dataset/JobHop_v2_train_limpio.parquet.
ARCHIVOS_EXCLUIDOS = {"JobHop_v2_train.parquet"}


# ---------------------------------------------------------------------------
# Diccionario de columnas (observado / documentado por ESCO dictionary_en.csv)
# ---------------------------------------------------------------------------
# Nota: las descripciones provienen de los propios datos y del archivo
# oficial ESCO `dictionary_en.csv` que acompania al dataset. Si una columna
# no puede determinarse se marca explicitamente.
SIGNIFICADO_COLUMNA = {
    # --- JobHop ---
    "resume_id": "ID de la persona/curriculum. Se repite en cada empleo de la misma persona (llave de persona).",
    "matched_code": "Codigo de ocupacion (taxonomia ESCO). 'unknown' = empleo no clasificable.",
    "start_date": "Trimestre de inicio del empleo (formato 'Qn AAAA').",
    "end_date": "Trimestre de fin del empleo, o 'Present' si sigue vigente.",
    "university_level": "Nivel educativo de la persona (Secondary school, Bachelor, Master, PhD, None).",
    # --- ESCO comun ---
    "conceptType": "Tipo de concepto ESCO (Occupation, KnowledgeSkillCompetence, ISCOGroup, etc.).",
    "conceptUri": "URI unica del concepto en ESCO (identificador estable).",
    "preferredLabel": "Etiqueta oficial / nombre preferido del concepto.",
    "altLabels": "Nombres alternativos (sinonimos) separados por ' | '.",
    "hiddenLabels": "Etiquetas de busqueda ocultas (solo texto, no se muestran en visuales).",
    "status": "Estado ISO del concepto (p. ej. 'released').",
    "modifiedDate": "Fecha de ultima modificacion del registro.",
    "scopeNote": "Nota de alcance / aclaracion de uso del concepto.",
    "definition": "Definicion formal del significado del concepto.",
    "inScheme": "Esquema(s) de concepto al que pertenece (URIs separadas por coma).",
    "description": "Descripcion general del concepto.",
    "code": "Codigo/notacion del concepto en su esquema (p. ej. codigo de ocupacion ESCO).",
    # --- occupations_en.csv ---
    "iscoGroup": "Codigo ISCO-08 a 4 digitos del grupo al que pertenece la ocupacion.",
    "naceCode": "URIs NACE (sector economico) asociadas a la ocupacion; puede haber varias separadas por ',\n'.",
    "regulatedProfessionNote": "Nota sobre si la ocupacion es una profesion regulada.",
    # --- ISCOGroups_en.csv ---
    "ISCO code": "Codigo ISCO-08 (se lee como texto para conservar ceros a la izquierda).",
    # --- relaciones broader ---
    "conceptLabel": "Etiqueta del concepto hijo (nivel inferior).",
    "broaderType": "Tipo del concepto padre (ISCOGroup u Occupation).",
    "broaderUri": "URI del concepto padre.",
    "broaderLabel": "Etiqueta del concepto padre.",
    # --- occupationSkillRelations_en.csv ---
    "occupationUri": "URI de la ocupacion (enlaza con occupations.conceptUri).",
    "occupationLabel": "Etiqueta de la ocupacion.",
    "relationType": "Tipo de relacion: 'essential' (esencial) u 'optional' (opcional).",
    "skillType": "Tipo de habilidad: 'skill/competence' o 'knowledge'.",
    "skillUri": "URI de la habilidad (enlaza con skills.conceptUri).",
    "skillLabel": "Etiqueta de la habilidad.",
    # --- skillSkillRelations_en.csv ---
    "originalSkillUri": "URI de la habilidad origen de la relacion.",
    "originalSkillType": "Tipo de la habilidad origen.",
    "relatedSkillType": "Tipo de la habilidad relacionada.",
    "relatedSkillUri": "URI de la habilidad relacionada.",
    # --- skills_en.csv ---
    "reuseLevel": "Nivel de reutilizacion de la habilidad (transversal, cross-sector, sector-specific, occupation-specific).",
    # --- skillsHierarchy_en.csv ---
    "Level 0 URI": "URI del nivel 0 de la jerarquia de habilidades.",
    "Level 0 preferred term": "Etiqueta del nivel 0 de la jerarquia.",
    "Level 0 code": "Codigo del nivel 0 de la jerarquia.",
    "Level 1 URI": "URI del nivel 1 de la jerarquia.",
    "Level 1 preferred term": "Etiqueta del nivel 1.",
    "Level 1 code": "Codigo del nivel 1.",
    "Level 2 URI": "URI del nivel 2 de la jerarquia.",
    "Level 2 preferred term": "Etiqueta del nivel 2.",
    "Level 2 code": "Codigo del nivel 2.",
    "Level 3 URI": "URI del nivel 3 de la jerarquia.",
    "Level 3 preferred term": "Etiqueta del nivel 3.",
    "Level 3 code": "Codigo del nivel 3.",
    "Scope note": "Nota de alcance de la habilidad.",
    # --- colecciones (skills/occupations) ---
    "broaderConceptUri": "URI del concepto padre/agrupador en la coleccion.",
    "broaderConceptPT": "Etiqueta (preferred term) del concepto padre/agrupador en la coleccion.",
    # --- greenShareOcc_en.csv ---
    "greenShare": "Proporcion (0-1) de tareas 'verdes' asociadas al concepto (ocupacion o grupo ISCO).",
    # --- conceptSchemes_en.csv ---
    "conceptSchemeUri": "URI del esquema de conceptos.",
    "title": "Titulo del esquema de conceptos.",
    "hasTopConcept": "Concepto(s) tope del esquema (URI).",
    # --- dictionary_en.csv ---
    "filename": "Nombre del archivo de datos ESCO al que pertenece la fila.",
    "data header": "Nombre de la columna documentada.",
    "property": "Propiedad del modelo ESCO (URI de vocabulario SKOS/DCMI, etc.).",
    "title (dictionary)": "Titulo del esquema (contexto).",
}


def significado(columna: str) -> str:
    """Devuelve el significado documentado de una columna."""
    return SIGNIFICADO_COLUMNA.get(
        columna, "Significado no determinado; requiere revision."
    )


# ---------------------------------------------------------------------------
# Guia de limpieza por archivo (columnas criticas para el cruce futuro)
# ---------------------------------------------------------------------------
CRITICAS = {
    # nombre base -> columnas que no deberian quedar nulas para poder cruzar
    "JobHop_v2_train": ["resume_id", "matched_code", "start_date"],
    "occupations_en": ["code"],
    "ISCOGroups_en": ["code"],
    "occupationSkillRelations_en": ["occupationUri", "skillUri", "relationType"],
    "skillSkillRelations_en": ["originalSkillUri", "relatedSkillUri", "relationType"],
    "broaderRelationsOccPillar_en": ["conceptUri", "broaderUri"],
    "broaderRelationsSkillPillar_en": ["conceptUri", "broaderUri"],
    "skills_en": ["conceptUri"],
    "skillGroups_en": ["conceptUri", "code"],
    "greenShareOcc_en": ["code", "greenShare"],
    "conceptSchemes_en": ["conceptSchemeUri"],
}


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def carga_archivo(ruta: Path) -> pd.DataFrame:
    """Carga un archivo CSV (como texto) o Parquet segun su extension."""
    if ruta.suffix.lower() == EXT_CSV:
        # dtype=str: evita que los codigos pierdan ceros a la izquierda
        # encoding utf-8-sig: tolera BOM si existiera
        return pd.read_csv(ruta, encoding="utf-8-sig", dtype=str)
    return pd.read_parquet(ruta)


def clave_trimestre(valor) -> tuple:
    """Convierte 'Q1 2000' -> (2000, 1). 'Present' se envia al final."""
    if pd.isna(valor) or str(valor).lower() == "present":
        return (9999, 4)
    m = re.match(r"Q([1-4])\s+(\d{4})", str(valor).strip())
    if not m:
        return (0, 0)
    return (int(m.group(2)), int(m.group(1)))


# ---------------------------------------------------------------------------
# INSPECCION
# ---------------------------------------------------------------------------
def inspeccionar(df: pd.DataFrame, etiqueta: str, tipo: str) -> None:
    """Muestra la estructura del archivo: filas, columnas, tipos, nulos,
    duplicados y muestras TOP3 / BOTTOM3."""
    print("=" * 78)
    print(f"ARCHIVO: {etiqueta}")
    print(f"Filas: {len(df)} | Columnas: {df.shape[1]} | Tipo: {tipo}")
    print("-" * 78)

    print("Columnas y significado:")
    for i, col in enumerate(df.columns, start=1):
        print(f"  {i:>2}. {col:<32} {str(df.dtypes[col]):<10} {significado(col)}")

    nulos = df.isna().sum()
    nulos = nulos[nulos > 0]
    if len(nulos) > 0:
        print("\nColumnas con valores nulos:")
        print(nulos.to_string())
    else:
        print("\nColumnas con valores nulos: ninguna")

    print(f"\nFilas duplicadas (exactas): {int(df.duplicated().sum())}")

    print("\nTOP 3 filas (muestra):")
    _display(df.head(3))
    print("BOTTOM 3 filas (muestra):")
    _display(df.tail(3))
    print()
    return df


def nulos_criticos(df: pd.DataFrame, stem: str) -> int:
    """Cuenta nulos en las columnas criticas del archivo (si estan definidas)."""
    criticas = CRITICAS.get(stem, [])
    cols = [c for c in criticas if c in df.columns]
    return int(df[cols].isna().sum().sum()) if cols else 0


# ---------------------------------------------------------------------------
# LIMPIEZA
# ---------------------------------------------------------------------------
def limpiar_jobhop(df: pd.DataFrame, cambios: list, stats: dict) -> pd.DataFrame:
    """Limpieza especifica de JobHop_v2_train.parquet."""
    stats["cambio_tipos"] = ""
    stats["texto_normalizado"] = False

    # 1. end_date nulo -> 'Present'
    #    PROBLEMA: 136.497 registros no tienen fecha de fin y 'end_date' queda
    #    con NaN. Sin una decidida, esos empleos no pueden ubicarse en la
    #    trayectoria. TRANSFORMACION: representar "sin fecha de fin" como
    #    'Present' (empleo vigente), segun la practica ya documentada en el
    #    notebook Lectura.ipynb. IMPACTO: valores rellenados, 0 filas perdidas.
    n_end_null = int(df["end_date"].isna().sum())
    if n_end_null > 0:
        df["end_date"] = df["end_date"].fillna("Present")
        cambios.append(
            f"end_date: {n_end_null} nulos -> 'Present' (se interpreta como empleo vigente)."
        )
        stats["valores_modificados"] = True

    # 2. start_date nulo -> filas eliminadas
    #    PROBLEMA: 58.312 filas sin fecha de inicio no pueden ordenarse en la
    #    trayectoria (no se sabe cuando comenzaron). TRANSFORMACION: eliminarlas.
    #    IMPACTO: -58.312 filas.
    n_start_null = int(df["start_date"].isna().sum())
    if n_start_null > 0:
        df = df.dropna(subset=["start_date"])
        cambios.append(
            f"start_date: {n_start_null} filas eliminadas (sin fecha de inicio, no ubicable en la trayectoria)."
        )
        stats["filas_eliminadas"] = True

    # 3. Duplicados exactos de fila completa
    #    PROBLEMA: registros identicos repiten la misma experiencia.
    #    TRANSFORMACION: drop_duplicates() (sin subset: fila completa).
    #    IMPACTO: se eliminan solo las filas exactamente iguales.
    n_dup = int(df.duplicated().sum())
    if n_dup > 0:
        df = df.drop_duplicates().reset_index(drop=True)
        cambios.append(f"Duplicados exactos: {n_dup} filas eliminadas.")
        stats["duplicados_eliminados"] = True

    # 4. Orden por persona y por fecha real (trimestre)
    #    PROBLEMA: ordenar por el string 'start_date' mezclaria 'Q4 1999'
    #    con 'Q1 2000'. TRANSFORMACION: clave numerica (anio, trimestre).
    #    IMPACTO: el orden cronologico interno de cada trayectoria es correcto.
    df["_clave_ini"] = df["start_date"].apply(clave_trimestre)
    df["_clave_fin"] = df["end_date"].apply(clave_trimestre)
    df = df.sort_values(["resume_id", "_clave_ini", "_clave_fin"]).drop(
        columns=["_clave_ini", "_clave_fin"]
    )
    df = df.reset_index(drop=True)
    cambios.append(
        "Ordenadas las filas por resume_id y fecha de inicio (por trimestre real)."
    )
    return df


def limpiar_csv(df: pd.DataFrame, stem: str, cambios: list, stats: dict) -> pd.DataFrame:
    """Limpieza generica + reglas especificas para los CSV de ESCO."""
    df = df.copy()

    # 0. Columnas 100% nulas -> eliminar
    #    PROBLEMA: una columna sin ningun valor no aporta informacion ni puede
    #    usarse para cruzar. TRANSFORMACION: eliminar.
    #    IMPACTO: solo se eliminan columnas vacias (p. ej. ISCOGroups.altLabels).
    completas = [c for c in df.columns if df[c].isna().all()]
    if completas:
        cambios.append(
            f"Columnas 100% nulas eliminadas: {completas} (sin informacion)."
        )
    df = df.drop(columns=completas)
    stats["columnas_eliminadas"] = bool(completas)

    # 1. Normalizacion de texto (espacios al inicio/fin)
    #    PROBLEMA: espacios residuales rompen comparaciones de igualdad en cruces
    #    ('code ' != 'code'). TRANSFORMACION: strip() en columnas de texto.
    #    IMPACTO: valores normalizados, 0 filas perdidas.
    n_texto = 0
    for col in df.select_dtypes(include=["object", "string"]).columns:
        s = df[col]
        s2 = s.str.strip()
        n_texto += int((s.notna() & (s != s2)).sum())
        df[col] = s2
    if n_texto > 0:
        cambios.append(f"Textos normalizados (strip): {n_texto} valores ajustados.")
        stats["texto_normalizado"] = True

    # 2. Reglas especificas por archivo (justificadas abajo)
    if stem == "occupations_en":
        # Duplicados por 'code':
        # PROBLEMA: 4 codigos aparecen 2 veces; las filas son identicas salvo
        # 'modifiedDate' (artefacto de dos fechas de publicacion de ESCO).
        # TRANSFORMACION: conservar la primera fila por 'code'.
        # IMPACTO: -4 filas; no se pierde informacion salvo la fecha duplicada.
        n_code = int(df["code"].duplicated().sum())
        if n_code > 0:
            df = df.drop_duplicates(subset="code", keep="first")
            cambios.append(
                f"occupations: {n_code} filas duplicadas por 'code' eliminadas "
                "(identicas salvo modifiedDate; se conserva la primera)."
            )
            stats["duplicados_eliminados"] = True

    elif stem in ("skills_en", "skillGroups_en"):
        # Duplicados por 'conceptUri':
        # PROBLEMA: skills tiene 21 conceptUri duplicados; en cada par las filas
        # son identicas salvo 'modifiedDate' (dos publicaciones de ESCO).
        # TRANSFORMACION: conservar la primera fila por 'conceptUri'.
        # IMPACTO: -21 filas en skills; en skillGroups no hay duplicados (0).
        n_uri = int(df["conceptUri"].duplicated().sum())
        if n_uri > 0:
            df = df.drop_duplicates(subset="conceptUri", keep="first")
            cambios.append(
                f"{stem}: {n_uri} filas duplicadas por 'conceptUri' eliminadas "
                "(identicas salvo modifiedDate; se conserva la primera)."
            )
            stats["duplicados_eliminados"] = True

    elif stem == "greenShareOcc_en":
        # 'greenShare' es una proporcion numerica.
        # PROBLEMA: al leer como texto quedo como string.
        # TRANSFORMACION: convertir a float; si algo no es numerico -> NaN.
        # IMPACTO: tipo corregido; se reporta cuantos valores no convertibles.
        antes_null = int(df["greenShare"].isna().sum())
        df["greenShare"] = pd.to_numeric(df["greenShare"], errors="coerce")
        nuevos_null = int(df["greenShare"].isna().sum()) - antes_null
        if nuevos_null:
            cambios.append(
                f"greenShare: {nuevos_null} valores no numericos quedaron como NaN (revisar)."
            )
        else:
            cambios.append("greenShare: convertido a numero (float).")
        stats["cambio_tipos"] = True

    elif stem == "occupationSkillRelations_en":
        # 'skillType' tiene 59 nulos.
        # PROBLEMA: no se sabe si la habilidad es competencia o conocimiento.
        # TRANSFORMACION: NO se eliminan filas: la relacion ocupacion-habilidad
        # sigue siendo valida (occupationUri, skillUri y relationType estan).
        # IMPACTO: se conservan las 59 filas; el nulo se mantiene y se reporta.
        if "skillType" in df.columns:
            n_st = int(df["skillType"].isna().sum())
            cambios.append(
                f"occupationSkillRelations: {n_st} filas con 'skillType' nulo "
                "conservadas (la relacion 1:N no depende de ese campo)."
            )

    elif stem in (
        "broaderRelationsOccPillar_en",
        "broaderRelationsSkillPillar_en",
        "skillSkillRelations_en",
    ):
        # Tablas de relaciones 1:N: NO se deduplica por clave.
        # PROBLEMA potencial: eliminar filas 'porque un codigo se repite'
        # romperia relaciones legitimas (una ocupacion tiene muchas habilidades).
        # TRANSFORMACION: ninguna deduplicacion por clave.
        # IMPACTO: se mantiene la cardinalidad 1:N.
        cambios.append(
            f"{stem}: tabla de relaciones 1:N conservada (sin deduplicacion por clave)."
        )

    # 3. Duplicados exactos de fila completa (final)
    #    PROBLEMA: filas totalmente identicas (todas las columnas) son
    #    redundantes en cualquier tabla. TRANSFORMACION: eliminar las exactas.
    #    IMPACTO: en la practica 0 (verificado); regla defensiva.
    n_dup = int(df.duplicated().sum())
    if n_dup > 0:
        df = df.drop_duplicates().reset_index(drop=True)
        cambios.append(f"Duplicados exactos (fila completa): {n_dup} eliminados.")
        stats["duplicados_eliminados"] = True

    return df


def destino_para(ruta_rel: Path) -> Path:
    """Ruta del archivo limpio: mismo subarbol con sufijo '_limpio'."""
    nombre = f"{ruta_rel.stem}_limpio{ruta_rel.suffix}"
    return DESTINO / ruta_rel.parent / nombre


# ---------------------------------------------------------------------------
# REPORTE DE VALIDACION
# ---------------------------------------------------------------------------
def validar(
    etiqueta: str,
    df_antes: dict,
    df_despues: pd.DataFrame,
    cambios: list,
) -> None:
    print("=" * 78)
    print(f"VALIDACION: {etiqueta}")
    filas_antes = df_antes["filas"]
    cols_antes = df_antes["columnas"]
    dups_antes = df_antes["dups_fila"]
    nulos_antes = df_antes["nulos_criticos"]

    filas_despues = len(df_despues)
    cols_despues = df_despues.shape[1]
    dups_despues = int(df_despues.duplicated().sum())

    stem = Path(etiqueta).name
    nulos_despues = nulos_criticos(df_despues, Path(stem).stem)

    print(f"  Filas originales:            {filas_antes}")
    print(f"  Filas despues de limpiar:    {filas_despues}")
    print(f"  Filas eliminadas:            {filas_antes - filas_despues} "
          f"({100 * (filas_antes - filas_despues) / filas_antes:.2f}%)")
    print(f"  Columnas originales:         {cols_antes}")
    print(f"  Columnas finales:            {cols_despues}")
    print(f"  Nulos criticos antes:        {nulos_antes}")
    print(f"  Nulos criticos despues:      {nulos_despues}")
    print(f"  Duplicados antes (exactos):  {dups_antes}")
    print(f"  Duplicados despues (exactos):{dups_despues}")
    print()
    print("  Transformaciones aplicadas:")
    for c in cambios:
        print(f"    - {c}")
    print()


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main() -> None:
    if not ORIGEN.exists():
        print(f"ERROR: no existe la carpeta de datos originales: {ORIGEN}")
        print("Crea la estructura data/original/ y coloca ahi los archivos.")
        return

    DESTINO.mkdir(parents=True, exist_ok=True)

    # Deteccion automatica de archivos (recorre subcarpetas de original/)
    archivos = sorted(ORIGEN.rglob("*"))
    archivos = [
        p
        for p in archivos
        if p.is_file()
        and p.suffix.lower() in (EXT_CSV, EXT_PARQUET)
        and p.name not in ARCHIVOS_EXCLUIDOS
    ]

    if not archivos:
        print(f"No se encontraron archivos {EXT_CSV}/{EXT_PARQUET} en {ORIGEN}.")
        return

    print(f"Se procesaran {len(archivos)} archivos de {ORIGEN}\n")

    resumen = []

    for ruta in archivos:
        ruta_rel = ruta.relative_to(ORIGEN)
        etiqueta = str(ruta_rel).replace("\\", "/")
        stem = ruta.stem
        tipo = "Parquet" if ruta.suffix.lower() == EXT_PARQUET else "CSV"

        # 1. Carga
        df = carga_archivo(ruta)

        # 2. Inspeccion
        inspeccionar(df, etiqueta, tipo)

        # 3. Limpieza
        cambios: list = []
        stats = {
            "filas_eliminadas": False,
            "columnas_eliminadas": False,
            "valores_modificados": False,
            "cambio_tipos": False,
            "texto_normalizado": False,
            "duplicados_eliminados": False,
        }
        if ruta.suffix.lower() == EXT_PARQUET:
            df_limpio = limpiar_jobhop(df, cambios, stats)
        else:
            df_limpio = limpiar_csv(df, stem, cambios, stats)

        # 4. Guardar (nunca toca original/)
        destino = destino_para(ruta_rel)
        stats["destino"] = destino
        destino.parent.mkdir(parents=True, exist_ok=True)
        if destino.suffix.lower() == EXT_PARQUET:
            df_limpio.to_parquet(destino, index=False)
        else:
            df_limpio.to_csv(destino, index=False, encoding="utf-8")

        # 5. Validacion
        validacion = {
            "filas": len(df),
            "columnas": df.shape[1],
            "dups_fila": int(df.duplicated().sum()),
            "nulos_criticos": nulos_criticos(df, stem),
        }
        validar(etiqueta, validacion, df_limpio, cambios)

        # 6. Muestra del resultado limpio (TOP 3 como tabla)
        print(f"Muestra del resultado limpio ({etiqueta}) - TOP 3 filas:")
        _display(df_limpio.head(3))
        print()

        resumen.append(
            {
                "archivo": etiqueta,
                "filas_antes": len(df),
                "filas_despues": len(df_limpio),
                "columnas": df.shape[1],
                "columnas_finales": df_limpio.shape[1],
                "cambios": stats,
            }
        )

    # Resumen global
    print("#" * 78)
    print("RESUMEN GLOBAL")
    print("#" * 78)
    df_resumen = pd.DataFrame(resumen)
    df_resumen["filas_eliminadas"] = (
        df_resumen["filas_antes"] - df_resumen["filas_despues"]
    )
    df_resumen = df_resumen[
        [
            "archivo",
            "filas_antes",
            "filas_despues",
            "filas_eliminadas",
            "columnas",
            "columnas_finales",
        ]
    ]
    _display(df_resumen.sort_values("archivo"))

    print()
    print("Los archivos limpios quedaron en:", DESTINO)
    print("Los archivos originales NO fueron modificados.")


if __name__ == "__main__":
    main()