"""Auditorias que justifican las decisiones de la fase de Transformacion.

Companero de `transformacion.py`: este modulo NO produce la `X`, produce las
medidas que sostienen por que la `X` es como es. Todo lo que aqui vive salio de
`notebooks/4.0_transformacion.ipynb` y `4.1_transformacion_sin_outliers.ipynb`.

Las auditorias responden, en orden:

- `comprobaciones_cruce()`   el cruce con ESCO es 1:1 y las banderas cuadran.
- `revisar_isco()`           `isco_level` es ~constante, asi que se descarta.
- `segmentos_cuantiles()`    las fechas se pueden discretizar en 5 cuartiles
  (exploracion: esos segmentos NO entran a la `X` final, ver `PCA`).
- `bloque_onehot_completo()` cuanto pesa la codificacion sparse frente a la densa.
- `tabla_tukey()`            IQR y proporcion de atipicos de cada variable.
- `comparar_escaladores()`   los tres escaladores sobre `dur_q`, lado a lado.
- `escenarios_distancia()`   cuanto aporta cada columna a la distancia euclidea.
  Es la justificacion central de la seccion de escalado: KNN y K-means eligen
  vecinos por distancia, y como la distancia suma diferencias al cuadrado, la
  columna con mas unidades secuestra la metrica.
- `auditoria_pca()`          el PCA como diagnostico (casi no comprime, asi que no
  se aplica a la `X` final).

Igual que en `transformacion.py`: ninguna funcion imprime, todas devuelven los
datos para que los formatee el cuaderno.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import (KBinsDiscretizer, MinMaxScaler,
                                   OneHotEncoder, RobustScaler, StandardScaler)

import transformacion as T

# Columnas numericas que entran a la auditoria de PCA. `reincide` NO entra por la
# misma razon que las dummies: es un indicador categorico, no una dimension
# continua. Nota que `dur_q = end_ord - start_ord` hace que las tres primeras
# guarden una relacion lineal casi exacta (de ahi el componente con varianza 0).
# El nombre NO puede ser `PCA`: ese lo ocupa la clase de sklearn.
NUM_PCA = T.NUM + T.ORDINAL + T.SKILLS

COLUMNAS_TUKEY = ["variable", "Q1", "Q3", "IQR", "lim_inf", "lim_sup",
                  "outliers", "prop_outliers"]


def comprobaciones_cruce(df: pd.DataFrame) -> dict:
    """Verifica que el cruce con ESCO sea 1:1 y que las banderas sean coherentes.

    `max_etiquetas_por_codigo == 1` y `max_etiquetas_por_grupo == 1` son la
    garantia de que un codigo no este hablando de dos ocupaciones distintas: si
    un dia sale >1, la tabla de competencias quedaria mal atribuida.
    """
    ok = df[df["emparejado"] == "ok"]
    g = df.dropna(subset=["occupation_code", "occupation_label"])
    g2 = df.dropna(subset=["isco_group", "isco_group_label"])
    return {
        "code_coincide": round(
            float((ok["matched_code"] == ok["occupation_code"]).mean()), 4),
        "max_etiquetas_por_codigo": int(
            g.groupby("occupation_code")["occupation_label"].nunique().max()),
        "max_etiquetas_por_grupo": int(
            g2.groupby("isco_group")["isco_group_label"].nunique().max()),
        "isco_level_valores": df["isco_level"].dropna().unique().tolist(),
        "isco_nan_coincide": int(
            (df["isco_level"].isna()
             == (df["es_unknown_ocupacion"] == "True")).all()),
        "matched_unknown": df.loc[
            df["emparejado"] == "unknown", "matched_code"].unique()[:3],
        "matched_rescatado": df.loc[
            df["emparejado"] == "rescatado", "matched_code"].dropna().unique()[:3],
    }


def revisar_isco(df: pd.DataFrame) -> tuple[pd.Series, float]:
    """Cuenta `isco_level` y devuelve la proporcion de filas con nivel 4.

    Si el nivel 4 es practicamente todo, la columna no aporta: es ~constante y
    ademas ya esta resumida en `isco_group`.
    """
    tabla = df["isco_level"].fillna("NaN").value_counts()
    return tabla, tabla.get("4", 0) / len(df)


def segmentos_cuantiles(df: pd.DataFrame, n_bins: int = 5) -> dict:
    """Discretiza `start_ord` y `end_ord` en `n_bins` segmentos por cuartil.

    Exploracion, no parte de la `X`: los bordes y el conteo por segmento sirven
    para ver que la tenure se reparte de forma pareja. Devuelve las claves
    `bordes_inicio`, `bordes_fin` y `conteo_inicio`.

    `subsample=None` es obligatorio y no es cosmetico. `KBinsDiscretizer` trae
    `subsample=200_000` por defecto: si hay mas filas que eso, ajusta los bordes
    sobre una submuestra **con reemplazo**, y como su `random_state` por defecto
    es `None`, esa submuestra cambia en cada ejecucion. Con 376.567 filas el
    primer y el ultimo borde salian distintos en cada corrida, y nunca
    coincidian con el minimo ni con el maximo reales de la columna. Sin la
    semilla, la salida no era reproducible (regla D5 del proyecto).
    Con `subsample=None` se usan todas las filas: los bordes son los cuantiles
    exactos, el primero es el minimo real y el ultimo el maximo real, y el
    resultado es estable sin necesitar semilla.
    """
    kbd_inicio = KBinsDiscretizer(n_bins=n_bins, encode="ordinal",
                                  strategy="quantile", subsample=None)
    kbd_fin = KBinsDiscretizer(n_bins=n_bins, encode="ordinal",
                               strategy="quantile", subsample=None)
    bins_inicio = kbd_inicio.fit_transform(df["start_ord"].to_frame()).ravel()
    kbd_fin.fit_transform(df["end_ord"].to_frame())
    return {
        "bordes_inicio": kbd_inicio.bin_edges_[0],
        "bordes_fin": kbd_fin.bin_edges_[0],
        "conteo_inicio": pd.Series(bins_inicio).value_counts().sort_index(),
    }


def bloque_onehot_completo(df: pd.DataFrame) -> tuple[tuple[int, ...], int]:
    """Forma y peso en memoria del bloque one-hot sobre el dataset completo.

    Es la justificacion de la submuestra: si el bloque sparse ya pesa mucho en el
    dataset entero, la version densa de la `X` completa no es viable en memoria.
    """
    ohe = OneHotEncoder(sparse_output=True, handle_unknown="ignore")
    X_ohe_full = ohe.fit_transform(df[["emparejado", "occupation_code"]])
    return X_ohe_full.shape, X_ohe_full.data.nbytes


def tukey(s: pd.Series) -> tuple:
    """Cuartiles, limites del cerco y numero de atipicos de una variable."""
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    li, ls = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return q1, q3, iqr, li, ls, int(((s < li) | (s > ls)).sum())


def tabla_tukey(df_antes: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """IQR y proporcion de atipicos de las variables transformadas.

    `dur_q` aparece dos veces a proposito: censurado (los vigentes quedan en NaN,
    que es como lo dejo la sesion 3) y ubicado en Q1 2026. La diferencia entre las
    dos filas es el costo de tratar la censura como si tuviera fecha de fin.

    El denominador de la proporcion es el del propio universo medido
    (`var.dropna()`), no `len(df)`: para `dur_q` censurado son filas distintas,
    porque las experiencias vigentes quedan en NaN. Dividir por `len(df)`
    subestimaba la proporcion en alrededor de un 5 %.

    **La funcion mide sobre dos universos distintos, y es a proposito.** Las
    cuatro primeras filas se miden sobre `df_antes`, el dataframe previo al
    recorte por falta de dato de competencias; la quinta (la `dur_q` censurada)
    se mide sobre `df`, el dataframe ya recortado. Es como la midio el cuaderno
    desde que existe, y se conserva tal cual para que las cifras publicadas no
    se muevan. Lo que la tabla afirma es "de estos datos, cuantos se salen del
    cerco", y "de estos datos" es el universo completo para unas filas y el
    recortado para otra.

    Corregirlo (medir las cinco sobre el mismo universo) cambia los conteos de
    atipicos de las cuatro primeras filas y obliga a corregir el markdown que los
    cita. Es un cambio de fondo, no un refactor: toca las cifras del entregable
    y conviene hacerlo solo, con su justificacion.
    """
    dur_q_censurado = T.to_ordinal(df["end_date"]) - df["start_ord"]

    filas = []
    for nombre, var in [("start_ord", df_antes["start_ord"]),
                        ("end_ord", df_antes["end_ord"]),
                        ("dur_q (Present censurado)", dur_q_censurado),
                        ("dur_q (Present = Q1 2026)", df_antes["dur_q"]),
                        ("university_map", df_antes["univ_ord"])]:
        var = var.dropna()
        q1, q3, iqr, li, ls, out = tukey(var)
        filas.append([nombre, round(q1, 1), round(q3, 1), round(iqr, 1),
                      round(li, 1), round(ls, 1), out, round(out / len(var), 3)])
    return pd.DataFrame(filas, columns=COLUMNAS_TUKEY)


def comparar_escaladores(df_s: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Los tres escaladores sobre `dur_q`, lado a lado, para las primeras `n` filas.

    El robust mantiene la estructura de la distribucion; el minmax y el standard
    quedan a merced de los extremos.
    """
    durq_demo = df_s["dur_q"].to_numpy().reshape(-1, 1).astype(float)
    return pd.DataFrame({
        "crudo": durq_demo[:n, 0],
        "minmax": MinMaxScaler().fit_transform(durq_demo)[:n, 0],
        "standard": StandardScaler().fit_transform(durq_demo)[:n, 0],
        "robust": RobustScaler().fit_transform(durq_demo)[:n, 0],
    })


