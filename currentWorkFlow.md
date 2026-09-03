# SEGMENT 7 — Draw the Graph

**Phase 1 · See it · Segment 2 of 5**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` §15 (dashboard spec) and §2.3 (structural rules), and `decisionLedger.md` D8, D14–D17, D30, D32. `WORKFLOW_LOG.md` **Entry 006** rules on segment 6 and carries three decisions that appear below as T1 — read it before starting.
> Append your findings to the **bottom** of this file. Do not modify the spec text above it.

---

## Goal

**Put the graph on screen.** 200 nodes at their real coordinates, 735 edges, and the optimal path lit up across them.

Segment 6 proved a number could travel from the engine to a browser. This segment proves a *picture* can — and picture-drawing is where the temptation to compute locally becomes real for the first time. Every visual decision below is chosen to make that temptation structurally impossible rather than merely discouraged.

Still no timeline, no disruptions, no arms. One graph, one moment, drawn honestly.

## Why this is the segment that can go wrong quietly

A wrong number looks wrong. **A wrong picture looks fine.**

If the browser lays out nodes itself, you get a plausible, pretty, completely fictional graph — and nothing in the test suite objects, because every number is still correct. That is exactly what Rudra saw the first time he ran v1: a spaghetti tangle that *looked* like a result.

So the rule for this segment is sharper than §2.3's general one:

> **The browser receives geometry. It never invents geometry.**
> Positions come from `view.topology.pos`. Edges come from the core's edge list. The path comes from `core.oracle`. The browser's entire job is to convert numbers it was given into pixels — scaling and centring, nothing else.

---

## ⚠️ T0 — MEASURE, and project before you measure

Same two surfaces as segment 6.

1. **`src/` — expect `2005 / 2100`, delta `+0`.** If the drawing needs something the core does not expose, **stop and report**. §2.3 says the core exposes it, but that is a ruling to be made, not a change to be improvised.
2. **`dashboard/` — currently `45 / 1000`, headroom 955.**

**Do this first, before writing:** project the dashboard delta, in statements, from the tasks below. Then report the actual. Entry 005 established the habit and it paid — a projection that misses badly is telling you the design drifted while you were typing.

Report the number segments 8–10 are left with.

---

## Scope

**In scope**
- `dashboard/server.py` — one new endpoint
- `dashboard/static/` — the drawing
- `tests/test_dashboard.py` — new tests
- `RUNBOOK.md` — T1.1 only
- `pyproject.toml` — only if T1.3 needs `httpx`
- One local commit

**Out of scope**
- **Anything under `src/`**
- Timeline, disruptions, playback, arms, charts — segments 8–10
- `viz/replay.py` — retires when the dashboard covers it, which is not yet (D17)
- F4, F7, F8 — Phase 3
- `git push`

---

## Tasks

### T1 — The three rulings from Entry 006

Small, and they go first so they are not squeezed at the end.

**T1.1 — `RUNBOOK.md`: delete the test count, do not re-correct it.**

Two sites, not one:
- **line 27** — `# ~60 s, 271 not-slow tests`
- **line 38** — `**276 collected · 5 slow · 271 not-slow · all passing.**` — you did not flag this one; it carries the same rot

The count has gone stale three times in six segments because it goes stale every time anyone adds a test, which is every segment. **A static file cannot hold a moving quantity honestly.**

Line 27 keeps a rough wall-clock and drops the count. Line 38 says what the suite is *for* and tells the reader to run it for the number. The authoritative counts live in `WORKFLOW_LOG.md`, where each is dated and append-only — **a number describing a moment cannot rot; a number claiming to be current always can.**

**T1.2 — Give the Hydra dependency a test named for what it guards.**

`tier()` reads `ConfigStore.instance().repo["graph"][...]`. That was the right call. But today the only thing that would catch a Hydra change is `test_has_coordinates_is_read_from_the_topology_not_assumed`, which is named for something else entirely — so a future segment could rewrite it for its own reasons and silently delete the protection.

