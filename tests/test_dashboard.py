"""The boundary that keeps the dashboard a view.

`ARCHITECTURE.md` §2.3 states the rule these tests enforce: there is one
engine, and the dashboard is not it.  The reason is in the repository's
own history — v1 died of instrumentation that looked fine and quietly
disagreed with the thing it was instrumenting.

The rule is established here, before any drawing code exists, because a
boundary asserted after the fact is a boundary somebody has already had a
reason to cross.
"""

from __future__ import annotations

import ast
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from dynaswarm.core.generate import build
from dynaswarm.core.oracle import shortest_path
from dynaswarm.core.rng import stream
from tests.test_hygiene import _statement_count

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "dynaswarm"
DASHBOARD = ROOT / "dashboard"

#: The dashboard's own ceiling (D13/D14), separate from the science
#: surface's 2100 and never borrowed from it.
MAX_DASHBOARD_STATEMENTS = 1000


def _dashboard_files() -> list[Path]:
    return sorted(DASHBOARD.rglob("*.py"))


# ---------------------------------------------------------------------------
# Direction of dependency
# ---------------------------------------------------------------------------


def test_dynaswarm_never_imports_dashboard():
    """The core may not know the dashboard exists.

    Walked with ``ast`` rather than grepped, so a function-level or
    conditional import is caught too — this codebase already uses
    function-level imports (``generate._endpoints``), so "it is not at the
    top of the file" is not evidence of anything.
    """
    offenders = []
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                if name.split(".")[0] == "dashboard":
                    offenders.append(f"{path.relative_to(SRC)}:{node.lineno}")
    assert not offenders, f"dynaswarm imports dashboard at {offenders}"


def test_the_core_is_importable_and_usable_without_fastapi():
    """`dynaswarm` must not acquire a web dependency by proximity.

    Proved by making the import genuinely impossible in a subprocess
    rather than by trusting that nothing imports it: a meta-path hook
    raises on the whole web stack, and then the core is asked to do real
    work.  Checking ``sys.modules`` instead would pass in an interpreter
    that simply had not imported FastAPI yet.
    """
    program = textwrap.dedent(
        """
        import sys

        BANNED = {"fastapi", "uvicorn", "starlette"}

        class Blocker:
            def find_module(self, name, path=None):
                return self.find_spec(name, path)

            def find_spec(self, name, path=None, target=None):
                if name.split(".")[0] in BANNED:
                    raise ImportError(f"blocked: {name}")
                return None

        sys.meta_path.insert(0, Blocker())

        import dynaswarm
        from dynaswarm.config import GraphCfg
        from dynaswarm.core.generate import build
        from dynaswarm.core.oracle import shortest_path
        from dynaswarm.core.rng import stream

        cfg = GraphCfg(model="geometric", n_nodes=60, density=0.08)
        view, source, target = build(cfg, stream(7, "graph"))
        cost, _, _ = shortest_path(view, source, target, heuristic=True)
        assert cost > 0
        print("core works without fastapi")
        """
    )
    done = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True, cwd=ROOT
    )
    assert done.returncode == 0, done.stderr
    assert "core works without fastapi" in done.stdout


# ---------------------------------------------------------------------------
# The dashboard's own budget
# ---------------------------------------------------------------------------


def test_dashboard_statement_budget():
    """The dashboard has its own ceiling and never borrows from src/.

    Counted with ``test_hygiene``'s counter, imported rather than
    reimplemented.  A second counter that drifted from the first would be
    the same class of defect this whole segment exists to prevent, in
    miniature.
    """
    total = sum(_statement_count(p) for p in _dashboard_files())
    assert total < MAX_DASHBOARD_STATEMENTS, (
        f"dashboard/ is {total} statements, ceiling is {MAX_DASHBOARD_STATEMENTS}"
    )


def test_dashboard_is_outside_the_science_surface():
    """D14, asserted structurally.

    If ``dashboard/`` ever moved under ``src/``, its statements would
    start counting against the science cap and ``FORBIDDEN_IMPORTS``
    would ban its own web framework.  Both failures would be confusing;
    this one is not.
    """
    assert not str(DASHBOARD).startswith(str(SRC))
    assert _dashboard_files(), "no dashboard modules found — has it moved?"


# ---------------------------------------------------------------------------
# The anti-reimplementation test
# ---------------------------------------------------------------------------


def test_endpoint_returns_exactly_what_the_core_returns():
    """The endpoint asks the engine; it does not answer for it.

    Written to fail against a *plausible* reimplementation rather than a
    missing route, which is why it checks two different kinds of value:

    ``optimum_at_t0`` is a property of the graph — a competent
    reimplementation could arrive at it, though rarely bit-for-bit, since
    floating-point sums depend on the order edges are added.

    ``expansions`` is not a property of the graph at all.  It counts the
    nodes *this* A* popped, so it depends on the heuristic, the tie-break
    order and the heap discipline.  Nothing that recomputed the answer
    independently would reproduce it by luck.  That is the field that
    turns "the number looks right" into "it came from the engine".
    """
    server = pytest.importorskip("dashboard.server")

    payload = server.api_graph()

    cfg = server.tier("medium200")
    view, source, target = build(cfg, stream(payload["seed"], "graph"))
    optimum, path, expansions = shortest_path(view, source, target, heuristic=True)

    assert payload["source"] == source
    assert payload["target"] == target
    assert payload["optimum_at_t0"] == float(optimum)
    assert payload["expansions"] == expansions, (
        "expansion count differs — the dashboard is running its own search"
    )
    assert payload["hops"] == len(path) - 1
    assert payload["n_nodes"] == view.n_nodes
    assert payload["n_edges"] == view.n_active_edges


def test_the_endpoint_is_not_returning_a_constant():
    """A stub that hardcoded one real-looking answer would pass the above.

    Two seeds must give two different graphs.  Cheap, and it closes the
    one hole the equality test leaves open.
    """
    server = pytest.importorskip("dashboard.server")

    first = server.api_graph(seed=1000)
    second = server.api_graph(seed=1001)
    assert first["optimum_at_t0"] != second["optimum_at_t0"]


def test_has_coordinates_is_read_from_the_topology_not_assumed():
    """The fact that made the original replay useless.

    ``medium200`` is geometric and carries positions; ``small30`` is
    Erdos-Renyi and does not.  A hardcoded ``True`` would pass every other
    test in this file, and would send segment 7 off to draw a graph that
    has nowhere to put its nodes.
    """
    server = pytest.importorskip("dashboard.server")

    assert server.describe_graph(name="medium200")["has_coordinates"] is True
    assert server.describe_graph(name="small30")["has_coordinates"] is False


def test_run_classes_does_not_filter_to_manifest():
    """D30's single-run rule, in the place it actually bites.

    Every dashboard-created run is ``exploratory``, and since D31 there
    are no ``manifest`` runs at all — so a filtered read shows an empty
    screen for every run in existence. The failure would look like a
    broken page rather than a wrong default, which is why it is pinned.
    """
    server = pytest.importorskip("dashboard.server")

    classes = server.run_classes()
    assert "manifest" not in classes, "no manifest runs exist; see D31"
    if classes:
        assert set(classes) <= {"exploratory", "inversion"}
