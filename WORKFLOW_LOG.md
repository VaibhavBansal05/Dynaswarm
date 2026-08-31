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
