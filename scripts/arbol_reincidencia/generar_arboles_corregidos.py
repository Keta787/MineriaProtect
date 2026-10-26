"""Entrena y grafica los tres árboles corregidos de la Sesión 7.

El flujo separa segmentación descriptiva de clasificación operativa:
- usa particiones por persona para evitar compartir trayectorias entre train/test;
- conserva una categoría explícita para niveles educativos no reportados;
- aplica ``class_weight='balanced'``;
- selecciona el umbral sobre validación mediante F1 de la clase 1;
- audita las competencias como variables derivadas de la ocupación.

Los artefactos se escriben en ``reports/arbol_reincidencia_corregido`` y no
reemplazan los PNG históricos.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "notebooks" / "refactor"))
from lib import categorias
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "03_processed" / "empleos_con_competencias_limpio.csv"
OUT = ROOT / "reports" / "arbol_reincidencia_corregido"
FIGURES = OUT / "figuras"
RULES = OUT / "reglas"
TABLES = OUT / "tablas"

RANDOM_STATE = 42
TEST_SIZE = 0.25
VALIDATION_SIZE = 0.25
MAX_DEPTH = 3


def _split_by_person(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Devuelve índices disjuntos de ajuste, validación y prueba."""
    groups = df["resume_id"].astype("string")
    first = GroupShuffleSplit(
        n_splits=1, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    train_valid, test = next(first.split(df, groups=groups))
    second = GroupShuffleSplit(
        n_splits=1, test_size=VALIDATION_SIZE, random_state=RANDOM_STATE
    )
    train, validation = next(
        second.split(df.iloc[train_valid], groups=groups.iloc[train_valid])
    )
    return train_valid[train], train_valid[validation], test


def _prepare_features(
    df: pd.DataFrame, train_idx: np.ndarray
) -> dict[str, pd.DataFrame]:
    """Construye X por árbol sin convertir los faltantes educativos en nivel cero."""
    isco = categorias.isco_mayor(df).astype("string").fillna("No reportado")
    x_isco = pd.get_dummies(isco, prefix="isco_mayor", dtype=float)

    nivel = categorias.nivel_ordinal(df).astype("float64")
    x_nivel = pd.DataFrame(
        {
            "nivel_ordinal": nivel,
            "nivel_no_reportado": nivel.isna().astype(float),
        },
        index=df.index,
    )
    nivel_mediana = x_nivel.iloc[train_idx]["nivel_ordinal"].median()
    x_nivel["nivel_ordinal"] = x_nivel["nivel_ordinal"].fillna(nivel_mediana)

    competencias = pd.to_numeric(df["n_skills_competence"], errors="coerce")
    x_competencias = pd.DataFrame(
        {
            "n_skills_competence": competencias,
            "skills_no_reportadas": competencias.isna().astype(float),
        },
        index=df.index,
    )
    competencia_mediana = x_competencias.iloc[train_idx][
        "n_skills_competence"
    ].median()
    x_competencias["n_skills_competence"] = x_competencias[
        "n_skills_competence"
    ].fillna(competencia_mediana)
    return {
        "isco": x_isco,
        "nivel_educativo": x_nivel,
        "competencias_ESCO": x_competencias,
    }


def _threshold(y_true: pd.Series, probabilities: np.ndarray) -> tuple[float, float]:
    """Selecciona el umbral con mejor F1 en validación, sin tocar el test."""
    candidates = np.linspace(0.10, 0.90, 81)
    scores = [
        f1_score(y_true, probabilities >= threshold, zero_division=0)
        for threshold in candidates
    ]
    best = int(np.argmax(scores))
    return float(candidates[best]), float(scores[best])


def _plot_tree(
    model: DecisionTreeClassifier,
    features: pd.DataFrame,
    title: str,
    path: Path,
) -> None:
    width = max(18, 5 * model.get_n_leaves())
    plt.figure(figsize=(width, 12))
    plot_tree(
        model,
        feature_names=list(features.columns),
        class_names=["Primera vez", "Reincide"],
        filled=True,
        rounded=True,
        proportion=True,
        impurity=True,
        precision=3,
    )
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()


def main() -> None:
    if not DATA.exists():
        raise FileNotFoundError(
            f"No existe {DATA}. Ejecuta primero el pipeline de preparación "
            "descrito en README.md, sección 'Cómo ejecutar'."
        )

    df = pd.read_csv(DATA)
    required = {
        "resume_id",
        "veces_ese_oficio",
        "isco_group",
        "university_level",
        "n_skills_competence",
        "occupation_code",
    }
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {missing}")

    y = (pd.to_numeric(df["veces_ese_oficio"], errors="coerce") >= 2).astype(int)
    train_idx, validation_idx, test_idx = _split_by_person(df)
    features = _prepare_features(df, train_idx)

    FIGURES.mkdir(parents=True, exist_ok=True)
    RULES.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    leakage_rows: list[dict[str, object]] = []
    for name, x in features.items():
        model = DecisionTreeClassifier(
            max_depth=MAX_DEPTH,
            class_weight="balanced",
            criterion="gini",
            min_samples_leaf=100,
            random_state=RANDOM_STATE,
        )
        model.fit(x.iloc[train_idx], y.iloc[train_idx])
        validation_proba = model.predict_proba(x.iloc[validation_idx])[:, 1]
        threshold, validation_f1 = _threshold(
            y.iloc[validation_idx], validation_proba
        )
        test_proba = model.predict_proba(x.iloc[test_idx])[:, 1]
        test_pred = test_proba >= threshold
        y_test = y.iloc[test_idx]

        rows.append(
            {
                "modelo": name,
                "n_train": len(train_idx),
                "n_validation": len(validation_idx),
                "n_test": len(test_idx),
                "threshold_validacion": threshold,
                "f1_validacion": validation_f1,
                "accuracy_test": accuracy_score(y_test, test_pred),
                "precision_test_clase_1": precision_score(
                    y_test, test_pred, zero_division=0
                ),
                "recall_test_clase_1": recall_score(
                    y_test, test_pred, zero_division=0
                ),
                "f1_test_clase_1": f1_score(y_test, test_pred, zero_division=0),
                "pr_auc_test": average_precision_score(y_test, test_proba),
                "n_leaves": model.get_n_leaves(),
                "min_samples_leaf": 100,
            }
        )

        prefix = f"arbol_{name}"
        _plot_tree(
            model,
            x,
            f"Árbol corregido: {name} | max_depth={MAX_DEPTH}, "
            f"class_weight=balanced, threshold={threshold:.2f}",
            FIGURES / f"{prefix}.png",
        )
        (RULES / f"{prefix}.txt").write_text(
            export_text(model, feature_names=list(x.columns)),
            encoding="utf-8",
        )
        (TABLES / f"{prefix}_matriz_confusion.csv").write_text(
            pd.DataFrame(
                confusion_matrix(y_test, test_pred),
                index=["real_0", "real_1"],
                columns=["pred_0", "pred_1"],
            ).to_csv(),
            encoding="utf-8",
        )

        if name == "competencias_ESCO":
            occupation = df["occupation_code"].astype("string")
            feature = x["n_skills_competence"]
            distinct_by_occupation = (
                pd.DataFrame(
                    {
                        "occupation_code": occupation,
                        "n_skills_competence": feature,
                    }
                )
                .dropna(subset=["occupation_code", "n_skills_competence"])
                .groupby("occupation_code")["n_skills_competence"]
                .nunique()
            )
            leakage_rows.append(
                {
                    "diagnostico": "competencias_derivadas_de_occupation_code",
                    "occupation_codes": int(occupation.nunique(dropna=True)),
                    "filas_con_occupation_code": int(occupation.notna().sum()),
                    "competence_values": int(feature.nunique(dropna=True)),
                    "occupation_codes_with_multiple_competence_values": int(
                        (distinct_by_occupation > 1).sum()
                    ),
                    "nota": (
                        "Las competencias ESCO se atribuyen al cargo; auditar "
                        "procedencia antes de desplegar."
                    ),
                }
            )

    pd.DataFrame(rows).to_csv(TABLES / "metricas_arboles_corregidos.csv", index=False)
    pd.DataFrame(leakage_rows).to_csv(
        TABLES / "auditoria_leakage_competencias.csv", index=False
    )
    (OUT / "configuracion.json").write_text(
        json.dumps(
            {
                "max_depth": MAX_DEPTH,
                "class_weight": "balanced",
                "criterion": "gini",
                "min_samples_leaf": 100,
                "split": "GroupShuffleSplit por resume_id",
                "threshold": "mejor F1 en validacion",
                "clase_positiva": "veces_ese_oficio >= 2",
                "data": str(DATA.relative_to(ROOT)),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(pd.DataFrame(rows).to_string(index=False))
    print(f"PNG generados en: {FIGURES}")


if __name__ == "__main__":
    main()
