"""Optimizer invariants: budget, parameter liveness, state handling.

Two families of test here carry disproportionate weight.

*Budget* tests establish that "equal allowance" means equal work.  If an
arm can overrun by finishing an iteration in progress, and the iteration
size is itself controller-tuned, then the controller can buy CPU and the
extra compute will be misread as a better search.

*Liveness* tests establish that every declared parameter actually
reaches the search.  A parameter that is recorded but never read looks
identical in a decision log to one doing useful work, so an inert
parameter would not merely be a bug — it would quietly invalidate any
claim about whether tuning helps.
"""

from __future__ import annotations

import numpy as np
import pytest

from dynaswarm.config import GraphCfg
from dynaswarm.core.generate import build
from dynaswarm.core.meter import EvaluationMeter
from dynaswarm.core.oracle import shortest_path
from dynaswarm.core.rng import stream
from dynaswarm.core.timeline import GraphTimeline, build_schedule
from dynaswarm.optimizers.aco import ACO
from dynaswarm.optimizers.astar import AStar
from dynaswarm.optimizers.protocol import Optimizer
from dynaswarm.optimizers.spec import ParamSpec, bind, clamp, defaults

GEO = GraphCfg(model="geometric", n_nodes=150, density=0.05)


def make_aco(cfg: GraphCfg = GEO, seed: int = 0, **params):
    view, source, target = build(cfg, stream(seed, "graph"))
    aco = ACO(view, source, target, stream(seed, "aco"), params or None)
    return aco, view, source, target


# ---------------------------------------------------------------------------
# Meter
# ---------------------------------------------------------------------------


def test_meter_tracks_and_exhausts():
    meter = EvaluationMeter(3)
    assert not meter.exhausted and meter.remaining == 3
    meter.charge(2)
    assert meter.remaining == 1 and not meter.exhausted
    meter.charge()
    assert meter.exhausted and meter.remaining == 0


def test_meter_rejects_negative_budget():
    with pytest.raises(ValueError, match="non-negative"):
        EvaluationMeter(-1)


# ---------------------------------------------------------------------------
# Budget — equal allowance must mean equal work
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("budget", [50, 300, 1000])
def test_budget_is_spent_exactly(budget: int):
    aco, *_ = make_aco()
    meter = EvaluationMeter(budget)
    aco.spend(meter)
    assert meter.spent == budget, "an arm must spend its allowance, no more and no less"


@pytest.mark.parametrize("n_ants", [4, 20, 100])
def test_colony_size_buys_no_extra_work(n_ants: int):
    """A larger colony must mean fewer iterations, not more compute.

    Were the budget denominated in iterations, this arm would do
    ``n_ants`` times the work of a small one for the same nominal
    allowance — and since colony size is tunable, the controller could
    award itself that advantage.
    """
    aco, *_ = make_aco(n_ants=n_ants)
    meter = EvaluationMeter(400)
    aco.spend(meter)
    assert meter.spent == 400


def test_every_construction_is_charged():
    """The counter must equal the number of path constructions.

    Metering anywhere other than inside the construction routine would
    leave a path by which work escapes the count.
    """
    aco, *_ = make_aco()
    calls = 0
    original = ACO._construct

    def counting(self, meter):
        nonlocal calls
        calls += 1
        return original(self, meter)

    ACO._construct = counting
    try:
        meter = EvaluationMeter(250)
        aco.spend(meter)
    finally:
        ACO._construct = original
    assert calls == meter.spent


def test_zero_budget_does_nothing():
    aco, *_ = make_aco()
    meter = EvaluationMeter(0)
    aco.spend(meter)
    assert meter.spent == 0 and aco.best() is None


# ---------------------------------------------------------------------------
# Parameter binding and liveness
# ---------------------------------------------------------------------------


def test_bind_clamps_and_completes():
    table = {"a": ParamSpec(1.0, 0.0, 2.0), "b": ParamSpec(5, 0, 10, integer=True)}
    out = bind(table, {"a": 99.0})
    assert out == {"a": 2.0, "b": 5}
    assert bind(table, {"b": 3.4})["b"] == 3


