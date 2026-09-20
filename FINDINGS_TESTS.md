# FINDINGS_TESTS.md — what the evidence run measured

**Run:** `outputs/2026-09-19/18-43-05` · commit `b4d3d281266c985701abb3e0a7861364df60dff4` · `dirty: false`
**Date:** 19 September 2026 · re-derived from the raw rows 20 September 2026

This is the single reference for the report and the deck. **Nothing here should require opening `outputs/` again.**

### How to read this file

Every section opens with **one or two plain sentences saying what was measured and what came back**, before any number. Those sentences say what was *measured*, never what it *proves* — readings belong in the report.

Every result carries:

- the **command** that produced it, so it can be re-run;
- a **provenance tag** — **`[raw]`** means re-derived from the 720,000 parquet rows in segment 25, **`[analysis.txt]`** means carried from the earlier derived summary and *not* re-checked;
- a **status tag** — **`PRE-REGISTERED`** means committed to in writing before the run existed, **`EXPLORATORY`** means chosen after seeing the result.

**An exploratory result may explain a pre-registered one. It may never overturn one.** That distinction is the only reason the pre-registered half is worth anything, and it is marked on every table rather than stated once.

### Scales used throughout

| Quantity | Scale | How to read it |
|---|---|---|
| **excess** | percentage points above the true shortest route | 3.15% means the route found was 3.15% more expensive than optimal. Lower is better. |
| **Cliff's delta (effect)** | −1 to +1 | How often one arm beats the other, ignoring by how much. **< 0.147 negligible · < 0.33 small · < 0.474 medium · ≥ 0.474 large.** Sign follows `delta`: negative favours the first arm. |
| **p_adj** | 0 to 1 | Probability of seeing this pattern by chance, after correcting for having run 34 tests. **Below 0.05 counts.** The strictest single threshold here is 0.05/34 ≈ 0.0015. |
| **delta** | percentage points of excess | Mean paired difference, `arm_a − arm_b`. Negative means `arm_a` was better. |

---

## 0. The setup, for a reader who has not seen this project

**The problem.** Find the cheapest route across a road network while roads are being closed, reopened and re-priced underneath you. An exact method (A\*) recomputes the true answer every step and is used only as the yardstick; the algorithms under test are approximate and work to a fixed budget.

**The ten arms.** Each is one algorithm configuration. All ten run on every world.

| name | what it is |
|---|---|
| `astar` | exact shortest path. The **reference**, never ranked — it cannot lose |
| `aco` | Ant Colony Optimisation alone. Builds a pheromone map, so it has memory |
| `pso` | Particle Swarm alone. No memory of the old network |
| `hybrid` | ACO + PSO, budget split 50/50, no control machinery at all |
| `hybrid_fixed` | the same split, frozen at 50/50, **with** the machinery — the ablation twin |
| `hybrid_adaptive` | senses disruption and **nudges** the split by small steps |
| `hybrid_direct` | senses disruption and **jumps** the split straight to a target |
| `hybrid_scheduled` | sweeps the split on a **fixed timetable, ignoring the world** — the control for "does any movement help" |
| `aco_fixed` / `aco_adaptive` | ACO with its evaporation rate held vs allowed to adapt — the pair for Claim 2 |

**The four scenarios** differ *only* in how often roads break:

| name | breaks per step | role |
|---|---|---|
| `calm` | 0.0 | negative control — nothing to sense, so a sensing arm must not move |
| `light` | 0.1 | |
| `moderate` | 0.3 | |
| `severe` | 0.8 | the hardest setting |

**The two tiers** are network sizes: **`medium200` = 200 road junctions**, **`large1000` = 1,000**. Everything in this project was calibrated at `medium200`; `large1000` was added to test whether findings survive a size change.

**The comparison codes** used throughout. Each is one pair of arms, tested seed by seed:

