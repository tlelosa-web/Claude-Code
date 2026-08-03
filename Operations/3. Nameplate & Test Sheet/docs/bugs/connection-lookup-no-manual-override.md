# Bug: Save Nameplate silently blocks connection override when suggest_connection() has no rule for the selected combo

## Symptom

Clicking **Save Nameplate** fails with:

> A valid connection (STAR or DELTA) could not be determined from the supplied values.

even when the user has manually picked STAR or DELTA in the Connection dropdown. There is no way to work around it from the UI — the manual selection is silently discarded.

## Reproduction

1. Start the app, select **Poles = 4**, **Voltage = 525**.
2. Select **Motor kW = 5.5** (a value that legitimately appears in the Motor
   kW dropdown for 4-pole, because the dropdown is populated per-pole only,
   not filtered by voltage — see Root Cause).
3. Manually select **Connection = DELTA** in the dropdown (overriding the
   failed auto-fill).
4. Fill in the remaining required fields and click **Save Nameplate**.
5. Request fails with HTTP 400: `"...Motor (kW), Poles and Voltage must be
   numeric..."`-style validation block, specifically the connection clause:
   `"A valid connection (STAR or DELTA) could not be determined from the
   supplied values."` — even though the user selected DELTA.

Verified directly against the real motor performance PDF and
`connection_lookup.py`:

```
525V 4P 5.5 -> suggest_connection() returns ("", "No valid STAR or DELTA
configuration for given motor size, pole, and voltage.")
```

(4-pole kW options pulled from
`2025 - CTP 022- PB4  Performance Data Rev 0.pdf` include 5.5, 7.5, 9.2 —
all of which exceed the `DELTA_RULES_MAX[(525,4)] = 4.0` / `(220,4) = 3.0`
ceilings in `connection_lookup.py`.)

## Root cause

Two compounding issues:

1. **`4_Scripts/backend/main.py`, `api_generate_pdf()`, lines 353-357:**
   ```python
   conn = ""
   if all(x is not None for x in (m_f, p_i, v_f)):
       c, _ = suggest_connection(v_f, p_i, m_f)
       if c in ("STAR", "DELTA"):
           conn = c
   ```
   `conn` is only ever set from `suggest_connection()`. Unlike the FLA
   handling three lines above it (`if not fla: fla = _clean(payload.fla)`),
   there is **no fallback to `payload.connection`** — the value the user
   explicitly chose in the Connection dropdown is never consulted. Compare
   with `api_test_record_sheet_from_nameplate()` (lines 479-485 in the same
   file), which does have the fallback:
   ```python
   if not conn:
       conn = _clean(payload.connection) or _clean(test_sheet.get("connection"))
   ```
   This is the pattern `api_generate_pdf()` is missing.

2. **`4_Scripts/frontend/src/components/FormFields.jsx`, line 92:**
   ```jsx
   const motorOptions = motorsByPole[data.pole] || [];
   ```
   The Motor kW dropdown is derived purely from `options.motors_by_pole`
   (built in `main.py`'s `_options_cached()`, lines 217-223), which lists
   every kW value present in the motor performance PDF for the selected
   pole count — **not filtered by the selected voltage**. So the UI happily
   offers kW values that have no corresponding STAR/DELTA rule at 525V or
   220V (both of which cap out much lower than 380V — e.g. `DELTA_RULES_MAX`
   only goes up to 4.0kW at 525V/4-pole vs. 9.2kW available in the 380V-
   oriented motor table). This makes the failure in (1) reachable through
   completely normal UI interaction, not just an edge case requiring manual
   text entry.

Note: `connection_lookup.py`'s STAR/DELTA kW boundaries (e.g. the 380V gap
between `STAR_RULES[(380,4)]=3.0` and `DELTA_RULES_380_MIN[(380,4)]=4.0`)
line up exactly with the discrete kW steps in the motor PDF table, so that
particular gap is *not* independently reachable via the dropdowns — it's
the voltage-crossed combinations (2 above) that are the real trigger.

## Affected files

- `4_Scripts/backend/main.py` — `api_generate_pdf()` (lines 340-379,
  specifically 353-357: missing `payload.connection` fallback)
- `4_Scripts/backend/connection_lookup.py` — `suggest_connection()` /
  `DELTA_RULES_MAX` (lines 43-53): legitimate low ceilings at 525V/220V that
  make failures common for larger motors
- `4_Scripts/frontend/src/components/FormFields.jsx` — line 92: Motor kW
  options not filtered by selected voltage, so incompatible combos are
  directly selectable

