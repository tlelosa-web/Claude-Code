# Cross-Project Status Report — 2026-07-31

> Generated per `docs/patterns.md` § 9 (Cross-project status report). Rollup
> only — each project's own detail lives in its own `docs/todo.md` (or
> execution log, for lightweight pipeline projects).

## Summary table

| Project | Status | Target goal | Current state |
|---|---|---|---|
| `2. SOPS` | 🟡 | Flask sales/works/stock/purchase-order system, live prod | Clean tree, last commit today (`5e1e06d`). Batch 24 payment-status spot-check done (read-only); one live-data inconsistency found (SO4722) awaiting Tebello's manual review. Batch 32/33 migration + real-data import awaiting go-ahead. |
| `7. DELIVERY NOTE/delivery-note-system` | 🟢 | Next.js delivery-note register/edit/delete/PDF-export app | Clean tree, last commit 2026-07-21 (10 days idle — feature work finished, nothing broken). No automated tests; `dev.db` seed/reset policy still undecided (not urgent). |
| `3. Nameplate & Test Sheet` | 🟢 | FastAPI+React nameplate/test-sheet PDF generator | Clean tree, last commit today (`7db288e`). Connection-override fix plan (all 3 steps) fully closed as of today. Only open item: keep-vs-remove decision on an orphaned API endpoint. |
| `1. Daily Sales Order Files` | 🟢 | Sage ERP → daily Sales Order Excel report pipeline | Last successful run 2026-07-30 15:19, output file matches. No open bugs — one documented-by-design limitation (blank payment-status column in edge cases). |
| `8. AvgMovement` | 🔴 Retired | Inventory movement reporting | Superseded by SOPS Batches 32/33 (ADR-006, 2026-07-17). Folder untouched, not an active runbook — no further status tracking. |
| `Inventory Management & Reports` | ⚪ Excluded | Extract → build → report pipeline | Deliberately excluded from DCOE rollout (ADR-004) — reference resource for other projects, not tracked here. |

## Decisions needed

1. **SOPS — SO4722 data inconsistency**: "Cash Sale - Partial" with `amount_paid=0.0` on an already-Closed order (R19,521.25 total) — looks like a leftover best-guess from the original migration. Needs Tebello's manual correction call on the SO detail page. 18 of the other 19 flagged SOs need routine confirmation, no other anomalies found.
2. **SOPS — Batch 32/33 migration + real-data import**: awaiting authorization to proceed.
3. **Nameplate — orphaned endpoint**: `POST /api/reports/test-record-sheet` (unused duplicate payload contract, `main.py` lines 381–438) — keep or remove.
4. **DELIVERY NOTE — `dev.db` seed/reset policy**: whether it should be a documented workflow or stay pure local scratch. Not urgent, just undecided.
5. **Hub — Pappa T / `Claude-Code` hub machine plugin pull**: `dcoe-roster` plugin update (`agents/` folder stripped upstream 2026-07-29) still needs pulling on those two machines. Cosmetic, not urgent.

## Other things worth looking at

- **DELIVERY NOTE session-log gap**: last `session-log.md` entry is 2026-07-15, but real feature work (Edit/Delete/PDF export) shipped 2026-07-17/18 per `todo.md`. `session-log.md` for that project may need a backfill entry.
- **SOPS session-log gap**: previously noted several batches behind `todo.md` (Batches 27–30 not backfilled) — same pattern as above, worth a backfill pass if session-log accuracy matters for that project.
- **No automated test suite** flagged as a gap in two projects independently: DELIVERY NOTE (no tests at all yet) and Nameplate (`tests/` only has ad-hoc manual-check scripts). Neither is urgent standalone, but if either project's scope grows (DELIVERY NOTE mentioned "before auth" as the trigger), worth planning for.
- **Hub**: OneDrive junction periodic sanity check re-verified clean today (third pass same day, per `docs/todo.md`) — no action needed, standing check stays open by design.

---
*Process and update cadence: on request only (see `docs/patterns.md` § 9), not scheduled.*
