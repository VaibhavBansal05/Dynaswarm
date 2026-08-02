"""Command-line entry point.

Hydra owns the output directory, so every run is written to its own
timestamped folder together with the exact resolved config that produced
it.  That is the whole provenance story — there is no bespoke session-id
or results-directory machinery.
"""

from __future__ import annotations

import logging
from pathlib import Path

import hydra
from omegaconf import DictConfig, OmegaConf

from dynaswarm.config import Config, register
from dynaswarm.harness.runner import run_experiment
from dynaswarm.io.writer import write_manifest

log = logging.getLogger("dynaswarm")

register()


@hydra.main(version_base=None, config_path="../../conf", config_name="config")
def main(cfg: DictConfig) -> None:
    """Run an experiment described by ``cfg``."""
    directory = Path.cwd()  # Hydra has already chdir'd into the run directory.
    run_id = directory.name

    resolved: Config = OmegaConf.to_object(cfg)  # type: ignore[assignment]
    _check_seed_partition(resolved)

    log.info("run %s -> %s", run_id, directory)
    write_manifest(directory, run_id, OmegaConf.to_container(cfg, resolve=True))

    summary = run_experiment(resolved, list(resolved.experiment.arms), directory, run_id)

    log.info("%-10s %12s %12s %8s %10s", "arm", "mean excess", "final", "avail", "evals")
    for arm, metrics in summary.items():
        log.info(
            "%-10s %11.2f%% %11.2f%% %7.0f%% %10.0f",
            arm,
            100 * metrics["mean_excess"],
            100 * metrics["final_excess"],
            100 * metrics["availability"],
            metrics["evaluations"],
        )


def _check_seed_partition(cfg: Config) -> None:
    """Refuse to run if tuning and evaluation seeds overlap.

    Selecting a configuration on the same seeds it is then reported on
    turns the headline figure into a maximum over noise.  Checking at
    startup is cheap; discovering it after a long sweep is not.
    """
    overlap = set(cfg.experiment.tune_seeds) & set(cfg.experiment.eval_seeds)
    if overlap:
        raise ValueError(
            f"tune_seeds and eval_seeds overlap on {sorted(overlap)[:5]}; "
            "tuning and evaluating on the same seeds biases the baseline"
        )


if __name__ == "__main__":
    main()
