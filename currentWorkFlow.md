# SEGMENT 23 — The manifest. Freeze it, and make it reproducible by someone else.

**No new capability. The code is finished.** This segment decides exactly what will be run, records what every instance is, and makes the whole thing reproducible by a person who has only the repository.

After this, nothing about the experiment changes. **Anything not settled here is settled never.**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` **§12 (provenance), §9 (arms), §10.2 (fairness)**, and `WORKFLOW_LOG.md` **Entry 024 (the pre-registration, with both amendments), 028 and 029**.
> Append your findings to the **bottom** of this file.
>
> ## ⛔ YOU DO NOT COMMIT
>
> **Rudra commits. Not you.** Unstaged. No `git add`, no `git commit`, no `git stash`, never `git add -A`.
> Finish with `git status --short` pasted and the commit message fenced — **no `Co-Authored-By`**.

---

## ⚠️ T0 — Measure, both surfaces

`pytest`, `node --test`, `ruff`, counts reported. Kill every server and browser you start.

---

## T1 — The frozen configuration

Two runs, both stamped `manifest`, both reported whatever they say.

| | Primary | Scale check |
|---|---|---|
| graph | **`medium200`** | **`large1000`** |
| why | everything in this project was calibrated and verified at this size | to show whether the findings hold as the problem grows |
| seeds | **≥100** | ≥100, or the largest that fits the time budget — **say which and why** |
| arms | all nine — `astar`, `aco`, `pso`, `hybrid`, `hybrid_fixed`, `hybrid_adaptive`, `hybrid_scheduled`, `hybrid_direct`, `aco_fixed`, `aco_adaptive` | same |
| scenarios | as pre-registered | same |
| budget | unchanged | unchanged |

**`parallel_jobs` is permitted** — Z2 established the timing path carries no shared state. **State the job count in the manifest**, because wall-clock numbers from a parallel run are not comparable to Z2's single-threaded table, and the report must not mix them.

**Nothing else changes.** No arm, no policy, no parameter, no scenario. Frozen by Entry 024.

---

## T2 — ⚠️ Instance characterisation, recorded **per instance**

Entry 029's ruling. This cannot be recovered after the run: an instance property nobody recorded is gone.

For every seed in the manifest, record alongside the run:

- **bridge count** — edges added by `_ensure_connected`
- **bridge share** — what fraction of the optimal route's cost sits on a bridging edge, at `t=0`
- nodes, edges, density, and the optimum at `t=0`

**Why this matters and not as housekeeping:** on 2 of 8 seeds a single bridge hop carries ~45% of the optimal route. On those instances the search problem is largely *"reach the bridge"*, and arms will look alike **for a structural reason rather than because allocation does not help.** Recording the share per instance lets the report answer the obvious challenge directly — *are the arms also indistinguishable on the instances with no dominant bridge?* — instead of conceding it.

---

## T3 — ⚠️ Pre-flight: walk the pre-registration and prove every comparison is computable

Entry 024 plus its two amendments names **P1, P2, P3, P4, S1, S2**. Before spending any compute:

1. For each, confirm the arms it needs are in the manifest and that `stats.py` can compute it from the schema as it now stands.
2. **Confirm the paired structure holds** — each comparison's two arms must see byte-identical worlds on each seed.
3. **Run the whole analysis end to end on a tiny manifest** — 3 seeds, short horizon — and show every pre-registered number coming out with a value. Not the right value; *a* value.

**This is the cheapest possible place to discover that a planned comparison cannot be computed.** Finding it after a 4-hour run is the expensive version.

Report anything the pre-registration asks for that the code cannot currently produce. **Do not quietly drop it.**

---

## T4 — Reproducibility by a stranger

The manifest must let someone with only this repository reproduce both runs exactly.

- the exact command, written down
- every seed, listed — not "seeds 1000–1099", the actual list, because a range is a rule and a list is a fact
- the commit hash, the Python version, the platform, and the `parallel_jobs` count
- **a check that re-running one trial from the manifest reproduces its recorded row bit-for-bit**

That last one is the only thing that proves the rest is true rather than merely written down.

---

## T5 — The runtime estimate, before you start

From Z2's table, not from a guess. State expected wall-clock for each run, and **how you will know early if it is badly wrong** — a checkpoint after N trials with an updated estimate, so a 4-hour run that is secretly a 12-hour run is caught in the first ten minutes.

---

## T6 — Tests

- the manifest is complete: every field a rerun needs, with a test that fails if one is missing
- a `manifest`-stamped run cannot be produced by the dashboard, only by the CLI
- the instance characterisation is recorded for every seed, with no silent gaps

---

## T7 — One mutation, yours

Specified mutations end here — the code is frozen and there is nothing left of mine to break.

**Pick something that makes the manifest look complete while being unreproducible.** That is the failure mode of this segment: a document that reads like a specification and does not pin the thing it claims to. **If it passes everything, that is the finding.**

---

## T8 — Show it

- the frozen configuration, in full
- the per-instance characterisation for the first few seeds, and the **distribution of bridge share across all of them**
- **T3's end-to-end dry run** — every pre-registered comparison producing a value
- T4's bit-for-bit reproduction of one trial
- the runtime estimates
- your mutation, red
- **your read: is there anything the pre-registration asks for that this manifest cannot deliver?**

---

## T9 — Hand over, do **not** commit

`git status --short`, unstaged. Commit message fenced, no `Co-Authored-By`. FINDINGS appended.

**Do not start the evidence run.** That is segment 24, and it starts only after Rudra has committed this.

---

## Constraints

| | |
|---|---|
| **Change no arm, no policy, no parameter, no scenario** | |
| **Both runs reported, whatever they say** | |
| **Seeds listed, not described** | |
| **Wall-clock from a parallel run is never mixed with Z2's single-threaded table** | |
| **Do not start the run** | |
| **Do not commit, do not push** | |

---

## Definition of done

The configuration frozen and written out in full · every instance characterised, bridge share included · every pre-registered comparison shown producing a value on a tiny dry run · one trial reproduced bit-for-bit from the manifest alone · runtime estimated with an early-warning checkpoint · your mutation red · green suite · uncommitted with the message pasted · FINDINGS appended.

**Then segment 24 runs it, and the numbers are whatever they are.**

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->

## FINDINGS — Segment 23

**Status:** COMPLETE. Uncommitted. **The evidence run has NOT been started.**

### T0 — both surfaces

| | Before | After |
|---|---|---|
| Python suite | 520 passed | **529 passed** |
| JS suite | 53 passed | **53 passed** |
| `src/` statements | 2318 | **2318 — unchanged** |
| `ruff` | clean | clean |

`src/` is untouched. Everything this segment added is in `scripts/` and
`tests/`, which is what "the code is finished" should mean.

---

### T1 — the frozen configuration

```
arms      astar, aco, pso, hybrid, hybrid_fixed, hybrid_adaptive,
          hybrid_scheduled, hybrid_direct, aco_fixed, aco_adaptive
