## 2026-07-23 — What it is & stack
**Source:** tlelosa-web/NamePlateTool CLAUDE.md, README.md
**Status:** active

Full-stack desktop web app (local-only, Windows) that generates two PDFs
from one data-entry form — a motor **Nameplate** and a **Test Record
Sheet** — for Fan Movement's fan/motor assemblies. Source concept: the
`NAME PLATE PROCEDURE` Excel workbook (`NamePlateProc` tab, `Info+Data
Entry Form`).

- Backend: FastAPI (Python 3.11+) + ReportLab/pypdf/pdfplumber —
  `4_Scripts/backend/`.
- Frontend: React 19 + Vite — `4_Scripts/frontend/`.
- No database — stateless request→PDF; `doc_history.json` is just a
  generation log, not a source of truth.
- Predates DCOE and uses its own 5-folder layout
  (`1_Documentation/` → `2_Source_Data/` → `3_Live_Reports/` →
  `4_Scripts/` → `5_Archive_and_Debug/`); DCOE's `docs/` sits alongside
  it, not merged in.
- Launch via `RUN_PIPELINE.bat` (visible) or `Launch_NamePlate_Tool.vbs` →
  `RUN_PIPELINE_HIDDEN.ps1` (no terminal windows).

## 2026-07-23 — Payload-shape contract (cross-file gotcha)
**Source:** tlelosa-web/NamePlateTool CLAUDE.md
**Status:** active

`App.jsx`'s `TestLinePayload`-shaped objects, `main.py`'s `TestLinePayload`
pydantic model, and `pdf_generator.py`'s table renderer share one implicit
contract with no shared type system across the Python/JS boundary.
Changing one without checking the other two breaks PDF output silently.
Any change to a `test_lines`/nameplate field name or shape must touch all
three together, in the same task.

## 2026-07-23 — uvicorn --reload can't be killed by port alone
**Source:** tlelosa-web/NamePlateTool docs/session-log.md (2026-07-16 entry)
**Status:** active

`uvicorn --reload` runs a supervisor process that respawns a new worker
(new PID) the instant the old one is killed — killing whatever's listening
on the port just triggers whack-a-mole, never actually stops the backend.
Fix used here: capture the **root** process IDs at launch
(`Start-Process -PassThru` → `5_Archive_and_Debug/pipeline.pids`,
gitignored) and `taskkill /PID <root> /T /F` to kill the whole tree.

## 2026-07-28 — Bug still unfixed, no new attempt since revert
**Source:** session (cross-project status survey), `docs/todo.md`
**Status:** active

As of this check, the Excel-import bug below is still open and untouched
since the 2026-07-17 reverted attempt — it's the only active defect across
all 5 tracked repos and the top cross-project priority. No GitHub issue
tracks it; it lives only in this project's `docs/todo.md`.

## 2026-07-23 — Known open bug: Excel-import datetime + wrong sheet-name check
**Source:** tlelosa-web/NamePlateTool docs/todo.md
**Status:** active

`/api/nameplate/from-excel` crashes with `"Object of type datetime is not
JSON serializable"` — `date_of_manuf` comes back as a Python `datetime`
from the `Info+Data Entry Form` sheet path and isn't stringified before
`JSONResponse`. Separately, `excel_source.py`'s primary-sheet check looks
for `"Table 1"`, which doesn't exist in the real workbook (the actual
sheet is `NamePlateProc`) — the endpoint currently only works by falling
through to the `Info+Data Entry Form` branch. A same-day attempt to fix
the sheet-name check regressed to all-blank fields (tried, reverted) —
the real fix needs `NamePlateProc`'s label-reading logic adapted to that
sheet's actual layout, not just a renamed condition string.

## 2026-07-23 — Testing status
**Source:** tlelosa-web/NamePlateTool CLAUDE.md, docs/todo.md
**Status:** active

No automated test suite (pytest/vitest) yet. `tests/` holds ad-hoc
manual-check scripts only (`autofill_tests.py`, `check_api.py`,
`check_connection.py`, `inspect_excel.py`, `test_read_excel.py`,
`test_api_fixes.py`). Any non-trivial backend change should be manually
verified against a generated PDF before being considered done.
