"""Replaying a recorded run.

The viewer reads finished results and re-renders them.  It never drives a
simulation, holds no optimizer, and imports nothing from the harness, so
it cannot perturb a result or alter the determinism of one — a viewer
that stepped the search itself would be able to do both.

The cost is that only what was recorded can be shown: paths are stored
per timestep, so the replay is faithful to the run rather than a fresh
one that happens to look similar.

Requires the ``viz`` extra::

    pip install -e ".[viz]"
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd

from dynaswarm.core.rng import stream

__all__ = ["replay", "MAX_NODES"]

#: Above this the layout is unreadable and the point of watching is lost.
MAX_NODES = 400

_BACKGROUND = (18, 18, 22)
_EDGE = (60, 62, 72)
_EDGE_DISRUPTED = (200, 90, 70)
_NODE = (120, 124, 138)
_SOURCE = (90, 190, 120)
_TARGET = (230, 170, 70)
_PATH = (110, 170, 240)
_TEXT = (210, 212, 220)


def replay(
    run_dir: Path | str,
    arm: str | None = None,
    scenario: str | None = None,
    trial: int = 0,
    fps: float = 4.0,
    size: tuple[int, int] = (1000, 720),
) -> None:
    """Watch one trial unfold.

    Args:
        run_dir: A run directory containing ``steps.parquet`` and
            ``events.parquet``.
        arm: Which arm's route to draw; the first alphabetically if not
            given.
        scenario: Which scenario, if the run holds several.
        trial: Which trial.
        fps: Timesteps per second.
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

    steps = load_steps(run_dir)
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

    layout = _layout(n_nodes, size, seed=int(steps.seed.iloc[0]))
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
        _draw(pygame, screen, font, row, layout, touched.get(row.timestep, ()), arm, size)
        pygame.display.flip()

        if not paused:
            index += 1
            if index >= len(rows):
                index = len(rows) - 1
                paused = True
            time.sleep(max(0.0, 1.0 / fps))
        clock.tick(60)

    pygame.quit()


def _layout(n_nodes: int, size: tuple[int, int], seed: int) -> np.ndarray:
    """Screen positions for each node.

    Coordinates are not recorded in the results, so the layout is
    reproduced from the trial's seed.  It is a picture of the graph's
    connectivity, not its true geometry.
    """
    rng = stream(seed, "layout")
    margin = 60
    width, height = size[0] - 2 * margin, size[1] - 2 * margin - 80
    points = rng.random((n_nodes, 2))
    points[:, 0] = points[:, 0] * width + margin
    points[:, 1] = points[:, 1] * height + margin + 60
    return points


def _touched_by_timestep(events: pd.DataFrame) -> dict[int, tuple]:
    """Which node pairs a disruption hit, per timestep."""
    out: dict[int, list] = {}
    for row in events.itertuples():
        out.setdefault(row.timestep, []).append((row.u, row.v))
    return {k: tuple(v) for k, v in out.items()}


def _draw(pygame, screen, font, row, layout, touched, arm: str, size) -> None:
    """Render one timestep."""
    screen.fill(_BACKGROUND)

    for u, v in touched:
        if u < len(layout) and v < len(layout):
            pygame.draw.line(screen, _EDGE_DISRUPTED, layout[u], layout[v], 3)

    path = list(row.best_path) if hasattr(row, "best_path") else []
    for a, b in zip(path[:-1], path[1:], strict=False):
        pygame.draw.line(screen, _PATH, layout[a], layout[b], 3)

    for x, y in layout:
        pygame.draw.circle(screen, _NODE, (int(x), int(y)), 3)
    if path:
        pygame.draw.circle(screen, _SOURCE, layout[path[0]].astype(int), 7)
        pygame.draw.circle(screen, _TARGET, layout[path[-1]].astype(int), 7)

    excess = "n/a" if pd.isna(row.excess) else f"{row.excess:+.1%}"
    lines = [
        f"arm {arm}   scenario {row.scenario}   trial {row.trial}",
        f"t {row.timestep:3d}   events {row.num_events:2d}   excess {excess}",
        f"optimum {row.optimum:8.2f}   cost {row.best_cost:8.2f}"
        if not pd.isna(row.best_cost)
        else "no route held",
        "space pause    left/right step    q quit",
    ]
    for i, text in enumerate(lines):
        screen.blit(font.render(text, True, _TEXT), (20, 16 + i * 18))
