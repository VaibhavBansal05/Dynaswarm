"""Dynaswarm PPT Builder – Part 3: slides 23-32 (Results + Conclusion) then save final."""
exec(open('/home/vaibhav/ML_PROJECT/dynaswarm/make_ppt_p2.py').read())

# ── Slide 22b: One Real Trial, Watched ────────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "RESULTS")
slide_title(sl, "One Real Trial, Watched Frame by Frame")
add_image(sl, IMG_SIM, 0.4, 1.4, 12.5, 5.55)
txb(sl, "Same run the replay viewer (viz/replay.py) shows interactively — hybrid arm, geometric n=40, "
        "seed 4242. A spatial cluster of edge closures lands near the target; the moving optimum itself "
        "changes (150.6 → 84.2); the hybrid finds it again within a step.",
    0.4, 7.0, 12.5, 0.4, size=11, colour=LGREY, italic=True)

# ── Slide 23: Algorithm Performance ──────────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "RESULTS")
slide_title(sl, "Algorithm Performance: The Main Comparison")
add_image(sl, IMG_ARMS, 0.4, 1.5, 8.6, 4.3)
headers = ["Arm", "Stat.", "Low", "Mod.", "High"]
rows = [
    ["A*",     "0.0%",  "0.0%",  "0.0%",  "0.0%"],
    ["ACO",    "5.2%",  "7.0%",  "8.9%",  "10.5%"],
    ["PSO",    "9.1%",  "15.4%", "20.0%", "32.1%"],
    ["Hyb.",   "4.1%",  "5.5%",  "7.7%",  "8.1%"],
]
table_slide_data(sl, headers, rows, 9.15, 1.55, 3.75, 2.2)
bullet_block(sl, [
    "Hybrid beats both components",
    "in every scenario",
    "PSO degrades sharply (9→32%);",
    "ACO degrades more gently (5→10%)",
    "Hybrid stays flattest of the three",
], 9.15, 4.05, 3.75, 3.0, size=11.5, gap=0.34)
txb(sl, "Source: multirun/2026-08-13/10-47-40 — 4 arms × 4 scenarios × 30 trials, geometric n=200.",
    0.4, 6.05, 12.5, 0.4, size=11, colour=LGREY, italic=True)

# ── Slide 24: Hybrid vs ACO / PSO (Statistical) ──────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "RESULTS")
slide_title(sl, "Hybrid vs. ACO: Is the Advantage Real?")
add_image(sl, IMG_PAIR, 7.3, 1.35, 5.6, 5.25)
txb(sl, "Paired Wilcoxon, 30 trials, Holm-corrected across 4 scenarios", 0.4, 1.55, 6.7, 0.4,
    size=13, bold=True, colour=GOLD)
headers = ["Scenario", "Hybrid", "ACO", "p_holm", "Cliff's δ"]
rows = [
    ["Static",   "4.1%",  "5.2%",  "0.027", "−0.24 small"],
    ["Low",      "5.5%",  "7.0%",  "0.147", "−0.21 small (n.s.)"],
    ["Moderate", "7.7%",  "8.9%",  "0.177", "−0.12 negl. (n.s.)"],
    ["High",     "8.1%",  "10.5%", "0.036", "−0.24 small"],
]
table_slide_data(sl, headers, rows, 0.4, 2.0, 6.7, 3.0)
txb(sl, "Significant at Static and High; Low and Moderate trend the same way but don't clear\nthe Holm-corrected threshold at n=30. vs. PSO: significant at all four, p_holm<0.001, large effect.",
    0.4, 5.3, 6.7, 1.0, size=12, colour=WHITE)
txb(sl, "Source: same multirun as slide 23. compare_arms(hybrid, aco/pso, within=scenario).",
    0.4, 6.55, 12.5, 0.4, size=11, colour=LGREY, italic=True)

# ── Slide 24b: The Allocation Thesis (E4) ────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "RESULTS")
slide_title(sl, "The Allocation Thesis (E4): A Preliminary Read")
add_image(sl, IMG_ALLOC, 0.4, 1.5, 7.0, 5.3)
callout(sl,
    "This is the project's stated novelty: does shifting budget between ACO and PSO,\n"
    "driven by a recency signal, beat a frozen 50/50 split?\n\n"
    "Directionally yes — adaptive is lower in both scenarios tested — but neither\n"
    "crosses significance at n=30, and the hybrid vector used here is UNTUNED.\n\n"
    "Honest status: promising, not yet demonstrated. E2 (tune the hybrid) then a\n"
    "full 4-scenario E4 re-run is the direct next step — see Future Scope.",
    7.7, 1.6, 5.2, 4.6, border=GOLD, size=13)
