"""
Build the feature table: one row per Dexcom CGM reading, for one or all
participants of BIG IDEAs v1.1.3.

This script fits no model. It computes inputs and keeps the target column
(`glucose`) next to them, so that the registered experiments can read one
table. Definitions follow docs/02_preregistration_draft.md (sections 2-4).

Usage:
    python code/features.py RAW_ROOT SMALL_ROOT OUT_DIR [PID ...]

    RAW_ROOT    folder with <pid>/{ACC,BVP,EDA,HR,IBI,TEMP}_<pid>.csv
    SMALL_ROOT  folder with Demographics.csv and <pid>/{Dexcom,Food_Log}_<pid>.csv
                (v1.1.3; see code/download_data.sh)
    OUT_DIR     receives features_<pid>.csv.gz and features_log.csv

E4 and Dexcom files are byte-identical in v1.1.2 and v1.1.3 (SHA256SUMS
compared 22 Nov 2026; only four food logs changed), so RAW_ROOT may be
filled from the AWS mirror of v1.1.2. Food logs must come from v1.1.3.
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, find_peaks

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_time_of_day import load_food  # noqa: E402  (handles the header-less 003 file)

W_SHORT = 300            # s, physiological window before each CGM reading
W_LONG = 7200            # s, long activity window (Karunarathna & Liang)
WARMUP = 7200            # s, CGM warm-up dropped after start and after gaps > 2 h
FS = {"ACC": 32, "BVP": 64, "EDA": 4, "TEMP": 4, "HR": 1}
MIN_COVERAGE = 0.5       # reading dropped if any E4 signal has < 50% of samples
EDA_FLOOR = 0.05         # uS; EDA features valid if > 50% of samples >= floor
TEMP_RANGE = (20.0, 40.0)
SCR_PROMINENCE = 0.05    # uS, minimum SCR amplitude (0.01 gave 6 SCR/min on 001: noise)
PR_COVERAGE, HRV_COVERAGE = 0.5, 0.7
ACC_UNITS_PER_G = 64.0   # Empatica E4 accelerometer: 1/64 g per unit
MEAL_EXCLUDED = {"015", "016"}   # failed the food-log/CGM alignment check
MEAL_GAP_MIN = 30


# ---------------------------------------------------------------- loading
def _secs(ts):
    """datetime64 Series -> float seconds (naive local clock)."""
    return ts.astype("datetime64[ns]").astype("int64").to_numpy() / 1e9


def read_signal(path, cols):
    df = pd.read_csv(path, encoding="utf-8-sig", skipinitialspace=True)
    df.columns = [c.strip() for c in df.columns]
    t = _secs(pd.to_datetime(df["datetime"], format="ISO8601"))
    vals = [df[c].to_numpy(dtype=np.float64) for c in cols]
    order = np.argsort(t, kind="stable")
    return t[order], [v[order] for v in vals]


def read_hr(path):
    """HR timestamps have minute resolution ('2/13/20 15:29'); rows are 1 Hz.
    Seconds are reconstructed from the row's position within its minute."""
    df = pd.read_csv(path, encoding="utf-8-sig", skipinitialspace=True)
    df.columns = [c.strip() for c in df.columns]
    if "/" not in str(df["datetime"].iloc[0]):
        # some participants' HR files carry full ISO timestamps with seconds
        t = _secs(pd.to_datetime(df["datetime"], format="ISO8601"))
        order = np.argsort(t, kind="stable")
        return t[order], df["hr"].to_numpy(dtype=np.float64)[order]
    minute = pd.to_datetime(df["datetime"], format="%m/%d/%y %H:%M")
    k = df.groupby(df["datetime"], sort=False).cumcount().to_numpy()
    n = df.groupby(df["datetime"], sort=False)["hr"].transform("size").to_numpy()
    t = _secs(minute) + k * (60.0 / np.maximum(n, 60))
    return t, df["hr"].to_numpy(dtype=np.float64)


def read_cgm(path):
    df = pd.read_csv(path)
    df = df[df["Event Type"] == "EGV"]
    ts = pd.to_datetime(df["Timestamp (YYYY-MM-DDThh:mm:ss)"], errors="coerce")
    g = pd.to_numeric(df["Glucose Value (mg/dL)"], errors="coerce")
    out = pd.DataFrame({"ts": ts, "glucose": g}).dropna().sort_values("ts")
    return out.drop_duplicates("ts").reset_index(drop=True)


# ---------------------------------------------------------------- helpers
def segments(t, fs, max_gap=1.0):
    """Index ranges of contiguous samples (no gap longer than max_gap s)."""
    br = np.flatnonzero(np.diff(t) > max_gap + 1.0 / fs) + 1
    edges = np.concatenate([[0], br, [len(t)]])
    return list(zip(edges[:-1], edges[1:]))


