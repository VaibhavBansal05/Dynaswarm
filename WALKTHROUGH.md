# WALKTHROUGH

**A guided walk through Dynaswarm, with the checks at every stop.**

This file exists so you can sit down alone, follow the data from a single number all the way to a figure in your report, and satisfy yourself that every step does what it claims. It is both an explanation and a test plan — the two are interleaved on purpose, because a check you do not understand is a check you cannot trust.

---

## How to use this

Each stop has the same four parts:

**What happens** — the mechanism, in plain language.
**Where it lives** — the files, so you can read the real thing.
**See it yourself** — a command or a dashboard action.
**What you should see** — the expected output, and what a wrong one looks like.

Work through it in order the first time. After that it is a reference.

Everything assumes you are in the repository root with the virtual environment built:

```bash
cd ~/Desktop/ML\ Minor/Dynaswarm
./.venv/bin/pytest -m "not slow"        # should be green before you start
```

Two things are marked **[after 21]** — they do not exist until segment 21 lands.

---

# Part 0 — The whole thing, in one page

You have a road network. You have a start and a goal. You want the cheapest route between them.

That would be a solved problem, except the roads keep changing. They close, they reopen, they get slower, they get faster, some vanish and new ones appear. **So the cheapest route will not hold still** — and an algorithm that found the best answer at step 12 may be holding a bad answer, or an impossible one, by step 13.

The project measures how well different search algorithms cope with that.

**A\* is not a competitor.** It recomputes the exact best answer at every single step. It is the answer key — the thing everything else is measured against. The measure is called **excess**: how much worse than perfect your algorithm's route currently is.

**Three real competitors.** Ant Colony Optimisation keeps memory on the *roads* — a pheromone trail that builds up on good ones. Particle Swarm Optimisation keeps memory on the *places* — a set of opinions about which junctions are worth routing through. The Hybrid runs both and splits a fixed compute budget between them.

**And the actual contribution is what happens to that split.** The original idea was to adapt the algorithms' internal parameters. That was tried, it did not help, and the project can explain why. So the question changed: instead of tuning the search, **shift the compute between exploring and refining, based on how recently something broke.** Just after a disruption you want exploration. During calm you want refinement. The claim is that shifting the balance beats holding it fixed.

That is the whole project. Everything below is how it is built and how you check it.

```
seed ──► graph ──► timeline (all disruptions, decided up front)
                        │
                        ├──► A*        exact answer every step   ─┐
                        ├──► ACO       trails on roads            │  same
                        ├──► PSO       priorities on places       ├─ frozen
                        ├──► Hybrid    both, split by a fraction  │  timeline
                        └──► + 4 controlled arms  [after 21]     ─┘
                                        │
                                  run directory on disk
                                        │
                                  excess, recovery, statistics
                                        │
                                  report · deck · dashboard
```

---

# Stop 1 — The seed

## What happens

One number decides everything random in the entire run. Feed the same seed in and you get the same world, the same sequence of breaks, the same ant decisions, the same particle starting positions — on any machine, on any day.

It is not one generator though. The seed is split into named **streams**: one for building the graph, one for generating events, one for each algorithm. That separation matters more than it sounds. If every random draw came from one shared generator, then adding an ant would shift every later number — including the disruptions — and two arms would no longer be facing the same world. Named streams mean ACO can draw a thousand numbers and the timeline is untouched.

## Where it lives

`src/dynaswarm/core/rng.py` — `stream(seed, name)`.

## See it yourself

```bash
./.venv/bin/python -c "
from dynaswarm.core.rng import stream
a = stream(1000, 'graph').integers(0, 1000, 5)
b = stream(1000, 'graph').integers(0, 1000, 5)
c = stream(1000, 'events').integers(0, 1000, 5)
print('same seed+name :', a, b)
print('different name :', c)
"
```

## What you should see

The first two arrays **identical**. The third **different**. That is the whole guarantee: same stream reproduces, different streams are independent.

**Wrong looks like:** the first two differing. Then nothing in the project is reproducible and every result is a one-off.

---

# Stop 2 — The graph gets built

## What happens

You give it a model, a number of places, and a density. It builds a road network.

**Model matters more than anything else here.** `geometric` gives every place a real position on a unit square and connects places that are near each other — which is why it can be drawn, and why the picture looks like a map rather than a tangle. `grid` is a regular lattice. `erdos_renyi` connects places at random with no regard to distance, and has **no positions at all** — which is why the dashboard refuses to draw it rather than inventing a layout.

Then it picks the endpoints. **Source is always place 0.** The target is the *most distant reachable* place, found by running Dijkstra from the source and taking the furthest. That is deliberate: a fixed `(0, n-1)` pair would be trivially close on some graphs and the problem would evaporate.

**The bit worth understanding properly: nothing is ever created or destroyed later.** Every road that could ever exist — including ones that do not exist yet — gets a permanent slot at this moment. A flag called `base_active` records which slots are real roads at `t=0`; the rest are a *candidate pool*, latent roads that a future "new road" event can switch on. From here on, every disruption only ever flips a switch or changes a price. No slot is added, removed, or renumbered.

That is what makes a timeline replayable identically for every algorithm, and it is why the edge ledger on the dashboard can balance exactly.

## Where it lives

