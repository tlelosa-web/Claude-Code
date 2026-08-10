# Spec — repeatable runtime-data backup script

**Date:** 2026-08-06
**Status:** Implemented; **scope narrowed 2026-08-09** — see the amendment at the foot
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

## 2026-08-09 — Amendment: Operations dropped from scope, and a second leak found

**Why.** The Fan Movement (Pty) Ltd contract was terminated on 2026-08-03. This script
was copying that company's production `sops.db` into OneDrive on a daily schedule. The
task was disabled the same day as a stop-gap; this amendment is the actual fix, so the
task could be re-enabled for Pappa T's own databases rather than left off.

**Change.** `VAULTS` is now Pappa T only. `Desktop/Operations` moved to a new
`EXCLUDED_VAULTS` constant rather than being deleted from the list, because the
failure mode here is a *future* session reading a Pappa-T-only backup as a bug and
helpfully restoring the second entry. The constant carries the reason, the date, and an
explicit "do not add this back". Three supporting changes:

- **A run-time invariant, exit code 3.** `excluded_leaks()` resolves every discovered
  path and fails the run — writing nothing — if any of them lands inside an excluded
  vault. This is not a restatement of `VAULTS`: a junction or symlink under a scanned
  vault can point into an excluded one and the walk would follow it without ever
  naming it. `.claude/worktrees/` already proved that class of surprise is real here
  (one `.pfx` discovered three times through separate checkouts, 2026-08-06).
- **Drift output labels expected removals.** A `GONE` line normally means a file
  vanished and may need investigating. Every Operations path is now permanently gone
  by design, so they are tagged `(expected: vault excluded from this backup)` —
  otherwise the first run after the change reads like data loss, and every run after
  that reads like an unexplained mystery.
- **The prose was corrected, not just the code.** The docstring, the generated
  `MANIFEST.md` and the secrets `README.md` all claimed the backup covered
  "Operations and Pappa T". Left alone, every future run would have shipped a manifest
  asserting coverage it no longer had.

**A second, worse leak the dry run exposed — unrelated to Fan Movement.** With
Operations gone, five *new* databases appeared in the discovery set, all under
`Pappa T/TebelloReborn/.session/chrome-profile/`. That is the hand-signed-in Chrome
profile built for Phase E: **857 files, 133.8 MB, including `Login Data` and
`Network/Cookies`.** Its Chromium-internal `*.db` files were being copied into the
**OneDrive-synced** tree — a live authenticated session leaving the machine on a daily
schedule.

The credential stores themselves escaped only because Chrome names them `Login Data`
and `Cookies`, with no extension, so `DATA_PATTERNS` never matched them. **That is
luck, not design** — widen the patterns or let Chrome rename a file and real
credentials sync to a cloud provider. `.session` and `chrome-profile` are now pruned
outright. A browser profile is regenerable and re-signable; it is never worth backing
up, and it is exactly the kind of thing the script's own data/secret split exists to
keep out of the synced tree.

Worth noting how it surfaced: not by reading the code, but because narrowing one scope
changed what the *other* scope discovered. The dry run was the only thing that showed
it, and it had been true — and unnoticed — since the profile was created on 2026-08-08.

**Verification.** Ten unit checks on `excluded_leaks()` and `should_prune()` (including
that a lookalike sibling path like `Operations-archive` is *not* flagged, i.e. parent
containment rather than string prefix), then a dry run, then a real run: exit 0, 5
databases backed up and verified, 1 snapshot, 6 secrets local-only, 2 agent-memory
trees. The new synced run was then checked directly: **0 files matching Operations, 0
matching the Chrome profile, 0 secret-classified files.** Retention untouched at 6 runs
of 7 — the earlier runs still hold Fan Movement data and were deliberately not pruned,
since retention is a contract question tracked in `docs/todo.md`.

**Not covered by this amendment:** the Fan Movement data already sitting in the five
pre-existing backup runs, locally and in OneDrive. Stopping new copies and removing old
ones are separate decisions; only the first was taken.

## Codex second opinion (advisory) — 2026-08-09

The spec is directionally sound: it identifies real prior failures, narrows scope for a defensible reason, and adds hard checks around the worst leak class. I would not rubber-stamp it as complete, though. The remaining weak spots are mostly around trust boundaries, symlink behavior, retention semantics, and whether the acceptance criteria are precise enough to catch future leaks.