| code | compares | asks |
|---|---|---|
| P1 | `hybrid_adaptive` vs `hybrid_fixed` | does sensing beat not moving |
| P2 | `hybrid_direct` vs `hybrid_fixed` | same, with the split jumping rather than nudging |
| P3a | `hybrid_adaptive` vs `hybrid_scheduled` | does sensing beat moving blindly |
| P3b | `hybrid_direct` vs `hybrid_scheduled` | same, for the jumping arm |
| P4 | `aco_adaptive` vs `aco_fixed` | **Claim 2** — does adapting a parameter help |
| P5 | `hybrid_scheduled` vs `hybrid_fixed` | does *any* movement help, sensing aside |
| S1 | `hybrid_direct` vs `hybrid_adaptive` | does the shape of the response matter |
| S2a / S2b | `hybrid` vs `aco` / vs `pso` | **Claim 1** — does the combination beat its halves |

Nine comparisons × four scenarios = a **36-cell grid** per tier. Two cells are degenerate at `calm` (P1 and P4, where the two arms behave identically), leaving **34 tested**.

**Two more terms.** A **chunk** is one batch of 50 seeds written as a unit — the run was executed in 24 of them. The **governor** is the component that receives a policy's requested split and may cap how far it moves in one step; a request it caps is **clamped**.

---

## 1. The run

**What this is.** One execution of the frozen experiment: ten algorithms racing on the same 150 randomly-generated road networks, at four disruption rates, at two network sizes. Every algorithm sees byte-identical worlds, so any difference between them cannot be the world.

| | |
|---|---|
| trials | 1,200 — 150 seeds × 4 scenarios × 2 tiers |
| rows recorded | **720,000** — 24 chunks × 30,000, verified per chunk |
| arms | 10 |
| `medium200` | 600 trials, 24.3 min, 2.43 s/trial at 8 jobs |
| `large1000` | 600 trials, 191.8 min, 19.18 s/trial at 8 jobs |

Per-trial time held at 17.3–18.6 s for the first nine `large1000` chunks and rose to 20.3–23.8 s on the last three — thermal throttling on a fanless machine. **Wall-clock from this run is not uniform and any timing claim must carry that caveat.** Results are deterministic given the seed and are unaffected.

The runtime projection before the run was 57 min; the actual was 216 min, wrong by ~4× because it assumed 8× parallel speedup where the real figure is ~2.5×.

```
scripts/segment25.py :: steps()          # 720,000 rows
outputs/2026-09-19/18-43-05/run.log      # the timing lines
```
**`[raw]`**

---

## 2. Verification performed before any result was interpreted

**What this is.** Five checks, each one a failure that would have produced entirely plausible numbers. All five were run before any comparison was read.

1. **24 chunk folders + `provenance.json`.** Verified by **row count, not file count**: 30,000 rows per chunk × 24 = 720,000. An initial file-count check wrongly flagged all 24 as partial, having assumed 3 files per chunk where `ResultWriter` writes 2.
2. **`n` = 150 in all 34 non-degenerate cells, both tiers.** No seeds dropped. No cell pools scenarios — pooling would read 600.
3. **34 of 36 cells tested, 2 degenerate** — exactly `calm/P1` and `calm/P4`, where the sensing arms are byte-identical to their twins because there is nothing to sense.
4. **Sign of `delta` correct**, cross-checked against raw excess on two cells in opposite directions.
5. **`provenance.json` clean** at `b4d3d28`.

```
scripts/segment25.py :: steps(), paired()
```
**`[raw]`** — all five re-derived in segment 25.

---

## 3. Statistical frame

**What this is.** How the comparisons were made. Each algorithm pair is compared seed by seed rather than on averages, because the worlds differ enormously in difficulty and pairing cancels that out.

- **Seed-by-seed paired differences.** Worlds differ enormously in difficulty, so comparing averages would drown the effect in that variation. Pairing cancels it: on P1 in this run, the spread across arms drops from **1.2–1.6 to 0.5–0.6 percentage points** at `large1000` and from **6.9–8.5 to 2.5–5.0** at `medium200` — a factor of 1.7–2.8.

  *(An earlier draft quoted "4.110 to 2.132" here. Those are the six-seed pilot's figures from Entry 028, not this run's, and they were sitting inside a section describing this run. Replaced with the measured values above.)*
