## 2026-08-09 — Narrowing one backup scope revealed what the other scope was leaking
**Source:** session — re-scoping `scripts/backup-runtime-data.py` after the contract ended
**Status:** active

Dropping `Desktop/Operations` from the backup was the task. **Two unrelated leaks came out
of doing it**, and neither was found by reading code.

**1. A signed-in Chrome profile was syncing to OneDrive.** With Operations removed, five
*new* databases appeared in the discovery set — all under
`Pappa T/TebelloReborn/.session/chrome-profile/`, the hand-signed-in profile from Phase E
(857 files, `Login Data`, `Network/Cookies`). Its Chromium `*.db` files were being copied
into the **synced** tree daily. The credential stores escaped only because Chrome names them
with no extension, so `*.db` never matched — **luck, not design**. True and unnoticed since
2026-08-08. Prune browser profiles outright; they are regenerable and re-signable.

**2. The synced manifest was a map of every secret on the machine.** Raised by an advisory
Codex review, then *confirmed against a real run*: `manifest.json`'s `discovered` list
carried all six secret paths and `secrets_location` carried the secrets directory. No
contents left the machine — but the existing invariant checked for secret **files** in the
synced tree and said nothing about **references** to them, so the local-only split was
weaker than it read.

**Three reusable rules, in order of how much they earned:**

- **A scope change is a discovery event.** Narrowing one input changed what the other input
  surfaced. Nothing about the leak was new; removing the noise is what made it visible. After
  changing what a discovery-based tool scans, *read the dry run* rather than checking it
  exits 0.
- **"No X in the output" and "no reference to X in the output" are different invariants**,
  and the second is the one that gets forgotten. Redacting is not enough on its own —
  re-check that the redaction held.
- **Prove a new guard with a positive control.** The reference check was verified by running
  it against the pre-fix backup (5 detections) as well as the post-fix one (0). A guard only
  ever tested against clean data is indistinguishable from a guard that never fires.

Fix shape worth copying: `Desktop/Operations` went into a named `EXCLUDED_VAULTS` constant
carrying the reason, the date and an explicit "do not add this back", *plus* a run-time
invariant (exit 3) that fails the run if any discovered path resolves inside it. The constant
alone would have been undone by the first session that read a Pappa-T-only backup as a bug.

## 2026-08-09 — Fan Movement contract terminated 2026-08-03; company IP staged for handover
**Source:** session — owner notified mid-session, survey and staging performed same session
**Status:** active

**The contract with Fan Movement (Pty) Ltd ended Monday 2026-08-03.** Everything under
`Desktop/Operations/` is that company's domain. Recorded here because every other entry in
this file was written while the contract was live and silently assumes it.

**Staged:** `Desktop/Fan Movement - Company IP/` — 1,064 files, 108 MB, a **copy**. Scope
was business data plus the four tools built for the company; DCOE tooling, personal notes,
build artifacts excluded. `MANIFEST.md` + sha256 `CHECKSUMS.txt` over all 1,074 files.
Databases via the sqlite3 backup API and verified (`sops.db`: 13 tables / 6,501 rows,
integrity ok). The one `.env` staged into its own `04-credentials/` rather than left inside
the tool copy.

**The finding worth keeping is what a folder cannot do.** "Put the company IP in a folder"
sounds like a filesystem task and is mostly not one. The same material sits in **five**
places, and copying addresses one:

| Where | What | Reach |
|---|---|---|
| `Desktop/Operations/` | everything, live | local |
| `O-P-C/Operations/` | **641 files in git history** — 64 `.xlsx`, 14 `.csv`, 13 `.pdf`, incl. the invoice CSVs and contract register | private GitHub |
| `tlelosa-web/{sops,NamePlateTool,Claude-Code}` | full commit history, **personal account** | private GitHub |
| `~/OneDrive/DCOE-Backups/` | 5 dated backups incl. production `sops.db` | Microsoft cloud |
| `~/Backups/dcoe-{runtime,secrets}/` | same DBs + Operations `.env` | local |

