"""Ant Colony Optimization, MAX--MIN variant.

Ants build source-to-target paths by choosing each next hop with
probability proportional to ``tau^alpha * eta^beta`` — accumulated trail
against local edge desirability.

Trail limits
------------
Plain Ant System lets the ratio between the strongest and weakest trail
grow without bound.  Once it does, every ant follows one path, the colony
stops sampling alternatives, and no evaporation setting can revive it —
which would make adaptation unmeasurable, since the dial the controller
turns is no longer connected to anything.  Following Stuetzle & Hoos,
trails are clamped into ``[tau_min, tau_max]`` with
``tau_max = 1/(rho * C_best)`` and ``tau_min = tau_max/(2n)``, capping
that ratio at ``2n`` however long the colony runs.

Carrying trails across disruptions
----------------------------------
:meth:`rebind` keeps the trail on every surviving slot.  This is
deliberate and is the phenomenon the project studies: when a favoured
road closes, the colony keeps being drawn toward it until evaporation
washes the memory out.  Discarding trails on change would remove the
problem that adaptation is supposed to solve.

Goal direction
--------------
Visibility is ``1 / (w + goal_weight * h)``, where ``h`` is the geometric
distance from the arc's destination to the target.  Cheapness alone is
not enough to solve a *point-to-point* problem: an ant guided only by
``1/w`` has no notion of where the target lies, and must stumble on it.
Measured on 200-node random graphs, such a colony settled around 90 %
above optimum and stopped improving, while the same code on a 30-node
graph reached 2.5 % — not because the search was better there, but
because the graph was small enough that a wandering ant met the target
by chance.

``h`` is derived from node coordinates, which are part of the problem
statement for a spatial network, not from any shortest-path computation:
handing the colony a distance-to-target oracle would be handing it the
answer.  Topologies without coordinates leave ``h = 0``, which recovers
plain ``1/w``.
"""

from __future__ import annotations

import numpy as np

from dynaswarm.core.graphview import GraphView
from dynaswarm.core.meter import EvaluationMeter
from dynaswarm.optimizers.protocol import Solution
from dynaswarm.optimizers.spec import ParamSpec, bind, defaults

__all__ = ["ACO"]

#: Fraction of a node's local trail range above which an arc counts as
#: still competitive, when measuring branching (Mavrovouniotis & Yang).
_LAMBDA = 0.05

#: Visit weight below which a node is considered untouched by recent
#: search and excluded from the branching measure.
_VISIT_FLOOR = 1.0

#: Per-iteration decay of the visit counter.
_VISIT_DECAY = 0.9

#: Uniform draws taken per refill.  Amortises the numpy call that would
#: otherwise sit in the innermost loop.
_RAND_BUFFER = 4096


