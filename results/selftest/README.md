# Self-test on a noise target

`python code/experiments.py results/features results/selftest --self-test --quick`
run on the first 6 participants' feature tables, with glucose replaced by
independent Gaussian noise (mean 110, SD 20 mg/dL, clipped to 40–400). Grids, seeds and
bootstrap resamples are reduced (`--quick`), so **no number here is a result
of the study**. It checks that the pipeline runs end to end and that the
registered tests behave sensibly when there is nothing to learn:

- Every R² lies between −0.008 and 0.001, under RANDOM, LOPO and BLOCKED splits.
- H1 (leakage drop > 0.30) and H7 (adjacent readings leak) are not supported.
- H2 and H2b pass their Holm-corrected tests trivially, because every model
  is at R² ≈ 0. This is why the pre-registration now adds a guard: H2 and H2b
  are interpreted only if E1's lower bound of R² exceeds 0.30
  (`docs/02_preregistration_draft.md`, §7). Here they are marked
  "not interpretable".
- H6 is supported: a constant prediction puts 97.7% of noise readings in
  Clarke zones A+B, which is the point H6 makes about the Clarke grid.
