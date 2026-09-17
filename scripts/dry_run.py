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

import pandas as pd
from scripts.manifest import ARMS, SCENARIOS, SEEDS, run_config
from scripts.preregistration import (
    PLANNED,
    dose_response,
    format_results,
    run_preregistered,
)

from dynaswarm.analysis.load import load_steps
from dynaswarm.analysis.scoring import score_run
from dynaswarm.harness.runner import run_experiment


def main() -> None:
    seeds = SEEDS[:3]
    print("PRE-FLIGHT — the pre-registered analysis, end to end, all four scenarios")
    print("=" * 100)
    print(f"  {len(seeds)} seeds {seeds}, 12 timesteps, 60 evaluations, "
          f"{len(ARMS)} arms, {len(SCENARIOS)} scenarios")
    print("  run_class forced to `exploratory`: a dry run must never be able to")
    print("  produce evidence, and this one is deliberately not a measurement.")
    print()

    frames = []
    with tempfile.TemporaryDirectory() as tmp:
        for scenario in SCENARIOS:
            cfg = run_config("medium200", seeds, scenario=scenario)
            cfg.scenario.timesteps = 12
            cfg.budget.evaluations = 60
            cfg.experiment.parallel_jobs = 1
            cfg.run_class = "exploratory"
            directory = Path(tmp) / scenario
            run_experiment(cfg, list(ARMS), directory, run_id=f"dry-{scenario}")
            frames.append(load_steps(directory, run_class=None))
    frame = pd.concat(frames, ignore_index=True)

    print(f"  rows: {len(frame)}   arms: {frame['arm'].nunique()}   "
          f"scenarios: {sorted(frame['scenario'].unique())}")
    print()

    # --- 1. the paired structure, per scenario ------------------------
    print("  PAIRING — every comparison's arms must see identical worlds")
    ok = True
    for scenario in sorted(frame["scenario"].unique()):
        here = frame[frame["scenario"] == scenario]
        for plan in PLANNED:
            optima = {}
            for arm in (plan.arm_a, plan.arm_b):
                rows = here[here["arm"] == arm].sort_values(["trial", "timestep"])
                optima[arm] = list(rows["optimum"].round(9))
            if optima[plan.arm_a] != optima[plan.arm_b]:
                ok = False
                print(f"    *** {scenario}/{plan.key}: different worlds ***")
    print(f"    all {len(PLANNED)} comparisons x {frame['scenario'].nunique()} "
          f"scenarios paired on identical optima: {ok}")
    print()

    # --- 2. the whole grid --------------------------------------------
    report = run_preregistered(frame)
    print("  THE GRID")
    print(format_results(report))
    print()
    print("  DOSE-RESPONSE (effect size, uncorrected and descriptive)")
    print(dose_response(report))
    print()

    # --- 3. the ranking, per scenario ---------------------------------
    print("  RANKING produces a table per scenario")
    for scenario in sorted(frame["scenario"].unique()):
        ranking = score_run(frame[frame["scenario"] == scenario])
        best = ranking["arms"][0]
        print(f"    {scenario:<10}{len(ranking['arms'])} ranked  "
              f"top={best['arm']:<18} recovery={best['cells'][3]:<8} "
              f"ref={ranking['reference']['arm'] if ranking['reference'] else None}")
    print()

    print("  VERDICT")
    print(f"    grid {report['grid_size']} cells: {report['family_size']} tested, "
          f"{len(report['degenerate'])} identical-arm, {len(report['missing'])} "
          f"not computable")
    nan = [r["key"] for r in report["results"] if r["p_value"] != r["p_value"]]
    print(f"    produced NaN: {nan or 'none'}")
    if report["missing"]:
        print(f"    NOT COMPUTABLE: {report['missing']}")


if __name__ == "__main__":
    main()
