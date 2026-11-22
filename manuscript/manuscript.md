---
title: "Time and Identity Shortcuts in Wrist-Wearable Glucose Estimation: A Pre-Registered Re-Evaluation of the BIG IDEAs Dataset"
journal: Sensors (MDPI), Article
status: "PRE-RESULTS DRAFT, 22 Nov 2026. Sections 1, 2 and 6 are complete drafts. Results, Discussion and Abstract contain placeholders, marked [RESULT], that are filled only after the OSF registration is filed and the registered analyses are run."
bibliography: ../references/references.bib
---

<!--
Authoring rules for this file
- Every number in Sections 3-5 must be copied from a file under results/ that a script wrote.
- [RESULT: ...] marks text that depends on the registered analyses. Do not fill it in before the OSF DOI exists.
- Citations use [@key] from references/references.bib; all keys were checked against Crossref or arXiv on 22 Nov 2026.
- The text is written new for this paper. Methods shared with Abu Owida et al. (2026) are described in new words and cited, not copied.
-->

<!-- Author order from M. Banat, 22 Nov 2026. Names and affiliations copied from
Abu Owida et al., Sensors 2026, 26(22), 7340 (doi 10.3390/s26227340), where all
five authors appear. Re-check each affiliation with its author before submission. -->

**Authors:** Mohannad Banat ^1^, Hamza Abu Owida ^1^, Ayoub Alsarhan ^2^, Dimah Al-Fraihat ^3^ and Abdulmohsen Algarni ^4^

^1^ Department of Medical Engineering, Faculty of Engineering, Al-Ahliyya Amman University, Amman 19328, Jordan

^2^ Department of Information Technology, Faculty of Prince Al-Hussien bin Abdullah, The Hashemite University, Zarqa 13133, Jordan

^3^ Department of Software Engineering, Faculty of Information Technology, Isra University, Amman 11622, Jordan

^4^ Department of Computer Science, King Khalid University, Abha 61421, Saudi Arabia

\* Correspondence: [TODO: corresponding author(s) and e-mail address(es) to be agreed; in Abu Owida et al. (2026) they were H. Abu Owida and A. Algarni]

## Abstract

Wrist-worn wearables are often reported to estimate interstitial glucose
accurately, but most reports validate on random splits of readings, so the
same people, and often the same hours, appear in training and test data. We
re-evaluated glucose estimation on the public BIG IDEAs dataset (16 adults,
Dexcom G6 and Empatica E4, 8–10 days of free-living data) under an analysis
plan registered before any model was trained. We re-implemented a published
model that reported R² = 0.73 [@karunarathna_glucose_2025]. We then compared
random and leave-one-participant-out evaluation, tested models that see only
clock time, elapsed time or participant identity, measured what wrist
physiology adds to time, meal and demographic information, and checked
whether the Clarke error grid separates working models from a constant
prediction. [RESULT: two to three sentences giving the registered results,
with confidence intervals.] [RESULT: one sentence on the implication.]
Estimates of glucose from wrist wearables should be validated on
participants and periods the model has not seen, and compared against
shortcut-only baselines.

**Keywords:** continuous glucose monitoring; wearable sensors; data leakage;
shortcut learning; cross-validation; Empatica E4; pre-registration;
reproducibility

## 1. Introduction

Continuous glucose monitors (CGMs) measure interstitial glucose through a
filament under the skin. The sensors must be replaced every week or two, and
their cost limits use outside diabetes care. Wrist-worn devices that record
heart rate, skin temperature, electrodermal activity (EDA) and movement are
cheaper and non-invasive. Several studies have therefore asked whether
these signals can stand in for a CGM, at least among people with
high-normal glucose or prediabetes, for whom early feedback could support
lifestyle change [@bent_digital_2021; @dunn_wearables_2021].

