"""Transient response to disruption.

Mean excess averages a whole trial, which hides anything confined to the
few steps after an event.  Since the case for a hybrid rests on exactly
that window — the memoryless component covering the memory component's
staleness — the transient has to be measured directly or the argument
cannot be tested.

Three quantities, each answering a different question:

* **damage** — how far quality falls in the steps right after a
  disruption, relative to the calm before it;
* **recovery time** — how many steps until quality returns to that
  pre-disruption level;
* **settled excess** — quality during calm stretches only, which is the
  steady-state number the transient measures deviations from.

Disruptions too close to the end of a trial are dropped rather than
recorded as unrecovered.  An arm disrupted on the final timestep has no
opportunity to recover, and scoring that as a failure penalises whichever
arm happened to be hit late — right-censoring that falls unevenly and
would be read as a real difference.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

__all__ = ["Transient", "disruptions", "summarise_recovery", "per_trial_recovery"]

#: Steps after a disruption over which damage is measured.
DAMAGE_WINDOW = 3

#: Steps of calm required before a disruption for a clean baseline.
CALM_BEFORE = 2

#: Steps that must remain after a disruption for it to be scored at all.
MIN_HORIZON = 8

#: Fraction of the pre-disruption excess within which quality counts as
#: recovered.  A band rather than an exact return, since the search is
#: stochastic and will never land on precisely its former value.
RECOVERY_BAND = 0.10


@dataclass
class Transient:
    """One disruption and the arm's response to it.

    Attributes:
        timestep: When the disruption landed.
        baseline: Mean excess over the calm steps preceding it.
        damage: Worst excess in the window after it, minus the baseline.
            Negative means the disruption happened to help, which is
            possible: an event can open a shorter route.
        recovery: Steps until excess returned within the band, or
            ``None`` if it had not by the end of the trial.
    """

    timestep: int
    baseline: float
    damage: float
    recovery: int | None


def disruptions(
    excess: list[float | None],
    events: list[int],
    damage_window: int = DAMAGE_WINDOW,
    calm_before: int = CALM_BEFORE,
    min_horizon: int = MIN_HORIZON,
    band: float = RECOVERY_BAND,
) -> list[Transient]:
    """Locate scoreable disruptions and measure the response to each.

    Args:
        excess: Excess over the optimum per timestep; ``None`` where the
            arm held no route.
        events: Disruption count per timestep.
        damage_window: Steps after the event over which damage is taken.
        calm_before: Quiet steps required before the event.
        min_horizon: Steps that must remain after it.
        band: Tolerance for counting quality as recovered.

    Returns:
        One :class:`Transient` per scoreable disruption.
    """
    n = len(excess)
    out: list[Transient] = []

    for t in range(calm_before, n - min_horizon):
        if events[t] == 0:
            continue
        # A clean baseline needs genuine calm before the event, or the
        # "damage" is partly the tail of an earlier disruption.
        if any(events[t - k] > 0 for k in range(1, calm_before + 1)):
            continue

        before = [excess[t - k] for k in range(1, calm_before + 1)]
        if any(v is None for v in before):
            continue
        baseline = float(np.mean(before))

        after = [excess[k] for k in range(t, min(t + damage_window + 1, n))]
        after = [v for v in after if v is not None]
        if not after:
            continue
        damage = float(max(after)) - baseline

        threshold = baseline + band * max(abs(baseline), 1e-9)
        recovery: int | None = None
        for k in range(t, n):
            value = excess[k]
            if value is not None and value <= threshold:
                recovery = k - t
                break

        out.append(Transient(timestep=t, baseline=baseline, damage=damage, recovery=recovery))

    return out


def summarise_recovery(transients: list[Transient]) -> dict[str, float]:
    """Reduce a trial's transients to comparable numbers.

    Returns:
        ``mean_damage``, ``mean_recovery`` over those that recovered,
        ``recovered_fraction``, and ``n_disruptions``.  Means are ``nan``
        when nothing was scoreable, which keeps an empty trial out of an
        average rather than pulling it toward zero.
    """
    if not transients:
        return {
            "mean_damage": float("nan"),
            "mean_recovery": float("nan"),
            "recovered_fraction": float("nan"),
            "n_disruptions": 0,
        }

    recovered = [t.recovery for t in transients if t.recovery is not None]
    return {
        "mean_damage": float(np.mean([t.damage for t in transients])),
        "mean_recovery": float(np.mean(recovered)) if recovered else float("nan"),
        "recovered_fraction": len(recovered) / len(transients),
        "n_disruptions": len(transients),
    }


def per_trial_recovery(frame: pd.DataFrame) -> pd.DataFrame:
    """Compute transient metrics for every arm and trial in a run.

    Args:
        frame: Step rows, as loaded by :func:`~dynaswarm.analysis.load.load_steps`.

    Returns:
        One row per condition and trial, carrying the recovery summary
        alongside a ``settled_excess`` taken from quiet steps only.
    """
    from dynaswarm.analysis.load import TRIAL_KEYS

    keys = [k for k in TRIAL_KEYS if k in frame.columns]
    rows = []

    for values, group in frame.groupby(keys, sort=False):
        group = group.sort_values("timestep")
        excess = [None if pd.isna(v) else float(v) for v in group["excess"]]
        events = [int(v) for v in group["num_events"]]

        summary = summarise_recovery(disruptions(excess, events))
        quiet = [e for e, n in zip(excess, events, strict=True) if n == 0 and e is not None]
        summary["settled_excess"] = float(np.mean(quiet)) if quiet else float("nan")

        rows.append({**dict(zip(keys, values, strict=True)), **summary})

    return pd.DataFrame(rows)
