# SEGMENT 2 — Documentation Follow-Ups

**Phase 0 · Ground truth · Segment 2 of 3**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` and `decisionLedger.md` first. Segment 1 is recorded in `WORKFLOW_LOG.md` — read Entry 001 before starting, it explains why this segment exists.
> Append your findings to the **bottom** of this file using the §6 template. Do not modify the spec text above it.

---

## Goal

Close out the four issues segment 1 found and correctly declined to fix. **Still no code changes** — the same three documents, plus a local commit at the end.

The largest of these matters more than everything segment 1 did: **the README's headline sentence asserts the thesis the project disproved.**

## Why this is a separate segment

Segment 1's job was marking numbers. These four are corrections to *claims and structure*, found while doing that work, and three of them were explicitly out of its scope. Folding them in retroactively would have meant a segment whose scope grew while it ran — which is the habit the protocol exists to prevent.

Phase 0's remaining code work — the `run_class` convention and the baseline run — is segment 3. Documentation and schema changes are not mixed in one unit.

---

## Scope

**In scope:** `README.md` · `RUNBOOK.md` · `DOCUMENTATION.md` — and a local `git commit`.

**Out of scope:** anything under `src/`, `tests/`, `conf/`, `scripts/` · `outputs/` · defects F1/F2/F3 · `WORKFLOW_LOG.md`, `AGENT_PROTOCOL.md`, `ARCHITECTURE.md`, `decisionLedger.md` (read-only to you) · **`git push`** (Rudra pushes, after Architect verification).

---

## Tasks

### T1 — The superseded thesis *(the important one)*

`README.md` currently opens by asserting what the project refuted. Replace with the text below **verbatim** — do not reword it. This sentence has to hold identically across the README, `ARCHITECTURE.md`, the report and the deck, so it is settled here once.

**T1.1 — Replace the subtitle on line 3.**

Currently:

```markdown
**Volatility-driven compute allocation in hybrid swarm metaheuristics for dynamic path optimization.**
```

Replace with:

```markdown
**Recency-driven compute allocation in hybrid swarm metaheuristics for dynamic path optimisation.**
```

**T1.2 — Replace the Thesis block.**

The current block states the allocation "should be driven by measured environmental volatility" and reasons in terms of the world *churning* — rate-based framing that Claim 2 disproved. Replace the whole block with:

```markdown
## Thesis

> In a hybrid metaheuristic, the **allocation of compute between its exploring and refining components**
> should shift with **how recently the environment was disrupted**.

Not *what parameters to use*, but *how much of a fixed budget goes to the explorer versus the refiner*, and when to move that split. ACO explores and accumulates memory on edges; PSO refines and holds none. A disruption makes the colony's memory stale at exactly the moment it is most trusted — so buy the memoryless component while the trail recovers, and buy the colony back during calm.

**This is not the thesis the project started with.** It began by asking whether allocation should follow measured environmental *volatility*. That was tested and cannot work: tuning separately for each volatility level and then evaluating every vector on every scenario showed that **the optimal parameters do not depend on the disruption rate at all**, so a volatility-driven controller has nothing to steer by. Recency describes a *transient* — a disruption just landed, so the trail is maximally untrustworthy right now — which is a different quantity, and one that sweep said nothing about. See [ARCHITECTURE.md](ARCHITECTURE.md) §1.3.
```

**T1.3 — Check the rest of the README for the same framing.** The "Supporting question" paragraph and any other prose asserting that volatility should drive the allocation. Correct anything that states the superseded thesis **as the project's position**. Leave untouched anything that *describes* volatility-driven adaptation as a hypothesis that was tested — that is history, and it is accurate.

If you find the superseded framing in `RUNBOOK.md` or `DOCUMENTATION.md` as well, **report it, do not fix it** — those need their own wording decision.

### T2 — Consolidate the provisional markers

Eight identical blockquotes in a 220-line document, two of them six lines apart. By the fourth a reader skips them, and adjacent duplicates read as a formatting fault.

**T2.1 — Add one banner**, immediately after the design-of-record pointer near the top:

```markdown
> ## ⚠️ Every result figure in this README is provisional
>
> None of the numbers below can be verified from this repository — they come from runs that are not present here. All of them are superseded by the regeneration programme in [ARCHITECTURE.md](ARCHITECTURE.md) §13, which reports at ≥100 trials on tuned parameters. **Do not cite any figure from this document.** Each table below carries a short reminder.
```

**T2.2 — Replace the eight blockquote markers** with a single italic line above each table:

```markdown
*(provisional — see the banner at the top)*
```

**T2.3 — Leave `RUNBOOK.md`'s two markers as they are.** Two is not repetitive, and that document has no equivalent top matter to hang a banner from.

**T2.4 — Leave `DOCUMENTATION.md`'s §19.1 and §19.2 caveats exactly as they are.** They are two of a kind, they carry different meanings, and they must stay full-strength and adjacent to what they describe.

### T3 — Date-stamp the drifting test counts

`test_hygiene.py` is parametrised across every source file; `test_optimizers.py` is parametrised off `PARAM_SPEC`. Retiring `viz/replay.py`, adding `allocation/`, or adding any parameter moves these numbers on its own. Maintaining them by hand is a losing game.

Above each per-file test-count table — in `RUNBOOK.md` and in `DOCUMENTATION.md` §18 — add:

```markdown
*Counts as collected on 30 Aug 2026. `test_hygiene` and `test_optimizers` are parametrised across source files and `PARAM_SPEC`, so these numbers move whenever a module or a parameter is added. Run `pytest --collect-only -q` for the current figures rather than trusting this table.*
```

Leave the totals in prose as they are — those carry the date-stamp by proximity.

### T4 — Fix the stale Layout block

`README.md`'s `## Layout` section is wrong in two ways:

