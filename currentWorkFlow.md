# SEGMENT 1 — Documentation Truth Pass

**Phase 0 · Ground truth · Segment 1 of 2**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` and `decisionLedger.md` before starting.
> Append your findings to the **bottom** of this file using the §6 template. Do not modify the spec text above it.

---

## Goal

Make the repository's three main documents tell the truth. **No code changes at all.**

Every result number currently in `README.md`, `RUNBOOK.md` and `DOCUMENTATION.md` is either superseded, unverifiable, or both. None of them can be checked against a result file on this machine. Meanwhile the project is committed to regenerating every number from scratch at ≥100 trials (D5, D9).

Until that happens, the honest state is: **these numbers are provisional, and here is why.** Not deleted, not replaced with other unverifiable numbers — marked.

## Why this segment, and why first

Two reasons.

**It is the highest-risk-lowest-effort item in the project.** `DOCUMENTATION.md` quotes figures from a predecessor codebase whose own paper contains fabricated results. If any of those reach the report, that is an academic integrity problem rather than an untidiness problem.

**It is the safest possible first test of the protocol.** No code, no tests, no schema. If the segment cycle has a flaw, this is where it should surface.

---

## Scope

### In scope — exactly three files

- `README.md`
- `RUNBOOK.md`
- `DOCUMENTATION.md`

### Explicitly out of scope

- **Anything under `src/`, `tests/`, `conf/`, `scripts/`.** Not one line.
- `outputs/` — do not touch, do not delete, do not regenerate
- `WORKFLOW_LOG.md` — do **not** create it. The Architect creates it when this segment is verified
- The three known defects F1/F2/F3 — do not fix, do not touch
- `AGENT_PROTOCOL.md`, `ARCHITECTURE.md`, `decisionLedger.md` — read-only for you

---

## Tasks

### T1 — `README.md`

**T1.1 — Mark every result table as provisional.** Every table of measured results gets a short marker directly above it, in this form:

> **Provisional.** These figures come from runs not present in this repository and cannot be verified here. They are superseded by the regeneration programme in `ARCHITECTURE.md` §13, which reports at ≥100 trials. Do not cite them.

Do **not** delete the tables — they are the project's history and the starting point for comparison. Do **not** substitute numbers from any other source.

**T1.2 — Correct the test counts.** The README's figure is wrong. The real state, from `results_junit.xml` and confirmable by running the suite: **276 collected · 5 slow · 271 not-slow · all passing.**

**T1.3 — Correct the milestone table.** The status table lists `M7 · allocation experiment 🔬 ready to run`. That is no longer true: it was run once, on two scenarios, at 30 trials, with untuned parameters, on a signal misaligned by F1. Replace with an accurate status and a one-line note. Review every other row for the same problem and correct what is wrong; leave what is right.

**T1.4 — Add a pointer** near the top to `ARCHITECTURE.md` as the current design of record.

### T2 — `RUNBOOK.md`

**T2.1 — "Four more are marked `slow`" is wrong.** It is five.

**T2.2 — The per-file test count table does not match a real run.** Correct it against `results_junit.xml`, which records the counts as collected:

```
test_hygiene 75 · test_optimizers 40 · test_control 30 · test_environment 26
test_hybrid 25 · test_config 20 · test_harness 20 · test_analysis 17
test_tuning 11 · test_rng 8 · test_testbed 4          (276 total)
```

If your own run disagrees with these, **report the discrepancy rather than picking one** — it would mean the suite has changed since 8 Aug and the Architect needs to know.

**T2.3 — Mark the "current standing" figures provisional**, same wording as T1.1.

**T2.4 — Add a note to the experiments section** stating that the E1–E7 sequence is superseded by the experiment manifest in `ARCHITECTURE.md` §13, and that the RUNBOOK's commands remain valid as ad-hoc invocations but no longer define the reported programme.

### T3 — `DOCUMENTATION.md`

The largest and most contaminated document. Four targets, and they need **different** treatment — read this carefully rather than applying one rule.

**T3.1 — §19.1 "The 400-Trial Study (Legacy DPO, July 2026)".**
Legacy, from a codebase outside this repository, with no result files anywhere. These are probably genuine measurements rather than fabrications — but they came from a codebase with a known-broken benchmark runner, and nothing here can verify them.

Keep the section. Retitle it to make its status unmissable, and place directly beneath the heading:

> **Legacy and unverifiable — not evidence.** Produced by a predecessor codebase that is not part of this project and is not present in this repository. No result files exist for these figures. They are retained as project history only. Never cite them, and never carry a number from this section into a report, figure or presentation.

**T3.2 — §19.2 "Current Standing (Dynaswarm v2, 10 trials)".**
Different case. These *are* from this codebase — but at 10 trials, superseded by later 30-trial runs, and being regenerated at ≥100. Use the T1.1 provisional marker, not the legacy one. **Do not conflate the two.**

**T3.3 — §20 "Known Bugs & Limitations (Legacy DPO)".**
**Do not weaken or remove this section.** The bug history — a benchmark that ran on the pre-mutation graph, a budget split written but never read, a trigger that fired zero times — is precisely what justifies this project's entire design philosophy, and it is a report asset.

It needs only a framing line clarifying that it describes a **predecessor codebase, retired, outside this repository** — not the current system's state.

**T3.4 — §20.3 "Paper Numbers ≠ Measured Results".**
This section already flags the discrepancy internally. **Strengthen the existing caveat rather than adding a competing one.** Make explicit that those numbers appear in no generated result file, that the affected files are outside this repository, and that nothing from them may enter any deliverable.

**T3.5 — Correct the test count** where §1 states it.

**T3.6 — Clarify the two-codebase framing.** §1 currently presents "DPO_Minor_project — the legacy codebase" as though it were part of this project's scale. State plainly that it is a **separate, retired project, outside this repository**, retained only as history.

---

## Constraints

| | |
|---|---|
| **Never invent a number** | Not one figure may be added, adjusted, recomputed or estimated. This segment marks numbers; it does not produce them |
| **Never substitute one unverifiable number for another** | Do not replace README figures with the presentation deck's figures. Neither can be verified here |
| **Never delete a results table or the bug history** | They are history and report material. Marking is the whole job |
| **No code, no tests, no config** | `git diff --stat` must show exactly three files |
| **Do not fix F1/F2/F3** | However tempting while reading |
| **Preserve document structure** | No renumbered sections, no reordering, no reformatting beyond the additions |

If a task turns out to be wrong or impossible as written, **report it rather than improvising**. If you find a fourth contaminated section not listed here, **report it — do not fix it** in this segment.

---

## Acceptance check

Run all four and paste the actual output.

```bash
# 1. Exactly three files changed, nothing else
git diff --stat

