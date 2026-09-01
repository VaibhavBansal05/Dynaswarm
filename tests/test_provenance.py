"""Run provenance: what a results file says it is, and who is allowed to read it.

A `steps.parquet` from a hundred-trial experiment and one from a ten-second
smoke run are byte-identical in shape.  Nothing in the data distinguishes
them, so an analysis that loaded "all the results" would mix scratch rows
into a reported figure, produce a confident number, and raise nothing.
That is the failure that killed the predecessor codebase, and these tests
are what stop it recurring here.

Two halves, and they pull in opposite directions on purpose:

* **Aggregation is filtered.** :func:`load_steps` returns ``manifest`` rows
  and nothing else unless another class is named.  The unsafe direction is
  the one that needs an explicit request.
* **A single named run is not filtered.** Reporting on the run just
  produced, or replaying one directory, is not aggregation.  Filtering
  there would emit blank figures for every exploratory run and raise
  nothing — the same silent-wrongness in a new costume.

The migration rule (D27) sits underneath both: every parquet written
before the column existed reads as ``exploratory``, which is not merely
the safe default but the correct label for all of them.
"""

from __future__ import annotations

import json

import pandas as pd
import pytest

from dynaswarm.analysis.load import UNCLASSIFIED, load_events, load_steps
from dynaswarm.config import RUN_CLASSES, BudgetCfg, Config, ExperimentCfg, GraphCfg, ScenarioCfg
from dynaswarm.harness.trial import run_trial
from dynaswarm.io.writer import ResultWriter, write_manifest


def make_cfg(run_class: str = "exploratory", timesteps: int = 8) -> Config:
    return Config(
        root_seed=42,
        run_class=run_class,
        graph=GraphCfg(n_nodes=30, density=0.3),
        scenario=ScenarioCfg(name="test", events_per_step=0.8, timesteps=timesteps),
        experiment=ExperimentCfg(n_trials=1),
        budget=BudgetCfg(evaluations=120),
    )


def write_run(directory, cfg: Config, run_id: str = "r") -> None:
    """Write one real trial to ``directory`` the way the harness does."""
    with ResultWriter(directory, run_id=run_id) as writer:
        writer.write(run_trial(cfg, trial=0, arm_names=["aco"]))


# ---------------------------------------------------------------------------
# The field and its validation
# ---------------------------------------------------------------------------


def test_default_config_is_exploratory():
    """The safe default holds: a run that does not declare itself is scratch.

    Reportability has to be claimed deliberately.  A config that forgot to
    say what it was would otherwise default into the evidence pool.
    """
    assert Config().run_class == "exploratory"


def test_the_default_configuration_can_never_produce_an_inversion_run():
    """Required by ARCHITECTURE.md §12.

    Deliberately-broken code paths are the most dangerous thing in the
    repository, so ``inversion`` must be unreachable without asking for it
    by name.  Nothing can even set it yet — the inversion config group does
    not exist — and when it does, this test is what keeps it opt-in.
    """
    assert Config().run_class != "inversion"
    assert Config().run_class == "exploratory"


@pytest.mark.parametrize("value", ["manifest", "exploratory", "inversion"])
def test_every_permitted_run_class_is_accepted(value: str):
    assert Config(run_class=value).run_class == value


@pytest.mark.parametrize("value", ["Manifest", "real", "", "final", "experiment"])
def test_an_unrecognised_run_class_raises(value: str):
    """A typo must raise, never be absorbed.

    A misspelling that survived would create a class nobody filters on:
    the rows would be excluded from every reported figure and included in
    nothing, silently.
    """
    with pytest.raises(ValueError, match="unknown run_class"):
        Config(run_class=value)


def test_the_permitted_set_is_exactly_three():
    assert set(RUN_CLASSES) == {"manifest", "exploratory", "inversion"}


# ---------------------------------------------------------------------------
# Recorded in both places
# ---------------------------------------------------------------------------


def test_run_class_is_recorded_in_the_manifest(tmp_path):
    """The manifest describes the run, so it must carry the class."""
    cfg = make_cfg(run_class="manifest")
    write_manifest(tmp_path, "r", {"run_class": cfg.run_class})
    payload = json.loads((tmp_path / "manifest.json").read_text())
    assert payload["config"]["run_class"] == "manifest"


def test_run_class_is_recorded_as_a_column_on_every_row(tmp_path):
    """The column is what survives concatenation, which is the case that matters.

    The manifest alone is not enough: once rows from several runs are in
    one frame, the manifests are long gone.
    """
    write_run(tmp_path, make_cfg(run_class="manifest"))
    frame = pd.read_parquet(tmp_path / "steps.parquet")
    assert "run_class" in frame.columns
    assert (frame.run_class == "manifest").all()


