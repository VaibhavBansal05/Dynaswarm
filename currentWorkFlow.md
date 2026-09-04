# SEGMENT 9 — Two Layers: State and Event

**Phase 1 · See it · Segment 4 of 6**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` **§15.3 and §15.4** (the stages this segment serves), §15.7 (API shape), §2.3, and `decisionLedger.md` D8, D14–D17, D32. `WORKFLOW_LOG.md` **Entry 008** carries R1 (node as a test dependency), which is **T1 here**.
> Append your findings to the **bottom** of this file. Do not modify the spec text above it.

---

## Why Phase 1 is now six segments, and why this one comes before the pickers

**Rudra opened the browser and asked where the controls were. He was right to.**

`ARCHITECTURE.md` §17 says Phase 1 is *"scaffold, then Stages 1 → 2 → 3 → 4, one segment each."* §15.3's Stage 1 opens with **"Choose model, node count, density, seed. Generate."** The picker *is* Stage 1. §15.4's Stage 2 is **"Choose a scenario preset or set `events_per_step`, `cluster_size`, `timesteps` and the six event probabilities."**

Segments 7 and 8 built the *rendering* half of each stage and dropped the *choosing* half. That was a deliberate sequencing decision — proving the pipe before building controls, which paid: two segments of mutation testing found real defects that a UI would have hidden. **But it was never recorded and never announced, and the person it was built for found out by opening a browser and being confused.** That is the failure the protocol exists to prevent, and it was mine.

**Phase 1 is six segments now:** 6 scaffold · 7 render · 8 playback · **9 rendering model** · 10 pickers (Stage 1 + 2 controls, POST API, graph id) · 11 race (Stage 3) · 12 inspect (Stage 4). *(Counting: 6–12 is seven overall segments, six of them Phase 1 after the scaffold.)*

**Rendering comes before pickers, on merit.** The pickers exist so Rudra can generate different worlds and *look at them*. If the renderer is still mud, every world he picks is mud and he cannot evaluate his own choice. Fix the eye first, then give it things to look at.

---

## Goal

**Separate two things the picture currently conflates, and make the result readable across a room.**

Right now every change to a road is painted the same colour, so *"a new road appeared"* and *"a road closed"* — opposite events — look identical, and the amber accumulates until 244 of 735 edges are lit and the screen is mud.

The fix is not a better palette. It is recognising that **the picture is showing two different kinds of fact through one channel.**

> **A road's price is a STATE.** It is true right now, it stays true, and it is what the algorithms' cost function actually sees.
>
> **A road breaking is an EVENT.** It happens at one step and is over, and it is what the **recency signal** sees.

Two layers. State is quiet and permanent; events are loud and self-clearing. That is what makes mud impossible by construction rather than by tuning.

**And it is why this segment matters beyond legibility.** Those two layers are precisely the two inputs the allocation controller reads. Put both on screen and the demo stops illustrating the idea and starts showing the mechanism.

---

## ⚠️ T0 — MEASURE

1. **`src/`** — expect `2005 / 2100`, `+0`. Fourth segment running. If the rendering needs something the core does not expose, **stop and report.**
2. **`dashboard/**/*.py`** — currently `76 / 1000`
3. **`dashboard/static/**`** — currently `246 / 1200`. **This is the segment that will move it most.** Project honestly; if the projection exceeds ~600 say so before writing, because that changes what segments 10–12 have left

---

## Tasks

### T1 — Entry 008's R1: test the JavaScript

Segment 8's Mutation B was two characters, browser-side, and **the entire Python suite passed.** The page showed *"0 edges changed this step"* on the exact step 25 roads broke, beside a picture of the break. 246 lines of JavaScript are currently guarded by two greps and a human reading output once per segment.

**`node` is admitted as a dev-only test dependency.** The decisive reason is not that JS testing would be nice — it is that **the node harness already exists and has been load-bearing for three segments.** Every "what the page actually renders" artefact in Entries 006–008 came from executing `app.js` under node. The project has been accepting evidence from a tool it refuses to version. This admits an instrument already in use.

Terms:

| | |
|---|---|
| **Scope** | `tests/` and `dashboard/` only. Nothing under `src/` may require it, ever |
| **Boundary, asserted** | A test proving the science surface is fully testable with `node` **absent** — same shape as `test_the_core_is_importable_and_usable_without_fastapi`: make it genuinely unavailable, then do real work |
| **Node missing** | Skip, with a reason **naming what is not being checked** |
| **`RUNBOOK.md`** | states node is expected for the dashboard suite |
| **The trap** | **A skipped test is not a test.** Report the skip count in this and every future close, qualified alongside the pass counts. A JS suite silently skipping is Mutation B's defect wearing a third hat |

**Move the harness into the repository.** It has been rewritten from scratch three times in a scratchpad; that is three chances to have rewritten it wrongly and validated nothing.

**Plus the guard that does not wait for a test run.** Every step in the payload carries its own `t`; the renderer asserts `step.t === t` before drawing and throws otherwise. Two lines. It catches Mutation B on the spot — **and it fires in the browser, in front of the examiner**, which no test suite can do.

### T2 — Report what the code actually emits

**Before designing anything**, paste the **real** event kinds from the core — the enum or literals, from source, with file and line.

`ARCHITECTURE.md` §15.4 names six: closure, traffic-up, traffic-down, deleted, added, reopened. **That is the document, not the code.** This project has been wrong about docs-versus-code before; the palette must be built on what actually arrives in the payload.

If the set differs from §15.4, **report the difference and design for the code.** Then say whether §15.4 should be corrected — that is a ruling for the Architect, not an edit for you.

### T3 — The state layer

Every road drawn at **its condition right now**. No history, no accumulation.

| Road's current condition | Drawn as |
|---|---|
| unchanged from `t=0` | faint grey, thin — the fabric |
| **dearer** than at `t=0` | warmer / darker, thicker in proportion |
| **cheaper** than at `t=0` | cooler / lighter |
| **closed** | **not drawn as a road.** A faint ghost, or nothing |
| **deleted** | **not drawn at all** |

That last pair does most of the decluttering on its own: a closed road is not a road, and drawing it as a loud red line is the picture insisting on something that is no longer there.

**Keep the state channel subtle.** Use lightness/opacity and width, **not** hue — hue belongs to events. Subtle-and-busy is legible; loud-and-busy is mud. If most roads end up visibly deviating late in the run, say so — that is a finding about the disruption model, not a styling problem to hide.

**Where the current price comes from — report this before writing.** If an event carries the resulting weight, the browser applies it: that is bookkeeping, not computation, and stays inside segment 8's rule. If it does not, **the server must send the per-step weights**, and you should say what that costs in payload. If neither is possible without touching `src/`, **stop and report.**

### T4 — The event layer

A **flash**: bright, thick, and it fades back to nothing over a short window.

**Colour = is this good or bad for me. Dash = can I use it.**

| Event | Line | Usable after? |
|---|---|---|
| got slower | **orange**, thick, solid | yes |
| got faster | **teal**, thick, solid | yes |
| new road added | **green**, thick, solid | yes |
| reopened | **green**, thick, dashed | yes |
| closed | **red**, thick, dashed | no |
| deleted | **dark red**, faint, dashed | never |

Adjust to what T2 actually reports. Two hard requirements on whatever you land on:

- **Every distinction must survive greyscale.** Red-closed against green-added is the standard red-green confusion; the dash pattern and weight must carry the meaning on their own, with hue as reinforcement rather than the sole channel. **Check this and say how you checked.**
- **Legible on a dark background at projector distance.** This is shown to an examiner across a room, not read at arm's length.

### T5 — The fade, and what its length should be

Events decay from full brightness back to nothing over a short window, so recent breaks dominate and old ones vanish. **Only that window's worth of events is ever on screen**, which is what makes accumulation structurally impossible.

**Report first, then choose:** does the `recency` signal have a decay constant or half-life in the config? If it does, **use that number** and say so on the page.

The reason is not tidiness. **Recency of disruption is the signal the entire allocation thesis rests on.** If the visual fade runs on the same constant, the examiner is watching the *actual signal the controller reads*, not a decorative animation. If no such constant exists, pick a window, **state the number and why**, and flag it for the Architect.

### T6 — Markers and legend

**Rudra's ruling: the goal is green.**

- **Goal — solid green.** It is the thing you are heading for
- **Start — white ring.** Neutral. **Not red** — red means *closed* in T4's palette, and a red start marker is the same self-collision as the current red goal
- Both in the legend

**The legend names events in plain words.** *"road closed"*, *"got slower"*, *"new road"* — never *"changed"*. It must also distinguish the two layers, because a viewer needs to know that a thick warm line means *this road is expensive now* while a flashing one means *this just happened*.

Also: **the blue optimal path stays on top of everything**, and stays the thickest line on screen.

### T7 — Tests

| Test | What it catches |
|---|---|
| **Every event kind the core emits maps to a defined visual class** | A seventh kind added later renders as a silent default and nobody notices |
| **No event kind maps to the same class as another** | The bug this segment exists to fix, pinned so it cannot return |
| **A closed or deleted road is not drawn as a usable road** | The decluttering rule, asserted |
| **The fade window bounds what is on screen** | After the window passes, an event contributes nothing. This is the anti-mud guarantee — assert it, do not trust it |
| **The state layer reflects the current price, not the history** | Two roads with the same current price look the same regardless of how they got there |
| **`step.t === t` guard throws when they disagree** | T1's guard, tested |
| **The JS suite runs under node, and skips loudly without it** | T1 |
| **The science surface is testable with node absent** | T1's boundary |

### T8 — Mutations — two required, one of them yours

**Specified:** collapse two event kinds to the same visual class — closed and added, the opposite pair. That is the bug this segment fixes, reintroduced. Paste the failure.

**Yours: pick something the weak version of a test would wave through.** Entry 007 made this standing, and Entry 008's uncommissioned mutation is the reason the JS is being tested at all. Report anything you expected to be caught that was not — that remains the most valuable thing you can report.

### T9 — Show it

Three frames, executed and pasted, not described:

1. **A quiet step** — the state layer alone. Is the fabric still readable?
2. **A heavy disruption step** — flashes at full brightness over the state layer
3. **`t = 59`** — the frame that used to be mud. **Say plainly whether it is now readable**, and how many edges are lit compared with the 244 before

Then: **is there room on this canvas for four more coloured paths?** Segment 11 puts the arms here and inherits your answer.

### T10 — Commit

Whole tree. **Do not push.**

```
segment 9: two layers — state and event (phase 1)

Splits what the picture shows into a road's current condition, which
persists, and a disruption, which flashes and fades. One channel was
carrying both, so "a road closed" and "a new road appeared" — opposite
events — rendered identically, and touched edges accumulated until 244 of
735 were lit.

The state layer draws every road at its current price in a subtle channel;
closed and deleted roads are not drawn as roads. The event layer flashes in
six kinds distinguished by hue and dash together, so the distinctions
survive greyscale, and fades over a bounded window, which makes
accumulation impossible rather than merely unlikely. The fade runs on the
recency signal's own constant where one exists, so the picture shows the
signal the allocation controller reads.

Goal is green and start is a white ring, neither colliding with the event
palette. The legend names events in plain words rather than "changed".

Also lands Entry 008's R1: node is admitted as a dev-only test dependency,
the render harness moves out of the scratchpad into the repository, and the
renderer asserts its step index before drawing — the two-character
browser-side mutation that the entire Python suite passed.

Spec + findings: currentWorkFlow.md
Log: WORKFLOW_LOG.md entry 009
```

---

## Constraints

| | |
|---|---|
| **Zero statements added to `src/`** | Stop and report |
| **The browser computes no quantity** | It applies weights it was given and renders. It does not derive a price |
| **`node` is confined to `tests/` and `dashboard/`** | The science surface must be fully testable without it, asserted |
| **Hue is never the only channel** | Every distinction survives greyscale |
| **Bounded fade window** | Nothing accumulates without limit |
| **Closed and deleted roads are not drawn as roads** | |
| **Do not modify `/api/graph` or `/api/graph/geometry`** | Both pinned. Add, do not edit |
| **No pickers** | Segment 10. Resist it |
| **No arms** | Segment 11 |
| **New dependency: `node` only** | |
| **Do not push** | |

---

## Acceptance check

```bash
git diff --stat -- dashboard/ tests/ RUNBOOK.md pyproject.toml
git diff --stat -- src/                          # expect EMPTY
./.venv/bin/pytest -q -m "not slow"              # report passes AND skips
./.venv/bin/ruff check src/ tests/ dashboard/
./.venv/bin/pytest -q -k "statement or budget" -s
grep -rn "schedule\[" dashboard/ --include=*.py --include=*.js   # expect NONE in code
./.venv/bin/python -m dashboard.server           # then look at t=0, a heavy step, t=59
git log --oneline -2 && git status --short --branch | head -1
```

**Expected:** `src/` empty · all pass, **skips reported and explained** · lint clean · three budgets with projections · no re-derived indexing · commit on top, ahead 1, unpushed.

**Paste verbatim:**

1. **T0** — projection then actual, all three, and what segments 10–12 have left
2. **The real event kinds from the code**, file and line, and any divergence from §15.4
3. **Where the current price comes from** — event payload or server-sent weights, and the cost
4. **The fade window** — the recency constant if one exists, or your number and your reason
5. **The three frames**, and the `t=59` edge count against 244
6. **Both mutations**, and anything that slipped through
7. **The greyscale check** — how you did it, and the result
8. **Room for four arm paths?** — your honest answer

---

## Definition of done

All checks pass, eight artefacts pasted, commit exists unpushed, FINDINGS appended.

**After this the picture tells the truth about what happened, and keeps telling it at t=59.** Segment 10 hands Rudra the controls.

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->

---

# FINDINGS — Segment 9

## 1. T0 — three surfaces, projection then actual

```
surface                    projected        actual      delta
src/                      2005  (+0)    2005 / 2100      +0
dashboard/**/*.py           76  (+0)      76 / 1000      +0
dashboard/static/**       ~520 (+274)    361 / 1200    +115

   app.js     178      headroom: python 924
   model.js    81                static 839
   index.html  52
   style.css   50
```

**`src/` did not move — fourth segment running — and neither did the Python.**
Everything this segment needed was already in the payload; the only new server-
side artefact is a static data file. I projected ~274 static lines and added
115, over-projecting because I budgeted for per-frame classification that
became one precomputed pass plus a data file.

**Segments 10–12 have 839 static lines and 924 statements left.**

**One gap in the instrument, reported not fixed.** `_static_files()` globs
`.js`, `.css` and `.html`. The new `palette.json` — 12 lines, and the single
source of truth for the entire event encoding — is **not counted by the static
budget**. It is immaterial to the cap (373 either way) but material to the
instrument's honesty, which is the exact F5 shape Entry 008 R1 was about. The
counting rule is the Architect's; flagging rather than widening it.

## 2. The real event kinds, from the code

```python
# src/dynaswarm/core/events.py:33
KINDS = ("closure", "traffic_up", "traffic_down", "reopen", "delete", "add")
```

**No divergence from §15.4 in substance.** Six kinds, and they are the same six
the document names — `traffic-up`/`traffic_up`, `deleted`/`delete`,
`added`/`add`, `reopened`/`reopen` differ only in prose-versus-identifier
spelling. §15.4 needs no correction; the naming is the document writing English
where the code writes Python. Reported as required rather than assumed.

**Two facts from the source that the document does not carry, and that changed
the design:**

```python
# events.py:76 — apply_event
if event.kind in ("closure", "delete"):
    active[slot] = False; active[rev] = False
elif event.kind in ("reopen", "add"):
    active[slot] = True; active[rev] = True; weight[...] = event.new_weight
else:  # traffic_up / traffic_down
    weight[slot] = event.new_weight; weight[rev] = event.new_weight
```

**Closure and delete are mechanically identical** — the module docstring says so
outright: *"Under an active-mask representation they are the same operation …
Both labels are retained so event-type breakdowns stay faithful to the brief."*
So the visual distinction T3 asks for (closed → ghost, deleted → nothing) is a
presentation choice on top of one mechanism, not two mechanisms. I implemented
it by carrying the causing `kind` forward in the state ledger, and the code says
which of the two it is rather than implying the engine distinguishes them.

**`new_weight` is meaningless for closure and delete** — `_new_weight` falls
through to `return old` for both (`timeline.py:184`). Harmless here, because a
closed road is not drawn as a road and its price is never read, but it is a
field that looks informative and is not.

## 3. Where the current price comes from — reported before writing

**The event payload already carries it. No server change, no new field, no
per-step weight arrays, no `src/` touch.** Every price the state layer shows is
`event.new_weight`, which the core computed; the browser replays the stream.
That is bookkeeping, inside segment 8's rule.

**Verified before relying on it, against the core, exhaustively:**

```
checked 47325 (edge, t) pairs across 60 frames, mismatches 0
```

Every edge, every timestep: `model.js`'s reconstructed `{price, active}` equals
`GraphTimeline.state_at(t)`'s `weight[slot]` and `active[slot]` exactly. Not
approximately — zero mismatches at 1e-9. The alternative would have been
sending 735 weights × 60 steps (~1.7 MB against the current 34 KB), so this is
also the only affordable option; it being *correct* is what makes it usable.

## 4. The fade window — the recency signal's own constant

**It exists, and I used it.**

```python
# src/dynaswarm/control/signals.py:204
def __init__(self, window: int = 10, decay: float = 0.7) -> None:
```

`decay = 0.7`, and grepping `conf/`, `config.py` and `control/` shows **no
config anywhere overrides it** — so 0.7 is not merely the default, it is the
operative constant everywhere `RecencySignal` is constructed.

`model.js` exports it as `RECENCY_DECAY = 0.7`, and a flash's opacity is
`0.7 ** age` — the identical curve to `RecencySignal.observe`'s
`self._value * self._decay`. **The fade on screen and the signal the allocation
controller reads are the same number.** Watching a flash die out is watching
the signal die out, which is what T5 was asking for.

The cutoff at **13 steps** is mine, derived rather than picked: `0.7**13 ≈
0.0097`, the first age below 1 %, past which another frame of fade is not
distinguishable from zero.

```
age:  1     2     3     5     8     11     13
val: 0.70  0.49  0.34  0.17  0.058  0.020  0.0097
```

## 5. The three frames

Executed through the now-versioned harness, not described:

```
=== t = 0  (quiet — state layer alone) ===
  t = 0 / 59      optimum 99.96      hops 11      0 edges changed this step
  state layer : 735 roads drawn  (0 salient, 735 baseline fabric)
  ghosts      : 0        event layer : 0 flashes        path : 11 segments

=== t = 2  (heavy disruption — 25 events land) ===
  t = 2 / 59      optimum 99.96      hops 11      25 edges changed this step
  state layer : 735 roads drawn  (25 salient, 710 baseline fabric)
  ghosts      : 0        event layer : 25 flashes, 1 fade level   path : 11

=== t = 59  (horizon — the frame that used to be mud) ===
  t = 59 / 59     optimum 103.25     hops 11      0 edges changed this step
  state layer : 744 roads drawn  (92 salient, 652 baseline fabric)
  ghosts      : 50       event layer : 75 flashes, 3 fade levels  path : 11
```

**`t = 59` is readable, and the number that matters is 244 → 142.**

92 edges deviating in price, plus 50 closure ghosts, against **244 lit before**.
16 deleted roads are drawn as nothing at all.

**The reduction is semantic, not cosmetic, and that is the finding.** Segment
8's 244 counted every edge *ever touched* — an edge that went up at `t=12` and
came back down at `t=30` stayed amber to the horizon. The state layer only
lights what **currently** deviates, so a road that recovered goes quiet, which
is the truth about it. Recolouring alone would have moved nothing.

The event layer at `t=59` holds 75 flashes across 3 fade levels — the
disruptions at `t=47`, `54` and `57`, at opacities 0.014, 0.168 and 0.49. The
`t=47` set is effectively invisible, which is the window doing its job: nothing
older than 13 steps can contribute at all.

**Colour is the sharper comparison.** Before, all 244 were the same amber and
competed equally for attention. Now the 142 state marks are neutral greyscale
and only the event layer carries hue, most of it fading — so *things shouting in
colour* went from 244 to about 50.

## 6. Both mutations

### Specified — collapse two opposite kinds onto one class

`closure` given `add`'s `cls`, `dash` and `color` in `palette.json`.

```
not ok 3 - no two kinds share a visual class
        a class collision would let two opposite events look identical
not ok 4 - no two kinds share a dash pattern — the greyscale guarantee
        a shared dash pattern would rely on hue alone
# pass 19  # fail 2
```

Caught twice, and by the two different guarantees it breaks at once.

### Mine — the state layer reverted to segment 8's semantics

One expression: light an edge if it has *ever* been touched, rather than if its
price currently deviates.

```javascript
- const ratio = entry.price / baselinePrice;
+ const ratio = entry.changedAt >= 0 ? 2.0 : entry.price / baselinePrice;
```

```
not ok 1 - two edges landing on the same current price look the same
           regardless of path taken
        + opacity: 0.37     - opacity: 0.12
```

Caught by the unit test named for exactly that property.

### What slipped through, and it is the one worth reading

**The integration test that is nominally the anti-mud guard passed this
mutation.** Under it, salient edges at `t=59` went **92 → 178** (228 including
ghosts) — a 93 % regression back toward the mud this segment exists to remove —
and `t=59 has fewer salient edges than the old mud figure of 244` **passed**,
because 228 < 244.

I had asserted against **the figure I was improving on**. A threshold set at the
old bad value cannot detect anything short of total failure, and it is a
comfortable number to write precisely because it always passes.

Tightened to `< 160`, just above the achieved 142, and re-run under the same
mutation:

```
not ok 4 - 228 salient edges at t=59; the two-layer split achieves 142
```

Renamed too — its name still advertised the 244 it no longer asserts.

The general form, since this is the third segment in a row where a test I wrote
promised more than it checked: **a threshold copied from the state you are
leaving behind is not a guard, it is a memento.**

## 7. The greyscale check — how, and the result

Computed WCAG relative luminance for each palette colour, fully desaturated,
then ranked every pair by how close they land:

```
  traffic_up     #c47f00  L=0.2691   dash=none    w=2.4
  traffic_down   #17a673  L=0.2869   dash=1 4     w=2.4
  add            #2fae5a  L=0.3161   dash=8 3     w=2.4
  reopen         #2fae5a  L=0.3161   dash=4 2     w=2.4
  closure        #e5484d  L=0.2183   dash=2 2     w=2.4
  delete         #7a2b2e  L=0.0606   dash=1 6     w=1.0

Closest pairs — where hue alone would fail:
  add        vs reopen        ΔL=0.0000  '8 3' vs '4 2' -> separated by dash
  traffic_up vs traffic_down  ΔL=0.0178  'none' vs '1 4' -> separated by dash
  traffic_down vs add         ΔL=0.0292  '1 4' vs '8 3' -> separated by dash

distinct dash patterns: 6/6
=> every kind is identifiable with colour fully removed.
```

**The check justified the design rather than confirming it.** `add` and
`reopen` are the *same hex colour* — ΔL exactly 0 — and `traffic_up` against
`traffic_down` is ΔL 0.018, which is nothing. Three pairs would be
indistinguishable to a greyscale or red-green-colourblind viewer if hue were
doing the work.

So every kind carries a **unique dash pattern**, and that is the primary
channel; hue is reinforcement. `no two kinds share a dash pattern` is asserted
in the suite, so a future palette edit cannot quietly reintroduce the collapse.

## 8. Room for four more coloured paths?

**Yes, and the headroom is real, but it is in the hue channel specifically.**

The state layer is now entirely greyscale — 652 of 744 roads at `t=59` are
baseline fabric at 0.12 opacity, and the 92 salient ones vary only in lightness
and width. **Hue is unoccupied except by the event layer**, which is bounded to
13 steps and is mostly faded at any given frame.

Segment 11 gets: four arm paths, plus the blue optimum which must stay topmost
and thickest. Three constraints I would hand forward —

1. **The arms need four hues that do not collide with the six event hues**
   (orange, teal, green, red, dark red — plus blue for the optimum). That is
   seven taken. Feasible but not roomy; purple/magenta/cyan/yellow is about
   what remains, and yellow against orange is already marginal.
2. **The same greyscale rule will apply to the arms** and there is no dash
   channel left to give them — dashes now mean event kind. Arms will need
   width, or a stroke pattern that is clearly not one of the six.
3. **48 of 60 steps are still quiet.** Entry 008 flagged this and it remains
   unaddressed; four arms moving through 48 uneventful frames is worse than one
   path doing it, not better. A jump-to-next-event control is now the single
   highest-value thing the demo is missing.

## 9. Acceptance — all eight

| # | Check | Result |
|---|---|---|
| 1a | In scope | 14 files, +741 −104 |
| 1b | `git diff --stat -- src/` | **Empty** |
| 2 | Suite | **347 passed, 0 skipped** full · **342 passed, 5 deselected** not-slow |
| 3 | Lint, three trees | `All checks passed!` |
| 4 | Three budgets | 8 passed — 2005/2100 · 76/1000 · 361/1200 |
| 5 | No re-derived indexing | Two `schedule[` hits, both in `server.py`'s docstring quoting the contract; none in code, none in any `.js` |
| 6 | JS suite | **21 passed** under node, 0 failed |
| 7 | It runs | `palette.json`, `model.js`, `/` all HTTP 200 |
| 8 | Committed, not pushed | Below |

**Skip count, qualified per Entry 008 R1: 0 skipped.** `node` was present, so
`dashboard/static/*.js` was genuinely tested this run — 21 assertions across
`model.js` and the real `app.js`, not a green tick standing in for one.

## Deviations from spec

**1. The event layer's dash patterns are all six distinct, not solid-versus-
dashed.** T4's table implies a binary (`solid` for traffic, `dashed` for the
rest), but that leaves `traffic_up`/`traffic_down` and `add`/`reopen`
distinguished by hue alone, which §7's measurement shows fails outright in
greyscale. Six distinct patterns satisfies the hard requirement; the table's
hues are kept exactly as specified.

**2. State-layer direction is encoded as salience, not warm-versus-cool.** T3's
table says "warmer / darker" for dearer and "cooler / lighter" for cheaper, but
the constraint beneath it says lightness and width, **never hue**. I read the
constraint as binding and the adjectives as illustrative: dearer roads become
brighter and thicker, cheaper roads recede toward the background. That also
means salience tracks how much a road should worry you, which seems the right
thing for the eye to be drawn to.

**3. `app.js` and `model.js` are ES modules**, so `index.html` uses
`<script type="module">`. The split is what let 15 of the 21 JS tests run with
no DOM shim at all, against real imported functions.

## Surprises

**`node --test <directory>` is not portable.** This machine has three node
installs; the JS suite passed under nvm's v20 and failed under homebrew's v25
with `test at tests/js:1:1 — 'test failed'` and no subtest detail whatsoever.
The cause is that directory discovery globs differently across versions. The
Python side now globs `*.test.mjs` itself and passes explicit paths, which
passes under both. Had I only ever run it one way, this would have surfaced as
an unreproducible failure on someone else's machine.

**`pytest -q` in this repo means `-qq`.** `addopts` in `pyproject.toml` already
contains `-q`, so passing it again suppresses the summary line entirely — no
"N passed", just dots and a clean exit. I spent real time treating a missing
footer as a hung test or a broken reporter. Every acceptance block in this
document says `pytest -q`; it should say `pytest`.

**Stripping one `node` from `PATH` does not make node unavailable.** The
boundary test initially removed only the directory `shutil.which` returned and
believed it had succeeded — while two other installs remained reachable. It now
removes every `PATH` entry containing a `node` executable and asserts the
absence before proceeding. A test that believes it has removed a dependency and
has not is the same failure as a skipped test that reports as passing.

## Could not do

Nothing was blocked.

## Questions for the Architect

1. **`palette.json` is uncounted by the static budget** (§1). Widen
   `STATIC_SUFFIXES` to include `.json`, or is the budget deliberately about
   code rather than data?
2. **Hue is nearly exhausted before the arms arrive** (§8). Seven hues are
   committed; segment 11 needs four more that survive greyscale, with the dash
   channel already spent on event kinds. Worth deciding the arm encoding now,
   at the same time as the palette, rather than discovering the collision in
   segment 11?
3. **The quiet-step problem is now two entries old** (§8.3). Is jump-to-next-
   event segment 10's, segment 11's, or its own small task?

---

# FINDINGS — Segment 9, addendum: two defects Rudra found in the delivered page

Reported by Rudra immediately after the commit, from one screenshot of the
legend. Both are mine, both were in the delivered artefact, and **both had a
test that should have caught them and did not.**

## Defect 1 — a legend row reading "undefined"

`palette.json` carried its `_comment` in the same namespace as the six kinds,
and `buildLegend` iterated `Object.values(palette)` without filtering. The page
rendered a seventh row with no colour and the label `undefined`.

**Why the test missed it.** My own legend test contained:

```javascript
for (const entry of Object.values(fixtures.palette)) {
  if (typeof entry !== "object" || !entry.label) continue;   // <- skipped it
```

That line **skips the exact entry that was breaking the page.** The test walked
past the bug it existed to catch, because I wrote the filter to make the loop
work rather than asking why an entry had no label.

## Defect 2 — three legend swatches identically green

The swatches were solid colour blocks. `add` and `reopen` are **the same hex
colour**, and `traffic_down` is a near neighbour — the whole greyscale argument
in §7 rests on the *dash pattern*, and the legend showed none of it. The one
place a viewer learns the encoding was teaching them that three different
events are the same event.

I measured that hue collision in §7 of these findings, wrote "dash is the
primary channel", and then built a legend that displays only hue.

## Defect 3 — a test I designed, described, and never wrote

While planning I specified a Python test asserting `palette.json`'s keys equal
`dynaswarm.core.events.KINDS` exactly — the cross-language seam, since the JS
cannot import the Python tuple. **It does not exist in the segment 9 commit.** I
described it in reasoning and moved on.

It is the test that would have caught defect 1 outright: `_comment` was a key in
the kind namespace, and an exact set comparison against `KINDS` fails on it
immediately.

## What changed

**Structural, not a patch.** The kinds are now nested under their own key:

```json
{ "_comment": "...", "kinds": { "traffic_up": {...}, ... } }
```

so metadata **cannot** be mistaken for a kind by a consumer that forgets to
filter. Filtering-by-convention across three separate consumers was the actual
defect; removing one stray row would have left it in place.

**The legend swatch is now a real `<svg><line>`** carrying the kind's actual
`stroke`, `stroke-width` and `stroke-dasharray` — the same attributes the map
draws, so the legend and the picture cannot disagree.

**Four tests added or repaired:**

| Test | Catches |
|---|---|
| `test_palette_covers_exactly_the_cores_event_kinds` | the missing seam — palette keys vs `KINDS`, exact set equality, plus every field present and every label non-empty |
| `test_the_fixture_palette_matches_the_shipped_one` | the JS fixture drifting from the file the page actually serves |
| legend test, repaired | row count must equal kind count, and no row may read `undefined` — the lenient `continue` is gone |
| `each legend swatch carries its kind's real dash pattern` | a swatch that shows hue but not dash |

**Both defects reintroduced and confirmed caught:**

```
BUG A (metadata rendered as a row):  legend row count does not match the kind count   # fail 2
BUG B (solid swatches, no dash):     not ok 7 - each legend swatch carries its
                                                kind's real dash pattern              # fail 1
restored, byte-identical                                                              # pass 22
```

## Counts

**349 passed, 0 skipped** (was 347). JS suite **22 passed** (was 21). Lint
clean. `src/` diff empty. `dashboard/static/` **369 / 1200**.

## The pattern, stated because it is now four segments old

Segment 7: a test named for an invariant that only checked array lengths.
Segment 8: 246 lines of JavaScript with no tests at all.
Segment 9: a threshold asserted against the value I was improving on.
Segment 9 addendum: a test whose filter skipped the entry that was broken, and
a test I designed and never wrote.

Every one is the same failure — **the test was written to pass, not to fail on
the thing it names.** The mutation step catches these when I choose the right
mutation; it did not catch these two, because I mutated the renderer and the
palette semantics and never mutated *the legend*. Rudra found them by looking at
the screen, which is the one instrument I do not have.

**The one that would have helped: render the page and read it, every segment,
as an artefact — not only assert about it.** §5's three frames report element
counts, all of which were correct while the legend beside them was wrong.
