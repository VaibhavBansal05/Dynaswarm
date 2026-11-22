# dynaswarm

**ACO + PSO for shortest paths in changing road networks.**

Minor project · School of Computer Engineering, MIT Manipal (MAHE)
Vaibhav Krishna Bansal · Rudra Rajpurohit · Kartikey Goyal · Pavit Agrawal
Mentor: Mrs. Vidhya V

**Start with the results:** [FINDINGS_TESTS.md](FINDINGS_TESTS.md) is the reference for the completed evidence run. It records the run, verification checks, pre-registered comparisons, and figures re-derived from the raw trial rows. [ARCHITECTURE.md](ARCHITECTURE.md) describes the design; [decisionLedger.md](decisionLedger.md) records decisions and defects.

---

## What the 1,200-trial study found

The study paired **150 seeds × 4 road-disruption scenarios × 2 graph sizes** (200 and 1,000 nodes), with ten algorithm arms on the same changing worlds. It recorded **720,000 time-step rows**. Route quality is measured as excess cost above the true shortest path; **lower is better**. The [findings file](FINDINGS_TESTS.md) contains the run setup, verification checks, and pre-registered comparisons.

- **Combining ACO and PSO worked.** The plain 50/50 hybrid beat PSO in all four scenarios at both sizes. It beat ACO in all four scenarios at 1,000 nodes, and only under severe disruption at 200 nodes.
- **Adapting the ACO/PSO split did not deliver the hoped-for gain.** The recency-driven incremental split never significantly beat its fixed 50/50 twin. The direct-response split had one statistically significant win at 1,000 nodes under light disruption, but its effect size was negligible; there was no consistent, practically meaningful advantage from sensing. Under severe disruption, both sensing splits lost to a split that followed a timetable without sensing the roads, by statistically detectable but negligible effects.
- **Adapting ACO's evaporation rate showed no significant improvement** over its fixed counterpart in any of the eight size/scenario cells. The confidence interval in the hardest large-graph case is still wide enough to allow a benefit, so this is not proof that parameter adaptation can never help.

For a concrete comparison, on **1,000 nodes under severe disruption**, mean excess was 2.99% for the scheduled hybrid, 3.15% fixed, 3.24% direct, 3.27% incremental, 4.19% PSO, and 14.28% ACO. These are descriptive means for that setting; the paired tests above support the comparison claims. [Full results and limitations →](FINDINGS_TESTS.md)

## The question and the tested idea

When roads close, reopen, or change cost, should a hybrid give more of its fixed search budget to PSO immediately after a disruption, then return it to ACO as the colony's pheromone memory recovers?

That was the allocation hypothesis. The experiment tested a fixed 50/50 split, a split nudged by disruption recency, a split moved directly by recency, and a scheduled split that ignores disruptions. The negative result above is about **recency-driven allocation**: these policies detect *how recently* a road event happened, but do not use *how many* roads changed. A magnitude-aware policy remains a separate, untested question. See §12 of [FINDINGS_TESTS.md](FINDINGS_TESTS.md) for the source-level scope check.

Earlier exploratory work led from volatility-based tuning to the recency hypothesis. Those smaller runs are retained below as project history, with their original limitations; use [FINDINGS_TESTS.md](FINDINGS_TESTS.md) for result claims.

## Design commitments

Comparative studies of stochastic algorithms fail quietly. The result still looks like a number, so a broken comparison is indistinguishable from a real one unless the design makes the failure impossible or a test makes it loud. Five commitments, each enforced by a test rather than by discipline:

| Commitment | How it is enforced |
|---|---|
| **A sensing signal must span the range it is thresholded against.** A signal bounded far below its own decision boundary pins the controller in one regime forever. | Churn is a *fraction of edges*, so the edge-ratio signal means the same thing at any graph size. Every signal's dynamic range is asserted per scenario. |
| **Every tunable parameter must demonstrably change behaviour.** A parameter written to a registry but never read is indistinguishable from a tuned one in the logs. | `PARAM_SPEC` binding is total: a test sets each parameter to both bounds and requires the trajectories to differ. |
| **Every arm must see the identical world.** If one arm is evaluated before a disruption and another after, the comparison measures the schedule, not the algorithms. | The event schedule is materialised before any optimizer exists; `state_at(t)` is pure, and arms are checked to receive byte-identical states. |
| **Equal budget must mean equal work.** Equalising *iterations* lets an algorithm with a larger population buy itself CPU — and if population size is controller-tuned, the controller buys its own advantage. | Budget is denominated in candidate-path constructions and metered by the harness, not self-reported. |
| **An arm's randomness must depend only on itself.** Otherwise adding an arm silently rewrites another's results. | Streams are content-addressed by name; a test adds a third arm and requires the first two to be bit-identical. |

