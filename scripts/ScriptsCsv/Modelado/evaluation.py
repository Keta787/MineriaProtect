"""Person-grouped cross-validation and imbalance-aware evaluation for Phase 4."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import StratifiedGroupKFold

from .config import ModelingConfig, VERSION_LABELS
from .dataset_builder import VersionModelingData


@dataclass(frozen=True)
class CurveData:
    """PR and ROC curve points on the test set for plotting."""

    version_label: str
    model_name: str
    precision: np.ndarray
    recall: np.ndarray
    pr_auc: float
    fpr: np.ndarray
    tpr: np.ndarray
    roc_auc: float


@dataclass(frozen=True)
class EvaluationBundle:
    """Tables and curves produced by Phase 4 modeling and evaluation."""

    ablation_table: pd.DataFrame
    cv_summary_table: pd.DataFrame
    test_summary_table: pd.DataFrame
    feature_importance_table: pd.DataFrame
    top_occupations_table: pd.DataFrame
    curves: List[CurveData]
    cv_leak_check: Dict[str, object]


class PersonGroupedEvaluator:
    """Evaluate models with StratifiedGroupKFold by resume_id and imbalance-sensitive metrics."""

    def __init__(self, config: ModelingConfig) -> None:
        self.config = config

    @staticmethod
    def _compute_metrics(y_true: np.ndarray, y_prob: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Compute imbalance-aware classification metrics."""
        return {
            "pr_auc": float(average_precision_score(y_true, y_prob)),
            "roc_auc": float(roc_auc_score(y_true, y_prob)),
            "f1_pos": float(f1_score(y_true, y_pred, pos_label=1, zero_division=0)),
            "recall_pos": float(recall_score(y_true, y_pred, pos_label=1, zero_division=0)),
            "precision_pos": float(precision_score(y_true, y_pred, pos_label=1, zero_division=0)),
            "balanced_acc": float(balanced_accuracy_score(y_true, y_pred)),
            "brier": float(brier_score_loss(y_true, y_prob)),
        }

    @staticmethod
    def _predict_proba_pos(model: object, X: object) -> np.ndarray:
        """Extract positive-class probability from a fitted estimator."""
        probs = model.predict_proba(X)
        if probs.ndim == 2 and probs.shape[1] > 1:
            return probs[:, 1]
        return probs.ravel()

    def _build_linear_estimator(self) -> SGDClassifier:
        return SGDClassifier(
            loss="log_loss",
            penalty="l2",
            alpha=1e-4,
            class_weight="balanced",
            max_iter=50,
            tol=1e-3,
            random_state=self.config.random_state,
        )

    def _build_hgb_estimator(self) -> HistGradientBoostingClassifier:
        return HistGradientBoostingClassifier(
            max_iter=120,
            learning_rate=0.08,
            max_leaf_nodes=31,
            min_samples_leaf=100,
            class_weight="balanced",
            random_state=self.config.random_state,
        )

    def run_ablation_on_version_a(self, data_a: VersionModelingData) -> Tuple[pd.DataFrame, Dict[str, object]]:
        """Compare 5-fold StratifiedGroupKFold metrics with leakage vs without leakage vs clean."""
        sgkf = StratifiedGroupKFold(
            n_splits=self.config.cv_folds,
            shuffle=True,
            random_state=self.config.random_state,
        )
        modes = [
            ("1. Con fuga (prohibido)", "with_leakage"),
            ("2. Sin fuga (2,983 cols)", "no_leakage"),
            ("3. Sin fuga + sin colinealidad (2,981 cols)", "clean"),
        ]
        rows = []
        fold_overlaps = 0

        for label, mode in modes:
            X_csr, names = data_a.train.build_sparse_matrix(mode=mode)
            y = data_a.train.y
            groups = data_a.train.groups
            fold_metrics = []

            for fold_idx, (tr_idx, va_idx) in enumerate(sgkf.split(X_csr, y, groups)):
                if mode == "clean":
                    overlap = len(set(groups[tr_idx]).intersection(set(groups[va_idx])))
                    fold_overlaps += overlap
                clf = self._build_linear_estimator()
                clf.fit(X_csr[tr_idx], y[tr_idx])
                y_prob = self._predict_proba_pos(clf, X_csr[va_idx])
                y_pred = (y_prob >= 0.5).astype(np.int8)
                fold_metrics.append(self._compute_metrics(y[va_idx], y_prob, y_pred))

            df_m = pd.DataFrame(fold_metrics)
            rows.append(
                {
                    "esquema_features": label,
                    "n_columnas": int(len(names)),
                    "pr_auc_cv_media": round(float(df_m["pr_auc"].mean()), 4),
                    "pr_auc_cv_std": round(float(df_m["pr_auc"].std()), 4),
                    "roc_auc_cv_media": round(float(df_m["roc_auc"].mean()), 4),
                    "f1_pos_cv_media": round(float(df_m["f1_pos"].mean()), 4),
                    "recall_pos_cv_media": round(float(df_m["recall_pos"].mean()), 4),
                    "precision_pos_cv_media": round(float(df_m["precision_pos"].mean()), 4),
                    "balanced_acc_cv_media": round(float(df_m["balanced_acc"].mean()), 4),
                }
            )

        cv_check = {
            "n_splits": self.config.cv_folds,
            "splitter": "StratifiedGroupKFold(group=resume_id)",
            "personas_solapadas_entre_folds": int(fold_overlaps),
        }
        return pd.DataFrame(rows), cv_check

    def evaluate_versions(
        self,
        data_a: VersionModelingData,
        data_b: VersionModelingData,
    ) -> EvaluationBundle:
        """Run full CV and test evaluation across Versions A and B and extract feature importance."""
        ablation_df, cv_check = self.run_ablation_on_version_a(data_a)

        sgkf = StratifiedGroupKFold(
            n_splits=self.config.cv_folds,
            shuffle=True,
            random_state=self.config.random_state,
        )

        cv_rows = []
        test_rows = []
        curves: List[CurveData] = []
        importance_rows = []
        top_occ_rows = []

        for version_key, vdata in [(data_a.version, data_a), (data_b.version, data_b)]:
            vlabel = VERSION_LABELS[version_key]
            X_tr_csr, sparse_names = vdata.train.build_sparse_matrix(mode="clean")
            X_te_csr, _ = vdata.test.build_sparse_matrix(mode="clean")
            X_tr_dense = vdata.train.dense_clean.to_numpy(dtype=np.float32)
            X_te_dense = vdata.test.dense_clean.to_numpy(dtype=np.float32)
            dense_names = list(vdata.train.dense_clean.columns)
            y_tr = vdata.train.y
            y_te = vdata.test.y
            groups_tr = vdata.train.groups

            model_specs = [
                ("Baseline (Prior)", DummyClassifier(strategy="prior"), "dense"),
                ("Logística Regularizada (OHE 2,981 cols)", self._build_linear_estimator(), "sparse"),
                ("HistGradientBoosting (14 cols densas)", self._build_hgb_estimator(), "dense"),
            ]

            for model_name, base_est, matrix_kind in model_specs:
                X_cv = X_tr_csr if matrix_kind == "sparse" else X_tr_dense
                X_eval_test = X_te_csr if matrix_kind == "sparse" else X_te_dense

                if version_key == data_a.version and matrix_kind == "sparse":
                    clean_ab = ablation_df.iloc[2]
                    cv_rows.append(
                        {
                            "version": vlabel,
                            "modelo": model_name,
                            "pr_auc_cv": float(clean_ab["pr_auc_cv_media"]),
                            "pr_auc_std": float(clean_ab["pr_auc_cv_std"]),
                            "roc_auc_cv": float(clean_ab["roc_auc_cv_media"]),
                            "f1_pos_cv": float(clean_ab["f1_pos_cv_media"]),
                            "recall_pos_cv": float(clean_ab["recall_pos_cv_media"]),
                            "precision_pos_cv": float(clean_ab["precision_pos_cv_media"]),
                            "balanced_acc_cv": float(clean_ab["balanced_acc_cv_media"]),
                        }
                    )
                else:
                    fold_scores = []
                    for tr_idx, va_idx in sgkf.split(X_cv, y_tr, groups_tr):
                        est = clone(base_est)
                        est.fit(X_cv[tr_idx], y_tr[tr_idx])
                        prob_va = self._predict_proba_pos(est, X_cv[va_idx])
                        pred_va = (prob_va >= 0.5).astype(np.int8)
                        fold_scores.append(self._compute_metrics(y_tr[va_idx], prob_va, pred_va))

                    df_folds = pd.DataFrame(fold_scores)
                    cv_rows.append(
                        {
                            "version": vlabel,
                            "modelo": model_name,
                            "pr_auc_cv": round(float(df_folds["pr_auc"].mean()), 4),
                            "pr_auc_std": round(float(df_folds["pr_auc"].std()), 4),
                            "roc_auc_cv": round(float(df_folds["roc_auc"].mean()), 4),
                            "f1_pos_cv": round(float(df_folds["f1_pos"].mean()), 4),
                            "recall_pos_cv": round(float(df_folds["recall_pos"].mean()), 4),
                            "precision_pos_cv": round(float(df_folds["precision_pos"].mean()), 4),
                            "balanced_acc_cv": round(float(df_folds["balanced_acc"].mean()), 4),
                        }
                    )

                # Fit on full train and evaluate once on test
                final_est = clone(base_est)
                final_est.fit(X_cv, y_tr)
                prob_te = self._predict_proba_pos(final_est, X_eval_test)
                pred_te = (prob_te >= 0.5).astype(np.int8)
                te_m = self._compute_metrics(y_te, prob_te, pred_te)

                test_rows.append(
                    {
                        "version": vlabel,
                        "modelo": model_name,
                        "pr_auc_test": round(te_m["pr_auc"], 4),
                        "roc_auc_test": round(te_m["roc_auc"], 4),
                        "f1_pos_test": round(te_m["f1_pos"], 4),
                        "recall_pos_test": round(te_m["recall_pos"], 4),
                        "precision_pos_test": round(te_m["precision_pos"], 4),
                        "balanced_acc_test": round(te_m["balanced_acc"], 4),
                        "brier_test": round(te_m["brier"], 4),
                    }
                )

                if model_name != "Baseline (Prior)":
                    prec, rec, _ = precision_recall_curve(y_te, prob_te)
                    fpr, tpr, _ = roc_curve(y_te, prob_te)
                    # Subsample curve arrays to at most 400 points for fast, clean plotting
                    pr_step = max(1, len(prec) // 400)
                    roc_step = max(1, len(fpr) // 400)
                    curves.append(
                        CurveData(
                            version_label=vlabel,
                            model_name=model_name,
                            precision=prec[::pr_step],
                            recall=rec[::pr_step],
                            pr_auc=te_m["pr_auc"],
                            fpr=fpr[::roc_step],
                            tpr=tpr[::roc_step],
                            roc_auc=te_m["roc_auc"],
                        )
                    )

                if matrix_kind == "sparse" and hasattr(final_est, "coef_"):
                    coefs = final_est.coef_.ravel()
                    n_dense = len(dense_names)
                    for idx, dname in enumerate(dense_names):
                        importance_rows.append(
                            {
                                "version": vlabel,
                                "variable": dname,
                                "coef_logistico": round(float(coefs[idx]), 4),
                                "abs_coef": round(float(abs(coefs[idx])), 4),
                                "direccion": (
                                    "Aumenta prob. de reincidir (+)"
                                    if coefs[idx] > 0
                                    else "Reduce prob. de reincidir (-)"
                                ),
                            }
                        )
                    if version_key == data_a.version:
                        occ_coefs = coefs[n_dense:]
                        occ_names = sparse_names[n_dense:]
                        top_idx = np.argsort(np.abs(occ_coefs))[::-1][:15]
                        for r_idx in top_idx:
                            top_occ_rows.append(
                                {
                                    "feature_ocupacion": occ_names[r_idx],
                                    "coef_logistico": round(float(occ_coefs[r_idx]), 4),
                                    "abs_coef": round(float(abs(occ_coefs[r_idx])), 4),
                                }
                            )

        imp_df = (
            pd.DataFrame(importance_rows)
            .sort_values(["version", "abs_coef"], ascending=[True, False])
            .reset_index(drop=True)
        )
        return EvaluationBundle(
            ablation_table=ablation_df,
            cv_summary_table=pd.DataFrame(cv_rows),
            test_summary_table=pd.DataFrame(test_rows),
            feature_importance_table=imp_df,
            top_occupations_table=pd.DataFrame(top_occ_rows),
            curves=curves,
            cv_leak_check=cv_check,
        )

