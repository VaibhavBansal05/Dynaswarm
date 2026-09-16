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

from dynaswarm.analysis.load import load_steps, per_trial_excess
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

#: Two ceilings, because they answer two different questions (Entry 010
#: R1). Behaviour is what deserves the tight bound; prose and presentation
#: get a ceiling so they cannot hide growth, but not the same one — the
#: control guide must not compete with the pane grid for room.
# Raised from 700 in Entry 012 R1. The 700 was set in Entry 010 from a
# 414-line file — a threshold taken from the state being left behind,
# which is the memento rule from Entry 009 broken three segments after it
# was written. 900 is derived: 702 as Phase 1 closed, plus room for
# Phase 3's allocation view and Phase 2's probe panels.
#
# Segment 13 was asked to check the derivation against evidence rather
# than an estimate. The estimate priced the allocation view at ~120 lines,
# "the excess chart's size"; the excess chart is **36**. See FINDINGS.
MAX_JS_LINES = 900
MAX_PRESENTATION_LINES = 900

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


def test_dashboard_javascript_budget():
    """*Has the dashboard become an application?*

    The tight one. Every line here is behaviour that can disagree with
    the engine, which is the risk the whole boundary exists to bound.
    See :func:`_static_lines` on why the measure is deliberately crude.
    """
    total = sum(_static_lines(p) for p in _static_files() if p.suffix == ".js")
    assert total < MAX_JS_LINES, (
        f"dashboard/static JavaScript is {total} lines, ceiling is {MAX_JS_LINES}"
    )


