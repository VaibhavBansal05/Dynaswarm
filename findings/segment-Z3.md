# FINDINGS — Segment Z3

> Archived from `currentWorkFlow.md` by the Architect, 17 Sept 2026.

---

## FINDINGS — Segment Z3

**Status:** COMPLETE. Uncommitted.

### T0 — both surfaces

| | Before | After |
|---|---|---|
| Python suite | 518 passed | **520 passed** |
| JS suite | 52 passed | **53 passed** |
| `src/` statements | 2306 | **2318** across 42 files |
| `dashboard/static` JS | 920 lines | **921 lines** — reported, not capped |
| `ruff` | clean | clean |

Environment rule honoured: no leftover server, no leftover headless
browser. (The Chrome processes on this machine are Rudra's own — no
`--headless` flag — and were left alone.)

---

### T1 — implemented, with all three additions

The measurement and ruling are in Entry 028. What landed:

**1. The mean is restricted to `damage > 0`, and the count travels with
it.** On a real five-arm race the metric now discriminates:

```
  arm                                 recover   dmg  none  help  cens
  hybrid_adaptive                        1.00     2     3     3     0
  hybrid_direct                          0.50     2     5     1     0
  hybrid_fixed                           1.00     2     5     1     0
  hybrid_scheduled                       2.00     2     5     1     0
  A* (reference)                            —
```

Against `0.25 / 0.12 / 0.25 / 0.50` before — values that were all near
zero because ~80% of the population were non-events.

**A\* now reads `—` rather than `0.00`, and that is a correctness fix in
its own right.** A\* is never damaged, so it has no recovery time. The old
`0.00` asserted that the oracle *recovers instantly*, which is a claim
about an arm that never falls.

**2. `damage < 0` is counted separately.** The `help` column above is not
decoration: `hybrid_adaptive` had **3 disruptions that improved its
excess** against 1 for the other arms. That was previously merged into
"undamaged" and invisible.

**3. The damaged count is on the tab**, rendered as `1.00 (2)` with a
tooltip giving the full split, and styled with the same warning colour as
the censored dagger when the count is below five.

The two aggregation rules compose without interacting, and the docstring
says why: an undamaged disruption can never be censored, because if
`damage <= 0` the excess never rose above the band and `recovery` is 0 at
the disruption step itself. So excluding undamaged events keeps every
censored one.

Entry 028's defence of conditioning on an outcome is recorded in the code
where someone will meet it.

---

### T2 — the staleness row now discriminates

**Chosen summary: peak, and the count of non-zero steps.** Defended
against the alternatives:

- A `!` caveat alone would have declared the blind spot without removing
  it — the row would still print `0 0` beside a broken-value of `0.00`.
- Peak alone moves, but says nothing about how often the signal fires,
  which for a signal that is zero 80% of the time is the more informative
  half.

The row reads, alive and dead:

```
alive:  share of trail mass that died this step   0.2195      3   live
dead:   share of trail mass that died this step        0      0   INERT
```

The columns mean something different from the rest of the table, so the
row carries a `!` line saying so — an unexplained column change is its own
kind of misreading. The `when broken` text was updated to match the new
summary: `peak 0 over 0 steps — no invalidation ever seen`.

---

### T3 — F13 retitled, and it is not a text edit

```
F13 — PSO VELOCITY COLLAPSE: UNEXPLAINED. PHASE 3 CLOSED WITHOUT ANSWERING IT.
```

The section now records four things it did not: that Phase 3 closed
without picking this up and nobody owns it; that segment 18 fixed the
memory wipe and **did not** explain the collapse, which survived the
repair; that `WALKTHROUGH` Part 11's pre-fix reading of `~1e-14` against
today's `2.78e-04` is **ten orders of magnitude** and the clearest single
piece of evidence that segment 18 worked; and its bearing on Claim 1.

That last one matters most and the numbers are pulled live, not quoted:

```
      personal bests improved   93  ->  0
      global best improved      7  ->  0
      spread of priorities      0.1274  ->  3.688e-04
```

PSO ends a run effectively idle, so **part of the Hybrid's margin over
PSO-alone is that ACO is still working.** Any claim that the hybrid beats
its components has to say so, or it credits the architecture with a
result belonging to one half of it.

---

### T4 — the evidence tree is closed to the browser

`SCRATCH = ROOT / "dashboard-runs"`, gitignored. `race()` and
`_run_directory()` default to it; `run_classes()` still reads `outputs/`
on purpose, because that endpoint answers "what has been run" and the
CLI's runs are the ones that matter.

`conftest.py` names the carve-out explicitly rather than relying on the
two directories not overlapping — *a decision that exists only because two
paths happen not to collide is one nobody can find later*, and if the
dashboard is ever pointed back at the evidence tree the guard must still
fire.

The test drives `TestClient`, not `race()` directly, because **the defect
was in the endpoint's default and not in `race()`** — which has always
accepted a root. A direct-call test would have passed throughout. It also
asserts the run landed *somewhere*, so it cannot pass by nothing running.

---

### T5 — instance characterisation, and it corrects Entry 026

```
  model              n  bridges   hops  on bridges  route cost  % cost on bridges
  geometric        200        0     11           0       99.96          0.0%   <- seed 1000
                              1                                          0.0%   median of 8
                                                                        45.3%   worst seed
  erdos_renyi      200        0      7           0      166.50          0.0%   (all seeds)
  grid             400        0     38           0     3800.00          0.0%   (all seeds)
  geometric       1000        0      8           0       88.59          0.0%   (all seeds)
```

