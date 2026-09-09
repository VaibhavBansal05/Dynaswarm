# SEGMENT 15 — Prove PSO and the Hybrid Run

**Phase 2 · Trust it · Segment 2 of 3**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` **§5.3 (PSO), §6 (the Hybrid — §6.1 the budget split, §6.2 the exchange), §17.1 (PSO inertia)**, §2.1. `WORKFLOW_LOG.md` **Entry 014** carries R1, which is T1 here.
> Append your findings to the **bottom** of this file.
>
> ## ⛔ YOU DO NOT COMMIT
>
> Rudra commits. Leave the tree unstaged, paste `git status --short`, and paste the commit message as a copyable block **with no `Co-Authored-By` trailer**. No `git add`, no `git commit`, no `git stash`, never `git add -A`. Reading history is fine.

---

## Goal

Same discipline as segment 14, on the two components left. **Your standard from last segment is the standard:**

> *"Every probe answers **did it run**. None answers **did it run correctly**."*

Claim exactly that much and no more.

**The Hybrid matters more than PSO here**, and it is worth saying why up front. Claim 1 of the project is *"the hybrid beats its components."* If the budget split does not actually happen — if one component quietly gets the whole budget — then the hybrid is a component wearing a different name, and Claim 1 is comparing a thing to itself. **That is not a bug that would show up in the numbers. It would show up as a clean, publishable, wrong result.**

---

## ⚠️ T0 — MEASURE

`src/` **2015 / 2100**, margin **85**. Your projection was ~33 for this segment (PSO ~25 + Hybrid ~8, the Hybrid cheap because its probe is a prefix-wrapper).

**Report projection then actual.** If the wrapper insight does not hold up in practice, say so before spending — that projection is what made Phase 2 fit.

---

## T1 — Entry 014's R1: `state_at` stays, and the reason gets written down

`timeline.py:262` — `state_at` still does `for event in self.schedule[t - 1]`. You did not flag it, and **leaving it was right.**

But it must be written down or a future segment will delegate it in the name of F10 and make things worse:

- `state_at` **is** the definition. Applying `schedule[t-1]` to state `t-1` is what *"the state at `t`"* means. `events_at` reports that fact; `state_at` enacts it
- `events_at`'s out-of-range guard cuts the **other** way here. Delegating would turn an `IndexError` past the horizon into **silently returning the previous state** — the quiet-wrong-answer class this project keeps finding

**Two things:** a comment at that line naming it the definitional site and saying why it does not delegate, and a test asserting `state_at` past the horizon still raises. **The guard is the feature.**

---

## T2 — Report what PSO and the Hybrid record today

From source, before designing anything. What `probe` already carries for each, when it fires, what it costs.

**Confirm the prefix-wrapper.** Your projection rests on the Hybrid inheriting every component field for free. If that is a design you are about to build rather than one that exists, say which.

---

## T3 — The PSO probes (§5.3)

PSO here is **priority-vector encoding** — memory on nodes, not edges. The questions Phase 2 must be able to answer per step:

| Question | Why it cannot be assumed |
|---|---|
| **Are particle positions actually moving?** | A frozen swarm is a fixed set of random guesses re-evaluated. It produces routes, produces excess, looks like a result |
| **Is velocity being applied, and is it bounded?** | Velocity that explodes or collapses to zero both look like "PSO explores poorly," which is a finding you would report |
| **Are personal bests updating?** | Without them there is no memory, and PSO's whole claim here is *memory on nodes* |
| **Is the global best updating — and how often?** | A global best frozen after iteration two is premature convergence, and it is indistinguishable from a hard problem unless you count it |

**One note, not a task.** §17.1 records that PSO's **inertia** was promised in the synopsis and never delivered — `EXPLORE_SIGN` has seven entries and none is `inertia`. **Resolving that is Phase 3's.** But if a probe here makes its status visible, say so plainly in FINDINGS — Phase 3 has to decide *implement or formally drop*, and a measurement beats an argument.

## T4 — The Hybrid probes (§6.1, §6.2)

**The two that matter most in the project:**

| Question | Why it decides a claim |
|---|---|
| **Is the budget actually split in the declared ratio?** | Evaluations spent by each component, per step, against `aco_fraction` and the total budget. **If this is not true, Claim 1 compares the hybrid to itself** |
| **Does the exchange actually happen?** | §6.2. Count exchanges, not "exchange enabled". An exchange mechanism that never fires makes the hybrid two solvers in one process, which is not what the report will say it is |

**And the reading that matters for Phase 3:** with the uncontrolled hybrid, `aco_fraction` sits at 0.5 for all 60 steps — vClaude measured that in segment 12. **A probe that reports the split should show that flatness**, so the day the adaptive controller works, the same probe shows it moving. **The probe that proves the mechanism is inert today is the one that proves it live in Phase 3.**

## T5 — Prove each probe can say `inert`

**The task the phase exists for**, unchanged from segment 14:

1. Disable the mechanism — freeze the swarm, zero the velocity, stop personal-best updates, force the split to 100/0, disable the exchange
2. Run and paste the output
3. It must be **unmistakable**, and shown in both directions — a probe that reports inert while the mechanism runs is worse than none

**Two traps you found last segment, now checked for by name:**

- **Does the probe measure the effect or the call?** The bounds probe counted the *need* for a clip and would have reported "MAX–MIN active" with `np.clip` deleted. Ask it of every probe here before you demonstrate it
- **Do the counters reset per call?** All eight tests passed on monotonic totals last time. `> 0` is satisfied trivially by anything cumulative

## T6 — Tests

| Test | Catches |
|---|---|
| **`state_at` past the horizon raises** | T1 |
| **Each probe inert against its disabled mechanism** | |
| **Each probe live against the working one** | |
| **Counters reset per call** | Silence the mechanism on a second call, require exactly zero |
| **Probes do not change what they measure** | Same seed, probes on and off → identical `best_cost` at every step |
| **The budget split sums to the budget** | And matches `aco_fraction`. **The one that guards Claim 1** |

**Every invariant test shown failing against corrupted input, and the corruption pasted.**

## T7 — Mutations, two, one of them yours

**Specified:** make the Hybrid's split probe report the *requested* fraction rather than the evaluations actually spent. It would read 0.50 forever and be right by coincidence today — and would keep reading whatever was asked for on the day the controller starts asking for something else. **A probe that reports the input instead of the outcome is the exact shape of the bounds probe you already caught.**

**Yours.** Six consecutive segments. Entry 013 stated why it works: **a spec can only mutate what its author already imagined going wrong.**

## T8 — Show it

1. T0 projection vs actual
2. T1's comment and the horizon test
3. What PSO and the Hybrid record today, from source
4. **Every probe live and inert, side by side** — the artefact
5. **The budget split, measured** — evaluations to each component per step, against `aco_fraction`
6. Both mutations
7. **Your read: would you now believe a Hybrid number?** And say what you would still not defend

## T9 — Hand over, do **not** commit

`git status --short`, the commit message as a copyable block, no `Co-Authored-By`, one line confirming complete and uncommitted.

---

## Constraints

| | |
|---|---|
| **Project before spending** | Margin is 85 |
| **Every probe shown reporting inert** | Non-negotiable. An unproven probe does not ship |
| **Probes report numbers, not verdicts** | |
| **Measure the effect, not the call** | |
| **Counters reset per call** | |
| **Probes must not change what they measure** | Phase 4 runs this ≥100 times per arm |
| **No control-layer changes** | F4, F7, F8 and PSO inertia are Phase 3. **Measure and report; do not fix** |
| **No dashboard work** | The empty panels fill when the data exists |
| **No walkthrough** | Segment 16 |
| **Do not commit, do not push** | |

---

## Acceptance check

```bash
git diff --stat -- src/ tests/
./.venv/bin/pytest
./.venv/bin/ruff check src/ tests/ dashboard/
./.venv/bin/pytest -k "budget or statement" -s
ls outputs/
git status --short                       # UNSTAGED, UNCOMMITTED
```

**Paste verbatim:** projection vs actual · every probe live and inert · the measured budget split against `aco_fraction` · both mutations · every invariant test shown red · your read on believing a Hybrid number, and what you would still not defend.

---

## Definition of done

Green suite, artefacts pasted, **every probe demonstrated inert**, uncommitted with the message pasted, FINDINGS appended.

**After this all three optimizers can be shown to have actually run.** Segment 16 is the Layer 3 walkthrough, and closes Phase 2.

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->

---

# FINDINGS — Segment 15

## 1. T1 — `state_at` stays, and the reason is now at the line

Comment added at `timeline.py:262` and pinned by
`test_state_at_past_the_horizon_raises_rather_than_answering`:

```
state_at(20).t == 20        # last in-range state reachable
state_at(21)   -> IndexError
events_at(21)  -> ()        # deliberately different
```

The reason, written where someone reaching for consistency will meet it:
`changed_edges` was **a copy of the definition**, so F10 collapsing it was
right. `state_at` **is** the definition — applying `schedule[t-1]` to state
`t-1` is what "the state at t" means. Delegating would inherit `events_at`'s
out-of-range guard and turn the `IndexError` into **silently returning the
previous state under a later timestep's name**, in the one function every arm
reads its world from. **The guard is the feature.**

## 2. T2 — the prefix-wrapper is real, not planned

```python
out = {f"aco_{k}": v for k, v in self._aco.probe().items()}
out.update({f"pso_{k}": v for k, v in self._pso.probe().items()})
```

`hybrid.py:133-134`, already there. **Segment 14's projection rested on this and
it held**: every ACO field added last segment appeared in the Hybrid this
segment at zero cost, and every PSO field added today did the same. Only the
Hybrid's own two questions needed new code.

**`src/` 2015 → 2037, +22, margin 63.** Phase 2 has spent 32 of the 95 with
one segment left; segment 16 was projected at 10–15.

## 3. T3 — PSO, live

```
  t= 0 flown  222 repaired  44  speed 1.119e-01  pbest  93 gbest  7
  t=21 flown  300 repaired   0  speed 3.798e-06  pbest  20 gbest  0
  t=59 flown  264 repaired   0  speed 5.112e-14  pbest  20 gbest  0
