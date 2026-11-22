"""Section 4: Geometry, curse of dimensionality, distance contrast, and neighbor purity experiment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.metrics import pairwise_distances

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
class GeometryExperimentBundle:
    """Measured outputs of the Section 4 distance-contrast and neighbor-purity experiment."""

    geometry_table: pd.DataFrame
    sample_info: Dict[str, object]


class GeometryAnalyzer:
    """Measure distance concentration (contrast) and neighbor purity across KNN-D, KNN-G, and KNN-W."""

    def __init__(self, config: KNNConfig) -> None:
        self.config = config

    def run_experiment(
        self,
        train_blocks: KNNPartitionBlocks,
        orig_train: pd.DataFrame,
        selected_n_jobs: int = 8,
        n_ref_rows: int | None = None,
        n_query_rows: int | None = None,
        k_neighbors: int | None = None,
        block_weights: Sequence[float] | None = None,
    ) -> GeometryExperimentBundle:
        """Compute distance contrast and occupation/ISCO/class neighbor purity on fixed disjoint person samples."""
        n_ref = int(n_ref_rows or self.config.geometry_ref_rows)
        n_q = int(n_query_rows or self.config.geometry_query_rows)
        k = int(k_neighbors or self.config.geometry_k)
        bw_grid = tuple(float(w) for w in (block_weights or self.config.block_weight_grid))

        # Draw disjoint query persons and reference persons strictly inside train
        rng = np.random.default_rng(self.config.random_state + 404)
        unique_persons = np.unique(train_blocks.groups)
        perm_persons = rng.permutation(unique_persons)

        # Allocate first 1,000 persons for query pool, remaining for reference pool
        q_person_set = set(perm_persons[:1000].tolist())
        q_pool = np.flatnonzero(np.isin(train_blocks.groups, list(q_person_set)))
        ref_pool = np.flatnonzero(~np.isin(train_blocks.groups, list(q_person_set)))

        q_idx = np.sort(rng.choice(q_pool, size=min(n_q, len(q_pool)), replace=False))
        ref_idx = np.sort(rng.choice(ref_pool, size=min(n_ref, len(ref_pool)), replace=False))
        # Fixed 2,000-row subset of ref_idx for exact full-distribution pairwise contrast stats
        ref_contrast_local = np.sort(
            rng.choice(len(ref_idx), size=min(2000, len(ref_idx)), replace=False)
        )
        ref_contrast_idx = ref_idx[ref_contrast_local]

        occ_ref = orig_train["occupation_code"].to_numpy(dtype=str)[ref_idx]
        occ_q = orig_train["occupation_code"].to_numpy(dtype=str)[q_idx]
        isco_ref = orig_train["isco_major"].to_numpy(dtype=str)[ref_idx]
        isco_q = orig_train["isco_major"].to_numpy(dtype=str)[q_idx]
        y_ref = train_blocks.y[ref_idx]
        y_q = train_blocks.y[q_idx]

        # Build experiment specs: KNN-D (w=0), KNN-G (bw_grid), KNN-W (bw_grid)
        specs: List[tuple[str, float, str]] = [(MODEL_KNN_D, 0.0, "kd_tree")]
        for wg in bw_grid:
            specs.append((MODEL_KNN_G, wg, "brute"))
        for w in bw_grid:
            specs.append((MODEL_KNN_W, w, "brute"))

        rows: List[Dict[str, object]] = []
        for model_id, bw, algo in specs:
            if model_id == MODEL_KNN_D:
                X_ref = train_blocks.build_knn_d_matrix(ref_idx)
                X_q = train_blocks.build_knn_d_matrix(q_idx)
                X_rc = train_blocks.build_knn_d_matrix(ref_contrast_idx)
            elif model_id == MODEL_KNN_G:
                X_ref = train_blocks.build_knn_g_matrix(w_g=bw, row_idx=ref_idx)
                X_q = train_blocks.build_knn_g_matrix(w_g=bw, row_idx=q_idx)
                X_rc = train_blocks.build_knn_g_matrix(w_g=bw, row_idx=ref_contrast_idx)
            else:
                X_ref = train_blocks.build_knn_w_matrix(w=bw, row_idx=ref_idx)
                X_q = train_blocks.build_knn_w_matrix(w=bw, row_idx=q_idx)
                X_rc = train_blocks.build_knn_w_matrix(w=bw, row_idx=ref_contrast_idx)

            # 1. Global pairwise distance concentration on X_q vs X_rc (2,000 x 2,000)
            D_global = pairwise_distances(X_q, X_rc, metric="euclidean", n_jobs=selected_n_jobs)
            d_mean_per_q = np.mean(D_global, axis=1)
            d_std_per_q = np.std(D_global, axis=1)
            cv_per_q = d_std_per_q / np.maximum(d_mean_per_q, 1e-12)

            d_p05 = np.percentile(D_global, 5.0, axis=1)
            d_p50 = np.percentile(D_global, 50.0, axis=1)
            d_p95 = np.percentile(D_global, 95.0, axis=1)
            rel_iqr_p95_p05 = (d_p95 - d_p05) / np.maximum(d_p50, 1e-12)

            # Strictly positive d_min per query to avoid division by 0 on exact duplicates
            D_pos = np.where(D_global > 1e-9, D_global, np.inf)
            d_min_pos = np.min(D_pos, axis=1)
            d_max = np.max(D_global, axis=1)
            finite_mask = np.isfinite(d_min_pos) & (d_min_pos > 0.0)
            rel_contrast_max_min = float(
                np.median((d_max[finite_mask] - d_min_pos[finite_mask]) / d_min_pos[finite_mask])
            )

            # 2. Exact k-nearest neighbors on full 50,000 reference sample
            est = build_knn_classifier(
                KNNModelSpec(
                    model_id=model_id,
                    n_neighbors=k,
                    weights="uniform",
                    metric="euclidean",
                    algorithm=algo,
                    block_weight=bw,
                    n_jobs=selected_n_jobs,
                )
            )
            est.fit(X_ref, y_ref)
            nn_dists, nn_idx = est.kneighbors(X_q, n_neighbors=k, return_distance=True)

            # Neighbor purity (share of k neighbors sharing occupation_code, isco_major, and class y)
            same_occ = (occ_ref[nn_idx] == occ_q[:, np.newaxis]).mean(axis=1)
            same_isco = (isco_ref[nn_idx] == isco_q[:, np.newaxis]).mean(axis=1)
            same_y = (y_ref[nn_idx] == y_q[:, np.newaxis]).mean(axis=1)
            zero_dist_share = (nn_dists <= 1e-9).mean(axis=1)

            # Local contrast ratio d_k / d_1+ (median over queries with positive d_1)
            nn_pos = np.where(nn_dists > 1e-9, nn_dists, np.inf)
            d1_pos = np.min(nn_pos, axis=1)
            dk = nn_dists[:, -1]
            valid_loc = np.isfinite(d1_pos) & (d1_pos > 0.0)
            median_dk_over_d1 = (
                float(np.median(dk[valid_loc] / d1_pos[valid_loc])) if np.any(valid_loc) else np.nan
            )

            rows.append(
                {
                    "modelo_id": model_id,
                    "variante": MODEL_LABELS_ES[model_id],
                    "dimension_total": int(X_ref.shape[1]),
                    "peso_bloque_w": round(float(bw), 3),
                    "salto_teorico_oficio_distinto": round(float(bw * np.sqrt(2.0)), 4),
                    "dist_media_global": round(float(np.mean(d_mean_per_q)), 4),
                    "dist_std_global": round(float(np.mean(d_std_per_q)), 4),
                    "contraste_cv_std_sobre_media": round(float(np.mean(cv_per_q)), 4),
                    "contraste_mediana_dmax_dmin_sobre_dmin": round(rel_contrast_max_min, 4),
                    "contraste_p95_p05_sobre_p50": round(float(np.mean(rel_iqr_p95_p05)), 4),
                    "dist_mediana_vecino_k": round(float(np.median(dk)), 4),
                    "razon_local_dk_sobre_d1_pos": round(median_dk_over_d1, 4),
                    "pct_vecinos_dist_cero": round(100.0 * float(np.mean(zero_dist_share)), 2),
                    "pureza_misma_ocupacion_esco_pct": round(100.0 * float(np.mean(same_occ)), 2),
                    "pureza_mismo_grupo_isco_pct": round(100.0 * float(np.mean(same_isco)), 2),
                    "pureza_misma_clase_reincide_pct": round(100.0 * float(np.mean(same_y)), 2),
                }
            )

        sample_info = {
            "n_ref_filas_train": int(len(ref_idx)),
            "n_ref_personas": int(len(np.unique(train_blocks.groups[ref_idx]))),
            "n_consultas_filas_train": int(len(q_idx)),
            "n_consultas_personas": int(len(np.unique(train_blocks.groups[q_idx]))),
            "personas_solapadas_ref_consulta": int(
                len(set(train_blocks.groups[ref_idx]).intersection(set(train_blocks.groups[q_idx])))
            ),
            "k_vecinos_evaluado": int(k),
            "n_ref_contraste_global": int(len(ref_contrast_idx)),
        }
        return GeometryExperimentBundle(
            geometry_table=pd.DataFrame(rows),
            sample_info=sample_info,
        )
