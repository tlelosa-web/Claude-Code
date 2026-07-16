# Nameplate & Test Sheet — Task Queue

> Rewritten at the end of every project-level task (DCOE anti-drift pattern).
> Hub-level cross-project tasks live in `C:\Dev\Operations\docs\todo.md`,
> not here.

## In progress

- [ ] None currently.

## Next up

- [ ] Consider a real automated test suite (pytest for backend, a JS test
      runner for frontend) — `tests/` currently holds ad-hoc manual-check
      scripts only, not a gated suite. Not urgent; flagged in `CLAUDE.md` §
      Testing Standards.

## Backlog / ideas (not committed)

- [ ] `index_work.lock.bak`-style stray artifacts: none known here, but
      worth a periodic `.git` health check given the OneDrive-era lock
      issues seen in SOPS (this project's `.git` was never inside OneDrive
      sync, so lower risk — not urgent).
- [ ] `main.py` still carries an unrelated pre-existing uncommitted
      `/api/speed` endpoint (9 lines, predates this session — origin
      unknown, not something built or removed by any session tracked in
      this log). Left alone every time since it was never named or
      approved for either commit or removal. Tebello: worth deciding
      whether to finish/commit it or discard it next time this file is
      touched, rather than letting it sit indefinitely.

## Done

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
