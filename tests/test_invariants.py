"""Layer 1 — invariants that make cheating structurally impossible.

These do not check that a result is good.  They check that it *could* have
been obtained honestly: that no component saw the oracle's answer, that
none read a timestep that had not happened yet, and that no arm reached
into another arm.  A comparison study can produce entirely plausible
numbers while violating any of the three, which is why they are asserted
rather than reviewed.

All three are implemented **test-side**.  Production code carries no
scaffolding for them: the timeline is observed by substituting a
recording subclass at the point the harness constructs it, and the
optimizers are inspected by walking their object graphs from outside.
That costs zero statements against the science-surface cap and, more
importantly, means the thing under test is the real code path rather than
an instrumented variant of it.
"""

from __future__ import annotations

import numpy as np

from dynaswarm.config import BudgetCfg, Config, ExperimentCfg, GraphCfg, ScenarioCfg
from dynaswarm.core.generate import build
from dynaswarm.core.rng import stream
from dynaswarm.core.timeline import GraphTimeline
from dynaswarm.harness import trial as trial_module
from dynaswarm.harness.arm import build_arms
from dynaswarm.harness.trial import run_trial

ARMS = ["astar", "aco", "pso", "hybrid"]


def make_cfg(timesteps: int = 12) -> Config:
    return Config(
        root_seed=42,
        graph=GraphCfg(n_nodes=30, density=0.3),
        scenario=ScenarioCfg(name="inv", events_per_step=0.8, timesteps=timesteps),
        experiment=ExperimentCfg(n_trials=1),
        budget=BudgetCfg(evaluations=120),
    )


# ---------------------------------------------------------------------------
# Object-graph walk, shared by I1 and I3
# ---------------------------------------------------------------------------

#: Types that cannot hold a reference to anything, so recursion stops.
_LEAVES = (int, float, complex, bool, str, bytes, type(None), np.ndarray, np.generic)


def reachable(root: object, limit: int = 20000) -> list[object]:
    """Every object reachable from ``root`` by attribute or container.

    A field-list check only catches the mistake someone already thought
    of.  Walking the graph catches the ones nobody did — a policy that
    stashed a whole ``StepRow``, an optimizer holding the harness, an arm
    that ended up pointing at another arm's internals.

    Numpy arrays are treated as leaves: their contents are numbers, they
    cannot reference a Python object, and walking a few thousand floats
    per optimizer buys nothing.

    Args:
        root: Where to start.
        limit: Safety bound on objects visited.

    Returns:
        The objects found, ``root`` included.
    """
    seen: dict[int, object] = {}
    queue: list[object] = [root]

    while queue and len(seen) < limit:
        obj = queue.pop()
        if isinstance(obj, _LEAVES) or id(obj) in seen:
            continue
        seen[id(obj)] = obj

        if isinstance(obj, dict):
            queue.extend(obj.keys())
            queue.extend(obj.values())
        elif isinstance(obj, (list, tuple, set, frozenset)):
            queue.extend(obj)
        else:
            attrs = getattr(obj, "__dict__", None)
            if attrs:
                queue.extend(attrs.values())
            for slot in getattr(type(obj), "__slots__", ()):
                if hasattr(obj, slot):
                    queue.append(getattr(obj, slot))

    return list(seen.values())


def attribute_names(root: object) -> set[str]:
    """Every attribute name appearing anywhere in ``root``'s object graph."""
    names: set[str] = set()
    for obj in reachable(root):
        attrs = getattr(obj, "__dict__", None)
        if attrs:
            names.update(attrs.keys())
    return names


# ---------------------------------------------------------------------------
# I1 — no oracle leakage
# ---------------------------------------------------------------------------

#: Names that would denote the oracle's answer, or a quantity computed
#: from it.  ``excess = cost / optimum - 1`` is the canonical forbidden
#: value (D26): an arm that knows its own excess knows how far from
#: optimal it is, which no deployed router does.
_ORACLE_NAMES = {
    "optimum",
    "_optimum",
    "optima",
    "excess",
    "_excess",
    "best_known",
    "_best_known",
    "true_cost",
    "_true_cost",
}


def test_no_optimizer_holds_an_oracle_derived_value():
    """I1 — no optimizer may hold ``optimum`` or anything computed from it.

    Checked structurally rather than by value.  Value matching would be
    both flaky and wrong here: A\\* *is* the oracle and holds the optimum
    legitimately, and a metaheuristic that happened to find the optimal
    route would hold a cost numerically equal to it while having earned
    it honestly.  What matters is whether the oracle's answer was
    *handed* to a component, and that shows up as a name or a reference,
    not as a float.
    """
    cfg = make_cfg()
    view, source, target = build(cfg.graph, stream(1, "graph"))
    arms = build_arms(ARMS, view, source, target, cfg.root_seed, 0, cfg.control)

    for arm in arms:
        if arm.name == "astar":
            continue  # the oracle itself; exactness is its whole purpose
        leaked = attribute_names(arm.optimizer) & _ORACLE_NAMES
        assert not leaked, (
            f"{arm.name} holds oracle-derived state {sorted(leaked)}; "
            "an arm that knows its distance from optimal is not solving the "
            "problem a deployed system faces"
        )


