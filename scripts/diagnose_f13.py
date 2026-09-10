"""Why does PSO's swarm stop moving under disruption?

Temporary diagnostic instrumentation for F13. It monkeypatches `_move`
to record the three velocity terms separately, runs a disrupted trial and
an undisrupted one, and prints both. **Nothing here is permanent** — it
adds no telemetry to `src/`, and segment 17 proposes rather than installs.

    ./.venv/bin/python scripts/diagnose_f13.py
"""

from __future__ import annotations

import numpy as np

from dynaswarm.config import BudgetCfg, Config, ExperimentCfg, GraphCfg, ScenarioCfg
from dynaswarm.harness.trial import run_trial
from dynaswarm.optimizers.pso import PSO

GRAPH = GraphCfg(model="geometric", n_nodes=200, density=0.04)


def instrument() -> dict[int, dict[str, float]]:
    """Record |inertia|, |cognitive|, |social| per step, as APPLIED.

    Measured from the terms that actually go into the sum, not from the
    coefficients that produced them — a decomposition that reports its
    inputs rather than its contributions tells a plausible, wrong story
    (segment 14's bounds probe, in a new place). The three are asserted
    to reconstruct the real velocity in tests/test_f13_diagnosis.py.
    """
    log: dict[int, dict[str, float]] = {}

    def traced(self, i: int) -> None:
        r1, r2 = self._uniform(), self._uniform()
        cognitive = self._p["cognitive"] * r1 * (self._own_best[i] - self._position[i])
        social = 0.0
        if self._swarm_best is not None:
            social = self._p["social"] * r2 * (self._swarm_best - self._position[i])
        inertia = self._p["inertia"] * self._velocity[i]

        bucket = log.setdefault(self._probe_step, dict.fromkeys(
            ("inertia", "cognitive", "social", "resulting", "own_eq_pos", "n"), 0.0))
        bucket["inertia"] += float(np.abs(inertia).mean())
        bucket["cognitive"] += float(np.abs(cognitive).mean())
        bucket["social"] += float(np.abs(np.asarray(social)).mean())
        bucket["own_eq_pos"] += float(np.array_equal(self._own_best[i], self._position[i]))
        bucket["n"] += 1.0

        self._velocity[i] = inertia + cognitive + social
        np.clip(self._position[i] + self._velocity[i], 0.0, 1.0, out=self._position[i])
        bucket["resulting"] += float(np.abs(self._velocity[i]).mean())

    PSO._move = traced
    PSO._probe_step = 0
    return log


def restore(original) -> None:
    PSO._move = original


def run(events_per_step: float, timesteps: int = 60) -> tuple[dict, list[int]]:
    """One trial, with the step index threaded into the instrumentation."""
    original = PSO._move
    log = instrument()

    cfg = Config(
        run_class="exploratory",
        graph=GRAPH,
        scenario=ScenarioCfg(name="f13", events_per_step=events_per_step, timesteps=timesteps),
        experiment=ExperimentCfg(arms=["pso"], n_trials=1),
        budget=BudgetCfg(evaluations=300),
    )
    # The harness does not expose the step to the optimizer, so it is
    # threaded through a class attribute the traced _move reads.
    import dynaswarm.harness.trial as trial_module

    real_state_at = trial_module.GraphTimeline.state_at

    def counting(self, t):
        PSO._probe_step = t
        return real_state_at(self, t)

    trial_module.GraphTimeline.state_at = counting
    try:
        outcome = run_trial(cfg, 0, ["pso"])
    finally:
        trial_module.GraphTimeline.state_at = real_state_at
        restore(original)

    disrupted = [r.timestep for r in outcome.steps if r.num_events > 0]
    return log, disrupted


def fmt(x: float) -> str:
    if x == 0:
        return "0"
    return f"{x:,.4g}" if 1e-3 <= abs(x) < 1e6 else f"{x:.3e}"


def show(title: str, log: dict, disrupted: list[int]) -> None:
    print(f"\n{title}")
    print("-" * 92)
    print(f"  {'t':>3}  {'inertia':>11}{'cognitive':>12}{'social':>12}{'|v|':>12}"
          f"{'own==pos':>10}  events")
    for t in sorted(log):
        if t % 6 and t not in disrupted[:4]:
            continue
        b = log[t]
        n = max(b["n"], 1.0)
        mark = "  <- disruption" if t in disrupted else ""
        print(f"  {t:>3}  {fmt(b['inertia']/n):>11}{fmt(b['cognitive']/n):>12}"
              f"{fmt(b['social']/n):>12}{fmt(b['resulting']/n):>12}"
              f"{b['own_eq_pos']/n:>9.0%}{mark}")


def main() -> None:
    log_d, disrupted = run(events_per_step=0.3)
    show("DISRUPTED (moderate, 0.3 events/step)", log_d, disrupted)
    print(f"\n  disruption steps: {disrupted}")

    log_q, _ = run(events_per_step=0.0)
    show("ISOLATION (static, no disruptions)", log_q, [])


if __name__ == "__main__":
    main()
