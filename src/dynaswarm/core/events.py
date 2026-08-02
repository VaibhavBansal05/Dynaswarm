"""Dynamic events — pure transformations of graph state.

An event never mutates a :class:`GraphView`.  It reads the current
``(weight, active)`` arrays and returns modified copies, which is what
lets the timeline be replayed identically for every arm.

On closure versus deletion
--------------------------
The original design lists both.  Under an active-mask representation
they are the *same* operation — an edge stops being traversable — and
pretending otherwise would mean carrying a per-slot "permanently
removed" flag for no scientific gain.  Both labels are retained so
event-type breakdowns stay faithful to the brief, but they share one
mechanism, and the docstring says so rather than implying a distinction
the code does not make.

What separates ``reopen`` from ``add`` is which slots they may target:
``reopen`` reactivates an inactive *base* edge, ``add`` activates an
edge from the candidate pool.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from dynaswarm.core.graphview import Topology

__all__ = ["Event", "EventKind", "apply_event", "KINDS"]

#: Event labels, in the order their probabilities appear in ScenarioCfg.
KINDS = ("closure", "traffic_up", "traffic_down", "reopen", "delete", "add")

EventKind = str


@dataclass(frozen=True)
class Event:
    """One disruption.

    Attributes:
        kind: One of :data:`KINDS`.
        slot: Directed slot affected; its reverse is affected identically.
        u: Source endpoint, for reporting.
        v: Destination endpoint, for reporting.
        old_weight: Weight before the event.
        new_weight: Weight after the event.
    """

    kind: EventKind
    slot: int
    u: int
    v: int
    old_weight: float
    new_weight: float


def apply_event(
    event: Event, weight: np.ndarray, active: np.ndarray, topology: Topology
) -> None:
    """Apply ``event`` in place to working arrays.

    The arrays are the schedule builder's scratch buffers, never a
    published :class:`GraphView`'s frozen arrays.

    Args:
        event: The event to apply.
        weight: Mutable per-slot weights.
        active: Mutable per-slot mask.
        topology: For the reverse-slot mapping.
    """
    slot = event.slot
    rev = int(topology.rev[slot])

    if event.kind in ("closure", "delete"):
        active[slot] = False
        active[rev] = False
    elif event.kind in ("reopen", "add"):
        active[slot] = True
        active[rev] = True
        weight[slot] = event.new_weight
        weight[rev] = event.new_weight
    else:  # traffic_up / traffic_down
        weight[slot] = event.new_weight
        weight[rev] = event.new_weight


def cluster_slots(
    slots: np.ndarray,
    focus: int,
    size: int,
    topology: Topology,
    active: np.ndarray,
) -> np.ndarray:
    """Choose a spatially coherent group of slots around ``focus``.

    Disruptions in the world are not scattered uniformly over a network:
    congestion fills a district, weather covers an area, an incident
    closes a junction and everything feeding it.  Modelling each event as
    one edge drawn uniformly makes disruption almost always irrelevant to
    any particular journey — on a 150-edge graph a four-hop route is hit
    by roughly one event in forty, so whole trials pass with the optimum
    untouched and there is nothing to recover from.

    Raising the event rate to compensate removes the quiet stretches that
    recovery needs.  Clustering instead keeps disruptions rare *and*
    consequential: few events, each affecting a neighbourhood.

    Args:
        slots: Eligible slots for this event kind.
        focus: Node the disruption is centred on.
        size: Maximum slots to affect.
        topology: For adjacency.
        active: Current mask.

    Returns:
        Up to ``size`` slots, preferring those incident to ``focus`` and
        then to its neighbours.
    """
    if size <= 1:
        return slots[:1]

    eligible = set(slots.tolist())
    chosen: list[int] = []

    # Ripple outward: the focus node's own arcs first, then its
    # neighbours', which keeps the affected set connected.
    frontier = [focus]
    seen = {focus}
    while frontier and len(chosen) < size:
        node = frontier.pop(0)
        lo, hi = int(topology.indptr[node]), int(topology.indptr[node + 1])
        for slot in range(lo, hi):
            if len(chosen) >= size:
                break
            if slot in eligible and slot not in chosen:
                chosen.append(slot)
            neighbour = int(topology.indices[slot])
            if active[slot] and neighbour not in seen:
                seen.add(neighbour)
                frontier.append(neighbour)

    return np.array(chosen, dtype=np.int64) if chosen else slots[:1]


def candidate_slots(
    kind: EventKind, active: np.ndarray, topology: Topology
) -> np.ndarray:
    """Slots eligible for an event of this kind.

    Only forward slots (``u < v``) are returned so each undirected edge
    is considered once.

    Args:
        kind: Event kind.
        active: Current mask.
        topology: Structure, for base-edge membership.

    Returns:
        Array of eligible slot indices, possibly empty.
    """
    forward = _forward_mask(topology)

    if kind in ("closure", "delete", "traffic_up", "traffic_down"):
        eligible = active & forward
    elif kind == "reopen":
        # An inactive edge that belongs to the original graph.
        eligible = (~active) & np.asarray(topology.base_active) & forward
    elif kind == "add":
        # An inactive edge from the candidate pool.
        eligible = (~active) & (~np.asarray(topology.base_active)) & forward
    else:
        raise ValueError(f"unknown event kind: {kind!r}")

    return np.flatnonzero(eligible)


def _forward_mask(topology: Topology) -> np.ndarray:
    """Mark one slot per undirected edge (the one with ``u < v``)."""
    n_slots = topology.n_slots
    src = np.empty(n_slots, dtype=np.int32)
    for u in range(topology.n_nodes):
        src[topology.slots(u)] = u
    return src < topology.indices