Entry 005's R3 recorded this shape exactly: *if a test would catch something its name does not mention, the protection is incidental and one edit from gone.*

Add a test that says so in its name: `tier("medium200")` returns the fields the registration declares. Assert against the registration, not against restated literals — a test that hardcodes `n_nodes=200` reintroduces the drift `tier()` exists to prevent.

**T1.3 — One HTTP smoke test.**

Every dashboard test today calls the route function directly. Your browser does not — it goes over HTTP and receives JSON, and **numpy scalars are the classic thing that works in Python and 500s on serialisation.** `describe_graph` casts by hand today; the day someone adds a field and forgets, the direct call passes and the page breaks.

Use `fastapi.testclient.TestClient` — real routing, real serialisation, no socket, no port, no teardown. **No live-server fixture.** Assert 200 and a body that round-trips through `json.loads`.

**`httpx` is authorised** into the `dashboard` optional group if `TestClient` requires it. Nothing else is.

### T2 — The geometry endpoint

**A new endpoint. Do not modify `/api/graph`** — it is pinned by the anti-reimplementation test and its stability is worth more than tidiness.

`GET /api/graph/geometry`, returning everything needed to draw and **nothing that has to be worked out**:

| Field | Source | Why it is here and not computed in the browser |
|---|---|---|
| `positions` | `view.topology.pos` | The one field that makes the picture true rather than plausible |
| `edges` | the core's active edge list, as `[u, v]` index pairs | The browser must not decide which edges exist |
| `weights` | per edge, aligned to `edges` | So the drawing can show cost without asking a second time |
| `path` | `core.oracle`'s node sequence | **The browser highlights this sequence. It never searches for a path** |
| `optimum`, `source`, `target` | oracle / `_endpoints()` | So the quoted cost and the drawn path come from one call |
| `has_coordinates` | `view.topology.pos is not None` | Drives T4 |

Order matters: `edges[i]` and `weights[i]` describe the same edge, and the page will trust that. Say in the docstring that they are parallel arrays, because the day they silently desynchronise nothing visible breaks.

### T3 — Draw it

**Inline SVG, built in `app.js` from the endpoint's data.** Not canvas: SVG elements are inspectable in devtools, so "is that node really where the engine put it" is answerable by right-clicking, and this segment is as much a verification instrument as a demo.

- edges as lines, thin and low-contrast — 735 of them, they are context
- nodes as small circles
- **the optimal path highlighted** — its edges thicker and brighter, drawn *on top* of the rest
- source and target marked distinctly from each other, not just from the crowd
- the optimum cost and hop count shown as text beside the drawing, **taken from the same response** that produced the highlighted path

**The browser may do exactly one geometric thing: scale and centre the given coordinates to fit the viewport.** That is presentation. It may not lay out, spring, force-direct, jitter, cluster, or reposition anything.

**Banned, explicitly:** d3, cytoscape, vis.js, sigma, any graph or layout library, and any new dependency at all. They are banned not for weight but because every one of them ships a layout algorithm, and a layout algorithm is a second opinion about where the nodes are.

Keep it legible on a normal laptop screen. 200 nodes and 735 edges is a lot of ink — if it reads as a tangle, say so in FINDINGS rather than quietly making the edges invisible to hide it.

### T4 — Refuse to draw what has no coordinates

`small30` is Erdős–Rényi. It has **no positions.** Anything drawn from it is a picture of the layout algorithm, not of the graph — and it is the specific thing that made v1's replay worthless.

When `has_coordinates` is false the page **shows a clear message and draws nothing.** Not a fallback layout, not a circle arrangement, not a random scatter. A blank panel and a sentence explaining why.

This is a feature, not a limitation, and the page should say which: *this tier has no coordinates, so there is no honest way to draw it.*

### T5 — The tests

