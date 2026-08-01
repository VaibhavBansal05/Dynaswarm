"""Exact search — the quality reference.

A* is not a competitor in the equal-budget sense and is deliberately not
treated as one.  It is exact, so on any graph state it returns the
optimum by definition; comparing its *quality* against a metaheuristic
answers a question nobody asked.

What it is measured on is **cost**.  It holds no transferable state, so
every disruption forces a complete re-search, and the interesting
quantity is how that re-search scales.  ``probe()`` therefore reports
node expansions, which is the currency in which the "recomputation is
expensive" premise either holds or does not.

Because it cannot deliver a partial answer under a smaller allowance or
use a larger one, :meth:`spend` ignores the meter.  Recording that
honestly is better than pretending A* competes on a level it does not.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import ClassVar

from dynaswarm.core.graphview import GraphView
from dynaswarm.core.meter import EvaluationMeter
from dynaswarm.core.oracle import shortest_path
from dynaswarm.optimizers.protocol import Solution
from dynaswarm.optimizers.spec import ParamSpec

__all__ = ["AStar"]


class AStar:
    """Exact shortest path, recomputed on every graph change.

    Args:
        view: Initial graph state.
        source: Start node.
        target: Goal node.
        heuristic: Use the geometric heuristic when the topology carries
            node positions.
    """

    PARAM_SPEC: ClassVar[Mapping[str, ParamSpec]] = {}
    name = "astar"

    def __init__(
        self, view: GraphView, source: int, target: int, heuristic: bool = True
    ) -> None:
        self._view = view
        self._source = source
        self._target = target
        self._heuristic = heuristic
        self._best: Solution | None = None
        self._expansions = 0
        self._stale = True

    def rebind(self, view: GraphView) -> None:
        """Adopt ``view`` and invalidate the previous answer.

        A* carries nothing forward between states.  That is not an
        oversight in the implementation but the property being measured:
        exactness is bought by paying full price after every change.
        """
        self._view = view
        self._best = None
        self._stale = True

    def spend(self, meter: EvaluationMeter) -> None:
        """Recompute the exact path, ignoring ``meter``.

        Args:
            meter: Unused; present for interface compatibility.  A* can
                neither stop early with a usable partial answer nor
                improve given more allowance.
        """
        if not self._stale:
            return
        cost, path, expansions = shortest_path(
            self._view, self._source, self._target, heuristic=self._heuristic
        )
        self._expansions = expansions
        self._best = Solution(cost, tuple(path)) if path else None
        self._stale = False

    def best(self) -> Solution | None:
        return self._best

    def params(self) -> dict[str, float]:
        return {}

    def apply(self, values: Mapping[str, float]) -> None:
        """Reject any attempt to tune a parameter-free method."""
        if values:
            raise KeyError(f"{self.name} declares no tunable parameters, got {sorted(values)}")

    def probe(self) -> dict[str, float]:
        """Report the cost of the last re-search."""
        return {"expansions": float(self._expansions)}

    def reset_learned_state(self, strength: float) -> None:
        """No-op: there is no learned state to discard."""
        return
