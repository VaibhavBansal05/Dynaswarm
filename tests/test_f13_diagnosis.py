"""F13: the diagnosis, and the fix that followed it.

Segment 17 established that PSO's velocity collapse was never about
disruption. It was caused by ``PSO.rebind`` invalidating every personal
best cost, and the harness calls ``rebind`` on every arm at every
timestep whether or not the graph changed.

Segment 18 guards that invalidation on ``state_hash()``. These tests pin
both halves: the mechanism is still the mechanism — wipe the costs and
the swarm still collapses — and the trigger is now guarded, so a quiet
step costs the swarm nothing.
"""

from __future__ import annotations

import numpy as np
import pytest

from dynaswarm.config import GraphCfg
from dynaswarm.core.generate import build
from dynaswarm.core.meter import EvaluationMeter
from dynaswarm.core.rng import stream
from dynaswarm.optimizers.pso import PSO

GRAPH = GraphCfg(model="geometric", n_nodes=200, density=0.04)


def _swarm(seed: int = 1000):
    view, source, target = build(GRAPH, stream(seed, "graph"))
    return PSO(view, source, target, stream(seed, "pso"), {}), view


def _fly(mode: str, steps: int = 60, seed: int = 1000) -> tuple[float, float]:
    swarm, view = _swarm(seed)
    for _ in range(steps):
        if mode == "rebind":
            swarm.rebind(view)              # the SAME view — nothing changed
        elif mode == "wipe":
            swarm._own_cost[:] = np.inf     # the mechanism, unguarded
        swarm.spend(EvaluationMeter(300))
    return (
        float(np.abs(swarm._velocity).mean()),
        float(np.mean(np.std(swarm._position, axis=0))),
    )


def _changed(view, factor: float = 3.0):
    weight = np.array(view.weight, dtype=np.float64)
    weight[0] *= factor
    return view.with_state(weight, np.asarray(view.active), view.t + 1)


# ---------------------------------------------------------------------------
# The fix
# ---------------------------------------------------------------------------


def test_a_quiet_step_invalidates_nothing():
    """The fix, directly: rebind on an unchanged graph must not wipe memory."""
    swarm, view = _swarm()
    swarm.spend(EvaluationMeter(300))
    before = swarm._own_cost.copy()
    assert np.isfinite(before).any(), "no costs were established to preserve"

    swarm.rebind(view)
    assert np.array_equal(swarm._own_cost, before), (
        "a quiet step discarded the swarm's memory"
    )


def test_a_changed_graph_still_invalidates():
    """The other direction. A fix that never invalidates is worse than the bug.

    A cost measured against a graph that no longer exists is a stale
    number, and carrying it forward would let the swarm chase a route
    that has since closed.
    """
    swarm, view = _swarm()
    swarm.spend(EvaluationMeter(300))
    assert np.isfinite(swarm._own_cost).any()

    swarm.rebind(_changed(view))
    assert np.isinf(swarm._own_cost).all(), (
        "a real graph change did not invalidate the remembered costs"
    )


@pytest.mark.parametrize("seed", [1000, 1001, 1002, 7, 42, 9999])
def test_velocity_survives_a_static_sixty_step_run(seed):
    """**The regression test that would have caught F13 originally.**

    Sixty steps, nothing changing, rebind called every step exactly as
    the harness calls it. The outcome must be identical to never calling
    rebind at all — before the fix velocity fell by five to eleven orders
    of magnitude, and seed 1000 was the mildest of the six.
    """
    quiet, quiet_spread = _fly("none", seed=seed)
    rebound, rebound_spread = _fly("rebind", seed=seed)

    assert rebound == pytest.approx(quiet, rel=1e-9), (
        f"seed {seed}: rebind still changes the outcome "
        f"({rebound:.3e} against {quiet:.3e})"
    )
    assert rebound_spread == pytest.approx(quiet_spread, rel=1e-9)
    assert quiet > 1e-4, f"seed {seed} has no healthy baseline: {quiet:.3e}"


def test_the_mechanism_is_unchanged_only_the_trigger_is_guarded():
    """Wiping the costs directly must still collapse the swarm.

    The fix guards *when* the invalidation fires; it does not make the
    invalidation harmless. If this stopped collapsing, the guard would be
    hiding the mechanism rather than gating it, and whoever later removed
    the guard would find nothing apparently wrong.
    """
    quiet, _ = _fly("none")
    wiped, wiped_spread = _fly("wipe")

    assert wiped < quiet / 1e4, (
        f"wiping memory no longer collapses the swarm: {wiped:.3e} against {quiet:.3e}"
    )
    assert wiped_spread < 1e-5


