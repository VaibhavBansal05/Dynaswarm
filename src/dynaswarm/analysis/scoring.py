"""Rank the arms without putting a thumb on the scale (§15, segment Z).

Read-only. Nothing here computes anything new about the science — it
turns four recorded numbers into an ordering an examiner cannot accuse of
being built to flatter the thesis.

**Two deliberate refusals, because both are places a thumb goes:**

*No weights, and no normalisation.* A weighted sum needs a scale
conversion *and* a set of weights, and both are arguable. Ranks are
scale-free: a percentage and a count of timesteps contribute equally with
no constant to defend. The only arbitrary choice left is *which metrics
are in the set*, and that choice is printed on the face of the tab.

*No metric that is not a virtue.* Every metric here answers "why is more
of it better" in one sentence. ``hops`` cannot — a shorter route that
costs more is worse — so it stays a diagnostic and stays out of the
score. A metric that is not a virtue is bias wearing a number's clothes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

import numpy as np
import pandas as pd

from dynaswarm.analysis.recovery import disruptions

__all__ = [
    "METRICS",
    "format_metric",
    "ArmScore",
    "arm_metrics",
    "censored_recovery",
    "RecoverySummary",
    "mean_ranks",
    "comparable_metrics",
    "pareto_dominance",
    "score_run",
    "REFERENCE_ARM",
]

#: The arm that is the reference, never a competitor. A* is exact by
#: construction: it scores perfectly on every metric, so ranking it makes
#: every other position meaningless — third place out of four when one of
#: the four cannot lose is not a finding.
REFERENCE_ARM = "astar"

#: The metric set, fixed by Entry 024 **before** the evidence run. Each
#: entry is (key, display, lower_is_better). Adding a fifth here fails
#: `test_the_metric_set_is_exactly_the_four`, which is the point: a metric
#: set that can grow after the outcome is known is not pre-registered.
METRICS: tuple[tuple[str, str, bool, str], ...] = (
    ("mean_excess", "mean excess", True, "pct"),
    ("at_optimum", "% of steps at optimum", False, "raw_pct"),
    ("worst_excess", "worst excess", True, "pct"),
    ("mean_recovery", "mean steps to recover", True, "steps"),
)

#: Excess at or below this counts as "at the optimum". Not zero: excess is
#: a ratio of floats and an exactly-zero test would report 0% for an arm
#: sitting on the optimum at 1e-16.
AT_OPTIMUM_TOLERANCE = 1e-9



def format_metric(key: str, value: float) -> str:
    """Render one metric the way that metric should be rendered.

    **Server-side deliberately.** How a metric is written is part of what
    the metric *is* — `mean_excess` is a ratio shown as a percentage,
    `at_optimum` is already a percentage, `mean_recovery` is a count of
    timesteps. That knowledge lives here beside `METRICS`, and a view
    that formatted them itself would be a second place where a ratio
    could be printed as though it were a percentage.
    """
    if value is None or np.isnan(value):
        return "\u2014"
    kind = next(f for k, _, _, f in METRICS if k == key)
    if kind == "pct":
        return f"{value * 100:.2f}%"
    if kind == "raw_pct":
        return f"{value:.1f}%"
    return f"{value:.2f}"


def _evidence_line(n_seeds: int, run_classes: list[str], ok: bool) -> str:
    """The caveat, as a sentence, built where the numbers are."""
    classes = ", ".join(run_classes) or "unknown"
    if ok:
        return f"n = {n_seeds} \u00b7 {classes} \u00b7 evidence"
    plural = "" if n_seeds == 1 else "s"
    return (
        f"n = {n_seeds} \u00b7 {classes} \u00b7 NOT EVIDENCE \u2014 a ranking "
        f"from {n_seeds} seed{plural} of scratch work shows how this run went, "
        f"not how the arms compare"
    )


def _pareto_line(arms: list[dict], display: dict[str, str],
                 over: list[str] | None = None) -> str:
    """Pareto in words. The sentence a null needs and a mean rank cannot make.

    A mean rank always yields an ordering, even from pure noise. "No arm
    is at least as good as another on every metric" is the honest
    description of a tie, and it has to be said rather than inferred from
    four numbers being close together.
    """
    claims = [
        f"{display.get(a['arm'], a['arm'])} beats "
        + ", ".join(display.get(b, b) for b in a["dominates"])
        for a in arms
        if a["dominates"]
    ]
    scope = (
        ""
        if over is None or len(over) == len(METRICS)
        else f" (over the {len(over)} metrics defined here: {', '.join(over)})"
    )
    if not claims:
        return (
            f"Pareto{scope}: no arm is at least as good as another on every "
            f"metric. The ordering above is an artefact of averaging ranks "
            f"\u2014 on this run the arms are not distinguishable."
        )
    return (
        f"Pareto{scope}: {'; '.join(claims)}. Any ordering above not listed "
        f"here is an artefact of averaging ranks across metrics that disagree."
    )


@dataclass
class ArmScore:
    """One arm's metrics, ranks and mean rank."""

    arm: str
    metrics: dict[str, float]
    ranks: dict[str, float]
    mean_rank: float
    n_disruptions: int
    n_damaged: int
    n_unchanged: int
    n_improved: int
    n_censored: int