# 2. The suite is untouched and green — proves no code was modified
./.venv/bin/pytest -q -m "not slow"

# 3. Lint clean
./.venv/bin/ruff check src/ tests/

# 4. Every stale test-count claim is gone
grep -rn "271 tests\|four are marked\|Four more are marked" README.md RUNBOOK.md DOCUMENTATION.md
```

**Expected:**

1. Exactly three files: `README.md`, `RUNBOOK.md`, `DOCUMENTATION.md`
2. 271 passed
3. No findings
4. **No output** — every stale claim corrected

Then paste, verbatim:

- The new heading and caveat block for `DOCUMENTATION.md` §19.1
- The new heading and caveat block for `DOCUMENTATION.md` §19.2
- The corrected `README.md` milestone row for M7

---

## Definition of done

All four acceptance commands produce the expected output, the three verbatim blocks are pasted, and the FINDINGS block is appended below.

**Do not start segment 2.** Stop and wait for the Architect's verification.

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->

## FINDINGS — Segment 1

**Status:** COMPLETE

**Files changed**
- `README.md` — 8 provisional markers above measured-result tables; M7 milestone row corrected with an explanatory note; M10/M11 rows annotated; `ARCHITECTURE.md` pointer added near the top
- `RUNBOOK.md` — test counts corrected (2 places); per-file table replaced with verified counts; provisional markers on the current-standing figures and the sigma-span table; supersession note on the experiments section
- `DOCUMENTATION.md` — §1 scale block reframed and test count corrected; §18 test count and per-file table corrected; §19.1 retitled + legacy caveat; §19.2 retitled + provisional caveat; §20 framing line; §20.3 caveat strengthened

**Files added**
- None. This segment adds no files.

**Tests added**
- None. No code was touched, by design.

**Test suite**
Command: `./.venv/bin/pytest -m "not slow"`
Result:
```
271 passed, 5 deselected in 31.73s
```

**Lint**
Command: `./.venv/bin/ruff check src/ tests/`
Result:
```
All checks passed!
```

**Acceptance check**

1. `git diff --stat`
```
 DOCUMENTATION.md | 60 ++++++++++++++++++++++++++++++++++++++++----------------
 README.md        | 26 +++++++++++++++++++++---
 RUNBOOK.md       | 34 +++++++++++++++++++++-----------
 3 files changed, 89 insertions(+), 31 deletions(-)
```
Exactly three files. `git status --short` additionally shows only the four untracked documents the Architect created (`AGENT_PROTOCOL.md`, `ARCHITECTURE.md`, `currentWorkFlow.md`, `decisionLedger.md`) — nothing of mine.

2. `./.venv/bin/pytest -q -m "not slow"` → `271 passed, 5 deselected in 31.73s`

3. `./.venv/bin/ruff check src/ tests/` → `All checks passed!`

4. `grep -rn "271 tests\|four are marked\|Four more are marked" README.md RUNBOOK.md DOCUMENTATION.md` → **no output** (grep exit 1).

**Verbatim blocks requested by the spec**

`DOCUMENTATION.md` §19.1 heading and caveat:
```markdown
### 19.1 The 400-Trial Study — LEGACY AND UNVERIFIABLE, NOT EVIDENCE (Legacy DPO, July 2026)

