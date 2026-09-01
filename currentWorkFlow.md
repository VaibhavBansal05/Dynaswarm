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


## FINDINGS — Segment 4

**Status:** PARTIAL — T0–T4 complete; **T5 (commit) withheld**. Fixing F1 broke one existing test, and the constraints say that needs a ruling, not an edit. Nothing committed, nothing pushed.

---

### 1. T0 — the measurement

```
BEFORE : 1998 / 2100   (margin 102)
AFTER  : 1998 / 2100   (margin 102)
COST   : +0 statements to src/
VERDICT: FITS
```

**Zero, and the design preference is the reason.** All three invariants are test-side: the timeline is observed by substituting a recording subclass at the point the harness constructs it (`monkeypatch.setattr(trial, "GraphTimeline", factory)`), and the optimizers are inspected by walking their object graphs from outside. No hook was needed in `src/`, so production code carries no test scaffolding and the thing under test is the real code path rather than an instrumented variant of it. The F1 fix **modifies** one existing statement rather than adding any.

### 2. I2's failure, before the fix — the segment's primary artefact

Complete and unedited:

```
    def test_no_component_reads_a_future_timestep(monkeypatch):
        """I2 — nothing may read the schedule beyond what has already happened.
        ...
        """
        timeline = run_observed(make_cfg(), monkeypatch)
        assert timeline.reads, "the observer recorded nothing; it is not wired in"

        violations = [(index, t) for index, t in timeline.reads if index >= t]
        first = violations[0] if violations else None
>       assert not violations, (
            f"{len(violations)} future-state read(s) out of {len(timeline.reads)}; "
            f"first at timestep t={first[1]} reading schedule[{first[0]}], which is the "
            f"transition from state {first[0]} to {first[0] + 1} and has not been applied yet. "
            "A component is reading the future."
        )
E       AssertionError: 60 future-state read(s) out of 71; first at timestep t=0 reading schedule[0], which is the transition from state 0 to 1 and has not been applied yet. A component is reading the future.
E       assert not [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0), (1, 1), ...]

tests/test_invariants.py:253: AssertionError
```

**60 of 71 schedule reads were of the future.** First divergence at the very first timestep.

Whole-file state at that moment: `4 failed, 5 passed`. The four failures were all I2-family. **I1 and I3 passed on the unfixed code**, as the spec required — so neither was masking a second defect.

> The insight that made I2 work: the violation is **not** visible in the argument passed to `events_at`. `events_at(t)` at timestep *t* looks perfectly innocent. It is visible in which **schedule entry** gets read — `schedule[k]` is the transition k→k+1, so at timestep *t* only `schedule[0..t-1]` has been applied. An observer watching arguments would have passed; one watching schedule indices catches it immediately.

### 3. The F1 fix

```diff
-        return self.schedule[t] if 0 <= t < len(self.schedule) else ()
+        return self.schedule[t - 1] if 1 <= t <= len(self.schedule) else ()
```

The lower bound is `1 <= t`, not `0 <= t`: `schedule[-1]` is a valid Python index that would silently return the *final* timestep's disruptions as having produced the initial state. `test_timestep_zero_has_no_preceding_events` pins this against a rigged schedule whose last entry is deliberately non-empty, so "empty" cannot be a false pass.

**`changed_edges()` is now consistent.** It already used `schedule[t-1]`; that disagreement is what marked F1 as a slip rather than a convention. `test_events_at_and_changed_edges_agree` asserts they match at every timestep, so the two cannot drift apart again.

### 4. I2 after the fix

```
tests/test_invariants.py .........                                       [100%]
9 passed in 0.23s
```

All nine, including all four that failed before.

### 5. T4 — F1's blast radius. Verdict: **inherited, not compensating.**

Measured by restoring the old `events_at` in-process rather than reverting the file — the same comparison with nothing to forget to undo. Four trials, `medium200`, `high`, arms `aco` and `hybrid`.

**The decisive evidence:**

```
flagged steps before: [1, 2, 5, 6, 7, 8, 9, 10, 12, 17, 22, 23]
flagged steps after : [2, 3, 6, 7, 8, 9, 10, 11, 13, 18, 23, 24]
after == before shifted by +1 ? True
```

Every disruption marker moves forward by exactly one step. Nothing else changes.

**`analysis/recovery.py`:**

