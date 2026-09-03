# WORKFLOW LOG

> **Append-only.** Every completed and verified segment is recorded here, newest at the bottom. Entries are never edited, never truncated, never reordered. If something recorded here later turns out to be wrong, a *later* entry says so — the original stays.
>
> This is the project's memory. If you are unsure why something is the way it is, read here before asking.
>
> **This file is written by the Architect, after verification.** vClaude never writes to it.

---

## Entry 001 — Segment 1: Documentation Truth Pass

**Phase** 0 (Ground truth) · **Segment** 1 of 3
**Verified** 30 Aug 2026 · **Status** COMPLETE
**Commit** `7c569e4` "phase0 segment1" → pushed to `origin/main`

### What the segment asked for

Make `README.md`, `RUNBOOK.md` and `DOCUMENTATION.md` tell the truth. No code changes at all.

Every result figure in the repository was superseded, unverifiable, or both — none could be checked against a result file on this machine, and `DOCUMENTATION.md` quoted figures from a predecessor codebase whose own paper contains fabricated numbers. With every number due for regeneration at ≥100 trials (D5, D9), the honest state was: **these are provisional, and here is why.**

The instruction was to **mark**, never to delete and never to substitute one unverifiable number for another. Two distinct markers, deliberately not interchangeable:

- **Legacy and unverifiable — not evidence**, for figures from the predecessor codebase
- **Provisional**, for figures from *this* codebase that are merely superseded

This was also the first live test of the segment protocol, chosen because it carried zero risk to the science surface.

### What was done

| File | Change |
|---|---|
| `README.md` | 8 provisional markers above measured-result tables · M7 milestone corrected with an explanatory note · M10/M11 annotated · `ARCHITECTURE.md` pointer added near the top |
| `RUNBOOK.md` | Test counts corrected in 2 places · per-file table replaced with verified counts · provisional markers on the current-standing figures and the sigma-span table · supersession note on the experiments section |
| `DOCUMENTATION.md` | §1 scale block reframed and test count corrected · §18 test count and per-file table corrected · §19.1 retitled + legacy caveat · §19.2 retitled + provisional caveat · §20 framing line · §20.3 caveat strengthened |

No files added. No tests added. No code touched.

### Acceptance — as reported and as independently verified

| Check | Result |
|---|---|
| `git diff --stat` | Exactly 3 files: DOCUMENTATION.md (60), README.md (26), RUNBOOK.md (34) |
| `pytest -q -m "not slow"` | 271 passed, 5 deselected, 31.73s |
| `ruff check src/ tests/` | All checks passed |
| Stale-claim grep | No output (exit 1) |

**Architect verification.** The three files were read directly off the machine rather than accepted on report. All confirmed: 8 markers present; the design-of-record pointer at the top; M7 reading `⚠️ run once, result void — must be re-run` with the F1 explanation beneath; M9 correctly left as `🔬 ready to run` because it remains accurate; §19.1 retitled `LEGACY AND UNVERIFIABLE, NOT EVIDENCE`; §19.2 retitled `PROVISIONAL`; §20 intact; §20.3 strengthened; the stale-claim grep genuinely empty.

§1's two-codebase reframing came out better than the specification asked for: it states plainly that the predecessor is separate, retired and outside this repository, that none of its numbers may be cited, and then gives its size "for the record" rather than as part of this project's scale.

### Deviations from the specification — all reported, none improvised

1. **T1.2 had no target.** The spec asserted "the README's test-count figure is wrong." `README.md` states no test count at all. The stale counts were in `RUNBOOK.md` (×2) and `DOCUMENTATION.md` (×2). vClaude changed nothing in the README rather than inventing a place for it. **Architect error, correctly caught.**
2. **T3.5 named §1 only, but §18 carried the same stale claim** — and acceptance check 4 greps the whole file, so leaving §18 would have failed the check the spec itself set. Both corrected. **Architect under-specification, correctly caught.**
3. **T2.3 extended to the sigma-span table** in `RUNBOOK.md`, the only other table of measured results there. Marking prose figures while leaving a results table unmarked would have been the wrong reading of intent. **Ruled: keep.**
4. **M10/M11 annotated rather than having their ✅ changed** — both are true today but misleading. **Ruled: keep.** M9 was correctly left untouched.

### Findings that mattered more than the work itself

**1. The README's stated thesis is the superseded one.** Line 3 subtitles the project *"**Volatility-driven** compute allocation"*, and the Thesis block states the allocation *"should be driven by measured environmental volatility."* Per `ARCHITECTURE.md` §1.3 the current thesis is allocation driven by **recency**, and Claim 2 is precisely the finding that volatility *cannot* drive it.

> **The first sentence of the repository asserts the thing the project disproved.**

Outside the segment's four tasks, so it was reported and not fixed — correct behaviour. **Ruled: fixed in segment 2, with wording supplied by the Architect**, because the same sentence must hold consistently across the README, `ARCHITECTURE.md`, the report and the deck.

**2. Marker density.** Eight blockquotes in ~220 lines, two of them six lines apart. **Ruled: consolidate** to one prominent banner plus short inline pointers. Repetition dulls a warning; by the fourth identical box a reader skips it.