`src/dynaswarm/core/generate.py` — `build()` and `_endpoints()`
`src/dynaswarm/core/graphview.py` — the frozen `(weight, active, topology)` triple
`ARCHITECTURE.md` §4.1, §4.2, and **§4.3.1** — the slot model, written out

## See it yourself

```bash
./.venv/bin/python -c "
from dynaswarm.config import GraphCfg
from dynaswarm.core.generate import build
from dynaswarm.core.oracle import shortest_path
from dynaswarm.core.rng import stream
cfg = GraphCfg(model='geometric', n_nodes=200, density=0.04)
view, s, t = build(cfg, stream(1000, 'graph'))
cost, path, exp = shortest_path(view, s, t, heuristic=True)
print('places          ', view.n_nodes)
print('roads           ', view.n_active_edges)
print('has positions   ', view.topology.pos is not None)
print('start -> goal   ', s, '->', t)
print('cheapest route  ', round(cost, 4), 'in', len(path)-1, 'hops')
"
```

## What you should see

```
places           200
roads            735
has positions    True
start -> goal    0 -> 2
cheapest route   99.9633 in 11 hops
```

The exact numbers depend on the seed, but with seed 1000 on `medium200` you should get these precisely.

**Check by hand:** roads ÷ places should be around 7 — that is the mean degree the dashboard shows as *roads per place*. If it is 2, the graph is barely connected and most disruptions will disconnect it. If it is 40, nothing you break will matter.

**Wrong looks like:** `has positions False` on a geometric graph (then nothing can be drawn honestly), or a route of 1 hop (start and goal are neighbours, so the problem is trivial).

---

# Stop 3 — The world gets broken

## What happens

**Every disruption for the entire run is decided before anything runs.** All sixty timesteps of events are generated up front and frozen.

That is not a convenience. It is the reason the comparison means anything. If each algorithm generated its own disruptions as it went, they would face different worlds and *"the hybrid beat PSO"* would be a statement about luck. Frozen timeline, every arm replays the identical one.

**Six things can happen to a road**, and it is worth knowing they are not all "blocked":

| Event | Road usable after? |
|---|---|
| closure | no |
| delete | no, permanently |
| reopen | yes — was closed, now open |
| add | yes — a brand-new road from the candidate pool |
| traffic_up | **yes, just more expensive** |
| traffic_down | **yes, cheaper** |

Most events are the last two. The road is fine — it just costs more. That is why the cheapest route keeps moving even when nothing is blocked, and it is the difference between this and a maze.

**Events cannot act on nothing.** A closure can only target a road that is currently open. A reopen can only target a road that was in the original graph and is currently closed. An `add` can only target a pool slot that is currently off — so it can never "add" a road that already exists, and an added road can never be *reopened* later, only re-added. Original roads reopen; pool roads re-add. That distinction survives any number of cycles.

**Disruptions arrive in clusters, not singly.** A single random road closing is almost never on your route — measured on a small graph, single-edge events left the optimal path untouched in four trials out of six. So instead, one event takes out about 25 roads around one junction: a neighbourhood goes dark. Rare, but consequential.

**And one piece of arithmetic that has bitten this project hard.** `schedule[k]` holds the events that take you *from* state `k` *to* state `k+1`. So the events that **produced** state `t` are `schedule[t-1]`, not `schedule[t]`. Getting that wrong — reading one step into the future — was defect **F1**, and it invalidated every result the project had until it was found. There is now exactly one accessor, `events_at(t)`, and nothing else is allowed to index the schedule.

## Where it lives

`src/dynaswarm/core/events.py` — the six kinds, and `candidate_slots()` with the eligibility rules
`src/dynaswarm/core/timeline.py` — `build_schedule()`, `events_at()`, `state_at()`
`ARCHITECTURE.md` §4.3, §4.3.1, **§4.4 (the temporal contract)**

## See it yourself

Read the eligibility table first — it is the thing most worth understanding:

```bash
sed -n '147,177p' src/dynaswarm/core/events.py
```

Then watch the population stay closed:

**On the dashboard:** press **Generate**, then **Build**, and look at the **edge ledger** at the bottom right. Scrub from 0 to 59 and watch it.

## What you should see

The ledger must read **balances** at every single step. The arithmetic is exact, not approximate:

```
initial + added + reopened − closed − deleted = current
```

and `current` must equal the engine's own count of open roads — not the ledger's own running total. With seed 1000 on the default scenario:

| step | |
|---|---|
| t=0 | 735 + 0 + 0 − 0 − 0 = 735 |
| t=30 | 735 + 75 + 0 − 0 − 25 = 785 |
| t=59 | 735 + 75 + 9 − 50 − 25 = 744 |

**Notice `roads open` actually changes.** New roads are genuinely new — they connect a pair of places that had no road between them.

**Wrong looks like:** the ledger saying **DIVERGED**. That means the picture and the engine disagree about what exists, and nothing downstream can be trusted.

---

# Stop 4 — The trial loop

## What happens

This is the spine of the whole system, and it is a short loop.

For each timestep from 0 to the horizon: build the state at `t`, hand that state to every arm, give each arm an identical budget of evaluations, let it spend, then record one row per arm.

Three details carry all the weight.

**Every arm gets the identical state object.** `state_at(t)` is cached, so all four arms literally read the same bytes. The loop also asserts that no arm mutated the shared world — if one did, later arms would face a different graph and the comparison would be void.

