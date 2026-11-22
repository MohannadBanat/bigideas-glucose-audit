# OSF pre-registration: DRAFT, ready for co-author review (not filed)

**Working title:** Revealing time and identity shortcuts in wrist-wearable glucose estimation: a pre-registered re-evaluation of the BIG IDEAs dataset

**Status (22 Nov 2026).** Every earlier `TODO` now has a proposed value. Values
marked **[PROPOSED]** are judgement calls that all authors must accept or
change **before any model is trained**. After that, file this text on OSF
unchanged and record the OSF DOI in `docs/03_next_steps.md`. The structure and
wording follow the team's stress/exercise registration (Banat & Abu Owida,
OSF swge8; published as Abu Owida et al., *Sensors* 2026, 26, 7340).

---

## 1. Data

- BIG IDEAs Lab Glycemic Variability and Wearable Device Data, **v1.1.3**
  (doi 10.13026/aw6y-fc44). Food logs, Dexcom files and `Demographics.csv`
  are downloaded from physionet.org. E4 files are streamed from the AWS mirror
  (which stops at v1.1.2; its E4 and Dexcom files are byte-identical to v1.1.3)
  and every file is checked against the v1.1.3 `SHA256SUMS.txt`.
- 16 participants: Dexcom G6 (interstitial glucose every 5 min), Empatica E4
  (BVP 64 Hz, EDA and TEMP 4 Hz, ACC 32 Hz, HR 1 Hz, IBI), food logs, and
  `Demographics.csv` (sex, HbA1c).
- **Already seen by the authors before registration:**
  - the dataset documentation, and the article by Karunarathna & Liang (2025),
    including its methods and reported results;
  - the food log of participant 001, read to check that clock times are
    plausible;
  - the output of `code/check_time_of_day.py`, run on 22 Nov 2026
    (`results/time_of_day/`). It read the food logs, the Dexcom CGM glucose
    values and `Demographics.csv` for all 16 participants. It showed that clock
    time is preserved, that food log and CGM agree for 14 of 16 participants
    (015: the food log lies outside the CGM recording; 016: no meal response
    at the logged times), and that the cohort is 9 female and 7 male (HbA1c
    5.3–6.4%). It also showed mean CGM glucose by clock hour. No E4 data was
    read. One rule of that check was changed after its first run, and the
    change is documented there.
  - the per-participant counts from the feature build (`code/features.py`,
    22 Nov 2026; `results/features/features_log.csv`): how many CGM readings
    fall in the sensor warm-up, how many have no E4 data, and how many remain.
    These counts use only the timing of the E4 and Dexcom records. The glucose
    values in the feature tables were not summarised or plotted; the analysis
    code was checked only on a synthetic noise target (`results/selftest/`).
    These counts are what showed that participant 015 has far less overlapping
    data than the others, and rule 7 in §3 was written after seeing them.
- No glucose-estimation model has been trained by the authors on any version
  of this dataset.

## 2. Unit of analysis and target

- **Unit:** one CGM reading (Dexcom EGV row). The target is that reading in
  mg/dL.
- **Windows:** physiological and short activity features use the **5 min
  before** the CGM timestamp, as in Karunarathna & Liang. Long activity
  features use the **2 h before** it.
- **Lagged CGM values are never inputs.** With them the task becomes
  forecasting, not estimation.
- **Pre-modelling data check (not outcome-based).** For each participant,
  report the overlap between the E4 and Dexcom recording spans. Readings
  outside the E4 span are excluded under §3.

## 3. Exclusions and quality rules

These are fixed now and applied identically in every experiment.

1. **CGM warm-up.** Drop the first 2 h of each participant's CGM record, and
   the first 2 h after any CGM gap longer than 2 h (G6 sensor warm-up).
2. **No E4 data.** Drop a reading if more than 50% of the samples of any E4
   signal in its 5-min window are missing. This is Karunarathna & Liang's rule.
3. **E4 validity rules** (from the stress paper; failing features are set to
   missing, the reading is kept):
   - EDA features: more than 50% of samples at least 0.05 µS;
   - TEMP features: more than 50% of samples in 20–40 °C;
   - pulse-rate features: interval coverage at least 0.5; HRV features:
     interval coverage at least 0.7.
4. **Food-log times between 00:00 and 05:00** are flagged and kept. The check
   showed that one participant (010) consistently eats breakfast at about
   04:30.