> **Legacy and unverifiable — not evidence.** Produced by a predecessor codebase that is not part of this project and is not present in this repository. No result files exist for these figures. They are retained as project history only. Never cite them, and never carry a number from this section into a report, figure or presentation.
```

`DOCUMENTATION.md` §19.2 heading and caveat:
```markdown
### 19.2 Current Standing — PROVISIONAL (Dynaswarm v2, 10 trials)

> **Provisional.** These figures come from runs not present in this repository and cannot be verified here. They are superseded by the regeneration programme in `ARCHITECTURE.md` §13, which reports at ≥100 trials. Do not cite them.

Unlike §19.1, these figures were produced by *this* codebase — they are superseded, not legacy.
```

`README.md` corrected M7 row (plus the note placed under the table):
```markdown
| M7 · **allocation experiment** | ⚠️ run once, result void — must be re-run |
```
```markdown
**M7.** It was run once — two scenarios, 30 trials, untuned parameters — on a signal misaligned by defect F1, which made `RecencySignal` fire one timestep early. That result is a void rather than a negative finding, and the experiment is re-run after F1 is fixed. See `decisionLedger.md` §4 and `ARCHITECTURE.md` §13 (E4).
```

**Deviations from spec**

1. **T1.2 has no target in `README.md`.** The spec states "The README's figure is wrong," but `README.md` contains **no test-count claim at all** — `grep -in "test" README.md` returns only prose about testing, never a count. I made no change to README for T1.2 rather than inventing a place to put one. The stale counts actually lived in `RUNBOOK.md:27`, `RUNBOOK.md:38`, `DOCUMENTATION.md:19` and `DOCUMENTATION.md:1201`, all now corrected.

2. **T3.5 named §1 only; I also corrected §18 (was line 1201).** That line read "271 tests, ~60 seconds. Four `slow` tests…" and its per-file table carried the same stale numbers as the RUNBOOK's. Acceptance check 4 greps all three files for `271 tests`, so leaving §18 alone would have failed the check. Corrected both, and both per-file tables now match the verified counts.

3. **T2.3 extended to one additional table.** The spec names "the current standing figures". I also marked the **sigma-span table** in E4 (`0.002 | 0.468 → 0.500` etc.), which is the only other table of measured results in `RUNBOOK.md`. Marking the prose figures but leaving a results table unmarked seemed the wrong reading of the segment's purpose. Flagging it because it is an extension, not a literal instruction — trivially revertible if unwanted.

4. **T1.3 — I annotated M10 and M11 rather than changing their status.** The spec asks me to review every row and correct what is wrong. M9 (`🔬 ready to run`) is still accurate — the scale study has not been run. M10 (Pygame replay ✅) and M11 (documentation ✅) are both *true today* but misleading, so I added short annotations (retirement under D17; the new provisional markers) instead of altering the ✅. If the Architect prefers untouched rows, both annotations are one-line reverts.

**Surprises**

1. **The README's stated thesis is the superseded one — reported, not fixed.** Line 3 subtitles the project "**Volatility-driven** compute allocation", and the Thesis block states the allocation "should be driven by measured environmental volatility." Per `ARCHITECTURE.md` §1.3 the current thesis is allocation driven by **recency**, not volatility — and §1.3 Claim 2 is precisely the finding that volatility cannot drive it. So the README's headline sentence asserts the thing the project disproved. This is a fifth contaminated area, outside this segment's four tasks; per the spec I am **reporting it, not fixing it**. It is more consequential than any of the numbers I marked, because it is the first sentence a reader sees.

2. **The marker volume in `README.md` is high.** Eight blockquotes in a document of ~220 lines is heavy, and consecutive tables (the adaptation table and the cross-evaluation matrix are six lines apart) now carry near-adjacent identical markers. I applied the spec literally. If it reads badly, a single prominent banner near the top plus short inline pointers would carry the same warning with less repetition — the Architect's call.

3. **`test_hygiene.py` is 75 collected tests, not 3.** Every previous document said 3. It is parametrised across every source file, so retiring `viz/replay.py` and adding `allocation/` will move this number. The same applies to `test_optimizers.py` (40, parametrised off `PARAM_SPEC`) — adding a parameter changes the count. Worth knowing before Phase 3, since these tables will go stale again automatically.

4. **`README.md` §Layout is stale in two ways** (reported, not fixed, out of scope): it lists a `core/schedule` module that does not exist — that logic lives in `core/timeline.py` — and `analysis/` omits `recovery.py`. Also `RUNBOOK.md:15` gives a clone URL for a teammate's GitHub repository, which may or may not be where this project should now point.

**Could not do**

Nothing was blocked. Every task in scope was completed except T1.2, which had no target to act on (see Deviations 1).

**Questions for the Architect**

1. **The superseded thesis statement in `README.md`** (Surprise 1) — do you want a segment for it, or is it folded into a later documentation pass? It is currently the most misleading sentence in the repository.
2. **Marker density** (Surprise 2) — keep the literal eight, or consolidate to one banner plus pointers?
3. **T2.3 extension and the M10/M11 annotations** (Deviations 3 and 4) — keep or revert?
4. **`RUNBOOK.md:15` clone URL** — should it still point at `github.com/VaibhavBansal05/Dynaswarm.git`?
