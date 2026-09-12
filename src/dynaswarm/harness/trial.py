"""The shared timestep loop.

One trial advances the world once per timestep and then hands *the same
frozen state* to every arm in turn.  The ordering is the whole point: the
world moves, the optimum for that state is computed, and only then does
any arm search.  No arm can observe a state another arm did not, and none
can influence what the next one sees.

Three assertions run inside the loop rather than in a test, because they
guard properties that would otherwise fail silently and produce
plausible-looking numbers:

* an arm's reported cost never falls below the true optimum — if it does,
  the cost model and the oracle disagree and every excess figure is wrong;
* the state hash is unchanged after the arm loop — no arm mutated the
  shared world;
* every arm was handed the identical state hash — nobody was quietly
  given an easier problem.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from dynaswarm.allocation.governor import FRACTION_HIGH, FRACTION_LOW
from dynaswarm.allocation.observation import observe
from dynaswarm.config import Config
from dynaswarm.control.signals import StepObservation
from dynaswarm.core.generate import build
from dynaswarm.core.meter import EvaluationMeter
from dynaswarm.core.oracle import shortest_path
from dynaswarm.core.rng import stream
from dynaswarm.core.timeline import GraphTimeline, build_schedule
from dynaswarm.harness.arm import build_arms

__all__ = ["StepRow", "TrialOutcome", "run_trial"]

#: Tolerance when comparing an arm's cost against the exact optimum.
_COST_TOL = 1e-6


@dataclass
class StepRow:
    """One arm's result at one timestep."""

    run_class: str
    scenario: str
    events_per_step: float
    graph_model: str
    n_nodes: int
    n_edges: int
    trial: int
    seed: int
    timestep: int
    arm: str
    arm_family: str
    num_events: int
    optimum: float | None
    best_cost: float | None
    excess: float | None
    path_valid: bool
    path_changed: bool
    path_len: int
    best_path: list[int]
    evaluations_spent: int
    wall_ms: float
    astar_expansions: float | None
    signal_kind: str
    controller_kind: str
    signal_value: float | None
    params: dict[str, float]
    probe: dict[str, float]


@dataclass
class EventRow:
    """One disruption, recorded so signals can be re-derived offline."""

    run_class: str
    scenario: str
    trial: int
    seed: int
    timestep: int
    kind: str
    u: int
    v: int
    old_weight: float
    new_weight: float


@dataclass
class TrialOutcome:
    """Everything one trial produced."""

    steps: list[StepRow] = field(default_factory=list)
    events: list[EventRow] = field(default_factory=list)


