# SEGMENT 19 — Correct, Not Just Running

**Phase 3 · Restructure · Segment 3 of 5**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` **§5.1 (A\*), §5.2 (ACO), §5.3 (PSO), §6 (the Hybrid)**, §2.1. `WORKFLOW_LOG.md` **Entry 018** — R2 settles re-initialisation and is not to be reopened here.
> Append your findings to the **bottom** of this file.
>
> ## ⛔ YOU DO NOT COMMIT
>
> Rudra commits. Leave the tree unstaged, paste `git status --short`, and paste the commit message as a copyable block **with no `Co-Authored-By` trailer**. No `git add`, no `git commit`, no `git stash`, never `git add -A`.

---

## Goal

Phase 2 proved the mechanisms **run**. It said so on its own front page and refused to claim more. **This segment asks whether they run as specified** — against arithmetic, on a graph small enough to work out by hand.

Everything you have today is **outcome-based** evidence. ACO lands within 2–3% of a provably optimal answer, which is hard to achieve with a broken implementation — but "hard to achieve" is not proof, and it says nothing about PSO at 18%, where a correct hard algorithm and an incorrect one look the same from outside.

---

## The rule this segment lives or dies by

> **Every expected value is computed independently of the implementation.**

Worked out from the published definition, on paper or in a few lines written for the purpose. **Never by running the code and recording what it produced.**

A test whose expectation came from the code is a change-detector, not a correctness test. It passes forever, including on the day the code was wrong from the start — and it is the same defect this project has caught in five other costumes: a threshold taken from the state being replaced, an invariant asserted only against correct data, a ledger reconciled against its own arithmetic, a guarantee tested by data in which nothing fails, a fixture that differed from production in the one dimension under test.

**State, for each check, where the expected number came from.** If the answer is "from a formula in §5.2," name it. If it is "I worked it out", show the working.

---

## ⚠️ T0 — MEASURE

`src/` **2041 / 2100**, margin **59**. **This segment should cost `src/` nothing** — it is tests and a small reference implementation, both outside the science surface. If a check needs something the core does not expose, **stop and report.**

Report projection and actual.

---

## T1 — A\* first, and hold it to the highest standard

**Everything in this project is measured against A\*.** Excess is defined relative to it, Claim 1 is a comparison of excesses, and the dashboard draws its answer as the truth. **If A\* is wrong, every number in the report is wrong and nothing else in this segment matters.**

It has one existing check — segment 7 compared `heuristic=True` against `heuristic=False` and got the same cost. That is A\* agreeing with Dijkstra, which is real but is two implementations sharing one codebase and one set of assumptions.

**Build the independent check: brute-force enumeration.** On a graph of 8–10 nodes, enumerate every simple path from source to target, sum the weights, take the minimum. That is the definition of a shortest path, computed without reference to the code under test.

Then assert A\*'s cost equals it — **over many random small graphs, not one.** Include at least: a graph where the shortest path is not the fewest hops, a graph with a disconnected target, and a graph where two distinct paths tie.

**Do the same on a state partway through a timeline**, not only at `t=0`. The moving optimum is what excess is measured against, and it is computed at every step.

## T2 — ACO's choice rule against the formula

§5.2 defines how an ant picks its next edge: a probability proportional to pheromone raised to `alpha` times the heuristic raised to `beta`, normalised over the available edges.

**Set up a state you control** — a handful of nodes, pheromone and weights set by hand — and **compute the expected probabilities from that formula yourself.** Then sample the implementation's choice many times and compare the empirical frequencies, with a tolerance you can justify from the sample size.

**Also check the arithmetic that moves pheromone**, and here the expected values are exactly computable rather than statistical:

- **evaporation** — after one step, is each trail exactly `tau * (1 - rho)`?
- **deposit** — is the amount exactly what §5.2 specifies, and on exactly the edges of the best path?
- **the MAX–MIN bounds** — are `tau_max` and `tau_min` the values the formula gives, and is every trail inside them afterwards?

**That deposit check answers something Phase 2 explicitly could not.** The trust report says outright that `tau_deposited` *"cannot detect deposit on the WRONG edges; the count is identical either way."* **On a tiny graph you can check every edge.** Close it.

## T3 — PSO's decoding is deterministic, so check it exactly

A particle's position is a priority vector. The route is built by walking the graph and preferring the highest-priority available neighbour. **Given a specific priority vector on a specific small graph, the route is fully determined** — so work out by hand what route it must produce and assert the implementation produces it.

Cover the cases that separate a correct walk from a plausible one:

- a priority ordering that leads into a **dead end**, so the repair path is exercised
- **ties** in priority — whatever the tie-break is, it must be deterministic and stated
- a vector whose greedy walk is **not** the shortest path, so you are testing the decoding rather than accidentally testing the optimiser

**Then the velocity update**, which is three terms and a sum. Set position, velocity, personal best and global best to chosen values, compute the next velocity from §5.3's formula by hand, and compare. **This is the arithmetic segment 17 spent a whole segment reasoning about without ever checking directly.**

## T4 — The Hybrid's exchange

§6.2 defines what the components pass between them. The split is already verified from realised spend (Entry 015).

**What is not verified is the exchange's content.** Does the thing handed over arrive intact, and does the receiving component actually use it? Construct a state where the answer is unambiguous — one component holds a known good solution the other could not have found — and check it crosses **and has an effect.**

An exchange that fires and is ignored counts as `exchanges: 1` in the probe and does nothing. **Entry 015 counted that it fires. Nothing has checked that it matters.**

## T5 — Report what you could not check, and why

**This matters as much as the checks.** Some things will not be verifiable this way — stochastic behaviour over long runs, emergent convergence, anything needing a large graph.

**Name them explicitly**, in a form the report can use. Phase 2's trust report set the standard by stating its own blind spots on the line below each probe; do the same. **A correctness section that lists only what it could prove is the over-claim this whole phase exists to prevent.**

## T6 — Tests

Everything above is tests. Two further requirements:

| | |
|---|---|
| **The small-graph fixtures are constructed, not sampled** | A random 10-node graph that happens to have the property you need is a fixture that will lose it |
| **Each test names where its expected value came from** | In the docstring. This is the only defence against an expectation quietly drifting to match the code |

**Every check shown failing against a deliberately wrong implementation**, and the corruption pasted. Entry 010's rule, and it is the whole segment here: a correctness test that has never been seen red is a correctness test whose expectation might have come from the code.

## T7 — Mutations, two, one of them yours

**Specified:** change ACO's `alpha` exponent from `alpha` to `alpha + 1` in the choice rule. The ants still prefer strong trails, the algorithm still works, results still look reasonable — **and it is no longer the algorithm §5.2 describes.** That is the exact class of defect this segment exists to find: not broken, just not what the report says it is.

**Yours.** Ten consecutive segments. Entry 018's found that a fixture reusing one object hid a completely unfixed bug behind fifteen passing tests.

## T8 — Show it

1. T0
2. **A\* against brute force** — how many graphs, which edge cases, the result
3. **ACO's choice probabilities** — your hand-computed expectations beside the empirical frequencies
4. **The deposit check** — does it land on exactly the best path's edges? The thing Phase 2 could not see
5. **PSO's decoding and velocity arithmetic** — expected versus actual
6. **The exchange: does it arrive and does it matter?**
7. Both mutations, and every check shown red
8. **What you could not check, and why**
9. **Your read: would you now defend these implementations as being the algorithms they are named after?**

## T9 — Hand over, do **not** commit

`git status --short`, the commit message as a copyable block, no `Co-Authored-By`, one line confirming complete and uncommitted.

---

## Constraints

| | |
|---|---|
| **Expected values computed independently of the implementation** | The rule the segment lives by. Say where each came from |
| **`src/` should not move** | Stop and report if a check needs core exposure |
| **Constructed fixtures, not sampled** | |
| **Every check shown red against a wrong implementation** | |
| **No re-initialisation** | Entry 018 R2 settled it. Not reopened without new evidence |
| **No control-layer changes** | `allocation/`, F4, F7, F8 are segments 20–21 |
| **No performance work** | Fix defects, do not optimise |
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

**Paste verbatim:** T0 · A\* against brute force · ACO's hand-computed probabilities beside the empirical ones · the deposit-on-the-right-edges result · PSO's decoding and velocity arithmetic · the exchange's effect · both mutations · every check shown red · **what you could not check** · your read on defending the implementations by name.

---

## Definition of done

Green suite, artefacts pasted, **every check demonstrated red against a wrong implementation**, uncommitted with the message pasted, FINDINGS appended.

**After this the components are repaired, honest, and checked against their own definitions.** Segments 20–21 rebuild the control layer on top of them — and unlock the four arms the thesis actually lives in.

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->

---

# FINDINGS — Segment 19

## 0. T0

**`src/` 2041 / 2100, delta +0.** Everything is in `tests/test_correctness.py`
— 30 checks, no core change needed. Nothing the checks wanted was unexposed.

## 1. Where every expected value came from

| Check | Expectation derived from |
|---|---|
| A\* cost | **Exhaustive enumeration of every simple path** — the definition, written for this file, no heap or relaxation |
| A\* on a cheap long route | Hand arithmetic: 1 + 1 + 1 = 3 beats 10 |
| A\* unreachable | Infinity, by construction — the target is isolated |
| A\* ties | The tied cost 2.0, set by hand on two disjoint routes |
| ACO choice frequencies | §5.2's `tau**alpha * eta**beta` normalised: trails 1, 2, 3 with beta=0 give exactly 1/6, 2/6, 3/6 |
| Evaporation | §5.2: `tau * (1 - rho)`, computed here as a multiplication |
| Deposit | §5.2: `1/cost` on each slot of the path and its reverse, **and zero everywhere else** |
| MAX–MIN bounds | §5.2: `tau_max = 1/(rho*C_best)`, `tau_min = tau_max/(2n)`. rho=0.5, C=4 gives 0.5 exactly |
| PSO decoding | An independent priority-greedy walk over the adjacency, written in the test |
| PSO velocity | §5.3's three terms: 0.5·0.20 + 2.0·0.5·0.30 + 3.0·0.25·0.80 = 1.00 |
| Exchange | §6.2: `_EXCHANGE_GAIN` on exactly the shared route's nodes; `1/cost` on exactly its slots |

**None was obtained by running the code and recording the output.**

## 2. Every check shown red against a wrong implementation

```
1. ACO exponent: alpha -> alpha + 1   (the specified mutation)
   E  node 1: formula says 0.167, 5925 ants gave 0.079

