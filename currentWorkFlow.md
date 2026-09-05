# SEGMENT 12 — Inspect

**Phase 1 · See it · Segment 7 of 7 — the last one**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` **§15.6**, §7 (the control layer, and why it is being rebuilt), §12, §2.3. `WORKFLOW_LOG.md` **Entry 011** carries R1–R3; **R1 and R2 are T1 and T2 here and come before anything new.**
> Append your findings to the **bottom** of this file.
>
> ## ⛔ YOU DO NOT COMMIT
>
> Rudra commits. Leave the tree unstaged, paste `git status --short`, and paste the commit message as a copyable block **with no `Co-Authored-By` trailer**. No `git add`, no `git commit`, no `git stash`, never `git add -A`. Reading history is fine. `AGENT_PROTOCOL.md` carries this permanently.

---

## Goal

**Let Rudra click into it.** An edge, a node, an arm — and get the history behind what he is looking at.

Two repairs come first, both from Entry 011, and both are containment failures rather than missing features. **Neither is deferrable to "after the fun part."**

---

## ⚠️ T1 — R1: the test suite must stop writing into the evidence tree

**25 run directories accumulated under `outputs/2026-09-05/` in one afternoon**, because every Stage 3 test executes a real trial. One of them was stamped `manifest` by a corruption demo and **landed in the live tree**, where the provenance guard correctly went red.

State the consequence plainly, because it is the reason this is task one:

> `run_class` exists so that **scratch runs can never silently become evidence.** A test harness able to write a `manifest` run into `outputs/` is a hole straight through that guarantee. For one afternoon, a test fixture could manufacture evidence.

The detection worked — that red test is Phase 0 doing its job. **The containment did not exist.**

**Three parts:**

1. **No test writes into `outputs/`.** The run root becomes a parameter; tests pass `tmp_path`. **If threading that through needs something `src/` does not expose, stop and report** — this is worth a core change if it needs one, and it would be the first in seven segments
2. **A test asserting the suite creates nothing under `outputs/`.** Enforced, not remembered — a convention lasts exactly as long as the person who remembers it
3. Rudra has deleted `outputs/2026-09-05/` by hand. **You were right to refuse**: the guardrail says never touch `outputs/` and carves out no exception for litter you made yourself. Reading it that way was correct and should stay correct

## ⚠️ T2 — R2: a run in which something actually fails

Your mutation made `reaches` always true, so **a broken route could never render as broken**, and nothing caught it. §15.6's neighbouring section names the requirement outright — *a path failing to reach the goal shows up instantly* — and it has no test, because `preserve_connectivity` means no arm fails in any run currently obtainable.

Your line, kept verbatim because it generalises:

> **"A guarantee about failure can't be tested by data in which nothing fails."**

**Build a synthetic run where an arm's route stops short**, and assert it renders as *broken* — visibly distinct from a short path, not merely shorter. **Not deferrable:** ACO and PSO can genuinely fail to complete a route in early iterations, so this can happen live, in front of an examiner, and would currently read as a slightly shorter line.

This is the third instance of one family — a threshold copied from the state being replaced, an invariant asserted only against correct data, and now a guarantee exercised only by data that never triggers it. The rule, once, for all three:

> **A test is only as good as the worst input it is ever shown. If the failing case cannot arise from real data, construct it.**

---

## T3 — MEASURE, and report what telemetry actually exists

`src/` (expect `2005 / 2100`, `+0`, **seventh segment** — unless T1 needs a core change, which is a legitimate first), `dashboard/**/*.py`, and both static budgets: **JS ≤ 700**, **presentation ≤ 900**.

**Then, before designing any panel:** paste from source what per-arm telemetry a run actually records. §15.6 asks for pheromone level per edge and PSO priority statistics per node — **§17 assigns Layer 2 probes to Phase 2, so those may not exist yet.**

**Build against what is recorded. Where a §15.6 field is not available, say so and leave it out** — a panel with a plausible-looking number nobody can trace is worse than a panel with a gap.

---

## T4 — The hit-target policy, finally needed

Carried since Entry 007 and this is the segment it bites: **the minimum edge length is sub-pixel**, so at least one node pair is coincident on screen.

- **nearest within a radius**, not an exact hit — an exact-hit test on a 2.4px circle is unusable
- **a defined tie-break** when two candidates are equidistant, stated and deterministic. Two clicks in the same place must select the same thing
- **the selection is visible** — whatever is selected is unmistakable on a canvas of 735 edges
- **click empty space to deselect**

State the policy in a docstring, and **test the tie-break** rather than trusting it. A picker that silently selects the wrong one of two coincident nodes is a wrong answer delivered confidently, which is this project's recurring failure mode in miniature.

## T5 — Click an edge

- **its weight over time**, across the run
- **its event history** — what happened to it, and when, from `events_at()`. **Never a re-derived index**
- **its current state** — usable or not, original road or pool road (§4.3.1)

Per-arm pheromone if and only if T3 found it recorded.

## T6 — Click a node

Whatever is genuinely available: degree, position, whether it is source or target, whether it sits on the current optimal route, and which arms currently route through it.

PSO priority statistics if and only if T3 found them recorded.

## T7 — The per-arm panel

For each raced arm: **current excess, evaluations spent**, and whatever else the run records. Every figure from the run's own output via `analysis/`, never recomputed.

## T8 — The allocation bar: **reserved, not built**

§15.6 calls it *"the project's novelty made watchable"*, and it is. **It cannot be built truthfully today.**

It shows `aco_fraction` sliding toward PSO as disruption lands and drifting back during calm — which requires a **working controller**. F7 leaves the prescheduled controller built with no arguments, varying nothing while logging itself active; F4 leaves the windowed signals reading low through their warm-up. **Phase 3 rebuilds the control layer.**

A bar built now would animate against a mechanism known not to work, and it would be indistinguishable on screen from one that does. That is the F5 failure — a flattering picture nobody interrogates — installed in the one widget the whole thesis rests on.

**Leave a labelled empty slot** saying the allocation view arrives with the rebuilt control layer in Phase 3. An honest gap is worth more than a confident animation of nothing.

## T9 — Tests

| Test | Catches |
|---|---|
| **The suite writes nothing under `outputs/`** | T1, enforced |
| **A broken route renders as broken** | T2, against the synthetic run |
| **The tie-break is deterministic** | Same click, same selection, on coincident nodes |
| **Edge event history equals `events_at()` at every step** | F1's rule, in a new place |
| **Every displayed figure traces to the run's output** | The anti-reimplementation test for this segment |
| **No panel shows a field the run does not record** | The T3 rule, enforced |

**Entry 010's rule stands: every invariant test must be shown failing against deliberately corrupted input, and the corruption pasted.** Green proves nothing until it has been red.

## T10 — Mutations, two, one of them yours

**Specified:** make the edge panel show the weight history of a *different* edge. Same shape, plausible numbers, wrong edge — the inspect-panel version of the mutation that segment 11's pane grid was tested against.

**Yours.** Three segments running, the uncommissioned one has found the real defect.

## T11 — Show it, and look at it

Screenshots you have looked at: a selected edge, a selected node, the per-arm panel, and the broken-route fixture rendering as broken. Plus your honest read on whether the page is still legible now that Phase 1's full weight is on it.

## T12 — Hand over, do **not** commit

`git status --short`, the commit message as a copyable block, no `Co-Authored-By`, and one line confirming complete and uncommitted.

---

## Constraints

| | |
|---|---|
| **Zero statements added to `src/`** | Unless T1 requires it — that is a legitimate stop-and-report, and the first in seven segments |
| **No test writes to `outputs/`** | |
| **No allocation bar** | Reserved for Phase 3. A labelled gap, not an animation |
| **No field the run does not record** | Leave the gap and say so |
| **`events_at()` for all event timing** | |
| **Every figure from `analysis/` or the run's output** | Never recomputed in the browser |
| **JS ≤ 700 · presentation ≤ 900** | |
| **Do not commit, do not push** | Rudra does both |

---

## Acceptance check

```bash
git diff --stat -- dashboard/ tests/ && git diff --stat -- src/
./.venv/bin/pytest                       # passes AND skips
./.venv/bin/ruff check src/ tests/ dashboard/
./.venv/bin/pytest -k "budget or statement" -s
ls outputs/                              # unchanged by the suite — check before and after
grep -rn "schedule\[" dashboard/ --include=*.py --include=*.js
git status --short                       # UNSTAGED, UNCOMMITTED
```

**Paste verbatim:** four budget figures · **what telemetry the run actually records**, from source · the hit-target policy and its tie-break · `ls outputs/` before and after a full suite run · every invariant test **shown red** · both mutations · four screenshots · legibility, honestly.

---

## Definition of done

Checks pass, artefacts pasted, screenshots looked at, work uncommitted with the message pasted, FINDINGS appended.

**This closes Phase 1.** Rudra builds a world, breaks it, races three algorithms against the truth, and clicks into any of it.

Segment 13 is then a judgement call, not a commitment: the design work landed early, so what remains is a final pass and a decision on whether the sidebar layout is still wanted. **Say what you think** — you have been looking at this page longer than anyone.

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->

---

# FINDINGS — Segment 12

## 0. ⛔ STOP AND REPORT — the JavaScript budget is breached at 702 / 700

```
static/**/*.js   702 / 700     app.js 538 · model.js 164
```

**I have not shaved two lines to get under it.** The protocol says stop and
report, do not delete code to make room, never raise the cap yourself — and
two lines of "tightening" would be gaming a brake whose entire purpose is to
be felt. The suite is red on `test_dashboard_javascript_budget` and that is
the instrument working.

**What the number is made of.** Segment 12 added hit-testing with a stated
tie-break, an edge panel, a node panel, a per-arm panel and the selection
overlay — the interaction segment, in the surface the split named as the tight
one. I flagged 148 lines of headroom at the close of segment 11 and asked for a
projection before this spec was written; the honest read is that inspect does
not fit in 148.

**Three options, and the one I would argue against.**

- **(a) Raise the JS cap** on the terms the science cap was raised — measured,
  argued, recorded. The case: 700 was set in segment 11 from a 414-line file
  with no idea what inspect would cost, and Phase 1 is now complete, so the
  number can be set from what the finished thing actually weighs rather than
  from a guess made two segments early.
- **(b) Rule that Phase 1 is over budget and something comes out.** Defensible
  — but the only things large enough are the panes, the chart or the inspect
  panels, all of which are §15.5/§15.6 requirements.
- **(c) Shave to 699.** I would argue against this. It buys a green suite and
  teaches that the cap is a formality, and the next segment starts one line
  from the wall with the lesson already learned.

**Presentation has 247 spare.** The split I proposed in segment 11 has turned
out to bind hard on one side and slack on the other, which is itself a finding
about where the boundary was drawn.

## 1. T1 — the containment, and it holds

**No `src/` change was needed.** `run_experiment(cfg, arms, directory, run_id)`
already takes a directory, so the run root became a parameter entirely inside
`dashboard/server.py`: `race(spec, root=None)` and `read_run(run_id, root=None)`,
defaulting to `outputs/`, with every test passing `tmp_path`. Seventh segment
at `src/` `2005 / 2100`, `+0`.

**Enforced by a session fixture, not a convention** (`tests/conftest.py`),
because a convention lasts exactly as long as the person who remembers it. It
snapshots `outputs/` before the session and fails after if anything appeared.

**Shown red**, by writing a test that deliberately leaks:

```
E  AssertionError: the test suite wrote into outputs/, the evidence tree:
E      2026-09-05/11-24-06
E      2026-09-05/11-24-06/events.parquet
E      2026-09-05/11-24-06/manifest.json
E      2026-09-05/11-24-06/steps.parquet
E    Tests must pass a tmp_path run root. See tests/conftest.py.
```

**And green across a full run:**

```
outputs/ BEFORE suite:  17 run dirs
outputs/ AFTER  suite:  17 run dirs
```

**One thing the fixture does not cover, and should be known.** The demonstration
above wrote `outputs/2026-09-05/11-24-06` before the guard failed it, and it is
still there — same rule, I do not delete from `outputs/`. More generally, my
**screenshot harness still writes real runs**: it drives the live server, and a
server-driven race is a real dashboard run that lands in the real tree. That is
correct behaviour, not a leak, but it is why 17 directories exist. If Phase 2
wants those contained too, that is a separate ruling about the demo path rather
than the test path.

## 2. T2 — a run in which something actually fails

`tests/js/fixtures/race_broken.json`, **built from a real race and then
truncated**, so every field except the one under test is exactly what the
engine produced. ACO's route stops two hops short over `t = 18..24` and is
marked invalid there.

```
A*                 invalid steps: []
ACO standalone     invalid steps: [18, 19, 20, 21, 22, 23, 24]
PSO standalone     invalid steps: []
Hybrid (baseline)  invalid steps: []
```

The test asserts the pane reads `pane broken` **and** that its neighbours do
not — distinct from a short path, not merely shorter — and that the arm stops
being marked at `t = 30` when its route recovers.

## 3. T3 — what a run actually records

**`steps.parquet`** — 28 columns: `run_id, run_class, scenario,
events_per_step, graph_model, n_nodes, n_edges, trial, seed, timestep, arm,
arm_family, num_events, optimum, best_cost, excess, path_valid, path_changed,
path_len, best_path, evaluations_spent, wall_ms, astar_expansions, signal_kind,
controller_kind, signal_value, params, probe`

**`events.parquet`** — `run_id, run_class, scenario, trial, seed, timestep,
kind, u, v, old_weight, new_weight`

**`probe` is populated, and it is per-arm:**

```
astar    expansions
aco      iterations, lambda_branch, tau_ratio
pso      diversity, iterations
hybrid   aco_fraction, aco_iterations, aco_lambda_branch, aco_tau_ratio,
         exchanges, pso_diversity, pso_iterations
