# SEGMENT 5 — F2, F3, and the Loose Ends

**Phase 0.5 · Defect triage · Segment 2 of 2**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md`, and `decisionLedger.md` §4 (F2, F3) plus D30, D31, D32. `WORKFLOW_LOG.md` Entry 004 records segment 4 and the rulings this segment executes.
> Append your findings to the **bottom** of this file. Do not modify the spec text above it.

---

## Goal

Close Phase 0.5. Two remaining defects, one reclassification, and two gaps carried forward.

F1 was the dangerous one and it is done. What remains is smaller but not trivial — **F3 in particular is thinking work, not editing work**, and it has a dependency that means it can be repaired here but not run until Phase 4.

---

## ⚠️ T0 — MEASURE FIRST (D29)

Surface at **1998 / 2100** — margin 102. Sketch, count, report, stop if it breaches.

Test-side preferred wherever the work allows it, as in segment 4.

---

## Scope

**In scope**
- `src/dynaswarm/control/controllers.py` — F2
- `scripts/cross_evaluate.py` — F3
- `src/dynaswarm/analysis/load.py` — `load_events()` filter
- `tests/` — new and parametrised tests
- `outputs/2026-09-01/09-29-56/` — **the one authorised exception** to the never-touch-outputs rule, under D31 and only as T1 specifies
- One local commit

**Out of scope**
- Every other run under `outputs/` — do not modify, reclassify or delete
- The optimizers, the environment, the harness, `conf/`
- The allocation redesign — that is Phase 3
- `git push`

---

## Tasks

### T1 — Reclassify the one contaminated manifest run (D31)

`outputs/2026-09-01/09-29-56` is the only `manifest`-class run in existence and it carries a permanently misaligned `num_events` column — generated before F1's fix, so its disruption alignment is recorded data no code change can repair.

`manifest` means **reportable**. This run is not.

**Change the class from `manifest` to `exploratory`**, in `manifest.json` and in the `steps.parquet` and `events.parquet` columns.

**Do not touch any measurement column.** `excess`, `optimum`, `best_cost`, timings and parameters all stay byte-identical. Only the status label changes.

**Leave a written reason in the run directory** — a file named `RECLASSIFIED.md` recording: what changed, when, by which segment, why, and the explicit statement that no measurement data was altered. D31 permits the correction *only* with this trace.

Then show, verbatim, that a measurement column is unchanged before and after — a checksum or a value comparison. The label moved; the evidence did not.

### T2 — F2: the controller must raise on an unknown target

`IncrementalController.propose` silently ignores a target it does not recognise. A hybrid arm left on the default `targets=["rho"]` adapts **nothing** — hybrid parameters are named `aco_rho` — while still logging `controller_kind=incremental` beside moving signal values.

That is the inert-mechanism failure this project has already been bitten by: a component that reports itself active while doing nothing.

**Fix: raise.** `bind()` in `optimizers/spec.py` already raises on the same class of mistake; the controller must match. Consistency here is not cosmetic — two components handling the same error two different ways is how the next person learns the wrong lesson.

**Test both directions:** an unknown target raises, and a known one still works. And add one that would have caught the original bug: **a hybrid arm with `targets=["rho"]` must now fail loudly rather than silently adapting nothing.**

Then answer, from the record rather than assumption: **did any run ever execute with this silent-drop in effect?** The RUNBOOK command and the Round-1 deck both show `targets=[aco_fraction]` was passed explicitly, but "we probably got lucky" is not a finding. Check `.hydra/config.yaml` and `manifest.json` across the runs on disk and report what they actually say.

### T3 — F3: `cross_evaluate.py`, re-derived not renamed

This script backs **the project's key explanatory finding** — that the optimal parameters do not depend on volatility, which is what makes Claim 2 a diagnosis rather than a shrug. It currently raises `TypeError` immediately.

**It is not a keyword rename.** It passes:

```python
CHURN = {'static': 0.0, 'moderate': 0.006, 'high': 0.015}
ScenarioCfg(name='x', churn=churn, timesteps=60)
```

Those values are **fractions of |E|** — the old *proportional* disruption model, from before the switch to absolute Poisson rates. The semantics changed underneath the script, not just the parameter name.

**Do not invent a mapping from the old fractions to new rates.** Use the **registered scenario configurations as they are defined today** — `static`, `moderate`, `high` with their current `events_per_step`. The finding is being re-derived under the current model, and it may come out differently from the original. That would itself be informative and must be reported rather than smoothed over.

**The dependency, which is the important part:** the script globs `multirun/*/*/*/best_fixed.json` for per-scenario tuned vectors. **Those do not exist on this machine.** Tuning is Phase 4 (T1–T4 of the experiment manifest).

So this task is **repair, not execute**:

- Make it correct against the current API and the current scenario definitions
- Make it **fail clearly** when the tuned vectors are absent — a plain message naming what is missing and which Phase 4 step produces it, not a `TypeError` or an empty dict silently producing meaningless output
- Add a test that it imports and that its config construction is valid, without requiring the vectors

Say plainly in your findings that the finding itself remains **un-re-derived until Phase 4**, and that the current README and DOCUMENTATION figures for it are provisional (they already carry markers from segment 1).

### T4 — `load_events()` filtering (Architect's carry-over)

Ruling 4 in segment 3 named `EVENT_SCHEMA` and stopped there. `run_class` is in the events data but **`load_events()` takes no class argument and applies no filter** — and recovery analysis reads events across runs, so it is the same exposure one level up. Architect error.

Give `load_events()` the same treatment `load_steps()` has:

- default returns `manifest` rows only
- a missing `run_class` reads as `exploratory` (D27)
- a mixed load — some directories with the column, some without — succeeds without raising

**And apply D30 while you are here:** single-run tools are not filtered. Check every caller of `load_events()` the way segment 3 checked `load_steps()`'s seven, and report what you find *before* changing them. If a caller operates on one named run, it passes the class through.

Test the migration path against real pre-column data, not a fixture, exactly as segment 3 did.

### T5 — Parametrise the warm-up assertion (your flag)

F4's warm-up is currently asserted for `volatility` alone. `edge_ratio` and `lambda_branch` share the shape and have no equivalent test.

Parametrise it across all three windowed signals. `recency` is **excluded and the exclusion is asserted** — it is a decay rather than a rolling mean, carries no window, and therefore has no warm-up. That distinction is why Claim 3 survives F4, and a test that states it is worth more than a comment that mentions it.

### T6 — Commit

Whole tree. **Do not push.**

```
segment 5: F2, F3 and Phase 0.5 loose ends

