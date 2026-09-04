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

  const cost = step.reachable ? step.optimum.toFixed(2) : "unreachable";
  const hops = step.reachable ? step.path.length - 1 : "—";
  const n = step.events.length;
  const readout = document.getElementById("readout");
  readout.textContent =
    `t = ${t} / ${run.horizon - 1}      optimum ${cost}      hops ${hops}` +
    `      ${n} edge${n === 1 ? "" : "s"} changed this step`;
  readout.classList.toggle("broken", !step.reachable);
  document.getElementById("scrub").value = String(t);
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
  scrub.max = String(state.run.horizon - 1);
  scrub.addEventListener("input", () => show(Number(scrub.value)));
  document.getElementById("back").addEventListener("click", () => show(state.t - 1));
  document.getElementById("fwd").addEventListener("click", () => show(state.t + 1));
  document.getElementById("play").addEventListener("click", toggle);
  document.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") show(state.t - 1);
    else if (e.key === "ArrowRight") show(state.t + 1);
    else if (e.key === " ") { e.preventDefault(); toggle(); }
  });
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
  const refusal = document.getElementById("refusal");
  refusal.textContent =
    `The ${geo.tier} tier carries no node coordinates — it is an Erdős–Rényi ` +
    `graph, so the engine never generated positions for it. Drawing it would ` +
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

Promise.all([
  fetch("/api/graph/geometry").then((r) => r.json()),
  fetch("/api/timeline").then((r) => r.json()),
  fetch("/static/palette.json").then((r) => r.json()),
]).then(([geo, run, palette]) => {
  state.geo = geo;
  state.run = run;
  state.palette = palette.kinds;
  if (!geo.has_coordinates) return refuse(geo);
  state.xy = geo.positions.map(projector(geo.positions, VIEW.w, VIEW.h, VIEW.pad));
  state.baseline = baselineFrom(geo.edges, geo.weights);
  state.frames = buildStateFrames(state.baseline, run.steps);
  buildLegend(palette.kinds);
  wire();
  show(0);
}).catch((e) => {
  document.getElementById("readout").textContent = `error: ${e.message}`;
});

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
