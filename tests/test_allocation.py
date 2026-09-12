"""The allocation package (§7).

Everything the thesis claims runs through this machine, so the two Layer 1
invariants are proved here rather than asserted, and every test drives the
production entry point — Entry 019's lesson, which appeared in the segment
written to prevent it.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from dynaswarm.allocation import (
    POLICIES,
    AllocationGovernor,
    AllocationObservation,
    make_policy,
    observe,
)
from dynaswarm.allocation.governor import FRACTION_HIGH, FRACTION_LOW, MAX_AT_BOUND

ROOT = Path(__file__).resolve().parents[1]


def an_observation(**overrides) -> AllocationObservation:
    """Built through `observe`, the production constructor."""
    fields = dict(
        t=0,
        events_this_step=0,
        current_fraction=0.5,
        budget=300,
        probe={"aco_lambda_branch": 2.0, "pso_diversity": 0.1},
        own_cost=100.0,
        previous_cost=None,
        path_invalidated=False,
        recency=0.0,
        steps_since_disruption=0,
    )
    fields.update(overrides)
    return observe(**fields)


# ---------------------------------------------------------------------------
# T1 — the two hard constraints, proved
# ---------------------------------------------------------------------------


def test_an_observation_can_be_built_with_the_oracle_unreachable():
    """**I1, proved rather than asserted.**

    §7.2 removed `excess_last_step` because excess is `cost / optimum - 1`
    and a policy knowing its own excess knows how far from optimal it is
    — information no deployed router has.

    Asserting "we did not call the oracle" is not the same as proving it
    cannot be called, and this project has a rule about that from four
    separate segments. So the oracle is made genuinely unimportable, the
    way segment 6 made FastAPI unimportable, and an observation is built
    anyway.
    """
    program = textwrap.dedent(
        """
        import sys

        class Blocker:
            def find_module(self, name, path=None):
                return self.find_spec(name, path)

            def find_spec(self, name, path=None, target=None):
                if name.endswith("oracle") or name.endswith("core.oracle"):
                    raise ImportError(f"blocked: {name}")
                return None

        sys.meta_path.insert(0, Blocker())

        # Prove the blocker actually bites before relying on it.
        try:
            import dynaswarm.core.oracle  # noqa: F401
        except ImportError:
            pass
        else:
            raise SystemExit("the oracle was importable; the test proves nothing")

        from dynaswarm.allocation import observe

        obs = observe(
            t=7, events_this_step=2, current_fraction=0.5, budget=300,
            probe={"aco_lambda_branch": 3.0, "pso_diversity": 0.2},
            own_cost=120.0, previous_cost=100.0, path_invalidated=True,
            recency=1.0, steps_since_disruption=0,
        )
        assert obs.own_cost == 120.0 and obs.own_cost_delta == 20.0
        assert not hasattr(obs, "excess_last_step")
        print("observation built with the oracle unreachable")
        """
    )
    done = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True, cwd=ROOT
    )
    assert done.returncode == 0, done.stdout + done.stderr
    assert "observation built with the oracle unreachable" in done.stdout


def test_the_observation_carries_no_oracle_derived_field():
    """The field list itself, pinned against reintroduction.

    §7.2's list is exact. `own_cost` and `path_invalidated` exist
    *because* `excess_last_step` had to be removed, so adding anything
    shaped like excess, optimum or a ratio to them reopens I1.
    """
    obs = an_observation()
    banned = {"excess", "optimum", "excess_last_step", "gap", "ratio_to_optimal"}
    present = set(vars(obs))
    assert not (banned & present), f"an oracle-derived field appeared: {banned & present}"
    assert {"own_cost", "own_cost_delta", "path_invalidated"} <= present, (
        "the self-knowledge fields that replaced excess_last_step are missing"
    )


def test_every_observation_field_is_supplied_by_the_caller():
    """**I2.** The observation cannot reach forward because it cannot reach.

    `observe` fetches nothing — no timeline, no view, no optimizer. Every
    value arrives as an argument the caller already holds about `t` or
    earlier, so a field from `t+1` would have to be handed in
    deliberately. F1 was this defect one layer down.
    """
    import inspect

    from dynaswarm.allocation import observation as module

    source = inspect.getsource(module.observe)
    for reach in ("state_at", "events_at", "shortest_path", "schedule[", "timeline"):
        assert reach not in source, f"observe() reaches into {reach}"

    supplied = set(inspect.signature(module.observe).parameters)
    derived = {"recency", "steps_since_disruption", "events_this_step"}
    assert derived <= supplied, "a t-dependent field is computed here rather than passed"


def test_the_observation_is_frozen():
    """A policy must not edit its own inputs and pass them on."""
    obs = an_observation()
    from dataclasses import FrozenInstanceError

    with pytest.raises(FrozenInstanceError):
        obs.current_fraction = 0.9  # type: ignore[misc]


def test_own_cost_delta_is_none_when_there_is_nothing_to_compare():
    """Expected from the definition: a delta needs two costs."""
    assert an_observation(own_cost=100.0, previous_cost=None).own_cost_delta is None
    assert an_observation(own_cost=None, previous_cost=100.0).own_cost_delta is None
    assert an_observation(own_cost=90.0, previous_cost=100.0).own_cost_delta == -10.0


# ---------------------------------------------------------------------------
# T2 — the policies
# ---------------------------------------------------------------------------


def test_frozen_allocation_never_moves_the_split():
    policy = make_policy("frozen")
    for fraction in (0.2, 0.5, 0.8):
        assert policy.propose(an_observation(current_fraction=fraction)) == fraction


def test_scheduled_allocation_actually_varies_at_default_construction():
    """**F7 dies here, and this is the test that kills it.**

    Its predecessor was built with no arguments, giving `start == end ==
    1.0`, so it varied nothing while logging itself as an active
    schedule — results identical to the frozen arm, and a false null on
    the one arm whose job is to falsify the control story.

    Entry 005's bar: a control that does not vary is not a control. So
    this asserts the DEFAULTS sweep, not that the class is capable of
    sweeping when someone remembers to configure it.
    """
    policy = make_policy("scheduled")            # no arguments, deliberately
    values = [policy.propose(an_observation(t=t)) for t in range(60)]

    assert len(set(values)) > 1, "the default schedule varies nothing — F7 again"
    assert values[0] != values[-1], "the schedule starts and ends in the same place"
    assert abs(values[-1] - values[0]) > 0.25, (
        f"the default sweep is too small to be a control: {values[0]} -> {values[-1]}"
    )
    assert values == sorted(values, reverse=True), "the sweep is not monotone as defined"


def test_scheduled_allocation_ignores_everything_but_t():
    """The honest control for feedback: it must not sense.

    Ported from `test_prescheduled_ignores_the_signal`, which tested the
    same property of the class this replaces.
    """
    policy = make_policy("scheduled")
    calm = an_observation(t=5, recency=0.0, events_this_step=0)
    chaotic = an_observation(
        t=5, recency=1.0, events_this_step=9, path_invalidated=True,
        probe={"aco_lambda_branch": 99.0, "pso_diversity": 0.9},
    )
    assert policy.propose(calm) == policy.propose(chaotic)


def test_scheduled_allocation_sweeps_across_its_horizon():
    """Ported from `test_prescheduled_sweeps_across_the_horizon`.

    Expected values from the definition: a linear interpolation from
    `start` to `end` over `horizon - 1` steps.
    """
    policy = make_policy("scheduled", start=1.0, end=3.0, horizon=11)
    assert policy.propose(an_observation(t=0)) == pytest.approx(1.0)
    assert policy.propose(an_observation(t=5)) == pytest.approx(2.0)
    assert policy.propose(an_observation(t=10)) == pytest.approx(3.0)
    assert policy.propose(an_observation(t=99)) == pytest.approx(3.0), "past the horizon"


def test_incremental_allocation_does_not_act_on_its_first_reading():
    """Acting on the first reading means reacting to the absence of history."""
    policy = make_policy("incremental")
    assert policy.propose(an_observation(t=0, recency=1.0)) == 0.5


def test_incremental_allocation_moves_by_exactly_sigma():
    """Expected from the rule: pressure above the baseline buys PSO.

    Sign carried over from `EXPLORE_SIGN['aco_fraction'] = -1`: right
    after a disruption the trail is the least trustworthy thing in the
    system, so rising recency shifts budget to the memoryless component.
    """
    policy = make_policy("incremental", sigma=0.01)
    policy.propose(an_observation(t=0, recency=0.0))      # establishes the baseline
    after = policy.propose(an_observation(t=1, recency=1.0))
    assert after == pytest.approx(0.5 - 0.01), "a rising signal did not buy PSO"


def test_an_unknown_policy_raises_rather_than_defaulting():
    with pytest.raises(KeyError, match="unknown allocation policy"):
        make_policy("telepathy")


def test_learned_allocation_is_not_registered():
    """§7.2 registers it; D7 and O2 defer it to Phase 4 with sign-off.

    Pinned so it cannot arrive without that conversation.
    """
    assert "learned" not in POLICIES, "LearnedAllocation shipped without sign-off"


# ---------------------------------------------------------------------------
# T3/T4 — the governor, and the automated saturation check
# ---------------------------------------------------------------------------


class _Wants:
    """A policy that asks for a fixed series, so clipping is controllable."""

    name = "wants"

    def __init__(self, series):
        self._series = list(series)
        self._i = 0

    def propose(self, obs):
        value = self._series[min(self._i, len(self._series) - 1)]
        self._i += 1
        return value

    def reset(self):
        self._i = 0


def test_the_governor_clamps_to_the_declared_bounds():
    """At 0 or 1 one component receives nothing and the hybrid is one solver."""
    governor = AllocationGovernor(_Wants([5.0] * 40), sigma_max=1.0)
    for t in range(40):
        governor.step(an_observation(t=t))
    assert max(governor.applied) == pytest.approx(FRACTION_HIGH)

    governor = AllocationGovernor(_Wants([-5.0] * 40), sigma_max=1.0)
    for t in range(40):
        governor.step(an_observation(t=t))
    assert min(governor.applied) == pytest.approx(FRACTION_LOW)


def test_the_governor_rate_limits_each_step():
    """Expected from the rule: |delta| <= sigma_max, computed here."""
    governor = AllocationGovernor(_Wants([0.9]), sigma_max=0.05, fraction=0.5)
    assert governor.step(an_observation(t=0)) == pytest.approx(0.55)
    assert governor.step(an_observation(t=1)) == pytest.approx(0.60)


def test_proposed_and_applied_are_recorded_separately():
    """**The pair that cannot be one number.**

    A policy pressing hard against a clamp and a policy proposing
    exactly the clamped value are identical in the applied series and
    mean opposite things about whether the policy is working.
    """
    governor = AllocationGovernor(_Wants([0.9, 0.9, 0.9]), sigma_max=0.05, fraction=0.5)
    for t in range(3):
        governor.step(an_observation(t=t))

    assert governor.proposed == [0.9, 0.9, 0.9], "the policy's own ask was not recorded"
    assert governor.applied == pytest.approx([0.55, 0.60, 0.65])
    assert governor.saturation()["clipped"] == pytest.approx(1.0), (
        "every step was clipped and the record does not show it"
    )


def test_a_run_that_never_moves_is_not_reportable():
    """A split that never moved measured nothing about allocation."""
    governor = AllocationGovernor(make_policy("frozen"))
    for t in range(30):
        governor.step(an_observation(t=t, current_fraction=governor.fraction))

    stats = governor.saturation()
    assert stats["moved"] == 0.0
    assert stats["distinct"] == 1.0
    assert not governor.reportable(), "a frozen run was declared reportable"


def test_a_run_pinned_to_a_bound_is_not_reportable():
    """It measured the bound, not the policy. §7.2's 20% rule, automated."""
    # Rate-limited, so it ramps through several distinct values before
    # pinning — the realistic saturated run. Jumping straight to the
    # bound would give distinct == 1 and fail the *moved* rule instead,
    # which is a different defect.
    governor = AllocationGovernor(_Wants([5.0] * 30), sigma_max=0.05)
    for t in range(30):
        governor.step(an_observation(t=t))

    stats = governor.saturation()
    assert stats["moved"] == 1.0, "the fixture never moved, so it tests the wrong rule"
    assert stats["at_bound"] > MAX_AT_BOUND
    assert not governor.reportable(), "a saturated run was declared reportable"


