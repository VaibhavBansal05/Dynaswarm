"""Dynaswarm PPT Builder – Part 2: slides 12-22 (Methodology + Implementation)"""
import sys
sys.path.insert(0, '/home/vaibhav/ML_PROJECT/dynaswarm')
from make_ppt_p1 import *

prs.save   # already imported; prs is built up to slide 11

# Re-run part 1 silently to get prs back
exec(open('/home/vaibhav/ML_PROJECT/dynaswarm/make_ppt_p1.py').read())

# ── Slide 12: System Architecture ────────────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "METHODOLOGY")
slide_title(sl, "Layered System Architecture")
add_image(sl, IMG_ARCH, 0.4, 1.5, 6.1, 5.75)
layers = [
    ("CLI",         "Hydra entrypoint · run / tune / analyse / replay"),
    ("TUNING",      "Optuna TPE · seed-separated tuning vs evaluation"),
    ("HARNESS",     "run_trial · build_arms · EvaluationMeter"),
    ("CONTROL",     "4 signals · 3 controllers"),
    ("OPTIMIZERS",  "A* · MMAS ACO · priority PSO · Hybrid"),
    ("CORE / ENVIRONMENT", "GraphView (CSR) · Timeline · Events · Oracle · RNG"),
    ("IO / ANALYSIS", "Parquet + manifest · Wilcoxon/Holm · Recovery · Plots"),
]
cy = 1.55
for name, detail in layers:
    txb(sl, name, 6.75, cy, 2.6, 0.37, size=11, bold=True, colour=ACCENT)
    txb(sl, detail, 9.35, cy, 3.6, 0.5, size=11, colour=LGREY)
    cy += 0.62
txb(sl, "Key principles:", 6.75, 6.35, 3, 0.35, size=12, bold=True, colour=GOLD)
txb(sl, "Immutable shared world  ·  Budget in work not iterations  ·  Pluggable controllers",
    6.75, 6.68, 6.2, 0.6, size=11, colour=WHITE, italic=True)

# ── Slide 13: Environment ─────────────────────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "METHODOLOGY")
slide_title(sl, "Environment: Dynamic Graph Model")
txb(sl, "Graph Models", 0.4, 1.55, 5.5, 0.4, size=16, bold=True, colour=GOLD)
models = [
    ("Erdős–Rényi (n=30)", "Demo/debug only. No coordinates. A* = Dijkstra."),
    ("Geometric (n=200) ★", "PRIMARY TIER. Euclidean heuristic. Realistic topology."),
    ("Grid (n=400)",        "Worst case for A* pruning. Manhattan metric."),
]
cy = 2.0
for name, desc in models:
    txb(sl, "▸ " + name, 0.4, cy, 5.5, 0.35, size=13, bold=True, colour=ACCENT)
    txb(sl, desc, 0.4, cy + 0.33, 5.5, 0.35, size=12, colour=WHITE)
    cy += 0.8
txb(sl, "Disruption Events", 6.4, 1.55, 6.5, 0.4, size=16, bold=True, colour=GOLD)
headers = ["Event", "Effect"]
rows = [
    ["Closure",     "Weight → ∞"],
    ["Traffic Up",  "Weight × 2.0"],
    ["Traffic Down","Weight ÷ 2.0"],
    ["Reopen",      "New weight at free-flow"],
    ["Delete",      "Edge deactivated"],
    ["Add",         "Pool edge activated"],
]
table_slide_data(sl, headers, rows, 6.4, 1.95, 6.5, 3.2)
txb(sl, "Rate: Poisson(λ), λ ∈ {0, 0.1, 0.3, 0.8}  ·  Cluster size: 25 edges",
    6.4, 5.35, 6.5, 0.4, size=12, colour=LGREY)
callout(sl,
    "Pre-materialised timeline: entire event sequence frozen before any optimizer runs.\n"
    "Every arm sees byte-identical graph states — verified by BLAKE2b hash.",
    0.4, 5.6, 12.5, 1.1, border=ACCENT, size=13)

# ── Slide 14: A* and ACO ──────────────────────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "METHODOLOGY")
slide_title(sl, "Algorithms: A* (Oracle) and MAX-MIN ACO")
divider(sl, 1.55, colour=LGREY, w_in=0.0)   # vertical hint
txb(sl, "A* — Reference Oracle", 0.4, 1.55, 6.1, 0.45, size=18, bold=True, colour=GREEN)
txb(sl, "f(n) = g(n) + h(n)\n  g(n) = cost from source\n  h(n) = Euclidean dist × weight_scale",
    0.4, 2.05, 6.1, 1.0, size=14, colour=ACCENT)