class RecoverySummary(NamedTuple):
    """Recovery, and the population it was measured over.

    The counts are not diagnostics hanging off the number — they are what
    makes the number readable. At one seed the mean rests on three or four
    observations, and a reader who cannot see that will treat it as solid.
    """

    mean: float
    n_scoreable: int
    n_damaged: int
    n_unchanged: int
    n_improved: int
    n_censored: int


def censored_recovery(
    excess: list[float | None], events: list[int]
) -> RecoverySummary:
    """Mean steps to recover, over the disruptions that caused damage.

    Two aggregation rules, both learned the hard way in this metric.

    **Censored cases are counted, never dropped** (segment Z). An
    unrecovered disruption is scored at the full remaining horizon — a
    lower bound, so it under-states rather than invents a penalty.
    Dropping them made an arm that never recovers score 1.00 against 8.00
    for one that always did.

    **Undamaged disruptions are excluded** (segment Z3, Entry 028). You
    cannot measure recovery from an event that caused no degradation, and
    a `recovery` of 0 there is arithmetically right and informationally
    empty. Measured: only 3-4 of 19 scoreable disruptions actually damage
    an arm, so ~80% of the population contributed a zero that pulled every
    arm toward zero **and toward each other**. Restricted to damaged
    events the arms spread by 3x and the `hybrid_fixed` /
    `hybrid_scheduled` tie breaks.

    **Why conditioning on an outcome is legitimate here**, since it is the
    obvious objection: it discards the information that a robust arm was
    rarely damaged. But robustness is already carried by the other three
    metrics — mean excess, % at optimum and worst excess all measure how
    well an arm does, including how rarely it is hurt. Recovery answers a
    different question, *speed of return*, which is the one Claim 3 is
    about. The metric set has no gap and no double-count.

    The two rules compose without interacting: an undamaged disruption can
    never be censored, because if damage <= 0 then the excess never rose
    above the recovery band and `recovery` is 0 at the disruption step
    itself. So excluding undamaged events keeps every censored one.

    Returns:
        A :class:`RecoverySummary`. ``mean`` is ``nan`` when nothing
        damaging was scoreable, which keeps an arm that was never hurt out
        of an average rather than crediting it with instant recovery.
    """
    horizon = len(excess)
    transients = disruptions(excess, events)
    if not transients:
        return RecoverySummary(float("nan"), 0, 0, 0, 0, 0)

    # `improved` is counted apart from `unchanged` deliberately. A
    # disruption can open a shorter route — measured at -0.0017 — and
    # merging "the disruption helped" into "nothing happened" throws away
    # a real and counter-intuitive property of dynamic graphs.
    damaged = [t for t in transients if t.damage > 0.0]
    unchanged = sum(1 for t in transients if t.damage == 0.0)
    improved = sum(1 for t in transients if t.damage < 0.0)

    times, censored = [], 0
    for t in damaged:
        if t.recovery is None:
            censored += 1
            times.append(float(horizon - t.timestep))
        else:
            times.append(float(t.recovery))

    return RecoverySummary(
        mean=float(np.mean(times)) if times else float("nan"),
        n_scoreable=len(transients),
        n_damaged=len(damaged),
        n_unchanged=unchanged,
        n_improved=improved,
        n_censored=censored,
    )


