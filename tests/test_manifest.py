"""The frozen manifest (segment 23).

The manifest's whole job is to let a stranger reproduce both runs. So
these tests are about completeness and about the one property that
matters most: **a document that reads like a specification but does not
pin what it claims to** is the failure mode of this segment.
"""

from __future__ import annotations

import pytest
from scripts import manifest as m

#: Everything a rerun needs. A field missing from here is a field nobody
#: notices is missing until the rerun does not match.
REQUIRED_TOP = {"arms", "seeds", "scenarios", "budget_evaluations",
                "run_class", "provenance", "runs", "primary_tier"}
REQUIRED_PROVENANCE = {"commit", "branch", "dirty", "python", "platform",
                       "numpy", "parallel_jobs"}
REQUIRED_INSTANCE = {"seed", "n_nodes", "n_edges", "density", "optimum_t0",
                     "route_hops", "bridges", "bridge_hops", "bridge_share"}


@pytest.fixture(scope="module")
def small():
    """Three seeds, both tiers. Structure, not scale."""
    return m.build(("medium200", "large1000"), m.SEEDS[:3])


def test_the_manifest_carries_every_field_a_rerun_needs(small):
    """Fails if a field is dropped, which is how a manifest rots."""
    assert set(small) >= REQUIRED_TOP, f"missing: {REQUIRED_TOP - set(small)}"
    assert set(small["provenance"]) >= REQUIRED_PROVENANCE, (
        f"missing provenance: {REQUIRED_PROVENANCE - set(small['provenance'])}"
    )
    for tier, run in small["runs"].items():
        assert "graph" in run and "commands" in run, f"{tier} has no commands"
        assert len(run["commands"]) == len(small["scenarios"]), (
            f"{tier} lists {len(run['commands'])} commands for "
            f"{len(small['scenarios'])} scenarios"
        )
        assert run["instances"], f"{tier} recorded no instances"
        for inst in run["instances"]:
            assert set(inst) >= REQUIRED_INSTANCE, (
                f"{tier} seed {inst.get('seed')} missing: "
                f"{REQUIRED_INSTANCE - set(inst)}"
            )


def test_the_seeds_are_listed_not_described(small):
    """A range is a rule someone can mis-apply; a list is a fact.

    Asserted on the type, because "seeds 1000-1099" in a string field
    would satisfy a test that only checked the key was present.
    """
    assert isinstance(small["seeds"], list)
    assert all(isinstance(s, int) for s in small["seeds"])
    assert len(set(small["seeds"])) == len(small["seeds"]), "a seed is repeated"


def test_every_seed_is_characterised_with_no_silent_gaps(small):
    """An instance property nobody recorded is gone once the run is done.

    The count must match the seed list exactly — a characterisation that
    silently skips an unreachable or awkward instance leaves a hole the
    analysis cannot see.
    """
    for tier, run in small["runs"].items():
        recorded = [i["seed"] for i in run["instances"]]
        assert recorded == small["seeds"], (
            f"{tier}: characterised {recorded} against seeds {small['seeds']}"
        )
        for inst in run["instances"]:
            assert inst["n_edges"] > 0, f"{tier} seed {inst['seed']} has no edges"
            assert 0.0 <= inst["bridge_share"] <= 1.0, (
                f"{tier} seed {inst['seed']} bridge share {inst['bridge_share']} "
                f"is not a fraction"
            )
            if inst["bridge_hops"] > 0:
                assert inst["bridges"] > 0, (
                    "a route uses a bridging edge on an instance recorded as "
                    "having none"
                )


def test_bridge_share_is_measured_on_the_world_that_was_built():
    """**The bug this test exists for**, found in segment 23.

    `characterise` replays the model call to recover which edges
    `_ensure_connected` invented. Written first with a *fresh* stream for
    the bridging call, which looks equivalent and is not: the bridging
    step consumes draws the model call has already taken, so a fresh
    stream picks **different bridge endpoints**.

    The bridge *count* is unaffected — the same components need the same
    number of bridges — so every summary looked right except the one that
    mattered. It reported bridge share as 0.0000 on all 100 seeds,
    including two measured at ~45% in segment Z3, and would have frozen
    that zero into the manifest.

    Seeds 9999 and 555 are the check: both have a bridge carrying a large
    share of the optimal route, and both read 0.0 under the bug.
    """
    for seed, expected in ((9999, 0.45), (555, 0.42)):
        inst = m.characterise("medium200", seed)
        assert inst.bridges > 0, f"seed {seed} no longer has a bridging edge"
        assert inst.bridge_share == pytest.approx(expected, abs=0.02), (
            f"seed {seed} reports bridge share {inst.bridge_share:.4f}, expected "
            f"~{expected}. If this reads 0.0, the replay stream has been "
            f"reset between the model call and the bridging call again"
        )


