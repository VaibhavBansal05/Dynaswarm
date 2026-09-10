# SEGMENT 17 — Diagnose F13

**Phase 3 · Restructure · Segment 1 of ~4**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` **§5.3 (PSO), §7 (the control layer and why it is being rebuilt), §17.1 (PSO inertia)**. `WORKFLOW_LOG.md` **Entries 015 and 016** carry F13 and its second reading.
> Append your findings to the **bottom** of this file.
>
> ## ⛔ YOU DO NOT COMMIT
>
> Rudra commits. Leave the tree unstaged, paste `git status --short`, and paste the commit message as a copyable block **with no `Co-Authored-By` trailer**. No `git add`, no `git commit`, no `git stash`, never `git add -A`.

---

## Goal

**Find out why PSO's swarm stops moving under disruption. Do not fix it.**

Phase 3 rebuilds the control layer and settles the inertia question, and **both of those decisions depend on the answer to this one.** Building first and diagnosing after would mean choosing a lever without knowing what it has to move.

---

## What is already measured, and what is still a story

**Measured, from Phase 2:**

| | first | last |
|---|---|---|
| mean velocity | 0.1119 | 5.112e-14 |
| diversity | 0.1274 | 2.927e-13 |
| global-best updates | 7 | 0 |

And the contrast that makes it a finding rather than a curiosity: **in isolation, with no disruptions, velocity settles at ~1.4e-02 and stays there.** The collapse is specific to a disrupted run — which is backwards, since disruption ought to stir a swarm rather than flatten it.

**Not measured — the Architect's hypothesis, and this segment's job is to try to break it:**

> PSO's velocity has three parts: keep going (inertia × current velocity), pull toward the particle's own best, pull toward the swarm's best. **If the particles all converge onto the same point, both pull terms go to zero** — a particle sitting on its own best and on the swarm's best is being pulled nowhere. What remains is inertia multiplying a shrinking number by something less than one, with nothing feeding it. Velocity then decays geometrically to nothing and cannot recover, because recovery would require a pull, and there is nothing left to pull toward.

Diversity at `2.9e-13` is consistent with this. **Consistency is not confirmation.**

**Treat that paragraph as a claim to falsify, not a conclusion to illustrate.** It is the Architect's story, it has started to look right, and Entry 016 recorded exactly why that makes it dangerous: *a hypothesis that is starting to look right is the one that stops being tested.* Eight consecutive segments say the interesting finding is the one nobody asked for. **If the hypothesis is wrong, saying so is the most valuable outcome available here.**

---

## ⚠️ T0 — MEASURE

`src/` **2037 / 2100**, margin **63**.

**This is a diagnosis. It should cost `src/` almost nothing.** Temporary instrumentation, `scripts/`, or a test — not permanent telemetry. If you conclude a permanent probe is warranted by what you find, **propose it; do not add it.**

Report projection and actual, and say where the instrumentation lives.

---

## T1 — Decompose the velocity update

Log the **three terms separately**, per step, across a disrupted run: the inertia contribution, the cognitive pull, the social pull. Magnitudes, not verdicts.

The question is narrow and answerable: **at the moment velocity collapses, which terms are still contributing and which have gone to zero?**

- if the two pull terms vanish and inertia is simply doing its job → the hypothesis holds, and the mechanism is diversity loss
- if a pull term is still large while velocity dies anyway → **the hypothesis is wrong**, something else is draining it, and that is the finding
- if velocity dies *before* diversity collapses → the causality is the other way round, and that changes the fix entirely

**Report which of these the numbers say.** Say it plainly, including if it is the second or third.

## T2 — Locate it in time

**When does it happen — and is it tied to disruption at all?**

- does the collapse begin at a disruption step, or drift down independently of them?
- is it one event, or accumulation across many?
- the isolation run settles at `1.4e-02` and *stays*. **What is different about the disrupted path?**

That last question is the one that matters most. **Something about disruption is not merely failing to help the swarm — it is actively worse than leaving it alone.** Whatever that is, it is the defect.

**One specific thing to check, and it is checkable rather than speculative:** what happens to the personal and global bests when the graph changes? A best evaluated against the old graph is a stale number. If bests are re-evaluated on the new graph and collapse onto current positions — or are reset — the pull terms die at exactly that moment. **Whether that is what happens is a fact about the code, not an opinion.**

## T3 — Say what the fix would be, and do not do it

Once you know the mechanism, state the options and what each would cost. Likely candidates, depending on what T1 and T2 say:

- **adaptive inertia** — raise it when disruption lands, re-energise the swarm. **This is §17.1's promised-and-never-delivered parameter**, and if the diagnosis points here, the *implement or formally drop* question is answered by the diagnosis rather than by argument
- **re-injection / hypermutation** — perturb some fraction of particles on disruption
- **best re-evaluation policy** — if T2 finds the bests are the problem, the fix is there and inertia is a workaround for it

**Do not implement any of them.** Segment 18 decides, with this in hand.

**And say if the honest answer is "this is correct behaviour."** Premature convergence on a hard dynamic problem is a real phenomenon, not automatically a bug. If that is what the numbers say, the consequence is not a code change — it is that the report states PSO standalone is handicapped by design, and Claim 1 is stated accordingly. **That is a legitimate outcome of this segment.**

## T4 — What it means for Claim 1

PSO standalone runs **27–41% above the optimum.** Claim 1 is that the hybrid beats its components.

**Estimate, from what you now know, how much of that gap is attributable to the collapse.** A number with error bars, or an honest "cannot be estimated without running the fix" — both are answers. What is not an answer is leaving it unaddressed, because it is the first thing an examiner asks when one component does conspicuously badly.

## T5 — Tests

Whatever you keep must be pinned. At minimum:

| Test | Catches |
|---|---|
| **The decomposition sums to the actual velocity update** | An instrument that measures three things which do not add up to the thing they explain is measuring something else |
| **The isolation-versus-disruption contrast reproduces** | It is the entire basis of the finding. If it does not reproduce, say so immediately |

**Every invariant test shown failing against corrupted input.**

## T6 — Mutations, two, one of them yours

**Specified:** make the decomposition report the terms *before* they are combined rather than as applied. Plausible magnitudes, wrong story — the same shape as segment 14's probe that observed the call instead of the effect.

**Yours.** Eight consecutive segments.

## T7 — Show it

1. T0, and where the instrumentation lives
2. **The three terms across the run** — the artefact of this segment
3. **When the collapse starts, relative to disruptions**
4. **Your verdict on the hypothesis: holds, wrong, or something else** — and if wrong, what the numbers actually say
5. What the bests do on a graph change
6. The options and their costs, unimplemented
7. **Your estimate of how much of PSO's gap this accounts for**

## T8 — Hand over, do **not** commit

`git status --short`, the commit message as a copyable block, no `Co-Authored-By`, one line confirming complete and uncommitted.

---

## Constraints

| | |
|---|---|
| **Diagnose. Do not fix.** | Segment 18 decides with this in hand |
| **The hypothesis is to be falsified, not illustrated** | Saying it is wrong is the best available outcome |
| **`src/` should barely move** | Temporary instrumentation. Propose permanent probes; do not add them |
| **Report magnitudes, not verdicts** | Except in T4 and T7, which explicitly ask for your reading — mark it as reading |
| **No control-layer changes** | F4, F7, F8 and the `allocation/` package are later in Phase 3 |
| **No inertia implementation** | §17.1 is decided in segment 18, against this |
| **No dashboard work** | |
| **Do not commit, do not push** | |

---

## Acceptance check

```bash
git diff --stat -- src/ tests/ scripts/
./.venv/bin/pytest
./.venv/bin/ruff check src/ tests/ dashboard/ scripts/
./.venv/bin/pytest -k "budget or statement" -s
ls outputs/
git status --short                       # UNSTAGED, UNCOMMITTED
```

**Paste verbatim:** T0 · the three-term decomposition across a disrupted run · when the collapse starts relative to disruptions · what the bests do on a graph change · **your verdict on the hypothesis** · the options, unimplemented · your estimate for Claim 1 · both mutations · every invariant test shown red.

---

## Definition of done

Green suite, artefacts pasted, **a verdict on the hypothesis stated plainly**, uncommitted with the message pasted, FINDINGS appended.

**After this, Phase 3 knows what it is fixing before it starts fixing.** Segment 18 settles inertia and opens the `allocation/` package.

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->

---

# FINDINGS — Segment 17

## 0. The verdict, first: **the hypothesis is wrong, and so is F13's premise**

Two claims were on the table. Both fail.

| Claim | Verdict |
|---|---|
| *"The collapse is specific to a disrupted run"* — F13, Entry 015 | **False.** It reproduces exactly on a static graph with no events at all |
| *"Particles converge, both pull terms go to zero, inertia coasts down"* | **False.** All three terms decay together, in lockstep, at the same order of magnitude throughout |

**What the numbers actually say:** the collapse is caused by one line in
`PSO.rebind` — `self._own_cost[:] = np.inf` — and the harness calls `rebind`
on every arm at **every timestep, unconditionally**, whether or not the graph
changed.

Disruption is not the variable. It never was.

## 1. T0 — cost

**`src/` 2037 / 2100, delta +0, margin 63.** Untouched, as a diagnosis should
be.

Instrumentation lives in **`scripts/diagnose_f13.py`** — temporary,
monkeypatching `PSO._move` to record the three terms — and the finding is
pinned in **`tests/test_f13_diagnosis.py`**. No permanent telemetry was added;
a proposal for one is in §6.

## 2. T1 — the three terms, as applied

```

