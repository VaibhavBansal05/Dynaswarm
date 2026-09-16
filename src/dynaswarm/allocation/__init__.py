"""Resource allocation between the hybrid's components (§7).

Claim 3 is an allocation question, not a parameter-tuning one. The old
control layer expressed ``aco_fraction`` as just another named parameter
nudged by ``±sigma``, which could only represent a monotonic response —
so a null result would have said nothing about allocation, only about
that rule. This package replaces it: a structured observation, policies
that return a target, and a governor that is the only thing permitted to
act.
"""

from dynaswarm.allocation.governor import AllocationGovernor
from dynaswarm.allocation.observation import AllocationObservation, observe
from dynaswarm.allocation.policies import (
    POLICIES,
    AllocationPolicy,
    DirectAllocation,
    FrozenAllocation,
    IncrementalAllocation,
    ScheduledAllocation,
    make_policy,
)

__all__ = [
    "DirectAllocation",
    "AllocationGovernor",
    "AllocationObservation",
    "AllocationPolicy",
    "FrozenAllocation",
    "IncrementalAllocation",
    "POLICIES",
    "ScheduledAllocation",
    "make_policy",
    "observe",
]
