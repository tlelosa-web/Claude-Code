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

## Codex second opinion (advisory) — 2026-08-03

**Findings**

1. **Ambiguous ownership and execution context**
   The spec says "**Machine: Operations only**" and later "**Pull `origin/main` on this hub repo first**," but it does not define whether the tests are added in the NamePlateTool repo, the hub repo, or both. "Hub bookkeeping" implies there is a separate coordination repo, while the test suite belongs to the application repo. Acceptance criteria should name the exact repo paths and where commands must be run.

2. **"Convert the existing ad-hoc scripts" is underspecified**
   The scripts listed may depend on local files, live services, generated artifacts, or machine-specific paths. The spec does not say which scripts are meaningful, which should be deleted, which should remain as utilities, or what fixtures replace their current inputs. "Where they already exercise something meaningful" is subjective and hard to test.

3. **The `TestLinePayload` contract criterion is good but not yet concrete**
   The spec says to "assert the payload shape stays in sync" across `App.jsx`, `main.py`, and `pdf_generator.py`. That is the right risk, but it does not define the canonical contract source. Is the backend Pydantic model authoritative? Is the frontend expected to mirror field names only, types too, defaults too, optional/required status too? Without that, a test can pass while still missing the real incompatibility class.

4. **Frontend test may be brittle or impractical as written**
   "Smoke-test that `App.jsx` builds a `TestLinePayload`-shaped object" assumes payload construction is extractable from `App.jsx`. If it is embedded in component event handlers/state, testing it through the rendered component may be noisy, while testing it directly may require refactoring. The spec should explicitly allow extracting a pure helper such as `buildTestLinePayload()` and testing that.

5. **PDF generation coverage needs a sharper acceptance target**
   The scope mentions "PDF generation from a known payload," while the DoD only requires Excel import and `TestLinePayload` coverage. If PDF generation is in scope, define what is asserted: no exception, valid PDF bytes/header, page count, expected text, expected dimensions, or specific generated file metadata. Otherwise it risks becoming another weak smoke test.

6. **Missing environment/install criteria**
   "A runnable `pytest`/`vitest` command exists and passes" does not say whether dependencies must be added, whether commands run from repo root, whether CI scripts/package scripts should be updated, or whether tests must avoid network/local Excel/PDF app dependencies. This matters because the current gap is manual verification.

7. **No failure-mode coverage for fixture drift**
   The spec calls out "silent breakage," but does not require tests to fail loudly when sample Excel files, payload fixtures, or generated output assumptions change. A realistic suite should include checked-in minimal fixtures or fixture builders, not depend on whatever local/generated files happen to exist.

**Assumptions To Make Explicit**

- Backend Pydantic model is the source of truth for `TestLinePayload`.
- Tests must be deterministic and not require a running frontend/backend server unless explicitly marked integration.
- Excel import tests use committed fixtures with known expected parsed output.
- PDF tests validate structure/content only, not visual pixel equivalence.
- Existing ad-hoc scripts are either migrated, renamed, or left untouched with a documented reason.

**Acceptance Criteria Gaps**

Add concrete criteria like:

- `pytest` can be run from the backend/repo root and passes on a clean checkout.
- `vitest` can be run from the frontend/repo root and passes on a clean checkout.
- At least one Excel fixture asserts parsed rows/fields, not just "no crash."
- A `TestLinePayload` frontend fixture/object validates successfully against the backend Pydantic model, or both are compared against a shared schema.
- PDF generation test asserts valid PDF output from a known payload and at least one stable structural property.
- Tests do not require manual files outside the repo, live APIs, or generated PDFs from previous runs.

**Failure Modes Not Covered**

- Frontend and backend diverge on optional fields/defaults while field names still match.
- Type mismatches, especially strings vs numbers/booleans, pass through loose JS tests.
- Excel import works only for the current manually tested workbook shape.
- PDF generator accepts the payload but silently drops fields.
- Tests pass locally because of existing generated artifacts or machine-specific paths.
- Vitest cannot import payload-building code cleanly because it is buried inside `App.jsx`.
- Pydantic version differences affect validation behavior.

**Alternatives Worth Weighing**

1. **Backend-owned JSON Schema contract**
   Generate JSON Schema from the Pydantic `TestLinePayload` model and have frontend tests validate constructed payloads against that schema. This makes the backend model canonical and avoids hand-maintained duplicate expectations.

2. **Extract a shared payload builder on the frontend**
   Instead of testing `App.jsx` directly, extract payload construction into a small module and test that module. Then keep one lightweight component smoke test if needed. This is usually cleaner and less brittle.

3. **Start with backend-only contract tests plus fixture coverage**
   If vitest setup is currently absent or heavy, a first useful slice could be pytest coverage for Excel import, Pydantic validation, and PDF generation. Then add frontend contract tests once payload construction is extracted. This reduces initial setup risk, but it leaves the cross-file gotcha only partially covered.

Overall, the spec is directionally sound: it correctly avoids PDF pixel diffing and targets the documented payload-contract risk. The main weakness is that the success criteria are still too qualitative for someone to implement without making important testing architecture decisions implicitly.

_Advisory only — reviewer agent retains sole APPROVE/BLOCK authority._
