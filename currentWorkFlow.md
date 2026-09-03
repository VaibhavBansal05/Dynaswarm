# SEGMENT 8 — Make It Move

**Phase 1 · See it · Segment 3 of 5**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` §4.4 (**the temporal contract — the single most important section for this segment**), §15, §2.3, and `decisionLedger.md` D8, D14–D17, D30, D32. `WORKFLOW_LOG.md` **Entry 007** rules on your three questions; R1 is T1 below.
> Append your findings to the **bottom** of this file. Do not modify the spec text above it.

---

## Goal

**Put time on the screen.** Roads break, the graph changes, and the optimal path re-routes in front of you — step by step, with playback you control.

This is the segment where Dynaswarm stops being a picture and becomes the thing the project is actually about: **a shortest path that will not hold still.**

Still no arms, no algorithms racing, no charts. Segments 9–10. This segment shows the *problem* moving; the next one shows the solvers chasing it.

## The one thing that can go wrong, and it is invisible

**F1 was an off-by-one in time.** Every component read one timestep into the future, and it voided every recency-driven result the project had. It was fixed in Phase 0.5 and the fix is pinned by tests.

**This segment can reintroduce it in a place no test currently looks: the picture.**

If the page draws a disruption marker one step early or late, nothing crashes, nothing looks wrong, and the demo shows an edge snapping at the wrong moment while quoting a correct cost. It would be a lie you could point at, in the artefact built to convince your examiner.

`ARCHITECTURE.md` §4.4 and `timeline.events_at()` define the contract:

> `schedule[k]` is the transition from state *k* to state *k+1*, so the events that **produced** state `t` are `schedule[t-1]`.

**Do not re-derive that indexing anywhere.** Not in Python, not in JavaScript, not "just for the marker." Ask `events_at()`, every time. And T7 makes you prove a shifted marker is caught.

## What the browser may and may not do with time

Segment 7's rule stands and gets one careful extension.

**The browser may reconstruct which edges are currently changed**, by applying the event list it was given, in order. That is *visual* state — what to grey out — and it is the only way to avoid shipping 735 edges per timestep.

**The browser may not compute any number.** Every optimum, every path, every cost at every `t` is precomputed by `core.oracle` server-side and sent. The page looks them up; it never solves.

That line is the whole design: **the browser reconstructs appearance, the engine owns every quantity.** If the browser's reconstruction ever drifts from the engine's state, the two disagree visibly — the highlighted path runs through an edge the page has greyed out — which is a failure you can *see*, and that is deliberate.

---

## ⚠️ T0 — MEASURE — three numbers now, not two

**T1 lands first**, then measure against both dashboard budgets.

1. **`src/`** — expect `2005 / 2100`, delta `+0`. If the timeline drawing needs something the core does not expose, **stop and report.** Third segment running; if it breaks here that is worth knowing loudly.
2. **`dashboard/**/*.py`** — currently `56 / 1000`.
3. **`dashboard/static/**`** — the new budget. **Report the opening figure**, since nobody has ever measured it.

Project all three before writing. Report actual beside projection.

---

## Scope

**In scope**
- `dashboard/server.py`, `dashboard/static/`
- `tests/test_dashboard.py`, `tests/test_hygiene.py` (T1 only)
- One local commit

**Out of scope**
- **Anything under `src/`**
- Arms, algorithms, ACO/PSO/hybrid, charts — segments 9–10
- **Reading timelines from `outputs/`** — see T2's ruling
- Clicking or selecting nodes — segment 9, and it needs the hit-target policy Entry 007 recorded
- F4, F7, F8 — Phase 3
- `git push`

---

## Tasks

### T1 — Entry 007's R1: the second budget

The Python cap counts `*.py` and nothing else. `app.js` grew 36 → 142 lines last segment and counted **zero**, while segments 8–10 are the JavaScript-heavy ones. A brake reporting comfortable headroom while the growing half is unmeasured is **F5 again** — a dead instrument returning a flattering number.

Two budgets, two distinct questions. Do not merge them.

| Budget | Question | Cap |
|---|---|---|
| `dashboard/**/*.py` statements | *Has the dashboard become a second engine?* | **1000** |
| `dashboard/static/**` non-blank, non-comment lines — `.js`, `.css`, `.html` | *Has the dashboard become an application?* | **1200** |

**The unit is deliberately cruder than the Python one, and the test must say so in its docstring.** Counting JS statements needs a JS parser and this repo will not take a dependency for a budget. Line-counting is blunt and mildly gameable — and it is *not zero*, which is the entire property the current instrument lacks. Say that plainly where the next reader will see it, so nobody mistakes it for the AST count and reasons from a false equivalence.

Report the opening number. If `static/` is already close to 1200, **say so rather than raising the cap** — that is a finding, not a configuration problem.

### T2 — The timeline endpoint

`GET /api/timeline` — one call, the whole run, no server state.

**Stateless by construction.** The server holds no cursor, no "current step", no session. The page asks once for everything and scrubs locally. A stateful server would make "which step are we on" a thing that can disagree between the page and the process, which is a bug surface this project does not need.

**Build the timeline live from the core. Do not read `outputs/`.** Every run on disk predates F1's fix and carries a permanently misaligned `num_events` column (D32). Drawing disruption markers from those files would draw them one step early — **the exact bug this segment must not reintroduce, reintroduced by trusting stored data instead of the engine.** Stored-run replay waits for Phase 4's regenerated runs.

Return, per timestep `t` from 0 to the horizon:

| Field | Source | Note |
|---|---|---|
| `events` | **`timeline.events_at(t)`** | The contract. Never `schedule[t]`, never a re-derived index |
| `optimum` | `core.oracle` at state `t` | The moving optimum — the quantity the entire project measures against |
| `path` | the oracle's node sequence at `t` | What gets highlighted |
| `reachable` | whether target is still reachable | A disruption can disconnect the graph. **Decide what the page shows then, and say what you decided** |

Plus the horizon and the scenario name once, at the top.

Report the payload size. If it is unreasonable, say so and propose — do not silently thin it.

**First, report what the core actually exposes**: the real names and signatures of the timeline/scenario API, and how a state at `t` is obtained. If applying the timeline requires something not public, **stop and report** before writing around it.

### T3 — Draw the disruptions

On the graph from segment 7:

- **changed edges are visibly changed** — colour or weight, and consistent from the moment they change onward, not only on the step they happen
- **the step where a change lands is marked distinctly** — the difference between "this edge is broken" and "this edge just broke" is the difference between state and event, and both belong on screen
- **the optimal path re-routes** as `t` advances, drawn from the endpoint's `path` for that `t`

Keep segment 7's rule: geometry is received, never invented. Nodes do not move. Ever.

### T4 — Playback

- **step back / step forward**, one timestep
- **play / pause**, at a speed that is watchable rather than impressive
- **a scrubber** — drag to any `t`
- **the current `t` displayed as a number**, always, unambiguously

**Scrubbing must be exact.** Landing on `t` shows state `t` — not `t±1`, not an interpolation. If the scrubber and the step buttons can ever disagree about which step is showing, that is the off-by-one wearing a different hat.

Keyboard: arrow keys step, space toggles play. Cheap and it makes the demo one-handed.

### T5 — Show the moving optimum as a number

Beside the graph, always visible:

```
t = 14 / 60      optimum 104.23      hops 13      2 edges changed this step
```

This is the sentence your examiner needs to understand the entire project. **The optimum moves. That is the problem.** Show it moving.

Every number on that line comes from the endpoint. None is computed in the browser.

### T6 — Tests

| Test | What it catches |
|---|---|
| **Marker time equals engine time, at every `t`** | The endpoint's `events` at `t` are exactly `timeline.events_at(t)`. **The F1 test for the visual layer** |
| **The optimum at every `t` equals the oracle's at that state** | Not the first, not the last — **every** one. This is the anti-reimplementation test for this segment |
| **Every `path` is a real walk in the graph as it stands at that `t`** | A path valid at `t=0` and invalid at `t=30` is what a stale cache looks like |
| **Every `path`'s summed weights equal that `t`'s `optimum`** | Segment 7's strongest test, extended across time |
| **The timeline is stateless** | Two identical requests return identical payloads; requests in any order return the same thing |
| **Unreachability is represented, not crashed on** | Whatever T2 decided, pinned |
| **T1's static budget** | with its docstring stating its own imprecision |

### T7 — Mutations — two required

**The specified one: shift the markers by one.** Make the endpoint return `schedule[t]` instead of `events_at(t)`. That is F1, reintroduced in the visual layer, and it is the mutation this whole segment is built around. **Paste the failure.** If it does not fail, you have found something far more important than a passing test — report it as the headline.

**And at least one nobody specified.** Entry 007 made this a standing rule: the commissioned mutation confirmed a prediction, the uncommissioned one found a real defect. Pick something plausible that the weak version of a test would wave through — a stale path cached from an earlier `t`, an optimum array off by one against the events array, a scrubber that lands on `t-1`.

Report what you tried, what caught it, and — most valuable of all — **anything you expected to be caught that was not.**

### T8 — Show it

1. `/api/timeline` truncated sensibly — the top-level fields, the full first three timesteps, the full timestep with the most events, and total payload size
2. The page as it renders at three different `t`: **0, a step where a disruption lands, and the horizon.** Execute it, do not describe it
3. **State whether the movement is legible.** Does a re-route read as a re-route, or as a flicker? Segment 9 puts four algorithms on this same canvas and inherits whatever you say here

### T9 — Commit

Whole tree. **Do not push.**

```
segment 8: make it move (phase 1)

Adds GET /api/timeline: one stateless call returning, for every timestep,
the events that produced that state via timeline.events_at(), the oracle's
optimum and path at that state, and whether the target is still reachable.
Built live from the core rather than read from outputs/, whose stored runs
predate F1 and carry a misaligned num_events column (D32).

The page plays it: disruptions land on the graph, changed edges stay
changed, and the optimal path re-routes as t advances, with step, play and
scrub controls and the moving optimum shown as a number. The browser
reconstructs which edges have changed so it knows what to grey out; every
quantity it displays is the engine's.

Tests pin marker time to engine time at every timestep, and every path to a
real walk whose summed weights equal that step's quoted optimum. Returning
schedule[t] instead of events_at(t) — F1 reintroduced in the visual layer —
is caught.

Also lands Entry 007's R1: dashboard/static/ gets its own line budget, since
the statement counter globs *.py and had been reporting zero for a file that
grew to 142 lines.

Spec + findings: currentWorkFlow.md
Log: WORKFLOW_LOG.md entry 008
```

---

## Constraints

| | |
|---|---|
| **Zero statements added to `src/`** | Stop and report if the drawing needs one |
| **`events_at()` is the only source of event timing** | No re-derived index, anywhere, in any language |
| **The browser computes no quantity** | It reconstructs appearance. Every number is the engine's |
| **No server state** | Stateless endpoint, client-side playback |
| **Do not read timelines from `outputs/`** | D32. Live from the core |
| **Nodes never move** | Geometry received, never invented |
| **No new dependency** | |
| **Do not modify `/api/graph` or `/api/graph/geometry`** | Both are pinned. Add, do not edit |
| **No clicking the graph** | Segment 9, and it needs a hit-target policy first |
| **Do not push** | |

---

## Acceptance check

```bash
# 1a. In scope
git diff --stat -- dashboard/ tests/
# 1b. The science surface is untouched
git diff --stat -- src/                       # expect EMPTY

# 2. Suite
./.venv/bin/pytest -q -m "not slow"

# 3. Lint
./.venv/bin/ruff check src/ tests/ dashboard/

# 4. All three budgets — report each
./.venv/bin/pytest -q -k "statement or budget" -s

# 5. No re-derived event indexing anywhere
grep -rn "schedule\[" dashboard/                        # expect NONE
grep -rn "t - 1\|t-1\|t + 1\|t+1" dashboard/static/     # inspect every hit, justify or remove

# 6. Nothing reads stored runs for timing
grep -rn "load_events\|load_steps" dashboard/           # only run_classes(), nothing timeline-related

# 7. It runs
curl -s "localhost:8000/api/timeline" | head -c 400

# 8. Committed, not pushed
git log --oneline -2
git status --short --branch | head -1
```

**Expected:** `src/` diff empty · all tests pass · lint clean across three trees · three budgets reported with projections · no `schedule[` in the dashboard and every arithmetic-on-`t` hit justified · no stored-run read in the timeline path · endpoint answers · commit on top, ahead 1, unpushed.

**Paste verbatim:**

1. **T0** — projection then actual, all three surfaces, plus `static/`'s opening figure against 1200
2. **What the core exposes for timelines** — real names and signatures
3. **The truncated timeline JSON** — top-level fields, first three steps, busiest step, total size
4. **The page at `t` = 0, a disruption step, and the horizon**
5. **Both mutations** — the specified shift and your own — what caught each, and anything that slipped through
6. **Your honest read on legibility of movement**, and what you decided for unreachable states

---

## Definition of done

Eight checks pass, six artefacts pasted, commit exists unpushed, FINDINGS appended.

**After this, Rudra can hit play and watch the problem his project exists to solve.** Segment 9 puts the algorithms on it.

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->

---

# FINDINGS — Segment 8

## 1. T0 — three surfaces, projection then actual

```
surface                    projected        actual      delta
src/                      2005  (+0)    2005 / 2100      +0
dashboard/**/*.py           81 (+25)      76 / 1000     +20
dashboard/static/**        340 (+172)    246 / 1200     +78

   app.js       156        headroom: python 924
   index.html    45                  static 954
   style.css     45
```

**`src/` did not move, third segment running.** Everything the timeline needed
was already public: `build_schedule()`, `GraphTimeline`, `events_at()`,
`state_at()`, `shortest_path()`, and `Event`'s `kind/u/v/old_weight/new_weight`
— which is exactly the set a browser needs to reconstruct appearance without
being told anything it could get wrong.

**`static/`'s opening figure was 168 / 1200.** Not close to the cap, so nothing
to report there beyond the number. I over-projected its growth by 94 lines,
mostly because I budgeted for per-frame edge classification that turned out to
be one precomputed pass.

**Both budgets are in `tests/test_dashboard.py`, and `test_hygiene.py` was not
touched.** The spec allowed editing it for T1; I did not, because the two
dashboard budgets answer questions about the dashboard and reading them side by
side is worth more than proximity to the counter they borrow. Flagging it since
the scope line offered otherwise.

## 2. What the core exposes — reported before writing

```python
build_schedule(base: GraphView, cfg: ScenarioCfg, rng, source: int,
               target: int, preserve_connectivity: bool = True)
        -> tuple[tuple[Event, ...], ...]

class GraphTimeline:
    base: GraphView
    schedule: tuple[tuple[Event, ...], ...]
    timesteps  -> int                      # property; len(schedule)
    events_at(t: int)   -> tuple[Event, ...]
    state_at(t: int)    -> GraphView       # pure, cached
    changed_edges(t: int) -> int

@dataclass(frozen=True)
class Event:
    kind: EventKind; slot: int; u: int; v: int
    old_weight: float; new_weight: float
```

Nothing was missing and nothing needed writing around.

**One thing found while reading, reported not touched.**
`GraphTimeline.changed_edges` (`core/timeline.py:272`) is
`len(self.schedule[t - 1])` — it re-derives the index rather than calling
`events_at(t)`. It is **correct today** and agrees with the contract. But the
constraint for this segment is that the arithmetic exists in exactly one place,
and in `src/` it exists in two. A future edit to one and not the other is F1's
whole shape. `src/` is out of scope and it is not broken, so: named, not fixed.

**Also worth knowing before segment 9: `events_per_step` counts *clusters*, not
edges.** `build_schedule` draws `Poisson(events_per_step)` **clusters**, and
`_draw_cluster` returns "a coherent group of edges, all of the same kind and
centred on one node" — in practice 25. At `moderate` this run has **12
disrupted steps out of 60** (80 % quiet against the predicted `exp(-0.3)` =
74 %, fine for n=60) and **284 events**. The registration comment's claim about
quiet fractions is about *timesteps*, and is correct; the field name reads like
it is about edges, and is not. This is why T5's line says "25 edges changed
this step" rather than the spec's illustrative "2".

## 3. The timeline JSON

```
TOP LEVEL
   tier               medium200        horizon   60
   seed               1000             source    0
   scenario           moderate         target    2
   events_per_step    0.3              steps     60

   payload 33.9 KB
```

33.9 KB for a whole 60-step run is not a problem and needs no thinning.

```
FIRST THREE STEPS
   t=0  events=0   optimum=99.96328976797456  hops=11  reachable=True
   t=1  events=0   optimum=99.96328976797456  hops=11  reachable=True
   t=2  events=25  optimum=99.96328976797456  hops=11  reachable=True

BUSIEST STEP — t=2, 25 events
   kinds: {'traffic_up': 25}
   traffic_up    23-31   10.727 -> 21.453
   traffic_up    23-50    5.072 -> 10.144
   traffic_up    23-100   8.810 -> 17.619   …

disrupted steps: [2, 5, 8, 9, 14, 19, 21, 28, 35, 47, 54, 57]
optimum range  : 99.96 .. 110.54
```

**Note t=2: 25 edges break and the optimum does not move.** The cluster is
centred on node 23, which is not on the route. That is correct and it is the
honest case — a disruption that costs nothing because it happened somewhere
else. Four steps actually move the number:

```
t= 5   99.96 -> 102.02    11 hops
t= 8  102.02 -> 103.25    11 hops
t=21  103.25 -> 110.54    11 -> 12 hops     <- a real re-route
t=57  110.54 -> 103.25    12 -> 11 hops     <- and a recovery
```

## 4. The page at t = 0, 21, 59

Executed, not described — the real `app.js` under node against the live server:

```
=== t = 0 ===
  t = 0 / 59      optimum 99.96      hops 11      0 edges changed this step
  svg groups : {"e-base":735,"e-changed":0,"e-gone":0,"nodes":200,
                "e-hit":0,"path":11,"ends":2}

=== t = 21 ===
  t = 21 / 59      optimum 110.54      hops 12      25 edges changed this step
  svg groups : {"e-base":610,"e-changed":125,"e-gone":25,"nodes":200,
                "e-hit":25,"path":12,"ends":2}

=== t = 59 ===
  t = 59 / 59      optimum 103.25      hops 11      0 edges changed this step
  svg groups : {"e-base":566,"e-changed":178,"e-gone":66,"nodes":200,
                "e-hit":0,"path":11,"ends":2}
```

Damage accumulates as it should: 0 changed at t=0, 150 by t=21, 244 by t=59,
and `e-hit` is non-zero **only** on a step where something actually lands. The
path is 11 hops, 12 at the re-route, 11 again after the recovery — matching the
endpoint exactly. The scrubber reads 0, 21, 59 with max 59; it sets `t` to its
own value and nothing adjusts it.

Edge totals exceed 735 later on because `add` events create edges the base list
never had. The browser draws them from `event.u`, `event.v` and the node
positions it already has — no geometry is invented, only edges the engine said
appeared.

### The browser's reconstruction agrees with the engine

The design's claim is that if the page's greyed-out set ever drifts from the
engine's active set, the highlighted path visibly crosses a broken edge. Tested
that directly across the whole run:

```
696 path edges checked across 60 timesteps
drawn as removed while carrying the route: 0
-> the page's greyed-out set and the engine's active set agree everywhere
```

## 5. Both mutations

### A — the specified one: F1, reintroduced in the visual layer

```python
-                for event in timeline.events_at(t)
+                for event in timeline.schedule[t]
```

**Caught by two tests, and the failure names the timestep:**

```
E  AssertionError: t=1
E  assert 25 == 0
FAILED test_marker_time_equals_engine_time_at_every_timestep

E  AssertionError: server.py:245 indexes the schedule
FAILED test_the_dashboard_never_derives_event_timing_itself
```

It fails at **t=1**, not t=0 — both are empty at t=0, which is precisely why
the test walks every timestep rather than sampling. The disruption really lands
at t=2; the mutation would have drawn it at t=1, one step early, with a correct
optimum beside it.

### B — mine: the same off-by-one, one layer out, where nothing was looking

```javascript
-  const step = run.steps[t];
+  const step = run.steps[Math.max(0, t - 1)];
```

Server untouched. The drawing stays current; only the numbers and the
highlighted route go one step stale.

```
24 passed
```

**The entire Python suite is blind to it.** Every endpoint test still passes,
because the endpoint is still perfect. What the page then shows at t=21:

```
mutated : t = 21 / 59   optimum 103.25   hops 11   0 edges changed this step
correct : t = 21 / 59   optimum 110.54   hops 12   25 edges changed this step
```

It reports **"0 edges changed this step"** on the exact step where 25 edges
break and the route re-routes — while the picture beside it shows the break
happening. That is the segment's stated nightmare, produced by a two-character
edit in a file no test reads.

**What did catch it — partly.** The design's self-disagreement property fired:

```
696 path edges checked across 60 timesteps
drawn as removed while carrying the route: 3
  t=5 path uses 64,164: { gone: true, hit: 5 }
  t=5 path uses 164,181: { gone: true, hit: 5 }
-> DISAGREEMENT: the visible failure this design was built to expose
```

So a human watching t=5 would see a blue route crossing two red broken roads.
**But 3 out of 696**, on one step out of sixty. It is a real property and it
worked; it is not a safety net. You would have to be looking at the right
frame.

And acceptance check 5b — `grep "t - 1" dashboard/static/` — flags it on line
80. So the thing standing between this defect and the demo is **a human reading
grep output once, at the end of a segment.**

## 6. Legibility, and the unreachable decision

**Movement reads as movement.** The re-route at t=21 is unmistakable: the blue
line visibly takes a different corridor, the hop count ticks 11 → 12, and 25
edges go bright red at once. Because a disruption is a *cluster* centred on one
node, a break reads as a neighbourhood going dark rather than a single hairline
changing — much easier to see than I expected, and the reason is the core's
clustering, not the drawing.

`e-hit` (bright red, this step) versus `e-changed` (amber, earlier) is the
distinction that makes it work. Without it, a step where damage lands looks
identical to a step where damage merely persists.

**Two honest caveats for segment 9:**

1. **Quiet steps look like nothing is happening, because nothing is** — 48 of
   60. At 320 ms a frame the run plays in 19 s and most of it is still. That is
   the truth of the scenario, not a rendering problem, but four algorithms
   racing on the same canvas will want a way to skip to the next event.
2. **244 of 810 edges are amber by t=59.** Damage accumulates and never clears
   visually, so late steps are busier than early ones. Legible now; adding four
   coloured arm-paths on top of that is the thing most likely to tip it.

**Unreachable states — decided and pinned:** `optimum: null`, `path: []`,
`reachable: false`, the step still present so playback runs through it, and the
readout shows `optimum unreachable` / `hops —` in red rather than a number.
Never an exception, never a skipped step. It did not occur in this run —
`preserve_connectivity` rejects severing events — so the test exercises
`scenario_name="high"` and asserts the representation holds for whatever
happens there.

## 7. Acceptance — all eight

| # | Check | Result |
|---|---|---|
| 1a | In scope | 5 files, +534 −107 |
| 1b | `git diff --stat -- src/` | **Empty** |
| 2 | Suite | **345 full** · **340 not-slow, 5 deselected** |
| 3 | Lint, three trees | `All checks passed!` |
| 4 | Three budgets | 8 passed — 2005/2100 · 76/1000 · 246/1200 |
| 5a | No `schedule[` in dashboard code | Two hits, both in the header comment quoting §4.4; the AST/comment-stripping test asserts the real thing |
| 5b | Every `t ± 1` in `static/` | 5 hits, all **playback navigation** (`show(state.t ± 1)`) — moving the cursor, never indexing an event list |
| 6 | No stored-run reads | `load_steps` appears twice, both in `run_classes()`; nothing timeline-related |
| 7 | It runs | 33.9 KB payload over HTTP |
| 8 | Committed, not pushed | Below |

**345 full / 340 not-slow**, from 337 / 332 — **+8**.

## Deviations from spec

**None.** T1's placement (§1) was a choice the spec permitted either way.

## Surprises

**The uncommissioned mutation found the hole again, and it is the same hole in a
new place.** Segment 7's lesson was that a test can be named for a guarantee it
does not provide. This one is worse: the guarantee has no test at all in the
language that half the dashboard is now written in. 246 lines of JavaScript are
covered by exactly two greps and my ad-hoc node harness, which is not in the
repository and runs only when I choose to run it.

**A break that costs nothing is common.** At t=2, 25 edges break and the
optimum does not move — the cluster landed off-route. I had assumed disruption
implied cost. Most of them do not, and that is worth knowing before segment 9
tries to show algorithms *reacting* to disruptions: many of the reactions will
be to events that never mattered.

## Could not do

Nothing was blocked.

## Questions for the Architect

1. **The headline (§5B): should the browser be tested, and with what?** Options
   as I see them, cheapest first — (a) extend the existing textual guard to
   assert every `run.steps[...]` index is bare `t`, which is brittle and
   segments 9–10 will fight it; (b) admit `node` as a **dev-only test
   dependency** and run the existing harness under pytest with
   `pytest.importorskip`-style skipping when node is absent; (c) accept the
   grep and the visible-disagreement property as sufficient, and record that
   the JS is deliberately untested. I lean (b) — the harness already exists and
   has now caught something twice — but it admits a whole language into the
   test story, which is a ruling and not mine.
2. **`changed_edges` duplicates the index arithmetic in `src/`** (§2). Phase 3
   defect, or leave it — it is correct and the segment that would touch it has
   no other reason to?
3. **Quiet steps** (§6) — should segment 9 get a "jump to next event" control,
   or does watching 48 still frames honestly represent the problem?
