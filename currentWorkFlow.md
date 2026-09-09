# SEGMENT 16 — The Trust Report

**Phase 2 · Trust it · Segment 3 of 3 — closes the phase**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` **§2.1 (the layers), §10.3, §17**, and `WORKFLOW_LOG.md` **Entries 014 and 015** — 015 carries F13, R2 and R3, which constrain this segment.
> Append your findings to the **bottom** of this file.
>
> ## ⛔ YOU DO NOT COMMIT
>
> Rudra commits. Leave the tree unstaged, paste `git status --short`, and paste the commit message as a copyable block **with no `Co-Authored-By` trailer**. No `git add`, no `git commit`, no `git stash`, never `git add -A`.

---

## Goal

**One command that answers, for every mechanism in this system: did it run, and how do we know.**

Segments 14 and 15 built the probes. They live in a run's telemetry, readable by someone who knows where to look. **That is not the same as being able to answer the question**, and the question gets asked in a viva.

Phase 2's gate — *every mechanism proven live or reported inert* — is currently true and **unproducible on demand**. This segment makes it producible.

---

## What this is not

**Not a dashboard feature.** Phase 1 is closed. The per-arm panel could now carry probe telemetry and §15.6 says it eventually should — **that waits for Phase 3**, when the panel gets its real content alongside the allocation view. Adding it here would dilute the segment that closes the phase.

**Not a verdict machine.** Entry 015's standard holds:

> *"Every probe answers **did it run**. None answers **did it run correctly**."*

The report says what was measured. It does not grade.

---

## ⚠️ T0 — MEASURE

`src/` **2037 / 2100**, margin **63**. Your projection for this segment was 10–15.

**A large part of this should live outside `src/`** — it is a reporting tool, not science. Say where you put it and why. `scripts/` and `tests/` are both outside the cap; the dashboard is not the right home.

Report projection then actual, plus the closing Phase 2 total against the 95 you started with.

---

## T1 — The report

**One command. Human-readable output. Every mechanism in one place.**

For each of ACO, PSO and the Hybrid, and for each probed mechanism:

- **what was measured** — the count or magnitude, not a grade
- **live or inert** — and the reading that says so
- **the reading it gives when broken** — from the demonstrations already done in 14 and 15

That third column is what makes the document evidence rather than a status page. **A reader must be able to see what a failure would have looked like**, otherwise the report is a list of numbers asserting their own significance.

**Entry 015's R2 is binding on every value printed:** no fixed-decimal format on a quantity whose scale is unknown. PSO's velocity reaches `5e-14`; a `:.4f` renders that as `0.0000` and manufactures the exact claim this phase exists to make honestly. **That mistake has already been made once in this project, by the person looking for it.**

## T2 — Carry the insufficiencies forward

**Entry 015's R3.** Where a probe is known not to detect something, the report says so **beside the probe**, not in a footnote.

Known already:

- **`speed_mean` cannot detect a frozen swarm** — velocity keeps its healthy random initial value. `particles_flown` is what detects it
- **`tau_deposited` cannot detect deposit on the wrong edges** — the count is identical either way
- **No probe answers "did it run *correctly*"** — this belongs at the top of the document, not buried

**A trust report that lists only what it can prove, with no account of what it cannot, is exactly the over-claim the phase was built to prevent.**

## T3 — F13 must be visible in it

Entry 015 logged PSO's velocity collapse — `1.1e-01 → 5.1e-14` across a disrupted run, against `~1.4e-02` stable in isolation.

**It goes in the report as a measurement, with the isolation contrast beside it**, and marked as open for Phase 3. Not as a defect, not as a caveat in prose — as a number with a number to compare it against.

This is the one finding in Phase 2 that changes what the project can claim, and the report is where an examiner will meet it. **Better there, stated by you, than found by them.**

## T4 — Reproducible and dated

The report is **regenerated from a run, not stored**. Someone must be able to run the command after Phase 3 and get a different, current answer — that is the difference between a verification tool and a snapshot that ages into a lie.

**Stamp it** with what produced it: seed, tier, scenario, arms, and the run directory. A trust report that cannot say which run it describes is describing nothing.

**And it must not write into `outputs/`** — segment 12's containment. Whatever run it reads, it reads.

## T5 — Tests

| Test | Catches |
|---|---|
| **The report names every probed mechanism** | Add a probe without adding it to the report and the test fails. **The one that keeps this honest as the system grows** |
| **A disabled mechanism appears as inert in the report** | End to end, not just in the probe |
| **No value renders as `0.0000` when it is non-zero** | R2, enforced |
| **The report writes nothing into `outputs/`** | |
| **It reports the run it actually read** | Not a default, not the last one |

**Every invariant test shown failing against corrupted input, and the corruption pasted.**

## T6 — Mutations, two, one of them yours

**Specified:** drop one mechanism from the report while leaving its probe in place. The document still reads complete — every line in it true — and the missing line is the one nobody notices. **A trust report's failure mode is omission, not error.**

**Yours.** Seven consecutive segments.

## T7 — Show it

1. T0, and the Phase 2 closing total against 95
2. **The report itself, in full.** It is the deliverable — paste it, do not describe it
3. The same report against a deliberately broken mechanism
4. Both mutations
5. **Your read, closing Phase 2: what can this project now honestly claim about its own machinery, and what can it not?** You have built every probe in it

## T8 — Hand over, do **not** commit

`git status --short`, the commit message as a copyable block, no `Co-Authored-By`, one line confirming complete and uncommitted.

---

## Constraints

| | |
|---|---|
| **Report measurements, never verdicts** | |
| **No fixed-decimal formats on unknown scales** | R2. It has already caught this project once |
| **Insufficiencies stated beside the probe** | R3 |
| **Regenerated, never stored** | |
| **Writes nothing to `outputs/`** | |
| **Prefer outside `src/`** | It is a tool, not science |
| **No dashboard work** | Phase 1 is closed; probe telemetry in the per-arm panel is Phase 3 |
| **No control-layer changes, no PSO fix** | F13, F4, F7, F8 are Phase 3. **Report; do not fix** |
| **Do not commit, do not push** | |

---

## Acceptance check

```bash
git diff --stat -- src/ tests/ scripts/
./.venv/bin/pytest
./.venv/bin/ruff check src/ tests/ dashboard/ scripts/
./.venv/bin/pytest -k "budget or statement" -s
ls outputs/                              # unchanged before and after
git status --short                       # UNSTAGED, UNCOMMITTED
```

**Paste verbatim:** T0 and the Phase 2 total · **the report in full** · the report against a broken mechanism · both mutations · every invariant test shown red · your closing read on what the project can and cannot claim.

---

## Definition of done

Green suite, artefacts pasted, the report produced and shown failing, uncommitted with the message pasted, FINDINGS appended.

**This closes Phase 2.** Then Phase 3 — the control layer gets rebuilt, and the four arms your thesis actually lives in come back.

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->
