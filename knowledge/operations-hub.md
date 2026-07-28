## 2026-07-28 — Operations ↔ cloud-environment git-sync bridge confirmed
**Source:** Operations hub session (work PC)
**Status:** active

Set up Operations (work PC) as a DCOE hub client of this repo, mirroring
the Pappa T setup (see `knowledge/pappa-t.md`). Same architecture: git
push/pull is the only sync channel, no live remote-environment bridge.

- Clone path on this machine: `C:\Dev\Claude-Code` — a sibling of
  `C:\Dev\Operations`, not nested inside it. Deliberately kept separate:
  the Operations hub's own root `CLAUDE.md` hard rule 2 says
  `C:\Dev\Operations` itself doesn't become a git repo without a
  standalone deliberate decision, and this setup doesn't trigger that —
  `Claude-Code` is a different repo in a different folder.
- Repo was already cloned and on `main` when this session started (not a
  fresh clone) — confirmed clean working tree, then `git fetch origin` +
  `git pull origin main` pulled 8 files of genuinely new upstream work
  (`.claude/commands/continue.md`, updated root `CLAUDE.md`,
  `docs/session-log.md`, `docs/todo.md`, `knowledge/pappa-t.md`,
  `knowledge/tlelosa-claude-config.md`, `knowledge/nameplatetool.md`,
  `knowledge/INDEX.md`) — i.e. this pull was not a no-op, unlike the
  bridge-check pattern used for Pappa T.
- `git push origin main --dry-run` confirmed "Everything up-to-date"
  immediately after the pull — push side of the bridge verified working
  with nothing to push yet.

**Reusable takeaway:** confirming this bridge on a second machine doesn't
require the pull to be a no-op — a real fast-forward that applies cleanly
with no conflicts is just as valid a confirmation, arguably a stronger one
since it exercises the merge path, not just the network round-trip.

## 2026-07-24 — OneDrive-synced folders corrupt `.git` internals; fix is relocate + junction, not just `.gitignore`
**Source:** Operations hub (Fan Movement work PC) — SOPS project's own `docs/todo.md` Batch 14/22 entries (2026-07-08 onward)
**Status:** active

If a git repo lives inside a folder OneDrive is actively syncing (e.g. the
default `Desktop\...` path), OneDrive's own backup/sync process reaches
into `.git` internals mid-operation — not just tracked files — and leaves
corruption artifacts:

- `.git/index.lock.bak.*`, `.git/HEAD.lock.bak.*` — stale lock files from
  OneDrive syncing a lock file while git held it.
- `.git/refs/heads/master.lock.bak.*` — same pattern on ref files, breaks
  `git branch -a` / `git log --all` with `fatal: bad object` until removed.

This recurred multiple times across sessions (once causing a stuck
`.git/index.lock` mid-task) before the root cause was pinned down: it's
not a one-off — it's structural as long as the repo stays under active
OneDrive sync scope. `.gitignore`-ing `.git` contents doesn't help; OneDrive
touches the files regardless of git's own ignore rules.

**Fix that actually resolved it:** relocate the whole working tree outside
any OneDrive-synced path (e.g. `Desktop\Operations` → `C:\Dev\Operations`),
then leave a **directory junction** at the old OneDrive path pointing to
the new location (`mklink /J "old\path" "C:\Dev\new\path"` equivalent).
This keeps existing shortcuts/pinned paths/muscle memory resolving
correctly while taking the actual `.git` directory out of OneDrive's sync
scope entirely. Confirmed no recurrence of lock corruption after the move.

**Recovery when it happens before you can relocate:** the `.lock.bak.*`
files are safe to delete once you've confirmed (via `git fsck` and
checking what ref the lock file's target commit points to) that no data
loss would result — they're leftover copies, not the live lock. A plain
`git status` / `git reset` afterward rebuilds a clean index.

**Reusable check:** if you see `.lock.bak.*` files anywhere under `.git/`,
or `bad object` errors from ref-walking commands, on a repo living under
any cloud-sync folder (OneDrive, Dropbox, Google Drive), suspect this
pattern before assuming local git corruption — the sync client is the
actual cause, and the fix is moving the repo, not just cleaning locks.
