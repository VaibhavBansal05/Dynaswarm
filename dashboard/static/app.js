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
  TIER_PRESETS, SCENARIO_PRESETS, ledgerAt, seekEvent, excessPath,
  pickNode, pickEdge, edgeHistory, edgeKey,
} from "./model.js";

const SVG_NS = "http://www.w3.org/2000/svg";
// §9's display names are NOT duplicated here. This page used to keep its
// own copy of the map, which meant adding an arm server-side left it
// invisible in the picker with nothing failing anywhere — the same
// two-spellings-of-one-name defect that cost segment 20. Fetched from
// /api/arms instead, so the server's RACEABLE is the only list.
let ARM_NAMES = {};
let ARM_COLORS = {};
const VIEW = { w: 900, h: 620, pad: 24 };
const FRAME_MS = 320;

const state = { geo: null, run: null, race: null, palette: null, selection: null, t: 0, timer: null, xy: [], frames: [] };

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
  if (state.race) drawPanes(t);
  drawArmPanel(t);
  drawAllocationNow(t);

  const sel = state.selection;
  if (sel && sel.kind === "node") {
    svg.append(el("circle", { cx: xy[sel.index][0], cy: xy[sel.index][1], r: 9, class: "sel-node" }));
    inspectNode(sel.index, t);
  } else if (sel && sel.kind === "edge") {
    const [u, v] = geo.edges[sel.index];
    const g = el("g", { class: "sel-edge" });
    g.append(el("line", { x1: xy[u][0], y1: xy[u][1], x2: xy[v][0], y2: xy[v][1] }));
    svg.append(g);
    inspectEdge(sel.index, t);
  }
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
  document.getElementById("canvas").addEventListener("click", (e) => {
    if (!state.geo || !state.geo.has_coordinates) return;
    const box = e.currentTarget.getBoundingClientRect();
    const px = ((e.clientX - box.left) / box.width) * VIEW.w;
    const py = ((e.clientY - box.top) / box.height) * VIEW.h;
    const node = pickNode(state.xy, px, py);
    const edge = node === null ? pickEdge(state.xy, state.geo.edges, px, py) : null;
    if (node !== null) state.selection = { kind: "node", index: node };
    else if (edge !== null) state.selection = { kind: "edge", index: edge };
    else clearInspect();
    show(state.t);
  });
  document.getElementById("reset").addEventListener("click", () => show(0));
  document.getElementById("next-event").addEventListener("click", () => jump(1));
  document.getElementById("prev-event").addEventListener("click", () => jump(-1));
  document.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") show(state.t - 1);
    else if (e.key === "ArrowRight") show(state.t + 1);
    else if (e.key === " ") { e.preventDefault(); toggle(); }
  });
}

// The page must never show a state it is not in. A click that produces
// nothing visible is indistinguishable from an ignored click, so the
// second click is either wasted work or a race — and the stale figures
// beside it go on looking current while they are not.
async function pending(button, label, panel, work) {
  const original = button.textContent;
  button.disabled = true;
  button.textContent = label;
  if (panel) panel.classList.add("busy");
  document.getElementById("readout").textContent = "";
  try {
    return await work();
  } catch (error) {
    document.getElementById("readout").textContent = error.message;
    throw error;
  } finally {
    button.disabled = false;
    button.textContent = original;
    if (panel) panel.classList.remove("busy");
  }
}

const PANE = { w: 240, h: 180, pad: 8 };

