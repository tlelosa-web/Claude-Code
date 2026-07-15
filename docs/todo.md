# DELIVERY NOTE (delivery-note-system) — Task Queue

> Rewritten at the end of every project-level task (DCOE anti-drift pattern).
> Hub-level cross-project tasks live in `C:\Dev\Operations\docs\todo.md`,
> not here.

## In progress

- [ ] None currently.

## Next up

- [ ] No automated test suite exists yet (no `tests/` folder, no test
      runner configured). Not urgent for the current MVP scope, but worth
      adding before the feature grows (edit/delete, PDF export, auth).
- [ ] `README.md` is still the default `create-next-app` boilerplate — not
      wrong, just not delivery-note-specific. Low priority; update
      opportunistically alongside the next real feature task.
- [ ] No edit/delete for registered delivery notes yet, and no PDF/print
      output — likely the next real features once prioritized. Not started;
      no spec written yet.

## Backlog / ideas (not committed)

- [ ] Confirm whether `dev.db` should ever be seeded/reset as part of a
      documented workflow, or is purely local scratch state — not decided,
      not urgent.

## Done

- [x] **2026-07-15** — DCOE onboarding: `CLAUDE.md` (replacing the old
      `@AGENTS.md`-import stub), `docs/` scaffold (`todo.md`,
      `session-log.md`, `decisions/`, `bugs/`, `research/`, `specs/`),
      `.claude/commands/continue.md`, `.claude/settings.json`. Recorded
      `docs/decisions/ADR-001-dcoe-onboarding.md`.
- [x] **2026-07-15** — Committed the pre-existing uncommitted MVP feature
      (`048e08b`): delivery-note register (Prisma/SQLite model, 3 API
      routes, full page UI). Reviewed for correctness first; excluded
      `dev.db` from git and added `*.db`/`*.db-journal` to `.gitignore`.
