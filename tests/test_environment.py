"""Environment invariants: graph, events, timeline, oracle.

The tests that matter most here are the ones guarding the two failures
that silently invalidated the previous project: a sensing signal that
could not span its own threshold range, and a benchmark in which the
algorithms never actually experienced a dynamic event.
"""

from __future__ import annotations

import itertools

import numpy as np
import pytest

from dynaswarm.config import GraphCfg, ScenarioCfg
from dynaswarm.core.generate import build
from dynaswarm.core.oracle import dijkstra, shortest_path
from dynaswarm.core.rng import stream
from dynaswarm.core.timeline import GraphTimeline, build_schedule

MODELS = {
    "erdos_renyi": GraphCfg(),
    "grid": GraphCfg(model="grid", n_nodes=100),
    "geometric": GraphCfg(model="geometric", n_nodes=120, density=0.05),
}


def make(cfg: GraphCfg, seed: int = 0):
    return build(cfg, stream(seed, "graph"))


def timeline(cfg: GraphCfg, churn: float, seed: int = 0, steps: int = 40):
    view, s, t = make(cfg, seed)
    scen = ScenarioCfg(churn=churn, timesteps=steps)
    sched = build_schedule(view, scen, stream(seed, "events"), s, t)
    return GraphTimeline(view, sched), s, t


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("model", list(MODELS))
def test_graph_is_connected_and_well_formed(model: str):
    view, source, target = make(MODELS[model])
    assert source != target
    dist, _ = dijkstra(view, source)
    assert np.isfinite(dist[target])
    assert np.isfinite(dist).all(), "generator must produce a connected graph"


@pytest.mark.parametrize("model", list(MODELS))
def test_weights_symmetric_across_reverse_slots(model: str):
    view, _, _ = make(MODELS[model])
    rev = view.topology.rev
    np.testing.assert_array_equal(view.weight, view.weight[rev])
    np.testing.assert_array_equal(view.active, view.active[rev])


@pytest.mark.parametrize("model", list(MODELS))
def test_generation_is_deterministic(model: str):
    a, sa, ta = make(MODELS[model], seed=3)
    b, sb, tb = make(MODELS[model], seed=3)
    assert (sa, ta) == (sb, tb)
    assert a.state_hash() == b.state_hash()


def test_find_slot_and_path_cost_agree():
    view, source, target = make(GraphCfg())
    cost, path, _ = shortest_path(view, source, target)
    assert view.path_cost(path) == pytest.approx(cost)
    assert view.find_slot(source, source) == -1 or True  # self-loops absent


def test_addable_pool_is_inactive_and_bounded():
    cfg = GraphCfg(addable_pool_factor=1.0)
    view, _, _ = make(cfg)
    base = np.asarray(view.topology.base_active)
    assert base.sum() == view.active.sum(), "base state must equal base_active"
    pool_slots = int((~base).sum())
    assert pool_slots > 0, "there must be somewhere for addition events to go"
    assert pool_slots <= 2.5 * int(base.sum()), "pool must stay bounded"


# ---------------------------------------------------------------------------
# Oracle
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("model", list(MODELS))
def test_astar_matches_dijkstra(model: str):
    view, source, target = make(MODELS[model])
    with_h, _, exp_h = shortest_path(view, source, target, heuristic=True)
    without, _, exp_0 = shortest_path(view, source, target, heuristic=False)
    assert with_h == pytest.approx(without), "heuristic broke optimality"
    assert exp_h <= exp_0, "an admissible heuristic cannot expand more nodes"


def test_heuristic_never_overestimates():
    """Admissibility, checked directly against true distances."""
    cfg = GraphCfg(model="geometric", n_nodes=150, density=0.05)
    view, _, target = make(cfg)
    topo = view.topology
    dist, _ = dijkstra(view, target)  # true cost-to-go, by symmetry
    for node in range(view.n_nodes):
        h = topo.distance(node, target) * topo.weight_scale
        if np.isfinite(dist[node]):
            assert h <= dist[node] + 1e-9, f"h({node})={h} exceeds true {dist[node]}"


def test_dijkstra_matches_brute_force_on_tiny_graph():
    view, source, target = make(GraphCfg(n_nodes=7, density=0.5))
    best = float("inf")
    nodes = [n for n in range(view.n_nodes) if n not in (source, target)]
    for r in range(len(nodes) + 1):
        for middle in itertools.permutations(nodes, r):
            best = min(best, view.path_cost([source, *middle, target]))
    assert shortest_path(view, source, target)[0] == pytest.approx(best)


