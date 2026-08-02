"""What the controller senses.

Three signals, deliberately of two different kinds:

*External* signals watch the environment — how much of the graph changed,
how often anything changed at all.  *Internal* signals watch the search —
whether the colony has collapsed onto one route.  The literature picks
one or the other largely by convention, and the choice is rarely tested;
comparing them is a stated aim of this project.

Scales are not comparable, and deliberately so
----------------------------------------------
The edge ratio lives near the churn rate (a few percent), volatility
spans the whole of ``[0, 1]``, and branching runs from 1 to roughly the
mean degree.  Rescaling them onto a common interval would require
inventing bounds that do not exist, and would bake an arbitrary constant
into the comparison being tested.

Instead each signal reports its *natural* units and declares an
:attr:`Signal.explore_direction`: ``+1`` when a larger reading means more
exploration is wanted, ``-1`` when it means less.  Branching is the
inverted case — a *low* branching factor means the colony has converged
and needs shaking up.  The controller then works on
``direction * value`` relative to that signal's own running baseline, so
no absolute threshold has to be justified for any of them.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

__all__ = [
    "StepObservation",
    "Signal",
    "EdgeRatioSignal",
    "VolatilitySignal",
    "LambdaBranchingSignal",
    "make_signal",
    "SIGNALS",
]


@dataclass(frozen=True)
class StepObservation:
    """Everything a signal is allowed to see at one timestep.

    Signals receive this rather than the optimizer itself, so each can be
    unit-tested in isolation and none can reach into search internals
    that another signal would not have.

    Attributes:
        t: Timestep.
        n_events: Disruptions applied to reach this state.
        n_edges: Active undirected edges.
        best_cost: The arm's incumbent cost, if it holds a route.
        probe: Optimizer telemetry, e.g. ``lambda_branch``.
    """

    t: int
    n_events: int
    n_edges: int
    best_cost: float | None
    probe: Mapping[str, float] = field(default_factory=dict)


@runtime_checkable
class Signal(Protocol):
    """A sensed quantity driving adaptation."""

    name: str

    #: ``+1`` if a larger reading calls for more exploration, ``-1`` if less.
    explore_direction: float

    def observe(self, obs: StepObservation) -> None:
        """Absorb one timestep."""
        ...

    def value(self) -> float:
        """Current reading, in the signal's own units."""
        ...


class _Windowed:
    """Shared rolling-window bookkeeping."""

    def __init__(self, window: int) -> None:
        if window < 1:
            raise ValueError(f"window must be >= 1, got {window}")
        self._history: deque[float] = deque(maxlen=window)

    def value(self) -> float:
        if not self._history:
            return 0.0
        return sum(self._history) / len(self._history)


class EdgeRatioSignal(_Windowed):
    """Fraction of edges disturbed per timestep, averaged over a window.

    This is the intuitive reading of "how much is the world changing",
    and it is scale-comparable only because events are driven at a
    fraction of ``|E|``: were a fixed number of edges changed per step,
    this would report ``k/|E|`` and shrink toward zero as graphs grow,
    while any threshold written against it stayed put.
    """

    name = "edge_ratio"
    explore_direction = 1.0

    def observe(self, obs: StepObservation) -> None:
        self._history.append(obs.n_events / max(obs.n_edges, 1))


class VolatilitySignal(_Windowed):
    """Fraction of recent timesteps that carried any disruption.

    Insensitive to how *much* changed, only to how often.  That bounds it
    to ``[0, 1]`` at any graph size, but also gives it a working range
    rather than universal applicability: it saturates once the expected
    event count per step exceeds one or two, and beyond that cannot tell
    a busy world from a chaotic one.

    Because events are driven at a *fraction* of ``|E|``, that count
    grows with the graph, so the usable range shrinks as graphs get
    larger.  Measured: at n=30 (|E| ~ 150) the scenario tiers read 0.00,
    0.26, 0.56 and 0.86; at n=200 (|E| ~ 1200) even the moderate tier
    delivers about seven events per step and the signal pins at 1.000
    everywhere.  A pinned signal has no gradient, and a controller driven
    by one cannot move at all.
    """

    name = "volatility"
    explore_direction = 1.0

    def observe(self, obs: StepObservation) -> None:
        self._history.append(1.0 if obs.n_events > 0 else 0.0)


class LambdaBranchingSignal(_Windowed):
    """Mean competitive arcs per visited node — colony stagnation.

    The one *internal* signal: it reads the search rather than the world.
    A reading near 1 means each node retains a single attractive onward
    arc and the colony has stopped sampling alternatives, which is when
    exploration is most needed — hence the inverted direction.

    It answers a different question from the other two, and the
    difference is measurable.  Across static, low, moderate and high
    scenarios its mean readings are 7.30, 7.38, 7.14 and 7.24 — a spread
    of about 3 % of its range, and not even monotone — while within a
    single trial it moves over a factor of two as the colony converges.
    It is therefore a poor volatility detector and a direct measure of
    stagnation, which is what it is for: it answers "should I explore
    *now*", not "how much is the world changing".

    That distinction matters for interpreting the comparison.  A signal
    that fails to track churn is not thereby broken; it is broken only if
    it fails to track the thing it claims to.

    It is also the only signal that says nothing at all when the arm it
    watches exposes no branching telemetry, in which case it holds at its
    neutral reading and the controller sees no pressure.
    """

    name = "lambda_branch"
    explore_direction = -1.0

    def observe(self, obs: StepObservation) -> None:
        reading = obs.probe.get("lambda_branch")
        if reading is not None:
            self._history.append(float(reading))


#: Signal constructors, keyed by the name used in config.
SIGNALS = {
    "edge_ratio": EdgeRatioSignal,
    "volatility": VolatilitySignal,
    "lambda_branch": LambdaBranchingSignal,
}


def make_signal(kind: str, window: int = 10) -> Signal:
    """Construct a signal by name.

    Args:
        kind: A key of :data:`SIGNALS`.
        window: Rolling-window length.

    Returns:
        The signal.

    Raises:
        KeyError: If ``kind`` is not registered.
    """
    if kind not in SIGNALS:
        raise KeyError(f"unknown signal {kind!r}; registered: {sorted(SIGNALS)}")
    return SIGNALS[kind](window)
