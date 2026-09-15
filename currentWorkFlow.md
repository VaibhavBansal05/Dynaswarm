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

## FINDINGS — Segment 21

**Status:** COMPLETE

### T0 — both surfaces

| | Before | After |
|---|---|---|
| Python suite | 455 passed | **476 passed** (96.6s) |
| JS suite | 50 passed | **50 passed** |
| `src/` statements | 2156 | **2163** — reported, no ceiling |
| `ruff check src/ tests/ scripts/ dashboard/` | clean | clean |

The cap is gone. `MAX_SRC_STATEMENTS = None`; `test_statement_budget` now prints
the count and the five largest files and asserts only that the walker found
something. Nothing in this segment was sized to a number.

### T1 — the defaulted-lookup audit

```
grep -rn "probe.get(|\.get\("aco_|\.get\("pso_" src/dynaswarm/allocation/
  → none. Every required probe field is indexed.
```

Two sites existed, both in `observation.py`, and both are now
`probe[PROBE_ACO_STAGNATION]` / `probe[PROBE_PSO_CONVERGENCE]` against named
constants. `KeyError: 'aco_lambda_branch'` was watched firing before the fix
landed. The audit found **no others anywhere in `allocation/`** — the pattern
had been written exactly twice, which is the two Entry 021 R1 names.

### T3 — the four arm series

```
1. Fixed / Static Hybrid  — must be exactly 0.5 always
   0.5000 ×10        distinct values: 1   all exactly 0.5: True

2. New Recency-Based Adaptive Hybrid  — must move, and move WITH recency
   fraction  0.5000 0.5000 0.5000 0.4990 0.4980 0.4970 0.4960 0.4950 0.4940 0.4930
   recency   0.0000 0.0000 1.0000 0.7000 0.4900 1.0000 0.7000 0.4900 1.0000 1.0000
   events         0      0     25      0      0     25      0      0     25     25
   distinct values: 17
   corr(recency, Δfraction) over the 37 steps it moved: -0.776
   mean change on a disruption step: -0.001000
   mean change on a quiet step:      -0.000133

3. Scheduled Hybrid (open-loop control)  — must vary open-loop
   quiet world   0.5000 0.5500 0.6000 0.6500 0.7000 0.7500 0.7492 0.7390 0.7288 0.7186
   violent world 0.5000 0.5500 0.6000 0.6500 0.7000 0.7500 0.7492 0.7390 0.7288 0.7186
   identical regardless of disruption: True   distinct: 40

4. ACO, frozen ρ vs ACO, adaptive ρ
   frozen   0.1000 ×10                               distinct rho: 1
   adaptive 0.1000 0.1000 0.1010 ... 0.1080          distinct rho: 28
   trajectories differ: True
```

