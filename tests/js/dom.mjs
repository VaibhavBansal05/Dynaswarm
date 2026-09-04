// The render harness — moved into the repository per Entry 008 R1.
//
// It has been rewritten from scratch three times in a scratchpad across
// segments 6, 7 and 8, and every "what the page actually renders"
// artefact in those segments' FINDINGS came from it. This is that same
// approach, written once and versioned, so the next segment extends it
// instead of reinventing it.
//
// It is deliberately small: enough DOM to let app.js run its real code
// unmodified (via a genuine file:// import, so app.js's own `import
// "./model.js"` resolves exactly as the browser would resolve it), and
// a fetch shim that serves fixture JSON instead of requiring a live
// server. No third-party test or DOM library is used.
import { pathToFileURL } from "node:url";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const STATIC = path.resolve(HERE, "../../dashboard/static");

function makeElement(tag) {
  return {
    tag,
    children: [],
    attrs: {},
    style: {},
    hidden: false,
    _text: "",
    classList: {
      _set: new Set(),
      toggle(name, on) {
        if (on) this._set.add(name);
        else this._set.delete(name);
      },
      has(name) { return this._set.has(name); },
    },
    set textContent(v) { this._text = String(v); },
    get textContent() { return this._text; },
    setAttribute(k, v) { this.attrs[k] = v; },
    removeAttribute(k) { delete this.attrs[k]; },
    replaceChildren(...kids) { this.children = kids; },
    append(...kids) { this.children.push(...kids); },
    addEventListener() {},
  };
}

// One fixed set of ids: every element app.js's index.html declares.
const ELEMENT_IDS = [
  "canvas", "refusal", "readout", "controls", "back", "play", "fwd",
  "scrub", "runs", "warning", "legend-events",
];

/**
 * Load the real app.js under node, with document/fetch/timers shimmed.
 *
 * @param fixtures {{ geometry: object, timeline: object, palette: object }}
 *   Canned responses for the three endpoints app.js fetches on load.
 * @returns {Promise<{nodes: object, test: object}>}
 *   `nodes` is every shimmed element, keyed by id. `test` is the hook
 *   app.js exposes on `globalThis.__TEST__` when it is present — see
 *   the guard at the bottom of app.js. Real internal state, not a
 *   reimplementation of it.
 */
export async function loadPage(fixtures) {
  const nodes = {};
  for (const id of ELEMENT_IDS) nodes[id] = makeElement("el");

  globalThis.document = {
    getElementById: (id) => nodes[id] ?? null,
    createElement: (tag) => makeElement(tag),
    createElementNS: (_ns, tag) => makeElement(tag),
    createTextNode: (text) => ({ text }),
    addEventListener() {},
  };

  const routes = {
    "/api/graph/geometry": fixtures.geometry,
    "/api/timeline": fixtures.timeline,
    "/static/palette.json": fixtures.palette,
    "/api/runs": fixtures.runs ?? { run_classes: {}, warning: "" },
  };
  globalThis.fetch = async (url) => {
    const p = String(url).replace(/^https?:\/\/[^/]+/, "");
    if (!(p in routes)) throw new Error(`unshimmed fetch: ${p}`);
    return { json: async () => routes[p] };
  };

  globalThis.setInterval = () => 0;
  globalThis.clearInterval = () => {};
  globalThis.__TEST__ = {};

  const url = pathToFileURL(path.join(STATIC, "app.js")).href;
  // Cache-bust: node's ESM loader caches by URL, and every test in a
  // file that reloads app.js needs a fresh module instance with fresh
  // top-level state, not the first run's.
  await import(`${url}?t=${Date.now()}-${Math.random()}`);
  await new Promise((resolve) => setTimeout(resolve, 50));

  return { nodes, test: globalThis.__TEST__ };
}

export function readFixture(name) {
  return JSON.parse(readFileSync(path.join(HERE, "fixtures", name), "utf8"));
}
