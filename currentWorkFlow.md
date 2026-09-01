# SEGMENT 3 — Run Provenance (`run_class`) and a Clean Baseline

**Phase 0 · Ground truth · Segment 3 of 3**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` §12 and §12.1, and `decisionLedger.md` D27 before starting. `WORKFLOW_LOG.md` Entries 001 and 002 record the two segments behind this one.
> Append your findings to the **bottom** of this file using the §6 template. Do not modify the spec text above it.

---

## Goal

Make results files say what they are.

Right now a `steps.parquet` from a real 100-trial experiment and one from a ten-second scratch run are indistinguishable. Three exploratory runs already sit in `outputs/2026-08-30/`. When the analysis layer later loads "all the results" to build a figure, those scratch runs get silently mixed with real ones and produce a confident wrong answer with no error message.

**That is the exact failure that killed the predecessor codebase** — instrumentation that looked fine and was not.

This is the first segment that touches code.

---

## ⚠️ T0 — MEASURE BEFORE YOU BUILD

**Do this first. Do not write any implementation until you have reported the result.**

The science surface sits at **1984 / 2000 statements — sixteen of headroom.** This segment adds provenance machinery to `config.py`, `io/schema.py`, `io/writer.py`, `harness/trial.py` and `analysis/load.py`.

**Sketch the minimal implementation for T1–T3, count the executable statements it would add to `src/`, and report the number.**

- **If it fits within the headroom** — say so, and continue to T1.
- **If it does not fit — STOP.** Report the measured cost and your sketch. Do not delete anything to make room, do not raise the cap yourself, do not compress the design past the point of clarity to squeeze under. The Architect will set the new cap **from your measured number**, per D25, and a follow-up segment will implement it.

Tests do not count against this cap — `test_statement_budget` measures `src/` only. Do not economise on test coverage to save statements.

---

## Scope

**In scope**
- `src/dynaswarm/config.py`
- `src/dynaswarm/io/schema.py`
- `src/dynaswarm/io/writer.py`
- `src/dynaswarm/harness/trial.py`
- `src/dynaswarm/analysis/load.py`
- `tests/` — new tests
- `README.md` — one small carry-over (T5)
- Two runs written into `outputs/` (T6)
- One local commit (T7)

**Out of scope**
- Defects F1, F2, F3 — **still not yours to fix**, however close you pass to them
- `conf/`, `scripts/`, the optimizers, the control layer
- Existing files under `outputs/` — do not modify, delete or regenerate the three runs from 30 Aug
- `git push`

---

## Tasks

### T1 — The `run_class` field

Add `run_class` to `Config`, defaulting to **`"exploratory"`**.

Three permitted values, and only three:

| Value | Meaning | Reportable |
|---|---|---|
| `manifest` | produced by a named entry in the experiment manifest | **yes** |
| `exploratory` | ad-hoc — a smoke run, a dashboard session, a sanity check | **never** |
| `inversion` | produced by a deliberately-broken code path | **never**, and never mixed |

An unrecognised value must **raise at compose time**, not be silently accepted. The experiment manifest does not exist yet (Phase 4), so `manifest` is set explicitly on the command line for now; `inversion` has no way to be set at all yet, which is correct — nothing can produce it until the inversion config group exists.

### T2 — Record it

`run_class` must appear in **both** places:

- **`manifest.json`** — it is part of the resolved config, so confirm it lands there rather than assuming it does
- **`steps.parquet`** — as a column on every row, via `StepRow`

Both, not either. The manifest describes the run; the column survives when rows from several runs are concatenated, which is the case the filtering exists for.

### T3 — Load-time filtering and the migration rule

**Default behaviour:** `load_steps()` returns **`manifest` rows only**. Any other class must be requested explicitly by name.

**The migration rule (D27, `ARCHITECTURE.md` §12.1) — implement exactly this:**

> **A missing `run_class` is read as `exploratory`.**

Every parquet currently on disk predates the column. `load_steps()` concatenates across directories, so one old file must not poison a mixed load. It must **fill the column when absent, never raise**, and handle a load where some directories have it and some do not.

No migration script. No schema version. No rewriting of existing files.

### T4 — Tests

At minimum:

| Test | What it protects |
|---|---|
| default config produces `run_class == "exploratory"` | the safe default holds |
| **the default configuration can never produce `inversion`** | required by `ARCHITECTURE.md` §12 |
| an unrecognised `run_class` raises | no silent acceptance |
| `run_class` appears in `manifest.json` **and** as a `steps.parquet` column | recorded in both places |
| a parquet with no `run_class` column loads, and its rows read as `exploratory` | **the migration rule** |
| a mixed load — one directory with the column, one without — succeeds and classifies both correctly | the concatenation case |
| `load_steps()` with no arguments returns only `manifest` rows | the default filter |

Name them so the intent is readable from the test name alone.

### T5 — Carry-over from segment 2

The provisional banner in `README.md` is a blockquote containing an `h2`, so it appears in the document outline as a section. **A warning is not a section.** Change the heading line to bold text; keep the blockquote, the wording and the emoji exactly as they are. Architect's markup, Architect's correction.

### T6 — Two baseline runs, proving both paths

Generate **two** runs on the research tier. Together they demonstrate the whole mechanism end to end.

```bash
# A — default: must come out as exploratory
./.venv/bin/python -m dynaswarm.cli \
  graph=medium200 scenario=high \
  'experiment.arms=[astar,aco,pso,hybrid]' \
  experiment.n_trials=12 report=true

