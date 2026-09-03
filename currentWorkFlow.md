# SEGMENT 6 — Dashboard Scaffold

**Phase 1 · See it · Segment 1 of 5**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` §15 (the dashboard specification) and §2.3 (structural rules), and `decisionLedger.md` D14–D17, D30, D32. `WORKFLOW_LOG.md` Entries 001–005 record Phases 0 and 0.5.
> Append your findings to the **bottom** of this file. Do not modify the spec text above it.

---

## Goal

Stand up the dashboard's skeleton and **prove the pipe works end to end** — a browser page displaying data that came from the real `dynaswarm` engine, not a fixture and not a reimplementation.

Nothing is drawn in this segment. No graph rendering, no timeline, no arms. Those are segments 2–5. **This segment proves that a page can ask the engine a question and get a true answer back**, and establishes the structural boundaries that keep the dashboard a view rather than a second engine.

## Why a scaffold segment at all

Because the failure this project is guarding against is a second implementation that quietly disagrees with the first. `ARCHITECTURE.md` §2.3 states it as the one rule above all others, and the reason is in the repository's own history: v1 died of instrumentation that looked fine and wasn't.

If the boundary is established and tested **before** any drawing code exists, it cannot be eroded later by someone in a hurry. If it is established afterwards, it will not be.

---

## ⚠️ T0 — MEASURE, but a different measurement this time

The **science surface** (`src/`) is at **2005 / 2100**. This segment should add **zero** statements to it — the dashboard lives outside `src/` entirely (D14).

**Report both:**

1. `src/` count before and after. **If this segment changes it at all, say why.** A scaffold that needs to touch the science surface is a design problem, not a measurement problem — stop and report rather than proceeding.
2. The **dashboard's own** statement count, against its cap of **1000** (`ARCHITECTURE.md` §2.3). Report the number you land on and how much headroom the remaining four segments have.

**One thing to verify rather than assume:** `test_hygiene`'s `FORBIDDEN_IMPORTS` scan currently covers `src/`. Confirm it does **not** reach `dashboard/`, so importing FastAPI there is legal without touching that test. If it does reach it, **stop and report** — that changes the design, and D14 exists precisely because of that scan.

---

## Scope

**In scope**
- `dashboard/` — new, at the **repo root**, outside `src/`
- `pyproject.toml` — a `dashboard` optional-dependency group
- `tests/` — the boundary tests and the dashboard statement cap
- `.gitignore` — only if the dashboard needs it
- One local commit

**Out of scope**
- **Anything under `src/`.** If the dashboard needs something the core does not expose, **stop and report** — per §2.3 the core exposes it, but that is a decision, not something to improvise
- Drawing anything: graphs, timelines, arms, charts — segments 2–5
- `viz/replay.py` — it is retired *later*, when the dashboard covers it (D17). Leave it alone
- Defects F4, F7, F8 — Phase 3
- `git push`

---

## Tasks

### T1 — Authorise and declare the dependencies

`fastapi` and `uvicorn`, as a **dashboard-only optional group** in `pyproject.toml` — not core dependencies. `dynaswarm` must remain installable and fully testable without them.

**Explicitly authorised by this segment.** Nothing else. No Streamlit, no Dash, no JS framework, no bundler, no build step.

### T2 — The package, and the boundary that defines it

Create `dashboard/` at the repo root:

```
dashboard/
  __init__.py
  server.py          FastAPI app
  static/
    index.html
    app.js
    style.css
