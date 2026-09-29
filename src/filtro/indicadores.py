"""Indicadores reutilizables para el análisis de los cuadernos del proyecto.

Derivados calculados en vivo a partir de `data/03_processed/empleos_limpio.csv`:

- Duración de cada experiencia en trimestres (fórmula inclusiva; `Present` → NaN).
- Distribuciones (IQR de Tukey) y concentración por ocupación / grupo ISCO.
- Transiciones consecutivas entre grupos ISCO por persona.
- Brechas sin empleo registrado (proxy de desempleo), previa fusión de
  periodos solapados para no confundir pluriempleo con desempleo.

Y los nombres de las competencias ESCO, que no viven en los CSV del pipeline
(allí solo hay contadores, para no multiplicar las filas). Hay dos caminos:

- `cargar_competencias()`: lee `data/03_processed/competencias_por_oficio.csv`,
  la tabla normalizada que produce `src/limpieza/generar_competencias.py`
  (1 fila = 1 competencia de 1 oficio). Es la vía preferida.
- `cargar_relaciones()`: lee el puente ESCO crudo y resuelve el salto
  `code` -> `occupationUri` (UUID) en el momento. Sin ese salto el cruce no es
  posible y falla en silencio devolviendo 0 filas; se conserva como lectura
  directa de la fuente y como referencia de contraste.

Sobre esa tabla: `perfil_persona()` arma la trayectoria de una persona con las
competencias que exigía cada contrato, y `salto_competencias()` mide el
Jaccard entre contratos consecutivos.

Práctica: las funciones son puras (sin I/O) para que el libro decida qué
muestra y cómo lo interpreta. Las dos únicas excepciones son
`cargar_competencias()` y `cargar_relaciones()`.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

SENTINELA_FIN = 99_999  # fin ordinal de 'Present': última experiencia censurada
TRIMESTRE_VALIDO = re.compile(r"^Q([1-4])\s+(\d{4})$")

# Puente de competencias ESCO (única fuente de los NOMBRES de skill; los CSV del
# pipeline solo llevan contadores). Vive en data/02_interim/SKILLS/ porque se
# limpió aparte del resto de ESCO.
RAIZ = Path(__file__).resolve().parents[2]
RUTA_RELACIONES = RAIZ / "data" / "02_interim" / "SKILLS" / "occupationSkillRelations_en_limpio.csv"
RUTA_OCCUPATIONS = RAIZ / "data" / "02_interim" / "ESCO" / "occupations_en_limpio.csv"

# Tabla normalizada de competencias (produce `src/limpieza/generar_competencias.py`).
# Ya viene con el salto `code` -> `occupationUri` resuelto y contrastada contra los
# contadores del pipeline, asi que consultarla no obliga a rehacer ese cruce.
RUTA_COMPETENCIAS = RAIZ / "data" / "03_processed" / "competencias_por_oficio.csv"

# Como se ve un cargo que no se pudo clasificar. NUNCA se deja en blanco: vacio
# diria "no hay informacion de competencias", cuando lo cierto es "no sabemos que
# cargo era" - y no son lo mismo. `saber_skills` conserva el dato crudo; esto es
# solo la forma de mostrarlo.
OFICIO_NO_CLASIFICADO = "[OFICIO NO CLASIFICADO]"
AVISO_SIN_COMPETENCIAS = "\u26a0 habilidades desconocidas: no sabemos que trabajo era"

# Solo 'essential'. Ver `integrar_empleos.py`: las 'optional' son telemetría de
# jerarquía y el pipeline no las usa.
RELACION_KEPT = "essential"

# Banderas de clasificacion que escribe `limpiar_empleos.py`.
BANDERAS = ("es_unknown_ocupacion", "es_rescatado", "es_vigente")


def cargar_relaciones() -> pd.DataFrame:
    """ÚNICA función con I/O del módulo: lee el puente de competencias.

    Devuelve `code` (código de ocupación ESCO) en lugar de `occupationUri`
    (UUID), porque `code` es la llave que ya existe en `empleos_limpio.csv`.
    Ese salto code -> occupationUri es el que hace el cruce posible; omitirlo
    devuelve 0 filas sin error visible, así que va resuelto aquí una sola vez.
    """
    occ = pd.read_csv(RUTA_OCCUPATIONS, dtype=str, encoding="utf-8",
                      keep_default_na=False, na_values=[""])
    rel = pd.read_csv(RUTA_RELACIONES, dtype=str, encoding="utf-8",
                      keep_default_na=False, na_values=[""])
    mapa = occ[["code", "conceptUri"]].drop_duplicates(subset="code")
    rel = rel.loc[rel["relationType"].eq(RELACION_KEPT)]
    rel = rel.drop_duplicates(subset=["occupationUri", "skillUri"])
    par = rel.merge(mapa, left_on="occupationUri", right_on="conceptUri", how="inner")
    return par[["code", "occupationLabel", "skillType", "skillLabel"]].rename(
        columns={"code": "occupation_code", "skillType": "skill_type",
                 "skillLabel": "skill_label"}
    )


def skills_de_ocupacion(relaciones: pd.DataFrame, occupation_code: str) -> pd.DataFrame:
    """Competencias esenciales que exige un cargo (tabla de `cargar_relaciones`).

    Devuelve una fila por competencia, ordenada por tipo. Se llama con el
    `occupation_code` de `empleos_limpio.csv`; ese código coincide con
    `n_skills_essential`, así que el conteo y la lista son consistentes.
    """
    sub = relaciones.loc[relaciones["occupation_code"].eq(occupation_code)]
    assert not sub.empty, f"El código {occupation_code!r} no tiene competencias"
    return sub.sort_values(["skill_type", "skill_label"]).reset_index(drop=True)


def skills_de_persona(empleos: pd.DataFrame, relaciones: pd.DataFrame) -> pd.DataFrame:
    """Competencias atribuidas a una persona a lo largo de TODAS sus experiencias.

    Devuelve una fila por (`resume_id`, `skill_label`): si la persona repite el
    mismo cargo 19 veces, esa skill aparece UNA vez, no 19. El conteo de
    experiencias y de cargos distintos queda en la propia tabla, para que la
    repetición siga siendo visible.

    Solo incluye filas con `saber_skills == 'ok'`; las 'no_clasificado' no
    tienen cargo y por lo tanto no tienen competencias atribuibles.
    """
    clave = ["resume_id", "occupation_code", "occupation_label",
             "n_skills_essential", "saber_skills"]
    trabajo = empleos.loc[empleos["saber_skills"].eq("ok"), clave].drop_duplicates()
    salida = trabajo.merge(relaciones, on="occupation_code", how="inner")
    salida = salida.sort_values(["resume_id", "skill_type", "skill_label"])
    return salida.reset_index(drop=True)


def resumen_competencias(empleos: pd.DataFrame) -> pd.DataFrame:
    """Reparto de `n_skills_essential` por tipo de cargo y split knowledge/competence.

    Los contadores llegan como texto porque el proyecto lee los CSV con
    `dtype=str` (regla para no perder ceros en los códigos); se convierten aquí.
    """
    num = lambda c: pd.to_numeric(empleos[c], errors="coerce")
    trabajo = empleos.loc[empleos["saber_skills"].eq("ok")].copy()
    trabajo["_n"] = num("n_skills_essential").loc[trabajo.index]
    trabajo["_c"] = num("n_skills_competence").loc[trabajo.index]
    trabajo["_k"] = num("n_skills_knowledge").loc[trabajo.index]
    trabajo["_s"] = num("n_skills_sin_tipo").loc[trabajo.index]
    por_cargo = trabajo.groupby("occupation_code").agg(
        n_skills_essential=("_n", "first"),
        n_skills_competence=("_c", "first"),
        n_skills_knowledge=("_k", "first"),
        n_skills_sin_tipo=("_s", "first"),
        experiencias=("resume_id", "size"),
    )
    return por_cargo.sort_values("n_skills_essential", ascending=False).reset_index()


def cargar_competencias() -> pd.DataFrame:
    """Lee la tabla de competencias por oficio (produce `generar_competencias.py`).

    Devuelve columnas `occupation_code`, `occupation_label`, `habilidad_nombre` y
    `habilidad_tipo`. Es la vía preferida para consultar nombres: el archivo ya
    existe, el salto `code` -> `occupationUri` ya está hecho y validado contra
    `n_skills_essential`, y leerlo no depende de que la fuente ESCO siga donde
    estaba.

    `cargar_relaciones()` se conserva como lectura directa de la fuente ESCO, que
    es la que usaba el pipeline antes de que existiera esta tabla.

    Si la fuente ESCO cambia, hay que regenerar el archivo antes de usar esto:
        python src/limpieza/generar_competencias.py
    """
    assert RUTA_COMPETENCIAS.exists(), (
        f"Falta la tabla de competencias: {RUTA_COMPETENCIAS}\n"
        "Generala con: python src/limpieza/generar_competencias.py"
    )
    return pd.read_csv(RUTA_COMPETENCIAS, dtype=str, encoding="utf-8",
                       keep_default_na=False, na_values=[""])


def competencias_por_oficio(competencias: pd.DataFrame) -> dict[str, list[str]]:
    """De la tabla normalizada (1 fila = 1 competencia) a 1 lista por oficio.

    Es el paso de "guardar desglosado" a "mostrar junto": un cargo con 20
    competencias ocupa 20 filas en el CSV y aparece aquí como una sola lista de
    20 nombres, que es como se lee. Los nombres van ordenados para que dos
    llamadas den el mismo resultado.

    Un oficio ausente del diccionario no tiene competencias conocidas: eso NO es
    lo mismo que tener cero, y por eso la ausencia no se rellena con una lista
    vacía en los llamadores.
    """
    por_codigo = (
        competencias.sort_values("habilidad_nombre", kind="stable")
        .groupby("occupation_code")["habilidad_nombre"]
        .agg(list)
    )
    return por_codigo.to_dict()
def _ordinal_trimestre(serie: pd.Series) -> pd.Series:
    """Ordinal continuo de un trimestre 'Q4 2010' -> 2010*4 + 4 = 8044."""
    partes = serie.str.extract(TRIMESTRE_VALIDO, expand=False)
    anio = partes[1].astype("float64")
    trim = partes[0].astype("float64")
    return (anio * 4 + trim).astype("float64")


def _ordenar_empleos(
    df: pd.DataFrame, columnas: list[str]
) -> "tuple[pd.DataFrame, pd.Series, pd.Series]":
    """Ordena experiencias de cada persona por (inicio, fin) y devuelve ordin.

    `Present` recibe el sentinel SENTINELA_FIN y su duración será NaN.
    """
    trabajo = df[["resume_id", "start_date", "end_date", *columnas]].copy()
    ini = _ordinal_trimestre(trabajo["start_date"])
    fin = _ordinal_trimestre(trabajo["end_date"])
    cod = trabajo["end_date"].ne("Present")
    trabajo = trabajo.assign(
        _ini=ini,
        _fin=fin.where(cod, SENTINELA_FIN),
    ).sort_values(["resume_id", "_ini", "_fin"], kind="stable")
    return trabajo, trabajo["_ini"], trabajo["_fin"]


def duracion_trimestres(df: pd.DataFrame) -> pd.Series:
    """Duración inclusiva de cada experiencia (ordinal_fin - ordinal_ini + 1).

    `Present` no tiene fin observado: se devuelve NaN (censura), nunca 0.
    """
    trabajo, ini, fin = _ordenar_empleos(df, [])
    observada = trabajo["end_date"].notna() & trabajo["end_date"].ne("Present")
    return (fin - ini + 1).where(observada)


def distribucion_duracion(df: pd.DataFrame) -> pd.DataFrame:
    """Resumen de duración (finalizadas): mediana, IQR de Tukey y outliers.

    Se calcula sobre duraciones observadas; no se imputa ni se gana.
    Un periodo finalizado puede durar 1 trimestre como mínimo.
    """
    dur = duracion_trimestres(df).dropna()
    q1, q3 = dur.quantile([0.25, 0.75])
    iqr = q3 - q1
    lim_inf, lim_sup = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    fuera = dur[(dur < lim_inf) | (dur > lim_sup)]
    return pd.DataFrame(
        {
            "n_finalizadas": [int(dur.size)],
            "mediana": [float(dur.median())],
            "media": [round(float(dur.mean()), 2)],
            "q1": [float(q1)],
            "q3": [float(q3)],
            "iqr": [float(iqr)],
            "min": [float(dur.min())],
            "max": [float(dur.max())],
            "fuera_de_iqr_n": [int(fuera.size)],
            "fuera_de_iqr_%": [round(100 * fuera.size / dur.size, 2)],
        }
    )


def duracion_mediana_por_grupo(df: pd.DataFrame, top: int = 15) -> pd.DataFrame:
    """Mediana de duración por grupo ISCO (grupos más frecuentes)."""
    grupo = df[["isco_group_label", "start_date", "end_date", "resume_id"]].copy()
    grupo = grupo.dropna(subset=["isco_group_label"])
    grupo = grupo.assign(dur=duracion_trimestres(grupo)).dropna(subset=["dur"])
    resumen = (
        grupo.groupby("isco_group_label")["dur"]
        .agg(mediana="median", n_empleos="size")
        .sort_values("n_empleos", ascending=False)
        .head(top)
    )
    return resumen.round(2)


def duracion_mediana_por_nivel(df: pd.DataFrame) -> pd.DataFrame:
    """Mediana de duración por nivel educativo."""
    sub = df[["university_level", "start_date", "end_date", "resume_id"]].copy()
    sub = sub.assign(dur=duracion_trimestres(sub)).dropna(subset=["dur"])
    return (
        sub.groupby("university_level")["dur"]
        .agg(mediana="median", n_empleos="size")
        .round(2)
    )


def top_valores(serie: pd.Series, n: int = 10) -> pd.DataFrame:
    """Top n de una columna categórica (% sobre el total con etiqueta)."""
    vc = serie.dropna().value_counts().head(n).rename("n")
    total = int(serie.notna().sum())
    out = vc.to_frame()
    out["%_de_con_etiqueta"] = (out["n"] / total * 100).round(2)
    return out


def crosstab_nivel_grupo(df: pd.DataFrame, top: int = 30) -> pd.DataFrame:
    """% de filas por fila-nivel: frecuencia relativa de grupos ISCO por nivel."""
    top_grupos = df["isco_group_label"].dropna().value_counts().head(top).index
    sub = df[df["isco_group_label"].isin(top_grupos)]
    cruce = pd.crosstab(sub["university_level"], sub["isco_group_label"])
    return (cruce.div(cruce.sum(axis=1), axis=0) * 100).round(2)


def _repetidas_exactas(df: pd.DataFrame) -> pd.DataFrame:
    """Quita filas repetidas (resume_id, start, end) para transiciones/solape.

    El pipeline ya marcó estas 18.749 repeticiones; mantenerlas inflaría
    los indicadores de transición y pluriempleo con ruido.
    """
    return df.drop_duplicates(subset=["resume_id", "start_date", "end_date"], keep="first")


def _etiquetas_por_oficio(competencias: pd.DataFrame) -> pd.Series:
    """`occupation_code` -> `occupation_label`, con una sola etiqueta por oficio."""
    oficios = competencias[["occupation_code", "occupation_label"]].drop_duplicates(
        subset="occupation_code"
    )
    assert not oficios["occupation_code"].duplicated().any(), (
        "La tabla de competencias trae mas de una etiqueta para el mismo oficio"
    )
    return oficios.set_index("occupation_code")["occupation_label"]


def resumen_perfil(empleos: pd.DataFrame, resume_id: str) -> pd.DataFrame:
    """Una fila con los numeros de la trayectoria, para encabezar `perfil_persona()`.

    `contrato_mas_repetido` es el mayor valor de `veces_ese_oficio`: quantas
    veces la persona repite un mismo cargo. Va aparte de `periodos` porque
    "12 periodos" y "12 periodos del mismo cargo" son trayectorias opuestas.
    """
    ruta = empleos.loc[empleos["resume_id"].eq(resume_id)]
    assert not ruta.empty, f"La persona {resume_id!r} no tiene experiencias"
    niveles = ruta["university_level"].dropna().unique()
    veces = pd.to_numeric(ruta["veces_ese_oficio"], errors="coerce")
    sin_oficio = int(ruta["occupation_code"].isna().sum())
    return pd.DataFrame([{
        "persona": resume_id,
        "nivel_educativo": niveles[0] if len(niveles) else "No reportado",
        "periodos": int(len(ruta)),
        "oficios_distintos": int(ruta["occupation_code"].nunique()),
        "periodos_con_oficio": int(len(ruta) - sin_oficio),
        "periodos_sin_oficio": sin_oficio,
        "contrato_mas_repetido": int(veces.max()) if veces.notna().any() else 0,
    }])


def perfil_persona(
    empleos: pd.DataFrame, competencias: pd.DataFrame, resume_id: str
) -> pd.DataFrame:
    """Trayectoria de una persona: una fila por experiencia, con lo que exigía cada cargo.

    Las experiencias van en orden cronológico (inicio, fin), no en el orden del
    CSV, para que la ruta se lea como una línea de tiempo. Se conservan TODAS,
    incluidas las repeticiones exactas: en una trayectoria, "estuvo 12 periodos
    como auxiliar de nómina" es información, no ruido.

    Qué significa cada columna (leer antes de interpretar):
        `occupation_label`  : el cargo según ESCO. Donde no se pudo clasificar
            aparece `[OFICIO NO CLASIFICADO]`, nunca vacío: vacío diría "este
            cargo no exige nada", que es falso, cuando lo cierto es que no
            sabemos qué cargo era.
        `competencias`      : los NOMBRES de las competencias 'essential' que
            el contrato exigía. Es atribución por CONTRATO - si la persona
            ocupó el cargo, su contrato obligaba a esas competencias. No dice
            que las ejecute hoy ni que las domine todas; y no dice nada de los
            periodos sin oficio clasificado, que quedan declarados desconocidos.
        `n_competencias`    : cuántas son. Sale de la tabla de competencias, no
            del contador `n_skills_essential` del dataset; ambos se cruzan aquí
            y tienen que coincidir.
        `veces_ese_oficio`  : cuántas experiencias tiene esta persona en ESTE
            cargo, para que la repetición no se esconda detrás del nombre.
        `aviso`             : vacío, o el texto que declara que las competencias
            son desconocidas. Viaja con la fila para que el "no sabemos" no se
            pierda al filtrar o al exportar.
    """
    columnas = ["occupation_code", "occupation_label", "saber_skills",
                "veces_ese_oficio", "n_skills_essential"]
    trabajo, ini, fin = _ordenar_empleos(
        empleos.loc[empleos["resume_id"].eq(resume_id)], columnas
    )
    assert not trabajo.empty, f"La persona {resume_id!r} no tiene experiencias"
    trabajo = trabajo.reset_index(drop=True)

    por_oficio = competencias_por_oficio(competencias)
    sin_oficio = trabajo["occupation_code"].isna()

    salida = trabajo.assign(
        # 'Present' no tiene fin observado: su duración es NaN (censura), nunca 0.
        duracion_trimestres=(fin - ini + 1).where(trabajo["end_date"].ne("Present")),
        occupation_label=trabajo["occupation_label"].where(
            ~sin_oficio, OFICIO_NO_CLASIFICADO
        ),
        orden=range(1, len(trabajo) + 1),
    )
    salida["competencias"] = [
        por_oficio[code] if pd.notna(code) else []
        for code in salida["occupation_code"]
    ]
    salida["n_competencias"] = salida["competencias"].apply(len)
    salida["aviso"] = sin_oficio.map({True: AVISO_SIN_COMPETENCIAS, False: ""})
    # El proyecto lee los CSV como texto (regla para no perder ceros en los
    # codigos), asi que los contadores llegan como '1.0' y no como 1. Se
    # convierten aqui, igual que en `resumen_competencias`: convertirlos en el
    # llamador repetition es donde uno se encuentra `int('1.0')`.
    salida["veces_ese_oficio"] = pd.to_numeric(
        salida["veces_ese_oficio"], errors="coerce"
    )

    # El contador del dataset y el conteo de la tabla no pueden separarse: son
    # la misma informacion en dos sitios. Si divergen, alguien regenero uno y no
    # el otro, y el perfil no debe decidir cual de los dos va bien.
    declarado = pd.to_numeric(salida["n_skills_essential"], errors="coerce")
    assert not (declarado.isna() != sin_oficio).any(), (
        "vacío != 0 roto: hay ocupacion con el contador vacio o al reves"
    )
    assert not ((declarado != salida["n_competencias"]) & declarado.notna()).any(), (
        "n_skills_essential no coincide con el conteo de la tabla de competencias"
    )
    # Invariante del puente: si hay codigo, hay competencias. El generador lo
    # garantiza; un vacio aqui significa tabla y dataset desincronizados.
    sin_competencias = (~sin_oficio) & salida["n_competencias"].eq(0)
    assert not sin_competencias.any(), (
        f"{int(sin_competencias.sum())} filas con occupation_code pero sin ninguna "
        "competencia: regenera la tabla con generar_competencias.py"
    )

    return salida[[
        "orden", "occupation_code", "occupation_label", "start_date", "end_date",
        "duracion_trimestres", "veces_ese_oficio", "n_competencias",
        "competencias", "saber_skills", "aviso",
    ]]


def salto_competencias(
    empleos: pd.DataFrame, competencias: pd.DataFrame
) -> "tuple[pd.DataFrame, dict[str, float | int]]":
    """Similitud entre las competencias que exigen dos contratos consecutivos.

    Devuelve `(detalle, resumen)`. El detalle tiene una fila por transición
    consecutiva de una persona en la que **ambos** cargos son conocidos
    (`occupation_code` presente); el resumen trae la distribución de esa medida.

    La medida es el índice de Jaccard de los nombres: `|A ∩ B| / |A ∪ B|`. Vale
    1 cuando los dos cargos exigen exactamente las mismas competencias y 0
    cuando no comparten ni una sola. Como la mediana es 0 y más de la mitad de
    las transiciones no comparte ninguna, el resumen reporta ese porcentaje
    aparte: es el dato que separa "el salto de oficio no tocó las competencias"
    de "el salto fue suave".

    Las repeticiones exactas (misma persona, mismo inicio, mismo fin) se eliminan
    antes de emparejar, igual que en `transiciones_consecutivas`. Ojo con lo que
    son: de los 15.290 grupos repetidos de `empleos_limpio.csv`, solo 2.127
    tienen un unico cargo (ahi si es duplicado). Los otros 13.163 son cargos
    DISTINTOS en el mismo periodo, es decir pluriempleo simultaneo. Un trabajo
    simultaneo no es una transicion, asi que se descarta: emparejar A -> B cuando
    los dos ocurrieron a la vez seria un salto de empleo inexistente.

    Un periodo SIN OFICIO CLASIFICADO, en cambio, si rompe la cadena: no se salta
    para emparejar los trabajos de los lados. Si alguien tiene un hueco de tres
    anos cuyo cargo desconocemos, no se puede afirmar que paso directamente de A
    a B. Esto es el mismo criterio de `transiciones_consecutivas`, y hace que los
    dos indicadores de transicion del proyecto se calculen sobre la misma base y
    sean comparables.
    """
    por_oficio = {code: frozenset(nombres)
                  for code, nombres in competencias_por_oficio(competencias).items()}
    etiquetas = _etiquetas_por_oficio(competencias)

    trabajo, _, _ = _ordenar_empleos(
        _repetidas_exactas(empleos), ["occupation_code"]
    )
    # Se empareja PRIMERO y se filtra DESPUES: una fila sin oficio ocupa su lugar
    # en la secuencia y rompe la cadena, en vez de desaparecer y dejar que se
    # emparejen los trabajos de sus lados. Sin codigo no hay contrato que
    # comparar, y meter esas filas daria un Jaccard indefinido (0/0), no un cero.
    hacia = trabajo.groupby("resume_id")["occupation_code"].shift(-1)
    par = trabajo.loc[hacia.notna()].copy()
    par["hacia_code"] = hacia.loc[par.index]
    par = par.loc[par["occupation_code"].isin(por_oficio)
                  & par["hacia_code"].isin(por_oficio)]

    desde_conjuntos = [por_oficio[c] for c in par["occupation_code"]]
    hacia_conjuntos = [por_oficio[c] for c in par["hacia_code"]]
    compartidas = np.array([len(a & b) for a, b in zip(desde_conjuntos, hacia_conjuntos)])
    uniones = np.array([len(a | b) for a, b in zip(desde_conjuntos, hacia_conjuntos)])
    # Toda transicion emparejada tiene ambos cargos con competencias, asi que
    # la union nunca es 0; el `where` esta para que un dato roto se vea como NaN
    # en vez de become un error o un falso cero.
    jaccard = np.where(uniones > 0, compartidas / uniones, np.nan)

    detalle = pd.DataFrame({
        "resume_id": par["resume_id"].to_numpy(),
        "desde_code": par["occupation_code"].to_numpy(),
        "desde_label": par["occupation_code"].map(etiquetas).to_numpy(),
        "hacia_code": par["hacia_code"].to_numpy(),
        "hacia_label": par["hacia_code"].map(etiquetas).to_numpy(),
        "n_desde": [len(a) for a in desde_conjuntos],
        "n_hacia": [len(b) for b in hacia_conjuntos],
        "n_compartidas": compartidas,
        "jaccard": jaccard,
    })
    mismo_cargo = int(detalle["desde_code"].eq(detalle["hacia_code"]).sum())
    sin_compartir = int(detalle["n_compartidas"].eq(0).sum())
    resumen: dict[str, float | int] = {
        "personas": int(detalle["resume_id"].nunique()),
        "transiciones": int(len(detalle)),
        "mismo_cargo": mismo_cargo,
        "%_mismo_cargo": round(100 * mismo_cargo / len(detalle), 2) if len(detalle) else np.nan,
        "jaccard_mediana": float(np.median(jaccard)) if len(detalle) else np.nan,
        "jaccard_p25": float(np.percentile(jaccard, 25)) if len(detalle) else np.nan,
        "jaccard_p75": float(np.percentile(jaccard, 75)) if len(detalle) else np.nan,
        "transiciones_sin_ninguna_compartida": sin_compartir,
        "%_sin_ninguna_compartida": round(100 * sin_compartir / len(detalle), 2) if len(detalle) else np.nan,
    }
    return detalle, resumen


def transiciones_consecutivas(df: pd.DataFrame, columna: str = "isco_group_label") -> pd.DataFrame:
    """Pares consecutivos (desde -> hacia) por persona, ordenados por fecha.

    Solo cuenta parejas con ambas etiquetas conocidas; la primera experiencia
    de una persona no tiene 'desde' anterior y la última no tiene 'hacia'.
    """
    trabajo, _, _ = _ordenar_empleos(_repetidas_exactas(df), [columna])
    desde = trabajo[columna]
    hacia = trabajo.groupby("resume_id")[columna].shift(-1)
    parejas = trabajo.loc[desde.notna() & hacia.notna(), ["resume_id"]].copy()
    parejas["desde"] = desde[parejas.index]
    parejas["hacia"] = hacia[parejas.index]
    return (
        parejas.groupby(["desde", "hacia"], dropna=False)
        .size()
        .rename("n")
        .reset_index()
        .sort_values("n", ascending=False)
    )


def proporcion_mismo_grupo(df: pd.DataFrame) -> float:
    """% de transiciones consecutivas que conservan el grupo ISCO."""
    trans = transiciones_consecutivas(df)
    total = int(trans["n"].sum())
    if total == 0:
        return 0.0
    mismo = int(trans.loc[trans["desde"].eq(trans["hacia"]), "n"].sum())
    return 100 * mismo / total


def primera_a_segunda(df: pd.DataFrame, columna: str = "isco_group_label") -> pd.DataFrame:
    """De la primera a la segunda experiencia de cada persona."""
    trabajo, _, _ = _ordenar_empleos(_repetidas_exactas(df), [columna])
    orden = trabajo.groupby("resume_id").cumcount()
    primera = trabajo.loc[orden.eq(0), ["resume_id", columna]].copy()
    segunda = trabajo.loc[orden.eq(1), ["resume_id", columna]].copy()
    parejas = primera.merge(
        segunda, on="resume_id", suffixes=("_primera", "_segunda")
    ).dropna(subset=[f"{columna}_primera", f"{columna}_segunda"])
    return (
        parejas.groupby([f"{columna}_primera", f"{columna}_segunda"], dropna=False)
        .size()
        .rename("n")
        .reset_index()
        .sort_values("n", ascending=False)
    )


def brechas_entre_empleos(df: pd.DataFrame) -> "tuple[pd.DataFrame, dict[str, float | int]]":
    """Períodos sin empleo registrado por persona (proxy de desempleo).

    Se ordena por (inicio, fin) y se usa el máximo de fines previos para
    fusionar periodos solapados: si el siguiente inicio cae dentro (o
    pegado al) empleo previo, la brecha es <= 0 y se cuenta como 0.

    Brecha positiva = trimestres sin empleo registrado entre experiencias.
    `Present` censura el final: su fila no produce brecha (asume continuidad
    hasta el corte; la limitación se declara en el libro).
    """
    trabajo, ini, _ = _ordenar_empleos(df, [])
    fin_max_previo = (
        trabajo.groupby("resume_id")["_fin"].cummax().groupby(trabajo["resume_id"]).shift(1)
    )
    brecha = (ini - fin_max_previo - 1).where(fin_max_previo.notna(), 0.0)
    trabajo = trabajo.assign(
        brecha=brecha.clip(lower=0.0),
        con_brecha=brecha > 0,
    )
    positivo = trabajo.loc[trabajo["con_brecha"], "brecha"]
    resumen: dict[str, float | int] = {
        "personas": int(trabajo["resume_id"].nunique()),
        "personas_con_brecha": int(trabajo.groupby("resume_id")["con_brecha"].any().sum()),
        "brechas": int(trabajo["con_brecha"].sum()),
        "mediana_trimestres": float(positivo.median()) if len(positivo) else np.nan,
        "max_trimestres": float(positivo.max()) if len(positivo) else np.nan,
    }
    columnas_salida = ["resume_id", "start_date", "end_date", "brecha", "con_brecha"]
    return trabajo[columnas_salida], resumen


def brechas_por_nivel(df: pd.DataFrame) -> pd.DataFrame:
    """Personas con brecha (n y %) y mediana de su mayor brecha por nivel."""
    brechas, _ = brechas_entre_empleos(df)
    mayor = (
        brechas.loc[brechas["con_brecha"], ["resume_id", "brecha"]]
        .groupby("resume_id")["brecha"]
        .max()
        .rename("max_brecha")
    ).reset_index()
    nivel = df[["resume_id", "university_level"]].drop_duplicates()
    mayor = mayor.merge(nivel, on="resume_id", how="left")
    base = nivel.groupby("university_level")["resume_id"].count().rename("personas_nivel")
    resumen = (
        mayor.groupby("university_level")
        .agg(personas_con_brecha=("resume_id", "nunique"), mediana_brecha=("max_brecha", "median"))
        .join(base)
    )
    resumen["%_con_brecha"] = (resumen["personas_con_brecha"] / resumen["personas_nivel"] * 100).round(2)
    return resumen.round(2)


def resumen_personas_solapadas(df: pd.DataFrame) -> pd.DataFrame:
    """Traslapes entre experiencias consecutivas de la misma persona.

    Usa el mismo método del diagnóstico (`contarFilasSolapadas`): comparar
    cada inicio con el **fin de la fila anterior** de la persona (tras ordenar
    por inicio/fin). Es una medición conservadora de pluriempleo / datos
    imprecisos; brechas no se ve afectada por ellos.
    """
    trabajo, ini, _ = _ordenar_empleos(df, [])
    fin_anterior = trabajo.groupby("resume_id")["_fin"].shift(1)
    traslapada = ini <= fin_anterior
    filas = int(traslapada.sum())
    personas = int(trabajo.loc[traslapada, "resume_id"].nunique())
    return pd.DataFrame(
        {
            "metrica": ["filas_traslapadas", "personas_traslapadas", "personas_total", "%_personas"],
            "valor": [
                filas,
                personas,
                int(df["resume_id"].nunique()),
                round(100 * personas / df["resume_id"].nunique(), 2),
            ],
        }
    )


def resumen_banderas(df: pd.DataFrame) -> pd.DataFrame:
    """Conteo de las banderas de clasificación del pipeline.

    Usa `_como_bool` de `filtros` porque el proyecto lee los CSV con
    `dtype=str` y las banderas llegan como el texto 'True'/'False'; sin la
    normalización, `int(serie.sum())` concatena las cadenas y revienta.
    """
    from filtros import _como_bool  # import diferido: evita ciclo con filtros

    banderas = {c: _como_bool(df[c]) for c in BANDERAS}
    return pd.DataFrame(
        {
            "flag": list(BANDERAS),
            "n": [int(banderas[c].sum()) for c in BANDERAS],
            "%_del_total": [round(100 * banderas[c].mean(), 2) for c in BANDERAS],
        }
    )