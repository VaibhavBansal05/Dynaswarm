# FINDINGS_TESTS.md — what the evidence run measured

**Run:** `outputs/2026-09-19/18-43-05` · commit `b4d3d281266c985701abb3e0a7861364df60dff4` · `dirty: false`
**Date:** 19 September 2026
**Authoritative artefact:** `outputs/2026-09-19/18-43-05/analysis.txt` (282 lines). This document summarises it and does not replace it.

This file is the run's results in one place. The reasoning behind each ruling lives in `WORKFLOW_LOG.md` Entries 024, 028–033; the per-segment record lives in `findings/`.

---

## 1. The run

| | |
|---|---|
| trials | 1,200 — 150 seeds × 4 scenarios × 10 arms × 2 tiers |
| step rows | 720,000 (30,000 per chunk × 24 chunks) |
| `medium200` | 600 trials, 24.3 min, 2.43 s/trial at 8 jobs |
| `large1000` | 600 trials, 191.8 min, 19.18 s/trial at 8 jobs |
| total | 216 min |

Per-trial time held at 17.3–18.6 s for the first nine `large1000` chunks and rose to 20.3–23.8 s on the last three — consistent with thermal throttling on a fanless machine. **Wall-clock from this run is not uniform and any timing claim must carry that caveat.** Results are deterministic given the seed and are unaffected.

Architect's runtime projection was 57 min — wrong by ~4×. Recorded.

## 2. Verification performed before any result was interpreted

Each of these is a failure that would have produced entirely plausible numbers.

1. **24 chunk folders + `provenance.json`.** Verified by row count, not file count: 30,000 rows per chunk × 24 = 720,000 = 50 seeds × 10 arms × 60 timesteps × 24. An initial file-count check wrongly flagged all 24 as partial, having assumed 3 files per chunk where `ResultWriter` writes 2.
2. **`n_pairs` = 150 in all 34 non-degenerate cells, both tiers.** No seeds dropped. No cell pools scenarios — pooling would read 600.
3. **34 of 36 cells tested, 2 degenerate** — exactly `calm/P1` and `calm/P4` at both tiers, where the sensing arms are byte-identical to their twins because there is nothing to sense. The predicted pair and only that pair.
4. **Sign of `delta` correct**, cross-checked on two cells in opposite directions.
5. **`provenance.json` clean** at `b4d3d28`: `reproducible_from_commit: true`, 150 seeds listed individually, `parallel_jobs: 8`, Python 3.13.0, numpy 2.5.2, Darwin 25.0.0 arm64.

## 3. Statistical frame

- Every comparison is a **seed-by-seed paired difference** — both arms face a byte-identical world on each seed. Pairing reduced the spread from 4.110 (level) to 2.132 (paired).
- **Paired Wilcoxon signed-rank**, **Holm correction applied once across all 34 tested cells** of the 9 × 4 grid, giving α ≈ 0.0015.
- Effect size is **Cliff's delta**. Thresholds: negligible < 0.147, small < 0.33, medium < 0.474, large above.
- Every comparison was pre-registered in Entry 024 with three dated amendments, all before any result existed.

## 4. Results

### Claim 1 — the hybrid beats its own components

| | `large1000` | `medium200` |
|---|---|---|
| `hybrid` vs `pso` (S2b) | significant in **all 4** scenarios | significant in **all 4** |
| `hybrid` vs `aco` (S2a) | significant in **all 4**, δ ≈ −0.99, p_adj 7.8e-25 | significant in **1 of 4** (severe only) |

At `medium200/calm` the paired delta is **+0.0036** — nominally favouring ACO.

**Supported, with a scope qualification that must not be dropped.** The hybrid reliably beats PSO everywhere. It reliably beats ACO only at the larger problem size, and at 200 nodes only under severe disruption. `medium200` is the size at which every calibration in this project was performed, so a claim that holds at the unverified size and fails at the verified one is itself a finding.

### Claim 2 — adapting a parameter does not help

P4 (`aco_adaptive` vs `aco_fixed`) is **not significant in any of the 8 cells** at either tier.

**Reproduced.** This matters beyond itself: Claim 3 is only an interesting question because parameter adaptation had already been shown to fail. The premise survives.

### Claim 3 — allocation as the better-posed question

