# SEGMENT X — Run the Manual. Settle the Step Size.

**Not numbered.** This segment sits between Phase 3 and segment 22 and belongs to neither. Its job is to run every check in `WALKTHROUGH.md` that a machine can run, so that when Rudra runs the rest **by hand** in segment 22 he is checking a system that has already passed everything checkable, and any surprise he hits is a real one.

> Read `AGENT_PROTOCOL.md`, `WALKTHROUGH.md` **in full**, `WORKFLOW_LOG.md` **Entry 022** — T1, T2 and T3 below are my three rulings from it.
> Append your findings to the **bottom** of this file.
>
> ## ⛔ YOU DO NOT COMMIT
>
> **Rudra commits. Not you. This supersedes any commit step written anywhere.**
> Leave the work unstaged. Do not `git add`, do not `git commit`, do not `git stash`, never `git add -A`.
> Finish by running `git status --short`, pasting it, and pasting the commit message as a fenced block he can copy — **with no `Co-Authored-By` trailer.**

---

## Goal

Three things, in this order of importance:

1. **Settle `sigma` by measurement**, not by argument. I believe it is below the resolution of what it controls. Prove it or refute it.
2. **Exercise the fields and paths that have never been exercised** — `path_invalidated`, which has never once been `True`, and every test in `WALKTHROUGH.md` that runs without a human.
3. **Close the three defects I found in segment 21's review** (Entry 022).

If T1 refutes me, say so plainly and stop there on that thread. **I would rather be wrong in this segment than in the report.**

---

## ⚠️ T0 — Measure, both surfaces, no ceiling

Same as every segment. `pytest`, `node --test`, `ruff`, and the statement count reported not capped. Paste before and after.

---

## T1 — **The step size, measured.** This is the segment.

Entry 022's claim, which you are testing:

> The hybrid splits a budget of 300 evaluations. `sigma = 0.001` moves the declared fraction by 0.001 — **0.3 of one evaluation.** The realised split cannot move by a third of an evaluation. The minimum step that changes any actual work is `1/budget` = 0.0033. `sigma` is set to less than a third of that.

`hybrid.py:140-152` already reports `aco_spent`/`pso_spent` from `self._split` (**realised**) separately from `aco_fraction` (**declared**). That separation was built for exactly this question. Use it.

**T1a — the floor.** Run `hybrid_adaptive` over a full scenario at the default budget. For every step, record declared `aco_fraction` and realised `aco_spent`. Then answer, with numbers:

- Over the run, how many **distinct** values does declared take? Realised?
- On the steps where declared moved by one `sigma`, how many times did realised change **at all**?
- What is the total distance declared travelled, and what is the total distance realised travelled, in evaluations?

**If realised barely moves while declared moves 17 times, the mechanism is inert and Entry 022 is right.** If realised tracks declared, I am wrong — show me and stop.

**T1b — the floor is a function of budget, so vary the budget.** Repeat T1a at `evaluations` = 300, 1000 and 2000. The predicted floor `1/budget` falls as the budget rises, so the same `sigma = 0.001` should go from inert at 300 to live at 2000. **If the inertness does not depend on budget the way the arithmetic says, the arithmetic is wrong.** This is the real test of the explanation, not just of the symptom.

**T1c — set it, from the measurement.** Only once T1a and T1b agree with the derivation. The three constraints from Entry 022, all fixed before any result is seen:

| Constraint | Source | Value |
|---|---|---|
| Floor | one step must move ≥ 1 evaluation | `1/budget` = 0.0033 |
| Ceiling | the governor's rate limit | `sigma_max` = 0.05 |
| Reach | half the distance to a bound over the ~37 of 60 steps it moves | 0.225/37 ≈ 0.006 |

Set `IncrementalAllocation.sigma` and `ControlCfg.sigma` to the value your measurement supports — **0.006 if the derivation holds, a different value if your numbers say otherwise, and say which and why.**

