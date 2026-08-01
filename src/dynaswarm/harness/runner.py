"""Trial fan-out.

Trials are independent given content-addressed seeds, so they parallelise
cleanly.  Parallelism stops there: distributing work *within* a trial
would make the order in which arms touch shared state nondeterministic,
and reproducibility is worth more here than the extra cores.
"""

from __future__ import annotations

import logging
from pathlib import Path

from joblib import Parallel, delayed

from dynaswarm.config import Config
from dynaswarm.harness.trial import TrialOutcome, run_trial, summarise
from dynaswarm.io.writer import ResultWriter

log = logging.getLogger("dynaswarm.runner")

__all__ = ["run_experiment"]


def run_experiment(
    cfg: Config,
    arm_names: list[str],
    directory: Path | str,
    run_id: str,
) -> dict[str, dict[str, float]]:
    """Run every trial and stream the results to Parquet.

    Args:
        cfg: Resolved configuration.
        arm_names: Arms to compare.
        directory: Output directory.
        run_id: Identifier stamped into every row.

    Returns:
        A per-arm summary aggregated over trials, for logging.
    """
    n_trials = cfg.experiment.n_trials
    jobs = max(1, cfg.experiment.parallel_jobs)

    log.info(
        "running %d trial(s) of %s on %s n=%d, arms=%s, %d job(s)",
        n_trials,
        cfg.scenario.name,
        cfg.graph.model,
        cfg.graph.n_nodes,
        ",".join(arm_names),
        jobs,
    )

    if jobs == 1:
        outcomes = [run_trial(cfg, t, arm_names) for t in range(n_trials)]
    else:
        outcomes = Parallel(n_jobs=jobs)(
            delayed(run_trial)(cfg, t, arm_names) for t in range(n_trials)
        )

    with ResultWriter(directory, run_id) as writer:
        for outcome in outcomes:
            writer.write(outcome)

    return _aggregate(outcomes)


def _aggregate(outcomes: list[TrialOutcome]) -> dict[str, dict[str, float]]:
    """Mean each arm's per-trial summary across trials."""
    totals: dict[str, dict[str, list[float]]] = {}
    for outcome in outcomes:
        for arm, metrics in summarise(outcome).items():
            bucket = totals.setdefault(arm, {})
            for key, value in metrics.items():
                bucket.setdefault(key, []).append(float(value))

    return {
        arm: {key: sum(values) / len(values) for key, values in metrics.items()}
        for arm, metrics in totals.items()
    }
