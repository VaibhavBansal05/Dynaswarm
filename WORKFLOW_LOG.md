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

---

## Entry 007 — Segment 7: Draw the Graph

**Phase** 1 (See it) · **Segment** 2 of 5 · **Overall segment** 7
**Verified** 3 Sept 2026 · **Status** COMPLETE
**Commit** `050069b`, ahead 1, unpushed

### What the segment asked for

Put the graph on screen — real coordinates, the oracle's path lit across it — under a rule sharper than §2.3's general one: **the browser receives geometry and never invents it.** Plus Entry 006's three rulings as T1.

### Architect verification

Read off disk, not taken from the report:

| Claim | Verified |
|---|---|
| `RUNBOOK.md` stale counts removed, both sites | Yes — `grep "271\|276 collected"` returns nothing |
| No layout library reached `static/` | Yes — `d3\|cytoscape\|vis\.js\|sigma\|force\|spring\|jitter` all absent |
| `/api/graph` untouched, geometry added alongside | Yes — `describe_graph` intact, `describe_geometry` at `server.py:116`, route at 197 |
| The transform is scale-and-centre only | Yes — `projector()` at `app.js:43-53`: min/max, one uniform `scale`, one centring offset. No inversion, no per-node adjustment |
| Refusal path draws nothing | Yes — `app.js:60-66`, SVG hidden, message shown. Not a fallback layout |
| `dashboard/` = 56 statements | **Recomputed independently.** `__init__.py` 0, `server.py` 56. Exact match |

### The instrument is measuring the wrong thing — and vClaude found it

**This is the entry's most important item.**

`_python_files()` globs `*.py`. `app.js` went 36 → 142 lines this segment and counted **zero**. So "944 headroom" describes the Python half of a component whose growth from here is overwhelmingly JavaScript: segments 8–10 add playback, arms and charts, all of them client-side.

A cap that reports comfortable headroom while the thing it guards grows unmeasured is not a weak brake. **It is F5 again** — `mean_recovery` reading a constant 0.000, a dead instrument returning a flattering number nobody interrogates. Second occurrence in this project of the same species.

**R1 — Ruled: two budgets, two distinct jobs. Do not stretch one to cover both.**

| Budget | Question it answers | Cap |
|---|---|---|
| `dashboard/**/*.py` statements | *Has the dashboard become a second engine?* | **1000** (unchanged, at 56) |
| `dashboard/static/**` non-blank, non-comment lines across `.js`, `.css`, `.html` | *Has the dashboard become an application?* | **1200** |

These are different failure modes and collapsing them would hide both. The Python cap guards the science boundary; the static cap guards scope.

**The unit is deliberately cruder, and the test must say so.** Counting JS statements needs a JS parser, which is a dependency this repo will not take for a budget. Non-blank non-comment lines is blunt and slightly gameable — and it is not zero, which is the entire property the current instrument lacks. **The test's docstring states its own imprecision**, so nobody later mistakes it for the AST count and reasons from a false equivalence.

Segment 8 implements it and reports the opening figure.

**R2 — The y-flip: leave it. And here is the condition that would change that.**

The mirror has no truth value today. `topology.pos` is points in a unit square from a geometric generator; **nothing in the data says which way is up**, so SVG's downward y is a different rendering of the same graph, not a wrong one. vClaude was right not to add a third transform unprompted.

**Revisit the moment anything on the page carries orientation** — printed raw coordinates in a tooltip, an axis, a legend keyed to position, any overlay with a top and a bottom. At that point the mirror stops being a convention and starts being a contradiction between two things on the same screen. Recorded so the trigger is recognised rather than rediscovered.

**R3 — `httpx` / `httpx2`: do not chase it. Logged as F9.**

The error message demanded `httpx2`; the source (`testclient.py:33-45`) still falls back to plain `httpx`. **vClaude trusted the source over the message, which is the correct order** — and worth noting that both available shortcuts were wrong: installing the unauthorised package, or reporting T1.3 blocked.

Neither migrate nor pin now. `starlette` is a **dev-only test dependency of a dev-only tool**; it cannot reach the science surface, and pinning it buys a stale pin in exchange for a warning.

**F9 — `TestClient`'s `httpx` fallback is deprecated and will be removed.** When it goes, the suite breaks for a reason unrelated to anything anyone changed — the expensive kind of failure, because it arrives during Phase 4 or 5 and costs an hour of looking in the wrong place. **The fix is known in advance: authorise `httpx2` into the `dashboard` group.** That sentence is the whole value of this entry; recognition is the cost, not repair.

### Mutation 3 — the finding of the segment

Mutation 1 was the one I specified: a valid path routed via a detour. `assert 171.75 == 99.96`. It behaved exactly as predicted — the real-walk test **passed**, because it *is* a real walk, and the drawing would have rendered a perfectly plausible longer line to the right target beside a caption quoting a different route's cost.

**Mutation 3 was vClaude's own, and it is the one that found a defect.** It rolled `weights` by one against `edges`: same length, every value real, every label wrong. `test_edges_and_weights_are_parallel` **passed** — it compared only lengths.

Incidental protection under a name that promised the real thing — the exact pattern Entry 005's R3 and Entry 006's R2 both ruled on, committed inside the segment whose T1.2 was about that pattern, by the agent that had just read both.

Caught downstream by the summed-weights test, which is luck rather than design. **Fixed properly, not merely filed:** each weight is now checked against `view.find_slot(u, v)` — verified on disk at `tests/test_dashboard.py:352-372` — so the test fails by its own name.

**Two rules out of this:**

