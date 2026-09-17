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

function makeElement(tag, value = "") {
  return {
    tag,
    value,
    max: "",
    children: [],
    attrs: {},
    style: {},
    hidden: false,
    checked: false,
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

// Element ids and their default values are read out of the real
// index.html rather than listed here. A hand-maintained list is a
// fixture, and a fixture that falls behind the page tests itself — the
// failure this project has hit twice already. Adding a control to the
// page now automatically gives the harness that control.
function pageElements() {
  const html = readFileSync(path.join(STATIC, "index.html"), "utf8");
  const found = new Map();
  for (const m of html.matchAll(/<(\w+)([^>]*\bid="([^"]+)"[^>]*)>/g)) {
    const [, , attrs, id] = m;
    const value = /\bvalue="([^"]*)"/.exec(attrs);
    const selected = /<option value="([^"]*)"[^>]*\bselected\b/;
    found.set(id, value ? value[1] : "");
    void selected;
  }
  // <select> carries its value on the selected <option>, not on itself.
  for (const m of html.matchAll(/<select[^>]*\bid="([^"]+)"[^>]*>([\s\S]*?)<\/select>/g)) {
    const [, id, body] = m;
    const chosen = /<option value="([^"]*)"[^>]*selected/.exec(body)
      ?? /<option value="([^"]*)"/.exec(body);
    found.set(id, chosen ? chosen[1] : "");
  }
  return found;
}

/**
 * Load the real app.js under node, with document/fetch/timers shimmed.
 *
 * @param fixtures {{ geometry: object, timeline: object, palette: object }}
 *   Canned responses for the three endpoints app.js fetches on load.
 * @returns {Promise<{nodes: object, test: object}>}
 *   `nodes` is every shimmed element, keyed by id. `calls` is every
 *   fetch the page made, in order, with method and body. `test` is the hook
 *   app.js exposes on `globalThis.__TEST__` when it is present — see
 *   the guard at the bottom of app.js. Real internal state, not a
 *   reimplementation of it.
 */
export async function loadPage(fixtures) {
  const nodes = {};
  for (const [id, value] of pageElements()) nodes[id] = makeElement("el", value);

  globalThis.document = {
    getElementById: (id) => nodes[id] ?? null,
    createElement: (tag) => makeElement(tag),
    createElementNS: (_ns, tag) => makeElement(tag),
    createTextNode: (text) => ({ text }),
    addEventListener() {},
    // Narrow on purpose: only the selectors app.js actually uses are
    // supported, and an unknown one throws rather than quietly returning
    // an empty list. A shim that answers every query with "nothing found"
    // makes a broken selector look like an empty page.
    querySelectorAll(selector) {
      if (selector === "#arm-picks input:checked") {
        return nodes["arm-picks"].children
          .flatMap((label) => label.children)
          .filter((el) => el.tag === "input" && el.checked);
      }
      throw new Error(`unshimmed selector: ${selector}`);
    },
    querySelector(selector) {
      const found = this.querySelectorAll(selector);
      return found[0] ?? null;
    },
  };

  const routes = {
    "/api/graph/geometry": fixtures.geometry,
    "/api/graph": fixtures.world ?? fixtures.geometry,
    "/api/timeline": fixtures.timeline,
    "/static/palette.json": fixtures.palette,
    "/api/runs": fixtures.runs ?? { run_classes: {} },
    "/api/run": fixtures.started ?? { run_id: "fixture-run", run_class: "exploratory" },
    "/api/run/fixture-run": fixtures.raced ?? null,
    "/api/run/fixture-run/score": fixtures.score ?? null,
  };
  // Records what the page asked for, so a test can assert that Stage 1
  // and Stage 2 actually POST rather than merely that they rendered.
  const calls = [];
  globalThis.fetch = async (url, init) => {
    const p = String(url).replace(/^https?:\/\/[^/]+/, "");
    calls.push({ path: p, method: init?.method ?? "GET", body: init?.body });
    if (!(p in routes)) throw new Error(`unshimmed fetch: ${p}`);
    // Cloned, not shared. Handing every test the same fixture object let
    // one test's mutation of `state.run.steps` leak into the next five —
    // a real HTTP response is fresh each time, and the harness has to be
    // too, or tests pass or fail depending on their order.
    return { ok: true, status: 200, json: async () => structuredClone(routes[p]) };
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

  return { nodes, calls, test: globalThis.__TEST__ };
}

export function readFixture(name) {
  return JSON.parse(readFileSync(path.join(HERE, "fixtures", name), "utf8"));
}