Fixes F2 — IncrementalController silently ignored unknown targets, so a
hybrid arm on the default targets=["rho"] adapted nothing while logging
itself active. Now raises, matching bind() in optimizers/spec.py.

Repairs F3 — cross_evaluate.py used the old proportional churn model,
superseded by absolute Poisson rates. Rebuilt against the current
scenario definitions and made to fail clearly when the tuned vectors it
needs are absent. The finding remains un-re-derived until Phase 4
produces those vectors.

Adds run_class filtering to load_events(), closing the asymmetry left by
segment 3, with single-run callers passing the class through per D30.

Reclassifies outputs/2026-09-01/09-29-56 from manifest to exploratory
under D31 — its num_events predates F1's fix and is permanently
misaligned. Measurement data untouched; reason recorded in the run
directory.

Parametrises the F4 warm-up assertion across all three windowed signals,
with recency's exemption asserted rather than assumed.

Closes phase 0.5.

Spec + findings: currentWorkFlow.md
Log: WORKFLOW_LOG.md entry 005
```

---

## Constraints

| | |
|---|---|
| **T0 before implementation** | |
| **T1 touches exactly one run directory** | Every other run under `outputs/` is untouchable. No measurement column changes, anywhere |
| **F3 is repaired, not executed** | It cannot run without Phase 4's tuned vectors. Do not fabricate them, do not stub them with plausible values |
| **Do not invent an old-churn-to-new-rate mapping** | Use today's scenario definitions |
| **Report before changing `load_events()`'s callers** | Same discipline as segment 3 |
| **No existing test deleted, weakened or skipped** | |
| **Do not push** | |

---

## Acceptance check

```bash
# 1a. In scope
git diff --stat -- src/ tests/ scripts/
git status --short outputs/          # only 09-29-56, plus RECLASSIFIED.md
# 1b. Nothing elsewhere
git diff --stat -- conf/ README.md RUNBOOK.md DOCUMENTATION.md

# 2. Suite
./.venv/bin/pytest -q -m "not slow"

# 3. Lint
./.venv/bin/ruff check src/ tests/

# 4. Budget, count reported against 2100
./.venv/bin/pytest -q -k statement_budget -s