**Every arm gets the same number of evaluations.** That is the fairness currency. An "evaluation" is one construction and pricing of a candidate route. An arm that got more would look better for a reason that has nothing to do with its algorithm.

**Every arm is told the graph changed, every step, unconditionally.** That call is named `rebind`, and it is how an optimizer receives the current world. It must happen every step — skipping it would leave an arm searching a stale graph. But what an optimizer *does* in response is its own business, and that is where defect **F13** lived: PSO threw away its entire memory on every call, including on the fifty-odd steps where nothing had changed. It now checks whether the graph actually differs first.

## Where it lives

`src/dynaswarm/harness/trial.py` — `run_trial()`, the loop
`src/dynaswarm/harness/runner.py` — `run_experiment()`, which loops trials and writes results
`src/dynaswarm/harness/arm.py` — the arm registry
`ARCHITECTURE.md` §10.1, **§10.2 (the five fairness guarantees)**

## See it yourself

```bash
sed -n '160,200p' src/dynaswarm/harness/trial.py
```

Read the loop. It is short enough to hold in your head, and that is deliberate.

Then run the smallest possible real experiment:

```bash
./.venv/bin/python -m dynaswarm.cli
```

## What you should see

A run completes in seconds and writes a directory under `outputs/<date>/<time>/`. Inside: `steps.parquet`, `events.parquet`, `manifest.json`, and a `.hydra/` folder with the exact configuration.

**The `.hydra/` folder is the reproducibility claim.** Any run can be re-run from its own recorded config — that is what makes a number in your report checkable by someone else.

**Wrong looks like:** an assertion about an arm mutating the shared world. That would mean the arms are not facing the same problem.

---

# Stop 5 — The four algorithms

## What happens

### A\* — the answer key

Exact shortest path, recomputed from scratch at every step. It has no memory and does not need any. Its only job is to produce the number everything else is measured against.

It uses a straight-line-distance heuristic on graphs that have positions, which makes it faster than plain Dijkstra without changing the answer — **provided the heuristic never overestimates.** If it ever did, A\* would silently return a route that is not the cheapest, and every excess figure in the project would be wrong in a way nothing else would catch. That is checked directly: on small graphs, against brute-force enumeration of every possible route.

### ACO — memory on the roads

Ants walk from start to goal, choosing each next road with a probability that favours roads with strong pheromone and low cost. When they arrive, the best ant lays pheromone along its route, so good roads get more attractive.

Two things stop it converging on one answer and staying there. **Evaporation** removes a fixed fraction of all pheromone every iteration, so old preferences fade. And **MAX–MIN bounds** clamp every trail between a floor and a ceiling, so no road can become so dominant that nothing else is ever tried. That clamp is the difference between MAX–MIN Ant System and plain Ant System, and it is the version the report names.

### PSO — memory on the places

A swarm of twenty particles. **A particle is not a position on the map** — it holds a list of priority numbers, one per place, which is effectively an opinion about which junctions are worth routing through. The route is then *built* from that opinion by walking the graph and preferring the highest-priority neighbour available.

Each particle is pulled toward the best opinion it has personally found and toward the best the swarm has found. Those pulls, plus its existing momentum, move it to a new opinion. Over many iterations the swarm concentrates on opinions that produce cheap routes.

The priority vector is also why a graph change does not destroy a particle: places do not move, so *"junction 47 is worth more than junction 12"* remains a coherent belief. What does not survive is the **price** attached to a remembered opinion, because that was measured on roads that have since changed.

### Hybrid — both, with a budget split

Runs ACO and PSO, giving each a share of the evaluation budget set by `aco_fraction`. At 0.5 they get 150 evaluations each out of 300. They exchange solutions, so a good route found by one is available to the other.

**This is where the thesis lives.** Everything above is machinery; the contribution is what happens to that fraction.

## Where it lives

`src/dynaswarm/optimizers/astar.py`, `aco.py`, `pso.py`, `hybrid.py`
`src/dynaswarm/core/oracle.py` — `shortest_path()`, `dijkstra()`
`ARCHITECTURE.md` §5.1, §5.2, §5.3, §6

## See it yourself

**The correctness suite is the real check here.** It compares each algorithm against its published formula, with every expected value worked out independently rather than by running the code:

```bash
./.venv/bin/pytest tests/test_correctness.py -v
```

Read the test names as they scroll. They tell you exactly what is covered.

**Then check the mechanisms are actually running:**

```bash
./.venv/bin/python scripts/trust_report.py
```

## What you should see

From the correctness suite: thirty checks, all passing, with names that describe real properties — A\* against exhaustive enumeration, ACO's choice frequencies against the normalised formula, evaporation as exactly `tau × (1 − rho)`, deposit landing on exactly the best path's roads, PSO's decoding against an independent greedy walk.

From the trust report: three columns per mechanism — what was measured, whether it is live, **and what that number reads when the mechanism is deliberately broken.** That third column is what lets you calibrate it rather than take it on faith.

```
ACO
  trail slots whose value moved          1,470      28   live  0 — table frozen
  trail mass removed by evaporation      345.3   3.767   live  0.00 — evaporation off
  slots the best ant reinforced            434     165   live  0 — deposit silent
  slots the MAX-MIN clip actually moved  1,470   2.19e+04  live  0 — bounds removed
```

