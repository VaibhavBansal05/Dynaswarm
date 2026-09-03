"""The Dynaswarm dashboard — a view onto the engine, never a second engine.

This package sits at the repository root, **outside** ``src/``, and that
placement is the design (D14).  It imports ``dynaswarm`` as a library;
``dynaswarm`` never imports it.  A direction of dependency cannot be
violated by accident the way a naming convention can — the import simply
fails — so "view, never an engine" is structural here rather than
aspirational.

Two consequences worth knowing before adding anything:

* ``pyproject.toml`` packages only ``src``, so this directory is not
  installed with the library.  It is a repository tool, not a shipped
  component.
* ``test_hygiene``'s scans are rooted at ``src/dynaswarm``, so FastAPI is
  legal here and banned there.  That asymmetry is the whole point of
  keeping the dashboard out of the science surface, and it is verified in
  ``tests/test_dashboard.py`` rather than assumed.

The rule that governs every future segment: **the dashboard computes
nothing.**  Every number it shows is asked of the core.  Not "mostly",
not "except for display".  The repository has already died once of
instrumentation that looked fine and quietly disagreed with the engine.
"""
