"""The trust report has to stay true as the system grows.

A report that lists what someone remembered to add is a status page. The
coverage test below is what makes this different: add a probe and forget
the report, and the suite fails rather than the document quietly going
stale — which is the failure mode of every verification document that
has ever aged into a lie.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import trust_report as tr  # noqa: E402


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    """One real run, built once, into a temp root — never ``outputs/``."""
    root = tmp_path_factory.mktemp("trust")
    return tr.build_run(root, evaluations=200)


def test_the_report_names_every_probed_mechanism(run):
    """Add a probe without adding it to the report and this fails.

    The one that keeps the document honest as the system grows. Checked
    against the fields a run *actually emits*, not against a list, so it
    cannot be satisfied by editing the expectation.
    """
    series, _ = tr.collect(run)
    covered = {(arm, field) for arm, field, _, _ in tr.MECHANISMS}

    missing = []
    for arm in tr.ARMS:
        for field in series.get(arm, {}):
            if field in tr.NON_MECHANISM or (arm, field) in covered:
                continue
            # Only then try the prefix. The Hybrid's probe wraps its
            # components' (hybrid.py:133), so `hybrid.aco_tau_changed` IS
            # `aco.tau_changed` — the same measurement under the arm that
            # owns the mechanism. But `hybrid.aco_spent` is the Hybrid's
            # OWN field about ACO, which is why the direct match comes
            # first: splitting everything on the prefix would file the
            # budget-split fields under an arm that does not have them.
            owner, name = arm, field
            if arm == "hybrid" and field.startswith(("aco_", "pso_")):
                owner, name = field.split("_", 1)
            if name in tr.NON_MECHANISM:
                continue
            if (owner, name) not in covered:
                missing.append(f"{arm}.{field}")
    assert not missing, (
        f"probe fields emitted but absent from the trust report: {sorted(missing)}"
    )


def test_no_value_renders_as_a_manufactured_zero(run):
    """Entry 015 R2, enforced rather than remembered.

    PSO's velocity reaches 5e-14. A fixed-decimal format turns that into
    ``0.0000`` and manufactures the exact claim this phase exists to make
    honestly — a mistake already nearly made once here, by the person
    looking for it.
    """
    assert tr.scale(5.112e-14) != "0"
    assert tr.scale(3.8e-06) != "0"
    assert "e-" in tr.scale(5.112e-14)
    assert tr.scale(0.0) == "0", "an actual zero should read as zero"

    series, horizon = tr.collect(run)
    text = tr.render(*tr.describe(run)) + tr.f13(series)
    for line in text.splitlines():
        assert "0.0000" not in line, f"a value was flattened to zero: {line!r}"


def test_a_disabled_mechanism_reads_inert_end_to_end(tmp_path, monkeypatch):
    """Not just in the probe — in the document a reader would be handed."""
    from dynaswarm.optimizers.aco import ACO

    monkeypatch.setattr(ACO, "_deposit", lambda self, path, cost: None)
    directory = tr.build_run(tmp_path, evaluations=200)
    series, _ = tr.collect(directory)
    text = tr.render(*tr.describe(directory))

    assert series["aco"]["tau_deposited"] == [0.0] * len(series["aco"]["tau_deposited"])
    deposit_line = next(
        line for line in text.splitlines() if "best ant reinforced" in line
    )
    assert "INERT" in deposit_line, f"a silent deposit did not read as inert: {deposit_line!r}"


def test_the_report_states_the_run_it_actually_read(run):
    """Not a default and not the last one.

    A trust report that cannot say which run it describes is describing
    nothing.
    """
    text = tr.render(*tr.describe(run))
    assert run.name in text, "the report does not name the run it read"
    assert str(run) in text, "the report does not say where it read it"
    assert "exploratory" in text

    other = tr.describe(run)[0]
    assert other["run_id"] == run.name


def test_the_report_carries_its_blind_spots_beside_the_probes(run):
    """Entry 015 R3 — beside, not in a footnote."""
    text = tr.render(*tr.describe(run))
    lines = text.splitlines()
    for field, note in tr.BLIND_SPOTS.items():
        what = next(w for _, f, w, _ in tr.MECHANISMS if f == field)
        row = next(i for i, line in enumerate(lines) if what in line)
        assert note[:40] in lines[row + 1], (
            f"the blind spot for {field} is not on the line below its probe"
        )


def test_f13_appears_with_its_contrast(run):
    """The finding that changes what the project can claim, with a number
    to compare it against rather than as prose."""
    series, _ = tr.collect(run)
    text = tr.f13(series)
    assert "F13" in text and "PHASE 3" in text
    assert "in isolation" in text, "the contrast is missing; the number means nothing alone"
    assert "1.4e-02" in text


def test_the_report_writes_nothing_into_outputs():
    """Segment 12's containment. Whatever run it reads, it reads."""
    outputs = ROOT / "outputs"
    before = {str(p) for p in outputs.rglob("*")} if outputs.exists() else set()
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "trust_report.py"),
             "--evaluations", "100"],
            capture_output=True, text=True, cwd=ROOT, check=True,
        )
        assert tmp  # the script uses its own temp root, not this one
    after = {str(p) for p in outputs.rglob("*")} if outputs.exists() else set()
    assert after == before, f"the report wrote into outputs/: {sorted(after - before)}"