The publicly available BIG IDEAs dataset made this question testable
[@cho_bigideas_2026; @pollard_physionet_2026]. It pairs a Dexcom G6 CGM with
an Empatica E4 wristband and a food log for 16 adults over 8–10 days of
ordinary life. The dataset authors predicted CGM glucose with a
gradient-boosted model evaluated by leave-one-person-out cross-validation
(LOPO) and reported a root mean squared error (RMSE) of 21.22 ± 4.14 mg/dL
[@bent_digital_2021]. More than a third of the model's feature importance
came from the food log, and a further 10.8% from user-entered variables
such as sex and HbA1c [@bent_digital_2021]. A later study in *Sensors*
removed food logs and used only passively recorded signals, circadian
features and biological sex. It reported R² = 0.73, an RMSE of 11.9 mg/dL
and 99.4% of predictions in Clarke zones A and B
[@karunarathna_glucose_2025]. That study evaluated its models on "an 80/20
train–test split" of 26,380 five-minute epochs, repeated over 20 random
seeds, and does not state whether participants were kept apart. Its most
important feature was biological sex [@karunarathna_glucose_2025].

The two results differ by almost a factor of two in RMSE, and the
difference matters. If readings are split at random, the test set holds
readings taken minutes before or after training readings from the same
person. Clinical machine learning has long warned that such record-wise
splits overstate how well a model works for a new person
[@saeb_usecase_2017; @little_cv_2017]. Leakage between training and test
data is now recognised as a common cause of irreproducible results across
fields that use machine learning [@kapoor_leakage_2023]. A related problem
is shortcut learning, in which a model reaches high accuracy through a cue
that is correlated with the target in the data but is not the mechanism of
interest [@geirhos_shortcut_2020]. Two shortcuts are plausible in wearable
glucose data. With 16 people, sex and a few slowly varying signals can
nearly identify the person, and person-level mean glucose then explains
part of the variance. Clock time carries the daily rhythm of meals, which
drives much of the variation in glucose.

Ramesh et al. recently re-assessed estimation of glucose from
photoplethysmography (PPG) on two clinical datasets. Models that looked
competitive under random window-level splits fell to an R² near or below
zero when participants were held out. In every model and split, including
a constant mean prediction, more than 90% of predictions fell in Clarke
zones A and B [@ramesh_reassessing_2026]. Their study did not use BIG
IDEAs, free-living multimodal wrist data, leave-one-participant-out
evaluation, controls for time or identity, or a registered analysis plan.
Reproducibility problems have also been documented for deep-learning
forecasting of glucose from past CGM values in type 1 diabetes, which is a
different task from estimation [@lu_reproducibility_2026]. In earlier work,
our group used a pre-registered design with explicit shortcut controls to
show that a wearable stress detector raised alarms through most exercise
sessions [@abuowida_stress_2026]. Here we apply the same discipline to
glucose estimation.

This paper makes four contributions. (i) It is a participant-level
re-evaluation of glucose estimation on BIG IDEAs, with the analysis plan
registered before any model was trained [OSF DOI: RESULT]. (ii) It tests
shortcut-only models: clock time alone, elapsed time with participant
identity, and identity alone. We found no such controls in the published
work on this dataset. (iii) It measures what wrist physiology adds to time,
meal and demographic information when participants are held out. (iv) It
reports a data-quality check that is a precondition for meal-based
features: in the current release, the food logs of two participants do not
line up with their CGM recordings. We do not claim to be the first to show
that random splits inflate estimates of glucose from wearables. Ramesh et
al. showed this for clinical PPG [@ramesh_reassessing_2026]. Our
contribution is to identify *what* the inflated models use, in free-living
multimodal data, under a registered plan.

## 2. Materials and Methods

The analysis plan, including hypotheses, margins, exclusions, models and
statistics, was registered on the Open Science Framework (OSF) on [RESULT:
date; DOI] before any model was fitted. Section 2.9 lists what the authors
had seen before registration. Deviations are reported in Appendix B.

### 2.1. Dataset

