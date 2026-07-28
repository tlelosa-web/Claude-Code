# Daily Sales Order Files (pipeline)

Python pipeline for Fan Movement (Pty) Ltd that rebuilds a Sales Order Excel
report from SAGE ERP CSV exports plus a Contract Register workbook. No git
repo (`C:\Dev\Operations\1. Daily Sales Order Files`) — lightweight DCOE
onboarding per the hub's ADR-003 pipeline convention (own `CLAUDE.md`, no
`docs/` scaffold; history lives in `1_Documentation/USER_GUIDE.md` instead).
Runs roughly once per weekday, manually (no scheduler).

## 2026-07-28 — Architecture and reusable facts
**Source:** project `CLAUDE.md` / `1_Documentation/USER_GUIDE.md`
**Status:** active

- **Pipeline shape:** five scripts run in sequence via
  `RUN_DAILY_PIPELINE.bat`: extract PDF payment-status comments → rebuild
  the daily tab from CSVs + Contract Register → re-inject validated payment
  statuses into column J → format/highlight the report → rebuild the Monthly
  Invoice tab.
- **Folder layout is load-bearing** (hardcoded into scripts, not just a
  convention): `1_Documentation/` (execution log + fix history, canonical
  project history — auto-appended to by `run_daily_update.py`),
  `2_Source_Data/` (CSV inputs), `3_Live_Reports/` (production Excel
  outputs), `4_Scripts/`, `5_Archive_and_Debug/`. This same 5-folder layout
  is reused by three other pipeline projects in the Operations vault
  (`8. AvgMovement`, `Inventory Management & Reports`,
  `3. Nameplate & Test Sheet`) — see hub `docs/patterns.md` pattern #6.
- **External dependencies live outside the project tree:** a OneDrive-hosted
  Contract Register workbook and a Released-Jobs PDF folder, both
  colleague-owned — paths aren't guaranteed stable and shouldn't be assumed
  without checking `USER_GUIDE.md` first.
- **Self-correcting filename resolution:** the pipeline looks for
  `Ops Sales Order Report - MM.YYYY.xlsx` for the current month, falls back
  to auto-renaming a legacy filename if found, then falls back further to
  the most recently modified matching report — a reusable pattern for any
  pipeline that needs to tolerate manual file-naming drift.
- **Design decision — blank over stale:** when no validated payment status
  exists (no prior daily-sheet value, no PDF-comment match), column J is
  deliberately left blank rather than filled with a stale `VLOOKUP` formula
  — an explicit "blank is more honest than a guess" choice, fixed 2026-05-28.
- **History mechanism:** `run_daily_update.py` auto-appends timestamped
  SUCCESS/FAILURE entries directly into `USER_GUIDE.md`'s Execution Log —
  this is the project's actual audit trail; don't change that behavior as a
  side effect of unrelated work.

## 2026-07-28 — Status
**Source:** `1_Documentation/USER_GUIDE.md` Execution Log
**Status:** active

Healthy and current — last successful run 2026-07-28, consistent daily
SUCCESS entries through July 2026, no open bugs in Fix History as of this
survey. No outstanding items to add to the hub queue for this project.
