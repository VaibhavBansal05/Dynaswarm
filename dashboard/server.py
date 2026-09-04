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
from pathlib import Path

import numpy as np
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from hydra.core.config_store import ConfigStore
from omegaconf import OmegaConf
from pydantic import BaseModel, Field

from dynaswarm.analysis.load import load_steps
from dynaswarm.config import GraphCfg, ScenarioCfg, register
from dynaswarm.core.generate import build
from dynaswarm.core.oracle import shortest_path
from dynaswarm.core.rng import stream
from dynaswarm.core.timeline import GraphTimeline, build_schedule

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


@app.get("/api/runs")
def api_runs() -> dict:
    """What is on disk, and the caveat that governs reading it."""
    return {"run_classes": run_classes(), "warning": F1_WARNING}


@app.get("/")
def index() -> FileResponse:
    """The page itself."""
    return FileResponse(STATIC / "index.html")


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
