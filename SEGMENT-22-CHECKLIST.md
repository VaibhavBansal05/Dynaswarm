# Segment 22 — your checklist

**What this is.** The parts of `WALKTHROUGH.md` a machine could not run. vClaude ran everything automatable in **Segment X** — don't redo those.

**How to use it.** Work down the list. For each item, read the expectation *first*, decide whether you agree, then do it. Tick it or write what you actually saw.

**If something looks wrong: write it down and tell me. Do not fix it, and do not let vClaude fix it mid-pass.** A half-fixed system mid-verification is worse than a known-broken one.

---

## A · The full dashboard pass

`WALKTHROUGH.md` Stop 9. Server running, defaults, seed 1000.

| ☐ | Do this | You should see |
|---|---|---|
| ☐ | Press **Run the demo** | builds, breaks, races, stops on each step where the optimum moves |
| ☐ | Slider to **t=0** | `best route 99.96`, 11 hops |
| ☐ | Slider to **t=21** | `110.54`, hops 11 → 12, **and the blue line visibly changes shape** |
| ☐ | Slider to **t=57** | back to `103.25`, 11 hops — a recovery |
| ☐ | Press **→** once from a break | red lines turn orange (red = just now, orange = earlier) |
| ☐ | Scrub end to end, slowly | **no grey dot ever moves.** Places don't move; only roads change |
| ☐ | Arrow-key to t=21, note numbers; then **drag** the slider to t=21 | identical. A one-step difference is an off-by-one |
| ☐ | Look at the blue route anywhere | it must **never** cross a **red dashed** road. Orange and teal are fine |
| ☐ | Click any road | price now, price at t=0, open or not, original or new, every event that touched it |
| ☐ | Click any place | degree, position, which algorithms route through it |
| ☐ | **A\*** pane cost vs the headline `best route` | must match **to the digit** |
| ☐ | Watch the **edge ledger** throughout | always **balances**, never `DIVERGED` |

**Any of these is a real failure:** blue route crossing a closed road · ledger says DIVERGED · A\* pane and headline disagree · a pane draws a route that stops short without reading as broken · a dot moves while scrubbing.

---

## B · Break it on purpose — the four vClaude couldn't

Exercises 1, 3, 4 (same-process) and 5 are done. These four are yours.

**☐ Exercise 2 — Severe preset, `roads per break` = 40, Race.**

Expect: the optimum jumps around; ACO and PSO get much worse. **The one that matters:** if an arm finds no route at all, its pane must go *visibly broken* — not draw a short line that reaches nowhere as though that were an answer.

> A pane drawing a stub that looks like a route means the display is lying about a failure.

**☐ Exercise 4, restart half — reproducibility across a process.**

Same seed, Race, note the numbers. **Quit the server entirely.** Restart it. Race again with the same seed.

Expect: identical to the last digit. If it differs across restarts, some randomness isn't seeded and **no number in your report is reproducible.**

**☐ Exercise 6 — the extremes.**

Try: 4 places · 1 timestep · `large1000` · a budget of **1 evaluation**.

Expect: it works, or it fails with a clear message. **If it returns a confident-looking answer at 4 places on a 1-evaluation budget, ask where that answer came from.** Confident nonsense is more dangerous than a crash.

**☐ Exercise 7 — the thesis. Read the rewritten version in the doc before doing this one.**

Race **New Recency-Based Adaptive Hybrid** alongside **Fixed / Static Hybrid**, watch the allocation view.

Expect:

- Fixed sits at **exactly 0.5**, one value, no movement
- Adaptive starts at 0.5 and walks **downward** toward PSO, ending around **0.39–0.49** — a gentle staircase, not a sawtooth
- Each disrupted step moves it down by exactly **0.006**
- Calm steps move it **5–15× less**, direction not stable, and that's fine

**Real failures:** Fixed is not at exactly 0.5 · the adaptive line is *genuinely* flat (one value all run) · it oscillates and ends where it started · it looks identical in a calm and a violent world.

**Not a failure:** total travel of only a few hundredths. That's the arithmetic, not a fault. **Zoom in before calling it flat** — the axis is fixed 0–1 on purpose, so a real 0.06 move looks small.

---

## C · Sequence robustness — all six are yours

Interfaces break on *order*, not values.

| ☐ | Do | Expect |
|---|---|---|
| ☐ | Press **Race** before **Build** | refuses or tells you — doesn't race on nothing |
| ☐ | Press **Build** before **Generate** | same |
| ☐ | **Generate** a new world *after* racing | panes and timeline show the **raced** world, not the new form values — they visibly disagree rather than silently agreeing |
| ☐ | Double-click **Race** fast | the second click does nothing while the first runs |
| ☐ | Scrub while it's still racing | controls locked, or it behaves sanely |
| ☐ | Reload the page mid-run | opens empty, no half-state |

---

## D · The ranking tab (new in Segment Z)

| ☐ | Check | Why |
|---|---|---|
| ☐ | The evidence-strength line is visible without hovering — `n = 1 · exploratory · not evidence` | a one-race table must not pose as a result |
| ☐ | **A\*** appears as a reference, **not** as a ranked competitor | it wins everything by definition |
| ☐ | Where arms are close, **Pareto says "no winner"** rather than the ranking implying one | this is the tab's whole reason to exist |
| ☐ | Any arm showing `†` (never recovered) reads as a penalty, not a blank | dropping those made a failing arm look 8× better |

**The question to answer:** does this read as an honest comparison, or as a leaderboard? If arms within 0.14pp of each other look like 1st, 2nd and 3rd, tell me — that's the failure mode it was built to prevent.

---

## E · Already done — don't redo

| | Where |
|---|---|
| Exercises 1, 3, 4 (same-process), 5 | Segment X, T5 |
| Command-based checks in Stops 1–9 | Segment X, T4 |
| 19-combination sweep (4 models × 4 sizes × 4 scenarios, numeric edges) | Segment X, T7 |
| **The timing table** — 1.9s medium200 · 11.7s large1000 · 16.5s severe/500 | Segment X, T7 |

---

## F · When you're done

Tell me, in whatever form is easiest:

1. Anything that didn't match the document — **and which one you think is wrong**, the doc or the code
2. Anything that looked odd but you're not sure about. Say it anyway; three of my predictions have already turned out wrong
3. Whether the ranking tab reads honestly

Then the manifest freezes and the run goes.
