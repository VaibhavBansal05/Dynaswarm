"""Generate the figures used by the presentation deck, from real run data.

Every chart here reads an actual ``multirun`` directory already on disk —
nothing is hand-typed.  Run this before ``make_ppt_p3.py``.

Sources
-------
multirun/2026-08-13/10-47-40 : 4 scenarios x [astar, aco, pso, hybrid] x 30 trials,
                                geometric n=200. The main comparison (E1/E3-style).
multirun/2026-08-15/12-55-14 : moderate+high x [hybrid_fixed, hybrid_adaptive] x 30
                                trials, signal=recency, targets=[aco_fraction],
                                default (untuned) hybrid params. The allocation
                                thesis (E4), run once, preliminary.
"""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Circle, Wedge

from dynaswarm.analysis.load import load_steps, per_trial_excess
from dynaswarm.analysis.stats import compare_arms

OUT = Path(__file__).parent / "ppt_assets"
OUT.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Theme — matches make_ppt_p1.py's colour constants exactly
# ---------------------------------------------------------------------------
BG = "#0D1B2A"
PANEL = "#142A3E"
ACCENT = "#00D4FF"
GOLD = "#FFC000"
WHITE = "#FFFFFF"
LGREY = "#B0BECC"
RED = "#FF4545"
GREEN = "#4CAF50"
ARM_COLOR = {"astar": LGREY, "aco": GOLD, "pso": RED, "hybrid": ACCENT}

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "savefig.facecolor": BG,
    "text.color": WHITE,
    "axes.edgecolor": LGREY,
    "axes.labelcolor": WHITE,
    "xtick.color": LGREY,
    "ytick.color": LGREY,
    "font.size": 13,
    "font.family": "DejaVu Sans",
})

SCEN_ORDER = ["static", "low", "moderate", "high"]
SCEN_LABEL = {"static": "Static", "low": "Low\n(0.1)", "moderate": "Moderate\n(0.3)", "high": "High\n(0.8)"}


def save(fig, name, w=10, h=6):
    fig.set_size_inches(w, h)
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=200, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"wrote {name}")


# ---------------------------------------------------------------------------
# 1. Main comparison — grouped bars, all 4 arms x 4 scenarios (real, 30 trials)
# ---------------------------------------------------------------------------

