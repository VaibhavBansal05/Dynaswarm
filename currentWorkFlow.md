# SEGMENT 13 — Ship It

**Phase 1 · See it · Segment 8 of 8 — the close-out**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` §9 (display names), §10.2 (the five fairness guarantees), §15.5, §2.3. `WORKFLOW_LOG.md` **Entry 012** carries R1 and R2, both of which are tasks here.
> Append your findings to the **bottom** of this file.
>
> ## ⛔ YOU DO NOT COMMIT
>
> Rudra commits. Leave the tree unstaged, paste `git status --short`, and paste the commit message as a copyable block **with no `Co-Authored-By` trailer**. No `git add`, no `git commit`, no `git stash`, never `git add -A`. Reading history is fine.

---

## Goal

**Close Phase 1.** Six small things, most of which exist to make what is already true *visible*.

There is no new mechanism here. That is deliberate — everything below either unblocks a red suite, surfaces a guarantee the page currently asks the viewer to take on trust, or makes the thing demonstrable in front of an examiner.

---

## T1 — R1: the JavaScript cap becomes **900**

You were right to stop at `702 / 700` and right to refuse to shave two lines. **Two lines of tightening would have bought a green suite and taught that the cap is a formality**, and a brake exists to be felt.

**The cap was my error, and of a kind this log has already named.** I set 700 in Entry 010 from a **414-line file**, before anyone knew what inspect would cost — a threshold lifted from the state I was leaving behind. That is exactly the defect Entry 009 ruled on, in your words:

> *"A threshold copied from the state you're leaving behind is a memento, not a guard."*

Three segments after writing that down, I did it. So the new number is **derived, not picked**:

| | |
|---|---|
| Phase 1 dashboard, complete | 702 |
| Phase 3's allocation view — the one substantial JS build left | ~120, the size of the excess chart it most resembles |
| Demo affordance + slack for Phase 2's probe panels | ~80 |
| **JS cap** | **900** |

Presentation stays **900**.

**Report the excess chart's actual line count**, so 900 rests on a measurement rather than my estimate. If it is materially larger than 120, say so — that is a finding about the cap, and better raised now than in Phase 3.

Your observation that the split "binds hard on one side and slack on the other" **is the split working.** It says in one number that this dashboard's growth is *behavioural*. A single combined budget would have shown comfortable headroom and told us nothing.

## T2 — R2: no sidebar. Your argument is accepted.

> *"The stacked layout is why the page survived having panes, a chart and inspect panels added to it — every band is one idea. What made it readable was dropping layers from the panes and separating the state and event channels, not the layout."*

**Accepted, and the reasoning is the part worth keeping:** legibility was bought by *reducing what each band carries*, not by rearranging bands. A sidebar would have moved the problem and then taken credit for a fix that came from somewhere else.

Nothing to build. Recorded so nobody re-proposes it.

---

## T3 — Each pane carries cost and hops, not just excess

**Rudra's request.** A pane currently shows `+%` alone. Percentage without a magnitude is a number you cannot check against anything — the main canvas says `best route 102.02` and a pane says `+3.1%`, and reconciling them is arithmetic the viewer should not be doing.

Each pane shows, for that arm at the current `t`:

- **its route cost** — same units, same precision as the main readout
- **its hop count**
- **its excess over the optimum**, as now

Use §9's **display names** — *A\**, *ACO standalone*, *PSO standalone*, *Hybrid (baseline)* — never the code ids.

**Every figure from the run's own output via `analysis/`.** The A\* pane's cost must equal the main readout's optimum at that `t` by construction, not by coincidence — **and a test should say so**, since that equality is the one relationship a viewer will check by eye and the one that would embarrass the demo if it drifted.

Space is tight at quarter size. **If three figures will not fit legibly, say so and propose** rather than shrinking type until it technically fits.

## T4 — Make the shared world visible

**Rudra's concern, and it is the right concern:** if the four panes were showing different disruption states, every comparison on the page would be meaningless.

**It is already true and already tested.** The timeline is built once and frozen; `state_at(t)` is cached, so all four arms read the same bytes; §10.2 makes it a fairness guarantee, and segment 11 asserts it. **Nothing is broken.**

What is missing is that a viewer must take it on trust. An examiner asking *"how do I know they're facing the same disruptions?"* deserves an answer on the screen, not in a docstring.

**Make it visible, cheaply and honestly.** One line stating that all panes are showing timestep `t` of one frozen timeline is enough; if there is a way to show it that is *evidence* rather than *assertion* — a shared count, a shared identifier — prefer that. **Do not build a comparison that could disagree with itself; do not compute anything new.** State what is already guaranteed.

**Do not** dress this as a check that "passes". A green tick that can never be red is the tautology Entry 012 caught, wearing a UI costume.

## T5 — The legend, placed properly

It works and it is in the wrong place. Put it where someone reading a pane or the main canvas can reach it without hunting, and where it does not compete with the data for attention.

**Say what you changed and why.** You have looked at this page longer than either of us.

## T6 — One "run the demo" affordance

**Your proposal, accepted.** One control that walks the page through the whole story unattended: build a world, break it, race the arms, land on the step where the optimum moves.

Its job is a single one: **Rudra presses it in front of his examiner and the project explains itself.** The narrative that has emerged across this phase is already the right one —

> a shortest path that will not hold still · disruption lands · most of it costs nothing · sometimes the route re-routes · here is how each algorithm chases it.

Keep it short. An examiner's attention is the budget. If a full 60-step playback is too slow to watch, jump between the moments that matter rather than playing everything.

**Nothing on the main canvas. It is full.**

---

## T7 — Tests

| Test | Catches |
|---|---|
| **The A\* pane's cost equals the main readout's optimum at every `t`** | The equality a viewer checks by eye |
| **Each pane's cost, hops and excess come from the run's output** | Not recomputed, not derived from each other |
| **Panes use §9 display names, never code ids** | |
| **Both budgets, at the new caps** | |
| **The demo affordance visits the steps it claims to** | Not a fixed list that drifts when the run changes |

**Entry 010's rule stands: every invariant test shown failing against corrupted input, and the corruption pasted.** Green proves nothing until it has been red.

## T8 — Mutations, two, one of them yours

**Specified:** make a pane show a different arm's cost while keeping its own label. The panel and the label stay plausible; only the pairing is wrong. This is segment 12's selection-marker failure and segment 8's caption failure in a third costume, and **four consecutive segments say your uncommissioned mutation is the one that finds it.**

## T9 — Show it, and look at it

Screenshots you have opened: the pane grid with all three figures, the legend in its new home, and the demo affordance mid-run.

**Then, since this closes Phase 1:** your honest read on whether this page is ready to be shown to an examiner, and the one thing you would fix next if the budget were not the constraint.

## T10 — Hand over, do **not** commit

`git status --short`, the commit message as a copyable block, no `Co-Authored-By`, and one line confirming complete and uncommitted.

---

## Constraints

| | |
|---|---|
| **Zero statements added to `src/`** | Eighth segment. Stop and report |
| **No sidebar** | Settled |
| **Nothing on the main canvas** | Full |
| **No new mechanism** | This segment surfaces what exists; it does not add behaviour |
| **§9 display names in all UI text** | Code ids are frozen data, never labels |
| **Every figure from `analysis/` or the run's output** | |
| **JS ≤ 900 · presentation ≤ 900** | |
| **Do not commit, do not push** | |

---

## Acceptance check

```bash
git diff --stat -- dashboard/ tests/ && git diff --stat -- src/
./.venv/bin/pytest                       # passes AND skips — expect green
./.venv/bin/ruff check src/ tests/ dashboard/
./.venv/bin/pytest -k "budget or statement" -s
ls outputs/                              # unchanged before and after
git status --short                       # UNSTAGED, UNCOMMITTED
```

**Paste verbatim:** both budgets at the new caps, plus **the excess chart's real line count** · the three pane figures for all four arms at one timestep · what you did for T4 and why it is evidence rather than assertion · three screenshots · both mutations · **your read on demo-readiness, and the one thing you would fix next.**

---

## Definition of done

Green suite, artefacts pasted, screenshots looked at, uncommitted with the message pasted, FINDINGS appended.

**This closes Phase 1.** Then Phase 2 — trust it: every mechanism proven live or reported inert.

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->

---

# FINDINGS — Segment 13

## 1. T1 — the cap, and the derivation checked against evidence

Raised to **900**, presentation stays **900**. The ruling asked me to report the
excess chart's real line count so the number rests on a measurement. It does
not survive the check.

**The derivation was** `702 + ~120 for Phase 3's allocation view ("the size of
the excess chart it most resembles") + ~80`.

