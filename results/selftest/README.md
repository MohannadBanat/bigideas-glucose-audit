# Self-test on a noise target

`python code/experiments.py results/features results/selftest --self-test --quick`

Run on the 15 participants retained under the data-integrity rule (rule 7;
015 excluded; 27,934 readings), with glucose replaced by independent
Gaussian noise (mean 110, SD 20 mg/dL, clipped to 40–400). Grids, seeds and
bootstrap resamples are reduced (`--quick`), so **no number here is a result
of the study**. It checks that the pipeline runs end to end and that the
registered tests behave sensibly when there is nothing to learn:

- Every R² lies between −0.005 and 0.000, under RANDOM, LOPO and BLOCKED
  splits.
- H1 (leakage drop > 0.30) and H7 (adjacent readings leak) are not
  supported.
- H2, H2b and H3 would pass their Holm-corrected tests trivially, because
  FULL-KL has learned nothing (H2, H2b: every R² ≈ 0; H3: FULL-KL R² is
  slightly negative). The pre-registration therefore interprets these three
  only if E1's lower bound of R² exceeds 0.30
  (`docs/02_preregistration_draft.md`, §7). Here they are marked
  "not interpretable".
- H4 and H5 are supported. They claim that physiology adds little, which is
  true of noise, so this is the expected outcome rather than a flaw.
- H6 is supported: a constant prediction puts about 98% of noise readings in
  Clarke zones A+B, which is the point H6 makes about the Clarke grid.

The same run with `--include-low-overlap` (EA6, 16 participants) also
completes; its output is not kept here.
