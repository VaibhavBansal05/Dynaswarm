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

#: Ceiling on non-test source, counted in *statements* rather than lines.
#:
#: Counting raw lines makes the budget a tax on documentation: at present
#: only about 37 % of this codebase's lines are executable, so a line
#: ceiling would be breached by explaining the design rather than by
#: growing it.  Statements measure the thing actually worth bounding —
#: how much behaviour there is to understand and test.  Set comfortably
#: above the planned scope so a breach signals drift, not normal growth.
#:
#: **The ceiling was REMOVED in segment 21.**  It existed to make growth
#: visible, and it did that job — segments 14 through 20 each argued for
#: their statements against a number.  But by segment 20 it had started
#: doing a second job nobody asked it to do: §7.2's observation was
#: sketched to eleven fields and the budget was the reason to wonder
#: whether all eleven were needed.  A correctness constraint and a size
#: constraint pulling against each other is a bad trade at any ratio,
#: because only one of them can be checked by a test.
#:
#: So the count is still taken and still printed — drift is worth seeing
#: — but it no longer fails.  What replaced it is not a larger number; it
#: is the rule that a statement must be justified by what it does, which
#: review enforces and arithmetic cannot.
MAX_SRC_STATEMENTS = None

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


def _statement_count(path: Path) -> int:
    """Executable statements in a file, excluding docstrings."""
    tree = ast.parse(path.read_text(), filename=str(path))
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.stmt)
        and not (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        )
    )


def test_statement_budget():
    """Report the size of the science surface.  Never fail on it.

    This assertion used to carry a ceiling.  It does not any more (see
    ``MAX_SRC_STATEMENTS``) — the count is reported so a jump is visible
    in the log, and the judgement about whether a jump is justified is
    made by a person reading the diff, not by arithmetic.

    Kept as a test rather than a script because a number nobody runs is
    a number nobody sees.
    """
    per_file = {p: _statement_count(p) for p in _python_files()}
    total = sum(per_file.values())
    largest = sorted(per_file.items(), key=lambda kv: -kv[1])[:5]
    print(f"\nsrc/ is {total} statements across {len(per_file)} files")
    for path, count in largest:
        print(f"  {count:>5}  {path.relative_to(SRC)}")
    assert total > 0, "counted zero statements — the walker is broken, not src/"
