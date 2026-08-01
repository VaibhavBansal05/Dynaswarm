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

from dynaswarm.config import register

log = logging.getLogger("dynaswarm")

register()


@hydra.main(version_base=None, config_path="../../conf", config_name="config")
def main(cfg: DictConfig) -> None:
    """Run an experiment described by ``cfg``."""
    out = Path.cwd()  # Hydra has already chdir'd into the run directory.
    log.info("run directory: %s", out)
    log.info("\n%s", OmegaConf.to_yaml(cfg))

    seeds = cfg.experiment
    overlap = set(seeds.tune_seeds) & set(seeds.eval_seeds)
    if overlap:
        raise ValueError(
            f"tune_seeds and eval_seeds overlap on {sorted(overlap)[:5]}; "
            "tuning and evaluating on the same seeds biases the baseline"
        )

    log.info("M0 skeleton: config composed and validated. Nothing to run yet.")


if __name__ == "__main__":
    main()
