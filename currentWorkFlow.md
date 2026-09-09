# SEGMENT 14 — Prove ACO Runs

**Phase 2 · Trust it · Segment 1 of 3**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` **§5.2 (ACO), §2.1 (the layers), §10.3 (Layer 1 invariants), §17**, and `decisionLedger.md`. `WORKFLOW_LOG.md` **Entry 013** closes Phase 1; **Entry 008 logs F10, which is T1 here.**
> Append your findings to the **bottom** of this file.
>
> ## ⛔ YOU DO NOT COMMIT
>
> Rudra commits. Leave the tree unstaged, paste `git status --short`, and paste the commit message as a copyable block **with no `Co-Authored-By` trailer**. No `git add`, no `git commit`, no `git stash`, never `git add -A`. Reading history is fine.

---

## What Phase 2 is, and why it is not more building

Phase 1 made the system **visible**. Phase 2 makes it **believable**.

§17's gate is one sentence and it is unusual:

> **Every mechanism proven live or reported inert.**

Read the second half. The deliverable is not "we confirmed everything works." It is **an instrument that would have told us if something did not** — and the only way to earn that claim is to break each mechanism deliberately and watch the instrument say so.

This project has now hit the same failure five separate times, under five names: a threshold copied from the state being replaced, an invariant asserted only against correct data, a guarantee tested by data in which nothing fails, a ledger reconciled against its own arithmetic, a green tick that could never be red. Entry 013 stated the common root:

> **A test is only as good as the worst input it is ever shown.**

A probe is a test with a UI. It inherits the whole problem, and it inherits it in the place where it matters most — because the numbers a probe reports are the ones that go into your report.

**So the central requirement of this segment, above every feature in it:**

> **Every probe must be demonstrated reporting `inert` against a deliberately disabled mechanism.** Paste the disabling and paste the output. A probe that has only ever reported "working" is not evidence that anything works.

---

## ⚠️ T0 — MEASURE, and this time **project the whole phase before writing a line**

**`src/` is at `2005 / 2100`. Ninety-five statements of margin.** It has not moved in eight segments because nothing in Phase 1 belonged in the science surface. **Probes do.** That streak ends here, and it should.

Ninety-five is not obviously enough for Phase 2's probes *and* Phase 3's restructure.

**Before writing any probe code:** project the statement cost of **all of Phase 2** — ACO here, PSO and Hybrid next segment, the walkthrough after — and report it against the 95.

**If it does not fit, stop and report.** Do not start, discover the wall at 2098, and then be choosing between deleting something that mattered and asking for a raise under pressure. That is exactly how segment 12 ended at `702 / 700`, and the lesson from it was not "raise caps sooner" — it was **find out before you are committed.**

Note in passing that Phase 3 restructures the control layer into `allocation/`, which may be statement-negative. **Say whether you are counting on that**, because a projection that quietly assumes a future refactor will pay for today's spending is a projection that has already failed.

Also report `dashboard/` Python, JS, and presentation, unchanged expectations.

---

## T1 — F10: the F1 arithmetic still lives in two places

Logged in Entry 008 and assigned here.

`changed_edges` derives `schedule[t - 1]` independently instead of calling `events_at()`. **It is correct today.** The defect is that F1's arithmetic exists in two places, and **the second one is not the one the tests point at.**

A future edit to `events_at()` — a horizon change, an indexing convention, anything — leaves this behind, silently. F1 was the off-by-one that made every component read one timestep into the future and voided every recency-driven result the project had. **It does not get a second door.**

One line: `changed_edges` asks `events_at()`. Statement-neutral or better. **Confirm the values are identical before and after**, at every timestep, not by argument.

---

## T2 — Report the probe surface that already exists

Segment 12 found that `probe` carries **colony- and swarm-level aggregates**, and that per-edge and per-node probes do not exist. That is the extent of what is known.

**Before designing anything, paste from source:**

- what `probe` records today, field by field, and where it is written
- when it fires — every step, every arm, conditionally?
- what it costs when nobody is looking. **A probe that runs during Phase 4's manifest at ≥100 trials is a probe that changes what it measures if it is expensive**, and §10.2's fairness guarantees do not survive an instrument that slows one arm more than another
- whether it is already recorded to `steps.parquet` or dropped

**Build on what is there.** If the existing probe already answers a question below, say so and do not build a second one — a second instrument that disagrees with the first is this project's founding failure.

---

## T3 — The ACO probes

**ACO first, deliberately.** It is the most mechanism-heavy component — pheromone, evaporation, MAX–MIN bounds, the best ant's deposit — and it is the one where *"is this actually running"* is most checkable and most consequential. §5.2 is the contract.

Whatever the answers to T2, these are the questions Phase 2 must be able to answer about ACO from a recorded run, per step:

| Question | Why it cannot be assumed |
|---|---|
| **Is pheromone changing at all?** | A frozen pheromone table is an ACO that is really a random walk. It would still produce routes, still produce excess, still look like a result |
| **Is evaporation happening?** | Without it, ACO converges early and never re-explores — which would look like *"ACO recovers poorly from disruption,"* a finding you would report |
| **Are the MAX–MIN bounds actually binding?** | The bounds are the *point* of MAX–MIN Ant System. If they never clamp, this is plain ACO under a different name in the report |
| **Is the best ant depositing on the route it found?** | Deposit on the wrong edges is a mechanism that runs and does nothing |

**Report the numbers, not a verdict.** *"Pheromone changed on 47 of 735 edges this step, min 0.012, max 0.891, bounds [0.01, 0.9], clamped 12"* is a probe. *"pheromone: OK"* is a claim, and a claim is what a probe is supposed to replace.

**Aggregate, do not stream.** Per-edge pheromone at every step for every trial is the payload that made a 34 KB response into 1.7 MB in segment 10. Colony-level aggregates per step, and **say what you are giving up** by aggregating.

## T4 — Prove each probe can say `inert`

**The task the phase exists for.** For every probe in T3:

1. **Disable the mechanism it watches** — pin evaporation to zero, freeze the pheromone table, remove the bounds, deposit on a fixed edge set
2. **Run and paste the probe's output**
3. **It must be unmistakable.** Not a number a careful reader could interpret as inert — a report that says so

**If a probe cannot distinguish a disabled mechanism from a working one, it is not a probe and it does not ship.** Say so and say what you would need instead.

**And check the other direction too.** A probe that reports inert when the mechanism *is* running is worse than none — it would send someone hunting a defect that is not there, in a codebase where two of the last six real defects were found by someone following exactly such a trail.

## T5 — Tests

| Test | Catches |
|---|---|
| **F10: `changed_edges` and `events_at()` agree at every timestep** | Before and after the fix |
| **Each probe reports inert against its disabled mechanism** | T4, as a test rather than a demonstration |
| **Each probe reports live against the working one** | The other direction |
| **Probes do not change what they measure** | Same seed, same run, probes on and off → identical `best_cost` at every step. **The strong one** |
| **Probe cost is bounded** | Whatever T2 finds, pinned, since Phase 4 runs this ≥100 times |

**Every invariant test shown failing against corrupted input, and the corruption pasted.**

## T6 — Mutations, two, one of them yours

**Specified:** make a probe read the pheromone table *before* the update instead of after. It reports plausible, changing, in-bounds numbers — and they are one step stale. This is F1's shape moved into the instrument layer, and it is the failure that would be hardest to ever notice.

**Yours.** Five consecutive segments say the uncommissioned mutation is the one that finds the real defect. Entry 013 stated why: **a spec can only mutate what its author already imagined going wrong.**

## T7 — Show it

1. **T0's projection for all of Phase 2**, against the 95 — before anything else
2. F10's before/after equality
3. The existing probe surface, from source
4. **Each ACO probe, live and inert, side by side** — the artefact of this segment
5. Both mutations
6. **Your read: after this, would you believe a number ACO produced?** Not a formality — you have been closer to this code than either of us

## T8 — Hand over, do **not** commit

`git status --short`, the commit message as a copyable block, no `Co-Authored-By`, one line confirming complete and uncommitted.

---

## Constraints

| | |
|---|---|
| **`src/` will move — project the whole phase first** | Stop and report if Phase 2 does not fit in 95 |
| **Every probe must be shown reporting inert** | Non-negotiable. An unproven probe does not ship |
| **Probes report numbers, not verdicts** | |
| **Probes must not change what they measure** | Phase 4 runs this ≥100 times per arm |
| **Aggregate; do not stream per-edge state** | And say what aggregating gives up |
| **Build on the existing probe** | Never a second instrument beside the first |
| **No PSO, no Hybrid, no walkthrough** | Segments 15 and 16 |
| **No control-layer changes** | F4, F7, F8 are Phase 3 |
| **No dashboard work** | Phase 1 is closed. The panels segment 12 left empty get filled when the data exists, not before |
| **Do not commit, do not push** | |

---

## Acceptance check

```bash
git diff --stat -- src/ tests/          # src/ MOVES this time — report by how much
./.venv/bin/pytest                       # passes AND skips
./.venv/bin/ruff check src/ tests/ dashboard/
./.venv/bin/pytest -k "budget or statement" -s
ls outputs/                              # unchanged before and after
git status --short                       # UNSTAGED, UNCOMMITTED
```

**Paste verbatim:** the Phase 2 projection against the 95 · F10 before/after · the existing probe surface from source · **every probe live and inert** · both mutations · every invariant test shown red · your read on whether you would now believe an ACO number.

---

## Definition of done

Green suite, artefacts pasted, **every probe demonstrated inert**, uncommitted with the message pasted, FINDINGS appended.

**After this, one of the three optimizers can be trusted to have actually run.** Segment 15 does PSO and the Hybrid.

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->

---

# FINDINGS — Segment 14

## 1. T0 — the Phase 2 projection, against the 95

**It fits, with roughly 15–20 to spare, and I am not counting on Phase 3.**

| | statements | note |
|---|---|---|
| `src/` at segment start | **2005 / 2100** | margin **95** |
| T1 (F10) | **−2** | delegating removes a branch |
| Segment 14 — ACO probes | **+12** | measured, not estimated |
| Segment 15 — PSO | ~25 | sketched against `pso.py`'s existing probe |
| Segment 15 — Hybrid-specific | ~8 | see below |
| Segment 16 — walkthrough | ~10–15 | likely `scripts/`, possibly 0 in `src/` |
| **Phase 2 total** | **~55–60** | leaves **35–40** |

**The structural finding that made this fit: Hybrid's probe is a
prefix-wrapper over ACO's and PSO's.**

```python
out = {f"aco_{k}": v for k, v in self._aco.probe().items()}
out.update({f"pso_{k}": v for k, v in self._pso.probe().items()})
```

Every field added to ACO appears in Hybrid automatically, prefixed, **at zero
statement cost**. My first projection assumed Hybrid needed its own set and came
out at ~90 of 95 — a five-statement margin, which is not a margin. The real
figure is roughly 30 lower because the composition already exists.

**A second thing that keeps the cost down and is worth stating, because it
would otherwise look like an error:** extending the probe's returned dictionary
costs **nothing**. `return {...}` is one `Return` statement whether it carries
three keys or thirty. The cost of a probe is entirely in the computation behind
it, which is where it should be.

**I am not counting on Phase 3's restructure paying for any of this.** The
numbers above are against today's 95 with no assumed refactor credit. If
`allocation/` turns out statement-negative, that is Phase 3's margin, not this
phase's.

**Actual at close: `src/` 2015 / 2100, delta +10, margin 85.** Dashboard
unchanged — 177/1000 Python, 734/900 JS, 667/900 presentation.

## 2. T1 — F10 closed, and it was hiding a real difference

```python
-        if t <= 0:
-            return 0
-        return len(self.schedule[t - 1])
+        return len(self.events_at(t))
```

**Statement-negative: −2.**

**Identical at every timestep — 3 seeds × 60 steps = 180 comparisons, zero
mismatches.** Confirmed by capturing every value before the change and
comparing after, not by argument.

**And the duplication was hiding a behavioural difference, not just a stylistic
one.** Past the horizon the two doors did not agree at all:

```
before:  changed_edges(61)  ->  IndexError: tuple index out of range
after:   changed_edges(61)  ->  0        (events_at(61) returns ())
```

`events_at` guards its upper bound because F1's fix put the bound there
deliberately. `changed_edges` never had it. So F10 was not only *"the same
arithmetic in two places"* — the second copy was already subtly different, and
nobody had looked because nothing calls it past the horizon yet.

## 3. T2 — the probe surface that already exists

**Where:** `optimizer.probe()`, called once per timestep per arm at
`harness/trial.py:187`, written into `steps.parquet`'s `probe` map column at
`:245`. Not conditional — **every step, every arm, every trial.**

**What each arm recorded before this segment:**

| Arm | Fields |
|---|---|
| `astar` | `expansions` |
| `aco` | `lambda_branch`, `tau_ratio`, `iterations` |
| `pso` | `diversity`, `iterations` |
| `hybrid` | those two sets, prefixed, plus `aco_fraction`, `exchanges` |

**Cost:** `_lambda_branching()` and `_tau_ratio()` each scan the active mask,
O(n_slots) — ~1500 elements at `medium200`. Measured at **<2 ms per call** and
pinned by a test, because Phase 4 runs this at ≥100 trials per arm and "cheap"
is exactly the claim that stops being true unnoticed.

**Built on it rather than beside it.** `tau_ratio` already answers *"is there
any spread in the trails"*, so no second measure of spread was added; the new
fields answer the four questions it cannot.

## 4. T3 — the ACO probes, live

```
ACO probe, live (seed 1000, 300 evaluations):
  t= 0  changed 1470/1470  evap  345.32  dep  434  clamp   1470  tau [0.0150, 0.0425]
  t= 1  changed 1470/1470  evap   20.54  dep  276  clamp      0  tau [0.0031, 0.0569]
  t=21  changed 1520/1520  evap    3.41  dep  165  clamp  22492  tau [0.0002, 0.0879]
  t=59  changed   28/1488  evap    3.77  dep  165  clamp  21900  tau [0.0002, 0.0966]
