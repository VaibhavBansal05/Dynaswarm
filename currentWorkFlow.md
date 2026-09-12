# SEGMENT 20 — Build `allocation/`

**Phase 3 · Restructure · Segment 4 of 5**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` **§7 in full — §7.1 why it is being rebuilt, §7.2 the design, §7.3 what `recency` is** — plus **§10.3 (invariants I1–I3)** and §2.3. `WORKFLOW_LOG.md` **Entry 005** rules on F7, **Entry 019** on F14.
> Append your findings to the **bottom** of this file.
>
> ## ⛔ YOU DO NOT COMMIT
>
> Rudra commits. Leave the tree unstaged, paste `git status --short`, and paste the commit message as a copyable block **with no `Co-Authored-By` trailer**. No `git add`, no `git commit`, no `git stash`, never `git add -A`.

---

## Goal

**Build the machine the thesis runs on.** §7.2 specifies it completely: an observation object, three policies, and a governor. This segment builds those three things and proves them.

**It does not wire them to any arm.** That is segment 21, deliberately — because the machine has to be shown correct before anything depends on it, and because §7's whole reason for existing is that the previous control layer was trusted without that.

---

## ⚠️ T0 — MEASURE FIRST, and this one can stop the segment

`src/` is at **2041 / 2100**. **Fifty-nine statements.** A new package plus a governor plus three policies is not obviously smaller than that.

**Before writing anything, project:**

1. what `allocation/` costs
2. what the existing `control/` **releases** — this is a restructure, so say whether it is net-negative, neutral, or positive, and **do not assume**: measure the current `control/` and say what of it survives
3. what segment 21 will need on top

**If the total exceeds 59, stop and report with the numbers.** Segment 14 did this properly and it changed the design; segment 12 did not and hit the wall at `702/700`. **The lesson recorded then was not "raise caps sooner" — it was find out before you are committed.**

If the honest answer is that the cap needs raising, say so with the arithmetic, and **derive the new number rather than picking one** — Entry 012 records what happens when a cap is lifted from the state being left behind.

---

## T1 — `AllocationObservation`

§7.2 gives the full field list. Build it exactly.

**Two hard constraints, and both need tests, not comments.**

**Every field derives from state at `t′ ≤ t`.** This is I2. Constructing the observation is the **only** channel by which a policy learns anything about the world — so if anything leaks in from `t+1`, the entire thesis is reading the future. **F1 was exactly this defect one layer down**, and it voided every recency-driven result the project had.

**No field may derive from the oracle.** This is I1, and §7.2 records that an earlier draft carried `excess_last_step` and had to be removed, because excess is `cost/optimum − 1` and a policy that knows its own excess knows how far from optimal it is — information no deployed router has.

**Test it the way segment 6 tested the FastAPI boundary:** make the oracle genuinely unreachable, then construct an observation and assert it still works. A meta-path blocker or equivalent. **Asserting "we did not call it" is not the same as proving it cannot be called** — and this project has a rule about that, from four separate segments.

The three self-knowledge fields — `own_cost`, `own_cost_delta`, `path_invalidated` — are the replacements. §7.2 notes `own_cost_delta` is confounded by the graph itself becoming cheaper or dearer, **and accepts that**, because a deployed system faces the same confound. Keep that reasoning in the docstring; it is a defensible design choice that looks like an oversight if unexplained.

## T2 — The three policies

Per §7.2. `propose(obs) -> float` returns a **target**, not a delta.

| Policy | What it must do |
|---|---|
| `FrozenAllocation` | return `obs.current_fraction` unchanged. **A policy object, never an absent one**, so the ablation twin runs identical code paths to the thesis arm |
| `IncrementalAllocation` | the existing ±σ pressure-vs-EMA rule, **preserved exactly** — continuity with prior results depends on it being the same rule, not a tidied one |
| `ScheduledAllocation` | an open-loop timetable, ignoring everything but `t` |

**`LearnedAllocation` is NOT built.** Phase 4, and only with mentor sign-off (D7, O2).

### F7 dies here, and Entry 005's ruling is the acceptance criterion

`harness/arm.py:228` built the old prescheduled controller **with no arguments**, so `start == end == 1.0` and it varied nothing while logging itself as an active controller.

Its role makes that worse than an ordinary bug. §7.2: *"the honest control for feedback itself — if a schedule matches a sensing policy, what helped was varying, not sensing."* **A `ScheduledAllocation` that varies nothing produces results identical to the frozen arm while claiming to be the control**, and the conclusion drawn would be *"an open-loop schedule does not help either"* — a false null on the one arm whose entire job is to falsify the control story.

> **Entry 005's ruling stands and is the bar: `ScheduledAllocation` is not complete until a test asserts it actually varies something.**

Not that it can vary. That it does, with the parameters it is constructed with by default.

### F8 dies here too

The old `current.get(name, 0.0)` fallback was left unreachable behind F2's guard and **encodes `0.0` as an initial value** — which would come alive as a wrong default if the guard were relaxed. Entry 005 deferred it to this restructure precisely so it would not be touched twice. It should not survive into `allocation/`.

## T3 — The governor

**Enforcement lives here, not in policies.** The governor wraps every policy and is the only thing that touches the optimizer. Per §7.2:

- clamp to `[0.05, 0.95]`
- rate-limit `|Δ| ≤ sigma_max` per step
- **record proposed and applied separately**, so clipping is visible in the data rather than silent
- accumulate saturation statistics — fraction of steps at a bound, and whether the value moved at all

**Why proposed-and-applied both:** a policy pressing hard against a clamp and a policy proposing exactly the clamped value are indistinguishable from the applied series alone, and they mean opposite things about whether the policy is working. **One number cannot carry both.**

## T4 — The saturation check, automated

§7.2 makes this a gate, not a guideline. A reported allocation run must satisfy **both**:

- the fraction **moved** — more than one distinct value
- **under 20%** of steps at a bound

**A run failing either is not reportable.** Make that a check the code performs, not an instruction someone remembers — Phase 2's containment lesson: *a convention lasts exactly as long as the person who remembers it.*

Decide and state what "not reportable" does mechanically: refuse, warn, or stamp the run. Whatever you choose, **it must be visible in the run's own record**, in the way `run_class` is.

## T5 — Tests

| Test | Catches |
|---|---|
| **An observation can be built with the oracle unreachable** | I1, proved not asserted |
| **No field reads state from `t+1`** | I2. F1 one layer up |
| **`FrozenAllocation` returns exactly `current_fraction`** | The ablation twin is a twin |
| **`IncrementalAllocation` reproduces the old rule's output** | Continuity. Same inputs, same numbers as `control/`'s version |
| **`ScheduledAllocation` varies something with default arguments** | **F7. Entry 005's bar** |
| **The governor clamps, rate-limits, and records both series** | |
| **A saturated run is flagged by the code** | T4, and shown flagging |
| **A policy cannot reach the optimizer except through the governor** | Structural — assert it, since "enforcement lives in the governor" is only true if nothing else can |

**Every invariant test shown failing against deliberately wrong input**, and the corruption pasted. **And per Entry 019: every test must call the production entry point, not a re-implementation of it.** That failure appeared in the segment written to prevent it.

## T6 — Mutations, two, one of them yours

**Specified:** make the governor record the **proposed** value in the applied column. Every run then shows a policy that is never clipped, saturation reads zero, the automated check passes, and the allocation series looks healthier than it is. **A clipped policy that reports itself unclipped is the exact shape of F7** — machinery reporting a state it is not in.

**Yours.** Eleven consecutive segments.

## T7 — Show it

1. **T0's projection and the actual**, with what `control/` released
2. **The oracle-unreachable observation test**, shown passing with the oracle genuinely blocked
3. **`ScheduledAllocation` varying something** — the values, at default construction
4. **The governor's proposed-vs-applied series** on a run where clipping actually happens
5. **The saturation check flagging a saturated run**
6. Both mutations, and every invariant shown red
7. **Your read: is this machine ready to carry the thesis?** Segment 21 wires four arms to it and everything the project claims runs through it

## T8 — Hand over, do **not** commit

`git status --short`, the commit message as a copyable block, no `Co-Authored-By`, one line confirming complete and uncommitted.

---

## Constraints

| | |
|---|---|
| **Project the whole restructure before writing** | Stop and report if it exceeds 59 |
| **No arms wired** | Segment 21. Build the machine, prove it, then connect it |
| **`LearnedAllocation` not built** | Phase 4, mentor sign-off (D7, O2) |
| **`IncrementalAllocation` preserved exactly** | Continuity depends on it being the same rule |
| **Enforcement only in the governor** | And asserted, not assumed |
| **Every test calls the production entry point** | Entry 019 |
| **No re-initialisation** | Entry 018 R2 |
| **No dashboard work** | The allocation view is segment 21 or later |
| **Do not commit, do not push** | |

---

## Acceptance check

```bash
git diff --stat -- src/ tests/
./.venv/bin/pytest
./.venv/bin/ruff check src/ tests/ dashboard/ scripts/
./.venv/bin/pytest -k "budget or statement" -s
ls outputs/
git status --short                       # UNSTAGED, UNCOMMITTED
```

**Paste verbatim:** the projection and the actual with `control/`'s release · the oracle-unreachable proof · `ScheduledAllocation`'s values at default construction · proposed-vs-applied where clipping happens · the saturation check flagging · both mutations · every invariant shown red · your read on whether the machine is ready.

---

## Definition of done

Green suite, artefacts pasted, **F7 and F8 closed**, uncommitted with the message pasted, FINDINGS appended.

**After this the control layer exists and has been proven.** Segment 21 connects the four arms — and the thesis runs for the first time.

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->
