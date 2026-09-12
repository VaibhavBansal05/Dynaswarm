"""Every observation field from a live trial, and what saturation really is.

T4: nothing had ever built an `AllocationObservation` from a running
trial before segment 21 — mutation C showed that is exactly where a
silent zero lives, so the fields are printed and read rather than
asserted green.

T6: §7.2's reportability rule allows at most 20% of steps at a bound.
That number was written down, not derived. This measures the actual
distribution so it can be justified or replaced.

    ./.venv/bin/python scripts/observation_and_saturation.py
"""

from __future__ import annotations

import numpy as np

from dynaswarm.allocation.observation import observe
from dynaswarm.config import BudgetCfg, Config, ExperimentCfg, GraphCfg, ScenarioCfg
from dynaswarm.harness.trial import run_trial

GRAPH = GraphCfg(model="geometric", n_nodes=200, density=0.04)
FIELDS = [
    "t", "recency", "steps_since_disruption", "events_this_step",
    "current_fraction", "budget", "aco_lambda_branch", "pso_diversity",
    "own_cost", "own_cost_delta", "path_invalidated",
]


def trial(arm="hybrid_adaptive", seed=1000, events=0.3, steps=60):
    cfg = Config(
        graph=GRAPH,
        scenario=ScenarioCfg(name="o", events_per_step=events, timesteps=steps),
        experiment=ExperimentCfg(arms=[arm], n_trials=1, eval_seeds=[seed]),
        budget=BudgetCfg(evaluations=300),
    )
    return [r for r in run_trial(cfg, 0, [arm]).steps if r.arm == arm]


def rebuild(rows, t):
    """The observation as the trial built it, from that step's own row."""
    row = rows[t]
    previous = rows[t - 1].best_cost if t > 0 else None
    quiet = 0
    for k in range(t, -1, -1):
        if rows[k].num_events:
            break
        quiet += 1
    return observe(
        t=row.timestep,
        events_this_step=row.num_events,
        current_fraction=dict(row.probe)["aco_fraction"],
        budget=300,
        probe=dict(row.probe),
        own_cost=row.best_cost,
        previous_cost=previous,
        path_invalidated=not row.path_valid,
        recency=row.signal_value,
        steps_since_disruption=quiet,
    )


def main() -> None:
    rows = trial()
    disruption = next(r.timestep for r in rows if r.num_events > 0)
    picks = [(0, "quiet, opening"), (disruption, "disruption lands"),
             (min(disruption + 3, len(rows) - 1), "recovering")]

    print("T4 — EVERY OBSERVATION FIELD, FROM A LIVE TRIAL")
    print("=" * 78)
    print(f"  {'field':<24}" + "".join(f"{label:>18}" for _, label in picks))
    obs = {t: rebuild(rows, t) for t, _ in picks}
    for field in FIELDS:
        cells = []
        for t, _ in picks:
            v = getattr(obs[t], field)
            cells.append("—" if v is None else (f"{v:.4g}" if isinstance(v, float) else str(v)))
        print(f"  {field:<24}" + "".join(f"{c:>18}" for c in cells))

    print("\n  Is each field carrying information, or a constant?")
    for field in FIELDS:
        values = [getattr(rebuild(rows, t), field) for t in range(len(rows))]
        real = [v for v in values if v is not None]
        distinct = len(set(real))
        verdict = "CONSTANT" if distinct <= 1 else f"{distinct} distinct"
        print(f"    {field:<24} {verdict}")

    print("\n\nT6 — WHAT SATURATION ACTUALLY LOOKS LIKE")
    print("=" * 78)
    print(f"  {'scenario':<12}{'seed':>6}{'distinct':>10}{'at bound':>11}{'reportable':>12}")
    at_bounds = []
    for events, label in ((0.0, "static"), (0.1, "low"), (0.3, "moderate"), (0.8, "high")):
        for seed in (1000, 1001, 7, 42):
            rows = trial(seed=seed, events=events)
            fracs = [dict(r.probe)["aco_fraction"] for r in rows]
            at_bound = sum(1 for v in fracs if v <= 0.05 or v >= 0.95) / len(fracs)
            at_bounds.append(at_bound)
            ok = len(set(fracs)) > 1 and at_bound < 0.20
            print(f"  {label:<12}{seed:>6}{len(set(fracs)):>10}{at_bound:>10.1%}"
                  f"{('yes' if ok else 'NO'):>12}")
    arr = np.array(at_bounds)
    print(f"\n  across {arr.size} runs: max {arr.max():.1%}, mean {arr.mean():.1%}, "
          f"threshold 20%")
    print(f"  headroom: the worst run is {0.20 - arr.max():.1%} below the limit")


if __name__ == "__main__":
    main()
