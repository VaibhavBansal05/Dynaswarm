"""Graph builders.

Produces the fixed :class:`Topology` for a trial — base edges plus the
bounded pool of candidate edges that addition events may switch on — and
the initial :class:`GraphView`.

Model choice is not cosmetic.  On Erdos-Renyi graphs with independent
random weights there is no geometry, so A* has no admissible heuristic
beyond zero and degenerates to Dijkstra.  It then stays fast at any size,
and the premise that "recomputing from scratch is expensive" is never
exercised however large the graph gets.  ``grid`` and ``geometric``
assign Euclidean weights, which gives A* a real heuristic and gives the
metaheuristics a structured landscape.
"""

from __future__ import annotations

import numpy as np

from dynaswarm.config import GraphCfg
from dynaswarm.core.graphview import GraphView, Topology, freeze

__all__ = ["build"]


def build(cfg: GraphCfg, rng: np.random.Generator) -> tuple[GraphView, int, int]:
    """Construct a trial's topology and initial state.

    Args:
        cfg: Graph configuration.
        rng: Stream for topology and weights.

    Returns:
        ``(view, source, target)``.

    Raises:
        ValueError: If ``cfg.model`` is unknown.
    """
    if cfg.model == "erdos_renyi":
        edges, pos = _erdos_renyi(cfg, rng)
    elif cfg.model == "grid":
        edges, pos = _grid(cfg)
    elif cfg.model == "geometric":
        edges, pos = _geometric(cfg, rng)
    else:
        raise ValueError(f"unknown graph model: {cfg.model!r}")

    n = cfg.n_nodes if cfg.model != "grid" else pos.shape[0]
    edges = _ensure_connected(edges, n, rng)
    pool = _addable_pool(edges, n, cfg.addable_pool_factor, rng)

    topology, weight, base_active = _to_csr(edges, pool, n, pos, cfg, rng)
    view = GraphView(topology, freeze(weight), freeze(base_active), t=0)

    source, target = _endpoints(view, rng)
    return view, source, target


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


def _erdos_renyi(cfg: GraphCfg, rng: np.random.Generator) -> tuple[set, np.ndarray | None]:
    n = cfg.n_nodes
    iu, ju = np.triu_indices(n, k=1)
    keep = rng.random(iu.size) < cfg.density
    edges = {(int(a), int(b)) for a, b in zip(iu[keep], ju[keep], strict=True)}
    return edges, None


