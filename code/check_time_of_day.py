"""
Gate check: are clock time and meal timing usable in BIG IDEAs v1.1.3?

The TIME control (E3) and the MEAL feature set both assume that
(a) clock time survived PhysioNet's date-shifting, and
(b) the food log and the Dexcom CGM share one clock.

The first version of this script checked (a) on the food log only. That
cannot detect a food log that is offset from the CGM (for example by
whole days), which would silently corrupt MEAL features. This version adds
three checks per participant:

  1. Coverage: share of meal events that fall inside the CGM recording.
  2. Meal response: mean glucose rise in the 2 h after logged meals,
     compared with the same statistic at random times in the same
     recording (permutation null). Real meals should raise glucose more.
  3. Lag sweeps: the rise statistic recomputed with meal times shifted
     by whole days (-21..+21 d) and by minutes (-180..+180 min). If the
     clocks agree, the best whole-day shift is 0 and the best minute
     shift is near 0.

Usage:
    python code/check_time_of_day.py ./data/big-ideas-1.1.3 [out_dir]

Outputs (in out_dir, default ./results/time_of_day):
    meal_hours_by_participant.csv   clock-hour plausibility from food logs
    alignment_by_participant.csv    checks 1-3 and the per-participant verdict
    lag_sweep_minutes.csv           rise statistic vs minute shift
    lag_sweep_days.csv              rise statistic vs whole-day shift
    glucose_by_hour.csv             mean CGM glucose by clock hour
    summary.txt                     printed go/no-go

Note for the pre-registration: this script reads CGM glucose values. It
does not fit any model, but its outputs must be listed under "already
seen by the authors" in the OSF registration.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20261122
MEAL_GAP_MIN = 30        # entries closer than this are one meal event
MIN_CARB_G = 10          # meal events with fewer carbs are ignored
BASELINE_MIN = 15        # baseline = mean glucose in the 15 min before t
RISE_WINDOW_MIN = 120    # rise = max glucose in (t, t+120 min] - baseline
N_NULL = 2000
MINUTE_LAGS = range(-720, 721, 15)   # +/-12 h, so an hours-scale offset is visible
DAY_LAGS = range(-21, 22)

# Food_Log_003.csv in v1.1.3 has no header row and only 11 columns.
# Mapping inferred from the values (e.g. 8 chicken nuggets -> 19 g carb,
# 20 g protein, matching 3 nuggets -> 7.2 g carb in participant 001).
HEADERLESS_11 = ["date", "time", "time_begin", "logged_food", "amount", "unit",
                 "searched_food", "calorie", "total_carb", "sugar", "protein"]


def find_col(df, *candidates):
    """Return the first column whose lower-cased name contains a candidate."""
    cols = {c.lower().strip(): c for c in df.columns}
    for cand in candidates:
        for low, orig in cols.items():
            if cand in low:
                return orig
    return None


def load_food(path):
    with open(path, encoding="utf-8-sig") as fh:
        first = fh.readline()
    if "logged_food" in first:
        df = pd.read_csv(path, encoding="utf-8-sig")
        header = "present"
    else:
        df = pd.read_csv(path, header=None, encoding="utf-8-sig")
        if df.shape[1] != len(HEADERLESS_11):
            raise ValueError(f"{path}: no header and {df.shape[1]} columns; map them by hand")
        df.columns = HEADERLESS_11
        header = "missing (11-column layout assumed)"
    tcol = find_col(df, "time_begin")
    ts = pd.to_datetime(df[tcol], errors="coerce")
    carb = pd.to_numeric(df[find_col(df, "total_carb")], errors="coerce")
    out = pd.DataFrame({"ts": ts, "carb": carb,
                        "logged_food": df[find_col(df, "logged_food")].astype(str)})
    n_bad = int(out["ts"].isna().sum())
    return out.dropna(subset=["ts"]).sort_values("ts").reset_index(drop=True), header, n_bad


def load_dexcom(path):
    df = pd.read_csv(path)
    etype = find_col(df, "event type")
    if etype is not None:
        df = df[df[etype] == "EGV"]
    tcol = find_col(df, "timestamp")
    vcol = find_col(df, "glucose value")
    out = pd.DataFrame({
        "ts": pd.to_datetime(df[tcol], errors="coerce"),
        "glucose": pd.to_numeric(df[vcol], errors="coerce"),
    }).dropna().sort_values("ts")
    return out.reset_index(drop=True)


def meal_events(food):
    """Merge entries within MEAL_GAP_MIN into events; keep events with enough carbs."""
    new = food["ts"].diff() > pd.Timedelta(minutes=MEAL_GAP_MIN)
    grp = new.cumsum()
    ev = food.groupby(grp).agg(ts=("ts", "first"), carb=("carb", "sum"))
    return ev[ev["carb"] >= MIN_CARB_G].reset_index(drop=True)


class Grid:
    """CGM on a regular 5-min grid (minutes since first reading), with NaN in gaps."""

    def __init__(self, cgm):
        self.t0 = cgm["ts"].iloc[0]
        mins = (cgm["ts"] - self.t0).dt.total_seconds().to_numpy() / 60
        self.grid = np.arange(0, mins[-1] + 5, 5.0)
        g = np.interp(self.grid, mins, cgm["glucose"].to_numpy())
        # blank out grid points more than 15 min from any real reading
        idx = np.searchsorted(mins, self.grid)
        near = np.minimum(np.abs(self.grid - mins[np.clip(idx, 0, len(mins) - 1)]),
                          np.abs(self.grid - mins[np.clip(idx - 1, 0, len(mins) - 1)]))
        g[near > 15] = np.nan
        self.g = g
        self.span = mins[-1]

    def rises(self, t_min):
        """Rise statistic at each time in t_min (minutes since t0). NaN if not covered."""
        t_min = np.asarray(t_min, dtype=float)
        out = np.full(t_min.shape, np.nan)
        nb, nr = BASELINE_MIN // 5, RISE_WINDOW_MIN // 5
        for k, t in enumerate(t_min):
            i = int(round(t / 5))
            if i - nb < 0 or i + nr >= len(self.g):
                continue
            base = self.g[i - nb:i + 1]
            post = self.g[i + 1:i + nr + 1]
            if np.isnan(base).any() or np.isnan(post).mean() > 0.2:
                continue
            out[k] = np.nanmax(post) - base.mean()
        return out


def analyse(pid, food, cgm, rng):
    grid = Grid(cgm)
    ev = meal_events(food)
    t = (ev["ts"] - grid.t0).dt.total_seconds().to_numpy() / 60
    inside = (t >= 0) & (t <= grid.span)
    r0 = grid.rises(t)
    n_used = int(np.isfinite(r0).sum())
    obs = float(np.nanmean(r0)) if n_used else np.nan

    # permutation null: random times inside the recording, same number of events
    null = np.full(N_NULL, np.nan)
    if n_used:
        for b in range(N_NULL):
            rs = grid.rises(rng.uniform(BASELINE_MIN, grid.span - RISE_WINDOW_MIN, size=n_used))
            null[b] = np.nanmean(rs)
    p = float((1 + np.sum(null >= obs)) / (1 + N_NULL)) if n_used else np.nan

    min_rows = []
    for L in MINUTE_LAGS:
        r = grid.rises(t + L)
        n = int(np.isfinite(r).sum())
        min_rows.append({"participant": pid, "lag_min": L,
                         "mean_rise": np.nanmean(r) if n >= 5 else np.nan, "n": n})
    day_rows = []
    for d in DAY_LAGS:
        r = grid.rises(t + d * 1440)
        n = int(np.isfinite(r).sum())
        day_rows.append({"participant": pid, "lag_days": d,
                         "mean_rise": np.nanmean(r) if n >= 5 else np.nan, "n": n})
    mdf, ddf = pd.DataFrame(min_rows), pd.DataFrame(day_rows)
    best_min = int(mdf.loc[mdf["mean_rise"].idxmax(), "lag_min"]) if mdf["mean_rise"].notna().any() else None
    # Only compare day shifts that keep at least half of the events scored at
    # the best-supported shift; otherwise a mean over 5-7 events at the edge of
    # the recording can win by noise alone.
    ddf["comparable"] = ddf["n"] >= 0.5 * ddf["n"].max()
    cmp_ = ddf[ddf["comparable"] & ddf["mean_rise"].notna()]
    best_day = int(cmp_.loc[cmp_["mean_rise"].idxmax(), "lag_days"]) if len(cmp_) else None

    row = {
        "participant": pid,
        "food_first": food["ts"].min(), "food_last": food["ts"].max(),
        "cgm_first": cgm["ts"].min(), "cgm_last": cgm["ts"].max(),
        "n_meal_events": len(ev),
        "pct_events_inside_cgm": round(100 * inside.mean(), 1) if len(ev) else np.nan,
        "n_events_scored": n_used,
        "mean_rise_mg_dl": round(obs, 1) if n_used else np.nan,
        "null_mean_rise_mg_dl": round(float(np.nanmean(null)), 1) if n_used else np.nan,
        "perm_p": round(p, 4) if n_used else np.nan,
        "best_day_shift": best_day,
        "best_minute_shift": best_min,
    }
    checks = {
        "coverage_ok": row["pct_events_inside_cgm"] >= 80,
        "response_ok": n_used >= 10 and p < 0.05,
        "day_ok": best_day == 0,
        "minute_ok": best_min is not None and abs(best_min) <= 60,
    }
    row.update(checks)
    row["aligned"] = all(checks.values())
    return row, mdf, ddf


def meal_hours(pid, food, header, n_bad):
    hour = food["ts"].dt.hour + food["ts"].dt.minute / 60
    first_of_day = food.groupby(food["ts"].dt.date)["ts"].min()
    fod_h = first_of_day.dt.hour + first_of_day.dt.minute / 60
    sb = food[food["logged_food"].str.contains("Standard Breakfast", case=False, na=False)]
    sb_h = sb["ts"].dt.hour + sb["ts"].dt.minute / 60
    return {
        "participant": pid,
        "header": header,
        "n_entries": len(food),
        "n_unparseable_times": n_bad,
        "median_entry_hour": round(hour.median(), 2),
        "median_first_entry_of_day_hour": round(fod_h.median(), 2),
        "pct_entries_00_05h": round(100 * (hour < 5).mean(), 1),
        "n_standard_breakfast": len(sb),
        "standard_breakfast_median_hour": round(sb_h.median(), 2) if len(sb) else None,
    }


def main(root, out_dir):
    root, out_dir = Path(root), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    hours, align, mins, days, glu = [], [], [], [], []
    pdirs = sorted(p for p in root.iterdir() if p.is_dir() and p.name.isdigit())
    if not pdirs:
        sys.exit(f"No participant folders found under {root}")
    for pdir in pdirs:
        pid = pdir.name
        food_files = sorted(pdir.glob("Food_Log_*.csv"))
        dex_files = sorted(pdir.glob("Dexcom_*.csv"))
        if not food_files or not dex_files:
            print(f"{pid}: missing food log or Dexcom file, skipped")
            continue
        food, header, n_bad = load_food(food_files[0])
        cgm = load_dexcom(dex_files[0])
        hours.append(meal_hours(pid, food, header, n_bad))
        row, mdf, ddf = analyse(pid, food, cgm, rng)
        align.append(row)
        mins.append(mdf)
        days.append(ddf)
        by_h = cgm.groupby(cgm["ts"].dt.hour)["glucose"].mean()
        glu.append({"participant": pid, **{f"h{h:02d}": round(v, 1) for h, v in by_h.items()}})

    H, A = pd.DataFrame(hours), pd.DataFrame(align)
    H.to_csv(out_dir / "meal_hours_by_participant.csv", index=False)
    A.to_csv(out_dir / "alignment_by_participant.csv", index=False)
    pd.concat(mins).to_csv(out_dir / "lag_sweep_minutes.csv", index=False)
    pd.concat(days).to_csv(out_dir / "lag_sweep_days.csv", index=False)
    pd.DataFrame(glu).to_csv(out_dir / "glucose_by_hour.csv", index=False)

    lines = []
    with pd.option_context("display.width", 200, "display.max_columns", 30):
        lines += ["== Food-log clock hours ==", H.to_string(index=False), ""]
        lines += ["== Food log vs CGM alignment ==",
                  A.drop(columns=["food_first", "food_last", "cgm_first", "cgm_last"]).to_string(index=False), ""]
        off = A[~A["aligned"]]
        if len(off):
            lines += ["== Recording spans of participants that failed ==",
                      off[["participant", "food_first", "food_last", "cgm_first", "cgm_last"]].to_string(index=False), ""]

    clock_ok = H["median_first_entry_of_day_hour"].between(5, 11).all()
    lines.append("TIME control (clock hour preserved): " +
                 ("GO: first food entry of the day falls between 05:00 and 11:00 for every participant"
                  if clock_ok else "CHECK MANUALLY: first-entry hour outside 05-11 for some participant"))
    bad = A.loc[~A["aligned"], "participant"].tolist()
    lines.append(f"Food log / CGM alignment: {len(A) - len(bad)} of {len(A)} participants pass all checks"
                 + (f"; FAILED: {', '.join(bad)}" if bad else ""))
    lines.append("MEAL features: " + ("usable for all participants" if not bad else
                 "do not use for the failed participants until the offset is resolved; "
                 "the registration must state how they are handled"))
    text = "\n".join(lines)
    (out_dir / "summary.txt").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "./data/big-ideas-1.1.3",
         sys.argv[2] if len(sys.argv) > 2 else "./results/time_of_day")
