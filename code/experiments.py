"""
Registered experiments E1-E6 (docs/02_preregistration_draft.md, sections 5-8).

DO NOT RUN ON THE REAL TARGET BEFORE THE OSF REGISTRATION IS FILED.
`--self-test` runs the whole pipeline on a synthetic target (the real glucose
column is replaced by noise), so the code can be checked without seeing any
result.

Usage:
    python code/experiments.py FEATURE_DIR OUT_DIR --osf-doi 10.17605/OSF.IO/XXXXX
    python code/experiments.py FEATURE_DIR OUT_DIR --self-test [--quick]

Outputs in OUT_DIR:
    predictions/<experiment>__<config>.csv.gz   every test prediction
    metrics.csv                                 pooled metrics with 95% bootstrap CIs
    metrics_by_participant.csv
    hypotheses.csv                              registered tests, raw and Holm p values
    run_info.json                               versions, seeds, OSF DOI, self-test flag
"""
import argparse
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.model_selection import GridSearchCV, GroupKFold, KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

SEEDS = list(range(20))
N_BOOT = 10_000
BOOT_SEED = 20261122
ALPHA = 0.05
H2_GUARD = 0.30          # E1 R2 lower bound needed before H2/H2b are interpreted (pre-registration §7)
BUFFERS = [0, 30, 60, 120, 240]
N_BLOCKS = 5

PHYS = ["eda_tonic_mean", "eda_tonic_sd", "eda_tonic_slope", "eda_tonic_min", "eda_tonic_max",
        "eda_tonic_range", "eda_scr_count", "eda_scr_amp_mean", "eda_phasic_area",
        "pulse_rate_mean", "pulse_rate_sd", "sdnn_ms", "rmssd_ms", "pulse_amp_sd", "pulse_coverage",
        "hr_mean", "temp_mean", "temp_sd", "temp_slope"]
ACT = ["acc_2h_min", "acc_2h_max", "acc_2h_mean", "acc_5m_mean", "acc_5m_sd"]
TIME = ["min_from_midnight", "min_sin", "min_cos"]
ELAPSED = ["elapsed_min"]
MEAL = ["min_since_meal", "carb_2h", "carb_8h", "carb_24h", "sugar_2h", "sugar_8h", "sugar_24h"]
ID = ["sex_male", "hba1c"]

XGB_GRID = {"m__max_depth": [3, 6], "m__n_estimators": [100, 300],
            "m__learning_rate": [0.05, 0.1], "m__subsample": [0.8]}
RIDGE_GRID = {"m__alpha": [0.1, 1, 10, 100]}


# ---------------------------------------------------------------- data
def load(feature_dir, self_test):
    F = pd.concat([pd.read_csv(p, dtype={"participant": str})
                   for p in sorted(Path(feature_dir).glob("features_*.csv.gz"))], ignore_index=True)
    F = F[F["e4_ok"] & ~F["cgm_warmup"]].reset_index(drop=True)
    F["ts"] = pd.to_datetime(F["ts"])
    if self_test:
        rng = np.random.default_rng(0)
        F["glucose"] = rng.normal(110, 20, len(F)).clip(40, 400)
    for p in F["participant"].unique():          # participant one-hot (ID+P)
        F[f"pid_{p}"] = (F["participant"] == p).astype(int)
    return F


def pid_cols(F):
    return [c for c in F.columns if c.startswith("pid_")]


# ---------------------------------------------------------------- models
def make_search(kind, grouped, quick):
    if kind == "xgb":
        est = XGBRegressor(tree_method="hist", n_jobs=-1, random_state=0, verbosity=0)
        grid = {"m__max_depth": [3], "m__n_estimators": [50], "m__learning_rate": [0.1],
                "m__subsample": [0.8]} if quick else XGB_GRID
    else:
        est, grid = Ridge(), ({"m__alpha": [1]} if quick else RIDGE_GRID)
    pipe = Pipeline([("i", SimpleImputer(strategy="median", keep_empty_features=True)),
                     ("s", StandardScaler()), ("m", est)])
    cv = GroupKFold(n_splits=5) if grouped else KFold(n_splits=5, shuffle=True, random_state=0)
    return GridSearchCV(pipe, grid, cv=cv, scoring="neg_root_mean_squared_error", n_jobs=1)


def select_kl(X, y, cols, seed):
    """Karunarathna & Liang's step: top 30 by random-forest importance, training data only."""
    if len(cols) <= 30:
        return cols
    rf = RandomForestRegressor(n_estimators=200, random_state=seed, n_jobs=-1)
    rf.fit(SimpleImputer(strategy="median").fit_transform(X[cols]), y)
    return [cols[i] for i in np.argsort(rf.feature_importances_)[::-1][:30]]