def test_a_healthy_run_is_reportable():
    """The other direction: a check that never passes is not a check."""
    governor = AllocationGovernor(make_policy("scheduled"), sigma_max=1.0)
    for t in range(60):
        governor.step(an_observation(t=t))

    stats = governor.saturation()
    assert stats["moved"] == 1.0
    assert stats["at_bound"] < MAX_AT_BOUND, f"at_bound was {stats['at_bound']}"
    assert governor.reportable()


def test_reset_clears_the_record_and_the_policy():
    governor = AllocationGovernor(make_policy("incremental"))
    for t in range(5):
        governor.step(an_observation(t=t, recency=1.0))
    assert governor.proposed and governor.applied

    governor.reset()
    assert governor.proposed == [] and governor.applied == []
    assert governor.saturation()["distinct"] == 0.0


def test_the_governor_is_the_only_thing_that_enforces():
    """§7.2: policies propose, the governor disposes.

    A policy that clamped internally would hide its own saturation, and
    the record would show a well-behaved policy that was in fact pinned.
    """
    import inspect

    from dynaswarm.allocation import policies

    source = inspect.getsource(policies)
    for guard in ("FRACTION_LOW", "FRACTION_HIGH", "sigma_max"):
        assert guard not in source, f"a policy is enforcing {guard} itself"