We used version 1.1.3 of the BIG IDEAs Lab Glycemic Variability and
Wearable Device Data [@cho_bigideas_2026], which is openly available on
PhysioNet [@pollard_physionet_2026] under the Open Data Commons Attribution
licence. Sixteen adults aged 35–65 years with high-normal glucose or
prediabetes wore a Dexcom G6 CGM and an Empatica E4 wristband for 8–10 days
and logged their food intake [@bent_digital_2021]. The CGM reports
interstitial glucose every 5 min. The E4 records blood volume pulse (BVP)
at 64 Hz, EDA and skin temperature at 4 Hz, and three-axis acceleration
(ACC) at 32 Hz. It also derives heart rate (HR) at 1 Hz and inter-beat
intervals (IBI) on the device. `Demographics.csv` lists 9 female and 7 male
participants, with HbA1c between 5.3% and 6.4%. PhysioNet shifts all dates
to protect identity. Version 1.1.3 differs from version 1.1.2 only in four
food-log files (participants 007, 013, 015 and 016). The E4 and Dexcom files
of the two versions are byte-identical (comparison of the published SHA-256
checksums), so the E4 files were taken from the PhysioNet mirror of v1.1.2
and verified against the v1.1.3 checksums. The study by Karunarathna and
Liang used v1.1.2 [@karunarathna_glucose_2025].

### 2.2. Food-Log and CGM Alignment Check

Meal-based features are valid only if the food log and the CGM share a
clock. Before registration we therefore tested, for each participant,
whether logged meals are followed by a rise in glucose. Food entries
within 30 min of each other were merged into one meal event, and events
with less than 10 g of carbohydrate were ignored. For each event we
computed the *meal rise*: the highest glucose value in the 2 h after the
logged time minus the mean glucose in the 15 min before it. A participant
passed if four conditions held. (a) At least 80% of meal events fell inside
the CGM recording. (b) The mean meal rise exceeded that at random times in
the same recording (2000 permutations, p < 0.05). (c) Shifting all meal
times by whole days (−21 to +21 days) did not give a larger mean rise than
a shift of zero. Only shifts that kept at least half the events were
compared. (d) The best shift within ±12 h was within 60 min of zero.

Fourteen participants passed (Figure 1). For them, the mean meal rise was
28.8–47.1 mg/dL, against 11.8–22.3 mg/dL at random times, and the best
shift lay between −30 and +15 min. Two participants failed. For participant
015, the food log covers 5–13 July (shifted dates) while the CGM covers
19–27 July, so no logged meal falls inside the recording. For participant
016, the rise at logged meals (19.6 mg/dL) did not differ from that at
random times (19.1 mg/dL; p = 0.45). Its largest rise came from a shift of
−3 h, but the offset could not be confirmed, so it was not corrected.
Meal-based features were therefore registered for the 14 aligned
participants only (Section 2.4).

The same check, run on the version 1.1.2 food logs of the four participants
whose logs changed in version 1.1.3, explains the problem. In version
1.1.2, none of these four logs overlapped its CGM recording: each began
about 5 months before the CGM data. Their version 1.1.1 files are
byte-identical to version 1.1.2. Version 1.1.3 fully realigned 007 and 013.
It moved 016 into the recording window, but with no detectable meal
response, and it left 015 outside the window
(`results/food_log_versions/`). Miyakoshi and Ito related postprandial
glucose to logged nutrients using version 1.1.1 [@miyakoshi_glucose_2024].
For four of the 16 participants, that version's food logs did not overlap
the CGM data at all.

Clock time itself appears preserved by the date shift. In 15 of 16 participants, the first food entry of the day falls
between 05:00 and 11:00 (median per participant). The exception,
participant 010, logs the same breakfast at about 04:30 on six days, and
the CGM confirms meals at those times.

![Figure 1. Mean glucose rise in the 2 h after logged meals, recomputed after shifting all logged meal times of a participant by −12 to +12 h (one panel per participant). The dashed line is the same statistic at random times in the same recording. For aligned participants the curve peaks at a shift near zero. For 015, no logged meal falls inside the CGM recording. For 016, there is no peak at zero.](../results/time_of_day/fig_lag_sweep_minutes.png)

### 2.3. Pre-Processing and Exclusions

Each CGM reading is one sample, and its value in mg/dL is the target. CGM
values from earlier times were never used as inputs, which keeps the task
one of estimation rather than forecasting. We excluded the first 2 h of
each CGM record, and the first 2 h after any gap longer than 2 h, to remove
sensor warm-up. Following Karunarathna and Liang
[@karunarathna_glucose_2025], a reading was excluded if, in the 5 min before
it, more than half of the expected samples were missing for any of the
ACC, BVP, EDA, skin-temperature or HR signals.

