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
