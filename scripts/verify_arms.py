"""Does each arm do what its name says?

Four checks, and each one, if it fails, means that arm reports nothing.
Prints the series rather than a verdict — a fraction that "moved" and a
fraction that moved *with the signal* are different claims, and only one
of them is the thesis.

    ./.venv/bin/python scripts/verify_arms.py
"""

from __future__ import annotations

import numpy as np

from dynaswarm.config import BudgetCfg, Config, ExperimentCfg, GraphCfg, ScenarioCfg
from dynaswarm.harness.trial import run_trial

GRAPH = GraphCfg(model="geometric", n_nodes=200, density=0.04)

#: §9's display names. Code ids are frozen data (D23a); these are the
#: only strings a human should see.
DISPLAY = {
    "hybrid_fixed": "Fixed / Static Hybrid",
    "hybrid_adaptive": "New Recency-Based Adaptive Hybrid",
    "hybrid_scheduled": "Scheduled Hybrid (open-loop control)",
    "aco_fixed": "ACO, frozen \u03c1",
    "aco_adaptive": "ACO, adaptive \u03c1",
}


def run(arm: str, seed: int = 1000, events: float = 0.3, steps: int = 40):
    cfg = Config(
        graph=GRAPH,
        scenario=ScenarioCfg(name="v", events_per_step=events, timesteps=steps),
        experiment=ExperimentCfg(arms=[arm], n_trials=1, eval_seeds=[seed]),
        budget=BudgetCfg(evaluations=300),
    )
    return [r for r in run_trial(cfg, 0, [arm]).steps if r.arm == arm]


def series(rows, key, source="probe"):
    out = []
    for r in rows:
        bag = dict(r.probe) if source == "probe" else dict(r.params)
        out.append(bag.get(key))
    return out


def show(values, width=10):
    return " ".join(f"{v:.4f}" if v is not None else "  —  " for v in values[:width])


def main() -> None:
    print("DOES EACH ARM DO WHAT ITS NAME SAYS?")
    print("=" * 78)

    # --- 1. the ablation twin must not move at all -----------------------
    rows = run("hybrid_fixed")
    fixed = series(rows, "aco_fraction")
    print(f"\n1. {DISPLAY['hybrid_fixed']}  — must be exactly 0.5 always")
    print(f"   {show(fixed)}")
    print(f"   distinct values: {len(set(fixed))}   all exactly 0.5: "
          f"{all(v == 0.5 for v in fixed)}")

    # --- 2. the thesis arm must move, and move WITH recency --------------
    rows = run("hybrid_adaptive")
    adaptive = series(rows, "aco_fraction")
    recency = [r.signal_value for r in rows]
    events = [r.num_events for r in rows]
    print(f"\n2. {DISPLAY['hybrid_adaptive']}  — must move, and move with recency")
    print(f"   fraction  {show(adaptive)}")
    print(f"   recency   {show(recency)}")
    print(f"   events    {' '.join(f'{e:5d} ' for e in events[:10])}")
    print(f"   distinct values: {len(set(adaptive))}")

    # Does it move WITH the signal, or merely move?
    delta = np.diff(adaptive)
    rec = np.array(recency[:-1], dtype=float)
    moved = np.flatnonzero(np.abs(delta) > 1e-12)
    if moved.size > 2:
        corr = float(np.corrcoef(rec[moved], delta[moved])[0, 1])
        print(f"   corr(recency, change in fraction) over the {moved.size} steps "
              f"it moved: {corr:+.3f}")
        print("   (negative is the designed direction: rising recency buys PSO)")
    # delta[i] is the change FROM step i TO step i+1, so the response to
    # a disruption at step i appears in delta[i], not delta[i-1]. Written
    # the other way first, and it reported a mean change of exactly
    # +0.000000 on disruption steps — a clean-looking zero produced by
    # reading the wrong end of the difference.
    after = [delta[i] for i, e in enumerate(events) if e > 0 and i < len(delta)]
    quiet = [delta[i] for i, e in enumerate(events) if e == 0 and i < len(delta)]
    if after and quiet:
        print(f"   mean change on a disruption step: {np.mean(after):+.6f}")
        print(f"   mean change on a quiet step:      {np.mean(quiet):+.6f}")

    # --- 3. the open-loop control must ignore the world ------------------
    a = series(run("hybrid_scheduled", events=0.0), "aco_fraction")
    b = series(run("hybrid_scheduled", events=0.8), "aco_fraction")
    print(f"\n3. {DISPLAY['hybrid_scheduled']}  — must vary open-loop")
    print(f"   quiet world   {show(a)}")
    print(f"   violent world {show(b)}")
    print(f"   identical regardless of disruption: {a == b}   distinct: {len(set(a))}")

    # --- 4. Claim 2's pair must differ -----------------------------------
    frozen = series(run("aco_fixed"), "rho", source="params")
    adapt = series(run("aco_adaptive"), "rho", source="params")
    print(f"\n4. {DISPLAY['aco_fixed']} vs {DISPLAY['aco_adaptive']}  — rho must differ")
    print(f"   frozen   {show(frozen)}")
    print(f"   adaptive {show(adapt)}")
    print(f"   trajectories differ: {frozen != adapt}   "
          f"distinct rho: frozen {len(set(frozen))}, adaptive {len(set(adapt))}")


if __name__ == "__main__":
    main()
