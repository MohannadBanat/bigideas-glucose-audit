# Shortcut and leakage audit of wrist-wearable glucose estimation (BIG IDEAs)

This is a pre-registered re-evaluation of glucose estimation from the Empatica
E4 wristband on the PhysioNet BIG IDEAs dataset (v1.1.3). It is the first-author
project of M. Banat (Al-Ahliyya Amman University), targeting *Sensors* (MDPI).

**Status (22 Nov 2026):** the analysis plan was registered on OSF and approved
(https://doi.org/10.17605/OSF.IO/CVFA3). The registered analysis, the
pre-specified sensitivity analysis (EA6) and the exploratory analyses (EA1–EA5)
have been run, and the manuscript is a full draft with results
(`manuscript/`). Title: *Temporal Leakage Inflates Reported Accuracy of
Wrist-Wearable Glucose Estimation: A Pre-Registered Re-Evaluation*.

## Order of work

| Step | Command | Output | Status |
|---|---|---|---|
| 1. Small files (food logs, Dexcom, demographics) | `./code/download_data.sh` | `data/big-ideas-1.1.3/` | done |
| 2. Food-log/CGM alignment gate | `python code/check_time_of_day.py data/big-ideas-1.1.3 results/time_of_day` | `results/time_of_day/` | done (14/16 aligned) |
| 3. Feature table (streams E4 data, ~2.6 GB per participant at peak) | `./code/build_features.sh data/big-ideas-1.1.3 results/features` | `results/features/` | done (16 participants; 28,404 of 36,898 readings usable; 015 then fails the data-integrity rule, leaving 15) |
| 4. Analysis code check on a noise target | `python code/experiments.py results/features results/selftest --self-test --quick` | `results/selftest/` | done on the 15 participants retained under rule 7 (no-signal target behaves as expected) |
| 5. **File the registration on OSF** | `docs/02_preregistration_draft.md` | OSF DOI | registered 22 Nov 2026: https://doi.org/10.17605/OSF.IO/CVFA3 |
| 6. Registered experiments E1–E6 | `python code/experiments.py results/features results/experiments --osf-doi 10.17605/OSF.IO/CVFA3` (EA6: add `--include-low-overlap`, output `results/experiments_ea6/`) | `results/experiments/` | done 22 Nov 2026 |
| 7. Exploratory analyses EA1–EA5 | `python code/exploratory.py results/features data/big-ideas-1.1.3 results/exploratory` | `results/exploratory/` | done 22 Nov 2026 |
| 8. Figures and tables | `python code/figures.py results/experiments`; `python code/summarize.py results` | `results/experiments/figures/`, `results/summary/` | done |
| 9. Manuscript | `python manuscript/assemble.py`; `python manuscript/build_mdpi.py OUT.docx --pdf` | MDPI-style Word and PDF | full draft with results |

## Layout

```
code/         download, gate check, features, experiments, figures
docs/         novelty check, pre-registration draft, next steps
manuscript/   manuscript draft (Markdown; citations are keys in references/references.bib)
references/   bibliography; every DOI checked against Crossref, PubMed or arXiv on 22 Nov 2026
results/      outputs written by the scripts; every number in the manuscript comes from here
```

## Data notes

- The AWS mirror (`s3://physionet-open/big-ideas-glycemic-wearable/`) stops at
  v1.1.2. Versions 1.1.2 and 1.1.3 differ only in the food logs of 007, 013,
  015 and 016 (published SHA-256 checksums), so E4 and Dexcom files are
  streamed from the mirror and verified against the v1.1.3 checksums.
- `Food_Log_003.csv` has no header row. Food logs name their clock column
  `time` or `time_of_day`. HR files store time either to the minute
  (`2/13/20 15:29`) or as full ISO timestamps. The code handles all of these.

## Requirements

Python ≥ 3.11 with the packages in `code/requirements.txt`.
