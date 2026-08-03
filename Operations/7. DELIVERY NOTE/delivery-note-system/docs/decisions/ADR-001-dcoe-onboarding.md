# ADR-001 — Onboard DELIVERY NOTE (delivery-note-system) to DCOE

**Date:** 2026-07-15
**Status:** Accepted
**Owner:** Tebello Lelosa

## Context

Hub-level `docs/todo.md` (`C:\Dev\Operations\docs\todo.md`) listed this
project as the last of the four remaining DCOE rollouts under ADR-002 (hub),
which pre-approved onboarding without re-litigating the decision per
project — but still required each project's own onboarding to happen as a
deliberate, concrete-work-triggered task with its own scope confirmation
(hub hard rule 6).

A Domain-agent scope pass found this project was not the "mechanical" case
the pipeline projects were (ADR-003 doesn't apply — this isn't a
5-folder-convention pipeline project). It's a genuinely early-stage Next.js
app: one commit ("Initial commit from Create Next App"), thin boilerplate
`CLAUDE.md`/`AGENTS.md`, and — critically — a **complete, working MVP
feature sitting entirely uncommitted** in the working tree (a delivery-note
register: Prisma/SQLite model, three API routes, a full page UI with
shadcn/ui components). This had never been committed since the initial
scaffold.

Asked Tebello two questions directly:
1. Onboarding depth — full DCOE scaffold (Nameplate precedent) vs.
   lightweight. Answer: **full DCOE scaffold**.
2. How to handle the uncommitted MVP — commit it first, or leave it and
   onboard around the current state. Answer: **commit it first**.

## Decision

1. **Committed the uncommitted MVP as its own baseline commit** (`048e08b`,
   "Add delivery note MVP: register + list with auto-incrementing DN
   numbers") before any DCOE docs were written, so onboarding documentation
   describes a state that's actually saved in git history, not working-tree
   state that could be lost. Reviewed the diff for correctness first (API
   routes, Prisma schema, `src/lib/prisma.ts` singleton pattern) — no
   issues found. Excluded `dev.db` (the SQLite dev database — a binary data
   file, not source) from the commit and added `*.db`/`*.db-journal` to
   `.gitignore`, since it wasn't there before and committing it wasn't part
   of what was asked.
2. **Full DCOE scaffold**, matching the `3. Nameplate & Test Sheet`
   precedent: project-level `CLAUDE.md` (replacing the old
   `@AGENTS.md`-import stub with real project-specific content), `docs/`
   (`todo.md`, `session-log.md`, `decisions/`, `bugs/`, `research/`,
   `specs/`), `.claude/commands/continue.md`, `.claude/settings.json`.
3. **`AGENTS.md` is kept, not deleted or folded in.** Unlike the generic
   pipeline-project legacy files seen elsewhere, this one has real,
   narrowly-scoped content: a warning that this project's Next.js version
   (16.2.6) is newer than any AI assistant's training data and has
   documented breaking changes — agents should read
   `node_modules/next/dist/docs/` before writing Next.js-specific code.
   Verified that docs folder actually exists. `CLAUDE.md` now points to it
   explicitly as a hard rule rather than silently importing it.
4. **No pre-existing folder-layout convention to reconcile** — this is a
   standard Next.js App Router project (`src/app/`, `src/components/`,
   `src/lib/`, `prisma/`), not one of the pipeline projects. DCOE's `docs/`
   sits at the project root like any other top-level folder — no ADR-003-
   style layering question here.
5. Model routing / effort tiers / agent roster policy is **not** duplicated
   in the new project `CLAUDE.md` — points to the hub `CLAUDE.md`'s
   standing policy, per the pattern ADR-002 established.

## Consequences

- This project now has its own `docs/todo.md` / `session-log.md` — future
  sessions opened inside this folder should read those first (its
  `CLAUDE.md` takes precedence over the hub brain per hub hard rule 1).
- Hub `docs/todo.md` § DCOE rollout: this project's sub-task is marked
  done. DCOE rollout is now complete for all currently-in-scope projects
  (`Inventory Management & Reports` was separately excluded — see hub
  `docs/decisions/ADR-004`).
- The committed MVP (`048e08b`) is the real baseline going forward —
  `docs/todo.md` § Next up should track what's actually missing (edit/
  delete, PDF export, auth, etc.) as the next planning task, not treated as
  "done" just because it's committed.
