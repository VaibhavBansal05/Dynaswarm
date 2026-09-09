# SEGMENT 16 — The Trust Report

**Phase 2 · Trust it · Segment 3 of 3 — closes the phase**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` **§2.1 (the layers), §10.3, §17**, and `WORKFLOW_LOG.md` **Entries 014 and 015** — 015 carries F13, R2 and R3, which constrain this segment.
> Append your findings to the **bottom** of this file.
>
> ## ⛔ YOU DO NOT COMMIT
>
> Rudra commits. Leave the tree unstaged, paste `git status --short`, and paste the commit message as a copyable block **with no `Co-Authored-By` trailer**. No `git add`, no `git commit`, no `git stash`, never `git add -A`.

---

## Goal

**One command that answers, for every mechanism in this system: did it run, and how do we know.**

Segments 14 and 15 built the probes. They live in a run's telemetry, readable by someone who knows where to look. **That is not the same as being able to answer the question**, and the question gets asked in a viva.

Phase 2's gate — *every mechanism proven live or reported inert* — is currently true and **unproducible on demand**. This segment makes it producible.

---

## What this is not

**Not a dashboard feature.** Phase 1 is closed. The per-arm panel could now carry probe telemetry and §15.6 says it eventually should — **that waits for Phase 3**, when the panel gets its real content alongside the allocation view. Adding it here would dilute the segment that closes the phase.

**Not a verdict machine.** Entry 015's standard holds:

> *"Every probe answers **did it run**. None answers **did it run correctly**."*

The report says what was measured. It does not grade.

---

## ⚠️ T0 — MEASURE

`src/` **2037 / 2100**, margin **63**. Your projection for this segment was 10–15.

**A large part of this should live outside `src/`** — it is a reporting tool, not science. Say where you put it and why. `scripts/` and `tests/` are both outside the cap; the dashboard is not the right home.

Report projection then actual, plus the closing Phase 2 total against the 95 you started with.

---

## T1 — The report

**One command. Human-readable output. Every mechanism in one place.**

For each of ACO, PSO and the Hybrid, and for each probed mechanism:

- **what was measured** — the count or magnitude, not a grade
- **live or inert** — and the reading that says so
- **the reading it gives when broken** — from the demonstrations already done in 14 and 15

That third column is what makes the document evidence rather than a status page. **A reader must be able to see what a failure would have looked like**, otherwise the report is a list of numbers asserting their own significance.

**Entry 015's R2 is binding on every value printed:** no fixed-decimal format on a quantity whose scale is unknown. PSO's velocity reaches `5e-14`; a `:.4f` renders that as `0.0000` and manufactures the exact claim this phase exists to make honestly. **That mistake has already been made once in this project, by the person looking for it.**

## T2 — Carry the insufficiencies forward

**Entry 015's R3.** Where a probe is known not to detect something, the report says so **beside the probe**, not in a footnote.

Known already:

- **`speed_mean` cannot detect a frozen swarm** — velocity keeps its healthy random initial value. `particles_flown` is what detects it
- **`tau_deposited` cannot detect deposit on the wrong edges** — the count is identical either way
- **No probe answers "did it run *correctly*"** — this belongs at the top of the document, not buried

**A trust report that lists only what it can prove, with no account of what it cannot, is exactly the over-claim the phase was built to prevent.**

## T3 — F13 must be visible in it

Entry 015 logged PSO's velocity collapse — `1.1e-01 → 5.1e-14` across a disrupted run, against `~1.4e-02` stable in isolation.

**It goes in the report as a measurement, with the isolation contrast beside it**, and marked as open for Phase 3. Not as a defect, not as a caveat in prose — as a number with a number to compare it against.

This is the one finding in Phase 2 that changes what the project can claim, and the report is where an examiner will meet it. **Better there, stated by you, than found by them.**

## T4 — Reproducible and dated

The report is **regenerated from a run, not stored**. Someone must be able to run the command after Phase 3 and get a different, current answer — that is the difference between a verification tool and a snapshot that ages into a lie.

**Stamp it** with what produced it: seed, tier, scenario, arms, and the run directory. A trust report that cannot say which run it describes is describing nothing.

**And it must not write into `outputs/`** — segment 12's containment. Whatever run it reads, it reads.

## T5 — Tests

| Test | Catches |
|---|---|
| **The report names every probed mechanism** | Add a probe without adding it to the report and the test fails. **The one that keeps this honest as the system grows** |
| **A disabled mechanism appears as inert in the report** | End to end, not just in the probe |
| **No value renders as `0.0000` when it is non-zero** | R2, enforced |
| **The report writes nothing into `outputs/`** | |
| **It reports the run it actually read** | Not a default, not the last one |

**Every invariant test shown failing against corrupted input, and the corruption pasted.**

## T6 — Mutations, two, one of them yours

**Specified:** drop one mechanism from the report while leaving its probe in place. The document still reads complete — every line in it true — and the missing line is the one nobody notices. **A trust report's failure mode is omission, not error.**

**Yours.** Seven consecutive segments.

## T7 — Show it

1. T0, and the Phase 2 closing total against 95
2. **The report itself, in full.** It is the deliverable — paste it, do not describe it
3. The same report against a deliberately broken mechanism
4. Both mutations
5. **Your read, closing Phase 2: what can this project now honestly claim about its own machinery, and what can it not?** You have built every probe in it

## T8 — Hand over, do **not** commit

`git status --short`, the commit message as a copyable block, no `Co-Authored-By`, one line confirming complete and uncommitted.

---

## Constraints

| | |
|---|---|
| **Report measurements, never verdicts** | |
| **No fixed-decimal formats on unknown scales** | R2. It has already caught this project once |
| **Insufficiencies stated beside the probe** | R3 |
| **Regenerated, never stored** | |
| **Writes nothing to `outputs/`** | |
| **Prefer outside `src/`** | It is a tool, not science |
| **No dashboard work** | Phase 1 is closed; probe telemetry in the per-arm panel is Phase 3 |
| **No control-layer changes, no PSO fix** | F13, F4, F7, F8 are Phase 3. **Report; do not fix** |
| **Do not commit, do not push** | |

---

## Acceptance check

```bash
git diff --stat -- src/ tests/ scripts/
./.venv/bin/pytest
./.venv/bin/ruff check src/ tests/ dashboard/ scripts/
./.venv/bin/pytest -k "budget or statement" -s
ls outputs/                              # unchanged before and after
git status --short                       # UNSTAGED, UNCOMMITTED
```

**Paste verbatim:** T0 and the Phase 2 total · **the report in full** · the report against a broken mechanism · both mutations · every invariant test shown red · your closing read on what the project can and cannot claim.

---

## Definition of done

Green suite, artefacts pasted, the report produced and shown failing, uncommitted with the message pasted, FINDINGS appended.

**This closes Phase 2.** Then Phase 3 — the control layer gets rebuilt, and the four arms your thesis actually lives in come back.

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->

---

# FINDINGS — Segment 16

## 1. T1 — the report

One command, `./.venv/bin/python scripts/trust_report.py`. It lives in
`scripts/`, so **`src/` did not move: 2037 / 2100, delta +0, margin 63.**
Phase 2 spent 32 of its 95 in total.

```
DYNASWARM — TRUST REPORT
================================================================================================
generated  2026-09-09 21:02
run        21-02-20   class exploratory
read from  /var/folders/ms/tp0_9gpx1ks5vmyd_zqwvzdm0000gn/T/tmpa4fnl815/21-02-20
graph      geometric/200   seed 1000   60 timesteps
arms       aco, hybrid, pso