// Panes carry the state fabric and the arm's own route, and nothing else.
// At quarter size the event layer, the ghosts and the node dots turn 735
// edges into texture with a line somewhere inside it; dropping them is
// what makes "does this route reach the goal" answerable at a glance,
// which is the one question a pane exists to answer (§15.5).
function drawPanes(t) {
  const host = document.getElementById("panes");
  host.replaceChildren();

  // Every pane is showing the same timestep of one timeline that was
  // built and frozen before any arm ran (§10.2). This is deliberately a
  // STATEMENT, not a check: a tick that can never be red is a tautology
  // wearing a UI costume. What makes it evidence rather than assertion is
  // that the identifiers are shared — one seed and one graph id produce
  // one schedule, and there is only one of each on screen to point at.
  document.getElementById("shared").textContent =
    `All ${state.race.arms.length} panes show timestep ${t} of one timeline, ` +
    `frozen before any algorithm ran — seed ${state.geo.spec.seed}, ` +
    `graph ${state.race.graph_id}, ${state.run.steps[t].n_active_edges} roads open.`;
  const at = projector(state.geo.positions, PANE.w, PANE.h, PANE.pad);
  const xy = state.geo.positions.map(at);

  for (const arm of state.race.arms) {
    const path = arm.paths[t] ?? [];
    const reaches = arm.valid[t];
    const pane = document.createElement("div");
    pane.className = reaches ? "pane" : "pane broken";

    const head = document.createElement("h4");
    head.textContent = arm.name;
    const badge = document.createElement("span");
    badge.textContent = arm.excess[t] === null
      ? "no route"
      : `+${(arm.excess[t] * 100).toFixed(1)}%`;
    head.append(badge);

    // Cost in the same units and precision as the main readout, so the
    // A* pane and the headline optimum can be checked against each other
    // by eye. A percentage alone is a number with nothing to compare to.
    const figures = document.createElement("p");
    figures.className = "pane-figures";
    figures.textContent = arm.cost[t] === null
      ? "—"
      : `${arm.cost[t].toFixed(2)} · ${arm.hops[t]} hops`;

    const svg = el("svg", { viewBox: `0 0 ${PANE.w} ${PANE.h}` });
    const fabric = el("g", { class: "fabric" });
    for (const [u, v] of state.geo.edges) {
      fabric.append(el("line", { x1: xy[u][0], y1: xy[u][1], x2: xy[v][0], y2: xy[v][1] }));
    }
    const route = el("g", { class: "arm-path" });
    for (let i = 0; i < path.length - 1; i += 1) {
      const a = xy[path[i]], b = xy[path[i + 1]];
      route.append(el("line", { x1: a[0], y1: a[1], x2: b[0], y2: b[1] }));
    }
    const ends = el("g", { class: "ends" });
    ends.append(el("circle", { cx: xy[state.geo.source][0], cy: xy[state.geo.source][1], r: 4, class: "start" }));
    ends.append(el("circle", { cx: xy[state.geo.target][0], cy: xy[state.geo.target][1], r: 3.5, class: "goal" }));
    svg.append(fabric, route, ends);

    pane.append(head, figures, svg);
    host.append(pane);
  }
}

const CHART = { w: 1180, h: 190, left: 44, right: 10, top: 12, bottom: 20 };

function drawExcess() {
  const svg = document.getElementById("excess");
  const run = state.race, steps = state.run.steps;
  svg.replaceChildren();
  svg.setAttribute("viewBox", `0 0 ${CHART.w} ${CHART.h}`);

  const all = run.arms.flatMap((a) => a.excess).filter((v) => v !== null);
  const top = Math.max(0.05, Math.max(...all)) * 1.1;
  const x = (t) => CHART.left + (t / (run.horizon - 1)) * (CHART.w - CHART.left - CHART.right);
  const y = (v) => CHART.h - CHART.bottom - (v / top) * (CHART.h - CHART.top - CHART.bottom);

  // Markers come from the timeline's own events — events_at() server-side,
  // never an index re-derived here (F1's rule, in a new place).
  const marks = el("g", { class: "marker" });
  steps.forEach((step) => {
    if (step.events.length) marks.append(el("line", { x1: x(step.t), y1: CHART.top, x2: x(step.t), y2: CHART.h - CHART.bottom }));
  });

  const axis = el("g", { class: "axis" });
  axis.append(el("line", { x1: CHART.left, y1: CHART.h - CHART.bottom, x2: CHART.w - CHART.right, y2: CHART.h - CHART.bottom }));
  for (const frac of [0, 0.5, 1]) {
    const label = el("text", { x: CHART.left - 6, y: y(top * frac) + 3, "text-anchor": "end" });
    label.textContent = `${Math.round(top * frac * 100)}%`;
    axis.append(label, el("line", { x1: CHART.left - 3, y1: y(top * frac), x2: CHART.left, y2: y(top * frac) }));
  }

  const series = el("g", { class: "series" });
  for (const arm of run.arms) {
    series.append(el("path", { d: excessPath(arm.excess, x, y), stroke: ARM_COLORS[arm.id] ?? "#888" }));
  }
  svg.append(marks, axis, series);

  const key = document.getElementById("chart-key");
  key.replaceChildren();
  for (const arm of run.arms) {
    const item = document.createElement("span");
    const swatch = document.createElement("i");
    swatch.style.borderTopColor = ARM_COLORS[arm.id] ?? "#888";
    swatch.style.borderTopStyle = "solid";
    item.append(swatch, document.createTextNode(`${arm.name} · ${(arm.mean_excess * 100).toFixed(1)}% avg`));
    key.append(item);
  }
}