**3. Test counts drift by themselves.** `test_hygiene.py` is 75 collected tests, not the 3 every document claimed — it is parametrised across every source file. `test_optimizers.py` (40) is parametrised off `PARAM_SPEC`. So retiring `viz/replay.py`, adding `allocation/`, or adding any parameter will move these numbers automatically. **Ruled: date-stamp the tables with a drift note rather than pretending to maintain them by hand.**

**4. `README.md` §Layout is stale** — lists a `core/schedule` module that does not exist (that logic lives in `core/timeline.py`) and omits `analysis/recovery.py`. **Ruled: fixed in segment 2.**

### Decisions arising

| | |
|---|---|
| **Repository** | `RUNBOOK.md`'s clone URL stays at `github.com/VaibhavBansal05/Dynaswarm.git`. Rudra has collaborator write access; no fork needed |
| **Commit cadence** | One local commit per segment. **vClaude commits, Rudra pushes, and only after Architect verification** — nothing unreviewed reaches the remote |
| **Phase 0 is three segments, not two** | Segment 2 takes the documentation follow-ups arising above; segment 3 takes the `run_class` convention and the baseline run. Doc work and schema work are not mixed in one unit |

### Assessment of the protocol's first run

It worked, and it earned its keep. vClaude found two errors in the Architect's own specification (deviations 1 and 2), one of which would have made the segment's own acceptance check unpassable. It reported a fifth contaminated area rather than fixing it outside scope. It flagged both of its extensions rather than burying them. The independent file verification found no discrepancy between report and reality.

**Continue as designed.** The one adjustment: from segment 2, Rudra approves edits in bulk rather than one at a time — the per-edit approval in segment 1 confirmed the behaviour is trustworthy, and the acceptance check plus Architect verification remain the real gates.

---

## Entry 002 — Segment 2: Documentation Follow-Ups

**Phase** 0 (Ground truth) · **Segment** 2 of 3
**Verified** 31 Aug 2026 · **Status** COMPLETE
**Commit** `c5e96cd`

### What the segment asked for

Close out the four issues segment 1 found and correctly declined to fix. Still no code — the same three documents, plus a local commit.

The largest mattered more than everything segment 1 did: **the README's headline sentence asserted the thesis the project disproved.** Line 3 read *"Volatility-driven compute allocation…"* and the Thesis block said the allocation *"should be driven by measured environmental volatility"* — which is precisely what Claim 2 refuted.

### What was done

| File | Change |
|---|---|
| `README.md` | Subtitle → *"Recency-driven compute allocation…"* · Thesis block replaced with Architect-supplied text · "Supporting question" paragraph reframed as settled history · provisional banner added · all 8 blockquote markers replaced with a single inline pointer each · `Layout` block corrected |
| `RUNBOOK.md` | Drift note above the per-file test-count table |
| `DOCUMENTATION.md` | Same drift note above the §18 table |

**The new Thesis block does something the old one could not: it states plainly that this is not the thesis the project started with, and why it changed** — that the optimal parameters do not depend on the disruption rate at all, so a volatility-driven controller has nothing to steer by, while recency describes a transient the sweep said nothing about. The correction became a strength rather than something to hide.

### Acceptance — reported and independently verified

| Check | Result |
|---|---|
| Scoped diff | Exactly the three in-scope files; `src/ tests/ conf/ scripts/` empty |
| `pytest -q -m "not slow"` | 271 passed, 5 deselected, 35.26s |
| `ruff check src/ tests/` | All checks passed |
| Superseded framing in README claims | No output |
| Banner / inline pointers | 1 and 8 |
| Phantom `core/schedule` | No output |

**Architect verification.** Files read directly off the machine. T3's drift notes confirmed at `RUNBOOK.md:43` and `DOCUMENTATION.md:1210`; findings block at `currentWorkFlow.md:204`; commit `c5e96cd` clean and unpushed. Everything vClaude reported was accurate.

### An Architect error, recorded because it changed a convention

Before verifying, the Architect asked vClaude to resume on the assumption it had been interrupted, describing T3 and T5 as "unverified" — meaning only *"I have not looked"*, but reading as doubt about completed work. vClaude had in fact finished the whole segment before the laptop closed.

**It refused to silently reconcile**, laid out its evidence task by task, declined to re-run finished work or amend a correct commit, and offered a read-only re-verification instead. That is exactly the behaviour the protocol is for, applied against the Architect rather than the code.

### Deviations — all reported, none improvised

1. **Acceptance check 1 was unsatisfiable as written.** "Exactly three files" assumes a clean tree at segment start. Specs now arrive *as* uncommitted edits to `currentWorkFlow.md`, and `AGENT_PROTOCOL.md` and `WORKFLOW_LOG.md` were also modified before the segment began. The check would have made **every future segment report a false deviation** — and a check that cries wolf trains people to stop reading it. **Architect error.**
2. **The commit swept the whole tree**, following segment 1's precedent.
3. **T1.3 — the "Supporting question" paragraph was reworded on vClaude's own judgement**, flagged explicitly as judgement rather than instruction. The original read in the present tense, presenting a settled comparison as a live question, directly beneath a thesis block that had just moved past it.

