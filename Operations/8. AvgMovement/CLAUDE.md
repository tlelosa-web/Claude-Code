# CLAUDE.md — Item Movement / AvgMovement Automation

> ⚠️ **RETIRED 2026-07-17 — superseded by SOPS.** See hub
> `docs/decisions/ADR-006-avgmovement-retired-superseded-by-sops.md` at
> `C:\Users\tlelo\Desktop\Operations\docs\decisions\`. Every calculation this pipeline
> performs (Supplier, Lead Time, AMU, Min/Max reorder suggestions) now has
> a live equivalent in `2. SOPS` (Batches 32 and 33 — see that project's
> `docs/todo.md`), sourced from the same Sage exports but imported directly
> into SOPS's own Stock Report and Item detail pages instead of a separate
> hand-run Excel pipeline. **Don't run `RUN_PIPELINE.bat` going forward** —
> use SOPS's Import CSV / Import Supplier-Lead-Time / Import Movement
> History buttons instead. Nothing in this folder has been deleted or
> moved; it's left in place as-is per the ADR, not cleaned up.
>
> Everything below this notice describes the pipeline as it was built and
> onboarded — kept for reference, not as an active runbook.

> Lightweight DCOE onboarding — see hub `docs/decisions/ADR-003-pipeline-
> project-dcoe-convention.md` at `C:\Users\tlelo\Desktop\Operations\docs\decisions\` for why
> this project doesn't have a full `docs/specs/`+`docs/todo.md` scaffold.
> Loaded when Claude Code opens in this folder. Shared cross-project policy
> (model routing, agent roster, hard rules) is governed by the root hub
> `CLAUDE.md` at `C:\Users\tlelo\Desktop\Operations\CLAUDE.md` — read it too, don't assume
> it's duplicated here.

```
Owner:      Tebello Lelosa
Company:    Fan Movement (Pty) Ltd
Type:       Python pipeline (Sage ERP exports → item movement / stock reports)
```

## What this is

Automates item movement reporting and analysis. `RUN_PIPELINE.bat` runs the
scripts in `4_Scripts/`, reading Sage exports plus a manually-maintained
current-stock workbook, and produces two Excel reports into
`3_Live_Reports/`: `Item Movement [date].xlsx` (summary + order-summary
tabs) and `Item Movement By Cat [date].xlsx` (one tab per category).

Full run instructions, input/output file specs, and troubleshooting live in
[`1_Documentation/USER_GUIDE.md`](1_Documentation/USER_GUIDE.md) — that's
the file to read for "how do I run this" and "what does script X do."

**Note (unlike `1. Daily Sales Order Files`):** `USER_GUIDE.md` here does
*not* have an actively-maintained execution log or fix history — no script
auto-appends to it. There's no equivalent canonical history file for this
project yet. If ongoing history-tracking is ever wanted, that's a separate
decision (would mean adding logging to a script, a code change) — not
assumed by this onboarding.

## Legacy `1_Documentation/AGENT.md` — superseded, left in place

This project has a pre-existing `AGENT.md` (a generic "Directive →
Orchestration → Execution" template, not project-specific content — its own
execution-log and memory-buffer sections are still unfilled placeholders,
and it names a log file, `5_Archive_and_Debug/debug_log.txt`, that doesn't
actually exist; the real log there is `debug_output_utf8.txt`, per
`USER_GUIDE.md`). It appears to be unused boilerplate rather than a living
process, possibly read by another AI tool (a `.qwen/` config also exists in
this folder). **Claude Code does not read `AGENT.md`** — this `CLAUDE.md`
is authoritative for Claude Code sessions here. `AGENT.md` was left
untouched rather than deleted or merged — that's a separate decision to
make deliberately if it ever comes up, not a side effect of this onboarding.

## Folder layout — load-bearing, do not rename

```
1_Documentation/    ← USER_GUIDE.md (run guide), AGENT.md (legacy, superseded)
2_Source_Data/       ← Sage CSV exports + ImportStockFinal.xlsx (inputs)
3_Live_Reports/       ← Excel outputs — PRODUCTION DATA, see hard rule below
4_Scripts/            ← automation scripts, run via RUN_PIPELINE.bat
5_Archive_and_Debug/  ← archived reports, debug_output_utf8.txt, scratch
```

These five folder names are hardcoded into the scripts. Do not rename,
move, or restructure them without also updating the scripts that reference
them — that's a code change, not a docs change.

## Hard rules specific to this project

1. **`3_Live_Reports/*.xlsx` are production data** — per hub `CLAUDE.md`
   hard rule 4, ask before deleting or moving any live report file.
2. **`2_Source_Data/ImportStockFinal.xlsx` is manually maintained** —
   Current Stock values are hand-updated by a human in the
   `ImportStockCount_TOT` sheet before each run (see `USER_GUIDE.md`). Don't
   overwrite or regenerate this file programmatically without asking.
3. **Don't delete or merge `1_Documentation/AGENT.md`** as a side effect of
   unrelated work — its disposition (keep/retire/archive) hasn't been
   decided; see note above.
4. **No `docs/todo.md` or `docs/session-log.md` here** — per ADR-003. If a
   genuinely new feature/redesign task ever lands here (not a routine fix),
   a one-off `docs/specs/<date>-<task>.md` may be created for that task
   alone — don't stand up a permanent `docs/` scaffold for it.
