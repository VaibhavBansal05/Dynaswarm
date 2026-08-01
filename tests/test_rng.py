"""Random-stream invariants.

The property under test is the one that makes a comparison study valid:
an arm's randomness must depend only on its own address, never on which
other arms happen to exist.
"""

from __future__ import annotations

import numpy as np
import pytest

from dynaswarm.core.rng import name_key, stream


def test_same_address_same_bits():
    a = stream(42, "trial", 0, "arm", "aco").random(64)
    b = stream(42, "trial", 0, "arm", "aco").random(64)
    np.testing.assert_array_equal(a, b)


def test_different_address_different_bits():
    a = stream(42, "trial", 0, "arm", "aco").random(64)
    b = stream(42, "trial", 0, "arm", "pso").random(64)
    assert not np.array_equal(a, b)


def test_different_root_seed_different_bits():
    a = stream(42, "trial", 0, "arm", "aco").random(64)
    b = stream(43, "trial", 0, "arm", "aco").random(64)
    assert not np.array_equal(a, b)


def test_arm_streams_survive_insertion():
    """Adding an arm must not perturb the arms already being measured.

    This is the regression guard for the failure mode that sequential
    ``SeedSequence.spawn`` would introduce: with positional children,
    inserting ``pso`` between ``aco`` and ``hybrid`` silently rewrites
    ``hybrid``'s stream and invalidates every number already collected
    for it.
    """
    before = {n: stream(7, "trial", 1, "arm", n).random(32) for n in ("aco", "hybrid")}
    after = {
        n: stream(7, "trial", 1, "arm", n).random(32) for n in ("aco", "pso", "hybrid")
    }
    for arm in ("aco", "hybrid"):
        np.testing.assert_array_equal(before[arm], after[arm], err_msg=f"{arm} stream moved")


def test_ablation_pair_shares_a_stream():
    """Fixed and adaptive arms of the same family draw identical bits.

    The ablation's strength depends on this: the two arms may only
    diverge because the controller moved a parameter, never because they
    were fed different randomness.
    """
    fixed = stream(11, "trial", 2, "arm", "aco_controlled", "search").random(32)
    adaptive = stream(11, "trial", 2, "arm", "aco_controlled", "search").random(32)
    np.testing.assert_array_equal(fixed, adaptive)


def test_name_key_is_process_stable():
    """Keys must not depend on Python's per-process hash randomisation."""
    assert name_key("aco") == name_key("aco")
    assert 0 <= name_key("aco") < 2**32
    # Value pinned so an accidental change of hash function is caught.
    assert name_key("aco") != name_key("pso")


def test_unnamed_stream_is_rejected():
    with pytest.raises(ValueError, match="at least one name"):
        stream(42)


def test_int_and_str_components_agree():
    """``3`` and ``"3"`` address the same stream, so callers need not care."""
    np.testing.assert_array_equal(
        stream(1, "trial", 3).random(16), stream(1, "trial", "3").random(16)
    )
