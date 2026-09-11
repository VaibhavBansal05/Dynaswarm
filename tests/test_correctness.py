"""Correctness against arithmetic, not against plausible outcomes.

**Every expected value here is computed independently of the
implementation** — from the published definition, by a few lines written
for the purpose, never by running the code and recording what it did.

A test whose expectation came from the code is a change-detector. It
passes forever, including on the day the code was wrong from the start,
and it is the defect this project has now caught in six costumes: a
threshold taken from the state being replaced, an invariant asserted
only against correct data, a ledger reconciled against its own
arithmetic, a guarantee tested by data in which nothing fails, a probe
counting the need for a mechanism rather than its effect, and a fixture
that differed from production in the one dimension under test.

Each check names where its expected number came from.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from dynaswarm.config import GraphCfg
from dynaswarm.core.generate import build
from dynaswarm.core.oracle import shortest_path
from dynaswarm.core.rng import stream

# ---------------------------------------------------------------------------
# The independent reference: the definition of a shortest path
# ---------------------------------------------------------------------------


def edges_of(view) -> dict[tuple[int, int], float]:
    """Every active undirected edge and its weight, read off the CSR."""
    topo = view.topology
    active = np.asarray(view.active)
    out: dict[tuple[int, int], float] = {}
    for u in range(topo.n_nodes):
        for slot in range(int(topo.indptr[u]), int(topo.indptr[u + 1])):
            if not active[slot]:
                continue
            v = int(topo.indices[slot])
            key = (min(u, v), max(u, v))
            out[key] = float(view.weight[slot])
    return out


def brute_force(view, source: int, target: int) -> float:
    """Enumerate every simple path and take the cheapest.

    **This is the definition**, not an algorithm borrowed from the code:
    a shortest path is the minimum total weight over all simple paths.
    No heap, no relaxation, no heuristic — nothing A* and this could get
    wrong in the same way.

    Returns ``inf`` when the target is unreachable.
    """
    adjacency: dict[int, list[tuple[int, float]]] = {}
    for (u, v), w in edges_of(view).items():
        adjacency.setdefault(u, []).append((v, w))
        adjacency.setdefault(v, []).append((u, w))

    best = math.inf

    def walk(node: int, seen: frozenset[int], cost: float) -> None:
        nonlocal best
        if cost >= best:
            return
        if node == target:
            best = cost
            return
        for nxt, w in adjacency.get(node, ()):
            if nxt not in seen:
                walk(nxt, seen | {nxt}, cost + w)

    walk(source, frozenset({source}), 0.0)
    return best


def with_edges(view, prices: dict[tuple[int, int], float]):
    """A view with these undirected edges set to these weights, **and active.**

    The activation is the point. `find_slot` returns a slot whether or
    not it is live, so setting a weight on an inactive slot builds a
    fixture whose intended route does not exist — which is exactly what
    happened on the first attempt here, and it read as A* returning a
    suboptimal answer rather than as a broken fixture.
    """
    topo = view.topology
    weights = np.array(view.weight, dtype=np.float64)
    active = np.asarray(view.active).copy()
    for (u, v), price in prices.items():
        slot = view.find_slot(u, v)
        assert slot >= 0, f"the fixture graph has no slot for {u}-{v}"
        for s in (slot, int(topo.rev[slot])):
            weights[s] = price
            active[s] = True
    return view.with_state(weights, active, view.t)


def tiny(seed: int, n_nodes: int = 9, density: float = 0.35, model: str = "erdos_renyi"):
    """A graph small enough to enumerate exhaustively.

    `model` matters more than it looks. On `erdos_renyi` the topology
    carries no coordinates and `weight_scale` is 0, so A*'s heuristic is
    **identically zero** and the search degenerates to Dijkstra. The
    first version of this file ran every A* check on such graphs, which
    meant doubling the heuristic — making it inadmissible, the one way
    A* can silently return a suboptimal answer — changed nothing and was
    not caught. `geometric` gives it a live heuristic.
    """
    cfg = GraphCfg(model=model, n_nodes=n_nodes, density=density)
    return build(cfg, stream(seed, "graph"))


# ---------------------------------------------------------------------------
# T1 — A*, held to the highest standard
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("model", ["erdos_renyi", "geometric"])
@pytest.mark.parametrize("seed", range(8))
def test_astar_equals_exhaustive_enumeration(seed, model):
    """Everything in this project is measured against A*.

    Excess is defined relative to it, Claim 1 compares excesses, and the
    dashboard draws its answer as the truth. The existing check compared
    `heuristic=True` against `heuristic=False` — real, but two
    implementations sharing one codebase and one set of assumptions.

    Expected value: **enumeration of every simple path**, the definition.
    """
    view, source, target = tiny(seed, model=model)
    expected = brute_force(view, source, target)
    got, path, _ = shortest_path(view, source, target, heuristic=True)

    if math.isinf(expected):
        assert not np.isfinite(got), "A* found a route where none exists"
        return
    assert got == pytest.approx(expected, rel=1e-12), (
        f"{model} seed {seed}: A* says {got}, enumeration says {expected}"
    )
    # The returned path must also be a real walk costing what was quoted.
    weights = edges_of(view)
    walked = sum(
        weights[(min(a, b), max(a, b))] for a, b in zip(path, path[1:], strict=False)
    )
    assert walked == pytest.approx(got, rel=1e-12), "the path does not cost what A* said"


def test_astar_is_right_when_the_cheapest_route_is_not_the_shortest():
    """A heuristic that over-weighted distance would fail exactly here.

    Built by hand: a two-hop route priced above a three-hop one, so hop
    count and cost disagree. Expected value worked out on paper —
    1 + 1 + 1 = 3 beats 10.
    """
    bent = with_edges(tiny(0, n_nodes=8, density=0.9)[0],
                      # direct 0-3 expensive; the 0-1-2-3 chain cheap
                      {(0, 3): 10.0, (0, 1): 1.0, (1, 2): 1.0, (2, 3): 1.0})

    cost, path, _ = shortest_path(bent, 0, 3, heuristic=True)
    assert cost == pytest.approx(3.0), f"expected 3.0 by hand, got {cost}"
    assert len(path) - 1 == 3, f"took the expensive short route: {path}"
    assert brute_force(bent, 0, 3) == pytest.approx(3.0)


def test_astar_reports_unreachable_rather_than_guessing():
    """Expected value: infinity, because no path exists by construction."""
    view, source, target = tiny(3)
    active = np.asarray(view.active).copy()
    topo = view.topology
    for slot in range(int(topo.indptr[target]), int(topo.indptr[target + 1])):
        active[slot] = False
        active[int(topo.rev[slot])] = False
    cut = view.with_state(np.asarray(view.weight), active, view.t)

    assert math.isinf(brute_force(cut, source, target)), "the fixture did not isolate it"
    cost, path, _ = shortest_path(cut, source, target, heuristic=True)
    assert not np.isfinite(cost)
    assert path == [], "a path was returned to an unreachable target"


def test_astar_ties_resolve_to_a_real_path_of_the_tied_cost():
    """Two distinct routes of identical cost.

    Which one is returned is not specified, so it is not asserted. What
    must hold is that the answer costs the tied amount and is a genuine
    walk — a tie-break bug that returned a blended path would fail here.
    """
    tied = with_edges(tiny(1, n_nodes=8, density=0.9)[0], {
        (0, 1): 1.0, (1, 4): 1.0,   # route A, cost 2
        (0, 2): 1.0, (2, 4): 1.0,   # route B, cost 2
        (0, 4): 5.0,                # direct, deliberately worse
    })

    cost, path, _ = shortest_path(tied, 0, 4, heuristic=True)
    assert cost == pytest.approx(2.0), f"expected the tied cost 2.0, got {cost}"
    assert path in ([0, 1, 4], [0, 2, 4]), f"not one of the two tied routes: {path}"


@pytest.mark.parametrize("seed", [5, 11])
def test_astar_is_still_exact_partway_through_a_timeline(seed):
    """The moving optimum is what excess is measured against.

    Checked at a state produced by real events, not only at t=0.
    """
    from dynaswarm.config import ScenarioCfg
    from dynaswarm.core.timeline import GraphTimeline, build_schedule

    view, source, target = tiny(seed, model="geometric", density=0.5)
    schedule = build_schedule(
        view, ScenarioCfg(name="c", events_per_step=0.8, timesteps=12, cluster_size=2),
        stream(seed, "events"), source, target,
    )
    timeline = GraphTimeline(view, schedule)

    for t in (3, 7, 11):
        state = timeline.state_at(t)
        expected = brute_force(state, source, target)
        got, _, _ = shortest_path(state, source, target, heuristic=True)
        if math.isinf(expected):
            assert not np.isfinite(got), f"t={t}: A* found a route where none exists"
        else:
            assert got == pytest.approx(expected, rel=1e-12), (
                f"seed {seed} t={t}: A* {got} against enumeration {expected}"
            )


# ---------------------------------------------------------------------------
# T2 — ACO's arithmetic against §5.2's formulas
# ---------------------------------------------------------------------------


def _colony(view, source, target, seed=1000, params=None):
    from dynaswarm.optimizers.aco import ACO

    return ACO(view, source, target, stream(seed, "aco"), params or {})


def test_aco_choice_frequencies_match_the_formula():
    """§5.2: p(edge) proportional to tau**alpha * eta**beta, normalised.

    Expected values from that formula by hand: with alpha=1, beta=0 and
    trails of 1, 2, 3 on the source's three live edges, the shares are
    exactly 1/6, 2/6, 3/6.

    **Sampled from `_construct` itself.** The first version of this test
    re-implemented the selection loop inside the test and sampled that —
    so it compared a formula against a copy of the code and never ran
    the code at all. Changing the real exponent from `alpha` to
    `alpha + 1` left it green. That is the precise circularity this
    segment exists to prevent, committed while writing the segment
    about it.
    """
    from dynaswarm.core.meter import EvaluationMeter

    view, source, _ = tiny(2, n_nodes=9, density=0.9)
    topo = view.topology
    active = np.asarray(view.active)

    slots = [
        s for s in range(int(topo.indptr[source]), int(topo.indptr[source + 1]))
        if active[s]
    ][:3]
    assert len(slots) == 3, "the fixture source does not have three live edges"
    first_hop = [int(topo.indices[s]) for s in slots]

    # Every other edge out of the source is closed, so the ant's first
    # hop is a choice between exactly these three and the sampled
    # frequencies are directly comparable to the formula.
    closed = active.copy()
    for s in range(int(topo.indptr[source]), int(topo.indptr[source + 1])):
        if s not in slots:
            closed[s] = False
            closed[int(topo.rev[s])] = False
    graph = view.with_state(np.asarray(view.weight), closed, view.t)

    colony = _colony(graph, source, first_hop[0], params={"alpha": 1.0, "beta": 0.0})
    colony._tau[:] = 0.0
    colony._eta[:] = 1.0
    for tau, s in zip((1.0, 2.0, 3.0), slots, strict=True):
        colony._tau[s] = tau
        colony._tau[int(topo.rev[s])] = tau
    colony._sync_lists()

    expected = dict(zip(first_hop, (1 / 6, 2 / 6, 3 / 6), strict=True))

    draws, seen = 6000, dict.fromkeys(first_hop, 0)
    for _ in range(draws):
        built = colony._construct(EvaluationMeter(2))
        if built is None:
            continue
        seen[built[0][1]] += 1
    total = sum(seen.values())
    assert total > draws * 0.5, "too few ants completed a first hop to measure"

    # Tolerance from the sample size: se of a proportion at n>=3000 is at
    # most 0.5/sqrt(n) ~= 0.009, so 4 sigma is ~0.037.
    for node, want in expected.items():
        got = seen[node] / total
        assert abs(got - want) < 0.037, (
            f"node {node}: formula says {want:.3f}, {total} ants gave {got:.3f}"
        )


def test_evaporation_is_exactly_tau_times_one_minus_rho():
    """§5.2. Expected value: multiplication, computed here, not observed."""
    view, source, target = tiny(4)
    colony = _colony(view, source, target, params={"rho": 0.25})
    colony._tau[:] = 0.0
    colony._tau[:8] = np.array([1.0, 2.0, 4.0, 8.0, 0.5, 0.25, 3.0, 7.0])
    before = colony._tau.copy()

    colony._evaporate()

    expected = before * (1.0 - 0.25)
    assert np.allclose(colony._tau, expected, rtol=0, atol=1e-15), (
        "evaporation is not tau * (1 - rho)"
    )


def test_deposit_lands_on_exactly_the_edges_of_the_best_path():
    """**The gap Phase 2's trust report says it cannot see.**

    It states outright that `tau_deposited` *"cannot detect deposit on
    the WRONG edges; the count is identical either way."* On a small
    graph every edge can be checked, so it is checked here.

    Expected value: §5.2's deposit is `1 / cost` added to each slot of
    the path and its reverse, and **nothing anywhere else**.
    """
    view, _, _ = tiny(6, n_nodes=9, density=0.9)
    graph = with_edges(view, {(0, 1): 2.0, (1, 2): 3.0})
    colony = _colony(graph, 0, 2)
    colony._tau[:] = 0.0

    path, cost = [0, 1, 2], 5.0
    colony._deposit(path, cost)

    amount = 1.0 / cost
    topo = graph.topology
    expected = np.zeros_like(colony._tau)
    for a, b in ((0, 1), (1, 2)):
        s = graph.find_slot(a, b)
        expected[s] += amount
        expected[int(topo.rev[s])] += amount

    assert np.allclose(colony._tau, expected, rtol=0, atol=1e-15), (
        "deposit did not land on exactly the path's edges"
    )
    off_path = colony._tau[expected == 0.0]
    assert not off_path.any(), (
        f"{int((off_path != 0).sum())} slots off the path received trail"
    )


def test_the_maxmin_bounds_are_the_values_the_formula_gives():
    """§5.2: `tau_max = 1/(rho * C_best)` and `tau_min = tau_max/(2n)`.

    Expected values computed from those two expressions here, with
    rho and C_best chosen so the arithmetic is checkable by eye:
    rho=0.5, C_best=4 gives tau_max = 0.5 exactly.
    """
    from dynaswarm.optimizers.aco import Solution

    view, source, target = tiny(8)
    colony = _colony(view, source, target, params={"rho": 0.5})
    colony._best = Solution(4.0, (source, target))

    tau_max = 1.0 / (0.5 * 4.0)                      # = 0.5
    tau_min = tau_max / (2.0 * max(view.n_nodes, 2))
    assert tau_max == 0.5, "the hand arithmetic is wrong, not the code"

    # Every live slot pushed outside both bounds, so the clamp must move
    # each one to a specific value rather than merely into a range. The
    # first version asserted `min >= tau_min`, which a WIDER floor also
    # satisfies — changing tau_min from tau_max/(2n) to tau_max/n left
    # it green.
    active = np.asarray(view.active)
    live = np.flatnonzero(active)
    assert live.size >= 2, "the fixture has too few live slots"
    colony._tau[:] = 0.0
    colony._tau[live[0::2]] = 99.0      # above tau_max
    colony._tau[live[1::2]] = -5.0      # below tau_min
    colony._clamp_trails()

    assert colony._tau[live[0::2]] == pytest.approx(tau_max), (
        f"trails above the ceiling were not clamped to exactly {tau_max}"
    )
    assert colony._tau[live[1::2]] == pytest.approx(tau_min), (
        f"trails below the floor were not clamped to exactly {tau_min}"
    )


# ---------------------------------------------------------------------------
# T3 — PSO's decoding is deterministic, so it is checked exactly
# ---------------------------------------------------------------------------


def _swarm(view, source, target, seed=1000, params=None):
    from dynaswarm.optimizers.pso import PSO

    return PSO(view, source, target, stream(seed, "pso"), params or {})


def _uniform_graph(seed, n_nodes=9, density=0.9, price=1.0):
    """Every live edge the same weight, so visibility cannot break ties.

    The decoder scores a neighbour as `priority * eta`, and eta derives
    from weight. Holding weight constant isolates the priority ordering,
    which is the thing under test.
    """
    view, source, target = tiny(seed, n_nodes=n_nodes, density=density)
    weights = np.full_like(np.asarray(view.weight, dtype=np.float64), price)
    return view.with_state(weights, np.asarray(view.active), view.t), source, target


def test_the_decoder_follows_the_priority_order_by_hand():
    """Given a priority vector, the route is fully determined.

    Expected route worked out here by walking the adjacency myself and
    taking the highest-priority unvisited neighbour at each step — not
    by running the decoder and recording where it went.
    """
    from dynaswarm.core.meter import EvaluationMeter

    view, source, target = _uniform_graph(2)
    swarm = _swarm(view, source, target)

    rng = np.random.default_rng(0)
    priority = rng.random(view.n_nodes)

    # Independent walk: pure priority-greedy over live, unvisited edges.
    topo, active = view.topology, np.asarray(view.active)
    expected, current, seen = [source], source, {source}
    while current != target:
        best, best_p = -1, -1.0
        for slot in range(int(topo.indptr[current]), int(topo.indptr[current + 1])):
            nxt = int(topo.indices[slot])
            if not active[slot] or nxt in seen:
                continue
            if priority[nxt] > best_p:
                best, best_p = nxt, priority[nxt]
        if best < 0:
            pytest.skip("this priority vector dead-ends; covered by the repair test")
        expected.append(best)
        seen.add(best)
        current = best

    result = swarm._construct(priority, EvaluationMeter(10))
    assert result is not None, "the decoder failed on a walkable vector"
    assert result[0] == expected, f"decoder took {result[0]}, hand-walk says {expected}"
    assert result[1] == pytest.approx(len(expected) - 1), (
        "unit weights mean cost must equal hop count"
    )


def test_the_decoder_ties_break_deterministically_and_are_stated():
    """**The tie-break: lowest CSR slot index wins.**

    `_construct` uses `score > best_score`, strictly greater, so the
    first candidate encountered survives a tie and iteration is in slot
    order. Two identical calls must therefore agree exactly — a decoder
    that alternated would make every downstream comparison noise.
    """
    from dynaswarm.core.meter import EvaluationMeter

    view, source, target = _uniform_graph(3)
    swarm = _swarm(view, source, target)
    priority = np.full(view.n_nodes, 0.5)   # every node tied

    first = swarm._construct(priority, EvaluationMeter(10))
    second = swarm._construct(priority, EvaluationMeter(10))
    assert first is not None and first == second, "a tied vector decoded two ways"


def test_a_dead_ending_vector_returns_none_rather_than_a_partial_route():
    """The decoder must not hand back a walk that never reached the goal."""
    from dynaswarm.core.meter import EvaluationMeter

    view, source, target = _uniform_graph(5)
    active = np.asarray(view.active).copy()
    topo = view.topology
    for slot in range(int(topo.indptr[target]), int(topo.indptr[target + 1])):
        active[slot] = False
        active[int(topo.rev[slot])] = False
    cut = view.with_state(np.asarray(view.weight), active, view.t)

    swarm = _swarm(cut, source, target)
    result = swarm._construct(np.random.default_rng(1).random(view.n_nodes),
                              EvaluationMeter(10))
    assert result is None, f"a route was returned to an unreachable target: {result}"


def test_the_velocity_update_matches_the_formula_term_by_term():
    """§5.3: v' = w*v + c1*r1*(pbest - x) + c2*r2*(gbest - x).

    **The arithmetic segment 17 reasoned about for a whole segment
    without ever checking it directly.** Every input is set here and the
    expected vector is computed from the formula, with the two random
    draws pinned so the comparison is exact rather than statistical.
    """
    view, source, target = _uniform_graph(7)
    swarm = _swarm(view, source, target,
                   params={"inertia": 0.5, "cognitive": 2.0, "social": 3.0})

    n = view.n_nodes
    swarm._position[0] = np.full(n, 0.10)
    swarm._velocity[0] = np.full(n, 0.20)
    swarm._own_best[0] = np.full(n, 0.40)
    swarm._swarm_best = np.full(n, 0.90)

    r1, r2 = 0.5, 0.25
    swarm._uniform = lambda _draws=iter((r1, r2)): next(_draws)

    # By hand: 0.5*0.20 + 2.0*0.5*(0.40-0.10) + 3.0*0.25*(0.90-0.10)
    #        = 0.10      + 0.30                + 0.60              = 1.00
    expected_v = np.full(n, 0.5 * 0.20 + 2.0 * r1 * 0.30 + 3.0 * r2 * 0.80)
    assert expected_v[0] == pytest.approx(1.00), "the hand arithmetic is wrong"

    swarm._move(0)
    assert np.allclose(swarm._velocity[0], expected_v, rtol=0, atol=1e-15), (
        f"velocity is {swarm._velocity[0][0]}, formula gives {expected_v[0]}"
    )
    # Position is the velocity applied and clipped into [0, 1].
    assert np.allclose(swarm._position[0], np.clip(0.10 + expected_v, 0.0, 1.0))


# ---------------------------------------------------------------------------
# T4 — the Hybrid's exchange: does the content arrive, and does it matter?
# ---------------------------------------------------------------------------


def test_the_exchange_content_crosses_and_has_an_effect():
    """§6.2. Entry 015 counted that it fires; nothing checked that it matters.

    An exchange that fires and is ignored counts as `exchanges: 1` and
    does nothing. Here each component is given a solution the other
    could not have produced, and the receiving side is checked for the
    specific change the formula prescribes.
    """
    from dynaswarm.optimizers.aco import Solution
    from dynaswarm.optimizers.hybrid import _EXCHANGE_GAIN, Hybrid

    view, source, target = _uniform_graph(9)
    hybrid = Hybrid(view, source, target, stream(1000, "hybrid"), {})

    route = (source, target)
    hybrid._aco._best = Solution(4.0, route)
    hybrid._pso._best = Solution(8.0, route)

    before_pos = hybrid._pso._position.copy()
    before_tau = hybrid._aco._tau.copy()

    hybrid._exchange()

    # ACO's best raises the swarm's priorities on exactly those nodes.
    nodes = list(route)
    raised = hybrid._pso._position[:, nodes] - before_pos[:, nodes]
    assert np.allclose(raised, np.clip(before_pos[:, nodes] + _EXCHANGE_GAIN, 0, 1)
                       - before_pos[:, nodes]), "the colony's route did not reach the swarm"
    assert (raised > 0).any(), "the exchange changed nothing at all"

    others = [i for i in range(view.n_nodes) if i not in nodes]
    assert np.array_equal(hybrid._pso._position[:, others], before_pos[:, others]), (
        "the exchange altered priorities away from the shared route"
    )

    # The swarm's best deposits trail on exactly its own route.
    delta = hybrid._aco._tau - before_tau
    slot = view.find_slot(source, target)
    assert delta[slot] == pytest.approx(1.0 / 8.0), (
        "the swarm's route did not deposit 1/cost on the colony's trail"
    )
    assert delta.sum() == pytest.approx(2.0 / 8.0), (
        "trail appeared on slots outside the exchanged route"
    )
