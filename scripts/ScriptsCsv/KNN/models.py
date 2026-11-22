"""KNN model factories (KNN-D, KNN-G, KNN-W) and Section 2 manual distance walkthrough."""

from __future__ import annotations

from dataclasses import dataclass
import inspect
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier

from .config import MODEL_KNN_D, MODEL_KNN_G, MODEL_KNN_W, MODEL_LABELS_ES
from .feature_blocks import KNNPartitionBlocks

VERIFIED_KNN_INIT_PARAMS: Tuple[str, ...] = tuple(
    p for p in inspect.signature(KNeighborsClassifier.__init__).parameters if p != "self"
)


@dataclass(frozen=True)
class KNNModelSpec:
    """Specification for building an exact scikit-learn KNeighborsClassifier."""

    model_id: str
    n_neighbors: int = 5
    weights: str = "uniform"
    metric: str = "euclidean"
    algorithm: str = "auto"
    leaf_size: int = 30
    block_weight: float = 0.0
    n_jobs: int = 4

    def label_es(self) -> str:
        """Return Spanish display label for this variant."""
        return MODEL_LABELS_ES.get(self.model_id, self.model_id)

    def to_sklearn_params(self) -> Dict[str, object]:
        """Return verified KNeighborsClassifier constructor kwargs."""
        if self.model_id == MODEL_KNN_W:
            # Sparse input forces brute force in sklearn; setting explicitly prevents silent fallback UserWarning
            algo = "brute"
        else:
            algo = self.algorithm
        p_val = 1 if self.metric == "manhattan" else 2
        params: Dict[str, object] = {
            "n_neighbors": int(self.n_neighbors),
            "weights": str(self.weights),
            "algorithm": str(algo),
            "leaf_size": int(self.leaf_size),
            "p": p_val,
            "metric": str(self.metric),
            "metric_params": None,
            "n_jobs": int(self.n_jobs),
        }
        unknown = set(params.keys()) - set(VERIFIED_KNN_INIT_PARAMS)
        if unknown:
            raise ValueError(f"Unverified KNeighborsClassifier parameters: {unknown}")
        return params


def build_knn_classifier(spec: KNNModelSpec) -> KNeighborsClassifier:
    """Instantiate a KNeighborsClassifier from a validated KNNModelSpec."""
    return KNeighborsClassifier(**spec.to_sklearn_params())


def build_knn_d(
    n_neighbors: int = 5,
    weights: str = "uniform",
    metric: str = "euclidean",
    algorithm: str = "kd_tree",
    leaf_size: int = 30,
    n_jobs: int = 4,
) -> KNeighborsClassifier:
    """Factory for KNN-D (audited dense block, exact tree search)."""
    return build_knn_classifier(
        KNNModelSpec(
            model_id=MODEL_KNN_D,
            n_neighbors=n_neighbors,
            weights=weights,
            metric=metric,
            algorithm=algorithm,
            leaf_size=leaf_size,
            block_weight=0.0,
            n_jobs=n_jobs,
        )
    )


def build_knn_g(
    n_neighbors: int = 5,
    weights: str = "uniform",
    metric: str = "euclidean",
    algorithm: str = "ball_tree",
    leaf_size: int = 30,
    w_g: float = 1.0,
    n_jobs: int = 4,
) -> KNeighborsClassifier:
    """Factory for KNN-G (audited dense + 10 weighted ISCO major-group dummies)."""
    return build_knn_classifier(
        KNNModelSpec(
            model_id=MODEL_KNN_G,
            n_neighbors=n_neighbors,
            weights=weights,
            metric=metric,
            algorithm=algorithm,
            leaf_size=leaf_size,
            block_weight=w_g,
            n_jobs=n_jobs,
        )
    )


def build_knn_w(
    n_neighbors: int = 5,
    weights: str = "uniform",
    metric: str = "euclidean",
    w: float = 1.0,
    n_jobs: int = 4,
) -> KNeighborsClassifier:
    """Factory for KNN-W (audited dense + 2,967 weighted sparse occupation dummies, brute force)."""
    return build_knn_classifier(
        KNNModelSpec(
            model_id=MODEL_KNN_W,
            n_neighbors=n_neighbors,
            weights=weights,
            metric=metric,
            algorithm="brute",
            leaf_size=30,
            block_weight=w,
            n_jobs=n_jobs,
        )
    )


@dataclass(frozen=True)
class ManualKNNDemoResult:
    """Outputs of Section 2 (hand-computed KNN distances vs scikit-learn on 1 test case)."""

    test_row_index: int
    k_neighbors: int
    n_train_reference: int
    query_case_table: pd.DataFrame
    neighbors_original_units_table: pd.DataFrame
    comparison_table: pd.DataFrame
    max_abs_diff_distances: float
    max_abs_diff_proba_uniform: float
    max_abs_diff_proba_distance: float


