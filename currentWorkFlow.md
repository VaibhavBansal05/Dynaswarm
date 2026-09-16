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

## FINDINGS — Segment Y

**Status:** COMPLETE. Uncommitted.

**Headline: the policy was built and it works as designed. Two of the three
things it was built to fix are not fixable at the policy layer, and the
measurement says so.**

### T0 — both surfaces

| | Before | After |
|---|---|---|
| Python suite | 486 passed | **491 passed** (98.0s) |
| JS suite | 52 passed | **52 passed** |
| `src/` statements | 2167 | **2180** — reported, no ceiling |
| `ruff` (src, tests, scripts, dashboard) | clean | clean |

---

### T1 — what the staleness signal costs, and the branch

#### T1a — the cost, measured by building it

The point is `aco.py:132`, `self._tau[~np.asarray(view.active)] = 0.0`.

**It is cheap, and cheaper than expected, for a reason worth recording.**
Mass on an inactive slot *is* this step's loss with no bookkeeping at all:
a slot deactivated earlier was already zeroed here, and the MAX–MIN clip
is `where=active`, so nothing puts it back. One sum, one division.

```
src/dynaswarm/optimizers/aco.py    6 statements (2167 -> 2173)
scripts/trust_report.py            1 row
files touched                      2
new plumbing                       none
```

No plumbing because `Hybrid.probe()` already prefixes its components'
fields, so `aco_trail_mass_lost` reaches the hybrid's probe for free.

Two things the build surfaced that reading would not have:

1. **The value cannot live in `_mech`.** `spend()` resets that dict
   wholesale and runs *after* `rebind`, so a value parked there is zeroed
   before anything can read it. It needs its own attribute.
2. **The first rebind reported 0.500 as damage.** The trail table starts
   uniform at 1.0 across *all* slots including inactive ones, so the
   opening rebind counted the initial inactive fraction as loss. Fixed by
   zeroing inactive slots at construction — behaviourally a no-op, since
   construction is masked by `active` and `rebind` would zero them on
   step one anyway.

And one cost that is a feature: `test_the_report_names_every_probed_mechanism`
failed the moment the probe existed. **A probe field that is not explained
in the trust report is telemetry nobody sees**, and the guard said so.

#### T1b — not oracle-derived

Computed from `self._tau` (ACO's own state) and `view.active` (the event
mask). No A\*, no `optimum`, nothing derived from either. The I1 AST check
over `observation.py` is untouched, because — see T1c — the field was
**not** added to the observation.

#### T1c — the architectural cost, named and then avoided

Adding `trail_mass_lost` to `AllocationObservation` would make one field
of a deliberately component-agnostic structure depend on how ACO stores
trails. **I did not pay that cost.** The field ships as ACO telemetry
only: it is on the probe and in the trust report, where it is evidence,
and no policy reads it. The coupling price is therefore currently zero,
and it becomes payable only if a policy is written that needs it.

#### T1d — the branch: **build on recency**

**The cost argument said staleness. The distribution said recency, and the
distribution wins.**

```
    seed  steps  disrupt   s>0  s>0|disrupt    max s  mean s|s>0
    1000     60       12     3         3/12   0.0200      0.0094
    1001     60       21     3         3/21   0.0040      0.0033
       7     60       11     3         3/11   0.0630      0.0229
      42     60       19     3         3/19   0.0966      0.0345

  pooled: 240 steps, 63 disrupted, 12 with any trail loss
  on a DISRUPTED step, s is zero 51/63 times
```

Two facts kill it as a drop-in `s`:

- **It is zero on 81% of disrupted steps.**
- **When non-zero it lives in [0, 0.1], not [0, 1].** Max across 240
  steps: 0.0966.

The commissioned form is `split = 0.5 + A × (0.5 − s)` with `s` on [0,1]
and 0.5 neutral. Feeding it a signal confined to the bottom tenth of that
range leaves `(0.5 − s)` in [0.4, 0.5]: the arm sits ACO-heavy
permanently and swings a tenth of its intended range. Making it usable
means rescaling, and **every available rescaling constant would be fitted
to the observed distribution** — which is the tuning this project's
credibility rests on not doing.

**The sparsity is not a defect in the signal. It is the signal being
right.** A disruption that destroys no pheromone genuinely invalidates
nothing, and `s = 0` correctly reports that ACO's knowledge is intact.
That is exactly the severity-awareness Entry 023 wanted — it is simply
not usable by a linear map that assumes the signal spans its range.

**Decision: recency now, staleness recorded as the named extension**, with
the probe shipped as its evidence base so the next segment starts from a
measurement rather than a proposal.

---

### T2 — `DirectAllocation`, arm `hybrid_direct`