| Test | What it catches |
|---|---|
| **The path is the oracle's, and it is a real walk** | Starts at `source`, ends at `target`, and **every consecutive pair is an active edge**. A returned path that is merely a plausible node list fails this |
| **The path's summed weights equal `optimum`** | The strong one. It proves the drawn path and the quoted cost came from the *same* computation. If someone ever recomputes either independently, these two drift and this test is what notices |
| **`positions` are the core's, not a copy that drifted** | Compare against `view.topology.pos` directly, element-wise |
| **`edges` count equals `view.n_active_edges`** | The browser draws what the core says exists, no more and no less |
| **`edges` and `weights` are the same length** | The parallel-array assumption, asserted rather than trusted |
| **`small30` reports `has_coordinates: false`** and the endpoint still answers | T4's contract, server-side |
| **T1.2's Hydra test** | named for what it guards |
| **T1.3's HTTP test** | serialisation over the real route |

**Then mutate, as you did in segment 6 — and pick the mutation that would pass the weak tests.** The interesting one is not a broken path; it is a *valid* path that is not the optimal one, or positions that are shuffled but still 200 coordinates. Paste the mutation and the failure. If a mutation you expected to be caught slips through, **that is the most valuable thing you can report this segment.**

### T6 — Show it

Screenshot is Rudra's job and he will take it. Yours:

1. `curl -s localhost:8000/api/graph/geometry` — **truncated sensibly**; do not paste 735 edges. First few of each array, plus every length, plus the full `path`
2. The SVG the page actually builds — element counts by type, and the first path segment's real coordinates. Execute it, do not describe it
3. **State plainly whether it is legible.** If 735 edges is visual mud, say so — segment 8 inherits that problem and would rather know now

### T7 — Commit

Whole tree. **Do not push.**

```
segment 7: draw the graph (phase 1)

Adds GET /api/graph/geometry, returning positions from view.topology.pos,
the core's active edge list, and the oracle's path — everything needed to
draw, and nothing the browser has to work out. The page builds inline SVG
from it: edges as context, the optimal path highlighted on top, source and
target marked. The browser scales and centres the given coordinates and
does nothing else geometric; no layout library is present to tempt it.

Tiers without coordinates are refused rather than drawn. small30 is
Erdos-Renyi and any picture of it is a picture of a layout algorithm, which
is what made v1's replay worthless.

Tests assert the path is a real walk over active edges from source to
target and that its summed weights equal the quoted optimum — the pair that
drift apart the moment either is recomputed independently.

Also lands Entry 006's three rulings: the stale test count is removed from
RUNBOOK rather than corrected a fourth time, the Hydra config-store
dependency gets a test named for what it guards, and one TestClient smoke
test covers JSON serialisation over the real route.

Spec + findings: currentWorkFlow.md
Log: WORKFLOW_LOG.md entry 007
```

---

## Constraints

| | |
|---|---|
| **Zero statements added to `src/`** | If the drawing seems to need one, stop and report |
| **The browser receives geometry, never invents it** | Scale and centre. Nothing else |
| **No graph or layout library** | Every one ships a second opinion about where the nodes are |
| **No new dependency** | Except `httpx`, and only if `TestClient` requires it |
| **Do not modify `/api/graph`** | It is pinned. Add, do not edit |
| **No timeline, no disruptions, no arms** | Segments 8–10 |
| **Do not touch `viz/replay.py`** | |
| **Use the existing statement counter** | |
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

# 4. Both budgets
./.venv/bin/pytest -q -k "statement" -s

# 5. The stale counts are gone
grep -n "271\|276 collected" RUNBOOK.md        # expect NO test-count hits

# 6. No layout library reached the page
grep -rn "d3\|cytoscape\|vis\.js\|sigma\|force" dashboard/static/   # expect none

# 7. It runs
./.venv/bin/python -m dashboard.server, then:
curl -s localhost:8000/api/graph/geometry | head -c 400

