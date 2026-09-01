# SEGMENT 4 — The Invariants, and F1

**Phase 0.5 · Defect triage · Segment 1 of 2**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` §4.4 and §10.3, and `decisionLedger.md` §4 (F1). `WORKFLOW_LOG.md` Entries 001–003 record Phase 0.
> Append your findings to the **bottom** of this file. Do not modify the spec text above it.

---

## Goal

Write the three Layer 1 invariants, **watch I2 fail on the current code**, then fix F1 and watch it pass.

F1 is the most consequential defect in the project. `state_at(t)` applies `schedule[t-1]`, so `schedule[k]` is the transition k→k+1 — but `events_at(t)` returns `schedule[t]`, which is **the events that have not happened yet**. Structurally this is a component reading the future.

The effect: `RecencySignal` fires 1.0 one timestep early, so by the step where pheromone is actually stale it has already decayed to 0.7. **Every recency-driven result the project has ever produced ran on a misaligned signal** — including the allocation experiment that is the project's stated novelty. That result is a void, not a weak finding.

## Why the ordering matters more than the fix

The fix is one line. The value is in the sequence.

If you fix F1 and then write a test, you never learn whether the test would have caught anything — it might pass regardless. **Writing I2 first, watching it fail, then fixing, then watching it pass** turns a one-line repair into a permanent guard with evidence in the log that the guard bites.

Your own observation stands: after the fix that failure is unreproducible without reverting. **Capture it verbatim while you can.**

---

## ⚠️ T0 — MEASURE FIRST (D29)

Surface is at **1998 / 2100** — margin 102.

Sketch I1–I3 and the F1 fix, count the statements added to `src/`, report. Stop if it breaches.

**Design preference, not a requirement:** prefer a **test-side observer** over instrumenting `src/`. Production code should not carry test scaffolding, and a spy costs zero statements against the cap. If the invariants genuinely cannot be expressed without a hook in `src/`, say so in T0 with the reason — that is a legitimate answer, not a failure.

---

## Scope

**In scope**
- `tests/` — the three invariants and their supporting machinery
- `src/dynaswarm/core/timeline.py` — the F1 fix
- `src/dynaswarm/analysis/recovery.py` and `src/dynaswarm/analysis/plots.py` — **only if T3 shows they need it**
- One local commit

**Out of scope**
- **F2 and F3** — segment 5. You will pass close to F2 while reading the controller. Leave it.
- `load_events()` — segment 5
- The optimizers, the control layer, `conf/`, `scripts/`, the dashboard
- Anything under `outputs/` — do not modify or delete the five existing runs
- `git push`

---

## Tasks

### T1 — Write the invariants. Do not fix anything yet.

Three tests. **I2 is expected to fail.** That is the point, and a passing I2 at this stage means the test is wrong.

**I1 — no oracle leakage.**

> No optimizer, policy or observation may receive `optimum`, **or any quantity computed from it**.

`excess` is `cost / optimum − 1` and is therefore the canonical forbidden value (D26). Self-knowledge is permitted — an arm's own cost, how it changed, whether its path broke — because a deployed system has those without an oracle.

Implement as an **object-graph walk**, not a field-list check: walk what is reachable from each optimizer and assert no oracle-derived value is held. A field list only catches the mistake you thought of; a walk catches someone passing a whole `StepRow`, or a policy stashing a harness reference.

**I2 — no access to future state. ← this is the one that catches F1.**

> No component may reference the schedule or any graph state at t′ > t.

Run a real trial with the timeline observed, record the maximum index each caller touches, assert it never exceeds the current timestep.

**I3 — no cross-arm references.**

> No arm may hold a reference into another arm's internals.

The Hybrid's own ACO↔PSO exchange is **the only sanctioned channel of its kind** and must be asserted as such — not merely excluded, but named as the single permitted exception, so adding a second one later fails loudly.

### T2 — Run them, and capture I2's failure verbatim

Run all three. Paste the **complete, unedited** failure output for I2 — the assertion, the indices involved, the timestep at which it first diverges.

This output is the evidence that the guard works and that F1 was real. **It cannot be regenerated after T3 without reverting the fix.** Treat it as the segment's primary artefact.

If I1 or I3 also fail, **stop and report.** They are expected to pass — a failure means either the test is wrong or there is a defect nobody has found, and both need a ruling before you continue.

### T3 — Fix F1

The temporal contract, from `ARCHITECTURE.md` §4.4:

> `schedule[k]` is the transition from state *k* to state *k+1*.
> Therefore the events that **produced** state *t* are `schedule[t-1]`.
> `events_at(t)` must return `schedule[t-1]`.

Fix `events_at()` to satisfy it. Mind the boundary at `t = 0` — there is no `schedule[-1]`, and Python will happily hand you the last element instead of raising.

The unused `changed_edges()` already uses the correct convention. Check it, and say whether it is now consistent with `events_at()` or whether one of them still disagrees.

Then re-run I2 and paste the passing output beside the failure from T2.

### T4 — F1's blast radius

Correcting `events_at()` silently changes what two consumers produce, because both were written against the wrong indexing:

- `analysis/recovery.py` — the damage window
- `analysis/plots.py` — `recovery_profile`'s event alignment

**This is verification, not rewriting.** Take one existing run — `outputs/2026-08-30/22-53-36` has a recovery profile already — and produce, for both:

1. The output **before** the F1 fix (stash or revert temporarily; do not commit the revert)
2. The output **after**
3. The difference, stated concretely — how many disruptions detected, how the damage window shifted, whether any transient moved into or out of scoring range

Then answer the question that matters: **did these two simply inherit the off-by-one, or does either compensate for it?**

- **Inherited** → the fix propagates and they are now correct. Nothing to change. Say so, with the evidence.
- **Compensates** → the compensation must come out, or the fix double-counts. Correct it, and show the corrected output.

One piece of luck worth stating: **recovery analysis has never produced a reported number.** Only exploratory runs. So there is no published result to invalidate — you are correcting the tool before it was ever used in anger.

### T5 — Commit

Whole tree. **Do not push.**

```
segment 4: temporal invariants and F1 (phase 0.5)