def fig_arm_comparison():
    steps = load_steps("multirun/2026-08-13/10-47-40")
    per_trial = per_trial_excess(steps)
    g = per_trial.groupby(["scenario", "arm"]).mean_excess.mean().unstack()
    sd = per_trial.groupby(["scenario", "arm"]).mean_excess.std().unstack()
    g = g.reindex(SCEN_ORDER)
    sd = sd.reindex(SCEN_ORDER)

    arms = ["astar", "aco", "pso", "hybrid"]
    x = np.arange(len(SCEN_ORDER))
    width = 0.2
    fig, ax = plt.subplots()
    for i, arm in enumerate(arms):
        vals = g[arm].values * 100
        errs = sd[arm].values * 100
        ax.bar(x + (i - 1.5) * width, vals, width, yerr=errs, capsize=3,
               label=arm.upper() if arm != "astar" else "A* (exact)",
               color=ARM_COLOR[arm], edgecolor=BG, linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels([SCEN_LABEL[s] for s in SCEN_ORDER])
    ax.set_ylabel("Mean excess over optimum (%)")
    ax.set_title("Excess by arm and disruption level — 30 trials, geometric n=200", color=WHITE, fontsize=13)
    ax.legend(frameon=False, ncol=4, loc="upper left", fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color=PANEL, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    save(fig, "fig_arm_comparison.png", w=11, h=5.6)


# ---------------------------------------------------------------------------
# 2. Hybrid vs ACO — per-trial paired scatter, high scenario (real, 30 trials)
# ---------------------------------------------------------------------------

def fig_hybrid_vs_aco_paired():
    steps = load_steps("multirun/2026-08-13/10-47-40")
    per_trial = per_trial_excess(steps)
    high = per_trial[per_trial.scenario == "high"]
    aco = high[high.arm == "aco"].set_index("trial").mean_excess * 100
    hyb = high[high.arm == "hybrid"].set_index("trial").mean_excess * 100
    common = aco.index.intersection(hyb.index)
    aco, hyb = aco.loc[common], hyb.loc[common]

    fig, ax = plt.subplots()
    lim = max(aco.max(), hyb.max()) * 1.15
    ax.plot([0, lim], [0, lim], color=LGREY, linestyle="--", linewidth=1, zorder=1,
            label="equal performance")
    below = hyb < aco
    ax.scatter(aco[below], hyb[below], color=GREEN, s=55, zorder=3, label="hybrid wins the trial")
    ax.scatter(aco[~below], hyb[~below], color=RED, s=55, zorder=3, label="ACO wins the trial")
    ax.set_xlabel("ACO — mean excess this trial (%)")
    ax.set_ylabel("Hybrid — mean excess this trial (%)")
    ax.set_title("Every trial, high-disruption scenario (paired by seed)", color=WHITE, fontsize=13)
    ax.legend(frameon=False, loc="upper left", fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    n_win = int(below.sum())
    ax.text(0.98, 0.04, f"hybrid lower in {n_win}/{len(common)} trials",
            transform=ax.transAxes, ha="right", color=GOLD, fontsize=11)
    save(fig, "fig_hybrid_vs_aco_paired.png", w=6.4, h=6.0)


# ---------------------------------------------------------------------------
# 3. Allocation ablation (E4) — real, preliminary, untuned (30 trials)
# ---------------------------------------------------------------------------

def fig_allocation_ablation():
    steps = load_steps("multirun/2026-08-15/12-55-14")
    per_trial = per_trial_excess(steps)
    table = compare_arms(per_trial, "hybrid_adaptive", "hybrid_fixed", within=("scenario",))
    table = table.set_index("scenario").reindex(["moderate", "high"])

    fig, ax = plt.subplots()
    x = np.arange(len(table))
    width = 0.32
    fixed = table["hybrid_fixed"].values * 100
    adaptive = table["hybrid_adaptive"].values * 100
    ax.bar(x - width / 2, fixed, width, label="hybrid_fixed (50/50 split)", color=LGREY)
    ax.bar(x + width / 2, adaptive, width, label="hybrid_adaptive (recency-driven)", color=ACCENT)
    for i, (p, d) in enumerate(zip(table["p_holm"], table["cliffs_delta"], strict=True)):
        ax.text(i, max(fixed[i], adaptive[i]) + 0.3,
                f"p_holm={p:.2f}\nδ={d:.2f} (n.s.)",
                ha="center", fontsize=10, color=GOLD)
    ax.set_xticks(x)
    ax.set_xticklabels([SCEN_LABEL[s] for s in table.index])
    ax.set_ylabel("Mean excess over optimum (%)")
    ax.set_title("Allocation ablation (E4) — untuned, preliminary, 30 trials", color=WHITE, fontsize=13)
    ax.legend(frameon=False, loc="upper left", fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color=PANEL, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.set_ylim(0, max(fixed.max(), adaptive.max()) * 1.35)
    save(fig, "fig_allocation_ablation.png", w=7.2, h=5.6)


# ---------------------------------------------------------------------------
# 4. Conceptual: a small dynamic graph with one disruption highlighted
# ---------------------------------------------------------------------------

def fig_disruption_network():
    rng = np.random.default_rng(7)
    n = 14
    pos = rng.random((n, 2))
    edges = [(0, 1), (1, 2), (2, 3), (0, 4), (4, 5), (5, 3), (1, 6), (6, 7),
             (7, 8), (8, 3), (2, 9), (9, 10), (10, 3), (4, 11), (11, 5),
             (6, 12), (12, 8), (0, 13), (13, 4)]
    disrupted = {(6, 7), (9, 10)}
    path = [0, 4, 11, 5, 3]

    fig, ax = plt.subplots()
    for u, v in edges:
        key = (u, v)
        if key in disrupted:
            color, lw, ls = RED, 3.0, (0, (4, 2))
        else:
            color, lw, ls = "#3A4A5E", 1.4, "solid"
        ax.plot([pos[u, 0], pos[v, 0]], [pos[u, 1], pos[v, 1]], color=color, lw=lw, ls=ls, zorder=1)
    for a, b in zip(path[:-1], path[1:], strict=False):
        ax.plot([pos[a, 0], pos[b, 0]], [pos[a, 1], pos[b, 1]], color=ACCENT, lw=4, zorder=2, alpha=0.9)

    ax.scatter(pos[:, 0], pos[:, 1], s=180, color="#3A4A5E", edgecolor=LGREY, zorder=3)
    ax.scatter(*pos[0], s=260, color=GREEN, edgecolor=WHITE, zorder=4)
    ax.scatter(*pos[3], s=260, color=GOLD, edgecolor=WHITE, zorder=4)
    for u, v in disrupted:
        mx, my = (pos[u, 0] + pos[v, 0]) / 2, (pos[u, 1] + pos[v, 1]) / 2
        ax.scatter(mx, my, marker="x", s=220, color=RED, linewidth=3, zorder=5)

    ax.set_xlim(-0.08, 1.08)
    ax.set_ylim(-0.08, 1.08)
    ax.axis("off")
    save(fig, "fig_disruption_network.png", w=6.4, h=6.0)


# ---------------------------------------------------------------------------
# 5. Conceptual: explore / exploit dial
# ---------------------------------------------------------------------------

def fig_explore_exploit_dial():
    fig, ax = plt.subplots(subplot_kw={"aspect": "equal"})
    theta = np.linspace(180, 0, 200)
    for i, t in enumerate(theta[:-1]):
        frac = i / len(theta)
        color = matplotlib.colormaps["cool"](frac)
        w = Wedge((0, 0), 1.0, theta[i + 1], theta[i], width=0.32, facecolor=color, edgecolor=None)
        ax.add_patch(w)
    ax.add_patch(Wedge((0, 0), 0.68, 0, 180, width=0.0, facecolor="none"))

    needle_angle = np.radians(60)  # points toward "explore" side under disruption
    ax.plot([0, 0.78 * np.cos(needle_angle)], [0, 0.78 * np.sin(needle_angle)],
            color=WHITE, lw=4, zorder=5, solid_capstyle="round")
    ax.add_patch(Circle((0, 0), 0.05, color=WHITE, zorder=6))

    ax.text(-1.05, 0.15, "EXPLOIT", color=GOLD, fontsize=16, weight="bold", ha="center")
    ax.text(-1.05, -0.05, "(colony memory)", color=GOLD, fontsize=10, ha="center")
    ax.text(1.05, 0.15, "EXPLORE", color=ACCENT, fontsize=16, weight="bold", ha="center")
    ax.text(1.05, -0.05, "(swarm search)", color=ACCENT, fontsize=10, ha="center")
    ax.text(0, -0.35, "budget allocation, aco_fraction", color=LGREY, fontsize=11, ha="center")

    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-0.5, 1.15)
    ax.axis("off")
    save(fig, "fig_explore_exploit_dial.png", w=7.0, h=4.6)


# ---------------------------------------------------------------------------
# 6. Conceptual: layered system architecture
# ---------------------------------------------------------------------------

def _box(ax, x, y, w, h, text, color=PANEL, textcolor=WHITE, fontsize=11, edge=ACCENT):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.03",
                          facecolor=color, edgecolor=edge, linewidth=1.4, zorder=2)
    ax.add_patch(box)
    ax.text(x + w / 2, y + h / 2, text, color=textcolor, fontsize=fontsize,
            ha="center", va="center", zorder=3, wrap=True)


def _arrow(ax, x1, y1, x2, y2, color=LGREY):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14,
                                  color=color, linewidth=1.6, zorder=1))