txb(sl, "Source: multirun/2026-08-15/12-55-14 — hybrid_fixed vs hybrid_adaptive, signal=recency, "
        "targets=[aco_fraction], sigma=0.01, 30 trials, moderate+high, default (untuned) params.",
    0.4, 6.9, 12.5, 0.4, size=10.5, colour=LGREY, italic=True)

# ── Slide 25: ρ-Parameter Adaptation Ablation ────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "RESULTS")
slide_title(sl, "A Different Ablation: Adapting ρ Online")
txb(sl, "Not the allocation thesis above — this ablation adapts ACO's own evaporation rate (ρ)\n"
        "against a volatility signal, starting from a tuned baseline.",
    0.4, 1.5, 12.5, 0.6, size=12, colour=LGREY, italic=True)
headers = ["Scenario", "Δ (Adaptive − Fixed)", "p_holm", "Cliff's δ", "Verdict"]
rows = [
    ["Static",   "+0.017 (fixed better)", "0.003", "0.07 — negligible", "FIXED BETTER ⚠"],
    ["Low",      "−0.001",               "0.71",  "0.02 — negligible", "Not significant"],
    ["Moderate", "−0.001",               "0.94",  "0.01 — negligible", "Not significant"],
    ["High",     "−0.009",               "0.23",  "0.04 — negligible", "Not significant"],
]
table_slide_data(sl, headers, rows, 0.4, 2.25, 12.5, 3.5)
callout(sl,
    "The only statistically significant result FAVOURS the FROZEN arm (static scenario).\n"
    "No result favours the adaptive arm at ANY disruption level.  All effect sizes negligible.\n"
    "Consistent with Stützle et al.: a well-tuned fixed setting is a hard baseline to beat online.",
    0.4, 5.85, 12.5, 1.3, border=RED, size=13)

# ── Slide 26: Why Adaptation Doesn't Help ─────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "RESULTS")
slide_title(sl, "Why Adaptation Doesn't Help: Parameter Quality vs. Online Tuning")
headers = ["Intervention", "Mean Excess", "Gain"]
rows = [
    ["Hand-authored presets (original baseline)", "~3.6%",   "—"],
    ["Tuned fixed parameters (Optuna, 60 candidates)", "~0.06%",  "−3.54% ★"],
    ["Tuned + online adaptation",                "~0.056%", "−0.004%"],
]
table_slide_data(sl, headers, rows, 0.4, 1.55, 12.5, 2.5)
callout(sl,
    "97% of achievable gain comes from choosing good parameters.\n"
    "1% comes from adapting them online.\n\n"
    "Optimal parameters do NOT vary significantly with volatility level.\n"
    "Tuning for 'high' disruption and running on 'moderate' — no significant penalty (p=0.47).\n"
    "The controller has nothing to exploit because there is no regime-specific optimum at this scale.",
    0.4, 4.2, 12.5, 2.8, border=GOLD, size=14)

# ── Slide 27: Signal Behaviour ────────────────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "RESULTS")
slide_title(sl, "Signal Behaviour: Not All Signals Are Usable")
headers = ["Signal", "Static", "Low", "Moderate", "High", "Verdict"]
rows = [
    ["edge_ratio",   "0.000", "0.002", "0.007", "0.015", "⚠ Tiny on n=200"],
    ["volatility",   "0.000", "0.262", "0.561 → 1.0", "1.000", "⚠ SATURATES on n=200"],
    ["λ-branching",  "7.30",  "7.38",  "7.14",  "7.24",  "❌ Not volatility"],
    ["recency ★",    "0.000", "peaks & decays", "peaks & decays", "peaks & decays", "✅ Best for E4"],
]
table_slide_data(sl, headers, rows, 0.4, 1.55, 12.5, 3.6)
callout(sl,
    "Key finding: a signal's usability is a joint property of the signal AND the graph tier.\n"
    "Volatility perfectly separates scenarios at n=30 (86% of range).\n"
    "At n=200 it pins at 1.000 for λ≥0.3 — the controller cannot move.",
    0.4, 5.45, 12.5, 1.3, border=ACCENT, size=13)
