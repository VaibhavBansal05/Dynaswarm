# SEGMENT 18 — Fix F13, Measure It, Settle Inertia

**Phase 3 · Restructure · Segment 2 of 5**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` **§5.3 (PSO), §6 (the Hybrid), §10.2 (the five fairness guarantees), §17.1 (PSO inertia)**. `WORKFLOW_LOG.md` **Entry 017** is the diagnosis this segment acts on — R1 restates F13, R2 sets the fix, R3 reframes inertia, R4 covers the Hybrid.
> Append your findings to the **bottom** of this file.
>
> ## ⛔ YOU DO NOT COMMIT
>
> Rudra commits. Leave the tree unstaged, paste `git status --short`, and paste the commit message as a copyable block **with no `Co-Authored-By` trailer**. No `git add`, no `git commit`, no `git stash`, never `git add -A`.

---

## Goal

Three things, in this order and not another: **fix it · measure it · then decide inertia against the measurement.**

The ordering is the point. §17.1's inertia question has been open since Phase 0 and was always going to be settled by argument. It should not be. **Fix the defect first, measure what is left, and let the number decide** — otherwise inertia gets credited or blamed for F13's behaviour, which is what Entry 017 R3 ruled against.

---

## ⚠️ T0 — MEASURE

`src/` **2037 / 2100**, margin **63**. The fix itself is a handful of statements; the measurement should cost `src/` nothing.

Report projection and actual, and say what remains for segments 19–21.

---

## T1 — Fix F13

**The fix goes in PSO, not the harness.** `rebind` also assigns `self._view = view`, and the optimizer genuinely needs the current graph every step. **The harness must keep calling `rebind` unconditionally** — if you "fix" it there, view propagation breaks and every arm starts operating on a stale graph, which is a far worse defect than the one being repaired. Say in a comment why the call stays unconditional, so a later segment does not helpfully move it.

**The change:** invalidate the personal-best costs **only when the graph actually differs from the one PSO last saw.**

**Detecting that:** the view already carries `state_hash()` — the harness uses it to assert nobody mutates the shared world. Store the last one, compare, skip the invalidation when it matches. No API change, no new fairness surface, no cost to any other arm.

**One property of this fix to state plainly rather than let a reader assume otherwise:** it is **conservative, not exact.** When any edge anywhere changes, every remembered cost is invalidated — including those of particles whose remembered route is nowhere near the change. That is correct-but-blunt. The exact version re-prices each best instead of destroying it, and Entry 017 R2 records why that is not being done now: re-pricing costs metered evaluations, and making PSO pay for disruption in a currency ACO does not pay is a fairness decision, not an implementation detail. **Note the imprecision in the docstring so the next person does not mistake blunt for wrong.**

## T2 — Measure what the fix buys, and be careful what you compare

**Before and after, same seeds, both conditions:**

| | static graph | disrupted graph |
|---|---|---|
| PSO standalone | | |
| Hybrid | | |

Report **excess over the optimum**, and the three collapse indicators — **velocity, diversity, global-best updates.**

**Do not repeat segment 15's mistake.** That comparison differed in two ways at once and pointed at the wrong cause for two segments. **Every comparison here changes exactly one thing.** State, for each, what is held fixed.

Enough seeds that the answer is not one lucky run. Segment 17 needed six to find that seed 1000 was the weakest of them.

## T3 — The question that decides segments 19–21

**Does the fix restore the swarm's spread under disruption, or only on a static graph?**

This is the whole reason the measurement is in this segment rather than waiting.

- **If diversity holds up under disruption after the fix** → the defect was the whole story. Nothing further is needed, and re-scattering stays unbuilt
- **If diversity still collapses under disruption** → the fix was necessary but not sufficient. Something about disruption genuinely does drain the swarm, and **re-initialisation (scattering a fraction of particles on a graph change) becomes a real candidate** — a standard technique for dynamic PSO, and one this project has deliberately held in reserve

**Report which, with the numbers.** Do not implement re-initialisation either way; that is a decision for the next segment, made against this answer.

## T4 — Claim 1, measured

Entry 017 R4: the Hybrid contains a PSO and has carried this defect its whole life, while ACO's half was unaffected. Its 2.2% excess is largely ACO's work.

**So measure what the fix does to the gap Claim 1 rests on:**

- PSO standalone, before and after
- Hybrid, before and after
- **the gap between Hybrid and its better component**, before and after

**Report the direction honestly, including if it narrows.** A hybrid that beats its components by less once those components work properly is still a true result, and a smaller true result is worth more than a larger one that rested on a crippled baseline. **This is the number that would have gone into the report unexamined**, and it is the reason Phase 2 existed.

Do **not** run a full manifest here — that is Phase 4. Enough seeds for a direction and a rough size, clearly labelled as preliminary.

## T5 — Settle §17.1: adaptive inertia, implement or formally drop

**Now, and only now**, with T2 and T3 in hand.

The state of it: `inertia` is applied at `pso.py:204` but is absent from `EXPLORE_SIGN`, so it is **implemented and un-adaptable**. The synopsis promised adaptive tuning of it. §17.1 says the report must state which way this went and why — *"either is defensible; silence is not."*

Entry 017 R3 removed F13 as an argument for it. So decide it on its own merits, and **let T3's answer carry weight**: if the swarm still loses spread under disruption after the fix, adaptive inertia has an identified job. If it does not, dropping it is clean and says so.

**Make the decision and write the justification**, in a form the report can use. If you implement it, `EXPLORE_SIGN` needs an entry and the sign needs arguing — higher inertia means more roaming, so exploring is `+1`. If you drop it, the reasoning must be the same shape as the one already documented for `n_ants` and `n_particles`.

**State which you chose and why, in one paragraph.** That paragraph is going in the report.

## T6 — Tests

| Test | Catches |
|---|---|
| **A quiet step does not invalidate any personal-best cost** | The fix, directly |
| **A changed graph still does** | The other direction — a fix that never invalidates is worse than the bug |
| **Velocity does not collapse on a static 60-step run** | F13, pinned. **The regression test that would have caught this originally** |
| **`rebind` still propagates the view every step** | The thing not to break |
| **The Hybrid inherits the fix** | It passes `rebind` down; assert it, do not assume it |

**Every invariant test shown failing against corrupted input, and the corruption pasted.**

## T7 — Mutations, two, one of them yours

**Specified:** make the change-detection always report "unchanged." The fix then never invalidates anything, stale costs survive disruptions forever, and **the collapse tests all pass** because velocity is healthy. A fix that over-corrects looks exactly like a fix that works, from the direction you were watching.

**Yours.** Nine consecutive segments; Entry 017's was the one that found the diagnosis rested on a single seed.

## T8 — Show it

1. T0
2. **The before/after table** — both arms, both conditions, seeds stated
3. **T3's answer: does spread survive disruption after the fix?**
4. **Claim 1's gap, before and after**, labelled preliminary
5. **The inertia decision and its one-paragraph justification**
6. Both mutations
7. **Your read: is PSO now a fair baseline for the Hybrid to be compared against?** That is the question the report will be judged on

## T9 — Hand over, do **not** commit

`git status --short`, the commit message as a copyable block, no `Co-Authored-By`, one line confirming complete and uncommitted.

---

## Constraints

| | |
|---|---|
| **The fix goes in PSO, not the harness** | `rebind` must keep being called every step |
| **Conservative fix only** | No re-pricing. Entry 017 R2 — the fairness question stays unopened |
| **No re-initialisation** | Decide in the next segment, against T3 |
| **Every comparison changes exactly one thing** | Segment 15's error does not recur |
| **No manifest runs** | Phase 4. Preliminary numbers, labelled |
| **No control-layer changes** | F4, F7, F8 and `allocation/` are segments 20–21 |
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

**Paste verbatim:** T0 · the before/after table with seeds · whether spread survives disruption · Claim 1's gap before and after · **the inertia decision and its justification paragraph** · both mutations · every invariant test shown red · your read on whether PSO is now a fair baseline.

---

## Definition of done

Green suite, artefacts pasted, **the inertia question closed with a written justification**, uncommitted with the message pasted, FINDINGS appended.

**After this the components are repaired and honest.** Segment 19 checks they are also correct.

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->

---

# FINDINGS — Segment 18

## 1. T1 — the fix

In `PSO.rebind`, guarded on `view.state_hash()`:

```python
digest = view.state_hash()
if digest != self._last_state:
    self._own_cost[:] = np.inf
    self._last_state = digest
