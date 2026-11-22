"""
Gate check: is clock time preserved in BIG IDEAs v1.1.3 despite date-shifting?

If breakfasts cluster in the morning and dinners in the evening for every
participant, the TIME shortcut control (E3) is valid. If not, drop it and
report why.

Usage:
    python check_time_of_day.py ./data/big-ideas-1.1.3

Outputs (in the current directory):
    meal_hours_by_participant.csv
    glucose_by_hour.csv
    and a printed go/no-go summary.

Written without access to the full dataset: column names are detected, not
assumed (the PhysioNet docs say `time_of_day`, the file for 001 has `time`).
"""
import sys
from pathlib import Path

import pandas as pd


def find_col(df, *candidates):
    cols = {c.lower().strip(): c for c in df.columns}
    for cand in candidates:
        for low, orig in cols.items():
            if cand in low:
                return orig
    return None


def load_food(path):
    df = pd.read_csv(path)
    tcol = find_col(df, "time_begin", "time_of_day", "time")
    if tcol is None:
        raise ValueError(f"No time column in {path}: {list(df.columns)}")
    ts = pd.to_datetime(df[tcol].astype(str), errors="coerce")
    if ts.isna().all():  # pure HH:MM:SS column
        ts = pd.to_datetime("2000-01-01 " + df[tcol].astype(str), errors="coerce")
    df["hour"] = ts.dt.hour + ts.dt.minute / 60
    df["logged_food"] = df.get(find_col(df, "logged_food") or tcol)
    return df


def load_dexcom(path):
    df = pd.read_csv(path)
    tcol = find_col(df, "timestamp")
    vcol = find_col(df, "glucose value", "value")
    if tcol is None or vcol is None:
        raise ValueError(f"Unexpected Dexcom columns in {path}: {list(df.columns)}")
    out = pd.DataFrame({
        "ts": pd.to_datetime(df[tcol], errors="coerce"),
        "glucose": pd.to_numeric(df[vcol], errors="coerce"),
    }).dropna()
    out["hour"] = out["ts"].dt.hour
    return out


def main(root):
    root = Path(root)
    meal_rows, glu_rows = [], []
    for pdir in sorted(p for p in root.iterdir() if p.is_dir() and p.name.isdigit()):
        pid = pdir.name
        food_files = list(pdir.glob("*Food*Log*.csv"))
        dex_files = list(pdir.glob("*Dexcom*.csv"))
        if food_files:
            f = load_food(food_files[0])
            breakfast = f[f["logged_food"].astype(str).str.contains("Standard Breakfast", case=False, na=False)]
            meal_rows.append({
                "participant": pid,
                "n_entries": len(f),
                "median_meal_hour": round(f["hour"].median(), 2),
                "pct_entries_00_05h": round(100 * (f["hour"] < 5).mean(), 1),
                "n_standard_breakfast": len(breakfast),
                "standard_breakfast_median_hour": round(breakfast["hour"].median(), 2) if len(breakfast) else None,
            })
        if dex_files:
            g = load_dexcom(dex_files[0])
            by_h = g.groupby("hour")["glucose"].mean()
            glu_rows.append({"participant": pid, **{f"h{h:02d}": round(v, 1) for h, v in by_h.items()}})

    meals = pd.DataFrame(meal_rows)
    meals.to_csv("meal_hours_by_participant.csv", index=False)
    pd.DataFrame(glu_rows).to_csv("glucose_by_hour.csv", index=False)
    print(meals.to_string(index=False))

    # Go/no-go: standard breakfast should sit between 05:00 and 11:00 for everyone.
    sb = meals["standard_breakfast_median_hour"].dropna()
    ok = sb.between(5, 11).all() and len(sb) == len(meals)
    print("\nTIME control:", "GO — clock time looks preserved" if ok
          else "CHECK MANUALLY — breakfast hours missing or outside 05–11")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "./data/big-ideas-1.1.3")
