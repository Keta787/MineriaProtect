"""Transformacion de `data/03_processed/empleos_limpio*.csv` a una matriz `X`.

Este modulo es el codigo de la fase de Transformacion (KDD / CRISP-DM) que hasta
ahora vivia suelto dentro de `notebooks/4.0_transformacion.ipynb` y
`notebooks/4.1_transformacion_sin_outliers.ipynb`. Se extrajo para que:

- La logica se pueda ejecutar y verificar fuera del cuaderno, como el resto de
  `src/` (ver `docs/BUENAS_PRACTICAS_CODIGO.md`).
- Los dos cuadernos dejen de ser dos copias de las mismas ~500 lineas: ambos
  importan este modulo y solo difieren en la constante `VERSION`.

Que hace, en orden:

1. `leer()`             carga el CSV de la version pedida.
2. `fusionar_rescatado()`  completa `occupation_code` con el `matched_code` de las
   filas rescatadas en la sesion 3.
3. `fechas_ordinales()`/`educacion_ordinal()`  crean las variables derivadas
   (trimestre ordinal, duracion, nivel educativo ordinal).
4. `universo_con_competencias()`  deja el universo de trabajo: convierte los
   contadores de ESCO a numero, descarta las filas sin dato de competencias
   (midiendo el costo) y deriva el binario de reincidencia.
5. `submuestra()`/`codificar()`  toman la submuestra de trabajo y la codifican
   (one-hot + banderas en 0/1).
6. `escalar()`  aplica los tres escaladores, cada uno sobre las columnas que le
   corresponden, y `armar_X()` las concatena en la `X` final.

Practica: **ninguna funcion imprime**. Devuelven los datos y es el cuaderno quien
los formatea, porque el texto que las justifica ("sin escala, KNN agruparia por
calendario, no por carrera") es parte del entregable y debe seguir visible en la
celda, no escondido dentro de un `.py`.

El unico valor que el cuaderno elige es la semilla: se crea UN `RandomState` y se
pasa a `submuestra()` y despues a `diagnostico.auditoria_pca()`. Si cada paso
creara el suyo, el PCA recibiria un estado distinto y la corrida no seria
reproducible.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, RobustScaler

RAIZ = Path(__file__).resolve().parents[2]
PROC = RAIZ / "data" / "03_processed"

VERSION_CON_OUTLIERS = "con_outliers"
VERSION_SIN_OUTLIERS = "sin_outliers"
CSV_POR_VERSION = {
    VERSION_CON_OUTLIERS: "empleos_limpio.csv",
    VERSION_SIN_OUTLIERS: "empleos_limpio_sin_outliers.csv",
}

# Submuestra de trabajo: las dummies de ocupacion son ~2.800 columnas densas y
# no caben enteras en la `X` de prueba. Es una decision de Memoria, no de метodo.
SAMPLE_SIZE = 50_000
SEED_MUESTRA = 42
N_PARES = 300
SEED_DIST = 42

# El numero de columnas de la `X`, verificado en ejecucion y citado en
# README.md y docs/SKILLS.md. No es un numero fijo del codigo: las columnas de
# oficios salen de `get_dummies` sobre la submuestra, asi que un cambio de
# codificacion o de datos las moveria. Para eso `armar_X` lo comprueba al final
# y su mensaje obliga a actualizar las cifras en el MISMO commit.
FORMAS_X = {
    VERSION_CON_OUTLIERS: 2325,
    VERSION_SIN_OUTLIERS: 2326,
}

TRIMESTRE_VALIDO = re.compile(r"^Q([1-4])\s+(\d{4})$")
# 'Present' es censura por la derecha (el empleo sigue vigente): no se inventa su
# fin, se ubica en el trimestre del proyecto (Q1 2026). El valor usa la misma
# convencion que `to_ordinal` (anio * 4 + trimestre), no un indice de 0.
TRIMESTRE_CENSURA = 2026 * 4 + 1

# La ausencia es un estado, no un cero engañoso de estudios: 'No reportado' es el
# nivel mas bajo de la escala ordinal, no una credencial.
ORDEN_UNIV = {
    "No reportado": 0,
    "Secondary school": 1,
    "Bachelor": 2,
    "Master": 3,
    "PhD": 4,
}

# Las tres banderas del dataset limpio. Las dos primeras son True exactamente
# cuando `occupation_code` esta vacio. `es_vigente` NO sigue esa regla: es True
# en 18.956 filas, de las cuales 18.832 si tienen oficio, asi que describe otra
# cosa (el empleo que sigue vigente) y no la ausencia de dato.
BANDERAS = ["es_unknown_ocupacion", "es_rescatado", "es_vigente"]

# De las tres, solo UNA entra en la `X`. Las otras dos quedan constante False en el
# universo de trabajo, y una columna constante es ruido con consecuencias:
#
#   - no aporta nada a una distancia euclidea (KNN, k-means, PCA): todas las filas
#     estan a la misma distancia de ella, luego la dimension colapsa a 0;
#   - infla el conteo de features (2.327 -> 2.325);
#   - sobre todo, ENGAÑA cualquier lectura de importancia de variables: un modelo
#     que le de peso distinto de cero a una constante no esta usando informacion,
#     esta usando un artefacto del drop.
#
# No es un defecto del drop, es su consecuencia logica. El drop de la 2.5 se lleva
# las filas sin dato de competencia, y esas son exactamente las que llevan estas dos
# banderas en True. La `X` se construye solo con filas donde SI se conoce el oficio,
# asi que "no se conoce el oficio" es False por construccion: es una tautologia, no
# un dato. La informacion no se pierde, se muda al hecho de que esas filas no estan
# en la `X`. Las banderas siguen en el dataset, donde si significan algo.
#
# `es_vigente` si entra: "el empleo sigue vigente" no tiene relacion con conocer el
# oficio, asi que sobrevive al drop con sus dos valores.
BANDERAS_EN_X = ["es_vigente"]

# Las que quedan fuera, y por que. El `assert` de `codificar` verifica que sigan
# siendo constantes: si alguna vez dejaran de serlo, el aviso salta en vez de que la
# `X` cambie de forma silenciosa y todas las cifras citadas queden desactualizadas.
BANDERAS_EXCLUIDAS = ["es_unknown_ocupacion", "es_rescatado"]

# Los dos contadores de ESCO, listados una sola vez. `SKILLS` es el nombre que usa
# la medicion de aporte a la distancia; `CONTADORES`, el de la conversion a
# numero y la tabla de descriptivos. Son las mismas dos columnas.
SKILLS = ["n_skills_essential", "veces_ese_oficio"]
CONTADORES = SKILLS

# Columnas agrupadas por el escalador que les corresponde. El agrupamiento no es
# estetico: es la decision de la seccion de escalado, y las medidas de aporte a la
# distancia se leen sobre el mismo grupo.
NUM = ["start_ord", "end_ord", "dur_q"]        # Robust: tienen cola real
ORDINAL = ["univ_ord"]                          # MinMax: rango acotado, sin atipicos
BINARIA = ["reincide"]                         # sin escalar: ya es 0/1

# Orden de concatenacion de la `X` final.
TODAS = NUM + SKILLS + ORDINAL + BINARIA


def ruta_csv(version: str) -> Path:
    """Ruta del CSV de la version pedida."""
    if version not in CSV_POR_VERSION:
        raise ValueError(
            f"version desconocida: {version!r}. Use {sorted(CSV_POR_VERSION)}."
        )
    return PROC / CSV_POR_VERSION[version]


def leer(version: str) -> pd.DataFrame:
    """Carga el dataset de la version pedida.

    `dtype=str` en todo: los codigos ESCO son texto y deben conservar sus ceros a
    la izquierda ('0110' no puede colisionar con '110'). Es la convencion del
    proyecto, no un descuido; los contadores de competencias tambien llegan como
    texto y se convierten con `pd.to_numeric` en `universo_con_competencias()`.
    """
    return pd.read_csv(
        ruta_csv(version), dtype=str, encoding="utf-8",
        keep_default_na=False, na_values=[""],
    )


def fusionar_rescatado(df: pd.DataFrame) -> pd.DataFrame:
    """Completa `occupation_code` con el `matched_code` de las filas rescatadas.

    En la sesion 3, `limpieza` marco como `es_rescatado` las filas a las que se
    les recupero un codigo por prefijo (grupo ISCO de 4 digitos). Esas filas
    llegaron a `empleos_limpio.csv` con `occupation_code` vacio, asi que aqui se
    les reponte el codigo recuperado y dejan de ser 'sin ocupacion'.
    """
    ocup = df["occupation_code"].copy()
    fusion = ocup.isna() & (df["matched_code"] != "unknown")
    ocup.loc[fusion] = df.loc[fusion, "matched_code"]
    return df.assign(occupation_code=ocup)


def to_ordinal(x: pd.Series) -> pd.Series:
    """'Q3 2015' -> ordinal. Devuelve NaN en lo que no matchea el patron."""
    p = x.str.extract(TRIMESTRE_VALIDO.pattern)
    return (pd.to_numeric(p[1], errors="coerce") * 4
            + pd.to_numeric(p[0], errors="coerce"))


def fechas_ordinales(df: pd.DataFrame) -> pd.DataFrame:
    """Anade `start_ord`, `end_ord` y `dur_q` (duracion trimestral)."""
    start_ord = to_ordinal(df["start_date"])
    end_ord = to_ordinal(df["end_date"])
    end_ord = end_ord.mask(df["end_date"] == "Present", TRIMESTRE_CENSURA)
    return df.assign(start_ord=start_ord, end_ord=end_ord, dur_q=end_ord - start_ord)


def educacion_ordinal(df: pd.DataFrame) -> pd.DataFrame:
    """Anade `univ_ord`, la version ordinal de `university_level`."""
    return df.assign(univ_ord=df["university_level"].map(ORDEN_UNIV))


def universo_con_competencias(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Deja el universo de trabajo y devuelve el informe de lo que se perdio.

    Los contadores llegan como texto (ver `leer()`) y hay que convertirlos antes
    de usarlos como numero. Se descartan las filas sin dato de competencias: la
    `X` necesita las columnas y no se puede inventar un 0 (vacio != 0). El
    costo se mide ANTES de descartar, y se devuelve en el `informe` para que el
    cuaderno lo imprima en vez de recalcularlo.

    De `veces_ese_oficio` se derivan DOS columnas porque no son lo mismo: el
    conteo distingue 2 repeticiones de 19, y el binario es estable frente al
    escalador.

    Devuelve TRES cosas, en este orden:

    - `df_antes`  el dataframe previo al recorte. Lo necesita la auditoria de
      Tukey (`diagnostico.tabla_tukey`), que se mide sobre el universo completo y
      no sobre el recortado.
    - `df`        el universo de trabajo.
    - `informe`   lo que se perdio, ya medido.
    """
    for c in CONTADORES:
        df = df.assign(**{c: pd.to_numeric(df[c], errors="coerce")})

    sin_dato = df["n_skills_essential"].isna()
    informe = {
        "n_sin_dato": int(sin_dato.sum()),
        "prop_sin_dato": float(sin_dato.mean()),
        "composicion": df.loc[sin_dato, "emparejado"].value_counts(),
        "ceros": int(df["n_skills_essential"].eq(0).sum()),
        "vacio_exacto": bool(
            (sin_dato == (df["saber_skills"] == "no_clasificado")).all()
        ),
        "filas_antes": len(df),
        "personas_antes": df["resume_id"].nunique(),
    }

    df_antes = df
    df = df.loc[~sin_dato].copy()
    df["reincide"] = (df["veces_ese_oficio"] > 1).astype(np.uint8)
    informe.update(
        filas_despues=len(df),
        personas_despues=df["resume_id"].nunique(),
        oficios=df["occupation_code"].nunique(),
    )
    return df_antes, df, informe


