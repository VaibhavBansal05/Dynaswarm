"""Segment 24 — execute the frozen manifest.

Runs both tiers, all four scenarios, 150 seeds, ten arms, through the
CLI's own entry point (`run_experiment`). Nothing here decides anything
about the experiment: the configuration comes from `scripts/manifest.py`
and is frozen.

**Chunked into 50-trial blocks** so a run going wrong is visible in
minutes rather than at the end. Each chunk is its own `run_experiment`
call with its own `run_id`, which is why the analysis pairs on
`(run_id, trial)` — trial indices restart in every chunk.

    ./.venv/bin/python scripts/evidence_run.py --tier medium200
    ./.venv/bin/python scripts/evidence_run.py            # both tiers
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from scripts.manifest import (
    ARMS,
    PARALLEL_JOBS,
    SCENARIOS,
    SEEDS,
    TRIAL_SECONDS,
    provenance,
    run_config,
)

from dynaswarm.harness.runner import run_experiment

#: Trials per `run_experiment` call. Progress granularity, nothing else:
#: the seeds in a chunk are a slice of the frozen list, so chunking
#: changes which call a trial runs in and not which world it sees.
CHUNK = 50

OUT = Path(__file__).resolve().parents[1] / "outputs"


def banner(text: str, char: str = "=") -> None:
    line = char * 78
    print(f"\n{line}\n{text}\n{line}", flush=True)


def run_tier(tier: str, root: Path, seeds: list[int]) -> dict:
    """Every scenario for one tier, with progress and a live estimate."""
    total = len(seeds) * len(SCENARIOS)
    expected = TRIAL_SECONDS[tier] * total

    banner(
        f"TIER {tier.upper()}  STARTING\n"
        f"  {len(SCENARIOS)} scenarios x {len(seeds)} seeds = {total} trials"
        f"   ({len(ARMS)} arms, {PARALLEL_JOBS} jobs)\n"
        f"  expected ~{expected / 60:.0f} min serial-equivalent of work"
    )

    started = time.perf_counter()
    done = 0
    per_trial: list[float] = []

    for scenario in SCENARIOS:
        for offset in range(0, len(seeds), CHUNK):
            block = seeds[offset : offset + CHUNK]
            cfg = run_config(tier, block, scenario=scenario)
            run_id = f"{tier}-{scenario}-{offset:04d}"

            t0 = time.perf_counter()
            run_experiment(cfg, list(ARMS), root / run_id, run_id=run_id)
            elapsed = time.perf_counter() - t0

            done += len(block)
            per_trial.append(elapsed / len(block))
            # Estimate from what this run is actually doing, not from the
            # constant measured in segment 23 — a machine under different
            # load is the case the estimate exists to catch.
            rate = sum(per_trial) / len(per_trial)
            remaining = (total - done) * rate
            print(
                f"  [{tier}] {done:>4}/{total} trials"
                f"   {scenario:<9} seeds {block[0]}..{block[-1]}"
                f"   {elapsed:6.1f}s ({elapsed / len(block):5.2f}s/trial)"
                f"   elapsed {(time.perf_counter() - started) / 60:5.1f} min"
                f"   remaining ~{remaining / 60:5.1f} min",
                flush=True,
            )

    wall = time.perf_counter() - started
    banner(
        f"TIER {tier.upper()}  FINISHED\n"
        f"  {total} trials in {wall / 60:.1f} min"
        f"   ({wall / total:.2f}s per trial wall-clock at {PARALLEL_JOBS} jobs)"
    )
    return {"tier": tier, "trials": total, "wall_minutes": wall / 60,
            "seconds_per_trial": wall / total}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tier", default=None, help="one tier, else both")
    parser.add_argument("--seeds", type=int, default=None,
                        help="first N seeds (rehearsal only)")
    args = parser.parse_args()

    seeds = SEEDS[: args.seeds] if args.seeds else SEEDS
    tiers = (args.tier,) if args.tier else ("medium200", "large1000")

    prov = provenance()
    stamp = datetime.now().strftime("%Y-%m-%d/%H-%M-%S")
    root = OUT / stamp
    root.mkdir(parents=True, exist_ok=True)

    banner("DYNASWARM — EVIDENCE RUN (segment 24)", "#")
    print(f"  commit      {prov['commit'][:12]}   clean: {not prov['dirty']}")
    print(f"  python      {prov['python']}   {prov['platform']}")
    print(f"  jobs        {PARALLEL_JOBS}")
    print(f"  arms        {len(ARMS)}")
    print(f"  seeds       {len(seeds)}  ({seeds[0]}..{seeds[-1]})")
    print(f"  scenarios   {list(SCENARIOS)}")
    print(f"  tiers       {list(tiers)}")
    print(f"  writing to  {root}")

    if prov["dirty"]:
        raise SystemExit(
            "\nREFUSING TO RUN: the working tree is dirty, so the commit "
            "recorded beside these results does not describe the code that "
            "produced them."
        )

    # Provenance captured at EXECUTION time, beside the results. The
    # static MANIFEST.json cannot record the commit that contains it — a
    # file cannot hold its own hash — so this is the authoritative record.
    (root / "provenance.json").write_text(
        json.dumps({"provenance": prov, "tiers": list(tiers),
                    "seeds": list(seeds), "scenarios": list(SCENARIOS),
                    "arms": list(ARMS), "chunk": CHUNK,
                    "started": datetime.now().isoformat()}, indent=2) + "\n"
    )

    timings = [run_tier(tier, root, seeds) for tier in tiers]

    banner("ALL TIERS FINISHED", "#")
    for t in timings:
        print(f"  {t['tier']:<12}{t['trials']:>5} trials  "
              f"{t['wall_minutes']:>6.1f} min  {t['seconds_per_trial']:.2f}s/trial")
    print(f"\n  results in {root}")
    print(f"  analyse with: ./.venv/bin/python scripts/analyse_run.py {root}")


if __name__ == "__main__":
    main()
