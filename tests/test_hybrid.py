"""Swarm and hybrid invariants.

The encoding is the design decision worth guarding here.  Any encoding
whose search space contains the exact optimum at a distinguished point
reduces the method to an exact solver in disguise, and would make every
comparison against it meaningless — so that is asserted against directly.
"""

from __future__ import annotations

import numpy as np
import pytest

from dynaswarm.config import BudgetCfg, Config, ControlCfg, ExperimentCfg, GraphCfg, ScenarioCfg
from dynaswarm.core.generate import build
from dynaswarm.core.meter import EvaluationMeter
from dynaswarm.core.oracle import shortest_path
from dynaswarm.core.rng import stream
from dynaswarm.harness.trial import run_trial
from dynaswarm.optimizers.hybrid import Hybrid
from dynaswarm.optimizers.protocol import Optimizer
from dynaswarm.optimizers.pso import PSO

GEO = GraphCfg(model="geometric", n_nodes=150, density=0.05)


def make(cls, cfg: GraphCfg = GEO, seed: int = 0, **params):
    view, source, target = build(cfg, stream(seed, "graph"))
    return cls(view, source, target, stream(seed, "search"), params or None), view, source, target


# ---------------------------------------------------------------------------
# PSO
# ---------------------------------------------------------------------------


def test_pso_satisfies_the_protocol():
    optimizer, *_ = make(PSO)
    assert isinstance(optimizer, Optimizer)


@pytest.mark.parametrize("budget", [50, 300])
def test_pso_spends_its_whole_allowance(budget: int):
    optimizer, *_ = make(PSO)
    meter = EvaluationMeter(budget)
    optimizer.spend(meter)
    assert meter.spent == budget


def test_repair_attempts_are_charged():
    """A swarm that repairs constantly is working, and must pay for it.

    Leaving repairs unmetered would let a high repair budget buy extra
    search that never appears in the accounting.
    """
    cheap, *_ = make(PSO, repair_attempts=0)
    costly, *_ = make(PSO, repair_attempts=10)
    for optimizer in (cheap, costly):
        meter = EvaluationMeter(400)
        optimizer.spend(meter)
        assert meter.spent == 400


def test_pso_never_beats_the_optimum():
    optimizer, view, source, target = make(PSO)
    truth, _, _ = shortest_path(view, source, target, heuristic=True)
    for _ in range(6):
        optimizer.spend(EvaluationMeter(300))
        best = optimizer.best()
        if best is not None:
            assert best.cost >= truth - 1e-9
            assert view.path_cost(list(best.path)) == pytest.approx(best.cost)


def test_pso_is_a_search_not_a_disguised_exact_solver():
    """No distinguished point in the search space may hold the answer.

    A bias-the-weights encoding fails this: its zero vector yields the
    exact shortest path, so a swarm containing it solves the problem on
    its first evaluation and measures nothing about swarm search.  With
    priorities there is no such point — uniform priorities give an
    arbitrary greedy walk, not the optimum.
    """
    optimizer, view, source, target = make(PSO)
    truth, _, _ = shortest_path(view, source, target, heuristic=True)

    # The canonical points a swarm is likely to hold or drift through.
    for name, priority in (
        ("uniform", np.full(view.n_nodes, 0.5)),
        ("zeros", np.zeros(view.n_nodes)),
        ("ones", np.ones(view.n_nodes)),
    ):
        result = optimizer._construct(priority, EvaluationMeter(10))
        # Dead-ending is an acceptable outcome and is itself evidence the
        # encoding is doing real work; handing back the optimum is not.
        if result is not None:
            assert result[1] > truth + 1e-9, (
                f"{name} priorities returned the optimum, so the encoding is "
                "an exact solver in disguise rather than a search"
            )


@pytest.mark.parametrize("param", sorted(PSO.PARAM_SPEC))
def test_every_pso_parameter_changes_behaviour(param: str):
    spec = PSO.PARAM_SPEC[param]

    def trajectory(value: float) -> list[float]:
        optimizer, *_ = make(PSO, **{param: value})
        costs = []
        for _ in range(5):
            optimizer.spend(EvaluationMeter(200))
            best = optimizer.best()
            costs.append(best.cost if best else float("inf"))
        return costs

    assert trajectory(spec.lo) != trajectory(spec.hi), f"{param} did nothing"


def test_rebind_keeps_priorities_but_drops_stale_costs():
    optimizer, view, source, target = make(PSO)
    for _ in range(4):
        optimizer.spend(EvaluationMeter(300))
    positions = optimizer._position.copy()

    heavier = np.array(view.weight) * 3.0
    optimizer.rebind(view.with_state(heavier, view.active, t=1))

    np.testing.assert_array_equal(optimizer._position, positions)
    assert np.isinf(optimizer._own_cost).all(), "remembered costs were priced on the old graph"