**Generalisable:** when a request names a *destination* ("put it in a folder"), check whether
the thing being moved has copies the destination does not govern. Here the git history is the
larger footprint and the one a folder is structurally incapable of touching — and a completed
folder looks exactly like a completed job.

**One live consequence, handled:** the daily `DCOE runtime-data backup` task was still
scheduled and would have copied the production `sops.db` into OneDrive at 12:30 the next day.
**Disabled** (`Disable-ScheduledTask -TaskName "DCOE runtime-data backup"`), not deleted —
re-enable with `Enable-ScheduledTask`. It also covered Pappa T's `career.db` and
`outreach.db`, so that protection has lapsed until the script is re-scoped.

**Deliberately not done:** nothing deleted, no history rewritten, no repo made private-er or
transferred. Retention terms are a contract question, and history rewrites are irreversible
and break every clone. Tracked as open items in `docs/todo.md`.

**Also now stale by this:** the "IT clearance on record" caveat attached to the
codex-gate/OpenAI-egress item and to cloud sessions cloning this vault — that clearance was
granted by a company that is no longer the contracting party. See
`knowledge/tlelosa-claude-config.md`.

## 2026-08-09 — `C:\Dev\…` is gone; every cached Operations path predating 2026-08-03 is suspect
**Source:** session — verifying `/overwatch`'s project→path table before landing it
**Status:** active

**`C:\Dev` does not exist on this machine.** Every Operations project lives under
`Desktop/Operations/` since the 2026-08-03 consolidation. Confirmed live paths:

| Project | Path |
|---|---|
| Operations machine-level queue | `Desktop/Operations/docs/todo.md` |
| SOPS | `Desktop/Operations/2. SOPS/` (git default branch is **`master`**, not `main`) |
| NamePlateTool | `Desktop/Operations/3. Nameplate & Test Sheet/` |
| delivery-note-system | `Desktop/Operations/7. DELIVERY NOTE/delivery-note-system/` |
| daily-sales-order-files | `Desktop/Operations/1. Daily Sales Order Files/` (no `docs/` scaffold) |
| This hub | `Desktop/O-P-C/` — **not** `C:\Dev\Claude-Code` |