# 5. F2 raises
python -c "
from dynaswarm.control.controllers import IncrementalController
# unknown target must raise; known target must still work"

# 6. Reclassification took, measurements did not move
python -c "
import json, pandas as pd
d='outputs/2026-09-01/09-29-56'
print(json.load(open(f'{d}/manifest.json'))['config']['run_class'])
print(pd.read_parquet(f'{d}/steps.parquet').run_class.unique())"

# 7. No manifest runs remain
python -c "
from dynaswarm.analysis.load import load_steps
print(len(load_steps('outputs')))"

# 8. load_events filters and migrates
python -c "
from dynaswarm.analysis.load import load_events
print(load_events('outputs', run_class=None).run_class.value_counts())"

# 9. F3 fails clearly, not with a TypeError
./.venv/bin/python scripts/cross_evaluate.py

# 10. Committed, not pushed
git log --oneline -2
git status --short --branch | head -1
```

**Expected:** in-scope only · all tests pass · lint clean · under 2100 · F2 raises on unknown and works on known · the run reads `exploratory` in manifest and both parquets · **check 7 returns 0 rows — there are now no manifest runs at all, which is correct and expected** · `load_events` migrates without raising · F3 exits with a readable message naming the missing vectors and the Phase 4 step that produces them · commit on top, ahead 1, unpushed.

**Paste verbatim:**

1. **T0's measurement**
2. **Proof a measurement column is unchanged** across T1's reclassification
3. **What the run configs on disk actually say about `control.targets`** (T2's record check)
4. **F3's new failure message**
5. **The `load_events()` caller audit** — every caller, and which are single-run

---

## Definition of done

All ten checks pass, five artefacts pasted, commit exists unpushed, FINDINGS appended.

**This closes Phase 0.5, and with it every known defect.** Phase 1 — the dashboard — is next, and it is a different kind of work again: the first thing built rather than repaired.

---
---


## FINDINGS — Segment 5

**Status:** COMPLETE. Commit `4ab4f06`, unpushed. **Phase 0.5 closed — every known defect is now fixed or repaired.**

---

### 1. T0 — the measurement

```
BEFORE : 1998 / 2100   (margin 102)
AFTER  : 2002 / 2100   (margin 98)
COST   : +4 statements   (scripts/ and tests/ are outside the cap)
VERDICT: FITS
```

**+4 rather than +9** because `load_events()`'s filtering was factored into a shared `_classified()` helper rather than duplicated. That removed six statements of copy from `load_steps()` while adding the new loader — and more importantly, provenance filtering that disagreed between the step table and the event table would be worse than none at all, since the disagreement would only surface once someone joined them.

Breakdown: F2's guard +3, the `_classified` helper +6, `load_steps` simplification −4, `load_events` −1 net. Test-side wherever possible, as in segment 4.

### 2. Proof the measurements did not move across T1's reclassification

Digest over the measurement columns — `excess`, `optimum`, `best_cost`, `wall_ms`, `evaluations_spent`, `path_len` for steps; `old_weight`, `new_weight`, `u`, `v`, `kind` for events — taken immediately before and after:

```
BEFORE  steps  measurement digest: f0d4fb0949de46be664ef76b046fccc2
BEFORE  events measurement digest: d26540d9120b6b93093b2b005e483b98
BEFORE  run_class: manifest | manifest.json: manifest

AFTER   steps  measurement digest: f0d4fb0949de46be664ef76b046fccc2
AFTER   events measurement digest: d26540d9120b6b93093b2b005e483b98
AFTER   run_class: exploratory | manifest.json: exploratory

