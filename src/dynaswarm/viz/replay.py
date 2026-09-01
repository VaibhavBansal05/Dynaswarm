"""Replaying a recorded run.

The viewer reads finished results and re-renders them.  It never drives a
simulation, holds no optimizer, and imports nothing from the harness, so
it cannot perturb a result or alter the determinism of one — a viewer
that stepped the search itself would be able to do both.

The cost is that only what was recorded can be shown: paths are stored
per timestep, so the replay is faithful to the run rather than a fresh
one that happens to look similar.

Layout
------
For spatial graph models (``geometric``, ``grid``) the viewer reconstructs
the trial's graph from ``manifest.json`` and the per-trial seed — the
same call the harness made — so the positions it shows match the actual
node coordinates used during the run.  For non-spatial models
(``erdos_renyi``) there are no coordinates, so a seeded random scatter is
used; the layout is stable across calls but not geometrically meaningful.

Requires the ``viz`` extra::

    pip install -e ".[viz]"
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from dynaswarm.core.rng import stream

__all__ = ["replay", "MAX_NODES"]

#: Above this the layout is unreadable and the point of watching is lost.
MAX_NODES = 400

_BACKGROUND = (18, 18, 22)
_EDGE_NORMAL = (50, 52, 65)
_EDGE_DISRUPTED = (210, 75, 55)
_EDGE_PATH = (80, 145, 225)
_NODE = (95, 99, 115)
_NODE_PATH = (140, 175, 235)
_SOURCE = (75, 200, 105)
_TARGET = (230, 165, 55)
_TEXT = (210, 212, 220)
_TEXT_DIM = (115, 118, 132)


def replay(
    run_dir: Path | str,
    arm: str | None = None,
    scenario: str | None = None,
    trial: int = 0,
    fps: float = 1.0,
    size: tuple[int, int] = (1000, 720),
) -> None:
    """Watch one trial unfold.

    Args:
        run_dir: A run directory containing ``steps.parquet``,
            ``events.parquet``, and ``manifest.json``.
        arm: Which arm's route to draw; the first alphabetically if not
            given.
        scenario: Which scenario, if the run holds several.
        trial: Which trial.
        fps: Timesteps per second.  Defaults to 1 so each frame is
            readable; use :kbd:`Space` to pause and arrow keys to step.
        size: Window size.

    Raises:
        ImportError: If pygame is not installed.
        ValueError: If the selection matches no rows, or the graph is too
            large to render usefully.
    """
    try:
        import pygame
    except ImportError as exc:  # pragma: no cover - depends on the extra
        raise ImportError(
            "the replay viewer needs pygame: pip install -e '.[viz]'"
        ) from exc

    from dynaswarm.analysis.load import load_events, load_steps

    # One named run, so no class filter — see cli.py.  A viewer that
    # filtered would refuse to open every run it was pointed at.
    steps = load_steps(run_dir, run_class=None)
    events = load_events(run_dir)

    if scenario is not None:
        steps = steps[steps.scenario == scenario]
        events = events[events.scenario == scenario]
    steps = steps[steps.trial == trial]
    events = events[events.trial == trial]
    arm = arm or sorted(steps.arm.unique())[0]
    steps = steps[steps.arm == arm].sort_values("timestep")

    if steps.empty:
        raise ValueError(f"no rows for arm={arm!r} scenario={scenario!r} trial={trial}")

    n_nodes = int(steps.n_nodes.iloc[0])
    if n_nodes > MAX_NODES:
        raise ValueError(
            f"{n_nodes} nodes is past the {MAX_NODES} the viewer can show legibly; "
            "replay a smaller tier, or read the figures instead"
        )

    seed = int(steps.seed.iloc[0])
    layout, adjacency = _load_graph_layout(run_dir, seed, n_nodes, size)
    touched = _touched_by_timestep(events)

    pygame.init()
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption(f"dynaswarm — {arm} — trial {trial}")
    font = pygame.font.SysFont("monospace", 14)
    clock = pygame.time.Clock()

    rows = list(steps.itertuples())
    index, paused, running = 0, False, True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_RIGHT:
                    index = min(index + 1, len(rows) - 1)
                elif event.key == pygame.K_LEFT:
                    index = max(index - 1, 0)

        row = rows[index]
        _draw(
            pygame, screen, font, row,
            layout, adjacency, touched.get(row.timestep, ()),
            arm, size,
        )
        pygame.display.flip()

        if not paused:
            index += 1
            if index >= len(rows):
                index = len(rows) - 1
                paused = True
            time.sleep(max(0.0, 1.0 / fps))
        clock.tick(60)

    pygame.quit()


# ---------------------------------------------------------------------------
# Layout — real geometry from the trial seed
# ---------------------------------------------------------------------------


def _load_graph_layout(
    run_dir: Path | str,
    seed: int,
    n_nodes: int,
    size: tuple[int, int],
) -> tuple[np.ndarray, list[tuple[int, int]]]:
    """Return screen positions and base-edge list for the trial's graph.

    Reads ``manifest.json`` to recover the ``GraphCfg``, then calls
    :func:`build` with ``stream(seed, "graph")`` — the exact same call
    the harness made — so ``topo.pos`` contains the real node coordinates.

    Falls back to a seeded random scatter when the manifest is missing or
    the model carries no spatial coordinates.

    Args:
        run_dir: Run directory.
        seed: Trial seed (``steps.seed`` column).
        n_nodes: Node count, used only for the fallback.
        size: Screen dimensions in pixels.

    Returns:
        ``(layout, adjacency)`` where *layout* is an ``(n, 2)`` float
        array of pixel positions and *adjacency* is a list of
        ``(u, v)`` pairs for every base edge (u < v).
    """
    manifest_path = Path(run_dir) / "manifest.json"

    adjacency: list[tuple[int, int]] = []
    pos: np.ndarray | None = None

    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
            graph_cfg_dict = manifest.get("config", {}).get("graph", {})
            pos, adjacency = _rebuild_positions(graph_cfg_dict, seed)
        except Exception:  # noqa: BLE001 — never let a layout error crash the viewer
            pos = None

    if pos is None:
        # Non-spatial model or manifest not found: seeded random scatter.
        rng = stream(seed, "layout")
        pos = rng.random((n_nodes, 2))

    layout = _pos_to_screen(pos, size)
    return layout, adjacency


def _rebuild_positions(
    graph_cfg_dict: dict,
    seed: int,
) -> tuple[np.ndarray | None, list[tuple[int, int]]]:
    """Rebuild topology and extract real node positions and base edges.

    Args:
        graph_cfg_dict: The ``config.graph`` sub-dict from the manifest.
        seed: Trial seed.

    Returns:
        ``(pos, adjacency)`` — *pos* is ``None`` for non-spatial models.
    """
    from dynaswarm.config import GraphCfg
    from dynaswarm.core.generate import build

    cfg = GraphCfg(**graph_cfg_dict)
    rng = stream(seed, "graph")
    view, _source, _target = build(cfg, rng)

    topo = view.topology
    pos: np.ndarray | None = (
        np.asarray(topo.pos, dtype=np.float64)
        if topo.pos is not None
        else None
    )

    # Collect base edges (u < v, active at t=0).
    active = np.asarray(view.active)
    seen: set[tuple[int, int]] = set()
    adjacency: list[tuple[int, int]] = []
    for u in range(topo.n_nodes):
        lo, hi = int(topo.indptr[u]), int(topo.indptr[u + 1])
        for slot in range(lo, hi):
            v = int(topo.indices[slot])
            if active[slot] and u < v:
                key = (u, v)
                if key not in seen:
                    seen.add(key)
                    adjacency.append(key)

    return pos, adjacency


def _pos_to_screen(pos: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    """Map node coordinates to pixel positions.

    Normalises the coordinate range to [0, 1] so both unit-square models
    (geometric) and integer-grid models (grid) map cleanly to the same
    screen region.

    Args:
        pos: ``(n, 2)`` coordinate array.
        size: Screen width and height in pixels.

    Returns:
        ``(n, 2)`` float array of pixel positions.
    """
    margin = 70
    header = 90  # vertical pixels reserved for the text overlay
    w = size[0] - 2 * margin
    h = size[1] - 2 * margin - header

    xy = pos.copy().astype(np.float64)
    for dim in range(2):
        lo, hi = float(xy[:, dim].min()), float(xy[:, dim].max())
        if hi > lo:
            xy[:, dim] = (xy[:, dim] - lo) / (hi - lo)

    screen = np.empty_like(xy)
    screen[:, 0] = xy[:, 0] * w + margin
    screen[:, 1] = xy[:, 1] * h + margin + header
    return screen


# ---------------------------------------------------------------------------
# Event index
# ---------------------------------------------------------------------------


def _touched_by_timestep(events: pd.DataFrame) -> dict[int, tuple[tuple[int, int], ...]]:
    """Which node pairs a disruption hit, per timestep."""
    out: dict[int, list[tuple[int, int]]] = {}
    for row in events.itertuples():
        out.setdefault(row.timestep, []).append((min(row.u, row.v), max(row.u, row.v)))
    return {k: tuple(set(v)) for k, v in out.items()}


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _draw(
    pygame,
    screen,
    font,
    row,
    layout: np.ndarray,
    adjacency: list[tuple[int, int]],
    touched: tuple[tuple[int, int], ...],
    arm: str,
    size: tuple[int, int],
) -> None:
    """Render one timestep."""
    screen.fill(_BACKGROUND)

    # Build fast lookups.
    path = list(row.best_path) if hasattr(row, "best_path") else []
    path_edges: set[tuple[int, int]] = {
        (min(a, b), max(a, b))
        for a, b in zip(path[:-1], path[1:], strict=False)
    }
    disrupted: set[tuple[int, int]] = set(touched)

    # Draw all base edges: disrupted → red, path → blue, else dim grey.
    for u, v in adjacency:
        key = (u, v)  # u < v guaranteed by construction
        if key in disrupted:
            color, width = _EDGE_DISRUPTED, 2
        elif key in path_edges:
            color, width = _EDGE_PATH, 3
        else:
            color, width = _EDGE_NORMAL, 1
        pygame.draw.line(screen, color, layout[u], layout[v], width)

    # Also highlight disrupted pool edges that aren't in the initial adjacency.
    adj_set = set(adjacency)
    for u, v in touched:
        if (u, v) not in adj_set and u < len(layout) and v < len(layout):
            pygame.draw.line(screen, _EDGE_DISRUPTED, layout[u], layout[v], 2)

    # Draw all nodes; nodes on the path are brighter.
    path_set = set(path)
    for i, (x, y) in enumerate(layout):
        color = _NODE_PATH if i in path_set else _NODE
        pygame.draw.circle(screen, color, (int(x), int(y)), 3)

    # Emphasise source and target.
    if path:
        pygame.draw.circle(screen, _SOURCE, layout[path[0]].astype(int), 8)
        pygame.draw.circle(screen, _TARGET, layout[path[-1]].astype(int), 8)

    # Text overlay.
    n_ts = int(row.timestep)
    excess_str = "n/a" if pd.isna(row.excess) else f"{row.excess:+.1%}"
    lines = [
        f"arm {arm}   scenario {row.scenario}   trial {row.trial}",
        f"t {n_ts:3d}   disruptions this step: {row.num_events:2d}   excess {excess_str}",
        (
            f"optimum {row.optimum:8.2f}   cost {row.best_cost:8.2f}"
            if not pd.isna(row.best_cost)
            else "no route held yet"
        ),
        "space pause    \u2190/\u2192 step    q quit",
    ]
    dim_row = 3
    for i, text in enumerate(lines):
        color = _TEXT_DIM if i == dim_row else _TEXT
        screen.blit(font.render(text, True, color), (20, 16 + i * 18))