```

**The boundary, stated as code rather than convention:**

- `dashboard/` imports `dynaswarm` as a library
- **`dynaswarm` never imports `dashboard`** — not in any module, not conditionally, not inside a function

This is what makes "view, never an engine" structural. A convention would be a comment; this is a direction of dependency that cannot be violated without the import failing.

### T3 — One endpoint that proves the pipe

A single endpoint — `GET /api/graph` — that builds a graph **through the real core** and returns a description of it.

It must call `dynaswarm.core.generate.build()` with a real `GraphCfg` and a real seeded RNG from `core.rng.stream()`. It must **not** construct nodes, edges, weights or coordinates itself.

Return enough to prove the answer is genuine and not a plausible-looking stub:

| Field | Why |
|---|---|
| `n_nodes`, `n_edges` | basic shape |
| `source`, `target` | chosen by the real `_endpoints()`, not picked arbitrarily |
| `optimum_at_t0` | the true shortest-path cost from `core.oracle` — **a number nothing but the real engine could produce** |
| `has_coordinates` | true for geometric and grid, false for Erdős–Rényi |

That last one matters: it is the fact that made the original replay useless, and the dashboard needs to know it from the start.

**Defaults:** `medium200`, the research tier. **Not `small30`** — that tier has no coordinates, and every visual built on it is meaningless (D8, and the reason Rudra saw spaghetti the first time he ran the project).

### T4 — A page that displays it

`index.html` plus a small `app.js` that fetches `/api/graph` and renders the returned fields **as text**. A definition list or a table. No canvas, no SVG, no drawing.

The page must show, visibly:

- the values from T3
- **which run classes exist in `outputs/`**, obtained through `load_steps(..., run_class=None)` — and here is why that is in the scaffold: **every dashboard-created run is `exploratory` by design** (D30), so the page must prove from day one that it can see them. A dashboard that filtered to `manifest` would show a blank screen for every run it ever made.

**And one warning, rendered on the page itself:** the five runs predating F1's fix carry a permanently misaligned `num_events` column (D32). Any disruption timing drawn from them will be one step early. This is a Phase 1 problem, not a Phase 4 one — segment 3 will draw those markers. Put the warning in now, where whoever builds segment 3 cannot miss it.

### T5 — Make it runnable, and document the one command

A single documented command that starts the server. Add it to `RUNBOOK.md` under a new short section — the dashboard is a tool people will run, and a tool nobody can start is not a tool.

State the port explicitly, and that it is a **local development server**: not hosted, not exposed, not deployed. The synopsis lists web deployment as out of scope (O1) and this is a local tool, which is the distinction that keeps it inside scope.

### T6 — The tests that hold the boundary

| Test | What it protects |
|---|---|
| **`dynaswarm` never imports `dashboard`** | Walk every module under `src/` and assert it. The rule of §2.3, enforced rather than trusted |
| **`dashboard/` statement count ≤ 1000** | Mirror `test_statement_budget`, scoped to `dashboard/`. **Use the existing counter, do not reimplement it** — a second counter that disagrees is the same class of bug as a second engine |
| **The core is importable and testable without FastAPI** | If `fastapi` is absent, `import dynaswarm` and the whole suite still work |
| **`/api/graph` returns the same values as calling the core directly** | The endpoint's `optimum_at_t0` must equal what `core.oracle` returns for the same config and seed. **This is the anti-reimplementation test** — it would fail the moment someone computed anything in the dashboard instead of asking for it |

That last test is the important one. Write it so it would catch a plausible reimplementation, not merely a missing endpoint.

### T7 — Show it working

Start the server, open the page, and **paste what it actually displays.** Not a description of what it should display.

If you cannot open a browser, `curl` the endpoint and paste the JSON, plus the rendered HTML the page would build from it.

### T8 — Commit

Whole tree. **Do not push.**

```
segment 6: dashboard scaffold (phase 1)

Creates dashboard/ at the repo root, outside src/, importing dynaswarm as
a library. Adds fastapi and uvicorn as a dashboard-only optional group;
the core remains installable and testable without them.

One endpoint, /api/graph, builds a graph through core.generate.build()
and returns its shape plus the true optimum from core.oracle — a value
nothing but the real engine could produce. A page renders those fields as
text. Nothing is drawn yet.

Four tests hold the boundary: dynaswarm never imports dashboard, the
dashboard has its own 1000-statement cap, the core is importable without
FastAPI, and the endpoint's optimum matches the core's directly — the
test that would catch a reimplementation rather than a missing route.

The page surfaces the run classes present in outputs/ and warns that runs
predating F1 carry a misaligned num_events column (D32), because segment
3 draws those markers.

Spec + findings: currentWorkFlow.md
Log: WORKFLOW_LOG.md entry 006
```

---

## Constraints

| | |
|---|---|
| **Zero statements added to `src/`** | If the scaffold seems to need one, stop and report — that is a design decision |
| **The dashboard computes nothing** | Every value it shows is asked of the core. Not "mostly", not "except for display" |
| **No drawing** | Segments 2–5. Resist it |
| **No new dependency beyond fastapi and uvicorn** | |
| **Default to `medium200`** | `small30` has no coordinates and every visual on it is meaningless |
| **Do not touch `viz/replay.py`** | It retires when the dashboard covers it, which is not yet |
| **Use the existing statement counter** | Do not write a second one |
| **Do not push** | |

---

## Acceptance check

```bash
# 1a. In scope
git diff --stat -- dashboard/ tests/ pyproject.toml RUNBOOK.md
# 1b. The science surface is untouched
git diff --stat -- src/                       # expect EMPTY

