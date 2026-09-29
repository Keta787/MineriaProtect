"""
generar_competencias.py
=======================
Construye `data/03_processed/competencias_por_oficio.csv`: la tabla
normalizada de competencias ESCO, con UNA FILA POR (OFICIO, COMPETENCIA).

Por que una tabla aparte y no una columna dentro de `empleos_limpio.csv`
-----------------------------------------------------------------------
Las competencias de ESCO son atributos de un CARGO, no de una persona. Hay
2.855 oficios distintos para 71.061 personas y 376.567 experiencias, asi que
escribir los nombres dentro de `empleos_limpio.csv` repetiria el mismo texto
~376.000 veces (+230 MB) y destruiria el grano del dataset, que debe seguir
siendo 1 fila = 1 experiencia.

La tabla aparte se une despues con un cruce N:1 por `occupation_code`, que YA
existe en los tres CSV del pipeline (`empleos.csv`, `empleos_limpio.csv`,
`empleos_limpio_sin_outliers.csv`). No hay que modificar ni un byte de ellos.

"1 fila = 1 competencia de 1 oficio" es la regla de GUARDADO, no la de LECTURA.
Para mostrar el perfil de un cargo se agrupa por `occupation_code` y sale una
linea con todas sus competencias: ver `src/filtro/indicadores.py`
(`perfil_persona`, `cargar_competencias`).

Que significa "competencia de una persona" (leer antes de usar)
---------------------------------------------------------------
Misma regla que en `integrar_empleos.py`: ESCO describe lo que un CARGO exige,
no lo que un INDIVIDUO sabe. Si alguien ocupo el cargo, su contrato obligaba a
esas competencias (atribucion por contrato). La lectura correcta es "este cargo
exige N competencias", nunca "esta persona sabe N cosas". Cuando no hay oficio
clasificado no hay contrato que leer y las competencias se declaran
desconocidas, nunca en 0.

Que NO se incluye
-----------------
    - Relaciones 'optional': son telemetria de jerarquia y el pipeline entero
      las descarta (misma decision documentada en `integrar_empleos.py`).
    - Filtrado por los oficios que JobHop usa: la tabla describe a ESCO
      (3.039 oficios), no a JobHop (2.855). Es un superconjunto a proposito,
      para poder ampliar sin volver a la fuente.

Relacion con `n_skills_essential`
---------------------------------
Esa columna NO se elimina (esta dentro de la X de los cuadernos 4.0 y 4.1 y no
cuesta nada), pero deja de ser un dato independiente: pasa a ser una cache
desnormalizada de esta tabla, verificada en cada corrida. Este script es la red
de seguridad: si el puente ESCO se rompe, el bloque de validacion corta la
ejecucion con diagnostico en vez de dejar dos numeros distintos circulando por
el proyecto.

Salida (unica): `data/03_processed/competencias_por_oficio.csv` (4 columnas)

Como ejecutar:
    python src/limpieza/generar_competencias.py

Debe correr DESPUES de `integrar_empleos.py`, porque el bloque de validacion
contrasta esta tabla contra los contadores de `data/03_processed/empleos.csv`.
Si ese archivo no esta, la tabla se genera igual pero el contraste se omite y
el script lo avisa en pantalla (no lo omite en silencio).

Requisitos:
    pandas (los CSV de entrada se leen como texto: dtype=str +
    keep_default_na=False + na_values=[''], para no perder ceros a la izquierda
    en los codigos ESCO/ISCO ni convertir el literal 'None' a NaN).
"""

from __future__ import annotations

import csv
import hashlib
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
    while (p / "data").exists() is False and p != p.parent:
        p = p.parent
    return p


