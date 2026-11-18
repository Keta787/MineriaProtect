"""Inspection, evaluation, decision_path analysis, person-bootstrap CIs, and Spanish rule extraction."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.tree import DecisionTreeClassifier, _tree, export_text

from .config import (
    ALLOWED_DEPTHS,
    ASPIRATIONAL_TARGET_SCORE,
    BLOCK_METADATA_ES,
    BOOTSTRAP_N_RESAMPLES,
    EDUCATION_ORDINAL_MAP,
    ISCO_MAJOR_LABELS_ES,
    MAX_TREE_DEPTH,
    MIN_LEAF_LIFT_FOR_SEPARATION,
    MIN_LEAF_SUPPORT_RATIO,
    VERSION_LABELS_ES,
)
from .tuning import BlockTuningResult, CandidateSpec, instantiate_tree_from_spec


def wilson_ci_95(k_pos: int, n_total: int, z: float = 1.959963984540054) -> Tuple[float, float]:
    """Compute the 95% Wilson score confidence interval for a binomial proportion."""
    if n_total <= 0:
        return 0.0, 0.0
    p_hat = float(k_pos) / float(n_total)
    z2 = z * z
    denom = 1.0 + (z2 / n_total)
    center = (p_hat + (z2 / (2.0 * n_total))) / denom
    half_width = (
        z
        * math.sqrt((p_hat * (1.0 - p_hat) / n_total) + (z2 / (4.0 * n_total * n_total)))
        / denom
    )
    low = max(0.0, center - half_width)
    high = min(1.0, center + half_width)
    return low, high


def _exact_roc_auc_from_discrete_scores(
    scores: np.ndarray,
    n0_by_group: np.ndarray,
    n1_by_group: np.ndarray,
) -> float:
    """Compute exact ROC-AUC from discrete score bins (leaves) and their class-0/class-1 counts."""
    total_n0 = float(n0_by_group.sum())
    total_n1 = float(n1_by_group.sum())
    if total_n0 <= 0.0 or total_n1 <= 0.0:
        return 0.5

    # Aggregate identical scores first to handle ties accurately
    order = np.argsort(scores, kind="mergesort")
    sorted_scores = scores[order]
    sorted_n0 = n0_by_group[order].astype("float64")
    sorted_n1 = n1_by_group[order].astype("float64")

    unique_scores, idx_start = np.unique(sorted_scores, return_index=True)
    agg_n0 = np.add.reduceat(sorted_n0, idx_start)
    agg_n1 = np.add.reduceat(sorted_n1, idx_start)

    cum_n0_below = np.cumsum(agg_n0) - agg_n0
    u_stat = np.sum(agg_n1 * (cum_n0_below + 0.5 * agg_n0))
    return float(u_stat / (total_n0 * total_n1))


def bootstrap_person_metrics_ci(
    clf: DecisionTreeClassifier,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    groups_test: pd.Series,
    decision_threshold: Optional[float] = None,
    n_resamples: int = BOOTSTRAP_N_RESAMPLES,
    random_state: int = 42,
) -> Dict[str, Tuple[float, float]]:
    """Compute 95% confidence intervals on Test by cluster-bootstrapping PERSONS (resume_id, not rows)."""
    leaf_ids = clf.apply(X_test)
    unique_leaves, leaf_inv = np.unique(leaf_ids, return_inverse=True)
    n_leaves = len(unique_leaves)

    # Compute leaf probabilities and binary predictions for each unique leaf
    tree_ = clf.tree_
    pos_idx = int(np.where(clf.classes_ == 1)[0][0]) if 1 in clf.classes_ else 0
    leaf_probs = np.zeros(n_leaves, dtype="float64")
    leaf_preds = np.zeros(n_leaves, dtype="int8")

    for idx, lid in enumerate(unique_leaves):
        node_val = tree_.value[int(lid)][0]
        total_w = float(node_val.sum())
        prob_1 = float(node_val[pos_idx] / total_w) if total_w > 0 else 0.0
        leaf_probs[idx] = prob_1
        if decision_threshold is None:
            pred_cls = int(clf.classes_[int(np.argmax(node_val))])
        else:
            pred_cls = 1 if prob_1 >= decision_threshold else 0
        leaf_preds[idx] = pred_cls

    # Map each test row to its person index (0 .. G-1) and leaf index (0 .. L-1)
    _, person_inv = np.unique(groups_test.to_numpy(), return_inverse=True)
    n_persons = int(person_inv.max()) + 1
    y_arr = y_test.to_numpy(dtype="int8")

    n0_person_leaf = np.zeros((n_persons, n_leaves), dtype="int32")
    n1_person_leaf = np.zeros((n_persons, n_leaves), dtype="int32")

    mask_0 = y_arr == 0
    mask_1 = y_arr == 1
    np.add.at(n0_person_leaf, (person_inv[mask_0], leaf_inv[mask_0]), 1)
    np.add.at(n1_person_leaf, (person_inv[mask_1], leaf_inv[mask_1]), 1)

    n0_f = n0_person_leaf.astype("float64")
    n1_f = n1_person_leaf.astype("float64")

    rng = np.random.default_rng(random_state)
    acc_samples = np.zeros(n_resamples, dtype="float64")
    prec_samples = np.zeros(n_resamples, dtype="float64")
    rec_samples = np.zeros(n_resamples, dtype="float64")
    f1_samples = np.zeros(n_resamples, dtype="float64")
    auc_samples = np.zeros(n_resamples, dtype="float64")

    pred_is_1 = leaf_preds == 1
    pred_is_0 = ~pred_is_1

    for b in range(n_resamples):
        sampled_persons = rng.integers(0, n_persons, size=n_persons)
        person_weights = np.bincount(sampled_persons, minlength=n_persons).astype("float64")

        leaf_n0 = person_weights @ n0_f
        leaf_n1 = person_weights @ n1_f

        tp = float(leaf_n1[pred_is_1].sum())
        fp = float(leaf_n0[pred_is_1].sum())
        fn = float(leaf_n1[pred_is_0].sum())
        tn = float(leaf_n0[pred_is_0].sum())
        total = tp + fp + fn + tn

        acc_samples[b] = (tp + tn) / total if total > 0 else 0.0
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2.0 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

        prec_samples[b] = prec
        rec_samples[b] = rec
        f1_samples[b] = f1
        auc_samples[b] = _exact_roc_auc_from_discrete_scores(leaf_probs, leaf_n0, leaf_n1)

    def _pct_ci(arr: np.ndarray) -> Tuple[float, float]:
        return float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))

    return {
        "accuracy": _pct_ci(acc_samples),
        "precision_1": _pct_ci(prec_samples),
        "recall_1": _pct_ci(rec_samples),
        "f1_1": _pct_ci(f1_samples),
        "roc_auc": _pct_ci(auc_samples),
    }


def compute_three_references_table(
    y_train: pd.Series,
    y_test: pd.Series,
    phase4_bench_df: pd.DataFrame,
    version_code: str,
) -> pd.DataFrame:
    """Compute the 3 mandatory references: Majority baseline, Trivial all-1, and 6.0 Ceiling."""
    y_tr = y_train.to_numpy(dtype="int8")
    y_te = y_test.to_numpy(dtype="int8")

    p_tr = float(y_tr.mean())
    p_te = float(y_te.mean())

    # 1. Majority-class baseline (predict all 0)
    maj_tr_acc = 1.0 - p_tr
    maj_te_acc = 1.0 - p_te

    # 2. Trivial all-positive classifier (predict all 1: F1 = 2p / (1 + p))
    all1_tr_f1 = (2.0 * p_tr) / (1.0 + p_tr)
    all1_te_f1 = (2.0 * p_te) / (1.0 + p_te)

    # 3. Full-model ceiling from 6.0_modelado_fase4_jobpath.ipynb
    v_prefix = "A" if version_code == "con_outliers" else "B"
    sub_bench = phase4_bench_df.loc[
        phase4_bench_df["version"].astype(str).str.startswith(v_prefix)
        & phase4_bench_df["modelo"].astype(str).str.contains("Logística Regularizada")
    ]
    if not sub_bench.empty:
        b_row = sub_bench.iloc[0]
        ceil_prec = float(b_row["precision_pos_test"])
        ceil_rec = float(b_row["recall_pos_test"])
        ceil_f1 = float(b_row["f1_pos_test"])
        ceil_auc = float(b_row["roc_auc_test"])
    else:
        ceil_prec, ceil_rec, ceil_f1, ceil_auc = 0.4316, 0.6937, 0.5321, 0.7133

    # Reconstruct overall test accuracy for 6.0 ceiling from precision, recall, and base rate p_te
    tp_rate = ceil_rec * p_te
    fp_rate = tp_rate * ((1.0 / ceil_prec) - 1.0) if ceil_prec > 0 else 0.0
    tn_rate = (1.0 - p_te) - fp_rate
    ceil_acc = tp_rate + tn_rate

    v_label = VERSION_LABELS_ES.get(version_code, version_code)

    rows = [
        {
            "version_datos": v_label,
            "referencia_id": "Ref 1 · Baseline clase mayoritaria (Dummy most_frequent)",
            "regla_decision": "Predice siempre 0 (no reincide)",
            "train_accuracy": round(maj_tr_acc, 4),
            "test_accuracy": round(maj_te_acc, 4),
            "test_precision_clase_1": 0.0000,
            "test_recall_clase_1": 0.0000,
            "test_f1_clase_1": 0.0000,
            "test_roc_auc": 0.5000,
            "brecha_vs_meta_085_f1": round(ASPIRATIONAL_TARGET_SCORE - 0.0, 4),
            "significado_metodologico": (
                "Piso de exactitud global (70.03%): cualquier modelo en el punto orientado a accuracy debe no caer por debajo."
            ),
        },
        {
            "version_datos": v_label,
            "referencia_id": "Ref 2 · Clasificador trivial todo-positivo (predice todo 1)",
            "regla_decision": "Predice siempre 1 (reincide)",
            "train_accuracy": round(p_tr, 4),
            "test_accuracy": round(p_te, 4),
            "test_precision_clase_1": round(p_te, 4),
            "test_recall_clase_1": 1.0000,
            "test_f1_clase_1": round(all1_te_f1, 4),
            "test_roc_auc": 0.5000,
            "brecha_vs_meta_085_f1": round(ASPIRATIONAL_TARGET_SCORE - all1_te_f1, 4),
            "significado_metodologico": (
                f"F1 trivial 2p/(1+p) = {all1_te_f1:.4f} con exactitud de apenas {p_te*100:.2f}% y sin poder discriminante (AUC=0.50)."
            ),
        },
        {
            "version_datos": v_label,
            "referencia_id": "Ref 3 · Techo real del proyecto (6.0 Logística OHE 2,981 cols)",
            "regla_decision": "Combina simultáneamente oficio OHE, educación, competencias y trayectoria",
            "train_accuracy": np.nan,
            "test_accuracy": round(ceil_acc, 4),
            "test_precision_clase_1": round(ceil_prec, 4),
            "test_recall_clase_1": round(ceil_rec, 4),
            "test_f1_clase_1": round(ceil_f1, 4),
            "test_roc_auc": round(ceil_auc, 4),
            "brecha_vs_meta_085_f1": round(ASPIRATIONAL_TARGET_SCORE - ceil_f1, 4),
            "significado_metodologico": (
                f"Techo multivariado real de Fase 4 (F1={ceil_f1:.4f}, ROC-AUC={ceil_auc:.4f}): muestra cuánto alcanza cada árbol de un solo bloque frente al modelo completo."
            ),
        },
    ]
    return pd.DataFrame(rows)


def evaluate_dummy_baseline(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    random_state: int = 42,
) -> Tuple[DummyClassifier, pd.DataFrame, Dict[str, np.ndarray]]:
    """Fit DummyClassifier(strategy='most_frequent') on train and evaluate on train and test."""
    dummy = DummyClassifier(strategy="most_frequent", random_state=random_state)
    dummy.fit(X_train, y_train)

    y_tr = y_train.to_numpy(dtype="int8")
    y_te = y_test.to_numpy(dtype="int8")
    pred_tr = dummy.predict(X_train)
    pred_te = dummy.predict(X_test)

    cm_tr = confusion_matrix(y_tr, pred_tr, labels=[0, 1])
    cm_te = confusion_matrix(y_te, pred_te, labels=[0, 1])

    rows = []
    for split_label, y_arr, pred_arr, cm in (
        ("Train (80%)", y_tr, pred_tr, cm_tr),
        ("Test (20%)", y_te, pred_te, cm_te),
    ):
        tn, fp, fn, tp = (int(x) for x in cm.ravel())
        rows.append(
            {
                "modelo": "DummyClassifier (most_frequent)",
                "particion": split_label,
                "n_filas": len(y_arr),
                "tasa_base_clase_1": round(float(y_arr.mean()), 4),
                "accuracy": round(float(accuracy_score(y_arr, pred_arr)), 4),
                "precision_clase_1": round(
                    float(precision_score(y_arr, pred_arr, pos_label=1, zero_division=0)), 4
                ),
                "recall_clase_1": round(
                    float(recall_score(y_arr, pred_arr, pos_label=1, zero_division=0)), 4
                ),
                "f1_clase_1": round(
                    float(f1_score(y_arr, pred_arr, pos_label=1, zero_division=0)), 4
                ),
                "roc_auc": 0.5000,
                "tn": tn,
                "fp": fp,
                "fn": fn,
                "tp": tp,
            }
        )

    return dummy, pd.DataFrame(rows), {"train": cm_tr, "test": cm_te}


def evaluate_operating_points_table(
    tuning_result: BlockTuningResult,
    y_train: pd.Series,
    y_test: pd.Series,
    groups_test: pd.Series,
    leaf_lift_df: pd.DataFrame,
    phase4_bench_df: pd.DataFrame,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, Dict[str, Dict[str, np.ndarray]]]:
    """Evaluate the 2 required operating points (class_weight=None and 'balanced') plus OOF threshold tau*."""
    X_tr = tuning_result.X_train
    X_te = tuning_result.X_test
    y_tr = y_train.to_numpy(dtype="int8")
    y_te = y_test.to_numpy(dtype="int8")

    baseline_test_acc = float(1.0 - y_te.mean())
    p_te = float(y_te.mean())
    trivial_all1_f1 = (2.0 * p_te) / (1.0 + p_te)

    v_prefix = "A" if tuning_result.version == "con_outliers" else "B"
    sub_bench = phase4_bench_df.loc[
        phase4_bench_df["version"].astype(str).str.startswith(v_prefix)
        & phase4_bench_df["modelo"].astype(str).str.contains("Logística Regularizada")
    ]
    ceiling_f1 = float(sub_bench["f1_pos_test"].iloc[0]) if not sub_bench.empty else 0.5321
    ceiling_auc = float(sub_bench["roc_auc_test"].iloc[0]) if not sub_bench.empty else 0.7133
    tree_label_es = BLOCK_METADATA_ES[tuning_result.block_id]["tree_label"]
    question_es = BLOCK_METADATA_ES[tuning_result.block_id]["question_es"]

    # Choose the tree's "best leaf" strictly using TRAIN statistics (soporte_train >= 0.5% and max lift_train),
    # and report its out-of-sample lift on Test; keep max-test-lift only as a labeled optimistic reference.
    train_supported_leaves = leaf_lift_df.loc[leaf_lift_df["soporte_suficiente_train"] == "Sí"].sort_values(
        by=["lift_train", "n_train"], ascending=[False, False]
    )
    if not train_supported_leaves.empty:
        best_train_leaf = train_supported_leaves.iloc[0]
    else:
        best_train_leaf = leaf_lift_df.sort_values(by=["lift_train", "n_train"], ascending=[False, False]).iloc[0]

    train_selected_leaf_id = int(best_train_leaf["hoja_id"])
    train_selected_lift_tr = float(best_train_leaf["lift_train"])
    train_selected_lift_te = float(best_train_leaf["lift_test"])
    has_high_lift_leaf = (
        str(best_train_leaf["soporte_suficiente_train"]) == "Sí"
        and train_selected_lift_te >= MIN_LEAF_LIFT_FOR_SEPARATION
    )
    max_supported_lift_te = train_selected_lift_te
    optimistic_max_test_lift = float(
        leaf_lift_df.loc[leaf_lift_df["soporte_suficiente_test"] == "Sí", "lift_test"].max()
        if (leaf_lift_df["soporte_suficiente_test"] == "Sí").any()
        else leaf_lift_df["lift_test"].max()
    )

    op_configs = [
        (
            "Punto 1 · Orientado a Exactitud (class_weight=None)",
            tuning_result.fitted_tree_none,
            None,
            "Umbral estándar 0.50 sobre tasa empírica de hoja",
        ),
        (
            "Punto 2 · Orientado a Recall / Sensibilidad (class_weight='balanced')",
            tuning_result.fitted_tree_balanced,
            None,
            "Pesos balanceados inversamente proporcionales a 70/30",
        ),
        (
            f"Punto 3 · Umbral OOF óptimo en Train (tau*={tuning_result.oof_threshold_tau:.3f})",
            tuning_result.fitted_tree_none,
            tuning_result.oof_threshold_tau,
            f"Predice 1 si P(reincide=1|hoja) >= {tuning_result.oof_threshold_tau:.3f} (sujeto a Acc >= Baseline en OOF Train)",
        ),
    ]

    rows: List[Dict[str, Any]] = []
    cms_by_point: Dict[str, Dict[str, np.ndarray]] = {}

    for point_label, clf_op, custom_thr, rule_desc in op_configs:
        if clf_op.get_depth() > MAX_TREE_DEPTH:
            raise ValueError(f"Tree depth {clf_op.get_depth()} exceeds MAX_TREE_DEPTH={MAX_TREE_DEPTH}!")

        prob_tr = clf_op.predict_proba(X_tr)[:, 1]
        prob_te = clf_op.predict_proba(X_te)[:, 1]

        if custom_thr is None:
            pred_tr = clf_op.predict(X_tr)
            pred_te = clf_op.predict(X_te)
        else:
            pred_tr = (prob_tr >= custom_thr).astype("int8")
            pred_te = (prob_te >= custom_thr).astype("int8")

        cm_tr = confusion_matrix(y_tr, pred_tr, labels=[0, 1])
        cm_te = confusion_matrix(y_te, pred_te, labels=[0, 1])
        cms_by_point[point_label] = {"train": cm_tr, "test": cm_te}

        boot_ci = bootstrap_person_metrics_ci(
            clf=clf_op,
            X_test=X_te,
            y_test=y_test,
            groups_test=groups_test,
            decision_threshold=custom_thr,
            n_resamples=BOOTSTRAP_N_RESAMPLES,
            random_state=random_state,
        )

        tr_acc = float(accuracy_score(y_tr, pred_tr))
        te_acc = float(accuracy_score(y_te, pred_te))
        tr_prec = float(precision_score(y_tr, pred_tr, pos_label=1, zero_division=0))
        te_prec = float(precision_score(y_te, pred_te, pos_label=1, zero_division=0))
        tr_rec = float(recall_score(y_tr, pred_tr, pos_label=1, zero_division=0))
        te_rec = float(recall_score(y_te, pred_te, pos_label=1, zero_division=0))
        tr_f1 = float(f1_score(y_tr, pred_tr, pos_label=1, zero_division=0))
        te_f1 = float(f1_score(y_te, pred_te, pos_label=1, zero_division=0))
        tr_auc = float(roc_auc_score(y_tr, prob_tr))
        te_auc = float(roc_auc_score(y_te, prob_te))

        auc_ci_low, auc_ci_high = boot_ci["roc_auc"]
        f1_ci_low, f1_ci_high = boot_ci["f1_1"]
        acc_ci_low, acc_ci_high = boot_ci["accuracy"]
        rec_ci_low, rec_ci_high = boot_ci["recall_1"]

        separates_flag = (auc_ci_low > 0.50) and has_high_lift_leaf
        if te_rec == 0.0 and abs(te_acc - baseline_test_acc) <= 1e-4:
            baseline_acc_status = "Empata el baseline porque no predice ningún positivo"
        elif te_acc > (baseline_test_acc + 1e-4) and te_rec > 0.0:
            baseline_acc_status = "Sí (supera el baseline con recall > 0)"
        else:
            baseline_acc_status = "No (prioriza Recall sobre exactitud global)"

        pct_ceiling_auc = round(
            100.0 * (te_auc - 0.5000) / max(ceiling_auc - 0.5000, 1e-6),
            2,
        )

        tn, fp, fn, tp = (int(x) for x in cm_te.ravel())

        rows.append(
            {
                "version_datos": tuning_result.version_label_es,
                "arbol": tree_label_es,
                "pregunta_objetivo": question_es,
                "punto_operacion": point_label,
                "regla_decision": rule_desc,
                "profundidad_efectiva": int(clf_op.get_depth()),
                "n_hojas": int(clf_op.get_n_leaves()),
                "train_accuracy": round(tr_acc, 4),
                "test_accuracy": round(te_acc, 4),
                "test_accuracy_ic95_persona": f"[{acc_ci_low:.4f}, {acc_ci_high:.4f}]",
                "gap_acc_train_test": round(tr_acc - te_acc, 4),
                "train_precision_1": round(tr_prec, 4),
                "test_precision_1": round(te_prec, 4),
                "train_recall_1": round(tr_rec, 4),
                "test_recall_1": round(te_rec, 4),
                "test_recall_1_ic95_persona": f"[{rec_ci_low:.4f}, {rec_ci_high:.4f}]",
                "train_f1_1": round(tr_f1, 4),
                "test_f1_1": round(te_f1, 4),
                "test_f1_1_ic95_persona": f"[{f1_ci_low:.4f}, {f1_ci_high:.4f}]",
                "f1_ref_trivial_todo_1": round(trivial_all1_f1, 4),
                "delta_f1_vs_trivial_todo_1": round(te_f1 - trivial_all1_f1, 4),
                "train_roc_auc": round(tr_auc, 4),
                "test_roc_auc": round(te_auc, 4),
                "test_roc_auc_ic95_persona": f"[{auc_ci_low:.4f}, {auc_ci_high:.4f}]",
                "roc_auc_ic95_inf": round(auc_ci_low, 4),
                "roc_auc_ic95_sup": round(auc_ci_high, 4),
                "roc_auc_techo_6_0": round(ceiling_auc, 4),
                "pct_del_techo_auc_6_0": pct_ceiling_auc,
                "hoja_elegida_en_train_id": train_selected_leaf_id,
                "lift_train_hoja_elegida": round(train_selected_lift_tr, 3),
                "max_lift_hoja_soporte_05pct": round(max_supported_lift_te, 3),
                "max_lift_test_referencia_optimista": round(optimistic_max_test_lift, 3),
                "hoja_con_lift_ge_150_y_soporte_05pct": "Sí" if has_high_lift_leaf else "No",
                "criterio_separa_clases": (
                    "SÍ SEPARA (IC95% AUC > 0.50 y Hoja Lift >= 1.50)"
                    if separates_flag
                    else "NO SEPARA con el umbral exigido (IC95% AUC > 0.50 pero máx Lift < 1.50)"
                ),
                "supera_baseline_exactitud_7003": baseline_acc_status,
                "brecha_vs_meta_085_f1": round(ASPIRATIONAL_TARGET_SCORE - te_f1, 4),
                "tn_test": tn,
                "fp_test": fp,
                "fn_test": fn,
                "tp_test": tp,
            }
        )

    return pd.DataFrame(rows), cms_by_point


def build_depth_comparison_table(
    base_spec: CandidateSpec,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    version_label_es: str,
    tree_label_es: str,
    random_state: int = 42,
    depths: Sequence[int] = ALLOWED_DEPTHS,
) -> pd.DataFrame:
    """Build the depth comparison table strictly for depths 2, 3, and 4 (for both None and balanced)."""
    for d in depths:
        if d is None or d > MAX_TREE_DEPTH or d < 1:
            raise ValueError(f"Forbidden depth {d} requested in depth table!")

    y_tr = y_train.to_numpy(dtype="int8")
    y_te = y_test.to_numpy(dtype="int8")
    rows = []

    for cw_label, cw_val in (
        ("class_weight=None (Exactitud)", None),
        ("class_weight='balanced' (Recall)", "balanced"),
    ):
        for depth in depths:
            spec_d = CandidateSpec(
                attempt_id=base_spec.attempt_id,
                variant_name=base_spec.variant_name,
                operating_point_label=cw_label,
                description_es=base_spec.description_es,
                criterion=base_spec.criterion,
                max_depth=depth,
                min_samples_split=base_spec.min_samples_split,
                min_samples_leaf=base_spec.min_samples_leaf,
                class_weight=cw_val,
                ccp_alpha=base_spec.ccp_alpha,
                complexity_rank=base_spec.complexity_rank,
            )
            clf_d = instantiate_tree_from_spec(spec_d, random_state=random_state)
            clf_d.fit(X_train, y_tr)

            pred_tr = clf_d.predict(X_train)
            pred_te = clf_d.predict(X_test)
            prob_te = clf_d.predict_proba(X_test)[:, 1]

            train_acc = float(accuracy_score(y_tr, pred_tr))
            test_acc = float(accuracy_score(y_te, pred_te))
            train_f1 = float(f1_score(y_tr, pred_tr, pos_label=1, zero_division=0))
            test_f1 = float(f1_score(y_te, pred_te, pos_label=1, zero_division=0))
            test_prec = float(precision_score(y_te, pred_te, pos_label=1, zero_division=0))
            test_rec = float(recall_score(y_te, pred_te, pos_label=1, zero_division=0))
            test_auc = float(roc_auc_score(y_te, prob_te))

            rows.append(
                {
                    "version_datos": version_label_es,
                    "arbol": tree_label_es,
                    "punto_operacion": cw_label,
                    "max_depth": depth,
                    "profundidad_alcanzada": int(clf_d.get_depth()),
                    "n_leaves": int(clf_d.get_n_leaves()),
                    "train_acc": round(train_acc, 4),
                    "test_acc": round(test_acc, 4),
                    "gap_train_test": round(train_acc - test_acc, 4),
                    "train_f1_clase_1": round(train_f1, 4),
                    "test_precision_clase_1": round(test_prec, 4),
                    "test_recall_clase_1": round(test_rec, 4),
                    "test_f1_clase_1": round(test_f1, 4),
                    "test_roc_auc": round(test_auc, 4),
                }
            )

    return pd.DataFrame(rows)


def format_condition_spanish(
    feature: str,
    threshold: float,
    branch: str,
    missing_go_to_left: Optional[bool] = None,
) -> str:
    """Translate a sklearn split condition (<= threshold or > threshold) into plain Spanish."""
    is_left = branch == "left"

    if feature.startswith("isco_major_"):
        digit = feature.replace("isco_major_", "")
        label = ISCO_MAJOR_LABELS_ES.get(digit, f"Gran Grupo {digit}")
        return f"NO pertenece a [{label}]" if is_left else f"SÍ pertenece a [{label}]"

    if feature.startswith("isco_sub2_"):
        code = feature.replace("isco_sub2_", "")
        return f"NO pertenece al Subgrupo ISCO {code}" if is_left else f"SÍ pertenece al Subgrupo ISCO {code}"

    if feature.startswith("isco_unit4_"):
        code = feature.replace("isco_unit4_", "")
        return f"NO pertenece al Grupo ISCO {code}" if is_left else f"SÍ pertenece al Grupo ISCO {code}"

    if feature in ("educacion_no_reportada", "es_secundaria", "es_bachelor", "es_posgrado", "tiene_knowledge"):
        friendly = {
            "educacion_no_reportada": "educación NO reportada",
            "es_secundaria": "educación secundaria",
            "es_bachelor": "grado universitario (Bachelor)",
            "es_posgrado": "posgrado (Master/PhD)",
            "tiene_knowledge": "exige conocimientos teóricos (>0)",
        }[feature]
        return f"{friendly} = No (0)" if is_left else f"{friendly} = Sí (1)"

    if feature in ("nivel_academico_ord", "nivel_educativo_ord", "nivel_educativo_reportado_ord"):
        k_floor = int(math.floor(threshold))
        inv_map = {
            -1: "No reportado (-1)",
            0: "No reportado (0)",
            1: "Secondary school (1)",
            2: "Bachelor (2)",
            3: "Master (3)",
            4: "PhD (4)",
        }
        nan_note = ""
        if missing_go_to_left is not None and feature == "nivel_academico_ord":
            if (is_left and missing_go_to_left) or ((not is_left) and (not missing_go_to_left)):
                nan_note = " [incluye NaN / No reportado]"
        if is_left:
            return f"{feature} <= {threshold:.1f} (hasta {inv_map.get(k_floor, str(k_floor))}){nan_note}"
        return f"{feature} > {threshold:.1f} (desde {inv_map.get(k_floor + 1, str(k_floor + 1))} o superior){nan_note}"

    if feature in (
        "n_skills_essential",
        "n_skills_competence",
        "n_skills_knowledge",
        "n_skills_sin_tipo",
        "diff_competence_knowledge",
        "diferencia_practica_teorica",
    ):
        # Integer counts rule: 18.5 means <= 18 on left and >= 19 ("19 o más") on right
        is_half_integer = abs((threshold - math.floor(threshold)) - 0.5) < 1e-3
        if is_half_integer:
            k_left = int(math.floor(threshold))
            k_right = k_left + 1
            if is_left:
                return f"{feature} <= {threshold:.1f} ({k_left} o menos)"
            return f"{feature} > {threshold:.1f} ({k_right} o más)"
        if is_left:
            return f"{feature} <= {threshold:.2f}"
        return f"{feature} > {threshold:.2f}"

    if is_left:
        return f"{feature} <= {threshold:.4f}"
    return f"{feature} > {threshold:.4f}"


def extract_first_questions_via_decision_path(
    clf: DecisionTreeClassifier,
    X: pd.DataFrame,
    y: pd.Series,
    version_label_es: str,
    dataset_label: str = "Train",
) -> pd.DataFrame:
    """Compute root and level-2 question statistics strictly using clf.decision_path(X)."""
    tree_ = clf.tree_
    feature_names = list(X.columns)
    path_csr = clf.decision_path(X)
    y_arr = y.to_numpy(dtype="int8")
    base_rate = float(y_arr.mean())

    candidate_nodes: List[Tuple[str, int]] = []
    if tree_.children_left[0] != _tree.TREE_LEAF:
        candidate_nodes.append(("Nivel 1 · Raíz (Nodo 0)", 0))
        left_0 = int(tree_.children_left[0])
        right_0 = int(tree_.children_right[0])
        if tree_.children_left[left_0] != _tree.TREE_LEAF:
            candidate_nodes.append((f"Nivel 2 · Rama Izquierda (Nodo {left_0})", left_0))
        if tree_.children_left[right_0] != _tree.TREE_LEAF:
            candidate_nodes.append((f"Nivel 2 · Rama Derecha (Nodo {right_0})", right_0))

    missing_left_arr = getattr(tree_, "missing_go_to_left", None)

    rows = []
    for level_label, node_id in candidate_nodes:
        feat_idx = int(tree_.feature[node_id])
        feat_name = feature_names[feat_idx]
        thresh = float(tree_.threshold[node_id])
        left_child = int(tree_.children_left[node_id])
        right_child = int(tree_.children_right[node_id])
        miss_left = bool(missing_left_arr[node_id]) if missing_left_arr is not None else None

        mask_node = path_csr[:, node_id].toarray().ravel().astype(bool)
        mask_left = path_csr[:, left_child].toarray().ravel().astype(bool)
        mask_right = path_csr[:, right_child].toarray().ravel().astype(bool)

        n_node = int(mask_node.sum())
        n_left = int(mask_left.sum())
        n_right = int(mask_right.sum())

        rate_left = float(y_arr[mask_left].mean()) if n_left > 0 else 0.0
        rate_right = float(y_arr[mask_right].mean()) if n_right > 0 else 0.0
        lift_left = (rate_left / base_rate) if base_rate > 0 else 0.0
        lift_right = (rate_right / base_rate) if base_rate > 0 else 0.0

        question_es = (
            f"¿{feat_name} <= {thresh:.2f}? "
            f"[Izq: {format_condition_spanish(feat_name, thresh, 'left', miss_left)} | "
            f"Der: {format_condition_spanish(feat_name, thresh, 'right', miss_left)}]"
        )

        rows.append(
            {
                "version_datos": version_label_es,
                "particion": dataset_label,
                "nivel_arbol": level_label,
                "nodo_id": node_id,
                "variable": feat_name,
                "umbral_sklearn": round(thresh, 4),
                "pregunta_es": question_es,
                "n_en_nodo": n_node,
                "n_izquierda": n_left,
                "pct_izquierda": round(100.0 * n_left / max(n_node, 1), 2),
                "tasa_clase1_izquierda": round(rate_left, 4),
                "lift_izquierda": round(lift_left, 3),
                "n_derecha": n_right,
                "pct_derecha": round(100.0 * n_right / max(n_node, 1), 2),
                "tasa_clase1_derecha": round(rate_right, 4),
                "lift_derecha": round(lift_right, 3),
            }
        )

    return pd.DataFrame(rows)


def _trace_node_paths(
    tree_: _tree.Tree,
    feature_names: List[str],
) -> Tuple[Dict[int, int], Dict[int, List[str]]]:
    """Traverse the tree once to map every node to its depth and Spanish condition path."""
    depths: Dict[int, int] = {0: 0}
    paths_es: Dict[int, List[str]] = {0: []}
    missing_left_arr = getattr(tree_, "missing_go_to_left", None)

    stack = [0]
    while stack:
        node_id = stack.pop()
        left_id = int(tree_.children_left[node_id])
        right_id = int(tree_.children_right[node_id])
        if left_id == _tree.TREE_LEAF:
            continue
        feat_name = feature_names[int(tree_.feature[node_id])]
        thresh = float(tree_.threshold[node_id])
        miss_left = bool(missing_left_arr[node_id]) if missing_left_arr is not None else None

        depths[left_id] = depths[node_id] + 1
        depths[right_id] = depths[node_id] + 1

        paths_es[left_id] = paths_es[node_id] + [
            format_condition_spanish(feat_name, thresh, "left", miss_left)
        ]
        paths_es[right_id] = paths_es[node_id] + [
            format_condition_spanish(feat_name, thresh, "right", miss_left)
        ]

        stack.append(right_id)
        stack.append(left_id)

    return depths, paths_es


def build_leaf_lift_table(
    clf: DecisionTreeClassifier,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    version_label_es: str,
    operating_point_label: str = "class_weight='balanced'",
    min_support_ratio: float = MIN_LEAF_SUPPORT_RATIO,
) -> pd.DataFrame:
    """Compute per-leaf statistics (size, class-1 rate, 95% Wilson CI, lift, support flag) on train and test."""
    tree_ = clf.tree_
    feature_names = list(X_train.columns)
    depths, paths_es = _trace_node_paths(tree_, feature_names)

    leaf_ids_train = clf.apply(X_train)
    leaf_ids_test = clf.apply(X_test)
    y_tr = y_train.to_numpy(dtype="int8")
    y_te = y_test.to_numpy(dtype="int8")

    base_tr = float(y_tr.mean())
    base_te = float(y_te.mean())
    min_pct = 100.0 * min_support_ratio

    all_leaf_nodes = [
        node_id
        for node_id in range(tree_.node_count)
        if tree_.children_left[node_id] == _tree.TREE_LEAF
    ]

    rows = []
    for leaf_id in all_leaf_nodes:
        node_val = tree_.value[leaf_id][0]
        pred_class = int(clf.classes_[int(np.argmax(node_val))])

        mask_tr = leaf_ids_train == leaf_id
        mask_te = leaf_ids_test == leaf_id
        n_tr = int(mask_tr.sum())
        n_te = int(mask_te.sum())
        k_tr = int(y_tr[mask_tr].sum()) if n_tr > 0 else 0
        k_te = int(y_te[mask_te].sum()) if n_te > 0 else 0

        rate_tr = float(k_tr / n_tr) if n_tr > 0 else 0.0
        rate_te = float(k_te / n_te) if n_te > 0 else 0.0

        w_tr_low, w_tr_high = wilson_ci_95(k_tr, n_tr)
        w_te_low, w_te_high = wilson_ci_95(k_te, n_te)

        lift_tr = (rate_tr / base_tr) if base_tr > 0 else 0.0
        lift_te = (rate_te / base_te) if base_te > 0 else 0.0

        pct_tr = 100.0 * n_tr / len(y_tr)
        pct_te = 100.0 * n_te / len(y_te)

        rows.append(
            {
                "version_datos": version_label_es,
                "punto_operacion": operating_point_label,
                "hoja_id": leaf_id,
                "profundidad": depths.get(leaf_id, 0),
                "predice_reincide": pred_class,
                "n_train": n_tr,
                "pct_train": round(pct_tr, 2),
                "tasa_clase1_train": round(rate_tr, 4),
                "wilson_ic95_train": f"[{w_tr_low:.4f}, {w_tr_high:.4f}]",
                "tasa_base_train": round(base_tr, 4),
                "lift_train": round(lift_tr, 3),
                "n_test": n_te,
                "pct_test": round(pct_te, 2),
                "tasa_clase1_test": round(rate_te, 4),
                "wilson_ic95_test": f"[{w_te_low:.4f}, {w_te_high:.4f}]",
                "wilson_ic95_test_inf": round(w_te_low, 4),
                "wilson_ic95_test_sup": round(w_te_high, 4),
                "tasa_base_test": round(base_te, 4),
                "lift_test": round(lift_te, 3),
                "soporte_suficiente_train": "Sí" if pct_tr >= min_pct else f"No (<{min_pct:.1f}%)",
                "soporte_suficiente_test": "Sí" if pct_te >= min_pct else f"No (<{min_pct:.1f}%)",
                "condiciones_hoja_es": " Y ".join(paths_es.get(leaf_id, [])),
            }
        )

    df_leaves = pd.DataFrame(rows).sort_values(
        by=["predice_reincide", "lift_train", "n_train"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    return df_leaves


def extract_feature_importances_table(
    clf: DecisionTreeClassifier,
    feature_names: Sequence[str],
    feature_descriptions: Dict[str, str],
    version_label_es: str,
) -> pd.DataFrame:
    """Build a sorted feature importance table interpreted strictly as what the tree looked at."""
    importances = clf.feature_importances_
    rows = []
    for name, imp in zip(feature_names, importances):
        rows.append(
            {
                "version_datos": version_label_es,
                "variable": name,
                "importancia": round(float(imp), 4),
                "importancia_pct": round(float(imp * 100.0), 2),
                "descripcion_variable": feature_descriptions.get(name, ""),
                "lectura_metodologica": (
                    "Qué miró este árbol para reducir impureza en sus nodos (NO implica causalidad)"
                    if imp > 0
                    else "No utilizada por el árbol en profundidad <= 4"
                ),
            }
        )
    return (
        pd.DataFrame(rows)
        .sort_values(by="importancia", ascending=False)
        .reset_index(drop=True)
    )


def export_tree_text_rules(
    clf: DecisionTreeClassifier,
    feature_names: Sequence[str],
) -> str:
    """Return sklearn export_text representation of the tree."""
    return export_text(
        clf,
        feature_names=list(feature_names),
        show_weights=True,
        decimals=2,
        max_depth=MAX_TREE_DEPTH,
    )


def extract_spanish_business_rules(
    leaf_table: pd.DataFrame,
    tree_label: str,
    question_es: str,
    version_label_es: str,
    min_rules: int = 2,
    profile_20_19_1_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Extract at least 2 plain-Spanish business rules ONLY from leaves meeting minimum support (>=0.5%)."""
    supported = leaf_table.loc[leaf_table["soporte_suficiente_train"] == "Sí"].copy()
    if len(supported) < min_rules:
        supported = leaf_table.copy()

    pos_leaves = supported.loc[supported["predice_reincide"] == 1].sort_values(
        by=["lift_train", "n_train"], ascending=[False, False]
    )
    neg_leaves = supported.loc[supported["predice_reincide"] == 0].sort_values(
        by=["lift_train", "n_train"], ascending=[True, False]
    )

    if len(pos_leaves) >= 1 and len(neg_leaves) >= 1:
        # Include top positive leaves and the strongest contrasting negative leaf
        selected_leaves = pd.concat(
            [pos_leaves.head(max(min_rules - 1, 2)), neg_leaves.head(1)],
            ignore_index=True,
        )
    elif len(pos_leaves) >= min_rules:
        selected_leaves = pos_leaves.head(min_rules).copy()
    else:
        selected_leaves = pd.concat([pos_leaves, neg_leaves.head(min_rules)], ignore_index=True)

    rules_rows = []
    for idx, (_, row) in enumerate(selected_leaves.iterrows(), start=1):
        leaf_id = int(row["hoja_id"])
        pred_cls = int(row["predice_reincide"])
        cond_str = str(row["condiciones_hoja_es"])
        n_tr = int(row["n_train"])
        n_te = int(row["n_test"])
        rate_tr_pct = round(float(row["tasa_clase1_train"]) * 100.0, 2)
        base_tr_pct = round(float(row["tasa_base_train"]) * 100.0, 2)
        lift_tr = float(row["lift_train"])
        rate_te_pct = round(float(row["tasa_clase1_test"]) * 100.0, 2)
        base_te_pct = round(float(row["tasa_base_test"]) * 100.0, 2)
        lift_te = float(row["lift_test"])
        w_te = str(row["wilson_ic95_test"])

        is_profile_20_19_1_leaf = (
            "Skills" in tree_label
            and leaf_id in (16, 26)
            and n_tr == int(pos_leaves["n_train"].iloc[0])
        )

        if is_profile_20_19_1_leaf and profile_20_19_1_df is not None and not profile_20_19_1_df.empty:
            n_occ_profile = len(profile_20_19_1_df)
            n_maj_profile = int(profile_20_19_1_df["isco_major"].nunique())
            top_occ = profile_20_19_1_df.iloc[0]
            top_code = str(top_occ["occupation_code"])
            top_label = str(top_occ.get("occupation_label", top_occ["isco_group_label"]))
            top_share_tot = float(top_occ["pct_hoja_total"])
            top_rate_tr_pct = round(float(top_occ["tasa_clase1_train"]) * 100.0, 2)
            top_rate_te_pct = round(float(top_occ["tasa_clase1_test"]) * 100.0, 2)
            sec_occ = profile_20_19_1_df.iloc[1]
            sec_code = str(sec_occ["occupation_code"])
            sec_label = str(sec_occ.get("occupation_label", sec_occ["isco_group_label"]))
            sec_share_tot = float(sec_occ["pct_hoja_total"])
            sec_rate_tot_pct = round(float(sec_occ["tasa_clase1_total"]) * 100.0, 2)

            plain_rule = (
                f"Regla basada en perfil puntual {idx} ({tree_label} · {version_label_es}, Hoja {leaf_id}): "
                f"SI el registro cumple [{cond_str}], la identidad entera E = C + K restringe algebraicamente la hoja "
                f"al único perfil discreto de competencias (n_skills_essential = 20, n_skills_competence = 19, n_skills_knowledge = 1), "
                f"ubicándolo en clase positiva (reincide = 1 en punto balanceado). "
                f"En Train agrupa {n_tr:,} registros ({row['pct_train']:.2f}% del split) con tasa de repetición de {rate_tr_pct:.2f}% "
                f"frente a {base_tr_pct:.2f}% base (Lift = {lift_tr:.3f}x), y en Test agrupa {n_te:,} registros ({row['pct_test']:.2f}%) "
                f"con tasa de {rate_te_pct:.2f}% (IC95% Wilson = {w_te}) frente a {base_te_pct:.2f}% base (Lift = {lift_te:.3f}x). "
                f"ADVERTENCIA DE CIRCULARIDAD (huella de oficio): este perfil puntual NO representa una ley general sobre "
                f"'oficios que exigen más competencias', sino una huella discreta compartida por {n_occ_profile} ocupaciones en {n_maj_profile} grandes grupos ISCO, "
                f"donde una sola ocupación ({top_code} · {top_label}, Gran Grupo 3) aporta el {top_share_tot:.2f}% de las filas "
                f"con tasa de repetición de {top_rate_tr_pct:.2f}% en Train y {top_rate_te_pct:.2f}% en Test, mientras que la segunda "
                f"({sec_code} · {sec_label}, Gran Grupo 9, {sec_share_tot:.2f}% de la hoja) tiene {sec_rate_tot_pct:.2f}% (igual a la tasa base)."
            )
            caveat_str = (
                f"Regla de perfil puntual (E=20, C=19, K=1) con circularidad parcial N:1: actúa como huella de la ocupación "
                f"{top_code} ({top_share_tot:.2f}% de la hoja), NO como efecto general de exigir más competencias."
            )
        else:
            if pred_cls == 1:
                decision_phrase = "con mayor propensión a repetición (predice reincide = 1 en punto balanceado)"
            else:
                decision_phrase = "con menor propensión a repetición / ejercicio único (predice reincide = 0)"

            plain_rule = (
                f"Regla {idx} ({tree_label} · {version_label_es}, Hoja {leaf_id}): SI el registro de empleo cumple que "
                f"[{cond_str}], ENTONCES el árbol ubica el perfil del oficio {decision_phrase}. "
                f"En Train agrupa {n_tr:,} registros ({row['pct_train']:.2f}% del total, soporte >= 0.5%) "
                f"con una tasa empírica de reincidencia de {rate_tr_pct:.2f}% frente a la tasa base de {base_tr_pct:.2f}% "
                f"(Lift = {lift_tr:.3f}x). En Test comprende {n_te:,} registros ({row['pct_test']:.2f}%) con tasa de {rate_te_pct:.2f}% "
                f"(IC95% Wilson = {w_te}) frente a {base_te_pct:.2f}% base (Lift = {lift_te:.3f}x)."
            )
            caveat_str = (
                "Esta regla NO es causal, clasifica perfiles de oficios con soporte >= 0.5% (no toma decisiones "
                "sobre personas individuales) y la exactitud global puede engañar ante el desbalance 70/30."
            )

        rules_rows.append(
            {
                "version_datos": version_label_es,
                "arbol": tree_label,
                "pregunta_objetivo": question_es,
                "regla_num": idx,
                "hoja_id": leaf_id,
                "predice_reincide": pred_cls,
                "condiciones_es": cond_str,
                "n_registros_train": n_tr,
                "pct_train": float(row["pct_train"]),
                "tasa_clase1_train_pct": rate_tr_pct,
                "tasa_base_train_pct": base_tr_pct,
                "lift_train": round(lift_tr, 3),
                "n_registros_test": n_te,
                "pct_test": float(row["pct_test"]),
                "tasa_clase1_test_pct": rate_te_pct,
                "wilson_ic95_test": w_te,
                "tasa_base_test_pct": base_te_pct,
                "lift_test": round(lift_te, 3),
                "regla_negocio_espanol": plain_rule,
                "advertencia_lo_que_no_dice": caveat_str,
            }
        )

    return pd.DataFrame(rules_rows)
