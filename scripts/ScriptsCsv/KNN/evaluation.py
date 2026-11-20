"""Person-level subsampling, grouped-CV honest tuning, learning curves, OOF threshold, test eval & fair comparisons."""

from __future__ import annotations

from dataclasses import dataclass
import gc
import hashlib
import json
from pathlib import Path
import time
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.calibration import calibration_curve
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.neighbors import KNeighborsClassifier

from scripts.ScriptsCsv.Modelado.dataset_builder import VersionModelingData
from scripts.ScriptsCsv.NaiveBayes.config import NaiveBayesConfig
from scripts.ScriptsCsv.NaiveBayes.evaluation import (
    ModelCurveBundle,
    bootstrap_person_metrics,
    compute_classification_metrics,
    compute_equal_alert_rate_cutoff,
    compute_matrix_memory_mb,
    paired_bootstrap_person_diffs,
    select_oof_threshold_from_proba,
)
from scripts.ScriptsCsv.NaiveBayes.feature_blocks import NaiveBayesFeatureBuilder
from scripts.ScriptsCsv.NaiveBayes.models import HybridNaiveBayes, build_bernoulli_nb
from scripts.ScriptsCsv.NaiveBayes.pipeline import current_process_rss_mb

from .chunked_predictor import ChunkedKNNPredictor, ChunkedPredictResult
from .config import (
    EXTENDED_BLOCK_WEIGHT_LOWER,
    EXTENDED_BLOCK_WEIGHT_UPPER,
    EXTENDED_K_UPPER_VALUES,
    KNNConfig,
    MODEL_KNN_D,
    MODEL_KNN_G,
    MODEL_KNN_W,
    MODEL_LABELS_ES,
    MODEL_ORDER,
)
from .feature_blocks import KNNPartitionBlocks
from .models import KNNModelSpec, build_knn_classifier


def proba_from_kneighbors(
    distances: np.ndarray,
    indices: np.ndarray,
    y_train_fold: np.ndarray,
    k: int,
    weights: str,
) -> np.ndarray:
    """Compute exact sklearn KNeighborsClassifier class-1 probability from precomputed top-k_max neighbors.

    Mathematically identical to KNeighborsClassifier(n_neighbors=k, weights=weights).predict_proba()[:, 1],
    including exact handling of zero-distance ties under weights='distance'.
    """
    d_k = np.asarray(distances[:, :k], dtype=np.float64)
    idx_k = indices[:, :k]
    y_k = y_train_fold[idx_k].astype(np.float64, copy=False)

    if weights == "uniform":
        return np.mean(y_k, axis=1)

    if weights == "distance":
        with np.errstate(divide="ignore"):
            w = 1.0 / d_k
        inf_mask = np.isinf(w)
        has_inf = np.any(inf_mask, axis=1)
        if np.any(has_inf):
            w = w.copy()
            w[has_inf] = inf_mask[has_inf].astype(np.float64)
        denom = np.sum(w, axis=1)
        return np.sum(w * y_k, axis=1) / denom

    raise ValueError(f"Unsupported KNN weights mode: {weights}")


class PersonSubsampler:
    """Deterministic person-level subsampling preserving all rows of every sampled resume_id."""

    def __init__(self, random_state: int = 42) -> None:
        self.random_state = int(random_state)

    def sample_persons_nested(
        self,
        groups: np.ndarray,
        y: np.ndarray,
        fractions: Sequence[float],
    ) -> Dict[float, Tuple[np.ndarray, Dict[str, object]]]:
        """Create nested person-level subsamples (e.g. 10% subset of 25% subset of 50%) with prevalence audits."""
        groups_str = np.asarray(groups, dtype=str)
        unique_persons = np.unique(groups_str)
        n_total_persons = len(unique_persons)
        rng = np.random.default_rng(self.random_state)
        perm_persons = rng.permutation(unique_persons)
        overall_prev = float(np.mean(y)) * 100.0

        out: Dict[float, Tuple[np.ndarray, Dict[str, object]]] = {}
        for frac in sorted(set(float(f) for f in fractions)):
            if not (0.0 < frac <= 1.0):
                raise ValueError(f"Fraction must be in (0, 1], got {frac}")
            n_keep = max(5, int(round(frac * n_total_persons)))
            kept_persons = perm_persons[:n_keep]
            row_idx = np.flatnonzero(np.isin(groups_str, kept_persons))
            sub_y = y[row_idx]
            prev_pct = float(np.mean(sub_y)) * 100.0
            summary = {
                "fraccion_personas": frac,
                "personas_muestreadas": int(n_keep),
                "filas_muestreadas": int(len(row_idx)),
                "pct_filas_total": round(100.0 * len(row_idx) / float(len(y)), 2),
                "prevalencia_submuestra_pct": round(prev_pct, 2),
                "prevalencia_train_total_pct": round(overall_prev, 2),
                "brecha_prevalencia_pp": round(prev_pct - overall_prev, 3),
            }
            out[frac] = (row_idx, summary)
        return out


@dataclass(frozen=True)
class KNNTuningBundle:
    """Outputs of Section 7 (honest grouped-CV tuning on 10% person subsample + 25%/50% learning curve)."""

    subsample_summary_table: pd.DataFrame
    tuning_all_attempts_table: pd.DataFrame
    tuning_winners_table: pd.DataFrame
    score_resolution_table: pd.DataFrame
    learning_curve_table: pd.DataFrame
    learning_curve_knn_w_paired_table: pd.DataFrame
    winner_specs: Dict[str, KNNModelSpec]
    winner_oof_proba: Dict[str, np.ndarray]
    tuning_row_idx: np.ndarray
    tuning_y: np.ndarray
    tuning_groups: np.ndarray
    cv_person_overlap_count: int


@dataclass(frozen=True)
class KNNThresholdBundle:
    """Outputs of Section 10 (OOF threshold selection maximizing F1 + NB-H equal-alert-rate benchmark)."""

    oof_threshold_summary_table: pd.DataFrame
    oof_threshold_curves: Dict[str, pd.DataFrame]
    oof_thresholds_tau: Dict[str, float]
    nb_h_alert_rate_test: float


@dataclass(frozen=True)
class KNNTestEvaluationBundle:
    """Outputs of Sections 11, 12, and 14 (final test metrics, calibration, fair comparisons, and paired CIs)."""

    references_table: pd.DataFrame
    trees_reference_table: pd.DataFrame
    nb_reference_table: pd.DataFrame
    reproduced_baselines_table: pd.DataFrame
    test_metrics_table: pd.DataFrame
    confusion_matrices_table: pd.DataFrame
    calibration_summary_table: pd.DataFrame
    like_for_like_dense_table: pd.DataFrame
    like_for_like_occ_table: pd.DataFrame
    paired_bootstrap_table: pd.DataFrame
    equal_alert_rate_table: pd.DataFrame
    cost_comparison_table: pd.DataFrame
    final_unified_comparison_table: pd.DataFrame
    test_proba_by_model: Dict[str, np.ndarray]
    baseline_test_proba: Dict[str, np.ndarray]
    baseline_thresholds: Dict[str, float]
    chunked_results: Dict[str, ChunkedPredictResult]
    model_curves: Dict[str, ModelCurveBundle]
    eval_row_idx_test: np.ndarray
    is_full_test_evaluation: bool
    bootstrap_elapsed_s: float