MEASUREMENTS UNCHANGED: True
```

The relabel was applied at the Arrow level via `set_column`, so every type survives — including the `map<string, double>` `params` and `probe` columns that a pandas round-trip would have destroyed (the lesson from segment 4's fixture). `RECLASSIFIED.md` is in the run directory recording what changed, when, by which segment, why, and this digest pair.

### 3. What the run configs on disk actually say — T2's record check

The question was whether any run ever executed with the silent-drop in effect. **It did not**, and the reason is stronger than "we got lucky":

```
--- outputs/2026-08-30/22-53-05   arms: ['astar', 'aco']                    targets: ['rho']  signal: None
--- outputs/2026-08-30/22-53-36   arms: ['astar', 'aco', 'pso', 'hybrid']   targets: ['rho']  signal: None
--- outputs/2026-08-30/22-54-54   arms: ['astar', 'aco', 'hybrid']          targets: ['rho']  signal: None
--- outputs/2026-09-01/09-29-19   arms: ['astar', 'aco', 'pso', 'hybrid']   targets: ['rho']  signal: None
--- outputs/2026-09-01/09-29-56   arms: ['astar', 'aco', 'pso', 'hybrid']   targets: ['rho']  signal: None
```

Every run used `targets: ['rho']` — the default, the exact configuration that was silently inert. But **not one used a controlled arm.** `astar`, `aco`, `pso` and `hybrid` carry no signal and no controller; only `aco_fixed`/`aco_adaptive`/`hybrid_fixed`/`hybrid_adaptive` do. `_make_controller` returned `None` for every arm in every run, so `IncrementalController.propose` was **never constructed and never called**.

So the record shows something better than luck: the defect could not have contaminated any run on disk, because no run on disk ever built the controller. That is a stronger statement than the RUNBOOK-and-deck argument the spec anticipated, and it comes from the configs rather than from documentation about them.

### 4. F3's new failure message

```
cross_evaluate: cannot run — no tuned parameter vectors for ['static', 'moderate', 'high'].
  Looked in: multirun/*/*/*/best_fixed.json
  Found:     nothing

  These are produced by the tuning steps of the experiment manifest (ARCHITECTURE.md §13.1, T1-T4), which run in Phase 4.
  This script is repaired and ready; the finding it produces cannot be re-derived until those vectors exist.
  Until then the figures quoted for it in README.md and DOCUMENTATION.md are provisional and are marked as such.
