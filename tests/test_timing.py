"""The time ledger (segment Z2).

A wrong timing number is the worst defect this project can produce,
because **nothing contradicts it.** An excess figure has an oracle to
check against; a ledger has an identity that must balance; a duration
looks plausible at any value. So timing gets the same treatment the edge
ledger gets: an identity, checked against something measured
independently, with a demonstrated failure mode.
"""

from __future__ import annotations

from dynaswarm.config import (
    BudgetCfg,
    Config,
    ExperimentCfg,
    GraphCfg,
    ScenarioCfg,
)
from dynaswarm.harness.trial import run_trial

ARMS = ["astar", "aco", "pso", "hybrid"]

#: The residual may not exceed this share of a timestep. Not a precision
#: claim — it is the line past which the timers are measuring the wrong
#: region rather than merely missing interpreter noise. Measured at 2-4%
#: on the reference machine (segment Z2, T2); 25% leaves room for a
#: loaded or throttled machine without excusing a timer that has wandered
#: off the thing it is supposed to be timing.
MAX_OVERHEAD_FRACTION = 0.25


def _trial(arms=ARMS, steps=8, nodes=200, evaluations=300):
    cfg = Config(
        graph=GraphCfg(model="geometric", n_nodes=nodes, density=0.04),
        scenario=ScenarioCfg(name="clock", events_per_step=0.3, timesteps=steps),
        experiment=ExperimentCfg(arms=arms, n_trials=1, eval_seeds=[1000]),
        budget=BudgetCfg(evaluations=evaluations),
    )
    return list(run_trial(cfg, 0, arms).steps)


def _ledger(rows):
    """Per timestep: (total, arms, rebind, oracle, residual)."""
    out = {}
    for t in {r.timestep for r in rows}:
        group = [r for r in rows if r.timestep == t]
        total = group[0].step_wall_ms
        arms = sum(r.wall_ms for r in group)
        rebind = sum(r.rebind_ms for r in group)
        oracle = group[0].oracle_ms
        out[t] = (total, arms, rebind, oracle, total - arms - rebind - oracle)
    return out


def test_the_time_ledger_balances_against_measured_wall_clock():
    """Arms + rebind + oracle + overhead must reconcile to the timestep.

    **The total is measured, not summed.** `trial.py` takes its own clock
    around the whole timestep, so this compares a measured whole against
    measured parts. Summing the parts to produce the total would make the
    identity balance however wrong the parts were — segment 14 established
    that an invariant tested only against correct data cannot tell an
    invariant from a tautology.

    The residual is therefore free to come out negative, and that is the
    failure this catches: parts exceeding the whole means something is
    counted twice.
    """
    rows = _trial()
    ledger = _ledger(rows)
    assert ledger, "no timesteps were recorded"

    for t, (total, arms, rebind, oracle, residual) in sorted(ledger.items()):
        assert total > 0, f"t={t} recorded no elapsed time at all"
        assert residual >= -1e-6, (
            f"t={t}: the parts sum to more than the timestep they belong to "
            f"(arms {arms:.2f} + rebind {rebind:.2f} + oracle {oracle:.2f} = "
            f"{arms + rebind + oracle:.2f}ms against a measured {total:.2f}ms). "
            f"Something is being counted twice"
        )
        assert residual / total <= MAX_OVERHEAD_FRACTION, (
            f"t={t}: {residual / total:.1%} of the timestep is unattributed. "
            f"The timers are measuring the wrong region, not merely missing "
            f"interpreter noise"
        )


def test_the_ledger_is_not_a_tautology():
    """The residual must be genuinely non-zero, or nothing is being checked.

    If `step_wall_ms` were ever computed from the parts the identity would
    balance exactly and forever, and the test above would pass on any
    timing code at all. A residual that is small **but reliably present**
    is the evidence that the total came from its own clock.
    """
    ledger = _ledger(_trial())
    residuals = [r for _, _, _, _, r in ledger.values()]
    assert any(r > 1e-9 for r in residuals), (
        f"no timestep left any unattributed time (residuals {residuals}). Two "
        f"different faults produce this and the message must not name only "
        f"one: either `step_wall_ms` is being derived from the parts rather "
        f"than measured, in which case the ledger cannot fail; or the parts "
        f"have been inflated until they fill the whole timestep, which is a "
        f"double-count. Check which before changing anything"
    )


