# SEGMENT 25 — The analysis we promised, and four things the analysis file got wrong

**No new run. No report.** Everything here is a re-reading of the 720,000 rows already on disk at `outputs/2026-09-19/18-43-05`.

The report is **not** in this segment and is not to be started. It waits on Rudra's professor.

Two of these tasks are **pre-registration commitments**, not improvements. Entry 024's decision rule says a null is reported *with the bound the run establishes*; Entry 029 approved per-instance bridge recording specifically so the report could condition on it. Neither has been done. **A report that omits a bound it promised is weaker than one that never promised it.**

> Read `AGENT_PROTOCOL.md`, `WORKFLOW_LOG.md` **Entries 024 (pre-registration + three amendments), 028, 029, 031, 032, 033**, and **`findings/segment-24.md`**.
> Append your FINDINGS block to the **bottom of this file before reporting in chat.** Segment 24 was reported in chat only and the repository nearly lost it.
>
> ## ⛔ YOU DO NOT COMMIT
>
> **Rudra commits. Not you.** Unstaged. No `git add`, no `git commit`, no `git stash`, never `git add -A`.
> Finish with `git status --short` pasted and the commit message fenced — **no `Co-Authored-By`**.

---

## ⚠️ T0 — Measure, both surfaces

`pytest`, `node --test`, `ruff`, counts reported. Kill every server and browser you start.

---

## ⚠️ T0b — **The deliverable is `FINDINGS_TESTS.md`, and its current contents are unverified**

`FINDINGS_TESTS.md` exists at the repository root. **Every number in it was taken from `analysis.txt`** — a derived summary — **by the Architect, who did not open a single parquet chunk.** It is a summary of a summary and it is currently the only document anyone would consult.

That file is intended to become the single reference for the report and the deck, so that neither has to reopen `outputs/`. **A file that serves that purpose and was never checked against the data is worse than no file**, because it will be trusted exactly as if it had been.

**Before adding anything to it, re-derive its numbers from the 720,000 rows.** At minimum:

- row counts per chunk and in total
- `n` per cell, both tiers
- the 34-cell grid: `delta`, `p`, `p_adj`, effect, for every row of §4
- the damaged-event counts in §5
- the `large1000/severe` ranking table in §4
- the four defects in §6 — confirm each is real before it is written down as real
- **the `events_this_step` claim in §7** — confirm the field is on the observation, confirm both sensing policies read only `obs.recency`, and quote the lines

**Report every disagreement. Do not fix one silently.** A number that moves between `analysis.txt` and the raw rows means one of the two is wrong, and which one it is matters more than the number.

### How everything in this segment is recorded

Each result from T2 onward goes into `FINDINGS_TESTS.md` **as it is produced**, under a new section, with four parts in this order:

1. **What it means, in one or two plain sentences.** Written so a reader who has never seen this codebase understands what was asked and what came back. No arm names without saying what the arm is, no statistic quoted without saying what question it answers. **This comes first, before the number.**
2. the number, in a table where there is more than one,
3. **the command or function call that produced it**, so anyone can re-run it,
4. a provenance tag — **`[raw]`** if derived from the parquet rows in this segment, **`[analysis.txt]`** if carried over from the earlier summary and not re-derived.

**The plain sentence states what was measured and what the measurement was. It does not argue for a conclusion.** *"Adaptive did not beat fixed in any cell; the largest benefit consistent with the data is X"* is the shape. *"This shows adaptation is a dead end"* is not — that is a reading, it belongs to the report, and a reference document that embeds it will have that reading quoted back as if it were a measurement.

Where a number needs interpretation to be usable — an effect size, a p-value, a bound — say what the scale is and where the thresholds sit, once, in the sentence. A reader should never need a second document to know whether 0.100 is big.

Every existing number in the file gets a tag too. **By the end of this segment nothing in that file should still read `[analysis.txt]` unless you say why it could not be re-derived.**

The FINDINGS block in *this* file stays the segment's narrative record. `FINDINGS_TESTS.md` is the reference document. They are not the same thing and neither replaces the other.

---

## T1 — ⚠️ The labelling rule. Read this before writing any code.

Everything in T2 and T3 was **pre-registered**. Everything in T4 onward was chosen **after seeing the result**.

That is the exact shape of the P3 selection bug I introduced in Entry 024 and you caught. So:

| | |
|---|---|
| **T2, T3** | primary. Reported as pre-registered analysis. |
| **T4–T8** | **exploratory. Labelled exploratory in every table, every figure, every sentence.** |
| **No exploratory result may overturn a pre-registered one.** They explain the null. They do not replace it. | |

