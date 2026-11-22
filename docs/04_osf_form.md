# OSF Preregistration template: paste-ready text

Source: `docs/02_preregistration_draft.md` (this branch), mapped onto the
pages of the current OSF "OSF Preregistration" form: Metadata, Overview,
Research Design, Sampling, Variables, Analysis Plan, then Other. Field names
inside a page may be worded differently on OSF; match by meaning. Values marked [PROPOSED]
in the draft are written here as fixed values. **Filing commits the team to
all eleven decisions in the draft's appendix.** Paste the text under each
heading into the OSF field of the same name. E-mail addresses are left out on
purpose; add them in OSF's contributor settings, not in these fields.

Analysis code at registration: `code/experiments.py` in
https://github.com/MohannadBanat/bigideas-glucose-audit, commit
08829e9e58a98d8e09cdc87ae5d7562e9eb61aca (22 Nov 2026). Upload a copy of
`docs/02_preregistration_draft.md` and `code/experiments.py` to the OSF
registration as files, so the plan does not depend on GitHub.

---

## 1. Metadata

### Title

Time and Identity Shortcuts in Wrist-Wearable Glucose Estimation: A Pre-Registered Re-Evaluation of the BIG IDEAs Dataset

### Contributors (add in OSF's contributor field, in this order)

Mohannad Banat (1), Hamza Abu Owida (1), Ayoub Alsarhan (2), Dimah Al-Fraihat (3), Abdulmohsen Algarni (4)

(1) Department of Medical Engineering, Faculty of Engineering, Al-Ahliyya Amman University, Amman 19328, Jordan
(2) Department of Information Technology, Faculty of Prince Al-Hussien bin Abdullah, The Hashemite University, Zarqa 13133, Jordan
(3) Department of Software Engineering, Faculty of Information Technology, Isra University, Amman 11622, Jordan
(4) Department of Computer Science, King Khalid University, Abha 61421, Saudi Arabia

### Description

A recent study (Karunarathna and Liang, Sensors 2025, 25, 3207) reported that interstitial glucose can be estimated from an Empatica E4 wristband with R² = 0.73 on the public BIG IDEAs dataset (16 adults, Dexcom G6 CGM, about 8–10 days each). Its evaluation split individual 5-min readings at random into training and test sets, so the same participants, and readings minutes apart, appear on both sides of the split. This study re-implements that model approximately and re-evaluates it. It asks (1) how much of the reported accuracy survives when participants are held out, (2) whether models that see only clock time, elapsed time or participant identity match the full model under the published random split, (3) what wrist physiology and activity add to time, meal and demographic information when participants are held out, (4) whether the Clarke error grid separates working models from a constant prediction, and (5) whether readings adjacent in time leak information. It is a secondary analysis of existing public data. No glucose-estimation model has been trained by the authors on this dataset before registration.

### Tags (suggested)

continuous glucose monitoring; wearable sensors; Empatica E4; data leakage; shortcut learning; cross-validation; leave-one-participant-out; BIG IDEAs

---

## 2. Overview

### Research questions

As in the Description: (1) leakage size under participant hold-out, (2) whether time-only or identity-only shortcut models match the full model under the published random split, (3) what wrist physiology adds under honest evaluation, (4) whether the Clarke grid separates working models from a constant prediction, (5) temporal leakage between adjacent readings.

### Hypotheses

Eight registered tests, all one-sided, corrected together with Holm–Bonferroni at a family-wise alpha of 0.05. Primary hypotheses: H1, H2b and H4. "Bound" means the one-sided 95% participant-bootstrap bound.

