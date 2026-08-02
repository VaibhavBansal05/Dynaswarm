"""Harness invariants: shared world, stream independence, reproducibility.

These are integration-level guards.  The unit tests establish that an
individual optimizer behaves; these establish that putting several of
them in one loop does not quietly make the comparison unfair — by
handing one arm a different world, by letting one arm's randomness
depend on which others are present, or by producing results that cannot
be reproduced.
"""

from __future__ import annotations

import dataclasses

import pytest

from dynaswarm.analysis.load import expand_maps, load_steps, per_trial_excess
from dynaswarm.config import BudgetCfg, Config, ExperimentCfg, GraphCfg, ScenarioCfg
from dynaswarm.harness.arm import build_arms
from dynaswarm.harness.trial import run_trial
from dynaswarm.io.writer import ResultWriter


def make_cfg(churn: float = 0.015, timesteps: int = 20, n_trials: int = 2) -> Config:
    return Config(
        root_seed=42,
        graph=GraphCfg(n_nodes=30, density=0.3),
        scenario=ScenarioCfg(name="test", churn=churn, timesteps=timesteps),
        experiment=ExperimentCfg(n_trials=n_trials),
        budget=BudgetCfg(evaluations=200),
    )


def rows_for(outcome, arm: str) -> list:
    return [r for r in outcome.steps if r.arm == arm]


# ---------------------------------------------------------------------------
# Shape and bookkeeping
# ---------------------------------------------------------------------------


def test_one_row_per_arm_per_timestep():
    cfg = make_cfg(timesteps=15)
    outcome = run_trial(cfg, trial=0, arm_names=["astar", "aco"])
    assert len(outcome.steps) == 15 * 2
    assert {r.timestep for r in rows_for(outcome, "aco")} == set(range(15))


def test_events_are_recorded_against_their_timestep():
    cfg = make_cfg(churn=0.02, timesteps=25)
    outcome = run_trial(cfg, trial=0, arm_names=["aco"])
    assert outcome.events, "a dynamic scenario must record events"
    for row in outcome.steps:
        recorded = sum(1 for e in outcome.events if e.timestep == row.timestep)
        assert row.num_events == recorded


def test_duplicate_and_unknown_arms_are_rejected():
    cfg = make_cfg()
    with pytest.raises(ValueError, match="duplicate"):
        run_trial(cfg, trial=0, arm_names=["aco", "aco"])
    with pytest.raises(KeyError, match="unknown arm"):
        run_trial(cfg, trial=0, arm_names=["nonexistent"])


# ---------------------------------------------------------------------------
# The shared world
# ---------------------------------------------------------------------------


def test_all_arms_are_scored_against_the_same_optimum():
    """Per timestep there is one world, so one optimum for everyone."""
    cfg = make_cfg(churn=0.02, timesteps=20)
    outcome = run_trial(cfg, trial=0, arm_names=["astar", "aco"])
    by_step: dict[int, set] = {}
    for row in outcome.steps:
        by_step.setdefault(row.timestep, set()).add(row.optimum)
    for timestep, optima in by_step.items():
        assert len(optima) == 1, f"arms disagreed about the optimum at t={timestep}"


def test_astar_is_exactly_the_optimum():
    """The M3 acceptance check.

    A* is exact, so its excess is zero by construction.  Any drift means
    the harness and the oracle are pricing paths differently, and every
    excess figure in the table is then measuring that discrepancy rather
    than search quality.
    """
    cfg = make_cfg(churn=0.02, timesteps=25)
    outcome = run_trial(cfg, trial=0, arm_names=["astar", "aco"])
    for row in rows_for(outcome, "astar"):
        assert row.best_cost == row.optimum
        assert row.excess == 0.0


def test_optimum_moves_within_the_trial():
    cfg = make_cfg(churn=0.02, timesteps=40)
    outcome = run_trial(cfg, trial=0, arm_names=["astar"])
    assert len({r.optimum for r in outcome.steps}) > 1


# ---------------------------------------------------------------------------
# Equal work
# ---------------------------------------------------------------------------