def _grid(cfg: GraphCfg) -> tuple[set, np.ndarray]:
    side = int(round(np.sqrt(cfg.n_nodes)))
    n = side * side
    pos = np.array([(i % side, i // side) for i in range(n)], dtype=np.float64)
    edges = set()
    for i in range(n):
        r, c = divmod(i, side)
        if c + 1 < side:
            edges.add((i, i + 1))
        if r + 1 < side:
            edges.add((i, i + side))
    return edges, pos


def _geometric(cfg: GraphCfg, rng: np.random.Generator) -> tuple[set, np.ndarray]:
    n = cfg.n_nodes
    pos = rng.random((n, 2))
    # Connect points within a radius giving expected degree ~= density * n:
    # on the unit square, E[deg] = (n - 1) * pi * r^2.
    radius = float(np.sqrt(cfg.density / np.pi))
    d2 = ((pos[:, None, :] - pos[None, :, :]) ** 2).sum(-1)
    iu, ju = np.triu_indices(n, k=1)
    keep = d2[iu, ju] <= radius**2
    edges = {(int(a), int(b)) for a, b in zip(iu[keep], ju[keep], strict=True)}
    return edges, pos


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------


def _components(edges: set, n: int) -> list[set[int]]:
    """Union-find over the edge set."""
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for u, v in edges:
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv

    groups: dict[int, set[int]] = {}
    for node in range(n):
        groups.setdefault(find(node), set()).add(node)
    return list(groups.values())


def _ensure_connected(edges: set, n: int, rng: np.random.Generator) -> set:
    """Bridge components until the graph is connected."""
    comps = _components(edges, n)
    while len(comps) > 1:
        a, b = comps[0], comps[1]
        u = int(rng.choice(sorted(a)))
        v = int(rng.choice(sorted(b)))
        edges.add((min(u, v), max(u, v)))
        comps = _components(edges, n)
    return edges


def _addable_pool(
    edges: set, n: int, factor: float, rng: np.random.Generator
) -> set:
    """Sample candidate edges that addition events may later switch on.

    Bounded deliberately: an unrestricted pool is O(N^2), which is 10^6
    slots at N=1000, and the CSR superset must be allocated up front.

    Args:
        edges: Existing base edges.
        n: Node count.
        factor: Pool size as a multiple of ``|E|``.
        rng: Stream.

    Returns:
        Candidate edges disjoint from ``edges``.
    """
    target = int(factor * len(edges))
    if target <= 0 or n < 3:
        return set()
    pool: set[tuple[int, int]] = set()
    # Rejection sampling; the graph is sparse so collisions are rare.
    for _ in range(target * 8):
        if len(pool) >= target:
            break
        u, v = int(rng.integers(n)), int(rng.integers(n))
        if u == v:
            continue
        key = (min(u, v), max(u, v))
        if key not in edges:
            pool.add(key)
    return pool


def _to_csr(
    edges: set,
    pool: set,
    n: int,
    pos: np.ndarray | None,
    cfg: GraphCfg,
    rng: np.random.Generator,
) -> tuple[Topology, np.ndarray, np.ndarray]:
    """Assemble sorted CSR arrays over ``edges | pool``."""
    every = sorted(edges | pool)
    arcs: list[tuple[int, int]] = []
    for u, v in every:
        arcs.append((u, v))
        arcs.append((v, u))
    arcs.sort()

    indices = np.array([v for _, v in arcs], dtype=np.int32)
    counts = np.zeros(n, dtype=np.int64)
    for u, _ in arcs:
        counts[u] += 1
    indptr = np.zeros(n + 1, dtype=np.int32)
    indptr[1:] = np.cumsum(counts)

    slot_of = {arc: i for i, arc in enumerate(arcs)}
    rev = np.array([slot_of[(v, u)] for u, v in arcs], dtype=np.int32)

    metric = "manhattan" if cfg.model == "grid" else "euclidean"

    weight = np.empty(len(arcs), dtype=np.float64)
    active = np.zeros(len(arcs), dtype=bool)
    for (u, v), slot in slot_of.items():
        if u > v:
            continue  # assign once per undirected edge
        w = _weight_for(u, v, pos, metric, cfg, rng)
        weight[slot] = w
        weight[rev[slot]] = w
        present = (min(u, v), max(u, v)) in edges
        active[slot] = present
        active[rev[slot]] = present

    topology = Topology(
        n_nodes=n,
        indptr=freeze(indptr),
        indices=freeze(indices),
        rev=freeze(rev),
        base_active=freeze(active),
        base_weight=freeze(weight),
        pos=None if pos is None else freeze(pos),
        weight_scale=0.0 if pos is None else cfg.weight_max - cfg.weight_min,
        metric="manhattan" if cfg.model == "grid" else "euclidean",
    )
    return topology, weight, active


def _weight_for(
    u: int,
    v: int,
    pos: np.ndarray | None,
    metric: str,
    cfg: GraphCfg,
    rng: np.random.Generator,
) -> float:
    """Weight for one undirected edge.

    Weights must be derived under the **same metric** the heuristic uses.
    Pricing edges by Euclidean distance while the heuristic reasons in
    Manhattan makes the heuristic overestimate — Manhattan dominates
    Euclidean — and an inadmissible heuristic silently returns
    suboptimal paths.  On a 4-connected grid this is invisible for the
    lattice edges, where the two metrics agree, and only surfaces once
    an addition event introduces a diagonal shortcut.

    Args:
        u: One endpoint.
        v: The other endpoint.
        pos: Node coordinates, or ``None`` for non-spatial models.
        metric: ``"euclidean"`` or ``"manhattan"``.
        cfg: Graph configuration.
        rng: Stream, for non-spatial weights.

    Returns:
        The edge weight.
    """
    if pos is None:
        return float(rng.uniform(cfg.weight_min, cfg.weight_max))
    delta = np.abs(pos[u] - pos[v])
    dist = float(delta.sum()) if metric == "manhattan" else float(np.sqrt((delta**2).sum()))
    scale = cfg.weight_max - cfg.weight_min
    return cfg.weight_min + dist * scale


def _endpoints(view: GraphView, rng: np.random.Generator) -> tuple[int, int]:
    """Pick a source and a far-away target.

    Choosing the most distant reachable node rather than ``(0, n-1)``
    keeps the problem non-trivial at every graph size and model.
    """
    from dynaswarm.core.oracle import dijkstra

    source = 0
    dist, _ = dijkstra(view, source)
    finite = np.where(np.isfinite(dist))[0]
    target = int(finite[np.argmax(dist[finite])])
    if target == source:
        target = int(rng.integers(1, view.n_nodes))
    return source, target
