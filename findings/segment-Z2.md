# FINDINGS — Segment Z2

> Archived from `currentWorkFlow.md` by the Architect, 17 Sept 2026.

---

## FINDINGS — Segment Z2

**Status:** COMPLETE. Uncommitted.

### T0 — both surfaces

| | Before | After |
|---|---|---|
| Python suite | 505 passed, 1 failed | **514 passed** |
| JS suite | 52 passed | **52 passed** |
| `src/` statements | 2292 | **2306** across 42 files — reported |
| `dashboard/static` JS | 920 lines, **capped at 900 (failing)** | **920 lines, no cap** |
| `ruff` | clean | clean |

**`MAX_JS_LINES` is deleted** (Entry 025), not raised. The budget test now
prints the count per file and asserts only that the walker found
something. `MAX_PRESENTATION_LINES` survives and is documented as a
different question: markup and styling do not execute, so they cannot
disagree with the engine.

---

### T1 — what is timed, and the rebind ruling

**`wall_ms` covers `spend()` and nothing else** — the search. Not the
rebind, not `best()`, not `probe()`, not row construction, not the
parquet write. `time.perf_counter()` throughout, which is monotonic.

**The oracle was already excluded and now that is provable.**
`shortest_path` runs once per timestep at `trial.py:158`, *outside* the
arms loop, so no arm's total can carry it. It is now timed into its own
`oracle_ms` column, which makes the exclusion checkable from a recorded
run rather than by reading the loop.

**Ruling on rebind: timed, but in its own column.**

Argued both ways. *For inclusion:* rebind is real work an arm must do to
function, a deployed system pays it, and the arms pay different amounts —
ACO zeroes trails, PSO guards on `state_hash`. Excluding it understates
the true cost. *Against:* it is driven by the environment changing, not
by the search budget, so folding it into `wall_ms` conflates "what the
budget buys" with "what the disruption costs", and §10.2's fairness
guarantee is about equal *search*.

Neither answer is wrong, so I refused the either/or: `rebind_ms` is
recorded separately. The report can quote search cost, total cost, or
both, and the ledger attributes it explicitly instead of burying it in
overhead. What must not happen is the two being silently mixed, and
`test_rebind_is_recorded_separately_from_the_search` fails if they are.

---

### T2 — the time ledger

Per timestep: **arms + rebind + oracle + overhead == the measured
timestep**, where the timestep total comes from **its own clock** around
the whole loop body, not from summing the parts.

```
t=0  step   88.80ms = arms   85.75 + rebind  0.67 + oracle  0.47 + overhead  1.90  ( 2.1%)
t=1  step   50.68ms = arms   47.77 + rebind  0.75 + oracle  0.43 + overhead  1.73  ( 3.4%)
t=2  step   46.91ms = arms   43.97 + rebind  0.73 + oracle  0.42 + overhead  1.78  ( 3.8%)
```

**Overhead fraction: 2–4%.** Small enough that the timers cover the right
region; reliably non-zero, which is the evidence that the total is
measured rather than derived. `test_the_ledger_is_not_a_tautology`
asserts that non-zero residual directly — if `step_wall_ms` were ever
computed from the parts, the identity would balance forever and the
whole ledger would be checking nothing.

#### The red case, and the first attempt at it failed

Starting the arm timer before `rebind` — so rebind is counted once in
`rebind_ms` and again inside `wall_ms` — **passed all six timing tests.**

At 200 nodes with a 300-evaluation budget, rebind is 0.75ms against a
46ms timestep. Doubling it moves the residual by 1.6% and vanishes inside
the tolerance. **A tolerance-based identity can only catch a double-count
larger than the true overhead**, and I had written one that could not
fail on its own fixture.

Rebind cost scales with the graph; search cost scales with the budget.
So the detector has to run where the doubled quantity is material:

```
  n=  200 budget= 300: step   46.16ms  rebind  0.75 ( 1.6%)  residual  3.5%
  n= 1000 budget= 300: step  464.11ms  rebind 17.05 ( 3.7%)  residual  2.7%
  n= 1000 budget=  20: step   65.12ms  rebind 16.90 (25.9%)  residual 16.6%   <- here
  n= 2000 budget=  10: step  202.33ms  rebind 70.51 (34.9%)  residual 12.7%
```

At 1000 nodes / 20 evaluations, rebind is 26% of the timestep against a
17% residual, so counting it twice drives the residual **negative**.
`test_the_ledger_catches_a_double_count_where_the_doubled_part_is_material`
runs there, and first asserts the fixture still has rebind above 10% of a
timestep — a detector whose own preconditions have drifted is a detector
that cannot fail. Shown red:

