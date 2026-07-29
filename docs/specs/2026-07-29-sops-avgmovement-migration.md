# Spec — SOPS: run the AvgMovement migration (pending go-ahead)

**Machine:** Operations only (`C:\Dev\Operations\2. SOPS`).
**Todo item:** `docs/todo.md` "SOPS: give the go-ahead to run the
AvgMovement migration"
**Size:** small execution, high blast-radius (live DB) — gated.

## Status: NOT cleared to run yet

This is prepared so the moment Tebello gives the go-ahead **in a session on
this machine**, there's nothing left to figure out — but do not run the
migration speculatively. SOPS's standing schema-change convention (see
`knowledge/sops.md`) holds every migration for Tebello's explicit go-ahead
before touching `instance/sops.db`. Confirm the go-ahead was actually given
in this session before proceeding — a stale todo.md checkbox is not
sufficient confirmation on its own.

## Background

Batch 32/33 (commits `fe06eaa` + `112e321`) ported AvgMovement's
Supplier/Lead-Time and AMU/suggested-Min-Max reorder logic into SOPS as new
`Item` fields. Fully tested: a dry run against real data updated 1,219
items with zero exceptions. The migration scripts exist and are ready —
they have simply never been run against the live database.

## Steps (once go-ahead is confirmed this session)

1. `git status` on the SOPS working tree — confirm clean, no other
   session's in-progress work present (see the concurrent-session
   contamination gotcha in `knowledge/sops.md`).
2. Take a backup of `instance/sops.db` before running anything against it.
3. Run the Batch 32/33 migration scripts (locate via `git log` /
   `docs/todo.md` for the exact script path — not reproduced here since
   it's SOPS-repo-internal detail).
4. Run SOPS's full test suite after migrating — confirm still green.
5. Spot-check a handful of migrated `Item` rows' new Supplier/Lead-Time and
   AMU/Min-Max fields against the known-good dry-run output.

## Definition of done

- Migration run against live `instance/sops.db`, test suite green,
  spot-check confirms correct values. This is the blocking step before
  `8. AvgMovement` (already Retired) can be formally decommissioned.

## Hub bookkeeping (after the migration)

- Pull `origin/main` on this hub repo first (Hard Rule 6).
- Update `knowledge/sops.md`'s outstanding-items entry to mark this done.
- Remove this item from `docs/todo.md`, renumber remaining items, add a
  `docs/session-log.md` entry. Note whether `8. AvgMovement` decommission
  is now unblocked.
