"""End-to-end integration and governance tests for the 8-idea Numerical Methods Core Suite."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ScriptsCsv.MetodosNumericos.config import APPROVED_FIGURES, NUMERICAL_TOL, default_config
from scripts.ScriptsCsv.MetodosNumericos.validation import (
    audit_wording_compliance,
    validate_geogebra_scripts,
    verify_figure_manifest,
)


class TestPipelineOutputs(unittest.TestCase):
    """Validate all exported tables, figures, GeoGebra scripts, numerical invariants & SHA-256 audit."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.cfg = default_config(ROOT)
        cls.tdir = cls.cfg.tables_dir
        if not (cls.tdir / "ols_summary_all_ideas.csv").exists():
            raise unittest.SkipTest("Run `python -m scripts.ScriptsCsv.MetodosNumericos.pipeline` first.")

    def test_ols_polyfit_equivalence_and_rejections(self) -> None:
        ols_all = pd.read_csv(self.tdir / "ols_summary_all_ideas.csv")
        self.assertGreaterEqual(len(ols_all), 20)
        # Relative tolerance check (handles large uncentered year intercepts like |a0| ~ 5.4e6 cleanly)
        scale = ols_all[["a0", "a1"]].abs().max(axis=1).clip(lower=1.0)
        max_rel_diff = float((ols_all["polyfit_max_abs_diff"] / scale).max())
        self.assertLess(max_rel_diff, NUMERICAL_TOL)

        # IDEA-RL-01 verified strong career-step skill progression
        rl01 = pd.read_csv(self.tdir / "rl01_ols_summary.csv")
        sk_row = rl01.loc[(rl01["idea_id"] == "IDEA-RL-01") & (rl01["y_var"] == "mean_skills")].iloc[0]
        self.assertGreater(float(sk_row["r2"]), 0.99)

        # IDEA-RL-02 verified honest rejection of low-R^2 pairs (MR-06)
        rl02 = pd.read_csv(self.tdir / "rl02_esco_catalog_ols.csv")
        opt_row = rl02.loc[(rl02["x_var"] == "n_essential") & (rl02["y_var"] == "n_optional")].iloc[0]
        grn_row = rl02.loc[(rl02["x_var"] == "n_essential") & (rl02["y_var"] == "greenShare")].iloc[0]
        self.assertIn("Rejected", str(opt_row["quality_verdict"]))
        self.assertIn("Rejected", str(grn_row["quality_verdict"]))
        self.assertEqual(int(opt_row["n"]), 3039)

    def test_rl04_extrapolation_failure_and_raw_parity(self) -> None:
        ext = pd.read_csv(self.tdir / "rl04_extrapolation_failure_audit.csv")
        dur_2027 = ext.loc[(ext["y_var"] == "mean_dur_q") & (ext["year"] == 2027)].iloc[0]
        self.assertTrue(bool(dur_2027["physically_invalid"]))
        self.assertLess(float(dur_2027["y_pred_from_2000_2019"]), 0.0)

        parity = pd.read_csv(self.tdir / "rl04_raw_partition_parity.csv")
        self.assertEqual(len(parity), 3)
        self.assertEqual(int(parity["total_rows_raw"].sum()), 1_993_291)

    def test_rl05_outlier_audit_and_affine_invariance(self) -> None:
        out_df = pd.read_csv(self.tdir / "rl05_four_way_outlier_comparison.csv")
        self.assertEqual(len(out_df), 8)  # 4 variants x 2 predictor pairs

        inv_df = pd.read_csv(self.tdir / "rl05_affine_scale_invariance.csv")
        self.assertEqual(len(inv_df), 8)  # 2 versions x 2 splits x 2 pairs
        self.assertTrue(bool(inv_df["passes_tol"].all()))
        self.assertLess(float(inv_df["max_invariance_err"].max()), NUMERICAL_TOL)

    def test_lg01_runge_explosion_and_chebyshev_mitigation(self) -> None:
        rb = pd.read_csv(self.tdir / "lg01_runge_phenomenon_benchmark.csv")
        eq16 = rb.loc[(rb["degree"] == 16) & (rb["node_strategy"] == "Equispaced Global Lagrange")].iloc[0]
        ch16 = rb.loc[(rb["degree"] == 16) & (rb["node_strategy"] == "Chebyshev-Snapped Global Lagrange")].iloc[0]
        self.assertGreater(float(eq16["max_abs_err"]), 1.0)
        self.assertGreater(int(eq16["n_prob_bound_violations"]), 0)
        self.assertLess(float(ch16["max_abs_err"]), 0.20)

        ev = pd.read_csv(self.tdir / "lg01_milestone_P3_weights_and_eval.csv")
        self.assertLess(float((ev["sum_Li"] - 1.0).abs().max()), 1e-10)

    def test_lg02_pca_forward_inverse_and_plateau(self) -> None:
        fwd = pd.read_csv(self.tdir / "lg02_pca_forward_P3_eval.csv")
        self.assertEqual(len(fwd), 8)
        self.assertLess(float((fwd["sum_Li"] - 1.0).abs().max()), 1e-10)

        inv = pd.read_csv(self.tdir / "lg02_pca_inverse_effective_dim.csv")
        self.assertEqual(len(inv), 8)
        self.assertTrue(bool(inv["meets_target"].all()))

    def test_hyb01_four_by_four_rubric(self) -> None:
        bm = pd.read_csv(self.tdir / "hyb01_loocv_and_extrapolation_matrix.csv")
        self.assertEqual(len(bm), 16)
        self.assertTrue(bm[["loocv_mae", "loocv_rmse", "extrap_2step_mae"]].notna().all().all())

        rubric = pd.read_csv(self.tdir / "hyb01_method_selection_rubric.csv")
        self.assertEqual(len(rubric), 4)

    def test_hyb02_geogebra_figures_sha256_and_wording(self) -> None:
        ggb = validate_geogebra_scripts(self.cfg.geogebra_dir)
        self.assertEqual(len(ggb), 5)
        self.assertTrue(bool(ggb["passed"].all()))

        fig_rep = verify_figure_manifest(self.cfg)
        self.assertEqual(len(fig_rep), len(APPROVED_FIGURES))
        self.assertTrue(bool(fig_rep["exists"].all()))
        self.assertTrue(bool((fig_rep["size_kb"] > 10.0).all()))

        sha_df = pd.read_csv(self.tdir / "sha256_input_integrity.csv")
        self.assertGreaterEqual(len(sha_df), 15)
        self.assertTrue(bool(sha_df["intact"].all()))

        wording = audit_wording_compliance(
            [
                self.cfg.verification_log_path,
                self.cfg.geogebra_dir / "geogebra_verification_index.md",
                self.cfg.root / "notebooks" / "refactor" / "8.0_regresion_lineal_minimos_cuadrados.ipynb",
                self.cfg.root / "notebooks" / "refactor" / "8.1_interpolacion_lagrange.ipynb",
                self.cfg.root / "notebooks" / "refactor" / "8.2_comparativa_regresion_vs_interpolacion.ipynb",
            ]
        )
        self.assertTrue(bool(wording["passed"].all()))


if __name__ == "__main__":
    unittest.main()
