# Operations Status Report — 2026-07-18

**Author:** Claude (hub session) | **Scope:** All active Fan Movement (Pty) Ltd projects under `C:\Dev\Operations`, plus hub-level (non-project) work

## Executive Summary

Biggest hub-level event since the last report (2026-07-17): the ADR-007 shared-core `CLAUDE.md` distribution mechanism (a plain read-instruction pointing every opted-in project at a shared `CORE.md`, after `@import` was proven not to resolve absolute paths) is now **verified end-to-end** — this session was the fresh session that confirmed it. Per-project opt-in hasn't started yet. On the project side: SOPS has a substantial Batch 34 spec (Sales Order Report Excel export + a reworked status model) waiting on your review before it's built; Nameplate has one new backend bug found but not yet fixed; Delivery Note and Daily Sales Order Files are quiet and healthy; AvgMovement is formally retired (ADR-006) but the hub's own `todo.md` still carries a stale "revisit retirement" item that should be removed.

## Status Legend

🟢 On track — no action needed | 🟡 Needs a decision or check-in | 🔴 Stalled / at risk | ⚫ Retired

## Project Status

| Project | Status | Target Goal | Current State |
|---|---|---|---|
| **Root hub (non-project)** | 🟡 | Cross-project DCOE governance + shared pattern library | ADR-007 read-instruction mechanism **verified working** this session (`CORE.md` read successfully in a genuinely fresh session). Per-project opt-in not yet started for any of the 4 onboarded projects or Pappa T's machine. Session hygiene: 1 completed session archived, 1 renamed to reflect real content |
| **2. SOPS** | 🟡 | Production & stores-pack system, Sales Order → Works/Stock Order → Reports lifecycle | Batch 33 (AMU/Min-Max) shipped 2026-07-17. Batch 34 (native Sales Order Report Excel export + computed `report_status`/`on_hold` + event-driven Change Log — 24-step plan, schema change) **spec written and revised, not yet dispatched to an Executor** — waiting on your review of 2 open design questions. Batch 24 payment-status review (19/22 SOs on guessed values) is carried forward but you've already said to ignore it for now |
| **7. DELIVERY NOTE** | 🟢 | Delivery-note register app (Next.js/Prisma) | Edit/Delete/PDF export shipped 2026-07-17/18 (4 commits), verified end-to-end in-browser. No activity since, working tree clean. Still no automated test suite (not urgent, flagged in its own `todo.md`) |
| **3. Nameplate & Test Sheet** | 🟡 | Motor Nameplate + Test Record Sheet PDF generator | Prior dirty-working-tree issue (stray `/api/speed` endpoint) resolved 2026-07-17 — tree is clean now. **New bug found the same day, not yet fixed:** `/api/nameplate/from-excel` crashes (`datetime` not JSON-serializable) against the real workbook; a related sheet-name check bug (`"Table 1"` doesn't exist, endpoint only works by accident via a fallback branch) needs fixing alongside it |
| **1. Daily Sales Order Files** | 🟢 | Daily Sage ERP → Sales Order Excel report automation | Running as expected — last successful run 2026-07-17 08:09 (Fri). No run logged yet today (Sat 2026-07-18); consistent with a business-day-only automation, not flagged as an issue |
| **8. AvgMovement** | ⚫ | Item movement / stock report automation | **Formally retired** via ADR-006 (2026-07-17) — every calculation it performed (Supplier/Lead Time, AMU, Min/Max) now lives in SOPS Batches 32/33. Folder left untouched per that ADR. Hub `docs/todo.md` still has a "revisit retirement decision" item open that's now stale — see Decisions Needed |
| **Inventory Management & Reports** | ⚪ N/A | — | Deliberately excluded from active-project tracking (ADR-004) — reference resource only |

*Data-only folders (Casing Analysis, Sage Inventory Report, Stock Report Reference, Workshop Stock, FM Planning & Stock Control, General - Info) omitted — nothing to report status on.*

## Decisions Needed

| Decision | Context | Recommended Action |
|---|---|---|
| SOPS Batch 34 spec review | 2 open design questions block Executor dispatch: `Ready-Dispatch` "any complete" vs "all complete" semantic, and whether STO `Edit` should be allowed from the new `Released` status | Read `2. SOPS/docs/specs/sales-order-report-excel-export-2026-07-17.md` (Decision 1 for the semantics finding, "Not yet dispatched" note for both questions) and give a ruling on each |
| Nameplate `/api/nameplate/from-excel` bug | Crashes against the real workbook (`datetime` serialization) and only works today by accident (wrong sheet-name check falls through to a working fallback branch) | Next session in that project: fix both together — see `3. Nameplate & Test Sheet/docs/todo.md` "Next up" for full detail, including a same-day attempt that regressed and was discarded |
| Hub `docs/todo.md` stale entry | The "Revisit the `8. AvgMovement` retirement decision" item is already resolved — ADR-006 retired it 2026-07-17, and root `CLAUDE.md`'s project index already reflects that | Say the word and I'll remove the stale item from `docs/todo.md` (small doc-only edit, not touching the AvgMovement folder itself) |
| ADR-007 per-project opt-in order | Mechanism now verified; SOPS, DELIVERY NOTE, Nameplate, the pipeline projects, and Pappa T's machine all still need their `CLAUDE.md` updated with the read instruction | Pick whichever project you're next actually working in — opt-in happens then, not as a batch job (spec Step 4) |

## Other Things Worth Looking At

- **Hub backlog items still open** (unchanged since 2026-07-17): periodic recheck that OneDrive hasn't recreated an `Operations` folder at the old Desktop path; decide the fate of the `General - Info/` folder (currently just images).
- **SOPS working tree has 2 uncommitted changes** (`docs/todo.md` modified, `docs/specs/sales-order-report-excel-export-2026-07-17.md` untracked) — expected in-progress state for the Batch 34 spec-review gate, not a concern on its own.
- Last report's "recurring stale-dev-server issue in SOPS" and "SOPS `.git` history" notes weren't re-verified this pass — flagging that they're carried over from 2026-07-17, not re-checked today.

## Next Period Priorities (suggested)

1. Review SOPS Batch 34's two open design questions so it can move to Executor.
2. Fix the Nameplate `from-excel` bug (datetime serialization + sheet-name check).
3. Confirm removal of the stale AvgMovement item from hub `docs/todo.md`.
4. Pick the first project for ADR-007 opt-in when you're next working in one.

---

*Generated by reading each project's `docs/todo.md` (or `USER_GUIDE.md` execution log for the pipeline project), plus `git log`/`git status` and live-report file timestamps where relevant. Includes hub-level (non-project) execution per this run's request. See `docs/patterns.md` § 9 for how to regenerate this on demand.*