One data-integrity rule applied at the level of participants. A participant
was excluded from all registered experiments if fewer than 864 readings
(72 h at 5-min sampling) had both a CGM value and usable E4 data after the
two rules above. The rule depends only on when the two devices were
recording, not on glucose values or model performance. It guarantees at
least three full daily cycles per participant, and enough training data
around each test block in the BLOCKED-240 scheme, which removes up to 8 h
around every test block. Only participant 015 failed it: 470 usable readings
(about 39 h), because its E4 recording started two weeks before its CGM
recording and ended two days before it. The next-lowest participant had
1331 usable readings. The threshold was set before registration but after
the per-participant reading counts had been seen (Section 2.9). A
pre-specified sensitivity analysis repeats every registered test with 015
included (EA6, Section 2.8). The main analyses therefore use 15 participants,
and 14 when MEAL features are used, since 015 also failed the alignment
check.

Validity rules for individual features were fixed in the registration.
Values that broke a rule were set to missing, and the reading was kept.

- EDA features required more than half of the window's samples to be at
  least 0.05 µS.
- Skin-temperature features required more than half of the samples to lie
  between 20 and 40 °C.
- Pulse-rate features required inter-beat intervals covering at least half
  of the window. Heart-rate-variability features required at least 70%.

Missing values were imputed with the median of the training fold inside the
model pipeline. [RESULT: numbers of readings before and after each
exclusion, per participant, from `features_log.csv`.]

### 2.4. Features

All window-based features use the 5 min before the CGM timestamp, unless
stated otherwise.

**Physiology (PHYS; 19 features).**

- *EDA (9).* Each contiguous EDA segment was low-pass filtered (fourth-order
  Butterworth, 1 Hz, zero phase). The tonic component was taken as a further
  0.05 Hz low-pass of the filtered signal, and the phasic component as the
  difference between them. Skin-conductance responses (SCRs) were peaks of
  the phasic component with a prominence of at least 0.05 µS, at least 1 s
  apart. A prominence of 0.01 µS gave about 6 SCRs per minute in
  participant 001, which we judged to be noise. The nine features are the
  mean, standard deviation (SD), slope, minimum, maximum and range of the
  tonic component; the SCR count; the mean SCR amplitude; and the area of
  the positive phasic component.
- *Pulse (6).* Computed from the E4's inter-beat intervals: mean and SD of
  pulse rate; SDNN; RMSSD, using only successive differences between beats
  detected one after the other; the SD of the beat-wise peak-to-trough BVP
  amplitude; and interval coverage, the summed IBIs divided by the window
  length.
- *Heart rate (1).* The mean of the device HR. The HR file records time to
  the minute only, so the seconds were reconstructed from each row's
  position within its minute.
- *Skin temperature (3).* Mean, SD and slope.

**Activity (ACT; 5).** We used the acceleration magnitude in units of g
(the E4 reports 1/64 g). The minimum, maximum and mean over the 2 h before
the reading follow Karunarathna and Liang [@karunarathna_glucose_2025]. The
mean and SD over the 5-min window were added.

**Clock time (TIME; 3).** Minutes from midnight, and its sine and cosine
over a 24 h period.

**Elapsed time (ELAPSED; 1).** Minutes since the participant's first CGM
reading. This feature has no physiological meaning. It was registered only
as a probe for leakage between neighbouring readings.

**Meals (MEAL; 7).** Minutes since the last meal event, and the
carbohydrate and sugar logged over the previous 2, 8 and 24 h. These were
computed for the 14 aligned participants only, and set to missing for
readings before the first food entry.

**Identity (ID).** Biological sex and HbA1c. In random-split experiments
only, ID+P adds a one-hot participant indicator. This measures how much a
model gains from knowing who the reading belongs to.

**Composite sets.**

- FULL-KL approximates Karunarathna and Liang's model: PHYS, ACT, TIME and
  sex, followed by their selection step, which keeps the 30 features
  ranked highest by random-forest importance on the training split only
  [@karunarathna_glucose_2025]. Their 236 features include 87 time-,
  frequency- and non-linear-domain features each for HR and skin
  temperature. Their code is not public, so we kept their windows,
  activity, circadian and sex features, selection step and evaluation, and
  replaced their physiology with ours. This was declared in the
  registration.