### Rulings

| # | Question | Ruling |
|---|---|---|
| **Q1** | Commit scope — sweep, or vClaude's files only? | **Sweep, and it is now explicit.** Between segments the tree holds only the segment's work and the Architect documents from that same cycle — the spec that drove it, the log entry closing the previous one, any protocol patch it depends on. Those are one moment in the history, not separate concerns. Splitting them would leave Architect files uncommitted and drifting |
| **Q2** | Acceptance check wording | **vClaude's form adopted verbatim as the standard.** Two scoped diffs — one for the in-scope files, one asserting `src/ tests/ conf/ scripts/` is empty. "Exactly N files" was never the real requirement; the requirement is that the segment touched what it was scoped to and nothing on the science surface |
| **Q3** | `DOCUMENTATION.md:1115` | **No change.** It states a measured result about a hypothesis that was tested — history, and accurate |
| **Q4** | The "Supporting question" edit | **Keep, exactly as written.** Better than what it replaced and better than the Architect would have specified. Flagging it was right, and so was the judgement |

### A rule that came out of Q3, and will recur

> A sentence that **describes a hypothesis that was tested** is history and stays.
> A sentence that **asserts it as the project's position** gets corrected.

`DOCUMENTATION.md:1115` is the first kind; the README subtitle was the second. This is a cleaner test than searching for the word "volatility", and it applies to the report and the deck as much as to the repo.

### A seam worth naming for future specs

When a task supplies replacement text **verbatim** and an adjacent paragraph depends on what was replaced, that paragraph is in scope but its wording is not supplied. The convention: **make the minimal correction, and flag it explicitly as judgement rather than instruction.** Deviation 3 is the worked example.

### Also noted

- The provisional banner is a blockquote containing an `h2`, so it appears in the document outline as a section. A warning is not a section — **corrected in segment 3** to bold text. Architect's markup, Architect's fix.
- Every other README mention of volatility is legitimately history and was left alone.
- The `Layout` block's module ordering does not match the tree, but the spec said not to restructure, so only the two named inaccuracies were fixed. Correct restraint.

---

## Entry 003 — Segment 3: Run Provenance and a Clean Baseline

**Phase** 0 (Ground truth) · **Segment** 3 of 3 · **PHASE 0 CLOSED**
**Verified** 31 Aug 2026 · **Status** COMPLETE
**Commit** `a71cb93`

### What the segment asked for

Make results files say what they are. A `steps.parquet` from a real 100-trial experiment and one from a ten-second scratch run were indistinguishable, and three exploratory runs already sat in `outputs/`. Loading "all the results" would have silently mixed them and produced a confident wrong answer with no exception — **the exact failure that killed the predecessor codebase.**

First segment to touch code.

### What was done

`run_class` with three permitted values (`manifest` / `exploratory` / `inversion`), defaulting to `exploratory`, validated so an unrecognised value raises. Recorded in `manifest.json`, `steps.parquet` **and** `events.parquet`. `load_steps()` returns `manifest` rows only by default; single-run tools pass the class through and are not filtered (D30). A missing `run_class` reads as `exploratory` (D27), so every run predating the column loads without migration.

Six source files, four test files, `README.md`. Statement cap raised to 2100 (D28).

### Acceptance — ten checks, all independently verified

| # | Result |
|---|---|
| 1a | 11 in-scope files |
| 1b | `conf/ scripts/` empty |
| 2 | **292 passed**, 5 deselected — 271 before plus 21 new, none lost |
| 3 | Lint clean |
| 4 | `src/` at **1998 / 2100** — margin 102 |
| 5 | Run B: `manifest` in all three places. Run A: `exploratory` |
| 6 | `load_steps("outputs")` → `['manifest']`; unfiltered → 6360 exploratory + 2880 manifest, no raise |
| 7 | A\* exact — 720 rows per run, `True` |
| 8 | `a71cb93` on top, ahead 1, unpushed |
| 9 | Five named tests pass, **every assertion byte-identical** — the diff is five lines, only the `load_steps()` argument |
| 10 | Run A's report: 48-row CSVs, 33–108 KB figures — **not blank** |

**Architect verification.** `load.py` and `schema.py` read directly. Confirmed `load_steps(directory, run_class="manifest")`, the migration fill via `UNCLASSIFIED`, and `run_class` in both schemas at lines 26 and 71. Report accurate throughout.

Check 10 is the permanent guard added by the addendum — the check that would have caught the Architect's original contradiction, now part of the suite.

### T0 re-measured, because scope changed

D29 says measure. The addendum added two source files and `EVENT_SCHEMA` **after** the original sketch, so vClaude **re-established the number rather than carrying a stale one forward**: the addendum cost +1 statement (`EventRow.run_class`), everything else free. 1984 → 1997 → 1998.

That is D29 applied correctly on its first outing after being written. A measurement that predates a scope change is not a measurement.

### Three findings worth keeping

