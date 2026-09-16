"""Did every mechanism actually run, and how do we know?

Phase 2's gate is one sentence — *every mechanism proven live or reported
inert* — and the second half is the point.  This is where that claim is
either backed or exposed.

Three columns, and the third is what makes this evidence rather than a
status page:

* **measured** — the count or magnitude, never a grade
* **live / inert** — the reading that says which
* **when broken** — what the same field reads when the mechanism is
  deliberately disabled, taken from the demonstrations in segments 14
  and 15

Without that third column a reader has a list of numbers asserting their
own significance.  With it they can see what a failure would have looked
like, which is the only thing that makes the other two mean anything.

Regenerated from a run, never stored.  Run it after Phase 3 and it should
say something different; a report that cannot change is a snapshot ageing
into a lie.

    ./.venv/bin/python scripts/trust_report.py
"""

from __future__ import annotations

import argparse
import tempfile
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from dynaswarm.analysis.load import load_steps
from dynaswarm.config import BudgetCfg, Config, ExperimentCfg, GraphCfg, ScenarioCfg
from dynaswarm.harness.runner import run_experiment
from dynaswarm.io.writer import write_manifest

#: Every probed mechanism, with what its field means and what that field
#: reads when the mechanism is disabled.  The inert readings are not
#: predictions — each was produced by disabling the mechanism and running
#: it, in segments 14 and 15.
#:
#: `tests/test_trust_report.py` asserts that every probe field a run
#: actually emits appears here, so adding a probe without adding it to
#: this table fails the suite rather than quietly going unreported.
MECHANISMS: list[tuple[str, str, str, str]] = [
    # arm, probe field, what it measures, reading when broken
    ("aco", "tau_changed", "trail slots whose value moved", "0 — table frozen"),
    ("aco", "tau_evaporated", "trail mass removed by evaporation", "0.00 — evaporation off"),
    ("aco", "tau_deposited", "slots the best ant reinforced", "0 — deposit silent"),
    ("aco", "tau_clamped", "slots the MAX-MIN clip actually moved", "0 — bounds removed"),
    ("aco", "tau_ratio", "strongest trail over weakest", "1.0 — no spread"),
    ("aco", "lambda_branch", "competitive arcs per visited node", "1.0 — fully converged"),
    # Measured in `rebind`, before the trails are zeroed. Reads 0.00 on a
    # step where nothing broke AND on a step where plenty broke but none
    # of it carried pheromone — those are different facts and this figure
    # cannot tell them apart on its own. Read it beside `num_events`.
    ("aco", "trail_mass_lost", "share of trail mass that died this step",
     "0.00 — nothing the colony knew was invalidated"),
    ("pso", "particles_flown", "particles the flight step displaced", "0 — swarm frozen"),
    ("pso", "particles_repaired", "particles moved by repair instead", "0 — repair silent"),
    ("pso", "speed_mean", "mean |velocity| across the swarm", "unchanged from random init"),
    ("pso", "own_best_updates", "personal bests improved", "0 — no memory"),
    ("pso", "swarm_best_updates", "global best improved", "0 — no global memory"),
    ("pso", "diversity", "mean spread of priorities", "0.0 — swarm collapsed"),
    ("hybrid", "aco_share_realised", "budget share ACO actually spent",
     "1.0 — one side got nothing"),
    ("hybrid", "aco_spent", "evaluations ACO actually spent", "0 — component silent"),
    ("hybrid", "pso_spent", "evaluations PSO actually spent", "0 — component silent"),
    ("hybrid", "exchanged_this_step", "exchanges that fired this step",
     "0 — components never meet"),
]

#: Fields that carry an arm's identity or bookkeeping rather than a
#: mechanism.  Listed so the coverage test can tell "not a mechanism"
#: from "a mechanism nobody wrote down".
NON_MECHANISM = frozenset({
    "iterations", "expansions", "particles", "aco_fraction", "exchanges",
    # Scale and bounds, not mechanisms. They give the other numbers a
    # size to be read against; on their own they answer nothing about
    # whether anything ran.
    "tau_active", "tau_min", "tau_max", "speed_max",
})

#: What each probe cannot see.  Beside the probe, per Entry 015 R3 — a
#: report listing only what it can prove, with no account of what it
#: cannot, is the over-claim this phase was built to prevent.
BLIND_SPOTS: dict[str, str] = {
    "speed_mean": "cannot detect a frozen swarm: velocity keeps its random initial value",
    "tau_deposited": "cannot detect deposit on the WRONG edges; the count is identical either way",
    "particles_repaired": "counts repair moves, which are not PSO's search mechanism",
}


def scale(value: float) -> str:
    """Format without ever manufacturing a zero.

    **Entry 015 R2.** A fixed-decimal format on a quantity whose scale is
    unknown is not a display choice, it is a measurement error: PSO's
    velocity reaches 5e-14, and ``f"{v:.4f}"`` renders that as ``0.0000``
    — the exact claim this phase exists to make honestly, and one this
    project has already nearly published once.
    """
    if value == 0:
        return "0"
    if 1e-3 <= abs(value) < 1e6:
        return f"{value:,.4g}"
    return f"{value:.3e}"


def collect(directory: Path) -> tuple[dict[str, dict[str, list[float]]], int]:
    """Per-arm, per-field series from one run's recorded probes."""
    frame = load_steps(directory, run_class=None).sort_values("timestep")
    out: dict[str, dict[str, list[float]]] = {}
    for arm in frame["arm"].unique():
        rows = frame[frame["arm"] == arm]
        series: dict[str, list[float]] = {}
        for probe in rows["probe"]:
            for key, value in probe or []:
                series.setdefault(key, []).append(float(value))
        out[str(arm)] = series
    return out, int(frame["timestep"].max()) + 1