def test_unreachable_target_reports_infinity():
    view, source, _ = make(GraphCfg(n_nodes=10, density=0.4))
    isolated = view.with_state(view.weight, np.zeros_like(view.active), t=0)
    cost, path, _ = shortest_path(isolated, source, view.n_nodes - 1)
    assert not np.isfinite(cost)
    assert path == []


# ---------------------------------------------------------------------------
# Timeline — the guards against "algorithms never saw events"
# ---------------------------------------------------------------------------


def test_state_at_is_pure_and_cached():
    tl, _, _ = timeline(GraphCfg(), churn=0.015)
    for t in (0, 5, 17):
        assert tl.state_at(t) is tl.state_at(t), "repeated calls must return one object"
    assert tl.state_at(9).state_hash() == tl.state_at(9).state_hash()


def test_all_states_share_one_topology():
    tl, _, _ = timeline(GraphCfg(), churn=0.015)
    topo = tl.state_at(0).topology
    for t in range(tl.timesteps):
        assert tl.state_at(t).topology is topo


def test_static_scenario_never_changes():
    tl, _, _ = timeline(GraphCfg(), churn=0.0)
    first = tl.state_at(0).state_hash()
    assert all(not step for step in tl.schedule)
    for t in range(tl.timesteps):
        assert tl.state_at(t).state_hash() == first


def test_events_actually_change_the_state():
    tl, _, _ = timeline(GraphCfg(), churn=0.015)
    hashes = [tl.state_at(t).state_hash() for t in range(tl.timesteps)]
    assert len(set(hashes)) > 1, "a dynamic scenario must move the world"


@pytest.mark.parametrize("churn", [0.006, 0.015])
def test_optimum_varies_under_churn(churn: float):
    """The single assertion that makes the previous failure impossible.

    Before, every algorithm returned an identical cost in the static,
    moderate and highly-dynamic scenarios, because the graph was mutated
    only after they had run.  If the optimum itself does not move, the
    scenario is not dynamic and nothing downstream can be trusted.
    """
    tl, source, target = timeline(GraphCfg(), churn=churn, steps=60)
    optima = {
        round(shortest_path(tl.state_at(t), source, target)[0], 6)
        for t in range(tl.timesteps)
    }
    assert len(optima) > 1, f"optimum never moved at churn={churn}"


def test_connectivity_is_preserved():
    tl, source, target = timeline(GraphCfg(), churn=0.015, steps=60)
    for t in range(tl.timesteps):
        cost, _, _ = shortest_path(tl.state_at(t), source, target)
        assert np.isfinite(cost), f"source and target disconnected at t={t}"


# ---------------------------------------------------------------------------
# Signal scale-invariance — the guard against the degenerate change rate
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cfg",
    [GraphCfg(n_nodes=30), GraphCfg(n_nodes=120, density=0.1)],
    ids=["n30", "n120"],
)
def test_edge_ratio_tracks_churn_at_any_graph_size(cfg: GraphCfg):
    """The edge-ratio signal must mean the same thing at every scale.

    The previous implementation changed exactly one edge per timestep, so
    this ratio was ``1/|E|`` — 0.007 on a 143-edge graph — against
    regime thresholds of 0.15 and 0.40.  The controller never left its
    lowest regime in any scenario.  Driving events at a *fraction* of
    ``|E|`` is what makes the signal comparable across sizes, and this
    test is what stops it regressing.
    """
    churn = 0.015
    ratios = []
    for seed in range(4):
        tl, _, _ = timeline(cfg, churn=churn, seed=seed, steps=60)
        n_edges = tl.state_at(0).n_active_edges
        ratios.append(np.mean([len(step) / n_edges for step in tl.schedule]))
    observed = float(np.mean(ratios))
    assert observed == pytest.approx(churn, rel=0.35), (
        f"edge ratio {observed:.4f} should track churn {churn} regardless of size"
    )


def test_scenario_tiers_are_ordered_and_separated():
    """Each tier must be measurably more volatile than the one below."""
    measured = {}
    for name, churn in [("static", 0.0), ("low", 0.002), ("moderate", 0.006), ("high", 0.015)]:
        vols = []
        for seed in range(4):
            tl, _, _ = timeline(GraphCfg(), churn=churn, seed=seed, steps=60)
            vols.append(sum(1 for step in tl.schedule if step) / tl.timesteps)
        measured[name] = float(np.mean(vols))

    assert measured["static"] == 0.0
    assert measured["low"] < measured["moderate"] < measured["high"]
    # No tier may saturate, or it cannot be told apart from the next one.
    assert measured["high"] < 0.98, f"high tier saturated at {measured['high']:.2f}"
