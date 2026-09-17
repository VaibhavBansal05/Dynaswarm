"""Suite-wide containment.

`run_class` exists so that a scratch run can never silently become
evidence. A test harness able to write into `outputs/` is a hole straight
through that guarantee — and for one afternoon it was one: 25 run
directories accumulated there in a single session, one of them stamped
`manifest` by a corruption demonstration, which the provenance guard then
correctly failed on.

The detection worked. The containment did not exist. This is the
containment, and it is a fixture rather than a convention because a
convention lasts exactly as long as the person who remembers it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"

#: The dashboard's scratch root, ignored by this guard **by name**.
#:
#: Named rather than left outside `outputs/` by accident of path: the
#: carve-out is a decision, and a decision that exists only because two
#: directories happen not to overlap is one nobody can find later. If the
#: dashboard is ever pointed back at the evidence tree, this guard must
#: still fire — so it excludes one specific directory, not "anything that
#: is not outputs/".
SCRATCH = ROOT / "dashboard-runs"


def _snapshot() -> set[str]:
    if not OUTPUTS.exists():
        return set()
    return {str(p.relative_to(OUTPUTS)) for p in OUTPUTS.rglob("*")}


@pytest.fixture(scope="session", autouse=True)
def outputs_is_read_only():
    """Fail the session if anything appeared under ``outputs/``.

    Session-scoped and autouse so no test can opt out, and so it holds
    across the whole run rather than at whichever moment a single test
    happened to look.
    """
    before = _snapshot()
    yield
    appeared = sorted(_snapshot() - before)
    assert not appeared, (
        "the test suite wrote into outputs/, the evidence tree:\n  "
        + "\n  ".join(appeared[:20])
        + "\nTests must pass a tmp_path run root. See tests/conftest.py."
    )