# 8. Committed, not pushed
git log --oneline -2
git status --short --branch | head -1
```

**Expected:** `src/` diff empty · all tests pass · lint clean across three trees · both counts reported with the projection beside them · no stale count survives in `RUNBOOK.md` · no layout library anywhere in `static/` · the endpoint answers · commit on top, ahead 1, unpushed.

**Paste verbatim:**

1. **T0** — projection, then actual, for both surfaces, and headroom left for segments 8–10
2. **The truncated geometry JSON** — array lengths in full, contents sampled, `path` complete
3. **The SVG as built** — element counts, first path segment's coordinates
4. **The mutation** — what you broke, which test caught it, and anything you expected to be caught that was not
5. **`small30`** — what the page shows when it refuses
6. **Your honest read on legibility** at 200 nodes / 735 edges

---

## Definition of done

Eight checks pass, six artefacts pasted, commit exists unpushed, FINDINGS appended.

**After this, Rudra opens a browser and sees the actual graph his experiments run on, with the optimal path lit across it.** Segment 8 makes it move.

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->

---

# FINDINGS — Segment 7

## 1. T0 — projection, then actual

```
                projected        actual       delta
src/            2005  (+0)       2005 / 2100   +0
dashboard/        61 (+16)         56 / 1000  +11    headroom 944
```

**`src/` did not move.** Nothing the drawing needs was missing from the core.
The one thing I expected to need a ruling was the active edge list — the core
exposes no accessor for it — but `viz/replay.py:238` already walks the CSR the
same way, and that file retires into the dashboard under D17. So the dashboard
inherited an existing in-repo pattern rather than inventing one, and `active`
still decides which edges exist. I read that as reading the core's structure,
not computing; flagging it because it is the closest this segment came to the
line.

**The projection missed by 5, high.** I counted a `pos is None` guard as an
if/else (2) and the return dict as several; both collapsed — the guard became
a ternary inside the dict literal, which `ast` counts once. Erring high is the
harmless direction, but the habit is worth keeping precisely because it caught
nothing this time: a projection that only ever matches is not being tested.

**Headroom 944 for segments 8–10**, and one caveat below that number.

### The cap does not measure the thing that grew

`_python_files()` globs `*.py`. `app.js` went from **36 lines to 142** this
segment and contributes **zero** to the 56. The statement brake watches Python;
the dashboard's behaviour is now mostly JavaScript, and segments 8–10 (timeline,
playback, controls) are all JS-heavy.

Not proposing a change — the cap is the Architect's. Reporting it because "56 /
1000, plenty of room" is a true sentence that describes less than half of what
the dashboard now is.

## 2. Geometry JSON, truncated

```
lengths : {'positions': 200, 'edges': 735, 'weights': 735, 'path': 12}
scalars : {'tier': 'medium200', 'seed': 1000, 'n_nodes': 200,
           'has_coordinates': True, 'optimum': 99.96328976797456,
           'source': 0, 'target': 2}

positions[:3] : [[0.49735, 0.66644], [0.05068, 0.70986], [0.99452, 0.17153]]
edges[:5]     : [[0, 35], [0, 40], [0, 89], [0, 116], [0, 119]]
weights[:5]   : [3.6655, 5.0396, 5.0278, 8.3822, 5.6629]
path (full)   : [0, 198, 141, 64, 164, 181, 14, 133, 195, 16, 132, 2]
```

735 edges equals `view.n_active_edges` exactly, and `optimum` is byte-identical
to `/api/graph`'s — the two endpoints are asking the same engine the same
question and neither was touched to make that true.

## 3. The SVG as built

Executed, not described — the real `app.js` run under node against the live
server, with the minimum DOM it touches:

```
SVG AS BUILT BY app.js
  root attrs        : {"viewBox":"0 0 900 620"}
  top-level groups  : edges, nodes, path, ends
  <g class="edges">    {"line":735}
  <g class="nodes">    {"circle":200}
  <g class="path">     {"line":11}
  <g class="ends">     {"circle":1,"rect":1}
  total elements    : 948

  first path segment (real pixel coords):
    x1=444.38 y1=406.50  ->  x2=454.95 y2=356.19

  summary rendered beside the drawing:
    optimum          99.9633
    hops             11
    source → target  0 → 2
    nodes / edges    200 / 735