- H1 (E2, leakage size): for the full model (FULL-KL, XGBoost), R² under the random split minus R² under leave-one-participant-out (LOPO) is greater than 0.30. Supported if the lower bound exceeds 0.30.
- H2 (E3): under the random split, a model using only clock time plus sex, HbA1c and a participant indicator (TIME+ID+P) is non-inferior to FULL-KL within 0.05 in R². Supported if the upper bound of R²(FULL-KL) − R²(TIME+ID+P) is below 0.05.
- H2b (E3, leakage mechanism): the same with elapsed time since the start of the recording instead of clock time (ELAPSED+ID+P). Elapsed time has no physiological meaning, so non-inferiority would show that the random-split R² measures temporal leakage.
- H3 (E3): under the random split, R²(ID+P alone) is greater than half of R²(FULL-KL). Supported if the lower bound of R²(ID+P) − 0.5 × R²(FULL-KL) exceeds 0.
- Guard on H2, H2b and H3: these three are interpreted only if the lower bound of the E1 R² (FULL-KL, random split) exceeds 0.30. Otherwise they are reported as "not interpretable", stay in the Holm family, and count as no support. Reason: each passes trivially when the full model has learned nothing.
- H4 (E4, primary): under LOPO in the 14 participants with usable meal data, RMSE(TIME+MEAL+ID) − RMSE(FULL-B) is less than 2.0 mg/dL, i.e. adding wrist physiology and activity improves RMSE by less than 2 mg/dL. Supported if the upper bound is below 2.0.
- H5 (E4): under LOPO, R²(FULL-B) − R²(training-mean baseline) is less than 0.10. Supported if the upper bound is below 0.10.
- H6 (E5): under LOPO, a constant prediction (training-fold mean) puts at least 90% of readings in Clarke zones A+B. Supported if the lower bound is at least 90%.
- H7 (E6): within-participant blocked cross-validation with no buffer gives a higher R² than with a 60-min buffer between training and test blocks. Supported if the lower bound of R²(BLOCKED-0) − R²(BLOCKED-60) exceeds 0.

E1 (descriptive, not tested): the approximate re-implementation is called "approximately reproduced" if its mean R² over 20 random splits is at least 0.63 (within 0.10 of the published 0.73). Whatever E1 shows, E2 and E3 are interpreted relative to E1.

---

## 3. Research Design

### Study type

Observational Study (secondary analysis of an existing public dataset; no new data are collected).

### Blinding

No blinding is involved in this study.

### Is there any additional blinding in this study?

The analysis code was written and tested before registration on a synthetic target: with the `--self-test` option, every glucose value is replaced by random noise, so the code could be checked without producing any real result. The script refuses to run on real glucose unless an OSF registration DOI is supplied.

### Study design

Within-dataset comparison of evaluation schemes and feature sets for the same estimation task (CGM glucose from wrist signals, one sample per CGM reading).