def test_diversity_falls_as_the_swarm_converges():
    optimizer, *_ = make(PSO, inertia=0.1, social=3.0)
    optimizer.spend(EvaluationMeter(300))
    early = optimizer.probe()["diversity"]
    for _ in range(15):
        optimizer.spend(EvaluationMeter(300))
    assert optimizer.probe()["diversity"] <= early


# ---------------------------------------------------------------------------
# Hybrid
# ---------------------------------------------------------------------------


def test_hybrid_satisfies_the_protocol():
    optimizer, *_ = make(Hybrid)
    assert isinstance(optimizer, Optimizer)


def test_hybrid_exposes_both_components_parameters():
    assert "aco_rho" in Hybrid.PARAM_SPEC
    assert "pso_inertia" in Hybrid.PARAM_SPEC
    assert "aco_fraction" in Hybrid.PARAM_SPEC


@pytest.mark.parametrize("fraction", [0.1, 0.5, 0.9])
def test_the_split_buys_no_extra_work(fraction: float):
    """Shifting the budget between components must not create budget."""
    optimizer, *_ = make(Hybrid, aco_fraction=fraction)
    meter = EvaluationMeter(400)
    optimizer.spend(meter)
    assert meter.spent == pytest.approx(400, abs=2)


def test_the_split_actually_moves_work_between_components():
    colony_heavy, *_ = make(Hybrid, aco_fraction=0.9)
    swarm_heavy, *_ = make(Hybrid, aco_fraction=0.1)
    for optimizer in (colony_heavy, swarm_heavy):
        optimizer.spend(EvaluationMeter(400))

    assert (
        colony_heavy._aco.probe()["iterations"] > swarm_heavy._aco.probe()["iterations"]
    ), "a larger colony share should buy the colony more iterations"


def test_hybrid_never_beats_the_optimum():
    optimizer, view, source, target = make(Hybrid)
    truth, _, _ = shortest_path(view, source, target, heuristic=True)
    for _ in range(5):
        optimizer.spend(EvaluationMeter(300))
        best = optimizer.best()
        if best is not None:
            assert best.cost >= truth - 1e-9


def test_hybrid_reports_the_better_of_its_components():
    optimizer, *_ = make(Hybrid)
    for _ in range(5):
        optimizer.spend(EvaluationMeter(300))
    parts = [s.cost for s in (optimizer._aco.best(), optimizer._pso.best()) if s]
    assert optimizer.best().cost == pytest.approx(min(parts))


def test_components_exchange_information():
    optimizer, *_ = make(Hybrid)
    optimizer.spend(EvaluationMeter(300))
    assert optimizer.probe()["exchanges"] > 0


# ---------------------------------------------------------------------------
# The allocation ablation
# ---------------------------------------------------------------------------


def test_allocation_arms_share_a_stream_and_differ_only_by_control():
    cfg = Config(
        graph=GraphCfg(n_nodes=30, density=0.3),
        scenario=ScenarioCfg(name="t", events_per_step=0.8, timesteps=25),
        experiment=ExperimentCfg(n_trials=1),
        budget=BudgetCfg(evaluations=200),
        control=ControlCfg(signal="recency", targets=["aco_fraction"], sigma=0.02),
    )
    outcome = run_trial(cfg, 0, ["hybrid_fixed", "hybrid_adaptive"])

    fixed = [r for r in outcome.steps if r.arm == "hybrid_fixed"]
    adaptive = [r for r in outcome.steps if r.arm == "hybrid_adaptive"]

    assert fixed[0].best_cost == adaptive[0].best_cost, "the arms must start together"
    assert len({r.params["aco_fraction"] for r in fixed}) == 1, "the frozen arm must not move"
    assert len({r.params["aco_fraction"] for r in adaptive}) > 1, (
        "the adaptive arm must actually shift its allocation"
    )


def test_recency_peaks_on_disruption_and_decays():
    """The transient signal must be largest when memory is least reliable."""
    cfg = Config(
        graph=GraphCfg(n_nodes=30, density=0.3),
        scenario=ScenarioCfg(name="t", events_per_step=0.3, timesteps=40),
        experiment=ExperimentCfg(n_trials=1),
        budget=BudgetCfg(evaluations=150),
        # A hybrid's parameters are `aco_`/`pso_`-prefixed, so the default
        # targets=["rho"] names nothing it declares.  That used to be
        # silently dropped (F2) and now raises, so the target is named.
        control=ControlCfg(signal="recency", targets=["aco_fraction"]),
    )
    rows = run_trial(cfg, 0, ["hybrid_adaptive"]).steps
    disturbed = [r.signal_value for r in rows if r.num_events > 0]
    quiet_runs = [r.signal_value for r in rows if r.num_events == 0]

    assert disturbed and all(v == pytest.approx(1.0) for v in disturbed)
    assert min(quiet_runs) < 1.0, "the signal must decay through calm"
