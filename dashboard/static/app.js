// The browser reconstructs appearance. The engine owns every quantity.
//
// What this file is allowed to work out: which edges are currently changed,
// by applying the event list it was handed, in order. That is what to grey
// out, and sending 735 edges per timestep instead would be the only
// alternative.
//
// What it is NOT allowed to work out: any number. Every optimum, path, hop
// count and event list at every t was computed server-side by core.oracle
// and timeline.events_at(). This file looks them up.
//
// Event timing especially. schedule[k] is the transition k -> k+1, so the
// events that produced state t are schedule[t-1] — and that arithmetic is
// written once, in the core, because re-deriving it here is how F1 comes
// back somewhere no test looks. The `t ± 1` below moves the playback
// cursor and nothing else: it never indexes an event list. Every event
// this file reads arrives already attached to the step it belongs to.
"use strict";

const SVG_NS = "http://www.w3.org/2000/svg";
const VIEW = { w: 900, h: 620, pad: 24 };
const FRAME_MS = 320;

const state = { geo: null, run: null, t: 0, timer: null, xy: [], history: [] };

function el(name, attrs) {
  const node = document.createElementNS(SVG_NS, name);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  return node;
}

function key(u, v) {
  return u < v ? `${u},${v}` : `${v},${u}`;
}

// Scale and centre. The whole permitted transform, unchanged from segment 7.
function projector(positions) {
  const xs = positions.map((p) => p[0]);
  const ys = positions.map((p) => p[1]);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const span = Math.max(maxX - minX, maxY - minY) || 1;
  const scale = Math.min(VIEW.w - 2 * VIEW.pad, VIEW.h - 2 * VIEW.pad) / span;
  const offX = (VIEW.w - (maxX - minX) * scale) / 2;
  const offY = (VIEW.h - (maxY - minY) * scale) / 2;
  return ([x, y]) => [(x - minX) * scale + offX, (y - minY) * scale + offY];
}

// Cumulative appearance, precomputed once per run rather than per frame.
// history[t] maps an edge to how it looks at t. Built by walking the
// engine's own event lists forward, applying each exactly where the engine
// says it landed — no index is adjusted on the way through.
function buildHistory(run, baseEdges) {
  const live = new Map();
  for (const [u, v] of baseEdges) live.set(key(u, v), { u, v, gone: false, hit: -1 });
  const frames = [];
  for (const step of run.steps) {
    for (const ev of step.events) {
      const k = key(ev.u, ev.v);
      if (!live.has(k)) live.set(k, { u: ev.u, v: ev.v, gone: true, hit: -1 });
      const edge = live.get(k);
      edge.gone = ev.kind === "closure" || ev.kind === "delete";
      edge.hit = step.t;
    }
    frames.push(new Map([...live].map(([k, e]) => [k, { ...e }])));
  }
  return frames;
}

function classOf(edge, t) {
  if (edge.gone) return "gone";
  if (edge.hit === t) return "hit";
  if (edge.hit >= 0) return "changed";
  return "base";
}

function draw() {
  const svg = document.getElementById("canvas");
  const { geo, run, t, xy } = state;
  const step = run.steps[t];
  svg.replaceChildren();
  svg.setAttribute("viewBox", `0 0 ${VIEW.w} ${VIEW.h}`);

  const groups = { base: el("g", { class: "e-base" }), changed: el("g", { class: "e-changed" }),
                   gone: el("g", { class: "e-gone" }), hit: el("g", { class: "e-hit" }) };
  for (const edge of state.history[t].values()) {
    const a = xy[edge.u], b = xy[edge.v];
    groups[classOf(edge, t)].append(
      el("line", { x1: a[0], y1: a[1], x2: b[0], y2: b[1] }));
  }
  // Painted in this order so a fresh break sits above the clutter.
  svg.append(groups.base, groups.changed, groups.gone);

  const nodes = el("g", { class: "nodes" });
  for (const [x, y] of xy) nodes.append(el("circle", { cx: x, cy: y, r: 2.4 }));
  svg.append(nodes, groups.hit);

  // step.path is the oracle's route at this state. Highlighted, not sought.
  const route = el("g", { class: "path" });
  for (let i = 0; i < step.path.length - 1; i += 1) {
    const a = xy[step.path[i]], b = xy[step.path[i + 1]];
    route.append(el("line", { x1: a[0], y1: a[1], x2: b[0], y2: b[1] }));
  }
  svg.append(route);

  const ends = el("g", { class: "ends" });
  ends.append(el("circle", { cx: xy[geo.source][0], cy: xy[geo.source][1], r: 7, class: "source" }));
  ends.append(el("rect", { x: xy[geo.target][0] - 6, y: xy[geo.target][1] - 6,
                           width: 12, height: 12, class: "target" }));
  svg.append(ends);

  // Every figure on this line came from the endpoint.
  const cost = step.reachable ? step.optimum.toFixed(2) : "unreachable";
  const hops = step.reachable ? step.path.length - 1 : "—";
  const n = step.events.length;
  document.getElementById("readout").textContent =
    `t = ${t} / ${run.horizon - 1}      optimum ${cost}      hops ${hops}` +
    `      ${n} edge${n === 1 ? "" : "s"} changed this step`;
  document.getElementById("readout").classList.toggle("broken", !step.reachable);
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
  // Exact: the scrubber sets t to its own value and nothing adjusts it.
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

Promise.all([
  fetch("/api/graph/geometry").then((r) => r.json()),
  fetch("/api/timeline").then((r) => r.json()),
]).then(([geo, run]) => {
  state.geo = geo;
  state.run = run;
  if (!geo.has_coordinates) return refuse(geo);
  state.xy = geo.positions.map(projector(geo.positions));
  state.history = buildHistory(run, geo.edges);
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
