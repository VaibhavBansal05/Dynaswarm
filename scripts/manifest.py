"""The frozen experiment manifest (segment 23).

After this segment nothing about the experiment changes. The manifest's
job is to be enough for **a stranger with only this repository** to
reproduce both runs exactly — so every field here is a fact, not a rule.
Seeds are listed rather than described: a range is a rule someone can
mis-apply, a list is a fact they cannot.

    ./.venv/bin/python scripts/manifest.py --write
    ./.venv/bin/python scripts/manifest.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from dynaswarm.config import BudgetCfg, Config, ExperimentCfg, GraphCfg, ScenarioCfg
from dynaswarm.core import generate as g
from dynaswarm.core.oracle import shortest_path
from dynaswarm.core.rng import stream

ROOT = Path(__file__).resolve().parents[1]

#: Every arm in the experiment. Ten, not nine — Entry 024's prose says
#: "all nine" while its own list names ten. The list is the fact and the
#: count is the slip; flagged in the segment's findings rather than
#: silently resolved either way.
ARMS = [
    "astar", "aco", "pso", "hybrid",
    "hybrid_fixed", "hybrid_adaptive", "hybrid_scheduled", "hybrid_direct",
    "aco_fixed", "aco_adaptive",
]

#: **150 seeds, listed.** Raised from 100 in Entry 031, and the reason is
#: the multiplicity correction rather than the effect size.
#:
#: Holm runs across every tested cell of the 9 x 4 grid, so the strictest
#: threshold is 0.05/36 rather than 0.05/9. That costs power, and the
#: answer taken was to **spend compute rather than argue the
#: denominator**: from the pilot's paired SD of 2.132pp against an
#: observed 0.787pp effect, 100 seeds left roughly 75% power under the
#: grid-wide correction and 150 restores it to about 90%.
SEEDS = list(range(1000, 1150))

#: **Four scenarios, frozen by Entry 030.** The rates are the project's
#: own presets (`model.js`: static 0.0, low 0.1, moderate 0.3, high 0.8);
#: only the display names differ, and the mapping is recorded here so
#: nobody reads these as invented numbers.
#:
#: The set exists to buy two claims a single scenario cannot produce:
#:
#: * **`calm` is the negative control.** With no disruptions, recency
#:   never fires and a recency-driven arm must not move. An effect here
#:   would mean the mechanism adds noise rather than responds to damage.
#: * **`light` -> `moderate` -> `severe` is the dose-response.** If the
#:   adaptive margin grows with disruption rate, that is far stronger
#:   than one significant difference: a spurious effect has no reason to
#:   scale with the thing it is supposed to depend on.
SCENARIOS = {
    "calm":     {"events_per_step": 0.0},   # preset `static`
    "light":    {"events_per_step": 0.1},   # preset `low`
    "moderate": {"events_per_step": 0.3},   # preset `moderate`
    "severe":   {"events_per_step": 0.8},   # preset `high`
}

#: Shared by all four. Only the event rate varies, so a difference between
#: scenarios is attributable to disruption frequency and nothing else.
SCENARIO_COMMON = {"cluster_size": 25, "timesteps": 60}


def scenario_cfg(name: str) -> dict:
    return {"name": name, **SCENARIO_COMMON, **SCENARIOS[name]}

#: Evaluations per arm per timestep. The `sigma` derivation in segment X
#: is a function of this number, so it cannot move without invalidating it.
BUDGET = 300

TIERS = {
    "medium200": {"model": "geometric", "n_nodes": 200, "density": 0.04},
    "large1000": {"model": "geometric", "n_nodes": 1000, "density": 0.04},
}

#: Job count for `joblib`. Stated because **wall-clock from a parallel run
#: is not comparable to segment Z2's single-threaded timing table**, and a
#: report that mixes them is comparing two different machines.
PARALLEL_JOBS = 8


@dataclass(frozen=True)
class Instance:
    """What one seed's world actually is, recorded before it is used.

    An instance property nobody records is gone once the run finishes
    (Entry 029). `bridge_share` is the one that matters: on some seeds a
    single bridging edge carries ~45% of the optimal route, and there the
    arms will look alike for a structural reason rather than because
    allocation does not help. Recording it per instance lets the report
    answer that challenge instead of conceding it.
    """

    seed: int
    n_nodes: int
    n_edges: int
    density: float
    optimum_t0: float | None
    route_hops: int
    bridges: int
    bridge_hops: int
    bridge_share: float


def characterise(tier: str, seed: int) -> Instance:
    """Build one instance and measure it, at t=0."""
    spec = TIERS[tier]
    cfg = GraphCfg(model=spec["model"], n_nodes=spec["n_nodes"],
                   density=spec["density"])

    view, source, target = g.build(cfg, stream(seed, "graph"))

    # Which edges `_ensure_connected` had to invent, replayed on **one**
    # stream that flows from the model call into the bridging call — the
    # way `build()` does it.
    #
    # Written first with a fresh `stream(seed, "graph")` for each, which
    # looks equivalent and is not: `_ensure_connected` consumes draws that
    # `_geometric` has already taken, so a fresh stream picks *different
    # bridge endpoints*. The COUNT is unaffected (the same components need
    # the same number of bridges), so the bug was invisible in every
    # summary except the one that mattered — it reported bridge share as
    # 0.0000 on all 100 seeds, including the two measured at ~45% in
    # segment Z3. It would have frozen that zero into the manifest, and an
    # instance property recorded wrongly is worse than one not recorded
    # at all.
    replay = stream(seed, "graph")
    raw, _ = (g._geometric(cfg, replay) if spec["model"] == "geometric"
              else g._erdos_renyi(cfg, replay))
    bridges = g._ensure_connected(set(raw), cfg.n_nodes, replay) - set(raw)

    cost, path, _ = shortest_path(view, source, target, heuristic=True)
    reachable = bool(np.isfinite(cost)) and len(path) >= 2

    bridge_hops, bridge_cost = 0, 0.0
    if reachable:
        for u, v in zip(path, path[1:], strict=False):
            if (min(u, v), max(u, v)) in bridges:
                slot = view.find_slot(int(u), int(v))
                bridge_hops += 1
                bridge_cost += float(view.weight[slot]) if slot >= 0 else 0.0

    return Instance(
        seed=seed,
        n_nodes=view.n_nodes,
        n_edges=int(view.n_active_edges),
        density=spec["density"],
        optimum_t0=float(cost) if reachable else None,
        route_hops=(len(path) - 1) if reachable else 0,
        bridges=len(bridges),
        bridge_hops=bridge_hops,
        bridge_share=(bridge_cost / cost) if reachable and cost else 0.0,
    )


#: **The primary tier, pre-registered with its condition and fallback.**
#:
#: `large1000` is the basis for all claims, because it has **zero bridging
#: edges on every instance** and is therefore free of the confound that
#: affects 40% of `medium200` instances. `medium200` is reported alongside
#: as the instrument-verified tier — everything in this project was
#: calibrated there.
#:
#: **Conditional, and the condition is measured not assumed.** A tier can
#: only be primary if all four pre-registered metrics are computable on
#: it. Three are computed from every recorded step and cannot degenerate.
#: The fourth, `mean steps to recover`, is computed only over disruptions
#: that actually damaged the arm — and that count had never been measured
#: at 1000 nodes.
#:
#: Measured in segment 23 over 10 arm-trials per cell:
#:
#:     large1000   moderate  0.40 damaged per arm-trial
#:     large1000   severe    0.20
#:     medium200   moderate  2.10
#:     medium200   severe    1.30
#:
#: **Not degenerate — about 5x thinner.** At 150 seeds that is roughly
#: 30-60 damaged events per arm per scenario against 195-315 at
#: `medium200`. Computable, and a materially weaker basis for that one
#: metric.
PRIMARY_TIER = "large1000"
FALLBACK_TIER = "medium200"

#: Minimum damaged disruptions per arm per scenario for the recovery
#: metric to be reported at a tier at all. Below this the metric is not
#: reported for that tier and the report says why — it is not quietly
#: averaged over whatever happened to be there.
#:
#: Set at 30, which is the lower end of what `large1000` is projected to
#: deliver at 150 seeds. **Chosen as a floor on evidence, not to make a
#: tier pass**: the projection is 30-60, so if the real run lands under 30
#: the metric genuinely has too little behind it and the fallback applies.
MIN_DAMAGED_FOR_RECOVERY = 30


def primary_tier_holds(damaged_by_cell: dict[tuple[str, str], float]) -> dict:
    """Decide the primary tier from the run's own data, by the rule above.

    **The counts must be PER ARM.** `MIN_DAMAGED_FOR_RECOVERY` is a
    per-arm floor, and the caller in segment 24 passed totals summed over
    ten arms — so `large1000/light` at 11.7 per arm arrived as 117 and
    cleared a floor of 30 that it actually fails by a factor of three.
    A units mismatch between a constant and its caller makes a threshold
    ten times more lenient than it reads, and nothing about the output
    looks wrong.

    Args:
        damaged_by_cell: ``{(tier, scenario): damaged disruptions PER ARM}``.

    Returns:
        The tier that carries the claims, whether the condition held, and
        the reason — so a fallback is reported as a finding rather than
        appearing as an unexplained change of emphasis.
    """
    # **`calm` is excluded from the population, not failed by it.**
    #
    # The negative control has no disruptions by construction, so zero
    # damaged events there is the designed outcome. As first written the
    # floor was applied to every cell, so it fired on `calm` and sent the
    # primary tier to the fallback on the one scenario that could never
    # have passed — the same error as averaging non-events into the
    # recovery mean (Entry 028), three segments later.
    cells = {
        k: v
        for k, v in damaged_by_cell.items()
        if k[0] == PRIMARY_TIER and k[1] != "calm"
    }
    short = {k: v for k, v in cells.items() if v < MIN_DAMAGED_FOR_RECOVERY}
    held = bool(cells) and not short
    return {
        "primary": PRIMARY_TIER if held else FALLBACK_TIER,
        "condition_held": held,
        "threshold": MIN_DAMAGED_FOR_RECOVERY,
        "short_cells": {f"{t}/{s}": v for (t, s), v in sorted(short.items())},
        "reason": (
            f"{PRIMARY_TIER} is primary: free of the bridging confound and all "
            f"four metrics computable"
            if held
            else f"{PRIMARY_TIER} could not support the recovery metric "
                 f"({sorted(short.values())} damaged events against a floor of "
                 f"{MIN_DAMAGED_FOR_RECOVERY}); {FALLBACK_TIER} is primary and "
                 f"this is the reason"
        ),
    }


def run_config(tier: str, seeds: list[int], scenario: str = "moderate",
               run_class: str = "manifest") -> Config:
    """The exact configuration a run executes under.

    One function, used by the manifest, the dry run and segment 24, so
    there is no second description of the experiment that can drift from
    this one.
    """
    spec = TIERS[tier]
    return Config(
        run_class=run_class,
        graph=GraphCfg(model=spec["model"], n_nodes=spec["n_nodes"],
                       density=spec["density"]),
        scenario=ScenarioCfg(**scenario_cfg(scenario)),
        experiment=ExperimentCfg(
            arms=list(ARMS), n_trials=len(seeds), eval_seeds=list(seeds),
            parallel_jobs=PARALLEL_JOBS,
        ),
        budget=BudgetCfg(evaluations=BUDGET),
    )


def provenance() -> dict:
    """Everything a stranger needs that is not in the configuration."""
    def git(*args: str) -> str:
        try:
            return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                                  text=True, check=False).stdout.strip()
        except OSError:
            return ""

    dirty = bool(git("status", "--porcelain"))
    return {
        "commit": git("rev-parse", "HEAD"),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": dirty,
        # **Stated, not left to a reader to infer from a boolean.** A
        # manifest naming a commit while the tree carries uncommitted work
        # is not reproducible: a stranger checks out that commit and gets
        # different code, and every field around it still looks complete.
        # Segment 23's mutation was exactly this — reporting `dirty` as
        # False passed the entire suite, because the completeness test
        # asserted the key existed and nothing asserted it was true.
        "reproducible_from_commit": not dirty,
        "warning": (
            ""
            if not dirty
            else "UNCOMMITTED CHANGES PRESENT — this commit does not describe "
                 "the code that ran. Commit before the evidence run."
        ),
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.release()} {platform.machine()}",
        "numpy": np.__version__,
        "parallel_jobs": PARALLEL_JOBS,
    }


def build(tiers: tuple[str, ...] = ("medium200", "large1000"),
          seeds: list[int] | None = None) -> dict:
    """The whole manifest."""
    seeds = SEEDS if seeds is None else seeds
    return {
        "arms": list(ARMS),
        "seeds": list(seeds),
        "scenarios": {n: scenario_cfg(n) for n in SCENARIOS},
        "budget_evaluations": BUDGET,
        "run_class": "manifest",
        "primary_tier": {
            "tier": PRIMARY_TIER,
            "fallback": FALLBACK_TIER,
            "why": (
                "large1000 has zero bridging edges on every instance and is "
                "free of the confound affecting 40% of medium200 instances; "
                "medium200 is the instrument-verified tier and is reported "
                "alongside"
            ),
            "condition": (
                "all four metrics computable; the binding one is at least "
                f"{MIN_DAMAGED_FOR_RECOVERY} damaged disruptions per arm per "
                "scenario for mean-steps-to-recover"
            ),
            "measured_damaged_per_arm_trial": {
                "large1000/moderate": 0.40, "large1000/severe": 0.20,
                "medium200/moderate": 2.10, "medium200/severe": 1.30,
            },
            "decided_after_the_run_by": "manifest.primary_tier_holds()",
        },
        "provenance": provenance(),
        "runs": {
            tier: {
                "graph": dict(TIERS[tier]),
                "commands": [
                    "./.venv/bin/python -m dynaswarm.cli run "
                    f"--tier {tier} --scenario {s} --manifest scripts/manifest.py"
                    for s in SCENARIOS
                ],
                "instances": [asdict(characterise(tier, s)) for s in seeds],
            }
            for tier in tiers
        },
    }


#: Measured cost of one full manifest trial — all ten arms, 60 timesteps —
#: on the machine named in `provenance()`. **Measured, not derived from
#: segment Z2's table**, which timed four arms and would have to be scaled
#: by an arm mix rather than a count.
#: Mean across the four scenarios, not one of them: measured at
#: 5.73-6.21s (medium200) and 38.2-40.3s (large1000), so the spread is
#: under 10% and a single-scenario figure would have been fine — but
#: measuring it is what establishes that, and assuming it is how a four-
#: scenario run comes in four times over a one-scenario estimate.
TRIAL_SECONDS = {"medium200": 5.99, "large1000": 39.3}

#: Report an updated estimate this often during the run. **A four-hour run
#: that is secretly a twelve-hour run must be caught in the first ten
#: minutes, not at hour four**, so the checkpoint is early and frequent
#: enough to be actionable at either tier.
CHECKPOINT_EVERY = 10


#: Cost scales with how much searching happens, and a calm scenario has
#: no disruptions to recover from — but every arm still spends its full
#: budget every timestep, so the per-trial cost is essentially flat across
#: scenarios. Measured rather than assumed; see `measure_scenarios()`.
SCENARIO_COST_FACTOR = dict.fromkeys(SCENARIOS, 1.0)


def runtime_estimate(tier: str, n_trials: int = len(SEEDS),
                     scenarios: tuple[str, ...] | None = None) -> dict:
    """What the run should cost, and when to stop believing it."""
    scenarios = tuple(SCENARIOS) if scenarios is None else scenarios
    per_trial = TRIAL_SECONDS[tier]
    serial = sum(per_trial * SCENARIO_COST_FACTOR[s] for s in scenarios) * n_trials
    return {
        "tier": tier,
        "scenarios": list(scenarios),
        "trials": n_trials,
        "seconds_per_trial": per_trial,
        "serial_minutes": serial / 60,
        # Deliberately not `serial / PARALLEL_JOBS`: joblib has process
        # overhead and these trials are memory-bandwidth bound, so linear
        # speedup is the optimistic bound and quoting it as the estimate
        # is how a run comes in "late" against a number that was never
        # achievable.
        "parallel_minutes_optimistic": serial / 60 / PARALLEL_JOBS,
        "checkpoint_every": CHECKPOINT_EVERY,
        "abort_if_per_trial_exceeds": per_trial * 2.0,
        "runs": len(scenarios) * n_trials,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write MANIFEST.json")
    parser.add_argument("--seeds", type=int, default=None,
                        help="use the first N seeds (characterisation only)")
    parser.add_argument("--tier", default=None, help="restrict to one tier")
    args = parser.parse_args()

    seeds = SEEDS[: args.seeds] if args.seeds else SEEDS
    tiers = (args.tier,) if args.tier else ("medium200", "large1000")
    manifest = build(tiers, seeds)

    if args.write:
        out = ROOT / "MANIFEST.json"
        out.write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"wrote {out.relative_to(ROOT)}")
    else:
        print(json.dumps(manifest["provenance"], indent=2))
        for tier, run in manifest["runs"].items():
            shares = [i["bridge_share"] for i in run["instances"]]
            print(f"\n{tier}: {len(run['instances'])} instances")
            print(f"  bridge share: median {float(np.median(shares)):.3f}  "
                  f"max {max(shares):.3f}  "
                  f"instances above 10%: {sum(1 for s in shares if s > 0.10)}")


if __name__ == "__main__":
    main()