# ---------------------------------------------------------------------------
# Coverage inherited from the class F7 killed
# ---------------------------------------------------------------------------
#
# `PrescheduledController` is gone. Its four tests were not deleted — the
# behaviour they asserted is asserted here against `ScheduledAllocation`,
# which took over its role. Two of them tested the F2/F6 silent-drop
# guard on `targets`, and that guard has no counterpart: a policy returns
# a target fraction rather than naming parameters to nudge, so there is
# nothing to drop silently. That is a property of the redesign and is
# pinned below rather than assumed.


def test_a_policy_cannot_silently_drop_what_it_was_asked_to_change():
    """F2 and F6's failure mode is structurally absent here.

    Both were the same bug: a controller handed `targets` it did not
    recognise carried on, adapting nothing while logging itself active.
    An allocation policy has no `targets` — it returns the split it wants
    — so there is no name to mismatch and nothing to drop.

    Asserted rather than assumed, so that reintroducing a name-based
    interface fails here first.
    """
    for kind in POLICIES:
        policy = make_policy(kind)
        assert not hasattr(policy, "targets"), (
            f"{kind} has a targets list; F2/F6's failure mode is reachable again"
        )
        proposal = policy.propose(an_observation(t=3, recency=1.0))
        assert isinstance(proposal, float), f"{kind} did not return a fraction"