**Read the report's front page.** It states plainly that it proves things **ran**, not that they ran **correctly** — and lists each probe's blind spots underneath it. That honesty is deliberate and it is worth quoting in your methodology.

**Wrong looks like:** any mechanism reading its "when broken" value during a normal run.

---

# Stop 6 — The controller **[after 21]**

## What happens

This is the project's contribution, and it is a small loop with three parts.

**Observation.** At each step, a structured snapshot of what this arm can legitimately know: how recently a disruption happened, how many events landed, what the current split is, how stagnant the ant colony is, how converged the swarm is, and three facts about the arm's own incumbent route — its cost, how that cost changed, and whether the route broke.

**The thing to notice is what is absent.** There is no field for "how far from optimal am I." An earlier draft had one, and it was removed, because excess is computed from the oracle's answer — and a policy that knows its own excess knows something no real routing system could know. A rule like *"explore harder when excess is high"* would be trained on the answer key. The three self-knowledge fields replace it.

**Policy.** Takes the observation, returns a target fraction. Three of them exist: one that never changes it (the ablation twin), one that moves it based on how recently disruption hit (the thesis), and one that follows a fixed timetable ignoring the world entirely.

That third one is the cleverest part of the design and it is worth understanding. If a blind timetable performs as well as the recency-driven policy, then **what helped was *varying* the split, not *sensing* when to vary it** — and the thesis would be wrong in a specific, interesting way. It is the honest control for the idea itself.

**Governor.** The only thing allowed to act. It clamps the proposal to a sane range, limits how fast it can move, and — importantly — **records what was proposed and what was applied separately.** A policy pushing hard against a limit and a policy proposing exactly the limit look identical in the applied series, and they mean opposite things about whether the policy is doing anything.

## Where it lives

`src/dynaswarm/allocation/observation.py`, `policies.py`, `governor.py`
`ARCHITECTURE.md` **§7.2 and §7.3** — read both; §7.3 defines what *recency* actually is

## See it yourself

**On the dashboard:** tick the adaptive hybrid, race, and watch the **allocation view**. The fraction should visibly move.

## What you should see

| Arm | What must be true |
|---|---|
| **Fixed / Static Hybrid** | the fraction is exactly 0.5 at every step — never moves |
| **Recency-Based Adaptive Hybrid** | the fraction **moves, and moves when disruption lands** |
| **Scheduled** | varies on a timetable, ignoring what happens |
| **ACO frozen ρ vs adaptive ρ** | the two produce *different* ρ trajectories |

**If the adaptive arm's fraction is flat, your thesis has nothing to report.** That is not a small bug — it is the difference between a result and a well-formatted null. It has happened before in this project: a controller that logged itself as active while varying nothing (defect **F7**), and the results were indistinguishable from the frozen arm.

**Wrong looks like:** the adaptive line sitting flat, or the frozen line wobbling.

---

# Stop 7 — Results land on disk

## What happens

Every run writes a directory. One row per arm per timestep, in Parquet, plus a separate table of events, plus the exact configuration that produced it.

**One column decides whether a number may appear in your report.** `run_class` is stamped on every run and takes one of three values:

| | |
|---|---|
| `manifest` | a run from the planned experiment set. **Reportable** |
| `exploratory` | a scratch run — anything from the dashboard, anything ad-hoc. **Never reportable** |
| `inversion` | a deliberate ablation |

Every run currently on disk is `exploratory`. The analysis layer filters to `manifest` by default, so a scratch run cannot drift into an aggregate by accident.

This is the system that protects your report from your own experiments, and it has already caught one real violation: a test fixture once stamped a run `manifest` and it landed in the live folder. The tests now write to a temporary directory and there is a check that the suite creates nothing under `outputs/`.

## Where it lives

`src/dynaswarm/io/schema.py` — every column, with types
`src/dynaswarm/io/writer.py` — the writer
`src/dynaswarm/analysis/load.py` — `load_steps()`, `load_events()`, and the default filter
`ARCHITECTURE.md` §12

## See it yourself

```bash
./.venv/bin/python -c "
from pathlib import Path
from dynaswarm.analysis.load import load_steps
f = load_steps(Path('outputs'), run_class=None)
print(f['run_class'].value_counts())
print()
print(sorted(f.columns))
"
```

## What you should see

Every run classed `exploratory`, and **no `manifest` runs at all** until Phase 4 produces them.

The columns are worth reading once, because they are what your report is built from:

`optimum` (A\*'s answer), `best_cost` (this arm's answer), `excess` (the headline metric), `path_valid`, `path_len`, `evaluations_spent`, `num_events`, `signal_value`, `params`, `probe`.

**Wrong looks like:** a `manifest` run appearing that you did not deliberately create. That means something can promote scratch work to evidence.

---

# Stop 8 — The numbers

## What happens

**Excess is the headline.** For an arm at a timestep: `best_cost / optimum − 1`. Zero means you found the perfect route. 0.03 means you are 3% worse. Because the optimum is recomputed every step, this is excess over a *moving* target — which is the whole point.

**Recovery metrics describe what happens around a disruption.** How much worse the arm got when the break landed (*damage*), how long until it settled again (*recovery time*), and where it settled (*settled excess*). An arm that never gets much worse and an arm that recovers fast are different virtues, and the mean excess alone hides both.

