# Runbook

What to run, in what order, and what is still missing.

Timings below are measured on a 12-core laptop and scale roughly with
core count. Every experiment writes to its own timestamped directory
alongside the exact config that produced it, so nothing needs to be
recorded by hand.

---

## 0. Setup — 5 minutes

```bash
git clone https://github.com/VaibhavBansal05/Dynaswarm.git
cd Dynaswarm
python3 -m venv .venv
./.venv/bin/pip install -e ".[dev,viz]"
```

Needs Python 3.10 or newer. The `viz` extra pulls in pygame and is only
required for the live demo.

**Verify the install:**

```bash
./.venv/bin/pytest -q -m "not slow"     # ~35 s
./.venv/bin/ruff check src/ tests/ dashboard/
./.venv/bin/python -m dynaswarm.cli     # smoke run, ~10 s
```

If the suite passes, everything below will run.

---

## 1. The test suite

The suite is the project's standing claim that its mechanisms actually run —
the structural guards, the temporal invariants, and the boundary that keeps
the dashboard a view. **Run it for the count**; it changes every segment, so a
number written here would be wrong within the week. The `slow` tests run
tuning searches and are excluded by default; include them with `pytest -q`
before a release. The authoritative counts are recorded, dated, in
`WORKFLOW_LOG.md` — a number describing a moment cannot rot, while a number
claiming to be current always can.

Counts in the table below are as collected, several files being heavily
parametrised.

*Counts as collected on 30 Aug 2026. `test_hygiene` and `test_optimizers` are parametrised across source files and `PARAM_SPEC`, so these numbers move whenever a module or a parameter is added. Run `pytest --collect-only -q` for the current figures rather than trusting this table.*

| file | tests | what it protects |
|---|---|---|
| `test_hygiene.py` | 75 | no global RNG, no GUI imports, statement budget |
| `test_optimizers.py` | 40 | budget exactness, parameter liveness, A\* correctness |
| `test_control.py` | 30 | signal dynamic range, controller step sizes, the ablation |
| `test_environment.py` | 26 | graph construction, event clustering, timeline purity |
| `test_hybrid.py` | 25 | PSO encoding, budget splitting, component exchange |
| `test_config.py` | 20 | every config combination composes |
| `test_harness.py` | 20 | shared world, stream independence, reproducibility |
| `test_analysis.py` | 17 | recovery detection, Holm correction, effect sizes, figures |
| `test_tuning.py` | 11 | seed separation, per-arm parameter spaces |
| `test_rng.py` | 8 | stream stability under arm insertion |
| `test_testbed.py` | 4 | the tier in use can show the effect being claimed |

Several are worth knowing about individually, because they fail loudly on
mistakes that are otherwise silent:

- **`test_signal_discriminates_scenarios`** — a signal must read
  differently in calm and chaos, by a margin large enough to act on, not
  merely by a significant p-value.
- **`test_every_parameter_changes_behaviour`** — parametrised off
  `PARAM_SPEC`, so a newly added parameter cannot be introduced inert.
- **`test_budget_is_spent_exactly`** — equal allowance must mean equal
  work, whatever the population size.
- **`test_adding_an_arm_does_not_disturb_the_others`** — results must not
  depend on which other arms are running.
- **`test_pheromone_contributes_on_the_science_tier`** — the mechanism
  under study must do measurable work on the graphs in use, or a null
  result says nothing.

---

## 2. Experiments

> **Superseded as the reported programme.** The E1–E7 sequence below no longer
> defines what this project reports. The experiment manifest in
> `ARCHITECTURE.md` §13 does — tuning T1–T4 first, then E1–E12, every reported
> condition at ≥100 trials. The commands here remain valid as ad-hoc
> invocations for exploration and debugging, and runs they produce are
> `exploratory` and are never reportable.

Ordered so each one's result informs the next. Run them from a working
directory you are happy to fill with output.

### E1 — Do the algorithms behave? *(~6 min)*