| comparison | `large1000` result |
|---|---|
| P1 `adaptive` vs `fixed` | never significant. Delta positive (adaptive worse) in **5 of the 6 cells where the arms differ** across both tiers; the two `calm` cells are degenerate. |
| P2 `direct` vs `fixed` | significant once, `light`, δ = −0.097 (negligible) |
| P5 `scheduled` vs `fixed` | never significant — blind movement neither helps nor costs |
| P3a `adaptive` vs `scheduled` | **significant at `severe`, δ = +0.100 — against the thesis** |
| P3b `direct` vs `scheduled` | **significant at `severe`, δ = +0.080 — against the thesis** |
| S1 `direct` vs `adaptive` | significant at `light`, δ = −0.105 |

12 of 34 cells significant at `large1000`; 5 of 34 at `medium200`.

Entry 024's pre-registered decision rule read: *a sensing arm beats fixed but not scheduled → what helped was varying the split, not sensing when to.* **Neither sensing arm beats fixed, and at `severe` both lose to `scheduled`** — the open-loop controller that ignores the world.

**A null, plus a directional signal against sensing at the highest disruption rate.**

### Magnitude versus significance

P3a and P3b clear α ≈ 0.0015 with δ = 0.100 and 0.080 — **negligible** on the same scale where Claim 1 scored 0.99. 150 paired seeds with halved noise will reliably resolve very small differences; that is power working as designed. **The correct statement is "reliably detectable, practically negligible."** A p-value does not stand in for a magnitude anywhere in this project's output.

### Dose-response

At `large1000`, P3a is monotone increasing: **+0.063 → +0.082 → +0.100** across light → moderate → severe. Only the event rate varies between scenarios (cluster size and horizon are held identical, with a test), so the ordering aligns with the single knob that was turned. Random variation has no mechanism for producing that alignment.

**No equivalent monotonicity at `medium200`** — P3a there reads −0.036 / +0.039 / +0.010.

Reported in `analysis.txt` as uncorrected and descriptive, correctly.

### Ranking, `large1000/severe` (mean excess, lower better)

| arm | mean excess |
|---|---|
| `hybrid_scheduled` | 2.99% |
| `hybrid_fixed` | 3.15% |
| `hybrid_direct` | 3.24% |
| `hybrid_adaptive` | 3.27% |
| `pso` | 4.19% |
| `aco` | 14.28% |

Every hybrid beats every single-algorithm arm comfortably. The four controlled hybrids then sit inside a 0.28-point band. **Splitting the budget is worth a great deal; how the split is moved is worth almost nothing.**

## 5. Primary tier

Entry 031 ruled `large1000` primary for the step-derived metrics and `medium200` for recovery, with `large1000`'s recovery still reported carrying its own n. Entry 033 amends one part of that.

| metric | primary tier | reason |
|---|---|---|
| mean excess | `large1000` | computed from every timestep; unaffected by damage rarity |
| worst excess | `large1000` | same |
| **% of steps at optimum** | **`medium200`** | **degenerate at `large1000` — 0.0% for every arm in three of four scenarios. A metric that takes one value cannot rank nine arms.** |
| recovery | `medium200` | 82.8–261.7 damaged events per arm against 11.7–42.9 at `large1000` |

`large1000`'s zeros and its recovery values are still printed with their n, not suppressed — a metric reading zero everywhere is itself a finding about the problem size.

### The evidence floor

`MIN_DAMAGED_FOR_RECOVERY = 30` per arm, set before the run at the low end of the projection.

| tier | light | moderate | severe |
|---|---|---|---|
| `large1000` | 11.7 ✗ | 31.8 ✓ | 42.9 ✓ |
| `medium200` | 82.8 ✓ | 238.2 ✓ | 261.7 ✓ |

`large1000/light` fails and is reported with its count, carrying no claim. **The floor does not move** — lowering it to admit `light` would be tuning a threshold to pass.

`calm` is excluded from the floor's population by definition: it has no disruptions by construction, so zero damaged events there is the designed outcome, not a shortage. The check as first written applied the floor to `calm` and therefore fired on the negative control (Entry 032).

### The structural tension, stated as a finding

> **The property that removes the bridge confound is the property that starves the recovery metric.**

At 1000 nodes the graph is richly connected — **zero bridging edges on all 150 instances** — so a 25-road break rarely touches the optimal route. The same connectivity that makes `large1000` free of the confound makes it nearly free of damage to recover from. They are not independent properties and `large1000` cannot be presented as strictly better.

