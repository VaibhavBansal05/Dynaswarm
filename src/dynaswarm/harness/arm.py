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
from inspect import signature

import numpy as np

from dynaswarm.allocation.governor import AllocationGovernor
from dynaswarm.allocation.policies import POLICIES, make_policy
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
from dynaswarm.optimizers.hybrid import Hybrid
from dynaswarm.optimizers.protocol import Optimizer
from dynaswarm.optimizers.pso import PSO

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
        controller: How it responds to what it senses — parameter
            adaptation, for Claim 2's evidence set (§8).
        governor: How it responds by *allocating* — the budget split
            between colony and swarm, for Claim 3 (§7.2).  An arm carries
            one or the other, never both: they are different claims and
            an arm doing both would make neither attributable.
    """

    name: str
    family: str
    optimizer: Optimizer
    metered: bool = True
    signal: Signal | None = None
    controller: Controller | None = None
    governor: AllocationGovernor | None = None


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
        policy: Name of the allocation policy, or ``None``.  Mutually
            exclusive with ``controller``.
    """

    family: str
    build: Callable[[GraphView, int, int, np.random.Generator], Optimizer]
    metered: bool = True
    signal: str | None = None
    controller: str | None = None
    policy: str | None = None


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
    "pso": ArmSpec(
        family="pso",
        build=lambda view, s, t, rng: PSO(view, s, t, rng),
    ),
    "hybrid": ArmSpec(
        family="hybrid",
        build=lambda view, s, t, rng: Hybrid(view, s, t, rng),
    ),
    # The allocation ablation.  Both hold the same optimizer and the same
    # stream; one may shift the budget between colony and swarm, the
    # other may not.
    "hybrid_fixed": ArmSpec(
        family="hybrid_controlled",
        build=lambda view, s, t, rng: Hybrid(view, s, t, rng),
        signal="recency",
        policy="frozen",
    ),
    "hybrid_adaptive": ArmSpec(
        family="hybrid_controlled",
        build=lambda view, s, t, rng: Hybrid(view, s, t, rng),
        signal="recency",
        policy="incremental",
    ),
    # The honest control for feedback itself (§7.2): an open-loop
    # timetable that ignores the world entirely.  If it matches the
    # adaptive arm, what helped was *varying* the split, not sensing —
    # and it cannot play that role from outside the registry.
    "hybrid_scheduled": ArmSpec(
        family="hybrid_controlled",
        build=lambda view, s, t, rng: Hybrid(view, s, t, rng),
        signal="recency",
        policy="scheduled",
    ),
    # The rule the problem calls for (segment Y). Same family, same
    # signal, same starting split as the incremental arm — the ONLY
    # difference is the shape of the response, which is what makes a gap
    # between the two attributable to that and nothing else.
    "hybrid_direct": ArmSpec(
        family="hybrid_controlled",
        build=lambda view, s, t, rng: Hybrid(view, s, t, rng),
        signal="recency",
        policy="direct",
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
                governor=_make_governor(spec, control),
            )
        )
    return arms


def _make_signal(spec: ArmSpec, control: ControlCfg) -> Signal | None:
    """Build the arm's signal, honouring a config-level override."""
    if spec.signal is None:
        return None
    kind = control.signal or spec.signal
    return make_signal(kind, window=control.window)


def _make_governor(spec: ArmSpec, control: ControlCfg) -> AllocationGovernor | None:
    """Build the arm's allocation governor, if it allocates.

    The policy is named by the arm, not by the config — that is what
    distinguishes the two halves of the ablation. A config-level policy
    would collapse both arms onto the same behaviour and destroy the
    comparison.
    """
    if spec.policy is None:
        return None
    # `allocation_sigma`, not `sigma`: the latter belongs to the rho
    # controller and Claim 2. Asked of the policy rather than matched
    # against a list of names — `frozen` has no step size by definition
    # and `scheduled` sets its own from its endpoints, and a hardcoded
    # name list would silently stop covering the next policy added.
    accepts = signature(POLICIES[spec.policy]).parameters
    kwargs = (
        {"sigma": control.allocation_sigma} if "sigma" in accepts else {}
    )
    return AllocationGovernor(
        policy=make_policy(spec.policy, **kwargs),
        sigma_max=control.sigma_max,
        fraction=control.initial_fraction,
    )


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
