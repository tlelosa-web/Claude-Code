# Operations Status Report — 2026-07-17

**Author:** Claude (hub session) | **Scope:** All active Fan Movement (Pty) Ltd projects under `C:\Dev\Operations`

## Executive Summary

Hub-level DCOE rollout is complete and nothing is queued at root. Of the four onboarded
projects, SOPS is by far the most active (30 batches shipped, currently on Batch 30) and
in good shape, but has a 3-day-old live-data review sitting unactioned (Batch 24 payment
status). Delivery Note and Nameplate are both quiet since their last shipped feature —
Nameplate has uncommitted changes sitting in its working tree that need a decision. The
two unattended pipeline automations diverge sharply: Daily Sales Order ran successfully
again this morning, but AvgMovement hasn't produced a new report in over two months and
is worth checking.

## Status Legend

🟢 On track — no action needed | 🟡 Needs a decision or check-in | 🔴 Stalled / at risk

## Project Status

| Project | Status | Target Goal | Current State |
|---|---|---|---|
| **2. SOPS** | 🟡 | Production & stores-pack system covering the full Sales Order → Works/Stock Order → Reports lifecycle, now extended with Purchase Orders, demand-netted shortfalls, picking, and a Settings/currency module | Batch 30 shipped 2026-07-16 (216 tests green). Extremely active — 30 batches since late May. No feature work queued; **open item:** 19 of 22 Sales Orders from the Batch 24 payment-status migration still carry auto-guessed values, unreviewed since 2026-07-14 (Tebello deferred it twice) |
| **7. DELIVERY NOTE** | 🟡 | Delivery-note register app (Next.js/Prisma) — currently just create + list | MVP shipped and DCOE-onboarded 2026-07-15; no activity since. No test suite, no edit/delete, no PDF export — none started, none prioritized |
| **3. Nameplate & Test Sheet** | 🟡 | Motor Nameplate + Test Record Sheet PDF generator | Hidden (no-terminal) launcher shipped 2026-07-16. **Working tree currently dirty**: 6 modified files (`main.py`, `excel_source.py`, `doc_history.json`, docs) + 1 untracked script (`test_api_fixes.py`), uncommitted. Includes a stray unrelated `/api/speed` endpoint that's sat uncommitted across multiple sessions with no decision on keep-or-discard |
| **1. Daily Sales Order Files** | 🟢 | Daily Sage ERP → Sales Order Excel report automation | Running as expected — last successful run this morning, 2026-07-17 08:09. No open issues |
| **8. AvgMovement** | 🔴 | Item movement / stock report automation (same pattern as Daily Sales Order) | **No new report since 2026-05-13** (`3_Live_Reports/` — over 2 months stale) despite the project being described as an active pipeline. Worth confirming whether this is still being run manually, was deprioritized, or has silently broken |
| **Inventory Management & Reports** | ⚪ N/A | — | Deliberately excluded from active-project tracking (ADR-004) — kept only as a reference resource for SOPS/other projects, not run standalone |
| **Root hub** | 🟢 | Cross-project DCOE governance + shared pattern library | Rollout complete (4/4 in-scope projects onboarded). No hub-level task queued |

*Data-only folders with no code or active work (Casing Analysis, Sage Inventory Report, Stock Report Reference, Workshop Stock, FM Planning & Stock Control, General - Info) are omitted from this table — nothing to report status on.*

## Decisions Needed

| Decision | Context | Recommended Action |
|---|---|---|
| SOPS Batch 24 payment-status review | 19/22 SOs still on the migration's best-guess mapping, deferred twice already | Set aside 15–20 min to review the list in `2. SOPS/docs/todo.md` (Ops — Payment Status Data Migration Run entry) and correct any wrong guesses on the SO detail page |
| Nameplate uncommitted changes | 6 modified files + 1 untracked script sitting in the working tree, unclear which are intentional | Next session in that project: review `git diff`, decide what to commit vs. discard, and finally resolve the long-standing stray `/api/speed` endpoint (keep & finish, or delete) |
| AvgMovement staleness | No report generated since 2026-05-13 | Confirm with whoever normally triggers `RUN_PIPELINE.bat` whether this pipeline is still in use |
| Delivery Note next features | Edit/delete + PDF export not started, no spec | Decide if/when this becomes a priority; needs a spec before any build work per DCOE rules |

## Other Things Worth Looking At

- **Recurring stale-dev-server issue in SOPS** — flagged 5 separate times in `2. SOPS/docs/session-log.md`/`todo.md` (Batches 12, 20, 27, 28, 30) where a leftover Werkzeug process kept serving pre-fix code. Never fixed at the root — worth a one-time addition (a pre-launch port check in `launch.bat`/`launch.ps1`) rather than continuing to catch it manually each time.
- **Hub backlog items still open:** periodic recheck that OneDrive hasn't recreated an `Operations` folder at the old Desktop path; decide the fate of the `General - Info/` folder (currently just images).
- **SOPS `.git` history of OneDrive lock corruption** — resolved at the hub level (moved off OneDrive), but SOPS's own repo previously lived through several lock-corruption incidents; worth a periodic `git fsck` given that history, even though the root cause is gone.

## Next Period Priorities (suggested)

1. Tebello reviews the SOPS Batch 24 payment-status list (data-correctness, not code).
2. Resolve Nameplate's dirty working tree (commit or discard, including the `/api/speed` stray endpoint).
3. Confirm AvgMovement is intentionally idle or needs a run.
4. Decide whether Delivery Note's edit/delete/PDF-export backlog gets picked up next, or stays parked.

---

*Generated by reading each project's `docs/todo.md`/`docs/session-log.md` (or `USER_GUIDE.md` execution log for lightweight pipeline projects), plus `git log`/`git status` and live report file timestamps where relevant. See `docs/patterns.md` § 9 for how to regenerate this on demand.*