RAIZ = _raiz_proyecto()
INTERIM = RAIZ / "data" / "02_interim"
OCCUPATIONS = INTERIM / "ESCO" / "occupations_en_limpio.csv"
SKILL_RELATIONS = INTERIM / "SKILLS" / "occupationSkillRelations_en_limpio.csv"
PROC = RAIZ / "data" / "03_processed"
# `empleos.csv` no es un insumo: se lee solo para CONTRASTAR la tabla contra los
# contadores que el pipeline ya calculo. Si no esta, se genera igual y se avisa.
EMPLEOS = PROC / "empleos.csv"
SALIDA = PROC / "competencias_por_oficio.csv"
LOGS_DIR = RAIZ / "logs"
BITACORA = LOGS_DIR / "bitacora_generar_competencias.csv"

# Solo 'essential' (el piso minimo que el cargo exige). Las 'optional' son
# telemetria de jerarquia: la misma decision y el mismo motivo que en
# `integrar_empleos.py`.
RELACION_KEPT = "essential"

# Orden de columnas de la salida. La clave del par es
# (`occupation_code`, `habilidad_nombre`); `occupation_label` va en medio porque es
# lo que se lee al inspeccionar el archivo a ojo, y `habilidad_tipo` al final
# porque es lo unico que se puede filtrar.
COLUMNAS = [
    "occupation_code",
    "occupation_label",
    "habilidad_nombre",
    "habilidad_tipo",
]

# 39 de las 67.600 relaciones 'essential' llegan sin `skillType` (defecto
# conocido de la fuente, documentado en el README). No se dejan vacias: se
# etiquetan 'sin_tipo', el mismo nombre del bucket `n_skills_sin_tipo` del
# pipeline, para que agrupar por esta columna reproduzca los tres contadores.
TIPOS_ESCO = ("skill/competence", "knowledge")
TIPO_SIN_DEFINIR = "sin_tipo"

# Contadores con los que esta tabla debe reconciliar contra `empleos.csv`. Se
# nombran igual que alli porque `conteo` (la tabla de 4 columnas que se arma
# desde la salida) ya se renombro para que el contraste sea un `==` y no un
# translate de nombres.
CONTADORES = (
    "n_skills_essential",
    "n_skills_competence",
    "n_skills_knowledge",
    "n_skills_sin_tipo",
)

# Que tipo ESCO debe reproducir cada contador, para el mensaje de la validacion.
TIPO_QUE_REPRODUCE = {
    "n_skills_essential": "todos los tipos",
    "n_skills_competence": "skill/competence",
    "n_skills_knowledge": "knowledge",
    "n_skills_sin_tipo": TIPO_SIN_DEFINIR,
}

# Canon verificado sobre las fuentes limpias actuales. Si la fuente ESCO cambia,
# la falla es aqui y no mas tarde en un cuaderno.
ESPERADO = {
    "pares_essential": 67_600,
    "oficios_esco": 3_039,
    "competencias": 51_155,
    "conocimiento": 16_406,
    "sin_tipo": 39,
    # Oficios que JobHop no usa: la tabla es un superconjunto a proposito.
    "oficios_en_empleos": 2_855,
}


def _cargar(ruta: Path, **kw) -> pd.DataFrame:
    """Lee un CSV de texto: solo la celda vacia es NaN."""
    return pd.read_csv(ruta, dtype=str, encoding="utf-8", keep_default_na=False,
                       na_values=[""], **kw)