```
split = 0.5 + amplitude * (0.5 - obs.recency)
```

Reads `obs.recency` and nothing else. **`obs.current_fraction` is
deliberately not read** — reading it is precisely how a direct rule
quietly becomes an incremental one. No curvature added: recency already
decays ×0.7 per quiet step, so a linear map on it is already exponential
in time.

---

### T3 — ⚠️ the rate-limit trap. It bit, hard.

**Measured before `A` was chosen, as instructed.**

`recency` jumps a **full 0 → 1.0** on the step a break lands — in every
seed and at every event rate tested (0.1, 0.3, 0.8), 12 runs, max
|Δrecency| = 1.0000 in all twelve.

```
  delta_split = A * delta_s, clamp binds when A > sigma_max / delta_s
  sigma_max = 0.05,  delta_s = 1.0   ->   A_max before clamping = 0.0500
```

**The clamp report, `hybrid_direct` at A = 0.6:**

```
    seed  steps  clamped    rate  mean |gap|  max |gap|     applied range
    1000     60       46   76.7%      0.1213     0.5381   [0.356, 0.788]
    1001     60       51   85.0%      0.1402     0.5442   [0.244, 0.794]
       7     60       40   66.7%      0.1215     0.5486   [0.406, 0.799]
      42     60       51   85.0%      0.1413     0.5154   [0.315, 0.765]

  pooled clamp rate: 78.3%
```

The step-by-step shape, which is the clearest statement of it:

```
    t   ev  recency  proposed  applied  searched  clamped
    2   25    1.000    0.2000   0.5500    0.6000      YES
    3    0    0.700    0.3800   0.5000    0.5500      YES
```

At t=2 the break lands, the rule correctly asks for 0.20 — and the
governor applies 0.55, *moving the split the wrong way* because it is
still crawling toward a target two steps stale.

**This is a finding about the governor, not the policy, and `A` was not
shrunk to hide it.** Stronger than that:

> **T4's three constraints are mutually unsatisfiable.** Reach demands
> A ≈ 0.6; the rate limit caps A at 0.05, which spans [0.475, 0.525] —
> 15 evaluations out of 300, and *less* range than the incremental arm
> already achieves. **There is no `A` that satisfies all three**, and
> that is a fact about `sigma_max` being a policy-shaped assumption
> living in the enforcement layer.

`sigma_max = 0.05` is coherent for an *integrator*, where it bounds how
fast accumulated error moves things. For a rule whose entire purpose is
to be in the right place immediately, it is a contradiction of the design.
**I have not changed the default** — that is the governor's contract and
it is the Architect's. Both behaviours are measured and reported below.

---

### T4 — `A = 0.6`, derived before any excess was seen

| Constraint | Source | Value |
|---|---|---|
| Floor | one full swing must move whole evaluations, `1/budget` | 0.0033 |
| Ceiling | both ends inside the governor's `[0.05, 0.95]` | 0.9 |
| Reach | the two ends must be meaningfully different searches | **0.6** |

**Reach is not a taste judgement.** `ScheduledAllocation` already sweeps
0.8 → 0.2, so A = 0.6 makes this arm cover *exactly the span the
project's own open-loop control covers*. That matters for the ablation:
the scheduled arm exists to kill "any movement helps, sensing is
irrelevant", and that comparison is only fair if both arms can reach the
same places and differ solely in what drives them.

Excess was not looked at until after this was fixed.

---

### T5 — does the arm do what its name says?

**(a) Responds on the step the break lands — yes.** Recency → 1.000 and
the proposal → 0.2000 in the same row, not the next one.

**(b) Scales with severity — NO.**

```
      distinct disruption sizes in this run: [9, 25]
      proposed displacement at each: [0.3]
```

Nine roads and twenty-five roads produce **identical** displacement. The
cause is upstream of the policy: `RecencySignal.observe` is
`self._value = 1.0 if obs.n_events > 0 else ...` — **recency is binary on
arrival.** A direct *shape* cannot recover a magnitude the *signal* has
already discarded.

So of the two pathologies Entry 023 named, the redesign addresses one.
Severity-blindness is a property of the signal layer, and the only
candidate replacement is the staleness signal T1 measured as unusable.
**Neither signal currently available supports a severity-aware allocator**
— that is the segment's most consequential finding and it is a finding
about signals, not policies. Pinned in
`test_the_direct_arm_is_severity_blind_because_recency_is`, which fails
the day recency changes.

**(c) Cancellation — and the specified metric is the wrong instrument
here.**

```
      New Recency-Based Adaptive Hybrid  applied  0.158   proposed  0.172
      Direct Recency Hybrid              applied  0.008   proposed  0.032
```