txb(sl, "Source: tests/test_control.py — test_volatility_saturates_above_a_few_events_per_step, "
        "test_branching_does_not_proxy_for_volatility.",
    0.4, 6.9, 12.5, 0.4, size=10.5, colour=LGREY, italic=True)

# ── Slide 28: Testbed Matters ─────────────────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "RESULTS")
slide_title(sl, "Right Testbed: The Mechanism Must Do Measurable Work")
txb(sl, "What happens when pheromone is completely disabled (α = 0)?",
    0.4, 1.55, 12.5, 0.45, size=15, colour=LGREY)
headers = ["Graph Tier", "With Pheromone", "Without (α=0)", "Delta", "p-value"]
rows = [
    ["Erdős–Rényi n=30", "0.91%", "0.75%",   "−0.15%",  "0.910  (NOT significant)"],
    ["Geometric n=200 ★", "8.25%", "23.88%",  "+15.63%", "< 0.001  ✅ SIGNIFICANT"],
]
table_slide_data(sl, headers, rows, 0.4, 2.1, 12.5, 2.0)
callout(sl,
    "Pheromone does nothing at n=30 and almost everything at n=200.\n\n"
    "A null result on n=30 would mean nothing — the mechanism is simply irrelevant there.\n"
    "A 30-node graph of mean degree 18 puts the target one or two hops away; ants find it by luck.\n\n"
    "Testbed selection is a SCIENTIFIC decision, not a convenience decision.\n"
    "Two tests enforce this: the testbed that shows the effect must be used for the claim.",
    0.4, 4.3, 12.5, 2.5, border=ACCENT, size=14)
txb(sl, "Source: tests/test_testbed.py — test_pheromone_contributes_on_the_science_tier, "
        "test_the_demo_tier_is_too_easy_for_mechanism_claims.",
    0.4, 6.85, 12.5, 0.4, size=10.5, colour=LGREY, italic=True)

# ── Slide 29: Conclusion – What We Found ─────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "CONCLUSION")
slide_title(sl, "What We Found: Four Findings")
findings = [
    ("1", GREEN,  "✅  Hybrid architecture works.",
     "Hybrid beats ACO (significant at static & high, p_holm<0.04) and beats PSO everywhere\n(p_holm<0.001, large effect). Advantage widens as PSO degrades under disruption."),
    ("2", GOLD,   "✅  Parameter quality dominates.",
     "Tuning beats hand-authored presets by ~3.5 percentage points — the single largest lever\nin the system is simply choosing good parameters, not adapting them online."),
    ("3", RED,    "❌  ρ-adaptation does not help.",
     "Against a tuned opponent, no scenario favours online ρ-adaptation; static significantly\nfavours the frozen arm (p_holm=0.003). Consistent with Stützle et al.'s established finding."),
    ("4", ACCENT, "🔬  Allocation adaptation (E4) — preliminary, promising, unproven.",
     "Recency-driven aco_fraction beats a fixed 50/50 split directionally in both scenarios\ntested, but not significantly at n=30 with untuned params. The open question remains open."),
]
cy = 1.45
for num, col, title, body in findings:
    txb(sl, num, 0.4, cy, 0.5, 0.6, size=32, bold=True, colour=col)
    txb(sl, title, 1.0, cy, 11.5, 0.4, size=15, bold=True, colour=col)
    txb(sl, body, 1.0, cy+0.38, 11.5, 0.65, size=12, colour=WHITE)
    cy += 1.28

# ── Slide 30: Honest Framing ──────────────────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "CONCLUSION")
slide_title(sl, "The Honest Framing: A Publishable Negative Result")
callout(sl,
    '"We built a controlled harness for testing online parameter adaptation in dynamic path optimisation.\n'
    'Using it, we find that (a) parameter quality matters enormously — poorly chosen presets cost ~3.6%\n'
    'excess against a tuned baseline of ~0.06% — while (b) adapting an already-tuned parameter online\n'
    'is indistinguishable from noise at n=30.  A hybrid of the two metaheuristics beats either alone,\n'
    'and shifting its allocation by a recency signal shows a promising but not yet significant edge.\n\n'
    'We identify the harness design choices necessary to reach this conclusion, several of which\n'
    'INVERT the result when omitted."',
    0.4, 1.55, 12.5, 3.4, border=ACCENT, size=13)