def test_bind_rejects_unknown_names():
    """A misspelled parameter must raise, not be absorbed silently."""
    with pytest.raises(KeyError, match="unknown parameter"):
        bind({"a": ParamSpec(1.0, 0.0, 2.0)}, {"alpha": 1.0})


def test_spec_rejects_incoherent_range():
    with pytest.raises(ValueError, match="exceeds"):
        ParamSpec(1.0, 5.0, 2.0)
    with pytest.raises(ValueError, match="outside"):
        ParamSpec(9.0, 0.0, 2.0)


def test_clamp_respects_integrality():
    assert clamp(ParamSpec(0, -10, 10, integer=True), 3.6) == 4
    assert clamp(ParamSpec(0.0, -1.0, 1.0), 3.6) == 1.0


def test_params_round_trip():
    aco, *_ = make_aco()
    aco.apply({"alpha": 2.5, "rho": 0.4})
    assert aco.params()["alpha"] == 2.5
    assert aco.params()["rho"] == 0.4
    assert set(aco.params()) == set(ACO.PARAM_SPEC), "params() must be total"


@pytest.mark.parametrize("param", sorted(ACO.PARAM_SPEC))
def test_every_parameter_changes_behaviour(param: str):
    """Drive each tunable to both bounds and require the search to differ.

    Parametrised straight off ``PARAM_SPEC``, so a newly declared
    parameter is covered the moment it is added and cannot be introduced
    inert.
    """
    spec = ACO.PARAM_SPEC[param]

    def trajectory(value: float) -> list[float]:
        aco, *_ = make_aco(**{param: value})
        costs = []
        for _ in range(6):
            aco.spend(EvaluationMeter(200))
            best = aco.best()
            costs.append(best.cost if best else float("inf"))
        return costs

    low, high = trajectory(spec.lo), trajectory(spec.hi)
    assert low != high, f"{param} at {spec.lo} and {spec.hi} produced identical searches"


def test_astar_rejects_parameters():
    view, source, target = build(GEO, stream(0, "graph"))
    astar = AStar(view, source, target)
    assert astar.params() == {}
    with pytest.raises(KeyError, match="no tunable"):
        astar.apply({"alpha": 1.0})


# ---------------------------------------------------------------------------
# A* — the quality reference
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cfg",
    [
        GraphCfg(),
        GraphCfg(model="geometric", n_nodes=150, density=0.05),
        GraphCfg(model="grid", n_nodes=400),
    ],
    ids=["erdos_renyi", "geometric", "grid"],
)
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_astar_is_exact_at_every_timestep(cfg: GraphCfg, seed: int):
    """A* must return the true optimum on every state of every model.

    Covering all three models matters: heuristic admissibility depends on
    weights and the heuristic sharing a metric, and a mismatch shows up
    only on the model whose metric differs and only once an event
    introduces an edge the lattice did not already have.  A single-model
    test would pass while A* silently returned suboptimal paths.
    """
    from dynaswarm.config import ScenarioCfg

    view, source, target = build(cfg, stream(seed, "graph"))
    sched = build_schedule(
        view, ScenarioCfg(events_per_step=0.8, timesteps=25), stream(seed, "events"), source, target
    )
    tl = GraphTimeline(view, sched)
    astar = AStar(view, source, target)

    for t in range(tl.timesteps):
        state = tl.state_at(t)
        astar.rebind(state)
        astar.spend(EvaluationMeter(300))
        truth, _, _ = shortest_path(state, source, target, heuristic=False)
        assert astar.best().cost == pytest.approx(truth), f"A* not exact at t={t}"


def test_astar_reports_recomputation_cost():
    view, source, target = build(GEO, stream(2, "graph"))
    astar = AStar(view, source, target)
    astar.spend(EvaluationMeter(1))
    assert astar.probe()["expansions"] > 0