Then put the derivation in the docstring, **including the sentence that it was chosen from the budget and the scenario length before any excess figure was looked at.** That provenance is the difference between deriving a constant and tuning one, and it is only true if you do it in that order. Do not look at excess until this value is fixed.

**T1d — re-run T3 from segment 21 at the new value.** `scripts/verify_arms.py`. All four arms must still do what their names say — in particular `hybrid_fixed` must still be 1 distinct value, and the recency correlation must still be negative. **A larger step that breaks the correlation is worse than a small one that holds it**; if the sign flips or the magnitude collapses, report it and revert.

**T1e — then, and only then, look at excess.** Race the three hybrids. Report whether they still all finish at +0.0% with identical routes. **Report the number you get, whatever it is.** A step size that is now provably above the floor and still produces no outcome difference is a real and reportable finding about the thesis — it is not a failure of this segment.

---

## T2 — `path_invalidated` has never been `True`. Make it, or kill it.

Entry 022's ruling. A field that has never once taken its other value has never had its wiring exercised: it could be permanently `False` through an inverted test or a wrong attribute and **nothing in 476 tests would say so.**

1. Find a scenario that forces the hybrid to genuinely lose a path — high `events_per_step`, `Severe`, many roads per break, a sparse graph, whatever it takes. `WALKTHROUGH.md` Part 10 exercise 2 is the shape of it.
2. Show `path_invalidated == True` in at least one recorded row, with the config that produced it.
3. Add a test that runs on that config and asserts the field can be `True` — **a test of a feature must run on data where the feature is active.**
4. **If you cannot make it `True` under any scenario, remove the field.** A permanently-false column in the observation is a rule-input that votes the same way forever, and no policy should be able to read it. Removing it is the correct outcome, not a failure — report it as such.

---

## T3 — The three defects in `test_the_allocation_view_is_a_labelled_gap_not_a_drawing`

From my review in Entry 022. Your other two replaced tests are approved as they stand; this one is not.

1. **The docstring asserts F7 as a live cause** — *"F7 leaves the prescheduled controller built with no arguments"*. **F7 was closed in segment 20 and the class was deleted.** The assertion is still correct but for a different reason: plain `hybrid` has no governor at all. Rewrite the docstring to say the true reason. This is the `model.js` phantom-comment defect, one file over.
2. **The failure message is stale** — *"this test is the reminder to build it"*. It has been built.
3. **`assert "arm.allocation.searched[t]" in app` is a source-text grep**, written in the same segment in which you concluded twice that a text grep was the wrong instrument. **Move it to `tests/js/` as a render assertion**: drive the harness one step, read what the bar actually draws, compare it against the recorded `searched` series. That is the same defect (F1 in the view layer) caught by measurement rather than by substring.

---

## T4 — Run the automatable half of `WALKTHROUGH.md`

Every check in Parts 0–9 that has a command rather than a dashboard action. For each: **paste the command, paste the real output, and say whether it matches what the document predicts.** Where it does not match, the document is wrong or the system is — say which.

**Do not fix the document to match the system without telling me which one you changed.** `WALKTHROUGH.md` is what Rudra verifies against by hand; a document quietly edited to agree with the code is worse than no document.

---

## T5 — Part 10, exercises 1–6, automated

The predict-then-check exercises, run as scripts. Exercise 7 is T6 below.

Exercise 5 (**kill `_evaporate`, watch the trust report read 0.00, put it back**) is the one that matters most — it is the only place a human sees the instrument report a failure. **Confirm it still works after the restructure**, and paste the report both ways.

For 1, 3 and 4: calm-preset stability, a different seed, and **byte-identical reproduction across a server restart**. Exercise 4's restart half is the one most likely to have rotted.

---

## T6 — **Exercise 7 predicts behaviour the system does not have. I wrote it wrong.**

`WALKTHROUGH.md` Part 10 exercise 7 says:

> **Predict:** the fraction sits near its start, jumps when a disruption lands, and **drifts back during calm.**