**The generalisable part is why the cache was wrong rather than that it was.** The
`C:\Dev\` paths were not errors when written: the 2026-07-24 entry below records a real
OneDrive-corruption fix that genuinely relocated repos off the synced Desktop, and the
2026-07-28 entry records a clone that genuinely sat at `C:\Dev\Claude-Code`. Both were
correct on a machine that no longer exists as a separate thing. **A cached path is a
claim with an expiry date that nothing in its own text reveals** — the entry reads as
confidently as it did the day it was true, which is the same failure shape as a stale
`session-log.md` entry (see `hub-process.md`) applied to filesystem layout instead of
commit clocks.

**What this cost, concretely:** `/overwatch` shipped its path table through two reviewer
rounds with two `C:\Dev\` entries in it. A reviewer reads a path; only a filesystem
answers it. Had it landed unverified, 5 NamePlateTool and 4 delivery-note-system open
items would have been reported "unreachable" on every run — silently, by the one command
built to make open work visible.

**Corrected in this pass:** `daily-sales-order-files.md` and `delivery-note-system.md`
(header paths, in place, with the reason). Left as history per Hard Rule 2: the dated
entries below, and `docs/todo.md`'s 2026-07-28 Done entry — those record what was true
then and are not claims about now. `sops.md` already said "was `C:\Dev\…`" and needed
nothing.

**Standing check:** when a `knowledge/` entry supplies a path you are about to act on,
test it before trusting it. Cheap, and this session found a 33% error rate in a
hand-maintained list that had already been reviewed twice.

## 2026-08-06 — Backup scheduled daily (Windows Task Scheduler)
**Source:** session (this machine, `TshepangLelosa`)
**Status:** active

`scripts/backup-runtime-data.py` now runs automatically.

| | |
|---|---|
| Task name | `DCOE runtime-data backup` |
| Schedule | daily, 12:30 |
| Runs as | `TshepangLelosa\tlelo`, interactive, **Limited** (no elevation) |
| Log | `~/Backups/backup-runtime.log` (appended, one header block per run) |

Verified by triggering it manually: `LastTaskResult = 0`, and the run produced
a real backup — 7 databases, all `integrity_check` + row-count verified, no
failures. A clean exit code alone would not have proved that; the manifest was
checked too.

**Why it runs only while logged on.** A task that runs whether or not the user
is logged on requires storing the account password with the task. That is not
something to hand over, so the task is registered `LogonType Interactive`
instead. The practical cost: if the machine is off or the user is signed out at
12:30, that day's run is missed — mitigated by `-StartWhenAvailable`, which
makes Task Scheduler catch up on the next opportunity rather than skipping the
day entirely.

**Settings that matter and why:**

- `-StartWhenAvailable` — catch up a missed run (the machine will not always be
  on at 12:30).
- `-MultipleInstances IgnoreNew` — a catch-up run must not overlap a manual one.
- `-ExecutionTimeLimit 30m` — the real run takes seconds; anything near the cap
  means something is wrong, so it fails rather than hanging indefinitely.
- `-AllowStartIfOnBatteries` / `-DontStopIfGoingOnBatteries` — a ~7 MB copy is
  not worth skipping on battery.

**Scheduled runs use `--log-file`, not `--quiet`.** A scheduled task has no
console, so quiet mode would discard the detail entirely and leave nothing to
diagnose. Full output goes to the log; `--quiet` remains for interactive use.

**Managing it:**

```powershell
Get-ScheduledTaskInfo -TaskName "DCOE runtime-data backup"   # last result, next run
Start-ScheduledTask   -TaskName "DCOE runtime-data backup"   # run now
Disable-ScheduledTask -TaskName "DCOE runtime-data backup"   # pause
Unregister-ScheduledTask -TaskName "DCOE runtime-data backup" -Confirm:$false
```

To change the time, re-register with a new `-Daily -At` trigger — the whole
registration is in `docs/session-log.md`'s 2026-08-06 scheduling entry.

**Not covered:** nothing alerts on failure. A failed run sets a non-zero
`LastTaskResult` and writes the reason to the log, but nobody is told. Checking
`Get-ScheduledTaskInfo` occasionally is the current answer.

## 2026-08-06 — Runtime-data backup is now a committed script
**Source:** session (this machine, `TshepangLelosa`)
**Status:** active

Supersedes the hand-run procedure in the entry below — that entry's *reasoning*
still stands, but the file list in it is no longer authoritative. The script
discovers files rather than reading a list.

**Run it:**

```bash
python scripts/backup-runtime-data.py            # back up + verify
python scripts/backup-runtime-data.py --dry-run  # show what would happen
python scripts/backup-runtime-data.py --quiet --keep 14
```

Exit codes: `0` verified, `1` some file failed, `2` the data/secret separation
invariant broke. Retention defaults to the last 7 runs per destination.

**Discovery beats a hardcoded list, demonstrated.** On its first dry run the
script found three things the hand-written list had missed entirely: a
`TebelloLelosa.pfx` certificate under
`TebelloReborn/_archive_qwen_prototype/2_Source_Data/Legacy_CV_Archive/`, and
agent-memory trees under `Operations/.claude/` and
`Operations/2. SOPS/.claude/`. Nothing would ever have reported those as
missing.

**Two gotchas found building it, both worth remembering:**

1. **`*.db` does not match `sops.db.pre-batch34-backup-...`.** SOPS's seven
   dated rollback snapshots were silently dropped by the first draft. Fixed
   with a separate `SNAPSHOT` class (`*.db.*`), copied as plain files since
   they are static. Caught only by diffing the run against the earlier
   hand-run output — *not* by reading the code. When replacing a manual
   process with an automated one, compare outputs before trusting it.
2. **`.claude/worktrees/` are live git worktrees**, not scratch folders.
   Walking into them backed up every match two and three times (the `.pfx`
   appeared three times). Now pruned. `git worktree list` confirms what they
   are.

**The invariant that gets a hard check:** no `SECRET`-classified file may land
in the OneDrive-synced tree. The script re-scans the synced output after
writing it and exits `2` if any appear. This is the one failure that would be
both silent and serious — plaintext OAuth tokens and a `.pfx` reaching cloud
sync — so it is asserted rather than assumed.

**Still not scheduled.** The script supports unattended use; nothing runs it
automatically. Registering a Windows scheduled task changes system config and
stays a deliberate decision.

## 2026-08-06 — Live runtime data: what it is, and how it gets backed up
**Source:** session (this machine, `TshepangLelosa`) — first real backup run
**Status:** active

The gitignored runtime state across both vaults is the only data in this
system with no second copy — git never captured it by design, which is
precisely why the O-P-C consolidation kept the Desktop folders rather than
superseding them. First backup taken 2026-08-06.

**Inventory (it is small — ~1.3 MB live, ~6.9 MB with history):**

| What | Where | Notes |
|---|---|---|
| `sops.db` | `Operations/2. SOPS/instance/` | production, 13 tables, 6,501 rows |
| `dev.db` | `Operations/7. DELIVERY NOTE/delivery-note-system/` | 2 tables |
| `career.db` | `Pappa T/TebelloReborn/` | 5 tables |
| `outreach.db` | `Pappa T/ai-outreach-agency/` | 3 tables |
| `cache.db` ×2 | `Pappa T/Tenders/`, `Tenders/4_Scripts/` | 6 tables each |
| 7 `sops.db.pre-*` snapshots | `Operations/2. SOPS/instance/` | pre-migration safety copies |
| agent memory | `Pappa T/.claude/`, `TebelloReborn/.claude/` | 8 files, accumulated |
| 6 secret files | see below | live OAuth + API keys, ~2.4 KB |

`Pappa T/TebelloReborn/data/career.db` is 0 bytes — an empty stub, skipped.

**Two destinations, split by sensitivity — this split is the point:**

- **Databases + agent memory** → `~/Backups/dcoe-runtime/<stamp>/` **and**
  `~/OneDrive/DCOE-Backups/<stamp>/`. Safe to sync: no credentials in it.
- **Secrets** (`.env` ×4, `credentials.json`, `token.json`) →
  `~/Backups/dcoe-secrets/<stamp>/` **local-only, never synced.** Keeping
  live OAuth tokens out of a cloud-synced folder is deliberate, not fussiness.
  Verified after the run that the OneDrive copy contains zero secret files.

**Use the sqlite3 backup API, not `copy`.** `sqlite3` CLI is not installed on
this machine, but Python's built-in `sqlite3` has it:

```python
s = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
d = sqlite3.connect(dst)
with d:
    s.backup(d)