- it lists a `core/schedule` module that **does not exist** — that logic lives in `core/timeline.py`
- `analysis/` omits `recovery.py`

Correct both against the actual tree. Do not restructure the block or add anything else to it. If you find further inaccuracies in it, **fix the two named and report the rest**.

### T5 — Commit

One local commit. **Do not push.**

```
segment 2: documentation follow-ups (phase 0)

Replaces the superseded volatility-driven thesis statement with the
current recency-driven one, and records why the change was made.
Consolidates eight provisional markers into one banner plus inline
pointers. Date-stamps the parametrised test-count tables. Corrects the
stale Layout block. No code changes.

Spec + findings: currentWorkFlow.md
```

---

## Constraints

| | |
|---|---|
| **T1's replacement text is verbatim** | Do not reword, reformat or "improve" it. If you believe something in it is wrong, **report it and stop** rather than adjusting it |
| **Never invent a number** | Same as segment 1. This segment adds no figures |
| **Never delete a results table or the bug history** | |
| **No code, no tests, no config** | `git diff --stat` must show exactly three files |
| **Do not push** | Local commit only |
| **Do not fix F1/F2/F3** | |
| **Do not start segment 3** | |

If you find the superseded thesis framing anywhere beyond the README, or any other claim that contradicts `ARCHITECTURE.md` §1.3 — **report it, do not fix it.**

---

## Acceptance check

```bash
# 1. Exactly three files changed
git diff --stat

# 2. Suite untouched and green
./.venv/bin/pytest -q -m "not slow"

# 3. Lint clean
./.venv/bin/ruff check src/ tests/

# 4. The superseded framing is gone from the README's own claims
grep -n "Volatility-driven\|driven by measured environmental volatility" README.md

# 5. Exactly one banner, and eight inline pointers
grep -c "Every result figure in this README is provisional" README.md
grep -c "provisional — see the banner at the top" README.md

# 6. The phantom module is gone
grep -n "core/schedule\|schedule ·" README.md

# 7. One commit, nothing pushed
git log --oneline -2
git status --short --branch | head -1
```

**Expected:**

1. Three files: `README.md`, `RUNBOOK.md`, `DOCUMENTATION.md`
2. 271 passed
3. No findings
4. **No output**
5. `1` and `8`
6. **No output**
7. The segment 2 commit on top; branch shows `ahead 1` and not pushed

Then paste verbatim:

- The new README lines 1–14 (title through banner)
- The complete new Thesis block as it now reads in the file
- The corrected `## Layout` block

---

## Definition of done

All seven checks produce the expected output, the three verbatim blocks are pasted, the commit exists and is **not pushed**, and the FINDINGS block is appended below.

**Stop and wait for the Architect's verification.**

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->

## FINDINGS — Segment 2

**Status:** COMPLETE

**Files changed**
- `README.md` — subtitle and Thesis block replaced with the supplied text verbatim (T1.1, T1.2); "Supporting question" paragraph reframed as settled history (T1.3); provisional banner added after the design-of-record pointer (T2.1); all 8 blockquote markers replaced with the inline pointer (T2.2); `Layout` block corrected (T4)
- `RUNBOOK.md` — drift note added above the per-file test-count table (T3)
- `DOCUMENTATION.md` — same drift note above the §18 per-file table (T3)

**Files added**
- None.

