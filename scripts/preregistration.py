"""The pre-registered analysis, executable (segment 23, T3).

Entry 024 and its two amendments fix six comparisons and their decision
rules **before** the run. This module is that document as code, so that
"every pre-registered number comes out with a value" is something a
machine checks rather than something a person believes.

**Holm is applied across the whole family here, not inside each
comparison.** `stats.compare_arms` corrects within its own call, so
calling it once per comparison would produce six separate families of one
— which is no correction at all. The primitives `paired_compare` and
`holm_correct` are used directly instead.

Nothing here decides anything. It reports the numbers and the rule that
applies to them; the reading is the report's job.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from dynaswarm.analysis.load import per_trial_excess
from dynaswarm.analysis.stats import Comparison, holm_correct, paired_compare

__all__ = ["PLANNED", "Planned", "run_preregistered", "format_results",
           "dose_response"]


@dataclass(frozen=True)
class Planned:
    """One pre-registered comparison.

    Attributes:
        key: P1..P4, S1, S2 — the label used in Entry 024.
        arm_a: The arm under test.
        arm_b: Its baseline.
        tests: What a difference would mean.
    """

    key: str
    arm_a: str
    arm_b: str
    tests: str


#: The family, in Entry 024's order of precedence.
#:
#: **P3 is split into two tests, deliberately.** The pre-registration says
#: "best sensing arm vs `hybrid_scheduled`", which chooses an arm by
#: looking at the results and then tests the one that won. That inflates
#: the false-positive rate exactly as multiple testing does, and it cannot
#: be corrected for afterwards because the selection is invisible in the
#: p-value. Both sensing arms are therefore tested against the open-loop
#: control and both enter the Holm family. It is a strictly more
#: conservative reading of the same intent, and it is flagged in the
#: segment's findings rather than done quietly.
#:
#: **S2 is likewise two tests**, since "hybrid vs aco, pso" is two
#: questions.
PLANNED: tuple[Planned, ...] = (
    Planned("P1", "hybrid_adaptive", "hybrid_fixed",
            "does sensing beat not moving"),
    Planned("P2", "hybrid_direct", "hybrid_fixed",
            "same, with the split correctly positioned"),
    Planned("P3a", "hybrid_adaptive", "hybrid_scheduled",
            "does sensing beat moving blindly"),
    Planned("P3b", "hybrid_direct", "hybrid_scheduled",
            "does sensing beat moving blindly"),
    Planned("P4", "aco_adaptive", "aco_fixed",
            "Claim 2 — does adapting rho help"),
    # **P5 completes the Claim 3 set.** With P1, P2, P3a, P3b and S1 it
    # makes all six pairs among the four controlled hybrids, so nothing is
    # selected and nothing can be asked for that is not already here.
    #
    # It is also the ONLY live comparison in the calm cell. The scheduled
    # arm sweeps on a timetable and moves whether or not anything happens,
    # so at calm — where the sensing arms are identical to their twins and
    # drop out — P5 still asks a real question: does blind movement COST
    # anything when there is nothing to respond to?
    Planned("P5", "hybrid_scheduled", "hybrid_fixed",
            "does any movement help, independent of sensing"),
    Planned("S1", "hybrid_direct", "hybrid_adaptive",
            "does response shape matter"),
    Planned("S2a", "hybrid", "aco", "Claim 1 — hybrid against its components"),
    Planned("S2b", "hybrid", "pso", "Claim 1 — hybrid against its components"),
)

#: The metric every pre-registered comparison is made on. Fixed in Entry
#: 024; the other three metrics inform the ranking tab, not these tests.
METRIC = "mean_excess"


def _paired(trials: pd.DataFrame, arm_a: str, arm_b: str, metric: str):
    """Values for two arms, aligned by the trial they share.

    Aligned on `trial` rather than concatenated in whatever order the
    groupby produced. Every arm sees a byte-identical world within a trial
    (§10.2 guarantee 1), so the trial index *is* the pairing — but only if
    it is used. Two equal-length arrays are not paired data.
    """
    a = trials[trials["arm"] == arm_a].set_index("trial")[metric]
    b = trials[trials["arm"] == arm_b].set_index("trial")[metric]
    shared = sorted(set(a.index) & set(b.index))
    return (
        np.asarray([a.loc[t] for t in shared], dtype=float),
        np.asarray([b.loc[t] for t in shared], dtype=float),
        shared,
    )


def run_preregistered(frame: pd.DataFrame, metric: str = METRIC) -> dict:
    """Execute the whole family, across every scenario, and correct once.

    **The family is every test performed, not every test per scenario.**
    Entry 030 froze four scenarios, so the grid is 8 comparisons x 4
    scenarios = 32 tests. Holm is applied across all of them in a single
    correction: running the same eight hypotheses four times and reporting
    whichever cells came out significant is multiplicity, whatever the
    scenarios are called.

    The strictest Holm threshold is therefore 0.05/32 = 0.0016. That is
    conservative, and the dose-response claim does **not** depend on it —
    that claim is read off the *effect sizes* trending across light ->
    moderate -> severe, which is descriptive and needs no correction. A
    pattern that scales with disruption rate is stronger evidence than a
    single cell clearing a threshold, because a spurious effect has no
    reason to scale with the thing it depends on.

    Args:
        frame: Step rows, as `load_steps` returns them.
        metric: The per-trial column compared.

    Returns:
        ``{"results": [...], "missing": [...], "degenerate": [...]}``.
        A comparison whose arms are absent, or whose paired differences
        are all zero, is reported rather than dropped — a family that
        quietly shrinks is a correction applied to the wrong denominator.
    """
    trials = per_trial_excess(frame)
    scenarios = sorted(trials["scenario"].unique()) if "scenario" in trials else [""]

    comparisons: list[Comparison] = []
    context: list[tuple[str, Planned]] = []
    missing: list[dict] = []
    degenerate: list[dict] = []

    for scenario in scenarios:
        here = trials[trials["scenario"] == scenario] if scenario else trials
        present = set(here["arm"].unique())

        for plan in PLANNED:
            absent = [a for a in (plan.arm_a, plan.arm_b) if a not in present]
            if absent:
                missing.append({"scenario": scenario, "key": plan.key,
                                "absent": absent})
                continue
            a, b, shared = _paired(here, plan.arm_a, plan.arm_b, metric)
            if len(shared) < 2:
                missing.append({"scenario": scenario, "key": plan.key,
                                "absent": ["fewer than two paired trials"]})
                continue
            # Two arms that behaved identically give Wilcoxon nothing to
            # rank. That is not an error and must not be silently dropped:
            # at `calm` a recency-driven arm SHOULD be identical to the
            # frozen one, and "no difference at all" is the negative
            # control succeeding, not a missing measurement.
            if np.allclose(a, b):
                degenerate.append({"scenario": scenario, "key": plan.key,
                                   "n_pairs": len(shared),
                                   "note": "arms identical on every trial"})
                continue
            comparisons.append(paired_compare(a, b, label=f"{scenario}/{plan.key}"))
            context.append((scenario, plan))

    corrected = holm_correct(comparisons)
    results = [
        {
            "scenario": scenario,
            "key": p.key,
            "arm_a": p.arm_a,
            "arm_b": p.arm_b,
            "tests": p.tests,
            "n_pairs": c.n_pairs,
            "mean_a": c.mean_a,
            "mean_b": c.mean_b,
            "delta": c.delta,
            "p_value": c.p_value,
            "p_adjusted": c.p_adjusted,
            "effect": c.effect,
            "effect_label": c.effect_label,
            "significant": c.significant,
        }
        for (scenario, p), c in zip(context, corrected, strict=True)
    ]
    return {
        "metric": metric,
        "scenarios": list(scenarios),
        "results": results,
        "missing": missing,
        "degenerate": degenerate,
        "family_size": len(comparisons),
        "grid_size": len(scenarios) * len(PLANNED),
    }


def format_results(report: dict) -> str:
    """The grid as a table, with every column a reader needs."""
    lines = [
        f"  metric: {report['metric']}   scenarios: {report['scenarios']}",
        f"  grid: {report['grid_size']} cells   tested: {report['family_size']}"
        f"   (Holm across all tested cells, once)",
        "",
        f"  {'scenario':<10}{'':<5}{'comparison':<36}{'n':>4}{'delta':>10}"
        f"{'p':>9}{'p adj':>9}{'effect':>9}  sig",
        "  " + "-" * 96,
    ]
    for r in report["results"]:
        lines.append(
            f"  {r['scenario']:<10}{r['key']:<5}"
            f"{r['arm_a'] + ' vs ' + r['arm_b']:<36}"
            f"{r['n_pairs']:>4}{r['delta']:>+10.4f}{r['p_value']:>9.4f}"
            f"{r['p_adjusted']:>9.4f}{r['effect']:>+9.3f}"
            f"  {'YES' if r['significant'] else 'no'}"
        )
    if report["degenerate"]:
        lines += ["", "  IDENTICAL ARMS (no difference to rank — not an error):"]
        for d in report["degenerate"]:
            lines.append(f"    {d['scenario']}/{d['key']}: {d['note']} "
                         f"({d['n_pairs']} pairs)")
    if report["missing"]:
        lines += ["", "  NOT COMPUTABLE:"]
        for m in report["missing"]:
            lines.append(f"    {m['scenario']}/{m['key']}: {m['absent']}")
    return "\n".join(lines)


def dose_response(report: dict) -> str:
    """Effect size across light -> moderate -> severe, per comparison.

    **Read off effect sizes, not p-values, and deliberately uncorrected.**
    This is the descriptive pattern the four-scenario design exists to
    produce: if a margin grows with disruption rate it is evidence a
    spurious result has no reason to produce, and it does not depend on
    any cell clearing a threshold.
    """
    order = [s for s in ("light", "moderate", "severe") if s in report["scenarios"]]
    if len(order) < 2:
        return "  (needs at least two of light/moderate/severe)"

    by_key: dict[str, dict[str, float]] = {}
    for r in report["results"]:
        by_key.setdefault(r["key"], {})[r["scenario"]] = r["effect"]

    lines = [f"  {'comparison':<6}" + "".join(f"{s:>12}" for s in order)
             + "   monotone?"]
    lines.append("  " + "-" * (6 + 12 * len(order) + 12))
    for key in sorted(by_key):
        row = by_key[key]
        vals = [row.get(s) for s in order]
        cells = "".join("         —  " if v is None else f"{v:>+12.3f}" for v in vals)
        known = [v for v in vals if v is not None]
        mono = (len(known) == len(vals)
                and (all(x <= y for x, y in zip(known, known[1:], strict=False))
                     or all(x >= y for x, y in zip(known, known[1:], strict=False))))
        lines.append(f"  {key:<6}{cells}   {'yes' if mono else 'no'}")
    return "\n".join(lines)
