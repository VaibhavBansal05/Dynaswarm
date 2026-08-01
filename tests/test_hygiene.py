"""Structural guards.

These tests encode constraints that code review does not reliably catch
by eye — an unused import, a stray global, a module that quietly doubles
in size.  They are deliberately blunt: each fails the build rather than
warning.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src" / "dynaswarm"

#: Only this module may construct a random generator.
RNG_OWNER = "core/rng.py"

#: Heavyweight UI stacks.  Interfaces are where research code grows
#: fastest and contributes least; keeping them out of ``src`` entirely is
#: easier than policing how much of one is justified.
FORBIDDEN_IMPORTS = {"tkinter", "fastapi", "uvicorn", "flask", "starlette"}

#: pygame is legitimate, but only for the replay viewer.
PYGAME_ALLOWED_UNDER = "viz"

#: Ceiling on non-test source.  Chosen to be comfortably above what the
#: planned scope needs, so breaching it signals scope drift rather than
#: normal growth.
MAX_SRC_LINES = 3000

#: Names under ``np.random`` that merely *refer to* a type rather than
#: producing randomness.  Annotating a parameter as
#: ``np.random.Generator`` is exactly the discipline this module is
#: enforcing, so banning it outright would punish the correct pattern.
RNG_TYPE_NAMES = {"Generator", "SeedSequence", "BitGenerator"}


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
                    f"{_rel(path)} imports `random`; use dynaswarm.core.rng.stream()"
                )
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] != "random", (
                f"{_rel(path)} imports from `random`; use dynaswarm.core.rng.stream()"
            )
        elif (
            # np.random.seed / np.random.default_rng / np.random.rand ...
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Attribute)
            and node.value.attr == "random"
            and isinstance(node.value.value, ast.Name)
            and node.value.value.id in {"np", "numpy"}
            and node.attr not in RNG_TYPE_NAMES
        ):
            pytest.fail(
                f"{_rel(path)} touches np.random.{node.attr}; "
                "use dynaswarm.core.rng.stream()"
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
    is itself crude: a codebase can grow large enough that nobody notices
    its central mechanism is not running.
    """
    total = sum(len(p.read_text().splitlines()) for p in _python_files())
    assert total < MAX_SRC_LINES, f"src/ is {total} lines, ceiling is {MAX_SRC_LINES}"