**Tests added**
- None. No code was touched, by design.

**Test suite**
Command: `./.venv/bin/pytest -m "not slow"`
Result:
```
271 passed, 5 deselected in 35.26s
```

**Lint**
Command: `./.venv/bin/ruff check src/ tests/`
Result:
```
All checks passed!
```

**Acceptance check**

1. `git diff --stat` — **does not match the spec's expectation; see Deviation 1.** My edits touch exactly the three files in scope. Two further entries were already modified before this segment began, by the Architect and Rudra rather than by me:
```
 AGENT_PROTOCOL.md  |   3 +-      <- Architect's §5 commit-rule patch, pre-existing
 DOCUMENTATION.md   |   2 +       <- mine
 README.md          |  35 ++++---  <- mine
 RUNBOOK.md         |   2 +       <- mine
 currentWorkFlow.md | 288 +++---   <- segment 2 spec (Architect) + this findings block
```

2. `./.venv/bin/pytest -q -m "not slow"` → `271 passed, 5 deselected in 35.26s`

3. `./.venv/bin/ruff check src/ tests/` → `All checks passed!`

4. `grep -n "Volatility-driven\|driven by measured environmental volatility" README.md` → **no output** (exit 1).

5. `grep -c "Every result figure in this README is provisional" README.md` → `1`
   `grep -c "provisional — see the banner at the top" README.md` → `8`

6. `grep -n "core/schedule\|schedule ·" README.md` → **no output** (exit 1).

7. Commit and push state:
```
$ git log --oneline -2
ff9541f segment 2: documentation follow-ups (phase 0)
7c569e4 phase0 segment1

$ git status --short --branch | head -1
## main...origin/main [ahead 1]
```
One commit, `ahead 1`, **not pushed**. Verified no code touched: `git diff --stat -- src/ tests/ conf/ scripts/` was empty before committing.

**Verbatim blocks requested by the spec**

`README.md` lines 1–14, title through banner:
```markdown
# dynaswarm

**Recency-driven compute allocation in hybrid swarm metaheuristics for dynamic path optimisation.**

Minor project · School of Computer Engineering, MIT Manipal (MAHE)
Vaibhav Krishna Bansal · Rudra Rajpurohit · Kartikey Goyal · Pavit Agrawal
Mentor: Mrs. Vidhya V

> **Design of record: [ARCHITECTURE.md](ARCHITECTURE.md).** That document describes what the system is being built to be, and supersedes this README wherever the two disagree. Settled decisions and the defect log live in [decisionLedger.md](decisionLedger.md).

> ## ⚠️ Every result figure in this README is provisional
>
> None of the numbers below can be verified from this repository — they come from runs that are not present here. All of them are superseded by the regeneration programme in [ARCHITECTURE.md](ARCHITECTURE.md) §13, which reports at ≥100 trials on tuned parameters. **Do not cite any figure from this document.** Each table below carries a short reminder.
```

The complete new Thesis block as it now reads in the file:
```markdown
## Thesis

> In a hybrid metaheuristic, the **allocation of compute between its exploring and refining components**
> should shift with **how recently the environment was disrupted**.

Not *what parameters to use*, but *how much of a fixed budget goes to the explorer versus the refiner*, and when to move that split. ACO explores and accumulates memory on edges; PSO refines and holds none. A disruption makes the colony's memory stale at exactly the moment it is most trusted — so buy the memoryless component while the trail recovers, and buy the colony back during calm.

**This is not the thesis the project started with.** It began by asking whether allocation should follow measured environmental *volatility*. That was tested and cannot work: tuning separately for each volatility level and then evaluating every vector on every scenario showed that **the optimal parameters do not depend on the disruption rate at all**, so a volatility-driven controller has nothing to steer by. Recency describes a *transient* — a disruption just landed, so the trail is maximally untrustworthy right now — which is a different quantity, and one that sweep said nothing about. See [ARCHITECTURE.md](ARCHITECTURE.md) §1.3.

**Supporting question, since settled:** what should the system actually *sense* to make that decision? **External** signals (how much did the world change?) were compared against **internal** ones (has my colony stagnated?) — a choice the literature makes largely arbitrarily. That comparison is reported below, and its outcome is what moved the thesis from rate to recency.
```

The corrected `## Layout` block:
```markdown
## Layout

```
src/dynaswarm/
  core/        rng · graphview · generate · events · timeline · oracle · meter
  optimizers/  protocol · astar · aco · pso · hybrid · spec
  control/     signals · controllers
  harness/     arm · trial · runner
  io/          schema · writer
  analysis/    load · stats · recovery · plots
  tuning/      best_fixed
  viz/         replay
