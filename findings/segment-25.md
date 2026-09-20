## FINDINGS — Segment 25

**Status:** COMPLETE. Uncommitted. No new run; no report; `paper.tex` and
`docs/presentation.md` untouched.

### T0 — both surfaces

| | Before | After |
|---|---|---|
| Python suite | 536 passed, **1 failed** | **543 passed** |
| JS suite | 53 | 53 |
| `src/` statements | 2318 | 2318 |
| ruff | clean | clean |

**The failure was caused by the evidence run existing.**
`test_run_classes_does_not_filter_to_manifest` asserted *"no manifest runs
exist; see D31"* — a fact segment 24 was commissioned to make false.
`run_classes()` now returns `{'manifest': 720000, 'exploratory': 15256}`.
The rule it guards (D30: this endpoint must not filter, or the page goes
blank) is untouched and is what it now asserts. The test had encoded a
fact about the world instead of the rule it was protecting.

---

### T0b — re-deriving `FINDINGS_TESTS.md` from the rows

Everything checked. **Three disagreements, and one of them was mine.**

| claim | verdict |
|---|---|
| 720,000 rows, 24 chunks, 30,000 each | **confirmed** |
| `n` = 150 in all 34 cells, both tiers | **confirmed** (68 cells checked) |
| the 34-cell grid: delta, p, p_adj, effect | **confirmed — zero disagreements** |
| damaged-event counts §5 | confirmed **after fixing a bug in my re-derivation** |
| `large1000/severe` ranking, all 6 values | **confirmed** |
| §6a Pareto defect | **confirmed at both tiers**, but the quoted example is `large1000`-only |
| §6b sign disagreement | **confirmed**, all four cells |
| §6c `% at optimum` degenerate | **WRONG as stated — 1 of 4 scenarios, not 3** |
| §6d floor included `calm` | **confirmed**, and a second defect found beneath it |
| §7 `events_this_step` | **confirmed**, with one imprecision |

**The bug was mine and it is worth recording.** My cache stored excess as
`to_numpy(dtype=float)`, turning `None` into `NaN`. `recovery.disruptions()`
guards with `v is None`, which a NaN slips past, so a NaN baseline
propagated and the damaged counts came out 1–8 events low. `large1000`
matched exactly and only `medium200` disagreed — because `large1000` has
**zero** unroutable steps and `medium200/severe` has **169**. The
asymmetry is what identified it as mine rather than `analysis.txt`'s.

**§6c is wrong.** Re-derived per arm, every arm reads 0.0% at optimum in
**one** scenario (`calm`), not three. Maxima at light/moderate/severe are
0.16%, 0.58%, 0.59%. The metric is near-degenerate, not degenerate; the
ruling to read it from `medium200` stands on the corrected figure.

**§6a's example is tier-specific.** The quoted `hybrid_direct` 2.44% vs
`aco` 13.33% are `large1000` numbers, presented without naming the tier.
At `medium200` the pair reads 4.16% vs 4.92% and `hybrid_direct` does
**not** dominate. The defect is real at both tiers — 33 and 13 dominance
relations respectively over the defined metrics — but that illustration
holds at one.

**§7 is correct.** `events_this_step` is on the observation at
`observation.py:75`, neither sensing policy reads it, and the quoted
docstring lines are verbatim. One imprecision: *"both read `obs.recency`
and nothing else"* is exact for `DirectAllocation` and loose for
`IncrementalAllocation`, which also reads `current_fraction` and `t`. The
substantive claim holds for both.

---

### T2 — the upper bound on every null `PRE-REGISTERED`

Entry 024 promised it; there was no interval anywhere in the output.
95% bootstrap CI on the paired difference, 4,000 resamples, raw excess
scale.

At `large1000`, any sensing benefit is bounded under **0.3 percentage
points of excess**, and at `severe/P1` the data supports **no advantage
at all**.

**The widest bound belongs to Claim 2.** P4 at `large1000/severe` cannot
rule out a **1.07 pp** benefit from adapting ρ. *"Not significant"* and
*"cannot help by more than a point"* are different statements and only
the second is what the run established.

---

### T3 — conditioning on bridge share `PRE-REGISTERED`

Entry 029 promised it. Split at **10%**, the threshold already fixed in
that entry rather than chosen after seeing both answers.

| half | seeds | Claim 3 cells significant |
|---|---|---|
| low bridge ≤10% | 87 | **0 of 19** |
| high bridge >10% | 63 | **0 of 19** |

**The null survives its most obvious challenge, with data.** `large1000`
has zero bridges on all 150 instances and shows the same null, so two
independent answers agree. Claim 1 also survives both halves — and
`hybrid` vs `aco` is significant on the low-bridge half but not the
high-bridge one, consistent with a dominant bridge making arms alike.

---

### T4–T6 `EXPLORATORY`

**T4 — the mechanism works.** `hybrid_fixed` never moves (0.000 travel,
so the ablation pair differs in exactly one thing); every other arm moves
on ~58 of 60 steps. `hybrid_direct` is **clamped on 75%** of its steps,
confirming segment Y's 78% measured at n = 1. This separates *"the
mechanism works and the benefit is not there"* from *"the mechanism was
broken"* — it is the former.