def submuestra(df: pd.DataFrame, rng: np.random.RandomState,
               size: int = SAMPLE_SIZE) -> pd.DataFrame:
    """Submuestra de trabajo, con el indice reiniciado.

    Sin `reset_index`, las Series que el cuaderno guarda de etapas anteriores
    (los descriptivos de Tukey) se alinearian por indice contra este frame y
    saldrian con huecos.
    """
    idx = rng.choice(len(df), size=min(size, len(df)), replace=False)
    return df.iloc[idx].reset_index(drop=True)


def codificar(df_s: pd.DataFrame) -> dict:
    """One-hot de las categoricas + las banderas que si aportan, en 0/1.

    Las banderas ya son one-hot de k-1: no pasan por `get_dummies` ni por
    escalador. Devuelve un dict con las claves `emparejado`, `ocupacion` y
    `banderas`.

    De las tres banderas solo entra `es_vigente`. `es_unknown_ocupacion` y
    `es_rescatado` quedan constante False en este universo, y una columna constante
    no aporta nada a una distancia y falsea cualquier lectura de importancia de
    variables. El razon completo esta en el comentario de `BANDERAS_EN_X`, arriba.

    El `assert` es la parte que importa a futuro. Si alguien cambia la regla del drop
    y esas banderas dejan de ser constantes, el universo de trabajo ya no seria "solo
    filas con oficio conocido" y excluirlas seria una perdida real. El `assert` lo
    dice en el momento en que se rompe, en vez de dejar la `X` con una forma
    distinta a la que todos los documentos y salidas guardadas dan por hecha.
    """
    for c in BANDERAS_EXCLUIDAS:
        valores = sorted(df_s[c].unique())
        assert valores == ["False"], (
            f"{c} deja de ser constante en el universo de trabajo (valores: "
            f"{valores}). Eso significa que el drop de la 2.5 ya no se lleva todas "
            f"las filas sin oficio conocido, asi que {c} SI aporta informacion y "
            f"tiene que entrar en la `X`: agreguela a BANDERAS_EN_X y saque el "
            f"nombre de BANDERAS_EXCLUIDAS. Ademas la forma de la `X` cambia y hay "
            f"que actualizar las cifras citadas en README.md y docs/SKILLS.md."
        )

    dummies_emparejado = pd.get_dummies(
        df_s["emparejado"], prefix="emparejado", dtype=np.uint8)
    dummies_ocupacion = pd.get_dummies(
        df_s["occupation_code"], prefix="occupation", dtype=np.uint8)
    flags = (df_s[BANDERAS_EN_X]
             .replace({"True": 1, "False": 0})
             .astype(np.uint8))
    return {"emparejado": dummies_emparejado,
            "ocupacion": dummies_ocupacion,
            "banderas": flags}