Segment 21 measured: mean change on a disruption step **−0.001000**, on a quiet step **−0.000133**. **Both negative.** The split does not drift back during calm — it drifts the *same direction*, slower, because the baseline EMA decays the pressure rather than reversing it. My prediction describes a mean-reverting controller. This one is not mean-reverting.

Worse: the exercise ends *"If the adaptive line is flat, stop and tell me"* — and at `sigma = 0.001` the line **is** visually flat. **Rudra would correctly follow my instruction and report a failure that is a step-size artefact.**

1. Rewrite exercise 7 to predict what the mechanism actually does, at the `sigma` T1c settles on.
2. State plainly in it what a *real* failure looks like versus a small-but-working one, so the distinction is available to someone who has not read Entry 022.
3. Check the rest of `WALKTHROUGH.md` for the same class of error — **any prediction I wrote that the measured system does not produce.** I wrote 843 lines of it from a model of the system, and this is the first place that model has been caught diverging from the system. It is unlikely to be the only one. **List every one you find, even if you are not sure.**

---

## T7 — Part 12, the combination sweep

Four models × four size presets × four disruption scenarios, the eight numeric edges, and the six sequence tests. Automate it. **A table of pass/fail is not enough** — for every failure, say whether it is a crash, a wrong answer, or confident nonsense, because those are three different problems and only one of them is loud.

Record the timing table. Segment 24 runs the real experiment and needs to know what it costs before it starts.

---

## T8 — Mutations, two, one of them yours

As always. One I specify, one you choose.

**Mine:** in `IncrementalAllocation.propose`, change `self._baseline += self.baseline_alpha * pressure` to `self._baseline = reading`. The baseline now tracks the signal exactly, so pressure is always the difference between a reading and itself one step later rather than a decayed history. **The arm still adapts and still correlates with recency.** Predict what breaks before you run it, then run it.

**Yours:** pick something T1 through T7 would catch and the existing suite would not. Say what you expected and what happened. **If it passes everything, that is the finding** — write it up as one, the way you did with mutation B.

---

## T9 — Tests

Every measurement in T1, T2 and T6 that will still be true next month becomes a test. The one-off diagnostics stay as scripts.

**The judgement call, stated:** T1's floor is a property of the system (`sigma` above `1/budget`), so it is a test. T1a's specific distinct-value counts are a snapshot, so they are a script. Get this line right and say where you drew it.

---

## T10 — Show it

Paste verbatim:

- **T1's four numbers** — declared distinct, realised distinct, declared distance, realised distance — at all three budgets
- **The `sigma` you set and the derivation, in the order you did it**
- **`verify_arms.py` at the new value, all four arms**
- **Excess for the three hybrids at the new value** — whatever it is
- `path_invalidated == True` with its config, **or your case that it cannot be**
- The trust report with `_evaporate` killed and restored
- Every `WALKTHROUGH.md` mismatch, and which side you changed
- **Every wrong prediction you found in `WALKTHROUGH.md`**
- Both mutations, shown red
- The sweep table and the timing table
- **Your read: is Claim 3 arguable from what this system now produces?** Not whether it is true — whether the evidence exists to argue it either way.

---

## T11 — Hand over, do **not** commit

`git status --short`, unstaged. The commit message as a fenced block, no `Co-Authored-By`. FINDINGS appended below. Say plainly that it is complete and uncommitted.

---

## Constraints

| | |
|---|---|
| **No statement ceiling.** Report the count. | |
| **Do not look at excess until `sigma` is fixed** (T1c before T1e) | |
| **Every test calls the production entry point** | |
| **A test of a feature runs on data where the feature is active** | |
| **Do not edit `WALKTHROUGH.md` to agree with the code without saying so** | |
| **Do not commit, do not push** | |

---

## Acceptance check

```bash
git diff --stat -- src/ tests/ dashboard/ scripts/
./.venv/bin/pytest
node --test tests/js/*.test.mjs
./.venv/bin/ruff check src/ tests/ dashboard/ scripts/
./.venv/bin/pytest -k "statement" -q -s          # reports, never fails
git status --short                                # UNSTAGED, UNCOMMITTED
```