# B — explicitly a manifest run
./.venv/bin/python -m dynaswarm.cli \
  graph=medium200 scenario=high \
  'experiment.arms=[astar,aco,pso,hybrid]' \
  experiment.n_trials=12 run_class=manifest report=true
```

Then demonstrate the filtering across **everything in `outputs/`** — the two new runs plus the three from 30 Aug that have no column at all:

```python
from dynaswarm.analysis.load import load_steps
all_rows = load_steps("outputs")                    # default → manifest only
print(all_rows.run_class.unique())                  # expect: ['manifest']
every = load_steps("outputs", run_class=None)       # or whatever the API you build is
print(every.run_class.value_counts())               # expect manifest + exploratory, no raise
```

**Sanity check while you are there:** A\*'s `excess` must be exactly `0.0` in every row of both runs. It is exact by construction, so any drift means the harness and the oracle disagree about what a path costs — and every other number is then measuring that disagreement.

### T7 — Commit

One local commit, whole tree (Entry 002, Q1). **Do not push.**

```
segment 3: run provenance and clean baseline (phase 0)

Adds run_class to the config, the manifest and the steps schema, with
three permitted values and validation. load_steps() now returns manifest
rows only by default; a missing run_class reads as exploratory, so runs
predating the column load without migration. Two baseline runs on
medium200 demonstrate both paths. Banner heading demoted from h2.

Closes phase 0.

Spec + findings: currentWorkFlow.md
Log: WORKFLOW_LOG.md entries 001-003
```

---

## Constraints

| | |
|---|---|
| **T0 first, always** | No implementation before the statement cost is measured and reported |
| **Never delete code to fit the cap** | Stop and report instead |
| **Never raise the cap yourself** | The Architect sets it, from your measured number |
| **Do not touch F1, F2 or F3** | T3 puts you inside `analysis/load.py` and T2 inside `harness/trial.py` — F1 lives near both. Leave it |
| **Do not modify anything already in `outputs/`** | The three runs from 30 Aug are evidence of the pre-`run_class` state |
| **No existing test deleted, weakened or skipped** | If one fails and you believe the test is wrong, report it and stop |
| **Do not push** | |

---

## Acceptance check

Using the two-scoped-diff form adopted in Entry 002 — not "exactly N files".

```bash
# 1a. The segment's own changes
git diff --stat -- src/ tests/ README.md

# 1b. Nothing outside scope on the science surface
git diff --stat -- conf/ scripts/

# 2. Full suite, including the new tests
./.venv/bin/pytest -q -m "not slow"

# 3. Lint
./.venv/bin/ruff check src/ tests/

# 4. Statement budget — report the number, not just pass/fail
./.venv/bin/pytest -q -k statement_budget -s

# 5. run_class recorded in both places
python -c "import json;print(json.load(open('<run B>/manifest.json'))['config']['run_class'])"
python -c "import pandas as pd;print(pd.read_parquet('<run B>/steps.parquet').run_class.unique())"

# 6. The migration rule, against a real pre-column run
python -c "
from dynaswarm.analysis.load import load_steps
print(load_steps('outputs').run_class.unique())"