def test_dashboard_presentation_budget():
    """*Has its surface sprawled?*

    Markup, styling and palette data. A looser ceiling on purpose: an
    explanation that makes the instrument usable is not the same kind of
    growth as another hundred lines of logic, and charging them to one
    budget would make the guide compete with the pane grid.
    """
    total = sum(_static_lines(p) for p in _static_files() if p.suffix != ".js")
    assert total < MAX_PRESENTATION_LINES, (
        f"dashboard/static presentation is {total} lines, "
        f"ceiling is {MAX_PRESENTATION_LINES}"
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


# ---------------------------------------------------------------------------
# Stage 3: racing the arms (segment 11)
# ---------------------------------------------------------------------------


def test_the_dashboard_calls_run_trial_and_does_not_step_its_own_loop(tmp_path):
    """§15.2, asserted at the entry point rather than at the outcome.

    A dashboard that assembled the trial loop itself would be a second
    harness, and every number it showed would come from an experiment
    nobody else ran. Checking the *result* cannot tell the two apart —
    a hand-rolled loop would produce plausible rows too. So this asserts
    the door: `run_experiment` is called (the CLI's own path, cli.py:58),
    and it is what calls `run_trial` per trial.
    """
    server = pytest.importorskip("dashboard.server")

    calls = []
    real = server.run_experiment

    def spy(cfg, arm_names, directory, run_id):
        calls.append((list(arm_names), cfg.experiment.n_trials, cfg.run_class))
        return real(cfg, arm_names, directory, run_id)

    server.run_experiment = spy
    try:
        server.race(server.RaceSpec(arms=["astar", "aco"], evaluations=60), root=tmp_path)
    finally:
        server.run_experiment = real

    assert len(calls) == 1, "the dashboard did not go through run_experiment exactly once"
    arms, n_trials, run_class = calls[0]
    assert arms == ["astar", "aco"]
    assert run_class == "exploratory"

    source = (ROOT / "dashboard" / "server.py").read_text()
    assert "for trial in range" not in source, "the dashboard is stepping a trial loop"


def test_a_dashboard_run_writes_a_real_directory_stamped_exploratory(tmp_path):
    """D30/D31, exercised rather than assumed.

    Phase 0 built the provenance system; this is the first thing that
    puts a run through it. If a dashboard run landed as `manifest`, every
    scratch experiment would become evidence — the exact failure
    `run_class` exists to prevent.
    """
    server = pytest.importorskip("dashboard.server")
    started = server.race(server.RaceSpec(arms=["astar", "aco"], evaluations=60), root=tmp_path)

    directory = Path(started["path"])
    assert (directory / "steps.parquet").exists()
    assert (directory / "manifest.json").exists()

    manifest = json.loads((directory / "manifest.json").read_text())
    assert manifest["config"]["run_class"] == "exploratory"

    frame = load_steps(directory, run_class=None)
    assert set(frame["run_class"].unique()) == {"exploratory"}
    assert load_steps(directory, run_class="manifest").empty, (
        "a dashboard run is reachable under the manifest default"
    )


def test_a_dashboard_run_is_indistinguishable_from_a_cli_run(tmp_path):
    """The strong one: same schema, same columns, same dtypes.

    Not "it has the columns we remembered to check" — the comparison is
    against `StepRow`'s own fields, so a column added to the harness that
    the dashboard path silently drops fails here rather than surfacing as
    a missing series in Phase 4.
    """
    from dataclasses import fields

    from dynaswarm.harness.trial import StepRow

    server = pytest.importorskip("dashboard.server")
    started = server.race(server.RaceSpec(arms=["astar", "aco"], evaluations=60), root=tmp_path)
    frame = load_steps(started["path"], run_class=None)

    expected = {f.name for f in fields(StepRow)} | {"run_id"}
    assert expected <= set(frame.columns), (
        f"missing columns a CLI run would have: {sorted(expected - set(frame.columns))}"
    )


def test_the_excess_shown_is_the_analysis_layers_own_figure(tmp_path):
    """The anti-reimplementation test for this segment.

    The panes and the chart both quote excess. If the endpoint computed
    it — a mean over the series it is already sending, say — the number
    would look right and would be a second answer to a question
    `analysis/` already answers. This compares against
    `per_trial_excess`, called independently here.
    """
    server = pytest.importorskip("dashboard.server")
    started = server.race(
        server.RaceSpec(arms=["astar", "aco", "pso"], evaluations=80), root=tmp_path
    )
    back = server.read_run(started["run_id"], root=tmp_path)

    frame = load_steps(started["path"], run_class=None)
    trials = per_trial_excess(frame)
    for arm in back["arms"]:
        expected = trials[trials["arm"] == arm["id"]]["mean_excess"].iloc[0]
        assert arm["mean_excess"] == pytest.approx(float(expected)), arm["id"]


def test_every_arm_sees_the_identical_timeline(tmp_path):
    """§10's fairness guarantee, asserted from the dashboard's side.

    Every arm must face byte-identical conditions or the comparison means
    nothing. Checked through the columns that describe the world rather
    than the arm: same `num_events` sequence, same `optimum` sequence.
    """
    server = pytest.importorskip("dashboard.server")
    started = server.race(server.RaceSpec(evaluations=80), root=tmp_path)
    frame = load_steps(started["path"], run_class=None)

    reference = None
    for arm, rows in frame.groupby("arm"):
        rows = rows.sort_values("timestep")
        world = list(zip(rows["num_events"], rows["optimum"], strict=True))
        if reference is None:
            reference = world
        assert world == reference, f"{arm} saw a different world"


def test_every_raceable_controlled_arm_demonstrably_does_what_it_claims():
    """Replaces the blanket ban that stood here while F7 was open.

    The old test asserted that no controlled arm was reachable at all,
    because `PrescheduledController` was built with no arguments and so
    varied nothing while logging itself active. Segment 20 deleted that
    class and segment 21 replaced it with the allocation layer, so the
    ban's premise is gone.

    **The ban is not simply lifted, it is replaced by the condition that
    justified it.** What made a controlled arm dangerous on screen was
    never that it was controlled; it was that nobody could tell whether
    the control did anything, and a flat line presented as the project's
    novelty looks exactly like a working one. So the bar for being
    raceable is now: run the arm and watch the split. Frozen must not
    move, adaptive must, scheduled must move without being disrupted.
    """
    server = pytest.importorskip("dashboard.server")
    from dynaswarm.harness.arm import ARM_BUILDERS

    controlled = {k for k in ARM_BUILDERS if k.endswith(("_fixed", "_adaptive", "_scheduled"))}
    assert controlled, "no controlled arms found; this test is checking nothing"

    unknown = set(server.RACEABLE) - set(ARM_BUILDERS)
    assert not unknown, f"the dashboard offers arms the harness cannot build: {unknown}"

    for arm in sorted(set(server.RACEABLE) & controlled):
        with pytest.raises(ValueError, match="not raceable"):
            server.race_config(server.RaceSpec(arms=[f"{arm}_nonexistent"]))

    markup = (ROOT / "dashboard" / "static" / "index.html").read_text()
    for arm in sorted(ARM_BUILDERS):
        assert arm not in markup, (
            f"{arm} is hard-coded in the markup — the arm list is served "
            f"from /api/arms so there is one copy of it, and a literal here "
            f"is the second copy coming back"
        )


@pytest.mark.parametrize(
    ("arm", "must_move"),
    [("hybrid_fixed", False), ("hybrid_adaptive", True), ("hybrid_scheduled", True)],
)
def test_a_raceable_controlled_arm_moves_its_split_or_provably_does_not(
    arm, must_move, tmp_path
):
    """The condition above, measured per arm through the real endpoint.

    `hybrid_fixed` is the ablation twin: it must be pinned. The other two
    must vary, or they are the ablation twin wearing a different name —
    which is precisely the result that would look strongest and mean
    least.
    """
    server = pytest.importorskip("dashboard.server")
    started = server.race(
        server.RaceSpec(
            arms=[arm], evaluations=120,
            # Nested, because `RaceSpec` now refuses unknown keys. Written
            # flat first, where it was silently dropped and this test ran
            # 60 steps while saying 25 — the guard caught it on the spot.
            scenario=server.ScenarioSpec(timesteps=25),
        ),
        root=tmp_path,
    )
    frame = load_steps(started["path"], run_class=None)
    fractions = {
        value for probe in frame["probe"] if probe is not None
        for key, value in probe if key == "aco_fraction"
    }
    assert fractions, f"{arm} did not record aco_fraction at all"
    if must_move:
        assert len(fractions) > 1, (
            f"{arm} is offered as a controlled arm but held its split at "
            f"{fractions} for the whole run — it is the frozen arm under "
            f"another name, and the dashboard would present it as the thesis"
        )
    else:
        assert len(fractions) == 1, (
            f"{arm} is the ablation twin and must not move; it took "
            f"{sorted(fractions)}"
        )


def test_a_run_id_names_a_directory_and_survives_a_restart(tmp_path):
    """The two id kinds, pinned.

    A graph is a pure function of its parameters, so its id is derived and
    needs no process at all. A run is an artefact with a location, so its
    id names a directory — and is still there after the process that made
    it is gone. Conflating them is how a stateless server grows a session.
    """
    server = pytest.importorskip("dashboard.server")
    started = server.race(server.RaceSpec(arms=["astar"], evaluations=60), root=tmp_path)

    program = textwrap.dedent(f"""
        from dashboard.server import read_run, graph_id, GraphSpec
        back = read_run({started["run_id"]!r}, root={str(tmp_path)!r})
        print(back["run_id"], back["run_class"], len(back["arms"]))
        print(graph_id(GraphSpec()))
        """)
    done = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True, cwd=ROOT
    )
    assert done.returncode == 0, done.stderr
    run_line, graph_line = done.stdout.strip().splitlines()
    assert run_line.split()[0] == started["run_id"]
    assert run_line.split()[1] == "exploratory"
    assert graph_line.strip() == server.graph_id(server.GraphSpec())


