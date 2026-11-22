"""Pilot benchmarks: algorithm & n_jobs selection, baseline timing, cost curves, and Step 9 full-run projection."""

from __future__ import annotations

from dataclasses import dataclass
import gc
import time
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import sparse

from scripts.ScriptsCsv.NaiveBayes.evaluation import (
    compute_classification_metrics,
    compute_matrix_memory_mb,
)
from scripts.ScriptsCsv.NaiveBayes.pipeline import current_process_rss_mb

from .config import (
    KNNConfig,
    MODEL_KNN_D,
    MODEL_KNN_G,
    MODEL_KNN_W,
    MODEL_LABELS_ES,
)
from .feature_blocks import KNNPartitionBlocks
from .models import KNNModelSpec, build_knn_classifier


@dataclass(frozen=True)
class PilotSelectionBundle:
    """Results of exact algorithm & n_jobs pilot plus Section 6 baseline timing."""

    algorithm_njobs_table: pd.DataFrame
    selected_algorithms: Dict[str, str]
    selected_n_jobs: int
    baseline_pilot_table: pd.DataFrame
    pilot_split_info: Dict[str, object]


@dataclass(frozen=True)
class CostCurveBundle:
    """Section 8 cost curves (predict time vs training size and dimensionality) with log-log slopes."""

    cost_measurements_table: pd.DataFrame
    loglog_slopes_table: pd.DataFrame


@dataclass(frozen=True)
class FullRunProjectionBundle:
    """Section 9 benchmark (~5,000 test queries against full train) and extrapolation to 347,720 rows."""

    projection_table: pd.DataFrame
    any_exceeds_limit: bool
    max_projected_hours_limit: float
    total_projected_hours_all_models: float


def sample_disjoint_person_splits(
    groups: np.ndarray,
    n_train_persons: int,
    n_val_persons: int,
    random_state: int = 42,
) -> Tuple[np.ndarray, np.ndarray]:
    """Deterministically draw two disjoint person-level row index arrays from train."""
    unique_persons = np.unique(np.asarray(groups, dtype=str))
    total_needed = int(n_train_persons) + int(n_val_persons)
    if total_needed > len(unique_persons):
        raise ValueError(
            f"Requested {total_needed} persons, but only {len(unique_persons)} available."
        )
    rng = np.random.default_rng(random_state)
    perm = rng.permutation(unique_persons)
    tr_persons = set(perm[:n_train_persons].tolist())
    va_persons = set(perm[n_train_persons:total_needed].tolist())
    tr_idx = np.flatnonzero(np.isin(groups, list(tr_persons)))
    va_idx = np.flatnonzero(np.isin(groups, list(va_persons)))
    return tr_idx, va_idx