# 7. A* is exact
python -c "
from dynaswarm.analysis.load import load_steps
s = load_steps('<run B>')
print((s[s.arm=='astar'].excess == 0.0).all())"

# 8. Committed, not pushed
git log --oneline -2
git status --short --branch | head -1
```

**Expected**

1a. Only the six in-scope source files, the new test file, and `README.md`
1b. Empty
2. All previous tests plus the new ones, passing
3. No findings
4. Passing, **with the current statement count stated**
5. `manifest` in both
6. `['manifest']` — the exploratory runs are filtered out by default
7. `True`
8. The segment 3 commit on top, branch `ahead 1`, not pushed

Then paste verbatim:

- **The T0 measurement** — your sketch's statement cost, and the count before and after
- The `run_class` validation code
- The migration branch in `load_steps()`
- The `value_counts()` across all five runs with filtering disabled

---

## Definition of done

T0 reported. All eight checks produce the expected output. The four verbatim blocks pasted. Commit exists, unpushed. FINDINGS appended below.

**This closes Phase 0.** Stop and wait for the Architect's verification — Phase 0.5 is the defect triage, and it is a different kind of work.

---
---


## FINDINGS — Segment 3

**Status:** BLOCKED — T0–T3 and T5 complete; T4, T6, T7 blocked on a scope conflict the spec did not anticipate. **Nothing committed. Nothing pushed. No out-of-scope file touched.**

---

### T0 — the measurement, reported before any implementation

Measured by applying the sketch to a **copy** of `src/` in a scratch directory and counting with `test_hygiene`'s own `_statement_count` method. The repository was not written to during T0.

```
BEFORE : 1984 / 2000   (headroom 16)
AFTER  : 1997 / 2000   (headroom 3)
COST   : +13 statements
VERDICT: FITS — margin 3
```

Breakdown of the +13: `config.py` +6 (`RUN_CLASSES` constant, the `run_class` field, `__post_init__` with its guard and raise); `harness/trial.py` +1 (the `StepRow` field — the keyword in the existing `StepRow(...)` call costs nothing); `analysis/load.py` +6 (`UNCLASSIFIED` constant, and the filter plus migration branch); `io/schema.py` **+0** — a new `pa.field(...)` inside the existing list literal adds no statement.

**The real count after implementation is exactly 1997**, matching the prediction.

> **It fits, so I continued as T0 directs — but margin 3 is not a margin.** Phase 0.5 instruments `GraphTimeline` to record the maximum index each caller touches (I2), and adds I1 and I3. That cannot land in 3 statements. Per D25 the cap rises from a measured number, and this segment's number is now on the record.

**Design assumption verified rather than assumed.** `__post_init__` does fire through `OmegaConf.to_object()`, which is the call `cli.py` makes — checked empirically. One nuance worth stating precisely: raw `OmegaConf.merge` (Hydra's compose step proper) *accepts* a bad value; the raise happens at the `to_object` boundary. That is still before any trial executes, so the guarantee the spec wanted holds, but "raises at compose time" is more exactly "raises when the composed config becomes a `Config`, before any work begins."

---

### The blocker

**T3's manifest-only default changes behaviour for every existing caller of `load_steps()`, and two of them are in files this segment may not touch.**

`grep -rn "load_steps(" tests src` finds seven call sites. Two are in `src/`:

| Caller | In scope? | Effect of the change |
|---|---|---|
| `src/dynaswarm/cli.py:91` (`_write_report`) | **no** | Gets **0 rows** for any `exploratory` run — i.e. the default. Emits **blank figures and empty CSVs and raises nothing** |
| `src/dynaswarm/viz/replay.py:89` | **no** | Raises `ValueError: no rows for arm=…` on any exploratory run — which is every run that exists today |

Measured on the real pre-column run `outputs/2026-08-30/22-53-36`:

```
load_steps(run)                 ->     0 rows   <- what cli.py _write_report gets
load_steps(run, run_class=None) ->  2880 rows   class=['exploratory']
excess_over_time(empty)  : no exception, figure is blank
per_trial_excess(empty)  : 0 rows
```

**This collides with T6 directly.** T6 run A is `report=true` on a default (therefore `exploratory`) run. As specified, it would write a run directory full of blank figures and an empty `per_trial.csv`, silently. That is precisely the failure mode named in this segment's own Goal — *"instrumentation that looked fine and was not"* — so I will not produce it and call the segment done.

The fix is one line in each file (`run_class=None`; a run reporting on itself, and a viewer replaying one directory, should see their own rows whatever the class). **Both files are outside the declared scope, and `AGENT_PROTOCOL.md` §5 says: "Do not touch files outside the segment's declared scope. If you believe you must — stop and report it instead of doing it."** So I stopped.

### The second, smaller conflict

Five existing tests now fail, all for the same reason — they write default-config runs and call `load_steps(tmp_path)`, which now filters them out:

```
FAILED tests/test_analysis.py::test_replay_reads_what_it_needs_from_results
FAILED tests/test_harness.py::test_parquet_round_trip_preserves_results
FAILED tests/test_harness.py::test_map_columns_survive_the_round_trip
FAILED tests/test_harness.py::test_per_trial_excess_reduces_to_one_row_per_arm_trial
FAILED tests/test_harness.py::test_conditions_from_one_sweep_are_not_merged
```

**None of these tests is wrong**, so the "report it and stop" trigger for a wrong test does not apply. They test round-tripping, map columns, per-trial reduction, condition separation and replay columns — none is about `run_class`. Each needs one mechanical edit: `load_steps(tmp_path)` → `load_steps(tmp_path, run_class=None)`, restoring exactly the pre-change semantics and preserving every assertion at full strength.

I did not make that edit either, for two reasons. The scope line reads "`tests/` — **new tests**", not existing ones. And if the Architect resolves the blocker differently — for instance by making the default `None` with reporting code opting *in* to `manifest` — then these five edits would be wrong, and I would have churned five tests to no purpose.

### What I propose (not implemented — awaiting a ruling)

**Option A — keep the manifest-only default, widen the scope by three files.** Add `cli.py` and `viz/replay.py` to scope for a one-line change each, plus the five test updates. Preserves T3 exactly as specified and as `ARCHITECTURE.md` §12 states it. My recommendation, and it costs **0 additional statements** (`run_class=None` is a keyword in an existing call).

**Option B — invert the default.** `load_steps()` returns everything; reporting code asks for `manifest` explicitly. No caller breaks and no test changes. But it contradicts `ARCHITECTURE.md` §12 — *"`load_steps()` returns `manifest` rows only unless another class is requested explicitly"* — and it makes the unsafe behaviour the default, which is the opposite of D27's reasoning. **I do not recommend it.**

---

### Completed and verified

**T1 — the `run_class` field.** Added to `Config` defaulting to `"exploratory"`, with `RUN_CLASSES = ("manifest", "exploratory", "inversion")` and `__post_init__` validation.

```python
RUN_CLASSES = ("manifest", "exploratory", "inversion")

    def __post_init__(self) -> None:
        """Reject an unrecognised run class before any work begins."""
        if self.run_class not in RUN_CLASSES:
            raise ValueError(f"unknown run_class {self.run_class!r}; permitted: {RUN_CLASSES}")
