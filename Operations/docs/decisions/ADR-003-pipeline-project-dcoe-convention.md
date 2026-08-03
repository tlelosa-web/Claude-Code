# ADR-003 — DCOE convention for pipeline projects (lightweight onboarding)

**Date:** 2026-07-15
**Status:** Accepted
**Owner:** Tebello Lelosa

## Context

ADR-002 flagged that the three pipeline projects (`1. Daily Sales Order
Files`, `8. AvgMovement`, `Inventory Management & Reports`) share the
`1_Documentation/ → 2_Source_Data/ → 3_Live_Reports/ → 4_Scripts/ →
5_Archive_and_Debug/` folder convention (`docs/patterns.md` § 6), and that
this needed reconciling with DCOE's `docs/specs/`+`docs/todo.md` convention
once, generically, on whichever pipeline project onboarded first.

`1. Daily Sales Order Files` onboarded first (2026-07-15). Domain-agent
exploration found:

- The five pipeline folders are **load-bearing** — scripts hardcode these
  paths (e.g. `run_daily_update.py` writes execution-log entries directly
  into `1_Documentation/USER_GUIDE.md`; `extract_pdf_comments.py` writes to
  `5_Archive_and_Debug/`). They cannot be renamed or restructured without
  touching code.
- `1_Documentation/USER_GUIDE.md` already contains an informal **Execution
  Log** and **Fix History** section that functions like `docs/session-log.md`
  + `docs/decisions/` combined, auto-appended to by the pipeline scripts
  themselves on every run.
- The earlier hub project-index note referencing legacy `AGENT.md`/`GEMINI.md`
  files in this project was stale — no such files exist. The only
  agent-adjacent artifact is `.qwen/settings.json` (a permissions config, not
  an instruction file).

Asked Tebello directly: onboarding depth (lightweight vs. full DCOE scaffold)
and precedent scope (decide generically now vs. per-project later). Answers:
**lightweight**, and **write the convention generically now**.

## Decision

1. **Pipeline projects get a lightweight DCOE onboarding**, not the full
   SOPS-style scaffold. Onboarding means: add a project-root `CLAUDE.md`
   that documents the existing pipeline folder layout, explains why it's
   load-bearing (don't rename/restructure without a code change), and
   defers to the project's existing `1_Documentation/` guide for run
   instructions and history.
2. **No parallel `docs/` DCOE scaffold** (`docs/specs/`, `docs/todo.md`,
   `docs/session-log.md`, `docs/decisions/`) gets added alongside the
   pipeline folders. The existing `1_Documentation/<guide>.md` Execution
   Log / Fix History sections remain canonical for that project's history —
   they are not duplicated or migrated into hub-style docs files.
3. **Ad hoc exception:** if a pipeline project later takes on a genuinely
   new feature or redesign (not a routine fix), a one-off
   `docs/specs/<date>-<task>.md` may be created for that task alone, without
   standing up a permanent `docs/` directory. This should be rare — these
   are stable automation scripts, not evolving applications.
4. **Runtime behavior is out of scope for onboarding.** Scripts that
   auto-append to the project's guide file (e.g. `run_daily_update.py`) are
   left untouched. Onboarding is a documentation/process decision, not a
   code change.
5. **This convention applies to all three pipeline projects** —
   `1. Daily Sales Order Files` (done, this ADR), `8. AvgMovement`, and
   `Inventory Management & Reports` — without re-litigating per project.
   Their onboarding becomes mechanical: explore, confirm nothing project-
   specific breaks the pattern, add the analogous `CLAUDE.md`.

## Consequences

- `docs/patterns.md` § 6 updated to mark this reconciled, pointing here.
- Root `CLAUDE.md` project index updated: `1. Daily Sales Order Files` now
  shows lightweight-DCOE status; stale `AGENT.md`/`GEMINI.md` note removed.
- `docs/todo.md`: the "pipeline convention reconciliation" sub-task and the
  `1. Daily Sales Order Files` onboarding sub-task both close. `8. AvgMovement`
  and `Inventory Management & Reports` remain open but unblocked — their
  onboarding sessions can skip straight to project-specific Domain-agent
  confirmation instead of re-deciding this convention.
