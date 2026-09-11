"""Particle Swarm Optimization over node priorities.

PSO optimises real vectors, and a path is not one, so the encoding is
where the design lives.

Why not bias the edge weights
-----------------------------
The tempting encoding gives each particle a per-node bias ``b`` and takes
the shortest path under ``w'(u,v) = w(u,v) * (1 + b[v])``.  It always
yields a valid path and provably contains the optimum — at ``b = 0``.
That last property is fatal rather than attractive: a swarm holding
``b = 0`` finds the exact optimum on its first evaluation, so the method
is Dijkstra wearing a costume and tells you nothing about swarm search.
Any encoding whose search space contains the answer at a distinguished
point has the same problem.

What is used instead
--------------------
A particle holds one *priority* per node.  A path is built greedily from
the source, at each step taking the unvisited neighbour maximising
``priority[v] * visibility(u, v)``, where visibility is the same
``1 / (w + goal_weight * h)`` the colony uses.  Sharing the visibility
term keeps the two methods comparable: they differ in how candidates are
weighted — accumulated trail against per-particle priorities — not in
what they can see.

Greedy construction can dead-end, which is the honest cost of the
encoding, so a particle that fails is repaired by perturbing its
priorities a few times before being given up on.  Every construction and
every repair attempt is charged to the meter, since a swarm that repairs
constantly is doing real work and must pay for it.
"""

from __future__ import annotations

import numpy as np

from dynaswarm.core.graphview import GraphView
from dynaswarm.core.meter import EvaluationMeter
from dynaswarm.optimizers.protocol import Solution
from dynaswarm.optimizers.spec import ParamSpec, bind

__all__ = ["PSO"]

#: Uniform draws taken per refill, as in the colony.
_RAND_BUFFER = 4096


