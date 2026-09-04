// The browser reconstructs appearance. The engine owns every quantity.
//
// Two layers, because the picture was pushing two different kinds of
// fact through one channel. A road's PRICE is a state: it is true right
// now and stays true until something changes it. A road BREAKING is an
// event: it happens once and is over. Painting both the same way made
// "a road closed" and "a new road appeared" look identical, and touched
// edges piled up until the whole graph was amber. model.js keeps that
// split in the data; this file only turns the result into pixels.
//
// What this file may compute: which bucket a road falls in, and how
// faded a flash is. Both are pure functions of numbers the server sent.
// It never derives a price and never re-indexes an event list — the
// only arithmetic on `t` below moves the playback cursor.
"use strict";

import {
  FADE_CUTOFF, fadeOpacity,
  buildStateFrames, baselineFrom, stateStyle, projector,
  TIER_PRESETS, SCENARIO_PRESETS, ledgerAt, seekEvent,
} from "./model.js";

const SVG_NS = "http://www.w3.org/2000/svg";
const VIEW = { w: 900, h: 620, pad: 24 };
const FRAME_MS = 320;

const state = { geo: null, run: null, palette: null, t: 0, timer: null, xy: [], frames: [] };

function el(name, attrs) {
  const node = document.createElementNS(SVG_NS, name);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  return node;
}

function draw() {
  const svg = document.getElementById("canvas");
  const { geo, run, palette, t, xy } = state;
  const step = run.steps[t];

  // T1's guard: the payload's own index must agree with the cursor, and
  // it fires here, in the browser, in front of whoever is watching — not
  // only in a test run. This is the check that would have caught segment
  // 8's Mutation B on the spot.
  if (step.t !== t) {
    throw new Error(`renderer asked for t=${t} but received step.t=${step.t}`);
  }

  svg.replaceChildren();
  svg.setAttribute("viewBox", `0 0 ${VIEW.w} ${VIEW.h}`);

  // --- state layer: every road's current condition, quiet by design ---
  const stateGroup = el("g", { class: "layer-state" });
  const ghostGroup = el("g", { class: "layer-ghost" });
  for (const [key, edge] of state.frames[t]) {
    const a = xy[edge.u], b = xy[edge.v];
    if (!a || !b) continue; // an added edge may reference a node with a known position but no base slot; both endpoints always have positions.
    const baseline = state.baseline.get(key)?.price ?? edge.price;
    const style = stateStyle(edge, baseline);
    if (!style.visible) continue; // deleted: not drawn at all.
    const line = el("line", {
      x1: a[0], y1: a[1], x2: b[0], y2: b[1],
      class: style.ghost ? "road-ghost" : "road",
    });
    line.style.opacity = style.opacity;
    line.style.strokeWidth = style.width;
    if (style.dash !== "none") line.setAttribute("stroke-dasharray", style.dash);
    (style.ghost ? ghostGroup : stateGroup).append(line);
  }
  svg.append(ghostGroup, stateGroup);

  // --- node dots, drawn between the two layers ---
  const nodes = el("g", { class: "nodes" });
  for (const [x, y] of xy) nodes.append(el("circle", { cx: x, cy: y, r: 2.4 }));
  svg.append(nodes);

  // --- event layer: flashes, fading with age, painted on top of state ---
  const eventGroup = el("g", { class: "layer-event" });
  for (let age = FADE_CUTOFF; age >= 0; age -= 1) {
    const at = t - age;
    if (at < 0) continue;
    const opacity = fadeOpacity(age);
    if (opacity <= 0) continue;
    for (const ev of run.steps[at].events) {
      const entry = palette[ev.kind];
      const a = xy[ev.u], b = xy[ev.v];
      const line = el("line", {
        x1: a[0], y1: a[1], x2: b[0], y2: b[1], stroke: entry.color,
      });
      line.style.opacity = entry.opacity * opacity;
      line.style.strokeWidth = entry.width;
      if (entry.dash !== "none") line.setAttribute("stroke-dasharray", entry.dash);
      eventGroup.append(line);
    }
  }
  svg.append(eventGroup);

  // --- the optimal path: on top of everything, always thickest ---
  const route = el("g", { class: "path" });
  for (let i = 0; i < step.path.length - 1; i += 1) {
    const a = xy[step.path[i]], b = xy[step.path[i + 1]];
    route.append(el("line", { x1: a[0], y1: a[1], x2: b[0], y2: b[1] }));
  }
  svg.append(route);

  // --- markers: goal is green, start is a neutral ring (never red — red means closed) ---
  const ends = el("g", { class: "ends" });
  ends.append(el("circle", { cx: xy[geo.source][0], cy: xy[geo.source][1], r: 7, class: "start" }));
  ends.append(el("circle", { cx: xy[geo.target][0], cy: xy[geo.target][1], r: 6, class: "goal" }));
  svg.append(ends);

  const n = step.events.length;
  const set = (id, value) => { document.getElementById(id).textContent = String(value); };
  set("stat-t", `${t} / ${run.horizon - 1}`);
  set("stat-optimum", step.reachable ? step.optimum.toFixed(2) : "unreachable");
  set("stat-hops", step.reachable ? step.path.length - 1 : "—");
  set("stat-edges", step.n_active_edges);
  set("stat-changed", n);
  document.getElementById("stat-optimum").classList.toggle("broken", !step.reachable);
  document.getElementById("readout").textContent = "";
  document.getElementById("scrub").value = String(t);
  drawLedger(run.steps, t);
}