```

**Two §15.6 fields do not exist and are left out.**

| §15.6 asks for | Status |
|---|---|
| per-**edge** pheromone level | **Not recorded.** `tau_ratio` is a colony-level aggregate, not per edge |
| per-**node** PSO priority statistics | **Not recorded.** `diversity` is swarm-level, not per node |

Both are Layer 2 probes and §17 assigns those to Phase 2. `test_no_panel_shows_a_field_the_run_does_not_record` pins the absence, so the day the probes land it fails and the panels get extended deliberately rather than by someone noticing.

**`signal_kind` and `controller_kind` are empty for all four arms** — correct, they are the uncontrolled arms.

## 4. T8 — the allocation view, and the measurement behind the gap

```
hybrid aco_fraction over 60 steps:
  distinct values: [0.5]
  min 0.5  max 0.5  ->  moves: False
```

**Pinned at 0.5 for the entire run.** A bar built today would draw a flat line
at fifty percent and present it as the project's novelty. The slot is labelled
and says why, and `test_the_allocation_view_is_a_labelled_gap_not_a_drawing`
fails the moment `aco_fraction` starts moving — which turns the gap into a
reminder to build it rather than something to rediscover.

## 5. T4 — the hit-target policy

> **Nearest within a radius of 14 view units, not an exact hit.** A 2.4px node
> needs a target far larger than itself.
>
> **Tie-break: lowest index wins.** `<` rather than `<=`, iterating in order,
> so the first candidate encountered is kept. The minimum edge length in a
> `medium200` graph is sub-pixel, so a tie is not hypothetical — a picker that
> alternates between two coincident nodes is a wrong answer delivered
> confidently.
>
> **Nodes take precedence over edges**, since a node click is the more specific
> intent. **Empty space deselects.**

Tested rather than trusted: twenty clicks on a coincident pair, same answer
every time; nearest-not-merely-within; null outside the radius; and edge
distance measured **to the segment**, so a click at the midpoint of a long edge
selects it rather than missing both endpoints.

## 6. Every invariant shown red

```
T1  suite writes into outputs/
    E  AssertionError: the test suite wrote into outputs/, the evidence tree: ...