def verdict(series: list[float]) -> str:
    """live if the mechanism ever did anything; inert if it never did.

    Deliberately not a grade. "live" here means *observed acting at least
    once*, which is the only thing a count can support — it says nothing
    about whether it acted correctly.
    """
    return "live " if any(v != 0 for v in series) else "INERT"


def render(run: dict, series: dict[str, dict[str, list[float]]], horizon: int) -> str:
    lines = [
        "DYNASWARM — TRUST REPORT",
        "=" * 96,
        f"generated  {datetime.now():%Y-%m-%d %H:%M}",
        f"run        {run['run_id']}   class {run['run_class']}",
        f"read from  {run['path']}",
        f"graph      {run['graph_id']}   seed {run['seed']}   {horizon} timesteps",
        f"arms       {', '.join(a['name'] for a in run['arms'])}",
        "",
        "Every figure below answers ONE question: did this mechanism run.",
        "None of them answers whether it ran CORRECTLY — an evaporation rate ten times",
        "too high reports a large number and looks healthy. That distinction is the",
        "whole reason this document exists rather than a line saying 'verified'.",
        "",
    ]
    for arm in ("aco", "pso", "hybrid"):
        rows = [m for m in MECHANISMS if m[0] == arm]
        present = series.get(arm)
        if not present:
            continue
        heading = [f"{arm.upper()}", "-" * 96]
        if arm == "hybrid":
            heading.append(
                "  Its ACO and PSO components report through the sections above —"
                " the Hybrid's"
            )
            heading.append(
                "  probe carries their fields prefixed, so they are the same"
                " measurements, not copies."
            )
        lines += heading + [
                  f"  {'mechanism':<34}{'first':>12}{'last':>12}   {'':<6}{'when broken'}"]
        for _, field, what, broken in rows:
            values = present.get(field)
            if values is None:
                lines.append(f"  {what:<34}{'not recorded':>22}  {'':<6}{broken}")
                continue
            lines.append(
                f"  {what:<34}{scale(values[0]):>12}{scale(values[-1]):>12}"
                f"   {verdict(values):<6}{broken}"
            )
            if field in BLIND_SPOTS:
                lines.append(f"    ! {BLIND_SPOTS[field]}")
        lines.append("")
    return "\n".join(lines)


def f13(series: dict[str, dict[str, list[float]]]) -> str:
    """PSO's velocity collapse, as a measurement with its contrast beside it.

    The one Phase 2 finding that changes what the project can claim, so
    it goes in the report rather than a footnote — better stated here
    than found by an examiner.
    """
    speed = series.get("pso", {}).get("speed_mean")
    if not speed:
        return ""
    return "\n".join([
        "F13 — PSO VELOCITY, OPEN FOR PHASE 3",
        "-" * 96,
        f"  under disruption   {scale(speed[0])}  ->  {scale(speed[-1])}"
        f"   ({len(speed)} timesteps)",
        "  in isolation       ~1.4e-02, stable, measured over the same horizon",
        "",
        "  Reported as a measurement, not a verdict. The flight step still runs and still",
        "  displaces particles, by amounts near the limit of float resolution. Whether that",
        "  is convergence working or exploration failing is Phase 3's to answer, and it",
        "  comes before the inertia decision in §17.1 rather than beside it.",
        "",
    ])


#: The arms with mechanisms to report on. A* has none — it is the exact
#: reference, not a search.
ARMS = ["aco", "pso", "hybrid"]


def build_run(root: Path, evaluations: int) -> Path:
    """Execute one trial into ``root`` through the harness's own door.

    ``run_experiment`` is what ``cli.py`` calls, so what this reads is a
    normal run rather than something assembled for the report.
    """
    cfg = Config(
        run_class="exploratory",
        graph=GraphCfg(model="geometric", n_nodes=200, density=0.04),
        scenario=ScenarioCfg(name="trust", events_per_step=0.3, timesteps=60),
        experiment=ExperimentCfg(arms=ARMS, n_trials=1, parallel_jobs=1),
        budget=BudgetCfg(evaluations=evaluations),
    )
    directory = root / datetime.now().strftime("%H-%M-%S")
    directory.mkdir(parents=True, exist_ok=True)
    write_manifest(directory, directory.name, asdict(cfg))
    run_experiment(cfg, ARMS, directory, directory.name)
    return directory


def describe(directory: Path) -> tuple[dict, dict, int]:
    """Stamp the report with the run it actually read, not a default."""
    frame = load_steps(directory, run_class=None)
    series, horizon = collect(directory)
    run = {
        "run_id": directory.name,
        "run_class": str(frame["run_class"].iloc[0]),
        "path": str(directory),
        "graph_id": f"{frame['graph_model'].iloc[0]}/{int(frame['n_nodes'].iloc[0])}",
        "seed": int(frame["seed"].iloc[0]),
        "arms": [{"name": a} for a in sorted(frame["arm"].unique())],
    }
    return run, series, horizon


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, help="an existing run directory to read")
    parser.add_argument("--evaluations", type=int, default=300)
    args = parser.parse_args()

    if args.run:
        run, series, horizon = describe(args.run)
    else:
        # Into a temporary root, never outputs/ — segment 12's containment.
        # The report reads a run; it does not add one to the evidence tree.
        with tempfile.TemporaryDirectory() as tmp:
            run, series, horizon = describe(build_run(Path(tmp), args.evaluations))
    print(render(run, series, horizon))
    print(f13(series))


if __name__ == "__main__":
    main()
