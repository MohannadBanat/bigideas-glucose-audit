# OSF pre-registration — DRAFT (not filed)

**Working title:** Revealing time and identity shortcuts in wrist-wearable glucose estimation: a pre-registered re-evaluation of the BIG IDEAs dataset

Every `TODO` must be resolved and agreed by all authors **before any model is trained**. The structure follows the team's stress/exercise registration (Abu Owida et al., Sensors 2026), so reuse its wording where possible.

---

## 1. Data

- BIG IDEAs Lab Glycemic Variability and Wearable Device Data, **v1.1.3** (doi 10.13026/aw6y-fc44).
- 16 participants, Dexcom G6 (5-min interstitial glucose) and Empatica E4 (BVP 64 Hz, EDA/TEMP 4 Hz, ACC 32 Hz, HR 1 Hz), plus food logs and Demographics.csv (sex, HbA1c).
- **Already seen by the authors before registration:**
  - the dataset documentation
  - the food log of participant 001 (to check clock-time plausibility)
  - the output of `check_time_of_day.py`, run on 22 Nov 2026 (`results/time_of_day/`). It read the food logs, Dexcom CGM glucose values and Demographics.csv for all 16 participants. It showed that clock time is preserved, that food log and CGM agree for 14 of 16 participants (015: food log lies outside the CGM recording; 016: no meal response at logged times), and that the cohort is 9 female / 7 male. No E4 data was read.
- No glucose-prediction model has been trained by the authors.

## 2. Unit of analysis and target

- **Unit:** one CGM reading (5 min). Wearable features are computed in windows ending at the CGM timestamp.
  - TODO: window lengths. Suggested 5 min for physiology and 2 h for activity, matching Karunarathna & Liang.
- **Target:** CGM glucose (mg/dL).
- Lagged CGM values are **never** used as inputs. Otherwise the task becomes forecasting, not estimation.

## 3. Exclusions and quality rules

TODO: fix these before running.
- Periods with no E4 data.
- CGM warm-up periods.
- E4 validity rules reused from the stress paper (EDA ≥ 0.05 µS, TEMP between 20 and 40 °C, pulse coverage ≥ 0.5).
- Food-log entries with implausible times. TODO: rule, e.g. flag 00:00–05:00 entries, but do not drop them silently.

## 4. Feature sets

| Set | Contents |
|---|---|
| PHYS | E4 physiology: HR, HRV, TEMP, EDA tonic/phasic, BVP features |
| ACT | ACC summaries over 2 h (min/max/mean) |
| TIME | Minutes from midnight, plus sin/cos |
| MEAL | Time since last logged meal; carbs and sugar over the previous 2/8/24 h. Computed only for participants who passed the food-log/CGM alignment check (14 of 16; 015 and 016 excluded, see `results/time_of_day/README.md`). TODO: agree this rule. |
| ID | Sex; HbA1c; participant ID (one-hot, only where it is not leakage-trivial) |
| FULL-KL | Re-implementation of Karunarathna & Liang's feature list (PHYS + ACT + TIME + sex) |
| FULL-B | Re-implementation of Bent et al.'s inputs (PHYS + ACT + TIME + MEAL + HbA1c + sex) |

## 5. Models

- **Primary:** XGBoost.
- **Secondary:** ridge regression.
- **Baselines:**
  - Population mean (training-fold mean)
  - Participant-mean baseline (personal split only)
- Hyperparameters: small fixed grid, tuned by grouped 5-fold CV on training participants only. TODO: copy the grid format of the stress paper's Table A1.

## 6. Registered experiments and hypotheses

| Exp | Question | Comparison | Hypothesis |
|---|---|---|---|
| E1 | Does re-implementing Karunarathna & Liang reproduce the published R² 0.73? | FULL-KL, random window-level 80/20, 20 seeds | Criterion: mean R² within TODO (e.g. 0.05) of 0.73 |
| E2 | Does R² fall when participants are held out? | FULL-KL: random 80/20 vs LOPO | **H1:** R²(random) − R²(LOPO) > TODO (e.g. 0.30) |
| E3 | Can shortcuts alone match the full model under the leaky split? | Under random 80/20: TIME-only, ID-only, TIME+ID vs FULL-KL | **H2:** TIME+ID R² non-inferior to FULL-KL within margin TODO (e.g. 0.05). **H3:** ID-only R² > 0.5 × FULL-KL R² |
| E4 | Does wrist physiology add anything under honest evaluation? | LOPO: population mean; TIME+MEAL+ID; TIME+MEAL+ID+PHYS+ACT (FULL-B) | **H4:** FULL-B RMSE not lower than TIME+MEAL+ID RMSE by more than TODO mg/dL. **H5:** FULL-B under LOPO does not beat the population mean on R² by more than TODO |
| E5 | Does the Clarke grid hide failure? | Clarke A+B% for population-mean baseline vs FULL-KL (both splits) | **H6:** Baseline A+B% ≥ 90% |
| E6 | Do adjacent windows leak information? | Random split vs blocked split with a TODO-min buffer (e.g. 60 min) between training and test blocks, within participants | **H7:** R² decreases as buffer length increases |

Primary hypotheses: TODO, choose them, e.g. H1, H2, H4. All hypotheses will be tested with Holm–Bonferroni correction across the family.

## 7. Metrics and statistics

- **Metrics:** RMSE, MARD, R², Clarke error grid zones; per participant and pooled.
- **Confidence intervals:** 95% from a participant-level bootstrap. TODO: number of resamples (stress paper used …).
- **Non-inferiority/equivalence:** one-sided tests at margins fixed above.
- With n = 16, report every LOPO fold individually (a per-participant plot) as well as the summary.

## 8. Exploratory analyses (labelled as such; not registered)

- **EA1:** SHAP attribution on FULL-KL under random vs LOPO splits.
- **EA2:** personalized models (first 50% / last 50%, as in Bent 2021) vs the participant-mean baseline.
- **EA3:** CGM reliability ceiling (Dexcom G6 MARD) as an upper bound on achievable R².

## 9. Deviations

Any deviation from this plan will be reported in a dedicated table, as in the stress paper's Appendix B.