# ---------------------------------------------------------------------------
# The things not to break
# ---------------------------------------------------------------------------


def test_rebind_still_propagates_the_view_every_step():
    """Why the guard is in PSO and not at the call site.

    `rebind` is how an optimizer receives the current world. Making the
    *call* conditional would leave every arm searching a stale graph — a
    far worse defect than the one being repaired. So the view assignment
    must happen even when the hash matches.
    """
    swarm, view = _swarm()
    changed = _changed(view, factor=5.0)

    swarm.rebind(changed)
    assert swarm._view is changed, "the optimizer did not receive the new view"

    swarm.rebind(view)
    assert swarm._view is view, "an unchanged-hash rebind skipped the view assignment"


def test_the_harness_still_calls_rebind_unconditionally():
    """Pinned as source, because a comment alone will not stop a refactor."""
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1]
        / "src" / "dynaswarm" / "harness" / "trial.py"
    ).read_text()
    call = "arm.optimizer.rebind(state)"
    assert call in source
    tail = source[: source.index(call)].rsplit("for arm in arms:", 1)[-1]
    assert "if" not in tail, (
        "rebind has become conditional at the call site; view propagation is at risk"
    )


def test_the_hybrid_inherits_the_fix():
    """It passes rebind down. Asserted, not assumed."""
    from dynaswarm.optimizers.hybrid import Hybrid

    view, source, target = build(GRAPH, stream(1000, "graph"))
    hybrid = Hybrid(view, source, target, stream(1000, "hybrid"), {})
    hybrid.spend(EvaluationMeter(300))
    before = hybrid._pso._own_cost.copy()
    assert np.isfinite(before).any()

    hybrid.rebind(view)
    assert np.array_equal(hybrid._pso._own_cost, before), (
        "the Hybrid's swarm still loses its memory on a quiet step"
    )

    hybrid.rebind(_changed(view))
    assert np.isinf(hybrid._pso._own_cost).all(), (
        "the Hybrid's swarm kept stale costs across a real change"
    )


def test_inertia_is_formally_dropped_not_overlooked():
    """§17.1 settled: silence is not an option, so the absence is pinned.

    `inertia` is applied at `pso.py:204` and is deliberately not in
    `EXPLORE_SIGN`. Without this test the exclusion is indistinguishable
    from an oversight, which is exactly the state §17.1 objected to —
    and somebody would eventually "fix" it by adding an entry.
    """
    from dynaswarm.control.controllers import EXPLORE_SIGN

    assert "inertia" not in EXPLORE_SIGN, (
        "inertia has been made adaptable; §17.1's decision needs revisiting, "
        "and hybrid_adaptive now has two adapting mechanisms at once"
    )
    for adaptable in ("rho", "aco_fraction"):
        assert adaptable in EXPLORE_SIGN, "the table itself has changed shape"


@pytest.mark.parametrize("seed", [1000, 42])
def test_velocity_survives_a_static_run_through_the_real_harness(seed):
    """**The test the unit ones could not be.**

    Every test above reuses one `GraphView` object across all sixty
    rebinds. The harness does not: `state_at(t)` caches a distinct object
    per timestep, identical in content on a quiet step but a different
    object. A guard comparing object identity rather than state value
    therefore passes the entire unit suite and fixes nothing — found by
    mutation, and it collapsed to 5.17e-14 here while thirteen tests
    stayed green.

    So this runs the real path: real harness, real per-step views, static
    scenario, and asserts the swarm is still flying at the end.
    """
    from dynaswarm.config import BudgetCfg, Config, ExperimentCfg, ScenarioCfg
    from dynaswarm.harness.trial import run_trial

    cfg = Config(
        graph=GRAPH,
        scenario=ScenarioCfg(name="static", events_per_step=0.0, timesteps=60),
        experiment=ExperimentCfg(arms=["pso"], n_trials=1, eval_seeds=[seed]),
        budget=BudgetCfg(evaluations=300),
    )
    rows = run_trial(cfg, 0, ["pso"]).steps
    speed = dict(rows[-1].probe)["speed_mean"]
    assert speed > 1e-4, (
        f"seed {seed}: velocity collapsed to {speed:.3e} on a static run through "
        "the harness — the guard is comparing something other than state value"
    )