> **A test that names a relationship must assert the relationship, not a consequence of it.** Equal lengths are a consequence of parallelism. They are not parallelism.

> **The mutations worth running are the ones nobody specified.** The commissioned mutation confirmed a prediction. The uncommissioned one found a real hole. Every future segment's mutation step must include at least one the spec did not name.

vClaude's own note is worth preserving verbatim: *"Knowing the rule is evidently not the same as not breaking it, which is presumably why the mutation step exists."*

### D8 corroborated from the pixel side

Unasked, and useful:

```
longest edge : 65 px on a 570 px canvas
edges > 100px: 0 (0.0%)
median edge  : 46 px      mean node spacing: 40 px
```

735 edges read as **fabric, not spaghetti**, because a geometric generator connects near neighbours — no edge crosses the picture. On Erdős–Rényi the median edge would span roughly a third of the canvas.

So **v1's tangle was never a drawing defect. It was the tier.** Same rendering code, different generator. D8 was decided on research grounds; this is the same conclusion reached independently from the rendering side, and it is a better answer to *"why medium200?"* in a viva than the original argument, because it is visible.

### Carried to segment 8

**Minimum edge length is sub-pixel** — at least one node pair is coincident on screen. Anything clickable needs a hit-target policy; nearest-node-within-radius rather than exact hit, and a defined tie-break. Recorded now so segment 8 does not discover it through a control that silently selects the wrong node.

### Close

**337 full / 332 not-slow** (from 329 / 324, **+8**). Lint clean across three trees. `src/` **2005 / 2100**, delta **+0** for the second consecutive segment. `dashboard/` **56 / 1000** Python — and an unmeasured 142 lines of JavaScript, which R1 fixes.

948 SVG elements on screen, every coordinate the engine's own, verified by recomputing the transform independently from raw JSON.

Segment 8 makes it move.

---

## Entry 008 — Segment 8: Make It Move

**Phase** 1 (See it) · **Segment** 3 of 5 · **Overall segment** 8
**Verified** 3 Sept 2026 · **Status** COMPLETE
**Commit** `e38ffe9`, ahead 1, unpushed

### Architect verification

Read off disk:

| Claim | Verified |
|---|---|
| No re-derived event indexing in the dashboard | Yes — `schedule[` appears **only inside comments** explaining the contract, in both files. Never as code |
| `events_at()` is the source | Yes — `server.py:245` |
| No stored-run read in the timeline path | Yes — `load_steps` appears once, in `run_classes()` at `:280`. The timeline is built live |
| The static budget exists and states its own imprecision | Yes — `test_dashboard.py:398-455`. The docstring names `_statement_count` as the stricter measure and explains why this one is blunt |
| 24 tests | Yes — counted, including one I did not ask for: `test_the_dashboard_never_derives_event_timing_itself` |
| `src/` `2005 / 2100`, delta `+0` | Third consecutive segment |

### Mutation B — the gap, and it is the largest one open

Two characters, browser-side. `run.steps[t]` → `run.steps[Math.max(0, t - 1)]`. Server untouched, endpoint still perfect.

```
24 passed
```

**The entire Python suite is blind to it.** And what the page then shows at `t=21`:

```
mutated : optimum 103.25   hops 11    0 edges changed this step
correct : optimum 110.54   hops 12   25 edges changed this step
```

*"0 edges changed"* on the exact step where 25 edges break and the route re-routes — **printed beside a picture showing the break happen.** That is F1's shape exactly: not a crash, not an error, a confident wrong number in the artefact built to convince an examiner.

**246 lines of JavaScript are guarded by two greps and a harness that is not in the repository.**

#### My error, stated plainly

The spec claimed the design's self-disagreement property — the highlighted path visibly crossing an edge the page has greyed out — as a defence. **It is not one, and calling it one was me admiring a design instead of testing it.**

It fired: at `t=5` the blue route crosses two red broken roads. Three hits out of 696, on one frame of sixty, visible only to someone looking at that frame. A property, not a safety net. vClaude said so and was right to.

What actually stands between this and the demo is acceptance check 5b: **a human reading grep output once, at the end of a segment, when they are tired.** That is not a control.

#### R1 — Ruled: `node` is admitted as a dev-only test dependency

The decisive fact is not that JavaScript testing would be nice. It is this:

> **The node harness already exists and has been load-bearing for three segments.** Every "what the page actually renders" artefact in Entries 006, 007 and 008 came from executing `app.js` under node. The project has been relying on it to believe its own evidence — while keeping it in a scratchpad, unversioned, rewritten each time.

So this is not adopting an instrument. It is **admitting one already in use**, and the alternative is continuing to accept evidence from a tool the repository refuses to acknowledge.

Terms:

| | |
|---|---|
| **Scope** | `tests/` and `dashboard/` only. Nothing under `src/` may require it, ever |
| **Boundary, asserted** | A test proving the science surface is fully testable with `node` absent — mirroring segment 6's `test_the_core_is_importable_and_usable_without_fastapi`. Same shape: make it genuinely unavailable, then do real work |
| **Absent node** | Skip, with a reason naming what is not being checked. `RUNBOOK.md` states node is expected for the dashboard suite |
| **The trap** | **A skipped test is not a test.** Report the skip count in every segment close from here, qualified, alongside the pass counts — Entry 005's convention, extended. A JS suite silently skipping is this same defect wearing a third hat |

**And one guard that does not wait for segment 9.** Every step in the payload carries its own `t`; the renderer asserts `step.t === t` before drawing and throws if not. Two lines. It would have caught Mutation B on the spot — and it fires **in the browser, in front of your examiner**, which no test suite can do.