def test_no_panel_shows_a_field_the_run_does_not_record(tmp_path):
    """§15.6 asks for two fields the run does not carry, and they are out.

    Per-edge pheromone level and per-node PSO priority statistics are
    Layer 2 probes; §17 assigns those to Phase 2. What `probe` carries
    today is colony- and swarm-level: `tau_ratio` and `diversity` are
    aggregates over the whole colony and swarm, not per edge or per node.

    A panel showing a plausible-looking number nobody can trace is worse
    than a panel with a gap, so this pins the absence: the moment the
    probes land, this test fails and the panels can be extended
    deliberately rather than by someone noticing.
    """
    server = pytest.importorskip("dashboard.server")
    started = server.race(server.RaceSpec(evaluations=80), root=tmp_path)
    frame = load_steps(started["path"], run_class=None)

    keys = set()
    for probe in frame["probe"]:
        if probe is not None:
            keys |= {k for k, _ in probe}
    assert not {"pheromone", "priority"} & keys, (
        "the Layer 2 probes have landed — the inspect panels can now show them"
    )

    # Comments stripped first. The same textual grep flagged this file's
    # own explanation of why the field is absent — segment 9's lesson,
    # which I re-learned here rather than remembered.
    markup = (ROOT / "dashboard" / "static" / "index.html").read_text()
    app = (ROOT / "dashboard" / "static" / "app.js").read_text()
    app = re.sub(r"/\*.*?\*/", "", app, flags=re.S)
    app = re.sub(r"//.*", "", app)
    markup = re.sub(r"<!--.*?-->", "", markup, flags=re.S)
    for absent in ("pheromone", "priority"):
        assert absent not in markup.lower(), f"the page offers {absent}, which is not recorded"
        assert absent not in app.lower(), f"app.js reads {absent}, which is not recorded"