seeds     1000..1099, listed individually in MANIFEST.json
scenario  moderate · events_per_step 0.3 · cluster_size 25 · 60 timesteps
budget    300 evaluations per arm per timestep
class     manifest
jobs      parallel_jobs = 8
primary   medium200  (geometric, 200 nodes, density 0.04)
scale     large1000  (geometric, 1000 nodes, density 0.04)
```

**The spec says "all nine" and its own list names ten.** I ran all ten.
The list is the fact and the count is the slip, but flagging rather than
silently resolving it: if nine was meant, one arm has to be named and the
pre-registration adjusted, because `aco_fixed`/`aco_adaptive` are P4's
whole basis and each hybrid variant kills a specific objection.

`parallel_jobs = 8` is recorded in the manifest because **wall-clock from
a parallel run is not comparable to segment Z2's single-threaded table**,
and a report that mixes them is comparing two machines.

---

### T2 — instance characterisation, and **it caught a bug that would have been frozen in**

Recorded per seed: `n_nodes`, `n_edges`, `density`, `optimum_t0`,
`route_hops`, `bridges`, `bridge_hops`, `bridge_share`.

```
medium200: 100 instances
   bridges:      min 0  median 1  max 5     instances with >=1: 57
   bridge share: median 0.0000  mean 0.1876  max 0.6733
   share >10%: 40    >25%: 37
   optimum t=0:  median 141.74  range 99.96..268.88   unreachable 0