bullet_block(sl, [
    "Admissible heuristic: never overestimates",
    "Stateless: full re-search every timestep",
    "Provides c*(G⁽ᵗ⁾) — the moving optimum",
    "Expansion count = cost-of-recomputation metric",
], 0.4, 3.1, 6.1, 2.5, size=13, colour=WHITE)
txb(sl, "MAX-MIN ACO", 6.9, 1.55, 6.1, 0.45, size=18, bold=True, colour=GOLD)
txb(sl, "P(i→j) ∝ τᵢⱼᵅ × ηᵢⱼᵝ\n  η = 1/(w + γ·h)  [goal-directed visibility]",
    6.9, 2.05, 6.1, 0.9, size=14, colour=ACCENT)
bullet_block(sl, [
    "Each iteration: Evaporate → Reinforce best → Clamp",
    "τ_max = 1/(ρ·C_best),  τ_min = τ_max/2n",
    "Bounds cap ratio at 2n: keeps evaporation meaningful",
    "Stale trail on closed road = the phenomenon under study",
], 6.9, 3.1, 6.1, 2.5, size=13, colour=WHITE)
divider(sl, 5.7, colour=LGREY, w_in=12.5)
txb(sl, "Without goal-direction (γ=0): colony settled 90% above optimum on n=200 graphs",
    0.4, 5.8, 12.5, 0.4, size=12, colour=RED, italic=True)

# ── Slide 15: PSO & Hybrid ────────────────────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "METHODOLOGY")
slide_title(sl, "Algorithms: Priority-Vector PSO and the Hybrid")
txb(sl, "Priority-Vector PSO", 0.4, 1.55, 6.1, 0.45, size=18, bold=True, colour=ACCENT)
txb(sl, "Each particle: x ∈ [0,1]ⁿ  (one priority per node)\nPath: greedy argmax priority[v]·η(u,v)",
    0.4, 2.05, 6.1, 0.85, size=13, colour=WHITE)
txb(sl, "v ← w·v + c₁r₁(p_best−x) + c₂r₂(g_best−x)\nx ← clip(x+v, 0, 1)",
    0.4, 2.95, 6.1, 0.85, size=13, colour=ACCENT)
bullet_block(sl, [
    "On disruption: positions kept, costs invalidated",
    "Global best position always kept (dropping it costs +90% excess)",
    "Dead-end repair: perturb & retry up to R times",
], 0.4, 3.85, 6.1, 1.8, size=13, colour=WHITE)
txb(sl, "Hybrid ACO-PSO", 6.9, 1.55, 6.1, 0.45, size=18, bold=True, colour=GOLD)
bullet_block(sl, [
    "Budget split: B_ACO = round(B×f),  B_PSO = B−B_ACO",
    "f ∈ [0.05, 0.95] — the allocation controller target",
    "Colony→Swarm: boost priorities along ACO path (+0.25)",
    "Swarm→Colony: deposit 1/cost trail on PSO path",
    "Exchange gain 0.25: nudge, not domination",
], 6.9, 2.05, 6.1, 3.3, size=13, colour=WHITE)
callout(sl, "Bet: memoryless PSO covers ACO's staleness window immediately after disruption.",
        6.9, 5.5, 6.1, 0.75, border=GOLD, size=13)
callout(sl, "NOT edge-weight bias (= Dijkstra in disguise). Priority-vector encodes node importance.",
        0.4, 5.5, 6.1, 0.75, border=RED, size=12)

# ── Slide 16: Adaptive Controller ────────────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "METHODOLOGY")
slide_title(sl, "Adaptive Controller: Sense → Propose → Apply")
add_image(sl, IMG_LOOP, 7.1, 1.4, 5.8, 4.3)
headers = ["Signal", "Formula", "Range", "Limitation"]
rows = [
    ["Edge Ratio",  "mean(K / |E|) over window",   "[0, ∞)", "Graph-size dependent; tiny on n=200"],
    ["Volatility",  "mean(K > 0) over window",      "[0, 1]", "Saturates at λ≈1 on large graphs"],
    ["λ-Branching", "mean competitive arcs (ACO)",  "[1, d̄]", "Stagnation detector, NOT volatility"],
    ["Recency ★",   "1.0 on event; ×0.7 each quiet step", "[0,1]","Best for E4 — transient signal"],
]
table_slide_data(sl, headers, rows, 0.4, 1.55, 6.4, 3.5)
txb(sl, "★ Recency preferred for allocation experiment: peaks at staleness, decays geometrically.",
    0.4, 5.9, 12.5, 0.45, size=13, colour=GOLD, italic=True)
txb(sl, "One target at a time — moving several parameters together would make it impossible\nto attribute an effect to any single one.",
    0.4, 6.4, 12.5, 0.7, size=12, colour=LGREY, italic=True)