function show(t) {
  state.t = Math.max(0, Math.min(state.run.horizon - 1, t));
  draw();
}

function toggle() {
  const button = document.getElementById("play");
  if (state.timer) {
    clearInterval(state.timer);
    state.timer = null;
    button.textContent = "play";
    return;
  }
  button.textContent = "pause";
  state.timer = setInterval(() => {
    if (state.t >= state.run.horizon - 1) return toggle();
    show(state.t + 1);
  }, FRAME_MS);
}

function wire() {
  const scrub = document.getElementById("scrub");
  scrub.addEventListener("input", () => show(Number(scrub.value)));
  document.getElementById("back").addEventListener("click", () => show(state.t - 1));
  document.getElementById("fwd").addEventListener("click", () => show(state.t + 1));
  document.getElementById("play").addEventListener("click", toggle);
  document.getElementById("reset").addEventListener("click", () => show(0));
  document.getElementById("next-event").addEventListener("click", () => jump(1));
  document.getElementById("prev-event").addEventListener("click", () => jump(-1));
  document.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") show(state.t - 1);
    else if (e.key === "ArrowRight") show(state.t + 1);
    else if (e.key === " ") { e.preventDefault(); toggle(); }
  });
}

// §4.3.1's identity, on screen. It is not a statistic — it is an
// invariant an examiner can watch hold for sixty steps, and a divergence
// would be visible the moment it happened.
function drawLedger(steps, t) {
  const l = ledgerAt(steps, t);
  const dl = document.getElementById("ledger-stats");
  dl.replaceChildren();
  const rows = [
    ["initial", l.initial], ["+ added", l.added], ["+ reopened", l.reopened],
    ["− closed", l.closed], ["− deleted", l.deleted], ["= current", l.predicted],
  ];
  for (const [k, v] of rows) {
    const dt = document.createElement("dt");
    dt.textContent = k;
    const dd = document.createElement("dd");
    dd.textContent = String(v);
    dl.append(dt, dd);
  }
  const balance = document.getElementById("ledger-balance");
  balance.textContent = l.balances
    ? `balances — engine reports ${l.engineCount} active edges`
    : `DIVERGED — ledger says ${l.predicted}, engine says ${l.engineCount}`;
  balance.classList.toggle("broken", !l.balances);
}

function jump(direction) {
  const landing = seekEvent(state.run.steps, state.t, direction);
  if (landing !== null) show(landing);
}

// The legend draws each swatch as a real line carrying the real dash
// pattern, because the dash IS the distinction: three of the six kinds
// share a hue (add and reopen are the same hex), and a solid colour
// block shows none of that. A legend that cannot tell them apart is
// teaching the viewer that they are the same thing.
function buildLegend(kinds) {
  const list = document.getElementById("legend-events");
  list.replaceChildren();
  for (const entry of Object.values(kinds)) {
    const item = document.createElement("li");
    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("class", "swatch-line");
    svg.setAttribute("viewBox", "0 0 34 8");
    const line = el("line", {
      x1: 1, y1: 4, x2: 33, y2: 4,
      stroke: entry.color, "stroke-width": entry.width,
    });
    line.style.opacity = entry.opacity;
    if (entry.dash !== "none") line.setAttribute("stroke-dasharray", entry.dash);
    svg.append(line);
    item.append(svg, document.createTextNode(" " + entry.label));
    list.append(item);
  }
}

function refuse(geo) {
  document.getElementById("canvas").setAttribute("hidden", "hidden");
  document.getElementById("controls").setAttribute("hidden", "hidden");
  document.getElementById("readout").textContent =
    `${geo.n_nodes} nodes, ${geo.n_edges} edges — but no coordinates.`;
  const refusal = document.getElementById("refusal");
  refusal.textContent =
    `This graph carries no node coordinates — the ${geo.spec.model} model ` +
    `does not generate positions. Drawing it would ` +
    `mean inventing a layout, and the picture would show the layout algorithm ` +
    `rather than the graph. Nothing is drawn on purpose.`;
  refusal.hidden = false;
}