large1000: 100 instances
   bridges:      0 on every instance
   bridge share: 0.0000 everywhere
   optimum t=0:  median 115.93  range 79.05..149.61   unreachable 0
```

**This is a bigger effect than Z3's eight-seed sample showed.** Z3
estimated ~25% of instances affected; across the actual 100 manifest
seeds it is **40 with more than a tenth of the optimal route on a
bridging edge, and 37 above a quarter, peaking at 67%.**

**And `large1000` has no bridges at all** — at 1000 nodes the geometric
graph is connected without help. That makes the scale check do a second
job nobody planned: it is a **natural control for the bridging
confound**. If the arms are indistinguishable at `medium200` *and* at
`large1000`, "they only look alike because the problem is reach-the-
bridge" is answered by the data rather than argued with.

#### The bug

`characterise` replays the model call to recover which edges
`_ensure_connected` invented. I wrote it with a **fresh** `stream(seed,
"graph")` for the bridging call instead of continuing the one the model
call was using — which is what `build()` does.

It looks equivalent. It is not: the bridging step consumes draws the
model call has already taken, so a fresh stream **picks different bridge
endpoints**.

**The bridge count is unaffected** — the same components need the same
number of bridges — so every summary I printed looked reasonable. The
only thing that broke was the membership test against the real route, and
it broke silently:

```
before fix:  bridge share 0.0000 on all 100 seeds, max 0.0000
after fix:   mean 0.1876, max 0.6733, 40 instances above 10%
```

It was caught by cross-checking the refactored function against segment
Z3's original on the seeds where Z3 had measured a non-zero share — 9999
and 555, both ~45%, both reading 0.0 under the bug.

**This is the single most valuable thing in the segment.** Entry 029
ruled this property must be recorded because *an instance property nobody
records is gone*. A property recorded **wrongly** is worse: it would have
been frozen into the manifest as "no instance has a dominant bridge", the
confound would have looked dismissed, and nothing downstream could have
contradicted it. Pinned by
`test_bridge_share_is_measured_on_the_world_that_was_built`, which asserts
the two known seeds and says what a 0.0 means.

---

### T3 — the pre-flight, and it is what the spec said it would be

**8 of 8 pre-registered comparisons produced a value.** Three seeds, 12
timesteps, 60 evaluations, all ten arms, whole analysis end to end.

```
  PAIRING — every comparison's arms must see identical worlds
    all 8 comparisons paired on identical optima: True

       comparison                               n    mean A    mean B     delta        p    p adj   effect  sig
  P1   hybrid_adaptive vs hybrid_fixed          3    0.3084    0.3358   -0.0274   0.2500   1.0000   -0.333  no
  P2   hybrid_direct vs hybrid_fixed            3    0.2557    0.3358   -0.0801   0.2500   1.0000   -0.556  no
  P3a  hybrid_adaptive vs hybrid_scheduled      3    0.3084    0.2765   +0.0319   0.7500   1.0000   +0.333  no
  P3b  hybrid_direct vs hybrid_scheduled        3    0.2557    0.2765   -0.0208   1.0000   1.0000   +0.000  no
  P4   aco_adaptive vs aco_fixed                3    0.5580    0.5702   -0.0121   0.7500   1.0000   -0.111  no
  S1   hybrid_direct vs hybrid_adaptive         3    0.2557    0.3084   -0.0527   0.2500   1.0000   -0.556  no
  S2a  hybrid vs aco                            3    0.2803    0.4801   -0.1997   0.2500   1.0000   -1.000  no
  S2b  hybrid vs pso                            3    0.2803    0.1552   +0.1251   0.2500   1.0000   +0.778  no

  VERDICT
    8 of 8 pre-registered comparisons produced a value
    ranking produced 9 ranked arms + reference astar