- **Paired Wilcoxon signed-rank**, a test that uses rank order rather than raw values, so one freak world cannot dominate.
- **Holm correction applied once across all 34 tested cells**, not within each comparison. Running nine hypotheses in four scenarios and reporting the significant ones is multiplicity whatever the scenarios are called.
- **Cliff's delta** for effect size, thresholds in the table above.
- Every comparison was pre-registered in `WORKFLOW_LOG.md` Entry 024 with three dated amendments, all before any result existed.

**`[raw]`**

---

## 4. Results — the pre-registered comparisons  `PRE-REGISTERED`

### Claim 1 — the hybrid beats its own components

**What was measured.** Whether the combined ACO+PSO algorithm finds cheaper routes than either of its two halves running alone. Compared on mean excess, seed by seed, in all four disruption scenarios at both network sizes.

**What came back.** The hybrid beat PSO in all four scenarios at both sizes. It beat ACO in all four scenarios at the large size, but at the small size only under severe disruption.

| | `large1000` | `medium200` |
|---|---|---|
| `hybrid` vs `pso` (S2b) | significant in **all 4** | significant in **all 4** |
| `hybrid` vs `aco` (S2a) | significant in **all 4**, δ ≈ −0.99 (large), p_adj 7.8e-25 | significant in **1 of 4** (severe) |

At `medium200/calm` the mean paired difference is **+0.0036** — nominally favouring ACO — while ACO loses on 90 of 150 individual seeds. See §6b.

```
scripts/segment25.py :: paired(); dynaswarm.analysis.stats :: paired_compare, holm_correct
```
**`[raw]`**

### Claim 2 — adapting a parameter does not help

**What was measured.** Two identical ACO colonies, one allowed to adjust its pheromone-evaporation rate during the run and one held fixed. Eight cells: four scenarios × two sizes.

**What came back.** No difference anywhere. P4 is not significant in any of the 8 cells at either tier.

```
scripts/segment25.py :: paired(cell, "aco_adaptive", "aco_fixed")
```
**`[raw]`**

### Claim 3 — moving the budget split between the two halves

**What was measured.** Four hybrids that differ *only* in how they move the ACO/PSO budget split: one frozen at 50/50, one that senses disruption and nudges, one that senses and jumps, and one that sweeps a fixed timetable ignoring the world entirely. All six pairs among them were tested.

**What came back.** No sensing arm beat the frozen split anywhere. At the highest disruption rate both sensing arms were beaten by the timetable that ignores the world.

| comparison | what it asks | `large1000` result |
|---|---|---|
| P1 `adaptive` vs `fixed` | does sensing beat not moving | never significant; delta positive (adaptive worse) in 5 of 6 non-degenerate cells |
| P2 `direct` vs `fixed` | same, split correctly positioned | significant once, `light`, δ = −0.097 (negligible) |
| P5 `scheduled` vs `fixed` | does *any* movement help | never significant |
| P3a `adaptive` vs `scheduled` | does sensing beat moving blindly | **significant at `severe`, δ = +0.100 — against sensing** |
| P3b `direct` vs `scheduled` | same, for the direct arm | **significant at `severe`, δ = +0.080 — against sensing** |
| S1 `direct` vs `adaptive` | does response shape matter | significant at `light`, δ = −0.105 |

12 of 34 cells significant at `large1000`; 5 of 34 at `medium200`.

**`[raw]`**

### Magnitude versus significance

**What this says.** The two results that reached significance against sensing are, on the effect-size scale, the smallest category there is.

P3a and P3b clear the threshold with δ = 0.100 and 0.080 — **negligible** (< 0.147), on the same scale where Claim 1 scored 0.99 (large). 150 paired seeds with halved noise reliably resolve very small differences; that is power working as designed. **The accurate phrase is "reliably detectable, practically negligible."**

**`[raw]`**

### Dose-response