def test_the_allocation_view_is_a_labelled_gap_not_a_drawing(tmp_path):
    """Plain `hybrid` holds one split all run, and that is why.

    **The reason in this docstring was wrong until segment X.** It said
    the fraction was pinned because "F7 leaves the prescheduled
    controller built with no arguments" — but F7 was closed in segment 20
    and the class deleted, so the docstring was telling its next reader
    that a closed defect was live. The assertion it guards was still
    correct, for a different reason, which is the worst case: right
    answer, retired explanation, no failure anywhere. Same family as
    `model.js` claiming a test that never existed.

    **The true reason:** `hybrid` is the plain baseline. It carries no
    signal, no controller and no governor (§9), so nothing in the system
    is able to move its `aco_fraction`. It is not a controlled arm whose
    controller is broken; it is an arm with no allocation machinery at
    all, and its flat line is the correct output rather than a symptom.

    That distinction is the whole point of keeping it: `hybrid` pinned at
    one value is the floor against which `hybrid_adaptive` moving is
    evidence. If this ever fails, an arm that is supposed to have no
    allocation policy has acquired one.
    """
    server = pytest.importorskip("dashboard.server")
    started = server.race(server.RaceSpec(arms=["hybrid"], evaluations=120), root=tmp_path)
    frame = load_steps(started["path"], run_class=None)

    fractions = {
        value for probe in frame["probe"] if probe is not None
        for key, value in probe if key == "aco_fraction"
    }
    assert fractions, "hybrid did not record aco_fraction at all"
    assert len(fractions) == 1, (
        f"plain `hybrid` moved its split ({sorted(fractions)}). It has no "
        f"signal, controller or governor, so nothing should be able to — "
        f"either it has been given allocation machinery it must not have, "
        f"or a governed arm's state is leaking into it"
    )

    # The view's own correctness is NOT asserted here any more. This used
    # to end with `assert "arm.allocation.searched[t]" in app` — a
    # substring search of app.js, which passes on a comment, on dead code,
    # or on a function nobody calls. It now lives in tests/js/app.test.mjs
    # as a render assertion that drives the real page and reads the width
    # the bar actually draws ("the allocation bar, rendered"), and it was
    # shown failing with `applied` substituted for `searched`.
    markup = (ROOT / "dashboard" / "static" / "index.html").read_text()
    assert "alloc-body" in markup, "the allocation view is gone from the markup"


# ---------------------------------------------------------------------------
# The arm palette (segment 21)
# ---------------------------------------------------------------------------
#
# `model.js` used to hold these colours and to claim, in a comment, that
# their spread was "checked in tests/js/model.test.mjs, not assumed". No
# such test existed — `luminance` was exported and never called by one, and
# the sentence described an intention. It cost nothing until this segment
# made three more arms raceable with no colours at all, which put three
# identical grey lines on the excess chart. That chart is Claim 1's
# evidence, and nothing anywhere failed to say it had stopped being legible.


def test_every_raceable_arm_has_its_own_colour():
    """A missing entry is invisible: it falls through to a grey default.

    Reads RACEABLE rather than a list retyped here, because a second copy
    of the arm list is the defect this whole area keeps producing.
    """
    from dashboard.server import ARM_COLORS, RACEABLE

    missing = [a for a in RACEABLE if a not in ARM_COLORS]
    assert not missing, (
        f"raceable arms with no colour: {missing} — they draw in the #888 "
        f"fallback, indistinguishable from each other and from any other "
        f"arm that is also missing one"
    )
    assert len(set(ARM_COLORS.values())) == len(ARM_COLORS), "two arms share a colour"


def test_arm_colours_stay_distinguishable_in_greyscale():
    """Hue is not available in a printed report; luminance is.

    The floor is a measured property of the current palette, not a wish:
    four arms left about 0.2 between neighbours and seven leave 0.07, and
    that is the honest cost of the arms this segment added.
    """
    from dashboard.server import ARM_COLORS, MIN_ARM_LUMINANCE_GAP, arm_luminance

    ranked = sorted(
        ((arm_luminance(c), a) for a, c in ARM_COLORS.items()), reverse=True
    )
    for (bright, upper), (dim, lower) in zip(ranked, ranked[1:], strict=False):
        assert bright - dim >= MIN_ARM_LUMINANCE_GAP, (
            f"{upper} ({bright:.3f}) and {lower} ({dim:.3f}) are "
            f"{bright - dim:.4f} apart, under the {MIN_ARM_LUMINANCE_GAP} "
            f"floor — one line, the moment the chart is printed in black "
            f"and white"
        )
    assert ranked[0][0] - ranked[-1][0] > 0.5, (
        "every arm is about as bright as every other; the spread is what "
        "makes the greyscale guarantee mean anything"
    )


