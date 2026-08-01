"""Structured configuration.

There is exactly one configuration system.  Every group below is a
dataclass registered with Hydra's :class:`ConfigStore`, which means the
dataclass *is* the schema: a key that no component reads cannot exist,
and a mistyped key fails at compose time rather than being silently
ignored at run time.

The previous codebase carried two config systems that disagreed — a
dataclass tree used by the controller and a YAML tree whose
``controller`` section described algorithm-switching behaviour that was
never implemented.  Anyone reading the YAML to understand the system was
misled.  One schema, mechanically bound to constructor arguments, makes
that failure inexpressible.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from hydra.core.config_store import ConfigStore

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------


@dataclass
class GraphCfg:
    """Topology and edge weights.

    Attributes:
        model: ``erdos_renyi`` | ``grid`` | ``geometric``.  The large
            tier should use ``grid`` or ``geometric``: on Erdos-Renyi
            graphs with random weights A* has no admissible heuristic
            beyond zero, so it degenerates to Dijkstra and stays fast no
            matter how large the graph gets — which never exercises the
            cost premise the project exists to test.
        n_nodes: Node count.
        density: Edge probability (``erdos_renyi``) or connection radius
            scaling (``geometric``).  Ignored by ``grid``.
        weight_min: Minimum edge weight.
        weight_max: Maximum edge weight.
        addable_pool_factor: Size of the candidate-edge pool that
            addition events may draw from, as a multiple of ``|E|``.
            Bounded because an unrestricted pool is O(N^2) — 10^6 slots
            at N=1000 — and the CSR topology superset must be allocated
            once up front.
    """

    model: str = "erdos_renyi"
    n_nodes: int = 30
    density: float = 0.3
    weight_min: float = 1.0
    weight_max: float = 100.0
    addable_pool_factor: float = 1.0


@dataclass
class ScenarioCfg:
    """Disruption regime.

    Attributes:
        name: Label used in results.
        churn: Expected fraction of edges disturbed per timestep.  Event
            count per step is ``Poisson(churn * |E|)``.

            Expressing churn as a *fraction* rather than a count is what
            makes the edge-ratio signal comparable across graph sizes.
            In the previous codebase exactly one edge changed per step,
            so on a 143-edge graph the edge-ratio signal could not exceed
            0.007 while the controller's thresholds sat at 0.15 and 0.40
            — it never left the lowest regime in any scenario.

            Note that no single churn value makes *all* signals span a
            wide range: volatility (fraction of steps carrying an event)
            saturates once ``churn * |E| >> 1``, while the edge ratio
            stays near ``churn``.  That asymmetry is real and is measured
            in M4 rather than assumed away.
        timesteps: Steps per trial.
        p_*: Relative probabilities of each event kind; normalised on use.
        traffic_factor: Multiplier applied by traffic events.
    """

    name: str = "moderate"
    churn: float = 0.015
    timesteps: int = 60
    p_closure: float = 0.15
    p_traffic_up: float = 0.30
    p_traffic_down: float = 0.20
    p_reopen: float = 0.10
    p_delete: float = 0.10
    p_add: float = 0.15
    traffic_factor: float = 2.0


# ---------------------------------------------------------------------------
# Experiment
# ---------------------------------------------------------------------------


@dataclass
class ExperimentCfg:
    """Trial counts, seed partition, and parallelism.

    Attributes:
        name: Label used in results.
        n_trials: Independent trials per scenario.
        tune_seeds: Seeds the tuner may see.
        eval_seeds: Seeds reported on.  **Must be disjoint from
            ``tune_seeds``** — tuning and evaluating on the same seeds
            reproduces the optimistic bias that made the previous
            project's parameter sweep untrustworthy.  A test asserts the
            disjointness.
        parallel_jobs: joblib workers over trials.  Parallelism is over
            trials only; parallelising within a trial would make arm
            ordering nondeterministic and break reproducibility.
        record_traces: Emit within-timestep traces for anytime curves.
    """

    name: str = "smoke"
    n_trials: int = 2
    tune_seeds: list[int] = field(default_factory=lambda: list(range(9000, 9016)))
    eval_seeds: list[int] = field(default_factory=lambda: list(range(1000, 1032)))
    parallel_jobs: int = 1
    record_traces: bool = False


@dataclass
class BudgetCfg:
    """Per-timestep work allowance.

    Attributes:
        evaluations: Candidate path constructions granted to every arm at
            every timestep.  Denominating the budget in *work* rather
            than iterations is what stops an arm buying itself CPU by
            enlarging its population.
    """

    evaluations: int = 300


@dataclass
class Config:
    """Top-level composition root."""

    root_seed: int = 42
    graph: GraphCfg = field(default_factory=GraphCfg)
    scenario: ScenarioCfg = field(default_factory=ScenarioCfg)
    experiment: ExperimentCfg = field(default_factory=ExperimentCfg)
    budget: BudgetCfg = field(default_factory=BudgetCfg)


def register() -> ConfigStore:
    """Register every schema and group option with Hydra.

    Returns:
        The populated :class:`ConfigStore`.
    """
    cs = ConfigStore.instance()
    cs.store(name="base_config", node=Config)

    cs.store(group="graph", name="small30", node=GraphCfg())
    cs.store(group="graph", name="medium200", node=GraphCfg(n_nodes=200, density=0.06))
    cs.store(
        group="graph",
        name="large1000",
        node=GraphCfg(model="geometric", n_nodes=1000, density=0.05),
    )
    cs.store(group="graph", name="grid20", node=GraphCfg(model="grid", n_nodes=400))

    # Churn values chosen so the four scenarios span a usable range of
    # disruption at N=30; validated empirically in M4.
    cs.store(group="scenario", name="static", node=ScenarioCfg(name="static", churn=0.0))
    cs.store(group="scenario", name="low", node=ScenarioCfg(name="low", churn=0.004))
    cs.store(group="scenario", name="moderate", node=ScenarioCfg(name="moderate", churn=0.015))
    cs.store(group="scenario", name="high", node=ScenarioCfg(name="high", churn=0.05))

    cs.store(group="experiment", name="smoke", node=ExperimentCfg(name="smoke", n_trials=2))
    cs.store(
        group="experiment",
        name="main",
        node=ExperimentCfg(name="main", n_trials=30, parallel_jobs=11),
    )

    cs.store(group="budget", name="eval300", node=BudgetCfg(evaluations=300))
    cs.store(group="budget", name="eval2000", node=BudgetCfg(evaluations=2000))
    return cs
