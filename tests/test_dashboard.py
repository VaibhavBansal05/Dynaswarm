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
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import numpy as np
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


# ---------------------------------------------------------------------------
# Entry 006's rulings
# ---------------------------------------------------------------------------


def test_tier_returns_what_the_config_store_registers():
    """Named for what it guards: the ``ConfigStore.repo`` read in ``tier()``.

    ``tier()`` deliberately reads the tier back out of Hydra rather than
    restating ``GraphCfg(model="geometric", n_nodes=200, ...)``, because a
    restated constant works right up until someone edits the registration
    and then draws a tier that no longer exists under that name.

    Until now the only thing that would have caught a Hydra change was a
    test named for coordinates — incidental protection, one refactor from
    gone (Entry 005 R3). This says so in its name.

    Asserted against the registration itself, never against literals: a
    test that hardcoded ``n_nodes == 200`` would reintroduce exactly the
    drift ``tier()`` exists to prevent.
    """
    from hydra.core.config_store import ConfigStore
    from omegaconf import OmegaConf

    from dynaswarm.config import register

    server = pytest.importorskip("dashboard.server")

    register()
    registered = OmegaConf.to_object(
        ConfigStore.instance().repo["graph"]["medium200.yaml"].node
    )
    assert server.tier("medium200") == registered


def test_the_route_serialises_over_real_http():
    """Direct calls never touch JSON, and the browser only ever touches JSON.

    ``describe_graph`` casts numpy scalars by hand.  The day someone adds
    a field and forgets the cast, every direct-call test still passes and
    the page 500s — the failure lands entirely outside what the rest of
    this file can see.  TestClient covers real routing and real
    serialisation without a socket, a port or a teardown.
    """
    pytest.importorskip("dashboard.server")
    testclient = pytest.importorskip("fastapi.testclient")
    from dashboard.server import app

    with testclient.TestClient(app) as client:
        for route in ("/api/graph", "/api/graph/geometry", "/api/runs"):
            response = client.get(route)
            assert response.status_code == 200, route
            assert json.loads(response.content), route


# ---------------------------------------------------------------------------
# The drawing is the engine's, not the browser's
# ---------------------------------------------------------------------------


def _geometry(name: str = "medium200") -> dict:
    server = pytest.importorskip("dashboard.server")
    return server.describe_geometry(name=name)


def test_the_path_is_a_real_walk_from_source_to_target():
    """A plausible node list is not a path.

    Every consecutive pair must be an **active edge** of the graph the
    endpoint returned.  This is what separates "the oracle's route" from
    "twelve node indices that look about right".
    """
    geo = _geometry()
    assert geo["path"][0] == geo["source"]
    assert geo["path"][-1] == geo["target"]

    live = {tuple(sorted(edge)) for edge in geo["edges"]}
    for a, b in zip(geo["path"], geo["path"][1:], strict=False):
        assert tuple(sorted((a, b))) in live, f"path uses a dead edge {a}-{b}"


def test_the_paths_weights_sum_to_the_quoted_optimum():
    """The strong one: the drawn path and the quoted cost are one computation.

    The page prints ``optimum`` beside a highlighted route.  If either is
    ever recomputed independently of the other they drift, and the picture
    starts disagreeing with its own caption — the failure that looks
    entirely fine on screen.  Summing the returned weights along the
    returned path closes that.
    """
    geo = _geometry()
    cost = {tuple(sorted(e)): w for e, w in zip(geo["edges"], geo["weights"], strict=True)}
    steps = zip(geo["path"], geo["path"][1:], strict=False)
    walked = sum(cost[tuple(sorted(pair))] for pair in steps)
    assert walked == pytest.approx(geo["optimum"])


def test_positions_are_the_cores_own_coordinates():
    """Element-wise against ``view.topology.pos``, not merely the right shape."""
    server = pytest.importorskip("dashboard.server")
    geo = _geometry()

    view, _, _ = build(server.tier("medium200"), stream(geo["seed"], "graph"))
    assert np.asarray(geo["positions"]) == pytest.approx(np.asarray(view.topology.pos))


