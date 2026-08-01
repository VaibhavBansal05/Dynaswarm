"""Exact shortest paths — the moving optimum.

Raw path cost is not comparable across timesteps once the graph starts
changing: a run can appear to improve simply because the graph became
cheaper.  Every quality number in this project is therefore reported as
*excess over the optimum for the graph as it stands at that timestep*,
and this module computes that optimum exactly.

It doubles as the A* arm's implementation.  That makes A* the quality
ceiling by construction rather than a competitor — which is the honest
framing, since on these graph sizes exact recomputation is cheap.  What
A* is measured on is its *cost*: node expansions and wall time as the
graph grows.
"""

from __future__ import annotations

import heapq

import numpy as np

from dynaswarm.core.graphview import GraphView

__all__ = ["dijkstra", "shortest_path", "UNREACHABLE"]

#: Sentinel for "no route exists".
UNREACHABLE = float("inf")


def dijkstra(view: GraphView, source: int) -> tuple[np.ndarray, np.ndarray]:
    """Single-source shortest distances over active edges.

    Args:
        view: Graph state.
        source: Start node.

    Returns:
        ``(dist, prev)``; unreachable entries are ``inf`` and ``-1``.
    """
    n = view.n_nodes
    dist = np.full(n, UNREACHABLE, dtype=np.float64)
    prev = np.full(n, -1, dtype=np.int32)
    dist[source] = 0.0

    topo = view.topology
    heap: list[tuple[float, int]] = [(0.0, source)]
    visited = np.zeros(n, dtype=bool)

    while heap:
        d, u = heapq.heappop(heap)
        if visited[u]:
            continue
        visited[u] = True
        lo, hi = int(topo.indptr[u]), int(topo.indptr[u + 1])
        for slot in range(lo, hi):
            if not view.active[slot]:
                continue
            v = int(topo.indices[slot])
            if visited[v]:
                continue
            nd = d + float(view.weight[slot])
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))

    return dist, prev


def shortest_path(
    view: GraphView, source: int, target: int, heuristic: bool = False
) -> tuple[float, list[int], int]:
    """Exact shortest path from ``source`` to ``target``.

    Args:
        view: Graph state.
        source: Start node.
        target: Goal node.
        heuristic: Use the Euclidean heuristic when the topology carries
            node positions.  Admissible only because geometric and grid
            models derive weights from those same distances.

    Returns:
        ``(cost, path, expansions)``.  ``cost`` is ``inf`` and ``path``
        empty when no route exists.  ``expansions`` counts popped nodes
        and is the cost-of-recomputation measure.
    """
    topo = view.topology
    n = view.n_nodes

    use_h = heuristic and topo.pos is not None and topo.weight_scale > 0.0
    if use_h:
        scale = topo.weight_scale

        def h(node: int) -> float:
            return topo.distance(node, target) * scale
    else:

        def h(node: int) -> float:
            return 0.0

    dist = np.full(n, UNREACHABLE, dtype=np.float64)
    prev = np.full(n, -1, dtype=np.int32)
    dist[source] = 0.0
    visited = np.zeros(n, dtype=bool)
    heap: list[tuple[float, float, int]] = [(h(source), 0.0, source)]
    expansions = 0

    while heap:
        _, d, u = heapq.heappop(heap)
        if visited[u]:
            continue
        visited[u] = True
        expansions += 1
        if u == target:
            break
        lo, hi = int(topo.indptr[u]), int(topo.indptr[u + 1])
        for slot in range(lo, hi):
            if not view.active[slot]:
                continue
            v = int(topo.indices[slot])
            if visited[v]:
                continue
            nd = d + float(view.weight[slot])
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd + h(v), nd, v))

    if not np.isfinite(dist[target]):
        return UNREACHABLE, [], expansions

    path: list[int] = []
    node = target
    while node != -1:
        path.append(int(node))
        node = int(prev[node])
    path.reverse()
    return float(dist[target]), path, expansions