class ManualKNNExplainer:
    """Compute exact KNN distances and class-1 probability by hand and verify against scikit-learn."""

    def __init__(self, k_neighbors: int = 5, n_reference_sample: int | None = None, random_state: int = 42) -> None:
        self.k_neighbors = int(k_neighbors)
        self.n_reference_sample = n_reference_sample
        self.random_state = int(random_state)

    @staticmethod
    def _pick_tie_free_test_index(
        X_ref: np.ndarray,
        X_test: np.ndarray,
        k: int,
        candidate_limit: int = 200,
    ) -> int:
        """Select the first test index with strictly distinct distances around rank k (no boundary tie)."""
        n_cand = min(candidate_limit, len(X_test))
        for idx in range(n_cand):
            x_q = X_test[idx]
            dists = np.sqrt(np.sum((X_ref - x_q) ** 2, axis=1))
            top = np.partition(dists, k + 1)[: k + 2]
            top_sorted = np.sort(top)
            # Ensure non-zero distances (clean distance weighting) and strict gap between k-th and (k+1)-th
            if top_sorted[0] > 1e-6 and (top_sorted[k] - top_sorted[k - 1]) > 1e-5:
                return int(idx)
        return 0

    def run_demo(
        self,
        train_blocks: KNNPartitionBlocks,
        test_blocks: KNNPartitionBlocks,
        orig_train: pd.DataFrame,
        orig_test: pd.DataFrame,
        test_row_index: int | None = None,
    ) -> ManualKNNDemoResult:
        """Compute Euclidean distances by hand for 1 test case against train and compare with sklearn."""
        k = self.k_neighbors
        if self.n_reference_sample is not None and self.n_reference_sample < len(train_blocks.y):
            rng = np.random.default_rng(self.random_state)
            ref_idx = np.sort(
                rng.choice(len(train_blocks.y), size=int(self.n_reference_sample), replace=False)
            )
        else:
            ref_idx = np.arange(len(train_blocks.y), dtype=np.int64)

        # Use float64 for machine-precision agreement verification in Section 2
        X_ref = train_blocks.X_dense_scaled[ref_idx].astype(np.float64)
        y_ref = train_blocks.y[ref_idx].astype(np.int8)
        X_te_all = test_blocks.X_dense_scaled.astype(np.float64)

        if test_row_index is None:
            test_row_index = self._pick_tie_free_test_index(X_ref, X_te_all, k=k)

        x_query = X_te_all[test_row_index]

        # 1. Manual Euclidean distance calculation: d(x, x_i) = sqrt(sum_j (x_j - x_{i,j})^2)
        diff = X_ref - x_query[np.newaxis, :]
        manual_dists_all = np.sqrt(np.sum(diff * diff, axis=1))
        # Exact partial sort + sort of top k
        part_idx = np.argpartition(manual_dists_all, k)[:k]
        order = np.argsort(manual_dists_all[part_idx], kind="mergesort")
        manual_nn_local_idx = part_idx[order]
        manual_nn_dists = manual_dists_all[manual_nn_local_idx]
        manual_nn_labels = y_ref[manual_nn_local_idx]
        manual_nn_orig_idx = ref_idx[manual_nn_local_idx]

        # Manual predicted probabilities (uniform and inverse-distance weighted)
        manual_prob_uniform = float(np.mean(manual_nn_labels == 1))
        if np.any(manual_nn_dists == 0.0):
            zero_mask = manual_nn_dists == 0.0
            manual_prob_distance = float(np.mean(manual_nn_labels[zero_mask] == 1))
            inv_weights = np.where(zero_mask, 1.0, 0.0)
        else:
            inv_weights = 1.0 / manual_nn_dists
            manual_prob_distance = float(
                np.sum(inv_weights * (manual_nn_labels == 1)) / np.sum(inv_weights)
            )
        norm_weights = inv_weights / np.sum(inv_weights)

        # 2. Scikit-learn KNeighborsClassifier verification (uniform & distance)
        knn_unif = KNeighborsClassifier(
            n_neighbors=k,
            weights="uniform",
            metric="euclidean",
            algorithm="kd_tree",
            n_jobs=1,
        )
        knn_unif.fit(X_ref, y_ref)
        sk_dists, sk_idx = knn_unif.kneighbors(x_query.reshape(1, -1), n_neighbors=k, return_distance=True)
        sk_dists_1d = sk_dists.ravel()
        sk_idx_1d = sk_idx.ravel()
        sk_prob_uniform = float(knn_unif.predict_proba(x_query.reshape(1, -1))[0, 1])

        knn_dist = KNeighborsClassifier(
            n_neighbors=k,
            weights="distance",
            metric="euclidean",
            algorithm="kd_tree",
            n_jobs=1,
        )
        knn_dist.fit(X_ref, y_ref)
        sk_prob_distance = float(knn_dist.predict_proba(x_query.reshape(1, -1))[0, 1])

        max_diff_dist = float(np.max(np.abs(manual_nn_dists - sk_dists_1d)))
        diff_prob_unif = abs(manual_prob_uniform - sk_prob_uniform)
        diff_prob_dist = abs(manual_prob_distance - sk_prob_distance)

        if max_diff_dist > 1e-9 or diff_prob_unif > 1e-12 or diff_prob_dist > 1e-12:
            raise AssertionError(
                f"Manual KNN vs sklearn mismatch: dist={max_diff_dist:.2e}, "
                f"unif={diff_prob_unif:.2e}, dist_w={diff_prob_dist:.2e}"
            )

        # Build query summary table in original units
        q_row = orig_test.iloc[test_row_index]
        query_df = pd.DataFrame(
            [
                {
                    "fila_test_idx": int(test_row_index),
                    "gran_grupo_isco": str(q_row["isco_major_label_es"]),
                    "ocupacion_esco": f"{q_row['occupation_code']} · {q_row['occupation_label']}",
                    "job_order": int(q_row["job_order"]),
                    "duracion_trimestres": round(float(q_row["dur_q"]), 1),
                    "anio_inicio": int(q_row["start_year"]),
                    "es_vigente": int(q_row["es_vigente"]),
                    "nivel_educativo": str(q_row["university_level"]),
                    "skills_esenciales": round(float(q_row["n_skills_essential"]), 1),
                    "reincide_real": int(q_row["reincide"]),
                }
            ]
        )

        # Build neighbors table in original units
        nn_rows: List[Dict[str, object]] = []
        for rank in range(k):
            tr_row_pos = int(manual_nn_orig_idx[rank])
            nr = orig_train.iloc[tr_row_pos]
            nn_rows.append(
                {
                    "rango_vecino": rank + 1,
                    "fila_train_idx": tr_row_pos,
                    "distancia_manual_euclidiana": round(float(manual_nn_dists[rank]), 6),
                    "distancia_sklearn": round(float(sk_dists_1d[rank]), 6),
                    "peso_inverso_normalizado": round(float(norm_weights[rank]), 4),
                    "gran_grupo_isco": str(nr["isco_major_label_es"]),
                    "ocupacion_esco": f"{nr['occupation_code']} · {nr['occupation_label']}",
                    "job_order": int(nr["job_order"]),
                    "duracion_trimestres": round(float(nr["dur_q"]), 1),
                    "anio_inicio": int(nr["start_year"]),
                    "nivel_educativo": str(nr["university_level"]),
                    "skills_esenciales": round(float(nr["n_skills_essential"]), 1),
                    "reincide_vecino": int(nr["reincide"]),
                }
            )
        neighbors_df = pd.DataFrame(nn_rows)

        comparison_df = pd.DataFrame(
            [
                {
                    "cantidad_verificada": f"Distancias euclidianas a los {k} vecinos (máx |diff|)",
                    "calculo_manual": f"[{manual_nn_dists[0]:.6f}, ..., {manual_nn_dists[-1]:.6f}]",
                    "scikit_learn": f"[{sk_dists_1d[0]:.6f}, ..., {sk_dists_1d[-1]:.6f}]",
                    "diferencia_absoluta_max": f"{max_diff_dist:.3e}",
                    "coincide_exactamente": bool(max_diff_dist <= 1e-9),
                },
                {
                    "cantidad_verificada": "Índices de vecinos más cercanos",
                    "calculo_manual": str(manual_nn_local_idx.tolist()),
                    "scikit_learn": str(sk_idx_1d.tolist()),
                    "diferencia_absoluta_max": "0" if np.array_equal(manual_nn_local_idx, sk_idx_1d) else "Empate",
                    "coincide_exactamente": bool(np.array_equal(manual_nn_local_idx, sk_idx_1d)),
                },
                {
                    "cantidad_verificada": "P(reincide=1 | x) · pesos uniformes (fracción de vecinos)",
                    "calculo_manual": f"{manual_prob_uniform:.6f} ({int(manual_nn_labels.sum())}/{k})",
                    "scikit_learn": f"{sk_prob_uniform:.6f}",
                    "diferencia_absoluta_max": f"{diff_prob_unif:.3e}",
                    "coincide_exactamente": bool(diff_prob_unif <= 1e-12),
                },
                {
                    "cantidad_verificada": "P(reincide=1 | x) · pesos por distancia inversa (1/d)",
                    "calculo_manual": f"{manual_prob_distance:.6f}",
                    "scikit_learn": f"{sk_prob_distance:.6f}",
                    "diferencia_absoluta_max": f"{diff_prob_dist:.3e}",
                    "coincide_exactamente": bool(diff_prob_dist <= 1e-12),
                },
            ]
        )

        return ManualKNNDemoResult(
            test_row_index=int(test_row_index),
            k_neighbors=k,
            n_train_reference=int(len(ref_idx)),
            query_case_table=query_df,
            neighbors_original_units_table=neighbors_df,
            comparison_table=comparison_df,
            max_abs_diff_distances=max_diff_dist,
            max_abs_diff_proba_uniform=diff_prob_unif,
            max_abs_diff_proba_distance=diff_prob_dist,
        )
