# SEGMENT 11 — Race the Arms

**Phase 1 · See it · Segment 6 of 7**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` **§15.2 (the hard constraint), §15.5, §15.7**, §9 (arms and display names), §10 (harness and fairness), §12 (run provenance), §2.3. `WORKFLOW_LOG.md` **Entry 010** carries R1–R4, which are tasks here.
> Append your findings to the **bottom** of this file.
>
> ## ⛔ RULE CHANGE — YOU DO NOT COMMIT ANY MORE
>
> **From now on Rudra commits, not you.** He does not want agent-authored commits in his repository's history. That is his call about his own project and needs no justification.
>
> This **supersedes T9 below and every commit step in every earlier segment.** At the end: leave the work unstaged, paste `git status --short`, and paste the commit message as a copyable block **with no `Co-Authored-By` trailer**. No `git add`, no `git commit`, no `git stash`, never `git add -A`. Reading history is still fine.
>
> `AGENT_PROTOCOL.md` carries this permanently.

---

## Goal

**Put the optimizers on screen, racing.** Four panes, same graph, same timestep, synchronised — each drawing that arm's current best path, with A\* drawing the truth. Below them, excess over time, one line per arm, with disruption markers.

Everything built so far *describes*. **This segment is the first that RUNS something.** That changes the risk profile entirely, and most of this spec is about that.

---

## The three things that make this segment different

**1. It executes a real trial, through the same door the CLI uses.**

§15.2 is not advisory: *"Drives runs through `run_trial()` — the same entry point the CLI uses. It configures and calls; **it never steps a loop itself**."* If the dashboard drives its own trial loop, it becomes a second harness, and every number it shows is from an experiment nobody else ran. **If `run_trial()` cannot be called with what you have, stop and report** — do not assemble the loop by hand.

**2. It writes to disk, so provenance stops being theoretical.**

A dashboard-driven run **writes a normal run directory, indistinguishable from a CLI run, stamped `run_class: exploratory`** (D30, D31). This is the first time the provenance system built in Phase 0 is exercised by anything. Get it wrong and scratch runs become evidence — the exact failure `run_class` exists to prevent.

**3. Configure → run → observe. Never run → tweak → continue.**

§15.2's hard constraint. No dashboard-specific parameter may enter a run; nothing may mutate a run in flight. The controls are locked while a run executes, or they are not controls, they are a way to produce an unreproducible result.

## Which arms — and which are barred

**Race the four uncontrolled arms: `astar`, `aco`, `pso`, `hybrid`.**

**Do not race any controlled arm.** F7 is open: `harness/arm.py:228` builds the prescheduled controller with no arguments, so `start == end == 1.0` and it varies nothing while logging itself as active. F4 is open too. Both are Phase 3's to fix.

A demo that showed an adaptive arm today would show **a controller that is known not to control**, and it would look exactly like a real result. That is the F5 failure mode — a flattering number nobody interrogates — staged in front of an examiner.

Use §9's **display names**, not the internal keys.

---

## ⚠️ T0 — MEASURE, and split the static budget first (Entry 010 R1)

The budget splits, on the same reasoning that split Python from static. Implement, then measure.

| Budget | Question | Cap |
|---|---|---|
| `static/**/*.js` | **Has the dashboard become an application?** | **700** |
| `static/` `.html` + `.css` + `.json` | Has its surface sprawled? | **900** |

Behaviour is what deserves the tight bound. Prose and presentation get a ceiling so they cannot hide growth, but not the same one — **the control guide does not compete with the pane grid for room.**

Report both opening figures and both closing figures, plus `src/` (expect `2005 / 2100`, `+0`, sixth segment) and `dashboard/**/*.py`.

---

## Tasks

### T1 — Entry 010's small rulings

- **R1** — the budget split above
- **R2** — **drop the "runs on disk" panel.** Your argument was accepted: with the D32 banner gone it is a bare count with nothing to click. It returns when the dashboard can load a run, in Phase 4

### T2 — Report the run surface before building against it

Paste, **from source**: `run_trial()`'s real signature, what it returns, what it writes and where, how `run_class` is stamped, and the registered arm keys with their §9 display names.

If anything Stage 3 needs is not reachable through that entry point, **stop and report.** §2.3 says the core exposes it — that is a ruling to be made, not a gap to route around.

### T3 — Stage 3: the controls

Tick arms, set the evaluation budget, **Race**. One real trial through `run_trial()`.

`POST /api/run` per §15.7, returning a **run id**.

**A note on statelessness, because this genuinely differs from segments 10's rule.** A graph is a pure function of its parameters, so its id is derived. **A run is not** — it is an artefact on disk with a real location. So the run id names a run *directory*, and `GET /api/run/{id}/steps` reads that directory back. That is a file, not server memory: restart the process and the run is still there. Say plainly which of the two kinds each id in the API now is.

**Lock the controls while a run executes.** Report the wall-clock for the default configuration. If it exceeds ~10 s, **say so and propose** — do not build streaming or progress machinery unasked, but do not let the page appear frozen and lie about it either.

### T3b — Two things Rudra asked for directly

**Both are about the page telling the truth about its own state**, which is the same discipline as everything else in this project, applied to the interface.

**1. Pending feedback on `Generate`, `Build` and `Race`.**

Today a click produces nothing visible until the work finishes, so Rudra cannot tell a running build from an ignored click and clicks again. A second click on a running build is either wasted work or a race, and neither should be reachable.

- the button **disables itself** for the duration and says what it is doing
- the affected panel reads as busy — the stale figures beside it must not look current
- **on failure the page says so**, in the error channel that already exists
- **`Race` needs this most**, since a trial is the only thing here that is not near-instant

No spinner library, no new dependency. The requirement is that **the page never shows a state it is not in.**

**2. Open empty. Do not auto-generate a world on load.**

The page currently arrives with a graph already built, which reads as *"here is a thing"* rather than *"build a thing"* — and it silently spends a decision Rudra was given controls to make. First load should show the empty canvas and a short line naming what this is and the two steps to start: **Generate**, then **Build**.

One sentence, not a paragraph. The reference section below already explains everything else.

**This will break tests that load the page and expect a rendered graph** — several JS tests do. That is the change working as intended: those tests were asserting an auto-generate that is now gone. Update them to drive Generate explicitly, which is closer to what a user does anyway, and **say which ones you changed and why** rather than folding it into a diff.

### T4 — The pane grid

**One pane per arm, same graph, same timestep, synchronised.** Each draws that arm's current best path; the A\* pane draws the true optimum.

**Position carries arm identity, not hue** (Entry 009 R1). Every pane may draw its path in the same colour, because a pane is unambiguous. Do not spend the event palette on arms.

**A pane must be readable at quarter size.** At 200 nodes and 735 edges it will not be, if it carries everything the main canvas carries. **Drop layers until it is, and say which you dropped and why** — my expectation is that panes carry the state layer and the arm's path only, with the event layer staying on the main canvas, but decide from what you actually see and justify it.

**This is where correctness becomes visible.** §15.5: *"a path failing to reach the goal shows up instantly, in whichever arm."* A pane whose path stops short is a defect you can point at. Make sure a broken path reads as broken rather than as a short path.

### T5 — Excess over time

Full width, below the grid. One line per arm, disruption markers along it.

**This is the chart the project's claims are made from**, so:

- **Hue is spent here, and only here.** Four categorical colours on their own ground, no event palette competing. They must survive greyscale — same standard as segment 9, and say how you checked
- **Excess comes from the analysis layer, computed from the run's own output.** Not recomputed in the browser, not derived from the panes. If `analysis/` already computes excess, call it
- Disruption markers use `events_at()`. **Never a re-derived index** — F1's rule, in a new place

### T6 — Tests

| Test | Catches |
|---|---|
| **The dashboard calls `run_trial()` and does not step a loop** | §15.2. Assert the entry point, not the outcome |
| **A dashboard run writes a real run directory stamped `exploratory`** | D30/D31. Load it back with `load_steps` and check the class |
| **A dashboard run is indistinguishable from a CLI run** | Same schema, same columns. **The strong one** |
| **The excess shown equals the analysis layer's own figure** | The anti-reimplementation test for this segment |
| **Every arm sees the identical timeline** | §10's fairness guarantee, asserted from the dashboard's side |
| **Controls are locked during a run** | The configure → run → observe constraint |
| **A run id survives a process restart; a graph id needs no process at all** | The two id kinds, pinned |
| **No controlled arm is reachable from the UI** | F7's blast radius, closed by test rather than by intention |

### T7 — Mutations, two, and the new standing rule

**Entry 010's rule is now in force:** *an invariant test written only against correct data cannot tell a real invariant from a tautology.* **Every invariant test in this segment must be shown failing against deliberately corrupted input, and the corruption pasted.** A green invariant test proves nothing until it has been seen red.

**Specified:** have one arm's pane read another arm's path. Same graph, same shape, plausible on screen — and the excess chart would still show four distinct lines. If that passes, the panes are decorative.

**Yours.** Entry 009's and 010's uncommissioned mutations both found real defects; the commissioned ones only confirmed predictions.

### T8 — Show it, and look at it

**Screenshot before handing back — this is now standing.** Entry 010: a width change to an invisible colour measured as done and read as nothing. Any visual claim comes with a screenshot you have looked at.

1. The grid at a quiet step and at a heavy disruption step
2. The excess chart across the full run
3. **Is a pane readable at quarter size?** Your honest answer
4. Wall-clock for the default race
5. **The empty first-load state**, screenshotted
6. **The pending state** on a running Race, screenshotted — the one place it matters most
5. The run directory: path, `run_class`, and `load_steps` reading it back

### T9 — Hand over, do **not** commit

**Rudra commits from now on.** See the banner at the top of this file and `AGENT_PROTOCOL.md`.

Leave everything unstaged. Then paste, in this order:

1. `git status --short` — every file you touched, so he can see the shape of it
2. The commit message, as a fenced block he can copy straight out. **No `Co-Authored-By` trailer**
3. One line confirming the segment is complete and uncommitted

If you find yourself about to run `git add` or `git commit`, that is the instruction firing — stop.

---

## Constraints

| | |
|---|---|
| **Zero statements added to `src/`** | Stop and report. Sixth segment |
| **`run_trial()` or nothing** | The dashboard configures and calls; it never steps a loop |
| **Every dashboard run is `exploratory`** | D30/D31 |
| **Configure → run → observe** | Controls locked in flight; no dashboard-only parameter enters a run |
| **No controlled arms** | F7 and F4 are open. Phase 3 |
| **Position carries arm identity on the graph; hue only in the chart** | |
| **Excess comes from `analysis/`** | Not from the browser, not from the panes |
| **`events_at()` for every marker** | |
| **Budgets: JS ≤ 700, presentation ≤ 900** | |
| **The page never shows a state it is not in** | Pending is visible; failure is visible; nothing stale reads as current |
| **No auto-generate on load** | The page opens empty and asks |
| **Do not commit, and do not push** | Rudra does both. Leave the tree unstaged and paste the message for him |

---

## Acceptance check

```bash
git diff --stat -- dashboard/ tests/ && git diff --stat -- src/   # src EMPTY
./.venv/bin/pytest                                                # passes AND skips
./.venv/bin/ruff check src/ tests/ dashboard/
./.venv/bin/pytest -k "budget or statement" -s                    # four numbers
grep -rn "schedule\[" dashboard/ --include=*.py --include=*.js    # none in code
git status --short          # your changes, UNSTAGED and UNCOMMITTED
```

**Paste verbatim:** T0's four figures with projections · `run_trial()`'s real surface · the two id kinds · both screenshots · the run directory and its class read back · every invariant test **shown red** against corrupted input · both mutations · pane legibility, honestly.

---

## Definition of done

Checks pass, artefacts pasted, screenshots looked at, **work left uncommitted with the message pasted for Rudra**, FINDINGS appended.

**After this Rudra watches his three algorithms chase a moving optimum, with the truth drawn beside them.** Segment 12 lets him click into it.

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->

---

# FINDINGS — Segment 11

## 1. T0 — four surfaces

```
                      opening    projected     closing
