"""Allocation policies — each returns a **target** split, not a delta.

§7.2.  Returning a target rather than a ``±sigma`` nudge is what makes
non-monotonic and state-dependent policies expressible at all: the old
``IncrementalController`` could only ever walk the fraction one step up
or down, so a null result from it would have said nothing about
allocation, only about that rule.

**No policy enforces anything.**  Clamping, rate-limiting and saturation
accounting all live in :mod:`dynaswarm.allocation.governor`, so a policy
is free to propose something unsafe and the record shows both what it
wanted and what it got.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from dynaswarm.allocation.observation import AllocationObservation

__all__ = [
    "AllocationPolicy",
    "FrozenAllocation",
    "IncrementalAllocation",
    "ScheduledAllocation",
    "POLICIES",
    "make_policy",
]


@runtime_checkable
class AllocationPolicy(Protocol):
    """Turns an observation into a target ``aco_fraction``."""

    name: str

    def propose(self, obs: AllocationObservation) -> float:
        """Return the split to aim for at ``obs.t``."""
        ...

    def reset(self) -> None:
        """Discard any accumulated state."""
        ...


@dataclass
class FrozenAllocation:
    """Never moves the split — the ablation twin.

    A policy object rather than an absent one, so the fixed and adaptive
    arms run identical code paths and any divergence between them is
    attributable to the policy being permitted to move, and to nothing
    else.
    """

    name: str = "frozen"

    def propose(self, obs: AllocationObservation) -> float:
        return obs.current_fraction

    def reset(self) -> None:
        return None


@dataclass
class IncrementalAllocation:
    """The ±sigma pressure-against-baseline rule, preserved exactly.

    Carried over from ``IncrementalController`` unchanged so results
    remain comparable across the restructure.  It compares the signal
    against its own running baseline rather than an absolute threshold,
    because a threshold placed outside a signal's attainable range
    silently freezes the policy.

    Attributes:
        sigma: Step size per adaptation cycle.
        deadband: Pressure magnitude below which nothing moves.
        baseline_alpha: Weight of the newest reading in the baseline.
        adapt_every: Timesteps between adaptation cycles.
    """

    sigma: float = 0.001
    deadband: float = 0.0
    baseline_alpha: float = 0.05
    adapt_every: int = 1
    name: str = "incremental"
    _baseline: float | None = field(default=None, init=False, repr=False)

    def propose(self, obs: AllocationObservation) -> float:
        reading = obs.recency
        if self._baseline is None:
            # The first reading defines the baseline; acting on it would
            # mean reacting to the absence of history.
            self._baseline = reading
            return obs.current_fraction

        pressure = reading - self._baseline
        self._baseline += self.baseline_alpha * pressure
        if obs.t % self.adapt_every != 0 or abs(pressure) <= self.deadband:
            return obs.current_fraction

        # Right after a disruption the trail is the least trustworthy
        # thing in the system, so rising recency buys the memoryless
        # component more of the budget — the sign carried over from
        # EXPLORE_SIGN's `aco_fraction: -1`.
        step = self.sigma if pressure > 0 else -self.sigma
        return obs.current_fraction - step

    def reset(self) -> None:
        self._baseline = None


@dataclass
class ScheduledAllocation:
    """An open-loop timetable. Ignores everything but ``t``.

    **The honest control for feedback itself**: if a schedule matches a
    sensing policy, what helped was *varying* the split, not sensing
    anything.

    The defaults **must sweep**.  Its predecessor was constructed with
    ``start == end == 1.0`` (F7), so it varied nothing while logging
    itself as an active schedule — producing results identical to the
    frozen arm and a false null on the one arm whose job is to falsify
    the control story.  ``test_scheduled_allocation_actually_varies_at_
    default_construction`` holds the defaults to Entry 005's bar: a
    control that does not vary is not a control.

    Attributes:
        start: Target fraction at ``t = 0``.
        end: Target fraction at ``horizon - 1``.
        horizon: Timesteps over which the sweep completes.
    """

    start: float = 0.8
    end: float = 0.2
    horizon: int = 60
    name: str = "scheduled"

    def propose(self, obs: AllocationObservation) -> float:
        through = min(max(obs.t / max(self.horizon - 1, 1), 0.0), 1.0)
        return self.start + (self.end - self.start) * through

    def reset(self) -> None:
        return None


#: Policy constructors, keyed by the name used in config.
#:
#: ``LearnedAllocation`` is deliberately absent. §7.2 registers it, but
#: D7 and O2 defer it to Phase 4 and make it conditional on mentor
#: sign-off, and it carries its own budget conversation.
POLICIES = {
    "frozen": FrozenAllocation,
    "incremental": IncrementalAllocation,
    "scheduled": ScheduledAllocation,
}


def make_policy(kind: str, **kwargs: object) -> AllocationPolicy:
    """Construct a policy by name.

    Raises:
        KeyError: If ``kind`` is not registered — never a silent default,
            which is how F7's predecessor came to exist.
    """
    if kind not in POLICIES:
        raise KeyError(f"unknown allocation policy {kind!r}; registered: {sorted(POLICIES)}")
    return POLICIES[kind](**kwargs)  # type: ignore[arg-type]