class PSO:
    """Priority-encoded particle swarm over a :class:`GraphView`.

    Args:
        view: Initial graph state.
        source: Start node.
        target: Goal node.
        rng: Random stream for this arm.
        params: Optional overrides for :attr:`PARAM_SPEC`.
    """

    PARAM_SPEC = {
        "inertia": ParamSpec(0.7, 0.0, 1.0, doc="carry-over of a particle's velocity"),
        "cognitive": ParamSpec(1.5, 0.0, 4.0, doc="pull toward the particle's own best"),
        "social": ParamSpec(1.5, 0.0, 4.0, doc="pull toward the swarm's best"),
        "n_particles": ParamSpec(20, 4, 100, integer=True, doc="swarm size"),
        "goal_weight": ParamSpec(
            1.0, 0.0, 5.0, doc="pull of geometric distance-to-target in visibility"
        ),
        "repair_attempts": ParamSpec(
            3, 0, 10, integer=True, doc="perturbations tried when a particle dead-ends"
        ),
    }
    name = "pso"

    def __init__(
        self,
        view: GraphView,
        source: int,
        target: int,
        rng: np.random.Generator,
        params: dict[str, float] | None = None,
    ) -> None:
        self._view = view
        self._source = source
        self._target = target
        self._rng = rng
        self._p = bind(self.PARAM_SPEC, params or {})

        n = view.n_nodes
        size = int(self._p["n_particles"])
        self._position = rng.random((size, n))
        self._velocity = rng.random((size, n)) * 0.2 - 0.1
        self._own_best = self._position.copy()
        self._own_cost = np.full(size, np.inf)
        self._last_state = view.state_hash()
        self._swarm_best: np.ndarray | None = None
        self._best: Solution | None = None
        self._pos_before = self._position.copy()
        self._mech = dict.fromkeys(("own_best", "swarm_best", "flown", "repaired"), 0.0)
        self._iterations = 0

        self._eta = np.zeros(view.topology.n_slots, dtype=np.float64)
        self._goal_cost = self._compute_goal_cost()
        self._refresh_visibility()

        self._rand_buf = rng.random(_RAND_BUFFER)
        self._rand_i = 0
        self._sync_lists()

    # -- protocol ---------------------------------------------------------

    def rebind(self, view: GraphView) -> None:
        """Adopt ``view``, keeping positions but re-pricing every memory.

        Priorities stay meaningful across a disruption — they rank nodes,
        and the nodes are unchanged.  What cannot survive is the *cost*
        attached to each remembered best, which was measured against a
        graph that no longer exists.  Carrying those forward would let the
        swarm chase a route that has since closed, so they are invalidated
        and re-established from the new state.
        """
        self._view = view
        self._refresh_visibility()
        self._sync_lists()

        # Costs were measured against a graph that no longer exists, so
        # they are invalidated and re-established from the new state.
        # The *positions* they point at are kept: a priority vector ranks
        # nodes, and the nodes are unchanged.  Discarding the swarm's
        # attractor as well would leave every particle with no social
        # pull until some particle happened to succeed — measured, that
        # cost roughly ninety points of excess under disruption, because
        # the swarm was restarting from scratch every timestep.
        #
        # **Only when the graph actually changed (F13).**  The harness
        # calls `rebind` every timestep and must keep doing so — the
        # assignment above is how the optimizer receives the current
        # world, and making the *call* conditional would leave every arm
        # searching a stale graph, which is far worse than the defect
        # this guard repairs.  So the guard lives here, on the
        # invalidation, and not at the call site.
        #
        # Without it, `inf` made the next evaluation of every particle
        # beat its own record by construction, re-anchoring each memory
        # to wherever the particle already was.  With nothing left to be
        # pulled back toward, the swarm drifted together and velocity
        # decayed to ~1e-14 over sixty steps **on a completely static
        # graph** — the collapse logged as F13, which was never about
        # disruption at all.
        #
        # **Conservative, not exact.**  Any change anywhere invalidates
        # every remembered cost, including those of particles whose route
        # is nowhere near it.  The exact form re-prices each best instead
        # of discarding it, and that is deliberately not done here: it
        # costs metered evaluations, and making PSO pay for disruption in
        # a currency ACO does not pay is a fairness decision rather than
        # an implementation detail (Entry 017 R2).  Blunt, not wrong.
        digest = view.state_hash()
        if digest != self._last_state:
            self._own_cost[:] = np.inf
            self._last_state = digest
        self._revalidate_best()

    def spend(self, meter: EvaluationMeter) -> None:
        """Fly the swarm until ``meter`` is exhausted."""
        self._pos_before = self._position.copy()
        self._mech = dict.fromkeys(self._mech, 0.0)
        while not meter.exhausted:
            for i in range(self._position.shape[0]):
                if meter.exhausted:
                    break
                self._move(i)
                result = self._construct(self._position[i], meter)
                if result is None:
                    result = self._repair(i, meter)
                if result is None:
                    continue

                path, cost = result
                if cost < self._own_cost[i]:
                    self._own_cost[i] = cost
                    self._own_best[i] = self._position[i].copy()
                    self._mech["own_best"] += 1.0
                if self._best is None or cost < self._best.cost:
                    self._best = Solution(cost, tuple(path))
                    self._swarm_best = self._position[i].copy()
                    self._mech["swarm_best"] += 1.0
            self._iterations += 1

    def best(self) -> Solution | None:
        return self._best

    def params(self) -> dict[str, float]:
        return dict(self._p)

    def apply(self, values) -> None:
        """Adopt ``values``; unknown names raise rather than being ignored."""
        previous = int(self._p["n_particles"])
        self._p = bind(self.PARAM_SPEC, {**self._p, **dict(values)})
        self._refresh_visibility()
        self._sync_lists()
        if int(self._p["n_particles"]) != previous:
            self._resize(int(self._p["n_particles"]))

    def probe(self) -> dict[str, float]:
        """Internal telemetry.

        ``diversity`` is the swarm's counterpart to the colony's
        branching factor: the mean spread of priorities across particles,
        which collapses toward zero as the swarm converges on one region.
        """
        speed = np.abs(self._velocity)
        return {
            "diversity": float(np.mean(np.std(self._position, axis=0))),
            "iterations": float(self._iterations),
            "particles_flown": self._mech["flown"],
            "particles_repaired": self._mech["repaired"],
            "particles": float(self._position.shape[0]),
            "speed_mean": float(speed.mean()),
            "speed_max": float(speed.max()),
            "own_best_updates": self._mech["own_best"],
            "swarm_best_updates": self._mech["swarm_best"],
        }

    def reset_learned_state(self, strength: float) -> None:
        """Scatter a fraction of the swarm back to random priorities."""
        s = min(max(float(strength), 0.0), 1.0)
        if s <= 0.0:
            return
        size, n = self._position.shape
        count = int(round(s * size))
        if count == 0:
            return
        victims = np.argsort(self._own_cost)[-count:]
        self._position[victims] = self._rng.random((count, n))
        self._own_cost[victims] = np.inf

    # -- search -----------------------------------------------------------

    def _move(self, i: int) -> None:
        """Update one particle's velocity and position."""
        r1, r2 = self._uniform(), self._uniform()
        cognitive = self._p["cognitive"] * r1 * (self._own_best[i] - self._position[i])
        social = 0.0
        if self._swarm_best is not None:
            social = self._p["social"] * r2 * (self._swarm_best - self._position[i])
        self._velocity[i] = self._p["inertia"] * self._velocity[i] + cognitive + social
        # Counted here, inside the mechanism, rather than by diffing
        # positions across the call. `_repair` also writes positions, so
        # a position-diff answers "did anything move a particle" when the
        # question is "is the swarm flying" — two mechanisms through one
        # channel, which is the confusion segment 9 split the picture to
        # avoid.
        before = self._position[i].copy()
        np.clip(self._position[i] + self._velocity[i], 0.0, 1.0, out=self._position[i])
        if not np.array_equal(self._position[i], before):
            self._mech["flown"] += 1.0

    def _construct(
        self, priority: np.ndarray, meter: EvaluationMeter
    ) -> tuple[list[int], float] | None:
        """Build a path greedily under ``priority``, charging the meter once."""
        meter.charge()

        indptr, indices = self._indptr_l, self._indices_l
        active, eta, weight = self._active_l, self._eta_l, self._weight_l
        prio = priority.tolist()

        current = self._source
        target = self._target
        path = [current]
        cost = 0.0
        visited = {current}

        while current != target:
            best_slot = -1
            best_score = -1.0
            for slot in range(indptr[current], indptr[current + 1]):
                if not active[slot] or indices[slot] in visited:
                    continue
                score = prio[indices[slot]] * eta[slot]
                if score > best_score:
                    best_score = score
                    best_slot = slot
            if best_slot < 0:
                return None
            cost += weight[best_slot]
            current = indices[best_slot]
            path.append(current)
            visited.add(current)

        return path, cost

    def _repair(self, i: int, meter: EvaluationMeter) -> tuple[list[int], float] | None:
        """Retry a dead-ended particle under perturbed priorities."""
        for _ in range(int(self._p["repair_attempts"])):
            if meter.exhausted:
                return None
            jitter = np.array([self._uniform() for _ in range(self._position.shape[1])])
            candidate = np.clip(self._position[i] * 0.5 + jitter * 0.5, 0.0, 1.0)
            result = self._construct(candidate, meter)
            if result is not None:
                self._position[i] = candidate
                self._mech["repaired"] += 1.0
                return result
        return None

    def _resize(self, size: int) -> None:
        """Grow or shrink the swarm, keeping the fittest particles."""
        current, n = self._position.shape
        if size == current:
            return
        if size < current:
            keep = np.argsort(self._own_cost)[:size]
            self._position = self._position[keep]
            self._velocity = self._velocity[keep]
            self._own_best = self._own_best[keep]
            self._own_cost = self._own_cost[keep]
        else:
            extra = size - current
            self._position = np.vstack([self._position, self._rng.random((extra, n))])
            self._velocity = np.vstack(
                [self._velocity, self._rng.random((extra, n)) * 0.2 - 0.1]
            )
            self._own_best = np.vstack([self._own_best, self._position[-extra:].copy()])
            self._own_cost = np.concatenate([self._own_cost, np.full(extra, np.inf)])

    # -- state ------------------------------------------------------------

    def _uniform(self) -> float:
        if self._rand_i >= self._rand_buf.size:
            self._rand_buf = self._rng.random(_RAND_BUFFER)
            self._rand_i = 0
        value = self._rand_buf[self._rand_i]
        self._rand_i += 1
        return float(value)

    def _refresh_visibility(self) -> None:
        weight = np.asarray(self._view.weight)
        denom = weight + self._p["goal_weight"] * self._goal_cost
        np.divide(1.0, np.maximum(denom, 1e-12), out=self._eta)
        self._eta[~np.asarray(self._view.active)] = 0.0

    def _compute_goal_cost(self) -> np.ndarray:
        topo = self._view.topology
        if topo.pos is None or topo.weight_scale <= 0.0:
            return np.zeros(topo.n_slots, dtype=np.float64)
        dest = np.asarray(topo.indices)
        delta = np.abs(np.asarray(topo.pos)[dest] - np.asarray(topo.pos)[self._target])
        dist = delta.sum(axis=1) if topo.metric == "manhattan" else np.sqrt((delta**2).sum(axis=1))
        return dist * topo.weight_scale

    def _sync_lists(self) -> None:
        topo = self._view.topology
        self._indptr_l = topo.indptr.tolist()
        self._indices_l = topo.indices.tolist()
        self._active_l = np.asarray(self._view.active).tolist()
        self._eta_l = self._eta.tolist()
        self._weight_l = np.asarray(self._view.weight).tolist()

    def _revalidate_best(self) -> None:
        if self._best is None:
            return
        cost = self._view.path_cost(list(self._best.path))
        self._best = Solution(cost, self._best.path) if np.isfinite(cost) else None