**Then statistics, and the protocol matters.** Arms are compared **pairwise on the same trials** — same seed, same graph, same timeline — so a paired test is the right one. Wilcoxon signed-rank, because excess distributions are not normal. Then **Holm correction**, because comparing several arms means several tests, and without correction some of them are significant by chance alone. And **Cliff's delta** alongside the p-value, because with enough trials almost anything becomes statistically significant and you need to know whether the difference is *large*.

A p-value says *"this is unlikely to be luck."* Cliff's delta says *"and here is how much it actually matters."* Report both.

## Where it lives

`src/dynaswarm/analysis/recovery.py` — `disruptions()`, `per_trial_recovery()`
`src/dynaswarm/analysis/stats.py` — `paired_compare()`, `holm_correct()`, `cliffs_delta()`, `compare_arms()`
`ARCHITECTURE.md` §11.1 – §11.4

## See it yourself

```bash
sed -n '60,100p' src/dynaswarm/analysis/stats.py
```

Read `cliffs_delta` and its thresholds. It is short, and knowing what counts as "large" is the kind of thing you get asked.

## What you should see

Excess values that are plausible: A\* exactly 0, ACO and the Hybrid a few percent, PSO higher. Recovery metrics that are **not** all zero — a column of identical zeros was defect **F5**, a dead instrument reporting a flattering number nobody interrogated.

**Wrong looks like:** every recovery figure identical. That is not a result, that is a broken measurement.

---

# Stop 9 — The dashboard

## What happens

It is a **view**, never a second engine. It imports the core as a library and asks it questions; it computes nothing of its own. The direction of that dependency is enforced — the core does not know the dashboard exists — and it is tested, because the previous version of this project died of instrumentation that looked fine and quietly disagreed with the thing it was instrumenting.

```bash
./.venv/bin/python -m dashboard.server
# then open http://127.0.0.1:8000
```

## The three buttons, in order

**Generate** builds the world. **Build** freezes the disruption timeline — all sixty steps, decided now. **Race** runs one real trial through the same function the command line uses, and writes a normal run directory.

Then everything is replay. Scrubbing, playing, stepping — all lookups into results that already exist. **Nothing computes while you watch.** That is deliberate: every arm must face byte-identical disruptions, so the timeline is frozen before any algorithm starts.

## What each line means

| Line | Meaning |
|---|---|
| faint grey | untouched road |
| orange | got slower — **still usable** |
| teal | got faster — still usable |
| green | new road appeared |
| green dashed | reopened |
| red dashed | closed |
| dark red, faint | removed permanently |
| **blue, thickest** | the current cheapest route |

**Two layers, not one.** A road's *price* is a state that persists — it stays visible for as long as it is true. A road *breaking* is an event that flashes and fades. Those were once painted in the same channel, which is why the screen turned to mud by step 59.

**And the fade is your recency signal.** Events decay at `0.7 ** age` — the identical curve the allocation controller reads. When you watch a flare fade, you are watching the number the algorithm makes its decision from.

## See it yourself — the full pass

| Do this | You should see |
|---|---|
| Press **Run the demo** | Builds, breaks, races, then stops on each step where the optimum moves |
| Drag the slider to **t=0** | `best route 99.96`, 11 hops |
| Drag to **t=21** | `110.54`, hops 11 → 12, **and the blue line visibly changes shape** |
| Drag to **t=57** | back to `103.25`, 11 hops — a recovery |
| Press **→** once from a break | red lines turn orange — red is *just now*, orange is *earlier* |
| Scrub end to end slowly | **no grey dot ever moves.** Places do not move; only roads change |
| Arrow-key to t=21, note the numbers; then drag the slider to t=21 | identical. If they differ by one step, that is an off-by-one |
| Look at the blue route anywhere | it must **never** pass through a **red dashed** road. Orange and teal are fine — a slower road can still be the best one |
| Click any road | price now, price at t=0, whether it is open, whether it is original or new, and every event that touched it |
| Click any place | degree, position, and which algorithms route through it |
| Compare the **A\*** pane's cost to the headline `best route` | they must match **to the digit** |
| Watch the **edge ledger** the whole time | always **balances** |

## What wrong looks like

Any of these means the picture and the engine disagree, which is the failure this project was built to prevent:

- the blue route crossing a closed road
- the ledger saying DIVERGED
- the A\* pane and the headline disagreeing
- a pane drawing a route that stops short but does not read as broken
- a dot moving as you scrub

---

# Part 10 — Break it on purpose

Everything above checks that the system behaves. **This checks that you understand it** — and it is the strongest verification available, because it is the only one that tests your model of the system rather than the system itself.

For each: read the prediction, decide whether you agree, then do it.

### 1. Nothing ever breaks

Set the disruption preset to **Calm** and Race.

**Predict:** the optimum is identical at every step. Every arm's excess settles and stops moving. The ledger never changes. "Broke this step" is 0 for all sixty steps.

**If instead** the optimum moves, something is generating events when it should not.

### 2. Break everything

Set **Severe**, `roads per break` to 40, and Race.

**Predict:** the optimum jumps around. Excess for ACO and PSO gets much worse. And **most importantly** — if an arm fails to find any route at all, its pane goes visibly broken rather than drawing a shorter line that reaches nowhere.

**If instead** a pane draws a short line that stops in the middle of the map as though that were a route, the display is lying about a failure.

### 3. A different world

Change the seed. Race.