// Test-only hook. `globalThis.__TEST__` is undefined on every real page
// load, so this changes nothing in the browser; the harness in
// tests/js/dom.mjs sets it before importing this file, and this exposes
// real internal state rather than a reimplementation of it.
if (typeof globalThis.__TEST__ !== "undefined") {
  globalThis.__TEST__.state = state;
  globalThis.__TEST__.show = show;
  globalThis.__TEST__.draw = draw;
}

// --- Stage 1 / Stage 2: the page now asks for a world, rather than
// being handed one. Both endpoints are POST and both are stateless: the
// graph id in the response is derived from the parameters, so nothing
// here depends on the server remembering anything between calls.

const $ = (id) => document.getElementById(id);
const num = (id) => Number($(id).value);

function graphSpec() {
  return {
    model: $("model").value,
    n_nodes: num("n_nodes"),
    density: num("density"),
    seed: num("seed"),
  };
}

function scenarioSpec() {
  return {
    events_per_step: num("events_per_step"),
    cluster_size: num("cluster_size"),
    timesteps: num("timesteps"),
    p_closure: num("p_closure"),
    p_traffic_up: num("p_traffic_up"),
    p_traffic_down: num("p_traffic_down"),
    p_reopen: num("p_reopen"),
    p_delete: num("p_delete"),
    p_add: num("p_add"),
    traffic_factor: num("traffic_factor"),
  };
}

async function post(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(`${url} returned ${response.status}`);
  return response.json();
}

function showStats(world) {
  $("graph-id").textContent = world.graph_id;
  const dl = $("world-stats");
  dl.replaceChildren();
  const rows = [
    ["|V|", world.n_nodes], ["|E|", world.n_edges],
    ["mean degree", world.mean_degree.toFixed(2)],
    ["optimal cost", world.reachable ? world.optimum.toFixed(2) : "unreachable"],
  ];
  for (const [k, v] of rows) {
    const dt = document.createElement("dt");
    dt.textContent = k;
    const dd = document.createElement("dd");
    dd.textContent = String(v);
    dl.append(dt, dd);
  }
}

async function generate() {
  const world = await post("/api/graph", graphSpec());
  state.geo = world;
  showStats(world);
  if (!world.has_coordinates) return refuse(world);
  $("canvas").removeAttribute("hidden");
  $("controls").removeAttribute("hidden");
  $("refusal").hidden = true;
  state.xy = world.positions.map(projector(world.positions, VIEW.w, VIEW.h, VIEW.pad));
  state.baseline = baselineFrom(world.edges, world.weights);
  await rebuild();
}

async function rebuild() {
  if (!state.geo || !state.geo.has_coordinates) return;
  const run = await post("/api/timeline", {
    graph: graphSpec(), scenario: scenarioSpec(),
  });
  state.run = run;
  state.frames = buildStateFrames(state.baseline, run.steps);
  $("scrub").max = String(run.horizon - 1);
  show(0);
}

function applyTierPreset() {
  const preset = TIER_PRESETS[$("tier").value];
  if (!preset) return;
  $("model").value = preset.model;
  $("n_nodes").value = String(preset.n_nodes);
  $("density").value = String(preset.density);
}

fetch("/static/palette.json")
  .then((r) => r.json())
  .then((palette) => {
    state.palette = palette.kinds;
    buildLegend(palette.kinds);
    wire();
    $("world").addEventListener("submit", (e) => {
      e.preventDefault();
      generate().catch((err) => { $("readout").textContent = `error: ${err.message}`; });
    });
    $("disruption").addEventListener("submit", (e) => {
      e.preventDefault();
      rebuild().catch((err) => { $("readout").textContent = `error: ${err.message}`; });
    });
    $("tier").addEventListener("change", applyTierPreset);
    $("preset").addEventListener("change", () => {
      $("events_per_step").value = String(SCENARIO_PRESETS[$("preset").value]);
    });
    $("reroll").addEventListener("click", () => {
      $("seed").value = String(Math.floor(Math.random() * 100000));
      generate().catch((err) => { $("readout").textContent = `error: ${err.message}`; });
    });
    return generate();
  })
  .catch((e) => { $("readout").textContent = `error: ${e.message}`; });

fetch("/api/runs")
  .then((r) => r.json())
  .then((data) => {
    const dl = document.getElementById("runs");
    dl.replaceChildren();
    for (const [k, v] of Object.entries(data.run_classes)) {
      const dt = document.createElement("dt");
      dt.textContent = k;
      const dd = document.createElement("dd");
      dd.textContent = String(v);
      dl.append(dt, dd);
    }
    const warning = document.getElementById("warning");
    warning.textContent = data.warning;
    warning.hidden = false;
  })
  .catch(() => {});