**Measured, per top-level function, non-blank non-comment:**

```
  drawExcess       36 lines     <- the excess chart, priced at ~120
  drawPanes        34
  inspectEdge      27
  drawArmPanel     24
  drawLedger       21
  inspectNode      18
```

**The excess chart is 36 lines, not ~120 — the estimate is 3.3× the real
thing**, and no widget on this page exceeds 36. On the same benchmark the
allocation view is ~40, so the honest arithmetic reads `702 + ~40 + ~80 ≈ 820`.

**The demo affordance came in at 11 lines against ~80 budgeted** — the same
estimate running high a second time, independently.

**I am not proposing you lower it.** 900 errs in the safe direction and the
cost of the other error was demonstrated last segment. It matters because
*"derived, not picked"* only beats *"picked"* if the derivation is checkable —
this one was checked and came back 3× out, so 900 carries roughly 80 lines more
headroom than the reasoning intended. Worth knowing at the next raise rather
than corrected now.

## 2. T3 — cost and hops on every pane

```
All 4 panes show timestep 21 of one timeline, frozen before any algorithm ran
— seed 1000, graph 1e06d1c7b60e, 760 roads open.

  A*                 110.54 · 12 hops    +0.0%
  ACO standalone     113.80 · 11 hops    +3.0%
  PSO standalone     155.96 · 17 hops   +41.1%
  Hybrid (baseline)  111.57 · 13 hops    +0.9%
```

