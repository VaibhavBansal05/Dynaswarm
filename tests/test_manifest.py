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
REQUIRED_TOP = {"arms", "seeds", "scenario", "budget_evaluations",
                "run_class", "provenance", "runs"}
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
        assert "graph" in run and "command" in run, f"{tier} has no command"
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