def win(t, T, width):
    """Slice of sorted times t inside [T - width, T)."""
    return np.searchsorted(t, T - width, "left"), np.searchsorted(t, T, "left")


def slope_per_min(t, x):
    ok = np.isfinite(x)
    if ok.sum() < 3:
        return np.nan
    tt = (t[ok] - t[ok].mean()) / 60.0
    den = (tt ** 2).sum()
    return float((tt * (x[ok] - x[ok].mean())).sum() / den) if den > 0 else np.nan


def eda_decompose(t, eda, fs=4):
    """Per contiguous segment: 1 Hz low-pass (4th-order Butterworth, zero
    phase); tonic = 0.05 Hz low-pass of that; phasic = cleaned - tonic.
    Segments shorter than 60 s are left as NaN."""
    clean = np.full_like(eda, np.nan)
    tonic = np.full_like(eda, np.nan)
    b1, a1 = butter(4, 1.0, btype="low", fs=fs)
    b2, a2 = butter(2, 0.05, btype="low", fs=fs)
    for s, e in segments(t, fs):
        if e - s < 60 * fs:
            continue
        c = filtfilt(b1, a1, eda[s:e])
        clean[s:e] = c
        tonic[s:e] = filtfilt(b2, a2, c)
    phasic = clean - tonic
    peaks = []
    for s, e in segments(t, fs):
        seg = phasic[s:e]
        if np.isnan(seg).all():
            continue
        p, prop = find_peaks(np.nan_to_num(seg, nan=0.0), prominence=SCR_PROMINENCE, distance=fs)
        peaks.append(np.column_stack([t[s:e][p], prop["prominences"]]))
    peaks = np.vstack(peaks) if peaks else np.empty((0, 2))
    return tonic, phasic, peaks


def beat_amplitudes(t_bvp, bvp, t_beat, ibi):
    """Peak-to-trough BVP amplitude within each inter-beat interval."""
    lo = np.searchsorted(t_bvp, t_beat - ibi, "left")
    hi = np.searchsorted(t_bvp, t_beat, "right")
    amp = np.full(len(t_beat), np.nan)
    for k in np.flatnonzero(hi - lo >= 4):
        seg = bvp[lo[k]:hi[k]]
        amp[k] = seg.max() - seg.min()
    return amp


def per_second(t, x):
    """Aggregate a high-rate signal to 1-s bins: start time, min, max, sum, sumsq, n."""
    sec = np.floor(t)
    starts = np.flatnonzero(np.r_[True, np.diff(sec) > 0])
    return (sec[starts],
            np.minimum.reduceat(x, starts), np.maximum.reduceat(x, starts),
            np.add.reduceat(x, starts), np.add.reduceat(x * x, starts),
            np.diff(np.r_[starts, len(x)]))


