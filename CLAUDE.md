# CLAUDE.md — Claude-Code

# Owner: Tebello Lelosa

> The DCOE hub root for everything Tebello Lelosa is working on — projects,
> repos, and machines. Read `knowledge/INDEX.md` at session start for the
> topic-keyed fact cache, and read
> `~/.claude/plugins/marketplaces/tlelosa-claude-config/dcoe-roster/CORE.md`
> at session start for the DCOE architecture, sub-agent roster, model
> routing, and universal hard rules — treat its contents as part of this
> session's operating instructions, same as any other rule in this file.
> If that path doesn't exist on this machine, say so rather than silently
> skipping it.

-----

## How this repo works

Two things live here at once, deliberately kept separate:

- **`knowledge/`** — a flat, topic-keyed fact cache. Don't re-derive facts
  already found in a prior session.
  1. **Before researching anything** not already in this session's
     context, check `knowledge/INDEX.md` for a matching topic. If found,
     read that file instead of re-deriving the answer.
  2. **Before ending a task** that surfaced a reusable fact (a config
     quirk, a decision, an API behavior, an approach that didn't work) —
     append it to the matching `knowledge/<topic>.md` (create a new one if
     nothing fits), and update its line in `knowledge/INDEX.md`.
- **`docs/todo.md` + `docs/session-log.md`** — the actual hub-level task
  queue and session log that `.claude/commands/continue.md` (the
  `/continue` resume command, from `tlelosa-claude-config`'s
  `hub-template/`, copied here 2026-07-28) reads on every run. Hub-level
  only: cross-project tasks, or new work started at root. A project's own
  `docs/todo.md` (in its own repo) stays authoritative for anything scoped
  inside that project.

**Session commands.** `/continue` (resume) and `/session-end` (close out) are
the routine pair — one at each end of a session, per ADR-008. `/retro`
(`.claude/commands/retro.md`, copied in 2026-08-09) is **periodic, not
routine**: run it weekly, or whenever a session felt like a repeat of one
already done. It reads backward across `docs/session-log.md` and
`docs/todo.md` for *framework* friction — the queue asserting completion it
didn't have, a fact about another repo that was stale when written, the same
gap recurring — and proposes a confirmable batch. It records each run in
`docs/retro-log.md`, which is what stops it repeating its own complaint.

**Hub-and-spoke:** any sub-project with its own `CLAUDE.md`/`AGENTS.md`
takes precedence over this file for work done inside that project's
folder. This file governs cross-project decisions and new work started at
root — not everything everywhere.

-----

## 📍 Live copies vs. this repo's snapshot

`Operations/` and `Pappa T/` **inside this repo** are a historical
consolidation snapshot (the 2026-08-03 subtree merges — committed git
history only). They hold no runtime state: no databases, no real `.env`
files (only `.env.example`), no `agent-memory`. Verified 2026-08-10.

> ⚠️ **Nothing lives under `Desktop/` any more, including this hub.**
> `Desktop/Operations/` and `Desktop/Pappa T/` were deleted to the Recycle
> Bin on 2026-08-10 (~06:43), deliberately. Separately — and recorded
> nowhere until 2026-08-10 — **this repo itself moved from
> `Desktop/O-P-C/` to `~/O-P-C/`**. `Desktop/` now holds exactly one
> folder, `Fan Movement - Company IP/`.
>
> **Pappa T is back, at a new path.** Re-cloned 2026-08-10 from
> `tlelosa-web/pappa-t` to **`~/Pappa T/`** (not Desktop), with its runtime
> state restored from the `20260809-215839` backup run and every database
> re-verified. `Operations` was **not** restored and is not intended to be.
>
> Every path table in this repo naming a `Desktop/…` copy is therefore
> **still stale** — `.claude/commands/overwatch.md`, `continue.md` and
> `session-end.md`, and several `knowledge/` entries. They are left in place
> rather than rewritten piecemeal; that sweep is an open item in
> `docs/todo.md`. Re-check before trusting any of them.
>
> One thing the restore does **not** bring back:
> `TebelloReborn/.session/chrome-profile`, the hand-signed-in Indeed profile
> from Phase E. It was deliberately pruned from the backup on 2026-08-09 as
> a credential leak, so it existed only in the deleted tree. Phase E needs a
> fresh manual sign-in via `tools/indeed_login_setup.py`.

What survives, and what does not:

| Repo | Default branch | Remote — now the only copy | Runtime state |
|---|---|---|---|
| Pappa T — **one** repo covering every sub-project (TebelloReborn, ai-outreach-agency, IQ, MIMS App, Tenders…) — live again at **`~/Pappa T/`** | `main` | `tlelosa-web/pappa-t` | live in `~/Pappa T/`, backed up daily; also `~/Backups/dcoe-runtime/` + `dcoe-secrets` |
| SOPS | **`master`** | `tlelosa-web/sops` | `sops.db` in the Fan Movement staged copy only |
| Nameplate & Test Sheet | `main` | `tlelosa-web/NamePlateTool` | — |
| delivery-note-system | `master` | ⚠️ **none — no copy anywhere** | `dev.db` + `.env` in the Fan Movement staged copy only |
| this hub | `main` | `tlelosa-web/Claude-Code` | n/a |

`delivery-note-system` is the one real loss: it never had a remote, so its
git history existed only inside the deleted tree. The Fan Movement staged
copy carries its `dev.db` and `.env` but explicitly **not** git history.

Editing a file in this repo's snapshot still does **not** reach a running
project — it only creates a re-merge to do later. That is why `docs/todo.md`
flags items with 📍, and why `/overwatch` is forbidden from reading the
snapshot folders even as a fallback.

Per `knowledge/operations-hub.md`, a cached path table is a claim with an
expiry date nothing in its own text reveals. This one expired four minutes
after it was written — re-check rather than trust it.

-----

## Commands

There is no build and no hub-level test suite — this repo is docs, process,
and one script. Work runs through three commands in `.claude/commands/`:

- **`/continue`** — session resume. Steps 1.75 / 1.8 / 1.9 carry the weight:
  pull before any edit, find branches earlier sessions stranded, and verify
  the hub's log against the live sub-projects' commit clocks *before*
  believing it. It ends by waiting for confirmation — it never starts work.
- **`/session-end`** — close-out: reconcile `docs/todo.md`, write the dated
  `docs/session-log.md` entry, update `knowledge/`. Surfaces uncommitted and
  unpushed work; never commits or pushes without explicit confirmation.
- **`/overwatch`** — read-only status across this hub, every tracked
  sub-project, and the config repo. Its project→path table is hand-maintained
  inside the command file; update it by hand when a project moves.

The one script:

```
python scripts/backup-runtime-data.py [--dry-run] [--quiet] [--keep N] [--log-file PATH]
```

Backs up the gitignored live runtime state of the Pappa T vault — the only
data here with no second copy. Exit `2`, `3` or `4` means an invariant broke
(data/secret separation; an excluded vault reaching the discovery set; or a
configured vault missing/empty), not an ordinary failure. `Desktop/Operations`
is excluded **deliberately** (Fan Movement contract terminated 2026-08-03) —
don't add it back to "fix" a Pappa-T-only backup.

**Coverage restored 2026-08-10.** `VAULTS` is now `~/Pappa T` and the daily
task runs against it again — verified by a real scheduled run, not just an
exit code. Do **not** re-point it at this repo's `Pappa T/` snapshot: that
holds no runtime state, so it would look like a working backup and protect
nothing.

Two traps this script has now hit twice, both worth knowing before editing it:

- **The scheduled task holds its own copy of the path.** Re-pointing `VAULTS`
  fixed nothing on its own — the task still named
  `Desktop/O-P-C/scripts/backup-runtime-data.py`, which no longer exists, so
  it would have died with a Python "can't open file" rather than the
  deliberate exit `4`. **A config change in the script is not a config change
  in the thing that runs it.** Check
  `(Get-ScheduledTask "DCOE runtime-data backup").Actions` after any move.
- **`prune_old()` was reporting success while failing.** `rmtree` with
  `ignore_errors=True` plus an unconditional "pruned" line hid that Windows
  refuses `rmdir` on a ReadOnly directory — and `copytree` inherits ReadOnly
  from the vault's `agent-memory` trees. Every prune deleted a run's *files*
  and left the directory shell, which then occupied a retention slot, so
  `--keep 7` quietly kept one fewer real run each cycle. Only `dcoe-secrets`
  escaped, by being flat. Fixed 2026-08-10. Same shape as the exit-4 bug and
  the same shape as the `rmtree` attribute failure already recorded in
  `docs/todo.md`'s Fan Movement entry — **on Windows, treat any `rmtree` that
  cannot fail as a bug.**

Decisions live in `docs/decisions/` (ADR-007…ADR-010), build specs in
`docs/specs/`, dated. A build task with no spec is a spec-gate stop, not a
green light.

-----

`knowledge/`'s own dated-entry format (below) already carries date, source,
and status per entry — treat it as satisfying `hub-template`'s note-
frontmatter convention (date/source/project/status) in spirit; it's not
reformatted to literal YAML frontmatter since the per-topic-file structure
already encodes `project` via the filename.

-----

## Entry format

Each `knowledge/<topic>.md` file holds dated entries, most recent first:

```
## YYYY-MM-DD — <short finding title>
**Source:** session / URL / project name
**Status:** active | superseded

<the finding itself, written so it's directly usable — not a summary of
a conversation, the conversation's *output*>
```

-----

## Hard rules

These add to `CORE.md`'s Universal Hard Rules — they never relax them.

1. Keep entries factual and usable as-is — not a transcript summary, the
   actual data/decision/gotcha.
2. Superseded entries are marked `Status: superseded`, not deleted — the
   history of what changed is itself useful context.
3. One topic = one file. Split a file once it's covering more than one
   clearly separate subject.
4. No company or project data beyond what's already public in the source
   project's own repo — same discipline as `tlelosa-claude-config`.
5. Update `docs/todo.md` and `docs/session-log.md` after every hub-level
   task, same discipline as the knowledge-cache update rule above.
6. **Pull before you edit a contention file.** `docs/todo.md`,
   `docs/session-log.md`, `knowledge/INDEX.md`, and `docs/retro-log.md`
   (the fourth, added 2026-08-09 with `/retro`) get written by nearly
   every hub-level session — with Operations, Pappa T, and cloud sessions
   all able to run concurrently, stale-base edits to these four files have
   already caused two real merge conflicts (see `docs/session-log.md`,
   2026-07-28 entries). Before editing any of them, `git fetch origin` +
   `git pull origin main` (or merge/rebase onto latest `main`) first. If a
   conflict still happens anyway, resolve it as a real union of both
   sides' changes — never pick one branch and discard the other's work.
7. **Record the command, not the count.** Literal numbers in todos/logs
   (branch counts, open-items tallies, file counts) go stale within 48
   hours in active repos — the unmerged-branch count has run 13 → 14 → 15
   across three days, nothing looks wrong, and the next reader is misled.
   Convention: **record the command that regenerates the count** rather than
   the number itself (e.g. `"git branch -r --no-merged origin/main | wc -l"`),
   and where a literal number is genuinely needed in a critical list (like
   branch deletion sheets), stamp it as-of a specific `git fetch` and
   explicitly say "re-measure before acting on it." This costs one line and
   prevents decisions made on stale data.
8. **Windows shell traps that have already cost this repo real time** —
   full detail in `knowledge/session-tooling.md`. The four that recur:
   `git commit -m` with a PowerShell here-string splits into pathspecs (use
   `-F <file>`); `Get-Content -Raw` decodes a BOM-less UTF-8 file as ANSI
   and silently mojibakes every em-dash, so round-trip source files through
   Python rather than PowerShell; a `CHECKSUMS.txt` written by Python on
   Windows needs `newline=""` or `sha256sum -c` fails every line at once and
   reads like corrupt data; and a git `A..B` revision range built with a
   PowerShell variable is eaten by the `..` **range operator** before git
   sees it — quote the whole spec (`"main..$b"`) or ask the question with
   `git merge-base --is-ancestor`. All four **succeed** with a wrong value
   rather than failing, which is what makes them expensive: where a shell
   can rewrite an argument, verify the value the tool received.