src/                 2005/2100    2005 (+0)   2005 / 2100   +0   ← sixth segment
dashboard/**/*.py     129/1000     ~185        172 / 1000  +43
static/**/*.js        414/700      ~600        552 / 700  +138   ← 148 left
presentation          552/900      ~620        599 / 900   +47   ← 301 left
```

**The split was the right call and it shows immediately.** Under the old
single 1200 the page would now stand at 1151 — 49 lines from the wall, with
segments 12 and 13 unbuilt. Split, the pressure is where it belongs: the
control guide is not competing with the pane grid.

**JS is the binding surface: 148 lines for segments 12 and 13.** Segment 12 is
click-to-inspect, which is interaction code. Worth a projection before it is
written.

## 2. The run surface, from source

```python
run_trial(cfg: Config, trial: int, arm_names: list[str],
          seeds: list[int] | None = None,
          preserve_connectivity: bool = True) -> TrialOutcome
# TrialOutcome: steps: list[StepRow], events: list[EventRow]
```

**`run_trial` does not write.** Writing is `run_experiment`
(`harness/runner.py:25`), which calls `run_trial` per trial and streams
through `ResultWriter` — and it is what `cli.py:58` calls. **The dashboard
calls `run_experiment`**, which satisfies "never steps a loop itself" and is
strictly better for T6's strong test: what lands on disk is shaped by the same
function that shapes a CLI run, not by anything in `dashboard/`.

**`run_class` is stamped inside `run_trial`** from `cfg.run_class`
(`trial.py:162, 219`), onto every row. Setting it on the `Config` is the whole
mechanism; the dashboard sets `exploratory` and does not expose it as a
control, because offering one would hand a user the single mistake the
provenance system exists to prevent.

**Registered arms and their §9 display names** — eight exist, four are raceable:

| Code id | Display name | Raceable here |
|---|---|---|
| `astar` | A\* | ✅ |
| `aco` | ACO standalone | ✅ |
| `pso` | PSO standalone | ✅ |
| `hybrid` | Hybrid (baseline) | ✅ |
| `aco_fixed` / `aco_adaptive` | ACO, frozen ρ / adaptive ρ | ❌ F7 |
| `hybrid_fixed` / `hybrid_adaptive` | Fixed / Static Hybrid · New Recency-Based Adaptive Hybrid | ❌ F7 |

Nothing was missing. `src/` did not move.

## 3. The two kinds of id, stated plainly

| | Derived from | Needs | Survives a restart |
|---|---|---|---|
| **graph id** | `blake2b(model, n_nodes, density, seed)` | nothing at all | trivially — it is a function |
| **run id** | the run **directory's** name | that directory on disk | yes — it is a file, not a memory |

**A run is not a pure function of its parameters**, so it cannot be derived:
it is an artefact with a location. `GET /api/run/{id}` globs `outputs/*/{id}`
and reads it back. Still no server state — the server holds no registry, no
session and no cursor; it holds the same thing anyone with a shell holds,
which is a directory.

**No cache anywhere.** A whole race is 1.8 s and a whole world is 12 ms, so
there is nothing to evict, which is the cheapest possible guarantee that
evicting changes no answer.

## 4. Wall-clock

```
race: 1.8s -> outputs/2026-09-05/10-39-36 class=exploratory
  astar    mean_excess 0.0000
  aco      mean_excess 0.0200
  pso      mean_excess 0.3960
  hybrid   mean_excess 0.0046
```

**1.8 s at the default**, well inside the ~10 s threshold, so no streaming or
progress machinery was built. The pending state still exists, because 1.8 s is
long enough to click twice.

## 5. The panes — what was dropped, and whether it works

**Panes carry the state fabric and the arm's own route. Nothing else.**
Dropped from each pane: the event layer, the closure ghosts, the node dots and
the markers. At quarter size 735 edges plus flashes plus dots is texture with a
line somewhere inside it — and the one question a pane exists to answer is
*does this route reach the goal*, which none of those help with. The event
layer stays on the main canvas, which is full width and can carry it.

**Honest answer on legibility: yes, and the reason is the fabric drop to
0.07 opacity.** At the first attempt the fabric was the main canvas's 0.12 and
the routes were competing with it. In the screenshot the four routes read
clearly and PSO's wandering is visibly different from A\*'s directness — which
is the comparison the grid exists to make, visible without reading a number.

```
A*  +0.0%    ACO standalone  +3.0%    PSO standalone  +41.1%    Hybrid  +0.9%
```

## 6. The excess chart, and a hue collision I had to fix

**The four arm colours had a minimum greyscale gap of 0.033** on my first
choice — `aco` 0.529 against `hybrid` 0.496, indistinguishable desaturated.
Respread:

```
astar 0.932   aco 0.724   pso 0.527   hybrid 0.307     min adjacent gap 0.197
```

Six times the separation, and they now run light→dark so they order as greys.
Checked by computing perceived luminance, not by looking.

**And the disruption markers were amber — against PSO's orange.** `--warn`
`#c47f00` beside `#c9762b`. The markers were spending hue in the one place hue
is reserved for arms. Neutralised to `--ink` at 0.16.

Markers come from each step's own `events` array, which the server filled from
`events_at()`. No index is re-derived in the browser.

## 7. Every invariant test, shown red

Five by corrupting the source, two by corrupting the artefact.

```
1. dashboard steps its own trial loop
   E  AssertionError: the dashboard is stepping a trial loop

2. dashboard run stamped manifest
   E  AssertionError: assert 'manifest' == 'exploratory'

3. a CLI column dropped from the written run
   E  AssertionError: missing columns a CLI run would have: ['astar_expansions']

4. excess recomputed in the endpoint
   E  AssertionError: astar / assert 0.01 == 0.0 ± 1.0e-12

5. one arm shown a different world
   E  AssertionError: astar saw a different world

6. a controlled arm made raceable
   E  AssertionError: assert not ({...'hybrid_adaptive'} & {...'hybrid_adaptive'})

7. run id served from memory, not disk
   E  AssertionError: Traceback ... back = read_run('10-46-41')
```

**Tests 3 and 5 corrupt a written parquet at the Arrow level**, not through
pandas — a pandas round-trip mangles the `map<string,double>` `params`/`probe`
columns, and a fixture that differs from reality in a second way tests the
fixture (segment 5's lesson, in a new place).

**Test 5's first corruption did not fire and I nearly recorded it as caught.**
I bumped `num_events` at row index 10 where `arm == "aco"` — but the parquet
is not ordered arm-major, so that row does not exist. The corruption changed
nothing and the test passed. Fixed by finding the first `aco` row whatever its
index. **A corruption that does not corrupt is a green test wearing a
disguise**, and it looks exactly like success.

## 8. Both mutations

### A — specified: every pane reads A\*'s path

```javascript
-    const path = arm.paths[t] ?? [];
+    const path = state.race.arms[0].paths[t] ?? [];
```

```
not ok 1 - each pane draws its OWN arm's route
    pane 1 (ACO standalone) drew a route of the wrong length
    expected: 11   actual: 12
```

The excess chart still showed four distinct lines throughout, exactly as the
spec predicted — the chart reads a different field, so it cannot notice.

### B — mine: a broken route can never read as broken

```javascript
-    const reaches = arm.valid[t];
+    const reaches = true;
```

```
JS suite:      # pass 33  # fail 0
Python suite:  passed
```

**Nothing caught it.** §15.5 asks specifically that *"a path failing to reach
the goal shows up instantly, in whichever arm"*, and the styling that does
that had **never been exercised** — because `preserve_connectivity` rejects
events that would sever the route, so no arm fails in any run this fixture
has. The one requirement the spec called out by name was the one with no test.

Now covered by a test that builds a synthetic failure:

```
not ok 2 - a route that never reaches the goal reads as broken, not as short
    a failed route did not read as broken
    expected: 'pane broken'   actual: 'pane'
```

**The generalisation:** a guarantee about failure cannot be tested by data in
which nothing fails. Every run available was a run where every arm succeeded,
so the failure path was unreachable from the fixtures — and unreachable code
is not tested code, however green the suite is.

## 9. The auto-generate removal, and the tests it broke

**Nine call sites in `tests/js/app.test.mjs`**, all of which called `loadPage`
and then asserted against a rendered graph. They now go through
`loadAndGenerate`, which presses Generate first — closer to what a user does
than the auto-generate they were relying on.

**One needed more than a rename.** `the step.t === t guard throws on a
mismatched payload` handed `loadPage` a scrambled timeline, and that is now
caught one layer *earlier* by `buildStateFrames`'s own ordering guard — so the
test passed while never running its own subject, the guard inside `draw()`.
Retargeted to scramble at render time.

**And a harness defect surfaced.** The fetch shim handed every test the same
fixture object, so the guard test's mutation of `state.run.steps` leaked into
the next five and they failed in a way that depended on execution order. The
shim now `structuredClone`s each response, which is what a real HTTP response
does anyway.

## 10. ⚠️ I wrote a `manifest`-class run into `outputs/`, and I have not deleted it

**`outputs/2026-09-05/10-46-38`** carries `run_class: manifest`. My corruption
demonstration #2 patched `race()` to stamp `manifest`, and `race()` writes to
the real `outputs/` tree, so the corruption landed on disk rather than staying
in the test.

**Consequence:** `test_run_classes_does_not_filter_to_manifest` now fails —
correctly. D31's invariant is that no `manifest` runs exist, and one does.

```
1 failed, 364 passed
E  AssertionError: no manifest runs exist; see D31
```

**I have not deleted it**, because the guardrail says never to delete anything
under `outputs/` and it does not carve out an exception for litter I made
myself. It is one command and it is yours to run:

```bash
rm -rf outputs/2026-09-05/10-46-38
```

**The real defect is mine and it is a process one:** a corruption harness that
writes into the live artefact tree can corrupt the artefact tree. It should
have pointed `OUTPUTS` at a temporary directory. I have not changed that
either — it is a test-infrastructure decision and segment 12 should make it
deliberately rather than me patching it at the end of this one.

**Also worth knowing: I created 21 run directories under
`outputs/2026-09-05/` today**, all `exploratory`, all from tests and
demonstrations. None of them is evidence and they will keep accumulating every
time the suite runs, because the Stage 3 tests each execute a real trial. That
is a design question for segment 12 — a temp directory for test runs would
solve both this and the manifest one above.

## 11. Acceptance

| Check | Result |
|---|---|
| `git diff --stat -- src/` | **Empty** — sixth segment |
| Suite | **364 passed, 1 failed, 0 skipped** — the failure is §10, on disk not in code |
| Lint, three trees | `All checks passed!` |
| Four budgets | 2005/2100 · 172/1000 · 552/700 · 599/900 |
| `schedule[` in dashboard code | Two hits, both docstring, quoting the contract |
| JS suite | **34 passed** |

**Skips: 0.**

## Deviations from spec

**One.** The spec says `run_trial()` or nothing; I call `run_experiment`, which
is the function that calls `run_trial` and the one `cli.py` uses. Using
`run_trial` directly would have meant writing the parquet myself, which is the
second-harness risk moved one layer down. Flagging it because the constraint
names `run_trial` explicitly.

## Questions for the Architect

1. **Test runs writing into `outputs/`** (§10). Should Stage 3's tests point at
   a temp directory? It fixes the manifest litter, the 21 accumulating runs,
   and the corruption-harness hazard in one ruling.
2. **JS budget: 148 lines for segments 12 and 13**, and segment 12 is
   interaction code. Projection before the spec is written?
3. **`run_experiment` vs `run_trial`** (deviations). Accept, or do you want the
   dashboard on `run_trial` with its own writer?
