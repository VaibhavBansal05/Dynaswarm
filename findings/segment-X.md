# FINDINGS — Segment X

> Archived from `currentWorkFlow.md` by the Architect, 16 Sept 2026. Two passes: the first banked T0–T3, T8, T9 because T1's measurement changed the project's own beliefs; the second covers T4–T7.

---

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

## FINDINGS — Segment X (second pass: T4–T7)

**Status:** COMPLETE. Both passes done; the segment is finished and uncommitted.

### T0 — final surfaces

| | Start of segment | End |
|---|---|---|
| Python suite | 476 passed | **486 passed** (99.2s) |
| JS suite | 50 passed | **52 passed** |
| `src/` statements | 2163 | **2167** — reported, no ceiling |
| `ruff` (src, tests, scripts, dashboard) | clean | clean |

### T4 — the walkthrough's commands, run

| Check | Result |
|---|---|
| Stop 1 — RNG streams | **matches exactly**: two identical arrays, third different |
| Stop 2 — graph build | **byte-identical to the document**, `99.9633 in 11 hops`, 735 roads |
| Stop 4/5 — suites | green |
| Stop 7 — `load_steps` over `outputs/` | **matches**: 14,160 rows, all `exploratory`, no `manifest` |
| Stop 6 — trust report | runs; every mechanism reports live |

**Two real defects found, and a third the Architect ruled on.**

#### Defect 1 — the dashboard's seed box never reached the race

`WALKTHROUGH` Part 10 exercise 3 promises "completely different map,
completely different breaks, different numbers throughout". It did not
happen. **Two different seeds produced byte-identical excess for all four
arms.**

`trial.py:135` builds the graph from the per-trial *evaluation* seed.
`race_config` set `ExperimentCfg(arms=..., n_trials=1, parallel_jobs=1)`
and never passed `spec.graph.seed` anywhere — so **every race the
dashboard has ever run used the default eval seed**, whatever was typed.
The page's own reference card promises "One seed, one run. The seed fixes
the world *and* its sequence of breaks."

Fixed by passing `eval_seeds=[spec.graph.seed]`. Note that setting
`root_seed` instead — the obvious-looking fix — would have changed the
manifest and changed nothing that runs.

```
before:  graph_id seed 1000: 1e06d1c7b60e   seed 2024: 1e06d1c7b60e   different map: False
after :  graph_id seed 1000: efc1c968922f   seed 2024: 2bf87371a8ba    different map: True
```

The test asserts `optimum` differs, not the id — a differing id proves
only that the id is a function of the seed.

#### Defect 2 — the provenance caption named a world nobody raced

`read_run` computed `graph_id` from `manifest["config"]["root_seed"]` (42
at the defaults) while the graph was built from the eval seed (1000). The
dashboard prints that id beside a **correct** `seed` field, so the two
halves of one provenance line disagreed and neither looked wrong alone.
Now derived from the recorded seed; `graph_id` for seed 1000 matches the
world the browser draws.

#### Defect 3 — the HTTP boundary dropped unknown fields silently

Found by making the mistake. I called `RaceSpec(seed=2024)` — where
`seed` belongs under `graph` — and pydantic **silently dropped it**, so
the race ran the default world and I very nearly reported exercise 3's
failure before re-reading my own request. `RaceSpec(nonsense_field=99)`
was accepted too.

Per the Architect's ruling, fixed now rather than deferred with Q3: a
browser posts JSON here, so a typo runs a different experiment in silence
and returns a well-formed result with a run id. `extra="forbid"` on
`RaceSpec`, `GraphSpec` and `ScenarioSpec`.

```
{"graph":{"sead":2024}}  ->  422  extra_forbidden  loc: ["body","graph","sead"]
a full browser-shaped POST -> 200
```

**It immediately caught a live bug in my own segment-21 test**, which
passed `RaceSpec(..., timesteps=25)` flat. That had been silently dropped,
so the test had been running 60 steps while its name and its argument both
said 25. Nested properly.

### T5 — Part 10, exercises 1–6

| # | Result |
|---|---|
| 1 | Calm: optimum never moves; A\*, ACO, PSO each settle. **The Hybrid does not** — see T6 |
| 3 | Passes **after defect 1 was fixed**; different map, different numbers |
| 4 | Same process: identical. **Across three separate OS processes: identical** |
| 5 | **Works.** Killing `_evaporate` flips the report to `INERT 0.00 — evaporation off` |
| 6 | Extremes: see T7's sweep — all clean, no confident nonsense |

Exercise 4's restart half, the one flagged as most likely to have rotted:

```
process 1  graph=efc1c968922f  sha256=a142ce543232032c684b6adec28ac36ea86f23ea2c42b81ed7c81f1c6ab7cb3a
process 2  graph=efc1c968922f  sha256=a142ce543232032c684b6adec28ac36ea86f23ea2c42b81ed7c81f1c6ab7cb3a
process 3  graph=efc1c968922f  sha256=a142ce543232032c684b6adec28ac36ea86f23ea2c42b81ed7c81f1c6ab7cb3a
```

Exercise 5, both ways:

```
killed:    trail mass removed by evaporation     0       0    INERT 0.00 — evaporation off
restored:  trail mass removed by evaporation   345.3   3.767  live  0.00 — evaporation off
```

### T6 — every wrong prediction found. There were three.

**All three are the same error: a prediction generalised from seed 1000.**

#### 1. Exercise 7 — the thesis (the one you flagged)

Rewritten. The document predicted a **mean-reverting** controller; this one
**ratchets**. Measured over eight runs (two horizons × four seeds):

```
   steps  seed   disruption       quiet    ratio       net     end
      40  1000    -0.006000   -0.000800      7.5   -0.0780  0.4220
      40  1001    -0.006000   +0.000400     15.0   -0.0420  0.4580
      40     7    -0.006000   +0.000909      6.6   -0.0060  0.4940
      40    42    -0.006000   -0.001385      4.3   -0.1140  0.3860
      60  1000    -0.006000   +0.000383     15.7   -0.0540  0.4460
      60  1001    -0.006000   +0.000462     13.0   -0.1020  0.3980
      60     7    -0.006000   +0.000500     12.0   -0.0420  0.4580
      60    42    -0.006000   +0.000000    999.0   -0.1140  0.3860
```

What is robust, and is now what the document predicts: the disrupted-step
move is **−0.006000 in every single run**, and the net is **always
negative** — it ends below 0.5 every time, between 0.386 and 0.494.

**What is NOT robust, and the document must therefore not claim:** the
*direction* of movement during calm. It is sometimes up, sometimes down,
and it flips with the horizon. My own two scripts disagreed on its sign
(−0.000800 at 40 steps, +0.000383 at 60) and I traced that before writing
anything — the scripts used different horizons. **Only the magnitude is
stable: calm movement is 4–16× smaller than disrupted movement.**

The rewrite states the old prediction, why it was wrong, exactly what to
expect, what a real failure looks like (four named cases), and — the part
that was missing — **what is small-but-working and must not be reported as
a failure.** The old text ended "If the adaptive line is flat, stop and
tell me", which at the old step size would have fired on a working system.

#### 2. Part 11's per-arm table — "ACO and Hybrid low single digits · PSO higher"

**True of seed 1000 and of no other seed tested.**

```
  seed  1000: ACO    2.93%  PSO   38.26%  Hybrid    0.52%
  seed  1001: ACO    8.06%  PSO   13.29%  Hybrid    8.19%
  seed     7: ACO   18.98%  PSO   11.05%  Hybrid   10.91%
  seed    42: ACO   28.84%  PSO   11.67%  Hybrid   18.26%
  seed  9999: ACO   13.76%  PSO   19.98%  Hybrid   22.50%
```

Wrong twice over: "low single digits" holds for the Hybrid in **two of
five** seeds, and **PSO is not reliably the worst** — at seeds 7 and 42 it
beats ACO comfortably. A reader following the old table would report a
healthy run as broken. Replaced with the measured table and the point it
makes: between-seed variation exceeds the differences between arms, which
is why the project commits to ≥100 trials. A\*'s `+0.0%` is the only hard
invariant on that page.

#### 3. Exercise 1 — "every arm's excess settles and stops moving"

A\*, ACO and PSO settle. **The Hybrid does not** — 2.06% at t=40, 0.96% at
t=59, still improving at the last step. It has two components and an
exchange, so it keeps finding small gains after the single-method arms
have stopped. Corrected with the reason, so a working Hybrid is not
reported as a fault.

**Checked and correct, left alone:** Part 12's "roads per break = 1 → the
optimum almost never moves" (measured: 0–1 moves in 39 transitions at
cluster 1, rising to 1.7 at cluster 25 — the clustering finding holds);
Stops 1, 2 and 7's outputs; the ledger; A\*'s `+0.0%`.

**In all three cases I changed the DOCUMENT, not the code**, and each
correction says so inline and names the segment.

### T7 — the combination sweep

`scripts/sweep_combinations.py`. Nineteen combinations, classified
crash / wrong answer / confident nonsense.