## Related work this builds on

- Stützle et al. find that a single well-chosen fixed parameter setting usually beats run-time variation, and that adaptation schemes are typically chosen without first studying what the parameters do. This project therefore treats a **best-fixed-parameter arm** as the opponent to beat, and compares sensing signals rather than assuming one.
- Mavrovouniotis & Yang adapt ACO's evaporation rate in dynamic routing using the **λ-branching factor** — an internal measure of colony stagnation — moved in small ±σ increments. Both choices are adopted here: no regime-preset tables, and internal sensing as a first-class alternative to environmental sensing.

## Earlier exploratory results

> **Historical, provisional measurements below.** These small runs predate the completed 1,200-trial study; their original output is not available here for verification. They document how the project developed, but should not be cited as current performance results. Use [FINDINGS_TESTS.md](FINDINGS_TESTS.md) for the verified comparison.

## The hybrid beats both of its components

The project's original goal, and the first positive result. Geometric n=200, paired over 10 trials, equal evaluation budget:

*(provisional historical result — see “Earlier exploratory results” above)*

| scenario | ACO | PSO | **Hybrid** | hybrid − ACO | Wilcoxon |
|---|---|---|---|---|---|
| moderate | 8.2% | 13.7% | **7.7%** | −0.5% | 0.625 |
| high | 9.3% | 26.8% | **7.1%** | **−2.3%** | **0.004** |

The advantage grows with disruption and is significant in the busier scenario, which is what the design predicts: the colony's pheromone is worth a great deal in the steady state but goes stale immediately after a closure, and the swarm — whose priorities rank nodes rather than edges — is unaffected by that staleness. The hybrid is a bet that one covers the other's failure window, not simply that two methods are better than one.

At the time, this ten-trial result motivated the allocation experiment (M7). The later 1,200-trial study found no meaningful improvement from shifting the split by *time since disruption*; see the current findings above.

## Why volatility-driven adaptation does not help

The result the harness was built to produce. On geometric n=200 — the tier where disabling pheromone costs +23 points, so the adapted mechanism is genuinely load-bearing — against a tuned baseline, paired over 16 trials:

*(provisional historical result — see “Earlier exploratory results” above)*

| signal | scenario | tuned fixed | adaptive | delta | Wilcoxon |
|---|---|---|---|---|---|
| edge_ratio | moderate | 4.28% | 4.32% | +0.04% | 0.893 |
| edge_ratio | high | 3.35% | 3.52% | +0.18% | 0.552 |
| volatility | moderate | 4.28% | 4.21% | −0.07% | 0.317 |
| volatility | high | 3.35% | 3.35% | +0.00% | — |
| lambda_branch | moderate | 4.28% | 4.22% | −0.06% | 0.859 |
| lambda_branch | high | 3.35% | 3.39% | +0.05% | 0.530 |

Smallest p is 0.317 against a Holm threshold of 0.0083 for six tests.

**And here is why.** Tuning separately for each volatility level, then evaluating every vector on every scenario (evaluation seeds, never seen by any tuning run):

*(provisional historical result — see “Earlier exploratory results” above)*

| tuned for ↓ / run on → | static | moderate | high |
|---|---|---|---|
| static | 3.23% | 4.28% | 3.48% |
| moderate | 2.99% | 4.09% | 5.16% |
| high | 3.23% | 4.28% | 3.48% |

The vector matched to a scenario never significantly beats a mismatched one — no comparison reaches p < 0.47, and twice the mismatched vector is numerically better. **The optimal parameters do not depend on volatility in any way we can measure**, so a volatility-driven controller has nothing to gain. The null results above are not a failure of the controller; they follow from the problem.

Two caveats stated plainly. Twelve trials cannot rule out small effects — the largest gap (1.68 points) still carries p = 0.47. And the static and high searches returned identical vectors partly because all three shared a sampler seed and so explored the same candidates; the cross-evaluation, not that coincidence, is the evidence.

