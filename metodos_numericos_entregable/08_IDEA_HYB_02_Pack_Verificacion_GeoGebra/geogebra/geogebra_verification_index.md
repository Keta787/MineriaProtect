# GeoGebra Verification Pack Index (`IDEA-HYB-02`)

Open [GeoGebra Classic](https://www.geogebra.org/classic) and paste the commands from any `.txt` file below into the Algebra Input bar. English command names work in all GeoGebra language locales.

| Case Study | File | Method | Expected Key Output (Python Verified `< 1e-10`) |
|---|---|---|---|
| `IDEA-RL-01` | `ggb_rl01_career_steps_skills.txt` | OLS `FitLine` | `a0 = 22.516043`, `a1 = 0.224971`, `R2 = 0.995498`, `f(12) = 25.215697` |
| `IDEA-RL-02` | `ggb_rl02_isco10_transferability.txt` | OLS `FitLine` (`MR-06` Rejected) | `a0 = 3.448113`, `a1 = 0.432990`, `R2 = 0.280010` (`< 0.30`: `f(45)` solo verificación aritmética) |
| `IDEA-RL-04` | `ggb_rl04_annual_duration_extrapolation.txt` | OLS `FitLine` (`MR-09` `~es_vigente`) | `a0 = 16.441713`, `a1 = -0.792601`, `R2 = 0.972874`, `f(27) = -4.958505` (negative!) |
| `IDEA-LG-01` | `ggb_lg01_survival_p3_milestones.txt` | Lagrange `P3` vs `Polynomial(P)` | `P3(12) = 0.206491` (true `S(12) = 0.251949`) |
| `IDEA-LG-02` | `ggb_lg02_pca_forward_p3.txt` | Lagrange `P3` vs `Polynomial(P)` | `P3(4) = 0.877777` (true `V(4) = 0.877604`) |
