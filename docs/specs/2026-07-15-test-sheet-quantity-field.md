# Spec — Replace Test Sheet Fan Lines UI with a single Quantity field

**Date:** 2026-07-15 | **Status:** Implemented (Tebello, this session) | **Owner:** Tebello Lelosa

## Problem

`docs/specs/2026-07-15-test-sheet-fan-lines-table.md` replaced the per-fan
boxed panel with a per-fan *table* — still exposing individual editable rows
to the user. Tebello's actual intent was different: no per-fan UI at all.
For an order with N identical fans, the operator should only enter a single
**Quantity**, and the test sheet should get N identical rows automatically —
"the Test Sheet Fan Lines happens unseen."

## Decision

Remove the Fan Lines UI entirely (state, handlers, table markup, styles).
Add a **Quantity** field next to **Date of Manufacture** on the main form.
The row-per-fan expansion moves server-side: the frontend sends `quantity`,
the backend builds `quantity` identical rows from the same order-level
values already being used for the nameplate, and `pdf_generator.py`'s
existing row renderer (unchanged) draws them exactly as before.

**Motor Serial No. / Tacho Serial across rows** — Tebello: same value
repeated on every row, not left blank. Since no per-fan input exists to
source that from, it's sourced from the existing Excel-driven fallback
(`derived_fallback["motor_serial_number"]`, populated from
`test_sheet.get("motor_serial_number")` in
`api_test_record_sheet_from_nameplate`) — which already existed but was
silently dropped due to a bug in `_normalise_test_lines` (see below).

### Frontend (`App.jsx`, `FormFields.jsx`, `App.css`)

- Removed: `testLines` state, `createTestLine`, `MAX_TEST_LINES`,
  `updateTestLine`/`addTestLine`/`removeTestLine`, `buildTestLinesPayload`,
  the `.test-lines-panel`/`.test-sheet-column` table JSX and its CSS.
- Added: `quantity` to `formData` (default `"1"`), included in
  `buildRequestPayload()` as a coerced integer, included in
  `getPreviewDataKey()` and the preview-refresh effect's dependency array
  (so changing quantity re-triggers the live preview).
- `FormFields.jsx`: new `Field label="Quantity" type="number"` immediately
  after "Date of Manufacture".
- `validateForm`: quantity must be 1-20 (test sheet capacity), replacing the
  old `testLines.length > MAX_TEST_LINES` check.

### Backend (`main.py`)

- `NameplatePayload`: removed `test_lines: list[TestLinePayload]`, added
  `quantity: int = 1`.
- `_normalise_test_lines`: fixed a pre-existing bug where the `fallback`
  dict's `motor_serial_number`/`current_ph1`/`current_ph2`/`current_ph3`
  entries were built by both call sites but never actually read — added the
  `or _clean(fallback.get(...))` fallback for all four, matching the
  pattern already used for `blade_pitch_deg`/`speed_actual`/`voltage_ph*`/
  `connection`. This also improves the untouched, unused
  `/api/reports/test-record-sheet` endpoint (`TestRecordSheetPayload`) for
  free, harmlessly.
- `api_test_record_sheet_from_nameplate`: replaced the
  `len(payload.test_lines) > 20` check with a `quantity` bound (clamped to
  ≥1, rejected >20 with the same error message), and replaced
  `_normalise_test_lines(payload.test_lines, derived_fallback)` with
  `_normalise_test_lines([TestLinePayload() for _ in range(quantity)],
  derived_fallback)` — `quantity` blank lines, each filled entirely from the
  fallback dict.
- `pdf_generator.py`: **no changes** — `test_line_row()` already renders
  whatever normalized dicts it's given.
- `TestRecordSheetPayload`/`api_test_record_sheet` (the standalone endpoint,
  confirmed unused by the frontend or any test script via grep): left
  untouched, out of scope.

## Verification

- `POST /api/reports/test-record-sheet/from-nameplate` with `quantity: 3`
  → PDF has 3 identical rows (verified via `pypdf` text extraction).
- `quantity: 25` → `400 {"error": "A single test sheet can hold up to 20
  fan lines."}`.
- Live dev server: "Quantity" field renders next to "Date of Manufacture",
  no "Test Sheet Fan Lines" section remains, no console errors, `eslint`
  shows no new issues (only the pre-existing unrelated `loadFromExcel`
  unused-var error).

## Out of scope

- No change to `MAX_ROWS = 20` cap in `pdf_generator.py`.
- No new field for Motor Serial No. — reuses the existing Excel-sourced
  fallback rather than adding UI Tebello didn't ask for.
- No automated test coverage added (still tracked in `docs/todo.md`).