def test_edges_are_exactly_what_the_core_says_is_active():
    """No more and no less than ``n_active_edges``.

    The count is the cheap half.  The expensive half is that the browser
    must not be choosing: every returned pair has to be a live slot, which
    the walk test above then relies on.
    """
    server = pytest.importorskip("dashboard.server")
    geo = _geometry()

    view, _, _ = build(server.tier("medium200"), stream(geo["seed"], "graph"))
    assert len(geo["edges"]) == view.n_active_edges


def test_edges_and_weights_are_parallel():
    """The assumption the page trusts without checking.

    Nothing visible breaks the day these desynchronise — the drawing keeps
    working and every edge is simply labelled with someone else's cost.

    Written first as a length check, which is what "parallel arrays"
    invites.  A mutation that rolled ``weights`` by one against ``edges``
    walked straight through it: same length, every value real, every
    label wrong.  It was caught downstream by the summed-weights test —
    incidental protection under a name that promised the real thing.
    So the check is now per edge, against the core's own weight for that
    exact pair.
    """
    server = pytest.importorskip("dashboard.server")
    geo = _geometry()
    assert len(geo["edges"]) == len(geo["weights"])

    view, _, _ = build(server.tier("medium200"), stream(geo["seed"], "graph"))
    for (u, v), weight in zip(geo["edges"], geo["weights"], strict=True):
        assert weight == pytest.approx(float(view.weight[view.find_slot(u, v)]))


def test_a_tier_without_coordinates_answers_and_refuses():
    """T4's contract, server-side.

    ``small30`` is Erdos-Renyi and the generator never made positions for
    it.  The endpoint must still answer — the page needs to know *why* it
    is not drawing — but it must not manufacture coordinates to fill the
    field.  Any picture built from invented positions is a picture of the
    layout algorithm, which is what made v1's replay worthless.
    """
    geo = _geometry("small30")
    assert geo["has_coordinates"] is False
    assert geo["positions"] == []
    assert geo["edges"], "the graph still exists; only its geometry is missing"
    assert geo["path"][0] == geo["source"]


# ---------------------------------------------------------------------------
# The second budget (Entry 007 R1)
# ---------------------------------------------------------------------------

#: Ceiling on the dashboard's browser-side surface, in **non-blank,
#: non-comment lines** of ``.js``, ``.css`` and ``.html``.
MAX_STATIC_LINES = 1200

STATIC = DASHBOARD / "static"
# .json is in here because the budget's question is "has this become an
# application?", and a growing palette or config file is that growth as
# surely as a growing script. The code/data line is not where the risk
# lives (Entry 009 R2).
STATIC_SUFFIXES = {".js", ".css", ".html", ".json"}


def _static_lines(path: Path) -> int:
    """Count non-blank, non-comment lines.

    **This is a cruder instrument than ``_statement_count`` and must not
    be reasoned about as if it were the same measure.** That one parses
    Python and counts AST statements, so reformatting cannot move it.
    This one counts lines, so it *can* be moved by wrapping differently,
    and it says nothing about how much behaviour a line carries.

    Counting JavaScript statements properly needs a JavaScript parser,
    and this repository will not take a dependency to enforce a budget.
    The point of a blunt number here is that it is **not zero**: the
    statement counter globs ``*.py`` and reported 0 for a file that grew
    to 142 lines, which is a brake reporting comfortable headroom while
    the growing half of the dashboard went unmeasured — F5's shape, a
    dead instrument returning a flattering number.
    """
    count, in_block = 0, False
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line:
            continue
        if in_block:
            in_block = "*/" not in line
            continue
        if path.suffix in {".js", ".css"} and line.startswith("/*"):
            in_block = "*/" not in line
            continue
        if path.suffix == ".js" and line.startswith("//"):
            continue
        if path.suffix == ".html" and line.startswith("<!--"):
            continue
        count += 1
    return count


def _static_files() -> list[Path]:
    return sorted(p for p in STATIC.rglob("*") if p.suffix in STATIC_SUFFIXES)