If an exploratory analysis produces something that looks like it changes a conclusion, **report it and say it cannot change the conclusion.** That sentence is not a hedge; it is the reason anyone can trust the pre-registered part.

---

## T2 — ⚠️ **The upper bound on the null.** Entry 024 promised this.

There is no confidence interval anywhere in `analysis.txt` — only p-values and Cliff's delta.

For every non-significant pre-registered comparison, compute a **two-sided interval on the paired difference**, on the **raw excess scale** so a reader can interpret it without a lookup table.

Then state each null in this form, with the numbers filled in:

> *`hybrid_adaptive` did not beat `hybrid_fixed`. With 150 paired seeds, any true benefit is smaller than **X** percentage points of excess — that is the ceiling this run establishes.*

**Why the raw scale and not δ:** "δ is below 0.147" tells a reader the effect is negligible by a convention. "Any benefit is under 0.4 percentage points of excess" tells them what it would have been worth. Only the second survives a viva question.

Report the bound for **P1, P2, P3a, P3b, P5 and P4 at both tiers.** Those are the nulls Claim 2 and Claim 3 rest on.

---

## T3 — ⚠️ **Conditioning on bridge share.** Entry 029 promised this.

`MANIFEST.json` carries `bridge_share` for all 150 `medium200` instances; the run carries `seed`; you verified the join is clean.

63 of 150 instances sit above 10% bridge share. On those, a single hop carries much of the optimal route and the search problem is substantially *"reach the bridge"* — so arms could look alike for a structural reason rather than because allocation does not help.

1. Split the `medium200` seeds at a threshold **stated in advance and justified** — not chosen after looking at both answers.
2. Re-run the pre-registered comparisons on each half.
3. Report both halves side by side, with n for each.

**Both outcomes are results and both go in.** If the arms still tie on the low-bridge half, the null survives its most obvious challenge with data instead of argument. If they stop tying, the null was partly an artefact of the instance distribution and the report says so. **Do not report only the half that agrees with the pre-registered result.**

`large1000` has zero bridges on all 150 instances, so the cross-tier comparison is a second, independent answer to the same challenge. Say whether the two agree.

---

## T4 — **Did the allocation mechanism actually work?** (exploratory)

This is the most valuable thing left, because it separates two very different papers:

- *the mechanism works and the benefit is not there* — a real finding about the problem
- *the mechanism was broken* — a finding about our code

**Right now nobody can tell which, and every column needed has been sitting on disk untouched.**

`alloc_proposed`, `alloc_applied`, `alloc_held_back`, `alloc_at_bound`, `aco_fraction` and `signal_value` are in the probe map on all 720,000 rows. Segment Y measured a 78% clamp rate and corr(split, recency) of −0.016 for the incremental arm against −0.239 for the direct one — at n = 1 to 6. At 150 seeds those become real numbers.

Report per arm, per scenario, per tier: **how often the policy proposed a move, how often the move was applied, how often it was clamped, how far the split actually travelled, and the correlation between the applied split and the signal.**

---

## T5 — ⚠️ **Measure the saturation.** (exploratory, and it tests the Architect's own story)

Entry 032 contains my reading: `RecencySignal` is binary, so as the disruption rate rises it saturates near 1.0, the sensing arms steer on a constant, and that is why they lose to `hybrid_scheduled` at `severe` by a margin that grows with the rate.

**That is currently a story I told. `signal_value` is on every row.**

Compute, per scenario per tier, **the fraction of timesteps where the signal reads 1.0**, and its distribution.

If it climbs light → moderate → severe and approaches 1.0 at severe, the explanation becomes a measurement. If it does not climb, **my explanation is wrong and Entry 032 gets corrected** — report that outcome exactly as readily as the other one.

This does not make the prediction pre-registered and the report will not present it as one. It moves it from narrative to evidence, which is a different and smaller claim.

---

## T6 — The metrics we built and never reported (exploratory)

- **Recovery per arm, with its n and interval**, at both tiers. Two segments were spent building this metric and it has been used only to choose a tier. `medium200` primary per Entry 031; `large1000` reported alongside with its own n, and `large1000/light` marked as below the evidence floor.
- **Availability** — `path_valid`: how often each arm held no route at all. Failing to find any route is worse than finding a poor one and it has never been counted. Directly relevant to Claim 1 at `severe`.
- **Route churn** — `path_changed`: whether the adaptive arm destabilises its own solution.
- **The timing table at n = 150** — `wall_ms`, `rebind_ms`, `oracle_ms`, with intervals. Z2's table was n = 1. **Flag the throttling:** the last three `large1000` chunks ran 20.3–23.8 s/trial against 17.3–18.6 s for the preceding nine, so wall-clock from this run is not uniform and any timing claim must say so.
- **Win counts** — "A beat B on 61 of 150 seeds." Free, already in the data, and far more legible in a viva than `p_adj = 1.0000`.

