"""Section 13: Pattern analyses K1 to K6 on Version A in original units (user priority: occupational groups)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    cohen_kappa_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from scripts.ScriptsCsv.NaiveBayes.evaluation import (
    compute_equal_alert_rate_cutoff,
    paired_bootstrap_person_diffs,
)
from scripts.ScriptsCsv.NaiveBayes.occupation_analysis import wilson_ci_95

from .config import ISCO_MAJOR_LABELS_ES, KNNConfig
from .feature_blocks import KNNPartitionBlocks
from .models import KNNModelSpec
from .neighbors_explainer import CaseExplanationBundle, NeighborsExplainer


@dataclass(frozen=True)
class KNNPatternsBundle:
    """Complete outputs of Section 13 (Pattern analyses K1 through K6 in original units)."""

    primary_knn_model_id: str
    k1_isco_performance_table: pd.DataFrame
    k2_case_explanations: CaseExplanationBundle
    k3_deciles_table: pd.DataFrame
    k3_top_vs_bottom_profile_table: pd.DataFrame
    k3_isco_composition_table: pd.DataFrame
    k4_agreement_summary: Dict[str, object]
    k4_crosstab_table: pd.DataFrame
    k4_disagreement_by_isco_table: pd.DataFrame
    k4_disagreement_profiles_table: pd.DataFrame
    k5_error_profiles_table: pd.DataFrame
    k5_error_subgroups_table: pd.DataFrame
    k6_job_order_table: pd.DataFrame
    k6_start_year_table: pd.DataFrame
    k6_slope_summary_table: pd.DataFrame


class KNNPatternAnalyzer:
    """Execute Section 13 pattern analyses K1 to K6 on Version A in original units."""

    def __init__(
        self,
        config: KNNConfig,
        neighbors_explainer: NeighborsExplainer | None = None,
    ) -> None:
        self.config = config
        self.min_support = int(config.min_subgroup_support)
        self.neighbors_explainer = neighbors_explainer or NeighborsExplainer(top_neighbors_to_display=5)

    def analyze_k1_by_isco_major(
        self,
        orig_train: pd.DataFrame,
        orig_eval_test: pd.DataFrame,
        groups_eval_test: np.ndarray,
        knn_prob: np.ndarray,
        nb_h_prob: np.ndarray,
        knn_tau_eq: float,
        nb_h_tau: float,
    ) -> pd.DataFrame:
        """K1: Observed rates (train & test + Wilson CI + >5pp flag) and KNN vs NB-H metrics with paired CIs."""
        y_te = orig_eval_test["reincide"].to_numpy(dtype=np.int8)
        rows: List[Dict[str, object]] = []

        for digit in sorted(ISCO_MAJOR_LABELS_ES.keys()):
            label_es = ISCO_MAJOR_LABELS_ES[digit]
            m_tr = (orig_train["isco_major"] == digit).to_numpy()
            m_te = (orig_eval_test["isco_major"] == digit).to_numpy()
            n_tr = int(m_tr.sum())
            n_te = int(m_te.sum())
            if n_tr < self.min_support or n_te < 30:
                continue

            pos_tr = int(orig_train.loc[m_tr, "reincide"].sum())
            rate_tr = 100.0 * pos_tr / float(n_tr)
            lo_tr, hi_tr = wilson_ci_95(pos_tr, n_tr)

            y_g = y_te[m_te]
            pos_te = int(y_g.sum())
            rate_te = 100.0 * pos_te / float(n_te)
            lo_te, hi_te = wilson_ci_95(pos_te, n_te)
            gap_pp = rate_te - rate_tr

            pk = knn_prob[m_te]
            pn = nb_h_prob[m_te]
            gg = groups_eval_test[m_te]

            pred_k = (pk >= knn_tau_eq).astype(np.int8)
            pred_n = (pn >= nb_h_tau).astype(np.int8)

            pr_k = float(average_precision_score(y_g, pk))
            roc_k = float(roc_auc_score(y_g, pk))
            f1_k = float(f1_score(y_g, pred_k, pos_label=1, zero_division=0))
            rec_k = float(recall_score(y_g, pred_k, pos_label=1, zero_division=0))

            pr_n = float(average_precision_score(y_g, pn))
            roc_n = float(roc_auc_score(y_g, pn))
            f1_n = float(f1_score(y_g, pred_n, pos_label=1, zero_division=0))
            rec_n = float(recall_score(y_g, pred_n, pos_label=1, zero_division=0))

            paired = paired_bootstrap_person_diffs(
                y_true=y_g,
                prob_a=pk,
                prob_b=pn,
                groups=gg,
                threshold_a=knn_tau_eq,
                threshold_b=nb_h_tau,
                n_resamples=self.config.bootstrap_resamples,
                random_state=self.config.random_state,
            )

            rows.append(
                {
                    "isco_major": digit,
                    "gran_grupo_isco": label_es,
                    "soporte_train": n_tr,
                    "tasa_obs_train_pct": round(rate_tr, 2),
                    "ic95_wilson_train_pct": f"[{100.0 * lo_tr:.2f}, {100.0 * hi_tr:.2f}]",
                    "soporte_test": n_te,
                    "tasa_obs_test_pct": round(rate_te, 2),
                    "ic95_wilson_test_pct": f"[{100.0 * lo_te:.2f}, {100.0 * hi_te:.2f}]",
                    "brecha_test_menos_train_pp": round(gap_pp, 2),
                    "alerta_brecha_mayor_5pp": bool(abs(gap_pp) > 5.0),
                    "knn_pr_auc_test": round(pr_k, 4),
                    "nb_h_pr_auc_test": round(pr_n, 4),
                    "delta_pr_auc_knn_menos_nbh": round(float(paired["delta_pr_auc"]), 4),
                    "ic95_delta_pr_auc": f"[{float(paired['delta_pr_auc_ci_low']):+.4f}, {float(paired['delta_pr_auc_ci_high']):+.4f}]",
                    "veredicto_pr_auc": str(paired["veredicto_pr_auc"]),
                    "knn_roc_auc_test": round(roc_k, 4),
                    "nb_h_roc_auc_test": round(roc_n, 4),
                    "delta_roc_auc_knn_menos_nbh": round(float(paired["delta_roc_auc"]), 4),
                    "knn_f1_igual_alerta": round(f1_k, 4),
                    "nb_h_f1_igual_alerta": round(f1_n, 4),
                    "delta_f1_igual_alerta": round(float(paired["delta_f1"]), 4),
                    "knn_recall_igual_alerta": round(rec_k, 4),
                    "nb_h_recall_igual_alerta": round(rec_n, 4),
                    "prob_media_knn_test_pct": round(100.0 * float(pk.mean()), 2),
                    "brecha_pred_menos_obs_knn_pp": round(100.0 * float(pk.mean()) - rate_te, 2),
                }
            )

        return pd.DataFrame(rows).sort_values("tasa_obs_test_pct", ascending=False).reset_index(drop=True)

    def analyze_k3_risk_deciles(
        self,
        orig_eval_test: pd.DataFrame,
        knn_prob: np.ndarray,
        nb_h_prob: np.ndarray,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """K3: Test risk deciles (observed rate, lift, cumulative gain), D10 vs D01 profile, ISCO composition vs NB-H."""
        work = orig_eval_test.copy()
        work["prob_knn"] = knn_prob
        work["prob_nbh"] = nb_h_prob
        work["decil_knn"] = pd.qcut(work["prob_knn"].rank(method="first"), q=10, labels=False) + 1
        work["decil_nbh"] = pd.qcut(work["prob_nbh"].rank(method="first"), q=10, labels=False) + 1

        overall_rate = float(work["reincide"].mean())
        total_pos = int(work["reincide"].sum())

        dec_rows: List[Dict[str, object]] = []
        cum_pos_k = 0
        cum_pos_n = 0
        cum_rows = 0

        for d in range(10, 0, -1):
            sk = work.loc[work["decil_knn"] == d]
            sn = work.loc[work["decil_nbh"] == d]
            n_d = len(sk)
            pos_k = int(sk["reincide"].sum())
            pos_n = int(sn["reincide"].sum())
            rate_k = pos_k / float(n_d)
            rate_n = pos_n / float(len(sn))
            cum_pos_k += pos_k
            cum_pos_n += pos_n
            cum_rows += n_d

            dec_rows.append(
                {
                    "decil_riesgo": f"D{d:02d}" + (" (Mayor riesgo)" if d == 10 else (" (Menor riesgo)" if d == 1 else "")),
                    "decil_orden": d,
                    "soporte_test": int(n_d),
                    "prob_media_knn_pct": round(100.0 * float(sk["prob_knn"].mean()), 2),
                    "tasa_obs_knn_test_pct": round(100.0 * rate_k, 2),
                    "brecha_pred_menos_obs_knn_pp": round(100.0 * (float(sk["prob_knn"].mean()) - rate_k), 2),
                    "lift_knn_test": round(rate_k / max(overall_rate, 1e-9), 3),
                    "ganancia_acum_knn_pct": round(100.0 * cum_pos_k / float(total_pos), 2),
                    "tasa_obs_nb_h_test_pct": round(100.0 * rate_n, 2),
                    "lift_nb_h_test": round(rate_n / max(overall_rate, 1e-9), 3),
                    "ganancia_acum_nb_h_pct": round(100.0 * cum_pos_n / float(total_pos), 2),
                    "pct_poblacion_acumulada": round(100.0 * cum_rows / float(len(work)), 1),
                }
            )

        d10 = work.loc[work["decil_knn"] == 10]
        d01 = work.loc[work["decil_knn"] == 1]
        d10_n = work.loc[work["decil_nbh"] == 10]
        d01_n = work.loc[work["decil_nbh"] == 1]

        prof_rows = [
            {
                "indicador_unidades_originales": "Soporte de filas (test)",
                "D01_KNN": f"{len(d01):,}",
                "D10_KNN": f"{len(d10):,}",
                "diff_D10_menos_D01_KNN": f"{len(d10) - len(d01):,}",
                "D01_NB_H": f"{len(d01_n):,}",
                "D10_NB_H": f"{len(d10_n):,}",
            },
            {
                "indicador_unidades_originales": "Tasa observada de reincidencia (%)",
                "D01_KNN": round(100.0 * float(d01["reincide"].mean()), 2),
                "D10_KNN": round(100.0 * float(d10["reincide"].mean()), 2),
                "diff_D10_menos_D01_KNN": round(100.0 * float(d10["reincide"].mean() - d01["reincide"].mean()), 2),
                "D01_NB_H": round(100.0 * float(d01_n["reincide"].mean()), 2),
                "D10_NB_H": round(100.0 * float(d10_n["reincide"].mean()), 2),
            },
            {
                "indicador_unidades_originales": "Empleos previos acumulados (media / mediana)",
                "D01_KNN": f"{d01['previous_jobs'].mean():.2f} / {d01['previous_jobs'].median():.1f}",
                "D10_KNN": f"{d10['previous_jobs'].mean():.2f} / {d10['previous_jobs'].median():.1f}",
                "diff_D10_menos_D01_KNN": round(float(d10["previous_jobs"].mean() - d01["previous_jobs"].mean()), 2),
                "D01_NB_H": f"{d01_n['previous_jobs'].mean():.2f} / {d01_n['previous_jobs'].median():.1f}",
                "D10_NB_H": f"{d10_n['previous_jobs'].mean():.2f} / {d10_n['previous_jobs'].median():.1f}",
            },
            {
                "indicador_unidades_originales": "Duración del empleo en trimestres (media / mediana)",
                "D01_KNN": f"{d01['dur_q'].mean():.2f} / {d01['dur_q'].median():.1f}",
                "D10_KNN": f"{d10['dur_q'].mean():.2f} / {d10['dur_q'].median():.1f}",
                "diff_D10_menos_D01_KNN": round(float(d10["dur_q"].mean() - d01["dur_q"].mean()), 2),
                "D01_NB_H": f"{d01_n['dur_q'].mean():.2f} / {d01_n['dur_q'].median():.1f}",
                "D10_NB_H": f"{d10_n['dur_q'].mean():.2f} / {d10_n['dur_q'].median():.1f}",
            },
            {
                "indicador_unidades_originales": "Año de inicio (media / mediana)",
                "D01_KNN": f"{d01['start_year'].mean():.1f} / {d01['start_year'].median():.0f}",
                "D10_KNN": f"{d10['start_year'].mean():.1f} / {d10['start_year'].median():.0f}",
                "diff_D10_menos_D01_KNN": round(float(d10["start_year"].mean() - d01["start_year"].mean()), 2),
                "D01_NB_H": f"{d01_n['start_year'].mean():.1f} / {d01_n['start_year'].median():.0f}",
                "D10_NB_H": f"{d10_n['start_year'].mean():.1f} / {d10_n['start_year'].median():.0f}",
            },
            {
                "indicador_unidades_originales": "Competencias esenciales ESCO (media / mediana)",
                "D01_KNN": f"{d01['n_skills_essential'].mean():.2f} / {d01['n_skills_essential'].median():.1f}",
                "D10_KNN": f"{d10['n_skills_essential'].mean():.2f} / {d10['n_skills_essential'].median():.1f}",
                "diff_D10_menos_D01_KNN": round(float(d10["n_skills_essential"].mean() - d01["n_skills_essential"].mean()), 2),
                "D01_NB_H": f"{d01_n['n_skills_essential'].mean():.2f} / {d01_n['n_skills_essential'].median():.1f}",
                "D10_NB_H": f"{d10_n['n_skills_essential'].mean():.2f} / {d10_n['n_skills_essential'].median():.1f}",
            },
            {
                "indicador_unidades_originales": "Proporción de empleos vigentes (%)",
                "D01_KNN": round(100.0 * float(d01["es_vigente"].mean()), 2),
                "D10_KNN": round(100.0 * float(d10["es_vigente"].mean()), 2),
                "diff_D10_menos_D01_KNN": round(100.0 * float(d10["es_vigente"].mean() - d01["es_vigente"].mean()), 2),
                "D01_NB_H": round(100.0 * float(d01_n["es_vigente"].mean()), 2),
                "D10_NB_H": round(100.0 * float(d10_n["es_vigente"].mean()), 2),
            },
        ]

        isco_rows: List[Dict[str, object]] = []
        for digit in sorted(ISCO_MAJOR_LABELS_ES.keys()):
            sh_all = 100.0 * float((work["isco_major"] == digit).mean())
            sh_k01 = 100.0 * float((d01["isco_major"] == digit).mean())
            sh_k10 = 100.0 * float((d10["isco_major"] == digit).mean())
            sh_n01 = 100.0 * float((d01_n["isco_major"] == digit).mean())
            sh_n10 = 100.0 * float((d10_n["isco_major"] == digit).mean())
            isco_rows.append(
                {
                    "isco_major": digit,
                    "gran_grupo_isco": ISCO_MAJOR_LABELS_ES[digit],
                    "participacion_test_total_pct": round(sh_all, 2),
                    "participacion_D01_KNN_pct": round(sh_k01, 2),
                    "participacion_D10_KNN_pct": round(sh_k10, 2),
                    "diff_D10_menos_D01_KNN_pp": round(sh_k10 - sh_k01, 2),
                    "participacion_D01_NB_H_pct": round(sh_n01, 2),
                    "participacion_D10_NB_H_pct": round(sh_n10, 2),
                    "sobremuestreo_D10_KNN_vs_total": round(sh_k10 / max(sh_all, 1e-4), 2),
                }
            )

        return pd.DataFrame(dec_rows), pd.DataFrame(prof_rows), pd.DataFrame(isco_rows)

    def analyze_k4_agreement_with_nb_h(
        self,
        orig_train: pd.DataFrame,
        orig_eval_test: pd.DataFrame,
        knn_prob: np.ndarray,
        nb_h_prob: np.ndarray,
        knn_tau_eq: float,
        nb_h_tau: float,
    ) -> Tuple[Dict[str, object], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """K4: Spearman correlation, equal-alert-rate cross-tabulation, and disagreement analysis vs NB-H."""
        y_te = orig_eval_test["reincide"].to_numpy(dtype=np.int8)
        rho_sp = float(stats.spearmanr(knn_prob, nb_h_prob).statistic)
        r_pears = float(np.corrcoef(knn_prob, nb_h_prob)[0, 1])

        pred_k = (knn_prob >= knn_tau_eq).astype(np.int8)
        pred_n = (nb_h_prob >= nb_h_tau).astype(np.int8)
        agree_pct = 100.0 * float(np.mean(pred_k == pred_n))
        kappa = float(cohen_kappa_score(pred_n, pred_k))

        # Descriptive complementarity diagnostic (equal-weight rank average; not tuned on test!)
        rank_k = stats.rankdata(knn_prob) / float(len(knn_prob))
        rank_n = stats.rankdata(nb_h_prob) / float(len(nb_h_prob))
        blend_5050 = 0.5 * (rank_k + rank_n)
        pr_k = float(average_precision_score(y_te, knn_prob))
        pr_n = float(average_precision_score(y_te, nb_h_prob))
        pr_blend = float(average_precision_score(y_te, blend_5050))
        roc_blend = float(roc_auc_score(y_te, blend_5050))

        summary = {
            "spearman_rho_test": round(rho_sp, 4),
            "pearson_r_test": round(r_pears, 4),
            "acuerdo_binario_igual_alerta_pct": round(agree_pct, 2),
            "desacuerdo_binario_igual_alerta_pct": round(100.0 - agree_pct, 2),
            "cohen_kappa_igual_alerta": round(kappa, 4),
            "tasa_alerta_knn_pct": round(100.0 * float(pred_k.mean()), 2),
            "tasa_alerta_nb_h_pct": round(100.0 * float(pred_n.mean()), 2),
            "pr_auc_knn_test": round(pr_k, 4),
            "pr_auc_nb_h_test": round(pr_n, 4),
            "pr_auc_promedio_rangos_50_50_descriptivo": round(pr_blend, 4),
            "roc_auc_promedio_rangos_50_50_descriptivo": round(roc_blend, 4),
            "ganancia_complementariedad_pr_auc_vs_mejor": round(pr_blend - max(pr_k, pr_n), 4),
        }

        cells = [
            ("Ambos predicen 1 (Acuerdo positivo)", (pred_k == 1) & (pred_n == 1)),
            ("Solo KNN predice 1 (Desacuerdo KNN+ / NB-H-)", (pred_k == 1) & (pred_n == 0)),
            ("Solo NB-H predice 1 (Desacuerdo KNN- / NB-H+)", (pred_k == 0) & (pred_n == 1)),
            ("Ambos predicen 0 (Acuerdo negativo)", (pred_k == 0) & (pred_n == 0)),
        ]
        ct_rows: List[Dict[str, object]] = []
        prof_rows: List[Dict[str, object]] = []
        for lbl, mask in cells:
            n_c = int(mask.sum())
            rate_c = 100.0 * float(y_te[mask].mean()) if n_c > 0 else np.nan
            ct_rows.append(
                {
                    "celda_concordancia": lbl,
                    "filas_test": n_c,
                    "pct_del_test": round(100.0 * n_c / float(len(y_te)), 2),
                    "tasa_obs_reincidencia_test_pct": round(rate_c, 2),
                    "prob_media_knn_pct": round(100.0 * float(knn_prob[mask].mean()), 2) if n_c > 0 else np.nan,
                    "prob_media_nb_h_pct": round(100.0 * float(nb_h_prob[mask].mean()), 2) if n_c > 0 else np.nan,
                }
            )
            if n_c > 0:
                sub = orig_eval_test.loc[mask]
                prof_rows.append(
                    {
                        "celda_concordancia": lbl,
                        "soporte_test": n_c,
                        "tasa_obs_reincide_pct": round(rate_c, 2),
                        "empleos_previos_mediana": round(float(sub["previous_jobs"].median()), 1),
                        "duracion_mediana_trim": round(float(sub["dur_q"].median()), 1),
                        "anio_inicio_mediana": int(sub["start_year"].median()),
                        "skills_esenciales_mediana": round(float(sub["n_skills_essential"].median()), 1),
                        "pct_empleo_vigente": round(100.0 * float(sub["es_vigente"].mean()), 2),
                        "gran_grupo_isco_modal": str(sub["isco_major_label_es"].mode().iloc[0]),
                        "nivel_educativo_modal": str(sub["university_level"].mode().iloc[0]),
                    }
                )

        # Disagreement by ISCO major group
        dis_isco_rows: List[Dict[str, object]] = []
        for digit in sorted(ISCO_MAJOR_LABELS_ES.keys()):
            m_tr = (orig_train["isco_major"] == digit).to_numpy()
            m_te = (orig_eval_test["isco_major"] == digit).to_numpy()
            n_tr = int(m_tr.sum())
            n_te = int(m_te.sum())
            if n_tr < self.min_support or n_te < 30:
                continue
            r_tr = 100.0 * float(orig_train.loc[m_tr, "reincide"].mean())
            r_te = 100.0 * float(y_te[m_te].mean())
            gap_pp = r_te - r_tr
            dis_pct = 100.0 * float(np.mean(pred_k[m_te] != pred_n[m_te]))
            only_k = 100.0 * float(np.mean((pred_k[m_te] == 1) & (pred_n[m_te] == 0)))
            only_n = 100.0 * float(np.mean((pred_k[m_te] == 0) & (pred_n[m_te] == 1)))
            rho_g = float(stats.spearmanr(knn_prob[m_te], nb_h_prob[m_te]).statistic)
            dis_isco_rows.append(
                {
                    "isco_major": digit,
                    "gran_grupo_isco": ISCO_MAJOR_LABELS_ES[digit],
                    "soporte_train": n_tr,
                    "soporte_test": n_te,
                    "tasa_obs_train_pct": round(r_tr, 2),
                    "tasa_obs_test_pct": round(r_te, 2),
                    "brecha_test_menos_train_pp": round(gap_pp, 2),
                    "alerta_brecha_mayor_5pp": bool(abs(gap_pp) > 5.0),
                    "spearman_rho_grupo": round(rho_g, 4),
                    "desacuerdo_total_pct": round(dis_pct, 2),
                    "solo_knn_alerta_pct": round(only_k, 2),
                    "solo_nb_h_alerta_pct": round(only_n, 2),
                }
            )
        dis_isco_df = pd.DataFrame(dis_isco_rows).sort_values("desacuerdo_total_pct", ascending=False).reset_index(drop=True)

        return summary, pd.DataFrame(ct_rows), dis_isco_df, pd.DataFrame(prof_rows)

    def analyze_k5_error_analysis(
        self,
        orig_train: pd.DataFrame,
        orig_eval_test: pd.DataFrame,
        knn_prob: np.ndarray,
        knn_tau_oof: float,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """K5: Original-unit profiles of TP, FP, FN, TN and subgroup error concentration (ISCO & job_order)."""
        y_te = orig_eval_test["reincide"].to_numpy(dtype=np.int8)
        pred_te = (knn_prob >= knn_tau_oof).astype(np.int8)

        quads = [
            ("TP · Verdadero Positivo (reincide=1, pred=1)", (y_te == 1) & (pred_te == 1)),
            ("FP · Falso Positivo (reincide=0, pred=1)", (y_te == 0) & (pred_te == 1)),
            ("FN · Falso Negativo (reincide=1, pred=0)", (y_te == 1) & (pred_te == 0)),
            ("TN · Verdadero Negativo (reincide=0, pred=0)", (y_te == 0) & (pred_te == 0)),
        ]
        prof_rows: List[Dict[str, object]] = []
        for q_lbl, mask in quads:
            n_q = int(mask.sum())
            if n_q == 0:
                continue
            sub = orig_eval_test.loc[mask]
            prof_rows.append(
                {
                    "celda_confusion": q_lbl,
                    "soporte_test": n_q,
                    "pct_total_test": round(100.0 * n_q / float(len(y_te)), 2),
                    "prob_media_knn_pct": round(100.0 * float(knn_prob[mask].mean()), 2),
                    "empleos_previos_mediana": round(float(sub["previous_jobs"].median()), 1),
                    "empleos_previos_media": round(float(sub["previous_jobs"].mean()), 2),
                    "duracion_mediana_trim": round(float(sub["dur_q"].median()), 1),
                    "duracion_media_trim": round(float(sub["dur_q"].mean()), 2),
                    "anio_inicio_mediana": int(sub["start_year"].median()),
                    "skills_esenciales_mediana": round(float(sub["n_skills_essential"].median()), 1),
                    "pct_empleo_vigente": round(100.0 * float(sub["es_vigente"].mean()), 2),
                    "gran_grupo_isco_modal": str(sub["isco_major_label_es"].mode().iloc[0]),
                    "nivel_educativo_modal": str(sub["university_level"].mode().iloc[0]),
                }
            )

        sub_err_rows: List[Dict[str, object]] = []
        for digit in sorted(ISCO_MAJOR_LABELS_ES.keys()):
            m_tr = (orig_train["isco_major"] == digit).to_numpy()
            m_te = (orig_eval_test["isco_major"] == digit).to_numpy()
            if int(m_tr.sum()) < self.min_support or int(m_te.sum()) < 30:
                continue
            r_tr = 100.0 * float(orig_train.loc[m_tr, "reincide"].mean())
            y_g = y_te[m_te]
            p_g = pred_te[m_te]
            r_te = 100.0 * float(y_g.mean())
            gap_pp = r_te - r_tr
            fpr = 100.0 * float(((y_g == 0) & (p_g == 1)).sum()) / float(max(int((y_g == 0).sum()), 1))
            fnr = 100.0 * float(((y_g == 1) & (p_g == 0)).sum()) / float(max(int((y_g == 1).sum()), 1))
            err = 100.0 * float((y_g != p_g).mean())
            sub_err_rows.append(
                {
                    "dimension": "Gran grupo ISCO",
                    "subgrupo": ISCO_MAJOR_LABELS_ES[digit],
                    "soporte_train": int(m_tr.sum()),
                    "soporte_test": int(m_te.sum()),
                    "tasa_obs_train_pct": round(r_tr, 2),
                    "tasa_obs_test_pct": round(r_te, 2),
                    "brecha_test_menos_train_pp": round(gap_pp, 2),
                    "alerta_brecha_mayor_5pp": bool(abs(gap_pp) > 5.0),
                    "tasa_error_global_test_pct": round(err, 2),
                    "FPR_falsos_positivos_pct": round(fpr, 2),
                    "FNR_falsos_negativos_pct": round(fnr, 2),
                    "tipo_fallo_dominante": (
                        "Falsos Positivos (sobrepredicción)" if fpr > fnr else "Falsos Negativos (omisión)"
                    ),
                }
            )

        for jb_lbl, cond_fn in [
            ("1 (1er empleo)", lambda df: (df["job_order"] == 1).to_numpy()),
            ("2 a 3 empleos", lambda df: df["job_order"].isin([2, 3]).to_numpy()),
            ("4 a 5 empleos", lambda df: df["job_order"].isin([4, 5]).to_numpy()),
            ("6+ empleos (carrera avanzada)", lambda df: (df["job_order"] >= 6).to_numpy()),
        ]:
            m_tr = cond_fn(orig_train)
            m_te = cond_fn(orig_eval_test)
            r_tr = 100.0 * float(orig_train.loc[m_tr, "reincide"].mean())
            y_g = y_te[m_te]
            p_g = pred_te[m_te]
            r_te = 100.0 * float(y_g.mean())
            gap_pp = r_te - r_tr
            fpr = 100.0 * float(((y_g == 0) & (p_g == 1)).sum()) / float(max(int((y_g == 0).sum()), 1))
            fnr = 100.0 * float(((y_g == 1) & (p_g == 0)).sum()) / float(max(int((y_g == 1).sum()), 1))
            err = 100.0 * float((y_g != p_g).mean())
            sub_err_rows.append(
                {
                    "dimension": "Tramo de orden del empleo",
                    "subgrupo": jb_lbl,
                    "soporte_train": int(m_tr.sum()),
                    "soporte_test": int(m_te.sum()),
                    "tasa_obs_train_pct": round(r_tr, 2),
                    "tasa_obs_test_pct": round(r_te, 2),
                    "brecha_test_menos_train_pp": round(gap_pp, 2),
                    "alerta_brecha_mayor_5pp": bool(abs(gap_pp) > 5.0),
                    "tasa_error_global_test_pct": round(err, 2),
                    "FPR_falsos_positivos_pct": round(fpr, 2),
                    "FNR_falsos_negativos_pct": round(fnr, 2),
                    "tipo_fallo_dominante": (
                        "Falsos Positivos (sobrepredicción)" if fpr > fnr else "Falsos Negativos (omisión)"
                    ),
                }
            )

        return pd.DataFrame(prof_rows), pd.DataFrame(sub_err_rows)

    def analyze_k6_career_position_and_period(
        self,
        orig_train: pd.DataFrame,
        orig_eval_test: pd.DataFrame,
        knn_prob: np.ndarray,
        nb_h_prob: np.ndarray,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """K6: Observed vs predicted rate by job_order & start_year with slope ratios and per-bin gaps."""
        def _job_bands(s: pd.Series) -> pd.Series:
            return pd.cut(
                s,
                bins=[0, 1, 2, 3, 5, 8, 10000],
                labels=["1 (1er empleo)", "2 (2do empleo)", "3 (3er empleo)", "4–5 empleos", "6–8 empleos", "9+ empleos"],
            )

        def _year_bands(s: pd.Series) -> pd.Series:
            return pd.cut(
                s,
                bins=[-10000, 1999, 2004, 2009, 2014, 2019, 10000],
                labels=["<= 1999", "2000–2004", "2005–2009", "2010–2014", "2015–2019", "2020+"],
            )

        def _summarize(b_tr: pd.Series, b_te: pd.Series, col_name: str) -> pd.DataFrame:
            rows: List[Dict[str, object]] = []
            for cat in b_tr.cat.categories:
                m_tr = (b_tr == cat).to_numpy()
                m_te = (b_te == cat).to_numpy()
                n_tr = int(m_tr.sum())
                n_te = int(m_te.sum())
                if n_tr < self.min_support or n_te < 20:
                    continue
                pos_tr = int(orig_train.loc[m_tr, "reincide"].sum())
                obs_tr = 100.0 * pos_tr / float(n_tr)
                pos_te = int(orig_eval_test.loc[m_te, "reincide"].sum())
                obs_te = 100.0 * pos_te / float(n_te)
                lo_te, hi_te = wilson_ci_95(pos_te, n_te)

                pred_k = 100.0 * float(knn_prob[m_te].mean())
                pred_n = 100.0 * float(nb_h_prob[m_te].mean())
                gap_tr_te = obs_te - obs_tr

                rows.append(
                    {
                        col_name: str(cat),
                        "soporte_train": n_tr,
                        "tasa_obs_train_pct": round(obs_tr, 2),
                        "soporte_test": n_te,
                        "tasa_obs_test_pct": round(obs_te, 2),
                        "ic95_wilson_test_pct": f"[{100.0 * lo_te:.2f}, {100.0 * hi_te:.2f}]",
                        "brecha_test_menos_train_pp": round(gap_tr_te, 2),
                        "alerta_brecha_mayor_5pp": bool(abs(gap_tr_te) > 5.0),
                        "prob_media_knn_test_pct": round(pred_k, 2),
                        "brecha_knn_menos_obs_test_pp": round(pred_k - obs_te, 2),
                        "prob_media_nb_h_test_pct": round(pred_n, 2),
                        "brecha_nb_h_menos_obs_test_pp": round(pred_n - obs_te, 2),
                    }
                )
            return pd.DataFrame(rows)

        jb_df = _summarize(_job_bands(orig_train["job_order"]), _job_bands(orig_eval_test["job_order"]), "tramo_job_order")
        yr_df = _summarize(_year_bands(orig_train["start_year"]), _year_bands(orig_eval_test["start_year"]), "periodo_anio_inicio")

        # Quantify slope ratios & max absolute bin gaps for both job_order and start_year
        slope_rows: List[Dict[str, object]] = []
        for dim_lbl, df_d in [
            ("Posición en la carrera (job_order: 1er empleo -> 9+)", jb_df),
            ("Período calendario (start_year: <=1999 -> 2020+)", yr_df),
        ]:
            obs_rng = float(df_d["tasa_obs_test_pct"].iloc[-1] - df_d["tasa_obs_test_pct"].iloc[0])
            knn_rng = float(df_d["prob_media_knn_test_pct"].iloc[-1] - df_d["prob_media_knn_test_pct"].iloc[0])
            nbh_rng = float(df_d["prob_media_nb_h_test_pct"].iloc[-1] - df_d["prob_media_nb_h_test_pct"].iloc[0])
            ratio_k = knn_rng / obs_rng if abs(obs_rng) > 1e-9 else np.nan
            ratio_n = nbh_rng / obs_rng if abs(obs_rng) > 1e-9 else np.nan
            slope_rows.append(
                {
                    "dimension_temporal_carrera": dim_lbl,
                    "rango_observado_test_pp": round(obs_rng, 2),
                    "rango_predicho_knn_test_pp": round(knn_rng, 2),
                    "razon_pendiente_knn_sobre_obs": round(ratio_k, 4),
                    "brecha_max_abs_tramo_knn_pp": round(float(df_d["brecha_knn_menos_obs_test_pp"].abs().max()), 2),
                    "brecha_media_abs_tramo_knn_pp": round(float(df_d["brecha_knn_menos_obs_test_pp"].abs().mean()), 2),
                    "rango_predicho_nb_h_test_pp": round(nbh_rng, 2),
                    "razon_pendiente_nb_h_sobre_obs": round(ratio_n, 4),
                    "brecha_max_abs_tramo_nb_h_pp": round(float(df_d["brecha_nb_h_menos_obs_test_pp"].abs().max()), 2),
                }
            )

        return jb_df, yr_df, pd.DataFrame(slope_rows)

    def run_all_patterns(
        self,
        train_blocks: KNNPartitionBlocks,
        test_blocks: KNNPartitionBlocks,
        orig_train: pd.DataFrame,
        orig_test: pd.DataFrame,
        primary_spec: KNNModelSpec,
        knn_test_proba: np.ndarray,
        knn_tau_oof: float,
        nb_h_test_proba: np.ndarray,
        nb_h_tau: float,
        eval_row_idx_test: np.ndarray | None = None,
    ) -> KNNPatternsBundle:
        """Orchestrate K1 through K6 on Version A in original units."""
        if eval_row_idx_test is None:
            eval_idx = np.arange(len(orig_test), dtype=np.int64)
        else:
            eval_idx = np.asarray(eval_row_idx_test, dtype=np.int64)

        orig_eval_test = orig_test.iloc[eval_idx].reset_index(drop=True)
        groups_eval_test = test_blocks.groups[eval_idx]

        # Equal-alert-rate threshold matching NB-H on evaluated test rows (no test label tuning)
        nb_h_alert = float(np.mean(nb_h_test_proba >= nb_h_tau))
        knn_tau_eq, _ = compute_equal_alert_rate_cutoff(knn_test_proba, nb_h_alert)

        k1_df = self.analyze_k1_by_isco_major(
            orig_train=orig_train,
            orig_eval_test=orig_eval_test,
            groups_eval_test=groups_eval_test,
            knn_prob=knn_test_proba,
            nb_h_prob=nb_h_test_proba,
            knn_tau_eq=knn_tau_eq,
            nb_h_tau=nb_h_tau,
        )
        k2_bundle = self.neighbors_explainer.explain_six_profiles(
            train_blocks=train_blocks,
            test_blocks=test_blocks,
            orig_train=orig_train,
            orig_test=orig_test,
            model_spec=primary_spec,
            knn_test_proba=knn_test_proba,
            nb_h_test_proba=nb_h_test_proba,
            eval_row_idx_test=eval_idx,
        )
        k3_dec, k3_prof, k3_isco = self.analyze_k3_risk_deciles(
            orig_eval_test=orig_eval_test,
            knn_prob=knn_test_proba,
            nb_h_prob=nb_h_test_proba,
        )
        k4_sum, k4_ct, k4_dis_isco, k4_dis_prof = self.analyze_k4_agreement_with_nb_h(
            orig_train=orig_train,
            orig_eval_test=orig_eval_test,
            knn_prob=knn_test_proba,
            nb_h_prob=nb_h_test_proba,
            knn_tau_eq=knn_tau_eq,
            nb_h_tau=nb_h_tau,
        )
        k5_prof, k5_sub = self.analyze_k5_error_analysis(
            orig_train=orig_train,
            orig_eval_test=orig_eval_test,
            knn_prob=knn_test_proba,
            knn_tau_oof=knn_tau_oof,
        )
        k6_jb, k6_yr, k6_slp = self.analyze_k6_career_position_and_period(
            orig_train=orig_train,
            orig_eval_test=orig_eval_test,
            knn_prob=knn_test_proba,
            nb_h_prob=nb_h_test_proba,
        )

        return KNNPatternsBundle(
            primary_knn_model_id=primary_spec.model_id,
            k1_isco_performance_table=k1_df,
            k2_case_explanations=k2_bundle,
            k3_deciles_table=k3_dec,
            k3_top_vs_bottom_profile_table=k3_prof,
            k3_isco_composition_table=k3_isco,
            k4_agreement_summary=k4_sum,
            k4_crosstab_table=k4_ct,
            k4_disagreement_by_isco_table=k4_dis_isco,
            k4_disagreement_profiles_table=k4_dis_prof,
            k5_error_profiles_table=k5_prof,
            k5_error_subgroups_table=k5_sub,
            k6_job_order_table=k6_jb,
            k6_start_year_table=k6_yr,
            k6_slope_summary_table=k6_slp,
        )