Per seed at `medium200`:

```
  seed  1000: bridges 0   share  0.0%        seed    42: bridges 2   share  0.0%
  seed  1001: bridges 0   share  0.0%        seed  9999: bridges 1   share 45.3%
  seed  1002: bridges 1   share  0.0%        seed   123: bridges 1   share  0.0%
  seed     7: bridges 0   share  0.0%        seed   555: bridges 1   share 42.5%
```

**Answering the four questions.**

1. **How many bridges:** 0–2 at `medium200`, median 1. `grid` has none by
   construction, which is the control the spec predicted and it behaves.
2. **What fraction of the optimal route sits on them:** median **0%**, but
   **2 of 8 seeds (9999 and 555) put ~45% of the route cost on a single
   bridge hop.** So the mechanism is real and occasionally severe.
3. **Is seed 1000 typical:** yes for this property, and at the benign end
   — **it has zero bridges.**
4. **By model:** only `geometric` produces them at all.

**The correction, and it matters because a ruling was built on it.**
Entry 026 attributed Rudra's 87.228 road to `_ensure_connected`. For
`medium200` seed 1000 that cannot be so:

```
  raw geometric edges: 735   after connect: 735   bridges added: 0
  is (63,125) an edge?  False      slot: -1
  euclidean distance 63-125: 0.529   canvas spans: 0.99
  longest edge on the optimal route: 11.59  =  11.6% of the 99.96 cost
```

**The pair is not in the CSR superset at all** — not a base edge, not an
addable-pool slot — and no single edge on that route carries more than
11.6% of its cost. So the road Rudra saw came from a different instance
than the default one: another tier, density, or a re-rolled seed. **I
could not reproduce it and am not going to explain it away.**

**What survives the correction is the important half.** The competing
explanation — *arms look alike because the problem is "reach the bridge"*
— is **not present at the default instance**, but it is live on roughly a
quarter of seeds. At 100 seeds that is ~25 instances where it applies.
**Recommendation for the manifest:** record bridge count and bridge share
per instance, so the analysis can test whether arms converge more on
bridge-dominated instances rather than assuming either way. The generator
is untouched.

---

### T7 — both mutations, and the specified one exposed a weak test of mine

**Specified** — make the sparse row read its broken value while alive.

*Actual:* **passed all 9 trust-report tests on the first attempt.**

My test compared the whole rendered row, and the rows still differ by
`live` against `INERT` even when both numbers read `0`. **That is exactly
the defect Entry 026 described** — the verdict column was always correct,
and the numbers beside it discriminated nothing. My test was checking the
half that already worked.

Fixed to compare the two numeric fields with the verdict stripped, then
shown red:

```
E  AssertionError: the two reported values are identical whether the
   mechanism is alive or dead: ['0', '0']. The verdict word may differ,
   but the numbers a reader compares against `when broken` do not
```

**Mine** — render `n_disruptions` instead of `n_damaged` in the tab's
recovery cell.

*Predicted:* passes everything. The payload test asserts both keys exist;
nothing asserted which one reaches the screen. It reads as a naming slip.

*Actual:* **passed the entire Python suite and all 52 JS tests.** The cell
would read `0.50 (8)` instead of `0.50 (2)` — making a mean over two
observations look four times better evidenced, which defeats the exact
purpose Entry 028's third addition was added for.

Closed with a **render assertion** in `tests/js/` — driving the real
`drawScore` through the harness and reading the cell — not a source grep.
The fixture is generated **through the real API** rather than by
`json.dumps`, which mattered: raw `json.dumps` emits bare `NaN`, invalid
JSON that `JSON.parse` rejects, while FastAPI correctly serialises it as
`null`. A hand-written fixture would have differed from reality in a
second way. Shown red:

```
E  the recovery cell reads "0.50 (8)" but only 2 disruptions damaged this
   arm. Showing 8 makes the mean look 8x better evidenced than it is
```

---

**Files changed**
- `src/dynaswarm/analysis/scoring.py` — `RecoverySummary`; damaged-only mean; improved/unchanged split
- `scripts/trust_report.py` — `SPARSE_FIELDS`; the F13 section
- `dashboard/server.py` — `SCRATCH`; races relocated
- `dashboard/static/app.js` — damaged count on the tab; `drawScore` exposed to the harness
- `tests/conftest.py` — the carve-out, by name
- `tests/test_scoring.py`, `tests/test_trust_report.py`, `tests/test_dashboard.py`, `tests/js/app.test.mjs`, `tests/js/dom.mjs`
- `.gitignore` — `dashboard-runs/`

**Files added**
- `scripts/instance_characterisation.py` — T5
- `tests/js/fixtures/score.json` — generated through the API

**Surprises**
1. **Entry 026's bridge diagnosis does not hold for seed 1000** — that
   instance has zero bridges and the named edge does not exist in it.
2. **A\* was claiming instant recovery** from disruptions that never
   touched it. Fixed as a side effect of T1.
3. **The specified mutation passed**, because my test compared a row that
   differed only in the column that was never broken.
4. **`json.dumps` emits invalid JSON for NaN** and FastAPI does not — a
   fixture built the convenient way would not have matched the browser.

**Questions for the Architect**

1. **Where did Rudra's 87.228 road come from?** It is not in `medium200`
   seed 1000. If he re-rolled the seed or changed the tier, the instance
   should be identified before the report repeats the explanation.
2. **Record bridge count and share per instance in the manifest?** ~25 of
   100 seeds will carry the property; recording it costs nothing now and
   cannot be recovered later.