txb(sl, "Design choices that invert the result if omitted:", 0.4, 4.9, 6.5, 0.4, size=13, bold=True, colour=GOLD)
bullet_block(sl, [
    "Pre-materialised timeline (ordering artefact gives wrong answer)",
    "Equal-work budget (population size gaming inflates adaptive arm)",
    "Paired-trial statistics (timestep independence inflates sample size 60×)",
    "Tuned opponent (comparing to defaults is not a fair test)",
], 0.4, 5.35, 6.5, 1.8, size=12)
txb(sl, "Target venues:", 7.2, 4.9, 5.5, 0.4, size=13, bold=True, colour=GOLD)
txb(sl, "GECCO · IEEE CEC\nPPSN / ANTS\nTransportation Research Part C",
    7.2, 5.35, 5.5, 1.2, size=14, colour=WHITE)

# ── Slide 31: Future Scope – Near Term ───────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
section_tag(sl, "FUTURE SCOPE")
slide_title(sl, "What Comes Next")
txb(sl, "Phase 1 — Immediate (before Round 2)", 0.4, 1.55, 12.5, 0.4, size=16, bold=True, colour=GOLD)
bullet_block(sl, [
    "Tune the hybrid (E2) — the E4 run above used default, untuned parameters",
    "Re-run E4 on the tuned hybrid, across all 4 scenarios, not just moderate/high",
    "Extend the main comparison (slide 23) to 1000+ node and grid tiers",
    "Bring trial counts to 30 uniformly and report confidence intervals, not just point estimates",
], 0.4, 2.0, 12.5, 1.8, size=13)
divider(sl, 3.95)
txb(sl, "Phase 2 — Short Term (3–6 months)", 0.4, 4.05, 12.5, 0.4, size=16, bold=True, colour=ACCENT)
bullet_block(sl, [
    "RL-based Decision Engine (PPO/SAC) via pluggable Controller Protocol",
    "Real-world graphs: Sioux Falls, Chicago Sketch, OpenStreetMap cities",
    "Multi-objective optimisation (NSGA-II, multiple pheromone matrices)",
    "PyPI packaging + Docker image for reproducible deployment",
], 0.4, 4.5, 12.5, 1.8, size=13)
txb(sl, "Phase 3–4 (6–24 months): Neural ACO/PSO · Edge deployment · V2X · Meta-learning (MAML)",
    0.4, 6.5, 12.5, 0.45, size=12, colour=LGREY, italic=True)

# ── Slide 32: Thank You ───────────────────────────────────────
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(sl)
add_image(sl, IMG_NET, 7.0, 0.5, 6.0, 6.8)
txb(sl, "Thank You", 0.4, 1.8, 6.3, 1.1, size=48, bold=True, colour=ACCENT)
txb(sl, "Questions?", 0.4, 2.95, 6.3, 0.7, size=28, colour=WHITE)
divider(sl, 3.85, w_in=6.0)
txb(sl, "GitHub Repository", 0.4, 4.0, 3.5, 0.38, size=13, bold=True, colour=GOLD)
txb(sl, "github.com/VaibhavBansal05/Dynaswarm", 0.4, 4.38, 6.0, 0.38, size=12, colour=LGREY)
txb(sl, "Documentation", 0.4, 4.85, 3.5, 0.38, size=13, bold=True, colour=GOLD)
txb(sl, "DOCUMENTATION.md  ·  dynaswarm_algorithms.pdf", 0.4, 5.23, 6.0, 0.38, size=12, colour=LGREY)
txb(sl, "Test Suite", 0.4, 5.7, 3.5, 0.38, size=13, bold=True, colour=GOLD)
txb(sl, "271 pytest tests · 60s runtime · fully reproducible", 0.4, 6.08, 6.0, 0.38, size=12, colour=LGREY)

# ── Save final ────────────────────────────────────────────────
OUT = "/home/vaibhav/ML_PROJECT/dynaswarm/dynaswarm_presentation.pptx"
prs.save(OUT)
print(f"✅  Saved {len(prs.slides)} slides → {OUT}")