---

## Definition of done

`sigma` settled by measurement with its derivation recorded in the order it was made · `path_invalidated` demonstrated or removed · the three T3 defects closed · every automatable `WALKTHROUGH.md` check run with real output · every wrong prediction in it found and listed · both mutations shown red · green suite · uncommitted with the message pasted · FINDINGS appended.

**Segment 22 is Rudra verifying the rest by hand.** What you leave unchecked here, he checks himself — so leave nothing checkable.

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->

## FINDINGS — Segment X (first pass: T0–T3, T8, T9)

**Status:** PARTIAL — T1, T2, T3, T8, T9 complete. T4–T7 are a second pass.

Banked deliberately: T1 changes what the project believes about its own
mechanism, and that should not sit uncommitted behind the walkthrough
automation.

### T0 — both surfaces

| | Before | After |
|---|---|---|
| Python suite | 476 passed | **483 passed** (97.4s) |
| JS suite | 50 passed | **52 passed** |
| `src/` statements | 2163 | **2167** — reported, no ceiling |
| `ruff check src/ tests/ scripts/ dashboard/` | clean | clean |

### T1a/T1b — the step size, measured

```
 budget   1/budget  sigma>floor  declared  realised   moved  followed   decl dist  real dist
            (floor)              distinct  distinct   steps               (evals)    (evals)
    300     0.0033           no        17         6      57        15        17.1       15.0
   1000     0.0010           no        17        17      57        57        57.0       57.0
   2000     0.0005          YES        17        17      57        57       114.0      114.0
```

Per-budget detail, same run:

```
budget  300: declared 0.5000 -> 0.4910   realised 150 -> 147   levels [145..150]
budget 1000: declared 0.5000 -> 0.4910   realised 500 -> 491   levels [484..500]
budget 2000: declared 0.5000 -> 0.4910   realised 1000 -> 982  levels [968..1000]
```

**Entry 022's mechanism is confirmed exactly; its conclusion was too
strong, and the Architect has since corrected the entry.** The
budget-dependence is precisely as derived — below the floor the realised
split takes 6 distinct values against the 17 requested and follows only
15 of 57 requested moves; at and above the floor it follows 57 of 57.
The predicted transition appears exactly where the arithmetic puts it.

But the realised split was **not** frozen: it travelled 15.0 evaluations
and moved 150 → 147. **Below the floor the mechanism loses resolution; it
does not stop.** "It moves by zero" was the one part that did not survive
measurement.

**The constraint that actually binds is Reach, not Floor — and it binds
at every budget.** The declared fraction travelled 0.057 in total
variation but only **0.009 net**: 84% of the movement cancels. The
identical declared trajectory at all three budgets is the giveaway —
`sigma` is a fraction, so raising the budget fixes the quantisation and
changes the declared path not at all. Even at budget 2000, where tracking
is perfect, the split moves 1000 → 982: **1.8% of the budget.**

### T1c — the value, and the derivation, in the order it was done

`IncrementalAllocation.sigma`: **0.001 → 0.006.** Excess was not looked at
until after this was fixed; the three constraints come from the budget and
the scenario length alone.

| Constraint | Source | Value |
|---|---|---|
| Floor | one step must move ≥ 1 evaluation | 1/300 = 0.0033 |
| Ceiling | the governor's rate limit | `sigma_max` = 0.05 |
| Reach | half the distance to a bound over the ~37 of 60 steps it moves | 0.225/37 ≈ 0.0061 |

**I did not set it to the value that would produce the Reach row's *realised*
displacement.** With 84% cancellation, hitting a net 0.225 would need
sigma ≈ 0.025. That number is derived from one run's measured cancellation
ratio, which is fitting the constant to observed behaviour — the practice
this derivation exists to avoid. 0.006 is what the three
fixed-in-advance constraints give on the "able to reach" reading, and the
shortfall is reported rather than engineered away.