# ── Slide 17: Controller Update Rule ─────────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "METHODOLOGY")
slide_title(sl, "Controller: Incremental Update Rule")
txb(sl, "Algorithm (one adaptation step):", 0.4, 1.55, 7, 0.4, size=15, bold=True, colour=GOLD)
steps = [
    "1.  pressure δ  =  ξ · σ(t)  −  baseline",
    "2.  baseline  ←  baseline + αb · δ          [EMA update]",
    "3.  If |δ| > deadband  AND  t mod p == 0:",
    "       step = +Δ if δ > 0  else  −Δ",
    "       θk  ←  clip(θk + sign_k · step,  θ_min,  θ_max)",
]
cy = 1.98
for s in steps:
    txb(sl, s, 0.5, cy, 7.5, 0.38, size=13, colour=WHITE)
    cy += 0.38
headers = ["Parameter", "sign_k", "Why"]
rows = [
    ["ρ  (evaporation)", "+1", "Faster evaporation = forgets sooner → explore"],
    ["α  (trail exp.)",  "−1", "Higher α trusts trail → exploit"],
    ["β  (visibility)",  "−1", "Higher β is greedy → exploit"],
    ["aco_fraction f",   "−1", "Lower f = more PSO budget = explore"],
]
table_slide_data(sl, headers, rows, 7.8, 1.55, 5.1, 3.3)
callout(sl,
    "Σ = 0.001 per step — a misread costs one-thousandth of a parameter unit.\n"
    "Increments, not preset jumps: evidence accumulates; one bad reading costs little.",
    0.4, 5.35, 12.5, 1.1, border=ACCENT, size=13)

# ── Slide 18: Fair Evaluation Harness ────────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "METHODOLOGY")
slide_title(sl, "The Fair Evaluation Harness")
headers = ["Design Commitment", "How It Is Enforced"]
rows = [
    ["Every arm sees identical world",
     "Pre-materialised timeline; BLAKE2b hash asserted per arm per step"],
    ["Equal budget = equal work",
     "Budget in candidate-path constructions, metered by harness not self-reported"],
    ["Arms cannot disturb each other",
     "RNG streams content-addressed by family name; inserting arm doesn't rewire others"],
    ["Tuning ≠ evaluation seeds",
     "Harness raises ValueError if tune_seeds ∩ eval_seeds ≠ ∅"],
    ["Null controller comparable",
     "NullController takes identical code path; differs only in propose() returning unchanged params"],
]
table_slide_data(sl, headers, rows, 0.4, 1.55, 12.5, 4.8)
txb(sl, "Three in-loop assertions (fail loudly, not silently):", 0.4, 6.45, 7, 0.35, size=12, bold=True, colour=GOLD)
txb(sl, "arm cost ≥ true optimum  ·  state hash unchanged after rebind  ·  all arms got identical state hash",
    0.4, 6.8, 12.5, 0.4, size=12, colour=WHITE)

# ── Slide 19: Tech Stack ──────────────────────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "IMPLEMENTATION")
slide_title(sl, "Technology Stack & Project Scale")
txb(sl, "Stack", 0.4, 1.55, 5.5, 0.4, size=18, bold=True, colour=GOLD)
stack = [
    "Python 3.10+  +  NumPy  +  SciPy",
    "Hydra (config)  +  Optuna (tuning)",
    "Apache Parquet (results storage)",
    "Pygame (network visualizer)",
    "pytest (271 tests, ~60s)",
    "python-pptx (this presentation)",
]
bullet_block(sl, stack, 0.4, 2.0, 5.5, 3.5, size=14)
txb(sl, "Scale", 6.5, 1.55, 6.3, 0.4, size=18, bold=True, colour=GOLD)
scale = [
    "7 sub-packages, ~10 core modules",
    "271 pytest tests, run in ~60 seconds",
    "786-line LaTeX academic paper (auto-compiled to PDF)",
    "1,377-line DOCUMENTATION.md",
    "Results: steps.parquet — 1 row per arm per timestep",
    "Headline study: 4 arms × 4 scenarios × 30 trials, geometric n=200",
]
bullet_block(sl, scale, 6.5, 2.0, 6.3, 3.5, size=14)
divider(sl, 5.75)
txb(sl, "Every run writes: manifest.json · steps.parquet · events.parquet · figures/ · .hydra/config.yaml",
    0.4, 5.85, 12.5, 0.45, size=12, colour=LGREY, italic=True)