```

**The finding: velocity collapses by thirteen orders of magnitude over a
disrupted run.** 1.1e-01 at t=0, 3.8e-06 by t=21, **5.1e-14 by t=59.** The
flight step still runs hundreds of times and still displaces particles, but by
amounts at the edge of float resolution. The swarm is not exploring; it is
being nudged.

**Reported as a measurement, not a verdict.** I have not concluded it is a
defect and it may be correct convergence behaviour. But it is exactly the
shape §17.1's open question is about — **`inertia` is applied
(`pso.py:204`) but is absent from `EXPLORE_SIGN`, so it is implemented and
un-adaptable** — and Phase 3 has to decide *implement or formally drop*. This
number is what that decision should be made against: whatever inertia is
doing, by t=59 there is almost no velocity left for it to carry.

**In isolation, without disruptions, velocity settles at ~1.4e-02 and stays
there.** The collapse is specific to a disrupted run. I did not chase why —
that is Phase 3's, and guessing would be a verdict.

### I nearly reported this wrong, twice

**First:** my print format was `:.4f`, so 3.8e-06 rendered as `0.0000` and I
was one step from reporting *"PSO's velocity is exactly zero"*. It is not; it
is small. I read the display instead of the value — the same class of error as
everything else this phase has found, committed while looking for it.

**Second:** the probe first counted `particles_moved` by diffing positions
across the call, and reported **14 moved on a swarm with `_move` disabled**.
`_repair` also writes positions (`pso.py:264`), so the probe was answering
*"did anything move a particle"* when the question was *"is the swarm
flying"* — two mechanisms through one channel, which is the confusion segment
9 split the picture to avoid. Now counted inside `_move`, and `particles_repaired`
carries the other mechanism separately.

## 4. T4 — the Hybrid, and Claim 1 is safe

```
  t= 0 declared 0.50 realised 0.500  spent 150/150  exch 1
  t=21 declared 0.50 realised 0.500  spent 150/150  exch 1
  t=59 declared 0.50 realised 0.500  spent 150/150  exch 1