def fit_predict(train, test, cols, kind, grouped, quick, seed=0, kl_select=False):
    if kind == "mean":
        return np.full(len(test), train["glucose"].mean()), {}
    if kl_select:
        cols = select_kl(train, train["glucose"], cols, seed)
    s = make_search(kind, grouped, quick)
    fit_kw = {"groups": train["participant"]} if grouped else {}
    s.fit(train[cols], train["glucose"], **fit_kw)
    return s.predict(test[cols]), {"best": s.best_params_, "n_features": len(cols)}


# ---------------------------------------------------------------- splits
def random_splits(F):
    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        test = rng.random(len(F)) < 0.2
        yield seed, np.flatnonzero(~test), np.flatnonzero(test)


def lopo_splits(F):
    for k, p in enumerate(sorted(F["participant"].unique())):
        yield k, np.flatnonzero(F["participant"] != p), np.flatnonzero(F["participant"] == p)


def blocked_splits(F, buffer_min):
    """Block k of every participant is tested together; training readings within
    buffer_min of that participant's test block are dropped."""
    block = np.zeros(len(F), dtype=int)
    for p, idx in F.groupby("participant").indices.items():
        order = idx[np.argsort(F["ts"].to_numpy()[idx])]
        block[order] = np.minimum(np.arange(len(order)) * N_BLOCKS // len(order), N_BLOCKS - 1)
    ts = F["ts"].to_numpy()
    for k in range(N_BLOCKS):
        test = block == k
        keep = ~test
        if buffer_min:
            for p, idx in F.groupby("participant").indices.items():
                tb = idx[test[idx]]
                lo, hi = ts[tb].min(), ts[tb].max()
                pad = np.timedelta64(int(buffer_min), "m")
                near = (ts[idx] >= lo - pad) & (ts[idx] <= hi + pad)
                keep[idx[near]] = False
        yield k, np.flatnonzero(keep), np.flatnonzero(test)


# ---------------------------------------------------------------- run one config
def run(F, name, splits, cols, kind, grouped, quick, out, kl_select=False):
    rows, info = [], []
    for k, tr, te in splits:
        yhat, meta = fit_predict(F.iloc[tr], F.iloc[te], cols, kind, grouped, quick, seed=k,
                                 kl_select=kl_select)
        rows.append(pd.DataFrame({"participant": F["participant"].to_numpy()[te],
                                  "ts": F["ts"].to_numpy()[te],
                                  "y": F["glucose"].to_numpy()[te], "yhat": yhat, "split": k}))
        info.append({"split": k, **{kk: str(v) for kk, v in meta.items()}})
        print(f"  {name}: split {k} done", flush=True)
    P = pd.concat(rows, ignore_index=True)
    P.to_csv(out / "predictions" / f"{name}.csv.gz", index=False)
    pd.DataFrame(info).to_csv(out / "predictions" / f"{name}__fits.csv", index=False)
    return P


# ---------------------------------------------------------------- metrics
def clarke_zone(ref, pred):
    """Clarke et al. (1987) zones, mg/dL. Returns array of 'A'..'E'."""
    r, p = np.asarray(ref, float), np.asarray(pred, float)
    z = np.full(r.shape, "B", dtype="<U1")
    A = ((r <= 70) & (p <= 70)) | ((p <= 1.2 * r) & (p >= 0.8 * r))
    E = ((r >= 180) & (p <= 70)) | ((r <= 70) & (p >= 180))
    C = (((r >= 70) & (r <= 290)) & (p >= r + 110)) | (((r >= 130) & (r <= 180)) & (p <= (7 / 5) * r - 182))
    D = ((r >= 240) & (p >= 70) & (p <= 180)) | ((r <= 175 / 3) & (p <= 180) & (p >= 70)) | \
        (((r >= 175 / 3) & (r <= 70)) & (p >= (6 / 5) * r))
    z[D] = "D"; z[C] = "C"; z[E] = "E"; z[A] = "A"
    return z


def participant_sums(P):
    """Additive sufficient statistics per participant."""
    e = P["yhat"] - P["y"]
    zone = clarke_zone(P["y"], P["yhat"])
    g = P.assign(sse=e ** 2, ae_rel=np.abs(e) / P["y"], y2=P["y"] ** 2,
                 ab=np.isin(zone, ["A", "B"]).astype(float), a=(zone == "A").astype(float))
    return g.groupby("participant").agg(n=("y", "size"), sy=("y", "sum"), sy2=("y2", "sum"),
                                         sse=("sse", "sum"), are=("ae_rel", "sum"),
                                         ab=("ab", "sum"), a=("a", "sum"))


def metrics_from(S):
    """S: DataFrame or (B x columns) arrays of summed statistics."""
    n, sy, sy2, sse = S["n"], S["sy"], S["sy2"], S["sse"]
    sst = sy2 - sy ** 2 / n
    return {"r2": 1 - sse / sst, "rmse": np.sqrt(sse / n), "mard": 100 * S["are"] / n,
            "clarke_ab": 100 * S["ab"] / n, "clarke_a": 100 * S["a"] / n}


class Bootstrap:
    def __init__(self, participants):
        self.p = sorted(participants)
        rng = np.random.default_rng(BOOT_SEED)
        draws = rng.integers(0, len(self.p), size=(N_BOOT, len(self.p)))
        self.W = np.zeros((N_BOOT, len(self.p)))
        for j in range(len(self.p)):
            self.W[:, j] = (draws == j).sum(axis=1)

    def stats(self, P):
        S = participant_sums(P).reindex(self.p)
        if S.isna().any().any():
            raise ValueError("bootstrap participants missing from predictions")
        point = metrics_from(S.sum())
        boot = metrics_from({c: self.W @ S[c].to_numpy() for c in S.columns})
        return point, boot


def ci(b):
    return np.nanpercentile(b, 2.5), np.nanpercentile(b, 97.5)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("feature_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--osf-doi")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--quick", action="store_true", help="tiny grids and 2 seeds (self-test only)")
    a = ap.parse_args()
    if not a.self_test and not a.osf_doi:
        sys.exit("Refusing to run on real glucose without --osf-doi: file the registration first.")
    if a.quick and not a.self_test:
        sys.exit("--quick is for --self-test only")
    global SEEDS, N_BOOT
    if a.quick:
        SEEDS, N_BOOT = [0, 1], 500

    out = Path(a.out_dir)
    (out / "predictions").mkdir(parents=True, exist_ok=True)
    F = load(a.feature_dir, a.self_test)
    PID = pid_cols(F)
    meal_pids = sorted(F.loc[F["meal_ok"], "participant"].unique())
    FM = F[F["participant"].isin(meal_pids) & F["meal_ok"]].reset_index(drop=True)
    FULL_KL = PHYS + ACT + TIME + ["sex_male"]
    FULL_B = PHYS + ACT + TIME + MEAL + ID
    q = a.quick
    res = {}

    # E1/E2 (FULL-KL), E3 shortcut sets: RANDOM, ungrouped inner CV for E1, grouped otherwise
    res["E1_random_fullkl"] = run(F, "E1_random_fullkl", random_splits(F), FULL_KL, "xgb", False, q, out, kl_select=True)
    res["E2_lopo_fullkl"] = run(F, "E2_lopo_fullkl", lopo_splits(F), FULL_KL, "xgb", True, q, out, kl_select=True)
    for nm, cols in [("time_idp", TIME + ID + PID), ("elapsed_idp", ELAPSED + ID + PID), ("idp", ID + PID)]:
        res[f"E3_random_{nm}"] = run(F, f"E3_random_{nm}", random_splits(F), cols, "xgb", False, q, out)
    # E4 on the MEAL participants, LOPO
    res["E4_lopo_mean"] = run(FM, "E4_lopo_mean", lopo_splits(FM), [], "mean", True, q, out)
    res["E4_lopo_timemealid"] = run(FM, "E4_lopo_timemealid", lopo_splits(FM), TIME + MEAL + ID, "xgb", True, q, out)
    res["E4_lopo_fullb"] = run(FM, "E4_lopo_fullb", lopo_splits(FM), FULL_B, "xgb", True, q, out)
    # E5: population-mean baseline under LOPO, all participants
    res["E5_lopo_mean"] = run(F, "E5_lopo_mean", lopo_splits(F), [], "mean", True, q, out)
    # E6: blocked splits, FULL-KL inputs without sex
    for b in BUFFERS:
        res[f"E6_blocked_{b}"] = run(F, f"E6_blocked_{b}", blocked_splits(F, b), PHYS + ACT + TIME, "xgb", True, q, out)
    # secondary model (ridge) for the main comparisons
    res["E2_lopo_fullkl_ridge"] = run(F, "E2_lopo_fullkl_ridge", lopo_splits(F), FULL_KL, "ridge", True, q, out)
    res["E4_lopo_fullb_ridge"] = run(FM, "E4_lopo_fullb_ridge", lopo_splits(FM), FULL_B, "ridge", True, q, out)

    # ------------------------------------------------ metrics with bootstrap CIs
    B_all, B_meal = Bootstrap(F["participant"].unique()), Bootstrap(meal_pids)
    boot, rows, by_p = {}, [], []
    for k, P in res.items():
        Bk = B_meal if k.startswith("E4") else B_all
        point, b = Bk.stats(P)
        boot[k] = b
        for m in point:
            lo, hi = ci(b[m])
            rows.append({"config": k, "metric": m, "value": point[m], "ci_low": lo, "ci_high": hi})
        S = participant_sums(P)
        by_p.append(pd.DataFrame(metrics_from(S)).assign(config=k).reset_index())
    pd.DataFrame(rows).to_csv(out / "metrics.csv", index=False)
    pd.concat(by_p).to_csv(out / "metrics_by_participant.csv", index=False)

    # ------------------------------------------------ registered tests (one-sided bootstrap)
    def pval(stat_boot, null_side):          # fraction of resamples on the null side
        s = np.asarray(stat_boot)
        s = s[np.isfinite(s)]
        return (1 + np.sum(null_side(s))) / (1 + len(s))

    def point(k, m):
        return next(r["value"] for r in rows if r["config"] == k and r["metric"] == m)

    R = lambda k: boot[k]["r2"]
    H = []
    d = R("E1_random_fullkl") - R("E2_lopo_fullkl")
    H.append(("H1", "R2(RANDOM) - R2(LOPO) > 0.30", point("E1_random_fullkl", "r2") - point("E2_lopo_fullkl", "r2"),
              *ci(d), pval(d, lambda s: s <= 0.30), True))
    for h, k, lab in [("H2", "E3_random_time_idp", "TIME+ID+P"), ("H2b", "E3_random_elapsed_idp", "ELAPSED+ID+P")]:
        d = R("E1_random_fullkl") - R(k)
        H.append((h, f"R2(FULL-KL) - R2({lab}) < 0.05, RANDOM (non-inferiority)",
                  point("E1_random_fullkl", "r2") - point(k, "r2"), *ci(d), pval(d, lambda s: s >= 0.05), h == "H2b"))
    d = R("E3_random_idp") - 0.5 * R("E1_random_fullkl")
    H.append(("H3", "R2(ID+P) - 0.5 R2(FULL-KL) > 0",
              point("E3_random_idp", "r2") - 0.5 * point("E1_random_fullkl", "r2"), *ci(d), pval(d, lambda s: s <= 0), False))
    d = boot["E4_lopo_timemealid"]["rmse"] - boot["E4_lopo_fullb"]["rmse"]
    H.append(("H4", "RMSE(TIME+MEAL+ID) - RMSE(FULL-B) < 2.0 mg/dL",
              point("E4_lopo_timemealid", "rmse") - point("E4_lopo_fullb", "rmse"), *ci(d), pval(d, lambda s: s >= 2.0), True))
    d = R("E4_lopo_fullb") - R("E4_lopo_mean")
    H.append(("H5", "R2(FULL-B) - R2(mean) < 0.10", point("E4_lopo_fullb", "r2") - point("E4_lopo_mean", "r2"),
              *ci(d), pval(d, lambda s: s >= 0.10), False))
    d = boot["E5_lopo_mean"]["clarke_ab"]
    H.append(("H6", "Clarke A+B of mean baseline >= 90%", point("E5_lopo_mean", "clarke_ab"), *ci(d),
              pval(d, lambda s: s < 90), False))
    d = R("E6_blocked_0") - R("E6_blocked_60")
    H.append(("H7", "R2(BLOCKED-0) - R2(BLOCKED-60) > 0", point("E6_blocked_0", "r2") - point("E6_blocked_60", "r2"),
              *ci(d), pval(d, lambda s: s <= 0), False))
    Hd = pd.DataFrame(H, columns=["hypothesis", "statement", "estimate", "ci_low", "ci_high", "p_one_sided", "primary"])
    # Holm-Bonferroni over the 8 registered tests
    order = np.argsort(Hd["p_one_sided"].to_numpy())
    m, adj, running = len(Hd), np.empty(len(Hd)), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * Hd["p_one_sided"].iloc[i]))
        adj[i] = running
    Hd["p_holm"] = adj
    # Registered guard: H2/H2b are interpretable only if E1's lower one-sided 95% bound of R2 exceeds 0.30
    e1_lower = float(np.nanpercentile(R("E1_random_fullkl"), 5))
    Hd["interpretable"] = ~Hd["hypothesis"].isin(["H2", "H2b"]) | (e1_lower > H2_GUARD)
    Hd["supported"] = (Hd["p_holm"] < ALPHA) & Hd["interpretable"]
    Hd.to_csv(out / "hypotheses.csv", index=False)

    info = {"self_test": a.self_test, "quick": a.quick, "osf_doi": a.osf_doi, "seeds": SEEDS,
            "n_boot": N_BOOT, "h2_guard_e1_r2_lower": e1_lower, "python": platform.python_version(), "numpy": np.__version__,
            "pandas": pd.__version__, "sklearn": sklearn.__version__, "xgboost": xgboost.__version__,
            "n_readings": len(F), "n_participants": F["participant"].nunique(), "meal_participants": meal_pids}
    (out / "run_info.json").write_text(json.dumps(info, indent=2))
    print(Hd.to_string(index=False))


if __name__ == "__main__":
    main()