def test_events_carry_the_run_class_too(tmp_path):
    """``events.parquet`` has the same concatenation exposure as the steps.

    Recovery analysis loads events across runs; an unlabelled scratch run
    would be mixed in there just as silently.
    """
    write_run(tmp_path, make_cfg(run_class="manifest"))
    events = pd.read_parquet(tmp_path / "events.parquet")
    assert "run_class" in events.columns
    assert (events.run_class == "manifest").all()


# ---------------------------------------------------------------------------
# The default filter
# ---------------------------------------------------------------------------


def test_load_steps_returns_only_manifest_rows_by_default(tmp_path):
    """Aggregation is filtered, and the unsafe direction needs asking for."""
    write_run(tmp_path / "keep", make_cfg(run_class="manifest"), run_id="keep")
    write_run(tmp_path / "drop", make_cfg(run_class="exploratory"), run_id="drop")

    default = load_steps(tmp_path)
    assert not default.empty
    assert set(default.run_class.unique()) == {"manifest"}

    every = load_steps(tmp_path, run_class=None)
    assert set(every.run_class.unique()) == {"manifest", "exploratory"}
    assert len(every) > len(default)


def test_a_named_class_can_be_requested_explicitly(tmp_path):
    write_run(tmp_path / "a", make_cfg(run_class="manifest"), run_id="a")
    write_run(tmp_path / "b", make_cfg(run_class="exploratory"), run_id="b")
    only_scratch = load_steps(tmp_path, run_class="exploratory")
    assert set(only_scratch.run_class.unique()) == {"exploratory"}


# ---------------------------------------------------------------------------
# The migration rule (D27) — no rewriting, no schema version
# ---------------------------------------------------------------------------


def _strip_run_class(directory) -> None:
    """Rewrite a run's parquet without the column, imitating a pre-D27 run.

    Done at the Arrow level rather than through pandas: ``params`` and
    ``probe`` are ``map<string, double>``, and a pandas round-trip turns
    them into lists of tuples that cannot be written back.  The point of
    the fixture is a file identical to a real pre-column run in every
    respect except the column, so the types have to survive.
    """
    import pyarrow.parquet as pq

    for name in ("steps.parquet", "events.parquet"):
        path = directory / name
        table = pq.read_table(path)
        pq.write_table(table.drop_columns(["run_class"]), path)


def test_a_parquet_with_no_run_class_column_loads_and_reads_as_exploratory(tmp_path):
    """The migration rule, against a file that genuinely lacks the column.

    Every parquet already on disk predates it.  Reading a missing value as
    ``exploratory`` is both the safe default — an old run can never
    silently become evidence — and the correct label, since all of them
    are in fact scratch runs.
    """
    write_run(tmp_path, make_cfg(run_class="manifest"))
    _strip_run_class(tmp_path)
    assert "run_class" not in pd.read_parquet(tmp_path / "steps.parquet").columns

    frame = load_steps(tmp_path, run_class=None)
    assert not frame.empty
    assert set(frame.run_class.unique()) == {UNCLASSIFIED}
    assert UNCLASSIFIED == "exploratory"


def test_a_pre_column_run_is_excluded_from_the_default_load(tmp_path):
    """Filling the column is not the same as trusting it.

    A run that predates the column must not become reportable by being
    read; it must be filtered out exactly like any other scratch run.
    """
    write_run(tmp_path, make_cfg(run_class="manifest"))
    _strip_run_class(tmp_path)
    assert load_steps(tmp_path).empty


def test_load_events_filters_and_migrates_exactly_as_load_steps_does(tmp_path):
    """The event table carries the same exposure, so it gets the same rules.

    Recovery analysis reads events *across* runs, so an unlabelled scratch
    run would be mixed into a reported transient there just as silently.
    Segment 3 added the column to ``EVENT_SCHEMA`` and stopped; the loader
    was left unfiltered, which closed the gap in the data and left it open
    in the code path that reads the data.
    """
    write_run(tmp_path / "keep", make_cfg(run_class="manifest"), run_id="keep")
    write_run(tmp_path / "drop", make_cfg(run_class="exploratory"), run_id="drop")
    write_run(tmp_path / "old", make_cfg(run_class="manifest"), run_id="old")
    _strip_run_class(tmp_path / "old")  # a genuine pre-column run

    default = load_events(tmp_path)
    assert not default.empty
    assert set(default.run_class.unique()) == {"manifest"}, "default is manifest-only"

    every = load_events(tmp_path, run_class=None)
    assert every.run_class.notna().all(), "no event row may come back unclassified"
    assert set(every.run_class.unique()) == {"manifest", "exploratory"}
    assert len(every) > len(default), "the mixed load must include the filtered rows"


