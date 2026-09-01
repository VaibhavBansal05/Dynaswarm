"""Analysis invariants: recovery, statistics, figures.

The statistics are where a comparison is most easily overstated, so the
tests here are mostly about refusing to overstate: pairing on trials
rather than timesteps, correcting across the whole family of tests, and
reporting an effect size beside every p-value.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from dynaswarm.analysis.plots import (
    arm_comparison,
    excess_over_time,
    recovery_profile,
    save,
    scaling,
)
from dynaswarm.analysis.recovery import (
    disruptions,
    per_trial_recovery,
    summarise_recovery,
)
from dynaswarm.analysis.stats import (
    cliffs_delta,
    compare_arms,
    holm_correct,
    paired_compare,
)
from dynaswarm.config import BudgetCfg, Config, ExperimentCfg, ScenarioCfg
from dynaswarm.harness.trial import run_trial

# ---------------------------------------------------------------------------
# Recovery
# ---------------------------------------------------------------------------


def test_finds_a_disruption_and_measures_the_response():
    excess = [0.05, 0.05, 0.20, 0.14, 0.09, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05]
    events = [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    found = disruptions(excess, events, min_horizon=4)

    assert len(found) == 1
    assert found[0].timestep == 2
    assert found[0].baseline == pytest.approx(0.05)
    assert found[0].damage == pytest.approx(0.15)
    assert found[0].recovery == 3


def test_late_disruptions_are_skipped_not_counted_as_failures():
    """An arm hit on the final step has no chance to recover.

    Scoring that as unrecovered would penalise whichever arm happened to
    be disrupted late, which is right-censoring: it falls unevenly across
    arms and would read as a genuine difference between them.
    """
    excess = [0.05] * 10 + [0.30]
    events = [0] * 10 + [1]
    assert disruptions(excess, events, min_horizon=5) == []


def test_a_disruption_without_prior_calm_is_skipped():
    """Damage measured during another disruption's tail is not damage."""
    excess = [0.05, 0.20, 0.22, 0.10, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05]
    events = [0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0]
    found = disruptions(excess, events, min_horizon=4)
    assert all(f.timestep != 2 for f in found), "back-to-back events need a clean baseline"


def test_unrecovered_disruption_is_reported_as_such():
    excess = [0.05, 0.05, 0.40] + [0.40] * 12
    events = [0, 0, 1] + [0] * 12
    found = disruptions(excess, events)
    assert len(found) == 1 and found[0].recovery is None
    summary = summarise_recovery(found)
    assert summary["recovered_fraction"] == 0.0
    assert np.isnan(summary["mean_recovery"])


def test_empty_summary_is_nan_not_zero():
    """An absent measurement must not be averaged in as a good one."""
    summary = summarise_recovery([])
    assert np.isnan(summary["mean_damage"])
    assert summary["n_disruptions"] == 0