```

Nothing is significant, and nothing can be: Wilcoxon at n=3 floors at
p=0.25, and Holm across eight pushes everything to 1.0. **That is correct
for a dry run** — it proves computability without being able to produce a
result, which is the right property for a pre-flight to have.

**Two structural findings, both reported rather than absorbed.**

**1. Holm must be applied across the family, not inside each comparison.**
`stats.compare_arms` corrects *within* its own call. Calling it once per
comparison would produce eight separate families of one — no correction
at all, while looking corrected. The analysis therefore uses
`paired_compare` and `holm_correct` directly.

**2. P3 as pre-registered selects on the outcome.** Entry 024 says "best
sensing arm vs `hybrid_scheduled`" — which picks an arm by looking at the
results and then tests the winner. That inflates the false-positive rate
the same way multiple testing does, and it **cannot be corrected
afterwards**, because the selection leaves no trace in the p-value.

I split it into **P3a and P3b**: both sensing arms tested against the
open-loop control, both in the Holm family. Strictly more conservative,
same intent, and the family is 8 rather than 6. **Flagging rather than
doing it quietly, because it changes the correction denominator** — if
you prefer a single pre-specified arm for P3, name it before the run and
the family drops back to 7.

---

### T4 — reproducibility by a stranger

```
T4 — BIT-FOR-BIT REPRODUCTION OF ONE MANIFEST TRIAL
  tier medium200, trial 0, seed 1000, 10 arms
  rows compared: 120
  IDENTICAL — every recorded field except the clocks
  clocks differ between runs: True
  event rows identical: True  (100 events)
```

The clocks-differ line is not decoration: if the timing columns were
*also* identical, "except the clocks" would be excusing nothing and the
comparison would be weaker than it reads.

`MANIFEST.json` is 58,730 bytes and carries all 100 seeds individually,
both tiers' instances, the command, and provenance.

---

### T5 — runtime, measured

**Measured on one full manifest trial — ten arms, 60 timesteps — not
scaled from Z2's four-arm table**, which would need an arm-mix
assumption rather than a count.

```
  medium200      5.58 s/trial  x100  =   9.3 min serial   ~1.2 min at 8 jobs (optimistic)
  large1000     37.34 s/trial  x100  =  62.2 min serial   ~7.8 min at 8 jobs (optimistic)
```

**Both runs together are about 71 minutes single-threaded.** That is well
under Entry 029's estimate of ~30 min plus ~4.5 hours, so there is no
argument anywhere for trimming either run.

The parallel figures are labelled optimistic deliberately: joblib has
process overhead and these trials are memory-bandwidth bound, so linear
speedup is a bound and quoting it as the estimate is how a run comes in
"late" against a number that was never achievable.

**Knowing early if it is wrong:** `runtime_estimate()` returns
`checkpoint_every = 10` trials and `abort_if_per_trial_exceeds` at **2x
the measured per-trial cost** — 11.2s and 74.7s. At `medium200` the first
checkpoint lands within a minute; at `large1000` within seven.

---

### T7 — my mutation: **report `provenance.dirty` as `False`**

*Predicted:* passes everything. The completeness test asserts the key is
*present*; nothing asserts it is *true*.

*Actual:* **passed the entire suite.**

The manifest would then name a commit and declare the tree clean while
uncommitted work was running. A stranger checks out that commit, gets
different code, and **every other field still reads correct** — the seeds
are listed, the command is there, the instances are characterised. It is
exactly this segment's named failure mode: a document that reads like a
specification and pins nothing.

Closed by `test_the_provenance_tells_the_truth_about_the_working_tree`,
which calls `git` independently rather than trusting the value the
manifest computed — **a field cannot verify itself**. Shown red:

```
E  AssertionError: the manifest reports dirty=False and the tree is dirty=True.
   A provenance field that does not match reality is worse than an absent one
   — it is read as a guarantee
