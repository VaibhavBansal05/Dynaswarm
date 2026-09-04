// Pure functions: no DOM, no fetch, no globals. Every one of these is
// importable directly under node with zero shimming, which is what makes
// them the cheapest and most reliable thing in this segment to test.
//
// This is where the state/event split actually lives. The picture was
// pushing two different kinds of fact through one channel — a road's
// PRICE, which persists, and a road BREAKING, which happens once and
// fades. Splitting them here, in pure data transforms, is what makes
// app.js's rendering code a thin, mechanical translation of numbers to
// pixels rather than a place logic can drift into.
"use strict";

//: Per quiet timestep, an event's visual weight is multiplied by this.
// It is not a decoration's constant — it is RecencySignal's own `decay`
// default (control/signals.py:204), the number the allocation controller
// actually reads. The fade on screen and the signal the thesis rests on
// are the same number, so watching the flash die out IS watching the
// signal die out.
export const RECENCY_DECAY = 0.7;

//: Timesteps after which a flash contributes nothing further. 0.7**13
// is ~0.0097 — below that an added frame of fade is not distinguishable
// from zero, and this is what makes accumulation structurally bounded
// rather than merely unlikely: no event survives past this age.
export const FADE_CUTOFF = 13;

export function fadeOpacity(age, decay = RECENCY_DECAY, cutoff = FADE_CUTOFF) {
  if (age < 0 || age > cutoff) return 0;
  return decay ** age;
}

export function edgeKey(u, v) {
  return u < v ? `${u},${v}` : `${v},${u}`;
}

// Look up an event kind's visual definition. Throws on anything the
// palette does not name, deliberately: a seventh kind silently falling
// through to a default is exactly the failure this segment exists to
// close off, and the earlier six-colour table only works if "unknown"
// is loud rather than a grey line nobody notices.
export function classify(palette, kind) {
  const entry = palette[kind];
  if (!entry) {
    throw new Error(`no visual class defined for event kind ${JSON.stringify(kind)}`);
  }
  return entry;
}

// Whether a road can carry the highlighted path after this event. Mirrors
// apply_event's own grouping (core/events.py:76): closure and delete both
// deactivate; reopen and add both activate; traffic events touch neither.
export function isUsable(kind) {
  if (kind === "closure" || kind === "delete") return false;
  return true;
}

// Replay one run's events into a per-edge price/activity ledger, one
// entry per timestep — the STATE layer. This is bookkeeping, not
// computation: every price comes straight from the event's own
// `new_weight`, which the core already computed. Verified empirically
// against `GraphTimeline.state_at(t).weight` before this was written —
// see the segment's FINDINGS — so this function's contract is that it
// reproduces the core exactly, not that it approximates it.
//
// baseline: Map<edgeKey, weight-at-t=0>, built from the geometry endpoint.
// steps: the timeline endpoint's `steps` array.
// Returns: frames[t] -> Map<edgeKey, {u, v, price, active, changedAt}>.
export function buildStateFrames(baseline, steps) {
  const live = new Map();
  for (const [key, { u, v, price }] of baseline) {
    live.set(key, { u, v, price, active: true, changedAt: -1, kind: "base" });
  }
  const frames = [];
  for (const step of steps) {
    if (step.t !== frames.length) {
      throw new Error(`steps out of order: expected t=${frames.length}, got t=${step.t}`);
    }
    for (const event of step.events) {
      const key = edgeKey(event.u, event.v);
      const usable = isUsable(event.kind);
      const existing = live.get(key) ?? { u: event.u, v: event.v, price: event.new_weight };
      live.set(key, {
        u: event.u,
        v: event.v,
        price: usable ? event.new_weight : existing.price,
        active: usable,
        changedAt: step.t,
        kind: event.kind,
      });
    }
    frames.push(new Map([...live].map(([k, e]) => [k, { ...e }])));
  }
  return frames;
}

export function baselineFrom(edges, weights) {
  const baseline = new Map();
  edges.forEach(([u, v], i) => {
    baseline.set(edgeKey(u, v), { u, v, price: weights[i] });
  });
  return baseline;
}

// The state layer's own encoding: lightness, opacity and width only —
// never hue, which is reserved for the event layer so the two channels
// cannot be confused for one another.
export function stateStyle(entry, baselinePrice) {
  if (!entry.active) {
    // closure: a road that might reopen, worth a faint trace so the mesh
    // still reads as connected around it. delete: gone from the candidate
    // pool entirely — drawn as nothing, per T3's explicit distinction.
    if (entry.kind === "delete") return { visible: false };
    return { visible: true, ghost: true, opacity: 0.05, width: 0.5, dash: "1 3" };
  }
  const ratio = entry.price / baselinePrice;
  const dev = Math.max(-2, Math.min(3, Math.log2(ratio)));
  if (dev > 0.02) {
    // Dearer: more salient, because it is the direction worth noticing.
    return { visible: true, ghost: false, opacity: Math.min(0.85, 0.15 + dev * 0.22), width: 0.6 + dev * 0.6, dash: "none" };
  }
  if (dev < -0.02) {
    // Cheaper: recedes toward the background rather than standing out.
    return { visible: true, ghost: false, opacity: Math.max(0.06, 0.15 + dev * 0.05), width: 0.5, dash: "none" };
  }
  return { visible: true, ghost: false, opacity: 0.12, width: 0.6, dash: "none" };
}

// Scale and centre only — segment 7's rule, unmoved.
export function projector(positions, viewW, viewH, pad) {
  const xs = positions.map((p) => p[0]);
  const ys = positions.map((p) => p[1]);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const span = Math.max(maxX - minX, maxY - minY) || 1;
  const scale = Math.min(viewW - 2 * pad, viewH - 2 * pad) / span;
  const offX = (viewW - (maxX - minX) * scale) / 2;
  const offY = (viewH - (maxY - minY) * scale) / 2;
  return ([x, y]) => [(x - minX) * scale + offX, (y - minY) * scale + offY];
}
