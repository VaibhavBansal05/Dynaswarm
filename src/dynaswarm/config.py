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

#: The only permitted values of :attr:`Config.run_class`.
#:
#: ``manifest`` rows are the only ones any reported figure may be built
#: from.  ``exploratory`` covers smoke runs, dashboard sessions and
#: sanity checks; ``inversion`` covers deliberately-broken code paths.
#: Neither of the latter two is ever reportable, and they are never mixed.
RUN_CLASSES = ("manifest", "exploratory", "inversion")

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
        events_per_step: Expected disruptions per timestep, drawn as
            ``Poisson(events_per_step)``.

            An **absolute** rate, not a fraction of ``|E|``.  Scaling
            disruption with graph size sounds neutral and is not: a city
            suffers roughly as many incidents per hour however finely one
            chooses to model its roads.  Tying the rate to edge count
            meant that at 1200 edges even a modest fraction produced
            around eighteen events per step, so the graph never settled
            and there was no quiet period to recover *to* — measured, one
            hundred percent of timesteps carried a disruption, which
            makes recovery unobservable.

            Keeping the rate absolute preserves quiet stretches at every
            graph size.  It does mean the edge-ratio signal reads smaller
            on larger graphs, since it divides by ``|E|`` — but that is a
            true property of that signal rather than something to
            engineer away.
        cluster_size: Edges affected per disruption.  Real disruptions
            are spatially coherent — congestion fills a district, an
            incident closes a junction and its approaches — and modelling
            each as a single uniformly drawn edge makes disruption almost
            always irrelevant to any given route.  Measured on a 30-node
            graph, single-edge events left the optimum untouched in four
            trials out of six.  Clustering keeps events rare enough to
            leave quiet stretches while making each one consequential.

            Calibrated by measurement: at 25 edges per disruption the
            optimum moves in every trial at both graph tiers (four to
            eight distinct optima per run) while roughly three quarters
            of timesteps stay quiet at the moderate rate.  Smaller
            clusters left the optimum untouched in a third of trials;
            larger ones bought little beyond the noise.
        timesteps: Steps per trial.
        p_*: Relative probabilities of each event kind; normalised on use.
        traffic_factor: Multiplier applied by traffic events.
    """

    name: str = "moderate"
    events_per_step: float = 0.3
    cluster_size: int = 25
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
        fixed_params: Starting parameter values applied to every ACO arm.
            This is how a tuned baseline is supplied: the tuner writes a
            vector, and both halves of an ablation start from it, so the
            comparison is adaptive-versus-tuned rather than
            adaptive-versus-arbitrary.
    """

    signal: str | None = None
    window: int = 10
    targets: list[str] = field(default_factory=lambda: ["rho"])
    sigma: float = 0.001
    deadband: float = 0.0
    baseline_alpha: float = 0.05
    adapt_every: int = 1
    fixed_params: dict[str, float] = field(default_factory=dict)

    #: Allocation (§7.2). Separate from the parameter-adaptation settings
    #: above because they serve different claims: those are Claim 2's
    #: evidence set, these are Claim 3.
    sigma_max: float = 0.05
    initial_fraction: float = 0.5


@dataclass
class TuningCfg:
    """Search for a fixed parameter vector.

    Attributes:
        enabled: Run the search instead of an experiment.
        candidates: Parameter vectors to try.
        trials: Instances each candidate is averaged over.
        arm: Which arm to tune.  Its own ``PARAM_SPEC`` is searched, so
            tuning a hybrid covers both components and the budget split.
        params_file: A vector produced by an earlier search, applied as
            the starting point for every arm.  Supplying one is what
            turns the comparison into adaptive-versus-tuned; without it
            the fixed arm is merely the default, which is a far easier
            opponent than the literature actually poses.
    """

    enabled: bool = False
    arm: str = "aco"
    candidates: int = 60
    trials: int = 6
    params_file: str | None = None


@dataclass
class Config:
    """Top-level composition root.

    Attributes:
        report: Emit figures and comparison tables after the run.  Off by
            default so a sweep is not slowed by rendering it will discard.
        run_class: What kind of run this is, one of :data:`RUN_CLASSES`.

            Defaults to ``exploratory`` because the safe default is the
            one that is never reportable: a scratch run that forgets to
            declare itself cannot then be mistaken for evidence.  A
            reportable run has to say so explicitly.  Recorded in
            ``manifest.json`` and as a column on every result row, so the
            distinction survives rows from several runs being
            concatenated — which is the case the filtering exists for.
    """

    root_seed: int = 42
    report: bool = False
    run_class: str = "exploratory"
    graph: GraphCfg = field(default_factory=GraphCfg)
    scenario: ScenarioCfg = field(default_factory=ScenarioCfg)
    experiment: ExperimentCfg = field(default_factory=ExperimentCfg)
    budget: BudgetCfg = field(default_factory=BudgetCfg)
    control: ControlCfg = field(default_factory=ControlCfg)
    tuning: TuningCfg = field(default_factory=TuningCfg)

    def __post_init__(self) -> None:
        """Reject an unrecognised run class before any work begins.

        Runs when the composed config is turned into a :class:`Config`,
        which happens in the CLI before a single trial executes.  A typo
        that silently became a class nobody filters on would put scratch
        rows into a reported figure.
        """
        if self.run_class not in RUN_CLASSES:
            raise ValueError(f"unknown run_class {self.run_class!r}; permitted: {RUN_CLASSES}")


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

    # Rates chosen so quiet stretches survive: the fraction of undisturbed
    # timesteps is exp(-rate), giving 90%, 74% and 45% for the three
    # dynamic tiers.  A disruption therefore has somewhere to decay to,
    # which is the precondition for measuring recovery at all.  Being
    # absolute, these hold at any graph size.
    cs.store(group="scenario", name="static", node=ScenarioCfg(name="static", events_per_step=0.0))
    cs.store(group="scenario", name="low", node=ScenarioCfg(name="low", events_per_step=0.1))
    cs.store(
        group="scenario", name="moderate", node=ScenarioCfg(name="moderate", events_per_step=0.3)
    )
    cs.store(group="scenario", name="high", node=ScenarioCfg(name="high", events_per_step=0.8))

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
