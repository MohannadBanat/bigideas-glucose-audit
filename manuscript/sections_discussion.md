## 4. Discussion

### 4.1. Principal Findings

Under the random split used in the published work, a model that knew only
which participant a reading came from and how many minutes had passed since
the start of that participant's recording estimated glucose better than our
re-implementation of the published physiology model (R² 0.76 against 0.61).
When participants were held out, the physiology model kept an R² of 0.07,
with an interval that includes zero. When time of day, meals, sex and HbA1c
were already known, wrist physiology and activity improved the RMSE by
0.4 mg/dL. And a constant prediction placed 99.2% of readings in Clarke
zones A + B, the same share as every model we fitted. All three primary
hypotheses (H1, H2b and H4) were supported; the sensitivity analysis with
participant 015 included changed only one verdict, that of H7, whose effect was negligible in either analysis.

### 4.2. What a Random-Split R² Measures

CGM glucose changes slowly relative to the 5-min sampling interval. When
readings are split at random, nearly every test reading has training
readings from the same person a few minutes before and after it, and a
flexible model can interpolate between them. ELAPSED+ID+P has no access to
physiology; it can only place a reading on the participant's own timeline
(from which, with the participant's start time, clock time could also be
derived). That it outperformed FULL-KL (H2b) shows that
this interpolation alone is enough to exceed the accuracy of the physiology
model under a random split. Two further results locate the shortcut more
precisely. Clock time with identity (H2) reached only about half of the
FULL-KL R², so the shortcut is not, in the main, a shared daily rhythm of
meals and glucose. Identity alone (H3) reached less than half, so it is not
simply each person's mean glucose either. The shortcut is the position of a
reading *within* a recording. Contiguous blocks removed almost all of it
(E6): with each fifth of a recording held out, R² fell to 0.11, close to the
LOPO value, even though the training data still held the same
participant's other days.

Our re-implementation did not reach the published R² of 0.73 (E1). It
approximated the published pipeline with fewer and different physiology
features, because the original code is not available, so our results do
not show directly what the published model learned. They do show that, on
the same data and under the same split, an R² of this size is reached more
easily by a model with no physiology at all, and that the same physiology
explains almost none of the variance in a person it has not seen. Under the random split, the attribution of our model was spread over slowly varying inputs such as 2-h activity summaries and mean skin temperature (EA1); such inputs can locate a reading within a recording as well as reflect physiology, and attribution alone cannot tell the two apart.
A random-split R² on these data therefore cannot be read as evidence that
wrist signals carry information about glucose.

### 4.3. What Wrist Physiology Adds

Held out by participant, the best model in this study (FULL-B) explained
about a fifth of the variance in glucose (R² 0.21), with an RMSE of
20.6 mg/dL. Most of that came from time of day, meals and HbA1c: removing
the wristband signals cost 0.4 mg/dL of RMSE, a fifth of the registered
margin (H4). This matches the attribution reported by Bent et al., in whose
model food-log and demographic variables carried most of the importance
[@bent_digital_2021]. Three exploratory analyses point the same way. Without sex, the LOPO R² of FULL-KL fell to about zero (EA5). Personalised models trained on the first half of a participant's own recording did no better than that participant's mean (EA2). And when meal features were withheld, physiology and activity recovered about 1 mg/dL of RMSE (EA4), still within the registered margin. The added value of the wristband is
therefore small even in the setting where the dataset was designed to show
it. H5 was not supported because time, meals and HbA1c, rather than
physiology, lifted FULL-B above the baseline; the registered hypothesis
grouped them together, and the result should not be read as evidence for
the wristband.

### 4.4. Why the Clarke Grid Is Not Evidence of Accuracy

The Clarke error grid was designed to judge whether self-monitored blood
glucose readings would lead to wrong treatment decisions in diabetes
[@clarke_ceg_1987]. In BIG IDEAs, 98% of readings lie between 70 and
180 mg/dL, where zone B is wide and zones C and E cannot be reached by a
prediction near the cohort mean. A constant prediction therefore placed
99.2% of readings in zones A + B, as did every model we fitted. Ramesh et
al. reported the same for PPG-based estimation [@ramesh_reassessing_2026].
In cohorts with high-normal glucose or prediabetes, the percentage in zones
A + B carries no information about a model and should not be reported as
evidence of accuracy. Zone A, MARD and R² separate models better, provided
they are compared with a constant baseline evaluated the same way.

### 4.5. Recommendations

For studies that estimate glucose from wearables, our results support five
practices:

1. Evaluate on participants the model has not seen (LOPO or grouped
   cross-validation). Where within-person accuracy is of interest, hold out
   contiguous blocks of each recording rather than random readings.
2. Report shortcut-only baselines evaluated in the same way: the training
   mean, identity, clock time and, under any within-person split, elapsed
   time.
3. Report R², RMSE and MARD next to the same metrics for those baselines,
   and do not use the Clarke A + B percentage as evidence of accuracy in
   cohorts whose glucose stays in the normal range.
4. Check that food logs and CGM recordings share a clock before using
   meal features; in the current BIG IDEAs release, two of 16 do not.
5. Register the analysis plan, including margins for what counts as a
   useful improvement, before training models.

### 4.6. Limitations

The analysed cohort is small (15 participants of the 16 in the dataset),
so participant-level intervals are wide; the registered margins were set so
that the conclusions do not rest on non-significant differences. All
participants had high-normal glucose or prediabetes and wore one device
model, so the results may not transfer to people with diabetes, whose
glucose varies more, or to other wearables. The CGM is itself a noisy
reference, with an overall MARD of 10.0% against blood glucose
[@wadwa_g6_2018]. Under a simple error model, sensor error alone would cap the R² of a perfect estimator of blood glucose near 0.59 (EA3), a value that the random-split models reached or exceeded, which suggests that they also learned the CGM's own error. Our FULL-KL is an approximate re-implementation
and did not reach the published R², so our conclusions concern the
evaluation design, not the exact published model. Pulse and
heart-rate-variability features were valid in only about a quarter of
readings, because the E4 drops inter-beat intervals during movement, and
imputation may have weakened them; EDA, temperature and activity features
were largely complete. Meal features were unavailable for two participants
whose food logs did not line up with their CGM records. H7 was supported
in the primary analysis, but the effect of a 60-min buffer was negligible
in size and was not supported when participant 015 was included (EA6), so
we draw no practical conclusion from it. Finally, the design
follows our earlier study of stress detection [@abuowida_stress_2026], and
a reader may ask whether the result was foreseen; the shortcut-only
controls (E3) and the constant baseline (E5) were registered precisely so
that the conclusions rest on direct comparisons rather than on that
expectation.

## 5. Conclusions

On the BIG IDEAs dataset, the accuracy of wrist-wearable glucose estimation
under a random split of readings is explained by where each reading lies
in a participant's recording: a model with no physiology at all
outperformed the physiology model. Held out by participant, wrist
physiology explained almost none of the variance in glucose, and added
0.4 mg/dL of RMSE to what time, meals and HbA1c already provided. A constant
prediction placed 99.2% of readings in Clarke zones A + B. Claims that wrist
wearables estimate glucose should rest on participant-held-out evaluation,
compared against shortcut-only and constant baselines, and not on
random-split R² or on the Clarke grid.
