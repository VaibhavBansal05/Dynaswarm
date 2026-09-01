"""Result table schemas.

Results are written long — one row per ``(trial, timestep, arm)`` — so
analysis is a groupby rather than a reshape, and adding an arm or a
scenario widens the table by rows instead of by columns.

Tunable values and telemetry are stored as ``map<string, double>`` rather
than fixed columns.  Different optimizers declare different parameters,
and a fixed schema would either need widening every time one is added or
would silently drop the ones it does not know about.
"""

from __future__ import annotations

import pyarrow as pa

__all__ = ["STEP_SCHEMA", "EVENT_SCHEMA"]

STEP_SCHEMA = pa.schema(
    [
        # provenance
        pa.field("run_id", pa.string()),
        # Carried per row, not only in the manifest: rows from several
        # runs get concatenated, and that is exactly when a scratch run
        # would otherwise be indistinguishable from a reported one.
        pa.field("run_class", pa.string()),
        # condition
        pa.field("scenario", pa.string()),
        pa.field("events_per_step", pa.float64()),
        pa.field("graph_model", pa.string()),
        pa.field("n_nodes", pa.int32()),
        pa.field("n_edges", pa.int32()),
        # position
        pa.field("trial", pa.int32()),
        pa.field("seed", pa.int64()),
        pa.field("timestep", pa.int32()),
        pa.field("arm", pa.string()),
        pa.field("arm_family", pa.string()),
        # what happened
        pa.field("num_events", pa.int32()),
        # quality, relative to the optimum for *this* state
        pa.field("optimum", pa.float64(), nullable=True),
        pa.field("best_cost", pa.float64(), nullable=True),
        pa.field("excess", pa.float64(), nullable=True),
        pa.field("path_valid", pa.bool_()),
        pa.field("path_changed", pa.bool_()),
        pa.field("path_len", pa.int32()),
        # The route itself, so a replay can draw what the arm actually
        # chose rather than reconstruct something merely plausible.
        pa.field("best_path", pa.list_(pa.int32())),
        # cost
        pa.field("evaluations_spent", pa.int32()),
        pa.field("wall_ms", pa.float64()),
        pa.field("astar_expansions", pa.float64(), nullable=True),
        # what was sensed, and what responded to it
        pa.field("signal_kind", pa.string()),
        pa.field("controller_kind", pa.string()),
        pa.field("signal_value", pa.float64(), nullable=True),
        # internals
        pa.field("params", pa.map_(pa.string(), pa.float64())),
        pa.field("probe", pa.map_(pa.string(), pa.float64())),
    ]
)

EVENT_SCHEMA = pa.schema(
    [
        pa.field("run_id", pa.string()),
        # Same exposure as the step table: events get concatenated across
        # runs for recovery analysis, and an unlabelled scratch run would
        # be silently mixed in there too.
        pa.field("run_class", pa.string()),
        pa.field("scenario", pa.string()),
        pa.field("trial", pa.int32()),
        pa.field("seed", pa.int64()),
        pa.field("timestep", pa.int32()),
        pa.field("kind", pa.string()),
        pa.field("u", pa.int32()),
        pa.field("v", pa.int32()),
        pa.field("old_weight", pa.float64()),
        pa.field("new_weight", pa.float64()),
    ]
)
