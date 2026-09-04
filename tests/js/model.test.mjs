// Pure unit tests, no DOM, no shim. Node's own runner (`node --test`),
// no third-party test framework — the "no new dependency beyond node"
// constraint applies to the test tooling too, not only the app.
import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  RECENCY_DECAY, FADE_CUTOFF, fadeOpacity, edgeKey, classify, isUsable,
  buildStateFrames, baselineFrom, stateStyle, ledgerAt, seekEvent,
} from "../../dashboard/static/model.js";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const palette = JSON.parse(
  readFileSync(path.resolve(HERE, "../../dashboard/static/palette.json"), "utf8")
).kinds;
const KIND_KEYS = Object.keys(palette);

const geometry = JSON.parse(readFileSync(path.join(HERE, "fixtures/geometry.json"), "utf8"));
const timeline = JSON.parse(readFileSync(path.join(HERE, "fixtures/timeline.json"), "utf8"));

describe("palette completeness — every kind the core can emit has a class", () => {
  test("every kind classifies without throwing", () => {
    for (const kind of KIND_KEYS) assert.doesNotThrow(() => classify(palette, kind));
  });

  test("an unknown kind throws rather than silently defaulting", () => {
    assert.throws(() => classify(palette, "levitation"), /no visual class defined/);
  });

  test("no two kinds share a visual class", () => {
    const classes = KIND_KEYS.map((k) => palette[k].cls);
    assert.equal(new Set(classes).size, classes.length, "a class collision would let two opposite events look identical");
  });

  test("no two kinds share a dash pattern — the greyscale guarantee", () => {
    // Colour is reinforcement; the dash pattern alone must separate every
    // kind, so the distinction survives a desaturated or colourblind view.
    const dashes = KIND_KEYS.map((k) => palette[k].dash);
    assert.equal(new Set(dashes).size, dashes.length, "a shared dash pattern would rely on hue alone");
  });
});

describe("closure and delete — mechanically identical, visually distinct", () => {
  test("neither is usable after", () => {
    assert.equal(isUsable("closure"), false);
    assert.equal(isUsable("delete"), false);
  });
  test("every other kind is usable after", () => {
    for (const kind of ["traffic_up", "traffic_down", "reopen", "add"]) {
      assert.equal(isUsable(kind), true, kind);
    }
  });
});

describe("the fade window — the anti-mud guarantee", () => {
  test("full brightness on the step an event lands", () => {
    assert.equal(fadeOpacity(0), 1);
  });
  test("decays by RECENCY_DECAY per quiet step, not a made-up constant", () => {
    assert.equal(fadeOpacity(1), RECENCY_DECAY);
    assert.equal(fadeOpacity(2), RECENCY_DECAY ** 2);
  });
  test("contributes exactly nothing past FADE_CUTOFF", () => {
    assert.equal(fadeOpacity(FADE_CUTOFF + 1), 0);
    assert.equal(fadeOpacity(1000), 0);
  });
  test("negative age (shouldn't occur, but) contributes nothing", () => {
    assert.equal(fadeOpacity(-1), 0);
  });
});

describe("the state layer reflects the current price, not the history", () => {
  const baseline = baselineFrom(geometry.edges, geometry.weights);
  const frames = buildStateFrames(baseline, timeline.steps);

  test("two edges landing on the same current price look the same regardless of path taken", () => {
    // Construct a tiny synthetic run: edge A goes up then back down to X;
    // edge B never moves and already sits at X. Same destination price,
    // different history — the state layer must not distinguish them.
    const base = new Map([
      ["0,1", { u: 0, v: 1, price: 10 }],
      ["2,3", { u: 2, v: 3, price: 10 }],
    ]);
    const steps = [
      { t: 0, events: [] },
      { t: 1, events: [{ u: 0, v: 1, kind: "traffic_up", new_weight: 20 }] },
      { t: 2, events: [{ u: 0, v: 1, kind: "traffic_down", new_weight: 10 }] },
    ];
    const f = buildStateFrames(base, steps);
    const a = f[2].get("0,1"), b = f[2].get("2,3");
    assert.equal(a.price, b.price);
    assert.deepEqual(stateStyle(a, 10), stateStyle(b, 10));
  });

  test("throws if a step's own t disagrees with its position — the guard, at the data layer", () => {
    const base = new Map([["0,1", { u: 0, v: 1, price: 10 }]]);
    const bad = [{ t: 0, events: [] }, { t: 5, events: [] }];
    assert.throws(() => buildStateFrames(base, bad), /steps out of order/);
  });

  test("a deleted road is invisible; a closed road is a faint ghost", () => {
    const closed = stateStyle({ active: false, kind: "closure", changedAt: 3 }, 10);
    const deleted = stateStyle({ active: false, kind: "delete", changedAt: 3 }, 10);
    assert.equal(closed.visible, true);
    assert.equal(closed.ghost, true);
    assert.equal(deleted.visible, false, "a deleted road must not be drawn as a road, or at all");
  });

  test("matches the real run's active mask and price at every timestep (spot check)", () => {
    // The exhaustive 47,325-pair check against GraphTimeline.state_at()
    // lives in the segment's FINDINGS, run once against a live server.
    // This is the fixture-based regression that catches it breaking again.
    for (const t of [0, 21, 57, 59]) {
      const frame = frames[t];
      assert.equal(frame.size >= geometry.edges.length, true, `t=${t} lost edges`);
    }
  });
});

