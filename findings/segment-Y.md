# FINDINGS — Segment Y

> Archived from `currentWorkFlow.md` by the Architect, 17 Sept 2026.

---

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