```

**The split is real and exact.** `aco_share_realised` is computed from the
sub-meters' actual spend, not from `aco_fraction` — 150 evaluations each out of
300, at every step. **Claim 1 is not comparing the hybrid to itself.**

**The exchange fires every step** (`exchanged_this_step` 1). The hybrid is not
two solvers sharing a process.

**And the flatness is the point.** `aco_fraction` sits at 0.50 for all 60 steps
because the uncontrolled hybrid has nothing moving it — segment 12 measured the
same thing from the other side. **The probe that shows this flat today is the
one that shows the allocation moving in Phase 3**, and it will show it from
realised spend rather than from the number the controller asked for.

## 5. T5 — every probe shown inert

| Mechanism disabled | Probe reports |
|---|---|
| swarm frozen (`_move` silenced) | `particles_flown` **0** |
| personal bests can never update | `own_best_updates` **0** |
| PSO given nothing to spend | `pso_spent` **0**, `aco_share_realised` **1.0** |
| exchange silenced | `exchanged_this_step` **0** |
| velocity and all pulls zeroed | `particles_flown` **0**, `speed_mean` **0** |

Each also asserts the *other* mechanisms still report non-zero, so a probe
cannot pass by everything going quiet together.

**One probe was checked and found insufficient, and it is recorded rather than
quietly strengthened.** `speed_mean` **cannot** detect a frozen swarm: with
`_move` disabled the velocity array simply keeps its random initial value —
0.05, entirely healthy-looking. `particles_flown` is what detects it. The test
says so at the assertion, so nobody later "tidies" it into asserting zero speed.

## 6. Both traps from segment 14, checked on every probe

**Effect or call?** Caught two:

- `particles_flown` — first version diffed positions, which `_repair` also
  changes. Now counted at the displacement inside `_move`
- `aco_share_realised` — measured from spend, never from `aco_fraction`

**Do the counters reset?** Checked by test for PSO
(`test_the_swarm_counters_report_this_call_not_a_running_total`) rather than by
inspection, because inspection is what missed it last segment.

## 7. Both mutations

**A — specified: the split probe echoes the requested fraction.**

```
E  AssertionError: a one-sided split did not read as one-sided
E  assert 0.5 == 1.0
```

On a hybrid where PSO was given nothing, the echo reports a perfect 50/50.
Caught.

**B — mine: flight counted per call rather than per displacement.**

```
19 tests: 18 passed
```

**Not caught.** Counting `_move` calls instead of the positions they changed
passed everything. It matters precisely because of §3's finding: at t=59
velocity is 5e-14, so the flight step runs 264 times and moves nothing
measurable — and a per-call counter reports a swarm in vigorous motion on a
swarm that has stopped.

Now pinned, and shown red:

```
E  AssertionError: 263 flights counted with zero velocity
E  assert 263.0 == 0
```

**Seven consecutive segments.** The commissioned mutation confirmed a
prediction; the uncommissioned one found the gap.

## 8. Acceptance

| Check | Result |
|---|---|
| Suite | **386 passed, 0 failed, 0 skipped** |
| Lint, three trees | `All checks passed!` |
| `src/` | **2037 / 2100**, delta **+22**, margin 63 |
| `outputs/` before / after | **26 / 26** |
| `tests/test_probes.py` | **19 passed** |

## 9. Would I believe a number PSO or the Hybrid produced?

**The Hybrid's split: yes, without qualification.** It is measured from what
was spent, it is exact, and it has been seen reporting a one-sided split as
one-sided. That is the one this project most needed, because Claim 1 rests on
it.

**PSO: less than for ACO, and the reason is worth stating.** I can now show
that particles fly, that personal and global bests update, and that a frozen
swarm reads as frozen. What the probes also show is that **by the end of a
disrupted run the flight mechanism has almost nothing left to do** — and I
cannot yet tell you whether that is convergence working or exploration
failing. The probe made the question askable; it does not answer it.

**What none of this covers**, same boundary as last segment: every probe
answers *did it run*, not *did it run correctly*. A cognitive coefficient ten
times too large would fly particles vigorously and report beautifully.