T2  a broken route rendering as a short one
    E  a failed route did not read as broken   expected 'pane broken'  actual 'pane'

    edge panel reads a different edge
    E  The input did not match /road 23.31/. Input: 'road 0–35'

    selection marker on the wrong node
    E  the marker is not on the node the panel describes
       expected: '267.00'   actual: '444.38'

    a field the run does not record
    E  the page offers pheromone, which is not recorded

    the allocation gap becoming a drawing
    E  aco_fraction now moves (...) — the allocation view can be built
```

## 7. Both mutations

**A — specified: the edge panel reads `edges[0]` whatever was clicked.**
Caught: `expected /road 23.31/, actual 'road 0–35'`.

**B — mine: the selection marker draws at `xy[0]` whatever was selected.**
The panel stayed correct and the highlight pointed somewhere else.

```
JS suite:      # pass 42  # fail 0
Python suite:  passed
```

**Nothing caught it.** It is segment 8's failure — the picture and its caption
disagreeing while both look right — moved into the selection layer, and it is
the fourth consecutive segment where the uncommissioned mutation found the real
gap. Now covered, and shown red above.

**A note on my own repeat.** The first version of
`test_no_panel_shows_a_field_the_run_does_not_record` grepped `app.js` for
"pheromone" and failed on **its own comment explaining why the field is
absent** — the identical mistake as segment 9's `schedule[` grep hitting a
docstring. I had written the fix once already and did not carry it forward.
Comments are stripped now.

## 8. Legibility, honestly, with Phase 1's full weight on the page

**It holds, and it holds because it is stacked rather than dense.** The page is
now setup → stat bar → main canvas → transport → panes → chart → inspect →
legend/ledger → reference, and every band is one idea. Nothing competes for the
same space, and the eye is never asked to separate two things drawn on top of
each other.

**The one place it is genuinely busy is the main canvas**, and that was true
before this segment: state layer, event flashes, ghosts, path, markers, and now
a selection overlay. The selection is the widest stroke on it at 4px so it wins,
but at a heavy disruption step there is a lot happening in one square.

**What I would not add to that canvas:** anything else. Segment 13 should treat
the main canvas as full.

## 9. Acceptance

| Check | Result |
|---|---|
| `git diff --stat -- src/` | **Empty** — seventh segment |
| Suite | **366 passed, 1 failed** — the failure is §0, the budget |
| Lint, three trees | `All checks passed!` |
| Budgets | 2005/2100 · 174/1000 · **702/700 breached** · 653/900 |
| `outputs/` before / after | **17 / 17** |
| `schedule[` in dashboard code | docstring only |
| JS suite | **43 passed** |

**Skips: 0.**

## Segment 13 — what I think, having looked at this longest

**Do not do a sidebar.** The stacked layout is the reason the page survived
having panes, a chart and inspect panels added to it, and a sidebar would take
the one thing that is working — every band being one idea — and trade it for
density the page does not need. What made this readable was never the layout;
it was dropping layers from the panes and giving the state and event channels
separate encodings.

**What I would actually spend segment 13 on**, in order:

1. **The budget ruling**, because everything else depends on it
2. **A default that tells the story** — the page opens empty and correct, but a
   first-time viewer has to know to press three buttons in order. One "run the
   demo" affordance that does Generate → Build → Race would make the thing
   self-demonstrating in front of an examiner
3. **Nothing on the main canvas.** It is full

**And one thing I would not call design work but would not ship without:** the
screenshot path still writes real runs into `outputs/`. It is correct
behaviour and it is also why there are 17 directories there.
