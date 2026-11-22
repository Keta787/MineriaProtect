"""End-to-end integration and governance tests for the 8-idea Numerical Methods Core Suite."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

import numpy as np
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
        self.assertGreaterEqual(len(sha_df), 19)
        self.assertTrue(bool(sha_df["intact"].all()))
        self.assertIn("hash_mode", sha_df.columns)
        hex64 = re.compile(r"^[0-9a-f]{64}$")
        for col in ("sha256_before", "sha256_after"):
            for h in sha_df[col].astype(str):
                self.assertRegex(h, hex64)
        self.assertTrue(
            set(sha_df["hash_mode"].unique()).issubset(
                {"full_sha256", "sampled_24MiB_plus_meta_sha256"}
            )
        )

        # Verify explicit MR-06 warning in ggb_rl02 and monomial forms in ggb_lg01 / ggb_lg02
        rl02_ggb = (self.cfg.geogebra_dir / "ggb_rl02_isco10_transferability.txt").read_text(encoding="utf-8")
        self.assertIn("MR-06", rl02_ggb)
        self.assertIn("REJECTED", rl02_ggb)
        lg01_ggb = (self.cfg.geogebra_dir / "ggb_lg01_survival_p3_milestones.txt").read_text(encoding="utf-8")
        lg02_ggb = (self.cfg.geogebra_dir / "ggb_lg02_pca_forward_p3.txt").read_text(encoding="utf-8")
        self.assertIn("Expanded monomial", lg01_ggb)
        self.assertIn("Expanded monomial", lg02_ggb)

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

    def test_mr09_closed_job_duration_consistency_and_wls(self) -> None:
        # RL-04 annual duration must exclude active jobs (~es_vigente), removing the 2019 rebound
        ann = pd.read_csv(self.tdir / "rl04_annual_macro_series.csv").set_index("start_year")
        self.assertIn("n_closed_starts", ann.columns)
        self.assertIn("mean_dur_q_incl_active", ann.columns)
        self.assertLess(float(ann.loc[2019, "mean_dur_q"]), float(ann.loc[2018, "mean_dur_q"]))

        # RL-01 must filter closed rows (~es_vigente) and include WLS robustness metrics
        prof = pd.read_csv(self.tdir / "rl01_career_step_profile.csv")
        self.assertIn("n_closed_rows", prof.columns)
        self.assertTrue(bool((prof["n_closed_rows"] < prof["n_rows"]).all()))

        rl01 = pd.read_csv(self.tdir / "rl01_ols_summary.csv")
        for col in ("wls_a0", "wls_a1", "wls_slope_rel_diff_pct"):
            self.assertIn(col, rl01.columns)
        sk_row = rl01.loc[(rl01["idea_id"] == "IDEA-RL-01") & (rl01["y_var"] == "mean_skills")].iloc[0]
        self.assertLess(float(sk_row["wls_slope_rel_diff_pct"]), 5.0)

        # LG-01 Chebyshev-Lobatto must produce 0 [0, 1] probability bound violations across ALL degrees
        rb = pd.read_csv(self.tdir / "lg01_runge_phenomenon_benchmark.csv")
        cheb_rows = rb.loc[rb["node_strategy"] == "Chebyshev-Snapped Global Lagrange"]
        self.assertEqual(len(cheb_rows), 5)
        self.assertEqual(int(cheb_rows["n_prob_bound_violations"].sum()), 0)

    def test_lg_monomial_expansions_and_live_pca_precision(self) -> None:
        mono = pd.read_csv(self.tdir / "lg_monomial_expansions.csv")
        self.assertEqual(len(mono), 3)
        self.assertLess(float(mono["kronecker_max_err"].max()), 1e-12)
        self.assertLess(float(mono["unity_sum_max_err"].max()), 1e-12)
        self.assertLess(float(mono["scipy_max_abs_diff"].max()), NUMERICAL_TOL)

        # Evaluate LG-01 expanded monomial at q=12 and match P3(12)
        r_lg01 = mono.loc[mono["idea_id"] == "IDEA-LG-01"].iloc[0]
        p3_12 = float(np.polyval([r_lg01["c3"], r_lg01["c2"], r_lg01["c1"], r_lg01["c0"]], 12.0))
        ev_lg01 = pd.read_csv(self.tdir / "lg01_milestone_P3_weights_and_eval.csv")
        ref_12 = float(ev_lg01.loc[ev_lg01["quarter_q"] == 12, "P3_pred"].iloc[0])
        self.assertAlmostEqual(p3_12, ref_12, places=10)

        # Live float64 PCA precision check (Version A rank-9 collinearity vs Version B full-rank)
        pca_ref = pd.read_csv(self.tdir / "lg02_pca_50k_reference.csv").set_index("k_components")
        self.assertLess(float(pca_ref.loc[10, "marginal_var_version_a"]), 1e-12)
        self.assertGreater(float(pca_ref.loc[10, "marginal_var_version_b"]), 1e-5)

    def test_deliverable_completeness_bilingual_wording_and_links(self) -> None:
        ent = self.cfg.root / "metodos_numericos_entregable"
        if not ent.is_dir():
            self.skipTest("Run `python -m scripts.ScriptsCsv.MetodosNumericos.deliverable_packager` first.")

        for req in [
            ent / "README.md",
            ent / "index.html",
            ent / "presentaciones_separadas.html",
            ent / "00_general" / "EVALUACION_UNIFICADA_8_CASOS.md",
            self.cfg.root / "metodos_numericos_entregable.zip",
        ]:
            self.assertTrue(req.exists(), f"Missing required deliverable artifact: {req}")

        exps = sorted(ent.glob("0*/EXPLICACION_*.md"))
        guias = sorted(ent.glob("0*/GUIA_FACIL_*.md"))
        pres = sorted(ent.glob("0*/presentacion_IDEA_*.html"))
        nlm = sorted((ent / "fuentes_notebooklm").glob("Caso_*.md"))
        self.assertEqual(len(exps), 8)
        self.assertEqual(len(guias), 8)
        self.assertEqual(len(pres), 8)
        self.assertEqual(len(nlm), 8)

        # Check ZERO broken relative markdown links in fuentes_notebooklm/*.md and README.md
        link_pat = re.compile(r"\]\((?!https?://|#|mailto:)([^)]+)\)")
        for md_file in [*nlm, ent / "README.md"]:
            text = md_file.read_text(encoding="utf-8")
            for rel in link_pat.findall(text):
                target = (md_file.parent / rel).resolve()
                self.assertTrue(target.exists(), f"Broken relative link in {md_file.name}: {rel} -> {target}")

        # Bilingual EN+ES MR-07/MR-08 wording audit over ALL deliverable markdown and HTML decks
        wording_ent = audit_wording_compliance([*exps, *guias, *pres])
        failed = wording_ent.loc[~wording_ent["passed"]]
        self.assertTrue(
            bool(wording_ent["passed"].all()),
            f"Wording audit violations in deliverable: {failed[['file_path', 'violations']].to_dict('records')}",
        )


if __name__ == "__main__":
    unittest.main()
