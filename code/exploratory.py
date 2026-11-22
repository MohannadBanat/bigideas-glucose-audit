"""
Exploratory analyses EA1-EA5 (pre-registration §9, osf.io/cvfa3). NOT registered tests:
no Holm correction, no "supported" verdicts; estimates and 95% participant-bootstrap CIs only.

Written and committed on 22 Nov 2026 before the registered results (experiments.py) were
inspected. Each analysis follows the one-line description in §9; where §9 leaves a detail
open, the choice is fixed here, in the docstring of each function, before running.

Usage:
    python code/exploratory.py results/features data/big-ideas-1.1.3 results/exploratory

Outputs in OUT_DIR:
    ea_metrics.csv       pooled metrics with 95% CIs for every exploratory configuration
    ea_contrasts.csv     paired differences with 95% CIs
    ea1_shap.csv         mean |SHAP| per feature, RANDOM (seed 0) vs LOPO (mean over folds)
    ea3_ceiling.csv      CGM-noise ceiling on R2, pooled and within participant
    predictions/         test predictions
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from xgboost import DMatrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experiments as X  # noqa: E402
from features import meal_features  # noqa: E402

G6_MARD = 0.10           # overall MARD of the Dexcom G6 vs reference (Wadwa et al. 2018)
FOOD_SHIFT_016_MIN = -180  # EA4b: shift suggested by the alignment check (results/time_of_day)


def save_run(P, name, out):
    P.to_csv(out / "predictions" / f"{name}.csv.gz", index=False)
    return P


# ------------------------------------------------------------------ EA1
def ea1_shap(F, out):
    """FULL-KL XGBoost refitted exactly as in E1 (seed-0 RANDOM split) and E2 (every LOPO fold).
    TreeSHAP values from XGBoost's pred_contribs on the test readings (standardised inputs).
    Reported: mean |SHAP| per feature; for LOPO, averaged over folds (features not selected
    in a fold count as 0). Group shares: PHYS, ACT, TIME, sex."""
    rows = []
    FULL_KL = X.PHYS + X.ACT + X.TIME + ["sex_male"]
    schemes = [("RANDOM", [next(X.random_splits(F))], False)] + [("LOPO", list(X.lopo_splits(F)), True)]
    for scheme, splits, grouped in schemes:
        acc = []
        for k, tr, te in splits:
            train, test = F.iloc[tr], F.iloc[te]
            cols = X.select_kl(train, train["glucose"], FULL_KL, k)
            s = X.make_search("xgb", grouped, False)
            s.fit(train[cols], train["glucose"], **({"groups": train["participant"]} if grouped else {}))
            pipe = s.best_estimator_
            Z = pipe[:-1].transform(test[cols])
            contrib = pipe[-1].get_booster().predict(DMatrix(Z), pred_contribs=True)[:, :-1]
            v = pd.Series(np.abs(contrib).mean(axis=0), index=cols).reindex(FULL_KL, fill_value=0.0)
            acc.append(v)
            print(f"  EA1 {scheme}: split {k} done", flush=True)
        m = pd.concat(acc, axis=1).mean(axis=1)
        for f, val in m.items():
            rows.append({"scheme": scheme, "feature": f, "mean_abs_shap": val})
    S = pd.DataFrame(rows)
    grp = {**{f: "PHYS" for f in X.PHYS}, **{f: "ACT" for f in X.ACT}, **{f: "TIME" for f in X.TIME}, "sex_male": "sex"}
    S["group"] = S["feature"].map(grp)
    S["share"] = S["mean_abs_shap"] / S.groupby("scheme")["mean_abs_shap"].transform("sum")
    S.to_csv(out / "ea1_shap.csv", index=False)


# ------------------------------------------------------------------ EA2
def ea2_personalised(F, out):
    """Per-participant models, as in Bent et al. (2021): train on the first 50% of each
    participant's readings (by time), test on the last 50%. Baseline: the participant's
    training mean. Model: XGBoost on PHYS + ACT + TIME (sex and HbA1c are constant within a
    participant), same grid, inner 5-fold CV over contiguous folds (no shuffling)."""
    rows_m, rows_x = [], []
    cols = X.PHYS + X.ACT + X.TIME
    for p, d in F.groupby("participant"):
        d = d.sort_values("ts")
        h = len(d) // 2
        tr, te = d.iloc[:h], d.iloc[h:]
        base = pd.DataFrame({"participant": p, "ts": te["ts"].to_numpy(), "y": te["glucose"].to_numpy()})
        rows_m.append(base.assign(yhat=tr["glucose"].mean()))
        s = X.make_search("xgb", False, False)
        s.cv = KFold(n_splits=5, shuffle=False)
        s.fit(tr[cols], tr["glucose"])
        rows_x.append(base.assign(yhat=s.predict(te[cols])))
        print(f"  EA2: participant {p} done", flush=True)
    return (save_run(pd.concat(rows_m, ignore_index=True), "EA2_personal_mean", out),
            save_run(pd.concat(rows_x, ignore_index=True), "EA2_personal_xgb", out))


# ------------------------------------------------------------------ EA3
def ea3_ceiling(F, out):
    """CGM-noise ceiling. If the CGM reading = true glucose x (1 + e), with |e| averaging the
    G6 MARD of 10% and e normal, then SD(e) = 0.10 x sqrt(pi/2). The sensor-noise variance is
    mean((SD(e) y)^2). Ceiling R2 for predicting the true glucose from a CGM-trained model is
    1 - noise variance / CGM variance (the variance of y that is not sensor noise). Reported
    pooled over readings and within participant (variance around each participant's mean, the
    part LOPO models must explain)."""
    sd = G6_MARD * np.sqrt(np.pi / 2)
    y = F["glucose"].to_numpy()
    noise = np.mean((sd * y) ** 2)
    rows = [{"scope": "pooled", "var_cgm": y.var(), "var_noise": noise, "ceiling_r2": 1 - noise / y.var()}]
    for p, d in F.groupby("participant"):
        yy = d["glucose"].to_numpy()
        nn = np.mean((sd * yy) ** 2)
        rows.append({"scope": p, "var_cgm": yy.var(), "var_noise": nn, "ceiling_r2": 1 - nn / yy.var()})
    within = F.groupby("participant")["glucose"].transform(lambda s: s - s.mean()).to_numpy()
    rows.append({"scope": "within-participant (pooled)", "var_cgm": within.var(), "var_noise": noise,
                 "ceiling_r2": 1 - noise / within.var()})
    pd.DataFrame(rows).assign(sd_rel_error=sd).to_csv(out / "ea3_ceiling.csv", index=False)


# ------------------------------------------------------------------ EA4
def shifted_meal_016(F, small):
    """MEAL features for 016 recomputed from a copy of its food log in which every time
    (time_begin, time_end) is moved by FOOD_SHIFT_016_MIN. The dataset files are not changed."""
    import tempfile
    import features as FT
    d = F[F["participant"] == "016"]
    src = Path(small) / "016" / "Food_Log_016.csv"
    food = pd.read_csv(src, encoding="utf-8-sig")
    for c in [c for c in food.columns if c.startswith("time_")]:
        t = pd.to_datetime(food[c], errors="coerce") + pd.Timedelta(minutes=FOOD_SHIFT_016_MIN)
        food[c] = t.dt.strftime("%Y-%m-%d %H:%M:%S")
    old = FT.MEAL_EXCLUDED
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "016").mkdir()
        food.to_csv(Path(tmp) / "016" / "Food_Log_016.csv", index=False)
        FT.MEAL_EXCLUDED = set()
        try:
            M = FT.meal_features("016", Path(tmp), d["ts"].reset_index(drop=True))
        finally:
            FT.MEAL_EXCLUDED = old
    G = F.copy()
    for c in M.columns:
        G[c] = G[c].astype(object) if c == "meal_ok" else G[c]
        G.loc[d.index, c] = M[c].to_numpy()
    G["meal_ok"] = G["meal_ok"].astype(bool)
    return G


def ea4(F, small, out, res):
    """EA4a: E4 on all 15 participants retained under rule 7, without MEAL features (LOPO):
    population mean; TIME+ID; PHYS+ACT+TIME+ID (FULL-B without MEAL).
    EA4b: E4 on 15 MEAL participants (the 14 plus 016 with the -3 h food-log shift):
    population mean; TIME+MEAL+ID; FULL-B. Same models and grids as E4."""
    res["EA4a_lopo_mean"] = X.run(F, "EA4a_lopo_mean", X.lopo_splits(F), [], "mean", True, False, out)
    res["EA4a_lopo_timeid"] = X.run(F, "EA4a_lopo_timeid", X.lopo_splits(F), X.TIME + X.ID, "xgb", True, False, out)
    res["EA4a_lopo_fullb_nomeal"] = X.run(F, "EA4a_lopo_fullb_nomeal", X.lopo_splits(F),
                                          X.PHYS + X.ACT + X.TIME + X.ID, "xgb", True, False, out)
    G = shifted_meal_016(F, small)
    meal = sorted(G.loc[G["meal_ok"].astype(bool), "participant"].unique())
    GM = G[G["participant"].isin(meal) & G["meal_ok"].astype(bool)].reset_index(drop=True)
    res["EA4b_lopo_mean"] = X.run(GM, "EA4b_lopo_mean", X.lopo_splits(GM), [], "mean", True, False, out)
    res["EA4b_lopo_timemealid"] = X.run(GM, "EA4b_lopo_timemealid", X.lopo_splits(GM), X.TIME + X.MEAL + X.ID, "xgb", True, False, out)
    res["EA4b_lopo_fullb"] = X.run(GM, "EA4b_lopo_fullb", X.lopo_splits(GM),
                                   X.PHYS + X.ACT + X.TIME + X.MEAL + X.ID, "xgb", True, False, out)
    return meal


# ------------------------------------------------------------------ main
def main(feature_dir, small, out):
    out = Path(out)
    (out / "predictions").mkdir(parents=True, exist_ok=True)
    F, _ = X.load(feature_dir, self_test=False)
    res = {}
    # EA5: E2 without sex (FULL-KL minus sex, KL selection, LOPO)
    res["EA5_lopo_fullkl_nosex"] = X.run(F, "EA5_lopo_fullkl_nosex", X.lopo_splits(F),
                                         X.PHYS + X.ACT + X.TIME, "xgb", True, False, out, kl_select=True)
    res["EA2_personal_mean"], res["EA2_personal_xgb"] = ea2_personalised(F, out)
    meal_b = ea4(F, small, out, res)
    ea3_ceiling(F, out)
    ea1_shap(F, out)

    pids = sorted(F["participant"].unique())
    B = {"all": X.Bootstrap(pids), "meal_b": X.Bootstrap(meal_b)}
    boot, rows = {}, []
    for k, P in res.items():
        Bk = B["meal_b"] if k.startswith("EA4b") else B["all"]
        point, b = Bk.stats(P)
        boot[k] = (point, b)
        for m in point:
            lo, hi = X.ci(b[m])
            rows.append({"config": k, "metric": m, "value": point[m], "ci_low": lo, "ci_high": hi})
    pd.DataFrame(rows).to_csv(out / "ea_metrics.csv", index=False)

    # paired contrasts that need the registered E2 predictions use the same bootstrap weights
    reg = Path(feature_dir).parent / "experiments" / "predictions" / "E2_lopo_fullkl.csv.gz"
    C = []

    def contrast(name, a, b, metric):
        pa, ba = boot[a]
        pb, bb = boot[b]
        d = ba[metric] - bb[metric]
        C.append({"contrast": name, "metric": metric, "estimate": pa[metric] - pb[metric],
                  "ci_low": X.ci(d)[0], "ci_high": X.ci(d)[1]})

    if reg.exists():
        boot["E2_lopo_fullkl"] = B["all"].stats(pd.read_csv(reg, dtype={"participant": str}))
        contrast("EA5: FULL-KL without sex - with sex (LOPO)", "EA5_lopo_fullkl_nosex", "E2_lopo_fullkl", "r2")
        contrast("EA5: FULL-KL without sex - with sex (LOPO)", "EA5_lopo_fullkl_nosex", "E2_lopo_fullkl", "rmse")
    contrast("EA2: personalised XGBoost - participant mean", "EA2_personal_xgb", "EA2_personal_mean", "r2")
    contrast("EA2: personalised XGBoost - participant mean", "EA2_personal_xgb", "EA2_personal_mean", "rmse")
    contrast("EA4a: RMSE(TIME+ID) - RMSE(PHYS+ACT+TIME+ID)", "EA4a_lopo_timeid", "EA4a_lopo_fullb_nomeal", "rmse")
    contrast("EA4a: R2(PHYS+ACT+TIME+ID) - R2(mean)", "EA4a_lopo_fullb_nomeal", "EA4a_lopo_mean", "r2")
    contrast("EA4b: RMSE(TIME+MEAL+ID) - RMSE(FULL-B)", "EA4b_lopo_timemealid", "EA4b_lopo_fullb", "rmse")
    contrast("EA4b: R2(FULL-B) - R2(mean)", "EA4b_lopo_fullb", "EA4b_lopo_mean", "r2")
    pd.DataFrame(C).to_csv(out / "ea_contrasts.csv", index=False)
    (out / "run_info.json").write_text(json.dumps({"n_boot": X.N_BOOT, "boot_seed": X.BOOT_SEED,
                                                   "participants": pids, "ea4b_meal_participants": meal_b,
                                                   "food_shift_016_min": FOOD_SHIFT_016_MIN,
                                                   "g6_mard": G6_MARD}, indent=2))
    print("exploratory analyses written to", out)


if __name__ == "__main__":
    main(*sys.argv[1:4])