def fig_architecture():
    fig, ax = plt.subplots()
    layers = [
        ("core/", "CSR graph · timeline · oracle · RNG streams", GOLD),
        ("optimizers/", "A*  ·  MMAS ACO  ·  priority PSO  ·  Hybrid", ACCENT),
        ("control/", "signals (edge_ratio, volatility, λ-branch, recency) + controllers", ACCENT),
        ("harness/", "shared timeline loop · metered budget · one trial per seed", GOLD),
        ("io/ + analysis/", "Parquet + manifest  →  stats, figures, replay", LGREY),
    ]
    n = len(layers)
    h = 0.9
    gap = 0.35
    total_h = n * h + (n - 1) * gap
    y0 = 0.2
    for i, (name, detail, color) in enumerate(layers):
        y = y0 + (n - 1 - i) * (h + gap)
        _box(ax, 0.3, y, 9.6, h, "", color=PANEL, edge=color)
        ax.text(0.55, y + h * 0.68, name, color=color, fontsize=13, weight="bold",
                ha="left", va="center", zorder=3)
        ax.text(0.55, y + h * 0.3, detail, color=WHITE, fontsize=10.5,
                ha="left", va="center", zorder=3)
        if i < n - 1:
            _arrow(ax, 5.1, y, 5.1, y - gap + 0.02)

    ax.set_xlim(0, 10.2)
    ax.set_ylim(0, y0 + total_h + 0.3)
    ax.axis("off")
    ax.set_title("Every layer above only talks to the layer below it", color=LGREY, fontsize=11, pad=10)
    save(fig, "fig_architecture.png", w=7.2, h=6.6)


