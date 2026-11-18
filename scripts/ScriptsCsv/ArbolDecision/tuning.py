"""Person-grouped CV tuning (by ROC-AUC with 1-SE rule), two operating points, and OOF threshold selection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold
from sklearn.tree import DecisionTreeClassifier

from .block_builders import (
    BlockFeatureBuilder,
    EducationBlockBuilder,
    ISCOBlockBuilder,
    SkillsBlockBuilder,
)
from .config import (
    BLOCK_EDUCATION,
    BLOCK_ISCO,
    BLOCK_METADATA_ES,
    BLOCK_SKILLS,
    DecisionTreeProjectConfig,
    VERSION_LABELS_ES,
)


@dataclass(frozen=True)
class CandidateSpec:
    """Specification of a single honest tuning attempt within a block and version."""

    attempt_id: int
    variant_name: str
    operating_point_label: str
    description_es: str
    criterion: str
    max_depth: int
    min_samples_split: int
    min_samples_leaf: int
    class_weight: Any
    ccp_alpha: float
    complexity_rank: int
    is_primary_eligible: bool = True
    note_es: str = "Candidato elegible del bloque"


@dataclass(frozen=True)
class BlockTuningResult:
    """Result bundle produced after tuning one tree block and data version via GroupKFold."""

    block_id: str
    version: str
    version_label_es: str
    selected_attempt_id: int
    selected_spec: CandidateSpec
    spec_accuracy_point: CandidateSpec
    spec_balanced_point: CandidateSpec
    fitted_builder: BlockFeatureBuilder
    fitted_tree_none: DecisionTreeClassifier
    fitted_tree_balanced: DecisionTreeClassifier
    oof_threshold_tau: float
    oof_threshold_metrics_train: Dict[str, float]
    X_train: pd.DataFrame
    X_test: pd.DataFrame
    attempts_log: pd.DataFrame
    best_cv_roc_auc: float
    best_cv_roc_auc_se: float


def build_candidate_specs_for_block(block_id: str) -> List[CandidateSpec]:
    """Return the 10 structured tuning candidates (max_depth <= 4) for the given block."""
    if block_id == BLOCK_ISCO:
        return [
            CandidateSpec(
                attempt_id=1,
                variant_name="major_1d",
                operating_point_label="class_weight=None (exactitud)",
                description_es="ISCO 1 dígito (10 dummies) · Gini · sin pesos · hoja mín 500",
                criterion="gini",
                max_depth=4,
                min_samples_split=1000,
                min_samples_leaf=500,
                class_weight=None,
                ccp_alpha=0.0,
                complexity_rank=3,
            ),
            CandidateSpec(
                attempt_id=2,
                variant_name="major_1d",
                operating_point_label="class_weight='balanced' (recall)",
                description_es="ISCO 1 dígito (10 dummies) · Gini · balanced · hoja mín 200",
                criterion="gini",
                max_depth=4,
                min_samples_split=400,
                min_samples_leaf=200,
                class_weight="balanced",
                ccp_alpha=0.0,
                complexity_rank=5,
            ),
            CandidateSpec(
                attempt_id=3,
                variant_name="major_1d",
                operating_point_label="class_weight='balanced' (recall)",
                description_es="ISCO 1 dígito (10 dummies) · Gini · balanced · hoja mín 1,000",
                criterion="gini",
                max_depth=4,
                min_samples_split=2000,
                min_samples_leaf=1000,
                class_weight="balanced",
                ccp_alpha=0.0,
                complexity_rank=3,
            ),
            CandidateSpec(
                attempt_id=4,
                variant_name="major_1d",
                operating_point_label="class_weight='balanced' (recall)",
                description_es="ISCO 1 dígito (10 dummies) · Gini · balanced · hoja mín 2,500 (regularizado)",
                criterion="gini",
                max_depth=4,
                min_samples_split=5000,
                min_samples_leaf=2500,
                class_weight="balanced",
                ccp_alpha=0.0,
                complexity_rank=2,
            ),
            CandidateSpec(
                attempt_id=5,
                variant_name="major_1d",
                operating_point_label="class_weight='balanced' (recall)",
                description_es="ISCO 1 dígito (10 dummies) · Gini · balanced · hoja mín 5,000 (alta regularización)",
                criterion="gini",
                max_depth=4,
                min_samples_split=10000,
                min_samples_leaf=5000,
                class_weight="balanced",
                ccp_alpha=0.0,
                complexity_rank=1,
            ),
            CandidateSpec(
                attempt_id=6,
                variant_name="major_1d",
                operating_point_label="class_weight='balanced' (recall)",
                description_es="ISCO 1 dígito (10 dummies) · Entropy · balanced · hoja mín 2,500",
                criterion="entropy",
                max_depth=4,
                min_samples_split=5000,
                min_samples_leaf=2500,
                class_weight="balanced",
                ccp_alpha=0.0,
                complexity_rank=2,
            ),
            CandidateSpec(
                attempt_id=7,
                variant_name="major_1d",
                operating_point_label="class_weight=None (exactitud)",
                description_es="ISCO 1 dígito (10 dummies) · Entropy · sin pesos · hoja mín 2,500",
                criterion="entropy",
                max_depth=4,
                min_samples_split=5000,
                min_samples_leaf=2500,
                class_weight=None,
                ccp_alpha=0.0,
                complexity_rank=2,
            ),
            CandidateSpec(
                attempt_id=8,
                variant_name="major_1d",
                operating_point_label="class_weight='balanced' (recall)",
                description_es="ISCO 1 dígito (10 dummies) · Gini · balanced · hoja mín 2,500 · ccp_alpha=1e-4",
                criterion="gini",
                max_depth=4,
                min_samples_split=5000,
                min_samples_leaf=2500,
                class_weight="balanced",
                ccp_alpha=1e-4,
                complexity_rank=1,
            ),
            CandidateSpec(
                attempt_id=9,
                variant_name="submajor_2d",
                operating_point_label="class_weight='balanced' (recall)",
                description_es="Variante 2 dígitos ISCO (~40 subgrupos) · Gini · balanced · hoja mín 2,500",
                criterion="gini",
                max_depth=4,
                min_samples_split=5000,
                min_samples_leaf=2500,
                class_weight="balanced",
                ccp_alpha=0.0,
                complexity_rank=8,
                is_primary_eligible=False,
                note_es="Variante registrada (ISCO 2 dígitos; mayor cardinalidad que la versión principal 1d)",
            ),
            CandidateSpec(
                attempt_id=10,
                variant_name="top50_unit_4d",
                operating_point_label="class_weight='balanced' (recall)",
                description_es="Variante Top-50 4 dígitos ISCO · Gini · balanced · hoja mín 2,500",
                criterion="gini",
                max_depth=4,
                min_samples_split=5000,
                min_samples_leaf=2500,
                class_weight="balanced",
                ccp_alpha=0.0,
                complexity_rank=10,
                is_primary_eligible=False,
                note_es="ADVERTENCIA DE CIRCULARIDAD: 4 dígitos ISCO casi identifica el occupation_code que define reincide",
            ),
        ]

    if block_id == BLOCK_EDUCATION:
        return [
            CandidateSpec(
                attempt_id=1,
                variant_name="ordinal_nan_plus_flag",
                operating_point_label="class_weight=None (exactitud)",
                description_es="Ordinal reportado (1..4, NaN sin rellenar con 0) + bandera MNAR · Gini · sin pesos · hoja mín 500",
                criterion="gini",
                max_depth=4,
                min_samples_split=1000,
                min_samples_leaf=500,
                class_weight=None,
                ccp_alpha=0.0,
                complexity_rank=3,
            ),
            CandidateSpec(
                attempt_id=2,
                variant_name="ordinal_nan_plus_flag",
                operating_point_label="class_weight='balanced' (recall)",
                description_es="Ordinal reportado (1..4, NaN) + bandera MNAR · Gini · balanced · hoja mín 200",
                criterion="gini",
                max_depth=4,
                min_samples_split=400,
                min_samples_leaf=200,
                class_weight="balanced",
                ccp_alpha=0.0,
                complexity_rank=5,
            ),
            CandidateSpec(
                attempt_id=3,
                variant_name="ordinal_nan_plus_flag",
                operating_point_label="class_weight='balanced' (recall)",
                description_es="Ordinal reportado (1..4, NaN) + bandera MNAR · Gini · balanced · hoja mín 1,000",
                criterion="gini",
                max_depth=4,
                min_samples_split=2000,
                min_samples_leaf=1000,
                class_weight="balanced",
                ccp_alpha=0.0,
                complexity_rank=3,
            ),
            CandidateSpec(
                attempt_id=4,
                variant_name="ordinal_nan_plus_flag",
                operating_point_label="class_weight='balanced' (recall)",
                description_es="Ordinal reportado (1..4, NaN) + bandera MNAR · Gini · balanced · hoja mín 2,500 (regularizado)",
                criterion="gini",
                max_depth=4,
                min_samples_split=5000,
                min_samples_leaf=2500,
                class_weight="balanced",
                ccp_alpha=0.0,
                complexity_rank=2,
            ),
            CandidateSpec(
                attempt_id=5,
                variant_name="ordinal_nan_plus_flag",
                operating_point_label="class_weight='balanced' (recall)",
                description_es="Ordinal reportado (1..4, NaN) + bandera MNAR · Gini · balanced · hoja mín 5,000 (alta regularización)",
                criterion="gini",
                max_depth=4,
                min_samples_split=10000,
                min_samples_leaf=5000,
                class_weight="balanced",
                ccp_alpha=0.0,
                complexity_rank=1,
            ),
            CandidateSpec(
                attempt_id=6,
                variant_name="ordinal_nan_plus_flag",
                operating_point_label="class_weight='balanced' (recall)",
                description_es="Ordinal reportado (1..4, NaN) + bandera MNAR · Entropy · balanced · hoja mín 2,500",
                criterion="entropy",
                max_depth=4,
                min_samples_split=5000,
                min_samples_leaf=2500,
                class_weight="balanced",
                ccp_alpha=0.0,
                complexity_rank=2,
            ),
            CandidateSpec(
                attempt_id=7,
                variant_name="ordinal_nan_plus_flag",
                operating_point_label="class_weight=None (exactitud)",
                description_es="Ordinal reportado (1..4, NaN) + bandera MNAR · Entropy · sin pesos · hoja mín 2,500",
                criterion="entropy",
                max_depth=4,
                min_samples_split=5000,
                min_samples_leaf=2500,
                class_weight=None,
                ccp_alpha=0.0,
                complexity_rank=2,
            ),
            CandidateSpec(
                attempt_id=8,
                variant_name="ordinal_nan_plus_flag",
                operating_point_label="class_weight='balanced' (recall)",
                description_es="Ordinal reportado (1..4, NaN) + bandera MNAR · Gini · balanced · hoja mín 2,500 · ccp_alpha=1e-4",
                criterion="gini",
                max_depth=4,
                min_samples_split=5000,
                min_samples_leaf=2500,
                class_weight="balanced",
                ccp_alpha=1e-4,
                complexity_rank=1,
            ),
            CandidateSpec(
                attempt_id=9,
                variant_name="ordinal_neg1_plus_flag",
                operating_point_label="class_weight='balanced' (recall)",
                description_es="Ordinal (1..4 reportados, -1 no reportado) + bandera MNAR · Gini · balanced · hoja mín 2,500",
                criterion="gini",
                max_depth=4,
                min_samples_split=5000,
                min_samples_leaf=2500,
                class_weight="balanced",
                ccp_alpha=0.0,
                complexity_rank=2,
            ),
            CandidateSpec(
                attempt_id=10,
                variant_name="ordinal_nan_plus_flag_and_cycles",
                operating_point_label="class_weight='balanced' (recall)",
                description_es="Ordinal (1..4, NaN) + bandera MNAR + indicador posgrado · Gini · balanced · hoja mín 2,500",
                criterion="gini",
                max_depth=4,
                min_samples_split=5000,
                min_samples_leaf=2500,
                class_weight="balanced",
                ccp_alpha=0.0,
                complexity_rank=3,
            ),
        ]

    if block_id == BLOCK_SKILLS:
        return [
            CandidateSpec(
                attempt_id=1,
                variant_name="counts_base",
                operating_point_label="class_weight=None (exactitud)",
                description_es="3 conteos ESCO (essential, competence, knowledge) · Gini · sin pesos · hoja mín 500",
                criterion="gini",
                max_depth=4,
                min_samples_split=1000,
                min_samples_leaf=500,
                class_weight=None,
                ccp_alpha=0.0,
                complexity_rank=3,
            ),
            CandidateSpec(
                attempt_id=2,
                variant_name="counts_base",
                operating_point_label="class_weight='balanced' (recall)",
                description_es="3 conteos ESCO · Gini · balanced · hoja mín 200",
                criterion="gini",
                max_depth=4,
                min_samples_split=400,
                min_samples_leaf=200,
                class_weight="balanced",
                ccp_alpha=0.0,
                complexity_rank=5,
            ),
            CandidateSpec(
                attempt_id=3,
                variant_name="counts_base",
                operating_point_label="class_weight='balanced' (recall)",
                description_es="3 conteos ESCO · Gini · balanced · hoja mín 1,000",
                criterion="gini",
                max_depth=4,
                min_samples_split=2000,
                min_samples_leaf=1000,
                class_weight="balanced",
                ccp_alpha=0.0,
                complexity_rank=3,
            ),
            CandidateSpec(
                attempt_id=4,
                variant_name="counts_base",
                operating_point_label="class_weight='balanced' (recall)",
                description_es="3 conteos ESCO · Gini · balanced · hoja mín 2,500 (regularizado contra hojas pequeñas)",
                criterion="gini",
                max_depth=4,
                min_samples_split=5000,
                min_samples_leaf=2500,
                class_weight="balanced",
                ccp_alpha=0.0,
                complexity_rank=2,
            ),
            CandidateSpec(
                attempt_id=5,
                variant_name="counts_base",
                operating_point_label="class_weight='balanced' (recall)",
                description_es="3 conteos ESCO · Gini · balanced · hoja mín 5,000 (alta regularización)",
                criterion="gini",
                max_depth=4,
                min_samples_split=10000,
                min_samples_leaf=5000,
                class_weight="balanced",
                ccp_alpha=0.0,
                complexity_rank=1,
            ),
            CandidateSpec(
                attempt_id=6,
                variant_name="counts_base",
                operating_point_label="class_weight='balanced' (recall)",
                description_es="3 conteos ESCO · Entropy · balanced · hoja mín 2,500",
                criterion="entropy",
                max_depth=4,
                min_samples_split=5000,
                min_samples_leaf=2500,
                class_weight="balanced",
                ccp_alpha=0.0,
                complexity_rank=2,
            ),
            CandidateSpec(
                attempt_id=7,
                variant_name="counts_with_sin_tipo",
                operating_point_label="class_weight='balanced' (recall)",
                description_es="4 conteos ESCO (incluyendo n_skills_sin_tipo) · Gini · balanced · hoja mín 2,500",
                criterion="gini",
                max_depth=4,
                min_samples_split=5000,
                min_samples_leaf=2500,
                class_weight="balanced",
                ccp_alpha=0.0,
                complexity_rank=3,
            ),
            CandidateSpec(
                attempt_id=8,
                variant_name="counts_plus_shares",
                operating_point_label="class_weight='balanced' (recall)",
                description_es="Conteos ESCO + proporciones (competence/essential, knowledge/essential, razón, dif) · Gini · balanced · hoja mín 2,500",
                criterion="gini",
                max_depth=4,
                min_samples_split=5000,
                min_samples_leaf=2500,
                class_weight="balanced",
                ccp_alpha=0.0,
                complexity_rank=4,
            ),
            CandidateSpec(
                attempt_id=9,
                variant_name="counts_plus_shares",
                operating_point_label="class_weight=None (exactitud)",
                description_es="Conteos ESCO + proporciones · Gini · sin pesos · hoja mín 2,500",
                criterion="gini",
                max_depth=4,
                min_samples_split=5000,
                min_samples_leaf=2500,
                class_weight=None,
                ccp_alpha=0.0,
                complexity_rank=4,
            ),
            CandidateSpec(
                attempt_id=10,
                variant_name="counts_plus_shares",
                operating_point_label="class_weight='balanced' (recall)",
                description_es="Conteos ESCO + proporciones · Entropy · balanced · hoja mín 2,500 · ccp_alpha=5e-5",
                criterion="entropy",
                max_depth=4,
                min_samples_split=5000,
                min_samples_leaf=2500,
                class_weight="balanced",
                ccp_alpha=5e-5,
                complexity_rank=3,
            ),
        ]

    raise ValueError(f"Unknown block_id: {block_id}")


def instantiate_builder(block_id: str, variant_name: str) -> BlockFeatureBuilder:
    """Factory helper returning the appropriate BlockFeatureBuilder instance."""
    if block_id == BLOCK_ISCO:
        return ISCOBlockBuilder(granularity=variant_name)
    if block_id == BLOCK_EDUCATION:
        return EducationBlockBuilder(encoding_mode=variant_name)
    if block_id == BLOCK_SKILLS:
        return SkillsBlockBuilder(feature_set=variant_name)
    raise ValueError(f"Unknown block_id: {block_id}")


def instantiate_tree_from_spec(spec: CandidateSpec, random_state: int) -> DecisionTreeClassifier:
    """Create a DecisionTreeClassifier enforcing max_depth <= 4."""
    if spec.max_depth is None or spec.max_depth > 4:
        raise ValueError(f"Hard constraint violation: max_depth={spec.max_depth} exceeds 4!")
    return DecisionTreeClassifier(
        criterion=spec.criterion,
        max_depth=spec.max_depth,
        min_samples_split=spec.min_samples_split,
        min_samples_leaf=spec.min_samples_leaf,
        class_weight=spec.class_weight,
        ccp_alpha=spec.ccp_alpha,
        random_state=random_state,
    )


def evaluate_predictions_with_auc(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_score: np.ndarray,
) -> Dict[str, float]:
    """Compute accuracy, class-1 precision, recall, F1, and ROC-AUC using fast exact confusion counts."""
    y_t = np.asarray(y_true, dtype="int8")
    y_p = np.asarray(y_pred, dtype="int8")
    n_tot = len(y_t)
    tp = int(((y_t == 1) & (y_p == 1)).sum())
    fp = int(((y_t == 0) & (y_p == 1)).sum())
    fn = int(((y_t == 1) & (y_p == 0)).sum())
    tn = n_tot - tp - fp - fn

    acc = float((tp + tn) / n_tot) if n_tot > 0 else 0.0
    prec_1 = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    rec_1 = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1_1 = float(2.0 * prec_1 * rec_1 / (prec_1 + rec_1)) if (prec_1 + rec_1) > 0 else 0.0
    auc = float(roc_auc_score(y_t, y_score))
    return {
        "accuracy": acc,
        "precision_1": prec_1,
        "recall_1": rec_1,
        "f1_1": f1_1,
        "roc_auc": auc,
    }


def _select_oof_threshold(
    y_true: np.ndarray,
    oof_proba_1: np.ndarray,
    baseline_acc: float,
) -> Tuple[float, Dict[str, float]]:
    """Choose threshold tau on OOF leaf class-1 probabilities subject to accuracy >= baseline_acc."""
    candidate_taus = np.linspace(0.30, 0.70, 81)
    best_tau = 0.50
    best_f1 = -1.0
    best_metrics: Dict[str, float] = {}

    y_t = np.asarray(y_true, dtype="int8")
    n_tot = float(len(y_t))
    pos_mask = y_t == 1
    neg_mask = ~pos_mask
    total_pos = int(pos_mask.sum())
    total_neg = int(neg_mask.sum())

    for tau in candidate_taus:
        pred_1 = oof_proba_1 >= tau
        tp = int((pred_1 & pos_mask).sum())
        fp = int((pred_1 & neg_mask).sum())
        fn = total_pos - tp
        tn = total_neg - fp
        acc_tau = float((tp + tn) / n_tot)
        if acc_tau + 1e-6 >= baseline_acc:
            prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
            rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
            f1_tau = float(2.0 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
            if f1_tau > best_f1:
                best_f1 = f1_tau
                best_tau = float(np.round(tau, 4))
                best_metrics = {
                    "accuracy": acc_tau,
                    "precision_1": prec,
                    "recall_1": rec,
                    "f1_1": f1_tau,
                }

    if not best_metrics:
        pred_1 = oof_proba_1 >= 0.50
        tp = int((pred_1 & pos_mask).sum())
        fp = int((pred_1 & neg_mask).sum())
        fn = total_pos - tp
        tn = total_neg - fp
        prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1_def = float(2.0 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        best_tau = 0.50
        best_metrics = {
            "accuracy": float((tp + tn) / n_tot),
            "precision_1": prec,
            "recall_1": rec,
            "f1_1": f1_def,
        }

    return best_tau, best_metrics


def tune_block_with_grouped_cv(
    block_id: str,
    version: str,
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    groups_train: pd.Series,
    config: DecisionTreeProjectConfig,
    precomputed_folds: Optional[List[Tuple[np.ndarray, np.ndarray]]] = None,
    locked_attempt_id: Optional[int] = None,
) -> BlockTuningResult:
    """Tune a tree block using GroupKFold on train (choosing by ROC-AUC + 1-SE rule) and log all 10 attempts."""
    specs = build_candidate_specs_for_block(block_id)[: config.max_tuning_attempts]
    version_label_es = VERSION_LABELS_ES.get(version, version)
    tree_question_es = BLOCK_METADATA_ES[block_id]["question_es"]

    if precomputed_folds is None:
        gkf = GroupKFold(n_splits=config.cv_folds)
        folds = list(gkf.split(df_train, y_train, groups=groups_train))
    else:
        folds = precomputed_folds

    variant_cache: Dict[str, Tuple[BlockFeatureBuilder, pd.DataFrame, pd.DataFrame]] = {}
    for spec in specs:
        if spec.variant_name not in variant_cache:
            builder = instantiate_builder(block_id, spec.variant_name)
            X_tr_var = builder.fit_transform(df_train)
            X_te_var = builder.transform(df_test)
            variant_cache[spec.variant_name] = (builder, X_tr_var, X_te_var)

    y_tr_arr = y_train.to_numpy(dtype="int8")
    y_te_arr = y_test.to_numpy(dtype="int8")
    baseline_train_acc = float((y_tr_arr == 0).mean())

    # Evaluate all 10 attempts in GroupKFold, slicing one fold at a time per variant (or reuse deterministic cached CV metrics if present)
    cv_summary_by_attempt: Dict[int, Dict[str, float]] = {}
    v_tag = "version_a" if version == "con_outliers" else "version_b"
    cache_csv_path = config.tables_dir / f"bitacora_intentos_{BLOCK_METADATA_ES[block_id]['short_name']}_{v_tag}.csv"

    if cache_csv_path.exists() and len(df_train) == 1391018:
        cached_df = pd.read_csv(cache_csv_path)
        if len(cached_df) == len(specs):
            for _, c_row in cached_df.iterrows():
                att_num = int(c_row["intento_num"])
                cv_summary_by_attempt[att_num] = {
                    "accuracy": float(c_row["cv_accuracy"]),
                    "precision_1": float(c_row["cv_precision_1"]),
                    "recall_1": float(c_row["cv_recall_1"]),
                    "f1_1": float(c_row["cv_f1_1"]),
                    "roc_auc": float(c_row["cv_roc_auc"]),
                    "roc_auc_std": float(c_row["cv_roc_auc_se"]) * float(np.sqrt(config.cv_folds)),
                    "roc_auc_se": float(c_row["cv_roc_auc_se"]),
                    "n_leaves": float(c_row["cv_hojas_media"]),
                }

    if len(cv_summary_by_attempt) != len(specs):
        for v_name, (_, X_tr_var, _) in variant_cache.items():
            X_tr_np = np.ascontiguousarray(X_tr_var.to_numpy(dtype="float32"))
            v_specs = [sp for sp in specs if sp.variant_name == v_name]
            fold_accum: Dict[int, List[Dict[str, float]]] = {sp.attempt_id: [] for sp in v_specs}

            for tr_idx, val_idx in folds:
                X_f_tr = X_tr_np[tr_idx]
                y_f_tr = y_tr_arr[tr_idx]
                X_f_val = X_tr_np[val_idx]
                y_f_val = y_tr_arr[val_idx]

                for sp in v_specs:
                    clf_fold = instantiate_tree_from_spec(sp, random_state=config.random_state)
                    clf_fold.fit(X_f_tr, y_f_tr)
                    val_pred = clf_fold.predict(X_f_val)
                    val_proba = clf_fold.predict_proba(X_f_val)[:, 1]
                    m_fold = evaluate_predictions_with_auc(y_f_val, val_pred, val_proba)
                    m_fold["n_leaves"] = float(clf_fold.get_n_leaves())
                    fold_accum[sp.attempt_id].append(m_fold)

            for sp in v_specs:
                f_list = fold_accum[sp.attempt_id]
                auc_vals = [m["roc_auc"] for m in f_list]
                auc_mean = float(np.mean(auc_vals))
                auc_std = float(np.std(auc_vals, ddof=1))
                auc_se = float(auc_std / np.sqrt(len(auc_vals)))
                cv_summary_by_attempt[sp.attempt_id] = {
                    "accuracy": float(np.mean([m["accuracy"] for m in f_list])),
                    "precision_1": float(np.mean([m["precision_1"] for m in f_list])),
                    "recall_1": float(np.mean([m["recall_1"] for m in f_list])),
                    "f1_1": float(np.mean([m["f1_1"] for m in f_list])),
                    "roc_auc": auc_mean,
                    "roc_auc_std": auc_std,
                    "roc_auc_se": auc_se,
                    "n_leaves": float(np.mean([m["n_leaves"] for m in f_list])),
                }

    # Select candidate by ROC-AUC + One-Standard-Error (1-SE) simplicity rule among primary-eligible specs
    eligible_specs = [sp for sp in specs if sp.is_primary_eligible]
    best_auc_spec = max(
        eligible_specs,
        key=lambda sp: round(cv_summary_by_attempt[sp.attempt_id]["roc_auc"], 5),
    )
    max_auc = cv_summary_by_attempt[best_auc_spec.attempt_id]["roc_auc"]
    max_auc_se = max(cv_summary_by_attempt[best_auc_spec.attempt_id]["roc_auc_se"], 0.0005)
    one_se_threshold = max_auc - max_auc_se

    if locked_attempt_id is not None:
        selected_spec = next(sp for sp in specs if sp.attempt_id == locked_attempt_id)
    else:
        within_1se = [
            sp
            for sp in eligible_specs
            if cv_summary_by_attempt[sp.attempt_id]["roc_auc"] >= (one_se_threshold - 1e-6)
        ]
        # Prefer simpler/more regularized tree (lower complexity_rank, higher min_samples_leaf, balanced operating point for main tree)
        selected_spec = min(
            within_1se,
            key=lambda sp: (
                sp.complexity_rank,
                0 if sp.class_weight == "balanced" else 1,
                -round(cv_summary_by_attempt[sp.attempt_id]["roc_auc"], 5),
            ),
        )

    # Build the paired operating-point specs (accuracy-oriented None and recall-oriented balanced) with identical variables & regularization
    spec_none = CandidateSpec(
        attempt_id=selected_spec.attempt_id,
        variant_name=selected_spec.variant_name,
        operating_point_label="class_weight=None (orientado a exactitud)",
        description_es=f"{selected_spec.description_es} [Punto: class_weight=None]",
        criterion=selected_spec.criterion,
        max_depth=selected_spec.max_depth,
        min_samples_split=selected_spec.min_samples_split,
        min_samples_leaf=selected_spec.min_samples_leaf,
        class_weight=None,
        ccp_alpha=selected_spec.ccp_alpha,
        complexity_rank=selected_spec.complexity_rank,
    )
    spec_balanced = CandidateSpec(
        attempt_id=selected_spec.attempt_id,
        variant_name=selected_spec.variant_name,
        operating_point_label="class_weight='balanced' (orientado a recall)",
        description_es=f"{selected_spec.description_es} [Punto: class_weight='balanced']",
        criterion=selected_spec.criterion,
        max_depth=selected_spec.max_depth,
        min_samples_split=selected_spec.min_samples_split,
        min_samples_leaf=selected_spec.min_samples_leaf,
        class_weight="balanced",
        ccp_alpha=selected_spec.ccp_alpha,
        complexity_rank=selected_spec.complexity_rank,
    )

    selected_builder, X_train_sel, X_test_sel = variant_cache[selected_spec.variant_name]
    X_tr_sel_np = np.ascontiguousarray(X_train_sel.to_numpy(dtype="float32"))

    # Compute OOF class-1 probabilities on train for the selected unweighted tree to choose threshold tau*
    oof_proba_1 = np.zeros(len(y_tr_arr), dtype="float32")
    for tr_idx, val_idx in folds:
        clf_oof = instantiate_tree_from_spec(spec_none, random_state=config.random_state)
        clf_oof.fit(X_tr_sel_np[tr_idx], y_tr_arr[tr_idx])
        oof_proba_1[val_idx] = clf_oof.predict_proba(X_tr_sel_np[val_idx])[:, 1]

    oof_tau, oof_tau_metrics = _select_oof_threshold(y_tr_arr, oof_proba_1, baseline_train_acc)

    # Fit both final operating-point trees ONCE on full train and evaluate ONCE on test
    tree_none = instantiate_tree_from_spec(spec_none, random_state=config.random_state)
    tree_none.fit(X_train_sel, y_tr_arr)

    tree_balanced = instantiate_tree_from_spec(spec_balanced, random_state=config.random_state)
    tree_balanced.fit(X_train_sel, y_tr_arr)

    # Evaluate test ONCE for the selected candidate to populate its log row
    tree_sel = tree_balanced if selected_spec.class_weight == "balanced" else tree_none
    test_pred_sel = tree_sel.predict(X_test_sel)
    test_proba_sel = tree_sel.predict_proba(X_test_sel)[:, 1]
    test_m_sel = evaluate_predictions_with_auc(y_te_arr, test_pred_sel, test_proba_sel)

    # Build the 10-row attempts log DataFrame
    log_rows = []
    for sp in specs:
        cv_m = cv_summary_by_attempt[sp.attempt_id]
        is_selected = sp.attempt_id == selected_spec.attempt_id
        within_1se_flag = cv_m["roc_auc"] >= (one_se_threshold - 1e-6)

        if is_selected:
            t_acc = round(test_m_sel["accuracy"], 4)
            t_prec = round(test_m_sel["precision_1"], 4)
            t_rec = round(test_m_sel["recall_1"], 4)
            t_f1 = round(test_m_sel["f1_1"], 4)
            t_auc = round(test_m_sel["roc_auc"], 4)
            decision_str = (
                f"SELECCIONADO por regla 1-SE en ROC-AUC CV "
                f"(ROC-AUC={cv_m['roc_auc']:.4f} ± {cv_m['roc_auc_se']:.4f}; hoja mín={sp.min_samples_leaf})"
            )
        else:
            t_acc = np.nan
            t_prec = np.nan
            t_rec = np.nan
            t_f1 = np.nan
            t_auc = np.nan
            if not sp.is_primary_eligible:
                decision_str = f"Descartado como principal ({sp.note_es})"
            elif not within_1se_flag:
                decision_str = (
                    f"Descartado en CV (ROC-AUC={cv_m['roc_auc']:.4f} inferior al umbral 1-SE={one_se_threshold:.4f})"
                )
            else:
                decision_str = (
                    "Descartado por regla 1-SE (se prefiere candidato más regularizado/simple dentro de 1 error estándar)"
                )

        log_rows.append(
            {
                "intento_id": f"{BLOCK_METADATA_ES[block_id]['short_name'].upper()}-{version[:3].upper()}-{sp.attempt_id:02d}",
                "intento_num": sp.attempt_id,
                "arbol_pregunta": tree_question_es,
                "version_datos": version_label_es,
                "variante_variables": sp.variant_name,
                "punto_operativo": sp.operating_point_label,
                "configuracion": sp.description_es,
                "criterion": sp.criterion,
                "max_depth": sp.max_depth,
                "min_samples_leaf": sp.min_samples_leaf,
                "ccp_alpha": sp.ccp_alpha,
                "cv_roc_auc": round(cv_m["roc_auc"], 4),
                "cv_roc_auc_se": round(cv_m["roc_auc_se"], 4),
                "cv_accuracy": round(cv_m["accuracy"], 4),
                "cv_precision_1": round(cv_m["precision_1"], 4),
                "cv_recall_1": round(cv_m["recall_1"], 4),
                "cv_f1_1": round(cv_m["f1_1"], 4),
                "cv_hojas_media": round(cv_m["n_leaves"], 1),
                "test_roc_auc": t_auc,
                "test_accuracy": t_acc,
                "test_precision_1": t_prec,
                "test_recall_1": t_rec,
                "test_f1_1": t_f1,
                "decision_y_razon": decision_str,
            }
        )

    attempts_log = pd.DataFrame(log_rows)

    return BlockTuningResult(
        block_id=block_id,
        version=version,
        version_label_es=version_label_es,
        selected_attempt_id=selected_spec.attempt_id,
        selected_spec=selected_spec,
        spec_accuracy_point=spec_none,
        spec_balanced_point=spec_balanced,
        fitted_builder=selected_builder,
        fitted_tree_none=tree_none,
        fitted_tree_balanced=tree_balanced,
        oof_threshold_tau=oof_tau,
        oof_threshold_metrics_train=oof_tau_metrics,
        X_train=X_train_sel,
        X_test=X_test_sel,
        attempts_log=attempts_log,
        best_cv_roc_auc=max_auc,
        best_cv_roc_auc_se=max_auc_se,
    )
