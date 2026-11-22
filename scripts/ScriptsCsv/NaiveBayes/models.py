"""Naive Bayes model factories, HybridNaiveBayes estimator, and mandatory unit tests."""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

import numpy as np
from scipy import sparse
from scipy.special import logsumexp
from sklearn.base import BaseEstimator, ClassifierMixin, clone
from sklearn.naive_bayes import BernoulliNB, GaussianNB
from sklearn.utils.validation import check_is_fitted


def resolve_priors(prior_mode: str | Sequence[float] | None) -> List[float] | None:
    """Map prior mode identifier ('empirical' or 'balanced') to sklearn prior sequence."""
    if prior_mode is None or prior_mode == "empirical":
        return None
    if prior_mode == "balanced":
        return [0.5, 0.5]
    if isinstance(prior_mode, (list, tuple, np.ndarray)):
        return [float(v) for v in prior_mode]
    raise ValueError(f"Unsupported prior_mode: {prior_mode}")


def build_gaussian_nb(
    var_smoothing: float = 1e-9,
    priors: Sequence[float] | str | None = None,
) -> GaussianNB:
    """Instantiate a GaussianNB classifier with standardized prior handling."""
    return GaussianNB(var_smoothing=float(var_smoothing), priors=resolve_priors(priors))


def build_bernoulli_nb(
    alpha: float = 1.0,
    priors: Sequence[float] | str | None = None,
    binarize: float | None = 0.0,
    force_alpha: bool = True,
) -> BernoulliNB:
    """Instantiate a BernoulliNB classifier with standardized prior handling."""
    return BernoulliNB(
        alpha=float(alpha),
        force_alpha=force_alpha,
        binarize=binarize,
        fit_prior=True,
        class_prior=resolve_priors(priors),
    )


def compute_gaussian_log_odds_contributions(
    gnb: GaussianNB,
    X_dense: np.ndarray,
) -> Tuple[float, np.ndarray]:
    """Return prior log-odds and per-feature additive log-odds contributions for GaussianNB."""
    check_is_fitted(gnb, attributes=["theta_", "var_", "class_prior_"])
    X_arr = np.asarray(X_dense, dtype=np.float64)
    prior_log_odds = float(np.log(gnb.class_prior_[1]) - np.log(gnb.class_prior_[0]))

    theta0 = gnb.theta_[0]
    theta1 = gnb.theta_[1]
    var0 = gnb.var_[0]
    var1 = gnb.var_[1]

    # log P(x_j | c) = -0.5 * log(2 * pi * var_c) - 0.5 * (x_j - theta_c)^2 / var_c
    const_diff = -0.5 * np.log(var1 / var0)  # shape (n_features,)
    quad1 = -0.5 * ((X_arr - theta1) ** 2) / var1
    quad0 = -0.5 * ((X_arr - theta0) ** 2) / var0
    contributions = const_diff + quad1 - quad0
    return prior_log_odds, contributions


def compute_bernoulli_log_odds_weights(
    bnb: BernoulliNB,
) -> Tuple[float, np.ndarray, np.ndarray]:
    """Return prior log-odds, baseline absence log-odds (x_j=0), and presence delta (x_j=1 vs 0)."""
    check_is_fitted(bnb, attributes=["feature_log_prob_", "class_log_prior_"])
    prior_log_odds = float(bnb.class_log_prior_[1] - bnb.class_log_prior_[0])
    flp0 = bnb.feature_log_prob_[0]
    flp1 = bnb.feature_log_prob_[1]
    neg0 = np.log1p(-np.exp(flp0))
    neg1 = np.log1p(-np.exp(flp1))

    absence_log_ratio = neg1 - neg0  # Contribution when x_j == 0
    presence_log_ratio = flp1 - flp0  # Contribution when x_j == 1
    delta_weight = presence_log_ratio - absence_log_ratio
    return prior_log_odds, absence_log_ratio, delta_weight