class ACO:
    """MAX--MIN Ant System over a :class:`GraphView`.

    Args:
        view: Initial graph state.
        source: Start node.
        target: Goal node.
        rng: Random stream for this arm.
        params: Optional overrides for :attr:`PARAM_SPEC`.
    """

    PARAM_SPEC = {
        "alpha": ParamSpec(1.0, 0.0, 5.0, doc="trail exponent; weight on accumulated memory"),
        "beta": ParamSpec(2.0, 0.0, 8.0, doc="visibility exponent; weight on edge cost"),
        "rho": ParamSpec(0.10, 0.01, 0.90, doc="evaporation rate per iteration"),
        "n_ants": ParamSpec(20, 4, 100, integer=True, doc="paths built per iteration"),
        "goal_weight": ParamSpec(
            1.0, 0.0, 5.0, doc="pull of geometric distance-to-target in visibility"
        ),
    }
    name = "aco"

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

        n_slots = view.topology.n_slots
        self._tau = np.full(n_slots, 1.0, dtype=np.float64)
        self._eta = np.zeros(n_slots, dtype=np.float64)
        self._visits = np.zeros(view.n_nodes, dtype=np.float64)
        self._best: Solution | None = None
        self._iterations = 0
        self._goal_cost = self._compute_goal_cost()
        self._refresh_visibility()

        self._rand_buf = rng.random(_RAND_BUFFER)
        self._rand_i = 0
        self._sync_lists(structure=True)

    # -- protocol ---------------------------------------------------------

    def rebind(self, view: GraphView) -> None:
        """Adopt ``view``, keeping trails and re-pricing the incumbent."""
        self._view = view
        self._refresh_visibility()
        # A trail on a slot that has gone inactive is meaningless; zeroing
        # it now avoids resurrecting a stale preference if the edge later
        # reopens with a quite different weight.
        self._tau[~np.asarray(view.active)] = 0.0
        self._sync_lists(structure=True)
        self._revalidate_best()

    def spend(self, meter: EvaluationMeter) -> None:
        """Build ants until ``meter`` is exhausted.

        An iteration is abandoned part-way when the allowance runs out,
        and whatever ants completed still deposit.  Finishing the
        iteration instead would overrun the budget by up to ``n_ants``
        constructions — an overrun that grows precisely when the
        controller enlarges the colony.
        """
        while not meter.exhausted:
            found: list[tuple[list[int], float]] = []
            for _ in range(int(self._p["n_ants"])):
                if meter.exhausted:
                    break
                result = self._construct(meter)
                if result is not None:
                    found.append(result)

            self._evaporate()
            if found:
                best_path, best_cost = min(found, key=lambda pc: pc[1])
                self._offer(best_path, best_cost)
                self._deposit(best_path, best_cost)
            self._clamp_trails()
            self._sync_lists()

            self._visits *= _VISIT_DECAY
            self._iterations += 1

    def best(self) -> Solution | None:
        return self._best

    def params(self) -> dict[str, float]:
        return dict(self._p)

    def apply(self, values) -> None:
        """Adopt ``values``; unknown names raise rather than being ignored.

        Visibility is recomputed here because ``goal_weight`` enters it.
        Deferring that to the next :meth:`rebind` would leave the
        parameter recorded but not yet in effect — which reads, in a
        decision log, exactly like a parameter that does nothing.
        """
        self._p = bind(self.PARAM_SPEC, {**self._p, **dict(values)})
        self._refresh_visibility()
        self._sync_lists(structure=True)

    def probe(self) -> dict[str, float]:
        """Internal telemetry, including the branching measure."""
        return {
            "lambda_branch": self._lambda_branching(),
            "tau_ratio": self._tau_ratio(),
            "iterations": float(self._iterations),
        }

    def reset_learned_state(self, strength: float) -> None:
        """Wash out trails toward the uniform state.

        Args:
            strength: ``0`` leaves trails untouched, ``1`` erases all
                differences between them.
        """
        s = min(max(float(strength), 0.0), 1.0)
        if s <= 0.0:
            return
        active = np.asarray(self._view.active)
        if not active.any():
            return
        mean = float(self._tau[active].mean())
        self._tau[active] = (1.0 - s) * self._tau[active] + s * mean
        self._sync_lists()

    # -- search -----------------------------------------------------------

    def _construct(self, meter: EvaluationMeter) -> tuple[list[int], float] | None:
        """Build one path, charging the meter exactly once.

        Written against plain Python lists rather than the numpy arrays
        that back them.  A node's candidate set is its degree — a dozen
        entries or so — and at that size numpy is the wrong tool: each
        call costs a microsecond or two of dispatch regardless of how
        little data it touches, and this loop makes several per step.
        Profiling put 72 % of a run inside this function, almost all of
        it dispatch on arrays of about twelve elements.

        The lists are mirrors of the arrays, refreshed once per iteration
        rather than per step, so bulk operations like evaporation still
        get to be vectorised where that genuinely pays.

        Returns:
            ``(path, cost)``, or ``None`` if the ant reached a dead end.
        """
        meter.charge()

        indptr, indices = self._indptr_l, self._indices_l
        active, tau, eta, weight = self._active_l, self._tau_l, self._eta_l, self._weight_l
        alpha, beta = self._p["alpha"], self._p["beta"]

        current = self._source
        target = self._target
        path = [current]
        cost = 0.0
        visited = {current}

        while current != target:
            candidates: list[int] = []
            scores: list[float] = []
            total = 0.0
            for slot in range(indptr[current], indptr[current + 1]):
                if not active[slot] or indices[slot] in visited:
                    continue
                score = (tau[slot] ** alpha) * (eta[slot] ** beta)
                candidates.append(slot)
                scores.append(score)
                total += score

            if not candidates:
                return None

            if total > 0.0:
                threshold = self._uniform() * total
                acc = 0.0
                chosen = candidates[-1]
                for slot, score in zip(candidates, scores, strict=True):
                    acc += score
                    if acc >= threshold:
                        chosen = slot
                        break
            else:
                # Every option scored zero — an underflow rather than a
                # preference, so fall back to an unbiased choice.
                chosen = candidates[int(self._uniform() * len(candidates))]

            cost += weight[chosen]
            current = indices[chosen]
            path.append(current)
            visited.add(current)
            self._visits[current] += 1.0

        return path, cost

    def _uniform(self) -> float:
        """Next uniform draw, taken from a pre-filled buffer.

        Drawing singly would put a numpy call in the innermost loop, at
        roughly the cost of the arithmetic it guards.
        """
        if self._rand_i >= self._rand_buf.size:
            self._rand_buf = self._rng.random(_RAND_BUFFER)
            self._rand_i = 0
        value = self._rand_buf[self._rand_i]
        self._rand_i += 1
        return float(value)

    def _sync_lists(self, structure: bool = False) -> None:
        """Refresh the Python mirrors of the numpy state.

        Args:
            structure: Also refresh topology and per-edge state, which
                change only when the graph does.
        """
        self._tau_l = self._tau.tolist()
        if structure:
            topo = self._view.topology
            self._indptr_l = topo.indptr.tolist()
            self._indices_l = topo.indices.tolist()
            self._active_l = np.asarray(self._view.active).tolist()
            self._eta_l = self._eta.tolist()
            self._weight_l = np.asarray(self._view.weight).tolist()

    def _offer(self, path: list[int], cost: float) -> None:
        if self._best is None or cost < self._best.cost:
            self._best = Solution(cost, tuple(path))

    def _evaporate(self) -> None:
        self._tau *= 1.0 - self._p["rho"]

    def _deposit(self, path: list[int], cost: float) -> None:
        """Reinforce one path, symmetrically across both directions."""
        if cost <= 0.0:
            return
        amount = 1.0 / cost
        rev = self._view.topology.rev
        for u, v in zip(path[:-1], path[1:], strict=True):
            slot = self._view.find_slot(u, v)
            if slot >= 0:
                self._tau[slot] += amount
                self._tau[int(rev[slot])] += amount

    def _clamp_trails(self) -> None:
        """Apply the MAX--MIN bounds once a reference cost exists."""
        if self._best is None or not np.isfinite(self._best.cost) or self._best.cost <= 0:
            return
        rho = self._p["rho"]
        if rho <= 0.0:
            return
        tau_max = 1.0 / (rho * self._best.cost)
        tau_min = tau_max / (2.0 * max(self._view.n_nodes, 2))
        active = np.asarray(self._view.active)
        np.clip(self._tau, tau_min, tau_max, out=self._tau, where=active)

    # -- state ------------------------------------------------------------

    def _refresh_visibility(self) -> None:
        """Recompute ``1 / (w + goal_weight * h)`` for the current state.

        ``h`` depends only on coordinates and the target, so it is
        computed once and cached; only the weight term moves as the graph
        changes.
        """
        weight = np.asarray(self._view.weight)
        denom = weight + self._p["goal_weight"] * self._goal_cost
        np.divide(1.0, np.maximum(denom, 1e-12), out=self._eta)
        self._eta[~np.asarray(self._view.active)] = 0.0

    def _compute_goal_cost(self) -> np.ndarray:
        """Geometric lower bound on the remaining cost after each arc.

        Returns:
            Per-slot cost-to-go estimate, all zeros when the topology
            carries no coordinates.
        """
        topo = self._view.topology
        n_slots = topo.n_slots
        if topo.pos is None or topo.weight_scale <= 0.0:
            return np.zeros(n_slots, dtype=np.float64)
        dest = np.asarray(topo.indices)
        delta = np.abs(np.asarray(topo.pos)[dest] - np.asarray(topo.pos)[self._target])
        if topo.metric == "manhattan":
            dist = delta.sum(axis=1)
        else:
            dist = np.sqrt((delta**2).sum(axis=1))
        return dist * topo.weight_scale

    def _revalidate_best(self) -> None:
        """Re-price the incumbent; drop it if it no longer exists."""
        if self._best is None:
            return
        cost = self._view.path_cost(list(self._best.path))
        self._best = Solution(cost, self._best.path) if np.isfinite(cost) else None

    # -- telemetry --------------------------------------------------------

    def _lambda_branching(self) -> float:
        """Mean number of still-competitive arcs per recently visited node.

        A value near 1 means each node retains a single attractive
        onward arc and the colony has converged; values approaching the
        mean degree mean it is still spread across alternatives.

        The measure is conventionally halved, because in a tour every
        node carries exactly two arcs and 1 is therefore the converged
        value.  That reference point does not transfer to point-to-point
        routing, where a converged node has one competitive *outgoing*
        arc rather than two.  Reporting the unhalved mean keeps 1 as the
        convergence point and the mean degree as the diffuse extreme,
        both of which are directly interpretable here.

        Only nodes the ants have actually visited recently are counted.
        Untouched nodes keep uniform trails, so every incident arc counts
        as competitive; including them would report healthy diversity for
        a colony that had in fact converged on the region it searches.
        """
        topo = self._view.topology
        active = np.asarray(self._view.active)

        recent = self._visits >= _VISIT_FLOOR
        nodes = np.flatnonzero(recent)
        if nodes.size == 0:
            return 0.0

        total = 0.0
        counted = 0
        for node in nodes:
            lo, hi = int(topo.indptr[node]), int(topo.indptr[node + 1])
            mask = active[lo:hi]
            if mask.sum() < 2:
                continue
            trails = self._tau[lo:hi][mask]
            lo_t, hi_t = float(trails.min()), float(trails.max())
            threshold = lo_t + _LAMBDA * (hi_t - lo_t)
            total += float((trails >= threshold).sum())
            counted += 1

        return total / counted if counted else 0.0

    def _tau_ratio(self) -> float:
        """Strongest trail over weakest, on active slots."""
        active = np.asarray(self._view.active)
        if not active.any():
            return 1.0
        trails = self._tau[active]
        lo = float(trails.min())
        return float(trails.max() / lo) if lo > 0 else float("inf")


def default_params() -> dict[str, float]:
    """Convenience accessor for the declared defaults."""
    return defaults(ACO.PARAM_SPEC)