def test_the_oracle_time_is_never_inside_an_arms_total():
    """A\\* runs every timestep to produce the optimum.

    If any part of that landed in another arm's timer, every number in the
    timing table would be inflated by a constant that looks like real
    work — and there is no oracle for an oracle, so nothing downstream
    would contradict it.

    Asserted structurally: the oracle call sits outside the arms loop, so
    the A\\* *arm*'s own search time must be a different number from the
    per-timestep oracle time. If they were ever equal, the same call is
    being attributed twice.
    """
    rows = _trial()
    astar = [r for r in rows if r.arm == "astar"]
    assert astar, "the fixture no longer races A*"

    identical = [r for r in astar if r.wall_ms == r.oracle_ms]
    assert not identical, (
        f"{len(identical)} A* rows report a search time exactly equal to the "
        f"oracle time for the same step; the oracle's work is being counted "
        f"as an arm's"
    )

    # And no arm's search time may exceed the timestep that contains it.
    for row in rows:
        assert row.wall_ms <= row.step_wall_ms + 1e-6, (
            f"{row.arm} at t={row.timestep} searched for {row.wall_ms:.2f}ms "
            f"inside a {row.step_wall_ms:.2f}ms timestep"
        )


def test_every_arm_and_every_timestep_carries_a_timing():
    """A missing timing must be visible, not averaged over.

    A silent `None` in this column would be dropped by any mean and would
    make an arm look faster by having been measured less often.
    """
    rows = _trial()
    steps = {r.timestep for r in rows}
    arms = {r.arm for r in rows}
    assert len(rows) == len(steps) * len(arms), (
        f"{len(rows)} rows for {len(arms)} arms over {len(steps)} timesteps"
    )

    for row in rows:
        for field in ("wall_ms", "rebind_ms", "step_wall_ms", "oracle_ms"):
            value = getattr(row, field)
            assert value is not None, f"{row.arm} t={row.timestep}: {field} is None"
            assert value >= 0.0, f"{row.arm} t={row.timestep}: {field} is negative"


def test_rebind_is_recorded_separately_from_the_search():
    """T1's ruling, pinned.

    Rebind is real cost and the arms pay different amounts of it, but it
    is driven by the world changing rather than by the search budget.
    Folding it into `wall_ms` would conflate what the budget buys with
    what the disruption costs, and the report needs to be able to quote
    either.
    """
    rows = _trial()
    assert any(r.rebind_ms > 0.0 for r in rows), "rebind is never timed"
    assert all(r.rebind_ms != r.wall_ms for r in rows), (
        "rebind and search report identical durations; one is being copied "
        "from the other"
    )


def test_the_schema_and_loader_carry_the_timing_columns(tmp_path):
    """The columns must survive the round trip to Parquet and back."""
    from dynaswarm.analysis.load import load_steps
    from dynaswarm.io.writer import ResultWriter

    cfg = Config(
        graph=GraphCfg(model="geometric", n_nodes=200, density=0.04),
        scenario=ScenarioCfg(name="clock", events_per_step=0.3, timesteps=4),
        experiment=ExperimentCfg(arms=ARMS, n_trials=1, eval_seeds=[1000]),
        budget=BudgetCfg(evaluations=300),
    )
    outcome = run_trial(cfg, 0, ARMS)
    with ResultWriter(tmp_path, run_id="timing") as writer:
        writer.write(outcome)

    frame = load_steps(tmp_path, run_class=None)
    for column in ("wall_ms", "rebind_ms", "step_wall_ms", "oracle_ms"):
        assert column in frame.columns, f"{column} did not survive the schema"
        assert frame[column].notna().all(), f"{column} came back with nulls"
    assert (frame["step_wall_ms"] > 0).all()


