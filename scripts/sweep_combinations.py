"""WALKTHROUGH Part 12, automated (segment X, T7).

Every combination reachable from the interface that a script can drive.
For each: do the three universal invariants hold, and if not, is the
failure a **crash**, a **wrong answer**, or **confident nonsense** — the
last being the one that does not announce itself.

    ./.venv/bin/python scripts/sweep_combinations.py
"""

from __future__ import annotations

import time
import traceback
from pathlib import Path
from tempfile import mkdtemp

from dashboard.server import GraphSpec, RaceSpec, ScenarioSpec, race

from dynaswarm.analysis.load import load_steps

ROOT = Path(mkdtemp())
ARMS = ["astar", "aco", "pso", "hybrid"]

CRASH, WRONG, NONSENSE, OK, REFUSED = "CRASH", "WRONG", "NONSENSE", "ok", "refused"


def check(label, *, arms=ARMS, evaluations=200, **kw):
    """Run one combination and classify the outcome."""
    graph = GraphSpec(**{k: v for k, v in kw.items() if k in GraphSpec.model_fields})
    scen = ScenarioSpec(**{k: v for k, v in kw.items() if k in ScenarioSpec.model_fields})
    start = time.perf_counter()
    try:
        started = race(
            RaceSpec(arms=arms, evaluations=evaluations, graph=graph, scenario=scen),
            root=ROOT,
        )
    except Exception as exc:  # noqa: BLE001 — classification is the point
        kind = REFUSED if isinstance(exc, ValueError) else CRASH
        return kind, f"{type(exc).__name__}: {str(exc)[:60]}", time.perf_counter() - start
    elapsed = time.perf_counter() - start

    frame = load_steps(started["path"], run_class=None)
    notes = []

    # (b) A* is the oracle: its excess is 0 by construction. Anything else
    #     is the measurement broken, and it is the quietest possible break.
    astar = frame[frame["arm"] == "astar"]["excess"].dropna()
    if len(astar) and float(astar.abs().max()) > 1e-9:
        notes.append(f"A* excess {float(astar.abs().max()):.2e}")

    # A route that costs something while being invalid, or vice versa.
    bad = frame[frame["path_valid"] & frame["best_cost"].isna()]
    if len(bad):
        notes.append(f"{len(bad)} rows valid-but-costless")
    ghost = frame[(~frame["path_valid"]) & frame["best_cost"].notna()]
    if len(ghost):
        notes.append(f"{len(ghost)} rows costed-but-invalid")

    # An optimum that is absent or non-positive is not a shortest path.
    opt = frame["optimum"].dropna()
    if len(opt) and float(opt.min()) <= 0:
        notes.append(f"optimum min {float(opt.min())}")

    if notes:
        return NONSENSE, "; ".join(notes), elapsed
    return OK, f"{len(frame)} rows", elapsed


def section(title, rows):
    print(f"\n{title}")
    print("=" * 94)
    print(f"  {'combination':<46}{'verdict':>10}{'secs':>8}   detail")
    for label, kw in rows:
        verdict, detail, secs = check(label, **kw)
        print(f"  {label:<46}{verdict:>10}{secs:>8.1f}   {detail[:34]}")


def main() -> None:
    section("THE FOUR MODELS", [
        ("Map-based (geometric), 200", dict(model="geometric", n_nodes=200, timesteps=20)),
        ("Street grid, 400", dict(model="grid", n_nodes=400, timesteps=20)),
        ("Random / no map (erdos_renyi), 200",
         dict(model="erdos_renyi", n_nodes=200, timesteps=20)),
        ("Custom: geometric 137 @ 0.07",
         dict(model="geometric", n_nodes=137, density=0.07, timesteps=20)),
    ])

    section("THE FOUR SIZE PRESETS", [
        ("Small 30 (erdos_renyi)", dict(model="erdos_renyi", n_nodes=30, timesteps=20)),
        ("Medium 200 (the research tier)", dict(model="geometric", n_nodes=200, timesteps=20)),
        ("Large 1000", dict(model="geometric", n_nodes=1000, timesteps=20)),
        ("Grid 400", dict(model="grid", n_nodes=400, timesteps=20)),
    ])

    section("THE FOUR DISRUPTION SCENARIOS", [
        ("Calm (0.0)", dict(events_per_step=0.0, timesteps=30)),
        ("Light (0.1)", dict(events_per_step=0.1, timesteps=30)),
        ("Moderate (0.3)", dict(events_per_step=0.3, timesteps=30)),
        ("Severe (0.8)", dict(events_per_step=0.8, timesteps=30)),
    ])

    section("THE EDGES OF THE NUMERIC FIELDS", [
        ("places = 4 (minimum)", dict(n_nodes=4, timesteps=10)),
        ("how connected = 0.005 (very sparse)", dict(density=0.005, timesteps=10)),
        ("how connected = 1.0 (complete)", dict(n_nodes=60, density=1.0, timesteps=10)),
        ("how long = 1", dict(timesteps=1)),
        ("breaks per step = 0", dict(events_per_step=0.0, timesteps=10)),
        ("roads per break = 1", dict(cluster_size=1, timesteps=20)),
        ("roads per break = 100", dict(cluster_size=100, timesteps=20)),
    ])

    print("\nTIMING — what Phase 4 is buying")
    print("=" * 94)
    for label, kw in [
        ("medium200, moderate, 60 steps", dict(n_nodes=200, events_per_step=0.3, timesteps=60)),
        ("large1000, moderate, 60 steps", dict(n_nodes=1000, events_per_step=0.3, timesteps=60)),
        ("medium200, severe, 500 steps", dict(n_nodes=200, events_per_step=0.8, timesteps=500)),
    ]:
        verdict, _, secs = check(label, evaluations=300, **kw)
        print(f"  {label:<46}{verdict:>10}{secs:>8.1f}s")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
