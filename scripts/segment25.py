"""Segment 25 — re-derive every claim from the 720,000 rows.

`FINDINGS_TESTS.md` was written from `analysis.txt`, which is itself a
derived summary. This module goes back to the parquet rows so that
document can carry a `[raw]` tag instead of a chain of transcriptions.

Loading 720,000 rows takes ~30s, so the per-trial reduction is cached
once and every later analysis reads the cache. The cache is derived, not
evidence: it lives in the scratchpad and can be deleted at any time.

    from scripts.segment25 import steps, trials
"""

from __future__ import annotations

import functools
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1] / "outputs" / "2026-09-19" / "18-43-05"

#: Where the paired analysis draws its per-seed numbers from. Both arms
#: of a comparison face a byte-identical world within one (run_id, trial),
#: so that pair is the unit of analysis.
PAIR_KEY = ["run_id", "trial"]


def tier_of(run_id: str) -> str:
    """`medium200-severe-0050` -> `medium200`."""
    return str(run_id).split("-")[0]


@functools.cache
def steps() -> pd.DataFrame:
    """Every recorded step row, with `tier` added."""
    from dynaswarm.analysis.load import load_steps

    frame = load_steps(RUN, run_class=None)
    frame["tier"] = frame["run_id"].map(tier_of)
    return frame


@functools.cache
def trials() -> pd.DataFrame:
    """One row per arm per seed, carrying everything the analyses need.

    Built here rather than with `per_trial_excess` because that reduction
    keeps only excess-derived columns, and segment 25 needs availability,
    churn, timing and the allocation telemetry at the same granularity.
    """
    frame = steps()
    rows = []
    for (tier, scenario, run_id, trial, arm), g in frame.groupby(
        ["tier", "scenario", "run_id", "trial", "arm"], sort=False
    ):
        g = g.sort_values("timestep")
        probe = [dict(p) if p is not None else {} for p in g["probe"]]
        excess = g["excess"].to_numpy(dtype=float)
        present = excess[~np.isnan(excess)]

        def probed(key: str, _probe=probe) -> np.ndarray:
            # `_probe` bound as a default: the closure would otherwise
            # capture the loop variable and every group would read the
            # last one's telemetry.
            return np.array([p.get(key, np.nan) for p in _probe], dtype=float)

        applied = probed("alloc_applied")
        proposed = probed("alloc_proposed")
        held = probed("alloc_held_back")
        fraction = probed("aco_fraction")
        signal = g["signal_value"].to_numpy(dtype=float)

        rows.append({
            "tier": tier, "scenario": scenario, "run_id": run_id,
            "trial": int(trial), "arm": arm, "seed": int(g["seed"].iloc[0]),
            "mean_excess": float(np.mean(present)) if present.size else np.nan,
            "worst_excess": float(np.max(present)) if present.size else np.nan,
            "availability": float(g["path_valid"].mean()),
            "route_changes": int(g["path_changed"].sum()),
            "wall_ms": float(g["wall_ms"].mean()),
            "rebind_ms": float(g["rebind_ms"].mean()),
            "oracle_ms": float(g["oracle_ms"].mean()),
            "n_events": int(g["num_events"].sum()),
            # Allocation telemetry. NaN for arms with no governor, which
            # is different from zero and must stay distinguishable.
            "alloc_moves": int(np.sum(np.abs(np.diff(applied[~np.isnan(applied)])) > 1e-12))
            if np.isfinite(applied).any() else -1,
            "alloc_clamped": int(np.sum(np.abs(held[~np.isnan(held)]) > 1e-12))
            if np.isfinite(held).any() else -1,
            "alloc_steps": int(np.isfinite(applied).sum()),
            "split_travel": float(np.nansum(np.abs(np.diff(fraction))))
            if np.isfinite(fraction).any() else np.nan,
            "split_min": float(np.nanmin(fraction)) if np.isfinite(fraction).any() else np.nan,
            "split_max": float(np.nanmax(fraction)) if np.isfinite(fraction).any() else np.nan,
            "corr_split_signal": _corr(fraction, signal),
            "signal_at_one": float(np.mean(signal >= 1.0 - 1e-9))
            if np.isfinite(signal).any() else np.nan,
            # Arms with no signal (A*, the uncontrolled ones) record all
            # NaN here, which is correct and different from zero.
            "signal_mean": float(np.nanmean(signal)) if np.isfinite(signal).any() else np.nan,
            # **`None`, not `NaN`.** `recovery.disruptions()` guards with
            # `v is None`, and a NaN slips past it — a NaN baseline then
            # propagates and silently changes the scoreable-disruption
            # count. Caching this as a float array made the medium200
            # damaged counts disagree with `analysis.txt` by 1-8 events
            # while large1000 matched exactly, because large1000 has no
            # unroutable steps and medium200/severe has 169.
            "_excess": [None if np.isnan(v) else float(v) for v in excess],
            "_events": g["num_events"].to_numpy(dtype=int),
            "_proposed": proposed,
        })
    return pd.DataFrame(rows)


def _corr(a: np.ndarray, b: np.ndarray) -> float:
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 3 or np.std(a[ok]) == 0 or np.std(b[ok]) == 0:
        return np.nan
    return float(np.corrcoef(a[ok], b[ok])[0, 1])


def paired(frame: pd.DataFrame, arm_a: str, arm_b: str,
           metric: str = "mean_excess") -> tuple[np.ndarray, np.ndarray]:
    """Two arms' values, aligned on the world they shared.

    Aligned on `(run_id, trial)`, not `trial`: the run was executed in
    chunks of 50 and trial indices restart in each, so `trial` alone
    would pair different worlds.
    """
    a = frame[frame["arm"] == arm_a].set_index(PAIR_KEY)[metric]
    b = frame[frame["arm"] == arm_b].set_index(PAIR_KEY)[metric]
    shared = sorted(set(a.index) & set(b.index))
    return (np.array([a.loc[k] for k in shared], dtype=float),
            np.array([b.loc[k] for k in shared], dtype=float))
