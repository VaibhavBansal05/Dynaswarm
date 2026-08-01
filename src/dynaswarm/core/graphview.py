"""Immutable graph state in CSR form.

The topology is fixed once per trial and never reallocated.  What varies
over time is only ``weight`` and ``active``.  Every arm receives the same
frozen :class:`GraphView`; nothing an arm can do mutates the world.

Why a static topology superset
------------------------------
Edge-addition events need somewhere to add edges *to*.  Allowing
arbitrary additions would mean the adjacency structure changes shape
every timestep, which forces every optimizer holding edge-indexed state
(pheromone, most obviously) to rebuild that state from scratch on each
change — an O(|E|) dictionary rebuild per mutation, and a decision about
what value newly-seen edges should start at.

Instead the superset — base edges plus a bounded pool of candidate edges
that additions may draw from — is allocated up front.  Edges are then
switched on and off via the ``active`` mask.  Pheromone becomes a flat
``float64`` array indexed by slot, so a deactivated edge that later
returns keeps the trail it had.  That is both faster and more faithful:
a road that reopens has not erased the colony's memory of it.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np

__all__ = ["Topology", "GraphView"]


@dataclass(frozen=True)
class Topology:
    """Fixed directed-slot structure shared by every state of a trial.

    Each undirected edge occupies two directed slots, ``s`` and
    ``rev[s]``, so an optimizer can index trail values per direction
    while weight updates stay symmetric.

    Attributes:
        n_nodes: Node count.
        indptr: CSR row pointers, length ``n_nodes + 1``.
        indices: Destination node of each slot, length ``2 * n_edges``.
        rev: Slot index of the reverse arc.
        base_active: Which slots are active in the initial state.
        pos: Optional node coordinates, used by geometric/grid graphs to
            give A* an admissible heuristic.
        weight_scale: Cost per unit Euclidean distance, or ``0.0`` when
            weights carry no geometric meaning.

            With ``weight = weight_min + d * scale`` for an edge of
            length ``d``, the cost of covering one unit of Euclidean
            distance is ``weight_min / d + scale >= scale``.  So
            ``scale * ||u - target||`` never overestimates and is an
            admissible A* heuristic.  Without this factor the heuristic
            underestimates by the full scale and A* degenerates to
            Dijkstra — which is exactly what makes the "recomputation is
            expensive" premise untestable.
        metric: ``"euclidean"`` or ``"manhattan"``.  A 4-connected grid
            admits no diagonal movement, so Euclidean distance
            underestimates the true cost badly and prunes nothing;
            Manhattan is the tight admissible bound there.
    """

    n_nodes: int
    indptr: np.ndarray
    indices: np.ndarray
    rev: np.ndarray
    base_active: np.ndarray
    pos: np.ndarray | None = None
    weight_scale: float = 0.0
    metric: str = "euclidean"

    def distance(self, node: int, target: int) -> float:
        """Geometric distance between two nodes under :attr:`metric`."""
        if self.pos is None:
            return 0.0
        delta = np.abs(self.pos[node] - self.pos[target])
        if self.metric == "manhattan":
            return float(delta.sum())
        return float(np.sqrt((delta**2).sum()))

    @property
    def n_slots(self) -> int:
        """Number of directed slots (twice the undirected edge count)."""
        return int(self.indices.size)

    def slots(self, node: int) -> slice:
        """Return the slot range belonging to ``node``."""
        return slice(int(self.indptr[node]), int(self.indptr[node + 1]))

    def neighbours(self, node: int) -> np.ndarray:
        """Return the destination nodes reachable from ``node``."""
        return self.indices[self.slots(node)]


@dataclass(frozen=True)
class GraphView:
    """One timestep's graph state.

    Attributes:
        topology: Shared structure.
        weight: Per-slot weight; symmetric across ``rev``.
        active: Per-slot presence mask; symmetric across ``rev``.
        t: Timestep this state belongs to.
    """

    topology: Topology
    weight: np.ndarray
    active: np.ndarray
    t: int

    @property
    def n_nodes(self) -> int:
        return self.topology.n_nodes

    @property
    def n_active_edges(self) -> int:
        """Undirected active edge count."""
        return int(self.active.sum()) // 2

    def state_hash(self) -> bytes:
        """Content hash of the mutable state.

        Used by the harness to assert that no arm perturbed the world and
        that every arm was handed byte-identical input.

        Returns:
            A 16-byte digest over ``weight`` and ``active``.
        """
        h = hashlib.blake2b(digest_size=16)
        h.update(np.ascontiguousarray(self.weight).tobytes())
        h.update(np.ascontiguousarray(self.active).tobytes())
        return h.digest()

    def with_state(self, weight: np.ndarray, active: np.ndarray, t: int) -> GraphView:
        """Return a new view over the same topology.

        Args:
            weight: New per-slot weights.
            active: New per-slot mask.
            t: Timestep of the new state.

        Returns:
            A fresh frozen view; ``self`` is untouched.
        """
        weight = np.asarray(weight, dtype=np.float64)
        active = np.asarray(active, dtype=bool)
        weight.flags.writeable = False
        active.flags.writeable = False
        return GraphView(self.topology, weight, active, t)

    def path_cost(self, path: list[int] | np.ndarray) -> float:
        """Total weight of a node sequence.

        Args:
            path: Node sequence.

        Returns:
            Sum of traversed weights, or ``inf`` if any step is missing
            or inactive.
        """
        if path is None or len(path) < 2:
            return float("inf")
        total = 0.0
        for u, v in zip(path[:-1], path[1:], strict=True):
            slot = self.find_slot(int(u), int(v))
            if slot < 0 or not self.active[slot]:
                return float("inf")
            total += float(self.weight[slot])
        return total

    def find_slot(self, u: int, v: int) -> int:
        """Return the slot for arc ``u -> v``, or ``-1`` if absent.

        Args:
            u: Source node.
            v: Destination node.

        Returns:
            Slot index, or ``-1``.
        """
        lo, hi = int(self.topology.indptr[u]), int(self.topology.indptr[u + 1])
        row = self.topology.indices[lo:hi]
        idx = np.searchsorted(row, v)
        if idx < row.size and row[idx] == v:
            return lo + int(idx)
        return -1


def freeze(array: np.ndarray) -> np.ndarray:
    """Return a read-only copy, so shared state cannot be mutated in place.

    Args:
        array: Any array.

    Returns:
        A read-only view of a contiguous copy.
    """
    out = np.ascontiguousarray(array).copy()
    out.flags.writeable = False
    return out
