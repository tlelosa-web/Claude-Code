# Spec — Fix `/api/nameplate/from-excel` datetime crash + dead `Table 1` sheet check

**Date:** 2026-07-28 | **Status:** Implemented (this session) | **Owner:** Tebello Lelosa

## Problem

`/api/nameplate/from-excel` crashes with `"Object of type datetime is not
JSON serializable"` against the real `NAME PLATE PROCEDURE.xlsx`.

Root cause, confirmed by loading the real workbook directly:

- `excel_source.read_nameplate_from_excel()` branches on sheet name: `"Table
  1"` (primary) → `"Info+Data Entry Form"` (fallback) → else `"Name Plate"`.
  The real workbook has no `"Table 1"` sheet, so it always falls into the
  `"Info+Data Entry Form"` branch.
- In that branch, `date_of_manuf = _find_labeled_value(ws, "Date")` returns
  the **raw cell value** — confirmed via direct read: `Info+Data Entry
  Form!C4` is `datetime.datetime(2026, 5, 6, 0, 0)`, not a string. This raw
  `datetime` flows straight into the dict returned to `main.py`, which wraps
  it in `JSONResponse(...)` — FastAPI/`json` can't serialize a `datetime`,
  hence the crash.
- The `else` branch (assumed `"Name Plate"` sheet) already does this
  correctly: `date_of_manuf = _fmt_month_year(_find_labeled_value(ws, "Date
  of Manuf"))`. The `"Info+Data Entry Form"` branch is simply missing the
  same formatting call.

Separately, the `"Table 1"` primary check is dead code — that sheet never
exists in the real workbook, so the branch is unreachable and misleading.

## Why the 2026-07-17 fix attempt regressed (do not repeat)

That attempt renamed the primary check from `"Table 1"` to `"NamePlateProc"`
on the theory that `NamePlateProc` was the "real" primary sheet. Verified by
direct inspection this session: `NamePlateProc` is a **static
instructions/reference sheet** — every "value" cell next to a label (e.g.
`Series` → `"As per Sales Order"`, `Motor` → `"As per Sales Order or
Supplier Order"`) is boilerplate procedure text, not per-job data. Routing
real reads through `NamePlateProc`'s label-reading logic is why every field
came back blank — there was no real data on that sheet to read in the first
place. `"Info+Data Entry Form"` is the actual per-job data-entry sheet and
must stay the effective primary source.

## Decision

1. **`excel_source.py`, `"Info+Data Entry Form"` branch:** wrap
   `date_of_manuf` in the same `_fmt_month_year()` call the `else` branch
   already uses, so a `datetime` cell is formatted to a JSON-safe string
   (`"MAY.2026"` style) before it ever reaches `main.py`'s `JSONResponse`.
2. **Remove the dead `"Table 1"` branch.** Since it never matches on the
   real workbook, drop the `if "Table 1" in wb.sheetnames:` condition and
   make `"Info+Data Entry Form"` the primary (first-checked) branch, with
   the `"Name Plate"` sheet as `else` fallback — same effective behavior as
   today (nothing changes at runtime, since `"Table 1"` was already
   unreachable), just without a misleading dead condition referencing a
   sheet name that doesn't exist in the real file.
3. **No change to sheet-selection logic beyond that** — do not touch
   `NamePlateProc` handling at all; it isn't a data source for this
   endpoint.

## Out of scope

- `Class/Pitch` on `"Info+Data Entry Form"` reads as an `int` (`26`) rather
  than a class/pitch code string — pre-existing, not reported, not touched.
- No automated test suite added (tracked separately in `docs/todo.md`).
- No changes to `read_test_sheet_from_excel()` (Test Sheet path )— unrelated
  to this bug.

## Verification plan

- Call `read_nameplate_from_excel()` directly against
  `2_Source_Data/raw_sources/NAME PLATE PROCEDURE.xlsx` and confirm
  `date_of_manuf` is a plain string, not a `datetime`.
- Hit `GET /api/nameplate/from-excel` against a live backend and confirm
  `200` with populated fields (not blank), matching the current
  `"Info+Data Entry Form"`-derived values.

## Verification (actual)

- Direct call to `read_nameplate_from_excel()` against the real
  `NAME PLATE PROCEDURE.xlsx`: returns `date_of_manuf: "MAY.2026"` (`str`,
  not `datetime`); all other fields populated (`series: "MAXFLO"`,
  `customer_name: "BREEZEAIR TECHNICAL SERVICES"`, `serial_no: "FM4032"`,
  etc.) — matches the pre-crash `"Info+Data Entry Form"`-derived values.
- Live backend: `uvicorn main:app` + `GET /api/nameplate/from-excel` →
  `200 {"nameplate": {...}, "xlsx_path": "...", "error": null}`, no crash.
- `python3 -m py_compile excel_source.py` passes.
- Also removed `_read_block_by_labels()`/`_norm()`, orphaned by dropping the
  dead `"Table 1"` branch (their only caller) — not adding this as new
  scope, just not leaving dead code behind from the edit.