# ---------------------------------------------------------------------------
# 7. Conceptual: sense -> propose -> apply control loop
# ---------------------------------------------------------------------------

def fig_control_loop():
    fig, ax = plt.subplots()
    nodes = {
        "sense": (1.3, 3.0, "SENSE\nsignal.observe(obs)\n→ signal_value"),
        "propose": (4.3, 4.6, "PROPOSE\ncontroller.propose(\n  pressure vs baseline)"),
        "apply": (7.3, 3.0, "APPLY\noptimizer.apply(Δσ)\nPARAM_SPEC.bind()"),
        "step": (4.3, 1.2, "STEP\narm acts on the\ncurrent GraphView"),
    }
    colors = {"sense": ACCENT, "propose": GOLD, "apply": ACCENT, "step": LGREY}
    for key, (x, y, label) in nodes.items():
        _box(ax, x - 1.1, y - 0.55, 2.2, 1.1, label, color=PANEL, edge=colors[key], fontsize=10.5)

    _arrow(ax, 2.3, 3.5, 3.4, 4.3)
    _arrow(ax, 5.3, 4.3, 6.2, 3.5)
    _arrow(ax, 7.0, 2.5, 5.3, 1.5)
    _arrow(ax, 3.4, 1.5, 1.9, 2.5)

    ax.text(4.3, 5.55, "every adapt_every timesteps, one target at a time", color=LGREY,
            fontsize=10, ha="center", style="italic")
    ax.set_xlim(0, 8.6)
    ax.set_ylim(0.3, 6.0)
    ax.axis("off")
    save(fig, "fig_control_loop.png", w=7.6, h=5.6)


if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    fig_arm_comparison()
    fig_hybrid_vs_aco_paired()
    fig_allocation_ablation()
    fig_disruption_network()
    fig_explore_exploit_dial()
    fig_architecture()
    fig_control_loop()
    print(f"\nAll figures written to {OUT}/")
