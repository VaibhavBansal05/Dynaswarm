"""What a policy is allowed to know.

Constructing an :class:`AllocationObservation` is the **only** channel by
which an allocation policy learns anything about the world.  That makes
this module the enforcement point for both Layer 1 invariants, and both
are pinned by tests rather than asserted in prose:

**I2 — every field derives from state at t' <= t.**  If anything leaks in
from ``t+1`` the entire thesis is reading the future.  F1 was exactly
this defect one layer down: ``events_at`` returned ``schedule[t]``, the
recency signal fired a step early, and every recency-driven result the
project had was voided.

**I1 — no field derives from the oracle.**  An earlier draft of §7.2
carried ``excess_last_step``.  Excess is ``cost / optimum - 1``, so it is
computed from the oracle's answer: a policy that knows its own excess
knows how far from optimal it currently is, which no deployed router
does, and "buy PSO when excess is high" would be a rule trained on
oracle knowledge.  It was removed and replaced by three fields of
**self-knowledge** — ``own_cost``, ``own_cost_delta`` and
``path_invalidated`` — all of which a real routing system has and none
of which needs the optimum.

``own_cost_delta`` is confounded by the graph itself becoming cheaper or
dearer.  That is accepted rather than corrected, because correcting it
would require knowing what the graph did to the optimum, and a deployed
system faces the same confound.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

__all__ = ["AllocationObservation", "observe"]


@dataclass(frozen=True)
class AllocationObservation:
    """One step's view of the world, as a policy sees it (§7.2).

    Frozen because a policy must not be able to edit its own inputs and
    hand the mutated object to the next policy in a comparison.

    Attributes:
        t: Timestep this observation describes.
        recency: ``1.0`` on a disruption step, decaying by ``decay`` each
            quiet step.  §7.3, derived from ``events_at(t)``.
        steps_since_disruption: Quiet steps since the last event.
        events_this_step: How many disruptions landed at ``t``.
        current_fraction: The split in force right now.
        budget: Evaluations granted this step.
        aco_lambda_branch: Colony stagnation, from ACO's probe.
        pso_diversity: Swarm convergence, from PSO's probe.
        own_cost: Cost of **this arm's** current best.  Not the optimum,
            and not a ratio to it.
        own_cost_delta: Change in ``own_cost`` since the previous step.
        path_invalidated: Did this arm's incumbent path break at ``t``?
    """

    t: int
    recency: float
    steps_since_disruption: int
    events_this_step: int
    current_fraction: float
    budget: int
    aco_lambda_branch: float
    pso_diversity: float
    own_cost: float | None
    own_cost_delta: float | None
    path_invalidated: bool


def observe(
    t: int,
    events_this_step: int,
    current_fraction: float,
    budget: int,
    probe: Mapping[str, float],
    own_cost: float | None,
    previous_cost: float | None,
    path_invalidated: bool,
    recency: float,
    steps_since_disruption: int,
) -> AllocationObservation:
    """Assemble the observation for one step.

    Every argument is a quantity the caller already holds about ``t`` or
    earlier.  Nothing is fetched here — in particular nothing is computed
    from a :mod:`dynaswarm.core.oracle` call, which is what lets the
    oracle be made genuinely unreachable while this still works.

    Args:
        t: Timestep.
        events_this_step: Disruptions that produced state ``t``.
        current_fraction: Split in force.
        budget: Evaluations for the step.
        probe: The arm's own telemetry.
        own_cost: This arm's incumbent cost, or ``None`` if it has none.
        previous_cost: The same figure at ``t-1``.
        path_invalidated: Whether the incumbent broke.
        recency: §7.3's decayed disruption signal.
        steps_since_disruption: Quiet steps since the last event.

    Returns:
        The frozen observation.
    """
    delta = None
    if own_cost is not None and previous_cost is not None:
        delta = own_cost - previous_cost
    return AllocationObservation(
        t=t,
        recency=recency,
        steps_since_disruption=steps_since_disruption,
        events_this_step=events_this_step,
        current_fraction=current_fraction,
        budget=budget,
        aco_lambda_branch=float(probe.get("aco_lambda_branch", 0.0)),
        pso_diversity=float(probe.get("pso_diversity", 0.0)),
        own_cost=own_cost,
        own_cost_delta=delta,
        path_invalidated=path_invalidated,
    )
