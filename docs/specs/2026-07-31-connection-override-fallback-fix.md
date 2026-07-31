# Spec: Fix silent connection-override block in api_generate_pdf()

**Date:** 2026-07-31 | **Source bug report:** `docs/bugs/connection-lookup-no-manual-override.md`
**Source todo item:** `docs/todo.md` § Next up, item 1 (fix plan step 1 only — this task)

## Problem

`4_Scripts/backend/main.py`'s `api_generate_pdf()` (lines 353-357) computes
`conn` only from `suggest_connection()`, with no fallback to
`payload.connection`. When `suggest_connection()` finds no STAR/DELTA rule
for the selected voltage/pole/kW combo (reachable via normal UI use, since
Motor kW options aren't filtered by voltage), Save Nameplate fails even
after the user manually picks a connection — their choice is discarded.

## Fix (scope of this task)

Mirror the existing fallback pattern already used by the sibling endpoint
`api_test_record_sheet_from_nameplate()` (lines 479-485):

```python
if not conn:
    conn = _clean(payload.connection) or _clean(test_sheet.get("connection"))
```

Adapted for `api_generate_pdf()`'s scope (no `test_sheet` dict there — just
`payload`):

```python
if c in ("STAR", "DELTA"):
    conn = c
if not conn:
    conn = _clean(payload.connection)
```

Only `main.py` changes. No payload-shape change (still populates the same
`conn` variable used downstream), so the frontend/PDF-generator contract
(CLAUDE.md hard rule 1) is untouched — confirmed no `App.jsx` or
`pdf_generator.py` change needed.

## Out of scope (separate todo items, not this task)

- Optional UX filter of `motors_by_pole` by voltage (todo.md fix-plan step 2)
- `excel_source.py` datetime-serialization fix (todo.md fix-plan step 3)
- Orphaned endpoint decision, cosmetic PDF overflow guard

## Verification

Re-run the bug report's failing case:
`POST /api/generate-pdf` with `{motor: "5.5", pole: "4", voltage: "525",
connection: "DELTA", ...}` → expect `200 OK` with `connection=DELTA` honored
(was `400`). Verify against a live `uvicorn` server, not just static
inspection, per this project's Testing Standards (no automated suite yet).
