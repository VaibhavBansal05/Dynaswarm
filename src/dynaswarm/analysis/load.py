"""Reading results back.

The tables are long and tidy, so most analysis is a groupby.  The only
awkwardness is the ``params`` and ``probe`` map columns, which pandas
surfaces as lists of key/value pairs; :func:`expand_maps` widens them
into ordinary columns on demand.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

#: What a row is taken to be when it predates the ``run_class`` column.
#:
#: Every parquet written before that column existed is, in fact, a
#: scratch run — so reading a missing value as ``exploratory`` is not
#: merely the safe default, it is the correct label.  Safe *and* correct:
#: an old run can never silently become evidence, and nothing has to be
#: migrated or rewritten to make that true (D27).
UNCLASSIFIED = "exploratory"

__all__ = ["load_steps", "load_events", "expand_maps", "per_trial_excess", "UNCLASSIFIED"]


def load_steps(
    directory: Path | str, run_class: str | None = "manifest"
) -> pd.DataFrame:
    """Load ``steps.parquet`` from one or more run directories.

    Reportable rows only, by default.  A scratch run and a hundred-trial
    experiment produce byte-identical tables apart from this column, so
    a load that silently mixed them would build a confident figure out of
    the wrong data and raise nothing.  Anything other than ``manifest``
    has to be asked for by name.

    Args:
        directory: A run directory, or a parent containing several.
        run_class: Which class to return; ``None`` returns every row
            regardless of class, which is what a provenance audit wants.

    Returns:
        The selected step rows, always carrying a ``run_class`` column.

    Raises:
        FileNotFoundError: If no ``steps.parquet`` exists beneath it.
    """
    return _classified(_load(directory, "steps.parquet"), run_class)


def load_events(
    directory: Path | str, run_class: str | None = "manifest"
) -> pd.DataFrame:
    """Load ``events.parquet`` from one or more run directories.

    Filtered exactly as :func:`load_steps` is, and for the same reason:
    recovery analysis reads events *across* runs, so an unlabelled scratch
    run would be mixed into a reported transient just as silently there.

    Args:
        directory: A run directory, or a parent containing several.
        run_class: Which class to return; ``None`` returns every row.

    Returns:
        The selected event rows, always carrying a ``run_class`` column.

    Raises:
        FileNotFoundError: If no ``events.parquet`` exists beneath it.
    """
    return _classified(_load(directory, "events.parquet"), run_class)


def _classified(frame: pd.DataFrame, run_class: str | None) -> pd.DataFrame:
    """Fill the class column, then apply the filter.

    Two distinct gaps to close, and a mixed load produces both at once: a
    tree where *no* run has the column, and a concatenation where only
    some do — pandas fills the latter with NaN.  Neither may raise.

    Shared by both loaders rather than written twice.  Provenance
    filtering that disagreed between the step table and the event table
    would be worse than none at all, because the disagreement would only
    surface once someone joined them.
    """
    if "run_class" not in frame.columns:
        frame["run_class"] = None
    frame["run_class"] = frame["run_class"].fillna(UNCLASSIFIED)
    if run_class is not None:
        frame = frame[frame["run_class"] == run_class]
    return frame


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


#: Columns that together identify one trial of one condition.
#:
#: ``run_id`` and the control settings belong here even though they feel
#: redundant.  A sweep writes several runs into one tree, and trial
#: indices restart in each: grouping on ``(scenario, arm, trial)`` alone
#: would silently average trial 0 of the ``edge_ratio`` run together with
#: trial 0 of the ``volatility`` run, yielding a number belonging to
#: neither condition and looking entirely reasonable.
TRIAL_KEYS = ["run_id", "scenario", "signal_kind", "controller_kind", "arm", "trial"]


def per_trial_excess(frame: pd.DataFrame) -> pd.DataFrame:
    """Reduce steps to one excess figure per trial of each condition.

    Paired tests operate on trials, not timesteps: successive timesteps
    within a trial share a graph and an event sequence and are strongly
    dependent, so treating them as independent observations would inflate
    the sample size and understate every p-value.

    Args:
        frame: Step rows.

    Returns:
        One row per :data:`TRIAL_KEYS` combination, with ``mean_excess``,
        ``final_excess``, ``availability``, ``evaluations`` and
        ``wall_ms``.
    """
    keys = [k for k in TRIAL_KEYS if k in frame.columns]
    return frame.groupby(keys, as_index=False).agg(
        mean_excess=("excess", "mean"),
        final_excess=("excess", "last"),
        availability=("path_valid", "mean"),
        evaluations=("evaluations_spent", "sum"),
        wall_ms=("wall_ms", "sum"),
    )