```

**T2 — recorded in both places.** `pa.field("run_class", pa.string())` added to `STEP_SCHEMA` directly after `run_id`; `run_class: str` added to `StepRow` and populated from `cfg.run_class`. `write_manifest` already serialises the whole resolved config, so `manifest.json` carries it with no code change — to be *confirmed* by a test rather than assumed, per T2, which is part of blocked T4.

**T3 — filtering and the migration rule.** The migration branch:

```python
    frame = _load(directory, "steps.parquet")
    # Two distinct gaps to close, and a mixed load produces both at once:
    # a tree where *no* run has the column, and a concatenation where
    # only some do — pandas fills the latter with NaN.  Neither may raise.
    if "run_class" not in frame.columns:
        frame["run_class"] = None
    frame["run_class"] = frame["run_class"].fillna(UNCLASSIFIED)
    if run_class is not None:
        frame = frame[frame["run_class"] == run_class]
    return frame
```

**Verified against real pre-column data**, not a fixture: all 2880 rows of `outputs/2026-08-30/22-53-36` load without raising and classify as `exploratory`.

**T5 — banner demoted.** `## ⚠️ …` → `**⚠️ …**`. Blockquote, wording and emoji unchanged; the warning no longer appears in the document outline as a section.

### Not done

- **T4** — tests. Blocked: the five existing-test updates depend on the ruling above, and writing new tests against an API that may change would waste them.
- **T6** — the two baseline runs. Blocked: run A as specified emits blank figures.
- **T7** — the commit. Blocked: I will not commit a tree with five failing tests.