**What was measured.** Whether the effect grows as disruptions get more frequent. Only the event rate differs between scenarios — network size, break size and run length are held identical, with a test — so an ordering that tracks the rate tracks the one knob that moved.

**What came back.** At the large size the disadvantage to sensing grows monotonically with disruption rate. At the small size it does not.

| | light | moderate | severe |
|---|---|---|---|
| P3a at `large1000` | +0.063 | +0.082 | **+0.100** |
| P3a at `medium200` | −0.036 | +0.039 | +0.010 |

Reported as uncorrected and descriptive.

**`[raw]`**

### Ranking, `large1000/severe` (mean excess, lower is better)

**What was measured.** Average excess for each algorithm on the hardest setting at the larger network size.

**What came back.** Every hybrid beat both single algorithms comfortably. The four hybrids then sat inside a 0.28-percentage-point band.

| arm | mean excess |
|---|---|
| `hybrid_scheduled` | 2.99% |
| `hybrid_fixed` | 3.15% |
| `hybrid_direct` | 3.24% |
| `hybrid_adaptive` | 3.27% |
| `pso` | 4.19% |
| `aco` | 14.28% |

```
trials()[(tier=="large1000") & (scenario=="severe")].groupby("arm").mean_excess.mean()
```
**`[raw]`** — all six values re-derived and matching.

---

## 5. The upper bound on every null  `PRE-REGISTERED`

**What was measured.** When a comparison finds no difference, "no difference" is not the same as "no difference bigger than X". For every non-significant pre-registered comparison, a 95% confidence interval was computed on the paired difference by bootstrap — resampling the 150 seeds 4,000 times — and read on the raw excess scale so it needs no lookup table.

**What came back.** At the larger network size, the most any sensing arm could plausibly be ahead by is **under a third of one percentage point of excess**, and for several cells the data supports no advantage at all.

**Read as:** *`hybrid_adaptive` did not beat `hybrid_fixed`. With 150 paired seeds, any true benefit is smaller than **0.06** percentage points of excess at `light`, **0.01** at `moderate`, and **zero** at `severe` — the data supports no advantage there at all.*

`large1000` — the bound is how far ahead `arm_a` could plausibly be:

| cell | mean diff | 95% CI | bound on `arm_a`'s advantage |
|---|---|---|---|
| light P1 | +0.018 | [−0.058, +0.097] | **0.058 pp** |
| moderate P1 | +0.087 | [−0.011, +0.196] | **0.011 pp** |
| severe P1 | +0.115 | [+0.018, +0.221] | **0 — no advantage supported** |
| light P2 | −0.182 | [−0.292, −0.073] | 0.292 pp |
| moderate P2 | −0.069 | [−0.198, +0.057] | 0.198 pp |
| severe P2 | +0.087 | [−0.069, +0.246] | **0.069 pp** |
| severe P5 | −0.155 | [−0.296, −0.026] | 0.296 pp |
| light P4 | −0.018 | [−0.463, +0.433] | 0.463 pp |
| moderate P4 | −0.388 | [−0.945, +0.163] | 0.945 pp |
| severe P4 | −0.243 | [−1.068, +0.575] | **1.068 pp** |

`medium200` bounds are 3–10× wider (0.23–1.47 pp) because that tier is noisier.

**Claim 2's bound is the widest thing here.** P4 at `large1000/severe` cannot rule out a 1.07-percentage-point benefit from adapting ρ. *"No significant difference"* and *"adaptation cannot help by more than a point"* are different statements, and only the second is what this run established.

```
np.percentile([rng.choice(d, len(d)).mean() for _ in range(4000)], [2.5, 97.5])
# d = (a - b) * 100, paired on (run_id, trial), seed 20260920
```
**`[raw]`**

---

## 6. Conditioning on the bridge confound  `PRE-REGISTERED`

**What was measured.** Some randomly-generated networks contain one very long road that carries most of the best route. On those, the problem is largely *"reach that road"*, and every algorithm could look alike for a structural reason rather than because the idea under test fails. The 150 small-network instances were split at **10% of route cost on a single bridging hop** — the threshold already fixed in Entry 029, not chosen after seeing the answer — and the whole pre-registered family was re-run on each half.

