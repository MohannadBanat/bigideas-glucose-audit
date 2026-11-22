"""
Tables and numbers for the manuscript, copied from the outputs of experiments.py and
exploratory.py. Every number in Results comes from a file this script writes.

Usage:
    python code/summarize.py results

Writes into results/summary/:
    table2_cohort.csv            readings per participant before and after each exclusion
    table3_registered.csv        the eight registered tests (primary analysis)
    tableS1_ea6.csv               primary vs EA6 (015 included), side by side
    e1_seed_r2.csv               R2 of each of the 20 RANDOM seeds (E1 decision rule uses the mean)
    numbers.json                 every number quoted in the text
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experiments as X  # noqa: E402


def cohort(feature_dir):
    rows = []
    for p in sorted(Path(feature_dir).glob("features_*.csv.gz")):
        F = pd.read_csv(p, dtype={"participant": str})
        pid = F["participant"].iloc[0]
        a = F[~F["cgm_warmup"]]
        b = a[a["e4_ok"]]
        rows.append({"participant": pid, "cgm_readings": len(F), "after_warmup": len(a),
                     "with_e4": len(b), "hours_usable": len(b) * 5 / 60,
                     "rule7_retained": len(b) >= X.MIN_USABLE,
                     "meal_features": bool(b["meal_ok"].any()),
                     "pct_pulse_valid": 100 * b["sdnn_ms"].notna().mean(),
                     "pct_eda_valid": 100 * b["eda_tonic_mean"].notna().mean(),
                     "glucose_mean": b["glucose"].mean(), "glucose_sd": b["glucose"].std(),
                     "hba1c": b["hba1c"].iloc[0], "sex_male": int(b["sex_male"].iloc[0])})
    return pd.DataFrame(rows)


def seed_r2(pred):
    P = pd.read_csv(pred)
    out = []
    for s, d in P.groupby("split"):
        sse = ((d["yhat"] - d["y"]) ** 2).sum()
        sst = ((d["y"] - d["y"].mean()) ** 2).sum()
        out.append({"seed": s, "r2": 1 - sse / sst, "rmse": np.sqrt(sse / len(d))})
    return pd.DataFrame(out)


def main(res):
    res = Path(res)
    out = res / "summary"
    out.mkdir(exist_ok=True)
    C = cohort(res / "features")
    C.to_csv(out / "table2_cohort.csv", index=False)

    H = pd.read_csv(res / "experiments" / "hypotheses.csv")
    H.to_csv(out / "table3_registered.csv", index=False)
    H6 = pd.read_csv(res / "experiments_ea6" / "hypotheses.csv")
    S = H.merge(H6, on=["hypothesis", "statement"], suffixes=("_primary", "_ea6"))
    S["verdict_changes"] = S["supported_primary"] != S["supported_ea6"]
    S.to_csv(out / "tableS1_ea6.csv", index=False)

    E1 = seed_r2(res / "experiments" / "predictions" / "E1_random_fullkl.csv.gz")
    E1.to_csv(out / "e1_seed_r2.csv", index=False)

    M = pd.read_csv(res / "experiments" / "metrics.csv")
    M6 = pd.read_csv(res / "experiments_ea6" / "metrics.csv")
    info = json.loads((res / "experiments" / "run_info.json").read_text())
    num = {"run_info": info,
           "cohort": {"n_participants_dataset": len(C), "n_retained": int(C["rule7_retained"].sum()),
                      "readings_total": int(C["cgm_readings"].sum()),
                      "readings_after_warmup": int(C["after_warmup"].sum()),
                      "readings_with_e4": int(C["with_e4"].sum()),
                      "readings_analysed": int(C.loc[C["rule7_retained"], "with_e4"].sum()),
                      "hours_median": float(C.loc[C["rule7_retained"], "hours_usable"].median()),
                      "hours_min": float(C.loc[C["rule7_retained"], "hours_usable"].min()),
                      "hours_max": float(C.loc[C["rule7_retained"], "hours_usable"].max())},
           "e1_seed_r2_mean": float(E1["r2"].mean()), "e1_seed_r2_sd": float(E1["r2"].std()),
           "e1_seed_r2_min": float(E1["r2"].min()), "e1_seed_r2_max": float(E1["r2"].max()),
           "e1_approximately_reproduced": bool(E1["r2"].mean() >= 0.63),
           "metrics": {f"{r.config}|{r.metric}": [r.value, r.ci_low, r.ci_high] for r in M.itertuples()},
           "metrics_ea6": {f"{r.config}|{r.metric}": [r.value, r.ci_low, r.ci_high] for r in M6.itertuples()},
           "verdict_changes_ea6": S.loc[S["verdict_changes"], "hypothesis"].tolist()}
    ea = res / "exploratory"
    if (ea / "ea_metrics.csv").exists():
        E = pd.read_csv(ea / "ea_metrics.csv")
        num["ea_metrics"] = {f"{r.config}|{r.metric}": [r.value, r.ci_low, r.ci_high] for r in E.itertuples()}
        K = pd.read_csv(ea / "ea_contrasts.csv")
        num["ea_contrasts"] = {f"{r.contrast}|{r.metric}": [r.estimate, r.ci_low, r.ci_high] for r in K.itertuples()}
        num["ea3"] = pd.read_csv(ea / "ea3_ceiling.csv").set_index("scope")["ceiling_r2"].to_dict()
        sh = pd.read_csv(ea / "ea1_shap.csv")
        num["ea1_group_share"] = sh.groupby(["scheme", "group"])["share"].sum().unstack().to_dict(orient="index")
        num["ea1_top5"] = {s: d.nlargest(5, "mean_abs_shap")["feature"].tolist() for s, d in sh.groupby("scheme")}
    (out / "numbers.json").write_text(json.dumps(num, indent=2, default=float))
    print("summary written to", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results")


# ---------------------------------------------------------------- markdown tables for the manuscript
LAB = {"E1_random_fullkl": ("E1", "FULL-KL", "RANDOM"), "E3_random_time_idp": ("E3", "TIME+ID+P", "RANDOM"),
       "E3_random_elapsed_idp": ("E3", "ELAPSED+ID+P", "RANDOM"), "E3_random_idp": ("E3", "ID+P", "RANDOM"),
       "E2_lopo_fullkl": ("E2", "FULL-KL", "LOPO"), "E2_lopo_fullkl_ridge": ("E2", "FULL-KL (ridge)", "LOPO"),
       "E5_lopo_mean": ("E5", "Training mean", "LOPO"), "E4_lopo_mean": ("E4", "Training mean", "LOPO (14)"),
       "E4_lopo_timemealid": ("E4", "TIME+MEAL+ID", "LOPO (14)"), "E4_lopo_fullb": ("E4", "FULL-B", "LOPO (14)"),
       "E4_lopo_fullb_ridge": ("E4", "FULL-B (ridge)", "LOPO (14)"),
       **{f"E6_blocked_{b}": ("E6", "FULL-KL without sex", f"BLOCKED-{b}") for b in X.BUFFERS}}


def fmt_ci(v, lo, hi, d):
    f = lambda x: f"{x:.{d}f}".replace("-", "−")
    sep = "–" if lo >= 0 else " to "
    return f"{f(v)} ({f(lo)}{sep}{f(hi)})"


def md_tables(res):
    res = Path(res)
    C = cohort(res / "features")
    t2 = ["| ID | Sex | HbA1c (%) | CGM readings | After warm-up | With E4 data | Usable hours | Analysed | Valid pulse (%) | Valid EDA (%) |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for r in C.itertuples():
        an = "Yes" if r.rule7_retained else "No (rule 7)"
        an += "" if r.meal_features or not r.rule7_retained else ", no MEAL"
        t2.append(f"| {r.participant} | {'M' if r.sex_male else 'F'} | {r.hba1c:.1f} | {r.cgm_readings:,} | {r.after_warmup:,} | "
                  f"{r.with_e4:,} | {r.hours_usable:.0f} | {an} | {r.pct_pulse_valid:.0f} | {r.pct_eda_valid:.0f} |")
    t2.append(f"| Total | 9 F, 7 M | 5.3–6.4 | {C.cgm_readings.sum():,} | {C.after_warmup.sum():,} | {C.with_e4.sum():,} | | 15 | | |")
    M = pd.read_csv(res / "experiments" / "metrics.csv")
    g = lambda k, m: M[(M.config == k) & (M.metric == m)].iloc[0]
    t3 = ["| Exp. | Inputs | Evaluation | R² | RMSE (mg/dL) | MARD (%) | Zone A (%) | Zones A+B (%) |",
          "|---|---|---|---|---|---|---|---|"]
    for k, (e, inp, ev) in LAB.items():
        if k not in set(M.config):
            continue
        r2, rm, ma, za, zab = (g(k, m) for m in ["r2", "rmse", "mard", "clarke_a", "clarke_ab"])
        t3.append(f"| {e} | {inp} | {ev} | {fmt_ci(r2.value, r2.ci_low, r2.ci_high, 3)} | {fmt_ci(rm.value, rm.ci_low, rm.ci_high, 1)} | "
                  f"{ma.value:.1f} | {za.value:.1f} | {zab.value:.1f} |")
    H = pd.read_csv(res / "experiments" / "hypotheses.csv")
    verdict = lambda h, s: ("Supported" if s else ("Not established" if h in ("H2", "H2b") else "Not supported"))
    t4 = ["| Test | Registered claim | Estimate (95% CI) | Holm *p* | Result |", "|---|---|---|---|---|"]
    for r in H.itertuples():
        d = 1 if r.hypothesis == "H6" else (2 if r.hypothesis == "H4" else 3)
        if r.hypothesis == "H7":
            d = 4
        stmt = r.statement.replace(" - ", " − ").replace("R2", "R²").replace(" (non-inferiority)", "").replace(">=", "≥")
        p = "0.0008" if r.p_holm < 0.001 else f"{r.p_holm:.3f}".rstrip("0").rstrip(".") if r.p_holm < 1 else "1.0"
        prim = " (primary)" if r.primary else ""
        t4.append(f"| {r.hypothesis}{prim} | {stmt} | {fmt_ci(r.estimate, r.ci_low, r.ci_high, d)} | {p} | {verdict(r.hypothesis, r.supported)} |")
    out = {"TABLE2": "\n".join(t2), "TABLE3": "\n".join(t3), "TABLE4": "\n".join(t4)}
    if (res / "experiments_ea6" / "hypotheses.csv").exists():
        H6 = pd.read_csv(res / "experiments_ea6" / "hypotheses.csv")
        ts = ["| Test | Primary: estimate (95% CI) | Primary Holm *p* | EA6: estimate (95% CI) | EA6 Holm *p* | Verdict changes? |",
              "|---|---|---|---|---|---|"]
        for a, b in zip(H.itertuples(), H6.itertuples()):
            d = 1 if a.hypothesis == "H6" else (2 if a.hypothesis == "H4" else (4 if a.hypothesis == "H7" else 3))
            pf = lambda p: "0.0008" if p < 0.001 else (f"{p:.3f}" if p < 1 else "1.0")
            ts.append(f"| {a.hypothesis} | {fmt_ci(a.estimate, a.ci_low, a.ci_high, d)} | {pf(a.p_holm)} | "
                      f"{fmt_ci(b.estimate, b.ci_low, b.ci_high, d)} | {pf(b.p_holm)} | {'Yes' if a.supported != b.supported else 'No'} |")
        out["TABLES1"] = "\n".join(ts)
    return out