5. **MEAL features** are computed only for the 14 participants who passed the
   food-log/CGM alignment check. Participants 015 and 016 are excluded from
   every experiment that uses MEAL features. No offset is corrected.
6. Missing feature values are imputed with the training-fold median inside the
   model pipeline, as Karunarathna & Liang did.
7. **Data-integrity exclusion: minimum E4/CGM overlap [PROPOSED].** A
   participant is excluded from every registered experiment if fewer than
   **864 readings (72 h at 5-min sampling)** remain after rules 1 and 2, that
   is, readings with both a valid CGM value and usable E4 data. This is a
   data-integrity rule, not an outlier rule: it depends only on when the two
   devices were recording, never on glucose values or model performance.
   Reasons for the threshold: 72 h gives at least three full daily cycles,
   which the TIME features need; and BLOCKED-240 removes up to 8 h of
   training data around each of 5 test blocks, which leaves too little to
   train on in a short recording. The rule excludes one participant, 015
   (470 usable readings, about 39 h: its E4 recording starts two weeks before
   its CGM recording and ends two days before the CGM does). The next-lowest
   participant has 1,331 usable readings (about 111 h), so the result does not
   depend on the exact threshold between 470 and 1,331. Participant 015 is
   already excluded from MEAL experiments by rule 5, so E4 is unchanged; E1,
   E2, E3, E5 and E6 use 15 participants. EA6 repeats the analysis with 015
   included.

## 4. Feature sets

| Set | Contents | n features |
|---|---|---|
| PHYS | Stress-paper physiology on the 5-min window. EDA (9): tonic mean, SD, slope, min, max, range; SCR count; mean SCR amplitude; phasic area. BVP/IBI (6): mean pulse rate, SD of pulse rate, SDNN, RMSSD, pulse-amplitude SD, interval coverage. HR (1): mean device HR. TEMP (3): mean, SD, slope | 19 |
| ACT | ACC magnitude over the previous 2 h: min, max, mean (Karunarathna & Liang). ACC magnitude over the 5-min window: mean, SD | 5 |
| TIME | Minutes from midnight, plus its sine and cosine | 3 |
| ELAPSED | Minutes since the participant's first CGM reading. **A pure leakage probe with no physiological meaning** | 1 |
| MEAL | Minutes since the last logged meal event; carbohydrate and sugar over the previous 2, 8 and 24 h (14 participants) | 7 |
| ID | Sex and HbA1c. **ID+P** adds a one-hot participant indicator, used only under random splits, where it measures identity leakage | 2 (+16) |
| FULL-KL | Approximate re-implementation of Karunarathna & Liang: PHYS + ACT + TIME + sex, then random-forest importance on the training split only, keeping the top 30 (or all, if fewer) | ≤30 |
| FULL-B | Approximate re-implementation of Bent et al.: PHYS + ACT + TIME + MEAL + HbA1c + sex | 36 |

**[PROPOSED] Re-implementation scope.** Karunarathna & Liang built 236
features, 87 of them per signal for HR and TEMP using five non-linear
libraries. Their code is not public. FULL-KL keeps their windows, their 2-h
activity, circadian and sex features, their feature-selection step and their
evaluation, but uses the stress-paper physiology. E1 therefore approximates
the published result rather than reproducing it. This is stated in advance,
as it was in the stress paper.

## 5. Models

- **Primary:** XGBoost regression. **Secondary:** ridge regression.
- **Baselines:** the population mean (training-fold mean), and the
  participant mean (personalised split, EA2 only).
- **Pipeline:** median imputation, then standard scaling, then the regressor,
  fitted on training data only.
- **[PROPOSED] Grids** (Appendix Table A1 style):
  - XGBoost: depth {3, 6}; trees {100, 300}; learning rate {0.05, 0.1};
    subsampling 0.8.
  - Ridge: α {0.1, 1, 10, 100}.
- **Inner CV:** grouped 5-fold by participant for every participant-held-out
  or blocked experiment (E2, E4, E5, E6). The RANDOM experiments (E1, E3)
  use ungrouped 5-fold CV, as published, so that E3's shortcut models are
  tuned the same way as the model they are compared with.
- **Seeds:** random-split experiments are repeated with **20 seeds** (as
  published). Participant-held-out experiments use one seed per fold. The
  seeds are 0–19.