Every figure below answers ONE question: did this mechanism run.
None of them answers whether it ran CORRECTLY — an evaporation rate ten times
too high reports a large number and looks healthy. That distinction is the
whole reason this document exists rather than a line saying 'verified'.

ACO
------------------------------------------------------------------------------------------------
  mechanism                                first        last         when broken
  trail slots whose value moved            1,470          28   live  0 — table frozen
  trail mass removed by evaporation        345.3       3.767   live  0.00 — evaporation off
  slots the best ant reinforced              434         165   live  0 — deposit silent
    ! cannot detect deposit on the WRONG edges; the count is identical either way
  slots the MAX-MIN clip actually moved       1,470    2.19e+04   live  0 — bounds removed
  strongest trail over weakest             2.833       399.2   live  1.0 — no spread
  competitive arcs per visited node         3.91       7.444   live  1.0 — fully converged

PSO
------------------------------------------------------------------------------------------------
  mechanism                                first        last         when broken
  particles the flight step displaced         222         264   live  0 — swarm frozen
  particles moved by repair instead           44           0   live  0 — repair silent
    ! counts repair moves, which are not PSO's search mechanism
  mean |velocity| across the swarm        0.1119   5.112e-14   live  unchanged from random init
    ! cannot detect a frozen swarm: velocity keeps its random initial value
  personal bests improved                     93          20   live  0 — no memory
  global best improved                         7           0   live  0 — no global memory
  mean spread of priorities               0.1274   2.927e-13   live  0.0 — swarm collapsed

