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

#: Scenario tiers, as absolute disruptions per timestep.
SCENARIO_RATES = {"static": 0.0, "low": 0.1, "moderate": 0.3, "high": 0.8}


def make_cfg(events_per_step: float, signal: str, timesteps: int = 40) -> Config:
    return Config(
        root_seed=42,
        graph=GraphCfg(n_nodes=30, density=0.3),
        scenario=ScenarioCfg(name="test", events_per_step=events_per_step, timesteps=timesteps),
        experiment=ExperimentCfg(n_trials=1),
        budget=BudgetCfg(evaluations=200),
        control=ControlCfg(signal=signal),
    )


def observe_sequence(signal_kind: str, events_per_step: float, trials: int = 4) -> list[float]:
    """Collect signal readings across several trials of one scenario."""
    readings: list[float] = []
    for trial in range(trials):
        outcome = run_trial(make_cfg(events_per_step, signal_kind), trial, ["aco_adaptive"])
        readings.extend(
            row.signal_value for row in outcome.steps if row.signal_value is not None
        )
    return readings


# ---------------------------------------------------------------------------
# Signal mechanics
# ---------------------------------------------------------------------------


def test_registry_is_complete():
    assert set(SIGNALS) == {"edge_ratio", "volatility", "lambda_branch", "recency"}
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


def test_volatility_saturates_above_a_few_events_per_step():
    """Volatility has a working range, and the disruption rate sets it.

    It asks only "did anything change this step?", so the fraction of
    disturbed steps is ``1 - exp(-rate)``: already 0.86 at two events per
    step, and indistinguishable from one beyond about four.  Past that
    the signal is pinned, has no gradient, and a controller driven by it
    cannot move at all.

    Driving disruption at an absolute rate keeps every scenario tier
    inside the usable range at any graph size.  Tying the rate to edge
    count instead pushes larger graphs past saturation — at a few
    hundred edges even a modest tier delivers enough events that no step
    is ever quiet.

    **The warm-up ramp is asserted, not skipped (F4).**  The signal is a
    mean over a rolling window, so for its first ``window`` steps it is
    averaging fewer samples than it claims and necessarily reads low:
    ``t=0`` is 0.0 because nothing precedes the initial state, then the
    value climbs as the window fills.  Only from ``t = window`` is it
    measuring what it purports to.

    That ramp was invisible for the project's entire history because F1
    made ``t=0`` report a disruption that had not happened, pinning every
    reading at 1.0.  Asserting only the saturated tail would re-hide it
    by a different mechanism, so the whole shape is checked here.
    """
    window = ControlCfg().window
    for rate in (5.0, 8.0):
        cfg = make_cfg(rate, "volatility", timesteps=25)
        outcome = run_trial(cfg, 0, ["aco_adaptive"])
        readings = [r.signal_value for r in outcome.steps if r.signal_value is not None]
        events = [r.num_events for r in outcome.steps]

        # The signal is the mean of "did anything change" over the window
        # so far.  Deriving the expectation from the observed events keeps
        # this an assertion about the *signal*, not about how many
        # disruptions this particular seed happened to draw.
        indicator = [1.0 if n > 0 else 0.0 for n in events]
        expected = [
            float(np.mean(indicator[max(0, k - window + 1) : k + 1]))
            for k in range(len(indicator))
        ]
        assert readings == pytest.approx(expected), (
            f"volatility does not match a {window}-step rolling mean of its own input"
        )

        assert readings[0] == 0.0, "nothing precedes the initial state, so t=0 is quiet"
        assert readings[:window] != readings[window:], "the warm-up ramp must be visible"

        # The original claim, at full strength: once the window is full the
        # signal is pinned at exactly 1.0 and has no gradient left to offer
        # a controller.
        assert min(readings[window:]) == 1.0, "volatility should be pinned at these rates"


#: Signals that average over a rolling window, and therefore have a warm-up.
WINDOWED_SIGNALS = ["edge_ratio", "volatility", "lambda_branch"]


@pytest.mark.parametrize("signal_kind", WINDOWED_SIGNALS)
def test_windowed_signals_ramp_before_their_window_fills(signal_kind: str):
    """F4 — every windowed signal reads low for its first ``window`` steps.

    A rolling mean over a partially-filled window is averaging fewer
    samples than it claims.  For its first ``window`` steps the signal is
    not yet measuring what it purports to, and controllers act from
    ``t = 0`` — so with 60 timesteps and a window of 10, roughly the first
    sixth of every trial drives adaptation from a signal that is still
    warming up.  That is a systematic early-life bias in every adaptive
    arm, and it was invisible for the project's entire history because F1
    made ``t = 0`` report a disruption that had not happened.

    Asserted here for all three windowed signals, since the shape is a
    property of the window rather than of any one signal.  Whether a
    policy should be *permitted* to act before its window fills is a
    design question deferred to the allocation governor in Phase 3; this
    test only pins that the ramp exists and is not mistaken for signal.
    """
    window = ControlCfg().window
    cfg = make_cfg(0.8, signal_kind, timesteps=40)
    outcome = run_trial(cfg, 0, ["aco_adaptive"])
    readings = [r.signal_value for r in outcome.steps if r.signal_value is not None]

    assert len(readings) > window, "trial must outlast the window to show a ramp"
    early, settled = readings[:window], readings[window:]
    assert early != settled[: len(early)], (
        f"{signal_kind} shows no warm-up ramp; either the window is not being "
        "filled progressively or the signal is not windowed after all"
    )