def compute_bernoulli_log_odds_contributions(
    bnb: BernoulliNB,
    X_bin: sparse.spmatrix | np.ndarray,
    split_dense_and_ohe_at: int | None = None,
) -> Tuple[float, np.ndarray]:
    """Return prior log-odds and per-feature (or block-aggregated OHE) log-odds contributions."""
    prior_log_odds, absence_lr, delta_w = compute_bernoulli_log_odds_weights(bnb)
    n_rows = X_bin.shape[0]

    if split_dense_and_ohe_at is not None and split_dense_and_ohe_at < X_bin.shape[1]:
        k = int(split_dense_and_ohe_at)
        X_first = X_bin[:, :k].toarray() if sparse.issparse(X_bin) else np.asarray(X_bin[:, :k], dtype=np.float64)
        X_First_f = np.asarray(X_first, dtype=np.float64)
        if bnb.binarize is not None:
            X_First_f = (X_First_f > bnb.binarize).astype(np.float64)
        contrib_first = absence_lr[:k] + X_First_f * delta_w[:k]

        X_rest = X_bin[:, k:]
        if bnb.binarize is not None:
            if sparse.issparse(X_rest):
                X_rest = X_rest.copy()
                X_rest.data = (X_rest.data > bnb.binarize).astype(np.float64)
            else:
                X_rest = (np.asarray(X_rest) > bnb.binarize).astype(np.float64)
        rest_base = float(np.sum(absence_lr[k:]))
        rest_dot = np.asarray(X_rest.dot(delta_w[k:])).ravel()
        contrib_rest = (rest_base + rest_dot).reshape(n_rows, 1)
        return prior_log_odds, np.hstack([contrib_first, contrib_rest])

    X_dense = X_bin.toarray() if sparse.issparse(X_bin) else np.asarray(X_bin, dtype=np.float64)
    X_dense = np.asarray(X_dense, dtype=np.float64)
    if bnb.binarize is not None:
        X_dense = (X_dense > bnb.binarize).astype(np.float64)
    contributions = absence_lr + X_dense * delta_w
    return prior_log_odds, contributions