```

Exit code 1, no traceback.

**Stated plainly, as the spec requires: the finding itself remains un-re-derived.** The script is correct against today's API and today's registered scenarios — `{static: 0.0, moderate: 0.3, high: 0.8}`, absolute Poisson rates, with **no mapping invented** from the old `{0.0, 0.006, 0.015}` fractions. Whether "the optimal parameters do not depend on volatility" still holds under the current disruption model is **unknown and untested** until Phase 4 produces the vectors. The README and DOCUMENTATION figures for it already carry provisional markers from segment 1.

One thing worth flagging about the original failure: an empty glob fed an empty `VECTORS` dict, so had the `TypeError` not fired first, the script would have cross-evaluated *default* parameters against themselves and printed a confident table of near-identical numbers — which would have looked exactly like the finding it was supposed to test. `require_vectors()` exists to make that impossible.

### 5. The `load_events()` caller audit — reported before changing, per the spec

```
src/dynaswarm/analysis/load.py:61   the definition
src/dynaswarm/viz/replay.py:92      events = load_events(run_dir)          <- SINGLE RUN
tests/test_analysis.py:327          load_events(tmp_path)                   <- SINGLE RUN
```

Three call sites, two of them real. **Both operate on one named run**, so both fall under D30 and pass the class through — `viz/replay.py` now calls `load_events(run_dir, run_class=None)`. Notably `cli.py` does *not* call `load_events` at all, so unlike segment 3 there was only one source caller to correct.

That the audit found no aggregating caller is itself informative: `load_events` had no reader that the filter would have protected, which is presumably why the asymmetry survived segment 3 unnoticed. The filter is prospective — recovery analysis in Phase 4 is what will read events across runs.

### 6. Acceptance

| Check | Result |
|---|---|
| 1a in-scope | 8 files: `scripts/cross_evaluate.py`, 3 × `src/`, 4 × `tests/` |
| 1a `outputs/` | **empty — see Surprise 1**; `outputs/` is gitignored |
| 1b elsewhere | `conf/ README.md RUNBOOK.md DOCUMENTATION.md` — **empty** |
| 2 suite | **313 passed**, 5 deselected |
| 3 lint | `All checks passed!` (`src/`, `tests/`, `scripts/`) |
| 4 budget | `src/ = 2002 / 2100` |
| 5 F2 | unknown raises `KeyError`; known target still adapts |
| 6 reclassification | `exploratory` in `manifest.json`, `steps.parquet`, `events.parquet` |
| 7 no manifest runs remain | **0 rows** — correct and expected |
| 8 `load_events` | default 0 rows; unfiltered 49 603 rows, all `exploratory`, no raise |
| 9 F3 | readable message, exit 1, no `TypeError` |
| 10 commit | `4ab4f06`, `ahead 1`, **not pushed** |

Suite went 302 → 313: +11 tests (3 for F2, 2 for F3, 2 for `load_events`, 3 parametrised warm-up, 1 recency exemption), none deleted, none weakened, none skipped.

### Deviations from spec

**One existing test needed a call-site correction: `test_hybrid.py::test_recency_peaks_on_disruption_and_decays`.** It ran `hybrid_adaptive` under the default `targets=["rho"]` — precisely the configuration F2 makes raise, and precisely what T2 asked me to add a *new* test for. It was relying on the silent drop.

The whole change, with every assertion untouched:

```diff
-        control=ControlCfg(signal="recency"),
+        # A hybrid's parameters are `aco_`/`pso_`-prefixed, so the default
+        # targets=["rho"] names nothing it declares.  That used to be
+        # silently dropped (F2) and now raises, so the target is named.
+        control=ControlCfg(signal="recency", targets=["aco_fraction"]),
```

Same class of change as segment 3's Ruling 2 — the behaviour asserted is unchanged, only the call that reaches it — and the spec anticipates this exact raise. Flagged rather than buried.

### Surprises

1. **`outputs/` is gitignored, so acceptance check 1a could not show what it expected.** The check anticipated `git status --short outputs/` listing `09-29-56` and `RECLASSIFIED.md`; it lists nothing, because `.gitignore:18` excludes `outputs/` entirely. The reclassification is real on disk and verified by checks 6 and 7 — but it is **not in the commit and not in version control**. `RECLASSIFIED.md` is the only record that it happened, and it lives inside an untracked directory. If that trace is meant to be durable, D31's requirement may need somewhere tracked to live; a run directory that git does not see is a thin place to keep the sole evidence of a corrected label.

2. **`PrescheduledController` has the identical silent-drop bug and I did not fix it.** Line-for-line the same pattern — `if name in proposed:` with no guard — so a prescheduled hybrid on default targets would sweep nothing while logging itself active. F2 named `IncrementalController` only, and `PrescheduledController` is unexercised (no `ArmSpec` uses it), so I left it. But the consistency argument that justified fixing F2 applies here verbatim, and it will be wired up in Phase 3 as `ScheduledAllocation` — the open-loop control for feedback itself. Reporting rather than fixing.

3. **The parquet reclassification exposed how narrow "immutable" has to be.** Rewriting one column of a parquet means rewriting the whole file, so "measurement data untouched" is a claim about content that has to be *verified*, not a property the operation guarantees. The digest check is the only thing standing between a relabel and an undetected corruption. Worth keeping if D31 is ever exercised again.

4. **49 603 event rows across five runs**, versus 9 240 step rows. Events outnumber steps five to one because disruptions arrive in 25-edge clusters. Not a problem — but any Phase 4 recovery analysis that loads events across runs is handling a substantially bigger table than the step-based analyses, and the filter now added to `load_events` is doing correspondingly more work.

### Could not do

Nothing. All six tasks completed.

### Questions for the Architect

1. **`PrescheduledController` (Surprise 2)** — fix now as an F2 sibling, or leave it to Phase 3's `ScheduledAllocation` rewrite? It is inert today either way, but a known-broken component sitting in the tree is what F2 just demonstrated the cost of.
2. **The D31 trace lives only in an untracked directory (Surprise 1).** Should the reclassification also be recorded somewhere version-controlled — a line in `decisionLedger.md`, or a `RECLASSIFICATIONS.md` at the repo root — so the correction survives the run directory being moved or lost?
3. **F3's re-derivation is now a Phase 4 dependency with a name.** Should it become an explicit entry in the experiment manifest (§13.1's E7) with the tuning steps listed as its prerequisites, so it cannot be forgotten between here and then?

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->


---
---

# ADDENDUM — Architect rulings, 1 Sept 2026

**Three rulings. One adds a task (T7); Phase 0.5 does not close until it lands.**

---

## R1 — D31's trace needs a tracked home. Amended.

You are right, and the flaw is in D31 as I wrote it.

`outputs/` is gitignored. `RECLASSIFIED.md` therefore lives where version control cannot see it — **the trace is as ephemeral as the thing it describes.** A record that vanishes with the directory is not a record; it is a note to whoever happens to be standing there.

**D31 is amended: the reclassification is recorded in two places, and they do different jobs.**

| Where | Purpose | Durable? |
|---|---|---|
| `RECLASSIFIED.md` in the run directory | The local warning — for anyone who opens that folder and starts reading its parquets | No, and that is acceptable for this purpose |
| **`WORKFLOW_LOG.md`** | **The authoritative trace** — what was reclassified, when, why, and that no measurement column moved | **Yes. Tracked, committed, append-only** |

Keep `RECLASSIFIED.md` where it is. The log entry is what makes the trace survive.

No action for you here beyond noting it — Entry 005 will carry the authoritative record.

## R2 — `PrescheduledController`: fix it. It is F6, and it is worse than F2.

You left it correctly — it was outside the named scope. But your consistency argument is right and there is a sharper reason on top of it.

`PrescheduledController` becomes **`ScheduledAllocation` in Phase 3** (`ARCHITECTURE.md` §7.2), and its role there is specific:

> **the honest control for feedback itself** — if an open-loop schedule matches a signal-driven policy, what helped was *varying*, not *sensing*.

Now consider the bug in that role. A silent-drop `ScheduledAllocation` adapts **nothing**, so it produces results **identical to the frozen arm** — while logging itself as an active scheduled controller. The conclusion drawn would be *"an open-loop schedule does not help either,"* which is a **false null on the one arm whose entire job is to falsify the control story.**

F2 was inert machinery that never ran. This is inert machinery that is *guaranteed* to run, in an experiment specifically designed to distinguish two hypotheses, where the failure mode is indistinguishable from a real result.

**"Unexercised" is the reason to fix it now, not the reason to leave it.** The first time it is exercised will be in an experiment whose answer matters.

Logged as **F6**.

### T7 — Fix F6

Same treatment as F2: `PrescheduledController.propose` raises on a target it does not recognise, matching `IncrementalController` and `bind()` in `optimizers/spec.py`.

Same test shape as F2's: unknown raises, known still works.

**Then check the whole family.** F2 and F6 are the same bug in two of three controllers. `NullController` returns `dict(current)` unchanged and has no target handling at all, so it is presumably exempt by construction — **confirm that rather than assuming it**, and say so. If a fourth place handles targets, name it.

That is the last known defect. Phase 0.5 closes when it does.

## R3 — The test that was relying on the drop

`test_recency_peaks_on_disruption_and_decays` ran `hybrid_adaptive` on `targets=["rho"]` — the inert configuration — and passed. One-line call-site correction, assertions untouched. Correct handling.

Worth recording, because the pattern will recur: **the test was measuring the signal, not the controller.** It asserted that `recency` peaks and decays, which is true whether or not anything acts on the reading. So it was not testing a falsehood — it was testing a narrower thing than its position in the suite implied.

The general lesson for Phase 3, where the allocation governor gets its tests:

> A test that exercises a controlled arm is not thereby testing the controller. If the assertion would hold with the controller removed, it is testing something else — and should say so in its name.

## On your record check

This is the standard the project should hold to, and it deserves saying plainly.

The question was whether F2 ever contaminated a run. The available answer was *"the RUNBOOK and the deck both show `targets=[aco_fraction]` was passed explicitly."* You did not accept it. You read the five run configs and found something better:

> All five used `targets: ['rho']` — **the inert configuration** — but **none used a controlled arm.** `astar`, `aco`, `pso` and `hybrid` carry no controller, so `IncrementalController.propose` was never constructed and never called.

So the answer is not "we got lucky with the flag." It is **"the code path could not execute,"** established from the configs rather than from documentation about the configs. Those are different strengths of claim, and the second one survives a viva.

---

## Revised close-out

| | |
|---|---|
| **T7** | Fix F6 · confirm `NullController`'s exemption · name any fourth site |
| **T8** | Re-run the suite, lint, and the statement budget. Report the count |
| **T9** | **Amend the existing commit** to include T7 — `git commit --amend`. This is the one sanctioned amendment: `e98f5c7` is unpushed, and Phase 0.5 should close as a single coherent commit rather than a fix chasing its own tail |

**Amended commit message** — add before "Closes phase 0.5.":

```
Fixes F6 — PrescheduledController carried the identical silent-drop bug.
Left unexercised it would have surfaced in Phase 3 as ScheduledAllocation,
the open-loop control for feedback itself, where adapting nothing produces
results identical to the frozen arm and a false null on the one arm whose
job is to falsify the control story.
```

**Additional acceptance:**

- **11:** `PrescheduledController` raises on an unknown target and works on a known one
- **12:** the controller family audited — every controller that handles targets either raises or is documented as exempt by construction, with the reason

---

Append a **second** FINDINGS block below. The first stays as written.

<!-- vClaude: append your SECOND findings block below this line -->

---

# FINDINGS — Segment 5, second block (addendum: T7–T9)

## 1. T0 — re-measured, because scope changed mid-segment (D29)

```
before T7:  src/ = 2002 / 2100   margin 98
projected:  +3  (Assign + If + Raise — the guard, mirroring F2 exactly)
after T7:   src/ = 2005 / 2100   margin 95
```

The projection was exact. Counted with the suite's own `_statement_count`
(`tests/test_hygiene.py:113`), not an approximation of it — an independent
counter that disagreed with the enforcer would make the margin fiction.

## 2. T7 — F6 fixed

Guard added at the top of `PrescheduledController.propose`, textually
parallel to F2's:

```python
        unknown = set(self.targets) - set(current)
        if unknown:
            raise KeyError(
                f"controller target(s) {sorted(unknown)} are not parameters of this "
                f"optimizer; it declares {sorted(current)}"
            )