**What came back.** The Claim 3 null holds on both halves. Not one of the 19 Claim 3 cells is significant on either side.

| | seeds | Claim 3 cells significant | Claim 1 cells significant |
|---|---|---|---|
| low bridge (≤10%) | 87 | **0 of 19** | 6 |
| high bridge (>10%) | 63 | **0 of 19** | 4 |

`large1000` has **zero** bridging edges on all 150 instances and shows the same Claim 3 null, so there are two independent answers to the same objection and **they agree**.

One difference worth recording: `hybrid` vs `aco` is significant on the low-bridge half at `light` and `severe` but on neither at the high-bridge half — consistent with a dominant bridge making all arms look more alike.

```
seeds split on MANIFEST.json bridge_share; family re-run via paired() + holm_correct()
```
**`[raw]`**

---

## 7. Did the allocation mechanism actually work?  `EXPLORATORY`

**What was measured.** Before asking whether moving the budget split helps, it is worth knowing whether the split moved at all. The run recorded, on every timestep, what each policy asked for, what the governor allowed, and whether the request was capped. None of it had been looked at.

**What came back.** The mechanism works. The frozen arm never moved; every other arm moved on nearly every step. The direct policy is capped by the governor on **75% of its steps** — it asks for far more movement than it is allowed.

`severe`, mean per 60-step trial (identical at both tiers to 2 decimals):

| arm | steps where split moved | steps capped | total distance travelled | split range | corr(split, signal) |
|---|---|---|---|---|---|
| `hybrid_fixed` | 0.0 | 0.0 | 0.000 | 0.500..0.500 | — |
| `hybrid_adaptive` | 58.2 | **0.0** | 0.343 | 0.303..0.500 | −0.137 |
| `hybrid_scheduled` | 59.0 | 5.0 | 0.790 | 0.210..0.750 | −0.023 |
| `hybrid_direct` | 52.3 | **44.9 (75%)** | 2.567 | 0.203..0.613 | −0.196 |

Three things this establishes. The **ablation twin is genuinely frozen** — 0.000 travel, so the pair differs in exactly one thing. The **75% cap rate confirms segment Y's 78% measured at n = 1**. And the adaptive arm, though never capped, only ever moves *downward* from 0.5 and travels 0.343 in total against the direct arm's 2.567.

The correlation between split and signal is negative for both sensing arms — the designed direction — but weak (−0.14, −0.20).

```
probe map: alloc_applied, alloc_held_back, aco_fraction; signal_value column
scripts/segment25.py :: trials()
```
**`[raw]` `EXPLORATORY`** — chosen after seeing the result. Explains the null; cannot overturn it.

---

## 8. Does the disruption signal saturate?  `EXPLORATORY`

**What was measured.** Entry 032 offered an explanation for why sensing loses at high disruption rates: the signal is binary, reading 1.0 on any disruption step, so as breaks get more frequent it sits at 1.0 most of the time and the sensing arms are steering on a constant. That was a story. `signal_value` is on every row, so it is checkable.

**What came back.** The signal does climb with the disruption rate, as predicted. It does **not** approach 1.0 — at the highest rate it reads exactly 1.0 on 54% of steps, leaving 46% still carrying information.

| scenario | fraction of steps at exactly 1.0 | mean signal |
|---|---|---|
| calm | 0.000 | 0.000 |
| light | 0.095 | 0.253 |
| moderate | 0.259 | 0.527 |
| severe | **0.539** | 0.782 |

(`large1000`; `medium200` agrees to within 0.003.)

**Entry 032 is half-confirmed and needs correcting.** The direction is right and now measured: saturation rises monotonically with the event rate. The magnitude is overstated — *"the arms steer on a constant"* is not what 54% describes. The signal is degraded at `severe`, not constant.

```
signal_value column, arm == "hybrid_adaptive"; fraction >= 1.0 - 1e-9
```
**`[raw]` `EXPLORATORY`**