**Files changed so far:** `src/dynaswarm/config.py`, `src/dynaswarm/io/schema.py`, `src/dynaswarm/harness/trial.py`, `src/dynaswarm/analysis/load.py`, `README.md`. All in scope. `git diff --stat -- conf/ scripts/` is empty. Nothing under `outputs/` touched.

### Questions for the Architect

1. **Option A or B?** A is my recommendation: three extra files, one line each, zero statement cost, and `ARCHITECTURE.md` §12 preserved as written.
2. **Do the five existing-test edits count as "new tests" scope**, or do they need naming explicitly in the revised spec?
3. **The cap.** This segment lands at 1997/2000. Phase 0.5's I1–I3 cannot fit in 3 statements. D25 says the number comes from a measured design sketch — should the Phase 0.5 spec open with a T0 like this one, so the cap is set from that measurement rather than guessed?
4. **`run_class` in `EVENT_SCHEMA`?** The spec names `steps.parquet` only. `events.parquet` has the same concatenation exposure, but I did not add it — out of what was asked.

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->


---
---

# ADDENDUM — Architect rulings, 31 Aug 2026

**Segment 3 is unblocked. Scope is widened as set out below. Resume from T4.**

Your stop was correct, and the contradiction you found was mine: the spec set a manifest-only default and then asked you to produce a `report=true` run that is exploratory by definition. Blank figures with no exception is exactly the failure this segment exists to prevent, and you were right to refuse to produce it and call it done.

---

## Ruling 1 — Option A, and the principle behind it

Option A. Option B is correctly rejected: inverting the default would make the unsafe behaviour the default, which inverts D27's whole reasoning.

But this is not two mechanical edits. It is a design principle that was missing, and it needs stating because it governs Phase 1 as well:

> **`load_steps()`'s manifest-only default exists to protect aggregation *across* runs.**
> **A tool that operates on one named run is not aggregating, and must load that run's rows whatever their class.**

The report generator reports on the run it just produced. The replay viewer replays one specific run. Neither is building evidence from a pool of runs, so neither should be filtered — and both must pass the class through explicitly rather than relying on a default written for a different purpose.

This also settles the dashboard in Phase 1 before it is built: **the dashboard loads one named run and does not filter.** Its runs are `exploratory` by design, and it would otherwise show a blank screen for every run it ever created.

**Scope is widened by two source files:**

- `src/dynaswarm/cli.py` — `_write_report`
- `src/dynaswarm/viz/replay.py`

Make the smallest change that implements the principle. Do not restructure either file, and do not touch anything else in them.

## Ruling 2 — the five existing tests are in scope, explicitly

Named, so there is no ambiguity:

```
test_analysis.py::test_replay_reads_what_it_needs_from_results
test_harness.py::test_parquet_round_trip_preserves_results
test_harness.py::test_map_columns_survive_the_round_trip
test_harness.py::test_per_trial_excess_reduces_to_one_row_per_arm_trial
test_harness.py::test_conditions_from_one_sweep_are_not_merged
```

These are permitted **only** because the default changed underneath them — the behaviour they assert is unchanged, only the call that reaches it.

**Hard constraint: every assertion must survive byte-identical.** The only permitted change is the argument passed to `load_steps()`. If any of the five needs an assertion altered to pass, **stop and report** — that would mean the default filter has changed a behaviour rather than a call signature, and that is a different conversation.

## Ruling 3 — the cap rises to 2100, and T0 becomes standard

**D28 — the science-surface statement cap is 2100**, up from 2000.

Your measurement forced this, and it is set from your number rather than a guess: the surface lands at **1997/2000** with `run_class`, and Phase 0.5's I1–I3 including the `GraphTimeline` instrumentation cannot fit in three. Margin 3 is not a margin, as you said.

The justification is real rather than convenient. The original 2000 predates two things the project has since committed to permanently — **run provenance** (D27) and **correctness invariants** (I1–I3), both science-surface machinery, neither optional. The thesis also moved, so the surface now carries allocation as live code *and* parameter adaptation as reproducible evidence. That is a genuine scope increase, not accretion.

