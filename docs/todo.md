# Nameplate & Test Sheet — Task Queue

> Rewritten at the end of every project-level task (DCOE anti-drift pattern).
> Hub-level cross-project tasks live in `C:\Dev\Operations\docs\todo.md`,
> not here.

## In progress

- [ ] **Commit the Quantity-field rework + scroll/layout tweaks** (not yet
      committed — awaiting Tebello's go-ahead). Touches `App.jsx`,
      `App.css`, `FormFields.jsx`, `main.py`. Note: `main.py` also has an
      unrelated pre-existing uncommitted `/api/speed` endpoint addition
      (9 lines) that predates this session — must stage only this task's
      hunks, not that one, when committing (`git add -p` or equivalent
      surgical staging).

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

## Done

- [x] **2026-07-15** — Test Sheet Fan Lines UI **replaced** by a Quantity
      field (Tebello clarified the table approach below was still the wrong
      design — no per-fan UI at all was wanted). Spec:
      `docs/specs/2026-07-15-test-sheet-quantity-field.md`. Not yet
      committed — see "In progress" above.
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
