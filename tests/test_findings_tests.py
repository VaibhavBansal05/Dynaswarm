"""`FINDINGS_TESTS.md` is the reference the report is written from.

It is the only document anyone will consult, so the properties that make
it trustworthy are worth a test rather than a convention. A convention
lasts exactly as long as the person who remembers it.
"""

from __future__ import annotations

import re
from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "FINDINGS_TESTS.md"

#: Sections committed to in writing before the run existed — Entry 024's
#: family plus the two analyses Entries 024 and 029 promised. **Anything
#: not on this list was chosen after seeing the result.**
PRE_REGISTERED = {
    "4",   # the pre-registered comparisons
    "5",   # the upper bound on every null   (Entry 024)
    "6",   # conditioning on bridge share    (Entry 029)
}

#: Results sections chosen after the outcome was known.
EXPLORATORY = {"7", "8", "9"}


def _sections() -> dict[str, tuple[str, str]]:
    """`{number: (title, tag)}` for every numbered top-level section."""
    out = {}
    for line in DOC.read_text().splitlines():
        m = re.match(r"^## (\d+)\.\s+(.*)$", line)
        if m:
            number, rest = m.group(1), m.group(2)
            tag = ""
            if "`PRE-REGISTERED`" in rest:
                tag = "PRE-REGISTERED"
            elif "`EXPLORATORY`" in rest:
                tag = "EXPLORATORY"
            out[number] = (rest, tag)
    return out


def test_every_exploratory_section_says_so():
    """**The mutation this exists for**, segment 25.

    Removing the `EXPLORATORY` tag from §7 passed the entire suite,
    because nothing read this file. §7 is the worst one to mislabel: it
    is the section explaining *why* the null happened, and presented as
    pre-registered it reads as though the null had been predicted rather
    than discovered.

    The whole value of the pre-registered half is that a reader can tell
    which half they are looking at.
    """
    sections = _sections()
    for number in sorted(EXPLORATORY):
        assert number in sections, f"§{number} has gone missing from the document"
        title, tag = sections[number]
        assert tag == "EXPLORATORY", (
            f"§{number} ({title[:40]}) is tagged {tag or 'NOTHING'}. It was "
            f"chosen after seeing the result and must say so in its heading"
        )


def test_only_the_promised_analyses_are_tagged_pre_registered():
    """A section cannot become pre-registered by being labelled one.

    The list is fixed by `WORKFLOW_LOG.md` Entries 024 and 029. If a new
    section claims the tag, either the entry exists and this list is
    stale, or the claim is false — and the second is the one that
    matters.
    """
    sections = _sections()
    claimed = {n for n, (_, tag) in sections.items() if tag == "PRE-REGISTERED"}
    assert claimed == PRE_REGISTERED, (
        f"sections claiming PRE-REGISTERED are {sorted(claimed)}, expected "
        f"{sorted(PRE_REGISTERED)}. Adding one requires a log entry that "
        f"predates the run"
    )


def test_no_result_carries_an_unverified_provenance_tag():
    """Every number should be re-derived from the rows, or say why not.

    `[analysis.txt]` means carried from a derived summary without being
    checked against the data. By the end of segment 25 nothing should
    still be in that state unless the document explains the exception.
    """
    # A real provenance tag stands as its own line at the end of a
    # section. The legend and the closing summary both mention the tag
    # inside a sentence, and matching those was the first version of this
    # test failing on a clean document — the check has to distinguish a
    # tag from a word.
    lines = [ln.strip() for ln in DOC.read_text().splitlines()]
    tags = [ln for ln in lines if ln.startswith("**`[") and ln.endswith("**")]
    assert tags, "no provenance tags at all"

    stray = [ln for ln in tags if "[analysis.txt]" in ln]
    assert not stray, (
        f"{len(stray)} section(s) still carry an unverified provenance tag: "
        f"{stray}"
    )
    assert sum("[raw]" in ln for ln in tags) >= 10, (
        f"only {sum('[raw]' in ln for ln in tags)} sections are marked as "
        f"re-derived from the rows"
    )


def test_the_document_states_its_scales():
    """A reader must never need a second document to size a number.

    An effect of 0.100 is meaningless without knowing 0.147 is the
    negligible boundary, and a report quoting it without that context
    invites exactly the wrong reading.
    """
    text = DOC.read_text()
    for needed in ("negligible", "0.147", "percentage points", "p_adj"):
        assert needed in text, f"the scale legend no longer explains {needed!r}"
