"""Unit and integration self-tests for the KNN package (Stage 1+)."""

from __future__ import annotations

from pathlib import Path
import tempfile
from typing import Dict
import warnings

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.neighbors import KNeighborsClassifier

from .chunked_predictor import ChunkedKNNPredictor
from .config import ALL_DENSE_CLEAN_FEATURES, ISCO_MAJOR_DUMMY_COLS
from .evaluation import PersonSubsampler, proba_from_kneighbors
from .feature_blocks import (
    AuditedStandardBinaryScaler,
    KNNPartitionBlocks,
    TukeyWinsorizedStandardScaler,
)
from .models import ManualKNNExplainer, build_knn_d, build_knn_g, build_knn_w
from .revision_checks import ExactOccupationPrefilterKNN, tie_aware_equal_alert_weights


def _make_synthetic_blocks(
    n_train: int = 300,
    n_test: int = 60,
    n_ohe: int = 12,
    random_state: int = 42,
) -> tuple[KNNPartitionBlocks, KNNPartitionBlocks, pd.DataFrame, pd.DataFrame]:
    """Create deterministic synthetic train/test KNNPartitionBlocks and original-unit frames."""
    rng = np.random.default_rng(random_state)

    def _build_df(n: int) -> pd.DataFrame:
        data = {
            "start_ord_rob": rng.normal(0.0, 1.0, size=n),
            "end_ord_rob": rng.normal(0.0, 1.0, size=n),
            "dur_q_rob": rng.exponential(1.2, size=n),
            "n_skills_essential_rob": rng.normal(0.2, 1.0, size=n),
            "n_skills_knowledge_rob": rng.normal(0.1, 0.9, size=n),
            "n_skills_sin_tipo_rob": np.zeros(n, dtype=np.float64),  # near-constant (< 1%)
            "job_order_rob": rng.normal(0.3, 0.9, size=n),
            "univ_ord_mm": rng.choice([0.0, 0.25, 0.5, 0.75, 1.0], size=n),
            "es_vigente": (rng.uniform(size=n) < 0.08).astype(np.uint8),
            "dur_q_bin": rng.integers(0, 3, size=n, dtype=np.uint8),
            "n_skills_essential_bin": rng.integers(0, 4, size=n, dtype=np.uint8),
            "tiene_skills": np.ones(n, dtype=np.uint8),  # constant
            "tiene_knowledge": (rng.uniform(size=n) < 0.88).astype(np.uint8),
            "tiene_sin_tipo": np.zeros(n, dtype=np.uint8),  # constant
        }
        return pd.DataFrame(data)[list(ALL_DENSE_CLEAN_FEATURES)]

    df_tr = _build_df(n_train)
    df_te = _build_df(n_test)

    # Inject a deliberate extreme outlier in test only to verify scaler does not leak test stats
    df_te.loc[0, "dur_q_rob"] = 999.0

    scaler = AuditedStandardBinaryScaler(near_constant_threshold_pct=1.0)
    X_tr_sc = scaler.fit_transform(df_tr)
    X_te_sc = scaler.transform(df_te)

    isco_tr_idx = rng.integers(0, 10, size=n_train)
    isco_te_idx = rng.integers(0, 10, size=n_test)
    X_tr_isco = np.eye(10, dtype=np.float32)[isco_tr_idx]
    X_te_isco = np.eye(10, dtype=np.float32)[isco_te_idx]

    ohe_tr_idx = rng.integers(0, n_ohe, size=n_train)
    ohe_te_idx = rng.integers(0, n_ohe, size=n_test)
    ohe_tr = sparse.csr_matrix(
        (np.ones(n_train, dtype=np.float32), (np.arange(n_train), ohe_tr_idx)),
        shape=(n_train, n_ohe),
    )
    ohe_te = sparse.csr_matrix(
        (np.ones(n_test, dtype=np.float32), (np.arange(n_test), ohe_te_idx)),
        shape=(n_test, n_ohe),
    )

    y_tr = (rng.uniform(size=n_train) < 0.30).astype(np.int8)
    y_te = (rng.uniform(size=n_test) < 0.30).astype(np.int8)
    g_tr = np.array([f"tr_p_{i // 3}" for i in range(n_train)], dtype=str)
    g_te = np.array([f"te_p_{i // 3}" for i in range(n_test)], dtype=str)

    tr_blocks = KNNPartitionBlocks(
        split_name="train",
        dense_clean_df=df_tr,
        X_dense_scaled=X_tr_sc,
        X_dense_raw_active=df_tr[list(scaler.active_columns_)].to_numpy(dtype=np.float32),
        X_isco_major=X_tr_isco,
        ohe_sparse=ohe_tr,
        active_dense_features=scaler.active_columns_,
        dropped_dense_features=scaler.dropped_columns_,
        isco_feature_names=ISCO_MAJOR_DUMMY_COLS,
        ohe_feature_names=tuple(f"occupation_code_{i}" for i in range(n_ohe)),
        y=y_tr,
        groups=g_tr,
    )
    te_blocks = KNNPartitionBlocks(
        split_name="test",
        dense_clean_df=df_te,
        X_dense_scaled=X_te_sc,
        X_dense_raw_active=df_te[list(scaler.active_columns_)].to_numpy(dtype=np.float32),
        X_isco_major=X_te_isco,
        ohe_sparse=ohe_te,
        active_dense_features=scaler.active_columns_,
        dropped_dense_features=scaler.dropped_columns_,
        isco_feature_names=ISCO_MAJOR_DUMMY_COLS,
        ohe_feature_names=tuple(f"occupation_code_{i}" for i in range(n_ohe)),
        y=y_te,
        groups=g_te,
    )

    def _make_orig(n: int, isco_idx: np.ndarray, y: np.ndarray, g: np.ndarray) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "resume_id": g,
                "reincide": y,
                "occupation_code": [f"occ_{i % n_ohe}" for i in range(n)],
                "occupation_label": [f"Oficio sintético {i % n_ohe}" for i in range(n)],
                "isco_major": [str(d) for d in isco_idx],
                "isco_major_label_es": [f"{d} · Grupo {d}" for d in isco_idx],
                "job_order": rng.integers(1, 8, size=n, dtype=np.int32),
                "dur_q": rng.integers(1, 20, size=n).astype(np.float32),
                "start_year": rng.integers(2005, 2024, size=n).astype(np.float32),
                "es_vigente": (rng.uniform(size=n) < 0.08).astype(np.int8),
                "university_level": rng.choice(["No reportado", "Bachelor", "Master"], size=n),
                "n_skills_essential": rng.integers(5, 40, size=n).astype(np.float32),
            }
        )

    orig_tr = _make_orig(n_train, isco_tr_idx, y_tr, g_tr)
    orig_te = _make_orig(n_test, isco_te_idx, y_te, g_te)
    return tr_blocks, te_blocks, orig_tr, orig_te


