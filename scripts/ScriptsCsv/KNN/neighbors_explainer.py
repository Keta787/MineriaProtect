"""K2: Case-based explanation showing k nearest neighbors in original units for 6 typical profiles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd

from .config import ISCO_MAJOR_LABELS_ES, MODEL_KNN_D, MODEL_KNN_G
from .feature_blocks import KNNPartitionBlocks
from .models import KNNModelSpec, build_knn_classifier


@dataclass(frozen=True)
class CaseExplanationBundle:
    """Outputs of K2 (6 prototype test profiles explained by their k nearest training neighbors)."""

    model_id: str
    profiles_summary_table: pd.DataFrame
    neighbors_detail_table: pd.DataFrame


class NeighborsExplainer:
    """Explain KNN predictions by example on 6 P2-aligned test profiles in original units."""

    def __init__(self, top_neighbors_to_display: int = 5) -> None:
        self.top_neighbors_to_display = int(top_neighbors_to_display)

    def explain_six_profiles(
        self,
        train_blocks: KNNPartitionBlocks,
        test_blocks: KNNPartitionBlocks,
        orig_train: pd.DataFrame,
        orig_test: pd.DataFrame,
        model_spec: KNNModelSpec,
        knn_test_proba: np.ndarray,
        nb_h_test_proba: np.ndarray,
        eval_row_idx_test: np.ndarray | None = None,
    ) -> CaseExplanationBundle:
        """Select 6 P2-aligned profiles from evaluated test rows and extract their k nearest train neighbors."""
        if eval_row_idx_test is None:
            eval_idx = np.arange(len(orig_test), dtype=np.int64)
        else:
            eval_idx = np.asarray(eval_row_idx_test, dtype=np.int64)
        orig_eval = orig_test.iloc[eval_idx].reset_index(drop=True)

        # Quantiles computed strictly on train (same P2 definitions as Notebook 7.1)
        q25_dur, q50_dur, q75_dur = np.percentile(orig_train["dur_q"], [25.0, 50.0, 75.0])
        q50_job, q75_job, q90_job = np.percentile(orig_train["job_order"], [50.0, 75.0, 90.0])
        q75_year = np.percentile(orig_train["start_year"], 75.0)
        q90_skills = np.percentile(orig_train["n_skills_essential"], 90.0)

        # Identify highest and lowest reincidence ISCO major groups from train (support >= 200)
        isco_rates = orig_train.groupby("isco_major")["reincide"].agg(["count", "mean"])
        isco_rates = isco_rates.loc[isco_rates["count"] >= 200].sort_values("mean", ascending=False)
        high_isco = str(isco_rates.index[0])
        low_isco = str(isco_rates.index[-1])

        profile_specs = [
            (
                "K2-01 (P2-01)",
                "1. Carrera corta y reciente (primer empleo)",
                (orig_eval["job_order"] == 1)
                & (orig_eval["dur_q"] <= q50_dur)
                & (orig_eval["start_year"] >= q75_year)
                & (orig_eval["es_vigente"] == 0),
            ),
            (
                "K2-02 (P2-02)",
                "2. Carrera larga con empleo vigente",
                (orig_eval["job_order"] >= q90_job)
                & (orig_eval["dur_q"] >= q75_dur)
                & (orig_eval["es_vigente"] == 1),
            ),
            (
                "K2-03 (P2-03)",
                "3. Ocupación de alta exigencia de competencias ESCO (>= P90)",
                (orig_eval["n_skills_essential"] >= q90_skills)
                & (orig_eval["university_level"].isin(["Bachelor", "Master"]))
                & (orig_eval["job_order"] == int(q50_job)),
            ),
            (
                "K2-04 (P2-04)",
                "4. Educación 'No reportado' en trayectoria media",
                (orig_eval["university_level"] == "No reportado")
                & (orig_eval["job_order"] == int(q50_job))
                & (orig_eval["dur_q"] == q50_dur),
            ),
            (
                "K2-05 (P2-05)",
                f"5. Grupo ISCO de mayor reincidencia ({ISCO_MAJOR_LABELS_ES[high_isco]}) con rotación previa",
                (orig_eval["isco_major"] == high_isco)
                & (orig_eval["job_order"] >= q75_job)
                & (orig_eval["dur_q"] <= q25_dur),
            ),
            (
                "K2-06 (P2-06)",
                f"6. Grupo ISCO de menor reincidencia ({ISCO_MAJOR_LABELS_ES[low_isco]}) en primer empleo",
                (orig_eval["isco_major"] == low_isco)
                & (orig_eval["job_order"] == 1)
                & (orig_eval["dur_q"] >= q50_dur),
            ),
        ]

        selected_local_pos: List[int] = []
        for _, _, mask in profile_specs:
            cands = np.flatnonzero(mask.to_numpy())
            if len(cands) == 0:
                cands = np.array([0], dtype=np.int64)
            selected_local_pos.append(int(cands[0]))

        selected_global_test_idx = eval_idx[selected_local_pos]

        # Build feature matrices for full train and the 6 selected test cases ONLY (fast exact query!)
        if model_spec.model_id == MODEL_KNN_D:
            X_tr = train_blocks.build_knn_d_matrix()
            X_q6 = test_blocks.build_knn_d_matrix(selected_global_test_idx)
        elif model_spec.model_id == MODEL_KNN_G:
            X_tr = train_blocks.build_knn_g_matrix(w_g=model_spec.block_weight)
            X_q6 = test_blocks.build_knn_g_matrix(w_g=model_spec.block_weight, row_idx=selected_global_test_idx)
        else:
            X_tr = train_blocks.build_knn_w_matrix(w=model_spec.block_weight)
            X_q6 = test_blocks.build_knn_w_matrix(w=model_spec.block_weight, row_idx=selected_global_test_idx)

        est = build_knn_classifier(model_spec)
        est.fit(X_tr, train_blocks.y)
        k_val = int(model_spec.n_neighbors)
        dists, idxs = est.kneighbors(X_q6, n_neighbors=k_val, return_distance=True)
        probs_direct = est.predict_proba(X_q6)[:, 1]

        summary_rows: List[Dict[str, object]] = []
        detail_rows: List[Dict[str, object]] = []
        n_disp = min(self.top_neighbors_to_display, k_val)

        for i, (pid, title, _) in enumerate(profile_specs):
            loc_i = selected_local_pos[i]
            g_idx = int(selected_global_test_idx[i])
            q_row = orig_eval.iloc[loc_i]
            nn_ids = idxs[i]
            nn_d = dists[i]

            nn_y = train_blocks.y[nn_ids]
            nn_occ = orig_train["occupation_code"].to_numpy(dtype=str)[nn_ids]
            nn_isco = orig_train["isco_major"].to_numpy(dtype=str)[nn_ids]

            purity_occ = 100.0 * float(np.mean(nn_occ == str(q_row["occupation_code"])))
            purity_isco = 100.0 * float(np.mean(nn_isco == str(q_row["isco_major"])))
            n_pos_nn = int(np.sum(nn_y == 1))

            summary_rows.append(
                {
                    "perfil_id": pid,
                    "perfil_descripcion": title,
                    "fila_test_idx": g_idx,
                    "gran_grupo_isco": str(q_row["isco_major_label_es"]),
                    "ocupacion_esco": f"{q_row['occupation_code']} · {q_row['occupation_label']}",
                    "job_order": int(q_row["job_order"]),
                    "duracion_trimestres": round(float(q_row["dur_q"]), 1),
                    "anio_inicio": int(q_row["start_year"]),
                    "es_vigente": int(q_row["es_vigente"]),
                    "nivel_educativo": str(q_row["university_level"]),
                    "skills_esenciales": round(float(q_row["n_skills_essential"]), 1),
                    "k_vecinos": k_val,
                    "vecinos_con_reincide_1": f"{n_pos_nn}/{k_val} ({100.0 * n_pos_nn / k_val:.1f}%)",
                    "pureza_misma_ocupacion_pct": round(purity_occ, 1),
                    "pureza_mismo_isco_pct": round(purity_isco, 1),
                    "dist_vecino_1": round(float(nn_d[0]), 4),
                    "dist_vecino_k": round(float(nn_d[-1]), 4),
                    "prob_knn_pct": round(100.0 * float(knn_test_proba[loc_i]), 2),
                    "prob_knn_directa_pct": round(100.0 * float(probs_direct[i]), 2),
                    "prob_nb_h_pct": round(100.0 * float(nb_h_test_proba[loc_i]), 2),
                    "y_real": int(q_row["reincide"]),
                }
            )

            for r_pos in range(n_disp):
                tr_row_id = int(nn_ids[r_pos])
                nr = orig_train.iloc[tr_row_id]
                detail_rows.append(
                    {
                        "perfil_id": pid,
                        "rango_vecino": r_pos + 1,
                        "distancia": round(float(nn_d[r_pos]), 5),
                        "misma_ocupacion_esco": "Sí"
                        if str(nr["occupation_code"]) == str(q_row["occupation_code"])
                        else "No",
                        "mismo_grupo_isco": "Sí"
                        if str(nr["isco_major"]) == str(q_row["isco_major"])
                        else "No",
                        "gran_grupo_isco_vecino": str(nr["isco_major_label_es"]),
                        "ocupacion_esco_vecino": f"{nr['occupation_code']} · {nr['occupation_label']}",
                        "job_order_vecino": int(nr["job_order"]),
                        "duracion_trim_vecino": round(float(nr["dur_q"]), 1),
                        "anio_inicio_vecino": int(nr["start_year"]),
                        "nivel_educativo_vecino": str(nr["university_level"]),
                        "reincide_vecino": int(nr["reincide"]),
                    }
                )

        return CaseExplanationBundle(
            model_id=model_spec.model_id,
            profiles_summary_table=pd.DataFrame(summary_rows),
            neighbors_detail_table=pd.DataFrame(detail_rows),
        )
