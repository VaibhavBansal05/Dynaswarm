"""Is `sigma` below the resolution of the thing it steps? (Segment X, T1)

Entry 022's claim: the hybrid splits a budget of 300 evaluations, and
`sigma = 0.001` moves the declared fraction by 0.3 of one evaluation.
A third of an evaluation cannot be spent, so the realised split cannot
follow the declared one and the mechanism is inert.

This measures it rather than arguing it. `hybrid.py` reports declared
`aco_fraction` and realised `aco_spent`/`pso_spent` separately, which is
the separation the question needs.

    ./.venv/bin/python scripts/measure_step_size.py
"""

from __future__ import annotations

from dynaswarm.config import BudgetCfg, Config, ExperimentCfg, GraphCfg, ScenarioCfg
from dynaswarm.harness.trial import run_trial

ARM = "hybrid_adaptive"


def run(evaluations: int, sigma: float | None = None, steps: int = 60, seed: int = 1000):
    cfg = Config(
        graph=GraphCfg(model="geometric", n_nodes=200, density=0.04),
        scenario=ScenarioCfg(name="moderate", events_per_step=0.3, timesteps=steps),
        experiment=ExperimentCfg(arms=[ARM], n_trials=1, eval_seeds=[seed]),
        budget=BudgetCfg(evaluations=evaluations),
    )
    if sigma is not None:
        cfg.control.sigma = sigma
    rows = [r for r in run_trial(cfg, 0, [ARM]).steps if r.arm == ARM]
    declared = [dict(r.probe)["aco_fraction"] for r in rows]
    spent = [dict(r.probe)["aco_spent"] for r in rows]
    total = [dict(r.probe)["aco_spent"] + dict(r.probe)["pso_spent"] for r in rows]
    return declared, spent, total


def report(evaluations: int, sigma: float | None = None) -> dict:
    declared, spent, total = run(evaluations, sigma)
    budget = total[0] if total else evaluations

    # Distance travelled, both in the same unit — evaluations — so they
    # are comparable. Declared is a fraction, so it is scaled by the
    # budget it is a fraction OF.
    declared_distance = sum(
        abs(b - a) for a, b in zip(declared, declared[1:], strict=False)
    ) * budget
    realised_distance = sum(
        abs(b - a) for a, b in zip(spent, spent[1:], strict=False)
    )

    moved_steps = [
        i for i, (a, b) in enumerate(zip(declared, declared[1:], strict=False)) if a != b
    ]
    realised_changed_on_those = sum(
        1 for i in moved_steps if spent[i] != spent[i + 1]
    )

    return {
        "budget": int(budget),
        "floor": 1.0 / budget if budget else float("nan"),
        "declared_distinct": len(set(declared)),
        "realised_distinct": len(set(spent)),
        "declared_moves": len(moved_steps),
        "realised_followed": realised_changed_on_those,
        "declared_distance": declared_distance,
        "realised_distance": realised_distance,
        "spent_range": (min(spent), max(spent)),
    }


def show(title: str, rows: list[dict], sigma: float) -> None:
    print(f"\n{title}   (sigma = {sigma})")
    print("=" * 96)
    print(f"  {'budget':>7}{'1/budget':>11}{'sigma>floor':>13}"
          f"{'declared':>10}{'realised':>10}{'moved':>8}{'followed':>10}"
          f"{'decl dist':>12}{'real dist':>11}")
    print(f"  {'':>7}{'(floor)':>11}{'':>13}{'distinct':>10}{'distinct':>10}"
          f"{'steps':>8}{'':>10}{'(evals)':>12}{'(evals)':>11}")
    for r in rows:
        print(f"  {r['budget']:>7}{r['floor']:>11.4f}"
              f"{('YES' if sigma > r['floor'] else 'no'):>13}"
              f"{r['declared_distinct']:>10}{r['realised_distinct']:>10}"
              f"{r['declared_moves']:>8}{r['realised_followed']:>10}"
              f"{r['declared_distance']:>12.1f}{r['realised_distance']:>11.1f}")


def main() -> None:
    print("T1a/T1b — DECLARED vs REALISED SPLIT, ACROSS BUDGETS")
    current = [report(b) for b in (300, 1000, 2000)]
    show("AT THE INHERITED VALUE", current, 0.001)

    print("\n  Read: `declared distinct` is how many splits the policy asked for.")
    print("  `realised distinct` is how many the search actually ran. `followed`")
    print("  counts the steps where declared moved AND realised moved with it.")


if __name__ == "__main__":
    main()
