"""Occupational-group analyses O1 to O6 in original units for Notebook 7.1 (Naive Bayes)."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from .config import (
    BINARY_DENSE_FEATURES,
    GAUSSIAN_HYBRID_FEATURES,
    ISCO_MAJOR_LABELS_ES,
    MODEL_LABELS_ES,
    MODEL_NB_B,
    MODEL_NB_G,
    MODEL_NB_H,
    MODEL_ORDER,
    NaiveBayesConfig,
)
from .evaluation import TunedModelArtifact
from .feature_blocks import NaiveBayesPartitionBlocks
from .models import HybridNaiveBayes


def wilson_ci_95(positives: int, total: int, z: float = 1.959963984540054) -> Tuple[float, float]:
    """Compute 95% Wilson confidence interval for a binomial proportion."""
    if total <= 0:
        return 0.0, 0.0
    p = float(positives) / float(total)
    z2 = z * z
    denom = 1.0 + z2 / float(total)
    center = (p + z2 / (2.0 * float(total))) / denom
    margin = (
        z
        * math.sqrt((p * (1.0 - p) / float(total)) + (z2 / (4.0 * float(total) * float(total))))
        / denom
    )
    return max(0.0, center - margin), min(1.0, center + margin)


@dataclass(frozen=True)
class OccupationAnalysisBundle:
    """Complete tables and matrices for Block 1 (O1 to O6 occupational group analyses)."""

    o1_rates_table: pd.DataFrame
    o2_performance_by_isco_table: pd.DataFrame
    o3_log_odds_heatmap_df: pd.DataFrame
    o3_original_units_diff_table: pd.DataFrame
    o4_profile_by_group_table: pd.DataFrame
    o5_subgroups_2d_table: pd.DataFrame
    o5_occupations_4d_table: pd.DataFrame
    o6_transitions_persistence_table: pd.DataFrame
    o6_correlations_summary: Dict[str, float]


class OccupationPatternAnalyzer:
    """Execute analyses O1 through O6 in original units on Version A with minimum support guards."""

    def __init__(self, config: NaiveBayesConfig) -> None:
        self.config = config
        self.min_support = int(config.min_subgroup_support)

    @staticmethod
    def _verify_alignment(
        orig_df: pd.DataFrame,
        blocks: NaiveBayesPartitionBlocks,
        split_label: str,
    ) -> None:
        """Mandatory row-by-row alignment verification before joining predictions with descriptive columns."""
        if len(orig_df) != len(blocks.y):
            raise AssertionError(
                f"Length mismatch on {split_label}: orig_df={len(orig_df)} vs y={len(blocks.y)}"
            )
        if not np.array_equal(orig_df["reincide"].to_numpy(dtype=np.int8), blocks.y):
            raise AssertionError(f"Target vector y mismatch on {split_label} during descriptive join!")
        if not np.array_equal(orig_df["resume_id"].to_numpy(dtype=str), blocks.groups):
            raise AssertionError(
                f"Person vector resume_id mismatch on {split_label} during descriptive join!"
            )

    def analyze_o1_reincidence_by_isco(
        self,
        orig_train: pd.DataFrame,
        orig_test: pd.DataFrame,
        oof_proba_nb_h: np.ndarray,
        test_proba_nb_h: np.ndarray,
    ) -> pd.DataFrame:
        """O1: Observed reincidence rate by ISCO major group (1 digit) with 95% Wilson CI and support."""
        rows: List[Dict[str, object]] = []
        overall_tr = float(orig_train["reincide"].mean() * 100.0)
        overall_te = float(orig_test["reincide"].mean() * 100.0)

        for digit in sorted(ISCO_MAJOR_LABELS_ES.keys()):
            label_es = ISCO_MAJOR_LABELS_ES[digit]
            m_tr = (orig_train["isco_major"] == digit).to_numpy()
            m_te = (orig_test["isco_major"] == digit).to_numpy()

            n_tr = int(m_tr.sum())
            if n_tr < self.min_support:
                continue
            pos_tr = int(orig_train.loc[m_tr, "reincide"].sum())
            rate_tr = 100.0 * pos_tr / float(n_tr)
            lo_tr, hi_tr = wilson_ci_95(pos_tr, n_tr)
            persons_tr = int(orig_train.loc[m_tr, "resume_id"].nunique())

            n_te = int(m_te.sum())
            pos_te = int(orig_test.loc[m_te, "reincide"].sum())
            rate_te = 100.0 * pos_te / float(n_te) if n_te > 0 else np.nan
            lo_te, hi_te = wilson_ci_95(pos_te, n_te) if n_te > 0 else (np.nan, np.nan)

            pred_tr = 100.0 * float(oof_proba_nb_h[m_tr].mean())
            pred_te = 100.0 * float(test_proba_nb_h[m_te].mean()) if n_te > 0 else np.nan

            diff_te_tr = (rate_te - rate_tr) if not np.isnan(rate_te) else np.nan
            rows.append(
                {
                    "isco_major": digit,
                    "gran_grupo_isco": label_es,
                    "soporte_filas_train": n_tr,
                    "personas_train": persons_tr,
                    "positivos_train": pos_tr,
                    "tasa_observada_train_pct": round(rate_tr, 2),
                    "ic95_wilson_train_pct": f"[{100.0 * lo_tr:.2f}, {100.0 * hi_tr:.2f}]",
                    "ic95_inf_train_pct": round(100.0 * lo_tr, 2),
                    "ic95_sup_train_pct": round(100.0 * hi_tr, 2),
                    "diff_vs_media_train_pp": round(rate_tr - overall_tr, 2),
                    "prob_media_oof_nb_h_train_pct": round(pred_tr, 2),
                    "soporte_filas_test": n_te,
                    "tasa_confirmada_test_pct": round(rate_te, 2),
                    "ic95_wilson_test_pct": f"[{100.0 * lo_te:.2f}, {100.0 * hi_te:.2f}]",
                    "diff_vs_media_test_pp": round(rate_te - overall_te, 2),
                    "prob_media_nb_h_test_pct": round(pred_te, 2),
                    "brecha_test_menos_train_pp": round(diff_te_tr, 2)
                    if not np.isnan(diff_te_tr)
                    else np.nan,
                    "alerta_brecha_mayor_5pp": bool(abs(diff_te_tr) > 5.0)
                    if not np.isnan(diff_te_tr)
                    else False,
                }
            )

        return (
            pd.DataFrame(rows)
            .sort_values("tasa_observada_train_pct", ascending=False)
            .reset_index(drop=True)
        )

    def analyze_o2_model_performance_by_isco(
        self,
        orig_train: pd.DataFrame,
        orig_test: pd.DataFrame,
        tuned_models: Dict[str, TunedModelArtifact],
    ) -> pd.DataFrame:
        """O2: Per-ISCO major group metrics (PR-AUC, ROC-AUC, F1, Recall, Precision, Brier, calibration) for NB-G, NB-B, NB-H."""
        rows: List[Dict[str, object]] = []
        y_tr = orig_train["reincide"].to_numpy(dtype=np.int8)
        y_te = orig_test["reincide"].to_numpy(dtype=np.int8)

        for digit in sorted(ISCO_MAJOR_LABELS_ES.keys()):
            label_es = ISCO_MAJOR_LABELS_ES[digit]
            m_tr = (orig_train["isco_major"] == digit).to_numpy()
            m_te = (orig_test["isco_major"] == digit).to_numpy()
            n_tr = int(m_tr.sum())
            n_te = int(m_te.sum())
            if n_tr < self.min_support or n_te < 20:
                continue

            y_tr_g = y_tr[m_tr]
            y_te_g = y_te[m_te]
            obs_rate_te = float(y_te_g.mean())

            for model_id in MODEL_ORDER:
                art = tuned_models[model_id]
                tau = art.oof_threshold_tau
                p_oof_g = art.oof_proba_train[m_tr]
                p_te_g = art.test_proba[m_te]
                pred_te_g = (p_te_g >= tau).astype(np.int8)
                pred_oof_g = (p_oof_g >= tau).astype(np.int8)

                pr_auc_cv = float(average_precision_score(y_tr_g, p_oof_g))
                roc_auc_cv = float(roc_auc_score(y_tr_g, p_oof_g))
                f1_cv = float(f1_score(y_tr_g, pred_oof_g, pos_label=1, zero_division=0))

                pr_auc_te = float(average_precision_score(y_te_g, p_te_g))
                roc_auc_te = float(roc_auc_score(y_te_g, p_te_g))
                f1_te = float(f1_score(y_te_g, pred_te_g, pos_label=1, zero_division=0))
                rec_te = float(recall_score(y_te_g, pred_te_g, pos_label=1, zero_division=0))
                prec_te = float(precision_score(y_te_g, pred_te_g, pos_label=1, zero_division=0))
                brier_te = float(brier_score_loss(y_te_g, p_te_g))
                mean_pred_te = float(p_te_g.mean())
                calib_bias = mean_pred_te - obs_rate_te

                rows.append(
                    {
                        "isco_major": digit,
                        "gran_grupo_isco": label_es,
                        "modelo_id": model_id,
                        "soporte_train": n_tr,
                        "soporte_test": n_te,
                        "prevalencia_test_pct": round(100.0 * obs_rate_te, 2),
                        "pr_auc_oof_train": round(pr_auc_cv, 4),
                        "roc_auc_oof_train": round(roc_auc_cv, 4),
                        "f1_oof_train": round(f1_cv, 4),
                        "pr_auc_test": round(pr_auc_te, 4),
                        "lift_pr_auc_vs_azar_test": round(pr_auc_te / max(obs_rate_te, 1e-6), 3),
                        "roc_auc_test": round(roc_auc_te, 4),
                        "f1_test": round(f1_te, 4),
                        "recall_test": round(rec_te, 4),
                        "precision_test": round(prec_te, 4),
                        "brier_test": round(brier_te, 4),
                        "prob_media_pred_test_pct": round(100.0 * mean_pred_te, 2),
                        "sesgo_calibracion_pp": round(100.0 * calib_bias, 2),
                    }
                )

        return pd.DataFrame(rows)

    def analyze_o3_log_odds_and_original_diffs(
        self,
        orig_train: pd.DataFrame,
        train_blocks: NaiveBayesPartitionBlocks,
        nb_h_estimator: HybridNaiveBayes,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """O3: Group-by-variable mean log-odds contributions and original-unit differences (reincide vs no reincide)."""
        # Compute 10 Gaussian + 4 dense binary + 1 aggregated occupation dummy log-odds contribution per row
        prior_lo, contrib_15 = nb_h_estimator.feature_log_odds_contributions(
            train_blocks.X_nb_h,
            split_binary_dense_and_ohe_at=len(BINARY_DENSE_FEATURES),
        )
        col_names_15 = (
            list(GAUSSIAN_HYBRID_FEATURES)
            + list(BINARY_DENSE_FEATURES)
            + ["occupation_code_ohe_bloque"]
        )
        # Exclude constant zero-variance columns so the heatmap shows informative dimensions
        active_indices = [
            i
            for i, c in enumerate(col_names_15)
            if c not in ("n_skills_sin_tipo_rob", "tiene_sin_tipo")
        ]
        active_names = [col_names_15[i] for i in active_indices]
        contrib_active = contrib_15[:, active_indices]

        heatmap_rows: List[Dict[str, object]] = []
        diff_rows: List[Dict[str, object]] = []

        y_tr = orig_train["reincide"].to_numpy(dtype=np.int8)
        edu_high = orig_train["university_level"].isin(["Bachelor", "Master", "PhD"]).to_numpy(dtype=np.float64)

        for digit in sorted(ISCO_MAJOR_LABELS_ES.keys()):
            label_es = ISCO_MAJOR_LABELS_ES[digit]
            mask_g = (orig_train["isco_major"] == digit).to_numpy()
            n_g = int(mask_g.sum())
            if n_g < self.min_support:
                continue

            mask_g1 = mask_g & (y_tr == 1)
            mask_g0 = mask_g & (y_tr == 0)

            # Mean difference in log-odds contribution between reincide=1 and reincide=0 within this group
            mean_c1 = contrib_active[mask_g1].mean(axis=0)
            mean_c0 = contrib_active[mask_g0].mean(axis=0)
            net_shift = mean_c1 - mean_c0

            h_row: Dict[str, object] = {
                "isco_major": digit,
                "gran_grupo_isco": label_es,
                "soporte_train": n_g,
            }
            for col_name, val in zip(active_names, net_shift):
                h_row[col_name] = round(float(val), 4)
            heatmap_rows.append(h_row)

            # Original-units mean differences (reincide=1 minus reincide=0) within the group
            dur_1 = float(orig_train.loc[mask_g1, "dur_q"].mean())
            dur_0 = float(orig_train.loc[mask_g0, "dur_q"].mean())
            prev_1 = float(orig_train.loc[mask_g1, "previous_jobs"].mean())
            prev_0 = float(orig_train.loc[mask_g0, "previous_jobs"].mean())
            sy_1 = float(orig_train.loc[mask_g1, "start_year"].mean())
            sy_0 = float(orig_train.loc[mask_g0, "start_year"].mean())
            ess_1 = float(orig_train.loc[mask_g1, "n_skills_essential"].mean())
            ess_0 = float(orig_train.loc[mask_g0, "n_skills_essential"].mean())
            know_1 = float(orig_train.loc[mask_g1, "n_skills_knowledge"].mean())
            know_0 = float(orig_train.loc[mask_g0, "n_skills_knowledge"].mean())
            vig_1 = 100.0 * float(orig_train.loc[mask_g1, "es_vigente"].mean())
            vig_0 = 100.0 * float(orig_train.loc[mask_g0, "es_vigente"].mean())
            uni_1 = 100.0 * float(edu_high[mask_g1].mean())
            uni_0 = 100.0 * float(edu_high[mask_g0].mean())

            diff_rows.append(
                {
                    "isco_major": digit,
                    "gran_grupo_isco": label_es,
                    "n_reincide_1": int(mask_g1.sum()),
                    "n_reincide_0": int(mask_g0.sum()),
                    "diff_empleos_previos_media": round(prev_1 - prev_0, 2),
                    "diff_duracion_trimestres_media": round(dur_1 - dur_0, 2),
                    "diff_anio_inicio_media": round(sy_1 - sy_0, 2),
                    "diff_skills_essential_media": round(ess_1 - ess_0, 2),
                    "diff_skills_knowledge_media": round(know_1 - know_0, 2),
                    "diff_es_vigente_pp": round(vig_1 - vig_0, 2),
                    "diff_educacion_universitaria_pp": round(uni_1 - uni_0, 2),
                }
            )

        return pd.DataFrame(heatmap_rows), pd.DataFrame(diff_rows)

    def analyze_o4_profile_by_group(self, orig_train: pd.DataFrame) -> pd.DataFrame:
        """O4: Profile by ISCO major group separating reincide=1 vs reincide=0 in original units."""
        rows: List[Dict[str, object]] = []
        for digit in sorted(ISCO_MAJOR_LABELS_ES.keys()):
            label_es = ISCO_MAJOR_LABELS_ES[digit]
            sub_g = orig_train.loc[orig_train["isco_major"] == digit]
            if len(sub_g) < self.min_support:
                continue

            for target_val, target_label in [(0, "0 · No reincide"), (1, "1 · Reincide")]:
                sub = sub_g.loc[sub_g["reincide"] == target_val]
                n_rows = len(sub)
                if n_rows == 0:
                    continue
                edu_vc = sub["university_level"].value_counts()
                top_edu = str(edu_vc.index[0])
                top_edu_pct = 100.0 * float(edu_vc.iloc[0]) / float(n_rows)

                rows.append(
                    {
                        "isco_major": digit,
                        "gran_grupo_isco": label_es,
                        "clase_reincide": target_label,
                        "soporte_filas_train": int(n_rows),
                        "duracion_mediana_trimestres": round(float(sub["dur_q"].median()), 1),
                        "duracion_media_trimestres": round(float(sub["dur_q"].mean()), 2),
                        "empleos_previos_mediana": round(float(sub["previous_jobs"].median()), 1),
                        "empleos_previos_media": round(float(sub["previous_jobs"].mean()), 2),
                        "nivel_educativo_modal": top_edu,
                        "pct_nivel_educativo_modal": round(top_edu_pct, 1),
                        "skills_esenciales_mediana": round(float(sub["n_skills_essential"].median()), 1),
                        "skills_esenciales_media": round(float(sub["n_skills_essential"].mean()), 2),
                        "pct_empleo_vigente": round(100.0 * float(sub["es_vigente"].mean()), 2),
                    }
                )
        return pd.DataFrame(rows)

    def analyze_o5_subgroups_and_occupations(
        self,
        orig_train: pd.DataFrame,
        orig_test: pd.DataFrame,
        o1_df: pd.DataFrame,
        alpha: float = 1.0,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """O5: 2-digit ISCO subgroups and specific ESCO occupations in the 3 highest and 3 lowest ISCO major groups."""
        top3_majors = o1_df.head(3)["isco_major"].tolist()
        bot3_majors = o1_df.tail(3)["isco_major"].tolist()
        selected_majors = top3_majors + [m for m in bot3_majors if m not in top3_majors]
        tier_map = {m: "Top 3 mayor reincidencia" for m in top3_majors}
        for m in bot3_majors:
            tier_map[m] = "Bottom 3 menor reincidencia"

        y_tr = orig_train["reincide"].to_numpy(dtype=np.int8)
        n_c0 = int((y_tr == 0).sum())
        n_c1 = int((y_tr == 1).sum())

        # 1. Two-digit submajor groups within the selected major groups
        sub2_rows: List[Dict[str, object]] = []
        for major in selected_majors:
            sub_tr = orig_train.loc[orig_train["isco_major"] == major]
            sub_te = orig_test.loc[orig_test["isco_major"] == major]
            for s2, grp in sub_tr.groupby("isco_sub2", sort=True):
                n_tr_s = len(grp)
                if n_tr_s < self.min_support:
                    continue
                pos_tr = int(grp["reincide"].sum())
                neg_tr = n_tr_s - pos_tr
                p_s_c1 = (pos_tr + alpha) / (n_c1 + 2.0 * alpha)
                p_s_c0 = (neg_tr + alpha) / (n_c0 + 2.0 * alpha)
                log_ratio = float(np.log(p_s_c1 / p_s_c0))
                lo_tr, hi_tr = wilson_ci_95(pos_tr, n_tr_s)

                grp_te = sub_te.loc[sub_te["isco_sub2"] == s2]
                n_te_s = len(grp_te)
                rate_te = (
                    100.0 * float(grp_te["reincide"].mean()) if n_te_s > 0 else np.nan
                )
                sample_label = str(grp["isco_group_label"].mode().iloc[0])

                rate_tr_s = 100.0 * pos_tr / float(n_tr_s)
                diff_s2 = (rate_te - rate_tr_s) if not np.isnan(rate_te) else np.nan
                sub2_rows.append(
                    {
                        "extremo_grupo": tier_map[major],
                        "gran_grupo_isco": ISCO_MAJOR_LABELS_ES[major],
                        "subgrupo_2d": str(s2),
                        "ejemplo_grupo_unitario": sample_label,
                        "soporte_train": int(n_tr_s),
                        "tasa_reincide_train_pct": round(rate_tr_s, 2),
                        "ic95_wilson_train_pct": f"[{100.0 * lo_tr:.2f}, {100.0 * hi_tr:.2f}]",
                        "log_likelihood_ratio_train": round(log_ratio, 4),
                        "soporte_test": int(n_te_s),
                        "tasa_confirmada_test_pct": round(rate_te, 2)
                        if not np.isnan(rate_te)
                        else np.nan,
                        "brecha_test_menos_train_pp": round(diff_s2, 2)
                        if not np.isnan(diff_s2)
                        else np.nan,
                        "alerta_brecha_mayor_5pp": bool(abs(diff_s2) > 5.0)
                        if not np.isnan(diff_s2)
                        else False,
                        "advertencia_metodologica": (
                            "Asociación descriptiva sujeta a huella ocupacional (reincide se cuenta por resume_id + occupation_code)."
                        ),
                    }
                )
        sub2_df = (
            pd.DataFrame(sub2_rows)
            .sort_values(["extremo_grupo", "log_likelihood_ratio_train"], ascending=[True, False])
            .reset_index(drop=True)
        )

        # 2. Specific ESCO occupations (highest and lowest log-ratio within each selected major group)
        occ_rows: List[Dict[str, object]] = []
        for major in selected_majors:
            sub_tr = orig_train.loc[orig_train["isco_major"] == major]
            sub_te = orig_test.loc[orig_test["isco_major"] == major]
            candidates: List[Dict[str, object]] = []
            for (occ_code, occ_label), grp in sub_tr.groupby(
                ["occupation_code", "occupation_label"], sort=False
            ):
                n_tr_o = len(grp)
                if n_tr_o < self.min_support:
                    continue
                pos_tr = int(grp["reincide"].sum())
                neg_tr = n_tr_o - pos_tr
                p_o_c1 = (pos_tr + alpha) / (n_c1 + 2.0 * alpha)
                p_o_c0 = (neg_tr + alpha) / (n_c0 + 2.0 * alpha)
                log_ratio = float(np.log(p_o_c1 / p_o_c0))
                lo_tr, hi_tr = wilson_ci_95(pos_tr, n_tr_o)

                grp_te = sub_te.loc[sub_te["occupation_code"] == occ_code]
                n_te_o = len(grp_te)
                rate_te = (
                    100.0 * float(grp_te["reincide"].mean()) if n_te_o > 0 else np.nan
                )
                rate_tr_o = 100.0 * pos_tr / float(n_tr_o)
                diff_occ = (rate_te - rate_tr_o) if not np.isnan(rate_te) else np.nan
                candidates.append(
                    {
                        "extremo_grupo": tier_map[major],
                        "gran_grupo_isco": ISCO_MAJOR_LABELS_ES[major],
                        "occupation_code": str(occ_code),
                        "ocupacion_esco": str(occ_label),
                        "soporte_train": int(n_tr_o),
                        "tasa_reincide_train_pct": round(rate_tr_o, 2),
                        "ic95_wilson_train_pct": f"[{100.0 * lo_tr:.2f}, {100.0 * hi_tr:.2f}]",
                        "log_likelihood_ratio_train": round(log_ratio, 4),
                        "soporte_test": int(n_te_o),
                        "tasa_confirmada_test_pct": round(rate_te, 2)
                        if not np.isnan(rate_te)
                        else np.nan,
                        "brecha_test_menos_train_pp": round(diff_occ, 2)
                        if not np.isnan(diff_occ)
                        else np.nan,
                        "alerta_brecha_mayor_5pp": bool(abs(diff_occ) > 5.0)
                        if not np.isnan(diff_occ)
                        else False,
                        "advertencia_circularidad": (
                            "Huella ocupacional N:1 (reincide cuenta repeticiones de occupation_code por persona; describe propensión a repetirse, no causa)."
                        ),
                    }
                )
            if candidates:
                c_df = pd.DataFrame(candidates).sort_values(
                    "log_likelihood_ratio_train", ascending=False
                )
                top_k = c_df.head(3).copy()
                top_k["direccion_en_grupo"] = "Mayor log-ratio (empuja a reincide=1)"
                bot_k = c_df.tail(3).copy()
                bot_k["direccion_en_grupo"] = "Menor log-ratio (empuja a reincide=0)"
                occ_rows.extend(top_k.to_dict("records"))
                occ_rows.extend(bot_k.to_dict("records"))

        occ_df = pd.DataFrame(occ_rows).drop_duplicates(
            subset=["gran_grupo_isco", "occupation_code"]
        ).reset_index(drop=True)
        return sub2_df, occ_df

    def analyze_o6_transitions_link(
        self,
        orig_train: pd.DataFrame,
        orig_test: pd.DataFrame,
        oof_proba_nb_h: np.ndarray,
        test_proba_nb_h: np.ndarray,
    ) -> Tuple[pd.DataFrame, Dict[str, float]]:
        """O6: Persistence in the same ISCO major group in the next classified job vs. mean predicted reincidence probability."""
        def _compute_persistence(df_orig: pd.DataFrame, probs: np.ndarray) -> pd.DataFrame:
            work = df_orig[
                ["resume_id", "start_ord", "job_order", "occupation_code", "isco_group", "isco_major", "reincide"]
            ].copy()
            work["pred_prob"] = probs
            work = work.sort_values(["resume_id", "start_ord", "job_order"], kind="mergesort")
            grp = work.groupby("resume_id", sort=False)
            work["next_occ"] = grp["occupation_code"].shift(-1)
            work["next_isco_4d"] = grp["isco_group"].shift(-1)
            work["next_isco_major"] = grp["isco_major"].shift(-1)
            has_next = work["next_isco_major"].notna()
            trans = work.loc[has_next].copy()
            trans["stay_major_1d"] = trans["isco_major"] == trans["next_isco_major"]
            trans["stay_isco_4d"] = trans["isco_group"] == trans["next_isco_4d"]
            trans["self_loop_occ"] = trans["occupation_code"] == trans["next_occ"]
            return work, trans

        work_tr, trans_tr = _compute_persistence(orig_train, oof_proba_nb_h)
        work_te, trans_te = _compute_persistence(orig_test, test_proba_nb_h)

        rows: List[Dict[str, object]] = []
        for digit in sorted(ISCO_MAJOR_LABELS_ES.keys()):
            label_es = ISCO_MAJOR_LABELS_ES[digit]
            w_tr = work_tr.loc[work_tr["isco_major"] == digit]
            t_tr = trans_tr.loc[trans_tr["isco_major"] == digit]
            w_te = work_te.loc[work_te["isco_major"] == digit]
            t_te = trans_te.loc[trans_te["isco_major"] == digit]

            if len(t_tr) < self.min_support:
                continue

            pers_1d_tr = 100.0 * float(t_tr["stay_major_1d"].mean())
            pers_4d_tr = 100.0 * float(t_tr["stay_isco_4d"].mean())
            stay1_tr = t_tr.loc[t_tr["stay_major_1d"]]
            cond_4d_given_1d_tr = (
                100.0 * float(stay1_tr["stay_isco_4d"].mean()) if len(stay1_tr) > 0 else np.nan
            )
            loop_tr = 100.0 * float(t_tr["self_loop_occ"].mean())
            pred_tr_pct = 100.0 * float(w_tr["pred_prob"].mean())
            obs_tr_pct = 100.0 * float(w_tr["reincide"].mean())
            gap_abs_tr = abs(pred_tr_pct - obs_tr_pct)

            if len(t_te) > 0:
                pers_1d_te = 100.0 * float(t_te["stay_major_1d"].mean())
                stay1_te = t_te.loc[t_te["stay_major_1d"]]
                cond_4d_given_1d_te = (
                    100.0 * float(stay1_te["stay_isco_4d"].mean()) if len(stay1_te) > 0 else np.nan
                )
            else:
                pers_1d_te, cond_4d_given_1d_te = np.nan, np.nan

            if len(w_te) > 0:
                pred_te_pct = 100.0 * float(w_te["pred_prob"].mean())
                obs_te_pct = 100.0 * float(w_te["reincide"].mean())
                gap_abs_te = abs(pred_te_pct - obs_te_pct)
            else:
                pred_te_pct, obs_te_pct, gap_abs_te = np.nan, np.nan, np.nan

            rows.append(
                {
                    "isco_major": digit,
                    "gran_grupo_isco": label_es,
                    "n_empleos_train": int(len(w_tr)),
                    "n_transiciones_origen_train": int(len(t_tr)),
                    "persistencia_mismo_gran_grupo_1d_train_pct": round(pers_1d_tr, 2),
                    "persistencia_mismo_isco_4d_train_pct": round(pers_4d_tr, 2),
                    "fraccion_4d_dado_mismo_1d_train_pct": round(cond_4d_given_1d_tr, 2)
                    if not np.isnan(cond_4d_given_1d_tr)
                    else np.nan,
                    "autolazo_mismo_oficio_train_pct": round(loop_tr, 2),
                    "prob_media_predicha_nb_h_train_pct": round(pred_tr_pct, 2),
                    "tasa_observada_reincide_train_pct": round(obs_tr_pct, 2),
                    "brecha_abs_pred_vs_obs_train_pp": round(gap_abs_tr, 2),
                    "persistencia_mismo_gran_grupo_1d_test_pct": round(pers_1d_te, 2)
                    if not np.isnan(pers_1d_te)
                    else np.nan,
                    "fraccion_4d_dado_mismo_1d_test_pct": round(cond_4d_given_1d_te, 2)
                    if not np.isnan(cond_4d_given_1d_te)
                    else np.nan,
                    "prob_media_predicha_nb_h_test_pct": round(pred_te_pct, 2)
                    if not np.isnan(pred_te_pct)
                    else np.nan,
                    "tasa_observada_reincide_test_pct": round(obs_te_pct, 2)
                    if not np.isnan(obs_te_pct)
                    else np.nan,
                    "brecha_abs_pred_vs_obs_test_pp": round(gap_abs_te, 2)
                    if not np.isnan(gap_abs_te)
                    else np.nan,
                }
            )

        out_df = pd.DataFrame(rows)
        x_pers = out_df["persistencia_mismo_gran_grupo_1d_train_pct"].to_numpy(dtype=np.float64)
        y_prob = out_df["prob_media_predicha_nb_h_train_pct"].to_numpy(dtype=np.float64)
        x_loop = out_df["autolazo_mismo_oficio_train_pct"].to_numpy(dtype=np.float64)

        r_pers, p_pers = stats.pearsonr(x_pers, y_prob)
        rho_pers, p_rho_pers = stats.spearmanr(x_pers, y_prob)
        r_loop, p_loop = stats.pearsonr(x_loop, y_prob)
        rho_loop, p_rho_loop = stats.spearmanr(x_loop, y_prob)

        corr_summary = {
            "n_grupos_isco": int(len(out_df)),
            "pearson_r_persistencia_1d_vs_prob": round(float(r_pers), 4),
            "pearson_p_valor_persistencia_1d": round(float(p_pers), 4),
            "spearman_rho_persistencia_1d_vs_prob": round(float(rho_pers), 4),
            "spearman_p_valor_persistencia_1d": round(float(p_rho_pers), 4),
            "pearson_r_autolazo_oficio_vs_prob": round(float(r_loop), 4),
            "pearson_p_valor_autolazo_oficio": round(float(p_loop), 4),
            "spearman_rho_autolazo_oficio_vs_prob": round(float(rho_loop), 4),
            "spearman_p_valor_autolazo_oficio": round(float(p_rho_loop), 4),
            "brecha_media_abs_pred_vs_obs_train_pp": round(
                float(out_df["brecha_abs_pred_vs_obs_train_pp"].mean()), 2
            ),
            "brecha_max_abs_pred_vs_obs_train_pp": round(
                float(out_df["brecha_abs_pred_vs_obs_train_pp"].max()), 2
            ),
        }
        return out_df, corr_summary

    def run_all_occupation_analyses(
        self,
        orig_train: pd.DataFrame,
        orig_test: pd.DataFrame,
        train_blocks: NaiveBayesPartitionBlocks,
        test_blocks: NaiveBayesPartitionBlocks,
        tuned_models: Dict[str, TunedModelArtifact],
    ) -> OccupationAnalysisBundle:
        """Verify alignment and execute O1 through O6 on Version A."""
        self._verify_alignment(orig_train, train_blocks, split_label="train")
        self._verify_alignment(orig_test, test_blocks, split_label="test")

        nb_h_art = tuned_models[MODEL_NB_H]
        oof_prob_h = nb_h_art.oof_proba_train
        test_prob_h = nb_h_art.test_proba
        nb_h_est: HybridNaiveBayes = nb_h_art.fitted_estimator  # type: ignore[assignment]
        alpha_opt = float(nb_h_art.best_params.get("alpha", 1.0))

        o1_df = self.analyze_o1_reincidence_by_isco(
            orig_train, orig_test, oof_prob_h, test_prob_h
        )
        o2_df = self.analyze_o2_model_performance_by_isco(
            orig_train, orig_test, tuned_models
        )
        o3_heatmap_df, o3_diff_df = self.analyze_o3_log_odds_and_original_diffs(
            orig_train, train_blocks, nb_h_est
        )
        o4_df = self.analyze_o4_profile_by_group(orig_train)
        o5_sub2_df, o5_occ_df = self.analyze_o5_subgroups_and_occupations(
            orig_train, orig_test, o1_df, alpha=alpha_opt
        )
        o6_df, o6_corr = self.analyze_o6_transitions_link(
            orig_train, orig_test, oof_prob_h, test_prob_h
        )

        return OccupationAnalysisBundle(
            o1_rates_table=o1_df,
            o2_performance_by_isco_table=o2_df,
            o3_log_odds_heatmap_df=o3_heatmap_df,
            o3_original_units_diff_table=o3_diff_df,
            o4_profile_by_group_table=o4_df,
            o5_subgroups_2d_table=o5_sub2_df,
            o5_occupations_4d_table=o5_occ_df,
            o6_transitions_persistence_table=o6_df,
            o6_correlations_summary=o6_corr,
        )