## A signal's working range depends on the graph, not just the churn

`volatility` asks "did anything change this step?", so it saturates once events per step exceed a couple. Because events are driven at a fraction of |E|, that threshold arrives sooner on larger graphs:

*(provisional historical result — see “Earlier exploratory results” above)*

| | n=30 (\|E\|≈150) | n=200 (\|E\|≈1200) |
|---|---|---|
| static | 0.00 | 0.00 |
| moderate | 0.56 | **1.000** |
| high | 0.86 | **1.000** |

Pinned at 1.000, the signal has no gradient and the controller cannot move — measured, its arm came out bit-identical to the frozen twin. The gate that was supposed to catch this ran only at n=30, where volatility still discriminates. **A signal's usability is a property of the signal and the tier together.** There is now a test pinning the saturation, so recalibrating the tiers fails loudly rather than silently reviving a dead controller.

## Choosing a testbed that can show the effect

A null result means nothing if the mechanism under test does no work on the instances used. Disabling pheromone entirely (α = 0):

*(provisional historical result — see “Earlier exploratory results” above)*

| graph | with pheromone | without | delta | Wilcoxon |
|---|---|---|---|---|
| Erdős–Rényi n=30 | 0.91% | 0.75% | −0.15% | 0.910 |
| geometric n=200 | 8.25% | **23.88%** | **+15.63%** | **<0.001** |

**Pheromone does nothing at n=30 and almost everything at n=200.** A 30-node graph of mean degree 18 puts the target a hop or two from anywhere, so almost any goal-directed walk finds a good route and the colony's collective memory is redundant.

The small tier is therefore a demo and a debugging aid, **not a testbed for any claim about pheromone** — including claims about adapting its evaporation rate. Two tests enforce that distinction rather than leaving it to memory.

## Tuning versus adapting

A best-fixed vector found by Optuna on sixteen tuning seeds, evaluated on sixteen seeds it never saw:

*(provisional historical result — see “Earlier exploratory results” above)*

| | moderate | high |
|---|---|---|
| default parameters | 6.81% | 6.18% |
| **tuned, frozen** | **1.28%** | **0.71%** |
| tuned, adapting ρ | 1.27% | 0.62% |
| adaptive − frozen | −0.01% (p=0.686) | −0.10% (p=0.109) |

Tuning buys a factor of 5–9. Adapting buys nothing distinguishable. That is Stützle et al.'s conclusion, reproduced — with the caveat above that these numbers come from the demo tier and must be repeated where the mechanism is load-bearing.

The tuned vector is itself informative: α=0.59, β=0.95, ρ=0.75, goal_weight=2.90. At n=30 the search sensibly turned the pheromone mechanism down, because there it contributes nothing.

## First findings

Adapting evaporation alone, driven by each of the three signals, against its own frozen twin — paired by trial, n=16:

*(provisional historical result — see “Earlier exploratory results” above)*

| signal | scenario | frozen | adaptive | delta | Wilcoxon |
|---|---|---|---|---|---|
| edge_ratio | moderate | 6.81% | 6.82% | +0.00% | 0.674 |
| edge_ratio | high | 6.18% | 6.02% | −0.16% | 0.929 |
| volatility | moderate | 6.81% | 6.88% | +0.07% | 0.499 |
| volatility | high | 6.18% | 6.73% | +0.55% | 0.059 |
| lambda_branch | moderate | 6.81% | 6.92% | +0.11% | 0.594 |
| lambda_branch | high | 6.18% | 6.29% | +0.11% | 0.875 |

No signal beats freezing. The parameter did move — `rho` drifts from 0.100 to as low as 0.043 over a trial — so this is not an inert controller; it is adaptation that makes no difference. That is consistent with Stützle et al.

**This study is underpowered for small effects.** Trial-to-trial variance in excess is 5–12%, so detecting a 0.5% difference would need on the order of a thousand trials. n=16 rules out large effects only.

**The signals behave very differently.** Measured across scenarios:

*(provisional historical result — see “Earlier exploratory results” above)*

| signal | static | low | moderate | high | separation |
|---|---|---|---|---|---|
| edge_ratio | 0.0000 | 0.0022 | 0.0066 | 0.0152 | 50% of range |
| volatility | 0.0000 | 0.262 | 0.561 | 0.861 | 86% of range |
| lambda_branch | 7.30 | 7.38 | 7.14 | 7.24 | 4% of range |