def test_every_registered_policy_survives_a_full_run_and_reset():
    """Each policy driven through the governor, the production path.

    Entry 019's rule: the test must call the entry point, not a
    re-implementation of it.
    """
    for kind in POLICIES:
        governor = AllocationGovernor(make_policy(kind))
        for t in range(60):
            governor.step(an_observation(
                t=t,
                recency=1.0 if t % 7 == 0 else 0.7 ** (t % 7),
                events_this_step=3 if t % 7 == 0 else 0,
                current_fraction=governor.fraction,
            ))
        assert len(governor.applied) == 60
        assert all(FRACTION_LOW <= v <= FRACTION_HIGH for v in governor.applied), (
            f"{kind} escaped the bounds"
        )
        governor.reset()
        assert governor.applied == []


def test_the_probe_keys_the_observation_reads_are_keys_the_hybrid_emits():
    """**The cross-module contract, which nothing else checks.**

    `observe` pulls `aco_lambda_branch` and `pso_diversity` out of the
    arm's probe with `.get(..., 0.0)`. If either name stops matching what
    the Hybrid emits — a rename inside ACO would do it — the default
    takes over and **every policy sees 0.0 for colony stagnation and
    swarm convergence, forever, with nothing raised.** Two of §7.2's
    eleven fields become constants and the thesis runs on them.

    Found by mutation: renaming the key to one that does not exist passed
    the entire suite. The names are asserted against a real Hybrid's real
    probe rather than against a list, so the contract is checked at both
    ends.
    """
    from dynaswarm.config import GraphCfg
    from dynaswarm.core.generate import build
    from dynaswarm.core.meter import EvaluationMeter
    from dynaswarm.core.rng import stream
    from dynaswarm.optimizers.hybrid import Hybrid

    view, source, target = build(
        GraphCfg(model="geometric", n_nodes=200, density=0.04), stream(1000, "graph")
    )
    hybrid = Hybrid(view, source, target, stream(1000, "hybrid"), {})
    hybrid.spend(EvaluationMeter(300))
    emitted = hybrid.probe()

    import inspect

    from dynaswarm.allocation import observation as module

    source_text = inspect.getsource(module.observe)
    read = {
        name for name in emitted
        if f'probe.get("{name}"' in source_text
    }
    assert read, "observe() reads no probe key at all; the wiring is gone"

    # Every key observe() asks for must be one the Hybrid actually emits.
    import re

    asked = set(re.findall(r'probe\.get\("([^"]+)"', source_text))
    missing = asked - set(emitted)
    assert not missing, (
        f"observe() reads probe keys the Hybrid never emits: {sorted(missing)} — "
        f"each silently becomes 0.0 for every policy, forever"
    )

    # And the values must not be the silent default when real telemetry exists.
    obs = observe(
        t=0, events_this_step=0, current_fraction=0.5, budget=300, probe=emitted,
        own_cost=100.0, previous_cost=None, path_invalidated=False,
        recency=0.0, steps_since_disruption=0,
    )
    assert obs.aco_lambda_branch != 0.0, "colony stagnation read as the default"
    assert obs.pso_diversity != 0.0, "swarm convergence read as the default"