def test_no_optimizer_can_reach_the_harness_or_a_result_row():
    """I1, the structural half — no back-door to the oracle.

    A ``StepRow`` carries ``optimum`` and ``excess``; a ``GraphTimeline``
    carries every future state.  Holding either would grant exactly what
    I1 and I2 forbid, whatever the attribute happened to be called.
    """
    cfg = make_cfg()
    view, source, target = build(cfg.graph, stream(1, "graph"))
    arms = build_arms(ARMS, view, source, target, cfg.root_seed, 0, cfg.control)

    forbidden = (trial_module.StepRow, trial_module.EventRow, GraphTimeline)
    for arm in arms:
        held = [o for o in reachable(arm.optimizer) if isinstance(o, forbidden)]
        assert not held, (
            f"{arm.name} can reach {[type(o).__name__ for o in held]}, which would "
            "hand it the oracle's answer or the future schedule"
        )


# ---------------------------------------------------------------------------
# I2 — no access to future state.  This is the one that catches F1.
# ---------------------------------------------------------------------------


class _RecordingSchedule(tuple):
    """A schedule that records the index of every read made against it.

    The violation F1 represents is not visible in the *argument* passed to
    ``events_at`` — it is visible in which **schedule entry** gets read.
    ``schedule[k]`` is the transition from state *k* to state *k+1*, so
    the entries that have already been applied to produce state *t* are
    ``schedule[0 .. t-1]``.  Reading ``schedule[t]`` is reading a
    disruption that has not landed yet.
    """

    def __new__(cls, items, owner):
        obj = super().__new__(cls, items)
        obj._owner = owner
        return obj

    def __getitem__(self, index):
        self._owner.reads.append((index, self._owner.current_t))
        return tuple.__getitem__(self, index)


class ObservedTimeline(GraphTimeline):
    """A timeline that records every schedule read against the current step.

    Substituted for the real class at the point the harness builds it, so
    the code under observation is the production path unmodified.
    """

    def __post_init__(self) -> None:
        super().__post_init__()
        self.reads: list[tuple[int, int]] = []
        self.current_t = -1
        self.schedule = _RecordingSchedule(self.schedule, self)

    def state_at(self, t: int):
        # The trial loop calls state_at(t) at the top of each timestep, and
        # t only ever increases.  The internal recursion to t-1 must not
        # wind the clock back, hence the max.
        if t > self.current_t:
            self.current_t = t
        return super().state_at(t)


def run_observed(cfg: Config, monkeypatch) -> ObservedTimeline:
    """Run one real trial with the timeline observed, and return it."""
    created: list[ObservedTimeline] = []

    def factory(base, schedule):
        timeline = ObservedTimeline(base, schedule)
        created.append(timeline)
        return timeline

    monkeypatch.setattr(trial_module, "GraphTimeline", factory)
    run_trial(cfg, trial=0, arm_names=ARMS)
    assert len(created) == 1, "expected exactly one timeline per trial"
    return created[0]


def test_no_component_reads_a_future_timestep(monkeypatch):
    """I2 — nothing may read the schedule beyond what has already happened.

    At timestep *t* the applied entries are ``schedule[0 .. t-1]``, so
    every read must satisfy ``index < t``.  A read of ``schedule[t]`` is a
    component seeing a disruption before it lands.

    This is the invariant that catches **F1**: ``events_at(t)`` returned
    ``schedule[t]``, so ``RecencySignal`` fired a step early and every
    recency-driven result ran on a misaligned signal.
    """
    timeline = run_observed(make_cfg(), monkeypatch)
    assert timeline.reads, "the observer recorded nothing; it is not wired in"

    violations = [(index, t) for index, t in timeline.reads if index >= t]
    first = violations[0] if violations else None
    assert not violations, (
        f"{len(violations)} future-state read(s) out of {len(timeline.reads)}; "
        f"first at timestep t={first[1]} reading schedule[{first[0]}], which is the "
        f"transition from state {first[0]} to {first[0] + 1} and has not been applied yet. "
        "A component is reading the future."
    )


def test_events_at_returns_the_events_that_produced_the_state(monkeypatch):
    """I2, stated as the temporal contract rather than as an index bound.

    ``ARCHITECTURE.md`` §4.4: the events that produced state *t* are
    ``schedule[t-1]``.  Checked by comparing what ``events_at`` reports
    against the edges that actually changed between consecutive states,
    which is the observable consequence of the contract holding.
    """
    cfg = make_cfg()
    outcome = run_trial(cfg, trial=0, arm_names=["aco"])

    # Rebuild the same timeline the trial used, from the same seed.
    seed = outcome.steps[0].seed
    view, source, target = build(cfg.graph, stream(seed, "graph"))
    from dynaswarm.core.timeline import build_schedule

    schedule = build_schedule(
        view, cfg.scenario, stream(seed, "events"), source, target
    )
    timeline = GraphTimeline(view, schedule)

    for t in range(1, timeline.timesteps):
        before = np.asarray(timeline.state_at(t - 1).active)
        after = np.asarray(timeline.state_at(t).active)
        weight_before = np.asarray(timeline.state_at(t - 1).weight)
        weight_after = np.asarray(timeline.state_at(t).weight)
        changed = int(((before != after) | (weight_before != weight_after)).sum())
        reported = len(timeline.events_at(t))
        if changed > 0:
            assert reported > 0, (
                f"the world changed between t={t-1} and t={t} but events_at({t}) "
                "reported nothing — it is describing a different transition"
            )


