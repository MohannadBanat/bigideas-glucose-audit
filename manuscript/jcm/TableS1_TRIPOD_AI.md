---
title: "Supplementary Table S1. TRIPOD+AI checklist"
---

**Supplementary Table S1.** TRIPOD+AI checklist [Collins et al., BMJ 2024;385:e078378] for "Temporal Leakage Inflates Reported Accuracy of Wrist-Wearable Glucose Estimation: A Pre-Registered Re-Evaluation". The study re-implements and evaluates published glucose-estimation models and compares them with shortcut-only and constant baselines; items marked D (development only) are answered for the re-implemented models. Section numbers refer to the manuscript.

| Item | Topic | Where reported / response |
|---|---|---|
| 1 | Title | Title: evaluation ("re-evaluation") of wrist-wearable glucose estimation; outcome = glucose. Target population is described in the Abstract (adults with high-normal glucose or prediabetes). |
| 2 | Abstract | Structured abstract (Background/Objectives, Methods, Results, Conclusions). |
| 3a | Healthcare context, rationale, existing models | Section 1 (paragraphs 1–3): clinical-safety context, existing models [Bent et al.; Karunarathna and Liang]. |
| 3b | Target population, intended purpose, users | Section 1 (paragraphs 1–2): non-invasive estimation of glucose for people with high-normal glucose or prediabetes; users are patients and clinicians. |
| 3c | Known health inequalities | Not addressed. Sex is analysed as a predictor (Sections 2.4, 3.7 EA1, EA5); no other sociodemographic data are available in the dataset. |
| 4 | Objectives | Section 1, final paragraph (four contributions); Section 2.7 and Table 1 (registered hypotheses). |
| 5a | Data sources, rationale, representativeness | Section 2.1 (BIG IDEAs v1.1.3, PhysioNet); representativeness discussed in Section 4.7. |
| 5b | Dates of data collection | Dates are shifted by PhysioNet for de-identification (Section 2.1); 8–10 days per participant. |
| 6a | Setting, centres | Section 2.1: free-living, single study [Bent et al.]. |
| 6b | Eligibility criteria | Section 2.1 (adults aged 35–65 years with high-normal glucose or prediabetes, per the dataset); exclusions in Section 2.3. |
| 6c | Treatments | Not reported in the dataset; not applicable to the analysis. |
| 7 | Data preparation and quality checking | Sections 2.2 (food-log/CGM alignment check), 2.3 (pre-processing, exclusions, feature validity rules). |
| 8a | Outcome definition | Section 2.3: CGM interstitial glucose (mg/dL) at each 5-min reading; estimation, not forecasting. |
| 8b | Subjective outcome assessment | Not applicable (device measurement). |
| 8c | Blinding of outcome assessment | Not applicable (device measurement; analysis plan registered before any model was fitted to glucose, Section 2). |
| 9a | Choice of initial predictors | Section 2.4 (feature sets follow the published models; differences declared in the registration). |
| 9b | Predictor definitions and timing | Section 2.4 (all features computed from the 5 min, or 2 h for activity, before each reading). |
| 9c | Subjective predictor assessment | Not applicable; food logs were self-reported by participants (Section 2.1). |
| 10 | Sample size | Section 2.1: fixed by the public dataset, no sample size calculation; registered margins in Section 2.8; limitation in Section 4.7. |
| 11 | Missing data | Sections 2.3 (exclusions, validity rules, training-fold median imputation) and 3.1 (Table 2). |
| 12a | Use of data, partitioning | Section 2.6 (RANDOM, LOPO, BLOCKED-b). |
| 12b | Predictor handling | Section 2.5 (median imputation, standard scaling within the training fold). |
| 12c | Model type, building steps, tuning, internal validation | Section 2.5; Appendix A, Table A1. |
| 12d | Heterogeneity across clusters | Per-participant metrics (Section 3.3, Figure 3); participant-level bootstrap (Section 2.8). |
| 12e | Performance measures and model comparison | Section 2.8 (R², RMSE, MARD, Clarke error grid; bootstrap; Holm correction). |
| 12f | Model updating | Not applicable (no updating or recalibration). |
| 12g | How predictions were calculated | Code archived on Zenodo (doi:10.5281/zenodo.24448197) and on GitHub (Section 2.10). |
| 13 | Class imbalance | Not applicable (continuous outcome). |
| 14 | Fairness | Not addressed beyond sex (Sections 3.7 EA1, EA5); dataset too small for subgroup fairness analysis. |
| 15 | Model output | Continuous glucose estimate in mg/dL; no thresholds (Section 2.3). |
| 16 | Differences between development and evaluation data | Section 2.4 (differences between the re-implementation and the published model); Section 2.1 (dataset versions). |
| 17 | Ethical approval | Institutional Review Board and Informed Consent Statements (back matter). |
| 18a | Funding | Funding statement (back matter). |
| 18b | Conflicts of interest | Conflicts of Interest statement (back matter). |
| 18c | Protocol | Registered analysis plan, https://doi.org/10.17605/OSF.IO/CVFA3 (Section 2). |
| 18d | Registration | OSF registration, https://doi.org/10.17605/OSF.IO/CVFA3 (Section 2). |
| 18e | Data sharing | Data Availability Statement (PhysioNet doi:10.13026/aw6y-fc44). |
| 18f | Code sharing | Section 2.10 and Data Availability Statement (Zenodo, GitHub). |
| 19 | Patient and public involvement | Section 2.11: none. |
| 20a | Participant flow | Section 3.1 and Table 2 (16 recordings; 15 analysed; 14 with meal features). |
| 20b | Participant characteristics | Section 2.1 and Table 2 (sex, HbA1c, readings, missing data); Section 3.1 (glucose distribution). |
| 20c | Comparison with development data | Not applicable (same dataset as the published models; Section 2.1). |
| 21 | Numbers in each analysis | Sections 2.6 and 3.1 (readings and participants per scheme). |
| 22 | Full model specification | Code and settings archived (Zenodo; Appendix A). The re-implemented models are evaluation baselines, not models proposed for use. |
| 23a | Performance with confidence intervals | Tables 3–5; Figures 2–6. Sex subgroup: exploratory EA5 (Section 3.7). |
| 23b | Heterogeneity across clusters | Per-participant RMSE (Figure 3; Section 3.3). |
| 24 | Model updating results | Not applicable. |
| 25 | Interpretation | Sections 4.1–4.5. |
| 26 | Limitations | Section 4.7. |
| 27a | Handling poor-quality input data in implementation | Not applicable: no model is proposed for implementation. |
| 27b | User interaction and expertise | Not applicable: no model is proposed for implementation. |
| 27c | Next steps for research | Sections 4.5 and 4.6 (Recommendations). |
