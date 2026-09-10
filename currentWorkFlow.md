# SEGMENT 17 — Diagnose F13

**Phase 3 · Restructure · Segment 1 of ~4**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` **§5.3 (PSO), §7 (the control layer and why it is being rebuilt), §17.1 (PSO inertia)**. `WORKFLOW_LOG.md` **Entries 015 and 016** carry F13 and its second reading.
> Append your findings to the **bottom** of this file.
>
> ## ⛔ YOU DO NOT COMMIT
>
> Rudra commits. Leave the tree unstaged, paste `git status --short`, and paste the commit message as a copyable block **with no `Co-Authored-By` trailer**. No `git add`, no `git commit`, no `git stash`, never `git add -A`.

---

## Goal

**Find out why PSO's swarm stops moving under disruption. Do not fix it.**

Phase 3 rebuilds the control layer and settles the inertia question, and **both of those decisions depend on the answer to this one.** Building first and diagnosing after would mean choosing a lever without knowing what it has to move.

---

## What is already measured, and what is still a story

**Measured, from Phase 2:**

| | first | last |
|---|---|---|
| mean velocity | 0.1119 | 5.112e-14 |
| diversity | 0.1274 | 2.927e-13 |
| global-best updates | 7 | 0 |

And the contrast that makes it a finding rather than a curiosity: **in isolation, with no disruptions, velocity settles at ~1.4e-02 and stays there.** The collapse is specific to a disrupted run — which is backwards, since disruption ought to stir a swarm rather than flatten it.

**Not measured — the Architect's hypothesis, and this segment's job is to try to break it:**

> PSO's velocity has three parts: keep going (inertia × current velocity), pull toward the particle's own best, pull toward the swarm's best. **If the particles all converge onto the same point, both pull terms go to zero** — a particle sitting on its own best and on the swarm's best is being pulled nowhere. What remains is inertia multiplying a shrinking number by something less than one, with nothing feeding it. Velocity then decays geometrically to nothing and cannot recover, because recovery would require a pull, and there is nothing left to pull toward.

Diversity at `2.9e-13` is consistent with this. **Consistency is not confirmation.**

**Treat that paragraph as a claim to falsify, not a conclusion to illustrate.** It is the Architect's story, it has started to look right, and Entry 016 recorded exactly why that makes it dangerous: *a hypothesis that is starting to look right is the one that stops being tested.* Eight consecutive segments say the interesting finding is the one nobody asked for. **If the hypothesis is wrong, saying so is the most valuable outcome available here.**

---

## ⚠️ T0 — MEASURE

`src/` **2037 / 2100**, margin **63**.

**This is a diagnosis. It should cost `src/` almost nothing.** Temporary instrumentation, `scripts/`, or a test — not permanent telemetry. If you conclude a permanent probe is warranted by what you find, **propose it; do not add it.**

Report projection and actual, and say where the instrumentation lives.

---

## T1 — Decompose the velocity update

Log the **three terms separately**, per step, across a disrupted run: the inertia contribution, the cognitive pull, the social pull. Magnitudes, not verdicts.

The question is narrow and answerable: **at the moment velocity collapses, which terms are still contributing and which have gone to zero?**

- if the two pull terms vanish and inertia is simply doing its job → the hypothesis holds, and the mechanism is diversity loss
- if a pull term is still large while velocity dies anyway → **the hypothesis is wrong**, something else is draining it, and that is the finding
- if velocity dies *before* diversity collapses → the causality is the other way round, and that changes the fix entirely

**Report which of these the numbers say.** Say it plainly, including if it is the second or third.

## T2 — Locate it in time

**When does it happen — and is it tied to disruption at all?**

- does the collapse begin at a disruption step, or drift down independently of them?
- is it one event, or accumulation across many?
- the isolation run settles at `1.4e-02` and *stays*. **What is different about the disrupted path?**

That last question is the one that matters most. **Something about disruption is not merely failing to help the swarm — it is actively worse than leaving it alone.** Whatever that is, it is the defect.

**One specific thing to check, and it is checkable rather than speculative:** what happens to the personal and global bests when the graph changes? A best evaluated against the old graph is a stale number. If bests are re-evaluated on the new graph and collapse onto current positions — or are reset — the pull terms die at exactly that moment. **Whether that is what happens is a fact about the code, not an opinion.**

## T3 — Say what the fix would be, and do not do it

Once you know the mechanism, state the options and what each would cost. Likely candidates, depending on what T1 and T2 say:

- **adaptive inertia** — raise it when disruption lands, re-energise the swarm. **This is §17.1's promised-and-never-delivered parameter**, and if the diagnosis points here, the *implement or formally drop* question is answered by the diagnosis rather than by argument
- **re-injection / hypermutation** — perturb some fraction of particles on disruption
- **best re-evaluation policy** — if T2 finds the bests are the problem, the fix is there and inertia is a workaround for it

**Do not implement any of them.** Segment 18 decides, with this in hand.

**And say if the honest answer is "this is correct behaviour."** Premature convergence on a hard dynamic problem is a real phenomenon, not automatically a bug. If that is what the numbers say, the consequence is not a code change — it is that the report states PSO standalone is handicapped by design, and Claim 1 is stated accordingly. **That is a legitimate outcome of this segment.**

## T4 — What it means for Claim 1

PSO standalone runs **27–41% above the optimum.** Claim 1 is that the hybrid beats its components.

**Estimate, from what you now know, how much of that gap is attributable to the collapse.** A number with error bars, or an honest "cannot be estimated without running the fix" — both are answers. What is not an answer is leaving it unaddressed, because it is the first thing an examiner asks when one component does conspicuously badly.

## T5 — Tests

Whatever you keep must be pinned. At minimum:

| Test | Catches |
|---|---|
| **The decomposition sums to the actual velocity update** | An instrument that measures three things which do not add up to the thing they explain is measuring something else |
| **The isolation-versus-disruption contrast reproduces** | It is the entire basis of the finding. If it does not reproduce, say so immediately |

**Every invariant test shown failing against corrupted input.**

## T6 — Mutations, two, one of them yours

**Specified:** make the decomposition report the terms *before* they are combined rather than as applied. Plausible magnitudes, wrong story — the same shape as segment 14's probe that observed the call instead of the effect.

**Yours.** Eight consecutive segments.

## T7 — Show it

1. T0, and where the instrumentation lives
2. **The three terms across the run** — the artefact of this segment
3. **When the collapse starts, relative to disruptions**
4. **Your verdict on the hypothesis: holds, wrong, or something else** — and if wrong, what the numbers actually say
5. What the bests do on a graph change
6. The options and their costs, unimplemented
7. **Your estimate of how much of PSO's gap this accounts for**

## T8 — Hand over, do **not** commit

`git status --short`, the commit message as a copyable block, no `Co-Authored-By`, one line confirming complete and uncommitted.

---

## Constraints

| | |
|---|---|
| **Diagnose. Do not fix.** | Segment 18 decides with this in hand |
| **The hypothesis is to be falsified, not illustrated** | Saying it is wrong is the best available outcome |
| **`src/` should barely move** | Temporary instrumentation. Propose permanent probes; do not add them |
| **Report magnitudes, not verdicts** | Except in T4 and T7, which explicitly ask for your reading — mark it as reading |
| **No control-layer changes** | F4, F7, F8 and the `allocation/` package are later in Phase 3 |
| **No inertia implementation** | §17.1 is decided in segment 18, against this |
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

**Paste verbatim:** T0 · the three-term decomposition across a disrupted run · when the collapse starts relative to disruptions · what the bests do on a graph change · **your verdict on the hypothesis** · the options, unimplemented · your estimate for Claim 1 · both mutations · every invariant test shown red.

---

## Definition of done

Green suite, artefacts pasted, **a verdict on the hypothesis stated plainly**, uncommitted with the message pasted, FINDINGS appended.

**After this, Phase 3 knows what it is fixing before it starts fixing.** Segment 18 settles inertia and opens the `allocation/` package.

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->