**T5 — Entry 032 is half-confirmed, and needs correcting.** The signal
does saturate monotonically with the event rate (0.000 → 0.095 → 0.259 →
**0.539** of steps at exactly 1.0). It does **not** approach 1.0:
*"the arms steer on a constant"* is not what 54% describes. Direction
right, magnitude overstated.

**T6** — recovery per arm with n (all clear the floor of 30), availability
(≥99.68% everywhere, never a real problem), churn (the four hybrids
indistinguishable), timing at n = 150 with the throttling caveat, and win
counts (`large1000/severe` P3a: the adaptive arm wins **47 of 150**).

---

### T7 — the four defects

**7a Pareto at `calm`: confirmed, fixed.** An undefined metric returned
"not comparable" from both helpers, so no arm could dominate any other
and the tab printed *"the arms are not distinguishable"* — the null —
in the scenario built as a negative control. Now judged over the metrics
both arms have, with the count named in the output. Two tests.

**7b sign disagreement: confirmed, not a bug.** Demonstrated on
`calm/S2a`: mean **+0.0036**, median **−0.0044**, hybrid wins **90 of
150**, skewness **+2.31**, four seeds at +11 to +23 pp. A mean is
skew-sensitive and Cliff's delta is not; they answer different questions.

**7c: the ruling stands on a corrected fact.** See T0b.

**7d: two defects, not one.** The floor fired on `calm` — where zero is
the designed outcome — and, not previously noticed,
**`MIN_DAMAGED_FOR_RECOVERY` is a per-arm floor and the caller passed
totals over ten arms.** `large1000/light` arrived as 117 against a floor
of 30 and passed, when its real per-arm count is 11.7 and it fails by a
factor of three. A units mismatch made the threshold **ten times more
lenient than it reads**. Both fixed; one test drives both branches.

---

### T8 — my mutation

Stripped the `EXPLORATORY` tag from §7, the section explaining *why* the
null happened. **It passed all 543 tests**, because nothing read
`FINDINGS_TESTS.md`. Presented as pre-registered, that section reads as
though the null had been predicted rather than discovered.

Closed by `tests/test_findings_tests.py` — four tests asserting every
exploratory section says so, that only the three genuinely promised
sections claim `PRE-REGISTERED`, that no section still carries an
unverified tag, and that the scale legend survives.

The first version of the provenance test failed on a clean document: it
matched the legend sentence as if it were a tag. A check that cannot tell
a tag from a word naming the tag is not checking provenance.

---

### The cold read

Read start to finish as a stranger, the file failed in six places, all
the same kind: **names used before they mean anything.** `hybrid_adaptive`
first appeared in a table on line 170 with no description anywhere;
`calm/P1` appeared 64 lines before P1 was defined; `medium200` was never
mapped to 200 nodes; the scenario event rates were absent; `governor` and
`chunk` were used undefined.

Fixed by **§0 — the setup**: all ten arms with one-line descriptions, the
four scenarios with their break rates, both tiers with node counts, all
nine comparison codes, and the two loose terms. The report is now
writable from this file alone.

---

### Does the null still say what Entry 032 says it says?

**Mostly, and one part needs correcting.**

What survives: the null is real, it is not an artefact of the instance
distribution (T3, both halves, both tiers), and the mechanism it is a
null *about* demonstrably worked (T4). Those three together make it a
finding about the problem rather than about the code.

What needs correcting: Entry 032 says the sensing arms "steer on a
constant" at `severe`. **They steer on a signal that is pinned 54% of the
time** — degraded, not constant.

And the bound changes the sentence. Entry 032 reads the null as *sensing
does not help*. What the run supports is *sensing does not help by more
than ~0.3 percentage points of excess at `large1000`* — a ceiling, not an
absence. For Claim 2 the ceiling is 1.07 pp, wide enough that "reproduced"
should be stated with it attached.

**None of this is changed by the exploratory work, and none of it may
be.** T4 and T5 explain the null. They cannot overturn it.

---

**Files changed**
- `FINDINGS_TESTS.md` — rewritten: §0 setup, T2/T3 as pre-registered sections, T4–T6 exploratory, corrections to §6a and §6c, every section tagged `[raw]`
- `src/dynaswarm/analysis/scoring.py` — 7a; `comparable_metrics()`
- `scripts/manifest.py`, `scripts/analyse_run.py` — 7d, both defects
- `tests/test_dashboard.py` — the retired-premise test
- `tests/test_scoring.py`, `tests/test_manifest.py` — 7a and 7d guards

**Files added**
- `scripts/segment25.py` — the re-derivation layer
- `tests/test_findings_tests.py` — the labelling guard

**Questions for the Architect**
1. **Entry 032 needs amending** on the saturation magnitude (54%, not ~1.0).
2. **Entries 031/033's §6c justification** rests on "3 of 4 scenarios"; the fact is 1 of 4. The ruling is unaffected, the stated reason is not.
3. **`primary_tier_holds` now has a vestigial job** — Entry 033 already sends recovery to `medium200` unconditionally, so its tier verdict decides nothing. Keep as a per-cell reporter, or retire it?