# ---------------------------------------------------------------------------
# ACO behaviour
# ---------------------------------------------------------------------------


def test_aco_never_beats_the_optimum():
    """A cost below the true optimum means the cost model is wrong."""
    aco, view, source, target = make_aco()
    truth, _, _ = shortest_path(view, source, target, heuristic=True)
    for _ in range(6):
        aco.spend(EvaluationMeter(300))
        best = aco.best()
        if best is not None:
            assert best.cost >= truth - 1e-9
            assert view.path_cost(list(best.path)) == pytest.approx(best.cost)


def test_aco_improves_toward_the_optimum():
    aco, view, source, target = make_aco()
    truth, _, _ = shortest_path(view, source, target, heuristic=True)
    aco.spend(EvaluationMeter(200))
    early = aco.best().cost
    for _ in range(10):
        aco.spend(EvaluationMeter(300))
    late = aco.best().cost
    assert late <= early
    assert late / truth - 1 < 0.35, f"excess {late / truth - 1:.1%} suggests no convergence"


def test_trail_limits_bound_the_ratio():
    """MAX--MIN caps strongest-over-weakest at ``2n``, however long it runs.

    Without the bound the ratio grows without limit, every ant walks one
    path, and no evaporation setting can restore search — which would
    leave nothing for a controller to act on.
    """
    aco, view, _, _ = make_aco()
    for _ in range(15):
        aco.spend(EvaluationMeter(300))
    assert aco.probe()["tau_ratio"] <= 2.0 * view.n_nodes + 1e-6


def test_rebind_preserves_trails_but_reprices_the_best():
    aco, view, source, target = make_aco()
    for _ in range(4):
        aco.spend(EvaluationMeter(300))
    before = aco._tau.copy()
    incumbent = aco.best()

    heavier = np.array(view.weight) * 3.0
    mutated = view.with_state(heavier, view.active, t=1)
    aco.rebind(mutated)

    np.testing.assert_array_equal(
        aco._tau[np.asarray(mutated.active)], before[np.asarray(mutated.active)]
    )
    assert aco.best().cost == pytest.approx(incumbent.cost * 3.0)


def test_rebind_drops_a_best_path_that_no_longer_exists():
    aco, view, source, target = make_aco()
    for _ in range(4):
        aco.spend(EvaluationMeter(300))
    assert aco.best() is not None

    severed = view.with_state(view.weight, np.zeros_like(view.active), t=1)
    aco.rebind(severed)
    assert aco.best() is None


def test_reset_flattens_trails():
    aco, *_ = make_aco()
    for _ in range(8):
        aco.spend(EvaluationMeter(300))
    before = aco.probe()["tau_ratio"]
    aco.reset_learned_state(0.0)
    assert aco.probe()["tau_ratio"] == pytest.approx(before), "strength 0 must be a no-op"
    aco.reset_learned_state(1.0)
    assert aco.probe()["tau_ratio"] == pytest.approx(1.0), "strength 1 must erase differences"


def test_branching_measure_falls_as_the_colony_converges():
    """The stagnation signal must move in the direction it claims to."""
    aco, *_ = make_aco(rho=0.02, alpha=3.0)
    aco.spend(EvaluationMeter(300))
    early = aco.probe()["lambda_branch"]
    for _ in range(20):
        aco.spend(EvaluationMeter(300))
    late = aco.probe()["lambda_branch"]
    assert late <= early, f"branching rose ({early:.2f} -> {late:.2f}) while converging"
    assert late >= 1.0, "a visited node always retains at least one competitive arc"


def test_both_optimizers_satisfy_the_protocol():
    view, source, target = build(GEO, stream(0, "graph"))
    assert isinstance(AStar(view, source, target), Optimizer)
    assert isinstance(ACO(view, source, target, stream(0, "aco")), Optimizer)


def test_defaults_match_the_spec():
    assert defaults(ACO.PARAM_SPEC) == {n: s.default for n, s in ACO.PARAM_SPEC.items()}