def test_load_events_reads_a_missing_column_as_exploratory_on_real_data(tmp_path):
    """The migration rule (D27) applied to events, against a real pre-column file."""
    write_run(tmp_path, make_cfg(run_class="manifest"))
    _strip_run_class(tmp_path)
    assert "run_class" not in pd.read_parquet(tmp_path / "events.parquet").columns

    frame = load_events(tmp_path, run_class=None)
    assert not frame.empty
    assert set(frame.run_class.unique()) == {UNCLASSIFIED}
    assert load_events(tmp_path).empty, "a pre-column run is not reportable"


def test_a_mixed_load_classifies_both_halves_and_never_raises(tmp_path):
    """One directory with the column, one without — the concatenation case.

    This is the failure the column exists to prevent: pandas fills the
    missing side with NaN, and without the migration rule those rows
    would either raise or silently compare unequal to every class.
    """
    write_run(tmp_path / "new", make_cfg(run_class="manifest"), run_id="new")
    write_run(tmp_path / "old", make_cfg(run_class="manifest"), run_id="old")
    _strip_run_class(tmp_path / "old")

    every = load_steps(tmp_path, run_class=None)
    assert every.run_class.notna().all(), "no row may come back unclassified"
    assert set(every.run_class.unique()) == {"manifest", "exploratory"}

    default = load_steps(tmp_path)
    assert set(default.run_class.unique()) == {"manifest"}
    assert len(default) < len(every), "the pre-column half must be filtered out"


# ---------------------------------------------------------------------------
# Ruling 1 — a single named run is not an aggregation
# ---------------------------------------------------------------------------


def test_a_single_run_load_is_not_filtered(tmp_path):
    """The report path must see its own rows whatever class they are.

    ``load_steps``'s default protects aggregation *across* runs.  A tool
    reporting on one named run is not aggregating, so it passes the class
    through explicitly.  Without this, ``report=true`` on an exploratory
    run writes blank figures and an empty CSV and raises nothing — which
    is the same silent wrongness the column was added to prevent.
    """
    write_run(tmp_path, make_cfg(run_class="exploratory"))

    assert load_steps(tmp_path).empty, "aggregation must still filter this run out"

    single = load_steps(tmp_path, run_class=None)
    assert not single.empty, "a single-run load must return its rows"
    assert set(single.run_class.unique()) == {"exploratory"}


def test_the_report_path_produces_non_empty_output_for_an_exploratory_run(tmp_path):
    """End to end, the check that would have caught the spec's contradiction.

    Run A of this segment is ``report=true`` on a default — therefore
    exploratory — run.  Under a filtered read its figures and tables come
    out empty with no error at all.
    """
    from dynaswarm.analysis.load import per_trial_excess

    write_run(tmp_path, make_cfg(run_class="exploratory"))
    steps = load_steps(tmp_path, run_class=None)
    assert not steps.empty
    assert not per_trial_excess(steps).empty


# ---------------------------------------------------------------------------
# F3 — cross_evaluate.py is repaired, though it cannot run until Phase 4
# ---------------------------------------------------------------------------


def test_cross_evaluate_imports_and_builds_a_valid_config():
    """F3 — the script is correct against today's API and scenarios.

    It cannot be *executed* until Phase 4 produces the per-scenario tuned
    vectors it needs, so what is testable now is that it constructs valid
    configuration under the current disruption model.  It previously
    passed ``churn`` — a fraction of |E| from the superseded proportional
    model — and raised ``TypeError`` on import of the first config.
    """
    import importlib.util
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "cross_evaluate", root / "scripts" / "cross_evaluate.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Today's registered rates, not a translation of the old fractions.
    assert module.SCENARIOS == {"static": 0.0, "moderate": 0.3, "high": 0.8}
    assert not hasattr(module, "CHURN"), "the proportional churn model is gone"

    cfg = module.make_cfg({"rho": 0.2}, module.SCENARIOS["high"])
    assert isinstance(cfg, Config)
    assert cfg.scenario.events_per_step == 0.8
    assert cfg.control.fixed_params == {"rho": 0.2}
    assert cfg.run_class == "exploratory", "a script run is never reportable"


def test_cross_evaluate_refuses_to_run_without_tuned_vectors(monkeypatch, tmp_path):
    """It must fail readably, not with a TypeError or an empty table.

    The original failure mode would have been worse than a crash: an empty
    glob feeding an empty dict produces a confident-looking cross-
    evaluation built on default parameters — a vector silently compared
    against itself.
    """
    import importlib.util
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "cross_evaluate_missing", root / "scripts" / "cross_evaluate.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    monkeypatch.setattr(module, "VECTOR_GLOB", str(tmp_path / "nothing" / "*.json"))
    with pytest.raises(SystemExit) as excinfo:
        module.require_vectors()

    message = str(excinfo.value)
    assert "cannot run" in message
    assert "Phase 4" in message, "must name the phase that produces the vectors"
    assert "ARCHITECTURE.md" in message, "must name where the step is specified"