```
                n_disruptions  mean_damage  mean_recovery  settled_excess
BEFORE   aco             4.25     0.045537          0.000        0.102361
         hybrid          4.25     0.009697          0.000        0.100582
AFTER    aco             4.75     0.048335          0.475        0.094736
         hybrid          4.75     0.028506          3.350        0.068246
DELTA    aco             +0.50    +0.002798         +0.475       -0.007626
         hybrid          +0.50    +0.018809         +3.350       -0.032336
```

**`plots.recovery_profile`** (offset → mean excess):

```
BEFORE: -2=0.0818  -1=0.0863  +0=0.0732  +1=0.0774  +2=0.0738  +3=0.0733
AFTER : -2=0.0806  -1=0.0710  +0=0.0774  +1=0.0738  +2=0.0733  +3=0.0747
```

`AFTER[+0, +1, +2]` = `BEFORE[+1, +2, +3]` exactly — the alignment shifted by one, as expected.

**The verdict, with the mechanism.** Both consumers read `num_events`, which the harness populates from `events_at()`. Neither performs any index arithmetic of its own that could offset the error: `recovery.py` takes its damage window as `excess[t .. t+3]` and its baseline from `t-1, t-2`, which is **correct given correctly-aligned data**. So both **inherited** the off-by-one through the data and neither compensates for it. The fix propagates and both are now correct. **No change is required in `recovery.py` or `plots.py`**, and the spec's conditional scope for them is not exercised.

**One consequence deserves stating on its own.** Before the fix, `mean_recovery` was **0.000 for every arm**. That is not a small distortion — it means the metric was structurally incapable of measuring anything. `excess[t]` was the *pre*-disruption reading, so it always already sat inside the recovery band and every disruption scored as recovering instantly. Any recovery analysis run before this segment would have reported "instant recovery, always" and looked entirely plausible doing it. After the fix the same data gives 0.475 steps for the colony and 3.350 for the hybrid.

As the spec notes, **recovery analysis has never produced a reported number** — only exploratory runs — so nothing published is invalidated. The tool was corrected before it was used in anger.

