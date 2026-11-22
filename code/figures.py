"""
Manuscript figures from the outputs of experiments.py.

Usage:
    python code/figures.py RESULTS_DIR

Writes into RESULTS_DIR/figures/:
    fig2_random_vs_lopo.png      R2 by configuration (RANDOM vs LOPO, shortcut models), 95% CIs
    fig3_per_participant.png     per-participant RMSE under LOPO (E2, E4), one marker per participant
    fig4_clarke.png              Clarke grid: mean baseline vs FULL-KL (LOPO)
    fig5_buffer.png              R2 against buffer length (E6)
    fig6_hypotheses.png          registered tests: estimate, 95% CI, margin
    figS2_shap_groups.png        EA1 (exploratory): share of mean |SHAP| by feature group
Each figure is drawn with constrained layout and checked for overlapping text
by `assert_no_overlap`.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from experiments import clarke_zone  # noqa: E402

BLUE, ORANGE, GREY, INK = "#2b6cb0", "#c05621", "#718096", "#1f2933"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})

LABELS = {
    "E1_random_fullkl": "FULL-KL, RANDOM (E1)",
    "E3_random_time_idp": "Clock time + ID + participant, RANDOM",
    "E3_random_elapsed_idp": "Elapsed time + ID + participant, RANDOM",
    "E3_random_idp": "ID + participant only, RANDOM",
    "E2_lopo_fullkl": "FULL-KL, LOPO (E2)",
    "E2_lopo_fullkl_ridge": "FULL-KL ridge, LOPO",
    "E5_lopo_mean": "Training mean, LOPO",
    "E4_lopo_mean": "Training mean, LOPO (14)",
    "E4_lopo_timemealid": "Time + meals + ID, LOPO (14)",
    "E4_lopo_fullb": "FULL-B, LOPO (14)",
    "E4_lopo_fullb_ridge": "FULL-B ridge, LOPO (14)",
}


def assert_no_overlap(fig):
    """Fail if any two visible text boxes in the figure overlap."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    boxes = []
    for t in fig.findobj(matplotlib.text.Text):
        if t.get_visible() and t.get_text().strip():
            bb = t.get_window_extent(renderer=r)
            if bb.width > 0 and bb.height > 0:
                boxes.append((t.get_text()[:30], bb))
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i][1], boxes[j][1]
            ov = min(a.x1, b.x1) - max(a.x0, b.x0), min(a.y1, b.y1) - max(a.y0, b.y0)
            if ov[0] > 1 and ov[1] > 1:
                raise AssertionError(f"overlapping text: {boxes[i][0]!r} / {boxes[j][0]!r}")


def save(fig, path):
    assert_no_overlap(fig)
    fig.savefig(path, dpi=300)
    plt.close(fig)


def fig_r2(M, out):
    keys = [k for k in LABELS if k in set(M["config"])]
    R = M[M["metric"] == "r2"].set_index("config").loc[keys]
    fig, ax = plt.subplots(figsize=(6.5, 0.38 * len(keys) + 1.0), layout="constrained")
    y = np.arange(len(keys))[::-1]
    col = [ORANGE if "random" in k else BLUE for k in keys]
    for yi, (_, r), c in zip(y, R.iterrows(), col):
        ax.errorbar(r["value"], yi, xerr=[[r["value"] - r["ci_low"]], [r["ci_high"] - r["value"]]],
                    fmt="o", color=c, ms=4.5, elinewidth=1.4, capsize=2, zorder=3)
    ax.axvline(0, color=GREY, lw=0.8)
    ax.set_yticks(y, [LABELS[k] for k in keys])
    ax.set_xlabel("R² (pooled; 95% participant-bootstrap CI)")
    ax.set_title("Orange: random 80/20 split of readings. Blue: participant held out.", loc="left", fontsize=8.5)
    save(fig, out / "fig2_random_vs_lopo.png")


def fig_participants(BP, out):
    keys = [k for k in ["E5_lopo_mean", "E2_lopo_fullkl", "E4_lopo_timemealid", "E4_lopo_fullb"] if k in set(BP["config"])]
    fig, ax = plt.subplots(figsize=(6.5, 3.2), layout="constrained")
    for i, k in enumerate(keys):
        d = BP[BP["config"] == k]
        jitter = np.linspace(-0.15, 0.15, len(d))
        ax.scatter(np.full(len(d), i) + jitter, d["rmse"], s=14, color=BLUE if i else GREY, alpha=0.8)
        ax.hlines(d["rmse"].median(), i - 0.25, i + 0.25, color=INK, lw=1.5)
    ax.set_xticks(range(len(keys)), [LABELS[k].replace(", LOPO", "\nLOPO") for k in keys])
    ax.set_ylabel("RMSE of held-out participant (mg/dL)")
    ax.set_title("One marker per participant; bar: median.", loc="left", fontsize=8.5)
    save(fig, out / "fig3_per_participant.png")


def clarke_background(ax):
    ax.plot([0, 400], [0, 400], color=GREY, lw=0.6, ls=":")
    for xs, ys in [([0, 175 / 3], [70, 70]), ([175 / 3, 400 / 1.2], [70, 400]), ([70, 70], [84, 400]),
                   ([0, 70], [180, 180]), ([70, 290], [180, 400]), ([70, 70], [0, 56]),
                   ([70, 400], [56, 320]), ([180, 180], [0, 70]), ([180, 400], [70, 70]),
                   ([240, 240], [70, 180]), ([240, 400], [180, 180]), ([130, 180], [0, 70])]:
        ax.plot(xs, ys, color=INK, lw=0.6)
    for txt, x, y in [("A", 30, 15), ("A", 370, 330), ("B", 285, 370), ("B", 370, 260), ("C", 160, 370),
                      ("C", 160, 15), ("D", 30, 120), ("D", 370, 120), ("E", 30, 370), ("E", 370, 15)]:
        ax.text(x, y, txt, fontsize=9, color=INK, ha="center", va="center")
    ax.set_xlim(0, 400); ax.set_ylim(0, 400); ax.set_aspect("equal")


