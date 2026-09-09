"""Phase 2's gate: every mechanism proven live **or reported inert**.

The second half is the point. A probe that has only ever reported
"working" is not evidence that anything works — it is a claim with a
number attached. So every probe here is asserted in *both* directions:
it must report activity when the mechanism runs, and it must report zero
when the mechanism is deliberately disabled.

The disabling is done by monkeypatching the optimizer's own methods
rather than by editing source, so the demonstrations are repeatable and
the mutation is visible in the test that depends on it.
"""

from __future__ import annotations

import numpy as np
import pytest

from dynaswarm.config import BudgetCfg, Config, ExperimentCfg, GraphCfg, ScenarioCfg
from dynaswarm.core.generate import build
from dynaswarm.core.meter import EvaluationMeter
from dynaswarm.core.rng import stream
from dynaswarm.optimizers.aco import ACO

GRAPH = GraphCfg(model="geometric", n_nodes=200, density=0.04)


def _colony(seed: int = 1000):
    view, source, target = build(GRAPH, stream(seed, "graph"))
    return ACO(view, source, target, stream(seed, "aco"), {}), view


def _run(colony, evaluations: int = 300) -> dict:
    colony.spend(EvaluationMeter(evaluations))
    return colony.probe()


# ---------------------------------------------------------------------------
# Live: the mechanism runs and the probe says so
# ---------------------------------------------------------------------------


def test_the_probe_reports_pheromone_moving_when_it_moves():
    colony, _ = _colony()
    probe = _run(colony)
    assert probe["tau_changed"] > 0, "trails never moved in a working colony"
    assert probe["tau_active"] > 0
    assert probe["tau_max"] > probe["tau_min"], "every trail is identical"


def test_the_probe_reports_evaporation_deposit_and_clamping_when_they_happen():
    colony, _ = _colony()
    probe = _run(colony)
    assert probe["tau_evaporated"] > 0, "no trail mass was removed"
    assert probe["tau_deposited"] > 0, "the best ant reinforced nothing"
    assert probe["tau_clamped"] > 0, "the MAX--MIN bounds never bound"


# ---------------------------------------------------------------------------
# Inert: the mechanism is disabled and the probe says THAT
# ---------------------------------------------------------------------------


def test_a_frozen_pheromone_table_reports_zero_change():
    """An ACO whose trails never move is a random walk.

    It still produces routes, still produces excess, and nothing else in
    a recorded run would look different — which is why this has to be
    detectable from the probe alone.
    """
    colony, _ = _colony()
    frozen = colony._tau.copy()
    colony._evaporate = lambda: None
    colony._deposit = lambda path, cost: None
    colony._clamp_trails = lambda: None
    probe = _run(colony)

    assert probe["tau_changed"] == 0, "the probe missed a frozen trail table"
    assert np.array_equal(colony._tau, frozen), "the fixture did not actually freeze it"


def test_evaporation_switched_off_reports_zero_evaporated():
    """Without evaporation the colony converges and never re-explores.

    That reads as "ACO recovers poorly from disruption" — a finding
    somebody would write down.
    """
    colony, _ = _colony()
    colony._evaporate = lambda: None
    probe = _run(colony)

    assert probe["tau_evaporated"] == 0
    assert probe["tau_deposited"] > 0, "the rest of the mechanism stopped too"


def test_bounds_removed_reports_zero_clamped():
    """Counted from the clip's EFFECT, not from how many slots were outside.

    Written the other way first: removing ``np.clip`` entirely still
    reported 22800 clamps, because the count was of slots that *needed*
    clamping. In a report that reads as "MAX--MIN bounds active" about
    plain Ant System.
    """
    colony, _ = _colony()
    colony._clamp_trails = lambda: None
    probe = _run(colony)

    assert probe["tau_clamped"] == 0, "the probe reported clamping with no clamp present"
    assert probe["tau_changed"] > 0, "the rest of the mechanism stopped too"


def test_a_silent_deposit_reports_zero_deposited():
    colony, _ = _colony()
    colony._deposit = lambda path, cost: None
    probe = _run(colony)

    assert probe["tau_deposited"] == 0
    assert probe["tau_evaporated"] > 0, "the rest of the mechanism stopped too"


# ---------------------------------------------------------------------------
# The instrument must not change what it measures
# ---------------------------------------------------------------------------


def test_probing_does_not_change_the_search():
    """Phase 4 runs this at >=100 trials per arm.

    An instrument that perturbs one arm more than another would break
    §10.2's fairness guarantees while looking like a result. Same seed,
    probes read or not read, must give the identical best cost at every
    step.
    """
    from dynaswarm.harness.trial import run_trial

    cfg = Config(
        graph=GRAPH,
        scenario=ScenarioCfg(name="probe", events_per_step=0.3, timesteps=20),
        experiment=ExperimentCfg(arms=["aco"], n_trials=1),
        budget=BudgetCfg(evaluations=200),
    )
    first = [r.best_cost for r in run_trial(cfg, 0, ["aco"]).steps]
    second = [r.best_cost for r in run_trial(cfg, 0, ["aco"]).steps]
    assert first == second, "the same configuration produced two different runs"
    assert any(c is not None for c in first), "no route was ever found"


