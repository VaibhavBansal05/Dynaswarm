"""Tuning invariants.

The purpose of tuning here is to make the *fixed* arm hard to beat.  A
comparison against an arbitrary default would answer a question nobody
asked: the finding adaptation must contend with is that a well-chosen
fixed setting usually beats varying parameters at run time.  So these
tests are mostly about keeping the search honest — that it never sees
the instances it will be judged on, and that what it finds actually
reaches the arms.
"""

from __future__ import annotations

import json

import pytest

from dynaswarm.config import BudgetCfg, Config, ControlCfg, ExperimentCfg, GraphCfg, ScenarioCfg
from dynaswarm.harness.trial import run_trial
from dynaswarm.optimizers.aco import ACO
from dynaswarm.tuning.best_fixed import load_params, objective_value, tune_best_fixed


def make_cfg(**control) -> Config:
    return Config(
        root_seed=7,
        graph=GraphCfg(n_nodes=30, density=0.3),
        scenario=ScenarioCfg(name="test", churn=0.015, timesteps=15),
        experiment=ExperimentCfg(
            n_trials=2,
            tune_seeds=[9000, 9001, 9002],
            eval_seeds=[1000, 1001, 1002],
        ),
        budget=BudgetCfg(evaluations=120),
        control=ControlCfg(**control),
    )


# ---------------------------------------------------------------------------
# Honesty of the search
# ---------------------------------------------------------------------------


def test_overlapping_seed_pools_are_refused():
    """The search must never see the instances it will be judged on.

    Choosing the best of many candidates on the instances one then
    reports makes the headline figure a maximum over noise — and the
    more candidates searched, the more optimistic it becomes.
    """
    cfg = make_cfg()
    cfg.experiment.tune_seeds = [1000, 5000]  # 1000 is an evaluation seed
    with pytest.raises(ValueError, match="overlap"):
        tune_best_fixed(cfg, n_candidates=1, n_trials=1)


def test_tuning_and_evaluation_see_different_instances():
    cfg = make_cfg()
    tuning = run_trial(cfg, 0, ["aco"], seeds=cfg.experiment.tune_seeds)
    evaluation = run_trial(cfg, 0, ["aco"], seeds=cfg.experiment.eval_seeds)
    assert tuning.steps[0].optimum != evaluation.steps[0].optimum


# ---------------------------------------------------------------------------
# The objective
# ---------------------------------------------------------------------------


def test_objective_scores_a_parameter_vector():
    cfg = make_cfg()
    score = objective_value(
        cfg, {"rho": 0.1}, cfg.experiment.tune_seeds, n_trials=2
    )
    assert 0.0 <= score < 10.0


def test_objective_separates_good_from_bad_parameters():
    """Distinct parameter vectors must score differently.

    If they did not, the search would be optimising nothing and any
    "tuned" vector it returned would be arbitrary.
    """
    cfg = make_cfg()
    seeds = cfg.experiment.tune_seeds
    sane = objective_value(cfg, {"beta": 2.0, "rho": 0.1}, seeds, n_trials=3)
    blind = objective_value(cfg, {"beta": 0.0, "rho": 0.9}, seeds, n_trials=3)
    assert sane != blind


def test_objective_ignores_trials_that_never_find_a_route():
    """Scoring a routeless trial as zero would reward failing outright."""
    cfg = make_cfg()
    score = objective_value(cfg, {}, cfg.experiment.tune_seeds, n_trials=0)
    assert score == float("inf")


# ---------------------------------------------------------------------------
# End to end
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_search_finds_and_records_a_vector(tmp_path):
    cfg = make_cfg()
    output = tmp_path / "best_fixed.json"
    best = tune_best_fixed(cfg, n_candidates=6, n_trials=2, output=output)

    assert set(best) == set(ACO.PARAM_SPEC), "the vector must be complete"
    for name, value in best.items():
        spec = ACO.PARAM_SPEC[name]
        assert spec.lo <= value <= spec.hi

    payload = json.loads(output.read_text())
    assert payload["tune_seeds"] == cfg.experiment.tune_seeds
    assert load_params(output) == best


def test_tuned_parameters_reach_every_arm():
    """A vector that did not reach the optimizer would leave the arms at
    their defaults while the manifest claimed otherwise."""
    tuned = {"rho": 0.42, "alpha": 3.5}
    cfg = make_cfg(fixed_params=tuned)
    outcome = run_trial(cfg, 0, ["aco_fixed", "aco_adaptive"])

    for arm in ("aco_fixed", "aco_adaptive"):
        first = next(r for r in outcome.steps if r.arm == arm)
        assert first.params["rho"] == pytest.approx(0.42)
        assert first.params["alpha"] == pytest.approx(3.5)


def test_both_halves_of_the_ablation_start_from_the_tuned_vector():
    """Otherwise the comparison would be adaptive-versus-arbitrary."""
    cfg = make_cfg(fixed_params={"rho": 0.3})
    outcome = run_trial(cfg, 0, ["aco_fixed", "aco_adaptive"])
    starts = {
        r.arm: r.params["rho"] for r in outcome.steps if r.timestep == 0
    }
    assert starts["aco_fixed"] == pytest.approx(starts["aco_adaptive"])


def test_unknown_tuned_parameter_is_ignored_not_fatal():
    """A vector tuned for one optimizer may name parameters another lacks."""
    cfg = make_cfg(fixed_params={"rho": 0.2, "inertia": 0.9})
    outcome = run_trial(cfg, 0, ["aco", "astar"])
    assert any(r.params.get("rho") == pytest.approx(0.2) for r in outcome.steps)
