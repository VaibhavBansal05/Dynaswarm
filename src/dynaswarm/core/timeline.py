"""Pre-materialised event schedule and the graph states it produces.

This module exists to make one class of bug inexpressible.

If events are generated *inside* the loop that also runs the algorithms,
then "the world at time t" and "whatever the loop has done so far" are
the same object, and which disruptions an arm experiences depends on
where it sits in the iteration order.  An arm evaluated before a closure
and one evaluated after it are not being compared on the same problem —
but both still return a number, so the defect is invisible in the output.

Here the entire event sequence is built **before any optimizer exists**,
and :meth:`GraphTimeline.state_at` is a pure function of that frozen
schedule.  There is no code path that yields a graph state outside the
timeline, so no arm can be handed a state another arm did not see.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from dynaswarm.config import ScenarioCfg
from dynaswarm.core.events import KINDS, Event, apply_event, candidate_slots
from dynaswarm.core.graphview import GraphView, freeze
from dynaswarm.core.oracle import dijkstra

__all__ = ["build_schedule", "GraphTimeline"]


def build_schedule(
    base: GraphView,
    cfg: ScenarioCfg,
    rng: np.random.Generator,
    source: int,
    target: int,
    preserve_connectivity: bool = True,
) -> tuple[tuple[Event, ...], ...]:
    """Materialise the whole event sequence up front.

    Event count per timestep is ``Poisson(churn * |E|)``.  Expressing
    churn as a *fraction of edges* rather than an absolute count is what
    makes the edge-ratio signal comparable across graph sizes.  Driving a
    fixed number of events per step instead would make that signal
    ``k/|E|`` — on a 150-edge graph, a single event reads as 0.007, which
    is two orders of magnitude below any threshold one would naturally
    write down, and shrinks further as the graph grows.

    Args:
        base: Initial state.
        cfg: Scenario parameters.
        rng: Stream for this trial's events.
        source: Source node, for the connectivity guard.
        target: Target node, for the connectivity guard.
        preserve_connectivity: Reject events that would disconnect
            ``source`` from ``target``.  A permanent disconnection would
            leave every arm scoring nothing for the remainder of the
            trial, wasting the run without teaching anything; transient
            unreachability is still possible and is what
            ``path_availability`` measures.

    Returns:
        One tuple of events per timestep.
    """
    topology = base.topology
    weight = np.array(base.weight, dtype=np.float64)
    active = np.array(base.active, dtype=bool)

    probs = np.array(
        [
            cfg.p_closure,
            cfg.p_traffic_up,
            cfg.p_traffic_down,
            cfg.p_reopen,
            cfg.p_delete,
            cfg.p_add,
        ],
        dtype=np.float64,
    )
    probs = probs / probs.sum()

    n_edges = base.n_active_edges
    lam = cfg.churn * n_edges
    schedule: list[tuple[Event, ...]] = []

    for _ in range(cfg.timesteps):
        step: list[Event] = []
        count = int(rng.poisson(lam)) if lam > 0 else 0
        for _ in range(count):
            event = _draw(kinds_rng=rng, probs=probs, weight=weight, active=active,
                          topology=topology, cfg=cfg)
            if event is None:
                continue
            if preserve_connectivity and _would_disconnect(
                event, weight, active, topology, source, target
            ):
                continue
            apply_event(event, weight, active, topology)
            step.append(event)
        schedule.append(tuple(step))

    return tuple(schedule)


def _draw(
    kinds_rng: np.random.Generator,
    probs: np.ndarray,
    weight: np.ndarray,
    active: np.ndarray,
    topology,
    cfg: ScenarioCfg,
) -> Event | None:
    """Sample one applicable event, or ``None`` if no slot is eligible."""
    order = kinds_rng.permutation(len(KINDS))
    chosen = int(kinds_rng.choice(len(KINDS), p=probs))
    # Try the sampled kind first, then others, so a scenario whose
    # preferred kind has no eligible slots still produces a disruption
    # instead of silently doing nothing.
    for idx in [chosen, *order.tolist()]:
        kind = KINDS[idx]
        slots = candidate_slots(kind, active, topology)
        if slots.size == 0:
            continue
        slot = int(kinds_rng.choice(slots))
        u = int(np.searchsorted(topology.indptr, slot, side="right") - 1)
        v = int(topology.indices[slot])
        old = float(weight[slot])
        new = _new_weight(kind, old, cfg, kinds_rng)
        return Event(kind=kind, slot=slot, u=u, v=v, old_weight=old, new_weight=new)
    return None


def _new_weight(
    kind: str, old: float, cfg: ScenarioCfg, rng: np.random.Generator
) -> float:
    if kind == "traffic_up":
        return old * cfg.traffic_factor
    if kind == "traffic_down":
        return old / cfg.traffic_factor
    if kind in ("reopen", "add"):
        return float(rng.uniform(1.0, max(2.0, old if old > 0 else 2.0)))
    return old


def _would_disconnect(
    event: Event,
    weight: np.ndarray,
    active: np.ndarray,
    topology,
    source: int,
    target: int,
) -> bool:
    """Check whether applying ``event`` severs ``source`` from ``target``."""
    if event.kind not in ("closure", "delete"):
        return False
    trial_active = active.copy()
    trial_weight = weight.copy()
    apply_event(event, trial_weight, trial_active, topology)
    probe = GraphView(topology, trial_weight, trial_active, t=-1)
    dist, _ = dijkstra(probe, source)
    return not np.isfinite(dist[target])


@dataclass
class GraphTimeline:
    """Replayable sequence of graph states.

    Attributes:
        base: State at ``t = 0``.
        schedule: Events per timestep, as returned by
            :func:`build_schedule`.
    """

    base: GraphView
    schedule: tuple[tuple[Event, ...], ...]

    def __post_init__(self) -> None:
        self._cache: dict[int, GraphView] = {0: self.base}

    @property
    def timesteps(self) -> int:
        return len(self.schedule)

    def events_at(self, t: int) -> tuple[Event, ...]:
        """Events applied to reach state ``t``."""
        return self.schedule[t] if 0 <= t < len(self.schedule) else ()

    def state_at(self, t: int) -> GraphView:
        """Return the state at timestep ``t``.

        Pure and cached: repeated calls return the identical object, so
        every arm provably observes the same bytes.

        Args:
            t: Timestep.

        Returns:
            The frozen :class:`GraphView` for that timestep.
        """
        if t in self._cache:
            return self._cache[t]

        prev = self.state_at(t - 1)
        weight = np.array(prev.weight, dtype=np.float64)
        active = np.array(prev.active, dtype=bool)
        for event in self.schedule[t - 1]:
            apply_event(event, weight, active, prev.topology)

        view = GraphView(prev.topology, freeze(weight), freeze(active), t=t)
        self._cache[t] = view
        return view

    def changed_edges(self, t: int) -> int:
        """Undirected edges altered between ``t-1`` and ``t``."""
        if t <= 0:
            return 0
        return len(self.schedule[t - 1])
