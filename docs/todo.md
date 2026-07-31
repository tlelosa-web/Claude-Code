# Nameplate & Test Sheet — Task Queue

> Rewritten at the end of every project-level task (DCOE anti-drift pattern).
> Hub-level cross-project tasks live in `C:\Dev\Operations\docs\todo.md`,
> not here.

## In progress

- [ ] None currently.

## Next up

- [ ] **Save Nameplate connection override — remaining follow-ups.** Step 1
      of the original fix plan (the actual override-blocking bug) is fixed
      — see Done below. Remaining optional items from
      `docs/bugs/connection-lookup-no-manual-override.md`:
      2. Optional UX follow-up: filter `motors_by_pole` in
         `_options_cached()` by voltage too (key by `(voltage, pole)`,
         only include kW values with *some* STAR/DELTA rule) so incompatible
         combos aren't offered in the first place. Not required now that (1)
         is done, but avoids ever needing the override for the common case.
      3. While in the area, fix the same datetime-not-JSON-serializable
         defect pattern in `excel_source.py`'s `read_test_sheet_from_excel()`
         (line 288, raw `datetime` from `_cell(ws, 1, 21)`) alongside the
         already-logged `from-excel` bug below — same root cause, currently
         dead code path but will resurface if that field gets wired up.
- [ ] Decide fate of orphaned `POST /api/reports/test-record-sheet` endpoint
      (`main.py` lines 381-438) — a second, unused copy of the
      `TestLinePayload` array contract, superseded by the quantity-driven
      `/api/reports/test-record-sheet/from-nameplate` flow (2026-07-15
      rework, see Done below) but never removed. Not a live bug, but it's a
      second fragile payload-shape contract sitting unused — pick remove vs.
      keep-for-future-per-fan-editing deliberately rather than leaving two
      to drift. Found during the 2026-07-29 bug-hunt pass.
- [ ] Cosmetic: `pdf_generator.py`'s `_render_test_sheet_direct()` only
      guards text overflow/auto-shrink for Row 2 fields (line 156); longer
      free-text fields like `customer_name` and `motor_desc` have no
      equivalent length guard and can visually overflow their bordered box.
      No crash/data loss, layout only. Found during the 2026-07-29 bug-hunt
      pass.
- [ ] Consider a real automated test suite (pytest for backend, a JS test
      runner for frontend) — `tests/` currently holds ad-hoc manual-check
      scripts only, not a gated suite. Not urgent; flagged in `CLAUDE.md` §
      Testing Standards.

## Backlog / ideas (not committed)

- [ ] `index_work.lock.bak`-style stray artifacts: none known here, but
      worth a periodic `.git` health check given the OneDrive-era lock
      issues seen in SOPS (this project's `.git` was never inside OneDrive
      sync, so lower risk — not urgent).

## Done

- [x] **2026-07-31** — Save Nameplate connection-override fix (fix-plan step
      1 only): `main.py`'s `api_generate_pdf()` now falls back to
      `_clean(payload.connection)` when `suggest_connection()` finds no
      STAR/DELTA rule for the combo, mirroring the existing pattern in
      `api_test_record_sheet_from_nameplate()`. Spec:
      `docs/specs/2026-07-31-connection-override-fallback-fix.md`. Bug
      report: `docs/bugs/connection-lookup-no-manual-override.md`. Verified
      against a live `uvicorn` server: `POST /api/generate-pdf` with
      `{motor: "5.5", pole: "4", voltage: "525", connection: "DELTA"}` now
      returns `200` with a valid PDF (was `400`); confirmed the no-override
      case (`connection: ""`) still correctly returns `400`, so the fix only
      rescues a genuine manual override rather than masking real validation
      failures. Fix-plan steps 2 (voltage-filtered motor options) and 3
      (`excel_source.py` datetime fix) remain open — see Next up.
- [x] **2026-07-28** — `/api/nameplate/from-excel` datetime crash fixed.
      `date_of_manuf` in `excel_source.py`'s `"Info+Data Entry Form"` branch
      is now formatted via `_fmt_month_year()` before returning (was a raw
      `datetime`, unlike the `else` branch which already formatted it).
      Confirmed by direct inspection why the 2026-07-17 attempt regressed:
      `NamePlateProc` is a static instructions/reference sheet with no real
      per-job data — `"Info+Data Entry Form"` is the correct data source and
      stays the effective primary. Also dropped the dead, unreachable
      `"Table 1"` primary-sheet check (never matches the real workbook) and
      the now-orphaned `_read_block_by_labels`/`_norm` helpers. Spec:
      `docs/specs/2026-07-28-excel-import-datetime-and-sheet-check.md`.
      Verified against the real `NAME PLATE PROCEDURE.xlsx` both directly
      and via a live `uvicorn` server (`200`, populated fields, no crash).