# 2. Suite
./.venv/bin/pytest -q -m "not slow"

# 3. Lint
./.venv/bin/ruff check src/ tests/ dashboard/

# 4. Both budgets — report both numbers
./.venv/bin/pytest -q -k "statement" -s

# 5. The core does not depend on the dashboard
python -c "import dynaswarm; print('core imports clean')"

# 6. The boundary holds
./.venv/bin/pytest -q -k "imports_dashboard or boundary" -v

# 7. It actually runs
<the T5 command>, then: curl -s localhost:<port>/api/graph

# 8. Committed, not pushed
git log --oneline -2
git status --short --branch | head -1
```

**Expected:** `src/` diff **empty** · all tests pass including the four new · lint clean across three trees · both counts reported · core imports without FastAPI · boundary tests pass by name · the endpoint returns real values · commit on top, ahead 1, unpushed.

**Paste verbatim:**

1. **Both T0 measurements** — `src/` before and after, and the dashboard's count against 1000 with remaining headroom
2. **Whether `FORBIDDEN_IMPORTS` reaches `dashboard/`** — verified, not assumed
3. **The raw JSON** from `/api/graph`
4. **What the page actually displays** — the rendered content, not a description of it
5. **The anti-reimplementation test** — its code, and the values it compared

---

## Definition of done

All eight checks pass, five artefacts pasted, commit exists unpushed, FINDINGS appended.

**After this, Rudra can start the dashboard and see real numbers from the real engine in a browser.** Segment 7 draws the first graph.

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->

---

# FINDINGS — Segment 6

## 0. The interrupted state, and how it was restored

The session ended mid-mutation: `dashboard/server.py:97` was left reading
`heuristic=False`, a deliberate mutation to prove the anti-reimplementation
test bites. It bit — `assert 200 == 75`.

I did not restore by editing the line back. The scratchpad copy survived, so
I first **proved it was the right file** before trusting it:

```
$ diff <(sed 's/heuristic=False/heuristic=True/' dashboard/server.py) $S/server.good.py
(no output)
```

The mutated file with the flag flipped back is byte-identical to the saved
copy — so the saved copy contains that one difference and nothing else, and
restoring from it cannot have smuggled in anything I had forgotten. Then:

```
$ ./.venv/bin/pytest tests/test_dashboard.py
8 passed in 2.57s
```

`git diff dashboard/server.py` is empty and always would be: `dashboard/` is
untracked in this segment, so git has no baseline to compare against. That
is why the diff above is against the scratchpad rather than against git —
the check the Architect asked for could not have been meaningful as stated,
and saying so is better than pasting an empty diff as if it proved something.

## 1. T0 — three measurements

```
SCIENCE SURFACE
  src/ before : 2005 / 2100
  src/ after  : 2005 / 2100     delta +0

DASHBOARD, against its own 1000 cap
  dashboard/__init__.py     0
  dashboard/server.py      45
  TOTAL                    45 / 1000    headroom 955
```

**`src/` did not move, and nothing was needed from it.** The core already
exposed everything the scaffold asks for — `build()`, `shortest_path()`,
`stream()`, `load_steps()` — which is worth recording as a *result* rather
than an absence: §2.3 says the core exposes what the dashboard needs, and
this segment is the first evidence that it already does.

**955 statements for segments 7–10.** For scale, the entire retiring
`viz/replay.py` is 158, and it does the graph-drawing job segment 7 inherits.
Four segments at replay's size would be ~630. The cap is not close.

## 2. Does `FORBIDDEN_IMPORTS` reach `dashboard/`? — verified two ways

**Structurally.** The scan is rooted at `src/dynaswarm`, not the repo root:

```
scan root            : src/dynaswarm
files enumerated     : 37
any outside that root: none
dashboard/__init__.py enumerated? False
dashboard/server.py   enumerated? False
FORBIDDEN_IMPORTS    : ['fastapi', 'flask', 'starlette', 'tkinter', 'uvicorn']
```

`test_statement_budget` uses the same `_python_files()`, so the dashboard's
45 statements do not count against `src/`'s 2100 either.

**Behaviourally — because "it is not scanned" only matters if the scan would
otherwise reject it.** Running `FORBIDDEN_IMPORTS`' own logic over
`dashboard/server.py` by hand:

```
If dashboard/server.py were inside the scan, it would fail on:
    line 21: fastapi
    line 22: fastapi.responses
    line 23: fastapi.staticfiles
    line 170: uvicorn
