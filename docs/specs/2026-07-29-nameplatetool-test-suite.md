# Spec — NamePlateTool: add a real automated test suite

**Machine:** Operations only.
**Todo item:** `docs/todo.md` "NamePlateTool: add a real automated test
suite"
**Size:** medium — not urgent, but scoped here so a session can start
without a separate planning pass.

## Goal

`tests/` currently holds only ad-hoc manual-check scripts
(`autofill_tests.py`, `check_api.py`, `check_connection.py`,
`inspect_excel.py`, `test_read_excel.py`, `test_api_fixes.py`) — no real
pytest/vitest suite. Every non-trivial backend change is currently
verified by hand against a generated PDF.

## Suggested scope (confirm with Tebello before building — this is a
starter scope, not a locked spec)

- **Backend (pytest):** convert the existing ad-hoc scripts into real
  pytest cases where they already exercise something meaningful (Excel
  import, PDF generation from a known payload). Cover the
  `TestLinePayload` contract specifically, since it's the documented
  cross-file gotcha (`App.jsx` ↔ `main.py` ↔ `pdf_generator.py`) — a test
  that asserts the payload shape stays in sync would catch the exact class
  of silent breakage already documented in `knowledge/nameplatetool.md`.
- **Frontend (vitest):** at minimum, smoke-test that `App.jsx` builds a
  `TestLinePayload`-shaped object matching the backend's pydantic model.
- Do not attempt full PDF-pixel-diff testing — out of scope; structural/
  payload-contract coverage is the actual gap.

## Definition of done

- A runnable `pytest`/`vitest` command exists and passes; at minimum the
  Excel-import path and the `TestLinePayload` contract have real test
  coverage, not just ad-hoc scripts.

## Hub bookkeeping (after landing)

- Pull `origin/main` on this hub repo first (Hard Rule 6).
- Update `knowledge/nameplatetool.md`'s "Testing status" entry.
- Remove this item from `docs/todo.md`, renumber remaining items, add a
  `docs/session-log.md` entry.