```

**`src/` 2041 / 2100**, +4 from segment 17's 2037, margin 59. No API change,
no new fairness surface, no cost to any other arm.

Both required comments are in place. In `pso.rebind`, why the guard lives here
and not at the call site, and that it is **conservative rather than exact** —
any change anywhere invalidates every remembered cost, and re-pricing instead
would cost metered evaluations, which is a fairness decision rather than an
implementation detail (Entry 017 R2). In `trial.py:175`, why the call stays
unconditional: `rebind` is how an optimizer receives the current world, and
making the *call* conditional would leave every arm searching a stale graph.

## 2. T2 — before and after, one variable per comparison

Every pair below holds seed, graph, scenario, budget and arm fixed and varies
**only the guard** — simulated by clearing the remembered hash, so `rebind`
itself is untouched. n = 8 seeds.

```
F13 FIX — BEFORE AND AFTER
====================================================================
  Each pair varies the guard and nothing else: same seeds, same graph,
  same scenario, same budget, same arm.

  STATIC     (pso, 0.0 events/step, n=8)
                       before        after       change
    excess             0.1115       0.1054      -0.6 pp
    velocity        4.400e-08      0.02713    x6.17e+05
    diversity       3.161e-07      0.04242    x1.34e+05
    gbest               11.38        14.88        x1.31

  DISRUPTED  (pso, 0.3 events/step, n=8)
                       before        after       change
    excess             0.2499       0.1831      -6.7 pp
    velocity         0.005911       0.0173        x2.93
    diversity         0.01044      0.02201        x2.11
    gbest                16.5        23.88        x1.45

  STATIC     (hybrid, 0.0 events/step, n=8)
                       before        after       change
    excess            0.06438      0.06032      -0.4 pp
    velocity          0.02797      0.06995         x2.5
    diversity         0.03189      0.07286        x2.29
    gbest               14.25        14.62        x1.03

  DISRUPTED  (hybrid, 0.3 events/step, n=8)
                       before        after       change
    excess            0.09572      0.08402      -1.2 pp
    velocity          0.03045      0.02956       x0.971
    diversity         0.03224      0.03798        x1.18
    gbest               25.88        27.12        x1.05


  CLAIM 1 — the hybrid against its better component
  ------------------------------------------------------------------
    before static     PSO   11.1%   Hybrid    6.4%   gap   +4.7%
    before disrupted  PSO   25.0%   Hybrid    9.6%   gap  +15.4%
    after  static     PSO   10.5%   Hybrid    6.0%   gap   +4.5%
    after  disrupted  PSO   18.3%   Hybrid    8.4%   gap   +9.9%
