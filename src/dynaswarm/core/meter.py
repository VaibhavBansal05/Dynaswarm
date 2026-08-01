"""The work counter.

Every arm is granted the same per-timestep budget, denominated in
*candidate path constructions* rather than iterations.  The distinction
matters because an iteration is not a fixed amount of work: an ACO
iteration costs one construction per ant, and a PSO iteration one per
particle, so equalising iterations hands a larger population
proportionally more CPU.

That becomes actively misleading once population size is something the
controller tunes, because the controller can then buy itself an advantage
that looks like a better search.  Counting constructions closes the hole.

The meter is created by the harness and passed *into* the optimizer.  An
optimizer cannot inflate or under-report its own budget, and because
:meth:`charge` is called inside the construction routine itself, a test
can assert that the number of charges equals the number of times that
routine ran.
"""

from __future__ import annotations

__all__ = ["EvaluationMeter"]


class EvaluationMeter:
    """A bounded allowance of candidate-path constructions.

    Args:
        budget: Constructions this arm may spend.

    Raises:
        ValueError: If ``budget`` is negative.
    """

    __slots__ = ("budget", "spent")

    def __init__(self, budget: int) -> None:
        if budget < 0:
            raise ValueError(f"budget must be non-negative, got {budget}")
        self.budget = int(budget)
        self.spent = 0

    def charge(self, amount: int = 1) -> None:
        """Record ``amount`` constructions as spent."""
        self.spent += amount

    @property
    def exhausted(self) -> bool:
        """Whether the allowance is used up."""
        return self.spent >= self.budget

    @property
    def remaining(self) -> int:
        """Constructions still available, never negative."""
        return max(0, self.budget - self.spent)

    def __repr__(self) -> str:
        return f"EvaluationMeter(spent={self.spent}/{self.budget})"