DISRUPTED (moderate, 0.3 events/step)
--------------------------------------------------------------------------------------------
    t      inertia   cognitive      social         |v|  own==pos  events
    0      0.08656      0.0404     0.07115      0.1235      32%
    2      0.01112     0.00816     0.01081     0.01554      10%  <- disruption
    5     0.001081   9.292e-04    0.001061    0.001457       7%  <- disruption
    6    8.209e-04   7.702e-04   8.196e-04    0.001158       7%
    8    5.044e-04   4.656e-04   4.928e-04   7.049e-04       7%  <- disruption
    9    3.176e-04   3.204e-04   3.436e-04   4.514e-04       7%  <- disruption
   12    1.424e-04   1.230e-04   1.303e-04   1.900e-04       7%
   18    1.133e-05   1.230e-05   1.257e-05   1.651e-05       7%
   24    3.123e-06   3.030e-06   2.837e-06   4.197e-06       7%
   30    2.077e-08   2.045e-08   2.094e-08   2.848e-08       7%
   36    1.135e-08   1.206e-08   1.113e-08   1.587e-08       7%
   42    8.931e-11   9.552e-11   8.876e-11   1.306e-10       7%
   48    1.055e-11   6.197e-12   6.180e-12   1.292e-11       7%
   54    2.649e-12   3.783e-12   2.749e-12   3.321e-12      11%  <- disruption

  disruption steps: [2, 5, 8, 9, 14, 19, 21, 28, 35, 47, 54, 57]

