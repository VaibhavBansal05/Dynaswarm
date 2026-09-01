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

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->