def test_the_ledger_catches_a_double_count_where_the_doubled_part_is_material():
    """**The balance check above cannot fail on the default fixture.**

    Found by trying it: starting the arm timer before `rebind` — so rebind
    is counted once in `rebind_ms` and again inside `wall_ms` — passed all
    six tests. At 200 nodes with a 300-evaluation budget, rebind is 0.75ms
    against a 46ms timestep, so doubling it moves the residual by 1.6%
    and vanishes inside the tolerance.

    A tolerance-based identity only catches a double-count larger than the
    true overhead. So the detector has to run where the doubled quantity
    is material, which is the standing rule applied to the ledger itself:
    *a test of a feature runs on data where the feature is active.*

    Rebind cost scales with the graph; search cost scales with the budget.
    At 1000 nodes and a 20-evaluation budget rebind is ~26% of the
    timestep against a residual of ~17%, so counting it twice drives the
    residual **negative** and the balance assertion fires.
    """
    rows = _trial(arms=["aco", "pso", "hybrid"], steps=4, nodes=1000, evaluations=20)
    ledger = _ledger(rows)

    shares = [
        sum(r.rebind_ms for r in rows if r.timestep == t) / total
        for t, (total, _, _, _, _) in ledger.items()
        if total > 0
    ]
    assert max(shares) > 0.10, (
        f"rebind is at most {max(shares):.1%} of a timestep even here, so a "
        f"double-count of it would still hide inside the tolerance and this "
        f"test cannot fail — the fixture no longer exercises what it guards"
    )

    for t, (total, arms, rebind, oracle, residual) in sorted(ledger.items()):
        assert residual >= -1e-6, (
            f"t={t}: parts sum to {arms + rebind + oracle:.2f}ms against a "
            f"measured {total:.2f}ms timestep — something is counted twice"
        )


def test_recorded_time_is_consistent_with_recorded_work():
    """**A sum-based ledger is blind to attribution.** Segment Z2, my mutation.

    Rotating `wall_ms` within a timestep — every arm handed the previous
    arm's duration — passed all 513 tests. The multiset of durations is
    unchanged, so the ledger balances to the same residual, the overhead
    fraction is identical, and every number sits in a believable range.
    It is F1's shape in the timing layer: correct values, wrong owner.

    Measured at 1000 nodes under that mutation:

        astar   0 evaluations   true   3.22ms -> reported 122.38ms
        aco   300 evaluations   true 114.68ms -> reported   3.28ms

    An identity over a sum cannot see this, because the sum is right. The
    check that can is a cross-column one: **time must be consistent with
    the work the same row records.** An arm that spent no evaluation
    budget did no search, and cannot have taken longer than one that
    spent the whole of it.

    This is deliberately a loose bound, not a ranking. It is not asserting
    which metered arm is fastest — the timing table reports that with its
    spread, and at some sizes the arms are not separable at all.
    """
    rows = _trial(steps=6, nodes=1000, evaluations=300)

    unmetered = [r for r in rows if r.evaluations_spent == 0]
    metered = [r for r in rows if r.evaluations_spent > 0]
    assert unmetered and metered, (
        "the fixture no longer contains both a metered and an unmetered arm, "
        "so there is nothing to cross-check"
    )

    slowest_free = max(r.wall_ms for r in unmetered)
    fastest_paid = min(r.wall_ms for r in metered)
    assert slowest_free <= max(fastest_paid, 1e-6) * 2.0, (
        f"an arm that spent 0 evaluations took {slowest_free:.2f}ms while an "
        f"arm that spent its whole budget took {fastest_paid:.2f}ms. Time is "
        f"not attributed to the arm that did the work"
    )

    # And within a row, spending nothing must not cost more than the
    # timestep's own oracle call, which is the same kind of exact search.
    for row in unmetered:
        assert row.wall_ms <= row.step_wall_ms, (
            f"{row.arm} at t={row.timestep} reports {row.wall_ms:.2f}ms inside "
            f"a {row.step_wall_ms:.2f}ms timestep"
        )