```
E  AssertionError: t=0: parts sum to 71.81ms against a measured 59.94ms
   timestep — something is counted twice
```

This is the standing rule applied to the ledger itself: *a test of a
feature runs on data where the feature is active*, and the feature here
is **detection**.

---

### T3/T4 — the three-size table

```
PER-ARM SEARCH TIME PER TIMESTEP
  machine: Apple M2 | Darwin 25.0.0 | Python 3.13.0
  5 repeats per size; median of per-run medians, spread = half the min..max range

  size                    astar              aco              pso           hybrid     oracle
  -------------------------------------------------------------------------------------------
  small            0.02 ± 0.00     1.46 ± 0.04     2.50 ± 0.08     2.17 ± 0.05      0.025
                all metered arms separated at this size
  medium200        0.40 ± 0.00    10.44 ± 0.26     6.84 ± 0.06    13.65 ± 0.06      0.410
                all metered arms separated at this size
  large1000        3.22 ± 0.03   114.68 ± 1.07    16.90 ± 0.06   106.08 ± 0.77      3.273
                all metered arms separated at this size
```

One machine, named in the artefact. The script checks for overlapping
spreads and would print "NOT distinguishable" rather than let a row be
read as an ordering; at these three sizes the metered arms are separated.

---

### T5 — what this table is allowed to claim

**A\* is faster than every metered arm at every size tested, by one to
two orders of magnitude**, and it is exact. 0.02ms against 1.46–2.50 at
small; 0.40 against 6.84–13.65 at medium; 3.22 against 16.90–114.68 at
large. **No arm is cheaper than A\* at any size**, and that is reported
in the same words it would have been if the result had gone the other
way.

Two things the table shows that are worth the report's space, neither of
them a claim about the thesis:

- **ACO scales badly with graph size** — 1.46 → 10.44 → 114.68ms, roughly
  an order of magnitude per tier, while PSO goes 2.50 → 6.84 → 16.90.
- **The Hybrid tracks ACO, not PSO** (106.08 against 114.68 and 16.90 at
  large). Its cost is dominated by its more expensive half, which is the
  kind of thing an allocation argument has to account for.

The units are not comparable in the abstract — one evaluation builds a
whole path, one A\* step pops a node — so wall-clock is the only common
currency, and the script says so in its own output.

---

### T7 — both mutations. **Both of my predictions were wrong.**

**Specified** — timer wraps rebind, search and bookkeeping.

*Predicted:* every arm gains roughly the same fixed overhead, compressing
the ratios, so the arm doing the least real searching (A\*) is hurt worst
and the slow arms are flattered.

*Actual:* **every arm inflated by the same 1.1×.** The added work is
*proportional* to the arm, not constant — rebind scales with the arm's own
state and so does `probe()`. So every ratio survives intact and only the
absolute numbers are 10% high.

**That is worse than what I predicted, not better.** A reader comparing
arms draws entirely correct conclusions; a reader quoting an absolute
number is wrong by 10%, and nothing in the table looks odd. Caught by two
ledger tests (parts exceed the whole; residual never positive).

**Mine** — rotate `wall_ms` attribution *within* a timestep, so each arm
records the previous arm's duration.

*Predicted:* passes everything, because the multiset of durations is
unchanged, so every sum is identical and an identity over a sum is
structurally blind to it.

*Actual:* **passed all 513 tests.** Confirmed. At 1000 nodes:

```
   astar    evaluations    0   true    3.22ms -> REPORTED  122.38ms
   aco      evaluations  300   true  114.68ms -> REPORTED    3.28ms
   pso      evaluations  300   true   16.90ms -> REPORTED  198.07ms
   hybrid   evaluations  300   true  106.08ms -> REPORTED   17.01ms
```

**A\* spends zero evaluations and reports 122ms; ACO spends 300 and
reports 3ms.** Every number is in a believable range, the ledger balances
to the same residual, the overhead fraction is identical, and the entire
cost story is inverted. This is F1's shape in the timing layer: correct
values, wrong owner.

Closed by `test_recorded_time_is_consistent_with_recorded_work`, which is
a **cross-column** check rather than another identity: an arm that spent
no evaluation budget did no search and cannot have taken longer than one
that spent the whole of it. Deliberately a loose bound, not a ranking —
the table reports ordering, with spreads, and this only refuses an
attribution that contradicts the work recorded on the same row.

**The lesson generalises past this segment.** The ledger proves the total
is right. It cannot prove any individual number is. Those need a
different kind of check, and a suite can have a balancing identity and
still be blind to every row being wrong.

---

### ⚠️ The intermittent error, diagnosed — and it was mine, not the code's

