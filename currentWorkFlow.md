# SEGMENT 10 — Hand Over the Controls

**Phase 1 · See it · Segment 5 of 7**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` **§15.3, §15.4, §15.7** and **§4.3.1 (new — the edge lifecycle)**, §2.3. `WORKFLOW_LOG.md` **Entry 009** carries R2–R4, all of which are tasks here.
> Append your findings to the **bottom** of this file.

---

## Goal

**Stop hardcoding the world.** Rudra chooses the graph and chooses how it breaks, then watches what he built.

Segments 7–9 built the rendering halves of §15.3 and §15.4 and left the choosing halves out. This closes both.

---

## ⚠️ T0 — MEASURE

`src/` `2005 / 2100` (expect `+0`, fifth segment) · `dashboard/**/*.py` `76 / 1000` · `dashboard/static/**` `361 / 1200`. Project, then report actual, plus what segments 11–13 have left.

---

## Tasks

### T1 — The small ruled items, first

| | |
|---|---|
| **R2** | Widen `STATIC_SUFFIXES` to include `.json`. The budget asks *"has this become an application?"* and a growing config file is that growth as surely as a growing script. Report the new figure |
| **R3** | Every acceptance block in this repo's specs said `pytest -q`; `addopts` already carries `-q`, so that meant `-qq` and suppressed the summary. **This spec says `pytest`.** If `RUNBOOK.md` repeats the mistake, fix it there too |
| **R4** | **Jump-to-next-event** — 48 of 60 steps are quiet and the demo dies waiting. Next/previous step *with events*. Beside the playback controls |
| | **Reset → `t=0`** |
| | Drop `Phase 1 · segment N` from the page header — internal bookkeeping, not for an examiner |
| | Drop the **D32 warning banner**. Its job is done: it existed so whoever built the timeline could not miss that stored runs carry misaligned timing, and segment 8 built from live data instead. **Report whether the "runs on disk" panel still earns its place** — that is a ruling, not your call |
| | Drop the **"local development server…"** footer |
| | **Thicken `delete`** — currently width 1.0 / opacity 0.55 and effectively invisible. It must read as *"this road is gone permanently"*, distinct from `closure`, without competing with live events |

### T2 — Stage 1: build the world (§15.3)

Controls for **model, node count, density, seed** → **Generate**. Re-rolling the seed browses variants.

**`POST /api/graph` per §15.7 — and do not touch the existing `GET /api/graph`.** That endpoint is pinned by the anti-reimplementation test and its stability is worth more than tidiness. Add alongside.

**The graph id must be derived, not stored.** A deterministic function of `(model, n_nodes, density, seed)` — a hash is fine. This matters: segment 8 ruled the server holds **no state**, and an id handed out from a server-side registry would break that, bringing sessions, eviction and two-viewers-disagree with it. A derived id means any request carrying it rebuilds the identical graph from nothing. Segment 11 gets the identity it needs to race on *this* graph; the server still remembers nothing.

A cache for speed is permitted **only if evicting it cannot change any answer.** Say which you did.

Panel shows `|V|`, `|E|`, mean degree, optimal cost. **`small30` must remain selectable and must still refuse to draw** — the refusal is a feature and the picker is where a user will first meet it.

### T3 — Stage 2: design the disruption (§15.4)

A **scenario preset** dropdown (`static` / `low` / `moderate` / `high`), and the underlying knobs: `events_per_step`, `cluster_size`, `timesteps`, and the six event probabilities. → **Build**.

**`POST /api/timeline`**, same derived-id discipline, keyed on the graph id plus the scenario parameters.

Report which preset names and parameters the **code** actually exposes, from source. §4.3's scenario table is the document.

### T4 — The ledger — the invariant made watchable

**Rudra's request, and it is worth more than a stat panel.**

Per §4.3.1 the population of slots is closed, so at every `t`:

```
active(t) = active(0) + (adds + reopens) − (closures + deletes)
```

That is an **exact identity, not an approximation.** Put it on screen as a running ledger — `initial`, `added`, `reopened`, `closed`, `deleted`, `current` — and it becomes an invariant an examiner can watch hold for sixty steps.

Also: **live `|E|` on the stat line.** A pool road genuinely connects a node pair that had none, so the edge count really moves, and the picture currently hides that.

**Every number comes from the engine's counts.** If the browser must tally events to produce them, that is bookkeeping over data it was given — but the *reconciliation* (`current` against the engine's `n_active_edges` at that `t`) must compare against the engine's own figure, not against the browser's running total. **A ledger that only agrees with itself proves nothing.**

### T5 — Tests

| Test | Catches |
|---|---|
| **The ledger balances at every `t`** | Against the engine's `n_active_edges`, not the browser's tally. **The one that matters** |
| **`|E|` changes when a pool road is added** | Proves `add` is not an overlay |
| **A derived id round-trips** | Same parameters → same id → identical graph, from a cold process |
| **Evicting any cache changes no answer** | The statelessness rule, asserted rather than promised |
| **`closure`/`delete` only target `active` slots; `reopen` only `base_active`; `add` only pool** | §4.3.1's eligibility table. Rudra asked whether a road that never existed can be deleted — pin the answer |
| **An added road can be closed and re-added, and never becomes `reopen`-eligible** | The lifecycle across cycles |
| **`small30` picked → refuses to draw** | |
| **Jump-to-next-event lands on a step with events** | And on the *nearest* one |

### T6 — Mutations, two, one of them yours

**Specified:** make the graph id ignore `seed`. Two different worlds collapse to one id — the failure segment 11 would inherit as arms racing on a graph they were not built for.

**Yours.** Entry 009's slipped mutation is the standing warning: **a threshold or bound must come from the property protected, never from the number being replaced.** Say what you tried and anything that got through.

### T7 — Show it

1. Generate a **different** graph (change nodes and seed) — paste the panel and the new `|E|`
2. Build a **different** scenario — paste the timeline summary
3. **The ledger at `t=0`, mid-run, and `t=59`**, with the balance shown holding
4. Jump-to-next-event from `t=0`: which step does it land on, and is that the nearest one with events?
5. Does the page still read cleanly with the banners gone?

### T8 — Commit

**Name the files explicitly. Do not use `git add -A`.** The Architect's `WORKFLOW_LOG.md` and `ARCHITECTURE.md` edits live in this same tree as unstaged changes, and `git add -A` cannot tell them apart — it swept Entry 008 last segment. Noticing is not a control.

```
segment 10: hand over the controls (phase 1)

Stage 1 and Stage 2 of the dashboard: choose model, nodes, density and
seed and generate; choose a scenario preset or set the disruption knobs
and build. POST /api/graph and POST /api/timeline per §15.7, alongside the
existing GET endpoints, which stay pinned.

The graph id is derived from its parameters rather than issued from a
registry, so identity costs no server state: any request carrying an id
rebuilds the same graph from nothing, and segment 11 can race on a named
graph without the server remembering one.

Adds the edge ledger. §4.3.1's population of slots is closed, so
active(t) = active(0) + adds + reopens - closures - deletes exactly, and
the panel shows it holding against the engine's own count rather than
against its own tally. Live |E| joins the stat line, since a pool road
connects a node pair that had none.

Also: jump-to-next-event (48 of 60 steps are quiet), reset to t=0, a
readable weight for deleted roads, .json inside the static budget, and the
internal banners removed from a page that is now shown to people.

Spec + findings: currentWorkFlow.md
Log: WORKFLOW_LOG.md entry 010
```

---

## Constraints

| | |
|---|---|
| **Zero statements added to `src/`** | Stop and report |
| **No server state** | Derived ids only. A cache must be evictable with no change in answers |
| **Do not modify `GET /api/graph`, `/api/graph/geometry`, `/api/timeline`** | Pinned. Add alongside |
| **The browser computes no quantity** | The ledger reconciles against the engine's count |
| **Hue is not spent on arms** | §15.5 gives each arm its own pane; position carries identity (Entry 009 R1) |
| **No arms, no inspect panels, no design pass** | Segments 11, 12, 13 |
| **Commit names files** | No `git add -A` |
| **Do not push** | |

---

## Acceptance check

```bash
git diff --stat -- dashboard/ tests/ RUNBOOK.md
git diff --stat -- src/                     # expect EMPTY
./.venv/bin/pytest                          # NOT -q. Report passes and skips
./.venv/bin/ruff check src/ tests/ dashboard/
./.venv/bin/pytest -k "statement or budget" -s
grep -rn "segment\|D32\|not hosted" dashboard/static/index.html   # expect none
git log --oneline -2 && git status --short --branch | head -1
```

**Paste verbatim:** T0 all three with projections · the preset names and parameters **from source** · the derived-id scheme and whether a cache exists · the ledger at three points with the balance holding · jump-to-next-event's landing step · both mutations · whether the "runs on disk" panel should survive.

---

## Definition of done

Checks pass, artefacts pasted, commit exists unpushed, FINDINGS appended.

**After this Rudra builds his own world and watches it break.** Segment 11 races the arms on it.

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->

---

# FINDINGS — Segment 10

## 1. T0 — three surfaces

```
                       projected        actual       delta
src/                  2005  (+0)    2005 / 2100       +0
dashboard/**/*.py       ~130 (+54)    125 / 1000      +49
dashboard/static/**     ~640 (+279)   665 / 1200     +296
```

`src/` **+0 for the fifth consecutive segment.** Two POST endpoints, derived
ids, per-step active-edge counts and the whole picker surface, and the core
still exposed everything: `GraphView.n_active_edges`, `candidate_slots`,
`base_active` and `build()` were already public.

**Left for segments 11–13: 875 Python statements, 535 static lines.** The
static figure is the one to watch — this segment spent 296 of the 1032 that
existed, and segment 11's pane grid is the next large consumer.

`.json` is now inside the static budget (**R2**), which moved the figure by
**+59** on its own — `palette.json` had been growing unmeasured, which is the
exact shape of the thing R2 exists to stop.

**R3 confirmed empirically.** `pytest` without `-q` prints
`357 passed in 67.65s`; the same command with `-q` prints nothing after the
progress dots. The suppressed summary I spent several tool calls debugging at
the end of segment 9 was `addopts`' `-q` doubling with mine, exactly as ruled.
`RUNBOOK.md` had the same mistake in two places and now says `pytest`. Its
`pytest --collect-only -q` is **left alone** — there `-q` selects the
collection listing format and is correct.

## 2. The presets the code actually registers

**Graph tiers** (`config.py:288-302`) — four:

```python
cs.store(group="graph", name="small30",    node=GraphCfg())                                    # erdos_renyi, 30, 0.3
cs.store(group="graph", name="medium200",  node=GraphCfg(model="geometric", n_nodes=200,  density=0.04))
cs.store(group="graph", name="large1000",  node=GraphCfg(model="geometric", n_nodes=1000, density=0.01))
cs.store(group="graph", name="grid20",     node=GraphCfg(model="grid",      n_nodes=400))
```

**Scenarios** (`config.py:308-313`) — four, and here is the finding:

```python
cs.store(group="scenario", name="static",   node=ScenarioCfg(name="static",   events_per_step=0.0))
cs.store(group="scenario", name="low",      node=ScenarioCfg(name="low",      events_per_step=0.1))
cs.store(group="scenario", name="moderate", node=ScenarioCfg(name="moderate", events_per_step=0.3))
cs.store(group="scenario", name="high",     node=ScenarioCfg(name="high",     events_per_step=0.8))
```

**A "scenario preset" changes exactly one number.** `cluster_size` (25),
`timesteps` (60), the six probabilities and `traffic_factor` (2.0) are
`ScenarioCfg`'s defaults in all four. The word "preset" implies a bundle; it is
a single knob.

That is why Stage 2 puts the knobs *beside* the preset rather than behind it —
picking `high` and picking `moderate` differ only in rate, and everything that
actually shapes a disruption is in the fields underneath. **`static` is
`events_per_step = 0.0`**, so it produces a genuinely empty timeline and
jump-to-next-event correctly has nowhere to go.

## 3. The derived id, and the cache that does not exist

```python
payload = f"{spec.model}|{spec.n_nodes}|{spec.density!r}|{spec.seed}"
return hashlib.blake2b(payload.encode(), digest_size=6).hexdigest()
```

`blake2b` and not `hash()`: Python salts `hash()` per process, so the same graph
would be named differently after every restart — and an id that changes on
restart is a registry with extra steps. It is also what `core/rng.py` already
uses to name streams, so content-addressing is the house convention rather than
a new idea.

**There is no cache.** The spec permits one only if evicting it cannot change an
answer, and the cheapest guarantee of that is having nothing to evict. It is
affordable because rebuilding is cheap:

```
build_world (200 nodes)          12 ms
build_run   (200 nodes, 60 steps) 74 ms
```

74 ms to rebuild an entire run from four parameters. A cache would buy nothing
worth the statelessness it costs. `test_the_server_holds_no_state_between_requests`
asserts identical calls stay identical however they are interleaved, and also
asserts no `_CACHE` attribute has appeared — so the day someone adds one, the
eviction rule stops being hypothetical and the test says so.

## 4. The ledger

Verified against the engine before any UI existed:

```
ledger checked at all 60 timesteps, mismatches: 0
final: initial 735 + adds 75 + reopens 9 - closures 50 - deletes 25 = 744,
       engine says 744
```

On screen, at three points:

```
=== t = 0 ===
  t = 0 / 59      optimum 99.96      hops 11      |E| 735      0 edges changed this step
  ledger : initial 735   + added 0   + reopened 0   − closed 0   − deleted 0   = current 735
  balances — engine reports 735 active edges

=== t = 30 ===
  t = 30 / 59      optimum 110.54      hops 12      |E| 785      0 edges changed this step
  ledger : initial 735   + added 75   + reopened 0   − closed 0   − deleted 25   = current 785
  balances — engine reports 785 active edges

=== t = 59 ===
  t = 59 / 59      optimum 103.25      hops 11      |E| 744      0 edges changed this step
  ledger : initial 735   + added 75   + reopened 9   − closed 50   − deleted 25   = current 744
  balances — engine reports 744 active edges
```

**`|E|` moves 735 → 785 → 744.** A pool road really does connect a node pair
that had none, and the picture was hiding that until now.

## 5. Jump-to-next-event

```
disrupted steps: 2, 5, 8, 9, 14, 19, 21, 28, 35, 47, 54, 57
four presses land on: 2 -> 5 -> 8 -> 9
nearest disrupted step after 0 is 2 -> correct
```

`seekEvent` returns `null` rather than guessing when there is no next event, so
the cursor stays where it is at the end of a run and throughout a `static`
scenario.

## 6. T7.1 / T7.2 — a different world, differently broken

```
400 nodes, density 0.02, seed 7:
  graph_id     515bf7aa93a5
  |V| 400   |E| 1549   mean degree 7.75   optimal cost 146.75   0 -> 122

for comparison, the default:
  graph_id efc1c968922f  |V| 200  |E| 735  deg 7.35  opt 99.96
```

```
high rate, 8-edge clusters, 40 steps, closure-heavy:
  disrupted steps: 22 of 40   (the default run: 12 of 60)
  event kinds: closure 88, delete 48, traffic_down 48, traffic_up 32, add 16, reopen 8
  |E|      1549 -> 1437
  optimum  146.75 -> 153.55
```

All six kinds present, `|E|` falling under a closure/delete-heavy mix. The
knobs do what they say.

## 7. Both mutations

### A — specified: the graph id ignores `seed`

```
E  AssertionError: seed does not reach the graph id
E  assert 'efce1e910f78' != 'efce1e910f78'
FAILED test_different_parameters_give_different_ids
```

**`test_a_derived_id_round_trips_from_a_cold_process` passed under it.**
Determinism survived the mutation intact — only *distinctness* broke. A
segment that had tested only "same parameters give the same id" would have
shipped two worlds sharing one name.

### B — mine: a ledger that reconciles against itself

```javascript
-  const engineCount = steps[t].n_active_edges;
+  const engineCount = predicted;
```

The ledger then balances on any data whatsoever.

**The test named for the property did not catch it.**
`balances against the engine's own count at every timestep` asserted
`l.balances === true`, which is satisfied trivially by a ledger that can never
be false. Only `the ledger says DIVERGED rather than quietly rounding` — which
I wrote as an afterthought about UI wording — failed.

**And the obvious repair did not work either.** I added
`assert.equal(l.engineCount, run.steps[t].n_active_edges)` and re-ran the
mutation: still green, because on correct data the predicted value *is* that
number. Nothing checked against a correct run can distinguish the two.

The only thing that can is data where they disagree. The test now perturbs one
step's count by +7 and asserts the ledger notices:

```
not ok 1 - balances against the engine's own count at every timestep
not ok 8 - the edge ledger — an invariant, not a statistic
# pass 30  # fail 2
```

restored → `# pass 32  # fail 0`.

**The generalisation, and it is the sharpest form of Entry 009's warning yet:**
an invariant test written only against correct data cannot tell a real
invariant from a tautology. Both are green. **The assertion has to be handed
something that ought to break it.**

## 8. Acceptance

| Check | Result |
|---|---|
| In scope | 9 files |
| `git diff --stat -- src/` | **Empty** — fifth segment |
| Suite | **357 passed, 0 skipped** (from 349) |
| Lint, three trees | `All checks passed!` |
| Three budgets | 2005/2100 · 125/1000 · 665/1200 |
| Banners gone | no hits for `segment`, `D32`, `not hosted` in `index.html` |
| JS suite | **32 passed** under both node installs |
| Committed, not pushed | below |

**Skips: 0.** Node was present, so nothing went unchecked.

## Deviations from spec

**None.**

## Surprises

**The `.json` widening was not cosmetic.** `palette.json` is 59 lines — 9% of
the static budget — and it had been invisible to the brake since the day it was
created. R2 was filed as a one-liner; it turned out to be the second-largest
unmeasured file on the page.

**`erdos_renyi` at 30 nodes has 125 edges and a mean degree of 8.3**, which is
why `small30` "survives" as a test tier despite being undrawable — the target is
one or two hops from anywhere. The picker now makes that concrete: choosing it
refuses to draw and says why, which is a better explanation of D8 than the
sentence in the docs.

## Could not do

Nothing was blocked.

## Questions for the Architect

1. **Does the "runs on disk" panel still earn its place?** My read: **no, not
   in its current form.** With the D32 banner gone it is a bare count of
   `exploratory: 9240` with nothing to click and nothing to load — it answers
   "how much scratch data exists", which is a question nobody standing in front
   of this page is asking. It becomes worth having when the dashboard can
   *load* one of those runs, which is stored-run replay, which waits for Phase
   4's regenerated data. Suggest dropping it until then; it is four lines of
   HTML to restore. Your ruling.
2. **`ScenarioCfg.name` is set to `"custom"`** for every POST-built timeline,
   since the knobs may not match any registered preset. If a dashboard-driven
   run is ever written to `outputs/` (D15/D16), that name lands in the manifest
   — is `"custom"` the right label, or should the endpoint detect an exact
   preset match and name it?
3. **Static budget pacing.** 665/1200 with three segments left, and segment 11's
   pane grid is the next large consumer. Worth a projection before segment 11
   is written rather than discovering it mid-segment?

---

# FINDINGS — Segment 10 addendum: a design pass, out of order, at Rudra's request

**Flagging the scope breach first.** Segment 10's constraints say *"No arms, no
inspect panels, no design pass — Segments 11, 12, 13."* Rudra looked at the
delivered page and asked for it directly. He is the owner, so I did it; recording
it as **out-of-order work done at his request**, not as drift, so the segment 13
spec is written knowing this already happened.

## What was actually wrong

The page set **everything** in monospace — headings, labels, prose and data
alike — so a field label shouted as loudly as the number beside it, and nothing
established what to read first. Panels had no ground of their own, controls were
browser defaults, and the most important line on the page (`t`, optimum, hops,
`|E|`) was a run-on paragraph of space-padded text.

## What changed

**Two typefaces, doing two jobs.** System UI face for prose and controls;
monospace **only for numbers**, tabular-lining so a changing digit does not shift
the ones beside it. That is not decoration — on a page whose whole purpose is
watching figures move while a picture changes, digits that jitter are a
readability defect.

**The stat line became five stat blocks** with label-above-value, which is a
real structural change rather than styling: it needed new markup and new JS.
`#readout` is now the error channel alone, hidden by `.readout:empty` so no JS
coordination is required to show or hide it.

**One accent, used three times** — the step badges, the optimal path, and the
single filled button per panel. Everything else is neutral. The semantic event
colours are untouched: they are the data encoding, and this pass had no business
near them.

**The ledger's closing row is weighted like a total**, because that is the row
that has to balance.

```
=== t = 0 ===
  0 / 59   |   99.96   |   11   |   735   |   0
=== t = 30 ===
  30 / 59  |  110.54   |   12   |   785   |   0
=== t = 59 ===
  59 / 59  |  103.25   |   11   |   744   |   0
```

## Three tests changed, and why that was necessary rather than convenient

`loads and renders t=0`, `scrubbing lands exactly on the requested t` and
`the stat line carries live |E|` all read `#readout`'s text, which no longer
carries figures. They now read the stat blocks.

The `|E|` test was **strengthened while it was open**: it now asserts the shown
value equals `steps[59].n_active_edges` *and* differs from `steps[0]`'s — a
test that only matched `/\|E\| \d+/` would have passed against a hardcoded
opening count, which is the exact defect the live count exists to expose.

The harness needed no change: it derives element ids and defaults from
`index.html`, so the five new stat ids appeared on their own. That decision paid
within the hour.

## ⚠️ The budget, and it is now the constraint

```
static/**   665 -> 856 / 1200      the design pass cost +191
```

**344 lines left for segments 11, 12 and 13.** Segment 11's pane grid is the
largest remaining consumer and segment 13 is *itself* the design segment, whose
budget I have now partly spent.

This wants a ruling before segment 11 is written. Three options as I see them:
**(a)** accept that segment 13 is now mostly done and re-scope it; **(b)** raise
the static cap on the same terms the science cap was raised — measured, argued,
recorded; **(c)** hold 1200 and let segment 11 discover the wall mid-flight,
which is the one option I would argue against, since that is how a segment ends
up deleting something that mattered to make room.

**All 36 dashboard tests pass, 32 JS tests pass, lint clean, `src/` untouched.**
