# Registered analysis (primary)

`python code/experiments.py results/features results/experiments --osf-doi 10.17605/OSF.IO/CVFA3`

- Registration: https://doi.org/10.17605/OSF.IO/CVFA3 (filed 22 Nov 2026 12:58 UTC,
  approved and public 22 Nov 2026; DOI minted 13:14 UTC).
- `code/experiments.py` at run time is byte-identical to the file deposited with
  the registration (SHA-256 `dea04bc30585246b0998e4adc89aa45d4e9322739fa3787c2ccf8f3d5333182b`).
- Run 22 Nov 2026, 13:28–14:00 UTC, on 15 participants (rule 7 excludes 015),
  27,934 readings; E4 uses the 14 participants with aligned food logs.
- `run.log` is the console output, ending with the table of registered tests.

| File | Contents |
|---|---|
| `metrics.csv` | Pooled R², RMSE, MARD, Clarke A and A+B per configuration, with 95% participant-bootstrap intervals (10,000 resamples) |
| `metrics_by_participant.csv` | The same metrics per participant |
| `hypotheses.csv` | The eight registered tests: estimate, 95% interval, one-sided and Holm p, guard, verdict |
| `predictions/*.csv.gz` | Every test prediction; `*__fits.csv` holds the chosen hyperparameters per split |
| `run_info.json` | Versions, seeds, OSF DOI, guard value, rule-7 details |
| `figures/` | Figures 2–6 of the manuscript (`code/figures.py`) |

Summary of the registered tests (Holm-corrected): H1, H2b, H4, H6 and H7
supported; H2 not established; H3 and H5 not supported. E1 mean R² over seeds
0.613 (< 0.63, so the published R² of 0.73 was not approximately reproduced);
E1 lower bound 0.550 (> 0.30, so H2, H2b and H3 are interpretable).

The pre-specified sensitivity analysis with participant 015 included is in
`results/experiments_ea6/` (same command with `--include-low-overlap`). It
changes one verdict: H7 is not supported there.