**1. The fixture nearly tested the wrong thing.** The first pre-column fixture round-tripped parquet through pandas, which mangles `map<string,double>` columns — three tests failed with `ArrowTypeError`. Rewritten at the Arrow level so the fixture is byte-identical to a real pre-column run **except for the missing column**.

> A fixture that differs from reality in a second way is not testing the migration rule. It is testing the fixture.

**2. The two baseline runs are numerically identical** — ACO 10.33%, PSO 39.50%, hybrid 8.69%. This is **correct, and it is the reproducibility guarantee working**: `run_class` is metadata, not entropy, so it cannot perturb a result. Flagged because three matching result sets could otherwise read as a copy-paste error — including to an examiner.

**3. Ruling 4 was half a fix — Architect error.** `run_class` now lives in `events.parquet`, but **`load_events()` takes no `run_class` argument and applies no filter.** The asymmetry is closed in the data and still open in the loader, and **recovery analysis reads events across runs** — the same exposure one level up. The ruling named the schema; it should have named the loader too. Reported rather than improvised, correctly.

**Ruled: closed in Phase 0.5**, as an explicit task. Phase 0.5 already touches `analysis/recovery.py` — F1's off-by-one shifts the damage window — so it is the same neighbourhood and the same reviewer attention. Segment 3 is not reopened; Phase 0 closes with the gap recorded rather than forgotten.

### Phase 0 closed — what it bought

Three segments. The repository no longer lies about what it knows.

- **Documents** state what is unverifiable, and distinguish *legacy* (predecessor, no result files, never evidence) from *provisional* (this codebase, superseded, being regenerated)
- **The README no longer asserts the thesis the project disproved**, and says plainly why the thesis changed
- **Results files declare their own class**, and the default load returns only reportable rows
- **Runs predating the column load without migration**, so nothing had to be rewritten or discarded
- **A real baseline exists** on the research tier, with A\* verified exact

No experiment has been run yet. No defect has been fixed. That is the point of a ground-truth phase — the floor is trustworthy before anything is built on it.

### The protocol after three segments

vClaude has now found **five errors in Architect specifications** across three segments: a task with no target, an under-specified section, an unsatisfiable acceptance check, a contradiction that would have produced blank figures silently, and a half-closed ruling. Every one was reported rather than improvised around, and two were caught *before* any work was done.

It has twice declined to proceed on instructions it judged wrong — once refusing to produce the blank-figure run, once refusing to re-do work the Architect wrongly believed unfinished. Both refusals were correct.

**Three conventions now permanent, all originating with vClaude:** the two-scoped-diff acceptance form (Entry 002), the T0 measurement before any `src/` change (D29), and re-measuring when scope changes mid-segment (this entry).

---

## Entry 004 — Segment 4: The Invariants, and F1

**Phase** 0.5 (Defect triage) · **Segment** 1 of 2
**Verified** 1 Sept 2026 · **Status** COMPLETE
**Commit** `e7cdffd`

### What the segment asked for

Write the three Layer 1 invariants, **watch I2 fail on the unfixed code**, then fix F1 and watch it pass. The fix is one line; the ordering was the deliverable.

### The sequence, as evidence

**T0 — `+0` statements.** Everything went test-side: the timeline observed by substituting a recording subclass where the harness builds it, optimizers by walking their object graphs from outside. No hook in `src/`. The F1 fix modifies one statement rather than adding any. Surface unchanged at **1998 / 2100**.

**I2's failure, before the fix:**

```
AssertionError: 60 future-state read(s) out of 71; first at timestep t=0 reading
schedule[0], which is the transition from state 0 to 1 and has not been applied
yet. A component is reading the future.
```

Four failures, all in the I2 family. **I1 and I3 passed on unfixed code**, as required — a failure there would have meant either a wrong test or an undiscovered defect.

**The fix:**

```diff
-        return self.schedule[t] if 0 <= t < len(self.schedule) else ()
+        return self.schedule[t - 1] if 1 <= t <= len(self.schedule) else ()
```

`1 <= t`, not `0 <= t`, because `schedule[-1]` is a valid Python index that would have handed back the final timestep's events. `changed_edges()` already used the correct convention and is now pinned to agree.

**After: 9 passed.**

### Why I2 worked — the transferable lesson

> The violation is invisible in `events_at`'s argument. `events_at(t)` at timestep `t` looks innocent. It is visible in **which schedule index is read**. An observer watching arguments would have passed.

**Observe the effect, not the call.** This generalises to I1 and I3, and it will apply again to the allocation governor's saturation checks in Phase 3.

### Blast radius — inherited, not compensating

```
flagged steps before: [1, 2, 5, 6, 7, 8, 9, 10, 12, 17, 22, 23]
flagged steps after : [2, 3, 6, 7, 8, 9, 10, 11, 13, 18, 23, 24]
after == before shifted by +1 ? True
```

Both consumers read `num_events`; neither does index arithmetic that could offset the error. `recovery.py`'s window is correct given aligned data. **The fix propagates. Neither file needed changing.**

### F5 — the metric that was reading a constant

