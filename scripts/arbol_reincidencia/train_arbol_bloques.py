"""Arboles de decision por bloque de variables · Sesion 7.

Misma y, mismo split y misma comparacion de profundidades para todos los
bloques, de modo que la unica diferencia sea el conjunto de predictores:

    isco   -> gran grupo ISCO (get_dummies)
    nivel  -> nivel educativo ordinal + bandera de no reportado
    skills -> conteos de competencias ESCO del oficio

Objetivo: responder "que bloque separa mejor la reincidencia por oficio" y
dejar las 4 primeras preguntas de cada arbol listas para el informe.

Uso:
    python scripts/arbol_reincidencia/train_arbol_bloques.py --bloque skills
    python scripts/arbol_reincidencia/train_arbol_bloques.py --bloque todos
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "notebooks" / "refactor"))
from lib import categorias  # noqa: E402

DATOS = BASE / "data" / "03_processed" / "empleos_limpio_con_competencias.csv"
SALIDA = BASE / "reports" / "arbol_reincidencia"
FIGURAS = SALIDA / "figuras"
TABLAS = SALIDA / "tablas"
REGLAS = SALIDA / "reglas"

PROFUNDIDADES = [2, 3, 4, 5, 8, None]
PROFUNDIDAD_FINAL = 3  # la misma que el cuaderno, para que las cifras coincidan
SEMILLA = 42
MIN_HOJA = 500  # hojas menores no cuentan para el "lift maximo"

COLS_SKILLS = ["n_skills_essential", "n_skills_competence", "n_skills_knowledge"]

ETIQUETA_NIVEL = {1: "Secundaria", 2: "Bachelor", 3: "Master", 4: "PhD"}

BLOQUES = {
    "isco": "Gran grupo ISCO",
    "nivel": "Nivel educativo",
    "skills": "Competencias ESCO del oficio",
}


# --------------------------------------------------------------------------- #
# Datos
# --------------------------------------------------------------------------- #
def cargar() -> pd.DataFrame:
    """Carga el dataset y deja solo filas con y definida.

    `veces_ese_oficio` es nulo cuando la ocupacion no se pudo estandarizar
    (28.304 filas, 7,5%: las mismas que `saber_skills == 'no_clasificado'`).
    Etiquetarlas como "primera vez" inventaria la respuesta, asi que se excluyen.
    """
    df = pd.read_csv(DATOS)
    df = df.dropna(subset=["veces_ese_oficio"]).copy()
    df["y"] = (df["veces_ese_oficio"] >= 2).astype(int)
    return df


def construir_x(df: pd.DataFrame, bloque: str) -> pd.DataFrame:
    """Devuelve el bloque de predictores pedido."""
    if bloque == "isco":
        return pd.get_dummies(categorias.isco_mayor(df), prefix="isco", dtype=int)

    if bloque == "nivel":
        nivel = categorias.nivel_ordinal(df)
        return pd.DataFrame(
            {
                "nivel_ordinal": pd.Series(
                    nivel.to_numpy(dtype="float64", na_value=np.nan), index=df.index
                ),
                "nivel_no_reportado": categorias.nivel_no_reportado(df).astype(int),
            },
            index=df.index,
        )

    if bloque == "skills":
        return df[COLS_SKILLS].astype("float64")

    raise ValueError(f"Bloque desconocido: {bloque}")


# --------------------------------------------------------------------------- #
# Evaluacion
# --------------------------------------------------------------------------- #
def metricas(nombre: str, y_true: pd.Series, y_pred: np.ndarray, arbol=None) -> dict:
    fila = {
        "modelo": nombre,
        "accuracy": accuracy_score(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "recall_clase1": recall_score(y_true, y_pred, zero_division=0),
        "f1_clase1": f1_score(y_true, y_pred, zero_division=0),
    }
    if arbol is not None:
        t = arbol.tree_
        hojas = np.where(t.children_left == -1)[0]
        valor = t.value[hojas, 0, :]
        total = valor.sum(axis=1)
        tasa = np.divide(valor[:, 1], total, out=np.zeros_like(total), where=total > 0)
        grandes = t.n_node_samples[hojas] >= MIN_HOJA
        fila["n_hojas"] = len(hojas)
        fila["hojas_clase1"] = int((valor.argmax(axis=1) == 1).sum())
        fila["tasa_hoja_max"] = float(tasa[grandes].max()) if grandes.any() else np.nan
        fila["lift_max"] = fila["tasa_hoja_max"] / float(y_true.mean())
    return fila


def comparar_profundidades(X_train, y_train, X_test, y_test) -> pd.DataFrame:
    filas = []
    for d in PROFUNDIDADES:
        clf = DecisionTreeClassifier(max_depth=d, random_state=SEMILLA)
        clf.fit(X_train, y_train)
        filas.append(
            {
                "max_depth": str(d),
                "train_acc": clf.score(X_train, y_train),
                "test_acc": clf.score(X_test, y_test),
                "n_hojas": clf.get_n_leaves(),
                "brecha_train_test": clf.score(X_train, y_train) - clf.score(X_test, y_test),
            }
        )
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------- #
# Las 4 primeras preguntas
# --------------------------------------------------------------------------- #
def texto_pregunta(columna: str, umbral: float) -> tuple[str, str]:
    """Traduce un split del arbol a lenguaje de negocio."""
    if columna.startswith("isco_"):
        grupo = columna.split("_")[-1]
        return (
            f"¿Pertenece al grupo ISCO {grupo}?",
            f"{columna} > 0.5",
        )
    if columna == "nivel_ordinal":
        nivel = int(np.floor(umbral))
        etiqueta = ETIQUETA_NIVEL.get(nivel, "?")
        return (
            f"¿Nivel educativo hasta {etiqueta} (nivel {nivel})?",
            f"{columna} <= {umbral:.1f}",
        )
    if columna == "nivel_no_reportado":
        return ("¿El nivel educativo no fue reportado?", f"{columna} > 0.5")
    return (f"¿{columna} <= {umbral:.1f}?", f"{columna} <= {umbral:.1f}")


def primeras_preguntas(arbol, X_train, y_train, top: int = 4) -> pd.DataFrame:
    """Recorre el arbol en el mismo orden que `export_text` y describe los splits.

    Usa `decision_path` en lugar de repetir la comparacion `<= umbral`: sklearn
    puede enviar los valores nulos (`NaN`) a la rama izquierda, y una
    comparacion manual los mandaria a la derecha, falseando los tamanos.
    """
    t = arbol.tree_
    nombres = list(X_train.columns)
    camino = arbol.decision_path(X_train).toarray().astype(bool)
    base = float(y_train.mean())
    y = y_train.to_numpy()

    filas: list[dict] = []
    pila = [(0, 0)]
    while pila and len(filas) < top:
        nodo, prof = pila.pop()
        if t.feature[nodo] < 0:
            continue

        columna = nombres[t.feature[nodo]]
        umbral = float(t.threshold[nodo])
        nodo_izq, nodo_der = t.children_left[nodo], t.children_right[nodo]
        izq = camino[:, nodo_izq]
        der = camino[:, nodo_der]

        pregunta, regla = texto_pregunta(columna, umbral)
        n_izq, n_der = int(izq.sum()), int(der.sum())
        tasa_izq = float(y[izq].mean()) if n_izq else np.nan
        tasa_der = float(y[der].mean()) if n_der else np.nan

        filas.append(
            {
                "#": len(filas) + 1,
                "pregunta": pregunta,
                "regla": regla,
                "profundidad": prof,
                "n_nodo": int(camino[:, nodo].sum()),
                "tasa_nodo": float(y[camino[:, nodo]].mean()),
                "n_izq": n_izq,
                "tasa_izq": tasa_izq,
                "n_der": n_der,
                "tasa_der": tasa_der,
                "lift_izq": tasa_izq / base,
                "lift_der": tasa_der / base,
                "delta_pp_izq": 100 * (tasa_izq - base),
                "delta_pp_der": 100 * (tasa_der - base),
            }
        )

        pila.append((t.children_right[nodo], prof + 1))
        pila.append((t.children_left[nodo], prof + 1))

    tabla = pd.DataFrame(filas)
    for c in ["tasa_nodo", "tasa_izq", "tasa_der"]:
        tabla[c] = (100 * tabla[c]).round(2)
    for c in ["lift_izq", "lift_der"]:
        tabla[c] = tabla[c].round(3)
    for c in ["delta_pp_izq", "delta_pp_der"]:
        tabla[c] = tabla[c].round(2)
    return tabla


# --------------------------------------------------------------------------- #
# Un bloque completo
# --------------------------------------------------------------------------- #
def entrenar_bloque(df: pd.DataFrame, bloque: str) -> dict:
    X = construir_x(df, bloque)
    y = df["y"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=SEMILLA, stratify=y
    )

    for carpeta in (FIGURAS, TABLAS, REGLAS):
        carpeta.mkdir(parents=True, exist_ok=True)
    destino = TABLAS

    dummy = DummyClassifier(strategy="most_frequent").fit(X_train, y_train)
    tabla_metricas = [
        metricas("baseline (most_frequent)", y_test, dummy.predict(X_test)),
    ]

    tabla_prof = comparar_profundidades(X_train, y_train, X_test, y_test)
    tabla_prof.to_csv(destino / f"{bloque}_profundidades.csv", index=False)

    arbol = DecisionTreeClassifier(max_depth=PROFUNDIDAD_FINAL, random_state=SEMILLA)
    arbol.fit(X_train, y_train)
    tabla_metricas.append(metricas(f"arbol depth={PROFUNDIDAD_FINAL}", y_test, arbol.predict(X_test), arbol))
    metricas_df = pd.DataFrame(tabla_metricas).round(4)
    metricas_df.to_csv(destino / f"{bloque}_metricas.csv", index=False)

    importancias = (
        pd.DataFrame({"feature": X.columns, "importance": arbol.feature_importances_})
        .sort_values("importance", ascending=False)
        .round(6)
    )
    importancias.to_csv(destino / f"{bloque}_importancias.csv", index=False)

    reglas = export_text(arbol, feature_names=list(X.columns), decimals=2)
    (REGLAS / f"{bloque}_export.txt").write_text(reglas, encoding="utf-8")

    preguntas = primeras_preguntas(arbol, X_train, y_train)
    preguntas.to_csv(destino / f"{bloque}_preguntas.csv", index=False)

    fig, ax = plt.subplots(figsize=(max(14, 2.0 * arbol.get_n_leaves()), 10))
    plot_tree(
        arbol,
        feature_names=list(X.columns),
        class_names=["Primera vez", "Reincide"],
        filled=True,
        rounded=True,
        proportion=True,
        fontsize=9,
        ax=ax,
    )
    fig.tight_layout()
    fig.savefig(FIGURAS / f"arbol_{bloque}.png", dpi=150)
    plt.close(fig)

    return {
        "bloque": bloque,
        "n": len(df),
        "predictores": list(X.columns),
        "metricas": metricas_df,
        "profundidades": tabla_prof,
        "importancias": importancias,
        "preguntas": preguntas,
        "reglas": reglas,
        "destino": destino,
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(description="Arboles por bloque de variables")
    parser.add_argument("--bloque", default="skills", choices=[*BLOQUES, "todos"])
    args = parser.parse_args()

    df = cargar()
    base = float(df["y"].mean())
    print(f"Filas: {len(df)} | reincidencia: {base:.2%}")

    elegidos = list(BLOQUES) if args.bloque == "todos" else [args.bloque]
    resumen = []
    for bloque in elegidos:
        print(f"\n=== {bloque} · {BLOQUES[bloque]} ===")
        r = entrenar_bloque(df, bloque)
        print(r["metricas"].to_string(index=False))
        print("\nProfundidades:")
        print(r["profundidades"].round(4).to_string(index=False))
        print("\nImportancias:")
        print(r["importancias"].to_string(index=False))
        print("\n4 primeras preguntas:")
        print(r["preguntas"].drop(columns=["regla"]).to_string(index=False))
        print("\nReglas:")
        print(r["reglas"])
        resumen.append(
            {
                "bloque": bloque,
                "accuracy": r["metricas"].iloc[-1]["accuracy"],
                "f1_clase1": r["metricas"].iloc[-1]["f1_clase1"],
                "recall_clase1": r["metricas"].iloc[-1]["recall_clase1"],
                "n_hojas": r["metricas"].iloc[-1]["n_hojas"],
                "hojas_clase1": r["metricas"].iloc[-1]["hojas_clase1"],
                "tasa_hoja_max": r["metricas"].iloc[-1]["tasa_hoja_max"],
                "lift_max": r["metricas"].iloc[-1]["lift_max"],
                "predictores": ", ".join(r["predictores"]),
            }
        )

    comparacion = pd.DataFrame(resumen).round(4)
    TABLAS.mkdir(parents=True, exist_ok=True)
    ruta = TABLAS / "comparacion_bloques.csv"
    if ruta.exists():
        previo = pd.read_csv(ruta)
        comparacion = (
            pd.concat([previo, comparacion], ignore_index=True)
            .drop_duplicates(subset=["bloque"], keep="last")
            .sort_values("bloque")
        )
    comparacion.to_csv(ruta, index=False)
    print("\n=== Comparacion de bloques ===")
    print(comparacion.to_string(index=False))


if __name__ == "__main__":
    main()