- **Secondary model use:** ridge regression is run for E2 (FULL-KL, LOPO)
  and E4 (FULL-B, LOPO) and reported descriptively. The registered tests use
  XGBoost.
- **Analysis code:** `code/experiments.py` implements this plan. Before
  filing, it was checked only with `--self-test`, which replaces glucose
  with random noise. It refuses to run on real glucose without an OSF DOI.

## 6. Splits

| Name | Definition |
|---|---|
| RANDOM | Readings pooled across participants, then a random 80/20 split (Karunarathna & Liang). 20 seeds |
| LOPO | Leave one participant out: 16 folds (14 for MEAL sets) |
| BLOCKED-b | Within each participant, split the recording into 5 contiguous blocks. Each block is the test set once, and training readings within *b* minutes of the test block are removed. *b* ∈ {0, 30, 60, 120, 240}. Inputs exclude ELAPSED and ID+P |

## 7. Registered experiments and hypotheses

| Exp | Question | Comparison | Hypothesis and decision rule |
|---|---|---|---|
| E1 | Does the approximate re-implementation reach the published R² 0.73? | FULL-KL, XGBoost, RANDOM, 20 seeds | Descriptive. **[PROPOSED]** "Approximately reproduced" if the mean R² is at least 0.63 (within 0.10). If not, the reasons are discussed, and E2 and E3 are still interpreted *relative to E1* |
| E2 | Does R² fall when participants are held out? | FULL-KL: RANDOM vs LOPO | **H1:** R²(RANDOM) − R²(LOPO) > **0.30 [PROPOSED]**. Supported if the lower one-sided 95% bootstrap bound exceeds 0.30 |
| E3 | Can shortcuts alone match the full model under the leaky split? | RANDOM: TIME+ID+P, ELAPSED+ID+P and ID+P alone vs FULL-KL | **H2:** TIME+ID+P is non-inferior to FULL-KL within a margin of 0.05 in R². **H2b:** ELAPSED+ID+P is non-inferior to FULL-KL within 0.05. **H3:** ID+P R² > 0.5 × FULL-KL R² |
| E4 | Does wrist physiology add anything under honest evaluation? | LOPO, 14 MEAL participants: population mean; TIME+MEAL+ID; FULL-B | **H4:** RMSE(TIME+MEAL+ID) − RMSE(FULL-B) < **2.0 mg/dL [PROPOSED]**, i.e. physiology and activity improve RMSE by less than 2 mg/dL. Supported if the upper one-sided 95% bound is below 2.0. **H5:** R²(FULL-B) − R²(population mean) < **0.10 [PROPOSED]**, upper bound below 0.10 |
| E5 | Does the Clarke grid hide failure? | Clarke A+B% for the population-mean baseline under LOPO | **H6:** baseline A+B ≥ 90%. Supported if the lower one-sided 95% bound is at least 90% |
| E6 | Do adjacent readings leak information? | FULL-KL inputs without sex, BLOCKED-0 vs BLOCKED-60 | **H7:** R²(BLOCKED-0) − R²(BLOCKED-60) > 0. Supported if the lower one-sided 95% bound exceeds 0. The other buffers are reported descriptively |