**A\*'s 110.54 is the main readout's optimum at t=21, to the digit.** That
equality is asserted at *every* timestep, not sampled — it is the one
relationship a viewer checks by eye and the one that would embarrass the demo
if it drifted.

`cost` and `hops` are the run's own `best_cost` and `path_len` columns. Not
derived from the drawn route: the test deliberately does **not** assert that
`hops` equals the drawn segment count, because the run does not claim that
relationship and inventing it would be asserting something nobody measured.

**Space was not a problem.** Three figures fit at quarter size because they
went on two lines — excess stayed in the header beside the name, cost and hops
took a line of their own. No type was shrunk.

## 3. T4 — the shared world, stated rather than checked

```
All 4 panes show timestep 21 of one timeline, frozen before any algorithm ran
— seed 1000, graph 1e06d1c7b60e, 760 roads open.
```

**Deliberately a statement, not a tick.** A green check that can never be red
is the tautology Entry 012 caught, wearing a UI costume, and building a
comparison here would mean computing something new to compare.

**What makes it evidence rather than caption is that the identifiers are the
run's own.** `graph_id` is derived from the graph config recorded in *the run's
manifest*, not from whatever the form currently holds — so editing the world
after racing leaves the line naming the graph the arms actually ran on, and the
two visibly disagree instead of silently agreeing. One seed and one graph id
produce one schedule, and there is exactly one of each on screen to point at.

### It shipped reading "graph undefined", and only the screenshot caught it

`read_run` returned no `graph_id`, so the template interpolated the gap and
rendered the word. Every test passed. The suite was green, the panes were
correct, and the line under them read `graph undefined` — which would have gone
in front of an examiner.

**A caption that renders a missing value as a word is worse than one that
fails, because it looks like information.** Now pinned by a test asserting the
line contains no `undefined`/`null`/`NaN` and carries the run's own identifiers,
and shown red against a mutation that points it at the form instead of the run.

This is the standing screenshot rule earning its place for the second time —
the first was `delete` being invisible in segment 10.

## 4. T5 — the legend, moved

**From the bottom row, beside the ledger → directly beneath the transport**, above
the pane grid.