```

Numbers, not verdicts. And they say something: **28 changed of 1488 at t=59**
is a colony that has converged, which no `"pheromone: OK"` would have told
anyone.

**What aggregating gives up, stated plainly:** *which* edges changed. Per-edge
trails at every step of every trial is the payload that took a response from
34 KB to 1.7 MB in segment 10, and Phase 4 multiplies that by ≥100 trials.
Colony-level counts answer *did it run*; they cannot answer *did it run on the
right edges*. `tau_deposited` is the partial substitute — the deposit loop
walks the best path, so a non-zero count is deposit-on-route by construction.

## 5. T4 — every probe shown inert, and one of them failed

Each mechanism disabled at source, run, probe pasted. All at `t=21`:

```
LIVE                          changed 1520/1520  evap  3.41  dep  165  clamp 22492

1. PHEROMONE FROZEN           changed    0/1520  evap  0.00  dep  462  clamp 22800
2. EVAPORATION OFF            changed  626/1520  evap  0.00  dep  410  clamp  1266
3. MAX-MIN BOUNDS REMOVED     changed 1420/1520  evap  2.49  dep  165  clamp     0
4. BEST ANT DEPOSITS NOTHING  changed 1520/1520  evap  0.43  dep    0  clamp 22800
```

Three of the four were unmistakable first time. **The third was not, and it is
the finding of this segment.**

### The bounds probe reported 22800 clamps on a codebase with no clamp in it

First version counted slots that were **outside** the bounds and then clipped:

```python
outside = active & ((self._tau < tau_min) | (self._tau > tau_max))
self._mech["clamped"] += float(outside.sum())
np.clip(...)
```

Delete `np.clip` entirely and it still reports **22800**. It was measuring the
*need* for a mechanism, not the mechanism. In a report that reads as
**"MAX–MIN bounds active"** about plain Ant System — which is exactly the claim
§5.2 says the bounds exist to support.

Fixed by measuring the clip's effect:

```python
before = self._tau.copy()
np.clip(self._tau, tau_min, tau_max, out=self._tau, where=active)
self._mech["clamped"] += float((active & (self._tau != before)).sum())
```

**This is segment 4's lesson in the instrument layer.** F1 was invisible in
`events_at`'s argument and visible only in which index was read: *observe the
effect, not the call.* I wrote a probe that observed the call.

**The other direction is checked too** — every inert test asserts the remaining
mechanisms still report non-zero, so a probe cannot pass by everything going
quiet at once.

## 6. Both mutations

**A — specified: the probe reads the pre-update table.**

```
E  AssertionError: trails never moved in a working colony
E  assert 0.0 > 0
```

F1's shape in the instrument layer, caught.

**B — mine: the per-call counters never reset.**

```
JS/Python suite:  8 passed
```

**Nothing caught it**, and what it reports is the problem:

```
  t= 0  evap   345.32  dep    434  clamp    1470
  t=10  evap   401.84  dep   2255  clamp  154194
  t=30  evap   473.00  dep   5555  clamp  603090
  t=59  evap   580.28  dep  10662  clamp 1267734