Both land in segment 9 as T1.

### Mutation A — and why it fails at t=1

`events_at(t)` → `schedule[t]`. Caught twice, failing at **`t=1`** with `assert 25 == 0` — *not* at `t=0`, where both are correctly empty.

Worth keeping: **the off-by-one is invisible at the boundary it is nearest to.** A test that sampled the first step, the last step and something in the middle could have missed it. Walking every timestep is why it was caught, and that is now the standard for anything indexed by time.

### F10 — the F1 arithmetic exists in two places

Found in `src/` and correctly left alone: `changed_edges` derives `schedule[t - 1]` independently rather than calling `events_at()`.

**Correct today.** The defect is that F1's arithmetic now lives in two places, and the second one is not the one the tests point at. A future edit to `events_at()` — a horizon change, an indexing convention, anything — leaves this behind, silently, and F1 returns through the door nobody is watching.

**Logged as F10. Assigned to Phase 2**, whose entire job is trusting what is there. One line: `changed_edges` asks `events_at()`. Statement-neutral or better.

### What the run actually does — worth having for the viva

```
t= 5    99.96 -> 102.02   11 hops
t=21   103.25 -> 110.54   11 -> 12 hops    <- a real re-route
t=57   110.54 -> 103.25   12 -> 11 hops    <- and a recovery
```

Twelve disrupted steps of sixty, and the optimum moves four times. Two facts neither of us had assumed:

- **`events_per_step` counts clusters, not edges.** Each is ~25 edges around one node, so a break reads as a neighbourhood going dark rather than a single road closing. That is a better demo than a single edge would have been, and it is worth being able to say why when asked.
- **A break that costs nothing is the common case.** At `t=2`, 25 edges break and the optimum does not move — the cluster landed off-route. **This is the project's thesis visible on screen:** disruption and *relevant* disruption are different things, which is precisely why recency of disruption, not volume of it, is what the allocation policy reads.

### Carried into segment 9 — legibility, now a design constraint

vClaude's read: movement is legible, and `e-hit` (red, this step) versus `e-changed` (amber, earlier) is what makes it work. Two warnings, both real:

- **48 of 60 steps are quiet.** Watching it play is mostly waiting. Segment 9 needs a jump-to-next-event control, or the demo dies in front of an examiner watching nothing happen for forty seconds
- **244 edges are amber by `t=59`.** Four coloured arm-paths on top of a mostly-amber field is the thing most likely to tip this into mud. Segment 9 must solve contrast *before* it adds arms, not after

### Close

**345 full / 340 not-slow** (from 337 / 332, **+8**). Lint clean. `src/` **2005 / 2100**, `+0` for the third consecutive segment — everything the timeline needed was already public. `dashboard/` Python **76 / 1000**; `static/` **246 / 1200**, opening figure 168.

Phase 1 is 3 of 5. The problem now moves on screen. Segment 9 puts the solvers on it — and closes the hole this segment found.

---

## Entry 009 — Segment 9: Two Layers, State and Event

**Phase** 1 (See it) · **Segment** 4 of 7 · **Overall segment** 9
**Verified** 4 Sept 2026 · **Status** COMPLETE
**Commit** `a41c0e8`, ahead 1, unpushed

### Architect verification

| Claim | Verified |
|---|---|
| `KINDS` are the six §15.4 names | Yes — `core/events.py:33`, exact |
| `palette.json` keys match `KINDS` byte for byte | Yes — read both; and pinned by a test, not by care |
| Six distinct dash patterns | Yes — `none / 1 4 / 8 3 / 4 2 / 2 2 / 1 6` |
| `add` and `reopen` share a hex | Yes — `#2fae5a` both. Separated by dash alone, deliberately |
| Entry 008 survived the `git add -A` sweep | Yes — present and intact in the working tree |
| `src/` `2005 / 2100`, `+0` | Fourth consecutive segment |

### The reduction is semantic, not cosmetic — this is the segment's result

`t=59`: **244 lit → 142** (92 deviating in price, 50 closure ghosts, 16 deleted drawn as nothing). On the colour channel alone, **244 → ~50**.

The sentence that matters:

> Segment 8's 244 counted **every edge ever touched**. A road that went up at `t=12` and recovered at `t=30` stayed amber to the horizon.

**Recolouring would have moved nothing.** The mud was not a palette failure; it was a category error — history painted where state belonged. The state layer lights only what *currently* deviates, so a road that recovered goes quiet, correctly, because it *is* quiet. That is the state/event split earning its keep rather than merely being implemented.

### The fade is the signal

`RecencySignal.decay = 0.7` (`signals.py:204`), unoverridden anywhere in `conf/` or `config.py`. A flash's opacity is **`0.7 ** age`** — not "about the same shape as" the controller's curve. **The same curve.** Cutoff derived rather than chosen: `0.7**13 ≈ 0.0097`, the first age under 1%.

So when the examiner watches a flare decay, she is watching the exact number the allocation controller reads. The demo shows the mechanism instead of describing it — which is what this segment was for.

### The price came from the payload, and it was checked before it was trusted

No server change, no new field, no `src/` touch. And rather than assuming the event payload's weights were authoritative:

```
checked 47325 (edge, t) pairs across 60 frames, mismatches 0
```

The rejected alternative — per-step weight arrays — would have been **~1.7 MB against the current 34 KB**. Fifty times the payload for a number already present.

### The greyscale check justified the design instead of confirming it

```
add        vs reopen        ΔL = 0.0000   -> separated by dash
traffic_up vs traffic_down  ΔL = 0.0178   -> separated by dash
distinct dash patterns: 6/6
```