```
THE FOUR MODELS                     all ok    (geometric, grid, erdos_renyi, custom)
THE FOUR SIZE PRESETS               all ok    (30, 200, 1000, grid 400)
THE FOUR DISRUPTION SCENARIOS       all ok    (calm, light, moderate, severe)
THE EDGES OF THE NUMERIC FIELDS     all ok    (places=4, density 0.005 and 1.0,
                                               timesteps=1, breaks=0, cluster 1 and 100)
```

**No crashes, no wrong answers, and — the one that matters — no confident
nonsense.** The checks are not "did it return": A\*'s excess must be
identically zero, no row may be path-valid without a cost or costed
without a valid path, and no optimum may be non-positive.

The document names very-sparse graphs as the place a system invents a
route. It does not:

```
  density 0.005: astar  valid 10/10   invented routes: 0
  density 0.005: aco    valid  0/10   invented routes: 0
  density 0.002: aco    valid  1/10   invented routes: 0
```

ACO honestly reports no route on 10 of 10 steps while A\* proves one
exists. That is a budgeted search failing to find a path that is there —
honest failure, correctly recorded, and exactly the distinction the page
asks for.

**Timing — what Phase 4 is buying**

| Configuration | Seconds (4 arms) |
|---|---|
| medium200, moderate, 60 steps | **1.9** |
| large1000, moderate, 60 steps | **11.7** |
| medium200, severe, 500 steps | **16.5** |

At the research tier a 4-arm 60-step race is ~1.9s, so ~0.48s per arm per
trial. **100 trials × 8 arms × 3 scenarios ≈ 20 minutes single-threaded**,
and the large tier is ~6× that. Phase 4 is not compute-bound at
`medium200`; it becomes an overnight job only at `large1000`.

**Not automated, and why:** the six sequence-robustness checks (Race before
Build, double-click Race, scrub mid-race, reload mid-run) are properties of
the *interface's ordering*, not of any payload. They need a driven browser,
and asserting them server-side would test a different thing while looking
like coverage. **Left for segment 22's manual pass, called out here so they
are not assumed covered.**

### Is Claim 3 arguable from what this system now produces?

**Yes — the evidence now exists to argue it in either direction. It did
not before this segment.**

At `sigma = 0.001` every hybrid finished with identical routes. There was
no measurement to interrogate: not weak evidence, *absent* evidence, and
any conclusion drawn would have been about the step size rather than the
thesis. That is now fixed, for a reason derived from the budget before any
outcome was seen, and the allocation demonstrably changes the search —
routes differ on roughly half the steps.

What the evidence does **not** yet do is settle the direction. The paired
difference is +0.787pp at 0.37 paired SD, n=6, CI crossing zero, and six
seeds could never have resolved it. The honest position is *undetermined,
adequately instrumented* — and the instrumentation is the part this
segment was for.

Two caveats I would want stated in the report, both mine to flag:

1. **The recency correlation is not sufficient evidence on its own.** A
   mutation that reallocates nothing on net scores −0.798 against the real
   arm's −0.776. Any argument for Claim 3 that leans on the correlation is
   leaning on a statistic that cannot distinguish the thesis from its null.
2. **84% of the movement cancels.** The mechanism is real but inefficient,
   and the pre-registered criterion for addressing that (reversal rate
   below 0.35 without lowering the response ratio) is defined on the
   control signal and awaits your ruling. **No excess figure has been
   consulted in proposing it, and none will be in evaluating it.**

**Files changed (second pass)**
- `dashboard/server.py` — defects 1, 2 and 3
- `tests/test_dashboard.py` — three tests; one nesting bug of mine that
  defect 3's guard exposed
- `WALKTHROUGH.md` — **document corrected in three places**, each marked

**Files added (second pass)**
- `scripts/sweep_combinations.py` — T7

**Surprises**
1. **The dashboard's seed control had never worked.** Every race in the
   project's history ran the same world. It was invisible because the
   *displayed* world honoured the seed — only the raced one did not.
2. **I found defect 3 by committing it**, and the fix immediately found a
   second instance in my own segment-21 test.
3. **All three wrong predictions were seed-1000 generalisations.** Worth
   recording as a pattern rather than three incidents: the document was
   written against one run.

**Could not do**

The six sequence-robustness checks need a driven browser (above).

**Questions for the Architect**

1. The two open questions from the first pass stand: the **seed count**
   (58/78 from the paired SD) and the **cancellation criterion**.
2. **Does `graph_id`'s definition need a §12 note?** Defect 2 was possible
   because two different seeds could both plausibly define a graph's
   identity. It is now the eval seed; that deserves to be written down
   where provenance is specified, and that document is yours.