def fig_clarke(pred_dir, out):
    pairs = [("E5_lopo_mean", "Training mean (LOPO)"), ("E2_lopo_fullkl", "FULL-KL (LOPO)")]
    pairs = [(k, t) for k, t in pairs if (pred_dir / f"{k}.csv.gz").exists()]
    fig, axes = plt.subplots(1, len(pairs), figsize=(3.3 * len(pairs), 3.6), layout="constrained")
    for ax, (k, t) in zip(np.atleast_1d(axes), pairs):
        P = pd.read_csv(pred_dir / f"{k}.csv.gz")
        z = clarke_zone(P["y"], P["yhat"])
        ab = 100 * np.isin(z, ["A", "B"]).mean()
        ax.scatter(P["y"], P["yhat"], s=2, alpha=0.15, color=BLUE, rasterized=True)
        clarke_background(ax)
        ax.set_title(f"{t}\nzones A+B: {ab:.1f}%", fontsize=8.5)
        ax.set_xlabel("CGM glucose (mg/dL)")
        ax.set_ylabel("Estimated glucose (mg/dL)")
    save(fig, out / "fig4_clarke.png")


def fig_buffer(M, out):
    R = M[(M["metric"] == "r2") & M["config"].str.startswith("E6_blocked_")].copy()
    if R.empty:
        return
    R["b"] = R["config"].str.rsplit("_", n=1).str[-1].astype(int)
    R = R.sort_values("b")
    fig, ax = plt.subplots(figsize=(4.2, 3.0), layout="constrained")
    ax.errorbar(R["b"], R["value"], yerr=[R["value"] - R["ci_low"], R["ci_high"] - R["value"]],
                color=BLUE, marker="o", ms=4, capsize=2)
    ax.axhline(0, color=GREY, lw=0.8)
    ax.set_xticks(R["b"])
    ax.set_xlabel("Buffer between training and test blocks (min)")
    ax.set_ylabel("R² (95% CI)")
    save(fig, out / "fig5_buffer.png")


def fig_hypotheses(H, out):
    margins = {"H1": 0.30, "H2": 0.05, "H2b": 0.05, "H3": 0.0, "H4": 2.0, "H5": 0.10, "H6": 90, "H7": 0.0}
    fig, axes = plt.subplots(len(H), 1, figsize=(6.5, 0.62 * len(H) + 0.6), layout="constrained")
    for ax, (_, h) in zip(np.atleast_1d(axes), H.iterrows()):
        ax.errorbar([h["estimate"]], [0], xerr=[[h["estimate"] - h["ci_low"]], [h["ci_high"] - h["estimate"]]],
                    fmt="o", color=BLUE if h["supported"] else GREY, capsize=2, ms=4)
        note = "" if h.get("interpretable", True) else ", not interpretable (E1 guard)"
        ax.axvline(margins[h["hypothesis"]], color=ORANGE, lw=1, ls="--")
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
        ax.set_title(f"{h['hypothesis']}: {h['statement'].replace('R2', 'R²')}  (Holm p = {h['p_holm']:.3g}{note})", loc="left", fontsize=7.5)
        ax.tick_params(labelsize=7)
    save(fig, out / "fig6_hypotheses.png")


def fig_shap(ea_dir, out):
    f = ea_dir / "ea1_shap.csv"
    if not f.exists():
        return
    S = pd.read_csv(f).groupby(["scheme", "group"])["share"].sum().unstack().reindex(["RANDOM", "LOPO"])
    groups = [g for g in ["TIME", "sex", "ACT", "PHYS"] if g in S.columns]
    colors = {"TIME": ORANGE, "sex": INK, "ACT": GREY, "PHYS": BLUE}
    fig, ax = plt.subplots(figsize=(6.0, 1.9), layout="constrained")
    left = np.zeros(len(S))
    for g in groups:
        ax.barh(range(len(S)), S[g], left=left, color=colors[g], height=0.55, label=g)
        left += S[g].to_numpy()
    ax.set_yticks(range(len(S)), ["RANDOM (seed 0)", "LOPO (mean of folds)"])
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xlabel("Share of mean |SHAP| (FULL-KL, XGBoost)")
    ax.legend(ncol=len(groups), loc="lower center", bbox_to_anchor=(0.5, 1.02), frameon=False, fontsize=8)
    save(fig, out / "figS2_shap_groups.png")


def main(res):
    res = Path(res)
    out = res / "figures"
    out.mkdir(exist_ok=True)
    M = pd.read_csv(res / "metrics.csv")
    BP = pd.read_csv(res / "metrics_by_participant.csv")
    H = pd.read_csv(res / "hypotheses.csv")
    fig_r2(M, out)
    fig_participants(BP, out)
    fig_clarke(res / "predictions", out)
    fig_buffer(M, out)
    fig_hypotheses(H, out)
    fig_shap(res.parent / "exploratory", out)
    print("figures written to", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results/experiments")