```

I also added `reproducible_from_commit` and a plain-English `warning`,
because a boolean a reader has to notice is not the same as a sentence
telling them. **The manifest currently reports `dirty: true`** — correctly,
since this work is uncommitted. It becomes clean when you commit, and the
evidence run should not start before then.

---

### Is there anything the pre-registration asks for that this manifest cannot deliver?

**No — everything computes. Four things need your decision, none of them
blocking.**

1. **Nine arms or ten.** The spec's prose and its list disagree. I ran ten.
2. **P3's selection-on-outcome.** Split into P3a/P3b, family size 8 not 6.
   If you want a single pre-specified arm, name it before the run.
3. **`large1000` is a bridging control**, unplanned and free. Worth saying
   in the report, because it converts the strongest competing explanation
   for a null into something the data answers.
4. **Recovery at `large1000` is unmeasured.** Entry 029 flagged that the
   metric rests on 3–4 damaged events per run at `medium200` and that the
   number at `large1000` is unknown. It still is — the manifest records
   what is needed to compute it, but nobody has checked it behaves there.
   It is a scale check, `medium200` is primary, and the damaged count now
   travels with the value, so it will be visible rather than silent.

**One thing I want on the record.** The bridging bug in T2 was mine, it
was caught by cross-checking against the previous segment's
implementation, and had I not done that it would have frozen a false
zero into the document this whole segment exists to make trustworthy.
The dry run found nothing wrong with the analysis; the characterisation
is where the risk actually was.

---

**Files added**
- `scripts/manifest.py` — the frozen configuration, instance characterisation, runtime estimate
- `scripts/preregistration.py` — the family as code, Holm across all of it
- `scripts/dry_run.py` — T3
- `scripts/reproduce_one.py` — T4
- `tests/test_manifest.py` — 9 tests
- `MANIFEST.json` — the artefact

**Files changed** — none in `src/`.

**Surprises**
1. **The bridging confound is much larger than Z3's sample suggested** —
   40 of 100 instances, not ~25%.
2. **`large1000` has no bridges at all**, making the scale check a
   control for the confound.
3. **A fresh RNG stream that "looks equivalent"** silently changed which
   edges were identified while leaving every count intact.
4. **Both runs cost ~71 minutes total**, not the ~5 hours estimated.

**Questions for the Architect**

1. **Nine arms or ten?**
2. **P3: two tests or one pre-specified arm?** It changes the Holm
   denominator and must be fixed before the run.
3. **Should the report condition on `bridge_share`** as a planned
   analysis, or record it and only use it if challenged? The data
   supports either; pre-registering it is stronger.

---

## FINDINGS — Segment 23, ADDENDUM: re-frozen to four scenarios (Entry 030)

**Status:** COMPLETE. Uncommitted. **The evidence run has NOT been started.**

Both rulings adopted: Holm across the family in a single correction, and
P3 split into P3a/P3b. The manifest is re-frozen to four scenarios.

### Surfaces

| | Before addendum | After |
|---|---|---|
| Python suite | 529 passed | **532 passed** |
| JS suite | 53 | **53** |
| `src/` statements | 2318 | **2318 — still untouched** |

---

### The re-frozen configuration

```
scenarios  calm 0.0 · light 0.1 · moderate 0.3 · severe 0.8   events per step
           cluster_size 25, 60 timesteps — IDENTICAL across all four
seeds      1000..1099, listed
arms       all ten
tiers      medium200 (primary) · large1000 (scale check + bridging control)
total      100 seeds x 4 scenarios x 2 tiers = 800 trials
```

The rates are the project's own presets from `model.js` — `static 0.0,
low 0.1, moderate 0.3, high 0.8` — under Entry 030's display names. The
mapping is recorded in the manifest so nobody reads them as invented.

**Only the event rate varies.** `cluster_size` and `timesteps` are held
identical, and a test asserts it: if either also moved, a difference
between scenarios would have two possible causes and the dose-response
claim would mean nothing.

---

### The dry run over all four — and it found the thing worth finding

```
  grid: 32 cells   tested: 30   (Holm across all tested cells, once)
  all 8 comparisons x 4 scenarios paired on identical optima: True

  IDENTICAL ARMS (no difference to rank — not an error):
    calm/P1: arms identical on every trial (3 pairs)
    calm/P4: arms identical on every trial (3 pairs)

  VERDICT
    grid 32 cells: 30 tested, 2 identical-arm, 0 not computable
    produced NaN: none
```

**At `calm`, P1 and P4 are not merely non-significant — they are
mathematically undefined.** `hybrid_adaptive` is byte-identical to
`hybrid_fixed`, and `aco_adaptive` to `aco_fixed`, on every trial. Fed to
Wilcoxon that is a vector of zero differences: nothing to rank.

Verified as the control working rather than a defect:

```
  calm       events    0   recency distinct 1   aco_fraction distinct 1   rho distinct 1
  moderate   events  150   recency distinct 6   aco_fraction distinct 14  rho distinct 19