ISOLATION (static, no disruptions)
--------------------------------------------------------------------------------------------
    t      inertia   cognitive      social         |v|  own==pos  events
    0      0.08656      0.0404     0.07115      0.1235      32%
    6    8.725e-04   8.086e-04   8.469e-04    0.001232       7%
   12    1.404e-04   1.221e-04   1.278e-04   1.851e-04       7%
   18    1.067e-05   1.165e-05   1.191e-05   1.554e-05       7%
   24    3.142e-06   3.042e-06   2.840e-06   4.232e-06       7%
   30    2.041e-08   1.987e-08   2.050e-08   2.789e-08       7%
   36    1.139e-08   1.212e-08   1.116e-08   1.593e-08       7%
   42    8.892e-11   9.472e-11   8.754e-11   1.302e-10       7%
   48    1.060e-11   6.192e-12   6.145e-12   1.297e-11       7%
   54    2.684e-12   3.834e-12   2.787e-12   3.365e-12      18%
```

**All three decay together.** At t=18 they are 1.13e-05, 1.23e-05, 1.26e-05 —
indistinguishable. At t=42, 8.9e-11, 9.6e-11, 8.9e-11. There is no point in
the run where the pulls have died and inertia is coasting: **the pulls are the
same size as inertia the whole way down.**

That is the third of the spec's three cases, not the first. The pulls are not
vanishing *and then* velocity decaying — everything shrinks together, because
what shrinks is the *distances* the pulls are computed from.

**And `own_best == position` sits at 7%**, not 100%. If the hypothesis were
right — particles sitting on their own bests, pulled nowhere — that figure
would be high. It is not. The cognitive term is alive; it just has almost no
distance left to act over.

## 3. T2 — locating it, and the fact about the code

### It is not tied to disruption

The isolation run in the same output collapses to the same magnitude on the
same schedule. `2.789e-08` at t=30 undisrupted against `2.848e-08` disrupted.

**So why did segment 15 measure `~1.4e-02` stable in isolation?** Because that
loop called `spend()` repeatedly on a standalone `PSO` object and **never
called `rebind`**. The harness calls it every step. The contrast was never
disrupted-versus-quiet; it was **harness-versus-standalone**, and nobody had
noticed because no measurement had separated them.

### The decisive experiment

Same graph, same seed, nothing changing between steps:

```
  step     no rebind    rebind each step
     0     2.002e-01           2.002e-01
     5     3.947e-02           8.685e-02
    15     2.350e-02           3.419e-02
    30     1.945e-02           1.185e-02
    45     1.931e-02           1.327e-04
    59     1.424e-02           2.513e-08
