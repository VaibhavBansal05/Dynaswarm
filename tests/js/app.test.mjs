// Integration tests: the real app.js, executed under node with the
// harness from dom.mjs. These are the tests that would have caught
// segment 8's Mutation B — a defect visible only once app.js's own
// rendering code runs, not in any pure function underneath it.
import { test, describe } from "node:test";
import assert from "node:assert/strict";

import { loadPage, readFixture } from "./dom.mjs";

const fixtures = {
  world: readFixture("world.json"),
  geometry: readFixture("world.json"),
  timeline: readFixture("run.json"),
  palette: readFixture("palette.json"),
};

describe("the real page, driven under node", () => {
  test("loads and renders t=0 without error", async () => {
    const { nodes } = await loadPage(fixtures);
    assert.equal(nodes.readout.textContent.startsWith("t = 0 / 59"), true, nodes.readout.textContent);
  });

  test("the step.t === t guard throws on a mismatched payload", async () => {
    // Mirrors segment 8's Mutation B: an off-by-one between the cursor
    // and the step it reads, reproduced by handing the renderer a
    // timeline whose steps are permuted. Nothing server-side is touched;
    // this is the guard T1 requires firing in the browser's own code.
    const scrambled = {
      ...fixtures.timeline,
      steps: fixtures.timeline.steps.map((s, i, arr) => arr[(i + 1) % arr.length]),
    };
    const { test: hook } = await loadPage({ ...fixtures, timeline: scrambled });
    assert.throws(() => hook.show(1), /renderer asked for t=1 but received step\.t=/);
  });

  test("scrubbing lands exactly on the requested t, not t±1", async () => {
    const { nodes, test: hook } = await loadPage(fixtures);
    hook.show(21);
    assert.equal(nodes.scrub.value, "21");
    assert.equal(nodes.readout.textContent.startsWith("t = 21 / 59"), true);
  });

  test("t=59 stays close to the 142 salient edges the two-layer split achieves", async () => {
    // "Salient" = visibly deviating from baseline (state layer) or a
    // closure ghost — the roads a viewer's eye actually catches on, not
    // every DOM element (unchanged roads are drawn too, faintly, as the
    // fabric — counting them would compare total elements, not mud).
    // Segment 8's 244 counted every edge EVER touched, whether or not it
    // had returned to its original price by t=59; this layer only lights
    // an edge while its current price actually differs, which is the
    // semantic fix, not a cosmetic one.
    const { nodes, test: hook } = await loadPage(fixtures);
    hook.show(59);
    const canvas = nodes.canvas;
    const stateGroup = canvas.children.find((g) => g.attrs.class === "layer-state");
    const ghostGroup = canvas.children.find((g) => g.attrs.class === "layer-ghost");
    const salient = stateGroup.children.filter((line) => line.style.opacity > 0.13).length
      + ghostGroup.children.length;
    // The threshold is NOT the old 244. Asserting against the figure you
    // just improved on is a test that sleeps through almost any
    // regression: this segment's own mutation — reverting the state layer
    // to "lit once, lit forever" — pushed this from 142 back to 228 and
    // this assertion still passed, because 228 < 244. Pinned just above
    // the achieved value instead, so the guarantee is what is guarded.
    assert.ok(
      salient < 160,
      `${salient} salient edges at t=59; the two-layer split achieves 142`
    );
  });

  test("small30 refuses to draw rather than inventing a layout", async () => {
    const smallGeo = readFixture("world_small30.json");
    const { nodes } = await loadPage({ ...fixtures, world: smallGeo, geometry: smallGeo });
    assert.equal(nodes.canvas.attrs.hidden, "hidden");
    assert.equal(nodes.refusal.hidden, false);
  });

  test("the legend names every event kind in plain words, never 'changed'", async () => {
    const { nodes } = await loadPage(fixtures);
    const rows = nodes["legend-events"].children;
    const text = rows.map((li) => li.children.map((c) => c.text ?? "").join("")).join(" ");

    // Written first with `if (!entry.label) continue;`, which SKIPPED the
    // palette's `_comment` key instead of noticing app.js was rendering
    // it as a row reading "undefined". The test worked around the bug it
    // existed to catch. One row per kind, exactly, and every row named.
    const kinds = Object.values(fixtures.palette.kinds);
    assert.equal(rows.length, kinds.length, "legend row count does not match the kind count");
    for (const entry of kinds) {
      assert.ok(text.includes(entry.label), `legend missing "${entry.label}"`);
    }
    assert.ok(!/undefined/.test(text), `legend rendered an undefined row: ${text}`);
    assert.ok(!/\bchanged\b/i.test(text), "legend used the word 'changed' instead of naming the event");
  });

  test("each legend swatch carries its kind's real dash pattern", async () => {
    // Three of the six kinds share a hue — add and reopen are the same
    // hex — so a solid colour block shows the viewer nothing that
    // distinguishes them, which is exactly what the first version did.
    const { nodes } = await loadPage(fixtures);
    const kinds = Object.values(fixtures.palette.kinds);
    const drawn = nodes["legend-events"].children.map((li) => {
      const line = li.children.find((c) => c.tag === "svg").children[0];
      return line.attrs["stroke-dasharray"] ?? "none";
    });
    assert.deepEqual(drawn, kinds.map((k) => k.dash));
    assert.equal(new Set(drawn).size, drawn.length, "legend swatches are not visually distinct");
  });
});


describe("Stage 1 and Stage 2 ask the server, statelessly", () => {
  test("the page POSTs for its world and its timeline", async () => {
    // Not merely "it rendered" — the two stages must actually go to the
    // POST endpoints, since that is what carries the chosen parameters.
    const { calls } = await loadPage(fixtures);
    const graph = calls.find((c) => c.path === "/api/graph");
    const timeline = calls.find((c) => c.path === "/api/timeline");
    assert.equal(graph?.method, "POST");
    assert.equal(timeline?.method, "POST");
    assert.deepEqual(JSON.parse(graph.body), {
      model: "geometric", n_nodes: 200, density: 0.04, seed: 1000,
    }, "Stage 1 did not send the form's own values");
  });

  test("the ledger renders and reports it balances", async () => {
    const { nodes, test: hook } = await loadPage(fixtures);
    hook.show(59);
    assert.match(nodes["ledger-balance"].textContent, /balances — engine reports \d+/);
    assert.equal(nodes["ledger-balance"].classList.has("broken"), false);
  });

  test("the ledger says DIVERGED rather than quietly rounding", async () => {
    // The panel's whole value is that a divergence is visible. Feed it a
    // run whose engine count disagrees with its own events and check the
    // page says so instead of showing a plausible number.
    const bent = {
      ...fixtures.timeline,
      steps: fixtures.timeline.steps.map((s, i) =>
        i === 30 ? { ...s, n_active_edges: s.n_active_edges + 7 } : s),
    };
    const { nodes, test: hook } = await loadPage({ ...fixtures, timeline: bent });
    hook.show(30);
    assert.match(nodes["ledger-balance"].textContent, /DIVERGED/);
    assert.equal(nodes["ledger-balance"].classList.has("broken"), true);
  });

  test("the stat line carries live |E|", async () => {
    const { nodes, test: hook } = await loadPage(fixtures);
    hook.show(59);
    assert.match(nodes.readout.textContent, /\|E\| \d+/);
  });
});