Adds three Layer 1 invariants: no oracle leakage, no access to future
state, no cross-arm references. I2 was written first and observed failing
on the unfixed code; its output is recorded in the findings.

Fixes F1 — events_at() returned schedule[t] where the temporal contract
requires schedule[t-1], so every component reading it saw one timestep
into the future. RecencySignal fired a step early, misaligning every
recency-driven result including the allocation experiment.

Verifies F1's blast radius through analysis/recovery.py and
plots.recovery_profile.

Spec + findings: currentWorkFlow.md
Log: WORKFLOW_LOG.md entry 004
```

---

## Constraints

| | |
|---|---|
| **T0 before any implementation** | |
| **Do not fix F1 before I2 exists and has been observed failing** | The ordering is the deliverable, not the fix |
| **Do not weaken I2 to make it pass** | If it fails after the fix, the fix is wrong or the test is — report, do not adjust |
| **Do not touch F2 or F3** | Segment 5 |
| **Do not commit a temporary revert** | T4 needs a before/after; the revert is scratch |
| **No existing test deleted, weakened or skipped** | If one starts failing because F1 was fixed, **report it** — that is highly informative, it means the test encoded the bug |
| **Do not push** | |

That last one deserves emphasis. **If fixing F1 breaks an existing test, do not fix the test.** A test that passed with the off-by-one and fails without it was asserting the buggy behaviour, and that needs a ruling, not an edit.

---

## Acceptance check

```bash
# 1a. In-scope changes only
git diff --stat -- src/ tests/
# 1b. Nothing elsewhere
git diff --stat -- conf/ scripts/ README.md dashboard/ 2>/dev/null

# 2. Full suite
./.venv/bin/pytest -q -m "not slow"

# 3. Lint
./.venv/bin/ruff check src/ tests/

# 4. Statement budget, count reported against 2100
./.venv/bin/pytest -q -k statement_budget -s

# 5. The three invariants, by name
./.venv/bin/pytest -q -k "oracle or future_state or cross_arm" -v

# 6. t=0 boundary is handled
python -c "
from dynaswarm.core.timeline import GraphTimeline
print('events_at(0) ->', 'no crash, no wraparound — verify manually')"

# 7. Committed, not pushed
git log --oneline -2
git status --short --branch | head -1
```

**Expected:** in-scope only · all tests pass including the three new · lint clean · count under 2100 · the three invariants pass **by name** · `t=0` returns empty rather than wrapping to the last element · commit on top, ahead 1, unpushed.

**Paste verbatim, in this order:**

1. **The T0 measurement** — sketch cost, count before and after
2. **I2's failure output before the fix** — complete and unedited. *The segment's primary artefact.*
3. **The one-line diff of the F1 fix**
4. **I2's passing output after the fix**
5. **T4's before/after** for recovery and the recovery profile, with your verdict: inherited, or compensating?

---

## Definition of done

All seven checks pass. All five artefacts pasted, **in order**, with I2's failure captured before the fix. The blast-radius question answered with evidence rather than assertion. Commit exists, unpushed. FINDINGS appended below.

Segment 5 — F2, F3 and `load_events()` — follows verification. **Do not start it.**

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->