// Everything below reads what the run recorded and nothing else. Where
// §15.6 asks for a field the run does not carry — per-edge pheromone,
// per-node PSO priority — the panel leaves a gap rather than showing a
// plausible number nobody can trace. Both are Layer 2 probes and Phase 2
// records them; `probe` today carries colony- and swarm-level aggregates
// (tau_ratio, diversity), which are not per-edge or per-node.
function rows(host, pairs) {
  host.replaceChildren();
  for (const [k, v] of pairs) {
    const dt = document.createElement("dt");
    dt.textContent = k;
    const dd = document.createElement("dd");
    dd.textContent = String(v);
    host.append(dt, dd);
  }
}

function inspectEdge(index, t) {
  const [u, v] = state.geo.edges[index];
  const frame = state.frames[t].get(edgeKey(u, v));
  const baseline = state.baseline.get(edgeKey(u, v));
  const history = edgeHistory(state.run.steps, u, v);
  document.getElementById("ins-hint").textContent = `road ${u}–${v}`;

  rows(document.getElementById("ins-body"), [
    ["price now", frame ? frame.price.toFixed(3) : "—"],
    ["price at t=0", baseline ? baseline.price.toFixed(3) : "—"],
    ["open right now", frame && frame.active ? "yes" : "no"],
    ["original road", baseline ? "yes" : "no — appeared during the run"],
    ["times changed", history.length],
    ["on the best route", onBestRoute(u, v, t) ? "yes" : "no"],
  ]);

  const table = document.getElementById("ins-events");
  table.replaceChildren();
  for (const e of history) {
    const tr = document.createElement("tr");
    for (const cell of [`t=${e.t}`, state.palette[e.kind].label,
                        `${e.old_weight.toFixed(2)} → ${e.new_weight.toFixed(2)}`]) {
      const td = document.createElement("td");
      td.textContent = cell;
      tr.append(td);
    }
    table.append(tr);
  }
}

function onBestRoute(u, v, t) {
  const path = state.run.steps[t].path;
  for (let i = 0; i < path.length - 1; i += 1) {
    if (edgeKey(path[i], path[i + 1]) === edgeKey(u, v)) return true;
  }
  return false;
}

function inspectNode(node, t) {
  const step = state.run.steps[t];
  const degree = [...state.frames[t].values()]
    .filter((e) => e.active && (e.u === node || e.v === node)).length;
  const [x, y] = state.geo.positions[node];
  const through = (state.race?.arms ?? [])
    .filter((a) => (a.paths[t] ?? []).includes(node)).map((a) => a.name);

  document.getElementById("ins-hint").textContent = `place ${node}`;
  rows(document.getElementById("ins-body"), [
    ["roads open here", degree],
    ["position", `${x.toFixed(3)}, ${y.toFixed(3)}`],
    ["role", node === state.geo.source ? "start"
      : node === state.geo.target ? "goal" : "—"],
    ["on the best route", step.path.includes(node) ? "yes" : "no"],
    ["arms routing through", through.length ? through.join(", ") : "none"],
  ]);
  document.getElementById("ins-events").replaceChildren();
}

function clearInspect() {
  state.selection = null;
  document.getElementById("ins-hint").textContent = "click a road or a place";
  document.getElementById("ins-body").replaceChildren();
  document.getElementById("ins-events").replaceChildren();
}

// Per-arm, at this step. Every figure is a column the run recorded.
function drawArmPanel(t) {
  const host = document.getElementById("ins-arms");
  host.replaceChildren();
  if (!state.race) {
    const empty = document.createElement("p");
    empty.className = "hint";
    empty.textContent = "race the algorithms to see their figures here";
    host.append(empty);
    return;
  }
  for (const arm of state.race.arms) {
    const row = document.createElement("div");
    row.className = "ins-arm";
    const name = document.createElement("b");
    name.textContent = arm.name;
    const excess = document.createElement("span");
    excess.textContent = arm.excess[t] === null ? "no route"
      : `+${(arm.excess[t] * 100).toFixed(1)}%`;
    const spent = document.createElement("span");
    spent.textContent = `${arm.evaluations[t] ?? "—"} evals`;
    row.append(name, excess, spent);
    host.append(row);
  }
}

