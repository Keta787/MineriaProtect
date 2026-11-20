"""Unit tests for the first-principles OLS engine (T-NM-01, T-NM-02)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ScriptsCsv.MetodosNumericos.ols import (
    build_summation_and_residual_table,
    predict_ols,
    regresion_lineal,
    verify_affine_scaling_invariance,
)


class TestOLSEngine(unittest.TestCase):
    """Verify closed-form OLS against Presentation 1 fixtures and numpy.polyfit."""

    def test_presentation_server_load_fixture(self) -> None:
        # Exact guided exercise from regresion_lineal_minimos_cuadrados.html Slides 6-12
        x = [1, 2, 3, 4, 5, 6]
        y = [120, 145, 185, 200, 240, 260]
        res = regresion_lineal(x, y, name="Server Load Benchmark")

        self.assertEqual(res.n, 6)
        self.assertAlmostEqual(res.sum_x, 21.0, places=10)
        self.assertAlmostEqual(res.sum_y, 1150.0, places=10)
        self.assertAlmostEqual(res.sum_xx, 91.0, places=10)
        self.assertAlmostEqual(res.sum_xy, 4525.0, places=10)
        self.assertAlmostEqual(res.a1, 3000.0 / 105.0, places=10)
        self.assertAlmostEqual(res.a0, 1150.0 / 6.0 - (3000.0 / 105.0) * 3.5, places=10)
        self.assertAlmostEqual(res.r2, 0.98977233, places=6)
        self.assertAlmostEqual(res.r, 0.99487302, places=6)
        self.assertAlmostEqual(res.s_yx, 6.07492896, places=6)
        self.assertLess(res.centroid_err, 1e-10)
        self.assertLess(abs(res.residual_sum), 1e-10)
        self.assertLess(res.polyfit_max_abs_diff, 1e-10)

        preds = predict_ols(res, [3.5, 7.0])
        self.assertFalse(bool(preds.loc[0, "is_extrapolation"]))
        self.assertTrue(bool(preds.loc[1, "is_extrapolation"]))
        self.assertAlmostEqual(float(preds.loc[1, "y_hat"]), 291.66666667, places=6)

        tbl = build_summation_and_residual_table(x, y, res)
        self.assertAlmostEqual(float(tbl["e_i_sq"].sum()), res.s_r, places=10)
        self.assertAlmostEqual(float(tbl["y_minus_ybar_sq"].sum()), res.s_t, places=10)

    def test_presentation_practice_loc_fixture(self) -> None:
        # Exact practice exercise from regresion_lineal_minimos_cuadrados.html Slide 13
        x = [2, 4, 6, 8, 10]
        y = [5, 9, 12, 18, 21]
        res = regresion_lineal(x, y, name="LOC Compilation Practice")
        self.assertAlmostEqual(res.a1, 2.05, places=10)
        self.assertAlmostEqual(res.a0, 0.70, places=10)
        self.assertLess(res.polyfit_max_abs_diff, 1e-10)

    def test_low_r2_verdict_and_guards(self) -> None:
        # Zero variance in x must raise ValueError
        with self.assertRaises(ValueError):
            regresion_lineal([5, 5, 5], [1, 2, 3])
        # NaN input must raise ValueError
        with self.assertRaises(ValueError):
            regresion_lineal([1, 2, np.nan], [1, 2, 3])
        # Poor linear fit must be flagged honestly (MR-06)
        res_poor = regresion_lineal([1, 2, 3, 4, 5], [10, 2, 9, 1, 10], name="Noisy")
        self.assertIn("Rejected", res_poor.quality_verdict)

    def test_affine_scaling_invariance(self) -> None:
        rng = np.random.default_rng(42)
        x = rng.uniform(10.0, 50.0, size=500)
        y = 3.5 + 1.25 * x + rng.normal(0.0, 2.0, size=500)
        cx, sx = 25.0, 12.0
        cy, sy = 30.0, 15.0
        raw = regresion_lineal(x, y, name="raw")
        scaled = regresion_lineal((x - cx) / sx, (y - cy) / sy, name="scaled")
        check = verify_affine_scaling_invariance(raw, scaled, cx, sx, cy, sy)
        self.assertTrue(check["passes_tol"])
        self.assertLess(check["max_invariance_err"], 1e-10)


if __name__ == "__main__":
    unittest.main()