**Why ELAPSED (H2b) was added [PROPOSED].** Under a random split of readings
taken every 5 min, the test readings sit between training readings from the
same participant a few minutes away. A model then needs only "who" and
"when" to interpolate. ELAPSED+ID+P carries no physiology and no
time-of-day biology, so if it matches FULL-KL, the published R² measures
temporal leakage. Clock time (H2) mixes leakage with real circadian effects,
so H2b is the cleaner test. The stress paper used the same probe ("elapsed
time alone").

**Guard on H2 and H2b [PROPOSED].** A non-inferiority test is trivially
passed when both arms are near zero: if FULL-KL itself has R² ≈ 0 under
RANDOM, any shortcut model is "within 0.05" of it. H2 and H2b are therefore
interpreted only if the lower one-sided 95% bootstrap bound of E1's R² exceeds
0.30. If it does not, H2 and H2b are reported as "not interpretable", their
p values stay in the Holm family (so the correction does not get easier), and
neither counts as support. A dry run of the analysis code on a noise target
(`--self-test`) showed this failure mode: H2 and H2b came out "supported" with
every R² near 0.

**Primary hypotheses [PROPOSED]:** H1, H2b and H4.

**Multiplicity:** the eight registered tests (H1, H2, H2b, H3, H4, H5, H6 and
H7) are corrected together with Holm–Bonferroni at a family-wise α of 0.05.
E1 is descriptive and is not tested.

## 8. Metrics and statistics

- **Metrics:** R² (pooled over all test readings of an experiment), RMSE,
  MARD, and Clarke error grid zones (Clarke et al., 1987), pooled and per
  participant.
- **Uncertainty:** 95% CIs and one-sided p values from **10,000 participant
  bootstrap resamples** (as in the stress paper). Each resample draws 15
  participants (or 14 for E4) with replacement, and the statistic is recomputed from
  those participants' test predictions. For RANDOM, a participant's test
  predictions are pooled across the 20 seeds.
- **Paired differences** (H1, H2, H2b, H3, H4, H5, H7) are computed within
  each bootstrap resample, so both arms use the same participants.
- **Non-inferiority and equivalence:** one-sided at the margins above. A
  failed non-inferiority test is reported as "not established", never as
  "inferior".
- With n = 15, every LOPO fold is also reported individually in a
  per-participant figure.

## 9. Exploratory analyses (labelled as such; not registered)

- **EA1:** SHAP attribution of FULL-KL under RANDOM vs LOPO.
- **EA2:** personalised models (first 50% / last 50% of each recording, as in
  Bent et al. 2021) vs the participant-mean baseline.
- **EA3:** CGM reliability ceiling. Dexcom G6 MARD gives an upper bound on
  achievable R².
- **EA4:** E4 repeated on all 15 participants retained under rule 7, without MEAL features, and
  FULL-B on 016 with the −3 h food-log shift that the alignment check
  suggested. Both are sensitivity analyses only.
- **EA5:** sex is the top feature in Karunarathna & Liang. Repeat E2 for
  FULL-KL without sex.
- **EA6 (pre-specified sensitivity analysis) [PROPOSED]:** repeat E1–E6 and
  all eight registered tests with rule 7 switched off, so that participant 015
  is included (16 participants; E4 still 14). Estimates, CIs and Holm p values
  are reported next to the primary ones in a supplementary table. EA6 does not
  replace the primary analysis and is not part of the Holm family. If any
  registered test's verdict differs between the two analyses, the Discussion
  says so.

## 10. Deviations

Any deviation from this plan will be reported in a dedicated table (as in the
stress paper's Appendix Table A2), with its reason and its effect on the
registered tests.

## Appendix: decisions co-authors must confirm before filing

| # | Decision | Proposed value | Basis |
|---|---|---|---|
| 1 | E1 reproduction criterion | mean R² ≥ 0.63 | Approximate re-implementation; same tolerance logic as the stress paper |
| 2 | H1 margin | 0.30 | Handover suggestion. Bent et al.'s LOPO RMSE (21 mg/dL) against Karunarathna & Liang's 11.9 implies a drop of this size or larger |
| 3 | Non-inferiority margins H2, H2b | 0.05 R² | Same margin as the stress paper's H2 |
| 4 | H4 margin | 2.0 mg/dL RMSE | About 2% of a typical 100 mg/dL reading; well below G6 sensor error (overall MARD 10.0%; Wadwa et al. 2018) |
| 5 | H5 margin | 0.10 R² | Judgement: an R² gain below 0.10 over a constant prediction is not useful for estimation |
| 6 | Primary hypotheses | H1, H2b, H4 | One per claim: leakage size, leakage mechanism, physiology's added value |
| 7 | ELAPSED probe (H2b) | Add | See §7 |
| 8 | MEAL exclusions | 015, 016 | `results/time_of_day/` |
| 9 | XGBoost grid | depth {3,6}, trees {100,300}, lr {0.05,0.1} | Stress-paper grid with deeper trees for a regression on about 28,000 readings |
| 10 | Guard on H2, H2b | Interpret only if E1 R² lower bound > 0.30 | Prevents a trivial pass when every model is near R² = 0 (seen in the noise-target dry run) |
| 11 | Data-integrity exclusion (§3 rule 7) | ≥ 864 usable readings (72 h); excludes 015; sensitivity analysis EA6 with 015 | 015 has 470 usable readings; next lowest 1,331. Rule written after seeing coverage counts, not outcomes, and disclosed in §1 |