---

## T7 — ⚠️ Four defects in `analysis.txt`. Entry 033 has the detail.

**7a. The Pareto message at `calm` is false at both tiers.** It prints *"the arms are not distinguishable"* while `hybrid_direct` reads 2.44% mean excess against `aco` at 13.33%, tied on % at optimum and better on worst excess. Likely cause: recovery is undefined at `calm` and the comparison treats an undefined metric as incomparable rather than absent. **Fix it, compute Pareto over the metrics that exist, name which ones those were, and add a test that drives the undefined-recovery branch.**

This one matters more than its size. *"The arms are not distinguishable"* is the null — the single most consequential sentence this project can print. Reaching it automatically, from a code path that mishandled an undefined column, in the scenario designed as a negative control, is how a null gets manufactured instead of found.

**7b. `delta` and `effect` disagree in sign in at least four cells** — `medium200` calm/S2a (+0.0036 vs −0.107), light/P2, light/P3b, severe/P1. Skew is a plausible explanation and `medium200`'s 236–892% worst-excess values fit it. **Demonstrate it on the raw paired differences for one of those cells, or find the bug.** Pre-run check (4) verified the sign on a cell where the two agree, so it never exercised this case.

**7c. `% of steps at optimum` is degenerate at `large1000`** — 0.0% for every arm in three of four scenarios. Entry 033 amends Entry 031: **that metric is reported from `medium200`.** `large1000`'s zeros are still printed, because a metric reading zero everywhere is a finding about the problem size.

**7d. The primary-tier floor excludes `calm`** — Entry 032. Implement it, and **add a test that drives both branches**, because a fallback that cannot fire is decoration.

---

## T8 — One mutation, yours

**Pick something that makes an exploratory result look pre-registered**, or that lets an exploratory number silently contradict a pre-registered one without the output saying so. That is this segment's failure mode: the analysis is now a mix of promised and chosen, and the whole value of the promised half is that a reader can tell which is which.

If it passes everything, that is the finding.

---

## T9 — Show it

- **T0b's cross-check: every number in `FINDINGS_TESTS.md` re-derived from the rows, with every disagreement named**
- T2's bounds, in the sentence form specified, for every null
- T3's split, both halves, with n, and whether the two tiers agree
- T4's mechanism table
- T5's saturation numbers — **including the case where they contradict Entry 032**
- T6's five metrics
- T7's four fixes, with the re-run `analysis.txt`
- your mutation, red
- **`FINDINGS_TESTS.md` complete: every section opening with its plain-English meaning, every number carrying the call that produced it, every section tagged `[raw]` or `[analysis.txt]`, and the report writable from that file alone**
- **Read the finished file start to finish as if you had never seen the project, and say where it stops making sense.** A reference document that only its author can follow has not been written yet.
- **your read: after all of this, does the null still say what Entry 032 says it says?**

---

## T10 — Hand over, do **not** commit

`git status --short`, unstaged. Commit message fenced, no `Co-Authored-By`. **FINDINGS appended to this file**, then reported in chat.

**Do not write the report. Do not start a deck. Do not touch `paper.tex` or `docs/presentation.md`** — those are Rudra's to delete and that happens before any report exists.

---

## Constraints

| | |
|---|---|
| **No new run.** Everything comes from `outputs/2026-09-19/18-43-05` | |
| **Change no arm, no policy, no parameter, no scenario** | |
| **Exploratory results are labelled exploratory and cannot overturn a pre-registered one** | |
| **The bridge-share threshold is stated before the split, not chosen after** | |
| **Both halves of every split reported** | |
| **Timing claims carry the throttling caveat** | |
| **No report, no deck** | |
| **Do not commit, do not push** | |

---

## Definition of done

`FINDINGS_TESTS.md` cross-checked against the raw rows and every disagreement named · every null carries a bound on the raw excess scale · the bridge-share split computed and both halves reported · the allocation mechanism characterised at n = 150 · the saturation measured and Entry 032 confirmed or corrected · recovery, availability, churn, timing and win counts reported · the four `analysis.txt` defects fixed with tests · **`FINDINGS_TESTS.md` holding all of it, each number tagged and each carrying its call** · your mutation red · green suite · uncommitted with the message pasted · FINDINGS in this file.

**Then Rudra talks to his professor, and only then does anyone write a report.**

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->

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