def test_the_dashboard_cannot_produce_a_manifest_run():
    """`manifest` is the evidence class and only the CLI may stamp it.

    Two independent guards, because either alone is one edit from being
    bypassed: the dashboard hardcodes `exploratory`, and it writes to a
    scratch root rather than the evidence tree.
    """
    server = pytest.importorskip("dashboard.server")

    cfg = server.race_config(server.RaceSpec(arms=["astar", "aco"]))
    assert cfg.run_class == "exploratory", (
        f"the dashboard builds runs stamped {cfg.run_class!r}; scratch work "
        f"can become evidence"
    )
    assert server.SCRATCH != server.OUTPUTS
    assert "outputs" not in str(server.SCRATCH.name)


def test_the_manifest_run_class_is_the_evidence_class(small):
    assert small["run_class"] == "manifest"


def test_the_arm_set_matches_what_the_harness_can_build(small):
    """Every named arm must exist, and every controlled arm must be present.

    Entry 024 froze the set. A manifest naming an arm the harness cannot
    build fails at trial one of a hundred; a manifest silently omitting
    one produces an analysis with a comparison missing.
    """
    from dynaswarm.harness.arm import ARM_BUILDERS

    unknown = set(small["arms"]) - set(ARM_BUILDERS)
    assert not unknown, f"manifest names arms the harness cannot build: {unknown}"

    missing = set(ARM_BUILDERS) - set(small["arms"])
    assert not missing, (
        f"the harness can build {missing} and the manifest does not run them. "
        f"Every arm exists to kill an objection; an omitted one is an "
        f"objection left alive"
    )


def test_every_preregistered_comparison_has_its_arms_in_the_manifest(small):
    """T3's first check, as a permanent test.

    The cheapest place to discover a planned comparison cannot be
    computed. Entry 024 plus both amendments name the family; if an arm
    it needs is not in the manifest, the run produces data that cannot
    answer the question it was run for.
    """
    from scripts.preregistration import PLANNED

    present = set(small["arms"])
    for plan in PLANNED:
        for arm in (plan.arm_a, plan.arm_b):
            assert arm in present, (
                f"{plan.key} ({plan.tests}) needs {arm}, which the manifest "
                f"does not run"
            )


def test_the_provenance_tells_the_truth_about_the_working_tree():
    """**A manifest that looks complete and pins nothing** — segment 23's mutation.

    Reporting `dirty` as `False` unconditionally passed the entire suite.
    The completeness test asserts the key is *present*; nothing asserted
    it was *true*. The manifest would then name a commit and declare the
    tree clean while uncommitted work was running, so a stranger checking
    out that commit gets different code — and every field around it still
    reads correct.

    Checked against `git` independently rather than against the value the
    manifest computed, because a field cannot verify itself.
    """
    import subprocess

    prov = m.provenance()
    actual = bool(
        subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=m.ROOT, capture_output=True, text=True, check=False,
        ).stdout.strip()
    )
    assert prov["dirty"] is actual, (
        f"the manifest reports dirty={prov['dirty']} and the tree is "
        f"dirty={actual}. A provenance field that does not match reality is "
        f"worse than an absent one — it is read as a guarantee"
    )
    assert prov["reproducible_from_commit"] is (not actual)
    assert bool(prov["warning"]) is actual, (
        "a dirty tree must say so in words, not only in a boolean a reader "
        "has to notice"
    )
    assert prov["commit"], "no commit hash recorded at all"


