// The browser receives geometry. It never invents geometry.
//
// Positions come from view.topology.pos, edges from the core's active
// mask, the path from core.oracle. The only geometric thing this file is
// permitted to do is scale and centre the given coordinates so they fit
// the viewport — presentation, not layout.
//
// There is deliberately no graph library here. Every one of them ships a
// layout algorithm, and a layout algorithm is a second opinion about where
// the nodes are. A wrong number looks wrong; a wrong picture looks fine.
"use strict";

const SVG_NS = "http://www.w3.org/2000/svg";
const VIEW = { w: 900, h: 620, pad: 24 };

function render(target, pairs) {
  const dl = document.getElementById(target);
  dl.replaceChildren();
  for (const [key, value] of pairs) {
    const dt = document.createElement("dt");
    dt.textContent = key;
    const dd = document.createElement("dd");
    dd.textContent = String(value);
    dl.append(dt, dd);
  }
}

function fail(target, error) {
  render(target, [["error", error.message]]);
}

function el(name, attrs) {
  const node = document.createElementNS(SVG_NS, name);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  return node;
}

// Scale and centre — the whole of the permitted transform. Uniform on both
// axes, so the picture cannot be stretched into a different shape, and no
// vertical flip: SVG's y grows downward and the spec allows two operations,
// not three. A random geometric graph has no inherent up, so the drawing is
// faithful either way.
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

function draw(geo) {
  const svg = document.getElementById("canvas");
  const refusal = document.getElementById("refusal");
  svg.replaceChildren();

  if (!geo.has_coordinates) {
    // Not a fallback layout, not a circle, not a scatter. A tier without
    // positions has no honest picture, and inventing one is precisely what
    // made the previous project's replay worthless.
    svg.setAttribute("hidden", "hidden");
    refusal.textContent =
      `The ${geo.tier} tier carries no node coordinates — it is an Erdős–Rényi ` +
      `graph, so the engine never generated positions for it. Drawing it would ` +
      `mean inventing a layout, and the picture would show the layout algorithm ` +
      `rather than the graph. Nothing is drawn on purpose.`;
    refusal.hidden = false;
    return;
  }

  refusal.hidden = true;
  svg.removeAttribute("hidden");
  svg.setAttribute("viewBox", `0 0 ${VIEW.w} ${VIEW.h}`);

  const at = projector(geo.positions);
  const xy = geo.positions.map(at);

  // Context first, so the path lands on top of it rather than under.
  const context = el("g", { class: "edges" });
  for (const [u, v] of geo.edges) {
    context.append(el("line", {
      x1: xy[u][0], y1: xy[u][1], x2: xy[v][0], y2: xy[v][1],
    }));
  }
  svg.append(context);

  const nodes = el("g", { class: "nodes" });
  for (const [x, y] of xy) nodes.append(el("circle", { cx: x, cy: y, r: 2.4 }));
  svg.append(nodes);

  // The oracle's sequence, highlighted. This loop walks a path it was
  // given; it does not look for one.
  const route = el("g", { class: "path" });
  for (let i = 0; i < geo.path.length - 1; i += 1) {
    const a = xy[geo.path[i]], b = xy[geo.path[i + 1]];
    route.append(el("line", { x1: a[0], y1: a[1], x2: b[0], y2: b[1] }));
  }
  svg.append(route);

  const ends = el("g", { class: "ends" });
  ends.append(el("circle", {
    cx: xy[geo.source][0], cy: xy[geo.source][1], r: 7, class: "source",
  }));
  ends.append(el("rect", {
    x: xy[geo.target][0] - 6, y: xy[geo.target][1] - 6,
    width: 12, height: 12, class: "target",
  }));
  svg.append(ends);

  // Quoted from the same response that produced the highlighted path, so
  // the number beside the picture and the picture cannot disagree.
  render("summary", [
    ["optimum", geo.optimum.toFixed(4)],
    ["hops", geo.path.length - 1],
    ["source → target", `${geo.source} → ${geo.target}`],
    ["nodes / edges", `${geo.n_nodes} / ${geo.edges.length}`],
  ]);
}

fetch("/api/graph/geometry")
  .then((r) => r.json())
  .then(draw)
  .catch((e) => fail("summary", e));

fetch("/api/graph")
  .then((r) => r.json())
  .then((data) => render("graph", Object.entries(data)))
  .catch((e) => fail("graph", e));

fetch("/api/runs")
  .then((r) => r.json())
  .then((data) => {
    const classes = Object.entries(data.run_classes);
    render("runs", classes.length ? classes : [["(none)", "no runs found"]]);
    const warning = document.getElementById("warning");
    warning.textContent = data.warning;
    warning.hidden = false;
  })
  .catch((e) => fail("runs", e));
