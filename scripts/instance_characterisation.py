"""How much of an optimal route sits on a bridging edge (segment Z3, T5).

`_ensure_connected` joins disconnected components by picking **one random
node from each**, not the nearest pair. On a geometric graph that bridge
can span the whole canvas, and since weight is Euclidean distance it is
priced accordingly — Rudra found one costing 87.228 on a route of ~100.

**Why this is not cosmetic.** If a few enormous bridges carry most of a
typical optimal route, the search problem is largely *"reach the
bridge"*, and every arm will look alike **for a structural reason rather
than because allocation does not help.** Those two conclusions produce
identical-looking results, and only one of them is about the thesis.

This measures it. It does **not** change the generator: every measurement
in this project was taken on these instances, and changing the problem
after seeing flat results is indistinguishable from searching for a
difference (Entry 024).

    ./.venv/bin/python scripts/instance_characterisation.py
"""

from __future__ import annotations

import statistics as st

import numpy as np

from dynaswarm.config import GraphCfg
from dynaswarm.core import generate as g
from dynaswarm.core.oracle import shortest_path
from dynaswarm.core.rng import stream

SEEDS = (1000, 1001, 1002, 7, 42, 9999, 123, 555)

MODELS = (
    ("geometric", 200, 0.04),
    ("erdos_renyi", 200, 0.04),
    ("grid", 400, 0.04),
    ("geometric", 1000, 0.04),
)


def bridges_for(cfg: GraphCfg, rng: np.random.Generator) -> set[tuple[int, int]]:
    """The edges `_ensure_connected` had to invent, as an undirected set.

    Recomputed rather than recorded: the generator does not mark them, and
    this is characterisation, so nothing in `src/` is touched to support
    it. The model call is re-run on a *fresh* stream seeded identically,
    so the edge set matches the one the real build produced.
    """
    if cfg.model == "geometric":
        raw, _ = g._geometric(cfg, rng)
    elif cfg.model == "erdos_renyi":
        raw, _ = g._erdos_renyi(cfg, rng)
    elif cfg.model == "grid":
        raw, _ = g._grid(cfg)
    else:
        raise ValueError(cfg.model)

    before = set(raw)
    after = g._ensure_connected(set(raw), cfg.n_nodes, rng)
    return after - before


def characterise(model: str, n_nodes: int, density: float, seed: int) -> dict:
    cfg = GraphCfg(model=model, n_nodes=n_nodes, density=density)

    # Two identical streams: one for the real build, one to replay the
    # model call and recover which edges were bridges.
    view, source, target = g.build(cfg, stream(seed, "graph"))
    bridges = bridges_for(cfg, stream(seed, "graph"))

    cost, path, _ = shortest_path(view, source, target, heuristic=True)
    if not np.isfinite(cost) or len(path) < 2:
        return {"bridges": len(bridges), "route_cost": None}

    on_route, bridge_cost = 0, 0.0
    for u, v in zip(path, path[1:], strict=False):
        slot = view.find_slot(int(u), int(v))
        w = float(view.weight[slot]) if slot >= 0 else 0.0
        if (min(u, v), max(u, v)) in bridges:
            on_route += 1
            bridge_cost += w

    return {
        "bridges": len(bridges),
        "route_cost": float(cost),
        "route_hops": len(path) - 1,
        "bridge_hops": on_route,
        "bridge_cost": bridge_cost,
        "share": bridge_cost / cost if cost else 0.0,
    }


def main() -> None:
    print("BRIDGING EDGES AND THE OPTIMAL ROUTE")
    print("=" * 92)
    print("  `_ensure_connected` joins components by one RANDOM node from each,")
    print("  not the nearest pair, so a bridge is priced by its Euclidean span.")
    print()
    print(
        f"  {'model':<14}{'n':>6}{'bridges':>9}{'hops':>7}"
        f"{'on bridges':>12}{'route cost':>12}{'% cost on bridges':>19}"
    )
    print("  " + "-" * 88)

    for model, n_nodes, density in MODELS:
        shares, counts = [], []
        for seed in SEEDS:
            r = characterise(model, n_nodes, density, seed)
            if r["route_cost"] is None:
                continue
            shares.append(r["share"])
            counts.append(r["bridges"])
            if seed == 1000:
                print(
                    f"  {model:<14}{n_nodes:>6}{r['bridges']:>9}{r['route_hops']:>7}"
                    f"{r['bridge_hops']:>12}{r['route_cost']:>12.2f}"
                    f"{r['share'] * 100:>18.1f}%   <- seed 1000"
                )
        if not shares:
            print(f"  {model:<14}{n_nodes:>6}   no reachable route in any seed")
            continue
        print(
            f"  {'':<14}{'':>6}{st.median(counts):>9.0f}{'':>7}{'':>12}{'':>12}"
            f"{st.median(shares) * 100:>18.1f}%   median over {len(shares)} seeds"
        )
        print(
            f"  {'':<14}{'':>6}{'':>9}{'':>7}{'':>12}{'':>12}"
            f"{max(shares) * 100:>18.1f}%   worst seed"
        )
        print()

    print("  A high share would mean the search problem is largely 'reach the")
    print("  bridge', and arms would look alike for a structural reason rather")
    print("  than because allocation does not help.")


if __name__ == "__main__":
    main()
