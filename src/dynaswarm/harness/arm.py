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
    """

    name: str
    family: str
    optimizer: Optimizer
    metered: bool = True


@dataclass(frozen=True)
class ArmSpec:
    """How to build one arm.

    Attributes:
        family: Random-stream key, declared here rather than discovered
            from an instance so the stream can be addressed before the
            optimizer exists.
        build: Constructs the optimizer.
        metered: Whether the arm competes under the shared budget.
    """

    family: str
    build: Callable[[GraphView, int, int, np.random.Generator], Optimizer]
    metered: bool = True


#: Registry of arm specifications, keyed by the name used in config.
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
}


def build_arms(
    names: list[str],
    view: GraphView,
    source: int,
    target: int,
    root_seed: int,
    trial: int,
) -> list[Arm]:
    """Construct the requested arms with independent random streams.

    Args:
        names: Arm names, each a key of :data:`ARM_BUILDERS`.
        view: Initial graph state.
        source: Start node.
        target: Goal node.
        root_seed: Experiment seed.
        trial: Trial index.

    Returns:
        The arms, in the order requested.

    Raises:
        KeyError: If a name is not registered.
        ValueError: If a name is repeated, which would make results
            ambiguous once written to a table keyed by arm.
    """
    if len(set(names)) != len(names):
        raise ValueError(f"duplicate arm names: {names}")

    arms: list[Arm] = []
    for name in names:
        if name not in ARM_BUILDERS:
            raise KeyError(f"unknown arm {name!r}; registered: {sorted(ARM_BUILDERS)}")
        spec = ARM_BUILDERS[name]
        rng = stream(root_seed, "trial", trial, "arm", spec.family, "search")
        arms.append(
            Arm(
                name=name,
                family=spec.family,
                optimizer=spec.build(view, source, target, rng),
                metered=spec.metered,
            )
        )
    return arms
