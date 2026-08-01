# dynaswarm

**Volatility-driven compute allocation in hybrid swarm metaheuristics for dynamic path optimization.**

Minor project · School of Computer Engineering, MIT Manipal (MAHE)
Rudra Rajpurohit · Vaibhav Krishna Bansal · Kartikey Goyal · Pavit Agrawal
Mentor: Mrs. Vidhya V

---

## The question

When you search for a shortest path through a network that keeps changing underneath you — roads closing, traffic spiking, links appearing — how should a swarm algorithm respond?

The usual answer is to retune the algorithm's parameters (evaporation rate, inertia) as the environment shifts. That has been studied extensively, and the founders of Ant Colony Optimization concluded there is *"[no] clear benefit in varying the parameter settings at run-time"* (Stützle et al.).

This project asks a different question.

## Thesis

> In a hybrid metaheuristic, the **allocation of compute between exploration and exploitation components** should be driven by measured environmental volatility.

Not *what parameters to use*, but *how much of your budget to give the explorer versus the refiner*, and when to shift that balance. ACO explores; PSO refines. When the world churns, buy exploration. When it settles, buy refinement.

**Supporting question:** what should the system actually *sense* to make that decision? We compare **external** signals (how much did the world change?) against **internal** signals (has my colony stagnated?), a choice the literature makes largely arbitrarily.

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

## Status

| Milestone | State |
|---|---|
| M0 · skeleton, RNG, config, CLI | ✅ |
| M1 · graph, events, timeline, oracle | 🚧 |
| M2 · optimizer protocol, meter, A\*, ACO | ⬜ |
| M3 · harness, IO, first result | ⬜ |
| M4 · signals + controllers | ⬜ |
| M5 · best-fixed baseline (Optuna) | ⬜ |
| M6 · PSO (cost-biased) + Hybrid | ⬜ |
| M7 · **allocation experiment** | ⬜ |
| M8 · statistics + figures | ⬜ |
| M9 · scale study | ⬜ |
| M10 · Pygame replay | ⬜ |

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
  core/        rng · graphview · generate · events · schedule · timeline · oracle · meter
  optimizers/  protocol · astar · aco · pso · hybrid · spec
  control/     signals · controllers
  harness/     arm · trial · runner
  io/          schema · writer
  analysis/    load · stats · plots
  tuning/      best_fixed
  viz/         replay
conf/          graph/ scenario/ experiment/ budget/ ...
tests/
```

Source is capped at 3000 lines by a test. Research code accretes interfaces and reporting faster than it accretes science; the cap is a crude but honest brake.

## References

- Dorigo, Maniezzo & Colorni (1996), *Ant System* — ACO
- Kennedy & Eberhart (1995), *Particle Swarm Optimization* — PSO
- Stützle & Hoos, *MAX–MIN Ant System* — trail limits
- Stützle et al., *Parameter Adaptation in Ant Colony Optimization* — the negative result this project works against
- Mavrovouniotis & Yang (2013), *Adapting the Pheromone Evaporation Rate in Dynamic Routing Problems* — λ-branching signal, ±σ increments

## Licence

MIT
