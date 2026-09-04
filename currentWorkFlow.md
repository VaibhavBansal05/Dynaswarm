# SEGMENT 10 — Hand Over the Controls

**Phase 1 · See it · Segment 5 of 7**

> Read `AGENT_PROTOCOL.md`, `ARCHITECTURE.md` **§15.3, §15.4, §15.7** and **§4.3.1 (new — the edge lifecycle)**, §2.3. `WORKFLOW_LOG.md` **Entry 009** carries R2–R4, all of which are tasks here.
> Append your findings to the **bottom** of this file.

---

## Goal

**Stop hardcoding the world.** Rudra chooses the graph and chooses how it breaks, then watches what he built.

Segments 7–9 built the rendering halves of §15.3 and §15.4 and left the choosing halves out. This closes both.

---

## ⚠️ T0 — MEASURE

`src/` `2005 / 2100` (expect `+0`, fifth segment) · `dashboard/**/*.py` `76 / 1000` · `dashboard/static/**` `361 / 1200`. Project, then report actual, plus what segments 11–13 have left.

---

## Tasks

### T1 — The small ruled items, first

| | |
|---|---|
| **R2** | Widen `STATIC_SUFFIXES` to include `.json`. The budget asks *"has this become an application?"* and a growing config file is that growth as surely as a growing script. Report the new figure |
| **R3** | Every acceptance block in this repo's specs said `pytest -q`; `addopts` already carries `-q`, so that meant `-qq` and suppressed the summary. **This spec says `pytest`.** If `RUNBOOK.md` repeats the mistake, fix it there too |
| **R4** | **Jump-to-next-event** — 48 of 60 steps are quiet and the demo dies waiting. Next/previous step *with events*. Beside the playback controls |
| | **Reset → `t=0`** |
| | Drop `Phase 1 · segment N` from the page header — internal bookkeeping, not for an examiner |
| | Drop the **D32 warning banner**. Its job is done: it existed so whoever built the timeline could not miss that stored runs carry misaligned timing, and segment 8 built from live data instead. **Report whether the "runs on disk" panel still earns its place** — that is a ruling, not your call |
| | Drop the **"local development server…"** footer |
| | **Thicken `delete`** — currently width 1.0 / opacity 0.55 and effectively invisible. It must read as *"this road is gone permanently"*, distinct from `closure`, without competing with live events |

### T2 — Stage 1: build the world (§15.3)

Controls for **model, node count, density, seed** → **Generate**. Re-rolling the seed browses variants.

**`POST /api/graph` per §15.7 — and do not touch the existing `GET /api/graph`.** That endpoint is pinned by the anti-reimplementation test and its stability is worth more than tidiness. Add alongside.

**The graph id must be derived, not stored.** A deterministic function of `(model, n_nodes, density, seed)` — a hash is fine. This matters: segment 8 ruled the server holds **no state**, and an id handed out from a server-side registry would break that, bringing sessions, eviction and two-viewers-disagree with it. A derived id means any request carrying it rebuilds the identical graph from nothing. Segment 11 gets the identity it needs to race on *this* graph; the server still remembers nothing.

A cache for speed is permitted **only if evicting it cannot change any answer.** Say which you did.

Panel shows `|V|`, `|E|`, mean degree, optimal cost. **`small30` must remain selectable and must still refuse to draw** — the refusal is a feature and the picker is where a user will first meet it.

### T3 — Stage 2: design the disruption (§15.4)

A **scenario preset** dropdown (`static` / `low` / `moderate` / `high`), and the underlying knobs: `events_per_step`, `cluster_size`, `timesteps`, and the six event probabilities. → **Build**.

**`POST /api/timeline`**, same derived-id discipline, keyed on the graph id plus the scenario parameters.

Report which preset names and parameters the **code** actually exposes, from source. §4.3's scenario table is the document.

### T4 — The ledger — the invariant made watchable

**Rudra's request, and it is worth more than a stat panel.**

Per §4.3.1 the population of slots is closed, so at every `t`:

```
active(t) = active(0) + (adds + reopens) − (closures + deletes)
```

That is an **exact identity, not an approximation.** Put it on screen as a running ledger — `initial`, `added`, `reopened`, `closed`, `deleted`, `current` — and it becomes an invariant an examiner can watch hold for sixty steps.

Also: **live `|E|` on the stat line.** A pool road genuinely connects a node pair that had none, so the edge count really moves, and the picture currently hides that.

**Every number comes from the engine's counts.** If the browser must tally events to produce them, that is bookkeeping over data it was given — but the *reconciliation* (`current` against the engine's `n_active_edges` at that `t`) must compare against the engine's own figure, not against the browser's running total. **A ledger that only agrees with itself proves nothing.**