```

`1.424e-02` is segment 15's isolation figure, reproduced exactly by simply not
calling `rebind`.

### Isolated to one line

```
  none        final |v| 1.424e-02   diversity 1.903e-02
  full        final |v| 2.513e-08   diversity 5.440e-07
  cost_only   final |v| 2.513e-08   diversity 5.440e-07     <- the wipe alone
  rest_only   final |v| 1.424e-02   diversity 1.903e-02     <- everything else
```

`cost_only` reproduces `full` **bit for bit**. `rest_only` — refresh
visibility, re-sync lists, re-price the global best — reproduces the healthy
baseline **bit for bit**. The cause is `self._own_cost[:] = np.inf` and
nothing else in the method.

### The mechanism, stated

Setting every personal-best cost to infinity means the next evaluation of each
particle **always** improves on it, so `own_best[i] = position[i]`. The
particle's memory is re-anchored to wherever it currently is, every step. The
swarm therefore has no persistent memory of anywhere better — and with nothing
to be pulled back toward, positions drift together, the distances shrink, and
all three terms shrink with them. Inertia then multiplies a shrinking number
by 0.7.

**The policy is correct when the graph changed.** A cost measured against a
graph that no longer exists is a stale number, and `rebind`'s docstring
defends discarding it well. The defect is that **it fires when nothing
changed**, and the harness never checks (`trial.py:176`, unconditional inside
`for arm in arms:`).

### Reproduces across seeds

```
    seed     no rebind        rebind       ratio
    1000     1.424e-02     2.513e-08     5.7e+05
    1001     3.627e-02     9.717e-14     3.7e+11
    1002     2.188e-02     4.072e-14     5.4e+11
       7     5.369e-02     4.139e-12     1.3e+10
      42     3.159e-03     1.239e-12     2.5e+09
    9999     9.360e-03     6.484e-13     1.4e+10
```

Six of six. **Seed 1000 is the weakest case**, so the original single-seed
diagnosis understated it.

## 4. T4 — how much of PSO's gap this accounts for

Measured on a **static** graph, 60 steps, wipe on versus wipe off:

```
    seed    wipe each step    wipe never       gap
    1000             0.0%          1.0%      -1.0%
    1001            10.2%          6.0%       4.2%
    1002             5.5%          2.0%       3.5%
       7            13.1%          0.0%      13.1%
      42            12.7%          4.4%       8.3%

  mean 5.6 percentage points   sd 4.8   n = 5
