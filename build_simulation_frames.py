"""Render real simulation frames for the deck, using the actual replay viewer.

This runs one real trial, writes it to disk exactly like the harness does,
then drives ``dynaswarm.viz.replay``'s own drawing code headlessly (no
window) to capture PNG frames at a few representative timesteps. Nothing
here is hand-drawn — every node position, edge, and path comes from a
real run and the same renderer used interactively.
"""

from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from dataclasses import asdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from dynaswarm.config import BudgetCfg, Config, ExperimentCfg, GraphCfg, ScenarioCfg
from dynaswarm.harness.trial import run_trial
from dynaswarm.io.writer import ResultWriter, write_manifest

RUN_DIR = Path(__file__).parent / "ppt_assets" / "sim_run"
OUT = Path(__file__).parent / "ppt_assets"

BG = (13, 27, 42)
PANEL = (20, 42, 62)
ACCENT = (0, 212, 255)
GOLD = (255, 192, 0)
WHITE = (255, 255, 255)
LGREY = (176, 190, 204)


def run_and_record() -> tuple[str, int]:
    """Run one real trial with visible disruption, write it to RUN_DIR."""
    cfg = Config(
        graph=GraphCfg(model="geometric", n_nodes=40, density=0.16),
        scenario=ScenarioCfg(name="demo", events_per_step=0.6, cluster_size=6, timesteps=30),
        experiment=ExperimentCfg(n_trials=1, eval_seeds=[4242]),
        budget=BudgetCfg(evaluations=300),
    )
    outcome = run_trial(cfg, 0, ["hybrid"])
    with ResultWriter(RUN_DIR, run_id="sim") as writer:
        writer.write(outcome)
    write_manifest(RUN_DIR, "sim", asdict(cfg))
    return "hybrid", sum(r.num_events or 0 for r in outcome.steps)


def render_frames(arm: str) -> list[tuple[int, Path]]:
    """Capture PNG frames at a baseline / disruption / recovering / settled timestep."""
    import pygame

    from dynaswarm.analysis.load import load_events, load_steps
    from dynaswarm.viz.replay import _load_graph_layout, _touched_by_timestep, _draw

    steps = load_steps(RUN_DIR)
    events = load_events(RUN_DIR)
    steps = steps[steps.arm == arm].sort_values("timestep")
    n_nodes = int(steps.n_nodes.iloc[0])
    seed = int(steps.seed.iloc[0])
    size = (900, 680)

    layout, adjacency = _load_graph_layout(RUN_DIR, seed, n_nodes, size)
    touched = _touched_by_timestep(events)
    rows = list(steps.itertuples())

    pygame.init()
    screen = pygame.display.set_mode(size)
    font = pygame.font.SysFont("monospace", 14)

    # Find the real peak-damage timestep rather than a fixed offset —
    # a disruption's cost may not show up until a step or two later.
    excesses = [(r.timestep, r.excess or 0.0) for r in rows]
    peak_t = max(excesses, key=lambda p: p[1])[0]
    disrupted_ts = sorted(touched.keys())
    prior_events = [t for t in disrupted_ts if t < peak_t]
    disruption_t = prior_events[-1] if prior_events else max(peak_t - 1, 0)
    settled_t = next((t for t, e in excesses if t > peak_t and e <= 0.02), rows[-1].timestep)
    picks = {
        "1_baseline": 0,
        "2_disruption": disruption_t,
        "3_peak_damage": peak_t,
        "4_settled": settled_t,
    }

    by_t = {r.timestep: r for r in rows}
    saved = []
    for label, t in picks.items():
        row = by_t.get(t, rows[min(t, len(rows) - 1)])
        _draw(pygame, screen, font, row, layout, adjacency, touched.get(row.timestep, ()), arm, size)
        pygame.display.flip()
        path = OUT / f"sim_frame_{label}.png"
        pygame.image.save(screen, str(path))
        excess_str = "n/a" if row.excess is None else f"{row.excess:+.1%}"
        saved.append((row.timestep, path, row.num_events, excess_str))
        print(f"{label}: t={row.timestep} events={row.num_events} excess={excess_str}")

    pygame.quit()
    return saved


def _font(size: int) -> ImageFont.ImageFont:
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def storyboard(frames: list[tuple[int, Path, int, str]]) -> Path:
    """Compose the 4 captured frames into a 2x2 grid with large, readable captions.

    The pygame HUD baked into each frame is real but tiny at 14pt; the
    stats that matter for a slide are redrawn here at a size that reads
    from the back of a room, underneath the (untouched) rendered frame.
    """
    titles = ["1. Baseline route", "2. Disruption hits", "3. Peak damage", "4. Settled again"]
    imgs = [Image.open(p).convert("RGB") for _, p, _, _ in frames]
    w, h = imgs[0].size
    pad, cap_h, stat_h = 16, 44, 40
    cols, rows_n = 2, 2
    cell_h = cap_h + h + stat_h
    sheet_w = w * cols + pad * (cols + 1)
    sheet_h = cell_h * rows_n + pad * (rows_n + 1)
    sheet = Image.new("RGB", (sheet_w, sheet_h), BG)
    draw = ImageDraw.Draw(sheet)
    title_font = _font(28)
    stat_font = _font(22)
    for i, ((t, _p, n_events, excess), im, title) in enumerate(zip(frames, imgs, titles, strict=True)):
        col, row = i % cols, i // cols
        x = pad + col * (w + pad)
        y = pad + row * (cell_h + pad)
        bbox = draw.textbbox((0, 0), title, font=title_font)
        draw.text((x + (w - (bbox[2] - bbox[0])) / 2, y), title, fill=GOLD, font=title_font)
        sheet.paste(im, (x, y + cap_h))
        draw.rectangle([x, y + cap_h, x + w, y + cap_h + h], outline=(70, 80, 95), width=2)
        stat = f"t={t}   disruptions this step: {n_events}   excess {excess}"
        sbbox = draw.textbbox((0, 0), stat, font=stat_font)
        draw.text((x + (w - (sbbox[2] - sbbox[0])) / 2, y + cap_h + h + 8), stat,
                   fill=WHITE, font=stat_font)
    out_path = OUT / "fig_simulation_storyboard.png"
    sheet.save(out_path)
    print(f"wrote {out_path}")
    return out_path


if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    arm, _ = run_and_record()
    frames = render_frames(arm)
    storyboard(frames)
