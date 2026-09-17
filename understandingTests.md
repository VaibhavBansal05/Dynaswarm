# Understanding the experiment

**What `MANIFEST.json` is, and what this file is.** The manifest is a machine document: arms, seeds, config, provenance. It exists so the run can be reproduced exactly. It says *what* will be run and nothing about *why*.

This file is the why. Anyone — a supervisor, an examiner, a future you — should be able to read this alone and understand what the experiment asks, how it avoids fooling itself, and what each possible outcome would mean.

---

## 1 · The question

**When a shortest-path problem keeps changing, does it help to move compute between the two algorithms solving it?**

The hybrid has a fixed budget of 300 evaluations per timestep, divided between ACO and PSO. The **split** is that division. The thesis is that the split should move in response to how recently the map was disrupted — and that moving it is a better lever than tuning the algorithms' parameters.

Three claims:

| | |
|---|---|
| **Claim 1** | The hybrid beats ACO and PSO used alone |
| **Claim 2** | Adapting a *parameter* (ACO's evaporation rate ρ) does not help — and here is the mechanism |
| **Claim 3** | Adapting the *allocation* is the better-posed question |

Claim 2 is a negative result. Claim 3 is where it leads.

---

## 2 · What one trial is

A **seed** produces an entire world: the places, the roads, and the full sequence of disruptions for sixty timesteps. All of it fixed before any algorithm starts.

Then the clock runs. At each timestep:

1. the scheduled events fire — roads close, reopen, change price, appear, disappear
2. **A\* solves the map exactly**, giving the true shortest path for that step
3. every arm gets its 300 evaluations to find a route on the map as it now stands
4. each arm's answer is recorded as **excess** — how far above A\*'s optimum it landed

**Every arm sees the identical world, from identical random numbers.** That is what makes the whole experiment work: when two arms differ, the world cannot be the reason.

One trial produces 10 arms × 60 timesteps of rows.

---

## 3 · Why A\* is here

**A\* is the oracle, not a competitor.** Its job is to compute the true optimum so that "excess" means something.

It is not claimed to be beaten. At the graph sizes studied, A\* is faster than every metered arm by one to two orders of magnitude *and* exact — measured, and reported. The appropriate exact baseline for a *changing* graph is an incremental method such as **D\* Lite** or **LPA\***, which repairs the solution rather than re-solving; comparison against those is out of scope and is named in the report as the natural next step.

The question is: *given that a metaheuristic is being used, does adapting its allocation beat adapting its parameters?*

---

## 4 · Every knob, and why it is set that way

| Knob | Setting | Why |
|---|---|---|
| **seed** | **varies** — 100 per cell | The only axis averaged over. Each seed is another sample of the same question |
| **disruption preset** | **varies** — calm, light, moderate, severe | Reported separately, never pooled. The effect is *supposed* to depend on disruption, so averaging calm into severe would dilute the very thing being measured |
| **graph size** | **varies** — medium200, large1000 | Reported separately. Tests whether the finding generalises |
| graph model | geometric, fixed | Varying it adds cells without adding a question |
| density | default, fixed | A difficulty dial, not a question. Difficulty already varies across 100 seeds and the size jump |
| **search budget** | **300, fixed** | The allocation step size `A = 0.006` was **derived from** this budget — the floor constraint is `1/budget`. Change the budget and the derivation is void, and a win could not be attributed to allocation rather than budget |
| six event probabilities | fixed | These *are* the scenario — the presets differ in exactly these values |
| roads per break, duration | set by preset | Same |
| arms | all 10, always | They are the comparison itself |

---

## 5 · Why every comparison is a *pair*

Worlds differ enormously in difficulty. One seed's optimum is 99.96, another's is 110.45. Some break more roads; some have nastier geometry.

If each arm's results were averaged across 100 worlds and the averages compared, **most of what you would be measuring is world difficulty, not arm quality.**

So every comparison is done **seed by seed**. For each world, subtract one arm's result from the other's. Because both arms ran the *same* world from the *same* random numbers, the world's difficulty appears in both numbers and cancels.

From the six-seed pilot:

| | |
|---|---|
| spread of the raw levels | **4.110** |
| spread of the paired differences | **2.132** |

**Halving the noise, for free**, from a design decision made long before the run. The effect under test is 0.787 — visible against 2.132, invisible against 4.110.

Real data is messier than the ideal: pairing removed about half the noise here, not all of it. That is normal and it is still the difference between an answerable question and an unanswerable one.

---

## 6 · Every comparison, and which claim it serves

Nine comparisons, all pre-registered before any result existed.

### Claim 1 — the hybrid beats its components

| | Pair | Question |
|---|---|---|
| **S2a** | `hybrid` − `aco` | Does combining beat ACO alone? |
| **S2b** | `hybrid` − `pso` | Does combining beat PSO alone? |

Uses the **plain** `hybrid`, which has no control machinery at all — the right baseline for a claim about combining, not about controlling.

### Claim 2 — parameter adaptation does not help

| | Pair | Question |
|---|---|---|
| **P4** | `aco_adaptive` − `aco_fixed` | Does adapting ρ help? |

Two ACO arms identical but for whether ρ is allowed to move. **If this comes back showing adaptation helps, Claim 2 is contradicted by this project's own evidence and the argument for Claim 3 loses its premise.** That outcome is pre-registered and would be reported as prominently as any positive result.

### Claim 3 — allocation adaptation is the better lever

Four arms, each removing one alternative explanation for a win:

| Arm | What it is |
|---|---|
| `hybrid_fixed` | the split **cannot move** — pinned at exactly 0.5. The ablation twin |
| `hybrid_scheduled` | the split **moves on a timetable**, identically in a calm world and a violent one. It senses nothing |
| `hybrid_adaptive` | the split moves by **accumulating small steps** driven by disruption recency |
| `hybrid_direct` | the split is **set directly** from disruption recency — no accumulation |

| | Pair | Question it settles |
|---|---|---|
| **P1** | `hybrid_adaptive` − `hybrid_fixed` | Does sensing beat not moving? |
| **P2** | `hybrid_direct` − `hybrid_fixed` | Same, with the split provably in the right place |
| **P3a** | `hybrid_adaptive` − `hybrid_scheduled` | **Does sensing beat moving blindly?** |
| **P3b** | `hybrid_direct` − `hybrid_scheduled` | Same, for the direct arm |
| **P5** | `hybrid_scheduled` − `hybrid_fixed` | Does *any* movement help, independent of sensing? |
| **S1** | `hybrid_direct` − `hybrid_adaptive` | Does the *shape* of the response matter? |

**P3a and P3b are the ones the thesis lives on.** Beating `hybrid_fixed` only proves that movement helps. Beating `hybrid_scheduled` proves that *knowing when to move* helps — and that is the actual claim.

**P5 completes the logic.** Without it, if the adaptive arm beats fixed but ties with scheduled, you know sensing bought nothing but you cannot say whether movement bought anything either. With it, all three outcomes separate cleanly.

### Why P3 is two tests and not one

An earlier draft compared *"the best sensing arm"* against `hybrid_scheduled`. **That selects on the outcome** — you cannot look at two arms, pick whichever did better, and then test it, because you have effectively taken two shots and reported one, and the inflation leaves no trace in the result. Split into two pre-registered tests instead. More conservative, same intent.

---

## 7 · What is measured

Four metrics per arm per seed. Each one must pass a single test: *can you say in one sentence why more of it is better?*

| Metric | Why more is better |
|---|---|
| **mean excess** | closer to optimal, on average |
| **% of steps at optimum** | how often it was exactly right |
| **worst excess** | how bad its worst moment was |
| **mean steps to recover** | how fast it returned after a disruption |

**Deliberately excluded**, and the exclusions matter as much as the inclusions:

| Excluded | Why |
|---|---|
| hops | nobody argues fewer hops is better — a shorter route that costs more is worse |
| raw path cost | already inside excess, and it moves when the optimum moves |
| evaluations spent | identical across all metered arms by design, so it carries no information |

**Recovery is measured only over disruptions that actually caused damage.** About 80% of disruptions harm an arm not at all, and a recovery time of zero from an event that caused no degradation is not a fast recovery — it is a missing observation wearing a number. Including them dragged every arm toward zero and toward each other. Events that *improved* an arm's position (which happens) are counted separately again.

---

## 8 · The statistics, in plain terms

**Wilcoxon signed-rank, paired.** Takes the 100 per-seed differences and asks how unlikely that pattern would be if neither arm were better. Uses ranks rather than raw values, so one freak world cannot dominate.

**Holm correction, applied once across all nine comparisons.** Nine comparisons means nine chances to get lucky, so each must clear a higher bar. Correcting *within* each comparison instead would produce nine families of one — looking corrected and correcting nothing.

**Cliff's delta, reported beside every p-value.** A p-value says *this is probably not chance*. Cliff's delta says *and here is whether it matters*. With enough trials almost anything becomes statistically significant; a result that is significant and negligible is a true finding about a difference nobody would care about, and saying so is stronger than hiding it.

| |Δ| | Label |
|---|---|
| < 0.147 | negligible |
| < 0.33 | small |
| < 0.474 | medium |
| ≥ 0.474 | large |

**Why 100 seeds.** The pilot measured an effect of 0.787 against a paired spread of 2.132. The uncertainty in an average shrinks as the square root of the sample, so:

| Seeds | Uncertainty in the average | Effect vs its own uncertainty |
|---|---|---|
| 6 | 2.132/√6 = 0.87 | **smaller than its own uncertainty — invisible** |
| 58 | 0.28 | 2.8× — 80% power |
| 100 | **0.213** | **3.7× — comfortable** |

At six seeds the test could not have returned a result whatever the data said. At 100 it can.

---

## 9 · What each outcome means — decided in advance

Fixed before the run, so that no result can be re-interpreted after the fact.

| Outcome | Conclusion |
|---|---|
| A sensing arm beats `hybrid_fixed` **and** `hybrid_scheduled` | **Claim 3 supported.** Both must hold |
| Beats `hybrid_fixed` but **not** `hybrid_scheduled` | **What helped was varying the split, not sensing when to.** Reported as the finding, not buried |
| Beats neither | **A null, reported as a null**, with the upper bound the run establishes on how large the effect can be. A bound is a result |
| `hybrid_direct` beats `hybrid_adaptive` | The response *shape* matters independently of the target. Both reported |
| `aco_adaptive` beats `aco_fixed` | **Claim 2 is contradicted** and the report's argument is rewritten, not retained |

**Committed regardless of outcome:** no arm is added and no parameter changed after this point; every comparison is reported whatever it says; no comparison is dropped for being unflattering.

---

## 10 · Five further claims, free from the same data

| | |
|---|---|
| **Dose-response** | Does the benefit grow from light → moderate → severe? A spurious effect has no reason to scale with the thing it supposedly depends on, so this is far stronger evidence than a single significant difference |
| **Robustness to the bridge confound** | 40 of 100 `medium200` instances have a "bridging" road carrying over 10% of the optimal route. Split the seeds by that share and re-test |
| **Wall-clock efficiency** | One ACO evaluation costs ~7× more time than one PSO evaluation. The thesis arm shifts toward PSO, so it is systematically cheaper at an identical evaluation budget — measurable, ~5% |
| **Recovery vs steady-state** | Does an arm help by recovering faster, or by being better during calm? Different mechanisms |
| **Scale** | Does any of it hold at 1000 nodes? |

---

## 11 · Known limitations, stated up front

| | |
|---|---|
| **The bridge confound** | On 40% of `medium200` instances one road carries much of the route, so the problem is partly *"reach the bridge"* and arms may look alike for structural reasons. **`large1000` has zero bridges on every instance**, which makes the scale check an unplanned control: indistinguishable arms at both tiers answers the objection with data |
| **Recency is binary** | The signal reads 1.0 if anything broke. Nine roads and twenty-five produce the same number, so **no policy shape can recover a magnitude the signal discarded** |
| **The governor clamps the direct arm** | On 78% of steps. The three constraints on its amplitude are mutually unsatisfiable — a finding about the rate limiter, not the policy |
| **PSO ends runs idle** | Personal bests improved 93 → 0, swarm spread collapsed. Part of the hybrid's margin over PSO alone is simply that ACO is still working |
| **`hybrid` vs `hybrid_fixed` is not a clean pair** | They are in different random-stream families, so they differ in two ways. The cost of the control machinery itself is therefore not measured |
| **Exact methods dominate at these sizes** | A\* is faster and exact. D\* Lite is the appropriate exact baseline and is out of scope |

---

## 12 · Why any of this can be trusted

The instrument was built before the evidence, and it was attacked deliberately.

Every segment introduced **two deliberate defects** — one specified, one chosen by the implementer — and the suite had to catch them. Several times it did not, and each miss became a test:

- a timing change that rotated *who* each duration belonged to, leaving every total exact while inverting the entire cost story — passed 513 tests
- a tolerance raised from `1e-9` to `0.005`, reading as a rounding fix, which reordered the final ranking — passed 501 tests
- a provenance field reporting the working tree as clean while uncommitted work ran — passed everything, because the test checked the field *existed*
- a recovery average that silently dropped the cases where an arm never recovered, making a permanently-failing arm score eight times better than a reliable one

Thirteen defects were found and fixed across the project, several of them in the measuring instruments rather than the algorithms. **A human working through the system by hand found four more that 505 automated tests did not** — every one of them an instrument producing a plausible reading that carried no information.

The full record is in `WORKFLOW_LOG.md`, entry by entry, including the errors made by the person who designed the experiment.
