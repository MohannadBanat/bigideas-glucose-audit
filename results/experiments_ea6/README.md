# Pre-specified sensitivity analysis EA6 (participant 015 included)

`python code/experiments.py results/features results/experiments_ea6 --osf-doi 10.17605/OSF.IO/CVFA3 --include-low-overlap`

Registered in §9 of the pre-registration (https://doi.org/10.17605/OSF.IO/CVFA3):
all registered experiments and tests repeated with the data-integrity rule
(rule 7) switched off, so participant 015 (470 usable readings) is included:
16 participants, 28,404 readings; E4 still uses 14. Not part of the Holm
family of the primary analysis. Run 22 Nov 2026, 14:00–14:31 UTC.

Files have the same layout as `results/experiments/`.

Result: every registered verdict is the same as in the primary analysis
except H7 (BLOCKED-0 minus BLOCKED-60 R²: 0.0021, 95% CI −0.0016 to 0.0062,
Holm p = 0.58; not supported). Side-by-side table:
`results/summary/tableS1_ea6.csv`.