def test_timestep_zero_has_no_preceding_events():
    """The boundary. There is no ``schedule[-1]``.

    Python would hand back the *last* element for index ``-1`` rather than
    raising, so an off-by-one at the boundary would silently report the
    final timestep's disruptions as having produced the initial state.
    """
    cfg = make_cfg()
    view, source, target = build(cfg.graph, stream(7, "graph"))
    from dynaswarm.core.timeline import build_schedule

    schedule = build_schedule(view, cfg.scenario, stream(7, "events"), source, target)
    assert GraphTimeline(view, schedule).events_at(0) == ()

    # "Empty" alone is a false pass when the real last entry happens to be
    # empty too, so rig one that is not: an unguarded ``schedule[t - 1]``
    # would now return these events as though they preceded state 0.
    populated = next(step for step in schedule if step)
    rigged = GraphTimeline(view, (*schedule[:-1], populated))
    assert rigged.schedule[-1], "fixture needs a non-empty final entry to be meaningful"
    assert rigged.events_at(0) == (), "index -1 wrapped round to the last entry"


def test_events_at_and_changed_edges_agree():
    """The two accessors must use one convention.

    ``changed_edges`` already read ``schedule[t-1]`` while ``events_at``
    read ``schedule[t]``.  That disagreement is what marked F1 as a slip
    rather than a deliberate convention, and it must not return.
    """
    cfg = make_cfg()
    view, source, target = build(cfg.graph, stream(3, "graph"))
    from dynaswarm.core.timeline import build_schedule

    schedule = build_schedule(view, cfg.scenario, stream(3, "events"), source, target)
    timeline = GraphTimeline(view, schedule)

    for t in range(timeline.timesteps):
        assert len(timeline.events_at(t)) == timeline.changed_edges(t), (
            f"events_at({t}) and changed_edges({t}) disagree; they index the "
            "schedule differently"
        )


# ---------------------------------------------------------------------------
# I3 — no cross-arm references
# ---------------------------------------------------------------------------


def test_no_arm_can_reach_another_arms_internals():
    """I3 — arms must be isolated, or a comparison measures contamination.

    If one arm could read another's incumbent, the better result would be
    an artefact of the coupling rather than of the search.
    """
    cfg = make_cfg()
    view, source, target = build(cfg.graph, stream(2, "graph"))
    arms = build_arms(ARMS, view, source, target, cfg.root_seed, 0, cfg.control)

    for arm in arms:
        graph_ids = {id(o) for o in reachable(arm.optimizer)}
        for other in arms:
            if other is arm:
                continue
            assert id(other.optimizer) not in graph_ids, (
                f"{arm.name} can reach {other.name}'s optimizer"
            )


def test_the_hybrids_exchange_is_the_only_sanctioned_cross_component_channel():
    """I3's exception, named rather than merely tolerated.

    The Hybrid legitimately holds an ACO and a PSO and lets them exchange
    — that is the method.  Asserting the exception by name means a
    *second* such channel, added later anywhere else, fails this test
    instead of quietly joining an allow-list.
    """
    cfg = make_cfg()
    view, source, target = build(cfg.graph, stream(2, "graph"))
    arms = build_arms(ARMS, view, source, target, cfg.root_seed, 0, cfg.control)
    by_name = {arm.name: arm.optimizer for arm in arms}

    holders = {}
    for name, optimizer in by_name.items():
        held = {
            type(o).__name__
            for o in reachable(optimizer)
            if o is not optimizer and hasattr(o, "PARAM_SPEC") and hasattr(o, "spend")
        }
        if held:
            holders[name] = held

    assert set(holders) == {"hybrid"}, (
        f"components holding other optimizers: {holders}. Exactly one such "
        "channel is sanctioned — the Hybrid's ACO<->PSO exchange"
    )
    assert holders["hybrid"] == {"ACO", "PSO"}, (
        f"the Hybrid holds {holders['hybrid']}; the sanctioned channel is "
        "exactly one colony and one swarm"
    )


def test_arms_of_a_shared_family_still_hold_separate_optimizers():
    """Sharing a random stream must not mean sharing an object.

    ``aco_fixed`` and ``aco_adaptive`` are fed identical bits precisely so
    they can diverge for exactly one reason.  If they shared an optimizer
    they would diverge for none.
    """
    cfg = make_cfg()
    view, source, target = build(cfg.graph, stream(4, "graph"))
    arms = build_arms(
        ["aco_fixed", "aco_adaptive"], view, source, target, cfg.root_seed, 0, cfg.control
    )
    assert arms[0].family == arms[1].family
    assert arms[0].optimizer is not arms[1].optimizer