# ---------------------------------------------------------------- per participant
def participant_features(pid, raw, small, demo):
    t0 = time.time()
    cgm = read_cgm(small / pid / f"Dexcom_{pid}.csv")
    T = _secs(cgm["ts"])

    # CGM warm-up: first 2 h, and 2 h after any gap > 2 h
    gap_start = np.r_[True, np.diff(T) > WARMUP]
    last_start = np.maximum.accumulate(np.where(gap_start, T, -np.inf))
    warmup = (T - last_start) < WARMUP

    t_acc, (ax, ay, az) = read_signal(raw / pid / f"ACC_{pid}.csv", ["acc_x", "acc_y", "acc_z"])
    mag = np.sqrt(ax * ax + ay * ay + az * az) / ACC_UNITS_PER_G
    del ax, ay, az
    s_t, s_min, s_max, s_sum, s_sq, s_n = per_second(t_acc, mag)

    t_bvp, (bvp,) = read_signal(raw / pid / f"BVP_{pid}.csv", ["bvp"])
    t_eda, (eda,) = read_signal(raw / pid / f"EDA_{pid}.csv", ["eda"])
    t_tmp, (tmp,) = read_signal(raw / pid / f"TEMP_{pid}.csv", ["temp"])
    t_ibi, (ibi,) = read_signal(raw / pid / f"IBI_{pid}.csv", ["ibi"])
    t_hr, hr = read_hr(raw / pid / f"HR_{pid}.csv")

    tonic, phasic, scr = eda_decompose(t_eda, eda)
    amp = beat_amplitudes(t_bvp, bvp, t_ibi, ibi)
    # successive-difference pairs only between consecutive detected beats
    contiguous = np.r_[False, np.abs(np.diff(t_ibi) - ibi[1:]) < 0.1 * ibi[1:]]

    rows = []
    for i, Ti in enumerate(T):
        r = {}
        # --- coverage of each E4 signal in the 5-min window
        a, b = win(s_t, Ti, W_SHORT)
        r["cov_ACC"] = s_n[a:b].sum() / (FS["ACC"] * W_SHORT)
        for name, tt in [("BVP", t_bvp), ("EDA", t_eda), ("TEMP", t_tmp), ("HR", t_hr)]:
            lo, hi = win(tt, Ti, W_SHORT)
            r[f"cov_{name}"] = (hi - lo) / (FS[name] * W_SHORT)

        # --- EDA (9)
        lo, hi = win(t_eda, Ti, W_SHORT)
        raw_e, ton, pha, te = eda[lo:hi], tonic[lo:hi], phasic[lo:hi], t_eda[lo:hi]
        eda_valid = len(raw_e) > 0 and (raw_e >= EDA_FLOOR).mean() > 0.5 and np.isfinite(ton).any()
        if eda_valid:
            ks = (scr[:, 0] >= Ti - W_SHORT) & (scr[:, 0] < Ti)
            r.update({
                "eda_tonic_mean": np.nanmean(ton), "eda_tonic_sd": np.nanstd(ton),
                "eda_tonic_slope": slope_per_min(te, ton),
                "eda_tonic_min": np.nanmin(ton), "eda_tonic_max": np.nanmax(ton),
                "eda_tonic_range": np.nanmax(ton) - np.nanmin(ton),
                "eda_scr_count": int(ks.sum()),
                "eda_scr_amp_mean": float(scr[ks, 1].mean()) if ks.any() else 0.0,
                "eda_phasic_area": float(np.nansum(np.clip(pha, 0, None)) / FS["EDA"]),
            })

        # --- pulse from E4 inter-beat intervals (6)
        lo, hi = win(t_ibi, Ti, W_SHORT)
        bi, ba, bc = ibi[lo:hi], amp[lo:hi], contiguous[lo:hi]
        cov = min(bi.sum() / W_SHORT, 1.0) if len(bi) else 0.0
        r["pulse_coverage"] = cov
        if cov >= PR_COVERAGE and len(bi) >= 2:
            pr = 60.0 / bi
            r.update({"pulse_rate_mean": pr.mean(), "pulse_rate_sd": pr.std(),
                      "pulse_amp_sd": np.nanstd(ba)})
        if cov >= HRV_COVERAGE and len(bi) >= 3:
            d = np.diff(bi * 1000.0)[bc[1:]]
            r["sdnn_ms"] = (bi * 1000.0).std()
            r["rmssd_ms"] = np.sqrt(np.mean(d ** 2)) if len(d) >= 2 else np.nan

        # --- device HR (1)
        lo, hi = win(t_hr, Ti, W_SHORT)
        if hi > lo:
            r["hr_mean"] = hr[lo:hi].mean()

        # --- TEMP (3)
        lo, hi = win(t_tmp, Ti, W_SHORT)
        x = tmp[lo:hi]
        if len(x) and ((x >= TEMP_RANGE[0]) & (x <= TEMP_RANGE[1])).mean() > 0.5:
            r.update({"temp_mean": x.mean(), "temp_sd": x.std(),
                      "temp_slope": slope_per_min(t_tmp[lo:hi], x)})

        # --- ACC: 5-min mean and SD, 2-h min / max / mean (g)
        a, b = win(s_t, Ti, W_SHORT)
        n = s_n[a:b].sum()
        if n:
            m = s_sum[a:b].sum() / n
            r["acc_5m_mean"] = m
            r["acc_5m_sd"] = np.sqrt(max(s_sq[a:b].sum() / n - m * m, 0.0))
        a, b = win(s_t, Ti, W_LONG)
        if b > a:
            r.update({"acc_2h_min": s_min[a:b].min(), "acc_2h_max": s_max[a:b].max(),
                      "acc_2h_mean": s_sum[a:b].sum() / s_n[a:b].sum()})
        rows.append(r)

    F = pd.DataFrame(rows)
    F.insert(0, "participant", pid)
    F.insert(1, "ts", cgm["ts"].to_numpy())
    F.insert(2, "glucose", cgm["glucose"].to_numpy())
    F["cgm_warmup"] = warmup
    covs = F[[c for c in F.columns if c.startswith("cov_")]]
    F["e4_ok"] = (covs >= MIN_COVERAGE).all(axis=1)

    # --- TIME, ELAPSED
    mins = cgm["ts"].dt.hour * 60 + cgm["ts"].dt.minute + cgm["ts"].dt.second / 60
    F["min_from_midnight"] = mins.to_numpy()
    F["min_sin"] = np.sin(2 * np.pi * F["min_from_midnight"] / 1440)
    F["min_cos"] = np.cos(2 * np.pi * F["min_from_midnight"] / 1440)
    F["elapsed_min"] = (T - T[0]) / 60.0

    # --- MEAL (7)
    F = F.join(meal_features(pid, small, cgm["ts"]))

    # --- ID
    d = demo.loc[int(pid)]
    F["sex_male"] = int(str(d["Gender"]).strip().upper() == "MALE")
    F["hba1c"] = float(d["HbA1c"])

    log = {"participant": pid, "n_cgm": len(F), "n_warmup": int(warmup.sum()),
           "n_e4_fail": int((~F["e4_ok"]).sum()),
           "n_usable": int((F["e4_ok"] & ~F["cgm_warmup"]).sum()),
           "e4_first": pd.to_datetime(min(t_eda[0], t_acc[0]), unit="s"),
           "e4_last": pd.to_datetime(max(t_eda[-1], t_acc[-1]), unit="s"),
           "cgm_first": cgm["ts"].iloc[0], "cgm_last": cgm["ts"].iloc[-1],
           "n_scr": len(scr), "seconds": round(time.time() - t0, 1)}
    return F, log