```

This yields a consistent snapshot even if something is mid-write. A raw file
copy of a live SQLite database can capture a torn state — a real risk for
`sops.db`, which a running SOPS dev server holds open.

**Verify by row count, not by file size.** Each backup was checked with
`PRAGMA integrity_check` (all `ok`) and then re-opened to compare per-table
row counts against the source. Sizes can match while contents differ; row
counts caught nothing this run but are the check that would.

**Reusable script:** the run used a one-off script rather than anything
committed. Re-deriving it is ~15 minutes; if this becomes routine, promote it
to `Operations/` or a hub `scripts/` folder rather than rewriting it.

**What this does not cover:** it is a point-in-time snapshot, not continuous.
Nothing schedules it. `sops.db` changes daily in normal use, so the backup is
stale the moment SOPS is used again.

## 2026-07-28 — Operations ↔ cloud-environment git-sync bridge confirmed
**Source:** Operations hub session (work PC)
**Status:** active

Set up Operations (work PC) as a DCOE hub client of this repo, mirroring
the Pappa T setup (see `knowledge/pappa-t.md`). Same architecture: git
push/pull is the only sync channel, no live remote-environment bridge.

> **Paths in this entry are superseded (2026-08-09).** The bridge and its
> reasoning still hold; `C:\Dev\…` does not exist since the 2026-08-03
> consolidation. See the 2026-08-09 entry at the top of this file for current
> paths. Kept as written per Hard Rule 2 — this records what was true then.

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
