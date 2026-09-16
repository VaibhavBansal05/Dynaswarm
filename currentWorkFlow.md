# SEGMENT Y — The rule the problem calls for

**Phase 3.5 · a single commissioned policy · the last code before the arm set freezes**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` **§7.2, §9, §10.2, §12, §15.6**, and `WORKFLOW_LOG.md` **Entry 023 in full** — the ruling, the design question and the trap below are all argued there.
> Append your findings to the **bottom** of this file.
>
> ## ⛔ YOU DO NOT COMMIT
>
> **Rudra commits. Not you. This supersedes any commit step written anywhere.**
> Leave the work unstaged. Do not `git add`, do not `git commit`, do not `git stash`, never `git add -A`.
> Finish by running `git status --short`, pasting it, and pasting the commit message as a fenced block he can copy — **with no `Co-Authored-By` trailer.**

---

## Why this segment exists

`IncrementalAllocation` is an **integrator**. It uses only the *sign* of pressure and discards its magnitude, accumulating one-bit decisions. That is the correct instrument when hunting a setpoint you do not know — the ρ situation it was inherited from.

**Claim 3 asserts the setpoint is known.** Fresh damage means ACO's trails describe a map that is gone, so favour PSO. Both measured pathologies follow directly from using an integrator anyway: severity-blindness because magnitude was discarded, and 84% cancellation because an oscillating signal integrated wanders around the middle.

This is a commission with its justification on the record **before** any outcome comparison — severity-blind and 84% cancelling, both measured in segment X; inherited rather than designed, per its own docstring. **The incremental arm stays.** It holds Claim 2's rule form constant while changing only the target, which isolates *what* is adapted; the new arm isolates *how* it responds.

---

## ⚠️ T0 — Measure, both surfaces, no ceiling

`pytest`, `node --test`, `ruff`, statement count reported not capped. Before and after.

---

## T1 — **Measure what the staleness signal costs.** The design branches here.

The principle says ACO's pheromone describes a map that is gone. **Recency does not measure that** — it measures elapsed time and assumes damage scales with freshness. Twenty-five roads breaking where ACO laid no pheromone invalidates nothing; three roads on the current best path, where the trail is thickest, invalidates a great deal. Recency scores both 1.00.

Segment 21 established that ACO's `rebind` zeroes trails **only on newly-inactive slots**. It already visits exactly the stale edges and already holds their pheromone.

**T1a.** Find that point in `aco.py`. Report what it would take to compute, at each rebind, the **fraction of total trail mass that sat on slots deactivated this step** — and to surface it on the probe. Line count, files touched, whether it needs new plumbing or fits where the values already are.

**T1b.** Confirm it is not oracle-derived. It must be ACO's own state plus the event mask, nothing from A\*. `test_the_observation_carries_nothing_derived_from_the_oracle` must still pass over the AST.

**T1c.** Name the architectural cost explicitly: the observation is currently component-agnostic, and this field makes one entry depend on how ACO stores things. **Do not absorb that silently — state it and say whether you think it is worth paying.**

**T1d — the branch.** Cheap and clean → **build on staleness.** Real plumbing → **build on recency** and record staleness as the named extension. Say which you chose and why, with the measurement, before writing the policy.

---

## T2 — Build the policy

A **direct** rule. The split at time *t* is a function of the state at time *t* and nothing else. No accumulation, no baseline, no history — so it cannot drift, cannot thrash, and cannot be somewhere it shouldn't be because of where it has been.

The shape, on whichever signal T1 selected (call it `s`, on [0, 1], high meaning ACO's knowledge is least trustworthy):

> **split = 0.5 + A × (0.5 − s)**

`s = 0` → ACO-heavy. `s = 1` → PSO-heavy. `s = 0.5` → exactly 0.5.

Note, if you build on recency: **a linear map on recency is already exponential in time**, because recency decays ×0.7 per step. The shape is right; do not add curvature to make it look more sophisticated.

Name the arm and the policy class. Do not edit `ARCHITECTURE.md` §9 — hand me the row you want, as segment 21 did.

---

## T3 — ⚠️ **The rate-limit trap. Measure this before choosing `A`.**

The governor rate-limits. **A direct policy's entire purpose is to jump hard on the step a break lands.** If that jump exceeds the limit, the governor clamps it and silently converts your direct policy into a slow one — while every instrument keeps reading the *request* rather than the *result*.

**That is the `sigma` defect exactly, one layer up, and it is the most likely way this segment produces a null result that means nothing.**

1. Measure the largest single-step change in `s` that actually occurs in a real scenario (recency going 0.24 → 1.00 is the shape of it).
2. Work out what `A` makes that jump collide with the rate limit.
3. Report `alloc_proposed` against `alloc_applied` for the new arm across a full run, and say **how often the governor clamped it.**
4. If the clamp binds at any sane `A`, that is a finding about the governor, not about the policy. **Report it; do not quietly shrink `A` until the clamp stops firing.**

---

## T4 — Derive `A`, before any excess

Same discipline as `sigma` in segment X. From quantities fixed before a result is seen:

| Constraint | Source |
|---|---|
| Floor | the swing must move whole evaluations — `1/budget` |
| Ceiling | the governor's bounds, and T3's rate limit |
| Reach | the swing must be large enough that the two ends are meaningfully different searches |

Put the derivation in the docstring **including the sentence that it was chosen before any excess figure was looked at** — which is only true if you do it in that order. **Do not look at excess until `A` is fixed.**

---

## T5 — Prove the arm does what its name says

Extend `scripts/verify_arms.py`. The new arm must show, on a live trial:

- the split **responding on the step the break lands**, not two steps later
- the response **scaling with severity** — a big break must move it further than a small one. This is the property the incremental arm provably does not have, and it is the whole reason this arm exists. **Measure it directly: correlate the size of the step against the size of the disruption.**
- **total variation against net displacement.** The incremental arm cancels 84%. Report the new arm's ratio. If it also cancels most of its movement, the redesign did not work and I want that stated plainly.
- `hybrid_fixed` still pinned at exactly 0.5, and the other arms unchanged

---

## T6 — Then, and only then, excess

Race all four hybrids. Report what you get, whatever it is. **A direct policy that is provably severity-aware and still produces no outcome difference is a real and reportable finding about the thesis, not a failure of this segment.**

---

## T7 — Tests

Every measured property that will still be true next month. In particular:

- the split is a **pure function of the current state** — same observation, same output, regardless of what came before. That is the defining property of the redesign and it is one assertion.
- the response **scales with severity**
- the governor does not clamp the arm under normal operation (or, if it does, the test records the clamp rate as the guarded property)

**A test of a feature runs on data where the feature is active.** A severity test needs disruptions of genuinely different sizes in the same run.

---

## T8 — Mutations, two, one of them yours

**Mine:** in the new policy, replace `s` with `obs.recency` **regardless of which signal T1 selected**. If T1 chose recency, invert the sign instead. Predict what breaks before running it.

**Yours:** pick something this segment's tests would catch and the existing suite would not. If it passes everything, **that is the finding** — write it up as one, as you did with segment 21's mutation B.

---

## T9 — Show it

Paste verbatim:

- **T1's cost measurement and your branch decision**, with the reasoning
- **T3's clamp report** — proposed against applied, and how often it bound
- **`A` and its derivation, in the order you did it**
- **T5's three artefacts**: response timing, severity scaling, and the cancellation ratio against the incremental arm's 84%
- Excess for all four hybrids
- Both mutations, shown red
- The §9 row you want
- **Your read: is the new arm a better instrument for Claim 3 than the incremental one, on the evidence rather than the design argument?**

---

## T10 — Hand over, do **not** commit

`git status --short`, unstaged. The commit message as a fenced block, no `Co-Authored-By`. FINDINGS appended.

---

## Constraints

| | |
|---|---|
| **No statement ceiling.** Report the count. | |
| **Do not look at excess until `A` is fixed** (T4 before T6) | |
| **Do not shrink `A` to stop the governor clamping** — report the clamp | |
| **Every test calls the production entry point** | |
| **A test of a feature runs on data where the feature is active** | |
| **A claim about system behaviour written from one seed is a claim about that seed** | |
| **Do not commit, do not push** | |

---

## Acceptance check

```bash
git diff --stat -- src/ tests/ dashboard/ scripts/
./.venv/bin/pytest
node --test tests/js/*.test.mjs
./.venv/bin/ruff check src/ tests/ dashboard/ scripts/
git status --short                                # UNSTAGED, UNCOMMITTED
```

---

## Definition of done

The signal chosen by measurement · `A` derived before any excess was seen · the governor's clamp behaviour reported · the arm shown responding on the right step and scaling with severity · its cancellation ratio measured against the incremental arm's 84% · both mutations red · green suite · uncommitted with the message pasted · FINDINGS appended.

**This is the last code before the arm set freezes.** Segment 22 is Rudra by hand; segment 23 is the manifest.

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->
