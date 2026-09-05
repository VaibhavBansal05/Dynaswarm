// Integration tests: the real app.js, executed under node with the
// harness from dom.mjs. These are the tests that would have caught
// segment 8's Mutation B — a defect visible only once app.js's own
// rendering code runs, not in any pure function underneath it.
import { test, describe } from "node:test";
import assert from "node:assert/strict";

import { loadPage, readFixture } from "./dom.mjs";

// The page opens empty by design (segment 11 T3b): arriving with a world
// already built reads as "here is a thing" rather than "build a thing".
// These tests therefore drive Generate explicitly, which is what a user
// does anyway — they were previously relying on an auto-generate that no
// longer exists.
async function loadAndGenerate(fixtures) {
  const page = await loadPage(fixtures);
  await page.test.generate();
  return page;
}

const fixtures = {
  world: readFixture("world.json"),
  geometry: readFixture("world.json"),
  timeline: readFixture("run.json"),
  palette: readFixture("palette.json"),
};

describe("the real page, driven under node", () => {
  test("loads and renders t=0 without error", async () => {
    const { nodes } = await loadAndGenerate(fixtures);
    assert.equal(nodes["stat-t"].textContent, "0 / 59");
    assert.equal(nodes.readout.textContent, "", "an error was rendered");
  });

  test("the step.t === t guard throws on a mismatched payload", async () => {
    // Mirrors segment 8's Mutation B: an off-by-one between the cursor
    // and the step it reads, reproduced by handing the renderer a
    // timeline whose steps are permuted. Nothing server-side is touched;
    // this is the guard T1 requires firing in the browser's own code.
    // Scrambled at RENDER time, not at load: buildStateFrames now has its
    // own ordering guard and catches a scrambled payload first, so
    // handing one to loadPage would exercise the data layer and leave
    // this test's own subject — the guard inside draw() — unrun.
    const { test: hook } = await loadAndGenerate(fixtures);
    hook.state.run.steps = fixtures.timeline.steps.map((s, i, arr) => arr[(i + 1) % arr.length]);
    assert.throws(() => hook.show(1), /renderer asked for t=1 but received step\.t=/);
  });

  test("scrubbing lands exactly on the requested t, not t±1", async () => {
    const { nodes, test: hook } = await loadAndGenerate(fixtures);
    hook.show(21);
    assert.equal(nodes.scrub.value, "21");
    assert.equal(nodes["stat-t"].textContent, "21 / 59");
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
    const { nodes, test: hook } = await loadAndGenerate(fixtures);
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
    const { nodes } = await loadAndGenerate({ ...fixtures, world: smallGeo, geometry: smallGeo });
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
    const { calls } = await loadAndGenerate(fixtures);
    const graph = calls.find((c) => c.path === "/api/graph");
    const timeline = calls.find((c) => c.path === "/api/timeline");
    assert.equal(graph?.method, "POST");
    assert.equal(timeline?.method, "POST");
    assert.deepEqual(JSON.parse(graph.body), {
      model: "geometric", n_nodes: 200, density: 0.04, seed: 1000,
    }, "Stage 1 did not send the form's own values");
  });

  test("the ledger renders and reports it balances", async () => {
    const { nodes, test: hook } = await loadAndGenerate(fixtures);
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
    const { nodes, test: hook } = await loadAndGenerate({ ...fixtures, timeline: bent });
    hook.show(30);
    assert.match(nodes["ledger-balance"].textContent, /DIVERGED/);
    assert.equal(nodes["ledger-balance"].classList.has("broken"), true);
  });

  test("the stat bar carries live |E| from the engine's own count", async () => {
    const { nodes, test: hook } = await loadAndGenerate(fixtures);
    hook.show(59);
    const shown = Number(nodes["stat-edges"].textContent);
    assert.equal(shown, fixtures.timeline.steps[59].n_active_edges);
    // It has to be live, not the opening count — that is the whole point
    // of putting it on the bar.
    assert.notEqual(shown, fixtures.timeline.steps[0].n_active_edges);
  });
});

describe("the panes are the arms', not decoration", () => {
  const raced = readFixture("race.json");

  test("each pane draws its OWN arm's route", async () => {
    // The mutation this exists for: every pane reads arms[0].paths. Same
    // graph, same shape, entirely plausible on screen — and the excess
    // chart still shows four distinct lines, because the chart reads a
    // different field. If this passes, the panes are decorative.
    const { nodes, test: hook } = await loadAndGenerate(fixtures);
    hook.state.race = raced;
    hook.show(21);

    const panes = nodes.panes.children;
    assert.equal(panes.length, raced.arms.length);
    panes.forEach((pane, i) => {
      const drawn = pane.children.find((c) => c.tag === "svg")
        .children.find((g) => g.attrs.class === "arm-path").children.length;
      assert.equal(drawn, Math.max(0, raced.arms[i].paths[21].length - 1),
        `pane ${i} (${raced.arms[i].name}) drew a route of the wrong length`);
    });

    // Two arms with different-length routes must render differently — the
    // length check above is only meaningful if they are not all equal.
    const lengths = raced.arms.map((a) => a.paths[21].length);
    assert.ok(new Set(lengths).size > 1, "fixture arms all agree; the test proves nothing");
  });

  test("a route that never reaches the goal reads as broken, not as short", async () => {
    // §15.5: "a path failing to reach the goal shows up instantly, in
    // whichever arm." Nothing exercised that — every arm reaches the goal
    // in every run this fixture has, because preserve_connectivity keeps
    // the route alive. So a mutation making `reaches` always true passed
    // the entire suite, Python and JavaScript both, and a pane whose arm
    // had failed would have rendered as an ordinary short route.
    const broken = structuredClone(raced);
    broken.arms[1].valid[21] = false;
    broken.arms[1].excess[21] = null;

    const { nodes, test: hook } = await loadAndGenerate(fixtures);
    hook.state.race = broken;
    hook.show(21);

    const panes = nodes.panes.children;
    assert.equal(panes[1].attrs.class ?? panes[1].className, "pane broken",
      "a failed route did not read as broken");
    assert.equal(panes[0].className, "pane", "an intact route was marked broken");
    const badge = panes[1].children[0].children.at(-1);
    assert.equal(badge.textContent, "no route");
  });
});
