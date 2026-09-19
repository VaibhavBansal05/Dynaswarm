# FINDINGS — Segment 24: the evidence run and the pre-registered analysis

**Status:** COMPLETE. Uncommitted at time of archiving.
**Run:** `outputs/2026-09-19/18-43-05` · commit `b4d3d281266c985701abb3e0a7861364df60dff4` · `dirty: false`
**Raw analysis output:** `outputs/2026-09-19/18-43-05/analysis.txt` (282 lines) — the authoritative artefact. This file summarises it; it does not replace it.

> **Protocol note.** vClaude reported segment 24 in chat and did not append a FINDINGS block to `currentWorkFlow.md`. This archive was assembled by the Architect from vClaude's chat report plus independent reading of `analysis.txt` and `provenance.json`. **Standing correction: segment 25 onward, the FINDINGS block goes in the file before the chat report, or the chat report is the only record and the file loses it.**

---

## The run

| | |
|---|---|
| trials | 1,200 — 150 seeds × 4 scenarios × 10 arms × 2 tiers |
| step rows | 720,000 (30,000 per chunk × 24 chunks) |
| `medium200` | 600 trials, 24.3 min, 2.43 s/trial at 8 jobs |
| `large1000` | 600 trials, 191.8 min, 19.18 s/trial at 8 jobs |
| total wall clock | 216 min |
| Architect's projection | 57 min — **wrong by ~4×** |

Per-trial time held at 17.3–18.6 s for the first three quarters of `large1000` and rose to 20.3–23.8 s on the last three chunks. Consistent with thermal throttling on a fanless machine. **Affects the timing table only** — results are deterministic given the seed.

## The five pre-run verifications

1. **24 chunk folders + `provenance.json`.** vClaude's first pass flagged all 24 as partial, having assumed 3 files per chunk where `ResultWriter` writes 2 (`steps.parquet`, `events.parquet`). Re-verified by row count: 30,000 per chunk, 720,000 total = 50 × 10 × 60 × 24. Independently confirmed by the Architect: the directory held exactly 25 entries before analysis ran, 27 after `analysis.txt` and `run.log` were written.
2. **`n_pairs` = 150 in all 34 non-degenerate cells, both tiers.** Confirmed by the Architect reading `analysis.txt` — every row reads `n 150`. No seeds dropped, and no cell pools scenarios (pooling would read 600).
3. **34 of 36 tested, 2 degenerate** — exactly `calm/P1` and `calm/P4`, at both tiers. The predicted pair and only that pair.
4. **Delta sign correct**, cross-checked on two cells in opposite directions.
5. **`provenance.json` clean** at `b4d3d28`, `reproducible_from_commit: true`, 150 seeds listed individually, `parallel_jobs: 8`, Python 3.13.0, numpy 2.5.2, Darwin 25.0.0 arm64.

## The primary-tier condition, and the flaw it exposed

`primary_tier_holds()` returned `medium200` because `large1000/calm` recorded 0 damaged disruptions against a floor of 30.

Zero is the designed outcome at `calm` — it has no disruptions by construction, and `medium200/calm` is also 0. The floor fired on the negative control.

Damaged disruptions, excluding `calm`:

```
large1000   light 117    moderate  318   severe  429      (11.7 / 31.8 / 42.9 per arm)
medium200   light 828    moderate 2382   severe 2617      (82.8 / 238.2 / 261.7 per arm)
```

vClaude did not change the check and reported the result as computed. **Ruled by the Architect in Entry 032:** the floor is computed over scenarios with a nonzero event rate; `calm` is excluded by definition. The floor itself stays at 30, so `large1000/light` at 11.7 per arm fails it and carries no claim.

## Results as computed

**Claim 1 — supported at `large1000`, materially weaker at `medium200`.**

`hybrid vs pso` (S2a/S2b) is significant in all four scenarios at **both** tiers. `hybrid vs aco` is significant in all four scenarios at `large1000` (δ ≈ −0.99, p_adj 7.8e-25) but in **only 1 of 4** at `medium200` — severe only — and at `medium200/calm` the paired delta is **positive** (+0.0036), i.e. nominally favouring ACO.

**Claim 2 — reproduced.** P4 (`aco_adaptive vs aco_fixed`) not significant in any of the 8 cells at either tier.