def test_recency_has_no_warm_up_because_it_carries_no_window():
    """The exemption that lets Claim 3 survive F4, asserted rather than assumed.

    ``recency`` is a geometric decay, not a rolling mean: it reads 1.0 on
    the step a disruption lands and decays from there, with no history to
    accumulate and nothing to fill.  It therefore has no warm-up bias.

    This distinction is load-bearing. The three windowed signals are the
    **evidence set** and underpin Claim 2, the diagnosed null.  ``recency``
    drives Claim 3, the allocation thesis.  F4 touches the evidence for
    the null; it does not touch the thesis — and that is true only for as
    long as ``recency`` stays windowless, which is what this asserts.
    """
    from dynaswarm.control.signals import SIGNALS, RecencySignal

    signal = make_signal("recency", window=10)
    assert isinstance(signal, RecencySignal)
    assert not hasattr(signal, "_history"), (
        "recency has acquired a rolling window; it would now carry a warm-up "
        "bias, and Claim 3's exemption from F4 no longer holds"
    )

    # It reaches full scale on the very first disturbed step, with no ramp.
    signal.observe(StepObservation(t=0, n_events=3, n_edges=100, best_cost=1.0))
    assert signal.value() == 1.0, "recency must peak immediately, not accumulate"

    # Every other registered signal is windowed and is covered above.
    assert set(SIGNALS) - {"recency"} == set(WINDOWED_SIGNALS)


