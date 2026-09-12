"""Enforcement — the only thing that touches the optimizer.

§7.2 puts every guarantee here rather than in the policies, so a policy
is free to be wrong and the damage is bounded in one auditable place.

**Why proposed and applied are both recorded.**  A policy pressing hard
against a clamp and a policy proposing exactly the clamped value are
indistinguishable from the applied series alone, and they mean opposite
things about whether the policy is working.  One number cannot carry
both, so two are kept.

**Why saturation is a check and not an instruction.**  The RUNBOOK used
to ask the operator to verify the split moved and did not pin to a
bound.  A check that lives in a document is a check that eventually is
not run — Phase 2's containment lesson, in a new place.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from dynaswarm.allocation.observation import AllocationObservation
from dynaswarm.allocation.policies import AllocationPolicy

__all__ = ["AllocationGovernor", "FRACTION_LOW", "FRACTION_HIGH", "MAX_AT_BOUND"]

#: The split may never reach either extreme: at 0 or 1 one component
#: receives nothing and the hybrid silently becomes a single solver.
FRACTION_LOW = 0.05
FRACTION_HIGH = 0.95

#: A reported allocation run may spend at most this fraction of its steps
#: sitting at a bound (§7.2).
#:
#: **Measured in segment 21 (T6), and the measurement says something the
#: number alone does not.**  Across 16 runs — four scenarios x four seeds
#: — the observed time-at-bound was 0.0% in every single one.  Not close
#: to 20%: zero.
#:
#: That is not the check passing comfortably, it is the check being
#: unable to fail.  ``IncrementalAllocation`` steps by ``sigma = 0.001``
#: from a start of 0.5, so reaching 0.05 needs 450 consecutive steps in
#: one direction and scenarios run 60.  For this policy, at this step
#: size, the clause is arithmetically unreachable.
#:
#: It is kept rather than tuned to fit, because the two facts point the
#: same way: 20% is the right *kind* of limit and nothing currently
#: exercises it.  It binds on ``ScheduledAllocation``, whose timetable is
#: free to end anywhere its endpoints are set to, and it is the guard
#: that matters most for ``LearnedAllocation``, which has no built-in
#: reason to stay near the middle.  Lowering it to fit today's runs would
#: be fitting a threshold to the one policy that cannot trip it.
#:
#: **What must not be claimed: that a run passed this check is evidence
#: the split stayed healthy.**  For the incremental arm it is evidence of
#: nothing at all.  The live half of ``reportable()`` is the ``distinct``
#: clause, which does fail — every static-scenario run fails it, because
#: with no disruptions recency never moves and the policy correctly
#: never adapts.
MAX_AT_BOUND = 0.20


@dataclass
class AllocationGovernor:
    """Wraps a policy and enforces §7.2's limits on what it proposes.

    Attributes:
        policy: The policy being governed.
        sigma_max: Largest change permitted in one step.
        fraction: The split currently in force.
        proposed: What the policy asked for, per step.
        applied: What was actually adopted, per step.
    """

    policy: AllocationPolicy
    sigma_max: float = 0.05
    fraction: float = 0.5
    proposed: list[float] = field(default_factory=list)
    applied: list[float] = field(default_factory=list)

    def step(self, obs: AllocationObservation) -> float:
        """Take one proposal, bound it, record both, adopt it."""
        want = float(self.policy.propose(obs))
        self.proposed.append(want)

        delta = want - self.fraction
        if abs(delta) > self.sigma_max:
            want = self.fraction + (self.sigma_max if delta > 0 else -self.sigma_max)
        self.fraction = min(max(want, FRACTION_LOW), FRACTION_HIGH)
        self.applied.append(self.fraction)
        return self.fraction

    def reset(self) -> None:
        self.policy.reset()
        self.proposed.clear()
        self.applied.clear()

    def saturation(self) -> dict[str, float]:
        """How much of the run sat at a bound, and whether it moved at all.

        Returns:
            ``moved`` — more than one distinct applied value.
            ``at_bound`` — fraction of steps at either limit.
            ``distinct`` — how many different splits were adopted.
            ``clipped`` — steps where the proposal was not adopted as
            asked, which is the figure the applied series alone hides.
        """
        if not self.applied:
            return {"moved": 0.0, "at_bound": 0.0, "distinct": 0.0, "clipped": 0.0}
        at_bound = sum(
            1 for v in self.applied if v <= FRACTION_LOW or v >= FRACTION_HIGH
        )
        clipped = sum(
            1 for want, got in zip(self.proposed, self.applied, strict=True)
            if abs(want - got) > 1e-12
        )
        distinct = len(set(self.applied))
        return {
            "moved": float(distinct > 1),
            "at_bound": at_bound / len(self.applied),
            "distinct": float(distinct),
            "clipped": clipped / len(self.applied),
        }

    def reportable(self) -> bool:
        """Whether this run may be reported at all (§7.2).

        A run whose split never moved measured nothing about allocation,
        and one pinned to a bound measured the bound rather than the
        policy. Automated here so it cannot go unrun.
        """
        stats = self.saturation()
        return bool(stats["moved"]) and stats["at_bound"] < MAX_AT_BOUND
