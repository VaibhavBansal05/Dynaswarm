"""Does a vector tuned for one disruption level cost anything at another?

This script backs the project's **key explanatory finding**: that the
optimal parameters do not depend on the disruption rate, which is what
makes Claim 2 a *diagnosis* rather than a shrug.  Without it the null
result reads "adaptation did not help here"; with it, "adaptation cannot
help, and here is the measurement showing why."

How it works: tune separately on each scenario, then evaluate every
resulting vector on every scenario, always on **evaluation seeds no
tuning run ever saw**.  If the vector matched to a scenario does not beat
the mismatched ones, a volatility-driven controller has nothing to steer
by.

Two things to know before trusting anything it prints
-----------------------------------------------------
**The disruption model changed underneath this script.**  It previously
passed ``churn`` as a *fraction of |E|* — the old proportional model.
Disruption is now an absolute ``Poisson(events_per_step)`` rate, because
a proportional rate produced ~18 events per step at 1200 edges, so the
graph never settled and recovery was unmeasurable.  There is deliberately
**no mapping from the old fractions to new rates**; the scenarios are
taken as they are registered today.  The finding is therefore being
*re-derived*, not reproduced, and it may come out differently.  If it
does, that is itself a result.

**It cannot run until Phase 4.**  It needs one tuned vector per scenario,
produced by the experiment manifest's tuning steps (``ARCHITECTURE.md``
§13.1, T1–T4).  Those do not exist yet.  Run without them it exits with a
message saying so rather than inventing a baseline.
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

from dynaswarm.config import (
    BudgetCfg,
    Config,
    ControlCfg,
    ExperimentCfg,
    GraphCfg,
    ScenarioCfg,
)
from dynaswarm.harness.trial import run_trial

#: Where the tuning steps write their vectors.
VECTOR_GLOB = "multirun/*/*/*/best_fixed.json"

#: The scenarios to cross-evaluate, **as registered today**.  These are the
#: absolute Poisson rates from ``config.register()`` — not a translation of
#: the fractions this script used under the old proportional model.
SCENARIOS: dict[str, float] = {"static": 0.0, "moderate": 0.3, "high": 0.8}

#: The tier on which mechanism-level claims may be made (D8).
GRAPH = GraphCfg(model="geometric", n_nodes=200, density=0.04)

N_TRIALS = 12
BUDGET = 300
TIMESTEPS = 60


def load_vectors() -> dict[str, dict[str, float]]:
    """Collect one tuned parameter vector per scenario.

    Returns:
        ``{scenario: params}`` for every vector found.
    """
    vectors: dict[str, dict[str, float]] = {}
    for path in sorted(glob.glob(VECTOR_GLOB)):
        payload = json.loads(Path(path).read_text())
        scenario = payload.get("scenario")
        if scenario:
            vectors[scenario] = payload["params"]
    return vectors


def require_vectors() -> dict[str, dict[str, float]]:
    """Return the tuned vectors, or exit with an explanation.

    Exiting loudly matters more than it looks.  The original failure mode
    of this script was an empty glob feeding an empty dict, which would
    have produced a confident-looking table built on default parameters —
    a cross-evaluation that silently compared a vector against itself.
    """
    vectors = load_vectors()
    missing = [name for name in SCENARIOS if name not in vectors]
    if missing:
        sys.exit(
            "cross_evaluate: cannot run — no tuned parameter vectors for "
            f"{missing}.\n"
            f"  Looked in: {VECTOR_GLOB}\n"
            f"  Found:     {sorted(vectors) or 'nothing'}\n\n"
            "  These are produced by the tuning steps of the experiment "
            "manifest (ARCHITECTURE.md §13.1, T1-T4), which run in Phase 4.\n"
            "  This script is repaired and ready; the finding it produces "
            "cannot be re-derived until those vectors exist.\n"
            "  Until then the figures quoted for it in README.md and "
            "DOCUMENTATION.md are provisional and are marked as such."
        )
    return vectors


def make_cfg(params: dict[str, float], events_per_step: float) -> Config:
    """One evaluation condition: a fixed vector, run at one disruption rate."""
    return Config(
        graph=GRAPH,
        scenario=ScenarioCfg(
            name="cross", events_per_step=events_per_step, timesteps=TIMESTEPS
        ),
        experiment=ExperimentCfg(n_trials=N_TRIALS),
        budget=BudgetCfg(evaluations=BUDGET),
        control=ControlCfg(fixed_params=params),
    )


def evaluate(params: dict[str, float], events_per_step: float) -> np.ndarray:
    """Mean excess per trial for one vector at one rate."""
    cfg = make_cfg(params, events_per_step)
    scores = []
    for trial in range(N_TRIALS):
        rows = run_trial(cfg, trial, ["aco"]).steps
        values = [r.excess for r in rows if r.excess is not None]
        if values:
            scores.append(float(np.mean(values)))
    return np.array(scores)


def main() -> None:
    vectors = require_vectors()
    names = list(SCENARIOS)

    print("CROSS-EVALUATION: rows = vector tuned for, columns = evaluated on")
    print("(evaluation seeds, never seen by any tuning run)")
    print(f"(absolute Poisson rates: {SCENARIOS})")
    print()

    results = {
        (tuned_for, run_on): evaluate(vectors[tuned_for], SCENARIOS[run_on])
        for tuned_for in names
        for run_on in names
    }

    print(f"{'tuned for':12s}" + "".join(f"{n:>12s}" for n in names))
    for tuned_for in names:
        row = "".join(f"{results[(tuned_for, n)].mean():11.2%} " for n in names)
        print(f"{tuned_for:12s}{row}")

    print()
    print("Does the matching vector beat the mismatched ones on each scenario?")
    for run_on in names:
        native = results[(run_on, run_on)]
        for tuned_for in names:
            if tuned_for == run_on:
                continue
            other = results[(tuned_for, run_on)]
            try:
                _, p = stats.wilcoxon(native, other)
            except ValueError:
                p = float("nan")
            verdict = (
                "native better" if native.mean() < other.mean() else "MISMATCHED BETTER"
            )
            print(
                f"  on {run_on:9s}: native {native.mean():6.2%} vs "
                f"{tuned_for:9s} {other.mean():6.2%}  "
                f"delta {native.mean() - other.mean():+6.2%}  p={p:.3f}  {verdict}"
            )


if __name__ == "__main__":
    main()