**Predict:** completely different map, completely different breaks, different numbers throughout. The ledger still balances. A\*'s pane still matches the headline.

**The point:** nothing should be hard-coded to one seed. Every invariant must hold on a world nobody designed.

### 4. The same world, twice

Set the seed back. Race again.

**Predict:** identical numbers, to the last digit. Then quit the server entirely, restart it, and do it once more. **Still identical.**

**If instead** it differs across restarts, some randomness is not seeded and no result in your report is reproducible.

### 5. Kill a mechanism

```bash
./.venv/bin/python scripts/trust_report.py
```

Note ACO's four numbers. Now open `src/dynaswarm/optimizers/aco.py`, find `_evaporate`, and comment out the line that shrinks the trails. Re-run the report.

**Predict:** `trail mass removed by evaporation` reads **0.00** and the report says so. ACO's excess gets worse.

**Then put it back** — `git checkout src/dynaswarm/optimizers/aco.py`.

**The point:** you have now seen the instrument report a failure. From here on, when it says *live*, you know what that word cost.

### 6. The extremes

Try: 4 places · 1 timestep · `large1000` · a budget of 1 evaluation.

**Predict:** it either works or fails with a clear message.

**If instead** it produces a confident-looking answer at 4 places with a 1-evaluation budget, ask yourself where that answer came from. **Confident nonsense is more dangerous than a crash.**

### 7. The thesis itself **[after 21]**

Race the **New Recency-Based Adaptive Hybrid** alongside the **Fixed / Static Hybrid** and watch the allocation view.

> **This exercise predicted the wrong behaviour until segment X**, and the old prediction is worth knowing because it is the intuitive one. It said the fraction "jumps when a disruption lands, and **drifts back during calm**" — a mean-reverting controller, returning to where it started. This one does not mean-revert. It ratchets: each disruption moves it down and calm does not undo that. Measured over eight runs (two horizons × four seeds), it ended **below** its start every single time.
>
> The distinction is not cosmetic. A mutation that makes the arm mean-revert — tested in segment X — passes all 486 tests **and makes the recency correlation look stronger**, while reallocating nothing on net. If you see the old prediction's behaviour, that is the failure, not the success.

**Predict, concretely:**

- The Fixed / Static Hybrid sits at **exactly 0.5** for the whole run. One value, no movement.
- The adaptive one starts at 0.5 and walks **downward**, toward PSO. Over 40–60 steps it ends somewhere around **0.39–0.49** — a gentle staircase, not a sawtooth.
- Each step where roads break moves it down by **one full step of 0.006**. That figure is exact and does not vary with the seed.
- Between disruptions it moves **very little** — a tenth of that or less. Sometimes slightly up, sometimes slightly down; the direction in calm is not stable and is not meant to be. What matters is that calm movement is **much smaller** than disrupted movement, roughly 5–15× smaller.

**What a real failure looks like:**

- **The Fixed hybrid is not at exactly 0.5.** It has acquired an allocation policy it must not have.
- **The adaptive line is genuinely flat** — one distinct value for the whole run. Nothing is driving it. This is what F7 did, and it makes every later number meaningless.
- **The line oscillates around 0.5 and ends where it started.** It is moving as much in calm as under disruption. It is varying on the clock rather than on the signal — which correlates with recency just as well and allocates nothing.
- **The line is identical in a calm world and a violent one.** Then it is not reading the signal at all. (The *Scheduled* Hybrid is *supposed* to do this — it is the open-loop control. The adaptive one is not.)

**What is small-but-working, and is NOT a failure to report:**

- A total travel of only a few hundredths over the run. The step is 0.006 and there are ~15 disrupted steps in 60 at the moderate preset, so a few hundredths is the arithmetic working, not the mechanism failing. On screen it is a shallow slope. **Zoom before concluding it is flat** — the chart's axis is fixed to 0–1 deliberately, so a real 0.06 move looks small, and an auto-scaled axis that made it look dramatic would be the chart overstating the evidence.
- The three hybrids finishing at similar excess. At the time of writing, the allocation changes the *search* (routes differ on roughly half the steps) but whether it changes the *outcome* is not yet established — see segment X's findings. A small or absent excess difference is a real result, not a broken run.

**Check the number, not the picture.** In the per-step panel, `asked` and `allowed` should agree (the governor only holds a proposal back if it exceeds 0.05 in one step, which this policy never does), and `at a bound` should read `no` throughout.

---

# Part 11 — Every number, decoded

You will see a lot of figures. Here is what each one is, and what a healthy value looks like.

## On the dashboard — the stat bar

| Field | What it is | Healthy |
|---|---|---|
| **timestep** | which step of the frozen timeline you are looking at | `t / horizon−1`, e.g. `14 / 59` |
| **best route** | A\*'s exact cheapest cost right now. **The answer key** | moves a handful of times across a run |
| **hops** | how many roads that route uses | 10–14 on `medium200` |
| **roads open** | how many roads exist *right now* | starts at 735, moves as roads close and appear |
| **broke this step** | how many roads an event touched at this step | 0 on most steps, ~25 when a cluster lands |

**The single most informative thing on this bar** is that *broke this step* can read 25 while *best route* does not move at all. That is disruption landing away from your route — and it is why the project measures how *recently* something broke rather than how *much* broke.

## On the dashboard — the world panel

