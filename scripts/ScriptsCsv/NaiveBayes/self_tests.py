"""Unit tests for revision helpers (paired bootstrap, equal alert rate, and Tukey winsorization)."""

from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd
from scipy import sparse

from .config import ALL_DENSE_CLEAN_FEATURES, BINARY_DENSE_FEATURES, GAUSSIAN_HYBRID_FEATURES
from .evaluation import (
    compute_equal_alert_rate_cutoff,
    paired_bootstrap_person_diffs,
    select_oof_threshold_from_proba,
)
from .feature_blocks import NaiveBayesPartitionBlocks
from .outlier_diagnostics import build_version_b_bounds_table, winsorize_continuous_blocks_in_ram


def run_revision_self_tests(random_state: int = 42) -> Dict[str, object]:
    """Run unit tests for paired bootstrap, equal-alert-rate cutoff, OOF sweep, and E2 winsorization."""
    rng = np.random.default_rng(random_state)
    n_persons = 150
    rows_per_person = rng.integers(2, 6, size=n_persons)
    groups = np.repeat([f"P{i:04d}" for i in range(n_persons)], rows_per_person)
    n = len(groups)

    latent = rng.normal(0.0, 1.0, size=n)
    y = (rng.uniform(size=n) < (1.0 / (1.0 + np.exp(-latent + 0.8)))).astype(np.int8)
    prob_strong = 1.0 / (1.0 + np.exp(-(1.2 * latent - 0.8 + rng.normal(0.0, 0.25, size=n))))
    prob_weak = 1.0 / (1.0 + np.exp(-(0.2 * latent - 0.8 + rng.normal(0.0, 0.7, size=n))))

    # 1. Paired bootstrap: identical models must give exact 0 difference and 0-width CI
    res_same = paired_bootstrap_person_diffs(
        y_true=y,
        prob_a=prob_strong,
        prob_b=prob_strong,
        groups=groups,
        threshold_a=0.35,
        threshold_b=0.35,
        n_resamples=60,
        random_state=random_state,
    )
    assert abs(float(res_same["delta_pr_auc"])) < 1e-12, "Identical models must have zero delta PR-AUC."
    assert abs(float(res_same["delta_roc_auc"])) < 1e-12, "Identical models must have zero delta ROC-AUC."
    assert not bool(res_same["pr_auc_excluye_cero"]), "Identical models CI must include 0."

    # 2. Paired bootstrap: strong model must strictly beat weak model with CI > 0 and be reproducible
    res_diff_1 = paired_bootstrap_person_diffs(
        y_true=y,
        prob_a=prob_strong,
        prob_b=prob_weak,
        groups=groups,
        threshold_a=0.35,
        threshold_b=0.35,
        n_resamples=80,
        random_state=random_state,
    )
    res_diff_2 = paired_bootstrap_person_diffs(
        y_true=y,
        prob_a=prob_strong,
        prob_b=prob_weak,
        groups=groups,
        threshold_a=0.35,
        threshold_b=0.35,
        n_resamples=80,
        random_state=random_state,
    )
    assert float(res_diff_1["delta_pr_auc_ci_low"]) > 0.0, "Strong model should beat weak model in paired CI."
    assert float(res_diff_1["delta_roc_auc_ci_low"]) > 0.0, "Strong model should beat weak model in ROC CI."
    assert res_diff_1 == res_diff_2, "Paired bootstrap must be strictly deterministic with fixed seed."

    # 3. Equal-alert-rate cutoff must reproduce target rate on continuous scores
    target_rate = 0.40
    cutoff, actual_rate = compute_equal_alert_rate_cutoff(prob_strong, target_rate)
    assert abs(actual_rate - target_rate) <= (2.0 / float(n)), (
        f"Equal-alert-rate cutoff mismatch: expected {target_rate}, got {actual_rate}"
    )

    # 4. OOF threshold selection returns valid threshold inside [0.02, 0.98]
    tau_oof, curve_df = select_oof_threshold_from_proba(y, prob_strong)
    assert 0.02 <= tau_oof <= 0.98 and len(curve_df) == 193, "Invalid OOF threshold sweep output."

    # 5. In-RAM Tukey winsorization fits fences strictly on train and clips train/test without mutating inputs
    n_tr, n_te = 200, 80
    dense_tr_dict = {c: rng.normal(0.0, 1.0, size=n_tr).astype(np.float32) for c in ALL_DENSE_CLEAN_FEATURES}
    dense_te_dict = {c: rng.normal(0.0, 1.0, size=n_te).astype(np.float32) for c in ALL_DENSE_CLEAN_FEATURES}
    # Inject extreme values in dur_q_rob in train and test
    dense_tr_dict["dur_q_rob"][0] = 500.0
    dense_te_dict["dur_q_rob"][0] = 900.0
    for bcol in BINARY_DENSE_FEATURES:
        dense_tr_dict[bcol] = rng.integers(0, 2, size=n_tr).astype(np.float32)
        dense_te_dict[bcol] = rng.integers(0, 2, size=n_te).astype(np.float32)

    df_tr = pd.DataFrame(dense_tr_dict)
    df_te = pd.DataFrame(dense_te_dict)
    X_b_tr = sparse.csr_matrix(df_tr[list(BINARY_DENSE_FEATURES)].to_numpy(dtype=np.float32))
    X_b_te = sparse.csr_matrix(df_te[list(BINARY_DENSE_FEATURES)].to_numpy(dtype=np.float32))
    X_g10_tr = sparse.csr_matrix(df_tr[list(GAUSSIAN_HYBRID_FEATURES)].to_numpy(dtype=np.float32))
    X_g10_te = sparse.csr_matrix(df_te[list(GAUSSIAN_HYBRID_FEATURES)].to_numpy(dtype=np.float32))

    tr_blk = NaiveBayesPartitionBlocks(
        split_name="train",
        dense_clean_df=df_tr,
        X_nb_g=df_tr.to_numpy(dtype=np.float32, copy=True),
        X_nb_b=X_b_tr,
        X_nb_h=sparse.hstack([X_g10_tr, X_b_tr], format="csr"),
        nb_g_feature_names=ALL_DENSE_CLEAN_FEATURES,
        nb_b_feature_names=BINARY_DENSE_FEATURES,
        nb_h_feature_names=GAUSSIAN_HYBRID_FEATURES + BINARY_DENSE_FEATURES,
        continuous_idx=tuple(range(len(GAUSSIAN_HYBRID_FEATURES))),
        binary_idx=tuple(range(len(GAUSSIAN_HYBRID_FEATURES), len(GAUSSIAN_HYBRID_FEATURES) + len(BINARY_DENSE_FEATURES))),
        y=rng.integers(0, 2, size=n_tr).astype(np.int8),
        groups=np.array([f"TR{i}" for i in range(n_tr)], dtype=str),
    )
    te_blk = NaiveBayesPartitionBlocks(
        split_name="test",
        dense_clean_df=df_te,
        X_nb_g=df_te.to_numpy(dtype=np.float32, copy=True),
        X_nb_b=X_b_te,
        X_nb_h=sparse.hstack([X_g10_te, X_b_te], format="csr"),
        nb_g_feature_names=ALL_DENSE_CLEAN_FEATURES,
        nb_b_feature_names=BINARY_DENSE_FEATURES,
        nb_h_feature_names=GAUSSIAN_HYBRID_FEATURES + BINARY_DENSE_FEATURES,
        continuous_idx=tuple(range(len(GAUSSIAN_HYBRID_FEATURES))),
        binary_idx=tuple(range(len(GAUSSIAN_HYBRID_FEATURES), len(GAUSSIAN_HYBRID_FEATURES) + len(BINARY_DENSE_FEATURES))),
        y=rng.integers(0, 2, size=n_te).astype(np.int8),
        groups=np.array([f"TE{i}" for i in range(n_te)], dtype=str),
    )

    Xg_tr_w, Xg_te_w, Xh_tr_w, Xh_te_w, fences_df = winsorize_continuous_blocks_in_ram(tr_blk, te_blk)
    dur_idx = list(ALL_DENSE_CLEAN_FEATURES).index("dur_q_rob")
    dur_hi = float(fences_df.loc[fences_df["variable_rob"] == "dur_q_rob", "valla_sup_tukey_train_rob"].iloc[0])
    assert tr_blk.X_nb_g[0, dur_idx] == 500.0, "Winsorization must not mutate original train matrix."
    assert Xg_tr_w[0, dur_idx] <= dur_hi + 1e-3, "Train extreme was not clipped to train Tukey fence."
    assert Xg_te_w[0, dur_idx] <= dur_hi + 1e-3, "Test extreme was not clipped to train Tukey fence."
    assert float(Xh_te_w[0, dur_idx]) <= dur_hi + 1e-3, "NB-H test extreme was not clipped."

    # 6. Dynamic Version B bounds table contains exactly 4 clipped columns from IQR_WINSOR_BOUNDS_INFO
    vb_df = build_version_b_bounds_table()
    n_clipped_b = int((vb_df["recortada_en_version_B"].str.startswith("Sí")).sum())
    assert n_clipped_b == 4, f"Expected 4 clipped columns in Version B table, found {n_clipped_b}."

    return {
        "test_paired_bootstrap_zero_diff": True,
        "test_paired_bootstrap_deterministic_and_positive": True,
        "test_equal_alert_rate_cutoff_err": round(abs(actual_rate - target_rate), 6),
        "test_oof_threshold_sweep": True,
        "test_winsorization_train_only_no_mutation": True,
        "test_version_b_bounds_count": n_clipped_b,
        "all_revision_tests_passed": True,
    }