`mean_recovery` was **identically 0.000** — every arm, every disruption, every scenario. `excess[t]` was the pre-disruption reading, so it always already sat inside the recovery band and everything scored as recovering instantly.

Not a distortion. **A measurement instrument reading a constant** — and one that would have looked entirely plausible in a report, because "the hybrid recovers immediately" is a flattering result nobody interrogates.

`ARCHITECTURE.md` §11.2 makes recovery analysis a first-class experiment precisely because Claim 1's mechanism predicts the advantage lives just after a disruption. **That experiment was going to be run on a dead instrument.**

Same data after the fix: ACO 0.475 steps, hybrid 3.350.

### F4 — the warm-up transient F1 was concealing

Every windowed signal reads low for its first `window` steps, and controllers act from `t=0`. A systematic early-life bias in every adaptive arm, present for the project's entire history, hidden because F1 made `t=0` falsely report a disruption.

Scoped precisely: it affects `edge_ratio`, `volatility` and `lambda_branch` — the **evidence set** behind Claim 2. It does **not** affect `recency`, which is a decay rather than a mean and carries no window. **Claim 3, the allocation thesis, is untouched.**

### R1 — the test was strengthened, not relaxed

The literal `min(readings) > 0.99` could not survive; it asserted a falsehood that only F1 made true. What replaced it asserts strictly more:

| | before | after |
|---|---|---|
| Saturation | `min(readings) > 0.99` | `min(readings[window:]) == 1.0` — narrower range, exact value |
| Warm-up ramp | unasserted | asserted exactly, against a rolling mean derived from observed events |
| `t=0` | unasserted | asserted quiet |
| Rates | pooled into one list | checked per rate, so neither can mask the other |

The expectation is **derived from the event series rather than hard-coded**, so it tests the signal rather than this seed's draw. F4's explanation lives in the docstring.

302 passed. Lint clean.

### Check 9 could not run — and that is the finding

The specified guard was `mean_recovery` non-zero on `outputs/2026-08-30/22-53-36`. It is 0.0, and **always will be**.

> All five stored runs predate the fix, so their `num_events` is **recorded data — permanently misaligned**. The fix corrects what new runs write. It cannot repair a parquet.

vClaude implemented the *intent* instead: a permanent test pooling transients across six trials and two arms, asserting not all recovered instantly. Proof it bites, via in-process revert:

```
WITH F1: 42 recovered, any(>0) = False  max=0
FIXED  : 44 recovered, any(>0) = True   max=10
```

**The pooling is the part worth keeping.** `medium200` at 40 steps yields `mean_recovery = 0.0` legitimately on three disruptions, so a per-arm assertion would go red for innocent reasons — and that is exactly how a guard gets weakened later by someone who assumes it is flaky. A guard that cries wolf is a guard that gets removed.

### Ruling — the pre-fix runs, and a new principle

**All five stored runs are permanently unusable for anything disruption-aligned.** Their quality columns (`excess`, `optimum`, `best_cost`) are fine — those derive from `state_at()`, which was always correct. Only `num_events`, and therefore every disruption-relative analysis, is off by one.

`outputs/2026-09-01/09-29-56` — the only `manifest`-class run in existence — carries that misalignment. **Ruled: reclassify it to `exploratory`.**

`manifest` means *reportable*. A run whose disruption alignment is permanently wrong is not reportable for anything touching disruptions, and a class meaning "reportable for some columns but not others" is not a class — it is a footnote nobody reads. Phase 4 regenerates everything at ≥100 trials regardless.

This required resolving a genuine conflict, and the resolution is now a standing principle:

> **A run's measurement data is immutable. Its `run_class` may be corrected — but only with a written reason left in the run directory itself.**

Immutability protects a run as *evidence of what happened*. It does not oblige a mislabelled run to keep a label that will actively poison future analysis. A status label is metadata about standing, not a measurement, and correcting it is not falsifying anything. But it is never done silently.

Recorded as **D31**. Executed in segment 5.

---

## Entry 005 — Segment 5: F2, F3, and the Loose Ends

