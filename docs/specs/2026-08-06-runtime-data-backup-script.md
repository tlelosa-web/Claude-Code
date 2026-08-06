# Spec — repeatable runtime-data backup script

**Date:** 2026-08-06
**Status:** Implemented
**Owner:** Tebello Lelosa

## Problem

The 2026-08-06 backup of the vaults' gitignored runtime data (see
`knowledge/operations-hub.md`) worked, but it was a one-off script run by hand
from a scratch directory and then discarded. Three consequences:

1. **It has to be re-derived every time.** The procedure is documented, but
   documentation is not execution — someone still has to rewrite ~150 lines.
2. **The file list was hardcoded.** A new project, a new `.env`, or a new
   SQLite database would silently not be backed up, and nothing would say so.
3. **Nothing re-runs it.** `sops.db` changes daily in normal use, so a
   point-in-time snapshot ages immediately.

## Decision

Commit a single script at **`scripts/backup-runtime-data.py`** in this hub.

**Why the hub and not `Operations/`:** it backs up *both* `Desktop/Operations`
and `Desktop/Pappa T`. Cross-project work is what this hub governs under
`CLAUDE.md`'s hub-and-spoke rule; putting it inside one vault would make it
that vault's concern and leave the other's backup owned by nothing. It also
means the script is itself version-controlled and pushed — the one-off was not.

**Discovery over hardcoding.** The script walks both vault roots and classifies
by filename pattern, pruning regenerable trees (`node_modules`, `.venv`,
`__pycache__`, `.next`, `.ruff_cache`, `.pytest_cache`, `.git`, `egg-info`).
Two classes:

- `DATA` — `*.db`, `*.sqlite*`, plus `.claude/agent-memory/` trees
- `SECRET` — `.env`, `.env.*`, `credentials*.json`, `token*.json`, `*.pem`

`*.example` files are excluded from `SECRET` (they are templates and are
already in git). Zero-byte databases are skipped and reported, not backed up.

A third class was added during implementation:

- `SNAPSHOT` — `*.db.*`, `*.sqlite.*` — dated safety copies sitting beside a
  live database, e.g. `sops.db.pre-batch34-backup-20260718-184741`. These do
  **not** match `*.db`, so the first draft silently dropped all seven of SOPS's
  rollback points, which the hand-run version had captured. Caught by comparing
  the run against the earlier one. They are copied as plain files rather than
  through the sqlite backup API — they are static, so there is no torn-read
  risk to protect against.

`.claude/worktrees/` is also pruned. Those are live git worktrees — separate
checkouts of a repo already covered — and descending into them duplicated every
match two and three times (one `.pfx` was found three times before the fix).

**The data/secret split is enforced, not just intended.** Data goes to a local
folder *and* OneDrive; secrets go to a separate local-only folder. The script
asserts that no `SECRET`-classified path is ever written under the synced root,
and fails loudly if that invariant breaks. This is the one property whose
violation is silent and serious — plaintext OAuth tokens reaching a cloud-
synced folder — so it gets a hard check rather than careful coding.

**Verification is part of the backup, not a follow-up.** Each database is
copied with Python's `sqlite3` backup API (not a file copy — a raw copy of a
live database can capture a torn state), then `PRAGMA integrity_check`, then a
per-table row-count comparison against the source. A backup that fails any of
these is reported and sets a non-zero exit code.

**Drift reporting.** Each run compares its discovered file list against the
previous run's manifest and reports files that are new or have disappeared.
This is what stops problem 2 above from recurring silently.

**Retention.** Keeps the most recent `--keep N` runs (default 7) in each
destination and prunes older ones. Bounded growth without manual cleanup.

## Not in scope

- **Registering a scheduled task.** The script supports unattended use
  (`--quiet`, meaningful exit codes) but does not install itself. Changing
  system scheduler config is Tebello's call, not a side effect of committing a
  script.
- **Encryption of the secrets backup.** Out of scope here: it needs a password
  or key, which is Tebello's to hold. The mitigation for now is that the
  secrets copy is local-only and never synced.
- **Off-site beyond OneDrive.** An external drive or second cloud target is a
  separate decision.

## Consequences

- Backups become a one-command operation, and the command is in git.
- New projects are picked up automatically; new *categories* of runtime state
  (say, a Redis dump) would still need a pattern added — the drift report makes
  that visible rather than silent, but does not fix it. The `SNAPSHOT` gap above
  is exactly this failure mode, and it is worth noting it was caught by
  comparing against a known-good previous run, not by reading the code.
- Discovery immediately found three things the hand-written list had missed: a
  `TebelloLelosa.pfx` certificate, and agent-memory trees under `Operations/`
  and `Operations/2. SOPS/`. That is the case for discovery over hardcoding,
  made concretely.
- The secrets copy remains unencrypted on local disk. That is a deliberate,
  documented tradeoff, not an oversight.

## References

- `knowledge/operations-hub.md` — inventory, procedure, and the sqlite-backup-API
  rationale this script implements
- `docs/session-log.md`, 2026-08-06 "Live runtime data backed up" — the one-off
  run this replaces