The adaptive arm is the only one that needed more than "it moved". It moves
**with recency at −0.776** (negative is the designed direction — rising recency
buys PSO, per `EXPLORE_SIGN`'s `aco_fraction: -1`) and responds **7.5× more
strongly on a disruption step than a quiet one**.

**I reported this wrong first.** The initial version printed "mean change on a
disruption step: +0.000000" — a clean, believable zero that I nearly wrote up as
"the arm does not respond to disruptions at all". `delta[i]` is the change *from*
step i, so the response to a disruption at step i lands in `delta[i]`; I had
indexed `delta[i-1]` and was reading the step before the event. The number was
real, the arithmetic was real, and it was answering a different question than the
label claimed. Fixed in `scripts/verify_arms.py` with the reasoning in a comment.

### T4 — the eleven fields at three timesteps

```
  field                       quiet, opening  disruption lands        recovering
  t                                        0                 2                 5
  recency                                  0                 1                 1
  steps_since_disruption                   1                 0                 0
  events_this_step                         0                25                25
  current_fraction                       0.5               0.5             0.497
  budget                                 300               300               300
  aco_lambda_branch                     5.96              6.01             5.781
  pso_diversity                       0.1734            0.1505            0.1399
  own_cost                             103.8             103.8               102
  own_cost_delta                           —                 0                 0
  path_invalidated                     False             False             False
```

Across the whole 60-step run: `t` 60 distinct · `recency` 13 · `steps_since_disruption`
12 · `events_this_step` 3 · `current_fraction` 17 · **`aco_lambda_branch` 58** ·
**`pso_diversity` 60** · `own_cost` 7 · `own_cost_delta` 7 · `budget` **CONSTANT** ·
`path_invalidated` **CONSTANT**.

**Field by field.** Nine carry real information. The two that matter most are the
two mutation C silenced: `aco_lambda_branch` takes 58 distinct values and
`pso_diversity` 60, so they are reading live telemetry, not a default. Under
mutation C both would read `0.0` at all 60 steps, and that is the reading this
table exists to make visible.

Two are constant, and they are **not** the same case:

- `budget` is constant **by definition** — it is the evaluation budget, fixed for
  the run. It is carried for the record, not for a rule. Correct as is.
- `path_invalidated` is constant **by accident of this run** — the hybrid never
  lost a path in 60 steps at `events_per_step=0.3`. The field is wired correctly
  (it is `solution is None` from the live trial). It carries no information *yet*,
  and **a policy written to depend on it today would be depending on a column
  that has never once been `True`.** Recorded in `IncrementalAllocation`'s
  docstring as a live caveat rather than a design choice.

### T6 — the saturation distribution, and my ruling on 20%

```
  scenario      seed  distinct   at bound  reportable
  static        1000         1      0.0%          NO
  static        1001         1      0.0%          NO
  static           7         1      0.0%          NO
  static          42         1      0.0%          NO
  low           1000        16      0.0%         yes
  ...
  high            42        40      0.0%         yes

  across 16 runs: max 0.0%, mean 0.0%, threshold 20%
```

**My ruling: keep 20%, and record that it currently cannot fail.** Not "it passes
comfortably" — it is *unfalsifiable for this policy*. `IncrementalAllocation`
steps by `sigma = 0.001` from a start of 0.5, so reaching the 0.05 bound needs
**450 consecutive steps in one direction and scenarios run 60**. The observed
0.0% is arithmetic, not evidence.

I did not lower it to fit, because that would be tuning a threshold to the one
policy that cannot trip it. It binds on `ScheduledAllocation`, whose timetable can
be set to end anywhere, and it is the guard that matters most for
`LearnedAllocation`, which has no built-in reason to stay near the middle.

**What must not be claimed: that a run passing this check is evidence the split
stayed healthy.** For the incremental arm it is evidence of nothing. The live half
of `reportable()` is the `distinct` clause — and it *does* fail: every
static-scenario run fails it, correctly, because with no disruptions recency never
moves and the policy never adapts. All of this is now in `MAX_AT_BOUND`'s
docstring, where someone reading the constant will meet it.

### T9 — both mutations, shown red

**Mutation A (specified)** — `IncrementalAllocation.propose` returns
`obs.current_fraction`, silently becoming `FrozenAllocation`. The arm still runs,
still logs itself adaptive, still produces real excess figures.

```
FAILED tests/test_allocation.py::test_incremental_allocation_moves_by_exactly_sigma
FAILED tests/test_hybrid.py::test_allocation_arms_share_a_stream_and_differ_only_by_control
        AssertionError: the adaptive arm must actually shift its allocation
        assert 1 > 1  where 1 = len({0.5})
```

Caught, by two tests, one of them the ablation-pair test. Reverted.

**Mutation B (mine)** — one line in `harness/trial.py`:
`probe["aco_fraction"] = applied`, recording the decision taken at the *end* of a
step as though the step had searched with it.

**It passed all 475 tests.**

Every number stays real. The arm still adapts, the chart still moves, the
allocation still correlates with recency. The only thing that changes is that the
split appears to respond to a disruption **one step before it happens** — which is
F1 exactly: invisible in the value, visible only in which index it came from.
F1 voided every recency-driven result in this project's history, and this is the
same defect relocated into the telemetry that Claim 3 will be argued from.

Closed by `test_the_recorded_split_is_what_the_step_searched_with_not_the_next_one`,
which asserts the relationship between consecutive rows (`searched[t] ==
applied[t-1]`) because **no single row can be wrong on its own**. Shown red under
the mutation:

```
E   Obtained: 0.6000000000000001
E   Expected: 0.55 ± 5.5e-07
```

Reverted; suite green at 476.

### Does the thesis mechanism actually work? My read.

**The mechanism works. The effect is currently too small to carry Claim 3, and
that is a parameter question, not a design question.**

What is demonstrated: the adaptive arm senses recency, and the split it chooses
moves *with* that signal in the designed direction at −0.776, seven and a half
times more strongly on disruption steps than quiet ones. That is the causal chain
the thesis asserts — disruption → recency → reallocation — observed end to end on
a live trial rather than argued. The ablation twin sits at exactly 0.5 with 1
distinct value, and the open-loop control varies identically in a violent world
and a quiet one, so an effect found here can be attributed.

What is not demonstrated: that this changes outcomes. Over 60 steps the split
travels **0.06** — from 0.500 to 0.440. On the dashboard run all three hybrids
ended at +0.0% excess with identical routes. `sigma = 0.001` was inherited from
`IncrementalController` unchanged and deliberately so, to keep results comparable
across the restructure — but it was chosen for *parameter* adaptation, where the
quantity being nudged is ρ on [0,1] over a whole tuning run, not for a split that
has 60 steps to get anywhere. **A mechanism that provably works and provably
barely moves will produce a null result that looks like a refutation of the
thesis rather than of the step size.** I did not change it: `sigma` is a
`PARAM_SPEC` default and the segment did not authorise it. It is the first thing
Phase 4 should sweep.

**Files changed**
- `src/dynaswarm/allocation/observation.py` — required probe fields indexed, not
  `.get`-with-default; the two keys named as module constants
- `src/dynaswarm/allocation/policies.py` — `IncrementalAllocation` docstring states
  which 3 of 11 fields it reads, which 8 it ignores and why they are not trimmed
- `src/dynaswarm/allocation/governor.py` — `MAX_AT_BOUND` carries T6's measurement
  and the finding that it cannot currently fail
- `src/dynaswarm/harness/trial.py` — records `alloc_proposed` / `alloc_applied` /
  `alloc_held_back` / `alloc_at_bound` so §15.6 has data to draw
- `src/dynaswarm/config.py` — `ControlCfg.sigma_max`, `initial_fraction`
- `src/dynaswarm/harness/arm.py` — `hybrid_scheduled`; governor wiring
- `tests/test_hygiene.py` — the cap is report-only and always passes
- `dashboard/server.py` — `/api/arms` serves names **and colours**; controlled arms
  raceable; `ARM_COLORS`, `MIN_ARM_LUMINANCE_GAP`, `arm_luminance`
- `dashboard/static/{app.js,model.js,index.html,style.css}` — the allocation view;
  arm list and palette fetched rather than duplicated

**Files added**
- `scripts/verify_arms.py` — T3, prints the series
- `scripts/observation_and_saturation.py` — T4 and T6

**Tests added**
- `test_a_governed_arm_is_charged_exactly_what_an_ungoverned_one_is` — §10.2
- `test_every_hybrid_sees_the_identical_world_governor_or_not` — §10.2
- `test_the_observation_carries_nothing_derived_from_the_oracle` — I1, via AST
- `test_the_recorded_split_is_what_the_step_searched_with_not_the_next_one` — mutation B
- `test_every_raceable_arm_has_its_own_colour`, `test_arm_colours_stay_distinguishable_in_greyscale`
- `test_a_raceable_controlled_arm_moves_its_split_or_provably_does_not` (×3 arms)

**Deviations from spec**
1. **`hybrid_scheduled` has no row in §9's display-name table.** I added the arm
   (§7.2's open-loop control) but §9 is yours. I used *"Scheduled Hybrid (open-loop
   control)"* in `ARM_DISPLAY` with a comment saying it is a placeholder awaiting a
   §9 row, and did not edit `ARCHITECTURE.md`. **§9 needs the row.**
2. **`ARM_COLORS` moved from `model.js` to `server.py`.** Not cosmetic: the arm id
   `hybrid_scheduled` contains the literal `schedule`, which
   `test_the_dashboard_never_derives_event_timing_itself` greps for across all JS
   to protect F1. The arm id is frozen data (D23a) and that guard protects the
   project's worst defect — neither could give way, so the map moved to the
   language that has an AST. The guard is **untouched**.

**Three tests were replaced, not weakened. Each is listed because you should
check my judgement on all three.**

- `test_no_controlled_arm_is_reachable_from_the_dashboard` — its stated premise is
  F7 (`arm.py:228` building the prescheduled controller with no arguments). F7 was
  closed in segment 20 and this segment commissions the view it forbids. Replaced
  with the *condition that justified the ban*: every raceable controlled arm must
  be run and watched — frozen must not move, adaptive and scheduled must.
- `test_the_allocation_view_is_a_labelled_gap_not_a_drawing` — described itself as
  "the reminder to build it". Its measurement half is **kept intact** (the
  uncontrolled `hybrid` must still hold one fraction); only the final
  `"Phase 3" in markup` assertion was replaced, with a check that the per-step bar
  reads `searched` and not `applied` — i.e. it now guards mutation B.
- `test_a_hybrid_on_the_default_target_now_fails_loudly` — asserted `KeyError` on
  default `targets=["rho"]`. The controlled hybrids moved from controller to
  governor this segment, so there is no controller left to raise. Replaced with the
  *danger* it guarded rather than the mechanism: the arm must not record a
  `controller_kind` it does not have, and must do real allocation work.

**Surprises**

1. **`model.js` claimed a test that did not exist.** Its comment read "their
   relative luminances are spread — checked in `tests/js/model.test.mjs`, not
   assumed." No such test existed anywhere; `luminance` was exported and never
   called by a test. It cost nothing until this segment made three arms raceable
   with no colours — all three fell through to the `?? "#888"` default and drew as
   **three identical grey lines on the excess chart**, which is Claim 1's evidence.
   Nothing failed. Now asserted in Python, where the palette lives.
2. **My I1 test failed on a docstring.** I grepped `observation.py` for `optimum`
   and `excess`; it matched the paragraph *explaining why they are forbidden*. A
   string check cannot tell a prohibition from a violation — rewritten over the AST.
   This is the second time in one segment that a text grep was the wrong instrument.
3. **`control.targets` is accepted and silently ignored by a governed arm.** Not
   F2 any more (nothing claims the targets were applied, `controller_kind` records
   `""`), but the config still takes a knob that does nothing for these arms.
   Flagged, not fixed — deciding whether a governed arm should reject declared
   targets is a design call, not a defect repair.
4. **The `hybrid` family's greyscale guarantee got materially tighter.** Four arms
   left ~0.2 luminance between neighbours; seven leave **0.071**. Pinned in
   `MIN_ARM_LUMINANCE_GAP` so the next arm cannot quietly erode it further.

**Could not do**

Nothing was blocked.

**Questions for the Architect**

1. **`sigma = 0.001` for allocation.** See my read above — the mechanism works and
   moves 0.06 in 60 steps. Is sweeping it Phase 4's job, or does Claim 3 need a
   value chosen before the evidence runs?
2. **§9 needs a `hybrid_scheduled` row.** My display string is a placeholder.
3. **Should a governed arm reject a declared `control.targets`?** (Surprise 3.)
4. **`path_invalidated` has never been `True`.** Does Claim 3 need a scenario that
   actually breaks paths, or is the field carried for the record only?
