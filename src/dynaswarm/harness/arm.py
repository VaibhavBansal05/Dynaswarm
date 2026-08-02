"""One competitor in a trial.

An arm bundles an optimizer with the identity under which its results are
recorded.  The distinction between :attr:`Arm.name` and
:attr:`Arm.family` carries real weight: the *family* keys the random
stream, so two arms that differ only in whether a controller is active
draw identical randomness and can diverge for exactly one reason.
Keying on the name instead would give them different bits and confound
the comparison with noise.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from dynaswarm.config import ControlCfg
from dynaswarm.control.controllers import (
    Controller,
    IncrementalController,
    NullController,
    make_controller,
)
from dynaswarm.control.signals import Signal, make_signal
from dynaswarm.core.graphview import GraphView
from dynaswarm.core.rng import stream
from dynaswarm.optimizers.aco import ACO
from dynaswarm.optimizers.astar import AStar
from dynaswarm.optimizers.protocol import Optimizer

__all__ = ["Arm", "build_arms", "ARM_BUILDERS"]


@dataclass
class Arm:
    """An optimizer plus its reporting identity.

    Attributes:
        name: Label used in results; unique within a trial.
        family: Random-stream key.  Arms sharing a family are fed
            identical bits, which is what makes an ablation between them
            attributable to the thing that differs.
        optimizer: The search itself.
        metered: Whether the arm competes under the shared evaluation
            budget.  Exact methods are recorded but not budget-limited,
            since they can neither use a larger allowance nor return a
            usable partial answer under a smaller one.
        signal: What this arm senses.
        controller: How it responds to what it senses.
    """

    name: str
    family: str
    optimizer: Optimizer
    metered: bool = True
    signal: Signal | None = None
    controller: Controller | None = None


@dataclass(frozen=True)
class ArmSpec:
    """How to build one arm.

    Attributes:
        family: Random-stream key, declared here rather than discovered
            from an instance so the stream can be addressed before the
            optimizer exists.
        build: Constructs the optimizer.
        metered: Whether the arm competes under the shared budget.
        signal: Name of the signal to sense, or ``None`` for arms that
            do not adapt.
        controller: Name of the controller, or ``None``.
    """

    family: str
    build: Callable[[GraphView, int, int, np.random.Generator], Optimizer]
    metered: bool = True
    signal: str | None = None
    controller: str | None = None


#: Registry of arm specifications, keyed by the name used in config.
#:
#: ``aco_fixed`` and ``aco_adaptive`` share a family, and therefore a
#: random stream.  Fed identical bits and starting from identical
#: parameters, they can diverge for exactly one reason: whether the
#: controller was allowed to move anything.  That is the ablation.
ARM_BUILDERS: dict[str, ArmSpec] = {
    "astar": ArmSpec(
        family="astar",
        build=lambda view, s, t, rng: AStar(view, s, t, heuristic=True),
        metered=False,
    ),
    "aco": ArmSpec(
        family="aco",
        build=lambda view, s, t, rng: ACO(view, s, t, rng),
    ),
    "aco_fixed": ArmSpec(
        family="aco_controlled",
        build=lambda view, s, t, rng: ACO(view, s, t, rng),
        signal="volatility",
        controller="none",
    ),
    "aco_adaptive": ArmSpec(
        family="aco_controlled",
        build=lambda view, s, t, rng: ACO(view, s, t, rng),
        signal="volatility",
        controller="incremental",
    ),
}


def build_arms(
    names: list[str],
    view: GraphView,
    source: int,
    target: int,
    root_seed: int,
    trial: int,
    control: ControlCfg | None = None,
) -> list[Arm]:
    """Construct the requested arms with independent random streams.

    Args:
        names: Arm names, each a key of :data:`ARM_BUILDERS`.
        view: Initial graph state.
        source: Start node.
        target: Goal node.
        root_seed: Experiment seed.
        trial: Trial index.
        control: Signal and controller settings.  A ``signal`` named
            here overrides the arm's default, which is what lets one
            sweep compare the same ablation across all three signals.

    Returns:
        The arms, in the order requested.

    Raises:
        KeyError: If a name is not registered.
        ValueError: If a name is repeated, which would make results
            ambiguous once written to a table keyed by arm.
    """
    if len(set(names)) != len(names):
        raise ValueError(f"duplicate arm names: {names}")

    control = control or ControlCfg()
    arms: list[Arm] = []
    for name in names:
        if name not in ARM_BUILDERS:
            raise KeyError(f"unknown arm {name!r}; registered: {sorted(ARM_BUILDERS)}")
        spec = ARM_BUILDERS[name]
        rng = stream(root_seed, "trial", trial, "arm", spec.family, "search")
        optimizer = spec.build(view, source, target, rng)
        if control.fixed_params:
            # Applied to every arm alike, so an ablation's two halves
            # start from the same place and differ only in what happens
            # to them afterwards.
            optimizer.apply(
                {k: v for k, v in control.fixed_params.items() if k in optimizer.PARAM_SPEC}
            )
        arms.append(
            Arm(
                name=name,
                family=spec.family,
                optimizer=optimizer,
                metered=spec.metered,
                signal=_make_signal(spec, control),
                controller=_make_controller(spec, control),
            )
        )
    return arms


def _make_signal(spec: ArmSpec, control: ControlCfg) -> Signal | None:
    """Build the arm's signal, honouring a config-level override."""
    if spec.signal is None:
        return None
    kind = control.signal or spec.signal
    return make_signal(kind, window=control.window)


def _make_controller(spec: ArmSpec, control: ControlCfg) -> Controller | None:
    """Build the arm's controller.

    The arm's own ``controller`` decides *whether* it adapts — that is
    what distinguishes the two halves of an ablation — while the config
    supplies the settings.  A config-level kind would collapse both arms
    onto the same behaviour and destroy the comparison.
    """
    if spec.controller is None:
        return None
    if spec.controller == "none":
        return NullController()
    if spec.controller == "incremental":
        return IncrementalController(
            targets=tuple(control.targets),
            sigma=control.sigma,
            deadband=control.deadband,
            baseline_alpha=control.baseline_alpha,
            adapt_every=control.adapt_every,
        )
    return make_controller(spec.controller)