```

### What the numbers say

**On a static graph the collapse was catastrophic and cost almost nothing.**
Velocity ×617,000, diversity ×134,000 — and excess improves by 0.6 points.
The swarm was frozen and still found routes nearly as good, because with no
disruption the first decent answer stays the right answer.

**Under disruption it was moderate and cost a great deal.** Velocity only
×2.9 — and **excess improves 6.7 points, 25.0% → 18.3%.** That is where the
defect was actually being paid for.

### An inversion worth stating

**Before the fix, disruption was the only thing keeping the swarm alive.**
Static diversity was `3.16e-07`; disrupted was `1.04e-02` — *thirty thousand
times healthier*. `reset_learned_state` scatters particles when the graph
changes, and that scattering was partially rescuing a swarm the wipe was
destroying.

That is why F13 looked like a disruption problem and was the opposite of one.
The quiet case was worse, and nobody had measured the quiet case.

## 3. T3 — does spread survive disruption after the fix?

**No. The fix was necessary and is not sufficient.**

```
  diversity, after the fix:    static 0.0424     disrupted 0.0220
```

The swarm holds **about half its static spread** under disruption. Before the
fix that comparison was meaningless — the static case was the broken one.

**So the answer that decides segments 19–21 is the second branch:** something
about disruption genuinely does drain the swarm beyond what F13 explains, and
**re-initialisation becomes a real candidate.** Not implemented, per the
constraint.

**One honest qualification.** Disrupted PSO is at 18.3% against static 10.5%,
and I have *not* established that the 7.8-point difference is caused by the
spread loss — a moving optimum is a harder problem regardless. What is
established is that spread is materially lower and that the fix did not
restore it.

## 4. T4 — Claim 1, measured

```
  before  static     PSO  11.1%   Hybrid  6.4%   gap  +4.7%
  before  disrupted  PSO  25.0%   Hybrid  9.6%   gap +15.4%
  after   static     PSO  10.5%   Hybrid  6.0%   gap  +4.5%
  after   disrupted  PSO  18.3%   Hybrid  8.4%   gap  +9.9%
