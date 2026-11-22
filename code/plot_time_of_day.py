"""
Figures for the time-of-day / alignment gate check.

Usage:
    python code/plot_time_of_day.py results/time_of_day

Reads the CSVs written by check_time_of_day.py and writes:
    fig_lag_sweep_minutes.png   mean post-meal glucose rise vs minute shift, one panel per participant
    fig_lag_sweep_days.png      the same vs whole-day shift
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

INK = "#1f2933"
LINE = "#2b6cb0"
FAIL = "#c0392b"
NULL = "#9aa5b1"


def panel_grid(n):
    ncols = 4
    nrows = -(-n // ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(11, 2.4 * nrows + 0.8),
                             sharex=True, sharey=True, layout="constrained")
    return fig, axes.ravel()


def plot(df, xcol, xlabel, align, out, xticks, note=""):
    pids = sorted(df["participant"].unique())
    fig, axes = panel_grid(len(pids))
    for ax, pid in zip(axes, pids):
        s = df[df["participant"] == pid]
        a = align[align["participant"] == pid].iloc[0]
        colour = LINE if a["aligned"] else FAIL
        if "comparable" in s:
            # day shifts that keep < 50% of the events: drawn faint, not used by the check
            ax.plot(s[xcol], s["mean_rise"], color=colour, lw=1, alpha=0.3)
            s = s.assign(mean_rise=s["mean_rise"].where(s["comparable"]))
        ax.plot(s[xcol], s["mean_rise"], color=colour, lw=1.4)
        if s["mean_rise"].isna().all():
            ax.text(0.5, 0.5, "No logged meal falls\ninside the CGM recording",
                    transform=ax.transAxes, ha="center", va="center", fontsize=8, color=FAIL)
        if pd.notna(a["null_mean_rise_mg_dl"]):
            ax.axhline(a["null_mean_rise_mg_dl"], color=NULL, lw=1, ls="--")
        ax.axvline(0, color=INK, lw=0.6, alpha=0.5)
        verdict = "aligned" if a["aligned"] else "NOT aligned"
        ax.set_title(f"{pid:03d}: {verdict}", fontsize=9, color=colour, loc="left")
        ax.set_xticks(xticks)
        ax.tick_params(labelsize=8)
        ax.grid(alpha=0.2)
    for ax in axes[len(pids):]:
        ax.set_visible(False)
    fig.supxlabel(xlabel, fontsize=10)
    fig.supylabel("Mean glucose rise within 2 h (mg/dL)", fontsize=10)
    fig.suptitle("Logged meal times shifted against the CGM trace. "
                 "Dashed line: same statistic at random times." + note, fontsize=10)
    fig.savefig(out, dpi=200)
    plt.close(fig)


def main(res):
    res = Path(res)
    align = pd.read_csv(res / "alignment_by_participant.csv")
    align["participant"] = align["participant"].astype(int)
    mins = pd.read_csv(res / "lag_sweep_minutes.csv")
    days = pd.read_csv(res / "lag_sweep_days.csv")
    mins["lag_h"] = mins["lag_min"] / 60
    plot(mins, "lag_h", "Shift applied to logged meal times (hours)", align,
         res / "fig_lag_sweep_minutes.png", [-12, -6, 0, 6, 12])
    plot(days, "lag_days", "Shift applied to logged meal times (days)", align,
         res / "fig_lag_sweep_days.png", [-21, -14, -7, 0, 7, 14, 21],
         note="\nFaint segments: shifts that keep fewer than half the meals (not used by the check).")
    print("wrote", res / "fig_lag_sweep_minutes.png", res / "fig_lag_sweep_days.png")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results/time_of_day")