It is still a brake. 2100 is not a budget to spend, and Phase 1's retirement of `viz/replay.py` returns roughly 158 statements, so Phase 3's allocation package should not need another raise. If it does, it gets one on the same terms: measured, justified, recorded.

**Update `test_statement_budget`'s constant as part of this segment.** That is the one existing test you may change, and only this constant.

**D29 — every segment that touches `src/` opens with a T0 measurement.** Your fourth question answers itself: yes, Phase 0.5's spec will open with one, and so will every code segment after it. Sketch, count, report, and stop if it breaches. This is now standard and it came from you — it has already earned its place twice in one segment, catching both that the fit was real and that the margin was not.

## Ruling 4 — add `run_class` to `EVENT_SCHEMA` too

Yes. You are right that `events.parquet` carries the same concatenation exposure, and the asymmetry is a trap: someone will eventually load events across runs and get a silently wrong recovery analysis, which is the exact class of bug this segment exists to close.

Two statements to prevent it, against a cap that now has room. Consistency here is cheap; the bug it would prevent is not.

---

## Revised remaining tasks

| | |
|---|---|
| **T3b** | Apply Ruling 1 to `cli.py` and `viz/replay.py` |
| **T3c** | Add `run_class` to `EVENT_SCHEMA` (Ruling 4) |
| **T3d** | Raise `test_statement_budget`'s constant to **2100** (Ruling 3) |
| **T4** | The new tests as originally specified, **plus** the five existing-test updates (Ruling 2) |
| **T4b** | One further test: **a single-run load is not filtered** — the report path returns rows for an exploratory run. This is Ruling 1's principle, and without a test it will be undone by someone later |
| **T6** | The two baseline runs, unchanged — run A will now produce real figures |
| **T7** | The commit, with the message amended below |

**Revised commit message:**

```
segment 3: run provenance and clean baseline (phase 0)

Adds run_class to the config, the manifest, and both the step and event
schemas, with three permitted values and validation. load_steps() returns
manifest rows only by default, protecting aggregation across runs; tools
operating on a single named run pass the class through and are not
filtered. A missing run_class reads as exploratory, so runs predating the
column load without migration. Raises the science statement cap to 2100
(D28), measured. Two baseline runs on medium200 demonstrate both paths.

Closes phase 0.

Spec + findings: currentWorkFlow.md
Log: WORKFLOW_LOG.md entries 001-003
```

## Revised acceptance

The original eight, with these changes:

- **1a** now covers `src/`, `tests/`, `README.md` — including `cli.py` and `viz/replay.py`
- **4** must report the count against the **new 2100 cap**
- **New 9:** the five named tests pass with every assertion unchanged — paste the diff for each, showing only the call site changed
- **New 10:** a report generated from run A (exploratory) contains **non-empty** figures and a non-empty `per_trial.csv`. This is the check that would have caught the original spec's contradiction, so it is now permanent

---

## Note for the record

Your fourth question in the previous findings and your third here are the same question arriving from two directions, and both were right. D29 exists because of them.

Append a **second** FINDINGS block below for the resumed work — do not edit the first. The BLOCKED report stays as written; it is the more useful half of this segment's history.

<!-- vClaude: append your SECOND findings block below this line -->

## FINDINGS — Segment 3 (resumed, post-addendum)

**Status:** COMPLETE

The first FINDINGS block above stands as written. This one covers only the work done after the addendum unblocked it.

### T0 — re-measured, because the scope changed

D29 says every `src`-touching segment opens with a measurement, and the addendum widened scope by two source files plus `EVENT_SCHEMA`. The original T0 measured a sketch that no longer matches what was asked, so the number was re-established rather than carried forward.

| | statements |
|---|---|
| Before this segment | 1984 |
| After T1–T3 (first half) | 1997 |
| **After the addendum work** | **1998** |
| Cap (D28) | 2100 |
| **Margin** | **102** |

The addendum cost **+1 statement**: `EventRow.run_class`. Everything else was free — `pa.field(...)` inside an existing list literal, `run_class=None` as a keyword in an existing call, and a changed constant are all zero-statement edits.

### Files changed