```

**Under disruption the gap narrows from 15.4 points to 9.9 — it loses over a
third of its size.** Claim 1 survives: the hybrid still beats its better
component by ~10 points. But a third of the margin that would have been
reported was PSO being crippled.

Entry 017 R4 predicted this and the prediction holds: the Hybrid's own excess
barely moves (9.6% → 8.4%), because its ACO half was never affected and was
doing most of the work. **The gap narrowed almost entirely from the baseline
improving, not from the hybrid getting worse.**

**This is the number that would have gone into the report unexamined**, and a
smaller true result is worth more than a larger one resting on a crippled
baseline.

Preliminary: n = 8 seeds, one trial each, not a manifest. Phase 4 measures it
properly.

## 5. T5 — §17.1 settled: **adaptive inertia is formally dropped**

> **`inertia` is dropped, and not for the reason `n_ants` is.** Its sign is
> not ambiguous — higher inertia carries more of the previous velocity, so a
> particle roams further and `+1.0` would be correct. It is excluded because
> of **attribution**. PSO runs inside the hybrid, so an adaptive inertia would
> give `hybrid_adaptive` two adapting mechanisms at once: the allocation split
> and the swarm's own momentum. A win could then not be attributed to either.
> That is precisely the objection this project already makes to pairing
> `hybrid` against `hybrid_adaptive` — two arms differing in two ways answer
> no question — and the thesis is that *recency-driven allocation* helps, a
> claim which becomes unmeasurable if something else is adapting beside it.
> The job adaptive inertia would have done is real: after F13's fix the swarm
> still holds only about half its static spread under disruption. But that job
> is better served by re-initialisation, which is internal to PSO, adds no
> controlled parameter, and leaves the allocation claim clean.

Documented in `controllers.py` beside the other exclusions, and pinned by
`test_inertia_is_formally_dropped_not_overlooked` — because without a test the
absence is indistinguishable from an oversight, which is the state §17.1
objected to.

## 6. Both mutations

**A — specified: change-detection always reports "unchanged."**

```
E  AssertionError: a real graph change did not invalidate the remembered costs
```

Caught by the other-direction test. The collapse tests all passed, exactly as
predicted — a fix that over-corrects looks like a fix that works from the
direction you were watching.

**B — mine: compare object identity instead of state value.**

```
15 tests: all passed
real harness, static run, final velocity: 5.171e-14
```

**Every test passed and the bug was completely unfixed.**

All my unit tests reuse a single `GraphView` object across sixty rebinds, so
`id(view)` never changes and the guard appears to work. The harness does not
do that — `state_at(t)` caches a **distinct object per timestep**, identical
in content on a quiet step but not the same object. The guard would have
skipped nothing, in production, silently.

The fixture was unrepresentative of the call pattern it was standing in for.
Now covered by a test that runs the **real harness path** on a static
scenario, and shown red:

```
E  seed 1000: velocity collapsed to 5.171e-14 on a static run through the
   harness — the guard is comparing something other than state value
```

**Ten consecutive segments.**

## 7. Acceptance

| Check | Result |
|---|---|
| Suite | **409 passed, 0 failed, 0 skipped** |
| Lint, four trees | `All checks passed!` |
| `src/` | **2041 / 2100**, +4, margin 59 |
| `outputs/` before / after | **26 / 26** |
| `tests/test_f13_diagnosis.py` | **15 passed** |

## 8. What segment 19 inherits

- **T3 says re-initialisation has an identified job**, with a number attached:
  half the static spread, after the fix
- **Adaptive inertia is closed**, so it is not competing for that job
- **Claim 1's real size under disruption is ~10 points, not ~15**, and Phase 4
  should be planned against the smaller figure
- The exact re-pricing alternative to the conservative invalidation is still
  open, and is a fairness question about metered evaluations rather than an
  implementation one