def run_stage1_self_tests(random_state: int = 42) -> Dict[str, object]:
    """Run deterministic Stage 1 unit tests for scalers, model geometry, sparse warning, and manual KNN."""
    tr_blocks, te_blocks, orig_tr, orig_te = _make_synthetic_blocks(random_state=random_state)

    # Test 1: Near-constant drop + train-only scaling + binary {0, 1} preservation
    expected_dropped = {"tiene_skills", "tiene_sin_tipo", "n_skills_sin_tipo_rob"}
    assert set(tr_blocks.dropped_dense_features) == expected_dropped, (
        f"Unexpected dropped features: {tr_blocks.dropped_dense_features}"
    )
    assert len(tr_blocks.active_dense_features) == 11, (
        f"Expected 11 active features, got {len(tr_blocks.active_dense_features)}"
    )
    for bin_col in ("es_vigente", "tiene_knowledge"):
        b_idx = tr_blocks.active_dense_features.index(bin_col)
        uniq = set(np.unique(tr_blocks.X_dense_scaled[:, b_idx]).tolist())
        assert uniq.issubset({0.0, 1.0}), f"Binary column {bin_col} was altered: {uniq}"

    # Verify continuous/ordinal columns have train std ~ 1.0
    for col in tr_blocks.active_dense_features:
        if col not in ("es_vigente", "tiene_knowledge"):
            idx = tr_blocks.active_dense_features.index(col)
            std_tr = float(np.std(tr_blocks.X_dense_scaled[:, idx]))
            assert abs(std_tr - 1.0) < 1e-4, f"Expected unit std on train for {col}, got {std_tr}"

    # Verify TukeyWinsorizedStandardScaler clips test extremes using train fences only
    tw_scaler = TukeyWinsorizedStandardScaler(near_constant_threshold_pct=1.0)
    tw_scaler.fit(tr_blocks.dense_clean_df)
    X_te_tw = tw_scaler.transform(te_blocks.dense_clean_df)
    dur_idx = tw_scaler.active_columns_.index("dur_q_rob")
    assert float(X_te_tw[0, dur_idx]) < 10.0, (
        "TukeyWinsorizedStandardScaler failed to clip extreme test value using train fences!"
    )

    # Test 2: Block weight w_g=0 (KNN-G) and w=0 (KNN-W) reproduce KNN-D exactly
    knn_d = build_knn_d(n_neighbors=11, weights="uniform", metric="euclidean", algorithm="kd_tree", n_jobs=1)
    knn_d.fit(tr_blocks.build_knn_d_matrix(), tr_blocks.y)
    p_d = knn_d.predict_proba(te_blocks.build_knn_d_matrix())[:, 1]

    knn_g0 = build_knn_g(n_neighbors=11, weights="uniform", metric="euclidean", algorithm="ball_tree", w_g=0.0, n_jobs=1)
    knn_g0.fit(tr_blocks.build_knn_g_matrix(w_g=0.0), tr_blocks.y)
    p_g0 = knn_g0.predict_proba(te_blocks.build_knn_g_matrix(w_g=0.0))[:, 1]
    diff_g0 = float(np.max(np.abs(p_d - p_g0)))
    assert diff_g0 < 1e-12, f"KNN-G with w_g=0 differs from KNN-D by {diff_g0}"

    knn_w0 = build_knn_w(n_neighbors=11, weights="uniform", metric="euclidean", w=0.0, n_jobs=1)
    knn_w0.fit(tr_blocks.build_knn_w_matrix(w=0.0), tr_blocks.y)
    p_w0 = knn_w0.predict_proba(te_blocks.build_knn_w_matrix(w=0.0))[:, 1]
    diff_w0 = float(np.max(np.abs(p_d - p_w0)))
    assert diff_w0 < 1e-12, f"KNN-W with w=0 differs from KNN-D by {diff_w0}"

    # Test 3: Verify sparse kd_tree fallback warning in sklearn (Section 2 constraint)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        probe_sparse = KNeighborsClassifier(n_neighbors=5, algorithm="kd_tree", metric="euclidean")
        probe_sparse.fit(tr_blocks.build_knn_w_matrix(w=1.0), tr_blocks.y)
        sparse_fallback_warned = any(issubclass(w.category, UserWarning) for w in caught)
    assert sparse_fallback_warned, "Expected UserWarning when fitting kd_tree on sparse CSR input."

    # Test 4: ManualKNNExplainer exact agreement vs sklearn
    manual_demo = ManualKNNExplainer(k_neighbors=5).run_demo(
        train_blocks=tr_blocks,
        test_blocks=te_blocks,
        orig_train=orig_tr,
        orig_test=orig_te,
    )
    assert manual_demo.max_abs_diff_distances < 1e-9
    assert manual_demo.max_abs_diff_proba_uniform < 1e-12
    assert manual_demo.max_abs_diff_proba_distance < 1e-12

    return {
        "test_1_scaler_train_only_and_drop_ok": True,
        "test_2_knn_g_w0_max_diff_vs_knn_d": diff_g0,
        "test_3_knn_w_w0_max_diff_vs_knn_d": diff_w0,
        "test_4_sparse_kd_tree_fallback_warned": sparse_fallback_warned,
        "test_5_manual_knn_max_dist_diff": manual_demo.max_abs_diff_distances,
        "test_5_manual_knn_max_prob_unif_diff": manual_demo.max_abs_diff_proba_uniform,
        "test_5_manual_knn_max_prob_dist_diff": manual_demo.max_abs_diff_proba_distance,
        "all_stage1_passed": True,
    }