def aporte_porcentual(Z: np.ndarray, pares: np.ndarray) -> np.ndarray:
    """% que aporta cada columna a la distancia euclidea, promedio de los pares.

    Como la distancia suma diferencias al cuadrado, el aporte de cada columna es
    proporcional a la suma de sus diferencias al cuadrado.
    """
    dif = (Z[pares[:, 0]] - Z[pares[:, 1]]) ** 2
    return 100 * dif.sum(axis=0) / dif.sum()


def parejas_aleatorias(n_filas: int, n_pares: int = T.N_PARES,
                       seed: int = T.SEED_DIST) -> np.ndarray:
    """Parejas de filas para medir el aporte a la distancia.

    El generador es propio y sembrado aparte del de la submuestra: es una
    muestra distinta y no debe competir por el estado de la misma semilla.
    """
    return np.random.RandomState(seed).randint(0, n_filas, size=(n_pares, 2))


def escenarios_distancia(df_s: pd.DataFrame, escalado: dict) -> dict:
    """Las cinco matrices contra las que se mide el aporte de cada columna.

    La ultima es la mezcla que sale a produccion: los tres escaladores ya
    fiteados, cada uno sobre sus columnas. Se pasan los ajustadores (no las
    matrices) porque asi se ve que el bloque de produccion es el mismo ajuste,
    no un cuarto escalador mas.
    """
    return {
        "CRUCO (sin escalar)": df_s[T.TODAS].to_numpy(float),
        "StandardScaler": StandardScaler().fit_transform(df_s[T.TODAS]),
        "MinMaxScaler": MinMaxScaler().fit_transform(df_s[T.TODAS]),
        "RobustScaler": RobustScaler().fit_transform(df_s[T.TODAS]),
        "PRODUCCION (rob+mm)": np.hstack([
            escalado["rob"].transform(df_s[T.NUM].to_numpy()),
            escalado["rob_sk"].transform(df_s[T.SKILLS].to_numpy()),
            escalado["mm"].transform(df_s[T.ORDINAL].to_numpy()),
            df_s[T.BINARIA].to_numpy(float),
        ]),
    }