```

**And the pixels are the engine's coordinates.** Recomputing the scale-and-centre
transform independently in Python from the raw JSON:

```
node 0   at [0.49735, 0.66644] -> pixel (444.38, 406.5)
node 198 at [0.5157,  0.5791 ] -> pixel (454.95, 356.19)
app.js drew : x1=444.38 y1=406.50 -> x2=454.95 y2=356.19
```

Exact. 735 + 11 = 746 lines, one per edge and one per hop — the browser drew
what it was handed and nothing more.

**One deliberate omission: no vertical flip.** SVG's y grows downward and the
spec permits two operations, scale and centre. A y-flip is a third, so the
picture is a vertical mirror of a conventional maths plot. A random geometric
graph has no inherent up, so it is faithful either way — but if you would
rather it matched a scatter plot's orientation, that is a one-line ruling, not
a redesign.

## 4. The mutations

Three, all reverted, each verified byte-identical against a pre-mutation copy
before moving on.

### Mutation 1 — a *valid* path that is not the *optimal* one

The one the spec asked for. Routed source → midpoint → target, so every
consecutive pair is still a live edge and it still runs end to end:

```python
+    detour = view.n_nodes // 2
+    _, leg1, _ = shortest_path(view, source, detour, heuristic=True)
+    _, leg2, _ = shortest_path(view, detour, target, heuristic=True)
+    path = leg1 + leg2[1:]
```

```
E   assert 171.74759783120726 == 99.96328976797456 ± 1.0e-04
FAILED test_the_paths_weights_sum_to_the_quoted_optimum
1 failed, 15 passed
```

**`test_the_path_is_a_real_walk_from_source_to_target` passed.** It is a real
walk. The drawing would have rendered perfectly — a longer blue line, still
connected, still ending on the target — beside a caption reading 99.96 for a
route that costs 171.75. Only summing the weights along the drawn path noticed.

That is the segment's point in one failure: **the picture and its caption can
disagree while both look correct, and only a test that forces them through one
computation sees it.**

### Mutation 2 — positions rolled by 3

Still 200 real coordinates, just not the right ones per node.
`test_positions_are_the_cores_own_coordinates` failed on **400 / 400 mismatched
elements**. Everything else passed, including every path and weight test — as
expected, since the graph is still correct, only its picture is fiction.

### Mutation 3 — the one that got through

Weights rolled by one against `edges`. Same length, every value a real weight,
every edge labelled with its neighbour's cost.

```
FAILED test_the_paths_weights_sum_to_the_quoted_optimum
1 failed, 15 passed
```

**`test_edges_and_weights_are_parallel` passed** — the test named for exactly
this, defending exactly this array pair. It only compared lengths, which is
what "parallel arrays" invites you to write. The mutation was caught downstream
by the weight-sum test: incidental protection under a name promising the real
thing, which is the shape Entry 005 R3 and Entry 006 R2 both ruled on.

**Fixed rather than only reported.** The check is now per edge against the
core's own weight for that exact pair, via `view.find_slot(u, v)`. Re-applying
mutation 3 afterwards:

```
FAILED test_the_paths_weights_sum_to_the_quoted_optimum
FAILED test_edges_and_weights_are_parallel
2 failed, 14 passed
```

It now fails by name. Restored, byte-identical, 16 passed.

I fixed it rather than filing it because the test was written *this* segment and
the name was mine — leaving a test whose name overstates it would have been
adding the defect the last two entries ruled against, in the same commit that
quotes them.

## 5. `small30` — what the page shows when it refuses

```
svg attrs      : {"hidden":"hidden"}
svg children   : 0 (nothing drawn)
refusal hidden : false