The suite reported `514 passed, 1 error` in roughly one run in five.

**Answering the three questions directly.**

**(1) Intermittent, not consistent.** Eight full runs: seven clean, one
error. There is no randomisation plugin — `addopts` is `-q
--strict-markers` and ordering is deterministic — so test-order shuffling
was never the mechanism.

**(2) The full traceback puts it in TEARDOWN, not setup or body:**

```
___________ ERROR at teardown of test_a_hybrid_can_actually_be_tuned ___________
    @pytest.fixture(scope="session", autouse=True)
    def outputs_is_read_only():
        before = _snapshot()
        yield
        appeared = sorted(_snapshot() - before)
>       assert not appeared
E       AssertionError: the test suite wrote into outputs/, the evidence tree:
E           2026-09-17/10-58-26
E           2026-09-17/10-58-26/events.parquet
E           2026-09-17/10-58-26/manifest.json
E           2026-09-17/10-58-26/steps.parquet
tests/conftest.py:41: AssertionError
```

It is `conftest.py`'s session-scoped containment guard. It is attributed
to the tuning test only because that test happens to be last — the
fixture tears down there. **The tuning test is not implicated at all.**

**(3) The shared-state hypothesis is clean, and I checked it properly
because the consequence for segment 24 is serious.**

- `trial.py` has exactly two module-level names: `__all__` (a list of
  strings, never mutated) and `_COST_TOL` (a float).
- **No function attributes and no `global` statement anywhere in `src/`.**
- Every timing variable — `step_started`, `oracle_started`,
  `rebind_started`, `wall_ms`, `rebind_ms`, `oracle_ms`, `step_wall_ms` —
  is local to `run_trial`.

So the timing path carries no state across trials and is safe under
`parallel_jobs`. The `run_trial._carry` function attribute the Architect
flagged was scaffolding inside my own mutation and never existed in
committed source; it is reverted.

**The actual cause: my own leftover processes.** I left the dashboard
server running from the screenshot work, and a headless Chrome still
pointed at `?demo=1`. That deep-link auto-runs a race, which POSTs to
`/api/run` — and **`api_race` takes no `root` parameter, so it writes to
the default `OUTPUTS`**. Whenever one of those late requests completed
inside a pytest session, a new run directory appeared mid-session and the
guard fired. Both processes killed.

**Two things worth keeping from this.**

First, **the guard worked exactly as designed.** `conftest.py` exists
because 25 run directories once accumulated in `outputs/` in a single
afternoon, one of them stamped `manifest`. It caught a real intrusion
into the evidence tree from a direction nobody had anticipated — a
browser, not a test.

Second, **I left dead code in the timing path** — a `timings` dict
written on every arm and never read. Found while auditing for shared
state, removed. It was harmless, and it was exactly the shape the audit
was looking for.

**A recommendation I have not acted on**, because it changes an endpoint
and this segment is not scoped to it: `/api/run` writing to the live
`outputs/` by default is the hole that let this happen. `race()` already
takes a `root`; the HTTP layer does not expose it. Worth a ruling before
segment 24, since the evidence run and a curious browser currently share
a directory.

---

**Files changed**
- `src/dynaswarm/harness/trial.py` — `rebind_ms`, `step_wall_ms`, `oracle_ms`; the timestep's own clock
- `src/dynaswarm/io/schema.py` — the three columns
- `tests/test_harness.py` — the new clocks excluded from bit-reproducibility, as an explicit list not a suffix rule
- `tests/test_dashboard.py` — `MAX_JS_LINES` deleted; the budget test reports

**Files added**
- `tests/test_timing.py` — 8 tests
- `scripts/timing_table.py` — T3/T4

**Deviations from spec**
1. **Rebind is recorded in its own column** rather than being ruled in or
   out of `wall_ms`. The spec asked me to pick one; I think the either/or
   loses information the report needs, and the ledger attributes it
   explicitly either way.

**Surprises**
1. **My first red case was not red.** A tolerance-based identity cannot
   catch a double-count smaller than its own overhead.
2. **The specified mutation preserved every ratio**, inflating all arms by
   the same 1.1× — plausible in a way a constant offset would not be.
3. **The ledger is structurally blind to attribution.** It checks a sum,
   and rotating the owners leaves the sum exact.
4. **A browser wrote into the evidence tree.** The containment fixture
   caught it; the endpoint that allowed it is still open.

**Questions for the Architect**

1. **Should `/api/run` accept a run root, or refuse to write to `outputs/`
   at all?** See above — relevant before segment 24.
2. **Is `rebind_ms` as a separate column accepted**, or do you want a
   single ruling folded into `wall_ms`?