### T5 — Tests

| Test | Catches |
|---|---|
| **The ledger balances at every `t`** | Against the engine's `n_active_edges`, not the browser's tally. **The one that matters** |
| **`|E|` changes when a pool road is added** | Proves `add` is not an overlay |
| **A derived id round-trips** | Same parameters → same id → identical graph, from a cold process |
| **Evicting any cache changes no answer** | The statelessness rule, asserted rather than promised |
| **`closure`/`delete` only target `active` slots; `reopen` only `base_active`; `add` only pool** | §4.3.1's eligibility table. Rudra asked whether a road that never existed can be deleted — pin the answer |
| **An added road can be closed and re-added, and never becomes `reopen`-eligible** | The lifecycle across cycles |
| **`small30` picked → refuses to draw** | |
| **Jump-to-next-event lands on a step with events** | And on the *nearest* one |

### T6 — Mutations, two, one of them yours

**Specified:** make the graph id ignore `seed`. Two different worlds collapse to one id — the failure segment 11 would inherit as arms racing on a graph they were not built for.

**Yours.** Entry 009's slipped mutation is the standing warning: **a threshold or bound must come from the property protected, never from the number being replaced.** Say what you tried and anything that got through.

### T7 — Show it

1. Generate a **different** graph (change nodes and seed) — paste the panel and the new `|E|`
2. Build a **different** scenario — paste the timeline summary
3. **The ledger at `t=0`, mid-run, and `t=59`**, with the balance shown holding
4. Jump-to-next-event from `t=0`: which step does it land on, and is that the nearest one with events?
5. Does the page still read cleanly with the banners gone?

### T8 — Commit

**Name the files explicitly. Do not use `git add -A`.** The Architect's `WORKFLOW_LOG.md` and `ARCHITECTURE.md` edits live in this same tree as unstaged changes, and `git add -A` cannot tell them apart — it swept Entry 008 last segment. Noticing is not a control.

```
segment 10: hand over the controls (phase 1)

Stage 1 and Stage 2 of the dashboard: choose model, nodes, density and
seed and generate; choose a scenario preset or set the disruption knobs
and build. POST /api/graph and POST /api/timeline per §15.7, alongside the
existing GET endpoints, which stay pinned.

The graph id is derived from its parameters rather than issued from a
registry, so identity costs no server state: any request carrying an id
rebuilds the same graph from nothing, and segment 11 can race on a named
graph without the server remembering one.

Adds the edge ledger. §4.3.1's population of slots is closed, so
active(t) = active(0) + adds + reopens - closures - deletes exactly, and
the panel shows it holding against the engine's own count rather than
against its own tally. Live |E| joins the stat line, since a pool road
connects a node pair that had none.

Also: jump-to-next-event (48 of 60 steps are quiet), reset to t=0, a
readable weight for deleted roads, .json inside the static budget, and the
internal banners removed from a page that is now shown to people.

Spec + findings: currentWorkFlow.md
Log: WORKFLOW_LOG.md entry 010
```

---

## Constraints

| | |
|---|---|
| **Zero statements added to `src/`** | Stop and report |
| **No server state** | Derived ids only. A cache must be evictable with no change in answers |
| **Do not modify `GET /api/graph`, `/api/graph/geometry`, `/api/timeline`** | Pinned. Add alongside |
| **The browser computes no quantity** | The ledger reconciles against the engine's count |
| **Hue is not spent on arms** | §15.5 gives each arm its own pane; position carries identity (Entry 009 R1) |
| **No arms, no inspect panels, no design pass** | Segments 11, 12, 13 |
| **Commit names files** | No `git add -A` |
| **Do not push** | |

---

## Acceptance check

```bash
git diff --stat -- dashboard/ tests/ RUNBOOK.md
git diff --stat -- src/                     # expect EMPTY
./.venv/bin/pytest                          # NOT -q. Report passes and skips
./.venv/bin/ruff check src/ tests/ dashboard/
./.venv/bin/pytest -k "statement or budget" -s
grep -rn "segment\|D32\|not hosted" dashboard/static/index.html   # expect none
git log --oneline -2 && git status --short --branch | head -1
```

**Paste verbatim:** T0 all three with projections · the preset names and parameters **from source** · the derived-id scheme and whether a cache exists · the ledger at three points with the balance holding · jump-to-next-event's landing step · both mutations · whether the "runs on disk" panel should survive.

---

## Definition of done

Checks pass, artefacts pasted, commit exists unpushed, FINDINGS appended.

**After this Rudra builds his own world and watches it break.** Segment 11 races the arms on it.

---
---

<!-- vClaude: append your FINDINGS block below this line, using the template in AGENT_PROTOCOL.md §6 -->
