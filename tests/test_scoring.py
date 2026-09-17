"""The scorer (segment Z).

The ranking is the artefact an examiner reads first, so the tests here are
mostly about what it must refuse to do: drop an arm's worst cases, rank
the oracle, or render a table without saying how much evidence is behind
it.
"""

from __future__ import annotations

import pandas as pd
import pytest

from dynaswarm.analysis.scoring import (
    METRICS,
    REFERENCE_ARM,
    arm_metrics,
    censored_recovery,
    mean_ranks,
    pareto_dominance,
    score_run,
)


def _frame(series: dict[str, tuple[list[float], list[int]]], run_class="exploratory"):
    """A step frame with the columns the scorer reads, and nothing else.

    Built by hand rather than run, because the behaviour under test —
    a disruption that is never recovered from — does not occur in the
    scenarios the harness produces at any setting tried (segment Z, T2).
    A property that cannot be reached by a real run still has to be
    guarded, and the production entry point is `score_run` on a frame,
    which is exactly what this calls.
    """
    rows = []
    for arm, (excess, events) in series.items():
        for t, (e, n) in enumerate(zip(excess, events, strict=True)):
            rows.append({
                "arm": arm, "timestep": t, "excess": e, "num_events": n,
                "seed": 1000, "run_class": run_class,
            })
    return pd.DataFrame(rows)


def _gives_up(horizon=60):
    """Recovers instantly twice, then breaks permanently."""
    excess, events = [0.10] * 3, [0] * 3
    for _ in range(2):
        excess += [0.50, 0.10] + [0.10] * 4
        events += [5, 0] + [0] * 4
    excess.append(0.50)
    events.append(5)
    while len(excess) < horizon:
        excess.append(0.50)
        events.append(0)
    return excess[:horizon], events[:horizon]


def _always_recovers(horizon=60):
    """Recovers from every disruption, slowly."""
    excess, events = [0.10] * 3, [0] * 3
    for _ in range(3):
        excess += [0.50] + [0.50] * 7 + [0.10] + [0.10] * 4
        events += [5] + [0] * 7 + [0] + [0] * 4
    while len(excess) < horizon:
        excess.append(0.10)
        events.append(0)
    return excess[:horizon], events[:horizon]


# ---------------------------------------------------------------------------
# T2 — the one that matters
# ---------------------------------------------------------------------------


def test_an_arm_that_never_recovers_does_not_outrank_one_that_always_does():
    """**Censored recoveries must never be dropped.**

    This is the single quiet `dropna` that would bias the entire ranking
    in favour of the worst possible behaviour: an arm that gives up
    permanently has its failures deleted from its own average, leaving
    only the disruptions it handled well.

    Measured on the fixtures below — three disruptions each:

    * `gives_up` recovers in 1 step twice and never recovers once.
      **Dropped: 1.00. Counted: 15.67.**
    * `always_recovers` takes 8 steps every time. **8.00 either way.**

    So dropping makes the arm that permanently failed look eight times
    better than the arm that always came back.
    """
    frame = _frame({"gives_up": _gives_up(), "always_recovers": _always_recovers()})
    scores = mean_ranks(arm_metrics(frame))

    gives_up = scores["gives_up"]
    always = scores["always_recovers"]

    assert gives_up.n_censored == 1, "the fixture no longer censors anything"
    assert always.n_censored == 0, "the comparison arm should recover every time"

    assert gives_up.metrics["mean_recovery"] > always.metrics["mean_recovery"], (
        f"the arm that never recovered scored {gives_up.metrics['mean_recovery']:.2f} "
        f"against {always.metrics['mean_recovery']:.2f} for the arm that always "
        f"did. Its unrecovered disruption has been dropped from its own average"
    )
    assert gives_up.ranks["mean_recovery"] > always.ranks["mean_recovery"], (
        "the arm that gives up out-ranks the arm that always recovers"
    )