// ---------------------------------------------------------------------------
// The allocation view (§15.6) — the project's novelty, made watchable.
// ---------------------------------------------------------------------------
//
// This replaces a placeholder that said the bar could not honestly be drawn
// while F7 left the controller varying nothing. F7 is closed, so it is drawn.
//
// Three things the chart must not imply:
//   * that an arm without a governor chose to sit at 0.5 — those arms are
//     absent from this chart entirely, not flat lines on it;
//   * that proposed and applied are two independent readings — where they
//     coincide the note says so in words, because two perfectly overlapping
//     lines look like one line that failed to render;
//   * that the split shown at step t is what step t searched with. It is
//     not. It is the decision taken at the end of t, and `searched` is the
//     separate series the server sends for exactly that reason.

const ALLOC_BOUND_LOW = 0.05, ALLOC_BOUND_HIGH = 0.95;

function allocArms() {
  return state.race ? state.race.arms.filter((a) => a.allocation) : [];
}

function drawAllocation() {
  const wrap = document.getElementById("alloc-wrap");
  const arms = allocArms();
  wrap.hidden = arms.length === 0;
  if (!arms.length) return;

  const svg = document.getElementById("allocation");
  const run = state.race, steps = state.run.steps;
  svg.replaceChildren();
  svg.setAttribute("viewBox", `0 0 ${CHART.w} ${CHART.h}`);

  // Fixed 0..1 axis, never fitted to the data. An auto-scaled axis would
  // magnify a 0.06 wander into a dramatic sweep across the panel, which is
  // the chart telling a better story than the numbers support.
  const x = (t) => CHART.left + (t / (run.horizon - 1)) * (CHART.w - CHART.left - CHART.right);
  const y = (v) => CHART.h - CHART.bottom - v * (CHART.h - CHART.top - CHART.bottom);

  const bands = el("g", { class: "alloc-band" });
  bands.append(el("rect", {
    x: CHART.left, y: y(1), width: CHART.w - CHART.left - CHART.right,
    height: y(ALLOC_BOUND_HIGH) - y(1),
  }));
  bands.append(el("rect", {
    x: CHART.left, y: y(ALLOC_BOUND_LOW), width: CHART.w - CHART.left - CHART.right,
    height: y(0) - y(ALLOC_BOUND_LOW),
  }));

  const marks = el("g", { class: "marker" });
  steps.forEach((step) => {
    if (step.events.length) {
      marks.append(el("line", { x1: x(step.t), y1: CHART.top, x2: x(step.t), y2: CHART.h - CHART.bottom }));
    }
  });

  const axis = el("g", { class: "axis" });
  axis.append(el("line", { x1: CHART.left, y1: CHART.h - CHART.bottom, x2: CHART.w - CHART.right, y2: CHART.h - CHART.bottom }));
  for (const [v, text] of [[0, "all PSO"], [0.5, "even"], [1, "all ACO"]]) {
    const label = el("text", { x: CHART.left - 6, y: y(v) + 3, "text-anchor": "end" });
    label.textContent = text;
    axis.append(label, el("line", { x1: CHART.left - 3, y1: y(v), x2: CHART.left, y2: y(v) }));
  }

  const series = el("g", { class: "series" });
  const pinned = el("g", { class: "alloc-pinned" });
  let anyHeld = false;
  for (const arm of arms) {
    const applied = arm.allocation.applied;
    const colour = ARM_COLORS[arm.id] ?? "#888";
    series.append(el("path", { d: excessPath(applied, x, y), stroke: colour }));

    // Proposed is drawn ONLY where the governor actually held it back.
    // Everywhere else it is the same number, and a second line there would
    // be decoration claiming to be evidence.
    arm.allocation.held_back.forEach((held, t) => {
      if (held !== null && Math.abs(held) > 1e-12) {
        anyHeld = true;
        pinned.append(el("circle", { cx: x(t), cy: y(arm.allocation.proposed[t]), r: 2.5, fill: colour }));
      }
    });
    arm.allocation.at_bound.forEach((at, t) => {
      if (at) pinned.append(el("circle", { cx: x(t), cy: y(applied[t]), r: 3.5, class: "at-bound" }));
    });
  }
  svg.append(bands, marks, axis, series, pinned);

  const key = document.getElementById("alloc-key");
  key.replaceChildren();
  for (const arm of arms) {
    const item = document.createElement("span");
    const swatch = document.createElement("i");
    swatch.style.borderTopColor = ARM_COLORS[arm.id] ?? "#888";
    swatch.style.borderTopStyle = "solid";
    const moved = new Set(arm.allocation.applied.filter((v) => v !== null)).size;
    item.append(swatch, document.createTextNode(
      `${arm.name} · ${moved} distinct split${moved === 1 ? "" : "s"}`));
    key.append(item);
  }

  // Said in words, because the absence of a second line is not self-explanatory.
  const note = document.getElementById("alloc-note");
  note.textContent = anyHeld
    ? "Dots mark steps where the governor held a proposal back; ringed dots mark a split sitting at a bound."
    : "The governor never had to hold a proposal back in this run, so proposed and applied are the same number at every step and only one line is drawn. Not a rendering fault \u2014 the step size is smaller than the per-step limit, so the limit never bound.";
}