```

Every number rises smoothly and every number is plausible. A reader concludes
**"clamping intensifies sharply over the run"** — from an artefact of never
zeroing a counter. My eight tests all asserted `> 0`, which a running total
satisfies trivially.

Now covered by a test that silences the mechanism for a *second* call and
asserts exactly zero, so a cumulative counter still carrying the first call's
total fails:

```
E  AssertionError: deposits carried over from the previous call: 376.0
```

**Six consecutive segments.** The commissioned mutation confirmed a prediction;
the uncommissioned one found the defect.

## 7. Acceptance

| Check | Result |
|---|---|
| Suite | **376 passed, 0 failed, 0 skipped** |
| Lint, three trees | `All checks passed!` |
| `src/` | **2015 / 2100**, delta **+10**, margin 85 |
| Dashboard budgets | 177/1000 · 734/900 · 667/900 |
| `outputs/` before / after | **26 / 26** |
| New tests | `tests/test_probes.py`, **9 passed** |

## 8. Would I believe a number ACO produced?

**Yes — for the four things now instrumented, and no further, and the boundary
matters more than the answer.**

What I would now defend: that pheromone moves, that evaporation removes mass,
that the MAX–MIN bounds actually bind, that the best ant reinforces something.
Each is a count, each is falsifiable, and each has been seen reporting zero
against a broken mechanism. Before this segment none of that was checkable from
a recorded run — `tau_ratio` would have looked perfectly healthy on a frozen
table, because a frozen table still has spread.

**What I would not yet defend, and nobody should quote:**

- **That deposit lands on the *right* edges.** `tau_deposited` counts slots the
  loop touched. It walks `best_path`, so the count is deposit-on-route by
  construction — but if `find_slot` returned the wrong slot the count would be
  identical. Catching that needs per-edge data, which is the payload we
  deliberately did not send.
- **That the *magnitudes* are right.** Every probe here answers *did it run*.
  None answers *did it run correctly* — an evaporation rate ten times too high
  reports a large `tau_evaporated` and looks healthy.
- **Anything about PSO or the Hybrid.** Segment 15.

**The honest summary: ACO is no longer a black box that produces plausible
numbers. It is a box with four windows in it.** That is a real change from
where this started, and it is less than "ACO is verified" — which is the
distinction Phase 2's gate was written to force, and the reason it says
*"reported inert"* rather than *"confirmed working"*.
