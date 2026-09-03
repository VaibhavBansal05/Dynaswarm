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

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from hydra.core.config_store import ConfigStore
from omegaconf import OmegaConf

from dynaswarm.analysis.load import load_steps
from dynaswarm.config import GraphCfg, register
from dynaswarm.core.generate import build
from dynaswarm.core.oracle import shortest_path
from dynaswarm.core.rng import stream

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