**`ControlCfg.sigma` was NOT changed, against the letter of the spec.**
It feeds only `IncrementalController`, which adapts ρ for `aco_adaptive`
— Claim 2's settled evidence set (§8). ρ is continuous with no quantum,
so the budget-derived floor does not apply to it, and Entry 022's own
argument says 0.001 is correct there. Raising it would have moved Claim
2's evidence to fix Claim 3's. Added `ControlCfg.allocation_sigma = 0.006`
and wired it through `_make_governor` instead, so the allocation step is
configurable without touching ρ. **The Architect has since confirmed this
was the right call.**

The kwarg is passed by asking the policy whether it takes one
(`signature(...).parameters`) rather than matching policy names: `frozen`
has no step size by definition and `scheduled` derives its own from its
endpoints, and a hardcoded name list would silently stop covering the
next policy added.

### T1d — all four arms at the new value

```
1. Fixed / Static Hybrid      distinct 1, all exactly 0.5          UNCHANGED
2. New Recency-Based Adaptive Hybrid
   corr(recency, change) = -0.776                                  UNCHANGED
   mean change, disruption step: -0.006000   (was -0.001000)       x6
   mean change, quiet step:      -0.000800   (was -0.000133)       x6
3. Scheduled Hybrid           identical in quiet and violent worlds UNCHANGED
4. ACO frozen vs adaptive rho: 1 vs 28 distinct                     UNCHANGED
```

The correlation is **identical**, as it must be — `sigma` scales every
step uniformly and correlation is scale-invariant. Both means scaled by
exactly 6. The ACO pair is untouched, which is the check that `ControlCfg.sigma`
really was left alone.

### T1e — excess, after the value was fixed

```
                    seed 1000    mean of 6 seeds
hybrid_fixed           1.678%          8.651%
hybrid_adaptive        0.659%          7.864%
hybrid_scheduled       1.538%         11.360%

routes differing from hybrid_fixed, seed 1000:
  hybrid_adaptive     32/60 steps        hybrid_scheduled  36/60 steps
```

At the old value all three arms finished with **identical routes**. They
no longer do: the allocation is now changing the search, which is the
thing that was missing.

**The paired analysis, corrected.** The arms see an identical world by
§10.2 guarantee 1, so the per-seed differences are paired and the spread
of the *levels* is the wrong denominator. I used it in my first report;
the Architect caught it.

```
paired differences (fixed - adaptive), pp:
  [1.019, 2.782, 3.169, -0.207, -2.678, 0.636]
  n=6   mean +0.787pp   paired SD 2.132   SE 0.870   t +0.90
  95% CI [-1.451, +3.024]   crosses zero
  wins 4/6

  wrong denominator (SD of levels):      4.110pp
  right denominator (SD of differences): 2.132pp
```

The conclusion is unchanged but the reasoning was wrong: the effect is
**0.37 paired SD**, and the interval crosses zero. Not "inside the noise"
as asserted from the levels — undetermined, on the correct denominator.

**Six seeds could never have answered this.** A two-sided Wilcoxon
signed-rank test at n=6 has a floor of p = 2/2⁶ = **0.031 even at 6/6
wins**, so the design had no power to reach significance regardless of
outcome. Reporting 4/6 as evidence either way was not available.

**Seed-count recommendation, carried to segment 23**, from the paired SD
of 2.132pp and the observed +0.787pp effect:

| Power | Seeds |
|---|---|
| 80% | **58** |
| 90% | **78** |

D5/D9's ≥100 trials clears both. That is worth stating positively: the
planned evidence run is adequately powered for an effect of this size,
and this is the first time that has been checked against a measured
variance rather than assumed.

### T2 — `path_invalidated` is real; the field stays

Found by search, not by argument. At the default scenario the hybrid
never loses a route in 60 steps, which is how the field went unexercised.

