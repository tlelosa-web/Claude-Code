# Spec — Test Sheet Fan Lines: table UI instead of per-fan panel

**Date:** 2026-07-15 | **Status:** Approved (Tebello, this session) | **Owner:** Tebello Lelosa

## Problem

`4_Scripts/frontend/src/App.jsx`'s "Test Sheet Fan Lines" section (added in
commit `e04c543`, 2026-06-08) renders each fan as a full duplicated form
panel: a bordered card titled "Fan N" with 10 `Field`s + 1 `Select`
(Motor Serial No., Blade Pitch Deg., Tacho/Clamp Serial, Speed r/min,
Current PH1-3, Voltage PH1-3, Connection), plus Duplicate/Remove buttons per
panel.

Tebello: this doesn't match what was imagined. The feature exists for orders
with multiple *identical* fans on one order — "Add Fan" was meant to add
**more lines to the test sheet**, not a second full form section per fan.

Confirmed via `4_Scripts/backend/pdf_generator.py` (lines 238-304): the
actual Test Record Sheet PDF already renders this as **one table**, shared
header row, one data row per fan (`test_line_row()`, `MAX_ROWS = 20`). The
backend payload shape (`TestLinePayload` in `main.py`) and PDF output are
already correct — only the frontend UI doesn't match.

## Decision

Replace the boxed per-fan panel UI with a compact table matching the PDF's
column layout. No backend or PDF changes — payload shape
(`test_lines: [{motor_serial_number, blade_pitch_deg, tacho_clamp_serial_no,
speed_actual, current_ph1-3, voltage_ph1-3, connection}]`) stays identical.

### Frontend (`App.jsx`)

- Replace the `.test-lines-panel` render block (current lines ~544-591)
  with a `<table className="test-lines-table">`:
  - `<thead>`: one `<th>` per column (Fan #, Motor Serial No., Blade Pitch
    Deg., Tacho/Clamp Serial, Speed r/min, Current PH1/PH2/PH3, Voltage
    PH1/PH2/PH3, Connection, and a trailing blank header for the remove
    action).
  - `<tbody>`: one `<tr>` per `testLines` entry. Each cell holds a bare
    `<input>` (or `<select>` for Connection) wired to `updateTestLine`,
    no per-field `<label>` since the column header already labels it.
  - Row-index cell shows `Fan {index + 1}` (plain text, not editable).
  - Last cell: a small "×" / "Remove" button calling `removeTestLine(index)`,
    disabled when `testLines.length === 1` (unchanged behavior).
  - "Add Fan" button stays in the section header, calls `addTestLine()`,
    disabled at `MAX_TEST_LINES` (unchanged).
- Remove `duplicateTestLine` (handler + its two call sites) — not part of
  the "add more lines" intent, and dead weight once the "Duplicate" button
  is gone from the per-row UI. `MAX_TEST_LINES` and `addTestLine`/
  `removeTestLine`/`updateTestLine` logic is otherwise unchanged.
- No change to `buildTestLinesPayload`, `createTestLine`, or any
  backend-facing code — the row objects have the same shape as before.

### Styling (`App.css`)

- Replace `.test-lines-panel` / `.test-line` / `.test-line-title` /
  `.test-line-actions` / `.test-line-grid` (current lines 262-315) with
  table styles: `.test-lines-table` (full width, border-collapse), compact
  `th`/`td` padding, small text-only inputs inside cells (no field
  container/label chrome), and horizontal scroll (`overflow-x: auto` on a
  wrapper) for narrow viewports instead of the old 1-column collapse at
  900px — a wide table doesn't collapse to one column sensibly.

## Out of scope

- No backend/`main.py`/`pdf_generator.py` changes — payload contract is
  unchanged and already correct.
- No automated test coverage added (project has no test suite yet — see
  `docs/todo.md` § Next up).
- No change to `MAX_TEST_LINES` cap (20) or the fallback-from-`formData`
  behavior in `buildTestLinesPayload`.

## Acceptance

- "Add Fan" appends one row to a visible table (not a new boxed panel).
- Each row has inline editable cells for all 10 fields + connection select.
- Removing a row works; the last remaining row cannot be removed.
- Generating a Test Sheet PDF with 2+ fan rows still produces one row per
  fan in the PDF output, unchanged from current behavior.
