# Verification Log — JobPath Numerical Methods 8-Idea Core Suite

- **Timestamp:** `2026-11-21 23:12:35`
- **Selected Scope:** 8-Idea Core (`IDEA-RL-01`, `IDEA-RL-02`, `IDEA-RL-04`, `IDEA-RL-05`, `IDEA-LG-01`, `IDEA-LG-02`, `IDEA-HYB-01`, `IDEA-HYB-02`)
- **Read-Only `data/` Integrity (SHA-256, 64-char hex):** `PASS (100% intact)` (19 audited inputs: 13 full SHA-256 + 6 sampled 24 MiB+meta SHA-256)
- **Censoring Consistency (`MR-09` `~es_vigente`):** `PASS` (`mean_dur_q` computed strictly on closed jobs across `RL-01`, `RL-04`, and `LG-01`)
- **Live PCA Source (`IDEA-LG-02`):** `live_50k_from_03_processed_float64` (computed directly from `data/03_processed`, zero hardcoded curves)
- **Approved Figures Generated:** `PASS` (12/12 PNGs at 150 DPI)
- **GeoGebra Verification Pack:** `PASS` (5 `.txt` scripts + Markdown index)
- **Bilingual Wording Audit (`MR-07/MR-08` EN+ES):** `PASS` (28 files scanned, 0 violations)
- **Max OLS Diff vs. `numpy.polyfit`:** relative `2.294e-12` (`PASS < 1e-10`) · raw abs `1.523e-07` (on uncentered year intercept `|a0| ~ 2.18e6`)
- **Max Affine Scale-Invariance Error (`04_transformed`):** `7.216e-14` (threshold `< 1e-10`)
- **Lagrange `LG-01` P3 SciPy Diff:** `5.052e-15` | Kronecker: `0.000e+00` | Partition of Unity: `4.441e-16`
- **Runge's Phenomenon Verification (deg=16, Chebyshev-Lobatto):** Equispaced `E_inf = 2.5262` vs. Chebyshev-Lobatto `E_inf = 0.1301` (`19.4x` error reduction, `0` total `[0,1]` violations across degrees 3–16)
- **PCA Plateau Distinct-Node Guard (`MR-04`):** `TRIGGERED` (`Interpolation nodes x_i must be strictly distinct (min gap = 0.000e+00 < 1.0e-12).`)
