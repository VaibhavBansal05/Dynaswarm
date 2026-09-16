"""The scaffold: one page, two endpoints, and nothing drawn.

What this proves is narrow and deliberate — that a browser page can ask
the real engine a question and get a true answer back.  ``optimum_at_t0``
is the field that carries the proof: it is the exact shortest-path cost
from :mod:`dynaswarm.core.oracle`, a number no plausible-looking stub
could produce, and it is what ``tests/test_dashboard.py`` compares
against a direct call into the core.

Every value below is *asked for*.  The graph comes from
:func:`dynaswarm.core.generate.build`, its endpoints from that function's
own ``_endpoints``, its optimum from the oracle, and even the tier
definition is read back out of the config store rather than restated
here — see :func:`tier`.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from hydra.core.config_store import ConfigStore
from omegaconf import OmegaConf
from pydantic import BaseModel, ConfigDict, Field

from dynaswarm.analysis.load import load_steps, per_trial_excess
from dynaswarm.config import (
    BudgetCfg,
    Config,
    ExperimentCfg,
    GraphCfg,
    ScenarioCfg,
    register,
)
from dynaswarm.core.generate import build
from dynaswarm.core.oracle import shortest_path
from dynaswarm.core.rng import stream
from dynaswarm.core.timeline import GraphTimeline, build_schedule
from dynaswarm.harness.runner import run_experiment
from dynaswarm.io.writer import write_manifest

ROOT = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).resolve().parent / "static"
OUTPUTS = ROOT / "outputs"

#: The research tier, and not a negotiable default.  ``small30`` is
#: Erdos-Renyi and carries **no coordinates**, so every visual built on it
#: is a meaningless tangle — which is exactly what the first run of this
#: project looked like.  Mechanism-level claims are made at ``medium200``
#: (D8), so that is what the dashboard opens on.
DEFAULT_TIER = "medium200"

#: Trial 0's evaluation seed, from ``ExperimentCfg.eval_seeds``.  Named
#: rather than inlined so the value the page shows is traceable to the
#: pool the experiments actually report on.
DEFAULT_SEED = 1000

#: The scenario the dashboard opens on.  Moderate rather than high: at
#: 0.8 events/step roughly 55% of timesteps carry a disruption and the
#: graph never settles, so nothing reads as an *event*.  At 0.3, 74% of
#: steps are quiet and a break is visibly a break.
DEFAULT_SCENARIO = "moderate"

#: Rendered on the page, not buried in a docstring, because segment 3
#: draws disruption markers and this is the fact that would silently make
#: them wrong.
F1_WARNING = (
    "Every run currently in outputs/ predates the F1 fix: its num_events "
    "column is off by one, so any disruption timing drawn from these runs "
    "is one step early (D32). Quality columns (excess, optimum, best_cost) "
    "are sound. Phase 4 regenerates everything."
)


def tier(name: str = DEFAULT_TIER) -> GraphCfg:
    """Return a graph tier **as ``config.py`` registers it**.

    Restating ``GraphCfg(model="geometric", n_nodes=200, density=0.04)``
    here would work today and drift silently the day someone edits the
    registration — the dashboard would keep drawing a tier that no longer
    exists under that name.  Reading it back means a divergence is
    impossible rather than merely unlikely.

    Args:
        name: A tier registered under the ``graph`` config group.

    Returns:
        The registered :class:`~dynaswarm.config.GraphCfg`.
    """
    register()
    node = ConfigStore.instance().repo["graph"][f"{name}.yaml"].node
    return OmegaConf.to_object(node)


def describe_graph(seed: int = DEFAULT_SEED, name: str = DEFAULT_TIER) -> dict:
    """Build one graph through the core and describe what came back.

    This function constructs nothing itself — no nodes, no edges, no
    weights, no coordinates, and in particular it does not choose the
    endpoints.  ``build()`` picks those via its own ``_endpoints``, and
    the cost between them is the oracle's.

    Args:
        seed: Root seed for the ``graph`` stream.
        name: Graph tier.

    Returns:
        A JSON-serialisable description.
    """
    cfg = tier(name)
    view, source, target = build(cfg, stream(seed, "graph"))
    optimum, path, expansions = shortest_path(view, source, target, heuristic=True)
    return {
        "tier": name,
        "model": cfg.model,
        "seed": seed,
        "n_nodes": view.n_nodes,
        "n_edges": view.n_active_edges,
        "source": int(source),
        "target": int(target),
        "optimum_at_t0": float(optimum),
        "hops": len(path) - 1,
        "expansions": int(expansions),
        # False for Erdos-Renyi.  The dashboard has to know this from the
        # start: it is the fact that made the original replay useless.
        "has_coordinates": view.topology.pos is not None,
    }


def describe_geometry(seed: int = DEFAULT_SEED, name: str = DEFAULT_TIER) -> dict:
    """Everything needed to draw one graph, and nothing to be worked out.

    The browser receives geometry; it never invents geometry.  Positions
    are ``topology.pos`` as the generator laid them down, the edge list is
    whichever slots the ``active`` mask says are live, and ``path`` is the
    oracle's own node sequence — the page highlights that sequence, it does
    not search for one.  Every geometric decision has already been made by
    the time this returns; all that is left is scaling pixels.

    ``edges`` and ``weights`` are **parallel arrays**: ``edges[i]`` and
    ``weights[i]`` describe the same edge, and the page trusts that
    without checking.  Nothing visible breaks on the day they
    desynchronise, which is why ``test_edges_and_weights_are_parallel``
    exists rather than a comment.

    Args:
        seed: Root seed for the ``graph`` stream.
        name: Graph tier.

    Returns:
        A JSON-serialisable description, with ``positions`` empty when the
        tier carries no coordinates.
    """
    cfg = tier(name)
    view, source, target = build(cfg, stream(seed, "graph"))
    optimum, path, _ = shortest_path(view, source, target, heuristic=True)
    topo = view.topology
    # Each CSR slot is one direction of one edge.  Taking only the slots
    # whose owner index is the smaller of the pair yields each undirected
    # edge exactly once, and the `active` mask — not this function —
    # decides which of them exist.
    owner = np.repeat(np.arange(topo.n_nodes), np.diff(topo.indptr))
    keep = np.asarray(view.active) & (owner < topo.indices)
    return {
        "tier": name,
        "seed": seed,
        "n_nodes": view.n_nodes,
        "has_coordinates": topo.pos is not None,
        "positions": [] if topo.pos is None else topo.pos.tolist(),
        "edges": np.stack([owner[keep], topo.indices[keep]], axis=1).tolist(),
        "weights": np.asarray(view.weight)[keep].tolist(),
        "path": [int(node) for node in path],
        "optimum": float(optimum),
        "source": int(source),
        "target": int(target),
    }


def _registered(group: str, name: str) -> object:
    """Read a registered config node back out of the store.

    Args:
        group: Hydra config group.
        name: Entry within it.

    Returns:
        The registered dataclass instance.
    """
    register()
    return OmegaConf.to_object(ConfigStore.instance().repo[group][f"{name}.yaml"].node)


def describe_timeline(
    seed: int = DEFAULT_SEED,
    name: str = DEFAULT_TIER,
    scenario_name: str = DEFAULT_SCENARIO,
) -> dict:
    """The whole run, in one stateless answer.

    **Built live from the core, never read from ``outputs/``.**  Every run
    on disk predates F1's fix and carries a permanently misaligned
    ``num_events`` column (D32), so drawing markers from stored files
    would reintroduce the exact off-by-one this endpoint exists to avoid
    — by trusting recorded data instead of the engine.  Stored replay
    waits for Phase 4's regenerated runs.

    ``events`` comes from :meth:`GraphTimeline.events_at`, and from
    nothing else.  The contract (`ARCHITECTURE.md` §4.4) is that
    ``schedule[k]`` is the transition *k -> k+1*, so the events that
    **produced** state ``t`` are ``schedule[t-1]``.  That arithmetic is
    written once, in the core, and re-deriving it here — or in the
    browser, or "just for the marker" — is how F1 comes back somewhere no
    test is looking.

    The server holds no cursor and no session: the page asks once and
    scrubs locally, so "which step are we on" cannot disagree between the
    page and the process.

    Args:
        seed: Root seed for the ``graph`` and ``events`` streams.
        name: Graph tier.
        scenario_name: Registered scenario, setting the disruption rate.

    Returns:
        A JSON-serialisable run: metadata plus one entry per timestep.
    """
    cfg = tier(name)
    scenario: ScenarioCfg = _registered("scenario", scenario_name)
    view, source, target = build(cfg, stream(seed, "graph"))
    schedule = build_schedule(
        view, scenario, stream(seed, "events"), source, target
    )
    timeline = GraphTimeline(view, schedule)

    steps = []
    # range(timesteps) matches harness.trial exactly, so the dashboard
    # shows the same steps the experiments run rather than one more.
    for t in range(timeline.timesteps):
        state = timeline.state_at(t)
        optimum, path, _ = shortest_path(state, source, target, heuristic=True)
        reachable = bool(np.isfinite(optimum))
        steps.append({
            "t": t,
            "events": [
                {
                    "kind": event.kind,
                    "u": int(event.u),
                    "v": int(event.v),
                    "old_weight": float(event.old_weight),
                    "new_weight": float(event.new_weight),
                }
                for event in timeline.events_at(t)
            ],
            # An unreachable target is a real outcome, not an error: the
            # page shows the break rather than a cost, and keeps playing.
            "optimum": float(optimum) if reachable else None,
            "path": [int(node) for node in path] if reachable else [],
            "reachable": reachable,
        })

    return {
        "tier": name,
        "seed": seed,
        "scenario": scenario.name,
        "events_per_step": float(scenario.events_per_step),
        "horizon": timeline.timesteps,
        "source": int(source),
        "target": int(target),
        "steps": steps,
    }


class GraphSpec(BaseModel):
    """What a world is: four parameters and nothing else.

    Deliberately not a tier name.  Stage 1 (§15.3) is "choose model, node
    count, density, seed", so the picker hands over the parameters
    themselves; the registered tiers become presets that fill this in
    rather than a closed set the user must pick from.
    """

    #: **A field this model does not know is an error, not a shrug.**
    #: Pydantic's default is to drop unknown keys silently, and this is
    #: the HTTP boundary — a browser posts JSON, so a typo or a field at
    #: the wrong nesting level runs a *different experiment* and returns a
    #: perfectly well-formed result. Found in segment X, T4: a race asked
    #: for with a top-level `seed` (which belongs under `graph`) ran the
    #: default world and reported success. Same family as F2 and F6, at
    #: the one layer where a human is typing the values.
    model_config = ConfigDict(extra="forbid")

    model: str = "geometric"
    n_nodes: int = Field(default=200, ge=4, le=2000)
    density: float = Field(default=0.04, gt=0.0, le=1.0)
    seed: int = Field(default=DEFAULT_SEED, ge=0)


class ScenarioSpec(BaseModel):
    """How the world breaks.

    Every field is a ``ScenarioCfg`` field, defaulted to ``ScenarioCfg``'s
    own default, so a request that sets nothing gets exactly what the
    engine would have used.
    """

    #: **A field this model does not know is an error, not a shrug.**
    #: Pydantic's default is to drop unknown keys silently, and this is
    #: the HTTP boundary — a browser posts JSON, so a typo or a field at
    #: the wrong nesting level runs a *different experiment* and returns a
    #: perfectly well-formed result. Found in segment X, T4: a race asked
    #: for with a top-level `seed` (which belongs under `graph`) ran the
    #: default world and reported success. Same family as F2 and F6, at
    #: the one layer where a human is typing the values.
    model_config = ConfigDict(extra="forbid")

    events_per_step: float = Field(default=0.3, ge=0.0, le=10.0)
    cluster_size: int = Field(default=25, ge=1, le=200)
    timesteps: int = Field(default=60, ge=1, le=500)
    p_closure: float = 0.15
    p_traffic_up: float = 0.30
    p_traffic_down: float = 0.20
    p_reopen: float = 0.10
    p_delete: float = 0.10
    p_add: float = 0.15
    traffic_factor: float = Field(default=2.0, gt=1.0)


def graph_id(spec: GraphSpec) -> str:
    """A graph's identity, **derived from its parameters, never issued.**

    Segment 8 ruled that this server holds no state, and an id handed out
    from a registry would quietly undo that: a registry needs entries,
    entries need eviction, eviction needs sessions, and then two viewers
    can disagree about what a given id means.  A derived id has none of
    that — any request carrying one rebuilds the identical graph from
    nothing, on any process, forever.

    ``blake2b`` rather than ``hash()`` because Python salts the latter per
    process, so the same graph would get a different id on every restart.
    It is also what ``core/rng.py`` already uses to name streams, so the
    house convention is content-addressing rather than counters.

    Args:
        spec: The four parameters that define the world.

    Returns:
        A 12-character hex digest.
    """
    payload = f"{spec.model}|{spec.n_nodes}|{spec.density!r}|{spec.seed}"
    return hashlib.blake2b(payload.encode(), digest_size=6).hexdigest()


def _graph_cfg(spec: GraphSpec) -> GraphCfg:
    return GraphCfg(model=spec.model, n_nodes=spec.n_nodes, density=spec.density)


def build_world(spec: GraphSpec) -> dict:
    """Generate a graph to order, and describe it.

    No cache, deliberately.  The spec permits one only if evicting it
    cannot change an answer, and the cheapest way to guarantee that is to
    have nothing to evict — every response is rebuilt from the parameters
    in the request.  See the segment's FINDINGS for the timing that made
    this affordable.

    Args:
        spec: Model, node count, density and seed.

    Returns:
        The derived id, the panel statistics, and the geometry needed to
        draw it — ``positions`` empty when the model carries none.
    """
    cfg = _graph_cfg(spec)
    view, source, target = build(cfg, stream(spec.seed, "graph"))
    optimum, path, _ = shortest_path(view, source, target, heuristic=True)
    topo = view.topology
    owner = np.repeat(np.arange(topo.n_nodes), np.diff(topo.indptr))
    keep = np.asarray(view.active) & (owner < topo.indices)
    reachable = bool(np.isfinite(optimum))
    return {
        "graph_id": graph_id(spec),
        "spec": spec.model_dump(),
        "n_nodes": view.n_nodes,
        "n_edges": view.n_active_edges,
        "mean_degree": 2.0 * view.n_active_edges / view.n_nodes,
        "optimum": float(optimum) if reachable else None,
        "reachable": reachable,
        "source": int(source),
        "target": int(target),
        "has_coordinates": topo.pos is not None,
        "positions": [] if topo.pos is None else topo.pos.tolist(),
        "edges": np.stack([owner[keep], topo.indices[keep]], axis=1).tolist(),
        "weights": np.asarray(view.weight)[keep].tolist(),
    }


def build_run(graph: GraphSpec, scenario: ScenarioSpec) -> dict:
    """A world plus a disruption timeline, in one stateless answer.

    The same contract as :func:`describe_timeline` — ``events_at()`` is
    the only source of event timing — with one addition that earns its
    place: every step carries the engine's **own** ``n_active_edges``.

    That is what makes §4.3.1's identity checkable rather than decorative.
    The page tallies adds, reopens, closures and deletes from the events
    it was given and asserts

        active(t) == active(0) + adds + reopens - closures - deletes

    against *this* number.  Reconciling a browser tally against a browser
    tally would prove only that the browser is self-consistent, which it
    would be even if the engine disagreed with both.

    Args:
        graph: The world.
        scenario: How it breaks.

    Returns:
        Metadata, the derived graph id, and one entry per timestep.
    """
    cfg = _graph_cfg(graph)
    view, source, target = build(cfg, stream(graph.seed, "graph"))
    scenario_cfg = ScenarioCfg(name="custom", **scenario.model_dump())
    schedule = build_schedule(
        view, scenario_cfg, stream(graph.seed, "events"), source, target
    )
    timeline = GraphTimeline(view, schedule)

    steps = []
    for t in range(timeline.timesteps):
        state = timeline.state_at(t)
        optimum, path, _ = shortest_path(state, source, target, heuristic=True)
        reachable = bool(np.isfinite(optimum))
        steps.append({
            "t": t,
            "events": [
                {
                    "kind": event.kind,
                    "u": int(event.u),
                    "v": int(event.v),
                    "old_weight": float(event.old_weight),
                    "new_weight": float(event.new_weight),
                }
                for event in timeline.events_at(t)
            ],
            "optimum": float(optimum) if reachable else None,
            "path": [int(node) for node in path] if reachable else [],
            "reachable": reachable,
            # The engine's own count, not a tally. This is the figure the
            # ledger reconciles against.
            "n_active_edges": state.n_active_edges,
        })

    return {
        "graph_id": graph_id(graph),
        "graph": graph.model_dump(),
        "scenario": scenario.model_dump(),
        "horizon": timeline.timesteps,
        "source": int(source),
        "target": int(target),
        "steps": steps,
    }


#: Display names (ARCHITECTURE.md §9). Code ids are frozen data — they key
#: ARM_BUILDERS, land in the `arm` column of every parquet and are asserted
#: in tests (D23a) — so the map is display-only and travels one way.
ARM_DISPLAY = {
    "astar": "A*",
    "aco": "ACO standalone",
    "pso": "PSO standalone",
    "hybrid": "Hybrid (baseline)",
    # §9's table, verbatim. The "New" in the adaptive arm's name is part
    # of the display string there and is not trimmed here, because the
    # map is supposed to have one spelling and this file is not the place
    # to decide it reads better without.
    "hybrid_fixed": "Fixed / Static Hybrid",
    "hybrid_adaptive": "New Recency-Based Adaptive Hybrid",
    # NOT in §9's table — `hybrid_scheduled` was added in segment 21 as
    # §7.2's open-loop control and the table predates it. Named here so
    # the dashboard does not fall back to the raw code id, and reported
    # to the Architect, who owns that table. Do not treat this line as
    # the canonical name; it is a placeholder awaiting a §9 row.
    "hybrid_scheduled": "Scheduled Hybrid (open-loop control)",
}

#: Every arm the dashboard may race.
#:
#: This list was held to the uncontrolled four for the whole of Phase 1
#: and 2, because F7 built the prescheduled controller with no arguments
#: — `start == end == 1.0` — so it varied nothing while logging itself
#: active, and racing it would have put a controller known not to control
#: on screen looking exactly like a result.
#:
#: **Segment 20 removed that controller and segment 21 replaced it with
#: the allocation layer, so the guard is lifted and the three controlled
#: hybrids are raceable.** The condition for lifting it was never "F7 is
#: closed" on its own: it is that each arm is now shown to do what its
#: name says, arm by arm, against a printed series
#: (`scripts/verify_arms.py`). An arm that cannot be demonstrated that
#: way does not belong on this list however fixed its defects are.
RACEABLE = tuple(ARM_DISPLAY)


class RaceSpec(BaseModel):
    """One trial of some arms on one world, at one budget."""

    #: **A field this model does not know is an error, not a shrug.**
    #: Pydantic's default is to drop unknown keys silently, and this is
    #: the HTTP boundary — a browser posts JSON, so a typo or a field at
    #: the wrong nesting level runs a *different experiment* and returns a
    #: perfectly well-formed result. Found in segment X, T4: a race asked
    #: for with a top-level `seed` (which belongs under `graph`) ran the
    #: default world and reported success. Same family as F2 and F6, at
    #: the one layer where a human is typing the values.
    model_config = ConfigDict(extra="forbid")

    graph: GraphSpec = Field(default_factory=GraphSpec)
    scenario: ScenarioSpec = Field(default_factory=ScenarioSpec)
    arms: list[str] = Field(default_factory=lambda: list(RACEABLE))
    evaluations: int = Field(default=300, ge=10, le=20000)


def race_config(spec: RaceSpec) -> Config:
    """Assemble the configuration a race runs under.

    Every field is a real ``Config`` field. **No dashboard-only parameter
    enters a run** (§15.2) — if it is not something the CLI could also
    set, it is not here.

    The run root is a parameter so the test suite can write into a
    temporary directory instead of ``outputs/``. That is containment, not
    convenience: ``run_class`` exists so a scratch run can never silently
    become evidence, and a harness able to write into the live tree is a
    hole straight through that guarantee — one corruption demo put a
    ``manifest``-stamped run there and the provenance guard went red.
    Detection worked; containment did not exist.

    ``run_class`` is ``exploratory`` and not a parameter: a dashboard run
    is a scratch run by construction (D30/D31), and offering a control
    that could stamp one `manifest` would hand a user the one mistake the
    provenance system exists to prevent.
    """
    unknown = [arm for arm in spec.arms if arm not in RACEABLE]
    if unknown:
        raise ValueError(f"arm(s) {unknown} are not raceable; permitted: {list(RACEABLE)}")
    return Config(
        run_class="exploratory",
        graph=_graph_cfg(spec.graph),
        scenario=ScenarioCfg(name="custom", **spec.scenario.model_dump()),
        # `eval_seeds`, not `root_seed`: `trial.py:135` builds the graph from
        # the per-trial evaluation seed, so that is the only field the
        # dashboard's seed box can reach. Setting `root_seed` here would
        # look right, change the manifest, and change nothing that runs.
        #
        # Found in segment X, T4 exercise 3: the seed control did not
        # affect the race at all. Two different seeds produced byte-
        # identical excess for all four arms, because every race used this
        # default regardless of what was typed. The reference card promises
        # "One seed, one run. The seed fixes the world and its sequence of
        # breaks" — it now does.
        experiment=ExperimentCfg(
            arms=list(spec.arms), n_trials=1, parallel_jobs=1,
            eval_seeds=[spec.graph.seed],
        ),
        budget=BudgetCfg(evaluations=spec.evaluations),
    )


def race(spec: RaceSpec, root: Path | None = None) -> dict:
    """Execute one real trial and write a normal run directory.

    **The dashboard configures and calls; it never steps a loop.**
    ``run_experiment`` is the CLI's own door (`cli.py:58`) — it calls
    ``run_trial`` per trial and streams rows through ``ResultWriter``, so
    what lands on disk is shaped by the same code that shapes a CLI run,
    not by anything here.

    Returns:
        The run id — which, unlike a graph id, **names a directory**. A
        graph is a pure function of its parameters and can be rebuilt from
        them; a run is an artefact with a location, and survives a restart
        because it is a file rather than a memory.
    """
    cfg = race_config(spec)
    stamp = datetime.now()
    root = OUTPUTS if root is None else Path(root)
    directory = root / stamp.strftime("%Y-%m-%d") / stamp.strftime("%H-%M-%S")
    run_id = directory.name
    directory.mkdir(parents=True, exist_ok=True)

    write_manifest(directory, run_id, asdict(cfg))
    summary = run_experiment(cfg, list(cfg.experiment.arms), directory, run_id)

    return {
        "run_id": run_id,
        "path": str(directory),
        "run_class": cfg.run_class,
        "arms": [{"id": a, "name": ARM_DISPLAY[a]} for a in cfg.experiment.arms],
        "evaluations": cfg.budget.evaluations,
        "summary": {arm: {k: float(v) for k, v in m.items()} for arm, m in summary.items()},
    }



#: The probe keys the allocation view needs, named here so a rename in
#: `trial.py` breaks the import rather than silently emptying the chart
#: — Entry 021 R1's rule, one layer out.
_ALLOC_KEYS = ("alloc_proposed", "alloc_applied", "alloc_held_back", "alloc_at_bound")


def _allocation_series(rows):
    """Per-step allocation telemetry, or ``None`` if this arm has none.

    Reads the probe map the harness recorded. Returning ``None`` rather
    than an empty list matters: the pane distinguishes "this arm has no
    allocation policy" from "this arm has one that did nothing", and
    those are different claims about the same flat line.
    """
    probes = [dict(p) if p is not None else {} for p in rows["probe"]]
    if not any("alloc_applied" in p for p in probes):
        return None
    series = {k.removeprefix("alloc_"): [] for k in _ALLOC_KEYS}
    for probe in probes:
        for key in _ALLOC_KEYS:
            value = probe.get(key)
            series[key.removeprefix("alloc_")].append(
                None if value is None else float(value)
            )
    # `searched` is the split the step actually ran with, which is the
    # PREVIOUS step's applied value. Carried explicitly so the pane never
    # has to shift an index by hand — F1 was an off-by-one nobody could
    # see, and a chart is where one would hide best.
    series["searched"] = [
        None if (v := p.get("aco_fraction")) is None else float(v) for p in probes
    ]
    return series

def read_run(run_id: str, root: Path | None = None) -> dict:
    """Read a finished run back off disk.

    ``run_class=None`` deliberately: a dashboard run is ``exploratory``
    by construction, so the manifest-only default — which exists to stop
    scratch runs being aggregated into evidence (D30) — would return an
    empty frame for every run this page has ever made. One named run is
    not an aggregation.

    Excess comes from ``analysis.per_trial_excess``, the same function
    the CLI's report uses. Recomputing it here would be a second answer
    to a question the analysis layer already answers.

    Args:
        run_id: Directory name, as returned by :func:`race`.

    Returns:
        Per-arm paths per timestep for the panes, and the excess series
        for the chart.

    Raises:
        FileNotFoundError: If no such run directory exists.
    """
    root = OUTPUTS if root is None else Path(root)
    matches = sorted(root.glob(f"*/{run_id}"))
    if not matches:
        raise FileNotFoundError(f"no run directory named {run_id!r} under {root}")
    directory = matches[-1]

    frame = load_steps(directory, run_class=None)
    trials = per_trial_excess(frame)

    arms = []
    for arm in frame["arm"].unique():
        rows = frame[frame["arm"] == arm].sort_values("timestep")
        summary = trials[trials["arm"] == arm]
        arms.append({
            "id": str(arm),
            "name": ARM_DISPLAY.get(str(arm), str(arm)),
            "paths": [[int(n) for n in p] for p in rows["best_path"]],
            "excess": [None if pd.isna(x) else float(x) for x in rows["excess"]],
            "valid": [bool(v) for v in rows["path_valid"]],
            "evaluations": [int(e) for e in rows["evaluations_spent"]],
            # cost and hops are recorded columns, not derived from the
            # path above: a pane must not compute a figure it could
            # instead be told, and `path_len` is what the harness counted.
            "cost": [None if pd.isna(c) else float(c) for c in rows["best_cost"]],
            "hops": [int(h) for h in rows["path_len"]],
            # From the analysis layer, not from the series above.
            "mean_excess": float(summary["mean_excess"].iloc[0]) if len(summary) else None,
            # §15.6's allocation bar. `None` — not a zero-filled series —
            # for an arm with no governor: a flat line at 0.5 drawn for
            # A* would read as "it considered moving and chose not to".
            "allocation": _allocation_series(rows),
        })

    # Derived from the graph config the RUN recorded, not from whatever
    # the form currently holds. If someone edits the world after racing,
    # this id keeps naming the graph the arms actually ran on — which is
    # what makes the shared-timeline line evidence rather than a caption.
    manifest = json.loads((directory / "manifest.json").read_text())
    graph = manifest["config"]["graph"]
    return {
        "run_id": run_id,
        "path": str(directory),
        "run_class": str(frame["run_class"].iloc[0]),
        "horizon": int(frame["timestep"].max()) + 1,
        # Built from the seed the graph was ACTUALLY built from — the
        # recorded eval seed — not from `root_seed`. They are different
        # numbers (42 against 1000 at the defaults), so this caption used
        # to name a world that was never raced while sitting beside a
        # correct `seed` field. A provenance line that is confidently
        # wrong is worse than none.
        "graph_id": graph_id(GraphSpec(
            model=graph["model"], n_nodes=graph["n_nodes"],
            density=graph["density"], seed=int(frame["seed"].iloc[0]),
        )),
        "seed": int(frame["seed"].iloc[0]),
        "arms": arms,
    }


def run_classes() -> dict[str, int]:
    """Row counts per ``run_class`` across every run in ``outputs/``.

    Read with ``run_class=None`` deliberately.  The manifest-only default
    exists to protect aggregation across runs (D30), but **every run this
    dashboard creates is ``exploratory`` by design** — so a filtered read
    would show a blank screen for every run it ever made, and today it
    would show a blank screen for every run that exists at all, since D31
    left no ``manifest`` runs anywhere.

    Returns:
        ``{run_class: n_rows}``, empty if nothing has been run yet.
    """
    try:
        frame = load_steps(OUTPUTS, run_class=None)
    except FileNotFoundError:
        return {}
    return {str(k): int(v) for k, v in frame["run_class"].value_counts().items()}


app = FastAPI(
    title="Dynaswarm dashboard",
    description="A view onto the engine. It asks; it does not compute.",
)


@app.get("/api/graph")
def api_graph(seed: int = DEFAULT_SEED, tier_name: str = DEFAULT_TIER) -> dict:
    """The pipe, end to end: browser to engine and back."""
    return describe_graph(seed, tier_name)


@app.get("/api/graph/geometry")
def api_geometry(seed: int = DEFAULT_SEED, tier_name: str = DEFAULT_TIER) -> dict:
    """Coordinates, edges and the optimal path — enough to draw, exactly."""
    return describe_geometry(seed, tier_name)


@app.get("/api/timeline")
def api_timeline(
    seed: int = DEFAULT_SEED,
    tier_name: str = DEFAULT_TIER,
    scenario_name: str = DEFAULT_SCENARIO,
) -> dict:
    """One call, the whole run. No cursor lives on this server."""
    return describe_timeline(seed, tier_name, scenario_name)


@app.post("/api/graph")
def api_build_graph(spec: GraphSpec) -> dict:
    """Stage 1: generate a world to order. Its id is derived, not issued."""
    return build_world(spec)


@app.post("/api/timeline")
def api_build_timeline(graph: GraphSpec, scenario: ScenarioSpec) -> dict:
    """Stage 2: break that world on demand."""
    return build_run(graph, scenario)


@app.post("/api/run")
def api_race(spec: RaceSpec) -> dict:
    """Stage 3: run one real trial. The id names a directory on disk."""
    return race(spec)


@app.get("/api/run/{run_id}")
def api_read_run(run_id: str) -> dict:
    """Read a finished run back. Survives a restart; it is a file."""
    return read_run(run_id)


#: Categorical colours, one per arm. Hue is spent ONLY here (Entry 009 R1).
#:
#: **Moved out of `model.js` in segment 21.** Two reasons, and the second
#: is the one that forced it. First, the display names had already moved
#: here to stop two copies of one list drifting, and leaving the colours
#: behind kept half the problem. Second, `model.js` keyed this map by arm
#: id, and `hybrid_scheduled` contains the literal "schedule" — which the
#: repo-wide guard forbidding the dashboard from indexing the event
#: schedule greps for, correctly and bluntly, across all JavaScript. The
#: arm id is frozen data (D23a) and that guard protects F1. Neither could
#: give way, so the map moved to the language with an AST.
#:
#: The luminances are spread so the arms survive greyscale, and the gap
#: is asserted in `test_dashboard.py`, not merely intended here.
ARM_COLORS = {
    "astar": "#eceef1",            # 0.932
    "hybrid_scheduled": "#d7e39a",  # 0.843  open-loop control
    "aco": "#8fc0ff",              # 0.724
    "hybrid_adaptive": "#b98cff",  # 0.653  the thesis
    "pso": "#c9762b",              # 0.527
    "hybrid_fixed": "#c04a6e",     # 0.445  the ablation twin
    "hybrid": "#22683d",           # 0.307
}

#: The closest luminance pair the palette achieves. Four arms left ~0.2
#: between neighbours; seven leaves this. Asserted, not aspirational.
MIN_ARM_LUMINANCE_GAP = 0.07


def arm_luminance(hex_colour: str) -> float:
    """Perceived luminance, the standard weighting."""
    n = int(hex_colour.lstrip("#"), 16)
    return (0.299 * ((n >> 16) & 255) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255


#: Raced by default when the page opens: the four that answer Claim 1.
#: The controlled hybrids are offered but unticked — racing seven arms by
#: default triples the wait for a first result, and the three extra ones
#: answer a different claim than the page's opening question.
DEFAULT_ARMS = ("astar", "aco", "pso", "hybrid")


@app.get("/api/arms")
def api_arms() -> dict:
    """The arm list and its display names, served rather than duplicated.

    The page used to carry its own copy of §9's map. Two spellings of one
    name is the shape of the defect that cost segment 20 (a probe key
    renamed on one side only), so there is now one copy and the client
    asks for it.
    """
    return {
        "arms": [
            {
                "id": a,
                "name": ARM_DISPLAY[a],
                "colour": ARM_COLORS[a],
                "default": a in DEFAULT_ARMS,
            }
            for a in RACEABLE
        ]
    }


@app.get("/api/runs")
def api_runs() -> dict:
    """What is on disk, and the caveat that governs reading it."""
    return {"run_classes": run_classes(), "warning": F1_WARNING}


@app.get("/")
def index() -> FileResponse:
    """The page itself."""
    return FileResponse(STATIC / "index.html")


@app.middleware("http")
async def _never_cache(request, call_next):
    """Serve everything uncached.

    A development tool whose stylesheet is edited between refreshes must
    not be able to show a stale one — the browser revalidates against an
    ETag, a plain reload reuses the cached copy, and the page silently
    disagrees with the file on disk. That cost Rudra two rounds of
    "it still looks wrong" against a server that was serving the right
    bytes the whole time.

    Correct for a loopback dev server and nowhere else; this is not
    deployed (synopsis O1).
    """
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, must-revalidate"
    return response


app.mount("/static", StaticFiles(directory=STATIC), name="static")


def main() -> None:
    """Start the **local development** server.

    Bound to the loopback address on purpose: this is a tool for the
    machine it runs on, not a deployment.  Web deployment is out of scope
    (synopsis O1), and binding to localhost is what keeps that true by
    construction rather than by intention.
    """
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