**Buried Assumptions**

1. The spec assumes “Pappa T only” is a sufficient scope boundary.

   The amendment says `VAULTS` is now Pappa T only and `Desktop/Operations` is excluded. But the Chrome-profile leak shows the real boundary is not vault membership; it is “what runtime state is safe to copy into a synced destination.” A file can be inside Pappa T and still be inappropriate for backup, especially browser profiles, auth caches, app state, local databases containing tokens, or third-party session stores.

2. It assumes filename patterns can safely classify sensitivity.

   The spec says:

   > `DATA` — `*.db`, `*.sqlite*`, plus `.claude/agent-memory/` trees  
   > `SECRET` — `.env`, `.env.*`, `credentials*.json`, `token*.json`, `*.pem`

   But the amendment itself disproves this model:

   > Chrome names them `Login Data` and `Cookies`, with no extension... That is luck, not design

   So the current design still relies heavily on negative pruning to compensate for incomplete sensitivity detection. That should be stated as a core limitation, not just as a discovered incident.

3. It assumes OneDrive is acceptable for all `DATA`.

   The spec treats `DATA` as safe to sync. That is not established. SQLite databases can contain user data, company data, auth artifacts, browser state, API responses, customer records, or embedded secrets. The `sops.db` incident shows that “database” does not mean “safe for cloud sync.”

4. It assumes local-only plaintext secrets are acceptable enough.

   This is documented as a tradeoff, but the threat model is unstated. Local-only still exposes secrets to malware, device theft, other local users, indexing tools, backup software, and accidental future sync. If encryption is out of scope, the spec should still define the accepted residual risk.

5. It assumes previous manifest comparison is enough drift detection.

   The spec says drift reporting prevents missed files from recurring silently. It only detects discovered files whose paths match the current discovery rules. It will not detect new categories that are pruned, files with unrecognized names, extensionless credential stores, or sensitive files that are misclassified as `DATA`.

6. It assumes scheduled execution exists or will exist separately.

   The problem says:

   > Nothing re-runs it.

   But “Registering a scheduled task” is out of scope. That is acceptable as a boundary, but then the spec does not fully solve problem 3. It creates an unattended-compatible script, not a repeatable scheduled backup system.

**Missing Or Untestable Acceptance Criteria**

1. “Fails loudly” needs exact behavior.

   The spec says:

   > The script asserts that no `SECRET`-classified path is ever written under the synced root, and fails loudly if that invariant breaks.

   Good intent, but acceptance criteria should specify:

   - exit code
   - whether partial outputs are deleted
   - whether manifests are written
   - whether local secret backups still proceed
   - exact summary wording or machine-readable signal

   The amendment does this better for excluded leaks with “exit code 3” and “writing nothing.” The same precision should apply to secret-sync violations.

2. “Writing nothing” needs definition.

   For excluded leaks:

   > fails the run — writing nothing

   Does that mean no destination directories are created, no manifest is updated, no logs are written, no retention pruning occurs, and no temp files remain? That matters because partial backup runs can confuse retention and drift state.

3. SQLite verification criteria are incomplete.

   The spec says:

   > `PRAGMA integrity_check`, then a per-table row-count comparison against the source.

   Missing criteria:

   - what happens if the source database changes between backup and row-count comparison
   - whether WAL/SHM mode is handled
   - whether attached databases are considered
   - whether views, virtual tables, FTS tables, triggers, indexes, and schema are compared
   - whether row-count mismatches are retryable or fatal

   Row counts are a weak consistency check. They catch some failures, not content corruption or wrong rows with same counts.

4. Retention acceptance criteria are underspecified.

   > Keeps the most recent `--keep N` runs

   Missing:

   - sorted by directory name, manifest timestamp, filesystem mtime, or successful-run marker?
   - does a failed run count?
   - are local data, OneDrive data, and secrets pruned independently?
   - can retention delete pre-amendment runs with Fan Movement data?
   - what happens if pruning fails after backup succeeds?

