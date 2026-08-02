"""Signal and controller invariants.

The gate in this file is :func:`test_signal_discriminates_scenarios`.  A
controller can only act on what its signal can distinguish, so a signal
whose readings are the same in a calm world and a chaotic one reduces the
whole adaptive arm to a fixed one — while still emitting decision logs
that look like adaptation.  That failure is silent by construction, which
is why it is gated here rather than left to be noticed in results.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats as scipy_stats

from dynaswarm.config import BudgetCfg, Config, ControlCfg, ExperimentCfg, GraphCfg, ScenarioCfg
from dynaswarm.control.controllers import (
    EXPLORE_SIGN,
    IncrementalController,
    NullController,
    PrescheduledController,
    make_controller,
)
from dynaswarm.control.signals import (
    SIGNALS,
    LambdaBranchingSignal,
    StepObservation,
    make_signal,
)
from dynaswarm.harness.trial import run_trial

SCENARIO_CHURN = {"static": 0.0, "low": 0.002, "moderate": 0.006, "high": 0.015}


def make_cfg(churn: float, signal: str, timesteps: int = 40) -> Config:
    return Config(
        root_seed=42,
        graph=GraphCfg(n_nodes=30, density=0.3),
        scenario=ScenarioCfg(name="test", churn=churn, timesteps=timesteps),
        experiment=ExperimentCfg(n_trials=1),
        budget=BudgetCfg(evaluations=200),
        control=ControlCfg(signal=signal),
    )


def observe_sequence(signal_kind: str, churn: float, trials: int = 4) -> list[float]:
    """Collect signal readings across several trials of one scenario."""
    readings: list[float] = []
    for trial in range(trials):
        outcome = run_trial(make_cfg(churn, signal_kind), trial, ["aco_adaptive"])
        readings.extend(
            row.signal_value for row in outcome.steps if row.signal_value is not None
        )
    return readings


# ---------------------------------------------------------------------------
# Signal mechanics
# ---------------------------------------------------------------------------


def test_registry_is_complete():
    assert set(SIGNALS) == {"edge_ratio", "volatility", "lambda_branch"}
    for kind in SIGNALS:
        assert make_signal(kind).name == kind


def test_unknown_signal_is_rejected():
    with pytest.raises(KeyError, match="unknown signal"):
        make_signal("vibes")


def test_window_must_be_positive():
    with pytest.raises(ValueError, match="window"):
        make_signal("volatility", window=0)


def test_edge_ratio_reports_the_fraction_disturbed():
    signal = make_signal("edge_ratio", window=4)
    for _ in range(4):
        signal.observe(StepObservation(t=0, n_events=5, n_edges=100, best_cost=1.0))
    assert signal.value() == pytest.approx(0.05)


def test_volatility_counts_steps_not_events():
    """Ten events in one step is one disturbed step, not ten."""
    signal = make_signal("volatility", window=4)
    for events in (10, 0, 0, 0):
        signal.observe(StepObservation(t=0, n_events=events, n_edges=100, best_cost=1.0))
    assert signal.value() == pytest.approx(0.25)


def test_lambda_branching_ignores_arms_without_telemetry():
    """An arm exposing no branching leaves the signal neutral, not zero-biased."""
    signal = LambdaBranchingSignal(window=4)
    signal.observe(StepObservation(t=0, n_events=0, n_edges=10, best_cost=1.0, probe={}))
    assert signal.value() == 0.0
    signal.observe(
        StepObservation(t=1, n_events=0, n_edges=10, best_cost=1.0, probe={"lambda_branch": 3.0})
    )
    assert signal.value() == pytest.approx(3.0)


def test_branching_is_the_inverted_signal():
    """Low branching means stagnation, so it calls for *more* exploration."""
    assert make_signal("lambda_branch").explore_direction == -1.0
    assert make_signal("volatility").explore_direction == +1.0
    assert make_signal("edge_ratio").explore_direction == +1.0


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------


#: Minimum separation between scenario means, as a fraction of the
#: signal's full observed range, for it to be usable as a volatility
#: detector.
#:
#: A p-value alone is not enough here.  With several hundred readings per
#: scenario, a separation far too small to act on still clears p < 0.05 —
#: measured, the branching signal separates scenarios by 3 % of its range
#: at p = 1e-4.  Requiring a *proportion of range* asks the question that
#: matters: could a controller actually tell these conditions apart?
MIN_SEPARATION = 0.20

#: Signals that watch the environment, and so should track disruption.
EXTERNAL_SIGNALS = ["edge_ratio", "volatility"]


def separation(groups: list[list[float]]) -> float:
    """Spread of group means as a fraction of the pooled observed range."""
    means = [float(np.mean(g)) for g in groups]
    everything = [v for g in groups for v in g]
    span = max(everything) - min(everything)
    return (max(means) - min(means)) / span if span > 0 else 0.0


def test_volatility_saturates_on_larger_graphs():
    """Volatility is only usable while events per step stay near one.

    It asks "did anything change this step?", so it saturates once the
    expected event count exceeds a couple.  Because events are driven at
    a *fraction* of ``|E|``, that count grows with the graph: at n=30
    (|E| ~ 150) the scenario tiers span 0.00 to 0.87, but at n=200
    (|E| ~ 1200) even the moderate tier delivers about seven events per
    step and the signal pins at 1.000 in every scenario.

    A pinned signal has no gradient, so a controller driven by it cannot
    move — measured, the adaptive arm became bit-identical to its frozen
    twin.  This is asserted so the limitation stays visible: volatility
    is not a general-purpose signal, it is one with a working range, and
    the range depends on graph size as well as churn.
    """
    big = GraphCfg(model="geometric", n_nodes=200, density=0.04)
    readings = []
    for churn in (0.006, 0.015):
        cfg = make_cfg(churn, "volatility", timesteps=25)
        cfg.graph = big
        outcome = run_trial(cfg, 0, ["aco_adaptive"])
        readings.extend(
            r.signal_value for r in outcome.steps if r.signal_value is not None
        )

    assert min(readings) > 0.99, (
        "volatility is no longer saturated at n=200; the tiers may have been "
        "recalibrated, and the guidance about its working range needs revisiting"
    )


@pytest.mark.parametrize("signal_kind", EXTERNAL_SIGNALS)
def test_external_signal_discriminates_scenarios(signal_kind: str):
    """An environment-facing signal must read differently in calm and chaos.

    Kruskal-Wallis rather than ANOVA because these readings are bounded,
    skewed, and in the static case constant — none of which suits a
    parametric test.  Significance is necessary but not sufficient, so
    the separation is also required to be large enough to act on.

    A signal failing this cannot drive adaptation: the controller would
    receive near-identical input whatever the conditions and hold its
    parameters still, while logging decisions that suggest otherwise.
    The right response to a failure is to report the signal as
    degenerate, not to keep using it.
    """
    groups = [observe_sequence(signal_kind, churn) for churn in SCENARIO_CHURN.values()]
    _, p_value = scipy_stats.kruskal(*groups)
    gap = separation(groups)

    means = dict(zip(SCENARIO_CHURN, [f"{np.mean(g):.4f}" for g in groups], strict=True))
    assert p_value < 0.05, f"{signal_kind} does not distinguish scenarios: {means}"
    assert gap >= MIN_SEPARATION, (
        f"{signal_kind} separates scenarios by only {gap:.1%} of its range: {means}"
    )


def test_branching_does_not_proxy_for_volatility():
    """The internal signal is not a disruption detector, and should not be.

    Branching measures whether *the colony* has collapsed onto one route.
    A colony can stagnate in a calm world and stay diffuse in a chaotic
    one, so there is no reason for it to track churn — and measured, it
    does not: scenario means sit within a few percent of one another even
    as the reading itself ranges over a factor of two within trials.

    This is asserted rather than merely noted because the tempting error
    is to treat any signal as interchangeable with any other.  Branching
    answers "should I explore *now*", not "how volatile is the world",
    and using it for the latter would be reading it wrongly.
    """
    groups = [observe_sequence("lambda_branch", churn) for churn in SCENARIO_CHURN.values()]
    gap = separation(groups)
    assert gap < MIN_SEPARATION, (
        f"branching separated scenarios by {gap:.1%} of range; if it has become a "
        "volatility proxy, this test and the surrounding claim need revisiting"
    )


@pytest.mark.parametrize("signal_kind", ["edge_ratio", "volatility"])
def test_external_signals_are_ordered_by_churn(signal_kind: str):
    """External signals should rise monotonically with disruption.

    Only the environment-facing signals are held to this.  Branching
    measures the search, and a colony can stagnate under any amount of
    churn, so no ordering is expected of it.
    """
    means = [float(np.mean(observe_sequence(signal_kind, c))) for c in SCENARIO_CHURN.values()]
    assert means == sorted(means), f"{signal_kind} not monotone in churn: {means}"


def test_static_scenario_produces_no_external_pressure():
    for kind in ("edge_ratio", "volatility"):
        assert float(np.mean(observe_sequence(kind, 0.0))) == 0.0


# ---------------------------------------------------------------------------
# Controllers
# ---------------------------------------------------------------------------


def test_null_controller_never_moves_anything():
    controller = NullController()
    signal = make_signal("volatility")
    current = {"rho": 0.1, "alpha": 1.0}
    for t in range(10):
        signal.observe(StepObservation(t=t, n_events=t % 2, n_edges=100, best_cost=1.0))
        assert controller.propose(signal, current, t) == current


def test_incremental_moves_by_exactly_sigma():
    controller = IncrementalController(targets=("rho",), sigma=0.01)
    signal = make_signal("volatility", window=4)

    # Establish a calm baseline, then disturb every step.
    for t in range(6):
        signal.observe(StepObservation(t=t, n_events=0, n_edges=100, best_cost=1.0))
        controller.propose(signal, {"rho": 0.1}, t)

    current = {"rho": 0.1}
    moves = []
    for t in range(6, 12):
        signal.observe(StepObservation(t=t, n_events=3, n_edges=100, best_cost=1.0))
        current = controller.propose(signal, current, t)
        moves.append(current["rho"])

    steps = np.diff([0.1, *moves])
    assert np.allclose(np.abs(steps), 0.01), f"steps were not +/-sigma: {steps}"
    assert moves[-1] > 0.1, "rising volatility should raise evaporation"


def test_incremental_holds_still_on_the_first_reading():
    """Acting on the first reading would be reacting to no history at all."""
    controller = IncrementalController(sigma=0.01)
    signal = make_signal("volatility")
    signal.observe(StepObservation(t=0, n_events=5, n_edges=100, best_cost=1.0))
    assert controller.propose(signal, {"rho": 0.1}, 0) == {"rho": 0.1}


def test_deadband_suppresses_jitter():
    controller = IncrementalController(sigma=0.01, deadband=10.0)
    signal = make_signal("volatility")
    current = {"rho": 0.1}
    for t in range(10):
        signal.observe(StepObservation(t=t, n_events=t % 3, n_edges=100, best_cost=1.0))
        current = controller.propose(signal, current, t)
    assert current == {"rho": 0.1}


def test_inverted_signal_drives_the_opposite_way():
    """Falling branching means stagnation, which should raise evaporation."""
    controller = IncrementalController(targets=("rho",), sigma=0.01)
    signal = LambdaBranchingSignal(window=3)

    def feed(value: float, t: int, current: dict) -> dict:
        signal.observe(
            StepObservation(t=t, n_events=0, n_edges=100, best_cost=1.0,
                            probe={"lambda_branch": value})
        )
        return controller.propose(signal, current, t)

    current = {"rho": 0.1}
    for t in range(4):
        current = feed(5.0, t, current)          # healthy branching
    for t in range(4, 10):
        current = feed(1.0, t, current)          # collapsed onto one route
    assert current["rho"] > 0.1, "stagnation should push toward exploration"


def test_explore_signs_are_declared_for_adapted_parameters():
    assert EXPLORE_SIGN["rho"] > 0, "faster evaporation forgets sooner"
    assert EXPLORE_SIGN["alpha"] < 0, "trusting the trail more is exploitation"
    assert "n_ants" not in EXPLORE_SIGN, "colony size has no unambiguous direction"


def test_prescheduled_ignores_the_signal():
    controller = PrescheduledController(targets=("rho",), start=1.0, end=2.0, horizon=10)
    calm, chaotic = make_signal("volatility"), make_signal("volatility")
    for t in range(10):
        calm.observe(StepObservation(t=t, n_events=0, n_edges=100, best_cost=1.0))
        chaotic.observe(StepObservation(t=t, n_events=9, n_edges=100, best_cost=1.0))

    assert controller.propose(calm, {"rho": 0.1}, 5) == PrescheduledController(
        targets=("rho",), start=1.0, end=2.0, horizon=10
    ).propose(chaotic, {"rho": 0.1}, 5)


def test_prescheduled_sweeps_across_the_horizon():
    controller = PrescheduledController(targets=("rho",), start=1.0, end=3.0, horizon=11)
    signal = make_signal("volatility")
    assert controller.propose(signal, {"rho": 0.1}, 0)["rho"] == pytest.approx(0.1)
    assert controller.propose(signal, {"rho": 0.1}, 10)["rho"] == pytest.approx(0.3)


def test_unknown_controller_is_rejected():
    with pytest.raises(KeyError, match="unknown controller"):
        make_controller("telepathy")


# ---------------------------------------------------------------------------
# The ablation
# ---------------------------------------------------------------------------


def test_ablation_pair_starts_identical_and_diverges_only_by_control():
    """Fixed and adaptive share bits, so only the controller can separate them."""
    cfg = make_cfg(churn=0.015, signal="volatility", timesteps=30)
    outcome = run_trial(cfg, trial=0, arm_names=["aco_fixed", "aco_adaptive"])

    fixed = [r for r in outcome.steps if r.arm == "aco_fixed"]
    adaptive = [r for r in outcome.steps if r.arm == "aco_adaptive"]

    assert fixed[0].best_cost == adaptive[0].best_cost, "arms must start together"
    assert all(r.params["rho"] == fixed[0].params["rho"] for r in fixed), (
        "the frozen arm must never move a parameter"
    )
    assert len({r.params["rho"] for r in adaptive}) > 1, (
        "the adaptive arm must actually move its parameter"
    )


def test_adaptation_stays_within_declared_bounds():
    cfg = make_cfg(churn=0.015, signal="volatility", timesteps=60)
    cfg.control.sigma = 0.5  # deliberately violent
    outcome = run_trial(cfg, trial=0, arm_names=["aco_adaptive"])
    from dynaswarm.optimizers.aco import ACO

    spec = ACO.PARAM_SPEC["rho"]
    for row in outcome.steps:
        assert spec.lo <= row.params["rho"] <= spec.hi


@pytest.mark.parametrize("signal_kind", sorted(SIGNALS))
def test_every_signal_drives_the_controller(signal_kind: str):
    """Each signal must be able to move a parameter, not merely be read."""
    cfg = make_cfg(churn=0.015, signal=signal_kind, timesteps=40)
    outcome = run_trial(cfg, trial=0, arm_names=["aco_adaptive"])
    values = {row.params["rho"] for row in outcome.steps}
    assert len(values) > 1, f"{signal_kind} never moved the parameter"
    assert {row.signal_kind for row in outcome.steps} == {signal_kind}