def arm_metrics(frame: pd.DataFrame) -> dict[str, dict[str, float]]:
    """The four metrics per arm, from recorded step rows.

    Every figure comes from a column the harness wrote. Nothing here
    re-derives a quantity the run already recorded.
    """
    out: dict[str, dict[str, float]] = {}
    for arm, group in frame.groupby("arm", sort=False):
        group = group.sort_values("timestep")
        excess = [None if pd.isna(v) else float(v) for v in group["excess"]]
        events = [int(v) for v in group["num_events"]]
        present = [v for v in excess if v is not None]

        recovery = censored_recovery(excess, events)
        out[str(arm)] = {
            "mean_excess": float(np.mean(present)) if present else float("nan"),
            # Of the steps where a route existed. A step with no route is
            # not "not at the optimum", it is a different failure, and it
            # is already carried by mean excess being undefined there.
            "at_optimum": (
                100.0 * sum(1 for v in present if v <= AT_OPTIMUM_TOLERANCE)
                / len(present)
                if present
                else float("nan")
            ),
            "worst_excess": float(max(present)) if present else float("nan"),
            "mean_recovery": recovery.mean,
            "_n_disruptions": float(recovery.n_scoreable),
            "_n_damaged": float(recovery.n_damaged),
            "_n_unchanged": float(recovery.n_unchanged),
            "_n_improved": float(recovery.n_improved),
            "_n_censored": float(recovery.n_censored),
        }
    return out


def _rank(values: dict[str, float], lower_is_better: bool) -> dict[str, float]:
    """Competition ranks, ties averaged, `nan` last.

    Ties get the mean of the positions they span, so two arms tied for
    first take 1.5 each and the next takes 3. Averaging rather than
    breaking ties alphabetically matters: `hybrid_adaptive` would win
    every tie against `hybrid_fixed` on spelling alone, and across four
    metrics that is a whole rank of advantage from nothing.
    """
    usable = {k: v for k, v in values.items() if not np.isnan(v)}
    missing = [k for k in values if k not in usable]
    ordered = sorted(usable, key=lambda k: usable[k], reverse=not lower_is_better)

    ranks: dict[str, float] = {}
    i = 0
    while i < len(ordered):
        j = i
        while j + 1 < len(ordered) and usable[ordered[j + 1]] == usable[ordered[i]]:
            j += 1
        shared = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[ordered[k]] = shared
        i = j + 1

    # An arm with no value for a metric cannot be ranked against one that
    # has it, and must not be quietly treated as best.
    for k in missing:
        ranks[k] = float(len(values))
    return ranks


def mean_ranks(metrics: dict[str, dict[str, float]]) -> dict[str, ArmScore]:
    """Rank on each metric separately, then average the ranks."""
    per_metric = {
        key: _rank({a: m[key] for a, m in metrics.items()}, lower)
        for key, _, lower, _fmt in METRICS
    }
    scores = {}
    for arm, m in metrics.items():
        ranks = {key: per_metric[key][arm] for key, _, _, _f in METRICS}
        scores[arm] = ArmScore(
            arm=arm,
            metrics={k: m[k] for k, _, _, _f in METRICS},
            ranks=ranks,
            mean_rank=float(np.mean(list(ranks.values()))),
            n_disruptions=int(m.get("_n_disruptions", 0)),
            n_damaged=int(m.get("_n_damaged", 0)),
            n_unchanged=int(m.get("_n_unchanged", 0)),
            n_improved=int(m.get("_n_improved", 0)),
            n_censored=int(m.get("_n_censored", 0)),
        )
    return scores


