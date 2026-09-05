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

  test("a route that stops short renders as broken, from a real synthetic run", async () => {
    // T2: built from a real race with ACO's tail truncated over t=18..24,
    // so every field except the one under test is what the engine
    // produced. preserve_connectivity means no arm fails in any run
    // obtainable from the engine, so the failing case had to be
    // constructed — a guarantee about failure cannot be tested by data
    // in which nothing fails.
    const brokenRun = readFixture("race_broken.json");
    const { nodes, test: hook } = await loadAndGenerate(fixtures);
    hook.state.race = brokenRun;

    hook.show(21);   // inside the failure window
    const panes = nodes.panes.children;
    const aco = brokenRun.arms.findIndex((a) => a.id === "aco");
    assert.equal(panes[aco].className, "pane broken");
    assert.equal(panes[aco].children[0].children.at(-1).textContent, "no route");
    // Distinct from a short path, not merely shorter: the neighbours are
    // intact and must not be marked.
    brokenRun.arms.forEach((_, i) => {
      if (i !== aco) assert.equal(panes[i].className, "pane", `arm ${i} wrongly marked`);
    });

    hook.show(30);   // outside it — the same arm recovers
    assert.equal(nodes.panes.children[aco].className, "pane",
      "the arm stayed marked broken after its route recovered");
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

describe("the inspect panel is about the thing you clicked", () => {
  test("the edge panel shows THAT edge's history, not another's", async () => {
    // The mutation this exists for: read edges[0] whatever was clicked.
    // Same shape, plausible numbers, wrong road — and nothing else on the
    // page would look different.
    const { nodes, test: hook } = await loadAndGenerate(fixtures);
    const edges = hook.state.geo.edges;
    // Pick an edge that events actually touched, so its history is not
    // trivially empty and cannot coincide with another's by accident.
    const touched = fixtures.timeline.steps.flatMap((s) =>
      s.events.map((e) => [e.u, e.v, s.t]));
    assert.ok(touched.length, "fixture has no events");
    const [u, v] = touched[0];
    const index = edges.findIndex(([a, b]) =>
      (a === u && b === v) || (a === v && b === u));
    assert.ok(index >= 0, "the touched edge is not in the base edge list");

    hook.state.selection = { kind: "edge", index };
    hook.show(59);

    assert.match(nodes["ins-hint"].textContent, new RegExp(`road ${u}.${v}`));
    const shown = nodes["ins-events"].children.length;
    const expected = fixtures.timeline.steps
      .flatMap((s) => s.events)
      .filter((e) => (e.u === u && e.v === v) || (e.u === v && e.v === u)).length;
    assert.equal(shown, expected, "the panel listed a different edge's history");
    assert.ok(expected > 0, "chose an edge with no history; the test proves nothing");
  });
});

describe("the highlight and the panel agree", () => {
  test("the selection marker sits on the thing the panel describes", async () => {
    // My uncommissioned mutation: draw the marker at xy[0] whatever was
    // selected. The panel stayed correct, the picture pointed elsewhere,
    // and all 42 JS tests plus the Python suite passed. It is segment 8's
    // failure — the picture and its caption disagreeing while both look
    // right — moved into the selection layer.
    const { nodes, test: hook } = await loadAndGenerate(fixtures);
    const node = 137;
    hook.state.selection = { kind: "node", index: node };
    hook.show(10);

    assert.match(nodes["ins-hint"].textContent, new RegExp(`place ${node}`));
    const marker = nodes.canvas.children
      .find((c) => c.attrs.class === "sel-node");
    assert.ok(marker, "no selection marker was drawn");
    const [x, y] = hook.state.xy[node];
    assert.equal(Number(marker.attrs.cx).toFixed(2), x.toFixed(2),
      "the marker is not on the node the panel describes");
    assert.equal(Number(marker.attrs.cy).toFixed(2), y.toFixed(2));
  });
});
