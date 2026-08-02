"""Searching for the best fixed parameters.

The point of this module is to build a *hard* opponent.

The obvious way to make adaptation look good is to compare it against an
arbitrary fixed setting.  But the established finding it must contend
with is not "adaptation beats a bad default" — it is that a *well-chosen*
fixed setting usually beats varying parameters at run time (Stützle et
al.).  Testing against defaults would therefore answer a question nobody
is asking.  So the fixed arm gets its own search, on the same budget, and
the comparison becomes tuned-fixed against adaptive.

Seed separation
---------------
Tuning draws from ``experiment.tune_seeds``; evaluation draws from
``experiment.eval_seeds``, and the two pools must be disjoint.  Selecting
the best of many candidates on the instances one then reports turns the
headline figure into a maximum over noise rather than an estimate of
performance — and the more candidates searched, the more optimistic that
figure becomes.  Because a trial's seed *is* its entropy, disjoint pools
mean genuinely different graphs and event sequences.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import optuna
from joblib import Parallel, delayed

from dynaswarm.config import Config
from dynaswarm.harness.trial import run_trial
from dynaswarm.optimizers.spec import ParamSpec

log = logging.getLogger("dynaswarm.tuning")

__all__ = ["tune_best_fixed", "load_params", "objective_value"]


def param_spec_for(arm: str, cfg: Config) -> dict[str, ParamSpec]:
    """The tunable parameters of whichever optimizer ``arm`` builds.

    Read from the arm rather than hardcoded, so tuning a hybrid searches
    its own twelve parameters — both components plus the budget split —
    instead of silently searching a colony's five and leaving the rest at
    their defaults.  A tuner that optimises the wrong parameter set still
    returns a confident-looking vector, which is the kind of quiet wrong
    answer this codebase is built to avoid.

    Args:
        arm: A key of ``ARM_BUILDERS``.
        cfg: Supplies the graph the probe instance is built on.

    Returns:
        The arm's ``PARAM_SPEC``; empty for parameter-free methods.
    """
    from dynaswarm.core.generate import build
    from dynaswarm.core.rng import stream
    from dynaswarm.harness.arm import build_arms

    view, source, target = build(cfg.graph, stream(0, "spec_probe"))
    probe = build_arms([arm], view, source, target, 0, 0, cfg.control)[0]
    return dict(probe.optimizer.PARAM_SPEC)


def _suggest(trial: optuna.Trial, name: str, spec: ParamSpec) -> float:
    """Draw one parameter from its declared range."""
    if spec.integer:
        return float(trial.suggest_int(name, int(spec.lo), int(spec.hi)))
    return trial.suggest_float(name, spec.lo, spec.hi)


def objective_value(
    cfg: Config,
    params: dict[str, float],
    seeds: list[int],
    n_trials: int,
    arm: str = "aco",
) -> float:
    """Mean excess of a fixed parameter vector over ``seeds``.

    Args:
        cfg: Experiment configuration.
        params: Fixed parameters to evaluate.
        seeds: Pool to draw instances from.
        n_trials: Instances to average over.
        arm: Which arm to configure.

    Returns:
        Mean excess over the optimum; lower is better.  Trials that never
        hold a route contribute nothing rather than being scored zero,
        which would reward failing to find a path at all.
    """
    tuned = dict(cfg.control.fixed_params)
    tuned.update(params)
    cfg = _with_fixed_params(cfg, tuned)

    jobs = max(1, cfg.experiment.parallel_jobs)
    if jobs == 1:
        outcomes = [run_trial(cfg, t, [arm], seeds=seeds) for t in range(n_trials)]
    else:
        # Parallelism goes here rather than across Optuna trials: the
        # sampler is sequential by design, and the objective is
        # CPU-bound Python, so threading it would gain nothing.
        outcomes = Parallel(n_jobs=jobs)(
            delayed(run_trial)(cfg, t, [arm], seeds=seeds) for t in range(n_trials)
        )

    excesses: list[float] = []
    for outcome in outcomes:
        values = [row.excess for row in outcome.steps if row.excess is not None]
        if values:
            excesses.append(float(np.mean(values)))

    return float(np.mean(excesses)) if excesses else float("inf")


def tune_best_fixed(
    cfg: Config,
    n_candidates: int = 60,
    n_trials: int = 6,
    output: Path | str | None = None,
    arm: str = "aco",
) -> dict[str, float]:
    """Search for the fixed parameter vector with the lowest excess.

    Args:
        cfg: Experiment configuration.
        n_candidates: Parameter vectors to try.
        n_trials: Instances each candidate is averaged over.
        output: Where to write the winning vector, if anywhere.
        arm: Which arm to tune.

    Returns:
        The best parameter vector found.

    Raises:
        ValueError: If the tuning and evaluation pools overlap, which
            would let the search see the instances it is later judged on.
    """
    overlap = set(cfg.experiment.tune_seeds) & set(cfg.experiment.eval_seeds)
    if overlap:
        raise ValueError(
            f"tuning and evaluation seeds overlap on {sorted(overlap)[:5]}; "
            "a configuration chosen on the instances it is reported on is "
            "a maximum over noise, not a measurement"
        )

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=cfg.root_seed),
    )

    spec_table = param_spec_for(arm, cfg)

    def objective(trial: optuna.Trial) -> float:
        params = {name: _suggest(trial, name, spec) for name, spec in spec_table.items()}
        return objective_value(
            cfg, params, cfg.experiment.tune_seeds, n_trials, arm=arm
        )

    log.info(
        "tuning %s: %d parameters, %d candidates x %d instances on %d tuning seeds",
        arm, len(spec_table), n_candidates, n_trials, len(cfg.experiment.tune_seeds),
    )
    study.optimize(objective, n_trials=n_candidates, show_progress_bar=False)

    best = {name: float(value) for name, value in study.best_params.items()}
    log.info("best tuning excess %.4f with %s", study.best_value, best)

    if output is not None:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "arm": arm,
                    "params": best,
                    "tuning_excess": study.best_value,
                    "n_candidates": n_candidates,
                    "n_trials": n_trials,
                    "tune_seeds": list(cfg.experiment.tune_seeds),
                    "graph": cfg.graph.model,
                    "n_nodes": cfg.graph.n_nodes,
                    "scenario": cfg.scenario.name,
                    "events_per_step": cfg.scenario.events_per_step,
                },
                indent=2,
            )
        )
        log.info("wrote %s", path)

    return best


def load_params(path: Path | str) -> dict[str, float]:
    """Read a tuned parameter vector written by :func:`tune_best_fixed`.

    Args:
        path: The JSON file.

    Returns:
        The parameter vector.
    """
    payload = json.loads(Path(path).read_text())
    return {name: float(value) for name, value in payload["params"].items()}


def _with_fixed_params(cfg: Config, params: dict[str, float]) -> Config:
    """Return a copy of ``cfg`` carrying ``params`` as fixed overrides."""
    import copy

    clone = copy.deepcopy(cfg)
    clone.control.fixed_params = dict(params)
    return clone
