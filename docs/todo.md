# DELIVERY NOTE (delivery-note-system) — Task Queue

> Rewritten at the end of every project-level task (DCOE anti-drift pattern).
> Hub-level cross-project tasks live in `C:\Dev\Operations\docs\todo.md`,
> not here.

## In progress

- [ ] None currently.

## Next up

- [ ] No automated test suite exists yet (no `tests/` folder, no test
      runner configured). Not urgent for the current MVP scope, but worth
      adding before the feature grows further (auth, etc.).
- [ ] `README.md` is still the default `create-next-app` boilerplate — not
      wrong, just not delivery-note-specific. Low priority; update
      opportunistically alongside the next real feature task.

## Backlog / ideas (not committed)

- [ ] Confirm whether `dev.db` should ever be seeded/reset as part of a
      documented workflow, or is purely local scratch state — not decided,
      not urgent.

## Done

- [x] **2026-07-17/18** — Edit / Delete / PDF export for delivery notes.
      Spec: `docs/specs/edit-delete-pdf-export-2026-07-17.md`. Built in 4
      sequenced commits: `26a3d90` (DN-number generation fixed to use
      numeric max, not most-recently-created — makes Delete safe),
      `1b35296` (Edit: Date/Customer/Description via `PATCH /api/dn/[id]`,
      `dnNumber` locked, shadcn Dialog), `24b9cc8` (Delete: `DELETE
      /api/dn/[id]`, shadcn AlertDialog confirmation, hard delete),
      `b7b9b95` (PDF export: `pdf-lib`, `GET /api/dn/[id]/pdf` generates a
      real downloadable A4 PDF). `prisma/schema.prisma` gained
      `updatedAt`, migration `20260717121049_add_updated_at`.
      `dev.db` was empty (0 rows) so establishing that migration's baseline
      was non-destructive — confirmed with Tebello before deleting it.
      Orchestrator-side verification (read every diff line-by-line, then
      drove the actual feature in a browser against a fresh `dev.db`):
      registered notes, edited one (confirmed a crafted PATCH with
      `dnNumber` in the body is ignored), deleted the newest one and
      confirmed the next-DN preview recomputed to the correct value rather
      than skipping ahead, downloaded a real PDF and confirmed its
      filename/content. `npm run lint` clean on every touched file (2
      pre-existing unrelated errors confirmed present before this batch,
      untouched lines).
      **Found and fixed along the way** (see `docs/bugs/prisma7-driver-
      adapter-missing-2026-07-17.md`): regenerating the Prisma Client for
      the `updatedAt` migration exposed a latent gap — `schema.prisma` had
      no datasource `url`, which Prisma 7.8.0's driver-adapter architecture
      no longer tolerates (every DB route 500'd, not just the new ones).
      Fixed by adding `@prisma/adapter-better-sqlite3` and wiring it into
      `src/lib/prisma.ts` (commit `6422542`) — this was a pre-existing
      time bomb, not something this batch introduced, and would have hit
      the same way on any future schema change.
      Also hit (documented in the same bug file, not a code fix): Turbopack
      failed with a Windows junction-point error trying to link the
      regenerated Prisma client into `.next/dev/`; verification used
      `next dev --webpack` to work around it. `npm run dev` is unchanged
      (still defaults to Turbopack) since this may be machine-specific.
- [x] **2026-07-15** — DCOE onboarding: `CLAUDE.md` (replacing the old
      `@AGENTS.md`-import stub), `docs/` scaffold (`todo.md`,
      `session-log.md`, `decisions/`, `bugs/`, `research/`, `specs/`),
      `.claude/commands/continue.md`, `.claude/settings.json`. Recorded
      `docs/decisions/ADR-001-dcoe-onboarding.md`.
- [x] **2026-07-15** — Committed the pre-existing uncommitted MVP feature
      (`048e08b`): delivery-note register (Prisma/SQLite model, 3 API
      routes, full page UI). Reviewed for correctness first; excluded
      `dev.db` from git and added `*.db`/`*.db-journal` to `.gitignore`.