class KNNEvaluator:
    """Run honest grouped-CV tuning, learning curves, OOF thresholding, final test evaluation, and fair comparisons."""

    def __init__(
        self,
        config: KNNConfig,
        chunked_predictor: ChunkedKNNPredictor | None = None,
    ) -> None:
        self.config = config
        self.chunked_predictor = chunked_predictor or ChunkedKNNPredictor(
            cache_root=config.cache_dir,
            chunk_size=config.chunk_size,
        )

    def load_external_reference_tables(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Read References 1-3, Version A Decision Trees (7.0), and Naive Bayes (7.1) CSVs dynamically."""
        for p in (
            self.config.references_csv_path,
            self.config.trees_comparison_csv_path,
            self.config.nb_test_metrics_csv_path,
        ):
            if not p.exists():
                raise FileNotFoundError(f"Required reference table not found: {p}")

        refs_df = pd.read_csv(self.config.references_csv_path, encoding="utf-8")
        trees_df = pd.read_csv(self.config.trees_comparison_csv_path, encoding="utf-8")
        nb_df = pd.read_csv(self.config.nb_test_metrics_csv_path, encoding="utf-8")

        if self.config.phase4_test_csv_path.exists():
            p4_df = pd.read_csv(self.config.phase4_test_csv_path, encoding="utf-8")
            log_a = p4_df.loc[
                p4_df["version"].astype(str).str.startswith("A")
                & p4_df["modelo"].astype(str).str.contains("Logística")
            ]
            if not log_a.empty:
                refs_df["test_pr_auc"] = [0.2997, 0.2997, float(log_a.iloc[0]["pr_auc_test"])]
                refs_df["test_brier_sin_ponderar"] = [0.2997, 0.7003, np.nan]

        trees_a_df = trees_df.loc[
            trees_df["version_datos"].astype(str).str.contains("CON outliers")
        ].reset_index(drop=True)
        return refs_df, trees_a_df, nb_df

    @staticmethod
    def _build_grouped_folds(
        y: np.ndarray,
        groups: np.ndarray,
        n_splits: int = 5,
        random_state: int = 42,
    ) -> Tuple[List[Tuple[np.ndarray, np.ndarray]], int]:
        """Build StratifiedGroupKFold splits and verify zero overlapping resume_id across folds."""
        sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
        dummy_x = np.zeros((len(y), 1), dtype=np.int8)
        folds: List[Tuple[np.ndarray, np.ndarray]] = []
        overlap = 0
        for tr_idx, va_idx in sgkf.split(dummy_x, y, groups):
            overlap += len(set(groups[tr_idx]).intersection(set(groups[va_idx])))
            folds.append((tr_idx, va_idx))
        if overlap != 0:
            raise AssertionError(f"Person overlap detected across CV folds: {overlap}")
        return folds, overlap

    @staticmethod
    def _evaluate_grid_for_single_space(
        X_sub: np.ndarray | sparse.csr_matrix,
        y_sub: np.ndarray,
        folds: List[Tuple[np.ndarray, np.ndarray]],
        model_id: str,
        algorithm: str,
        metric: str,
        block_weight: float,
        k_values: Sequence[int],
        weights_values: Sequence[str],
        n_jobs: int,
        stage_label: str,
        cache_dir: Path | None = None,
        force_recompute: bool = False,
        verbose: bool = False,
    ) -> Tuple[List[Dict[str, object]], Dict[Tuple[int, str], np.ndarray]]:
        """Query k_max neighbors once per fold and evaluate all (k, weights) combinations identically to sklearn.

        Supports optional per-fold disk caching under cache_dir so expensive CV folds resume cleanly.
        """
        k_sorted = sorted(set(int(k) for k in k_values))
        weights_tuple = tuple(str(w) for w in weights_values)
        k_max = max(k_sorted)

        sig_payload = {
            "model_id": model_id,
            "algorithm": algorithm,
            "metric": metric,
            "block_weight": round(float(block_weight), 6),
            "k_sorted": k_sorted,
            "weights": list(weights_tuple),
            "n_rows": int(len(y_sub)),
            "n_cols": int(X_sub.shape[1]),
            "n_folds": len(folds),
            "stage_label": stage_label,
        }
        sig = hashlib.sha256(
            json.dumps(sig_payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
        ).hexdigest()[:16]

        space_cache_dir: Path | None = None
        summary_cache_path: Path | None = None
        oof_cache_path: Path | None = None
        if cache_dir is not None:
            space_cache_dir = Path(cache_dir) / f"{model_id.lower().replace('-', '_')}_{metric}_bw{block_weight:g}_{sig}"
            space_cache_dir.mkdir(parents=True, exist_ok=True)
            summary_cache_path = space_cache_dir / "summary.json"
            oof_cache_path = space_cache_dir / "oof_probas.npz"
            if (not force_recompute) and summary_cache_path.exists() and oof_cache_path.exists():
                cached_rows = json.loads(summary_cache_path.read_text(encoding="utf-8"))
                npz = np.load(oof_cache_path)
                cached_oof: Dict[Tuple[int, str], np.ndarray] = {}
                all_present = True
                for k in k_sorted:
                    for wt in weights_tuple:
                        np_key = f"k{k}_{wt}"
                        if np_key not in npz:
                            all_present = False
                            break
                        cached_oof[(k, wt)] = npz[np_key].astype(np.float64, copy=False)
                if all_present:
                    return cached_rows, cached_oof

        oof_by_kw: Dict[Tuple[int, str], np.ndarray] = {
            (k, wt): np.zeros(len(y_sub), dtype=np.float64)
            for k in k_sorted
            for wt in weights_tuple
        }
        fold_query_times: List[float] = []

        for fold_idx, (tr_idx, va_idx) in enumerate(folds):
            fold_cache_file = (
                space_cache_dir / f"fold_{fold_idx}.npz" if space_cache_dir is not None else None
            )
            fold_time_file = (
                space_cache_dir / f"fold_{fold_idx}_time.txt" if space_cache_dir is not None else None
            )

            loaded_fold = False
            if (
                not force_recompute
                and fold_cache_file is not None
                and fold_cache_file.exists()
                and fold_time_file is not None
                and fold_time_file.exists()
            ):
                fnz = np.load(fold_cache_file)
                if all(f"k{k}_{wt}" in fnz for k in k_sorted for wt in weights_tuple):
                    for k in k_sorted:
                        for wt in weights_tuple:
                            oof_by_kw[(k, wt)][va_idx] = fnz[f"k{k}_{wt}"]
                    fold_query_times.append(float(fold_time_file.read_text(encoding="utf-8").strip()))
                    loaded_fold = True

            if loaded_fold:
                continue

            est = build_knn_classifier(
                KNNModelSpec(
                    model_id=model_id,
                    n_neighbors=k_max,
                    weights="uniform",
                    metric=metric,
                    algorithm=algorithm,
                    block_weight=block_weight,
                    n_jobs=n_jobs,
                )
            )
            t0 = time.perf_counter()
            est.fit(X_sub[tr_idx], y_sub[tr_idx])
            dists, idxs = est.kneighbors(X_sub[va_idx], n_neighbors=k_max, return_distance=True)
            dt_fold = time.perf_counter() - t0
            fold_query_times.append(dt_fold)

            y_fold_tr = y_sub[tr_idx]
            fold_payload: Dict[str, np.ndarray] = {}
            for k in k_sorted:
                for wt in weights_tuple:
                    p_va = proba_from_kneighbors(
                        distances=dists,
                        indices=idxs,
                        y_train_fold=y_fold_tr,
                        k=k,
                        weights=wt,
                    )
                    oof_by_kw[(k, wt)][va_idx] = p_va
                    fold_payload[f"k{k}_{wt}"] = p_va.astype(np.float32)

            if fold_cache_file is not None and fold_time_file is not None:
                np.savez_compressed(fold_cache_file, **fold_payload)
                fold_time_file.write_text(f"{dt_fold:.6f}", encoding="utf-8")

            if verbose and dt_fold >= 15.0:
                print(
                    f"    [{model_id} {metric} bw={block_weight:g}] fold {fold_idx + 1}/{len(folds)} "
                    f"completado en {dt_fold:.1f}s | RSS={current_process_rss_mb():.0f} MB",
                    flush=True,
                )

        mean_fold_s = float(np.mean(fold_query_times))
        rows: List[Dict[str, object]] = []
        for k in k_sorted:
            for wt in weights_tuple:
                oof_p = oof_by_kw[(k, wt)]
                fold_metrics = [
                    compute_classification_metrics(y_sub[va_idx], oof_p[va_idx], threshold=0.50)
                    for _, va_idx in folds
                ]
                df_f = pd.DataFrame(fold_metrics)
                n_uniq_oof = int(len(np.unique(np.round(oof_p, 6))))
                rows.append(
                    {
                        "modelo_id": model_id,
                        "etapa_rejilla": stage_label,
                        "algoritmo": algorithm,
                        "metrica": metric,
                        "peso_bloque": round(float(block_weight), 4),
                        "k_vecinos": int(k),
                        "pesos": wt,
                        "resolucion_teorica_1_sobre_k": round(1.0 / float(k), 5),
                        "puntajes_unicos_oof": n_uniq_oof,
                        "pr_auc_cv_media": round(float(df_f["pr_auc"].mean()), 5),
                        "pr_auc_cv_std": round(float(df_f["pr_auc"].std()), 5),
                        "roc_auc_cv_media": round(float(df_f["roc_auc"].mean()), 5),
                        "roc_auc_cv_std": round(float(df_f["roc_auc"].std()), 5),
                        "f1_cv_050": round(float(df_f["f1_pos"].mean()), 4),
                        "recall_cv_050": round(float(df_f["recall_pos"].mean()), 4),
                        "precision_cv_050": round(float(df_f["precision_pos"].mean()), 4),
                        "brier_cv": round(float(df_f["brier"].mean()), 4),
                        "tiempo_fold_kmax_s": round(mean_fold_s, 3),
                    }
                )

        if summary_cache_path is not None and oof_cache_path is not None:
            summary_cache_path.write_text(
                json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            np.savez_compressed(
                oof_cache_path,
                **{f"k{k}_{wt}": oof_by_kw[(k, wt)].astype(np.float32) for k in k_sorted for wt in weights_tuple},
            )
        return rows, oof_by_kw

    def run_honest_tuning_and_learning_curve(
        self,
        train_blocks: KNNPartitionBlocks,
        selected_algorithms: Dict[str, str],
        selected_n_jobs: int,
        tuning_fraction: float | None = None,
        learning_curve_fractions: Sequence[float] | None = None,
        extend_edges: bool = True,
        force_recompute_cache: bool = False,
        verbose: bool = True,
    ) -> KNNTuningBundle:
        """Section 7: 5-fold grouped CV tuning on person subsample + grid-edge extension + 25%/50% learning curves."""
        t_frac = float(tuning_fraction or self.config.tuning_person_fraction)
        lc_fracs = tuple(learning_curve_fractions or self.config.learning_curve_fractions)
        all_fracs = sorted(set((t_frac,) + lc_fracs))
        tuning_cache_dir = self.config.cache_dir / "tuning_cv"
        tuning_cache_dir.mkdir(parents=True, exist_ok=True)

        subsampler = PersonSubsampler(random_state=self.config.random_state)
        nested = subsampler.sample_persons_nested(
            groups=train_blocks.groups,
            y=train_blocks.y,
            fractions=all_fracs,
        )
        subsample_summary_df = pd.DataFrame([nested[f][1] for f in all_fracs])

        tun_idx, _ = nested[t_frac]
        y_tun = train_blocks.y[tun_idx]
        g_tun = train_blocks.groups[tun_idx]
        folds_tun, overlap_cnt = self._build_grouped_folds(
            y_tun, g_tun, n_splits=self.config.cv_folds, random_state=self.config.random_state
        )

        all_rows: List[Dict[str, object]] = []
        oof_store: Dict[Tuple[str, str, float, int, str], np.ndarray] = {}

        def _build_matrix(model_id: str, bw: float, idx: np.ndarray) -> np.ndarray | sparse.csr_matrix:
            if model_id == MODEL_KNN_D:
                return train_blocks.build_knn_d_matrix(idx)
            if model_id == MODEL_KNN_G:
                return train_blocks.build_knn_g_matrix(w_g=bw, row_idx=idx)
            return train_blocks.build_knn_w_matrix(w=bw, row_idx=idx)

        def _run_space(
            model_id: str,
            metric: str,
            bw: float,
            k_vals: Sequence[int],
            stage_lbl: str,
        ) -> None:
            algo = selected_algorithms[model_id]
            X_sub = _build_matrix(model_id, bw, tun_idx)
            t0 = time.perf_counter()
            rows, oof_kw = self._evaluate_grid_for_single_space(
                X_sub=X_sub,
                y_sub=y_tun,
                folds=folds_tun,
                model_id=model_id,
                algorithm=algo,
                metric=metric,
                block_weight=bw,
                k_values=k_vals,
                weights_values=self.config.weights_grid,
                n_jobs=selected_n_jobs,
                stage_label=stage_lbl,
                cache_dir=tuning_cache_dir,
                force_recompute=force_recompute_cache,
                verbose=verbose,
            )
            all_rows.extend(rows)
            for (k_val, wt), oof_vec in oof_kw.items():
                oof_store[(model_id, metric, round(float(bw), 4), int(k_val), wt)] = oof_vec
            if verbose:
                best_pr = max(r["pr_auc_cv_media"] for r in rows)
                print(
                    f"[Tuning {model_id}] {stage_lbl} | metric={metric} | bw={bw:g} | "
                    f"max_k={max(k_vals)} | best PR-AUC={best_pr:.5f} | {time.perf_counter()-t0:.1f}s",
                    flush=True,
                )

        # Base grid across KNN-D, KNN-G, KNN-W
        for metric in self.config.dense_metrics_grid:
            _run_space(MODEL_KNN_D, metric, 0.0, self.config.k_grid, "Rejilla base")

        for metric in self.config.dense_metrics_grid:
            for w_g in self.config.block_weight_grid:
                _run_space(MODEL_KNN_G, metric, float(w_g), self.config.k_grid, "Rejilla base")

        for metric in self.config.sparse_metrics_grid:
            for w in self.config.block_weight_grid:
                _run_space(MODEL_KNN_W, metric, float(w), self.config.k_grid, "Rejilla base")

        # Check grid edges and extend if an optimum landed on k_max or block-weight edge
        if extend_edges:
            df_tmp = pd.DataFrame(all_rows)
            max_base_k = max(self.config.k_grid)
            min_base_w = min(self.config.block_weight_grid)
            max_base_w = max(self.config.block_weight_grid)

            for model_id in MODEL_ORDER:
                sub_m = df_tmp.loc[df_tmp["modelo_id"] == model_id].sort_values(
                    ["pr_auc_cv_media", "roc_auc_cv_media"], ascending=[False, False]
                )
                top = sub_m.iloc[0]
                best_metric = str(top["metrica"])
                best_bw = float(top["peso_bloque"])
                best_k = int(top["k_vecinos"])

                if best_k == max_base_k:
                    _run_space(
                        model_id,
                        best_metric,
                        best_bw,
                        EXTENDED_K_UPPER_VALUES,
                        "Extensión de borde (k superior)",
                    )
                if model_id in (MODEL_KNN_G, MODEL_KNN_W):
                    if np.isclose(best_bw, min_base_w):
                        for extra_w in EXTENDED_BLOCK_WEIGHT_LOWER:
                            k_ext = self.config.k_grid + (
                                EXTENDED_K_UPPER_VALUES if best_k == max_base_k else ()
                            )
                            _run_space(
                                model_id,
                                best_metric,
                                float(extra_w),
                                k_ext,
                                "Extensión de borde (peso inferior)",
                            )
                    elif np.isclose(best_bw, max_base_w):
                        for extra_w in EXTENDED_BLOCK_WEIGHT_UPPER:
                            k_ext = self.config.k_grid + (
                                EXTENDED_K_UPPER_VALUES if best_k == max_base_k else ()
                            )
                            _run_space(
                                model_id,
                                best_metric,
                                float(extra_w),
                                k_ext,
                                "Extensión de borde (peso superior)",
                            )

        attempts_df = (
            pd.DataFrame(all_rows)
            .drop_duplicates(subset=["modelo_id", "metrica", "peso_bloque", "k_vecinos", "pesos"])
            .sort_values(["modelo_id", "pr_auc_cv_media", "roc_auc_cv_media"], ascending=[True, False, False])
            .reset_index(drop=True)
        )
        attempts_df.insert(1, "intento_num", attempts_df.groupby("modelo_id").cumcount() + 1)

        winner_rows: List[Dict[str, object]] = []
        winner_specs: Dict[str, KNNModelSpec] = {}
        winner_oof: Dict[str, np.ndarray] = {}
        top3_by_model: Dict[str, List[Dict[str, object]]] = {}

        for model_id in MODEL_ORDER:
            sub_m = attempts_df.loc[attempts_df["modelo_id"] == model_id].sort_values(
                ["pr_auc_cv_media", "roc_auc_cv_media"], ascending=[False, False]
            )
            top = sub_m.iloc[0]
            top3_by_model[model_id] = sub_m.head(3).to_dict(orient="records")
            key = (
                model_id,
                str(top["metrica"]),
                round(float(top["peso_bloque"]), 4),
                int(top["k_vecinos"]),
                str(top["pesos"]),
            )
            winner_oof[model_id] = oof_store[key]
            winner_specs[model_id] = KNNModelSpec(
                model_id=model_id,
                n_neighbors=int(top["k_vecinos"]),
                weights=str(top["pesos"]),
                metric=str(top["metrica"]),
                algorithm=selected_algorithms[model_id],
                block_weight=float(top["peso_bloque"]),
                n_jobs=selected_n_jobs,
            )
            winner_rows.append(
                {
                    "modelo_id": model_id,
                    "modelo": MODEL_LABELS_ES[model_id],
                    "algoritmo": selected_algorithms[model_id],
                    "metrica_optima": str(top["metrica"]),
                    "peso_bloque_optimo": round(float(top["peso_bloque"]), 4),
                    "k_optimo": int(top["k_vecinos"]),
                    "pesos_optimos": str(top["pesos"]),
                    "etapa_ganadora": str(top["etapa_rejilla"]),
                    "pr_auc_cv_media": float(top["pr_auc_cv_media"]),
                    "pr_auc_cv_std": float(top["pr_auc_cv_std"]),
                    "roc_auc_cv_media": float(top["roc_auc_cv_media"]),
                    "roc_auc_cv_std": float(top["roc_auc_cv_std"]),
                    "f1_cv_050": float(top["f1_cv_050"]),
                    "brier_cv": float(top["brier_cv"]),
                    "puntajes_unicos_oof": int(top["puntajes_unicos_oof"]),
                }
            )
        winners_df = pd.DataFrame(winner_rows)

        # Score resolution summary table (1/k effect across k values for winning metric/bw of each variant)
        res_rows: List[Dict[str, object]] = []
        for model_id in MODEL_ORDER:
            sp = winner_specs[model_id]
            sub_res = attempts_df.loc[
                (attempts_df["modelo_id"] == model_id)
                & (attempts_df["metrica"] == sp.metric)
                & (np.isclose(attempts_df["peso_bloque"], sp.block_weight))
            ].sort_values(["pesos", "k_vecinos"])
            for _, r in sub_res.iterrows():
                res_rows.append(
                    {
                        "modelo_id": model_id,
                        "pesos": str(r["pesos"]),
                        "k_vecinos": int(r["k_vecinos"]),
                        "resolucion_1_sobre_k": float(r["resolucion_teorica_1_sobre_k"]),
                        "puntajes_unicos_oof": int(r["puntajes_unicos_oof"]),
                        "pr_auc_cv_media": float(r["pr_auc_cv_media"]),
                        "roc_auc_cv_media": float(r["roc_auc_cv_media"]),
                        "brier_cv": float(r["brier_cv"]),
                    }
                )
        score_res_df = pd.DataFrame(res_rows)

        # Learning curve: repeat top-3 configs per variant at each fraction in lc_fracs (e.g. 10%, 25%, 50%)
        # - KNN-D and KNN-G: full 5-fold StratifiedGroupKFold at 10%, 25%, and 50%.
        # - KNN-W (sparse brute): SAME single person-disjoint validation holdout (fold 0 of 10% tuning ~28k rows)
        #   evaluated identically at 10%, 25%, and 50% (same protocol across all 3 points!), with person-level
        #   bootstrap 95% CIs and paired bootstrap comparisons among top-3 configs on that exact fold.
        #   Note: Primary 10% tuning (winners) and Section 10 OOF threshold remain strictly from full 5-fold CV.
        val_holdout_global_idx = tun_idx[folds_tun[0][1]]
        val_holdout_persons = set(train_blocks.groups[val_holdout_global_idx].tolist())
        y_val_holdout = train_blocks.y[val_holdout_global_idx]
        g_val_holdout = train_blocks.groups[val_holdout_global_idx]

        lc_rows: List[Dict[str, object]] = []
        knn_w_holdout_probas: Dict[Tuple[float, int], Tuple[str, np.ndarray]] = {}
        knn_w_paired_rows: List[Dict[str, object]] = []

        for frac in lc_fracs:
            lc_idx, lc_meta = nested[frac]
            y_lc = train_blocks.y[lc_idx]
            g_lc = train_blocks.groups[lc_idx]
            folds_lc, _ = self._build_grouped_folds(
                y_lc, g_lc, n_splits=self.config.cv_folds, random_state=self.config.random_state
            )

            for model_id in MODEL_ORDER:
                top3 = top3_by_model[model_id]
                # Group top-3 configs by (metric, block_weight) so we reuse kneighbors calls!
                grouped_cfg: Dict[Tuple[str, float], List[Tuple[int, int, str]]] = {}
                for rank_pos, cfg_row in enumerate(top3, start=1):
                    gkey = (str(cfg_row["metrica"]), round(float(cfg_row["peso_bloque"]), 4))
                    grouped_cfg.setdefault(gkey, []).append(
                        (rank_pos, int(cfg_row["k_vecinos"]), str(cfg_row["pesos"]))
                    )

                for (metric, bw), items in grouped_cfg.items():
                    if model_id == MODEL_KNN_W:
                        # Identical single person-disjoint validation fold protocol across 10%, 25%, AND 50%
                        tr_disjoint_mask = ~np.isin(train_blocks.groups[lc_idx], list(val_holdout_persons))
                        tr_pool_global_idx = lc_idx[tr_disjoint_mask]
                        y_tr_pool = train_blocks.y[tr_pool_global_idx]
                        # Verify zero person overlap between training pool and validation holdout
                        if len(set(train_blocks.groups[tr_pool_global_idx]).intersection(val_holdout_persons)) != 0:
                            raise AssertionError("Person overlap detected in KNN-W learning-curve holdout!")

                        k_needed = sorted(set(k_v for _, k_v, _ in items))
                        wt_needed = sorted(set(wt_v for _, _, wt_v in items))
                        k_max_lc = max(k_needed)

                        sig_lc = hashlib.sha256(
                            json.dumps(
                                {
                                    "schema": "lc_v2_same_fold_bootstrap",
                                    "model_id": model_id,
                                    "frac": round(float(frac), 4),
                                    "metric": metric,
                                    "bw": round(float(bw), 4),
                                    "k_needed": k_needed,
                                    "wt_needed": wt_needed,
                                    "n_tr": int(len(tr_pool_global_idx)),
                                    "n_va": int(len(val_holdout_global_idx)),
                                },
                                sort_keys=True,
                            ).encode("utf-8")
                        ).hexdigest()[:16]
                        lc_cache_json = tuning_cache_dir / f"lc_v2_knn_w_f{int(round(100*frac))}_bw{bw:g}_{sig_lc}.json"
                        lc_cache_npz = tuning_cache_dir / f"lc_v2_knn_w_f{int(round(100*frac))}_bw{bw:g}_{sig_lc}.npz"

                        if (not force_recompute_cache) and lc_cache_json.exists() and lc_cache_npz.exists():
                            cached_lc_rows = json.loads(lc_cache_json.read_text(encoding="utf-8"))
                            npz_lc = np.load(lc_cache_npz)
                            lc_rows.extend(cached_lc_rows)
                            for rank_pos, k_v, wt_v in items:
                                cfg_lbl = f"k={k_v}, {wt_v}, {metric}, w={bw:g}"
                                knn_w_holdout_probas[(frac, rank_pos)] = (
                                    cfg_lbl,
                                    npz_lc[f"r{rank_pos}"].astype(np.float64, copy=False),
                                )
                        else:
                            # At 10%, tr_pool_global_idx == tun_idx[folds_tun[0][0]], so fold-0 OOF already exists!
                            probas_by_rank: Dict[int, np.ndarray] = {}
                            if np.isclose(frac, t_frac):
                                for rank_pos, k_v, wt_v in items:
                                    full_oof_vec = oof_store[(model_id, metric, round(float(bw), 4), int(k_v), wt_v)]
                                    probas_by_rank[rank_pos] = full_oof_vec[folds_tun[0][1]].astype(np.float64, copy=True)
                            else:
                                X_tr_w = train_blocks.build_knn_w_matrix(w=bw, row_idx=tr_pool_global_idx)
                                X_va_w = train_blocks.build_knn_w_matrix(w=bw, row_idx=val_holdout_global_idx)
                                t0_lc = time.perf_counter()
                                est_lc = build_knn_classifier(
                                    KNNModelSpec(
                                        model_id=model_id,
                                        n_neighbors=k_max_lc,
                                        weights="uniform",
                                        metric=metric,
                                        algorithm="brute",
                                        block_weight=bw,
                                        n_jobs=selected_n_jobs,
                                    )
                                )
                                est_lc.fit(X_tr_w, y_tr_pool)
                                dists_lc, idxs_lc = est_lc.kneighbors(
                                    X_va_w, n_neighbors=k_max_lc, return_distance=True
                                )
                                for rank_pos, k_v, wt_v in items:
                                    probas_by_rank[rank_pos] = proba_from_kneighbors(
                                        dists_lc, idxs_lc, y_tr_pool, k=k_v, weights=wt_v
                                    )
                                if verbose:
                                    print(
                                        f"[LearningCurve KNN-W @ {int(round(100*frac))}% mismo pliegue] "
                                        f"bw={bw:g} n_tr={len(tr_pool_global_idx):,} in {time.perf_counter()-t0_lc:.1f}s",
                                        flush=True,
                                    )
                                del X_tr_w, X_va_w, est_lc
                                gc.collect()

                            new_lc_rows: List[Dict[str, object]] = []
                            npz_payload: Dict[str, np.ndarray] = {}
                            for rank_pos, k_v, wt_v in items:
                                p_va = probas_by_rank[rank_pos]
                                cfg_lbl = f"k={k_v}, {wt_v}, {metric}, w={bw:g}"
                                knn_w_holdout_probas[(frac, rank_pos)] = (cfg_lbl, p_va)
                                npz_payload[f"r{rank_pos}"] = p_va.astype(np.float32)

                                m_lc = compute_classification_metrics(y_val_holdout, p_va, threshold=0.50)
                                ci_lc = bootstrap_person_metrics(
                                    y_true=y_val_holdout,
                                    y_prob=p_va,
                                    groups=g_val_holdout,
                                    threshold=0.50,
                                    n_resamples=self.config.bootstrap_resamples,
                                    random_state=self.config.random_state,
                                )
                                new_lc_rows.append(
                                    {
                                        "modelo_id": model_id,
                                        "esquema_validacion": f"Pliegue único fijo disjunto ({len(y_val_holdout):,} filas · mismo protocolo 10/25/50 %)",
                                        "fraccion_personas_pct": round(100.0 * frac, 1),
                                        "personas_train": int(len(np.unique(train_blocks.groups[tr_pool_global_idx]))),
                                        "filas_train": int(len(tr_pool_global_idx)),
                                        "rango_en_10pct": int(rank_pos),
                                        "config_etiqueta": cfg_lbl,
                                        "k_vecinos": int(k_v),
                                        "pesos": wt_v,
                                        "metrica": metric,
                                        "peso_bloque": bw,
                                        "pr_auc_cv_media": round(float(m_lc["pr_auc"]), 5),
                                        "pr_auc_cv_std": np.nan,
                                        "pr_auc_ic95_persona": f"[{ci_lc['pr_auc'][0]:.5f}, {ci_lc['pr_auc'][1]:.5f}]",
                                        "pr_auc_ic95_inf": round(float(ci_lc["pr_auc"][0]), 5),
                                        "pr_auc_ic95_sup": round(float(ci_lc["pr_auc"][1]), 5),
                                        "roc_auc_cv_media": round(float(m_lc["roc_auc"]), 5),
                                        "roc_auc_ic95_persona": f"[{ci_lc['roc_auc'][0]:.5f}, {ci_lc['roc_auc'][1]:.5f}]",
                                        "brier_cv": round(float(m_lc["brier"]), 4),
                                    }
                                )
                            lc_cache_json.write_text(
                                json.dumps(new_lc_rows, indent=2, ensure_ascii=False), encoding="utf-8"
                            )
                            np.savez_compressed(lc_cache_npz, **npz_payload)
                            lc_rows.extend(new_lc_rows)
                    elif np.isclose(frac, t_frac):
                        # KNN-D and KNN-G at 10%: read directly from 5-fold CV attempts_df
                        for rank_pos, k_v, wt_v in items:
                            hit = attempts_df.loc[
                                (attempts_df["modelo_id"] == model_id)
                                & (attempts_df["metrica"] == metric)
                                & (np.isclose(attempts_df["peso_bloque"], bw))
                                & (attempts_df["k_vecinos"] == k_v)
                                & (attempts_df["pesos"] == wt_v)
                            ].iloc[0]
                            lc_rows.append(
                                {
                                    "modelo_id": model_id,
                                    "esquema_validacion": "StratifiedGroupKFold (5 pliegues)",
                                    "fraccion_personas_pct": round(100.0 * frac, 1),
                                    "personas_train": int(lc_meta["personas_muestreadas"]),
                                    "filas_train": int(lc_meta["filas_muestreadas"]),
                                    "rango_en_10pct": int(rank_pos),
                                    "config_etiqueta": f"k={k_v}, {wt_v}, {metric}"
                                    + (f", w={bw:g}" if model_id != MODEL_KNN_D else ""),
                                    "k_vecinos": int(k_v),
                                    "pesos": wt_v,
                                    "metrica": metric,
                                    "peso_bloque": bw,
                                    "pr_auc_cv_media": float(hit["pr_auc_cv_media"]),
                                    "pr_auc_cv_std": float(hit["pr_auc_cv_std"]),
                                    "pr_auc_ic95_persona": "5-fold CV (ver std)",
                                    "pr_auc_ic95_inf": np.nan,
                                    "pr_auc_ic95_sup": np.nan,
                                    "roc_auc_cv_media": float(hit["roc_auc_cv_media"]),
                                    "roc_auc_ic95_persona": "5-fold CV",
                                    "brier_cv": float(hit["brier_cv"]),
                                }
                            )
                    else:
                        k_needed = sorted(set(k_v for _, k_v, _ in items))
                        wt_needed = sorted(set(wt_v for _, _, wt_v in items))
                        X_lc = _build_matrix(model_id, bw, lc_idx)
                        algo_lc = (
                            "kd_tree"
                            if (model_id == MODEL_KNN_G and frac >= 0.25 and metric == "manhattan")
                            else selected_algorithms[model_id]
                        )
                        t0_lc = time.perf_counter()
                        sub_rows, _ = self._evaluate_grid_for_single_space(
                            X_sub=X_lc,
                            y_sub=y_lc,
                            folds=folds_lc,
                            model_id=model_id,
                            algorithm=algo_lc,
                            metric=metric,
                            block_weight=bw,
                            k_values=k_needed,
                            weights_values=wt_needed,
                            n_jobs=selected_n_jobs,
                            stage_label=f"Curva aprendizaje {int(round(100*frac))}%",
                            cache_dir=tuning_cache_dir,
                            force_recompute=force_recompute_cache,
                            verbose=verbose,
                        )
                        sub_df = pd.DataFrame(sub_rows)
                        for rank_pos, k_v, wt_v in items:
                            hit = sub_df.loc[
                                (sub_df["k_vecinos"] == k_v) & (sub_df["pesos"] == wt_v)
                            ].iloc[0]
                            lc_rows.append(
                                {
                                    "modelo_id": model_id,
                                    "esquema_validacion": "StratifiedGroupKFold (5 pliegues)",
                                    "fraccion_personas_pct": round(100.0 * frac, 1),
                                    "personas_train": int(lc_meta["personas_muestreadas"]),
                                    "filas_train": int(lc_meta["filas_muestreadas"]),
                                    "rango_en_10pct": int(rank_pos),
                                    "config_etiqueta": f"k={k_v}, {wt_v}, {metric}"
                                    + (f", w={bw:g}" if model_id != MODEL_KNN_D else ""),
                                    "k_vecinos": int(k_v),
                                    "pesos": wt_v,
                                    "metrica": metric,
                                    "peso_bloque": bw,
                                    "pr_auc_cv_media": float(hit["pr_auc_cv_media"]),
                                    "pr_auc_cv_std": float(hit["pr_auc_cv_std"]),
                                    "pr_auc_ic95_persona": "5-fold CV (ver std)",
                                    "pr_auc_ic95_inf": np.nan,
                                    "pr_auc_ic95_sup": np.nan,
                                    "roc_auc_cv_media": float(hit["roc_auc_cv_media"]),
                                    "roc_auc_ic95_persona": "5-fold CV",
                                    "brier_cv": float(hit["brier_cv"]),
                                }
                            )
                        if verbose:
                            print(
                                f"[LearningCurve {model_id} @ {int(round(100*frac))}%] "
                                f"metric={metric} bw={bw:g} algo={algo_lc} ({len(items)} cfgs) in {time.perf_counter()-t0_lc:.1f}s",
                                flush=True,
                            )
                        del X_lc
                        gc.collect()

            # Compute paired person-level bootstrap comparisons among KNN-W top-3 configs on this fraction's single fold
            if (frac, 1) in knn_w_holdout_probas:
                lbl1, p1 = knn_w_holdout_probas[(frac, 1)]
                for other_r in (2, 3):
                    if (frac, other_r) not in knn_w_holdout_probas:
                        continue
                    lbl_o, p_o = knn_w_holdout_probas[(frac, other_r)]
                    p_res = paired_bootstrap_person_diffs(
                        y_true=y_val_holdout,
                        prob_a=p1,
                        prob_b=p_o,
                        groups=g_val_holdout,
                        threshold_a=None,
                        threshold_b=None,
                        n_resamples=self.config.bootstrap_resamples,
                        random_state=self.config.random_state,
                    )
                    knn_w_paired_rows.append(
                        {
                            "fraccion_personas_pct": round(100.0 * frac, 1),
                            "n_val_pliegue_fijo": int(len(y_val_holdout)),
                            "personas_val_pliegue_fijo": int(len(val_holdout_persons)),
                            "comparacion_A_menos_B": f"Top 1 ({lbl1}) menos Top {other_r} ({lbl_o})",
                            "delta_pr_auc": round(float(p_res["delta_pr_auc"]), 5),
                            "ic95_delta_pr_auc": f"[{float(p_res['delta_pr_auc_ci_low']):+.5f}, {float(p_res['delta_pr_auc_ci_high']):+.5f}]",
                            "pr_auc_excluye_cero": bool(p_res["pr_auc_excluye_cero"]),
                            "veredicto_pr_auc": (
                                "Diferencia distinguible (IC 95 % excluye 0)"
                                if bool(p_res["pr_auc_excluye_cero"])
                                else "No se distingue (IC 95 % incluye 0)"
                            ),
                            "delta_roc_auc": round(float(p_res["delta_roc_auc"]), 5),
                            "ic95_delta_roc_auc": f"[{float(p_res['delta_roc_auc_ci_low']):+.5f}, {float(p_res['delta_roc_auc_ci_high']):+.5f}]",
                            "veredicto_roc_auc": (
                                "Diferencia distinguible (IC 95 % excluye 0)"
                                if bool(p_res["roc_auc_excluye_cero"])
                                else "No se distingue (IC 95 % incluye 0)"
                            ),
                        }
                    )

        lc_df = pd.DataFrame(lc_rows).sort_values(
            ["modelo_id", "fraccion_personas_pct", "rango_en_10pct"],
            ascending=[True, True, True],
        ).reset_index(drop=True)
        lc_knn_w_paired_df = pd.DataFrame(knn_w_paired_rows)

        return KNNTuningBundle(
            subsample_summary_table=subsample_summary_df,
            tuning_all_attempts_table=attempts_df,
            tuning_winners_table=winners_df,
            score_resolution_table=score_res_df,
            learning_curve_table=lc_df,
            learning_curve_knn_w_paired_table=lc_knn_w_paired_df,
            winner_specs=winner_specs,
            winner_oof_proba=winner_oof,
            tuning_row_idx=tun_idx,
            tuning_y=y_tun,
            tuning_groups=g_tun,
            cv_person_overlap_count=overlap_cnt,
        )

    def select_oof_thresholds(
        self,
        tuning_bundle: KNNTuningBundle,
    ) -> KNNThresholdBundle:
        """Section 10: Select threshold maximizing class-1 F1 on grouped OOF predictions (never touching test)."""
        # Read NB-H's test alert rate from exported 7.1 confusion matrix CSV
        nb_cm_df = pd.read_csv(self.config.nb_confusion_csv_path, encoding="utf-8")
        nb_h_cm = nb_cm_df.loc[
            (nb_cm_df["modelo_id"] == "NB-H")
            & (nb_cm_df["punto_operacion"].astype(str).str.contains("OOF"))
        ].iloc[0]
        nb_h_alert_rate = float(nb_h_cm["pct_predichos_positivos"]) / 100.0

        y_oof = tuning_bundle.tuning_y
        summary_rows: List[Dict[str, object]] = []
        curves: Dict[str, pd.DataFrame] = {}
        taus: Dict[str, float] = {}

        for model_id in MODEL_ORDER:
            p_oof = tuning_bundle.winner_oof_proba[model_id]
            tau_star, curve_df = select_oof_threshold_from_proba(y_oof, p_oof)
            taus[model_id] = tau_star
            curves[model_id] = curve_df

            m_050 = compute_classification_metrics(y_oof, p_oof, threshold=0.50)
            m_tau = compute_classification_metrics(y_oof, p_oof, threshold=tau_star)

            tau_eq, eff_rate_eq = compute_equal_alert_rate_cutoff(p_oof, nb_h_alert_rate)
            m_eq = compute_classification_metrics(y_oof, p_oof, threshold=tau_eq)

            summary_rows.append(
                {
                    "modelo_id": model_id,
                    "modelo": MODEL_LABELS_ES[model_id],
                    "n_filas_oof_submuestra": int(len(y_oof)),
                    "umbral_optimo_tau": round(tau_star, 4),
                    "tasa_alerta_en_tau_pct": round(100.0 * float(np.mean(p_oof >= tau_star)), 2),
                    "f1_oof_umbral_050": round(m_050["f1_pos"], 4),
                    "f1_oof_en_tau_optimo": round(m_tau["f1_pos"], 4),
                    "ganancia_f1_oof_vs_050": round(m_tau["f1_pos"] - m_050["f1_pos"], 4),
                    "recall_oof_en_tau": round(m_tau["recall_pos"], 4),
                    "precision_oof_en_tau": round(m_tau["precision_pos"], 4),
                    "tasa_alerta_nb_h_pct": round(100.0 * nb_h_alert_rate, 2),
                    "umbral_igual_alerta_nb_h_oof": round(tau_eq, 4),
                    "tasa_alerta_efectiva_oof_pct": round(100.0 * eff_rate_eq, 2),
                    "f1_oof_igual_alerta_nb_h": round(m_eq["f1_pos"], 4),
                    "recall_oof_igual_alerta_nb_h": round(m_eq["recall_pos"], 4),
                    "precision_oof_igual_alerta_nb_h": round(m_eq["precision_pos"], 4),
                }
            )

        return KNNThresholdBundle(
            oof_threshold_summary_table=pd.DataFrame(summary_rows),
            oof_threshold_curves=curves,
            oof_thresholds_tau=taus,
            nb_h_alert_rate_test=nb_h_alert_rate,
        )

    def reproduce_and_verify_baselines(
        self,
        modeling_data: VersionModelingData,
        tolerance: float = 5e-4,
    ) -> Tuple[pd.DataFrame, Dict[str, np.ndarray], Dict[str, float], Dict[str, Dict[str, float]]]:
        """Reproduce NB-B, NB-H, Logística 6.0, and HistGradientBoosting 6.0 on full train/test and verify vs CSV."""
        nb_cfg = NaiveBayesConfig(project_root=self.config.project_root)
        nb_tr = NaiveBayesFeatureBuilder.build_partition_blocks(modeling_data.train, "train")
        nb_te = NaiveBayesFeatureBuilder.build_partition_blocks(modeling_data.test, "test")

        nb_win_df = pd.read_csv(self.config.nb_winners_csv_path, encoding="utf-8").set_index("modelo_id")
        nb_te_csv = pd.read_csv(self.config.nb_test_metrics_csv_path, encoding="utf-8")
        p4_df = pd.read_csv(self.config.phase4_test_csv_path, encoding="utf-8")
        p4_a = p4_df.loc[p4_df["version"].astype(str).str.startswith("A")]

        y_tr = modeling_data.train.y
        y_te = modeling_data.test.y

        repro_probas: Dict[str, np.ndarray] = {}
        repro_taus: Dict[str, float] = {}
        repro_costs: Dict[str, Dict[str, float]] = {}
        ver_rows: List[Dict[str, object]] = []

        # 1. NB-B
        alpha_b = float(nb_win_df.loc["NB-B", "alpha_optimo"])
        tau_b = float(nb_win_df.loc["NB-B", "umbral_oof_optimo_tau"])
        est_nbb = build_bernoulli_nb(alpha=alpha_b, priors="empirical")
        t0 = time.perf_counter()
        est_nbb.fit(nb_tr.X_nb_b, y_tr)
        fit_b = time.perf_counter() - t0
        t1 = time.perf_counter()
        prob_nbb = est_nbb.predict_proba(nb_te.X_nb_b)[:, 1]
        pred_b = time.perf_counter() - t1
        repro_probas["NB-B"] = prob_nbb
        repro_taus["NB-B"] = tau_b
        repro_costs["NB-B"] = {
            "fit_s": fit_b,
            "pred_s": pred_b,
            "mem_mb": compute_matrix_memory_mb(nb_tr.X_nb_b),
        }

        # 2. NB-H
        vs_h = float(nb_win_df.loc["NB-H", "var_smoothing_optimo"])
        alpha_h = float(nb_win_df.loc["NB-H", "alpha_optimo"])
        tau_h = float(nb_win_df.loc["NB-H", "umbral_oof_optimo_tau"])
        est_nbh = HybridNaiveBayes(
            continuous_idx=nb_tr.continuous_idx,
            binary_idx=nb_tr.binary_idx,
            var_smoothing=vs_h,
            alpha=alpha_h,
            priors="empirical",
        )
        t0 = time.perf_counter()
        est_nbh.fit(nb_tr.X_nb_h, y_tr)
        fit_h = time.perf_counter() - t0
        t1 = time.perf_counter()
        prob_nbh = est_nbh.predict_proba(nb_te.X_nb_h)[:, 1]
        pred_h = time.perf_counter() - t1
        repro_probas["NB-H"] = prob_nbh
        repro_taus["NB-H"] = tau_h
        repro_costs["NB-H"] = {
            "fit_s": fit_h,
            "pred_s": pred_h,
            "mem_mb": compute_matrix_memory_mb(nb_tr.X_nb_h),
        }

        # 3. Logística Regularizada (6.0)
        X_tr_csr, _ = modeling_data.train.build_sparse_matrix(mode="clean")
        X_te_csr, _ = modeling_data.test.build_sparse_matrix(mode="clean")
        logit = SGDClassifier(
            loss="log_loss",
            penalty="l2",
            alpha=1e-4,
            class_weight="balanced",
            max_iter=50,
            tol=1e-3,
            random_state=self.config.random_state,
        )
        t0 = time.perf_counter()
        logit.fit(X_tr_csr, y_tr)
        fit_log = time.perf_counter() - t0
        t1 = time.perf_counter()
        prob_log = logit.predict_proba(X_te_csr)[:, 1]
        pred_log = time.perf_counter() - t1
        repro_probas["LOGIT_6_0"] = prob_log
        repro_taus["LOGIT_6_0"] = 0.50
        repro_costs["LOGIT_6_0"] = {
            "fit_s": fit_log,
            "pred_s": pred_log,
            "mem_mb": compute_matrix_memory_mb(X_tr_csr),
        }

        # 4. HistGradientBoosting (6.0)
        X_tr_d14 = modeling_data.train.dense_clean.to_numpy(dtype=np.float32)
        X_te_d14 = modeling_data.test.dense_clean.to_numpy(dtype=np.float32)
        hgb = HistGradientBoostingClassifier(
            max_iter=120,
            learning_rate=0.08,
            max_leaf_nodes=31,
            min_samples_leaf=100,
            class_weight="balanced",
            random_state=self.config.random_state,
        )
        t0 = time.perf_counter()
        hgb.fit(X_tr_d14, y_tr)
        fit_hgb = time.perf_counter() - t0
        t1 = time.perf_counter()
        prob_hgb = hgb.predict_proba(X_te_d14)[:, 1]
        pred_hgb = time.perf_counter() - t1
        repro_probas["HGB_6_0"] = prob_hgb
        repro_taus["HGB_6_0"] = 0.50
        repro_costs["HGB_6_0"] = {
            "fit_s": fit_hgb,
            "pred_s": pred_hgb,
            "mem_mb": compute_matrix_memory_mb(X_tr_d14),
        }

        # Verify reproduced metrics against exported CSVs
        nb_b_ref = nb_te_csv.loc[
            (nb_te_csv["modelo_id"] == "NB-B") & nb_te_csv["punto_operacion"].str.contains("OOF")
        ].iloc[0]
        nb_h_ref = nb_te_csv.loc[
            (nb_te_csv["modelo_id"] == "NB-H") & nb_te_csv["punto_operacion"].str.contains("OOF")
        ].iloc[0]
        log_ref = p4_a.loc[p4_a["modelo"].astype(str).str.contains("Logística")].iloc[0]
        hgb_ref = p4_a.loc[p4_a["modelo"].astype(str).str.contains("HistGradientBoosting")].iloc[0]

        for key, label, n_vars, weighted, ref_pr, ref_roc in [
            ("NB-B", "NB-B · BernoulliNB (7.1)", 2971, "Sin ponderar (empírico)", float(nb_b_ref["pr_auc_test"]), float(nb_b_ref["roc_auc_test"])),
            ("NB-H", "NB-H · HybridNaiveBayes (7.1)", 2981, "Sin ponderar (empírico)", float(nb_h_ref["pr_auc_test"]), float(nb_h_ref["roc_auc_test"])),
            ("LOGIT_6_0", "Logística Regularizada (6.0)", 2981, "Balanceada (class_weight='balanced')", float(log_ref["pr_auc_test"]), float(log_ref["roc_auc_test"])),
            ("HGB_6_0", "HistGradientBoosting (6.0)", 14, "Balanceada (class_weight='balanced')", float(hgb_ref["pr_auc_test"]), float(hgb_ref["roc_auc_test"])),
        ]:
            m = compute_classification_metrics(y_te, repro_probas[key], threshold=repro_taus[key])
            d_pr = abs(m["pr_auc"] - ref_pr)
            d_roc = abs(m["roc_auc"] - ref_roc)
            ok = bool(d_pr <= tolerance and d_roc <= tolerance)
            if not ok:
                raise AssertionError(
                    f"Baseline reproduction mismatch for {key}: d_pr={d_pr:.6f}, d_roc={d_roc:.6f}"
                )
            ver_rows.append(
                {
                    "modelo_referencia": label,
                    "n_variables_X": n_vars,
                    "ponderacion_clases": weighted,
                    "pr_auc_csv": round(ref_pr, 4),
                    "pr_auc_reproducido": round(m["pr_auc"], 4),
                    "diff_abs_pr_auc": round(d_pr, 6),
                    "roc_auc_csv": round(ref_roc, 4),
                    "roc_auc_reproducido": round(m["roc_auc"], 4),
                    "diff_abs_roc_auc": round(d_roc, 6),
                    "coincide_tolerancia_5e4": ok,
                }
            )

        return pd.DataFrame(ver_rows), repro_probas, repro_taus, repro_costs

    def evaluate_final_models_on_test(
        self,
        modeling_data: VersionModelingData,
        train_blocks: KNNPartitionBlocks,
        test_blocks: KNNPartitionBlocks,
        tuning_bundle: KNNTuningBundle,
        threshold_bundle: KNNThresholdBundle,
        test_row_idx: np.ndarray | None = None,
        models_to_evaluate: Sequence[str] = MODEL_ORDER,
        algorithm_overrides: Dict[str, str] | None = None,
        force_recompute_cache: bool = False,
        verbose: bool = True,
    ) -> KNNTestEvaluationBundle:
        """Sections 11, 12, 14: Fit winners on full train, predict via chunked cache, evaluate & compare fairly."""
        refs_df, trees_a_df, nb_ref_df = self.load_external_reference_tables()
        repro_ver_df, base_probas_full, base_taus, base_costs = self.reproduce_and_verify_baselines(
            modeling_data=modeling_data
        )

        is_full_test = test_row_idx is None
        if test_row_idx is None:
            eval_idx = np.arange(len(test_blocks.y), dtype=np.int64)
        else:
            eval_idx = np.asarray(test_row_idx, dtype=np.int64)

        y_te = test_blocks.y[eval_idx]
        g_te = test_blocks.groups[eval_idx]
        base_probas = {k: v[eval_idx] for k, v in base_probas_full.items()}
        nb_h_alert_rate = float(np.mean(base_probas["NB-H"] >= base_taus["NB-H"]))

        test_proba_by_model: Dict[str, np.ndarray] = {}
        chunked_results: Dict[str, ChunkedPredictResult] = {}
        fit_times_s: Dict[str, float] = {}
        mem_mb_by_model: Dict[str, float] = {}
        overrides = algorithm_overrides or {}

        for model_id in models_to_evaluate:
            base_spec = tuning_bundle.winner_specs[model_id]
            eff_algo = overrides.get(model_id, base_spec.algorithm)
            spec = KNNModelSpec(
                model_id=base_spec.model_id,
                n_neighbors=base_spec.n_neighbors,
                weights=base_spec.weights,
                metric=base_spec.metric,
                algorithm=eff_algo,
                leaf_size=base_spec.leaf_size,
                block_weight=base_spec.block_weight,
                n_jobs=base_spec.n_jobs,
            )
            if model_id == MODEL_KNN_D:
                X_tr = train_blocks.build_knn_d_matrix()
                X_te = test_blocks.build_knn_d_matrix(eval_idx)
            elif model_id == MODEL_KNN_G:
                X_tr = train_blocks.build_knn_g_matrix(w_g=spec.block_weight)
                X_te = test_blocks.build_knn_g_matrix(w_g=spec.block_weight, row_idx=eval_idx)
            else:
                X_tr = train_blocks.build_knn_w_matrix(w=spec.block_weight)
                X_te = test_blocks.build_knn_w_matrix(w=spec.block_weight, row_idx=eval_idx)

            mem_mb_by_model[model_id] = compute_matrix_memory_mb(X_tr)
            est = build_knn_classifier(spec)
            t0 = time.perf_counter()
            est.fit(X_tr, train_blocks.y)
            fit_times_s[model_id] = time.perf_counter() - t0

            meta = {
                "model_id": model_id,
                "version": "con_outliers",
                "n_train": int(len(train_blocks.y)),
                "is_full_test": bool(is_full_test),
                "spec": spec.to_sklearn_params(),
                "block_weight": round(float(spec.block_weight), 6),
                "active_dense_features": list(train_blocks.active_dense_features),
            }
            tag = f"{model_id.lower().replace('-', '_')}_{'fulltest' if is_full_test else f'sub{len(eval_idx)}'}"
            c_res = self.chunked_predictor.predict_proba_resumable(
                fitted_knn=est,
                X_query=X_te,
                run_tag=tag,
                metadata=meta,
                force_recompute=force_recompute_cache,
                verbose=verbose,
            )
            chunked_results[model_id] = c_res
            test_proba_by_model[model_id] = c_res.proba_pos

            del est, X_tr, X_te
            gc.collect()

        # Section 11 & 12: Metrics with 300-resample person bootstrap CIs, confusion matrices, calibration
        t_boot0 = time.perf_counter()
        test_rows: List[Dict[str, object]] = []
        cm_rows: List[Dict[str, object]] = []
        calib_rows: List[Dict[str, object]] = []
        curves_by_model: Dict[str, ModelCurveBundle] = {}

        for model_id in models_to_evaluate:
            spec = tuning_bundle.winner_specs[model_id]
            prob_te = test_proba_by_model[model_id]
            tau_oof = threshold_bundle.oof_thresholds_tau[model_id]
            c_res = chunked_results[model_id]

            for op_label, tau_val in [
                ("Umbral OOF óptimo (tau*)", tau_oof),
                ("Umbral por defecto (0.50)", 0.50),
            ]:
                m = compute_classification_metrics(y_te, prob_te, threshold=tau_val)
                ci = bootstrap_person_metrics(
                    y_true=y_te,
                    y_prob=prob_te,
                    groups=g_te,
                    threshold=tau_val,
                    n_resamples=self.config.bootstrap_resamples,
                    random_state=self.config.random_state,
                )
                pred_bin = (prob_te >= tau_val).astype(np.int8)
                tn, fp, fn, tp = confusion_matrix(y_te, pred_bin, labels=[0, 1]).ravel()

                test_rows.append(
                    {
                        "modelo_id": model_id,
                        "modelo": MODEL_LABELS_ES[model_id],
                        "muestra_evaluada": "Test completo" if is_full_test else f"Submuestra test ({len(eval_idx):,} filas)",
                        "punto_operacion": op_label,
                        "umbral_tau": round(float(tau_val), 4),
                        "tasa_alerta_test_pct": round(100.0 * float(pred_bin.mean()), 2),
                        "pr_auc_test": round(m["pr_auc"], 4),
                        "pr_auc_ic95": f"[{ci['pr_auc'][0]:.4f}, {ci['pr_auc'][1]:.4f}]",
                        "roc_auc_test": round(m["roc_auc"], 4),
                        "roc_auc_ic95": f"[{ci['roc_auc'][0]:.4f}, {ci['roc_auc'][1]:.4f}]",
                        "f1_clase_1_test": round(m["f1_pos"], 4),
                        "f1_clase_1_ic95": f"[{ci['f1_pos'][0]:.4f}, {ci['f1_pos'][1]:.4f}]",
                        "recall_clase_1_test": round(m["recall_pos"], 4),
                        "recall_clase_1_ic95": f"[{ci['recall_pos'][0]:.4f}, {ci['recall_pos'][1]:.4f}]",
                        "precision_clase_1_test": round(m["precision_pos"], 4),
                        "precision_clase_1_ic95": f"[{ci['precision_pos'][0]:.4f}, {ci['precision_pos'][1]:.4f}]",
                        "balanced_acc_test": round(m["balanced_acc"], 4),
                        "brier_test": round(m["brier"], 4),
                        "brier_ic95": f"[{ci['brier'][0]:.4f}, {ci['brier'][1]:.4f}]",
                        "accuracy_test": round(m["accuracy"], 4),
                        "tiempo_fit_train_s": round(fit_times_s[model_id], 3),
                        "tiempo_predict_test_s": round(c_res.total_recorded_compute_s, 2),
                        "memoria_matriz_train_mb": round(mem_mb_by_model[model_id], 2),
                    }
                )
                cm_rows.append(
                    {
                        "modelo_id": model_id,
                        "punto_operacion": op_label,
                        "umbral_tau": round(float(tau_val), 4),
                        "TN_verdaderos_negativos": int(tn),
                        "FP_falsos_positivos": int(fp),
                        "FN_falsos_negativos": int(fn),
                        "TP_verdaderos_positivos": int(tp),
                        "pct_predichos_positivos": round(100.0 * float((tp + fp) / len(y_te)), 2),
                    }
                )

            # Calibration & score resolution
            prob_true, prob_pred = calibration_curve(y_te, prob_te, n_bins=10, strategy="uniform")
            bin_edges = np.linspace(0.0, 1.0, 11)
            bin_ids = np.clip(np.digitize(prob_te, bin_edges[1:-1], right=False), 0, 9)
            bin_counts = np.bincount(bin_ids, minlength=10)
            ece = 0.0
            for b_i in range(10):
                mask_b = bin_ids == b_i
                if np.any(mask_b):
                    ece += (float(mask_b.sum()) / float(len(y_te))) * abs(
                        float(y_te[mask_b].mean()) - float(prob_te[mask_b].mean())
                    )

            n_uniq_test = int(len(np.unique(np.round(prob_te, 6))))
            pct_ext = 100.0 * float(np.mean((prob_te < 0.05) | (prob_te > 0.95)))
            calib_rows.append(
                {
                    "modelo_id": model_id,
                    "modelo": MODEL_LABELS_ES[model_id],
                    "k_vecinos": int(spec.n_neighbors),
                    "pesos": spec.weights,
                    "resolucion_1_sobre_k": round(1.0 / float(spec.n_neighbors), 5),
                    "puntajes_unicos_test": n_uniq_test,
                    "brier_test_sin_ponderar": round(float(brier_score_loss(y_te, prob_te)), 4),
                    "ece_error_calibracion": round(float(ece), 4),
                    "prob_media_predicha_test": round(float(prob_te.mean()), 4),
                    "prevalencia_real_test": round(float(y_te.mean()), 4),
                    "prob_mediana_clase_0": round(float(np.median(prob_te[y_te == 0])), 4),
                    "prob_mediana_clase_1": round(float(np.median(prob_te[y_te == 1])), 4),
                    "pct_extremos_lt005_o_gt095": round(pct_ext, 2),
                }
            )

            prec_c, rec_c, _ = precision_recall_curve(y_te, prob_te)
            fpr_c, tpr_c, _ = roc_curve(y_te, prob_te)
            pr_step = max(1, len(prec_c) // 450)
            roc_step = max(1, len(fpr_c) // 450)
            hist_edges = np.linspace(0.0, 1.0, 41)
            h_c0, _ = np.histogram(prob_te[y_te == 0], bins=hist_edges, density=True)
            h_c1, _ = np.histogram(prob_te[y_te == 1], bins=hist_edges, density=True)
            curves_by_model[model_id] = ModelCurveBundle(
                model_id=model_id,
                model_label_es=MODEL_LABELS_ES[model_id],
                pr_auc=float(average_precision_score(y_te, prob_te)),
                roc_auc=float(roc_auc_score(y_te, prob_te)),
                brier=float(brier_score_loss(y_te, prob_te)),
                ece=float(ece),
                precision_curve=prec_c[::pr_step],
                recall_curve=rec_c[::pr_step],
                fpr_curve=fpr_c[::roc_step],
                tpr_curve=tpr_c[::roc_step],
                calib_prob_pred=prob_pred,
                calib_prob_true=prob_true,
                calib_bin_counts=bin_counts,
                hist_bins=0.5 * (hist_edges[:-1] + hist_edges[1:]),
                hist_density_c0=h_c0,
                hist_density_c1=h_c1,
            )

        # Also append unweighted NB-B and NB-H calibration reference rows from exported 7.1 table
        if self.config.nb_calibration_csv_path.exists():
            nb_cal = pd.read_csv(self.config.nb_calibration_csv_path, encoding="utf-8")
            for _, nr in nb_cal.iterrows():
                if str(nr["modelo_id"]) in ("NB-B", "NB-H"):
                    calib_rows.append(
                        {
                            "modelo_id": str(nr["modelo_id"]),
                            "modelo": str(nr["modelo"]) + " (Ref. 7.1 sin ponderar)",
                            "k_vecinos": np.nan,
                            "pesos": "Probabilístico",
                            "resolucion_1_sobre_k": np.nan,
                            "puntajes_unicos_test": np.nan,
                            "brier_test_sin_ponderar": float(nr["brier_test"]),
                            "ece_error_calibracion": float(nr["ece_error_calibracion_esperado"]),
                            "prob_media_predicha_test": float(nr["prob_media_predicha_test"]),
                            "prevalencia_real_test": float(nr["prevalencia_real_test"]),
                            "prob_mediana_clase_0": float(nr["prob_mediana_clase_0"]),
                            "prob_mediana_clase_1": float(nr["prob_mediana_clase_1"]),
                            "pct_extremos_lt005_o_gt095": float(
                                nr["pct_probabilidades_extremas_<005_o_>095"]
                            ),
                        }
                    )

        # Section 14: Equal-alert-rate comparison, like-for-like tables, paired bootstrap CIs, cost table
        eq_specs: List[Tuple[str, str, int, str, np.ndarray, float | None]] = []
        for mid in models_to_evaluate:
            n_vars = (
                len(train_blocks.active_dense_features)
                if mid == MODEL_KNN_D
                else (
                    len(train_blocks.active_dense_features) + 10
                    if mid == MODEL_KNN_G
                    else len(train_blocks.active_dense_features) + len(train_blocks.ohe_feature_names)
                )
            )
            space_lbl = (
                f"Solo bloque denso ({n_vars} cols)"
                if mid == MODEL_KNN_D
                else (
                    f"Denso + proxy ISCO 1d ({n_vars} cols)"
                    if mid == MODEL_KNN_G
                    else f"Con ocupación ESCO OHE ({n_vars:,} cols)"
                )
            )
            eq_specs.append((mid, space_lbl, n_vars, "Sin ponderar (empírico)", test_proba_by_model[mid], None))

        eq_specs.extend(
            [
                ("NB-B", "Con ocupación ESCO OHE (2,971 cols)", 2971, "Sin ponderar (empírico)", base_probas["NB-B"], None),
                ("NB-H", "Con ocupación ESCO OHE (2,981 cols)", 2981, "Sin ponderar (empírico)", base_probas["NB-H"], base_taus["NB-H"]),
                ("Logística Regularizada (6.0)", "Con ocupación ESCO OHE (2,981 cols)", 2981, "Balanceada (class_weight='balanced')", base_probas["LOGIT_6_0"], None),
                ("HistGradientBoosting (6.0)", "Solo bloque denso (14 cols)", 14, "Balanceada (class_weight='balanced')", base_probas["HGB_6_0"], None),
            ]
        )

        eq_cutoffs: Dict[str, float] = {}
        eq_rows: List[Dict[str, object]] = []
        for m_name, space_lbl, n_vars, weight_lbl, p_vec, fixed_tau in eq_specs:
            if fixed_tau is not None:
                cutoff = float(fixed_tau)
                eff_rate = float(np.mean(p_vec >= cutoff))
            else:
                cutoff, eff_rate = compute_equal_alert_rate_cutoff(p_vec, nb_h_alert_rate)
            eq_cutoffs[m_name] = cutoff
            m_eq = compute_classification_metrics(y_te, p_vec, threshold=cutoff)
            eq_rows.append(
                {
                    "modelo": m_name,
                    "espacio_variables": space_lbl,
                    "n_variables_X": n_vars,
                    "ponderacion_clases": weight_lbl,
                    "tasa_alerta_objetivo_pct": round(100.0 * nb_h_alert_rate, 2),
                    "tasa_alerta_efectiva_pct": round(100.0 * eff_rate, 2),
                    "umbral_corte_equivalente": round(cutoff, 4),
                    "pr_auc_test": round(m_eq["pr_auc"], 4),
                    "roc_auc_test": round(m_eq["roc_auc"], 4),
                    "f1_igual_alerta_test": round(m_eq["f1_pos"], 4),
                    "recall_igual_alerta_test": round(m_eq["recall_pos"], 4),
                    "precision_igual_alerta_test": round(m_eq["precision_pos"], 4),
                    "balanced_acc_igual_alerta_test": round(m_eq["balanced_acc"], 4),
                    "brier_solo_sin_ponderar": round(m_eq["brier"], 4)
                    if weight_lbl.startswith("Sin ponderar")
                    else np.nan,
                }
            )
        eq_df = pd.DataFrame(eq_rows)
        test_metrics_df = pd.DataFrame(test_rows)

        # Like-for-like Dense-only table (KNN-D vs NB-G (7.1 CSV) vs HistGradientBoosting 6.0)
        dense_rows: List[Dict[str, object]] = []
        if MODEL_KNN_D in test_proba_by_model:
            r_kd = test_metrics_df.loc[
                (test_metrics_df["modelo_id"] == MODEL_KNN_D)
                & test_metrics_df["punto_operacion"].str.contains("OOF")
            ].iloc[0]
            eq_kd = eq_df.loc[eq_df["modelo"] == MODEL_KNN_D].iloc[0]
            dense_rows.append(
                {
                    "modelo": MODEL_LABELS_ES[MODEL_KNN_D],
                    "n_variables_X": len(train_blocks.active_dense_features),
                    "ponderacion_clases": "Sin ponderar (empírico)",
                    "pr_auc_test": float(r_kd["pr_auc_test"]),
                    "pr_auc_ic95": str(r_kd["pr_auc_ic95"]),
                    "roc_auc_test": float(r_kd["roc_auc_test"]),
                    "roc_auc_ic95": str(r_kd["roc_auc_ic95"]),
                    "f1_umbral_propio": float(r_kd["f1_clase_1_test"]),
                    "f1_igual_alerta_NB_H": float(eq_kd["f1_igual_alerta_test"]),
                    "brier_solo_sin_ponderar": float(r_kd["brier_test"]),
                }
            )
        nb_g_csv_rows = nb_ref_df.loc[
            (nb_ref_df["modelo_id"] == "NB-G") & nb_ref_df["punto_operacion"].str.contains("OOF")
        ]
        if not nb_g_csv_rows.empty:
            r_nbg = nb_g_csv_rows.iloc[0]
            dense_rows.append(
                {
                    "modelo": "NB-G · GaussianNB (7.1 · 14 cols densas)",
                    "n_variables_X": 14,
                    "ponderacion_clases": "Sin ponderar (empírico)",
                    "pr_auc_test": float(r_nbg["pr_auc_test"]),
                    "pr_auc_ic95": str(r_nbg["pr_auc_ic95"]),
                    "roc_auc_test": float(r_nbg["roc_auc_test"]),
                    "roc_auc_ic95": str(r_nbg["roc_auc_ic95"]),
                    "f1_umbral_propio": float(r_nbg["f1_clase_1_test"]),
                    "f1_igual_alerta_NB_H": np.nan,
                    "brier_solo_sin_ponderar": float(r_nbg["brier_test"]),
                }
            )
        m_hgb = compute_classification_metrics(y_te, base_probas["HGB_6_0"], threshold=0.50)
        ci_hgb = bootstrap_person_metrics(
            y_te, base_probas["HGB_6_0"], g_te, threshold=0.50,
            n_resamples=self.config.bootstrap_resamples, random_state=self.config.random_state,
        )
        eq_hgb = eq_df.loc[eq_df["modelo"] == "HistGradientBoosting (6.0)"].iloc[0]
        dense_rows.append(
            {
                "modelo": "HistGradientBoosting (6.0 · 14 cols densas)",
                "n_variables_X": 14,
                "ponderacion_clases": "Balanceada (class_weight='balanced')",
                "pr_auc_test": round(m_hgb["pr_auc"], 4),
                "pr_auc_ic95": f"[{ci_hgb['pr_auc'][0]:.4f}, {ci_hgb['pr_auc'][1]:.4f}]",
                "roc_auc_test": round(m_hgb["roc_auc"], 4),
                "roc_auc_ic95": f"[{ci_hgb['roc_auc'][0]:.4f}, {ci_hgb['roc_auc'][1]:.4f}]",
                "f1_umbral_propio": round(m_hgb["f1_pos"], 4),
                "f1_igual_alerta_NB_H": float(eq_hgb["f1_igual_alerta_test"]),
                "brier_solo_sin_ponderar": np.nan,
            }
        )
        like_dense_df = pd.DataFrame(dense_rows)

        # Like-for-like With-occupation table (KNN-G, KNN-W vs NB-B, NB-H, Logística 6.0)
        occ_rows: List[Dict[str, object]] = []
        for mid in (MODEL_KNN_G, MODEL_KNN_W):
            if mid not in test_proba_by_model:
                continue
            rm = test_metrics_df.loc[
                (test_metrics_df["modelo_id"] == mid) & test_metrics_df["punto_operacion"].str.contains("OOF")
            ].iloc[0]
            eq_m = eq_df.loc[eq_df["modelo"] == mid].iloc[0]
            occ_rows.append(
                {
                    "modelo": MODEL_LABELS_ES[mid],
                    "n_variables_X": int(eq_m["n_variables_X"]),
                    "ponderacion_clases": "Sin ponderar (empírico)",
                    "pr_auc_test": float(rm["pr_auc_test"]),
                    "pr_auc_ic95": str(rm["pr_auc_ic95"]),
                    "roc_auc_test": float(rm["roc_auc_test"]),
                    "roc_auc_ic95": str(rm["roc_auc_ic95"]),
                    "f1_umbral_propio": float(rm["f1_clase_1_test"]),
                    "f1_igual_alerta_NB_H": float(eq_m["f1_igual_alerta_test"]),
                    "brier_solo_sin_ponderar": float(rm["brier_test"]),
                }
            )
        for key, lbl, n_v, w_lbl in [
            ("NB-B", "NB-B · BernoulliNB (7.1)", 2971, "Sin ponderar (empírico)"),
            ("NB-H", "NB-H · HybridNaiveBayes (7.1)", 2981, "Sin ponderar (empírico)"),
            ("LOGIT_6_0", "Logística Regularizada (6.0)", 2981, "Balanceada (class_weight='balanced')"),
        ]:
            m_b = compute_classification_metrics(y_te, base_probas[key], threshold=base_taus[key])
            ci_b = bootstrap_person_metrics(
                y_te, base_probas[key], g_te, threshold=base_taus[key],
                n_resamples=self.config.bootstrap_resamples, random_state=self.config.random_state,
            )
            eq_key = "Logística Regularizada (6.0)" if key == "LOGIT_6_0" else key
            eq_b = eq_df.loc[eq_df["modelo"] == eq_key].iloc[0]
            occ_rows.append(
                {
                    "modelo": lbl,
                    "n_variables_X": n_v,
                    "ponderacion_clases": w_lbl,
                    "pr_auc_test": round(m_b["pr_auc"], 4),
                    "pr_auc_ic95": f"[{ci_b['pr_auc'][0]:.4f}, {ci_b['pr_auc'][1]:.4f}]",
                    "roc_auc_test": round(m_b["roc_auc"], 4),
                    "roc_auc_ic95": f"[{ci_b['roc_auc'][0]:.4f}, {ci_b['roc_auc'][1]:.4f}]",
                    "f1_umbral_propio": round(m_b["f1_pos"], 4),
                    "f1_igual_alerta_NB_H": float(eq_b["f1_igual_alerta_test"]),
                    "brier_solo_sin_ponderar": round(m_b["brier"], 4)
                    if w_lbl.startswith("Sin ponderar")
                    else np.nan,
                }
            )
        like_occ_df = pd.DataFrame(occ_rows)

        # Paired person-level bootstrap comparisons (strictly fair, same resampled persons)
        paired_specs: List[Tuple[str, str, str, np.ndarray, np.ndarray, float, float]] = []
        if MODEL_KNN_D in test_proba_by_model:
            paired_specs.append(
                (
                    "KNN-D vs. HistGradientBoosting (6.0)",
                    "Homogénea (solo bloque denso)",
                    f"{len(train_blocks.active_dense_features)} vs. 14 cols densas",
                    test_proba_by_model[MODEL_KNN_D],
                    base_probas["HGB_6_0"],
                    eq_cutoffs[MODEL_KNN_D],
                    eq_cutoffs["HistGradientBoosting (6.0)"],
                )
            )
        if MODEL_KNN_G in test_proba_by_model and MODEL_KNN_D in test_proba_by_model:
            paired_specs.append(
                (
                    "KNN-G vs. KNN-D",
                    "Aporte del proxy ISCO 1d sobre bloque denso",
                    "21 vs. 11 cols densas",
                    test_proba_by_model[MODEL_KNN_G],
                    test_proba_by_model[MODEL_KNN_D],
                    eq_cutoffs[MODEL_KNN_G],
                    eq_cutoffs[MODEL_KNN_D],
                )
            )
        if MODEL_KNN_W in test_proba_by_model and MODEL_KNN_G in test_proba_by_model:
            paired_specs.append(
                (
                    "KNN-W vs. KNN-G",
                    "Aporte de 2,967 ocupaciones ESCO vs. 10 grupos ISCO",
                    "2,978 vs. 21 cols",
                    test_proba_by_model[MODEL_KNN_W],
                    test_proba_by_model[MODEL_KNN_G],
                    eq_cutoffs[MODEL_KNN_W],
                    eq_cutoffs[MODEL_KNN_G],
                )
            )
        for mid in (MODEL_KNN_W, MODEL_KNN_G):
            if mid not in test_proba_by_model:
                continue
            n_v = 2978 if mid == MODEL_KNN_W else 21
            paired_specs.append(
                (
                    f"{mid} vs. NB-H (7.1)",
                    "Homogénea (con información ocupacional)" if mid == MODEL_KNN_W else "Proxy ISCO 1d vs. OHE 2,967",
                    f"{n_v:,} vs. 2,981 cols",
                    test_proba_by_model[mid],
                    base_probas["NB-H"],
                    eq_cutoffs[mid],
                    eq_cutoffs["NB-H"],
                )
            )
            paired_specs.append(
                (
                    f"{mid} vs. NB-B (7.1)",
                    "Con ocupación vs. Bernoulli OHE",
                    f"{n_v:,} vs. 2,971 cols",
                    test_proba_by_model[mid],
                    base_probas["NB-B"],
                    eq_cutoffs[mid],
                    eq_cutoffs["NB-B"],
                )
            )
            paired_specs.append(
                (
                    f"{mid} vs. Logística Regularizada (6.0)",
                    "Homogénea (mismo espacio OHE)" if mid == MODEL_KNN_W else "Proxy ISCO 1d vs. Techo OHE 6.0",
                    f"{n_v:,} vs. 2,981 cols",
                    test_proba_by_model[mid],
                    base_probas["LOGIT_6_0"],
                    eq_cutoffs[mid],
                    eq_cutoffs["Logística Regularizada (6.0)"],
                )
            )

        paired_rows: List[Dict[str, object]] = []
        for cname, ctype, vdesc, pa, pb, ta, tb in paired_specs:
            res = paired_bootstrap_person_diffs(
                y_true=y_te,
                prob_a=pa,
                prob_b=pb,
                groups=g_te,
                threshold_a=ta,
                threshold_b=tb,
                n_resamples=self.config.bootstrap_resamples,
                random_state=self.config.random_state,
            )
            paired_rows.append(
                {
                    "comparacion_A_menos_B": cname,
                    "tipo_comparacion": ctype,
                    "variables_comparadas": vdesc,
                    "delta_pr_auc": round(float(res["delta_pr_auc"]), 4),
                    "ic95_delta_pr_auc": f"[{float(res['delta_pr_auc_ci_low']):+.4f}, {float(res['delta_pr_auc_ci_high']):+.4f}]",
                    "pr_auc_excluye_cero": bool(res["pr_auc_excluye_cero"]),
                    "veredicto_pr_auc": str(res["veredicto_pr_auc"]),
                    "delta_roc_auc": round(float(res["delta_roc_auc"]), 4),
                    "ic95_delta_roc_auc": f"[{float(res['delta_roc_auc_ci_low']):+.4f}, {float(res['delta_roc_auc_ci_high']):+.4f}]",
                    "roc_auc_excluye_cero": bool(res["roc_auc_excluye_cero"]),
                    "veredicto_roc_auc": str(res["veredicto_roc_auc"]),
                    "delta_f1_igual_alerta": round(float(res["delta_f1"]), 4),
                    "ic95_delta_f1_igual_alerta": f"[{float(res['delta_f1_ci_low']):+.4f}, {float(res['delta_f1_ci_high']):+.4f}]",
                    "f1_excluye_cero": bool(res["f1_excluye_cero"]),
                    "veredicto_f1_igual_alerta": str(res["veredicto_f1"]),
                }
            )
        paired_df = pd.DataFrame(paired_rows)

        # Cost comparison table across KNN, Naive Bayes, and 6.0 baselines
        n_test_eval = float(len(y_te))
        cost_rows: List[Dict[str, object]] = []
        for mid in models_to_evaluate:
            c_res = chunked_results[mid]
            sp = tuning_bundle.winner_specs[mid]
            algo = "brute" if mid == MODEL_KNN_W else str(overrides.get(mid, sp.algorithm))
            cost_rows.append(
                {
                    "familia": "KNN (7.2)",
                    "modelo": MODEL_LABELS_ES[mid],
                    "algoritmo_o_motor": f"KNeighborsClassifier ({algo}, n_jobs={sp.n_jobs})",
                    "tiempo_fit_s": round(fit_times_s[mid], 3),
                    "tiempo_predict_por_1000_filas_s": round(
                        c_res.total_recorded_compute_s / (n_test_eval / 1000.0), 4
                    ),
                    "tiempo_predict_total_eval_s": round(c_res.total_recorded_compute_s, 2),
                    "memoria_matriz_train_mb": round(mem_mb_by_model[mid], 2),
                    "rss_pico_mb": round(c_res.peak_rss_mb, 1),
                    "escalabilidad_inferencia": (
                        "Sublineal en d baja (árbol exacto)"
                        if algo != "brute"
                        else "O(N_train * N_test) fuerza bruta"
                    ),
                }
            )
        n_full_f = float(len(modeling_data.test.y))
        for key, fam, lbl, eng, scal in [
            ("NB-B", "Naive Bayes (7.1)", "NB-B · BernoulliNB", "Producto matricial CSR", "O(1) en N_train; lineal en N_test"),
            ("NB-H", "Naive Bayes (7.1)", "NB-H · HybridNaiveBayes", "Gaussiano denso + Bernoulli CSR", "O(1) en N_train; lineal en N_test"),
            ("LOGIT_6_0", "Lineal (6.0)", "Logística Regularizada (6.0)", "SGDClassifier log-loss CSR", "O(1) en N_train; lineal en N_test"),
            ("HGB_6_0", "Boosting (6.0)", "HistGradientBoosting (6.0)", "Histogramas densos (14 cols)", "O(1) en N_train; rápido en N_test"),
        ]:
            bc = base_costs[key]
            cost_rows.append(
                {
                    "familia": fam,
                    "modelo": lbl,
                    "algoritmo_o_motor": eng,
                    "tiempo_fit_s": round(bc["fit_s"], 3),
                    "tiempo_predict_por_1000_filas_s": round(bc["pred_s"] / (n_full_f / 1000.0), 5),
                    "tiempo_predict_total_eval_s": round(bc["pred_s"], 3),
                    "memoria_matriz_train_mb": round(bc["mem_mb"], 2),
                    "rss_pico_mb": np.nan,
                    "escalabilidad_inferencia": scal,
                }
            )
        cost_comp_df = pd.DataFrame(cost_rows)

        # Unified master comparison table (Refs 1-3, Trees 7.0, NB-B/NB-H 7.1, 6.0 HGB, KNN variants)
        ref_pr_map: Dict[str, float] = {}
        if "test_pr_auc" in refs_df.columns:
            for _, rr in refs_df.iterrows():
                ref_pr_map[str(rr["referencia_id"])[:5]] = float(rr["test_pr_auc"])

        unified_rows: List[Dict[str, object]] = []
        for _, trow in trees_a_df.iterrows():
            ms = str(trow["modelo_corto"])
            ref_k = ms[:5] if ms.startswith("Ref") else ""
            is_w = ("Ref 3" in ms) or ("balanced" in str(trow["punto_operacion"]))
            unified_rows.append(
                {
                    "familia": "Referencia" if ms.startswith("Ref") else "Árbol de Decisión (7.0)",
                    "modelo": ms,
                    "n_variables_X": int(trow["n_variables_X"]),
                    "ponderacion_clases": "Balanceada" if is_w else "Sin ponderar",
                    "test_pr_auc": round(ref_pr_map[ref_k], 4) if ref_k in ref_pr_map else np.nan,
                    "test_roc_auc": round(float(trow["test_roc_auc"]), 4),
                    "test_f1_clase_1": round(float(trow["test_f1_clase_1"]), 4),
                    "test_recall_clase_1": round(float(trow["test_recall_clase_1"]), 4),
                    "test_precision_clase_1": round(float(trow["test_precision_clase_1"]), 4),
                    "test_accuracy": round(float(trow["test_accuracy"]), 4),
                    "test_brier_sin_ponderar": np.nan,
                }
            )
        for _, nr in nb_ref_df.loc[nb_ref_df["punto_operacion"].str.contains("OOF")].iterrows():
            if str(nr["modelo_id"]) in ("NB-B", "NB-H", "NB-G"):
                n_v = 14 if nr["modelo_id"] == "NB-G" else (2971 if nr["modelo_id"] == "NB-B" else 2981)
                unified_rows.append(
                    {
                        "familia": "Naive Bayes (7.1)",
                        "modelo": f"{nr['modelo_id']} (tau*={nr['umbral_tau']})",
                        "n_variables_X": n_v,
                        "ponderacion_clases": "Sin ponderar",
                        "test_pr_auc": float(nr["pr_auc_test"]),
                        "test_roc_auc": float(nr["roc_auc_test"]),
                        "test_f1_clase_1": float(nr["f1_clase_1_test"]),
                        "test_recall_clase_1": float(nr["recall_clase_1_test"]),
                        "test_precision_clase_1": float(nr["precision_clase_1_test"]),
                        "test_accuracy": float(nr["accuracy_test"]),
                        "test_brier_sin_ponderar": float(nr["brier_test"]),
                    }
                )
        for _, kr in test_metrics_df.loc[test_metrics_df["punto_operacion"].str.contains("OOF")].iterrows():
            mid = str(kr["modelo_id"])
            n_v = (
                len(train_blocks.active_dense_features)
                if mid == MODEL_KNN_D
                else (len(train_blocks.active_dense_features) + 10 if mid == MODEL_KNN_G else len(train_blocks.active_dense_features) + len(train_blocks.ohe_feature_names))
            )
            unified_rows.append(
                {
                    "familia": "KNN (7.2)",
                    "modelo": f"{mid} (tau*={kr['umbral_tau']})",
                    "n_variables_X": n_v,
                    "ponderacion_clases": "Sin ponderar",
                    "test_pr_auc": float(kr["pr_auc_test"]),
                    "test_roc_auc": float(kr["roc_auc_test"]),
                    "test_f1_clase_1": float(kr["f1_clase_1_test"]),
                    "test_recall_clase_1": float(kr["recall_clase_1_test"]),
                    "test_precision_clase_1": float(kr["precision_clase_1_test"]),
                    "test_accuracy": float(kr["accuracy_test"]),
                    "test_brier_sin_ponderar": float(kr["brier_test"]),
                }
            )
        unified_df = pd.DataFrame(unified_rows)

        boot_elapsed = time.perf_counter() - t_boot0
        return KNNTestEvaluationBundle(
            references_table=refs_df,
            trees_reference_table=trees_a_df,
            nb_reference_table=nb_ref_df,
            reproduced_baselines_table=repro_ver_df,
            test_metrics_table=test_metrics_df,
            confusion_matrices_table=pd.DataFrame(cm_rows),
            calibration_summary_table=pd.DataFrame(calib_rows),
            like_for_like_dense_table=like_dense_df,
            like_for_like_occ_table=like_occ_df,
            paired_bootstrap_table=paired_df,
            equal_alert_rate_table=eq_df,
            cost_comparison_table=cost_comp_df,
            final_unified_comparison_table=unified_df,
            test_proba_by_model=test_proba_by_model,
            baseline_test_proba=base_probas,
            baseline_thresholds=base_taus,
            chunked_results=chunked_results,
            model_curves=curves_by_model,
            eval_row_idx_test=eval_idx,
            is_full_test_evaluation=is_full_test,
            bootstrap_elapsed_s=round(boot_elapsed, 2),
        )
