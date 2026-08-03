# Spec: OneDrive/Git Corruption Fix

**Status:** Confirmed — scope expanded per Tebello's decision (2026-07-15) to
relocate the **entire `Operations` folder**, not just the 3 git repos. See
§ 3 for the decision record. Ready for execution once § 8 pre-flight checks
pass.
**Author:** Context agent (root hub session), 2026-07-15
**Related:** `CLAUDE.md` § Known Risk, `docs/todo.md` (Next up, item 1), `docs/patterns.md` § 6 (not directly related, listed there in error — no action needed on that link)

-----

## 1. Problem

Three project repos live inside the OneDrive-synced `Operations/` tree:

| Repo | Path | Lock artifacts found |
|---|---|---|
| SOPS | `2. SOPS/` | **18 stale files** — see § 2 |
| Nameplate & Test Sheet | `3. Nameplate & Test Sheet/` | None currently |
| Delivery Note | `7. DELIVERY NOTE/delivery-note-system/` | None currently |

Git writes `.git/index.lock`, `.git/HEAD.lock`, and per-ref lock files as part of
its normal atomic-write protocol (create lock → write → rename over target →
delete lock). OneDrive's sync filter driver runs on the same `.git/` directory
in real time and can grab or re-materialize a file mid-write on Windows. When
that race loses, git fails with `Unable to create '.git/index.lock': File
exists` (or the ref equivalent), and the lock file is left behind.

SOPS's own session log (`2. SOPS/docs/session-log.md`) documents this hitting
production work twice already:
- **Batch 6/7 (2026-06-29 – 07-01):** "git lock files on OneDrive mount
  required direct ref write" — a past session manually renamed live `.lock`
  files to `.lock.bak` to unblock itself rather than deleting them, which is
  why 18 renamed artifacts now sit in `2. SOPS/.git/`.
- **2026-07-13 health check:** two leftover `master.lock.bak.*` files under
  `.git/refs/heads/` broke `git branch -a` / `git log --all` with `fatal: bad
  object` until manually removed and verified against a known-good commit.

**Note:** `.gitignore` is not part of the problem or the fix — all three repos
already correctly ignore `venv/`, `.venv/`, and `node_modules/` from git's own
tracking. The issue is OneDrive syncing the `.git/` metadata directory itself,
which git ignore rules have no influence over.

-----

## 2. Current state (verified this session)

`2. SOPS/.git/` contains, all confirmed stale (repo is currently healthy — see
below):

- 8× `HEAD.lock.bak*` (0 bytes, dated Jun 26 – Jul 7)
- 6× `index.lock.bak*` (0 bytes, dated Jul 1)
- 1× `index_work.lock.bak` (0 bytes, Jun 29)
- 1× `ORIG_HEAD.lock.bak.8732` (0 bytes, Jul 1)
- 1× `index.lock.bad` (0 bytes, Jul 7)
- 2× `next-index-12.lock`, `next-index-13.lock` (~12–13 KB each, Jul 1) — the
  only non-empty ones; contents not yet inspected, but same OneDrive-mount
  interruption pattern as the rest.

Verified healthy despite these artifacts:
- `git status` → clean except one legitimately-in-progress edit
  (`docs/todo.md`), no lock errors.
- `git log --oneline -1` → resolves fine (`617ac77`).
- `git branch -a` → resolves fine (`master`, `agents`).
- `git fsck` → only expected `dangling commit/tree/blob` entries (normal git
  garbage from rebases/resets over time), **no corruption errors**.

Conclusion: the repo is not currently broken. This is stale-artifact cleanup,
not emergency repair.

-----

## 3. Decision record

`docs/todo.md` originally framed the long-term fix as "add OneDrive sync
exclusions ... or relocate repos outside OneDrive sync." Two rounds of
questions with Tebello resolved this:

1. **Relocate vs. exclude:** Relocate. Consumer OneDrive's "Choose folders"
   only supports excluding top-level folders under the OneDrive root, not an
   arbitrary nested path like `2. SOPS/.git` — the exclusion option was
   confirmed not achievable as originally scoped.
