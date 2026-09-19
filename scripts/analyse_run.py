"""Segment 24 — the pre-registered analysis of a completed evidence run.

Reports **every** comparison, whatever it says. Nothing is dropped for
being unflattering; that was committed in advance (Entry 024) and it is
the only thing that makes a pre-registration worth anything.

    ./.venv/bin/python scripts/analyse_run.py outputs/2026-09-19/18-30-00
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from scripts.manifest import (
    FALLBACK_TIER,
    MIN_DAMAGED_FOR_RECOVERY,
    PRIMARY_TIER,
    primary_tier_holds,
)
from scripts.preregistration import dose_response, format_results, run_preregistered

from dynaswarm.analysis.load import load_steps
from dynaswarm.analysis.scoring import censored_recovery, score_run


def banner(text: str, char: str = "=") -> None:
    print(f"\n{char * 90}\n{text}\n{char * 90}", flush=True)


def tier_of(run_id: str) -> str:
    return str(run_id).split("-")[0]


def damaged_counts(frame: pd.DataFrame) -> dict[tuple[str, str], float]:
    """Damaged disruptions per (tier, scenario), **per arm**.

    Divided by the arm count deliberately: `MIN_DAMAGED_FOR_RECOVERY` is
    a per-arm floor and this used to hand it a total over ten arms.

    This is what the primary-tier condition is decided on, and it is
    computed from the run rather than from the projection in the manifest.
    """
    out: dict[tuple[str, str], int] = {}
    for (tier, scenario, _arm, run_id, trial), group in frame.groupby(
        [frame["run_id"].map(tier_of), "scenario", "arm", "run_id", "trial"],
        sort=False,
    ):
        group = group.sort_values("timestep")
        summary = censored_recovery(
            [None if pd.isna(v) else float(v) for v in group["excess"]],
            [int(v) for v in group["num_events"]],
        )
        key = (tier, scenario)
        out[key] = out.get(key, 0) + summary.n_damaged
        del run_id, trial

    arms = frame["arm"].nunique()
    return {k: v / arms for k, v in out.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()

    frame = load_steps(args.directory, run_class=None)
    frame["tier"] = frame["run_id"].map(tier_of)

    banner("DYNASWARM — PRE-REGISTERED ANALYSIS (segment 24)", "#")
    prov_path = args.directory / "provenance.json"
    if prov_path.exists():
        prov = json.loads(prov_path.read_text())["provenance"]
        print(f"  commit {prov['commit'][:12]}   clean: {not prov['dirty']}   "
              f"{prov['platform']}")
    print(f"  rows {len(frame):,}   tiers {sorted(frame['tier'].unique())}   "
          f"scenarios {sorted(frame['scenario'].unique())}")
    print(f"  arms {frame['arm'].nunique()}   "
          f"run_class {sorted(frame['run_class'].unique())}")

    # --- the primary-tier condition, decided from the run -------------
    counts = damaged_counts(frame)
    decision = primary_tier_holds(counts)
    banner("PRIMARY TIER — the condition, decided from this run's own data")
    print(f"  floor: {MIN_DAMAGED_FOR_RECOVERY} damaged disruptions per "
          f"(tier, scenario)")
    for (tier, scenario), n in sorted(counts.items()):
        mark = "" if n >= MIN_DAMAGED_FOR_RECOVERY else "   <- below floor"
        print(f"    {tier:<11}{scenario:<10}{n:>6} damaged{mark}")
    print(f"\n  PRIMARY: {decision['primary']}   condition held: "
          f"{decision['condition_held']}")
    print(f"  {decision['reason']}")
    print(f"\n  Ruling (Entry 031): {PRIMARY_TIER} carries the three "
          f"step-derived metrics;")
    print(f"  recovery is reported from {FALLBACK_TIER}, and {PRIMARY_TIER}'s "
          f"recovery is reported")
    print("  with its own n and interval rather than suppressed.")

    # --- the family, per tier -----------------------------------------
    for tier in sorted(frame["tier"].unique()):
        here = frame[frame["tier"] == tier]
        report = run_preregistered(here)
        banner(f"TIER {tier.upper()} — the pre-registered family")
        print(format_results(report))
        print("\n  DOSE-RESPONSE (effect size, uncorrected and descriptive)")
        print(dose_response(report))

        sig = [r for r in report["results"] if r["significant"]]
        print(f"\n  {len(sig)} of {report['family_size']} tested cells "
              f"significant after Holm across the grid")
        for r in sig:
            print(f"    {r['scenario']:<10}{r['key']:<5}"
                  f"{r['arm_a']} vs {r['arm_b']}   "
                  f"delta {r['delta']:+.4f}   p_adj {r['p_adjusted']:.4g}   "
                  f"{r['effect_label']}")

    # --- the ranking, per tier and scenario ---------------------------
    banner("RANKING — mean rank with Pareto beside it")
    for tier in sorted(frame["tier"].unique()):
        for scenario in sorted(frame["scenario"].unique()):
            cell = frame[(frame["tier"] == tier) & (frame["scenario"] == scenario)]
            if cell.empty:
                continue
            ranking = score_run(cell)
            print(f"\n  {tier} / {scenario}   ({ranking['evidence']['n_seeds']} seeds)")
            print(f"    {'arm':<20}" + "".join(
                f"{m['label'][:13]:>15}" for m in ranking["metrics"]) + f"{'rank':>7}")
            for arm in ranking["arms"]:
                print(f"    {arm['arm']:<20}"
                      + "".join(f"{c:>15}" for c in arm["cells"])
                      + f"{arm['mean_rank']:>7.2f}")
            print(f"    {ranking['pareto_line']}")

    banner("DONE", "#")
    print("  Every pre-registered comparison above is reported as computed.")
    print("  Nothing was dropped for being unflattering (Entry 024).")


if __name__ == "__main__":
    main()