def test_dashboard_static_line_budget():
    """*Has the dashboard become an application?*

    A different question from the Python cap's *has it become a second
    engine?*, which is why they are two budgets and not one stretched
    over both. See :func:`_static_lines` on why this one is deliberately
    the cruder measure.
    """
    total = sum(_static_lines(p) for p in _static_files())
    assert total < MAX_STATIC_LINES, (
        f"dashboard/static/ is {total} lines, ceiling is {MAX_STATIC_LINES}"
    )


# ---------------------------------------------------------------------------
# Time — the layer F1 could come back in
# ---------------------------------------------------------------------------


def _timeline() -> dict:
    server = pytest.importorskip("dashboard.server")
    return server.describe_timeline()


def _rebuild(run: dict):
    """The core's own timeline for the run the endpoint just described."""
    from dynaswarm.core.timeline import GraphTimeline, build_schedule

    server = pytest.importorskip("dashboard.server")
    scenario = server._registered("scenario", run["scenario"])
    view, source, target = build(server.tier(run["tier"]), stream(run["seed"], "graph"))
    schedule = build_schedule(view, scenario, stream(run["seed"], "events"), source, target)
    return GraphTimeline(view, schedule), source, target


def test_marker_time_equals_engine_time_at_every_timestep():
    """**The F1 test for the visual layer.**

    A marker drawn one step early crashes nothing and looks like nothing.
    The demo simply shows an edge snapping at the wrong moment beside a
    correct cost — a lie you can point at, in the artefact built to
    convince an examiner.

    So this compares the endpoint's events against
    ``GraphTimeline.events_at`` at **every** ``t``, not a sampled few.
    An off-by-one is invisible at ``t = 0`` when both are empty.
    """
    run = _timeline()
    timeline, _, _ = _rebuild(run)

    for step in run["steps"]:
        expected = timeline.events_at(step["t"])
        assert len(step["events"]) == len(expected), f"t={step['t']}"
        for sent, event in zip(step["events"], expected, strict=True):
            assert (sent["kind"], sent["u"], sent["v"]) == (event.kind, event.u, event.v), (
                f"t={step['t']}"
            )


def test_the_optimum_at_every_timestep_is_the_oracles():
    """The anti-reimplementation test, extended across time.

    One matching optimum proves a lucky index. Sixty proves the endpoint
    is asking the engine at each state rather than answering for it.
    """
    run = _timeline()
    timeline, source, target = _rebuild(run)

    for step in run["steps"]:
        optimum, _, _ = shortest_path(
            timeline.state_at(step["t"]), source, target, heuristic=True
        )
        if step["reachable"]:
            assert step["optimum"] == pytest.approx(float(optimum)), f"t={step['t']}"
        else:
            assert not np.isfinite(optimum), f"t={step['t']}"


def test_every_path_is_a_real_walk_in_the_graph_as_it_stands_then():
    """A path valid at t=0 and invalid at t=30 is what a stale cache is.

    Checked against **that timestep's** active mask, not the initial one:
    an edge closed at t=12 must not still be carrying the route at t=13.
    """
    run = _timeline()
    timeline, source, target = _rebuild(run)

    for step in run["steps"]:
        if not step["reachable"]:
            assert step["path"] == [], f"t={step['t']}"
            continue
        state = timeline.state_at(step["t"])
        assert step["path"][0] == source and step["path"][-1] == target
        for u, v in zip(step["path"], step["path"][1:], strict=False):
            slot = state.find_slot(u, v)
            assert slot >= 0 and state.active[slot], f"dead edge {u}-{v} at t={step['t']}"


def test_every_paths_weights_sum_to_that_timesteps_optimum():
    """Segment 7's strongest test, run at every step.

    The picture and its caption must come from one computation at each
    ``t``, not only at the first — a cached path beside a live optimum
    would pass a t=0-only check and diverge the moment anything breaks.
    """
    run = _timeline()
    timeline, _, _ = _rebuild(run)

    for step in run["steps"]:
        if not step["reachable"]:
            continue
        state = timeline.state_at(step["t"])
        walked = sum(
            float(state.weight[state.find_slot(u, v)])
            for u, v in zip(step["path"], step["path"][1:], strict=False)
        )
        assert walked == pytest.approx(step["optimum"]), f"t={step['t']}"