Reported plainly as asked: **the direct arm cancels 99.2%, worse than the
incremental arm's 84%.**

But net-over-total-variation measures whether movement *accumulates*, and
a memoryless rule is not supposed to accumulate. A direct policy tracking
a signal that rises and decays *must* return to where it started when the
world calms — that is the design working, not waste. The metric diagnosed
a real pathology in the integrator and diagnoses nothing here.

**The instrument that does apply is whether the split is in the right
place at each moment**, and on that the two arms separate decisively:

```
corr(aco_fraction, recency) — NEGATIVE is correct (high recency -> favour PSO)
    seed   incremental    direct  direct unltd     calm-vs-post gap
    1000         0.145    -0.196        -0.372   inc -0.012  dir +0.043
    1001         0.034    -0.339        -0.575   inc -0.001  dir +0.135
    1002         0.157    -0.076        -0.198   inc -0.016  dir +0.064
       7         0.002    -0.279        -0.589   inc -0.004  dir +0.039
      42        -0.201    -0.178        -0.480   inc +0.023  dir +0.071
    9999        -0.230    -0.367        -0.527   inc +0.011  dir +0.112

  incremental        mean corr -0.016   negative on 2/6 seeds
  direct             mean corr -0.239   negative on 6/6 seeds
  direct unlimited   mean corr -0.457   negative on 6/6 seeds

  calm-minus-post gap (positive = correctly ACO-heavy in calm):
  incremental        mean +0.0001   positive on 2/6 seeds
  direct             mean +0.0774   positive on 6/6 seeds
```

**This is the sharpest available statement of the integrator pathology,
and it revises how segment 21's headline should be read.** That segment
reported `corr(recency, change in fraction) = −0.776` and it is correct.
But `corr(recency, fraction)` — the *level*, which is what determines
what search actually runs — is **−0.016, and the right sign on only 2 of
6 seeds.** Its calm-versus-disrupted gap is +0.0001: zero to four decimal
places.

**The incremental arm moves in the right direction and ends up nowhere in
particular.** The direct arm is correctly placed on 6 of 6 seeds.

**(d) The other arms are unchanged.** `hybrid_fixed` still 1 distinct
value at exactly 0.5; adaptive and scheduled series identical to segment
21's; the ACO ρ pair untouched.

---

### T6 — excess, after `A` was fixed

```
    seed     fixed  adaptive  scheduled   direct
    1000     1.678     0.659      1.538     1.671
    1001    11.910     9.129     22.161    14.972
    1002    10.812     7.644      9.236     8.310
       7     4.749     4.956      5.354     5.614
      42     9.461    12.139     12.911     9.074
    9999    13.295    12.659     16.960    16.113

  hybrid_fixed      8.651%     hybrid_scheduled  11.360%
  hybrid_adaptive   7.864%     hybrid_direct      9.292%

  direct vs its ablation twin (fixed - direct), paired:
    per seed [0.007, -3.062, 2.503, -0.865, 0.386, -2.818]
    mean -0.642pp  paired SD 2.098  SE 0.856  t -0.75
    95% CI [-2.843, +1.560]   wins 3/6
```

**The better-positioned allocator does not produce a better outcome.** It
is 0.642pp *worse* than its twin on average, three wins in six, interval
comfortably crossing zero.

Because 78% of its moves are clamped, that could have been the governor
masking the policy. It is not — the same comparison with the rate limit
lifted:

```
  fixed 8.651%   direct (sigma_max=1.0) 9.876%
  paired: mean -1.225pp  SD 4.049  t -0.74  CI [-5.475, +3.025]  wins 4/6
```

No improvement either way, and the unclamped arm's variance is **twice**
the clamped one's — a full-swing allocator is a higher-variance strategy
before it is a better one.

---

### T8 — both mutations. **Both of my predictions were wrong.**

**Specified** — invert the sign: `0.5 + A × (recency − 0.5)`.

*Predicted:* span, centre and purity tests all pass; only a directional
correlation catches it.
*Actual:* **caught immediately** by
`test_the_direct_split_spans_the_amplitude_and_centres_on_a_half`, which
asserts `s=0 → 0.5 + A/2` specifically rather than asserting a span.

**But the prediction was right about everything else, and that is the
finding.** Of the five tests covering this policy, **only that one**
caught it. Purity passed. The floor/ceiling derivation passed. The
severity test passed. The clamp-rate test passed. *A policy allocating
exactly backwards satisfies every behavioural test in the suite* — being
wrong-way-round is invisible to anything that does not check direction at
a known point.

**Mine** — wire `hybrid_direct` to `signal="volatility"` instead of
`"recency"`, leaving the policy untouched.