class PilotBenchmarkRunner:
    """Run exact-algorithm/n_jobs pilots, Section 6 baselines, Section 8 cost curves, and Step 9 projections."""

    def __init__(self, config: KNNConfig) -> None:
        self.config = config

    def run_pilot_selection_and_baseline(
        self,
        train_blocks: KNNPartitionBlocks,
        n_jobs_candidates: Sequence[int] = (1, 2, 4, 8),
        pilot_train_persons: int | None = None,
        pilot_val_persons: int | None = None,
    ) -> PilotSelectionBundle:
        """Compare exact search algorithms & n_jobs on a person-level pilot, then time default baselines."""
        n_tr_p = int(pilot_train_persons or self.config.pilot_train_persons)
        n_va_p = int(pilot_val_persons or self.config.pilot_val_persons)
        tr_idx, va_idx = sample_disjoint_person_splits(
            train_blocks.groups,
            n_train_persons=n_tr_p,
            n_val_persons=n_va_p,
            random_state=self.config.random_state,
        )
        y_tr = train_blocks.y[tr_idx]
        y_va = train_blocks.y[va_idx]

        X_d_tr = train_blocks.build_knn_d_matrix(tr_idx)
        X_d_va = train_blocks.build_knn_d_matrix(va_idx)
        X_g_tr = train_blocks.build_knn_g_matrix(w_g=1.0, row_idx=tr_idx)
        X_g_va = train_blocks.build_knn_g_matrix(w_g=1.0, row_idx=va_idx)
        X_w_tr = train_blocks.build_knn_w_matrix(w=1.0, row_idx=tr_idx)
        X_w_va = train_blocks.build_knn_w_matrix(w=1.0, row_idx=va_idx)

        algo_rows: List[Dict[str, object]] = []
        ref_probs_by_model: Dict[str, np.ndarray] = {}

        # 1. Compare exact algorithms (kd_tree vs ball_tree vs brute) at k=51 for KNN-D and KNN-G
        #    on both euclidean and manhattan, then test n_jobs candidates on KNN-D (kd_tree) and KNN-W (brute)
        test_jobs_for_algo = min(4, max(n_jobs_candidates))
        for model_id, X_tr, X_va, metrics_list, algos in [
            (MODEL_KNN_D, X_d_tr, X_d_va, ("euclidean", "manhattan"), ("kd_tree", "ball_tree", "brute")),
            (MODEL_KNN_G, X_g_tr, X_g_va, ("euclidean", "manhattan"), ("kd_tree", "ball_tree", "brute")),
        ]:
            for metric_name in metrics_list:
                ref_key = f"{model_id}_{metric_name}"
                for algo in algos:
                    rss_before = current_process_rss_mb()
                    est = build_knn_classifier(
                        KNNModelSpec(
                            model_id=model_id,
                            n_neighbors=51,
                            weights="uniform",
                            metric=metric_name,
                            algorithm=algo,
                            n_jobs=test_jobs_for_algo,
                        )
                    )
                    t0 = time.perf_counter()
                    est.fit(X_tr, y_tr)
                    fit_s = time.perf_counter() - t0

                    t1 = time.perf_counter()
                    probs = est.predict_proba(X_va)[:, 1]
                    pred_s = time.perf_counter() - t1
                    rss_after = current_process_rss_mb()

                    if ref_key not in ref_probs_by_model:
                        ref_probs_by_model[ref_key] = probs
                        max_diff = 0.0
                    else:
                        max_diff = float(np.max(np.abs(probs - ref_probs_by_model[ref_key])))

                    algo_rows.append(
                        {
                            "experimento": f"Algoritmo exacto ({metric_name}, k=51)",
                            "modelo_id": model_id,
                            "metrica": metric_name,
                            "algoritmo": algo,
                            "n_jobs": test_jobs_for_algo,
                            "n_train_piloto": int(len(y_tr)),
                            "n_val_piloto": int(len(y_va)),
                            "tiempo_fit_s": round(fit_s, 4),
                            "tiempo_predict_s": round(pred_s, 4),
                            "ms_por_1000_filas": round(1000.0 * pred_s / (len(y_va) / 1000.0), 2),
                            "rss_antes_mb": round(rss_before, 1),
                            "rss_despues_mb": round(rss_after, 1),
                            "delta_rss_mb": round(rss_after - rss_before, 1),
                            "max_diff_vs_ref": round(max_diff, 8),
                        }
                    )

        # Select fastest exact tree algorithm (kd_tree vs ball_tree) for KNN-D (per Section 3)
        # and fastest exact algorithm overall for KNN-G (checking trees vs brute on 21 dense dims)
        df_algo_tmp = pd.DataFrame(algo_rows)
        selected_algos: Dict[str, str] = {MODEL_KNN_W: "brute"}
        sub_d_trees = (
            df_algo_tmp.loc[
                (df_algo_tmp["modelo_id"] == MODEL_KNN_D)
                & (df_algo_tmp["algoritmo"].isin(["kd_tree", "ball_tree"]))
            ]
            .groupby("algoritmo", as_index=False)["tiempo_predict_s"]
            .sum()
            .sort_values("tiempo_predict_s")
        )
        selected_algos[MODEL_KNN_D] = str(sub_d_trees.iloc[0]["algoritmo"])

        sub_g_all = (
            df_algo_tmp.loc[df_algo_tmp["modelo_id"] == MODEL_KNN_G]
            .groupby("algoritmo", as_index=False)["tiempo_predict_s"]
            .sum()
            .sort_values("tiempo_predict_s")
        )
        selected_algos[MODEL_KNN_G] = str(sub_g_all.iloc[0]["algoritmo"])

        # 2. Sweep n_jobs on KNN-D (selected tree algorithm) and KNN-W (brute sparse) to check speed vs RSS
        njobs_rows: List[Dict[str, object]] = []
        for nj in n_jobs_candidates:
            for model_id, X_tr, X_va, algo in [
                (MODEL_KNN_D, X_d_tr, X_d_va, selected_algos[MODEL_KNN_D]),
                (MODEL_KNN_W, X_w_tr, X_w_va, "brute"),
            ]:
                rss_before = current_process_rss_mb()
                est = build_knn_classifier(
                    KNNModelSpec(
                        model_id=model_id,
                        n_neighbors=51,
                        weights="uniform",
                        metric="euclidean",
                        algorithm=algo,
                        n_jobs=int(nj),
                    )
                )
                t0 = time.perf_counter()
                est.fit(X_tr, y_tr)
                fit_s = time.perf_counter() - t0
                t1 = time.perf_counter()
                _ = est.predict_proba(X_va)[:, 1]
                pred_s = time.perf_counter() - t1
                rss_after = current_process_rss_mb()

                njobs_rows.append(
                    {
                        "experimento": "Paralelismo n_jobs (euclidean, k=51)",
                        "modelo_id": model_id,
                        "metrica": "euclidean",
                        "algoritmo": algo,
                        "n_jobs": int(nj),
                        "n_train_piloto": int(len(y_tr)),
                        "n_val_piloto": int(len(y_va)),
                        "tiempo_fit_s": round(fit_s, 4),
                        "tiempo_predict_s": round(pred_s, 4),
                        "ms_por_1000_filas": round(1000.0 * pred_s / (len(y_va) / 1000.0), 2),
                        "rss_antes_mb": round(rss_before, 1),
                        "rss_despues_mb": round(rss_after, 1),
                        "delta_rss_mb": round(rss_after - rss_before, 1),
                        "max_diff_vs_ref": 0.0,
                    }
                )

        algo_njobs_df = pd.DataFrame(algo_rows + njobs_rows)
        # Choose n_jobs minimizing combined KNN-D + KNN-W predict time while avoiding RSS spike > 4000 MB
        nj_summary = (
            pd.DataFrame(njobs_rows)
            .groupby("n_jobs", as_index=False)
            .agg(total_pred_s=("tiempo_predict_s", "sum"), max_delta_rss=("delta_rss_mb", "max"))
        )
        safe_nj = nj_summary.loc[nj_summary["max_delta_rss"] < 4000.0]
        if safe_nj.empty:
            safe_nj = nj_summary
        selected_n_jobs = int(safe_nj.sort_values("total_pred_s").iloc[0]["n_jobs"])

        # 3. Section 6 baseline run (default k=5, weights='uniform', metric='euclidean', w_g=1.0, w=1.0)
        baseline_rows: List[Dict[str, object]] = []
        for model_id, X_tr, X_va, block_w in [
            (MODEL_KNN_D, X_d_tr, X_d_va, 0.0),
            (MODEL_KNN_G, X_g_tr, X_g_va, 1.0),
            (MODEL_KNN_W, X_w_tr, X_w_va, 1.0),
        ]:
            algo = selected_algos[model_id]
            est = build_knn_classifier(
                KNNModelSpec(
                    model_id=model_id,
                    n_neighbors=5,
                    weights="uniform",
                    metric="euclidean",
                    algorithm=algo,
                    block_weight=block_w,
                    n_jobs=selected_n_jobs,
                )
            )
            t0 = time.perf_counter()
            est.fit(X_tr, y_tr)
            fit_s = time.perf_counter() - t0

            t1 = time.perf_counter()
            probs = est.predict_proba(X_va)[:, 1]
            pred_s = time.perf_counter() - t1

            m = compute_classification_metrics(y_va, probs, threshold=0.50)
            n_uniq_scores = int(len(np.unique(np.round(probs, 6))))
            baseline_rows.append(
                {
                    "modelo_id": model_id,
                    "modelo": MODEL_LABELS_ES[model_id],
                    "hiperparametros_base": (
                        f"k=5, uniform, euclidean, algo={algo}"
                        + (f", peso_bloque={block_w:g}" if block_w > 0 else "")
                    ),
                    "n_columnas": int(X_tr.shape[1]),
                    "n_train_piloto": int(len(y_tr)),
                    "n_val_piloto": int(len(y_va)),
                    "puntajes_unicos_k5": n_uniq_scores,
                    "pr_auc_piloto": round(m["pr_auc"], 4),
                    "roc_auc_piloto": round(m["roc_auc"], 4),
                    "f1_clase_1_050": round(m["f1_pos"], 4),
                    "recall_050": round(m["recall_pos"], 4),
                    "precision_050": round(m["precision_pos"], 4),
                    "brier_piloto": round(m["brier"], 4),
                    "accuracy_050": round(m["accuracy"], 4),
                    "tiempo_fit_s": round(fit_s, 4),
                    "tiempo_predict_s": round(pred_s, 4),
                    "ms_por_1000_filas": round(1000.0 * pred_s / (len(y_va) / 1000.0), 2),
                    "memoria_matriz_train_mb": round(compute_matrix_memory_mb(X_tr), 2),
                    "rss_proceso_mb": round(current_process_rss_mb(), 1),
                }
            )

        pilot_info = {
            "personas_train_piloto": int(n_tr_p),
            "filas_train_piloto": int(len(y_tr)),
            "prevalencia_train_piloto_pct": round(100.0 * float(y_tr.mean()), 2),
            "personas_val_piloto": int(n_va_p),
            "filas_val_piloto": int(len(y_va)),
            "prevalencia_val_piloto_pct": round(100.0 * float(y_va.mean()), 2),
            "algoritmos_seleccionados": selected_algos,
            "n_jobs_seleccionado": selected_n_jobs,
        }

        return PilotSelectionBundle(
            algorithm_njobs_table=algo_njobs_df,
            selected_algorithms=selected_algos,
            selected_n_jobs=selected_n_jobs,
            baseline_pilot_table=pd.DataFrame(baseline_rows),
            pilot_split_info=pilot_info,
        )

    def run_cost_curves(
        self,
        train_blocks: KNNPartitionBlocks,
        selected_algorithms: Dict[str, str],
        selected_n_jobs: int,
        k_eval: int = 101,
        train_sizes: Sequence[int] = (10000, 25000, 50000, 100000, 200000, 400000),
        n_query_rows: int = 2000,
    ) -> CostCurveBundle:
        """Section 8: Measure fit/predict cost & peak RSS vs training size and variant with log-log slopes."""
        # Draw disjoint query rows from dedicated persons first
        unique_persons = np.unique(train_blocks.groups)
        rng = np.random.default_rng(self.config.random_state + 88)
        perm_persons = rng.permutation(unique_persons)

        # Pick enough query persons to cover n_query_rows cleanly
        q_persons = set(perm_persons[:800].tolist())
        q_all_idx = np.flatnonzero(np.isin(train_blocks.groups, list(q_persons)))
        q_idx = q_all_idx[:n_query_rows]

        pool_idx = np.flatnonzero(~np.isin(train_blocks.groups, list(q_persons)))
        pool_perm = rng.permutation(pool_idx)

        X_d_q = train_blocks.build_knn_d_matrix(q_idx)
        X_g_q = train_blocks.build_knn_g_matrix(w_g=1.0, row_idx=q_idx)
        X_w_q = train_blocks.build_knn_w_matrix(w=1.0, row_idx=q_idx)

        rows: List[Dict[str, object]] = []
        for n_tr in train_sizes:
            if n_tr > len(pool_perm):
                continue
            tr_idx = np.sort(pool_perm[:n_tr])
            y_tr = train_blocks.y[tr_idx]

            variant_inputs = [
                (MODEL_KNN_D, train_blocks.build_knn_d_matrix(tr_idx), X_d_q, selected_algorithms[MODEL_KNN_D]),
                (MODEL_KNN_G, train_blocks.build_knn_g_matrix(w_g=1.0, row_idx=tr_idx), X_g_q, selected_algorithms[MODEL_KNN_G]),
                (MODEL_KNN_W, train_blocks.build_knn_w_matrix(w=1.0, row_idx=tr_idx), X_w_q, "brute"),
            ]
            for model_id, X_tr, X_q, algo in variant_inputs:
                est = build_knn_classifier(
                    KNNModelSpec(
                        model_id=model_id,
                        n_neighbors=k_eval,
                        weights="distance",
                        metric="euclidean",
                        algorithm=algo,
                        n_jobs=selected_n_jobs,
                    )
                )
                t0 = time.perf_counter()
                est.fit(X_tr, y_tr)
                fit_s = time.perf_counter() - t0

                t1 = time.perf_counter()
                _ = est.predict_proba(X_q)
                pred_s = time.perf_counter() - t1
                rss_mb = current_process_rss_mb()

                rows.append(
                    {
                        "modelo_id": model_id,
                        "modelo": MODEL_LABELS_ES[model_id],
                        "algoritmo": algo,
                        "n_columnas": int(X_tr.shape[1]),
                        "n_train": int(n_tr),
                        "n_queries": int(len(q_idx)),
                        "k_vecinos": int(k_eval),
                        "tiempo_fit_s": round(fit_s, 4),
                        "tiempo_predict_s": round(pred_s, 4),
                        "s_por_1000_filas": round(pred_s / (len(q_idx) / 1000.0), 4),
                        "memoria_matriz_train_mb": round(compute_matrix_memory_mb(X_tr), 2),
                        "rss_proceso_mb": round(rss_mb, 1),
                    }
                )
                del est
            gc.collect()

        cost_df = pd.DataFrame(rows)

        # Fit log-log OLS slopes: log10(s_por_1000_filas) = a + b * log10(n_train)
        slope_rows: List[Dict[str, object]] = []
        for model_id in (MODEL_KNN_D, MODEL_KNN_G, MODEL_KNN_W):
            sub = cost_df.loc[cost_df["modelo_id"] == model_id].sort_values("n_train")
            if len(sub) < 2:
                continue
            log_n = np.log10(sub["n_train"].to_numpy(dtype=np.float64))
            log_t = np.log10(np.maximum(sub["s_por_1000_filas"].to_numpy(dtype=np.float64), 1e-6))
            slope, intercept = np.polyfit(log_n, log_t, deg=1)
            r_corr = float(np.corrcoef(log_n, log_t)[0, 1]) if len(sub) > 2 else 1.0
            t_min = float(sub["s_por_1000_filas"].iloc[0])
            t_max = float(sub["s_por_1000_filas"].iloc[-1])
            algo_str = str(sub["algoritmo"].iloc[0])
            if algo_str != "brute" and slope < 0.75:
                interp_str = "Sublineal (búsqueda exacta en árbol)"
            elif algo_str == "brute" and slope < 0.75:
                interp_str = "Sublineal aparente por overhead inicial (fuerza bruta densa)"
            elif slope <= 1.25:
                interp_str = "Cuasilineal O(N) (fuerza bruta / alta dimensión)"
            else:
                interp_str = "Superlineal (> O(N))"
            slope_rows.append(
                {
                    "modelo_id": model_id,
                    "algoritmo": algo_str,
                    "n_columnas": int(sub["n_columnas"].iloc[0]),
                    "pendiente_log_log_b": round(float(slope), 4),
                    "intercepto_log10": round(float(intercept), 4),
                    "r2_ajuste_log_log": round(float(r_corr**2), 4),
                    "s_por_1k_en_n_min": round(t_min, 4),
                    "s_por_1k_en_n_max": round(t_max, 4),
                    "factor_crecimiento_tiempo": round(t_max / max(t_min, 1e-6), 2),
                    "rss_pico_mb": round(float(sub["rss_proceso_mb"].max()), 1),
                    "interpretacion_escala": interp_str,
                }
            )

        return CostCurveBundle(
            cost_measurements_table=cost_df,
            loglog_slopes_table=pd.DataFrame(slope_rows),
        )

    def run_step9_full_benchmark(
        self,
        train_blocks: KNNPartitionBlocks,
        test_blocks: KNNPartitionBlocks,
        winner_specs: Dict[str, KNNModelSpec],
        n_queries: int | None = None,
    ) -> FullRunProjectionBundle:
        """Step 9: Time ~5,000 test queries against FULL 1.39M train set and extrapolate to 347,720 rows."""
        n_q = int(n_queries or self.config.benchmark_n_queries)
        n_test_full = int(len(test_blocks.y))
        q_idx = np.arange(min(n_q, n_test_full), dtype=np.int64)
        scale_factor = float(n_test_full) / float(len(q_idx))

        rows: List[Dict[str, object]] = []
        any_exceeds = False
        total_hours = 0.0

        for model_id in (MODEL_KNN_D, MODEL_KNN_G, MODEL_KNN_W):
            if model_id not in winner_specs:
                continue
            spec = winner_specs[model_id]
            if model_id == MODEL_KNN_D:
                X_tr = train_blocks.build_knn_d_matrix()
                X_q = test_blocks.build_knn_d_matrix(q_idx)
            elif model_id == MODEL_KNN_G:
                X_tr = train_blocks.build_knn_g_matrix(w_g=spec.block_weight)
                X_q = test_blocks.build_knn_g_matrix(w_g=spec.block_weight, row_idx=q_idx)
            else:
                X_tr = train_blocks.build_knn_w_matrix(w=spec.block_weight)
                X_q = test_blocks.build_knn_w_matrix(w=spec.block_weight, row_idx=q_idx)

            mem_mb = compute_matrix_memory_mb(X_tr)
            est = build_knn_classifier(spec)

            t0 = time.perf_counter()
            est.fit(X_tr, train_blocks.y)
            fit_s = time.perf_counter() - t0

            t1 = time.perf_counter()
            _ = est.predict_proba(X_q)
            pred_q_s = time.perf_counter() - t1
            rss_mb = current_process_rss_mb()

            proj_s = pred_q_s * scale_factor
            proj_min = proj_s / 60.0
            proj_h = proj_s / 3600.0
            exceeds = bool(proj_h > self.config.max_projected_hours)
            if exceeds:
                any_exceeds = True
            total_hours += proj_h

            rows.append(
                {
                    "modelo_id": model_id,
                    "modelo": MODEL_LABELS_ES[model_id],
                    "algoritmo": spec.to_sklearn_params()["algorithm"],
                    "metrica": spec.metric,
                    "k_optimo": int(spec.n_neighbors),
                    "pesos_optimos": spec.weights,
                    "peso_bloque": round(float(spec.block_weight), 4),
                    "n_jobs": int(spec.n_jobs),
                    "n_train_completo": int(len(train_blocks.y)),
                    "n_queries_benchmark": int(len(q_idx)),
                    "tiempo_fit_completo_s": round(fit_s, 3),
                    "tiempo_predict_benchmark_s": round(pred_q_s, 3),
                    "s_por_1000_filas_test": round(pred_q_s / (len(q_idx) / 1000.0), 3),
                    "proyeccion_test_completo_min": round(proj_min, 2),
                    "proyeccion_test_completo_horas": round(proj_h, 3),
                    "limite_horas": float(self.config.max_projected_hours),
                    "excede_limite_4h": exceeds,
                    "memoria_matriz_train_mb": round(mem_mb, 2),
                    "rss_pico_mb": round(rss_mb, 1),
                }
            )
            del est, X_tr, X_q
            gc.collect()

        return FullRunProjectionBundle(
            projection_table=pd.DataFrame(rows),
            any_exceeds_limit=any_exceeds,
            max_projected_hours_limit=float(self.config.max_projected_hours),
            total_projected_hours_all_models=round(total_hours, 3),
        )