def test_the_four_scenarios_are_frozen_and_differ_only_in_event_rate(small):
    """Entry 030. Four scenarios, and only one thing varying between them.

    `calm` is the negative control and `light -> moderate -> severe` is
    the dose-response. Both claims depend on the scenarios being identical
    in every respect except disruption frequency — if `cluster_size` or
    `timesteps` also moved, a difference between scenarios would have two
    possible causes and the dose-response would mean nothing.
    """
    scenarios = small["scenarios"]
    assert set(scenarios) == {"calm", "light", "moderate", "severe"}

    rates = {n: s["events_per_step"] for n, s in scenarios.items()}
    assert rates == {"calm": 0.0, "light": 0.1, "moderate": 0.3, "severe": 0.8}
    assert rates["calm"] == 0.0, "the negative control has disruptions"
    assert rates["light"] < rates["moderate"] < rates["severe"], (
        "the dose-response ordering is not monotone in the event rate"
    )

    varying = {
        key
        for key in ("cluster_size", "timesteps")
        if len({s[key] for s in scenarios.values()}) > 1
    }
    assert not varying, (
        f"{varying} differs between scenarios, so a difference between them "
        f"has more than one possible cause"
    )


def test_the_calm_scenario_makes_the_sensing_arms_identical_to_their_twins():
    """**The negative control, asserted rather than assumed.**

    With no disruptions, recency never fires, so a recency-driven arm must
    not move — making it byte-identical to its frozen twin. Measured: at
    `calm` the adaptive hybrid takes **one** distinct split and adaptive
    rho takes **one** distinct value; at `moderate` they take 14 and 19.

    If this ever fails, a sensing arm is moving with nothing to sense,
    which means it is responding to something other than disruption and
    every positive result it produces is suspect.
    """
    from dynaswarm.harness.trial import run_trial

    arms = ["hybrid_fixed", "hybrid_adaptive", "aco_fixed", "aco_adaptive"]
    cfg = m.run_config("medium200", m.SEEDS, scenario="calm")
    cfg.scenario.timesteps = 20
    rows = list(run_trial(cfg, 0, arms).steps)

    assert sum(r.num_events for r in rows if r.arm == "hybrid_fixed") == 0, (
        "the calm scenario produced disruptions; it is not a negative control"
    )
    fractions = {dict(r.probe)["aco_fraction"] for r in rows
                 if r.arm == "hybrid_adaptive"}
    assert len(fractions) == 1, (
        f"the adaptive hybrid took {len(fractions)} splits with nothing to "
        f"sense: {sorted(fractions)}"
    )
    rho = {dict(r.params)["rho"] for r in rows if r.arm == "aco_adaptive"}
    assert len(rho) == 1, f"adaptive rho moved without disruptions: {sorted(rho)}"


def test_identical_arms_are_reported_not_dropped():
    """A degenerate comparison must shrink the Holm denominator, visibly.

    At `calm` the sensing arms are identical to their twins, so Wilcoxon
    has no differences to rank. That is the control **succeeding**, and it
    must be reported as such rather than silently skipped — a family that
    quietly shrinks is a correction applied to the wrong denominator, and
    a cell that vanishes looks like one that was never planned.
    """
    import numpy as np
    import pandas as pd
    from scripts.preregistration import run_preregistered

    rows = []
    for arm in ("hybrid_adaptive", "hybrid_fixed"):
        for trial in range(4):
            for t in range(12):
                rows.append({
                    "run_id": "x", "scenario": "calm", "signal_kind": "",
                    "controller_kind": "", "arm": arm, "trial": trial,
                    "timestep": t, "excess": 0.10, "num_events": 0,
                    "optimum": 1.0, "best_cost": 1.1, "path_valid": True,
                    "evaluations_spent": 60, "seed": 1000 + trial,
                    "run_class": "exploratory", "wall_ms": 1.0,
                })
    report = run_preregistered(pd.DataFrame(rows))

    keys = {d["key"] for d in report["degenerate"]}
    assert "P1" in keys, (
        f"identical arms were not reported as degenerate: {report['degenerate']}"
    )
    assert not any(r["key"] == "P1" for r in report["results"]), (
        "a comparison with nothing to rank produced a test result"
    )
    assert report["family_size"] < report["grid_size"], (
        "the Holm denominator still counts a cell that was never tested"
    )
    assert not np.isnan([r["p_value"] for r in report["results"]]).any()