def run_stage2_self_tests(random_state: int = 42) -> Dict[str, object]:
    """Run deterministic unit tests for proba_from_kneighbors, PersonSubsampler, and ChunkedKNNPredictor."""
    tr_blocks, te_blocks, _, _ = _make_synthetic_blocks(
        n_train=240, n_test=65, n_ohe=10, random_state=random_state
    )
    X_tr = tr_blocks.build_knn_d_matrix().astype(np.float64)
    X_te = te_blocks.build_knn_d_matrix().astype(np.float64)
    # Inject an exact duplicate of train row 0 into test row 0 to test zero-distance tie handling
    X_te[0] = X_tr[0]
    y_tr = tr_blocks.y

    k_max = 31
    knn_max = KNeighborsClassifier(n_neighbors=k_max, algorithm="kd_tree", metric="euclidean", n_jobs=1)
    knn_max.fit(X_tr, y_tr)
    dists, idxs = knn_max.kneighbors(X_te, n_neighbors=k_max, return_distance=True)

    max_err = 0.0
    for k in (5, 11, 31):
        for wt in ("uniform", "distance"):
            direct = KNeighborsClassifier(n_neighbors=k, weights=wt, algorithm="kd_tree", metric="euclidean", n_jobs=1)
            direct.fit(X_tr, y_tr)
            p_direct = direct.predict_proba(X_te)[:, 1]
            p_fast = proba_from_kneighbors(dists, idxs, y_tr, k=k, weights=wt)
            err = float(np.max(np.abs(p_direct - p_fast)))
            max_err = max(max_err, err)
            assert err < 1e-12, f"proba_from_kneighbors mismatch for k={k}, weights={wt}: {err}"

    # Test PersonSubsampler completeness and nesting
    subsampler = PersonSubsampler(random_state=random_state)
    nested = subsampler.sample_persons_nested(tr_blocks.groups, y_tr, fractions=(0.25, 0.50))
    idx_25, _ = nested[0.25]
    idx_50, _ = nested[0.50]
    p25 = set(tr_blocks.groups[idx_25].tolist())
    p50 = set(tr_blocks.groups[idx_50].tolist())
    assert p25.issubset(p50), "Nested person subsamples must satisfy p25 subset of p50."
    # Every sampled person must keep ALL its rows
    assert len(idx_25) == int(np.isin(tr_blocks.groups, list(p25)).sum())

    # Test ChunkedKNNPredictor exactness + resume after interruption + full cache hit
    with tempfile.TemporaryDirectory() as tmpdir:
        predictor = ChunkedKNNPredictor(cache_root=Path(tmpdir), chunk_size=17)
        est = KNeighborsClassifier(n_neighbors=11, weights="distance", algorithm="kd_tree", n_jobs=1)
        est.fit(X_tr, y_tr)
        p_ref = est.predict_proba(X_te)[:, 1]
        meta = {"test": "chunked", "k": 11}

        res1 = predictor.predict_proba_resumable(
            fitted_knn=est, X_query=X_te, run_tag="unit", metadata=meta, verbose=False
        )
        diff_chunk1 = float(np.max(np.abs(res1.proba_pos - p_ref)))
        assert diff_chunk1 < 1e-12, f"Chunked predictor mismatch: {diff_chunk1}"
        assert res1.chunks_computed_now == res1.n_chunks

        # Simulate interruption by deleting last 2 chunks and resuming
        for c_i in range(res1.n_chunks - 2, res1.n_chunks):
            (res1.cache_dir / f"chunk_{c_i:05d}.npy").unlink()
        res2 = predictor.predict_proba_resumable(
            fitted_knn=est, X_query=X_te, run_tag="unit", metadata=meta, verbose=False
        )
        assert res2.chunks_loaded_from_cache == res1.n_chunks - 2
        assert res2.chunks_computed_now == 2
        assert float(np.max(np.abs(res2.proba_pos - p_ref))) < 1e-12

        # Verify full-cache load works even when fitted_knn=None
        res3 = predictor.predict_proba_resumable(
            fitted_knn=None, X_query=X_te, run_tag="unit", metadata=meta, verbose=False
        )
        assert res3.used_full_cache
        assert float(np.max(np.abs(res3.proba_pos - p_ref))) < 1e-12

    return {
        "test_6_proba_from_kneighbors_max_err": max_err,
        "test_7_person_subsampler_nested_complete": True,
        "test_8_chunked_predictor_exact_and_resume_ok": True,
        "all_stage2_passed": True,
    }


