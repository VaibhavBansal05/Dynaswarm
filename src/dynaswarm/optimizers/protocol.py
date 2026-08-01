"""The optimizer contract.

Four methods carry the design:

``rebind``
    Adopt a mutated graph *while preserving learned state*.  Discarding
    that state on every change would erase the very phenomenon under
    study — a pheromone trail that has gone stale because the road it
    favours just closed.  Adaptation exists to correct exactly that, so
    it must be allowed to happen.

``spend``
    Do work until the injected meter is exhausted.  Partial iterations
    are legal and expected; finishing an iteration that has already
    overrun would overshoot by up to one population's worth of
    constructions, and that overshoot would scale with a controller-tuned
    parameter.

``params`` / ``apply``
    A total binding against ``PARAM_SPEC``, so a parameter cannot be
    written and then silently not read.

``probe`` supplies internal telemetry — colony stagnation, swarm
diversity — which is what lets a controller sense the *algorithm's* state
rather than only the environment's.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar, Protocol, runtime_checkable

from dynaswarm.core.graphview import GraphView
from dynaswarm.core.meter import EvaluationMeter
from dynaswarm.optimizers.spec import ParamSpec

__all__ = ["Solution", "Optimizer"]


@dataclass(frozen=True)
class Solution:
    """An incumbent route.

    Attributes:
        cost: Total path weight.
        path: Node sequence from source to target.
    """

    cost: float
    path: tuple[int, ...]


@runtime_checkable
class Optimizer(Protocol):
    """What the harness requires of every arm."""

    #: Declared tunables.  Empty for parameter-free methods.
    PARAM_SPEC: ClassVar[Mapping[str, ParamSpec]]

    #: Label used in results.
    name: str

    def rebind(self, view: GraphView) -> None:
        """Adopt ``view``, preserving learned state and re-pricing the best."""
        ...

    def spend(self, meter: EvaluationMeter) -> None:
        """Search until ``meter`` is exhausted."""
        ...

    def best(self) -> Solution | None:
        """Return the incumbent, or ``None`` if no route is held."""
        ...

    def params(self) -> dict[str, float]:
        """Return the current value of every declared tunable."""
        ...

    def apply(self, values: Mapping[str, float]) -> None:
        """Adopt ``values``, validated against :attr:`PARAM_SPEC`."""
        ...

    def probe(self) -> dict[str, float]:
        """Return internal telemetry for sensing and logging."""
        ...

    def reset_learned_state(self, strength: float) -> None:
        """Discard accumulated state; ``0`` is a no-op, ``1`` a full reset."""
        ...