def meal_features(pid, small, ts):
    cols = ["min_since_meal", "carb_2h", "carb_8h", "carb_24h", "sugar_2h", "sugar_8h", "sugar_24h"]
    out = pd.DataFrame(np.nan, index=range(len(ts)), columns=cols)
    out["meal_ok"] = False
    if pid in MEAL_EXCLUDED:
        return out
    food, _, _ = load_food(small / pid / f"Food_Log_{pid}.csv")
    # sugar is not in load_food's output; re-read it by position
    raw = pd.read_csv(small / pid / f"Food_Log_{pid}.csv", encoding="utf-8-sig", header=None
                      ) if pid == "003" else pd.read_csv(small / pid / f"Food_Log_{pid}.csv", encoding="utf-8-sig")
    if pid == "003":
        sugar = pd.to_numeric(raw.iloc[:, 9], errors="coerce")
        tb = pd.to_datetime(raw.iloc[:, 2], errors="coerce")
    else:
        sugar = pd.to_numeric(raw["sugar"], errors="coerce")
        tb = pd.to_datetime(raw["time_begin"], errors="coerce")
    sug = pd.DataFrame({"ts": tb, "sugar": sugar}).dropna(subset=["ts"]).sort_values("ts")
    food = food.assign(carb=food["carb"].fillna(0.0))
    sug = sug.assign(sugar=sug["sugar"].fillna(0.0))

    # meal events: entries within 30 min merged (as in the alignment check)
    new = food["ts"].diff() > pd.Timedelta(minutes=MEAL_GAP_MIN)
    ev_t = _secs(food.groupby(new.cumsum())["ts"].first())
    ft, fc = _secs(food["ts"]), food["carb"].to_numpy()
    st, sv = _secs(sug["ts"]), sug["sugar"].to_numpy()
    cf, cs = np.r_[0, np.cumsum(fc)], np.r_[0, np.cumsum(sv)]
    first = ft.min()
    T = _secs(ts)
    for i, Ti in enumerate(T):
        if Ti < first:
            continue
        k = np.searchsorted(ev_t, Ti, "right") - 1
        out.at[i, "min_since_meal"] = (Ti - ev_t[k]) / 60.0 if k >= 0 else np.nan
        for h in (2, 8, 24):
            a, b = np.searchsorted(ft, Ti - h * 3600, "left"), np.searchsorted(ft, Ti, "right")
            out.at[i, f"carb_{h}h"] = cf[b] - cf[a]
            a, b = np.searchsorted(st, Ti - h * 3600, "left"), np.searchsorted(st, Ti, "right")
            out.at[i, f"sugar_{h}h"] = cs[b] - cs[a]
        out.at[i, "meal_ok"] = True
    return out


def main(raw, small, out_dir, pids):
    raw, small, out_dir = Path(raw), Path(small), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    demo = pd.read_csv(small / "Demographics.csv", encoding="utf-8-sig").set_index("ID")
    if not pids:
        pids = sorted(p.name for p in raw.iterdir() if p.is_dir() and p.name.isdigit())
    logp = out_dir / "features_log.csv"
    logs = pd.read_csv(logp, dtype={"participant": str}) if logp.exists() else pd.DataFrame()
    for pid in pids:
        F, log = participant_features(pid, raw, small, demo)
        F.to_csv(out_dir / f"features_{pid}.csv.gz", index=False)
        if len(logs):
            logs = logs[logs["participant"] != pid]
        logs = pd.concat([logs, pd.DataFrame([log])], ignore_index=True)
        logs.sort_values("participant").to_csv(logp, index=False)
        print({k: log[k] for k in ("participant", "n_cgm", "n_warmup", "n_e4_fail", "n_usable", "seconds")}, flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])