def test_a_censored_recovery_is_counted_at_the_remaining_horizon():
    """The value used is a lower bound, and is stated as one.

    An unrecovered disruption is scored at the steps remaining after it
    landed. The arm had not recovered by the end, so the truth is *at
    least* this — under-stating rather than over-stating, which is the
    safe direction and needs no penalty constant to defend.
    """
    excess, events = _gives_up(horizon=60)
    mean, n, censored = censored_recovery(excess, events)
    assert (n, censored) == (3, 1)
    # Two instant recoveries plus one scored at the remaining horizon.
    last = max(i for i, e in enumerate(events) if e > 0)
    expected = (1.0 + 1.0 + (len(excess) - last)) / 3
    assert mean == pytest.approx(expected), (
        f"censored case scored as {mean * 3 - 2:.1f} steps, expected the "
        f"remaining horizon of {len(excess) - last}"
    )


def test_a_disruption_with_no_time_to_recover_is_still_excluded():
    """Censoring and no-opportunity are different, and only one is counted.

    `disruptions()` drops events inside `MIN_HORIZON` of the end, and that
    exclusion is kept deliberately. An arm hit on the final timestep had
    no chance to recover, and scoring that as a failure would penalise
    whichever arm happened to be hit late — right-censoring that falls
    unevenly and would read as a real difference between arms.
    """
    excess = [0.10] * 55 + [0.50] * 5
    events = [0] * 55 + [5] + [0] * 4
    _, n, censored = censored_recovery(excess, events)
    assert n == 0 and censored == 0, (
        "a disruption five steps from the end was scored; an arm has no "
        "opportunity to recover there and would be penalised for being hit late"
    )


# ---------------------------------------------------------------------------
# T4 — the oracle is a reference, not a competitor
# ---------------------------------------------------------------------------