```bash
./.venv/bin/python -m dynaswarm.cli --multirun \
  graph=medium200 scenario=static,low,moderate,high \
  'experiment.arms=[astar,aco,pso,hybrid]' \
  experiment.n_trials=30 experiment.parallel_jobs=11 report=true
```

**Check before trusting anything downstream:** A\*'s `excess` must be
exactly 0.0 in every row. It is exact by construction, so any drift means
the harness and the oracle disagree about what a path costs, and every
other number is measuring that disagreement.

```python
from dynaswarm.analysis.load import load_steps
steps = load_steps("multirun")
assert (steps[steps.arm == "astar"].excess == 0.0).all()
```

**Expected shape:** ACO around 8–9 % above optimum, PSO markedly worse,
hybrid at or below ACO with the gap widening as disruption rises.

### E2 — Tune each arm *(~15 min each)*

The comparison that matters is against a *well-chosen* fixed setting, not
a default. Each arm is searched over its own parameters — five for the
colony, six for the swarm, twelve for the hybrid including the budget
split.

```bash
for arm in aco pso hybrid; do
  ./.venv/bin/python -m dynaswarm.cli \
    tuning.enabled=true tuning.arm=$arm \
    tuning.candidates=60 tuning.trials=12 \
    graph=medium200 scenario=high experiment.parallel_jobs=11
done
```

Each writes `best_fixed.json` into its run directory. Tuning draws only
from `experiment.tune_seeds`, which is disjoint from the evaluation pool;
the run refuses to start otherwise.

**Tune per graph tier.** The best parameters are not transferable: β came
out at 0.95 on a 30-node graph and 5.59 at 200 nodes.

### E3 — Does the hybrid beat its components? *(~10 min)*

The project's original question. Feed in E2's hybrid vector so the
comparison is between tuned methods.

```bash
./.venv/bin/python -m dynaswarm.cli --multirun \
  graph=medium200 scenario=moderate,high \
  'experiment.arms=[aco,pso,hybrid]' \
  tuning.params_file=/abs/path/to/best_fixed.json \
  experiment.n_trials=30 experiment.parallel_jobs=11 report=true
```

```python
from dynaswarm.analysis.load import load_steps, per_trial_excess
from dynaswarm.analysis.stats import compare_arms

per_trial = per_trial_excess(load_steps("multirun"))
print(compare_arms(per_trial, "hybrid", "aco", within=("scenario",)))
```

Read `p_holm`, not `p_value`, and read `cliffs_delta` beside it. A
significant p-value on a negligible effect is not a result.

**Current standing:** at 10 trials the hybrid reached 7.1 % against ACO's
9.3 % in the busiest scenario, p = 0.004. Thirty trials on one tier would
make that solid rather than suggestive.

> **Provisional.** These figures come from runs not present in this repository and cannot be verified here. They are superseded by the regeneration programme in `ARCHITECTURE.md` §13, which reports at ≥100 trials. Do not cite them.

### E4 — Does allocation help? *(~20 min)*

The remaining open question, and the one nobody has answered. Both arms
are the same hybrid with the same random stream; one may shift its budget
between colony and swarm as disruption arrives, the other may not.

```bash
./.venv/bin/python -m dynaswarm.cli --multirun \
  graph=medium200 scenario=moderate,high \
  control.signal=recency 'control.targets=[aco_fraction]' \
  control.sigma=0.01 \
  'experiment.arms=[hybrid_fixed,hybrid_adaptive]' \
  tuning.params_file=/abs/path/to/best_fixed.json \
  experiment.n_trials=30 experiment.parallel_jobs=11 report=true
```

**Check the controller actually moved, and did not simply saturate.**
A null result means nothing if the split never shifted, and a positive
one means little if the split just pinned to a bound and stayed there —
that is a fixed arm with extra steps.

