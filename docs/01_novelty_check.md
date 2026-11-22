# Novelty and protocol check (22 Nov 2026)

All facts below come from the papers themselves or their PubMed Central/PhysioNet pages, read on 22 Nov 2026.

## A. Closest competitor work

| Paper | Data | What overlaps | What is not done |
|---|---|---|---|
| Ramesh, Neufeld, Küttner, Röddiger, Beigl (KIT). *Reassessing the Feasibility of PPG-Based Non-Invasive Blood Glucose Level Estimation*. arXiv:2608.01820 (Aug 2026) | VitalDB (500 Hz perioperative PPG + lab glucose); MUST (23 people, 67 sessions) | Random window split vs participant-aware split and a split holding out one-fifth of participants. Models collapse to R² ≈ 0 or below. A mean-prediction baseline matches published models on Clarke grid, MARD and often R². ">90% Clarke A+B for every model including baseline." | BIG IDEAs, Empatica E4, free-living data, LOPO, time-of-day or meal-time or identity shortcut controls, pre-registration |
| Lu, Wagle, Liang, Cui, Prioleau. *Deep learning for blood glucose prediction: Reproducibility challenges and factors affecting differential performance*. PLOS Digit Health 2026;5(9) | OhioT1DM, DiaTrend, T1DEXI (128 people with T1D) | Reproducibility framing | Different task: CGM-to-CGM forecasting in T1D |
| Zhao Y. *Measurement Reliability Confounds Cross-Regime Comparisons of Postprandial Glucose Prediction*. Research Square 2026 (rs-11558064) | CGMacros (45 subjects) → BIG IDEAs (16 subjects, 656 meals) | Uses BIG IDEAs and LOSO; reliability-ceiling argument | Different task: meal-response prediction, not wearable-to-glucose |

## B. BIG IDEAs glucose papers: validation protocols

| Paper | Validation | Headline result | Notes |
|---|---|---|---|
| Bent et al. 2021, npj Digit Med 4:89 | Population: **LOPOCV**. Personalized: first 50% / last 50% chronological. 3-class excursion: repeated stratified 10-fold (window-level) | LOPO XGBoost RMSE 21.22 ± 4.14 mg/dL, MAPE 14.33%. Personalized RMSE 21.10. Excursion decision tree 84.3% accuracy under window-level CV | Inputs include minutes from midnight, wake time, food sums (2/8/24 h), HbA1c, sex, a participant-ID feature. Top RF features: minutes from midnight 0.069, sugar 24 h 0.067, HbA1c 0.062, carbs 2 h 0.047, sex 0.047. Food ≈37%, activity ≈17%, circadian ≈10.6% of importance. No Clarke grid. |
| Karunarathna & Liang 2025, Sensors 25(10):3207 | "80/20 train–test split", 21,104 / 5,276 epochs; 5-fold CV grid search; 20 seeds. **Participant separation not stated**  Methods re-read 22 Nov 2026: the split is described only as "an 80/20 train–test split"; data from v1.1.2; 5-min epoch before each CGM reading; 236 features = 87 each for HR and TEMP + 13 HRV + 42 EDA + 3 ACC-2h + 3 circadian + sex; no code released | XGBoost R² 0.73, RMSE 11.9 mg/dL, MARD 7.1%, Clarke 99.4% A+B (~95% A) | 236 features → top 30 by RF importance. Includes minutes from midnight + sin/cos, sex, 2 h ACC, E4 physiology. Excludes food logs. **Top feature = biological sex.** |
| Piersanti et al. 2025, Sensors 25(13):4038 | Wilcoxon tests + mixed model; no ML | Skin-temperature variability metrics vs hypo/hyperglycemia | Splits day/night at 06:00/21:00 |
| Miyakoshi & Ito 2024, JMIR Diabetes 9:e62831 | Correlation/regression; no ML | No R² or RMSE | Used v1.1.1, before the food-log date fix |

**Interpretation:**
- [Likely] Karunarathna & Liang's split was window-level, so the same participant appears in both training and test data.
- [Certain] Bent's LOPO result is already honest about participant overlap. The open question there is attribution: how much of 21 mg/dL comes from time, food and HbA1c rather than the watch.

## C. Feasibility checks

- **Time of day.** PhysioNet says data is "time-shifted (by date)". The food log for participant 001 (header `date,time,time_begin,time_end,logged_food,...`) shows "Standard Breakfast" at 07:10 and 07:00, lunch at about 12:38, and dinner at about 20:00–20:30. Clock time therefore appears preserved. **Verify for all 16 participants** (`code/check_time_of_day.py`). One entry at 01:40 looks like a typo.
- **Column names differ from the documentation.** The PhysioNet page lists `time_of_day`, but the file has `time`. Code must detect column names rather than hard-code them.
- **Time since last meal.** Buildable from `time_begin` together with `total_carb` and `sugar`.

## D. Other ideas considered (not pursued here)

- **Cross-device PPG signal-quality transfer.** Already covered by Zanelli et al. (IEEE EMBC 2021), Mula et al. (CinC 2024 and an IEEE Access follow-up), a 2026 domain-independent SQA framework (PubMed 42477397), and SSL-TDA work.
- **Remaining gap:** smartphone-camera PPG as a domain (BUT PPG). A possible design uses the BUT PPG ≤5 bpm HR-error rule applied automatically to DaLiA and WESAD (both have chest ECG). This is a possible second paper.
