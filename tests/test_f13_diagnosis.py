"""F13's diagnosis, pinned.

Segment 17 diagnoses and does not fix. What is pinned here is the
*finding*, so that segment 18 builds against a measured fact and so that
the fact fails loudly if it stops being true.

The headline: **F13's premise is wrong.** The collapse is not specific to
a disrupted run. It is caused by `PSO.rebind` invalidating every
particle's personal-best cost, and the harness calls `rebind` on every
arm at every timestep whether or not the graph changed.
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


def _fly(mode: str, steps: int = 60, seed: int = 1000) -> tuple[float, float]:
    """Run a swarm on an unchanging graph, optionally wiping memory."""
    view, source, target = build(GRAPH, stream(seed, "graph"))
    swarm = PSO(view, source, target, stream(seed, "pso"), {})
    for _ in range(steps):
        if mode == "rebind":
            swarm.rebind(view)              # the SAME view — nothing changed
        elif mode == "wipe":
            swarm._own_cost[:] = np.inf     # only the memory invalidation
        elif mode == "rest":
            swarm._refresh_visibility()
            swarm._sync_lists()
            swarm._revalidate_best()
        swarm.spend(EvaluationMeter(300))
    return (
        float(np.abs(swarm._velocity).mean()),
        float(np.mean(np.std(swarm._position, axis=0))),
    )


def test_the_velocity_decomposition_reconstructs_the_real_update():
    """Three terms that do not add up to the thing they explain are
    measuring something else.

    Asserted against the velocity the mechanism actually stores, not
    against the sum of the coefficients that produced it.
    """
    view, source, target = build(GRAPH, stream(1000, "graph"))
    swarm = PSO(view, source, target, stream(1000, "pso"), {})
    swarm.spend(EvaluationMeter(300))

    i = 0
    r1, r2 = swarm._uniform(), swarm._uniform()
    inertia = swarm._p["inertia"] * swarm._velocity[i]
    cognitive = swarm._p["cognitive"] * r1 * (swarm._own_best[i] - swarm._position[i])
    social = swarm._p["social"] * r2 * (swarm._swarm_best - swarm._position[i])
    expected = inertia + cognitive + social

    # Replay the same draws through the real mechanism.
    swarm._uniform = lambda _values=iter((r1, r2)): next(_values)
    swarm._move(i)
    assert np.allclose(swarm._velocity[i], expected), (
        "the decomposition does not reconstruct the velocity it claims to explain"
    )


def test_the_collapse_is_caused_by_rebind_not_by_disruption():
    """**F13's premise, falsified.**

    Same graph, same seed, nothing changing. Calling `rebind` each step
    collapses velocity by six orders of magnitude; not calling it leaves
    the swarm flying. Disruption is not the variable.
    """
    quiet_v, quiet_d = _fly("none")
    rebound_v, rebound_d = _fly("rebind")

    assert quiet_v > 1e-3, f"the healthy baseline did not reproduce: {quiet_v:.3e}"
    assert rebound_v < quiet_v / 1e4, (
        f"rebind did not collapse the swarm: {rebound_v:.3e} against {quiet_v:.3e}"
    )
    assert rebound_d < quiet_d / 1e3, "diversity survived a collapse it should not have"


def test_the_cause_is_the_personal_best_invalidation_alone():
    """Isolated to one line: `self._own_cost[:] = np.inf`.

    `rebind` also refreshes visibility, re-syncs lists and re-prices the
    global best. Those three together leave the swarm exactly as healthy
    as no rebind at all; the cost wipe alone reproduces the collapse
    exactly.
    """
    baseline = _fly("none")
    wipe_only = _fly("wipe")
    rest_only = _fly("rest")
    full = _fly("rebind")

    assert wipe_only == pytest.approx(full, rel=1e-9), (
        "the memory wipe does not account for the whole effect"
    )
    assert rest_only == pytest.approx(baseline, rel=1e-9), (
        "something other than the wipe also contributes"
    )


def test_rebind_is_called_on_every_step_not_only_on_change():
    """The fact that turns a correct policy into a defect.

    Invalidating costs measured against a graph that no longer exists is
    right. Doing it when the graph did not change discards the swarm's
    memory for nothing — and the harness does not check.
    """
    source = (
        __import__("pathlib").Path(__file__).resolve().parents[1]
        / "src" / "dynaswarm" / "harness" / "trial.py"
    ).read_text()
    call = "arm.optimizer.rebind(state)"
    assert call in source
    before = source[: source.index(call)]
    tail = before.rsplit("for arm in arms:", 1)[-1]
    assert "if" not in tail, (
        "rebind now appears to be conditional; the diagnosis needs revisiting"
    )


@pytest.mark.parametrize("seed", [1000, 1001, 1002, 7, 42, 9999])
def test_the_collapse_reproduces_across_seeds(seed):
    """A diagnosis resting on one seed is an anecdote.

    Every test above ran on seed 1000 alone, and a defect that happened
    to be seed-specific would have passed all of them while the finding
    written up beside them was wrong. Six seeds, ratios from 5.7e5 to
    5.4e11 — and seed 1000 is the *weakest* of them, so the single-seed
    diagnosis was conservative rather than lucky. Which is luck.
    """
    quiet, _ = _fly("none", seed=seed)
    rebound, _ = _fly("rebind", seed=seed)
    assert quiet > 1e-4, f"seed {seed} had no healthy baseline: {quiet:.3e}"
    assert rebound < quiet / 1e4, (
        f"seed {seed}: rebind did not collapse the swarm "
        f"({rebound:.3e} against {quiet:.3e})"
    )
