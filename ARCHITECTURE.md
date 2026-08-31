# ARCHITECTURE — Dynaswarm

> **The target design.** This is the contract every `currentWorkFlow.md` segment implements.
> It describes what the system **should be**, not everything it currently is.
>
> **Precedence (D24).** For what the system should be: **`ARCHITECTURE.md` > `decisionLedger.md` > `AGENT_PROTOCOL.md`.** For how we work: `AGENT_PROTOCOL.md`. `WORKFLOW_LOG.md` is history, never authority. `currentWorkFlow.md` may narrow a segment's scope but never contradict — a contradiction is a defect to report, not a licence.

**Contents**

1. [Thesis and claim structure](#1-thesis-and-claim-structure)
2. [System overview](#2-system-overview)
3. [Technology stack](#3-technology-stack)
4. [The environment](#4-the-environment)
5. [The optimizers](#5-the-optimizers)
6. [The Hybrid](#6-the-hybrid)
7. [The control layer — redesigned](#7-the-control-layer--redesigned)
8. [The evidence set](#8-the-evidence-set)
9. [The arms, and the display-name map](#9-the-arms-and-the-display-name-map)
10. [The harness and its invariants](#10-the-harness-and-its-invariants)
11. [Evaluation and statistics](#11-evaluation-and-statistics)
12. [Run provenance](#12-run-provenance)
13. [The experiment manifest](#13-the-experiment-manifest)
14. [Inversion ablations](#14-inversion-ablations)
15. [The dashboard](#15-the-dashboard)
16. [Testing strategy](#16-testing-strategy)
17. [Phase plan](#17-phase-plan)
18. [Out of scope](#18-out-of-scope)

---

## 1. Thesis and claim structure

### 1.1 The problem

Find the shortest path through a network that keeps changing. Roads close, traffic spikes, links appear and vanish. Exact recomputation (A\*) is correct but stateless — it pays a full re-search for every change. Population methods (ACO, PSO) carry knowledge across time and adapt cheaply, at the cost of optimality.

### 1.2 The mechanism the project rests on

**ACO's memory lives on edges. PSO's memory lives on nodes.** That single difference produces complementary failure modes:

| | ACO | PSO |
|---|---|---|
| Steady state | strong (~5–10% excess) | weak (~9–32%) |
| Immediately after a disruption | **badly damaged** — pheromone still points down a closed road, and only slow evaporation clears it | **largely unaffected** — a node ranking survives a closure; only the remembered *cost* is invalidated |

The Hybrid is a bet that the memoryless component covers the memory component's known failure window. **This is falsifiable**: if true, the Hybrid's advantage should concentrate in the timesteps just after a disruption, not spread evenly. Testing that is a first-class experiment, not an afterthought.

### 1.3 The claim structure (D1)

Three claims, in this order. The architecture serves all three, and the report presents them in this sequence.

**Claim 1 — the Hybrid beats both of its components.** Positive, already evidenced, and it opens.

**Claim 2 — adapting parameters to volatility does not help, and here is why it cannot.** Against a *tuned* opponent no scenario favours adaptation, and the only significant ablation result favours the frozen arm. The diagnosis is the valuable half: tuning separately per volatility level and cross-evaluating every vector on every scenario shows **the optimal parameters do not depend on volatility at all**, so a volatility-driven controller has nothing to steer by. The null follows from the problem, not from a broken controller.

**Claim 3 — so we asked a different question: allocation.** Not *what parameters to use*, but *how much of a fixed compute budget goes to the explorer versus the refiner*, driven by **how recently a disruption landed** rather than by how volatile the environment is. The distinction matters: the sweep in Claim 2 proved the steady-state *rate* is uninformative, but said nothing about *transients*. This is the project's novelty, and it is currently **untested** — see F1.

### 1.4 What the architecture optimises for

Claim 3. The control layer is rebuilt so allocation is a first-class concept rather than one entry in a parameter table (§7). Claims 1 and 2 remain fully reproducible through the evidence set (§8), and the harness rigour that makes a null result meaningful is the foundation all three stand on.

---

## 2. System overview

### 2.1 Layers

```
┌──────────────────────────────────────────────────────────────────┐
│  dashboard/            web UI — OUTSIDE src/, imports dynaswarm  │
│                        FastAPI + plain JS · view, never engine   │
└──────────────────────────────────────────────────────────────────┘
                                  │ imports
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│  CLI              dynaswarm.cli — Hydra entrypoint               │
├──────────────────────────────────────────────────────────────────┤
│  TUNING           tuning/best_fixed — Optuna TPE, seed-separated │
├──────────────────────────────────────────────────────────────────┤
│  HARNESS          harness/{arm, trial, runner}                   │
├──────────────────────────────────────────────────────────────────┤
│  ALLOCATION       allocation/{policy, observation, governor}     │
│  (new)            allocation as a first-class control concept    │
├──────────────────────────────────────────────────────────────────┤
│  EVIDENCE         evidence/{signals, controllers}                │
│  (demoted)        parameter-adaptation machinery, runnable only  │
│                   for reproducing Claim 2                        │
├──────────────────────────────────────────────────────────────────┤
│  OPTIMIZERS       optimizers/{protocol, astar, aco, pso, hybrid, │
│                   spec}                                          │
├──────────────────────────────────────────────────────────────────┤
│  ENVIRONMENT      core/{rng, graphview, generate, events,        │
│                   timeline, oracle, meter}                       │
├──────────────────────────────────────────────────────────────────┤
│  IO / ANALYSIS    io/{schema, writer} · analysis/{load, stats,   │
│                   recovery, plots}                               │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 Repository layout (target)

```
Dynaswarm/
  ARCHITECTURE.md          this file — the contract
  AGENT_PROTOCOL.md        how the Architect and vClaude work
  decisionLedger.md        every settled decision, defects, open items
  WORKFLOW_LOG.md          append-only history of completed segments
  currentWorkFlow.md       exactly one segment of work

  src/dynaswarm/           the science surface — statement cap 2000
    core/                  environment, RNG, budget meter, oracle
    optimizers/            A*, ACO, PSO, Hybrid, protocol, param spec
    allocation/            NEW — allocation policies and governor
    evidence/              DEMOTED — old signals and parameter controllers
    harness/               arms, trial loop, runner
    io/                    Parquet schema and writer
    analysis/              load, stats, recovery, plots
    tuning/                Optuna best-fixed search

  dashboard/               NEW — web UI, statement cap 1000
    server.py              FastAPI app
    api/                   endpoints
    static/                index.html, app.js, style.css — no build step

  conf/                    Hydra config groups
  scripts/                 cross_evaluate.py (F3)
  experiments/             the experiment manifest (§13)
  tests/
  outputs/                 run directories (gitignored)
```

### 2.3 Non-negotiable structural rules

| Rule | Enforced by |
|---|---|
| `dynaswarm` never imports `dashboard` | package direction + hygiene test |
| The dashboard never reimplements graph generation, event application, optimizer logic or metric computation — **not even for display** | code review + the fact it has no access to those internals |
| No global RNG anywhere; all randomness flows through `core.rng.stream()` | `test_hygiene` |
| No GUI imports inside `core/`, `harness/`, `analysis/` | `test_hygiene` |
| Science surface ≤ **2000** executable statements | `test_statement_budget` |
| Dashboard surface ≤ **1000** executable statements | new test, mirroring the above |

The statement caps are brakes on scope, not budgets to spend. Breaching one is a signal to stop and report, never to delete unrelated code (D13).

> **The science cap will need raising at Phase 3, and it rises — it is never exempted.** Measured: 1984 today, 1826 after `viz/replay.py` retires, leaving 174 of headroom. The `control/` → `evidence/` demotion is a move and is statement-neutral. Phase 0.5's timeline instrumentation and Phase 3's `allocation/` package both draw on that 174, and `allocation/` is **science, not presentation** — so the dashboard's separate-cap reasoning does not transfer and a carve-out would be a dodge.
>
> The justification for raising it is real rather than convenient: the thesis moved, and the science surface now legitimately carries **two** control paradigms — allocation live, parameter adaptation preserved as reproducible evidence. **The new number is fixed when the Phase 3 segment is written, from a measured design sketch, and recorded as a superseding decision.** Never mid-segment, never by guessing, never by deleting other code.

---

## 3. Technology stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python ≥ 3.10 | |
| Numerics | NumPy, SciPy | vectorised bulk operations; Wilcoxon |
| Graphs | NetworkX (construction only) | promised in the synopsis; hot paths use raw CSR arrays |
| Data | pandas, PyArrow (Parquet) | columnar, typed, fast to reload |
| Config | Hydra + dataclasses | the dataclass *is* the schema; a mistyped key fails at compose time |
| Tuning | Optuna (TPE) | sequential Bayesian search |
| Parallelism | joblib | over trials, never over Optuna candidates |
| Plots | Matplotlib | static figures for the report |
| Dashboard | FastAPI + uvicorn + plain JS | no build step, no framework, no bundler |
| Tests | pytest | |
| Lint | ruff | |

**Retired:** Pygame and `viz/replay.py`, once the dashboard covers them (D17 — verified safe; `test_replay_reads_what_it_needs_from_results` never imports the replay module and becomes a schema guard for the dashboard instead).

**Not used:** Streamlit, Dash, React, any JS bundler, any deep-learning framework.

---

## 4. The environment

### 4.1 Graph representation

Two objects, split by what changes and what does not.

**`Topology`** — fixed for the whole trial: CSR `indptr` / `indices`, `rev` (reverse-arc slot index), `base_weight`, `base_active`, `pos` (coordinates, spatial models only), `weight_scale`.

**`GraphView`** — one timestep's frozen state: `weight[]`, `active[]`, `t`.

**The static topology superset.** Addition events need somewhere to add edges *to*. Rather than rebuilding a dictionary on every mutation, a bounded pool of candidate edges is pre-allocated alongside the base edges, and edges are switched on and off through the `active` mask. The consequence that matters: **the slot for an edge persists whether or not the edge is active**, so pheromone can live in a flat `float64` array indexed by slot with no reallocation, ever.

> **What happens to a trail across deactivation — stated precisely, because two wrong versions are in circulation.** The *slot* survives, but the *value* does not: `ACO.rebind()` deliberately zeroes the trail on any slot that has gone inactive. Nor does it stay at zero — when the edge reopens, `_clamp_trails()` lifts every active slot to `tau_min` at the end of the next iteration, so the edge returns **at the floor**. So it neither "keeps the trail it had" nor is "zeroed forever." An earlier draft of this document and `core/graphview.py`'s module docstring both say the former; §5.2 and the code are correct, and the docstring is a defect to fix.

Operations: `state_hash()` (Blake2b over `weight` and `active`) · `path_cost(path)` (`inf` if any edge is inactive) · `find_slot(u, v)` (binary search in the sorted CSR row).

### 4.2 Graph models and tiers

| Model | Structure | Coordinates | Role |
|---|---|---|---|
| `geometric` | points in the unit square, connected within a radius | ✓ | **the research model** |
| `grid` | N×N lattice, 4-connected, Manhattan metric | ✓ | worst case for A\* pruning |
| `erdos_renyi` | each pair connected with probability `density` | ✗ | **debug only** |

Build sequence: sample topology → `_ensure_connected()` (union-find) → `_addable_pool()` → `_to_csr()` → `_endpoints()` (source = node 0, target = farthest reachable node).

Spatial weights are `weight_min + dist × (weight_max − weight_min)`, which is what makes A\*'s heuristic admissible.

**Canonical tiers (D8):**

| Tier | Model | n | density | Status |
|---|---|---|---|---|
| `medium200` | geometric | 200 | 0.04 | **primary — all headline claims** |
| `large1000` | geometric | 1000 | 0.01 | **secondary — generality check** |
| `grid20` | grid | 400 | — | optional |
| `small30` | erdos_renyi | 30 | 0.3 | **debug only, enforced by test** |

`small30` is excluded from every reported claim. Disabling pheromone costs **+15.63 points at n=200 (p < 0.001)** and **nothing at n=30 (p = 0.91)** — a 30-node graph of mean degree 18 puts the target a hop or two from anywhere, so the colony's memory is redundant and any conclusion drawn there is vacuous. `test_pheromone_contributes_on_the_science_tier` keeps this honest.

### 4.3 The disruption model

Six event kinds, applied in **spatially coherent clusters**:

| Kind | Effect |
|---|---|
| `closure` | weight → effectively infinite |
| `traffic_up` | weight × `traffic_factor` (2.0) |
| `traffic_down` | weight ÷ `traffic_factor`, floored at free-flow |
| `reopen` | reactivates an inactive **base** edge |
| `delete` | deactivates an edge in the CSR mask |
| `add` | activates a **pool** edge at free-flow weight |

Three design decisions that must survive any refactor:

1. **Clustering (default 25 edges).** A single uniformly-drawn edge is almost always irrelevant to any route — measured on a 30-node graph, single-edge events left the optimal path untouched in 4 of 6 trials. Clusters keep events rare enough for quiet stretches while making each one consequential.
2. **The rate is absolute, not proportional to |E|.** `count ~ Poisson(events_per_step)`. A proportional rate produced ~18 events/step at 1200 edges, so the graph never settled and recovery was unmeasurable. *(This change is why `cross_evaluate.py` no longer runs — see F3.)*
3. **Connectivity guard.** Events that would disconnect source from target are rejected. Transient unreachability is still possible and is measured.

**Scenarios:**

| Name | `events_per_step` | P(quiet step) |
|---|---|---|
| `static` | 0.0 | 100% |
| `low` | 0.1 | 90% |
| `moderate` | 0.3 | 74% |
| `high` | 0.8 | 45% |

### 4.4 The timeline — and the temporal contract

`build_schedule()` materialises the entire event sequence **before any optimizer exists**. `GraphTimeline.state_at(t)` is pure and cached. Every arm provably observes identical bytes.

**The temporal contract, stated explicitly because F1 violated it:**

> `schedule[k]` is the transition from state *k* to state *k+1*.
> Therefore the events that **produced** state *t* are `schedule[t-1]`.
> `events_at(t)` must return `schedule[t-1]`.
> **No component may reference the schedule or any state at t′ > t.**

This is enforced by an invariant test (§10.3), not by care. F1 exists because it was left to care.

---

## 5. The optimizers

All four implement one `runtime_checkable` Protocol:

```python
class Optimizer(Protocol):
    PARAM_SPEC: ClassVar[Mapping[str, ParamSpec]]
    name: str
    def rebind(self, view: GraphView) -> None: ...
    def spend(self, meter: EvaluationMeter) -> None: ...
    def best(self) -> Solution | None: ...
    def params(self) -> dict[str, float]: ...
    def apply(self, values: Mapping[str, float]) -> None: ...
    def probe(self) -> dict[str, float]: ...
    def reset_learned_state(self, strength: float) -> None: ...
```

Every tunable is declared in `PARAM_SPEC` with a default, bounds, integer flag and a doc string. `bind()` **raises** on an unknown name — a typo cannot be silently absorbed. `test_every_parameter_changes_behaviour` drives each parameter to both bounds and requires the trajectories to differ, so a parameter cannot be introduced inert.

### 5.1 A\* — the oracle

Not a competitor. Its cost each timestep defines what "perfect" means.

`f(n) = g(n) + h(n)`, with `h = 0` for non-spatial models and `distance(n, target) × weight_scale` otherwise. Admissible because edge weight ≥ free-flow = `distance × weight_scale`.

- `PARAM_SPEC = {}` — parameter-free
- `rebind()` **discards** the previous solution. A\* holds no transferable state and pays a full re-search on every change — exactly the cost this project exists to expose
- `spend()` ignores the meter; `metered=False`
- `probe()` → `{"expansions"}`, the cost-of-recomputation metric

### 5.2 ACO — MAX–MIN Ant System

`P(i→j) ∝ τ^α × η^β`, where `η = 1 / (w + goal_weight × h)`.

One iteration: `n_ants` ants construct paths by roulette-wheel selection → evaporate `τ ← τ(1−ρ)` on active slots → the best ant deposits `1/cost` symmetrically via `rev` → clamp to `τ_max = 1/(ρ·C_best)`, `τ_min = τ_max/(2n)`.

| Parameter | Default | Range | Int | Meaning |
|---|---|---|---|---|
| `alpha` | 1.0 | [0, 5] | | trail exponent — weight on accumulated memory |
| `beta` | 2.0 | [0, 8] | | visibility exponent — weight on edge cost |
| `rho` | 0.10 | [0.01, 0.90] | | evaporation rate per iteration |
| `n_ants` | 20 | [4, 100] | ✓ | paths built per iteration |
| `goal_weight` | 1.0 | [0, 5] | | pull of geometric distance-to-target |

`probe()` → `lambda_branch`, `tau_ratio`, `iterations`.

**Invariants that must survive refactoring:**

- **Trail limits are load-bearing.** Without them the strongest/weakest ratio reached 9×10⁸ by iteration 80 and every ant walked an identical path. MAX–MIN caps the ratio at `2n`, which is what keeps any evaporation dial connected to anything.
- **Goal direction is mandatory at scale.** Without `goal_weight` a colony on 200 nodes settled ~90% above optimum.
- **Trails survive disruptions deliberately.** The stale trail on a road that just closed *is* the phenomenon under study. Trails on slots that go inactive are zeroed so a later reopen cannot resurrect a stale preference.
- **An iteration is abandoned part-way when the budget runs out.** Finishing it would overrun by up to `n_ants` — an overrun that grows precisely when a controller enlarges the colony.

### 5.3 PSO — priority-vector encoding

Each particle holds one priority per **node** in [0, 1]. A path is built greedily: from the current node take the unvisited neighbour maximising `priority[v] × η(u, v)`. On a dead end, perturb and retry up to `repair_attempts` times, each charged to the meter.

`v ← w·v + c₁r₁(p_best − x) + c₂r₂(g_best − x)`, then `x ← clamp(x + v, 0, 1)`.

| Parameter | Default | Range | Int | Meaning |
|---|---|---|---|---|
| `inertia` | 0.7 | [0, 1] | | velocity carry-over |
| `cognitive` | 1.5 | [0, 4] | | pull toward the particle's own best |
| `social` | 1.5 | [0, 4] | | pull toward the swarm's best |
| `n_particles` | 20 | [4, 100] | ✓ | swarm size |
| `goal_weight` | 1.0 | [0, 5] | | pull of geometric distance in visibility |
| `repair_attempts` | 3 | [0, 10] | ✓ | perturbations tried on a dead end |

`probe()` → `diversity`, `iterations`.

**Invariants:**

- **On `rebind()`: positions stay, costs are invalidated, the global best position is kept.** Priorities rank nodes and nodes do not change. Costs were priced against a graph that no longer exists. Discarding the global best *position* as well was measured to cost ~90 points of excess.
- **The rejected encoding stays rejected.** Biasing edge weights and running Dijkstra on `w × (1 + b[v])` puts the optimum at a distinguished point (`b = 0`) and turns the method into Dijkstra in a costume.
- Resize: shrink keeps the fittest, grow appends random particles with `own_cost = inf`.

---

## 6. The Hybrid

One `ACO` and one `PSO` instance with **independent random sub-streams derived by name** — `stream(root, "hybrid", "aco")` and `stream(root, "hybrid", "pso")` — so retuning one cannot perturb the other's draws, and adding a third component later would shift neither.

### 6.1 The budget split

```
budget    = meter.remaining
aco_share = max(1, round(budget × aco_fraction))
pso_share = budget − aco_share
```

Each component receives its own sub-meter; the parent is charged what they actually spent. The split cannot smuggle in extra work.

### 6.2 The exchange

After each spend, bidirectionally:

1. **Colony → Swarm** — the colony's best path raises the swarm's priorities along those nodes by `EXCHANGE_GAIN` (0.25), clipped to [0, 1]
2. **Swarm → Colony** — the swarm's best path deposits `1/cost` trail

Both are deliberately nudges. Stronger coupling collapses the two searches into one and forfeits the diversity that motivates running them together. **The exchange must be provably non-decorative** — see §16, Layer 2.

### 6.3 Parameters

All five ACO parameters prefixed `aco_`, all six PSO parameters prefixed `pso_`, plus:

| Parameter | Default | Range | Meaning |
|---|---|---|---|
| `aco_fraction` | 0.5 | [0.05, 0.95] | share of the budget given to the colony |

> The default is **0.5**; the best vector found by tuning is **0.82**. Every Hybrid result produced so far used the untuned 0.5. Re-tuning precedes every headline experiment (§13).

---

## 7. The control layer — redesigned

### 7.1 Why it is being rebuilt

The existing control layer is a **parameter-adaptation machine**: a scalar signal feeds an `IncrementalController` that nudges named parameter `targets` by ±σ, with direction supplied by a hard-coded sign table. That architecture served Claim 2, which is now settled.

Claim 3 is a **resource-allocation** question, and `aco_fraction` is currently bolted into that machine as though it were just another parameter. It is not. Three concrete costs of the mismatch:

1. **The ±σ rule can only express a monotonic response.** If the good allocation policy is non-monotonic or state-dependent, the rule *structurally cannot represent it* — and a null result would then say nothing about allocation, only about that rule.
2. **A scalar signal throws away the state a policy needs.** Colony stagnation, swarm convergence and time-since-disruption are all relevant to "should I buy more ACO right now"; a single float cannot carry them.
3. **Saturation is checked by hand.** The RUNBOOK asks the operator to verify the split moved and did not pin to a bound. A check that lives in a document is a check that eventually is not run.

### 7.2 The design

**Observation — structured, not scalar.**

```python
@dataclass(frozen=True)
class AllocationObservation:
    t: int
    recency: float                 # 1.0 on a disruption step, decays by `decay` each quiet step
    steps_since_disruption: int
    events_this_step: int
    current_fraction: float
    budget: int
    aco_lambda_branch: float       # colony stagnation
    pso_diversity: float           # swarm convergence
    own_cost: float | None         # cost of THIS arm's current best — no oracle involved
    own_cost_delta: float | None   # change in own_cost since the previous step
    path_invalidated: bool         # did this arm's incumbent path break this step?
```

**Two hard constraints on this object.**

**Every field is derived from state at t′ ≤ t.** Constructing it is the **only** channel by which a policy learns anything about the world (§10.3, I2).

**No field may be derived from the oracle.** An earlier draft carried `excess_last_step`; that is `cost / optimum − 1`, so it is computed from the oracle's answer and violates I1. A policy that knows its own excess knows how far from optimal it currently is — information no deployed router has — and a rule like "buy PSO when excess is high" would be a policy trained on oracle knowledge. It is removed.

The three replacement fields are **self-knowledge**: the raw cost of the arm's own incumbent, how that changed, and whether the incumbent path broke. A real routing system has all three and none of them requires knowing the optimum. `own_cost_delta` is confounded by the graph itself becoming cheaper or dearer — that is accepted, because a deployed system faces exactly the same confound.

**Policy — returns a target, not a delta.**

```python
class AllocationPolicy(Protocol):
    name: str
    def propose(self, obs: AllocationObservation) -> float: ...   # target aco_fraction
    def reset(self) -> None: ...
```

Returning a target rather than a ±σ delta is what makes non-monotonic and state-dependent policies expressible at all.

**Registered policies:**

| Policy | Behaviour | Role |
|---|---|---|
| `FrozenAllocation` | returns `obs.current_fraction` unchanged | the ablation twin — a policy object, never an absent one, so both arms run identical code paths |
| `IncrementalAllocation` | the existing ±σ pressure-vs-EMA-baseline rule, preserved exactly | keeps continuity with prior results |
| `ScheduledAllocation` | an open-loop timetable; ignores everything but `t` | **the honest control for feedback itself** — if a schedule matches a sensing policy, what helped was *varying*, not *sensing* |
| `LearnedAllocation` | contextual bandit or tabular Q-learner over discretised observations; trained on `tune_seeds`, evaluated on `eval_seeds` | **Phase 4, only with mentor sign-off** (D7, O2). Not PPO |

**Governor — enforcement lives here, not in policies.**

The governor wraps every policy and is the only thing that touches the optimizer:

- clamps the proposal to `[0.05, 0.95]`
- rate-limits `|Δ| ≤ sigma_max` per step
- records **proposed** and **applied** separately, so clipping is visible in the data rather than silent
- accumulates **saturation statistics** — the fraction of steps sitting at a bound, and whether the value moved at all

Saturation becomes a recorded quantity and an automated check, not a manual instruction. A reported allocation run must satisfy: the fraction moved (more than one distinct value) **and** spent under 20% of steps at a bound. A run failing either is not reportable.

### 7.3 What `recency` is, precisely

```
recency(t) = 1.0                       if a disruption landed at t
           = recency(t-1) × decay      otherwise   (decay = 0.7)
```

Derived from `events_at(t)` = `schedule[t-1]` (§4.4). **F1 broke exactly this**: it read `schedule[t]`, so the signal fired one step early and had already decayed to 0.7 by the step where pheromone was actually stale.

**Why recency and not volatility.** The cross-evaluation showed optimal parameters do not vary with the steady-state disruption *rate*. But recency describes a *transient* — a disruption just landed, so the trail is maximally untrustworthy right now. That is a different quantity, and the sweep said nothing about it.

---

## 8. The evidence set

The parameter-adaptation machinery moves to `src/dynaswarm/evidence/` (D6). It is:

- **out of the live control path** — no live arm depends on it
- **fully runnable and tested** — Claim 2's measurements must be reproducible on demand, and every number is being regenerated
- **clearly namespaced** so nobody mistakes findings-reproduction code for the system's controller

Contents: the `edge_ratio`, `volatility` and `lambda_branch` signals; `IncrementalController` and `PrescheduledController` as parameter controllers; `EXPLORE_SIGN`; and the `aco_fixed` / `aco_adaptive` arm pair.

**Required change (F2) — fixed in place at Phase 0.5, not at the move.** `IncrementalController.propose` must **raise** on an unknown target, not silently ignore it. The fix lands in `control/controllers.py` during defect triage; the Phase 3 demotion to `evidence/` simply carries it along. Do not defer it to the move. Today a hybrid arm left on the default `targets=["rho"]` adapts nothing — hybrid parameters are named `aco_rho` — while still logging `controller_kind=incremental` beside moving signal values. `bind()` in `optimizers/spec.py` already raises on the same class of mistake; the controller must match.

**Note:** `lambda_branch` is demoted as a *control signal* but remains available as an **observation field** for allocation policies (§7.2). Colony stagnation is legitimately relevant to how much budget the colony deserves; it was simply never a volatility proxy.

---

## 9. The arms, and the display-name map

**Code identifiers are frozen (D23a).** They key `ARM_BUILDERS`, appear in Hydra configs, are asserted in ~8 tests, and are written into the `arm` column of every `steps.parquet` on disk. Renaming them would silently break the ability to load any recorded run.

**The naming convention applies to the report, deck, dashboard labels and prose only**, through a single display-name map.

| Code id | Display name | Family | Signal | Control | Metered | Role |
|---|---|---|---|---|---|---|
| `astar` | **A\*** | `astar` | — | — | no | reference optimum |
| `aco` | **ACO standalone** | `aco` | — | — | yes | component baseline |
| `pso` | **PSO standalone** | `pso` | — | — | yes | component baseline |
| `hybrid` | **Hybrid (baseline)** | `hybrid` | — | — | yes | the Hybrid with no control machinery at all |
| `hybrid_fixed` | **Fixed / Static Hybrid** | `hybrid_controlled` | recency | `FrozenAllocation` | yes | **the ablation twin** |
| `hybrid_adaptive` | **New Recency-Based Adaptive Hybrid** | `hybrid_controlled` | recency | `IncrementalAllocation` (or `Learned`) | yes | **the thesis** |
| `aco_fixed` | **ACO, frozen ρ** *(evidence set)* | `aco_controlled` | volatility | null | yes | reproduces Claim 2 |
| `aco_adaptive` | **ACO, adaptive ρ** *(evidence set)* | `aco_controlled` | volatility | incremental | yes | reproduces Claim 2 |

### 9.1 D23b resolved

**"Fixed / Static Hybrid" means `hybrid_fixed`, never `hybrid`.**

They are different arms and are not interchangeable:

- `hybrid` has **no signal and no controller**. Pairing it against `hybrid_adaptive` would compare two arms differing in *two* ways — whether control machinery exists at all, and whether the controller may move — and they do not share a family, so they draw different random numbers.
- `hybrid_fixed` shares the `hybrid_controlled` family with `hybrid_adaptive`. Fed identical bits from identical starting parameters, **the pair can diverge for exactly one reason**: whether the policy was permitted to move the split. That is the ablation.

`hybrid` remains useful as a plain baseline for Claim 1 (Hybrid vs its components). It is never the control arm for Claim 3.

### 9.2 Why `family` keys the random stream

Streams are content-addressed by `family`, not by `name`. Two arms differing only in whether a controller is active therefore draw *identical* randomness. Keying on `name` would hand them different bits and confound the comparison. `test_adding_an_arm_does_not_disturb_the_others` guards this.

---

## 10. The harness and its invariants

### 10.1 The trial loop

```
seed = eval_pool[trial % len(pool)]
build(cfg.graph, stream(seed, "graph"))              → view, source, target
build_schedule(view, cfg.scenario, stream(seed, "events"))   → frozen schedule
GraphTimeline(view, schedule)
build_arms(...)                                      → arms, each with its own stream

for t in range(timesteps):
    state       = timeline.state_at(t)               # identical object for all arms
    before_hash = state.state_hash()
    optimum     = shortest_path(state, source, target)

    for arm in arms:
        arm.optimizer.rebind(state)
        assert state.state_hash() == before_hash
        meter = EvaluationMeter(budget)
        arm.optimizer.spend(meter)
        solution = arm.optimizer.best()
        assert solution.cost >= optimum - tol
        if arm.governor:
            obs = build_observation(timeline, t, arm)
            arm.governor.step(obs, arm.optimizer)
        record StepRow(...)
```

### 10.2 The five fairness guarantees

| Guarantee | Mechanism |
|---|---|
| Every arm sees the identical world | schedule frozen before any optimizer exists; Blake2b hash asserted per arm per step |
| Equal budget means equal **work** | budget denominated in candidate path constructions, metered externally, never self-reported |
| An arm's randomness depends only on itself | streams content-addressed by `family` |
| A signal spans the range it is thresholded against | dynamic range asserted per scenario |
| Every tunable demonstrably changes behaviour | `PARAM_SPEC` binding is total; each parameter driven to both bounds |

### 10.3 Layer 1 invariants — three to add

These are written **before** F1 is fixed, so each is watched failing first (§17, Phase 0.5).

**I1 — No oracle leakage.** No optimizer, policy or observation may receive `optimum`, **or any quantity computed from it**. The oracle's answer exists only in the harness and the recorded row.

"Computed from it" is meant literally and includes derived ratios. The canonical example is **`excess`**, which is `cost / optimum − 1` and is therefore **forbidden** as an input to any optimizer or allocation policy, however convenient. Self-knowledge is permitted — an arm's own cost, how it changed, whether its path broke — because a deployed system has those without an oracle. The test walks the objects reachable from every optimizer and policy and asserts none holds an oracle-derived value.

**I2 — No access to future state.** No component may reference the schedule or any graph state at t′ > t. Implemented by instrumenting `GraphTimeline` to record the maximum index each caller touches during a trial, and asserting it never exceeds the current timestep.

> This is the invariant that catches **F1**. Written first, it fails on the current code — which is the point.

**I3 — No cross-arm references.** No arm may hold a reference into another arm's internals. The Hybrid's own ACO↔PSO exchange is asserted as **the only sanctioned channel** of its kind.

---

## 11. Evaluation and statistics

### 11.1 Primary metric

```
excess(t) = best_cost(t) / optimum(t) − 1
```

Raw path cost is not comparable across timesteps once the graph changes — a run can appear to improve because the graph got cheaper. A\* recomputed each timestep is the denominator and scores exactly 0.0 by construction.

### 11.2 Recovery metrics

- **`damage`** = `max(excess[t : t+damage_window]) − baseline`, baseline = mean excess over `calm_before` quiet steps before the event. Negative damage is possible — an event can open a shorter route.
- **`recovery_time`** = steps until quality returns within `RECOVERY_BAND` (0.10) of the baseline.
- **`settled_excess`** = mean excess over quiet-only steps. The steady-state number.

Scoring rules: disruptions with fewer than `MIN_HORIZON` (8) steps remaining are **dropped, not scored as unrecovered** — an arm hit on the final timestep has no chance to recover, and counting that as failure is right-censoring bias. A clean baseline requires `calm_before` consecutive quiet steps.

**Recovery analysis is a first-class experiment, not an optional extra.** Claim 1's mechanism predicts the Hybrid's advantage concentrates just after disruptions. If instead it wins uniformly, the stated rationale is wrong even though the result stands — and the report must say so.

### 11.3 Statistical protocol (D21 — unchanged)

1. **Pair on trials, never timesteps.** The 60 steps within one trial share a graph and an event sequence. Treating them as independent inflates the sample 60× and finds significance almost anywhere. Each trial reduces to a scalar first.
2. **Holm correction across the whole comparison family.** Reports use `p_holm`, never `p_value`.
3. **Effect size beside every p-value.** Cliff's delta: `<0.147` negligible, `<0.33` small, `<0.474` medium, else large.
4. **Report confidence intervals, not point estimates alone.**
5. **Plot per-trial scatter before believing any mean.** In this project trial-to-trial spread has repeatedly exceeded the gap between arms.

### 11.4 Statistical power

Trial variance runs 5–12%. **All reported conditions use ≥ 100 trials** (D9). Any claim about an effect smaller than the residual detectable size is stated as a bound, not a finding.

---

## 12. Run provenance

Every run records a **`run_class`** in `manifest.json` **and** as a column in `steps.parquet`:

| Class | Meaning | Reportable |
|---|---|---|
| `manifest` | produced by a named entry in the experiment manifest | **yes** |
| `exploratory` | ad-hoc — a smoke run, a dashboard session, a sanity check | **never** |
| `inversion` | produced by a deliberately-broken code path (§14) | **never**, and never mixed |

`load_steps()` returns **`manifest` rows only** unless another class is requested explicitly. A test asserts that the default configuration can never produce anything other than `exploratory` or `manifest`.

This is a data-level guarantee, not a naming convention.

### 12.1 Migration rule for runs that predate the column

Every `steps.parquet` already on disk was written before `run_class` existed — including the three exploratory runs under `outputs/2026-08-30/`, which §12 retains. Since `load_steps()` concatenates across directories, one old file would otherwise poison a mixed load.

> **A missing `run_class` is read as `exploratory`.**

No migration, no schema version, no rewriting of existing files. It is the safe default — `exploratory` is never reportable, so an old run can never silently become evidence — and it is the correct label for every run that currently exists. `load_steps()` must fill the column when absent rather than raising, and must handle a mixed load where some directories have it and some do not.

---

## 13. The experiment manifest

A single declarative file under `experiments/` names every experiment that produces a reported number:

```yaml
- id: E2_hybrid_vs_components
  claim: 1
  graph: medium200
  scenarios: [static, low, moderate, high]
  arms: [astar, aco, pso, hybrid]
  params_file: best_fixed/hybrid_medium200.json
  trials: 100
  budget: 300
  feeds: [table_main_comparison, fig_arm_comparison]
```

Each entry carries: `id` · which `claim` it serves · graph tier · scenarios · arms · parameter file · trials · budget · which table or figure it feeds · expected runtime.

Three properties this buys:

1. **Regenerating everything is one command.**
2. **Every number in the report traces to a named run**, and every named run traces to a config.
3. **The experiment list cannot quietly become a wishlist** — an entry either has a completed run or is visibly outstanding.

### 13.1 Ordering

Tuning comes first and is a hard prerequisite. The tuned vector is an *input* to every headline experiment, and `aco_fraction = 0.5` is not the tuned value.

```
T1  tune ACO      on medium200        → best_fixed/aco_medium200.json
T2  tune PSO      on medium200        → best_fixed/pso_medium200.json
T3  tune Hybrid   on medium200        → best_fixed/hybrid_medium200.json   (12 parameters incl. aco_fraction)
T4  repeat T1–T3 on large1000         (parameters are not transferable across tiers)
────────────────────────────────────────────────────────────────────────
E1  sanity                A* excess exactly 0.0 in every row
E2  Claim 1               hybrid vs aco vs pso, 4 scenarios, tuned
E3  Claim 1 mechanism     recovery analysis on E2's output
E4  Claim 3               hybrid_fixed vs hybrid_adaptive, 4 scenarios, TUNED  ← the thesis
E5  Claim 3 control       ScheduledAllocation vs IncrementalAllocation
E6  Claim 2 (evidence)    aco_fixed vs aco_adaptive against a tuned baseline
E7  Claim 2 diagnosis     cross-evaluation, re-derived under the current model (F3)
E8  generality            E2 and E4 repeated on large1000
E9  budget axis           E4 at budget 2000
E10 testbed validity      pheromone ablation, medium200 vs small30
E11 signal characterisation  dynamic range of all four signals per tier
E12 inversions            four deliberately-broken variants (§14)
```

**E4 is the project's headline experiment.** It has never been run correctly: once, at 30 trials, on two scenarios, with untuned parameters, on a signal misaligned by F1.

---

## 14. Inversion ablations

Four deliberately-broken variants, each showing that omitting one harness commitment inverts the answer (D11):

| Inversion | Commitment broken | Expected wrong answer |
|---|---|---|
| `equal_iterations` | budget in work, not iterations | the arm with the larger population appears to win |
| `pair_on_timesteps` | pair on trials | p-values collapse; almost anything looks significant |
| `untuned_opponent` | compare against a *tuned* fixed baseline | adaptation appears to help substantially |
| `wrong_tier` | the mechanism must do measurable work on the tier in use | the pheromone null becomes vacuous |

This converts the methodology from a claim into a demonstrated result, and it is entirely original.

### 14.1 Safety design (D19) — mandatory

Deliberately-wrong code paths are the most dangerous thing in this repository.

1. **Enabled only through a dedicated Hydra config group** — `integrity=equal_iterations` and so on. Never a boolean deep in a config, never a default, never composable by accident.
2. **Any run with an inversion active is stamped `run_class: inversion`**, in `manifest.json` and as a `steps.parquet` column.
3. **`load_steps()` refuses inversion rows** unless asked for by name.
4. **A test asserts the default configuration can never produce `run_class: inversion`.**
5. **Every figure derived from an inversion is watermarked** in its title as a deliberately-broken control.

A broken path leaking into a real result would be worse than not building these at all.

---

## 15. The dashboard

### 15.1 Purpose

One tool, two jobs: **the instrument Rudra uses to understand and verify the system**, and **the demonstration shown to the professor**. It is explicitly *not* the experiment engine — batch sweeps stay with the CLI.

### 15.2 Constraints (D14–D17)

- Lives at **`dashboard/` in the repo root**, outside `src/`. Imports `dynaswarm`; `dynaswarm` never imports it.
- **Drives runs through `run_trial()`** — the same entry point the CLI uses. It configures and calls; it never steps a loop itself.
- A dashboard-driven run **writes a normal run directory**, indistinguishable from a CLI run, stamped `run_class: exploratory`.
- It can **also load and replay** an existing run directory.
- **Hard constraint: configure → run → observe.** Never run → tweak → continue. No dashboard-specific parameter may enter a run; nothing may mutate a run in flight.
- Statement cap **1000**.

### 15.3 Stage 1 — Build the world

Choose model, node count, density, seed. Generate.

Renders with **real coordinates**, source green, target amber, and draws **the true optimal path at t = 0** — so the first thing visible is that a start-to-goal path exists and what it looks like. Panel shows |V|, |E|, mean degree, optimal cost. Re-rolling the seed browses variants.

> Directly addresses the original complaint. The default `small30` is non-spatial, so the old viewer fell back to a random scatter and no path could look like a path. Spatial models are the default here.

### 15.4 Stage 2 — Design the disruption

Choose a scenario preset or set `events_per_step`, `cluster_size`, `timesteps` and the six event probabilities. Build the timeline.

A **timeline strip** shows every timestep with the count and kind of events that landed, colour-coded. **Scrubbing it** moves the graph to that timestep with changed edges highlighted by type — closure red, traffic-up orange, traffic-down blue, deleted grey dashed, added green, reopened teal.

### 15.5 Stage 3 — Race the arms

Tick arms, set budget, run. Executes one real trial through `run_trial()`.

Playback shows **a grid of panes, one per arm, same graph, same timestep, synchronised.** Each pane draws that arm's current best path; the A\* pane draws the true optimum. Along the bottom, a live excess-over-time chart with one line per arm and disruption markers.

This is where correctness becomes visible: a path failing to reach the goal shows up instantly, in whichever arm.

### 15.6 Stage 4 — Inspect

- Click an edge → weight history, per-arm pheromone level, event history
- Click a node → PSO priority statistics across particles
- Per-arm panel → current excess, evaluations spent, live parameter vector, probe telemetry
- **The allocation bar** → `aco_fraction` shown sliding toward PSO as a disruption lands and drifting back during calm, with proposed-vs-applied and saturation state visible

That last widget is the project's novelty made watchable rather than described.

### 15.7 API shape

```
POST /api/graph            build a graph          → graph id, geometry, endpoints, optimum
POST /api/timeline         build a schedule       → per-step event summary
GET  /api/state/{t}        graph state at t       → weights, active mask, changed slots
POST /api/run              execute one trial      → run id  (writes a run directory)
GET  /api/run/{id}/steps   recorded step rows
GET  /api/run/{id}/probe   telemetry per arm per step
GET  /api/runs             list existing run directories for replay
```

Every endpoint is a thin wrapper over an existing `dynaswarm` entry point. If one needs something the core does not expose, **the core exposes it** — the dashboard never computes it.

---

## 16. Testing strategy

Three layers, cheapest first. This is how correctness is established without reading every line.

**Layer 1 — invariants that make cheating impossible.** *(Phase 0.5)*
Existing: cost never below optimum · state hash unchanged · identical state to every arm · budget spent exactly · adding an arm leaves others bit-identical · every parameter changes behaviour · signals span their range · the tier can show the effect claimed.
New: **I1 no oracle leakage · I2 no access to future state · I3 no cross-arm references** (§10.3).

**Layer 2 — mechanism-alive probes.** *(Phase 2)*
A mechanism that is implemented but inert is the failure this project has already suffered.

- Does pheromone concentration actually increase over iterations?
- Does PSO diversity actually shrink?
- **Does disabling the Hybrid's exchange change results?** If not, the exchange is decorative and must be reported as such.
- Does `aco_fraction` actually move under an allocation policy, without pinning to a bound?
- Does every registered policy produce a trajectory distinguishable from `FrozenAllocation`?

**Layer 3 — watch it.** *(Phase 2)*
Each algorithm run alone on a small geometric graph in the dashboard, walked through against the code and against theory.

**Standing rules:** no existing test may be deleted, weakened or skipped. If a test appears wrong, that is reported, never edited. The full suite and `ruff` pass before any segment closes.

---

## 17. Phase plan

| Phase | Work | Gate |
|---|---|---|
| **0 — Ground truth** | Fix stale `README.md` and `RUNBOOK.md` (five slow tests, not four) · caveat or excise legacy and superseded figures in `DOCUMENTATION.md` §19.1, §19.2, §20 · establish the `run_class` convention · clean baseline run on `medium200` | Suite green; no unverifiable number presented as evidence |
| **0.5 — Defect triage** | **Write I1–I3 first and watch I2 fail** → fix **F1** → watch it pass · fix **F2** (raise on unknown target) · repair **F3**, re-deriving under the current disruption model | All three invariants pass; the log carries evidence the guard bites |
| **1 — See it** | `dashboard/` scaffold, then Stages 1 → 2 → 3 → 4, one segment each | A start-to-goal path is visible; disruptions are legible; arms race side by side |
| **2 — Trust it** | Layer 2 probes, then the Layer 3 guided walkthrough | Every mechanism proven live or reported inert |
| **3 — Restructure** | `allocation/` package — observation, policies, governor · `evidence/` demotion · PSO inertia resolved (implemented or formally dropped) · learned-policy interface | Allocation is first-class; saturation checks automated |
| **4 — Run the science** | The manifest in order: T1–T4, then E1–E12 | Every reported number traces to a manifest run at ≥100 trials |
| **5 — Deliverables** | Report · deck · demo | |

**Phase 0.5 precedes the dashboard deliberately.** F1 misaligns the signal the entire thesis depends on; nothing built on top of it is trustworthy until it is fixed and guarded.

### 17.1 PSO inertia

The synopsis promised adaptive tuning of ACO's ρ **and PSO's inertia**. `EXPLORE_SIGN` contains seven entries and none is `inertia`, so it was never delivered. Phase 3 resolves this one of two ways, and the report says which:

- **implement it** in the evidence set (higher inertia = more roaming = explore, so sign `+1`), or
- **formally drop it**, stating that under a fixed evaluation budget its exploration direction is ambiguous — the same reasoning already documented for `n_ants` and `n_particles`.

Either is defensible. Silence is not.

---

## 18. Out of scope

| Item | Status |
|---|---|
| Real GPS / OpenStreetMap / benchmark road networks | **Parked** (D12). The graph loader stays general enough to accept one later. Future work |
| Deep learning, neural networks, PPO/SAC | **Excluded** by the approved synopsis. A tabular or bandit policy is not a neural network but is still a scope extension (O2) |
| Mobile deployment, public hosting | **Excluded.** The dashboard is a local tool |
| Multi-objective routing | Future work |
| Distributed / MPI execution | Future work |
| v1 (`DPO_Minor_project-main`) | **Outside this repository and outside vClaude's reach.** Retirement is Rudra's task. Never import a number from it |

### Open items

| # | Item | Needs |
|---|---|---|
| **O1** | Web dashboard — synopsis lists web deployment as out of scope | Mentor sign-off |
| **O2** | Learned allocation policy | Mentor sign-off; decision point end of Phase 3 |
| **O3** | Walkthrough for the mentor: why `change_rate` was abandoned, and that Expected Outcome #3 was disproved by the team's own measurements | Rudra to present |
| **O5** | Three teammates hold synopsis-assigned roles and will each be vivaed on their own section | Rudra's call |

---

*Version 1.1 — 30 Aug 2026. Supersedes any conflicting statement in `AGENT_PROTOCOL.md` or `decisionLedger.md` regarding what the system should be.*

*v1.1 changes, all from vClaude's review: removed `excess_last_step` from `AllocationObservation` (it violated I1) and replaced it with three oracle-free self-knowledge fields; tightened I1 to name derived quantities explicitly; corrected §4.1's account of trail survival across deactivation, which had inherited a wrong docstring; recorded that the science statement cap rises at Phase 3 rather than being exempted; added §12.1, the `run_class` migration rule; corrected the §13 manifest example from E3 to E2; pinned F2's fix to Phase 0.5 in place rather than to the Phase 3 move.*