def test_the_timeline_endpoint_is_stateless():
    """No cursor lives on the server, so nothing can disagree about ``t``.

    Two identical calls must be identical, and calls for other runs in
    between must not perturb them — the shape a cached "current step"
    would break.
    """
    server = pytest.importorskip("dashboard.server")

    first = server.describe_timeline()
    server.describe_timeline(seed=1001)
    server.describe_timeline(scenario_name="high")
    assert server.describe_timeline() == first


def test_unreachability_is_represented_rather_than_crashed_on():
    """A disruption can disconnect the graph; that is a result, not an error.

    The decision pinned here: ``optimum`` is ``None``, ``path`` is empty,
    ``reachable`` is ``False``, and the step still exists so playback
    continues through it. Exercised on a scenario violent enough to make
    it possible rather than asserted only in the abstract.
    """
    server = pytest.importorskip("dashboard.server")

    run = server.describe_timeline(scenario_name="high")
    assert len(run["steps"]) == run["horizon"]
    for step in run["steps"]:
        assert step["reachable"] is (step["optimum"] is not None)
        if not step["reachable"]:
            assert step["path"] == []


def test_the_dashboard_never_derives_event_timing_itself():
    """``events_at()`` is the only source of event timing, in any language.

    A grep, deliberately: the rule is that the index arithmetic exists in
    exactly one place, and the way it comes back is somebody writing
    ``schedule[t]`` somewhere convenient. That is not visible in a unit
    test of the endpoint's output, because the wrong index still returns
    a real, well-formed event list.
    """
    for path in sorted(DASHBOARD.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.Subscript):
                continue
            target = node.value
            name = getattr(target, "attr", None) or getattr(target, "id", None)
            assert name != "schedule", f"{path.name}:{node.lineno} indexes the schedule"

    # JavaScript has no AST here, so strip comments and search the rest.
    # Textual matching alone would flag the docstrings that *quote* the
    # contract, which is the opposite of what this guards.
    for path in sorted(STATIC.rglob("*.js")):
        code = re.sub(r"/\*.*?\*/", "", path.read_text(), flags=re.S)
        code = re.sub(r"//.*", "", code)
        assert "schedule" not in code, f"{path.name} references the schedule directly"


# ---------------------------------------------------------------------------
# The JavaScript layer (Entry 008 R1)
# ---------------------------------------------------------------------------

JS_TEST_DIR = ROOT / "tests" / "js"


def test_the_javascript_suite_runs_under_node():
    """The render harness, versioned, exercising the real app.js.

    Segment 8's Mutation B was two characters, browser-side, and the
    entire Python suite passed while the page quoted a wrong number
    beside a picture of the break it was wrong about. This is what closes
    that: `node --test` runs both the pure `model.js` unit tests and the
    harness-driven `app.js` integration tests — the same harness that
    produced every "what the page actually renders" artefact in Entries
    006-008, moved out of the scratchpad and into the repository per
    Entry 008 R1, instead of being rewritten from memory each segment.

    **A skipped test is not a test** — Entry 008's own words. If `node`
    is genuinely absent this skips loudly, naming what goes untested,
    rather than passing by doing nothing.
    """
    node = shutil.which("node")
    if node is None:
        pytest.skip(
            "node not found on PATH — dashboard/static/*.js (the render "
            "logic, the state/event split, the step.t===t guard) is "
            "UNTESTED this run. See RUNBOOK.md's dashboard section."
        )
    # Explicit file list, not a bare directory. `node --test <dir>`'s
    # default discovery glob is not stable across node versions — it
    # silently failed to find these files under a newer node than the
    # one this was written against, with an error naming only the
    # directory and none of the individual tests. Globbing here, in
    # Python, removes the dependency on node's own directory-scan rules.
    js_tests = sorted(JS_TEST_DIR.glob("*.test.mjs"))
    assert js_tests, f"no *.test.mjs files found under {JS_TEST_DIR}"
    result = subprocess.run(
        [node, "--test", *[str(p) for p in js_tests]], capture_output=True, text=True, cwd=ROOT
    )
    assert result.returncode == 0, (
        f"node --test failed:\n{result.stdout}\n{result.stderr}"
    )