| Field | What it is |
|---|---|
| **places** | junctions. Never changes during a run |
| **roads** | roads at `t = 0`, before anything breaks |
| **roads per place** | mean degree. Around 7 on the default. Under 3 and the graph falls apart when hit; over 20 and nothing you break matters |
| **shortest route** | the optimum at `t = 0` — the number everything is measured against before anything happens |

## On the dashboard — the edge ledger

`initial + added + reopened − closed − deleted = current`

This is an **exact identity**, not an approximation, because the population of slots is closed. Six numbers and a verdict.

| Verdict | Means |
|---|---|
| **balances** | the ledger's arithmetic matches the engine's own count of open roads |
| **DIVERGED** | it does not. **Stop and tell me** — the picture and the engine disagree about what exists |

Crucially the check is against **the engine's count**, not the ledger's own sum. A ledger that only agrees with itself proves nothing.

## On the dashboard — each algorithm's pane

| Field | What it is | Healthy |
|---|---|---|
| **name** | the display name — *A\**, *ACO standalone*, *PSO standalone*, *Hybrid (baseline)* | never a code id like `erdos_renyi` |
| **cost** | this arm's current best route cost | A\*'s **must equal the headline `best route` exactly** |
| **hops** | roads in that route | |
| **+%** | excess — how much worse than perfect | A\* `+0.0%` always · ACO and Hybrid low single digits · PSO higher |

**A\* at anything other than `+0.0%` is impossible by construction.** If you ever see it, the measurement is broken, not the algorithm.

## The trust report — what each row means

```
./.venv/bin/python scripts/trust_report.py
```

Three columns: **first** (the value early in the run), **last** (at the end), **when broken** (what that same number reads if the mechanism is deliberately disabled). That third column is the point — it is what lets you calibrate the other two instead of trusting them.

| Row | Reading it |
|---|---|
| **trail slots whose value moved** | pheromone is changing. `0` means a frozen table — ACO is doing a random walk |
| **trail mass removed by evaporation** | old preferences fading. `0.00` means no evaporation — ACO converges early and never re-explores |
| **slots the best ant reinforced** | deposit is happening. `0` means the winning route is not being remembered |
| **slots the MAX–MIN clip actually moved** | the bounds are binding. `0` means it is plain Ant System, not the MAX–MIN version your report names |
| **particles the flight step displaced** | the swarm is moving. `0` means it is frozen |
| **mean velocity** | how fast. Falls over a run — that is convergence. **Falling to ~1e-14 was defect F13** |
| **budget share ACO actually spent** | measured from real spend, not from what was requested. `0.5` flat today |
| **exchanges that fired** | the two halves are talking. `0` means the Hybrid is two solvers in one process |

**Read the report's front page before the numbers.** It states outright that it proves things **ran**, not that they ran **correctly**, and lists each probe's blind spots beneath it. That honesty is the reason the rest is worth anything.

## In the results file

`outputs/<date>/<time>/steps.parquet` — one row per arm per timestep.

| Column | What it is |
|---|---|
| `optimum` | A\*'s exact answer at that step |
| `best_cost` | this arm's answer |
| `excess` | `best_cost / optimum − 1`. **The headline metric** |
| `path_valid` | did this arm actually have a working route? |
| `path_len` | hops |
| `num_events` | roads touched at that step |
| `evaluations_spent` | the fairness currency — **must be the same for every metered arm** |
| `run_class` | `exploratory` / `manifest` / `inversion`. **Decides whether it may be reported** |
| `params` | the arm's live parameter vector |
| `probe` | the mechanism telemetry from the trust report |
| `signal_value` | what the controller's signal read |

## The statistics

| Number | What it means | How to read it |
|---|---|---|
| **`n_pairs`** | trials contributing to both arms | fewer than ~20 and the test is weak whatever it says |
| **`mean_a`, `mean_b`** | mean excess for each arm | |
| **`delta`** | `mean_a − mean_b`. **Negative favours the first arm**, since lower excess is better | the size of the difference, in real units |
| **`p_value`** | raw Wilcoxon signed-rank, two-sided | *"how unlikely is this by chance"* |
| **`p_adjusted`** | after Holm correction across the family | **use this one**, not the raw. Comparing several arms means several chances to get lucky |
| **`effect`** | Cliff's delta, −1 to +1 | *"how much does it actually matter"* |
| **`effect_label`** | the word for that size | |
| **`significant`** | passed the corrected threshold | |

**Cliff's delta thresholds**, read straight from `stats.py`:

| |Δ| | Label |
|---|---|
| < 0.147 | negligible |
| < 0.33 | small |
| < 0.474 | medium |
| ≥ 0.474 | large |

**Always report both `p_adjusted` and `effect`.** With enough trials nearly anything becomes statistically significant — a p-value says *not luck*, Cliff's delta says *and here is whether it matters*. A result that is significant and negligible is a true finding about a difference nobody would care about, and saying so is stronger than hiding it.

## The recovery metrics

| Field | What it is |
|---|---|
| `timestep` | when the disruption landed |
| `baseline` | mean excess over the calm steps before it |
| `damage` | worst excess after it, minus the baseline. **Can be negative** — an event can open a *shorter* route, and that is real, not an error |
| `recovery` | steps until excess came back within the band, or **`None`** if it never did by the end |

`recovery = None` is not a missing value. It means the arm **never recovered**, and it is a finding.

