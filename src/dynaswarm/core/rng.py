"""Content-addressed random streams.

This is the **only** module in the package permitted to construct a
:class:`numpy.random.Generator`.  Everything else receives one.  A test
(``test_no_global_rng``) walks the source tree and fails the build if any
other module imports :mod:`random`, calls ``np.random.seed``, or builds a
generator itself.

Why streams are addressed by *name* rather than spawned sequentially
--------------------------------------------------------------------
The obvious approach is ``SeedSequence(seed).spawn(n)`` and handing out
children in order.  That is quietly disastrous for a comparison study:
inserting a sixth arm shifts every subsequent child, so the five arms you
already measured silently draw different randomness and every previously
collected number becomes non-comparable.

Deriving each ``spawn_key`` from a hash of the stream's *name* removes
the ordering dependence entirely.  ``stream(42, "trial", 3, "arm",
"aco", "search")`` denotes the same bits regardless of which other
streams exist, so arms can be added, removed or reordered without
invalidating prior results.
"""

from __future__ import annotations

import hashlib

import numpy as np

__all__ = ["stream", "name_key"]


def name_key(name: str) -> int:
    """Map a stream-name component to a stable 32-bit key.

    ``hash()`` is unusable here: Python randomises string hashing per
    process, so the same name would select different bits on every run.
    blake2b is stable across processes, machines and Python versions.

    Args:
        name: One component of a stream address.

    Returns:
        A non-negative integer below ``2**32``.
    """
    digest = hashlib.blake2b(name.encode("utf-8"), digest_size=4).digest()
    return int.from_bytes(digest, "big")


def stream(root_seed: int, *names: str | int) -> np.random.Generator:
    """Return the generator addressed by ``(root_seed, *names)``.

    The mapping is deterministic and order-independent: the same address
    always yields the same bit stream, and unrelated addresses are
    statistically independent.

    Args:
        root_seed: Seed for the whole experiment.
        *names: Address components, e.g. ``("trial", 3, "arm", "aco")``.

    Returns:
        A fresh :class:`numpy.random.Generator`.

    Raises:
        ValueError: If no address components are supplied.  An unnamed
            stream would collide with every other unnamed stream, which
            is never what the caller wants.
    """
    if not names:
        raise ValueError("stream() requires at least one name component")
    spawn_key = tuple(name_key(str(part)) for part in names)
    return np.random.default_rng(np.random.SeedSequence(entropy=root_seed, spawn_key=spawn_key))