def test_a_helpful_disruption_shows_negative_damage():
    """An event can open a shorter route; the sign should say so."""
    found = disruptions(
        [0.20, 0.20, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05],
        [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        min_horizon=4,
    )
    assert found and found[0].damage < 0


def test_per_trial_recovery_covers_every_condition():
    cfg = Config(
        scenario=ScenarioCfg(name="t", events_per_step=0.8, timesteps=40),
        experiment=ExperimentCfg(n_trials=2),
        budget=BudgetCfg(evaluations=150),
    )
    frames = []
    for trial in range(2):
        rows = run_trial(cfg, trial, ["astar", "aco"]).steps
        frames.append(pd.DataFrame([r.__dict__ for r in rows]))
    frame = pd.concat(frames, ignore_index=True)

    summary = per_trial_recovery(frame)
    assert len(summary) == 4  # two arms, two trials
    assert {"mean_damage", "mean_recovery", "settled_excess"} <= set(summary.columns)
    # A* is exact, so it is never damaged and never needs to recover.
    astar = summary[summary.arm == "astar"]
    assert (astar.settled_excess.fillna(0.0) == 0.0).all()


def test_recovery_time_is_not_structurally_pinned_at_zero():
    """The instrument must be able to register a non-zero recovery.

    This guards a failure that is far more dangerous than a crash: under
    F1 the disruption markers sat one step early, so ``excess[t]`` was the
    *pre*-disruption reading and therefore already inside the recovery
    band.  Every transient in every arm and every scenario scored as
    recovering in **0.000 steps**, and the metric — a measurement
    instrument reading a constant — looked entirely plausible doing it.

    "The hybrid recovers immediately" is a flattering result nobody would
    have interrogated, and `ARCHITECTURE.md` §11.2 makes recovery a
    first-class experiment, so it would have been reported.

    Asserted on pooled transients from several trials rather than on a
    single mean, because a mean over three disruptions can legitimately be
    zero.  What may never happen is *every* transient recovering instantly.
    """
    from dynaswarm.analysis.recovery import disruptions
    from dynaswarm.config import GraphCfg

    cfg = Config(
        graph=GraphCfg(n_nodes=30, density=0.3),
        scenario=ScenarioCfg(name="r", events_per_step=0.8, timesteps=40),
        experiment=ExperimentCfg(n_trials=6),
        budget=BudgetCfg(evaluations=150),
    )
    pooled = []
    for trial in range(6):
        rows = run_trial(cfg, trial, ["aco", "hybrid"]).steps
        for arm in ("aco", "hybrid"):
            of_arm = [r for r in rows if r.arm == arm]
            excess = [None if r.excess is None else float(r.excess) for r in of_arm]
            events = [r.num_events for r in of_arm]
            pooled.extend(disruptions(excess, events))

    recovered = [t.recovery for t in pooled if t.recovery is not None]
    assert recovered, "no transient was scoreable; the fixture is not exercising recovery"
    assert any(r > 0 for r in recovered), (
        f"all {len(recovered)} scored transients recovered in 0 steps. That is the "
        "signature of disruption markers misaligned against the quality series — "
        "the metric is reading a constant, not measuring recovery"
    )


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


def test_paired_test_detects_a_real_shift_and_ignores_noise():
    rng = np.random.default_rng(0)
    base = rng.normal(0.05, 0.01, 20)
    shifted = base + 0.005
    real = paired_compare(base, shifted, "real")
    noise = paired_compare(base, base + rng.normal(0, 1e-5, 20), "noise")
    assert real.p_value < 0.01
    assert noise.p_value > 0.05


def test_mismatched_samples_are_refused():
    """Unequal lengths mean the data is not paired, whatever it looks like."""
    with pytest.raises(ValueError, match="align"):
        paired_compare(np.zeros(5), np.zeros(4))


def test_identical_arms_report_no_effect_rather_than_crashing():
    """A frozen controller makes its arm identical to its twin.

    That is a result worth seeing as p = 1, not an exception: it says the
    controller never moved.
    """
    values = np.linspace(0.01, 0.09, 12)
    result = paired_compare(values, values.copy())
    assert result.p_value == 1.0
    assert not result.significant


def test_holm_is_monotone_and_more_conservative_than_raw():
    raw = [0.001, 0.02, 0.04, 0.3]
    comparisons = [
        paired_compare(np.zeros(3), np.zeros(3), f"c{i}") for i in range(len(raw))
    ]
    for c, p in zip(comparisons, raw, strict=True):
        c.p_value = p
    holm_correct(comparisons)

    adjusted = [c.p_adjusted for c in comparisons]
    assert adjusted == sorted(adjusted), "adjusted values must not decrease"
    assert all(a >= r for a, r in zip(adjusted, raw, strict=True))
    assert comparisons[0].significant and not comparisons[-1].significant


def test_holm_rescues_a_borderline_family():
    """Four tests at p = 0.04 are what multiple comparison is for."""
    comparisons = [paired_compare(np.zeros(3), np.zeros(3), f"c{i}") for i in range(4)]
    for c in comparisons:
        c.p_value = 0.04
    holm_correct(comparisons)
    assert not any(c.significant for c in comparisons), (
        "uncorrected, all four would have looked real"
    )


def test_cliffs_delta_spans_its_range():
    low, high = np.arange(10.0), np.arange(100.0, 110.0)
    assert cliffs_delta(high, low)[0] == pytest.approx(1.0)
    assert cliffs_delta(low, high)[0] == pytest.approx(-1.0)
    assert abs(cliffs_delta(low, low)[0]) < 1e-9
    assert cliffs_delta(low, low)[1] == "negligible"


def test_compare_arms_returns_one_row_per_condition():
    rng = np.random.default_rng(1)
    rows = []
    for scenario in ("moderate", "high"):
        for arm, centre in (("a", 0.05), ("b", 0.06)):
            for trial in range(10):
                rows.append(
                    {
                        "scenario": scenario,
                        "signal_kind": "volatility",
                        "arm": arm,
                        "trial": trial,
                        "mean_excess": rng.normal(centre, 0.005),
                    }
                )
    table = compare_arms(pd.DataFrame(rows), "a", "b")
    assert len(table) == 2
    assert {"p_value", "p_holm", "cliffs_delta", "significant"} <= set(table.columns)
    assert (table.p_holm >= table.p_value).all()


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------


def _frame() -> pd.DataFrame:
    cfg = Config(
        scenario=ScenarioCfg(name="t", events_per_step=0.8, timesteps=25),
        experiment=ExperimentCfg(n_trials=2),
        budget=BudgetCfg(evaluations=150),
    )
    frames = [
        pd.DataFrame([r.__dict__ for r in run_trial(cfg, t, ["astar", "aco"]).steps])
        for t in range(2)
    ]
    return pd.concat(frames, ignore_index=True)


def test_figures_render_and_write(tmp_path):
    frame = _frame()
    assert save(excess_over_time(frame), tmp_path / "over_time.png").exists()
    assert save(recovery_profile(frame), tmp_path / "recovery.png").exists()

    per_trial = frame.groupby(["scenario", "arm", "trial"], as_index=False).excess.mean()
    per_trial = per_trial.rename(columns={"excess": "mean_excess"})
    assert save(arm_comparison(per_trial), tmp_path / "arms.png").exists()


def test_scaling_figure_renders_across_sizes(tmp_path):
    """The figure that decides whether the cost premise holds.

    A* is exact, so it can only be beaten on cost; if its cost does not
    grow with graph size there is nothing for a metaheuristic to win, and
    this is where that shows.
    """
    from dynaswarm.config import GraphCfg

    frames = []
    for graph in (
        GraphCfg(n_nodes=30, density=0.3),
        GraphCfg(model="geometric", n_nodes=120, density=0.05),
    ):
        cfg = Config(
            graph=graph,
            scenario=ScenarioCfg(name="t", events_per_step=0.3, timesteps=12),
            experiment=ExperimentCfg(n_trials=1),
            budget=BudgetCfg(evaluations=150),
        )
        rows = run_trial(cfg, 0, ["astar", "aco"]).steps
        frames.append(pd.DataFrame([r.__dict__ for r in rows]))

    frame = pd.concat(frames, ignore_index=True)
    assert frame.n_nodes.nunique() == 2
    assert save(scaling(frame), tmp_path / "scaling.png").exists()


def test_replay_reads_what_it_needs_from_results(tmp_path):
    """The viewer must be able to reconstruct a run from stored rows alone.

    It deliberately imports nothing from the harness, so the only way it
    can go stale is if a column it depends on stops being recorded.  This
    checks those columns rather than opening a window.
    """
    from dynaswarm.analysis.load import load_events, load_steps
    from dynaswarm.io.writer import ResultWriter

    cfg = Config(
        scenario=ScenarioCfg(name="t", events_per_step=0.8, timesteps=10),
        experiment=ExperimentCfg(n_trials=1),
        budget=BudgetCfg(evaluations=150),
    )
    with ResultWriter(tmp_path, run_id="replay") as writer:
        writer.write(run_trial(cfg, 0, ["astar"]))

    steps, events = load_steps(tmp_path, run_class=None), load_events(tmp_path, run_class=None)
    required = {"best_path", "n_nodes", "seed", "timestep", "num_events",
                "optimum", "best_cost", "excess", "scenario", "trial", "arm"}
    assert required <= set(steps.columns)
    assert {"timestep", "u", "v"} <= set(events.columns)
    assert len(list(steps.best_path.iloc[0])) >= 2, "a route needs at least two nodes"