**Phase** 0.5 (Defect triage) · **Segment** 2 of 2 · **PHASE 0.5 CLOSED**
**Verified** 1 Sept 2026 · **Status** COMPLETE
**Commit** `20e5bbf` (amended to fold in the addendum's T7)

### What the segment asked for

Close Phase 0.5. Two remaining defects, one reclassification, two carried-forward gaps — then, by addendum, a third defect vClaude found while working.

### What was done

| | |
|---|---|
| **F2** | `IncrementalController.propose` now raises on an unknown target, matching `bind()` in `optimizers/spec.py` |
| **F3** | `cross_evaluate.py` rebuilt against the current scenario definitions; exits readably when the tuned vectors are absent, naming the glob and the Phase 4 step that produces them. Exit 1, no traceback |
| **F6** | `PrescheduledController` given the same guard (addendum T7) |
| **T1** | `outputs/2026-09-01/09-29-56` reclassified `manifest` → `exploratory` under D31 |
| **T4** | `load_events()` given `run_class` filtering, sharing a `_classified()` helper with `load_steps()` |
| **T5** | The F4 warm-up assertion parametrised across all three windowed signals, with `recency`'s exemption asserted |

**T0, re-measured after the addendum (D29):** `2002 → 2005 / 2100`, margin 95. Projected `+3` before writing — Assign, If, Raise — and it came out at exactly `+3`, counted with the suite's own `_statement_count` rather than a reimplementation of it.

The `+4` for the main block came in under a naive sketch's `+9` because `load_events`'s filtering went into a **shared** `_classified()` helper rather than being duplicated. The reasoning is worth keeping: **provenance filtering that disagreed between the step and event tables would be worse than none**, because the disagreement would only surface when someone joined them.

### The reclassification, and D31's amendment

Digests identical before and after, both tables. Applied at the Arrow level so the `map<string,double>` columns survive — carrying forward segment 4's fixture lesson.

**vClaude found the flaw in D31 as written.** `outputs/` is gitignored, so `RECLASSIFIED.md` lives where version control cannot see it — *the trace was as ephemeral as the thing it described.*

**D31 amended:** the correction is recorded in two places doing two jobs — `RECLASSIFIED.md` in the run directory as the local warning for whoever opens that folder, and **this log entry as the authoritative, tracked, durable record.**

> **Authoritative record of the reclassification.** On 1 Sept 2026, in segment 5, `outputs/2026-09-01/09-29-56` was reclassified from `run_class: manifest` to `run_class: exploratory` in `manifest.json`, `steps.parquet` and `events.parquet`. **Reason:** the run was generated before F1's fix, so its `num_events` column is permanently misaligned by one timestep and it is not reportable for anything disruption-related. **No measurement column was altered** — digests of the quality columns are identical before and after, verified at the Arrow level.

### The record check — the standard this project should hold to

The question was whether F2 ever contaminated a run. The easy answer was *"the RUNBOOK and the deck both show `targets=[aco_fraction]` was passed."* vClaude did not take it.

> All five runs used `targets: ['rho']` — **the inert configuration** — but **none used a controlled arm.** `astar`, `aco`, `pso` and `hybrid` carry no controller, so `IncrementalController.propose` was never constructed and never called.

So the finding is not *"we got lucky with a flag"* but **"the code path could not execute"** — established from the configs themselves rather than from documentation about them. Those are different strengths of claim, and only the second survives a viva.

### F6 — what the guard was hiding

The new test fails against unfixed code (`DID NOT RAISE KeyError`). The artefact worth reading is the consequence, reproduced from the pre-fix `propose` in the configuration that actually triggers it — a 1.0 → 2.0 sweep on `targets=("rho",)` against a hybrid's `aco_`-prefixed vector:

```
every timestep identical to the frozen vector: True
  t=0: {'aco_fraction': 0.5, 'aco_rho': 0.08, 'aco_alpha': 1.0}
  t=9: {'aco_fraction': 0.5, 'aco_rho': 0.08, 'aco_alpha': 1.0}
```

**Not approximately the frozen arm — byte-identical to it, at every timestep, while the multiplier ran to 2.0.** Nothing downstream could have distinguished `ScheduledAllocation` from its own control.

### The demonstration that was wrong first, and why that matters

vClaude's first attempt at that reproduction passed the target into `current`, so membership succeeded and the sweep worked correctly.

> "I had built a demo of the code not failing, and it looked convincing until I read the numbers."

**This is the same failure as segment 4's fixture, in a different costume.** A reproduction that differs from reality in one detail tests the reproduction. Twice now the detail was small, plausible, and would have produced a confident wrong conclusion. The habit that caught both was reading the output rather than trusting the setup.

### The family audit — and `NullController`'s exemption done properly

Five sites checked. `bind()` is the reference; both controllers now match it.

`NullController` is exempt **by construction**, and vClaude asserted the construction rather than the behaviour:

```python
assert not hasattr(NullController(), "targets")
```

The reasoning is the point: *a test that merely checked `propose` returns its input would still pass in a world where someone added target handling without a guard — which is exactly how F2 and F6 got in.* Assert the property that makes the bug impossible, not the symptom of its absence.

### F7 — the fourth site, and it is worse than the bug it was found beside

`harness/arm.py:228` builds the prescheduled controller as `make_controller(spec.controller)` — **no arguments**. It therefore takes every default: `control.targets` is silently discarded, and `start == end == 1.0` makes the multiplier **identically 1.0**, so it varies nothing even on a target it does have.

> **F6 needed a misconfiguration to bite. This needs nothing.** And the new guard does not protect it, because `("rho",)` is legitimately declared by an ACO arm.

**Not fixed, and correctly so.** Choosing `start`, `end` and `horizon` is a Phase 3 science decision, not a defect repair — half-fixing a component whose correct behaviour is undefined would be worse than leaving it named.

Neither F6 nor F7 can have touched a run on disk: **no registered arm requests `prescheduled` at all.**

**Ruled:** logged as F7. Phase 3 must address it when `ScheduledAllocation` is designed, and **`ScheduledAllocation` cannot be considered complete until a test asserts it actually varies something.** That constraint goes into Phase 3's spec.

### The dead fallback — deferred, deliberately

Mirroring F2 exactly left `current.get(name, 0.0)` and `if name in proposed:` unreachable behind the new guard. The `.get` is now not merely redundant but misleading: **it encodes `0.0` as an initial value**, which would come alive as a wrong default if the guard were ever relaxed.

**Ruled: leave it, and fix it in Phase 3** — where both controller classes are restructured into `allocation/` anyway. Touching them twice for tidiness is worse than touching them once for design. Logged so Phase 3 inherits it rather than rediscovering it.

vClaude's reason for leaving it was also right: *"two fixes for one bug should read identically."* Symmetry between F2 and F6 was worth more than removing an unreachable line.

### A counting correction, and a convention

The "313 tests" reported at the close of the first block was the `-m "not slow"` figure given **without the marker qualification**. The full suite stood at 318.

Flagged by vClaude precisely because this log records those counts, and *a number that quietly excludes five tests is the kind of thing that survives a phase unnoticed.*

**Convention from here: always record both, always qualified.** This segment closes at **321 passed, 316 not-slow, 5 slow.** Lint clean across `src/`, `tests/` and `scripts/`. Surface `2005 / 2100`.

### One unasked edit, correctly flagged

vClaude amended the commit line describing D31, which still said the reason was "recorded in the run directory" — D31's superseded form, and the exact claim R1 had corrected. Small, correct, and flagged rather than slipped in. **Approved.**

---

## PHASE 0.5 CLOSED

**Every known defect is fixed or repaired.** F1, F2, F3, F5 and F6 closed. F4 and F7 recorded, scoped and assigned to Phase 3 with the reasons they were not fixed here.

Two segments bought:

- **F1** — the off-by-one that made every component read one timestep into the future, and voided every recency-driven result the project had
- **F5** — `mean_recovery` reading a constant 0.000, a dead instrument that would have reported a *flattering* result nobody would have interrogated
- **F2 and F6** — two controllers reporting themselves active while adapting nothing
- **F3** — the script behind the project's key explanatory finding, restored to runnable
- **Three Layer 1 invariants**, one of them observed failing before its defect was fixed

And two habits that generalise: **observe the effect, not the call** — and **read the output, do not trust the setup.**

Phase 1 next. The first thing built rather than repaired.

---

## Entry 006 — Segment 6: Dashboard Scaffold

**Phase** 1 (See it) · **Segment** 1 of 5 · **Overall segment** 6
**Verified** 3 Sept 2026 · **Status** COMPLETE
**Commit** `c253e2a`, ahead 1, unpushed

### What the segment asked for

Stand up the dashboard and prove the pipe — a browser page showing numbers that came from the real engine. Draw nothing. Establish the boundary that keeps the dashboard a view **before** any drawing code exists, on the reasoning that a boundary asserted afterwards is one somebody has already had a reason to cross.

### Architect verification

Read off disk, not taken from the report:

| Claim | Verified |
|---|---|
| `server.py:97` restored to `heuristic=True` | Yes — read the file |
| `RUNBOOK.md` §6 "The dashboard" exists, port and host stated | Yes — lines 343–392 |
| `pyproject.toml:29` dashboard group, fastapi + uvicorn only | Yes |
| `dashboard/` statement count = 45 | **Recomputed independently** with `_statement_count`'s own logic: `__init__.py` 0, `server.py` 45, total **45 / 1000**, headroom 955. Exact match |
| `FORBIDDEN_IMPORTS` does not reach `dashboard/` | Yes — `test_hygiene.py:16` roots `SRC` at `src/dynaswarm`; `_python_files()` is `SRC.rglob` |
| FINDINGS appended | Yes, complete |

**Independent evidence the report did not have.** vClaude could not screenshot a browser and rendered the page by executing `app.js` under node. Rudra opened `127.0.0.1:8000` in Chrome and the browser render matches the node harness field for field — `optimum_at_t0 99.96328976797456`, `expansions 75`, `exploratory 9240`, the D32 warning, the footer. **The pipe is confirmed from outside the process that built it.**

### The result worth naming: `src/` did not move

`2005 / 2100`, delta **+0**. The spec said a scaffold needing the science surface is a design problem, not a measurement problem — stop and report. Nothing came up. Every value on the page was already reachable through a public function: `build()`, `shortest_path()`, `stream()`, `load_steps()`.

That is a *result*, not an absence. §2.3 asserts the core exposes what the dashboard needs; this is the first segment that could have falsified it, and did not.

**955 statements for segments 7–10.** The retiring `viz/replay.py` is 158 and does the graph-drawing job segment 7 inherits. The cap is not close.

### The mutation — the finding of the segment

vClaude mutated the dashboard into the most plausible reimplementation available: the same core function, the same correct answer, a different search (`heuristic=True → False`).

```
E   AssertionError: expansion count differs — the dashboard is running its own search
E   assert 200 == 75
```

**The optimum assertion passed. The answer was still exactly right.**

Only `expansions` caught it, and the reason generalises: `optimum_at_t0` is a property of the *graph*, which anything competent can arrive at. `expansions` is a property of *this search* — heuristic, tie-break order, heap discipline — and nothing that recomputed the answer independently reproduces it by luck.

> **The correct number arriving from the wrong place is the failure this project has already died of once, and equality on the answer does not detect it.**

That is the standard every future dashboard test is held to: assert a value the engine's *process* produces, not only the value its *answer* has.

### `FORBIDDEN_IMPORTS`, verified behaviourally rather than structurally

The structural check ("the scan is rooted elsewhere") only matters if the scan would otherwise reject the file. vClaude ran the scan's own logic over `dashboard/server.py`: **four hits** — three `fastapi` imports and a **function-level** `import uvicorn` inside `main()` that `ast.walk` would still catch.

So D14 is load-bearing, not decorative. Moving `dashboard/` under `src/` breaks the build in four places rather than silently degrading. A second structural guarantee turned up unlooked-for: `pyproject.toml` packages only `src`, so `pip install dynaswarm` cannot drag a web framework along.

### My spec error — the fourth of this family

I asked for `git diff dashboard/server.py` as proof of the restore. `dashboard/` was **untracked** this segment, so that diff is empty and always would be. The check could not have proved anything as stated.

vClaude substituted a better one — `diff <(sed 's/False/True/' server.py) $S/server.good.py`, empty — which proves the saved copy differs by exactly that one flag and smuggled nothing in. Then it *said so* rather than pasting an empty diff as evidence.

**Generalised, for every future acceptance block I write:** a diff against git proves something only for tracked files. For new files the baseline has to come from somewhere the segment created deliberately.

### Deviations — all three accepted

1. **`/api/runs` as a second endpoint.** T3's "single endpoint" was scoped to proving the pipe. Overloading `/api/graph` with run provenance would have coupled two unrelated concerns in the one endpoint the anti-reimplementation test pins. Correct reading.
2. **`expansions`, `hops`, `tier`, `model` returned beyond spec.** `expansions` is not surplus — without it the mutation walks through.
3. **Tier read from `ConfigStore` rather than restated.** See R2 below.

### Rulings

**R1 — `RUNBOOK.md`'s test count: delete it, don't re-correct it.**

vClaude flagged line 27 (`271 not-slow tests`, actually 324). There is a second, unflagged: **line 38** — `276 collected · 5 slow · 271 not-slow · all passing`. Same rot, same cause.

The count has gone stale three times in six segments because it goes stale every time anyone adds a test — which is every segment. That is not a documentation defect; it is a static file claiming a moving quantity.

**Ruled:** both sites lose the number. Line 27's comment keeps the rough wall-clock and drops the count; line 38 says what the suite is *for* and tells the reader to run it. The authoritative counts live **here**, in `WORKFLOW_LOG.md`, where each is dated and append-only — a number that describes a moment cannot rot, while a number that claims to be current always can.

Assigned to segment 7 as a one-line task.

**R2 — `ConfigStore.repo` is accepted, but the coverage gets a name.**

The argument is right: a restated `GraphCfg(...)` works until someone edits the registration, after which the dashboard silently draws a tier that no longer exists under that name. Reading it back makes divergence impossible rather than unlikely, and a Hydra change fails loudly instead of silently forever.

But the coverage today is **incidental** — `test_has_coordinates_...` would fail if `ConfigStore.repo` moved, while being named for something else entirely. Entry 005's R3 recorded exactly this shape: *a test that exercises a thing is not thereby testing it, and if the assertion would hold with that thing removed, it should say so in its name.* A future segment could rewrite that test for its own reasons and delete the Hydra protection without knowing it existed.

**Ruled:** keep the `ConfigStore` read; segment 7 adds one small test named for the thing it protects — `tier()` returns the fields the registration declares. ~3 statements against 955.

**R3 — Direct route calls stay the testing story. One HTTP test is added, for a reason the direct call cannot reach.**

A fixture that boots uvicorn tests uvicorn. But there is a real gap between calling `api_graph()` and serving it: **JSON serialisation**. `describe_graph` casts numpy scalars by hand today; the day someone adds a field and forgets the cast, the direct call passes and the HTTP response 500s. That is precisely *read the output, do not trust the setup*, one layer out.

**Ruled:** segment 7 adds one `fastapi.testclient.TestClient` smoke test — real routing, real serialisation, no socket, no port, no teardown — asserting 200 and a JSON body that round-trips. `httpx` is **authorised** into the dashboard optional group if TestClient requires it. No live-server fixture.

### Recorded, not acted on

`app.js`'s error path was exercised by accident: an early node harness failed with `Failed to parse URL from /api/graph` and the page rendered a visible `error` row rather than a blank panel. Unplanned, but it is the first evidence the page fails legibly, and segment 7 draws things that can fail.

### Close

**329 full / 324 not-slow** (from 321 / 316, **+8**, all in `tests/test_dashboard.py`). Lint clean across `src/`, `tests/`, `dashboard/`. `src/` **2005 / 2100**. `dashboard/` **45 / 1000**.

Phase 1 opens with the boundary tested before anything is drawn, and with a demonstration that the boundary's test catches a *plausible* violation rather than an obvious one.

Segment 7 draws the first graph.