def test_the_reference_arm_is_never_ranked():
    """A* is exact by construction and would win every metric.

    Third place out of four, when one of the four cannot lose, is not a
    finding. This is the check that catches it being quietly re-added by
    someone looping over every arm in the frame.
    """
    frame = _frame({
        REFERENCE_ARM: ([0.0] * 60, [0] * 60),
        "hybrid_fixed": _always_recovers(),
        "gives_up": _gives_up(),
    })
    result = score_run(frame)

    ranked = [a["arm"] for a in result["arms"]]
    assert REFERENCE_ARM not in ranked, (
        f"{REFERENCE_ARM} is being ranked against arms that can lose"
    )
    assert result["reference"] is not None, (
        "the reference arm was dropped entirely rather than shown beside "
        "the table — it is the line every other number is measured from"
    )
    assert result["reference"]["metrics"]["mean_excess"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# T5 — the tab must state its own evidence strength
# ---------------------------------------------------------------------------


def test_the_score_always_carries_its_evidence_strength():
    """A ranking table from one race looks authoritative and is worth nothing.

    Returned as data rather than left to the view, so a tab physically
    cannot render the ordering without the caveat that qualifies it.
    """
    frame = _frame({"a": _always_recovers(), "b": _gives_up()})
    result = score_run(frame)

    assert "evidence" in result
    assert result["evidence"]["n_seeds"] == 1
    assert result["evidence"]["run_classes"] == ["exploratory"]
    assert result["evidence"]["is_evidence"] is False, (
        "a single exploratory seed is being reported as evidence"
    )


def test_evidence_requires_both_a_manifest_class_and_enough_seeds():
    """Neither condition alone is sufficient, and both are checked."""
    many_seeds = pd.concat([
        _frame({"a": _always_recovers(), "b": _gives_up()}).assign(seed=s)
        for s in range(40)
    ])
    assert score_run(many_seeds)["evidence"]["is_evidence"] is False, (
        "40 exploratory seeds counted as evidence; scratch work cannot "
        "become evidence by being repeated"
    )

    promoted = many_seeds.assign(run_class="manifest")
    assert score_run(promoted)["evidence"]["is_evidence"] is True

    few = promoted[promoted["seed"] < 5]
    assert score_run(few)["evidence"]["is_evidence"] is False


# ---------------------------------------------------------------------------
# T7 — the metric set is pre-registered and cannot grow quietly
# ---------------------------------------------------------------------------


def test_the_metric_set_is_exactly_the_four():
    """Entry 024 fixed these **before** the run. That is the whole point.

    A metric set that can grow after the outcome is known is not
    pre-registered, and a fifth metric added later is indistinguishable
    from one chosen because it helped. If this fails, someone has to say
    in one sentence why more of the new thing is better — and write it in
    the log, not in a commit message.
    """
    assert tuple(k for k, *_ in METRICS) == (
        "mean_excess", "at_optimum", "worst_excess", "mean_recovery",
    )
    assert len(METRICS) == 4


def test_hops_and_evaluations_are_not_in_the_score():
    """The exclusions are as deliberate as the inclusions.

    `hops` is not a virtue — a shorter route that costs more is worse —
    and `evaluations_spent` is identical across metered arms by §10.2, so
    it carries no information and would only dilute the ranks.
    """
    keys = {k for k, *_ in METRICS}
    for excluded in ("hops", "path_len", "evaluations", "evaluations_spent", "cost"):
        assert excluded not in keys, (
            f"`{excluded}` has entered the score; it is a diagnostic, not a virtue"
        )


# ---------------------------------------------------------------------------
# The ranking mechanics
# ---------------------------------------------------------------------------


def test_ties_share_an_averaged_rank_rather_than_breaking_alphabetically():
    """Two arms with identical metrics must score identically.

    Without averaged ties, `hybrid_adaptive` beats `hybrid_fixed` on
    spelling in every tied metric, and across four metrics that is a
    whole rank of advantage arriving from nothing.
    """
    same = _always_recovers()
    frame = _frame({"hybrid_adaptive": same, "hybrid_fixed": same})
    scores = mean_ranks(arm_metrics(frame))
    assert scores["hybrid_adaptive"].mean_rank == scores["hybrid_fixed"].mean_rank
    assert scores["hybrid_adaptive"].mean_rank == pytest.approx(1.5)


def test_pareto_requires_at_least_as_good_everywhere():
    """Dominance is not "wins on average" — it is "never worse"."""
    frame = _frame({"strong": _always_recovers(), "weak": _gives_up()})
    metrics = arm_metrics(frame)
    dominance = pareto_dominance(metrics)

    # `weak` recovers instantly on the two it survives, so it is better on
    # nothing overall but not worse on everything either.
    assert "strong" not in dominance["weak"], "the failing arm dominates"

    # A genuinely dominated pair: identical but for one strictly worse metric.
    good = _always_recovers()
    worse_excess = ([min(v + 0.05, 1.0) for v in good[0]], good[1])
    pair = pareto_dominance(arm_metrics(_frame({"a": good, "b": worse_excess})))
    assert "b" in pair["a"], "a strictly-better arm does not dominate"
    assert "a" not in pair["b"]


def test_at_optimum_means_at_the_optimum_not_near_it():
    """**The tolerance is a semantic boundary, not a rounding convenience.**

    Segment Z, my own mutation: raising `AT_OPTIMUM_TOLERANCE` from 1e-9
    to 0.005 passed all 501 tests, changed every arm's `% at optimum`,
    and **swapped `hybrid_scheduled` and `hybrid_fixed` in the final
    ranking**. It reads as a floating-point fix — "excess is a ratio of
    floats, 1e-9 is too strict" — and nothing pinned it.

    The metric is labelled *% of steps at optimum*. If it counts routes
    that are 0.5% worse, the label is false and the column silently
    becomes a different metric that nobody pre-registered.

    So this asserts the **meaning** rather than the constant: a route
    0.1% above optimal is genuinely suboptimal — on a path costing ~100
    that is 0.1 cost units, orders of magnitude above float noise — and
    must not be counted. A tolerance large enough to admit it has stopped
    measuring what its name says.
    """
    from dynaswarm.analysis.scoring import AT_OPTIMUM_TOLERANCE

    horizon = 30
    exact = _frame({"exact": ([0.0] * horizon, [0] * horizon)})
    near = _frame({"near": ([0.001] * horizon, [0] * horizon)})

    assert arm_metrics(exact)["exact"]["at_optimum"] == pytest.approx(100.0)
    assert arm_metrics(near)["near"]["at_optimum"] == pytest.approx(0.0), (
        f"a route 0.1% above optimal counts as 'at the optimum'. The "
        f"tolerance is {AT_OPTIMUM_TOLERANCE}, which is wide enough to "
        f"admit real suboptimality, so the column no longer measures what "
        f"it is labelled"
    )
    assert AT_OPTIMUM_TOLERANCE < 1e-6, (
        f"tolerance {AT_OPTIMUM_TOLERANCE} admits more than float noise"
    )
