# Handover — Shortcut & Leakage Audit of Wearable Glucose Estimation (BIG IDEAs)

Prepared 22 Nov 2026 for Mohannad Banat (Al-Ahliyya Amman University).
Status: **design stage. No model trained yet. No data downloaded except one food log inspected.**

---

## ⚠️ Do this before anything else

1. **File the pre-registration on OSF before training any model.** The draft is `docs/02_preregistration_draft.md`. Everything marked `TODO` must be decided by the team first. The pre-registration is the paper's main edge over the closest competitor (KIT, arXiv 2608.01820), which was not pre-registered.
2. **Run `code/check_time_of_day.py`** on all 16 participants. The time-of-day shortcut control (E3) depends on clock time surviving PhysioNet's date-shifting. So far this has been checked for participant 001 only.
3. **Email Karunarathna & Liang** (Sensors 2025, 25(10):3207) and ask whether their 80/20 split kept participants separate. Log the date sent and any reply.

---

## 1. Goal

Publish a pre-registered re-evaluation in a **Scopus-Q1 journal**, with *Sensors* (MDPI) as the first target. The paper should show that the published accuracy of glucose estimation from wrist-worn wearables on the BIG IDEAs dataset is explained largely by **non-physiological shortcuts** (clock time, participant identity, and meal timing) and by **participant leakage**, not by the wrist physiology.

Venue facts, as of Nov 2026:
- *Sensors*: CiteScore Q1 (Instrumentation); JCR Q2.
- Scopus is the metric that matters for this project.
- Quote the exact category ("CiteScore Q1, Instrumentation") on CVs and applications.

## 2. Why this paper, and why now

- The team already published the same methodology in *Sensors* on another Empatica E4 dataset: Abu Owida, Alsarhan, Banat, Al-Fraihat & Algarni, 2026, doi 10.3390/s26227340. A copy is in `prior_work/`. **Reuse its structure:** registered experiments E1–E6, negative controls, leave-one-participant-out (LOPO), participant bootstrap confidence intervals, and Holm correction.
- BIG IDEAs is also Empatica E4 data, so the preprocessing code should port with little change.
- The published model this paper targets reports R² 0.73 from an unspecified 80/20 split of 26,380 five-minute epochs, and its **top feature is biological sex**. With n = 16, sex plus clock time comes close to identifying participants.

## 3. Key findings so far

Full detail is in `docs/01_novelty_check.md`.

| Paper | What it did | Role in this paper |
|---|---|---|
| Karunarathna & Liang, *Sensors* 2025 25(10):3207 | 80/20 split, participant separation not stated; XGBoost R² 0.73, RMSE 11.9 mg/dL, 99.4% Clarke A+B; top feature sex; circadian features included | **Main re-evaluation target** |
| Bent et al., *npj Digit Med* 2021 4:89 (dataset authors) | LOPO population model RMSE 21.22 mg/dL; top features: minutes from midnight, sugar intake over 24 h, HbA1c, carbs over 2 h, sex; food ≈37% of importance | Second target: do non-wearable inputs alone reach 21 mg/dL? |
| Ramesh et al. (KIT), arXiv 2608.01820 | Random vs participant splits on VitalDB/MUST; a mean-prediction baseline matches the published models; the Clarke grid hides failure | **Closest competitor.** Must be cited and differentiated: no BIG IDEAs, no LOPO, no time or identity shortcut controls, no pre-registration |
| Lu et al., *PLOS Digit Health* 2026 | Reproducibility of DL CGM forecasting (T1D datasets) | Cite in related work |
| Zhao, Research Square 2026 | Meal-response prediction, CGMacros → BIG IDEAs | Cite; different task |
| Piersanti et al., *Sensors* 2025; Miyakoshi & Ito, *JMIR Diabetes* 2024 | Statistical analyses, no predictive ML | Cite only, not targets |

## 4. The contribution (claim only this)

1. The first participant-level audit of glucose estimation on BIG IDEAs.
2. Shortcut controls not found anywhere in the literature: time of day alone, time since last meal alone, and identity alone (sex, HbA1c, participant ID).
3. Evidence from free-living multimodal wrist data (EDA, TEMP, ACC, BVP), extending KIT's clinical-PPG finding.
4. A pre-registered analysis plan.

**Do not claim** to be the first to show that random splits inflate glucose estimation. KIT already showed that.

## 5. Decisions made (and why)

| Decision | Reason |
|---|---|
| Dataset: BIG IDEAs v1.1.3 | Same device as the team's published paper; heavily used (18 citing works); a published model has likely leakage |
| Dropped: BUT PPG smartphone glucose | Only one glucometer reading per session; physiologically weak |
| Dropped: MGH/MF | Contains no PPG; dated |
| Parked: cross-device PPG quality transfer (BUT PPG → DaLiA/WESAD) | Generalization of PPG signal-quality assessment across devices is already published (Zanelli 2021, Mula CinC 2024, 2026 domain-independent SQA). The remaining gap (smartphone-camera PPG) is narrow. Viable as a **second paper**. |
| Use v1.1.3 only | Food-log dates were corrected in v1.1.3; earlier versions have misaligned meals |

## 6. Known risks

- **n = 16 gives wide LOPO confidence intervals.** Pre-register non-inferiority or equivalence margins so that null results still count as findings.
- **CGM measurement error caps achievable accuracy.** Discuss a reliability ceiling, as Zhao 2026 does.
- **Time-of-day may not be preserved.** If date-shifting also shifted clock time, drop the time-only control and say so.
- **Self-similarity with the stress paper.** Reviewers may call this "the same template again". The differentiating results are E3/E4 (shortcut attribution) and E5 (Clarke grid), and the paper should say so.
- **OGTT data is absent** (corrupted files), and the abstract's claim that participants were female-only is inconsistent with Demographics.csv. Read Demographics.csv before describing the cohort.

## 7. Folder contents

```
README_HANDOVER.md                  ← this file
docs/01_novelty_check.md            ← literature and protocol check, with numbers
docs/02_preregistration_draft.md    ← OSF draft: experiments, hypotheses, TODOs
docs/03_next_steps.md               ← ordered task list with owners and blank dates
references/references.bib           ← all citations (entries marked VERIFY need checking)
code/download_data.sh               ← fetch BIG IDEAs v1.1.3 (AWS, no account needed)
code/check_time_of_day.py           ← gate check for the time-of-day control
code/requirements.txt
prior_work/AbuOwida2026_Sensors_stress_exercise.pdf ← template paper
```

The code is **untested**: it was written without access to the full dataset. Expect to adjust file and column names on the first run.

## 8. Data access

- Dataset: https://doi.org/10.13026/aw6y-fc44. Open access under ODC-By 1.0. 34.1 GB unzipped, 4.7 GB zipped.
- Required citations: the dataset, Bent et al. 2021, and Pollard et al. 2026 (PhysioNet).
- AWS mirror: `s3://physionet-open/big-ideas-glycemic-wearable/` (`--no-sign-request`).
