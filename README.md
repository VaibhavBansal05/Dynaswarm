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

## Why the design looks the way it does

This codebase replaces an earlier implementation whose central mechanism, it turned out, never ran. The specifics shaped almost every decision here:

| What went wrong before | What prevents it here |
|---|---|
| The sensing signal `changed_edges / total_edges` maxed at 0.007 against a 0.15 threshold — the controller sat in one regime 100% of the time | Churn is a *fraction of edges*, so the signal is scale-comparable; three signals are implemented and their dynamic range is **asserted by test** |
| Four of ten "tuned" parameters were silently inert | `PARAM_SPEC` binding is total; a test proves every parameter changes behaviour |
| Baseline algorithms ran *before* the graph was mutated, so all scenarios returned identical costs | The event schedule is materialised up front; every arm provably sees the same graph state |
| Compute was equalised by *iterations*, so bigger populations bought more CPU | Budget is denominated in candidate-path constructions and metered by the harness |
| Global RNG seeding let arms perturb each other | Streams are content-addressed; adding an arm cannot move another's bits |

Each row has a corresponding test in `tests/`.

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

Source is capped at 3000 lines by a test. The previous implementation reached 13,300 while doing less.

## References

- Dorigo, Maniezzo & Colorni (1996), *Ant System* — ACO
- Kennedy & Eberhart (1995), *Particle Swarm Optimization* — PSO
- Stützle & Hoos, *MAX–MIN Ant System* — trail limits
- Stützle et al., *Parameter Adaptation in Ant Colony Optimization* — the negative result this project works against
- Mavrovouniotis & Yang (2013), *Adapting the Pheromone Evaporation Rate in Dynamic Routing Problems* — λ-branching signal, ±σ increments

## Licence

MIT