---

# Part 12 — The combination sweep

Part 10 tests whether you understand the system. **This tests whether it holds together across the space you can actually reach from the interface.**

No sweep is exhaustive — there are four models × four size presets × four scenarios × free-form numbers, and you cannot try all of them. So this is chosen coverage, not brute force: the combinations where something plausibly breaks.

Run each, and for each one confirm the **three universal invariants** hold:

> **(a)** the ledger balances · **(b)** A\*'s pane matches the headline · **(c)** the blue route never crosses a closed road

### The four models

| Setting | Expect |
|---|---|
| **Map-based** (geometric) | draws, roads connect near neighbours, looks like a map |
| **Street grid** | draws, regular lattice. **`how connected` is ignored** — the lattice fixes it |
| **Random · no map** | **refuses to draw**, with a message saying why. This is correct, not a bug |
| **Custom** with your own numbers | whatever you set, and the panel figures must match what you typed |

### The four size presets

| Setting | Expect |
|---|---|
| Small · 30 places | works, but it is Erdős–Rényi — so it refuses to draw. Numbers still correct |
| Medium · 200 | the research tier. Everything works |
| Large · 1,000 | works, slower. **Note how long Race takes** — this matters for Phase 4 planning |
| Grid · 400 | draws as a lattice |

### The four disruption scenarios

| Setting | Expect |
|---|---|
| Calm | optimum never moves, ledger never changes, every arm settles |
| Light | a break roughly every ten steps |
| Moderate | the default — about three in four steps quiet |
| Severe | roughly every other step. **The most likely place to see an arm fail to find a route** |

### The edges of the numeric fields

Each of these is a place where a system either fails cleanly or produces confident nonsense. **The second is the dangerous one.**

| Set | Expect |
|---|---|
| places = 4 (minimum) | works or refuses clearly. A 4-place "shortest route" should be checkable by eye |
| how connected = 0.005 | very sparse. Likely disconnected — it should **say so**, not invent a route |
| how connected = 1.0 | everything connects to everything. Route should be 1–2 hops |
| how long = 1 | a single timestep. No disruption can have happened yet |
| how long = 500 | slow, but the ledger must still balance at step 499 |
| breaks per step = 0 | identical to Calm |
| roads per break = 1 | single-road breaks. **Predict:** the optimum almost never moves — this is exactly the finding that motivated clustering |
| roads per break = 100 | huge neighbourhoods gone. Arms should fail visibly, not quietly |

### Sequence robustness

Interfaces break on *order*, not just values. Try these deliberately:

| Do | Expect |
|---|---|
| Press **Race** before **Build** | refuses or tells you, rather than racing on nothing |
| Press **Build** before **Generate** | same |
| **Generate** a new world *after* racing | the panes and the shared-timeline line should reflect the **raced** world, not the new form values — the two visibly disagree rather than silently agreeing |
| Double-click **Race** fast | the second click does nothing while the first runs |
| Scrub while it is still racing | controls are locked, or it behaves sanely |
| Reload the page mid-run | opens empty, no half-state |

### Timing — write these down

| Configuration | Seconds for one Race |
|---|---|
| medium200, moderate, 60 steps | |
| large1000, moderate, 60 steps | |
| medium200, severe, 500 steps | |

**This matters.** Phase 4 runs 100 trials × 8 arms × several scenarios. If one race is 2 seconds you are fine; if it is 30 at the research tier you are looking at many hours, and you need to know that **before** you start it rather than four hours in.

---

# Appendix — the one-page checklist

**Commands**

```bash
./.venv/bin/pytest                          # everything
./.venv/bin/pytest tests/test_correctness.py -v   # algorithms vs their formulas
./.venv/bin/python scripts/trust_report.py  # mechanisms live or inert
./.venv/bin/python -m dynaswarm.cli         # one real run
./.venv/bin/python -m dashboard.server      # the dashboard
./.venv/bin/ruff check src/ tests/ dashboard/ scripts/
```

**Must be true, every time**

- [ ] the edge ledger balances at every step
- [ ] A\*'s pane cost equals the headline optimum, to the digit
- [ ] the blue route never crosses a closed road
- [ ] no place ever moves as you scrub
- [ ] same seed → identical numbers, across process restarts
- [ ] every run on disk is `exploratory`
- [ ] recovery metrics are not all zero
- [ ] the arrow keys and the slider agree about which step you are on
- [ ] **[after 21]** the adaptive fraction moves; the frozen one does not

**Where to read**

| Question | File |
|---|---|
| How is the graph built? | `core/generate.py` |
| What can happen to a road? | `core/events.py` |
| When do events apply? | `core/timeline.py` — and `ARCHITECTURE.md` §4.4 |
| What does one run actually do? | `harness/trial.py` |
| How does each algorithm work? | `optimizers/` |
| How is the split decided? | `allocation/` — and §7.2 |
| What lands on disk? | `io/schema.py` |
| How are the numbers compared? | `analysis/stats.py` |
| Every decision and why | `decisionLedger.md`, `WORKFLOW_LOG.md` |

---

## If something here is wrong

This file describes what the system is supposed to do. If it does something else, **one of the two is wrong and both matter.** Write down what you did, what you expected, and what happened — and bring it back. A walkthrough that quietly drifts from the code is worse than none, because it manufactures confidence.