def test_the_primary_tier_is_pre_registered_with_its_condition_and_fallback(small):
    """Entry 031. Which tier carries the claims, decided before the run.

    `large1000` is primary because it has zero bridging edges on every
    instance and is free of the confound affecting 40% of `medium200`.
    But that is **conditional**: a tier can only be primary if all four
    metrics are computable on it, and the binding one is
    `mean steps to recover`, which had never been measured at 1000 nodes.

    Recording the condition *and* the fallback now is what stops a switch
    of emphasis after the results are seen from looking like a choice.
    """
    primary = small["primary_tier"]
    assert primary["tier"] == "large1000"
    assert primary["fallback"] == "medium200"
    assert primary["tier"] != primary["fallback"]
    assert primary["condition"], "no condition recorded, so nothing is conditional"
    assert primary["why"], "no reason recorded"
    assert primary["measured_damaged_per_arm_trial"], (
        "the condition names a measurement that is not recorded beside it"
    )


def test_the_primary_tier_falls_back_when_recovery_cannot_be_supported():
    """The fallback must actually fire, and say why.

    A pre-registered fallback that cannot trigger is decoration. Driven
    through the real decision function with counts on both sides of the
    threshold.
    """
    ok = m.primary_tier_holds({
        ("large1000", "moderate"): m.MIN_DAMAGED_FOR_RECOVERY + 10,
        ("large1000", "severe"): m.MIN_DAMAGED_FOR_RECOVERY,
    })
    assert ok["primary"] == "large1000" and ok["condition_held"]

    short = m.primary_tier_holds({
        ("large1000", "moderate"): m.MIN_DAMAGED_FOR_RECOVERY + 10,
        ("large1000", "severe"): m.MIN_DAMAGED_FOR_RECOVERY - 1,
    })
    assert short["primary"] == "medium200"
    assert short["condition_held"] is False
    assert "large1000/severe" in short["short_cells"]
    assert "recovery metric" in short["reason"], (
        "the fallback fired without recording why, so it would read as an "
        "unexplained change of emphasis"
    )


def test_p5_completes_the_controlled_hybrid_set():
    """Entry 031. All six pairs among the four controlled hybrids.

    Exhaustive within the family means nothing is selected and nothing can
    be asked for that is not already there — the strongest answer to "why
    did you not also compare X against Y".
    """
    from itertools import combinations

    from scripts.preregistration import PLANNED

    controlled = {"hybrid_fixed", "hybrid_adaptive", "hybrid_scheduled",
                  "hybrid_direct"}
    planned_pairs = {
        frozenset((p.arm_a, p.arm_b))
        for p in PLANNED
        if {p.arm_a, p.arm_b} <= controlled
    }
    every_pair = {frozenset(c) for c in combinations(sorted(controlled), 2)}
    assert planned_pairs == every_pair, (
        f"missing pairs: {[sorted(p) for p in every_pair - planned_pairs]}"
    )
    assert any(p.key == "P5" for p in PLANNED)


def test_p5_is_live_in_the_calm_cell():
    """P5 asks a real question where the sensing arms have none.

    At `calm` the adaptive arm is identical to its frozen twin, so P1
    drops out. The scheduled arm still sweeps on its timetable, so P5 asks
    whether blind movement **costs** anything when there is nothing to
    respond to — which is exactly what a negative control should be able
    to answer.
    """
    from dynaswarm.harness.trial import run_trial

    arms = ["hybrid_fixed", "hybrid_scheduled", "hybrid_direct"]
    cfg = m.run_config("medium200", m.SEEDS, scenario="calm")
    cfg.scenario.timesteps = 20
    rows = list(run_trial(cfg, 0, arms).steps)

    def splits(arm):
        return {dict(r.probe)["aco_fraction"] for r in rows if r.arm == arm}

    assert len(splits("hybrid_fixed")) == 1, "the frozen arm moved at calm"
    assert len(splits("hybrid_scheduled")) > 1, (
        "the scheduled arm did not move at calm, so P5 has nothing to compare "
        "and the calm cell loses its only movement-versus-stillness test"
    )
    # And the direct arm settles ACO-heavy rather than staying at 0.5 —
    # with nothing invalidating the trails, buying ACO is the principled
    # response, and it makes P2/P3b/S1 live here too.
    assert max(splits("hybrid_direct")) > 0.5