2. **Scope of the move — 3 repos, or the whole `Operations` folder:**
   **Whole `Operations` folder.** Tebello chose this over the narrower
   "just the 3 repos" option after being shown the tradeoff: `Operations`
   also holds pure-data folders (`Sage Inventory Report`,
   `Stock Report Reference`, `Workshop Stock - *`,
   `FM Planning & Stock Control`, xlsx masters, ERP exports) that have
   nothing to do with git and currently get OneDrive cloud backup/cross-device
   sync as a side effect of living in this tree. **Moving the whole folder
   means that backup/sync coverage stops for all of it, not just the 3
   repos** — Tebello accepted this explicitly.
   - **Mitigating consideration for future sessions:** if data-loss risk on
     these xlsx/ERP files matters later, that's a separate backlog item (a
     replacement backup strategy for `C:\Dev\FanMovement\Operations`) — not
     blocking this task, but worth surfacing once the move is done rather
     than silently dropped.
3. **Destination:** `C:\Dev\FanMovement\` → full new root becomes
   `C:\Dev\FanMovement\Operations\`.
4. **Discoverability pointer at the old Desktop location:** asked but
   superseded by the whole-folder decision — needs re-confirmation (see § 8,
   this is now "does `Desktop\Operations` keep a junction back to the new
   location," not per-repo).

-----

## 4. Proposed tasks (once Option A/B is confirmed)

### Task 1 — Clean up stale lock artifacts in SOPS (low-risk, do regardless of A/B)
1. Inspect `next-index-12.lock` / `next-index-13.lock` contents to confirm
   they're abandoned index snapshots, not something referenced elsewhere.
2. Delete all 18 confirmed-stale files listed in § 2.
3. Re-run `git fsck`, `git status`, `git log --all`, `git branch -a` to
   confirm no regression.
4. Commit nothing (these files were never tracked — they're untracked
   `.git/` internals, not repo content).

### Task 2A — Relocate repos (if Option A confirmed)
1. For each of the 3 repos: close any open editor/terminal handles, move the
   folder to the agreed non-synced location, verify `git status`/`git log`
   still resolve from the new path.
2. Decide and implement discoverability: shortcut, symlink, or just update
   any docs/READMEs that reference the old path (this hub's `CLAUDE.md`
   project index table included).
3. Update `CLAUDE.md` § Known Risk to reflect resolution, and
   `docs/patterns.md` if a reusable pattern emerges (e.g. "git repos inside
   OneDrive-synced folders should live outside the sync root").

### Task 2B — OneDrive exclusion attempt (only if Tebello rejects Option A)
1. Confirm exact OneDrive client version/edition (consumer vs. Business) —
   Business/SharePoint sync has different exclusion tooling than consumer.
2. If no supported exclusion exists, document that and fall back to Option A.

-----

## 5. Acceptance criteria

- Zero `.lock.bak*` / `.lock.bad` / stray `next-index-*.lock` files remain in
  any of the 3 repos' `.git/` directories.
- `git fsck`, `git status`, `git log --all`, `git branch -a` all run clean
  (no `fatal:` errors) in all 3 repos.
- If Option A: repos function correctly from their new location, and every
  place that referenced the old path (this hub's `CLAUDE.md`, any shortcuts,
  editor workspaces) is updated.
- `CLAUDE.md` § Known Risk updated to reflect resolved/mitigated status.
- `docs/todo.md` item removed from "Next up" and logged in "Done".

-----

## 6. Rollback

- Task 1 (lock cleanup) is non-destructive to tracked content and trivially
  safe — worst case, an artifact turns out to matter and can be restored from
  OneDrive's own version history (files were never deleted from OneDrive
  until this task runs).
- Task 2A (relocation) is reversible by moving the folder back; no history is
  rewritten, no commits change.

-----

## 7. Out of scope

- The unreviewed `2. SOPS/docs/todo.md` uncommitted edit and the still-open
  Batch 24 payment-status data review — pre-existing SOPS-project state,
  unrelated to this fix, not to be touched.
- Any DCOE onboarding decision for the other projects — separate backlog
  item in `docs/todo.md`.