---

## 9. The metrics that were built and never reported  `EXPLORATORY`

### 9a. Recovery — how many steps to get back to pre-disruption quality

**What was measured.** After a break that actually damaged an arm's route, how many timesteps until its excess returns to within 10% of where it was. Measured at `medium200`, which is the tier with enough damaging events to support it.

**What came back.** All four hybrids recover at essentially the same rate, and everything recovers faster when breaks are more frequent — because there is less quality to lose between them.

| scenario | fixed | adaptive | direct | scheduled | damaged events per arm |
|---|---|---|---|---|---|
| light | 12.53 | 12.32 | 11.72 | 12.75 | 87–100 |
| moderate | 7.50 | 8.03 | 7.40 | 7.65 | 263–281 |
| severe | 4.61 | 4.68 | 5.05 | 4.36 | 276–306 |

All counts clear the pre-set floor of 30 damaging events per arm.

### 9b. Availability — how often an arm had no route at all

**What was measured.** Failing to find any route is worse than finding a poor one, and it had never been counted.

**What came back.** Essentially never a problem. At the large size every arm held a route on 100% of steps. At the small size the worst case is ACO at 99.68%.

### 9c. Route churn — does the adaptive arm destabilise its own solution?

**What was measured.** How many times each arm changed its chosen route in a 60-step trial.

**What came back.** No. The four hybrids are indistinguishable from each other (15.4–16.2 at `medium200/severe`). ACO churns three times more than PSO at the large size (12.5 vs 2.0).

### 9d. Timing at n = 150

**What was measured.** Milliseconds per timestep per arm, with spread, from 150 seeds rather than the single trial Z2 used.

**⚠️ Read with the throttling caveat from §1: wall-clock in this run is not uniform.**

| tier | A\* | ACO | PSO | hybrid |
|---|---|---|---|---|
| `large1000` | 16.4 [10.6–21.9] | 285.8 [216–352] | 64.7 [52.6–81.2] | 198.6 [161–256] |
| `medium200` | 1.5 [0.9–2.1] | 28.5 [19.2–37.2] | 24.0 [16.5–36.1] | 31.5 [22.7–43.4] |

The four controlled hybrids are within 11% of each other at both sizes. **A\* is 12–17× faster than any metered arm and exact.**

### 9e. Win counts — seeds out of 150 where the first arm was better

**What was measured.** Plain counting, as a legibility check on the p-values.

| cell | P1 adaptive vs fixed | P3a adaptive vs scheduled | P5 scheduled vs fixed |
|---|---|---|---|
| `large1000/moderate` | 59/150 | 57/150 | 75/150 |
| `large1000/severe` | 64/150 | **47/150** | **88/150** |
| `medium200/severe` | 78/150 | 70/150 | 78/150 |

At `large1000/severe` the adaptive arm beats the timetable on 47 of 150 seeds — it loses on two thirds of them.

```
scripts/segment25.py :: trials(), paired()
```
**`[raw]` `EXPLORATORY`** for all of 9a–9e.

---

## 10. Which tier carries which metric

**What this is.** Two network sizes were run. They are not interchangeable, and which one a number should be read from depends on the number.

| metric | read from | why |
|---|---|---|
| mean excess | `large1000` | computed from every timestep; unaffected by how rare damage is |
| worst excess | `large1000` | same |
| **% of steps at optimum** | **`medium200`** | near-degenerate at `large1000` — see §11c |
| recovery | `medium200` | 82.8–261.7 damaging events per arm against 11.7–42.9 at `large1000` |

`large1000` is preferred where it can be, because it has **zero bridging edges on all 150 instances** and is therefore free of the confound §6 tests for.

### The evidence floor

A pre-set minimum of **30 damaging events per arm per scenario** for recovery to be reported at all.

| tier | light | moderate | severe |
|---|---|---|---|
| `large1000` | **11.7 ✗** | 31.8 ✓ | 42.9 ✓ |
| `medium200` | 82.8 ✓ | 238.2 ✓ | 261.7 ✓ |