```

With nothing to sense, a recency-driven arm does not move. **That is the
negative control succeeding in the strongest possible form** — not a small
effect, an identical one.

**Had this not been caught here it would have surfaced four hours into the
run**, as a NaN or an exception from `scipy` in the middle of the grid.
Handled explicitly: degenerate cells are reported, excluded from the Holm
denominator (30, not 32), and named in the output. A cell that vanished
silently would look like one nobody planned, and it would have inflated
the correction against 32 tests when only 30 were performed.

**Three tests pin it**: the scenarios differ only in rate; `calm` makes
the sensing arms identical to their twins; and identical arms are
reported rather than dropped.

---

### The Holm family with four scenarios — a decision I had to make

Entry 030 fixed the family at 8 *for one scenario*. Four scenarios make
the grid 32, and that needed a choice I am flagging rather than burying.

**Holm is applied across every tested cell, once — 30 here, up to 32 in
the real run.** Running the same eight hypotheses in four scenarios and
reporting whichever cells came out significant is multiplicity whatever
the scenarios are called. The strictest threshold becomes 0.05/32 =
**0.0016**.

That is conservative, and **the dose-response claim does not depend on
it.** That claim is read off *effect sizes* trending across light →
moderate → severe, which is descriptive and needs no correction:

```
  DOSE-RESPONSE (effect size, uncorrected and descriptive)
  comparison       light    moderate      severe   monotone?
  P1          -0.222      -0.333      +0.222   no
  P2          -0.556      -0.556      +0.222   yes
  P4          +0.000      -0.111      -0.556   yes
  S2a         -0.778      -1.000      -0.778   no
```

Those numbers are from 3 seeds and mean nothing yet — the point is that
the column exists and computes. **A pattern that scales with disruption
rate is stronger evidence than a single cell clearing a threshold**,
because a spurious effect has no reason to scale with the thing it is
supposed to depend on.

**If you would rather Holm ran within each scenario** (four families of
8, threshold 0.05/8 = 0.00625), say so before the run — it is one
constant, and it is a different claim about what the family is.

---

### Runtime, re-measured per scenario

Measured rather than assumed, because assuming flat cost is how a
four-scenario run comes in four times over a one-scenario estimate:

```
  medium200:  calm 6.21s · light 5.73s · moderate 5.86s · severe 6.14s
  large1000:  calm 38.21s · severe 40.33s
```

Under 10% spread, so a single figure would have been fine — **but
measuring it is what establishes that.** Means taken across scenarios:
5.99s and 39.3s.

```
  medium200   4 scenarios x 100 seeds =  400 trials    39.9 min serial   ~ 5.0 min at 8 jobs
  large1000   4 scenarios x 100 seeds =  400 trials   262.0 min serial   ~32.7 min at 8 jobs
  BOTH TIERS                                          301.9 min (5.0 h)  ~37.7 min at 8 jobs
```

Consistent with Entry 030's estimate of ~37 min + ~4 hr. The checkpoint
stays at every 10 trials with an abort threshold at 2× the measured
per-trial cost.

---

### Is there anything the pre-registration asks for that this manifest cannot deliver?

**No. Everything in the grid computes, and the two that don't are the
control working.** Three things still want your word, none blocking:

1. **The Holm family: 32 across the grid, or 8 within each scenario?**
   I chose the conservative reading. It is one constant either way.
2. **Nine arms or ten** — still open from the main findings.
3. **`large1000` at four scenarios is 4.4 hours single-threaded.** It fits,
   and it is the bridging control, so I have not trimmed it. If the time
   budget bites, dropping `large1000`'s `calm` and `light` would halve it
   while keeping the control and the severe end — but that is a
   pre-registration change and yours to make, not mine.

**What the addendum changed about my confidence:** the single-scenario
manifest would have run cleanly and produced a result. It would also have
had no negative control, and the first time anyone asked "does the effect
vanish when there is nothing to respond to?" the answer would have been
unavailable. The four-scenario design answers it, and the dry run shows
the answer is already visible in the mechanism — identical arms, not a
small difference.

**Files changed (addendum)**
- `scripts/manifest.py` — four scenarios, per-scenario runtime, commands per scenario
- `scripts/preregistration.py` — per-scenario grid, one Holm family, degenerate handling, `dose_response`
- `scripts/dry_run.py` — all four scenarios
- `tests/test_manifest.py` — three tests
- `MANIFEST.json` — regenerated, 800 trials
