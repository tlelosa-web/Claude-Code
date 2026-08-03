# CLAUDE.md — Daily Sales Order Automation

> Lightweight DCOE onboarding — see hub `docs/decisions/ADR-003-pipeline-
> project-dcoe-convention.md` at `C:\Users\tlelo\Desktop\Operations\docs\decisions\` for why
> this project doesn't have a full `docs/specs/`+`docs/todo.md` scaffold.
> Loaded when Claude Code opens in this folder. Shared cross-project policy
> (model routing, agent roster, hard rules) is governed by the root hub
> `CLAUDE.md` at `C:\Users\tlelo\Desktop\Operations\CLAUDE.md` — read it too, don't assume
> it's duplicated here.

**At the start of every session, read
`~/.claude/plugins/marketplaces/tlelosa-claude-config/dcoe-roster/CORE.md`
and treat its contents as part of this project's operating instructions** —
it carries the shared DCOE architecture, sub-agent roster, model routing,
and universal hard rules (ADR-007, opted in 2026-07-20). `@import` can't
reach that path, so this is a plain read instruction — follow it explicitly
each session.

```
Owner:      Tebello Lelosa
Company:    Fan Movement (Pty) Ltd
Type:       Python pipeline (Sage ERP exports → Sales Order Excel report)
```

## What this is

Daily automation that rebuilds the Sales Order Excel report from SAGE ERP
CSV exports plus a Contract Register workbook. Five scripts run in sequence
(`RUN_DAILY_PIPELINE.bat`): extract Released-Jobs PDF payment-status
comments → rebuild the daily tab from CSVs + Contract Register → re-inject
validated payment statuses into column J → format/highlight the report →
rebuild the Monthly Invoice tab. Runs roughly once per weekday, ad hoc (no
scheduler — run manually).

Full run instructions, requirements, troubleshooting, fix history, and the
execution log all live in
[`1_Documentation/USER_GUIDE.md`](1_Documentation/USER_GUIDE.md) — that file
is canonical for this project's history. This `CLAUDE.md` does not
duplicate it.

## Folder layout — load-bearing, do not rename

```
1_Documentation/    ← USER_GUIDE.md: run instructions, fix history, execution log
2_Source_Data/       ← SAGE CSV exports (inputs)
3_Live_Reports/       ← Excel outputs — PRODUCTION DATA, see hard rule below
4_Scripts/            ← automation scripts, run via RUN_DAILY_PIPELINE.bat
5_Archive_and_Debug/  ← old tools, logs, scratch
```

These five folder names are hardcoded into the scripts (e.g.
`run_daily_update.py` writes execution-log entries directly into
`1_Documentation/USER_GUIDE.md`; `extract_pdf_comments.py` writes into
`5_Archive_and_Debug/`). Do not rename, move, or restructure them without
also updating the scripts that reference them — this is a code change, not
a docs change.

## Hard rules specific to this project

1. **`3_Live_Reports/*.xlsx` are production data** — per hub `CLAUDE.md`
   hard rule 4, ask before deleting or moving any live report file.
2. **External dependency:** the pipeline reads from a OneDrive-hosted
   Contract Register workbook and a Released-Jobs PDF folder outside this
   project tree (paths documented in `USER_GUIDE.md`). Don't assume those
   paths are stable without checking `USER_GUIDE.md` first — they're
   colleague-owned folders, not ours to restructure.
3. **Don't change `run_daily_update.py`'s auto-append-to-`USER_GUIDE.md`
   behavior as a side effect of unrelated work** — it's the project's
   history mechanism (see ADR-003). Changing it is a deliberate decision on
   its own.
4. **No `docs/todo.md` or `docs/session-log.md` here** — use
   `USER_GUIDE.md`'s Execution Log / Fix History sections instead (see
   ADR-003). If a genuinely new feature/redesign task ever lands here (not
   a routine fix), a one-off `docs/specs/<date>-<task>.md` may be created
   for that task alone — don't stand up a permanent `docs/` scaffold for it.