```
       graph  nodes   dens  events  clust  budget  invalid   of
   geometric    200  0.040     0.8     25     300        0   40   <- default-ish
   geometric    200  0.020     2.0     60     300        3   40
   geometric    150  0.015     3.0     80     200        3   40
```

**And it means what its name says.** A `True` only ever at t=0 would be
"no route found yet", a different claim. Searching for a `True` that
*follows* a `False` found genuine losses across many seeds:

```
  seed 1000 n=150 d=0.015 ev=3.0 cl=80: route LOST at steps [5]
  seed 1000 n=250 d=0.018 ev=2.5 cl=70: route LOST at steps [3]
  seed 1002 n=250 d=0.018 ev=2.5 cl=70: route LOST at steps [8, 10]
  seed    7 n=200 d=0.02  ev=2.0 cl=60: route LOST at steps [4, 23]
```

Verified end to end through `observe()`: `observation.path_invalidated =
True`, `best_cost = None`. Two tests added on the severe config, so the
field is now exercised on data where it is active.

### T3 — the three defects, all three fixed

1. **Docstring asserted F7 as a live cause.** Rewritten to the true
   reason: plain `hybrid` has no signal, controller or governor at all
   (§9), so nothing in the system *can* move its fraction. It is not a
   controlled arm whose controller is broken. Right answer, retired
   explanation — the `model.js` defect one file over, as diagnosed.
2. **Stale failure message** ("the reminder to build it") replaced with
   what a failure would now mean: an arm with no allocation machinery has
   acquired some, or a governed arm's state is leaking into it.
3. **The source-text grep is gone**, replaced by a render assertion in
   `tests/js/app.test.mjs` ("the allocation bar, rendered"). It drives the
   real page through the existing harness, reads the width the bar
   actually draws, and compares it to the recorded `searched` series. The
   fixture is a **real recorded race**, not hand-written numbers, in which
   `searched` and `applied` differ at 58 of 60 positions. Shown failing
   with `applied` substituted:

   ```
   not ok 1 - the bar shows the split the step searched with, not the one it decided
     error: 'at t=2 the bar drew 49.4% but the step searched with 50%'
   ```

   A second test varies the cursor, because the first cannot see a
   renderer that ignores `t` and happens to agree.

**A fourth, found on the way.** `test_the_governor_is_the_only_thing_that_enforces`
greps `policies.py` for `sigma_max` — and fired on the new derivation
docstring, which names `sigma_max` as the ceiling it must stay under.
Prose about the guard, read as a violation of it. **Third text-grep false
positive in two segments.** Converted to the same AST walk.

### T8 — both mutations

**Specified** — `self._baseline = reading` in `IncrementalAllocation.propose`.

*Predicted:* pressure becomes a one-step difference; recency jumps on an
event and decays between, so pressure is negative on most steps and the
arm drifts the other way with the correlation flipping.

*Actual:* **the correlation did not flip — it got stronger, −0.798 against
−0.776 — and all 476 tests passed.** What changed is the quiet-step
behaviour: +0.005600 against the real arm's +0.000383. The mutant moves
just as hard during calm as during disruption, oscillating around its
start instead of reallocating.

**The correlation cannot tell them apart**, because both move in step with
recency. My prediction was right about the mechanism and wrong about which
statistic would show it.

**And the mutant is what `WALKTHROUGH.md` exercise 7 predicts** — "jumps
when a disruption lands, and drifts back during calm". The document
describes a mean-reverting controller; the real one is not mean-reverting;
the mutation makes the system match the document. Direct evidence for T6,
found before T6 was started.

Caught by response ratio, measured over four seeds — real ~13×, mutant
~1× — with the threshold at 3, inside the gap and stated as qualitative.

**Mine** — `_make_governor` passing `control.sigma` instead of
`control.allocation_sigma`. A one-word slip of exactly the kind a
two-field split invites, silently returning every config-built arm to the
inert regime this segment exists to leave.

*Predicted:* survives, because the step-size tests read the dataclass
default. *Actual:* **survived all 479 tests.**