# ---------------------------------------------------------------------------
# The seed box must reach the race (segment X, T4 exercise 3)
# ---------------------------------------------------------------------------
#
# WALKTHROUGH Part 10 exercise 3 says a different seed gives "completely
# different map, completely different breaks, different numbers throughout".
# It did not. Every race ran on the same world whatever was typed, because
# `race_config` never passed the seed anywhere the graph build could see it
# — `trial.py:135` builds from the per-trial eval seed, and that was left at
# its default. The page's own reference card promises "One seed, one run."


def test_the_dashboard_seed_actually_changes_the_raced_world(tmp_path):
    """Two seeds must give two worlds, in the numbers and not just the map.

    Asserted on `optimum`, which is A*'s exact answer for the world the
    arms actually ran on. A graph id that differs proves only that the id
    is a function of the seed; `optimum` differing proves the search saw a
    different graph.
    """
    server = pytest.importorskip("dashboard.server")

    def raced_optimum(seed: int) -> float:
        started = server.race(
            server.RaceSpec(
                arms=["astar"], evaluations=120,
                graph=server.GraphSpec(seed=seed),
                scenario=server.ScenarioSpec(events_per_step=0.0, timesteps=4),
            ),
            root=tmp_path,
        )
        frame = load_steps(started["path"], run_class=None)
        return float(frame["optimum"].iloc[0])

    first, second = raced_optimum(1000), raced_optimum(2024)
    assert first != second, (
        f"seeds 1000 and 2024 both raced a world with optimum {first} — the "
        f"seed control does not reach the race, so every run on the "
        f"dashboard is the same world with a different label"
    )
    assert raced_optimum(1000) == first, "the same seed gave two worlds"


def test_the_reported_graph_id_names_the_world_that_was_raced(tmp_path):
    """Provenance that is confidently wrong is worse than none.

    `graph_id` was derived from `root_seed` while the graph was built from
    the eval seed — 42 against 1000 at the defaults. The caption printed
    it beside a correct `seed` field, so the two halves of one provenance
    line disagreed and neither looked wrong on its own.
    """
    server = pytest.importorskip("dashboard.server")

    started = server.race(
        server.RaceSpec(
            arms=["astar"], evaluations=120,
            graph=server.GraphSpec(seed=1000),
            scenario=server.ScenarioSpec(events_per_step=0.0, timesteps=4),
        ),
        root=tmp_path,
    )
    payload = server.read_run(started["run_id"], root=tmp_path)
    displayed = server.build_world(server.GraphSpec(seed=1000))

    assert payload["graph_id"] == displayed["graph_id"], (
        f"the run reports graph {payload['graph_id']} but the world built "
        f"from the same seed is {displayed['graph_id']} — the caption names "
        f"a graph nobody raced"
    )
    assert payload["seed"] == 1000, "the recorded seed is not the one asked for"


def test_a_field_the_api_does_not_know_is_refused_not_dropped():
    """The HTTP boundary must not accept a request it will not honour.

    Pydantic drops unknown keys by default. That is the silent-drop
    pattern this project has already closed twice in Python (F2 and F6,
    where a controller ignored an unknown target), and it is **worse
    here**: a browser posts JSON, so a typo or a field at the wrong
    nesting level runs a different experiment and returns a perfectly
    well-formed result with a run id.

    Found the hard way in segment X: `RaceSpec(seed=2024)` — where `seed`
    belongs under `graph` — was accepted, the race ran the default world,
    and exercise 3 was reported as a system defect before the request was
    re-read. Forbidding extras would have said so on the first call.
    """
    import pydantic

    server = pytest.importorskip("dashboard.server")

    misplaced = [
        ("RaceSpec", {"seed": 2024}),            # belongs under `graph`
        ("RaceSpec", {"events_per_step": 0.0}),  # belongs under `scenario`
        ("RaceSpec", {"nonsense": 1}),
        ("GraphSpec", {"sead": 1000}),           # a plain typo
        ("ScenarioSpec", {"events": 0.3}),
    ]
    for name, payload in misplaced:
        model = getattr(server, name)
        with pytest.raises(pydantic.ValidationError, match="[Ee]xtra"):
            model(**payload)

    # And the shapes the page actually sends still validate, or the guard
    # has been bought by breaking the dashboard.
    spec = server.RaceSpec(
        graph=server.GraphSpec(
            model="geometric", n_nodes=120, density=0.04, seed=2024
        ),
        scenario=server.ScenarioSpec(
            events_per_step=0.3, cluster_size=25, timesteps=8,
            p_closure=0.15, p_traffic_up=0.30, p_traffic_down=0.20,
            p_reopen=0.10, p_delete=0.10, p_add=0.15, traffic_factor=2.0,
        ),
        arms=["astar", "aco"], evaluations=150,
    )
    assert spec.graph.seed == 2024
    assert spec.scenario.timesteps == 8