def run_revision_self_tests(random_state: int = 42) -> Dict[str, object]:
    """Run deterministic unit tests for ExactOccupationPrefilterKNN (including drop='first') and tie-aware alerts."""
    tr_blocks, te_blocks, orig_tr, orig_te = _make_synthetic_blocks(
        n_train=360, n_test=60, n_ohe=5, random_state=random_state
    )
    # Align orig occupation_code strictly with ohe_sparse AND simulate drop='first' (occ 0 -> zero OHE vector!)
    tr_codes = np.asarray(tr_blocks.ohe_sparse.argmax(axis=1)).ravel()
    te_codes = np.asarray(te_blocks.ohe_sparse.argmax(axis=1)).ravel()
    orig_tr = orig_tr.copy()
    orig_te = orig_te.copy()
    orig_tr["occupation_code"] = [f"occ_{c}" for c in tr_codes]
    orig_te["occupation_code"] = [f"occ_{c}" for c in te_codes]

    # Drop column 0 to replicate OneHotEncoder(drop='first') -> occ_0 has row sum == 0
    ohe_tr_dfirst = tr_blocks.ohe_sparse[:, 1:].tocsr()
    ohe_te_dfirst = te_blocks.ohe_sparse[:, 1:].tocsr()
    tr_b = KNNPartitionBlocks(
        **{**tr_blocks.__dict__, "ohe_sparse": ohe_tr_dfirst, "ohe_feature_names": tr_blocks.ohe_feature_names[1:]}
    )
    te_b = KNNPartitionBlocks(
        **{**te_blocks.__dict__, "ohe_sparse": ohe_te_dfirst, "ohe_feature_names": te_blocks.ohe_feature_names[1:]}
    )

    k_test = 11
    w_test = 8.0
    exact_est = build_knn_w(n_neighbors=k_test, weights="uniform", metric="euclidean", w=w_test, n_jobs=1)
    exact_est.fit(tr_b.build_knn_w_matrix(w=w_test), tr_b.y)
    p_exact = exact_est.predict_proba(te_b.build_knn_w_matrix(w=w_test))[:, 1]

    prefilter = ExactOccupationPrefilterKNN(n_neighbors=k_test, block_weight=w_test, n_jobs=1)
    prefilter.fit(tr_b, orig_tr)
    pf_res = prefilter.predict_with_diagnostics(te_b, orig_te, np.arange(len(te_b.y)))
    max_diff_pf = float(np.max(np.abs(pf_res.proba_certified_fallback - p_exact)))
    assert max_diff_pf < 1e-12, f"ExactOccupationPrefilterKNN mismatch vs sklearn: {max_diff_pf}"
    assert bool(pf_res.certified_sqrt2w_mask.any()), "Expected some queries certified by sqrt(2)*w bound."
    assert bool(pf_res.fallback_zero_ohe_mask.any()), "Expected zero-OHE drop='first' queries handled via fallback."

    # Test tie_aware_equal_alert_weights exact alert rate on discrete 1/101 scores
    rng = np.random.default_rng(random_state)
    disc_probs = rng.integers(0, 102, size=5000) / 101.0
    target_r = 0.5178
    weights, _, raw_r, matched_r, lam = tie_aware_equal_alert_weights(disc_probs, target_r)
    assert abs(matched_r - target_r) < 1e-6, f"Tie-aware matched rate {matched_r} != target {target_r}"
    assert 0.0 <= lam <= 1.0 and raw_r >= target_r - 1e-6

    return {
        "test_9_exact_prefilter_drop_first_max_diff": max_diff_pf,
        "test_10_tie_aware_equal_alert_exact_ok": True,
        "all_revision_tests_passed": True,
    }


def run_all_knn_unit_tests(random_state: int = 42) -> Dict[str, object]:
    """Run all deterministic KNN package unit tests."""
    r1 = run_stage1_self_tests(random_state=random_state)
    r2 = run_stage2_self_tests(random_state=random_state)
    r3 = run_revision_self_tests(random_state=random_state)
    return {
        **r1,
        **r2,
        **r3,
        "all_passed": bool(
            r1["all_stage1_passed"] and r2["all_stage2_passed"] and r3["all_revision_tests_passed"]
        ),
    }


if __name__ == "__main__":
    results = run_all_knn_unit_tests()
    for key, val in results.items():
        print(f"{key}: {val}")