`add` and `reopen` are **the same colour**. Three pairs would collapse for a greyscale or colour-blind viewer if hue carried the meaning. The check was run to *find out*, not to produce a tick — and it changed the design.

### The mutation that slipped through — third segment running

The specified mutation (collapse `closure` onto `add`) was caught twice. vClaude's own — reverting the state layer to *lit once, lit forever* — was caught by its unit test.

**But the integration test nominally guarding against mud passed it.** Salient edges went 92 → 178 under the mutation, and `salient < 244` still held, because 228 < 244.

> **The threshold was the figure being improved on.**

Tightened to `< 160`, renamed, now catches it. Its own summary is the keeper, verbatim:

> *"A threshold copied from the state you're leaving behind is a memento, not a guard."*

**Third consecutive segment where a test promised more than it checked** — Entry 007's parallel-arrays length check, Entry 008's Mutation B, and now this. The pattern is stable enough to state as a rule:

> **When a test asserts a bound, the bound must come from the property being protected, never from the measurement being replaced.** A number lifted from the old state passes trivially on day one and degrades silently thereafter.

### F11 — `closure` and `delete` are mechanically identical

`events.py:76` — both simply flip the active mask, and `_new_weight` falls through to `return old` for both. The docstring says the labels are retained for faithfulness to the brief.

**Not a defect in the code.** It is a defect waiting in the *report*: "six event types" is true of the vocabulary and false of the mechanism, and an examiner who reads the source will find two names for one operation. **Logged as F11 for Phase 5** — the report says six kinds, five behaviours, and why the distinction was kept.

### Rulings

**R1 — Hue is not the constraint. `§15.5` already spent the channel differently.**

The sharpest question, and the answer is in the architecture doc:

> §15.5 — *"Playback shows **a grid of panes, one per arm**, same graph, same timestep, synchronised. Each pane draws that arm's current best path."*

**The arms do not share a canvas.** Arm identity is carried by *position*, not hue — every pane can draw its path in the same blue, because a pane is unambiguous. Hue is only needed in the excess-over-time strip, which sits on its own ground with no event palette competing. Four categorical line colours in a chart is a solved problem.

So: **do not spend the palette on arms.** Segment 11 needs a pane grid, not four more hues. Recorded now, before it becomes a collision.

**R2 — `palette.json`: widen `STATIC_SUFFIXES` to include `.json`.**

The budget's question is *"has the dashboard become an application?"*, and a growing palette or config file is that growth as surely as a growing script. The code/data line is not where the risk lives. Segment 10, one line.

**R3 — `pytest -q` in every acceptance block is my error.** `addopts` already carries `-q`, so `-q` again means `-qq` and suppresses the summary line — every acceptance block has been asking for output it then hides. **All future blocks say `pytest`.** Small, but it is exactly the class of thing that makes an artefact look verified when it is not.

**R4 — Jump-to-next-event: segment 10.** Two entries old now, and 48 of 60 steps are quiet. It belongs with the playback controls segment 10 is already touching, beside the reset button. Not its own task.

### One process note

vClaude swept the uncommitted Entry 008 into its commit via `git add -A`, noticed, and backed it out — `WORKFLOW_LOG.md` restored as an unstaged working-tree change, md5 verified identical before and after. Confirmed intact from my side.

**The underlying hazard is structural:** the Architect's log edits and the implementer's commits live in one tree, and `git add -A` cannot tell them apart. Noticing is not a control. Segment 10's commit step names the files explicitly instead.

### Close

**347 passed, 0 skipped** — node present, so the JavaScript genuinely ran: **21 assertions**, the first in this project's history. Lint clean. `src/` **2005 / 2100** `+0` (fourth segment). `dashboard/` Python **76 / 1000** `+0`. `static/` **361 / 1200**, projected 520 — under, because the price came from the payload rather than a new endpoint.

The picture now tells the truth about what happened and keeps telling it at `t=59`. Segment 10 hands Rudra the controls.

---

## Entry 010 — Segment 10: Hand Over the Controls (+ an out-of-order design pass)

