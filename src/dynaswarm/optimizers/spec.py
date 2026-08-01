"""Typed, total parameter binding.

A tunable parameter that is recorded but never read is indistinguishable,
in a decision log, from one that is doing useful work: the log shows a
value changing either way.  Since the whole project turns on whether
adapting parameters helps, a silently inert parameter would not merely be
a bug — it would invalidate the result while leaving it looking healthy.

Two rules prevent that:

* every optimizer declares its tunables in a ``PARAM_SPEC`` table, and
  :func:`bind` rejects any name absent from it, so a typo raises instead
  of being absorbed;
* :func:`bind` returns a complete vector — every declared name present,
  clamped into range — so ``apply`` can assert it consumed all of them.

Liveness itself is enforced by a test that drives each parameter to both
bounds and requires the resulting search trajectories to differ.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

__all__ = ["ParamSpec", "bind", "defaults", "clamp"]


@dataclass(frozen=True)
class ParamSpec:
    """Declared range and meaning of one tunable.

    Attributes:
        default: Value used when none is supplied.
        lo: Inclusive lower bound.
        hi: Inclusive upper bound.
        integer: Round to the nearest integer on binding.
        doc: What the parameter controls.
    """

    default: float
    lo: float
    hi: float
    integer: bool = False
    doc: str = ""

    def __post_init__(self) -> None:
        if self.lo > self.hi:
            raise ValueError(f"lo {self.lo} exceeds hi {self.hi}")
        if not (self.lo <= self.default <= self.hi):
            raise ValueError(f"default {self.default} outside [{self.lo}, {self.hi}]")


def clamp(spec: ParamSpec, value: float) -> float:
    """Coerce ``value`` into ``spec``'s range.

    Args:
        spec: Declared range.
        value: Proposed value.

    Returns:
        The clamped value, rounded if the spec is integral.
    """
    out = min(max(float(value), spec.lo), spec.hi)
    return float(round(out)) if spec.integer else out


def defaults(table: Mapping[str, ParamSpec]) -> dict[str, float]:
    """Return the default vector for a spec table."""
    return {name: spec.default for name, spec in table.items()}


def bind(
    table: Mapping[str, ParamSpec], values: Mapping[str, float]
) -> dict[str, float]:
    """Validate ``values`` against ``table`` and return a complete vector.

    Args:
        table: The optimizer's ``PARAM_SPEC``.
        values: Proposed values; may be partial.

    Returns:
        Every declared name, clamped into range, with unspecified names
        left at their defaults.

    Raises:
        KeyError: If ``values`` contains a name the optimizer does not
            declare.  Silently ignoring it would let a controller believe
            it was tuning something that does not exist.
    """
    unknown = set(values) - set(table)
    if unknown:
        raise KeyError(
            f"unknown parameter(s) {sorted(unknown)}; declared: {sorted(table)}"
        )
    out = defaults(table)
    for name, value in values.items():
        out[name] = clamp(table[name], value)
    return out
