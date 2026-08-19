# Part 1 — Project Overview, Architecture & Environment

## 1. Project Overview

**Dynaswarm** (also referred to as *DPO — Dynamic Path Optimisation*) is a research codebase in
computational intelligence studying a single question:

> When searching for the shortest path through a network that keeps changing underneath you, does it
> help to automatically re-tune the search algorithm's settings in response to how fast the
> environment is changing?

The project implements four path-finding algorithms (A\*, ACO, PSO, Hybrid ACO-PSO), a simulated
dynamically-disrupted road network, an adaptive feedback-loop controller that retunes algorithm
parameters in real time, and a statistically rigorous experimental harness to measure whether the
controller actually helps.

**Scale (Dynaswarm v2 — the current codebase under `dynaswarm/`):**
- ~10 Python modules, ~7 sub-packages
- 271 pytest tests, run in ~60 seconds
- Hydra-based structured configuration
- Results written to Apache Parquet for post-hoc analysis

**Scale (DPO_Minor_project — the legacy codebase):**
- 63 Python files, ~13 300 lines of code
- 116 passing tests
- Three user interfaces: CLI, Tkinter GUI, FastAPI web dashboard

---

## 2. The Problem

### 2.1 Dynamic Shortest Path Problem

Real networks (road networks, telecoms, supply chains) change continuously:
- Roads close due to accidents → edge cost → ∞
- Traffic builds → edge cost multiplied
- Links are added or removed

Classical algorithms handle this poorly:

| Algorithm | Weakness under change |
|---|---|
| **A\* / Dijkstra** | Stateless. Every change forces a full re-search. Exact but expensive at scale. |
| **ACO** | Pheromone trails go *stale*. The colony keeps being pulled toward closed roads until evaporation slowly washes the memory out. |
| **PSO** | The swarm converges on a region. Once converged, it lacks the diversity to escape when the optimum moves. |

### 2.2 The Core Tension

Every swarm algorithm balances:
- **Exploitation** — refine what looks good (fast convergence, blind to change)
- **Exploration** — keep sampling elsewhere (adapts to change, wastes effort when stable)

The right balance depends on environmental volatility. A fixed parameter setting must compromise.

**Project hypothesis:** a controller that measures volatility in real-time and shifts the
exploration/exploitation balance accordingly will beat any fixed setting.

---

## 3. System Architecture

### 3.1 Layered Design

```
┌────────────────────────────────────────────────────────────────┐
│  INTERFACES         CLI (dynaswarm.cli)                        │
│                     Web Dashboard (FastAPI + JS) [legacy]      │
│                     Tkinter GUI [legacy]                        │
├────────────────────────────────────────────────────────────────┤
│  ORCHESTRATION      Hydra + dynaswarm.cli                      │
│                     ExperimentManager [legacy]                  │
├────────────────────────────────────────────────────────────────┤
│  TUNING             dynaswarm.tuning.best_fixed                │
│                     (Optuna TPE, seed-separated)               │
├────────────────────────────────────────────────────────────────┤
│  HARNESS            dynaswarm.harness.trial (run_trial)        │
│                     dynaswarm.harness.arm   (build_arms)       │
│                     dynaswarm.harness.runner                   │
├────────────────────────────────────────────────────────────────┤
│  CONTROL            dynaswarm.control.signals                  │
│                     dynaswarm.control.controllers              │
├────────────────────────────────────────────────────────────────┤
│  OPTIMIZERS         dynaswarm.optimizers.protocol (Optimizer)  │
│                     ├─ astar.AStar                             │
│                     ├─ aco.ACO                                 │
│                     ├─ pso.PSO                                 │
│                     └─ hybrid.Hybrid                           │
├────────────────────────────────────────────────────────────────┤
│  ENVIRONMENT        dynaswarm.core.generate    (graph builder) │
│                     dynaswarm.core.events      (event kinds)   │
│                     dynaswarm.core.timeline    (schedule)      │
│                     dynaswarm.core.graphview   (CSR state)     │
│                     dynaswarm.core.oracle      (Dijkstra/A*)   │
│                     dynaswarm.core.meter       (budget)        │
│                     dynaswarm.core.rng         (stream)        │
├────────────────────────────────────────────────────────────────┤
│  ANALYSIS &         dynaswarm.analysis.stats   (Wilcoxon/Holm) │
│  REPORTING          dynaswarm.analysis.recovery               │
│                     dynaswarm.analysis.plots                   │
│                     dynaswarm.analysis.load                    │
├────────────────────────────────────────────────────────────────┤
│  VISUALIZATION      dynaswarm.viz.replay       (Pygame)        │
├────────────────────────────────────────────────────────────────┤
│  CONFIGURATION      dynaswarm.config           (Hydra/dataclass)│
└────────────────────────────────────────────────────────────────┘
```

### 3.2 Key Design Principles

1. **Separation of concerns** — environment knows nothing about optimisation; algorithms know
   nothing about adaptation; evaluation is entirely after-the-fact.
2. **One config system** — Hydra dataclasses; no parallel YAML-and-code drift.
3. **Immutable shared world** — `GraphView` is frozen; no arm can mutate what another arm sees.
4. **Pluggable controllers** — `Controller` is a Protocol; a RL agent can replace the rule-based
   engine without touching anything else.
5. **Evaluation budget in work, not iterations** — candidate path constructions, so a controller
   cannot buy CPU by enlarging its population.

---

## 4. Environment

### 4.1 Graph Data Structure (`core/graphview.py`)

The graph is stored as a **Compressed Sparse Row (CSR)** structure, allocated once per trial and
never reallocated. This is split into two objects:

**`Topology`** — fixed directed-slot structure shared by every timestep:
```
indptr[u] .. indptr[u+1]  →  slice of neighbour slots for node u
indices[slot]             →  destination node
rev[slot]                 →  slot index of the reverse arc
base_weight[slot]         →  free-flow (uncongested) weight
base_active[slot]         →  present in the initial graph?
pos[node]                 →  (x, y) coordinates (geometric/grid only)
weight_scale              →  cost per unit Euclidean distance
```

**`GraphView`** — one timestep's mutable state (frozen numpy arrays):
```
topology   →  the fixed Topology above
weight[]   →  current per-slot weight (symmetric via rev)
active[]   →  current per-slot presence mask (symmetric)
t          →  timestep index
```

Key operations:
- `state_hash()` — Blake2b digest over `weight` and `active`; used by the harness to assert no arm
  mutated the world
- `path_cost(path)` — sum of traversed weights; returns `inf` if any edge is inactive
- `find_slot(u, v)` — binary search in sorted CSR row

**Why a static topology superset?** Addition events need somewhere to add edges *to*. Allowing
arbitrary additions forces a dictionary rebuild every mutation. Instead, a bounded pool of candidate
edges is pre-allocated alongside base edges. Edges are switched on/off via the `active` mask.
Pheromone becomes a flat `float64` array indexed by slot — a deactivated edge that later reopens
keeps the trail it had.

### 4.2 Graph Generation (`core/generate.py`)

Three supported models, chosen via `cfg.graph.model`:

| Model | Edge structure | Has coordinates | Notes |
|---|---|---|---|
| `erdos_renyi` | Random: each pair connected w/ prob `density` | No | Default. A* degenerates to Dijkstra (no heuristic). Only useful for small graphs. |
| `geometric` | Points in unit square; connect if distance ≤ radius | Yes | **Primary research tier.** A* gets a real Euclidean heuristic. |
| `grid` | N×N lattice, 4-connected | Yes | Manhattan metric. Worst case for A* pruning. |

**Build procedure:**
1. Sample topology under the chosen model
2. `_ensure_connected()` — union-find; bridge disconnected components
3. `_addable_pool()` — sample candidate edges that addition events may later switch on
   (bounded to `addable_pool_factor × |E|` to avoid O(N²) allocation)
4. `_to_csr()` — assemble sorted CSR over `edges ∪ pool`; assign weights:
   - **Spatial models:** `weight = weight_min + dist * (weight_max - weight_min)`, where `dist` is
     Euclidean or Manhattan distance. This makes A*'s heuristic admissible.
   - **Erdős–Rényi:** uniform random in `[weight_min, weight_max]`
5. `_endpoints()` — source = node 0; target = farthest reachable node (Dijkstra)

```
GraphCfg parameters:
  model             erdos_renyi | geometric | grid
  n_nodes           node count (default 30)
  density           edge probability / connection radius scaling
  weight_min/max    edge weight range (default 1.0 / 100.0)
  addable_pool_factor  pool size as multiple of |E| (default 1.0)
```

**Pre-defined tiers (registered with Hydra):**

| Name | Model | n_nodes | density |
|---|---|---|---|
| `small30` | erdos_renyi | 30 | 0.3 |
| `medium200` | geometric | 200 | 0.04 |
| `large1000` | geometric | 1000 | 0.01 |
| `grid20` | grid | 400 | — |

### 4.3 Dynamic Events (`core/events.py`)

Six event kinds, each affecting one or more edges in a **spatially coherent cluster**:

| Kind | Effect on the graph |
|---|---|
| `closure` | Edge weight → very large (effectively infinite) |
| `traffic_up` | Weight × `traffic_factor` (default 2.0) |
| `traffic_down` | Weight ÷ `traffic_factor` (floored at free-flow) |
| `reopen` | Closed edge: new weight in `[free_flow, free_flow × traffic_factor]` |
| `delete` | Edge deactivated (switched off in the CSR mask) |
| `add` | Pool edge activated at free-flow weight |

**Why clusters?** A single uniformly-drawn edge is almost always irrelevant to any given route.
Measured on a 30-node graph, single-edge events left the optimal path untouched in 4 out of 6
trials. Clustering (25 edges per disruption) keeps events rare enough for quiet stretches while
making each one consequential.

**Event rate — Poisson, absolute:** `count ~ Poisson(events_per_step)`. Keeping the rate
*absolute* (not proportional to |E|) preserves quiet stretches at every graph size. A
proportional rate meant that at 1 200 edges even a modest fraction produced ~18 events/step,
so the graph never settled and recovery was unmeasurable.

**Connectivity guard:** events that would disconnect source from target are rejected. A permanent
disconnection wastes the rest of the trial without teaching anything; transient unreachability is
still possible and is measured by `path_availability`.

### 4.4 Pre-materialised Timeline (`core/timeline.py`)

**`build_schedule()`** materialises the entire event sequence *before* any optimizer exists,
returning a tuple of event tuples, one per timestep. This eliminates a class of bugs where two
arms experience different graphs depending on their order in the loop.

**`GraphTimeline`** — replayable wrapper:
- `state_at(t)` — pure, cached; returns the frozen `GraphView` for timestep `t` by replaying events
  from `t-1`. Every arm provably observes the same bytes.
- `events_at(t)` — events applied to reach state `t`

```
Flowchart: how a trial's world is built

  GraphCfg ──► build(cfg, rng)
                    │
                    ▼
               Topology (CSR) ─────────── fixed for the trial
               GraphView (t=0)
                    │
                    ▼
         build_schedule(view, scenario_cfg, rng, ...)
                    │
                    ▼
         schedule: tuple[tuple[Event,...], ...]  ← frozen before any arm runs
                    │
                    ▼
         GraphTimeline  ──► state_at(t)  ──► every arm gets this identical object
```

### 4.5 Scenario Configuration

```
ScenarioCfg parameters:
  name             scenario label (static | low | moderate | high)
  events_per_step  Poisson rate (0.0, 0.1, 0.3, 0.8)
  cluster_size     edges per disruption cluster (default 25)
  timesteps        steps per trial (default 60)
  p_closure        relative probability of closure (0.15)
  p_traffic_up     traffic increase probability (0.30)
  p_traffic_down   traffic decrease probability (0.20)
  p_reopen         reopen probability (0.10)
  p_delete         deletion probability (0.10)
  p_add            addition probability (0.15)
  traffic_factor   multiplier for traffic events (2.0)
```

**Fraction of undisturbed timesteps:**
`P(quiet) = e^{-rate}` → 100%, 90%, 74%, 45% for rates 0, 0.1, 0.3, 0.8

This guarantees quiet stretches where recovery can decay to — a precondition for measuring recovery
at all.
# Part 2 — Core Algorithms

## 5. The Optimizer Protocol (`optimizers/protocol.py`)

All four optimizers implement a single structural Protocol (`runtime_checkable`):

```python
class Optimizer(Protocol):
    PARAM_SPEC: ClassVar[Mapping[str, ParamSpec]]   # declared tunables
    name: str

    def rebind(self, view: GraphView) -> None: ...   # adopt mutated graph, keep state
    def spend(self, meter: EvaluationMeter) -> None: # search until budget exhausted
    def best(self) -> Solution | None: ...           # incumbent route
    def params(self) -> dict[str, float]: ...        # current parameter values
    def apply(self, values: Mapping[str, float]) -> None: ...  # adopt new values
    def probe(self) -> dict[str, float]: ...         # internal telemetry
    def reset_learned_state(self, strength: float) -> None: ...  # 0=noop, 1=full reset
```

**`Solution`** — frozen dataclass:
```python
@dataclass(frozen=True)
class Solution:
    cost: float           # total path weight
    path: tuple[int, ...]  # node sequence from source to target
```

**`EvaluationMeter`** — budget counter:
```python
meter.charge()      # +1 to spent; raises when budget exhausted
meter.exhausted     # True when spent >= budget
meter.spent         # total charged
meter.remaining     # budget - spent
```

### 5.1 Typed Parameter Binding (`optimizers/spec.py`)

Every tunable parameter is declared in the optimizer's `PARAM_SPEC` dict:

```python
@dataclass(frozen=True)
class ParamSpec:
    default: float   # value when nothing is supplied
    lo:      float   # inclusive lower bound
    hi:      float   # inclusive upper bound
    integer: bool    # round to nearest int on binding
    doc:     str     # what the parameter controls
```

`bind(table, values)` — validates names (unknown names **raise**), clamps all values to range,
returns a complete vector with defaults for unspecified names. This is what makes a silently-inert
parameter impossible: a typo raises instead of being absorbed.

---

## 6. A* (`optimizers/astar.py`)

A\* is not a swarm competitor — it is the **reference optimum**. Its cost at each timestep defines
what "perfect" means, and every other arm's quality is reported as excess over it.

**Implementation:** standard priority-queue best-first search with `(f_score, g_score, node)` heap
entries.