## Suggested fix approach (not implemented — investigation only)

1. In `api_generate_pdf()`, mirror the FLA fallback pattern: if
   `suggest_connection()` doesn't return STAR/DELTA, fall back to
   `_clean(payload.connection)` before deciding whether to error out (same
   shape as `api_test_record_sheet_from_nameplate()` already does).
2. Separately (UX improvement, not strictly required to fix the override
   bug): filter `motors_by_pole` in `_options_cached()` by voltage as well
   as pole — e.g. key by `(voltage, pole)` and only include kW values that
   have *some* rule (STAR or DELTA) in the connection tables — so users
   aren't offered combinations guaranteed to fail engineering rules in the
   first place. This is optional if (1) is fixed, since manual override
   would then work, but doing both avoids ever *needing* the override for
   the common case.

## Failing test case (contract for the fix)

```python
# 4_Scripts/backend — pytest-style, no fixture infra needed
from connection_lookup import suggest_connection

def test_reproduces_gap():
    conn, err = suggest_connection(525, 4, 5.5)
    assert conn == ""  # confirms the gap exists — this call alone is correct
                        # behavior; the bug is that the caller has no fallback

# main.py integration case (requires a running app or TestClient):
# POST /api/generate-pdf with:
#   { motor: "5.5", pole: "4", voltage: "525", connection: "DELTA", ...other required fields... }
# Expected after fix: 200 OK, PDF generated with connection=DELTA (the
# user's manual choice honored).
# Current (buggy) behavior: 400 "A valid connection (STAR or DELTA) could
# not be determined from the supplied values."
```

## Secondary observations (lower severity, not separately filed)

- **Same root-cause class as the already-logged datetime-serialization bug**
  (`docs/todo.md` § Next up): `excel_source.py`'s `read_test_sheet_from_excel()`
  (line 288, `"date": _cell(ws, 1, 21)`) returns a raw Python `datetime`
  object straight from the Excel cell, same as the already-known
  `read_nameplate_from_excel()` issue. Currently **not reachable** through
  the live app — `main.py`'s `api_test_record_sheet_from_nameplate()` never
  reads `test_sheet.get("date")` into `derived_fallback` — but worth fixing
  in the same pass as the logged bug since it's the identical defect
  pattern in a sibling function, and would resurface the moment anyone
  wires that field up.
- **Dead endpoint / stale contract:** `POST /api/reports/test-record-sheet`
  (main.py lines 381-438, accepting a real `test_lines: list[TestLinePayload]`
  array) is no longer called anywhere in the frontend — `App.jsx` only calls
  `/api/reports/test-record-sheet/from-nameplate` (quantity-driven), per the
  2026-07-15 Fan Lines UI rework logged in `docs/todo.md`. Not a live bug,
  but it's a second, now-orphaned copy of the `TestLinePayload` contract
  that the project's own CLAUDE.md flags as fragile — worth a deliberate
  decision (remove vs. keep for a future per-fan-editing feature) rather
  than leaving two divergent contracts to accidentally drift.
- **Cosmetic:** `pdf_generator.py`'s `_render_test_sheet_direct()` truncates
  or auto-shrinks font only for the Row 2 fields (Contract No./Series/Size/
  Imp Form, line 156: `fs = 7 if len(val) > 14 else 9`). `customer_name`
  (Row 3), `motor_desc` (Row 5 Description box) and other longer free-text
  fields have no equivalent length guard, so an unusually long customer
  name or motor description can visually overflow its bordered box. No
  crash, no data loss — layout only.
- **Not a bug, confirmed safe by design:** the motor performance PDF
  (`2025 - CTP 022- PB4  Performance Data Rev 0.pdf`) only contains 2/4/6-
  pole data (no 8-pole rows), even though `connection_lookup.py` defines
  STAR/DELTA rules for 8-pole motors. `_options_cached()` in `main.py`
  intersects `poles_from_conn` with `poles_from_motor`, so 8-pole is
  correctly excluded from the UI dropdown — this is dead capability, not a
  live defect. Flagging only because `excel_source.py`'s Excel-import path
  (`read_nameplate_from_excel`) does not perform the same intersection
  check — an Excel-sourced nameplate with an 8-pole motor would fail FLA
  auto-lookup (falls back to the Excel sheet's own FLA value if present,
  which is graceful) but this path was not exercised in this investigation
  since it requires a workbook row with an 8-pole motor to trigger.
