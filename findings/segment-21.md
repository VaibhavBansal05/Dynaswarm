# FINDINGS — Segment 21

> Archived from `currentWorkFlow.md` by the Architect, 15 Sept 2026. From this segment onward each segment's FINDINGS block is kept here rather than surviving only in a git diff. Ruled in `WORKFLOW_LOG.md` Entry 022.

---


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
