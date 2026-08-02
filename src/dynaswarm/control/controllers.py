"""How the controller reacts.

A controller turns a sensed reading into a parameter change.  Separating
this from sensing is what allows the two choices to be ablated
independently: which signal you watch and how you respond to it are
different decisions, and conflating them makes it impossible to say
which one a result is about.

Increments, not presets
-----------------------
Adaptation moves each target parameter by a fixed small step per cycle
rather than jumping to a regime-specific value.  A jump discards
accumulated state: raising evaporation from 0.08 to 0.35 in one cycle
erases the colony's memory wholesale, which is a large intervention
justified by a single noisy reading.  Small steps let evidence
accumulate, and mean a misread signal costs little.  This follows
Mavrovouniotis & Yang, who use sigma = 0.001 and warn that larger steps
"destroy information".

Baselines, not thresholds
-------------------------
The controller compares the signal against *its own running baseline*
rather than an absolute threshold.  Because the three signals live on
different scales, any fixed threshold would have to be justified
separately for each — and a threshold placed outside a signal's attainable
range silently freezes the controller, which is the failure this design
exists to preclude.  Asking "is this higher than usual?" needs no such
constant.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from dynaswarm.control.signals import Signal

__all__ = [
    "Controller",
    "NullController",
    "IncrementalController",
    "PrescheduledController",
    "make_controller",
    "CONTROLLERS",
    "EXPLORE_SIGN",
]

#: Which direction moves each parameter toward exploration.
#:
#: Faster evaporation forgets sooner, so a higher ``rho`` explores more.
#: A higher ``alpha`` trusts accumulated trail more, so it exploits.  A
#: higher ``beta`` leans harder on immediate edge cost, which is greedy
#: rather than exploratory.  More ants sample more of the graph per
#: iteration, but under a fixed evaluation budget they also buy fewer
#: iterations, so the sign is genuinely ambiguous and it is left out.
EXPLORE_SIGN: Mapping[str, float] = {
    "rho": +1.0,
    "alpha": -1.0,
    "beta": -1.0,
}


@runtime_checkable
class Controller(Protocol):
    """Turns a sensed reading into proposed parameter values."""

    name: str

    def propose(
        self, signal: Signal, current: Mapping[str, float], t: int
    ) -> dict[str, float]:
        """Return the parameter vector to adopt at timestep ``t``."""
        ...


@dataclass
class NullController:
    """Never changes anything — the ablation arm.

    Deliberately a controller rather than an absence of one: the adaptive
    and frozen arms then run the same code path, differing only in which
    controller object they hold, so any divergence between them is
    attributable to adaptation and to nothing else.
    """

    name: str = "none"

    def propose(
        self, signal: Signal, current: Mapping[str, float], t: int
    ) -> dict[str, float]:
        return dict(current)


@dataclass
class IncrementalController:
    """Nudges parameters by +/- sigma according to sensed pressure.

    Attributes:
        targets: Parameters to adapt.  Starting with evaporation alone is
            deliberate: adapting several at once makes it impossible to
            attribute an effect to any of them.
        sigma: Step size per adaptation cycle.
        deadband: Pressure magnitude below which nothing moves, so the
            parameter does not jitter on noise alone.
        baseline_alpha: Weight of the newest reading in the running
            baseline the signal is compared against.
        adapt_every: Timesteps between adaptation cycles.
    """

    targets: tuple[str, ...] = ("rho",)
    sigma: float = 0.001
    deadband: float = 0.0
    baseline_alpha: float = 0.05
    adapt_every: int = 1
    name: str = "incremental"
    _baseline: float | None = field(default=None, init=False, repr=False)

    def propose(
        self, signal: Signal, current: Mapping[str, float], t: int
    ) -> dict[str, float]:
        reading = signal.explore_direction * signal.value()

        if self._baseline is None:
            # The first reading defines the baseline; acting on it would
            # mean reacting to the absence of history.
            self._baseline = reading
            return dict(current)

        pressure = reading - self._baseline
        self._baseline += self.baseline_alpha * pressure

        if t % self.adapt_every != 0 or abs(pressure) <= self.deadband:
            return dict(current)

        step = self.sigma if pressure > 0 else -self.sigma
        proposed = dict(current)
        for name in self.targets:
            sign = EXPLORE_SIGN.get(name, 1.0)
            if name in proposed:
                proposed[name] = proposed[name] + sign * step
        return proposed


@dataclass
class PrescheduledController:
    """Varies parameters on a fixed timetable, ignoring the signal.

    Included because it is the honest control for feedback itself.  If an
    open-loop schedule matches a signal-driven controller, then what
    helped was varying the parameter at all, not sensing anything — and
    that is a conclusion worth being able to reach.

    Attributes:
        targets: Parameters to sweep.
        start: Multiple of the parameter's initial value at ``t = 0``.
        end: Multiple at the final timestep.
        horizon: Timesteps over which the sweep completes.
    """

    targets: tuple[str, ...] = ("rho",)
    start: float = 1.0
    end: float = 1.0
    horizon: int = 60
    name: str = "prescheduled"
    _initial: dict[str, float] = field(default_factory=dict, init=False, repr=False)

    def propose(
        self, signal: Signal, current: Mapping[str, float], t: int
    ) -> dict[str, float]:
        for name in self.targets:
            self._initial.setdefault(name, float(current.get(name, 0.0)))

        fraction = min(max(t / max(self.horizon - 1, 1), 0.0), 1.0)
        multiplier = self.start + (self.end - self.start) * fraction

        proposed = dict(current)
        for name in self.targets:
            if name in proposed:
                proposed[name] = self._initial[name] * multiplier
        return proposed


#: Controller constructors, keyed by the name used in config.
CONTROLLERS = {
    "none": NullController,
    "incremental": IncrementalController,
    "prescheduled": PrescheduledController,
}


def make_controller(kind: str, **kwargs: object) -> Controller:
    """Construct a controller by name.

    Args:
        kind: A key of :data:`CONTROLLERS`.
        **kwargs: Forwarded to the controller.

    Returns:
        The controller.

    Raises:
        KeyError: If ``kind`` is not registered.
    """
    if kind not in CONTROLLERS:
        raise KeyError(f"unknown controller {kind!r}; registered: {sorted(CONTROLLERS)}")
    return CONTROLLERS[kind](**kwargs)  # type: ignore[arg-type]