def test_every_arm_with_mechanisms_gets_a_section(run):
    """An omitted arm is the report's worst failure and its quietest.

    Dropping PSO entirely leaves every remaining line true and the
    document looking complete. It was caught — but only by the F13 test
    and the blind-spot test, both of which happen to need PSO's fields.
    That is incidental protection: rewrite either for its own reasons and
    a whole optimizer can vanish from the trust report unremarked.

    Asserted against the arms that have mechanisms declared, so adding an
    arm to MECHANISMS without it reaching the report fails here.
    """
    text = tr.render(*tr.describe(run))
    declared = {arm for arm, _, _, _ in tr.MECHANISMS}
    assert declared, "no mechanisms declared at all"
    for arm in declared:
        assert f"\n{arm.upper()}\n" in text, (
            f"{arm} has declared mechanisms but no section in the report"
        )
    assert set(tr.ARMS) >= declared, (
        f"mechanisms declared for arms the report never runs: {declared - set(tr.ARMS)}"
    )


def test_a_sparse_row_reads_differently_dead_than_alive(run):
    """**The defect Rudra found by reading the report** (Entry 026).

    The staleness row read::

        share of trail mass that died this step  0  0  live  0.00 — ...

    Observed 0, broken-value 0.00, verdict ``live``. A row whose live and
    broken readings are identical discriminates nothing, and this whole
    document rests on the ``when broken`` column being a real
    discriminator.

    Not a probe defect: the signal is zero on 51 of 63 disrupted steps
    because a break that destroys no pheromone genuinely invalidates
    nothing. Zero is its normal value, so ``first``/``last`` was a summary
    of its silence.

    This drives the real renderer with a live series and a dead one and
    requires the two to differ — which is the property the row must have,
    stated without reference to how it is currently computed.
    """
    series, horizon = tr.collect(run)
    meta, _, _ = tr.describe(run)
    report = tr.render(meta, series, horizon)

    field = next(iter(tr.SPARSE_FIELDS))
    live = series["aco"].get(field)
    assert live is not None, f"{field} is not being recorded at all"
    assert any(v != 0 for v in live), (
        f"{field} was zero at every step in this run, so 'alive' and 'dead' "
        f"cannot be told apart here and the test proves nothing"
    )

    def row_for(values):
        import copy

        doctored = copy.deepcopy(series)
        doctored["aco"][field] = values
        text = tr.render(meta, doctored, horizon)
        return next(ln for ln in text.splitlines() if "died this step" in ln)

    alive_row = row_for(live)
    dead_row = row_for([0.0] * len(live))

    def numbers(row):
        """The two reported values, without the verdict word.

        **Compared separately on purpose.** Written first as
        `alive_row != dead_row`, which PASSED under the specified
        mutation — because the rows still differ by `live` against
        `INERT` even when both numbers read 0. That is exactly the defect
        Entry 026 described: the verdict column was always right, and the
        numbers beside it discriminated nothing. A reader comparing the
        value against `when broken` sees the same figure either way.
        """
        body = row.split("live")[0].split("INERT")[0]
        return body.split()[-2:]

    assert numbers(alive_row) != numbers(dead_row), (
        f"the two reported values are identical whether the mechanism is "
        f"alive or dead: {numbers(alive_row)}. The verdict word may differ, "
        f"but the numbers a reader compares against `when broken` do not"
    )
    assert "INERT" in dead_row, "a mechanism that never fired is not reported inert"
    assert "live" in alive_row

    # And the column change must be declared, or it is a different
    # misreading: two numbers under headings that no longer describe them.
    assert tr.SPARSE_FIELDS[field] in report, (
        "the row's columns mean something different from the rest of the "
        "table and the report does not say so"
    )
