"""Figures.

Deliberately few.  Each answers one question that the tables cannot, and
anything a table says better is left to the table.

Every figure draws per-trial points alongside whatever summary it shows.
A bar chart of means invites the reader to believe a difference that a
scatter of the underlying trials would immediately undercut, and in this
project the trial-to-trial spread has repeatedly been larger than the
differences between arms.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # figures are written, never displayed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from dynaswarm.core.rng import stream

__all__ = ["excess_over_time", "arm_comparison", "recovery_profile", "scaling", "save"]

_PALETTE = plt.get_cmap("tab10")


def save(fig: plt.Figure, path: Path | str) -> Path:
    """Write a figure and close it.

    Args:
        fig: The figure.
        path: Destination; the suffix chooses the format.

    Returns:
        The path written.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def excess_over_time(frame: pd.DataFrame, scenario: str | None = None) -> plt.Figure:
    """Quality against time, with disruptions marked.

    The figure that shows whether a transient exists at all: if excess
    does not visibly rise after the marked events and decay afterwards,
    there is no recovery to measure and no case for a hybrid built around
    covering one.

    Args:
        frame: Step rows.
        scenario: Restrict to one scenario, or use all of them.

    Returns:
        The figure.
    """
    if scenario is not None:
        frame = frame[frame.scenario == scenario]

    fig, ax = plt.subplots(figsize=(9, 4))
    for i, (arm, group) in enumerate(frame.groupby("arm", sort=True)):
        curve = group.groupby("timestep").excess.agg(["mean", "std"])
        colour = _PALETTE(i % 10)
        ax.plot(curve.index, curve["mean"], label=arm, color=colour, linewidth=1.6)
        ax.fill_between(
            curve.index,
            curve["mean"] - curve["std"],
            curve["mean"] + curve["std"],
            color=colour,
            alpha=0.12,
        )

    disrupted = frame.groupby("timestep").num_events.max()
    for t in disrupted[disrupted > 0].index:
        ax.axvline(t, color="0.75", linewidth=0.6, zorder=0)

    ax.set_xlabel("timestep")
    ax.set_ylabel("excess over optimum")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.set_title(f"quality over time{f' — {scenario}' if scenario else ''}")
    ax.legend(frameon=False, fontsize=8)
    return fig


def arm_comparison(per_trial: pd.DataFrame, metric: str = "mean_excess") -> plt.Figure:
    """Per-arm distributions, with every trial drawn.

    Points rather than bars: the spread across trials has repeatedly been
    wider than the gaps between arms, and a bar chart would hide exactly
    that.

    Args:
        per_trial: One row per arm and trial.
        metric: Column to plot.

    Returns:
        The figure.
    """
    scenarios = sorted(per_trial.scenario.unique()) if "scenario" in per_trial else [None]
    fig, axes = plt.subplots(
        1, len(scenarios), figsize=(4.2 * len(scenarios), 4), squeeze=False, sharey=True
    )

    for ax, scenario in zip(axes[0], scenarios, strict=True):
        subset = per_trial if scenario is None else per_trial[per_trial.scenario == scenario]
        arms = sorted(subset.arm.unique())
        for i, arm in enumerate(arms):
            values = subset[subset.arm == arm][metric].dropna().to_numpy()
            if values.size == 0:
                continue
            jitter = (stream(i, "jitter", arm).random(values.size) - 0.5) * 0.18
            ax.scatter(np.full(values.size, i) + jitter, values,
                       s=18, alpha=0.55, color=_PALETTE(i % 10))
            ax.hlines(np.median(values), i - 0.28, i + 0.28,
                      color=_PALETTE(i % 10), linewidth=2.4)
        ax.set_xticks(range(len(arms)))
        ax.set_xticklabels(arms, rotation=30, ha="right", fontsize=8)
        ax.set_title(scenario or "all", fontsize=10)

    axes[0][0].set_ylabel(metric.replace("_", " "))
    if metric.endswith("excess"):
        axes[0][0].yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    fig.suptitle("per-trial distributions (bars would hide this spread)", fontsize=10)
    return fig


def recovery_profile(frame: pd.DataFrame, window: int = 8) -> plt.Figure:
    """Mean excess aligned on the timestep each disruption landed.

    Averaging over a whole trial hides a transient; aligning on the event
    is what makes one visible.  A hybrid that helps only just after a
    disruption should separate here and nowhere else.

    Args:
        frame: Step rows.
        window: Steps to show either side of the event.

    Returns:
        The figure.
    """
    fig, ax = plt.subplots(figsize=(7, 4))

    for i, (arm, group) in enumerate(frame.groupby("arm", sort=True)):
        aligned: dict[int, list[float]] = {k: [] for k in range(-window, window + 1)}
        for _, trial in group.groupby("trial"):
            trial = trial.sort_values("timestep").reset_index(drop=True)
            events = trial.num_events.to_numpy()
            excess = trial.excess.to_numpy(float)
            for t in np.flatnonzero(events > 0):
                for offset in range(-window, window + 1):
                    k = t + offset
                    if 0 <= k < len(excess) and np.isfinite(excess[k]):
                        aligned[offset].append(excess[k])

        offsets = sorted(aligned)
        means = [np.mean(aligned[o]) if aligned[o] else np.nan for o in offsets]
        ax.plot(offsets, means, marker="o", markersize=3,
                label=arm, color=_PALETTE(i % 10), linewidth=1.6)

    ax.axvline(0, color="0.4", linestyle="--", linewidth=1)
    ax.annotate("disruption", (0, ax.get_ylim()[1]), fontsize=8,
                ha="center", va="top", color="0.4")
    ax.set_xlabel("timesteps relative to a disruption")
    ax.set_ylabel("excess over optimum")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.set_title("transient response, aligned on the event")
    ax.legend(frameon=False, fontsize=8)
    return fig


def scaling(frame: pd.DataFrame) -> plt.Figure:
    """Cost against graph size, for the exact method and the heuristics.

    The premise that recomputation is expensive is an empirical claim,
    and this is where it is either supported or not.  A* is exact, so it
    can only be beaten on cost — if its cost does not grow, there is
    nothing for a metaheuristic to win.

    Args:
        frame: Step rows spanning several graph sizes.

    Returns:
        The figure.
    """
    fig, (left, right) = plt.subplots(1, 2, figsize=(10, 4))

    astar = frame[frame.arm == "astar"]
    if not astar.empty:
        cost = astar.groupby("n_nodes").astar_expansions.mean()
        left.plot(cost.index, cost.values, marker="o", color=_PALETTE(0))
        left.set_xlabel("nodes")
        left.set_ylabel("A* node expansions per timestep")
        left.set_title("cost of exact recomputation")
        left.set_xscale("log")
        left.set_yscale("log")

    for i, (arm, group) in enumerate(frame[frame.arm != "astar"].groupby("arm", sort=True)):
        quality = group.groupby("n_nodes").excess.mean()
        right.plot(quality.index, quality.values, marker="o",
                   label=arm, color=_PALETTE(i % 10))
    right.set_xlabel("nodes")
    right.set_ylabel("excess over optimum")
    right.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    right.set_xscale("log")
    right.set_title("quality of the heuristics")
    right.legend(frameon=False, fontsize=8)
    return fig
