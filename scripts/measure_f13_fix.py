"""What the F13 fix buys, measured.

Every comparison here changes **exactly one thing**. Segment 15 compared
a harness run against a standalone loop, which differed in two ways at
once, and that confound pointed at the wrong cause for two segments.

The one thing varied is the fix itself, simulated by forcing the
unguarded behaviour — `_own_cost[:] = inf` on every rebind — rather than
by editing source. Seeds, graph, scenario, budget and arm are identical
across each pair.

    ./.venv/bin/python scripts/measure_f13_fix.py
"""

from __future__ import annotations

import numpy as np

from dynaswarm.config import BudgetCfg, Config, ExperimentCfg, GraphCfg, ScenarioCfg
from dynaswarm.harness.trial import run_trial
from dynaswarm.optimizers.pso import PSO

GRAPH = GraphCfg(model="geometric", n_nodes=200, density=0.04)
SEEDS = [1000, 1001, 1002, 1003, 7, 42, 9999, 31415]


class _Unfixed:
    """Restore the pre-fix behaviour without touching source.

    `rebind` is left exactly as it is and the guard is defeated by
    clearing the remembered hash, so the comparison varies the guard and
    nothing else.
    """

    def __enter__(self):
        self._real = PSO.rebind

        def unguarded(pso_self, view):
            pso_self._last_state = None      # force the hash comparison to miss
            return self._real(pso_self, view)

        PSO.rebind = unguarded
        return self

    def __exit__(self, *exc):
        PSO.rebind = self._real


def trial(seed: int, arm: str, events_per_step: float) -> dict[str, float]:
    cfg = Config(
        run_class="exploratory",
        graph=GRAPH,
        scenario=ScenarioCfg(name="m", events_per_step=events_per_step, timesteps=60),
        experiment=ExperimentCfg(arms=[arm], n_trials=1, eval_seeds=[seed]),
        budget=BudgetCfg(evaluations=300),
    )
    rows = [r for r in run_trial(cfg, 0, [arm]).steps if r.arm == arm]
    excess = [r.excess for r in rows if r.excess is not None]
    last = dict(rows[-1].probe)
    prefix = "pso_" if arm == "hybrid" else ""
    return {
        "excess": float(np.mean(excess)) if excess else float("nan"),
        "velocity": last.get(f"{prefix}speed_mean", float("nan")),
        "diversity": last.get(f"{prefix}diversity", float("nan")),
        "gbest": sum(dict(r.probe).get(f"{prefix}swarm_best_updates", 0.0) for r in rows),
    }


def fmt(x: float) -> str:
    if not np.isfinite(x):
        return "—"
    if x == 0:
        return "0"
    return f"{x:,.4g}" if 1e-3 <= abs(x) < 1e6 else f"{x:.3e}"


def compare(arm: str, events_per_step: float, label: str) -> dict[str, tuple]:
    """One cell of the table. Held fixed: seed, graph, scenario, budget, arm."""
    after = [trial(s, arm, events_per_step) for s in SEEDS]
    with _Unfixed():
        before = [trial(s, arm, events_per_step) for s in SEEDS]

    print(f"\n  {label}  ({arm}, {events_per_step} events/step, n={len(SEEDS)})")
    print(f"    {'':<12}{'before':>13}{'after':>13}{'change':>13}")
    out = {}
    for key in ("excess", "velocity", "diversity", "gbest"):
        b = float(np.mean([r[key] for r in before]))
        a = float(np.mean([r[key] for r in after]))
        out[key] = (b, a)
        delta = f"{(a - b) * 100:+.1f} pp" if key == "excess" else f"x{a / b:,.3g}" if b else "—"
        print(f"    {key:<12}{fmt(b):>13}{fmt(a):>13}{delta:>13}")
    return out


def main() -> None:
    print("F13 FIX — BEFORE AND AFTER")
    print("=" * 68)
    print("  Each pair varies the guard and nothing else: same seeds, same graph,")
    print("  same scenario, same budget, same arm.")
    results = {}
    for arm in ("pso", "hybrid"):
        for rate, label in ((0.0, "STATIC   "), (0.3, "DISRUPTED")):
            results[(arm, rate)] = compare(arm, rate, label)

    print("\n\n  CLAIM 1 — the hybrid against its better component")
    print("  " + "-" * 66)
    for when, idx in (("before", 0), ("after", 1)):
        for rate, label in ((0.0, "static"), (0.3, "disrupted")):
            pso = results[("pso", rate)]["excess"][idx]
            hyb = results[("hybrid", rate)]["excess"][idx]
            print(f"    {when:<7}{label:<11}PSO {pso:7.1%}   Hybrid {hyb:7.1%}"
                  f"   gap {pso - hyb:+7.1%}")


if __name__ == "__main__":
    main()