def _sha256(ruta: Path) -> str:
    """SHA-256 del archivo de entrada (huella para reproducir la corrida)."""
    h = hashlib.sha256()
    with ruta.open("rb") as fh:
        for bloque in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def _validar_contra_empleos(conteo: pd.DataFrame) -> bool:
    """Contrasta la tabla contra los contadores ya calculados por el pipeline.

    Devuelve False si `empleos.csv` no esta todavia (se omite el contraste y se
    avisa; nunca se omite en silencio). Con el archivo presente, exige que los
    cuatro contadores reproduzcan exactamente los de la tabla, oficio por
    oficio. La comparacion se restringe a los codigos que USAN los datos: los
    184 oficios que ESCO publica y JobHop no usa no tienen contraparte, y
    compararlos daria NaN != NaN (falso positivo, ver `docs/SKILLS.md`).
    """
    if not EMPLEOS.exists():
        print("=" * 78)
        print("AVISO: contraste de consistencia OMITIDO")
        print("=" * 78)
        print(f"No existe {EMPLEOS}, asi que no se puede contrastar la tabla")
        print("contra `n_skills_essential`. La tabla se genero, pero su consistencia")
        print("con el pipeline NO quedo verificada en esta corrida.")
        print("Ejecuta antes: python src/limpieza/integrar_empleos.py")
        return False

    # Solo las columnas de los contadores: leer 376.567 x 17 para usar cuatro
    # columnas seria gastar memoria a cambio de nada.
    emp = _cargar(EMPLEOS, usecols=list(CONTADORES) + ["occupation_code"])
    emp = emp.loc[emp["occupation_code"].notna()]
    emp = emp.drop_duplicates(subset="occupation_code").set_index("occupation_code")

    comunes = emp.index
    print("=" * 78)
    print("VALIDACION: la tabla contra los contadores de empleos.csv")
    print("=" * 78)
    print(f"Oficios en la tabla de ESCO      : {len(conteo):,}")
    print(f"Oficios usados por JobHop        : {len(emp):,}")
    print(f"Oficios de ESCO ausentes del dato: "
          f"{len(conteo.index.difference(emp.index)):,}  (superconjunto, no es error)")
    # El dataset no cambio desde que se fijo el canon. Si se ampliara, la falla
    # tiene que saltar aqui y no terminar partida en dos fuentes de verdad.
    assert len(emp) == ESPERADO["oficios_en_empleos"], (
        f"Oficios usados por JobHop: {len(emp):,} != {ESPERADO['oficios_en_empleos']:,}"
    )

    for columna in CONTADORES:
        esperado = pd.to_numeric(emp.loc[comunes, columna], errors="coerce")
        obtenido = conteo.loc[comunes, columna]
        # Ningun lado debe traer NaN: si lo trajera, la comparacion seria
        # NaN != NaN y contaria como falla sin que haya falla.
        assert esperado.notna().all(), f"{columna} trae NaN en {int(esperado.isna().sum())} oficios"
        assert obtenido.notna().all(), (
            f"La tabla no tiene {columna} para {int(obtenido.isna().sum())} oficios"
        )
        diferencia = int((esperado != obtenido).sum())
        print(f"  {columna:<22} reproduce {TIPO_QUE_REPRODUCE[columna]:<18} "
              f"oficios que no cuadran: {diferencia}")
        assert diferencia == 0, (
            f"{columna} no se reproduce desde la tabla de competencias: "
            f"{diferencia} oficios difieren (el puente ESCO cambio)"
        )
    return True