```

Four hits, one of them a **function-level** `import uvicorn` inside `main()`
that the `ast.walk` scan would still catch. So D14 is load-bearing, not
decorative: the placement is precisely what makes this code legal, and moving
`dashboard/` under `src/` would break the build in four places rather than
silently degrade. `test_dashboard_is_outside_the_science_surface` pins it.

**No change to `test_hygiene.py` was needed.** The design holds as ruled.

## 3. Raw JSON from the running server

```
$ ./.venv/bin/python -m dashboard.server
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)

$ curl -s localhost:8000/api/graph
{
    "tier": "medium200",
    "model": "geometric",
    "seed": 1000,
    "n_nodes": 200,
    "n_edges": 735,
    "source": 0,
    "target": 2,
    "optimum_at_t0": 99.96328976797456,
    "hops": 11,
    "expansions": 75,
    "has_coordinates": true
}

$ curl -s localhost:8000/api/runs
{
    "run_classes": {"exploratory": 9240},
    "warning": "Every run currently in outputs/ predates the F1 fix: ..."
}
```

**`source: 0, target: 2` looks like a placeholder and is not.** `_endpoints()`
fixes `source = 0` by construction and takes the *most distant reachable*
node as the target; on this graph that is node 2. I checked, because a
scaffold returning `0` and `2` is exactly what a stub would return, and I
would rather confirm it than have it asked in a viva.

**`run_classes` shows `exploratory: 9240` and no `manifest` key** — D31's
reclassification, visible from the outside for the first time. A dashboard
that had filtered to `manifest` would render an empty screen here, on every
run that exists.

## 4. What the page actually displays

Not a description of it. I executed the real `dashboard/static/app.js` under
node, against the live server, with the minimum DOM that file touches, and
printed the resulting nodes:

```
PAGE AS RENDERED  ——  http://127.0.0.1:8000

Dynaswarm
Phase 1 · segment 6 — scaffold. Nothing is drawn yet.
These values came from the engine, not from this page.

GRAPH AT T=0
  tier               medium200
  model              geometric
  seed               1000
  n_nodes            200
  n_edges            735
  source             0
  target             2
  optimum_at_t0      99.96328976797456
  hops               11
  expansions         75
  has_coordinates    true

RUNS ON DISK
  exploratory        9240

  ⚠ Every run currently in outputs/ predates the F1 fix: its num_events
    column is off by one, so any disruption timing drawn from these runs is
    one step early (D32). Quality columns (excess, optimum, best_cost) are
    sound. Phase 4 regenerates everything.