**Source**
- `src/dynaswarm/config.py` — `RUN_CLASSES`, the `run_class` field defaulting to `exploratory`, and `__post_init__` validation
- `src/dynaswarm/io/schema.py` — `run_class` in `STEP_SCHEMA` **and** `EVENT_SCHEMA` (T3c)
- `src/dynaswarm/harness/trial.py` — `run_class` on `StepRow` and `EventRow`, populated from `cfg.run_class`
- `src/dynaswarm/analysis/load.py` — `UNCLASSIFIED`, the `run_class` parameter, the default filter and the migration branch
- `src/dynaswarm/cli.py` — **T3b**, `_write_report` passes `run_class=None`
- `src/dynaswarm/viz/replay.py` — **T3b**, the viewer passes `run_class=None`

**Tests**
- `tests/test_provenance.py` — **new**, 21 tests
- `tests/test_hygiene.py` — **T3d**, `MAX_SRC_STATEMENTS` 2000 → 2100, that constant and nothing else
- `tests/test_harness.py`, `tests/test_analysis.py` — the five call sites named in Ruling 2

**Docs**
- `README.md` — T5, banner heading demoted from `h2` to bold

### Test suite

Command: `./.venv/bin/pytest -m "not slow"`
```
292 passed, 5 deselected in 32.46s
```
271 before, 21 added, none lost.

### Lint

Command: `./.venv/bin/ruff check src/ tests/`
```
All checks passed!
```

### Acceptance check

**1a — the segment's own changes**
```
 README.md                        |   2 +-
 src/dynaswarm/analysis/load.py   |  36 +++++++++++++++++++++++++++++----
 src/dynaswarm/cli.py             |   6 +++++-
 src/dynaswarm/config.py          |  29 ++++++++++++++++++++++++++++
 src/dynaswarm/harness/trial.py   |   4 ++++
 src/dynaswarm/io/schema.py       |   9 +++++++++
 src/dynaswarm/viz/replay.py      |   4 +++-
 tests/test_analysis.py           |   2 +-
 tests/test_harness.py            |   8 ++++----
 tests/test_hygiene.py            |   2 +-
 tests/test_provenance.py         | 258 +++++++++++++++++++++++++++++++++
```

**1b — nothing outside scope:** `git diff --stat -- conf/ scripts/` is empty.

**2 — suite:** `292 passed, 5 deselected in 32.46s`

**3 — lint:** `All checks passed!`

**4 — statement budget against the new cap:** `src/ = 1998 / 2100   margin 102`

**5 — `run_class` recorded in both places**, run B:
```
manifest.json  -> manifest
steps.parquet  -> ['manifest']
events.parquet -> ['manifest']
```
And run A, confirming the default holds end to end: `manifest.json -> exploratory`, `steps.parquet -> ['exploratory']`.

**6 — the migration rule against real pre-column runs.** Across all of `outputs/` — the two new runs plus the three from 30 Aug that have no column at all:
```
load_steps("outputs")                  -> ['manifest']

load_steps("outputs", run_class=None):
run_class
exploratory    6360
manifest       2880
```
No raise. The 6360 exploratory rows are run A (2880) plus 3480 from the three pre-column runs, which carry no column and are read as `exploratory` by D27.

**7 — A\* is exact**
```
run A: 720 astar rows, all excess == 0.0 -> True
run B: 720 astar rows, all excess == 0.0 -> True
```

**8 — committed, not pushed:** see the block below the commit.

**9 — the five named tests, every assertion byte-identical.** The complete diff for all five, showing only the call site changed:
```diff
-    steps, events = load_steps(tmp_path), load_events(tmp_path)
+    steps, events = load_steps(tmp_path, run_class=None), load_events(tmp_path)
-    frame = load_steps(tmp_path)
+    frame = load_steps(tmp_path, run_class=None)
-    frame = expand_maps(expand_maps(load_steps(tmp_path), "params"), "probe")
+    frame = expand_maps(expand_maps(load_steps(tmp_path, run_class=None), "params"), "probe")
-    summary = per_trial_excess(load_steps(tmp_path))
+    summary = per_trial_excess(load_steps(tmp_path, run_class=None))
-    summary = per_trial_excess(load_steps(tmp_path))
+    summary = per_trial_excess(load_steps(tmp_path, run_class=None))
```
That is every changed line in both files. No assertion, fixture, name or docstring touched. All five pass.