```

### The new test fails against the unfixed code

Captured before restoring the fix, so the guard is demonstrated to bite
rather than asserted to:

```
>       with pytest.raises(KeyError, match=r"\['aco_fraction'\]"):
E       Failed: DID NOT RAISE KeyError
tests/test_control.py:505: Failed
```

### What the defect actually produced — the false null, made concrete

Reproducing the pre-fix `propose` verbatim and running a 1.0 → 2.0 sweep
against a hybrid's parameter vector on the default `targets=("rho",)`:

```
PRE-FIX  targets=('rho',)  optimizer declares ['aco_alpha', 'aco_fraction', 'aco_rho']
  every timestep identical to the frozen vector: True
  t=0: {'aco_fraction': 0.5, 'aco_rho': 0.08, 'aco_alpha': 1.0}
  t=9: {'aco_fraction': 0.5, 'aco_rho': 0.08, 'aco_alpha': 1.0}   <- a 1.0->2.0 sweep that moved nothing
POST-FIX raises: "controller target(s) ['rho'] are not parameters of this
  optimizer; it declares ['aco_alpha', 'aco_fraction', 'aco_rho']"
```

`True` on that middle line is the whole finding. The schedule ran, the
multiplier reached 2.0, and the returned vector was byte-identical to the
input at every timestep — not approximately the frozen arm, *the frozen
arm*. A Phase 3 `ScheduledAllocation` in this state could not have been
told from its own control by any measurement downstream of it.

**First attempt at this demonstration was wrong and is worth recording.**
I initially passed `aco_fraction` in `current` while targeting it, so the
membership test succeeded and the sweep worked correctly — I had built a
demo of the code *not* failing. The bug needs the target to be **absent**
from `current`. A demonstration that does not reproduce the triggering
configuration is evidence of nothing, and it looked convincing until I
read the numbers.

## 3. T7 — the controller family, audited rather than assumed

Five sites in `src/` handle a target name. Enumerated by grep, not from
memory:

| Site | Handling | Verdict |
|---|---|---|
| `optimizers/spec.py:91` `bind()` | `unknown = set(values) - set(table)` → raises | **The reference.** Both fixes were written to match it |
| `control/controllers.py:139` `IncrementalController.propose` | raises | Fixed — F2 |
| `control/controllers.py:195` `PrescheduledController.propose` | was a silent drop | Fixed — F6 |
| `control/controllers.py:98` `NullController.propose` | `return dict(current)` | **Exempt by construction** — see below |
| `harness/arm.py:228` `_make_controller` | `return make_controller(spec.controller)` | **Not a target-drop, but see §4** |

### `NullController`'s exemption, confirmed not assumed

It has **no `targets` field at all** — not an empty one, not an ignored
one. There is no target for it to drop. That is a stronger exemption than
"it happens to handle them correctly," and it is now asserted:

```python
    assert not hasattr(NullController(), "targets")