def escalar(df_s: pd.DataFrame) -> dict:
    """Ajusta los tres escaladores, cada uno sobre las columnas que le tocan.

    - `rob` (RobustScaler) para fechas y duracion: tienen cola real, y el robust
      se apoya en la mediana en vez de en los extremos.
    - `mm` (MinMaxScaler) para la educacion: rango acotado, sin atipicos.
    - `rob_sk` (RobustScaler) para los contadores de ESCO. Esta decision NO es por
      outliers como las fechas, es por ESCALA: `n_skills_essential` va de 4 a 99
      y `veces_ese_oficio` de 1 a 19, asi que sin escalarlas su peso en la
      distancia aplasta a `univ_ord`, que va de 0 a 4.

    `reincide` NO se escala: ya es 0/1, y aplicarle un escalador lo achataria sin
    ganar nada.

    El dict trae los ajustadores ya fiteados porque `diagnostico` los vuelve a
    usar con `.transform()` para armar los escenarios de contraste.

    Advertencia: los escaladores se ajustan sobre la SUBCONSULTRA, no sobre el
    dataset completo. Es la decision ya tomada en el cuaderno; queda escrita
    aqui para que no parezca un descuido al leer el modulo suelto.
    """
    rob = RobustScaler()
    numericas = pd.DataFrame(
        rob.fit_transform(df_s[NUM].to_numpy()),
        columns=[f"{c}_rob" for c in NUM], index=df_s.index)

    mm = MinMaxScaler()
    educacion = pd.DataFrame(
        mm.fit_transform(df_s[ORDINAL].to_numpy()),
        columns=["university_mm"], index=df_s.index)

    rob_sk = RobustScaler()
    competencias = pd.DataFrame(
        rob_sk.fit_transform(df_s[CONTADORES].to_numpy()),
        columns=[c + "_rob" for c in CONTADORES], index=df_s.index)

    return {"rob": rob, "mm": mm, "rob_sk": rob_sk,
            "numericas": numericas, "educacion": educacion,
            "competencias": competencias}