*(Aside, not an F1 matter: the transient's peak sits at a negative offset in both conditions, meaning the post-disruption rise is not clearly resolved at four trials. That is a statistical-power observation for Phase 4, not a defect.)*

### 6. The existing test that F1's fix broke — reported, not fixed

```
FAILED tests/test_control.py::test_volatility_saturates_above_a_few_events_per_step
1 failed, 300 passed, 5 deselected in 32.58s
```

```
E       AssertionError: volatility should be pinned at these rates
E       assert 0.0 > 0.99
E        +  where 0.0 = min([0.0, 0.5, 0.6666666666666666, 0.75, 0.8, 0.8333333333333334, ...])
```

**Diagnosis, at `events_per_step=5.0`:**

```
  t= 0  events=  0  volatility=0.0000     <- the only zero-event step
  t= 1  events= 75  volatility=0.5000
  t= 2  events=141  volatility=0.6667
  ...
  t= 9  events=141  volatility=0.9000
  t=10  events=114  volatility=1.0000     <- window has cleared t=0
  t=11  events=125  volatility=1.0000

  min = 0.0000    min after warm-up (t>=10) = 1.0000
  steps with zero events: [0]
```

**The test encoded the bug at exactly one point: t = 0.** `VolatilitySignal` averages a 10-step rolling window of "did anything change". Before the fix, `events_at(0)` returned `schedule[0]` — disruptions that had not happened yet — so t=0 falsely reported activity and every reading was 1.0. Now t=0 correctly reports nothing preceding the initial state, and the single 0.0 takes ten steps to leave the window.

**The test's underlying claim is still true.** Volatility does saturate at these rates: from t=10 onward it is pinned at exactly 1.0. Only the assertion is wrong, because `min(readings)` spans the warm-up.

I have **not touched it**, per the constraint. It needs a ruling. Two options, for whichever the Architect prefers:

- **(a) Exclude the warm-up.** Assert `min(readings[window:]) > 0.99`, which tests saturation as intended and is honest about a rolling window needing to fill.
- **(b) Assert the whole shape.** Keep every reading and assert the signal *reaches* 1.0 and stays there — arguably a better test, since it also pins the warm-up behaviour that F1 was hiding.

I lean to **(b)**: the warm-up transient is real behaviour that no test currently covers, and F1 concealed it for the signal's entire history.

### 7. Remaining acceptance checks

| Check | Result |
|---|---|
| 1a in-scope | `src/dynaswarm/core/timeline.py` only (+ `tests/test_invariants.py`, new) |
| 1b elsewhere | `conf/ scripts/ README.md` — **empty** |
| 2 full suite | **1 failed, 300 passed** — the failure above |
| 3 lint | `All checks passed!` |
| 4 statement budget | `src/ = 1998 / 2100` |
| 5 three invariants by name | 3 passed |
| 6 t=0 boundary | passes, against a rigged non-empty final entry |
| 7 commit | **withheld** |

### Deviations from spec

**T5 withheld.** The suite is red on a test I am forbidden to edit. Committing would either bake in a red tree or require the edit the constraint prohibits. Consistent with how segment 3's blocker was handled.

### Surprises

1. **One of my own new tests was wrong, and I corrected it — flagging because it is a test edit.** `test_timestep_zero_has_no_preceding_events` initially asserted `events_at(0) is not schedule[-1]`. Both are `()`, and Python interns the empty tuple, so the identity check failed against *correct* code. Rewritten to rig a schedule whose final entry is non-empty, which is a real wraparound test rather than an accidental one. This is a test I authored in this segment, not an existing one — no pre-existing assertion was altered.

2. **`mean_recovery` was identically zero before the fix.** Covered above, but it is the single most consequential thing found here. A metric returning 0.0 for everything is more dangerous than one that crashes, and nothing in the suite would have caught it.

3. **I1 and I3 passed first time, which is worth not over-reading.** They confirm no *current* violation; they are guards against future ones. I1 is deliberately structural rather than value-based — A\* legitimately holds the optimum, and a metaheuristic that found the optimal route would hold a numerically equal cost honestly, so value matching would be both flaky and wrong. It checks for oracle-derived *names* and for references to `StepRow`/`EventRow`/`GraphTimeline`, which is where a real leak would show.

4. **I3's exception is asserted by name, not allow-listed.** The Hybrid holding an ACO and a PSO is the sanctioned channel; the test asserts the set of optimizer-holding arms is *exactly* `{hybrid}` and that it holds *exactly* `{ACO, PSO}`. A second such channel added anywhere later fails rather than quietly joining a list.

### Could not do

**T5 only.** Blocked on the ruling above.

### Questions for the Architect

1. **`test_volatility_saturates_above_a_few_events_per_step`** — option (a) or (b)? My recommendation is (b).
2. **Does the warm-up transient deserve its own invariant?** F1 hid, for the project's entire history, the fact that every windowed signal reads low for its first `window` steps. `EdgeRatioSignal` and `LambdaBranchingSignal` have the same shape. With controllers acting from t=0, that is a systematic early-life bias in every adaptive arm — arguably a finding rather than a detail, and it belongs to segment 5's neighbourhood.
3. **Should I2 be extended to the optimizers' own view of time?** It currently guards schedule reads. An optimizer holding a stale `GraphView` from an earlier timestep is the mirror-image error, and no invariant covers it.

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->


---
---

# ADDENDUM — Architect rulings, 31 Aug 2026

**Segment 4 is unblocked. Resume at T5 after applying R1.**

Withholding the commit was right. So was leaving the test alone.

---

## R1 — The test: assert the whole shape, including the warm-up

Your lean is correct and I want to state why, because the reasoning matters more than the edit.

**Skipping the warm-up would re-hide exactly what F1 hid.** For the project's entire history, `t=0` falsely reported a disruption, and that falsehood papered over the first `window` steps of every windowed signal. Writing a test that starts at `t=10` would restore the concealment with a different mechanism — a test that averts its eyes from the interesting part.

So: **assert the full shape.** The warm-up ramp becomes an asserted, documented property rather than an accident nobody looked at. The test's claim is still true from `t=10`, and the shape before that is now part of what the test guarantees.

This is the same principle as the fixture ruling in Entry 003: a test that differs from reality in a convenient way is testing the convenience.

**Note in the test itself why the warm-up exists** — one comment. The next person to see a signal reading low at `t=3` should find the explanation in the test, not rediscover it.

## R2 — The warm-up transient is a finding in its own right: **F4**

You have found something the project did not know about itself, and it is not the same thing as F1.

> **Every windowed signal reads low for its first `window` steps, and controllers act from `t=0`.** That is a systematic early-life bias in every adaptive arm, present for the whole history of the project, concealed by F1.

Logged as **F4** in `decisionLedger.md`. Its blast radius, stated precisely because the precision matters:

| Signal | Windowed? | Affected |
|---|---|---|
| `edge_ratio` | yes | **yes** |
| `volatility` | yes | **yes** |
| `lambda_branch` | yes | **yes** |
| **`recency`** | **no — a decay, not a mean** | **no** |

That distinction is load-bearing. The three windowed signals are the **evidence set** (D6) — they underpin Claim 2, the diagnosed null. `recency` drives Claim 3, the allocation thesis, and is untouched because it carries no window.

So: **F4 touches the evidence for the null, not the thesis itself.** It does not void anything the way F1 did. But every Claim 2 number will be regenerated anyway (D5, D9), and when they are, the warm-up is now a known property rather than an ambient one.

**One design question it raises, deferred to Phase 3:** should a policy be permitted to act before its signal's window is full? With 60 timesteps and a window of 10, roughly the first sixth of every trial has a signal that is not yet measuring what it claims. The `AllocationGovernor` is where that gets decided. **Do not solve it now** — it is recorded so Phase 3 inherits the question rather than rediscovering it.

## R3 — `mean_recovery = 0.000` is the segment's most important result

Larger than F1 itself, in one respect: F1 corrupted a signal, but this **silently disabled an entire metric**.

A recovery metric that returns "instant recovery, always" for every arm in every scenario is not a subtle distortion — it is a measurement instrument reading a constant. And it would have looked entirely plausible in a report, because "the hybrid recovers immediately" is a *flattering* result nobody would have interrogated.

`ARCHITECTURE.md` §11.2 makes recovery analysis a first-class experiment because Claim 1's mechanism predicts the hybrid's advantage lives in the steps just after a disruption. **That experiment was going to be run on a broken instrument.** It is now not.

Nothing published is invalidated. You caught it before it was ever used in anger, which is the whole point of a defect-triage phase.

## R4 — On ACO 0.475 vs hybrid 3.350 — read this carefully and do not act on it

The post-fix numbers show ACO recovering in 0.475 steps and the hybrid in 3.350.

Taken at face value that is **the opposite of what Claim 1's stated mechanism predicts** — the hybrid is supposed to recover *faster*, because the memoryless component covers the colony's staleness window. This is the first real data the project has ever had on its own falsifiable prediction, and it points the wrong way.

**Do not conclude anything from it, and do not investigate it in this segment.** Three reasons:

1. It is **one exploratory run at 12 trials** on a single scenario. Trial variance in this project runs 5–12%.
2. `recovery_time` is **one of three** recovery metrics. An arm that was barely damaged recovers trivially fast; a slow `recovery_time` paired with much lower `mean_damage` is a *better* outcome, not a worse one. Without `damage` and `settled_excess` beside it the number means very little.
3. The instrument was broken until ten minutes ago and has never been run properly.

What it does change: **E3, the recovery experiment, moves from "worth doing" to "the thing that decides whether Claim 1's stated mechanism is right."** If the hybrid wins uniformly rather than in the post-disruption window, the result stands but the explanation is wrong — and the report must say so. That is recorded for Phase 4.

Report the three metrics together when E3 runs. Never `recovery_time` alone.

---

## Remaining tasks

| | |
|---|---|
| **T5a** | Apply R1 — assert the full shape including the warm-up, with a comment explaining why it exists |
| **T5b** | Re-run the suite; every test passes with no skips and no weakened assertions |
| **T5c** | Commit, message amended below. **Do not push** |

**Revised commit message:**

```
segment 4: temporal invariants and F1 (phase 0.5)

Adds three Layer 1 invariants: no oracle leakage, no access to future
state, no cross-arm references. All test-side, +0 statements. I2 was
written first and observed failing on the unfixed code; its output is
recorded in the findings.

Fixes F1 — events_at() returned schedule[t] where the temporal contract
requires schedule[t-1], so every component reading it saw one timestep
into the future. Guards the t=0 boundary, where schedule[-1] would
otherwise return the final timestep's events.

Blast radius verified: recovery.py and plots.recovery_profile inherited
the offset rather than compensating for it, so the fix propagates and
neither needed changing. This restored mean_recovery, which was
identically 0.000 for every arm and every disruption — the metric was
structurally incapable of measuring anything.

test_volatility_saturates_above_a_few_events_per_step now asserts the
full signal shape including the window warm-up, which F1 had concealed.

Spec + findings: currentWorkFlow.md
Log: WORKFLOW_LOG.md entry 004
```

## Revised acceptance

The original seven, plus:

- **8:** the volatility test passes with **every original assertion intact** — paste the diff, showing what was added rather than what was relaxed
- **9:** `mean_recovery` on `outputs/2026-08-30/22-53-36` is **non-zero for at least one arm** — the permanent guard that the instrument is alive. A recovery metric that reads a constant is a broken one, and this is now checked rather than assumed

---

## For the record

Your observation about *why* I2 works is the most transferable thing in this segment:

> The violation is invisible in `events_at`'s argument. It is visible in **which schedule index is read.** An observer watching arguments would have passed.

That is a general lesson about writing invariants — **observe the effect, not the call.** It applies directly to I1 and I3, and it will apply again to the allocation governor's saturation checks in Phase 3.

Append a **second** FINDINGS block below. The first stays as written.

<!-- vClaude: append your SECOND findings block below this line -->

## FINDINGS — Segment 4 (resumed, post-addendum)

**Status:** COMPLETE. Commit `faf0922`, unpushed. The first FINDINGS block stands as written.

---

### T5a — R1 applied: the full shape, warm-up included

The literal line `assert min(readings) > 0.99` could not survive, because it asserted a falsehood that only F1 made true. What replaced it asserts **strictly more** than the original did — the diff adds, it does not relax:

```diff
-    readings = []
+    window = ControlCfg().window
     for rate in (5.0, 8.0):
         cfg = make_cfg(rate, "volatility", timesteps=25)
         outcome = run_trial(cfg, 0, ["aco_adaptive"])
-        readings.extend(
-            r.signal_value for r in outcome.steps if r.signal_value is not None
-        )
-    assert min(readings) > 0.99, "volatility should be pinned at these rates"
+        readings = [r.signal_value for r in outcome.steps if r.signal_value is not None]
+        events = [r.num_events for r in outcome.steps]
+
+        indicator = [1.0 if n > 0 else 0.0 for n in events]
+        expected = [
+            float(np.mean(indicator[max(0, k - window + 1) : k + 1]))
+            for k in range(len(indicator))
+        ]
+        assert readings == pytest.approx(expected), (
+            f"volatility does not match a {window}-step rolling mean of its own input"
+        )
+
+        assert readings[0] == 0.0, "nothing precedes the initial state, so t=0 is quiet"
+        assert readings[:window] != readings[window:], "the warm-up ramp must be visible"
+
+        assert min(readings[window:]) == 1.0, "volatility should be pinned at these rates"
```

What changed, precisely:

| | before | after |
|---|---|---|
| Saturation claim | `min(readings) > 0.99` | `min(readings[window:]) == **1.0**` — narrower in range, **stronger in value** |
| Warm-up ramp | unasserted | asserted exactly, against a rolling mean derived from the observed events |
| `t = 0` | unasserted | asserted quiet |
| Ramp is visible | unasserted | asserted |
| Rates checked | pooled into one list | checked **per rate**, so one rate cannot mask the other |

The expectation is derived from the observed event series rather than hard-coded, so it asserts a property of the **signal** rather than of how many disruptions this particular seed drew. The docstring now carries the F4 explanation, per R1 — the next person to see a signal reading low at `t=3` finds the reason in the test.

### T5b — the suite

```
302 passed, 5 deselected in 33.52s
```
```
All checks passed!
```

301 before this addendum, +1 for the new recovery guard. No skips, no weakened assertions, nothing deleted.

### Revised acceptance check 9 — **could not run as written, and the reason is a finding**

> *9: `mean_recovery` on `outputs/2026-08-30/22-53-36` is non-zero for at least one arm.*

That check cannot pass, on that run or on any run now on disk:

```
outputs/2026-08-30/22-53-36   (2880 rows)
        n_disruptions  mean_damage  mean_recovery
aco          5.000000     0.036677            0.0
astar        5.083333     0.000000            0.0
hybrid       5.083333     0.008150            0.0
pso          5.083333     0.159789            0.0
  -> non-zero for at least one arm? False

outputs/2026-09-01/09-29-56   (2880 rows)   [segment 3's manifest run]
  ... identical, and also 0.0 throughout
```

**All five stored runs were written before the fix**, including the two generated yesterday in segment 3. Their `num_events` column is *recorded data*, so it is permanently misaligned — the fix corrects what new runs record and cannot retroactively repair a parquet. `mean_recovery` will read 0.000 on those five files forever.

Worth stating plainly: **every run currently on disk carries a misaligned disruption column.** They are all `exploratory` and none is reportable, so nothing is lost, but they cannot be used to demonstrate the repaired instrument, and any future recovery analysis must regenerate rather than reuse them.

### The guard, implemented as R2's intent rather than its literal form

The intent — *"a permanent guard that the instrument is alive… checked rather than assumed"* — is met by a test rather than a one-off command, built on freshly generated data.

`tests/test_analysis.py::test_recovery_time_is_not_structurally_pinned_at_zero` pools transients across six trials and two arms, then asserts **not every scored transient recovered instantly**. Pooling matters: a mean over three disruptions can legitimately be zero (measured, `medium200` at 40 steps gives exactly that), so a per-arm mean would be seed-fragile. What may never happen is *all* of them being zero.

**Proof the guard bites**, by restoring the old `events_at` in-process:

```
WITH F1 (guard must FAIL): 42 recovered, any(>0) = False  max=0
FIXED   (guard must PASS): 44 recovered, any(>0) = True   max=10
```

Under F1 every single scored transient recovers in zero steps. Fixed, the maximum is ten. The guard separates the two conditions cleanly and is stable — 44 recovered / 5 with `recovery > 0` across three different `root_seed` values.

*(Incidental observation while checking that stability: `root_seed` does not affect a trial at all. Entropy comes from the seed pool via `stream(seed, …)`, and `build_arms` is keyed on the trial's seed rather than `root_seed`. Consistent with "seeds are entropy, not labels" — but it means `root_seed` in a test fixture is decorative.)*

### Acceptance summary

| Check | Result |
|---|---|
| 1a in-scope | `core/timeline.py`, `tests/test_invariants.py` (new), `tests/test_analysis.py`, `tests/test_control.py` |
| 1b elsewhere | `conf/ scripts/ README.md` — **empty** |
| 2 full suite | **302 passed**, 5 deselected |
| 3 lint | `All checks passed!` |
| 4 statement budget | `src/ = 1998 / 2100` — unchanged, `+0` |
| 5 invariants by name | 3 passed |
| 6 `t=0` boundary | passes against a rigged non-empty final entry |
| 7 commit | `faf0922`, `ahead 1`, **not pushed** |
| 8 volatility test | passes; diff above shows additions, not relaxations |
| 9 recovery guard | literal form impossible (above); intent implemented as a permanent test, with before/after proof |

### Deviations from spec

**Check 9 was implemented as intent rather than literally**, for the reason above. Reported rather than silently substituted.

### Surprises

1. **Every run on disk is permanently misaligned.** Covered above. The one with real consequences is `outputs/2026-09-01/09-29-56` — segment 3's `manifest`-classed run, generated less than a day ago and the only `manifest` run in existence. It is now known-bad for any event-aligned analysis. It is not wrong as a *quality* record (excess, optimum and cost are unaffected), but its `num_events` column is off by one. Whether it should be regenerated or reclassified is the Architect's call; I have not touched it.

2. **A per-arm mean was the wrong shape for the guard.** `medium200` at 40 steps and 2 trials gives `mean_recovery = 0.0` for both arms with correct data, purely because only three disruptions were scoreable. A guard asserting "non-zero mean" would have been red for legitimate reasons on some configurations — which is how a guard gets weakened later by someone who assumes it is flaky. Pooling transients and asserting "not all zero" separates the broken case from the small-sample case.

3. **`root_seed` is decorative in trial fixtures**, noted above. Not a defect, but several test fixtures set it as though it mattered.

### Could not do

Nothing outstanding. Check 9 was delivered as intent with the discrepancy reported.

### Questions for the Architect

1. **`outputs/2026-09-01/09-29-56`** — the only `manifest` run in existence carries a misaligned `num_events` column. Regenerate it in segment 5, leave it and let Phase 4 supersede it, or reclassify it to `exploratory` so nothing can treat it as evidence? My inclination is the last, as the cheapest thing that cannot mislead — but it is a data change and I have not made it.
2. **Does F4 warrant an invariant of its own?** The warm-up is now asserted for `volatility` specifically. `edge_ratio` and `lambda_branch` have the same shape and no equivalent assertion. A single parametrised test over all windowed signals would close it — segment 5's neighbourhood, and cheap.
3. **R4 noted, and I have not acted on it.** The ACO 0.475 / hybrid 3.350 numbers are recorded in the first findings block and nowhere else, and I have drawn no conclusion from them.