```python
steps = load_steps("multirun")
adaptive = steps[steps.arm == "hybrid_adaptive"]
fractions = [p["aco_fraction"] for p in adaptive.params]
assert len(set(fractions)) > 1, "the controller never shifted the split"
at_bound = sum(f <= 0.051 or f >= 0.949 for f in fractions) / len(fractions)
assert at_bound < 0.2, f"split pinned to a bound for {at_bound:.0%} of steps"
```

**Choosing sigma.** Over 60 timesteps the split can drift at most
`60 x sigma`, against a range of 0.9. Measured on geometric n=200 at the
moderate rate, the observed span was:

> **Provisional.** These figures come from runs not present in this repository and cannot be verified here. They are superseded by the regeneration programme in `ARCHITECTURE.md` §13, which reports at ≥100 trials. Do not cite them.

| sigma | span of `aco_fraction` |
|---|---|
| 0.002 | 0.468 → 0.500 |
| 0.005 | 0.420 → 0.500 |
| **0.01** | **0.340 → 0.500** |
| 0.02 | 0.180 → 0.500 |

0.01 gives room to move without pinning. Higher rates push harder — at
0.8 events per step on a small graph, 0.02 drove the split to its lower
bound — so re-check saturation whenever the scenario changes.

### E5 — Is recomputation expensive enough to matter? *(~40 min)*

A\* is exact, so it can only be beaten on cost. If its cost does not grow
with graph size, the premise motivating the whole project does not hold at
these scales — which is worth knowing either way.

```bash
./.venv/bin/python -m dynaswarm.cli --multirun \
  graph=small30,medium200,large1000 scenario=moderate \
  'experiment.arms=[astar,aco,hybrid]' \
  experiment.n_trials=12 experiment.parallel_jobs=11 report=true
```

```python
from dynaswarm.analysis.plots import save, scaling
save(scaling(load_steps("multirun")), "figures/scaling.png")
```

`large1000` takes roughly 11 s per trial per four arms, so budget
accordingly.

### E6 — Where does the advantage live? *(free, reuses E3)*

Mean excess averages a whole trial and hides anything confined to the few
steps after a disruption. The hybrid's rationale is precisely such an
effect, so it has to be looked at directly.

```python
from dynaswarm.analysis.recovery import per_trial_recovery
from dynaswarm.analysis.plots import recovery_profile, save

steps = load_steps("multirun")
print(per_trial_recovery(steps).groupby("arm")[
    ["mean_damage", "mean_recovery", "settled_excess"]].mean())
save(recovery_profile(steps), "figures/recovery.png")
```

If the hybrid's advantage is real and mechanistic, it should show up as
lower `mean_damage` or faster `mean_recovery` while `settled_excess`
stays comparable. If instead it wins uniformly, the stated rationale is
wrong even though the result stands — worth saying so.

### E7 — The demo *(interactive)*

```bash
./.venv/bin/python -c "
from dynaswarm.viz.replay import replay
replay('outputs/<date>/<time>', arm='hybrid', trial=0)"
```

Space pauses, arrow keys step, `q` quits. Replays recorded results, so it
cannot perturb a run. Capped at 400 nodes — use `small30` or `grid20`.

---

## 3. What is left

### Blocking nothing, but genuinely unfinished

| item | why it matters |
|---|---|
| **E4 has never been run** | The allocation thesis is the project's stated novelty and remains untested. Everything needed exists. |
| **Hybrid uses an untuned 50/50 split** | The headline hybrid result comes from an arbitrary split. E2 fixes this and may well improve it. |
| **One graph tier** | Every result is from geometric n=200. Whether the hybrid's advantage survives at other sizes is unknown. |
| **10 trials** | Enough to see a large effect, not enough to bound a small one. Trial variance runs 5–12 %, so ~30 trials is the minimum for a claim. |

### Known limitations, documented and tested

- **PSO scores ~83 % on `small30`.** Erdős–Rényi graphs have no
  coordinates, so neither A\*'s heuristic nor the swarm's goal term has
  anything to work with. Report from geometric tiers; `test_testbed.py`
  enforces the distinction.
