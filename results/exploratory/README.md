# Exploratory analyses EA1–EA5 (not registered tests)

`python code/exploratory.py results/features data/big-ideas-1.1.3 results/exploratory`

Specified in one line each in §9 of the registration
(https://doi.org/10.17605/OSF.IO/CVFA3). The details were fixed in
`code/exploratory.py` (commit 0865e8c) after the registered run had started
and before any registered result existed. A container restart killed the first
run; resume support was added (commit after 4a3ae25, no analysis change) and
the whole set was re-run from scratch on 22 Nov 2026, 16:15–16:41 UTC.
No multiplicity correction and no verdicts; estimates with 95%
participant-bootstrap intervals (10,000 resamples, seed 20261122).

| Analysis | Files | Main estimate |
|---|---|---|
| EA1 SHAP attribution of FULL-KL, RANDOM (seed 0) vs LOPO | `ea1_shap.csv`, `ea1_parts/` | Sex largest under both (20% vs 33% of attribution); physiology 42% vs 36%, activity 26% vs 22% |
| EA2 personalised models (first half → second half of each recording) | `predictions/EA2_*` | XGBoost R² 0.141 vs participant mean 0.142 |
| EA3 CGM-noise ceiling (G6 MARD 10%) | `ea3_ceiling.csv` | Ceiling R² ≈ 0.59 pooled, 0.49 within participant |
| EA4a E4 on 15 participants without MEAL | `predictions/EA4a_*` | Physiology + activity reduce RMSE by 1.02 mg/dL (0.26–2.01) |
| EA4b E4 with 016's food log shifted −3 h (15 MEAL participants) | `predictions/EA4b_*` | Physiology + activity reduce RMSE by 0.44 mg/dL (0.07–0.91) |
| EA5 FULL-KL without sex, LOPO | `predictions/EA5_*` | R² −0.011 (−0.099 to 0.040) vs 0.071 with sex |

`ea_metrics.csv` holds every pooled metric; `ea_contrasts.csv` the paired
differences.