Factors:
- Evaluation scheme: RANDOM (readings pooled across participants, random 80/20 split, 20 seeds, 0–19, as published); LOPO (each participant is the test set once); BLOCKED-b (each participant's recording cut into 5 contiguous blocks, each block the test set once, training readings within b minutes of the test block removed, b in {0, 30, 60, 120, 240}).
- Feature set: PHYS, ACT, TIME, ELAPSED, MEAL, ID, ID+P, FULL-KL, FULL-B (defined under Variables).
- Model: XGBoost regression (primary), ridge regression (secondary, descriptive), training-mean baseline.

Experiments:
- E1: FULL-KL, XGBoost, RANDOM (descriptive).
- E2: FULL-KL, RANDOM vs LOPO (H1).
- E3: RANDOM; TIME+ID+P, ELAPSED+ID+P and ID+P alone vs FULL-KL (H2, H2b, H3).
- E4: LOPO, 14 participants; training mean vs TIME+MEAL+ID vs FULL-B (H4, H5).
- E5: Clarke zones of the training-mean baseline under LOPO (H6).
- E6: FULL-KL inputs without sex, BLOCKED-b (H7 compares b = 0 with b = 60; other buffers descriptive).

### Randomization

The 80/20 random splits use seeds 0–19 (one random draw per reading, numpy default_rng). The participant bootstrap uses seed 20261122. Model training uses the split's seed. No participants are randomized to anything.

---

## 4. Sampling

### Existing data

Registration prior to analysis of the data.

### Explanation of existing data

The data are the public PhysioNet BIG IDEAs Lab Glycemic Variability and Wearable Device Data, version 1.1.3 (doi 10.13026/aw6y-fc44). They exist, were downloaded, and were loaded and quality-checked before registration. Full disclosure of what the authors saw:

1. The dataset documentation and the article by Karunarathna and Liang (2025), including its methods and reported results.
2. The food log of participant 001, read to check that clock times are plausible.
3. A food-log/CGM alignment check (`code/check_time_of_day.py`, run on 22 Nov 2026). It read the food logs, the Dexcom glucose values and the demographics file for all 16 participants. It computed the mean glucose rise in the 2 h after logged meals against random times, and re-computed it with the meal times shifted, to test whether logged meal times line up with the CGM. It showed that clock time is preserved by the dataset's date shifting, that food log and CGM agree for 14 of 16 participants (015: the food log lies outside the CGM recording; 016: no glucose rise at the logged meal times), and that the cohort is 9 female and 7 male with HbA1c 5.3–6.4%. It also displayed mean CGM glucose by clock hour. This is an analysis of glucose values, but for data quality only; it fits no estimation model. One rule of this check (which day-shifts are compared) was changed after its first run, because shifts that kept very few meal events flagged three otherwise aligned participants; the change is documented with the check. The exclusion of 015 and 016 from meal features (see Data exclusion) was decided from this check's output.
4. Per-participant reading counts from the feature build (`code/features.py`, 22 Nov 2026): how many CGM readings fall in the sensor warm-up, how many have no usable E4 data, and how many remain. These counts use only the timing of the E4 and Dexcom records. They showed that participant 015 has 470 usable readings, against at least 1,331 for every other participant. The minimum-overlap exclusion rule (rule 7 under Data exclusion) was written after these counts were known, and it excludes only 015. A pre-specified sensitivity analysis (EA6) repeats every registered test with 015 included.
5. The feature tables contain the glucose target, but its values were not summarised, plotted or modelled. The analysis code was run only on a synthetic noise target.

No glucose-estimation model has been trained or evaluated by the authors on any version of this dataset, and no model has seen real glucose values.

### Data collection procedures

No new data are collected. The dataset (Bent et al., npj Digital Medicine 2021; PhysioNet) contains, for each of 16 adults with normal or prediabetic HbA1c, about 8–10 days of free-living data: Dexcom G6 interstitial glucose every 5 min, Empatica E4 wristband signals (BVP 64 Hz, EDA and skin temperature 4 Hz, 3-axis accelerometry 32 Hz, heart rate 1 Hz, inter-beat intervals), a food log, and sex and HbA1c. Food logs, Dexcom files and demographics are downloaded from physionet.org; E4 files are taken from the PhysioNet AWS mirror (version 1.1.2, whose E4 and Dexcom files are byte-identical to 1.1.3). Every file is checked against the v1.1.3 SHA-256 checksums.

### Sample size

16 participants in the dataset; 15 in the primary analyses after the data-integrity exclusion (14 in experiments that use meal features). 36,898 Dexcom readings in total; 28,404 remain after the warm-up and missing-E4 rules, and 27,934 after the data-integrity exclusion.

### Sample size rationale

Fixed by the public dataset. There is no power analysis. With 15 participants, participant-level intervals are wide, so the hypotheses use pre-set margins and one-sided bounds, and every LOPO fold is reported individually.

### Stopping rule

Not applicable; all available data are analysed once.

---

## 5. Variables

### Manipulated variables

None. The evaluation scheme (RANDOM, LOPO, BLOCKED-b) and the feature set are analytic factors, defined under Study design and Indices.

### Measured variables

- Outcome: Dexcom G6 interstitial glucose of each CGM reading, in mg/dL. Earlier CGM values are never used as inputs, so the task is estimation, not forecasting.
- Predictors: Empatica E4 BVP, inter-beat intervals, EDA, skin temperature, accelerometry and device heart rate in windows before each reading; clock time of the reading; minutes since the participant's first CGM reading; food-log meal times and carbohydrate and sugar amounts; sex; HbA1c; participant identity.

### Indices

Feature windows: the 5 min before each CGM timestamp (as in Karunarathna and Liang), and the 2 h before it for long activity features.

- PHYS (19): EDA (9): tonic mean, SD, slope, minimum, maximum, range; SCR count (peak prominence at least 0.05 µS); mean SCR amplitude; phasic area. BVP/IBI (6): mean pulse rate, pulse-rate SD, SDNN, RMSSD, pulse-amplitude SD, interval coverage. HR (1): mean device heart rate. Skin temperature (3): mean, SD, slope.
- ACT (5): accelerometer magnitude over the previous 2 h (minimum, maximum, mean) and over the 5-min window (mean, SD).
- TIME (3): minutes from midnight, with its sine and cosine.
- ELAPSED (1): minutes since the participant's first CGM reading (a leakage probe with no physiological meaning).
- MEAL (7): minutes since the last logged meal; carbohydrate and sugar over the previous 2, 8 and 24 h. Computed only for the 14 participants who passed the alignment check.
- ID (2): sex and HbA1c. ID+P adds a one-hot participant indicator, used only under random splits.
- FULL-KL: approximate re-implementation of Karunarathna and Liang: PHYS + ACT + TIME + sex, followed by random-forest importance on the training data only, keeping the top 30 features (or all, if fewer). Their 236 features and code are not public, so this approximates rather than reproduces the published model.
- FULL-B (36): PHYS + ACT + TIME + MEAL + sex + HbA1c (approximate re-implementation of Bent et al. 2021).

Metrics: R² (pooled over all test readings of an experiment), RMSE, MARD, and Clarke error grid zones (Clarke et al. 1987), pooled and per participant.

---

## 6. Analysis Plan

### Statistical models

Pipeline, fitted on training data only: median imputation, standard scaling, then the regressor.
- XGBoost regression (primary). Grid: maximum depth {3, 6}; trees {100, 300}; learning rate {0.05, 0.1}; subsampling 0.8.
- Ridge regression (secondary; reported descriptively for E2 and E4). Grid: alpha {0.1, 1, 10, 100}.
- Baseline: training-fold mean glucose.

Hyperparameters are tuned by inner 5-fold cross-validation: grouped by participant for E2, E4, E5 and E6; ungrouped for the random-split experiments E1 and E3, as published, so that E3's shortcut models are tuned the same way as the model they are compared with. Random-split experiments are repeated with 20 seeds; participant-held-out experiments use one fit per fold.

### Transformations

Signal processing for the features listed under Indices: EDA low-pass filtered and split into tonic and phasic parts; SCRs detected as phasic peaks with prominence at least 0.05 µS; pulse rate and HRV from E4 inter-beat intervals; accelerometer magnitude per second. Missing values are imputed with the training-fold median inside the pipeline. No transformation of the glucose target.

### Inference criteria

- Uncertainty: 95% confidence intervals and one-sided p values from 10,000 participant-bootstrap resamples. Each resample draws 15 participants (14 for E4) with replacement and recomputes the statistic from their test predictions. For random splits, a participant's test predictions are pooled across the 20 seeds.
- Paired comparisons (H1, H2, H2b, H3, H4, H5, H7) are recomputed within each resample, so both arms use the same participants.
- The one-sided p value is the share of resamples on the null side of the margin.
- Holm–Bonferroni over the eight tests (H1, H2, H2b, H3, H4, H5, H6, H7) at a family-wise alpha of 0.05. Primary hypotheses: H1, H2b, H4.
- The guard described under Hypotheses applies to H2, H2b and H3.
- A failed non-inferiority test is reported as "not established", never as "inferior".

### Data exclusion

Applied identically in every experiment:
1. CGM warm-up: the first 2 h of each CGM record, and the first 2 h after any CGM gap longer than 2 h, are dropped.
2. Missing E4 data: a reading is dropped if more than 50% of the samples of any E4 signal in its 5-min window are missing (Karunarathna and Liang's rule).
3. E4 validity (features set to missing, reading kept): EDA features need more than 50% of samples at least 0.05 µS; temperature features need more than 50% of samples within 20–40 °C; pulse-rate features need inter-beat interval coverage at least 0.5; HRV features at least 0.7.
4. Food-log entries between 00:00 and 05:00 are flagged and kept (one participant, 010, consistently eats breakfast at about 04:30).
5. Meal features are computed only for the 14 participants who passed the food-log/CGM alignment check; 015 and 016 are excluded from every experiment that uses meal features. No time offset is corrected.
6. (see Missing data)
7. Data-integrity exclusion (minimum E4/CGM overlap): a participant is excluded from every registered experiment if fewer than 864 readings (72 h at 5-min sampling) remain after rules 1 and 2. The rule depends only on when the two devices were recording, never on glucose values or model performance. Reasons: 72 h gives at least three full daily cycles, which the time features need, and the BLOCKED-240 scheme removes up to 8 h of training data around each of 5 test blocks. It excludes one participant, 015 (470 usable readings, about 39 h, because its E4 recording starts two weeks before its CGM recording and ends two days before it). The next-lowest participant has 1,331 usable readings, so any threshold between 470 and 1,331 gives the same result. This rule was written after the per-participant reading counts were known (see Explanation of existing data). Sensitivity analysis EA6 repeats every registered test with this rule switched off.

### Missing data

Missing feature values (from rule 3 above, or from gaps inside a window) are imputed with the training-fold median inside the model pipeline, as in Karunarathna and Liang. Readings with no usable E4 data are excluded by rule 2. Missing glucose values are not imputed; readings exist only where the CGM recorded.

### Exploratory analysis

Not registered tests, not corrected for multiplicity, and labelled as exploratory:
- EA1: SHAP attribution of FULL-KL under random vs LOPO evaluation.
- EA2: personalised models (first 50% / last 50% of each recording, as in Bent et al. 2021) vs a participant-mean baseline.
- EA3: CGM reliability ceiling: the Dexcom G6 error (overall MARD 10.0%; Wadwa et al. 2018) as an upper bound on achievable R².
- EA4: E4 repeated on the 15 retained participants without meal features; and FULL-B for participant 016 with the −3 h food-log shift that the alignment check suggested. Sensitivity analyses only.
- EA5: E2 repeated for FULL-KL without sex (the top feature in Karunarathna and Liang).
- EA6 (pre-specified sensitivity analysis): E1–E6 and all eight registered tests repeated with the data-integrity exclusion switched off, so that participant 015 is included (16 participants; E4 still 14). Estimates, intervals and Holm p values are reported next to the primary ones. EA6 does not replace the primary analysis and is not part of the Holm family. If any registered verdict differs between the two analyses, the Discussion says so.

---

## 7. Other (if the form has a final page or an "Other" field)

### Other

- Analysis code: https://github.com/MohannadBanat/bigideas-glucose-audit (`code/experiments.py`, commit 08829e9e58a98d8e09cdc87ae5d7562e9eb61aca). Copies of the code and of the full plan are uploaded with this registration.
- Dry runs of the analysis code on a synthetic noise target showed that H2, H2b and H3 could pass trivially when no model learns anything; the guard on these three hypotheses was added for that reason before registration.
- This registration follows the structure of the authors' earlier registration (OSF swge8; published as Abu Owida et al., Sensors 2026, 26, 7340).
- Any deviation from this plan will be reported in a deviations table with its reason and its effect on the registered tests.
- Key references: Karunarathna and Liang, Sensors 2025, 25, 3207; Bent et al., npj Digital Medicine 2021; Clarke et al., Diabetes Care 1987; Holm, Scandinavian Journal of Statistics 1979; Wadwa et al., Diabetes Technology & Therapeutics 2018.