HYBRID
------------------------------------------------------------------------------------------------
  Its ACO and PSO components report through the sections above — the Hybrid's
  probe carries their fields prefixed, so they are the same measurements, not copies.
  mechanism                                first        last         when broken
  budget share ACO actually spent            0.5         0.5   live  1.0 — one side got nothing
  evaluations ACO actually spent             150         150   live  0 — component silent
  evaluations PSO actually spent             150         150   live  0 — component silent
  exchanges that fired this step               1           1   live  0 — components never meet

F13 — PSO VELOCITY, OPEN FOR PHASE 3
------------------------------------------------------------------------------------------------
  under disruption   0.1119  ->  5.112e-14   (60 timesteps)
  in isolation       ~1.4e-02, stable, measured over the same horizon

  Reported as a measurement, not a verdict. The flight step still runs and still
  displaces particles, by amounts near the limit of float resolution. Whether that
  is convergence working or exploration failing is Phase 3's to answer, and it
  comes before the inertia decision in §17.1 rather than beside it.

```

## 2. R2 — the formatter is part of the instrument

`scale()` never applies a fixed-decimal format to a quantity whose scale it
does not know:

```python
if value == 0:                       return "0"
if 1e-3 <= abs(value) < 1e6:         return f"{value:,.4g}"
return f"{value:.3e}"
```

`5.112e-14` renders as `5.112e-14`. Under `:.4f` it renders as `0.0000`, which
is the claim this phase exists to make honestly, and which I nearly published
last segment while looking for exactly that error.

**Enforced, not remembered:** `test_no_value_renders_as_a_manufactured_zero`
scans every line of the rendered document — table *and* F13 — for `0.0000`.

## 3. R3 — the insufficiencies sit beside the probes

Three, on the line directly below the mechanism they qualify, and asserted to
be there by `test_the_report_carries_its_blind_spots_beside_the_probes`:

- **`speed_mean` cannot detect a frozen swarm** — velocity keeps its healthy
  random initial value
- **`tau_deposited` cannot detect deposit on the *wrong* edges** — the count is
  identical either way
- **`particles_repaired` counts repair moves**, which are not PSO's search

And at the top of the document, not buried:

> Every figure below answers ONE question: did this mechanism run. None of them
> answers whether it ran CORRECTLY — an evaporation rate ten times too high
> reports a large number and looks healthy.

## 4. T3 — F13, as a measurement with its contrast

```
F13 — PSO VELOCITY, OPEN FOR PHASE 3
  under disruption   0.1119  ->  5.112e-14   (60 timesteps)
  in isolation       ~1.4e-02, stable, measured over the same horizon