def test_metered_arms_spend_their_whole_allowance():
    cfg = make_cfg(timesteps=12)
    outcome = run_trial(cfg, trial=0, arm_names=["astar", "aco"])
    for row in rows_for(outcome, "aco"):
        assert row.evaluations_spent == cfg.budget.evaluations
    for row in rows_for(outcome, "astar"):
        assert row.evaluations_spent == 0, "an exact method does not compete on budget"


def test_astar_records_its_recomputation_cost():
    cfg = make_cfg(timesteps=10)
    outcome = run_trial(cfg, trial=0, arm_names=["astar"])
    assert all(r.astar_expansions and r.astar_expansions > 0 for r in outcome.steps)


# ---------------------------------------------------------------------------
# Stream independence — the guard against arms perturbing each other
# ---------------------------------------------------------------------------


def test_adding_an_arm_does_not_disturb_the_others():
    """An arm's results must not depend on who else is running.

    Were streams handed out positionally, introducing a third arm would
    shift the randomness of the first two and silently invalidate every
    number already collected for them.
    """
    cfg = make_cfg(churn=0.02, timesteps=20)
    alone = run_trial(cfg, trial=0, arm_names=["aco"])
    together = run_trial(cfg, trial=0, arm_names=["astar", "aco"])

    solo = [(r.timestep, r.best_cost) for r in rows_for(alone, "aco")]
    joint = [(r.timestep, r.best_cost) for r in rows_for(together, "aco")]
    assert solo == joint


def test_arm_order_does_not_matter():
    cfg = make_cfg(churn=0.02, timesteps=15)
    forward = run_trial(cfg, trial=0, arm_names=["astar", "aco"])
    reverse = run_trial(cfg, trial=0, arm_names=["aco", "astar"])
    assert [(r.timestep, r.best_cost) for r in rows_for(forward, "aco")] == [
        (r.timestep, r.best_cost) for r in rows_for(reverse, "aco")
    ]


def test_same_family_receives_the_same_stream():
    """Arms sharing a family are fed identical bits.

    This is what will let a controller-on / controller-off pair differ
    for exactly one reason once controllers exist.
    """
    from dynaswarm.core.generate import build
    from dynaswarm.core.rng import stream

    cfg = make_cfg()
    view, source, target = build(cfg.graph, stream(cfg.root_seed, "graph"))
    first = build_arms(["aco"], view, source, target, cfg.root_seed, trial=3)[0]
    second = build_arms(["aco"], view, source, target, cfg.root_seed, trial=3)[0]
    assert first.optimizer._rng.random(8).tolist() == second.optimizer._rng.random(8).tolist()


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------


#: Fields that legitimately vary between identical runs.  Wall-clock time
#: measures the machine, not the search, and is recorded for cost
#: reporting rather than as part of the result.
_NONDETERMINISTIC = {"wall_ms"}


def _comparable(row) -> tuple:
    return tuple(
        value
        for field, value in dataclasses.asdict(row).items()
        if field not in _NONDETERMINISTIC
    )


def test_trials_reproduce_exactly():
    """Every recorded quantity except timing must be bit-reproducible."""
    cfg = make_cfg(churn=0.02, timesteps=20)
    first = run_trial(cfg, trial=1, arm_names=["astar", "aco"])
    second = run_trial(cfg, trial=1, arm_names=["astar", "aco"])
    assert [_comparable(r) for r in first.steps] == [_comparable(r) for r in second.steps]
    assert [dataclasses.astuple(e) for e in first.events] == [
        dataclasses.astuple(e) for e in second.events
    ]


def test_different_trials_differ():
    cfg = make_cfg(churn=0.02, timesteps=20)
    a = run_trial(cfg, trial=0, arm_names=["aco"])
    b = run_trial(cfg, trial=1, arm_names=["aco"])
    assert [r.best_cost for r in a.steps] != [r.best_cost for r in b.steps]