Every T9 assertion read `IncrementalAllocation().sigma`, which the
mutation does not touch. **Entry 019's rule — every test drives the
production entry point — broken inside the tests written to enforce it.
A default is not a wiring.** Now read off an arm from `build_arms`, and
the config is varied to prove the test reads the wiring rather than a
constant that agrees with it.

### T9 — where the line was drawn

**Tests** (properties that hold next month): the floor (`sigma > 1/budget`
at the default budget), the ceiling (`sigma < sigma_max`), ρ's step size
held separate from allocation's, the response ratio, and the built arm
carrying the configured value.

**Scripts** (snapshots of one seed and scenario): the distinct-value
counts, the per-budget tracking table, the cancellation ratio. These are
in `scripts/measure_step_size.py` and asserted nowhere.

### The 84% cancellation — a control-loop finding, and a pre-registered criterion

Stated before any measurement, per the Architect's instruction, and **not
acted on in this segment.**

The policy's declared path travels 0.057 in total variation to achieve
0.009 net. Two parameters could plausibly address it — `deadband`
(currently 0.0, so *every* non-zero pressure moves the split, including
baseline-chasing during calm) and `adapt_every` (currently 1).

**The criterion is defined on the control signal, not on excess:**

1. **Reversal rate** — the fraction of adaptation steps whose direction
   opposes the previous step's. An unbiased walk sits at 0.5. Target:
   **below 0.35.**
2. **Response ratio** — |mean move on a disrupted step| / |mean move on a
   calm step|, already measured and tested at ~13. Target: **it must not
   fall.**

A change is justified only if it lowers reversal rate without lowering
response ratio. **Excess is not an input to this decision**, and no excess
figure will be consulted while choosing the values. Proposed for segment
23; deliberately not done here.

**Files changed**
- `src/dynaswarm/allocation/policies.py` — `sigma` 0.001 → 0.006 with the
  derivation and its provenance; the refutation recorded beside it
- `src/dynaswarm/config.py` — `ControlCfg.allocation_sigma`, and why it is
  not `sigma`
- `src/dynaswarm/harness/arm.py` — governor wired to `allocation_sigma`,
  kwarg passed by signature rather than by policy name
- `tests/test_allocation.py` — T2, T9, both mutation guards; the AST fix
- `tests/test_dashboard.py` — T3.1, T3.2, T3.3
- `tests/js/app.test.mjs` — the render assertion
- `dashboard/static/app.js` — unchanged in effect (mutation reverted)

**Files added**
- `scripts/measure_step_size.py` — T1a/T1b
- `tests/js/fixtures/race_allocation.json` — a real recorded race

**Deviations from spec**
1. **`ControlCfg.sigma` deliberately not changed** — see T1c. Confirmed
   correct by the Architect after the fact.
2. **T1c's value is 0.006, not the ~0.025 that the Reach row's realised
   target implies.** Reasoned above; the shortfall is reported.

**Surprises**
1. **"Provably inert" was not what the measurement showed** — quantised,
   not stopped. Recorded because the difference matters: a mechanism that
   loses resolution still moves, and an argument that predicted zero would
   have been refuted by a single realised series.
2. **The specified mutation strengthened the headline statistic.** Any
   report that leans on the recency correlation alone cannot distinguish
   the real policy from one that reallocates nothing.
3. **`WALKTHROUGH.md` describes the mutant.** Found before T6 began.
4. **My own tests asserted defaults rather than wiring**, and my own
   mutation is what exposed it.

**Could not do**

T4–T7 are the second pass. Nothing in T1–T3, T8 or T9 was blocked.

**Questions for the Architect**

1. **Seed count**: 58 for 80% power, 78 for 90%, from a paired SD of
   2.132pp. D5/D9's ≥100 clears both — confirm that is the number segment
   23 plans against.
2. **The cancellation criterion above** — approve, amend, or reject the
   two thresholds before segment 23 measures anything against them.