**10 — a report from run A (exploratory) is not blank.** The check that would have caught the original contradiction:
```
per_trial.csv : 48 rows  non-empty=True
recovery.csv  : 48 rows  non-empty=True
arm_comparison.png         33700 bytes  non-blank=True
excess_over_time.png      108518 bytes  non-blank=True
recovery_profile.png       47629 bytes  non-blank=True
```
It is also pinned as a test — `test_the_report_path_produces_non_empty_output_for_an_exploratory_run` — so it cannot regress silently.

### Verbatim blocks

**The `run_class` validation:**
```python
RUN_CLASSES = ("manifest", "exploratory", "inversion")

    def __post_init__(self) -> None:
        """Reject an unrecognised run class before any work begins."""
        if self.run_class not in RUN_CLASSES:
            raise ValueError(f"unknown run_class {self.run_class!r}; permitted: {RUN_CLASSES}")
```

**The migration branch in `load_steps()`:**
```python
    frame = _load(directory, "steps.parquet")
    # Two distinct gaps to close, and a mixed load produces both at once:
    # a tree where *no* run has the column, and a concatenation where
    # only some do — pandas fills the latter with NaN.  Neither may raise.
    if "run_class" not in frame.columns:
        frame["run_class"] = None
    frame["run_class"] = frame["run_class"].fillna(UNCLASSIFIED)
    if run_class is not None:
        frame = frame[frame["run_class"] == run_class]
    return frame
```

**Ruling 1 applied, `cli.py`:**
```python
    # One named run, not an aggregation: the manifest-only default exists
    # to stop scratch rows contaminating a pool of runs, and reporting on
    # the run just produced is not that.  Filtering here would emit blank
    # figures for every exploratory run and raise nothing.
    steps = load_steps(directory, run_class=None)
```

**`value_counts()` across all five runs, filtering disabled** — pasted under check 6 above.

### Deviations from spec

None. Every task was implemented as the addendum directs.

One judgement recorded rather than deviated on: Ruling 3 says update `test_statement_budget`'s constant "and only this constant". The comment block above it explains the cap's rationale and does not name a number, so it needed no edit and got none.

### Surprises

1. **The migration-rule fixture nearly tested the wrong thing.** My first `_strip_run_class` helper round-tripped the parquet through pandas, which turns the `params` and `probe` `map<string, double>` columns into lists of tuples that cannot be written back — three tests failed with `ArrowTypeError`. Rewriting it at the Arrow level (`pq.read_table` → `drop_columns` → `pq.write_table`) preserves every type, so the fixture is now a file identical to a genuine pre-column run in every respect but the column. Worth recording because a fixture that differs from reality in a second way tests something other than what it claims.

2. **`run_class` comes back as `ArrowStringArray`, not `object`.** Under pandas 3 / pyarrow 25 the column loads as an Arrow-backed string dtype. Equality filtering and `fillna` both behave correctly, and `.unique()` prints as `<ArrowStringArray>` rather than a plain list — cosmetic in output, but worth knowing before anyone writes a strict dtype assertion against it later.

3. **The two baseline runs are numerically identical to each other and to the 30 Aug exploratory run** — ACO 10.33 %, PSO 39.50 %, hybrid 8.69 %, A\* 0.00 %. That is correct and is the reproducibility guarantee working: `run_class` is provenance metadata and is not entropy, so it cannot perturb a result. Runs A and B differ only in their label. Worth stating explicitly since three identical result sets could otherwise look like a copy-paste error.

4. **`events.parquet` had no test before this segment.** Adding `run_class` to `EVENT_SCHEMA` meant writing the first assertion anywhere in the suite that the event table's contents are correct. Ruling 4 closed a real asymmetry, and the gap behind it was slightly wider than the ruling described.

### Could not do

Nothing. All revised tasks completed.

### Questions for the Architect

1. **`load_events()` is still unfiltered.** `run_class` is now recorded in `events.parquet`, but `load_events()` takes no `run_class` argument and applies no default filter, so the asymmetry Ruling 4 identified is closed in the *data* and still open in the *loader*. I did not add it — the addendum specified the schema, not the loader, and T3's filtering language names `load_steps()` only. Recovery analysis reads events across runs, so this is the same exposure one level up. Worth its own small task rather than my improvising it here.
2. **`per_trial_recovery()` and other analysis entry points** take a frame rather than a directory, so they inherit whatever filtering the caller applied. That is the right design, but it means the guarantee rests on every future caller remembering. A single test asserting "no analysis helper accepts a directory path" would pin it — for Phase 2's Layer 2 probes, not for now.
