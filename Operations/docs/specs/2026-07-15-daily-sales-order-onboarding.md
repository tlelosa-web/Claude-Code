# Daily Sales Order Files — DCOE Onboarding

**Origin:** ADR-002's "pipeline convention reconciliation" sub-task —
`1. Daily Sales Order Files` is the first of three pipeline projects to
onboard, so the reconciliation between the pipeline folder layout and
DCOE's `docs/` convention (`docs/patterns.md` § 6) happens here first, then
reuses for `8. AvgMovement` and `Inventory Management & Reports`.

**Author:** Context/Planner pass, root hub session, 2026-07-15, following a
Domain-agent scope-confirmation pass.

-----

## Findings (Domain-agent exploration)

- Pipeline: Sage ERP CSV exports + Contract Register workbook →
  `3_Live_Reports/Ops Sales Order Report - MM.YYYY.xlsx`, via five scripts
  chained in `RUN_DAILY_PIPELINE.bat`, run roughly daily/ad hoc.
- The five pipeline folders (`1_Documentation/` → `5_Archive_and_Debug/`)
  are load-bearing — hardcoded into script paths. Cannot be renamed without
  a code change.
- `1_Documentation/USER_GUIDE.md` already contains an informal Execution
  Log (auto-appended by `run_daily_update.py` on every run) and Fix History
  section — functionally equivalent to `docs/session-log.md` +
  `docs/decisions/` combined.
- The hub project index's "Legacy `AGENT.md`/`GEMINI.md`" note was stale —
  no such files exist anywhere in this project tree. Only agent-adjacent
  artifact: `.qwen/settings.json` (a Qwen CLI permissions config, not an
  instruction file).

## Decisions (asked Tebello directly, both answered "recommended")

1. **Onboarding depth: lightweight.** Add a project `CLAUDE.md` documenting
   the existing structure; do not add `docs/specs/`, `docs/todo.md`,
   `docs/session-log.md`, or `docs/decisions/` alongside the pipeline
   folders. `USER_GUIDE.md`'s existing log sections stay canonical.
2. **Precedent scope: generic, now.** Written as ADR-003, covering all
   three pipeline projects, not just this one — `8. AvgMovement` and
   `Inventory Management & Reports` reuse it without re-deciding.

## Execution

1. `docs/decisions/ADR-003-pipeline-project-dcoe-convention.md` — records
   both decisions and the generic pipeline-project convention.
2. `1. Daily Sales Order Files/CLAUDE.md` — new lightweight project brain:
   what the pipeline does, folder layout (marked load-bearing), pointer to
   `USER_GUIDE.md` as canonical history, and project-specific hard rules
   (live-report files are production data; don't restructure folders
   without a code change; don't touch the auto-log-append behavior as a
   side effect; no parallel `docs/todo.md`/`docs/session-log.md`).
3. `docs/patterns.md` § 6 — updated from "not yet reconciled" to
   "reconciled — see ADR-003," with the resolution summarized inline.
4. Root `CLAUDE.md` project index — `1. Daily Sales Order Files` row
   updated from "Legacy `AGENT.md`/`GEMINI.md` — not onboarded" to
   "✅ Lightweight DCOE — own `CLAUDE.md` per ADR-003."
5. `docs/todo.md` — pipeline-convention-reconciliation and
   `1. Daily Sales Order Files` sub-tasks marked done; `8. AvgMovement` and
   `Inventory Management & Reports` left open but noted as unblocked
   (convention already decided, their sessions can skip straight to
   project-specific Domain confirmation).

No code changes. No git repo exists in this project (verified), so no
worktree/executor/atomic-commit step applies — this is a direct docs-only
change at hub + project level.