def tabla_aporte(escenarios: dict, pares: np.ndarray) -> pd.DataFrame:
    """Aporte a la distancia por columna y por escenario, con una fila cada uno."""
    tabla = pd.DataFrame(
        {nombre: aporte_porcentual(Z, pares) for nombre, Z in escenarios.items()},
        index=T.TODAS,
    ).T.round(2)
    tabla.columns = T.TODAS
    return tabla


def pareja_ilustrativa(df_s: pd.DataFrame) -> tuple[int, int]:
    """Dos filas del mismo nivel educativo con las duraciones mas opuestas.

    Es el caso concreto que hace tangible la tabla de aporte: mismo nivel, y a
    pesar de eso la distancia cruda las separa casi por completo.
    """
    nivel, dur = df_s["univ_ord"].to_numpy(), df_s["dur_q"].to_numpy()
    mejor = None
    for n in np.unique(nivel):
        pos = np.flatnonzero(nivel == n)
        if len(pos) < 2:
            continue
        d = dur[pos]
        cand = (d.max() - d.min(), pos[np.argmax(d)], pos[np.argmin(d)])
        if mejor is None or cand[0] > mejor[0]:
            mejor = cand
    return mejor[1], mejor[2]


def auditoria_pca(df_s: pd.DataFrame, rng: np.random.RandomState) -> dict:
    """PCA sobre las numericas estandarizadas, como diagnostico.

    `rng` es el MISMO `RandomState` que uso `transformacion.submuestra()`: se
    consume en orden, y pasarlo aparte garantiza que el PCA ve el estado que
    tendria en la corrida completa, no uno recien sembrado.

    No se aplica a la `X` final: con 6 numericas y `dur_q` linealmente
    dependiente de las otras dos, el PCA casi no comprime (componente 6 con
    varianza ~0). Se documenta como tal en vez de descartar la matriz.
    """
    X_num = df_s[NUM_PCA].astype(float)
    Xp_std = StandardScaler().fit_transform(X_num)
    pca = PCA(random_state=rng).fit(Xp_std)
    var_ac = np.cumsum(pca.explained_variance_ratio_)
    k = X_num.shape[1]
    varianza = pd.DataFrame({
        "varianza_individual": np.round(pca.explained_variance_ratio_[:k], 4),
        "varianza_acumulada": np.round(var_ac[:k], 4),
    }, index=pd.RangeIndex(1, k + 1, name="componente"))
    return {
        "X_num": X_num,
        "correlacion": X_num.corr(),
        "varianza": varianza,
        "k": k,
        "n_para_80": int((var_ac < 0.80).sum()) + 1,
    }