**Phase** 1 · **Segment** 5 of 7 · **Overall segment** 10
**Verified** 5 Sept 2026 · **Status** COMPLETE
**Commits** `b86c1ba` (segment), then `fb34242`, `a797a54`, `641eb56`, `fc9381d` (design, out of order at Rudra's request)

### Result

`src/` **2005 / 2100**, `+0` — **fifth consecutive segment.** Everything Stages 1 and 2 needed was already public. Python `125 / 1000`. **357 passed, 0 skipped; JS suite 32.**

The ledger holds, against the engine's own count, at every one of 60 steps:

```
t=0    735 + 0  + 0 − 0  − 0  = 735    balances
t=30   735 + 75 + 0 − 0  − 25 = 785    balances
t=59   735 + 75 + 9 − 50 − 25 = 744    balances
```

`|E|` moves **735 → 785 → 744**. The picture was hiding that for three segments.

**R2 was not cosmetic.** Adding `.json` to the static budget moved it **+59 on its own** — `palette.json` was 9% of the budget and invisible to the brake from the day it was created. Third dead-instrument finding in this project (F5, the `*.py` glob, and now this). **The pattern: every measurement instrument in this repo has been wrong at least once, and each was found by someone asking what it actually counts rather than reading its output.**

### The finding of the segment — and it outranks the feature

vClaude's own mutation made the ledger reconcile against its **own arithmetic** instead of the engine's count. The test named for the property **passed**: `assert balances === true` is satisfied by a ledger that can never be false.

Then the obvious repair also failed. Asserting `engineCount === steps[t].n_active_edges` passes on correct data, because there the predicted value *is* that number. It only works when handed data that ought to break it — so it now perturbs a step by `+7`.

> **An invariant test written only against correct data cannot tell a real invariant from a tautology. Both are green.**

**Standing rule, all future segments:** an invariant test must be shown failing against deliberately corrupted input, and the corruption pasted. A green invariant test proves nothing until it has been seen red. This joins Entry 009's threshold rule — the two together are the same lesson from opposite ends: *a test must be anchored to something outside the thing it measures.*

Also worth keeping: mutation A (id ignores `seed`) produced `assert 'efce1e910f78' != 'efce1e910f78'` — **the round-trip test still passed.** Determinism survived; only distinctness broke. Two properties, one test, and only one of them was being checked.

The derived id is **blake2b, not `hash()`** — Python salts `hash()` per process, so the same graph would be renamed on every restart. No cache: a full run rebuilds in **74 ms**, cheaper than the statelessness a cache would spend.

### The design pass, out of order — accepted

Rudra looked at the delivered page and asked for the design work directly. vClaude **flagged the scope breach before doing it** rather than after, which is the correct handling and is why this reads as a decision rather than drift.

Two things came out of it that matter beyond appearance:

- **vClaude can now screenshot the page headlessly** (Chrome, `--screenshot`). It stopped designing blind, and immediately caught truncated dropdowns and a legend swatch for "road removed" that was **invisible** — `#7a2b2e` on `#08090b`. Segment 10 had asked for that fix and it had only widened the line: **the problem was luminance, not weight.** A width change to an invisible colour is a fix that measures as done and reads as nothing. **From here, any visual claim is accompanied by a screenshot vClaude has looked at.**
- **`Cache-Control: no-store` on the dev server.** Two rounds of "the design didn't apply" were a browser reusing cached CSS while the server sent correct bytes. Fixed at the server rather than by telling Rudra to refresh harder.

Labels moved to plain English throughout — `places`, `roads`, `roads per place`, `shortest route`, `Map-based`, `Moderate · every ~3 steps`. **Per D23a the option *values* are untouched**; they key configs and tests. Only what is displayed changed. `|V|` and `|E|` are correct and unreadable.

The control guide was written as prose, rejected by Rudra as unreadable, and rewritten as a reference table with three callouts. Its facts were **checked against source, not assumed** — that the seed feeds both `stream(seed, "graph")` and `stream(seed, "events")`, that `density` is ignored by `grid`, and that a scenario preset changes exactly one number.

### Rulings

**R1 — The static budget splits in two, on the same reasoning that split Python from static.**

At `966 / 1200` with segments 11–13 unwritten, vClaude was right to raise it before segment 11 rather than let it hit the wall mid-flight. But raising 1200 to a bigger number treats a reference table and a pane grid as the same kind of growth, and they are not.

| Budget | Question | Now | Cap |
|---|---|---|---|
| `static/**/*.js` | **Has the dashboard become an application?** | ~413 | **700** |
| `static/` html + css + json | Has its surface sprawled? | ~553 | **900** |

Behaviour is the thing worth bounding tightly; presentation and prose still get a ceiling so they cannot hide growth either, but not the same one. Segment 11 implements the split and reports both opening figures. **The guide does not count against behaviour** — that answers vClaude's question directly.

**R2 — "Runs on disk": drop it.** vClaude's argument is accepted. With the D32 banner gone it is a bare `exploratory: 9240` with nothing to click, answering a question nobody in front of this page is asking. It earns its place back when the dashboard can load a run — Phase 4. Four lines to restore.

**R3 — Segment 13 survives but is re-scoped.** Most of its content shipped early. What remains: a final pass once the pane grid and inspect panels exist, and **a decision then** on whether the sidebar layout is still needed — it was drawn when the page was ugly and the stacked layout now reads well. It may be dropped entirely; that is a judgement to make with 11 and 12 on screen, not now.

**R4 — Rudra committed mid-segment** (`c525489`), sweeping `dashboard/server.py` in beside Architect edits to `ARCHITECTURE.md` and the spec. Nothing lost; segment 10's work is split across two commits. vClaude correctly left his history alone. **Convention: no commits from any party while a segment is in flight** — the tree has three writers and only one commit discipline.

### Close

Phase 1 is **5 of 7**. `src/` untouched for five segments running, which is now itself evidence: §2.3 claimed the core exposes what the dashboard needs, and five segments have failed to falsify it.

Segment 11 races the arms. It is the largest remaining segment and the first time the project's actual optimizers appear on screen.

---

## Entry 011 — Segment 11: Race the Arms

**Phase** 1 · **Segment** 6 of 7 · **Overall segment** 11
**Verified** 5 Sept 2026 · **Status** COMPLETE — **uncommitted, handed to Rudra**

**First segment under the new rule: vClaude does not commit.** It left the tree unstaged, pasted `git status --short` and the message, and touched neither `AGENT_PROTOCOL.md` nor `WORKFLOW_LOG.md`. Clean handover on the first attempt.

### What landed

The optimizers are on screen. Four panes, one per arm, position carrying identity so the event palette is not spent on arms. Excess over time from `analysis.per_trial_excess` rather than recomputed. A whole race is **1.8 s**, so no streaming machinery was needed. Pending states on every button; the page opens empty instead of auto-generating a world.

Two unprompted colour corrections worth recording, because both were found by *checking* rather than by taste: the first arm palette left a **greyscale gap of 0.033 between ACO and Hybrid** — invisible to a colour-blind viewer in the one chart the project's claims are read from — respread to **0.197**; and disruption markers moved off amber, which was competing with PSO's orange on the same ground.

### R1 — The test suite is writing into the evidence tree. Stop it. **This is the entry's most serious item.**

**25 run directories under `outputs/2026-09-05/`**, all created today by tests, because every Stage 3 test executes a real trial. Confirmed from disk.

Worse: a corruption demo stamped one of them `manifest`, and **it landed in the live tree**, where `test_run_classes_does_not_filter_to_manifest` correctly reported D31's invariant violated.

Read that consequence plainly. `run_class` exists so that **scratch runs can never silently become evidence**. A test harness that can write a `manifest` run into `outputs/` is a hole straight through that guarantee — not a tidiness problem. The one system built specifically to prevent fabricated evidence was, for one afternoon, reachable by a test fixture.

**And it is the provenance system that caught it.** A red test naming the violation is exactly the behaviour Phase 0 paid for. The system worked; the containment did not exist.

**Ruled, three parts:**

1. **No test may write into `outputs/`.** Ever. The run root becomes a parameter; tests pass `tmp_path`. If threading that through needs something `src/` does not expose, **stop and report** — this one is worth a core change if it needs one.
2. **A test asserting the suite creates nothing under `outputs/`.** The rule enforced rather than remembered — otherwise it survives exactly as long as the person who remembers it.
3. **Deleting today's 25 directories is authorised**, and vClaude was right to refuse: the guardrail says never touch `outputs/` and does not exempt litter it made itself. **Refusing to clean up its own mess, because the rule did not carve out an exception for it, is the correct reading of a guardrail.** Rudra deletes `outputs/2026-09-05/` by hand.

Segment 12, first task.

### R2 — A guarantee about failure cannot be tested by data in which nothing fails

vClaude's uncommissioned mutation made `reaches` always true, so **a broken route could never render as broken**. Nothing caught it — not Python, not JS.

§15.5 names this requirement explicitly: *"a path failing to reach the goal shows up instantly, in whichever arm."* It had no test, because `preserve_connectivity` means no arm fails in any run currently obtainable.

Its own summary, verbatim, because it generalises past this case:

> **"A guarantee about failure can't be tested by data in which nothing fails."**

**Third instance of one family** — Entry 009's threshold copied from the state being replaced, Entry 010's invariant asserted only against correct data, and now a guarantee exercised only by data that never triggers it. Stated once, for all of them:

> **A test is only as good as the worst input it is ever shown. If the failing case cannot arise from real data, it must be constructed.**

**Ruled:** segment 12 adds a **synthetic broken-route fixture** — a constructed run where an arm's path stops short — and asserts it renders as broken rather than as a short line. Not deferrable: ACO and PSO genuinely can fail to complete a route in early iterations, so this can happen live, in front of an examiner, and would currently look like a slightly shorter path.

### R3 — `run_experiment` instead of `run_trial`: accepted, and **the constraint was mine and was wrong**

vClaude called `run_experiment` — the function `cli.py` calls, which calls `run_trial` per trial and streams through `ResultWriter`. Going direct to `run_trial` would have meant writing the parquet by hand, **which is the second-harness risk moved down a layer** rather than avoided.

§15.2's intent is *"the same door the CLI uses; do not build a second harness."* `run_experiment` **is** that door; `run_trial` is a layer inside it. The letter of my constraint pointed at the wrong function, and following it literally would have produced exactly the defect the constraint exists to prevent.

**vClaude read the intent, took it, and flagged the letter.** That is the right order, and it is the second time this project has been saved by an implementer declining to follow a spec into a wall.

`ARCHITECTURE.md` §15.2 is amended: **"drives runs through the CLI's own entry point (`run_experiment`, which calls `run_trial`), never a loop of its own."**

### Close

**364 passed, 1 failed** — and the failure is the correct behaviour of a guardrail, not a defect. It clears when `outputs/2026-09-05/` is removed.

Phase 1 is **6 of 7**. `src/` untouched for six segments. Segment 12 opens with R1 and R2 before anything new is built.

---

## Entry 012 — Segment 12: Inspect — **PHASE 1 CLOSED**

**Phase** 1 · **Segment** 7 of 7 · **Overall segment** 12
**Verified** 6 Sept 2026 · **Status** COMPLETE — uncommitted, handed to Rudra

### R1 — The JS cap: raised to **900**. And the cap was my error, of the exact kind this project keeps cataloguing.

**702 / 700. vClaude refused to shave two lines, and that refusal is the correct answer.**

Two lines of "tightening" would have bought a green suite and taught that the cap is a formality. A brake whose whole purpose is to be *felt* cannot be quietly stepped around by the agent it is meant to constrain. **Stopping and reporting was right, and would have been right at 701.**

Now the part that matters more:

> I set 700 in Entry 010 **from a 414-line file**, before anyone knew what inspect would cost.

That is **precisely** Entry 009's defect, committed by me. vClaude's anti-mud test asserted `< 244` — the number it was improving on — and I ruled then:

> *"A threshold copied from the state you're leaving behind is a memento, not a guard."*

700 was a memento. It was lifted from where the file happened to be, not derived from what the dashboard should be allowed to become. **Three segments after writing that rule, I broke it in the same repository.** Knowing a rule is not the same as not breaking it — which is why the mutation step exists, and apparently why the log does too.

**Raised on D28's terms — measured, argued, recorded**, and this time *derived*:

| | |
|---|---|
| Phase 1 dashboard, complete | **702** |
| Phase 3's allocation view — the one substantial JS build left | ~**120**, the size of the excess chart it most resembles |
| A demo affordance, plus slack for Phase 2's probe panels | ~**80** |
| **JS cap** | **900** |

Presentation stays at **900** (≈653 used).

**vClaude's observation that the split "binds hard on one side and slack on the other" is itself the finding**, and it is the split working exactly as designed: it says, in one number, that this dashboard's growth is **behavioural**, not decorative. A single combined budget would have shown comfortable headroom and told us nothing.

Segment 13 implements the new cap and **reports the excess chart's real line count**, so 900 is checked against evidence rather than resting on my estimate.

### R2 — No sidebar. Segment 13 re-scoped to vClaude's proposal.

I drew that sidebar when the page was ugly, and said the decision would be made with 11 and 12 on screen. They are, and vClaude has looked at this page longer than either of us:

> *"The stacked layout is why the page survived having panes, a chart and inspect panels added to it — every band is one idea. What made it readable was dropping layers from the panes and separating the state and event channels, not the layout."*

**Accepted, and the reasoning is the valuable part:** the legibility was bought by *reducing what each band carries*, not by rearranging bands. A sidebar would have moved the problem, not solved it — and the fix that actually worked would have been credited to the wrong thing.

**Segment 13 is now: the raised cap, and a single "run the demo" affordance** — one control that walks the page through the whole story in front of an examiner. **Nothing on the main canvas; it is full.**

### The allocation gap was measured, not merely accepted

I ruled the allocation bar out on the argument that F7 leaves the controller inert. vClaude did not take the ruling on trust — it measured:

> **The uncontrolled hybrid holds `aco_fraction` at 0.5 for all 60 steps.**

So a bar built today would be **a flat line at fifty percent, presented as the project's novelty.** Not a subtly wrong widget — a completely static one, captioned as the thing that moves. **And a test now fails the moment it starts moving**, which turns the gap from a note into a tripwire: the day the control layer works, the suite says so.

That is the difference between accepting a ruling and confirming it. Same conclusion, evidence underneath.

### Mutation B — fourth segment running

The selection marker drew at `xy[0]` whatever was clicked. **The panel stayed correct; the highlight pointed elsewhere.** All 42 JS tests and the entire Python suite passed.

Segment 8's failure exactly — **the picture disagreeing with the caption** — relocated into the selection layer. Now covered, and shown red.

**Four consecutive segments in which the uncommissioned mutation found the real defect and the commissioned one confirmed a prediction.** That is no longer a pattern, it is the method: *the Architect's mutation tests the spec; the implementer's tests the code.*

### A repeated mistake, owned

The "no unrecorded field" test grepped `app.js` for `pheromone` and failed on **its own comment explaining why the field is absent** — identical to segment 9's `schedule[` grep hitting a docstring. Comments are stripped now.

Worth keeping because it is small and instructive: **a grep over source is a search over prose as well as code**, and this repository documents heavily by design. Any future source-scanning test strips comments first.

### What shipped

- **Containment holds.** Run root is a parameter, every test passes `tmp_path`, and **no `src/` change was needed** — `run_experiment` already took a directory. A session fixture in `tests/conftest.py` fails the run if anything appears under `outputs/`. **17 run directories before a full suite, 17 after.**
- **A synthetic broken run**, built from a real race and then truncated, so every field except the one under test is what the engine produced. The failing case had to be constructed because `preserve_connectivity` means none arises.
- **Edge inspect:** price now and at `t=0`, open or closed, original or pool road, full event history from the steps' own event lists. **Node inspect:** live degree, position, role, which arms route through it.
- **Hit-target policy:** nearest-within-radius, tie-break **lowest index wins**, stated and tested — the minimum edge length is sub-pixel, so a tie is not hypothetical.
- **Pheromone and PSO priority are absent, deliberately.** `probe` carries colony- and swarm-level aggregates only; the per-edge and per-node probes are Layer 2, which §17 assigns to Phase 2. **A test pins the absence**, so the panels get extended deliberately when those land rather than filled with something plausible.

`43` JS tests, `45` dashboard tests, one red — the budget, correctly.

---

## PHASE 1 CLOSED

Seven segments. `src/` **2005 / 2100**, `+0` **in every one of them** — §2.3 claimed the core already exposes what a view needs, and seven segments failed to falsify it.

What exists now: Rudra builds a world, designs how it breaks, races three optimizers against A\*'s truth, scrubs through sixty steps, and clicks into any edge, node or arm — with every number on screen traceable to the engine that produced it, and every gap labelled as a gap.

**Five rules came out of this phase, and they are the transferable part:**

1. **Observe the effect, not the call** — how I2 caught F1
2. **Read the output; do not trust the setup** — the fixture and the demo that were wrong first
3. **A threshold must come from the property protected, never the measurement replaced** — and I broke this myself three segments later
4. **An invariant test written only against correct data cannot tell an invariant from a tautology**
5. **A guarantee about failure cannot be tested by data in which nothing fails**

The last three are one idea from three directions: **a test is only as good as the worst input it is ever shown.**

Segment 13 is a short close-out. Then Phase 2 — trust it.

---

## Entry 013 — Segment 13: Ship It — **PHASE 1 COMPLETE**

**Phase** 1 · **Segment** 8 of 8 · **Overall segment** 13
**Verified** 9 Sept 2026 · **Status** COMPLETE — uncommitted at hand-over

### The cap: raised to 900, and the derivation did not survive its own check

That is the entry's finding, and it is about method rather than the number.

I raised the cap on the argument that a derived number beats a picked one, and priced Phase 3's allocation view at **~120 lines, "the size of the excess chart it most resembles."** vClaude measured:

```
drawExcess       36     <- the excess chart, priced at ~120
drawPanes        34
inspectEdge      27
drawArmPanel     24
drawLedger       21
inspectNode      18
```

**3.3× out, and nothing on the page exceeds 36.** On the same benchmark the allocation view is ~40, so the honest arithmetic is `702 + ~40 + ~80 ≈ 820`. The demo affordance came in at **11 lines against ~80 budgeted** — the same estimate running high a second time, independently.

**900 stands.** It errs in the safe direction and Entry 012 demonstrated the cost of the other error. What matters is the correction to the *reasoning*:

> **"Derived, not picked" only beats "picked" if the derivation is checkable.** This one was checked and came back 3× out.

So the cap now carries ~80 lines more headroom than its own justification intended — a fact to hold at the next raise, not a thing to correct now. vClaude proposing no change while reporting the discrepancy is the right handling: **the number was fine and the argument for it was not, and those are separate things.**

Closing: JS **734 / 900**, presentation **667 / 900**.

### T4 shipped reading "graph undefined" — and only the screenshot caught it

`read_run` returned no `graph_id`. The template interpolated the gap and rendered the word. **Every test passed.** Green suite, correct panes, and directly beneath them a line reading `graph undefined` — which would have gone in front of an examiner.

> **A caption that renders a missing value as a word is worse than one that fails, because it looks like information.**

**Second time the standing screenshot rule has paid for itself** — the first was `delete` being invisible in segment 10, where a width change to an unreadable colour measured as done and showed as nothing. Both defects were invisible to the suite and obvious to an eye. The rule stays.

The fix is the interesting part: `graph_id` now comes from the manifest **the run recorded**, not from the form. So editing the world after racing leaves the line naming the graph the arms actually ran on, and the two **visibly disagree** rather than silently agreeing. That is what makes it evidence rather than a caption — and it is why T4 was specified as a statement rather than a check. Pinned by two tests, both shown red.

### The panes now carry a number a viewer can check

```
All 4 panes show timestep 21 of one timeline, frozen before any algorithm ran
— seed 1000, graph 1e06d1c7b60e, 760 roads open.

  A*                 110.54 · 12 hops    +0.0%
  ACO standalone     113.80 · 11 hops    +3.0%
  PSO standalone     155.96 · 17 hops   +41.1%
  Hybrid (baseline)  111.57 · 13 hops    +0.9%
```

A\*'s **110.54 is the headline optimum to the digit**, asserted at *every* timestep rather than sampled.

`cost` and `hops` are the run's own `best_cost` and `path_len` columns — and the test deliberately **does not** assert that `hops` equals the drawn route's segment count, because the run makes no such claim and asserting it would invent a relationship nobody measured. That restraint is worth recording; it is the same discipline as refusing to show pheromone in segment 12.

Space was not the problem I anticipated: three figures fit at quarter size by going on two lines, no type shrunk.

### A correction to vClaude's own mutation method

Its first attempt at mutation A reassigned a `const`, so it **threw** rather than producing the silent wrong-pairing it meant to demonstrate — and tripped three unrelated tests, which *reads* like a strong catch and is nothing of the kind.

Caught and redone so the mutation is silent and the failure is the one claimed. **A mutation that crashes tests the interpreter, not the suite** — the same lesson as Entry 005's demo that was wrong first, in a new place.

### Demo readiness — the honest read

Asked whether the page is ready for an examiner, vClaude said yes, with a caveat about the room rather than the page:

> **The demo is over in about eight seconds.** Five moments at 1.4 s each — the right length for attention, the wrong length for someone who has never seen it. They will not know where to look before it has moved on.

**Practical instruction for Rudra: press the demo once to show the shape, then scrub to `t=21` and talk over it.** That is a better piece of advice than any code change would have been.

### The one thing left undone, named clearly

> *"The main canvas at a heavy disruption step. Every other band was made legible by reducing what it carries; the canvas never got that treatment, because every segment had a reason to add to it and none had a reason to take something off."*

**Recorded as the standing recommendation for Phase 5's demo preparation, not as a defect.** It is a design debt with a known shape and a known fix — spend a segment deciding what comes *off* — and it is worth carrying forward precisely because no segment will ever raise it on its own. Every future task will have a reason to add.

---

## PHASE 1 COMPLETE

**Eight segments. `src/` unmoved at `2005 / 2100` in every one of them.** §2.3 asserted the core would already expose what a view needs; eight consecutive segments failed to falsify it, which is now the strongest structural claim this project can make about its own architecture.

Final: **367 Python tests, 50 JavaScript tests, 0 skipped.** `dashboard/` Python **177 / 1000**, JS **734 / 900**, presentation **667 / 900**. `outputs/` unchanged by the suite — 24 before, 24 after.

**What exists:** Rudra builds a world, designs how it breaks, races three optimizers against A\*'s truth, scrubs sixty steps, clicks into any edge, node or arm, and presses one button that walks the whole story. Every number traceable to the engine that produced it. Every gap labelled as a gap — including the allocation view, which is an honest empty slot because the controller behind it is known not to work.

**The transferable result — five consecutive segments, now stated as a finding rather than an observation:**

> **The uncommissioned mutation found the real defect five times running** — the panes, the ledger, the broken-route styling, the selection marker, and the shared line. **The commissioned one confirmed a prediction every time.**
>
> A spec can only mutate what its author already imagined going wrong. **The defect that matters is by construction the one nobody thought to ask for.**

That is not a habit to carry into Phase 2. It is the reason Phase 2 exists.

**Next: Phase 2 — trust it.** Every mechanism proven live or reported inert.
