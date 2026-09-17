"""Pre-flight: prove every pre-registered number is computable (T3).

Three seeds, a short horizon, the whole analysis end to end. **Not the
right values — a value.** This is the cheapest possible place to discover
that a planned comparison cannot be computed; finding it after a
four-hour run is the expensive version.

    ./.venv/bin/python scripts/dry_run.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from scripts.manifest import ARMS, SEEDS, run_config
from scripts.preregistration import PLANNED, format_results, run_preregistered

from dynaswarm.analysis.load import load_steps
from dynaswarm.analysis.scoring import score_run
from dynaswarm.harness.runner import run_experiment


def main() -> None:
    seeds = SEEDS[:3]
    cfg = run_config("medium200", seeds)
    # Short horizon and small budget: this proves computability, not
    # results, and a dry run that costs real compute will stop being run.
    cfg.scenario.timesteps = 12
    cfg.budget.evaluations = 60
    cfg.experiment.parallel_jobs = 1

    print("PRE-FLIGHT — the pre-registered analysis, end to end")
    print("=" * 100)
    print(f"  {len(seeds)} seeds {seeds}, {cfg.scenario.timesteps} timesteps, "
          f"{cfg.budget.evaluations} evaluations, {len(ARMS)} arms")
    print("  run_class forced to `exploratory`: a dry run must never be able to")
    print("  produce evidence, and this one is deliberately not a real measurement.")
    print()

    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp) / "dry"
        cfg.run_class = "exploratory"
        run_experiment(cfg, list(ARMS), directory, run_id="dry-run")
        frame = load_steps(directory, run_class=None)

    print(f"  rows: {len(frame)}   arms: {frame['arm'].nunique()}   "
          f"trials: {frame['trial'].nunique()}")
    print()

    # --- 1. the paired structure --------------------------------------
    print("  PAIRING — every comparison's arms must see identical worlds")
    ok = True
    for plan in PLANNED:
        per_arm = {}
        for arm in (plan.arm_a, plan.arm_b):
            rows = frame[frame["arm"] == arm].sort_values(["trial", "timestep"])
            per_arm[arm] = list(rows["optimum"].round(9))
        same = per_arm[plan.arm_a] == per_arm[plan.arm_b]
        ok &= same
        if not same:
            print(f"    {plan.key}: *** {plan.arm_a} and {plan.arm_b} saw "
                  f"DIFFERENT worlds ***")
    print(f"    all {len(PLANNED)} comparisons paired on identical optima: {ok}")
    print()

    # --- 2. every pre-registered comparison ---------------------------
    print("  THE FAMILY")
    report = run_preregistered(frame)
    print(format_results(report))
    print()

    # --- 3. the ranking the report also needs -------------------------
    ranking = score_run(frame)
    print("  RANKING (the scorer's four metrics, same data)")
    print(f"    {'arm':<20}" + "".join(f"{m['label'][:12]:>14}" for m in ranking["metrics"]))
    for arm in ranking["arms"]:
        print(f"    {arm['arm']:<20}" + "".join(f"{c:>14}" for c in arm["cells"]))
    print(f"    evidence: {ranking['evidence']['line'][:78]}")
    print()

    missing = report["missing"]
    produced = len(report["results"])
    print("  VERDICT")
    print(f"    {produced} of {len(PLANNED)} pre-registered comparisons produced a value")
    if missing:
        print(f"    NOT COMPUTABLE: {missing}")
    nulls = [r["key"] for r in report["results"]
             if r["p_value"] != r["p_value"] or r["effect"] != r["effect"]]
    if nulls:
        print(f"    produced NaN: {nulls}")
    print(f"    ranking produced {len(ranking['arms'])} ranked arms "
          f"+ reference {ranking['reference']['arm'] if ranking['reference'] else None}")


if __name__ == "__main__":
    main()