- FULL-B approximates the input domains of Bent et al.
  [@bent_digital_2021]: PHYS, ACT, TIME, MEAL, sex and HbA1c.

### 2.5. Models

The primary model was gradient-boosted trees (XGBoost
[@chen_xgboost_2016]). The secondary model was ridge regression. Each model
sat in a pipeline of median imputation, standard scaling and the regressor,
and the pipeline was fitted on training data only. Hyperparameters were
chosen from fixed grids by five-fold cross-validation within the training
data (Appendix A, Table A1). That cross-validation grouped readings by
participant in every experiment except E1, which reproduces the published
ungrouped procedure. The reference baseline predicts the mean glucose of
the training fold for every test reading.

### 2.6. Evaluation Schemes

- **RANDOM.** Readings from all participants were pooled and split 80/20 at
  random, as published [@karunarathna_glucose_2025]. This was repeated with
  20 seeds.
- **LOPO.** Each participant served once as the test set: 15 folds, or 14
  when MEAL features were used.
- **BLOCKED-*b*.** Each participant's recording was cut into five
  contiguous blocks, and each block served once as the test set. Training
  readings within *b* minutes of the test block were removed, for *b* ∈ {0,
  30, 60, 120, 240}.

### 2.7. Registered Experiments and Hypotheses

The six registered experiments and eight hypotheses are listed in Table 1.
H1, H2b and H4 were designated primary. H2, H2b and H3 compare shortcut
models with FULL-KL, and each passes trivially when FULL-KL has learned
nothing: a non-inferiority test passes when both models score near zero,
and H3 passes when the FULL-KL R² is slightly negative. These three tests
were therefore to be interpreted only if the lower 95% bound of the E1 R²
exceeded 0.30. Dry runs of the analysis code on a noise target showed both
failure modes.

**Table 1.** Registered experiments and hypotheses.

| Exp. | Question | Comparison | Hypothesis |
|---|---|---|---|
| E1 | Does the re-implementation reach the published R²? | FULL-KL, RANDOM | Descriptive. Approximately reproduced if mean R² ≥ 0.63 |
| E2 | How much does holding participants out cost? | FULL-KL, RANDOM vs LOPO | H1: R² drop > 0.30 |
| E3 | Do shortcuts alone match the full model under RANDOM? | TIME+ID+P, ELAPSED+ID+P, ID+P vs FULL-KL | H2, H2b: non-inferior within 0.05 R². H3: ID+P R² > half of FULL-KL R² |
| E4 | What does wrist physiology add under LOPO? | Mean baseline; TIME+MEAL+ID; FULL-B (14 participants) | H4: RMSE gain from adding PHYS+ACT < 2.0 mg/dL. H5: FULL-B R² exceeds the baseline by < 0.10 |
| E5 | Does the Clarke grid separate models from a constant? | Mean baseline under LOPO | H6: zones A+B ≥ 90% |
| E6 | Do neighbouring readings leak? | BLOCKED-0 vs BLOCKED-60 | H7: R² falls with a 60-min buffer |

### 2.8. Metrics and Statistical Analysis

We report R², RMSE, mean absolute relative difference (MARD) and the
percentage of predictions in each zone of the Clarke error grid
[@clarke_ceg_1987]. Metrics are pooled over all test readings of an
experiment and are also given per participant. Uncertainty was estimated
with a participant-level bootstrap [@efron_bootstrap_1993]. In each of
10,000 resamples, participants were drawn with replacement, and the metric
or difference was recomputed from their test predictions. In the RANDOM
scheme, a participant's predictions were pooled over the 20 seeds. For
comparisons, both arms were recomputed within the same resample. With 15
participants, intervals from cross-validation are wide
[@varoquaux_cvfailure_2018], so the registration fixed non-inferiority
margins in advance. That way, a non-significant difference is not
mistaken for equivalence. All eight registered tests were one-sided, with
Holm–Bonferroni correction at a family-wise α of 0.05 [@holm_1979].
Exploratory analyses (Section 3.7) were not corrected and are labelled as
exploratory. One sensitivity analysis was pre-specified (EA6): all
registered tests were repeated with the data-integrity rule switched off,
so that participant 015 was included. Its results are reported beside the
primary ones and are not part of the Holm family.