`large1000/light` fails and is reported with its count, carrying no claim. **The floor does not move** — lowering it to admit `light` would be tuning a threshold to pass.

`calm` is excluded from the floor's population by definition: no disruptions, so zero damaging events is the designed outcome rather than a shortage.

```
scripts/manifest.py :: primary_tier_holds(); censored_recovery() per arm-trial
```
**`[raw]`**

### The structural tension, stated as a finding

> **The property that removes the bridge confound is the property that starves the recovery metric.**

At 1000 nodes the network is richly connected, so it has no bridging edges — and for the same reason a 25-road break rarely touches the best route. `large1000` cannot be presented as strictly better. At `medium200`, **63 of 150 instances** carry over 10% of the optimal route on a single hop.

**`[raw]`**

---

## 11. Defects found, and what happened to them

### 11a. Pareto printed the null at `calm` — **confirmed, fixed**

**What was wrong.** With no disruptions there is nothing to recover from, so recovery is undefined. The dominance check returned "not comparable" on an undefined value, which meant no arm could dominate any other, and the tab printed *"the arms are not distinguishable"* — in the scenario built as a negative control. Over the three metrics that *are* defined there, `large1000/calm` has **33** dominance relations and `medium200/calm` has **13**.

**Why it mattered more than its size.** *"The arms are not distinguishable"* is the null. Reaching it automatically, from a code path that mishandled an empty column, is how a null gets manufactured instead of found.

**Fixed.** Dominance is now judged over the metrics both arms actually have, and the output names how many it used. Two tests, one driving the undefined-recovery branch.

> **Correction to the earlier write-up:** the illustrative figures quoted for this defect (`hybrid_direct` 2.44% vs `aco` 13.33%) are **`large1000`** numbers and were presented without naming the tier. At `medium200` the same pair reads 4.16% vs 4.92%, and `hybrid_direct` does **not** dominate `aco` there — it is worse on % at optimum. The defect is real at both tiers; that example only holds at one.

**`[raw]`**

### 11b. `delta` and `effect` disagree in sign — **confirmed, not a bug**

**What was observed.** In four `medium200` cells the mean difference points one way and the effect size the other.

**What it is.** Right skew, demonstrated on `calm/S2a`: the mean paired difference is **+0.0036** (hybrid worse) while the median is **−0.0044** and the hybrid wins on **90 of 150 seeds**. Four seeds carry differences of +11 to +23 percentage points, and the skewness of the paired differences is **+2.31**.

`delta` is a mean and is skew-sensitive; Cliff's delta counts how often one arm wins and is not. **They answer different questions and can legitimately disagree.** Where they do, the skew should be reported rather than one of them suppressed.

**`[raw]`**

### 11c. `% of steps at optimum` at `large1000` — **confirmed as a problem, but the stated fact was wrong**

**What is true.** The metric is nearly useless at `large1000`: the best any ranked arm achieves is **0.59%**, against 12–32% at `medium200`. Reading it from `medium200` is correct.

> **Correction:** the earlier write-up said *"0.0% for every arm in three of four scenarios."* Re-derived per arm, **every arm reads 0.0% in exactly one scenario — `calm`.** At light, moderate and severe the maxima are 0.16%, 0.58% and 0.59%. The metric is near-degenerate, not degenerate, and the ruling stands on the corrected figure.

**`[raw]`**

### 11d. The recovery floor — **two defects, both fixed**

**First**, the floor was applied to `calm`, where zero damaging events is the designed outcome, so it fired on the negative control and demoted the primary tier on the one scenario that could never pass.

**Second, and not previously noticed:** `MIN_DAMAGED_FOR_RECOVERY` is documented as a **per-arm** floor and the caller passed **totals summed over ten arms**. `large1000/light` arrived as 117 against a floor of 30 and passed, when its real per-arm count is **11.7** and it fails by a factor of three. **A units mismatch between a constant and its caller made the threshold ten times more lenient than it reads**, and nothing in the output looked wrong.

