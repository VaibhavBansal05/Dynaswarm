# SEGMENT 21 — Wire the Arms. The Thesis Runs.

**Phase 3 · Restructure · Segment 5 of 5 — closes the phase**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` **§7 (all), §8 (the evidence set), §9 (arms and display names), §10.2 (fairness), §12 (provenance), §15.6 (the allocation view)**. `WORKFLOW_LOG.md` **Entry 021** — R1 is T1 here, and the three gaps you named are T5, T6 and T7.
> Append your findings to the **bottom** of this file.
>
> ## ⛔ YOU DO NOT COMMIT
>
> Rudra commits. Leave the tree unstaged, paste `git status --short`, and paste the commit message as a copyable block **with no `Co-Authored-By` trailer**. No `git add`, no `git commit`, no `git stash`, never `git add -A`.

---

## Goal

**Connect the machine to the trials, and prove each arm does the thing its name claims.**

Twenty segments of apparatus have been built around a thesis that has never executed. This is the segment where it runs.

**And the risk is concentrated here.** Every arm this wires is one whose failure mode is *looking exactly like a result*. F7 was a controller reporting itself active while varying nothing. Mutation C was two observation fields reading zero forever with the suite green. **Both would have produced clean, publishable, meaningless numbers.** The verification in this segment is not a formality attached to the wiring — it is the segment.

---

## ⚠️ T0 — MEASURE, and the cap is gone

**Rudra has removed the statement ceiling.** There is no cap on `src/`. **Build whatever the correct implementation requires** — never trim, split, defer or compromise a design for budget reasons again. That applies retroactively to anything you held back in segment 20.

`test_statement_budget` stops asserting a limit. It **reports the count and always passes.** Same for the dashboard's caps.

**The number is still reported in every segment close, with one line on why it moved.** That is the only reason the measurement survives: a measurement that stops being reported is F5 — the dead instrument reading `0.000` that nearly put a flattering wrong number in the report. Entry 020's R2 (science closes after this segment) and R3 (`LearnedAllocation` costed separately) are **withdrawn along with the cap.**

Report `src/` before and after, and the dashboard's two figures.

## T1 — Entry 021 R1: kill the silent zero structurally

`probe.get("aco_lambda_branch", 0.0)` → `probe[key]`, raising.

**A `.get(key, default)` on a required field is a silent-zero generator.** It turns a loud immediate failure into a quiet permanent wrong answer, and the quieter the failure the further it travels. **This is F8 reborn** — Entry 005 logged the same pattern in `control/` and deferred it to the restructure specifically so it would not be written twice. It was written twice.

Your contract test stays as the second line. The primary fix is structural: **a test can drift, a `KeyError` cannot.**

Audit `allocation/` for every other `.get` with a default on something that must exist, and say what you found.

---

## T2 — Wire the four controlled arms

Per §9's registry and §7.2's design:

| Arm | Policy | Role |
|---|---|---|
| `hybrid_fixed` — **Fixed / Static Hybrid** | `FrozenAllocation` | the ablation twin |
| `hybrid_adaptive` — **Recency-Based Adaptive Hybrid** | `IncrementalAllocation` | **the thesis** |
| `aco_fixed` — **ACO, frozen ρ** | evidence set, §8 | Claim 2 |
| `aco_adaptive` — **ACO, adaptive ρ** | evidence set, §8 | Claim 2 |

Plus `ScheduledAllocation` reachable as an arm — §7.2 calls it **the honest control for feedback itself**, and it cannot play that role from outside the registry.

**Use §9's display names in every human-facing string.** Code ids are frozen data (D23a).

**The fairness guarantees (§10.2) apply to the new arms exactly as to the old.** Adding a controller must not change what an arm sees or what it is charged. Assert it rather than assume it — a controlled arm that quietly gets more evaluations would show the thesis winning for the wrong reason, which is the most expensive possible failure here.

## T3 — **Prove each arm does what its name says.** This is the segment.

Four checks. **Each one, if it fails, means that arm reports nothing.**

| Arm | What must be true | What it means if not |
|---|---|---|
| **Frozen** | `aco_fraction` is **exactly** 0.5 at every step | The ablation twin is not a twin; Claim 3's control is broken |
| **Adaptive** | the fraction **moves**, and moves **in response to `recency`** | The thesis arm is the baseline wearing a label. F7 exactly |
| **Scheduled** | varies **open-loop**, ignoring the world | The control for feedback cannot distinguish varying from sensing |
| **ACO pair** | `aco_fixed` and `aco_adaptive` produce **different** ρ trajectories | Claim 2's evidence set is one arm run twice |

**Paste the actual series**, not a verdict. A number per step, for each.

**And the adaptive one needs more than "it moved."** A fraction that wanders would also move. Show it responds to the signal: **the fraction should change when `recency` changes, and the relationship should be visible.** If it moves but not with recency, say so — that is a finding, not a failure to report.

## T4 — Build a real observation from a live trial and print every field

Your first gap, and mutation C is why it matters: **nothing has ever built an observation from a running trial.**

Take one trial, at three timesteps — quiet, disruption, recovery — and **print all eleven fields with their values.**

Then look at them and say, field by field, whether each is carrying real information. **`aco_lambda_branch` and `pso_diversity` reading a constant is exactly what mutation C produced**, and a printed table is how a human sees it where a green suite did not.

## T5 — `IncrementalAllocation` uses three of eleven fields. State it.

Your second gap. It reads `recency` and little else — eight fields available and unused. **Correct for continuity** (§7.2 requires the rule preserved exactly), and it must be **written down where the report will find it**, because a reader seeing an eleven-field observation will assume the rule uses them.

**One paragraph, in the docstring:** which fields it reads, which it ignores, and that the richer ones exist for `LearnedAllocation` and for policies not yet written. **An unused field that looks used is a claim nobody made and everybody infers.**

## T6 — Measure saturation, then justify 20% or change it

Your third gap, and your own comparison is the reason: *"same shape as the caps we've twice had to re-derive."*

**Run the adaptive arm across several seeds and scenarios and report what saturation actually looks like** — the distribution of time at a bound, and whether 20% is loose, tight, or arbitrary.

Then **either justify 20% against that distribution or replace it with a number that is derived.** Entry 012's rule: a threshold must come from the property protected, never from where things happen to sit.

If the honest answer is "20% is arbitrary but no run comes close," say that — a documented arbitrary threshold with measurements beside it is defensible; an undocumented one is not.

## T7 — The allocation view

§15.6 calls it *"the project's novelty made watchable"* and segment 12 left a labelled gap saying it arrives when the controller works. **It works now.**

Show, per timestep: **`aco_fraction` proposed and applied** (both — the governor records them separately for a reason), and whether the value is at a bound.

**Why it belongs in this segment and not a later one:** the check in T3 is *"does the fraction actually move"*, and a person confirms that by watching it, not by reading a column. Rudra verifies this whole layer by hand in segment 22, and this is the instrument he does it with.

Small. The excess chart is 36 lines and this is comparable.

## T8 — Tests

| Test | Catches |
|---|---|
| **Frozen holds exactly 0.5 across a full run** | |
| **Adaptive's fraction moves, and correlates with `recency`** | The thesis arm being the baseline in disguise |
| **Scheduled varies with default construction** | F7's bar, now at arm level |
| **`aco_fixed` and `aco_adaptive` diverge** | Claim 2's evidence set being one arm twice |
| **Every observation field from a live trial is non-constant where it should vary** | Mutation C at the wiring layer |
| **A controlled arm is charged the same as an uncontrolled one** | §10.2. The most expensive failure available |
| **A missing probe key raises rather than defaults** | T1 |

**Every invariant shown failing against corrupted input**, and **every test calls the production entry point** — Entry 019's rule, broken in the segment written to prevent it.

## T9 — Mutations, two, one of them yours

**Specified:** make `IncrementalAllocation` return `obs.current_fraction` — i.e. silently become `FrozenAllocation`. The arm still runs, still logs itself as adaptive, still produces excess figures. **Every number is real and the thesis arm is the ablation twin.** That is F7 at the level where it would cost the most.

**Yours.** Twelve consecutive segments.

## T10 — Show it

1. T0, both surfaces
2. T1's audit — every defaulted lookup found
3. **The four series from T3** — frozen, adaptive, scheduled, and the ACO pair's ρ
4. **The eleven observation fields at three timesteps**, with your read on which carry information
5. **The saturation distribution**, and your justification or replacement for 20%
6. **A screenshot of the allocation view** with the fraction moving
7. Both mutations, every invariant shown red
8. **Your read: does the thesis mechanism work?** Not "is it wired" — does the fraction respond to disruption in the way §7.3 describes. **This is the first time anyone can answer that.**

## T11 — Hand over, do **not** commit

`git status --short`, the commit message as a copyable block, no `Co-Authored-By`, one line confirming complete and uncommitted.

---

## Constraints

| | |
|---|---|
| **No statement cap** | Build what correctness requires. Report the number, never trim to it |
| **Required fields index, never default** | |
| **§9 display names in all human-facing strings** | |
| **§10.2 fairness holds for controlled arms** | Asserted, not assumed |
| **`LearnedAllocation` still not built** | Mentor sign-off, D7/O2 |
| **Paste series, not verdicts** | |
| **Every test calls the production entry point** | |
| **Do not commit, do not push** | |

---

## Acceptance check

```bash
git diff --stat -- src/ tests/ dashboard/
./.venv/bin/pytest
./.venv/bin/ruff check src/ tests/ dashboard/ scripts/
./.venv/bin/pytest -k "budget or statement" -s     # reports, never fails
ls outputs/
git status --short                                  # UNSTAGED, UNCOMMITTED
```

**Paste verbatim:** T0 · the defaulted-lookup audit · **the four arm series** · the eleven fields at three timesteps · the saturation distribution and your 20% ruling · the allocation-view screenshot · both mutations · every invariant shown red · **your read on whether the thesis mechanism works.**

---

## Definition of done

Green suite, artefacts pasted, **all four arms shown doing what they are named for**, uncommitted with the message pasted, FINDINGS appended.

**This closes Phase 3.** Segment 22 is Rudra verifying the whole system by hand before any compute is committed.

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->