def run_trial(
    cfg: Config,
    trial: int,
    arm_names: list[str],
    seeds: list[int] | None = None,
    preserve_connectivity: bool = True,
) -> TrialOutcome:
    """Run every arm through one shared, pre-materialised event sequence.

    The seed drawn from *seeds* is the trial's entropy, not a label on
    it: the graph, the event sequence and every arm's stream are all
    addressed from it.  That is what gives a disjoint seed pool any
    meaning — tuning on one pool and evaluating on another must present
    genuinely different problem instances, or a configuration selected on
    the first would be reported on the very instances that chose it.

    Args:
        cfg: Full experiment configuration.
        trial: Trial index; selects which seed is used.
        arm_names: Arms to run, as keys of ``ARM_BUILDERS``.
        seeds: Pool to draw from.  Defaults to the evaluation pool; the
            tuner passes its own.
        preserve_connectivity: Reject events that would sever the route.

    Returns:
        The trial's step and event rows.
    """
    pool = seeds if seeds is not None else cfg.experiment.eval_seeds
    if not pool:
        raise ValueError("seed pool is empty")
    seed = pool[trial % len(pool)]

    view, source, target = build(cfg.graph, stream(seed, "graph"))
    schedule = build_schedule(
        view,
        cfg.scenario,
        stream(seed, "events"),
        source,
        target,
        preserve_connectivity=preserve_connectivity,
    )
    timeline = GraphTimeline(view, schedule)
    arms = build_arms(arm_names, view, source, target, seed, trial, cfg.control)

    outcome = TrialOutcome()
    previous_path: dict[str, tuple[int, ...]] = {}
    previous_cost: dict[str, float | None] = {}
    quiet_steps: dict[str, int] = {}

    for t in range(timeline.timesteps):
        state = timeline.state_at(t)
        before_hash = state.state_hash()
        # Recorded per timestep, not once: closures and additions change
        # the live edge count, and a constant column would hide that.
        n_edges = state.n_active_edges

        optimum, _, _ = shortest_path(state, source, target, heuristic=True)
        if not np.isfinite(optimum):
            optimum = None

        for event in timeline.events_at(t):
            outcome.events.append(
                EventRow(
                    run_class=cfg.run_class,
                    scenario=cfg.scenario.name,
                    trial=trial,
                    seed=seed,
                    timestep=t,
                    kind=event.kind,
                    u=event.u,
                    v=event.v,
                    old_weight=event.old_weight,
                    new_weight=event.new_weight,
                )
            )

        # Unconditional, and it must stay that way. `rebind` is how an
        # optimizer receives the current world; skipping it on quiet
        # steps would leave every arm searching a stale graph. The guard
        # that F13 needed belongs inside PSO, on the memory
        # invalidation, and it is there — see PSO.rebind.
        for arm in arms:
            arm.optimizer.rebind(state)
            assert state.state_hash() == before_hash, (
                f"{arm.name} mutated the shared world at t={t}"
            )

            meter = EvaluationMeter(cfg.budget.evaluations if arm.metered else 0)
            started = time.perf_counter()
            arm.optimizer.spend(meter)
            wall_ms = (time.perf_counter() - started) * 1000.0

            solution = arm.optimizer.best()
            probe = arm.optimizer.probe()

            cost = solution.cost if solution is not None else None
            if cost is not None and optimum is not None:
                assert cost >= optimum - _COST_TOL, (
                    f"{arm.name} reported {cost} below the optimum {optimum} at t={t}; "
                    "the cost model and the oracle disagree"
                )

            # Sense, then adapt.  Both happen after the arm has searched,
            # so a controller reacts to what this timestep revealed rather
            # than to a state that no longer holds.
            signal_value: float | None = None
            if arm.signal is not None:
                arm.signal.observe(
                    StepObservation(
                        t=t,
                        n_events=len(timeline.events_at(t)),
                        n_edges=n_edges,
                        best_cost=cost,
                        probe=probe,
                    )
                )
                signal_value = arm.signal.value()
                if arm.controller is not None:
                    arm.optimizer.apply(
                        arm.controller.propose(arm.signal, arm.optimizer.params(), t)
                    )
                if arm.governor is not None:
                    # The observation is the ONLY channel by which a
                    # policy learns anything (§7.2). Every field here is
                    # from t or earlier, and none of them is `optimum` or
                    # anything derived from it — `cost` is this arm's own
                    # incumbent, not its distance from optimal.
                    previous = previous_cost.get(arm.name)
                    observation = observe(
                        t=t,
                        events_this_step=len(timeline.events_at(t)),
                        current_fraction=arm.governor.fraction,
                        budget=cfg.budget.evaluations,
                        probe=probe,
                        own_cost=cost,
                        previous_cost=previous,
                        path_invalidated=solution is None,
                        recency=signal_value,
                        steps_since_disruption=quiet_steps.get(arm.name, 0),
                    )
                    applied = arm.governor.step(observation)
                    arm.optimizer.apply({"aco_fraction": applied})

                    # §15.6 wants proposed-vs-applied and saturation
                    # *watchable*, and a number that is never recorded
                    # cannot be drawn. Note what each one means: the
                    # `aco_fraction` already in `probe` is the split this
                    # step actually searched with; these are the decision
                    # taken at the end of it, which the next step will
                    # use. Drawing them on one axis without that
                    # distinction would put the response a step early —
                    # which is F1's shape, in the view layer.
                    wanted = arm.governor.proposed[-1]
                    probe["alloc_proposed"] = wanted
                    probe["alloc_applied"] = applied
                    probe["alloc_held_back"] = wanted - applied
                    probe["alloc_at_bound"] = float(
                        applied <= FRACTION_LOW or applied >= FRACTION_HIGH
                    )
                previous_cost[arm.name] = cost
                quiet_steps[arm.name] = (
                    0 if timeline.events_at(t) else quiet_steps.get(arm.name, 0) + 1
                )

            path = solution.path if solution is not None else ()
            outcome.steps.append(
                StepRow(
                    run_class=cfg.run_class,
                    scenario=cfg.scenario.name,
                    events_per_step=cfg.scenario.events_per_step,
                    graph_model=cfg.graph.model,
                    n_nodes=view.n_nodes,
                    n_edges=n_edges,
                    trial=trial,
                    seed=seed,
                    timestep=t,
                    arm=arm.name,
                    arm_family=arm.family,
                    num_events=len(timeline.events_at(t)),
                    optimum=optimum,
                    best_cost=cost,
                    excess=(cost / optimum - 1.0) if (cost and optimum) else None,
                    path_valid=solution is not None,
                    path_changed=path != previous_path.get(arm.name, ()),
                    path_len=max(len(path) - 1, 0),
                    best_path=list(path),
                    evaluations_spent=meter.spent,
                    wall_ms=wall_ms,
                    astar_expansions=probe.get("expansions"),
                    signal_kind=arm.signal.name if arm.signal else "",
                    controller_kind=arm.controller.name if arm.controller else "",
                    signal_value=signal_value,
                    params=dict(arm.optimizer.params()),
                    probe=dict(probe),
                )
            )
            previous_path[arm.name] = path

        assert state.state_hash() == before_hash, f"shared world mutated during t={t}"

    return outcome


def summarise(outcome: TrialOutcome) -> dict[str, Any]:
    """Compact per-arm summary, for logging a run without loading Parquet.

    Args:
        outcome: A completed trial.

    Returns:
        ``{arm: {metric: value}}``.
    """
    by_arm: dict[str, list[StepRow]] = {}
    for row in outcome.steps:
        by_arm.setdefault(row.arm, []).append(row)

    summary: dict[str, Any] = {}
    for arm, rows in by_arm.items():
        excesses = [r.excess for r in rows if r.excess is not None]
        summary[arm] = {
            "mean_excess": float(np.mean(excesses)) if excesses else float("nan"),
            "final_excess": excesses[-1] if excesses else float("nan"),
            "availability": sum(r.path_valid for r in rows) / len(rows),
            "evaluations": sum(r.evaluations_spent for r in rows),
            "wall_ms": sum(r.wall_ms for r in rows),
        }
    return summary
