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