def test_seeds_are_entropy_not_labels():
    """A disjoint seed pool must present genuinely different instances.

    If seeds only labelled rows while the randomness came from somewhere
    else, then tuning on one pool and evaluating on another would use the
    *same* graphs and event sequences — and the separation that is
    supposed to keep a tuned baseline honest would be decorative.
    """
    cfg = make_cfg(churn=0.02, timesteps=12)
    tuning = run_trial(cfg, trial=0, arm_names=["aco"], seeds=[9000, 9001])
    evaluation = run_trial(cfg, trial=0, arm_names=["aco"], seeds=[1000, 1001])

    assert tuning.steps[0].optimum != evaluation.steps[0].optimum, (
        "different seed pools produced the same problem instance"
    )
    assert tuning.steps[0].seed == 9000
    assert evaluation.steps[0].seed == 1000


def test_the_same_seed_reproduces_regardless_of_trial_index():
    """Entropy follows the seed, so the same seed is the same instance."""
    cfg = make_cfg(churn=0.02, timesteps=12)
    first = run_trial(cfg, trial=0, arm_names=["aco"], seeds=[4242])
    second = run_trial(cfg, trial=3, arm_names=["aco"], seeds=[4242])
    assert [r.optimum for r in first.steps] == [r.optimum for r in second.steps]


def test_empty_seed_pool_is_rejected():
    with pytest.raises(ValueError, match="seed pool"):
        run_trial(make_cfg(), trial=0, arm_names=["aco"], seeds=[])


# ---------------------------------------------------------------------------
# Round-trip through Parquet
# ---------------------------------------------------------------------------


def test_parquet_round_trip_preserves_results(tmp_path):
    cfg = make_cfg(churn=0.02, timesteps=15)
    outcome = run_trial(cfg, trial=0, arm_names=["astar", "aco"])

    with ResultWriter(tmp_path, run_id="test") as writer:
        writer.write(outcome)

    frame = load_steps(tmp_path)
    assert len(frame) == len(outcome.steps)
    assert set(frame.arm) == {"astar", "aco"}
    assert (frame[frame.arm == "astar"].excess == 0.0).all()

    original = [r.best_cost for r in outcome.steps if r.arm == "aco"]
    restored = frame[frame.arm == "aco"].best_cost.tolist()
    assert original == pytest.approx(restored)


def test_map_columns_survive_the_round_trip(tmp_path):
    cfg = make_cfg(timesteps=8)
    outcome = run_trial(cfg, trial=0, arm_names=["aco"])
    with ResultWriter(tmp_path, run_id="test") as writer:
        writer.write(outcome)

    frame = expand_maps(expand_maps(load_steps(tmp_path), "params"), "probe")
    for column in ("params_alpha", "params_rho", "params_n_ants", "probe_lambda_branch"):
        assert column in frame.columns
    assert frame["params_n_ants"].notna().all()


def test_per_trial_excess_reduces_to_one_row_per_arm_trial(tmp_path):
    cfg = make_cfg(timesteps=10)
    with ResultWriter(tmp_path, run_id="test") as writer:
        for trial in range(3):
            writer.write(run_trial(cfg, trial=trial, arm_names=["astar", "aco"]))

    summary = per_trial_excess(load_steps(tmp_path))
    assert len(summary) == 3 * 2
    assert (summary[summary.arm == "astar"].mean_excess == 0.0).all()


def test_conditions_from_one_sweep_are_not_merged(tmp_path):
    """Trials of different conditions must not be averaged together.

    A sweep writes several runs beneath one tree and trial indices
    restart in each, so a grouping that omits the run identity or the
    control settings silently pools trial 0 of one condition with trial 0
    of another.  The result is a number belonging to neither, and it
    looks perfectly ordinary.
    """
    for signal in ("edge_ratio", "volatility"):
        cfg = make_cfg(churn=0.02, timesteps=10)
        cfg.control.signal = signal
        directory = tmp_path / signal
        with ResultWriter(directory, run_id=signal) as writer:
            for trial in range(2):
                writer.write(run_trial(cfg, trial=trial, arm_names=["aco_adaptive"]))

    summary = per_trial_excess(load_steps(tmp_path))
    assert len(summary) == 2 * 2, "conditions were pooled instead of kept apart"
    assert set(summary.signal_kind) == {"edge_ratio", "volatility"}
