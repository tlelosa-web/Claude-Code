# SOPS

Flask/SQLAlchemy sales-order & works-order system for Fan Movement (Pty)
Ltd. Local-only git repo (`C:\Dev\Operations\2. SOPS`, no remote configured)
— currently the most DCOE-mature project (own `CLAUDE.md` v3.2, full
`docs/` scaffold, TDD test suite).

## 2026-07-28 — Stack, workflow, and testing facts
**Source:** SOPS `CLAUDE.md` / `README.md`
**Status:** active

- **Stack:** Flask + SQLAlchemy + SQLite (`instance/sops.db`), server-rendered
  templates (Jinja) + Tabulator.js for interactive tables, offline-first (no
  CDN dependencies — everything vendored, verified by grepping touched files
  for `cdn.`/`fonts.googleapis` before every commit).
- **TDD discipline:** every batch runs the full test suite before and after
  (suite size grows with each batch — was 216, now 230+ as of the last
  reviewed batch). Schema migrations are written but deliberately **not run**
  against `instance/sops.db` automatically — every schema change is held for
  Tebello's explicit go-ahead before touching the live DB, a standing
  convention across all batches, not a one-off.
- **Recurring gotcha — stale dev server:** the Flask dev server does not
  reload on route/model (`.py`) changes the same way it hot-reloads
  templates; a process restart is required or new/changed routes 404. This
  has recurred across many batches (documented recurring class of issue in
  SOPS's own todo.md). Always ask before restarting a dev server the current
  session didn't start.
- **git-worktree avoidance:** SOPS deliberately avoids git worktrees for
  parallel Executor work because of a documented history of OneDrive
  corrupting `.git` internals when the repo lived in an OneDrive-synced path
  (same root cause as `operations-hub.md`'s OneDrive+git finding — SOPS was
  the original project that surfaced it). The repo has since been relocated
  outside OneDrive sync (see `operations-hub.md`), so this may be worth
  revisiting, but hasn't been re-decided as of this entry.
- **Concurrent-session git contamination (proven anti-pattern):** when
  multiple Claude Code sessions work the same SOPS working tree at once, a
  broad `git add -A`/`.` in one session sweeps up another session's
  uncommitted in-progress files. Observed concretely 2026-07-23: one
  session's FM/Job-No. edit feature got split across two commits (`dca9ee4`
  + `229e346`) by another session's simultaneous commit. Mitigation: stage
  surgically (`git add <explicit paths>` or `git add -p`) whenever another
  session might be active in the same tree; never `git add -A`/`.` under
  those conditions.
- **PRODUCTION vs RECEIPT stock-movement distinction:** SOPS's stock-movement
  model deliberately separates internal production movements from external
  receipt movements as two distinct concepts rather than one generic
  "movement" type — a reusable domain-modeling pattern if another project
  ever needs similar inventory-movement tracking.
- **Design pattern — avoid duplicate computation across features:** when
  porting AvgMovement's Supplier/Lead-Time and AMU/Min-Max logic into SOPS
  (see below), on-order quantity was explicitly *not* re-imported from the
  Sage CSV because SOPS already computes `qty_on_order` live from its own
  Purchase Orders (`services/demand.py`) — the batch was scoped specifically
  to avoid recreating a "two processes compute the same thing" problem.
  Worth applying as a general check before porting logic between projects:
  confirm the target doesn't already compute the same fact a different way.

## 2026-07-28 — Outstanding items (as of SOPS's own docs/todo.md)
**Source:** SOPS `docs/todo.md`
**Status:** active

- **AvgMovement→SOPS migration go-ahead (Batch 32/33, spec'd + built
  2026-07-17, commits `fe06eaa` + `112e321`):** ported AvgMovement's
  Supplier/Lead-Time and AMU/suggested-Min-Max reorder logic into SOPS as new
  `Item` fields, fully tested (real-data dry run: 1,219 items updated, zero
  exceptions) but **migration scripts have not been run against the live
  `instance/sops.db`** — held for Tebello's go-ahead per SOPS's standing
  schema-change convention. This is the blocking step before `8. AvgMovement`
  (already marked Retired in the Operations hub's project index) can be
  formally decommissioned.
- **Payment Status data-migration review:** a batch of historical Sales
  Orders had payment-status values migrated/backfilled and flagged for human
  review before being treated as fully validated. Detail (specific SO
  numbers) stays in SOPS's own `docs/todo.md`/`docs/session-log.md`
  (2026-07-14 entry onward) per the no-company-data rule — not reproduced
  here.
- Full up-to-date detail for both items: see SOPS's own
  `C:\Dev\Operations\2. SOPS\docs\todo.md`.

Note: SOPS's own todo.md line ~875 (dated 2026-07-23) says the PO-edit/
upload-catalogue-picker work was "not yet committed" — this is now stale;
verified 2026-07-28 that it shipped as commit `46c9acb` (2026-07-24) and the
working tree is clean. Not carried forward as an outstanding item.
