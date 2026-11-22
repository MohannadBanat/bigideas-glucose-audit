# Feature tables

One gzipped CSV per participant (`features_<pid>.csv.gz`), one row per Dexcom
reading, written by `code/build_features.sh` / `code/features.py`.
`features_log.csv` gives counts per participant.

| | Readings |
|---|---|
| Dexcom readings | 36,898 |
| In the 2-h sensor warm-up (excluded) | 632 |
| No valid E4 data in the window (excluded) | 8,060 |
| **Usable** | **28,404** |

E4 coverage is all-or-nothing in practice: when a reading fails, every E4
stream is missing for that window (the band was off). Participant 015 keeps
only 470 readings because its E4 recording starts two weeks before its CGM
recording and ends two days before the CGM does.

Total SCR counts for 005 (66,181) and 010 (60,643) are about twice the
cohort median (about 28,000). They are kept as measured; SCR features are not
normalised per participant.