*Predicted:* survives everything, because every unit test constructs its
own observation and never exercises the wiring. Segment 21's mutation B
shape.
*Actual:* **caught**, by the clamp-rate test — 30% against the required
>50%, because a windowed rate signal does not jump 0→1 the way a
transient does.

That test was written to guard a property of the *governor* and caught a
defect in the *signal wiring*, which is the reach a behavioural test has
and a unit test does not.

**It also exposed a defect in my own error message.** It confidently
listed two causes — "`sigma_max` was raised or the amplitude was lowered"
— and the actual cause was neither. A message that enumerates causes and
omits the real one sends the next reader down two dead ends with
confidence. Rewritten to name all three, with the measured 30% figure and
the instruction to check the signal first.

---

### The §9 row I would like

Yours to accept or rewrite; I have not touched `ARCHITECTURE.md`.

| Code id | Display name | Family | Signal | Control | Metered | Role |
|---|---|---|---|---|---|---|
| `hybrid_direct` | **Direct Recency Hybrid** | `hybrid_controlled` | recency | `DirectAllocation` | yes | **kills "the response shape doesn't matter"** |

---

### Is the new arm a better instrument for Claim 3, on the evidence?

**Yes, and not marginally — on the measurement that decides what search
actually runs.**

The incremental arm's split level correlates with recency at **−0.016**,
with the correct sign on **2 of 6 seeds**, and a calm-versus-disrupted gap
of **+0.0001**. As an allocator it is, at the level of where the split
actually sits, doing nothing directional. Its −0.776 figure is real but is
a correlation of the *increments*, and increments in the right direction
do not imply a position in the right place — which is exactly what an
integrator fails at and exactly what Entry 023 predicted from first
principles before any of this was measured.

The direct arm is correctly placed on **6 of 6 seeds**, on both
measurements, clamped or not.

**Three things must be said against it, and they are not small:**

1. **It is still severity-blind**, and cannot be fixed at this layer.
2. **It produces no outcome benefit** — −0.642pp clamped, −1.225pp
   unclamped, neither close to significant, no hint of a positive effect.
3. **It is clamped on 78% of steps** by a rate limit that cannot
   coexist with any useful amplitude.

So the honest verdict is: **a better instrument, not a better result.**
Which is worth having, because Claim 3 can now be argued against a
well-positioned allocator rather than against one that was never in the
right place — and a null result from this arm means something, where a
null result from the incremental arm was confounded with its own
positioning failure.

**My read on the thesis, stated plainly:** two arms now allocate by
recency, one of them demonstrably correctly, and neither beats a fixed
50/50 split at n=6. That is not yet evidence against Claim 3 — the
intervals are far too wide — but it is the second independent arm to show
no effect, and the planned 100-seed run should be read with the
possibility of a genuine null firmly in view. Entry 023's framing already
covers this: a bound is a result.

---

**Files changed**
- `src/dynaswarm/optimizers/aco.py` — staleness probe; inactive slots zeroed at construction
- `src/dynaswarm/allocation/policies.py` — `DirectAllocation`, registry, `__all__`
- `src/dynaswarm/allocation/__init__.py` — export
- `src/dynaswarm/harness/arm.py` — `hybrid_direct`
- `scripts/trust_report.py` — the `trail_mass_lost` row
- `scripts/verify_arms.py` — T5's four artefacts
- `tests/test_allocation.py` — five tests

**Deviations from spec**
1. **T1 chose recency over staleness**, against the cost framing's
   expectation. The plumbing was cheap; the distribution was not usable.
2. **T5's severity requirement cannot be met** and is pinned as a
   limitation rather than faked as a passing test.
3. **T5's cancellation metric is reported as asked and then argued
   against** — the number is 0.008 and I do not think it means what it
   means for the integrator.

**Surprises**
1. **The incremental arm's split level is uncorrelated with its signal.**
   Not a small effect — the right sign on 2 of 6 seeds.
2. **The first rebind counted initialisation as damage** (0.500), found
   only by printing the series rather than trusting the derivation.
3. **A backwards policy passes every behavioural test.** Direction is
   invisible to anything that does not check it at a known point.
4. **My clamp-rate test caught a signal-wiring defect** it was not
   written for, and its error message named the wrong causes.

**Questions for the Architect**

1. **`sigma_max` and direct policies are incompatible.** Raise it, make it
   per-policy, or accept the clamp as the arm's shipped behaviour? I have
   changed nothing and measured all three.
2. **Severity needs a signal, not a policy.** A `severity` signal — events
   scaled by a fixed reference, not a fitted one — is the smallest thing
   that would let this arm do what it was commissioned to do. Worth a
   segment before the freeze, or after?
3. **The §9 row above.**
