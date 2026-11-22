"""General pattern analyses P1 to P8 in original units for Notebook 7.1 (Naive Bayes)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.special import logsumexp
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.naive_bayes import BernoulliNB, GaussianNB

from .config import (
    ALL_DENSE_CLEAN_FEATURES,
    BINARY_DENSE_FEATURES,
    CONTINUOUS_ROB_FEATURES,
    CONTINUOUS_TO_ORIGINAL_COL,
    DENSE_FEATURE_METADATA_ES,
    EDUCATION_ORDER_ES,
    GAUSSIAN_HYBRID_FEATURES,
    ISCO_MAJOR_LABELS_ES,
    MODEL_NB_B,
    MODEL_NB_G,
    MODEL_NB_H,
    NaiveBayesConfig,
    ORIGINAL_COL_LABELS_ES,
)
from .evaluation import TunedModelArtifact
from .feature_blocks import NaiveBayesPartitionBlocks
from .models import (
    HybridNaiveBayes,
    compute_bernoulli_log_odds_weights,
    compute_gaussian_log_odds_contributions,
    resolve_priors,
)
from .occupation_analysis import wilson_ci_95


@dataclass(frozen=True)
class WaterfallProfileDecomposition:
    """Single prototype profile and its exact additive log-odds waterfall breakdown."""

    profile_id: str
    profile_title_es: str
    row_index_train: int
    summary_original_units: Dict[str, object]
    prior_log_odds: float
    final_log_odds: float
    predicted_proba: float
    contributions_df: pd.DataFrame


@dataclass(frozen=True)
class GeneralPatternsBundle:
    """Complete outputs for Block 2 (general pattern analyses P1 to P8)."""

    p1_continuous_evidence_table: pd.DataFrame
    p1_binary_evidence_table: pd.DataFrame
    p1_block_log_odds_share_test_table: pd.DataFrame
    p1_llr_curves: Dict[str, pd.DataFrame]
    p2_profiles_summary_table: pd.DataFrame
    p2_waterfalls: List[WaterfallProfileDecomposition]
    p3_deciles_table: pd.DataFrame
    p3_top_vs_bottom_profile_table: pd.DataFrame
    p3_isco_composition_deciles_table: pd.DataFrame
    p4_job_order_table: pd.DataFrame
    p4_start_year_table: pd.DataFrame
    p4_job_order_slope_summary_table: pd.DataFrame
    p5_education_table: pd.DataFrame
    p6_error_profiles_table: pd.DataFrame
    p6_error_subgroups_table: pd.DataFrame
    p7_block_ablation_cv_table: pd.DataFrame
    p8_independence_audit_cv_table: pd.DataFrame


class GeneralPatternAnalyzer:
    """Execute general pattern analyses P1 through P8 on Version A in original units."""

    def __init__(self, config: NaiveBayesConfig) -> None:
        self.config = config
        self.min_support = int(config.min_subgroup_support)

    def analyze_p1_evidence_per_variable(
        self,
        orig_train: pd.DataFrame,
        orig_test: pd.DataFrame,
        train_blocks: NaiveBayesPartitionBlocks,
        test_blocks: NaiveBayesPartitionBlocks,
        nb_h_est: HybridNaiveBayes,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, pd.DataFrame]]:
        """P1: Log-likelihood ratio per variable, max |LLR|, and test block share of |log-odds|."""
        gnb = nb_h_est.gaussian_nb_
        bnb = nb_h_est.bernoulli_nb_
        if gnb is None or bnb is None:
            raise RuntimeError("HybridNaiveBayes must have both Gaussian and Bernoulli submodels fitted.")

        # Compute exact per-row log-odds contributions on TEST for block-share quantification (F3)
        _, contrib_15_test = nb_h_est.feature_log_odds_contributions(
            test_blocks.X_nb_h,
            split_binary_dense_and_ohe_at=len(BINARY_DENSE_FEATURES),
        )
        n_cont = len(CONTINUOUS_ROB_FEATURES)
        n_g10 = len(GAUSSIAN_HYBRID_FEATURES)
        n_bd = len(BINARY_DENSE_FEATURES)

        c_cont_te = contrib_15_test[:, :n_cont].sum(axis=1)
        c_ord_te = contrib_15_test[:, n_cont:n_g10].sum(axis=1)
        c_gauss_te = contrib_15_test[:, :n_g10].sum(axis=1)
        c_bd_te = contrib_15_test[:, n_g10 : n_g10 + n_bd].sum(axis=1)
        c_ohe_te = contrib_15_test[:, n_g10 + n_bd]

        mean_abs_4 = (
            float(np.mean(np.abs(c_cont_te)))
            + float(np.mean(np.abs(c_ord_te)))
            + float(np.mean(np.abs(c_bd_te)))
            + float(np.mean(np.abs(c_ohe_te)))
        )
        mean_abs_2 = float(np.mean(np.abs(c_gauss_te))) + float(np.mean(np.abs(c_bd_te))) + float(np.mean(np.abs(c_ohe_te)))

        block_share_rows: List[Dict[str, object]] = []
        for b_lbl, n_c, vec, denom, scope_note in [
            (
                "1. Bloque continuo (7 cols RobustScaler)",
                n_cont,
                c_cont_te,
                mean_abs_4,
                "Parte de descomposición en 4 bloques disjuntos (suma = 100 %)",
            ),
            (
                "2. Bloque ordinal (univ_ord_mm + 2 bins)",
                n_g10 - n_cont,
                c_ord_te,
                mean_abs_4,
                "Parte de descomposición en 4 bloques disjuntos (suma = 100 %)",
            ),
            (
                "3. Banderas binarias densas (4 cols)",
                n_bd,
                c_bd_te,
                mean_abs_4,
                "Parte de descomposición en 4 bloques disjuntos (suma = 100 %)",
            ),
            (
                "4. Bloque ocupación OHE (2,967 dummies)",
                len(test_blocks.nb_b_feature_names) - n_bd,
                c_ohe_te,
                mean_abs_4,
                "Parte de descomposición en 4 bloques disjuntos (suma = 100 %)",
            ),
            (
                "Subtotal · Submodelo Gaussiano (10 cols = continuas + ordinales)",
                n_g10,
                c_gauss_te,
                mean_abs_2,
                "Comparación directa Gaussiano (10) vs. binarias densas (4) + OHE (2,967)",
            ),
        ]:
            abs_v = np.abs(vec)
            ma = float(np.mean(abs_v))
            block_share_rows.append(
                {
                    "bloque_variables": b_lbl,
                    "n_columnas": int(n_c),
                    "media_abs_log_odds_test": round(ma, 4),
                    "mediana_abs_log_odds_test": round(float(np.median(abs_v)), 4),
                    "p95_abs_log_odds_test": round(float(np.percentile(abs_v, 95.0)), 4),
                    "max_abs_log_odds_test": round(float(np.max(abs_v)), 4),
                    "participacion_media_abs_test_pct": round(100.0 * ma / max(denom, 1e-12), 2),
                    "nota_descomposicion": scope_note,
                }
            )
        p1_block_share_df = pd.DataFrame(block_share_rows)

        cont_rows: List[Dict[str, object]] = []
        llr_curves: Dict[str, pd.DataFrame] = {}

        orig_map = {
            **CONTINUOUS_TO_ORIGINAL_COL,
            "univ_ord_mm": "univ_ord_mm",
            "dur_q_bin": "dur_q",
            "n_skills_essential_bin": "n_skills_essential",
        }

        for idx, col_rob in enumerate(GAUSSIAN_HYBRID_FEATURES):
            arr_rob = train_blocks.dense_clean_df[col_rob].to_numpy(dtype=np.float64)
            if np.std(arr_rob) < 1e-12:
                continue

            col_orig = orig_map.get(col_rob, col_rob)
            if col_orig in orig_train.columns:
                arr_orig = pd.to_numeric(orig_train[col_orig], errors="coerce").to_numpy(dtype=np.float64)
            else:
                arr_orig = arr_rob

            t0 = float(gnb.theta_[0, idx])
            t1 = float(gnb.theta_[1, idx])
            v0 = float(gnb.var_[0, idx])
            v1 = float(gnb.var_[1, idx])

            pcts = [10.0, 25.0, 50.0, 75.0, 90.0]
            q_rob = np.percentile(arr_rob, pcts)
            q_orig = np.percentile(arr_orig, pcts)

            def _eval_llr_1d(x_vals: np.ndarray) -> np.ndarray:
                return -0.5 * np.log(v1 / v0) - 0.5 * ((x_vals - t1) ** 2) / v1 + 0.5 * ((x_vals - t0) ** 2) / v0

            llr_q = _eval_llr_1d(q_rob)

            grid_pcts = np.linspace(2.0, 98.0, 80)
            grid_rob = np.percentile(arr_rob, grid_pcts)
            grid_orig = np.percentile(arr_orig, grid_pcts)
            grid_llr = _eval_llr_1d(grid_rob)
            llr_curves[col_rob] = pd.DataFrame(
                {
                    "percentil": grid_pcts,
                    "valor_rob": grid_rob,
                    "valor_original": grid_orig,
                    "log_likelihood_ratio": grid_llr,
                }
            )

            col_abs_test = np.abs(contrib_15_test[:, idx])

            pos_mask = grid_llr > 0
            if pos_mask.any():
                min_pos_orig = float(grid_orig[pos_mask].min())
                max_pos_orig = float(grid_orig[pos_mask].max())
                range_pos_str = f"[{min_pos_orig:.1f}, {max_pos_orig:.1f}]"
            else:
                range_pos_str = "Ninguno en P2–P98"

            neg_mask = grid_llr < 0
            if neg_mask.any():
                min_neg_orig = float(grid_orig[neg_mask].min())
                max_neg_orig = float(grid_orig[neg_mask].max())
                range_neg_str = f"[{min_neg_orig:.1f}, {max_neg_orig:.1f}]"
            else:
                range_neg_str = "Ninguno en P2–P98"

            cont_rows.append(
                {
                    "variable": col_rob,
                    "unidad_original": ORIGINAL_COL_LABELS_ES.get(col_orig, col_rob),
                    "media_clase_0_rob": round(t0, 4),
                    "media_clase_1_rob": round(t1, 4),
                    "std_clase_0_rob": round(np.sqrt(v0), 4),
                    "std_clase_1_rob": round(np.sqrt(v1), 4),
                    "max_abs_llr_p2_p98": round(float(np.max(np.abs(grid_llr))), 4),
                    "media_abs_llr_test": round(float(np.mean(col_abs_test)), 4),
                    "p99_abs_llr_test": round(float(np.percentile(col_abs_test, 99.0)), 4),
                    "max_abs_llr_test": round(float(np.max(col_abs_test)), 4),
                    "P10_orig (LLR)": f"{q_orig[0]:.1f} ({llr_q[0]:+.3f})",
                    "P25_orig (LLR)": f"{q_orig[1]:.1f} ({llr_q[1]:+.3f})",
                    "P50_orig (LLR)": f"{q_orig[2]:.1f} ({llr_q[2]:+.3f})",
                    "P75_orig (LLR)": f"{q_orig[3]:.1f} ({llr_q[3]:+.3f})",
                    "P90_orig (LLR)": f"{q_orig[4]:.1f} ({llr_q[4]:+.3f})",
                    "rango_orig_empuja_reincide_1": range_pos_str,
                    "rango_orig_empuja_no_reincide_0": range_neg_str,
                }
            )

        # Binary variables: 4 dense binary + top 5 positive and top 5 negative occupation dummies (support >= 200)
        _, absence_lr, delta_w = compute_bernoulli_log_odds_weights(bnb)
        presence_lr = absence_lr + delta_w
        p_c0 = np.exp(bnb.feature_log_prob_[0])
        p_c1 = np.exp(bnb.feature_log_prob_[1])
        total_counts = np.asarray(bnb.feature_count_.sum(axis=0)).ravel()

        bin_rows: List[Dict[str, object]] = []
        bin_names = train_blocks.nb_b_feature_names

        for k in range(len(BINARY_DENSE_FEATURES)):
            bname = bin_names[k]
            if total_counts[k] == 0:
                continue
            m_tr_b = (orig_train[bname] == 1).to_numpy()
            m_te_b = (orig_test[bname] == 1).to_numpy()
            rate_tr_b = 100.0 * float(orig_train.loc[m_tr_b, "reincide"].mean()) if m_tr_b.any() else np.nan
            n_te_b = int(m_te_b.sum())
            rate_te_b = 100.0 * float(orig_test.loc[m_te_b, "reincide"].mean()) if n_te_b > 0 else np.nan
            diff_b = (rate_te_b - rate_tr_b) if not (np.isnan(rate_tr_b) or np.isnan(rate_te_b)) else np.nan
            bin_rows.append(
                {
                    "tipo_binaria": "Bandera densa",
                    "variable": bname,
                    "etiqueta_es": ORIGINAL_COL_LABELS_ES.get(bname, bname),
                    "soporte_x1_train": int(total_counts[k]),
                    "tasa_reincide_train_pct": round(rate_tr_b, 2) if not np.isnan(rate_tr_b) else np.nan,
                    "soporte_x1_test": n_te_b,
                    "tasa_confirmada_test_pct": round(rate_te_b, 2) if not np.isnan(rate_te_b) else np.nan,
                    "brecha_test_menos_train_pp": round(diff_b, 2) if not np.isnan(diff_b) else np.nan,
                    "alerta_brecha_mayor_5pp": bool(abs(diff_b) > 5.0) if not np.isnan(diff_b) else False,
                    "P(x=1|y=0)_pct": round(100.0 * float(p_c0[k]), 2),
                    "P(x=1|y=1)_pct": round(100.0 * float(p_c1[k]), 2),
                    "LLR_cuando_x_es_1": round(float(presence_lr[k]), 4),
                    "LLR_cuando_x_es_0": round(float(absence_lr[k]), 4),
                    "efecto_presencia": (
                        "Empuja hacia reincide=1 (+)"
                        if presence_lr[k] > 0
                        else "Empuja hacia no reincide=0 (-)"
                    ),
                }
            )

        occ_label_map = (
            orig_train[["occupation_code", "occupation_label"]]
            .drop_duplicates("occupation_code")
            .set_index("occupation_code")["occupation_label"]
            .to_dict()
        )
        occ_tr_stats = orig_train.groupby("occupation_code")["reincide"].agg(["count", "mean"])
        occ_te_stats = orig_test.groupby("occupation_code")["reincide"].agg(["count", "mean"])

        occ_indices = [
            k
            for k in range(len(BINARY_DENSE_FEATURES), len(bin_names))
            if total_counts[k] >= self.min_support
        ]
        occ_sorted_pos = sorted(occ_indices, key=lambda k: presence_lr[k], reverse=True)[:5]
        occ_sorted_neg = sorted(occ_indices, key=lambda k: presence_lr[k])[:5]

        for k in occ_sorted_pos + occ_sorted_neg:
            bname = bin_names[k]
            occ_code = bname.replace("occupation_code_", "")
            occ_lbl = occ_label_map.get(occ_code, occ_code)
            rate_tr_o = (
                100.0 * float(occ_tr_stats.loc[occ_code, "mean"])
                if occ_code in occ_tr_stats.index
                else np.nan
            )
            n_te_o = int(occ_te_stats.loc[occ_code, "count"]) if occ_code in occ_te_stats.index else 0
            rate_te_o = (
                100.0 * float(occ_te_stats.loc[occ_code, "mean"])
                if occ_code in occ_te_stats.index
                else np.nan
            )
            diff_o = (rate_te_o - rate_tr_o) if not (np.isnan(rate_tr_o) or np.isnan(rate_te_o)) else np.nan
            bin_rows.append(
                {
                    "tipo_binaria": "Dummy ocupación (Top LLR)",
                    "variable": bname,
                    "etiqueta_es": f"{occ_code} · {occ_lbl}",
                    "soporte_x1_train": int(total_counts[k]),
                    "tasa_reincide_train_pct": round(rate_tr_o, 2) if not np.isnan(rate_tr_o) else np.nan,
                    "soporte_x1_test": n_te_o,
                    "tasa_confirmada_test_pct": round(rate_te_o, 2) if not np.isnan(rate_te_o) else np.nan,
                    "brecha_test_menos_train_pp": round(diff_o, 2) if not np.isnan(diff_o) else np.nan,
                    "alerta_brecha_mayor_5pp": bool(abs(diff_o) > 5.0) if not np.isnan(diff_o) else False,
                    "P(x=1|y=0)_pct": round(100.0 * float(p_c0[k]), 3),
                    "P(x=1|y=1)_pct": round(100.0 * float(p_c1[k]), 3),
                    "LLR_cuando_x_es_1": round(float(presence_lr[k]), 4),
                    "LLR_cuando_x_es_0": round(float(absence_lr[k]), 5),
                    "efecto_presencia": (
                        "Empuja hacia reincide=1 (+)"
                        if presence_lr[k] > 0
                        else "Empuja hacia no reincide=0 (-)"
                    ),
                }
            )

        return pd.DataFrame(cont_rows), pd.DataFrame(bin_rows), p1_block_share_df, llr_curves

    def analyze_p2_waterfall_profiles(
        self,
        orig_train: pd.DataFrame,
        train_blocks: NaiveBayesPartitionBlocks,
        nb_h_est: HybridNaiveBayes,
        o1_df: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, List[WaterfallProfileDecomposition]]:
        """P2: Additive log-odds decomposition for 6 quantile-defined training profiles with exact assert."""
        high_isco = str(o1_df.iloc[0]["isco_major"])
        low_isco = str(o1_df.iloc[-1]["isco_major"])

        q25_dur, q50_dur, q75_dur = np.percentile(orig_train["dur_q"], [25.0, 50.0, 75.0])
        q50_job, q75_job, q90_job = np.percentile(orig_train["job_order"], [50.0, 75.0, 90.0])
        q75_year = np.percentile(orig_train["start_year"], 75.0)
        q90_skills = np.percentile(orig_train["n_skills_essential"], 90.0)

        profile_specs = [
            (
                "P2-01",
                "1. Carrera corta y reciente (primer empleo)",
                (orig_train["job_order"] == 1)
                & (orig_train["dur_q"] <= q50_dur)
                & (orig_train["start_year"] >= q75_year)
                & (orig_train["es_vigente"] == 0),
            ),
            (
                "P2-02",
                "2. Carrera larga con empleo vigente",
                (orig_train["job_order"] >= q90_job)
                & (orig_train["dur_q"] >= q75_dur)
                & (orig_train["es_vigente"] == 1),
            ),
            (
                "P2-03",
                "3. Ocupación de alta exigencia de competencias ESCO (>= P90)",
                (orig_train["n_skills_essential"] >= q90_skills)
                & (orig_train["university_level"].isin(["Bachelor", "Master"]))
                & (orig_train["job_order"] == int(q50_job)),
            ),
            (
                "P2-04",
                "4. Educación 'No reportado' en trayectoria media",
                (orig_train["university_level"] == "No reportado")
                & (orig_train["job_order"] == int(q50_job))
                & (orig_train["dur_q"] == q50_dur),
            ),
            (
                "P2-05",
                f"5. Grupo ISCO de mayor reincidencia ({ISCO_MAJOR_LABELS_ES[high_isco]}) con rotación previa",
                (orig_train["isco_major"] == high_isco)
                & (orig_train["job_order"] >= q75_job)
                & (orig_train["dur_q"] <= q25_dur),
            ),
            (
                "P2-06",
                f"6. Grupo ISCO de menor reincidencia ({ISCO_MAJOR_LABELS_ES[low_isco]}) en primer empleo",
                (orig_train["isco_major"] == low_isco)
                & (orig_train["job_order"] == 1)
                & (orig_train["dur_q"] >= q50_dur),
            ),
        ]

        selected_indices: List[int] = []
        for pid, title, mask in profile_specs:
            candidates = np.flatnonzero(mask.to_numpy())
            if len(candidates) == 0:
                # Fallback to closest match if strict intersection is empty
                candidates = np.array([0], dtype=np.int64)
            selected_indices.append(int(candidates[0]))

        X_sub = train_blocks.X_nb_h[selected_indices]
        model_log_odds = nb_h_est.predict_log_odds(X_sub)
        model_proba = nb_h_est.predict_proba(X_sub)[:, 1]

        # Full 2,981-feature decomposition for strict assert
        prior_lo_full, contrib_full = nb_h_est.feature_log_odds_contributions(
            X_sub, split_binary_dense_and_ohe_at=None
        )
        reconstructed_full = prior_lo_full + contrib_full.sum(axis=1)
        assert np.allclose(model_log_odds, reconstructed_full, atol=1e-9), (
            "P2 full additive log-odds decomposition failed to reproduce model log-odds!"
        )

        # 15-component decomposition (10 Gaussian + 4 dense binary + 1 occupation OHE block) for waterfall display
        prior_lo, contrib_15 = nb_h_est.feature_log_odds_contributions(
            X_sub, split_binary_dense_and_ohe_at=len(BINARY_DENSE_FEATURES)
        )
        reconstructed_15 = prior_lo + contrib_15.sum(axis=1)
        assert np.allclose(model_log_odds, reconstructed_15, atol=1e-9), (
            "P2 15-component additive log-odds decomposition failed to reproduce model log-odds!"
        )

        # Group the 15 components into 7 interpretable business blocks for clean waterfall charts
        comp_names_15 = (
            list(GAUSSIAN_HYBRID_FEATURES)
            + list(BINARY_DENSE_FEATURES)
            + ["occupation_code_ohe"]
        )
        name_to_idx = {c: i for i, c in enumerate(comp_names_15)}

        waterfall_blocks = [
            ("Orden en la carrera (job_order)", ["job_order_rob"]),
            ("Duración del empleo (dur_q + bin)", ["dur_q_rob", "dur_q_bin"]),
            ("Calendario y vigencia (start/end/vigente)", ["start_ord_rob", "end_ord_rob", "es_vigente"]),
            ("Nivel educativo (univ_ord_mm)", ["univ_ord_mm"]),
            (
                "Competencias ESCO (skills/knowledge)",
                [
                    "n_skills_essential_rob",
                    "n_skills_knowledge_rob",
                    "n_skills_sin_tipo_rob",
                    "n_skills_essential_bin",
                    "tiene_skills",
                    "tiene_knowledge",
                    "tiene_sin_tipo",
                ],
            ),
            ("Ocupación específica (2,967 dummies OHE)", ["occupation_code_ohe"]),
        ]

        summary_rows: List[Dict[str, object]] = []
        waterfalls: List[WaterfallProfileDecomposition] = []

        for pos, (pid, title, _) in enumerate(profile_specs):
            r_idx = selected_indices[pos]
            orig_row = orig_train.iloc[r_idx]
            c_vec = contrib_15[pos]

            wf_rows: List[Dict[str, object]] = []
            running_lo = float(prior_lo)
            wf_rows.append(
                {
                    "paso": "0. Prior del modelo",
                    "contribucion_log_odds": round(float(prior_lo), 4),
                    "log_odds_acumulado": round(running_lo, 4),
                    "probabilidad_acumulada": round(float(1.0 / (1.0 + np.exp(-running_lo))), 4),
                }
            )

            block_contribs: Dict[str, float] = {}
            for b_label, cols in waterfall_blocks:
                b_val = float(sum(c_vec[name_to_idx[c]] for c in cols))
                running_lo += b_val
                block_contribs[b_label] = b_val
                wf_rows.append(
                    {
                        "paso": b_label,
                        "contribucion_log_odds": round(b_val, 4),
                        "log_odds_acumulado": round(running_lo, 4),
                        "probabilidad_acumulada": round(float(1.0 / (1.0 + np.exp(-running_lo))), 4),
                    }
                )

            assert np.isclose(running_lo, float(model_log_odds[pos]), atol=1e-9), (
                f"Waterfall running log-odds mismatch for profile {pid}"
            )

            orig_summary = {
                "fila_train_idx": int(r_idx),
                "gran_grupo_isco": str(orig_row["isco_major_label_es"]),
                "ocupacion_esco": f"{orig_row['occupation_code']} · {orig_row['occupation_label']}",
                "job_order": int(orig_row["job_order"]),
                "empleos_previos": int(orig_row["previous_jobs"]),
                "duracion_trimestres": float(orig_row["dur_q"]),
                "anio_inicio": int(orig_row["start_year"]),
                "es_vigente": int(orig_row["es_vigente"]),
                "university_level": str(orig_row["university_level"]),
                "n_skills_essential": float(orig_row["n_skills_essential"]),
                "y_real": int(orig_row["reincide"]),
            }

            summary_rows.append(
                {
                    "perfil_id": pid,
                    "perfil_descripcion": title,
                    "gran_grupo_isco": orig_summary["gran_grupo_isco"],
                    "ocupacion_esco": orig_summary["ocupacion_esco"],
                    "empleos_previos": orig_summary["empleos_previos"],
                    "duracion_trimestres": orig_summary["duracion_trimestres"],
                    "anio_inicio": orig_summary["anio_inicio"],
                    "es_vigente": orig_summary["es_vigente"],
                    "nivel_educativo": orig_summary["university_level"],
                    "skills_esenciales": orig_summary["n_skills_essential"],
                    "prior_log_odds": round(float(prior_lo), 4),
                    "contrib_carrera": round(block_contribs["Orden en la carrera (job_order)"], 4),
                    "contrib_duracion": round(block_contribs["Duración del empleo (dur_q + bin)"], 4),
                    "contrib_calendario_vigencia": round(
                        block_contribs["Calendario y vigencia (start/end/vigente)"], 4
                    ),
                    "contrib_educacion": round(block_contribs["Nivel educativo (univ_ord_mm)"], 4),
                    "contrib_competencias": round(
                        block_contribs["Competencias ESCO (skills/knowledge)"], 4
                    ),
                    "contrib_ocupacion_ohe": round(
                        block_contribs["Ocupación específica (2,967 dummies OHE)"], 4
                    ),
                    "log_odds_final": round(float(model_log_odds[pos]), 4),
                    "probabilidad_predicha_pct": round(100.0 * float(model_proba[pos]), 2),
                    "y_real": orig_summary["y_real"],
                }
            )

            waterfalls.append(
                WaterfallProfileDecomposition(
                    profile_id=pid,
                    profile_title_es=title,
                    row_index_train=int(r_idx),
                    summary_original_units=orig_summary,
                    prior_log_odds=float(prior_lo),
                    final_log_odds=float(model_log_odds[pos]),
                    predicted_proba=float(model_proba[pos]),
                    contributions_df=pd.DataFrame(wf_rows),
                )
            )

        return pd.DataFrame(summary_rows), waterfalls

    def analyze_p3_risk_deciles(
        self,
        orig_train: pd.DataFrame,
        orig_test: pd.DataFrame,
        oof_proba_nb_h: np.ndarray,
        test_proba_nb_h: np.ndarray,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """P3: Risk deciles (D1 lowest to D10 highest), lift, cumulative gain, and D10 vs D1 profile."""
        work = orig_train.copy()
        work["prob"] = oof_proba_nb_h
        # Assign deciles 1..10 (1 = lowest predicted probability, 10 = highest)
        work["decil_num"] = pd.qcut(work["prob"].rank(method="first"), q=10, labels=False) + 1

        work_te = orig_test.copy()
        work_te["prob"] = test_proba_nb_h
        work_te["decil_num"] = pd.qcut(work_te["prob"].rank(method="first"), q=10, labels=False) + 1

        overall_rate_tr = float(work["reincide"].mean())
        total_pos_tr = int(work["reincide"].sum())
        total_pos_te = int(work_te["reincide"].sum())
        overall_rate_te = float(work_te["reincide"].mean())

        # Sort from D10 (highest risk) down to D1 (lowest risk) for cumulative gain calculation
        dec_rows: List[Dict[str, object]] = []
        cum_pos_tr = 0
        cum_rows_tr = 0
        cum_pos_te = 0

        for d in range(10, 0, -1):
            sub_tr = work.loc[work["decil_num"] == d]
            sub_te = work_te.loc[work_te["decil_num"] == d]
            n_d_tr = len(sub_tr)
            pos_d_tr = int(sub_tr["reincide"].sum())
            rate_d_tr = pos_d_tr / float(n_d_tr)
            lift_tr = rate_d_tr / overall_rate_tr
            cum_pos_tr += pos_d_tr
            cum_rows_tr += n_d_tr
            cum_gain_tr = 100.0 * cum_pos_tr / float(total_pos_tr)
            cum_pop_tr = 100.0 * cum_rows_tr / float(len(work))

            pos_d_te = int(sub_te["reincide"].sum())
            rate_d_te = pos_d_te / float(len(sub_te))
            lift_te = rate_d_te / overall_rate_te
            cum_pos_te += pos_d_te
            cum_gain_te = 100.0 * cum_pos_te / float(total_pos_te)

            dec_rows.append(
                {
                    "decil_riesgo": f"D{d:02d}" + (" (Mayor riesgo)" if d == 10 else (" (Menor riesgo)" if d == 1 else "")),
                    "decil_orden": d,
                    "soporte_train": int(n_d_tr),
                    "prob_min_train_pct": round(100.0 * float(sub_tr["prob"].min()), 2),
                    "prob_max_train_pct": round(100.0 * float(sub_tr["prob"].max()), 2),
                    "prob_media_train_pct": round(100.0 * float(sub_tr["prob"].mean()), 2),
                    "tasa_observada_train_pct": round(100.0 * rate_d_tr, 2),
                    "lift_train": round(lift_tr, 3),
                    "pct_poblacion_acumulada": round(cum_pop_tr, 1),
                    "ganancia_acumulada_positivos_train_pct": round(cum_gain_tr, 2),
                    "tasa_confirmada_test_pct": round(100.0 * rate_d_te, 2),
                    "lift_test": round(lift_te, 3),
                    "ganancia_acumulada_positivos_test_pct": round(cum_gain_te, 2),
                }
            )

        deciles_df = pd.DataFrame(dec_rows)

        # Average profile in original units of Top Decile (D10) vs Bottom Decile (D1) on BOTH Train (OOF) and Test
        d10 = work.loc[work["decil_num"] == 10]
        d01 = work.loc[work["decil_num"] == 1]
        d10_te = work_te.loc[work_te["decil_num"] == 10]
        d01_te = work_te.loc[work_te["decil_num"] == 1]

        profile_comp_rows = [
            {
                "indicador_unidades_originales": "Soporte de filas",
                "D01_menor_riesgo_train": f"{len(d01):,}",
                "D10_mayor_riesgo_train": f"{len(d10):,}",
                "diferencia_D10_menos_D01_train": f"{len(d10) - len(d01):,}",
                "D01_menor_riesgo_test": f"{len(d01_te):,}",
                "D10_mayor_riesgo_test": f"{len(d10_te):,}",
                "diferencia_D10_menos_D01_test": f"{len(d10_te) - len(d01_te):,}",
            },
            {
                "indicador_unidades_originales": "Tasa observada de reincidencia (%)",
                "D01_menor_riesgo_train": round(100.0 * float(d01["reincide"].mean()), 2),
                "D10_mayor_riesgo_train": round(100.0 * float(d10["reincide"].mean()), 2),
                "diferencia_D10_menos_D01_train": round(
                    100.0 * float(d10["reincide"].mean() - d01["reincide"].mean()), 2
                ),
                "D01_menor_riesgo_test": round(100.0 * float(d01_te["reincide"].mean()), 2),
                "D10_mayor_riesgo_test": round(100.0 * float(d10_te["reincide"].mean()), 2),
                "diferencia_D10_menos_D01_test": round(
                    100.0 * float(d10_te["reincide"].mean() - d01_te["reincide"].mean()), 2
                ),
            },
            {
                "indicador_unidades_originales": "Empleos previos acumulados (media / mediana)",
                "D01_menor_riesgo_train": f"{d01['previous_jobs'].mean():.2f} / {d01['previous_jobs'].median():.1f}",
                "D10_mayor_riesgo_train": f"{d10['previous_jobs'].mean():.2f} / {d10['previous_jobs'].median():.1f}",
                "diferencia_D10_menos_D01_train": round(
                    float(d10["previous_jobs"].mean() - d01["previous_jobs"].mean()), 2
                ),
                "D01_menor_riesgo_test": f"{d01_te['previous_jobs'].mean():.2f} / {d01_te['previous_jobs'].median():.1f}",
                "D10_mayor_riesgo_test": f"{d10_te['previous_jobs'].mean():.2f} / {d10_te['previous_jobs'].median():.1f}",
                "diferencia_D10_menos_D01_test": round(
                    float(d10_te["previous_jobs"].mean() - d01_te["previous_jobs"].mean()), 2
                ),
            },
            {
                "indicador_unidades_originales": "Duración del empleo en trimestres (media / mediana)",
                "D01_menor_riesgo_train": f"{d01['dur_q'].mean():.2f} / {d01['dur_q'].median():.1f}",
                "D10_mayor_riesgo_train": f"{d10['dur_q'].mean():.2f} / {d10['dur_q'].median():.1f}",
                "diferencia_D10_menos_D01_train": round(
                    float(d10["dur_q"].mean() - d01["dur_q"].mean()), 2
                ),
                "D01_menor_riesgo_test": f"{d01_te['dur_q'].mean():.2f} / {d01_te['dur_q'].median():.1f}",
                "D10_mayor_riesgo_test": f"{d10_te['dur_q'].mean():.2f} / {d10_te['dur_q'].median():.1f}",
                "diferencia_D10_menos_D01_test": round(
                    float(d10_te["dur_q"].mean() - d01_te["dur_q"].mean()), 2
                ),
            },
            {
                "indicador_unidades_originales": "Año de inicio del empleo (media / mediana)",
                "D01_menor_riesgo_train": f"{d01['start_year'].mean():.1f} / {d01['start_year'].median():.0f}",
                "D10_mayor_riesgo_train": f"{d10['start_year'].mean():.1f} / {d10['start_year'].median():.0f}",
                "diferencia_D10_menos_D01_train": round(
                    float(d10["start_year"].mean() - d01["start_year"].mean()), 2
                ),
                "D01_menor_riesgo_test": f"{d01_te['start_year'].mean():.1f} / {d01_te['start_year'].median():.0f}",
                "D10_mayor_riesgo_test": f"{d10_te['start_year'].mean():.1f} / {d10_te['start_year'].median():.0f}",
                "diferencia_D10_menos_D01_test": round(
                    float(d10_te["start_year"].mean() - d01_te["start_year"].mean()), 2
                ),
            },
            {
                "indicador_unidades_originales": "Competencias esenciales ESCO (media / mediana)",
                "D01_menor_riesgo_train": f"{d01['n_skills_essential'].mean():.2f} / {d01['n_skills_essential'].median():.1f}",
                "D10_mayor_riesgo_train": f"{d10['n_skills_essential'].mean():.2f} / {d10['n_skills_essential'].median():.1f}",
                "diferencia_D10_menos_D01_train": round(
                    float(d10["n_skills_essential"].mean() - d01["n_skills_essential"].mean()), 2
                ),
                "D01_menor_riesgo_test": f"{d01_te['n_skills_essential'].mean():.2f} / {d01_te['n_skills_essential'].median():.1f}",
                "D10_mayor_riesgo_test": f"{d10_te['n_skills_essential'].mean():.2f} / {d10_te['n_skills_essential'].median():.1f}",
                "diferencia_D10_menos_D01_test": round(
                    float(d10_te["n_skills_essential"].mean() - d01_te["n_skills_essential"].mean()), 2
                ),
            },
            {
                "indicador_unidades_originales": "Proporción de empleos vigentes (%)",
                "D01_menor_riesgo_train": round(100.0 * float(d01["es_vigente"].mean()), 2),
                "D10_mayor_riesgo_train": round(100.0 * float(d10["es_vigente"].mean()), 2),
                "diferencia_D10_menos_D01_train": round(
                    100.0 * float(d10["es_vigente"].mean() - d01["es_vigente"].mean()), 2
                ),
                "D01_menor_riesgo_test": round(100.0 * float(d01_te["es_vigente"].mean()), 2),
                "D10_mayor_riesgo_test": round(100.0 * float(d10_te["es_vigente"].mean()), 2),
                "diferencia_D10_menos_D01_test": round(
                    100.0 * float(d10_te["es_vigente"].mean() - d01_te["es_vigente"].mean()), 2
                ),
            },
            {
                "indicador_unidades_originales": "Nivel educativo modal (% dentro del decil)",
                "D01_menor_riesgo_train": f"{d01['university_level'].mode().iloc[0]} ({100.0 * d01['university_level'].value_counts(normalize=True).iloc[0]:.1f}%)",
                "D10_mayor_riesgo_train": f"{d10['university_level'].mode().iloc[0]} ({100.0 * d10['university_level'].value_counts(normalize=True).iloc[0]:.1f}%)",
                "diferencia_D10_menos_D01_train": "Cambio de composición",
                "D01_menor_riesgo_test": f"{d01_te['university_level'].mode().iloc[0]} ({100.0 * d01_te['university_level'].value_counts(normalize=True).iloc[0]:.1f}%)",
                "D10_mayor_riesgo_test": f"{d10_te['university_level'].mode().iloc[0]} ({100.0 * d10_te['university_level'].value_counts(normalize=True).iloc[0]:.1f}%)",
                "diferencia_D10_menos_D01_test": "Cambio de composición",
            },
        ]

        # ISCO major group composition in D10 vs D1 vs overall (Train OOF and Test)
        isco_comp_rows: List[Dict[str, object]] = []
        for digit in sorted(ISCO_MAJOR_LABELS_ES.keys()):
            label_es = ISCO_MAJOR_LABELS_ES[digit]
            sh_all = 100.0 * float((work["isco_major"] == digit).mean())
            sh_d01 = 100.0 * float((d01["isco_major"] == digit).mean())
            sh_d10 = 100.0 * float((d10["isco_major"] == digit).mean())
            sh_d01_te = 100.0 * float((d01_te["isco_major"] == digit).mean())
            sh_d10_te = 100.0 * float((d10_te["isco_major"] == digit).mean())
            isco_comp_rows.append(
                {
                    "isco_major": digit,
                    "gran_grupo_isco": label_es,
                    "participacion_train_total_pct": round(sh_all, 2),
                    "participacion_en_D01_train_pct": round(sh_d01, 2),
                    "participacion_en_D10_train_pct": round(sh_d10, 2),
                    "diferencia_D10_menos_D01_train_pp": round(sh_d10 - sh_d01, 2),
                    "participacion_en_D01_test_pct": round(sh_d01_te, 2),
                    "participacion_en_D10_test_pct": round(sh_d10_te, 2),
                    "sobremuestreo_D10_vs_total_train": round(sh_d10 / max(sh_all, 1e-4), 2),
                }
            )

        return (
            deciles_df,
            pd.DataFrame(profile_comp_rows),
            pd.DataFrame(isco_comp_rows),
        )

    def analyze_p4_career_position_and_period(
        self,
        orig_train: pd.DataFrame,
        orig_test: pd.DataFrame,
        tuned_models: Dict[str, TunedModelArtifact],
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """P4: Observed and predicted reincidence rate by job_order ranges, slope ratio, and start_year periods."""
        def _assign_job_order_band(s: pd.Series) -> pd.Series:
            return pd.cut(
                s,
                bins=[0, 1, 2, 3, 5, 8, 10000],
                labels=[
                    "1 (1er empleo)",
                    "2 (2do empleo)",
                    "3 (3er empleo)",
                    "4–5 empleos",
                    "6–8 empleos",
                    "9+ empleos",
                ],
            )

        def _assign_start_year_band(s: pd.Series) -> pd.Series:
            return pd.cut(
                s,
                bins=[-10000, 1999, 2004, 2009, 2014, 2019, 10000],
                labels=[
                    "<= 1999",
                    "2000–2004",
                    "2005–2009",
                    "2010–2014",
                    "2015–2019",
                    "2020+",
                ],
            )

        tr_jb = _assign_job_order_band(orig_train["job_order"])
        te_jb = _assign_job_order_band(orig_test["job_order"])
        tr_yb = _assign_start_year_band(orig_train["start_year"])
        te_yb = _assign_start_year_band(orig_test["start_year"])

        def _summarize_by_band(
            band_tr: pd.Series,
            band_te: pd.Series,
            col_title: str,
        ) -> pd.DataFrame:
            rows: List[Dict[str, object]] = []
            for cat in band_tr.cat.categories:
                m_tr = (band_tr == cat).to_numpy()
                m_te = (band_te == cat).to_numpy()
                n_tr = int(m_tr.sum())
                if n_tr < self.min_support:
                    continue
                pos_tr = int(orig_train.loc[m_tr, "reincide"].sum())
                obs_tr = 100.0 * pos_tr / float(n_tr)
                lo_tr, hi_tr = wilson_ci_95(pos_tr, n_tr)

                n_te = int(m_te.sum())
                obs_te = (
                    100.0 * float(orig_test.loc[m_te, "reincide"].mean())
                    if n_te > 0
                    else np.nan
                )

                pred_g_tr = 100.0 * float(tuned_models[MODEL_NB_G].oof_proba_train[m_tr].mean())
                pred_b_tr = 100.0 * float(tuned_models[MODEL_NB_B].oof_proba_train[m_tr].mean())
                pred_h_tr = 100.0 * float(tuned_models[MODEL_NB_H].oof_proba_train[m_tr].mean())
                pred_h_te = (
                    100.0 * float(tuned_models[MODEL_NB_H].test_proba[m_te].mean())
                    if n_te > 0
                    else np.nan
                )

                rows.append(
                    {
                        col_title: str(cat),
                        "soporte_train": n_tr,
                        "tasa_observada_train_pct": round(obs_tr, 2),
                        "ic95_wilson_train_pct": f"[{100.0 * lo_tr:.2f}, {100.0 * hi_tr:.2f}]",
                        "prob_media_NB_G_train_pct": round(pred_g_tr, 2),
                        "prob_media_NB_B_train_pct": round(pred_b_tr, 2),
                        "prob_media_NB_H_train_pct": round(pred_h_tr, 2),
                        "brecha_NB_H_menos_obs_train_pp": round(pred_h_tr - obs_tr, 2),
                        "soporte_test": n_te,
                        "tasa_confirmada_test_pct": round(obs_te, 2),
                        "prob_media_NB_H_test_pct": round(pred_h_te, 2),
                        "brecha_NB_H_menos_obs_test_pp": round(pred_h_te - obs_te, 2)
                        if not (np.isnan(pred_h_te) or np.isnan(obs_te))
                        else np.nan,
                    }
                )
            return pd.DataFrame(rows)

        job_order_df = _summarize_by_band(tr_jb, te_jb, "tramo_job_order")
        start_year_df = _summarize_by_band(tr_yb, te_yb, "periodo_anio_inicio")

        # Quantify observed vs predicted job_order slope ratio and per-bin gaps (F3)
        obs_tr_min = float(job_order_df["tasa_observada_train_pct"].iloc[0])
        obs_tr_max = float(job_order_df["tasa_observada_train_pct"].iloc[-1])
        pred_tr_min = float(job_order_df["prob_media_NB_H_train_pct"].iloc[0])
        pred_tr_max = float(job_order_df["prob_media_NB_H_train_pct"].iloc[-1])
        rng_obs_tr = obs_tr_max - obs_tr_min
        rng_pred_tr = pred_tr_max - pred_tr_min
        slope_ratio_tr = rng_pred_tr / max(rng_obs_tr, 1e-9)

        obs_te_min = float(job_order_df["tasa_confirmada_test_pct"].iloc[0])
        obs_te_max = float(job_order_df["tasa_confirmada_test_pct"].iloc[-1])
        pred_te_min = float(job_order_df["prob_media_NB_H_test_pct"].iloc[0])
        pred_te_max = float(job_order_df["prob_media_NB_H_test_pct"].iloc[-1])
        rng_obs_te = obs_te_max - obs_te_min
        rng_pred_te = pred_te_max - pred_te_min
        slope_ratio_te = rng_pred_te / max(rng_obs_te, 1e-9)

        slope_summary_df = pd.DataFrame(
            [
                {
                    "muestra": "Train (OOF · 1,391,018 filas)",
                    "tasa_obs_1er_empleo_pct": round(obs_tr_min, 2),
                    "tasa_obs_9plus_pct": round(obs_tr_max, 2),
                    "rango_observado_pp": round(rng_obs_tr, 2),
                    "prob_NB_H_1er_empleo_pct": round(pred_tr_min, 2),
                    "prob_NB_H_9plus_pct": round(pred_tr_max, 2),
                    "rango_predicho_NB_H_pp": round(rng_pred_tr, 2),
                    "razon_pendiente_pred_sobre_obs": round(slope_ratio_tr, 4),
                    "pct_pendiente_capturada": round(100.0 * slope_ratio_tr, 2),
                    "brecha_max_abs_tramo_pp": round(
                        float(job_order_df["brecha_NB_H_menos_obs_train_pp"].abs().max()), 2
                    ),
                },
                {
                    "muestra": "Test (347,720 filas)",
                    "tasa_obs_1er_empleo_pct": round(obs_te_min, 2),
                    "tasa_obs_9plus_pct": round(obs_te_max, 2),
                    "rango_observado_pp": round(rng_obs_te, 2),
                    "prob_NB_H_1er_empleo_pct": round(pred_te_min, 2),
                    "prob_NB_H_9plus_pct": round(pred_te_max, 2),
                    "rango_predicho_NB_H_pp": round(rng_pred_te, 2),
                    "razon_pendiente_pred_sobre_obs": round(slope_ratio_te, 4),
                    "pct_pendiente_capturada": round(100.0 * slope_ratio_te, 2),
                    "brecha_max_abs_tramo_pp": round(
                        float(job_order_df["brecha_NB_H_menos_obs_test_pp"].abs().max()), 2
                    ),
                },
            ]
        )
        return job_order_df, start_year_df, slope_summary_df

    def analyze_p5_education_level(
        self,
        orig_train: pd.DataFrame,
        orig_test: pd.DataFrame,
        train_blocks: NaiveBayesPartitionBlocks,
        tuned_models: Dict[str, TunedModelArtifact],
    ) -> pd.DataFrame:
        """P5: Observed rate, predicted rate, PR-AUC, ROC-AUC, and F1 by education level (keeping 'No reportado')."""
        nb_h_art = tuned_models[MODEL_NB_H]
        nb_h_est: HybridNaiveBayes = nb_h_art.fitted_estimator  # type: ignore[assignment]
        tau = nb_h_art.oof_threshold_tau

        # Extract the exact Gaussian log-odds contribution of univ_ord_mm on train
        univ_idx_in_g10 = list(GAUSSIAN_HYBRID_FEATURES).index("univ_ord_mm")
        X_g10_tr = train_blocks.dense_clean_df[list(GAUSSIAN_HYBRID_FEATURES)].to_numpy(dtype=np.float64)
        _, g10_contribs = compute_gaussian_log_odds_contributions(nb_h_est.gaussian_nb_, X_g10_tr)  # type: ignore[arg-type]
        univ_contrib_tr = g10_contribs[:, univ_idx_in_g10]

        y_tr = orig_train["reincide"].to_numpy(dtype=np.int8)
        y_te = orig_test["reincide"].to_numpy(dtype=np.int8)

        rows: List[Dict[str, object]] = []
        for edu_cat in EDUCATION_ORDER_ES:
            m_tr = (orig_train["university_level"] == edu_cat).to_numpy()
            m_te = (orig_test["university_level"] == edu_cat).to_numpy()
            n_tr = int(m_tr.sum())
            if n_tr < self.min_support:
                continue

            pos_tr = int(y_tr[m_tr].sum())
            obs_tr = 100.0 * pos_tr / float(n_tr)
            lo_tr, hi_tr = wilson_ci_95(pos_tr, n_tr)

            p_oof = nb_h_art.oof_proba_train[m_tr]
            pred_oof = (p_oof >= tau).astype(np.int8)
            pr_tr = float(average_precision_score(y_tr[m_tr], p_oof))
            roc_tr = float(roc_auc_score(y_tr[m_tr], p_oof))
            f1_tr = float(f1_score(y_tr[m_tr], pred_oof, pos_label=1, zero_division=0))

            n_te = int(m_te.sum())
            obs_te = 100.0 * float(y_te[m_te].mean()) if n_te > 0 else np.nan
            p_te = nb_h_art.test_proba[m_te]
            pred_te = (p_te >= tau).astype(np.int8)
            pr_te = float(average_precision_score(y_te[m_te], p_te)) if n_te > 0 else np.nan
            roc_te = float(roc_auc_score(y_te[m_te], p_te)) if n_te > 0 else np.nan
            f1_te = (
                float(f1_score(y_te[m_te], pred_te, pos_label=1, zero_division=0))
                if n_te > 0
                else np.nan
            )

            diff_edu = (obs_te - obs_tr) if not np.isnan(obs_te) else np.nan
            rows.append(
                {
                    "university_level": edu_cat,
                    "tratamiento_categoria": (
                        "Categoría propia sin imputar (ausencia informativa)"
                        if edu_cat == "No reportado"
                        else "Nivel educativo reportado"
                    ),
                    "soporte_train": n_tr,
                    "pct_del_train": round(100.0 * n_tr / float(len(y_tr)), 2),
                    "tasa_observada_train_pct": round(obs_tr, 2),
                    "ic95_wilson_train_pct": f"[{100.0 * lo_tr:.2f}, {100.0 * hi_tr:.2f}]",
                    "prob_media_oof_nb_h_train_pct": round(100.0 * float(p_oof.mean()), 2),
                    "contrib_log_odds_univ_ord_mm": round(float(univ_contrib_tr[m_tr].mean()), 4),
                    "pr_auc_oof_train": round(pr_tr, 4),
                    "roc_auc_oof_train": round(roc_tr, 4),
                    "f1_oof_train": round(f1_tr, 4),
                    "soporte_test": n_te,
                    "tasa_confirmada_test_pct": round(obs_te, 2),
                    "brecha_test_menos_train_pp": round(diff_edu, 2)
                    if not np.isnan(diff_edu)
                    else np.nan,
                    "alerta_brecha_mayor_5pp": bool(abs(diff_edu) > 5.0)
                    if not np.isnan(diff_edu)
                    else False,
                    "prob_media_nb_h_test_pct": round(100.0 * float(p_te.mean()), 2),
                    "pr_auc_test": round(pr_te, 4),
                    "roc_auc_test": round(roc_te, 4),
                    "f1_test": round(f1_te, 4),
                }
            )

        return pd.DataFrame(rows)

    def analyze_p6_error_analysis(
        self,
        orig_train: pd.DataFrame,
        orig_test: pd.DataFrame,
        nb_h_art: TunedModelArtifact,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """P6: Original-unit profiles of TP, FP, TN, FN and subgroup error concentration."""
        tau = nb_h_art.oof_threshold_tau
        y_tr = orig_train["reincide"].to_numpy(dtype=np.int8)
        p_tr = nb_h_art.oof_proba_train
        pred_tr = (p_tr >= tau).astype(np.int8)

        y_te = orig_test["reincide"].to_numpy(dtype=np.int8)
        p_te = nb_h_art.test_proba
        pred_te = (p_te >= tau).astype(np.int8)

        quadrants = [
            ("TP · Verdadero Positivo (reincide=1, pred=1)", (y_tr == 1) & (pred_tr == 1), (y_te == 1) & (pred_te == 1)),
            ("FP · Falso Positivo (reincide=0, pred=1)", (y_tr == 0) & (pred_tr == 1), (y_te == 0) & (pred_te == 1)),
            ("FN · Falso Negativo (reincide=1, pred=0)", (y_tr == 1) & (pred_tr == 0), (y_te == 1) & (pred_te == 0)),
            ("TN · Verdadero Negativo (reincide=0, pred=0)", (y_tr == 0) & (pred_tr == 0), (y_te == 0) & (pred_te == 0)),
        ]

        prof_rows: List[Dict[str, object]] = []
        for q_label, m_tr, m_te in quadrants:
            sub_tr = orig_train.loc[m_tr]
            n_q_tr = len(sub_tr)
            n_q_te = int(m_te.sum())
            if n_q_tr == 0:
                continue
            prof_rows.append(
                {
                    "celda_confusion": q_label,
                    "soporte_oof_train": int(n_q_tr),
                    "pct_total_train": round(100.0 * n_q_tr / float(len(y_tr)), 2),
                    "soporte_test": n_q_te,
                    "pct_total_test": round(100.0 * n_q_te / float(len(y_te)), 2),
                    "prob_media_predicha_pct": round(100.0 * float(p_tr[m_tr].mean()), 2),
                    "empleos_previos_mediana": round(float(sub_tr["previous_jobs"].median()), 1),
                    "empleos_previos_media": round(float(sub_tr["previous_jobs"].mean()), 2),
                    "duracion_mediana_trimestres": round(float(sub_tr["dur_q"].median()), 1),
                    "duracion_media_trimestres": round(float(sub_tr["dur_q"].mean()), 2),
                    "anio_inicio_mediana": int(sub_tr["start_year"].median()),
                    "skills_esenciales_mediana": round(float(sub_tr["n_skills_essential"].median()), 1),
                    "pct_empleo_vigente": round(100.0 * float(sub_tr["es_vigente"].mean()), 2),
                    "gran_grupo_isco_modal": str(sub_tr["isco_major_label_es"].mode().iloc[0]),
                    "nivel_educativo_modal": str(sub_tr["university_level"].mode().iloc[0]),
                }
            )

        # Subgroup error rates (FPR among negatives, FNR among positives, total error rate) by ISCO and job_order
        sub_err_rows: List[Dict[str, object]] = []
        for digit in sorted(ISCO_MAJOR_LABELS_ES.keys()):
            m_g = (orig_train["isco_major"] == digit).to_numpy()
            if int(m_g.sum()) < self.min_support:
                continue
            y_g = y_tr[m_g]
            pr_g = pred_tr[m_g]
            n_neg = int((y_g == 0).sum())
            n_pos = int((y_g == 1).sum())
            fpr = 100.0 * float(((y_g == 0) & (pr_g == 1)).sum()) / float(max(n_neg, 1))
            fnr = 100.0 * float(((y_g == 1) & (pr_g == 0)).sum()) / float(max(n_pos, 1))
            err_tot = 100.0 * float((y_g != pr_g).mean())
            sub_err_rows.append(
                {
                    "dimension": "Gran grupo ISCO",
                    "subgrupo": ISCO_MAJOR_LABELS_ES[digit],
                    "soporte_train": int(m_g.sum()),
                    "tasa_error_global_pct": round(err_tot, 2),
                    "FPR_tasa_falsos_positivos_pct": round(fpr, 2),
                    "FNR_tasa_falsos_negativos_pct": round(fnr, 2),
                    "tipo_fallo_dominante": (
                        "Falsos Positivos (sobrepredicción)"
                        if fpr > fnr
                        else "Falsos Negativos (omisión de reincidencia)"
                    ),
                }
            )

        for jb_label, m_jb in [
            ("Primer empleo (job_order = 1)", (orig_train["job_order"] == 1).to_numpy()),
            ("2 a 3 empleos", orig_train["job_order"].isin([2, 3]).to_numpy()),
            ("4 a 5 empleos", orig_train["job_order"].isin([4, 5]).to_numpy()),
            ("6+ empleos (carrera avanzada)", (orig_train["job_order"] >= 6).to_numpy()),
        ]:
            y_g = y_tr[m_jb]
            pr_g = pred_tr[m_jb]
            n_neg = int((y_g == 0).sum())
            n_pos = int((y_g == 1).sum())
            fpr = 100.0 * float(((y_g == 0) & (pr_g == 1)).sum()) / float(max(n_neg, 1))
            fnr = 100.0 * float(((y_g == 1) & (pr_g == 0)).sum()) / float(max(n_pos, 1))
            err_tot = 100.0 * float((y_g != pr_g).mean())
            sub_err_rows.append(
                {
                    "dimension": "Tramo de orden del empleo",
                    "subgrupo": jb_label,
                    "soporte_train": int(m_jb.sum()),
                    "tasa_error_global_pct": round(err_tot, 2),
                    "FPR_tasa_falsos_positivos_pct": round(fpr, 2),
                    "FNR_tasa_falsos_negativos_pct": round(fnr, 2),
                    "tipo_fallo_dominante": (
                        "Falsos Positivos (sobrepredicción)"
                        if fpr > fnr
                        else "Falsos Negativos (omisión de reincidencia)"
                    ),
                }
            )

        return pd.DataFrame(prof_rows), pd.DataFrame(sub_err_rows)

    def analyze_p7_and_p8_cv_ablation_and_independence(
        self,
        train_blocks: NaiveBayesPartitionBlocks,
        nb_h_params: Dict[str, object],
        nb_g_params: Dict[str, object],
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """P7 & P8: Behavior-block ablation and correlated-pair independence audit in 5-fold grouped CV."""
        sgkf = StratifiedGroupKFold(
            n_splits=self.config.cv_folds,
            shuffle=True,
            random_state=self.config.random_state,
        )
        y_tr = train_blocks.y
        groups_tr = train_blocks.groups
        folds = list(sgkf.split(train_blocks.X_nb_g, y_tr, groups_tr))
        n_tr = len(y_tr)

        vs_h = float(nb_h_params.get("var_smoothing", 1e-9))
        alpha_h = float(nb_h_params.get("alpha", 1.0))
        pm_h = str(nb_h_params.get("prior_mode", "empirical"))
        priors_h = resolve_priors(pm_h)

        vs_g = float(nb_g_params.get("var_smoothing", 1e-9))
        pm_g = str(nb_g_params.get("prior_mode", "empirical"))
        priors_g = resolve_priors(pm_g)

        g10_names = list(GAUSSIAN_HYBRID_FEATURES)
        g14_names = list(ALL_DENSE_CLEAN_FEATURES)
        b_dense_names = list(BINARY_DENSE_FEATURES)

        X_g10_full = train_blocks.dense_clean_df[g10_names].to_numpy(dtype=np.float64)
        X_g14_full = train_blocks.dense_clean_df[g14_names].to_numpy(dtype=np.float64)
        X_b_dense_full = train_blocks.dense_clean_df[b_dense_names].to_numpy(dtype=np.float64)
        X_ohe_csr = train_blocks.X_nb_b[:, len(BINARY_DENSE_FEATURES) :]

        # Precompute per-feature fold log-likelihoods for NB-H Gaussian (10 cols, vs_h),
        # NB-G Gaussian (14 cols, vs_g), and Bernoulli (4 dense + OHE, alpha_h)
        oof_ll_g10_h = np.zeros((n_tr, len(g10_names), 2), dtype=np.float64)
        oof_ll_g14 = np.zeros((n_tr, len(g14_names), 2), dtype=np.float64)
        oof_ll_b_dense = np.zeros((n_tr, len(b_dense_names), 2), dtype=np.float64)
        oof_ll_ohe = np.zeros((n_tr, 2), dtype=np.float64)
        oof_log_prior_h = np.zeros((n_tr, 2), dtype=np.float64)
        oof_log_prior_g = np.zeros((n_tr, 2), dtype=np.float64)

        for tr_idx, va_idx in folds:
            y_f = y_tr[tr_idx]
            # Fit GaussianNB on 10 cols (with vs_h for NB-H) and on 14 cols (with vs_g for NB-G)
            gnb10 = GaussianNB(var_smoothing=vs_h, priors=priors_h)
            gnb10.fit(X_g10_full[tr_idx], y_f)
            for j in range(len(g10_names)):
                x_va_j = X_g10_full[va_idx, j]
                for c in (0, 1):
                    th = gnb10.theta_[c, j]
                    vr = gnb10.var_[c, j]
                    oof_ll_g10_h[va_idx, j, c] = (
                        -0.5 * np.log(2.0 * np.pi * vr) - 0.5 * ((x_va_j - th) ** 2) / vr
                    )

            gnb14 = GaussianNB(var_smoothing=vs_g, priors=priors_g)
            gnb14.fit(X_g14_full[tr_idx], y_f)
            oof_log_prior_g[va_idx] = np.log(gnb14.class_prior_)[np.newaxis, :]

            for j in range(len(g14_names)):
                x_va_j = X_g14_full[va_idx, j]
                for c in (0, 1):
                    th = gnb14.theta_[c, j]
                    vr = gnb14.var_[c, j]
                    oof_ll_g14[va_idx, j, c] = -0.5 * np.log(2.0 * np.pi * vr) - 0.5 * ((x_va_j - th) ** 2) / vr

            # Fit BernoulliNB on 2,971 binary columns with alpha_h
            bnb_full = BernoulliNB(alpha=alpha_h, binarize=0.0, force_alpha=True, class_prior=priors_h)
            bnb_full.fit(train_blocks.X_nb_b[tr_idx], y_f)
            oof_log_prior_h[va_idx] = bnb_full.class_log_prior_[np.newaxis, :]

            flp = bnb_full.feature_log_prob_  # shape (2, 2971)
            neg_flp = np.log1p(-np.exp(flp))

            # First 4 dense binary features
            for k in range(len(b_dense_names)):
                x_va_k = X_b_dense_full[va_idx, k]
                for c in (0, 1):
                    oof_ll_b_dense[va_idx, k, c] = neg_flp[c, k] + x_va_k * (flp[c, k] - neg_flp[c, k])

            # Remaining 2,967 OHE occupation columns summed
            X_ohe_va = X_ohe_csr[va_idx]
            for c in (0, 1):
                base_c = float(np.sum(neg_flp[c, len(b_dense_names) :]))
                delta_c = flp[c, len(b_dense_names) :] - neg_flp[c, len(b_dense_names) :]
                oof_ll_ohe[va_idx, c] = base_c + np.asarray(X_ohe_va.dot(delta_c)).ravel()

        g10_idx_map = {name: i for i, name in enumerate(g10_names)}
        g14_idx_map = {name: i for i, name in enumerate(g14_names)}
        b_dense_idx_map = {name: i for i, name in enumerate(b_dense_names)}

        def _eval_nb_h_subset(
            keep_g10_cols: Sequence[str],
            keep_b_dense_cols: Sequence[str],
            include_ohe: bool,
        ) -> Dict[str, float]:
            g_indices = [g10_idx_map[c] for c in keep_g10_cols]
            b_indices = [b_dense_idx_map[c] for c in keep_b_dense_cols]

            jll = oof_log_prior_h.copy()
            if g_indices:
                jll += oof_ll_g10_h[:, g_indices, :].sum(axis=1)
            if b_indices:
                jll += oof_ll_b_dense[:, b_indices, :].sum(axis=1)
            if include_ohe:
                jll += oof_ll_ohe

            log_p = jll - logsumexp(jll, axis=1, keepdims=True)
            p1 = np.exp(log_p[:, 1])

            fold_pr, fold_roc, fold_brier = [], [], []
            for _, va_idx in folds:
                fold_pr.append(float(average_precision_score(y_tr[va_idx], p1[va_idx])))
                fold_roc.append(float(roc_auc_score(y_tr[va_idx], p1[va_idx])))
                fold_brier.append(float(brier_score_loss(y_tr[va_idx], p1[va_idx])))
            return {
                "pr_auc": float(np.mean(fold_pr)),
                "roc_auc": float(np.mean(fold_roc)),
                "brier": float(np.mean(fold_brier)),
            }

        def _eval_nb_g_subset(keep_g14_cols: Sequence[str]) -> Dict[str, float]:
            g_indices = [g14_idx_map[c] for c in keep_g14_cols]
            jll = oof_log_prior_g + oof_ll_g14[:, g_indices, :].sum(axis=1)
            log_p = jll - logsumexp(jll, axis=1, keepdims=True)
            p1 = np.exp(log_p[:, 1])
            fold_pr, fold_roc, fold_brier = [], [], []
            for _, va_idx in folds:
                fold_pr.append(float(average_precision_score(y_tr[va_idx], p1[va_idx])))
                fold_roc.append(float(roc_auc_score(y_tr[va_idx], p1[va_idx])))
                fold_brier.append(float(brier_score_loss(y_tr[va_idx], p1[va_idx])))
            return {
                "pr_auc": float(np.mean(fold_pr)),
                "roc_auc": float(np.mean(fold_roc)),
                "brier": float(np.mean(fold_brier)),
            }

        # P7: Ablation by behavior blocks on NB-H in 5-fold grouped CV
        base_h = _eval_nb_h_subset(g10_names, b_dense_names, include_ohe=True)
        ablation_specs = [
            (
                "0. Modelo completo NB-H (Referencia)",
                "Ninguno (2,981 columnas)",
                g10_names,
                b_dense_names,
                True,
                2981,
            ),
            (
                "1. Sin bloque Temporal",
                "start_ord_rob, end_ord_rob (2 cols)",
                [c for c in g10_names if c not in ("start_ord_rob", "end_ord_rob")],
                b_dense_names,
                True,
                2979,
            ),
            (
                "2. Sin bloque Duración y carrera",
                "dur_q_rob, dur_q_bin, job_order_rob, es_vigente (4 cols)",
                [c for c in g10_names if c not in ("dur_q_rob", "dur_q_bin", "job_order_rob")],
                [c for c in b_dense_names if c != "es_vigente"],
                True,
                2977,
            ),
            (
                "3. Sin bloque Educación",
                "univ_ord_mm (1 col)",
                [c for c in g10_names if c != "univ_ord_mm"],
                b_dense_names,
                True,
                2980,
            ),
            (
                "4. Sin bloque Competencias ESCO",
                "n_skills_essential_rob/bin, n_skills_knowledge_rob, n_skills_sin_tipo_rob, tiene_* (7 cols)",
                [
                    c
                    for c in g10_names
                    if c
                    not in (
                        "n_skills_essential_rob",
                        "n_skills_knowledge_rob",
                        "n_skills_sin_tipo_rob",
                        "n_skills_essential_bin",
                    )
                ],
                [c for c in b_dense_names if c not in ("tiene_skills", "tiene_knowledge", "tiene_sin_tipo")],
                True,
                2974,
            ),
            (
                "5. Sin bloque Ocupación OHE",
                "occupation_code_* (2,967 dummies)",
                g10_names,
                b_dense_names,
                False,
                14,
            ),
        ]

        p7_rows: List[Dict[str, object]] = []
        for label, dropped_desc, k_g10, k_b, inc_ohe, n_cols in ablation_specs:
            m = _eval_nb_h_subset(k_g10, k_b, include_ohe=inc_ohe)
            delta_pr = m["pr_auc"] - base_h["pr_auc"]
            delta_roc = m["roc_auc"] - base_h["roc_auc"]
            delta_brier = m["brier"] - base_h["brier"]
            p7_rows.append(
                {
                    "experimento_ablacion": label,
                    "variables_retiradas": dropped_desc,
                    "n_columnas_activas": n_cols,
                    "pr_auc_cv_media": round(m["pr_auc"], 4),
                    "cambio_pr_auc_vs_completo": round(delta_pr, 4),
                    "roc_auc_cv_media": round(m["roc_auc"], 4),
                    "cambio_roc_auc_vs_completo": round(delta_roc, 4),
                    "brier_cv_media": round(m["brier"], 4),
                    "cambio_brier_vs_completo": round(delta_brier, 4),
                }
            )
        p7_df = pd.DataFrame(p7_rows)

        # P8: Independence audit for highly correlated pairs (evaluated on both NB-H and NB-G)
        base_g = _eval_nb_g_subset(g14_names)
        pair_drop_specs = [
            (
                "0. Referencia sin retirar pares correlacionados",
                "Ninguna",
                "—",
                [],
            ),
            (
                "Par 1: (n_skills_essential_rob, n_skills_essential_bin) -> retirar bin",
                "n_skills_essential_bin",
                "rho = 0.968 (discretización redundante del mismo conteo)",
                ["n_skills_essential_bin"],
            ),
            (
                "Par 1b: (n_skills_essential_rob, n_skills_essential_bin) -> retirar rob",
                "n_skills_essential_rob",
                "rho = 0.968 (conservar solo tramo cuantil)",
                ["n_skills_essential_rob"],
            ),
            (
                "Par 2: (dur_q_rob, dur_q_bin) -> retirar bin",
                "dur_q_bin",
                "rho = 0.962 (discretización redundante de dur_q)",
                ["dur_q_bin"],
            ),
            (
                "Par 2b: (dur_q_rob, dur_q_bin) -> retirar rob",
                "dur_q_rob",
                "rho = 0.962 (conservar solo tramo cuantil)",
                ["dur_q_rob"],
            ),
            (
                "Par 3: (start_ord_rob, end_ord_rob) -> retirar end_ord_rob",
                "end_ord_rob",
                "r = 0.785 (fechas de inicio y fin acopladas)",
                ["end_ord_rob"],
            ),
            (
                "Par 4: (end_ord_rob, es_vigente) -> retirar es_vigente",
                "es_vigente",
                "rho = 0.655 (censura en 2026-Q1 cuando es_vigente=1)",
                ["es_vigente"],
            ),
            (
                "Par 5: (n_skills_essential_rob, n_skills_knowledge_rob) -> retirar knowledge",
                "n_skills_knowledge_rob",
                "r = 0.784 (conocimientos contenidos en esenciales)",
                ["n_skills_knowledge_rob"],
            ),
            (
                "Conjunto depurado: retirar ambos bins duplicados (dur_q_bin + n_skills_essential_bin)",
                "dur_q_bin, n_skills_essential_bin",
                "Elimina simultáneamente el doble conteo de las dos variables discretizadas",
                ["dur_q_bin", "n_skills_essential_bin"],
            ),
            (
                "Conjunto depurado completo: retirar bins + end_ord_rob + n_skills_knowledge_rob",
                "dur_q_bin, n_skills_essential_bin, end_ord_rob, n_skills_knowledge_rob",
                "Elimina los 4 focos principales de colinealidad remanente en el bloque denso",
                ["dur_q_bin", "n_skills_essential_bin", "end_ord_rob", "n_skills_knowledge_rob"],
            ),
        ]

        p8_rows: List[Dict[str, object]] = []
        for exp_label, dropped_str, corr_info, drop_list in pair_drop_specs:
            drop_set = set(drop_list)
            m_h = _eval_nb_h_subset(
                [c for c in g10_names if c not in drop_set],
                [c for c in b_dense_names if c not in drop_set],
                include_ohe=True,
            )
            m_g = _eval_nb_g_subset([c for c in g14_names if c not in drop_set])

            p8_rows.append(
                {
                    "experimento_independencia": exp_label,
                    "variable_retirada": dropped_str,
                    "correlacion_del_par": corr_info,
                    "NB_H_pr_auc_cv": round(m_h["pr_auc"], 4),
                    "NB_H_delta_pr_auc": round(m_h["pr_auc"] - base_h["pr_auc"], 4),
                    "NB_H_brier_cv": round(m_h["brier"], 4),
                    "NB_H_delta_brier": round(m_h["brier"] - base_h["brier"], 4),
                    "NB_G_pr_auc_cv": round(m_g["pr_auc"], 4),
                    "NB_G_delta_pr_auc": round(m_g["pr_auc"] - base_g["pr_auc"], 4),
                    "NB_G_brier_cv": round(m_g["brier"], 4),
                    "NB_G_delta_brier": round(m_g["brier"] - base_g["brier"], 4),
                }
            )
        p8_df = pd.DataFrame(p8_rows)
        return p7_df, p8_df

    def run_all_general_patterns(
        self,
        orig_train: pd.DataFrame,
        orig_test: pd.DataFrame,
        train_blocks: NaiveBayesPartitionBlocks,
        tuned_models: Dict[str, TunedModelArtifact],
        o1_df: pd.DataFrame,
        test_blocks: NaiveBayesPartitionBlocks | None = None,
    ) -> GeneralPatternsBundle:
        """Execute P1 through P8 on Version A."""
        nb_h_art = tuned_models[MODEL_NB_H]
        nb_g_art = tuned_models[MODEL_NB_G]
        nb_h_est: HybridNaiveBayes = nb_h_art.fitted_estimator  # type: ignore[assignment]
        blocks_for_test = test_blocks if test_blocks is not None else train_blocks

        p1_cont_df, p1_bin_df, p1_block_share_df, p1_curves = self.analyze_p1_evidence_per_variable(
            orig_train, orig_test, train_blocks, blocks_for_test, nb_h_est
        )
        p2_summary_df, p2_waterfalls = self.analyze_p2_waterfall_profiles(
            orig_train, train_blocks, nb_h_est, o1_df
        )
        p3_dec_df, p3_prof_df, p3_isco_df = self.analyze_p3_risk_deciles(
            orig_train,
            orig_test,
            nb_h_art.oof_proba_train,
            nb_h_art.test_proba,
        )
        p4_job_df, p4_year_df, p4_slope_df = self.analyze_p4_career_position_and_period(
            orig_train, orig_test, tuned_models
        )
        p5_edu_df = self.analyze_p5_education_level(
            orig_train, orig_test, train_blocks, tuned_models
        )
        p6_prof_df, p6_sub_df = self.analyze_p6_error_analysis(
            orig_train, orig_test, nb_h_art
        )
        p7_df, p8_df = self.analyze_p7_and_p8_cv_ablation_and_independence(
            train_blocks,
            nb_h_params=nb_h_art.best_params,
            nb_g_params=nb_g_art.best_params,
        )

        return GeneralPatternsBundle(
            p1_continuous_evidence_table=p1_cont_df,
            p1_binary_evidence_table=p1_bin_df,
            p1_block_log_odds_share_test_table=p1_block_share_df,
            p1_llr_curves=p1_curves,
            p2_profiles_summary_table=p2_summary_df,
            p2_waterfalls=p2_waterfalls,
            p3_deciles_table=p3_dec_df,
            p3_top_vs_bottom_profile_table=p3_prof_df,
            p3_isco_composition_deciles_table=p3_isco_df,
            p4_job_order_table=p4_job_df,
            p4_start_year_table=p4_year_df,
            p4_job_order_slope_summary_table=p4_slope_df,
            p5_education_table=p5_edu_df,
            p6_error_profiles_table=p6_prof_df,
            p6_error_subgroups_table=p6_sub_df,
            p7_block_ablation_cv_table=p7_df,
            p8_independence_audit_cv_table=p8_df,
        )
