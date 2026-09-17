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

__all__ = ["PLANNED", "Planned", "run_preregistered", "format_results"]


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
    """Execute the whole family and Holm-correct it as one.

    Args:
        frame: Step rows, as `load_steps` returns them.
        metric: The per-trial column compared.

    Returns:
        ``{"results": [...], "missing": [...], "n_pairs": int}``. A
        comparison whose arms are absent is reported in ``missing`` and
        **not** silently skipped — a family that quietly shrinks is a
        correction applied to the wrong number of tests.
    """
    trials = per_trial_excess(frame)
    present = set(trials["arm"].unique())

    comparisons: list[Comparison] = []
    planned: list[Planned] = []
    missing: list[dict] = []

    for plan in PLANNED:
        absent = [a for a in (plan.arm_a, plan.arm_b) if a not in present]
        if absent:
            missing.append({"key": plan.key, "absent": absent})
            continue
        a, b, shared = _paired(trials, plan.arm_a, plan.arm_b, metric)
        if len(shared) < 2:
            missing.append({"key": plan.key, "absent": ["too few paired trials"]})
            continue
        comparisons.append(paired_compare(a, b, label=plan.key))
        planned.append(plan)

    corrected = holm_correct(comparisons)
    results = [
        {
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
        for p, c in zip(planned, corrected, strict=True)
    ]
    return {
        "metric": metric,
        "results": results,
        "missing": missing,
        "family_size": len(comparisons),
    }


def format_results(report: dict) -> str:
    """The family as a table, with every column a reader needs."""
    lines = [
        f"  metric: {report['metric']}   family size: {report['family_size']}"
        f"   (Holm across all of them, not within each)",
        "",
        f"  {'':<5}{'comparison':<38}{'n':>4}{'mean A':>10}{'mean B':>10}"
        f"{'delta':>10}{'p':>9}{'p adj':>9}{'effect':>9}  sig",
        "  " + "-" * 108,
    ]
    for r in report["results"]:
        lines.append(
            f"  {r['key']:<5}{r['arm_a'] + ' vs ' + r['arm_b']:<38}"
            f"{r['n_pairs']:>4}{r['mean_a']:>10.4f}{r['mean_b']:>10.4f}"
            f"{r['delta']:>+10.4f}{r['p_value']:>9.4f}{r['p_adjusted']:>9.4f}"
            f"{r['effect']:>+9.3f}  {'YES' if r['significant'] else 'no'}"
        )
    if report["missing"]:
        lines += ["", "  NOT COMPUTABLE:"]
        for m in report["missing"]:
            lines.append(f"    {m['key']}: {m['absent']}")
    return "\n".join(lines)