At `medium200`, **63 of 150 instances carry over 10% of the optimal route on a single bridging hop.**

## 6. Defects found in `analysis.txt`

Found by the Architect reading the file after it was produced. Detail in Entry 033; fixes specified in segment 25.

**6a. The Pareto message at `calm` is false at both tiers.** It prints *"no arm is at least as good as another on every metric… the arms are not distinguishable"* while `hybrid_direct` reads 2.44% mean excess against `aco` at 13.33%, tied on % at optimum and better on worst excess. Likely cause: recovery is undefined at `calm` and the comparison treats an undefined metric as incomparable rather than absent. **"The arms are not distinguishable" is the null — reaching it automatically from a code path that mishandled an empty column, in the scenario built as a negative control, is how a null gets manufactured rather than found.**

**6b. `delta` and `effect` disagree in sign in at least four cells** — `medium200` calm/S2a (+0.0036 vs −0.107), light/P2, light/P3b, severe/P1. Heavy right skew is a plausible explanation and `medium200`'s worst-excess values of 236–892% fit it, but it is unverified. Pre-run check (4) tested a cell where the two agree, so it never exercised this case.

**6c. `% at optimum` degenerate at `large1000`** — see §5.

**6d. The floor included `calm`** — see §5.

## 7. ⚠️ The gap between the design and the implementation

**This is the most consequential finding in the run and it is not in `analysis.txt`.**

The thesis is that the ACO/PSO split should move **in proportion to how much of the world was disturbed** — a large break buying more of the budget for the memoryless component than a small one.

`AllocationObservation` carries **`events_this_step: int`** — the actual count of disruptions landing at `t`. The magnitude reached the policy layer. It was available.

`IncrementalAllocation` and `DirectAllocation` both read `obs.recency` and nothing else. `policies.py` states the exclusion explicitly in its own field table:

```
``events_this_step``        ignored — ``recency`` is already the
``steps_since_disruption``  decayed form of both
```

**That justification is false.** `recency` is 1.0 on any disruption step and decays over quiet steps. It encodes *how long ago*, not *how much*. Decaying a magnitude-free signal does not reconstruct the magnitude. One road broken and twenty-five broken produce the identical reading, and `events_this_step` — the one field that distinguishes them — is discarded by a comment asserting it is redundant.

**Consequence.** The run did not test the thesis as designed. It tested allocation driven by **disruption recency**, not allocation **proportional to disruption magnitude**. The null is a true and well-evidenced result about the first; it is not a test of the second.

**Why it is not an invalidating error.** The experiment is internally sound, pre-registered, and correctly analysed. Nothing about the 34 cells changes. What changes is the sentence the report is permitted to write about what was tested.

**Why it is the most valuable thing here.** It converts the future-work section from a gesture into a specific, costed, half-built proposal: the field already exists on all 720,000 rows and in the observation contract; a magnitude-carrying policy is a change to one expression, rerun on the same 150 seeds for a known 216 minutes. Anyone can check the claim and anyone can run the next experiment.

**How it was missed.** The same failure this project has caught repeatedly and logged as a standing rule: **a plausible sentence in a docstring standing in for a checked claim.** This is its highest-stakes instance, because the sentence justified discarding the only input the thesis required.

## 8. Not yet analysed

720,000 rows carry 29 columns plus two map columns. **The analysis to date has used one — `excess`.** Verified present and joinable on disk:

`alloc_proposed`, `alloc_applied`, `alloc_held_back`, `alloc_at_bound`, `aco_fraction`, `signal_value`, `path_valid`, `path_changed`, `wall_ms`, `rebind_ms`, `oracle_ms`, `step_wall_ms`, `astar_expansions`, `num_events`, and `seed` — which joins cleanly to `MANIFEST.json`'s instance table for all 150 `medium200` seeds.

**Two of the outstanding items are pre-registration commitments, not improvements:**

1. **The upper bound on every null.** Entry 024's decision rule states a null is reported *together with the bound the run establishes*. There is no confidence interval anywhere in the output. *"We found nothing"* and *"any true benefit is smaller than X"* are different sentences and only the second is a result.
2. **Conditioning on bridge share.** Entry 029 approved per-instance recording specifically so the report could answer *are the arms also indistinguishable on the instances with no dominant bridge?*

Nothing outstanding requires another run.

---

**Nothing in this run was dropped for being unflattering (Entry 024). Every pre-registered comparison is reported as computed.**
