"""Dynaswarm PPT Builder - Part 1: helpers + slides 1-11"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import pptx.oxml.ns as nsmap
from lxml import etree
import copy, os

# ── Colours ──────────────────────────────────────────────────
BG      = RGBColor(0x0D, 0x1B, 0x2A)   # dark navy
ACCENT  = RGBColor(0x00, 0xD4, 0xFF)   # cyan
GOLD    = RGBColor(0xFF, 0xC0, 0x00)   # gold
WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
LGREY   = RGBColor(0xB0, 0xBE, 0xCC)
RED     = RGBColor(0xFF, 0x45, 0x45)
GREEN   = RGBColor(0x4C, 0xAF, 0x50)

W, H = Inches(13.33), Inches(7.5)      # 16:9

IMG_DIR = "/home/vaibhav/.gemini/antigravity/brain/3d615667-be85-4a4c-a2b0-e14d448bcb21"

def new_prs():
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    return prs

def set_bg(slide, colour=BG):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = colour

def txb(slide, text, x, y, w, h, size=18, bold=False, colour=WHITE,
        align=PP_ALIGN.LEFT, italic=False):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = colour
    return tb

def divider(slide, y, colour=ACCENT, w_in=12.5, x_in=0.4):
    line = slide.shapes.add_connector(
        1, Inches(x_in), Inches(y), Inches(x_in + w_in), Inches(y))
    line.line.color.rgb = colour
    line.line.width = Pt(1.5)

def section_tag(slide, label):
    txb(slide, label, 0.4, 0.1, 4, 0.35, size=9, colour=ACCENT, bold=True)

def slide_title(slide, title, y=0.55):
    txb(slide, title, 0.4, y, 12.5, 0.8, size=30, bold=True, colour=WHITE)
    divider(slide, y + 0.85)

def bullet_block(slide, items, x, y, w, h, size=15, colour=WHITE, gap=0.38):
    cy = y
    for item in items:
        prefix, rest = ("• ", item) if not item.startswith("  ") else ("  – ", item.strip())
        txb(slide, prefix + rest, x, cy, w, gap + 0.05, size=size, colour=colour)
        cy += gap
    return cy

def table_slide_data(slide, headers, rows, x, y, w, h, hdr_col=ACCENT):
    """Draw a simple table using textboxes."""
    cols = len(headers)
    cw = w / cols
    rh = 0.32
    # header
    for i, hdr in enumerate(headers):
        txb(slide, hdr, x + i*cw, y, cw, rh, size=12, bold=True, colour=hdr_col)
    divider(slide, y + rh, colour=ACCENT, w_in=w, x_in=x)
    # rows
    for ri, row in enumerate(rows):
        ry = y + rh + 0.05 + ri * rh
        bg_col = RGBColor(0x14, 0x2A, 0x3E) if ri % 2 == 0 else RGBColor(0x0D, 0x1B, 0x2A)
        for ci, cell in enumerate(row):
            c = GOLD if ci == 0 else WHITE
            txb(slide, str(cell), x + ci*cw, ry, cw - 0.05, rh, size=11, colour=c)

def callout(slide, text, x, y, w, h, border=ACCENT, size=14):
    shape = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(0x0A, 0x22, 0x38)
    shape.line.color.rgb = border
    shape.line.width = Pt(2)
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.15)
    tf.margin_top = tf.margin_bottom = Inches(0.1)
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.color.rgb = WHITE
    run.font.italic = True

def add_image(slide, path, x, y, w, h):
    if os.path.exists(path):
        slide.shapes.add_picture(path, Inches(x), Inches(y), Inches(w), Inches(h))

# ══════════════════════════════════════════════════════════════
# BUILD PRESENTATION
# ══════════════════════════════════════════════════════════════
prs = new_prs()
IMG_NET  = IMG_DIR + "/network_disruption_1787198421387.png"
IMG_DIAL = IMG_DIR + "/explore_exploit_dial_1787198434843.png"
IMG_ARCH = IMG_DIR + "/system_architecture_1787198449747.png"

# ── Slide 1: Title ────────────────────────────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
add_image(sl, IMG_NET, 7.2, 1.0, 5.8, 5.5)
# dark overlay on right side already handled by image bg
txb(sl, "DYNASWARM", 0.4, 1.2, 7.0, 1.2, size=52, bold=True, colour=ACCENT)
txb(sl, "Volatility-Driven Compute Allocation in\nHybrid Swarm Metaheuristics\nfor Dynamic Path Optimisation",
    0.4, 2.5, 6.8, 1.8, size=18, colour=WHITE)
divider(sl, 4.5, w_in=6.5)
txb(sl, "Vaibhav Krishna Bansal  ·  Rudra Rajpurohit  ·  Kartikey Goyal  ·  Pavit Agrawal",
    0.4, 4.6, 9.5, 0.4, size=13, colour=LGREY)
txb(sl, "Mentor: Mrs. Vidhya V  |  School of Computer Engineering, MIT Manipal (MAHE)",
    0.4, 5.05, 9.5, 0.4, size=12, colour=LGREY)
txb(sl, "Minor Project  ·  2026", 0.4, 5.5, 4, 0.35, size=11, colour=GOLD)

# ── Slide 2: Introduction – Real World Problem ────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "INTRODUCTION")
slide_title(sl, "Why does routing need intelligence?")
add_image(sl, IMG_NET, 7.8, 1.5, 5.1, 4.8)
bullets = [
    "Road networks change continuously: closures, traffic spikes, link additions",
    "Classical routing (GPS, Dijkstra) recomputes from scratch — exact but expensive at scale",
    "Swarm algorithms maintain a population that learns over time — but parameters must be tuned",
    "A fixed parameter setting cannot adapt when disruption rate changes mid-trial",
]
bullet_block(sl, bullets, 0.4, 1.6, 7.2, 4.5, size=16)

# ── Slide 3: Exploration vs Exploitation ─────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "INTRODUCTION")
slide_title(sl, "The Core Tension Every Swarm Algorithm Faces")
add_image(sl, IMG_DIAL, 2.5, 1.6, 8.3, 4.5)
txb(sl, "EXPLOIT", 0.4, 3.0, 2.2, 0.5, size=20, bold=True, colour=GOLD)
txb(sl, "Refine what looks good\nFast convergence\nBlind to change", 0.4, 3.55, 2.2, 1.2, size=13, colour=GOLD)
txb(sl, "EXPLORE", 10.7, 3.0, 2.2, 0.5, size=20, bold=True, colour=ACCENT)
txb(sl, "Keep sampling\nAdapts to change\nWastes effort when stable", 10.7, 3.55, 2.2, 1.2, size=13, colour=ACCENT)
txb(sl, "The optimal balance shifts with how fast the environment is changing.",
    2.5, 6.1, 8.3, 0.5, size=14, italic=True, colour=LGREY, align=PP_ALIGN.CENTER)

# ── Slide 4: Central Question ─────────────────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "INTRODUCTION")
slide_title(sl, "One Question, Rigorously Answered")
callout(sl,
    '"When searching for shortest paths through a dynamically disrupted network, does automatically\n'
    'retuning the algorithm\'s exploration–exploitation parameters in real time beat a carefully\n'
    'tuned static configuration?"',
    0.4, 1.6, 12.5, 1.9, border=ACCENT, size=16)
bullets = [
    "Four algorithms: A*, MAX-MIN ACO, Priority-Vector PSO, Hybrid ACO-PSO",
    "Adaptive controller that senses volatility and adjusts parameters/budget allocation",
    "400 independent trials · Wilcoxon signed-rank · Holm correction · Cliff's δ effect size",
    "Pre-materialised shared world — no arm gets an easier graph than another",
]
bullet_block(sl, bullets, 0.4, 3.7, 12.5, 3.2, size=15)

# ── Slide 5: Problem Statement – Formal ───────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "PROBLEM STATEMENT")
slide_title(sl, "Dynamic Shortest Path Problem (DSPP)")
txb(sl, "Network modelled as a dynamic weighted graph:", 0.4, 1.55, 12, 0.4, size=15, colour=LGREY)
txb(sl, "  G⁽ᵗ⁾ = (V,  E⁽ᵗ⁾,  w⁽ᵗ⁾)   —   fixed vertices, changing edges and weights",
    0.4, 1.95, 12, 0.4, size=16, bold=True, colour=ACCENT)
txb(sl, "Goal: at each timestep t, find path π⁽ᵗ⁾ from source s to target q minimising total cost c(π).",
    0.4, 2.5, 12, 0.4, size=15, colour=WHITE)
txb(sl, "Primary quality metric — Excess over the moving optimum:",
    0.4, 3.1, 12, 0.35, size=15, colour=LGREY)
txb(sl, "  ε⁽ᵗ⁾ = c(π̂⁽ᵗ⁾) / c*(G⁽ᵗ⁾) − 1  ≥ 0",
    0.4, 3.45, 8, 0.5, size=20, bold=True, colour=GOLD)
callout(sl,
    "Raw path cost is not comparable across timesteps — the network gets cheaper or costlier.\n"
    "Normalising against the moving optimum (A* recomputed each step) removes that confound.",
    0.4, 4.15, 12.5, 1.1, border=GOLD, size=13)
txb(sl, "A* scores exactly 0.0% excess by construction — it IS the denominator.",
    0.4, 5.5, 12, 0.45, size=14, colour=GREEN, bold=True)

# ── Slide 6: Algorithm Weaknesses ────────────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "PROBLEM STATEMENT")
slide_title(sl, "Why Existing Algorithms Fail Under Dynamic Conditions")
headers = ["", "A* / Dijkstra", "ACO", "PSO"]
rows = [
    ["Memory", "None", "Pheromone trails", "Particle positions"],
    ["On disruption", "Full re-search", "Trail goes STALE", "Swarm CONVERGED"],
    ["Cost", "Grows with |V|, |E|", "Fixed budget", "Fixed budget"],
    ["Adaptability", "None", "Slow (depends on ρ)", "Low (no edge memory)"],
]
table_slide_data(sl, headers, rows, 0.4, 1.55, 12.5, 4.0)
txb(sl, "Neither pure method handles the transition window after a disruption well.",
    0.4, 6.3, 12.5, 0.45, size=13, colour=RED, italic=True)

# ── Slide 7: Gap & Hypothesis ─────────────────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "PROBLEM STATEMENT")
slide_title(sl, "The Research Gap & Hypothesis")
txb(sl, "What's known:", 0.4, 1.55, 6.0, 0.35, size=14, bold=True, colour=GOLD)
bullet_block(sl, [
    "Parameter quality matters enormously — Stützle et al. (2000)",
    "Online adaptation yields negligible gain over a well-tuned fixed setting",
    "Most studies use small graphs where pheromone is nearly irrelevant",
], 0.4, 1.95, 6.0, 2.2, size=13, colour=LGREY)
txb(sl, "What's NOT tested:", 6.8, 1.55, 6.1, 0.35, size=14, bold=True, colour=ACCENT)
bullet_block(sl, [
    "Budget allocation between components as a sensing-driven variable",
    "Joint control of signal choice, controller design, and statistical fairness",
    "Recency-driven PSO↔ACO split immediately after a disruption",
], 6.8, 1.95, 6.1, 2.2, size=13, colour=WHITE)
divider(sl, 4.4)
txb(sl, "Project Hypothesis:", 0.4, 4.5, 4, 0.4, size=15, bold=True, colour=GOLD)
callout(sl,
    "In a hybrid metaheuristic, the allocation of compute between exploration and exploitation "
    "components should be driven by measured environmental volatility — not parameter values.",
    0.4, 4.95, 12.5, 1.3, border=GOLD, size=15)

# ── Slide 8: Literature Survey – Foundations ─────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "LITERATURE SURVEY")
slide_title(sl, "Foundations: Core Algorithms")
headers = ["Paper / Authors", "Key Contribution", "How Dynaswarm Uses It"]
rows = [
    ["Dorigo, Maniezzo & Colorni (1996)\nAnt System",
     "Original ACO: pheromone-based collective memory for combinatorial optimisation",
     "Base for MAX-MIN ACO; pheromone trail ∝ τᵅ·ηᵝ"],
    ["Kennedy & Eberhart (1995)\nParticle Swarm Optimization",
     "Velocity/position updates in continuous space via cognitive + social forces",
     "Priority-vector adaptation for discrete routing on graphs"],
    ["Stützle & Hoos (2000)\nMAX-MIN Ant System",
     "Trail clamping to [τ_min, τ_max]; reinforces only best solution; prevents premature convergence",
     "Directly implemented; bounds cap trail ratio at 2n, keeping controller meaningful"],
]
table_slide_data(sl, headers, rows, 0.4, 1.55, 12.5, 5.0)

# ── Slide 9: Literature Survey – Adaptation ───────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "LITERATURE SURVEY")
slide_title(sl, "Adaptation in Dynamic Environments")
headers = ["Paper / Authors", "Key Contribution", "How Dynaswarm Uses It"]
rows = [
    ["Mavrovouniotis & Yang (2013)\nAdapting Evaporation Rate",
     "λ-branching factor as stagnation signal; ±σ parameter increments",
     "Adopted both: λ-branch signal + incremental step size σ=0.001"],
    ["Stützle et al.\nParameter Adaptation in ACO",
     "No clear benefit in varying parameters at runtime vs a well-tuned fixed setting",
     "This IS the null hypothesis Dynaswarm rigorously tests and reproduces"],
    ["Various (2015–2023)\nHybrid Swarm Algorithms",
     "ACO+PSO combination for static graphs; budget splitting strategies",
     "Motivates our time-varying recency-driven budget split mechanism (E4)"],
]
table_slide_data(sl, headers, rows, 0.4, 1.55, 12.5, 5.0)

# ── Slide 10: Gap Identified ──────────────────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "LITERATURE SURVEY")
slide_title(sl, "What the Literature Leaves Unanswered")
items = [
    ("📊  Testbed bias", "Most adaptation studies use small graphs (n≤30) where pheromone is irrelevant. Null results follow from testbed choice, not mechanism failure.", GOLD),
    ("🔗  Budget allocation", "Compute split between exploration and exploitation components has never been studied as a sensing-driven control variable.", ACCENT),
    ("🔬  Statistical rigour", "No prior work jointly controls signal choice, controller design, AND uses paired trials + Holm correction + effect sizes.", GREEN),
]
cy = 1.6
for icon_label, body, colour in items:
    txb(sl, icon_label, 0.4, cy, 3.5, 0.4, size=16, bold=True, colour=colour)
    txb(sl, body, 0.4, cy + 0.4, 12.2, 0.6, size=14, colour=WHITE)
    cy += 1.3
callout(sl, "Dynaswarm closes all three gaps in a single reproducible harness.",
        0.4, 6.1, 12.5, 0.65, border=ACCENT, size=15)

# ── Slide 11: Objectives ──────────────────────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "OBJECTIVES")
slide_title(sl, "Research Objectives")
objs = [
    ("1.", "Implement a fair, reproducible multi-arm harness with equal evaluation budgets"),
    ("2.", "Build and validate A*, MAX-MIN ACO, Priority-Vector PSO, and Hybrid ACO-PSO"),
    ("3.", "Design four volatility sensing signals with measurable, verifiable dynamic ranges"),
    ("4.", "Build an incremental adaptive controller driven by signal pressure vs running baseline"),
    ("5.", "Test the allocation thesis: does recency-driven budget shifting improve post-disruption recovery?"),
    ("6.", "Produce statistically valid conclusions: paired Wilcoxon, Holm correction, Cliff's δ"),
]
cy = 1.6
for num, text in objs:
    txb(sl, num, 0.4, cy, 0.55, 0.45, size=20, bold=True, colour=ACCENT)
    txb(sl, text, 1.0, cy, 11.8, 0.45, size=15, colour=WHITE)
    cy += 0.72

prs.save("/tmp/dynaswarm_ppt_p1.prs")
print("Part 1 saved — 11 slides")