// The same decision, at the cursor, as a bar you can watch move.
//
// One bar per governed arm, not just the first one. Written for `arms[0]`
// first, which quietly picked the Fixed hybrid — the arm whose whole job is
// to never move — and so demonstrated the mechanism by showing it not
// happening. The comparison IS the evidence here: the three bars differ at
// the same timestep or the allocation layer is doing nothing.
function drawAllocationNow(t) {
  const host = document.getElementById("alloc-body");
  const bar = document.getElementById("alloc-bar");
  host.replaceChildren();
  bar.replaceChildren();
  bar.hidden = true;
  const arms = allocArms();
  if (!arms.length) {
    const hint = document.createElement("p");
    hint.className = "hint";
    hint.textContent = state.race
      // Worded around the literal "schedule": the repo-wide guard that
      // forbids this file from touching the event schedule greps the code
      // with strings included, and it cannot tell a hint from an index.
      // Rewording costs nothing; loosening that guard would cost F1 again.
      ? "no arm in this race allocates its budget \u2014 race an adaptive or open-loop hybrid"
      : "race the algorithms to watch the split move";
    host.append(hint);
    return;
  }

  for (const arm of arms) {
    // `searched` \u2014 what this step ran with \u2014 not `applied`, which is the
    // decision made at the END of this step and takes effect at the next one.
    const share = arm.allocation.searched[t];
    if (share === null || share === undefined) continue;

    const label = document.createElement("div");
    label.className = "alloc-arm";
    const dot = document.createElement("i");
    dot.style.background = ARM_COLORS[arm.id] ?? "#888";
    label.append(dot, document.createTextNode(arm.name));

    const row = document.createElement("div");
    row.className = "alloc-bar";
    const aco = document.createElement("span");
    aco.className = "alloc-seg aco";
    aco.style.width = `${share * 100}%`;
    aco.textContent = `ACO ${(share * 100).toFixed(0)}%`;
    const pso = document.createElement("span");
    pso.className = "alloc-seg pso";
    pso.style.width = `${(1 - share) * 100}%`;
    pso.textContent = `PSO ${((1 - share) * 100).toFixed(0)}%`;
    row.append(aco, pso);

    const held = arm.allocation.held_back[t];
    const note = document.createElement("p");
    note.className = "alloc-detail";
    note.textContent =
      `asked ${arm.allocation.proposed[t]?.toFixed(4) ?? "\u2014"} \u00b7 `
      + `allowed ${arm.allocation.applied[t]?.toFixed(4) ?? "\u2014"} \u00b7 `
      + `held back ${held === null || held === undefined ? "\u2014"
        : Math.abs(held) < 1e-12 ? "nothing" : held.toFixed(4)}`
      + (arm.allocation.at_bound[t] ? " \u00b7 AT A BOUND" : "");

    host.append(label, row, note);
  }
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
  // The page no longer auto-generates, so a test must drive Stage 1 and
  // Stage 3 the way a user does.
  globalThis.__TEST__.generate = () => generate();
  globalThis.__TEST__.race = () => runRace();
  globalThis.__TEST__.demo = (pace = 0) => demo(pace);
  globalThis.__TEST__.tellingSteps = tellingSteps;
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
  // Plain names, not graph-theory shorthand. |V| and |E| are correct and
  // unreadable; anyone who wants the symbols already knows them.
  const rows = [
    ["places", world.n_nodes.toLocaleString()],
    ["roads", world.n_edges.toLocaleString()],
    ["roads per place", world.mean_degree.toFixed(2)],
    ["shortest route", world.reachable ? world.optimum.toFixed(2) : "no route"],
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
  $("empty").hidden = true;
  // A new world invalidates any race run on the old one.
  state.race = null;
  $("grid-wrap").hidden = true;
  $("race-id").textContent = "";
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

function armPicks() {
  return [...document.querySelectorAll("#arm-picks input:checked")].map((i) => i.value);
}

async function runRace() {
  const started = await post("/api/run", {
    graph: graphSpec(), scenario: scenarioSpec(),
    arms: armPicks(), evaluations: num("evaluations"),
  });
  const loaded = await fetch(`/api/run/${started.run_id}`).then((r) => r.json());
  state.race = loaded;
  $("race-id").textContent = `${started.run_id} · ${started.run_class}`;
  $("grid-wrap").hidden = false;
  drawExcess();
  drawAllocation();
  show(state.t);
}

async function buildArmPicks() {
  const host = $("arm-picks");
  const { arms } = await fetch("/api/arms").then((r) => r.json());
  ARM_NAMES = Object.fromEntries(arms.map((a) => [a.id, a.name]));
  ARM_COLORS = Object.fromEntries(arms.map((a) => [a.id, a.colour]));
  host.replaceChildren();
  for (const arm of arms) {
    const label = document.createElement("label");
    const box = document.createElement("input");
    box.type = "checkbox";
    box.value = arm.id;
    box.checked = arm.default;
    label.append(box, document.createTextNode(arm.name));
    host.append(label);
  }
}

// The steps where the optimum actually moves, read out of the run rather
// than listed here: a fixed list would drift the moment the seed, the
// scenario or the horizon changed, and would then be showing an examiner
// the wrong moments with complete confidence.
function tellingSteps(steps) {
  const out = [0];
  for (let t = 1; t < steps.length; t += 1) {
    if (steps[t].optimum !== steps[t - 1].optimum) out.push(t);
  }
  return out;
}

//: How long each telling moment holds. Long enough to read the numbers
//: change, short enough that an examiner's attention is not the cost.
const DEMO_PACE_MS = 1400;

async function demo(pace = DEMO_PACE_MS) {
  await generate();
  await runRace();
  const stops = tellingSteps(state.run.steps);
  for (const [i, at] of stops.entries()) {
    show(at);
    if (i < stops.length - 1 && pace) await new Promise((r) => setTimeout(r, pace));
  }
  return stops;
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
  .then(async (palette) => {
    state.palette = palette.kinds;
    buildLegend(palette.kinds);
    wire();
    $("world").addEventListener("submit", (e) => {
      e.preventDefault();
      pending(e.submitter ?? $("world").querySelector("button[type=submit]"),
        "generating…", $("world"), generate).catch(() => {});
    });
    $("disruption").addEventListener("submit", (e) => {
      e.preventDefault();
      pending(e.submitter ?? $("disruption").querySelector("button[type=submit]"),
        "building…", $("disruption"), rebuild).catch(() => {});
    });
    $("tier").addEventListener("change", applyTierPreset);
    $("preset").addEventListener("change", () => {
      $("events_per_step").value = String(SCENARIO_PRESETS[$("preset").value]);
    });
    $("reroll").addEventListener("click", () => {
      $("seed").value = String(Math.floor(Math.random() * 100000));
      pending($("reroll"), "generating…", $("world"), generate).catch(() => {});
    });
    $("race").addEventListener("submit", (e) => {
      e.preventDefault();
      pending(e.submitter ?? $("race").querySelector("button[type=submit]"),
        "racing…", $("race"), runRace).catch(() => {});
    });
    await buildArmPicks();
    $("demo").addEventListener("click", (e) =>
      pending(e.currentTarget, "running the demo…", null, demo).catch(() => {}));

    // `?demo=1` runs it on load, and `?arms=a,b` picks the arms first.
    // This exists so the rendered page can be captured and looked at —
    // the allocation view is a chart about a mechanism, and segment 21's
    // whole lesson is that a mechanism nobody watched is a mechanism
    // nobody checked. `?demo=1&arms=hybrid_adaptive,hybrid_scheduled`
    // is the one that shows the split moving.
    const params = new URLSearchParams(location.search);
    if (params.has("arms")) {
      const want = new Set(params.get("arms").split(","));
      for (const box of $("arm-picks").querySelectorAll("input")) {
        box.checked = want.has(box.value);
      }
    }
    if (params.has("demo")) demo(0).catch(() => {});
    // No auto-generate. The page opens empty and asks: arriving with a
    // world already built reads as "here is a thing" rather than "build a
    // thing", and silently spends a decision the controls exist to give.
  })
  .catch((e) => { $("readout").textContent = `error: ${e.message}`; });