```

Stated as a number with a number beside it, marked open, and placed where an
examiner meets it rather than in a footnote. **Better there, stated by us.**

**A second reading supports it, and it was not asked for.** `diversity` — the
swarm's spread of priorities — runs `0.1274 → 2.927e-13` over the same run, and
`swarm_best_updates` goes `7 → 0`. Velocity, spread and global-best improvement
all collapse together. That is a coherent picture of a swarm that has stopped
searching, rather than one number that might be an artefact.

## 5. T5 — the tests, and what they caught while being written

**`test_the_report_names_every_probed_mechanism` found two real things
immediately**, which is the point of writing it against the fields a run
actually emits rather than against a list:

- Four fields were genuinely unclassified — `tau_active`, `tau_min`, `tau_max`,
  `speed_max`. They are **scale**, not mechanism: they give the other numbers a
  size to be read against and answer nothing on their own. Now declared as such
- The Hybrid's inherited fields (`hybrid.aco_tau_changed` and friends) were
  reported as missing. They are not — the prefix-wrapper means they *are*
  `aco.tau_changed`, reported under the arm that owns the mechanism. **The
  report now says so on the page**, so a reader does not go looking for a
  Hybrid section that duplicates ACO's

**One precedence bug in my own checker, worth recording.** Splitting every
`aco_`/`pso_` prefix filed `hybrid.aco_spent` under ACO — but that is the
Hybrid's *own* field about ACO, not an inherited one. Direct match now comes
first. Two fields that look identical in shape mean different things, and the
rule that tells them apart is which table declares them.

## 6. Both mutations, and a third

**A — specified: a mechanism dropped from the report, probe left in place.**

```
E  probe fields emitted but absent from the trust report:
   ['aco.tau_clamped', 'hybrid.aco_tau_clamped']
```

Caught. The document still read complete and every remaining line was true.

**B — mine: the formatter guard applied to the table but not to F13.**

```
E  a value was flattened to zero:
   '  under disruption   0.1543  ->  0.0000   (60 timesteps)'
```

Caught — because the zero-check scans the rendered document rather than the
table alone. Worth noting that F13 is rendered by a **different code path**
from the table, so a guard applied only where the numbers are dense would have
missed the one line an examiner reads most closely.

**C — mine: a whole arm dropped from the run.**

Two tests failed, so it was caught — **but by the F13 test and the blind-spot
test, both of which happen to need PSO's fields.** Nothing named for arm
coverage objected. Rewrite either for its own reasons and an entire optimizer
could vanish from the trust report unremarked.

**That is segment 12's ledger again**: caught by a neighbour, not by the test
that should own it. Now explicit, and failing by name:

```
E  AssertionError: pso has declared mechanisms but no section in the report
```

**Eight consecutive segments.**

## 7. Acceptance

| Check | Result |
|---|---|
| Suite | **394 passed, 0 failed, 0 skipped** |
| Lint, four trees | `All checks passed!` |
| `src/` | **2037 / 2100**, delta **+0**, margin 63 |
| `outputs/` before / after | **26 / 26** |
| `tests/test_trust_report.py` | **8 passed** |

## 8. Phase 2, closed

**What can now be said, and it is narrower than "verified".**

For eleven mechanisms across three optimizers there is a number, a reading that
says live or inert, and a demonstration of what the same field reads when the
mechanism is broken. Every one of those inert readings was produced by
disabling the thing and running it, not predicted.

**What cannot be said, and the report says so on its own first page:** none of
this establishes that anything ran *correctly*. Every probe answers *did it
run*. A wrong coefficient, a wrong rate, a deposit on the wrong edges — all
report healthy numbers.

**The one thing that changed what the project can claim** is F13, and it was
found by an instrument built to look for something else. That is the argument
for Phase 2 having existed: not that it confirmed the system works, but that it
was the first thing capable of saying otherwise, and on its first run it did.