**Claim 3 — a null, with a directional signal against the thesis at `severe`.**

| | `large1000` |
|---|---|
| P1 `adaptive` vs `fixed` | never significant; delta positive in 7 of 8 cells across both tiers |
| P2 `direct` vs `fixed` | significant once, `light`, δ = −0.097, negligible |
| P5 `scheduled` vs `fixed` | never significant |
| P3a `adaptive` vs `scheduled` | **significant at `severe`, δ = +0.100, against the thesis** |
| P3b `direct` vs `scheduled` | **significant at `severe`, δ = +0.080, against the thesis** |
| S1 `direct` vs `adaptive` | significant at `light`, δ = −0.105 |

12 of 34 cells significant at `large1000`; 5 of 34 at `medium200`.

**Dose-response, `large1000`.** P3a is monotone increasing: +0.063 → +0.082 → +0.100 across light → moderate → severe. The sensing disadvantage grows with disruption rate. Reported as uncorrected and descriptive in `analysis.txt`, correctly. **No equivalent monotonicity at `medium200`** — P3a there reads −0.036 / +0.039 / +0.010, non-monotone.

## What has NOT been analysed

720,000 rows carry 29 columns plus two map columns. **The analysis to date has used one — `excess`.** vClaude verified on disk that all of the following are present and joinable:

- `alloc_proposed`, `alloc_applied`, `alloc_held_back`, `alloc_at_bound`, `aco_fraction`, `signal_value` (in the probe map — confirmed persisted through Parquet)
- `path_valid`, `path_changed`
- `wall_ms`, `rebind_ms`, `oracle_ms`, `step_wall_ms`
- `astar_expansions`, `num_events`
- `seed` — joins cleanly to `MANIFEST.json`'s instance table; all 150 `medium200` seeds covered, so the bridge-share conditioning is one groupby away

**Two of the unanalysed items are pre-registration commitments, not opportunities:** the upper bound on the null (Entry 024's decision rule states a null is reported *with* the bound) and the bridge-share conditioning (Entry 029 approved per-instance recording specifically so the report could answer it). Both are outstanding.

Nothing in the outstanding work requires another run.

---

## Architect's independent verification — four items vClaude's report did not surface

Read directly from `analysis.txt`, not from the chat summary.

**1. Claim 1's `medium200` weakness was not in the chat report.** The phrasing given was *"significant in all four scenarios at `large1000`"* — accurate, and it omits that S2a fails in 3 of 4 cells at the tier where every calibration in this project was performed. The Architect propagated the strong version. Corrected here and in Entry 033.

**2. `delta` and `effect` disagree in sign in at least four cells.** `medium200/calm` S2a reads delta **+0.0036** with effect **−0.107**; `medium200/light` P2 reads −0.0004 with +0.022; `medium200/severe` P1 reads +0.0025 with −0.000; `medium200/light` P3b reads +0.0012 with −0.009. A paired mean difference and a rank-based effect size can legitimately disagree under heavy right skew — and `medium200` worst-excess values of 236–892% are exactly that. **But it is currently unexplained, and verification check (4) tested a cell where the two agree, so the sign check did not exercise this case.**

**3. `% of steps at optimum` is degenerate at `large1000`** — 0.0% for every arm in calm, light and moderate, with two exceptions at 0.1–0.6%. Against 12.2–32.3% at `medium200`. **Entry 031 ruled `large1000` primary for that metric. The ruling is not viable as written** — the metric carries no information at that tier.

**4. The Pareto message at `calm` is wrong at both tiers.** It reads *"no arm is at least as good as another on every metric. The ordering above is an artefact of averaging ranks — on this run the arms are not distinguishable."* At `large1000/calm`, `hybrid_direct` is 2.44% mean excess against `aco` at 13.33%, equal on % at optimum (0.0) and better on worst excess (11.56% vs 164.23%). That is domination. The most likely cause is that recovery is undefined (`—`) at `calm` and the comparison treats an undefined metric as incomparable rather than as absent. **The message is a substantive claim — "the arms are not distinguishable" — and the data contradicts it by a factor of five.**

Items 3 and 4 are the same failure this project has caught repeatedly: **output that reads plausibly and asserts something the data does not support.**
