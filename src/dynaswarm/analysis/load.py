"""Reading results back.

The tables are long and tidy, so most analysis is a groupby.  The only
awkwardness is the ``params`` and ``probe`` map columns, which pandas
surfaces as lists of key/value pairs; :func:`expand_maps` widens them
into ordinary columns on demand.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

__all__ = ["load_steps", "load_events", "expand_maps", "per_trial_excess"]


def load_steps(directory: Path | str) -> pd.DataFrame:
    """Load ``steps.parquet`` from one or more run directories.

    Args:
        directory: A run directory, or a parent containing several.

    Returns:
        All step rows concatenated.

    Raises:
        FileNotFoundError: If no ``steps.parquet`` exists beneath it.
    """
    return _load(directory, "steps.parquet")


def load_events(directory: Path | str) -> pd.DataFrame:
    """Load ``events.parquet`` from one or more run directories."""
    return _load(directory, "events.parquet")


def _load(directory: Path | str, filename: str) -> pd.DataFrame:
    root = Path(directory)
    direct = root / filename
    paths = [direct] if direct.exists() else sorted(root.rglob(filename))
    if not paths:
        raise FileNotFoundError(f"no {filename} under {root}")
    return pd.concat([pd.read_parquet(p) for p in paths], ignore_index=True)


def expand_maps(frame: pd.DataFrame, column: str, prefix: str | None = None) -> pd.DataFrame:
    """Widen a map column into one column per key.

    Args:
        frame: Step rows.
        column: ``"params"`` or ``"probe"``.
        prefix: Column-name prefix; defaults to ``column``.

    Returns:
        A copy with the map replaced by scalar columns.
    """
    prefix = prefix or column
    widened = pd.DataFrame(
        [dict(entry) if entry is not None else {} for entry in frame[column]],
        index=frame.index,
    ).add_prefix(f"{prefix}_")
    return pd.concat([frame.drop(columns=[column]), widened], axis=1)


def per_trial_excess(frame: pd.DataFrame) -> pd.DataFrame:
    """Reduce steps to one excess figure per ``(arm, trial)``.

    Paired tests operate on trials, not timesteps: successive timesteps
    within a trial share a graph and an event sequence and are strongly
    dependent, so treating them as independent observations would inflate
    the sample size and understate every p-value.

    Args:
        frame: Step rows.

    Returns:
        Columns ``scenario, arm, trial, mean_excess, final_excess,
        availability``.
    """
    grouped = frame.groupby(["scenario", "arm", "trial"], as_index=False)
    return grouped.agg(
        mean_excess=("excess", "mean"),
        final_excess=("excess", "last"),
        availability=("path_valid", "mean"),
        evaluations=("evaluations_spent", "sum"),
        wall_ms=("wall_ms", "sum"),
    )
