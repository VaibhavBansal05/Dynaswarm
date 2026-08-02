"""Structured configuration.

There is exactly one configuration system.  Every group below is a
dataclass registered with Hydra's :class:`ConfigStore`, which means the
dataclass *is* the schema: a key that no component reads cannot exist,
and a mistyped key fails at compose time rather than being silently
ignored at run time.

Two parallel config systems — say a dataclass tree the code reads and a
YAML tree humans read — will drift, and the YAML will end up describing
behaviour nobody implemented.  Anyone consulting it to understand the
system is then actively misled, and nothing fails.  One schema,
mechanically bound to constructor arguments, makes that inexpressible.
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

            Expressing churn as a *fraction* rather than an absolute
            count is what makes the edge-ratio signal comparable across
            graph sizes.  A fixed count of ``k`` events per step would
            make that signal ``k/|E|``, which on a 150-edge graph reads
            as 0.007 for a single event and shrinks as the graph grows —
            far below any threshold one would naturally choose, and not
            transferable between sizes.

            Note that no single churn value makes *all* signals span a
            wide range: volatility (fraction of steps carrying an event)
            saturates once ``churn * |E| >> 1``, while the edge ratio
            stays near ``churn``.  That asymmetry is real and is
            measured rather than assumed away.
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
        arms: Which competitors to run.  Nested under the experiment
            rather than at the top level because Hydra reads a bare
            top-level list key as a config-group override; a dotted key
            is unambiguously a value.  It also belongs here: which arms
            are compared is part of what defines the experiment.
        n_trials: Independent trials per scenario.
        tune_seeds: Seeds the tuner may see.
        eval_seeds: Seeds reported on.  **Must be disjoint from
            ``tune_seeds``** — selecting a configuration on the same
            seeds it is then reported on turns the headline figure into a
            maximum over noise.  A test asserts the disjointness.
        parallel_jobs: joblib workers over trials.  Parallelism is over
            trials only; parallelising within a trial would make arm
            ordering nondeterministic and break reproducibility.
        record_traces: Emit within-timestep traces for anytime curves.
    """

    name: str = "smoke"
    arms: list[str] = field(default_factory=lambda: ["astar", "aco"])
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
class ControlCfg:
    """Sensing and adaptation settings.

    Attributes:
        signal: Overrides each arm's default signal, so one sweep can run
            the same ablation across ``edge_ratio``, ``volatility`` and
            ``lambda_branch``.  ``None`` keeps each arm's own choice.
        window: Rolling-window length for the signal.
        targets: Parameters the incremental controller adapts.  One at a
            time by default: moving several together makes it impossible
            to attribute an effect to any of them.
        sigma: Step size per adaptation cycle.  Small by design — a large
            step discards accumulated search state on the strength of one
            noisy reading.
        deadband: Pressure magnitude below which nothing moves.
        baseline_alpha: Weight of the newest reading in the running
            baseline the signal is compared against.
        adapt_every: Timesteps between adaptation cycles.
    """

    signal: str | None = None
    window: int = 10
    targets: list[str] = field(default_factory=lambda: ["rho"])
    sigma: float = 0.001
    deadband: float = 0.0
    baseline_alpha: float = 0.05
    adapt_every: int = 1


@dataclass
class Config:
    """Top-level composition root."""

    root_seed: int = 42
    graph: GraphCfg = field(default_factory=GraphCfg)
    scenario: ScenarioCfg = field(default_factory=ScenarioCfg)
    experiment: ExperimentCfg = field(default_factory=ExperimentCfg)
    budget: BudgetCfg = field(default_factory=BudgetCfg)
    control: ControlCfg = field(default_factory=ControlCfg)


def register() -> ConfigStore:
    """Register every schema and group option with Hydra.

    Returns:
        The populated :class:`ConfigStore`.
    """
    cs = ConfigStore.instance()
    cs.store(name="base_config", node=Config)

    # Only the smallest tier is Erdos-Renyi.  Without coordinates there is
    # no distance-to-target term for either A*'s heuristic or the colony's
    # visibility, so both degrade to undirected search.  Measured at n=200
    # with a 300-evaluation budget, ACO settles ~90% above optimum on
    # Erdos-Renyi versus ~15% on a geometric graph of the same size.  The
    # small tier survives that only because a 30-node graph of degree ~18
    # puts the target within a hop or two of anywhere.
    cs.store(group="graph", name="small30", node=GraphCfg())
    cs.store(
        group="graph",
        name="medium200",
        node=GraphCfg(model="geometric", n_nodes=200, density=0.04),
    )
    cs.store(
        group="graph",
        name="large1000",
        node=GraphCfg(model="geometric", n_nodes=1000, density=0.01),
    )
    cs.store(group="graph", name="grid20", node=GraphCfg(model="grid", n_nodes=400))

    # Churn calibrated against measured volatility at N=30 (|E| ~= 147).
    # Expected events per step is churn * |E|, so the fraction of steps
    # carrying an event is 1 - exp(-churn * |E|), which saturates fast:
    # measured 0.95 at churn=0.015 and 1.00 at 0.05.  Beyond ~0.02 the
    # volatility signal cannot tell scenarios apart even though the edge
    # ratio keeps climbing, so the tiers stay in the range where *both*
    # signals still discriminate.
    cs.store(group="scenario", name="static", node=ScenarioCfg(name="static", churn=0.0))
    cs.store(group="scenario", name="low", node=ScenarioCfg(name="low", churn=0.002))
    cs.store(group="scenario", name="moderate", node=ScenarioCfg(name="moderate", churn=0.006))
    cs.store(group="scenario", name="high", node=ScenarioCfg(name="high", churn=0.015))

    cs.store(group="experiment", name="smoke", node=ExperimentCfg(name="smoke", n_trials=2))
    cs.store(
        group="experiment",
        name="main",
        node=ExperimentCfg(name="main", n_trials=30, parallel_jobs=11),
    )

    for kind in ("edge_ratio", "volatility", "lambda_branch"):
        cs.store(group="control", name=kind, node=ControlCfg(signal=kind))
    cs.store(group="control", name="default", node=ControlCfg())

    cs.store(group="budget", name="eval300", node=BudgetCfg(evaluations=300))
    cs.store(group="budget", name="eval2000", node=BudgetCfg(evaluations=2000))
    return cs