def pareto_dominance(metrics: dict[str, dict[str, float]]) -> dict[str, list[str]]:
    """Who dominates whom: at least as good on all, strictly better on one.

    No weights at all, so nothing here can be accused of being tuned. It
    will frequently return nobody dominating anybody — **that is
    information.** It marks where the mean-rank ordering reflects real
    dominance and where it is an artefact of averaging ranks across
    metrics that disagree, which is exactly the distinction a null needs
    in order to be legible.
    """
    def better_or_equal(a: float, b: float, lower: bool) -> bool:
        return a <= b if lower else a >= b

    def strictly_better(a: float, b: float, lower: bool) -> bool:
        return a < b if lower else a > b

    out: dict[str, list[str]] = {a: [] for a in metrics}
    for a, ma in metrics.items():
        for b, mb in metrics.items():
            if a == b:
                continue
            # **Compare over the metrics that EXIST for this pair.**
            #
            # Previously a NaN on either side returned False from both
            # helpers, so `all_ge` failed and no arm could dominate any
            # other. At `calm` recovery is undefined for every arm — no
            # disruptions, so nothing to recover from — and the result was
            # that the tab printed "the arms are not distinguishable" in
            # the one scenario built as a negative control, while
            # `hybrid_direct` sat at 2.44% mean excess against `aco` at
            # 13.33%.
            #
            # An undefined metric is **absent**, not incomparable. Treating
            # it as incomparable reached the null automatically from a
            # code path that mishandled an empty column, which is how a
            # null gets manufactured rather than found.
            usable = [
                (k, lower)
                for k, _, lower, _f in METRICS
                if not np.isnan(ma[k]) and not np.isnan(mb[k])
            ]
            if not usable:
                continue
            all_ge = all(better_or_equal(ma[k], mb[k], lo) for k, lo in usable)
            any_gt = any(strictly_better(ma[k], mb[k], lo) for k, lo in usable)
            if all_ge and any_gt:
                out[a].append(b)
    return out


def comparable_metrics(metrics: dict[str, dict[str, float]]) -> list[str]:
    """Which metrics are defined for every arm, so Pareto can say so.

    A dominance claim made over three metrics is a weaker statement than
    one made over four, and a reader cannot tell which they are looking
    at unless the output names them.
    """
    return [
        k
        for k, _, _, _f in METRICS
        if all(not np.isnan(m[k]) for m in metrics.values())
    ]


def score_run(frame: pd.DataFrame, display: dict[str, str] | None = None) -> dict:
    """Everything the ranking tab needs, including its own caveat.

    The evidence-strength fields are returned as **data, not decoration**,
    so the tab cannot render a ranking without them: a table from one race
    looks authoritative and is worth nothing, and this project spent five
    segments learning that.
    """
    ranked = {a: m for a, m in arm_metrics(frame).items() if a != REFERENCE_ARM}
    reference = arm_metrics(frame).get(REFERENCE_ARM)

    scores = mean_ranks(ranked) if ranked else {}
    dominance = pareto_dominance(ranked) if ranked else {}
    display = display or {}

    seeds = sorted({int(s) for s in frame["seed"].unique()})
    run_classes = sorted({str(c) for c in frame["run_class"].unique()})
    is_evidence = len(seeds) >= 30 and run_classes == ["manifest"]

    arms = [
        {
            "arm": s.arm,
            "metrics": s.metrics,
            "cells": [format_metric(k, s.metrics[k]) for k, _, _, _f in METRICS],
            "ranks": s.ranks,
            "mean_rank": s.mean_rank,
            "n_disruptions": s.n_disruptions,
            "n_damaged": s.n_damaged,
            "n_unchanged": s.n_unchanged,
            "n_improved": s.n_improved,
            "n_censored": s.n_censored,
            "dominates": sorted(dominance.get(s.arm, [])),
            "dominated_by": sorted(
                other for other, beaten in dominance.items() if s.arm in beaten
            ),
        }
        for s in sorted(scores.values(), key=lambda x: x.mean_rank)
    ]

    return {
        "columns": ["arm", *(label for _k, label, _l, _f in METRICS), "mean rank"],
        "metrics": [
            {"key": k, "label": label, "lower_is_better": lower}
            for k, label, lower, _f in METRICS
        ],
        "arms": arms,
        "reference": (
            {
                "arm": REFERENCE_ARM,
                "metrics": reference,
                "cells": [
                    format_metric(k, reference[k]) for k, _, _, _f in METRICS
                ],
            }
            if reference
            else None
        ),
        "evidence": {
            "n_seeds": len(seeds),
            "run_classes": run_classes,
            "is_evidence": is_evidence,
            "line": _evidence_line(len(seeds), run_classes, is_evidence),
        },
        "pareto_line": _pareto_line(arms, display, comparable_metrics(ranked)),
        "comparable_metrics": comparable_metrics(ranked),
        "basis_line": (
            "Ranked on "
            + ", ".join(label for _k, label, _l, _f in METRICS)
            + ". No weights and no normalisation: each metric is ranked "
            + "separately and the ranks averaged. Hops and evaluations are "
            + "deliberately excluded."
        ),
    }