5. Drift reporting needs testable expectations.

   > reports files that are new or have disappeared

   Acceptance criteria should define:

   - where previous manifest is read from
   - behavior on first run
   - behavior after failed run
   - whether expected removals are persisted or repeated forever
   - whether path normalization/case sensitivity is stable on Windows
   - whether renamed files appear as `NEW` plus `GONE`

6. The post-amendment verification is not enough as future acceptance criteria.

   The spec reports:

   > 0 files matching Operations, 0 matching the Chrome profile, 0 secret-classified files

   That is useful, but too pattern-bound. It verifies known bad strings, not the broader safety property. A future credential cache under another name could pass.

**Failure Modes Not Considered**

1. Junctions and symlinks beyond excluded vaults.

   The amendment handles symlinks/junctions pointing into excluded vaults. But what about symlinks pointing outside both vaults into arbitrary sensitive locations, cloud folders, browser profiles, SSH directories, or system app data? The current invariant seems specifically about excluded vault containment, not “all resolved paths must remain inside allowed roots.”

   I would add a hard invariant: every copied source must resolve under an allowed vault root and outside all excluded/pruned roots.

2. Misclassified sensitive databases.

   The Chrome example is only one instance. Other examples:

   - app caches with auth sessions in SQLite
   - Electron app `Local Storage` databases
   - OAuth token stores in `.db`
   - password-manager extension data
   - browser-like profiles not named `chrome-profile`
   - `.sqlite` files containing production/client data

   The spec’s `DATA` class is too broad for synced backup unless there is a denylist plus an allowlist or per-project policy.

3. Plaintext local secret backup becoming synced later.

   The script enforces that `SECRET` paths are not written under the synced root. But if the configured local-only secrets destination later moves under OneDrive, Dropbox, Google Drive, or a junction to a synced folder, does the invariant catch that? It should resolve the destination path too, not only classify source paths.

4. Partial backup after mid-run failure.

   The spec says failed DB verification sets non-zero exit code. It does not say whether the run directory is marked failed, deleted, excluded from future “previous manifest” comparisons, or protected from retention pruning.

5. Locked or mutating databases.

   SQLite backup API helps with live databases, but failure modes remain: busy timeout, permissions, long-running writers, WAL checkpoint behavior, source changes during verification, corrupted source DB, or source DB deleted mid-run. The spec should define expected behavior.

6. OneDrive sync behavior.

   Copying into OneDrive is not equivalent to confirmed off-machine backup. OneDrive may be paused, offline, out of quota, blocked by file locks, or still syncing. If the requirement is only “place files in the local OneDrive folder,” say that. If the requirement is “backed up to cloud,” this spec does not verify it.

7. Manifest leakage.

   The spec mentions generated `MANIFEST.md`. If manifests include full paths or filenames like `credentials-prod.json`, they may leak sensitive project details into OneDrive even when secret file contents do not. The spec does not say whether secret paths are included in synced manifests.

8. Case-insensitive and path-normalization bugs on Windows.

   The amendment mentions parent containment rather than string prefix. Good. But Windows has case-insensitive paths, 8.3 short names, reparse points, UNC paths, drive-letter aliases, and OneDrive redirections. The criteria should require resolved/canonical path comparison compatible with Windows semantics.

9. Prune list drift.

   The spec adds `.session` and `chrome-profile` after a leak. Future app-state directories may appear under different names. A denylist-only prune strategy has the same failure shape as the original hardcoded backup list, just inverted.

**Architectural Alternatives Worth Weighing**

1. Default-deny allowlist by project, not broad filename discovery.

   Instead of “walk vaults and copy any `*.db`,” define an allowlist manifest such as:

   ```yaml
   vaults:
     Pappa T:
       include:
         - path: "2. SOPS/sops.db"
           class: data
           sync: onedrive
         - path: ".claude/agent-memory/"
           class: data
           sync: onedrive
       exclude:
         - ".session/"
         - "chrome-profile/"
   ```

   Why weigh it: the spec’s own leaks came from over-broad discovery. Discovery is good for reporting candidates, but backup should maybe require explicit approval before syncing newly discovered data.

2. Two-phase model: discover candidates, require promotion to backup policy.

   The script could discover all candidate runtime files and emit `NEW_UNAPPROVED` without backing them up until added to a policy file. Known approved files are backed up; unknown files are surfaced but not synced.

   Why weigh it: this directly addresses the Chrome-profile class of failure. Unknown runtime data is more likely to be risky than safe.