# ── Slide 20: CSR Graph & RNG ─────────────────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "IMPLEMENTATION")
slide_title(sl, "Key Engineering: CSR Graph & Reproducible RNG")
txb(sl, "CSR Graph Structure", 0.4, 1.55, 6.1, 0.4, size=16, bold=True, colour=ACCENT)
bullet_block(sl, [
    "Static topology superset allocated once per trial",
    "weight[] and active[] — frozen numpy arrays; read-only for all arms",
    "Addition events use pre-allocated pool (no O(N²) rebuild)",
    "BLAKE2b hash verifies no arm mutated the shared world",
    "Deactivated slots retain trail — stale memory studied directly",
], 0.4, 2.0, 6.1, 3.0, size=13)
txb(sl, "Reproducible RNG Architecture", 6.9, 1.55, 6.1, 0.4, size=16, bold=True, colour=ACCENT)
bullet_block(sl, [
    "stream(seed, *tags) — content-addressed generator",
    "Tags are names, not indices: new arm doesn't disturb others",
    "tune_seeds [9000–9016) ∩ eval_seeds [1000–1032) = ∅",
    "Same config → byte-identical steps.parquet (verified by test)",
    "Two ablation arms share family key → differ only in controller",
], 6.9, 2.0, 6.1, 3.0, size=13)
callout(sl,
    "ACO inner loop uses Python lists (not numpy) for ~12-element candidate sets: 26–28× speedup\n"
    "(n=200 geo: 4039µs → 143µs per construction). Pre-filled random buffer avoids per-roulette numpy call.",
    0.4, 5.25, 12.5, 1.0, border=GOLD, size=13)

# ── Slide 21: Performance Optimisations ──────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "IMPLEMENTATION")
slide_title(sl, "Performance: Making Large-Scale Tuning Feasible")
items = [
    ("Python lists for ACO inner loop",
     "200-node graph, degree ≈18, candidate set ≈12 elements. NumPy dispatch overhead dominated data work.\nProfiling: 72% of runtime in _construct(). Switching to Python lists → 26–28× speedup (measured, not estimated)."),
    ("Pre-filled random buffer (4096 draws)",
     "Avoids one numpy.random call per roulette-wheel selection step.\nBuffer refilled when exhausted; no RNG state drift."),
    ("Bulk numpy for evaporate / deposit / clamp",
     "Vectorised over all slots simultaneously: τ ← τ×(1−ρ), clamping, deposition all in one pass.\nOnly the stochastic selection loop remains in Python."),
    ("Joblib parallelism over trials",
     "Each trial is independent; parallel_jobs=11 runs 11 trials simultaneously.\nOptuna tuning is sequential (TPE sampler) but trial objective is parallelised."),
]
cy = 1.6
for title, body in items:
    txb(sl, "▸ " + title, 0.4, cy, 12.5, 0.38, size=14, bold=True, colour=GOLD)
    txb(sl, body, 0.4, cy+0.38, 12.5, 0.65, size=12, colour=WHITE)
    cy += 1.15

# ── Slide 22: Configuration & CLI ────────────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "IMPLEMENTATION")
slide_title(sl, "Configuration System & CLI")
txb(sl, "Hydra Dataclass Config", 0.4, 1.55, 5.5, 0.4, size=15, bold=True, colour=GOLD)
cfg = ("Config\n"
       "├── graph:     n_nodes, model, density\n"
       "├── scenario:  events_per_step, cluster_size\n"
       "├── experiment: arms[], n_trials, seeds\n"
       "├── budget:    evaluations = 300\n"
       "└── control:   signal, targets, sigma")
txb(sl, cfg, 0.4, 2.0, 5.5, 2.5, size=12, colour=ACCENT)
txb(sl, "Example CLI Commands", 6.4, 1.55, 6.6, 0.4, size=15, bold=True, colour=GOLD)
cli = ("# Main experiment\npython -m dynaswarm.cli \\\n  graph=medium200 scenario=high \\\n"
       "  'experiment.arms=[aco,hybrid]' report=true\n\n"
       "# Allocation thesis (E4)\npython -m dynaswarm.cli --multirun \\\n"
       "  control.signal=recency \\\n  'control.targets=[aco_fraction]' \\\n"
       "  'experiment.arms=[hybrid_fixed,hybrid_adaptive]'\n\n"
       "# Tune parameters\npython -m dynaswarm.cli \\\n  tuning.enabled=true tuning.arm=hybrid \\\n"
       "  tuning.candidates=60 tuning.trials=12")
txb(sl, cli, 6.4, 2.0, 6.6, 4.5, size=10, colour=WHITE)
txb(sl, "Every run is fully reproducible: .hydra/config.yaml + manifest.json capture exact state.",
    0.4, 5.4, 12.5, 0.45, size=12, colour=LGREY, italic=True)

prs.save("/tmp/dynaswarm_ppt_p2.prs")
print("Part 2 saved — 22 slides total")