**Why:** it explains the encoding on the main canvas, and it was two full
sections below the thing it explains — so reading a colour meant scrolling past
the panes and the chart, and scrolling back. Now the canvas, its controls and
its key are one continuous band, and the eye never leaves the thing it is
decoding. It also no longer competes with the ledger, which is a *result*
rather than a key and deserves its own attention.

## 5. T6 — the demo walks the moments that matter

It runs Generate → Build → Race, then visits every timestep where the optimum
**actually moves**, holding 1.4 s on each.

**The stops are computed from the run, not listed.** A fixed set of timesteps
would drift the moment the seed, scenario or horizon changed, and would then
walk an examiner through the wrong moments with total confidence. Pinned by a
test that recomputes the moved-steps from the fixture and asserts the demo
visits all of them and nothing else.

It drives the same three functions the three buttons drive — not its own
sequence of requests, because a second route into the engine is a second way to
be wrong.

## 6. Every invariant shown red

```
A. a pane shows another arm's cost, keeping its own label
   not ok - cost, hops and excess are the run's own columns, not derived
   expected: '113.80 · 11 hops'   actual: '110.54 · 12 hops'

B. panes labelled with code ids instead of display names
   not ok - panes are labelled with display names, never code ids

C. the demo walks a fixed list of timesteps
   not ok - the demo visits the steps where the optimum moves
   the demo skips a moment that matters   expected: 5   actual: 4

D. the shared line reads the form instead of the run
   not ok - names real identifiers, never 'undefined'
   not ok - reports the graph the RUN used, not whatever the form now holds
```

**One correction to my own method.** My first attempt at mutation A reassigned
a `const` loop variable, so it *threw* rather than producing the silent
wrong-pairing I meant to demonstrate — and it tripped three unrelated tests,
which reads like a strong catch and is nothing of the kind. Redone so the
mutation is silent and the failure is the one I claimed.

## 7. Acceptance

| Check | Result |
|---|---|
| Suite | **367 passed, 0 failed, 0 skipped** |
| Lint, three trees | `All checks passed!` |
| `git diff --stat -- src/` | **Empty** — eighth segment |
| Budgets | 2005/2100 · 177/1000 · **734/900** · 667/900 |
| `outputs/` before / after | **24 / 24** |
| JS suite | **50 passed** |

## 8. Is it ready to show an examiner?

**Yes, with one caveat that is about the room rather than the page.**

What works: the narrative is on screen in order, and the demo button walks it
unattended. A world gets built, roads break, most of it costs nothing, then at
one moment the route re-routes and the number jumps — and four algorithms are
chasing that number with their distances shown. An examiner asking *"how do I
know they faced the same disruptions?"* gets an answer on screen. One asking
*"where does that percentage come from?"* can click the road it happened to.

**The caveat: the interesting moments are 1.4 seconds each and there are five
of them.** The demo is over in about eight seconds. That is the right length
for attention and the wrong length for someone who has never seen the thing —
they will not know where to look before it has moved on. In practice Rudra
should press the demo once to show the shape, then scrub manually to t=21 and
talk over it.

**The one thing I would fix next if budget were not the constraint:** the main
canvas at a heavy disruption step. It carries the state layer, event flashes,
ghosts, the optimal path, the endpoint markers and now a selection overlay, and
at t=21 with 25 roads breaking it is the one place on the page where two things
compete for the same pixels. Everything else was made legible by *reducing what
each band carries*; the main canvas is the band that never got that treatment,
because every segment had a reason to add to it and none had a reason to take
something away.

I would not add anything else to it, and I would spend a segment deciding what
comes off.

## 9. Phase 1, closed

Eight segments, `src/` unmoved at **2005 / 2100** in every one. §2.3 asserted
the core would expose what the dashboard needed; no segment falsified it.

**The one thing worth carrying into Phase 2:** the uncommissioned mutation found
the real defect in **five consecutive segments** — the panes, the ledger, the
broken-route styling, the selection marker, and now the shared line via a
screenshot rather than a test. The commissioned one confirmed a prediction every
time. That is a large enough sample to stop calling it luck: the mutation worth
writing is the one nobody thought to ask for, which a spec cannot contain by
construction.
