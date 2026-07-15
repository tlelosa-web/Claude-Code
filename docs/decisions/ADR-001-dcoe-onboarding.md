# ADR-001 — Onboard Nameplate & Test Sheet to DCOE

**Date:** 2026-07-15
**Status:** Accepted
**Owner:** Tebello Lelosa

## Context

Hub-level `docs/todo.md` (`C:\Dev\Operations\docs\todo.md`) listed this
project as one of five pending DCOE rollouts under ADR-002 (hub), which
pre-approved onboarding all five without re-litigating the decision per
project — but still required each project's own onboarding to happen as a
deliberate, concrete-work-triggered task with its own scope confirmation
(hub hard rule 6).

Concrete work arrived this session: a UI complaint about the "Test Sheet Fan
Lines" feature (`4_Scripts/frontend/src/App.jsx`). Tebello was asked
directly whether "update the project according to claude.md" meant applying
hub conventions informally for this one fix, or doing the full onboarding —
answer: **full onboarding now**.

## Decision

1. Create a project-level `CLAUDE.md`, generalized from SOPS's v3.2 (the
   only DCOE-mature project), adapted for this project's actual stack
   (FastAPI + React/Vite, no database, stateless request→PDF) rather than
   copied verbatim.
2. Keep the pre-existing 5-folder GEMINI-era layout
   (`1_Documentation/` → `5_Archive_and_Debug/`) untouched. DCOE's `docs/`
   planning layer (`todo.md`, `specs/`, `decisions/`, `bugs/`, `research/`,
   `session-log.md`) sits alongside it, not merged into it — this project
   is a full-stack app, not one of the three pipeline projects that share
   the pending pipeline-convention reconciliation (`docs/patterns.md` § 6
   at hub level), so that reconciliation doesn't apply here.
3. `1_Documentation/GEMINI.md` (the prior AI-brain file, used before this
   project ran on Claude Code) is left in place for history — not deleted,
   not treated as authoritative for Claude sessions going forward.
4. Model routing / effort tiers / agent roster policy is **not** duplicated
   in the new project `CLAUDE.md` — it points to the hub `CLAUDE.md`'s
   standing policy, per the pattern ADR-002 already established.

## Consequences

- This project now has its own `docs/todo.md` / `session-log.md` — future
  sessions opened inside this folder should read those first (its
  `CLAUDE.md` takes precedence over the hub brain per hub hard rule 1).
- The Test Sheet Fan Lines fix (this same session) is the first task run
  under the new structure — spec written to `docs/specs/` before
  implementation, per DCOE rules.
- Hub `docs/todo.md` § DCOE rollout gets this project's sub-task marked
  done.