class HybridNaiveBayes(BaseEstimator, ClassifierMixin):
    """Mixed Naive Bayes combining GaussianNB on numeric/ordinal columns and BernoulliNB on binary columns.

    By conditional independence, the unnormalized log-posterior of class c is:
        log P(c | x) = lp_G[c] + lp_B[c] - log pi_c
    where lp_G and lp_B are the log-posteriors of the Gaussian and Bernoulli submodels
    and pi_c is the class prior (subtracted once so it is not double-counted).
    Rows are then normalized with a numerically stable softmax (logsumexp).
    """

    def __init__(
        self,
        continuous_idx: Sequence[int] = (),
        binary_idx: Sequence[int] = (),
        var_smoothing: float = 1e-9,
        alpha: float = 1.0,
        priors: Sequence[float] | str | None = None,
        binarize: float | None = 0.0,
        force_alpha: bool = True,
    ) -> None:
        self.continuous_idx = continuous_idx
        self.binary_idx = binary_idx
        self.var_smoothing = var_smoothing
        self.alpha = alpha
        self.priors = priors
        self.binarize = binarize
        self.force_alpha = force_alpha

    @staticmethod
    def _extract_continuous_dense(X: sparse.spmatrix | np.ndarray, idx: List[int]) -> np.ndarray:
        """Convert only the continuous column slice to a dense float64 array."""
        sliced = X[:, idx]
        if sparse.issparse(sliced):
            return sliced.toarray().astype(np.float64, copy=False)
        return np.asarray(sliced, dtype=np.float64)

    @staticmethod
    def _extract_binary_slice(
        X: sparse.spmatrix | np.ndarray, idx: List[int]
    ) -> sparse.csr_matrix | np.ndarray:
        """Slice binary columns while preserving CSR sparsity when X is sparse."""
        sliced = X[:, idx]
        if sparse.issparse(sliced):
            return sliced.tocsr()
        return np.asarray(sliced, dtype=np.float64)

    def fit(self, X: sparse.spmatrix | np.ndarray, y: np.ndarray) -> "HybridNaiveBayes":
        """Fit GaussianNB on continuous_idx and BernoulliNB on binary_idx."""
        y_arr = np.asarray(y, dtype=np.int64).ravel()
        classes, counts = np.unique(y_arr, return_counts=True)
        if len(classes) != 2 or not np.array_equal(classes, np.array([0, 1])):
            raise ValueError(f"HybridNaiveBayes requires binary classes [0, 1], got {classes}.")

        cont_idx = [int(i) for i in self.continuous_idx]
        bin_idx = [int(i) for i in self.binary_idx]
        if not cont_idx and not bin_idx:
            raise ValueError("At least one of continuous_idx or binary_idx must be non-empty.")

        resolved_priors = resolve_priors(self.priors)
        if resolved_priors is not None:
            prior_arr = np.asarray(resolved_priors, dtype=np.float64)
            prior_arr = prior_arr / prior_arr.sum()
        else:
            prior_arr = counts.astype(np.float64) / float(len(y_arr))

        self.classes_ = classes
        self.class_count_ = counts.astype(np.float64)
        self.class_prior_ = prior_arr
        self.class_log_prior_ = np.log(prior_arr)
        self.continuous_idx_ = cont_idx
        self.binary_idx_ = bin_idx
        self.n_features_in_ = int(X.shape[1])

        if cont_idx:
            X_cont = self._extract_continuous_dense(X, cont_idx)
            self.gaussian_nb_: GaussianNB | None = GaussianNB(
                var_smoothing=float(self.var_smoothing),
                priors=prior_arr.tolist(),
            )
            self.gaussian_nb_.fit(X_cont, y_arr)
        else:
            self.gaussian_nb_ = None

        if bin_idx:
            X_bin = self._extract_binary_slice(X, bin_idx)
            self.bernoulli_nb_: BernoulliNB | None = BernoulliNB(
                alpha=float(self.alpha),
                force_alpha=self.force_alpha,
                binarize=self.binarize,
                fit_prior=True,
                class_prior=prior_arr.tolist(),
            )
            self.bernoulli_nb_.fit(X_bin, y_arr)
        else:
            self.bernoulli_nb_ = None

        return self

    def predict_log_proba(self, X: sparse.spmatrix | np.ndarray) -> np.ndarray:
        """Compute normalized class log-probabilities using lp_G + lp_B - log(pi_c)."""
        check_is_fitted(
            self,
            attributes=["classes_", "class_log_prior_", "continuous_idx_", "binary_idx_"],
        )
        lp_g: np.ndarray | None = None
        lp_b: np.ndarray | None = None

        if self.gaussian_nb_ is not None:
            X_cont = self._extract_continuous_dense(X, self.continuous_idx_)
            lp_g = self.gaussian_nb_.predict_log_proba(X_cont)

        if self.bernoulli_nb_ is not None:
            X_bin = self._extract_binary_slice(X, self.binary_idx_)
            lp_b = self.bernoulli_nb_.predict_log_proba(X_bin)

        if lp_g is not None and lp_b is not None:
            unnorm = lp_g + lp_b - self.class_log_prior_[np.newaxis, :]
        elif lp_g is not None:
            unnorm = lp_g
        elif lp_b is not None:
            unnorm = lp_b
        else:
            raise RuntimeError("Neither GaussianNB nor BernoulliNB is fitted.")

        log_norm = logsumexp(unnorm, axis=1, keepdims=True)
        return unnorm - log_norm

    def predict_proba(self, X: sparse.spmatrix | np.ndarray) -> np.ndarray:
        """Compute normalized class probabilities summing to 1 per row."""
        return np.exp(self.predict_log_proba(X))

    def predict(self, X: sparse.spmatrix | np.ndarray) -> np.ndarray:
        """Predict binary class labels using the argmax of posterior probability (threshold 0.5)."""
        log_proba = self.predict_log_proba(X)
        return self.classes_[np.argmax(log_proba, axis=1)]

    def predict_log_odds(self, X: sparse.spmatrix | np.ndarray) -> np.ndarray:
        """Return log(P(y=1|x) / P(y=0|x)) for each row."""
        lp = self.predict_log_proba(X)
        return lp[:, 1] - lp[:, 0]

    def feature_log_odds_contributions(
        self,
        X: sparse.spmatrix | np.ndarray,
        split_binary_dense_and_ohe_at: int | None = None,
    ) -> Tuple[float, np.ndarray]:
        """Return (prior_log_odds, contributions_matrix) whose sum reproduces predict_log_odds(X).

        Parameters
        ----------
        X : sparse matrix or ndarray
            Input matrix with the same column layout used during fit.
        split_binary_dense_and_ohe_at : int or None, default=None
            When None, returns one column per feature in `continuous_idx_ + binary_idx_`.
            When set to `k` (e.g., 4 for the 4 dense binary features), returns the `len(continuous_idx_)`
            Gaussian columns, the first `k` binary columns individually, and 1 aggregated column
            summing the remaining `len(binary_idx_) - k` sparse OHE columns.
        """
        check_is_fitted(
            self,
            attributes=["classes_", "class_log_prior_", "continuous_idx_", "binary_idx_"],
        )
        prior_log_odds = float(self.class_log_prior_[1] - self.class_log_prior_[0])
        pieces: List[np.ndarray] = []

        if self.gaussian_nb_ is not None:
            X_cont = self._extract_continuous_dense(X, self.continuous_idx_)
            _, cont_contrib = compute_gaussian_log_odds_contributions(self.gaussian_nb_, X_cont)
            pieces.append(cont_contrib)

        if self.bernoulli_nb_ is not None:
            X_bin = self._extract_binary_slice(X, self.binary_idx_)
            _, bin_contrib = compute_bernoulli_log_odds_contributions(
                self.bernoulli_nb_,
                X_bin,
                split_dense_and_ohe_at=split_binary_dense_and_ohe_at,
            )
            pieces.append(bin_contrib)

        if len(pieces) == 1:
            return prior_log_odds, pieces[0]
        return prior_log_odds, np.hstack(pieces)