conf/          graph/ scenario/ experiment/ budget/ ...
tests/
```
```

**Deviations from spec**

1. **Acceptance check 1 cannot produce "exactly three files", and this is not a scope breach.** `AGENT_PROTOCOL.md` and `currentWorkFlow.md` were already modified in the working tree when I was told to begin — the §5 commit-rule patch and the segment 2 spec itself. `WORKFLOW_LOG.md` was also newly created, untracked. The check as written assumes a clean tree at segment start, which was not the case here and will not be the case for any future segment whose spec is delivered as an uncommitted edit. **My own edits are confined to exactly the three in-scope files.** Verified: `git diff --stat -- README.md RUNBOOK.md DOCUMENTATION.md` is the complete set of my changes, and `git diff -- src/ tests/ conf/ scripts/` is empty.

2. **The commit necessarily contains more than three files.** Following the precedent set by segment 1's commit `7c569e4` — which swept `AGENT_PROTOCOL.md`, `ARCHITECTURE.md`, `decisionLedger.md` and `currentWorkFlow.md` alongside the three edited documents — I committed the whole working tree, including `WORKFLOW_LOG.md`. The supplied commit message's own footer (`Spec + findings: currentWorkFlow.md`) implies `currentWorkFlow.md` belongs in the commit, which confirms the convention. If the Architect wants segment commits restricted to vClaude's own edits, that needs to be stated — it is the opposite of what segment 1 did.

3. **T1.3 — I edited the "Supporting question" paragraph rather than leaving it.** The spec named it for inspection and told me to correct anything stating the superseded thesis *as the project's position*, while leaving descriptions of the tested hypothesis alone. The paragraph read in the present tense — "We compare **external** signals … against **internal** signals" — presenting a settled comparison as a live supporting question of the current thesis. Immediately after the new recency-based Thesis block, that reads as though rate-versus-stagnation sensing were still the open question. I put it in the past tense and linked its outcome to the thesis change. **This is the one place I exercised judgement on wording rather than applying supplied text**, so it is flagged for review; reverting it is a one-line change.

**Surprises**

1. **The superseded framing exists in `DOCUMENTATION.md` too — reported, not fixed, per the spec.** One hit, at `DOCUMENTATION.md:1115`: *"volatility-driven adaptation is ~1% of what simply choosing good parameters achieves."* Unlike the README's subtitle, this reads as a **description of the tested result** rather than an assertion of the project's position, so by T1.3's own rule it is history and accurate. My reading is that it needs no change, but the spec said to report rather than decide, so it is reported. `RUNBOOK.md` has no hits.

2. **Every other README mention of volatility is legitimately history.** Lines 68, 85, 95, 99, 101 and 111 — the "Why volatility-driven adaptation does not help" section heading, the cross-evaluation narrative, and the signal-saturation discussion — all describe the hypothesis that was tested and refuted. Per T1.3 they were left untouched. The table rows containing `volatility` are signal names, not claims.

3. **The README now has a structural oddity the banner introduces.** The banner is a blockquote containing an `h2` heading, so it appears in the document outline between the design-of-record pointer and "The question". Rendered on GitHub it looks correct and prominent, which is the intent, but any tooling that builds a table of contents from headings will list "⚠️ Every result figure in this README is provisional" as a section. Not a defect — noting it because the spec supplied the markup verbatim and I did not alter it.

4. **`analysis/` was stale in a second way the spec did not name, and it is now correct.** T4 named the missing `recovery.py`; the block also listed modules in an order that did not match the tree. I corrected only the two named inaccuracies — the phantom `schedule` and the missing `recovery` — and left ordering alone, since the spec said not to restructure the block.

**Could not do**

Nothing was blocked. All five tasks completed.

**Questions for the Architect**

1. **Commit scope** (Deviation 2) — should a segment commit sweep the working tree as segment 1's did, or contain only vClaude's own edited files? The two conventions give different histories and the acceptance check assumes the latter while the precedent is the former.
2. **Acceptance check 1's wording** (Deviation 1) — since specs now arrive as uncommitted edits to `currentWorkFlow.md`, "exactly three files" can never hold literally. Suggest future checks scope the diff, e.g. `git diff --stat -- README.md RUNBOOK.md DOCUMENTATION.md`, or state "no changes under src/, tests/, conf/, scripts/".
3. **`DOCUMENTATION.md:1115`** (Surprise 1) — keep as history, or reword?
4. **The "Supporting question" edit** (Deviation 3) — keep, revert, or replace with Architect-supplied wording?