```
f(n) = g(n) + h(n)
  g(n) = actual cost from source to n
  h(n) = 0                          (erdos_renyi — no coordinates)
       = distance(n, target) × weight_scale   (geometric/grid)
```

**Admissibility:** the heuristic never overestimates because edge weights are ≥ free-flow cost =
`distance × weight_scale`, so covering any distance costs at least `distance × scale`.

**`PARAM_SPEC`:** `{}` — no tunables. A\* is parameter-free.

**`rebind()`:** deliberately discards the previous solution. A\* holds no transferable state, so it
pays a full re-search on every change — exactly the cost the project sets out to expose.

**`spend()`:** ignores the meter. A\* is exact and single-shot; giving it more budget cannot improve
it. It is therefore marked `metered=False` in the harness and its wall time / expansion count are
recorded for the scalability experiment but it is not budget-constrained.

**`probe()` returns:** `{"expansions": float}` — nodes popped from the heap. This is the
cost-of-recomputation metric for E5.

---

## 7. Ant Colony Optimisation — MAX–MIN Variant (`optimizers/aco.py`)

### 7.1 Algorithm

Simulated ants walk from source to target. At each node an ant picks its next hop probabilistically:

```
P(i → j)  ∝  τ_ij^α × η_ij^β

  τ (tau)  = pheromone on slot (i,j) — collective memory of past success
  η (eta)  = visibility = 1 / (w + goal_weight × h)
               w          = current edge weight
               h          = geometric distance from j to target × weight_scale
  α (alpha) = trail exponent (trust accumulated memory)
  β (beta)  = visibility exponent (trust immediate edge cost)
```

**One iteration:**
1. Each of `n_ants` ants constructs a path via roulette-wheel selection
2. **Evaporate** — `τ ← τ × (1 − ρ)` for all active slots
3. **Deposit** — the best ant lays `1 / cost` on each slot of its path (symmetrically via `rev`)
4. **Clamp** — `τ_max = 1 / (ρ × C_best)`, `τ_min = τ_max / (2n)`, applied to all active slots

### 7.2 Trail Limits (MAX–MIN Ant System)

Without bounds the ratio between the strongest and weakest trail grows without bound. Measured: by
iteration 80 on a 30-node graph the ratio reached 9×10⁸, and every ant walked an identical path
— the colony stopped sampling alternatives and no evaporation setting could revive it.

Following Stützle & Hoos's MAX–MIN Ant System, bounds cap the ratio at `2n`, making adaptation
measurable because the controller's evaporation dial remains connected to something.

### 7.3 Goal Direction

Visibility is `1 / (w + goal_weight × h)` where `h` is the geometric distance from the arc's
destination to the target. Cheapness alone is insufficient for a *point-to-point* problem: without
the goal term a colony on a 200-node graph settled ~90% above optimum because ants had no notion
of where the target lay. On 30-node graphs they stumbled to it by chance.

### 7.4 Carrying Trails Across Disruptions

`rebind()` keeps the trail on every surviving slot. This is deliberate — the stale trail on a
favoured road that just closed *is* the phenomenon the project studies. A trail zeroed on a slot
that has gone inactive (via the `active` mask) avoids resurrecting a stale preference if the edge
later reopens.

### 7.5 `PARAM_SPEC`

| Name | Default | Range | Meaning |
|---|---|---|---|
| `alpha` | 1.0 | [0, 5] | trail exponent |
| `beta` | 2.0 | [0, 8] | visibility exponent |
| `rho` | 0.10 | [0.01, 0.90] | evaporation rate |
| `n_ants` | 20 | [4, 100] | paths built per iteration (integer) |
| `goal_weight` | 1.0 | [0, 5] | pull of geometric distance-to-target |

### 7.6 `probe()` returns

| Key | Meaning |
|---|---|
| `lambda_branch` | Mean competitive arcs per recently-visited node (colony convergence) |
| `tau_ratio` | Strongest / weakest trail on active slots |
| `iterations` | Iteration count since construction |

**Lambda branching:** a value near 1 means each node retains a single attractive onward arc —
the colony has converged. Values approaching the mean degree mean it is still exploring.
Only nodes recently visited are counted; untouched nodes have uniform trails and including them
would report false diversity.

### 7.7 Performance Details

Ant construction is written against **plain Python lists** (mirrors of numpy arrays), refreshed
once per iteration. A 200-node graph with degree ~18 means 12-element candidate sets where numpy
dispatch overhead dominates data work. Profiling placed 72% of runtime in `_construct()`, and
switching to Python lists measured a 2-3× speedup for this inner loop. Bulk operations (evaporation,
deposit, clamping) remain vectorised numpy.

A pre-filled random buffer of 4096 uniform draws is maintained to avoid a numpy call per roulette
step.

---

## 8. Particle Swarm Optimisation — Priority-Vector Encoding (`optimizers/pso.py`)

### 8.1 Encoding

PSO natively optimises real vectors. The project uses a **priority-vector encoding**:

- Each particle holds a real vector of length `n` — one **priority per node**, in `[0, 1]`
- To build a path: start at source; at each step take the unvisited neighbour maximising
  `priority[v] × η(u, v)` (same visibility as ACO — keeping the two comparable)
- If the greedy walk dead-ends, **repair** by perturbing priorities and retrying (up to
  `repair_attempts` times, each charged to the meter)

**Why not bias edge weights?** The tempting encoding gives each particle a per-node bias `b` and
takes the shortest path under `w'(u,v) = w(u,v) × (1 + b[v])`. It always yields a valid path
and contains the optimum at `b = 0` — but that makes the search space include the answer at a
distinguished point, which turns the method into Dijkstra wearing a costume.

### 8.2 Velocity Update

```
v ← w·v  +  c1·r1·(personal_best − x)  +  c2·r2·(global_best − x)
x ← clamp(x + v, 0.0, 1.0)

  w  (inertia)    momentum; higher = more exploration
  c1 (cognitive)  pull toward the particle's own best position
  c2 (social)     pull toward the swarm's global best
  r1, r2          uniform random draws per update
```

### 8.3 Handling Disruptions

On `rebind()`:
- **Positions stay** — node priorities rank nodes, not edges, so a closure does not invalidate
  the ranking itself
- **Costs are invalidated** — `own_cost[:] = inf`. Costs were priced against a graph that no
  longer exists; carrying them forward would let the swarm chase a route that has since closed
- **Global best position is kept** — discarding the swarm's attractor as well left every particle
  with no social pull until some particle happened to succeed. Measured: that cost ~90 points of
  excess under disruption

### 8.4 `PARAM_SPEC`

| Name | Default | Range | Meaning |
|---|---|---|---|
| `inertia` | 0.7 | [0, 1] | velocity carry-over |
| `cognitive` | 1.5 | [0, 4] | pull toward personal best |
| `social` | 1.5 | [0, 4] | pull toward global best |
| `n_particles` | 20 | [4, 100] | swarm size (integer) |
| `goal_weight` | 1.0 | [0, 5] | pull of geometric distance in visibility |
| `repair_attempts` | 3 | [0, 10] | perturbations tried on dead-end (integer) |

### 8.5 `probe()` returns

| Key | Meaning |
|---|---|
| `diversity` | Mean std-dev of priorities across particles (swarm convergence) |
| `iterations` | Iteration count |

### 8.6 Swarm Resize

