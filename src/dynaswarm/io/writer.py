"""Streaming Parquet output.

Rows are written per trial rather than accumulated and flushed at the
end, so a sweep that dies halfway leaves usable data for the trials that
finished instead of nothing at all.

Alongside the tables a manifest records the interpreter, package
versions, and the resolved configuration.  A result whose exact
provenance is unknown cannot be reproduced, and reproducing it later is
the only way to check a number that looks surprising.
"""

from __future__ import annotations

import json
import platform
import subprocess
from collections.abc import Iterable
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from dynaswarm.harness.trial import EventRow, StepRow, TrialOutcome
from dynaswarm.io.schema import EVENT_SCHEMA, STEP_SCHEMA

__all__ = ["ResultWriter", "write_manifest"]


class ResultWriter:
    """Appends trial outcomes to ``steps.parquet`` and ``events.parquet``.

    Args:
        directory: Where the tables are written.
        run_id: Identifier stamped into every row.
    """

    def __init__(self, directory: Path | str, run_id: str) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id
        self._steps: pq.ParquetWriter | None = None
        self._events: pq.ParquetWriter | None = None

    def __enter__(self) -> ResultWriter:
        self._steps = pq.ParquetWriter(self.directory / "steps.parquet", STEP_SCHEMA)
        self._events = pq.ParquetWriter(self.directory / "events.parquet", EVENT_SCHEMA)
        return self

    def __exit__(self, *exc: object) -> None:
        for writer in (self._steps, self._events):
            if writer is not None:
                writer.close()
        self._steps = self._events = None

    def write(self, outcome: TrialOutcome) -> None:
        """Append one trial's rows as a single row group each."""
        if self._steps is None or self._events is None:
            raise RuntimeError("ResultWriter must be used as a context manager")
        if outcome.steps:
            self._steps.write_table(_step_table(outcome.steps, self.run_id))
        if outcome.events:
            self._events.write_table(_event_table(outcome.events, self.run_id))


def _step_table(rows: Iterable[StepRow], run_id: str) -> pa.Table:
    records = [{"run_id": run_id, **asdict(row)} for row in rows]
    columns = {
        field.name: [record.get(field.name) for record in records]
        for field in STEP_SCHEMA
    }
    # Arrow wants maps as lists of key/value pairs.
    for key in ("params", "probe"):
        columns[key] = [list(value.items()) for value in columns[key]]
    return pa.table(columns, schema=STEP_SCHEMA)


def _event_table(rows: Iterable[EventRow], run_id: str) -> pa.Table:
    records = [{"run_id": run_id, **asdict(row)} for row in rows]
    columns = {
        field.name: [record.get(field.name) for record in records]
        for field in EVENT_SCHEMA
    }
    return pa.table(columns, schema=EVENT_SCHEMA)


def write_manifest(directory: Path | str, run_id: str, config: Any) -> Path:
    """Record what produced this run.

    Args:
        directory: Run directory.
        run_id: Identifier shared with the tables.
        config: Resolved configuration, as a plain container.

    Returns:
        Path to the written manifest.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    manifest = {
        "run_id": run_id,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "git_sha": _git_sha(),
        "packages": _versions(),
        "config": config,
    }
    path = directory / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, default=str))
    return path


def _git_sha() -> str | None:
    """Current commit, or ``None`` outside a repository."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() or None


def _versions() -> dict[str, str]:
    import numpy
    import pyarrow
    import scipy

    return {
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
        "pyarrow": pyarrow.__version__,
    }