```

**My reading, marked as reading:** the wipe costs roughly **5.6 points of
excess, ±4.8, on n=5** — and one seed went the other way, so the effect is
real but noisy at this sample size.

**I would not extrapolate that to the 27–41% seen under disruption**, and the
honest answer to "how much of the gap is this" is *cannot be settled without
running the fix*. The reason is in the table: on a static graph PSO sits at
0–13% even with the wipe, nowhere near 27–41%. Whatever else makes disrupted
PSO bad is not in this measurement. **The wipe is a real cost and it is
probably not the whole story.**

## 5. T3 — options, none implemented

| Option | What it does | Cost | My read |
|---|---|---|---|
| **Make the wipe conditional** | invalidate costs only when the graph actually changed | ~2 statements in `trial.py` or a dirty flag on `rebind` | **Smallest, most targeted, addresses the measured cause.** The policy stays right where it is right |
| **Re-evaluate bests instead of discarding** | re-price `own_best` against the new graph rather than setting `inf` | ~4 statements, plus one evaluation per particle per change | Keeps memory across genuine disruptions too. Costs budget, which is metered |
| **Adaptive inertia (§17.1)** | raise inertia when disruption lands | the promised-and-never-delivered parameter | **The diagnosis argues against this as the primary fix.** It would re-energise a swarm whose memory is being erased — treating the symptom. §17.1's *implement or drop* is now a question about adaptation, not about F13 |
| **Re-injection / hypermutation** | scatter some particles on disruption | moderate | `reset_learned_state` already does this and is not the problem |

**Not implemented. Segment 18 decides.**

**And the honest alternative is on the table:** this is *not* simply correct
premature convergence. Premature convergence on a hard dynamic problem would
not be switchable off by declining to erase memory on steps where nothing
happened. The static-graph contrast rules that reading out.

## 6. A permanent probe, proposed not added

The Phase 2 probe reports `speed_mean`, which is what surfaced F13 — but it
could not distinguish *why*. **Proposed: the three terms, per step, as
applied.** ~4 statements in `pso.probe()` given the decomposition already
exists in `_move`.

**Not added**, per the constraint. It is worth having only if segment 18's fix
needs to be shown working, which is segment 18's call.

## 7. Both mutations

**A — specified: the decomposition reports the terms before they are combined.**

```
E  AssertionError: the decomposition does not reconstruct the velocity it
   claims to explain
```

Caught. Reporting `velocity` instead of `inertia * velocity` gives plausible
magnitudes and a wrong story — segment 14's bounds probe in a new place.

**B — mine: the whole diagnosis rested on seed 1000.**

Every test ran on one seed. A seed-specific artefact would have passed all
four while the finding written beside them was wrong — and I would have had
six paragraphs of mechanism explaining something that did not generalise.

```
E  AssertionError: seed 1001: rebind did not collapse the swarm
   (3.627e-02 against 3.627e-02)
```

Now parametrised over six seeds. **Nine consecutive segments.**

## 8. Acceptance

| Check | Result |
|---|---|
| Suite | **404 passed, 0 failed, 0 skipped** |
| Lint, four trees | `All checks passed!` |
| `src/` | **2037 / 2100**, delta **+0** |
| `outputs/` before / after | **26 / 26** |
| New tests | `tests/test_f13_diagnosis.py`, **10 passed** |

## 9. What this changes

**F13 should be restated.** It is currently logged as *"PSO's velocity
collapses under disruption"*. It is not about disruption and it is not really
about velocity — it is about the swarm's memory being erased on every
timestep, of which the velocity collapse is a symptom. Under the current
wording, a future segment could fix disruption handling and leave the cause
untouched.

**And §17.1's inertia question is now separable from F13.** The diagnosis
argues adaptive inertia would be treating a symptom here. Whether adaptation
is wanted for its own sake is still open — but it should no longer be decided
*as the fix for this*.