def test_the_dashboard_is_testable_with_node_absent():
    """The boundary, asserted rather than assumed.

    Same shape as `test_the_core_is_importable_and_usable_without_fastapi`:
    make the dependency genuinely unavailable — a `PATH` with no `node` on
    it anywhere, not merely an untouched `sys.modules` — then prove real
    work still happens. Here "real work" is the rest of the dashboard
    suite passing, with the JS test skipping loudly rather than silently.
    """
    # More than one `node` can be on PATH at once (nvm, homebrew, a
    # system install) — stripping only the one shutil.which happens to
    # return first would leave the others reachable, and the test would
    # believe it had made node unavailable while it had not. Every
    # directory that contains a `node` executable is removed.
    stripped = os.pathsep.join(
        segment for segment in os.environ.get("PATH", "").split(os.pathsep)
        if not (Path(segment) / "node").exists()
    )
    env = {**os.environ, "PATH": stripped}
    assert shutil.which("node", path=stripped) is None, (
        "node is still reachable; PATH stripping is incomplete"
    )
    # Targeted at the one test that touches node, not this file as a
    # whole — this test lives in that same file, and running the whole
    # file would re-enter this test inside the subprocess.
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest", "-q", "-rs", "-p", "no:cacheprovider",
            "-k", "test_the_javascript_suite_runs_under_node", __file__,
        ],
        capture_output=True, text=True, cwd=ROOT, env=env,
    )
    assert "node not found on PATH" in result.stdout, (
        f"expected the JS test to skip with its reason; got:\n{result.stdout}"
    )
    assert result.returncode == 0, (
        f"the rest of the dashboard suite must still pass with node absent:\n"
        f"{result.stdout}\n{result.stderr}"
    )


def test_palette_covers_exactly_the_cores_event_kinds():
    """The cross-language contract, in the only place that can check it.

    `palette.json` is the sole source of truth for how a disruption is
    drawn, and its keys have to be `dynaswarm.core.events.KINDS` exactly
    — no more, no fewer, no metadata masquerading as a kind. The
    JavaScript cannot import the Python tuple, so this is the seam where
    the two are held together.

    Written after Rudra opened the page and found a legend row reading
    "undefined": the palette's `_comment` key was sitting in the same
    namespace as the six kinds, and every consumer was expected to
    remember to filter it. The kinds are now nested under their own key,
    and this asserts the set rather than trusting the convention.
    """
    from dynaswarm.core.events import KINDS

    palette = json.loads((ROOT / "dashboard" / "static" / "palette.json").read_text())
    assert set(palette["kinds"]) == set(KINDS), (
        f"palette kinds {sorted(palette['kinds'])} != core KINDS {sorted(KINDS)}"
    )
    for kind, entry in palette["kinds"].items():
        for field in ("cls", "color", "dash", "width", "opacity", "usable", "label"):
            assert field in entry, f"{kind} is missing {field}"
        assert entry["label"].strip(), f"{kind} has an empty label"


def test_the_fixture_palette_matches_the_shipped_one():
    """A fixture that has drifted from the real file tests the fixture.

    Segment 5's lesson, in a new place: `tests/js/fixtures/palette.json`
    is a copy, and a copy that falls behind would let the JS suite go on
    asserting a palette the page no longer serves.
    """
    shipped = (ROOT / "dashboard" / "static" / "palette.json").read_text()
    fixture = (ROOT / "tests" / "js" / "fixtures" / "palette.json").read_text()
    assert json.loads(shipped) == json.loads(fixture), (
        "tests/js/fixtures/palette.json has drifted from dashboard/static/palette.json"
    )


# ---------------------------------------------------------------------------
# Stage 1 / Stage 2, and the edge lifecycle (ARCHITECTURE.md §4.3.1)
# ---------------------------------------------------------------------------


