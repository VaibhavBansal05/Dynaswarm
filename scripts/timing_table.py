"""Per-arm, per-timestep wall-clock at three graph sizes (segment Z2, T3/T4).

**One machine produces the whole table.** Mixing hardware inside one table
makes every row meaningless and is invisible to a reader, so the machine
is recorded in the artefact itself.

A single run is not a measurement: an M-series chip downclocks under
sustained load and a laptop has background work. Each configuration is
repeated and the **median** reported with its **spread**, because a mean
over five samples is moved by one thermal stall.

    ./.venv/bin/python scripts/timing_table.py
"""

from __future__ import annotations

import platform
import statistics as st
import subprocess

from dynaswarm.config import BudgetCfg, Config, ExperimentCfg, GraphCfg, ScenarioCfg
from dynaswarm.harness.trial import run_trial

ARMS = ["astar", "aco", "pso", "hybrid"]
REPEATS = 5

#: The three tiers, as the dashboard presets define them.
SIZES = (
    ("small", "erdos_renyi", 30, 0.10),
    ("medium200", "geometric", 200, 0.04),
    ("large1000", "geometric", 1000, 0.04),
)


def machine() -> str:
    """Name the hardware in the artefact, not in a commit message."""
    try:
        cpu = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
    except OSError:
        cpu = ""
    return (
        f"{cpu or platform.processor() or 'unknown CPU'} | "
        f"{platform.system()} {platform.release()} | "
        f"Python {platform.python_version()}"
    )


def one_run(model: str, nodes: int, density: float, steps: int = 10) -> dict:
    """Per-arm median ms per timestep for a single trial."""
    cfg = Config(
        graph=GraphCfg(model=model, n_nodes=nodes, density=density),
        scenario=ScenarioCfg(name="timing", events_per_step=0.3, timesteps=steps),
        experiment=ExperimentCfg(arms=ARMS, n_trials=1, eval_seeds=[1000]),
        budget=BudgetCfg(evaluations=300),
    )
    rows = list(run_trial(cfg, 0, ARMS).steps)
    out = {a: st.median([r.wall_ms for r in rows if r.arm == a]) for a in ARMS}
    per_step = {r.timestep: r.oracle_ms for r in rows}
    out["_oracle"] = st.median(per_step.values())
    return out


def main() -> None:
    print("PER-ARM SEARCH TIME PER TIMESTEP")
    print("=" * 96)
    print(f"  machine: {machine()}")
    print(
        f"  {REPEATS} repeats per size; median of per-run medians, "
        f"spread = half the min..max range"
    )
    print()
    print("  Wall-clock is the only common currency here. One evaluation builds a")
    print("  whole path; one A* step pops a node. The units are NOT comparable in")
    print("  the abstract, and this table is context, not a claim.")
    print()

    header = f"  {'size':<12}" + "".join(f"{a:>17}" for a in ARMS) + f"{'oracle':>11}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    for label, model, nodes, density in SIZES:
        runs = [one_run(model, nodes, density) for _ in range(REPEATS)]
        line = f"  {label:<12}"
        for arm in ARMS:
            vals = sorted(r[arm] for r in runs)
            line += f"{st.median(vals):>9.2f} ±{(vals[-1] - vals[0]) / 2:>5.2f}"
        oracle = sorted(r["_oracle"] for r in runs)
        line += f"{st.median(oracle):>11.3f}"
        print(line)

        # If the bands overlap, the arms are not separated at this size and
        # the row must not be read as an ordering.
        bands = {a: (min(r[a] for r in runs), max(r[a] for r in runs)) for a in ARMS}
        metered = [a for a in ARMS if a != "astar"]
        overlapping = [
            (x, y)
            for i, x in enumerate(metered)
            for y in metered[i + 1 :]
            if bands[x][0] <= bands[y][1] and bands[y][0] <= bands[x][1]
        ]
        if overlapping:
            pairs = ", ".join(f"{x}/{y}" for x, y in overlapping)
            print(f"  {'':<12}  spreads overlap, NOT distinguishable: {pairs}")
        else:
            print(f"  {'':<12}  all metered arms separated at this size")

    print()
    print("  ± is half the min..max range across repeats, not a standard error.")


if __name__ == "__main__":
    main()