- **`volatility` saturates above a few events per step.** It asks only
  whether anything changed, so past roughly four events per timestep it
  pins at 1.0 and a controller driven by it cannot move.
- **`lambda_branch` does not track disruption**, and should not — it
  measures colony stagnation. Useful as a stagnation detector, useless as
  a volatility proxy.
- **`prescheduled` is implemented but unexercised.** Stützle et al. found
  open-loop schedules helped where feedback did not, so it is the honest
  control for feedback itself, and running it would strengthen any claim
  about the controller.
- **`grid20` is untested at scale.** Corner-to-corner queries on a
  uniform grid are the worst case for A\* pruning, since every node lies
  on some optimal path.

### Deliberately out of scope

Reinforcement-learning control, real traffic data, multi-objective
routing, and distributed execution. All were listed as future work in the
original brief and none is needed for the current claims.

---

## 4. Reading results honestly

Four habits the codebase is built around, worth keeping:

**Pair on trials, never timesteps.** Sixty steps within one trial share a
graph and an event sequence; treating them as independent inflates the
sample sixtyfold and will find significance almost anywhere.

**Report `p_holm`, not `p_value`.** A signal-by-scenario grid runs a dozen
tests, and one in twenty clears 0.05 by chance.

**Read the effect size.** `cliffs_delta` sits beside every p-value. With
enough trials a tenth of a percentage point becomes significant and still
does not matter.

**Look at the per-trial scatter before believing a mean.** Trial variance
has repeatedly exceeded the gap between arms in this project;
`arm_comparison.png` plots every trial for exactly that reason.

---

## 5. Reproducing a result

Every run directory holds `manifest.json` — git commit, package versions,
resolved config — and `.hydra/config.yaml`. To repeat a run exactly:

```bash
./.venv/bin/python -m dynaswarm.cli --config-dir <run>/.hydra --config-name config
```

Seeds are the trial's entropy, not a label, so the same seed gives the
same graph and the same event sequence. Two runs of the same config
produce byte-identical `steps.parquet` — `test_trials_reproduce_exactly`
enforces it, excluding only wall-clock timings.

---

## 6. The dashboard

A **local development server**. Not hosted, not exposed, not deployed —
web deployment is out of scope (synopsis O1), and this stays inside that
boundary by binding to the loopback address only.

**Install the extra** (it is not part of `dev` — the core installs and
tests without a web stack):

```bash
./.venv/bin/pip install -e ".[dashboard]"
```

**Start it:**

```bash
./.venv/bin/python -m dashboard.server
```

Then open <http://127.0.0.1:8000>. Stop it with Ctrl-C.

The port is **8000** and the host is **127.0.0.1**, both fixed in
`dashboard/server.py:main()`. Nothing outside this machine can reach it.

### What it shows today

As of segment 6 the dashboard is a **scaffold**: it proves the pipe, and
draws nothing. The page renders, as text, one `medium200` graph built by
the real engine — node and edge counts, the endpoints `build()` chose,
and the true shortest-path cost from `core.oracle` — plus which run
classes exist under `outputs/`. Graph rendering arrives in segment 7.

Two endpoints back it:

```bash
curl -s localhost:8000/api/graph          # one graph, described
curl -s localhost:8000/api/runs           # run classes present, plus the D32 caveat
```

`/api/graph` takes `?seed=` and `?tier_name=` if you want a different
graph; the defaults are seed 1000 (trial 0's evaluation seed) and
`medium200`. **`small30` carries no coordinates** — it is Erdős–Rényi —
so anything visual built on it is a meaningless tangle. That is why the
research tier is the default and not a convenience.

### The one rule

The dashboard **imports `dynaswarm`; `dynaswarm` never imports the
dashboard**, and it computes nothing for itself — every number it shows
is asked of the core. `tests/test_dashboard.py` enforces both, including
a test that compares the endpoint's A\* expansion count against the
core's. That count depends on the search's own tie-breaking, so it
catches a *plausible* reimplementation, not merely a missing route.