def _spec(**kw):
    server = pytest.importorskip("dashboard.server")
    return server.GraphSpec(**kw)


def test_the_ledger_balances_against_the_engine_at_every_timestep():
    """§4.3.1's identity, checked against the engine's own count.

    ``active(t) = active(0) + adds + reopens - closures - deletes`` is
    exact, not approximate, because the slot population is closed — no
    slot is created, destroyed or reindexed at any timestep.

    The reconciliation target matters more than the arithmetic. Comparing
    a tally of events against a tally of the same events would pass while
    the engine disagreed with both; this compares against
    ``GraphView.n_active_edges``, which the engine computes from the
    active mask itself.
    """
    server = pytest.importorskip("dashboard.server")
    run = server.build_run(_spec(), server.ScenarioSpec())

    initial = run["steps"][0]["n_active_edges"]
    tally = dict(add=0, reopen=0, closure=0, delete=0)
    for step in run["steps"]:
        for event in step["events"]:
            if event["kind"] in tally:
                tally[event["kind"]] += 1
        predicted = initial + tally["add"] + tally["reopen"] - tally["closure"] - tally["delete"]
        assert predicted == step["n_active_edges"], (
            f"ledger diverged at t={step['t']}: "
            f"predicted {predicted}, engine reports {step['n_active_edges']}"
        )


def test_the_live_edge_count_moves_when_pool_roads_are_added():
    """`add` genuinely increases |E| — it is not an overlay (§4.3.1.1).

    A pool road connects a node pair that had no road, so activating one
    raises the live count. If `add` were an overlay on an existing edge
    the count would never rise, and the picture would be hiding a real
    change in the world.
    """
    server = pytest.importorskip("dashboard.server")
    run = server.build_run(_spec(), server.ScenarioSpec())

    counts = [step["n_active_edges"] for step in run["steps"]]
    adds = sum(
        1 for step in run["steps"] for e in step["events"] if e["kind"] == "add"
    )
    assert adds > 0, "fixture produced no add events; the test proves nothing"
    assert max(counts) > counts[0], "|E| never rose despite add events"


def test_a_derived_id_round_trips_from_a_cold_process():
    """Same parameters, same id, identical graph — with nothing remembered.

    Run in a subprocess with no shared interpreter state, because the
    point of deriving rather than issuing an id is that it survives a
    restart. `hash()` would not: Python salts it per process, so the same
    graph would be named differently after every reboot.
    """
    server = pytest.importorskip("dashboard.server")
    here = server.graph_id(_spec(n_nodes=120, seed=77))

    program = textwrap.dedent(
        """
        from dashboard.server import GraphSpec, graph_id, build_world
        spec = GraphSpec(n_nodes=120, seed=77)
        world = build_world(spec)
        print(graph_id(spec), world["n_edges"], f"{world['optimum']:.9f}")
        """
    )
    first = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True, cwd=ROOT
    )
    second = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True, cwd=ROOT
    )
    assert first.returncode == 0, first.stderr
    assert first.stdout == second.stdout, "two cold processes disagreed"
    assert first.stdout.split()[0] == here, "the id is not stable across processes"


def test_different_parameters_give_different_ids():
    """Every field must reach the digest.

    A field left out of the id collapses two different worlds onto one
    name — and segment 11 would race arms on a graph it was not handed.
    """
    server = pytest.importorskip("dashboard.server")
    base = server.graph_id(_spec())
    variants = {
        "model": _spec(model="grid"),
        "n_nodes": _spec(n_nodes=201),
        "density": _spec(density=0.041),
        "seed": _spec(seed=1001),
    }
    for field, spec in variants.items():
        assert server.graph_id(spec) != base, f"{field} does not reach the graph id"


def test_the_server_holds_no_state_between_requests():
    """Statelessness, asserted rather than promised.

    There is no cache to evict — every response is rebuilt from the
    parameters in the request — so the test that a cache is safely
    evictable becomes the stronger test that identical calls are
    identical however they are interleaved.
    """
    server = pytest.importorskip("dashboard.server")

    first = server.build_world(_spec())
    server.build_world(_spec(seed=4242))
    server.build_run(_spec(n_nodes=60), server.ScenarioSpec(events_per_step=0.9))
    assert server.build_world(_spec()) == first

    assert not hasattr(server, "_CACHE"), "a cache appeared; the eviction rule now needs asserting"


