"""Unit tests for the first-principles Lagrange Interpolation engine (T-NM-03, T-NM-04, T-NM-05)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ScriptsCsv.MetodosNumericos.lagrange import (
    chebyshev_nodes,
    diagnose_lagrange,
    expand_monomial_coefficients,
    inverse_lagrange_eval,
    lagrange_eval,
    piecewise_lagrange_eval,
)


class TestLagrangeEngine(unittest.TestCase):
    """Verify Lagrange basis, evaluation, monomial expansion, Chebyshev & piecewise against Presentation 2."""

    def test_presentation_cpu_temperature_fixture(self) -> None:
        # Exact guided exercise from interpolacion_lagrange.html Slides 6-11
        xs = [20.0, 50.0, 80.0]
        ys = [45.0, 58.0, 76.0]
        y_hat, w, extrap = lagrange_eval(xs, ys, [65.0, 100.0])

        self.assertAlmostEqual(float(y_hat[0]), 66.375, places=10)
        self.assertAlmostEqual(float(w[0, 0]), -0.125, places=10)
        self.assertAlmostEqual(float(w[0, 1]), 0.75, places=10)
        self.assertAlmostEqual(float(w[0, 2]), 0.375, places=10)
        self.assertAlmostEqual(float(np.sum(w[0])), 1.0, places=12)
        self.assertFalse(bool(extrap[0]))
        self.assertTrue(bool(extrap[1]))

        coeffs = expand_monomial_coefficients(xs, ys)
        self.assertAlmostEqual(float(coeffs[0]), 1.0 / 360.0, places=10)
        self.assertAlmostEqual(float(coeffs[1]), 43.0 / 180.0, places=10)
        self.assertAlmostEqual(float(coeffs[2]), 352.0 / 9.0, places=10)

        diag = diagnose_lagrange(xs, ys, name="CPU Temp")
        self.assertLess(diag.kronecker_max_err, 1e-12)
        self.assertLess(diag.unity_sum_max_err, 1e-12)
        self.assertLess(diag.scipy_max_abs_diff, 1e-10)

    def test_presentation_practice_fixture(self) -> None:
        # Exact practice exercise from interpolacion_lagrange.html Slide 13
        xs = [0.0, 1.0, 3.0]
        ys = [1.0, 3.0, 25.0]
        y_hat, w, _ = lagrange_eval(xs, ys, [2.0])
        self.assertAlmostEqual(float(w[0, 0]), -1.0 / 3.0, places=10)
        self.assertAlmostEqual(float(w[0, 1]), 1.0, places=10)
        self.assertAlmostEqual(float(w[0, 2]), 1.0 / 3.0, places=10)
        self.assertAlmostEqual(float(y_hat[0]), 11.0, places=10)

    def test_distinct_node_and_monotonic_inverse_guards(self) -> None:
        # Duplicate x nodes must raise ValueError (MR-04)
        with self.assertRaises(ValueError):
            lagrange_eval([1.0, 2.0, 2.0], [3.0, 4.0, 5.0], [1.5])
        # Plateau y values in inverse interpolation (like PCA V(9)=V(10)=1.0) must raise ValueError
        with self.assertRaises(ValueError):
            inverse_lagrange_eval([1, 2, 3], [0.5, 1.0, 1.0], [0.75])

    def test_chebyshev_and_piecewise_quadratic(self) -> None:
        nodes = chebyshev_nodes(1.0, 40.0, degree=12, snap_int=True)
        self.assertTrue(np.all(np.diff(nodes) > 0))
        self.assertGreaterEqual(float(nodes[0]), 1.0)
        self.assertLessEqual(float(nodes[-1]), 40.0)

        # Piecewise P2 must recover any exact quadratic exactly
        xs = np.linspace(0.0, 10.0, 11)
        ys = 2.0 * xs**2 - 3.0 * xs + 7.0
        xq = np.array([0.5, 3.7, 8.2])
        yq = piecewise_lagrange_eval(xs, ys, xq, degree=2)
        np.testing.assert_allclose(yq, 2.0 * xq**2 - 3.0 * xq + 7.0, atol=1e-10)


if __name__ == "__main__":
    unittest.main()