The small30 tier carries no node coordinates — it is an Erdős–Rényi graph,
so the engine never generated positions for it. Drawing it would mean
inventing a layout, and the picture would show the layout algorithm rather
than the graph. Nothing is drawn on purpose.
```

The endpoint still answers: `has_coordinates: false`, `positions: []`, and the
edges and path present and correct. The graph exists; only its geometry does
not, and the page says which.

## 6. Legibility — measured, not eyeballed

```
drawing area   : 562 x 572 px
nodes          : 200   -> mean spacing ~40 px
mean degree    : 7.35
edge length px : min 0  p25 31  median 46  p75 56  max 65
edges > 100 px : 0  (0.0%)
```

**It is legible, and the numbers say why.** The longest edge on a 570 px canvas
is **65 px** — no edge crosses the picture. A geometric graph connects near
neighbours only, so 735 edges read as a *fabric* with local texture, not as
spaghetti. The 11-hop path at 2.6 px opaque blue sits on top of 0.6 px grey at
13 % opacity and is unmissable.

This also retroactively explains the v1 tangle Rudra saw. On Erdős–Rényi the
same 735 edges would be drawn uniformly at random and the median edge would
span roughly a third of the canvas — every edge crossing every other. The
difference is not the drawing code; it is the tier. Which is D8's argument,
arrived at from the pixel side.

**One thing segment 8 should know:** the minimum edge length is **sub-pixel** —
at least one node pair is effectively coincident on screen. Anything that
asks the user to click a node needs a hit-target policy for that.

## 7. Acceptance — all eight

| # | Check | Result |
|---|---|---|
| 1a | In scope | 7 files, +367 −12 |
| 1b | `git diff --stat -- src/` | **Empty** |
| 2 | Suite | **337 full** · **332 not-slow, 5 deselected** |
| 3 | Lint, three trees | `All checks passed!` |
| 4 | Both budgets | 2 passed — `src/` 2005/2100, `dashboard/` 56/1000 |
| 5 | Stale counts gone | No hits for `271` or `276 collected` |
| 6 | No layout library | No hits in `dashboard/static/` |
| 7 | It runs | Endpoint answers over HTTP |
| 8 | Committed, not pushed | Below |

**337 full / 332 not-slow**, from 329 / 324 — **+8**, all in
`tests/test_dashboard.py`.

## Deviations from spec

**1. `httpx` was authorised; the error message demanded `httpx2`.**

```
RuntimeError: The starlette.testclient module requires the httpx2 package
    $ pip install httpx2
```

I did not install it. Reading `starlette/testclient.py:33-45`, the import is
`try httpx2 / except ModuleNotFoundError: try httpx` — the fallback to plain
`httpx` is still there, and starlette's own `full` extra declares both. So the
authorised package works and the message is simply out of date. Installed
`httpx>=0.27`; nothing else. **It emits a deprecation warning** and will stop
working whenever starlette drops the fallback — see question 2.

**2. `test_edges_and_weights_are_parallel` was strengthened after writing it**
(§4). In-scope file, my own test, same segment.

## Surprises

**The failing error message told me to install the wrong package.** Had I
trusted it I would have installed something the segment did not authorise, and
had I trusted it the other way I would have reported T1.3 blocked. Neither was
true; the source said so and the message did not.

**Mutation 3 is the finding I did not expect.** I wrote that test, named it for
the invariant, and it did not test the invariant — in the same segment whose
briefing quotes two prior rulings about exactly that pattern. Knowing the rule
is evidently not the same as not breaking it, which is presumably why the
mutation step exists.

## Could not do

Nothing was blocked. No screenshot — §3 executes the page's own code instead.

## Questions for the Architect

1. **The y-flip** (§3) — leave the drawing in SVG's native orientation, or is a
   vertical mirror a third permitted presentation transform?
2. **`httpx` is deprecated for starlette's TestClient.** Migrate to `httpx2`
   when it breaks, or pin `starlette` now while the fallback exists?
3. **The statement cap counts no JavaScript** (§1). Segments 8–10 are the
   JS-heavy ones. Does the dashboard's brake want a second measure, or is the
   1000 explicitly a Python-only limit?