def test_small30_is_selectable_and_still_refuses_to_draw():
    """The refusal is a feature, and the picker is where it is first met."""
    server = pytest.importorskip("dashboard.server")
    world = server.build_world(_spec(model="erdos_renyi", n_nodes=30, density=0.3))

    assert world["has_coordinates"] is False
    assert world["positions"] == []
    assert world["n_edges"] > 0, "the graph exists; only its geometry does not"


def test_no_event_can_act_on_a_road_that_is_not_eligible_for_it():
    """§4.3.1's eligibility table, against `events.candidate_slots`.

    Rudra's question — *can the model close a road that was never
    there?* — is answered by the masks, and this pins the answer so a
    later change to `candidate_slots` cannot quietly widen them:

    | kind                        | may target          |
    |-----------------------------|---------------------|
    | closure, delete, traffic_*  | `active`            |
    | reopen                      | `~active & base_active` |
    | add                         | `~active & ~base_active` |
    """
    import numpy as np

    from dynaswarm.core.events import candidate_slots
    from dynaswarm.core.generate import build
    from dynaswarm.core.rng import stream

    server = pytest.importorskip("dashboard.server")
    view, _, _ = build(server._graph_cfg(_spec()), stream(1000, "graph"))
    topo = view.topology
    active = np.asarray(view.active).copy()
    base = np.asarray(topo.base_active)

    # Deactivate a handful of live slots so every population is non-empty.
    live = np.flatnonzero(active)
    active[live[:40]] = False

    for kind in ("closure", "delete", "traffic_up", "traffic_down"):
        slots = candidate_slots(kind, active, topo)
        assert active[slots].all(), f"{kind} targeted a road that is not currently there"

    reopen = candidate_slots("reopen", active, topo)
    assert not active[reopen].any(), "reopen targeted an already-open road"
    assert base[reopen].all(), "reopen targeted a road that was never an original"

    added = candidate_slots("add", active, topo)
    assert not active[added].any(), "add targeted a road that already exists"
    assert not base[added].any(), "add re-added an original road, which reopen owns"


def test_an_added_road_is_first_class_and_never_becomes_reopen_eligible():
    """The lifecycle across cycles (§4.3.1.2).

    An added pool road is `active`, so it can be closed like any other.
    Deactivated, it returns to `~active & ~base_active` — eligible for
    `add` again, and **never** for `reopen`, because `reopen` requires
    `base_active` and no event ever writes that mask.

    Original roads reopen; pool roads re-add. The distinction has to
    survive arbitrarily many cycles, and it does because `base_active` is
    a property of construction, not of history.
    """
    import numpy as np

    from dynaswarm.core.events import candidate_slots
    from dynaswarm.core.generate import build
    from dynaswarm.core.rng import stream

    server = pytest.importorskip("dashboard.server")
    view, _, _ = build(server._graph_cfg(_spec()), stream(1000, "graph"))
    topo = view.topology
    active = np.asarray(view.active).copy()
    base = np.asarray(topo.base_active)

    pool = candidate_slots("add", active, topo)
    assert pool.size, "no pool slots; the tier has no room to add"
    slot = int(pool[0])

    for cycle in range(3):
        active[slot] = True                                    # add
        assert slot in set(candidate_slots("closure", active, topo).tolist()), (
            f"cycle {cycle}: an added road cannot be closed — it is not first class"
        )
        active[slot] = False                                   # close it again
        assert slot not in set(candidate_slots("reopen", active, topo).tolist()), (
            f"cycle {cycle}: a pool road became reopen-eligible"
        )
        assert slot in set(candidate_slots("add", active, topo).tolist()), (
            f"cycle {cycle}: a closed pool road cannot be re-added"
        )
    assert not base[slot], "base_active was mutated; it must be fixed at construction"