The two external signals track disruption cleanly. λ-branching does not — and should not: it measures whether the *colony* has stagnated, not what the world is doing. It clears p < 0.05 purely on sample size, which is why the gate requires a separation large enough to act on rather than a p-value alone.

Under a 300-evaluation budget with per-timestep disruption the colony never stagnates — λ *rises* from 7.6 to 9.1 over a trial — so the stagnation signal only ever pushes one way and behaves as a one-directional drift rather than feedback.

## Status

| Milestone | State |
|---|---|
| M0 · skeleton, RNG, config, CLI | ✅ |
| M1 · graph, events, timeline, oracle | ✅ |
| M2 · optimizer protocol, meter, A\*, ACO | ✅ |
| M3 · harness, IO, first result | ✅ |
| M4 · signals + controllers | ✅ |
| M5 · best-fixed baseline (Optuna) | ✅ |
| M6 · PSO + Hybrid | ✅ |
| M7 · **allocation experiment** | ✅ completed in the 1,200-trial evidence run; recency-driven allocation showed no meaningful gain over fixed |
| M8 · statistics + figures | ✅ |
| M9 · scale study | ✅ completed at 200 and 1,000 nodes |
| M10 · Pygame replay | ✅ — to be retired once the dashboard replaces it (`decisionLedger.md` D17) |
| M11 · full technical documentation | ✅ — but see the provisional and legacy markers in [DOCUMENTATION.md](DOCUMENTATION.md) |

**M7 history.** An earlier two-scenario, 30-trial run was void because defect F1 made `RecencySignal` fire one timestep early. The later evidence run and its negative allocation result are documented in [FINDINGS_TESTS.md](FINDINGS_TESTS.md); see `decisionLedger.md` §4 for the earlier defect.

## Documentation

This repository contains exhaustive documentation detailing the project's architecture, mathematical formulations, and experimental methodology:
- **[DOCUMENTATION.md](DOCUMENTATION.md)**: Comprehensive technical documentation covering the project overview, system architecture, control feedback loops, operational workflows, and experimental setup.
- **[dynaswarm_algorithms.pdf](dynaswarm_algorithms.pdf)**: A formal, 13-page academic reference detailing the mathematical formulation of A*, MAX-MIN ACO, Priority-Vector PSO, the Hybrid ACO-PSO, and the adaptive controller. (Source: `dynaswarm_algorithms.tex`).

## Running it

See **[RUNBOOK.md](RUNBOOK.md)** for the full sequence: setup, the test suite, seven experiments with runtimes and acceptance checks, and what is still unfinished.

## Quick start

```bash
python3 -m venv .venv && ./.venv/bin/pip install -e ".[dev,viz]"
./.venv/bin/pytest -q
./.venv/bin/python -m dynaswarm.cli                       # smoke config
./.venv/bin/python -m dynaswarm.cli graph=medium200 scenario=high
```

Hydra owns run directories: every run writes to its own timestamped folder alongside the exact config that produced it.

## Layout

```
src/dynaswarm/
  core/        rng · graphview · generate · events · timeline · oracle · meter
  optimizers/  protocol · astar · aco · pso · hybrid · spec
  control/     signals · controllers
  harness/     arm · trial · runner
  io/          schema · writer
  analysis/    load · stats · recovery · plots
  tuning/      best_fixed
  viz/         replay
conf/          graph/ scenario/ experiment/ budget/ ...
tests/
```

Source is capped at 2000 *statements* by a test — statements rather than lines, because only about a third of these files are executable and a line budget would tax documentation instead of scope. Research code accretes interfaces and reporting faster than it accretes science; the cap is a crude but honest brake.

## References

- Dorigo, Maniezzo & Colorni (1996), *Ant System* — ACO
- Kennedy & Eberhart (1995), *Particle Swarm Optimization* — PSO
- Stützle & Hoos, *MAX–MIN Ant System* — trail limits
- Stützle et al., *Parameter Adaptation in Ant Colony Optimization* — the negative result this project works against
- Mavrovouniotis & Yang (2013), *Adapting the Pheromone Evaporation Rate in Dynamic Routing Problems* — λ-branching signal, ±σ increments

## Licence

MIT