When `n_particles` changes via `apply()`:
- **Shrink** → keep the fittest particles (lowest `own_cost`)
- **Grow** → append random new particles with `own_cost = inf`

---

## 9. Hybrid ACO-PSO (`optimizers/hybrid.py`)

### 9.1 Rationale

The two methods **fail differently**:

- **ACO** accumulates structure across timesteps. That memory is worth ~15 percentage points of
  excess on a 200-node graph. But the same memory is a liability immediately after a disruption —
  trails still point at a road that just closed.
- **PSO** carries no edge memory. Its priorities rank nodes, not edges, so a closure invalidates a
  remembered *cost* but not the ranking. It is weaker in steady state (~2× ACO's excess) and
  correspondingly unbothered by staleness.

**The bet:** the memoryless component covers the memory component's known failure window — the steps
immediately after a disruption. This makes a falsifiable prediction: any advantage should appear
*in the timesteps just after a disruption*, not uniformly.

### 9.2 Implementation

The hybrid holds one `ACO` and one `PSO` instance with independent sub-streams (so retuning one
cannot perturb the other's draws).

**`spend()`** splits the timestep's budget by `aco_fraction`:
```
aco_share = round(budget × aco_fraction)
pso_share = budget − aco_share

Each component gets its own sub-EvaluationMeter.
The parent is charged what they actually spent (cannot smuggle extra work).
```

**`_exchange()`** (bidirectional, after each spend):
1. **Colony → Swarm:** The colony's best path raises the swarm's priorities along those nodes by
   `+EXCHANGE_GAIN` (= 0.25), nudging particles toward the colony's known route
2. **Swarm → Colony:** The swarm's best path deposits `1 / cost` trail on the colony

Both are nudges (`EXCHANGE_GAIN = 0.25`); a stronger coupling would collapse the two searches
into one and forfeit the diversity that motivates running them together.

### 9.3 `PARAM_SPEC`

All ACO parameters prefixed `aco_`, all PSO parameters prefixed `pso_`, plus:

| Name | Default | Range | Meaning |
|---|---|---|---|
| `aco_fraction` | 0.5 | [0.05, 0.95] | share of budget given to the colony |

**This is the key lever for the allocation thesis (E4):** driven by the `recency` signal,
an adaptive controller can shift the budget toward the swarm immediately after a disruption
(when trails are stale) and back toward the colony during calm stretches.

### 9.4 `probe()` returns

Both components' probes, prefixed by origin (`aco_lambda_branch`, `pso_diversity`, etc.) plus
`aco_fraction` (current split) and `exchanges` (total exchange count).

---

## 10. Algorithm Comparison Summary

```
                    A*           ACO          PSO          Hybrid
──────────────────────────────────────────────────────────────────
Type                exact        stochastic   stochastic   stochastic
Learned state       none         pheromone    positions    both
State on change     discarded    kept (stale) cost inval   both
Budget-metered      no           yes          yes          yes
Tunables            0            5            6            12
Controller target   —            rho          inertia      aco_fraction
Role in project     optimum ref  competitor   competitor   primary arm
```

**ACO wins in steady state** over PSO by ~2×. **Hybrid typically beats both** (current standing:
7.1% vs ACO's 9.3% at p=0.004 in the busiest scenario, n=10 trials). **A\* is perfect by
construction** (0% excess always) but this is meaningful only at small scale.
# Part 3 — Adaptive Controller, Experimental Harness & Statistics

## 11. Adaptive Controller

The controller implements a closed feedback loop wrapped around any optimizer:

```
                ┌─────────────────────────────────────────────┐
                │                                             │
                ▼                                             │
         ┌─────────────┐  observe   ┌──────────────┐         │
         │ ENVIRONMENT │ ─────────► │    Signal    │         │
         │ GraphTimeline│           │ (one of four)│         │
         └─────────────┘           └──────┬───────┘         │
               ▲                          │ reading          │
               │                          ▼                  │
               │ rebind          ┌──────────────────┐        │
               │                 │   Controller     │        │
         ┌─────────────┐         │ (incremental /   │        │
         │  OPTIMIZER  │◄────────│  null /          │        │
         │ ACO/PSO/    │ apply() │  prescheduled)   │        │
         │ Hybrid      │         └──────────────────┘        │
         │             │                                      │
         │ spend(meter)│──────────────────────────────────────┘
         └─────────────┘
```

**Sense → Propose → Apply** happens *after* the arm has searched each timestep, so a controller
reacts to what this timestep revealed rather than to a state that no longer holds.

---

### 11.1 Signals (`control/signals.py`)

A signal is a `Protocol` with three methods: `observe(StepObservation)`, `value() -> float`,
and two attributes: `name` and `explore_direction` (±1).

All signals receive a `StepObservation` (not the optimizer itself), so they can be unit-tested in
isolation and none can reach into search internals another signal would not have.

Four signals are registered:

#### `EdgeRatioSignal`
```
value = mean over window of (n_events / n_active_edges)
explore_direction = +1
```
The intuitive reading of "how much is the world changing". **Limitation:** with disruption driven
at an absolute rate, dividing by `|E|` makes the signal read smaller on larger graphs. A threshold
written against it is therefore graph-specific, and on the research tiers it never left the "low
change" regime — classifying every scenario (including the most volatile) identically. This was the
original failure of the DPO legacy system.

#### `VolatilitySignal`
```
value = mean over window of (1 if n_events > 0 else 0)
explore_direction = +1
```
Fraction of recent timesteps that carried *any* disruption. Insensitive to how *much* changed,
only to how often. Bounded to [0, 1] at any graph size.

**Limitation:** saturates once the expected event count per step exceeds one or two. At 4+
events/step it pins at 1.0 and the controller driven by it cannot move.

#### `LambdaBranchingSignal`
```
value = mean competitive arcs per recently-visited node  (from aco.probe())
explore_direction = -1   (low branching → needs more exploration)
```
The one *internal* signal — reads the search rather than the world. A reading near 1 means the
colony has converged. Across scenarios its readings were 7.30, 7.38, 7.14, 7.24 (static to high)
— a spread of ~3% of its range, not even monotone. It is therefore **a colony stagnation detector,
not a volatility proxy**. Useful for detecting when exploration is needed *now*, useless for
tracking churn.

#### `RecencySignal`
```
value:  1.0 on timestep a disruption lands,
        decays geometrically: value *= decay (default 0.7) each quiet step
explore_direction = +1
```
Reads the *transient* after a disruption. Largest exactly when memory is least trustworthy. This
is the signal used by the allocation experiment (E4): the budget is shifted toward the memoryless
PSO component right after a disruption and back toward ACO during calm.

**Why `recency` for E4 and not `volatility`?** The parameter sweep showed that optimal parameters
do *not* vary with the steady-state volatility rate — the same vector performs well at any rate.
But `recency` describes a transient: a disruption just landed and the trail is maximally stale.
That is a different quantity, and the sweep said nothing about it.

---

### 11.2 Controllers (`control/controllers.py`)

A controller is a `Protocol` with one method: `propose(signal, current_params, t) -> dict[str, float]`.

Three controllers are registered:

#### `NullController` (the ablation arm)
```python
def propose(self, signal, current, t):
    return dict(current)   # never changes anything
```
Deliberately a controller rather than an absence of one. The adaptive and frozen arms run the
same code path, differing only in which controller object they hold, so any divergence is
attributable to adaptation and to nothing else.

#### `IncrementalController`
```python
# Nudge params by +/- sigma based on signal pressure vs running baseline

reading  = signal.explore_direction * signal.value()
baseline += baseline_alpha * (reading - baseline)    # EMA
pressure = reading - baseline

if |pressure| > deadband and t % adapt_every == 0:
    step = +sigma if pressure > 0 else -sigma
    for name in targets:
        sign = EXPLORE_SIGN[name]
        proposed[name] = current[name] + sign * step
```

**Design choices:**
- **Increments, not presets:** Jumping to a regime-specific value discards accumulated state on the
  strength of one noisy reading. Small steps let evidence accumulate; a misread costs little. This
  follows Mavrovouniotis & Yang who use σ = 0.001.
- **Baselines, not thresholds:** Comparing against the signal's own running baseline avoids
  justifying an absolute threshold for each signal separately. A threshold outside a signal's
  attainable range silently freezes the controller.

**`EXPLORE_SIGN` table** — which direction moves each parameter toward exploration:

| Parameter | Sign | Reasoning |
|---|---|---|
| `rho` | +1 | Faster evaporation forgets sooner → more exploration |
| `alpha` | −1 | Higher α trusts trail → exploits |
| `beta` | −1 | Higher β leans on edge cost (greedy) → exploits |
| `aco_alpha`, `aco_beta` | −1 | Same reasoning for hybrid |
| `aco_rho` | +1 | Same reasoning for hybrid |
| `aco_fraction` | −1 | Shifting budget toward colony buys accumulated structure; away = explore |

**Parameters:**

| Name | Default | Meaning |
|---|---|---|
| `targets` | `("rho",)` | Parameters to adapt |
| `sigma` | 0.001 | Step size per cycle |
| `deadband` | 0.0 | Min pressure to act |
| `baseline_alpha` | 0.05 | EMA weight on newest reading |
| `adapt_every` | 1 | Timesteps between adaptation cycles |

#### `PrescheduledController`
Varies parameters on a fixed timetable, ignoring the signal. Included as the honest control for
feedback itself: if an open-loop schedule matches a signal-driven controller, what helped was
*varying* the parameter, not *sensing* anything. This baseline makes that conclusion reachable.

---

## 12. Experimental Harness

### 12.1 Arm Specification (`harness/arm.py`)

An **`Arm`** bundles an optimizer with its reporting identity:

```python
@dataclass
class Arm:
    name:       str           # label in results; unique within a trial
    family:     str           # random-stream key
    optimizer:  Optimizer
    metered:    bool = True   # competes under shared budget?
    signal:     Signal | None = None
    controller: Controller | None = None
```

**`family` vs `name`:** the family keys the random stream. Two arms that differ only in
whether a controller is active draw *identical* randomness and can diverge for exactly one reason.
Keying on `name` instead would give them different bits and confound the comparison.

**Registered arms (`ARM_BUILDERS`):**

| Name | Family | Optimizer | Signal | Controller |
|---|---|---|---|---|
| `astar` | `astar` | AStar | — | — |
| `aco` | `aco` | ACO | — | — |
| `aco_fixed` | `aco_controlled` | ACO | volatility | none |
| `aco_adaptive` | `aco_controlled` | ACO | volatility | incremental |
| `pso` | `pso` | PSO | — | — |
| `hybrid` | `hybrid` | Hybrid | — | — |
| `hybrid_fixed` | `hybrid_controlled` | Hybrid | recency | none |
| `hybrid_adaptive` | `hybrid_controlled` | Hybrid | recency | incremental |

`aco_fixed` and `aco_adaptive` share `family="aco_controlled"` → identical randomness → the only
difference is whether the controller moved `rho`. That is the ablation.

### 12.2 The Shared Timestep Loop (`harness/trial.py`)

**`run_trial(cfg, trial, arm_names, seeds)`** is the heart of the project:

```
Flowchart: one trial

  seed = pool[trial % len(pool)]

  build(cfg.graph, stream(seed, "graph"))
      → view (GraphView), source, target

  build_schedule(view, cfg.scenario, stream(seed, "events"), ...)
      → schedule  (frozen before any arm sees it)

  GraphTimeline(view, schedule)

  build_arms(arm_names, view, source, target, root_seed, trial, cfg.control)
      → arms[]  (each with its own stream derived from its family)

  for t in range(timesteps):
      state = timeline.state_at(t)        ← identical frozen object for all arms
      before_hash = state.state_hash()
      optimum, _, _ = shortest_path(state, source, target)

      for arm in arms:
          arm.optimizer.rebind(state)
          assert state.state_hash() == before_hash   ← arm did not mutate world

          meter = EvaluationMeter(budget)
          arm.optimizer.spend(meter)

          solution = arm.optimizer.best()
          probe = arm.optimizer.probe()

          assert solution.cost >= optimum - tol       ← cost model agrees with oracle

          if arm.signal is not None:
              arm.signal.observe(StepObservation(...))
              arm.controller.propose(arm.signal, arm.optimizer.params(), t)
                  → arm.optimizer.apply(proposed_params)

          record StepRow(...)
```

**Three in-loop assertions** (fail loudly on silent bugs):
1. An arm's cost ≥ true optimum — cost model and oracle agree
2. State hash unchanged after each `rebind` — no arm mutated the shared world
3. Every arm was handed the identical state hash — nobody got an easier problem

**`StepRow`** — one arm's result at one timestep (written to Parquet):

| Column | Meaning |
|---|---|
| `scenario`, `trial`, `seed`, `timestep`, `arm` | Indexing keys |
| `optimum` | Exact shortest path cost at this timestep |
| `best_cost` | Arm's incumbent cost |
| `excess` | `best_cost / optimum − 1` (primary quality metric) |
| `path_valid` | Whether the arm holds any route |
| `path_changed` | Whether the route changed from the previous timestep |
| `evaluations_spent` | Budget actually used |
| `wall_ms` | Wall-clock time |
| `astar_expansions` | Nodes expanded (A* only) |
| `signal_kind`, `controller_kind` | Adaptation identity |
| `signal_value` | Sensed reading at this step |
| `params` | Full parameter vector at this step |
| `probe` | Internal telemetry dict |

### 12.3 Seed Architecture (`core/rng.py`)

**`stream(seed, *tags)`** produces a `numpy.random.Generator` by hashing the seed and tags into
a reproducible bit sequence. Tags are arbitrary objects; the sequence is stable under insertion of
new tags (a new arm adds a tag, not an index, so existing arms are not disturbed).

**Two seed pools:**
- `tune_seeds` — used by the tuner only
- `eval_seeds` — reported on

**They must be disjoint.** Selecting a configuration on the same seeds it is later judged on
turns the headline figure into a maximum over noise. The harness raises `ValueError` if they
overlap. Default: `tune_seeds = [9000..9016)`, `eval_seeds = [1000..1032)`.

---

## 13. Metrics and Statistics

### 13.1 Primary Metric: Excess Over Optimum

```
excess(t) = best_cost(t) / optimum(t) − 1
```

Raw path cost is not comparable across timesteps once the graph changes: a run can appear to
improve simply because the graph became cheaper. Excess over the **moving optimum** (A\*
recomputed each timestep) removes this confound.

A\* scores exactly 0.0% excess in every row by construction — it is the denominator.

### 13.2 Recovery Metrics (`analysis/recovery.py`)

Three quantities, each answering a different question:

**`damage`** — how far quality falls in the steps right after a disruption:
```
baseline = mean excess over calm_before (default 2) steps before the event
damage   = max(excess[t : t + damage_window]) − baseline
```
Negative damage is possible (an event can open a shorter route).

**`recovery_time`** — how many steps until quality returns to within `RECOVERY_BAND` (10%) of
the pre-disruption baseline.

**`settled_excess`** — mean excess during quiet-only timesteps (where `num_events == 0`). This
is the steady-state number; recovery measures deviations from it.

**Scoring rules:**
- Disruptions too close to the end of a trial (`< MIN_HORIZON = 8` steps remaining) are **dropped**
  — not counted as unrecovered. An arm hit on the final timestep has no opportunity to recover;
  scoring that as failure is right-censoring bias that falls unevenly.
- A clean baseline requires `calm_before` consecutive quiet steps before the event — prevents
  confounding with tails of earlier disruptions.
- `per_trial_recovery()` groups by all trial-identifying columns and returns one row per condition,
  carrying `mean_damage`, `mean_recovery`, `recovered_fraction`, `n_disruptions`, `settled_excess`.

### 13.3 Statistical Tests (`analysis/stats.py`)

**Three commitments preventing common analysis errors:**

**1. Pair on trials, not timesteps.**
Sixty successive timesteps within a trial share a graph and an event sequence — strongly dependent.
Treating them as independent inflates the sample by the trial length and shrinks every p-value
accordingly. The harness reduces each trial to a scalar (mean excess) before comparing.

**2. Holm correction for the family.**
A signal-by-scenario grid runs ~12 comparisons; at α=0.05 roughly one in twenty clears the
threshold by chance. Holm's step-down correction is applied to the whole family:
```python
holm_correct(comparisons, alpha=0.05)
```
Holm is used rather than Bonferroni because it is uniformly more powerful and equally valid with
no assumption of independence between tests. Reports use `p_holm`, not `p_value`.

**3. Effect size alongside every p-value.**
Significance says a difference is unlikely to be zero; it says nothing about whether it matters.
With enough trials a tenth of a percentage point clears any threshold.

**Cliff's delta** (distribution-free):
```
delta = (n_concordant − n_discordant) / (n_a × n_b)
  → [-1, 1]; 0 = interleaved distributions
  → |delta| < 0.147 = negligible, < 0.33 = small, < 0.474 = medium, else large
```

**`compare_arms(frame, arm_a, arm_b, metric, within, alpha)`** — runs `paired_compare` for every
condition in `within` (e.g., every scenario × signal combination), applies Holm correction across
the whole family, returns a DataFrame with one row per condition:

| Column | Meaning |
|---|---|
| `n_pairs` | Trials contributing to both arms |
| `{arm_a}`, `{arm_b}` | Mean metric for each arm |
| `delta` | `mean_a − mean_b` |
| `p_value` | Raw Wilcoxon two-sided p |
| `p_holm` | Holm-corrected p across the family |
| `cliffs_delta` | Effect size |
| `effect` | Conventional label |
| `significant` | Whether adjusted p < α |

### 13.4 Figures (`analysis/plots.py`)

Four figures, each answering one question tables cannot:

| Function | Question answered |
|---|---|
| `excess_over_time(frame)` | Does quality visibly respond to disruptions? (with disruption markers) |
| `arm_comparison(per_trial)` | How wide is the trial-to-trial spread vs the gap between arms? (scatter, not bar) |
| `recovery_profile(frame)` | Does the transient exist at all, and does the hybrid recover faster? (aligned on event) |
| `scaling(frame)` | Does A\*'s cost grow with graph size, and does quality hold up? (log-log) |

Every figure draws **per-trial points** alongside summaries. In this project the trial-to-trial
spread has repeatedly been larger than the gap between arms; a bar chart would hide exactly that.
# Part 4 — Configuration, Tuning, CLI, Visualization, Tests, Results & Roadmap

## 14. Configuration System (`config.py`)

**One configuration system.** Every group is a Hydra-registered dataclass. The dataclass *is* the
schema: a key that no component reads cannot exist, and a mistyped key fails at compose time
rather than being silently ignored at runtime.

### 14.1 Dataclass Hierarchy

```
Config
├── root_seed: int = 42
├── report: bool = False
├── graph:      GraphCfg
│   ├── model: str = "erdos_renyi"
│   ├── n_nodes: int = 30
│   ├── density: float = 0.3
│   ├── weight_min/max: float = 1.0 / 100.0
│   └── addable_pool_factor: float = 1.0
├── scenario:   ScenarioCfg
│   ├── name: str = "moderate"
│   ├── events_per_step: float = 0.3
│   ├── cluster_size: int = 25
│   ├── timesteps: int = 60
│   ├── p_closure/p_traffic_up/.../p_add: float
│   └── traffic_factor: float = 2.0
├── experiment: ExperimentCfg
│   ├── name: str = "smoke"
│   ├── arms: list[str] = ["astar", "aco"]
│   ├── n_trials: int = 2
│   ├── tune_seeds: list[int] = [9000..9016)
│   ├── eval_seeds: list[int] = [1000..1032)
│   ├── parallel_jobs: int = 1
│   └── record_traces: bool = False
├── budget:     BudgetCfg
│   └── evaluations: int = 300
├── control:    ControlCfg
│   ├── signal: str | None = None      (overrides each arm's default)
│   ├── window: int = 10               (rolling-window length)
│   ├── targets: list[str] = ["rho"]   (parameters to adapt)
│   ├── sigma: float = 0.001
│   ├── deadband: float = 0.0
│   ├── baseline_alpha: float = 0.05
│   ├── adapt_every: int = 1
│   └── fixed_params: dict[str, float] = {}  (starting point for both ablation arms)
└── tuning:     TuningCfg
    ├── enabled: bool = False
    ├── arm: str = "aco"
    ├── candidates: int = 60
    ├── trials: int = 6
    └── params_file: str | None = None
```

### 14.2 Hydra Groups

Pre-registered config groups (can be overridden on the command line with `graph=medium200`):

**Graph tiers:**
| Group key | model | n_nodes | density |
|---|---|---|---|
| `small30` | erdos_renyi | 30 | 0.3 |
| `medium200` | geometric | 200 | 0.04 |
| `large1000` | geometric | 1000 | 0.01 |
| `grid20` | grid | 400 | — |

**Scenarios:**
| Group key | events_per_step | P(quiet) |
|---|---|---|
| `static` | 0.0 | 100% |
| `low` | 0.1 | 90% |
| `moderate` | 0.3 | 74% |
| `high` | 0.8 | 45% |

**Control:**
| Group key | signal override |
|---|---|
| `edge_ratio` | edge_ratio |
| `volatility` | volatility |
| `lambda_branch` | lambda_branch |
| `default` | None (keep arm defaults) |

**Budgets:** `eval300` (300 evaluations), `eval2000` (2000 evaluations)

**Experiments:** `smoke` (2 trials), `main` (30 trials, 11 parallel jobs)

### 14.3 Reproducibility

Every run directory contains `manifest.json` (git commit, package versions, resolved Hydra
config). To repeat a run exactly:
```bash
python -m dynaswarm.cli --config-dir <run>/.hydra --config-name config
```
Seeds are trial entropy, not labels — the same seed gives the same graph and event sequence.
Two runs of the same config produce byte-identical `steps.parquet`.

---

## 15. Parameter Tuning (`tuning/best_fixed.py`)

### 15.1 Purpose

The established finding the controller must contend with (Stützle et al.) is that a **well-chosen
fixed setting** usually beats varying parameters at runtime. Testing against defaults would
answer a question nobody is asking.

The tuner searches for the best fixed parameter vector over `tune_seeds`, giving the ablation's
frozen arm a *hard opponent*. The comparison becomes **tuned-fixed vs adaptive**.

### 15.2 Optuna TPE Search

```
tune_best_fixed(cfg, n_candidates=60, n_trials=6, arm="aco")
```

1. Verify `tune_seeds ∩ eval_seeds = ∅` — raises if not
2. Create an Optuna study (`direction="minimize"`, `TPESampler(seed=cfg.root_seed)`)
3. For each candidate: suggest all parameters in `arm.PARAM_SPEC` via Optuna, evaluate
   `objective_value()` = mean excess over `n_trials` tuning-seed instances
4. Write best vector to `best_fixed.json`

**Parallelism:** over trials (joblib), not over Optuna candidates — the TPE sampler is sequential
by design, and parallelising the objective (CPU-bound Python) would gain nothing over GIL.

### 15.3 Applying Tuned Parameters

```python
# ControlCfg.fixed_params is applied to every arm at construction
optimizer.apply({k: v for k, v in fixed_params.items() if k in optimizer.PARAM_SPEC})
```

Both halves of an ablation start from the same tuned vector. Any difference between `aco_fixed`
and `aco_adaptive` afterwards is attributable to adaptation, not to starting point.

### 15.4 What the Sweep Found

A random search over 50 candidates per regime, 12 seeds each (legacy DPO system):

| Strategy | Mean excess |
|---|---|
| Hand-authored presets (the original) | ~0.036 |
| Best **single** preset used everywhere | 0.00056 |
| Best **per-regime** specialised presets | 0.00012 |

The presets were never tuned — the incumbent ranked 41st of 51 in the low regime. Fixing them buys
~0.035 excess; adapting them *per regime* buys a further ~0.0004. The achievable headroom from
volatility-driven adaptation is ~1% of what simply choosing good parameters achieves.

The same handful of configurations won in all three regimes. There is **no strong regime-specific
optimum** at this problem scale.

---

## 16. Command-Line Interface (`cli.py`)

Entry point: `python -m dynaswarm.cli` (or equivalently `dynaswarm.cli` as defined in
`pyproject.toml`).

The CLI is a Hydra application. All config groups can be overridden on the command line. Key usage
patterns:

```bash
# Smoke test (quick sanity check, ~10 seconds)
python -m dynaswarm.cli

# Main experiment: ACO vs Hybrid, moderate disruption, medium graph
python -m dynaswarm.cli \
  graph=medium200 scenario=moderate \
  'experiment.arms=[aco,hybrid]' \
  experiment=main report=true

# Multirun over scenario sweep
python -m dynaswarm.cli --multirun \
  graph=medium200 scenario=static,low,moderate,high \
  'experiment.arms=[astar,aco,pso,hybrid]' \
  experiment.n_trials=30 experiment.parallel_jobs=11 report=true

# Ablation experiment (E4 — allocation thesis)
python -m dynaswarm.cli --multirun \
  graph=medium200 scenario=moderate,high \
  control.signal=recency 'control.targets=[aco_fraction]' \
  control.sigma=0.01 \
  'experiment.arms=[hybrid_fixed,hybrid_adaptive]' \
  experiment.n_trials=30 experiment.parallel_jobs=11 report=true

# Tuning run
python -m dynaswarm.cli \
  tuning.enabled=true tuning.arm=hybrid \
  tuning.candidates=60 tuning.trials=12 \
  graph=medium200 scenario=high experiment.parallel_jobs=11

# Scalability (E5)
python -m dynaswarm.cli --multirun \
  graph=small30,medium200,large1000 scenario=moderate \
  'experiment.arms=[astar,aco,hybrid]' \
  experiment.n_trials=12 experiment.parallel_jobs=11 report=true
```

**Output structure:**
```
outputs/<date>/<time>/
├── manifest.json          git commit, pkg versions, resolved config
├── steps.parquet          all StepRow records
├── events.parquet         all EventRow records
├── figures/               PNG files (if report=true)
└── .hydra/config.yaml     the exact resolved config
```

---

## 17. Replay Visualizer (`viz/replay.py`)

**`replay(run_dir, arm, scenario, trial, fps, size)`** — reads finished results and re-renders them
in Pygame. It never drives a simulation, holds no optimizer, and imports nothing from the harness,
so it cannot perturb a result.

**Layout:** for spatial models (geometric, grid) the viewer reconstructs the trial's graph from
`manifest.json` and the per-trial seed — the same `build()` call the harness made — so positions
match actual node coordinates. For non-spatial models (erdős–rényi), a seeded random scatter
is used (stable but not geometrically meaningful).

**Rendering:**
- Background: dark (`#12121`6)
- Edges: disrupted → red, on current path → blue, normal → dim grey
- Nodes: path nodes → bright blue, source → green, target → amber
- Text overlay: timestep, disruptions, excess, optimum, current cost

**Controls:** Space = pause/resume, ← → = step frame by frame, Q/Esc = quit

**Limitation:** capped at 400 nodes (`MAX_NODES`) — beyond that the layout is unreadable.

**Requires `viz` extra:** `pip install -e ".[viz]"` (adds pygame).

---

## 18. Test Suite

271 tests, ~60 seconds. Four `slow` tests (tuning searches) excluded by default.

| File | Tests | What it protects |
|---|---|---|
| `test_control.py` | 27 | Signal dynamic range, controller step sizes, ablation correctness |
| `test_optimizers.py` | 24 | Budget exactness, parameter liveness, A\* correctness |
| `test_harness.py` | 23 | Shared world, stream independence, reproducibility |
| `test_analysis.py` | 17 | Recovery detection, Holm correction, effect sizes, figures |
| `test_environment.py` | 17 | Graph construction, event clustering, timeline purity |
| `test_hybrid.py` | 17 | PSO encoding, budget splitting, component exchange |
| `test_tuning.py` | 11 | Seed separation, per-arm parameter spaces |
| `test_rng.py` | 8 | Stream stability under arm insertion |
| `test_config.py` | 5 | Every config combination composes |
| `test_testbed.py` | 4 | The tier in use can show the effect being claimed |
| `test_hygiene.py` | 3 | No global RNG, no GUI imports, statement budget |

### 18.1 Key Tests Worth Knowing

**`test_signal_discriminates_scenarios`** — a signal must read differently in calm vs chaos by a
margin large enough to act on, not merely by a significant p-value.

**`test_every_parameter_changes_behaviour`** — parametrised off `PARAM_SPEC`, so a newly added
parameter cannot be introduced inert. Drives each parameter to both bounds and requires resulting
search trajectories to differ.

**`test_budget_is_spent_exactly`** — equal allowance must mean equal work, whatever the population
size. Validates that ACO at 20 vs 80 ants and PSO at 0.05 vs 0.50 mutation all spend ~300 of a
300 budget.

**`test_adding_an_arm_does_not_disturb_the_others`** — results must not depend on which other
arms are running. Validates stream isolation via the `family` key.

**`test_pheromone_contributes_on_the_science_tier`** — the mechanism under study must do
measurable work on the graphs in use, or a null result says nothing.

**`test_trials_reproduce_exactly`** — byte-identical `steps.parquet` across two runs of the same
config (excluding wall-clock timings).

---

## 19. Experimental Results (Measured)

### 19.1 The 400-Trial Study (Legacy DPO, July 2026)

Run over 400 independent trials per scenario (8 808 seconds). Primary metric: mean excess over
moving optimum. Arms: A\*, ACO, PSO, Fixed\_Hybrid, Adaptive\_Hybrid.

**Static (0% disruption):**

| Arm | Excess ± std | Availability |
|---|---|---|
| A\* | +0.0% | 100% |
| ACO | +8.1% ± 25% | 100% |
| PSO | +38.4% ± 72% | 100% |
| **Fixed\_Hybrid** | **+4.1% ± 15%** | 100% |
| **Adaptive\_Hybrid** | **+5.8% ± 18%** | 100% |

> Adaptive = 0.0585, Fixed = 0.0408 → **Fixed better**, Wilcoxon p = 0.0029 → **significant**

**Moderately Dynamic (30% disruption):**

| Arm | Excess | Recovery steps | Unrecovered |
|---|---|---|---|
| ACO | +7.2% | 8.5 | 17 |
| PSO | +37.0% | 12.3 | 46 |
| **Fixed\_Hybrid** | **+5.1%** | 5.7 | 11 |
| **Adaptive\_Hybrid** | **+5.0%** | 6.5 | 13 |

> Delta = −0.0007 (adaptive marginally better), p = 0.94 → **not significant**

**Highly Dynamic (70% disruption):**

| Arm | Excess | Recovery steps | Unrecovered |
|---|---|---|---|
| ACO | +8.2% | 10.0 | 45 |
| PSO | +35.4% | 11.8 | 105 |
| **Fixed\_Hybrid** | **+6.0% ± 17%** | 9.6 | 36 |
| **Adaptive\_Hybrid** | **+5.1% ± 13%** | 9.6 | **26** |

> Delta = −0.0094 (adaptive better), p = 0.23 → **not significant**

### 19.2 Current Standing (Dynaswarm v2, 10 trials)

On `medium200` (geometric, n=200), `high` scenario (0.8 events/step):
- ACO: ~9.3% excess
- Hybrid: ~7.1% excess
- Paired comparison: p = 0.004 (Holm-corrected)

**Caveat:** 10 trials is enough to see a large effect, not enough to bound a small one. Trial
variance runs 5–12%; ~30 trials is the minimum for a solid claim.

### 19.3 Reading Results Honestly

**What holds up:**
- The **Hybrid design works.** Both hybrid arms beat plain ACO and dramatically beat PSO in
  every scenario.
- The **adaptive arm degrades more gracefully.** Its standard deviation shrinks as volatility
  rises (18% → 16% → 13%) while others grow, and it leaves fewer disruptions unrecovered in the
  hardest scenario (26 vs 36).
- **PSO's priority-vector encoding is weak** for this problem — 35–38% above optimum.

**What does not hold up:**
- **The controller shows no significant benefit** anywhere at n=400. The only significant ablation
  result (Static scenario) favours the *frozen* arm.
- The achievable headroom from adaptation is ~1% of what choosing good parameters achieves.

**The honest framing (publishable):**
> We built a controlled harness for testing online parameter adaptation in dynamic path
> optimisation. Using it, we find that (a) parameter quality matters enormously — poorly chosen
> presets cost ~3.6% excess — while (b) adapting those parameters to measured volatility
> contributes ~0.04%, indistinguishable from noise at n = 400. We identify the harness design
> choices necessary to reach this conclusion, several of which invert the result when omitted.

---

## 20. Known Bugs & Limitations (Legacy DPO)

### 20.1 Bugs Now Fixed

| Component | Bug | Fix |
|---|---|---|
| `pheromone_forget` trigger | Used `smoothed_change_rate` which peaked at 0.007 → triggered 0 times | Switched to `volatility` |
| `hybrid.aco_weight` | Written to registry but never read; budget split hardcoded 50/50 | Added `set_aco_weight()`, budget now respects it |
| `pso.mutation_rate` setter | Silently dropped the value when swarm object didn't exist yet | Fixed to store value for swarm construction |
| `controller.apply_to_hybrid()` | Not called | Added |

### 20.2 The Legacy Benchmark Bug

`benchmark_runner.py` ran static algorithms on the base graph *before* the adaptive controller
began mutating it. Every algorithm returned the same cost in all three scenarios:
```
Static             A*=46.25  ACO=46.25  PSO=46.25  Hybrid=46.25
Moderately_Dynamic A*=46.25  ACO=46.25  PSO=46.25  Hybrid=46.25
Highly_Dynamic     A*=46.25  ACO=46.25  PSO=46.25  Hybrid=46.25
```

`dynamic_harness.py` was written to replace it with a properly controlled experiment.

### 20.3 Paper Numbers ≠ Measured Results

`paper/paper.tex` and `docs/presentation.md` report path costs of 142.3, 148.7, etc.;
t-statistics of −6.82; "p < 0.001" on every pairwise comparison; "18.3% improvement". None of
these numbers appear in any generated result file. They are placeholders that directly contradict
the 400-trial study. Must be corrected before submission.

---

## 21. Future Research Roadmap

**Phase 1 — Immediate (1–2 months):**
- Run E4 (allocation ablation) — the project's stated novelty, never yet tested
- Run E3 with 30 trials on the tuned hybrid
- Re-run the 400-trial study with all ten levers live (after the bug fixes)
- Point the default CLI and web dashboard at the fair harness; clearly mark the legacy runner

**Phase 2 — Short-term (3–6 months):**
- RL-based Decision Engine (PPO/SAC) via the `DecisionEngine` Protocol interface
- Multi-objective optimisation (NSGA-II, multiple pheromone matrices)
- Standard benchmark suite with real-world datasets (Sioux Falls, Chicago Sketch, OSM cities)
- PyPI packaging + Docker image

**Phase 3 — Medium-term (6–12 months):**
- Neural ACO (Pointer Networks / Transformer encoder with masked self-attention)
- Neural PSO (LSTM velocity updates)
- Grey Wolf Optimiser, Whale Optimisation, Cuckoo Search implementations
- Real-time OpenStreetMap + traffic API integration
- Test at scale (1 000–10 000 nodes) where A\* recomputation is genuinely expensive

**Phase 4 — Long-term (12–24 months):**
- Edge deployment (Raspberry Pi / NVIDIA Jetson)
- V2X simulation (Vehicle-to-Infrastructure / Vehicle-to-Vehicle)
- Meta-learning (MAML) for fast adaptation to new graph topologies
- Human-in-the-loop active learning

**Target venues:** GECCO, IEEE CEC (Paper 1); PPSN/ANTS (Paper 2 — RL control);
Transportation Research Part C (Paper 3 — multi-objective with real data)