def test_scenario_tiers_leave_room_to_recover():
    """Every dynamic tier must leave quiet stretches between disruptions.

    Recovery is only observable if there is calm to recover *into*.  A
    tier that disturbs every timestep produces no transient to measure,
    and any claim about recovery made on it would be vacuous.
    """
    for name, rate in SCENARIO_RATES.items():
        cfg = make_cfg(rate, "volatility", timesteps=60)
        outcome = run_trial(cfg, 0, ["aco_adaptive"])
        quiet = sum(1 for r in outcome.steps if r.num_events == 0) / len(outcome.steps)
        if name == "static":
            assert quiet == 1.0
        else:
            assert 0.2 < quiet < 0.98, (
                f"{name} leaves {quiet:.0%} of steps quiet; a disruption needs "
                "somewhere to decay to"
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
    groups = [observe_sequence(signal_kind, rate) for rate in SCENARIO_RATES.values()]
    _, p_value = scipy_stats.kruskal(*groups)
    gap = separation(groups)

    means = dict(zip(SCENARIO_RATES, [f"{np.mean(g):.4f}" for g in groups], strict=True))
    assert p_value < 0.05, f"{signal_kind} does not distinguish scenarios: {means}"
    assert gap >= MIN_SEPARATION, (
        f"{signal_kind} separates scenarios by only {gap:.1%} of its range: {means}"
    )


def test_branching_does_not_proxy_for_volatility():
    """The internal signal is not a disruption detector, and should not be.

    Branching measures whether *the colony* has collapsed onto one route.
    A colony can stagnate in a calm world and stay diffuse in a chaotic
    one, so there is no reason for it to track the rate — and measured, it
    does not: scenario means sit within a few percent of one another even
    as the reading itself ranges over a factor of two within trials.

    This is asserted rather than merely noted because the tempting error
    is to treat any signal as interchangeable with any other.  Branching
    answers "should I explore *now*", not "how volatile is the world",
    and using it for the latter would be reading it wrongly.
    """
    groups = [observe_sequence("lambda_branch", rate) for rate in SCENARIO_RATES.values()]
    gap = separation(groups)
    assert gap < MIN_SEPARATION, (
        f"branching separated scenarios by {gap:.1%} of range; if it has become a "
        "volatility proxy, this test and the surrounding claim need revisiting"
    )


@pytest.mark.parametrize("signal_kind", ["edge_ratio", "volatility"])
def test_external_signals_are_ordered_by_rate(signal_kind: str):
    """External signals should rise monotonically with disruption.

    Only the environment-facing signals are held to this.  Branching
    measures the search, and a colony can stagnate under any amount of
    the rate, so no ordering is expected of it.
    """
    means = [float(np.mean(observe_sequence(signal_kind, r))) for r in SCENARIO_RATES.values()]
    assert means == sorted(means), f"{signal_kind} not monotone in rate: {means}"


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


def test_unknown_target_raises_rather_than_being_dropped():
    """F2 — a target the optimizer does not declare is an error, not a no-op.

    Silently skipping it produced a controller that logged itself active
    while adapting nothing.  ``bind()`` in ``optimizers/spec.py`` raises on
    the same class of mistake; two components answering one error two
    different ways is how the next person learns the wrong lesson.
    """
    controller = IncrementalController(targets=("nonexistent",), sigma=0.01)
    signal = make_signal("volatility")
    signal.observe(StepObservation(t=0, n_events=1, n_edges=100, best_cost=1.0))
    with pytest.raises(KeyError, match="not parameters of this optimizer"):
        controller.propose(signal, {"rho": 0.1}, 0)


def test_a_known_target_still_adapts_normally():
    """The other direction: raising must not break the working path."""
    controller = IncrementalController(targets=("rho",), sigma=0.01)
    signal = make_signal("volatility", window=4)
    current = {"rho": 0.1}
    for t in range(8):
        signal.observe(StepObservation(t=t, n_events=t % 2, n_edges=100, best_cost=1.0))
        current = controller.propose(signal, current, t)
    assert current["rho"] != 0.1, "a declared target must still move"


def test_a_hybrid_on_the_default_target_now_fails_loudly():
    """The exact configuration that was silently inert (F2).

    A hybrid's parameters are ``aco_``/``pso_``-prefixed, so the default
    ``targets=["rho"]`` matches nothing it declares.  Before the fix this
    arm ran a full trial adapting **nothing** while recording
    ``controller_kind=incremental`` beside a moving signal value — a
    mechanism reporting itself alive while doing no work, which is the
    failure this project has already been bitten by once.
    """
    cfg = make_cfg(events_per_step=0.8, signal="recency", timesteps=10)
    assert cfg.control.targets == ["rho"], "fixture must use the default target"
    with pytest.raises(KeyError, match=r"\['rho'\]"):
        run_trial(cfg, 0, ["hybrid_adaptive"])


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


def test_prescheduled_raises_on_a_target_the_optimizer_does_not_declare():
    """F6 — the identical silent drop, in the arm that can least afford it.

    ``PrescheduledController`` becomes ``ScheduledAllocation`` in Phase 3,
    where it is the honest control for feedback itself: if an open-loop
    schedule matches a signal-driven policy, what helped was *varying*,
    not *sensing*.  A silent drop there varies nothing, so it reproduces
    the frozen arm exactly while logging itself as an active schedule —
    and the conclusion drawn is "an open-loop schedule does not help
    either."  That is a false null on the one arm whose entire job is to
    falsify the control story, and it is indistinguishable from a real
    result.
    """
    controller = PrescheduledController(
        targets=("aco_fraction",), start=1.0, end=2.0, horizon=10
    )
    signal = make_signal("volatility")
    with pytest.raises(KeyError, match=r"\['aco_fraction'\]"):
        controller.propose(signal, {"rho": 0.1}, 0)


def test_prescheduled_still_sweeps_a_declared_target():
    """The guard must reject the unknown without freezing the known."""
    controller = PrescheduledController(
        targets=("aco_fraction",), start=1.0, end=2.0, horizon=11
    )
    signal = make_signal("volatility")
    current = {"aco_fraction": 0.5, "rho": 0.1}
    assert controller.propose(signal, current, 10)["aco_fraction"] == pytest.approx(1.0)


def test_null_controller_is_exempt_from_the_target_guard_by_construction():
    """The third controller cannot carry F2/F6, and this says why.

    ``NullController`` has no ``targets`` field at all — it returns
    ``dict(current)`` unchanged — so there is no target for it to drop
    silently.  Asserting the absence rather than assuming it means the
    exemption survives someone adding target handling later: this test
    fails the moment it stops being true by construction.
    """
    assert not hasattr(NullController(), "targets")
    signal = make_signal("volatility")
    current = {"aco_fraction": 0.5}
    assert NullController().propose(signal, current, 0) == current


def test_unknown_controller_is_rejected():
    with pytest.raises(KeyError, match="unknown controller"):
        make_controller("telepathy")


# ---------------------------------------------------------------------------
# The ablation
# ---------------------------------------------------------------------------


def test_ablation_pair_starts_identical_and_diverges_only_by_control():
    """Fixed and adaptive share bits, so only the controller can separate them."""
    cfg = make_cfg(events_per_step=0.8, signal="volatility", timesteps=30)
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
    cfg = make_cfg(events_per_step=0.8, signal="volatility", timesteps=60)
    cfg.control.sigma = 0.5  # deliberately violent
    outcome = run_trial(cfg, trial=0, arm_names=["aco_adaptive"])
    from dynaswarm.optimizers.aco import ACO

    spec = ACO.PARAM_SPEC["rho"]
    for row in outcome.steps:
        assert spec.lo <= row.params["rho"] <= spec.hi


@pytest.mark.parametrize("signal_kind", sorted(SIGNALS))
def test_every_signal_drives_the_controller(signal_kind: str):
    """Each signal must be able to move a parameter, not merely be read."""
    cfg = make_cfg(events_per_step=0.8, signal=signal_kind, timesteps=40)
    outcome = run_trial(cfg, trial=0, arm_names=["aco_adaptive"])
    values = {row.params["rho"] for row in outcome.steps}
    assert len(values) > 1, f"{signal_kind} never moved the parameter"
    assert {row.signal_kind for row in outcome.steps} == {signal_kind}
