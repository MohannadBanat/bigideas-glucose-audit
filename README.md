# Shortcut and leakage audit of wrist-wearable glucose estimation (BIG IDEAs)

This is a pre-registered re-evaluation of glucose estimation from the Empatica
E4 wristband on the PhysioNet BIG IDEAs dataset (v1.1.3). It is the first-author
project of M. Banat (Al-Ahliyya Amman University), targeting *Sensors* (MDPI).

**Status:** the analysis plan is drafted but **not yet filed on OSF**. No
model has been trained on the real target. `code/experiments.py` refuses to
run on real glucose until an OSF DOI is passed to it.

## Order of work

| Step | Command | Output | Status |
|---|---|---|---|
| 1. Small files (food logs, Dexcom, demographics) | `./code/download_data.sh` | `data/big-ideas-1.1.3/` | done |
| 2. Food-log/CGM alignment gate | `python code/check_time_of_day.py data/big-ideas-1.1.3 results/time_of_day` | `results/time_of_day/` | done (14/16 aligned) |
| 3. Feature table (streams E4 data, ~2.6 GB per participant at peak) | `./code/build_features.sh data/big-ideas-1.1.3 results/features` | `results/features/` | done (16 participants; 28,404 of 36,898 readings usable) |
| 4. Analysis code check on a noise target | `python code/experiments.py results/features results/selftest --self-test --quick` | `results/selftest/` | done on 16 participants (no-signal target behaves as expected) |
| 5. **File the registration on OSF** | `docs/02_preregistration_draft.md` | OSF DOI | **waiting on co-authors** |
| 6. Registered experiments E1–E6 | `python code/experiments.py results/features results/experiments --osf-doi <DOI>` | `results/experiments/` | locked until step 5 |
| 7. Figures | `python code/figures.py results/experiments` | `results/experiments/figures/` | |
| 8. Manuscript | `manuscript/manuscript.md` | | Introduction and Methods drafted |

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
