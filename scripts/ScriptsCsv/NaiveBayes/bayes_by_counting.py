"""Pedagogical Bayes-by-counting calculator on training rows vs. BernoulliNB."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.naive_bayes import BernoulliNB


DEFAULT_TEACHING_BINARY_COLS: Tuple[str, ...] = (
    "es_vigente",
    "tiene_skills",
    "tiene_knowledge",
)


@dataclass(frozen=True)
class ManualBayesResult:
    """Outputs of the step-by-step manual Naive Bayes calculation vs. BernoulliNB."""

    feature_names: Tuple[str, ...]
    alpha: float
    priors_table: pd.DataFrame
    likelihood_table: pd.DataFrame
    comparison_table: pd.DataFrame
    max_abs_diff_vs_sklearn: float
    max_abs_diff_presence_only_naive: float


class ManualBayesCounter:
    """Compute Naive Bayes posteriors by hand from training counts with Laplace smoothing."""

    def __init__(
        self,
        feature_names: Sequence[str] = DEFAULT_TEACHING_BINARY_COLS,
        alpha: float = 1.0,
    ) -> None:
        self.feature_names = tuple(feature_names)
        self.alpha = float(alpha)

    def run_comparison(
        self,
        dense_train: pd.DataFrame,
        y_train: np.ndarray,
        n_rows: int = 5,
    ) -> ManualBayesResult:
        """Compute manual posteriors on 5 training rows and compare against BernoulliNB."""
        for col in self.feature_names:
            if col not in dense_train.columns:
                raise KeyError(f"Missing binary teaching column '{col}' in dense_train.")

        X_bin = dense_train[list(self.feature_names)].to_numpy(dtype=np.float64)
        y_arr = np.asarray(y_train, dtype=np.int64).ravel()
        if not np.isin(X_bin, [0.0, 1.0]).all():
            raise AssertionError("ManualBayesCounter requires strictly binary 0/1 columns.")

        n_total = len(y_arr)
        n_c0 = int((y_arr == 0).sum())
        n_c1 = int((y_arr == 1).sum())
        pi_0 = n_c0 / float(n_total)
        pi_1 = n_c1 / float(n_total)

        priors_table = pd.DataFrame(
            [
                {
                    "clase": "0 (No reincide)",
                    "conteo_filas_train": n_c0,
                    "total_train": n_total,
                    "prior_empirico": round(pi_0, 6),
                    "log_prior": round(float(np.log(pi_0)), 6),
                },
                {
                    "clase": "1 (Reincide)",
                    "conteo_filas_train": n_c1,
                    "total_train": n_total,
                    "prior_empirico": round(pi_1, 6),
                    "log_prior": round(float(np.log(pi_1)), 6),
                },
            ]
        )

        # Laplace-smoothed P(x_j = 1 | y = c) = (count(x_j=1, y=c) + alpha) / (N_c + 2 * alpha)
        theta_0 = np.zeros(len(self.feature_names), dtype=np.float64)
        theta_1 = np.zeros(len(self.feature_names), dtype=np.float64)
        likelihood_rows = []

        mask_0 = y_arr == 0
        mask_1 = y_arr == 1
        for j, col in enumerate(self.feature_names):
            c0_ones = int(X_bin[mask_0, j].sum())
            c1_ones = int(X_bin[mask_1, j].sum())
            p1_c0 = (c0_ones + self.alpha) / (n_c0 + 2.0 * self.alpha)
            p1_c1 = (c1_ones + self.alpha) / (n_c1 + 2.0 * self.alpha)
            theta_0[j] = p1_c0
            theta_1[j] = p1_c1
            likelihood_rows.append(
                {
                    "variable_binaria": col,
                    "conteo_x1_en_clase_0": c0_ones,
                    "conteo_x1_en_clase_1": c1_ones,
                    "P(x=1 | y=0)_laplace": round(p1_c0, 6),
                    "P(x=0 | y=0)_laplace": round(1.0 - p1_c0, 6),
                    "P(x=1 | y=1)_laplace": round(p1_c1, 6),
                    "P(x=0 | y=1)_laplace": round(1.0 - p1_c1, 6),
                    "razon_verosimilitud_x1": round(p1_c1 / p1_c0, 4),
                    "razon_verosimilitud_x0": round((1.0 - p1_c1) / (1.0 - p1_c0), 4),
                }
            )
        likelihood_table = pd.DataFrame(likelihood_rows)

        # Deterministically pick 5 rows covering distinct binary patterns in train
        sample_indices = self._select_illustrative_rows(X_bin, y_arr, n_rows=n_rows)
        X_sample = X_bin[sample_indices]
        y_sample = y_arr[sample_indices]

        # Fit sklearn BernoulliNB(alpha=self.alpha) on the same 3 columns
        bnb = BernoulliNB(alpha=self.alpha, binarize=0.0, force_alpha=True)
        bnb.fit(X_bin, y_arr)
        sklearn_probs = bnb.predict_proba(X_sample)[:, 1]

        comp_rows = []
        diffs_exact = []
        diffs_presence_only = []

        for idx_pos, row_idx in enumerate(sample_indices):
            x_vec = X_sample[idx_pos].astype(np.float64)
            # Full Bernoulli likelihood: P(x|c) = prod_j theta_{c,j}^{x_j} * (1 - theta_{c,j})^{1 - x_j}
            lik_c0 = float(np.prod((theta_0**x_vec) * ((1.0 - theta_0) ** (1.0 - x_vec))))
            lik_c1 = float(np.prod((theta_1**x_vec) * ((1.0 - theta_1) ** (1.0 - x_vec))))
            unnorm_0 = pi_0 * lik_c0
            unnorm_1 = pi_1 * lik_c1
            post_1_manual = unnorm_1 / (unnorm_0 + unnorm_1)

            # Presence-only formula (ignoring 1 - theta when x_j == 0) to illustrate why absence matters
            lik_pres_0 = float(np.prod(theta_0**x_vec))
            lik_pres_1 = float(np.prod(theta_1**x_vec))
            post_1_presence_only = (pi_1 * lik_pres_1) / (pi_0 * lik_pres_0 + pi_1 * lik_pres_1)

            sk_p1 = float(sklearn_probs[idx_pos])
            abs_diff = abs(post_1_manual - sk_p1)
            abs_diff_pres = abs(post_1_presence_only - sk_p1)
            diffs_exact.append(abs_diff)
            diffs_presence_only.append(abs_diff_pres)

            pattern_str = ", ".join(f"{name}={int(val)}" for name, val in zip(self.feature_names, x_vec))
            comp_rows.append(
                {
                    "fila_train_idx": int(row_idx),
                    "patron_binario": pattern_str,
                    "y_real": int(y_sample[idx_pos]),
                    "verosimilitud_P(x|y=0)": round(lik_c0, 6),
                    "verosimilitud_P(x|y=1)": round(lik_c1, 6),
                    "P_manual_bernoulli(y=1|x)": round(post_1_manual, 8),
                    "P_sklearn_BernoulliNB(y=1|x)": round(sk_p1, 8),
                    "diff_abs_manual_vs_sklearn": float(f"{abs_diff:.2e}"),
                    "P_solo_presencias_sin_ausencias(y=1|x)": round(post_1_presence_only, 6),
                }
            )

        max_diff = float(max(diffs_exact))
        max_diff_pres = float(max(diffs_presence_only))
        if max_diff > 1e-8:
            raise AssertionError(
                f"Manual Bernoulli Bayes calculation differs from BernoulliNB by {max_diff}"
            )

        return ManualBayesResult(
            feature_names=self.feature_names,
            alpha=self.alpha,
            priors_table=priors_table,
            likelihood_table=likelihood_table,
            comparison_table=pd.DataFrame(comp_rows),
            max_abs_diff_vs_sklearn=max_diff,
            max_abs_diff_presence_only_naive=max_diff_pres,
        )

    @staticmethod
    def _select_illustrative_rows(X_bin: np.ndarray, y_arr: np.ndarray, n_rows: int = 5) -> np.ndarray:
        """Select deterministic row indices spanning distinct binary feature patterns."""
        selected = []
        seen_patterns = set()
        for idx in range(len(y_arr)):
            pat = tuple(int(v) for v in X_bin[idx])
            if pat not in seen_patterns:
                seen_patterns.add(pat)
                selected.append(idx)
                if len(selected) == n_rows:
                    break
        if len(selected) < n_rows:
            for idx in range(len(y_arr)):
                if idx not in selected:
                    selected.append(idx)
                    if len(selected) == n_rows:
                        break
        return np.asarray(selected, dtype=np.int64)