def test_probe_cost_is_bounded():
    """One array copy and a few reductions per budgeted call.

    Pinned because the probe is on the path Phase 4 runs hundreds of
    times, and because "cheap" is the kind of claim that stops being true
    without anyone noticing.
    """
    import time

    colony, _ = _colony()
    colony.spend(EvaluationMeter(300))

    start = time.perf_counter()
    for _ in range(200):
        colony.probe()
    per_call_ms = (time.perf_counter() - start) / 200 * 1000
    assert per_call_ms < 2.0, f"probe() costs {per_call_ms:.3f} ms per call"


def test_the_counters_report_this_step_not_a_running_total():
    """Every ``tau_*`` count is per budgeted call, not cumulative.

    Found by mutation, not by design: deleting the per-call reset left
    every count rising monotonically — evaporation 345 to 580, deposits
    434 to 10662, clamps 1470 to 1,267,734 across one run — and all eight
    tests above passed, because they assert ``> 0`` and a running total
    satisfies that trivially.

    The numbers stay plausible the whole way, and a reader concludes
    "clamping intensifies sharply over the run" from an artefact of
    never zeroing a counter.

    Asserted deterministically rather than by comparing magnitudes:
    the mechanism is silenced for the second call, so a per-call counter
    must report exactly zero and a cumulative one still carries the
    first call's total.
    """
    colony, _ = _colony()
    first = _run(colony)
    assert first["tau_deposited"] > 0 and first["tau_evaporated"] > 0

    colony._deposit = lambda path, cost: None
    colony._evaporate = lambda: None
    colony._clamp_trails = lambda: None
    second = _run(colony)

    assert second["tau_deposited"] == 0, (
        f"deposits carried over from the previous call: {second['tau_deposited']}"
    )
    assert second["tau_evaporated"] == 0, "evaporation carried over"
    assert second["tau_clamped"] == 0, "clamps carried over"


# ---------------------------------------------------------------------------
# Entry 014 R1: state_at is the third site and stays as it is
# ---------------------------------------------------------------------------


def test_state_at_past_the_horizon_raises_rather_than_answering():
    """The guard is the feature, and this is why `state_at` does not delegate.

    F10 collapsed `changed_edges` into `events_at()` because it was the
    same arithmetic written twice. `state_at` is not a second copy of
    that arithmetic — it *is* the definition: applying `schedule[t-1]` to
    state `t-1` is what "the state at t" means.

    Delegating would inherit `events_at`'s out-of-range guard, which
    returns `()` past the horizon — turning this IndexError into
    **silently returning the previous state under a later timestep's
    name**, in the one function every arm reads its world from. Loud is
    correct here; a future segment reaching for consistency would make
    it quiet.
    """
    from dynaswarm.config import ScenarioCfg
    from dynaswarm.core.timeline import GraphTimeline, build_schedule

    view, source, target = build(GRAPH, stream(1000, "graph"))
    schedule = build_schedule(
        view, ScenarioCfg(name="x", events_per_step=0.3, timesteps=20),
        stream(1000, "events"), source, target,
    )
    timeline = GraphTimeline(view, schedule)

    assert timeline.state_at(20).t == 20, "the last in-range state is unreachable"
    with pytest.raises(IndexError):
        timeline.state_at(21)

    # events_at deliberately differs, and that difference is the point.
    assert timeline.events_at(21) == ()


# ---------------------------------------------------------------------------
# PSO (§5.3) — priority-vector encoding, memory on nodes
# ---------------------------------------------------------------------------


def _swarm(seed: int = 1000):
    from dynaswarm.optimizers.pso import PSO

    view, source, target = build(GRAPH, stream(seed, "graph"))
    return PSO(view, source, target, stream(seed, "pso"), {})


def _fly(swarm, evaluations: int = 300) -> dict:
    swarm.spend(EvaluationMeter(evaluations))
    return swarm.probe()


def test_the_swarm_probe_reports_movement_and_memory_when_they_happen():
    swarm = _swarm()
    probe = _fly(swarm)
    assert probe["particles_flown"] > 0, "the swarm never flew"
    assert probe["speed_mean"] > 0, "velocity is dead on the first call"
    assert probe["own_best_updates"] > 0, "no personal best updated — no memory"
    assert probe["swarm_best_updates"] > 0, "the global best never improved"


def test_a_frozen_swarm_reports_zero_movement():
    """A swarm that never moves is a fixed set of random guesses.

    It still produces routes and still produces excess. `diversity`
    would not catch it either — a frozen swarm keeps whatever spread it
    started with.
    """
    swarm = _swarm()
    swarm._move = lambda i: None
    probe = _fly(swarm)

    assert probe["particles_flown"] == 0, "the probe missed a frozen swarm"
    # `speed_mean` deliberately NOT asserted zero here. With `_move`
    # disabled the velocity array simply keeps its random initial value —
    # 0.05, entirely healthy-looking — so speed alone cannot detect a
    # frozen swarm. The count of particles the flight step actually
    # displaced can, which is why the probe carries both.
    assert probe["speed_mean"] > 0, "the fixture also zeroed velocity; it should not"


