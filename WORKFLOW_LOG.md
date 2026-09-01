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
