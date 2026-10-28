# Dynaswarm — state of the project

**Updated 20 September 2026.** One page. For anyone picking this up — a new session, a collaborator, or Rudra after a gap.

The authoritative records are `WORKFLOW_LOG.md` (the narrative, 34 entries) and `FINDINGS_TESTS.md` (every result). This file is the map to them.

---

## Where we are

**The research is finished.** Nothing needs re-running. The next action is a conversation with Rudra's professor, and it gates the report.

| Phase | State |
|---|---|
| 1 — See it (dashboard) | ✅ segments 6–13 |
| 2 — Trust it (verification) | ✅ segments 14–19 |
| 3 — Restructure the control layer | ✅ segments 20–21 |
| X / Y / Z / Z2 / Z3 — sigma, policy shapes, metrics | ✅ |
| 22 — Rudra's manual verification pass | ✅ |
| 23 — the manifest, frozen | ✅ |
| 24 — the evidence run + pre-registered analysis | ✅ |
| 25 — the promised analyses + four defects | ✅ committed `a1e83c6` |
| **— professor conversation** | **← next. Blocks everything below.** |
| 26 — report · 27 — deck · 28 — viva prep | blocked |

**Health:** 543 Python tests, 53 JS, ruff clean. `src/` 2318 statements, unchanged since segment 22 — segments 23–25 added only `scripts/` and `tests/`.

---

## The run

`outputs/2026-09-19/18-43-05` · commit `b4d3d28` · `dirty: false`

1,200 trials = 150 seeds × 4 scenarios × 10 arms × 2 tiers. 720,000 step rows across 24 chunks. 216 minutes at 8 parallel jobs.

**Verified reproducible.** Re-running the analyser over the same folder with corrected code produced byte-identical output for all 85 grid rows and all 72 ranking rows. Only a banner and two Pareto lines changed.

---

## The results

**Claim 1 — the hybrid beats its own components. Supported.**
`hybrid` vs `pso` significant in all four scenarios at both tiers. `hybrid` vs `aco` significant in all four at `large1000` (δ ≈ −0.99, p_adj 7.8e-25) but **only 1 of 4 at `medium200`** — the tier every calibration in this project was performed at. **That scope qualification must survive into the report.**

**Claim 2 — adapting a parameter does not help. Reproduced, weakly.**
P4 not significant in any of 8 cells. But the bound is **1.07 percentage points** — about a third of total excess, and 18× the ceiling this run places on sensing. It is a *non-detection*, not a demonstrated absence. **Never state it without the bound** (Entry 034).

**Claim 3 — allocation as the better-posed question. A null, with a mechanism.**
No sensing arm beats `hybrid_fixed`. At `severe` both lose to `hybrid_scheduled` — the blind timetable — by δ +0.100 and +0.080: significant, negligible in size. The disadvantage grows monotonically with disruption rate (+0.063 → +0.082 → +0.100). The null survives the bridge split (0 of 19 cells significant on either half) and both tiers agree.

**Why the null happened.**
`AllocationObservation` carries `events_this_step: int` — the damage count. Both sensing policies read only `obs.recency`, which is 1.0 on any disruption step regardless of magnitude. **The run tested allocation driven by disruption *recency*, not allocation proportional to *magnitude*, which is what the thesis specifies.**

`policies.py` documents the exclusion as *"recency is already the decayed form of both"*. That is false: `recency` encodes *when*, not *how many*.

History (verified in segment 25): the policy is `aa3c3c5` (segment 20); the justifying line is `4e4b6ad`, six days later, produced by segment 21's T5 documentation task. **The exclusion came first and the reason was written afterwards to describe it.** This changes what was tested, not whether the test was sound.

---

## The single reference document

**`FINDINGS_TESTS.md` — 527 lines.** Every section opens in plain English, carries the command that produced it, and is tagged `[raw]`, meaning re-derived from the 720,000 parquet rows in segment 25. §0 defines all ten arms, the four scenarios, both tiers and the nine comparison codes for a reader new to the project.

**The report is written from it. `outputs/` is never reopened.** That was the purpose of segment 25.

| Source | For |
|---|---|
| `FINDINGS_TESTS.md` | every number |
| `WORKFLOW_LOG.md` Entry 024 | the pre-registration + three dated amendments |
| `ARCHITECTURE.md` | design — §7 observation, §9 arms, §10.2 fairness, §12 provenance |
| `understandingTests.md` | design justification — ⚠️ written pre-results, needs a pass first |
| `WALKTHROUGH.md` | system description and the live demo |
| `MANIFEST.json`, `provenance.json` | reproducibility — 150 seeds listed, commit, platform |
| `WORKFLOW_LOG.md` Entries 028–034 | limitations, and what was caught |

---

## The protocol

The Architect (a Claude session) **never edits code.** It writes one segment spec into `currentWorkFlow.md`; Rudra pastes a one-liner to vClaude in VS Code; vClaude implements and appends a FINDINGS block **to that file before reporting in chat**; the Architect verifies **by reading the files**, rules on open questions, appends an entry to `WORKFLOW_LOG.md` and archives the findings to `findings/segment-<id>.md`.

**⛔ vClaude does not commit. Rudra commits.** No `Co-Authored-By` trailer. Written into `AGENT_PROTOCOL.md`.

**Never edit a segment spec after handing it over.** Violated once on 19 September; vClaude had to restart.

---

## Standing rules earned in segments 23–25

- **The Architect reads the artefact before ruling on it.** Entry 032 ruled on a 34-cell grid from a prose summary; three of four resulting errors were visible in the file's first eighty lines. **Six stated facts in this phase came from summaries and did not survive the data.**
- A property recorded once and never re-derivable must be cross-checked against an independent measurement before it is frozen.
- A provenance field cannot be verified by reading the provenance.
- **A document that has become a deliverable is not covered by the test suite until something reads it.** Stripping the `EXPLORATORY` tag from `FINDINGS_TESTS.md` §7 passed all 543 tests.
- **A constant and its caller must agree on units, and nothing in the output reveals when they do not.** A per-arm floor fed totals over ten arms was ten times too lenient.
- **When a re-derivation disagrees with its target, the shape of the disagreement says which one is wrong.** A difference that tracks a structural property of the data is a defect in the reader.
- A guard written for one representation of "absent" does not cover the others — `is None` does not catch `NaN`.
- Before declaring a metric primary at a tier, check that it takes more than one value there. Third population correction after non-events and `calm`.
- **The precision of a null comes from the variance of the arms compared, not the seed count.** The same 150 seeds bought 0.06 pp on sensing and 1.07 pp on ρ.
- Exploratory analyses are labelled as such and may never overturn a pre-registered conclusion.

---

## Outstanding, non-technical

1. **Professor conversation.** Four items: is the result acceptable in scope; does he want the magnitude-signal follow-up (one expression change, ~4 hours compute, needs its own pre-registration); dashboard sign-off; why `change_rate` was abandoned.
2. **`DPO_Minor_project-main`** — a sibling folder to `Dynaswarm` on the Desktop, **not in this repo and never pushed**. It holds `paper/paper.tex` and `docs/presentation.md` with fabricated numbers (A\* = 142.3, "18.3% improvement", t = −6.82) that claim the opposite of this run's findings. Establish whose it is, then delete it or move it out of `ML Minor/` so it cannot be bundled with the submission.
3. 13 stray `outputs/2026-09-17` directories, all verified exploratory. Optional.
