"""Structural guards.

These tests encode constraints that the previous codebase violated and
that no amount of review reliably catches by eye.  They are deliberately
blunt: each one fails the build rather than merely warning.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src" / "dynaswarm"

#: Only this module may construct a random generator.
RNG_OWNER = "core/rng.py"

#: Heavyweight UI stacks.  The previous codebase spent ~2,600 lines on a
#: Tkinter launcher, a FastAPI dashboard and a report generator, none of
#: which contributed to a single result.
FORBIDDEN_IMPORTS = {"tkinter", "fastapi", "uvicorn", "flask", "starlette"}

#: pygame is legitimate, but only for the replay viewer.
PYGAME_ALLOWED_UNDER = "viz"

#: Ceiling on non-test source.  The prior codebase reached 13,300 lines
#: while doing less science.
MAX_SRC_LINES = 3000


def _python_files() -> list[Path]:
    return sorted(SRC.rglob("*.py"))


def _rel(path: Path) -> str:
    return path.relative_to(SRC).as_posix()


@pytest.mark.parametrize("path", _python_files(), ids=_rel)
def test_no_global_rng(path: Path):
    """Randomness may only come from :mod:`dpo.core.rng`.

    Catches the failure where global seeding (``random.seed`` /
    ``np.random.seed``) let one component's draws perturb another's, so
    "same seed" did not imply "same event sequence".
    """
    if _rel(path) == RNG_OWNER:
        return

    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] != "random", (
                    f"{_rel(path)} imports `random`; use dpo.core.rng.stream()"
                )
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] != "random", (
                f"{_rel(path)} imports from `random`; use dpo.core.rng.stream()"
            )
        elif (
            # np.random.seed / np.random.default_rng / np.random.rand ...
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Attribute)
            and node.value.attr == "random"
            and isinstance(node.value.value, ast.Name)
            and node.value.value.id in {"np", "numpy"}
        ):
            pytest.fail(
                f"{_rel(path)} touches np.random.{node.attr}; use dpo.core.rng.stream()"
            )


@pytest.mark.parametrize("path", _python_files(), ids=_rel)
def test_no_forbidden_imports(path: Path):
    """No GUI or web frameworks outside the replay viewer."""
    tree = ast.parse(path.read_text(), filename=str(path))
    rel = _rel(path)

    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]

        for name in names:
            root = name.split(".")[0]
            assert root not in FORBIDDEN_IMPORTS, f"{rel} imports {root}"
            if root == "pygame":
                assert rel.startswith(f"{PYGAME_ALLOWED_UNDER}/"), (
                    f"{rel} imports pygame outside {PYGAME_ALLOWED_UNDER}/"
                )


def test_line_budget():
    """Total source stays under the ceiling.

    A crude proxy for scope discipline, but the failure it guards against
    was itself crude: the prior codebase grew to 13,300 lines while its
    central mechanism never ran.
    """
    total = sum(len(p.read_text().splitlines()) for p in _python_files())
    assert total < MAX_SRC_LINES, f"src/ is {total} lines, ceiling is {MAX_SRC_LINES}"