- [x] **2026-07-17** — Dirty working tree (flagged by the 2026-07-17
      hub-level cross-project status pass) reviewed and resolved. Read every
      file's actual diff before acting, per the pre-commit review discipline:
      - `main.py`'s stray `/api/speed` endpoint — discarded. Verified the
        frontend never calls it (computes op-speed locally from a hardcoded
        pole→RPM map instead); confirmed dead code before dropping it.
      - `excel_source.py`'s sheet-fallback change (checking for the real
        `NamePlateProc` sheet name instead of the nonexistent `Table 1`) —
        **discarded as a regression**, not committed. Verified directly
        against the real `NAME PLATE PROCEDURE.xlsx`: the committed code
        (falling through to `Info+Data Entry Form`) correctly extracts real
        data; the uncommitted diff matched `NamePlateProc` but its
        label-reading logic returned every field blank. Logged as a proper
        follow-up item above rather than shipping the broken version.
      - `1_Documentation/DEPLOYMENT.md` + `CONFLICT_ANALYSIS.md` (stale
        OneDrive path → `C:\Dev\Operations\...`, from the 2026-07-15 path
        audit) and `1_Documentation/USER_GUIDE.md` (removed docs for the now-
        dropped `/api/speed`, fixed stale `motor_kw`→`motor` param names for
        `/api/fla`/`/api/connection`) — verified `/api/fla` and
        `/api/connection` against a live server (both return correct values
        with the documented param names) and committed.
      - `doc_history.json` and `4_Scripts/backend/logs/backend.log` — these
        are runtime-generated, not source (2900+ and 400+ line diffs from
        normal app use). Added both to `.gitignore` and `git rm --cached`
        them (kept on disk, just untracked going forward) instead of
        committing another log dump.
      - Untracked `test_api_fixes.py` (ad-hoc endpoint smoke-test, matches
        this project's existing `tests/` convention of manual-check scripts)
        — moved into `tests/`, trimmed the `/api/speed` case since that
        endpoint was dropped, verified it passes against a live server.
- [x] **2026-07-16** — Hidden (no-terminal) launcher committed (`0b36ffb`):
      `Launch_NamePlate_Tool.vbs` / `Stop_NamePlate_Tool.vbs` +
      `RUN_PIPELINE_HIDDEN.ps1` / `STOP_PIPELINE.ps1`. Root cause found
      during testing: killing only the port-listening process doesn't stop
      the app, because `uvicorn --reload` runs a supervisor that respawns a
      new worker — fixed by recording the root PIDs at launch
      (`5_Archive_and_Debug/pipeline.pids`, gitignored) and using
      `taskkill /T` to kill the whole tree. `Nameplate Tool.lnk` (project
      root) repointed at the hidden launcher; a matching desktop shortcut
      was also created for Tebello directly (not tracked in git). Documented
      in `1_Documentation/USER_GUIDE.md` § Launching Without a Terminal.
      `RUN_PIPELINE.bat` (visible windows) kept as-is for debugging.
- [x] **2026-07-15** — Test Sheet Fan Lines UI **replaced** by a Quantity
      field, committed (`d5aab64`) — Tebello clarified the table approach
      below was still the wrong design; no per-fan UI at all was wanted.
      Includes the scroll/layout fixes from the same session (wider form
      column reverted to a 3-column page split once field density made it
      unnecessary, `align-items` misalignment fix, `field-span-3` on
      Customer Name). Spec: `docs/specs/2026-07-15-test-sheet-quantity-field.md`.
- [x] **2026-07-15** — Test Sheet Fan Lines UI fix committed (`7c0f785`),
      later superseded by the Quantity-field rework above:
      `App.jsx`/`App.css` per-fan panel replaced with a table matching
      `pdf_generator.py`'s output. Spec:
      `docs/specs/2026-07-15-test-sheet-fan-lines-table.md`.
- [x] **2026-07-15** — DCOE onboarding committed (`5571d63`): `CLAUDE.md`,
      `docs/` scaffold (`todo.md`, `session-log.md`, `decisions/`, `bugs/`,
      `research/`, `specs/`), recorded
      `docs/decisions/ADR-001-dcoe-onboarding.md`. Existing 5-folder
      GEMINI-era layout (`1_Documentation/` → `5_Archive_and_Debug/`) kept
      as-is; DCOE `docs/` layered alongside it, not merged into it.