3. Sync only encrypted archives, including data.

   Even if secrets encryption is out of scope, the safer architecture is to encrypt everything before OneDrive, not just secrets. That avoids needing perfect classification between `DATA` and `SECRET`.

   Why weigh it: the spec has already shown that classification can fail. Encryption reduces blast radius when it does.

4. Separate backup targets by sensitivity and ownership.

   The Fan Movement issue is partly an ownership/data-governance failure. Consider destination policies like:

   - personal data: OneDrive allowed
   - client/company data: local-only or excluded
   - secrets/session material: encrypted local-only
   - browser/app profiles: never

   Why weigh it: `Operations` was excluded because of contract termination, but the same issue could recur inside Pappa T if a project contains third-party data.

5. Use a backup manifest with explicit successful-run marker.

   Rather than treating any run directory as a retained backup, write to a temp directory, verify, then atomically finalize with a `SUCCESS.json` manifest. Retention only considers successful finalized runs.

   Why weigh it: it handles partial-run ambiguity, failed verification, and drift comparison more cleanly.

6. Add a “sensitive path scanner” independent of backup classification.

   Before writing synced output, scan all would-be synced files and paths for known-dangerous names:

   - `Login Data`
   - `Cookies`
   - `Local Storage`
   - `IndexedDB`
   - `Session Storage`
   - `Network`
   - `.session`
   - browser profile markers
   - `key`, `token`, `secret`, `credential`, `oauth`, `auth`

   Why weigh it: not sufficient alone, but it provides a second line of defense against the exact failure described in the amendment.

Bottom line: the spec is much better after the amendment, and the hard invariant for excluded vault leaks is the right kind of control. The main unresolved design risk is that “discovery over hardcoding” is still allowed to place newly discovered `DATA` into OneDrive by default. Given the spec’s own wording that the Chrome leak was “luck, not design,” I would seriously consider changing unknown discovery from “backup unless pruned” to “report until explicitly approved.”

_Advisory only — reviewer agent retains sole APPROVE/BLOCK authority._

## 2026-08-09 — Disposition of the Codex review

Two of Codex's points were acted on the same session; the rest are recorded, not adopted.

**Acted on — "Manifest leakage", and it was real rather than theoretical.** Checked against
the run made minutes earlier: the *synced* `manifest.json` carried all six secret paths in
its `discovered` list, and `secrets_location` carried the local secrets directory; the synced
`MANIFEST.md` named it twice more. No secret *contents* left the machine — but a precise map
of where every credential lives on this machine was syncing to a cloud provider, which is the
thing the local-only split exists to prevent. The existing invariant looked for secret
*files* in the synced tree and had nothing to say about *references* to them.

Fixed by redacting the synced manifest after the copy (the local copy keeps everything, so
restore is unaffected), and by extending the invariant to fail on a reference as well as a
file. The new check was proven with a **positive control** rather than assumed: run against
the pre-fix backup it detects 5 references; against the post-fix backup, 0.

**Acted on — the `.session`/`chrome-profile` prune**, which Codex independently reached from
the spec's own wording ("luck, not design") without seeing the code.

**Recorded, not adopted — the strongest structural point.** Codex argues discovery should
inarguably flip from *backup unless pruned* to *report until explicitly approved*: a
default-deny allowlist, or a two-phase discover-then-promote model. The reasoning is that
both leaks found today were newly-discovered `DATA` reaching OneDrive by default, so pruning
is a list of mistakes already made, and the next unknown gets synced before anyone looks.
That is correct as a diagnosis. It is also a redesign of the script's central premise
("discovery over hardcoding", the property that caught three files the hand-written list
missed), so it is an owner decision and a separate piece of work — tracked in `docs/todo.md`,
not silently taken here.

**Not adopted, with reasons:** encryption of the secrets backup was already an explicit
out-of-scope tradeoff in this spec and has not changed; "fails loudly"/"writes nothing" being
under-specified is fair but these are exit codes 1/2/3 with printed reasons, adequate for a
single-operator script; and the Windows case-insensitivity concern is real in principle but
`excluded_leaks()` compares resolved `Path` objects, which normalise case on Windows — its
lookalike-sibling test covers the specific bug shape.
