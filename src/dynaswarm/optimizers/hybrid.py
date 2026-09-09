"""Hybrid colony and swarm, sharing one budget.

The two methods fail differently, and that is the whole argument for
combining them.

The colony accumulates structure across timesteps.  Measured, that
memory is worth a great deal: disabling it costs around fifteen
percentage points of excess on a 200-node graph.  But the same memory is
a liability immediately after a disruption, when trails still point at a
road that has just closed and evaporation has not yet washed them out.

The swarm carries no such memory.  Its priorities rank nodes, not edges,
so a closure invalidates a remembered *cost* but not the ranking itself.
It is weaker in the steady state — measured at roughly twice the colony's
excess — and correspondingly unbothered by staleness.

So the hybrid is not "run both and hope".  It is a bet that the
memoryless component covers the memory component's known failure window,
and it makes a falsifiable prediction: the advantage, if any, should
appear in the timesteps just after a disruption rather than uniformly.

Allocation
----------
``aco_fraction`` splits each timestep's budget.  It is an ordinary tunable
so it can be fixed and tuned like any other, and it is the natural target
for a controller driven by *time since disruption* — which is a transient
property, unlike the volatility rate, whose optimum was measured not to
move at all.
"""

from __future__ import annotations

import numpy as np

from dynaswarm.core.graphview import GraphView
from dynaswarm.core.meter import EvaluationMeter
from dynaswarm.core.rng import stream
from dynaswarm.optimizers.aco import ACO
from dynaswarm.optimizers.protocol import Solution
from dynaswarm.optimizers.pso import PSO
from dynaswarm.optimizers.spec import ParamSpec, bind

__all__ = ["Hybrid"]

#: How strongly one component's best path biases the other.
_EXCHANGE_GAIN = 0.25


class Hybrid:
    """ACO and PSO over one graph, sharing a per-timestep budget.

    Args:
        view: Initial graph state.
        source: Start node.
        target: Goal node.
        rng: Random stream; the components draw from named sub-streams so
            neither is disturbed by a change to the other.
        params: Optional overrides for :attr:`PARAM_SPEC`.
    """

    PARAM_SPEC = {
        **{f"aco_{k}": v for k, v in ACO.PARAM_SPEC.items()},
        **{f"pso_{k}": v for k, v in PSO.PARAM_SPEC.items()},
        "aco_fraction": ParamSpec(
            0.5, 0.05, 0.95, doc="share of the budget given to the colony"
        ),
    }
    name = "hybrid"

    def __init__(
        self,
        view: GraphView,
        source: int,
        target: int,
        rng: np.random.Generator,
        params: dict[str, float] | None = None,
    ) -> None:
        self._p = bind(self.PARAM_SPEC, params or {})
        self._view = view

        # Independent sub-streams, so retuning the swarm cannot perturb
        # the colony's draws or vice versa.  Derived through the one
        # sanctioned entry point, and addressed by name so adding a third
        # component later would not shift either of these.
        root = int(rng.integers(0, 2**31 - 1))
        self._aco = ACO(view, source, target, stream(root, "hybrid", "aco"), self._sub("aco"))
        self._pso = PSO(view, source, target, stream(root, "hybrid", "pso"), self._sub("pso"))
        self._exchanges = 0
        self._split = (0.0, 0.0)
        self._exchanged = 0.0

    # -- protocol ---------------------------------------------------------

    def rebind(self, view: GraphView) -> None:
        self._view = view
        self._aco.rebind(view)
        self._pso.rebind(view)

    def spend(self, meter: EvaluationMeter) -> None:
        """Split the allowance between the components, then exchange.

        Each component receives its own sub-meter and the parent is
        charged what they actually spent, so the split cannot be used to
        smuggle in extra work.
        """
        budget = meter.remaining
        if budget <= 0:
            return

        aco_share = max(1, int(round(budget * self._p["aco_fraction"])))
        pso_share = max(1, budget - aco_share)

        aco_meter = EvaluationMeter(aco_share)
        self._aco.spend(aco_meter)
        pso_meter = EvaluationMeter(pso_share)
        self._pso.spend(pso_meter)

        # Measured from the sub-meters' actual spend, not from the ratio
        # that was requested. If the split does not really happen, Claim 1
        # compares the hybrid to itself, and a probe reporting the
        # intended fraction would say nothing about whether it did.
        self._split = (float(aco_meter.spent), float(pso_meter.spent))
        meter.charge(aco_meter.spent + pso_meter.spent)
        before = self._exchanges
        self._exchange()
        self._exchanged = float(self._exchanges - before)

    def best(self) -> Solution | None:
        candidates = [s for s in (self._aco.best(), self._pso.best()) if s is not None]
        return min(candidates, key=lambda s: s.cost) if candidates else None

    def params(self) -> dict[str, float]:
        return dict(self._p)

    def apply(self, values) -> None:
        self._p = bind(self.PARAM_SPEC, {**self._p, **dict(values)})
        self._aco.apply(self._sub("aco"))
        self._pso.apply(self._sub("pso"))

    def probe(self) -> dict[str, float]:
        """Telemetry from both components, prefixed by origin."""
        out = {f"aco_{k}": v for k, v in self._aco.probe().items()}
        out.update({f"pso_{k}": v for k, v in self._pso.probe().items()})
        out["aco_fraction"] = self._p["aco_fraction"]
        out["exchanges"] = float(self._exchanges)
        aco_spent, pso_spent = self._split
        total = aco_spent + pso_spent
        out["aco_spent"] = aco_spent
        out["pso_spent"] = pso_spent
        # The realised split, against `aco_fraction` above. With the
        # uncontrolled hybrid the two sit together at 0.5 for every step
        # — so the probe that shows this flat today is the one that shows
        # the allocation moving when Phase 3's controller works.
        out["aco_share_realised"] = aco_spent / total if total else 0.0
        out["exchanged_this_step"] = self._exchanged
        return out

    def reset_learned_state(self, strength: float) -> None:
        self._aco.reset_learned_state(strength)
        self._pso.reset_learned_state(strength)

    # -- coupling ---------------------------------------------------------

    def _exchange(self) -> None:
        """Let each component's best inform the other.

        The colony's best raises the swarm's priorities along that route,
        and the swarm's best deposits trail on it.  Both are nudges: a
        stronger coupling would collapse the two searches into one and
        forfeit the diversity that motivates running them together.
        """
        aco_best, pso_best = self._aco.best(), self._pso.best()

        if aco_best is not None and aco_best.path:
            nodes = np.fromiter(aco_best.path, dtype=np.int64)
            self._pso._position[:, nodes] = np.clip(
                self._pso._position[:, nodes] + _EXCHANGE_GAIN, 0.0, 1.0
            )
            self._pso._sync_lists()

        if pso_best is not None and pso_best.path and pso_best.cost > 0:
            self._aco._deposit(list(pso_best.path), pso_best.cost)
            self._aco._sync_lists()

        self._exchanges += 1

    def _sub(self, prefix: str) -> dict[str, float]:
        """Extract one component's parameters from the combined vector."""
        cut = len(prefix) + 1
        return {
            name[cut:]: value
            for name, value in self._p.items()
            if name.startswith(f"{prefix}_") and name != "aco_fraction"
        }
