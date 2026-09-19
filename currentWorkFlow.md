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

Each result from T2 onward goes into `FINDINGS_TESTS.md` **as it is produced**, under a new section, with:

1. the number,
2. **the command or function call that produced it**, so anyone can re-run it,
3. a provenance tag — **`[raw]`** if derived from the parquet rows in this segment, **`[analysis.txt]`** if carried over from the earlier summary and not re-derived.

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
- **`FINDINGS_TESTS.md` complete: every section tagged `[raw]` or `[analysis.txt]`, every number carrying the call that produced it, and the report writable from that file alone**
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