Both fixed; one test drives both branches and the run's own per-arm counts.

**`[raw]`**

---

## 12. ⚠️ The gap between the design and the implementation

**What this is.** The idea being tested is that the budget split should move *in proportion to how much of the world was disturbed* — a big break buying more budget for the memoryless half than a small one. The observation object carries a field with exactly that: `events_this_step`, the count of disruptions at each timestep. **Neither sensing policy reads it.**

Verified in source:

- `events_this_step: int` is declared on `AllocationObservation` (`observation.py:75`) and populated (`observation.py:132`).
- `DirectAllocation.propose` reads `obs.recency` and nothing else.
- `IncrementalAllocation.propose` reads `obs.recency` as its signal, plus `obs.current_fraction` and `obs.t` for step mechanics. **Neither reads `events_this_step`.**

`policies.py:92-93` states the exclusion and justifies it:

```
``events_this_step``        ignored — ``recency`` is already the
``steps_since_disruption``  decayed form of both
```

**That justification is false.** `recency` reads 1.0 on any disruption step and decays through quiet ones. It encodes *how long ago*, not *how much*. Decaying a magnitude-free signal does not reconstruct a magnitude. One road broken and twenty-five broken produce an identical reading — §8 measures exactly this, and it is why the signal reaches 1.0 on 54% of severe steps.

**Consequence.** The run tested allocation driven by **disruption recency**, not allocation **proportional to disruption magnitude**. The null is a true and well-evidenced result about the first. It is not a test of the second.

**Why this does not invalidate anything.** The experiment is internally sound, pre-registered and correctly analysed. None of the 34 cells change. What changes is the sentence the report may write about what was tested.

**Why it is worth more than a correction.** It converts future work from a gesture into a costed proposal: the field exists on all 720,000 rows, a magnitude-carrying policy is a change to one expression, and the rerun is 216 known minutes on the same 150 seeds.

**When the justification was written, and what that does and does not mean.**

The exclusion came first and the reasoning came after. `IncrementalAllocation` was written in **`aa3c3c5`** ("build allocation segment 20 phase 3"). The field-table line excluding `events_this_step` arrived six days later in **`4e4b6ad`** (2026-09-13, labelled "segment 22" but containing segment 21 — see Entry 022), and it was produced by **segment 21's T5**, a task whose instruction was *"`IncrementalAllocation` uses three of eleven fields. State it."*

So the sentence was written to **describe** an exclusion that already existed, not to decide one. Nobody weighed the magnitude and set it aside; the policy did not read it, and a later documentation pass wrote down a reason why that was acceptable. The reason was never checked against what `recency` actually encodes.

**This changes nothing about the run's validity.** It bears on *what was tested*, not on whether the test was sound. The experiment remains internally consistent, pre-registered and correctly analysed, and all 34 cells stand exactly as computed. What the history settles is a question the earlier write-up left open — whether this was a considered design decision or an unexamined assumption — and the commits say the second.

> **One precision note:** the phrase *"both read `obs.recency` and nothing else"* is exact for `DirectAllocation` and loose for `IncrementalAllocation`, which also reads `current_fraction` and `t`. The substantive claim — that neither reads the magnitude — holds for both.

```
grep -n "events_this_step" src/dynaswarm/allocation/observation.py
sed -n '/class DirectAllocation/,/def reset/p' src/dynaswarm/allocation/policies.py
```
**`[raw]`**

---

## 13. What is still not analysed

The run recorded 29 columns plus two map columns. After segment 25 the unused ones are `astar_expansions`, `path_len`, `best_path`, `params`, and the per-component probe fields (`tau_*`, `pso_*`, `exchanges`).

None of them bears on a pre-registered claim. All are recoverable from the same files.

---

**Nothing in this run was dropped for being unflattering (Entry 024). Every pre-registered comparison is reported as computed.**

**Provenance summary:** every section above is tagged **`[raw]`** — re-derived from the 720,000 parquet rows in segment 25. No section carries **`[analysis.txt]`**.