def armar_X(escalado: dict, codificado: dict, df_s: pd.DataFrame,
            version: str) -> pd.DataFrame:
    """Concatena las piezas en la `X` final, en el orden de `TODAS` mas las
    dummies y las banderas al final.

    Al final entra una sola bandera, `es_vigente`. Las otras dos del dataset son
    constante False aqui y se excluyen a proposito; el motivo esta en
    `BANDERAS_EN_X`.

    `version` es obligatoria y no tiene valor por defecto a proposito: el numero
    de columnas depende de ella (2.325 en `con_outliers`, 2.326 en
    `sin_outliers`). Un valor por defecto dejaria sin comprobar la mitad de las
    veces sin que nadie lo notara.

    Al final hay comprobaciones de dos clases. Los `assert` de invariante atacan
    bugs: cosas que tienen que ser verdad siempre. El ultimo compara contra la
    cifra citada y su mensaje obliga a corregir README.md y docs/SKILLS.md en el
    mismo commit en que la forma cambia, que es la unica forma de que las cifras
    citadas no queden viejas en silencio (regla B8 de
    docs/BUENAS_PRACTICAS_CODIGO.md).
    """
    X = pd.concat([
        escalado["numericas"],   # start_ord_rob, end_ord_rob, dur_q_rob
        escalado["competencias"],  # n_skills_essential_rob, veces_ese_oficio_rob
        escalado["educacion"],   # university_mm
        df_s[BINARIA],           # 0/1, sin escalar
        codificado["emparejado"],  # emparejado_ok
        codificado["ocupacion"],  # occupation_<codigo>
        codificado["banderas"],   # solo es_vigente (ver BANDERAS_EN_X)
    ], axis=1)

    nulos = int(X.isna().sum().sum())
    assert nulos == 0, (
        f"La `X` tiene {nulos} nulos. El universo de trabajo no debe traer filas "
        f"sin dato de competencias: si las trae, el drop de la 2.5 no se esta "
        f"aplicando. Sin ese drop no hay forma de distinguir un vacio honesto "
        f"(no sabemos el oficio) de un 0 falso (el oficio no exige nada).")

    no_num = X.select_dtypes(exclude=["number"]).shape[1]
    assert no_num == 0, (
        f"La `X` tiene {no_num} columnas no numericas. kNN, k-means y PCA las "
        f"aceptan como categoricas, pero la distancia euclidea no: habria que "
        f"decidir si se codifican o se descartan, no arrastrarlas por error.")

    n_dummies = codificado["ocupacion"].shape[1]
    n_oficios = int(df_s["occupation_code"].nunique())
    assert n_dummies == n_oficios, (
        f"Las dummies de oficios ({n_dummies}) no son una por oficio presente "
        f"({n_oficios}). El one-hot cambio: si ahora dejara una categoria fuera, "
        f"o una fila se quedara en todos 0, la `X` ya no describiria lo mismo "
        f"sin que se note en la forma.")

    assert X.shape[1] == FORMAS_X[version], (
        f"La `X` de {version} paso de {FORMAS_X[version]} a {X.shape[1]} "
        f"columnas. Con este assert, toda cifra citada sobre la `X` acaba de "
        f"quedarse vieja: actualiza README.md y docs/SKILLS.md en este mismo "
        f"commit y solo despues cambia `FORMAS_X`.")

    return X