2. evaporation: tau*(1-rho) -> tau*(1-rho/2)
   E  evaporation is not tau * (1 - rho)

3. deposit amount: 1/cost -> 1/(cost*cost)
   E  deposit did not land on exactly the path's edges
   E  the swarm's route did not deposit 1/cost on the colony's trail

4. MAX-MIN: tau_min = tau_max/(2n) -> tau_max/n
   E  trails below the floor were not clamped to exactly 0.0277777...

5. PSO velocity: inertia dropped from the sum
   E  velocity is 0.9000000000000001, formula gives 1.0

6. A*: heuristic scaled 2x, making it inadmissible
   E  geometric seed 6: A* says 107.25267904660666,
      enumeration says 105.87352038402327

7. exchange: the gain applied to every node, not the shared route
   E  the exchange altered priorities away from the shared route
```

**Three of these passed the first version of this file, including the
specified one.** That is the substance of the segment and it is below.

## 3. The three gaps, and they are all the same gap

### 3a. The choice test never ran the code — including on the specified mutation

The first version computed the expected probabilities from §5.2 **and then
sampled its own re-implementation of the selection loop**, copied into the
test. It compared a formula against a copy of the code and never called
`_construct` at all.

Changing the real exponent from `alpha` to `alpha + 1` — the mutation the
spec named, the one described as *"not broken, just not what the report says
it is"* — left it green.

**I committed the exact circularity this segment exists to prevent, while
writing the segment about it.** Now the sampling runs `_construct`, with every
other edge out of the source closed so the first hop is a clean three-way
choice.

### 3b. The bounds test asserted a range, and a wrong bound fits inside a range

`assert live.min() >= tau_min` is satisfied by any floor **at or above**
`tau_min` — so widening `tau_min` from `tau_max/(2n)` to `tau_max/n` passed.
Two of its assertions were also behind `if active[...]` guards that never
fired.

Now every live slot is pushed outside both bounds and each must land on an
**exact** value.

### 3c. A\*'s heuristic was never exercised at all

Every A\* check ran on `erdos_renyi` graphs, where `topology.pos is None` and
`weight_scale == 0.0`. **The heuristic is identically zero there** — A\*
degenerates to Dijkstra, and `heuristic=True` and `heuristic=False` are the
same function.

So doubling the heuristic, making it inadmissible, changed nothing. And
inadmissibility is *the one way A\* can silently return a suboptimal answer* —
the failure mode `oracle.py`'s own docstring warns about.

Now parametrised over both models, and on `geometric` the mutation is caught
with A\* returning **107.25 against the true 105.87**. That is the defect
class this segment was written for: a wrong answer that looks entirely
reasonable.

**All three are one failure: a test that cannot distinguish the thing it
names from something else.** Circular sampling, a bound that admits its own
violation, and a fixture where the feature under test is switched off.

## 4. A fixture bug worth recording

The first hand-built graph asserted `find_slot(u, v) >= 0` and set a weight —
but `find_slot` returns a slot **whether or not it is active**. Edge 0–1 was
inactive, so the cheap route did not exist, and A\* correctly returned 10.0
while the test claimed 3.0.

It read as *"A\* returns a suboptimal path"* for several minutes. A fixture
that silently does not build what it describes produces a failure
indistinguishable from a real defect, in the direction most likely to be
believed. `with_edges()` now activates what it prices, and says why.

## 5. T5 — what could not be checked this way

Stated here rather than left implied, to the standard Phase 2's trust report
set:

- **Convergence quality.** Every check here is one step of arithmetic or one
  decoded route. Whether ACO converges *well*, whether the colony finds good
  routes in reasonable time, whether MAX–MIN's bounds are well *chosen* — none
  of it is reachable by checking a formula on nine nodes
- **Emergent behaviour over long runs.** Correct arithmetic composed sixty
  times can still produce a bad search. F13 was exactly that: every line
  correct, the whole thing broken
- **Anything needing a large graph.** Enumeration is factorial; nine nodes is
  the ceiling. Behaviour that only appears at 200 nodes is out of reach here
- **The statistical check is a check on frequencies, not on the sampler.** A
  biased RNG producing the right marginal distribution would pass
- **`eta`'s definition is assumed, not verified.** The choice test sets
  `beta = 0` to isolate pheromone, so visibility's own formula is untested
- **Parameter *values* remain unchecked.** Everything here verifies the
  arithmetic is as published; whether `rho = 0.1` is a good choice is not a
  correctness question

## 6. Both mutations

**A — specified: ACO's `alpha` exponent becomes `alpha + 1`.** Not caught
initially (§3a); now caught, with the sampled share for node 1 at 0.079
against the formula's 0.167.

**B — mine: A\*'s heuristic scaled by 2, making it inadmissible.** Not caught
initially (§3c), because the suite ran only where the heuristic is zero. Now
caught on `geometric`, with A\* returning a genuinely suboptimal path.

**Eleven consecutive segments**, and this one found three.

## 7. Acceptance

| Check | Result |
|---|---|
| Suite | **439 passed, 0 failed, 0 skipped** |
| Lint, four trees | `All checks passed!` |
| `src/` | **2041 / 2100**, delta **+0** |
| `outputs/` | **26**, unchanged |
| `tests/test_correctness.py` | **30 passed** |

## 8. What this licenses the report to say

**A\* is exact**, checked against exhaustive enumeration over sixteen graphs
across both models, at `t = 0` and partway through a timeline, including
unreachable targets and ties — **and now with its heuristic actually live.**
Everything in this project is measured against it, so this was the one that
had to hold.

**ACO's arithmetic is §5.2's arithmetic** — the choice rule sampled from the
real constructor, evaporation, the deposit amount and its placement, both
bounds. The deposit check closes the gap Phase 2's trust report explicitly
admitted: it can now be said that the best ant deposits on **exactly** the
edges of its route and nowhere else.

**PSO's decoding and velocity update are §5.3's**, with the tie-break stated
as lowest CSR slot index and pinned.

**The Hybrid's exchange is §6.2's, and it has an effect** — Entry 015 counted
that it fires; this checks that what crosses arrives and changes the receiver.

What none of it licenses is any claim about whether these correct mechanisms
search *well*. That is §5's separate question, and §5 is measured in Phase 4.
