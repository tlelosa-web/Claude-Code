# Spec — SOPS: Payment Status data-migration review

**Machine:** Operations only (`C:\Dev\Operations\2. SOPS`).
**Todo item:** `docs/todo.md` "SOPS: Payment Status data-migration review"
**Size:** human review — Claude assists, Tebello decides.

## Goal

A batch of historical Sales Orders had payment-status values
migrated/backfilled and flagged for human review before being treated as
fully validated. Detail (specific SO numbers) intentionally isn't
reproduced in this hub's knowledge cache — per the no-company-data rule,
it stays in SOPS's own `docs/todo.md`/`docs/session-log.md` (2026-07-14
entry onward).

## Steps

1. Open SOPS's own `docs/todo.md` and `docs/session-log.md`, locate the
   2026-07-14 entry onward covering the Payment Status backfill.
2. Pull the list of flagged Sales Orders and their migrated/backfilled
   payment-status values.
3. Present them to Tebello in a reviewable format (table: SO number, old
   status, backfilled status, confidence/reasoning if recorded) — this is
   a judgment call for Tebello, not something to auto-approve.
4. Record Tebello's decisions (confirmed correct / needs correction) back
   into SOPS's own todo.md, and apply any corrections he flags.

## Definition of done

- Every flagged SO has an explicit human decision recorded — not just
  "reviewed," but confirmed-correct or corrected, with the correction
  applied if needed.

## Hub bookkeeping (after the review)

- Pull `origin/main` on this hub repo first (Hard Rule 6).
- Update `knowledge/sops.md`'s outstanding-items entry to mark this done
  (structurally — "reviewed, N corrections applied" — no SO-level detail
  per the no-company-data rule).
- Remove this item from `docs/todo.md`, renumber remaining items, add a
  `docs/session-log.md` entry.