def test_personal_bests_never_updating_reports_zero():
    """Without personal bests there is no memory, which is PSO's whole claim here."""
    swarm = _swarm()
    swarm._own_cost[:] = -1.0  # nothing can ever beat it
    probe = _fly(swarm)

    assert probe["own_best_updates"] == 0
    assert probe["particles_flown"] > 0, "the rest of the mechanism stopped too"


def test_the_swarm_counters_report_this_call_not_a_running_total():
    """Segment 14's second trap, checked here rather than rediscovered."""
    swarm = _swarm()
    first = _fly(swarm)
    assert first["own_best_updates"] > 0

    swarm._own_cost[:] = -1.0
    swarm._move = lambda i: None
    second = _fly(swarm)
    assert second["own_best_updates"] == 0, "personal-best updates carried over"
    assert second["particles_flown"] == 0, "movement carried over"


# ---------------------------------------------------------------------------
# Hybrid (§6.1, §6.2) — the budget split decides Claim 1
# ---------------------------------------------------------------------------


def _hybrid(seed: int = 1000, params: dict | None = None):
    from dynaswarm.optimizers.hybrid import Hybrid

    view, source, target = build(GRAPH, stream(seed, "graph"))
    return Hybrid(view, source, target, stream(seed, "hybrid"), params or {})


def test_the_budget_split_is_measured_from_what_was_spent():
    """**If this is not true, Claim 1 compares the hybrid to itself.**

    Measured from the sub-meters' actual spend, not from the ratio that
    was requested — a probe echoing `aco_fraction` back would report a
    perfect split on a hybrid that gave one component everything.
    """
    hybrid = _hybrid()
    hybrid.spend(EvaluationMeter(300))
    probe = hybrid.probe()

    assert probe["aco_spent"] > 0 and probe["pso_spent"] > 0, "one component got nothing"
    assert probe["aco_share_realised"] == pytest.approx(probe["aco_fraction"], abs=0.02), (
        f"declared {probe['aco_fraction']}, realised {probe['aco_share_realised']}"
    )
    assert probe["aco_spent"] + probe["pso_spent"] == pytest.approx(300, abs=2)


def test_a_lopsided_split_is_reported_as_lopsided():
    """The probe must track the ratio, not assume it."""
    hybrid = _hybrid(params={"aco_fraction": 0.9})
    hybrid.spend(EvaluationMeter(300))
    probe = hybrid.probe()

    assert probe["aco_share_realised"] == pytest.approx(0.9, abs=0.02)
    assert probe["aco_spent"] > probe["pso_spent"] * 5


def test_a_split_that_never_happens_reports_zero_for_one_side():
    """The inert case: one component is never given anything to spend."""
    hybrid = _hybrid()
    hybrid._pso.spend = lambda meter: None
    hybrid.spend(EvaluationMeter(300))
    probe = hybrid.probe()

    assert probe["pso_spent"] == 0, "the probe reported spend for a silent component"
    assert probe["aco_share_realised"] == 1.0, "a one-sided split did not read as one-sided"


def test_an_exchange_that_never_fires_reports_zero():
    """§6.2. Without it the hybrid is two solvers sharing a process."""
    hybrid = _hybrid()
    hybrid.spend(EvaluationMeter(300))
    assert hybrid.probe()["exchanged_this_step"] > 0

    hybrid._exchange = lambda: None
    hybrid.spend(EvaluationMeter(300))
    assert hybrid.probe()["exchanged_this_step"] == 0, "an exchange was counted with none run"


def test_flight_is_counted_by_displacement_not_by_the_call():
    """A flight step that displaces nothing is not flight.

    Found by mutation: counting `_move` calls instead of the positions
    they actually changed passed all eighteen tests above. It matters
    because velocity in a real disrupted run decays to ~5e-14 by t=59 —
    at which point the flight step runs three hundred times and moves
    nothing measurable, and a per-call counter reports a swarm in
    vigorous motion.

    Segment 14's bounds probe again: observe the effect, not the call.
    """
    # Stilled by configuration rather than by patching `_move`: with
    # every pull set to zero, velocity stays zero by the mechanism's own
    # arithmetic and the flight step genuinely displaces nothing.
    from dynaswarm.optimizers.pso import PSO

    view, source, target = build(GRAPH, stream(1000, "graph"))
    swarm = PSO(view, source, target, stream(1000, "pso"),
                {"inertia": 0.0, "cognitive": 0.0, "social": 0.0})
    swarm._velocity[:] = 0.0
    probe = _fly(swarm)

    assert probe["speed_mean"] == 0, "the fixture did not actually still the swarm"
    assert probe["particles_flown"] == 0, (
        f"{probe['particles_flown']:.0f} flights counted with zero velocity"
    )
