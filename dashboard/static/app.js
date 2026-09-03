// Fetch and render as text. No canvas, no SVG, no drawing — that is
// segments 7 onward. This file exists to prove the pipe carries real
// values, so it deliberately does the least possible with them.
"use strict";

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