Local development server. Not hosted, not exposed, not deployed.
```

The harness lives in the scratchpad, not the repo — it is a way of reading
the page, not a dependency. An earlier attempt at it failed with
`Failed to parse URL from /api/graph` (node's `fetch` has no page origin to
resolve against), which incidentally exercised `app.js`'s error path and
confirmed a failed fetch renders as a visible `error` row rather than a blank
panel.

## 5. The anti-reimplementation test — code, values, and the mutation

```python
def test_endpoint_returns_exactly_what_the_core_returns():
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
```

Values compared, both sides: `source 0`, `target 2`,
`optimum_at_t0 99.96328976797456`, `expansions 75`, `hops 11`,
`n_nodes 200`, `n_edges 735`.

**Why `expansions` is the field that does the work.** `optimum_at_t0` is a
property of the *graph* — a competent reimplementation can arrive at it, and
on a well-conditioned instance it may even match bit-for-bit. `expansions` is
not a property of the graph at all. It counts the nodes *this* A\* popped, so
it depends on the heuristic, the tie-break order and the heap discipline.
Nothing that computed the answer independently reproduces it by luck.

**Proved, not argued.** I mutated the dashboard into the most plausible
reimplementation available — the same core function, the same correct answer,
a different search:

```python
-    optimum, path, expansions = shortest_path(view, source, target, heuristic=True)
+    optimum, path, expansions = shortest_path(view, source, target, heuristic=False)
```

```
E       AssertionError: expansion count differs — the dashboard is running its own search
E       assert 200 == 75
```

The optimum assertion **passed** — the answer was still exactly right. Only
the expansion count caught it. A test written on `optimum_at_t0` alone would
have waved this through, and that is the whole finding: *the correct number
arriving from the wrong place is the failure mode this project has already
died of once, and equality on the answer does not detect it.*

Three further tests close the holes that one leaves: a constant stub
(two seeds must differ), a hardcoded `has_coordinates` (`medium200` true,
`small30` false), and a `manifest`-filtered run listing.

## 6. Acceptance — all eight

| # | Check | Result |
|---|---|---|
| 1a | In scope | 8 files, +575 — `dashboard/` (5), `tests/test_dashboard.py`, `pyproject.toml`, `RUNBOOK.md` |
| 1b | `git diff --stat -- src/` | **Empty** |
| 2 | Suite | **329 passed** full · **324 passed, 5 deselected** `-m "not slow"` |
| 3 | Lint, three trees | `All checks passed!` |
| 4 | Both budgets | 2 passed — `src/` 2005/2100, `dashboard/` 45/1000 |
| 5 | Core without dashboard | `core imports clean` |
| 6 | Boundary by name | 2 passed |
| 7 | It runs | Server up on 127.0.0.1:8000; JSON and page above |
| 8 | Committed, not pushed | Below |

Counts qualified per Entry 005's convention: **329 full / 324 not-slow**,
up from 321 / 316, i.e. **+8**, all in `tests/test_dashboard.py`.

## Deviations from spec

**1. `/api/runs` as a second endpoint.** T3 says "a single endpoint", but T4
requires the page to show run classes and the D32 warning, which needs data
from somewhere. I read "single endpoint" as scoped to T3's purpose — proving
the pipe — rather than a cap on the app, and kept `/api/graph` exactly as
specified rather than overloading it with unrelated payload. Chosen, not
drifted.

**2. `expansions`, `hops`, `tier`, `model` returned beyond the specified
fields.** `expansions` is the one that matters and §5 explains why; without
it the anti-reimplementation test would not have caught the mutation. The
other three are free context that makes the page legible.

**3. The tier is read from the config store, not restated.**

```python
    register()
    node = ConfigStore.instance().repo["graph"][f"{name}.yaml"].node
    return OmegaConf.to_object(node)
```

`cross_evaluate.py` sets the precedent for restating it as
`GraphCfg(model="geometric", n_nodes=200, density=0.04)`, and that works
until someone edits the registration, at which point the dashboard silently
draws a tier that no longer exists under that name. Reading it back makes
divergence impossible instead of merely unlikely. The cost is a dependency on
a Hydra internal (`ConfigStore.repo`) — but it fails **loudly at startup** if
Hydra changes, where the restated constant fails silently and forever.

## Surprises

**The core needed nothing added.** I expected at least one "the dashboard
needs X and `src/` does not expose it — stop and report". Nothing came up.
Every value on the page was already reachable through a public function.

**`pyproject.toml` packages only `src`,** so `dashboard/` is not installed
with the library at all — a second structural guarantee under D14 that I did
not expect and did not have to build. It is a repository tool, not a shipped
component, and `pip install dynaswarm` cannot drag a web framework along.

**`RUNBOOK.md:27` is stale again** — it reads `~60 s, 271 not-slow tests`;
the true figure is **324**, and the wall-clock is ~36 s. Segment 1 corrected
this exact line and it has gone stale three times since, because it goes
stale every time anyone adds a test. **Not fixed** — it is outside T5's named
task, and a number that rots on every segment probably wants deleting rather
than re-correcting, which is a decision rather than a typo fix.

## Could not do

Nothing was blocked. I could not screenshot a browser, so §4 executes the
page's own JavaScript instead of describing it.

## Questions for the Architect

1. **`RUNBOOK.md:27`** — re-correct it to 324, or drop the count from the
   command comment entirely? It has now gone stale three times.
2. **`ConfigStore.repo`** (deviation 3) — is depending on that Hydra internal
   acceptable for a local tool, or would you rather the dashboard took the
   restated-constant risk with a test pinning it to the registration?
3. **Server lifecycle** — nothing in the repo starts or stops the dashboard
   for tests; the T7 evidence came from a manually started server. Should
   segment 7 add a fixture that starts it, or does calling the route
   functions directly stay the testing story?