```

Asserting the *absence* is deliberate. The exemption is a property of the
class's shape, so the test fails the moment someone adds target handling
without adding a guard — which is exactly how F2 and F6 got in. A test
that only checked `propose` returned its input unchanged would still pass
in that world.

## 4. The fourth site — named, not fixed

`_make_controller` (`harness/arm.py:208`) forwards `control.targets` to
`IncrementalController` explicitly, but the prescheduled branch falls
through to:

```python
    return make_controller(spec.controller)
```

— **no arguments at all.** A prescheduled controller built through the
harness therefore takes every dataclass default: `targets=("rho",)`,
`start=1.0`, `end=1.0`, `horizon=60`. Two consequences, and they compound:

1. `control.targets` is silently discarded, so configuring the schedule's
   targets has no effect.
2. `start == end == 1.0` makes the multiplier identically 1.0, so it
   varies nothing **even on a target it does have** — the false null
   again, arrived at by a different route, and this one survives the F6
   guard untouched because `("rho",)` *is* declared by an ACO arm.

This is not F6 and I have not touched it. Fixing it means deciding what
`start`, `end` and `horizon` a schedule should carry, which is a Phase 3
science decision (`ARCHITECTURE.md` §7.2), not a defect repair — and the
protocol says name it rather than improvise it. Flagging it now because
Phase 3 will build `ScheduledAllocation` on this constructor, and the
guard I just added does not protect it.

**No registered arm requests `prescheduled` today** — `grep -rn
prescheduled src/ tests/ scripts/ conf/` returns only the class, its
`CONTROLLERS` entry, and its tests. So neither F6 nor this can have
touched a run on disk, by the same could-not-execute argument as T2's.

## 5. T8 — suite, lint, budget

```
pytest                 321 passed in 62.03s   (exit 0)
pytest -m "not slow"   316 collected
ruff check src/ tests/ scripts/   All checks passed!
src/ = 2005 / 2100   margin 95
```

**A correction to my previous report.** I reported "313 tests passing" at
the close of the first findings block. That was the `-m "not slow"`
figure, given without the marker qualification. The full suite stood at
**318**; it is **321** now, +3 from T7. Stating it plainly because the
workflow log records these counts and an unqualified number that quietly
excludes five tests is the kind of thing that goes unnoticed for a phase.

## 6. Acceptance — the addendum's two checks

| # | Check | Result |
|---|---|---|
| 11 | `PrescheduledController` raises on an unknown target, works on a known one | **Pass** — `test_prescheduled_raises_on_a_target_the_optimizer_does_not_declare` and `test_prescheduled_still_sweeps_a_declared_target`; the two pre-existing prescheduled tests still pass unmodified |
| 12 | Family audited; every target-handling site raises or is documented exempt with a reason | **Pass** — table in §3, `NullController`'s exemption asserted in §3, fourth site named in §4 |

## Deviations from spec

**One, and it is a non-change.** The addendum says "same treatment as F2."
I mirrored F2 exactly, which means I left `current.get(name, 0.0)` on
line 196 and `if name in proposed:` on line 203 in place, both of which
the new guard makes unreachable. The `.get` fallback is now not merely
redundant but misleading — it encodes `0.0` as an initial value, which
would make the multiplier meaningless if it could ever be reached.

I left them because "same treatment as F2" is an instruction to mirror,
and because two fixes for one bug should read identically — that was R2's
own argument about `bind()`. But a reader meeting the dead fallback will
reasonably wonder which of the two is the real contract. Say the word and
both come out, in either class or both; it is zero net statements.

## Surprises

**The fourth site is worse than the bug I was sent to fix.** F6 needed a
misconfigured target to bite. `_make_controller`'s `start == end == 1.0`
needs nothing — it is the default, it is what Phase 3 gets unless someone
overrides it, and a schedule that never varies is not detectable as an
error anywhere in the pipeline. I went looking for a fourth *drop* site
and found a fourth route to the same false null.

**`ruff format --check` disagrees with 23 of 52 files** — including
`NullController.propose`, which I did not write. The config sets
`line-length = 100`; the codebase is hand-wrapped at 88. My additions
match the surrounding style and F2's fix. `ruff check` (the acceptance
gate) passes clean. Not touching it: running `ruff format` would rewrite
23 files across every phase's work, which is well outside any segment's
scope. Reporting it because "lint clean" and "formatted" are not the same
claim, and I have only ever verified the first.

## Could not do

Nothing was blocked.

## Questions for the Architect

1. **The dead fallback** (deviations, above) — mirror F2 and leave it, or
   clean both classes?
2. **The `_make_controller` defect** (§4) — is this F7 and a Phase 3
   opening task, or does it belong to whoever builds `ScheduledAllocation`
   as part of building it? It is currently unreachable, but so was F6.
3. **`ruff format`** — is the 88-column hand-wrapping deliberate against
   the 100 in `pyproject.toml`, or is one of the two wrong? If the
   formatter is meant to be authoritative, the reformat wants its own
   segment rather than riding along with a science change.
