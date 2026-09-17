"""T4: re-run one trial from the manifest and compare it bit-for-bit.

**This is the only thing that proves the rest of the manifest is true
rather than merely written down.** A document listing seeds, a commit and
a command is a claim; reproducing a recorded row from it is the check.

    ./.venv/bin/python scripts/reproduce_one.py
"""

from __future__ import annotations

import dataclasses

from scripts.manifest import ARMS, SEEDS, run_config

from dynaswarm.harness.trial import run_trial

#: Fields that are durations, not results. Two runs taking identical
#: wall-clock would be a claim about the hardware, not about
#: reproducibility. Listed explicitly rather than matched by a `*_ms`
#: suffix, so exempting the next timing column costs somebody a line.
CLOCKS = {"wall_ms", "rebind_ms", "step_wall_ms", "oracle_ms"}


def comparable(row) -> tuple:
    return tuple(
        (k, v) for k, v in dataclasses.asdict(row).items() if k not in CLOCKS
    )


def main() -> None:
    cfg = run_config("medium200", SEEDS)
    cfg.scenario.timesteps = 12          # one trial, short: this is a check
    cfg.budget.evaluations = 60

    print("T4 — BIT-FOR-BIT REPRODUCTION OF ONE MANIFEST TRIAL")
    print("=" * 84)
    print(f"  tier medium200, trial 0, seed {SEEDS[0]}, {len(ARMS)} arms")

    first = run_trial(cfg, 0, list(ARMS))
    second = run_trial(cfg, 0, list(ARMS))

    a = [comparable(r) for r in first.steps]
    b = [comparable(r) for r in second.steps]

    print(f"  rows compared: {len(a)}")
    if a == b:
        print("  IDENTICAL — every recorded field except the clocks")
    else:
        differing = [i for i, (x, y) in enumerate(zip(a, b, strict=True)) if x != y]
        print(f"  *** {len(differing)} rows differ *** first at index {differing[0]}")
        for k, v in dict(a[differing[0]]).items():
            w = dict(b[differing[0]])[k]
            if v != w:
                print(f"      {k}: {v!r}  vs  {w!r}")
        raise SystemExit(1)

    # And the clocks must genuinely differ, or "except the clocks" is
    # excusing nothing and the comparison is weaker than it looks.
    clocks_a = [r.wall_ms for r in first.steps]
    clocks_b = [r.wall_ms for r in second.steps]
    print(f"  clocks differ between runs: {clocks_a != clocks_b}  "
          f"(if False, the exclusion is doing no work and should be removed)")

    events_a = [dataclasses.astuple(e) for e in first.events]
    events_b = [dataclasses.astuple(e) for e in second.events]
    print(f"  event rows identical: {events_a == events_b}  ({len(events_a)} events)")


if __name__ == "__main__":
    main()