### 2.9. Information Seen Before Registration

Before registration, the authors had read the dataset documentation and the
published articles. They had also run the alignment check of Section 2.2,
which read the food logs, CGM values and `Demographics.csv` but no E4 data,
and had built the feature table, which computes model inputs but fits no
model. From the feature build they had seen, per participant, how many
readings fell in the sensor warm-up, lacked E4 data, or remained usable;
these counts led to the data-integrity rule of Section 2.3. The glucose
values in the feature table were not summarised, and the analysis code was
tested only on a synthetic noise target. One rule of the alignment check was changed after its first run.
The day-shift comparison originally included shifts that kept as few as 5
meal events, and noise in those shifts flagged three participants who were
otherwise aligned. The change is documented with the check's code and
output.

### 2.10. Implementation and Availability

The analysis ran in Python [RESULT: version] with pandas, NumPy, SciPy,
scikit-learn, XGBoost [@chen_xgboost_2016] and Matplotlib. The code, the
registration, the check outputs and every reported number are available at
https://github.com/MohannadBanat/bigideas-glucose-audit [RESULT: Zenodo DOI
of the release used for submission].

## 3. Results

[RESULT] Each subsection reports one registered experiment, in the order of
Table 1, then the exploratory analyses. Each number is copied from
`results/` and named with its source file in the code comments.

### 3.1. Cohort and Readings
[RESULT: Table 2, with readings per participant before and after each
exclusion, the share of valid pulse and EDA features, and the E4/CGM overlap.]

### 3.2. E1: Re-Implementation Under a Random Split
### 3.3. E2: Random Versus Leave-One-Participant-Out
### 3.4. E3: Shortcut-Only Models
### 3.5. E4: What Wrist Physiology Adds
### 3.6. E5 and E6: Clarke Grid and Temporal Leakage
### 3.7. Exploratory Analyses

[RESULT: EA1–EA5. EA6 sensitivity analysis with participant 015 included:
supplementary table of all eight tests, and a sentence on any verdict that
changes.]

## 4. Discussion

[RESULT] Planned structure:

1. The main finding in one paragraph.
2. What the published R² measures.
3. What physiology adds.
4. Why the Clarke grid is not evidence of accuracy.
5. Recommendations for evaluating glucose estimation from wearables.
6. Limitations: n = 16; one device; prediabetic range only; CGM error as a
   ceiling (overall MARD of the G6 against reference blood glucose: 10.0% [@wadwa_g6_2018]); approximate re-implementation; food logs that
   cannot be aligned; the risk that the design is seen as repeating
   [@abuowida_stress_2026], answered by E3 and E5.

## 5. Conclusions

[RESULT]

## 6. Back Matter

**Author Contributions:** [to be agreed; CRediT taxonomy].

**Funding:** [to be completed].

**Institutional Review Board Statement:** Not applicable. This is a
secondary analysis of a public, de-identified dataset. The original data
collection was approved by the institutional review board of the dataset
authors [@bent_digital_2021].

**Informed Consent Statement:** Informed consent was obtained by the
original investigators [@bent_digital_2021].

**Data Availability Statement:** The dataset is openly available on
PhysioNet at https://doi.org/10.13026/aw6y-fc44 (version 1.1.3). The
registration is at [RESULT: OSF DOI]. The code and all outputs are at
https://github.com/MohannadBanat/bigideas-glucose-audit and archived at
[RESULT: Zenodo DOI].

**Use of AI tools:** [The authors must state here, in MDPI's required form,
which AI tools were used and for what. They take full responsibility for
the content.]

**Conflicts of Interest:** The authors declare no conflicts of interest.

## Appendix A

**Table A1.** Model settings: the XGBoost grid (depth {3, 6}; trees {100,
300}; learning rate {0.05, 0.1}; subsampling 0.8), the ridge grid (α {0.1,
1, 10, 100}), inner cross-validation, seeds, and 10,000 bootstrap resamples.

## Appendix B

**Table B1.** Deviations from the registered plan. [RESULT]
