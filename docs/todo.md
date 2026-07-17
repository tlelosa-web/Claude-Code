# Nameplate & Test Sheet — Task Queue

> Rewritten at the end of every project-level task (DCOE anti-drift pattern).
> Hub-level cross-project tasks live in `C:\Dev\Operations\docs\todo.md`,
> not here.

## In progress

- [ ] None currently.

## Next up

- [ ] **`/api/nameplate/from-excel` crashes** with `"Object of type datetime
      is not JSON serializable"` (found 2026-07-17 while verifying the dirty-
      tree cleanup below, against the real `NAME PLATE PROCEDURE.xlsx`).
      Pre-existing in committed code, unrelated to today's cleanup —
      `date_of_manuf` comes back as a Python `datetime` from the
      `Info+Data Entry Form` sheet read path and isn't stringified before
      `JSONResponse`. Also worth fixing while in there: the primary sheet
      check in `excel_source.py` looks for `"Table 1"`, which doesn't exist
      in the real workbook (`NamePlateProc` is the actual sheet name) — the
      endpoint currently only works by accident, falling through to the
      `Info+Data Entry Form` branch. A same-day attempt to fix the sheet-name
      check regressed to all-blank fields (verified, discarded — see Done
      below) — the correct fix needs the `NamePlateProc` branch's
      label-reading logic actually adapted to that sheet's real layout, not
      just a renamed condition.
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