def main() -> None:
    faltantes = [p for p in (OCCUPATIONS, SKILL_RELATIONS) if not p.exists()]
    if faltantes:
        raise FileNotFoundError(
            "Faltan las fuentes limpias de ESCO en data/02_interim/: "
            + ", ".join(p.name for p in faltantes)
            + "\nEjecuta primero: python src/limpieza/limpiar_datos.py"
        )

    print("=" * 78)
    print("TABLA DE COMPETENCIAS POR OFICIO (ESCO 'essential', normalizada)")
    print("=" * 78)
    occ = _cargar(OCCUPATIONS)
    rel = _cargar(SKILL_RELATIONS)
    print(f"occupations_en_limpio.csv          : {len(occ):,} filas")
    print(f"occupationSkillRelations_en_limpio : {len(rel):,} filas")

    # 1. Solo 'essential' y sin pares repetidos. La deduplicacion va por
    #    (occupationUri, skillUri) -los identificadores-, no por las etiquetas:
    #    es exactamente la que aplica `integrar_empleos.py`, y por eso los
    #    conteos de este script y los del pipeline son comparables.
    rel = rel.loc[rel["relationType"].eq(RELACION_KEPT)]
    rel = rel.drop_duplicates(subset=["occupationUri", "skillUri"])
    print(f"\nPares '{RELACION_KEPT}' tras deduplicar: {len(rel):,}")

    # 2. El salto code -> occupationUri (UUID). Sin el, el cruce es imposible y
    #    falla en silencio devolviendo 0 filas; va resuelto aqui una sola vez.
    mapa = occ[["code", "conceptUri", "preferredLabel"]].drop_duplicates(subset="code")
    par = rel.merge(mapa, left_on="occupationUri", right_on="conceptUri", how="inner")
    assert not par.empty, "El puente code <-> occupationUri devolvio 0 filas"

    # 3. Frontera de nombres: ESCO escribe en camelCase y ademas trae la misma
    #    etiqueta de oficio en el puente y en occupations. Se normaliza todo en
    #    este punto y se verifica que las dos copias coincidan.
    par = par.rename(
        columns={
            "code": "occupation_code",
            "preferredLabel": "occupation_label",
            "skillLabel": "habilidad_nombre",
            "skillType": "habilidad_tipo",
        }
    )
    etiquetas_bridge = par["occupation_label"].ne(par["occupationLabel"]) | par["occupationLabel"].isna()
    assert int(etiquetas_bridge.sum()) == 0, (
        f"El puente trae {int(etiquetas_bridge.sum())} etiquetas de oficio que "
        "difieren de occupations; la fuente se actualizo sin re-limpiar"
    )
    par["habilidad_tipo"] = par["habilidad_tipo"].where(par["habilidad_tipo"].notna(), TIPO_SIN_DEFINIR)
    tabla = par[COLUMNAS]

    # Orden determinista: el archivo se lee estable entre corridas y cada oficio
    # queda con sus competencias en filas contiguas, asi que el CSV crudo tambien
    # sirve para inspeccionar un cargo a ojo.
    #
    # El tipo NO se ordena alfabeticamente: como 'sin_tipo' empieza por 'i', el
    # orden alfabetico lo pondria antes que 'skill/competence'. Aqui se usa el
    # orden de los buckets que el pipeline ya declaro en `COLUMNAS` de
    # `integrar_empleos.py` (competence -> knowledge -> sin_tipo), que deja los
    # 39 pares sin tipo al final, donde se notan. La columna auxiliar se descarta
    # para no dejar `habilidad_tipo` como categorica: se propagaria al
    # `pivot_table` de abajo y contaminaria el conteo con categorias no vistas.
    orden_tipo = {t: i for i, t in enumerate((*TIPOS_ESCO, TIPO_SIN_DEFINIR))}
    tabla = tabla.assign(_tipo=tabla["habilidad_tipo"].map(orden_tipo))
    tabla = (
        tabla.sort_values(["occupation_code", "_tipo", "habilidad_nombre"], kind="stable")
        .drop(columns="_tipo")
        .reset_index(drop=True)
    )

    # 4. Validacion de la tabla, antes de escribirla.
    print("=" * 78)
    print("VALIDACION DE LA TABLA")
    print("=" * 78)
    n_habilidades = int(tabla["habilidad_nombre"].nunique())
    print(f"Pares (oficio, competencia) : {len(tabla):,}")
    print(f"Oficios con competencias   : {tabla['occupation_code'].nunique():,}")
    print(f"Habilidades distintas      : {n_habilidades:,}")
    print(f"Tipos: " + ", ".join(
        f"{t}={int(tabla['habilidad_tipo'].eq(t).sum()):,}"
        for t in (*TIPOS_ESCO, TIPO_SIN_DEFINIR)
    ))

    assert len(tabla) == ESPERADO["pares_essential"], (
        f"Pares (oficio, competencia): {len(tabla):,} != {ESPERADO['pares_essential']:,}"
    )
    assert tabla["occupation_code"].nunique() == ESPERADO["oficios_esco"], (
        f"Oficios: {tabla['occupation_code'].nunique():,} != {ESPERADO['oficios_esco']:,}"
    )
    assert int(tabla["habilidad_tipo"].eq("skill/competence").sum()) == ESPERADO["competencias"], (
        "El reparto de skill/competence cambio respecto al canon"
    )
    assert int(tabla["habilidad_tipo"].eq("knowledge").sum()) == ESPERADO["conocimiento"], (
        "El reparto de knowledge cambio respecto al canon"
    )
    assert int(tabla["habilidad_tipo"].eq(TIPO_SIN_DEFINIR).sum()) == ESPERADO["sin_tipo"], (
        "El numero de relaciones sin skillType cambio respecto al canon"
    )
    # Sin nombres vacios: una competencia sin nombre no se puede mostrar ni
    # comparar, y ESCO si los publica, asi que un vacio aqui es un dato roto.
    assert int(tabla["habilidad_nombre"].isna().sum()) == 0, (
        f"{int(tabla['habilidad_nombre'].isna().sum())} competencias sin nombre"
    )
    # Un par (oficio, competencia) no puede repetirse. Esto es lo que garantiza
    # que contar filas por oficio equivalga a contar competencias distintas: sin
    # este assert, el contraste contra `n_skills_essential` compararia dos
    # cosas distintas.
    assert not tabla.duplicated(subset=["occupation_code", "habilidad_nombre"]).any(), (
        "Hay pares (oficio, competencia) repetidos: el conteo por oficio dejaria "
        "de equivaler al conteo de competencias distintas"
    )

    # Conteo por oficio y por tipo: es la tabla de 4 columnas que despues se
    # compara con los contadores del pipeline, y la que usaria
    # `indicadores.resumen_competencias` sin releer la fuente ESCO.
    conteo = tabla.pivot_table(
        index="occupation_code", columns="habilidad_tipo", values="habilidad_nombre",
        aggfunc="size", fill_value=0,
    )
    for tipo in (*TIPOS_ESCO, TIPO_SIN_DEFINIR):
        if tipo not in conteo.columns:
            conteo[tipo] = 0
    conteo = conteo.rename(columns={
        "skill/competence": "n_skills_competence",
        "knowledge": "n_skills_knowledge",
        TIPO_SIN_DEFINIR: "n_skills_sin_tipo",
    })
    conteo["n_skills_essential"] = conteo[
        ["n_skills_competence", "n_skills_knowledge", "n_skills_sin_tipo"]
    ].sum(axis=1)
    desbalance = int((conteo[["n_skills_competence", "n_skills_knowledge", "n_skills_sin_tipo"]]
                      .sum(axis=1) != conteo["n_skills_essential"]).sum())
    assert desbalance == 0, f"{desbalance} oficios no cierran competence+knowledge+sin_tipo"
    print(f"Cierre competence+knowledge+sin_tipo por oficio: {desbalance} oficios descuadrados")

    # 5. Contraste con los contadores del pipeline (red de seguridad de la
    #    desnormalizacion de `n_skills_essential`).
    validado = _validar_contra_empleos(conteo)

    # 6. Exportar.
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(SALIDA, index=False, encoding="utf-8")
    print("=" * 78)
    print("SALIDA")
    print("=" * 78)
    print(f"Escrito: {SALIDA} ({SALIDA.stat().st_size / 1e6:.1f} MB)")
    print(f"Filas: {len(tabla):,} | Oficios: {tabla['occupation_code'].nunique():,} | "
          f"Columnas: {', '.join(COLUMNAS)}")
    print("Se une con los CSV del pipeline por `occupation_code` (N:1). Ningun CSV")
    print("existente fue modificado.")

    # 7. Bitacora de ejecucion.
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    nuevo = not BITACORA.exists()
    fila = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "script": Path(__file__).name,
        "python": sys.version.split()[0],
        "sha256_occupations": _sha256(OCCUPATIONS)[:16],
        "sha256_skill_relations": _sha256(SKILL_RELATIONS)[:16],
        "pares": len(tabla),
        "oficios": int(tabla["occupation_code"].nunique()),
        "habilidades_distintas": n_habilidades,
        "contraste_empleos": "OK" if validado else "OMITIDO",
        "estado": "OK",
    }
    with BITACORA.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(fila))
        if nuevo:
            writer.writeheader()
        writer.writerow(fila)
    print(f"Bitacora de ejecucion persistida: {BITACORA}")

    print("\nTabla de competencias generada sin errores.")


if __name__ == "__main__":
    main()