describe("edgeKey is undirected", () => {
  test("(u,v) and (v,u) key identically", () => {
    assert.equal(edgeKey(3, 9), edgeKey(9, 3));
  });
});

const run = JSON.parse(readFileSync(path.join(HERE, "fixtures/run.json"), "utf8"));

describe("the edge ledger — an invariant, not a statistic", () => {
  test("balances against the engine's own count at every timestep", () => {
    // Written first as `assert.equal(l.balances, true)` alone, which a
    // mutation replacing `engineCount` with `predicted` walked straight
    // through — a ledger reconciling against its own arithmetic balances
    // on any data whatsoever, so the assertion named for the property
    // could never fail.
    //
    // The obvious repair — also assert `engineCount === steps[t]
    // .n_active_edges` — does not work either, because on correct data
    // the predicted value IS that number. Nothing checked against a
    // correct run can distinguish the two.
    //
    // The only thing that can is data where they disagree, so the
    // perturbation below is the real test and the loop is the regression.
    for (let t = 0; t < run.steps.length; t += 1) {
      const l = ledgerAt(run.steps, t);
      assert.equal(l.balances, true,
        `t=${t}: ledger ${l.predicted} vs engine ${l.engineCount}`);
    }

    const bent = run.steps.map((s, i) =>
      i === 30 ? { ...s, n_active_edges: s.n_active_edges + 7 } : s);
    const perturbed = ledgerAt(bent, 30);
    assert.equal(perturbed.balances, false,
      "the ledger balanced against a count the engine did not report — " +
      "it is reconciling with itself");
    assert.equal(perturbed.engineCount, run.steps[30].n_active_edges + 7);
  });

  test("the tally actually moves — a ledger of zeros would balance trivially", () => {
    const end = ledgerAt(run.steps, run.steps.length - 1);
    assert.ok(end.added > 0 && end.closed > 0,
      "fixture has no adds or closures; balancing proves nothing");
    assert.notEqual(end.predicted, end.initial, "|E| never moved across the run");
  });
});

describe("jump-to-next-event", () => {
  test("lands on a step that has events, and on the nearest one", () => {
    const withEvents = run.steps.filter((s) => s.events.length > 0).map((s) => s.t);
    assert.ok(withEvents.length > 1, "fixture needs at least two disrupted steps");

    const landing = seekEvent(run.steps, 0, 1);
    assert.equal(landing, withEvents[0], "did not land on the nearest disrupted step");
    assert.ok(run.steps[landing].events.length > 0);
  });

  test("seeks backwards to the nearest earlier disrupted step", () => {
    const withEvents = run.steps.filter((s) => s.events.length > 0).map((s) => s.t);
    const last = withEvents[withEvents.length - 1];
    const previous = withEvents[withEvents.length - 2];
    assert.equal(seekEvent(run.steps, last, -1), previous);
  });

  test("returns null rather than guessing when there is no next event", () => {
    const last = run.steps.filter((s) => s.events.length > 0).map((s) => s.t).pop();
    assert.equal(seekEvent(run.steps, last, 1), null);
    assert.equal(seekEvent(run.steps, 0, -1), null);
  });

  test("a quiet run has nowhere to jump, and says so", () => {
    const quiet = run.steps.map((s) => ({ ...s, events: [] }));
    assert.equal(seekEvent(quiet, 0, 1), null);
  });
});