def run_hybrid_naive_bayes_self_tests(random_state: int = 42) -> Dict[str, object]:
    """Run the 5 mandatory unit tests on HybridNaiveBayes with strict assertions."""
    rng = np.random.default_rng(random_state)
    n_samples = 400
    n_cont = 6
    n_bin = 12

    X_cont = rng.normal(loc=0.0, scale=1.5, size=(n_samples, n_cont)).astype(np.float64)
    X_bin = rng.integers(0, 2, size=(n_samples, n_bin)).astype(np.float64)
    logits = 0.4 * X_cont[:, 0] - 0.3 * X_cont[:, 1] + 0.6 * X_bin[:, 0] - 0.5 * X_bin[:, 1] - 0.4
    probs = 1.0 / (1.0 + np.exp(-logits))
    y = (rng.uniform(size=n_samples) < probs).astype(np.int8)

    X_combined_csr = sparse.csr_matrix(np.hstack([X_cont, X_bin]))
    cont_idx = list(range(n_cont))
    bin_idx = list(range(n_cont, n_cont + n_bin))

    # Test 1: With no binary columns it reproduces GaussianNB
    gnb = GaussianNB(var_smoothing=1e-8)
    gnb.fit(X_cont, y)
    hnb_only_g = HybridNaiveBayes(continuous_idx=cont_idx, binary_idx=[], var_smoothing=1e-8)
    hnb_only_g.fit(X_combined_csr, y)
    proba_gnb = gnb.predict_proba(X_cont)
    proba_hnb_g = hnb_only_g.predict_proba(X_combined_csr)
    max_diff_g = float(np.max(np.abs(proba_gnb - proba_hnb_g)))
    assert np.allclose(proba_gnb, proba_hnb_g, atol=1e-12), (
        f"Test 1 failed: HybridNaiveBayes without binary cols differs from GaussianNB by {max_diff_g}"
    )

    # Test 2: With no continuous columns it reproduces BernoulliNB
    bnb = BernoulliNB(alpha=0.7, binarize=0.0, force_alpha=True)
    bnb.fit(X_combined_csr[:, bin_idx], y)
    hnb_only_b = HybridNaiveBayes(
        continuous_idx=[], binary_idx=bin_idx, alpha=0.7, binarize=0.0, force_alpha=True
    )
    hnb_only_b.fit(X_combined_csr, y)
    proba_bnb = bnb.predict_proba(X_combined_csr[:, bin_idx])
    proba_hnb_b = hnb_only_b.predict_proba(X_combined_csr)
    max_diff_b = float(np.max(np.abs(proba_bnb - proba_hnb_b)))
    assert np.allclose(proba_bnb, proba_hnb_b, atol=1e-12), (
        f"Test 2 failed: HybridNaiveBayes without continuous cols differs from BernoulliNB by {max_diff_b}"
    )

    # Test 3: Rows of predict_proba sum to 1
    hnb_full = HybridNaiveBayes(
        continuous_idx=cont_idx,
        binary_idx=bin_idx,
        var_smoothing=1e-7,
        alpha=1.2,
        priors="balanced",
    )
    hnb_full.fit(X_combined_csr, y)
    proba_full = hnb_full.predict_proba(X_combined_csr)
    row_sums = proba_full.sum(axis=1)
    max_row_sum_err = float(np.max(np.abs(row_sums - 1.0)))
    assert np.allclose(row_sums, 1.0, atol=1e-12), (
        f"Test 3 failed: predict_proba rows do not sum to 1 (max error {max_row_sum_err})"
    )

    # Test 4: sklearn.base.clone works and reproduces identical predictions
    hnb_cloned = clone(hnb_full)
    hnb_cloned.fit(X_combined_csr, y)
    proba_cloned = hnb_cloned.predict_proba(X_combined_csr)
    max_clone_diff = float(np.max(np.abs(proba_full - proba_cloned)))
    assert np.allclose(proba_full, proba_cloned, atol=1e-12), (
        f"Test 4 failed: cloned HybridNaiveBayes differs by {max_clone_diff}"
    )

    # Test 5: Prior log-odds + sum of per-variable contributions reproduces model log-odds
    model_log_odds = hnb_full.predict_log_odds(X_combined_csr)
    prior_lo, contrib_full = hnb_full.feature_log_odds_contributions(X_combined_csr)
    reconstructed_lo = prior_lo + contrib_full.sum(axis=1)
    max_lo_diff = float(np.max(np.abs(model_log_odds - reconstructed_lo)))
    assert np.allclose(model_log_odds, reconstructed_lo, atol=1e-10), (
        f"Test 5a failed: log-odds decomposition differs by {max_lo_diff}"
    )

    # Also test block-aggregated OHE contribution identity
    prior_lo_agg, contrib_agg = hnb_full.feature_log_odds_contributions(
        X_combined_csr, split_binary_dense_and_ohe_at=4
    )
    reconstructed_lo_agg = prior_lo_agg + contrib_agg.sum(axis=1)
    max_lo_agg_diff = float(np.max(np.abs(model_log_odds - reconstructed_lo_agg)))
    assert np.allclose(model_log_odds, reconstructed_lo_agg, atol=1e-10), (
        f"Test 5b failed: block-aggregated log-odds decomposition differs by {max_lo_agg_diff}"
    )

    return {
        "test_1_reproduces_gaussian_nb_max_diff": max_diff_g,
        "test_2_reproduces_bernoulli_nb_max_diff": max_diff_b,
        "test_3_predict_proba_row_sum_max_err": max_row_sum_err,
        "test_4_sklearn_clone_max_diff": max_clone_diff,
        "test_5_log_odds_additivity_max_diff": max_lo_diff,
        "test_5b_block_log_odds_additivity_max_diff": max_lo_agg_diff,
        "all_passed": True,
    }
